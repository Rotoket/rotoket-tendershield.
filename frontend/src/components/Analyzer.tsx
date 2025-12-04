import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle, AlertTriangle, AlertOctagon, X, Loader2, Zap, Download, ChevronRight, Calendar, ShieldAlert, BadgeCheck, Banknote, Landmark, ShieldCheck, Siren, ArrowRight, Activity, Clock, MapPin, Percent, Shield, Monitor, Hammer, Stethoscope, Layers, FileSpreadsheet } from 'lucide-react';
import { analyzeDocument, chatWithSinaps, APIErrorException, exportAnalysisToExcel } from '../services/geminiService';
import { AnalysisResult, ChatMessage, DeepAuditBlock } from '../types';
import { logEvent } from '../utils/logger';
import { buildSingleHubFromAnalysis } from '../utils/hubBuilders';
import TenderHubDashboard from './TenderHubDashboard';
import RateLimitError from './RateLimitError';
import { RegisterSuggestionModal } from './RegisterSuggestionModal';
import { useDemo } from '../context/DemoContext';
import { getCurrentUser, getAuthHeaders } from '../services/authService';
import type { APIError } from '../utils/apiErrorHandler';
import { AnalysisProgress } from './AnalysisProgress';
import { useToast } from './Toast';

// --- ТИПЫ ДЛЯ ЛОКАЛЬНОГО ИСПОЛЬЗОВАНИЯ ---
type Industry = 'UNIVERSAL' | 'IT' | 'CONSTRUCTION' | 'MEDICINE';

// --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
const getIndustryIcon = (ind: string) => {
    switch (ind) {
        case 'IT': return Monitor;
        case 'CONSTRUCTION': return Hammer;
        case 'MEDICINE': return Stethoscope;
        default: return Layers;
    }
}

const getIndustryLabel = (ind: string) => {
    switch (ind) {
        case 'IT': return "IT и ПО";
        case 'CONSTRUCTION': return "Строительство";
        case 'MEDICINE': return "Медицина";
        default: return "Универсальный";
    }
}

// --- КОМПОНЕНТЫ UI ---

