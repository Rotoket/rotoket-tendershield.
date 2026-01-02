/**
 * Сервис для работы с Kill Switch API
 */

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

export interface KillSwitchStatus {
  mode: 'NORMAL' | 'SAFE' | 'LOCKDOWN';
  is_active: boolean;
  kill_switch_enabled?: boolean;
  last_activation?: {
    id: string;
    timestamp: string;
    reason: string;
    trigger: string;
    previous_mode: string;
    new_mode: string;
  };
}

/**
 * Получение текущего статуса Kill Switch
 */
export const getKillSwitchStatus = async (): Promise<KillSwitchStatus> => {
  try {
    const response = await fetch(`${API_URL}/kill-switch/status`);
    if (!response.ok) {
      // Если endpoint не доступен, возвращаем нормальный режим
      return {
        mode: 'NORMAL',
        is_active: false,
        kill_switch_enabled: false,
      };
    }
    const data = await response.json();
    return data as KillSwitchStatus;
  } catch (error) {
    console.error('[KillSwitchService] Error fetching kill switch status:', error);
    // При ошибке возвращаем нормальный режим
    return {
      mode: 'NORMAL',
      is_active: false,
      kill_switch_enabled: false,
    };
  }
};





























