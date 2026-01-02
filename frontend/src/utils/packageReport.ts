import { PackageAnalysis } from '../types';
import { verdictLabel, severityLabel } from './hubUiHelpers';

/**
 * Строит текстовый отчёт по результатам комплексного аудита пакета документов.
 * Используется в UI и покрывается тестами (Rule 5).
 */
const formatDecisionLabel = (decision: string): string => {
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

const formatDateTime = (iso: string): string => {
  try {
    const d = new Date(iso);
    return d.toLocaleString('ru-RU');
  } catch {
    return iso;
  }
};

export const buildPackageAuditReport = (result: PackageAnalysis): string => {
  const lines: string[] = [];

  lines.push('ОТЧЁТ КОМПЛЕКСНОГО АУДИТА ПАКЕТА ТЕНДЕРНОЙ ДОКУМЕНТАЦИИ');
  lines.push('');
  
  // Секция решения (если есть) - ВСЕГДА ПЕРВАЯ
  if (result.userDecision) {
    lines.push('## Решение по тендеру');
    lines.push(`Статус: ${formatDecisionLabel(result.userDecision.decision)}`);
    lines.push(`Дата решения: ${formatDateTime(result.userDecision.timestamp)}`);
    if (result.userDecision.comment) {
      lines.push(`Комментарий: ${result.userDecision.comment}`);
    }
    lines.push('');
  }
  
  lines.push(`ID пакета: ${result.packageId}`);
  lines.push(`Итоговый балл: ${Math.round(result.summaryScore)} / 100`);
  lines.push(`Вердикт: ${verdictLabel(result.verdict)}`);
  lines.push('');

  // Глобальные риски
  lines.push('1. Глобальные риски по пакету');
  if (!result.globalIssues.length) {
    lines.push('  Значимых глобальных несоответствий не выявлено.');
  } else {
    result.globalIssues.forEach((gi, idx) => {
      lines.push(`  [${idx + 1}] ${gi.title} (${severityLabel(gi.severity)})`);
      lines.push(`      ${gi.description}`);
    });
  }
  lines.push('');

  // Документы пакета
  lines.push('2. Документы пакета и основные выводы');
  result.documents.forEach((doc, idx) => {
    lines.push('');
    lines.push(`  === Документ ${idx + 1}: ${doc.filename} ===`);
    lines.push(`  Балл: ${Math.round(doc.score)} / 100`);
    lines.push(`  Вердикт: ${verdictLabel(doc.verdict)}`);
    if (doc.summary) {
      lines.push(`  Краткое резюме: ${doc.summary}`);
    }
    if (doc.passport) {
      lines.push('  Паспорт документа:');
      if (doc.passport.nmck) lines.push(`    НМЦК: ${doc.passport.nmck}`);
      if (doc.passport.fz) lines.push(`    Закон: ${doc.passport.fz}`);
      if (doc.passport.region) lines.push(`    Регион / место: ${doc.passport.region}`);
      if (doc.passport.deadlineApp) lines.push(`    Подача заявки: ${doc.passport.deadlineApp}`);
      if (doc.passport.deadlineExecution) lines.push(`    Исполнение: ${doc.passport.deadlineExecution}`);
    }

    const topIssues = (doc.issues || []).slice(0, 3);
    if (topIssues.length) {
      lines.push('  Основные риски:');
      topIssues.forEach((iss, j) => {
        lines.push(
          `    (${j + 1}) ${iss.title}${
            iss.severity ? ` [${severityLabel(iss.severity)}]` : ''
          }`,
        );
        if (iss.description) lines.push(`        ${iss.description}`);
        if (iss.quote) lines.push(`        Цитата: "${iss.quote}"`);
      });
    }

    const topFlags = (doc.redFlags || []).slice(0, 3);
    if (topFlags.length) {
      lines.push('  Красные флаги:');
      topFlags.forEach((rf, j) => {
        lines.push(
          `    (${j + 1}) ${rf.title}${
            rf.severity ? ` [${severityLabel(rf.severity)}]` : ''
          }`,
        );
        if (rf.lawReference) lines.push(`        Норма: ${rf.lawReference}`);
        if (rf.explanation) lines.push(`        ${rf.explanation}`);
        if (rf.quote) lines.push(`        Цитата: "${rf.quote}"`);
      });
    }

    if (doc.financialSummary) {
      lines.push('  Финансовая сводка:');
      if (doc.financialSummary.nmck) lines.push(`    НМЦК: ${doc.financialSummary.nmck}`);
      if (doc.financialSummary.estimatedCost)
        lines.push(`    Оценочная себестоимость: ${doc.financialSummary.estimatedCost}`);
      if (doc.financialSummary.marginComment)
        lines.push(`    Комментарий по марже: ${doc.financialSummary.marginComment}`);
    }

    if (doc.timelineSummary) {
      lines.push('  Сводка по срокам:');
      if (doc.timelineSummary.deadlineApp)
        lines.push(`    Подача заявки: ${doc.timelineSummary.deadlineApp}`);
      if (doc.timelineSummary.deadlineExecution)
        lines.push(`    Исполнение контракта: ${doc.timelineSummary.deadlineExecution}`);
      if (doc.timelineSummary.timelineRisk)
        lines.push(`    Оценка сроков: ${doc.timelineSummary.timelineRisk}`);
    }

    const acts = (doc.actions || []) as any[];
    if (acts.length) {
      lines.push('  Управленческие шаги (по мнению системы):');
      acts
        .slice()
        .sort((a, b) => (a.priority || 0) - (b.priority || 0))
        .forEach((a, j) => {
          if (a.text) lines.push(`    (${j + 1}) ${a.text}`);
        });
    }
  });

  lines.push('');
  lines.push('3. Важное замечание');
  lines.push(
    'Система фиксирует предварительную аналитическую оценку на основе документов. Решение об участии в закупке, подаче жалоб и иных действиях принимает специалист, ответственность несёт пользователь.',
  );

  return lines.join('\n');
};
