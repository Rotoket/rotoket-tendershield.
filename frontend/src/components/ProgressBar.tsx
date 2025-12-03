import React from 'react';

interface ProgressBarProps {
    progress: number; // 0-100
    label?: string;
    showPercentage?: boolean;
    color?: 'primary' | 'success' | 'warning' | 'danger';
    animated?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
    progress,
    label,
    showPercentage = true,
    color = 'primary',
    animated = true
}) => {
    const clampedProgress = Math.min(100, Math.max(0, progress));
    
    const colorClasses = {
        primary: 'bg-blue-500',
        success: 'bg-green-500',
        warning: 'bg-yellow-500',
        danger: 'bg-red-500'
    };

    return (
        <div className="w-full">
            {label && (
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-300">{label}</span>
                    {showPercentage && (
                        <span className="text-sm text-gray-400">{Math.round(clampedProgress)}%</span>
                    )}
                </div>
            )}
            <div className="w-full bg-gray-700 rounded-full h-2.5 overflow-hidden">
                <div
                    className={`h-full ${colorClasses[color]} ${animated ? 'transition-all duration-300 ease-out' : ''}`}
                    style={{ width: `${clampedProgress}%` }}
                >
                    {animated && (
                        <div className="h-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                    )}
                </div>
            </div>
        </div>
    );
};

