"""
Тесты для Registry Checker
"""

import pytest
from registry_checker import RegistryChecker


class TestRegistryChecker:
    """Тесты для проверки реестров"""
    
    def test_extract_supplier_info(self):
        """Тест извлечения информации о поставщиках"""
        text = """
        Поставщик: ООО "Тестовая Компания"
        ИНН: 1234567890
        Адрес: г. Москва
        """
        
        suppliers = RegistryChecker.extract_supplier_info(text)
        
        assert len(suppliers) > 0
        assert any(s["inn"] == "1234567890" for s in suppliers)
    
    def test_extract_multiple_inns(self):
        """Тест извлечения нескольких ИНН"""
        text = """
        Заказчик: ООО "Заказчик" ИНН 1111111111
        Поставщик: ООО "Поставщик" ИНН 2222222222
        """
        
        suppliers = RegistryChecker.extract_supplier_info(text)
        
        assert len(suppliers) >= 2
        inns = [s["inn"] for s in suppliers]
        assert "1111111111" in inns or "2222222222" in inns
    
    def test_check_blocked_suppliers_structure(self):
        """Тест структуры ответа проверки блокировок"""
        result = RegistryChecker.check_blocked_suppliers("1234567890", "Тестовая Компания")
        
        assert "is_blocked" in result
        assert "block_reason" in result
        assert "source" in result
        assert "checked_at" in result
        assert isinstance(result["is_blocked"], bool)
    
    def test_check_sanctions_structure(self):
        """Тест структуры ответа проверки санкций"""
        result = RegistryChecker.check_sanctions("1234567890", "Тестовая Компания")
        
        assert "is_sanctioned" in result
        assert "sanction_type" in result
        assert "source" in result
        assert "checked_at" in result
        assert isinstance(result["is_sanctioned"], bool)
    
    def test_check_all_registries(self):
        """Тест комплексной проверки всех реестров"""
        text = """
        Поставщик: ООО "Тест" ИНН 1234567890
        Контракт на сумму 1 000 000 рублей
        """
        
        result = RegistryChecker.check_all_registries(text)
        
        assert "suppliers_found" in result
        assert "blocked_suppliers" in result
        assert "sanctioned_suppliers" in result
        assert "warnings" in result
        assert isinstance(result["suppliers_found"], list)
        assert isinstance(result["warnings"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

