import React from 'react';
import type { PackageAnalysis, PackageHubSummary } from '../types';
import { AlertTriangle, ShieldAlert, FileSearch, Clock, Banknote, CheckCircle } from 'lucide-react';
import { buildPackageHubFromAnalysis } from '../utils/hubBuilders';
import { verdictLabel, severityLabel } from '../utils/hubUiHelpers';

interface PackageHubDashboardProps {
  pkg: PackageAnalysis;
}

const severityColor = (severity: string): string => {
  const s = severity.toUpperCase();
  if (s.includes('HIGH') || s.includes('ВЫС')) return 'text-red-400 bg-red-500/10 border-red-500/40';
  if (s.includes('MED') || s.includes('СРЕД')) return 'text-amber-300 bg-amber-500/10 border-amber-500/40';
  return 'text-emerald-300 bg-emerald-500/10 border-emerald-500/40';
};

const PackageHubDashboard: React.FC<PackageHubDashboardProps> = ({ pkg }) => {
  const hub: PackageHubSummary = pkg.hub || buildPackageHubFromAnalysis(pkg);

  return (
    <div className="space-y-4">
      {/* Ряд ключевых блоков для тендерщика */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Критические риски и итог по пакету */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ShieldAlert size={18} className="text-[#f97316]" />
            <span>Критические риски и итог по пакету</span>
          </div>
          <div className="flex items-baseline gap-3 mt-1">
            <div className="text-3xl font-bold text-white">{Math.round(pkg.summaryScore)} / 100</div>
            <div className="text-xs text-slate-400">
              Вердикт:{' '}
              <span className="font-semibold text-slate-100">{verdictLabel(pkg.verdict)}</span>
            </div>
          </div>
          <div className="text-[11px] text-slate-300 mt-1">
            {hub.recommendation.summaryShort ||
              'Система оценила пакет на основе всех загруженных документов. Решение об участии остаётся за специалистом.'}
          </div>
          <div className="mt-2 text-[11px] text-slate-300">
            <span className="text-slate-400">Количество глобальных рисков:</span>{' '}
            <span className="font-semibold text-slate-100">{hub.legalViolations.length}</span>
          </div>
        </div>

        {/* Паспорт закупки */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <FileSearch size={16} className="text-[#00d4ff]" />
            <span>Паспорт закупки (по пакету)</span>
          </div>
          <div className="grid grid-cols-2 gap-3 mt-1 text-[11px] text-slate-300">
            <div>
              <div className="text-slate-400 mb-0.5">НМЦК (суммарно)</div>
              <div className="font-mono text-slate-100">{hub.baseInfo.nmckTotal}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-0.5">Документов</div>
              <div className="font-semibold text-slate-100">{hub.specsSummary.totalDocuments}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-0.5">Закон</div>
              <div>{hub.baseInfo.fz || '44‑ФЗ / 223‑ФЗ'}</div>
            </div>
            <div>
              <div className="text-slate-400 mb-0.5">Регион</div>
              <div>{hub.baseInfo.region || 'Не указан'}</div>
            </div>
          </div>
        </div>

        {/* Финансы и сроки по пакету */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-3 text-[11px] text-slate-300">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <Banknote size={16} className="text-[#00d4ff]" />
            <span>Финансы и сроки</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-[#00d4ff]" />
            <div>
              <div className="text-slate-400 mb-0.5">Сроки по пакету</div>
              <div className="text-slate-200">{hub.timeline.comment}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-[#00d4ff]" />
            <div>
              <div className="text-slate-400 mb-0.5">Финансовая оценка</div>
              {hub.financial.marginPercentApprox != null && (
                <div className="mb-0.5">
                  Ориентировочная маржа:{' '}
                  <span className="font-semibold text-slate-100">~{hub.financial.marginPercentApprox}%</span>
                </div>
              )}
              <div className="mb-0.5">{hub.financial.marginComment}</div>
              <div>
                Риск убытка:{' '}
                <span className="font-semibold text-slate-100">
                  {severityLabel(hub.financial.lossRiskLevel)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Красные флаги и интеграция */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-2 lg:col-span-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <AlertTriangle size={16} className="text-red-400" />
            <span>Красные флаги по пакету</span>
          </div>
          {hub.redFlagsTop.length === 0 ? (
            <p className="text-[11px] text-slate-400">
              Явных красных флагов по пакету не выделено. Всё равно проверьте условия по 44‑ФЗ/223‑ФЗ и проект договора.
            </p>
          ) : (
            <ul className="space-y-2 text-[11px]">
              {hub.redFlagsTop.map((rf, idx) => (
                <li
                  key={idx}
                  className={`px-2 py-1.5 rounded border ${severityColor(rf.severity)}`}
                >
                  <div className="font-semibold mb-0.5">{rf.title}</div>
                  {rf.lawReference && (
                    <div className="text-[10px] text-slate-300">Норма: {rf.lawReference}</div>
                  )}
                  {rf.explanation && (
                    <div className="text-[10px] text-slate-200 mt-0.5">{rf.explanation}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <FileSearch size={16} className="text-[#00d4ff]" />
            <span>Интеграция с другими экранами</span>
          </div>
          <p className="text-[11px] text-slate-300">
            Используйте результаты аудита для заполнения калькулятора маржи и генерации документов (протокол
            разногласий, жалоба в ФАС) на соответствующих вкладках.
          </p>
        </div>
      </div>

      {/* Быстрая статистика по документам пакета */}
      <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 text-[11px] text-slate-300 flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <FileSearch size={14} className="text-[#00d4ff]" />
          <span>
            В пакете <span className="font-semibold text-slate-100">{pkg.documents.length}</span> документов. Система
            подсветила основные противоречия и риски.
          </span>
        </div>
        <div className="text-[10px] text-slate-500">
          Итоговая оценка пакета формируется на основе худшего документа и глобальных рисков.
        </div>
      </div>
    </div>
  );
};

export default PackageHubDashboard;
