import React, { useState, useEffect, useRef } from 'react';
import { Tender, RiskAnalysis, ChatMessage, ProtocolRow, TenderDocument, ComplaintDraft } from '../types';
import { analyzeTenderDocuments, chatWithLegalAssistant, generateProtocolOfDisagreements, generateComplaintDraft } from '../services/geminiService';
import { 
  AlertTriangle, CheckCircle, Send, Bot, 
  AlertOctagon, Download, ChevronRight, Gavel, 
  FileText, Shield, Scale, X, Loader2, Upload,
  File as FileIcon, Trash2, Eye, Printer
} from 'lucide-react';

interface TenderDetailProps {
  tender: Tender;
  onBack: () => void;
}

// Helper: Gauge Chart
const GaugeChart = ({ value, label, colorClass }: { value: number, label: string, colorClass: string }) => {
  const angle = (value / 100) * 180;
  return (
    <div className="relative flex flex-col items-center justify-center">
      <div className="relative w-40 h-24 overflow-hidden">
         <div className="absolute top-0 left-0 w-full h-40 bg-slate-100 rounded-full border-[12px] border-slate-100 box-border"></div>
         <div 
            className={`absolute top-0 left-0 w-full h-40 rounded-full border-[12px] ${colorClass} box-border origin-center transition-transform duration-1000 ease-out`}
            style={{ 
                clipPath: 'polygon(0 0, 100% 0, 100% 50%, 0 50%)',
                transform: `rotate(${angle - 180}deg)` 
            }}
         ></div>
      </div>
      <div className="absolute top-12 flex flex-col items-center">
        <span className={`text-3xl font-bold ${colorClass.replace('border-', 'text-')}`}>{value}%</span>
        <span className="text-xs text-slate-400 uppercase font-semibold tracking-wider mt-1">{label}</span>
      </div>
    </div>
  );
};

