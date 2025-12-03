/**
 * Утилиты для обработки ошибок API
 */

export enum APIErrorType {
  RATE_LIMIT = 'RATE_LIMIT',
  AUTH_ERROR = 'AUTH_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR',
  SERVER_ERROR = 'SERVER_ERROR',
  UNKNOWN = 'UNKNOWN',
}

export interface APIError {
  type: APIErrorType;
  message: string;
  statusCode?: number;
  details?: any;
}

/**
 * Парсит ошибку ответа API и возвращает структурированную ошибку
 */
export const parseAPIError = async (response: Response, defaultMessage?: string): Promise<APIError> => {
  let errorDetail: string = defaultMessage || 'Произошла ошибка';
  let errorData: any = null;

  try {
    const text = await response.text();
    if (text) {
      try {
        errorData = JSON.parse(text);
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch {
        errorDetail = text || errorDetail;
      }
    }
  } catch {
    // Если не удалось прочитать ответ, используем дефолтное сообщение
  }

  // Определяем тип ошибки по статус-коду
  if (response.status === 401 || response.status === 403) {
    // Проверяем, это ошибка лимита или обычная ошибка авторизации
    if (errorDetail.includes('лимит') || errorDetail.includes('limit')) {
      return {
        type: APIErrorType.RATE_LIMIT,
        message: errorDetail,
        statusCode: response.status,
        details: errorData,
      };
    }
    return {
      type: APIErrorType.AUTH_ERROR,
      message: errorDetail,
      statusCode: response.status,
      details: errorData,
    };
  }

  if (response.status === 429 || response.status === 403) {
    return {
      type: APIErrorType.RATE_LIMIT,
      message: errorDetail || 'Превышен лимит использования. Обновите тариф для продолжения работы.',
      statusCode: response.status,
      details: errorData,
    };
  }

  if (response.status >= 500) {
    return {
      type: APIErrorType.SERVER_ERROR,
      message: errorDetail || 'Ошибка на сервере. Попробуйте позже.',
      statusCode: response.status,
      details: errorData,
    };
  }

  return {
    type: APIErrorType.UNKNOWN,
    message: errorDetail,
    statusCode: response.status,
    details: errorData,
  };
};

/**
 * Обрабатывает ошибку сети
 */
export const handleNetworkError = (error: Error): APIError => {
  const errorMessage = error.message.toLowerCase();

  // Детектируем различные типы сетевых ошибок
  let message = 'Проблема с подключением к серверу. ';

  if (errorMessage.includes('failed to fetch') || errorMessage.includes('networkerror')) {
    message += 'Не удалось подключиться к серверу. Убедитесь, что:\n';
    message += '• Backend сервер запущен на порту 8000\n';
    message += '• URL API настроен правильно (проверьте .env файл)\n';
    message += '• Нет проблем с CORS или файрволом';
  } else if (errorMessage.includes('timeout')) {
    message += 'Превышено время ожидания ответа от сервера.';
  } else if (errorMessage.includes('cors')) {
    message += 'Ошибка CORS. Проверьте настройки сервера.';
  } else if (errorMessage.includes('refused')) {
    message += 'Соединение отклонено. Убедитесь, что backend сервер запущен.';
  } else {
    message += 'Проверьте интернет-соединение и настройки сервера.';
  }

  return {
    type: APIErrorType.NETWORK_ERROR,
    message: message,
    details: {
      originalError: error.message,
      errorName: error.name,
    },
  };
};

/**
 * Парсит ошибку из исключения
 */
export const parseError = (error: unknown): APIError => {
  // Проверяем, является ли это APIErrorException
  if (error && typeof error === 'object' && 'apiError' in error) {
    const exception = error as { apiError: APIError };
    return exception.apiError;
  }

  if (error instanceof Error) {
    // Проверяем, содержит ли ошибка информацию об API ошибке
    if ('type' in error && 'message' in error) {
      return error as unknown as APIError;
    }
    return handleNetworkError(error);
  }

  return {
    type: APIErrorType.UNKNOWN,
    message: 'Произошла неизвестная ошибка',
    details: error,
  };
};

