import { AnalysisResult, ChatMessage, PackageAnalysis, AuditHistoryResponse, UserDecisionData } from '../types';
import { getAuthHeaders } from './authService';
import { parseAPIError, handleNetworkError, type APIError } from '../utils/apiErrorHandler';

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

/**
 * Класс ошибки API с типом
 */
export class APIErrorException extends Error {
    constructor(public apiError: APIError) {
        super(apiError.message);
        this.name = 'APIErrorException';
    }
}

export const analyzeDocument = async (
    file: File,
    industry: string = 'UNIVERSAL',
    demoSessionId?: string | null
): Promise<AnalysisResult | null> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('industry', industry);

    console.log(`[API] Отправка файла: ${file.name}, Сфера: ${industry}, Demo: ${!!demoSessionId}`);

    // В DEMO-режиме НЕ требуем токен авторизации
    // Используем только demoSessionId
    const headers: HeadersInit = {};
    
    if (demoSessionId) {
        // DEMO-режим: используем только demo session ID
        headers['X-Demo-Session-Id'] = demoSessionId;
    } else {
        // Обычный режим: используем токен авторизации (если есть)
        const authHeaders = getAuthHeaders();
        if (Object.keys(authHeaders).length > 0) {
            Object.assign(headers, authHeaders);
        }
    }

    try {
        const requestUrl = `${API_URL}/analyze`;
        console.log(`[API] Запрос к: ${requestUrl}`);
        console.log(`[API] API_URL из env: ${import.meta.env.VITE_API_URL || 'не установлен'}`);

        // Добавляем AbortController для таймаута запроса (5 минут)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 минут
        
        const response = await fetch(requestUrl, {
            method: 'POST',
            headers,
            body: formData,
            signal: controller.signal,
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка при анализе документа');
            console.error("[API Error]", apiError);
            
            // В DEMO-режиме скрываем технические ошибки авторизации
            if (demoSessionId && response.status === 401) {
                // Заменяем техническую ошибку на нейтральную
                apiError.message = 'Не удалось продолжить анализ. Попробуйте ещё раз или загрузите документы повторно.';
                apiError.details = {
                    ...apiError.details,
                    hint: 'Если проблема повторяется, попробуйте обновить страницу.'
                };
            }
            
            throw new APIErrorException(apiError);
        }

        const data = await response.json();
        console.log("[API Success]", data);
        return data;
    } catch (error) {
        console.error("[Network Error]", error);
        console.error("[Network Error] URL был:", `${API_URL}/analyze`);
        console.error("[Network Error] API_URL:", API_URL);

        if (error instanceof APIErrorException) {
            throw error;
        }
        
        // Проверяем если это ошибка таймаута
        if (error instanceof Error && error.name === 'AbortError') {
            const timeoutError: APIError = {
                type: 'TIMEOUT_ERROR',
                message: 'Превышено время ожидания ответа от сервера (5 минут). Анализ может быть слишком долгим для больших документов.',
                statusCode: 408,
                details: {
                    hint: 'Попробуйте загрузить документ меньшего размера или подождите еще немного - анализ может завершиться.',
                    requestUrl: `${API_URL}/analyze`,
                    apiUrl: API_URL,
                }
            };
            throw new APIErrorException(timeoutError);
        }
        
        const networkError = handleNetworkError(error as Error);
        // Добавляем информацию об URL в детали ошибки
        networkError.details = {
            ...networkError.details,
            requestUrl: `${API_URL}/analyze`,
            apiUrl: API_URL,
        };
        throw new APIErrorException(networkError);
    }
};

