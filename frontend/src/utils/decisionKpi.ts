import { AuditHistoryItem, DecisionKPI, AnalysisResult } from '../types';

/**
 * Рассчитывает KPI управленческих решений на основе истории анализов
 */
export const calculateDecisionKpi = (historyItems: AuditHistoryItem[]): DecisionKPI => {
  const kpi: DecisionKPI = {
    totalAnalyses: historyItems.length,
    decisionsMade: 0,
    participateCount: 0,
    participateWithConditionsCount: 0,
    doNotParticipateCount: 0,
    postponeCount: 0,
    highRiskParticipationCount: 0,
    decisionsWithDealBreakersCount: 0,
  };

  // Собираем статистику по решениям
  const participateScores: number[] = [];
  const rejectedScores: number[] = [];

  historyItems.forEach((item) => {
    if (!item.user_decision) {
      return; // Пропускаем анализы без решений
    }

    kpi.decisionsMade++;

    // Подсчитываем типы решений
    switch (item.user_decision.decision) {
      case 'participate':
        kpi.participateCount++;
        participateScores.push(item.summaryScore);
        // Высокий риск: score < 50 или verdict === 'STOP' или 'CAUTION'
        if (
          item.summaryScore < 50 ||
          item.verdict === 'STOP' ||
          item.verdict === 'CAUTION'
        ) {
          kpi.highRiskParticipationCount++;
        }
        break;

      case 'participate_with_conditions':
        kpi.participateWithConditionsCount++;
        participateScores.push(item.summaryScore);
        // Высокий риск: score < 50 или verdict === 'STOP' или 'CAUTION'
        if (
          item.summaryScore < 50 ||
          item.verdict === 'STOP' ||
          item.verdict === 'CAUTION'
        ) {
          kpi.highRiskParticipationCount++;
        }
        break;

      case 'do_not_participate':
        kpi.doNotParticipateCount++;
        rejectedScores.push(item.summaryScore);
        break;

      case 'postpone':
        kpi.postponeCount++;
        break;
    }

    // Подсчитываем решения с deal breakers
    if (item.deal_breakers && item.deal_breakers.length > 0) {
      kpi.decisionsWithDealBreakersCount++;
    }
  });

  // Рассчитываем средние score
  if (participateScores.length > 0) {
    kpi.averageScoreParticipate =
      participateScores.reduce((sum, score) => sum + score, 0) /
      participateScores.length;
  }

  if (rejectedScores.length > 0) {
    kpi.averageScoreRejected =
      rejectedScores.reduce((sum, score) => sum + score, 0) /
      rejectedScores.length;
  }

  return kpi;
};

// Компоненты Индекса управленческой нагрузки (ИУН) по канону A+B+C+D
export interface ManagementLoadComponents {
  A: number; // Документальные противоречия (0–30)
  B: number; // Финансовая неопределённость (0–25)
  C: number; // Юридико-процедурная сложность (0–25)
  D: number; // Объём ручного управленческого контроля (0–20)
  total: number; // Сумма A+B+C+D (0–100)
}

/**
 * Детерминированная оценка Индекса управленческой нагрузки (ИУН)
 * на основе результата анализа (AnalysisResult).
 *
 * Использует только наблюдаемые признаки: passport и issues.
 */
export const computeManagementLoadComponents = (result: AnalysisResult): ManagementLoadComponents => {
  const issues = result.issues || [];
  const dealBreakers = result.deal_breakers || [];

  // A. Документальные противоречия (0–30)
  const contradictionKeywords = ['разночт', 'противореч', 'несоответств', 'разные', 'расхожд'];
  const contradictionCount = issues.filter((iss) => {
    const text = `${iss.title || ''} ${iss.description || ''}`.toLowerCase();
    return contradictionKeywords.some((kw) => text.includes(kw));
  }).length;

  let A = 0;
  if (contradictionCount === 0) {
    A = 0;
  } else if (contradictionCount <= 2) {
    A = 10;
  } else if (contradictionCount <= 4) {
    A = 20;
  } else {
    A = 30;
  }

  // B. Финансовая неопределённость (0–25)
  const passport: any = (result as any).passport || {};
  const hasNmck = !!passport.nmck;
  const hasAnyGuarantee = !!(passport.guarantee || passport.bidSecurity || passport.contractSecurity);

  // Ищем упоминания штрафов/санкций/аванса в рисках
  const financialKeywords = ['штраф', 'санкц', 'аванс', 'оплат', 'расчёт', 'маржинал'];
  const hasFinancialIssues = issues.some((iss) => {
    const text = `${iss.title || ''} ${iss.description || ''}`.toLowerCase();
    return financialKeywords.some((kw) => text.includes(kw));
  });

  let B = 0;
  if (!hasNmck) {
    // Цена и объёмы не зафиксированы явно
    B = 25;
  } else if (hasNmck && !hasAnyGuarantee) {
    // Есть цена, но неясны обеспечения / блокировка средств
    B = hasFinancialIssues ? 20 : 10;
  } else {
    // Есть базовые финансовые параметры
    B = hasFinancialIssues ? 10 : 0;
  }

  // C. Юридико-процедурная сложность (0–25)
  const legalKeywords = ['жалоб', 'лиценз', 'заявк', 'отклонен', 'формальн', 'срок подач'];
  const legalIssuesCount = issues.filter((iss) => {
    const text = `${iss.title || ''} ${iss.description || ''}`.toLowerCase();
    const severity = (iss.severity || '').toUpperCase();
    const level = (iss as any).severity_level;
    return (
      severity === 'HIGH' ||
      severity === 'CRITICAL' ||
      level === 'DEAL_BREAKER' ||
      legalKeywords.some((kw) => text.includes(kw))
    );
  }).length;

  let C = 0;
  if (legalIssuesCount === 0) {
    C = 0;
  } else if (legalIssuesCount === 1) {
    C = 10;
  } else if (legalIssuesCount <= 3) {
    C = 15;
  } else {
    C = 25;
  }

  // D. Объём ручного управленческого контроля (0–20)
  const totalRisks = issues.length;
  const dealBreakersCount = dealBreakers.length;

  let D = 0;
  if (dealBreakersCount === 0 && totalRisks === 0) {
    D = 0;
  } else if (dealBreakersCount === 0 && totalRisks === 1) {
    D = 5;
  } else if (dealBreakersCount === 0 && totalRisks <= 3) {
    D = 10;
  } else {
    // Несколько рисков или есть критические факторы — требуется постоянный контроль
    D = 20;
  }

  const totalRaw = A + B + C + D;
  const total = Math.max(0, Math.min(100, totalRaw));

  return { A, B, C, D, total };
};














































