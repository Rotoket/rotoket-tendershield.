/**
 * Сервис для работы с профилем пользователя
 */

import { getAuthHeaders } from './authService';
import type { AuthUser } from './authService';

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

export interface TariffInfo {
  id: number;
  name: string;
  price: number;
  analyses_limit: number;
  package_limit: number;
  features?: Record<string, any>;
}

export interface UsageInfo {
  analyses_count: number;
  packages_count: number;
  analyses_limit: number;
  package_limit: number;
  analyses_remaining: number; // -1 для безлимита
  packages_remaining: number; // -1 для безлимита
}

export interface CompanyProfileInfo {
  has_sro: boolean;
  has_fstek: boolean;
  has_fsb: boolean;
  has_mchs: boolean;
  experience_level?: string;
  tax_system?: string;
}

export interface ProfileInfo {
  user: AuthUser;
  tariff: TariffInfo | null;
  usage: UsageInfo | null;
  company_profile?: CompanyProfileInfo | null;
}

export interface PaymentInfo {
  payment_id: string;
  confirmation_url: string;
  amount: number;
  currency: string;
  description: string;
  test_mode?: boolean;
}

/**
 * Получение полной информации о профиле пользователя
 */
export const getProfile = async (): Promise<ProfileInfo> => {
  const response = await fetch(`${API_URL}/profile`, {
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Ошибка загрузки профиля' }));
    throw new Error(errorData.detail || `Ошибка загрузки профиля: ${response.status}`);
  }

  const data: ProfileInfo = await response.json();
  return data;
};

/**
 * Обновление профиля компании (СРО, лицензии, опыт и т.п.)
 */
export const updateCompanyProfile = async (profile: CompanyProfileInfo): Promise<ProfileInfo> => {
  const response = await fetch(`${API_URL}/profile/company`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Не удалось сохранить профиль компании' }));
    throw new Error(errorData.detail || `Ошибка при сохранении профиля: ${response.status}`);
  }

  const data: ProfileInfo = await response.json();
  return data;
};

/**
 * Получение списка доступных тарифов
 */
export const getTariffs = async (): Promise<TariffInfo[]> => {
  const response = await fetch(`${API_URL}/tariffs`, {
    headers: {
      ...getAuthHeaders(),
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Ошибка загрузки тарифов' }));
    throw new Error(errorData.detail || `Ошибка загрузки тарифов: ${response.status}`);
  }

  const data: TariffInfo[] = await response.json();
  return data;
};

/**
 * Создание платежа для подписки на тариф
 */
export const createPayment = async (tariffId: number): Promise<PaymentInfo> => {
  const response = await fetch(
    `${API_URL}/payment/create?tariff_id=${tariffId}`,
    {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
      },
    },
  );

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(text || `Ошибка создания платежа: ${response.status}`);
  }

  const data: PaymentInfo = await response.json();
  return data;
};


