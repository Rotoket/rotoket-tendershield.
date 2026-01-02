import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  children: React.ReactNode;
  content: string;
  side?: 'top' | 'bottom' | 'left' | 'right';
}

/**
 * Простой Tooltip компонент для канонических текстов UI CANON.
 * Используется только для фиксации принципов системы, не для обучения или подсказок.
 */
const Tooltip: React.FC<TooltipProps> = ({ children, content, side = 'top' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const [actualSide, setActualSide] = useState<'top' | 'bottom' | 'left' | 'right'>(side);
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const updatePosition = () => {
    if (!triggerRef.current) return;
    
    const rect = triggerRef.current.getBoundingClientRect();
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Используем реальные размеры тултипа, если он уже отрендерен
    const tooltipElement = tooltipRef.current;
    let tooltipHeight = 250;
    let tooltipWidth = 320;
    
    if (tooltipElement) {
      const tooltipRect = tooltipElement.getBoundingClientRect();
      tooltipHeight = tooltipRect.height;
      tooltipWidth = tooltipRect.width;
    }

    let top = 0;
    let left = 0;
    let newActualSide = side;

    // Определяем оптимальную сторону с учётом границ экрана
    if (side === 'top' || side === 'bottom') {
      const spaceAbove = rect.top;
      const spaceBelow = viewportHeight - rect.bottom;
      
      if (side === 'top') {
        // Если сверху недостаточно места, показываем снизу
        if (spaceAbove < tooltipHeight + 20 && spaceBelow > spaceAbove) {
          newActualSide = 'bottom';
          top = rect.bottom + scrollY + 8;
        } else {
          top = rect.top + scrollY - 8;
        }
      } else {
        // Если снизу недостаточно места, показываем сверху
        if (spaceBelow < tooltipHeight + 20 && spaceAbove > spaceBelow) {
          newActualSide = 'top';
          top = rect.top + scrollY - 8;
        } else {
          top = rect.bottom + scrollY + 8;
        }
      }
      
      left = rect.left + scrollX + rect.width / 2;
      
      // Корректируем горизонтальную позицию, чтобы не выходить за границы
      const tooltipHalfWidth = tooltipWidth / 2;
      if (left - tooltipHalfWidth < 10) {
        left = tooltipHalfWidth + 10;
      } else if (left + tooltipHalfWidth > viewportWidth - 10) {
        left = viewportWidth - tooltipHalfWidth - 10;
      }
    } else {
      // Для left/right используем исходную логику
      switch (side) {
        case 'left':
          top = rect.top + scrollY + rect.height / 2;
          left = rect.left + scrollX - 8;
          break;
        case 'right':
          top = rect.top + scrollY + rect.height / 2;
          left = rect.right + scrollX + 8;
          break;
      }
    }

    setPosition({ top, left });
    setActualSide(newActualSide);
  };

  useEffect(() => {
    if (isVisible) {
      // Первый расчёт сразу
      updatePosition();
      
      // Повторный расчёт после рендера тултипа для точных размеров
      const timer = setTimeout(() => {
        updatePosition();
      }, 10);
      
      window.addEventListener('scroll', updatePosition);
      window.addEventListener('resize', updatePosition);
      return () => {
        clearTimeout(timer);
        window.removeEventListener('scroll', updatePosition);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isVisible, side]);

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-[#1F2933]',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-[#1F2933]',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-[#1F2933]',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-[#1F2933]',
  };

  const transformClasses = {
    top: '-translate-x-1/2 -translate-y-full',
    bottom: '-translate-x-1/2',
    left: '-translate-x-full -translate-y-1/2',
    right: '-translate-y-1/2',
  };

  return (
    <>
      <div
        ref={triggerRef}
        className="inline-block"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
      >
        {children}
      </div>
      {isVisible && typeof document !== 'undefined' && createPortal(
        <div
          ref={tooltipRef}
          className="fixed z-[99999] pointer-events-none"
          style={{
            top: `${position.top}px`,
            left: `${position.left}px`,
            transform: transformClasses[actualSide],
          }}
          role="tooltip"
        >
          <div className="bg-[#1F2933] border border-[#2A3441] rounded-[3px] px-4 py-3 max-w-[320px] text-sm text-slate-200 leading-relaxed shadow-lg whitespace-normal">
            {content}
          </div>
          <div
            className={`absolute w-0 h-0 border-4 border-transparent ${arrowClasses[actualSide]}`}
          />
        </div>,
        document.body
      )}
    </>
  );
};

export default Tooltip;

