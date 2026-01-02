import { AuditEvent } from '../types';
import { logEvent } from './logger';

const STORAGE_KEY = 'tender_shield_audit_trail_v1';

const readAuditTrail = (): AuditEvent[] => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: AuditEvent[] = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const writeAuditTrail = (events: AuditEvent[]): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
  } catch {
    // игнорируем ошибки записи — Audit Trail не должен ломать работу UI
  }
};

export const appendAuditEvent = (event: AuditEvent): void => {
  const events = readAuditTrail();
  events.push(event);
  writeAuditTrail(events);

  logEvent('AuditTrail', 'audit_event_appended', 'info', {
    eventType: event.eventType,
    entityType: event.entityType,
    entityId: event.entityId,
  });
};

export const getAuditTrail = (): AuditEvent[] => {
  const events = readAuditTrail();
  return events.slice().sort((a, b) => a.timestamp.localeCompare(b.timestamp));
};













































