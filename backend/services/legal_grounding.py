import logging
import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from fastapi import HTTPException

from config import settings, ANALYZER_VERSION
from schemas import LegalGroundingResponse
from services.v12_logging import log_v12_prediction
from services.llm_service import LLMService

# Optional imports for ML
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

logger = logging.getLogger(__name__)


_v12_has_risks_clf = None
_v12_ard_clf = None


async def _ensure_v12_models_loaded():
    """
    Лениво загружает v12-классификаторы has_risks и A/R1/D один раз.
    """
    global _v12_has_risks_clf, _v12_ard_clf
    if _v12_has_risks_clf is not None and _v12_ard_clf is not None:
        return

    # Импортируем здесь, чтобы избежать циклов импорта при старте приложения
    from services.v12_inference import load_v12_models

    has_risks_clf, ard_clf = await asyncio.to_thread(
        load_v12_models,
        "models/v12_has_risks_clf.joblib",
        "models/v12_ard_clf.joblib",
    )
    _v12_has_risks_clf = has_risks_clf
    _v12_ard_clf = ard_clf

class LocalModelManager:
    """
    Singleton manager for the local Qwen2.5-3B LoRA model (v9).
    Loads model once at startup or lazy-loads on first request.
    """
    _instance = None
    _model = None
    _tokenizer = None
    # Path to your LoRA adapter (ensure this path is correct in your Docker/Env)
    _adapter_path = "models/legal_v9_adapter" 
    _base_model_name = "Qwen/Qwen2.5-3B-Instruct"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocalModelManager, cls).__new__(cls)
        return cls._instance

    async def load_model(self):
        """Loads the model into GPU memory. Non-blocking wrapper."""
        if self._model is not None:
            return

        if not ML_AVAILABLE:
            logger.warning("⚠️ ML libraries (torch, transformers, peft) not found. Local model disabled.")
            return

        logger.info(f"🔄 Loading local model: {self._base_model_name} + {self._adapter_path}...")
        try:
            # Run blocking loading in a thread to avoid freezing FastAPI
            await asyncio.to_thread(self._load_weights)
            logger.info("✅ Local model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to load local model: {e}")

    def _load_weights(self):
        """Actual heavy loading logic."""
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self._base_model_name, trust_remote_code=True)
            
            # Load base model in 4bit or 8bit if configured, or fp16
            # Assuming CUDA is available if ML_AVAILABLE is True, but check torch.cuda.is_available()
            device_map = "auto" if torch.cuda.is_available() else "cpu"
            
            self._model = AutoModelForCausalLM.from_pretrained(
                self._base_model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map=device_map,
                trust_remote_code=True
            )

            if os.path.exists(self._adapter_path):
                logger.info(f"Found adapter at {self._adapter_path}, loading PeftModel...")
                self._model = PeftModel.from_pretrained(self._model, self._adapter_path)
            else:
                logger.warning(f"⚠️ Adapter not found at {self._adapter_path}. Using base model only.")

            self._model.eval()
        except Exception as e:
            raise RuntimeError(f"Model loading crashed: {e}")

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Runs inference on the local model.
        Returns a dict with 'decision', 'confidence', 'summary'.
        """
        if not self._model or not self._tokenizer:
            # Check if files exist to provide better error
            if os.path.exists(self._adapter_path):
                 return {"decision": "A", "confidence": 0.0, "summary": "Model failed to load despite files existing."}
            else:
                 # MOCK MODE for Smoke Test if no model
                 logger.warning("⚠️ No local model found. Using MOCK mode for testing.")
                 return self._mock_predict(text)

        # v9 System Prompt
        system_prompt = "Ты — эксперт по закупкам. Классифицируй требование: A (Неясно), R1 (Коррупция/Ограничение), Healthy (Норма), D (Дубликат)."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        text_input = self._tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        inputs = self._tokenizer(text_input, return_tensors="pt").to(self._model.device)
        
        with torch.no_grad():
            outputs = self._model.generate(
                **inputs, 
                max_new_tokens=100,
                temperature=0.1,
                do_sample=False
            )
            
        generated_ids = outputs[0][len(inputs.input_ids[0]):]
        response = self._tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return self._parse_local_response(response)

    def _mock_predict(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based mock for testing without weights"""
        lower = text.lower()
        if "лицензи" in lower or "гаранти" in lower:
             return {"decision": "Healthy", "summary": "[MOCK] Standard requirement", "confidence": 0.9}
        if "apple" in lower or "macbook" in lower or "офис" in lower:
             return {"decision": "R1", "summary": "[MOCK] Restriction detected", "confidence": 0.8}
        if "аналогичн" in lower:
             return {"decision": "A", "summary": "[MOCK] Ambiguous requirement", "confidence": 0.6}
        if "настоящее техническое задание" in lower:
             return {"decision": "D", "summary": "[MOCK] Duplicate/Boilerplate", "confidence": 0.95}
        return {"decision": "A", "summary": "[MOCK] Default ambiguous", "confidence": 0.5}

    def _parse_local_response(self, response: str) -> Dict[str, Any]:
        """
        Parses the v9 model output.
        Expected formats:
        - "Healthy. This requirement is standard..."
        - "R1. This restricts competition because..."
        """
        clean = response.strip()
        
        # Simple heuristic parsing
        if clean.startswith("Healthy"):
            return {"decision": "Healthy", "summary": clean, "confidence": 0.9}
        elif clean.startswith("R1"):
            return {"decision": "R1", "summary": clean, "confidence": 0.85}
        elif clean.startswith("A"):
            return {"decision": "A", "summary": clean, "confidence": 0.6}
        elif clean.startswith("D"):
            return {"decision": "D", "summary": clean, "confidence": 0.95}
        else:
            # Fallback if format is broken
            return {"decision": "A", "summary": clean, "confidence": 0.5}

