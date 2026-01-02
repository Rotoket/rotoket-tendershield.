import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import TenderAnalysis from './components/TenderAnalysis';
import HistoryView from './components/HistoryView';
import KnowledgeView from './components/KnowledgeView';
import Auth from './components/Auth';
import ResetPassword from './components/ResetPassword';
import DocumentGenerator from './components/DocumentGenerator';
import Calculator from './components/Calculator';
import Profile from './components/Profile';
import Analytics from './components/Analytics';
import HelpGuide from './components/HelpGuide';
import LandingScreen from './components/LandingScreen';
import AnalysisTypeSelector from './components/AnalysisTypeSelector';
import DecisionPreviewScreen from './components/DecisionPreviewScreen';
import AnalysisProgressScreen from './components/AnalysisProgressScreen';
import PostDecisionLock from './components/PostDecisionLock';
import PaymentActivationScreen from './components/PaymentActivationScreen';
import { DemoModeBanner } from './components/DemoModeBanner';
import { NotificationsPanel } from './components/NotificationsPanel';
import KillSwitchBanner from './components/KillSwitchBanner';
import { DemoProvider } from './context/DemoContext';
import type { AnalysisResult, PackageAnalysis } from './types';
import { AppView, User, CalculatorPreset, UserDecision } from './types';
import { getCurrentUser, logout as authLogout, type AuthUser } from './services/authService';
import { getKillSwitchStatus, type KillSwitchStatus } from './services/killSwitchService';
import { logEvent } from './utils/logger';

