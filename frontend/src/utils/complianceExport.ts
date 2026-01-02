import type { AnalysisResult, PackageAnalysis, UserDecision, AuditEvent, UserRole, AuditHistoryItem } from '../types';

export interface BuildComplianceReportParams {
  entityType: 'single' | 'package';
  entityId: string;
  result: AnalysisResult | PackageAnalysis;
  userDecision: UserDecision;
  auditTrail: AuditEvent[];
  role: UserRole;
}

const formatDateTime = (iso: string | undefined): string => {
  if (!iso) return '—';
  try {
    const date = new Date(iso);
    return isNaN(date.getTime()) ? '—' : date.toLocaleString('ru-RU');
  } catch {
    return '—';
  }
};

const frontendVersion = 'frontend_v1';

const countRisks = (result: AnalysisResult | PackageAnalysis): number => {
  if ('issues' in result) {
    return result.issues?.length ?? 0;
  }
  return result.globalIssues?.length ?? 0;
};

const countDealBreakers = (result: AnalysisResult | PackageAnalysis): number => {
  if ('deal_breakers' in result) {
    return result.deal_breakers?.length ?? 0;
  }
  // Для пакетного анализа пока опираемся только на глобальные критические риски
  if ('globalIssues' in result) {
    return result.globalIssues?.filter((g) => g.severity?.toLowerCase() === 'critical').length ?? 0;
  }
  return 0;
};

const getContext = (entityType: 'single' | 'package', result: AnalysisResult | PackageAnalysis) => {
  if (entityType === 'single') {
    const single = result as AnalysisResult;
    const law = single.hub?.baseInfo.fz || single.passport?.fz || '—';
    const nmck = single.hub?.baseInfo.nmck || single.passport?.nmck || '—';
    const region = single.hub?.baseInfo.region || single.passport?.region || '—';
    const documentsCount = 1; // для одиночного анализа
    const analysisDate = undefined; // отдельной даты анализа нет, фиксируется в Audit Trail
    return { law, nmck, region, documentsCount, analysisDate };
  }

  const pack = result as PackageAnalysis;
  const law = pack.hub?.baseInfo.fz || '—';
  const nmck = pack.hub?.baseInfo.nmckTotal || '—';
  const region = pack.hub?.baseInfo.region || '—';
  const documentsCount = pack.documents?.length ?? 0;
  const analysisDate = undefined;
  return { law, nmck, region, documentsCount, analysisDate };
};