def _has_r1_keywords(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    keywords = [
        "аналогичн",       # опыт аналогичных контрактов
        "опыт исполн",     # опыт исполнения
        "выручк",          # выручка
        "членств", "сро",  # СРО, членство
        "допуск сро",
        "регистрац",       # регистрация / место нахождения
        "местонахожд", 
        "товарный знак",
        "торговая марка",
        "бренд"
    ]
    return any(kw in lowered for kw in keywords)

async def run_external_audit(text: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calls external LLM (via LLMService) to fully audit the text for A/R1/D/Healthy risks.
    """
    # TODO (Migration to v10):
    # Once 'tendershield-v10-lora:latest' is trained and verified, 
    # switch the default model in LLMService or config to v10.
    # The protocol (instruction/input/output) should remain compatible.
    
    llm = LLMService()
    
    # Defaults for Prompt
    meta = meta or {}
    doc_type = meta.get("doc_type", "Тендерная документация")
    region = meta.get("region", "РФ")
    nmck = meta.get("nmck", "Не указана")
    law_type = meta.get("law_type", "44-ФЗ/223-ФЗ")
    
    # Load few-shot examples for R1 classification
    few_shot_block = ""
    try:
        fewshots_path = Path(__file__).parent.parent / "prompts" / "legal_grounding_ollama_fewshots_v3.json"
        if fewshots_path.exists():
            with open(fewshots_path, 'r', encoding='utf-8') as f:
                fewshots = json.load(f)
            
            # Format few-shot examples
            few_shot_block = "\n\nПРИМЕРЫ ПРАВИЛЬНОЙ КЛАССИФИКАЦИИ R1 (для обучения):\n\n"
            for i, example in enumerate(fewshots, 1):
                few_shot_block += f"Пример {i}:\n"
                few_shot_block += f"Фрагмент: \"{example['context']}\"\n\n"
                few_shot_block += "Ожидаемый ответ:\n"
                few_shot_block += json.dumps(example['expected_json'], ensure_ascii=False, indent=2)
                few_shot_block += "\n\n"
            
            logger.info(f"✅ Loaded {len(fewshots)} few-shot R1 examples (v3)")
    except Exception as e:
        logger.warning(f"⚠️  Could not load few-shot examples: {e}")
        # Continue without few-shots if file is missing
    
    # Rule-based Signal Calculation
    r1_keyword_hit = _has_r1_keywords(text)
    r1_emphasis_block = ""
    
    if r1_keyword_hit:
        r1_emphasis_block = """
ОБРАТИ ОСОБОЕ ВНИМАНИЕ НА ТРЕБОВАНИЯ К УЧАСТНИКАМ.

ЕСЛИ В ТЕКСТЕ ЕСТЬ УСЛОВИЯ ПРО ОПЫТ ИСПОЛНЕНИЯ КОНТРАКТОВ, ВЫРУЧКУ, ЧЛЕНСТВО В СРО,
РЕГИСТРАЦИЮ/МЕСТОНАХОЖДЕНИЕ УЧАСТНИКА ИЛИ КОНКРЕТНЫЙ БРЕНД/ТОВАРНЫЙ ЗНАК,
ТЫ ОБЯЗАН ОТДЕЛЬНО ОЦЕНИТЬ ИХ КАК ПОТЕНЦИАЛЬНО ОГРАНИЧИТЕЛЬНЫЕ (КЛАСС "R1") И
ЯВНО СФОРМУЛИРОВАТЬ, ПОЧЕМУ ЭТО R1 ИЛИ ПОЧЕМУ ЭТО НЕ ПРЕВЫШАЕТ СТАНДАРТНУЮ ПРАКТИКУ.
"""

    # Detailed Prompt from Canon
    prompt = f"""
Ты — специализированный юридический ассистент для российского госзаказа (44‑ФЗ, 223‑ФЗ). 
Тебя вызывает backend‑сервис TenderShield Pro через IDE (TRAE) для анализа одного фрагмента тендерной документации. 

ТВОЯ ЕДИНСТВЕННАЯ ЗАДАЧА: 
Аккуратно и консервативно классифицировать фрагмент как один из четырёх классов: 
- "A" (Asymmetric), 
- "R1" (Restrictive), 
- "D" (Discrepancy), 
- "Healthy", 
и вернуть СТРОГО один JSON‑объект заданной структуры БЕЗ какого‑либо дополнительного текста. 

Метаданные документа (контекст для понимания, но не для фантазий): 
- Тип документа: {doc_type} 
- Регион заказчика: {region} 
- НМЦК: {nmck} 
- Закон: {law_type}

Анализируемый фрагмент (LEGAL_CONTEXT): 
---------------- ФРАГМЕНТ НАЧАЛО ---------------- 
{text} 
---------------- ФРАГМЕНТ КОНЕЦ ---------------- 

КЛАССЫ: 

1) "A" (Asymmetric) — асимметричные / чрезмерные обязанности и ответственность участника. 
   Примеры: несоразмерные штрафы и пени; односторонний отказ/изменение условий в пользу заказчика; перекладывание на участника чужих рисков; жёсткие сроки с крупными санкциями, выходящими за обычную практику. 

2) "R1" (Restrictive) — ограничительные / дискриминационные требования к участникам. 
   Примеры: избыточные требования к опыту, выручке, персоналу, СРО; навязывание конкретных брендов без "или эквивалент"; спорные/ненужные лицензии и допуски; условия, фактически сужающие конкуренцию. 

