/**
 * Трансформация AnalysisResult в каноническую модель DecisionPreviewData
 * 
 * Правила генерации (жёстко):
 * - Decision определяется ТОЛЬКО так:
 *   - Есть ≥1 DEAL_BREAKER → НЕ УЧАСТВОВАТЬ
 *   - Нет DEAL_BREAKER, есть CONTROLLED → УЧАСТВОВАТЬ С ОГРАНИЧЕНИЯМИ
 *   - Только MARKET_NOISE → УЧАСТВОВАТЬ
 */

import type { AnalysisResult, SeverityLevel } from '../types';
import type { DecisionPreviewData, DecisionType, DecisionConfidence } from '../types/decisionPreview';
import { computeManagementLoadComponents } from './decisionKpi';

/**
 * Форматирование суммы в рубли
 */
function formatRuble(amount: number): string {
  if (amount >= 1_000_000) {
    return `${(amount / 1_000_000).toFixed(1).replace('.', ',')} млн ₽`;
  } else if (amount >= 1_000) {
    return `${(amount / 1_000).toFixed(0)} тыс ₽`;
  } else {
    return `${amount.toFixed(0)} ₽`;
  }
}

/**
 * Парсинг финансовых данных из passport
 */
function parseFinancialData(passport: any) {
  const parseAmount = (str: string): number => {
    if (!str || str === 'Нет') return 0;
    const cleaned = str.replace(/[^\d,.]/g, '').replace(/,/g, '.');
    const num = parseFloat(cleaned);
    return isNaN(num) ? 0 : num;
  };

  const nmck = passport?.nmck || '';
  const advance = passport?.advance || '';
  const secureBid = passport?.secureBid || '';
  const secureContract = passport?.secureContract || '';

  const nmckAmount = parseAmount(nmck);
  
  // Парсим аванс
  let advanceAmount = 0;
  if (advance && advance !== 'Нет') {
    if (advance.includes('%')) {
      const percent = parseAmount(advance.replace('%', ''));
      advanceAmount = nmckAmount > 0 ? (percent / 100) * nmckAmount : 0;
    } else {
      advanceAmount = parseAmount(advance);
    }
  }
  
  // Обеспечение заявки и контракта
  const secureBidAmount = parseAmount(secureBid);
  const secureContractAmount = parseAmount(secureContract);
  const totalGuarantee = secureBidAmount + secureContractAmount;

  return { nmckAmount, advanceAmount, totalGuarantee };
}

/**
 * Определение decision по правилам (жёстко)
 */
function determineDecision(
  dealBreakersCount: number,
  controlledRisksCount: number,
  marketNoiseCount: number
): DecisionType {
  if (dealBreakersCount > 0) {
    return 'DO_NOT_PARTICIPATE';
  } else if (controlledRisksCount > 0) {
    return 'PARTICIPATE_WITH_CONDITIONS';
  } else {
    return 'PARTICIPATE';
  }
}

/**
 * Получение текстовой метки решения
 */
function getDecisionLabel(decision: DecisionType): string {
  switch (decision) {
    case 'DO_NOT_PARTICIPATE':
      return 'НЕ УЧАСТВОВАТЬ';
    case 'PARTICIPATE_WITH_CONDITIONS':
      return 'УЧАСТВОВАТЬ С ОГРАНИЧЕНИЯМИ';
    case 'PARTICIPATE':
      return 'УЧАСТВОВАТЬ';
  }
}

/**
 * Формирование "why" (максимум 2 элемента, жёстко)
 */
function buildWhy(
  dealBreakersCount: number,
  controlledRisksCount: number,
  decision: DecisionType
): string[] {
  const why: string[] = [];

  if (dealBreakersCount > 0) {
    why.push(`Критические стоп-факторы выявлены. Участие несёт высокий риск отклонения заявки.`);
    why.push(`Формальные основания для отклонения заявки на этапе проверки.`);
  } else if (controlledRisksCount > 0) {
    why.push(`Критические стоп-факторы не выявлены. Обнаружены контролируемые риски, устранимые до подачи заявки.`);
    why.push(`Формальных оснований для отклонения заявки не обнаружено.`);
  } else {
    why.push(`Критические стоп-факторы не выявлены. Критических рисков не обнаружено.`);
    why.push(`Формальных оснований для отклонения заявки нет.`);
  }

  return why.slice(0, 2); // Максимум 2
}

/**
 * Формирование финансовой экспозиции
 */
