import React, { useState } from 'react';
import { TrendingUp, TrendingDown, HelpCircle, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { VerdictType } from '../../types';

interface DecisionSupportProps {
  verdict: VerdictType;
  score: number;
  financialAnalysis?: {
    margin_risk: 'High' | 'Low' | 'Medium';
    cash_gap_risk: 'Yes' | 'No';
    reasoning: string;
  };
  smartQuestions?: string[];
}

const DecisionSupport: React.FC<DecisionSupportProps> = ({
  verdict,
  score,
  financialAnalysis,
  smartQuestions,
}) => {
  const [selectedScenario, setSelectedScenario] = useState<'best' | 'worst' | null>(null);

  const getScenario = (type: 'best' | 'worst') => {
    if (verdict === 'STOP') {
      return type === 'best'
        ? {
            title: 'Лучший сценарий (при участии)',
            description:
              'Даже в лучшем случае вы столкнетесь с серьезными финансовыми и операционными рисками. Возможна частичная компенсация затрат, но прибыльность будет под вопросом.',
            icon: AlertTriangle,
            color: 'text-[#f59e0b]',
            bgColor: 'bg-[#f59e0b]/10',
            borderColor: 'border-[#f59e0b]/30',
          }
        : {
            title: 'Худший сценарий (при участии)',
            description:
              'Кассовый разрыв, невозможность выполнить обязательства, штрафы и репутационные потери. Высокий риск банкротства или значительных финансовых потерь.',
            icon: XCircle,
            color: 'text-[#ff4444]',
            bgColor: 'bg-[#ff4444]/10',
            borderColor: 'border-[#ff4444]/30',
          };
    }

    if (verdict === 'CAUTION') {
      return type === 'best'
        ? {
            title: 'Лучший сценарий',
            description:
              'При условии устранения выявленных рисков и правильной подготовки, участие может быть успешным. Возможна умеренная прибыль при соблюдении всех условий.',
            icon: TrendingUp,
            color: 'text-[#00e648]',
            bgColor: 'bg-[#00e648]/10',
            borderColor: 'border-[#00e648]/30',
          }
        : {
            title: 'Худший сценарий',
            description:
              'Невыполнение обязательств из-за недооценки рисков, задержки платежей, дополнительные расходы на устранение проблем. Прибыльность под вопросом.',
            icon: TrendingDown,
            color: 'text-[#f59e0b]',
            bgColor: 'bg-[#f59e0b]/10',
            borderColor: 'border-[#f59e0b]/30',
          };
    }

    // PARTICIPATE
    return type === 'best'
      ? {
          title: 'Лучший сценарий',
          description:
            'Успешное выполнение контракта в срок, получение прибыли, укрепление репутации и возможность дальнейшего сотрудничества с заказчиком.',
          icon: CheckCircle,
          color: 'text-[#00e648]',
          bgColor: 'bg-[#00e648]/10',
          borderColor: 'border-[#00e648]/30',
        }
      : {
          title: 'Худший сценарий',
          description:
            'Незначительные задержки или дополнительные расходы, но без критических последствий. Общая прибыльность сохраняется.',
          icon: AlertTriangle,
          color: 'text-[#f59e0b]',
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
        };
  };

  const bestScenario = getScenario('best');
  const worstScenario = getScenario('worst');
  const BestIcon = bestScenario.icon;
  const WorstIcon = worstScenario.icon;

  return (
    <div className="space-y-4">
      {/* Финансовый анализ */}
      {financialAnalysis && (
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3">
            <TrendingUp size={18} className="text-[#00d4ff]" />
            Финансовый анализ
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div className="bg-[#0f1419] rounded-xl p-4 border border-[#2a3441]">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Риск маржинальности
              </p>
              <p
                className={`text-lg font-bold ${
                  financialAnalysis.margin_risk === 'High'
                    ? 'text-[#ff4444]'
                    : financialAnalysis.margin_risk === 'Medium'
                    ? 'text-[#f59e0b]'
                    : 'text-[#00e648]'
                }`}
              >
                {financialAnalysis.margin_risk === 'High'
                  ? 'Высокий'
                  : financialAnalysis.margin_risk === 'Medium'
                  ? 'Средний'
                  : 'Низкий'}
              </p>
            </div>
            <div className="bg-[#0f1419] rounded-xl p-4 border border-[#2a3441]">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                Риск кассового разрыва
              </p>
              <p
                className={`text-lg font-bold ${
                  financialAnalysis.cash_gap_risk === 'Yes' ? 'text-[#ff4444]' : 'text-[#00e648]'
                }`}
              >
                {financialAnalysis.cash_gap_risk === 'Yes' ? 'Есть' : 'Нет'}
              </p>
            </div>
          </div>
          {financialAnalysis.reasoning && (
            <div className="bg-[#0f1419]/50 rounded-xl p-4 border border-[#2a3441]">
              <p className="text-white text-sm leading-relaxed">{financialAnalysis.reasoning}</p>
            </div>
          )}
        </div>
      )}

      {/* Сценарии */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3">
          <HelpCircle size={18} className="text-[#00d4ff]" />
          Сценарии развития событий
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {/* Лучший сценарий */}
          <div
            className={`border rounded-lg p-3 cursor-pointer transition-all ${
              selectedScenario === 'best'
                ? `${bestScenario.borderColor} ${bestScenario.bgColor} ring-2 ring-[#00d4ff]/50`
                : 'border-[#2a3441] bg-[#0f1419]/50 hover:bg-[#0f1419]'
            }`}
            onClick={() => setSelectedScenario(selectedScenario === 'best' ? null : 'best')}
          >
            <div className="flex items-center gap-2 mb-2">
              <BestIcon size={18} className={bestScenario.color} />
              <h4 className="font-bold text-white text-sm">{bestScenario.title}</h4>
            </div>
            <p className="text-slate-300 text-xs leading-relaxed">{bestScenario.description}</p>
          </div>

          {/* Худший сценарий */}
          <div
            className={`border rounded-lg p-3 cursor-pointer transition-all ${
              selectedScenario === 'worst'
                ? `${worstScenario.borderColor} ${worstScenario.bgColor} ring-2 ring-[#00d4ff]/50`
                : 'border-[#2a3441] bg-[#0f1419]/50 hover:bg-[#0f1419]'
            }`}
            onClick={() => setSelectedScenario(selectedScenario === 'worst' ? null : 'worst')}
          >
            <div className="flex items-center gap-2 mb-2">
              <WorstIcon size={18} className={worstScenario.color} />
              <h4 className="font-bold text-white text-sm">{worstScenario.title}</h4>
            </div>
            <p className="text-slate-300 text-xs leading-relaxed">{worstScenario.description}</p>
          </div>
        </div>
      </div>

      {/* Умные вопросы */}
      {smartQuestions && smartQuestions.length > 0 && (
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2 mb-3">
            <HelpCircle size={18} className="text-[#00d4ff]" />
            💬 Вопросы для заказчика
          </h3>
          <div className="space-y-3">
            {smartQuestions.map((question, idx) => {
              const handleCopy = async () => {
                try {
                  await navigator.clipboard.writeText(question);
                  // Можно добавить toast уведомление
                } catch (err) {
                  console.error('Failed to copy:', err);
                }
              };

              return (
                <div
                  key={idx}
                  className="bg-[#0f1419]/50 border border-[#2a3441] rounded-xl p-4 hover:border-[#00d4ff]/30 transition-colors"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-6 h-6 rounded-full bg-[#00d4ff]/20 border border-[#00d4ff]/30 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <span className="text-[#00d4ff] text-xs font-bold">{idx + 1}</span>
                    </div>
                    <p className="text-white text-sm leading-relaxed flex-1">{question}</p>
                  </div>
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-2 px-3 py-1.5 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-lg text-xs font-bold transition-all ml-9"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                    </svg>
                    Скопировать в буфер
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default DecisionSupport;