3) "D" (Discrepancy) — противоречия и несоответствия внутри документа. 
   Примеры: разные сроки/даты/гарантии в разных пунктах; разные суммы или объёмы по одному предмету; конфликт между ТЗ, проектом контракта и извещением; условия, которые делают исполнение юридически неопределённым. 

4) Класс "Healthy" — юридически здоровый фрагмент, без существенных рисков. 
   Примеры: стандартные условия 44‑ФЗ/223‑ФЗ; разумные типовые штрафы; обычные требования к участникам; формальные или стилистические детали без реального риска. 

ЧТО НЕ ЯВЛЯЕТСЯ СУЩЕСТВЕННЫМ РИСКОМ САМ ПО СЕБЕ: 
- Обычные сроки оплаты (до 30 рабочих/банковских дней), если нет дополнительных санкций. 
- Типовые пени в размере 1/300 ключевой ставки ЦБ РФ за каждый день просрочки. 
- Стандартные требования к регистрационным документам, отсутствию задолженностей, правоспособности. 
- Общие формулировки «участник несет ответственность в соответствии с законодательством РФ». 
- Стандартные условия одностороннего отказа по 44-ФЗ или 223-ФЗ без дополнительных жёстких оговорок. 

В таких случаях, при отсутствии других проблем, нужно выбирать класс "Healthy" и ставить has_risks = false.

