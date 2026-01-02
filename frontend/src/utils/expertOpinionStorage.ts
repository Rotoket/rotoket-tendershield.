import type { ExpertOpinion, ExpertOpinionScope } from '../types';

const STORAGE_KEY = 'tendershield_expert_opinions_v1';

interface StoredState<T> {
  items: T[];
}

function readState(): ExpertOpinion[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredState<ExpertOpinion> | ExpertOpinion[];
    if (Array.isArray(parsed)) return parsed;
    if (parsed && Array.isArray(parsed.items)) return parsed.items;
  } catch {
    // игнорируем ошибки
  }
  return [];
}

function writeState(items: ExpertOpinion[]): void {
  try {
    const payload: StoredState<ExpertOpinion> = { items };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // не ломаем UI на ошибках записи
  }
}

export function getExpertOpinions(tenderId: string): ExpertOpinion[] {
  return readState().filter(op => op.tender_id === tenderId);
}

export function addExpertOpinion(params: {
  tenderId: string;
  authorId: string;
  scope: ExpertOpinionScope;
  text: string;
}): ExpertOpinion {
  const all = readState();
  const nowIso = new Date().toISOString();
  const opinion: ExpertOpinion = {
    opinion_id: `op_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    tender_id: params.tenderId,
    author_id: params.authorId,
    created_at: nowIso,
    scope: params.scope,
    text: params.text,
    affects_decision: false,
  };
  all.push(opinion);
  writeState(all);
  return opinion;
}

































