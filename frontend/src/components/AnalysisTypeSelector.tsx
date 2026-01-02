import React from 'react';
import { FileText, FolderOpen, ArrowRight } from 'lucide-react';

interface AnalysisTypeSelectorProps {
  onSelect: (mode: 'single' | 'package') => void;
  defaultMode?: 'single' | 'package';
}

const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  onSelect,
  // По умолчанию предлагаем работу с ключевыми документами (пакет до 3–5 файлов)
  defaultMode = 'package',
}) => {
  const [selected, setSelected] = React.useState<'single' | 'package'>(defaultMode);

  const handleSelect = (mode: 'single' | 'package') => {
    setSelected(mode);
  };

  return (
    <div className="min-h-screen bg-[#0f1419] flex items-center justify-center p-8">
      <div className="max-w-3xl mx-auto">
        {/* Вопрос */}
        <h2 className="text-3xl font-bold text-white text-center mb-12">
          Какой формат анализа вы хотите запустить?
        </h2>

        {/* Две карточки */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Один документ */}
          <button
            onClick={() => handleSelect('single')}
            className={`p-8 rounded-2xl border-2 transition-all text-left ${
              selected === 'single'
                ? 'border-[#00d4ff] bg-[#00d4ff]/10 shadow-lg shadow-[#00d4ff]/20'
                : 'border-[#2a3441] bg-[#1a1f2e] hover:border-[#00d4ff]/50'
            }`}
          >
            <div className="flex items-center gap-4 mb-4">
              <div
                className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                  selected === 'single'
                    ? 'bg-[#00d4ff]/20 text-[#00d4ff]'
                    : 'bg-[#2a3441] text-slate-400'
                }`}
              >
                <FileText size={28} />
              </div>
              <h3 className="text-xl font-bold text-white">Один документ</h3>
            </div>
            <p className="text-slate-300 leading-relaxed">
              Быстрая проверка проекта договора или ТЗ
            </p>
          </button>

          {/* Пакет ключевых документов */}
          <button
            onClick={() => handleSelect('package')}
            className={`p-8 rounded-2xl border-2 transition-all text-left ${
              selected === 'package'
                ? 'border-[#00d4ff] bg-[#00d4ff]/10 shadow-lg shadow-[#00d4ff]/20'
                : 'border-[#2a3441] bg-[#1a1f2e] hover:border-[#00d4ff]/50'
            }`}
          >
            <div className="flex items-center gap-4 mb-4">
              <div
                className={`w-14 h-14 rounded-xl flex items-center justify-center ${
                  selected === 'package'
                    ? 'bg-[#00d4ff]/20 text-[#00d4ff]'
                    : 'bg-[#2a3441] text-slate-400'
                }`}
              >
                <FolderOpen size={28} />
              </div>
              <h3 className="text-xl font-bold text-white">Ключевые документы (пакет)</h3>
            </div>
            <p className="text-slate-300 leading-relaxed">
              3–5 основных файлов: извещение/документация, проект контракта, ТЗ, при необходимости — НМЦК и требования к заявке.
            </p>
          </button>
        </div>

        {/* Пояснение по количеству файлов */}
        <p className="text-sm text-slate-400 text-center max-w-2xl mx-auto mb-6 leading-relaxed">
          Для управленческого решения достаточно 3–5 ключевых документов. Расширенный пакет увеличивает время анализа и
          не всегда повышает качество решения.
        </p>

        {/* Кнопка продолжить */}
        <button
          onClick={() => onSelect(selected)}
          className="w-full md:w-auto px-8 py-4 bg-[#00d4ff] hover:bg-[#00b3e0] text-[#0f1419] font-bold rounded-xl shadow-lg shadow-[#00d4ff]/30 transition-all flex items-center justify-center gap-2 mx-auto"
        >
          Продолжить
          <ArrowRight size={20} />
        </button>
      </div>
    </div>
  );
};

export default AnalysisTypeSelector;










