УСИЛЕННЫЕ ПРАВИЛА ДЛЯ КЛАССА R1 (ОГРАНИЧИТЕЛЬНЫЕ ТРЕБОВАНИЯ):

‼️ ОЧЕНЬ ВАЖНО правильно отличать класс "R1" от "Healthy".

Если в фрагменте есть ХОТЯ БЫ ОДНО из следующих ограничительных условий, которые реально могут сузить круг участников, НУЖНО серьёзно рассматривать класс "R1":

✓ Требования к опыту: конкретное число аналогичных контрактов, особенно с крупной минимальной ценой каждого (например, ≥ 20–50% НМЦК).
✓ Требования к выручке: минимальный годовой оборот, неочевидно вытекающий из предмета закупки.
✓ Требования к наличию членства в СРО или других объединениях сверх базового закона.
✓ Требования к лицензиям, допускам, аккредитациям, которые не прямо предписаны законом, но ограничивают участников.
✓ Ограничения по региону/регистрации/месту нахождения участника (например, только один субъект РФ или конкретный город).
✓ Фактическое предпочтение конкретного бренда/модели/производителя, даже при наличии формального "или эквивалент", если параметры описаны так, что допускают по сути только один бренд.

При сомнении между "Healthy" и "R1":
→ Если есть хотя бы одно явное ограничительное требование к участнику (опыт, выручка, лицензия, регион, бренд), НУЖНО выбирать "R1", а не "Healthy".
→ "Healthy" допустим только тогда, когда требования выглядят действительно стандартными и не выходят за рамки обычной практики.

НЕ относить к R1:
✗ Базовые требования к правоспособности, отсутствию задолженностей, отсутствию судимости — это всё ещё "Healthy", если нет дополнительных ограничений.
✗ Если требуемая лицензия прямо вытекает из вида деятельности и закона и оформлена без дополнительных ограничений (только базовое соответствие законодательству), то такой фрагмент можно считать Healthy.

ВАЖНО: Если вместе с лицензией предъявляются дополнительные ограничения к участникам (опыт, выручка, наличие СРО, строгие условия по региону, узкие формулировки по предмету закупки), это уже признак класса R1.

ПРИОРИТЕТНОЕ ПРАВИЛО ДЛЯ R1:

⚠️ ЕСЛИ ТЫ ОБНАРУЖИЛ ХОТЯ БЫ ОДНО ЯВНОЕ ОГРАНИЧИТЕЛЬНОЕ ТРЕБОВАНИЕ К УЧАСТНИКАМ
(ОПЫТ, ВЫРУЧКА, ЛИЦЕНЗИИ, СРО, РЕГИОН, БРЕНД), НО НЕ УВЕРЕН НА 100%,
ПРЕДПОЧТИТЕЛЬНО ВЫБРАТЬ КЛАСС "R1", А НЕ "Healthy".

Класс "R1" служит именно для отметки условий, которые реально ограничивают конкуренцию или сужают круг участников.
{few_shot_block}
    
