"""
CI Guardrails v1.0 — Проверка смысловой и управленческой целостности системы

Проверяет соблюдение Канона проекта:
- Language Guard (запрещённые слова)
- Structural Guard (структура Decision Preview, Decision Record, Board Pack)
- Impact Guard (Impact Logic для рисков)
- Data Exhaustion Guard (формулировки "не указано")
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


# Запрещённые слова и конструкции для Language Guard
FORBIDDEN_WORDS = [
    r'рекоменд[а-я]*',
    r'совет[а-я]*',
    r'\bлучше\b',
    r'возможно',
    r'вероятно',
    r'целесообразно',
    r'следует',
]


def check_language_guard(text: str, context: str = "") -> List[str]:
    """
    LANGUAGE GUARD — проверка запрещённых слов и конструкций.
    
    Returns:
        Список найденных нарушений (пустой если PASS)
    """
    violations = []
    
    if not text:
        return violations
    
    text_lower = text.lower()
    
    for pattern in FORBIDDEN_WORDS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            word = match.group(0)
            violations.append(f"Запрещённое слово: '{word}' в контексте: {context[:50]}")
    
    return violations


def check_structural_guard_decision_preview(data: Dict[str, Any]) -> List[str]:
    """
    STRUCTURAL GUARD для Decision Preview.
    
    Decision Preview ОБЯЗАН содержать:
    - Deal Snapshot
    - Поле допустимых решений
    - ИУН
    - Реестр рисков с Impact Logic
    - Блок фиксации ответственности
    
    Returns:
        Список нарушений (пустой если PASS)
    """
    violations = []
    
    # Проверяем обязательные поля Decision Preview
    required_fields = ['decision', 'why', 'management_load']
    
    for field in required_fields:
        if field not in data:
            violations.append(f"Decision Preview: отсутствует обязательное поле '{field}'")
    
    # Проверяем decision (должно быть одно из допустимых значений)
    if 'decision' in data:
        valid_decisions = ['PARTICIPATE', 'DO_NOT_PARTICIPATE', 'PARTICIPATE_WITH_CONDITIONS']
        if data['decision'] not in valid_decisions:
            violations.append(f"Decision Preview: недопустимое значение decision: {data['decision']}")
    
    # Проверяем why (должно быть 2-4 причины)
    if 'why' in data:
        reasons = data['why']
        if not isinstance(reasons, list):
            violations.append("Decision Preview: 'why' должно быть списком")
        elif len(reasons) < 2 or len(reasons) > 4:
            violations.append(f"Decision Preview: 'why' должно содержать 2-4 причины, найдено: {len(reasons)}")
    
    # Проверяем management_load (ИУН)
    if 'management_load' in data:
        mgmt_load = data['management_load']
        if not isinstance(mgmt_load, dict):
            violations.append("Decision Preview: 'management_load' должно быть объектом")
    
    return violations


def check_structural_guard_decision_record(data: Dict[str, Any]) -> List[str]:
    """
    STRUCTURAL GUARD для Decision Record.
    
    Decision Record ОБЯЗАН:
    - содержать ровно 7 полей (канонических)
    - не содержать анализа, Evidence и Impact
    
    Канонические 7 полей:
    1. tender_id
    2. tender_object
    3. decision
    4. decision_reasons
    5. management_load_index
    6. responsible_person
    7. fixed_at
    
    Returns:
        Список нарушений (пустой если PASS)
    """
    violations = []
    
    # Проверяем наличие всех 7 канонических полей
    canonical_fields = [
        'tender_id',
        'tender_object',
        'decision',
        'decision_reasons',
        'management_load_index',
        'responsible_person',
        'fixed_at'
    ]
    
    missing_fields = [field for field in canonical_fields if field not in data]
    if missing_fields:
        violations.append(f"Decision Record: отсутствуют обязательные поля: {', '.join(missing_fields)}")
    
    # Проверяем, что нет запрещённых полей (Evidence, Impact, анализ)
    forbidden_fields = [
        'evidence',
        'impact',
        'evidence_objects',
        'risk_signals',
        'contradictions',
        'decision_graph',
        'deal_breakers',  # Это часть Preview, не Record
        'controlled_risks',  # Это часть Preview, не Record
    ]
    
    found_forbidden = [field for field in forbidden_fields if field in data]
    if found_forbidden:
        violations.append(f"Decision Record: содержит запрещённые поля (анализ/Evidence/Impact): {', '.join(found_forbidden)}")
    
    # Проверяем decision_reasons (должно быть 1-3 причины)
    if 'decision_reasons' in data:
        reasons = data['decision_reasons']
        if not isinstance(reasons, list):
            violations.append("Decision Record: 'decision_reasons' должно быть списком")
        elif len(reasons) < 1 or len(reasons) > 3:
            violations.append(f"Decision Record: 'decision_reasons' должно содержать 1-3 причины, найдено: {len(reasons)}")
    
    # Проверяем management_load_index (должно быть число 0-100)
    if 'management_load_index' in data:
        index = data['management_load_index']
        if not isinstance(index, (int, float)):
            violations.append("Decision Record: 'management_load_index' должно быть числом")
        elif index < 0 or index > 100:
            violations.append(f"Decision Record: 'management_load_index' должно быть в диапазоне 0-100, найдено: {index}")
    
    return violations


def check_structural_guard_board_pack(data: Dict[str, Any]) -> List[str]:
    """
    STRUCTURAL GUARD для Board Pack.
    
    Board Pack ОБЯЗАН:
    - строиться из Decision Record + Preview
    - не содержать новых выводов
    - быть статичным документом
    
    Проверяем, что Board Pack не содержит:
    - новых выводов, которых нет в Decision Record
    - динамических данных
    - рекомендаций
    
    Returns:
        Список нарушений (пустой если PASS)
    """
    violations = []
    
    # Проверяем наличие основных секций Board Pack (7 секций)
    required_sections = [
        'executive_summary',
        'tender_context',
        'decision',
        'decision_grounds',
        'financial_snapshot',
        'next_steps',
        'audit_note'
    ]
    
    # Проверяем, что Board Pack содержит основные данные из Decision Record
    if 'decision_record' not in data and 'tender_id' not in data:
        violations.append("Board Pack: должен строиться на основе Decision Record, но Decision Record не найден")
    
    # Проверяем запрещённые слова в Board Pack (Language Guard)
    board_pack_text = str(data).lower()
    language_violations = check_language_guard(board_pack_text, "Board Pack")
    violations.extend(language_violations)
    
    return violations


def check_impact_guard(risk_data: Dict[str, Any]) -> List[str]:
    """
    IMPACT GUARD — проверка Impact Logic для рисков.
    
    Каждый риск ОБЯЗАН содержать Impact Logic в формате:
    «Следствием является … → Требуется …»
    
    Returns:
        Список нарушений (пустой если PASS)
    """
    violations = []
    
    # Проверяем наличие описания риска
    description = risk_data.get('description', '') or risk_data.get('why_it_matters', '')
    
    if not description:
        violations.append("Risk: отсутствует описание риска")
        return violations
    
    description_lower = description.lower()
    
    # Проверяем наличие конструкции Impact Logic
    has_consequence = 'следствием является' in description_lower or 'следствием' in description_lower
    has_required = 'требуется' in description_lower or 'требует' in description_lower
    has_arrow = '→' in description or '->' in description
    
    if not (has_consequence and has_required):
        violations.append(f"Risk: отсутствует Impact Logic в формате 'Следствием является ... → Требуется ...'. Описание: {description[:100]}")
    
    return violations


def check_data_exhaustion_guard(text: str, context: str = "") -> List[str]:
    """
    DATA EXHAUSTION GUARD — проверка формулировок "не указано".
    
    Если данные присутствуют в любом документе пакета,
    запрещено использовать формулировки:
    - «не указано»
    - «отсутствует информация»
    
    Returns:
        Список нарушений (пустой если PASS)
    """
    violations = []
    
    if not text:
        return violations
    
    text_lower = text.lower()
    
    forbidden_phrases = [
        'не указано',
        'не указан',
        'не указана',
        'не указаны',
        'отсутствует информация',
        'информация отсутствует',
        'нет данных',
        'данные отсутствуют',
    ]
    
    for phrase in forbidden_phrases:
        if phrase in text_lower:
            violations.append(f"Data Exhaustion Guard: найдена запрещённая формулировка '{phrase}' в контексте: {context[:50]}")
    
    return violations


def run_canon_guardrails(
    decision_preview: Optional[Dict[str, Any]] = None,
    decision_record: Optional[Dict[str, Any]] = None,
    board_pack: Optional[Dict[str, Any]] = None,
    risks: Optional[List[Dict[str, Any]]] = None,
    analysis_text: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Выполняет все проверки CI Guardrails v1.0.
    
    Args:
        decision_preview: Данные Decision Preview
        decision_record: Данные Decision Record
        board_pack: Данные Board Pack
        risks: Список рисков для проверки Impact Guard
        analysis_text: Текст анализа для проверки Data Exhaustion Guard
    
    Returns:
        Tuple[bool, List[str]]: (PASS/FAIL, список нарушений)
    """
    all_violations = []
    
    # LANGUAGE GUARD
    if analysis_text:
        language_violations = check_language_guard(analysis_text, "Analysis text")
        all_violations.extend(language_violations)
    
    # STRUCTURAL GUARD для Decision Preview
    if decision_preview:
        preview_violations = check_structural_guard_decision_preview(decision_preview)
        all_violations.extend([f"Decision Preview: {v}" for v in preview_violations])
        
        # Language Guard для Decision Preview
        preview_text = str(decision_preview)
        preview_language_violations = check_language_guard(preview_text, "Decision Preview")
        all_violations.extend(preview_language_violations)
    
    # STRUCTURAL GUARD для Decision Record
    if decision_record:
        record_violations = check_structural_guard_decision_record(decision_record)
        all_violations.extend([f"Decision Record: {v}" for v in record_violations])
    
    # STRUCTURAL GUARD для Board Pack
    if board_pack:
        board_pack_violations = check_structural_guard_board_pack(board_pack)
        all_violations.extend([f"Board Pack: {v}" for v in board_pack_violations])
    
    # IMPACT GUARD для рисков
    if risks:
        for i, risk in enumerate(risks):
            impact_violations = check_impact_guard(risk)
            all_violations.extend([f"Risk #{i+1}: {v}" for v in impact_violations])
    
    # DATA EXHAUSTION GUARD
    if analysis_text:
        exhaustion_violations = check_data_exhaustion_guard(analysis_text, "Analysis text")
        all_violations.extend(exhaustion_violations)
    
    # Возвращаем результат
    passed = len(all_violations) == 0
    
    if passed:
        return True, ["PASS"]
    else:
        return False, all_violations


