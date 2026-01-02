import type { UserRole } from '../types';

export type RoleAction =
  | 'upload_files'
  | 'run_analysis'
  | 'use_chat'
  | 'open_calculator'
  | 'view_deep_dive'
  | 'enter_director_mode'
  | 'generate_board_pack'
  | 'generate_compliance_export'
  | 'record_decision'
  | 'view_history'
  | 'view_director_mode';

export const can = (role: UserRole, action: RoleAction): boolean => {
  if (role === 'expert') {
    // Эксперт имеет полный доступ ко всем действиям (кроме будущих ограничений)
    return true;
  }

  // Роль director — жёсткие ограничения
  switch (action) {
    case 'record_decision':
    case 'generate_board_pack':
    case 'generate_compliance_export':
    case 'view_history':
    case 'view_director_mode':
      return true;
    default:
      return false;
  }
};













































