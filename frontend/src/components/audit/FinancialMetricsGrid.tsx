import React from 'react';
import { Banknote, TrendingDown, TrendingUp, Clock, Scale, AlertTriangle } from 'lucide-react';
import { TenderPassport } from '../../types';
import ExplanationPopover from '../ExplanationPopover';

interface FinancialMetricsGridProps {
  passport: TenderPassport;
  financialAnalysis?: {
    margin_risk: 'High' | 'Low' | 'Medium';
    cash_gap_risk: 'Yes' | 'No';
    reasoning: string;
  };
  decisionRecorded?: boolean;
}

const FinancialMetricsGrid: React.FC<FinancialMetricsGridProps> = ({
  passport,
  financialAnalysis,
  decisionRecorded = false,
}) => {
  // Парсим НМЦК для отображения
  const parseNmck = (nmck: string): { value: string; isLow?: boolean } => {
    if (!nmck || nmck === 'Не найдено') return { value: 'Не указано' };
    return { value: nmck };
  };

  // Определяем риск маржи
  const getMarginRisk = () => {
    if (!financialAnalysis) {
      return { level: 'unknown', text: 'Не рассчитано', color: 'text-slate-400', icon: null };
    }
    const risk = financialAnalysis.margin_risk;
    if (risk === 'High') {
      return {
        level: 'high',
        text: 'ВЫСОКИЙ РИСК УБЫТКА',
        color: 'text-[#ff4444]',
        icon: TrendingDown,
      };
    }
    if (risk === 'Medium') {
      return {
        level: 'medium',
        text: 'СРЕДНИЙ РИСК',
        color: 'text-[#f59e0b]',
        icon: AlertTriangle,
      };
    }
    return {
      level: 'low',
      text: 'НИЗКИЙ РИСК',
      color: 'text-[#00e648]',
      icon: TrendingUp,
    };
  };

  // Определяем риск кассового разрыва
  const getCashGapRisk = () => {
    if (!financialAnalysis) {
      return { hasRisk: false, text: 'Не рассчитано', color: 'text-slate-400' };
    }
    const hasRisk = financialAnalysis.cash_gap_risk === 'Yes';
    return {
      hasRisk,
      text: hasRisk ? '⚠️ РИСК КАССОВОГО РАЗРЫВА' : '✅ БЕЗ ЯВНЫХ РИСКОВ',
      color: hasRisk ? 'text-[#ff4444]' : 'text-[#00e648]',
    };
  };

  // Анализируем баланс условий заказчика и исполнителя (упрощённая логика)
  const getAsymmetryRisk = () => {
    const noAdvance = !passport.advance || passport.advance === '0%' || passport.advance === 'Нет';
    const bidSecurity = passport.secureBid || (passport as any).bidSecurity;
    const hasSecurity = !!bidSecurity && bidSecurity !== 'Нет';

    if (noAdvance && hasSecurity) {
      return {
        hasRisk: true,
        text: '⚠️ ЗАКАЗЧИК «ЦАРЬ»',
        color: 'text-[#ff4444]',
        description: 'Нет аванса, но есть обеспечение заявки: финансовая нагрузка смещена в сторону исполнителя.',
      };
    }
    return {
      hasRisk: false,
      text: '✅ СБАЛАНСИРОВАНО',
      color: 'text-[#00e648]',
      description: 'Финансовые условия в целом сбалансированы между заказчиком и исполнителем.',
    };
  };

  const marginRisk = getMarginRisk();
  const cashGapRisk = getCashGapRisk();
  const asymmetryRisk = getAsymmetryRisk();
  const MarginIcon = marginRisk.icon || TrendingUp;
  const nmckData = parseNmck(passport.nmck);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Финансовые риски и потери */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Banknote size={20} className="text-[#00d4ff]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">💰 Финансовые риски и потери</h3>
            <p className="text-[11px] text-slate-400">
              Потенциальная маржа, возможные потери и объём средств под риском
            </p>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">НМЦК</p>
              <ExplanationPopover
                question="Что такое НМЦК (начальная максимальная цена контракта)?"
                context={{ term: 'nmcd' }}
                sourceBlock="nmcd"
                contourState={decisionRecorded ? 'after_decision' : 'before_decision'}
                decisionRecorded={decisionRecorded}
                position="bottom"
              >
                <span></span>
              </ExplanationPopover>
            </div>
            <p className={`text-2xl font-bold ${nmckData.isLow ? 'text-[#ff4444]' : 'text-white'}`}>
              {nmckData.value}
            </p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <div className="flex items-center gap-2 mb-1">
              <MarginIcon size={18} className={marginRisk.color} />
              <p className={`text-sm font-bold ${marginRisk.color}`}>{marginRisk.text}</p>
            </div>
            {financialAnalysis?.reasoning && (
              <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                {financialAnalysis.reasoning.substring(0, 100)}...
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Денежные потоки и условия оплаты */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Clock size={20} className="text-[#00d4ff]" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">⏳ Денежные потоки и условия оплаты</h3>
            <p className="text-[11px] text-slate-400">
              Сроки работ, аванс и риск кассового разрыва
            </p>
          </div>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Срок работ</p>
            <p className="text-lg font-bold text-white">
              {passport.deadlineExecution || 'Не указано'}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1 mb-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Аванс</p>
              <ExplanationPopover
                question="Что такое аванс (авансовый платёж) в закупках?"
                context={{ term: 'advance_payment' }}
                sourceBlock="term"
                contourState={decisionRecorded ? 'after_decision' : 'before_decision'}
                decisionRecorded={decisionRecorded}
                position="bottom"
              >
                <span></span>
              </ExplanationPopover>
            </div>
            <p className="text-lg font-bold text-white">{passport.advance || 'Нет'}</p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <p className={`text-sm font-bold ${cashGapRisk.color}`}>{cashGapRisk.text}</p>
            {cashGapRisk.hasRisk && (
              <p className="text-xs text-slate-400 mt-1">
                Нет аванса + отсрочка оплаты: возможен кассовый разрыв.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Баланс условий заказчика и исполнителя */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Scale size={20} className="text-[#00d4ff]" />
          </div>
          <h3 className="text-sm font-bold text-white">
            ⚖️ БАЛАНС УСЛОВИЙ ЗАКАЗЧИКА И ИСПОЛНИТЕЛЯ
          </h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="flex items-center gap-1 mb-1">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Обеспечение заявки
              </p>
              <ExplanationPopover
                question="Что такое банковская гарантия и обеспечение заявки?"
                context={{ term: 'bank_guarantee' }}
                sourceBlock="term"
                contourState={decisionRecorded ? 'after_decision' : 'before_decision'}
                decisionRecorded={decisionRecorded}
                position="bottom"
              >
                <span></span>
              </ExplanationPopover>
            </div>
            <p className="text-lg font-bold text-white">{passport.secureBid || (passport as any).bidSecurity || 'Нет'}</p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <p className={`text-sm font-bold ${asymmetryRisk.color} mb-1`}>{asymmetryRisk.text}</p>
            <p className="text-xs text-slate-400">{asymmetryRisk.description}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialMetricsGrid;
<<<<<<< HEAD







=======
>>>>>>> 53665ed (feat: Phase 5 - Database and API for procurement analysis)
