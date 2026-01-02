import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertTriangle, AlertOctagon, Info, Lightbulb, BookOpen, ExternalLink } from 'lucide-react';
import ExplanationPopover from '../ExplanationPopover';

interface LegalReference {
  id: string;
  category: string;
  lawReference: string;
  title: string;
  summary: string;
}

interface EvidenceItem {
  document_name: string;
  page_reference?: string | null;
  section_reference?: string | null;
  quote: string;
}

interface RiskItem {
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low' | string;
  risk_type?: 'CRITICAL' | 'POTENTIAL' | 'FORMAL'; // Устаревшее, используйте severity_level
  severity_level?: 'DEAL_BREAKER' | 'CONTROLLED_RISK' | 'MARKET_NOISE'; // Трёхуровневая модель
  confidence_level?: number; // 0-100, уровень уверенности в значимости риска
  quote?: string;
  evidence?: EvidenceItem[];
  recommendation?: string;
  legalReferences?: LegalReference[]; // 🆕 Ссылки на нормы из Базы знаний
}

interface RiskNarrativeProps {
  risks: RiskItem[];
  onViewKnowledge?: (query: string) => void; // 🆕 Интеграция с Базой знаний
  decisionRecorded?: boolean; // Зафиксировано ли решение
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
  }).catch(() => { });
};

