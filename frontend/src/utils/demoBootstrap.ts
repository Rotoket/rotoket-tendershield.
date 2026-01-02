/**
 * Утилита для создания demo-сессии и DecisionContour при входе с Landing
 */

import { createDecisionContour, saveDecisionContour, loadDecisionContour, type DecisionContour } from './decisionContour';
import { logEvent } from './logger';

export interface DemoSession {
  id: string;
  createdAt: string;
  expiresAt: string; // ISO
  source: 'landing';
  status: 'active';
}

const DEMO_SESSION_KEY = 'demo_session';
const CURRENT_CONTOUR_KEY = 'current_contour_id';

/**
 * Создаёт demo-сессию и DecisionContour при входе с Landing
 */
export const bootstrapDemoSession = (): { session: DemoSession; contour: DecisionContour } => {
  // Проверяем, есть ли уже активная сессия
  const existingSession = localStorage.getItem(DEMO_SESSION_KEY);
  if (existingSession) {
    try {
      const session: DemoSession = JSON.parse(existingSession);
      const expiresAt = new Date(session.expiresAt);
      
      // Если сессия ещё не истекла, используем её
      if (expiresAt > new Date()) {
        const contourId = localStorage.getItem(CURRENT_CONTOUR_KEY);
        if (contourId) {
          // Пытаемся загрузить существующий контур
          const contour = loadDecisionContour(contourId);
          if (contour && contour.lifecycle.state !== 'abandoned') {
            logEvent('DemoBootstrap', 'Existing demo session restored', 'info', { sessionId: session.id, contourId });
            return { session, contour };
          }
        }
      }
    } catch (e) {
      // Если ошибка парсинга, создаём новую сессию
      console.warn('Failed to parse existing demo session, creating new one', e);
    }
  }

  // Создаём новую demo-сессию
  const sessionId = `demo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 24 * 60 * 60 * 1000); // +24 часа

  const session: DemoSession = {
    id: sessionId,
    createdAt: now.toISOString(),
    expiresAt: expiresAt.toISOString(),
    source: 'landing',
    status: 'active',
  };

  // Создаём DecisionContour в draft-режиме
  const contourId = `contour_${sessionId}`;
  const contour = createDecisionContour('demo', contourId);

  // Добавляем событие session_started в audit trail
  const sessionEvent = {
    eventId: `${contourId}_session_started_${Date.now()}`,
    timestamp: now.toISOString(),
    type: 'contour_created' as const,
    actor: { type: 'system' as const },
  };

  const contourWithSession: DecisionContour = {
    ...contour,
    auditTrail: [
      ...contour.auditTrail,
      {
        ...sessionEvent,
        type: 'contour_created',
      },
    ],
  };

  // Сохраняем в localStorage
  localStorage.setItem(DEMO_SESSION_KEY, JSON.stringify(session));
  localStorage.setItem(CURRENT_CONTOUR_KEY, contourId);
  saveDecisionContour(contourWithSession);

  logEvent('DemoBootstrap', 'Demo session created', 'info', {
    sessionId,
    contourId,
    expiresAt: expiresAt.toISOString(),
  });

  return { session, contour: contourWithSession };
};

/**
 * Получает текущую demo-сессию
 */
export const getCurrentDemoSession = (): DemoSession | null => {
  try {
    const raw = localStorage.getItem(DEMO_SESSION_KEY);
    if (!raw) return null;
    const session: DemoSession = JSON.parse(raw);
    const expiresAt = new Date(session.expiresAt);
    if (expiresAt <= new Date()) {
      // Сессия истекла
      localStorage.removeItem(DEMO_SESSION_KEY);
      localStorage.removeItem(CURRENT_CONTOUR_KEY);
      return null;
    }
    return session;
  } catch {
    return null;
  }
};

/**
 * Получает текущий DecisionContour
 */
export const getCurrentContour = (): DecisionContour | null => {
  const contourId = localStorage.getItem(CURRENT_CONTOUR_KEY);
  if (!contourId) return null;
  
  return loadDecisionContour(contourId);
};

