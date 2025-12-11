import React, { useState } from 'react';
import { CalculatorPreset, AnalysisResult } from '../types';
import { analyzeFromZakupki } from '../services/geminiService';
import { logEvent } from '../utils/logger';
import { APIErrorException } from '../services/geminiService';
import type { APIError } from '../utils/apiErrorHandler';
import ComplexAudit from './ComplexAudit';
import TenderHubDashboard from './TenderHubDashboard';
import { buildSingleHubFromAnalysis } from '../utils/hubBuilders';
import { FileSearch, Hash } from 'lucide-react';

interface TenderAnalysisViewProps {
  onSelectForCalculator?: (preset: CalculatorPreset) => void;
  onOpenCalculator?: () => void;
  onOpenGenerator?: () => void;
}

export const TenderAnalysisView: React.FC<TenderAnalysisViewProps> = ({
  onSelectForCalculator,
  onOpenCalculator,
  onOpenGenerator,
}) => {
  const [mode, setMode] = useState<'zakupki' | 'files'>('zakupki');

  // Состояние для анализа по номеру закупки
  const [tenderId, setTenderId] = useState('');
  const [isLoadingZakupki, setIsLoadingZakupki] = useState(false);
  const [zakupkiResult, setZakupkiResult] = useState<AnalysisResult | null>(null);
  const [zakupkiError, setZakupkiError] = useState<string | null>(null);
  const [zakupkiRateLimitError, setZakupkiRateLimitError] = useState<APIError | null>(null);

  const handleAnalyzeZakupki = async () => {
    const trimmed = tenderId.trim();
    if (!trimmed) {
      setZakupkiError('Введите номер закупки в ЕИС.');
      return;
    }

    try {
      setIsLoadingZakupki(true);
      setZakupkiError(null);
      setZakupkiRateLimitError(null);
      setZakupkiResult(null);

      logEvent('TenderAnalysis', `Запуск анализа по номеру закупки: ${trimmed}`);
      const result = await analyzeFromZakupki(trimmed);

      const hub = buildSingleHubFromAnalysis(result);
      const enriched: AnalysisResult = { ...result, hub };
      setZakupkiResult(enriched);

      logEvent(
        'TenderAnalysis',
        `Анализ закупки ${trimmed} завершён: индекс безопасности ${result.score}/100, вердикт ${result.verdict}`,
      );
    } catch (e: any) {
      console.error('Zakupki analysis error:', e);
      if (e instanceof APIErrorException) {
        const apiError = e.apiError;
        if (apiError.type === 'RATE_LIMIT') {
          setZakupkiRateLimitError(apiError);
          setZakupkiError(null);
          logEvent('TenderAnalysis', `Превышен лимит при анализе по номеру закупки: ${apiError.message}`, 'error');
        } else {
          setZakupkiError(apiError.message || 'Ошибка анализа по номеру закупки');
          logEvent('TenderAnalysis', `Ошибка анализа по номеру закупки: ${apiError.message}`, 'error');
        }
      } else {
        setZakupkiError(e?.message ?? 'Ошибка анализа по номеру закупки');
        logEvent('TenderAnalysis', 'Непредвиденная ошибка анализа по номеру закупки', 'error', e);
      }
    } finally {
      setIsLoadingZakupki(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Переключатель режимов */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h2 className="text-3xl font-bold text-white mb-1">Анализ тендера</h2>
          <p className="text-slate-400 text-sm">
            Введите номер закупки из ЕИС или загрузите комплект документов. Система выполнит универсальный аудит с
            рекомендациями.
          </p>
        </div>
        <div className="inline-flex bg-[#1a1f2e] border border-[#2a3441] rounded-xl overflow-hidden text-xs font-semibold">
          <button
            type="button"
            onClick={() => setMode('zakupki')}
            className={`px-4 py-2 flex items-center gap-2 transition-colors ${
              mode === 'zakupki' ? 'bg-[#00d4ff] text-[#0f1419]' : 'text-slate-300 hover:bg-[#111827]'
            }`}
          >
            <Hash size={14} />
            По номеру закупки
          </button>
          <button
            type="button"
            onClick={() => setMode('files')}
            className={`px-4 py-2 flex items-center gap-2 border-l border-[#2a3441] transition-colors ${
              mode === 'files' ? 'bg-[#00d4ff] text-[#0f1419]' : 'text-slate-300 hover:bg-[#111827]'
            }`}
          >
            <FileSearch size={14} />
            По документам
          </button>
        </div>
      </div>

      {mode === 'zakupki' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Левая колонка: ввод номера закупки */}
          <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 space-y-3">
            <div className="text-sm font-semibold text-slate-200 flex items-center gap-2 mb-1">
              <Hash size={16} className="text-[#00d4ff]" />
              <span>Анализ по номеру закупки (EIS / zakupki.gov.ru)</span>
            </div>
            <p className="text-xs text-slate-400">
              Введите регистрационный номер закупки, например <span className="font-mono">0361500000525000170</span>.
              Сервис попытается автоматически получить документы из ЕИС и выполнить анализ.
            </p>
            <div className="space-y-2">
              <label className="text-xs text-slate-400">Номер закупки</label>
              <input
                type="text"
                value={tenderId}
                onChange={(e) => setTenderId(e.target.value)}
                placeholder="Например, 0361500000525000170"
                className="w-full bg-[#020617] border border-[#1f2937] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-[#00d4ff]"
              />
            </div>
            <button
              type="button"
              onClick={handleAnalyzeZakupki}
              disabled={isLoadingZakupki || !tenderId.trim()}
              className="inline-flex items-center justify-center w-full rounded-lg bg-[#00d4ff] text-slate-900 font-semibold py-2 text-sm hover:bg-[#06b6d4] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isLoadingZakupki ? 'Анализируем закупку...' : 'Проанализировать по номеру'}
            </button>
            {zakupkiError && (
              <div className="text-xs text-red-400 mt-2">{zakupkiError}</div>
            )}
            {zakupkiRateLimitError && (
              <div className="text-xs text-red-400 mt-2">
                {zakupkiRateLimitError.message || 'Превышен лимит запросов, попробуйте позже.'}
              </div>
            )}
            <p className="text-[10px] text-slate-500 mt-2">
              Использование интеграции с zakupki.gov.ru подчиняется правилам сайта. Сервис загружает только необходимые
              для анализа документы, не изменяя их.
            </p>
          </div>

          {/* Правая часть: результат анализа по номеру закупки */}
          <div className="lg:col-span-2">
            {zakupkiResult ? (
              <div className="space-y-4">
                {zakupkiResult.hub && (
                  <TenderHubDashboard
                    result={zakupkiResult}
                    hub={zakupkiResult.hub}
                    onSelectForCalculator={onSelectForCalculator}
                    onOpenCalculator={onOpenCalculator}
                    onOpenGenerator={onOpenGenerator}
                  />
                )}
                {!zakupkiResult.hub && (
                  <TenderHubDashboard
                    result={zakupkiResult}
                    hub={buildSingleHubFromAnalysis(zakupkiResult)}
                    onSelectForCalculator={onSelectForCalculator}
                    onOpenCalculator={onOpenCalculator}
                    onOpenGenerator={onOpenGenerator}
                  />
                )}
                <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 text-xs text-slate-200">
                  <h3 className="font-semibold text-sm mb-2">Краткое резюме закупки</h3>
                  <p className="mb-2 whitespace-pre-line">{zakupkiResult.summary}</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2 text-[11px]">
                    <div>
                      <div className="text-slate-400 mb-1">НМЦК</div>
                      <div className="font-mono">{zakupkiResult.passport.nmck}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 mb-1">Закон</div>
                      <div>{zakupkiResult.passport.fz}</div>
                    </div>
                    <div>
                      <div className="text-slate-400 mb-1">Регион</div>
                      <div>{zakupkiResult.passport.region}</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-500 border border-dashed border-[#1f2937] rounded-xl bg-[#020617]/40 p-6">
                Введите номер закупки слева и запустите анализ, чтобы увидеть сводку по тендеру.
              </div>
            )}
          </div>
        </div>
      )}

      {mode === 'files' && (
        <ComplexAudit onSelectForCalculator={onSelectForCalculator} onOpenCalculator={onOpenCalculator} />
      )}
    </div>
  );
};

export default TenderAnalysisView;
