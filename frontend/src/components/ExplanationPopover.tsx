import React, { useState, useEffect, useRef } from 'react';
import { Info, X, Loader2 } from 'lucide-react';
import { explainLegal, LegalExplainResponse } from '../services/mcpService';
import { logEvent } from '../utils/logger';

interface ExplanationPopoverProps {
  /** Текст вопроса для объяснения */
  question: string;
  /** Контекст (lawCode, pattern, term и т.д.) */
  context?: {
    lawCode?: string;
    pattern?: string;
    term?: string;
    [key: string]: any;
  };
  /** Источник блока для аналитики */
  sourceBlock: 'nmcd' | 'law' | 'penalty' | 'risk' | 'term' | 'pattern';
  /** Состояние контура для аналитики */
  contourState?: 'before_decision' | 'after_decision';
  /** Зафиксировано ли решение */
  decisionRecorded?: boolean;
  /** Дочерний элемент, к которому привязан popover */
  children: React.ReactNode;
  /** Позиция popover */
  position?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * Компонент для отображения объяснений через MCP.
 * 
 * ВАЖНО: Это read-only компонент, не влияет на анализ или решения.
 */
const ExplanationPopover: React.FC<ExplanationPopoverProps> = ({
  question,
  context,
  sourceBlock,
  contourState = 'before_decision',
  decisionRecorded = false,
  children,
  position = 'bottom',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [explanation, setExplanation] = useState<LegalExplainResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  // Закрытие при клике вне popover
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(event.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  // Загрузка объяснения при открытии
  useEffect(() => {
    if (isOpen && !explanation && !loading) {
      loadExplanation();
    }
  }, [isOpen]);

  const loadExplanation = async () => {
    setLoading(true);
    setError(null);

    try {
      // Логируем открытие объяснения
      logEvent('Explanation', 'explanation_opened', 'info', {
        source_block: sourceBlock,
        contour_state: contourState,
        decision_recorded: decisionRecorded,
        question: question.substring(0, 100),
      });

      const response = await explainLegal(question, context);
      setExplanation(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка загрузки объяснения';
      setError(errorMessage);
      logEvent('Explanation', 'explanation_error', 'error', {
        source_block: sourceBlock,
        error: errorMessage,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation();
    e.preventDefault();
    setIsOpen(!isOpen);
  };

  // Позиционирование popover
  const getPositionClasses = () => {
    switch (position) {
      case 'top':
        return 'bottom-full left-0 mb-2';
      case 'bottom':
        return 'top-full left-0 mt-2';
      case 'left':
        return 'right-full top-0 mr-2';
      case 'right':
        return 'left-full top-0 ml-2';
      default:
        return 'top-full left-0 mt-2';
    }
  };

  return (
    <div className="relative inline-block">
      {/* Триггер */}
      <div
        ref={triggerRef}
        onClick={handleToggle}
        className="inline-flex items-center gap-1 cursor-pointer text-slate-400 hover:text-[#00d4ff] transition-colors"
        title="Пояснить"
      >
        {children}
        <Info size={14} className="flex-shrink-0" />
      </div>

      {/* Popover */}
      {isOpen && (
        <div
          ref={popoverRef}
          className={`absolute z-50 ${getPositionClasses()} w-96 max-w-[calc(100vw-2rem)] bg-[#1a1f2e] border border-[#2a3441] rounded-xl shadow-xl`}
        >
          <div className="p-4">
            {/* Заголовок */}
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white">Что это значит</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors"
                aria-label="Закрыть"
              >
                <X size={16} />
              </button>
            </div>

            {/* Контент */}
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {loading && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 size={20} className="animate-spin text-[#00d4ff]" />
                  <span className="ml-2 text-sm text-slate-400">Загрузка...</span>
                </div>
              )}

              {error && (
                <div className="text-sm text-red-400">
                  {error}
                </div>
              )}

              {explanation && (
                <>
                  {/* Основное объяснение */}
                  <div className="text-sm text-slate-200 whitespace-pre-line">
                    {explanation.explanation}
                  </div>

                  {/* Источники (если есть) */}
                  {explanation.sources && explanation.sources.length > 0 && (
                    <div className="pt-2 border-t border-[#2a3441]">
                      <p className="text-xs text-slate-400 mb-1">Источники:</p>
                      <ul className="text-xs text-slate-500 space-y-1">
                        {explanation.sources.map((source, idx) => (
                          <li key={idx}>• {source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Дисклеймер (всегда видим) */}
            <div className="mt-4 pt-3 border-t border-[#2a3441]">
              <div className="flex items-start gap-2">
                <Info size={14} className="text-slate-400 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-slate-400">
                  {explanation?.disclaimer || 'Информация носит справочный характер и не является юридическим заключением.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplanationPopover;






































