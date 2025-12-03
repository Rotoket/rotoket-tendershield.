/**
 * Модальное окно с предложением регистрации
 * Контекстные триггеры для конверсии
 */

import React from 'react';
import { X, Check, FileText, Share2, Download } from 'lucide-react';

interface RegisterSuggestionProps {
  type: 'after_analysis' | 'export_pdf' | 'view_history';
  onRegister: () => void;
  onDismiss: () => void;
  visible: boolean;
}

const suggestions = {
  after_analysis: {
    title: '🎉 Анализ готов!',
    message: 'Сохраните результаты в личный кабинет',
    benefits: [
      { icon: FileText, text: 'Хранить все анализы' },
      { icon: Download, text: 'Экспортировать в PDF' },
      { icon: Share2, text: 'Делиться с коллегами' },
    ],
  },
  export_pdf: {
    title: '📄 Экспорт доступен!',
    message: 'Зарегистрируйтесь для экспорта анализов',
    benefits: [
      { icon: Download, text: 'PDF с вашей символикой' },
      { icon: FileText, text: 'Excel таблицы' },
      { icon: Share2, text: 'Отправка по email' },
    ],
  },
  view_history: {
    title: '📋 История анализов',
    message: 'Все анализы сохраняются в личном кабинете',
    benefits: [
      { icon: FileText, text: 'Доступ с любого устройства' },
      { icon: Check, text: 'Поиск по результатам' },
      { icon: Share2, text: 'Сравнение анализов' },
    ],
  },
};

export const RegisterSuggestionModal: React.FC<RegisterSuggestionProps> = ({
  type,
  onRegister,
  onDismiss,
  visible,
}) => {
  if (!visible) return null;

  const suggestion = suggestions[type];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6 relative">
        <button
          onClick={onDismiss}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="text-2xl font-bold mb-2">{suggestion.title}</h3>
        <p className="text-gray-600 mb-6">{suggestion.message}</p>

        <ul className="space-y-3 mb-6">
          {suggestion.benefits.map((benefit, i) => {
            const Icon = benefit.icon;
            return (
              <li key={i} className="flex items-center gap-3 text-gray-700">
                <Icon className="w-5 h-5 text-green-500" />
                <span>{benefit.text}</span>
              </li>
            );
          })}
        </ul>

        <div className="flex gap-3">
          <button
            className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg"
            onClick={onRegister}
          >
            Зарегистрироваться
          </button>
          <button
            className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
            onClick={onDismiss}
          >
            Позже
          </button>
        </div>
      </div>
    </div>
  );
};

