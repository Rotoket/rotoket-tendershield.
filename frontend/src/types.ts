
export enum AppView {
  LOGIN = 'LOGIN',
  ANALYZER = 'ANALYZER', // Анализ одного документа
  AUDIT = 'AUDIT', // Комплексный аудит пакета документов
  GENERATOR = 'GENERATOR', // Генератор документов
  KNOWLEDGE = 'KNOWLEDGE', // База знаний
  HISTORY = 'HISTORY',
  CALCULATOR = 'CALCULATOR', // Калькулятор маржинальности
  PROFILE = 'PROFILE', // Личный кабинет
  ANALYTICS = 'ANALYTICS', // Аналитика и метрики
  HELP = 'HELP', // Справочный центр / помощь
}

export interface User {
  id: string;
  name: string;
  company: string;
  tariff: 'Start' | 'Pro' | 'Enterprise';
  email?: string;
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

export interface TenderPassport {
  // Основное
  nmck: string; // "10 000 000 ₽"
  fz: string; // "44-ФЗ"

  // Деньги
  advance: string; // "30%" or "Нет"
  paymentTerms: string; // "7 раб. дней"
  secureBid: string; // "50 000 ₽ (0.5%)"
  secureContract: string; // "1 000 000 ₽ (10%)"
  secureWarranty: string; // "Нет" or "5%"

  // Сроки
  deadlineApp: string; // Дата подачи
  deadlineExecution: string; // Дата исполнения

  // Место
  region: string;
}

export interface KeywordMatch {
  keyword: string;
  context: string;
  count: number;
}

export type VerdictType = 'PARTICIPATE' | 'CAUTION' | 'STOP';

// Элемент истории аудитов
export interface AuditHistoryItem {
  id: string;
  createdAt: string; // ISO-строка
  kind: 'single' | 'package' | string;
  industry: string;
  files: string[];
  summaryScore: number;
  verdict: VerdictType | string;
}

export interface AuditHistoryResponse {
  items: AuditHistoryItem[];
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

export interface AnalysisResult {
  score: number;
  winProbability?: number;
  summary: string;
  verdict: VerdictType;
  passport: TenderPassport;
  deepAudit: DeepAuditBlock[];
  issues: {
    title: string;
    description: string;
    severity: string;
    quote?: string; // Добавили цитату
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
  // Стоп-факторы (DEAL BREAKERS)
  dealBreakers?: {
    title: string;
    quote?: string;
    essence: string;
    status: string;
    lawReference?: string | null;
    action?: {
      type: string;
      buttonLabel: string;
      justification: string;
    };
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
  // Структурированные ответы на 25 вопросов тендерного анализа
  structuredAnswers?: {
    customer?: string;
    subject?: string;
    nmck?: string;
    applicationDeadline?: string;
    executionDeadline?: string;
    participantRequirements?: string;
    securityAmounts?: string;
    paymentTerms?: string;
    evaluationCriteria?: string;
    contradictions?: string;
    penalties?: string;
    guarantees?: string;
    additionalRequirements?: string;
    tenderRisks?: string;
    documentationRequirements?: string;
    financialRequirements?: string;
    confidentiality?: string;
    customerHistory?: string;
    subcontractingLimits?: string;
    conflictsOfInterest?: string;
    discriminationSigns?: string;
    terminationConditions?: string;
    competitionLevel?: string;
    insuranceRequirements?: string;
    additionalRisks?: string;
  };
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

export type RiskAnalysis = AnalysisResult;

// Результат анализа одного документа в составе пакета
export interface PackageDocumentAnalysis {
  filename: string;
  score: number;
  summary: string;
  verdict: VerdictType | string;
  passport: any;
  issues: {
    title: string;
    description?: string;
    severity?: string;
    quote?: string;
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
  financialSummary?: {
    nmck?: string;
    estimatedCost?: string;
    marginComment?: string;
    advance?: string;
    bidSecurity?: string;
    contractSecurity?: string;
    paymentTerms?: string;
    penaltyRiskRubles?: string;
    workingCapitalNeeded?: string;
    guaranteeAmount?: string;
    [key: string]: any;
  };
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
  // Структурированные ответы на 25 вопросов тендерного анализа
  structuredAnswers?: {
    customer?: string;
    subject?: string;
    nmck?: string;
    applicationDeadline?: string;
    executionDeadline?: string;
    participantRequirements?: string;
    securityAmounts?: string;
    paymentTerms?: string;
    evaluationCriteria?: string;
    contradictions?: string;
    penalties?: string;
    guarantees?: string;
    additionalRequirements?: string;
    tenderRisks?: string;
    documentationRequirements?: string;
    financialRequirements?: string;
    confidentiality?: string;
    customerHistory?: string;
    subcontractingLimits?: string;
    conflictsOfInterest?: string;
    discriminationSigns?: string;
    terminationConditions?: string;
    competitionLevel?: string;
    insuranceRequirements?: string;
    additionalRisks?: string;
  };
}

// Глобальные риски по всему пакету документов
export interface GlobalIssue {
  title: string;
  severity: string;
  description: string;
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
