import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Analyzer from './components/Analyzer';
import ComplexAudit from './components/ComplexAudit';
import HistoryView from './components/HistoryView';
import KnowledgeView from './components/KnowledgeView';
import Auth from './components/Auth';
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
      <div className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-900 dark:bg-[#0f1419] dark:text-white">
        <div className="text-xl">Загрузка...</div>
      </div>
    );
  }

  // Render app even без реальной авторизации — временный dev-режим без входа по паролю
  if (!user) {
    const demoUser: User = {
      id: 'demo',
      name: 'Тестовый специалист',
      company: 'Организация',
      tariff: 'Start',
      email: 'demo@tendershield.local',
    };

    return (
      <DemoProvider>
        <DemoModeBanner />
        <NotificationsPanel />
        <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0f1419] dark:text-white">
          <Sidebar
            currentView={currentView}
            onChangeView={setCurrentView}
            user={demoUser}
            onLogout={handleLogout}
          />
          <main className="flex-1 ml-0 md:ml-[280px] p-8 h-screen overflow-y-auto custom-scrollbar">
            {renderContent()}
          </main>
        </div>
      </DemoProvider>
    );
  }

  const renderContent = () => {
    switch (currentView) {
      case AppView.ANALYZER:
        return (
          <Analyzer
            onAnalysisComplete={setCalcPreset}
            onOpenCalculator={openCalculator}
          />
        );
      case AppView.AUDIT:
        return (
          <ComplexAudit
            onSelectForCalculator={setCalcPreset}
            onOpenCalculator={openCalculator}
          />
        );
      case AppView.GENERATOR:
        return <DocumentGenerator />;
      case AppView.CALCULATOR:
        return <Calculator preset={calcPreset} />;
      case AppView.HISTORY:
        return <HistoryView />;
      case AppView.PROFILE:
        return <Profile user={user} />;
      case AppView.KNOWLEDGE:
        return <KnowledgeView />;
      case AppView.ANALYTICS:
        return <Analytics />;
      case AppView.HELP:
        return <HelpGuide />;
      default:
        return (
          <ComplexAudit
            onSelectForCalculator={setCalcPreset}
            onOpenCalculator={openCalculator}
          />
        );
    }
  };

  return (
    <DemoProvider>
      <DemoModeBanner />
      <NotificationsPanel />
      <div className="flex min-h-screen bg-slate-50 text-slate-900 dark:bg-[#0f1419] dark:text-white">
        <Sidebar
          currentView={currentView}
          onChangeView={setCurrentView}
          user={user}
          onLogout={handleLogout}
        />
        <main className="flex-1 ml-0 md:ml-[280px] p-8 h-screen overflow-y-auto custom-scrollbar">
          {renderContent()}
        </main>
      </div>
    </DemoProvider>
  );
};

export default App;