function buildFinancialExposure(
  passport: any,
  dealBreakersCount: number
): {
  potential_extra_costs_rub?: number;
  funds_blocking_percent?: string;
  comment?: string;
} {
  // Защита от отсутствия passport
  if (!passport || typeof passport !== 'object') {
    return {
      comment: 'Финансовые параметры не указаны в документах',
    };
  }

  const { nmckAmount, advanceAmount, totalGuarantee } = parseFinancialData(passport);

  if (dealBreakersCount > 0) {
    // Если есть DEAL_BREAKER - потенциальная потеря
    const potentialLoss = advanceAmount + totalGuarantee + (nmckAmount * 0.01);
    if (potentialLoss > 0) {
      return {
        potential_extra_costs_rub: Math.round(potentialLoss),
        comment: 'Потенциальная потеря (подготовка + обеспечение заявки)',
      };
    }
  } else {
    // Риск дополнительных затрат и блокировки средств
    const exposure: {
      potential_extra_costs_rub?: number;
      funds_blocking_percent?: string;
      comment?: string;
    } = {};

    if (totalGuarantee > 0 && nmckAmount > 0) {
      const guaranteePercent = (totalGuarantee / nmckAmount) * 100;
      if (guaranteePercent > 0) {
        exposure.funds_blocking_percent = `${guaranteePercent.toFixed(0)}%`;
      }
    }

    // Оценка дополнительных затрат (2.5% от НМЦК как средняя оценка)
    if (nmckAmount > 0) {
      exposure.potential_extra_costs_rub = Math.round(nmckAmount * 0.025);
    }

    exposure.comment = 'Экспозиция зависит от выбранных условий обеспечения';

    return exposure;
  }

  return {};
}

/**
 * Интерпретация индекса управленческой нагрузки (шкала для директора)
 *
 * 0–30   → Рутинное участие (делегируемо)
 * 31–50  → Участие с управленческим контролем
 * 51–70  → Участие только при личном внимании директора
 * 71–85  → Высокая управленческая нагрузка
 * 86–100 → Управленчески нецелесообразно
 */
function getManagementLoadInterpretation(score: number): string {
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
}

/**
 * Формирование сценариев (упрощённые, без воды)
 */
function buildScenarios(
  dealBreakersCount: number,
  controlledRisksCount: number
): { best: string; worst: string } {
  if (dealBreakersCount > 0) {
    return {
      best: 'Риски устранены → заявка принята → контракт исполним → прибыль в рамках модели',
      worst: 'Риски проигнорированы → отклонение заявки → потеря подготовительных затрат',
    };
  } else if (controlledRisksCount > 0) {
    return {
      best: 'Риски устранены → заявка принята → контракт исполним → прибыль в рамках модели',
      worst: 'Риски проигнорированы → блокировка средств → дополнительные расходы → маржа под угрозой',
    };
  } else {
    return {
      best: 'Участие без отклонений → контракт исполним → прибыль в рамках модели',
      worst: 'Игнорирование условий → дополнительные расходы → маржа под угрозой',
    };
  }
}

/**
 * Основная функция трансформации
 */
