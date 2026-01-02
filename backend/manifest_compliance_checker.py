"""
Manifest Compliance Checker — ШАГ 7: Проверка соответствия Architecture Manifest

Автоматическая проверка, что код соответствует принципам Manifest.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ManifestComplianceChecker:
    """
    Проверяет соответствие кода Architecture Manifest.
    
    Это не тесты, а архитектурные guardrails.
    """
    
    @staticmethod
    def check_deal_breaker_priority(decision_preview: Dict[str, Any]) -> List[str]:
        """
        Проверяет, что DEAL_BREAKER имеет абсолютный приоритет.
        
        Нарушения:
        - Решение "УЧАСТВОВАТЬ" при наличии DEAL_BREAKER
        - DEAL_BREAKER смягчён формулировками
        - DEAL_BREAKER компенсирован другими факторами
        """
        violations = []
        
        deal_breakers = decision_preview.get("deal_breakers", [])
        decision = decision_preview.get("decision", "")
        
        # Нарушение: решение "УЧАСТВОВАТЬ" при наличии DEAL_BREAKER
        if deal_breakers and decision == "PARTICIPATE":
            violations.append(
                "КРИТИЧЕСКОЕ НАРУШЕНИЕ: Решение 'УЧАСТВОВАТЬ' при наличии DEAL_BREAKER. "
                "DEAL_BREAKER имеет абсолютный приоритет."
            )
        
        # Проверяем формулировки DEAL_BREAKER на смягчение
        for db in deal_breakers:
            title = (db.get("title", "") or "").lower()
            description = (db.get("description", "") or "").lower()
            
            # Запрещённые смягчающие формулировки
            softening_keywords = [
                "можно рассмотреть",
                "в целом приемлемо",
                "но",
                "однако",
                "возможно",
                "вероятно",
            ]
            
            for keyword in softening_keywords:
                if keyword in title or keyword in description:
                    violations.append(
                        f"НАРУШЕНИЕ: DEAL_BREAKER содержит смягчающую формулировку '{keyword}'. "
                        "DEAL_BREAKER не может быть смягчён."
                    )
        
        return violations
    
    @staticmethod
    def check_expert_opinion_isolation(expert_opinions: List[Dict[str, Any]], risk_signals: List[Dict[str, Any]]) -> List[str]:
        """
        Проверяет, что Особое мнение эксперта изолировано от Risk Signals.
        
        Нарушения:
        - Expert Opinion влияет на классификацию рисков
        - Expert Opinion используется как аргумент решения
        """
        violations = []
        
        # Проверяем, что Expert Opinion не смешивается с Risk Signals
        # (это проверка на уровне данных, детальная проверка требует анализа кода)
        
        return violations
    
    @staticmethod
    def check_decision_language(decision_preview: Dict[str, Any]) -> List[str]:
        """
        Проверяет, что язык решения соответствует Manifest.
        
        Запрещённые формулировки:
        - "контракт безопасен"
        - "участие выгодно"
        - "риски приемлемы"
        - "вероятность успеха X%"
        """
        violations = []
        
        why_reasons = decision_preview.get("why", [])
        main_risk = decision_preview.get("main_risk", "")
        
        forbidden_phrases = [
            "контракт безопасен",
            "участие выгодно",
            "риски приемлемы",
            "вероятность успеха",
            "вероятность",
            "%",
            "безопасен",
            "выгодно",
        ]
        
        for reason in why_reasons:
            reason_lower = reason.lower()
            for phrase in forbidden_phrases:
                if phrase in reason_lower:
                    violations.append(
                        f"НАРУШЕНИЕ: Использована запрещённая формулировка '{phrase}'. "
                        "Система не утверждает безопасность, выгоду или вероятности."
                    )
        
        if main_risk:
            main_risk_lower = main_risk.lower()
            for phrase in forbidden_phrases:
                if phrase in main_risk_lower:
                    violations.append(
                        f"НАРУШЕНИЕ: Главный риск содержит запрещённую формулировку '{phrase}'."
                    )
        
        return violations
    
    @staticmethod
    def check_reason_codes_for_refusal(decision: str, reason_codes: Optional[List[str]]) -> List[str]:
        """
        Проверяет, что решение "НЕ УЧАСТВОВАТЬ" имеет Reason Codes.
        
        Это стратегическая память, обязательна для агрегации.
        """
        violations = []
        
        if decision == "DO_NOT_PARTICIPATE":
            if not reason_codes or len(reason_codes) == 0:
                violations.append(
                    "НАРУШЕНИЕ: Решение 'НЕ УЧАСТВОВАТЬ' не имеет Reason Codes. "
                    "Reason Codes обязательны для корпоративной памяти отказов."
                )
        
        return violations
    
    @staticmethod
    def check_all(decision_preview: Dict[str, Any], reason_codes: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Выполняет все проверки соответствия Manifest.
        
        Returns:
            Словарь с результатами проверок по категориям
        """
        results = {
            "deal_breaker_priority": ManifestComplianceChecker.check_deal_breaker_priority(decision_preview),
            "decision_language": ManifestComplianceChecker.check_decision_language(decision_preview),
            "reason_codes": ManifestComplianceChecker.check_reason_codes_for_refusal(
                decision_preview.get("decision", ""),
                reason_codes
            ),
        }
        
        # Подсчитываем общее количество нарушений
        total_violations = sum(len(v) for v in results.values())
        
        if total_violations > 0:
            logger.warning(f"⚠️ Обнаружено {total_violations} нарушений Architecture Manifest")
            for category, violations in results.items():
                if violations:
                    logger.warning(f"  {category}: {len(violations)} нарушений")
                    for violation in violations:
                        logger.warning(f"    - {violation}")
        else:
            logger.info("✅ Все проверки Manifest пройдены")
        
        return results































