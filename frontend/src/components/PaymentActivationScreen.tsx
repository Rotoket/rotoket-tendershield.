import React from 'react';
import { Shield, Check, ArrowRight } from 'lucide-react';

interface PaymentActivationScreenProps {
  onActivate: () => void;
  onBack?: () => void;
}

const PaymentActivationScreen: React.FC<PaymentActivationScreenProps> = ({
  onActivate,
  onBack,
}) => {
  return (
    <div className="min-h-screen bg-[#0f1419] flex items-center justify-center p-8">
      <div className="max-w-3xl mx-auto">
        {/* Заголовок */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 rounded-full bg-[#00d4ff]/20 border-4 border-[#00d4ff] flex items-center justify-center mx-auto mb-6">
            <Shield size={48} className="text-[#00d4ff]" />
          </div>
          <h1 className="text-4xl font-bold text-white mb-4">
            Активировать защиту решений
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Доступ открывает инструменты для работы с зафиксированными решениями
            и их последствиями
          </p>
        </div>

        {/* Список возможностей */}
        <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8">
          <h2 className="text-xl font-bold text-white mb-6">Доступ включает:</h2>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <Check size={20} className="text-[#00e648] mt-1 flex-shrink-0" />
              <div>
                <p className="text-white font-semibold mb-1">Расчёт финансовых последствий</p>
                <p className="text-sm text-slate-400">
                  Калькулятор маржинальности с учётом рисков по контракту
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Check size={20} className="text-[#00e648] mt-1 flex-shrink-0" />
              <div>
                <p className="text-white font-semibold mb-1">Генерация документов</p>
                <p className="text-sm text-slate-400">
                  Протоколы разногласий, жалобы в ФАС, письма заказчику
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Check size={20} className="text-[#00e648] mt-1 flex-shrink-0" />
              <div>
                <p className="text-white font-semibold mb-1">Экспорт для руководства и compliance</p>
                <p className="text-sm text-slate-400">
                  Board Pack, отчёты для юристов, экспорт в Excel и PDF
                </p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <Check size={20} className="text-[#00e648] mt-1 flex-shrink-0" />
              <div>
                <p className="text-white font-semibold mb-1">История и аудит решений</p>
                <p className="text-sm text-slate-400">
                  Журнал всех принятых решений, аналитика, неизменяемый Audit Trail
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Тариф */}
        <div className="bg-[#1a1f2e] border-2 border-[#00d4ff] rounded-2xl p-8 mb-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-white mb-2">Тендер.Щит</h3>
            <div className="flex items-baseline justify-center gap-2 mb-4">
              <span className="text-4xl font-bold text-[#00d4ff]">30 000 ₽</span>
              <span className="text-slate-400">/ месяц</span>
            </div>
            <p className="text-sm text-slate-400 mb-6">
              Отмена в любой момент
            </p>
            <button
              onClick={onActivate}
              className="w-full px-8 py-4 bg-[#00d4ff] hover:bg-[#00b3e0] text-[#0f1419] text-lg font-bold rounded-xl shadow-lg shadow-[#00d4ff]/30 transition-all flex items-center justify-center gap-2"
            >
              Активировать доступ
              <ArrowRight size={20} />
            </button>
          </div>
        </div>

        {onBack && (
          <div className="text-center">
            <button
              onClick={onBack}
              className="text-sm text-slate-400 hover:text-slate-300 underline"
            >
              Вернуться
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PaymentActivationScreen;










































