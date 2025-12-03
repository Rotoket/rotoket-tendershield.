import { describe, it, expect, beforeEach, vi } from 'vitest';
import { parseAPIError, handleNetworkError, parseError, APIErrorType } from './apiErrorHandler';
import { APIErrorException } from '../services/geminiService';

describe('apiErrorHandler', () => {
  describe('parseAPIError', () => {
    it('должен определить ошибку лимита по статусу 403', async () => {
      const response = new Response(
        JSON.stringify({ detail: 'Превышен лимит одиночных анализов по вашему тарифу.' }),
        { status: 403 }
      );

      const error = await parseAPIError(response);
      expect(error.type).toBe(APIErrorType.RATE_LIMIT);
      expect(error.statusCode).toBe(403);
      expect(error.message).toContain('лимит');
    });

    it('должен определить ошибку лимита по статусу 429', async () => {
      const response = new Response(
        JSON.stringify({ detail: 'Too many requests' }),
        { status: 429 }
      );

      const error = await parseAPIError(response);
      expect(error.type).toBe(APIErrorType.RATE_LIMIT);
      expect(error.statusCode).toBe(429);
    });

    it('должен определить ошибку авторизации по статусу 401', async () => {
      const response = new Response(
        JSON.stringify({ detail: 'Неверный email или пароль' }),
        { status: 401 }
      );

      const error = await parseAPIError(response);
      expect(error.type).toBe(APIErrorType.AUTH_ERROR);
      expect(error.statusCode).toBe(401);
    });

    it('должен определить ошибку сервера по статусу 500', async () => {
      const response = new Response(
        JSON.stringify({ detail: 'Internal server error' }),
        { status: 500 }
      );

      const error = await parseAPIError(response);
      expect(error.type).toBe(APIErrorType.SERVER_ERROR);
      expect(error.statusCode).toBe(500);
    });

    it('должен использовать сообщение из detail поля', async () => {
      const response = new Response(
        JSON.stringify({ detail: 'Custom error message' }),
        { status: 400 }
      );

      const error = await parseAPIError(response);
      expect(error.message).toBe('Custom error message');
    });

    it('должен использовать дефолтное сообщение, если detail отсутствует', async () => {
      const response = new Response(
        JSON.stringify({}),
        { status: 400 }
      );

      const error = await parseAPIError(response, 'Default error message');
      expect(error.message).toBe('Default error message');
    });
  });

  describe('handleNetworkError', () => {
    it('должен создать ошибку типа NETWORK_ERROR', () => {
      const error = new Error('Network request failed');
      const apiError = handleNetworkError(error);

      expect(apiError.type).toBe(APIErrorType.NETWORK_ERROR);
      expect(apiError.message).toContain('подключением');
      expect(apiError.details?.originalError).toBe('Network request failed');
    });
  });

  describe('parseError', () => {
    it('должен обработать APIErrorException', () => {
      const apiError = {
        type: APIErrorType.RATE_LIMIT,
        message: 'Rate limit exceeded',
        statusCode: 403,
      };
      const exception = new APIErrorException(apiError);

      const result = parseError(exception);
      expect(result.type).toBe(APIErrorType.RATE_LIMIT);
      expect(result.message).toBe('Rate limit exceeded');
    });

    it('должен обработать обычную Error как сетевую ошибку', () => {
      const error = new Error('Something went wrong');
      const result = parseError(error);

      expect(result.type).toBe(APIErrorType.NETWORK_ERROR);
    });

    it('должен обработать неизвестный тип ошибки', () => {
      const result = parseError('string error');
      expect(result.type).toBe(APIErrorType.UNKNOWN);
      expect(result.message).toBe('Произошла неизвестная ошибка');
    });
  });
});


