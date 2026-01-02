"""
Preprocessing & Evidence Layer — ШАГ 3

Архитектурный слой препроцессинга документов.
Преобразует Excel, PDF, сканы и чертежи в проверяемые Evidence Objects.

КРИТИЧЕСКИЕ ПРИНЦИПЫ:
1. LLM НЕ извлекает таблицы, суммы, структуру — только reasoning на готовых Evidence
2. Format-aware preprocessing обязателен
3. MCP — только специализированные ноды
4. Excel — источник истины (highest confidence)
5. OCR — только с валидацией и confidence map
6. Чертежи — только метаданные, не геометрия
"""

import os
import logging
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
import mimetypes

from evidence_types import (
    EvidenceObject,
    EvidenceClassification,
    EvidenceConfidence,
    FileFormatType,
    PreprocessingResult,
    EvidenceExtractionError,
)

# ФАЗА 2: Импорт расширенных типов для закупок
from core.evidence_types_extended import (
    EvidenceExtendedModel,
    classify_evidence_for_procurement,
    convert_to_extended,
    EvidenceSubClassification,
    EvidenceLegalBasis,
)

logger = logging.getLogger(__name__)


class FileClassifier:
    """Классификатор файлов по формату (format-aware preprocessing)."""
    
    @staticmethod
    def classify_file(file_path: str, filename: str) -> FileFormatType:
        """
        Классифицирует файл по типу формата.
        
        Неверная классификация = недостоверный анализ.
        """
        ext = (os.path.splitext(filename)[1] or "").lower()
        
        # Excel файлы
        if ext in (".xls", ".xlsx"):
            return FileFormatType.EXCEL_STRUCTURED
        
        # PDF файлы (требуется дополнительная проверка на сканы/таблицы)
        if ext == ".pdf":
            # TODO: Реализовать детекцию сканов и таблиц через MCP
            # Пока считаем текстовым
            return FileFormatType.PDF_TEXTUAL
        
        # DOCX файлы
        if ext in (".docx", ".doc"):
            return FileFormatType.DOCX_TEXTUAL
        
        # Чертежи (DWG, DXF и т.д.)
        if ext in (".dwg", ".dxf", ".dwf"):
            # TODO: Детекция векторных vs сканированных
            return FileFormatType.DRAWING_VECTOR
        
        return FileFormatType.UNKNOWN


