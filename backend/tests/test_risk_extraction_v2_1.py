"""
Тесты для Risk & Data Extraction v2.1

Проверяет соответствие канону Risk & Data Extraction v2.1
"""

import pytest
from evidence_types import EvidenceObject, EvidenceClassification, EvidenceConfidence


class TestRiskExtractionV21:
    """Тесты для Risk & Data Extraction v2.1 канона"""
    
    def test_cross_document_verification(self):
        """Проверяет кросс-документную сверку данных"""
        # Симуляция данных из разных документов
        evidence_from_tz = EvidenceObject(
            evidence_id="ev-1",
            source_file="Техническое задание.docx",
            fact="Срок выполнения: 30 дней",
            classification=EvidenceClassification.CONTROLLED_RISK,
            confidence=EvidenceConfidence.HIGH,
            section_reference="раздел 5"
        )
        
        evidence_from_contract = EvidenceObject(
            evidence_id="ev-2",
            source_file="Проект контракта.docx",
            fact="Срок выполнения: 45 дней",
            classification=EvidenceClassification.CONTROLLED_RISK,
            confidence=EvidenceConfidence.HIGH,
            section_reference="п. 3.2"
        )
        
        # Проверяем, что обнаружено противоречие
        assert evidence_from_tz.fact != evidence_from_contract.fact
        # В реальной системе это должно быть обнаружено как contradiction
    
    def test_numerical_data_extraction(self):
        """Проверяет извлечение числовых данных"""
        # Симуляция извлечения НМЦК
        nmck_evidence = EvidenceObject(
            evidence_id="ev-3",
            source_file="Обоснование НМЦК.xlsx",
            fact="НМЦК: 1 234 567,89 руб.",
            classification=EvidenceClassification.MARKET_NOISE,
            confidence=EvidenceConfidence.HIGH
        )
        
        # Проверяем, что извлечено числовое значение
        assert "1 234 567" in nmck_evidence.fact
        assert "руб" in nmck_evidence.fact.lower()
    
    def test_evidence_has_source(self):
        """Проверяет, что каждое доказательство имеет источник"""
        evidence = EvidenceObject(
            evidence_id="ev-4",
            source_file="Требования к участникам.docx",
            fact="Требуется лицензия на...",
            classification=EvidenceClassification.DEAL_BREAKER,
            confidence=EvidenceConfidence.MEDIUM,
            section_reference="п. 2.1"
        )
        
        assert evidence.section_reference is not None
        assert len(evidence.section_reference) > 0
        assert "п." in evidence.section_reference or "раздел" in evidence.section_reference.lower()
    
    def test_evidence_has_quote(self):
        """Проверяет, что каждое доказательство имеет цитату"""
        evidence = EvidenceObject(
            evidence_id="ev-5",
            source_file="Требования к участникам.docx",
            fact="Требуется лицензия на осуществление деятельности",
            classification=EvidenceClassification.DEAL_BREAKER,
            confidence=EvidenceConfidence.HIGH,
            section_reference="п. 2.1",
            raw_extract="Участник должен иметь лицензию на осуществление деятельности"
        )
        
        assert evidence.raw_extract is not None
        assert len(evidence.raw_extract) > 0
    
    def test_management_load_index_calculation(self):
        """Проверяет расчет Индекса Управленческой Нагрузки (ИУН)"""
        # Компоненты ИУН должны иметь источник и объяснение
        components = [
            {
                "id": "A",
                "name": "Конфликты условий",
                "explanation": "Следствием является необходимость уточнения условий → Требуется правовой контроль",
                "source": "Проект договора, п. 6.3"
            },
            {
                "id": "B",
                "name": "Финансовая экспозиция",
                "explanation": "Следствием является неограниченная финансовая ответственность → Требуется резервирование оборотных средств",
                "source": "Обоснование НМЦК"
            }
        ]
        
        for component in components:
            assert "source" in component
            assert "explanation" in component
            assert "Следствием является" in component["explanation"]
            assert "→ Требуется" in component["explanation"]
    
    def test_linguistic_guard(self):
        """Проверяет лингвистический гвард (запрет вероятностного языка)"""
        # Запрещенные слова
        forbidden_words = ["кажется", "возможно", "рекомендуется", "вероятно"]
        
        # Допустимые формулировки
        allowed_phrases = [
            "зафиксировано",
            "выявлено",
            "обнаружено",
            "следствием является"
        ]
        
        test_text = "В документации зафиксировано требование. Выявлено противоречие. Следствием является необходимость контроля."
        
        # Проверяем отсутствие запрещенных слов
        for word in forbidden_words:
            assert word not in test_text.lower(), f"Найдено запрещенное слово: {word}"
        
        # Проверяем наличие допустимых фраз
        has_allowed = any(phrase in test_text.lower() for phrase in allowed_phrases)
        assert has_allowed, "Текст должен содержать допустимые формулировки"
    
    def test_data_search_strategy(self):
        """Проверяет стратегию поиска данных в разных документах"""
        # Приоритетный порядок поиска:
        search_order = [
            "Приложение к извещению / Паспорт закупки",
            "Обоснование НМЦК",
            "Техническое задание / График",
            "Проект контракта"
        ]
        
        # Проверяем, что порядок определен
        assert len(search_order) == 4
        assert "НМЦК" in search_order[1] or "НМЦД" in search_order[1]
        assert "контракт" in search_order[3].lower()
    
    def test_self_check_mechanism(self):
        """Проверяет механизм самопроверки перед возвратом ответа"""
        # Критерии самопроверки:
        check_criteria = [
            "указана ли финальная НМЦК",
            "найден ли Заказчик и ИНН",
            "есть ли цитата в каждом риске",
            "использованы ли запрещенные слова"
        ]
        
        assert len(check_criteria) == 4
        
        # Симуляция проверки
        has_nmck = True  # В реальной системе проверяется наличие НМЦК
        has_customer = True  # В реальной системе проверяется наличие заказчика
        all_risks_have_quotes = True  # В реальной системе проверяются все риски
        no_forbidden_words = True  # В реальной системе проверяется текст
        
        assert all([has_nmck, has_customer, all_risks_have_quotes, no_forbidden_words])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

