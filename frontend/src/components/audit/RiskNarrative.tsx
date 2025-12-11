import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, AlertOctagon, Info, Lightbulb, FileText, BookOpen, ExternalLink } from 'lucide-react';

interface LegalReference {
  id: string;
  category: string;
  lawReference: string;
  title: string;
  summary: string;
}

interface RiskItem {
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low' | string;
  quote?: string;
  recommendation?: string;
  legalReferences?: LegalReference[]; // 🆕 Ссылки на нормы из Базы знаний
}

interface RiskNarrativeProps {
  risks: RiskItem[];
  dealBreakers?: string[];
  onGenerateProtocol?: (dealBreakers: string[]) => void; // 🆕 Интеграция с Генератором
  onViewKnowledge?: (query: string) => void; // 🆕 Интеграция с Базой знаний
}

// Хелпер для отладочного логирования
const debugLog = (location: string, message: string, data: any = {}) => {
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      message,
      data,
      timestamp: Date.now(),
      sessionId: 'debug-session',
      runId: 'run1',
      hypothesisId: 'RiskNarrative'
    })
  }).catch(() => {});
};

const RiskNarrative: React.FC<RiskNarrativeProps> = ({ risks, dealBreakers, onGenerateProtocol, onViewKnowledge }) => {
  // #region agent log
  debugLog('RiskNarrative.tsx:init', 'RiskNarrative initialized', {
    risksCount: risks.length,
    dealBreakersCount: dealBreakers?.length || 0,
    hasOnGenerateProtocol: !!onGenerateProtocol,
    hasOnViewKnowledge: !!onViewKnowledge
  });
  // #endregion
  const [expandedRisks, setExpandedRisks] = useState<Set<number>>(new Set());

  const toggleRisk = (index: number) => {
    const newExpanded = new Set(expandedRisks);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRisks(newExpanded);
  };

  const getSeverityConfig = (severity: string) => {
    const upper = severity.toUpperCase();
    if (upper === 'HIGH' || upper === 'CRITICAL') {
      return {
        color: 'text-[#ff4444]',
        bgColor: 'bg-[#ff4444]/10',
        borderColor: 'border-[#ff4444]/30',
        icon: AlertOctagon,
        label: 'КРИТИЧНО',
      };
    }
    if (upper === 'MEDIUM' || upper === 'WARNING') {
      return {
        color: 'text-[#f59e0b]',
        bgColor: 'bg-[#f59e0b]/10',
        borderColor: 'border-[#f59e0b]/30',
        icon: AlertTriangle,
        label: 'ВНИМАНИЕ',
      };
    }
    return {
      color: 'text-[#00d4ff]',
      bgColor: 'bg-[#00d4ff]/10',
      borderColor: 'border-[#00d4ff]/30',
      icon: Info,
      label: 'ИНФОРМАЦИЯ',
    };
  };

  if (risks.length === 0 && (!dealBreakers || dealBreakers.length === 0)) {
    return null;
  }

  const totalDealBreakers = dealBreakers?.length || 0;
  const totalRisks = risks.length;

  return (
    <div className="space-y-4">
      {/* Deal Breakers - всегда показываем первыми */}
      {dealBreakers && dealBreakers.length > 0 && (
        <div className="bg-[#ff4444]/10 border border-[#ff4444]/30 rounded-xl p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <AlertOctagon size={20} className="text-[#ff4444]" />
              <h3 className="text-lg font-bold text-white">🚩 КРИТИЧЕСКИЕ СТОП-ФАКТОРЫ</h3>
            </div>
            <span className="px-2 py-0.5 bg-[#ff4444] text-[#0f1419] text-[10px] font-bold rounded">
              Найдено: {totalDealBreakers}
            </span>
          </div>
          <div className="space-y-2">
            {dealBreakers.map((breaker, idx) => (
              <div
                key={idx}
                className="bg-[#0f1419]/50 border border-[#ff4444]/20 rounded-lg p-3 flex items-start gap-2"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-[#ff4444] mt-1.5 flex-shrink-0"></div>
                <p className="text-white text-sm leading-relaxed flex-1">{breaker}</p>
              </div>
            ))}
          </div>
          {/* Кнопка генерации протокола разногласий */}
          {onGenerateProtocol && (
            <div className="mt-4 pt-4 border-t border-[#ff4444]/20">
              <button
                onClick={() => {
                  // #region agent log
                  debugLog('RiskNarrative.tsx:generateProtocol', 'Generate protocol button clicked', {
                    dealBreakersCount: dealBreakers.length,
                    dealBreakers: dealBreakers
                  });
                  // #endregion
                  onGenerateProtocol(dealBreakers);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-xl text-sm font-bold transition-all hover:shadow-[0_0_15px_rgba(0,212,255,0.3)]"
              >
                <FileText size={18} />
                Сформировать протокол разногласий
              </button>
            </div>
          )}
        </div>
      )}

      {/* Риски */}
      {risks.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <AlertTriangle size={24} className="text-[#f59e0b]" />
              Анализ рисков
            </h3>
            <span className="px-3 py-1 bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30 text-xs font-bold rounded-lg">
              Найдено: {totalRisks}
            </span>
          </div>

          {risks.map((risk, index) => {
            const isExpanded = expandedRisks.has(index);
            const severityConfig = getSeverityConfig(risk.severity);
            const SeverityIcon = severityConfig.icon;

            return (
              <div
                key={index}
                className={`border rounded-xl transition-all duration-300 overflow-hidden ${
                  severityConfig.borderColor
                } ${severityConfig.bgColor}`}
              >
                {/* Заголовок карточки */}
                <div
                  className="p-3 flex items-center justify-between cursor-pointer hover:bg-[#2a3441]/30 transition-colors"
                  onClick={() => toggleRisk(index)}
                >
                  <div className="flex items-center gap-2 flex-1">
                    <SeverityIcon size={16} className={severityConfig.color} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h4 className="font-bold text-white text-sm">{risk.title}</h4>
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${severityConfig.borderColor} ${severityConfig.color}`}
                        >
                          {severityConfig.label}
                        </span>
                      </div>
                      {!isExpanded && (
                        <p className="text-slate-400 text-xs line-clamp-1">{risk.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="ml-2">
                    {isExpanded ? (
                      <ChevronUp size={16} className="text-slate-400" />
                    ) : (
                      <ChevronDown size={16} className="text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Раскрытое содержимое */}
                {isExpanded && (
                  <div className="border-t border-[#2a3441] bg-[#0f1419]/50">
                    <div className="p-3 space-y-3">
                      {/* Что это значит */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Info size={16} className="text-[#00d4ff]" />
                          <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Что это значит
                          </h5>
                        </div>
                        <p className="text-white text-sm leading-relaxed">{risk.description}</p>
                        {risk.quote && (
                          <div className="mt-3 p-3 bg-[#1a1f2e] border-l-4 border-[#00d4ff] rounded">
                            <p className="text-slate-300 text-xs italic">"{risk.quote}"</p>
                          </div>
                        )}
                      </div>

                      {/* Почему это важно для вас */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle size={16} className="text-[#f59e0b]" />
                          <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Почему это важно для вас
                          </h5>
                        </div>
                        <p className="text-white text-sm leading-relaxed">
                          {risk.recommendation ||
                            'Этот риск может повлиять на вашу способность выполнить контракт или получить прибыль. Рекомендуем внимательно оценить последствия.'}
                        </p>
                      </div>

                      {/* Мой совет */}
                      {risk.recommendation && (
                        <div className="bg-[#00d4ff]/10 border border-[#00d4ff]/30 rounded-xl p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb size={16} className="text-[#00d4ff]" />
                            <h5 className="text-xs font-bold text-[#00d4ff] uppercase tracking-wider">
                              Мой совет
                            </h5>
                          </div>
                          <p className="text-white text-sm leading-relaxed">{risk.recommendation}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RiskNarrative;

