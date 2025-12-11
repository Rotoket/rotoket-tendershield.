"""
Специализированные анализаторы для разных аспектов тендерной документации
Реализует рекомендации из TenderShield-Consolidated-Analysis
"""

import logging
import re
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LegalRiskAnalyzer:
    """Анализатор правовых рисков по 44-ФЗ и 223-ФЗ"""
    
    @staticmethod
    def analyze_44fz_risks(text: str) -> List[Dict]:
        """Анализ рисков по 44-ФЗ"""
        risks = []
        text_lower = text.lower()
        
        # Статья 33: Ограничение конкуренции
        if re.search(r'\b(только|исключительно|обязательно)\s+(intel|amd|nvidia|lenovo|dell|hp|microsoft)', text_lower):
            if 'или эквивалент' not in text_lower:
                risks.append({
                    "title": "Нарушение ст. 33 44-ФЗ: Ограничение конкуренции",
                    "severity": "HIGH",
                    "description": "Указание конкретных товарных знаков без формулировки 'или эквивалент'",
                    "law_reference": "ст. 33 44-ФЗ",
                    "quote": LegalRiskAnalyzer._extract_quote(text, r'\b(только|исключительно)\s+(intel|amd|nvidia)')
                })
        
        # Статья 34: Штрафы и неустойки
        penalty_matches = re.finditer(r'(штраф|неустойка|пеня)[^%]{0,100}(\d+[.,]?\d*)\s*%', text_lower)
        for match in penalty_matches:
            percent_str = match.group(2)
            try:
                value = float(percent_str.replace(',', '.'))
                if value > 0.5:  # Более 0.5% в день - высокий риск
                    risks.append({
                        "title": "Завышенные штрафы/неустойки",
                        "severity": "HIGH" if value >= 1.0 else "MEDIUM",
                        "description": f"Штраф {value}% в день может быть признан несоразмерным",
                        "law_reference": "ст. 34 44-ФЗ",
                        "quote": text[match.start():match.end()+50]
                    })
            except ValueError:
                pass
        
        # Статья 31: Избыточные требования к участникам
        excessive_keywords = ['опыт работы не менее 10 лет', 'обязательно наличие филиала', 
                            'обязательно сертификат iso 9001']
        for keyword in excessive_keywords:
            if keyword in text_lower:
                risks.append({
                    "title": "Избыточные требования к участникам",
                    "severity": "MEDIUM",
                    "description": "Требования могут быть признаны необоснованными",
                    "law_reference": "ст. 31 44-ФЗ",
                    "quote": LegalRiskAnalyzer._extract_quote(text, keyword)
                })
        
        return risks
    
    @staticmethod
    def analyze_223fz_risks(text: str) -> List[Dict]:
        """Анализ рисков по 223-ФЗ"""
        risks = []
        text_lower = text.lower()
        
        # Проверка на соответствие положению о закупке
        if 'положение о закупке' not in text_lower and '223-фз' in text_lower:
            risks.append({
                "title": "Отсутствие ссылки на положение о закупке",
                "severity": "MEDIUM",
                "description": "По 223-ФЗ закупка должна соответствовать положению о закупке заказчика",
                "law_reference": "223-ФЗ",
                "quote": ""
            })
        
        return risks
    
    @staticmethod
    def _extract_quote(text: str, pattern: str) -> str:
        """Извлекает цитату из текста вокруг найденного паттерна"""
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            return text[start:end].strip()
        return ""


