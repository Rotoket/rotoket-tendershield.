import { describe, it, expect } from 'vitest';
import { buildSingleHubFromAnalysis, buildPackageHubFromAnalysis } from './hubBuilders';
import type { AnalysisResult, PackageAnalysis } from '../types';

describe('hubBuilders', () => {
  describe('buildSingleHubFromAnalysis', () => {
    it('должен создать хаб из базового AnalysisResult', () => {
      const result: AnalysisResult = {
        score: 75,
        summary: 'Тестовое резюме анализа',
        verdict: 'CAUTION',
        passport: {
          nmck: '10 000 000 ₽',
          fz: '44-ФЗ',
          advance: '30%',
          paymentTerms: '7 раб. дней',
          secureBid: '50 000 ₽',
          secureContract: '1 000 000 ₽',
          secureWarranty: '5%',
          deadlineApp: '2024-12-31',
          deadlineExecution: '2025-03-31',
          region: 'Москва',
        },
        deepAudit: [],
        issues: [],
        specs: [
          { name: 'Товар 1', qty: '10 шт', details: 'Характеристики' },
          { name: 'Товар 2', qty: '5 шт', details: 'Характеристики' },
        ],
        redFlags: [
          {
            title: 'Тестовый красный флаг',
            severity: 'HIGH',
            lawReference: 'ст. 33 44-ФЗ',
            explanation: 'Тестовое объяснение',
          },
        ],
        keywordMatches: [],
      };

      const hub = buildSingleHubFromAnalysis(result, 'UNIVERSAL');

      expect(hub).toBeDefined();
      expect(hub.redFlagsTop).toHaveLength(1);
      expect(hub.redFlagsTop[0].title).toBe('Тестовый красный флаг');
      expect(hub.baseInfo.nmck).toBe('10 000 000 ₽');
      expect(hub.baseInfo.fz).toBe('44-ФЗ');
      expect(hub.baseInfo.region).toBe('Москва');
      expect(hub.specsSummary.totalPositions).toBe(2);
      expect(hub.recommendation.verdict).toBe('CAUTION');
      expect(hub.recommendation.summaryShort).toBe('Тестовое резюме анализа');
    });

    it('должен создать хаб с отраслевыми данными для IT', () => {
      const result: AnalysisResult = {
        score: 75,
        summary: 'Тестовое резюме анализа',
        verdict: 'CAUTION',
        passport: {
          nmck: '10 000 000 ₽',
          fz: '44-ФЗ',
          advance: '30%',
          paymentTerms: '7 раб. дней',
          secureBid: '50 000 ₽',
          secureContract: '1 000 000 ₽',
          secureWarranty: '5%',
          deadlineApp: '2024-12-31',
          deadlineExecution: '2025-03-31',
          region: 'Москва',
        },
        deepAudit: [],
        issues: [
          {
            title: 'Ограничение конкуренции по бренду (ст. 33 44-ФЗ)',
            severity: 'HIGH',
            description: 'Требуется только Python без "или эквивалент"',
            quote: 'Язык программирования - только Python',
          },
        ],
        specs: [
          { name: 'Веб-приложение', qty: '1 шт', details: 'Требуется Django фреймворк' },
        ],
        redFlags: [],
        keywordMatches: [],
      };

      const hub = buildSingleHubFromAnalysis(result, 'IT');

      expect(hub).toBeDefined();
      expect(hub.requirements).toBeDefined();
      expect(hub.requirements.length).toBeGreaterThan(0);
      expect(hub.requirements.some((r) => r.code === 'EXPERIENCE')).toBe(true);
    });

    it('должен обработать случай без redFlags', () => {
      const result: AnalysisResult = {
        score: 85,
        summary: 'Без красных флагов',
        verdict: 'PARTICIPATE',
        passport: {
          nmck: '5 000 000 ₽',
          fz: '223-ФЗ',
          advance: 'Нет',
          paymentTerms: '14 дней',
          secureBid: '100 000 ₽',
          secureContract: '500 000 ₽',
          secureWarranty: 'Нет',
          deadlineApp: '2024-12-15',
          deadlineExecution: '2025-02-15',
          region: 'СПб',
        },
        deepAudit: [],
        issues: [],
        specs: [],
        keywordMatches: [],
      };

      const hub = buildSingleHubFromAnalysis(result, 'UNIVERSAL');

      expect(hub.redFlagsTop).toHaveLength(0);
      expect(hub.specsSummary.totalPositions).toBe(0);
    });

    it('должен ограничить redFlagsTop до 3 элементов', () => {
      const result: AnalysisResult = {
        score: 60,
        summary: 'Много флагов',
        verdict: 'STOP',
        passport: {
          nmck: '1 000 000 ₽',
          fz: '44-ФЗ',
          advance: '20%',
          paymentTerms: '10 дней',
          secureBid: '10 000 ₽',
          secureContract: '100 000 ₽',
          secureWarranty: '3%',
          deadlineApp: '2024-12-20',
          deadlineExecution: '2025-04-20',
          region: 'Казань',
        },
        deepAudit: [],
        issues: [],
        specs: [],
        redFlags: [
          { title: 'Флаг 1', severity: 'HIGH' },
          { title: 'Флаг 2', severity: 'HIGH' },
          { title: 'Флаг 3', severity: 'MEDIUM' },
          { title: 'Флаг 4', severity: 'LOW' },
        ],
        keywordMatches: [],
      };

      const hub = buildSingleHubFromAnalysis(result, 'UNIVERSAL');

      expect(hub.redFlagsTop).toHaveLength(3);
      expect(hub.redFlagsTop[0].title).toBe('Флаг 1');
      expect(hub.redFlagsTop[2].title).toBe('Флаг 3');
    });
  });

  describe('buildPackageHubFromAnalysis', () => {
    it('должен создать хаб для пакета документов', () => {
      const pkg: PackageAnalysis = {
        packageId: 'test-pkg-1',
        summaryScore: 70,
        verdict: 'CAUTION',
        documents: [
          {
            filename: 'doc1.pdf',
            score: 80,
            summary: 'Документ 1',
            verdict: 'PARTICIPATE',
            passport: { nmck: '5 000 000 ₽', fz: '44-ФЗ', region: 'Москва' },
            issues: [],
            specs: [{ name: 'Товар 1', qty: '10 шт', details: 'Описание' }],
          },
          {
            filename: 'doc2.pdf',
            score: 60,
            summary: 'Документ 2',
            verdict: 'CAUTION',
            passport: { nmck: '5 000 000 ₽', fz: '44-ФЗ', region: 'Москва' },
            issues: [],
            specs: [{ name: 'Товар 2', qty: '5 шт', details: 'Описание' }],
            redFlags: [{ title: 'Риск в документе 2', severity: 'HIGH' }],
          },
        ],
        globalIssues: [
          {
            title: 'Глобальная проблема',
            severity: 'HIGH',
            description: 'Описание проблемы',
          },
        ],
      };

      const hub = buildPackageHubFromAnalysis(pkg);

      expect(hub).toBeDefined();
      expect(hub.baseInfo.nmckTotal).toBe('5 000 000 ₽');
      expect(hub.baseInfo.fz).toBe('44-ФЗ');
      expect(hub.specsSummary.totalDocuments).toBe(2);
      expect(hub.specsSummary.totalPositions).toBe(2);
      expect(hub.redFlagsTop.length).toBeGreaterThanOrEqual(0);
      expect(hub.recommendation.verdict).toBe('CAUTION');
    });

    it('должен обработать пустой пакет', () => {
      const pkg: PackageAnalysis = {
        packageId: 'empty-pkg',
        summaryScore: 0,
        verdict: 'STOP',
        documents: [],
        globalIssues: [],
      };

      const hub = buildPackageHubFromAnalysis(pkg);

      expect(hub.specsSummary.totalDocuments).toBe(0);
      expect(hub.specsSummary.totalPositions).toBe(0);
      expect(hub.baseInfo.nmckTotal).toBe('Не определено');
    });
  });
});

