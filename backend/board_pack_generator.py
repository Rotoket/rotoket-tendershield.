"""
Board Pack Generator — ШАГ 12: Board Pack (PDF экспорт Decision Records)

Канонический Board Pack всегда содержит 7 секций:
1. Executive Summary
2. Tender Context
3. Decision
4. Decision Grounds
5. Financial Snapshot
6. Next Steps
7. Audit Note

ПРИНЦИП:
Board Pack = доказательство решения, а не презентация.
Не содержит "ИИ считает", технические термины, неопределённые формулировки.
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
    logger.warning("reportlab не установлен. Board Pack генерация недоступна. Установите: pip install reportlab")


def format_decision_label(decision: str) -> str:
    """Форматирует решение для отображения"""
    decision_map = {
        "PARTICIPATE": "УЧАСТВОВАТЬ",
        "DO_NOT_PARTICIPATE": "НЕ УЧАСТВОВАТЬ",
        "PARTICIPATE_WITH_CONDITIONS": "УЧАСТВОВАТЬ С УСЛОВИЯМИ",
        "POSTPONE": "ОТЛОЖИТЬ РЕШЕНИЕ",
    }
    return decision_map.get(decision, decision)


def generate_board_pack(decision_record: Dict, analysis_data: Optional[Dict] = None) -> BytesIO:
    """
    Генерирует Board Pack (PDF) из Decision Record.
    
    Канонические 7 секций:
    1. Executive Summary
    2. Tender Context
    3. Decision
    4. Decision Grounds
    5. Financial Snapshot
    6. Next Steps
    7. Audit Note
    
    Args:
        decision_record: Словарь с данными Decision Record (канонические 7 полей)
        analysis_data: Опциональные данные анализа для Financial Snapshot и Tender Context
    
    Returns:
        BytesIO объект с PDF содержимым
    """
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab не установлен. Установите: pip install reportlab")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        rightMargin=20*mm, 
        leftMargin=20*mm, 
        topMargin=20*mm, 
        bottomMargin=20*mm
    )
    
    # Стили
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'BoardPackTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=16,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    section_style = ParagraphStyle(
        'BoardPackSection',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=16,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
        backColor=colors.HexColor('#f8f9fa'),
        leftIndent=0,
        rightIndent=0
    )
    
    normal_style = ParagraphStyle(
        'BoardPackNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        spaceAfter=8,
        leading=14
    )
    
    emphasis_style = ParagraphStyle(
        'BoardPackEmphasis',
        parent=normal_style,
        fontSize=12,
        textColor=colors.HexColor('#1a1a1a'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    # Содержимое документа
    story = []
    
    # Заголовок документа
    story.append(Paragraph("BOARD PACK", title_style))
    story.append(Paragraph("Управленческое решение по тендеру", ParagraphStyle(
        'Subtitle',
        parent=normal_style,
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20
    )))
    story.append(Spacer(1, 12))
    
    # ========== 1. EXECUTIVE SUMMARY ==========
    story.append(Paragraph("1. EXECUTIVE SUMMARY", section_style))
    
    executive_summary = (
        f"Принято решение <b>{format_decision_label(decision_record.get('decision', ''))}</b> "
        f"по тендеру <b>{decision_record.get('tender_id', 'N/A')}</b>. "
        f"Объект закупки: {decision_record.get('tender_object', 'Не указан')}. "
        f"Индекс управленческой нагрузки: <b>{decision_record.get('management_load_index', 0)}</b>. "
        f"Решение зафиксировано {datetime.fromisoformat(decision_record.get('fixed_at', datetime.now().isoformat())).strftime('%d.%m.%Y %H:%M')} "
        f"ответственным лицом: <b>{decision_record.get('responsible_person', 'Не указано')}</b>."
    )
    story.append(Paragraph(executive_summary, normal_style))
    story.append(Spacer(1, 12))
    
    # ========== 2. TENDER CONTEXT ==========
    story.append(Paragraph("2. TENDER CONTEXT", section_style))
    
    # Извлекаем контекст из analysis_data если доступен
    if analysis_data:
        passport = analysis_data.get("passport", {})
        context_data = [
            ["Параметр", "Значение"],
            ["Идентификатор тендера", decision_record.get('tender_id', 'Не указан')],
            ["Объект закупки", decision_record.get('tender_object', 'Не указан')],
            ["НМЦК", passport.get("nmck", "Не указано")],
            ["Регион", passport.get("region", "Не указано")],
            ["Закон", passport.get("fz", "Не указано")],
            ["Дедлайн подачи заявки", passport.get("deadlineApp", "Не указано")],
        ]
    else:
        context_data = [
            ["Параметр", "Значение"],
            ["Идентификатор тендера", decision_record.get('tender_id', 'Не указан')],
            ["Объект закупки", decision_record.get('tender_object', 'Не указан')],
        ]
    
    context_table = Table(context_data, colWidths=[70*mm, 100*mm])
    context_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
    ]))
    story.append(context_table)
    story.append(Spacer(1, 12))
    
    # ========== 3. DECISION ==========
    story.append(Paragraph("3. DECISION", section_style))
    
    decision_text = format_decision_label(decision_record.get('decision', ''))
    
    # Цвет решения
    decision_color_map = {
        "PARTICIPATE": colors.HexColor('#27ae60'),
        "DO_NOT_PARTICIPATE": colors.HexColor('#e74c3c'),
        "PARTICIPATE_WITH_CONDITIONS": colors.HexColor('#f39c12'),
        "POSTPONE": colors.HexColor('#95a5a6'),
    }
    decision_color = decision_color_map.get(decision_record.get('decision', ''), colors.HexColor('#333333'))
    
    decision_style = ParagraphStyle(
        'Decision',
        parent=emphasis_style,
        fontSize=16,
        textColor=decision_color,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph(f"<b>{decision_text}</b>", decision_style))
    story.append(Spacer(1, 12))
    
    # ========== 4. DECISION GROUNDS ==========
    story.append(Paragraph("4. DECISION GROUNDS", section_style))
    
    decision_reasons = decision_record.get('decision_reasons', [])
    if decision_reasons:
        for i, reason in enumerate(decision_reasons, 1):
            story.append(Paragraph(f"{i}. {reason}", normal_style))
    else:
        story.append(Paragraph("Основания решения не указаны", normal_style))
    
    story.append(Spacer(1, 12))
    
    # ========== 5. FINANCIAL SNAPSHOT ==========
    story.append(Paragraph("5. FINANCIAL SNAPSHOT", section_style))
    
    if analysis_data:
        passport = analysis_data.get("passport", {})
        financial_data = [
            ["Параметр", "Значение"],
            ["НМЦК", passport.get("nmck", "Не указано")],
            ["Обеспечение заявки", passport.get("bidSecurity", passport.get("guarantee", "Не указано"))],
            ["Обеспечение контракта", passport.get("contractSecurity", passport.get("guarantee", "Не указано"))],
        ]
        
        # Добавляем финансовый анализ если доступен
        financial_analysis = analysis_data.get("financialSummary") or analysis_data.get("financial_analysis")
        if financial_analysis:
            if isinstance(financial_analysis, dict):
                if financial_analysis.get("margin_risk"):
                    financial_data.append(["Риск маржинальности", financial_analysis.get("margin_risk", "Не указано")])
                if financial_analysis.get("cash_gap_risk"):
                    financial_data.append(["Риск кассового разрыва", financial_analysis.get("cash_gap_risk", "Не указано")])
        
        financial_table = Table(financial_data, colWidths=[70*mm, 100*mm])
        financial_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))
        story.append(financial_table)
    else:
        story.append(Paragraph("Финансовая информация недоступна", normal_style))
    
    story.append(Spacer(1, 12))
    
    # Индекс управленческой нагрузки
    story.append(Paragraph(f"<b>Индекс управленческой нагрузки (ИУН):</b> {decision_record.get('management_load_index', 0)}", emphasis_style))
    story.append(Spacer(1, 12))
    
    # ========== 6. NEXT STEPS ==========
    story.append(Paragraph("6. NEXT STEPS", section_style))
    
    decision = decision_record.get('decision', '')
    if decision == "PARTICIPATE":
        next_steps = [
            "Подготовка заявки на участие в тендере",
            "Сбор необходимых документов и подтверждений",
            "Подача заявки в установленные сроки"
        ]
    elif decision == "DO_NOT_PARTICIPATE":
        next_steps = [
            "Уведомление заказчика об отказе от участия (если требуется)",
            "Архивация материалов тендера",
            "Анализ причин отказа для будущих решений"
        ]
    elif decision == "PARTICIPATE_WITH_CONDITIONS":
        next_steps = [
            "Уточнение условий участия с заказчиком",
            "Подготовка запросов на разъяснение",
            "Оценка возможности выполнения условий",
            "Принятие окончательного решения после получения разъяснений"
        ]
    else:  # POSTPONE
        next_steps = [
            "Мониторинг изменений в условиях тендера",
            "Повторный анализ при появлении новой информации",
            "Принятие решения в установленные сроки"
        ]
    
    for i, step in enumerate(next_steps, 1):
        story.append(Paragraph(f"{i}. {step}", normal_style))
    
    story.append(Spacer(1, 12))
    
    # ========== 7. AUDIT NOTE ==========
    story.append(Paragraph("7. AUDIT NOTE", section_style))
    
    fixed_at = datetime.fromisoformat(decision_record.get('fixed_at', datetime.now().isoformat()))
    audit_note = (
        f"Решение зафиксировано <b>{fixed_at.strftime('%d.%m.%Y в %H:%M')}</b> "
        f"ответственным лицом: <b>{decision_record.get('responsible_person', 'Не указано')}</b>. "
        f"Идентификатор Decision Record: {decision_record.get('id', 'N/A')}. "
        f"Данный Board Pack является неизменяемым документом и частью корпоративной памяти ответственности."
    )
    story.append(Paragraph(audit_note, normal_style))
    story.append(Spacer(1, 12))
    
    # Футер
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<i>Board Pack сгенерирован системой Тендер.Щит</i><br/>"
        f"<i>Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}</i>",
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
    
    logger.info(f"✅ Board Pack сгенерирован для Decision Record {decision_record.get('id', 'N/A')}")
    
    return buffer





























