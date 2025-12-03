export type LogLevel = 'info' | 'warn' | 'error';

/**
 * Унифицированный логгер UI-событий.
 * Пример сообщения: "Нажали кнопку 'Сформировать протокол', все успешно".
 */
export const logEvent = (
  context: string,
  message: string,
  level: LogLevel = 'info',
  extra?: unknown,
): void => {
  const timestamp = new Date().toISOString();
  const prefix = `[LOG][${timestamp}][${context}][${level.toUpperCase()}]`;

  if (extra !== undefined) {
    // eslint-disable-next-line no-console
    console.log(prefix, message, extra);
  } else {
    // eslint-disable-next-line no-console
    console.log(prefix, message);
  }
};
