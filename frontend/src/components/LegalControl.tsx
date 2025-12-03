import React from 'react';
import { FileText, Gavel, BookOpen, Clock, ChevronRight, AlertCircle, FileCheck } from 'lucide-react';

const LegalControl: React.FC = () => {
    const generatedDocs = [
        { id: 1, type: 'Протокол разногласий', tender: 'Поставка серверов (Минцифры)', date: 'Сегодня, 10:45', status: 'ready' },
        { id: 2, type: 'Жалоба в ФАС', tender: 'Ремонт кровли (ГБУ Жилищник)', date: 'Вчера, 16:20', status: 'draft' },
        { id: 3, type: 'Запрос на разъяснение', tender: 'Разработка ПО (РЖД)', date: '23 окт, 09:15', status: 'sent' },
    ];

    const updates = [
        { id: 1, date: '01.10.2023', text: 'Вступили в силу изменения в ст. 34 44-ФЗ касательно сроков оплаты для СМП (теперь 7 дней).' },
        { id: 2, date: '15.09.2023', text: 'Новое Постановление Правительства №1528 об особенностях описания лекарственных препаратов.' },
    ];

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Правовой контроль</h2>
                    <p className="text-slate-400">Реестр документов и юридическая база знаний</p>
                </div>
                <button className="bg-[#00d4ff] text-[#0f1419] px-4 py-2 rounded-lg text-sm font-bold hover:bg-[#00b3d6] shadow-lg shadow-[#00d4ff]/20 transition-all flex items-center gap-2">
                    <BookOpen size={16} /> База знаний 44-ФЗ
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Generated Documents History */}
                <div className="lg:col-span-2 bg-[#1a1f2e] rounded-xl border border-[#2a3441] shadow-sm overflow-hidden">
                    <div className="p-6 border-b border-[#2a3441] flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white">История генерации документов</h3>
                        <span className="text-xs font-bold text-[#00d4ff] bg-[#00d4ff]/10 px-2 py-1 rounded-full">AI Created</span>
                    </div>
                    <div className="divide-y divide-[#2a3441]">
                        {generatedDocs.map((doc) => (
                            <div key={doc.id} className="p-4 hover:bg-[#232a3b] transition-colors flex items-center justify-between group cursor-pointer">
                                <div className="flex items-center gap-4">
                                    <div className={`p-3 rounded-lg ${doc.type === 'Жалоба в ФАС' ? 'bg-red-500/10 text-red-500' : 'bg-[#00d4ff]/10 text-[#00d4ff]'
                                        }`}>
                                        {doc.type === 'Жалоба в ФАС' ? <Gavel size={20} /> : <FileText size={20} />}
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-white text-sm">{doc.type}</h4>
                                        <p className="text-xs text-slate-400">{doc.tender}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-xs text-slate-500 flex items-center">
                                        <Clock size={12} className="mr-1" /> {doc.date}
                                    </span>
                                    <div className={`text-xs px-2 py-1 rounded font-bold uppercase ${doc.status === 'ready' ? 'bg-green-500/10 text-green-500' :
                                            doc.status === 'draft' ? 'bg-amber-500/10 text-amber-500' : 'bg-slate-700 text-slate-400'
                                        }`}>
                                        {doc.status === 'ready' ? 'Готов' : doc.status === 'draft' ? 'Черновик' : 'Отправлен'}
                                    </div>
                                    <ChevronRight size={16} className="text-slate-600 group-hover:text-[#00d4ff]" />
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="p-4 bg-[#1a1f2e] text-center border-t border-[#2a3441]">
                        <button className="text-sm font-medium text-[#00d4ff] hover:underline">Показать архив</button>
                    </div>
                </div>

                {/* Legislative Updates */}
                <div className="bg-[#1a1f2e] rounded-xl border border-[#2a3441] shadow-sm p-6 flex flex-col">
                    <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <AlertCircle size={20} className="text-amber-500" />
                        Изменения в законах
                    </h3>
                    <div className="space-y-4 flex-1">
                        {updates.map(upd => (
                            <div key={upd.id} className="bg-[#232a3b] p-3 rounded-lg border border-[#2a3441]">
                                <span className="text-[10px] font-bold text-slate-400 border border-[#2a3441] px-1.5 py-0.5 rounded bg-[#1a1f2e]">{upd.date}</span>
                                <p className="text-sm text-slate-300 mt-2 leading-snug">
                                    {upd.text}
                                </p>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-[#2a3441]">
                        <div className="flex items-center gap-3 p-3 bg-[#00d4ff]/10 rounded-lg">
                            <FileCheck className="text-[#00d4ff]" size={24} />
                            <div>
                                <p className="text-xs font-bold text-white">Умный помощник</p>
                                <p className="text-[10px] text-[#00d4ff]">Задайте вопрос по закону в чате тендера</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LegalControl;