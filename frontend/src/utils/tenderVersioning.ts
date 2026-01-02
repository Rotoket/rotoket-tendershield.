/**
 * Tender Versioning & Decision Actuality (ШАГ 1.1)
 *
 * Лёгкий клиентский реестр версий тендеров и принятых решений.
 * Хранится в localStorage, чтобы:
 * - привязать решение к конкретной версии документов;
 * - помечать решения как OUTDATED при появлении новой версии;
 * - включать UI-гварды (запрет экспорта, уведомление об устаревании).
 */

import type { TenderVersion, DecisionRecord, DecisionActuality } from '../types';

const VERSIONS_KEY = 'tendershield_tender_versions_v1';
const DECISIONS_KEY = 'tendershield_decision_records_v1';

interface StoredState<T> {
  items: T[];
}

// ===== Вспомогательные функции работы с localStorage =====

function readState<T>(key: string): T[] {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as StoredState<T> | T[];
    if (Array.isArray(parsed)) return parsed;
    if (parsed && Array.isArray((parsed as any).items)) return (parsed as any).items;
  } catch {
    // игнорируем ошибки, чтобы не ломать UI
  }
  return [];
}

function writeState<T>(key: string, items: T[]): void {
  try {
    const payload: StoredState<T> = { items };
    localStorage.setItem(key, JSON.stringify(payload));
  } catch {
    // Audit Trail и версионирование не должны ломать основной UX
  }
}

// ===== TenderVersion API =====

export function getTenderVersions(tenderId: string): TenderVersion[] {
  const all = readState<TenderVersion>(VERSIONS_KEY);
  return all.filter(v => v.tender_id === tenderId);
}

export function getCurrentTenderVersion(tenderId: string): TenderVersion | null {
  const versions = getTenderVersions(tenderId);
  if (versions.length === 0) return null;
  // Последняя по времени версия
  return versions.reduce((latest, v) =>
    !latest || v.created_at > latest.created_at ? v : latest,
  null as TenderVersion | null);
}

export function createTenderVersion(params: {
  tenderId: string;
  documentsHash: string;
}): TenderVersion {
  const versions = readState<TenderVersion>(VERSIONS_KEY);
  const now = new Date().toISOString();
  const version: TenderVersion = {
    tender_id: params.tenderId,
    version_id: `${params.tenderId}-${Date.now()}`,
    documents_hash: params.documentsHash,
    created_at: now,
  };

  versions.push(version);
  writeState(VERSIONS_KEY, versions);
  return version;
}

/**
 * Простейший детерминированный хеш по набору документов.
 * Использует имена и размеры файлов, чтобы отличать разные версии пакета.
 */
export function computeDocumentsHash(files: File[]): string {
  const key = files
    .map(f => `${f.name}:${f.size}`)
    .sort()
    .join('|');
  // Простая hash-функция (не крипто, только для сравнения версий)
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    const chr = key.charCodeAt(i);
    hash = (hash << 5) - hash + chr;
    hash |= 0; // 32-bit int
  }
  return `h${Math.abs(hash)}`;
}

// ===== DecisionRecord / DecisionActuality API =====

export function getDecisionRecords(tenderId: string): DecisionRecord[] {
  const all = readState<DecisionRecord>(DECISIONS_KEY);
  return all.filter(r => r.tender_id === tenderId);
}

export function getLatestDecisionRecord(tenderId: string): DecisionRecord | null {
  const records = getDecisionRecords(tenderId);
  if (records.length === 0) return null;
  return records.reduce((latest, r) =>
    !latest || (r.decision_fixed_at && (!latest.decision_fixed_at || r.decision_fixed_at > latest.decision_fixed_at))
      ? r
      : latest,
  null as DecisionRecord | null);
}

export function saveDecisionRecord(record: DecisionRecord): void {
  const records = readState<DecisionRecord>(DECISIONS_KEY);
  const withoutOld = records.filter(r => r.decision_id !== record.decision_id);
  withoutOld.push(record);
    writeState(DECISIONS_KEY, withoutOld);
}

/**
 * Обновляет флаг decision_actuality для всех решений по tenderId
 * в зависимости от актуальной версии тендера.
 */
export function recomputeDecisionActuality(tenderId: string, currentVersion: TenderVersion | null): void {
  const records = readState<DecisionRecord>(DECISIONS_KEY);
  const updated: DecisionRecord[] = records.map(rec => {
    if (rec.tender_id !== tenderId) return rec;
    let actuality: DecisionActuality = 'CURRENT';
    if (!currentVersion || rec.based_on_version_id !== currentVersion.version_id) {
      actuality = 'OUTDATED';
    }
    return { ...rec, decision_actuality: actuality };
  });
  writeState(DECISIONS_KEY, updated);
}

export function isDecisionOutdated(tenderId: string): boolean {
  const latest = getLatestDecisionRecord(tenderId);
  if (!latest) return false;
  return latest.decision_actuality === 'OUTDATED';
}

































