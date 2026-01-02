import type { AnalysisResult, PackageAnalysis, UserDecision, AuditEvent, AuditHistoryItem } from '../types';

const formatDate = (iso?: string) => {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString('ru-RU');
  } catch {
    return iso;
  }
};

const decisionLabel = (decision: UserDecision['decision']) => {
  switch (decision) {
    case 'participate':
      return 'Участвовать';
    case 'participate_with_conditions':
      return 'Участвовать с условиями';
    case 'do_not_participate':
      return 'Не участвовать';
    case 'postpone':
      return 'Отложить решение';
    default:
      return decision;
  }
};

// Упрощённая интерпретация индекса управленческой нагрузки (та же логика, что в Decision Preview)
const interpretManagementLoad = (score: number): string => {
  if (score <= 30) {
    return '0–30: рутинное участие (делегируемо). Нагрузка на управление в штатном диапазоне.';
  }
  if (score <= 50) {
    return '31–50: участие с управленческим контролем. Требуется внимание к условиям оплаты, срокам и ключевым рискам.';
  }
  if (score <= 70) {
    return '51–70: участие только при личном внимании директора. Существенная часть решений не делегируется.';
  }
  if (score <= 85) {
    return '71–85: высокая управленческая нагрузка. Требуется отдельное управленческое решение о целесообразности участия.';
  }
  return '86–100: управленчески нецелесообразно. Нагрузка и риски несоразмерны ожидаемому эффекту.';
};

export const buildBoardPackForSingle = (
  result: AnalysisResult,
  decision: UserDecision,
  auditNote?: { analysisAt?: string; trailId?: string }
): string => {
  const lines: string[] = [];

  const law = result.passport?.fz || 'Не указан';
  const nmck = result.passport?.nmck || 'Не указана';
  const region = result.passport?.region || 'Не указан';
  const tenderId = (result as any).tender_number || '—';
  const customer = (result as any).customer || 'Заказчик не указан';
  const score = typeof result.score === 'number' ? Math.round(result.score) : 0;

  // ===== СТРАНИЦА 1. EXECUTIVE SUMMARY =====
  lines.push('=== СТРАНИЦА 1. EXECUTIVE SUMMARY ===');
  lines.push('');
  lines.push('УПРАВЛЕНЧЕСКОЕ РЕШЕНИЕ ПО ТЕНДЕРУ');
  lines.push(`Номер тендера: ${tenderId}`);
  lines.push(`Заказчик: ${customer}`);
  lines.push(`Закон: ${law}`);
  lines.push(`НМЦК: ${nmck}`);
  lines.push(`Регион: ${region}`);
  lines.push('');

  lines.push('ИТОГОВОЕ РЕШЕНИЕ');
  lines.push(`РЕШЕНИЕ: ${decisionLabel(decision.decision).toUpperCase()}.`);
  lines.push('');

  lines.push('ОСНОВАНИЯ ДЛЯ РЕШЕНИЯ');
  const dealBreakers = result.deal_breakers || [];
  const issues = result.issues || [];
  lines.push(
    `Критических стоп-факторов: ${
      dealBreakers.length > 0 ? `выявлено (${dealBreakers.length})` : 'не выявлено'
    }`,
  );
  lines.push(`Управляемые риски: ${issues.length}`);

  // Финансовая определённость (грубая оценка по наличию passport/financial_analysis)
  const hasFinancialPassport =
    !!result.passport?.nmck &&
    (!!result.passport?.guarantee || !!result.passport?.bidSecurity || !!result.passport?.contractSecurity);
  const financialCertainty =
    hasFinancialPassport && result.financial_analysis
      ? 'достаточная'
      : hasFinancialPassport
      ? 'частичная'
      : 'недостаточная';
  lines.push(`Финансовая определённость: ${financialCertainty}.`);
  lines.push(`Индекс управленческой нагрузки: ${score} / 100.`);
  lines.push('');

  lines.push('ОТВЕТСТВЕННОСТЬ');
  lines.push(`Решение принято: ${formatDate(decision.timestamp)}`);
  lines.push(`Статус: ${decisionLabel(decision.decision)}`);
  lines.push('Ответственность за последствия зафиксирована за директором или уполномоченным лицом.');
  lines.push('');

  // ===== СТРАНИЦА 2. УПРАВЛЕНЧЕСКОЕ ОБОСНОВАНИЕ =====
  lines.push('=== СТРАНИЦА 2. УПРАВЛЕНЧЕСКОЕ ОБОСНОВАНИЕ ===');
  lines.push('');

  // 5. DEAL BREAKER
  lines.push('5. DEAL BREAKER');
  lines.push(
    `Статус: ${dealBreakers.length > 0 ? 'выявлены' : 'не выявлены'}.`,
  );
  if (dealBreakers.length > 0) {
    dealBreakers.slice(0, 3).forEach((db, i) => {
      lines.push(`  ${i + 1}) ${typeof db === 'string' ? db : (db as any).title || String(db)}`);
    });
  } else {
    lines.push('  Критические формальные основания для отказа не зафиксированы.');
  }
  lines.push('');

  // 6. Управляемые риски (таблица)
  lines.push('6. Управляемые риски');
  if (issues.length > 0) {
    lines.push('Риск\tОснование\tСтатус');
    issues.slice(0, 5).forEach((iss) => {
      const title = iss.title || 'Риск';
      const basis = iss.description || 'Основание по тексту документа';
      const status = (iss.severity || '').toUpperCase() === 'HIGH' ? 'Требует подтверждения' : 'Управляемый';
      lines.push(`${title}\t${basis}\t${status}`);
    });
  } else {
    lines.push('Управляемые риски не выделены.');
  }
  lines.push('');

  // 7. Индекс управленческой нагрузки (расшифровка)
  lines.push('7. Индекс управленческой нагрузки (ИУН)');
  lines.push(`ИУН: ${score} / 100.`);
  lines.push(`Интерпретация: ${interpretManagementLoad(score)}`);
  lines.push('');

  // ===== СТРАНИЦА 3. AUDIT & TRACE (опционально) =====
  lines.push('=== СТРАНИЦА 3. AUDIT & TRACE ===');
  lines.push('');

  lines.push('8. Audit Trail (сводка)');
  if (auditNote?.analysisAt) {
    lines.push(`Анализ выполнен: ${formatDate(auditNote.analysisAt)}`);
  }
  lines.push(`Решение зафиксировано: ${formatDate(decision.timestamp)}`);
  if (auditNote?.trailId) {
    lines.push(`ID Audit Trail: ${auditNote.trailId}`);
  }
  lines.push('');

  lines.push('9. Юридический дисклеймер');
  lines.push(
    'Документ является фиксацией управленческого решения. Аналитические материалы носят вспомогательный характер. Система не принимает решений автоматически.',
  );

  return lines.join('\n');
};

