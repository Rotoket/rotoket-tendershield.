import {
  DecisionContour,
  DecisionContourAuditEvent,
  AdvisorySnapshot,
  DecisionContourLifecycleState,
  AnalysisResult,
  UserDecision,
  ExportSnapshot,
  ExportType,
} from '../types';

const STORAGE_PREFIX = 'decision_contour_';

const buildStorageKey = (contourId: string) => `${STORAGE_PREFIX}${contourId}`;

export const createDecisionContour = (mode: 'demo' | 'prod', contourId: string): DecisionContour => {
  const now = new Date().toISOString();

  const base: DecisionContour = {
    contourId,
    mode,
    lifecycle: {
      state: 'draft',
      createdAt: now,
      updatedAt: now,
    },
    input: {},
    advisory: [],
    auditTrail: [],
  };

  const createdEvent: DecisionContourAuditEvent = {
    eventId: `${contourId}_contour_created_${Date.now()}`,
    timestamp: now,
    type: 'contour_created',
    actor: { type: 'system' },
  };

  return {
    ...base,
    auditTrail: [createdEvent],
  };
};

export const loadDecisionContour = (contourId: string): DecisionContour | null => {
  try {
    const raw = localStorage.getItem(buildStorageKey(contourId));
    if (!raw) return null;
    return JSON.parse(raw) as DecisionContour;
  } catch {
    return null;
  }
};

export const saveDecisionContour = (contour: DecisionContour): void => {
  try {
    localStorage.setItem(buildStorageKey(contour.contourId), JSON.stringify(contour));
  } catch {
    // Persistence ошибок не должны ломать UI
  }
};

// --- Иммутабельные действия над DecisionContour ---

export type ContourAction =
  | {
      type: 'SET_INPUT';
      payload: {
        fileMeta?: { name: string; size: number; hash: string };
        industry?: string;
      };
    }
  | {
      type: 'FREEZE_ANALYSIS';
      payload: {
        snapshot: AnalysisResult;
        fileMeta: { name: string; size: number; hash: string };
        industry?: string;
        actorRole?: string;
      };
    }
  | {
      type: 'APPEND_ADVISORY';
      payload: {
        snapshot: AdvisorySnapshot;
      };
    }
  | {
      type: 'RECORD_DECISION';
      payload: {
        decision: UserDecision;
        role?: string;
      };
    }
  | {
      type: 'ABANDON_CONTOUR';
      payload?: {
        role?: string;
      };
    }
  | {
      type: 'REGISTER_EXPORT';
      payload: {
        exportSnapshot: ExportSnapshot;
        role?: string;
      };
    };

const assertInvariant = (condition: boolean, message: string): void => {
  if (!condition) {
    throw new Error(`[DecisionContourInvariant] ${message}`);
  }
};

const assertState = (state: DecisionContourLifecycleState, allowed: DecisionContourLifecycleState[], action: string) => {
  if (!allowed.includes(state)) {
    throw new Error(`[DecisionContour] Action "${action}" is not allowed in state "${state}"`);
  }
};

/**
 * Единственная точка изменения DecisionContour.
 * Любая попытка нарушить правила жизненного цикла приводит к runtime‑ошибке.
 */
