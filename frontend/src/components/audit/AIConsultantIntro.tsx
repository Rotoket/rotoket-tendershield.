import React from 'react';
import { Bot, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { VerdictType } from '../../types';

interface AIConsultantIntroProps {
  verdict: VerdictType;
  executiveSummary?: string;
  summary?: string;
  score: number;
}

const AIConsultantIntro: React.FC<AIConsultantIntroProps> = ({
  verdict,
  executiveSummary,
  summary,
  score,
}) => {
  const getVerdictConfig = () => {
    switch (verdict) {
      case 'STOP':
        return {
          icon: XCircle,
          bgColor: 'bg-[#ff4444]/10',
          borderColor: 'border-[#ff4444]/30',
          iconColor: 'text-[#ff4444]',
          title: 'Высокая совокупная риск-нагрузка',
          subtitle: 'Условия участия при текущих параметрах несут недопустимую риск-нагрузку',
        };
      case 'CAUTION':
        return {
          icon: AlertTriangle,
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
          iconColor: 'text-[#f59e0b]',
          title: 'Требуется повышенное внимание',
          subtitle: 'Участие допускает управленческую нагрузку по контролю ключевых рисков',
        };
      case 'PARTICIPATE':
        return {
          icon: CheckCircle,
          bgColor: 'bg-[#00e648]/10',
          borderColor: 'border-[#00e648]/30',
          iconColor: 'text-[#00e648]',
          title: 'Риск в допустимом диапазоне',
          subtitle: 'Условия участия в целом управляемы с точки зрения рисков',
        };
      default:
        return {
          icon: AlertTriangle,
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
          iconColor: 'text-[#f59e0b]',
          title: 'Требуется дополнительное уточнение',
          subtitle: 'Необходимо запросить дополнительную аналитическую справку по ключевым рискам',
        };
    }
  };

  const config = getVerdictConfig();
  const Icon = config.icon;
  const displayText = executiveSummary || summary || 'Анализ завершен. Ознакомьтесь с деталями ниже.';

  return (
    <div className={`rounded-xl border ${config.bgColor} ${config.borderColor} p-4 relative overflow-hidden`}>
      {/* Декоративный фон */}
      <div className="absolute right-0 top-0 p-2 opacity-10">
        <Bot size={60} className={config.iconColor} />
      </div>

      <div className="relative z-10">
        {/* Заголовок с иконкой - компактно */}
        <div className="flex items-start gap-3 mb-3">
          <div className={`p-2 rounded-lg ${config.bgColor} border ${config.borderColor}`}>
            <Icon size={18} className={config.iconColor} />
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="text-lg font-bold text-white">{config.title}</h3>
              <div className="px-2 py-0.5 bg-[#1a1f2e] border border-[#2a3441] rounded">
                <span className="text-xs font-bold text-[#00d4ff]">
                  Индекс управленческой нагрузки: {score}/100
                </span>
              </div>
            </div>
            <p className="text-slate-400 text-xs">{config.subtitle}</p>
          </div>
        </div>

        {/* Основной текст - компактно */}
        <div className="bg-[#0f1419]/50 rounded-lg p-3 border border-[#2a3441]/50">
          <div className="flex items-start gap-2">
            <Bot size={16} className="text-[#00d4ff] mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                ОБОСНОВАНИЕ АНАЛИТИЧЕСКОЙ ОЦЕНКИ (НЕ ЯВЛЯЕТСЯ РЕШЕНИЕМ)
              </h4>
              <p className="text-white text-sm leading-relaxed whitespace-pre-line line-clamp-4">
                {displayText}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIConsultantIntro;