const PassportItem = ({ label, value, icon: Icon, alert }: any) => (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${alert ? 'bg-[#f59e0b]/10 border-[#f59e0b]/30' : 'bg-[#1a1f2e] border-[#2a3441]'}`}>
        <div className={`p-2 rounded-md ${alert ? 'bg-[#f59e0b]/20 text-[#f59e0b]' : 'bg-[#0f1419] text-[#00d4ff]'}`}>
            <Icon size={16} />
        </div>
        <div>
            <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-0.5">{label}</p>
            <p className={`text-base font-semibold ${alert ? 'text-[#f59e0b]' : 'text-white'}`}>{value || "—"}</p>
        </div>
    </div>
);

// Компонент строки аудита (Чек-лист)
interface DeepAuditRowProps {
    block: DeepAuditBlock;
    isExpanded: boolean;
    onToggle: () => void;
}

const DeepAuditRow: React.FC<DeepAuditRowProps> = ({ block, isExpanded, onToggle }) => {
    return (
        <div className={`border rounded-xl transition-all duration-300 overflow-hidden mb-3 ${block.status === 'CRITICAL' ? 'border-[#ff4444]/50 bg-[#ff4444]/5' :
            block.status === 'WARNING' ? 'border-[#f59e0b]/50 bg-[#f59e0b]/5' :
                'border-[#2a3441] bg-[#1a1f2e]'
            }`}>
            <div
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-[#2a3441]/50"
                onClick={onToggle}
            >
                <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${block.status === 'CRITICAL' ? 'bg-[#ff4444] animate-pulse' :
                        block.status === 'WARNING' ? 'bg-[#f59e0b]' :
                            'bg-[#00e648]'
                        }`}></div>
                    <span className="font-bold text-white text-sm uppercase tracking-wide">{block.title}</span>
                </div>
                <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-bold px-2 py-1 rounded border ${block.status === 'CRITICAL' ? 'border-[#ff4444] text-[#ff4444]' :
                        block.status === 'WARNING' ? 'border-[#f59e0b] text-[#f59e0b]' :
                            'border-[#00e648] text-[#00e648]'
                        }`}>
                        {block.status === 'CRITICAL' ? 'КРИТИЧНО' : block.status === 'WARNING' ? 'ВНИМАНИЕ' : 'НОРМА'}
                    </span>
                    <ChevronRight size={16} className={`text-slate-500 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </div>
            </div>

            {isExpanded && (
                <div className="border-t border-[#2a3441] bg-[#0f1419]/50">
                    {block.items.map((item, idx) => (
                        <div key={idx} className="p-4 border-b border-[#2a3441] last:border-0 flex items-start gap-4">
                            <div className="mt-1">
                                {item.status === 'YES' && <CheckCircle size={16} className="text-[#00e648]" />}
                                {item.status === 'NO' && <X size={16} className="text-slate-500" />}
                                {item.status === 'RISK' && <AlertOctagon size={16} className="text-[#ff4444]" />}
                                {item.status === 'PARTIAL' && <AlertTriangle size={16} className="text-[#f59e0b]" />}
                            </div>
                            <div className="flex-1">
                                <div className="flex justify-between mb-1">
                                    <span className="text-xs font-bold text-slate-500 uppercase">{item.label}</span>
                                </div>
                                <div className="text-base text-white font-medium">{item.value}</div>
                                {item.details && <div className="text-xs text-slate-400 mt-1 bg-[#1a1f2e] p-2 rounded border border-[#2a3441]">{item.details}</div>}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// --- ГЛАВНЫЙ КОМПОНЕНТ ---
const Analyzer: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [scanLog, setScanLog] = useState<string[]>([]);
    const [expandedBlock, setExpandedBlock] = useState<string | null>(null);
    const [analysisProgress, setAnalysisProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');

    // Toast notifications
    const { showToast, ToastComponent } = useToast();

    // Industry Selection
    const [selectedIndustry, setSelectedIndustry] = useState<string>('UNIVERSAL');

    // Chat state
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputMsg, setInputMsg] = useState('');
    const chatEndRef = useRef<HTMLDivElement>(null);

    // Error handling
    const [rateLimitError, setRateLimitError] = useState<APIError | null>(null);

    // Demo mode
    const { demoState, incrementAnalysis, getOrCreateSession } = useDemo();
    const [user, setUser] = useState<any>(null);
    const [showRegisterModal, setShowRegisterModal] = useState(false);
    const [registerModalType, setRegisterModalType] = useState<'after_analysis' | 'export_pdf' | 'view_history'>('after_analysis');

    useEffect(() => {
        if (!file && messages.length === 0) {
            setMessages([{
                id: 'init',
                role: 'model',
                text: 'Здравствуйте! Я готов к работе. Выберите сферу тендера, загрузите документацию, и я проведу профильный аудит.',
                timestamp: new Date()
            }]);
        }
    }, []);

    // Проверяем авторизацию
    useEffect(() => {
        getCurrentUser().then(setUser).catch(() => setUser(null));
    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files?.[0]) {
            const uploadedFile = e.target.files[0];

            // Валидация файла
            const { validateFile } = await import('../utils/fileValidation');
            const validation = validateFile(uploadedFile);

            if (!validation.valid) {
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'model',
                    text: `❌ ${validation.error}`,
                    timestamp: new Date(),
                }]);
                logEvent('Analyzer', `Ошибка валидации файла: ${validation.error}`, 'error');
                e.target.value = ''; // Сбрасываем input
                return;
            }

            setFile(uploadedFile);
            logEvent('Analyzer', `Загружен файл для одиночного аудита: ${uploadedFile.name} (${uploadedFile.size} байт)`);
            try {
                await startAnalysis(uploadedFile);
            } catch (err) {
                console.error('Upload failed', err);
                logEvent('Analyzer', 'Ошибка при запуске анализа после загрузки файла', 'error', err);
                setIsAnalyzing(false);
            }
        }
    };

    const startAnalysis = async (uploadedFile: File) => {
        setIsAnalyzing(true);
        setResult(null);
        setScanLog([]);

        logEvent('Analyzer', `Запуск анализа файла "${uploadedFile.name}" для отрасли ${selectedIndustry}`);

        // Динамические шаги анализа
        let steps = [
            'Инициализация ядра анализа...',
            'Чтение содержимого файла...',
            'Сканирование структуры документа...',
        ];

        if (selectedIndustry === 'IT') {
            steps.push('Анализ функциональных требований...', 'Проверка прав на код и лицензий...', 'Поиск скрытых SLA...');
        } else if (selectedIndustry === 'CONSTRUCTION') {
            steps.push('Сверка Сметы и ТЗ...', 'Анализ Формы 2 (Материалы)...', 'Проверка требований СРО...');
        } else if (selectedIndustry === 'MEDICINE') {
            steps.push('Проверка Рег. Удостоверений (РУ)...', 'Анализ температурных режимов...', 'Сверка сроков годности...');
        } else {
            steps.push('Извлечение финансовых параметров...', 'Сверка с базой нормативных актов (44-ФЗ)...');
        }

        steps.push('Генерация паспорта тендера...');

        // Обновляем прогресс для каждого шага
        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];
            setCurrentStep(step);
            setScanLog(prev => [...prev, step]);
            // Прогресс: 0-70% для шагов, остальное для реального анализа
            const stepProgress = Math.round((i + 1) / steps.length * 70);
            setAnalysisProgress(stepProgress);
            await new Promise(r => setTimeout(r, 600));
        }

        setAnalysisProgress(75);
        setCurrentStep('Отправка на анализ...');

        try {
            // Получаем или создаем демо-сессию, если пользователь не авторизован
            let demoSessionId: string | null = null;
            if (!user && demoState.isDemo) {
                demoSessionId = await getOrCreateSession();
            }

            setAnalysisProgress(85);
            setCurrentStep('Обработка результатов...');

            const analysis = await analyzeDocument(uploadedFile, selectedIndustry, demoSessionId);

            if (analysis) {
                setAnalysisProgress(100);
                setCurrentStep('Анализ завершен!');

                // Показываем уведомление об успехе
                showToast('success', `Анализ завершен! Индекс безопасности: ${analysis.score}/100`);

                // Очищаем ошибки при успешном анализе
                setRateLimitError(null);

                // Увеличиваем счетчик анализов для демо-режима
                if (!user && demoState.isDemo) {
                    incrementAnalysis();
                }

                // КОНТЕКСТНЫЙ ТРИГГЕР #1: После первого анализа в демо-режиме
                if (!user && demoState.isDemo && analysis.ui_suggestion) {
                    setRegisterModalType('after_analysis');
                    setShowRegisterModal(true);
                }

                // Собираем хаб-сводку на фронте (краткий обзор для тендерщика)
                const hub = buildSingleHubFromAnalysis(analysis, selectedIndustry as 'IT' | 'CONSTRUCTION' | 'MEDICINE' | 'UNIVERSAL');
                setResult({ ...analysis, hub });
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'model',
                    text: `Анализ завершен. Индекс безопасности: ${analysis.score}/100.`,
                    timestamp: new Date(),
                }]);

                logEvent(
                    'Analyzer',
                    `Анализ успешно завершен: индекс безопасности ${analysis.score}/100, вердикт ${analysis.verdict}`,
                );

                // Авто-раскрытие первого блока рисков
                if (analysis.deepAudit && analysis.deepAudit.length > 0) {
                    const riskyBlock = analysis.deepAudit.find(b => b.status === 'CRITICAL' || b.status === 'WARNING');
                    if (riskyBlock) setExpandedBlock(riskyBlock.id);
                }
            }
        } catch (error) {
            console.error('Critical analysis error:', error);
            setAnalysisProgress(0);
            setCurrentStep('');

            // Проверяем, это ошибка лимита или обычная ошибка
            if (error instanceof APIErrorException) {
                const apiError = error.apiError;

                if (apiError.type === 'RATE_LIMIT') {
                    setRateLimitError(apiError);
                    setMessages(prev => [...prev, {
                        id: Date.now().toString(),
                        role: 'model',
                        text: `⚠️ Превышен лимит использования. ${apiError.message}`,
                        timestamp: new Date(),
                    }]);
                    logEvent('Analyzer', `Превышен лимит: ${apiError.message}`, 'error');
                } else {
                    setScanLog(prev => [...prev, `Ошибка: ${apiError.message}`]);
                    setMessages(prev => [...prev, {
                        id: Date.now().toString(),
                        role: 'model',
                        text: `❌ Произошла ошибка: ${apiError.message}`,
                        timestamp: new Date(),
                    }]);
                    logEvent('Analyzer', `Ошибка анализа: ${apiError.message}`, 'error', error);
                }
            } else {
                // Проверяем, это сетевая ошибка
                const errorMessage = error instanceof Error ? error.message : String(error);
                let userMessage = '❌ Произошла ошибка при анализе. ';

                if (errorMessage.includes('Failed to fetch') || errorMessage.includes('network')) {
                    userMessage += '\n\nВозможные причины:\n';
                    userMessage += '• Backend сервер не запущен (проверьте, запущен ли сервер на порту 8000)\n';
                    userMessage += '• Неправильный URL API (проверьте настройки в .env файле)\n';
                    userMessage += '• Проблемы с CORS или файрволом\n\n';
                    userMessage += 'Проверьте консоль браузера (F12) для детальной информации.';
                } else {
                    userMessage += 'Попробуйте еще раз.';
                }

                setScanLog(prev => [...prev, `Ошибка: ${errorMessage}`]);
                setMessages(prev => [...prev, {
                    id: Date.now().toString(),
                    role: 'model',
                    text: userMessage,
                    timestamp: new Date(),
                }]);
                logEvent('Analyzer', 'Критическая ошибка при анализе документа', 'error', error);

                // Показываем toast с более детальной информацией
                showToast('error', errorMessage.includes('Failed to fetch')
                    ? 'Не удалось подключиться к серверу. Проверьте, запущен ли backend.'
                    : 'Ошибка при анализе документа');
            }
        } finally {
            setIsAnalyzing(false);
            setAnalysisProgress(0);
            setCurrentStep('');
        }
    };

    const exportToExcel = async () => {
        if (!result) return;

        try {
            showToast('info', 'Генерация Excel отчета...');

            const blob = await exportAnalysisToExcel(result);

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `analysis_${file?.name || 'document'}_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showToast('success', 'Excel отчет успешно экспортирован');
        } catch (error: any) {
            console.error('Export error:', error);
            if (error?.apiError?.statusCode === 403) {
                showToast('warning', 'Экспорт Excel доступен после регистрации');
                setRegisterModalType('export_pdf');
                setShowRegisterModal(true);
            } else {
                showToast('error', error?.apiError?.message || 'Ошибка при экспорте Excel');
            }
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
        logEvent('Analyzer', 'Отправлен вопрос в чат Sinaps AI из однодокового аудита', 'info');
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
            logEvent('Analyzer', 'Получен ответ от чата Sinaps AI', 'info');
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
            logEvent('Analyzer', 'Ошибка при обращении к чату Sinaps AI', 'error', err);
        }
    };

    return (
        <>
            <ToastComponent />
            <div className="flex h-full gap-6 flex-col animate-fade-in">
                {/* Header & Industry Selector */}
                <div className="flex justify-between items-end mb-2">
                    <div>
                        <h2 className="text-3xl font-bold text-white mb-1">Умный Аудит</h2>
                        <p className="text-slate-400 text-sm">Выберите сферу для активации профильных чек-листов</p>
                    </div>

                    {/* INDUSTRY SELECTOR UI */}
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
                                        logEvent('Analyzer', `Выбран профиль отрасли для аудита: ${ind}`);
                                    }}
                                    disabled={isAnalyzing}
                                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${isActive
                                        ? 'bg-[#00d4ff] text-[#0f1419] shadow-md'
                                        : 'text-slate-400 hover:text-white hover:bg-[#2a3441]'
                                        }`}
                                >
                                    <Icon size={16} />
                                    {getIndustryLabel(ind)}
                                </button>
                            );
                        })}
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
                                    // TODO: Navigate to profile/tariff page
                                    setRateLimitError(null);
                                }}
                            />
                        )}

                        {/* Analysis Progress */}
                        {isAnalyzing && (
                            <AnalysisProgress
                                isAnalyzing={isAnalyzing}
                                currentStep={currentStep}
                                progress={analysisProgress}
                                steps={scanLog}
                            />
                        )}

                        {!file ? (
                            <div className="relative border-2 border-dashed border-[#2a3441] bg-[#1a1f2e]/50 rounded-2xl p-12 text-center hover:border-[#00d4ff] transition-all cursor-pointer flex flex-col items-center justify-center flex-1 min-h-[400px]">
                                <input
                                    type="file"
                                    className="absolute inset-0 opacity-0 cursor-pointer z-10"
                                    onChange={handleFileUpload}
                                    accept=".pdf,.docx,.doc,.txt,.rtf,.xls,.xlsx"
                                />
                                <div className="relative mb-8">
                                    <div className="absolute inset-0 bg-[#00d4ff] blur-[40px] opacity-20 rounded-full"></div>
                                    <div className="inline-flex items-center justify-center w-24 h-24 bg-[#1a1f2e] rounded-2xl border border-[#2a3441] shadow-2xl relative z-10">
                                        <Upload className="text-[#00d4ff]" size={40} />
                                    </div>
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-3">Загрузите документацию</h3>
                                <p className="text-slate-400 max-w-md mx-auto leading-relaxed mb-4">
                                    Поддерживаются форматы PDF, DOCX/DOC, TXT, RTF, XLS/XLSX. <br />
                                </p>
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/20 text-xs font-bold">
                                    Активный профиль: {getIndustryLabel(selectedIndustry)}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* File Card & Status */}
                                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-4 flex justify-between items-center shadow-lg relative overflow-hidden">
                                    {isAnalyzing && <div className="absolute inset-0 animate-scan pointer-events-none bg-gradient-to-r from-transparent via-[#00d4ff]/5 to-transparent"></div>}
                                    <div className="flex items-center gap-4 relative z-10">
                                        <div className="w-12 h-12 bg-[#0f1419] rounded-xl flex items-center justify-center border border-[#2a3441] text-[#00d4ff]">
                                            {isAnalyzing ? <Loader2 className="animate-spin" size={24} /> : <FileText size={24} />}
                                        </div>
                                        <div>
                                            <h3 className="text-white font-bold">{file.name}</h3>
                                            <p className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                        </div>
                                    </div>
                                    {isAnalyzing ? (
                                        <div className="text-right">
                                            <div className="text-[#00d4ff] text-sm font-bold animate-pulse">Анализ...</div>
                                            <div className="text-slate-400 text-xs mt-1 font-mono">{scanLog[scanLog.length - 1]}</div>
                                        </div>
                                    ) : (
                                        <button onClick={() => { setFile(null); setResult(null); }} className="p-2 hover:bg-[#2a3441] rounded-lg transition-colors text-slate-400 hover:text-white">
                                            <X size={20} />
                                        </button>
                                    )}
                                </div>

                                {result && (
                                    <div className="animate-fade-in space-y-6">
                                        {/* DEAL BREAKERS / СТОП-ФАКТОРЫ */}
                                        {result.dealBreakers && result.dealBreakers.length > 0 && (
                                            <div className="bg-[#450a0a] border border-[#fecaca] rounded-2xl p-6 text-sm text-red-50 shadow-lg">
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="flex items-center gap-2">
                                                        <AlertOctagon className="text-red-300" size={22} />
                                                        <h3 className="text-lg font-bold tracking-wide">
                                                            Стоп‑факторы: проверка перед участием
                                                        </h3>
                                                    </div>
                                                    <span className="px-3 py-1 rounded-full bg-red-600 text-xs font-semibold uppercase tracking-wide">
                                                        Рекомендуется не участвовать
                                                    </span>
                                                </div>
                                                <div className="space-y-4">
                                                    {result.dealBreakers.map((db, idx) => (
                                                        <div
                                                            key={`${db.title}-${idx}`}
                                                            className="bg-black/10 border border-red-400/40 rounded-xl p-4"
                                                        >
                                                            <div className="flex items-start justify-between gap-3">
                                                                <div>
                                                                    <h4 className="font-bold text-red-50 mb-1">
                                                                        {db.title}
                                                                    </h4>
                                                                    {db.status && (
                                                                        <p className="text-[11px] uppercase tracking-wide text-red-200 mb-2">
                                                                            {db.status}
                                                                        </p>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            {db.quote && (
                                                                <p className="text-xs text-red-100 bg-black/20 border border-red-400/30 rounded-lg p-3 italic mb-2 whitespace-pre-line">
                                                                    «{db.quote}»
                                                                </p>
                                                            )}
                                                            <p className="text-sm text-red-50 mb-2 whitespace-pre-line">
                                                                {db.essence}
                                                            </p>
                                                            <div className="flex flex-wrap items-center gap-2 justify-between">
                                                                <div className="text-[11px] text-red-200">
                                                                    {db.lawReference && (
                                                                        <span>
                                                                            Норма: <span className="font-semibold">{db.lawReference}</span>
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                {db.action && (
                                                                    <button
                                                                        type="button"
                                                                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500 hover:bg-red-400 text-xs font-semibold text-[#0f1419] transition-colors"
                                                                    >
                                                                        {db.action.buttonLabel}
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* HUB-ДАШБОРД ДЛЯ ТЕНДЕРНОГО СПЕЦИАЛИСТА */}
                                        {result.hub && (
                                            <TenderHubDashboard result={result} hub={result.hub} />
                                        )}

                                        {/* 1. VERDICT & SCORE (детальный блок, можно оставить как есть) */}
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            <div className={`col-span-2 p-6 rounded-2xl border flex items-center gap-6 relative overflow-hidden ${result.verdict === 'STOP' ? 'bg-[#ff4444]/10 border-[#ff4444]/30' :
                                                result.verdict === 'CAUTION' ? 'bg-[#f59e0b]/10 border-[#f59e0b]/30' :
                                                    'bg-[#00e648]/10 border-[#00e648]/30'
                                                }`}>
                                                <div className="absolute right-0 top-0 p-4 opacity-10">
                                                    <ShieldAlert size={100} className={result.verdict === 'STOP' ? 'text-[#ff4444]' : result.verdict === 'CAUTION' ? 'text-[#f59e0b]' : 'text-[#00e648]'} />
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${result.verdict === 'STOP' ? 'bg-[#ff4444] text-[#0f1419]' :
                                                            result.verdict === 'CAUTION' ? 'bg-[#f59e0b] text-[#0f1419]' :
                                                                'bg-[#00e648] text-[#0f1419]'
                                                            }`}>Вердикт системы</span>
                                                    </div>
                                                    <h3 className="text-2xl font-bold text-white mb-2 leading-tight">
                                                        {result.verdict === 'STOP' ? 'ВЫСОКИЙ РИСК' : result.verdict === 'CAUTION' ? 'ТРЕБУЕТ ВНИМАНИЯ' : 'БЕЗОПАСНО'}
                                                    </h3>
                                                    <p className="text-slate-300 text-base max-w-md relative z-10">{result.summary}</p>
                                                </div>
                                            </div>

                                            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 flex flex-col items-center justify-center relative">
                                                <div className="text-4xl font-bold text-white">{result.score}</div>
                                                <div className="text-slate-400 text-xs font-bold uppercase mt-1">Индекс безопасности</div>
                                            </div>
                                        </div>

                                        {/* 2. PASSPORT GRID */}
                                        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl overflow-hidden">
                                            <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441] flex items-center justify-between">
                                                <h3 className="text-white font-bold flex items-center gap-2">
                                                    <BadgeCheck className="text-[#00d4ff]" size={20} /> Паспорт Тендера
                                                </h3>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-slate-400 text-xs font-mono bg-[#1a1f2e] px-2 py-1 rounded border border-[#2a3441]">{result.passport.fz}</span>
                                                    <button
                                                        onClick={exportToExcel}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/30 rounded-lg text-xs font-bold transition-colors"
                                                        title="Экспорт в Excel"
                                                    >
                                                        <FileSpreadsheet size={14} />
                                                        Excel
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="p-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                                                <PassportItem label="НМЦК" value={result.passport.nmck} icon={Banknote} />
                                                <PassportItem label="Аванс" value={result.passport.advance} icon={Percent} />
                                                <PassportItem label="Обеспечение заявки" value={result.passport.secureBid} icon={ShieldCheck} />
                                                <PassportItem label="Срок исполнения" value={result.passport.deadlineExecution} icon={Calendar} />
                                                <PassportItem label="Регион" value={result.passport.region} icon={MapPin} />
                                            </div>
                                        </div>

                                        {/* 2b. Финансовый удар в рублях */}
                                        { (result as any).financialSummary && (
                                            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                                                <div className="flex items-center justify-between mb-4">
                                                    <h3 className="text-white font-bold flex items-center gap-2">
                                                        <Banknote className="text-[#22c55e]" size={18} /> Финансовый удар
                                                    </h3>
                                                </div>
                                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                                    <div>
                                                        <div className="text-slate-400 text-xs mb-1">Риск штрафов за 1 день просрочки</div>
                                                        <div className="text-white font-semibold">
                                                            {(result as any).financialSummary?.penaltyRiskRubles || '—'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-400 text-xs mb-1">Кассовый разрыв (оценка своих средств)</div>
                                                        <div className="text-white font-semibold">
                                                            {(result as any).financialSummary?.workingCapitalNeeded || '—'}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <div className="text-slate-400 text-xs mb-1">Обеспечение контракта</div>
                                                        <div className="text-white font-semibold">
                                                            {(result as any).financialSummary?.guaranteeAmount ||
                                                                (result as any).financialSummary?.contractSecurity ||
                                                                '—'}
                                                        </div>
                                                    </div>
                                                </div>
                                                <p className="mt-3 text-xs text-slate-400 max-w-2xl">
                                                    Это ориентировочная оценка по условиям контракта. Точные цифры считайте в калькуляторе маржи с учётом вашей себестоимости.
                                                </p>
                                            </div>
                                        )}

                                        {/* 3. Список рисков в человеко-понятном формате */}
                                        {result.issues && result.issues.length > 0 && (
                                            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 space-y-4">
                                                <div className="flex items-center justify-between mb-2">
                                                    <h3 className="text-white font-bold flex items-center gap-2">
                                                        <AlertTriangle className="text-[#f59e0b]" size={18} /> Ключевые риски
                                                    </h3>
                                                </div>
                                                <div className="space-y-3">
                                                    {result.issues.map((issue, idx) => (
                                                        <div
                                                            key={`${issue.title}-${idx}`}
                                                            className="border border-[#2a3441] rounded-xl p-4 bg-[#020617]"
                                                        >
                                                            <div className="flex justify-between items-start gap-3 mb-1">
                                                                <div>
                                                                    <h4 className="text-base font-semibold text-white mb-1">
                                                                        {issue.title}
                                                                    </h4>
                                                                    <p className="text-sm text-slate-200 whitespace-pre-line">
                                                                        {issue.description}
                                                                    </p>
                                                                </div>
                                                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                                                                    issue.severity === 'HIGH'
                                                                        ? 'bg-[#b91c1c] text-red-50'
                                                                        : issue.severity === 'MEDIUM'
                                                                        ? 'bg-[#f59e0b]/20 text-[#fbbf24]'
                                                                        : 'bg-[#16a34a]/20 text-[#4ade80]'
                                                                }`}>
                                                                    {issue.severity}
                                                                </span>
                                                            </div>
                                                            {issue.quote && (
                                                                <p className="mt-2 text-[11px] text-slate-300 italic bg-black/30 border border-[#1f2937] rounded-lg p-3 whitespace-pre-line">
                                                                    «{issue.quote}»
                                                                </p>
                                                            )}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* 4. DEEP AUDIT CHECKLIST (ЕСЛИ ЕСТЬ) */}
                                        {result.deepAudit && result.deepAudit.length > 0 && (
                                            <div className="space-y-4">
                                                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl overflow-hidden">
                                                    <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441] flex items-center justify-between">
                                                        <h3 className="text-white font-bold flex items-center gap-2">
                                                            <FileSpreadsheet className="text-[#00d4ff]" size={20} /> Глубокий Аудит
                                                        </h3>
                                                    </div>
                                                    <div className="p-6">
                                                        {result.deepAudit.map((block) => (
                                                            <DeepAuditRow
                                                                key={block.id}
                                                                block={block}
                                                                isExpanded={expandedBlock === block.id}
                                                                onToggle={() => setExpandedBlock(expandedBlock === block.id ? null : block.id)}
                                                            />
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        )}

                                        {/* 5. СТРУКТУРИРОВАННЫЕ ОТВЕТЫ НА 25 ВОПРОСОВ */}
                                        {result.structuredAnswers && Object.keys(result.structuredAnswers).length > 0 && (
                                            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl overflow-hidden">
                                                <div className="bg-[#0f1419] px-6 py-4 border-b border-[#2a3441]">
                                                    <h3 className="text-white font-bold flex items-center gap-2 text-lg">
                                                        <FileText className="text-[#00d4ff]" size={20} /> Структурированный анализ по чек-листу
                                                    </h3>
                                                    <p className="text-slate-400 text-sm mt-1">Ответы на 25 ключевых вопросов тендерного анализа</p>
                                                </div>
                                                <div className="p-6 space-y-4">
                                                    {[
                                                        { key: 'customer', label: '1. Заказчик (ИНН, ОГРН, местонахождение)' },
                                                        { key: 'subject', label: '2. Предмет закупки' },
                                                        { key: 'nmck', label: '3. Начальная (максимальная) цена контракта' },
                                                        { key: 'applicationDeadline', label: '4. Сроки подачи заявок' },
                                                        { key: 'executionDeadline', label: '5. Сроки исполнения контракта' },
                                                        { key: 'participantRequirements', label: '6. Требования к участникам (опыт, лицензии, сертификации)' },
                                                        { key: 'securityAmounts', label: '7. Обеспечительные суммы (заявка и контракт)' },
                                                        { key: 'paymentTerms', label: '8. Условия оплаты (предоплата, постоплата, авансы)' },
                                                        { key: 'evaluationCriteria', label: '9. Критерии оценки заявок и методика присуждения' },
                                                        { key: 'contradictions', label: '10. Противоречия и неоднозначные формулировки' },
                                                        { key: 'penalties', label: '11. Штрафы и санкции за нарушение сроков и условий' },
                                                        { key: 'guarantees', label: '12. Гарантии и сервисное обслуживание' },
                                                        { key: 'additionalRequirements', label: '13. Дополнительные требования (поставка, монтаж, обучение)' },
                                                        { key: 'tenderRisks', label: '14. Риски изменения или отмены тендера' },
                                                        { key: 'documentationRequirements', label: '15. Требования по оформлению и комплектности документов' },
                                                        { key: 'financialRequirements', label: '16. Требования к финансовому положению и отчетности' },
                                                        { key: 'confidentiality', label: '17. Условия конфиденциальности и коммерческой тайны' },
                                                        { key: 'customerHistory', label: '18. История заказчика (жалобы, судебные дела)' },
                                                        { key: 'subcontractingLimits', label: '19. Ограничения по субподряду или участию юридических лиц' },
                                                        { key: 'conflictsOfInterest', label: '20. Возможные конфликты интересов' },
                                                        { key: 'discriminationSigns', label: '21. Признаки дискриминации или «заточки» под конкретного поставщика' },
                                                        { key: 'terminationConditions', label: '22. Условия расторжения и изменения контракта' },
                                                        { key: 'competitionLevel', label: '23. Уровень конкуренции и количество возможных участников' },
                                                        { key: 'insuranceRequirements', label: '24. Требования к страхованию ответственности' },
                                                        { key: 'additionalRisks', label: '25. Дополнительные риски и особенности участия' },
                                                    ].map(({ key, label }) => {
                                                        const answer = result.structuredAnswers?.[key as keyof typeof result.structuredAnswers];
                                                        if (!answer || answer === 'Не указано' || answer === 'Не найдено') return null;
                                                        return (
                                                            <div key={key} className="border border-[#2a3441] rounded-xl p-4 bg-[#020617]">
                                                                <div className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-2">{label}</div>
                                                                <div className="text-sm text-white leading-relaxed whitespace-pre-line">{answer}</div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}
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

            {/* Модальное окно с предложением регистрации */}
            <RegisterSuggestionModal
                type={registerModalType}
                visible={showRegisterModal}
                onRegister={() => {
                    setShowRegisterModal(false);
                    window.location.href = '/register';
                }}
                onDismiss={() => setShowRegisterModal(false)}
            />
        </>
    );
};

export default Analyzer;