class EvidencePreprocessor:
    """
    Ядро препроцессора с MCP-интеграцией.
    
    Каждый тип файла обрабатывается специализированным MCP-нодом.
    """
    
    def __init__(self):
        self.classifier = FileClassifier()
    
    def _detect_procurement_law(self, file_path: str, filename: str) -> str:
        """
        Определяет режим закупки (44-ФЗ или 223-ФЗ) на основе содержимого файла.
        
        Args:
            file_path: Путь к файлу
            filename: Имя файла
        
        Returns:
            "44-ФЗ" или "223-ФЗ"
        """
        # Пробуем прочитать начало файла для определения режима
        try:
            # Для DOCX/DOC файлов
            if filename.lower().endswith(('.docx', '.doc')):
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = " ".join([para.text for para in doc.paragraphs[:50]])  # Первые 50 параграфов
                except:
                    text = ""
            
            # Для PDF файлов
            elif filename.lower().endswith('.pdf'):
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = " ".join([page.extract_text() for page in pdf_reader.pages[:5]])  # Первые 5 страниц
                except:
                    text = ""
            
            else:
                text = ""
            
            text_lower = text.lower()
            
            # Признаки 44-ФЗ
            fz44_keywords = [
                "44-фз", "44 фз", "федеральный закон 44",
                "контрактная система", "государственные нужды", "муниципальные нужды",
                "еис", "единая информационная система", "zakupki.gov.ru"
            ]
            
            # Признаки 223-ФЗ
            fz223_keywords = [
                "223-фз", "223 фз", "федеральный закон 223",
                "положение о закупках", "отдельные виды юридических лиц",
                "госкорпорация", "естественная монополия"
            ]
            
            fz44_count = sum(1 for keyword in fz44_keywords if keyword in text_lower)
            fz223_count = sum(1 for keyword in fz223_keywords if keyword in text_lower)
            
            if fz223_count > fz44_count and fz223_count > 0:
                return "223-ФЗ"
            elif fz44_count > 0:
                return "44-ФЗ"
            else:
                # По умолчанию 44-ФЗ (более распространенный)
                return "44-ФЗ"
        
        except Exception as e:
            logger.warning(f"Не удалось определить режим закупки для {filename}: {e}")
            # По умолчанию 44-ФЗ
            return "44-ФЗ"
    
    async def preprocess_file(
        self,
        file_path: str,
        filename: str,
        industry: Optional[str] = None,
        procurement_law: Optional[str] = None
    ) -> PreprocessingResult:
        """
        Препроцессит файл и извлекает Evidence Objects.
        
        ФАЗА 2: Автоматически определяет режим закупки и классифицирует evidence
        для закупок (44-ФЗ или 223-ФЗ).
        
        Args:
            file_path: Путь к файлу
            filename: Имя файла
            industry: Отрасль (для контекста)
            procurement_law: Режим закупки ("44-ФЗ" или "223-ФЗ"). Если None, определяется автоматически.
        
        Returns:
            PreprocessingResult с массивом Evidence Objects (базовых, но готовых для расширения)
        """
        format_type = self.classifier.classify_file(file_path, filename)
        logger.info(f"📄 Классификация файла {filename}: {format_type}")
        
        # ФАЗА 2: Определяем режим закупки
        if procurement_law is None:
            procurement_law = self._detect_procurement_law(file_path, filename)
        logger.info(f"📋 Определен режим закупки: {procurement_law}")
        
        evidence_objects: List[EvidenceObject] = []
        errors: List[str] = []
        confidence_map: Optional[dict] = None
        
        try:
            if format_type == FileFormatType.EXCEL_STRUCTURED:
                result = await self._preprocess_excel(file_path, filename)
                evidence_objects.extend(result.evidence_objects)
                errors.extend(result.preprocessing_errors)
            
            elif format_type in (FileFormatType.PDF_TEXTUAL, FileFormatType.PDF_SCANNED, FileFormatType.PDF_WITH_TABLES):
                result = await self._preprocess_pdf(file_path, filename, format_type)
                evidence_objects.extend(result.evidence_objects)
                errors.extend(result.preprocessing_errors)
                confidence_map = result.confidence_map
            
            elif format_type == FileFormatType.DOCX_TEXTUAL:
                result = await self._preprocess_docx(file_path, filename)
                evidence_objects.extend(result.evidence_objects)
                errors.extend(result.preprocessing_errors)
            
            elif format_type in (FileFormatType.DRAWING_VECTOR, FileFormatType.DRAWING_SCANNED):
                result = await self._preprocess_drawing(file_path, filename, format_type)
                evidence_objects.extend(result.evidence_objects)
                errors.extend(result.preprocessing_errors)
            
            else:
                errors.append(f"Неподдерживаемый формат файла: {format_type}")
            
            # ФАЗА 2: Классифицируем evidence для закупок
            # Примечание: PreprocessingResult возвращает базовые EvidenceObject,
            # расширение до EvidenceExtendedModel происходит в reasoning_layer
            # Но мы можем добавить метаданные о режиме закупки в raw_extract
            
            for evidence in evidence_objects:
                if evidence.raw_extract is None:
                    evidence.raw_extract = f"procurement_law:{procurement_law}"
                else:
                    evidence.raw_extract += f"|procurement_law:{procurement_law}"
        
        except Exception as e:
            logger.error(f"Ошибка препроцессинга {filename}: {e}", exc_info=True)
            errors.append(f"Критическая ошибка препроцессинга: {str(e)}")
        
        return PreprocessingResult(
            file_path=file_path,
            filename=filename,
            format_type=format_type,
            evidence_objects=evidence_objects,
            preprocessing_errors=errors,
            confidence_map=confidence_map,
        )
    
    async def _preprocess_excel(
        self,
        file_path: str,
        filename: str
    ) -> PreprocessingResult:
        """
        Препроцессинг Excel файлов.
        
        Excel — источник истины (highest confidence).
        Извлекаются: таблицы, формулы, зависимости, итоги, валюты.
        """
        evidence_objects: List[EvidenceObject] = []
        errors: List[str] = []
        
        try:
            # TODO: Интеграция с excel-mcp для детерминированного извлечения
            # Пока используем fallback на openpyxl/xlrd
            
            ext = (os.path.splitext(filename)[1] or "").lower()
            
            if ext == ".xlsx":
                from openpyxl import load_workbook
                wb = load_workbook(file_path, data_only=False, read_only=True)  # data_only=False для формул
                
                for ws in wb.worksheets:
                    sheet_name = ws.title
                    
                    # Извлекаем таблицы (структура)
                    # TODO: Детекция таблиц через excel-mcp
                    
                    # Извлекаем формулы
                    for row in ws.iter_rows():
                        for cell in row:
                            if cell.data_type == "f":  # Formula
                                formula = cell.value
                                evidence_objects.append(
                                    EvidenceObject(
                                        evidence_id=f"E-{uuid.uuid4().hex[:8].upper()}",
                                        source_file=filename,
                                        fact=f"Формула в ячейке {cell.coordinate}: {formula}",
                                        classification=EvidenceClassification.CONTROLLED_RISK,
                                        financial_impact_rub=None,
                                        confidence=EvidenceConfidence.HIGH,
                                        derived_from=["excel-mcp-fallback"],
                                        page_reference=f"Лист: {sheet_name}",
                                        section_reference=cell.coordinate,
                                        raw_extract=str(formula),
                                    )
                                )
                    
                    # Извлекаем итоговые поля (SUM, COUNT и т.д.)
                    # TODO: Детекция через excel-mcp
                
                wb.close()
            
            elif ext == ".xls":
                import xlrd
                workbook = xlrd.open_workbook(file_path)
                
                for sheet_name in workbook.sheet_names():
                    sheet = workbook.sheet_by_name(sheet_name)
                    # TODO: Извлечение через excel-mcp
                
                # Пока минимальная обработка
                evidence_objects.append(
                    EvidenceObject(
                        evidence_id=f"E-{uuid.uuid4().hex[:8].upper()}",
                        source_file=filename,
                        fact=f"Excel файл содержит {len(workbook.sheet_names())} листов",
                        classification=EvidenceClassification.MARKET_NOISE,
                        financial_impact_rub=None,
                        confidence=EvidenceConfidence.HIGH,
                        derived_from=["excel-mcp-fallback"],
                        page_reference=None,
                        section_reference=None,
                    )
                )
        
        except Exception as e:
            logger.error(f"Ошибка препроцессинга Excel {filename}: {e}", exc_info=True)
            errors.append(f"Ошибка обработки Excel: {str(e)}")
        
        return PreprocessingResult(
            file_path=file_path,
            filename=filename,
            format_type=FileFormatType.EXCEL_STRUCTURED,
            evidence_objects=evidence_objects,
            preprocessing_errors=errors,
        )
    
    async def _preprocess_pdf(
        self,
        file_path: str,
        filename: str,
        format_type: FileFormatType
    ) -> PreprocessingResult:
        """
        Препроцессинг PDF файлов.
        
        OCR данные никогда не идут напрямую в LLM.
        Сопровождаются confidence map.
        При низкой уверенности маркируются как CONTROLLED_RISK: LOW_EVIDENCE.
        """
        evidence_objects: List[EvidenceObject] = []
        errors: List[str] = []
        confidence_map: Optional[dict] = None
        
        try:
            # TODO: Интеграция с pdf-table-mcp и pdf-ocr-mcp
            
            if format_type == FileFormatType.PDF_SCANNED:
                # OCR с валидацией
                # TODO: Вызов pdf-ocr-mcp с confidence map
                confidence_map = {"overall": "low"}  # Placeholder
                
                evidence_objects.append(
                    EvidenceObject(
                        evidence_id=f"E-{uuid.uuid4().hex[:8].upper()}",
                        source_file=filename,
                        fact="PDF файл является сканом (требует OCR)",
                        classification=EvidenceClassification.CONTROLLED_RISK,
                        financial_impact_rub=None,
                        confidence=EvidenceConfidence.LOW,
                        derived_from=["pdf-ocr-mcp-fallback"],
                        page_reference=None,
                        section_reference=None,
                    )
                )
            
            elif format_type == FileFormatType.PDF_WITH_TABLES:
                # Извлечение таблиц
                # TODO: Вызов pdf-table-mcp
                pass
            
            else:
                # Текстовый PDF
                # TODO: Извлечение структурированных фактов через pdf-text-mcp
                pass
        
        except Exception as e:
            logger.error(f"Ошибка препроцессинга PDF {filename}: {e}", exc_info=True)
            errors.append(f"Ошибка обработки PDF: {str(e)}")
        
        return PreprocessingResult(
            file_path=file_path,
            filename=filename,
            format_type=format_type,
            evidence_objects=evidence_objects,
            preprocessing_errors=errors,
            confidence_map=confidence_map,
        )
    
    async def _preprocess_docx(
        self,
        file_path: str,
        filename: str
    ) -> PreprocessingResult:
        """
        Препроцессинг DOCX файлов.
        """
        evidence_objects: List[EvidenceObject] = []
        errors: List[str] = []
        
        try:
            # TODO: Интеграция с docx-mcp для структурированного извлечения
            # Пока минимальная обработка
            pass
        
        except Exception as e:
            logger.error(f"Ошибка препроцессинга DOCX {filename}: {e}", exc_info=True)
            errors.append(f"Ошибка обработки DOCX: {str(e)}")
        
        return PreprocessingResult(
            file_path=file_path,
            filename=filename,
            format_type=FileFormatType.DOCX_TEXTUAL,
            evidence_objects=evidence_objects,
            preprocessing_errors=errors,
        )
    
    async def _preprocess_drawing(
        self,
        file_path: str,
        filename: str,
        format_type: FileFormatType
    ) -> PreprocessingResult:
        """
        Препроцессинг чертежей.
        
        Из чертежей извлекаются только управленческие сигналы:
        - стадия проектирования
        - полнота спецификаций
        - ссылки на нормы
        - ожидаемая координационная нагрузка
        
        Попытка «понять чертёж» через LLM запрещена.
        """
        evidence_objects: List[EvidenceObject] = []
        errors: List[str] = []
        
        try:
            # TODO: Интеграция с drawing-metadata-mcp
            # Извлечение только метаданных, не геометрии
            
            evidence_objects.append(
                EvidenceObject(
                    evidence_id=f"E-{uuid.uuid4().hex[:8].upper()}",
                    source_file=filename,
                    fact="Чертёж требует проверки метаданных (стадия, нормы, спецификации)",
                    classification=EvidenceClassification.CONTROLLED_RISK,
                    financial_impact_rub=None,
                    confidence=EvidenceConfidence.MEDIUM,
                    derived_from=["drawing-metadata-mcp-fallback"],
                    page_reference=None,
                    section_reference=None,
                )
            )
        
        except Exception as e:
            logger.error(f"Ошибка препроцессинга чертежа {filename}: {e}", exc_info=True)
            errors.append(f"Ошибка обработки чертежа: {str(e)}")
        
        return PreprocessingResult(
            file_path=file_path,
            filename=filename,
            format_type=format_type,
            evidence_objects=evidence_objects,
            preprocessing_errors=errors,
        )





