const RiskNarrative: React.FC<RiskNarrativeProps> = ({ risks, onViewKnowledge, decisionRecorded = false }) => {
  // #region agent log
  debugLog('RiskNarrative.tsx:init', 'RiskNarrative initialized', {
    risksCount: risks.length,
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

  const getSeverityLevelConfig = (severityLevel?: string) => {
    if (!severityLevel) return null;
    const upper = severityLevel.toUpperCase();
    switch (upper) {
      case 'DEAL_BREAKER':
        return {
          label: 'КРИТИЧЕСКИЙ СТОП-ФАКТОР',
          color: 'text-[#ff4444]',
          bgColor: 'bg-[#ff4444]/10',
          borderColor: 'border-[#ff4444]/30',
          description: 'Критический фактор, блокирующий участие',
        };
      case 'CONTROLLED_RISK':
        return {
          label: 'КОНТРОЛИРУЕМЫЙ РИСК',
          color: 'text-[#f59e0b]',
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
          description: 'Управляемый риск, требует контроля',
        };
      case 'MARKET_NOISE':
        return {
          label: 'РЫНОЧНЫЙ ФАКТОР (НЕ КРИТИЧЕН)',
          color: 'text-[#64748b]',
          bgColor: 'bg-[#64748b]/10',
          borderColor: 'border-[#64748b]/30',
          description: 'Рыночный шум, не влияет на решение',
        };
      default:
        return null;
    }
  };

  const getRiskTypeConfig = (riskType?: string) => {
    if (!riskType) return null;
    const upper = riskType.toUpperCase();
    switch (upper) {
      case 'CRITICAL':
        return {
          label: 'Подтверждённый риск',
          color: 'text-[#ff4444]',
          bgColor: 'bg-[#ff4444]/10',
          description: 'Реальное противоречие в условиях',
        };
      case 'POTENTIAL':
        return {
          label: 'Потенциальный риск',
          color: 'text-[#f59e0b]',
          bgColor: 'bg-[#f59e0b]/10',
          description: 'Требует проверки влияния на условия',
        };
      case 'FORMAL':
        return {
          label: 'Формальный след',
          color: 'text-[#64748b]',
          bgColor: 'bg-[#64748b]/10',
          description: 'Шаблонные ссылки, не влияют на условия',
        };
      default:
        return null;
    }
  };

  const getSeverityConfig = (severity: string, riskType?: string) => {
    // Если есть risk_type, используем его для определения цвета
    const typeConfig = getRiskTypeConfig(riskType);
    if (typeConfig) {
      return {
        color: typeConfig.color,
        bgColor: typeConfig.bgColor,
        borderColor: typeConfig.color.replace('text-', 'border-').replace('[#', '[#').replace(']', ']/30'),
        icon: riskType === 'CRITICAL' ? AlertOctagon : AlertTriangle,
        label: typeConfig.label,
      };
    }
    
    // Fallback на старую логику по severity
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

  if (risks.length === 0) {
    return null;
  }

  const totalRisks = risks.length;

  return (
    <div className="space-y-4">
      {/* Риски */}
      {risks.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-xl font-bold text-white flex items-center gap-2">
              <AlertTriangle size={24} className="text-[#f59e0b]" />
              Пояснение ключевых рисков для директора
            </h3>
            <span className="px-3 py-1 bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30 text-xs font-bold rounded-lg">
              Найдено: {totalRisks}
            </span>
          </div>

          {risks.map((risk, index) => {
            const isExpanded = expandedRisks.has(index);
            // Приоритет: severity_level > risk_type > severity
            const severityLevelConfig = getSeverityLevelConfig(risk.severity_level);
            const riskTypeConfig = getRiskTypeConfig(risk.risk_type);
            const severityConfig = severityLevelConfig 
              ? {
                  color: severityLevelConfig.color,
                  bgColor: severityLevelConfig.bgColor,
                  borderColor: severityLevelConfig.borderColor || 'border-[#2a3441]',
                  icon: risk.severity_level === 'DEAL_BREAKER' ? AlertOctagon : AlertTriangle,
                  label: severityLevelConfig.label,
                }
              : getSeverityConfig(risk.severity || 'medium', risk.risk_type);
            const SeverityIcon = severityConfig.icon;
            const confidenceLevel = risk.confidence_level ?? 100;

            return (
              <div
                key={index}
                className={`border rounded-xl transition-all duration-300 overflow-hidden ${severityConfig.borderColor
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
                      <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                        <h4 className="font-bold text-white text-sm">{risk.title}</h4>
                        {severityLevelConfig && (
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${severityConfig.borderColor} ${severityConfig.color}`}
                          >
                            {severityConfig.label}
                          </span>
                        )}
                        {!severityLevelConfig && riskTypeConfig && (
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${severityConfig.borderColor} ${severityConfig.color}`}
                          >
                            {severityConfig.label}
                          </span>
                        )}
                        {risk.confidence_level !== undefined && (
                          <span className="text-[9px] text-slate-400 px-1.5 py-0.5">
                            Уверенность: {confidenceLevel}%
                          </span>
                        )}
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
                      {/* Упрощённое объяснение: 3 секции */}
                      <div className="space-y-3">
                        {/* 1. Суть (2 строки) */}
                        <div>
                          <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                            Суть
                          </h5>
                          <p className="text-white text-sm leading-relaxed">
                            {risk.description?.split('\n')[0] || risk.description || 'Требует внимания при принятии решения.'}
                          </p>
                        </div>

                        {/* 2. Опасно, если... */}
                        {(risk.severity_level !== 'MARKET_NOISE' && risk.risk_type !== 'FORMAL') && (
                          <div>
                            <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                              Опасно, если...
                            </h5>
                            <p className="text-white text-sm leading-relaxed">
                              {risk.severity_level === 'DEAL_BREAKER'
                                ? (risk.recommendation || 'Не устранены указанные условия. Участие может привести к существенным рискам.')
                                : (risk.recommendation || 'Игнорируются условия, влияющие на финансовые или правовые обязательства.')}
                            </p>
                          </div>
                        )}

                        {/* 3. Можно игнорировать, если... */}
                        {(risk.severity_level === 'MARKET_NOISE' || risk.risk_type === 'FORMAL') && (
                          <div>
                            <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                              Можно игнорировать, если...
                            </h5>
                            <p className="text-white text-sm leading-relaxed">
                              {risk.recommendation ||
                                'Это типичный риск закупок, связанный с шаблонными формулировками. ' +
                                'Не влияет на условия участия, оплаты или ответственности.'}
                            </p>
                          </div>
                        )}

                        {/* Источник (цитата) */}
                        {(risk.evidence && risk.evidence.length > 0) || risk.quote ? (
                          <div className="bg-[#020617] border border-[#1e293b] rounded-xl p-3">
                            <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
                              Источник
                            </div>
                            {risk.evidence && risk.evidence.length > 0 ? (
                              <div className="space-y-2">
                                {risk.evidence.slice(0, 2).map((ev, evIdx) => (
                                  <div key={evIdx} className="text-xs text-slate-300">
                                    <div className="text-[11px] text-slate-400">
                                      {ev.document_name}
                                      {ev.page_reference ? ` · стр. ${ev.page_reference}` : ''}
                                      {ev.section_reference ? ` · ${ev.section_reference}` : ''}
                                    </div>
                                    <div className="text-slate-200 mt-1 whitespace-pre-line">
                                      {ev.quote}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="text-xs text-slate-200 whitespace-pre-line">
                                {risk.quote}
                              </div>
                            )}
                          </div>
                        ) : null}
                        
                        {/* Уровень уверенности */}
                        {risk.confidence_level !== undefined && (
                          <div className="mt-3 p-2 bg-[#1a1f2e] rounded border border-[#2a3441]">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-slate-400">Степень уверенности:</span>
                              <span className="text-xs font-bold text-white">{confidenceLevel}%</span>
                            </div>
                            <div className="w-full bg-[#0f1419] rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${severityConfig.color.replace('text-', 'bg-')}`}
                                style={{ width: `${confidenceLevel}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Управленческое основание */}
                      {risk.recommendation && (
                        <div className="bg-[#00d4ff]/10 border border-[#00d4ff]/30 rounded-xl p-4">
                          <div className="flex items-center gap-2 mb-2">
                            <Lightbulb size={16} className="text-[#00d4ff]" />
                            <h5 className="text-xs font-bold text-[#00d4ff] uppercase tracking-wider">
                              Основание для решения
                            </h5>
                          </div>
                          <p className="text-white text-sm leading-relaxed">{risk.recommendation}</p>
                        </div>
                      )}

                      {/* Релевантные нормы из Базы знаний */}
                      {risk.legalReferences && risk.legalReferences.length > 0 && (
                        <div className="bg-[#020617] border border-[#1e293b] rounded-xl p-3">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <BookOpen size={16} className="text-slate-300" />
                              <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                                Релевантные нормы и разъяснения
                              </h5>
                            </div>
                            {onViewKnowledge && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  const query = risk.legalReferences?.map((r) => r.lawReference).join(', ');
                                  if (query) {
                                    onViewKnowledge(query);
                                  }
                                }}
                                className="flex items-center gap-1 px-2 py-1 text-[11px] font-semibold text-[#00d4ff] hover:text-white"
                              >
                                Открыть в Базе знаний
                                <ExternalLink size={12} />
                              </button>
                            )}
                          </div>
                          <ul className="space-y-2">
                            {risk.legalReferences.map((ref) => {
                              // Извлекаем код закона из ссылки (например, "44-ФЗ" из "ФЗ-44" или "44-ФЗ")
                              const lawCodeMatch = ref.lawReference.match(/(\d+)-?ФЗ/i);
                              const lawCode = lawCodeMatch ? `${lawCodeMatch[1]}-ФЗ` : undefined;
                              
                              return (
                                <li key={ref.id} className="text-xs text-slate-300">
                                  <div className="flex items-center gap-1 font-semibold text-slate-100">
                                    <span>{ref.lawReference} — {ref.title}</span>
                                    {lawCode && (
                                      <ExplanationPopover
                                        question={`Что означает ссылка на ${lawCode} в контексте этого риска?`}
                                        context={{ lawCode }}
                                        sourceBlock="risk"
                                        contourState={decisionRecorded ? 'after_decision' : 'before_decision'}
                                        decisionRecorded={decisionRecorded}
                                        position="right"
                                      >
                                        <span className="text-[10px] text-slate-500">· пояснить</span>
                                      </ExplanationPopover>
                                    )}
                                  </div>
                                  <div className="text-slate-400">{ref.summary}</div>
                                </li>
                              );
                            })}
                          </ul>
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
