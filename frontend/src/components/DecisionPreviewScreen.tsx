import React, { useEffect } from 'react';
import { AlertTriangle, Lock } from 'lucide-react';
import type { AnalysisResult } from '../types';
import DecisionPreview from './audit/DecisionPreview';
import DecisionBlock, { type UserDecision } from './decision/DecisionBlock';
import { logEvent } from '../utils/logger';

interface DecisionPreviewScreenProps {
  result: AnalysisResult;
  /** Вызывается при попытке зафиксировать решение (требует авторизации) */
  onRequestFixDecision: () => void;
  /** Вызывается при фиксации решения (для авторизованных пользователей) */
  onDecisionChange?: (decision: UserDecision) => void;
  /** Зафиксированное решение (если есть) */
  fixedDecision?: UserDecision;
  /** Авторизован ли пользователь */
  isAuthenticated?: boolean;
}

/**
 * Экран первого вердикта с заблокированными кнопками решения.
 * Показывается после анализа, до авторизации.
 */
const DecisionPreviewScreen: React.FC<DecisionPreviewScreenProps> = ({
  result,
  onRequestFixDecision,
  onDecisionChange,
  fixedDecision,
  isAuthenticated = false,
}) => {
  useEffect(() => {
    logEvent('DecisionPreviewScreen', 'verdict_preview_viewed', 'info', {
      hasFixedDecision: !!fixedDecision,
      verdict: result.verdict,
      score: result.score,
    });
  }, [result.verdict, result.score, fixedDecision]);

  const hasDealBreakers = !!(result.deal_breakers && result.deal_breakers.length > 0);

  return (
    <div className="space-y-6">
      {/* Decision Preview — ориентация директора */}
      <DecisionPreview
        result={result}
        documentsCount={1}
        fixedDecision={fixedDecision ? {
          decision: fixedDecision.decision,
          timestamp: fixedDecision.timestamp,
          comment: fixedDecision.comment,
          user: undefined, // TODO: получить из user context
        } : undefined}
        onGoToDetails={() => {
          const detailsSection = document.querySelector('[data-section="details"]');
          if (detailsSection) {
            detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }}
        onGoToDecision={() => {
          const decisionSection = document.querySelector('[data-section="decision-block"]');
          if (decisionSection) {
            decisionSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        }}
      />

      {/* Decision Block с заблокированными кнопками */}
      <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6 space-y-4">
        <h3 className="text-sm font-bold uppercase text-slate-400 mb-2">
          Фиксация управленческого решения
        </h3>

        {/* Предупреждение о необходимости авторизации */}
        {!fixedDecision && (
          <div className="bg-[#020617] border border-[#4b5563] rounded-xl p-4 flex gap-3">
            <Lock className="text-[#f59e0b] flex-shrink-0 mt-0.5" size={20} />
            <div className="text-xs text-slate-300 space-y-1">
              <p className="font-semibold text-slate-200">
                Управленческое решение требует фиксации ответственности
              </p>
              <p>
                Для продолжения подтвердите доступ. Решение по тендеру фиксируется за конкретным лицом.
                Это требуется для отчётов, аудита и защиты репутации.
              </p>
            </div>
          </div>
        )}

        {/* DecisionBlock с заблокированными кнопками (если решение не зафиксировано) */}
        {!fixedDecision ? (
          <DecisionBlock
            verdict={result.verdict}
            dealBreakersCount={result.deal_breakers?.length ?? 0}
            fixedDecision={undefined}
            requiresAuth={!isAuthenticated}
            onDecision={(decisionData) => {
              if (!isAuthenticated) {
                // Заблокировано — вызываем onRequestFixDecision
                onRequestFixDecision();
              } else if (onDecisionChange) {
                // Пользователь авторизован, фиксируем решение
                onDecisionChange({
                  decision: decisionData.decision,
                  comment: decisionData.comment,
                  timestamp: decisionData.timestamp,
                });
              }
            }}
          />
        ) : (
          <DecisionBlock
            verdict={result.verdict}
            dealBreakersCount={result.deal_breakers?.length ?? 0}
            fixedDecision={fixedDecision.decision}
            fixedAt={fixedDecision.timestamp}
            fixedComment={fixedDecision.comment}
            fixedBy={fixedDecision.user}
            onDecision={() => {
              // Решение уже зафиксировано, ничего не делаем
            }}
          />
        )}

        {/* CTA для фиксации решения (если не зафиксировано) */}
        {!fixedDecision && (
          <div className="pt-4 border-t border-[#1f2937]">
            <button
              type="button"
              onClick={onRequestFixDecision}
              className="w-full px-6 py-3 rounded-lg bg-[#f97316] text-[#0f1419] font-bold text-sm hover:bg-[#ea580c] transition-colors"
            >
              Зафиксировать решение
            </button>
            <p className="text-xs text-slate-500 text-center mt-2">
              Действие необратимо
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DecisionPreviewScreen;