class FinancialAnalyzer:
    """Анализатор финансовых рисков и НМЦК"""
    
    @staticmethod
    def analyze_nmck(text: str) -> Dict:
        """Анализ НМЦК и финансовых параметров.

        Задача этого метода — максимально надёжно вытащить НМЦК и базовые
        финансовые параметры даже из "живых" формулировок, встречающихся в
        протоколах обоснования, сметах и договорах (в том числе строительных).
        """
        result = {
            "nmck": None,
            "nmck_numeric": None,
            "estimated_cost": None,
            "margin_comment": "",
            "risks": []
        }
        
        # Поиск НМЦК
        # Сначала более "узкие" паттерны, затем более общие
        nmck_patterns = [
            # 1) Классические формулировки
            r'нмцк[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|rub)',
            r'нмц[:\s]+(\d[\d\s]*[.,]?\d*)',
            r'цена\s+контракт[а]?[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽)',
            r'стоимость[ю]?:[\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽)',
            # 2) Строительные протоколы: "Начальная (максимальная) цена контракта составляет ..."
            r'начальн[аяя][^\n]{0,80}?цен[аы]\s+контракт[а]?[^\n]{0,80}?составляет[:\s]+(\d[\d\s]*[.,]?\d*)',
            # 3) Вариант без слова "составляет", но с "начальная (максимальная) цена контракта" и числом
            r'начальн[аяя][^\n]{0,40}?максимальн[аяя][^\n]{0,80}?цен[аы]\s+контракт[а]?[:\s]+(\d[\d\s]*[.,]?\d*)',
        ]
        
        for pattern in nmck_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nmck_str = match.group(1).replace(' ', '').replace(',', '.')
                try:
                    nmck_value = float(nmck_str)
                    result["nmck"] = f"{nmck_value:,.2f} ₽".replace(',', ' ')
                    result["nmck_numeric"] = nmck_value
                    break
                except ValueError:
                    pass
        
        # Если НМЦК всё ещё не найдена, пробуем более общий поиск: самое большое число с "руб/₽"
        if result["nmck_numeric"] is None:
            generic_match = re.findall(r'(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽)', text, re.IGNORECASE)
            if generic_match:
                try:
                    values = [float(m.replace(' ', '').replace(',', '.')) for m in generic_match]
                    if values:
                        nmck_value = max(values)
                        result["nmck"] = f"{nmck_value:,.2f} ₽".replace(',', ' ')
                        result["nmck_numeric"] = nmck_value
                except ValueError:
                    pass
        
        # Анализ обеспечения заявки/контракта
        guarantee_patterns = [
            r'обеспечени[ея]\s+заявк[и]?[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|%)',
            r'обеспечени[ея]\s+контракт[а]?[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|%)',
            r'обеспечени[ея][:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|%)',
            r'обеспечени[ея]\s+(\d[\d\s]*[.,]?\d*)\s*%',
        ]
        
        for pattern in guarantee_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                guarantee_str = match.group(1).replace(' ', '').replace(',', '.')
                try:
                    guarantee_value = float(guarantee_str)
                    if guarantee_value > 5:  # Более 5% - высокий риск
                        result["risks"].append({
                            "title": "Высокое обеспечение заявки/контракта",
                            "severity": "MEDIUM",
                            "description": f"Обеспечение {guarantee_value}% может быть завышенным",
                            "quote": text[match.start():match.end()+50]
                        })
                except ValueError:
                    pass
        
        # Анализ аванса
        advance_patterns = [
            r'аванс[а]?[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|%)',
            r'аванс[а]?\s+(\d[\d\s]*[.,]?\d*)\s*%',
            r'предоплат[аы][:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|%)',
        ]
        match = None
        for pattern in advance_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        if match:
            advance_str = match.group(1).replace(' ', '').replace(',', '.')
            try:
                advance_value = float(advance_str)
                if advance_value > 30:  # Более 30% - может быть проблемой
                    result["risks"].append({
                        "title": "Высокий размер аванса",
                        "severity": "LOW",
                        "description": f"Аванс {advance_value}% может быть ограничен бюджетным законодательством",
                        "quote": text[match.start():match.end()+50]
                    })
            except ValueError:
                pass
        
        return result


