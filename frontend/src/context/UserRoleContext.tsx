import React, { createContext, useContext, useEffect, useState } from 'react';
import type { UserRole } from '../types';
import { logEvent } from '../utils/logger';

interface UserRoleContextValue {
  role: UserRole;
  setRole: (role: UserRole) => void;
}

const UserRoleContext = createContext<UserRoleContextValue | undefined>(undefined);

const ROLE_STORAGE_KEY = 'user_role';

const getInitialRole = (): UserRole => {
  if (typeof window === 'undefined') return 'expert';
  try {
    const stored = localStorage.getItem(ROLE_STORAGE_KEY);
    if (stored === 'director' || stored === 'expert') {
      return stored;
    }
  } catch {
    // ignore
  }
  return 'expert';
};

export const UserRoleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [role, setRoleState] = useState<UserRole>(getInitialRole);

  const setRole = (next: UserRole) => {
    setRoleState(next);
    try {
      localStorage.setItem(ROLE_STORAGE_KEY, next);
    } catch {
      // ignore
    }
    logEvent('RBAC', 'role_changed', 'info', { role: next });
  };

  useEffect(() => {
    logEvent('RBAC', 'role_detected', 'info', { role });
  }, [role]);

  return (
    <UserRoleContext.Provider value={{ role, setRole }}>
      {children}
    </UserRoleContext.Provider>
  );
};

export const useUserRole = (): UserRoleContextValue => {
  const ctx = useContext(UserRoleContext);
  if (!ctx) {
    throw new Error('useUserRole must be used within UserRoleProvider');
  }
  return ctx;
};













































