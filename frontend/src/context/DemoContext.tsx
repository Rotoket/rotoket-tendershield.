/**
 * Контекст для управления демо-режимом
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

interface DemoState {
  isDemo: boolean;
  sessionId: string | null;
  remainingAnalyses: number;
  remainingHours: number;
  lastAnalysisAt: Date | null;
}

interface DemoContextType {
  demoState: DemoState;
  setDemoState: (state: Partial<DemoState>) => void;
  incrementAnalysis: () => void;
  getOrCreateSession: () => Promise<string>;
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export const useDemo = () => {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemo must be used within DemoProvider');
  }
  return context;
};

export const DemoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [demoState, setDemoStateInternal] = useState<DemoState>({
    isDemo: false,
    sessionId: null,
    remainingAnalyses: 3,
    remainingHours: 24,
    lastAnalysisAt: null,
  });

  const setDemoState = (updates: Partial<DemoState>) => {
    setDemoStateInternal((prev) => ({ ...prev, ...updates }));
  };

  const getOrCreateSession = async (): Promise<string> => {
    // Проверяем localStorage
    let sessionId = localStorage.getItem('demo_session_id');
    
    if (!sessionId) {
      // Создаем новую сессию
      sessionId = `demo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('demo_session_id', sessionId);
    }

    // Получаем информацию о сессии с сервера
    try {
      const response = await fetch(`http://localhost:8000/api/demo/session/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setDemoState({
          isDemo: true,
          sessionId: data.id,
          remainingAnalyses: 3 - data.analyses_count,
          remainingHours: data.remaining_hours || 24,
          lastAnalysisAt: data.last_analysis_at ? new Date(data.last_analysis_at) : null,
        });
      }
    } catch (error) {
      console.error('Ошибка получения демо-сессии:', error);
    }

    return sessionId;
  };

  const incrementAnalysis = () => {
    setDemoStateInternal((prev) => ({
      ...prev,
      remainingAnalyses: Math.max(0, prev.remainingAnalyses - 1),
      lastAnalysisAt: new Date(),
    }));
  };

  // Проверяем демо-режим при загрузке
  useEffect(() => {
    const checkDemoMode = async () => {
      const sessionId = localStorage.getItem('demo_session_id');
      if (sessionId) {
        await getOrCreateSession();
      }
    };
    checkDemoMode();
  }, []);

  return (
    <DemoContext.Provider
      value={{
        demoState,
        setDemoState,
        incrementAnalysis,
        getOrCreateSession,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
};

