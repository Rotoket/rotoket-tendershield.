/**
 * Decision Preview — ШАГ 5: Board-Ready Output
 * 
 * КЛЮЧЕВОЙ ПРИНЦИП:
 * ДИРЕКТОР ЧИТАЕТ РЕШЕНИЕ,
 * А НЕ ХОД МЫСЛЕЙ СИСТЕМЫ
 * 
 * ШАГ 5 НЕ АНАЛИЗИРУЕТ
 * ШАГ 5 НЕ ПЕРЕСЧИТЫВАЕТ
 * ШАГ 5 НЕ ДОБАВЛЯЕТ НОВЫЕ СМЫСЛЫ
 * 
 * Он ТОЛЬКО КОММУНИЦИРУЕТ РЕШЕНИЕ.
 */

import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Eye, EyeOff } from 'lucide-react';
import type { DecisionPreviewData } from '../../types/decisionPreview';
import DecisionFreshnessGuard, { type FreshnessStatus } from './DecisionFreshnessGuard';

interface DecisionPreviewStep5Props {
  previewData: DecisionPreviewData;
  /** Tender ID для Audit Trail */
  tenderId?: string;
  /** Версия анализа (для аудита) */
  analysisVersion?: string;
  /** Статус актуальности решения (ШАГ 6) */
  freshnessStatus?: FreshnessStatus;
  /** Причина устаревания (если применимо) */
  freshnessReason?: string;
  /** Decision Snapshot ID */
  decisionSnapshotId?: string;
}

