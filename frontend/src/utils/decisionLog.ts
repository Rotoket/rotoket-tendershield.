/**
 * Утилиты для создания Decision Log Entry
 * 
 * Decision Log — это killer-feature, превращающая продукт в Decision Support System.
 */

import type { DecisionPreviewData } from '../types/decisionPreview';
import type { DecisionLogEntry } from '../types/decisionLog';

interface CreateDecisionLogEntryParams {
  tenderId: string;
  decision: DecisionPreviewData['decision_preview']['decision'];
  decisionLabel: string;
  decisionPreview: DecisionPreviewData['decision_preview'];
  comment: string;
  decisionMakerId: string;
  decisionMakerRole?: string;
  decisionMakerEmail?: string;
  decisionMakerName?: string;
  analysisVersion?: string;
}

/**
 * Создание Decision Log Entry для сохранения в журнал
 */
export function createDecisionLogEntry(params: CreateDecisionLogEntryParams): DecisionLogEntry {
  const {
    tenderId,
    decision,
    decisionLabel,
    decisionPreview,
    comment,
    decisionMakerId,
    decisionMakerRole,
    decisionMakerEmail,
    decisionMakerName,
    analysisVersion,
  } = params;

  const logEntry: DecisionLogEntry = {
    decision_log_entry: {
      tender_id: tenderId,
      decision,
      decision_label: decisionLabel,
      timestamp: new Date().toISOString(),
      decision_maker_role: decisionMakerRole,
      decision_maker_id: decisionMakerId,
      decision_maker_email: decisionMakerEmail,
      decision_maker_name: decisionMakerName,
      decision_preview_snapshot: {
        deal_breakers_found: decisionPreview.summary.deal_breakers_found,
        controlled_risks_count: decisionPreview.summary.controlled_risks_count,
        market_noise_count: decisionPreview.summary.market_noise_count,
        financial_exposure_rub: decisionPreview.financial_exposure.potential_extra_costs_rub,
        funds_blocking_percent: decisionPreview.financial_exposure.funds_blocking_percent,
        management_load_index: decisionPreview.management_load_index.value,
        deal_breaker_ids: decisionPreview.deal_breakers.map(db => db.id),
        controlled_risk_ids: decisionPreview.controlled_risks.map(cr => cr.id),
      },
      comment,
      system_note: 'Решение принято пользователем. Система носит аналитический характер.',
      analysis_version: analysisVersion,
    },
  };

  return logEntry;
}

/**
 * Генерация уникального tender_id, если он не передан
 */
export function generateTenderId(): string {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return `TND-${new Date().getFullYear()}-${String(random).padStart(3, '0')}`;
}




































