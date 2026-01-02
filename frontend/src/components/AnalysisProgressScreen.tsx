import React, { useState, useEffect, useRef } from 'react';
import { Check, Loader2, Shield, AlertCircle, RefreshCw, MessageSquare, Send } from 'lucide-react';
import { logEvent } from '../utils/logger';
import { startAnalysis, getAnalysisStatus } from '../services/geminiService';
import { getCurrentDemoSession } from '../utils/demoBootstrap';

interface AnalysisProgressScreenProps {
  /** Файлы, которые анализируются */
  files: File[];
  /** Режим анализа */
  mode: 'single' | 'package';
  /** Название тендера/пакета (опционально) */
  tenderName?: string;
  /** Вызывается когда анализ завершён с результатом */
  onAnalysisComplete: (result: any) => void;
  /** Вызывается при ошибке */
  onError?: (error: Error) => void;
  /** Analysis ID для восстановления после перезагрузки */
  analysisId?: string | null;
}

/**
 * Экран анализа / ожидания результата
 * 
 * Цель:
 * - снимает тревогу директора
 * - показывает, что система работает
 * - готовит к принятию решения
 * 
 * Это экран доверия, а не загрузки.
 */
const AnalysisProgressScreen: React.FC<AnalysisProgressScreenProps> = ({
  files,
  mode,
  tenderName,
  onAnalysisComplete,
  onError,
  analysisId: initialAnalysisId,
}) => {
  // Состояние анализа
  const [analysisId, setAnalysisId] = useState<string | null>(initialAnalysisId || null);
  const [status, setStatus] = useState<'queued' | 'processing' | 'delayed' | 'done' | 'error'>('queued');
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  
  // Состояние UI
  const [showLongAnalysisWarning, setShowLongAnalysisWarning] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [chatMessage, setChatMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'system'; text: string }>>([
    {
      role: 'system',
      text: 'Анализ выполняется. Вы можете задать общий вопрос, но выводы будут доступны после завершения.',
    },
  ]);
  
  // Таймеры и refs
  const startTimeRef = useRef<number>(Date.now());
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const longAnalysisTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const completionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Фиксированные этапы анализа (не меняются)
  const stages = [
    { id: 'preparation', name: 'Подготовка документов', description: 'Проверяем структуру и читаем файлы' },
    { id: 'legal', name: 'Анализ правового режима', description: 'Проверяем 44-ФЗ / 223-ФЗ и соответствие условий' },
    { id: 'risks', name: 'Поиск критических рисков', description: 'Ищем стоп-факторы и противоречия' },
    { id: 'financial', name: 'Финансовая оценка', description: 'Анализ НМЦК, аванса, обеспечения, штрафов' },
    { id: 'verdict', name: 'Формирование управленческого вывода', description: 'Готовим вывод для директора' },
  ];

  // Маппинг backend stage на этапы UI
  const getStageIndex = (backendStage: string): number => {
    const stageMap: Record<string, number> = {
      'queued': 0,
      'parsing_documents': 0,
      'preparation': 0,
      'legal_checks': 1,
      'legal': 1,
      'risks': 2,
      'critical_flags': 2,
      'financial_risks': 3,
      'financial': 3,
      'verdict_building': 4,
      'verdict': 4,
      'done': 4,
    };
    return stageMap[backendStage] ?? 0;
  };

  // Получение текста для текущего этапа
  const getStageText = (backendStage: string): string => {
    const stageTexts: Record<string, string> = {
      'queued': 'Ожидание начала анализа...',
      'parsing_documents': 'Система анализирует документы и сопоставляет условия',
      'preparation': 'Система анализирует документы и сопоставляет условия',
      'legal_checks': 'Мы ищем риски, которые не всегда видны при ручной проверке',
      'legal': 'Мы ищем риски, которые не всегда видны при ручной проверке',
      'risks': 'Мы ищем риски, которые не всегда видны при ручной проверке',
      'critical_flags': 'Мы ищем риски, которые не всегда видны при ручной проверке',
      'financial_risks': 'Формируется управленческий вывод',
      'financial': 'Формируется управленческий вывод',
      'verdict_building': 'Формируется управленческий вывод',
      'verdict': 'Формируется управленческий вывод',
      'done': 'Анализ завершён. Формируем первый вывод…',
    };
    return stageTexts[backendStage] || 'Анализ выполняется...';
  };

  // Запуск анализа
  useEffect(() => {
    if (analysisId) {
      // Анализ уже запущен, начинаем polling
      startPolling(analysisId);
      return;
    }

    // Запускаем новый анализ
    const demoSession = getCurrentDemoSession();
    const demoSessionId = demoSession?.id || null;
    
    const file = mode === 'single' ? files[0] : null;
    const fileList = mode === 'package' ? files : null;
    
    startAnalysis(file, fileList, 'UNIVERSAL', demoSessionId)
      .then((response) => {
        setAnalysisId(response.analysis_id);
        setStatus('queued');
        logEvent('AnalysisProgressScreen', 'analysis_job_created', 'info', {
          analysisId: response.analysis_id,
        });
        
        // Сохраняем analysis_id в localStorage для восстановления после перезагрузки
        localStorage.setItem('current_analysis_id', response.analysis_id);
        
        // Начинаем polling
        startPolling(response.analysis_id, demoSessionId);
      })
      .catch((error) => {
        console.error('[AnalysisProgressScreen] Failed to start analysis:', error);
        logEvent('AnalysisProgressScreen', 'analysis_start_error', 'error', {
          error: error.message || String(error),
        });
        setStatus('error');
        setErrorMessage('Не удалось запустить анализ. Попробуйте снова.');
        if (onError) {
          onError(error);
        }
      });
  }, []); // Только при монтировании

  // Polling статуса анализа
  const startPolling = (jobId: string, demoSessionId: string | null = null) => {
    // Очищаем предыдущий интервал
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    const poll = async () => {
      try {
        const statusData = await getAnalysisStatus(jobId, demoSessionId);
        
        // Обновляем состояние
        setStatus(statusData.status);
        setProgress(statusData.progress || 0);
        if (statusData.stage) {
          setStage(statusData.stage);
        }
        
        // Проверка на долгий анализ (> 60 секунд)
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed > 60000 && !showLongAnalysisWarning) {
          setShowLongAnalysisWarning(true);
        }
        
        if (statusData.status === 'done' && statusData.result) {
          // Анализ завершён
          setAnalysisResult(statusData.result);
          setProgress(100);
          setStage('done');
          
          // Останавливаем polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          
          // Очищаем analysis_id из localStorage
          localStorage.removeItem('current_analysis_id');
          
          logEvent('AnalysisProgressScreen', 'analysis_completed', 'info', {
            elapsedMs: Date.now() - startTimeRef.current,
            analysisId: jobId,
          });
          
          // Показываем сообщение о завершении и переходим через 500-800 мс
          completionTimeoutRef.current = setTimeout(() => {
            onAnalysisComplete(statusData.result);
          }, 500 + Math.random() * 300); // 500-800 мс
          
        } else if (statusData.status === 'error') {
          // Ошибка анализа
          setErrorMessage(statusData.error_message || 'Произошла ошибка при анализе');
          
          // Останавливаем polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          
          logEvent('AnalysisProgressScreen', 'analysis_error', 'error', {
            error: statusData.error_message || 'Unknown error',
            analysisId: jobId,
          });
        }
      } catch (error) {
        console.error('[AnalysisProgressScreen] Polling error:', error);
        // Продолжаем polling даже при ошибке (может быть временная проблема сети)
      }
    };
    
    // Первый запрос сразу
    poll();
    
    // Polling каждые 1-2 секунды
    pollingIntervalRef.current = setInterval(poll, 1500);
  };

  // Обработка долгого анализа
  useEffect(() => {
    if (status === 'processing') {
      longAnalysisTimeoutRef.current = setTimeout(() => {
        setShowLongAnalysisWarning(true);
      }, 60000); // 60 секунд
    }
    
    return () => {
      if (longAnalysisTimeoutRef.current) {
        clearTimeout(longAnalysisTimeoutRef.current);
      }
    };
  }, [status]);

  // Очистка при размонтировании
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      if (longAnalysisTimeoutRef.current) {
        clearTimeout(longAnalysisTimeoutRef.current);
      }
      if (completionTimeoutRef.current) {
        clearTimeout(completionTimeoutRef.current);
      }
    };
  }, []);

  // Обработка отправки сообщения в чат (ограниченный режим)
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatMessage.trim()) return;
    
    // Добавляем сообщение пользователя
    setChatMessages(prev => [...prev, { role: 'user', text: chatMessage }]);
    
    // Ответ системы (ограниченный режим)
    setChatMessages(prev => [...prev, {
      role: 'system',
      text: 'Анализ ещё выполняется. Дождитесь завершения для получения полных выводов.',
    }]);
    
    setChatMessage('');
  };

  // Повторный запуск анализа при ошибке
  const handleRetry = () => {
    setStatus('queued');
    setErrorMessage(null);
    setProgress(0);
    setStage('');
    setAnalysisResult(null);
    startTimeRef.current = Date.now();
    
    // Перезапускаем анализ
    const demoSession = getCurrentDemoSession();
    const demoSessionId = demoSession?.id || null;
    
    const file = mode === 'single' ? files[0] : null;
    const fileList = mode === 'package' ? files : null;
    
    startAnalysis(file, fileList, 'UNIVERSAL', demoSessionId)
      .then((response) => {
        setAnalysisId(response.analysis_id);
        localStorage.setItem('current_analysis_id', response.analysis_id);
        startPolling(response.analysis_id, demoSessionId);
      })
      .catch((error) => {
        setStatus('error');
        setErrorMessage('Не удалось запустить анализ. Попробуйте снова.');
        if (onError) {
          onError(error);
        }
      });
  };

  // Определяем текущий этап для отображения
  const currentStageIndex = stage ? getStageIndex(stage) : 0;
  const currentStageText = stage ? getStageText(stage) : 'Идёт аналитическая проверка тендера';

  // Если ошибка - показываем экран ошибки
  if (status === 'error') {
    return (
      <div className="min-h-screen bg-[#0f1419] flex items-center justify-center p-8">
        <div className="max-w-2xl w-full space-y-6">
          <div className="bg-[#1a1f2e] border border-red-500/30 rounded-2xl p-8 text-center">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-4">Ошибка анализа</h2>
            <p className="text-slate-300 mb-6">
              {errorMessage || 'Мы столкнулись с технической ошибкой при анализе. Документы не были изменены.'}
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleRetry}
                className="bg-[#00d4ff] text-[#0f1419] font-bold px-6 py-3 rounded-xl hover:bg-[#00b8e6] transition-all flex items-center gap-2"
              >
                <RefreshCw size={20} />
                Повторить анализ
              </button>
              <a
                href="mailto:support@tendershield.pro"
                className="bg-[#1a1f2e] border border-[#2a3441] text-white font-medium px-6 py-3 rounded-xl hover:bg-[#2a3441] transition-all flex items-center gap-2"
              >
                Связаться с поддержкой
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f1419] p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl md:text-4xl font-bold text-white">
            {tenderName || 'Управленческое решение по тендеру'}
          </h1>
          <p className="text-sm text-slate-400">
            Анализ пакета документов для принятия решения директором
          </p>
        </div>

        {/* Stepper */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[#00e648] text-[#0f1419] flex items-center justify-center font-bold">
                <Check size={16} />
              </div>
              <span className="text-slate-300">Загрузка</span>
            </div>
            <div className="w-12 h-0.5 bg-[#00d4ff]"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[#00d4ff] text-[#0f1419] flex items-center justify-center font-bold">
                <Loader2 size={16} className="animate-spin" />
              </div>
              <span className="text-white font-medium">Анализ</span>
            </div>
            <div className="w-12 h-0.5 bg-[#2a3441]"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[#2a3441] text-slate-400 flex items-center justify-center font-bold">
                3
              </div>
              <span className="text-slate-400">Решение</span>
            </div>
            <div className="w-12 h-0.5 bg-[#2a3441]"></div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[#2a3441] text-slate-400 flex items-center justify-center font-bold">
                4
              </div>
              <span className="text-slate-400">Действия</span>
            </div>
          </div>
        </div>

        {/* Основной блок анализа */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6 space-y-6">
          {/* Прогресс-бар */}
          <div>
            <div className="flex justify-between text-sm text-slate-400 mb-2">
              <span>Прогресс анализа</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-[#2a3441] rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-[#00d4ff] to-[#0099cc] h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.max(progress, 5)}%` }}
              ></div>
            </div>
          </div>

          {/* Текущий этап */}
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-white">
              {stages[currentStageIndex]?.name || 'Анализ выполняется...'}
            </h3>
            <p className="text-slate-300 text-sm">
              {currentStageText}
            </p>
            {stages[currentStageIndex]?.description && (
              <p className="text-slate-400 text-xs">
                {stages[currentStageIndex].description}
              </p>
            )}
          </div>

          {/* Тайминг */}
          {status !== 'delayed' && (
            <div className="text-xs text-slate-500">
              Анализ занимает до 30 секунд. В сложных случаях — до 1–2 минут.
            </div>
          )}

          {/* Состояние delayed (>30 секунд) */}
          {status === 'delayed' && (
            <div className="bg-[#1a1f2e] border border-[#f59e0b]/30 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-[#f59e0b] flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-white font-medium mb-1">
                    Анализ занимает больше времени, чем обычно
                  </p>
                  <p className="text-xs text-slate-400 mb-2">
                    Это нормально для сложных пакетов документов. Система продолжает работу.
                  </p>
                  <p className="text-xs text-slate-500 italic">
                    Вы можете свернуть страницу — анализ продолжится в фоне.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Предупреждение о долгом анализе (>60 секунд) */}
          {showLongAnalysisWarning && status === 'delayed' && (
            <div className="bg-[#0a0e13] border border-yellow-500/30 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm text-yellow-200 font-medium mb-1">
                    Анализ выполняется дольше обычного
                  </p>
                  <p className="text-xs text-slate-400">
                    Это может быть связано со сложной структурой документов или большой нагрузкой на систему. 
                    Продолжаем анализ...
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Список этапов */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Этапы анализа</h3>
          <div className="space-y-3">
            {stages.map((stageItem, index) => {
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;
              
              return (
                <div
                  key={stageItem.id}
                  className={`flex items-start gap-4 p-3 rounded-lg transition-all ${
                    isCurrent ? 'bg-[#0a0e13] border border-[#00d4ff]/30' : ''
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                      isCompleted
                        ? 'bg-[#00e648] text-[#0f1419]'
                        : isCurrent
                        ? 'bg-[#00d4ff] text-[#0f1419]'
                        : 'bg-[#2a3441] text-slate-500'
                    }`}
                  >
                    {isCompleted ? (
                      <Check size={16} />
                    ) : isCurrent ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <span className="text-xs font-bold">{index + 1}</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div
                      className={`text-sm font-medium transition-colors ${
                        isCompleted || isCurrent ? 'text-white' : 'text-slate-400'
                      }`}
                    >
                      {stageItem.name}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {stageItem.description}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Блок доверия */}
        <div className="bg-[#0a0e13] border border-[#1f2937] rounded-xl p-4">
          <div className="flex items-start gap-3">
            <Shield size={16} className="text-slate-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-slate-500 leading-relaxed">
              Система проводит аналитическую оценку. Управленческое решение принимает директор.
            </p>
          </div>
        </div>

        {/* Чат AI-консультанта (ограниченный режим) */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <MessageSquare size={20} className="text-[#00d4ff]" />
            <h3 className="text-lg font-semibold text-white">AI-консультант</h3>
          </div>
          
          <div className="space-y-3 mb-4 max-h-64 overflow-y-auto">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-[#00d4ff]/10 text-white ml-8'
                    : 'bg-[#0a0e13] text-slate-300'
                }`}
              >
                <p className="text-sm">{msg.text}</p>
              </div>
            ))}
          </div>
          
          <form onSubmit={handleChatSubmit} className="flex gap-2">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Задайте вопрос..."
              className="flex-1 bg-[#0a0e13] border border-[#2a3441] rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:border-[#00d4ff]"
              disabled={status === 'done'}
            />
            <button
              type="submit"
              disabled={!chatMessage.trim() || status === 'done'}
              className="bg-[#00d4ff] text-[#0f1419] px-4 py-2 rounded-lg hover:bg-[#00b8e6] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Send size={16} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AnalysisProgressScreen;
