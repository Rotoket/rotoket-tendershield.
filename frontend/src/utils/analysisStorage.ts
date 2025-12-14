/**
 * Утилита для сохранения результатов анализа в localStorage
 * Автоматически удаляет записи старше 7 дней
 */

interface StoredAnalysis {
  id: string;
  mode: 'single' | 'package';
  result: any; // AnalysisResult | PackageAnalysis
  timestamp: number;
  expiresAt: number; // timestamp + 7 дней
}

const STORAGE_KEY = 'tender_shield_analyses';
const EXPIRY_DAYS = 7;

/**
 * Сохраняет результат анализа
 */
export const saveAnalysis = (mode: 'single' | 'package', result: any): string => {
  const id = `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const timestamp = Date.now();
  const expiresAt = timestamp + (EXPIRY_DAYS * 24 * 60 * 60 * 1000);

  const stored: StoredAnalysis = {
    id,
    mode,
    result,
    timestamp,
    expiresAt,
  };

  const analyses = getAllAnalyses();
  analyses.push(stored);
  
  // Очищаем просроченные перед сохранением
  const validAnalyses = analyses.filter(a => a.expiresAt > Date.now());
  validAnalyses.push(stored);
  
  localStorage.setItem(STORAGE_KEY, JSON.stringify(validAnalyses));
  
  return id;
};

/**
 * Получает все сохраненные анализы
 */
export const getAllAnalyses = (): StoredAnalysis[] => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    
    const analyses: StoredAnalysis[] = JSON.parse(stored);
    const now = Date.now();
    
    // Фильтруем просроченные
    const validAnalyses = analyses.filter(a => a.expiresAt > now);
    
    // Если были удалены просроченные, сохраняем обратно
    if (validAnalyses.length !== analyses.length) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(validAnalyses));
    }
    
    return validAnalyses.sort((a, b) => b.timestamp - a.timestamp); // Новые сверху
  } catch (error) {
    console.error('Error reading analyses from storage:', error);
    return [];
  }
};

/**
 * Получает анализ по ID
 */
export const getAnalysis = (id: string): StoredAnalysis | null => {
  const analyses = getAllAnalyses();
  const analysis = analyses.find(a => a.id === id);
  
  if (!analysis) return null;
  
  // Проверяем срок действия
  if (analysis.expiresAt <= Date.now()) {
    removeAnalysis(id);
    return null;
  }
  
  return analysis;
};

/**
 * Удаляет анализ по ID
 */
export const removeAnalysis = (id: string): void => {
  const analyses = getAllAnalyses();
  const filtered = analyses.filter(a => a.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
};

/**
 * Очищает все просроченные анализы
 */
export const cleanupExpiredAnalyses = (): number => {
  const analyses = getAllAnalyses();
  const now = Date.now();
  const validAnalyses = analyses.filter(a => a.expiresAt > now);
  const removedCount = analyses.length - validAnalyses.length;
  
  if (removedCount > 0) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(validAnalyses));
  }
  
  return removedCount;
};

/**
 * Получает последний анализ для режима
 */
export const getLastAnalysis = (mode: 'single' | 'package'): StoredAnalysis | null => {
  const analyses = getAllAnalyses();
  const filtered = analyses.filter(a => a.mode === mode);
  return filtered.length > 0 ? filtered[0] : null;
};






