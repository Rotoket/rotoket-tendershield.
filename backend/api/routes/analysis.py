"""
Минимальный analysis router для тестирования и комплексного аудита.
Содержит логику для /analyze-package (тест) и /package-audit (PROD/DEMO).
"""
import logging
import asyncio
import uuid
import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status
from sqlalchemy.orm import Session

# Локальные импорты (с fallback)
try:
    from backend.database import (
        get_db, User, PackageAnalysis, Usage, SessionLocal, Analysis, 
        PackageAnalysis, Usage
    )
    # Попытка импорта auth dependency (если существует)
    # Обычно это get_current_user или get_optional_user
    # Создадим заглушку если нет
    def get_optional_user():
        return None
except ImportError:
    # Fallback для тестов без БД
    def get_db():
        yield None
    class User:
        id = 1
    class PackageAnalysis:
        pass
    class Usage:
        pass
    def get_optional_user():
        return None # Demo mode mostly

# v12 LegalGroundingService для юридического анализа фрагментов
try:
    from services.legal_grounding import LegalGroundingService
    _legal_grounding_available = True
except ImportError:
    _legal_grounding_available = False

# Подготовка текста для v12 и фильтрация мусора
try:
    from services.v12_text_utils import (
        is_garbage_text,
        get_readable_start_for_v12,
    )
    _v12_text_utils_available = True
except ImportError:
    _v12_text_utils_available = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])

