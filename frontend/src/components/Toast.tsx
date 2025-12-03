import React, { useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastProps {
    toast: Toast;
    onClose: (id: string) => void;
}

const ToastComponent: React.FC<ToastProps> = ({ toast, onClose }) => {
    useEffect(() => {
        const duration = toast.duration || 5000;
        const timer = setTimeout(() => {
            onClose(toast.id);
        }, duration);

        return () => clearTimeout(timer);
    }, [toast.id, toast.duration, onClose]);

    const icons = {
        success: CheckCircle,
        error: XCircle,
        warning: AlertCircle,
        info: Info
    };

    const colors = {
        success: 'bg-green-500/20 border-green-500/50 text-green-400',
        error: 'bg-red-500/20 border-red-500/50 text-red-400',
        warning: 'bg-yellow-500/20 border-yellow-500/50 text-yellow-400',
        info: 'bg-blue-500/20 border-blue-500/50 text-blue-400'
    };

    const Icon = icons[toast.type];

    return (
        <div
            className={`flex items-center gap-3 p-4 rounded-lg border ${colors[toast.type]} shadow-lg backdrop-blur-sm animate-in slide-in-from-right`}
        >
            <Icon className="w-5 h-5 flex-shrink-0" />
            <p className="flex-1 text-sm font-medium">{toast.message}</p>
            <button
                onClick={() => onClose(toast.id)}
                className="flex-shrink-0 hover:opacity-70 transition-opacity"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

interface ToastContainerProps {
    toasts: Toast[];
    onClose: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onClose }) => {
    if (toasts.length === 0) return null;

    return (
        <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
            {toasts.map(toast => (
                <ToastComponent key={toast.id} toast={toast} onClose={onClose} />
            ))}
        </div>
    );
};

// Хук для управления уведомлениями
export const useToast = () => {
    const [toasts, setToasts] = React.useState<Toast[]>([]);

    const showToast = (type: ToastType, message: string, duration?: number) => {
        const id = Date.now().toString() + Math.random().toString(36).substr(2, 9);
        setToasts(prev => [...prev, { id, type, message, duration }]);
    };

    const removeToast = (id: string) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    };

    const ToastComponent = () => (
        <ToastContainer toasts={toasts} onClose={removeToast} />
    );

    return { showToast, ToastComponent };
};
