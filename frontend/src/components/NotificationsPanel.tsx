import React, { useState, useEffect } from 'react';
import { Bell, X, AlertTriangle, AlertCircle, Info, CheckCircle, TrendingUp } from 'lucide-react';
import { getAuthHeaders } from '../services/authService';

interface Notification {
  type: 'warning' | 'critical' | 'error' | 'info' | 'success';
  title: string;
  message: string;
  action?: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
}

const API_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000/api';

export const NotificationsPanel: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadNotifications();
    // Обновляем каждые 5 минут
    const interval = setInterval(loadNotifications, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${API_URL}/notifications`, {
        headers: {
          ...getAuthHeaders(),
        },
      });

      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      }
    } catch (error) {
      console.error('Error loading notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'critical':
      case 'error':
        return AlertTriangle;
      case 'warning':
        return AlertCircle;
      case 'success':
        return CheckCircle;
      default:
        return Info;
    }
  };

  const getColor = (type: string) => {
    switch (type) {
      case 'critical':
      case 'error':
        return 'border-red-500/50 bg-red-500/10 text-red-400';
      case 'warning':
        return 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400';
      case 'success':
        return 'border-green-500/50 bg-green-500/10 text-green-400';
      default:
        return 'border-blue-500/50 bg-blue-500/10 text-blue-400';
    }
  };

  const unreadCount = notifications.length;

  if (unreadCount === 0 && !isOpen) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-3 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-[#00d4ff] hover:bg-[#2a3441] transition-colors"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute top-14 right-0 w-96 bg-[#1a1f2e] border border-[#2a3441] rounded-xl shadow-xl max-h-[600px] overflow-y-auto">
          <div className="p-4 border-b border-[#2a3441] flex items-center justify-between">
            <h3 className="text-white font-bold">Уведомления</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-slate-400 hover:text-white"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-2">
            {isLoading ? (
              <div className="text-center py-8 text-slate-400">Загрузка...</div>
            ) : notifications.length === 0 ? (
              <div className="text-center py-8 text-slate-400">Нет уведомлений</div>
            ) : (
              notifications.map((notification, index) => {
                const Icon = getIcon(notification.type);
                return (
                  <div
                    key={index}
                    className={`p-4 mb-2 rounded-lg border ${getColor(notification.type)}`}
                  >
                    <div className="flex items-start gap-3">
                      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <h4 className="font-bold text-sm mb-1">{notification.title}</h4>
                        <p className="text-sm opacity-90">{notification.message}</p>
                        {notification.action && (
                          <button className="mt-2 text-xs font-bold hover:opacity-80 transition-opacity">
                            {notification.action === 'upgrade' && 'Обновить тариф →'}
                            {notification.action === 'subscribe' && 'Выбрать тариф →'}
                            {notification.action === 'analyze' && 'Проанализировать →'}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};

