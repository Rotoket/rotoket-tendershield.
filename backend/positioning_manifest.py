"""
Positioning Manifest — ШАГ 8: Канонические формулировки позиционирования

Защищает смысл продукта во внешней среде (маркетинг, sales, enterprise).
"""

from typing import List, Tuple
from enum import Enum


class PositioningCategory(str, Enum):
    """Категории формулировок позиционирования."""
    CANONICAL = "canonical"  # Допустимые формулировки
    FORBIDDEN = "forbidden"  # Запрещённые формулировки
    SALES_ALLOWED = "sales_allowed"  # Допустимые sales-тезисы
    SALES_FORBIDDEN = "sales_forbidden"  # Запрещённые sales-обещания


class PositioningManifest:
    """
    Канонические формулировки позиционирования Tender Shield Pro.
    
    ШАГ 8 НЕ МЕНЯЕТ ПРОДУКТ,
    он ЗАЩИЩАЕТ ЕГО СМЫСЛ ВО ВНЕШНЕЙ СРЕДЕ.
    """
    
    # Каноническое позиционирование (эталон)
    CANONICAL_POSITIONING = (
        "Tender Shield Pro — система управленческого решения для директора, "
        "которая выявляет блокирующие риски участия в тендерах "
        "и объясняет, можно ли принимать решение и почему."
    )
    
    # Запрещённые формулировки
    FORBIDDEN_PHRASES = [
        "AI анализирует контракт",
        "Автоматическая юридическая проверка",
        "Снижает риски участия",
        "Помогает выиграть тендер",
        "Оценивает вероятность успеха",
        "AI-юрист",
        "заменяет юристов",
        "ускоряет выигрыш",
        "оптимизирует цену",
        "предиктивная аналитика",
        "контракт безопасен",
        "участие выгодно",
        "риски приемлемы",
        "вероятность успеха",
        "AI magic",
        "compliance tool",
        "умнее человека",
    ]
    
    # Что система гарантирует (и только это)
    SYSTEM_GUARANTEES = [
        "выявление DEAL_BREAKER'ов на основе предоставленных документов",
        "объяснимость причин решения",
        "воспроизводимость вывода",
        "Audit Trail",
        "контроль актуальности решения",
    ]
    
    # Что система НЕ гарантирует
    SYSTEM_DOES_NOT_GUARANTEE = [
        "выигрыш",
        "юридическую чистоту",
        "отсутствие рисков",
        "рыночный успех",
        "замену экспертов",
    ]
    
    # Допустимые sales-тезисы
    SALES_ALLOWED_THESES = [
        "снижает вероятность управленческой ошибки",
        "позволяет отказаться от плохих тендеров раньше",
        "экономит управленческое внимание",
        "фиксирует причины решений для board и аудита",
        "защита управленческого решения",
        "снижение стоимости ошибки",
        "инструмент board-level контроля",
    ]
    
    # Запрещённые sales-обещания
    SALES_FORBIDDEN_PROMISES = [
        "замену юристов",
        "ускорение выигрыша",
        "оптимизацию цены",
        "предиктивную аналитику",
        "AI magic",
        "автоматическое принятие решений",
    ]
    
    # Enterprise / Legal Contract Boundary
    ENTERPRISE_DISCLAIMERS = [
        "Система является decision support tool, а не источником юридических гарантий",
        "Ответственность за управленческое решение остаётся у клиента",
        "Система не заменяет экспертов (юристов, финансистов, технадзор)",
        "Система не гарантирует выигрыш тендера или отсутствие рисков",
        "Система фиксирует управленческую реальность на основе предоставленных документов",
    ]
    
    @staticmethod
    def validate_text(text: str, category: PositioningCategory) -> Tuple[bool, List[str]]:
        """
        Проверяет текст на соответствие позиционированию.
        
        Returns:
            (is_valid, violations) — валидность и список нарушений
        """
        violations = []
        text_lower = text.lower()
        
        if category == PositioningCategory.FORBIDDEN or category == PositioningCategory.SALES_FORBIDDEN:
            # Проверяем на запрещённые фразы
            for phrase in PositioningManifest.FORBIDDEN_PHRASES + PositioningManifest.SALES_FORBIDDEN_PROMISES:
                if phrase.lower() in text_lower:
                    violations.append(f"Запрещённая формулировка: '{phrase}'")
        
        return len(violations) == 0, violations
    
    @staticmethod
    def get_canonical_description() -> str:
        """Возвращает каноническое описание продукта."""
        return PositioningManifest.CANONICAL_POSITIONING
    
    @staticmethod
    def get_system_guarantees() -> List[str]:
        """Возвращает список того, что система гарантирует."""
        return PositioningManifest.SYSTEM_GUARANTEES.copy()
    
    @staticmethod
    def get_system_limitations() -> List[str]:
        """Возвращает список того, что система НЕ гарантирует."""
        return PositioningManifest.SYSTEM_DOES_NOT_GUARANTEE.copy()
    
    @staticmethod
    def get_enterprise_disclaimers() -> List[str]:
        """Возвращает список дисклеймеров для enterprise-контрактов."""
        return PositioningManifest.ENTERPRISE_DISCLAIMERS.copy()































