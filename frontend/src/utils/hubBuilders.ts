import type {
  AnalysisResult,
  PackageAnalysis,
  TenderHubSummary,
  PackageHubSummary,
  RequirementItem,
  LegalViolationItem,
  ActionItemVm,
} from '../types';
import { buildITHub, buildMedicineHub, buildConstructionHub, extractIndustryData } from './industryHubBuilders';
import { logEvent } from './logger';

/**
 * Heuristic-сборка хаба для одиночного анализа
 * из уже существующих полей AnalysisResult.
 * Поддерживает отраслевые builder'ы для IT, MEDICINE, CONSTRUCTION.
 */
export const buildSingleHubFromAnalysis = (
  result: AnalysisResult,
  industry: 'IT' | 'CONSTRUCTION' | 'MEDICINE' | 'UNIVERSAL' = 'UNIVERSAL'
): TenderHubSummary => {
  logEvent('HubBuilders', `Построение хаба для отрасли: ${industry}`, 'info');

  // Базовые данные (общие для всех отраслей)
  const baseInfo: TenderHubSummary['baseInfo'] = {
    nmck: result.passport.nmck,
    procedure: undefined, // Можно дополнить позже после доработки backend/LLM
    customer: undefined,
    fz: result.passport.fz,
    region: result.passport.region,
    deadlineApp: result.passport.deadlineApp,
    deadlineExecution: result.passport.deadlineExecution,
  };

  const payments: TenderHubSummary['payments'] = {
    advance: (result.passport as any).advance || 'Не указано',
    mainPayment: (result.passport as any).paymentTerms,
    scheduleComment:
      ((result as any).financialSummary?.marginComment as string | undefined) ||
      'Условия оплаты требуют дополнительной проверки по проекту договора.',
  };

  const legalViolations: LegalViolationItem[] = (result.redFlags || [])
    .filter((rf) => !!rf.lawReference)
    .map((rf) => ({
      lawReference: rf.lawReference || '',
      description: rf.explanation || rf.title,
      type: 'other',
      severity: 'high',
    }));

  const financial: TenderHubSummary['financial'] = {
    marginPercentApprox: undefined,
    marginComment:
      ((result as any).financialSummary?.marginComment as string | undefined) ||
      'Маржа оценивается в отдельном калькуляторе, проверьте себестоимость и скрытые расходы.',
    lossRiskLevel: 'medium',
  };

  const recommendation: TenderHubSummary['recommendation'] = {
    verdict: result.verdict,
    summaryShort: result.summary,
    actions: ((result as any).actions as ActionItemVm[] | undefined) || [],
  };

  // Универсальные значения по умолчанию
  let redFlagsTop = (result.redFlags || []).slice(0, 3).map((rf) => ({
    title: rf.title,
    severity: rf.severity,
    lawReference: rf.lawReference,
    explanation: rf.explanation,
  }));

  let specsSummary: TenderHubSummary['specsSummary'] = {
    totalPositions: result.specs?.length || 0,
    highRiskCount: 0,
    examples: result.specs?.slice(0, 3).map((s) => ({
      name: s.name,
      riskLevel: 'medium' as const,
      riskReason: 'Проверьте параметры и совместимость с вашим предложением.',
    })) || [],
  };

  let timeline: TenderHubSummary['timeline'] = {
    riskLevel: 'ok' as const,
    comment:
      (result as any).timelineSummary?.timelineRisk ||
      'Сроки кажутся приемлемыми, но требуют дополнительной проверки по графику работ.',
  };

  let guarantees: TenderHubSummary['guarantees'] = {
    text: (result.passport as any).secureWarranty || 'Условия гарантий не описаны явно.',
    riskLevel: 'medium' as const,
  };

  let requirements: RequirementItem[] = [];

  // Применяем отраслевые builder'ы
  const industryData = extractIndustryData(result, industry);

  let industryHub: Partial<TenderHubSummary> = {};

  try {
    switch (industry) {
      case 'IT':
        industryHub = buildITHub(result, industryData as any);
        break;
      case 'MEDICINE':
        industryHub = buildMedicineHub(result, industryData as any);
        break;
      case 'CONSTRUCTION':
        industryHub = buildConstructionHub(result, industryData as any);
        break;
      default:
        // UNIVERSAL - используем базовые значения
        break;
    }

    // Объединяем отраслевые данные с базовыми
    if (industryHub.redFlagsTop && industryHub.redFlagsTop.length > 0) {
      redFlagsTop = industryHub.redFlagsTop.map(flag => ({
        title: flag.title,
        severity: flag.severity,
        lawReference: flag.lawReference,
        explanation: flag.explanation,
      }));
    }

    if (industryHub.specsSummary) {
      specsSummary = industryHub.specsSummary;
    }

    if (industryHub.timeline) {
      timeline = industryHub.timeline;
    }

    if (industryHub.guarantees) {
      guarantees = industryHub.guarantees;
    }

    if (industryHub.requirements && industryHub.requirements.length > 0) {
      requirements = industryHub.requirements;
    }

    if (industryHub.financial) {
      Object.assign(financial, industryHub.financial);
    }
  } catch (error) {
    logEvent('HubBuilders', `Ошибка при построении отраслевого хаба: ${error}`, 'error');
  }

  return {
    redFlagsTop,
    baseInfo,
    specsSummary,
    timeline,
    payments,
    guarantees,
    requirements,
    legalViolations,
    financial,
    recommendation,
  };
};