export function transformToDecisionPreview(result: AnalysisResult): DecisionPreviewData {
  // Защита от некорректных данных
  if (!result) {
    throw new Error('AnalysisResult is null or undefined');
  }

  const dealBreakers = result.deal_breakers || [];
  const issues = result.issues || [];
  // Детерминированный ИУН по канону A+B+C+D
  const mlComponents = computeManagementLoadComponents(result);
  const score = mlComponents.total;

  // Группировка рисков по severity_level
  const riskGroups: Map<SeverityLevel, Array<{ title: string; description?: string; evidence?: any }>> = new Map([
    ['DEAL_BREAKER', []],
    ['CONTROLLED_RISK', []],
    ['MARKET_NOISE', []],
  ]);

  // Обрабатываем deal_breakers как DEAL_BREAKER
  dealBreakers.forEach((db: any, idx: number) => {
    const title = typeof db === 'string' ? db : (db?.title || db);
    riskGroups.get('DEAL_BREAKER')!.push({
      title: String(title),
      description: typeof db === 'object' ? db.description : undefined,
    });
  });

  // Обрабатываем issues по severity_level
  issues.forEach((issue) => {
    const severityLevel = (issue as any).severity_level as SeverityLevel | undefined;
    const severity = (issue.severity || '').toUpperCase();
    
    let targetLevel: SeverityLevel = 'CONTROLLED_RISK';
    if (severityLevel) {
      targetLevel = severityLevel;
    } else if (severity === 'HIGH' || severity === 'CRITICAL') {
      targetLevel = 'CONTROLLED_RISK';
    } else if (severity === 'LOW' || (issue as any).risk_type === 'FORMAL') {
      targetLevel = 'MARKET_NOISE';
    }

    const group = riskGroups.get(targetLevel);
    if (group) {
      group.push({
        title: issue.title,
        description: issue.description,
        // evidence может содержать привязку к документу/пункту и цитату
        evidence: (issue as any).evidence,
      });
    }
  });

  const dealBreakersCount = riskGroups.get('DEAL_BREAKER')?.length || 0;
  const controlledRisksCount = riskGroups.get('CONTROLLED_RISK')?.length || 0;
  const marketNoiseCount = riskGroups.get('MARKET_NOISE')?.length || 0;

  // Определение decision (по правилам, жёстко)
  const decision = determineDecision(dealBreakersCount, controlledRisksCount, marketNoiseCount);
  const decisionLabel = getDecisionLabel(decision);
  
  // Валидация обязательных данных
  if (!decisionLabel || !decision) {
    console.error('[transformToDecisionPreview] Failed to determine decision', {
      dealBreakersCount,
      controlledRisksCount,
      marketNoiseCount,
      decision,
      decisionLabel,
    });
    throw new Error('Failed to determine decision type');
  }

  // Определение confidence на основе количества рисков
  let decisionConfidence: DecisionConfidence = 'MEDIUM';
  if (dealBreakersCount === 0 && controlledRisksCount === 0 && marketNoiseCount === 0) {
    decisionConfidence = 'HIGH';
  } else if (dealBreakersCount > 0) {
    decisionConfidence = 'LOW';
  }

  // Формирование controlled_risks (максимум 3).
  // Если для риска нет evidence, он не будет отображаться (юридическая воспроизводимость).
  const controlledRisks = (riskGroups.get('CONTROLLED_RISK') || [])
    .filter((risk) => Array.isArray((risk as any).evidence) && (risk as any).evidence.length > 0)
    .slice(0, 3)
    .map((risk, idx) => ({
      id: `CR-${String(idx + 1).padStart(2, '0')}`,
      title: risk.title,
      impact: 'Риск заморозки средств или дополнительных затрат',
      control: 'Выбор более жёсткого условия при подаче заявки и контроль исполнения контракта',
      document_name: (risk as any).document_name,
      section: (risk as any).section,
      rationale: (risk as any).rationale,
      risk_for_company: (risk as any).risk_for_company,
      status_label: (risk as any).status_label,
      evidence: (risk as any).evidence,
    }));

  // Формирование deal_breakers (максимум 2)
  const dealBreakersFormatted = (riskGroups.get('DEAL_BREAKER') || [])
    .slice(0, 2)
    .map((db, idx) => ({
      id: `DB-${String(idx + 1).padStart(2, '0')}`,
      title: db.title,
      impact: 'Отклонение заявки на формальной проверке',
      document_name: (db as any).document_name,
      section: (db as any).section,
      rationale: (db as any).rationale,
      risk_for_company: (db as any).risk_for_company,
      status_label: (db as any).status_label,
      evidence: (db as any).evidence,
    }));

  // Финансовая экспозиция
  const financialExposure = buildFinancialExposure(result.passport, dealBreakersCount);

  // Интерпретация индекса
  const managementLoadInterpretation = getManagementLoadInterpretation(score);

  // Сценарии
  const scenarios = buildScenarios(dealBreakersCount, controlledRisksCount);

  // Почему (максимум 2)
  const why = buildWhy(dealBreakersCount, controlledRisksCount, decision);

  // Аналитическое пояснение для директора (опционально, вывод по запросу)
  // По умолчанию не заполняется, чтобы не навязывать интерпретацию.
  const directorExplanation: string | undefined = undefined;

  return {
    decision_preview: {
      decision,
      decision_label: decisionLabel,
      decision_confidence: decisionConfidence,
      
      summary: {
        deal_breakers_found: dealBreakersCount > 0,
        controlled_risks_count: controlledRisksCount,
        market_noise_count: marketNoiseCount,
      },

      why,

      financial_exposure: financialExposure,

      management_load_index: {
        value: score,
        max: 100,
        interpretation: managementLoadInterpretation,
      },

      director_explanation: directorExplanation,

      deal_breakers: dealBreakersFormatted,

      controlled_risks: controlledRisks,

      scenarios,

      decision_actions: {
        allow_participate: decision !== 'DO_NOT_PARTICIPATE',
        allow_decline: true, // Всегда доступен
        require_comment: true, // Всегда требуется комментарий
      },
    },
  };
}

