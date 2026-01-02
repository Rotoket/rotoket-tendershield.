/**
 * PHASE 1: Компонент для отображения Tender Passport
 * Показывает основные параметры тендера с источниками данных
 */

import React, { useState } from 'react';
import { FileText, Calendar, Building2, DollarSign, Clock, Shield, AlertTriangle, Info } from 'lucide-react';
import type { TenderPassportNew, TenderSource } from '../../types';

interface TenderPassportSectionProps {
  passport: TenderPassportNew;
  onShowSource?: (source: TenderSource, fieldName: string) => void;
}

const TenderPassportSection: React.FC<TenderPassportSectionProps> = ({ passport, onShowSource }) => {
  const [showingSource, setShowingSource] = useState<{ source: TenderSource; fieldName: string } | null>(null);

  const formatNMCK = (value: number): string => {
    if (value >= 1000000000) {
      return (value / 1000000000).toFixed(2) + ' млрд руб.';
    }
    if (value >= 1000000) {
      return (value / 1000000).toFixed(2) + ' млн руб.';
    }
    return value.toLocaleString('ru-RU') + ' руб.';
  };

  const formatDate = (dateStr: string | undefined): string => {
    if (!dateStr) return 'Не найден';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const handleShowSource = (source: TenderSource, fieldName: string) => {
    if (onShowSource) {
      onShowSource(source, fieldName);
    } else {
      setShowingSource({ source, fieldName });
    }
  };

  const completionPercentage = passport.completion_percentage || 0;

  return (
    <div className="bg-gradient-to-br from-[#1a1f2e] to-[#0f1419] border border-[#00d4ff]/30 rounded-2xl p-6 mb-6 relative overflow-hidden shadow-lg shadow-[#00d4ff]/5">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 p-6 opacity-10">
        <FileText size={120} className="text-[#00d4ff]" />
      </div>

      <div className="relative z-10">
        <div className="flex items-center gap-2 mb-6">
          <FileText className="text-[#00d4ff]" size={24} />
          <h2 className="text-2xl font-bold text-white">Паспорт тендера</h2>
        </div>

        {/* Passport Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* НМЦК */}
          <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 relative group hover:border-[#00d4ff]/50 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase">НМЦК</span>
              {passport.nmck_source && (
                <button
                  onClick={() => handleShowSource(passport.nmck_source, 'НМЦК')}
                  className="text-[#00d4ff] opacity-50 hover:opacity-100 transition-opacity cursor-pointer"
                  title="Показать источник"
                >
                  <Info size={14} />
                </button>
              )}
            </div>
            <div className="text-lg font-bold text-white">{formatNMCK(passport.nmck_numeric)}</div>
            <div className="text-xs text-slate-500 mt-1">{passport.nmck_formatted}</div>
          </div>

          {/* Заказчик */}
          <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 relative group hover:border-[#00d4ff]/50 transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1">
                <Building2 size={12} />
                Заказчик
              </span>
              {passport.customer_source && (
                <button
                  onClick={() => handleShowSource(passport.customer_source, 'Заказчик')}
                  className="text-[#00d4ff] opacity-50 hover:opacity-100 transition-opacity cursor-pointer"
                  title="Показать источник"
                >
                  <Info size={14} />
                </button>
              )}
            </div>
            <div className="text-sm font-semibold text-white line-clamp-2">{passport.customer || 'Не найден'}</div>
          </div>

          {/* Дедлайн */}
          {passport.deadline && (
            <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 relative group hover:border-[#00d4ff]/50 transition-all">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1">
                  <Calendar size={12} />
                  Дедлайн
                </span>
                {passport.deadline_source && (
                  <button
                    onClick={() => handleShowSource(passport.deadline_source!, 'Дедлайн')}
                    className="text-[#00d4ff] opacity-50 hover:opacity-100 transition-opacity cursor-pointer"
                    title="Показать источник"
                  >
                    <Info size={14} />
                  </button>
                )}
              </div>
              <div className="text-sm font-semibold text-white">{formatDate(passport.deadline)}</div>
            </div>
          )}

          {/* Срок контракта */}
          {passport.contract_term_months && (
            <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 relative group hover:border-[#00d4ff]/50 transition-all">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400 uppercase flex items-center gap-1">
                  <Clock size={12} />
                  Срок контракта
                </span>
                {passport.contract_term_source && (
                  <button
                    onClick={() => handleShowSource(passport.contract_term_source!, 'Срок контракта')}
                    className="text-[#00d4ff] opacity-50 hover:opacity-100 transition-opacity cursor-pointer"
                    title="Показать источник"
                  >
                    <Info size={14} />
                  </button>
                )}
              </div>
              <div className="text-sm font-semibold text-white">{passport.contract_term_months} мес.</div>
            </div>
          )}
        </div>

        {/* Индикатор заполненности */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-slate-400">Заполненность данных</span>
            <span className="text-xs font-semibold text-slate-300">{completionPercentage}%</span>
          </div>
          <div className="h-2 bg-[#1f2937] rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#00d4ff] to-[#00e648] transition-all duration-300"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>
        </div>

        {/* Government Data (если доступна) */}
        {passport.government_data && passport.government_data.previous_tenders_count > 0 && (
          <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 mb-4">
            <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Building2 size={16} className="text-[#00d4ff]" />
              Историческая информация заказчика
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div>
                <span className="text-slate-400">Предыдущих тендеров:</span>
                <div className="text-white font-semibold">{passport.government_data.previous_tenders_count}</div>
              </div>
              {passport.government_data.avg_discount_percent !== undefined && (
                <div>
                  <span className="text-slate-400">Средняя скидка:</span>
                  <div className="text-white font-semibold">{passport.government_data.avg_discount_percent}%</div>
                </div>
              )}
              {passport.government_data.avg_competitor_count !== undefined && (
                <div>
                  <span className="text-slate-400">Средние конкуренты:</span>
                  <div className="text-white font-semibold">{passport.government_data.avg_competitor_count}</div>
                </div>
              )}
              {passport.government_data.avg_payment_delay_days !== undefined && (
                <div>
                  <span className="text-slate-400">Задержка оплаты:</span>
                  <div className="text-white font-semibold">{passport.government_data.avg_payment_delay_days} дн.</div>
                </div>
              )}
            </div>
            <div className="mt-2 text-xs text-slate-500">
              Источник: {passport.government_data.data_source} ({passport.government_data.data_freshness})
            </div>
          </div>
        )}

        {/* Warnings */}
        {passport.warnings && passport.warnings.length > 0 && (
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="text-yellow-500" size={16} />
              <h4 className="text-sm font-semibold text-yellow-400">Уведомления</h4>
            </div>
            <ul className="text-xs text-yellow-300 space-y-1">
              {passport.warnings.map((warning, idx) => (
                <li key={idx}>• {warning}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Source Modal (если не передан внешний обработчик) */}
      {showingSource && !onShowSource && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setShowingSource(null)}
        >
          <div
            className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-6 max-w-2xl w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">📌 Источник данных: {showingSource.fieldName}</h3>
              <button
                onClick={() => setShowingSource(null)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-400">Документ:</span>
                  <div className="text-white">{showingSource.source.document_name}</div>
                </div>
                {showingSource.source.page_number && (
                  <div>
                    <span className="text-slate-400">Страница:</span>
                    <div className="text-white">{showingSource.source.page_number}</div>
                  </div>
                )}
              </div>
              {showingSource.source.section && (
                <div>
                  <span className="text-slate-400">Раздел:</span>
                  <div className="text-white">{showingSource.source.section}</div>
                </div>
              )}
              <div>
                <span className="text-slate-400">Цитата:</span>
                <div className="bg-[#020617] border border-[#1f2937] rounded-lg p-3 mt-1 text-slate-300 italic">
                  {showingSource.source.quote}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-400">Метод извлечения:</span>
                  <div className="text-white">
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                        showingSource.source.extraction_method === 'llm'
                          ? 'bg-[#00d4ff]/20 text-[#00d4ff]'
                          : 'bg-slate-700 text-slate-300'
                      }`}
                    >
                      {showingSource.source.extraction_method === 'llm' ? 'AI анализ' : 'Паттерн'}
                    </span>
                  </div>
                </div>
                <div>
                  <span className="text-slate-400">Уверенность:</span>
                  <div className="text-white font-semibold">
                    {(showingSource.source.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TenderPassportSection;


