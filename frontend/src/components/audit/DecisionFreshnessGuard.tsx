/**
 * Decision Freshness Guard — ШАГ 6: UI-компонент для отображения статуса актуальности
 * 
 * Если решение STALE или INVALIDATED:
 * - UI ОБЯЗАН показать предупреждение
 * - решение НЕ МОЖЕТ выглядеть актуальным
 * - любые PDF/выгрузки МАРКИРУЮТСЯ
 */

import React from 'react';
import { AlertTriangle, XCircle, CheckCircle, Clock } from 'lucide-react';

export type FreshnessStatus = 'ACTUAL' | 'STALE' | 'INVALIDATED';

interface DecisionFreshnessGuardProps {
  freshnessStatus: FreshnessStatus;
  freshnessReason?: string;
  decisionSnapshotId?: string;
  /** Показывать ли детальную информацию (для юристов/аудиторов) */
  showDetails?: boolean;
}

const DecisionFreshnessGuard: React.FC<DecisionFreshnessGuardProps> = ({
  freshnessStatus,
  freshnessReason,
  decisionSnapshotId,
  showDetails = false,
}) => {
  if (freshnessStatus === 'ACTUAL') {
    // Актуальное решение — показываем только если запрошены детали
    if (showDetails) {
      return (
        <div className="bg-[#0f1419] border border-[#00e648]/30 rounded-xl p-3 mb-4">
          <div className="flex items-center gap-2 text-sm">
            <CheckCircle className="text-[#00e648]" size={16} />
            <span className="text-[#00e648] font-semibold">Решение актуально</span>
            {decisionSnapshotId && (
              <span className="text-xs text-slate-500 ml-auto">ID: {decisionSnapshotId}</span>
            )}
          </div>
        </div>
      );
    }
    return null; // Не показываем для актуальных решений по умолчанию
  }

  // Устаревшее или инвалидированное решение — ОБЯЗАТЕЛЬНО показываем
  const isInvalidated = freshnessStatus === 'INVALIDATED';
  const Icon = isInvalidated ? XCircle : AlertTriangle;
  const bgColor = isInvalidated ? 'bg-[#1a0f0f]' : 'bg-[#1a1a0f]';
  const borderColor = isInvalidated ? 'border-[#ff4444]' : 'border-[#ffaa00]';
  const textColor = isInvalidated ? 'text-[#ff4444]' : 'text-[#ffaa00]';
  const title = isInvalidated ? 'РЕШЕНИЕ ИНВАЛИДИРОВАНО' : 'РЕШЕНИЕ УСТАРЕЛО';

  return (
    <div className={`${bgColor} border-2 ${borderColor} rounded-xl p-4 mb-6`}>
      <div className="flex items-start gap-3">
        <Icon className={`${textColor} flex-shrink-0 mt-0.5`} size={20} />
        <div className="flex-1">
          <h3 className={`${textColor} font-bold text-sm mb-2`}>{title}</h3>
          <p className="text-sm text-slate-300 mb-2">
            {isInvalidated
              ? 'Это решение было инвалидировано и больше не может использоваться для принятия управленческих решений.'
              : 'Это решение основано на устаревших данных и требует актуализации.'}
          </p>
          {freshnessReason && (
            <p className="text-xs text-slate-400 mb-2">
              <strong>Причина:</strong> {freshnessReason}
            </p>
          )}
          {decisionSnapshotId && (
            <p className="text-xs text-slate-500">
              Decision Snapshot ID: {decisionSnapshotId}
            </p>
          )}
          <div className="mt-3 p-2 bg-[#0f1419] rounded border border-[#2a3441]">
            <p className="text-xs text-slate-400">
              ⚠️ <strong>Важно:</strong> Любые PDF/выгрузки этого решения должны быть маркированы как устаревшие.
              Для принятия решения требуется новый анализ.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DecisionFreshnessGuard;































