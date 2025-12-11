import type { VerdictType } from '../types';

/**
 * Человекочитаемая подпись вердикта для интерфейса.
 * Внутри системы мы продолжаем использовать коды STOP / CAUTION / PARTICIPATE,
 * а пользователю показываем русский текст.
 */
export const verdictLabel = (verdict: VerdictType | string): string => {
  if (!verdict) return 'Не оценено';
  const v = verdict.toString().toUpperCase();

  switch (v) {
    case 'STOP':
      return 'Не участвовать';
    case 'CAUTION':
      return 'Осторожно';
    case 'PARTICIPATE':
      return 'Можно участвовать';
    default:
      return verdict.toString();
  }
};

/**
 * Лейбл для уровня риска / серьёзности (HIGH / MEDIUM / LOW и т.п.) на русском.
 */
export const severityLabel = (severity?: string | null): string => {
  if (!severity) return 'Не оценено';
  const s = severity.toString().toUpperCase();

  if (s.includes('HIGH') || s.includes('КРИТ')) return 'Высокий риск';
  if (s.includes('MED') || s.includes('СРЕД') || s.includes('MID')) return 'Средний риск';
  if (s.includes('LOW') || s.includes('НИЗК')) return 'Низкий риск';

  return severity.toString();
};