export const buildBoardPackForHistoryItem = (
  item: AuditHistoryItem
): string => {
  const lines: string[] = [];

  // 1. Executive Summary
  lines.push('1. Executive Summary');
  lines.push('');
  const files = item.files || [];
  const mainFile = files[0] || 'Тендер';
  lines.push(`Рассмотрен тендер: ${mainFile}.`);
  if (item.user_decision) {
    lines.push(`Решение: ${decisionLabel(item.user_decision.decision).toUpperCase()}.`);
  } else {
    lines.push('Решение: не зафиксировано.');
  }
  if (item.executive_summary) {
    const firstLines = item.executive_summary.split('\n').filter(Boolean).slice(0, 2);
    if (firstLines.length) {
      lines.push('Контекст:');
      lines.push(...firstLines);
    }
  }
  lines.push('');

  // 2. Ключевые параметры
  lines.push('2. Ключевые параметры');
  lines.push('');
  lines.push(`Итоговый балл: ${Math.round(item.summaryScore)} / 100`);
  lines.push(`Вердикт системы: ${item.verdict}`);
  lines.push('');

  // 3. Принятое решение
  lines.push('3. Принятое решение');
  lines.push('');
  if (item.user_decision) {
    lines.push(`Статус: ${decisionLabel(item.user_decision.decision)}`);
    lines.push(`Дата решения: ${formatDate(item.user_decision.timestamp)}`);
    if (item.user_decision.comment) {
      lines.push(`Комментарий: ${item.user_decision.comment}`);
    }
  } else {
    lines.push('Решение не зафиксировано.');
  }
  lines.push('');

  // 4. Основания решения
  lines.push('4. Основания решения');
  lines.push('');
  const dealBreakers = item.deal_breakers || [];
  if (dealBreakers.length) {
    lines.push('Критические стоп-факторы:');
    dealBreakers.slice(0, 5).forEach((db, i) => {
      lines.push(`  ${i + 1}) ${db}`);
    });
  }
  lines.push('');

  // 5. Финансовая оценка
  lines.push('5. Финансовая оценка');
  lines.push('');
  if (item.financial_analysis) {
    const fa = item.financial_analysis as any;
    if (fa.reasoning) lines.push(`Комментарий по марже: ${fa.reasoning}`);
  }
  lines.push(`Индекс управленческой нагрузки: ${Math.round(item.summaryScore)} / 100.`);
  lines.push(`Интерпретация индекса: ${interpretManagementLoad(Math.round(item.summaryScore))}`);
  lines.push('');

  // 6. Управленческие шаги и следующие действия
  lines.push('6. Альтернативы и следующие шаги');
  lines.push('');
  lines.push('Управленческие шаги:');
  lines.push('- при необходимости — подготовить протокол разногласий или отказ от участия;');
  lines.push('- использовать выводы анализа при рассмотрении аналогичных тендеров.');
  lines.push('');

  // 7. Audit Note
  lines.push('7. Audit Note');
  lines.push('');
  lines.push(`Дата анализа: ${formatDate(item.createdAt)}`);
  if (item.user_decision) {
    lines.push(`Дата решения: ${formatDate(item.user_decision.timestamp)}`);
  }

  return lines.join('\n');
};















