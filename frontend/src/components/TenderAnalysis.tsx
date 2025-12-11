import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, X, Loader2, ArrowRight, FileSearch, ChevronRight, Monitor, Hammer, Stethoscope, Layers } from 'lucide-react';
import { analyzeDocument, analyzePackage, chatWithSinaps, APIErrorException, searchLegal } from '../services/geminiService';
import { AnalysisResult, PackageAnalysis, PackageDocumentAnalysis, VerdictType, CalculatorPreset, ChatMessage } from '../types';
import { logEvent } from '../utils/logger';
import { getCurrentUser } from '../services/authService';
import { useDemo } from '../context/DemoContext';
import { useToast } from './Toast';
import type { APIError } from '../utils/apiErrorHandler';
import RateLimitError from './RateLimitError';
import { RegisterSuggestionModal } from './RegisterSuggestionModal';
import TenderHubDashboard from './TenderHubDashboard';
import { saveAnalysis, getLastAnalysis } from '../utils/analysisStorage';

// Компоненты из audit/
import HeroVerdict from './audit/HeroVerdict';
import AIConsultantIntro from './audit/AIConsultantIntro';
import FinancialMetricsGrid from './audit/FinancialMetricsGrid';
import RiskNarrative from './audit/RiskNarrative';
import DecisionSupport from './audit/DecisionSupport';

interface LegalSnippetVm {
  id: string;
  category: string;
  lawReference: string;
  title: string;
  summary: string;
}

interface TenderAnalysisProps {
  mode?: 'single' | 'package'; // Режим анализа
  onAnalysisComplete?: (preset: any) => void;
  onOpenCalculator?: () => void;
  onOpenGenerator?: (dealBreakers: string[], smartQuestions?: string[]) => void;
  onSelectForCalculator?: (preset: CalculatorPreset) => void;
}

// Хелпер для отладочного логирования
const debugLog = (location: string, message: string, data: any = {}) => {
  fetch('http://127.0.0.1:7242/ingest/774c37f9-2730-424c-a946-358b90a4d038', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      location,
      message,
      data,
      timestamp: Date.now(),
      sessionId: 'debug-session',
      runId: 'run1',
      hypothesisId: 'TenderAnalysis'
    })
  }).catch(() => {});
};