class RedFlagsDetector:
    """Детектор красных флагов в тендерной документации"""
    
    RED_FLAGS = [
        {
            "code": "IT_BRAND_ONLY",
            "pattern": r'\b(intel|amd|nvidia|lenovo|dell|hp)\b.*(?:без|не\s+допускается|исключительно)',
            "severity": "HIGH",
            "title": "Ограничение конкуренции по бренду",
            "law_reference": "ст. 33 44-ФЗ"
        },
        {
            "code": "TIME_UNREAL",
            "pattern": r'срок\s+исполнения[:\s]+(\d+)\s+(?:дн|день|дней)',
            "severity": "MEDIUM",
            "title": "Нереалистичные сроки исполнения",
            "law_reference": "Практика ФАС"
        },
        {
            "code": "PRICE_DUMPING",
            "pattern": r'цена\s+предложения\s+ниже\s+нмцк\s+более\s+25%',
            "severity": "HIGH",
            "title": "Признаки демпинга",
            "law_reference": "ст. 37 44-ФЗ"
        },
        {
            "code": "MIXED_LOT",
            "pattern": r'(?:компьютер|пк|ноутбук).*(?:office|microsoft\s+office)',
            "severity": "HIGH",
            "title": "Смешение оборудования и ПО в одном лоте",
            "law_reference": "Практика ФАС"
        }
    ]
    
    @staticmethod
    def detect(text: str) -> List[Dict]:
        """Обнаруживает красные флаги в тексте"""
        flags = []
        text_lower = text.lower()
        
        for flag_config in RedFlagsDetector.RED_FLAGS:
            pattern = flag_config["pattern"]
            match = re.search(pattern, text_lower, re.IGNORECASE)
            
            if match:
                flags.append({
                    "code": flag_config["code"],
                    "title": flag_config["title"],
                    "severity": flag_config["severity"],
                    "law_reference": flag_config["law_reference"],
                    "explanation": RedFlagsDetector._get_explanation(flag_config["code"]),
                    "quote": text[max(0, match.start()-100):min(len(text), match.end()+100)]
                })
        
        return flags
    
    @staticmethod
    def _get_explanation(code: str) -> str:
        """Возвращает объяснение для кода красного флага"""
        explanations = {
            "IT_BRAND_ONLY": "Требование конкретного бренда без 'или эквивалент' ограничивает конкуренцию",
            "TIME_UNREAL": "Сроки могут быть нереалистичными для выполнения работ",
            "PRICE_DUMPING": "Цена ниже НМЦК более чем на 25% может быть признана демпингом",
            "MIXED_LOT": "Смешение оборудования и ПО в одном лоте часто признается ограничением конкуренции"
        }
        return explanations.get(code, "Требует дополнительного анализа")


class IndustryHeuristics:
    """Отраслевые эвристики (уже частично реализованы в main.py)"""
    
    @staticmethod
    def enrich_it_issues(text: str, issues: List[Dict]) -> List[Dict]:
        """Добавляет IT-специфичные проблемы (уже есть в main.py)"""
        # Эта функция уже реализована в main.py как enrich_it_specific_issues
        # Здесь можно добавить дополнительные проверки
        return issues
    
    @staticmethod
    def enrich_construction_issues(text: str, issues: List[Dict]) -> List[Dict]:
        """Добавляет строительные проблемы (уже есть в main.py)"""
        # Эта функция уже реализована в main.py
        return issues
    
    @staticmethod
    def enrich_medicine_issues(text: str, issues: List[Dict]) -> List[Dict]:
        """Добавляет медицинские проблемы (уже есть в main.py)"""
        # Эта функция уже реализована в main.py
        return issues


def analyze_with_specialized_analyzers(text: str, industry: str = "UNIVERSAL") -> Dict:
    """Запускает все специализированные анализаторы"""
    result = {
        "legal_risks": [],
        "financial_analysis": {},
        "red_flags": [],
        "industry_issues": []
    }
    
    # Правовой анализ
    legal_analyzer = LegalRiskAnalyzer()
    result["legal_risks"].extend(legal_analyzer.analyze_44fz_risks(text))
    result["legal_risks"].extend(legal_analyzer.analyze_223fz_risks(text))
    
    # Финансовый анализ
    financial_analyzer = FinancialAnalyzer()
    result["financial_analysis"] = financial_analyzer.analyze_nmck(text)
    
    # Красные флаги
    red_flags_detector = RedFlagsDetector()
    result["red_flags"] = red_flags_detector.detect(text)
    
    # Отраслевые проблемы (используем существующие функции из main.py)
    industry_heuristics = IndustryHeuristics()
    if industry == "IT":
        result["industry_issues"] = industry_heuristics.enrich_it_issues(text, [])
    elif industry == "CONSTRUCTION":
        result["industry_issues"] = industry_heuristics.enrich_construction_issues(text, [])
    elif industry == "MEDICINE":
        result["industry_issues"] = industry_heuristics.enrich_medicine_issues(text, [])
    
    return result