export const updateDecisionContour = (contour: DecisionContour, action: ContourAction): DecisionContour => {
  // Полностью заблокированное состояние
  if (contour.lifecycle.state === 'abandoned') {
    throw new Error('[DecisionContour] Contour is abandoned and cannot be modified');
  }

  const nowIso = new Date().toISOString();

  let updated: DecisionContour = contour;

  switch (action.type) {
    case 'SET_INPUT': {
      assertState(contour.lifecycle.state, ['draft'], 'SET_INPUT');

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          updatedAt: nowIso,
        },
        input: {
          ...contour.input,
          ...action.payload,
        },
      };
      break;
    }

    case 'FREEZE_ANALYSIS': {
      assertState(contour.lifecycle.state, ['draft'], 'FREEZE_ANALYSIS');
      if (contour.analysis) {
        throw new Error('[DecisionContour] Analysis is already frozen');
      }

      // Замораживаем snapshot анализа (поверхностно, но этого достаточно для UI‑уровня)
      const frozenSnapshot = Object.freeze({ ...(action.payload.snapshot as AnalysisResult) });

      const analysisEvent: DecisionContourAuditEvent = {
        eventId: `${contour.contourId}_analysis_completed_${Date.now()}`,
        timestamp: nowIso,
        type: 'analysis_completed',
        actor: {
          type: 'system',
          role: action.payload.actorRole,
        },
        snapshotRef: 'analysis',
      };

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          state: 'analysis_ready',
          updatedAt: nowIso,
        },
        input: {
          ...contour.input,
          fileMeta: action.payload.fileMeta,
          industry: action.payload.industry ?? contour.input.industry,
        },
        analysis: {
          snapshot: frozenSnapshot,
          frozenAt: nowIso,
        },
        auditTrail: [...contour.auditTrail, analysisEvent],
      };
      break;
    }

    case 'APPEND_ADVISORY': {
      const state = contour.lifecycle.state;
      // До анализа advisory недопустимы
      assertState(state, ['analysis_ready', 'decision_recorded'], 'APPEND_ADVISORY');

      // После фиксации решения допускаем только пояснительные advisory
      if (state === 'decision_recorded') {
        const t = action.payload.snapshot.type;
        const allowedTypes: AdvisorySnapshot['type'][] = ['decision_implications', 'board_summary'];
        if (!allowedTypes.includes(t)) {
          throw new Error('[DecisionContour] Only explanatory advisory allowed after decision_recorded');
        }
      }

      const advisoryEvent: DecisionContourAuditEvent = {
        eventId: `${contour.contourId}_advisory_generated_${Date.now()}`,
        timestamp: action.payload.snapshot.generatedAt,
        type: 'advisory_generated',
        actor: {
          type: 'system',
        },
        snapshotRef: action.payload.snapshot.advisoryId,
      };

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          updatedAt: action.payload.snapshot.generatedAt,
        },
        advisory: [...(contour.advisory ?? []), action.payload.snapshot],
        auditTrail: [...contour.auditTrail, advisoryEvent],
      };
      break;
    }

    case 'RECORD_DECISION': {
      assertState(contour.lifecycle.state, ['analysis_ready'], 'RECORD_DECISION');
      if (!contour.analysis) {
        throw new Error('[DecisionContour] Cannot record decision without frozen analysis');
      }
      if (contour.decision) {
        throw new Error('[DecisionContour] Decision is immutable and already recorded');
      }

      const frozenDecision = Object.freeze({ ...(action.payload.decision as UserDecision) });

      const decisionEvent: DecisionContourAuditEvent = {
        eventId: `${contour.contourId}_decision_recorded_${Date.now()}`,
        timestamp: action.payload.decision.timestamp,
        type: 'decision_recorded',
        actor: {
          type: 'user',
          role: action.payload.role,
        },
        snapshotRef: 'decision',
      };

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          state: 'decision_recorded',
          updatedAt: action.payload.decision.timestamp,
        },
        decision: frozenDecision,
        auditTrail: [...contour.auditTrail, decisionEvent],
      };
      break;
    }

    case 'ABANDON_CONTOUR': {
      // Нельзя отменить уже зафиксированное решение
      if (contour.lifecycle.state === 'decision_recorded') {
        throw new Error('[DecisionContour] Cannot abandon contour after decision_recorded');
      }

      const abandonEvent: DecisionContourAuditEvent = {
        eventId: `${contour.contourId}_decision_abandoned_${Date.now()}`,
        timestamp: nowIso,
        type: 'decision_abandoned',
        actor: {
          type: 'user',
          role: action.payload?.role,
        },
        snapshotRef: 'contour',
      };

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          state: 'abandoned',
          updatedAt: nowIso,
        },
        auditTrail: [...contour.auditTrail, abandonEvent],
      };
      break;
    }

    case 'REGISTER_EXPORT': {
      assertState(contour.lifecycle.state, ['decision_recorded'], 'REGISTER_EXPORT');
      if (!contour.analysis) {
        throw new Error('[DecisionContour] Cannot register export without frozen analysis');
      }
      if (!contour.decision) {
        throw new Error('[DecisionContour] Cannot register export without recorded decision');
      }

      const exportEvent: DecisionContourAuditEvent = {
        eventId: `${contour.contourId}_export_generated_${Date.now()}`,
        timestamp: action.payload.exportSnapshot.generatedAt,
        type: 'export_generated',
        actor: {
          type: 'user',
          role: action.payload.role,
        },
        snapshotRef: action.payload.exportSnapshot.exportId,
      };

      updated = {
        ...contour,
        lifecycle: {
          ...contour.lifecycle,
          updatedAt: action.payload.exportSnapshot.generatedAt,
        },
        exports: [...(contour.exports ?? []), action.payload.exportSnapshot],
        auditTrail: [...contour.auditTrail, exportEvent],
      };
      break;
    }

    default: {
      const neverAction: never = action;
      throw new Error(`[DecisionContour] Unsupported action: ${(neverAction as any).type}`);
    }
  }

  // --- Инварианты ---
  assertInvariant(
    updated.decision ? updated.lifecycle.state === 'decision_recorded' : true,
    'Decision must only exist in decision_recorded state',
  );

  assertInvariant(
    updated.analysis ? updated.lifecycle.state !== 'draft' : true,
    'Analysis snapshot cannot exist in draft state',
  );

  return updated;
};

