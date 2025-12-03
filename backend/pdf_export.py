"""
Модуль для экспорта результатов анализа в PDF
"""

import logging
from typing import Dict, Optional
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab не установлен. Экспорт в PDF недоступен. Установите: pip install reportlab")


def generate_pdf_report(analysis_data: Dict, filename: str = None) -> BytesIO:
    """Генерирует PDF отчет из данных анализа
    
    Args:
        analysis_data: Словарь с данными анализа
        filename: Имя файла (опционально)
        
    Returns:
        BytesIO объект с PDF содержимым
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab не установлен. Установите: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    
    # Стили
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    # Содержимое документа
    story = []
    
    # Заголовок
    story.append(Paragraph("Отчет об анализе тендерной документации", title_style))
    story.append(Spacer(1, 12))
    
    # Информация о документе
    doc_filename = analysis_data.get("filename", "Неизвестный файл")
    industry = analysis_data.get("industry", "UNIVERSAL")
    score = analysis_data.get("score", 0)
    verdict = analysis_data.get("verdict", "CAUTION")
    summary = analysis_data.get("summary", "Нет описания")
    
    story.append(Paragraph(f"<b>Файл:</b> {doc_filename}", normal_style))
    story.append(Paragraph(f"<b>Отрасль:</b> {industry}", normal_style))
    story.append(Paragraph(f"<b>Дата анализа:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
    story.append(Spacer(1, 12))
    
    # Оценка и вердикт
    verdict_text = {
        "STOP": "НЕ РЕКОМЕНДУЕТСЯ УЧАСТИЕ",
        "CAUTION": "ТРЕБУЕТСЯ ВНИМАНИЕ",
        "PARTICIPATE": "РЕКОМЕНДУЕТСЯ УЧАСТИЕ"
    }.get(verdict, verdict)
    
    verdict_color = {
        "STOP": colors.HexColor('#e74c3c'),
        "CAUTION": colors.HexColor('#f39c12'),
        "PARTICIPATE": colors.HexColor('#27ae60')
    }.get(verdict, colors.HexColor('#333333'))
    
    verdict_style = ParagraphStyle(
        'Verdict',
        parent=normal_style,
        fontSize=14,
        textColor=verdict_color,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    story.append(Paragraph(f"<b>Оценка безопасности:</b> {score}/100", heading_style))
    story.append(Paragraph(f"<b>{verdict_text}</b>", verdict_style))
    story.append(Spacer(1, 12))
    
    # Краткое описание
    story.append(Paragraph("<b>Краткое описание:</b>", heading_style))
    story.append(Paragraph(summary, normal_style))
    story.append(Spacer(1, 12))
    
    # Паспорт документа
    passport = analysis_data.get("passport", {})
    if passport:
        story.append(Paragraph("<b>Паспорт документа:</b>", heading_style))
        passport_data = [
            ["Параметр", "Значение"],
            ["НМЦК", passport.get("nmck", "Не указано")],
            ["Регион", passport.get("region", "Не указано")],
            ["Закон", passport.get("fz", "Не указано")],
            ["Дедлайн подачи заявки", passport.get("deadlineApp", "Не указано")],
            ["Обеспечение", passport.get("guarantee", "Не указано")]
        ]
        
        passport_table = Table(passport_data, colWidths=[60*mm, 110*mm])
        passport_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        story.append(passport_table)
        story.append(Spacer(1, 12))
    
    # Риски и проблемы
    issues = analysis_data.get("issues", [])
    if issues:
        story.append(Paragraph("<b>Выявленные риски и проблемы:</b>", heading_style))
        
        for i, issue in enumerate(issues[:20], 1):  # Ограничиваем 20 рисками
            severity = issue.get("severity", "MEDIUM")
            title = issue.get("title", "Неизвестный риск")
            description = issue.get("description", "")
            quote = issue.get("quote", "")
            
            severity_color_map = {
                "HIGH": '#e74c3c',
                "MEDIUM": '#f39c12',
                "LOW": '#3498db'
            }
            color_hex = severity_color_map.get(severity, '#333333')
            
            severity_color = colors.HexColor(color_hex)
            
            severity_text = {
                "HIGH": "КРИТИЧНО",
                "MEDIUM": "СРЕДНЕ",
                "LOW": "НИЗКО"
            }.get(severity, severity)
            
            story.append(Paragraph(
                f"<b>{i}. {title}</b> <font color='{color_hex}'>[{severity_text}]</font>",
                normal_style
            ))
            if description:
                story.append(Paragraph(description, normal_style))
            if quote:
                quote_style = ParagraphStyle(
                    'Quote',
                    parent=normal_style,
                    leftIndent=10,
                    rightIndent=10,
                    borderColor=colors.HexColor('#bdc3c7'),
                    borderWidth=1,
                    borderPadding=5,
                    backColor=colors.HexColor('#f8f9fa')
                )
                story.append(Paragraph(f"<i>\"{quote}\"</i>", quote_style))
            story.append(Spacer(1, 8))
        
        if len(issues) > 20:
            story.append(Paragraph(f"<i>... и еще {len(issues) - 20} рисков</i>", normal_style))
        story.append(Spacer(1, 12))
    
    # Спецификация
    specs = analysis_data.get("specs", [])
    if specs:
        story.append(Paragraph("<b>Спецификация товаров/работ:</b>", heading_style))
        specs_data = [["№", "Наименование", "Количество", "Характеристики"]]
        
        for i, spec in enumerate(specs[:15], 1):  # Ограничиваем 15 позициями
            specs_data.append([
                str(i),
                spec.get("name", "Не указано"),
                spec.get("qty", "Не указано"),
                spec.get("details", "Не указано")
            ])
        
        specs_table = Table(specs_data, colWidths=[10*mm, 60*mm, 30*mm, 70*mm])
        specs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        story.append(specs_table)
        story.append(Spacer(1, 12))
    
    # Рекомендации
    actions = analysis_data.get("actions", [])
    if actions:
        story.append(Paragraph("<b>Рекомендуемые действия:</b>", heading_style))
        for i, action in enumerate(actions[:10], 1):  # Ограничиваем 10 действиями
            action_type = action.get("type", "")
            action_text = action.get("text", "")
            priority = action.get("priority", 0)
            
            story.append(Paragraph(
                f"<b>{i}. [{action_type}]</b> {action_text}",
                normal_style
            ))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 12))
    
    # Футер
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<i>Отчет сгенерирован системой Tender Shield Pro</i><br/>"
        f"<i>Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>",
        ParagraphStyle(
            'Footer',
            parent=normal_style,
            fontSize=8,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        )
    ))
    
    # Собираем PDF
    doc.build(story)
    buffer.seek(0)
    
    return buffer


def export_analysis_to_pdf(analysis_id: int, db) -> Optional[BytesIO]:
    """Экспортирует анализ из БД в PDF
    
    Args:
        analysis_id: ID анализа в БД
        db: Сессия БД
        
    Returns:
        BytesIO объект с PDF или None если анализ не найден
    """
    from database import Analysis
    
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        return None
    
    analysis_data = analysis.result_json
    analysis_data["filename"] = analysis.filename
    analysis_data["industry"] = analysis.industry
    
    return generate_pdf_report(analysis_data, analysis.filename)

