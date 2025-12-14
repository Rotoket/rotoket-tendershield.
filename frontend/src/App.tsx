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
import { DemoModeBanner } from './components/DemoModeBanner';
import { NotificationsPanel } from './components/NotificationsPanel';
import { DemoProvider } from './context/DemoContext';
import { AppView, User, CalculatorPreset } from './types';
import { Clock } from 'lucide-react';
import { getCurrentUser, logout as authLogout, type AuthUser } from './services/authService';

const App: React.FC = () => {
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
  // Запрос для Базы знаний из анализа
  const [knowledgeQuery, setKnowledgeQuery] = useState<string | undefined>(undefined);

  // Проверка токена при загрузке приложения
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const authUser = await getCurrentUser();
        if (authUser) {
          // Преобразуем AuthUser в User
          const tariffMap: ('Start' | 'Pro' | 'Enterprise')[] = ['Start', 'Pro', 'Enterprise'];
          const tariff: 'Start' | 'Pro' | 'Enterprise' = authUser.tariff_id && authUser.tariff_id >= 1 && authUser.tariff_id <= 3
            ? tariffMap[authUser.tariff_id - 1]
            : 'Start';

          const mappedUser: User = {
            id: authUser.id.toString(),
            name: authUser.name || authUser.email.split('@')[0] || 'Специалист',
            company: authUser.company || 'Организация',
            tariff,
            email: authUser.email,
          };
          setUser(mappedUser);
        } else {
          // Токена нет или он невалиден — оставляем пользователя неавторизованным.
          // Это позволяет показать полноценное окно входа/регистрации.
          setUser(null);
        }
      } catch (error) {
        console.error('[Auth Check Error]', error);
        // При ошибке авторизации также оставляем пользователя неавторизованным,
        // чтобы пользователь мог залогиниться вручную.
        setUser(null);
      } finally {
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
  };

  const handleLogout = () => {
    authLogout();
    setUser(null);
    setCurrentView(AppView.AUDIT);
  };

  // Показываем загрузку при проверке авторизации
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0f1419] flex items-center justify-center">
        <div className="text-white text-xl">Загрузка...</div>
      </div>
    );
  }

  // Render Login if not authenticated (но с поддержкой демо-режима)
  // Проверяем наличие токена сброса пароля в URL
  const urlParams = new URLSearchParams(window.location.search);
  const resetToken = urlParams.get('token');

  if (resetToken && !user) {
    return (
      <DemoProvider>
        <DemoModeBanner />
        <ResetPassword
          token={resetToken}
          onSuccess={() => {
            // Удаляем token из URL и показываем форму входа
            window.history.replaceState({}, '', window.location.pathname);
            // Показываем форму входа после успешного сброса
            setUser(null);
          }}
        />
      </DemoProvider>
    );
  }

  if (!user) {
    return (
      <DemoProvider>
        <DemoModeBanner />
        <Auth onLogin={handleLogin} />
      </DemoProvider>
    );
  }

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
          />
        );
      case AppView.GENERATOR:
        return <DocumentGenerator initialData={generatorData} />;
      case AppView.CALCULATOR:
        return <Calculator preset={calcPreset} />;
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
        />
        <main className="flex-1 ml-0 md:ml-[280px] p-8 h-screen overflow-hidden">
          {renderContent()}
        </main>
      </div>
    </DemoProvider>
  );
};

export default App;