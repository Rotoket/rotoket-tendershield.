import React, { useState } from 'react';
import { analyzePackage, searchLegal, APIErrorException } from '../services/geminiService';
import { PackageAnalysis, PackageDocumentAnalysis, VerdictType, CalculatorPreset } from '../types';
import { AlertTriangle, FileSearch, Loader2, ChevronRight, FileSpreadsheet } from 'lucide-react';
import { logEvent } from '../utils/logger';
import { buildPackageAuditReport } from '../utils/packageReport';
import RateLimitError from './RateLimitError';
import type { APIError } from '../utils/apiErrorHandler';

interface LegalSnippetVm {
  id: string;
  category: string;
  lawReference: string;
  title: string;
  summary: string;
}

const verdictColor = (verdict: VerdictType | string): string => {
  switch (verdict) {
    case 'STOP':
      return 'bg-red-500/10 text-red-400 border-red-500/40';
    case 'CAUTION':
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/40';
    case 'PARTICIPATE':
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/40';
    default:
      return 'bg-slate-700/40 text-slate-200 border-slate-600/60';
  }
};

const blockStatusColor = (status?: string): string => {
  if (!status) return 'bg-slate-800 border-slate-700 text-slate-200';
  const upper = status.toUpperCase();
  if (upper === 'RED') return 'bg-red-500/10 border-red-500/40 text-red-300';
  if (upper === 'YELLOW' || upper === 'ORANGE') return 'bg-yellow-500/10 border-yellow-500/40 text-yellow-300';
  if (upper === 'GREEN') return 'bg-emerald-500/10 border-emerald-500/40 text-emerald-300';
  return 'bg-slate-800 border-slate-700 text-slate-200';
};

interface ComplexAuditProps {
  // Вызывается при выборе документа для передачи параметров в калькулятор
  onSelectForCalculator?: (preset: CalculatorPreset) => void;
  // Открыть экран калькулятора
  onOpenCalculator?: () => void;
}

