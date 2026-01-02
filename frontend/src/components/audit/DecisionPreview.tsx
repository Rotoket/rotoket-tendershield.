import React, { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, TrendingDown, FileText } from 'lucide-react';
import type { AnalysisResult } from '../../types';
import { logEvent } from '../../utils/logger';
import { getExpertOpinions, addExpertOpinion } from '../../utils/expertOpinionStorage';
import { appendAuditEvent } from '../../utils/auditTrail';
import { transformToDecisionPreview } from '../../utils/decisionPreviewTransformer';
import type { DecisionPreviewData } from '../../types/decisionPreview';
import DecisionPreviewStep5 from './DecisionPreviewStep5';
import KillSwitchBanner from '../KillSwitchBanner';
import TenderPassportSection from './TenderPassportSection';

interface DecisionPreviewProps {
  result: AnalysisResult;
  onGoToDetails?: () => void;
  onGoToDecision?: () => void;
  /** Количество документов в анализе (для пакетного анализа) */
  documentsCount?: number;
  /** Уже зафиксированное решение (для read-only режима) */
  fixedDecision?: {
    decision: string;
    timestamp: string;
    comment?: string;
    user?: string;
  };
  /** Версия анализа (для аудита) */
  analysisVersion?: string;
  /** Tender ID для Decision Log */
  tenderId?: string;
}

