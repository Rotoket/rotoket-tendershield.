import { useEffect, useRef, useState } from 'react';
import type { DecisionContour } from '../types';

interface UseDecisionGuardOptions {
  onAbandon?: () => void;
}

interface UseDecisionGuardResult {
  isDecisionPending: boolean;
  isLeaveModalOpen: boolean;
  openLeaveModal: () => void;
  confirmStay: () => void;
  confirmLeave: () => void;
}

/**
 * Навигационный guard для Decision Contour.
 * Отвечает за перехват browser back/forward и refresh/close,
 * и показ модального окна при попытке выхода без решения.
 */
export const useDecisionGuard = (
  contour: DecisionContour | null,
  options?: UseDecisionGuardOptions,
): UseDecisionGuardResult => {
  const [isLeaveModalOpen, setIsLeaveModalOpen] = useState(false);
  const guardDisabledRef = useRef(false);

  const lifecycleState = contour?.lifecycle.state;
  const isDecisionPending = !!contour && lifecycleState !== 'decision_recorded' && lifecycleState !== 'abandoned';

  // При входе в контур — пушим state в history
  useEffect(() => {
    if (!contour) return;
    try {
      window.history.pushState({ contourId: contour.contourId }, '', window.location.href);
    } catch {
      // игнорируем ошибки history API
    }
  }, [contour?.contourId]);

  // Перехват browser back/forward
  useEffect(() => {
    if (!contour) return;

    const handlePopState = (event: PopStateEvent) => {
      if (guardDisabledRef.current) {
        return;
      }
      if (isDecisionPending) {
        // Показываем модальное окно и возвращаем пользователя обратно в контур
        setIsLeaveModalOpen(true);
        try {
          window.history.pushState({ contourId: contour.contourId }, '', window.location.href);
        } catch {
          // ignore
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [contour, isDecisionPending]);

  // Перехват refresh / закрытия вкладки
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!isDecisionPending) return;
      e.preventDefault();
      e.returnValue =
        'A director decision has not been recorded. Leaving will interrupt the decision contour.';
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isDecisionPending]);

  const openLeaveModal = () => setIsLeaveModalOpen(true);
  const confirmStay = () => setIsLeaveModalOpen(false);

  const confirmLeave = () => {
    setIsLeaveModalOpen(false);
    // Фиксируем отказ от решения (если предусмотрено)
    if (options?.onAbandon) {
      options.onAbandon();
    }
    // Снимаем guard и разрешаем реальный переход назад
    guardDisabledRef.current = true;
    try {
      window.history.back();
    } catch {
      // ignore
    }
  };

  return {
    isDecisionPending,
    isLeaveModalOpen,
    openLeaveModal,
    confirmStay,
    confirmLeave,
  };
};

export default useDecisionGuard;









