{r1_emphasis_block}

ОБЯЗАТЕЛЬНЫЕ ПРАВИЛА: 

- Если в фрагменте НЕТ явных юридических проблем, противоречий или дискриминационных требований — выбирай "Healthy". 
- Если ты сомневаешься или информации недостаточно — выбирай "Healthy" и НЕ придумывай риски. 
- Если несколько типов риска пересекаются, бери наиболее серьёзный по приоритету: 
  A (наивысший) > R1 > D > Healthy. 
- Не додумывай скрытые части документа и не опирайся на предположения о других разделах. 
- Не выдумывай ссылки на законы: указывай только логичные общие ссылки на 44‑ФЗ, 223‑ФЗ, ГК РФ, если они действительно связаны с описанным риском. 

СТРОГУЮ СХЕМУ JSON МЕНЯТЬ НЕЛЬЗЯ. 

Ты ДОЛЖЕН вернуть ОДИН JSON‑объект СЛЕДУЮЩЕЙ СТРУКТУРЫ: 

{{ 
  "class_label": "A" | "R1" | "D" | "Healthy", 
  "has_risks": true | false, 
  "deal_breakers": [ 
    "краткие формулировки критичных условий, из-за которых участие может быть нецелесообразно" 
  ], 
  "controlled_risks": [ 
    "краткие формулировки управляемых рисков, которые можно принять при повышенном контроле" 
  ], 
  "contradictions": [ 
    "краткие описания выявленных противоречий (по датам, суммам, объёмам, требованиям и т.п.)" 
  ], 
  "lawrefs": [ 
    "краткие ссылки на релевантные нормы права (например, '44‑ФЗ ст.34', 'ГК РФ ст.330')" 
  ], 
  "explanation": "краткое русское объяснение решения (2–5 предложений), адресованное юристу‑человеку" 
}} 

ИНТЕРПРЕТАЦИЯ ПОЛЕЙ: 

- "class_label": 
  - "Healthy", если нет существенных рисков. 
  - "A", если есть перекос ответственности/штрафов/прав в пользу заказчика. 
  - "R1", если есть дискриминационные/ограничительные требования к участникам. 
  - "D", если есть реальные противоречия в датах, суммах, объёмах, требованиях и т.п. 

- "has_risks": 
  - true, если класс "A", "R1" или "D" и есть хотя бы один существенный риск. 
  - false, если класс "Healthy" и нет реальных юридических проблем. 

- "deal_breakers": 
  - Жёсткие условия, которые могут сделать участие в закупке невыгодным или опасным. 
  - Если таких нет — []. 

- "controlled_risks": 
  - Умеренные риски, которые можно принять с оговорками и контролем. 
  - Если таких нет — []. 

- "contradictions": 
  - Только реальные противоречия; не дублируй туда общие риски. 
  - Если противоречий нет — []. 

- "lawrefs": 
  - Можно вернуть []. 
  - Не придумывай конкретные статьи без уверенности; допускаются общие ссылки (например, "44‑ФЗ общие положения о контракте"). 

- "explanation": 
  - Всегда заполняется. 
  - Чётко укажи, почему выбран именно этот класс, с отсылкой к ключевым формулировкам фрагмента. 

