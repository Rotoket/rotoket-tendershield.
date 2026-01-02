"""
Извлечение паспорта тендера через regex + fallback механизм.

Этот модуль используется как fallback когда Ollama недоступна или не сработала.
Обеспечивает двухуровневую систему извлечения данных: LLM → Regex.
"""

import re
from typing import Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TenderPassportExtractor:
    """Извлечение паспорта тендера через regex + fallback"""
    
    def __init__(self):
        # НМЦК patterns - самые частые форматы
        self.nmck_patterns = [
            r'(?:НМЦК|начальн[а-я]?\s+(?:макси[а-я]*\s+)?цен[а-я])\s*[:\-]?\s*(\d+[\s\d]*(?:\d+))\s*(?:рублей?|руб|р\.)',
            r'(\d+[\s\d]*(?:\d+))\s*(?:рублей?|руб|р\.)\s*(?:без|с)?\s*(?:НДС)?',
            r'(?:цена|сумма|объем)\s*[:\-]?\s*(\d+[\s\d]*(?:\d+))\s*(?:руб|тыс|млн)',
        ]
        
        # Заказчик patterns
        self.customer_patterns = [
            r'(?:заказчик|подрядчик|поставщик)[ом]?\s*[:\-]?\s*([А-ЯА-ЯЁ][а-яёа-я0-9\s\(\)\.]+?)(?:\s*(?:инн|огрн|адрес|телефон)|$)',
            r'(?:организация|компания|учреждение)[ом]?\s*[:\-]?\s*([А-ЯА-ЯЁ][а-яёа-я0-9\s\(\)\.]+?)(?:\s*(?:инн|адрес)|$)',
        ]
        
        # Дедлайн patterns
        self.deadline_patterns = [
            r'(?:дедлайн|крайний сроки?|срок подачи)[ом]?\s*[:\-]?\s*(\d{2}[.\-]\d{2}[.\-]\d{4})',
            r'(\d{2}[.\-]\d{2}[.\-]\d{4})\s*(?:включительно|до|по)?\s*(?:включительно)?',
        ]
    
    def extract_nmck(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Извлечь НМЦК из текста"""
        for pattern in self.nmck_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_value = match.group(1).replace(' ', '').replace('\xa0', '')
                try:
                    nmck = float(raw_value)
                    if nmck > 0:  # Валидация: НМЦК не может быть 0
                        return nmck, match.group(0)
                except ValueError:
                    continue
        return None, None
    
    def extract_customer(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Извлечь название заказчика"""
        for pattern in self.customer_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                customer = match.group(1).strip()
                if len(customer) > 5:  # Должно быть реальное имя
                    return customer, match.group(0)
        return None, None
    
    def extract_deadline(self, text: str) -> Tuple[Optional[datetime], Optional[str]]:
        """Извлечь дедлайн подачи заявок"""
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                try:
                    # Попробовать разные форматы
                    for fmt in ['%d.%m.%Y', '%d-%m-%Y', '%d/%m/%Y']:
                        try:
                            deadline = datetime.strptime(date_str, fmt).date()
                            if deadline > datetime.now().date():  # Дедлайн в будущем
                                return deadline, match.group(0)
                        except ValueError:
                            continue
                except Exception as e:
                    logger.debug(f"Ошибка парсинга даты {date_str}: {e}")
        return None, None
    
    def extract_contract_terms(self, text: str) -> Tuple[Optional[int], Optional[str]]:
        """Извлечь длительность контракта в месяцах"""
        pattern = r'(?:период|срок|длитель)[а-я]*\s*[:\-]?\s*(\d+)\s*(?:месяц|мес|мес\.|м\.|год|лет)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            months = int(match.group(1))
            # Нормализовать в месяцы
            if 'год' in match.group(0).lower():
                months *= 12
            return months, match.group(0)
        return None, None
    
    def extract_guarantee(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Извлечь обеспечение участия в торгах"""
        pattern = r'(?:обеспечение|гарантия|залог)\s*[:\-]?\s*(\d+[\s\d]*(?:\d+))\s*(?:рублей?|руб|%)?'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                guarantee = float(match.group(1).replace(' ', ''))
                return guarantee, match.group(0)
            except ValueError:
                pass
        return None, None
    
    def extract_tender_passport_fallback(self, text: str, document_name: str = "unknown.pdf") -> dict:
        """
        Основная функция: извлечь ВСЕ данные паспорта используя regex.
        Это fallback когда Ollama недоступна или не сработала.
        
        Args:
            text: Текст документа
            document_name: Имя документа для источников
            
        Returns:
            dict с данными паспорта тендера
        """
        passport = {
            'nmck_numeric': None,
            'nmck_formatted': None,
            'nmck_source': None,
            'customer': None,
            'customer_source': None,
            'deadline': None,
            'deadline_source': None,
            'contract_term_months': None,
            'contract_term_source': None,
            'guarantee_amount': None,
            'guarantee_source': None,
            'extraction_method': 'regex',
            'warnings': []
        }
        
        # Извлечь НМЦК
        nmck, nmck_quote = self.extract_nmck(text)
        if nmck:
            passport['nmck_numeric'] = nmck
            # Форматирование НМЦК
            if nmck >= 1000000000:
                passport['nmck_formatted'] = f"{nmck / 1000000000:.2f} млрд руб."
            elif nmck >= 1000000:
                passport['nmck_formatted'] = f"{nmck / 1000000:.2f} млн руб."
            else:
                passport['nmck_formatted'] = f"{nmck:,.0f} руб."
            passport['nmck_source'] = {
                'document_name': document_name,
                'quote': nmck_quote[:200] if nmck_quote else '',
                'extraction_method': 'regex',
                'confidence': 0.8
            }
        else:
            passport['warnings'].append("НМЦК не найдена в документе")
        
        # Извлечь заказчика
        customer, cust_quote = self.extract_customer(text)
        if customer:
            passport['customer'] = customer
            passport['customer_source'] = {
                'document_name': document_name,
                'quote': cust_quote[:200] if cust_quote else '',
                'extraction_method': 'regex',
                'confidence': 0.75
            }
        else:
            passport['warnings'].append("Заказчик не идентифицирован")
        
        # Извлечь дедлайн
        deadline, deadline_quote = self.extract_deadline(text)
        if deadline:
            passport['deadline'] = deadline.isoformat()
            passport['deadline_source'] = {
                'document_name': document_name,
                'quote': deadline_quote[:200] if deadline_quote else '',
                'extraction_method': 'regex',
                'confidence': 0.85
            }
        else:
            passport['warnings'].append("Дедлайн не найден")
        
        # Извлечь условия контракта
        term_months, term_quote = self.extract_contract_terms(text)
        if term_months:
            passport['contract_term_months'] = term_months
            passport['contract_term_source'] = {
                'document_name': document_name,
                'quote': term_quote[:200] if term_quote else '',
                'extraction_method': 'regex',
                'confidence': 0.8
            }
        
        # Извлечь обеспечение
        guarantee, guarantee_quote = self.extract_guarantee(text)
        if guarantee:
            passport['guarantee_amount'] = guarantee
            passport['guarantee_source'] = {
                'document_name': document_name,
                'quote': guarantee_quote[:200] if guarantee_quote else '',
                'extraction_method': 'regex',
                'confidence': 0.7
            }
        
        # Вычислить процент заполненности
        filled = 0
        total = 4  # НМЦК, заказчик, дедлайн, срок контракта
        if passport['nmck_numeric']:
            filled += 1
        if passport['customer']:
            filled += 1
        if passport['deadline']:
            filled += 1
        if passport['contract_term_months']:
            filled += 1
        passport['completion_percentage'] = int((filled / total) * 100)
        
        return passport


# Функция для использования
def extract_tender_passport_fallback(text: str, document_name: str = "unknown.pdf") -> dict:
    """Публичная функция для использования в основном коде"""
    extractor = TenderPassportExtractor()
    return extractor.extract_tender_passport_fallback(text, document_name)


