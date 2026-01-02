
export enum AppView {
  LANDING = 'LANDING', // Первый экран для неавторизованных пользователей
  ANALYSIS_TYPE_SELECT = 'ANALYSIS_TYPE_SELECT', // Выбор типа анализа
  LOGIN = 'LOGIN',
  ANALYZER = 'ANALYZER', // Главный экран
  AUDIT = 'AUDIT', // Комплексный аудит пакета документов
  GENERATOR = 'GENERATOR', // Генератор документов
  KNOWLEDGE = 'KNOWLEDGE', // База знаний
  HISTORY = 'HISTORY',
  CALCULATOR = 'CALCULATOR', // Калькулятор маржинальности
  PROFILE = 'PROFILE', // Личный кабинет
  ANALYTICS = 'ANALYTICS', // Аналитика и метрики
  HELP = 'HELP', // Справочный центр / помощь
  POST_DECISION_LOCK = 'POST_DECISION_LOCK', // Экран после фиксации решения (требует оплаты)
  PAYMENT = 'PAYMENT', // Экран оплаты/активации доступа
}

export interface User {
  id: string;
  name: string;
  company: string;
  tariff: 'Start' | 'Pro' | 'Enterprise';
  email?: string;
}

// --- Decision Layer: user decision & roles ---

export type UserDecisionType =
  | 'participate'
  | 'participate_with_conditions'
  | 'do_not_participate'
  | 'postpone';

export interface UserDecision {
  decision: UserDecisionType;
  comment?: string;
  timestamp: string; // ISO
}

// Роль пользователя в системе (frontend-only RBAC)
export type UserRole = 'expert' | 'director';

// Для передачи решения в сервисы и отчёты
export interface UserDecisionData {
  decision: UserDecisionType;
  comment?: string;
  timestamp: string;
  dealBreakersCount?: number;
  score?: number;
  verdict?: VerdictType | string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
}

export interface UploadedFile {
  id: string;
  name: string;
  size: string; // e.g. "2.4 MB"
  type: 'pdf' | 'docx' | 'xlsx' | 'txt' | 'csv' | 'xls';
  content: string; // Base64 placeholder or text
}

// Universal structure for Deep Audit
export interface AuditCheckItem {
  label: string; // e.g. "Наличие аванса"
  status: 'YES' | 'NO' | 'PARTIAL' | 'RISK';
  value: string; // e.g. "30% в течение 10 дней"
  details?: string;
}

export interface DeepAuditBlock {
  id: string;
  title: string; // e.g. "Блок 1: Финансовые условия"
  status: 'OK' | 'WARNING' | 'CRITICAL';
  items: AuditCheckItem[];
}

// PHASE 1: Новый формат Tender Passport
export interface TenderSource {
  document_name: string;
  page_number?: number;
  section?: string;
  quote: string;
  extraction_method: 'llm' | 'regex' | 'manual';
  confidence: number; // 0.0 - 1.0
}

export interface GovernmentData {
  customer_id?: string;
  previous_tenders_count: number;
  avg_discount_percent?: number;
  avg_competitor_count?: number;
  avg_payment_delay_days?: number;
  data_source: string;
  data_freshness: string;
  confidence_level: 'low' | 'medium' | 'high';
}

export interface TenderPassportNew {
  // ОБЯЗАТЕЛЬНЫЕ поля
  nmck_numeric: number;
  nmck_formatted: string;
  nmck_source: TenderSource;
  customer: string;
  customer_source: TenderSource;
  
  // ОПЦИОНАЛЬНЫЕ поля
  deadline?: string; // ISO date string
  deadline_source?: TenderSource;
  contract_term_months?: number;
  contract_term_source?: TenderSource;
  guarantee_amount?: number;
  guarantee_source?: TenderSource;
  penalty_percent?: number;
  penalty_source?: TenderSource;
  
  // МЕТАДАННЫЕ
  completion_percentage: number;
  warnings: string[];
  government_data?: GovernmentData;
}

export interface TenderPassport {
  // Паспорт тендера (ключевые поля) - СТАРЫЙ ФОРМАТ (для обратной совместимости)
  tenderNumber?: string;
  customer?: string;

  // Основное
  nmck: string; // "10 000 000 ₽"
  /** Числовое значение НМЦК, если удалось извлечь (для сортировок/порогов) */
  nmckNumeric?: number | null;
  fz: string; // "44-ФЗ"