const getDecisionLabel = (decision: UserDecision['decision']): string => {
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

const getDecisionEventSnapshot = (
  entityType: 'single' | 'package',
  entityId: string,
  auditTrail: AuditEvent[],
) => {
  const mappedEntityType = entityType === 'single' ? 'single_analysis' : 'package_analysis';
  const eventsForEntity = auditTrail.filter(
    (e) => e.entityType === mappedEntityType && e.entityId === entityId,
  );

  const lastDecisionEvent = [...eventsForEntity]
    .reverse()
    .find((e) => e.eventType === 'decision_fixed' || e.eventType === 'decision_confirmed_by_director');

  return {
    decisionEventId: lastDecisionEvent?.id ?? '—',
    decisionEventDate: lastDecisionEvent?.timestamp ?? undefined,
    chainLength: eventsForEntity.length,
  };
};

export interface BuildComplianceReportFromHistoryParams {
  item: AuditHistoryItem;
  auditTrail: AuditEvent[];
  role: UserRole;
}

export const buildComplianceReport = (params: BuildComplianceReportParams): string => {
  const { entityType, entityId, result, userDecision, auditTrail, role } = params;

  const nowIso = new Date().toISOString();
  const context = getContext(entityType, result);
  const risksCount = countRisks(result);
  const dealBreakersCount = countDealBreakers(result);
  const { decisionEventId, decisionEventDate, chainLength } = getDecisionEventSnapshot(
    entityType,
    entityId,
    auditTrail,
  );

  const lines: string[] = [];

  // 1. DOCUMENT HEADER
  lines.push('COMPLIANCE / LEGAL EXPORT');
  lines.push('');
  lines.push(`Тип анализа: ${entityType === 'single' ? 'Одиночный анализ' : 'Комплексный аудит пакета'}`);
  lines.push(`ID анализа: ${entityId}`);
  lines.push(`Дата и время формирования: ${formatDateTime(nowIso)}`);
  lines.push('');

  // 2. ANALYSIS CONTEXT
  lines.push('ANALYSIS CONTEXT');
  lines.push(`Закон: ${context.law}`);
  lines.push(`НМЦК / совокупная НМЦК: ${context.nmck}`);
  lines.push(`Регион: ${context.region}`);
  lines.push(`Количество документов: ${context.documentsCount}`);
  lines.push(`Дата анализа: ${formatDateTime(context.analysisDate)}`);
  lines.push(`Версия системы: ${frontendVersion}`);
  lines.push('');

  // 3. ANALYSIS RESULTS (FACTS ONLY)
  lines.push('ANALYSIS RESULTS (FACTS)');
  if ('score' in result) {
    lines.push(`Индекс управленческой нагрузки: ${result.score}`);
    lines.push(`Вердикт системы: ${result.verdict}`);
  } else {
    lines.push(`Индекс управленческой нагрузки (сводный): ${result.summaryScore}`);
    lines.push(`Вердикт системы (по пакету): ${result.verdict}`);
  }
  lines.push(`Количество выявленных рисков: ${risksCount}`);
  lines.push(`Количество критических стоп-факторов: ${dealBreakersCount}`);
  lines.push('');

  // 4. IDENTIFIED ISSUES
  lines.push('IDENTIFIED ISSUES');
  lines.push('Deal breakers:');
  if ('deal_breakers' in result && result.deal_breakers && result.deal_breakers.length > 0) {
    result.deal_breakers.forEach((d, idx) => {
      lines.push(`  ${idx + 1}. ${d}`);
    });
  } else {
    lines.push('  Нет зафиксированных deal breakers.');
  }

  lines.push('');
  lines.push('Ключевые риски:');
  if ('issues' in result && result.issues && result.issues.length > 0) {
    result.issues.forEach((issue, idx) => {
      lines.push(`  ${idx + 1}. [${issue.severity}] ${issue.title}`);
    });
  } else if ('globalIssues' in result && result.globalIssues && result.globalIssues.length > 0) {
    result.globalIssues.forEach((issue, idx) => {
      lines.push(`  ${idx + 1}. [${issue.severity}] ${issue.title}`);
    });
  } else {
    lines.push('  Нет зафиксированных ключевых рисков.');
  }

  lines.push('');
  lines.push('Ссылки на нормы закона (если есть):');
  if ('redFlags' in result && result.redFlags && result.redFlags.length > 0) {
    result.redFlags.forEach((rf, idx) => {
      if (rf.lawReference) {
        lines.push(`  ${idx + 1}. ${rf.lawReference}`);
      }
    });
  } else if ('hub' in result && result.hub?.redFlagsTop?.length) {
    result.hub.redFlagsTop.forEach((rf, idx) => {
      if (rf.lawReference) {
        lines.push(`  ${idx + 1}. ${rf.lawReference}`);
      }
    });
  } else {
    lines.push('  Нет явных ссылок на нормы закона.');
  }
  lines.push('');

  // 5. USER DECISION
  lines.push('USER DECISION');
  lines.push(`Принятое решение: ${getDecisionLabel(userDecision.decision)}`);
  lines.push(`Дата и время решения: ${formatDateTime(userDecision.timestamp)}`);
  lines.push(`Роль пользователя: ${role === 'director' ? 'Директор / уполномоченное лицо' : 'Эксперт / аналитик'}`);
  lines.push(`Комментарий: ${userDecision.comment || '—'}`);
  lines.push('');

  // 6. AUDIT TRAIL SNAPSHOT
  lines.push('AUDIT TRAIL SNAPSHOT');
  lines.push(`ID события фиксации решения: ${decisionEventId}`);
  lines.push(`Дата события фиксации решения: ${formatDateTime(decisionEventDate)}`);
  lines.push(`Количество событий в цепочке по анализу: ${chainLength}`);
  lines.push('Хеш / fingerprint: —');
  lines.push('');

  // 7. DISCLAIMER
  lines.push('DISCLAIMER');
  lines.push(
    'Отчёт сформирован автоматически. Система не является юридическим консультантом. Решение принято уполномоченным лицом.',
  );

  return lines.join('\n');
};

export const buildComplianceReportFromHistoryItem = (
  params: BuildComplianceReportFromHistoryParams,
): string => {
  const { item, auditTrail, role } = params;

  const nowIso = new Date().toISOString();
  const entityType: 'single' | 'package' = item.kind === 'package' ? 'package' : 'single';
  const { decisionEventId, decisionEventDate, chainLength } = getDecisionEventSnapshot(
    entityType,
    item.id,
    auditTrail,
  );

  const lines: string[] = [];

  // 1. DOCUMENT HEADER
  lines.push('COMPLIANCE / LEGAL EXPORT');
  lines.push('');
  lines.push(`Тип анализа: ${entityType === 'single' ? 'Одиночный анализ' : 'Комплексный аудит пакета'}`);
  lines.push(`ID анализа: ${item.id}`);
  lines.push(`Дата и время формирования: ${formatDateTime(nowIso)}`);
  lines.push('');

  // 2. ANALYSIS CONTEXT (ограниченный — только доступные поля)
  lines.push('ANALYSIS CONTEXT');
  lines.push('Закон: —');
  lines.push('НМЦК / совокупная НМЦК: —');
  lines.push('Регион: —');
  lines.push(`Количество документов: ${item.files.length}`);
  lines.push(`Дата анализа: ${formatDateTime(item.createdAt)}`);
  lines.push(`Версия системы: ${frontendVersion}`);
  lines.push('');

  // 3. ANALYSIS RESULTS (FACTS ONLY)
  lines.push('ANALYSIS RESULTS (FACTS)');
  lines.push(`Индекс управленческой нагрузки: ${Math.round(item.summaryScore)}`);
  lines.push(`Вердикт системы: ${item.verdict}`);
  const dealBreakersCount = item.deal_breakers?.length ?? 0;
  lines.push(`Количество критических стоп-факторов: ${dealBreakersCount}`);
  lines.push('');

  // 4. IDENTIFIED ISSUES
  lines.push('IDENTIFIED ISSUES');
  lines.push('Deal breakers:');
  if (item.deal_breakers && item.deal_breakers.length > 0) {
    item.deal_breakers.forEach((d, idx) => {
      lines.push(`  ${idx + 1}. ${d}`);
    });
  } else {
    lines.push('  Нет зафиксированных deal breakers.');
  }
  lines.push('');
  lines.push('Ключевые риски:');
  lines.push('  Нет явных данных о ключевых рисках в краткой истории анализа.');
  lines.push('');
  lines.push('Ссылки на нормы закона (если есть):');
  lines.push('  Нет явных ссылок на нормы закона в краткой истории анализа.');
  lines.push('');

  // 5. USER DECISION
  lines.push('USER DECISION');
  if (item.user_decision) {
    lines.push(`Принятое решение: ${getDecisionLabel(item.user_decision.decision)}`);
    lines.push(`Дата и время решения: ${formatDateTime(item.user_decision.timestamp)}`);
    lines.push(
      `Роль пользователя: ${
        role === 'director' ? 'Директор / уполномоченное лицо' : 'Эксперт / аналитик'
      }`,
    );
    lines.push(`Комментарий: ${item.user_decision.comment || '—'}`);
  } else {
    lines.push('Решение пользователя не зафиксировано.');
  }
  lines.push('');

  // 6. AUDIT TRAIL SNAPSHOT
  lines.push('AUDIT TRAIL SNAPSHOT');
  lines.push(`ID события фиксации решения: ${decisionEventId}`);
  lines.push(`Дата события фиксации решения: ${formatDateTime(decisionEventDate)}`);
  lines.push(`Количество событий в цепочке по анализу: ${chainLength}`);
  lines.push('Хеш / fingerprint: —');
  lines.push('');

  // 7. DISCLAIMER
  lines.push('DISCLAIMER');
  lines.push(
    'Отчёт сформирован автоматически. Система не является юридическим консультантом. Решение принято уполномоченным лицом.',
  );

  return lines.join('\n');
};















