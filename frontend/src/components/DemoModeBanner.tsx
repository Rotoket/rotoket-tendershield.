/**
 * Баннер для демо-режима
 * Показывает информацию о лимитах и предложения регистрации
 */

import React from 'react';
import { useDemo } from '../context/DemoContext';
import { getCurrentUser } from '../services/authService';
import { AlertCircle, Clock, Zap } from 'lucide-react';

export const DemoModeBanner: React.FC = () => {
  const { demoState } = useDemo();
  const [user, setUser] = React.useState<any>(null);

  // Проверяем авторизацию
  React.useEffect(() => {
    getCurrentUser().then(setUser).catch(() => setUser(null));
  }, []);

  // Скрываем для авторизованных пользователей
  if (user || !demoState.isDemo) {
    return null;
  }

  const { remainingAnalyses, remainingHours } = demoState;

  // Триггер #2: При достижении лимита
  if (remainingAnalyses === 0 && remainingHours > 0) {
    return (
      <div className="fixed top-0 left-0 right-0 bg-amber-500 text-white px-4 py-3 flex justify-between items-center shadow-lg z-50">
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5" />
          <div>
            <span className="font-semibold">⚠️ Демо лимит достигнут</span>
            <p className="text-sm mt-1">
              Попробуйте через {remainingHours} часов или зарегистрируйтесь для неограниченного доступа
            </p>
          </div>
        </div>
        <button
          className="bg-white text-amber-600 px-4 py-2 rounded-md font-semibold hover:bg-amber-50 transition-colors"
          onClick={() => (window.location.href = '/register')}
        >
          Зарегистрироваться
        </button>
      </div>
    );
  }

  // Триггер #2 (вариант): При приближении к лимиту (1 анализ остался)
  if (remainingAnalyses === 1) {
    return (
      <div className="fixed top-0 left-0 right-0 bg-blue-500 text-white px-4 py-3 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Zap className="w-5 h-5" />
            <span>
              ℹ️ У вас остался <strong>1 бесплатный анализ</strong> в сутки.
              Получите 47 дополнительных в плане!
            </span>
          </div>
          <button
            className="bg-white text-blue-600 px-4 py-2 rounded-md font-semibold hover:bg-blue-50 transition-colors"
            onClick={() => (window.location.href = '/pricing')}
          >
            Перейти на PRO
          </button>
        </div>
      </div>
    );
  }

  // Информационный баннер для демо-режима
  if (remainingAnalyses > 1) {
    return (
      <div className="fixed top-0 left-0 right-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-2 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span className="text-sm">
              🎉 Демо-режим: {remainingAnalyses} анализов осталось сегодня
            </span>
          </div>
          <button
            className="text-sm underline hover:no-underline"
            onClick={() => (window.location.href = '/register')}
          >
            Зарегистрироваться для неограниченного доступа
          </button>
        </div>
      </div>
    );
  }

  return null;
};

