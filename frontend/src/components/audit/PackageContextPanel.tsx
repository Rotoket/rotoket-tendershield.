import React from 'react';

export interface PackageContext {
  documentsCount: number;
  law: string;              // '44-ФЗ' | '223-ФЗ' | 'Смешанный'
  totalNmck?: string;       // если есть
  region?: string;          // если есть
  analyzedAt?: string;      // ISO / human
  aiContext?: string;       // 1–2 предложения, опционально
}

interface PackageContextPanelProps {
  context: PackageContext;
}

const PackageContextPanel: React.FC<PackageContextPanelProps> = ({ context }) => {
  return (
    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
      <h3 className="text-white font-bold mb-3">Контекст пакета</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
        <div>
          <div className="text-slate-400">Документов</div>
          <div className="font-semibold">{context.documentsCount}</div>
        </div>
        <div>
          <div className="text-slate-400">Закон</div>
          <div className="font-semibold">{context.law}</div>
        </div>
        <div>
          <div className="text-slate-400">Общая НМЦК</div>
          <div className="font-semibold">{context.totalNmck ?? '—'}</div>
        </div>
        <div>
          <div className="text-slate-400">Регион</div>
          <div className="font-semibold">{context.region ?? '—'}</div>
        </div>
      </div>

      {context.aiContext && (
        <div className="text-xs text-slate-300 bg-[#0f1419] border border-[#2a3441] rounded-lg p-3">
          {context.aiContext}
        </div>
      )}
    </div>
  );
};

export default PackageContextPanel;















































