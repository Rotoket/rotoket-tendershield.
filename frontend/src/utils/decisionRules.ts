import { UserDecision } from '../types';

export type ActionType = 'calculator' | 'generator' | 'generator_refusal' | 'generator_participation' | 'generator_protocol';

/**
 * Каноническая матрица доступа действий на основе решения пользователя
 * Эти правила — КАНОН. Не обсуждаются в коде.
 */
export const isActionAllowed = (
  decision: UserDecision | undefined,
  action: ActionType
): boolean => {
  // Если решение не зафиксировано - все действия запрещены
  if (!decision) {
    return false;
  }

  switch (decision.decision) {
    case 'do_not_participate':
      // Разрешено: калькулятор (для оценки потерь/выгоды), генерация отказа / протокола разногласий
      // Запрещено: генерация документов участия
      return action === 'calculator' || action === 'generator_refusal' || action === 'generator_protocol';

    case 'participate_with_conditions':
      // Разрешено: генератор документов (с пометкой "с условиями"), калькулятор, протокол разногласий
      return action === 'generator' || action === 'generator_participation' || action === 'generator_protocol' || action === 'calculator';

    case 'participate':
      // Разрешено: калькулятор, генератор документов участия
      // Запрещено: генерация отказа
      return action === 'calculator' || action === 'generator' || action === 'generator_participation';

    case 'postpone':
      // Разрешено: просмотр анализа, история
      // Запрещено: любые генерации, калькулятор
      return false;

    default:
      return false;
  }
};

/**
 * Получить сообщение о недоступности действия
 */
export const getActionBlockedMessage = (
  decision: UserDecision | undefined,
  action: ActionType
): string => {
  if (!decision) {
    return 'Сначала зафиксируйте решение';
  }

  switch (decision.decision) {
    case 'do_not_participate':
      if (action === 'generator_participation') {
        return 'Генерация документов участия недоступна при решении "Не участвовать"';
      }
      break;

    case 'postpone':
      return 'Действия недоступны при отложенном решении';

    default:
      break;
  }

  return 'Действие недоступно для текущего решения';
};

/**
 * Получить доступные действия для решения
 */
export const getAllowedActions = (decision: UserDecision | undefined): ActionType[] => {
  if (!decision) {
    return [];
  }

  const allActions: ActionType[] = [
    'calculator',
    'generator',
    'generator_refusal',
    'generator_participation',
    'generator_protocol',
  ];

  return allActions.filter(action => isActionAllowed(decision, action));
};













