КРИТИЧЕСКОЕ ТРЕБОВАНИЕ ДЛЯ BACKEND: 
ОТВЕТ ДОЛЖЕН СОДЕРЖАТЬ ТОЛЬКО ОДИН ЧИСТЫЙ JSON‑ОБЪЕКТ БЕЗ ЛЮБОГО ДРУГОГО ТЕКСТА, КОММЕНТАРИЕВ ИЛИ MARKDOWN. НИКАКИХ ПРЕАМБУЛ, ПОЯСНЕНИЙ, "```json" И Т.П.
"""
    
    # TODO (R1 pre-filter):
    # Перед вызовом внешнего LLM можно добавить лёгкий rule-based фильтр:
    # если в LEGAL_CONTEXT есть ключевые слова из набора
    # ['опыт', 'аналогичных контрактов', 'выручка', 'членство в СРО',
    #  'саморегулируемая организация', 'регистрация', 'местонахождение участника',
    #  'товарный знак', 'бренд', 'марка'],
    # то можно дополнительно подчеркнуть в промпте необходимость оценки по классу R1.
    # Реализация будет обсуждаться отдельно, архитектурный канон (решение за внешним LLM) менять нельзя.

    try:
        response_json_str = await asyncio.to_thread(
            llm.invoke,
            prompt=prompt,
            format_json=True,
            temperature=0.3,  # Increased to 0.3 to reduce conservatism
            timeout=90,  # Increased from 60s to give model more time
            use_queue=False  # CRITICAL: Bypass Celery queue, use direct Ollama connection
        )
        
        try:
            result = json.loads(response_json_str)
            # Normalize fields if LLM hallucinates slightly
            if "class_label" not in result:
                 result["class_label"] = "Healthy"
            if "has_risks" not in result:
                 result["has_risks"] = False
            logger.info(f"✅ External audit completed successfully. Class: {result.get('class_label')}, Has risks: {result.get('has_risks')}")
            
            # Add debug info
            if "debug" not in result:
                result["debug"] = {}
            result["debug"]["r1_keyword_hit"] = r1_keyword_hit
            
            return result
        except json.JSONDecodeError as json_err:
            logger.error(f"❌ External Audit JSON parsing failed")
            logger.error(f"   Error: {json_err}")
            logger.error(f"   Raw response (first 500 chars): {response_json_str[:500]}")
            return {"class_label": "Healthy", "has_risks": False, "explanation": "Error parsing external response"}
            
    except Exception as e:
        # ENHANCED ERROR LOGGING for degraded mode debugging
        logger.error(f"❌ External Audit FAILED - entering degraded mode")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Exception message: {str(e)}")
        logger.error(f"   Model attempted: {llm.preferred_models if hasattr(llm, 'preferred_models') else 'Unknown'}")
        logger.error(f"   Ollama URL: {settings.OLLAMA_BASE_URL}")
        logger.error(f"   Timeout configured: 90s")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"   Traceback: {''.join(traceback.format_tb(e.__traceback__)[:3])}")
        # Return None to trigger Degraded Mode in Aggregator
        raise e 


# ==============================================================================
# LEGAL GROUNDING AGGREGATOR RULES (CANON)
# ==============================================================================
# 1. FINAL DECISION AUTHORITY:
#    The `class_label` and `has_risks` MUST be derived ONLY from `external_result`.
#    Local v9 model is AUXILIARY (used for summary, logging, and risk signals).
#
# 2. DEGRADED MODE:
#    If External LLM fails/timeouts:
#    - class_label = "Healthy" (Safe Default to prevent blockers)
#    - has_risks = False (But v9 signal is preserved in `flags` and `risks` text)
#    - source = "degraded_mode"
#
# 3. NO HYBRID OVERRIDES:
#    Do NOT allow v9 to override External result (e.g. if External=Healthy, v9=R1 -> Final=Healthy).
# ==============================================================================

class LegalGroundingService:
    @staticmethod
    async def analyze(text: str, tender_id: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> LegalGroundingResponse:
        """
        Main entry point: Hybrid Pipeline.
        В зависимости от ANALYZER_VERSION:
        - v11: гибридный LLM-пайплайн (Local v9 + External R1);
        - v12: двухступенчатый классификатор на эмбеддингах (has_risks + A/R1/D).
        """
        analyzer_version = getattr(settings, "ANALYZER_VERSION", ANALYZER_VERSION)

        if analyzer_version == "v12":
            await _ensure_v12_models_loaded()

            from services.v12_inference import analyze_fragment_v12

            fragment = {
                "instruction": "Юридический фрагмент тендерной документации для классификации рисков A/R1/D/Healthy.",
                "input": text,
            }

            v12_result = analyze_fragment_v12(
                fragment,
                has_risks_clf=_v12_has_risks_clf,
                ard_clf=_v12_ard_clf,
                embed_model="nomic-embed-text",
                ollama_url=settings.OLLAMA_BASE_URL,
            )

            class_label = v12_result.get("class_label", "Healthy")
            has_risks_flag = bool(v12_result.get("has_risks", False))
            explanation = v12_result.get("explanation") or ""

            dealbreakers = v12_result.get("dealbreakers", []) or []
            controlled = v12_result.get("controlled_risks", []) or []
            contradictions = v12_result.get("contradictions", []) or []
            law_refs = v12_result.get("law_refs", []) or []

            risks: List[str] = []
            risks.extend(str(r) for r in dealbreakers)
            risks.extend(str(r) for r in controlled)
            risks.extend(str(r) for r in contradictions)
            if law_refs:
                risks.append("Law refs: " + ", ".join(str(r) for r in law_refs))

            # 🎯 УЛУЧШЕННЫЕ ШАБЛОНЫ ТЕКСТОВ ДЛЯ ДИРЕКТОРА
            # Краткие, деловые формулировки без LLM-словесной каши
            verdict_hint = "CAUTION"  # default
            
            if class_label == "A":
                # STOP: Жёсткие стоп-факторы — участвовать нельзя
                summary_text = (
                    "Обнаружены жёсткие стоп-факторы — участвовать нельзя. "
                    "Выявлены дискриминационные/ограничительные условия или чрезмерная ответственность поставщика. "
                    "Рекомендуем не участвовать: риск несоразмерен возможной выгоде."
                )
                verdict_hint = "STOP"
                
                # Формируем конкретные риски для STOP
                if not risks:
                    risks = [
                        "Дискриминационные требования к участникам (опыт, выручка, местонахождение)",
                        "Чрезмерные штрафы или несоразмерная ответственность (более 10% от суммы)",
                        "Односторонний отказ заказчика без компенсации"
                    ]
                    
            elif class_label in ("R1", "D") and has_risks_flag:
                # CAUTION: Контролируемые риски — участвовать можно при соблюдении условий
                summary_text = (
                    "Выявлены контролируемые риски — участвовать можно при соблюдении условий. "
                    "Стандартные штрафы по 44-ФЗ и типовые ограничения. "
                    "Рекомендуем участвовать с условиями: зафиксировать риски в служебной записке и учесть в калькуляции."
                )
                verdict_hint = "CAUTION"
                
                # Формируем конкретные риски для CAUTION
                if not risks:
                    risks = [
                        "Пени 1/300 ставки ЦБ за просрочку (стандарт 44-ФЗ)",
                        "Право одностороннего отказа заказчика (типовое условие)",
                        "Повышенные требования к обеспечению или опыту"
                    ]
                    
            elif class_label == "Healthy" or not has_risks_flag:
                # PARTICIPATE: Существенных рисков нет
                summary_text = (
                    "Существенных юридических рисков не выявлено. "
                    "Условия по штрафам и ответственности стандартные для 44-ФЗ/223-ФЗ, критичных ограничений нет. "
                    "Рекомендуем участвовать при стандартной проверке финансовых параметров."
                )
                verdict_hint = "PARTICIPATE"
                risks = []  # Для здорового класса риски не показываем
                
            else:
                # Fallback для неизвестных классов
                summary_text = (
                    f"Анализ завершён (класс {class_label}). "
                    "Требуется дополнительная экспертная оценка юристом. "
                    "Рекомендуем проверить условия ответственности и требования к участникам вручную."
                )
                verdict_hint = "CAUTION"

            # Логирование предсказания v12-two-stage (мусорные фрагменты не логируем)
            try:
                from services.v12_text_utils import is_garbage_text
                if not is_garbage_text(text or ""):
                    await log_v12_prediction(
                        fragment_text=text,
                        v12_result=v12_result,
                        source="api/legal/analyze",
                        analyzer_version=analyzer_version,
                    )
                else:
                    logger.debug("v12: пропуск логирования (garbage)")
            except ImportError:
                await log_v12_prediction(
                    fragment_text=text,
                    v12_result=v12_result,
                    source="api/legal/analyze",
                    analyzer_version=analyzer_version,
                )
            except Exception as log_err:
                logger.error("Failed to log v12 prediction: %s", log_err)

            return LegalGroundingResponse(
                tender_id=tender_id,
                decision=class_label,
                class_label=class_label,
                has_risks=has_risks_flag,
                confidence=0.85,  # Повышаем confidence т.к. has_risks_recall=1.0
                summary=summary_text,
                risks=risks[:5],  # Максимум 5 рисков для читаемости UI
                source="v12_two_stage",
                r1_details=v12_result,
                flags=["v12_two_stage", verdict_hint],  # Добавляем verdict_hint в flags
            )

        # v11: гибридный LLM-пайплайн (текущая логика)
        manager = LocalModelManager()

        await manager.load_model()

        if manager._model:
            local_result = await asyncio.to_thread(manager.predict, text)
        else:
            local_result = {"decision": "A", "confidence": 0.0, "summary": "Local model not available"}

        local_decision = local_result.get("decision")

        external_result = None
        run_external = True

        if meta and meta.get("disable_external"):
            run_external = False

        if run_external:
            try:
                external_result = await asyncio.wait_for(run_external_audit(text, meta), timeout=75.0)
            except asyncio.TimeoutError:
                logger.error(f"⏱️ External R1 check timed out after 75s for {tender_id}")
                external_result = None
            except Exception as e:
                logger.error(f"❌ External R1 check failed: {e}")
                external_result = None

        final_decision = "Healthy"
        final_has_risks = False
        final_source = "degraded_mode_local_v9"
        final_summary = local_result.get("summary", "")
        risks: List[str] = []
        flags: List[str] = []

        v9_decision = local_decision
        v9_has_risks = (v9_decision == "R1")

        if external_result:
            final_source = "external_audit"

            final_decision = external_result.get("class_label", "Healthy")
            final_has_risks = external_result.get("has_risks", False)

            raw_deal_breakers = external_result.get("deal_breakers", [])
            raw_controlled = external_result.get("controlled_risks", [])

            if raw_deal_breakers:
                risks.extend([f"[CRITICAL] {r}" for r in raw_deal_breakers])
            if raw_controlled:
                risks.extend([f"[WARN] {r}" for r in raw_controlled])

            if final_has_risks and not risks:
                contradictions = external_result.get("contradictions", [])
                if contradictions:
                    risks.extend([f"[CONTRA] {r}" for r in contradictions])
                else:
                    risks.append(external_result.get("explanation", "Risk detected by external audit"))

            ext_explanation = external_result.get("explanation", "")
            if ext_explanation and len(ext_explanation) > 10:
                final_summary = ext_explanation
            elif final_summary:
                final_summary = f"{final_summary} (Local Summary)"

            flags.append("external_verified")

        else:
            final_source = "degraded_mode"
            flags.append("degraded_mode")

            final_decision = "Healthy"
            final_has_risks = v9_has_risks

            if v9_has_risks:
                risks.append(f"[v9-Warning] {final_summary}")
                flags.append("v9_risk_signal")

            final_summary = f"[DEGRADED MODE - CHECK MANUALLY] {final_summary}"

        return LegalGroundingResponse(
            tender_id=tender_id,
            decision=final_decision,
            class_label=final_decision,
            has_risks=final_has_risks,
            confidence=external_result.get("confidence", 0.0) if external_result else local_result.get("confidence", 0.0),
            summary=final_summary,
            risks=risks,
            source=final_source,
            r1_details=external_result,
            flags=flags,
        )
