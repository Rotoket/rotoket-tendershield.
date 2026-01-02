import React, { useState, useEffect } from 'react';
import { FileText, Download, PenTool, CheckSquare, X, Loader2, Copy, Unlock, AlertTriangle } from 'lucide-react';
import { logEvent } from '../utils/logger';
import { UserDecision } from '../types';
import { isActionAllowed, getActionBlockedMessage, type ActionType } from '../utils/decisionRules';
import {
    ProtocolRowForm,
    ViolationForm,
    buildProtocolDraft,
    buildComplaintDraft,
} from '../utils/docDrafts';

interface DocumentGeneratorProps {
  initialData?: {
    dealBreakers?: string[];
    smartQuestions?: string[];
    tenderNumber?: string;
    customer?: string;
  };
  decision?: UserDecision;
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
            hypothesisId: 'DocumentGenerator'
        })
    }).catch(() => {});
};

const DocumentGenerator: React.FC<DocumentGeneratorProps> = ({ initialData, decision: decisionProp }) => {
    // Decision должен приходить из App.tsx (единственный источник истины)
    // localStorage используется ТОЛЬКО как fallback для legacy-совместимости
    const getDecision = (): UserDecision | null => {
        // Приоритет: пропс из App.tsx
        if (decisionProp) return decisionProp;
        // Fallback: localStorage (только для legacy, не primary)
        try {
            const stored = localStorage.getItem('last_user_decision');
            return stored ? JSON.parse(stored) : null;
        } catch {
            return null;
        }
    };
    
    const [decision] = useState<UserDecision | null>(getDecision());
    // #region agent log
    debugLog('DocumentGenerator.tsx:init', 'DocumentGenerator initialized', {
        hasInitialData: !!initialData,
        dealBreakersCount: initialData?.dealBreakers?.length || 0,
        smartQuestionsCount: initialData?.smartQuestions?.length || 0
    });
    // #endregion
    const [activeTool, setActiveTool] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedResult, setGeneratedResult] = useState<string>('');
    const [generatedKind, setGeneratedKind] = useState<'protocol' | 'complaint' | null>(null);

    // Протокол разногласий
    const [protocolTenderNumber, setProtocolTenderNumber] = useState(initialData?.tenderNumber || '');
    const [protocolCustomer, setProtocolCustomer] = useState(initialData?.customer || '');
    const [protocolSubject, setProtocolSubject] = useState('');
    const [protocolRef, setProtocolRef] = useState('');
    const [protocolRows, setProtocolRows] = useState<ProtocolRowForm[]>(
        initialData?.dealBreakers && initialData.dealBreakers.length > 0
            ? initialData.dealBreakers.map(breaker => ({
                clause: breaker,
                customerVersion: breaker,
                supplierVersion: 'Требуется уточнение',
                justification: 'Выявлено при анализе тендерной документации',
            }))
            : [{ clause: '', customerVersion: '', supplierVersion: '', justification: '' }]
    );

    // Жалоба в ФАС
    const [complaintTo, setComplaintTo] = useState('Территориальное управление ФАС России');
    const [complaintFrom, setComplaintFrom] = useState('ООО "Участник"');
    const [complaintTenderNumber, setComplaintTenderNumber] = useState(initialData?.tenderNumber || '');
    const [complaintCustomer, setComplaintCustomer] = useState(initialData?.customer || '');
    const [complaintTopic, setComplaintTopic] = useState('Жалоба на документацию электронного аукциона');
    const [complaintRef, setComplaintRef] = useState('');
    const [violations, setViolations] = useState<ViolationForm[]>(
        initialData?.dealBreakers && initialData.dealBreakers.length > 0
            ? initialData.dealBreakers.map(breaker => ({
                point: breaker,
                argument: 'Выявлено при анализе тендерной документации',
                law: '44-ФЗ',
            }))
            : [{ point: '', argument: '', law: '' }]
    );

    // Определяем доступность инструментов на основе решения
    const isProtocolAllowed = isActionAllowed(decision, 'generator_protocol');
    const isComplaintAllowed = isActionAllowed(decision, 'generator_refusal');
    const isGeneratorDisabled = decision?.decision === 'postpone' || (!decision && !isProtocolAllowed && !isComplaintAllowed);

    const tools = [
        {
            id: 'protocol',
            title: 'Протокол разногласий',
            desc: 'Генерация таблицы разногласий с автоматическим юридическим обоснованием.',
            icon: FileText,
            allowed: isProtocolAllowed,
        },
        {
            id: 'complaint',
            title: 'Жалоба в ФАС',
            desc: 'Автоматическая генерация текста жалобы с ссылками на практику ФАС.',
            icon: PenTool,
            allowed: isComplaintAllowed,
        },
    ].filter(tool => tool.allowed);

    // Автоматически открываем протокол, если есть данные из анализа
    useEffect(() => {
        if (initialData?.dealBreakers && initialData.dealBreakers.length > 0 && !activeTool) {
            // #region agent log
            debugLog('DocumentGenerator.tsx:useEffect:autoOpen', 'Auto-opening protocol with analysis data', {
                dealBreakersCount: initialData.dealBreakers.length,
                dealBreakers: initialData.dealBreakers
            });
            // #endregion
            setActiveTool('protocol');
            logEvent('DocumentGenerator', 'Автоматически открыт протокол разногласий с данными из анализа', 'info');
        }
    }, [initialData]);
    
    // ❌ Убрано: слушание localStorage (decision должен приходить из App.tsx)

    const closeTool = () => {
        logEvent('DocumentGenerator', 'Закрыта модалка генератора документов');
        setActiveTool(null);
        setGeneratedResult('');
        setGeneratedKind(null);
        setIsGenerating(false);
    };

    const handleAddProtocolRow = () => {
        setProtocolRows([
            ...protocolRows,
            { clause: '', customerVersion: '', supplierVersion: '', justification: '' },
        ]);
    };

    const handleRemoveProtocolRow = (index: number) => {
        setProtocolRows(protocolRows.filter((_, i) => i !== index));
    };

    const handleProtocolRowChange = (index: number, field: keyof ProtocolRowForm, value: string) => {
        const updated = [...protocolRows];
        updated[index] = { ...updated[index], [field]: value };
        setProtocolRows(updated);
    };

    const handleAddViolation = () => {
        setViolations([...violations, { point: '', argument: '', law: '' }]);
    };

    const handleRemoveViolation = (index: number) => {
        setViolations(violations.filter((_, i) => i !== index));
    };

    const handleViolationChange = (index: number, field: keyof ViolationForm, value: string) => {
        const updated = [...violations];
        updated[index] = { ...updated[index], [field]: value };
        setViolations(updated);
    };

    const generateProtocolText = (): string => {
        return buildProtocolDraft({
            tenderNumber: protocolTenderNumber,
            customer: protocolCustomer,
            subject: protocolSubject,
            ref: protocolRef,
            rows: protocolRows,
            decision: decision,
        });
    };

    const generateComplaintText = (): string => {
        return buildComplaintDraft({
            to: complaintTo,
            from: complaintFrom,
            tenderNumber: complaintTenderNumber,
            customer: complaintCustomer,
            topic: complaintTopic,
            ref: complaintRef,
            violations,
            decision: decision,
        });
    };

    const handleGenerate = async (kind: 'protocol' | 'complaint') => {
        // Проверяем наличие решения
        if (!decision) {
            logEvent('DocumentGenerator', 'Попытка генерации отчёта без решения', 'warn');
            return;
        }

        try {
            setIsGenerating(true);
            
            logEvent('Report', 'report_generation_started', 'info', {
                decision: decision.decision,
                reportType: kind === 'protocol' ? 'protocol' : 'complaint',
                source: 'DocumentGenerator',
            });
            
            logEvent(
                'DocumentGenerator',
                kind === 'protocol'
                    ? 'Нажата кнопка "Сформировать протокол разногласий"'
                    : 'Нажата кнопка "Сформировать жалобу в ФАС"',
            );
            
            let text = '';
            if (kind === 'protocol') {
                text = generateProtocolText();
            } else {
                text = generateComplaintText();
            }
            setGeneratedResult(text);
            setGeneratedKind(kind);
            
            logEvent('Report', 'report_generated', 'info', {
                decision: decision.decision,
                reportType: kind === 'protocol' ? 'protocol' : 'complaint',
                source: 'DocumentGenerator',
            });
            
            logEvent(
                'DocumentGenerator',
                kind === 'protocol'
                    ? 'Черновик протокола разногласий успешно сформирован'
                    : 'Черновик жалобы в ФАС успешно сформирован',
            );
        } finally {
            setIsGenerating(false);
        }
    };

    const handleDownload = () => {
        if (!generatedResult || !generatedKind) return;
        logEvent(
            'DocumentGenerator',
            generatedKind === 'protocol'
                ? 'Скачивание .txt протокола разногласий'
                : 'Скачивание .txt жалобы в ФАС',
        );
        const blob = new Blob([generatedResult], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = generatedKind === 'protocol' ? 'protocol_disagreements.txt' : 'complaint_fas.txt';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleCopy = async () => {
        if (!generatedResult) return;
        try {
            await navigator.clipboard.writeText(generatedResult);
            logEvent('DocumentGenerator', 'Черновик документа скопирован в буфер обмена');
        } catch {
            logEvent('DocumentGenerator', 'Ошибка копирования черновика в буфер обмена', 'warn');
        }
    };

    // Логируем блокировку/разрешение действий при изменении decision
    useEffect(() => {
        if (decision) {
            const protocolAllowed = isActionAllowed(decision, 'generator_protocol');
            const complaintAllowed = isActionAllowed(decision, 'generator_refusal');
            
            if (protocolAllowed) {
                logEvent('Decision', 'decision_action_allowed', 'info', {
                    decision: decision.decision,
                    action: 'generator_protocol',
                    source: 'DocumentGenerator',
                });
            } else {
                logEvent('Decision', 'decision_action_blocked', 'info', {
                    decision: decision.decision,
                    action: 'generator_protocol',
                    source: 'DocumentGenerator',
                });
            }
            
            if (complaintAllowed) {
                logEvent('Decision', 'decision_action_allowed', 'info', {
                    decision: decision.decision,
                    action: 'generator_refusal',
                    source: 'DocumentGenerator',
                });
            } else {
                logEvent('Decision', 'decision_action_blocked', 'info', {
                    decision: decision.decision,
                    action: 'generator_refusal',
                    source: 'DocumentGenerator',
                });
            }
        } else {
            // Если решения нет - логируем блокировку
            logEvent('Decision', 'decision_action_blocked', 'info', {
                decision: undefined,
                action: 'generator',
                source: 'DocumentGenerator',
            });
        }
    }, [decision]);

    // Если решение не зафиксировано — показываем экран блокировки
    if (!decision) {
        return (
            <div className="animate-fade-in relative h-full flex flex-col items-center justify-center">
                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 max-w-md text-center">
                    <AlertTriangle size={48} className="text-slate-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-4">Сначала зафиксируйте решение</h2>
                    <p className="text-slate-400 text-sm mb-4">
                        Для использования генератора документов необходимо зафиксировать решение по тендеру в режиме анализа.
                    </p>
                    <p className="text-xs text-slate-500">
                        Вернитесь к анализу и зафиксируйте решение в режиме директора.
                    </p>
                </div>
            </div>
        );
    }

    // Если генератор недоступен по другим причинам (например, решение = postpone)
    if (isGeneratorDisabled) {
        const blockedMessage = getActionBlockedMessage(decision, 'generator');
        return (
            <div className="animate-fade-in relative h-full flex flex-col items-center justify-center">
                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 max-w-md text-center">
                    <AlertTriangle size={48} className="text-slate-400 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-white mb-4">Генератор недоступен</h2>
                    <p className="text-slate-400 text-sm">{blockedMessage}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="animate-fade-in relative h-full flex flex-col">
            <div className="mb-6 flex justify-between items-center">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Инструментарий</h2>
                    <p className="text-slate-400">Генерация документов с поддержкой AI</p>
                    {decision?.decision === 'participate_with_conditions' && (
                        <p className="text-xs text-yellow-400 mt-1">⚠️ Генерация с учётом условий участия</p>
                    )}
                </div>
                <div className="flex items-center gap-2 bg-[#00d4ff]/10 text-[#00d4ff] px-3 py-1.5 rounded-full text-xs font-bold border border-[#00d4ff]/20">
                    <Unlock size={14} /> PRO Функции активны
                </div>
            </div>

            {tools.length === 0 ? (
                <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 text-center">
                    <AlertTriangle size={32} className="text-slate-400 mx-auto mb-3" />
                    <p className="text-slate-400 text-sm">{getActionBlockedMessage(decision, 'generator')}</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {tools.map(tool => (
                        <div
                            key={tool.id}
                            onClick={() => {
                                setActiveTool(tool.id);
                                logEvent(
                                    'DocumentGenerator',
                                    tool.id === 'protocol'
                                        ? 'Открыт инструмент "Протокол разногласий"'
                                        : 'Открыт инструмент "Жалоба в ФАС"',
                                );
                            }}
                            className="border rounded-2xl p-6 transition-all group cursor-pointer relative overflow-hidden bg-[#1a1f2e] border-[#2a3441] hover:border-[#00d4ff]"
                        >
                            <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 bg-[#0f1419] text-[#00d4ff] border border-[#2a3441]">
                                <tool.icon size={24} />
                            </div>

                            <h3 className="text-xl font-bold mb-2 text-white">{tool.title}</h3>
                            <p className="text-slate-400 text-sm leading-relaxed mb-6 h-10">{tool.desc}</p>

                            <button className="w-full py-2 rounded-lg text-sm font-bold border transition-all bg-[#0f1419] border-[#2a3441] text-white group-hover:bg-[#00d4ff] group-hover:text-[#0f1419] group-hover:border-[#00d4ff]">
                                Открыть инструмент
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* MODALS */}
            {activeTool && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6 animate-fade-in">
                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl w-full max-w-6xl h-[82vh] flex flex-col shadow-2xl overflow-hidden">
                        <div className="p-5 border-b border-[#2a3441] flex justify-between items-center bg-[#1a1f2e]">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <FileText className="text-[#00d4ff]" /> Генератор документов
                                </h3>
                                <p className="text-xs text-slate-400">
                                    Черновики протокола разногласий и жалобы в ФАС. Текст является шаблоном и требует проверки юристом.
                                </p>
                            </div>
                            <button onClick={closeTool} className="text-slate-400 hover:text-white transition-colors">
                                <X size={24} />
                            </button>
                        </div>

                        {/* Содержимое модалки */}
                        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
                            {/* Левая панель: форма */}
                            <div className="w-full md:w-1/2 border-b md:border-b-0 md:border-r border-[#2a3441] p-5 space-y-4 overflow-auto custom-scrollbar text-sm">
                                {activeTool === 'protocol' && (
                                    <>
                                        <h4 className="text-white font-semibold mb-1">Протокол разногласий</h4>
                                        <p className="text-xs text-slate-400 mb-3">
                                            Заполните сведения о закупке и таблицу разногласий. Получится текстовый протокол, который можно вложить в ответ на проект контракта.
                                        </p>

                                        <div className="space-y-2 mb-4">
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Номер закупки / извещения</label>
                                                <input
                                                    value={protocolTenderNumber}
                                                    onChange={e => setProtocolTenderNumber(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="Например, 0445300000123000123"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Заказчик</label>
                                                <input
                                                    value={protocolCustomer}
                                                    onChange={e => setProtocolCustomer(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="Наименование заказчика"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Предмет закупки</label>
                                                <input
                                                    value={protocolSubject}
                                                    onChange={e => setProtocolSubject(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="Поставка..., выполнение работ..."
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Ссылка на извещение / контракт (ЕИС/ЭТП)</label>
                                                <input
                                                    value={protocolRef}
                                                    onChange={e => setProtocolRef(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="https://..."
                                                />
                                            </div>
                                        </div>

                                        {/* Обязательный блок условий для participate_with_conditions */}
                                        {decision?.decision === 'participate_with_conditions' && (
                                            <div className="mb-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <AlertTriangle size={16} className="text-yellow-400" />
                                                    <h5 className="text-xs font-semibold text-yellow-400">Условия участия</h5>
                                                </div>
                                                <p className="text-xs text-slate-300 mb-2">
                                                    При решении "Участвовать с условиями" необходимо явно указать условия в протоколе разногласий.
                                                </p>
                                            </div>
                                        )}

                                        <div className="flex items-center justify-between mb-2">
                                            <h5 className="text-xs font-semibold text-slate-200">Таблица разногласий</h5>
                                            <button
                                                type="button"
                                                onClick={handleAddProtocolRow}
                                                className="text-[11px] px-2 py-1 rounded border border-[#2a3441] text-slate-200 hover:border-[#00d4ff] hover:text-[#00d4ff]"
                                            >
                                                + Добавить строку
                                            </button>
                                        </div>
                                        <div className="space-y-3">
                                            {protocolRows.map((row, idx) => (
                                                <div
                                                    key={idx}
                                                    className="border border-[#2a3441] rounded-lg p-3 bg-[#0f1419] space-y-2"
                                                >
                                                    <div className="flex justify_between items-center mb-1">
                                                        <span className="text-[11px] text-slate-400">Строка {idx + 1}</span>
                                                        {protocolRows.length > 1 && (
                                                            <button
                                                                type="button"
                                                                onClick={() => handleRemoveProtocolRow(idx)}
                                                                className="text-[10px] text-slate-500 hover:text-red-400"
                                                            >
                                                                Удалить
                                                            </button>
                                                        )}
                                                    </div>
                                                    <textarea
                                                        value={row.clause}
                                                        onChange={e => handleProtocolRowChange(idx, 'clause', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Пункт проекта контракта (например, п. 3.2.1)"
                                                        rows={1}
                                                    />
                                                    <textarea
                                                        value={row.customerVersion}
                                                        onChange={e => handleProtocolRowChange(idx, 'customerVersion', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Редакция заказчика (как в проекте контракта)"
                                                        rows={2}
                                                    />
                                                    <textarea
                                                        value={row.supplierVersion}
                                                        onChange={e => handleProtocolRowChange(idx, 'supplierVersion', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Предлагаемая редакция участника"
                                                        rows={2}
                                                    />
                                                    <textarea
                                                        value={row.justification}
                                                        onChange={e => handleProtocolRowChange(idx, 'justification', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Обоснование (ссылка на закон/практику или деловые причины)"
                                                        rows={2}
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <p className="mt-3 text-[10px] text-slate-500 flex items-start gap-1">
                                            <AlertTriangle size={12} className="text-amber-400 mt-0.5" />
                                            <span>
                                                Система формирует черновик протокола разногласий. Перед направлением заказчику проверьте формулировки с юристом и учтите ограничения по 44-ФЗ/223-ФЗ.
                                            </span>
                                        </p>
                                    </>
                                )}

                                {activeTool === 'complaint' && (
                                    <>
                                        <h4 className="text-white font-semibold mb-1">Жалоба в ФАС</h4>
                                        <p className="text-xs text-slate-400 mb-3">
                                            Заполните реквизиты и нарушения. На выходе — структурированный текст жалобы, который можно доработать с юристом.
                                        </p>

                                        <div className="space-y-2 mb-4">
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Адресат (УФАС)</label>
                                                <input
                                                    value={complaintTo}
                                                    onChange={e => setComplaintTo(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Заявитель</label>
                                                <input
                                                    value={complaintFrom}
                                                    onChange={e => setComplaintFrom(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="Наименование и реквизиты участника"
                                                />
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                <div>
                                                    <label className="text-xs text-slate-400 mb-1 block">Номер закупки / извещения</label>
                                                    <input
                                                        value={complaintTenderNumber}
                                                        onChange={e => setComplaintTenderNumber(e.target.value)}
                                                        className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    />
                                                </div>
                                                <div>
                                                    <label className="text-xs text-slate-400 mb-1 block">Заказчик</label>
                                                    <input
                                                        value={complaintCustomer}
                                                        onChange={e => setComplaintCustomer(e.target.value)}
                                                        className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    />
                                                </div>
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Ссылка на закупку (ЕИС/ЭТП)</label>
                                                <input
                                                    value={complaintRef}
                                                    onChange={e => setComplaintRef(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    placeholder="https://..."
                                                />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-400 mb-1 block">Общее описание жалобы</label>
                                                <textarea
                                                    value={complaintTopic}
                                                    onChange={e => setComplaintTopic(e.target.value)}
                                                    className="w-full bg-[#0f1419] border border-[#2a3441] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-[#00d4ff]"
                                                    rows={2}
                                                />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between mb-2">
                                            <h5 className="text-xs font-semibold text-slate-200">Нарушения</h5>
                                            <button
                                                type="button"
                                                onClick={handleAddViolation}
                                                className="text-[11px] px-2 py-1 rounded border border-[#2a3441] text-slate-200 hover:border-[#00d4ff] hover:text-[#00d4ff]"
                                            >
                                                + Добавить нарушение
                                            </button>
                                        </div>
                                        <div className="space-y-3">
                                            {violations.map((v, idx) => (
                                                <div
                                                    key={idx}
                                                    className="border border-[#2a3441] rounded-lg p-3 bg-[#0f1419] space-y-2"
                                                >
                                                    <div className="flex justify_between items-center mb-1">
                                                        <span className="text-[11px] text-slate-400">Нарушение {idx + 1}</span>
                                                        {violations.length > 1 && (
                                                            <button
                                                                type="button"
                                                                onClick={() => handleRemoveViolation(idx)}
                                                                className="text-[10px] text-slate-500 hover:text-red-400"
                                                            >
                                                                Удалить
                                                            </button>
                                                        )}
                                                    </div>
                                                    <textarea
                                                        value={v.point}
                                                        onChange={e => handleViolationChange(idx, 'point', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Пункт документации (например, п. 1.2.3 ТЗ)"
                                                        rows={1}
                                                    />
                                                    <textarea
                                                        value={v.argument}
                                                        onChange={e => handleViolationChange(idx, 'argument', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Почему пункт нарушает 44-ФЗ/135-ФЗ, как ограничивает конкуренцию и ваши права"
                                                        rows={2}
                                                    />
                                                    <textarea
                                                        value={v.law}
                                                        onChange={e => handleViolationChange(idx, 'law', e.target.value)}
                                                        className="w-full bg-[#020617] border border-[#2a3441] rounded-lg px-2 py-1 text-[11px] text-white focus:outline-none focus:border-[#00d4ff]"
                                                        placeholder="Нормы закона (например, ч.1 ст.33 44-ФЗ; ст.15 135-ФЗ)"
                                                        rows={1}
                                                    />
                                                </div>
                                            ))}
                                        </div>

                                        <p className="mt-3 text-[10px] text-slate-500 flex items-start gap-1">
                                            <AlertTriangle size={12} className="text-amber-400 mt-0.5" />
                                            <span>
                                                Система формирует черновик жалобы. Окончательный текст, перечень приложений и сроки подачи жалобы должны быть проверены юристом с учётом фактической ситуации.
                                            </span>
                                        </p>
                                    </>
                                )}
                            </div>

                            {/* Правая панель: предпросмотр и действия */}
                            <div className="w-full md:w-1/2 p-5 flex flex-col bg-[#0f1419]">
                                <div className="flex items-center justify-between mb-3">
                                    <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                                        <CheckSquare size={16} className="text-[#00d4ff]" /> Предпросмотр черновика
                                    </h4>
                                    <div className="flex gap-2">
                                        {!decision && (
                                            <div className="mb-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                                <p className="text-[10px] text-amber-400">
                                                    ⚠️ Отчёт формируется после фиксации решения
                                                </p>
                                            </div>
                                        )}
                                        <button
                                            type="button"
                                            onClick={() =>
                                                handleGenerate(activeTool === 'protocol' ? 'protocol' : 'complaint')
                                            }
                                            disabled={isGenerating || !decision}
                                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#00d4ff] text-[#0f1419] text-xs font-semibold hover:bg-[#06b6d4] disabled:opacity-60 disabled:cursor-not-allowed"
                                            title={!decision ? 'Отчёт фиксирует принятое решение' : undefined}
                                        >
                                            {isGenerating ? (
                                                <Loader2 size={14} className="animate-spin" />
                                            ) : (
                                                <PenTool size={14} />
                                            )}
                                            Сформировать
                                        </button>
                                        {decision && (
                                            <p className="mt-1 text-[10px] text-slate-400 text-center">
                                                Отчёт фиксирует принятое решение
                                            </p>
                                        )}
                                        <button
                                            type="button"
                                            onClick={handleCopy}
                                            disabled={!generatedResult}
                                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#2a3441] text-xs text-slate-200 hover:border-[#00d4ff] disabled:opacity-40"
                                        >
                                            <Copy size={14} /> Копировать
                                        </button>
                                        <button
                                            type="button"
                                            onClick={handleDownload}
                                            disabled={!generatedResult}
                                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-[#2a3441] text-xs text-slate-200 hover:border-[#00d4ff] disabled:opacity-40"
                                        >
                                            <Download size={14} /> .txt
                                        </button>
                                    </div>
                                </div>

                                <div className="flex-1 border border-[#2a3441] rounded-lg bg-[#020617] p-3 overflow-auto text-xs text-slate-200 font-mono whitespace-pre-wrap">
                                    {generatedResult ? (
                                        generatedResult
                                    ) : (
                                        <span className="text-slate-500">
                                            {decision 
                                                ? 'Заполните поля слева и нажмите «Сформировать», чтобы увидеть черновик документа.'
                                                : 'Сначала зафиксируйте решение по тендеру, затем сформируйте отчёт.'}
                                        </span>
                                    )}
                                </div>
                                <p className="mt-2 text-[10px] text-slate-500 flex items-start gap-1">
                                    <AlertTriangle size={12} className="text-amber-400 mt-0.5" />
                                    <span>
                                        Черновики формируются автоматически и не являются юридической консультацией. Проверьте текст и согласуйте его с ответственным специалистом до отправки заказчику или в ФАС.
                                    </span>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DocumentGenerator;