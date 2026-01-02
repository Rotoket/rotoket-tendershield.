import { DecisionContour, AdvisorySnapshot } from '../types';
import { chatWithSinaps } from './geminiService';

export type AdvisoryProvider = 'ollama' | 'cloud';

export type AdvisoryType =
  | 'risk_summary'
  | 'financial_exposure'
  | 'legal_risks'
  | 'decision_implications'
  | 'board_summary';

interface GenerateAdvisoryParams {
  contour: DecisionContour;
  advisoryType: AdvisoryType;
  provider: AdvisoryProvider;
  question?: string;
}

// Простейший хеш по строке (placeholder вместо crypto)
const simpleHash = (input: string): string => {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) | 0;
  }
  return String(hash);
};

export const generateAdvisory = async ({
  contour,
  advisoryType,
  provider,
  question,
}: GenerateAdvisoryParams): Promise<AdvisorySnapshot> => {
  const analysisSnapshot = contour.analysis?.snapshot;
  const now = new Date().toISOString();

  const inputPayload = {
    contourId: contour.contourId,
    advisoryType,
    lifecycleState: contour.lifecycle.state,
    analysis: analysisSnapshot
      ? {
          verdict: analysisSnapshot.verdict,
          score: analysisSnapshot.score,
          nmck: analysisSnapshot.passport?.nmck,
          fz: analysisSnapshot.passport?.fz,
        }
      : null,
    question: question ?? null,
  };

  const inputHash = simpleHash(JSON.stringify(inputPayload));

  const systemPrompt = `Ты — аналитический модуль внутри системы Тендер.Щит.

ОБЯЗАТЕЛЬНО:
- Всегда отвечай ТОЛЬКО на русском языке.
- Используй деловой, управленческий стиль.
- Пиши так, как если бы текст читали директор или член правления.
- Используй российскую юридическую и финансовую терминологию.
- Все заголовки, подписи, предупреждения — ТОЛЬКО на русском.

ЗАПРЕЩЕНО:
- Использовать английские слова и фразы.
- Не давать рекомендаций «одобрить / отклонить» и не советовать конкретные действия.
- Принимать решения за директора.
- Изменять или переоценивать факты, переданные в анализе.

Твоя задача:
- Описывать риски, последствия и уязвимости.
- Объяснять, какие аспекты требуют управленческого внимания.
- Формулировать выводы в нейтральной, не директивной форме.

Твой ответ будет сохранён как официальный аналитический документ
и станет частью протокола принятия решения.`;

  // Пока используем существующий chat endpoint как cloud-провайдера без истории
  const messageParts: string[] = [];
  messageParts.push(systemPrompt);
  messageParts.push(`\nТип аналитической справки: ${advisoryType}`);
  if (analysisSnapshot) {
    messageParts.push(
      `\nКонтекст анализа: вердикт=${analysisSnapshot.verdict}, индекс_безопасности=${analysisSnapshot.score}, НМЦК=${analysisSnapshot.passport?.nmck}, закон=${analysisSnapshot.passport?.fz}`,
    );
  }
  if (question) {
    messageParts.push(`\nВопрос директора: ${question}`);
  }

  const content = await chatWithSinaps([], messageParts.join('\n'));

  // Валидация: пользовательский текст должен быть только на русском (без латинских букв)
  if (/[a-zA-Z]/.test(content)) {
    throw new Error('[AIOutputLanguage] Ожидался текст на русском языке, получен ответ с латинскими символами');
  }

  const advisoryId = `${contour.contourId}_${advisoryType}_${Date.now()}`;

  const snapshot: AdvisorySnapshot = {
    advisoryId,
    type: advisoryType,
    generatedAt: now,
    inputHash,
    model: provider === 'ollama' ? 'ollama:llama3' : 'cloud:sinaps',
    content,
  };

  return snapshot;
};











