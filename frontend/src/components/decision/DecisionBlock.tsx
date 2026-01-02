import React, { useEffect, useState } from 'react';
import { logEvent } from '../../utils/logger';
import { VerdictType } from '../../types';
import { getCurrentTenderVersion, recomputeDecisionActuality, isDecisionOutdated } from '../../utils/tenderVersioning';

export type UserDecision =
  | 'participate'
  | 'participate_with_conditions'
  | 'do_not_participate'
  | 'postpone';

export interface DecisionData {
  decision: UserDecision;
  comment?: string;
  timestamp: string;
}

interface DecisionBlockProps {
  verdict: VerdictType;
  dealBreakersCount: number;
  onDecision: (decision: DecisionData) => void;
  // Опционально: если решение уже зафиксировано, показываем только статус
  fixedDecision?: UserDecision;
  fixedAt?: string; // ISO timestamp из backend
  fixedComment?: string; // Комментарий директора из backend
  /** Кто принял решение (для аудита) */
  fixedBy?: string; // Имя пользователя или email
  /** Версия анализа (для аудита) */
  analysisVersion?: string;
  /** Требуется ли авторизация для фиксации решения */
  requiresAuth?: boolean;
}

interface DecisionButtonProps {
  label: string;
  type: UserDecision;
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
  variant: 'danger' | 'warning' | 'success' | 'neutral';
}

const DecisionButton: React.FC<DecisionButtonProps> = ({
  label,
  type,
  selected,
  disabled,
  onClick,
  variant,
}) => {
  const baseClasses = 'px-6 py-3 rounded-lg text-sm font-bold transition-all border-2';
  
  const variantClasses = {
    danger: selected
      ? 'bg-red-500/20 border-red-500 text-red-300 shadow-lg shadow-red-500/20'
      : 'bg-[#020617] border-red-500/40 text-red-400 hover:bg-red-500/10 hover:border-red-500/60',
    warning: selected
      ? 'bg-yellow-500/20 border-yellow-500 text-yellow-300 shadow-lg shadow-yellow-500/20'
      : 'bg-[#020617] border-yellow-500/40 text-yellow-400 hover:bg-yellow-500/10 hover:border-yellow-500/60',
    success: selected
      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-lg shadow-emerald-500/20'
      : 'bg-[#020617] border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 hover:border-emerald-500/60',
    neutral: selected
      ? 'bg-[#1e293b] border-[#38bdf8] text-slate-50 shadow-lg shadow-cyan-500/20'
      : 'bg-[#020617] border-[#1f2937] text-slate-300 hover:bg-[#020617]/80 hover:border-[#334155]',
  };

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`${baseClasses} ${variantClasses[variant]} ${
        disabled && !selected ? 'opacity-50 cursor-not-allowed' : ''
      }`}
    >
      {label}
    </button>
  );
};