  // Деньги
  advance: string; // "30%" or "Нет"
  paymentTerms?: string; // "7 раб. дней"

  /** Старое имя (используется в UI) */
  secureBid?: string; // "50 000 ₽ (0.5%)"
  /** Новое имя из backend / LLM */
  bidSecurity?: string;

  /** Старое имя (используется в UI) */
  secureContract?: string; // "1 000 000 ₽ (10%)"
  /** Новое имя из backend / LLM */
  contractSecurity?: string;

  secureWarranty?: string; // "Нет" or "5%"
  guarantee?: string;

  // Сроки
  deadlineApp: string; // Дата подачи
  deadlineExecution: string; // Дата исполнения

  // Место
  region: string;
}

export interface PassportValidation {
  is_complete: boolean;
  missing_fields: string[];
  warnings: string[];
}

export interface EvidenceItem {
  document_name: string;
  page_reference?: string | null;
  section_reference?: string | null;
  quote: string;
}

export interface KeywordMatch {
  keyword: string;
  context: string;
  count: number;
}

export type VerdictType = 'PARTICIPATE' | 'CAUTION' | 'STOP';

// Типы рисков по уровню уверенности (устаревшее, используется severity_level)
export type RiskType = 'CRITICAL' | 'POTENTIAL' | 'FORMAL';

// Трёхуровневая модель силы рисков
export type SeverityLevel = 'DEAL_BREAKER' | 'CONTROLLED_RISK' | 'MARKET_NOISE';

// Интерфейс для риска с градацией уверенности
export interface RiskItem {
  title: string;
  description?: string;
  type?: RiskType; // Устаревшее, используйте severity_level
  severity_level?: SeverityLevel; // DEAL_BREAKER | CONTROLLED_RISK | MARKET_NOISE
  confidenceLevel?: number; // 0-100, уровень уверенности в значимости риска
  source?: string; // где найден риск (преамбула, условия, расчеты и т.д.)
  canBeIgnored?: boolean; // может ли быть проигнорирован (для MARKET_NOISE рисков)
  whyImportant?: string; // почему это важно (для MCP explain)
  whenCanIgnore?: string; // когда можно игнорировать (для MCP explain)
}

// Элемент истории аудитов
export interface AuditHistoryItem {
  id: string;
  createdAt: string; // ISO-строка
  kind: 'single' | 'package' | string;
  industry: string;
  files: string[];
  summaryScore: number;
  verdict: VerdictType | string;
  // Новые поля для AI Business Advisor
  executive_summary?: string;
  deal_breakers?: string[];
  financial_analysis?: {
    margin_risk: 'High' | 'Low' | 'Medium';
    cash_gap_risk: 'Yes' | 'No';
    reasoning: string;
  };
  smart_questions?: string[];
  // Решение пользователя (Decision Layer)
  user_decision?: UserDecision;
}

export interface AuditHistoryResponse {
  items: AuditHistoryItem[];
}

// KPI управленческих решений
export interface DecisionKPI {
  totalAnalyses: number;
  decisionsMade: number;
  participateCount: number;
  participateWithConditionsCount: number;
  doNotParticipateCount: number;
  postponeCount: number;

  averageScoreParticipate?: number;
  averageScoreRejected?: number;

  highRiskParticipationCount: number;
  decisionsWithDealBreakersCount: number;
}

// --- Immutable audit trail events (глобальный уровень) ---

export type AuditEvent = {
  id: string;
  entityType: 'single_analysis' | 'package_analysis';
  entityId: string;

  eventType:
    // Аналитические события
    | 'analysis_started'
    | 'analysis_completed'
    | 'key_documents_selected'
    // Управленческие события
    | 'decision_draft_created'
    | 'decision_viewed'
    | 'decision_fixed'
    | 'decision_confirmed_by_director'
    // Рисковые события
    | 'deal_breaker_detected'
    | 'management_load_high'
    // Юридически значимые / экспорт
    | 'board_pack_exported'
    | 'compliance_exported'
    // Слой особого мнения эксперта
    | 'expert_opinion_added';

  timestamp: string; // ISO

  actor: {
    type: 'user' | 'system';
    userId?: string;
  };

  snapshot: {
    verdict?: string;
    score?: number;
    decision?: UserDecision;
    dealBreakersCount?: number;
    primaryLaw?: string;
    secondaryLaws?: string[];
    lawRegimeClassification?: 'none' | 'warning' | 'critical_conflict';
  };
};

