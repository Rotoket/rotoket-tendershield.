import { getAuthHeaders } from './authService';
import { parseAPIError, handleNetworkError, type APIError } from '../utils/apiErrorHandler';
import { APIErrorException } from './geminiService';

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

export interface UserStats {
  user_id: number;
  email: string;
  plan_type: string;
  total_analyses: number;
  total_packages: number;
  current_month_analyses: number;
  tariff_limit: number;
  trial_active: boolean;
  trial_days_left: number;
}

export interface SystemStats {
  total_users: number;
  active_users_30d: number;
  total_analyses: number;
  recent_analyses_30d: number;
  tariff_distribution: Record<string, number>;
  industry_distribution: Record<string, number>;
}

export interface TimelineData {
  date: string;
  count: number;
}

export interface PopularIndustry {
  industry: string;
  count: number;
}

export interface AverageScore {
  average_score: number;
  analyses_count: number;
}

// Получить статистику пользователя
export const getUserAnalytics = async (userId: number): Promise<UserStats> => {
  try {
    const response = await fetch(`${API_URL}/analytics/user/${userId}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      const apiError = await parseAPIError(response, 'Ошибка загрузки статистики пользователя');
      throw new APIErrorException(apiError);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIErrorException) {
      throw error;
    }
    const networkError = handleNetworkError(error as Error);
    throw new APIErrorException(networkError);
  }
};

// Получить системную статистику (только для админов)
export const getSystemAnalytics = async (): Promise<SystemStats> => {
  try {
    const response = await fetch(`${API_URL}/analytics/system`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      const apiError = await parseAPIError(response, 'Ошибка загрузки системной статистики');
      throw new APIErrorException(apiError);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIErrorException) {
      throw error;
    }
    const networkError = handleNetworkError(error as Error);
    throw new APIErrorException(networkError);
  }
};

// Получить временную линию анализов
export const getAnalyticsTimeline = async (days: number = 30): Promise<TimelineData[]> => {
  try {
    const response = await fetch(`${API_URL}/analytics/timeline?days=${days}`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(),
      },
    });

    if (!response.ok) {
      const apiError = await parseAPIError(response, 'Ошибка загрузки временной линии');
      throw new APIErrorException(apiError);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIErrorException) {
      throw error;
    }
    const networkError = handleNetworkError(error as Error);
    throw new APIErrorException(networkError);
  }
};

// Получить популярные отрасли
export const getPopularIndustries = async (limit: number = 5): Promise<PopularIndustry[]> => {
  try {
    const response = await fetch(`${API_URL}/analytics/popular-industries?limit=${limit}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const apiError = await parseAPIError(response, 'Ошибка загрузки популярных отраслей');
      throw new APIErrorException(apiError);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIErrorException) {
      throw error;
    }
    const networkError = handleNetworkError(error as Error);
    throw new APIErrorException(networkError);
  }
};

// Получить средние оценки по отраслям
export const getAverageScores = async (): Promise<Record<string, AverageScore>> => {
  try {
    const response = await fetch(`${API_URL}/analytics/average-scores`, {
      method: 'GET',
    });

    if (!response.ok) {
      const apiError = await parseAPIError(response, 'Ошибка загрузки средних оценок');
      throw new APIErrorException(apiError);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIErrorException) {
      throw error;
    }
    const networkError = handleNetworkError(error as Error);
    throw new APIErrorException(networkError);
  }
};

