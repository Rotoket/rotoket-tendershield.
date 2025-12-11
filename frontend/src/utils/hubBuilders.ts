import type {
  AnalysisResult,
  PackageAnalysis,
  TenderHubSummary,
  PackageHubSummary,
  RequirementItem,
  LegalViolationItem,
  ActionItemVm,
  PackageDocumentAnalysis,
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
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:20', message: 'buildSingleHubFromAnalysis entry', data: { industry, hasResult: !!result, hasPassport: !!result?.passport, hasRedFlags: !!result?.redFlags, hasSpecs: !!result?.specs, specsLength: result?.specs?.length || 0 }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'A' }) }).catch(() => { });
  // #endregion
  logEvent('HubBuilders', `Построение хаба для отрасли: ${industry}`, 'info');

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:27', message: 'Before baseInfo construction', data: { passportNmck: result?.passport?.nmck, passportFz: result?.passport?.fz, passportRegion: result?.passport?.region }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'B' }) }).catch(() => { });
  // #endregion

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
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:101', message: 'Before extractIndustryData', data: { industry }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'C' }) }).catch(() => { });
  // #endregion
  const industryData = extractIndustryData(result, industry);
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:102', message: 'After extractIndustryData', data: { hasIndustryData: !!industryData, industryDataType: industryData ? Object.keys(industryData).join(',') : 'undefined' }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'C' }) }).catch(() => { });
  // #endregion

  let industryHub: Partial<TenderHubSummary> = {};

  try {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:105', message: 'Before industry builder switch', data: { industry }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
    // #endregion
    switch (industry) {
      case 'IT':
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:108', message: 'Calling buildITHub', data: { hasIndustryData: !!industryData }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        industryHub = buildITHub(result, industryData as any);
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:109', message: 'After buildITHub', data: { hasRedFlags: !!industryHub.redFlagsTop, redFlagsLength: industryHub.redFlagsTop?.length || 0, hasRequirements: !!industryHub.requirements, requirementsLength: industryHub.requirements?.length || 0 }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        break;
      case 'MEDICINE':
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:111', message: 'Calling buildMedicineHub', data: { hasIndustryData: !!industryData }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        industryHub = buildMedicineHub(result, industryData as any);
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:112', message: 'After buildMedicineHub', data: { hasRedFlags: !!industryHub.redFlagsTop, redFlagsLength: industryHub.redFlagsTop?.length || 0, hasRequirements: !!industryHub.requirements, requirementsLength: industryHub.requirements?.length || 0 }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        break;
      case 'CONSTRUCTION':
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:114', message: 'Calling buildConstructionHub', data: { hasIndustryData: !!industryData }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
        industryHub = buildConstructionHub(result, industryData as any);
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:115', message: 'After buildConstructionHub', data: { hasRedFlags: !!industryHub.redFlagsTop, redFlagsLength: industryHub.redFlagsTop?.length || 0, hasRequirements: !!industryHub.requirements, requirementsLength: industryHub.requirements?.length || 0 }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'D' }) }).catch(() => { });
        // #endregion
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
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:150', message: 'Error in industry builder', data: { error: String(error), errorName: error instanceof Error ? error.name : 'unknown', errorMessage: error instanceof Error ? error.message : 'unknown' }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'E' }) }).catch(() => { });
    // #endregion
    logEvent('HubBuilders', `Ошибка при построении отраслевого хаба: ${error}`, 'error');
  }

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:154', message: 'Before return hub', data: { redFlagsLength: redFlagsTop.length, specsTotalPositions: specsSummary.totalPositions, hasTimeline: !!timeline, hasGuarantees: !!guarantees, requirementsLength: requirements.length, hasFinancial: !!financial, hasRecommendation: !!recommendation }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'F' }) }).catch(() => { });
  // #endregion

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
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:171', message: 'buildPackageHubFromAnalysis entry', data: { hasPkg: !!pkg, hasDocuments: !!pkg?.documents, documentsLength: pkg?.documents?.length || 0 }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'G' }) }).catch(() => { });
  // #endregion
  const docs = pkg.documents || [];

  const allRedFlags = docs.flatMap((d) => d.redFlags || []);
  const redFlagsTop = allRedFlags.slice(0, 3).map((rf) => ({
    title: rf.title,
    severity: rf.severity,
    lawReference: rf.lawReference,
    explanation: rf.explanation,
  }));

  // Определяем каноническую НМЦК по пакету: сначала сметы/ОНМЦК, затем остальные паспорта
  const pickCanonicalNmckForPackage = (documents: PackageDocumentAnalysis[]): string => {
    if (!documents || documents.length === 0) {
      return 'Не определено';
    }

    type PriceCandidate = {
      doc: PackageDocumentAnalysis;
      totalAmountNumeric?: number;
      nmckText?: string;
    };

    const candidates: PriceCandidate[] = documents
      .map((d) => {
        const name = (d.filename || '').toLowerCase();
        const docType = (d as any).docType || '';
        const smeta = ((d as any).smetaSummary || {}) as any;

        const isSmetaDoc =
          docType === 'SMETA_LOCAL' ||
          name.includes('смет') ||
          name.includes('локальн');

        const isOnmckDoc =
          docType === 'ONMCK_JUSTIFICATION' ||
          name.includes('онмцк') ||
          (name.includes('обоснован') && name.includes('цены')) ||
          name.includes('нмцк');

        if (!isSmetaDoc && !isOnmckDoc) {
          return null;
        }

        const totalAmountNumeric =
          typeof smeta.totalAmountNumeric === 'number'
            ? smeta.totalAmountNumeric
            : undefined;

        const nmckText = d.passport && (d.passport as any).nmck
          ? String((d.passport as any).nmck)
          : undefined;

        return { doc: d, totalAmountNumeric, nmckText } as PriceCandidate;
      })
      .filter((c): c is PriceCandidate => c !== null);

    let fromSmeta: string | undefined;

    if (candidates.length > 0) {
      const withNumeric = candidates.filter(
        (c) => typeof c.totalAmountNumeric === 'number'
      );

      const chosen =
        withNumeric.length > 0
          ? withNumeric.reduce((max, current) =>
            (current.totalAmountNumeric || 0) > (max.totalAmountNumeric || 0)
              ? current
              : max
          )
          : candidates[0];

      if (typeof chosen.totalAmountNumeric === 'number') {
        const smeta = ((chosen.doc as any).smetaSummary || {}) as any;
        const raw = smeta.totalAmount;
        let formatted: string;

        if (raw && String(raw).trim()) {
          formatted = String(raw).trim();
        } else {
          formatted = chosen.totalAmountNumeric.toLocaleString('ru-RU', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          });
        }

        const low = formatted.toLowerCase();
        if (!low.includes('руб') && !low.includes('₽')) {
          formatted = `${formatted} ₽`;
        }

        fromSmeta = formatted;
      } else if (chosen.nmckText) {
        fromSmeta = chosen.nmckText;
      }
    }

    if (fromSmeta) {
      return fromSmeta;
    }

    const nmcks = documents
      .map((d) => String((d.passport || {}).nmck || ''))
      .filter((v) =>
        Boolean(v) &&
        v !== 'undefined' &&
        v !== 'Не найдено' &&
        v !== 'Не указано'
      );

    return nmcks[0] || 'Не определено';
  };

  const baseInfo: PackageHubSummary['baseInfo'] = {
    nmckTotal: pickCanonicalNmckForPackage(docs),
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

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ location: 'hubBuilders.ts:341', message: 'buildPackageHubFromAnalysis return', data: { redFlagsLength: redFlagsTop.length, specsTotalDocuments: specsSummary.totalDocuments, specsTotalPositions: specsSummary.totalPositions, hasTimeline: !!timeline, hasGuarantees: !!guarantees, requirementsLength: requirements.length }, timestamp: Date.now(), sessionId: 'debug-session', runId: 'run1', hypothesisId: 'H' }) }).catch(() => { });
  // #endregion

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