/**
 * Хаб на уровне пакета — агрегирован на основе PackageAnalysis.
 */
export const buildPackageHubFromAnalysis = (pkg: PackageAnalysis): PackageHubSummary => {
  const docs = pkg.documents || [];

  const allRedFlags = docs.flatMap((d) => d.redFlags || []);
  const redFlagsTop = allRedFlags.slice(0, 3).map((rf) => ({
    title: rf.title,
    severity: rf.severity,
    lawReference: rf.lawReference,
    explanation: rf.explanation,
  }));

  const nmcks = docs
    .map((d) => String((d.passport || {}).nmck || ''))
    .filter(Boolean);

  const baseInfo: PackageHubSummary['baseInfo'] = {
    nmckTotal: nmcks[0] || 'Не определено',
    procedures: [],
    customers: [],
    fz: String((docs[0]?.passport || {}).fz || '44-ФЗ'),
    region: String((docs[0]?.passport || {}).region || 'РФ'),
  };

  const totalPositions = docs.reduce((acc, d) => acc + (d.specs?.length || 0), 0);

  const specsSummary: PackageHubSummary['specsSummary'] = {
    totalDocuments: docs.length,
    totalPositions,
    highRiskDocs: 0,
    highRiskPositions: 0,
  };

  const timeline: PackageHubSummary['timeline'] = {
    riskLevel: 'ok',
    comment:
      'Сроки по документам в пакете требуют сверки между собой (ТЗ, договор, протоколы).',
  };

  const payments: PackageHubSummary['payments'] = {
    advance: 'См. проект договора',
    scheduleComment: 'График оплат формируется по проекту договора и связанным документам.',
  };

  const guarantees: PackageHubSummary['guarantees'] = {
    text: 'Условия гарантий необходимо сверить между ТЗ и договором.',
    riskLevel: 'medium',
  };

  const requirements: RequirementItem[] = [];

  const legalViolations: LegalViolationItem[] = (pkg.globalIssues || []).map((gi) => ({
    lawReference: 'Проверьте соответствие 44-ФЗ/223-ФЗ и практике ФАС',
    description: gi.title,
    type: 'other',
    severity: 'high',
  }));

  const financial: PackageHubSummary['financial'] = {
    marginPercentApprox: undefined,
    marginComment:
      'Финансовый результат по пакету оценивается через калькулятор и сводку по каждому документу.',
    lossRiskLevel: 'medium',
  };

  const recommendation: PackageHubSummary['recommendation'] = {
    verdict: pkg.verdict,
    summaryShort:
      'Итоговая оценка пакета сформирована на основе худшего документа и глобальных рисков.',
    actions: [],
  };

  return {
    redFlagsTop,
    baseInfo,
    specsSummary,
    timeline,
    payments,
    guarantees,
    requirements,
    legalViolations,
    financial,
    recommendation,
  };
};
