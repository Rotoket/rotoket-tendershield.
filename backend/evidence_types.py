"""
Evidence Types — ШАГ 3: Preprocessing & Evidence Layer

Этот модуль определяет канонические типы для Evidence Objects.
Любые изменения должны соответствовать архитектурному контракту ШАГА 3.
"""

from typing import Literal, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class EvidenceClassification(str, Enum):
    """Классификация Evidence по управленческому воздействию."""
    DEAL_BREAKER = "DEAL_BREAKER"
    CONTROLLED_RISK = "CONTROLLED_RISK"
    MARKET_NOISE = "MARKET_NOISE"


class EvidenceConfidence(str, Enum):
    """Уровень уверенности в извлечённом факте."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FileFormatType(str, Enum):
    """Классификация файлов по формату (format-aware preprocessing)."""
    EXCEL_STRUCTURED = "excel_structured"
    PDF_TEXTUAL = "pdf_textual"
    PDF_SCANNED = "pdf_scanned"
    PDF_WITH_TABLES = "pdf_with_tables"
    DRAWING_VECTOR = "drawing_vector"
    DRAWING_SCANNED = "drawing_scanned"
    DOCX_TEXTUAL = "docx_textual"
    UNKNOWN = "unknown"


class EvidenceObject(BaseModel):
    """
    Единственный допустимый выход ШАГА 3.
    
    LLM работает только с этим форматом, не с сырым текстом.
    """
    evidence_id: str = Field(..., description="Уникальный идентификатор Evidence (E-XXXX)")
    source_file: str = Field(..., description="Имя исходного файла")
    fact: str = Field(..., description="Извлечённый факт (детерминированный, не интерпретация)")
    classification: EvidenceClassification = Field(..., description="Классификация по управленческому воздействию")
    financial_impact_rub: Optional[float] = Field(None, description="Финансовое воздействие в рублях (если применимо)")
    confidence: EvidenceConfidence = Field(..., description="Уровень уверенности в извлечённом факте")
    derived_from: List[str] = Field(default_factory=list, description="Список MCP-нод, из которых извлечён факт")
    
    # Метаданные для traceability
    page_reference: Optional[str] = Field(None, description="Ссылка на страницу/лист (если применимо)")
    section_reference: Optional[str] = Field(None, description="Ссылка на раздел/пункт (если применимо)")
    raw_extract: Optional[str] = Field(None, description="Сырой извлечённый фрагмент (для аудита)")


class PreprocessingResult(BaseModel):
    """
    Результат препроцессинга одного файла.
    
    Содержит классификацию файла и массив Evidence Objects.
    """
    file_path: str
    filename: str
    format_type: FileFormatType
    evidence_objects: List[EvidenceObject] = Field(default_factory=list)
    preprocessing_errors: List[str] = Field(default_factory=list)
    confidence_map: Optional[dict] = Field(None, description="Карта уверенности для OCR/сканов")


class EvidenceExtractionError(Exception):
    """Исключение при ошибке извлечения Evidence."""
    pass































