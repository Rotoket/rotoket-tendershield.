import React, { useState, useEffect } from 'react';
import { ProgressBar } from './ProgressBar';
import { Loader2 } from 'lucide-react';

interface AnalysisProgressProps {
    isAnalyzing: boolean;
    currentStep: string;
    progress: number;
    steps: string[];
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
    isAnalyzing,
    currentStep,
    progress,
    steps
}) => {
    const [displayedSteps, setDisplayedSteps] = useState<string[]>([]);

    useEffect(() => {
        if (isAnalyzing && currentStep) {
            // Добавляем текущий шаг, если его еще нет
            if (!displayedSteps.includes(currentStep)) {
                setDisplayedSteps(prev => [...prev, currentStep]);
            }
        } else if (!isAnalyzing) {
            // Очищаем при завершении
            setDisplayedSteps([]);
        }
    }, [isAnalyzing, currentStep, displayedSteps]);

    if (!isAnalyzing) {
        return null;
    }

    return (
        <div className="bg-gray-800/50 rounded-lg p-4 mb-4 border border-gray-700">
            <div className="flex items-center gap-3 mb-3">
                <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                <h3 className="text-lg font-semibold text-white">Анализ в процессе...</h3>
            </div>
            
            <ProgressBar
                progress={progress}
                showPercentage={true}
                color="primary"
                animated={true}
            />
            
            {currentStep && (
                <p className="text-sm text-gray-400 mt-3">{currentStep}</p>
            )}
            
            {displayedSteps.length > 0 && (
                <div className="mt-4 space-y-2">
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Выполненные шаги:</p>
                    <ul className="space-y-1">
                        {displayedSteps.map((step, index) => (
                            <li key={index} className="text-sm text-gray-400 flex items-center gap-2">
                                <span className="text-green-500">✓</span>
                                <span>{step}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