// --- Export Engine ---

// Простейший хеш для референсов (placeholder, можно заменить на crypto.subtle)
const simpleHash = (input: string): string => {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = (hash * 31 + input.charCodeAt(i)) | 0;
  }
  return String(Math.abs(hash));
};

interface RequestExportResult {
  contour: DecisionContour;
  exportSnapshot: ExportSnapshot;
}

/**
 * Запрашивает экспорт как следствие зафиксированного решения.
 * Проверяет права доступа на уровне state engine, создаёт ExportSnapshot,
 * регистрирует его в контуре, и только после этого разрешает генерацию файла.
 *
 * @throws Error если контур не в состоянии decision_recorded или отсутствует решение/анализ
 */
export const requestExport = (
  contourId: string,
  exportType: ExportType,
  format: 'pdf' | 'xlsx' | 'txt',
  role?: string,
): RequestExportResult => {
  const contour = loadDecisionContour(contourId);
  if (!contour) {
    throw new Error(`[ExportEngine] Contour ${contourId} not found`);
  }

  // Проверка на уровне state engine (не UI)
  if (contour.lifecycle.state !== 'decision_recorded') {
    throw new Error(
      `[ExportEngine] Export is only available after decision is recorded. Current state: ${contour.lifecycle.state}`,
    );
  }

  if (!contour.analysis) {
    throw new Error('[ExportEngine] Cannot export without frozen analysis snapshot');
  }

  if (!contour.decision) {
    throw new Error('[ExportEngine] Cannot export without recorded decision');
  }

  const nowIso = new Date().toISOString();
  const exportId = `${contourId}_${exportType}_${Date.now()}`;

  // Создаём хеши для референсов
  const analysisRefHash = simpleHash(JSON.stringify(contour.analysis.snapshot));
  const advisoryRefs = (contour.advisory ?? []).map((a) => a.advisoryId);

  // contentHash будет вычислен после генерации контента (placeholder пока)
  const contentHash = simpleHash(`${exportId}_${nowIso}`);

  const exportSnapshot: ExportSnapshot = {
    exportId,
    contourId,
    exportType,
    generatedAt: nowIso,
    decisionRef: contour.decision,
    analysisRefHash,
    advisoryRefs,
    format,
    contentHash,
  };

  // Регистрируем экспорт в контуре (через rule engine)
  const updatedContour = updateDecisionContour(contour, {
    type: 'REGISTER_EXPORT',
    payload: {
      exportSnapshot,
      role,
    },
  });

  // Сохраняем обновлённый контур
  saveDecisionContour(updatedContour);

  return {
    contour: updatedContour,
    exportSnapshot,
  };
};










































