"""
Decision Record Types — ШАГ 11: Decision Record Freeze v1.0

Канонический Decision Record — юридически значимая фиксация факта решения.
Содержит ТОЛЬКО 7 обязательных полей.

ПРИНЦИП:
Decision Record = факт, а не анализ.
Никаких Evidence, Impact Logic, расшифровок ИУН, рисков, инструкций.
"""

from typing import Literal, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DecisionRecord(BaseModel):
    """
    Decision Record v1.0 — каноническая запись в Журнале управленческих решений.
    
    Содержит ТОЛЬКО 7 обязательных полей:
    1. Tender ID
    2. Объект (кратко)
    3. Принятое решение
    4. Основание решения (1–3 причины)
    5. Индекс управленческой нагрузки (одно число)
    6. Ответственный
    7. Дата фиксации
    
    ⚠️ ВАЖНО: Это факт, а не анализ. Никаких Evidence, Impact Logic, расшифровок.
    """
    # 1. Tender ID
    tender_id: str = Field(..., description="Идентификатор тендера (из passport или извещения)")
    
    # 2. Объект (кратко)
    tender_object: str = Field(..., description="Краткое описание объекта закупки (1-2 предложения)")
    
    # 3. Принятое решение
    decision: Literal[
        "PARTICIPATE",
        "DO_NOT_PARTICIPATE", 
        "PARTICIPATE_WITH_CONDITIONS",
        "POSTPONE"
    ] = Field(..., description="Принятое управленческое решение")
    
    # 4. Основание решения (1–3 причины, без расшифровок)
    decision_reasons: List[str] = Field(
        ..., 
        min_items=1, 
        max_items=3,
        description="1-3 ключевых причины решения (без расшифровок и следствий)"
    )
    
    # 5. Индекс управленческой нагрузки (одно число)
    management_load_index: int = Field(
        ...,
        ge=0,
        le=100,
        description="Итоговый ИУН (одно число 0-100, без компонентов и объяснений)"
    )
    
    # 6. Ответственный
    responsible_person: str = Field(..., description="ФИО или должность ответственного лица")
    
    # 7. Дата фиксации
    fixed_at: datetime = Field(..., description="Дата и время фиксации решения")
    
    # Служебные поля (не часть канона, но нужны для связи с анализом)
    analysis_id: Optional[int] = Field(None, description="ID анализа (для single mode)")
    package_id: Optional[str] = Field(None, description="ID пакетного анализа (для package mode)")
    user_id: Optional[int] = Field(None, description="ID пользователя, принявшего решение")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tender_id": "252253600872825360100100450018010244",
                "tender_object": "Поставка оборудования для системы мониторинга",
                "decision": "PARTICIPATE_WITH_CONDITIONS",
                "decision_reasons": [
                    "Требования к лицензированию объектов с АТЗ",
                    "Короткий срок мобилизации персонала",
                    "Обязательный ручной контроль ГБР"
                ],
                "management_load_index": 57,
                "responsible_person": "Генеральный директор",
                "fixed_at": "2025-12-24T10:00:00",
                "analysis_id": 123,
                "user_id": 1
            }
        }


def calculate_management_load_index(management_load_explanation: dict) -> int:
    """
    Вычисляет итоговый ИУН (одно число 0-100) из ManagementLoadExplanation.
    
    Алгоритм упрощенный:
    - Базовая нагрузка: 20
    - Противоречия: +15 за каждое
    - Низкая уверенность Evidence: +10 за каждое
    - Нестандартные условия: +5 за каждое
    - Ручная верификация: +10 за каждое
    
    Максимум: 100
    """
    sources_count = len(management_load_explanation.get("sources", []))
    contradictions_count = management_load_explanation.get("contradictions_count", 0)
    low_confidence_count = management_load_explanation.get("low_confidence_evidence_count", 0)
    non_standard_count = len(management_load_explanation.get("non_standard_conditions", []))
    manual_verification_count = len(management_load_explanation.get("manual_verification_required", []))
    
    # Базовая нагрузка
    index = 20
    
    # Добавляем компоненты
    index += min(contradictions_count * 15, 30)  # Максимум 30 за противоречия
    index += min(low_confidence_count * 10, 20)  # Максимум 20 за низкую уверенность
    index += min(non_standard_count * 5, 15)  # Максимум 15 за нестандартные условия
    index += min(manual_verification_count * 10, 15)  # Максимум 15 за ручную верификацию
    index += min(sources_count * 2, 10)  # Максимум 10 за источники
    
    # Ограничиваем максимумом 100
    return min(index, 100)





























