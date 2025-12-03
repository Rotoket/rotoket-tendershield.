import React, { useEffect, useState, useMemo } from 'react';
import { AuditHistoryItem, VerdictType } from '../types';
import { fetchAuditHistory } from '../services/geminiService';
import { Clock, Search, Filter, X, Eye } from 'lucide-react';
import { logEvent } from '../utils/logger';

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
                    <option value="STOP">STOP</option>
                    <option value="CAUTION">CAUTION</option>
                    <option value="PARTICIPATE">PARTICIPATE</option>
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
        <div className="flex-1 overflow-auto border border-[#1f2937] rounded-xl bg-[#111827]">
          <table className="w-full text-xs text-left">
            <thead className="bg-[#020617] text-slate-300 sticky top-0">
              <tr>
                <th className="px-3 py-2 border-b border-[#1f2937]">Дата и время</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Тип</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Отрасль</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Файлы</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Балл</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Вердикт</th>
                <th className="px-3 py-2 border-b border-[#1f2937]">Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.map((it) => (
                <tr key={it.id} className="hover:bg-slate-800/60 cursor-pointer">
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    {formatDateTime(it.createdAt)}
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    {it.kind === 'package' ? 'Пакет' : 'Один документ'}
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    {it.industry}
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top max-w-xs">
                    <div className="truncate" title={it.files.join(', ')}>
                      {it.files.join(', ')}
                    </div>
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    {Math.round(it.summaryScore)} / 100
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    <span className={`inline-flex px-2 py-0.5 rounded-full border text-[10px] font-semibold ${verdictBadge(it.verdict)}`}>
                      {it.verdict}
                    </span>
                  </td>
                  <td className="px-3 py-2 border-b border-[#1f2937] align-top">
                    <button
                      onClick={() => {
                        logEvent('History', `Просмотр деталей анализа: ${it.id}`);
                        // TODO: Открыть модальное окно с деталями или перейти на страницу анализа
                        alert(`Просмотр анализа ${it.id} - будет реализовано далее`);
                      }}
                      className="text-[#00d4ff] hover:text-[#33e0ff] transition-colors flex items-center gap-1 text-xs"
                      title="Просмотреть детали"
                    >
                      <Eye size={14} />
                      Просмотр
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="mt-2 text-[10px] text-slate-500">
        Данные истории используются для внутреннего анализа качества тендерной работы и не являются юридически значимыми документами.
      </p>
    </div>
  );
};

export default HistoryView;