// --- Persistent Decision Contour (single source of truth для анализа и решения) ---

export type DecisionContourLifecycleState = 'draft' | 'analysis_ready' | 'decision_recorded' | 'abandoned';

// Export types and snapshots (consequence of recorded decision)
export type ExportType = 'board_pack' | 'financial_report' | 'compliance_export';

export interface ExportSnapshot {
  exportId: string;
  contourId: string;
  exportType: ExportType;
  generatedAt: string;
  decisionRef: UserDecision;
  analysisRefHash: string;
  advisoryRefs: string[];
  format: 'pdf' | 'xlsx' | 'txt';
  contentHash: string;
}

// Snapshot of AI advisory, not a mutable chat
export interface AdvisorySnapshot {
  advisoryId: string;
  type:
    | 'risk_summary'
    | 'financial_exposure'
    | 'legal_risks'
    | 'decision_implications'
    | 'board_summary';
  generatedAt: string;
  inputHash: string;
  model: string;
  content: string;
}

// Отдельный тип событий внутри DecisionContour (чтобы не ломать AuditEvent)
export interface DecisionContourAuditEvent {
  eventId: string;
  timestamp: string;
  type:
    | 'contour_created'
    | 'analysis_completed'
    | 'advisory_generated'
    | 'decision_recorded'
    | 'decision_abandoned'
    | 'export_generated';
  actor: {
    type: 'system' | 'user';
    role?: string;
  };
  snapshotRef?: string;
}

export interface DecisionContour {
  contourId: string;
  mode: 'demo' | 'prod';
  lifecycle: {
    state: DecisionContourLifecycleState;
    createdAt: string;
    updatedAt: string;
  };
  input: {
    fileMeta?: {
      name: string;
      size: number;
      hash: string;
    };
    industry?: string;
  };
  analysis?: {
    snapshot: AnalysisResult;
    frozenAt: string;
  };
  advisory?: AdvisorySnapshot[];
  decision?: UserDecision;
  exports?: ExportSnapshot[];
  auditTrail: DecisionContourAuditEvent[];
}

// Найди интерфейс AnalysisResult и добавь specs
export interface RequirementItem {
  code?: string; // например "Опыт", "Финансы"
  title: string;
  description: string;
  level: 'normal' | 'strict' | 'blocking';
}

export interface LegalViolationItem {
  lawReference: string;
  description: string;
  type: 'specs' | 'procedure' | 'requirements' | 'other';
  severity: 'low' | 'medium' | 'high';
}

export interface ActionItemVm {
  priority?: number;
  text: string;
}

export interface TenderHubSummary {
  redFlagsTop: {
    title: string;
    severity: string;
    lawReference?: string;
    explanation?: string;
  }[];
  baseInfo: {
    nmck: string;
    procedure?: string;
    customer?: string;
    fz: string;
    region: string;
    deadlineApp: string;
    deadlineExecution?: string;
  };
  specsSummary: {
    totalPositions: number;
    highRiskCount: number;
    examples: {
      name: string;
      riskLevel: 'low' | 'medium' | 'high';
      riskReason: string;
    }[];
  };
  timeline: {
    riskLevel: 'ok' | 'tight' | 'critical';
    comment: string;
  };
  payments: {
    advance: string;
    mainPayment?: string;
    scheduleComment: string;
  };
  guarantees: {
    text: string;
    riskLevel: 'low' | 'medium' | 'high';
  };
  requirements: RequirementItem[];
  legalViolations: LegalViolationItem[];
  financial: {
    marginPercentApprox?: number;
    marginComment: string;
    lossRiskLevel: 'low' | 'medium' | 'high';
  };
  recommendation: {
    verdict: VerdictType;
    summaryShort: string;
    actions: ActionItemVm[];
  };
}

// PHASE 1: Новый формат Tender Passport
export interface TenderSource {
  document_name: string;
  page_number?: number;
  section?: string;
  quote: string;
  extraction_method: 'llm' | 'regex' | 'manual';
  confidence: number; // 0.0 - 1.0
}

export interface GovernmentData {
  customer_id?: string;
  previous_tenders_count: number;
  avg_discount_percent?: number;
  avg_competitor_count?: number;
  avg_payment_delay_days?: number;
  data_source: string;
  data_freshness: string;
  confidence_level: 'low' | 'medium' | 'high';
}

