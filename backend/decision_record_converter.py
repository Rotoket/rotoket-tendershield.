"""
Decision Record Converter — ШАГ 11: Преобразование Decision Preview → Decision Record

Функция для канонического преобразования Decision Preview в Decision Record.
Извлекает ТОЛЬКО 7 обязательных полей, исключая весь анализ.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from reasoning_types import DecisionPreview
from decision_record_types import DecisionRecord, calculate_management_load_index

logger = logging.getLogger(__name__)


def convert_preview_to_record(
    decision_preview: DecisionPreview,
    tender_id: str,
    tender_object: str,
    responsible_person: str,
    fixed_at: datetime,
    analysis_id: Optional[int] = None,
    package_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> DecisionRecord:
    """
    Преобразует Decision Preview в канонический Decision Record.
    
    Извлекает ТОЛЬКО 7 обязательных полей:
    1. Tender ID
    2. Объект (кратко)
    3. Принятое решение
    4. Основание решения (1–3 причины)
    5. Индекс управленческой нагрузки (одно число)
    6. Ответственный
    7. Дата фиксации
    
    ⚠️ ВАЖНО: НЕ включает:
    - Evidence Objects
    - Impact Logic
    - Расшифровку ИУН по компонентам
    - Риски и их описания
    - Инструкции и рекомендации
    
    Args:
        decision_preview: Decision Preview из Reasoning Layer
        tender_id: Идентификатор тендера
        tender_object: Краткое описание объекта (1-2 предложения)
        responsible_person: ФИО или должность ответственного
        fixed_at: Дата и время фиксации решения
        analysis_id: ID анализа (для single mode)
        package_id: ID пакетного анализа (для package mode)
        user_id: ID пользователя
    
    Returns:
        DecisionRecord — каноническая запись с 7 полями
    """
    # 1. Tender ID — уже передан
    # 2. Объект — уже передан
    
    # 3. Принятое решение — из decision_preview.decision
    decision = decision_preview.decision
    
    # 4. Основание решения — берем первые 1-3 причины из why (без расшифровок)
    decision_reasons = decision_preview.why[:3]  # Максимум 3 причины
    
    # 5. Индекс управленческой нагрузки — вычисляем из management_load
    management_load_dict = decision_preview.management_load.dict() if hasattr(decision_preview.management_load, 'dict') else decision_preview.management_load
    management_load_index = calculate_management_load_index(management_load_dict)
    
    # 6. Ответственный — уже передан
    # 7. Дата фиксации — уже передана
    
    record = DecisionRecord(
        tender_id=tender_id,
        tender_object=tender_object,
        decision=decision,
        decision_reasons=decision_reasons,
        management_load_index=management_load_index,
        responsible_person=responsible_person,
        fixed_at=fixed_at,
        analysis_id=analysis_id,
        package_id=package_id,
        user_id=user_id,
    )
    
    logger.info(f"✅ Decision Record создан: tender_id={tender_id}, decision={decision}, index={management_load_index}")
    
    return record


def extract_tender_id_from_analysis(result_json: Dict[str, Any]) -> str:
    """
    Извлекает Tender ID из результата анализа.
    
    Ищет в следующих местах:
    1. result_json["passport"].get("tenderId") или похожее
    2. result_json["tender_id"]
    3. Или генерирует из других данных (если не найден)
    
    Returns:
        str — идентификатор тендера
    """
    # Пробуем извлечь из passport
    passport = result_json.get("passport", {})
    tender_id = (
        passport.get("tenderId") or
        passport.get("tender_id") or
        passport.get("noticeNumber") or
        result_json.get("tender_id") or
        result_json.get("tenderId")
    )
    
    if tender_id:
        return str(tender_id)
    
    # Если не найден, генерируем из filename или создаем placeholder
    filename = result_json.get("filename", "unknown")
    # Пытаемся найти число в названии файла (возможно, это номер тендера)
    import re
    numbers = re.findall(r'\d+', filename)
    if numbers:
        # Берем самое длинное число (скорее всего, это номер тендера)
        tender_id = max(numbers, key=len)
        return tender_id
    
    # Если совсем ничего не найдено, создаем placeholder
    return f"UNKNOWN-{filename[:20]}"


def extract_tender_object_from_analysis(result_json: Dict[str, Any]) -> str:
    """
    Извлекает краткое описание объекта из результата анализа.
    
    Использует summary из анализа, ограничивая 200 символами.
    
    Returns:
        str — краткое описание объекта (1-2 предложения)
    """
    summary = result_json.get("summary", "")
    if summary:
        # Ограничиваем 200 символами и берем первые 2 предложения
        summary_short = summary[:200]
        sentences = summary_short.split('.')
        if len(sentences) >= 2:
            return '. '.join(sentences[:2]) + '.'
        return summary_short
    return "Объект закупки не описан"





