const ComplexAudit: React.FC<ComplexAuditProps> = ({ onSelectForCalculator, onOpenCalculator }) => {
  const [files, setFiles] = useState<File[]>([]);
  const [industry, setIndustry] = useState<string>('UNIVERSAL');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<PackageAnalysis | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitError, setRateLimitError] = useState<APIError | null>(null);

  // Привязка к базе знаний по выбранному красному флагу
  const [legalFor, setLegalFor] = useState<string | null>(null);
  const [legalResults, setLegalResults] = useState<LegalSnippetVm[]>([]);
  const [isLegalLoading, setIsLegalLoading] = useState(false);
  const [legalError, setLegalError] = useState<string | null>(null);

  const buildPresetFromDoc = (
    pkg: PackageAnalysis,
    doc: PackageDocumentAnalysis,
  ): CalculatorPreset => ({
    source: 'package',
    packageId: pkg.packageId,
    documentName: doc.filename,
    nmck: doc.passport?.nmck || doc.financialSummary?.nmck,
    estimatedCost: doc.financialSummary?.estimatedCost,
    score: doc.score,
  });

  const handleFilesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files;
    if (!selected) return;
    const asArray = Array.from(selected);
    setFiles(asArray);
    setResult(null);
    setError(null);
    logEvent(
      'ComplexAudit',
      `Загружен пакет документов (${asArray.length} шт.) для комплексного аудита`,
      'info',
      asArray.map((f: File) => f.name),
    );
  };

  const handleAnalyze = async () => {
    if (!files.length) {
      setError('Добавьте хотя бы один файл для анализа.');
      return;
    }
    try {
      setIsAnalyzing(true);
      setError(null);
      logEvent(
        'ComplexAudit',
        `Запуск комплексного аудита: файлов ${files.length}, отрасль ${industry}`,
        'info',
        files.map((f) => f.name),
      );
      const data = await analyzePackage(files, industry);
      setResult(data);
      setSelectedIndex(0);
      logEvent(
        'ComplexAudit',
        `Комплексный аудит завершён: пакет ${data.packageId}, итоговый балл ${Math.round(
          data.summaryScore,
        )}/100, вердикт ${data.verdict}`,
      );
      // После первичного анализа сразу подставляем первый документ в калькулятор
      if (onSelectForCalculator && data.documents && data.documents.length > 0) {
        onSelectForCalculator(buildPresetFromDoc(data, data.documents[0]));
      }
    } catch (e: any) {
      console.error('ComplexAudit error:', e);

      // Проверяем, это ошибка лимита или обычная ошибка
      if (e instanceof APIErrorException) {
        const apiError = e.apiError;

        if (apiError.type === 'RATE_LIMIT') {
          setRateLimitError(apiError);
          setError(null);
          logEvent('ComplexAudit', `Превышен лимит: ${apiError.message}`, 'error');
        } else {
          setError(apiError.message || 'Ошибка анализа пакета');
          setRateLimitError(null);
          logEvent('ComplexAudit', `Ошибка анализа: ${apiError.message}`, 'error', e);
        }
      } else {
        setError(e?.message ?? 'Ошибка анализа пакета');
        setRateLimitError(null);
        logEvent('ComplexAudit', 'Ошибка при выполнении комплексного аудита пакета', 'error', e);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedDoc: PackageDocumentAnalysis | null =
    result && result.documents.length > 0 ? result.documents[selectedIndex] : null;

  const handleSelectDoc = (idx: number) => {
    setSelectedIndex(idx);
    if (result && onSelectForCalculator) {
      const doc = result.documents[idx];
      onSelectForCalculator(buildPresetFromDoc(result, doc));
      logEvent('ComplexAudit', `Выбран документ для детального просмотра и калькулятора: ${doc.filename}`);
    }
    // При смене документа сбрасываем панель норм закона
    setLegalFor(null);
    setLegalResults([]);
    setLegalError(null);
  };

  const handleOpenLaw = async (lawRef: string) => {
    if (!lawRef) return;
    setLegalFor(lawRef);
    setIsLegalLoading(true);
    setLegalError(null);
    logEvent('ComplexAudit', `Запрошены нормы закона по ссылке: ${lawRef}`);
    try {
      const data = await searchLegal(lawRef);
      setLegalResults(data.items || []);
      logEvent(
        'ComplexAudit',
        `Нормы закона по ссылке ${lawRef} успешно загружены, найдено элементов: ${data.items?.length ?? 0
        }`,
      );
    } catch (e: any) {
      setLegalError(e?.message ?? 'Ошибка загрузки норм закона');
      setLegalResults([]);
      logEvent('ComplexAudit', `Ошибка загрузки норм закона по ссылке: ${lawRef}`, 'error', e);
    } finally {
      setIsLegalLoading(false);
    }
  };

  // Простейшая проверка согласованности значений между документами
  const getConsistency = (values: (string | undefined | null)[]): 'match' | 'mismatch' | 'unknown' => {
    const normalized = values
      .map((v) => (v || '').toString().trim())
      .filter((v) => v.length > 0);
    if (normalized.length <= 1) return 'unknown';
    const first = normalized[0];
    const allEqual = normalized.every((v) => v === first);
    return allEqual ? 'match' : 'mismatch';
  };

  const handleDownloadReport = () => {
    if (!result) return;

    logEvent(
      'ComplexAudit',
      `Скачивание текстового отчёта по пакету: ${result.packageId}, документов: ${result.documents.length
      }`,
    );

    const reportText = buildPackageAuditReport(result);

    try {
      const blob = new Blob([reportText], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `audit_${result.packageId}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      logEvent('ComplexAudit', 'Текстовый отчёт по пакету успешно сформирован и скачан');
    } catch (e) {
      logEvent('ComplexAudit', 'Ошибка при формировании или скачивании текстового отчёта', 'error', e);
    }
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 h-full text-white">
      {/* Левая колонка: загрузка и итоги по пакету */}
      <div className="w-full md:w-1/3 space-y-4">
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileSearch size={20} className="text-[#00d4ff]" />
              <h2 className="font-semibold text-lg">Комплексный аудит пакета</h2>
            </div>
            {onOpenCalculator && (
              <button
                onClick={() => {
                  logEvent('ComplexAudit', 'Открыт калькулятор из экрана комплексного аудита');
                  onOpenCalculator();
                }}
                className="hidden md:inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-[#00d4ff]/10 border border-[#00d4ff]/60 text-[#00d4ff] text-[11px] font-semibold hover:bg-[#00d4ff]/20 transition-all"
              >
                <FileSpreadsheet size={14} />
                В калькулятор
              </button>
            )}
          </div>
          <p className="text-sm text-slate-400 mb-3">
            Загрузите ТЗ, проект договора и другие документы одним пакетом. Система
            проанализирует каждый документ и выделит глобальные риски по закупке.
          </p>
          <div className="space-y-3">
            <label className="block text-sm text-slate-300">Отрасль закупки</label>
            <select
              disabled={isAnalyzing}
              value={industry}
              onChange={(e) => setIndustry(e.target.value)}
              className="w-full bg-[#020617] border border-[#1f2937] rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#00d4ff]"
            >
              <option value="UNIVERSAL">Универсальная</option>
              <option value="IT">IT / оборудование / ПО</option>
              <option value="CONSTRUCTION">Строительство</option>
              <option value="MEDICINE">Медицина / медизделия</option>
            </select>

            <div className="mt-4">
              <label className="block text-sm text-slate-300 mb-2">Пакет документов</label>
              <input
                type="file"
                multiple
                onChange={handleFilesChange}
                className="block w-full text-sm text-slate-300 file:mr-3 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-[#00d4ff]/10 file:text-[#00d4ff] hover:file:bg-[#00d4ff]/20"
                accept=".pdf,.doc,.docx,.txt,.rtf,.xls,.xlsx"
              />
              <p className="mt-2 text-[10px] text-slate-500">
                Загружая пакет документов, вы подтверждаете законность их использования и соглашаетесь на обработку возможных персональных данных (152-ФЗ). Сервис даёт аналитическую оценку, окончательное решение остаётся за специалистом.
              </p>
              {files.length > 0 && (
                <ul className="mt-3 max-h-32 overflow-y-auto text-xs text-slate-400 space-y-1">
                  {files.map((f, idx) => (
                    <li key={idx} className="truncate">
                      {idx + 1}. {f.name}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !files.length}
              className="mt-4 inline-flex items-center justify-center w-full rounded-lg bg-[#00d4ff] text-slate-900 font-semibold py-2 text-sm hover:bg-[#06b6d4] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="animate-spin mr-2" size={16} /> Анализируем пакет...
                </>
              ) : (
                'Запустить комплексный аудит'
              )}
            </button>

            {rateLimitError && (
              <RateLimitError
                error={rateLimitError}
                onUpgrade={() => {
                  // TODO: Navigate to profile/tariff page
                  setRateLimitError(null);
                }}
              />
            )}
            {error && !rateLimitError && (
              <div className="mt-3 text-xs text-red-400 flex items-start gap-2">
                <AlertTriangle size={14} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </div>

        {result && (
          <div className={`bg-[#111827] border rounded-xl p-4 ${verdictColor(result.verdict)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs uppercase tracking-wide opacity-80">Итог по пакету</span>
              <span className="text-xs">ID: {result.packageId.slice(0, 8)}...</span>
            </div>
            <div className="text-3xl font-bold mb-1">{Math.round(result.summaryScore)} / 100</div>
            <div className="text-sm mb-2">Вердикт: {result.verdict}</div>
            <p className="text-xs text-slate-300 mb-2">
              Балл рассчитывается автоматически, окончательное решение принимает специалист.
            </p>
            <button
              onClick={handleDownloadReport}
              className="mt-1 inline-flex items-center justify-center rounded-lg border border-[#00d4ff]/60 text-[#00d4ff] px-3 py-1 text-[11px] hover:bg-[#00d4ff]/10"
            >
              Скачать отчёт (.txt)
            </button>
          </div>
        )}
      </div>

      {/* Правая часть: список документов и риски */}
      <div className="w-full md:w-2/3 space-y-4 text-sm">
        {result ? (
          <>
            {/* Таблица документов */}
            <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">Документы пакета</h3>
                <span className="text-xs text-slate-400">{result.documents.length} шт.</span>
              </div>
              <div className="divide-y divide-[#1f2937] text-xs">
                {result.documents.map((doc, idx) => (
                  <button
                    key={doc.filename + idx}
                    onClick={() => handleSelectDoc(idx)}
                    className={`w-full flex items-center justify-between py-2 px-2 rounded-md text-left hover:bg-slate-800/60 transition-colors ${idx === selectedIndex ? 'bg-slate-800/80' : ''
                      }`}
                  >
                    <div className="flex items-center gap-2">
                      <ChevronRight
                        size={14}
                        className={idx === selectedIndex ? 'text-[#00d4ff]' : 'text-slate-500'}
                      />
                      <div>
                        <div className="font-medium truncate max-w-[220px]">{doc.filename}</div>
                        <div className="text-[10px] text-slate-400 truncate max-w-[220px]">
                          {doc.summary || 'Краткое резюме не получено'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3 text-right">
                      <span className="text-xs text-slate-400 mr-1">
                        {Math.round(doc.score)} / 100
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-full border text-[10px] ${verdictColor(
                          doc.verdict,
                        )}`}
                      >
                        {doc.verdict}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Глобальные риски */}
            <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle size={18} className="text-[#f97316]" />
                <h3 className="font-semibold text-sm">Глобальные риски по пакету</h3>
              </div>
              {result.globalIssues.length === 0 ? (
                <p className="text-sm text-slate-300">Значимых глобальных несоответствий не найдено.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {result.globalIssues.map((gi, idx) => (
                    <li
                      key={idx}
                      className="border border-slate-700/80 rounded-lg p-2 bg-slate-900/40"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium">{gi.title}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full border border-slate-600 text-slate-200">
                          {gi.severity}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300 mb-1">{gi.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Сквозная сверка данных (матрица противоречий) */}
            {result.documents.length > 1 && (
              <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4">
                <h3 className="font-semibold text-base mb-3">Сквозная сверка данных по комплекту</h3>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                  {/* Деньги (НМЦК) */}
                  <div className="bg-[#020617] border border-slate-700 rounded-lg p-3">
                    <div className="text-[11px] font-bold uppercase tracking-wide text-slate-400 mb-2">
                      💸 Деньги (НМЦК)
                    </div>
                    {(() => {
                      const values = result.documents.map(
                        (doc) => (doc.financialSummary as any)?.nmck || doc.passport?.nmck,
                      );
                      const status = getConsistency(values);
                      return (
                        <div className="mb-2 text-[11px] font-semibold">
                          {status === 'match' && (
                            <span className="text-emerald-400">✅ Данные совпадают между файлами</span>
                          )}
                          {status === 'mismatch' && (
                            <span className="text-red-400">❗ Разные значения НМЦК — нужна проверка</span>
                          )}
                          {status === 'unknown' && (
                            <span className="text-slate-400">Недостаточно данных для сравнения</span>
                          )}
                        </div>
                      );
                    })()}
                    {result.documents.map((doc, idx) => (
                      <div
                        key={doc.filename + idx}
                        className="flex items-center justify-between text-xs py-1 border-b border-slate-800 last:border-0"
                      >
                        <span className="text-slate-400 truncate max-w-[60%]">{doc.filename}</span>
                        <span className="font-semibold text-slate-100">
                          {(doc.financialSummary as any)?.nmck || doc.passport?.nmck || '—'}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Сроки исполнения */}
                  <div className="bg-[#020617] border border-slate-700 rounded-lg p-3">
                    <div className="text-[11px] font-bold uppercase tracking-wide text-slate-400 mb-2">
                      ⏳ Сроки исполнения
                    </div>
                    {(() => {
                      const values = result.documents.map(
                        (doc) =>
                          (doc.timelineSummary as any)?.deadlineExecution ||
                          doc.passport?.deadlineExecution,
                      );
                      const status = getConsistency(values);
                      return (
                        <div className="mb-2 text-[11px] font-semibold">
                          {status === 'match' && (
                            <span className="text-emerald-400">✅ Сроки согласованы между документами</span>
                          )}
                          {status === 'mismatch' && (
                            <span className="text-red-400">
                              ❗ Расхождение в сроках — рекомендуется запрос разъяснений
                            </span>
                          )}
                          {status === 'unknown' && (
                            <span className="text-slate-400">Недостаточно данных для сравнения</span>
                          )}
                        </div>
                      );
                    })()}
                    {result.documents.map((doc, idx) => (
                      <div
                        key={doc.filename + idx}
                        className="flex items-center justify-between text-xs py-1 border-b border-slate-800 last:border-0"
                      >
                        <span className="text-slate-400 truncate max-w-[60%]">{doc.filename}</span>
                        <span className="font-semibold text-slate-100">
                          {(doc.timelineSummary as any)?.deadlineExecution ||
                            doc.passport?.deadlineExecution ||
                            '—'}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Обеспечение */}
                  <div className="bg-[#020617] border border-slate-700 rounded-lg p-3">
                    <div className="text-[11px] font-bold uppercase tracking-wide text-slate-400 mb-2">
                      🔒 Обеспечение
                    </div>
                    {(() => {
                      const values = result.documents.map(
                        (doc) =>
                          (doc.financialSummary as any)?.contractSecurity ||
                          doc.passport?.contractSecurity,
                      );
                      const status = getConsistency(values);
                      return (
                        <div className="mb-2 text-[11px] font-semibold">
                          {status === 'match' && (
                            <span className="text-emerald-400">✅ Условия обеспечения совпадают</span>
                          )}
                          {status === 'mismatch' && (
                            <span className="text-red-400">
                              ❗ Разные условия обеспечения — возможное противоречие
                            </span>
                          )}
                          {status === 'unknown' && (
                            <span className="text-slate-400">Недостаточно данных для сравнения</span>
                          )}
                        </div>
                      );
                    })()}
                    {result.documents.map((doc, idx) => (
                      <div
                        key={doc.filename + idx}
                        className="flex items-center justify-between text-xs py-1 border-b border-slate-800 last:border-0"
                      >
                        <span className="text-slate-400 truncate max-w-[60%]">{doc.filename}</span>
                        <span className="font-semibold text-slate-100">
                          {(doc.financialSummary as any)?.contractSecurity ||
                            doc.passport?.contractSecurity ||
                            '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Детали выбранного документа */}
            {selectedDoc && (
              <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4">
                <h3 className="font-semibold text-sm mb-2">Детальный анализ: {selectedDoc.filename}</h3>
                <p className="text-xs text-slate-300 mb-3">{selectedDoc.summary}</p>

                {/* Сводка по 4 ключевым блокам: Деньги / Время / Барьеры / Ловушки */}
                {selectedDoc.summaryBlocks && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] mb-4">
                    {(['money', 'time', 'barriers', 'traps'] as const).map((key) => {
                      const block = (selectedDoc.summaryBlocks as any)[key];
                      if (!block) return null;
                      const titleMap: Record<string, string> = {
                        money: 'Деньги',
                        time: 'Время',
                        barriers: 'Барьеры',
                        traps: 'Ловушки',
                      };
                      return (
                        <div
                          key={key}
                          className={`rounded-lg border px-3 py-2 ${blockStatusColor(block.status)} flex flex-col gap-1`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold">{titleMap[key]}</span>
                            {block.status && (
                              <span className="text-[10px] uppercase tracking-wide opacity-80">
                                {block.status}
                              </span>
                            )}
                          </div>
                          {block.comment && (
                            <p className="text-[10px] leading-snug text-slate-200">{block.comment}</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs mb-3">
                  <div>
                    <div className="text-slate-400 mb-1">НМЦК</div>
                    <div className="font-medium">{selectedDoc.passport?.nmck ?? '—'}</div>
                  </div>
                  <div>
                    <div className="text-slate-400 mb-1">Закон</div>
                    <div className="font-medium">{selectedDoc.passport?.fz ?? '—'}</div>
                  </div>
                  <div>
                    <div className="text-slate-400 mb-1">Регион / место</div>
                    <div className="font-medium">{selectedDoc.passport?.region ?? '—'}</div>
                  </div>
                </div>

                {/* Основные риски по документу */}
                <div className="mt-3 space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle size={14} className="text-[#f97316]" />
                      <span className="text-xs font-semibold">Риски документа</span>
                    </div>
                    {selectedDoc.issues.length === 0 ? (
                      <p className="text-xs text-slate-400">Явные риски в тексте документа не найдены.</p>
                    ) : (
                      <ul className="space-y-1 text-xs max-h-40 overflow-y-auto">
                        {selectedDoc.issues.slice(0, 10).map((iss, idx) => (
                          <li
                            key={idx}
                            className="border border-slate-700/80 rounded-md p-2 bg-slate-900/40"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium truncate max-w-[220px]">
                                {iss.title}
                              </span>
                              {iss.severity && (
                                <span className="text-[10px] text-slate-300 ml-2">
                                  {iss.severity}
                                </span>
                              )}
                            </div>
                            {iss.description && (
                              <p className="text-[11px] text-slate-300 mb-1">{iss.description}</p>
                            )}
                            {iss.quote && (
                              <p className="text-[10px] text-slate-400 italic truncate max-h-10">
                                "{iss.quote}"
                              </p>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Красные флаги и нарушения */}
                  {selectedDoc.redFlags && selectedDoc.redFlags.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle size={14} className="text-red-400" />
                        <span className="text-xs font-semibold">Красные флаги и возможные нарушения</span>
                      </div>
                      <ul className="space-y-1 text-xs max-h-40 overflow-y-auto">
                        {selectedDoc.redFlags.slice(0, 10).map((rf, idx) => (
                          <li
                            key={idx}
                            className="border border-red-500/40 rounded-md p-2 bg-red-950/20"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <span className="font-medium truncate max-w-[220px]">
                                {rf.title}
                              </span>
                              <span className="text-[10px] text-red-300 ml-2">
                                {rf.severity}
                              </span>
                            </div>
                            {rf.lawReference && (
                              <button
                                type="button"
                                onClick={() => handleOpenLaw(rf.lawReference!)}
                                className="text-[10px] text-red-200 mb-1 underline underline-offset-2 decoration-dotted hover:text-red-100 text-left"
                              >
                                Норма: {rf.lawReference}
                              </button>
                            )}
                            {rf.explanation && (
                              <p className="text-[11px] text-slate-200 mb-1">{rf.explanation}</p>
                            )}
                            {rf.quote && (
                              <p className="text-[10px] text-slate-400 italic truncate max-h-10">
                                "{rf.quote}"
                              </p>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Связанные нормы закона из базы знаний */}
                  {legalFor && (
                    <div className="mt-3 border border-[#1f2937] rounded-lg bg-slate-900/40 p-3 text-[11px]">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-100">Нормы закона по ссылке: {legalFor}</span>
                        {isLegalLoading && (
                          <span className="text-[10px] text-slate-400">Загрузка...</span>
                        )}
                      </div>
                      {legalError && (
                        <div className="text-[10px] text-red-400">{legalError}</div>
                      )}
                      {!isLegalLoading && !legalError && legalResults.length === 0 && (
                        <div className="text-[10px] text-slate-400">
                          Подходящие выдержки в базе знаний не найдены. Уточните формулировку или откройте раздел «База знаний».
                        </div>
                      )}
                      {!isLegalLoading && !legalError && legalResults.length > 0 && (
                        <ul className="space-y-1 mt-1">
                          {legalResults.slice(0, 3).map((snip) => (
                            <li
                              key={snip.id}
                              className="border border-[#1f2937] rounded-md p-2 bg-slate-950/40"
                            >
                              <div className="flex items-center justify-between mb-0.5">
                                <span className="font-semibold text-slate-100 truncate mr-2">
                                  {snip.title}
                                </span>
                                <span className="text-[9px] text-slate-400">
                                  {snip.lawReference}
                                </span>
                              </div>
                              <div className="text-[10px] text-slate-400 mb-0.5">{snip.category}</div>
                              <p className="text-[10px] text-slate-200 whitespace-pre-line max-h-24 overflow-y-auto">
                                {snip.summary}
                              </p>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}

                  {/* Финансовая сводка */}
                  {selectedDoc.financialSummary && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <div className="text-slate-400 mb-1">Финансовая сводка</div>
                        <div className="text-[11px] text-slate-300 whitespace-pre-line">
                          {selectedDoc.financialSummary.nmck}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Оценочная себестоимость</div>
                        <div className="text-[11px] text-slate-300 whitespace-pre-line">
                          {selectedDoc.financialSummary.estimatedCost || '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Комментарий по марже</div>
                        <div className="text-[11px] text-slate-300 whitespace-pre-line">
                          {selectedDoc.financialSummary.marginComment || '—'}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Сводка по срокам */}
                  {selectedDoc.timelineSummary && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                      <div>
                        <div className="text-slate-400 mb-1">Подача заявки</div>
                        <div className="font-medium">
                          {selectedDoc.timelineSummary.deadlineApp || '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Исполнение контракта</div>
                        <div className="font-medium">
                          {selectedDoc.timelineSummary.deadlineExecution || '—'}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-400 mb-1">Оценка сроков</div>
                        <div className="text-[11px] text-slate-300 whitespace-pre-line">
                          {selectedDoc.timelineSummary.timelineRisk || '—'}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Рекомендуемые действия */}
                  {selectedDoc.actions && selectedDoc.actions.length > 0 && (
                    <div>
                      <div className="text-xs font-semibold mb-1">Рекомендуемые шаги</div>
                      <ul className="list-disc list-inside text-[11px] text-slate-300 space-y-1">
                        {selectedDoc.actions
                          .slice()
                          .sort((a: any, b: any) => (a.priority || 0) - (b.priority || 0))
                          .map((act: any, idx: number) => (
                            <li key={idx}>{act.text}</li>
                          ))}
                      </ul>
                    </div>
                  )}

                  {/* Структурированные ответы на 25 вопросов */}
                  {selectedDoc.structuredAnswers && Object.keys(selectedDoc.structuredAnswers).length > 0 && (
                    <div className="mt-4 border border-[#1f2937] rounded-lg bg-slate-900/40 p-3">
                      <div className="flex items-center gap-2 mb-3">
                        <FileSpreadsheet size={14} className="text-[#00d4ff]" />
                        <span className="text-xs font-semibold">Структурированный анализ по чек-листу</span>
                      </div>
                      <div className="space-y-2 text-xs max-h-96 overflow-y-auto">
                        {[
                          { key: 'customer', label: '1. Заказчик (ИНН, ОГРН, местонахождение)' },
                          { key: 'subject', label: '2. Предмет закупки' },
                          { key: 'nmck', label: '3. Начальная (максимальная) цена контракта' },
                          { key: 'applicationDeadline', label: '4. Сроки подачи заявок' },
                          { key: 'executionDeadline', label: '5. Сроки исполнения контракта' },
                          { key: 'participantRequirements', label: '6. Требования к участникам' },
                          { key: 'securityAmounts', label: '7. Обеспечительные суммы' },
                          { key: 'paymentTerms', label: '8. Условия оплаты' },
                          { key: 'evaluationCriteria', label: '9. Критерии оценки заявок' },
                          { key: 'contradictions', label: '10. Противоречия и неоднозначности' },
                          { key: 'penalties', label: '11. Штрафы и санкции' },
                          { key: 'guarantees', label: '12. Гарантии и сервисное обслуживание' },
                          { key: 'additionalRequirements', label: '13. Дополнительные требования' },
                          { key: 'tenderRisks', label: '14. Риски изменения/отмены тендера' },
                          { key: 'documentationRequirements', label: '15. Требования по оформлению документов' },
                          { key: 'financialRequirements', label: '16. Требования к финансовому положению' },
                          { key: 'confidentiality', label: '17. Условия конфиденциальности' },
                          { key: 'customerHistory', label: '18. История заказчика' },
                          { key: 'subcontractingLimits', label: '19. Ограничения по субподряду' },
                          { key: 'conflictsOfInterest', label: '20. Конфликты интересов' },
                          { key: 'discriminationSigns', label: '21. Признаки дискриминации' },
                          { key: 'terminationConditions', label: '22. Условия расторжения и изменения' },
                          { key: 'competitionLevel', label: '23. Уровень конкуренции' },
                          { key: 'insuranceRequirements', label: '24. Требования к страхованию' },
                          { key: 'additionalRisks', label: '25. Дополнительные риски и особенности' },
                        ].map(({ key, label }) => {
                          const answer = selectedDoc.structuredAnswers?.[key as keyof typeof selectedDoc.structuredAnswers];
                          if (!answer || answer === 'Не указано' || answer === 'Не найдено') return null;
                          return (
                            <div key={key} className="border border-slate-700/80 rounded-md p-2 bg-slate-950/40">
                              <div className="text-[10px] font-semibold text-slate-400 mb-1">{label}</div>
                              <div className="text-[11px] text-slate-200 leading-relaxed whitespace-pre-line">{answer}</div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <p className="mt-3 text-[10px] text-slate-500">
                    Система даёт аналитическую оценку и рекомендации. Решение об участии и
                    ответственность остаются за специалистом.
                  </p>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="h-full flex items-center justify-center text-slate-500 text-sm text-center max-w-md mx-auto">
            Загрузите пакет документов слева и запустите анализ, чтобы увидеть предварительную
            оценку рисков по закупке. Окончательное решение всегда принимает специалист.
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplexAudit;
