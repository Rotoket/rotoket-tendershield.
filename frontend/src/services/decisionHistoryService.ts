import { VerdictType, UserDecision } from '../types';

/**
 * Каноническая сущность истории решений
 * История = факт принятого решения, а не весь анализ
 */
export interface TenderDecisionRecord {
  id: string;
  source: 'single' | 'package';
  sourceId: string; // documentId или packageId
  context: {
    title?: string;
    law?: string;
    nmck?: string;
    region?: string;
    documentsCount?: number;
  };
  verdict: VerdictType;
  score: number;
  dealBreakersCount: number;
  decision: {
    value: UserDecision;
    comment?: string;
    timestamp: string;
  };
  createdAt: string;
}

const STORAGE_KEY = 'tender_decisions_history';
const MAX_HISTORY_ITEMS = 100;

/**
 * Сохраняет решение в историю
 * Единственная точка сохранения решений
 */
export const saveDecisionToHistory = async (
  record: TenderDecisionRecord
): Promise<void> => {
  try {
    // Получаем текущую историю из localStorage
    const existing = localStorage.getItem(STORAGE_KEY);
    const history: TenderDecisionRecord[] = existing ? JSON.parse(existing) : [];
    
    // Добавляем новую запись
    history.unshift(record);
    
    // Ограничиваем размер истории
    const trimmed = history.slice(0, MAX_HISTORY_ITEMS);
    
    // Сохраняем обратно
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    
    console.log('[DecisionHistory] Решение сохранено в историю:', record.id);
  } catch (error) {
    console.error('[DecisionHistory] Ошибка сохранения решения:', error);
    throw error;
  }
};

/**
 * Получает историю решений
 */
export const getDecisionHistory = (): TenderDecisionRecord[] => {
  try {
    const existing = localStorage.getItem(STORAGE_KEY);
    if (!existing) return [];
    
    const history: TenderDecisionRecord[] = JSON.parse(existing);
    return history;
  } catch (error) {
    console.error('[DecisionHistory] Ошибка загрузки истории:', error);
    return [];
  }
};

/**
 * Очищает историю решений
 */
export const clearDecisionHistory = (): void => {
  localStorage.removeItem(STORAGE_KEY);
};













