// Component: File Upload & List
const DocumentsSection = ({ 
    files, 
    onUpload, 
    onDelete 
}: { 
    files: TenderDocument[], 
    onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void,
    onDelete: (id: string) => void
}) => {
    return (
        <div className="space-y-6">
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 flex flex-col items-center justify-center text-center hover:border-blue-500 hover:bg-blue-50 transition-all cursor-pointer relative">
                <input 
                    type="file" 
                    multiple 
                    onChange={onUpload} 
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="bg-blue-100 p-4 rounded-full text-blue-600 mb-3">
                    <Upload size={32} />
                </div>
                <h4 className="font-bold text-slate-700">Загрузите документацию</h4>
                <p className="text-sm text-slate-500 mt-1">Перетащите файлы PDF, DOCX или нажмите для выбора</p>
                <p className="text-xs text-slate-400 mt-2">ИИ автоматически распознает ТЗ, Проект контракта и Сметы</p>
            </div>

            <div className="space-y-3">
                <h4 className="font-bold text-slate-900 text-sm uppercase tracking-wide">Загруженные файлы ({files.length})</h4>
                {files.length === 0 && <p className="text-slate-400 text-sm italic">Нет файлов. Загрузите документацию для точного анализа.</p>}
                {files.map(file => (
                    <div key={file.id} className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-lg hover:shadow-sm transition-shadow">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${file.type === 'pdf' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'}`}>
                                <FileIcon size={20} />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-slate-800">{file.name}</p>
                                <p className="text-xs text-slate-500">{file.size} • {file.uploadDate.toLocaleDateString()}</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {file.status === 'scanning' && (
                                <span className="flex items-center gap-1 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full animate-pulse">
                                    <Loader2 size={10} className="animate-spin" /> Сканирование...
                                </span>
                            )}
                             {file.status === 'scanned' && (
                                <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-1 rounded-full">
                                    Готово
                                </span>
                            )}
                            <button onClick={() => onDelete(file.id)} className="p-2 text-slate-400 hover:text-red-500 transition-colors">
                                <Trash2 size={16} />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const TenderDetail: React.FC<TenderDetailProps> = ({ tender, onBack }) => {
  const [analysis, setAnalysis] = useState<RiskAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [scanStep, setScanStep] = useState<string>(''); // For scan visualization
  const [activeTab, setActiveTab] = useState<'analysis' | 'documents'>('documents');
  
  // Documents State
  const [documents, setDocuments] = useState<TenderDocument[]>([]);

  // Protocol & Complaint Modal States
  const [protocolRows, setProtocolRows] = useState<ProtocolRow[]>([]);
  const [complaintDraft, setComplaintDraft] = useState<ComplaintDraft | null>(null);
  
  const [isGeneratingProtocol, setIsGeneratingProtocol] = useState(false);
  const [showProtocolModal, setShowProtocolModal] = useState(false);
  
  const [isGeneratingComplaint, setIsGeneratingComplaint] = useState(false);
  const [showComplaintModal, setShowComplaintModal] = useState(false);

  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'model',
      text: 'Загрузите тендерную документацию, и я проведу полный правовой аудит по 44-ФЗ.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // File Upload Handler
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
        const newFiles: TenderDocument[] = Array.from(e.target.files).map((f: File) => ({
            id: Math.random().toString(36).substr(2, 9),
            name: f.name,
            size: (f.size / 1024 / 1024).toFixed(2) + ' MB',
            type: f.name.endsWith('pdf') ? 'pdf' : 'docx',
            uploadDate: new Date(),
            status: 'pending'
        }));
        
        setDocuments(prev => [...prev, ...newFiles]);
        setActiveTab('analysis'); // Switch to analysis view to show progress
        runAnalysis(newFiles); // Trigger AI analysis
    }
  };

  const deleteDocument = (id: string) => {
      setDocuments(prev => prev.filter(d => d.id !== id));
  };

  const runAnalysis = async (filesToScan: TenderDocument[]) => {
      setIsAnalyzing(true);
      
      // Visual Simulation of Deep Scanning
      const steps = [
          "OCR распознавание текста...",
          "Поиск несоответствий КТРУ...",
          "Сверка с Постановлением №2604...",
          "Анализ штрафных санкций...",
          "Проверка сроков оплаты..."
      ];

      for (const step of steps) {
          setScanStep(step);
          await new Promise(r => setTimeout(r, 600)); // Simulate work
      }
      setScanStep("Формирование отчета...");

      try {
        const fileNames = filesToScan.map(f => f.name);
        const result = await analyzeTenderDocuments(fileNames, tender.description);
        setAnalysis(result);
        
        // Update file status
        setDocuments(prev => prev.map(d => ({...d, status: 'scanned'})));
        
        // Add chat notification
        setMessages(prev => [...prev, {
            id: Date.now().toString(),
            role: 'model',
            text: `Анализ завершен. Я нашел ${result.issues.length} проблемных мест. Обратите внимание на нарушение ст. 33 44-ФЗ.`,
            timestamp: new Date()
        }]);

      } catch (err) {
        console.error(err);
      } finally {
        setIsAnalyzing(false);
        setScanStep('');
      }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      text: inputMessage,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsChatLoading(true);

    try {
      const history = messages.map(m => ({ role: m.role, text: m.text }));
      const responseText = await chatWithLegalAssistant(history, userMsg.text, tender.description);
      
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'model',
        text: responseText || 'Сервис временно недоступен.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleGenerateProtocol = async () => {
    if (!analysis) return;
    setIsGeneratingProtocol(true);
    setShowProtocolModal(true);
    try {
        const issuesSummary = analysis.issues.map(i => i.title).join("; ");
        const rows = await generateProtocolOfDisagreements(tender.description, issuesSummary);
        setProtocolRows(rows);
    } catch (e) { console.error(e); } 
    finally { setIsGeneratingProtocol(false); }
  };

  const handleGenerateComplaint = async () => {
      if (!analysis) return;
      setIsGeneratingComplaint(true);
      setShowComplaintModal(true);
      try {
          // Find critical issue
          const criticalIssue = analysis.issues.find(i => i.severity === 'critical') || analysis.issues[0];
          const draft = await generateComplaintDraft(tender.description, criticalIssue.description);
          setComplaintDraft(draft);
      } catch (e) { console.error(e); }
      finally { setIsGeneratingComplaint(false); }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] animate-fade-in relative">
      {/* Header */}
      <div className="mb-4 flex-none">
        <button onClick={onBack} className="text-slate-500 hover:text-blue-600 text-sm flex items-center mb-2 transition-colors">
          <ChevronRight className="rotate-180 mr-1" size={16} /> К списку заявок
        </button>
        <div className="flex justify-between items-start">
            <div>
                <div className="flex items-center gap-2 mb-1">
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">{tender.fz}</span>
                    <span className="text-slate-400 text-sm">#{tender.id}</span>
                </div>
                <h2 className="text-xl font-bold text-slate-900 leading-tight max-w-4xl">{tender.title}</h2>
            </div>
            <div className="flex gap-2">
                <button className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-50 flex items-center shadow-sm">
                    <Download size={16} className="mr-2" /> Скачать все
                </button>
                <button className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all hover:-translate-y-0.5">
                    Подать заявку
                </button>
            </div>
        </div>
      </div>

      <div className="flex flex-1 gap-6 overflow-hidden">
        {/* Left Column: Analysis & Docs */}
        <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-1">
            
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="col-span-1 bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center relative overflow-hidden">
                    <GaugeChart value={analysis ? (100 - analysis.score) : tender.winRate} label="Win Rate" colorClass="border-blue-600" />
                    <p className="text-sm text-slate-500 mt-[-10px] text-center">Шанс допуска</p>
                </div>

                <div className="col-span-1 bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col items-center justify-center">
                    <GaugeChart value={analysis ? analysis.score : 0} label="Риск отклонения" colorClass={(analysis?.score || 0) > 50 ? "border-red-500" : "border-green-500"} />
                    <p className="text-sm text-slate-500 mt-[-10px] text-center">Вероятность жалобы</p>
                </div>

                <div className="col-span-1 bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <div className="text-sm text-slate-500 font-medium">Обеспечение заявки</div>
                        <div className="text-2xl font-bold text-slate-900 mt-1">{(tender.price * 0.05 / 1000).toFixed(0)} тыс. ₽</div>
                    </div>
                    <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
                        <AlertTriangle size={14} className="text-amber-500" />
                        <span>Требуется спецсчет</span>
                    </div>
                </div>
            </div>

            {/* Main Tabs */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm flex-1 flex flex-col min-h-[500px]">
                <div className="border-b border-slate-100 flex px-2">
                     <button 
                        onClick={() => setActiveTab('documents')}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'documents' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                    >
                        <FileText size={16} />
                        Документация
                        {documents.length > 0 && <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-xs">{documents.length}</span>}
                    </button>
                    <button 
                        onClick={() => setActiveTab('analysis')}
                        className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${activeTab === 'analysis' ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700'}`}
                    >
                        <Shield size={16} />
                        AI Аудит (44-ФЗ)
                    </button>
                </div>

                <div className="p-6 flex-1 overflow-y-auto">
                    {activeTab === 'documents' && (
                        <DocumentsSection 
                            files={documents} 
                            onUpload={handleFileUpload} 
                            onDelete={deleteDocument} 
                        />
                    )}

                    {activeTab === 'analysis' && (
                        <>
                            {isAnalyzing ? (
                                <div className="flex flex-col items-center justify-center h-full space-y-6">
                                    <div className="relative">
                                        <div className="w-24 h-24 border-4 border-slate-100 border-t-blue-600 rounded-full animate-spin"></div>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <Shield size={32} className="text-blue-600 animate-pulse" />
                                        </div>
                                    </div>
                                    <div className="text-center space-y-2">
                                        <h3 className="text-lg font-bold text-slate-800">Идет глубокий анализ документов</h3>
                                        <p className="text-slate-500 text-sm font-mono">{scanStep}</p>
                                    </div>
                                </div>
                            ) : analysis ? (
                                <div className="space-y-6 animate-fade-in">
                                    {/* AI Verdict */}
                                    <div className={`p-5 rounded-xl border flex gap-4 ${analysis.score > 50 ? 'bg-red-50 border-red-100' : 'bg-green-50 border-green-100'}`}>
                                        <div className={`p-2 h-fit rounded-lg ${analysis.score > 50 ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}>
                                            <Bot size={24} />
                                        </div>
                                        <div>
                                            <h4 className={`font-bold mb-1 ${analysis.score > 50 ? 'text-red-900' : 'text-green-900'}`}>
                                                {analysis.score > 50 ? 'Высокий риск участия' : 'Рекомендуется к участию'}
                                            </h4>
                                            <p className={`text-sm leading-relaxed ${analysis.score > 50 ? 'text-red-800' : 'text-green-800'}`}>
                                                {analysis.summary}
                                            </p>
                                        </div>
                                    </div>

                                    <div>
                                        <div className="flex justify-between items-center mb-4">
                                            <h4 className="font-bold text-slate-900">Протокол проверки ({analysis.issues.length})</h4>
                                        </div>
                                        
                                        <div className="space-y-3">
                                            {analysis.issues.map((issue, idx) => (
                                                <div key={idx} className="group flex gap-4 p-4 border border-slate-100 rounded-xl hover:border-blue-200 hover:shadow-md transition-all bg-white">
                                                    <div className="mt-1">
                                                        {issue.severity === 'critical' ? (
                                                            <div className="bg-red-100 p-2 rounded-full text-red-600"><AlertOctagon size={20} /></div>
                                                        ) : issue.severity === 'warning' ? (
                                                            <div className="bg-amber-100 p-2 rounded-full text-amber-600"><AlertTriangle size={20} /></div>
                                                        ) : (
                                                            <div className="bg-blue-100 p-2 rounded-full text-blue-600"><CheckCircle size={20} /></div>
                                                        )}
                                                    </div>
                                                    <div className="flex-1">
                                                        <div className="flex justify-between items-start">
                                                            <h5 className="font-bold text-slate-800 text-sm">{issue.title}</h5>
                                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                                                                issue.severity === 'critical' ? 'bg-red-50 text-red-600' : 'bg-amber-50 text-amber-600'
                                                            }`}>{issue.severity}</span>
                                                        </div>
                                                        <p className="text-sm text-slate-600 mt-1 mb-2">{issue.description}</p>
                                                        
                                                        {issue.lawReference && (
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <Gavel size={12} className="text-slate-400" />
                                                                <span className="text-xs font-mono text-slate-500 bg-slate-100 px-1 rounded">
                                                                    Нарушение: {issue.lawReference}
                                                                </span>
                                                            </div>
                                                        )}

                                                        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 p-2 rounded border border-slate-100">
                                                            <Scale size={12} className="text-blue-500"/>
                                                            <strong>Рекомендация:</strong> {issue.recommendation}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                    
                                    <div className="pt-4 border-t border-slate-100 flex gap-4">
                                        <button 
                                            onClick={handleGenerateProtocol}
                                            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border-2 border-slate-200 rounded-xl text-sm font-bold text-slate-700 hover:border-blue-500 hover:text-blue-600 transition-all"
                                        >
                                            <FileText size={18} />
                                            Протокол разногласий
                                        </button>
                                        <button 
                                            onClick={handleGenerateComplaint}
                                            className="flex-1 flex items-center justify-center gap-2 py-3 bg-white border-2 border-red-100 rounded-xl text-sm font-bold text-red-600 hover:bg-red-50 hover:border-red-200 transition-all"
                                        >
                                            <Gavel size={18} />
                                            Сформировать Жалобу в ФАС
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                                    <div className="bg-slate-100 p-4 rounded-full">
                                        <FileText size={48} className="text-slate-300" />
                                    </div>
                                    <div>
                                        <p className="font-bold text-slate-700">Ожидание документации</p>
                                        <p className="text-sm text-slate-500">Загрузите файлы во вкладке "Документация" для начала анализа.</p>
                                    </div>
                                    <button onClick={() => setActiveTab('documents')} className="text-blue-600 font-medium text-sm hover:underline">
                                        Перейти к загрузке
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>

        {/* Right Column: Chat */}
        <div className="w-[380px] bg-white border border-slate-200 flex flex-col shadow-xl rounded-xl overflow-hidden mr-1">
            <div className="p-4 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-200">
                        <Bot size={20} className="text-white" />
                    </div>
                    <div>
                        <h3 className="font-bold text-slate-900 text-sm">Тендер.AI</h3>
                        <p className="text-xs text-green-600 font-medium">Контекст: {documents.length} файлов</p>
                    </div>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
                {messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm leading-relaxed ${
                            msg.role === 'user' 
                                ? 'bg-blue-600 text-white rounded-br-none' 
                                : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                        }`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                {isChatLoading && (
                     <div className="flex justify-start animate-pulse">
                        <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-none border border-slate-200 text-slate-400 text-sm">
                            <span className="flex gap-1">
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-100"></span>
                                <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce delay-200"></span>
                            </span>
                        </div>
                     </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 bg-white border-t border-slate-200">
                <div className="relative">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                        placeholder="Спросите про штрафы, НДС..."
                        className="w-full pl-4 pr-12 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    />
                    <button 
                        onClick={handleSendMessage}
                        disabled={!inputMessage.trim() || isChatLoading}
                        className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    >
                        <Send size={16} />
                    </button>
                </div>
            </div>
        </div>
      </div>

      {/* MODAL: Protocol of Disagreements */}
      {showProtocolModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col">
                <div className="flex justify-between items-center p-6 border-b border-slate-100">
                    <h3 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                        <FileText className="text-blue-600" />
                        Протокол разногласий (Черновик)
                    </h3>
                    <button onClick={() => setShowProtocolModal(false)} className="text-slate-400 hover:text-slate-600">
                        <X size={24} />
                    </button>
                </div>
                
                <div className="p-6 flex-1 overflow-y-auto bg-slate-50">
                    {isGeneratingProtocol ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                            <Loader2 size={48} className="animate-spin text-blue-600 mb-4" />
                            <p className="font-medium">ИИ формирует юридические формулировки...</p>
                        </div>
                    ) : (
                        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                                    <tr>
                                        <th className="p-4 w-1/6">Пункт договора</th>
                                        <th className="p-4 w-1/4">Редакция Заказчика</th>
                                        <th className="p-4 w-1/4">Редакция Поставщика</th>
                                        <th className="p-4 w-1/3">Обоснование</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                    {protocolRows.map((row, idx) => (
                                        <tr key={idx} className="hover:bg-blue-50/30 transition-colors">
                                            <td className="p-4 font-medium text-slate-900 align-top">{row.clause}</td>
                                            <td className="p-4 text-slate-600 align-top bg-red-50/20 rounded m-2">{row.customerVersion}</td>
                                            <td className="p-4 text-green-700 font-medium align-top bg-green-50/30">{row.supplierVersion}</td>
                                            <td className="p-4 text-slate-500 align-top italic">{row.justification}</td>
                                        </tr>
                                    ))}
                                    {protocolRows.length === 0 && (
                                        <tr>
                                            <td colSpan={4} className="p-8 text-center text-slate-500">
                                                Не удалось сгенерировать протокол. Попробуйте еще раз.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div className="p-6 border-t border-slate-100 bg-white rounded-b-xl flex justify-end gap-3">
                    <button onClick={() => setShowProtocolModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium">
                        Отмена
                    </button>
                    <button className="px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 rounded-lg text-sm font-medium flex items-center gap-2 shadow-lg shadow-blue-200">
                        <Download size={16} />
                        Скачать в DOCX
                    </button>
                </div>
            </div>
        </div>
      )}

      {/* MODAL: FAS Complaint */}
      {showComplaintModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col">
                <div className="flex justify-between items-center p-6 border-b border-slate-100 bg-red-50 rounded-t-xl">
                    <h3 className="text-xl font-bold text-red-900 flex items-center gap-2">
                        <Gavel className="text-red-600" />
                        Жалоба в ФАС (Предварительный просмотр)
                    </h3>
                    <button onClick={() => setShowComplaintModal(false)} className="text-red-400 hover:text-red-600">
                        <X size={24} />
                    </button>
                </div>
                
                <div className="p-8 flex-1 overflow-y-auto bg-white">
                    {isGeneratingComplaint ? (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                            <Loader2 size={48} className="animate-spin text-red-600 mb-4" />
                            <p className="font-medium">ИИ анализирует судебную практику и составляет текст...</p>
                        </div>
                    ) : complaintDraft ? (
                        <div className="prose prose-sm max-w-none font-serif leading-relaxed text-slate-800">
                            <div className="text-right mb-8">
                                <p><strong>Куда:</strong> {complaintDraft.to}</p>
                                <p><strong>От кого:</strong> {complaintDraft.from}</p>
                            </div>
                            
                            <h2 className="text-center font-bold text-lg mb-6 uppercase">{complaintDraft.topic}</h2>
                            
                            {complaintDraft.violations.map((v, i) => (
                                <div key={i} className="mb-6">
                                    <h4 className="font-bold underline mb-2">Нарушение №{i+1}: {v.point}</h4>
                                    <p className="mb-2">{v.argument}</p>
                                    <p className="italic bg-slate-50 p-2 border-l-4 border-slate-300">Основание: {v.law}</p>
                                </div>
                            ))}

                            <div className="mt-8 pt-4 border-t border-slate-200">
                                <h4 className="font-bold mb-2">ПРОШУ:</h4>
                                <div className="whitespace-pre-line">{complaintDraft.demand}</div>
                            </div>
                        </div>
                    ) : (
                         <p className="text-center text-slate-500">Ошибка генерации.</p>
                    )}
                </div>

                <div className="p-6 border-t border-slate-100 bg-white rounded-b-xl flex justify-between items-center">
                    <span className="text-xs text-slate-400">Сгенерировано AI v14.0. Требует проверки юристом.</span>
                    <div className="flex gap-3">
                        <button onClick={() => setShowComplaintModal(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium">
                            Закрыть
                        </button>
                        <button className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg text-sm font-medium flex items-center gap-2 shadow-lg shadow-red-200">
                            <Printer size={16} />
                            Печать / PDF
                        </button>
                    </div>
                </div>
            </div>
        </div>
      )}

    </div>
  );
};

export default TenderDetail;