const TenderAnalysis: React.FC<TenderAnalysisProps> = ({
  mode = 'package',
  onAnalysisComplete,
  onOpenCalculator,
  onOpenGenerator,
  onSelectForCalculator,
}) => {
  // #region agent log
  debugLog('TenderAnalysis.tsx:37', 'TenderAnalysis component initialized', { mode });
  // #endregion

  // Режим работы (single/package)
  const [currentMode, setCurrentMode] = useState<'single' | 'package'>(mode);
  
  // Состояние для single mode
  const [singleFile, setSingleFile] = useState<File | null>(null);
  const [singleResult, setSingleResult] = useState<AnalysisResult | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('UNIVERSAL');
  
  // Состояние для package mode
  const [packageFiles, setPackageFiles] = useState<File[]>([]);
  const [packageResult, setPackageResult] = useState<PackageAnalysis | null>(null);
  const [selectedDocIndex, setSelectedDocIndex] = useState<number>(-1); // -1 = меню закрыто
  
  // Общее состояние
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rateLimitError, setRateLimitError] = useState<APIError | null>(null);
  
  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMsg, setInputMsg] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);
  
  // Legal references для рисков
  const [legalReferencesMap, setLegalReferencesMap] = useState<Map<string, LegalSnippetVm[]>>(new Map());
  
  // Demo mode
  const { demoState, incrementAnalysis, getOrCreateSession } = useDemo();
  const [user, setUser] = useState<any>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [registerModalType, setRegisterModalType] = useState<'after_analysis' | 'export_pdf' | 'view_history'>('after_analysis');
  
  const { showToast, ToastComponent } = useToast();

  // Инициализация чата
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([{
        id: 'init',
        role: 'model',
        text: currentMode === 'single'
          ? 'Здравствуйте! Я готов к работе. Выберите сферу тендера, загрузите документацию, и я проведу профильный аудит.'
          : 'Здравствуйте! Я готов к работе. Загрузите пакет документов для комплексного аудита, и я проведу детальный анализ всех документов.',
        timestamp: new Date()
      }]);
    }
  }, [currentMode]);

  // Восстановление последнего анализа при монтировании
  useEffect(() => {
    const lastAnalysis = getLastAnalysis(currentMode);
    if (lastAnalysis && lastAnalysis.result) {
      // #region agent log
      debugLog('TenderAnalysis.tsx:useEffect:restore', 'Restoring last analysis from storage', {
        mode: currentMode,
        analysisId: lastAnalysis.id,
        timestamp: lastAnalysis.timestamp
      });
      // #endregion
      if (currentMode === 'single') {
        setSingleResult(lastAnalysis.result);
      } else {
        setPackageResult(lastAnalysis.result);
      }
    }
  }, [currentMode]);

  // Проверка авторизации
  useEffect(() => {
    getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Автопоиск норм для рисков (single mode)
  useEffect(() => {
    if (currentMode === 'single' && singleResult && singleResult.issues && singleResult.issues.length > 0) {
      // #region agent log
      debugLog('TenderAnalysis.tsx:useEffect:legalRefs:single', 'Loading legal references for single mode', {
        issuesCount: singleResult.issues.length,
        issueTitles: singleResult.issues.map(i => i.title)
      });
      // #endregion
      const loadLegalRefs = async () => {
        const newMap = new Map<string, LegalSnippetVm[]>();
        for (const issue of singleResult.issues) {
          try {
            const legalData = await searchLegal(issue.title);
            if (legalData.items && legalData.items.length > 0) {
              newMap.set(issue.title, legalData.items.slice(0, 3));
              // #region agent log
              debugLog('TenderAnalysis.tsx:loadLegalRefs:single', 'Legal references found', {
                issueTitle: issue.title,
                referencesCount: legalData.items.length
              });
              // #endregion
            }
          } catch (err) {
            // #region agent log
            debugLog('TenderAnalysis.tsx:loadLegalRefs:single', 'Error loading legal references', {
              issueTitle: issue.title,
              error: err instanceof Error ? err.message : String(err)
            });
            // #endregion
            console.error(`Ошибка загрузки норм для риска "${issue.title}":`, err);
          }
        }
        setLegalReferencesMap(newMap);
      };
      loadLegalRefs();
    }
  }, [singleResult, currentMode]);

  // Автопоиск норм для рисков (package mode)
  useEffect(() => {
    if (currentMode === 'package' && packageResult && packageResult.globalIssues.length > 0) {
      // #region agent log
      debugLog('TenderAnalysis.tsx:useEffect:legalRefs:package', 'Loading legal references for package mode', {
        globalIssuesCount: packageResult.globalIssues.length,
        issueTitles: packageResult.globalIssues.map(i => i.title)
      });
      // #endregion
      const loadLegalRefs = async () => {
        const newMap = new Map<string, LegalSnippetVm[]>();
        for (const issue of packageResult.globalIssues) {
          try {
            const legalData = await searchLegal(issue.title);
            if (legalData.items && legalData.items.length > 0) {
              newMap.set(issue.title, legalData.items.slice(0, 3));
              // #region agent log
              debugLog('TenderAnalysis.tsx:loadLegalRefs:package', 'Legal references found', {
                issueTitle: issue.title,
                referencesCount: legalData.items.length
              });
              // #endregion
            }
          } catch (err) {
            // #region agent log
            debugLog('TenderAnalysis.tsx:loadLegalRefs:package', 'Error loading legal references', {
              issueTitle: issue.title,
              error: err instanceof Error ? err.message : String(err)
            });
            // #endregion
            console.error(`Ошибка загрузки норм для риска "${issue.title}":`, err);
          }
        }
        setLegalReferencesMap(newMap);
      };
      loadLegalRefs();
    }
  }, [packageResult, currentMode]);

  // Обработка загрузки файла (single mode)
  const handleSingleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const uploadedFile = e.target.files[0];
      // #region agent log
      debugLog('TenderAnalysis.tsx:handleSingleFileUpload', 'File selected for single mode', {
        fileName: uploadedFile.name,
        fileSize: uploadedFile.size,
        fileType: uploadedFile.type,
        industry: selectedIndustry
      });
      // #endregion

      const { validateFile } = await import('../utils/fileValidation');
      const validation = validateFile(uploadedFile);

      if (!validation.valid) {
        // #region agent log
        debugLog('TenderAnalysis.tsx:handleSingleFileUpload', 'File validation failed', {
          error: validation.error,
          fileName: uploadedFile.name
        });
        // #endregion
        showToast(validation.error || 'Ошибка валидации файла', 'error');
        e.target.value = '';
        return;
      }

      setSingleFile(uploadedFile);
      setSingleResult(null);
      setError(null);
      setRateLimitError(null);
    }
  };

  // Обработка загрузки файлов (package mode)
  const handlePackageFilesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files;
    if (!selected) return;
    const asArray = Array.from(selected);
    // #region agent log
    debugLog('TenderAnalysis.tsx:handlePackageFilesChange', 'Files selected for package mode', {
      filesCount: asArray.length,
      fileNames: asArray.map(f => f.name),
      totalSizes: asArray.map(f => f.size)
    });
    // #endregion
    setPackageFiles(prevFiles => {
      const newFiles = [...prevFiles, ...asArray];
      const uniqueFiles = newFiles.filter((file, index, self) =>
        index === self.findIndex(f => f.name === file.name && f.size === file.size)
      );
      // #region agent log
      debugLog('TenderAnalysis.tsx:handlePackageFilesChange', 'Files deduplicated', {
        beforeDedup: newFiles.length,
        afterDedup: uniqueFiles.length
      });
      // #endregion
      return uniqueFiles;
    });
    setPackageResult(null);
    setError(null);
    setRateLimitError(null);
  };

  // Анализ одного документа
  const handleAnalyzeSingle = async () => {
    if (!singleFile) return;

    // #region agent log
    debugLog('TenderAnalysis.tsx:handleAnalyzeSingle', 'Starting single document analysis', {
      fileName: singleFile.name,
      fileSize: singleFile.size,
      industry: selectedIndustry
    });
    // #endregion

    setIsAnalyzing(true);
    setError(null);
    setRateLimitError(null);

    try {
      const demoSessionId = demoState?.sessionId || null;
      const result = await analyzeDocument(singleFile, selectedIndustry, demoSessionId);
      
      if (result) {
        // #region agent log
        debugLog('TenderAnalysis.tsx:handleAnalyzeSingle', 'Single analysis completed', {
          hasResult: !!result,
          verdict: result.verdict,
          score: result.score,
          hasPassport: !!result.passport,
          hasIssues: !!result.issues,
          issuesCount: result.issues?.length || 0,
          hasExecutiveSummary: !!result.executive_summary,
          hasDealBreakers: !!result.deal_breakers,
          dealBreakersCount: result.deal_breakers?.length || 0,
          hasFinancialAnalysis: !!result.financial_analysis,
          hasSmartQuestions: !!result.smart_questions,
          smartQuestionsCount: result.smart_questions?.length || 0
        });
        // #endregion
        setSingleResult(result);
        
        // Сохраняем анализ в localStorage
        const analysisId = saveAnalysis('single', result);
        debugLog('TenderAnalysis.tsx:handleAnalyzeSingle', 'Analysis saved to storage', { analysisId });
        
        logEvent('TenderAnalysis', `Анализ завершен (single, ${selectedIndustry})`, 'info');
        
        if (onAnalysisComplete && result.passport?.nmck) {
          onAnalysisComplete({
            source: 'single',
            nmck: result.passport.nmck,
            score: result.score,
          });
        }
      }
    } catch (err: any) {
      // #region agent log
      debugLog('TenderAnalysis.tsx:handleAnalyzeSingle', 'Single analysis error', {
        error: err?.message || String(err),
        errorType: err instanceof APIErrorException ? 'APIErrorException' : 'Unknown',
        statusCode: err instanceof APIErrorException ? err.apiError?.statusCode : undefined
      });
      // #endregion
      if (err instanceof APIErrorException) {
        const apiError = err.apiError;
        if (apiError.statusCode === 429 || apiError.statusCode === 503) {
          setRateLimitError(apiError);
        } else {
          setError(apiError.message || 'Ошибка при анализе документа');
        }
      } else {
        setError('Неизвестная ошибка при анализе документа');
      }
      logEvent('TenderAnalysis', 'Ошибка при анализе документа', 'error', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Анализ пакета документов
  const handleAnalyzePackage = async () => {
    if (packageFiles.length === 0) return;

    // #region agent log
    debugLog('TenderAnalysis.tsx:handleAnalyzePackage', 'Starting package analysis', {
      filesCount: packageFiles.length,
      fileNames: packageFiles.map(f => f.name),
      totalSize: packageFiles.reduce((sum, f) => sum + f.size, 0)
    });
    // #endregion

    setIsAnalyzing(true);
    setError(null);
    setRateLimitError(null);

    try {
      const formData = new FormData();
      packageFiles.forEach(file => formData.append('files', file));
      formData.append('industry', 'UNIVERSAL');

      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/analyze-package`, {
        method: 'POST',
        headers: {
          ...(localStorage.getItem('tender_shield_token') ? {
            'Authorization': `Bearer ${localStorage.getItem('tender_shield_token')}`
          } : {}),
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Ошибка: ${response.status}`);
      }

      const result: PackageAnalysis = await response.json();
      // #region agent log
      debugLog('TenderAnalysis.tsx:handleAnalyzePackage', 'Package analysis completed', {
        hasResult: !!result,
        verdict: result.verdict,
        summaryScore: result.summaryScore,
        documentsCount: result.documents?.length || 0,
        globalIssuesCount: result.globalIssues?.length || 0,
        hasHub: !!result.hub,
        hubBaseInfo: result.hub?.baseInfo ? Object.keys(result.hub.baseInfo) : []
      });
      // #endregion
      setPackageResult(result);
      
      // Сохраняем анализ в localStorage
      const analysisId = saveAnalysis('package', result);
      debugLog('TenderAnalysis.tsx:handleAnalyzePackage', 'Analysis saved to storage', { analysisId });
      
      logEvent('TenderAnalysis', 'Анализ пакета завершен', 'info');
    } catch (err: any) {
      // #region agent log
      debugLog('TenderAnalysis.tsx:handleAnalyzePackage', 'Package analysis error', {
        error: err?.message || String(err),
        errorType: err?.name || 'Unknown'
      });
      // #endregion
      if (err.message?.includes('503') || err.message?.includes('недоступны')) {
        setRateLimitError({
          statusCode: 503,
          message: 'Все AI-сервисы недоступны. Проверьте, запущен ли Ollama и установлены ли модели.',
          details: {},
        });
      } else {
        setError(err.message || 'Ошибка при анализе пакета документов');
      }
      logEvent('TenderAnalysis', 'Ошибка при анализе пакета', 'error', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Отправка сообщения в чат
  const handleSendMessage = async () => {
    if (!inputMsg.trim() || isAnalyzing) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: inputMsg,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMsg('');
    setIsAnalyzing(true);

    try {
      const response = await chatWithSinaps(messages, inputMsg);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: response,
        timestamp: new Date(),
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: 'Извините, произошла ошибка при обработке вашего запроса.',
        timestamp: new Date(),
      }]);
      logEvent('TenderAnalysis', 'Ошибка в чате', 'error', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Получение иконки отрасли
  const getIndustryIcon = (ind: string) => {
    switch (ind) {
      case 'IT': return Monitor;
      case 'CONSTRUCTION': return Hammer;
      case 'MEDICINE': return Stethoscope;
      default: return Layers;
    }
  };

  // Получение названия отрасли
  const getIndustryLabel = (ind: string) => {
    switch (ind) {
      case 'UNIVERSAL': return 'Универсальный';
      case 'IT': return 'IT и ПО';
      case 'CONSTRUCTION': return 'Строительство';
      case 'MEDICINE': return 'Медицина';
      default: return ind;
    }
  };

  const selectedDoc = packageResult?.documents?.[selectedDocIndex] || null;

  return (
    <>
      <ToastComponent />
      <div className="flex h-full gap-6">
        {/* Основная область */}
        <div className="flex-1 flex flex-col gap-6 overflow-auto">
          {/* Переключатель режима */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold text-white mb-1">
                {currentMode === 'single' ? 'Умный Аудит' : 'Комплексный Аудит Тендера'}
              </h2>
              <p className="text-slate-400 text-sm">
                {currentMode === 'single'
                  ? 'Выберите сферу для активации профильных чек-листов'
                  : 'Анализ пакета документов тендера'}
              </p>
            </div>

            {/* Переключатель режима */}
            <div className="flex bg-[#1a1f2e] p-1 rounded-xl border border-[#2a3441]">
            <button
              onClick={() => {
                // #region agent log
                debugLog('TenderAnalysis.tsx:modeSwitch', 'Switching to single mode', { previousMode: currentMode });
                // #endregion
                setCurrentMode('single');
                setSingleFile(null);
                setSingleResult(null);
                setPackageFiles([]);
                setPackageResult(null);
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentMode === 'single'
                  ? 'bg-[#00d4ff] text-[#0f1419]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Один документ
            </button>
            <button
              onClick={() => {
                // #region agent log
                debugLog('TenderAnalysis.tsx:modeSwitch', 'Switching to package mode', { previousMode: currentMode });
                // #endregion
                setCurrentMode('package');
                setSingleFile(null);
                setSingleResult(null);
                setPackageFiles([]);
                setPackageResult(null);
              }}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                currentMode === 'package'
                  ? 'bg-[#00d4ff] text-[#0f1419]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Пакет документов
            </button>
            </div>
          </div>

          {/* Выбор отрасли (только для single mode) */}
          {currentMode === 'single' && (
            <div className="flex bg-[#1a1f2e] p-1 rounded-xl border border-[#2a3441]">
              {(['UNIVERSAL', 'IT', 'CONSTRUCTION', 'MEDICINE'] as string[]).map((ind) => {
                const Icon = getIndustryIcon(ind);
                const isActive = selectedIndustry === ind;
                return (
                  <button
                    key={ind}
                    onClick={() => {
                      if (isAnalyzing) return;
                      setSelectedIndustry(ind);
                    }}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-[#00d4ff] text-[#0f1419]'
                        : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Icon size={16} />
                    {ind === 'UNIVERSAL' ? 'Универсальный' : ind === 'IT' ? 'IT и ПО' : ind === 'CONSTRUCTION' ? 'Строительство' : 'Медицина'}
                  </button>
                );
              })}
            </div>
          )}

          {/* Загрузка файлов */}
          {currentMode === 'single' ? (
            // Single mode upload
            !singleFile ? (
              <div className="relative border-2 border-dashed border-[#2a3441] bg-[#1a1f2e]/50 rounded-2xl p-12 text-center hover:border-[#00d4ff] transition-all cursor-pointer flex flex-col items-center justify-center min-h-[400px]">
                <label className="absolute inset-0 cursor-pointer z-20 w-full h-full" htmlFor="file-upload-single">
                  <input
                    id="file-upload-single"
                    type="file"
                    className="hidden"
                    onChange={handleSingleFileUpload}
                    accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
                  />
                </label>
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-[#00d4ff] blur-[40px] opacity-20 rounded-full"></div>
                  <div className="inline-flex items-center justify-center w-24 h-24 bg-[#1a1f2e] rounded-2xl border border-[#2a3441] shadow-2xl relative z-10">
                    <Upload className="text-[#00d4ff]" size={40} />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">Загрузите документ</h3>
                <p className="text-slate-400 max-w-md mx-auto leading-relaxed">
                  Поддерживаются форматы PDF, DOCX/DOC, TXT, RTF, XLS/XLSX
                </p>
              </div>
            ) : (
              <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <FileText className="text-[#00d4ff]" size={20} />
                    <div>
                      <p className="text-white font-medium">{singleFile.name}</p>
                      <p className="text-xs text-slate-400">{(singleFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setSingleFile(null);
                      setSingleResult(null);
                    }}
                    className="p-2 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400"
                  >
                    <X size={20} />
                  </button>
                </div>
                <button
                  onClick={handleAnalyzeSingle}
                  disabled={isAnalyzing}
                  className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all flex items-center justify-center gap-2 disabled:opacity-70"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="animate-spin" size={20} />
                      Анализируем...
                    </>
                  ) : (
                    <>
                      Запустить анализ <ArrowRight size={20} />
                    </>
                  )}
                </button>
              </div>
            )
          ) : (
            // Package mode upload
            !packageFiles.length ? (
              <div className="relative border-2 border-dashed border-[#2a3441] bg-[#1a1f2e]/50 rounded-2xl p-12 text-center hover:border-[#00d4ff] transition-all cursor-pointer flex flex-col items-center justify-center min-h-[400px]">
                <label className="absolute inset-0 cursor-pointer z-20 w-full h-full" htmlFor="file-upload-package">
                  <input
                    id="file-upload-package"
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handlePackageFilesChange}
                    accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
                  />
                </label>
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-[#00d4ff] blur-[40px] opacity-20 rounded-full"></div>
                  <div className="inline-flex items-center justify-center w-24 h-24 bg-[#1a1f2e] rounded-2xl border border-[#2a3441] shadow-2xl relative z-10">
                    <Upload className="text-[#00d4ff]" size={40} />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">Загрузите пакет документов</h3>
                <p className="text-slate-400 max-w-md mx-auto leading-relaxed">
                  Поддерживаются форматы PDF, DOCX/DOC, TXT, RTF, XLS/XLSX. Можно загрузить несколько файлов одновременно.
                </p>
              </div>
            ) : (
              <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-white font-bold">Загруженные документы ({packageFiles.length})</h3>
                  <div className="flex items-center gap-2">
                    <label className="relative cursor-pointer">
                      <input
                        type="file"
                        multiple
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        onChange={handlePackageFilesChange}
                        accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
                      />
                      <button className="px-3 py-1.5 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-lg text-xs font-bold transition-colors">
                        + Добавить файлы
                      </button>
                    </label>
                    <button
                      onClick={() => {
                        setPackageFiles([]);
                        setPackageResult(null);
                        setError(null);
                      }}
                      className="p-2 hover:bg-[#2a3441] rounded-lg transition-colors text-slate-400 hover:text-white"
                    >
                      <X size={20} />
                    </button>
                  </div>
                </div>
                <div className="space-y-2">
                  {packageFiles.map((file, idx) => (
                    <div key={idx} className="flex items-center gap-3 p-3 bg-[#0f1419] rounded-lg border border-[#2a3441]">
                      <FileSearch className="text-[#00d4ff]" size={20} />
                      <div className="flex-1">
                        <p className="text-white text-sm font-medium">{file.name}</p>
                        <p className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button
                        onClick={() => {
                          const newFiles = packageFiles.filter((_, i) => i !== idx);
                          setPackageFiles(newFiles);
                          if (newFiles.length === 0) {
                            setPackageResult(null);
                            setError(null);
                          }
                        }}
                        className="p-1 hover:bg-red-500/20 rounded text-slate-400 hover:text-red-400"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={handleAnalyzePackage}
                  disabled={isAnalyzing || !packageFiles.length}
                  className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-4 rounded-xl hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all flex items-center justify-center gap-2 disabled:opacity-70"
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
            )
          )}

          {/* Ошибки */}
          {rateLimitError && <RateLimitError error={rateLimitError} />}
          {error && !rateLimitError && (
            <div className="bg-red-500/10 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
              <X className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {/* Результаты анализа - Single Mode */}
          {currentMode === 'single' && singleResult && (
            <div className="animate-fade-in space-y-6">
              {/* Hero Verdict */}
              <HeroVerdict
                verdict={singleResult.verdict}
                score={singleResult.score}
                executiveSummary={singleResult.executive_summary}
                mainProblem={singleResult.executive_summary?.split('\n').find(line =>
                  line.toLowerCase().includes('проблема') || line.toLowerCase().includes('риск')
                )}
                onShowDetails={() => {
                  const detailsSection = document.querySelector('[data-section="details"]');
                  if (detailsSection) {
                    detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  } else {
                    window.scrollTo({ top: 600, behavior: 'smooth' });
                  }
                }}
                onGenerateRefusal={() => {
                  if (onOpenGenerator && packageResult?.globalIssues) {
                    const dealBreakers = packageResult.globalIssues
                      .filter(gi => gi.severity.toLowerCase() === 'critical' || gi.severity.toLowerCase() === 'high')
                      .map(gi => gi.title);
                    const smartQuestions = packageResult.hub?.recommendation?.actions?.map(a => a.text) || [];
                    onOpenGenerator(dealBreakers, smartQuestions);
                  } else {
                    logEvent('TenderAnalysis', 'Запрошено формирование отказа', 'info');
                  }
                }}
              />

              {/* AI Consultant Intro */}
              <AIConsultantIntro
                verdict={singleResult.verdict}
                executiveSummary={singleResult.executive_summary}
                summary={singleResult.summary}
                score={singleResult.score}
              />

              {/* Financial Metrics Grid */}
              {singleResult.passport && (
                <div data-section="details">
                  <FinancialMetricsGrid
                    passport={singleResult.passport}
                    financialAnalysis={singleResult.financial_analysis}
                  />
                </div>
              )}

              {/* Risk Narrative */}
              <RiskNarrative
                risks={(singleResult.issues || []).map(issue => ({
                  ...issue,
                  legalReferences: legalReferencesMap.get(issue.title),
                }))}
                dealBreakers={singleResult.deal_breakers}
                onGenerateProtocol={onOpenGenerator ? (dealBreakers) => {
                  onOpenGenerator(dealBreakers, singleResult.smart_questions);
                } : undefined}
                onViewKnowledge={(query) => {
                  logEvent('TenderAnalysis', `Переход в Базу знаний: ${query}`, 'info');
                }}
              />

              {/* Decision Support */}
              <DecisionSupport
                verdict={singleResult.verdict}
                score={singleResult.score}
                financialAnalysis={singleResult.financial_analysis}
                smartQuestions={singleResult.smart_questions}
              />

              {/* Hub Dashboard (если есть) */}
              {singleResult.hub && (
                <TenderHubDashboard result={singleResult} hub={singleResult.hub} />
              )}
            </div>
          )}

          {/* Результаты анализа - Package Mode */}
          {currentMode === 'package' && packageResult && (
            <div className="animate-fade-in space-y-6">
              {/* Hero Verdict */}
              <HeroVerdict
                verdict={packageResult.verdict as VerdictType}
                score={Math.round(packageResult.summaryScore)}
                executiveSummary={packageResult.hub?.recommendation?.summaryShort || `Анализ пакета из ${packageResult.documents.length} документов завершен.`}
                mainProblem={packageResult.globalIssues.length > 0 ? packageResult.globalIssues[0].title : undefined}
                onShowDetails={() => {
                  const detailsSection = document.querySelector('[data-section="details"]');
                  if (detailsSection) {
                    detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                  } else {
                    window.scrollTo({ top: 600, behavior: 'smooth' });
                  }
                }}
                onGenerateRefusal={() => {
                  if (onOpenGenerator && packageResult?.globalIssues) {
                    const dealBreakers = packageResult.globalIssues
                      .filter(gi => gi.severity.toLowerCase() === 'critical' || gi.severity.toLowerCase() === 'high')
                      .map(gi => gi.title);
                    const smartQuestions = packageResult.hub?.recommendation?.actions?.map(a => a.text) || [];
                    onOpenGenerator(dealBreakers, smartQuestions);
                  } else {
                    logEvent('TenderAnalysis', 'Запрошено формирование отказа', 'info');
                  }
                }}
              />

              {/* AI Consultant Intro */}
              <AIConsultantIntro
                verdict={packageResult.verdict as VerdictType}
                executiveSummary={packageResult.hub?.recommendation?.summaryShort}
                summary={`Проанализирован пакет из ${packageResult.documents.length} документов. ${packageResult.globalIssues.length > 0 ? `Обнаружено ${packageResult.globalIssues.length} глобальных рисков.` : 'Значимых глобальных рисков не обнаружено.'}`}
                score={Math.round(packageResult.summaryScore)}
              />

              {/* Financial Metrics Grid */}
              {packageResult.hub && packageResult.hub.baseInfo && (
                <div data-section="details">
                  <FinancialMetricsGrid
                    passport={{
                      nmck: packageResult.hub.baseInfo.nmckTotal || 'Не указано',
                      fz: packageResult.hub.baseInfo.fz || '44-ФЗ',
                      advance: packageResult.hub.payments.advance || 'Нет',
                      secureBid: packageResult.hub.guarantees.text || 'Нет',
                      deadlineExecution: packageResult.hub.timeline.comment || 'Не указано',
                      region: packageResult.hub.baseInfo.region || 'Не указано',
                    }}
                    financialAnalysis={packageResult.hub.financial ? {
                      margin_risk: packageResult.hub.financial.lossRiskLevel === 'high' ? 'High' : packageResult.hub.financial.lossRiskLevel === 'medium' ? 'Medium' : 'Low',
                      cash_gap_risk: packageResult.hub.payments.advance === 'Нет' || packageResult.hub.payments.advance === '0%' ? 'Yes' : 'No',
                      reasoning: packageResult.hub.financial.marginComment || '',
                    } : undefined}
                  />
                </div>
              )}

              {/* Risk Narrative */}
              <RiskNarrative
                risks={packageResult.globalIssues.map(gi => ({
                  title: gi.title,
                  description: gi.description,
                  severity: gi.severity.toLowerCase(),
                  recommendation: gi.details?.recommendation,
                  legalReferences: legalReferencesMap.get(gi.title),
                }))}
                dealBreakers={packageResult.globalIssues
                  .filter(gi => gi.severity.toLowerCase() === 'critical' || gi.severity.toLowerCase() === 'high')
                  .map(gi => gi.title)}
                onGenerateProtocol={onOpenGenerator ? (dealBreakers) => {
                  const smartQuestions = packageResult.hub?.recommendation?.actions?.map(a => a.text) || [];
                  onOpenGenerator(dealBreakers, smartQuestions);
                } : undefined}
                onViewKnowledge={(query) => {
                  logEvent('TenderAnalysis', `Переход в Базу знаний: ${query}`, 'info');
                }}
              />

              {/* Decision Support */}
              <DecisionSupport
                verdict={packageResult.verdict as VerdictType}
                score={Math.round(packageResult.summaryScore)}
                financialAnalysis={packageResult.hub?.financial ? {
                  margin_risk: packageResult.hub.financial.lossRiskLevel === 'high' ? 'High' : packageResult.hub.financial.lossRiskLevel === 'medium' ? 'Medium' : 'Low',
                  cash_gap_risk: packageResult.hub.payments.advance === 'Нет' || packageResult.hub.payments.advance === '0%' ? 'Yes' : 'No',
                  reasoning: packageResult.hub.financial.marginComment || '',
                } : undefined}
                smartQuestions={packageResult.hub?.recommendation?.actions?.map(a => a.text) || []}
              />

              {/* Список документов пакета - выезжающее меню вверх */}
              {packageResult.documents && packageResult.documents.length > 0 && (
                <div className="fixed bottom-0 left-0 right-0 md:left-[280px] z-50">
                  <div className="bg-[#1a1f2e] border-t border-[#2a3441] rounded-t-2xl shadow-2xl max-h-[60vh] overflow-hidden flex flex-col">
                    {/* Кнопка для открытия/закрытия */}
                    <button
                      onClick={() => setSelectedDocIndex(selectedDocIndex === -1 ? 0 : -1)}
                      className="bg-[#0f1419] px-6 py-3 border-b border-[#2a3441] flex items-center justify-between hover:bg-[#2a3441]/50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <FileSearch className="text-[#00d4ff]" size={18} />
                        <span className="text-white font-bold text-sm">Документы пакета</span>
                        <span className="text-xs text-slate-400">({packageResult.documents.length} шт.)</span>
                      </div>
                      <ChevronRight
                        size={18}
                        className={`text-slate-400 transition-transform ${selectedDocIndex !== -1 ? 'rotate-90' : '-rotate-90'}`}
                      />
                    </button>
                    
                    {/* Список документов (показывается при открытии) */}
                    {selectedDocIndex !== -1 && (
                      <div className="overflow-y-auto custom-scrollbar divide-y divide-[#2a3441]">
                        {packageResult.documents.map((doc, idx) => (
                          <button
                            key={doc.filename + idx}
                            onClick={() => setSelectedDocIndex(idx)}
                            className={`w-full flex items-center justify-between py-3 px-6 text-left hover:bg-[#2a3441]/50 transition-colors ${
                              idx === selectedDocIndex ? 'bg-[#2a3441] border-l-4 border-[#00d4ff]' : ''
                            }`}
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <ChevronRight
                                size={14}
                                className={`flex-shrink-0 ${idx === selectedDocIndex ? 'text-[#00d4ff]' : 'text-slate-500'}`}
                              />
                              <div className="flex-1 min-w-0">
                                <div className="font-semibold text-white text-sm truncate">{doc.filename}</div>
                                <div className="text-xs text-slate-400 line-clamp-1 mt-0.5">
                                  {doc.summary || 'Краткое резюме не получено'}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 text-right ml-4 flex-shrink-0">
                              <span className="text-xs font-bold text-white">
                                {Math.round(doc.score)}/100
                              </span>
                              <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold ${
                                doc.verdict === 'STOP' ? 'bg-red-500/10 text-red-400 border-red-500/40' :
                                doc.verdict === 'CAUTION' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/40' :
                                'bg-emerald-500/10 text-emerald-400 border-emerald-500/40'
                              }`}>
                                {doc.verdict}
                              </span>
                            </div>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Панель чата */}
        <div className="w-[400px] bg-[#1a1f2e] border border-[#2a3441] rounded-2xl flex flex-col h-full max-h-[calc(100vh-4rem)]">
          <div className="p-4 border-b border-[#2a3441]">
            <h3 className="text-white font-bold flex items-center gap-2">
              <FileText className="text-[#00d4ff]" size={20} />
              Чат с AI-консультантом
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-xl p-3 ${
                    msg.role === 'user'
                      ? 'bg-[#00d4ff] text-[#0f1419]'
                      : 'bg-[#0f1419] text-white border border-[#2a3441]'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          <div className="p-4 border-t border-[#2a3441]">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMsg}
                onChange={(e) => setInputMsg(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                placeholder="Задайте вопрос..."
                className="flex-1 px-4 py-2 bg-[#0f1419] border border-[#2a3441] rounded-xl text-white text-sm focus:outline-none focus:border-[#00d4ff]"
                disabled={isAnalyzing}
              />
              <button
                onClick={handleSendMessage}
                disabled={isAnalyzing || !inputMsg.trim()}
                className="px-4 py-2 bg-[#00d4ff] text-[#0f1419] rounded-xl font-bold hover:bg-[#00b3e0] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Отправить
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Модальное окно регистрации */}
      {showRegisterModal && (
        <RegisterSuggestionModal
          type={registerModalType}
          onClose={() => setShowRegisterModal(false)}
          onRegister={() => {
            setShowRegisterModal(false);
            window.location.reload();
          }}
        />
      )}
    </>
  );
};

export default TenderAnalysis;

