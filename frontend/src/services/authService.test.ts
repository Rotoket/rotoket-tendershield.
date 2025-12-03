import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  saveToken,
  getToken,
  removeToken,
  getAuthHeaders,
  register,
  login,
  getCurrentUser,
  logout,
  isAuthenticated,
} from './authService';

// Мокаем fetch
global.fetch = vi.fn();

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

describe('authService', () => {
  beforeEach(() => {
    // Очищаем localStorage перед каждым тестом
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Token management', () => {
    it('должен сохранять токен в localStorage', () => {
      saveToken('test-token-123');
      expect(localStorage.getItem('tender_shield_token')).toBe('test-token-123');
    });

    it('должен получать токен из localStorage', () => {
      localStorage.setItem('tender_shield_token', 'test-token-123');
      expect(getToken()).toBe('test-token-123');
    });

    it('должен возвращать null, если токен отсутствует', () => {
      expect(getToken()).toBeNull();
    });

    it('должен удалять токен из localStorage', () => {
      localStorage.setItem('tender_shield_token', 'test-token-123');
      removeToken();
      expect(localStorage.getItem('tender_shield_token')).toBeNull();
    });

    it('должен возвращать заголовки авторизации с токеном', () => {
      localStorage.setItem('tender_shield_token', 'test-token-123');
      const headers = getAuthHeaders();
      expect(headers).toEqual({ Authorization: 'Bearer test-token-123' });
    });

    it('должен возвращать пустые заголовки, если токена нет', () => {
      const headers = getAuthHeaders();
      expect(headers).toEqual({});
    });

    it('должен проверять, авторизован ли пользователь', () => {
      expect(isAuthenticated()).toBe(false);
      saveToken('test-token-123');
      expect(isAuthenticated()).toBe(true);
      removeToken();
      expect(isAuthenticated()).toBe(false);
    });
  });

  describe('register', () => {
    it('должен успешно зарегистрировать пользователя', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        company: 'Test Company',
        tariff_id: 1,
        is_active: true,
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const result = await register({
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
        company: 'Test Company',
      });

      expect(fetch).toHaveBeenCalledWith(`${API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
          name: 'Test User',
          company: 'Test Company',
        }),
      });

      expect(result).toEqual(mockUser);
    });

    it('должен выбрасывать ошибку при неудачной регистрации', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Пользователь уже существует' }),
      });

      await expect(
        register({
          email: 'test@example.com',
          password: 'password123',
        })
      ).rejects.toThrow('Пользователь уже существует');
    });
  });

  describe('login', () => {
    it('должен успешно войти и получить токен', async () => {
      const mockToken = {
        access_token: 'test-token-123',
        token_type: 'bearer',
      };

      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        company: 'Test Company',
        tariff_id: 1,
        is_active: true,
      };

      // Мокаем запрос логина
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockToken,
      });

      // Мокаем запрос получения пользователя
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const result = await login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(localStorage.getItem('tender_shield_token')).toBe('test-token-123');
      expect(result.access_token).toBe('test-token-123');
      expect(result.user).toEqual(mockUser);
    });

    it('должен выбрасывать ошибку при неверных учетных данных', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Неверный email или пароль' }),
      });

      await expect(
        login({
          email: 'test@example.com',
          password: 'wrong-password',
        })
      ).rejects.toThrow('Неверный email или пароль');
    });
  });

  describe('getCurrentUser', () => {
    it('должен возвращать пользователя, если токен валиден', async () => {
      localStorage.setItem('tender_shield_token', 'test-token-123');

      const mockUser = {
        id: 1,
        email: 'test@example.com',
        name: 'Test User',
        tariff_id: 1,
        is_active: true,
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUser,
      });

      const result = await getCurrentUser();
      expect(result).toEqual(mockUser);
      expect(fetch).toHaveBeenCalledWith(`${API_URL}/auth/me`, {
        headers: {
          Authorization: 'Bearer test-token-123',
        },
      });
    });

    it('должен возвращать null, если токена нет', async () => {
      const result = await getCurrentUser();
      expect(result).toBeNull();
      expect(fetch).not.toHaveBeenCalled();
    });

    it('должен удалять токен и возвращать null при 401 ошибке', async () => {
      localStorage.setItem('tender_shield_token', 'invalid-token');

      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      const result = await getCurrentUser();
      expect(result).toBeNull();
      expect(localStorage.getItem('tender_shield_token')).toBeNull();
    });
  });

  describe('logout', () => {
    it('должен удалять токен из localStorage', () => {
      localStorage.setItem('tender_shield_token', 'test-token-123');
      logout();
      expect(localStorage.getItem('tender_shield_token')).toBeNull();
    });
  });
});


