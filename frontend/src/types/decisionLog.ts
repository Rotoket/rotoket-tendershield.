/**
 * Decision Log / Audit Trail — журнал управленческих решений
 * 
 * Это killer-feature, превращающая продукт в Decision Support System.
 */

import type { DecisionType } from './decisionPreview';

export interface DecisionLogEntry {
  decision_log_entry: {
    /** Идентификатор тендера/анализа */
    tender_id: string;
    
    /** Тип решения */
    decision: DecisionType;
    
    /** Текстовая метка решения */
    decision_label: string;
    
    /** ISO timestamp решения */
    timestamp: string;
    
    /** Роль принимающего решение (CEO, Director, etc.) */
    decision_maker_role?: string;
    
    /** ID пользователя */
    decision_maker_id: string;
    
    /** Email пользователя (для идентификации) */
    decision_maker_email?: string;
    
    /** Имя пользователя */
    decision_maker_name?: string;
    
    /** Snapshot Decision Preview на момент принятия решения */
    decision_preview_snapshot: {
      deal_breakers_found: boolean;
      controlled_risks_count: number;
      market_noise_count: number;
      financial_exposure_rub?: number;
      funds_blocking_percent?: string;
      management_load_index: number;
      /** Список ID deal breakers */
      deal_breaker_ids?: string[];
      /** Список ID controlled risks */
      controlled_risk_ids?: string[];
    };
    
    /** Комментарий директора (обязателен) */
    comment: string;
    
    /** Системная пометка */
    system_note: string;
    
    /** Версия анализа, на основе которого принято решение */
    analysis_version?: string;
  };
}




































