import React, { useEffect, useState, useMemo } from 'react';
import { AuditHistoryItem, VerdictType } from '../types';
import { fetchAuditHistory } from '../services/geminiService';
import { Clock, Search, Filter, X, Eye, ChevronDown, ChevronUp, AlertTriangle, Flame } from 'lucide-react';
import { logEvent } from '../utils/logger';
import { verdictLabel } from '../utils/hubUiHelpers';

const formatDateTime = (iso: string): string => {
  try {
    const d = new Date(iso);
    return d.toLocaleString('ru-RU');
  } catch {
    return iso;
  }
};

const verdictBadge = (verdict: VerdictType | string): string => {
  switch (verdict) {
    case 'STOP':
      return 'bg-red-500/10 text-red-300 border-red-500/60';
    case 'CAUTION':
      return 'bg-amber-500/10 text-amber-300 border-amber-500/60';
    case 'PARTICIPATE':
      return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/60';
    default:
      return 'bg-slate-700/40 text-slate-200 border-slate-600/60';
  }
};

const HistoryView: React.FC = () => {
  const [items, setItems] = useState<AuditHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Фильтры и поиск
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'single' | 'package'>('all');
  const [filterVerdict, setFilterVerdict] = useState<'all' | VerdictType>('all');
  const [filterIndustry, setFilterIndustry] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  
  // Раскрытые карточки для отображения деталей
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        setError(null);
        logEvent('History', 'Запрошена история аудитов с фильтрами');

        // Передаем параметры поиска и фильтров на бэкенд
        const data = await fetchAuditHistory(
          100,
          searchQuery || undefined,
          filterIndustry !== 'all' ? filterIndustry : undefined,
          filterVerdict !== 'all' ? filterVerdict : undefined
        );
        setItems(data.items);
        logEvent('History', `История аудитов успешно загружена, записей: ${data.items?.length ?? 0}`);
      } catch (e: any) {
        setError(e?.message ?? 'Ошибка загрузки истории');
        logEvent('History', 'Ошибка загрузки истории аудитов', 'error', e);
      } finally {
        setIsLoading(false);
      }
    };

    // Задержка для debounce поиска
    const timeoutId = setTimeout(load, searchQuery ? 500 : 0);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, filterIndustry, filterVerdict]);

  // Фильтрация по типу (только на фронтенде, т.к. бэкенд не поддерживает фильтр по типу)
  const filteredItems = useMemo(() => {
    return items.filter(item => {
      // Фильтр по типу (только на фронтенде)
      if (filterType !== 'all' && item.kind !== filterType) {
        return false;
      }
      return true;
    });
  }, [items, filterType]);

  // Получение уникальных отраслей
  const industries = useMemo(() => {
    const unique = Array.from(new Set(items.map(item => item.industry)));
    return unique.sort();
  }, [items]);

  const clearFilters = () => {
    setSearchQuery('');
    setFilterType('all');
    setFilterVerdict('all');
    setFilterIndustry('all');
  };

  const hasActiveFilters = searchQuery || filterType !== 'all' || filterVerdict !== 'all' || filterIndustry !== 'all';

  return (
    <div className="h-full flex flex-col text-white">
      <div className="flex items-center gap-2 mb-1">
        <Clock size={20} className="text-[#00d4ff]" />
        <h2 className="text-lg font-semibold">История проверок</h2>
      </div>
      <p className="mb-4 text-xs text-slate-400 max-w-2xl">
        Здесь фиксируются недавние аудиты: одиночные документы и пакетные проверки. Балл и вердикт носят предварительный аналитический характер, решение остаётся за специалистом.
      </p>

      {error && <div className="mb-3 text-xs text-red-400">{error}</div>}

      {/* Поиск и фильтры */}
      {items.length > 0 && (
        <div className="mb-4 space-y-3">
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Поиск по названию файла..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-[#1a1f2e] border border-[#2a3441] rounded-xl text-white text-sm placeholder-slate-500 focus:outline-none focus:border-[#00d4ff]"
              />
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-xl border text-sm font-medium transition-colors flex items-center gap-2 ${showFilters || hasActiveFilters
                ? 'bg-[#00d4ff]/10 border-[#00d4ff] text-[#00d4ff]'
                : 'bg-[#1a1f2e] border-[#2a3441] text-slate-300 hover:border-[#00d4ff]/50'
                }`}
            >
              <Filter size={16} />
              Фильтры
              {hasActiveFilters && (
                <span className="ml-1 px-1.5 py-0.5 bg-[#00d4ff] text-[#0f1419] text-[10px] font-bold rounded-full">
                  {[searchQuery && '1', filterType !== 'all' && '1', filterVerdict !== 'all' && '1', filterIndustry !== 'all' && '1'].filter(Boolean).length}
                </span>
              )}
            </button>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 rounded-xl border border-[#2a3441] text-slate-400 hover:text-white hover:border-slate-500 text-sm transition-colors flex items-center gap-1"
              >
                <X size={14} />
                Сбросить
              </button>
            )}
          </div>

          {/* Панель фильтров */}
          {showFilters && (
            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Тип</label>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(e.target.value as 'all' | 'single' | 'package')}
                    className="w-full px-3 py-2 bg-[#0f1419] border border-[#2a3441] rounded-lg text-white text-sm focus:outline-none focus:border-[#00d4ff]"
                  >
                    <option value="all">Все типы</option>
                    <option value="single">Одиночные</option>
                    <option value="package">Пакеты</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Вердикт</label>
                  <select
                    value={filterVerdict}
                    onChange={(e) => setFilterVerdict(e.target.value as 'all' | VerdictType)}
                    className="w-full px-3 py-2 bg-[#0f1419] border border-[#2a3441] rounded-lg text-white text-sm focus:outline-none focus:border-[#00d4ff]"
                  >
                    <option value="all">Все вердикты</option>
                    <option value="STOP">Не участвовать</option>
                    <option value="CAUTION">Осторожно</option>
                    <option value="PARTICIPATE">Можно участвовать</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1.5">Отрасль</label>
                  <select
                    value={filterIndustry}
                    onChange={(e) => setFilterIndustry(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0f1419] border border-[#2a3441] rounded-lg text-white text-sm focus:outline-none focus:border-[#00d4ff]"
                  >
                    <option value="all">Все отрасли</option>
                    {industries.map(industry => (
                      <option key={industry} value={industry}>{industry}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Счетчик результатов */}
          {hasActiveFilters && (
            <div className="text-xs text-slate-400">
              Найдено: {filteredItems.length} из {items.length}
            </div>
          )}
        </div>
      )}

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400">
          Загружаем историю...
        </div>
      ) : items.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400 text-center max-w-md mx-auto">
          История пока пуста. Выполните анализ документа или пакетный аудит, чтобы увидеть записи.
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400 text-center max-w-md mx-auto">
          По запросу ничего не найдено. Попробуйте изменить фильтры или поисковый запрос.
        </div>
      ) : (
        <div className="flex-1 overflow-auto space-y-3">
          {filteredItems.map((it) => {
            const isExpanded = expandedItems.has(it.id);
            const toggleExpand = () => {
              const newExpanded = new Set(expandedItems);
              if (newExpanded.has(it.id)) {
                newExpanded.delete(it.id);
              } else {
                newExpanded.add(it.id);
              }
              setExpandedItems(newExpanded);
            };

            return (
              <div
                key={it.id}
                className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl overflow-hidden hover:border-[#00d4ff]/30 transition-colors"
              >
                {/* Основная строка */}
                <div
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#2a3441]/30 transition-colors"
                  onClick={toggleExpand}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronUp size={16} className="text-slate-400" />
                      ) : (
                        <ChevronDown size={16} className="text-slate-400" />
                      )}
                    </div>
                    <div className="flex-1 grid grid-cols-5 gap-4 text-sm">
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Дата</p>
                        <p className="text-white">{formatDateTime(it.createdAt)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Тип</p>
                        <p className="text-white">{it.kind === 'package' ? 'Пакет' : 'Один документ'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Файлы</p>
                        <p className="text-white truncate" title={it.files.join(', ')}>
                          {it.files.length} {it.files.length === 1 ? 'файл' : 'файлов'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Балл</p>
                        <p className="text-white font-bold">{Math.round(it.summaryScore)} / 100</p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-400 mb-1">Вердикт</p>
                        <span className={`inline-flex px-2 py-0.5 rounded-full border text-[10px] font-semibold ${verdictBadge(it.verdict)}`}>
                          {verdictLabel(it.verdict)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Раскрытое содержимое с новыми полями */}
                {isExpanded && (
                  <div className="border-t border-[#2a3441] bg-[#0f1419]/50 p-4 space-y-4">
                    {/* Executive Summary */}
                    {it.executive_summary && (
                      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Flame size={16} className="text-[#ff4444]" />
                          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                            Главная проблема
                          </h4>
                        </div>
                        <p className="text-white text-sm leading-relaxed">{it.executive_summary}</p>
                      </div>
                    )}

                    {/* Deal Breakers */}
                    {it.deal_breakers && it.deal_breakers.length > 0 && (
                      <div className="bg-[#ff4444]/10 border border-[#ff4444]/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-3">
                          <AlertTriangle size={16} className="text-[#ff4444]" />
                          <h4 className="text-xs font-bold text-[#ff4444] uppercase tracking-wider">
                            Критические стоп-факторы ({it.deal_breakers.length})
                          </h4>
                        </div>
                        <ul className="space-y-2">
                          {it.deal_breakers.map((breaker, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-white">
                              <span className="text-[#ff4444] mt-1">•</span>
                              <span>{breaker}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Financial Analysis */}
                    {it.financial_analysis && (
                      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                          Финансовый анализ
                        </h4>
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-xs text-slate-400 mb-1">Риск маржинальности</p>
                            <p className={`text-sm font-bold ${
                              it.financial_analysis.margin_risk === 'High' ? 'text-[#ff4444]' :
                              it.financial_analysis.margin_risk === 'Medium' ? 'text-[#f59e0b]' :
                              'text-[#00e648]'
                            }`}>
                              {it.financial_analysis.margin_risk === 'High' ? 'Высокий' :
                               it.financial_analysis.margin_risk === 'Medium' ? 'Средний' :
                               'Низкий'}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-slate-400 mb-1">Риск кассового разрыва</p>
                            <p className={`text-sm font-bold ${
                              it.financial_analysis.cash_gap_risk === 'Yes' ? 'text-[#ff4444]' : 'text-[#00e648]'
                            }`}>
                              {it.financial_analysis.cash_gap_risk === 'Yes' ? 'Есть' : 'Нет'}
                            </p>
                          </div>
                        </div>
                        {it.financial_analysis.reasoning && (
                          <p className="text-xs text-slate-300 mt-3">{it.financial_analysis.reasoning}</p>
                        )}
                      </div>
                    )}

                    {/* Smart Questions */}
                    {it.smart_questions && it.smart_questions.length > 0 && (
                      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-4">
                        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                          Умные вопросы ({it.smart_questions.length})
                        </h4>
                        <ul className="space-y-2">
                          {it.smart_questions.map((question, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-white">
                              <span className="text-[#00d4ff] mt-1 font-bold">{idx + 1}.</span>
                              <span>{question}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Файлы */}
                    <div>
                      <p className="text-xs text-slate-400 mb-2">Файлы:</p>
                      <div className="flex flex-wrap gap-2">
                        {it.files.map((file, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-1 bg-[#0f1419] border border-[#2a3441] rounded text-xs text-slate-300"
                          >
                            {file}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
      <p className="mt-2 text-[10px] text-slate-500">
        Данные истории используются для внутреннего анализа качества тендерной работы и не являются юридически значимыми документами.
      </p>
    </div>
  );
};

export default HistoryView;
