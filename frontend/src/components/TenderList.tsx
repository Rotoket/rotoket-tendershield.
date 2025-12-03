import React from 'react';
import { Tender, TenderStatus } from '../types';
import { ChevronRight, Calendar, AlertCircle } from 'lucide-react';

interface TenderListProps {
  tenders: Tender[];
  onSelectTender: (tender: Tender) => void;
}

const TenderList: React.FC<TenderListProps> = ({ tenders, onSelectTender }) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="p-6 border-b border-slate-100 flex justify-between items-center">
        <h2 className="text-xl font-bold text-slate-900">Мои заявки</h2>
        <div className="flex gap-2">
            <select className="text-sm border border-slate-200 rounded-lg px-3 py-1.5 bg-white text-slate-600 outline-none focus:border-blue-500">
                <option>Все статусы</option>
                <option>В работе</option>
                <option>На проверке</option>
            </select>
        </div>
      </div>
      
      <div className="divide-y divide-slate-100">
        {tenders.map((tender) => (
          <div 
            key={tender.id} 
            onClick={() => onSelectTender(tender)}
            className="p-6 hover:bg-slate-50 transition-colors cursor-pointer group"
          >
            <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded uppercase tracking-wide
                        ${tender.fz === '44-ФЗ' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}
                    `}>
                        {tender.fz}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">{tender.id}</span>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-sm font-bold text-slate-900">
                        {(tender.price).toLocaleString('ru-RU')} ₽
                    </span>
                     {tender.riskScore > 50 && (
                        <div className="flex items-center text-xs font-medium text-red-600 bg-red-50 px-2 py-0.5 rounded-full border border-red-100">
                            <AlertCircle size={12} className="mr-1" />
                            Риск: {tender.riskScore}%
                        </div>
                    )}
                </div>
            </div>

            <h3 className="text-base font-semibold text-slate-800 mb-3 group-hover:text-blue-600 transition-colors line-clamp-1">
                {tender.title}
            </h3>

            <div className="flex justify-between items-end">
                <div className="flex gap-4 text-sm text-slate-500">
                    <span className="flex items-center">
                        <Calendar size={14} className="mr-1.5" />
                        Дедлайн: {tender.deadline}
                    </span>
                    <span className="truncate max-w-[200px]">
                        Заказчик: {tender.customer}
                    </span>
                </div>
                
                <button className="text-sm font-medium text-blue-600 flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                    Анализ <ChevronRight size={16} className="ml-1" />
                </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TenderList;
