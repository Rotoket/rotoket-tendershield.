/**
 * Утилиты для валидации файлов
 */

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 МБ
const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.xls', '.xlsx'];
const ALLOWED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
  'text/plain',
  'application/rtf',
  'text/rtf',
  // Excel
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
];

/**
 * Проверяет файл перед загрузкой
 */
export const validateFile = (file: File): FileValidationResult => {
  // Проверка размера
  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: `Файл слишком большой (${(file.size / 1024 / 1024).toFixed(2)} МБ). Максимальный размер: ${MAX_FILE_SIZE / 1024 / 1024} МБ`,
    };
  }

  if (file.size === 0) {
    return {
      valid: false,
      error: 'Файл пустой',
    };
  }

  // Проверка расширения
  const fileName = file.name.toLowerCase();
  const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => fileName.endsWith(ext));

  if (!hasValidExtension) {
    return {
      valid: false,
      error: `Неподдерживаемый формат файла. Разрешенные форматы: ${ALLOWED_EXTENSIONS.join(', ')}`,
    };
  }

  // Проверка MIME типа (если доступен)
  if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
    // Не блокируем, если MIME тип не совпадает, но расширение правильное
    // (некоторые браузеры могут неправильно определять MIME тип)
    console.warn(`Неожиданный MIME тип: ${file.type} для файла ${file.name}`);
  }

  return { valid: true };
};

/**
 * Форматирует размер файла в читаемый вид
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Б';

  const k = 1024;
  const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

/**
 * Получает расширение файла
 */
export const getFileExtension = (fileName: string): string => {
  const lastDot = fileName.lastIndexOf('.');
  return lastDot !== -1 ? fileName.substring(lastDot).toLowerCase() : '';
};

/**
 * Проверяет, является ли файл допустимым типом
 */
export const isAllowedFileType = (fileName: string): boolean => {
  const extension = getFileExtension(fileName);
  return ALLOWED_EXTENSIONS.includes(extension);
};


