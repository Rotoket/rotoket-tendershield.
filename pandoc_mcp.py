"""
MCP-сервер для конвертации документов тендеров через Pandoc.
Создан для надежной работы на сервере без зависимости от npm пакетов.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

try:
    from mcp import FastMCP
except ImportError:
    print("ERROR: mcp library not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Инициализация MCP сервера
mcp = FastMCP("TenderShield-Pandoc-Converter")

# Путь к pandoc (можно переопределить через переменную окружения)
PANDOC_PATH = os.environ.get("PANDOC_PATH", "pandoc")


def check_pandoc_available() -> bool:
    """Проверяет доступность Pandoc в системе."""
    try:
        result = subprocess.run(
            [PANDOC_PATH, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


@mcp.tool()
def convert_to_markdown(file_path: str, output_path: Optional[str] = None) -> dict:
    """
    Конвертирует документ тендера (DOCX, DOC, XLSX и др.) в Markdown для точного анализа.
    
    Args:
        file_path: Путь к исходному файлу (DOCX, DOC, XLSX и др.)
        output_path: Опциональный путь для сохранения результата. Если не указан, 
                    создается временный файл с расширением .md
    
    Returns:
        dict с полями:
        - success: bool - успешность операции
        - output_path: str - путь к созданному Markdown файлу
        - content: str - содержимое Markdown (первые 1000 символов для preview)
        - error: str - сообщение об ошибке (если есть)
    """
    # Проверка доступности Pandoc
    if not check_pandoc_available():
        return {
            "success": False,
            "error": f"Pandoc не найден в системе. Убедитесь, что Pandoc установлен и доступен в PATH, или установите переменную окружения PANDOC_PATH."
        }
    
    # Проверка существования файла
    source_path = Path(file_path)
    if not source_path.exists():
        return {
            "success": False,
            "error": f"Файл не найден: {file_path}"
        }
    
    # Определение выходного файла
    if output_path:
        output_file = Path(output_path)
    else:
        # Создаем временный файл рядом с исходным
        output_file = source_path.parent / f"{source_path.stem}_converted.md"
    
    try:
        # Определение формата входного файла
        ext = source_path.suffix.lower()
        format_map = {
            '.docx': 'docx',
            '.doc': 'doc',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.odt': 'odt',
            '.rtf': 'rtf',
            '.html': 'html',
            '.htm': 'html',
        }
        
        input_format = format_map.get(ext, 'docx')
        
        # Выполнение конвертации
        result = subprocess.run(
            [PANDOC_PATH, '-f', input_format, '-t', 'markdown', str(source_path), '-o', str(output_file)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60  # 60 секунд максимум
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Ошибка Pandoc: {result.stderr[:500]}",
                "output_path": None
            }
        
        # Чтение результата для preview
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                preview = content[:1000] + "..." if len(content) > 1000 else content
        except Exception as e:
            preview = f"[Не удалось прочитать файл: {str(e)}]"
        
        return {
            "success": True,
            "output_path": str(output_file),
            "content": preview,
            "content_length": len(content) if 'content' in locals() else 0,
            "message": f"Успешно конвертировано: {source_path.name} -> {output_file.name}"
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Превышено время ожидания конвертации (60 секунд). Файл слишком большой или Pandoc завис."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Неожиданная ошибка: {str(e)}"
        }


@mcp.tool()
def extract_nmck_iun(file_path: str) -> dict:
    """
    Извлекает НМЦК (Начальная максимальная цена контракта) и ИУН (Идентификационный номер закупки)
    из документа тендера через конвертацию в Markdown и анализ.
    
    Args:
        file_path: Путь к документу тендера
    
    Returns:
        dict с полями:
        - success: bool
        - nmck: Optional[str] - найденная НМЦК
        - nmck_numeric: Optional[float] - числовое значение НМЦК
        - iun: Optional[str] - найденный ИУН
        - markdown_path: Optional[str] - путь к временному Markdown файлу
        - error: Optional[str] - сообщение об ошибке
    """
    import re
    
    # Сначала конвертируем в Markdown
    conversion_result = convert_to_markdown(file_path)
    
    if not conversion_result.get("success"):
        return {
            "success": False,
            "error": f"Не удалось конвертировать документ: {conversion_result.get('error', 'Unknown error')}"
        }
    
    markdown_path = conversion_result["output_path"]
    
    try:
        # Читаем Markdown
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result = {
            "success": True,
            "nmck": None,
            "nmck_numeric": None,
            "iun": None,
            "markdown_path": markdown_path
        }
        
        # Поиск НМЦК
        nmck_patterns = [
            r'нмцк[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|rub)',
            r'нмц[:\s]+(\d[\d\s]*[.,]?\d*)',
            r'начальн[аяя][^\n]{0,80}?цен[аы]\s+контракт[а]?[^\n]{0,80}?составляет[:\s]+(\d[\d\s]*[.,]?\d*)',
            r'нмцк\s+составляет[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽)',
            r'(\d[\d\s]{3,}[.,]?\d*)\s*(?:руб|₽).*?нмцк',
        ]
        
        for pattern in nmck_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value_str = match.group(1).replace(' ', '').replace(',', '.').strip()
                try:
                    value = float(value_str)
                    # Проверяем множитель (млн, тыс)
                    context = content[max(0, match.start()-50):match.end()+50].lower()
                    if 'млн' in context:
                        value *= 1_000_000
                    elif 'тыс' in context:
                        value *= 1_000
                    
                    result["nmck"] = f"{value:,.2f} руб."
                    result["nmck_numeric"] = value
                    break
                except ValueError:
                    continue
            if result["nmck"]:
                break
        
        # Поиск ИУН (идентификационный номер закупки)
        iun_patterns = [
            r'идентификационн[ыйой]+[^\n]{0,50}?номер[^\n]{0,50}?закупк[иы][:\s]+(\d+)',
            r'иун[:\s]+(\d+)',
            r'идентификационн[ыйой]+[^\n]{0,50}?код[^\n]{0,50}?закупк[иы][:\s]+(\d+)',
            r'номер[^\n]{0,30}?закупк[иы][:\s]+(\d{10,})',  # ИУН обычно длинный
        ]
        
        for pattern in iun_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                iun = match.group(1).strip()
                if len(iun) >= 10:  # ИУН обычно длинный номер
                    result["iun"] = iun
                    break
            if result["iun"]:
                break
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при извлечении данных: {str(e)}",
            "markdown_path": markdown_path
        }


@mcp.tool()
def extract_from_tender_docx(file_path: str) -> dict:
    """
    ФАЗА 4: Извлекает структурированные данные из DOCX документа тендера.
    
    Извлекает:
    - НМЦК (Начальная максимальная цена контракта)
    - Заказчик (название организации)
    - Дедлайн подачи заявок
    - Сроки контракта
    - Обеспечение (процент или сумма)
    - Режим закупки (44-ФЗ / 223-ФЗ)
    - ИУН (Идентификационный номер закупки)
    - География (регион, ЗАТО)
    - Требования к сертификатам
    
    Args:
        file_path: Путь к DOCX файлу тендера
    
    Returns:
        dict с полями:
        - success: bool
        - data: dict - структурированные данные
        - markdown_path: str - путь к временному Markdown файлу
        - error: Optional[str] - сообщение об ошибке
    """
    import re
    import json
    from datetime import datetime
    
    # Сначала конвертируем в Markdown
    conversion_result = convert_to_markdown(file_path)
    
    if not conversion_result.get("success"):
        return {
            "success": False,
            "error": f"Не удалось конвертировать документ: {conversion_result.get('error', 'Unknown error')}"
        }
    
    markdown_path = conversion_result["output_path"]
    
    try:
        # Читаем Markdown
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        result_data = {
            "nmck": None,
            "nmck_numeric": None,
            "customer": None,
            "deadline": None,
            "contract_term_months": None,
            "guarantee": None,
            "guarantee_percent": None,
            "procurement_law": None,
            "iun": None,
            "region": None,
            "is_zato": False,
            "certification_requirements": [],
            "payment_terms": None,
            "penalty_percent": None,
        }
        
        content_lower = content.lower()
        
        # 1. Извлечение НМЦК
        nmck_patterns = [
            r'нмцк[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽|rub)',
            r'нмц[:\s]+(\d[\d\s]*[.,]?\d*)',
            r'начальн[аяя][^\n]{0,80}?цен[аы]\s+контракт[а]?[^\n]{0,80}?составляет[:\s]+(\d[\d\s]*[.,]?\d*)',
            r'нмцк\s+составляет[:\s]+(\d[\d\s]*[.,]?\d*)\s*(?:руб|₽)',
            r'(\d[\d\s]{3,}[.,]?\d*)\s*(?:руб|₽).*?нмцк',
        ]
        
        for pattern in nmck_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                value_str = match.group(1).replace(' ', '').replace(',', '.').strip()
                try:
                    value = float(value_str)
                    # Проверяем множитель (млн, тыс)
                    context = content[max(0, match.start()-50):match.end()+50].lower()
                    if 'млн' in context:
                        value *= 1_000_000
                    elif 'тыс' in context:
                        value *= 1_000
                    
                    result_data["nmck"] = f"{value:,.2f} руб."
                    result_data["nmck_numeric"] = value
                    break
                except ValueError:
                    continue
            if result_data["nmck"]:
                break
        
        # 2. Извлечение заказчика
        customer_patterns = [
            r'заказчик[:\s]+([^\n]{10,200})',
            r'организатор[:\s]+([^\n]{10,200})',
            r'государственн[ыйой]+\s+заказчик[:\s]+([^\n]{10,200})',
            r'муниципальн[ыйой]+\s+заказчик[:\s]+([^\n]{10,200})',
        ]
        
        for pattern in customer_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                customer = match.group(1).strip()
                # Очищаем от лишних символов
                customer = re.sub(r'[^\w\s\-\(\)\.]', '', customer).strip()
                if len(customer) > 10 and len(customer) < 200:
                    result_data["customer"] = customer
                    break
        
        # 3. Извлечение дедлайна
        deadline_patterns = [
            r'крайн[ийей]+\s+срок\s+подач[иы]\s+заявок[:\s]+(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})',
            r'срок\s+подач[иы]\s+заявок[:\s]+(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})',
            r'дедлайн[:\s]+(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4})',
            r'(\d{1,2}[\.\/]\d{1,2}[\.\/]\d{2,4}).*?подач[иы]\s+заявок',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Пробуем разные форматы даты
                    for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%d.%m.%y', '%d/%m/%y']:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            result_data["deadline"] = date_obj.strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                    if result_data["deadline"]:
                        break
                except Exception:
                    continue
        
        # 4. Извлечение сроков контракта (в месяцах)
        term_patterns = [
            r'срок\s+выполнен[ия][:\s]+(\d+)\s*(?:мес|месяц)',
            r'период\s+выполнен[ия][:\s]+(\d+)\s*(?:мес|месяц)',
            r'срок\s+контракт[а][:\s]+(\d+)\s*(?:мес|месяц)',
            r'(\d+)\s*(?:мес|месяц).*?выполнен[ия]',
        ]
        
        for pattern in term_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    months = int(match.group(1))
                    result_data["contract_term_months"] = months
                    break
                except ValueError:
                    continue
        
        # Если срок в годах, конвертируем
        if not result_data["contract_term_months"]:
            year_patterns = [
                r'срок\s+выполнен[ия][:\s]+(\d+)\s*(?:год|лет)',
                r'период\s+выполнен[ия][:\s]+(\d+)\s*(?:год|лет)',
            ]
            for pattern in year_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        years = int(match.group(1))
                        result_data["contract_term_months"] = years * 12
                        break
                    except ValueError:
                        continue
        
        # 5. Извлечение обеспечения
        guarantee_patterns = [
            r'обеспечен[ие][:\s]+(\d+)\s*%',
            r'гарантийн[оеые]+\s+обеспечен[ие][:\s]+(\d+)\s*%',
            r'обеспечен[ие]\s+заявк[иы][:\s]+(\d+)\s*%',
            r'(\d+)\s*%.*?обеспечен[ие]',
        ]
        
        for pattern in guarantee_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    percent = int(match.group(1))
                    result_data["guarantee_percent"] = percent
                    result_data["guarantee"] = f"{percent}%"
                    break
                except ValueError:
                    continue
        
        # 6. Определение режима закупки
        if '44-фз' in content_lower or 'федеральный закон № 44' in content_lower:
            result_data["procurement_law"] = "44-ФЗ"
        elif '223-фз' in content_lower or 'федеральный закон № 223' in content_lower:
            result_data["procurement_law"] = "223-ФЗ"
        
        # 7. Извлечение ИУН
        iun_patterns = [
            r'идентификационн[ыйой]+[^\n]{0,50}?номер[^\n]{0,50}?закупк[иы][:\s]+(\d+)',
            r'иун[:\s]+(\d+)',
            r'идентификационн[ыйой]+[^\n]{0,50}?код[^\n]{0,50}?закупк[иы][:\s]+(\d+)',
            r'номер[^\n]{0,30}?закупк[иы][:\s]+(\d{10,})',
        ]
        
        for pattern in iun_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                iun = match.group(1).strip()
                if len(iun) >= 10:
                    result_data["iun"] = iun
                    break
        
        # 8. Определение ЗАТО
        if re.search(r'\bзато\b|\bзакрытое административно-территориальное образование\b', content, re.IGNORECASE):
            result_data["is_zato"] = True
        
        # 9. Извлечение требований к сертификатам
        cert_patterns = [
            r'сертификат\s+соответстви[я][^\n]{0,100}',
            r'деклараци[я]\s+о\s+соответстви[и][^\n]{0,100}',
            r'тр\s+еаэс[^\n]{0,100}',
            r'техническ[ийой]+\s+регламент[^\n]{0,100}',
        ]
        
        for pattern in cert_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                cert_text = match.group(0).strip()
                if cert_text not in result_data["certification_requirements"]:
                    result_data["certification_requirements"].append(cert_text)
        
        # 10. Извлечение условий оплаты
        payment_patterns = [
            r'оплат[аы][:\s]+(\d+)\s*(?:день|дней|дн)',
            r'срок\s+оплат[ыы][:\s]+(\d+)\s*(?:день|дней|дн)',
            r'(\d+)\s*(?:день|дней|дн).*?оплат[аы]',
        ]
        
        for pattern in payment_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    days = int(match.group(1))
                    result_data["payment_terms"] = f"{days} дней"
                    break
                except ValueError:
                    continue
        
        # 11. Извлечение штрафов
        penalty_patterns = [
            r'штраф[:\s]+(\d+)\s*%',
            r'неустойк[аы][:\s]+(\d+)\s*%',
            r'(\d+)\s*%.*?штраф',
        ]
        
        for pattern in penalty_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    percent = int(match.group(1))
                    result_data["penalty_percent"] = percent
                    break
                except ValueError:
                    continue
        
        return {
            "success": True,
            "data": result_data,
            "markdown_path": markdown_path,
            "message": "Структурированные данные успешно извлечены"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Ошибка при извлечении данных: {str(e)}",
            "markdown_path": markdown_path
        }


if __name__ == "__main__":
    # Запуск MCP сервера
    mcp.run()