export interface TenderPassportNew {
  // ОБЯЗАТЕЛЬНЫЕ поля
  nmck_numeric: number;
  nmck_formatted: string;
  nmck_source: TenderSource;
  customer: string;
  customer_source: TenderSource;
  
  // ОПЦИОНАЛЬНЫЕ поля
  deadline?: string; // ISO date string
  deadline_source?: TenderSource;
  contract_term_months?: number;
  contract_term_source?: TenderSource;
  guarantee_amount?: number;
  guarantee_source?: TenderSource;
  penalty_percent?: number;
  penalty_source?: TenderSource;
  
  // МЕТАДАННЫЕ
  completion_percentage: number;
  warnings: string[];
  government_data?: GovernmentData;
}

export interface AnalysisResult {
  // PHASE 1: Новый Tender Passport (структурированные данные)
  tender_passport?: TenderPassportNew;
  score: number;
  winProbability?: number;
  summary: string;
  verdict: VerdictType;
  passport: TenderPassport;
  passportValidation?: PassportValidation;
  passportEvidence?: Record<string, EvidenceItem[]>;
  deepAudit: DeepAuditBlock[];
  issues: {
    title: string;
    description: string;
    severity: string;
    quote?: string; // цитата из документа
    evidence?: EvidenceItem[]; // структурированный источник
    recommendation?: string; // Рекомендация по исправлению
  }[];
  // НОВОЕ ПОЛЕ:
  specs: {
    name: string;
    qty: string;
    details: string;
  }[];
  // Красные флаги по одному документу
  redFlags?: {
    code?: string;
    title: string;
    severity: string;
    lawReference?: string;
    explanation?: string;
    quote?: string;
  }[];
  keywordMatches: KeywordMatch[];
  // Хаб-сводка для тендерного специалиста (краткий обзор)
  hub?: TenderHubSummary;
  // Контекстный триггер для демо-режима
  ui_suggestion?: {
    type: string;
    title: string;
    message: string;
    benefits?: string[];
  };
  // НОВЫЕ ПОЛЯ ДЛЯ AI BUSINESS ADVISOR
  executive_summary?: string; // Жесткое резюме в 3-5 строк (Вердикт + Главная проблема)
  financial_analysis?: {
    margin_risk: 'High' | 'Low' | 'Medium';
    cash_gap_risk: 'Yes' | 'No';
    reasoning: string;
  };
  deal_breakers?: string[]; // Список критических стоп-факторов
  smart_questions?: string[]; // 3-5 вопросов Заказчику для вскрытия подвоха
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  text: string;
  timestamp: Date;
}

export interface TenderDocument {
  id: string;
  name: string;
  size: string;
  type: 'pdf' | 'docx' | 'xls' | 'txt' | 'other';
  uploadDate: Date;
  status: 'pending' | 'scanning' | 'scanned';
}

export enum TenderStatus {
  NEW = 'NEW',
  ANALYZING = 'ANALYZING',
  READY = 'READY',
}

export interface Tender {
  id: string;
  title: string;
  customer: string;
  price: number;
  deadline: string;
  fz: string;
  status: TenderStatus;
  winRate: number;
  riskScore: number;
  description: string;
  requirements: string[];
}

// Версионирование тендерной документации (ШАГ 1.1 — Tender Versioning & Decision Actuality)
export interface TenderVersion {
  /** Идентификатор тендера (tender_number / tender_id) */
  tender_id: string;
  /** Уникальный идентификатор версии (например, hash от набора документов + timestamp) */
  version_id: string;
  /** Хеш/сигнатура набора документов (имена файлов, размер, контрольные суммы) */
  documents_hash: string;
  /** Время формирования версии (ISO-строка) */
  created_at: string;
}

export type DecisionActuality = 'CURRENT' | 'OUTDATED';

export interface DecisionRecord {
  /** Уникальный идентификатор записи решения */
  decision_id: string;
  /** Идентификатор тендера, к которому относится решение */
  tender_id: string;
  /** Идентификатор версии документов, на основании которой принято решение */
  based_on_version_id: string;
  /** Фактический статус решения (например, fixed / draft / cancelled) */
  decision_status: 'draft' | 'fixed' | 'cancelled';
  /** Актуальность решения относительно текущей версии документов */
  decision_actuality: DecisionActuality;
  /** Момент фиксации решения (если применимо) */
  decision_fixed_at?: string;
}

export type RiskAnalysis = AnalysisResult;