# Глобальный кэш для тестирования
ANALYSIS_CACHE = {}

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Извлекает текст из файла. Для DOCX/PDF/XLSX использует нормальные экстракторы,
    чтобы в первые 3000 символов попадал человеко-читаемый текст, а не бинарные заголовки.
    """
    ext = os.path.splitext(filename or "")[1].lower()
    try:
        if ext in (".docx", ".doc"):
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
                return "\n".join(d.page_content for d in docs) if docs else ""
            except Exception as e:
                logger.debug("Docx2txtLoader failed for %s: %s", filename, e)
        if ext == ".pdf":
            try:
                from langchain_community.document_loaders import PyMuPDFLoader
                loader = PyMuPDFLoader(file_path)
                docs = loader.load()
                return "\n".join(d.page_content for d in docs) if docs else ""
            except Exception as e:
                logger.debug("PyMuPDFLoader failed for %s: %s", filename, e)
        if ext in (".xlsx", ".xls"):
            try:
                import pandas as pd
                xls = pd.ExcelFile(file_path)
                parts = []
                for sheet in xls.sheet_names:
                    df = pd.read_excel(xls, sheet_name=sheet)
                    parts.append(f"--- {sheet} ---\n{df.to_string(index=False)}")
                return "\n\n".join(parts)
            except Exception as e:
                logger.debug("Excel read failed for %s: %s", filename, e)
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
    except Exception as e:
        logger.warning("Extract text failed for %s: %s", filename, e)
    try:
        with open(file_path, "rb") as f:
            content = f.read(1024 * 10)
        return content.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error("Error reading file %s: %s", filename, e)
        return ""

def analyze_single_document_improved(document_text: str, nmck: Any = None, industry: str = "UNIVERSAL") -> Dict[str, Any]:
    """
    Симуляция улучшенного анализа документа.
    """
    # Эвристика на основе ключевых слов для демо
    text_lower = document_text.lower()
    
    score = 85
    verdict = "PARTICIPATE"
    risks = []
    
    if "штраф" in text_lower or "penalty" in text_lower:
        score -= 10
        risks.append({
            "title": "Высокие штрафные санкции",
            "description": "Обнаружены упоминания штрафов, требующие внимания.",
            "severity": "MEDIUM",
            "financial_impact_rubles": 50000
        })
    
    if "расторжение" in text_lower:
        score -= 20
        verdict = "CAUTION"
        risks.append({
            "title": "Риск расторжения контракта",
            "description": "Упоминаются условия расторжения в одностороннем порядке.",
            "severity": "HIGH", 
            "financial_impact_rubles": 0
        })

    if "неустойка" in text_lower:
        risks.append({
            "title": "Неустойка за просрочку",
            "description": "Стандартная неустойка за нарушение сроков.",
            "severity": "LOW",
            "financial_impact_rubles": 10000
        })

    return {
        "verdict": verdict,
        "score": max(0, score),
        "financial_impact": {
            "risks_total": sum(r.get("financial_impact_rubles", 0) for r in risks),
            "margin_prob": "HIGH" if score > 70 else "MEDIUM"
        },
        "deal_breakers": risks,
        "summary": "Автоматический анализ документа завершен."
    }

def extract_global_issues(all_risks: List[dict], documents: List[dict]) -> List[dict]:
    """
    Анализирует риски во всех документах и выделяет глобальные проблемы
    """
    global_issues = []
    
    # Группируем риски по типам
    risk_groups = {}
    for risk in all_risks:
        title = risk.get("title", "Unknown")
        if title not in risk_groups:
            risk_groups[title] = []
        risk_groups[title].append(risk)
    
    # Если риск встречается в нескольких документах = глобальный
    for title, risks in risk_groups.items():
        if len(risks) > 1:  # Встречается в нескольких документах
            global_issues.append({
                "type": "CROSS_DOCUMENT_RISK",
                "title": f"ВНИМАНИЕ: {title}",
                "description": f"Обнаружено в {len(risks)} документах",
                "severity": max([r.get("severity", "MEDIUM") for r in risks]),
                "severity_level": "CONTROLLED_RISK", # Добавлено для фронтенда
                "affected_documents": [r.get("source_file") for r in risks],
                "count": len(risks)
            })
    
    # Добавляем высокорисковые элементы
    for risk in all_risks:
        if risk.get("severity") == "CRITICAL" or risk.get("severity") == "HIGH":
            global_issues.append({
                "type": "CRITICAL_RISK",
                "title": risk.get("title", "Критический риск"),
                "description": risk.get("description", ""),
                "severity": risk.get("severity"),
                "severity_level": "DEAL_BREAKER" if risk.get("severity") == "CRITICAL" else "CONTROLLED_RISK",
                "source": risk.get("source_file"),
                "financial_impact": risk.get("financial_impact_rubles", 0)
            })
    
    # Сортируем по важности
    global_issues.sort(
        key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(
            x.get("severity", "MEDIUM"), 99
        )
    )
    
    return global_issues[:10]  # Макс 10 глобальных рисков


# --- ENDPOINTS ---

from app.services.pipeline.orchestrator import dir_orchestrator
from app.db.history import history_db, TenderHistoryItem

@router.get("/history", response_model=List[TenderHistoryItem])
async def get_tender_history():
    """Returns recent tender analysis history"""
    return await history_db.get_recent()

@router.post("/analyze-package")
async def analyze_package_test(
    files: List[UploadFile] = File(...),
    industry: str = Form("UNIVERSAL"),
    mode: str = Form("legacy") # New parameter: legacy or dir
):
    """
    Тестовый эндпоинт. Поддерживает режимы:
    - 'legacy': возвращает старый формат MOCK
    - 'dir': запускает реальный DIR Pipeline
    """
    analysis_id = str(uuid.uuid4())
    
    ANALYSIS_CACHE[analysis_id] = {
        "status": "processing",
        "createdAt": datetime.utcnow()
    }
    
    async def run():
        if mode == "dir":
            # Real AI Pipeline
            try:
                dir_result_dict = await dir_orchestrator.build_dir_pipeline(files)

                # Convert dict back to Pydantic for DB saving
                from backend.app.types.dir import DIR
                dir_obj = DIR.model_validate(dir_result_dict)
                
                # Save to History
                await history_db.add_record(dir_obj)
                
                # Wrap in legacy structure for frontend compatibility (optional)
                # Or just return raw DIR if frontend is updated.
                # Here we embed DIR into the legacy result structure
                result = {
                    "verdict": dir_result_dict["decision"]["verdict"],
                    "summaryScore": 0, # To be calculated based on risks
                    "documents": [],
                    "globalIssues": [],
                    "recommendations": [dir_result_dict["decision"]["director_rationale"]],
                    "dir": dir_result_dict # ✅ NEW FIELD
                }
                
                ANALYSIS_CACHE[analysis_id] = {
                    "status": "done",
                    "result": result,
                    "createdAt": ANALYSIS_CACHE[analysis_id]["createdAt"]
                }
                logger.info(f"✅ DIR Analysis {analysis_id} completed")
                
            except Exception as e:
                logger.error(f"❌ DIR Analysis failed: {e}")
                ANALYSIS_CACHE[analysis_id] = {"status": "error", "error": str(e)}
                
        else:
            # Legacy Mock Logic
            await asyncio.sleep(2) 
            result = {
                "verdict": "PARTICIPATE",
                "summaryScore": 88,
                "documents": [
                    {
                        "filename": file.filename,
                        "score": 88,
                        "verdict": "PARTICIPATE",
                        "risks": [],
                        "opportunities": []
                    }
                    for file in files
                ],
                "globalIssues": [],
                "recommendations": ["Тестовый анализ пройден успешно (MOCK)"]
            }
            
            ANALYSIS_CACHE[analysis_id] = {
                "status": "done",
                "result": result,
                "createdAt": ANALYSIS_CACHE[analysis_id]["createdAt"]
            }
            logger.info(f"✅ TEST: Analysis {analysis_id} completed (Mock)")
    
    asyncio.create_task(run())
    
    return {
        "analysisId": analysis_id,
        "status": "queued"
    }

@router.get("/analysis/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Проверка статуса анализа (для MOCK)"""
    if analysis_id in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[analysis_id]
    
    raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

