import React from 'react';
import { XCircle, AlertTriangle, CheckCircle, Flame, ChevronDown, FileText } from 'lucide-react';
import { VerdictType } from '../../types';

interface HeroVerdictProps {
  verdict: VerdictType;
  score: number;
  executiveSummary?: string;
  mainProblem?: string; // Главная проблема из executive_summary
  onShowDetails?: () => void;
  onGenerateRefusal?: () => void;
}

const HeroVerdict: React.FC<HeroVerdictProps> = ({
  verdict,
  score,
  executiveSummary,
  mainProblem,
  onShowDetails,
  onGenerateRefusal,
}) => {
  const getVerdictConfig = () => {
    switch (verdict) {
      case 'STOP':
        return {
          icon: XCircle,
          bgColor: 'bg-[#ff4444]/10',
          borderColor: 'border-[#ff4444]/30',
          iconColor: 'text-[#ff4444]',
          badgeColor: 'bg-[#ff4444]',
          title: 'НЕ РЕКОМЕНДУЕТСЯ',
          subtitle: 'Высокий Риск',
          actionText: 'Сформировать отказ',
        };
      case 'CAUTION':
        return {
          icon: AlertTriangle,
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
          iconColor: 'text-[#f59e0b]',
          badgeColor: 'bg-[#f59e0b]',
          title: 'ТРЕБУЕТ ВНИМАНИЯ',
          subtitle: 'Средний Риск',
          actionText: 'Показать риски',
        };
      case 'PARTICIPATE':
        return {
          icon: CheckCircle,
          bgColor: 'bg-[#00e648]/10',
          borderColor: 'border-[#00e648]/30',
          iconColor: 'text-[#00e648]',
          badgeColor: 'bg-[#00e648]',
          title: 'РЕКОМЕНДУЕТСЯ',
          subtitle: 'Низкий Риск',
          actionText: 'Показать детали',
        };
      default:
        return {
          icon: AlertTriangle,
          bgColor: 'bg-[#f59e0b]/10',
          borderColor: 'border-[#f59e0b]/30',
          iconColor: 'text-[#f59e0b]',
          badgeColor: 'bg-[#f59e0b]',
          title: 'ТРЕБУЕТ АНАЛИЗА',
          subtitle: 'Необходима проверка',
          actionText: 'Показать детали',
        };
    }
  };

  const config = getVerdictConfig();
  const Icon = config.icon;

  // Извлекаем главную проблему из executive_summary или используем переданную
  const extractMainProblem = () => {
    if (mainProblem) return mainProblem;
    if (!executiveSummary) return 'Требуется детальный анализ';
    
    // Ищем строку с "проблема" или "риск"
    const lines = executiveSummary.split('\n');
    const problemLine = lines.find(line => 
      line.toLowerCase().includes('проблема') || 
      line.toLowerCase().includes('риск') ||
      line.toLowerCase().includes('главн')
    );
    
    if (problemLine) {
      // Убираем маркеры и лишнее
      return problemLine
        .replace(/.*?проблема[:\s]+/i, '')
        .replace(/.*?риск[:\s]+/i, '')
        .replace(/.*?главн[а-я]+[:\s]+/i, '')
        .replace(/^[🔥🛑⚠️❌]+/g, '')
        .trim();
    }
    
    // Если не нашли, берем первую строку или первые 150 символов
    return lines[0]?.substring(0, 200) || executiveSummary.substring(0, 200);
  };

  const problemText = extractMainProblem();

  return (
    <div className={`rounded-xl border ${config.bgColor} ${config.borderColor} p-4 relative overflow-hidden shadow-lg`}>
      {/* Декоративный фон */}
      <div className="absolute right-0 top-0 w-20 h-20 opacity-5">
        <Icon size={80} className={config.iconColor} />
      </div>

      <div className="relative z-10">
        {/* Заголовок с вердиктом */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${config.bgColor} border ${config.borderColor}`}>
              <Icon size={20} className={config.iconColor} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-0.5">
                <h2 className="text-xl font-bold text-white">{config.title}</h2>
                <span className={`px-2 py-0.5 ${config.badgeColor} text-[#0f1419] text-[10px] font-bold rounded`}>
                  {config.subtitle}
                </span>
              </div>
              <p className="text-slate-400 text-xs">Вердикт системы</p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-white">{score}</div>
            <div className="text-[10px] font-bold text-slate-400 uppercase">Safety Score</div>
          </div>
        </div>

        {/* Главная проблема - компактно */}
        {problemText && (
          <div className="bg-[#0f1419]/70 rounded-lg p-3 border border-[#2a3441] mb-3">
            <div className="flex items-start gap-2">
              <Flame size={16} className="text-[#ff4444] flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                  ГЛАВНАЯ ПРОБЛЕМА:
                </h3>
                <p className="text-white text-sm leading-relaxed line-clamp-2">{problemText}</p>
              </div>
            </div>
          </div>
        )}

        {/* Кнопки действий */}
        <div className="flex items-center gap-2">
          <button
            onClick={onShowDetails}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-lg text-xs font-bold transition-all hover:shadow-[0_0_10px_rgba(0,212,255,0.3)]"
          >
            <ChevronDown size={14} />
            Детали
          </button>
          {verdict === 'STOP' && (
            <button
              onClick={onGenerateRefusal}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-[#ff4444]/10 hover:bg-[#ff4444]/20 text-[#ff4444] border border-[#ff4444]/30 rounded-lg text-xs font-bold transition-all hover:shadow-[0_0_10px_rgba(255,68,68,0.3)]"
            >
              <FileText size={14} />
              Отказ
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default HeroVerdict;