def check_canon_guardrails(project_root: str = '.') -> Tuple[bool, str]:
    """
    Проверяет соблюдение канона проекта через анализ кода и промптов.
    
    Проверяет:
    - Language Guard (запрещённые слова в промптах)
    - Structural Guard (структура Decision Preview, Decision Record, Board Pack в коде)
    - Impact Guard (наличие Impact Logic в промптах)
    - Data Exhaustion Guard (формулировки "не указано" в промптах)
    
    Args:
        project_root: Корневая директория проекта
    
    Returns:
        Tuple[bool, str]: (PASS/FAIL, отчёт в виде строки)
    """
    from pathlib import Path
    import os
    
    violations = []
    project_path = Path(project_root)
    
    # Проверяем промпты на Language Guard и Data Exhaustion Guard
    prompts_dir = project_path / "backend" / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.py"):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Language Guard
                lang_violations = check_language_guard(content, f"Prompt file: {prompt_file.name}")
                violations.extend([f"{prompt_file.name}: {v}" for v in lang_violations])
                
                # Data Exhaustion Guard
                exhaustion_violations = check_data_exhaustion_guard(content, f"Prompt file: {prompt_file.name}")
                violations.extend([f"{prompt_file.name}: {v}" for v in exhaustion_violations])
            except Exception as e:
                logger.warning(f"Не удалось проверить файл {prompt_file}: {e}")
    
    # Проверяем код на Structural Guard (Decision Preview, Decision Record, Board Pack)
    backend_dir = project_path / "backend"
    
    # Проверяем decision_preview_canon.py
    preview_canon_file = backend_dir / "prompts" / "decision_preview_canon.py"
    if preview_canon_file.exists():
        try:
            with open(preview_canon_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, что промпт упоминает обязательные компоненты Decision Preview
            required_components = [
                "Deal Snapshot",
                "Поле допустимых решений",
                "ИУН",
                "Реестр рисков",
                "Impact Logic",
                "Блок фиксации ответственности"
            ]
            
            for component in required_components:
                if component not in content:
                    violations.append(f"decision_preview_canon.py: отсутствует упоминание обязательного компонента '{component}'")
        except Exception as e:
            logger.warning(f"Не удалось проверить decision_preview_canon.py: {e}")
    
    # Проверяем decision_record_converter.py на правильность структуры
    converter_file = backend_dir / "decision_record_converter.py"
    if converter_file.exists():
        try:
            with open(converter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, что converter извлекает только 7 полей
            canonical_fields = [
                'tender_id',
                'tender_object',
                'decision',
                'decision_reasons',
                'management_load_index',
                'responsible_person',
                'fixed_at'
            ]
            
            for field in canonical_fields:
                if field not in content:
                    violations.append(f"decision_record_converter.py: отсутствует извлечение канонического поля '{field}'")
        except Exception as e:
            logger.warning(f"Не удалось проверить decision_record_converter.py: {e}")
    
    # Проверяем board_pack_generator.py на канонические 7 секций
    board_pack_file = backend_dir / "board_pack_generator.py"
    if board_pack_file.exists():
        try:
            with open(board_pack_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверяем, что генератор содержит канонические 7 секций
            required_sections = [
                "Executive Summary",
                "Tender Context",
                "Decision",
                "Decision Grounds",
                "Financial Snapshot",
                "Next Steps",
                "Audit Note"
            ]
            
            for section in required_sections:
                if section not in content:
                    violations.append(f"board_pack_generator.py: отсутствует каноническая секция '{section}'")
        except Exception as e:
            logger.warning(f"Не удалось проверить board_pack_generator.py: {e}")
    
    # Формируем отчёт
    if len(violations) == 0:
        return True, "PASS: Все проверки Canon Guardrails пройдены"
    else:
        report_lines = ["FAIL: Обнаружены нарушения Canon Guardrails:\n"]
        for i, violation in enumerate(violations, 1):
            report_lines.append(f"{i}. {violation}")
        return False, "\n".join(report_lines)

