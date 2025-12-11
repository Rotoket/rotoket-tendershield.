import React, { useState, useRef, useEffect } from 'react';
import { analyzePackage, searchLegal, APIErrorException, chatWithSinaps } from '../services/geminiService';
import { PackageAnalysis, PackageDocumentAnalysis, VerdictType, CalculatorPreset, ChatMessage } from '../types';
import { AlertTriangle, FileSearch, Loader2, ChevronRight, FileSpreadsheet, Zap, ArrowRight, Upload, Eye, EyeOff, X } from 'lucide-react';
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

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!files.length && messages.length === 0) {
      setMessages([{
        id: 'init',
        role: 'model',
        text: 'Здравствуйте! Я готов к работе. Загрузите пакет документов для комплексного аудита, и я проведу детальный анализ всех документов.',
        timestamp: new Date()
      }]);
    }
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
    // Добавляем новые файлы к существующим (если они есть)
    setFiles(prevFiles => {
      const newFiles = [...prevFiles, ...asArray];
      // Убираем дубликаты по имени и размеру
      const uniqueFiles = newFiles.filter((file, index, self) =>
        index === self.findIndex(f => f.name === file.name && f.size === file.size)
      );
      return uniqueFiles;
    });
    setResult(null);
    setError(null);
    logEvent(
      'ComplexAudit',
      `Загружено ${asArray.length} файл(ов) для комплексного аудита (всего: ${files.length + asArray.length})`,
      'info',
      asArray.map((f: File) => f.name),
    );
    // Сбрасываем input, чтобы можно было загрузить тот же файл снова
    event.target.value = '';
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

  const handleSendMessage = async () => {
    if (!inputMsg.trim()) return;
    const newMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: inputMsg,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, newMsg]);
    logEvent('ComplexAudit', 'Отправлен вопрос в чат Sinaps AI из комплексного аудита', 'info');
    setInputMsg('');
    try {
      const response = await chatWithSinaps(messages, newMsg.text);
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'model',
          text: response || 'Ошибка',
          timestamp: new Date(),
        },
      ]);
      logEvent('ComplexAudit', 'Получен ответ от чата Sinaps AI', 'info');
    } catch (err) {
      console.error('Chat error', err);
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'model',
          text: 'Произошла ошибка при обращении к чату.',
          timestamp: new Date(),
        },
      ]);
      logEvent('ComplexAudit', 'Ошибка при обращении к чату Sinaps AI', 'error', err);
    }
  };

  return (
    <div className="flex h-full gap-6 flex-col animate-fade-in">
      {/* Header & Industry Selector */}
      <div className="flex justify-between items-end mb-2">
        <div>
          <h2 className="text-3xl font-bold text-white mb-1">Комплексный аудит тендера</h2>
          <p className="text-slate-400 text-sm">Загрузите пакет документов для комплексного анализа</p>
        </div>

        {/* INDUSTRY SELECTOR UI - только Универсальный */}
        <div className="flex bg-[#1a1f2e] px-4 py-2 rounded-xl border border-[#2a3441]">
          <span className="text-sm font-bold text-[#00d4ff]">Универсальный</span>
        </div>
      </div>

      <div className="flex h-full gap-6 overflow-hidden">
        {/* LEFT: Analysis Content */}
        <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar pb-20">
          {/* Rate Limit Error Display */}
          {rateLimitError && (
            <RateLimitError
              error={rateLimitError}
              onUpgrade={() => {
                setRateLimitError(null);
              }}
            />
          )}

          {!files.length ? (
            <div className="relative border-2 border-dashed border-[#2a3441] bg-[#1a1f2e]/50 rounded-2xl p-12 text-center hover:border-[#00d4ff] transition-all cursor-pointer flex flex-col items-center justify-center flex-1 min-h-[400px]">
              <input
                type="file"
                multiple
                className="absolute inset-0 opacity-0 cursor-pointer z-10 w-full h-full"
                onChange={handleFilesChange}
                accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
              />
              <div className="relative mb-8">
                <div className="absolute inset-0 bg-[#00d4ff] blur-[40px] opacity-20 rounded-full"></div>
                <div className="inline-flex items-center justify-center w-24 h-24 bg-[#1a1f2e] rounded-2xl border border-[#2a3441] shadow-2xl relative z-10">
                  <Upload className="text-[#00d4ff]" size={40} />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">Загрузите пакет документов</h3>
              <p className="text-slate-400 max-w-md mx-auto leading-relaxed mb-4">
                Поддерживаются форматы PDF, DOCX/DOC, TXT, RTF, XLS/XLSX. <br />
                Можно загрузить несколько файлов одновременно.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/20 text-xs font-bold">
                Активный профиль: {industry === 'UNIVERSAL' ? 'Универсальный' : industry === 'IT' ? 'IT и ПО' : industry === 'CONSTRUCTION' ? 'Строительство' : 'Медицина'}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* File Cards */}
              <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-bold">Загруженные документы ({files.length})</h3>
                  <div className="flex items-center gap-2">
                    <label className="relative cursor-pointer">
                      <input
                        type="file"
                        multiple
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        onChange={handleFilesChange}
                        accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
                      />
                      <button
                        className="px-3 py-1.5 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-lg text-xs font-bold transition-colors"
                      >
                        + Добавить файлы
                      </button>
                    </label>
                    <button
                      onClick={() => { setFiles([]); setResult(null); setError(null); }}
                      className="p-2 hover:bg-[#2a3441] rounded-lg transition-colors text-slate-400 hover:text-white"
                      title="Очистить все файлы"
                    >
                      <X size={20} />
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  {files.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-[#0f1419] rounded-lg border border-[#2a3441]">
                      <FileSearch className="text-[#00d4ff]" size={20} />
                      <div className="flex-1">
                        <p className="text-white text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button
                        onClick={() => {
                          const newFiles = files.filter((_, i) => i !== idx);
                          setFiles(newFiles);
                          if (newFiles.length === 0) {
                            setResult(null);
                            setError(null);
                          }
                        }}
                        className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400 transition-colors"
                        title="Удалить файл"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !files.length}
                  className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Анализируем пакет...
                    </>
                  ) : (
                    <>
                      Запустить комплексный аудит <ArrowRight size={20} />
                    </>
                  )}
                </button>
              </div>

              {error && !rateLimitError && (
                <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
                  <AlertTriangle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                  <p className="text-red-400 text-sm">{error}</p>
                </div>
              )}
            </div>
          )}

          {result && (
            <div className="animate-fade-in space-y-6">
              {/* Package Summary Card */}
              <div className={`bg-[#1a1f2e] border rounded-2xl p-6 ${verdictColor(result.verdict)}`}>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs uppercase tracking-wide opacity-80">Итог по пакету</span>
                  <span className="text-xs opacity-60">ID: {result.packageId.slice(0, 8)}...</span>
                </div>
                <div className="text-4xl font-bold mb-2">{Math.round(result.summaryScore)} / 100</div>
                <div className="text-base mb-3">Вердикт: {result.verdict}</div>
                <p className="text-sm text-slate-300 mb-4">
                  Балл рассчитывается автоматически, окончательное решение принимает специалист.
                </p>
                <button
                  onClick={handleDownloadReport}
                  className="inline-flex items-center justify-center rounded-lg border border-[#00d4ff]/60 text-[#00d4ff] px-4 py-2 text-sm hover:bg-[#00d4ff]/10 transition-colors"
                >
                  <FileSpreadsheet size={16} className="mr-2" />
                  Скачать отчёт (.txt)
                </button>
              </div>
              {/* Documents List */}
              <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl overflow-hidden">
                <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441] flex items-center justify-between">
                  <h3 className="text-white font-bold flex items-center gap-2">
                    <FileSearch className="text-[#00d4ff]" size={20} /> Документы пакета
                  </h3>
                  <span className="text-xs text-slate-400">{result.documents.length} шт.</span>
                </div>
                <div className="divide-y divide-[#2a3441]">
                  {result.documents.map((doc, idx) => (
                    <button
                      key={doc.filename + idx}
                      onClick={() => handleSelectDoc(idx)}
                      className={`w-full flex items-center justify-between py-4 px-6 text-left hover:bg-[#2a3441]/50 transition-colors ${idx === selectedIndex ? 'bg-[#2a3441] border-l-4 border-[#00d4ff]' : ''
                        }`}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <ChevronRight
                          size={16}
                          className={idx === selectedIndex ? 'text-[#00d4ff]' : 'text-slate-500'}
                        />
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-white truncate mb-1">{doc.filename}</div>
                          <div className="text-xs text-slate-400 line-clamp-2">
                            {doc.summary || 'Краткое резюме не получено'}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 text-right ml-4">
                        <span className="text-sm font-bold text-white">
                          {Math.round(doc.score)} / 100
                        </span>
                        <span
                          className={`px-3 py-1 rounded-full border text-xs font-semibold ${verdictColor(
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

              {/* Global Risks */}
              <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl overflow-hidden">
                <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441]">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={18} className="text-[#f97316]" />
                    <h3 className="font-semibold text-sm text-white">Глобальные риски по пакету</h3>
                  </div>
                </div>
                <div className="p-6">
                  {result.globalIssues.length === 0 ? (
                    <p className="text-sm text-slate-400">Значимых глобальных несоответствий не найдено.</p>
                  ) : (
                    <ul className="space-y-3">
                      {result.globalIssues.map((gi, idx) => (
                        <li
                          key={idx}
                          className="border border-[#2a3441] rounded-lg p-4 bg-[#0f1419]"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-white">{gi.title}</span>
                            <span className="text-xs px-3 py-1 rounded-full border border-[#2a3441] text-slate-200 bg-[#1a1f2e]">
                              {gi.severity}
                            </span>
                          </div>
                          <p className="text-sm text-slate-300">{gi.description}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* Selected Document Details */}
              {selectedDoc && (
                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
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

                  <p className="mt-3 text-[10px] text-slate-500">
                    Система даёт аналитическую оценку и рекомендации. Решение об участии и
                    ответственность остаются за специалистом.
                  </p>
                </div>
              </div>
            )}
            </div>
          )}
        </div>

        {/* RIGHT: Chat Panel */}
        <div className="w-96 bg-[#1a1f2e] border border-[#2a3441] rounded-2xl flex flex-col overflow-hidden">
          <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441]">
            <h3 className="text-white font-bold flex items-center gap-2">
              <Zap className="text-[#00d4ff]" size={20} /> SINAPS AI
            </h3>
            <p className="text-slate-400 text-xs mt-1">Интеллектуальный помощник</p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-4 py-2 ${msg.role === 'user'
                    ? 'bg-[#00d4ff] text-[#0f1419]'
                    : 'bg-[#2a3441] text-white'
                    }`}
                >
                  <p className="text-base whitespace-pre-wrap">{msg.text}</p>
                  <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-[#0f1419]/70' : 'text-slate-400'}`}>
                    {msg.timestamp.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <div className="p-4 border-t border-[#2a3441] bg-[#0f1419]">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                placeholder="Задайте вопрос..."
                className="flex-1 bg-[#1a1f2e] border border-[#2a3441] rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-[#00d4ff]"
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMsg.trim()}
                className="px-4 py-2 bg-[#00d4ff] text-[#0f1419] rounded-lg font-bold hover:bg-[#00b8e6] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplexAudit;
