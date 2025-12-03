"""
Registry Checker - проверка реестров блокировок и санкций
Базовая реализация согласно TenderShield-Consolidated-Analysis
"""

import logging
import re
import requests
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class RegistryChecker:
    """Проверка поставщиков по реестрам"""
    
    # URL реестров (примеры, нужно обновить на реальные)
    REGISTRY_URLS = {
        "blocked_suppliers": "https://zakupki.gov.ru/epz/blocked-supplier/search.html",
        "sanctions": "https://minfin.gov.ru/ru/perfomance/sanctions/",
    }
    
    @staticmethod
    def check_blocked_suppliers(inn: str, name: str = None) -> Dict:
        """
        Проверка поставщика в реестре заблокированных поставщиков
        
        Args:
            inn: ИНН поставщика
            name: Наименование поставщика (опционально)
            
        Returns:
            Dict с результатами проверки
        """
        # TODO: Реальная интеграция с zakupki.gov.ru API
        # Пока возвращаем заглушку
        
        result = {
            "is_blocked": False,
            "block_reason": None,
            "block_date": None,
            "source": "реестр заблокированных поставщиков",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Пример проверки (заглушка)
        # В реальности здесь должен быть запрос к API zakupki.gov.ru
        try:
            # Заглушка для демонстрации
            # В продакшене здесь будет реальный API запрос
            logger.info(f"Проверка поставщика ИНН {inn} в реестре блокировок")
            
            # TODO: Реализовать реальный запрос
            # response = requests.get(f"{REGISTRY_URLS['blocked_suppliers']}?inn={inn}")
            # if response.status_code == 200:
            #     # Парсинг ответа
            #     pass
            
        except Exception as e:
            logger.error(f"Ошибка проверки реестра блокировок: {e}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def check_sanctions(inn: str, name: str = None) -> Dict:
        """
        Проверка поставщика в реестре санкций
        
        Args:
            inn: ИНН поставщика
            name: Наименование поставщика (опционально)
            
        Returns:
            Dict с результатами проверки
        """
        result = {
            "is_sanctioned": False,
            "sanction_type": None,
            "sanction_date": None,
            "source": "реестр санкций",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            logger.info(f"Проверка поставщика ИНН {inn} в реестре санкций")
            
            # TODO: Реализовать реальный запрос к реестру санкций
            # response = requests.get(f"{REGISTRY_URLS['sanctions']}?inn={inn}")
            
        except Exception as e:
            logger.error(f"Ошибка проверки реестра санкций: {e}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    def check_competitor_analysis(tender_data: Dict) -> Dict:
        """
        Анализ конкурентов по тендеру
        
        Args:
            tender_data: Данные тендера (НМЦК, отрасль, регион)
            
        Returns:
            Dict с анализом конкурентов
        """
        result = {
            "competitor_count": None,
            "average_bid": None,
            "market_analysis": None,
            "recommendations": []
        }
        
        # TODO: Интеграция с zakupki.gov.ru для получения истории похожих тендеров
        # Можно анализировать:
        # - Количество участников в похожих тендерах
        # - Средние цены предложений
        # - Популярность тендера
        
        logger.info("Анализ конкурентов (заглушка)")
        
        return result
    
    @staticmethod
    def extract_supplier_info(text: str) -> List[Dict]:
        """
        Извлекает информацию о поставщиках из текста документа
        
        Args:
            text: Текст документа
            
        Returns:
            List[Dict] с информацией о поставщиках (ИНН, название)
        """
        suppliers = []
        
        # Поиск ИНН (10 или 12 цифр)
        inn_pattern = r'\b(?:\d{10}|\d{12})\b'
        inn_matches = re.finditer(inn_pattern, text)
        
        for match in inn_matches:
            inn = match.group(0)
            # Ищем название организации рядом с ИНН
            start = max(0, match.start() - 200)
            end = min(len(text), match.end() + 200)
            context = text[start:end]
            
            # Простой поиск названия (между ИНН и следующими словами)
            name_match = re.search(r'([А-ЯЁ][А-Яа-яё\s]{10,100}?)\s*(?:ИНН|инн)', context, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
            else:
                name = None
            
            suppliers.append({
                "inn": inn,
                "name": name,
                "context": context[:100]
            })
        
        return suppliers
    
    @staticmethod
    def check_all_registries(text: str) -> Dict:
        """
        Комплексная проверка всех реестров по тексту документа
        
        Args:
            text: Текст документа
            
        Returns:
            Dict с результатами всех проверок
        """
        result = {
            "suppliers_found": [],
            "blocked_suppliers": [],
            "sanctioned_suppliers": [],
            "warnings": []
        }
        
        # Извлекаем информацию о поставщиках
        suppliers = RegistryChecker.extract_supplier_info(text)
        result["suppliers_found"] = suppliers
        
        # Проверяем каждого поставщика
        for supplier in suppliers:
            inn = supplier.get("inn")
            if not inn:
                continue
            
            # Проверка блокировок
            blocked_check = RegistryChecker.check_blocked_suppliers(inn, supplier.get("name"))
            if blocked_check.get("is_blocked"):
                result["blocked_suppliers"].append({
                    "supplier": supplier,
                    "block_info": blocked_check
                })
                result["warnings"].append({
                    "type": "blocked_supplier",
                    "severity": "HIGH",
                    "message": f"Поставщик {supplier.get('name', '')} (ИНН {inn}) находится в реестре заблокированных"
                })
            
            # Проверка санкций
            sanctions_check = RegistryChecker.check_sanctions(inn, supplier.get("name"))
            if sanctions_check.get("is_sanctioned"):
                result["sanctioned_suppliers"].append({
                    "supplier": supplier,
                    "sanction_info": sanctions_check
                })
                result["warnings"].append({
                    "type": "sanctioned_supplier",
                    "severity": "HIGH",
                    "message": f"Поставщик {supplier.get('name', '')} (ИНН {inn}) находится в реестре санкций"
                })
        
        return result

