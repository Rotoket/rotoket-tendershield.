/**
 * Сервис для работы с MCP (Model Context Protocol) - справочным слоем объяснений
 */

import { apiPost } from './api';

export interface LegalExplainRequest {
  question: string;
  context?: {
    lawCode?: string;
    pattern?: string;
    term?: string;
    [key: string]: any;
  };
}

export interface LegalExplainResponse {
  explanation: string;
  sources: string[];
  disclaimer: string;
}

/**
 * Получить объяснение правового вопроса через MCP
 */
export async function explainLegal(
  question: string,
  context?: LegalExplainRequest['context']
): Promise<LegalExplainResponse> {
  return apiPost<LegalExplainResponse>('/legal/explain', {
    question,
    context,
  });
}






































