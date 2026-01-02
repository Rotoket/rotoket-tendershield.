/**
 * Kill Switch Banner — ШАГ 13
 * 
 * Отображает информацию о режиме работы системы (NORMAL, SAFE, LOCKDOWN).
 */

import React from 'react';
import { AlertTriangle, Shield, Lock } from 'lucide-react';

interface KillSwitchStatus {
  mode: 'NORMAL' | 'SAFE' | 'LOCKDOWN';
  is_active: boolean;
  last_activation?: {
    id: string;
    timestamp: string;
    reason: string;
  };
  kill_switch_enabled?: boolean;
}

interface KillSwitchBannerProps {
  status: KillSwitchStatus | null;
  className?: string;
}

const KillSwitchBanner: React.FC<KillSwitchBannerProps> = ({ status, className = '' }) => {
  if (!status || !status.is_active || status.mode === 'NORMAL') {
    return null;
  }

  const getModeConfig = () => {
    switch (status.mode) {
      case 'SAFE':
        return {
          icon: Shield,
          bgColor: 'bg-[#f59e0b]/20',
          borderColor: 'border-[#f59e0b]',
          textColor: 'text-[#f59e0b]',
          title: 'Безопасный режим',
          message: 'Reasoning временно отключён. Система работает в безопасном режиме. Новые управленческие выводы не формируются.',
        };
      case 'LOCKDOWN':
        return {
          icon: Lock,
          bgColor: 'bg-[#ef4444]/20',
          borderColor: 'border-[#ef4444]',
          textColor: 'text-[#ef4444]',
          title: 'Режим блокировки',
          message: 'Система в режиме блокировки. Новые анализы и решения запрещены. Доступен только просмотр истории (Audit Trail).',
        };
      default:
        return null;
    }
  };

  const config = getModeConfig();
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div
      className={`${config.bgColor} ${config.borderColor} border-l-4 rounded-lg p-4 mb-6 ${className}`}
    >
      <div className="flex items-start gap-3">
        <Icon size={24} className={`${config.textColor} flex-shrink-0 mt-0.5`} />
        <div className="flex-1">
          <h3 className={`${config.textColor} font-semibold text-lg mb-1`}>
            {config.title}
          </h3>
          <p className="text-slate-300 text-sm leading-relaxed mb-2">
            {config.message}
          </p>
          {status.last_activation && (
            <div className="mt-3 pt-3 border-t border-slate-600/50">
              <p className="text-slate-400 text-xs">
                <span className="font-medium">Активация:</span>{' '}
                {new Date(status.last_activation.timestamp).toLocaleString('ru-RU')}
              </p>
              <p className="text-slate-400 text-xs mt-1">
                <span className="font-medium">Причина:</span>{' '}
                {status.last_activation.reason}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default KillSwitchBanner;































