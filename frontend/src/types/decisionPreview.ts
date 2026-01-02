/**
 * Каноническая JSON-модель Decision Preview
 * 
 * Это ядро продукта. Любой AI-анализ обязан приводиться к этой структуре.
 */

export type DecisionType = 'PARTICIPATE' | 'PARTICIPATE_WITH_CONDITIONS' | 'DO_NOT_PARTICIPATE';

export type DecisionConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface RiskEvidence {
  /** Идентификатор документа (если известен) */
  document_id?: string;
  /** Название документа (например, "Проект договора") */
  document_name?: string;
  /** Ссылка на раздел / пункт (например, "Раздел 3.2", "п. 4.1.1") */
  section_ref?: string;
  /** Дословная выдержка из документа (1–3 строки) */
  quote: string;
}

export interface DecisionPreviewData {
  decision_preview: {
    decision: DecisionType;
    decision_label: string;
    decision_confidence: DecisionConfidence;
    
    summary: {
      deal_breakers_found: boolean;
      controlled_risks_count: number;
      market_noise_count: number;
    };

    why: string[]; // Максимум 2 элемента

    financial_exposure: {
      potential_extra_costs_rub?: number;
      funds_blocking_percent?: string;
      comment?: string;
    };

    management_load_index: {
      value: number;
      max: number;
      interpretation: string;
    };

    /**
     * Опциональное аналитическое пояснение для директора.
     * Не участвует в расчёте ИУН, принятии решения и Board Pack.
     * Показывается только по явному запросу директора.
     */
    director_explanation?: string;

    deal_breakers: Array<{
      id: string;
      title: string;
      impact?: string;
      /** Название документа-источника (например, "Проект договора") */
      document_name?: string;
      /** Пункт или раздел (например, "п. 6.3", "раздел 5") */
      section?: string;
      /** Краткое описание найденного фрагмента */
      rationale?: string;
      /** Риск для компании (управленческое последствие) */
      risk_for_company?: string;
      /** Статус риска: "критический" / "управляемый" / "информационный" */
      status_label?: string;
      /** Подтверждающие материалы (источники риска) */
      evidence?: RiskEvidence[];
    }>;
    
    controlled_risks: Array<{
      id: string;
      title: string;
      impact: string;
      control: string;
      document_name?: string;
      section?: string;
      rationale?: string;
      risk_for_company?: string;
      status_label?: string;
      evidence?: RiskEvidence[];
    }>;

    scenarios: {
      best: string;
      worst: string;
    };

    decision_actions: {
      allow_participate: boolean;
      allow_decline: boolean;
      require_comment: boolean;
    };
  };
}





