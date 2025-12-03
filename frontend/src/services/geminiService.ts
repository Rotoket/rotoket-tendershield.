import { AnalysisResult, ChatMessage, PackageAnalysis, AuditHistoryResponse } from '../types';
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

    console.log(`[API] Отправка файла: ${file.name}, Сфера: ${industry}`);

    // Добавляем заголовок с demo_session_id, если есть
    const headers: HeadersInit = {
        ...getAuthHeaders(),
    };

    if (demoSessionId) {
        headers['X-Demo-Session-Id'] = demoSessionId;
    }

    try {
        const requestUrl = `${API_URL}/analyze`;
        console.log(`[API] Запрос к: ${requestUrl}`);
        console.log(`[API] API_URL из env: ${import.meta.env.VITE_API_URL || 'не установлен'}`);

        const response = await fetch(requestUrl, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const apiError = await parseAPIError(response, 'Ошибка при анализе документа');
            console.error("[API Error]", apiError);
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
): Promise<PackageAnalysis> => {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('industry', industry);

    console.log(`[API] Отправка пакета файлов (${files.length} шт.), Сфера: ${industry}`);

    const response = await fetch(`${API_URL}/analyze-package`, {
        method: 'POST',
        headers: {
            ...getAuthHeaders(),
        },
        body: formData,
    });

    if (!response.ok) {
        const apiError = await parseAPIError(response, 'Ошибка при анализе пакета документов');
        console.error('[API Error][package]', apiError);
        throw new APIErrorException(apiError);
    }

    const data = await response.json();
    console.log('[API Success][package]', data);
    return data as PackageAnalysis;
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
