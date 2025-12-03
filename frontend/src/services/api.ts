/**
 * Базовые API функции для работы с backend
 * 
 * Этот файл содержит общие утилиты для работы с API.
 * Специфичные функции (analyzeDocument, analyzePackage и т.д.) 
 * находятся в geminiService.ts
 */

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

/**
 * Базовая функция для выполнения HTTP запросов
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} ${errorText}`);
  }

  return response.json();
}

/**
 * POST запрос с JSON телом
 */
export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  return apiRequest<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * GET запрос
 */
export async function apiGet<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  let url = endpoint;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }
  return apiRequest<T>(url);
}

/**
 * POST запрос с FormData (для загрузки файлов)
 */
export async function apiPostFormData<T>(endpoint: string, formData: FormData): Promise<T> {
  const url = `${API_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
    // Не устанавливаем Content-Type для FormData - браузер установит автоматически с boundary
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} ${errorText}`);
  }

  return response.json();
}

export default {
  apiRequest,
  apiPost,
  apiGet,
  apiPostFormData,
};