const DecisionBlock: React.FC<DecisionBlockProps> = ({
  verdict,
  dealBreakersCount,
  onDecision,
  fixedDecision,
  fixedAt: fixedAtProp,
  fixedComment,
  fixedBy,
  analysisVersion,
  requiresAuth = false,
  tenderId,
}) => {
  const [selected, setSelected] = useState<UserDecision | null>(fixedDecision || null);
  const [comment, setComment] = useState(fixedComment || '');
  const [fixedAt, setFixedAt] = useState<string | null>(fixedAtProp || null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [outdated, setOutdated] = useState(false);

  // Если решение уже зафиксировано извне (из backend), показываем только статус (read-only)
  const isDecisionFixed = !!fixedDecision;

  // Проверяем актуальность решения относительно текущей версии тендера (если известен tenderId)
  useEffect(() => {
    if (!tenderId) return;
    const currentVersion = getCurrentTenderVersion(tenderId);
    // Пересчитываем актуальность всех решений по этому тендеру
    recomputeDecisionActuality(tenderId, currentVersion);
    const isOutdated = isDecisionOutdated(tenderId);
    setOutdated(isOutdated);
  }, [tenderId]);

  const handleSelect = (decision: UserDecision) => {
    if (isDecisionFixed) {
      // Решение уже зафиксировано, повторный выбор блокируем
      return;
    }

    setSelected(decision);

    // Если требуется авторизация, вызываем onDecision (который должен перевести к авторизации)
    if (requiresAuth) {
      // Для отказа все равно требуем комментарий, даже если требуется авторизация
      if (decision === 'do_not_participate' && !comment.trim()) {
        return; // Не вызываем onDecision, пока нет комментария
      }
      onDecision({
        decision,
        comment: comment.trim() || undefined,
        timestamp: new Date().toISOString(),
      });
      return;
    }

    // Для отказа требуем явный комментарий
    if (decision === 'do_not_participate' && !comment.trim()) {
      // Не блокируем выбор, но не даем зафиксировать без комментария
      return;
    }

    // Если есть deal breakers и пользователь выбирает "Участвовать" — требуем подтверждение
    if (decision === 'participate' && dealBreakersCount > 0) {
      const confirmed = window.confirm(
        'В анализе обнаружены критические стоп-факторы. Вы уверены, что хотите участвовать в тендере?'
      );
      if (!confirmed) {
        setSelected(null);
        return;
      }
    }
  };

  const handleSubmit = () => {
    if (!selected) {
      return;
    }

    // Для отказа комментарий обязателен
    if (selected === 'do_not_participate' && !comment.trim()) {
      alert('Для решения "Не участвовать" требуется краткий комментарий с указанием причины отказа.');
      return;
    }

    setIsSubmitting(true);
    const timestamp = new Date().toISOString();
    setFixedAt(timestamp);

    const decisionData: DecisionData = {
      decision: selected,
      comment: comment.trim() || undefined,
      timestamp,
    };

    logEvent('Decision', `Пользователь принял решение: ${selected}`, 'info');
    onDecision(decisionData);
    
    // Сбрасываем состояние отправки через небольшую задержку (для анимации)
    setTimeout(() => {
      setIsSubmitting(false);
    }, 500);
  };

  // Динамический подзаголовок
  const subtitle =
    dealBreakersCount > 0
      ? 'Обнаружены критические стоп-факторы или жёсткие условия. Участие требует осознанного решения.'
      : 'Критических стоп-факторов не выявлено. Решение принимается на основе стратегии компании.';

  // Две основные симметричные кнопки
  const primaryButtons: DecisionButtonProps[] = [
    {
      label: 'Участвовать',
      type: 'participate',
      selected: selected === 'participate',
      onClick: () => handleSelect('participate'),
      variant: 'success',
      disabled: requiresAuth || isDecisionFixed,
    },
    {
      label: 'Не участвовать',
      type: 'do_not_participate',
      selected: selected === 'do_not_participate',
      onClick: () => handleSelect('do_not_participate'),
      variant: 'danger',
      disabled: requiresAuth || isDecisionFixed,
    },
  ];

  // Дополнительные опции (скрыты по умолчанию, можно развернуть)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const advancedButtons: DecisionButtonProps[] = [
    {
      label: 'Участвовать с условиями',
      type: 'participate_with_conditions',
      selected: selected === 'participate_with_conditions',
      onClick: () => handleSelect('participate_with_conditions'),
      variant: 'warning',
      disabled: requiresAuth || verdict === 'STOP' || isDecisionFixed,
    },
    {
      label: 'Отложить решение',
      type: 'postpone',
      selected: selected === 'postpone',
      onClick: () => handleSelect('postpone'),
      variant: 'neutral',
      disabled: requiresAuth || isDecisionFixed,
    },
  ];

  const getDecisionLabel = (decision: UserDecision): string => {
    switch (decision) {
      case 'participate':
        return 'Участвовать';
      case 'participate_with_conditions':
        return 'Участвовать с условиями';
      case 'do_not_participate':
        return 'Не участвовать';
      case 'postpone':
        return 'Отложить решение';
      default:
        return decision;
    }
  };

  // Проверяем, можно ли зафиксировать решение
  const canSubmit =
    selected &&
    !isDecisionFixed &&
    !outdated &&
    (selected !== 'do_not_participate' || comment.trim().length > 0);

  return (
    <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-6" data-section="decision-block">
      <h3 className="text-sm font-bold uppercase text-slate-400 mb-2">
        Фиксация управленческого решения
      </h3>

      <p className="text-sm text-slate-300 mb-2">
        {subtitle}
      </p>
      {outdated && (
        <p className="text-xs text-amber-400 mb-3">
          ⚠ Зафиксированное или подготавливаемое решение основано на предыдущей версии документации.
          Для продолжения требуется актуализация анализа.
        </p>
      )}
      <p className="text-xs text-slate-500 mb-6">
        Система проводит аналитическую оценку. Ниже фиксируется выбор директора для внутреннего контроля и истории.
      </p>

      {!isDecisionFixed ? (
        <>
          {/* Две основные симметричные кнопки */}
          <div className="flex flex-wrap gap-4 mb-4">
            {primaryButtons.map((btn) => (
              <DecisionButton
                key={btn.type}
                label={btn.label}
                type={btn.type}
                selected={btn.selected}
                disabled={btn.disabled}
                onClick={btn.onClick}
                variant={btn.variant}
              />
            ))}
          </div>

          {/* Дополнительные опции (опционально) */}
          <div className="mb-4">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="text-xs text-slate-400 hover:text-slate-300 underline"
            >
              {showAdvanced ? 'Скрыть дополнительные опции' : 'Показать дополнительные опции'}
            </button>
            {showAdvanced && (
              <div className="flex flex-wrap gap-3 mt-2">
                {advancedButtons.map((btn) => (
                  <DecisionButton
                    key={btn.type}
                    label={btn.label}
                    type={btn.type}
                    selected={btn.selected}
                    disabled={btn.disabled}
                    onClick={btn.onClick}
                    variant={btn.variant}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Комментарий */}
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-400 mb-2">
              Комментарий к решению
              {selected === 'do_not_participate' && (
                <span className="text-red-400 ml-1">*</span>
              )}
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={
                selected === 'do_not_participate'
                  ? 'Укажите причину решения или условия, при которых участие возможно…'
                  : 'Опишите причины решения или условия участия…'
              }
              disabled={requiresAuth || isDecisionFixed}
              className="w-full px-3 py-2 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#38bdf8] disabled:opacity-50 disabled:cursor-not-allowed resize-none"
              rows={3}
            />
            {selected === 'do_not_participate' && !comment.trim() && (
              <p className="text-red-400 text-xs mt-1">
                Комментарий обязателен для решения "Не участвовать"
              </p>
            )}
            {selected && selected !== 'do_not_participate' && (
              <p className="text-[10px] text-slate-500 mt-1">
                Комментарий необязателен, но полезен для истории и команды
              </p>
            )}
          </div>

          {/* Кнопка фиксации */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit || requiresAuth || isSubmitting || outdated}
            className="w-full bg-gradient-to-r from-[#00d4ff] to-[#0099cc] text-[#0f1419] font-bold py-3 rounded-lg hover:shadow-[0_0_20px_rgba(0,212,255,0.4)] transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Фиксируем...' : outdated ? 'Актуализируйте анализ' : 'Зафиксировать решение'}
          </button>
        </>
      ) : (
        // Read-only режим: решение зафиксировано
        <div className="space-y-4">
          <div className="bg-[#020617] border border-[#1f2937] rounded-xl p-4 space-y-3">
            <p className="text-sm font-semibold text-white">
              Решение зафиксировано и не может быть изменено
            </p>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-slate-400">Решение:&nbsp;</span>
                <span className="text-white font-medium">{getDecisionLabel(fixedDecision!)}</span>
              </div>
              {fixedBy && (
                <div>
                  <span className="text-slate-400">Принял:&nbsp;</span>
                  <span className="text-white">{fixedBy}</span>
                </div>
              )}
              {fixedAt && (
                <div>
                  <span className="text-slate-400">Дата и время:&nbsp;</span>
                  <span className="text-white">
                    {new Date(fixedAt).toLocaleString('ru-RU', {
                      day: '2-digit',
                      month: '2-digit',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
              )}
              {analysisVersion && (
                <div>
                  <span className="text-slate-400">Версия анализа:&nbsp;</span>
                  <span className="text-white">{analysisVersion}</span>
                </div>
              )}
              {fixedComment && (
                <div className="pt-2 border-t border-[#1f2937]">
                  <p className="text-slate-400 mb-1">Комментарий директора:</p>
                  <p className="text-white whitespace-pre-line">{fixedComment}</p>
                </div>
              )}
            </div>
          </div>
          <p className="text-xs text-slate-500 text-center">
            После фиксации решения стали доступны экспорт отчётов, Board Pack и протоколы.
          </p>
        </div>
      )}
    </div>
  );
};

export default DecisionBlock;
