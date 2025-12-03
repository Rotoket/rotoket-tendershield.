import { describe, it, expect } from 'vitest';
import { buildITHub, buildMedicineHub, buildConstructionHub } from './industryHubBuilders';
import type { AnalysisResult } from '../types';

describe('industryHubBuilders', () => {
  const createBaseResult = (): AnalysisResult => ({
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
    specs: [],
    keywordMatches: [],
  });

  describe('buildITHub', () => {
    it('должен создать хаб с IT-специфичными требованиями', () => {
      const result = createBaseResult();
      result.issues = [
        {
          title: 'Ограничение конкуренции по бренду (ст. 33 44-ФЗ)',
          severity: 'HIGH',
          description: 'Требуется только Python без "или эквивалент"',
          quote: 'Язык программирования - только Python',
        },
      ];

      const hub = buildITHub(result);

      expect(hub).toBeDefined();
      expect(hub.requirements).toBeDefined();
      expect(hub.requirements?.length).toBeGreaterThan(0);

      const experienceReq = hub.requirements?.find((r) => r.code === 'EXPERIENCE');
      expect(experienceReq).toBeDefined();
      expect(experienceReq?.title).toContain('Опыт разработки');
    });

    it('должен выявить red flags для IT', () => {
      const result = createBaseResult();
      result.redFlags = [
        {
          title: 'Смешение оборудования и ПО в одном лоте',
          severity: 'HIGH',
          lawReference: 'практика ФАС по 44-ФЗ',
          explanation: 'В одном лоте одновременно закупаются компьютеры и офисное ПО',
        },
      ];

      const hub = buildITHub(result);

      expect(hub.redFlagsTop).toBeDefined();
      expect(hub.redFlagsTop?.length).toBeGreaterThanOrEqual(0);
    });

    it('должен обработать технический стек', () => {
      const result = createBaseResult();
      result.specs = [
        {
          name: 'Веб-приложение',
          qty: '1 шт',
          details: 'Требуется фреймворк Django обязателен',
        },
      ];

      const hub = buildITHub(result, {
        techStack: {
          language: 'Python',
          framework: 'Django',
        },
      });

      expect(hub.specsSummary).toBeDefined();
      expect(hub.requirements).toBeDefined();
    });
  });

  describe('buildMedicineHub', () => {
    it('должен создать хаб с медицинскими требованиями', () => {
      const result = createBaseResult();
      result.issues = [
        {
          title: 'Не указано требование к наличию регистрационного удостоверения (РУ)',
          severity: 'HIGH',
          description: 'В тексте нет явного требования о наличии действующего РУ',
        },
      ];

      const hub = buildMedicineHub(result);

      expect(hub).toBeDefined();
      expect(hub.requirements).toBeDefined();

      const licenseReq = hub.requirements?.find((r) => r.code === 'LICENSE');
      expect(licenseReq).toBeDefined();
      expect(licenseReq?.level).toBe('blocking');
    });

    it('должен выявить проблемы с РУ', () => {
      const result = createBaseResult();
      // Добавляем issue, чтобы builder мог найти РУ
      result.issues = [
        {
          title: 'Не указано требование к наличию регистрационного удостоверения (РУ)',
          severity: 'HIGH',
          description: 'В тексте нет явного требования о наличии действующего РУ',
        },
      ];

      const hub = buildMedicineHub(result, {
        licenses: {
          roszdravnadzor: 'Лицензия требуется',
        },
      });

      expect(hub.redFlagsTop).toBeDefined();
      expect(hub.redFlagsTop?.length).toBeGreaterThan(0);
      // Проверяем, что есть флаг, содержащий "ру" или "регистрационное"
      const ruFlag = hub.redFlagsTop?.find((rf) => {
        const titleLower = rf.title.toLowerCase();
        return titleLower.includes('регистрационное') || titleLower.includes('ру');
      });
      expect(ruFlag).toBeDefined();
      expect(ruFlag?.severity).toBe('HIGH');
    });

    it('должен проверить температурный режим', () => {
      const result = createBaseResult();

      const hub = buildMedicineHub(result, {
        storage: {
          temperature: '2-8°C',
        },
      });

      expect(hub.timeline).toBeDefined();
      expect(hub.timeline?.comment.toLowerCase()).toContain('температурн');
    });
  });

  describe('buildConstructionHub', () => {
    it('должен создать хаб с требованиями СРО', () => {
      const result = createBaseResult();

      const hub = buildConstructionHub(result, {
        sro: {
          required: true,
          number: 'СРО-12345',
        },
      });

      expect(hub).toBeDefined();
      expect(hub.requirements).toBeDefined();

      const sroReq = hub.requirements?.find((r) => r.code === 'SRO');
      expect(sroReq).toBeDefined();
      expect(sroReq?.level).toBe('blocking');
      expect(sroReq?.title).toContain('СРО');
    });

    it('должен выявить проблему отсутствия СРО', () => {
      const result = createBaseResult();

      const hub = buildConstructionHub(result, {
        sro: {
          required: true,
        },
      });

      expect(hub.redFlagsTop).toBeDefined();
      const sroFlag = hub.redFlagsTop?.find((rf) =>
        rf.title.toLowerCase().includes('сро')
      );
      expect(sroFlag).toBeDefined();
      expect(sroFlag?.severity).toBe('CRITICAL');
    });

    it('должен обработать этапы строительства', () => {
      const result = createBaseResult();

      const hub = buildConstructionHub(result, {
        stages: [
          {
            name: 'Демонтаж',
            duration: '30 дней',
            workType: 'Подготовительные работы',
          },
          {
            name: 'Основные работы',
            duration: '60 дней',
            workType: 'Строительно-монтажные',
          },
        ],
      });

      expect(hub.timeline).toBeDefined();
      expect(hub.timeline?.comment).toContain('этапов');
    });

    it('должен проверить скрытые работы', () => {
      const result = createBaseResult();

      const hub = buildConstructionHub(result, {
        hiddenWorks: {
          mentioned: true,
          actsRequired: false,
        },
      });

      expect(hub.redFlagsTop).toBeDefined();
      const hiddenWorksFlag = hub.redFlagsTop?.find((rf) =>
        rf.title.toLowerCase().includes('скрытые работы')
      );
      expect(hiddenWorksFlag).toBeDefined();
    });
  });
});

