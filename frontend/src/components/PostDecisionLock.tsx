import React from 'react';
import { CheckCircle, Lock, Calculator, FileText, Download, History } from 'lucide-react';
import { UserDecision } from '../types';

interface PostDecisionLockProps {
  decision: UserDecision;
  onActivateAccess: () => void;
  onBack?: () => void;
}

const PostDecisionLock: React.FC<PostDecisionLockProps> = ({
  decision,
  onActivateAccess,
  onBack,
}) => {
  const getDecisionLabel = (decision: UserDecision['decision']): string => {
    switch (decision) {
      case 'participate':
        return 'Участвовать';
      case 'participate_with_conditions':
        return 'Участвовать с условиями';
      case 'do_not_participate':
        return 'Не участвовать';
      case 'postpone':
        return 'Отложить решение';
      default:
        return decision;
    }
  };

  return (
    <div className="min-h-screen bg-[#0f1419] flex items-center justify-center p-8">
      <div className="max-w-2xl mx-auto text-center space-y-8">
        {/* Заголовок успеха */}
        <div className="space-y-4">
          <div className="w-20 h-20 rounded-full bg-emerald-500/20 border-4 border-emerald-500 flex items-center justify-center mx-auto">
            <CheckCircle size={48} className="text-emerald-400" />
          </div>
          <h1 className="text-3xl font-bold text-white">
            ✅ Решение зафиксировано
          </h1>
          <p className="text-lg text-slate-300">
            Изменить его будет невозможно
          </p>
        </div>

        {/* Информация о решении */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-xl p-6">
          <p className="text-sm text-slate-400 mb-2">Ваше решение:</p>
          <p className="text-xl font-bold text-white mb-2">
            {getDecisionLabel(decision.decision)}
          </p>
          {decision.comment && (
            <p className="text-sm text-slate-300 mt-3 italic">
              "{decision.comment}"
            </p>
          )}
          <p className="text-xs text-slate-500 mt-4">
            Зафиксировано: {new Date(decision.timestamp).toLocaleString('ru-RU')}
          </p>
        </div>

        {/* Разделитель */}
        <div className="border-t border-[#2a3441]"></div>

        {/* Блок про активацию доступа */}
        <div className="space-y-6">
          <div className="flex items-center justify-center gap-3">
            <Lock size={24} className="text-[#f59e0b]" />
            <h2 className="text-2xl font-bold text-white">
              Для продолжения работы требуется активировать доступ
            </h2>
          </div>

          <p className="text-slate-300 leading-relaxed">
            Анализ завершён, решение зафиксировано. Для использования инструментов
            принятия решений (расчёты, документы, отчёты) требуется активация доступа.
          </p>

          {/* Список доступных функций */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-lg p-4 flex items-center gap-3">
              <Calculator size={20} className="text-[#00d4ff]" />
              <span className="text-sm text-slate-300">Расчёт финансовых последствий</span>
            </div>
            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-lg p-4 flex items-center gap-3">
              <FileText size={20} className="text-[#00d4ff]" />
              <span className="text-sm text-slate-300">Генерация документов</span>
            </div>
            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-lg p-4 flex items-center gap-3">
              <Download size={20} className="text-[#00d4ff]" />
              <span className="text-sm text-slate-300">Экспорт для руководства</span>
            </div>
            <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-lg p-4 flex items-center gap-3">
              <History size={20} className="text-[#00d4ff]" />
              <span className="text-sm text-slate-300">История и аудит решений</span>
            </div>
          </div>

          {/* Кнопка активации */}
          <button
            onClick={onActivateAccess}
            className="w-full px-8 py-4 bg-[#00d4ff] hover:bg-[#00b3e0] text-[#0f1419] text-lg font-bold rounded-xl shadow-lg shadow-[#00d4ff]/30 transition-all"
          >
            Активировать защиту решений
          </button>

          {onBack && (
            <button
              onClick={onBack}
              className="text-sm text-slate-400 hover:text-slate-300 underline"
            >
              Вернуться к анализу
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PostDecisionLock;









