export const chatWithSinaps = async (history: ChatMessage[], message: string): Promise<string> => {
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders(),
            },
            body: JSON.stringify({
                history: history.map(msg => ({
                    role: msg.role,
                    text: msg.text,
                })),
                message: message,
            }),
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка при отправке сообщения в чат');
            console.error("[API Error][chat]", apiError);
            throw new APIErrorException(apiError);
        }

        const data = await response.json();
        return data.response || "Ошибка получения ответа от сервера.";
    } catch (error) {
        console.error("[Network Error][chat]", error);
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Анализ пакета документов (комплексный аудит)
export const analyzePackage = async (
    files: File[],
    industry: string = 'UNIVERSAL',
    demoSessionId?: string | null
): Promise<PackageAnalysis> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('industry', industry);

    console.log(`[API] Отправка пакета файлов (${files.length} шт.), Сфера: ${industry}, Demo: ${!!demoSessionId}`);

    // В DEMO-режиме НЕ требуем токен авторизации
    const headers: HeadersInit = {};
    
    if (demoSessionId) {
        // DEMO-режим: используем только demo session ID
        headers['X-Demo-Session-Id'] = demoSessionId;
    } else {
        // Обычный режим: используем токен авторизации (если есть)
        const authHeaders = getAuthHeaders();
        if (Object.keys(authHeaders).length > 0) {
            Object.assign(headers, authHeaders);
        }
    }

    try {
        // Добавляем AbortController для таймаута запроса (10 минут для пакета)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 минут для пакета
        
        const response = await fetch(`${API_URL}/analyze-package`, {
            method: 'POST',
            headers,
            body: formData,
            signal: controller.signal,
        });
        
        clearTimeout(timeoutId);

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка при анализе пакета документов');
            console.error('[API Error][package]', apiError);
            
            // В DEMO-режиме скрываем технические ошибки авторизации
            if (demoSessionId && response.status === 401) {
                // Заменяем техническую ошибку на нейтральную
                apiError.message = 'Не удалось продолжить анализ. Попробуйте ещё раз или загрузите документы повторно.';
                apiError.details = {
                    ...apiError.details,
                    hint: 'Если проблема повторяется, попробуйте обновить страницу.'
                };
            }
            
            // Специальная обработка ошибки 503 (Ollama недоступен)
            if (response.status === 503) {
                apiError.message = 'Все AI-сервисы недоступны. Проверьте, запущен ли Ollama и установлены ли модели.';
                apiError.details = {
                    ...apiError.details,
                    hint: 'Убедитесь, что Ollama запущен на http://localhost:11434 и установлены модели (например: ollama pull qwen2.5:0.5b)'
                };
            }
            
            throw new APIErrorException(apiError);
        }

        const data = await response.json();
        console.log('[API Success][package]', data);
        return data as PackageAnalysis;
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        
        // Проверяем если это ошибка таймаута
        if (error instanceof Error && error.name === 'AbortError') {
            const timeoutError: APIError = {
                type: 'TIMEOUT_ERROR',
                message: 'Превышено время ожидания ответа от сервера (10 минут). Анализ пакета документов может быть очень долгим.',
                statusCode: 408,
                details: {
                    hint: 'Попробуйте загрузить меньше документов одновременно или подождите еще немного.',
                    requestUrl: `${API_URL}/analyze-package`,
                    apiUrl: API_URL,
                }
            };
            throw new APIErrorException(timeoutError);
        }
        
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Анализ по номеру закупки через zakupki.gov.ru
/**
 * Запускает асинхронный анализ документа
 */
export const startAnalysis = async (
    file: File | null,
    files: File[] | null,
    industry: string = 'UNIVERSAL',
    demoSessionId?: string | null
): Promise<{ analysis_id: string; status: string; message: string }> => {
    const formData = new FormData();
    
    if (file) {
        formData.append('file', file);
    } else if (files && files.length > 0) {
        files.forEach(f => formData.append('files', f));
    } else {
        throw new Error('Не переданы файлы для анализа');
    }
    
    formData.append('industry', industry);
    
    const headers: HeadersInit = {};
    
    if (demoSessionId) {
        headers['X-Demo-Session-Id'] = demoSessionId;
    } else {
        const authHeaders = getAuthHeaders();
        if (Object.keys(authHeaders).length > 0) {
            Object.assign(headers, authHeaders);
        }
    }
    
    const response = await fetch(`${API_URL}/analysis/start`, {
        method: 'POST',
        headers,
        body: formData,
    });
    
    if (!response.ok) {
        const errorData = await parseAPIError(response);
        throw new APIErrorException(errorData);
    }
    
    return await response.json();
};

/**
 * Получает статус задачи анализа
 */
export const getAnalysisStatus = async (
    analysisId: string,
    demoSessionId?: string | null
): Promise<{
    analysis_id: string;
    status: string;
    progress: number;
    stage?: string;
    result?: any;
    error_message?: string;
    created_at: string;
    started_at?: string;
    finished_at?: string;
}> => {
    const headers: HeadersInit = {};
    
    if (demoSessionId) {
        headers['X-Demo-Session-Id'] = demoSessionId;
    } else {
        const authHeaders = getAuthHeaders();
        if (Object.keys(authHeaders).length > 0) {
            Object.assign(headers, authHeaders);
        }
    }
    
    const response = await fetch(`${API_URL}/analysis/status/${analysisId}`, {
        method: 'GET',
        headers,
    });
    
    if (!response.ok) {
        const errorData = await parseAPIError(response);
        throw new APIErrorException(errorData);
    }
    
    return await response.json();
};

export const analyzeFromZakupki = async (tenderId: string): Promise<AnalysisResult> => {
    const formData = new FormData();
    formData.append('tenderId', tenderId);
    formData.append('industry', 'UNIVERSAL');

    try {
        const response = await fetch(`${API_URL}/analyze-from-zakupki`, {
            method: 'POST',
            headers: {
                ...getAuthHeaders(),
            },
            body: formData,
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка анализа по номеру закупки');
            console.error('[API Error][zakupki]', apiError);
            throw new APIErrorException(apiError);
        }

        const data = await response.json();
        console.log('[API Success][zakupki]', data);
        return data as AnalysisResult;
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// История проверок
export const fetchAuditHistory = async (
    limit: number = 50,
    search?: string,
    industry?: string,
    verdict?: string,
    minScore?: number,
    maxScore?: number
): Promise<AuditHistoryResponse> => {
    try {
        const params = new URLSearchParams();
        params.append('limit', limit.toString());
        if (search) params.append('search', search);
        if (industry && industry !== 'all') params.append('industry', industry);
        if (verdict && verdict !== 'all') params.append('verdict', verdict);
        if (minScore !== undefined) params.append('min_score', minScore.toString());
        if (maxScore !== undefined) params.append('max_score', maxScore.toString());

        const resp = await fetch(`${API_URL}/history?${params.toString()}`, {
            headers: {
                ...getAuthHeaders(),
            },
        });
        if (!resp.ok) {
            const apiError = await parseAPIError(resp, 'Ошибка загрузки истории анализов');
            throw new APIErrorException(apiError);
        }
        const data = await resp.json();
        return data as AuditHistoryResponse;
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Поиск по правовой базе (законы, разъяснения, практика)
export const searchLegal = async (query: string) => {
    try {
        const resp = await fetch(`${API_URL}/legal/search?query=${encodeURIComponent(query)}&limit=10`, {
            headers: {
                ...getAuthHeaders(),
            },
        });
        if (!resp.ok) {
            const apiError = await parseAPIError(resp, 'Ошибка поиска по правовой базе');
            throw new APIErrorException(apiError);
        }
        return await resp.json();
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Экспорт анализа в Excel
export const exportAnalysisToExcel = async (analysisData: AnalysisResult): Promise<Blob> => {
    try {
        const response = await fetch(`${API_URL}/export/excel`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders(),
            },
            body: JSON.stringify(analysisData),
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка экспорта в Excel');
            throw new APIErrorException(apiError);
        }

        return await response.blob();
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Экспорт анализа в Excel по ID
export const exportAnalysisToExcelById = async (analysisId: number): Promise<Blob> => {
    try {
        const response = await fetch(`${API_URL}/export/excel/${analysisId}`, {
            method: 'GET',
            headers: {
                ...getAuthHeaders(),
            },
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка экспорта в Excel');
            throw new APIErrorException(apiError);
        }

        return await response.blob();
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

// Сохранение решения пользователя (Decision Layer)
export const saveAnalysisDecision = async (
    analysisId: number,
    decisionData: UserDecisionData
): Promise<void> => {
    try {
        const response = await fetch(`${API_URL}/analysis/${analysisId}/decision`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders(),
            },
            body: JSON.stringify(decisionData),
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка сохранения решения');
            throw new APIErrorException(apiError);
        }
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};

export const savePackageDecision = async (
    packageId: string,
    decisionData: UserDecisionData
): Promise<void> => {
    try {
        const response = await fetch(`${API_URL}/package/${packageId}/decision`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders(),
            },
            body: JSON.stringify(decisionData),
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка сохранения решения');
            throw new APIErrorException(apiError);
        }
    } catch (error) {
        if (error instanceof APIErrorException) {
            throw error;
        }
        const networkError = handleNetworkError(error as Error);
        throw new APIErrorException(networkError);
    }
};