// Слой "Особое мнение эксперта" (Expert Opinion Layer — ШАГ 2)
export type ExpertOpinionScope = 'reputation' | 'market_practice' | 'execution_risk' | 'other';

export interface ExpertOpinion {
  /** Уникальный идентификатор мнения */
  opinion_id: string;
  /** Идентификатор тендера, к которому относится мнение */
  tender_id: string;
  /** Идентификатор автора (эксперта) */
  author_id: string;
  /** Время создания мнения (ISO-строка) */
  created_at: string;
  /** Область, к которой относится мнение (репутация, практика, исполнение и т.п.) */
  scope: ExpertOpinionScope;
  /** Текст особого мнения (строгий, без рекомендаций) */
  text: string;
  /** Флаг влияния на решение — по канону всегда false (не меняется) */
  readonly affects_decision: false;
}

// Результат анализа одного документа в составе пакета
export interface PackageDocumentAnalysis {
  filename: string;
  score: number;
  summary: string;
  verdict: VerdictType | string;
  passport: any;
  passportValidation?: PassportValidation;
  passportEvidence?: Record<string, EvidenceItem[]>;
  issues: {
    title: string;
    description?: string;
    severity?: string;
    quote?: string;
    evidence?: EvidenceItem[];
    [key: string]: any;
  }[];
  specs: {
    name: string;
    qty: string;
    details: string;
    [key: string]: any;
  }[];
  redFlags?: {
    code?: string;
    title: string;
    severity: string;
    lawReference?: string;
    explanation?: string;
    quote?: string;
  }[];
  financialSummary?: any;
  timelineSummary?: any;
  participantRequirements?: {
    licenses?: string[];
    experienceRequired?: string;
    nationalRegime?: string;
    overallBarrier?: string;
    [key: string]: any;
  };
  summaryBlocks?: {
    money?: { status: string; comment: string };
    time?: { status: string; comment: string };
    barriers?: { status: string; comment: string };
    traps?: { status: string; comment: string };
    [key: string]: any;
  };
  actions?: any[];
}

// Глобальные риски по всему пакету документов
export interface GlobalIssue {
  title: string;
  severity: string;
  description: string;
  evidence?: EvidenceItem[];
  risk_type?: RiskType; // Устаревшее, используйте severity_level
  severity_level?: SeverityLevel; // DEAL_BREAKER | CONTROLLED_RISK | MARKET_NOISE
  confidence_level?: number; // 0-100, уровень уверенности в значимости риска
  details?: any;
}

export interface PackageHubSummary {
  redFlagsTop: {
    title: string;
    severity: string;
    lawReference?: string;
    explanation?: string;
  }[];
  baseInfo: {
    nmckTotal: string;
    procedures: string[];
    customers: string[];
    fz: string;
    region: string;
  };
  specsSummary: {
    totalDocuments: number;
    totalPositions: number;
    highRiskDocs: number;
    highRiskPositions: number;
  };
  timeline: {
    riskLevel: 'ok' | 'tight' | 'critical';
    comment: string;
  };
  payments: {
    advance: string;
    scheduleComment: string;
  };
  guarantees: {
    text: string;
    riskLevel: 'low' | 'medium' | 'high';
  };
  requirements: RequirementItem[];
  legalViolations: LegalViolationItem[];
  financial: {
    marginPercentApprox?: number;
    marginComment: string;
    lossRiskLevel: 'low' | 'medium' | 'high';
  };
  recommendation: {
    verdict: VerdictType | string;
    summaryShort: string;
    actions: ActionItemVm[];
  };
}

// Ответ бэкенда для комплексного аудита пакета
export interface PackageAnalysis {
  packageId: string;
  summaryScore: number;
  verdict: VerdictType | string;
  documents: PackageDocumentAnalysis[];
  globalIssues: GlobalIssue[];
  hub?: PackageHubSummary;
}

export interface ProtocolRow {
  clause: string;
  customerVersion: string;
  supplierVersion: string;
  justification: string;
}

export interface ComplaintDraft {
  to: string;
  from: string;
  topic: string;
  violations: { point: string; argument: string; law: string }[];
  demand: string;
}

// Пресет для автозаполнения калькулятора из результатов анализа
export interface CalculatorPreset {
  source: 'single' | 'package';
  packageId?: string;
  documentName?: string;
  nmck?: string; // как в паспорте/финансовой сводке ("10 000 000 ₽")
  estimatedCost?: string; // оценочная себестоимость из financialSummary
  score?: number; // индекс безопасности 0-100
}
