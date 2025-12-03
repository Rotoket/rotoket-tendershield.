import { describe, it, expect } from 'vitest';
import { buildPackageAuditReport } from './packageReport';
import type { PackageAnalysis } from '../types';

const makeSampleAnalysis = (): PackageAnalysis => ({
  packageId: 'pkg-12345',
  summaryScore: 82.7,
  verdict: 'CAUTION',
  globalIssues: [
    {
      title: 'Риск завышенных требований к опыту',
      severity: 'HIGH',
      description: 'В документации установлены требования к опыту, которые могут необоснованно ограничивать конкуренцию.',
    },
  ],
  documents: [
    {
      filename: 'tz.pdf',
      score: 78.2,
      summary: 'ТЗ в целом соответствует предмету закупки, но есть риск по срокам.',
      verdict: 'CAUTION',
      passport: {
        nmck: '10 000 000 ₽',
        fz: '44-ФЗ',
        region: 'г. Москва',
        deadlineApp: '10.01.2026',
        deadlineExecution: '31.12.2026',
      },
      issues: [
        {
          title: 'Сжатые сроки выполнения работ',
          description: 'Сроки могут быть нереалистичными для объёма работ.',
          severity: 'MEDIUM',
          quote: 'Срок выполнения работ составляет 10 календарных дней.',
        },
      ],
      specs: [],
      redFlags: [
        {
          title: 'Ограничение конкуренции по бренду',
          severity: 'HIGH',
          lawReference: 'ч.1 ст.33 44-ФЗ; ст.15 135-ФЗ',
          explanation: 'Указан конкретный бренд без эквивалента.',
          quote: 'Поставка оборудования марки X без указания "или эквивалент".',
        },
      ],
      financialSummary: {
        nmck: '10 000 000 ₽',
        estimatedCost: '8 500 000 ₽',
        marginComment: 'Потенциальная маржа около 15% до учёта рисков.',
      },
      timelineSummary: {
        deadlineApp: '10.01.2026',
        deadlineExecution: '31.12.2026',
        timelineRisk: 'Срок исполнения жёсткий, возможен риск штрафов при задержке поставки.',
      },
      actions: [
        { priority: 1, text: 'Уточнить у заказчика возможность корректировки сроков.' },
        { priority: 2, text: 'Оценить реалистичность поставки с учётом логистики.' },
      ],
    },
  ],
});

describe('buildPackageAuditReport', () => {
  it('формирует шапку и итоговые показатели по пакету', () => {
    const analysis = makeSampleAnalysis();
    const text = buildPackageAuditReport(analysis);

    expect(text).toContain('ОТЧЁТ КОМПЛЕКСНОГО АУДИТА ПАКЕТА ТЕНДЕРНОЙ ДОКУМЕНТАЦИИ');
    expect(text).toContain(`ID пакета: ${analysis.packageId}`);
    expect(text).toContain('Итоговый балл: 83 / 100');
    expect(text).toContain('Вердикт: CAUTION');
  });

  it('включает глобальные риски и сведения по документу', () => {
    const analysis = makeSampleAnalysis();
    const text = buildPackageAuditReport(analysis);

    // Глобальные риски
    expect(text).toContain('1. Глобальные риски по пакету');
    expect(text).toContain('[1] Риск завышенных требований к опыту (HIGH)');
    expect(text).toContain('ограничивать конкуренцию');

    // Документ и паспорт
    expect(text).toContain('=== Документ 1: tz.pdf ===');
    expect(text).toContain('Балл: 78 / 100');
    expect(text).toContain('Вердикт: CAUTION');
    expect(text).toContain('Паспорт документа:');
    expect(text).toContain('НМЦК: 10 000 000 ₽');
    expect(text).toContain('Закон: 44-ФЗ');
    expect(text).toContain('Регион / место: г. Москва');

    // Риски и красные флаги
    expect(text).toContain('Основные риски:');
    expect(text).toContain('Сжатые сроки выполнения работ');
    expect(text).toContain('Цитата: "Срок выполнения работ составляет 10 календарных дней."');
    expect(text).toContain('Красные флаги:');
    expect(text).toContain('Ограничение конкуренции по бренду');
    expect(text).toContain('Норма: ч.1 ст.33 44-ФЗ; ст.15 135-ФЗ');

    // Финансы, сроки, действия
    expect(text).toContain('Финансовая сводка:');
    expect(text).toContain('Оценочная себестоимость: 8 500 000 ₽');
    expect(text).toContain('Комментарий по марже: Потенциальная маржа около 15% до учёта рисков.');
    expect(text).toContain('Сводка по срокам:');
    expect(text).toContain('Подача заявки: 10.01.2026');
    expect(text).toContain('Исполнение контракта: 31.12.2026');
    expect(text).toContain('Оценка сроков: Срок исполнения жёсткий, возможен риск штрафов при задержке поставки.');
    expect(text).toContain('Рекомендуемые шаги (по мнению системы):');
    expect(text).toContain('Уточнить у заказчика возможность корректировки сроков.');
  });

  it('корректно обрабатывает отсутствие глобальных рисков', () => {
    const analysis = makeSampleAnalysis();
    analysis.globalIssues = [];

    const text = buildPackageAuditReport(analysis);
    expect(text).toContain('Значимых глобальных несоответствий не выявлено.');
  });
});