@router.post("/package-audit")
async def package_audit(
    files: List[UploadFile] = File(...),
    industry: str = Form("general"),
    # current_user: Optional[User] = Depends(get_optional_user), # Временно отключено если auth не настроен
    db: Session = Depends(get_db)
):
    """
    Комплексный анализ пакета документов (MAIN LOGIC).
    Заменяет старый endpoint.
    """
    # Mock user for now to avoid dependency issues during restoration
    current_user = None 
    
    try:
        is_demo = current_user is None
        
        # if not is_demo:
        #     can_analyze, error_msg = check_user_can_analyze(current_user, db)
        #     if not can_analyze:
        #         raise HTTPException(
        #             status_code=status.HTTP_402_PAYMENT_REQUIRED,
        #             detail=error_msg
        #         )
        
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Не загружены файлы"
            )
        
        # ✅ ВАЖНО: Анализируем каждый документ
        documents = []
        all_risks = []  # Для глобальных рисков
        total_score = 0
        garbage_skipped_count = 0
        garbage_examples = []  # до 2 примеров для DEBUG

        for file in files:
            try:
                # Сохраняем файл временно
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    # Читаем чанками
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = tmp.name
                
                try:
                    # Извлекаем текст
                    document_text = extract_text_from_file(tmp_path, file.filename)
                    
                    # ✅ Анализируем документ
                    doc_result = analyze_single_document_improved(
                        document_text=document_text,
                        nmck=None,
                        industry=industry
                    )
                    
                    # ✅ v12 Legal Grounding — юридический анализ через v12 классификатор
                    legal_grounding_data = None
                    if _legal_grounding_available and document_text and len(document_text.strip()) >= 50:
                        text_for_v12 = (
                            get_readable_start_for_v12(document_text, 3000)
                            if _v12_text_utils_available
                            else document_text[:3000]
                        )
                        is_garbage = (
                            _v12_text_utils_available and is_garbage_text(text_for_v12)
                        )
                        if is_garbage:
                            garbage_skipped_count += 1
                            if len(garbage_examples) < 2:
                                garbage_examples.append(
                                    (file.filename, (text_for_v12 or "")[:200])
                                )
                            logger.debug(
                                "v12: пропуск фрагмента (garbage), файл %s",
                                file.filename,
                            )
                        else:
                            try:
                                lg_result = await LegalGroundingService.analyze(
                                    text=text_for_v12,
                                    tender_id=f"pkg_{file.filename}",
                                )
                                legal_grounding_data = lg_result.model_dump()

                                v12_flags = legal_grounding_data.get("flags", [])
                                if "STOP" in v12_flags:
                                    doc_result["verdict"] = "STOP"
                                    doc_result["score"] = max(
                                        0, doc_result.get("score", 0) - 40
                                    )
                                elif "CAUTION" in v12_flags and doc_result.get("verdict") == "PARTICIPATE":
                                    doc_result["verdict"] = "CAUTION"
                                    doc_result["score"] = max(
                                        0, doc_result.get("score", 0) - 15
                                    )

                                logger.info(
                                    "✅ v12 Legal Grounding для %s: class=%s, flags=%s",
                                    file.filename,
                                    legal_grounding_data.get("class_label"),
                                    v12_flags,
                                )
                            except Exception as lg_err:
                                logger.warning(
                                    "⚠️ v12 Legal Grounding failed для %s: %s",
                                    file.filename,
                                    lg_err,
                                )
                    
                    # Формируем структуру документа для ответа
                    doc_entry = {
                        "id": f"doc_{len(documents)}",
                        "filename": file.filename,
                        "verdict": doc_result.get("verdict", "UNKNOWN"),
                        "score": doc_result.get("score", 0),
                        "financial_impact": doc_result.get("financial_impact", {}),
                        "key_risks": doc_result.get("deal_breakers", [])[:3],  # Топ-3 риска
                        "analysis_date": datetime.utcnow().isoformat(),
                         # Доп поля для фронтенда TenderAnalysis.tsx
                        "risks": doc_result.get("deal_breakers", []),
                        "opportunities": []
                    }
                    # Прокидываем legalGrounding в ответ документа для фронтенда
                    if legal_grounding_data:
                        doc_entry["legalGrounding"] = legal_grounding_data
                    documents.append(doc_entry)
                    
                    total_score += doc_result.get("score", 0)
                    
                    # Собираем все риски для глобального анализа
                    if "deal_breakers" in doc_result:
                        for risk in doc_result["deal_breakers"]:
                            risk["source_file"] = file.filename
                            all_risks.append(risk)
                    
                    logger.info(f"✅ Анализ документа: {file.filename} -> {doc_result.get('verdict')}")
                    
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                        
            except Exception as e:
                logger.error(f"❌ Ошибка анализа файла {file.filename}: {e}")
                documents.append({
                    "id": f"doc_error_{len(documents)}",
                    "filename": file.filename,
                    "verdict": "ERROR",
                    "error": str(e),
                    "score": 0,
                    "risks": [],
                    "opportunities": []
                })
                continue

        if garbage_skipped_count > 0:
            logger.debug(
                "v12: в пакете отфильтровано как garbage фрагментов: %s",
                garbage_skipped_count,
            )
            for fname, sample in garbage_examples:
                logger.debug(
                    "v12 garbage example filename=%s sample=%s",
                    fname,
                    (sample or "")[:120],
                )

        # ✅ Анализируем глобальные риски (кросс-документные)
        global_issues = extract_global_issues(all_risks, documents)
        
        # Рассчитываем итоговый вердикт
        if any(doc["verdict"] == "STOP" for doc in documents if "verdict" in doc):
            summary_verdict = "STOP"
        elif any(doc["verdict"] == "CLARIFY" or doc["verdict"] == "CAUTION" for doc in documents if "verdict" in doc):
            summary_verdict = "CAUTION" # CAUTION для фронта (там нет CLARIFY)
        else:
            summary_verdict = "PARTICIPATE"
        
        # Рассчитываем итоговый скор
        avg_score = total_score / len(documents) if documents else 0
        
        # Сохраняем пакетный анализ в БД
        package_id = f"pkg_{uuid.uuid4().hex[:12]}"
        
        # Пытаемся сохранить в БД если есть подключение и модель PackageAnalysis
        if db and not is_demo:
            try:
                # Адаптация под модель PackageAnalysis в database.py
                package = PackageAnalysis(
                    user_id=getattr(current_user, 'id', 1),
                    package_id=package_id,
                    summary_score=int(avg_score),
                    verdict=summary_verdict,
                    documents_json=documents,
                    global_issues=global_issues,
                    created_at=datetime.utcnow()
                )
                db.add(package)
                # Usage update omitted for brevity/safety in fix
                db.commit()
                logger.info(f"✅ Пакетный анализ сохранен в БД: {package_id}")
            except Exception as e:
                logger.error(f"⚠️ Не удалось сохранить в БД: {e}")
        
        # ✅ Прокидываем наиболее критичный legalGrounding на верхний уровень
        # (приоритет: STOP > CAUTION > PARTICIPATE)
        top_legal_grounding = None
        for doc in documents:
            doc_lg = doc.get("legalGrounding")
            if not doc_lg:
                continue
            doc_flags = doc_lg.get("flags", [])
            if "STOP" in doc_flags:
                top_legal_grounding = doc_lg
                break  # STOP — максимальный приоритет
            if top_legal_grounding is None or "CAUTION" in doc_flags:
                top_legal_grounding = doc_lg
        
        # ✅ ВАЖНО: Возвращаем полный результат
        result = {
            "packageId": package_id,
            "summaryScore": int(avg_score),
            "verdict": summary_verdict,
            "documents": documents,  # ← ТЕПЕРЬ ЗАПОЛНЕНО!
            "globalIssues": global_issues,  # ← ТЕПЕРЬ ЗАПОЛНЕНО!
            "analysisDate": datetime.utcnow().isoformat(),
            "filesCount": len(files)
        }
        # ✅ v12: прокидываем legalGrounding на верхний уровень
        if top_legal_grounding:
            result["legalGrounding"] = top_legal_grounding
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка пакетного анализа: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при анализе пакета: {str(e)}"
        )
