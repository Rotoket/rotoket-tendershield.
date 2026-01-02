import React from 'react';

import { AlertOctagon, FileText } from 'lucide-react';

import { UserDecision } from '../../types';

import { isActionAllowed } from '../../utils/decisionRules';

interface DealBreakersPanelProps {
  dealBreakers: string[];
  onGenerateProtocol?: (dealBreakers: string[]) => void;
  // Решения принимаются ТОЛЬКО через DecisionBlock, не здесь
  decision?: UserDecision;
}

const DealBreakersPanel: React.FC<DealBreakersPanelProps> = ({
  dealBreakers,
  onGenerateProtocol,
  decision,
}) => {
  const hasDealBreakers = dealBreakers && dealBreakers.length > 0;

  if (!hasDealBreakers && !onGenerateProtocol) {
    // Если нет данных и действий, не показываем блок вовсе
    return null;
  }

  return (
    <div className="bg-[#ff4444]/10 border border-[#ff4444]/30 rounded-xl p-4 shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertOctagon size={20} className="text-[#ff4444]" />
          <h3 className="text-lg font-bold text-white">🚩 КРИТИЧЕСКИЕ СТОП-ФАКТОРЫ</h3>
        </div>

        {hasDealBreakers && (
          <span className="px-2 py-0.5 bg-[#ff4444] text-[#0f1419] text-[10px] font-bold rounded">
            Найдено: {dealBreakers.length}
          </span>
        )}
      </div>

      {hasDealBreakers ? (
        <>
          <div className="space-y-2">
            {dealBreakers.map((breaker, idx) => (
              <div
                key={idx}
                className="bg-[#0f1419]/50 border border-[#ff4444]/20 rounded-lg p-3 flex flex-col gap-2"
              >
                <div className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-[#ff4444] mt-1.5 flex-shrink-0"></div>
                  <p className="text-white text-sm leading-relaxed flex-1">{breaker}</p>
                </div>

                {/* Потенциальные последствия для каждого критического фактора */}
                <div className="mt-1 text-[11px] text-slate-200">
                  <div className="font-semibold text-[#ffcccc] uppercase tracking-wide mb-1">
                    Потенциальные последствия
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="px-2 py-0.5 rounded-full border border-[#ff4444]/40 bg-[#ff4444]/10 text-[11px]">
                      риск отклонения
                    </span>
                    <span className="px-2 py-0.5 rounded-full border border-[#ff9f43]/40 bg-[#ff9f43]/10 text-[11px]">
                      финансовые санкции
                    </span>
                    <span className="px-2 py-0.5 rounded-full border border-[#64748b]/60 bg-[#020617]/60 text-[11px]">
                      потеря времени и ресурсов
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Информационное сообщение: действия доступны после фиксации решения */}
          {onGenerateProtocol && decision && isActionAllowed(decision, 'generator_protocol') && (
            <div className="mt-5 pt-4 border-t border-[#ff4444]/25">
              <button
                type="button"
                onClick={() => onGenerateProtocol(dealBreakers)}
                className="px-4 py-2 rounded-lg text-xs font-bold transition-all bg-[#0f172a] border border-[#00d4ff]/40 text-[#00d4ff] hover:bg-[#020617] hover:border-[#00d4ff]/60 flex items-center gap-2"
              >
                <FileText size={14} />
                Сформировать протокол разногласий
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="bg[#0f1419]/50 border border-[#2a3441] rounded-lg p-3">
          <p className="text-sm text-slate-200">
            Критических блокеров не обнаружено. Тем не менее, оцените финансовую, правовую и операционную экспозицию перед принятием решения.
          </p>
        </div>
      )}
    </div>
  );
};

export default DealBreakersPanel;









































