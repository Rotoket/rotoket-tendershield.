import React from 'react';
import { Banknote, TrendingDown, TrendingUp, Clock, Scale, AlertTriangle } from 'lucide-react';
import { TenderPassport } from '../../types';

interface FinancialMetricsGridProps {
  passport: TenderPassport;
  financialAnalysis?: {
    margin_risk: 'High' | 'Low' | 'Medium';
    cash_gap_risk: 'Yes' | 'No';
    reasoning: string;
  };
}

const FinancialMetricsGrid: React.FC<FinancialMetricsGridProps> = ({
  passport,
  financialAnalysis,
}) => {
  // Парсим НМЦК для отображения
  const parseNmck = (nmck: string): { value: string; isLow?: boolean } => {
    if (!nmck || nmck === 'Не найдено') return { value: 'Не указано' };
    return { value: nmck };
  };

  // Определяем риск маржи
  const getMarginRisk = () => {
    if (!financialAnalysis) return { level: 'unknown', text: 'Не рассчитано', color: 'text-slate-400', icon: null };
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
    if (!financialAnalysis) return { hasRisk: false, text: 'Не рассчитано' };
    const hasRisk = financialAnalysis.cash_gap_risk === 'Yes';
    return {
      hasRisk,
      text: hasRisk ? '⚠️ РИСК РАЗРЫВА' : '✅ БЕЗОПАСНО',
      color: hasRisk ? 'text-[#ff4444]' : 'text-[#00e648]',
    };
  };

  // Анализируем асимметрию (упрощенная логика)
  const getAsymmetryRisk = () => {
    // Если нет аванса и есть обеспечение - это асимметрия
    const noAdvance = !passport.advance || passport.advance === '0%' || passport.advance === 'Нет';
    const hasSecurity = passport.secureBid && passport.secureBid !== 'Нет';
    
    if (noAdvance && hasSecurity) {
      return {
        hasRisk: true,
        text: '⚠️ ЗАКАЗЧИК "ЦАРЬ"',
        color: 'text-[#ff4444]',
        description: 'Нет аванса, но есть обеспечение',
      };
    }
    return {
      hasRisk: false,
      text: '✅ СБАЛАНСИРОВАНО',
      color: 'text-[#00e648]',
      description: 'Условия справедливы',
    };
  };

  const marginRisk = getMarginRisk();
  const cashGapRisk = getCashGapRisk();
  const asymmetryRisk = getAsymmetryRisk();
  const MarginIcon = marginRisk.icon || TrendingUp;
  const nmckData = parseNmck(passport.nmck);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* ДЕНЬГИ (МАРЖА) */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Banknote size={20} className="text-[#00d4ff]" />
          </div>
          <h3 className="text-sm font-bold text-white">💰 ДЕНЬГИ (МАРЖА)</h3>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">НМЦК</p>
            <p className={`text-2xl font-bold ${nmckData.isLow ? 'text-[#ff4444]' : 'text-white'}`}>
              {nmckData.value}
            </p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <div className="flex items-center gap-2 mb-1">
              <MarginIcon size={18} className={marginRisk.color} />
              <p className={`text-sm font-bold ${marginRisk.color}`}>
                {marginRisk.text}
              </p>
            </div>
            {financialAnalysis?.reasoning && (
              <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                {financialAnalysis.reasoning.substring(0, 100)}...
              </p>
            )}
          </div>
        </div>
      </div>

      {/* СРОКИ И ОПЛАТА */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Clock size={20} className="text-[#00d4ff]" />
          </div>
          <h3 className="text-sm font-bold text-white">⏳ СРОКИ И ОПЛАТА</h3>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Срок работ</p>
            <p className="text-lg font-bold text-white">
              {passport.deadlineExecution || 'Не указано'}
            </p>
          </div>
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Аванс</p>
            <p className="text-lg font-bold text-white">
              {passport.advance || 'Нет'}
            </p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <p className={`text-sm font-bold ${cashGapRisk.color}`}>
              {cashGapRisk.text}
            </p>
            {cashGapRisk.hasRisk && (
              <p className="text-xs text-slate-400 mt-1">
                Нет аванса + отсрочка оплаты
              </p>
            )}
          </div>
        </div>
      </div>

      {/* АСИММЕТРИЯ */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-5 relative overflow-hidden">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-[#0f1419] rounded-lg border border-[#2a3441]">
            <Scale size={20} className="text-[#00d4ff]" />
          </div>
          <h3 className="text-sm font-bold text-white">⚖️ АСИММЕТРИЯ</h3>
        </div>
        <div className="space-y-3">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Обеспечение</p>
            <p className="text-lg font-bold text-white">
              {passport.secureBid || 'Нет'}
            </p>
          </div>
          <div className="pt-3 border-t border-[#2a3441]">
            <p className={`text-sm font-bold ${asymmetryRisk.color} mb-1`}>
              {asymmetryRisk.text}
            </p>
            <p className="text-xs text-slate-400">
              {asymmetryRisk.description}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinancialMetricsGrid;