const App: React.FC = () => {
  // Состояние для первого пользователя (неавторизованного)
  const [firstUserFlow, setFirstUserFlow] = useState<{
    step: 'landing' | 'type_select' | 'analysis' | 'analysis_progress' | 'decision_preview' | 'auth_for_decision' | 'post_decision' | 'payment';
    selectedMode?: 'single' | 'package';
    decision?: UserDecision;
    analysisResult?: any; // AnalysisResult или PackageAnalysis
    authReason?: 'fix_decision' | 'general';
  }>({ step: 'landing' });

  const [currentView, setCurrentView] = useState<AppView>(AppView.AUDIT);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Последний результат анализа для автоподстановки в калькулятор
  const [calcPreset, setCalcPreset] = useState<CalculatorPreset | null>(null);
  // Данные для генератора документов из анализа
  const [generatorData, setGeneratorData] = useState<{
    dealBreakers?: string[];
    smartQuestions?: string[];
    tenderNumber?: string;
    customer?: string;
  } | undefined>(undefined);
  // Решение пользователя для передачи в DocumentGenerator и Calculator
  // Единственный источник истины для userDecision
  const [currentDecision, setCurrentDecision] = useState<UserDecision | null>(null);
  // Запрос для Базы знаний из анализа
  const [knowledgeQuery, setKnowledgeQuery] = useState<string | undefined>(undefined);
  // Статус Kill Switch
  const [killSwitchStatus, setKillSwitchStatus] = useState<KillSwitchStatus | null>(null);

  // Обработчик изменения решения (канонический поток Decision)
  const handleDecisionChange = (decision: UserDecision) => {
    setCurrentDecision(decision);
    // Дублируем в localStorage как backup (не primary источник)
    try {
      localStorage.setItem('last_user_decision', JSON.stringify(decision));
    } catch (error) {
      logEvent('App', 'Failed to save decision to localStorage', 'error', error);
    }

    // Если пользователь не авторизован и решение зафиксировано, переходим к экрану Post-Decision Lock
    if (!user && decision.timestamp) {
      setFirstUserFlow(prev => ({
        ...prev,
        step: 'post_decision',
        decision,
      }));
    } else if (user && firstUserFlow.step === 'decision_preview') {
      // Если пользователь авторизован и находится на decision_preview, обновляем решение
      setFirstUserFlow(prev => ({
        ...prev,
        decision,
        step: 'post_decision',
      }));
    }
  };

  // Загрузка статуса Kill Switch
  useEffect(() => {
    const loadKillSwitchStatus = async () => {
      try {
        const status = await getKillSwitchStatus();
        setKillSwitchStatus(status);
      } catch (error) {
        console.error('[App] Error loading kill switch status:', error);
      }
    };

    loadKillSwitchStatus();
    // Обновляем статус каждые 30 секунд
    const interval = setInterval(loadKillSwitchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Проверка токена при загрузке приложения
  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log('[App] Checking auth...');
        const authUser = await getCurrentUser();
        console.log('[App] Auth check result:', authUser ? 'user found' : 'no user');
        if (authUser) {
          // Преобразуем AuthUser в User
          const tariffMap: ('Start' | 'Pro' | 'Enterprise')[] = ['Start', 'Pro', 'Enterprise'];
          const tariff: 'Start' | 'Pro' | 'Enterprise' = authUser.tariff_id && authUser.tariff_id >= 1 && authUser.tariff_id <= 3
            ? tariffMap[authUser.tariff_id - 1]
            : 'Start';

          // Безопасная обработка email (может быть undefined)
          const email = authUser.email || '';
          const emailName = email.split('@')[0] || 'Специалист';
          
          const mappedUser: User = {
            id: authUser.id ? authUser.id.toString() : '0',
            name: authUser.name || emailName,
            company: authUser.company || 'Организация',
            tariff,
            email: email,
          };
          console.log('[App] Setting user:', mappedUser);
          setUser(mappedUser);
          // Авторизованные пользователи идут сразу в основное приложение
          setFirstUserFlow({ step: 'landing' });
        } else {
          setUser(null);
        }
      } catch (error) {
        logEvent('App', 'Auth Check Error', 'error', error);
        setUser(null);
      } finally {
        logEvent('App', 'Auth check complete, setting isLoading to false', 'info');
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const openCalculator = () => {
    setCurrentView(AppView.CALCULATOR);
  };

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
    setCurrentView(AppView.AUDIT);
    
    // Если пришли с auth_for_decision, возвращаемся к decision_preview
    if (firstUserFlow.step === 'auth_for_decision' && firstUserFlow.analysisResult) {
      setFirstUserFlow(prev => ({
        ...prev,
        step: 'decision_preview',
        authReason: undefined,
      }));
    } else {
      // После обычного логина сбрасываем first user flow
      setFirstUserFlow({ step: 'landing' });
    }
  };

  const handleLogout = () => {
    authLogout();
    setUser(null);
    setCurrentView(AppView.AUDIT);
    setFirstUserFlow({ step: 'landing' });
  };

  // Защита от бесконечной загрузки - через 3 секунды показываем контент
  useEffect(() => {
    if (isLoading) {
      const timeout = setTimeout(() => {
        logEvent('App', 'Loading timeout, forcing isLoading to false', 'warn');
        setIsLoading(false);
      }, 3000);
      return () => clearTimeout(timeout);
    }
  }, [isLoading]);

  // Обработка ошибок рендеринга
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      logEvent('App', 'Global error', 'error', event.error);
    };
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      logEvent('App', 'Unhandled promise rejection', 'error', event.reason);
    };
    window.addEventListener('error', handleError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => {
      window.removeEventListener('error', handleError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  // Показываем загрузку при проверке авторизации
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f1419] flex items-center justify-center">
        <div className="text-white text-xl">Загрузка...</div>
      </div>
    );
  }

  // Проверяем наличие токена сброса пароля в URL
  // Проверяем токен восстановления пароля из URL
  const urlParams = new URLSearchParams(window.location.search);
  const resetToken = urlParams.get('token');

  if (resetToken && !user) {
    return (
      <DemoProvider>
        <DemoModeBanner />
        <ResetPassword
          token={resetToken}
          onSuccess={() => {
            // Очищаем токен из URL и переходим на экран входа
            window.history.replaceState({}, '', '/auth');
            setUser(null);
            // Переключаемся на экран авторизации
            setCurrentView(AppView.LOGIN);
          }}
        />
      </DemoProvider>
    );
  }

  // ===== FLOW ДЛЯ НЕАВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ =====
  if (!user) {
    // Landing Screen
    if (firstUserFlow.step === 'landing') {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <KillSwitchBanner status={killSwitchStatus} className="mb-6" />
          <LandingScreen
            onStartAnalysis={() => {
              logEvent('App', 'LandingScreen onStartAnalysis called, transitioning to type_select', 'info');
              setFirstUserFlow({ step: 'type_select' });
            }}
            onShowAuth={() => {
              logEvent('App', 'LandingScreen onShowAuth called, transitioning to auth', 'info');
              // Показываем форму входа/регистрации
              setFirstUserFlow({ step: 'auth_for_decision', authReason: 'general' });
            }}
            onShowHistory={() => {
              logEvent('App', 'LandingScreen onShowHistory called, transitioning to history', 'info');
              setCurrentView(AppView.HISTORY);
            }}
          />
        </DemoProvider>
      );
    }

    // Если пользователь хочет залогиниться напрямую (через кнопку "Войти")
    if (currentView === AppView.LOGIN || firstUserFlow.step === 'auth_for_decision') {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <Auth 
            onLogin={handleLogin}
            reason={firstUserFlow.authReason || 'general'}
          />
        </DemoProvider>
      );
    }

    // Выбор типа анализа
    if (firstUserFlow.step === 'type_select') {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <AnalysisTypeSelector
            defaultMode="package"
            onSelect={(mode) => {
              setFirstUserFlow({ step: 'analysis', selectedMode: mode });
            }}
          />
        </DemoProvider>
      );
    }

    // Экран анализа (без сайдбара)
    if (firstUserFlow.step === 'analysis') {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <div className="min-h-screen bg-[#0f1419]">
            <TenderAnalysis
              mode={firstUserFlow.selectedMode || 'package'}
              onAnalysisComplete={setCalcPreset}
              onAnalysisResultReady={(result, files) => {
                // Переходим к экрану прогресса анализа
                setFirstUserFlow(prev => ({
                  ...prev,
                  step: 'analysis_progress',
                  analysisResult: result,
                  analysisFiles: files || [],
                }));
              }}
              onOpenCalculator={() => {
                // Калькулятор заблокирован до оплаты для неавторизованных
                setFirstUserFlow(prev => ({ ...prev, step: 'post_decision' }));
              }}
              onOpenGenerator={() => {
                // Генератор заблокирован до оплаты для неавторизованных
                setFirstUserFlow(prev => ({ ...prev, step: 'post_decision' }));
              }}
              onSelectForCalculator={setCalcPreset}
              onViewKnowledge={(query) => {
                setKnowledgeQuery(query);
              }}
              onDecisionChange={handleDecisionChange}
            />
          </div>
        </DemoProvider>
      );
    }

    // Экран прогресса анализа (канонический)
    if (firstUserFlow.step === 'analysis_progress' && firstUserFlow.analysisFiles) {
      // Восстанавливаем analysis_id из localStorage при перезагрузке
      const savedAnalysisId = localStorage.getItem('current_analysis_id');
      
      return (
        <DemoProvider>
          <DemoModeBanner />
          <AnalysisProgressScreen
            files={firstUserFlow.analysisFiles}
            mode={firstUserFlow.selectedMode || 'package'}
            tenderName={firstUserFlow.tenderName}
            analysisId={savedAnalysisId}
            onAnalysisComplete={(result) => {
              // Сохраняем результат и переходим к decision_preview
              setFirstUserFlow(prev => ({
                ...prev,
                step: 'decision_preview',
                analysisResult: result,
              }));
            }}
            onError={(error) => {
              logEvent('App', 'Analysis error', 'error', error);
              // При ошибке возвращаемся к загрузке
              setFirstUserFlow(prev => ({
                ...prev,
                step: 'analysis',
              }));
            }}
          />
        </DemoProvider>
      );
    }

    // Экран первого вердикта (decision_preview) — ориентация директора
    if (firstUserFlow.step === 'decision_preview' && firstUserFlow.analysisResult) {
      const result = firstUserFlow.analysisResult as AnalysisResult | PackageAnalysis;
      // Преобразуем PackageAnalysis в формат, похожий на AnalysisResult для DecisionPreviewScreen
      const previewResult: AnalysisResult = 'passport' in result
        ? result
        : {
            verdict: result.verdict,
            score: Math.round(result.summaryScore),
            executive_summary: result.hub?.recommendation?.summaryShort || `Анализ пакета из ${result.documents.length} документов завершен.`,
            deal_breakers: result.globalIssues
              .filter(gi => gi.severity.toLowerCase() === 'critical' || gi.severity.toLowerCase() === 'high')
              .map(gi => ({ title: gi.title })),
          } as AnalysisResult;

      return (
        <DemoProvider>
          <DemoModeBanner />
          <div className="min-h-screen bg-[#0f1419] p-8">
            <DecisionPreviewScreen
              result={previewResult}
              isAuthenticated={!!user}
              onRequestFixDecision={() => {
                // Переходим к авторизации для фиксации решения
                setFirstUserFlow(prev => ({
                  ...prev,
                  step: 'auth_for_decision',
                  authReason: 'fix_decision',
                }));
              }}
              onDecisionChange={handleDecisionChange}
              fixedDecision={firstUserFlow.decision}
            />
          </div>
        </DemoProvider>
      );
    }

    // Экран после фиксации решения
    if (firstUserFlow.step === 'post_decision' && firstUserFlow.decision) {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <PostDecisionLock
            decision={firstUserFlow.decision}
            onActivateAccess={() => {
              setFirstUserFlow(prev => ({ ...prev, step: 'payment' }));
            }}
            onBack={() => {
              setFirstUserFlow(prev => ({ ...prev, step: 'analysis' }));
            }}
          />
        </DemoProvider>
      );
    }

    // Экран оплаты/активации
    if (firstUserFlow.step === 'payment') {
      return (
        <DemoProvider>
          <DemoModeBanner />
          <PaymentActivationScreen
            onActivate={() => {
              // После оплаты показываем форму регистрации
              setCurrentView(AppView.LOGIN);
            }}
            onBack={() => {
              setFirstUserFlow(prev => ({ ...prev, step: 'post_decision' }));
            }}
          />
        </DemoProvider>
      );
    }

    // Fallback: показываем Auth (для случаев, когда пользователь хочет залогиниться напрямую)
    return (
      <DemoProvider>
        <DemoModeBanner />
        <Auth onLogin={handleLogin} />
      </DemoProvider>
    );
  }

  // ===== FLOW ДЛЯ АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ =====
  const renderContent = () => {
    switch (currentView) {
      case AppView.ANALYZER:
      case AppView.AUDIT:
        return (
          <TenderAnalysis
            mode={currentView === AppView.ANALYZER ? 'single' : 'package'}
            onAnalysisComplete={setCalcPreset}
            onOpenCalculator={openCalculator}
            onOpenGenerator={(dealBreakers, smartQuestions) => {
              setGeneratorData({ dealBreakers, smartQuestions });
              setCurrentView(AppView.GENERATOR);
            }}
            onSelectForCalculator={setCalcPreset}
            onViewKnowledge={(query) => {
              setKnowledgeQuery(query);
              setCurrentView(AppView.KNOWLEDGE);
            }}
            onDecisionChange={handleDecisionChange}
          />
        );
      case AppView.GENERATOR:
        return <DocumentGenerator initialData={generatorData} decision={currentDecision} />;
      case AppView.CALCULATOR:
        return <Calculator preset={calcPreset} decision={currentDecision} />;
      case AppView.HISTORY:
        return <HistoryView />;
      case AppView.PROFILE:
        return <Profile user={user} />;
      case AppView.KNOWLEDGE:
        return <KnowledgeView initialQuery={knowledgeQuery} />;
      case AppView.ANALYTICS:
        return <Analytics />;
      case AppView.HELP:
        return <HelpGuide onBack={() => setCurrentView(AppView.AUDIT)} />;
      default:
        return (
          <TenderAnalysis
            mode="package"
            onSelectForCalculator={setCalcPreset}
            onOpenCalculator={openCalculator}
            onOpenGenerator={(dealBreakers, smartQuestions) => {
              setGeneratorData({ dealBreakers, smartQuestions });
              setCurrentView(AppView.GENERATOR);
            }}
            onViewKnowledge={(query) => {
              setKnowledgeQuery(query);
              setCurrentView(AppView.KNOWLEDGE);
            }}
            onDecisionChange={handleDecisionChange}
          />
        );
    }
  };

  return (
    <DemoProvider>
      <DemoModeBanner />
      <NotificationsPanel />
      <div className="flex min-h-screen bg-[#0f1419]">
        <Sidebar
          currentView={currentView}
          onChangeView={setCurrentView}
          user={user}
          onLogout={handleLogout}
          decisionFixed={!!currentDecision?.timestamp}
          currentDecision={currentDecision}
        />
        <main className="flex-1 ml-0 md:ml-[280px] p-8 h-screen overflow-hidden">
          <KillSwitchBanner status={killSwitchStatus} className="mb-6" />
          {renderContent()}
        </main>
      </div>
    </DemoProvider>
  );
};

export default App;