const DecisionPreview: React.FC<DecisionPreviewProps> = ({
  result,
  onGoToDetails,
  onGoToDecision,
  documentsCount = 1,
  fixedDecision,
  analysisVersion,
  tenderId,
}) => {
  if (!result) return null;

  const hasFixedDecision = !!fixedDecision;
  const [expandedRisks, setExpandedRisks] = useState<Set<string>>(new Set());
  const [showMarketNoise, setShowMarketNoise] = useState(false);
  const [showDirectorExplanation, setShowDirectorExplanation] = useState(false);
  const [expertOpinionText, setExpertOpinionText] = useState('');
  const [expertOpinionScope, setExpertOpinionScope] = useState<'reputation' | 'market_practice' | 'execution_risk' | 'other'>('execution_risk');
  const [expertOpinions, setExpertOpinions] = useState(() => (tenderId ? getExpertOpinions(tenderId) : []));
  const [transformError, setTransformError] = useState<string | null>(null);

  // Трансформируем AnalysisResult в каноническую модель DecisionPreviewData
  const previewData: DecisionPreviewData | null = useMemo(() => {
    try {
      return transformToDecisionPreview(result);
    } catch (error) {
      console.error('[DecisionPreview] Ошибка трансформации данных:', error);
      setTransformError(error instanceof Error ? error.message : 'Ошибка обработки данных');
      return null;
    }
  }, [result]);

  // Если трансформация не удалась, показываем ошибку
  if (!previewData) {
    return (
      <div className="bg-[#0f1419] border border-[#ff4444] rounded-2xl p-6 mb-6">
        <p className="text-[#ff4444] text-sm">
          Ошибка обработки данных анализа. Пожалуйста, попробуйте обновить страницу.
        </p>
        {transformError && (
          <p className="text-slate-500 text-xs mt-2">{transformError}</p>
        )}
      </div>
    );
  }

  const dp = previewData.decision_preview;

  // Проверяем, есть ли отформатированный Decision Preview от ШАГА 5
  const step5Preview = (result as any).decision_preview_step5;
  const decisionGraph = (result as any).decision_graph;
  // ШАГ 6: Проверяем статус актуальности решения
  const auditTrail = (result as any).audit_trail;
  const freshnessStatus = auditTrail?.freshness_status || 'ACTUAL';
  const freshnessReason = auditTrail?.freshness_reason;
  const decisionSnapshotId = auditTrail?.decision_snapshot_id;

  useEffect(() => {
    logEvent('DecisionPreview', 'verdict_viewed', 'info', {
      decision: dp.decision,
      decision_confidence: dp.decision_confidence,
      dealBreakersCount: dp.summary.deal_breakers_found ? 1 : 0,
      controlledRisksCount: dp.summary.controlled_risks_count,
      documentsCount,
      hasFixedDecision,
    });
  }, [dp.decision, dp.decision_confidence, dp.summary, documentsCount, hasFixedDecision]);

  // Форматирование суммы в рубли (для отображения)
  const formatRuble = (amount: number): string => {
    if (amount >= 1_000_000) {
      return `${(amount / 1_000_000).toFixed(1).replace('.', ',')} млн ₽`;
    } else if (amount >= 1_000) {
      return `${(amount / 1_000).toFixed(0)} тыс ₽`;
    } else {
      return `${amount.toFixed(0)} ₽`;
    }
  };

  // Формирование списка финансовой экспозиции для отображения
  const financialExposureItems = useMemo(() => {
    const items: string[] = [];
    const exp = dp.financial_exposure;

    if (exp.potential_extra_costs_rub) {
      items.push(`Потенциальные доп. затраты: до ~${formatRuble(exp.potential_extra_costs_rub)}`);
    }
    if (exp.funds_blocking_percent) {
      items.push(`Блокировка средств: до ${exp.funds_blocking_percent} суммы контракта`);
    }

    if (items.length === 0) {
      return [
        'Финансовые параметры в документации не зафиксированы',
        'Экспозиция требует уточнения до подачи заявки',
      ];
    }

    return items;
  }, [dp.financial_exposure]);

  // Оценка статуса финансовой определённости (для верхнего резюме)
  const financialCertaintyLabel = useMemo(() => {
    const exp = dp.financial_exposure;
    const hasAnyExposure =
      !!exp.potential_extra_costs_rub ||
      !!exp.funds_blocking_percent ||
      (exp.comment && exp.comment.trim().length > 0);

    if (!hasAnyExposure) {
      return 'Финансовая определённость: ❌ недостаточная (ключевые финансовые параметры не зафиксированы явно в документах)';
    }

    // Без усложнения логики считаем, что при наличии данных возможно уточнение
    return 'Финансовая определённость: ⚠ частичная (требует подтверждения до принятия обязательств)';
  }, [dp.financial_exposure]);

  const handleAddExpertOpinion = () => {
    if (!tenderId) return;
    const text = expertOpinionText.trim();
    if (!text) return;
    const opinion = addExpertOpinion({
      tenderId,
      authorId: 'expert', // в проде берётся из user context
      scope: expertOpinionScope,
      text,
    });
    setExpertOpinions(prev => [...prev, opinion]);
    setExpertOpinionText('');

    appendAuditEvent({
      id: `${Date.now()}_expert_opinion`,
      entityType: 'single_analysis',
      entityId: tenderId,
      eventType: 'expert_opinion_added',
      timestamp: new Date().toISOString(),
      actor: { type: 'user' },
      snapshot: {},
    });

    logEvent('DecisionPreview', 'expert_opinion_added', 'info', {
      tender_id: tenderId,
      scope: expertOpinionScope,
    });
  };

  // Подсчёт рисков до фильтрации evidence (для UI-гварда)
  const totalControlledRisksDeclared = dp.summary.controlled_risks_count;
  const totalControlledRisksShown = dp.controlled_risks.length;
  const hasFilteredRisksWithoutEvidence =
    totalControlledRisksDeclared > totalControlledRisksShown;

  const toggleRisk = (riskId: string) => {
    const newExpanded = new Set(expandedRisks);
    if (newExpanded.has(riskId)) {
      newExpanded.delete(riskId);
    } else {
      newExpanded.add(riskId);
    }
    setExpandedRisks(newExpanded);
  };

  // ШАГ 13: Получаем статус Kill Switch из результата
  const killSwitchStatus = (result as any).kill_switch_status;
  const safeModeResponse = (result as any).safe_mode_response;

  // Если есть Step5 preview, используем его (приоритет)
  if (step5Preview && previewData) {
    return (
      <div className="space-y-6">
        {/* ШАГ 13: Kill Switch Banner */}
        {(killSwitchStatus || safeModeResponse) && (
          <KillSwitchBanner
            status={killSwitchStatus || (safeModeResponse ? {
              mode: safeModeResponse.mode as 'NORMAL' | 'SAFE' | 'LOCKDOWN',
              is_active: safeModeResponse.mode !== 'NORMAL',
              last_activation: safeModeResponse.last_activation,
            } : null)}
          />
        )}
        <DecisionPreviewStep5
          previewData={previewData}
          tenderId={tenderId}
          analysisVersion={analysisVersion}
          freshnessStatus={freshnessStatus}
          freshnessReason={freshnessReason}
          decisionSnapshotId={decisionSnapshotId}
        />
      </div>
    );
  }

  // PHASE 1: Проверяем наличие нового Tender Passport
  const tenderPassport = (result as any).tender_passport;

  // Fallback на оригинальный DecisionPreview (если Step5 недоступен)
  return (
    <div className="space-y-6">
      {/* ШАГ 13: Kill Switch Banner */}
      {(killSwitchStatus || safeModeResponse) && (
        <KillSwitchBanner
          status={killSwitchStatus || (safeModeResponse ? {
            mode: safeModeResponse.mode as 'NORMAL' | 'SAFE' | 'LOCKDOWN',
            is_active: safeModeResponse.mode !== 'NORMAL',
            last_activation: safeModeResponse.last_activation,
          } : null)}
        />
      )}
      
      {/* PHASE 1: Tender Passport Section (если доступен) */}
      {tenderPassport && tenderPassport.nmck_numeric && tenderPassport.customer && (
        <TenderPassportSection passport={tenderPassport} />
      )}
      
      {/* 🟥 ZONE 1 — DECISION HEADER */}
      <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
        {/* Заголовок */}
        <h2 className="text-xl md:text-2xl font-bold text-white mb-4">
          УПРАВЛЕНЧЕСКОЕ РЕШЕНИЕ ПО ТЕНДЕРУ
        </h2>

        {/* Контур сделки (Deal Snapshot) — факты об объекте анализа */}
        {(() => {
          const hubBase = (result as any).hub?.baseInfo;
          const passport = (result as any).passport || {};

          const customer = hubBase?.customer || passport.customer;
          const nmckRaw: string | undefined = hubBase?.nmck || passport.nmck;
          const law = hubBase?.fz || passport.fz;
          const region = hubBase?.region || passport.region;
          const deadlineApp = hubBase?.deadlineApp || passport.deadlineApp;
          const deadlineExec = hubBase?.deadlineExecution || passport.deadlineExecution;

          // Предмет контракта: используем первую строку summary как фактическое описание объекта
          const subjectLine = (result.summary || '')
            .split('\n')
            .map((s) => s.trim())
            .filter(Boolean)[0];

          // Цена / НМЦК — три статуса
          let nmckLine = 'Не зафиксирована в документах';
          if (nmckRaw && nmckRaw.trim().length > 0) {
            const lower = nmckRaw.toLowerCase();
            if (lower.includes('до ') || lower.includes('максим')) {
              nmckLine = `Диапазон / НМЦК: ${nmckRaw}`;
            } else {
              nmckLine = `Определена: ${nmckRaw}`;
            }
          }

          return (
            <div className="mb-4 text-xs md:text-sm text-slate-300">
              <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 mb-2">
                Контур сделки (Deal Snapshot)
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1">
                <p>
                  <span className="text-slate-400">Предмет контракта:&nbsp;</span>
                  <span className="text-slate-200">
                    {subjectLine || 'Не зафиксирован в кратком описании документации'}
                  </span>
                </p>
                <p>
                  <span className="text-slate-400">Заказчик / организатор:&nbsp;</span>
                  <span className="text-slate-200">
                    {customer || 'Не зафиксирован в паспорте документации'}
                  </span>
                </p>
                <p>
                  <span className="text-slate-400">Цена контракта / НМЦК:&nbsp;</span>
                  <span className="text-slate-200">{nmckLine}</span>
                </p>
                <p>
                  <span className="text-slate-400">Правовой режим закупки:&nbsp;</span>
                  <span className="text-slate-200">
                    {law || 'Не зафиксирован в документации'}
                  </span>
                </p>
                <p className="md:col-span-2">
                  <span className="text-slate-400">Состав пакета в анализе:&nbsp;</span>
                  <span className="text-slate-200">
                    {documentsCount > 1
                      ? `В анализ включено ${documentsCount} ключевых документа.`
                      : 'В анализ включён 1 ключевой документ.'}
                  </span>
                </p>
              </div>
            </div>
          );
        })()}

        {/* РЕШЕНИЕ (самое крупное, спокойный фон) */}
        <div className="border-b border-[#1f2937] pb-4 mb-4">
          <div className="text-3xl md:text-4xl font-bold text-white mb-3">
            РЕШЕНИЕ: {dp.decision_label}
          </div>

          {/* Краткое резюме по стоп-факторам, рискам и финансам */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs md:text-sm text-slate-300 mb-3">
            <p>
              Критических стоп-факторов:{' '}
              {dp.summary.deal_breakers_found ? '✅ выявлены (см. ниже)' : '❌ не выявлено'}
            </p>
            <p>Управляемые риски: {dp.summary.controlled_risks_count} шт. (устранимы до подачи заявки).</p>
            <p>{financialCertaintyLabel}</p>
          </div>

          {/* Почему (2 bullets) */}
          <div className="mt-3">
            <p className="text-sm font-semibold text-slate-300 mb-2">Почему:</p>
            <ul className="text-sm text-slate-300 space-y-1 list-none ml-2">
              {dp.why.map((reason, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-slate-500 mr-2">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Основание по количеству документов */}
          {documentsCount > 0 && (
            <p className="text-xs text-slate-500 mt-3">
              Решение сформировано на основе анализа {documentsCount} ключевых документа(ов).
            </p>
          )}
        </div>

        {/* ФИНАНСОВАЯ ЭКСПОЗИЦИЯ */}
        <div className="mb-4">
          <p className="text-sm font-semibold text-white mb-2">Финансовая экспозиция:</p>
          <ul className="text-sm text-slate-300 space-y-1 list-none ml-2">
            {financialExposureItems.map((item, idx) => (
              <li key={idx} className="flex items-start">
                <span className="text-slate-500 mr-2">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* ИНДЕКС УПРАВЛЕНЧЕСКОЙ НАГРУЗКИ */}
        <div>
          <p className="text-sm font-semibold text-white mb-1">
            ИНДЕКС УПРАВЛЕНЧЕСКОЙ НАГРУЗКИ: {dp.management_load_index.value} / {dp.management_load_index.max}
          </p>
          <p className="text-xs text-slate-400">{dp.management_load_index.interpretation}</p>
          <p className="text-[11px] text-slate-500 mt-1">
            Индекс агрегирует четыре фактора: документальные противоречия, финансовую неопределённость,
            юридико-процедурную сложность и объём ручного управленческого контроля.
          </p>
        </div>
      </div>

      {/* 🟧 ZONE 2 — STOP VIEW (1 строка, бинарный) */}
      <div className={`border rounded-xl p-4 ${dp.summary.deal_breakers_found ? 'bg-[#ff4444]/10 border-[#ff4444]/30' : 'bg-[#00e648]/10 border-[#00e648]/30'}`}>
        {dp.summary.deal_breakers_found ? (
          <>
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="text-[#ff4444]" size={18} />
              <span className="text-sm font-bold text-[#ff4444]">
                КРИТИЧЕСКИЙ СТОП-ФАКТОР: {dp.deal_breakers[0]?.title || 'Обнаружен критический фактор'}
              </span>
            </div>
            <p className="text-xs text-slate-400 ml-7">
              Участие приведёт к отклонению заявки.
            </p>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="text-[#00e648]" size={18} />
              <span className="text-sm font-bold text-[#00e648]">🟢 КРИТИЧЕСКИЕ СТОП-ФАКТОРЫ: НЕ ОБНАРУЖЕНЫ</span>
            </div>
            <p className="text-xs text-slate-400 ml-7">
              Формальных оснований для отказа от участия не выявлено.
            </p>
          </>
        )}
      </div>

      {/* 🟨 ZONE 3 — KEY RISKS (accordion, только важное) */}
      {(dp.controlled_risks.length > 0 || hasFilteredRisksWithoutEvidence) && (
        <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">
            КЛЮЧЕВЫЕ РИСКИ, ВЛИЯЮЩИЕ НА РЕШЕНИЕ ({dp.controlled_risks.length})
          </h3>

          {hasFilteredRisksWithoutEvidence && (
            <p className="text-[11px] text-slate-500 mb-3">
              Некоторые выявленные риски не имеют документального основания (цитат и ссылок на пункты)
              и исключены из управленческого вывода.
            </p>
          )}

          <div className="space-y-3">
            {dp.controlled_risks.map((risk) => {
              const isExpanded = expandedRisks.has(risk.id);
              return (
                <div
                  key={risk.id}
                  className="bg-[#020617] border border-[#1f2937] rounded-xl overflow-hidden"
                >
                  <button
                    type="button"
                    onClick={() => toggleRisk(risk.id)}
                    className="w-full p-4 flex items-center justify-between hover:bg-[#1a1f2e] transition-colors"
                  >
                    <div className="flex items-start gap-3 flex-1 text-left">
                      <div className="mt-0.5">
                        <span className="text-xs font-bold text-[#f59e0b] uppercase tracking-wide">КОНТРОЛИРУЕМЫЙ РИСК</span>
                        <p className="text-sm font-semibold text-white mt-1">{risk.title}</p>
                        {risk.evidence && risk.evidence.length > 0 && (
                          <p className="text-[11px] text-slate-400 mt-1">
                            Источник: {risk.evidence[0].document_name || 'Документы тендера'}
                            {risk.evidence[0].section_ref ? ` — ${risk.evidence[0].section_ref}` : ''}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="ml-4 flex-shrink-0">
                      <span className={`text-slate-400 text-xs transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                        ▼
                      </span>
                    </div>
                  </button>

                  {isExpanded && (
                    <div className="px-4 pb-4 space-y-3 border-t border-[#1f2937] pt-4">
                      <div>
                        <span className="text-xs font-semibold text-white">Управленческое последствие:</span>
                        <p className="text-xs text-slate-300 mt-1 ml-2">
                          — {risk.impact}
                        </p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-white">Как контролируется:</span>
                        <p className="text-xs text-slate-300 mt-1 ml-2">
                          — {risk.control}
                        </p>
                      </div>
                      {risk.evidence && risk.evidence.length > 0 && (
                        <div>
                          <span className="text-xs font-semibold text-white">Источник риска:</span>
                          <div className="text-xs text-slate-300 mt-1 ml-2 space-y-2">
                            {risk.evidence.map((ev, idxEv) => (
                              <div key={idxEv} className="space-y-0.5">
                                <p>
                                  Документ: {ev.document_name || 'Документ не указан'}
                                  {ev.section_ref ? ` — ${ev.section_ref}` : ''}
                                </p>
                                <p className="text-[11px] text-slate-400">
                                  Фрагмент документа: «{ev.quote}»
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* MARKET_NOISE (свернута по умолчанию) */}
          {dp.summary.market_noise_count > 0 && (
            <div className="mt-4 pt-4 border-t border-[#1f2937]">
              <button
                type="button"
                onClick={() => setShowMarketNoise(!showMarketNoise)}
                className="w-full flex items-center justify-between text-sm text-slate-400 hover:text-slate-300 transition-colors"
              >
                <span>
                  РЫНОЧНЫЕ ФАКТОРЫ (НЕ КРИТИЧНЫЕ): формальные риски ({dp.summary.market_noise_count})
                </span>
                <span className={`transition-transform ${showMarketNoise ? 'rotate-180' : ''}`}>▼</span>
              </button>
              {showMarketNoise && (
                <div className="mt-2 text-xs text-slate-500 pl-4">
                  Не влияют на управленческое решение, приведены для полноты анализа.
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 🟦 ZONE 4 — SCENARIOS (2 карточки, без философии) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#0f1419] border border-[#2a3441] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="text-[#00e648]" size={16} />
            <h4 className="text-sm font-bold text-white">ЛУЧШИЙ СЦЕНАРИЙ</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{dp.scenarios.best}</p>
        </div>
        <div className="bg-[#0f1419] border border-[#2a3441] rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="text-[#ff4444]" size={16} />
            <h4 className="text-sm font-bold text-white">ХУДШИЙ СЦЕНАРИЙ</h4>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">{dp.scenarios.worst}</p>
        </div>
      </div>

      {/* 🟪 ZONE 4b — Аналитическое пояснение по запросу директора */}
      {dp.director_explanation && (
        <div className="bg-[#0f1419] border border-dashed border-[#334155] rounded-xl p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-1">
                Аналитическое пояснение (по запросу директора)
              </p>
              <p className="text-[11px] text-slate-500">
                Это пояснение не является управленческим решением и не подменяет ответственность директора.
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                const next = !showDirectorExplanation;
                setShowDirectorExplanation(next);
                if (next) {
                  logEvent('DecisionPreview', 'analytical_view_requested', 'info', {
                    eventType: 'ANALYTICAL_VIEW_REQUESTED',
                    tenderId,
                  });
                }
              }}
              className="px-3 py-1.5 text-xs rounded border border-[#475569] text-slate-200 hover:bg-[#111827] transition-colors"
            >
              {showDirectorExplanation ? 'Скрыть пояснение' : 'Показать аналитическое пояснение'}
            </button>
          </div>
          {showDirectorExplanation && (
            <div className="mt-3 text-xs text-slate-200 whitespace-pre-line leading-relaxed">
              {dp.director_explanation}
            </div>
          )}
        </div>
      )}

      {/* 🟫 ZONE 4c — Особое мнение эксперта (не влияет на управленческое решение) */}
      {tenderId && (
        <div className="bg-[#020617] border border-dashed border-[#374151] rounded-xl p-4 space-y-3">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
            <div>
              <p className="text-xs font-semibold text-slate-400">
                Особое мнение эксперта
              </p>
              <p className="text-[11px] text-slate-500">
                Особое мнение эксперта не влияет на управленческое решение и не меняет Индекс управленческой нагрузки.
              </p>
            </div>
          </div>

          {expertOpinions.length > 0 && (
            <div className="space-y-2 mt-2">
              {expertOpinions.map(op => (
                <div key={op.opinion_id} className="border border-[#1f2937] rounded-lg p-3 bg-[#020617]">
                  <p className="text-[11px] text-slate-400 mb-1">
                    Область: {op.scope === 'reputation'
                      ? 'Репутация'
                      : op.scope === 'market_practice'
                      ? 'Рыночная практика'
                      : op.scope === 'execution_risk'
                      ? 'Риски исполнения'
                      : 'Иное'}
                  </p>
                  <p className="text-xs text-slate-200 whitespace-pre-line">
                    {op.text}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-1">
                    Зафиксировано: {new Date(op.created_at).toLocaleString('ru-RU')}
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Форма ввода мнения эксперта (однократная фиксация, без редактирования) */}
          <div className="mt-2 space-y-2">
            <div className="flex flex-wrap gap-2 items-center">
              <label className="text-[11px] text-slate-400">Область:</label>
              <select
                className="bg-[#020617] border border-[#374151] text-xs text-slate-200 rounded px-2 py-1"
                value={expertOpinionScope}
                onChange={(e) => setExpertOpinionScope(e.target.value as any)}
              >
                <option value="execution_risk">Риски исполнения</option>
                <option value="reputation">Репутация</option>
                <option value="market_practice">Рыночная практика</option>
                <option value="other">Иное</option>
              </select>
            </div>
            <textarea
              className="w-full bg-[#020617] border border-[#374151] rounded-lg text-xs text-slate-200 px-3 py-2 placeholder-slate-500 focus:outline-none focus:border-[#38bdf8] resize-none"
              rows={3}
              placeholder="Кратко зафиксируйте наблюдение, не вытекающее напрямую из документов (без рекомендаций и оценочных суждений)…"
              value={expertOpinionText}
              onChange={(e) => setExpertOpinionText(e.target.value)}
            />
            <button
              type="button"
              onClick={handleAddExpertOpinion}
              disabled={!expertOpinionText.trim()}
              className="px-4 py-2 rounded-lg bg-[#111827] text-xs text-slate-200 border border-[#374151] hover:bg-[#1f2937] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              Зафиксировать особое мнение эксперта
            </button>
          </div>
        </div>
      )}

      {/* 🟩 ZONE 5 — FIX DECISION (финал, ритуал) */}
      {!hasFixedDecision && onGoToDecision && (
        <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-2">ФИКСАЦИЯ УПРАВЛЕНЧЕСКОГО РЕШЕНИЯ</h3>
          <p className="text-sm text-slate-400 mb-4">
            Система не принимает решение.<br />
            Ниже — фиксация выбора директора.
          </p>
          
          <div className="flex flex-col md:flex-row gap-3">
            {dp.decision_actions.allow_participate && (
              <button
                type="button"
                onClick={() => {
                  logEvent('DecisionPreview', 'proceed_to_decision_participate', 'info', {
                    decision: dp.decision,
                    requires_comment: dp.decision_actions.require_comment,
                    tender_id: tenderId,
                  });
                  onGoToDecision();
                }}
                className="flex-1 px-6 py-3 rounded-lg bg-[#00d4ff] text-[#0f1419] font-bold text-sm hover:bg-[#00b8e6] transition-colors"
              >
                Зафиксировать участие
              </button>
            )}
            {dp.decision_actions.allow_decline && (
              <button
                type="button"
                onClick={() => {
                  logEvent('DecisionPreview', 'proceed_to_decision_refuse', 'info', {
                    decision: dp.decision,
                    requires_comment: dp.decision_actions.require_comment,
                    tender_id: tenderId,
                  });
                  onGoToDecision();
                }}
                className="flex-1 px-6 py-3 rounded-lg bg-[#1a1f2e] border border-[#2a3441] text-slate-300 font-bold text-sm hover:border-[#ff4444] hover:text-[#ff4444] transition-colors"
              >
                Зафиксировать отказ
              </button>
            )}
          </div>
          
          <p className="text-xs text-slate-500 text-center mt-4">
            Решение сохраняется в журнале управленческой ответственности.
          </p>
        </div>
      )}

      {/* Информация о зафиксированном решении */}
      {hasFixedDecision && (
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-lg p-4">
          <p className="text-sm text-slate-400 mb-2">
            <strong className="text-slate-300">Решение зафиксировано и не может быть изменено</strong>
          </p>
          <div className="text-xs text-slate-500 space-y-1">
            {fixedDecision.user && (
              <p>Принял: {fixedDecision.user}</p>
            )}
            {fixedDecision.timestamp && (
              <p>
                Дата: {new Date(fixedDecision.timestamp).toLocaleString('ru-RU', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            )}
            {analysisVersion && (
              <p>Версия анализа: {analysisVersion}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DecisionPreview;
