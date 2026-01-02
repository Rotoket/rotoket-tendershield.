"""
Decision Preview Formatter — ШАГ 5: Decision Preview & Board-Ready Output

Преобразует Decision Graph в управленческий вывод для директора.

КЛЮЧЕВОЙ ПРИНЦИП:
ДИРЕКТОР ЧИТАЕТ РЕШЕНИЕ,
А НЕ ХОД МЫСЛЕЙ СИСТЕМЫ
"""

import logging
from typing import List, Optional, Dict, Any
from reasoning_types import (
    DecisionGraph,
    DecisionPreview,
    RiskSignal,
    Contradiction,
    ManagementLoadExplanation,
)

logger = logging.getLogger(__name__)


class DecisionPreviewFormatter:
    """
    Форматирует Decision Graph в Decision Preview.
    
    ШАГ 5 НЕ АНАЛИЗИРУЕТ
    ШАГ 5 НЕ ПЕРЕСЧИТЫВАЕТ
    ШАГ 5 НЕ ДОБАВЛЯЕТ НОВЫЕ СМЫСЛЫ
    
    Он ТОЛЬКО КОММУНИЦИРУЕТ РЕШЕНИЕ.
    """
    
    @staticmethod
    def format_preview(decision_preview: DecisionPreview) -> Dict[str, Any]:
        """
        Форматирует Decision Preview в board-ready формат.
        
        Обязательный шаблон:
        - Решение (УЧАСТВОВАТЬ / НЕ УЧАСТВОВАТЬ / УЧАСТВОВАТЬ ТОЛЬКО ПРИ УСЛОВИЯХ)
        - Почему (2-4 причины)
        - Ключевой риск
        - Управленческая нагрузка (словесное объяснение)
        - Что нужно для изменения решения (если применимо)
        """
        # Определяем главный риск
        main_risk = DecisionPreviewFormatter._extract_main_risk(decision_preview)
        
        # Форматируем управленческую нагрузку (словесно, без чисел)
        management_load_text = DecisionPreviewFormatter._format_management_load(
            decision_preview.management_load
        )
        
        # Форматируем условия изменения решения
        change_conditions = DecisionPreviewFormatter._format_change_conditions(
            decision_preview
        )
        
        return {
            "decision": decision_preview.decision,
            "decision_label": DecisionPreviewFormatter._format_decision_label(
                decision_preview.decision
            ),
            "why": decision_preview.why,
            "main_risk": main_risk,
            "management_load": management_load_text,
            "change_conditions": change_conditions,
            # Структурированные данные (для UI)
            "deal_breakers_count": len(decision_preview.deal_breakers),
            "controlled_risks_count": len(decision_preview.controlled_risks),
            "contradictions_count": len(decision_preview.contradictions),
        }
    
    @staticmethod
    def _extract_main_risk(decision_preview: DecisionPreview) -> str:
        """
        Извлекает главный риск.
        
        Правило:
        - если есть DEAL_BREAKER — он здесь
        - если нет — «критичных блокирующих рисков не выявлено»
        """
        if decision_preview.deal_breakers:
            # Берём первый DEAL_BREAKER как главный риск
            main_deal_breaker = decision_preview.deal_breakers[0]
            return DecisionPreviewFormatter._format_risk_description(main_deal_breaker)
        
        if decision_preview.main_risk:
            return decision_preview.main_risk
        
        return "Критичных блокирующих рисков не выявлено"
    
    @staticmethod
    def _format_risk_description(risk: RiskSignal) -> str:
        """
        Форматирует описание риска для директора.
        
        Убирает технические детали, оставляет управленческое следствие.
        """
        # Убираем технические маркеры (evidence_id, derived_from)
        description = risk.description
        
        # Если описание слишком длинное, обрезаем до сути
        if len(description) > 200:
            # Пытаемся найти ключевую фразу
            if ":" in description:
                description = description.split(":")[0] + ": " + description.split(":")[1][:100]
            else:
                description = description[:150] + "..."
        
        return description
    
    @staticmethod
    def _format_management_load(load: ManagementLoadExplanation) -> str:
        """
        Форматирует управленческую нагрузку словесно, без чисел.
        
        Запрещено:
        - числа
        - шкалы
        - проценты
        
        Разрешено:
        - словесное объяснение
        - источники сложности
        """
        if not load.sources:
            return "Управленческая нагрузка стандартная"
        
        # Формируем словесное описание
        parts = []
        
        if load.contradictions_count > 0:
            if load.contradictions_count == 1:
                parts.append("обнаружено одно противоречие между документами")
            elif load.contradictions_count <= 3:
                parts.append("обнаружено несколько противоречий между документами")
            else:
                parts.append("обнаружено множество противоречий между документами")
        
        if load.low_confidence_evidence_count > 0:
            parts.append("требуется дополнительная верификация данных")
        
        if load.non_standard_conditions:
            parts.append("обнаружены нестандартные условия")
        
        if load.manual_verification_required:
            parts.append("требуется ручная проверка ключевых параметров")
        
        if not parts:
            return "Управленческая нагрузка стандартная"
        
        # Объединяем части в связный текст
        if len(parts) == 1:
            return f"Управленческая нагрузка повышена: {parts[0]}"
        elif len(parts) == 2:
            return f"Управленческая нагрузка повышена: {parts[0]} и {parts[1]}"
        else:
            return f"Управленческая нагрузка повышена: {', '.join(parts[:-1])} и {parts[-1]}"
    
    @staticmethod
    def _format_change_conditions(decision_preview: DecisionPreview) -> Optional[str]:
        """
        Форматирует условия изменения решения.
        
        Показывается только если:
        - решение "УЧАСТВОВАТЬ ТОЛЬКО ПРИ УСЛОВИЯХ"
        - или есть risk_mitigation
        """
        if decision_preview.risk_mitigation:
            return "Для изменения решения требуется:\n" + "\n".join(
                f"- {condition}" for condition in decision_preview.risk_mitigation
            )
        
        if decision_preview.decision == "PARTICIPATE_WITH_CONDITIONS":
            if decision_preview.contradictions:
                return "Для изменения решения требуется уточнить противоречия в документах с заказчиком"
        
        return None
    
    @staticmethod
    def _format_decision_label(decision: str) -> str:
        """Форматирует метку решения для UI."""
        labels = {
            "PARTICIPATE": "УЧАСТВОВАТЬ",
            "DO_NOT_PARTICIPATE": "НЕ УЧАСТВОВАТЬ",
            "PARTICIPATE_WITH_CONDITIONS": "УЧАСТВОВАТЬ ТОЛЬКО ПРИ УСЛОВИЯХ",
        }
        return labels.get(decision, decision)
    
    @staticmethod
    def format_board_ready_text(decision_preview: DecisionPreview) -> str:
        """
        Форматирует Decision Preview в текстовый формат для Board Pack.
        
        Board-ready означает:
        - однозначный вывод
        - без технических деталей
        - управленческий язык
        """
        formatted = DecisionPreviewFormatter.format_preview(decision_preview)
        
        lines = [
            "=" * 60,
            "УПРАВЛЕНЧЕСКИЙ ВЫВОД",
            "=" * 60,
            "",
            f"Решение: {formatted['decision_label']}",
            "",
            "Почему это решение:",
        ]
        
        for i, reason in enumerate(formatted['why'], 1):
            lines.append(f"{i}. {reason}")
        
        lines.extend([
            "",
            f"Ключевой риск: {formatted['main_risk']}",
            "",
            f"Управленческая нагрузка: {formatted['management_load']}",
        ])
        
        if formatted['change_conditions']:
            lines.extend([
                "",
                formatted['change_conditions'],
            ])
        
        lines.extend([
            "",
            "=" * 60,
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def validate_preview(decision_preview: DecisionPreview) -> List[str]:
        """
        Валидирует Decision Preview на соответствие канону ШАГА 5.
        
        Возвращает список ошибок (если есть).
        """
        errors = []
        
        # Проверка: решение должно быть одним из допустимых
        if decision_preview.decision not in ["PARTICIPATE", "DO_NOT_PARTICIPATE", "PARTICIPATE_WITH_CONDITIONS"]:
            errors.append(f"Недопустимое решение: {decision_preview.decision}")
        
        # Проверка: почему должно быть 2-4 причины
        if len(decision_preview.why) < 2:
            errors.append("Поле 'why' должно содержать минимум 2 причины")
        if len(decision_preview.why) > 4:
            errors.append("Поле 'why' должно содержать максимум 4 причины")
        
        # Проверка: если есть DEAL_BREAKER, решение не может быть PARTICIPATE
        if decision_preview.deal_breakers and decision_preview.decision == "PARTICIPATE":
            errors.append("При наличии DEAL_BREAKER решение не может быть 'УЧАСТВОВАТЬ'")
        
        # Проверка: управленческая нагрузка должна быть словесной (не числовой)
        # (это проверяется на уровне типов, но можно добавить runtime проверку)
        
        return errors































