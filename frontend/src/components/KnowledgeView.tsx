import React, { useState } from 'react';
import { searchLegal } from '../services/geminiService';
import { BookOpen, Search } from 'lucide-react';
import { logEvent } from '../utils/logger';

interface LegalSnippetVm {
  id: string;
  category: string;
  lawReference: string;
  title: string;
  summary: string;
}

const KnowledgeView: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<LegalSnippetVm[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    try {
      setIsLoading(true);
      setError(null);
      logEvent('Knowledge', `Поиск по базе знаний: "${trimmed}"`);
      const data = await searchLegal(trimmed);
      setResults(data.items || []);
      logEvent('Knowledge', `Результаты поиска получены, элементов: ${data.items?.length ?? 0}`);
    } catch (e: any) {
      setError(e?.message ?? 'Ошибка поиска по базе знаний');
      logEvent('Knowledge', 'Ошибка при поиске по базе знаний', 'error', e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col text-white">
      <div className="flex items-center gap-2 mb-1">
        <BookOpen size={20} className="text-[#00d4ff]" />
        <h2 className="text-lg font-semibold">База знаний</h2>
      </div>
      <p className="mb-4 text-xs text-slate-400 max-w-2xl">
        Подборка норм 44-ФЗ, 223-ФЗ, 135-ФЗ, 152-ФЗ и типовой практики для быстрой навигации по рискам. Материалы носят справочный характер и не заменяют консультацию юриста.
      </p>

      <form onSubmit={handleSearch} className="mb-4 flex gap-2">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Введите норму или ситуацию (например, 'ограничение конкуренции по бренду')"
            className="w-full bg-[#020617] border border-[#1f2937] rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#00d4ff] text-white placeholder:text-slate-500"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="px-4 py-2 rounded-lg bg-[#00d4ff] text-slate-900 text-sm font-semibold hover:bg-[#06b6d4] disabled:opacity-60"
        >
          Найти
        </button>
      </form>

      {error && <div className="mb-3 text-xs text-red-400">{error}</div>}

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400">
          Поиск по базе знаний...
        </div>
      ) : results.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-slate-400 text-center max-w-md mx-auto">
          Введите запрос, чтобы найти релевантные нормы закона и типовые ситуации.
        </div>
      ) : (
        <div className="flex-1 overflow-auto border border-[#1f2937] rounded-xl bg-[#111827] p-4 space-y-3 text-xs">
          {results.map((r) => (
            <div key={r.id} className="border border-[#1f2937] rounded-lg p-3 bg-slate-900/40">
              <div className="flex items-center justify-between mb-1">
                <span className="font-semibold">{r.title}</span>
                <span className="text-[10px] text-slate-300 ml-2">{r.lawReference}</span>
              </div>
              <div className="text-[11px] text-slate-400 mb-1">{r.category}</div>
              <p className="text-[11px] text-slate-200 whitespace-pre-line">{r.summary}</p>
            </div>
          ))}
        </div>
      )}
      <p className="mt-2 text-[10px] text-slate-500">
        При принятии решений опирайтесь на официальные тексты законов и разъяснения уполномоченных органов. Сервис помогает с навигацией, но не подменяет эксперта.
      </p>
    </div>
  );
};

export default KnowledgeView;