const DecisionPreviewStep5: React.FC<DecisionPreviewStep5Props> = ({
  previewData,
  tenderId,
  analysisVersion,
  freshnessStatus = 'ACTUAL',
  freshnessReason,
  decisionSnapshotId,
}) => {
  const [showAuditTrail, setShowAuditTrail] = useState(false);
  const [showAllRisks, setShowAllRisks] = useState(false);

  const dp = previewData.decision_preview;

  // Форматируем решение согласно канону ШАГА 5
  const decisionLabel = dp.decision_label || 
    (dp.decision === 'PARTICIPATE' ? 'УЧАСТВОВАТЬ' :
     dp.decision === 'DO_NOT_PARTICIPATE' ? 'НЕ УЧАСТВОВАТЬ' :
     'УЧАСТВОВАТЬ ТОЛЬКО ПРИ УСЛОВИЯХ');

  // Главный риск (если есть DEAL_BREAKER — он здесь)
  const mainRisk = dp.deal_breakers.length > 0
    ? dp.deal_breakers[0].title
    : dp.controlled_risks.length > 0
    ? dp.controlled_risks[0].title
    : 'Критичных блокирующих рисков не выявлено';

  // Управленческая нагрузка (словесное объяснение, без чисел)
  const managementLoadText = dp.management_load_index?.interpretation || 
    'Управленческая нагрузка стандартная';

  // Условия изменения решения (если применимо)
  const changeConditions = dp.decision === 'PARTICIPATE_WITH_CONDITIONS' && dp.controlled_risks.length > 0
    ? 'Для изменения решения требуется уточнить условия с заказчиком'
    : null;

  // Показываем только главные риски (скрываем второстепенные)
  const visibleDealBreakers = dp.deal_breakers.slice(0, 1); // Только первый
  const visibleControlledRisks = showAllRisks 
    ? dp.controlled_risks 
    : dp.controlled_risks.slice(0, 3); // Максимум 3

  return (
    <div className="space-y-6">
      {/* 🛡️ ШАГ 6: Decision Freshness Guard (если решение устарело) */}
      {freshnessStatus !== 'ACTUAL' && (
        <DecisionFreshnessGuard
          freshnessStatus={freshnessStatus}
          freshnessReason={freshnessReason}
          decisionSnapshotId={decisionSnapshotId}
        />
      )}

      {/* 🎯 ZONE 1 — УПРАВЛЕНЧЕСКИЙ ВЫВОД (главное, всегда сверху) */}
      <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
        <h2 className="text-xl md:text-2xl font-bold text-white mb-6">
          🧭 УПРАВЛЕНЧЕСКИЙ ВЫВОД
        </h2>

        {/* РЕШЕНИЕ (самое крупное) */}
        <div className="mb-6">
          <div className="text-3xl md:text-4xl font-bold text-white mb-4">
            Решение: {decisionLabel}
          </div>

          {/* Почему это решение (2-4 причины) */}
          <div className="mb-4">
            <p className="text-sm font-semibold text-slate-300 mb-2">Почему это решение:</p>
            <ul className="text-sm text-slate-300 space-y-2 list-none ml-2">
              {dp.why.slice(0, 4).map((reason, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-slate-500 mr-2">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Ключевой риск */}
          <div className="mb-4">
            <p className="text-sm font-semibold text-slate-300 mb-2">Ключевой риск:</p>
            <p className="text-sm text-slate-200">{mainRisk}</p>
          </div>

          {/* Управленческая нагрузка (словесное объяснение, без чисел) */}
          <div className="mb-4">
            <p className="text-sm font-semibold text-slate-300 mb-2">Управленческая нагрузка:</p>
            <p className="text-sm text-slate-200">{managementLoadText}</p>
          </div>

          {/* Что нужно для изменения решения (если применимо) */}
          {changeConditions && (
            <div className="mb-4 p-3 bg-[#1a1f2e] border border-[#334155] rounded-lg">
              <p className="text-sm font-semibold text-slate-300 mb-1">Что нужно, чтобы изменить решение:</p>
              <p className="text-sm text-slate-200">{changeConditions}</p>
            </div>
          )}
        </div>
      </div>

      {/* 🟥 ZONE 2 — DEAL BREAKERS (если есть, визуально выделены) */}
      {visibleDealBreakers.length > 0 && (
        <div className="bg-[#1a0f0f] border border-[#ff4444] rounded-2xl p-6">
          <h3 className="text-lg font-bold text-[#ff4444] mb-4">
            КРИТИЧЕСКИЙ СТОП-ФАКТОР
          </h3>
          {visibleDealBreakers.map((db) => (
            <div key={db.id} className="mb-4">
              <p className="text-sm font-semibold text-white mb-2">{db.title}</p>
              {db.impact && (
                <p className="text-sm text-slate-300 mb-2">{db.impact}</p>
              )}
              {db.document_name && (
                <p className="text-xs text-slate-500">
                  Источник: {db.document_name}
                  {db.section && `, ${db.section}`}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 🟨 ZONE 3 — УПРАВЛЯЕМЫЕ РИСКИ (скрыты по умолчанию, показываются по запросу) */}
      {dp.controlled_risks.length > 0 && (
        <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-white">
              Управляемые риски ({dp.controlled_risks.length})
            </h3>
            {dp.controlled_risks.length > 3 && (
              <button
                type="button"
                onClick={() => setShowAllRisks(!showAllRisks)}
                className="text-xs text-slate-400 hover:text-slate-300 flex items-center gap-1"
              >
                {showAllRisks ? (
                  <>
                    <ChevronUp size={14} />
                    Скрыть детали
                  </>
                ) : (
                  <>
                    <ChevronDown size={14} />
                    Показать все
                  </>
                )}
              </button>
            )}
          </div>
          <div className="space-y-3">
            {visibleControlledRisks.map((risk) => (
              <div key={risk.id} className="p-3 bg-[#1a1f2e] border border-[#334155] rounded-lg">
                <p className="text-sm font-semibold text-white mb-1">{risk.title}</p>
                {risk.control && (
                  <p className="text-xs text-slate-400">{risk.control}</p>
                )}
                {risk.document_name && (
                  <p className="text-xs text-slate-500 mt-1">
                    Источник: {risk.document_name}
                    {risk.section && `, ${risk.section}`}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 🔒 ZONE 4 — AUDIT TRAIL (скрыт по умолчанию, доступен по запросу) */}
      <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6">
        <button
          type="button"
          onClick={() => setShowAuditTrail(!showAuditTrail)}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 w-full"
        >
          {showAuditTrail ? (
            <>
              <EyeOff size={16} />
              Скрыть Audit Trail
            </>
          ) : (
            <>
              <Eye size={16} />
              Показать Audit Trail
            </>
          )}
        </button>
        {showAuditTrail && (
          <div className="mt-4 space-y-2 text-xs text-slate-500">
            <p>Decision Graph ID: {tenderId || 'N/A'}</p>
            {analysisVersion && <p>Версия анализа: {analysisVersion}</p>}
            <p>DEAL_BREAKER: {dp.deal_breakers.length} шт.</p>
            <p>CONTROLLED_RISK: {dp.controlled_risks.length} шт.</p>
            <p>MARKET_NOISE: {dp.summary.market_noise_count} шт. (скрыто)</p>
            <p className="text-[10px] text-slate-600 mt-3">
              Audit Trail содержит ссылки: Decision → Risk → Evidence
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecisionPreviewStep5;

