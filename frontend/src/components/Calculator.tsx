import React, { useState, useEffect } from 'react';
import { DollarSign, AlertTriangle, TrendingUp, RefreshCw, Briefcase, Percent } from 'lucide-react';
import { CalculatorPreset } from '../types';
import { logEvent } from '../utils/logger';

interface CalculatorProps {
    preset?: CalculatorPreset | null;
}

// Простой парсер сумм вида "10 000 000 ₽" → 10000000
const parseAmountToNumber = (raw?: string): number | null => {
    if (!raw) return null;
    const cleaned = raw.replace(/[^0-9,\.]/g, '').replace(',', '.');
    if (!cleaned) return null;
    const num = Number(cleaned);
    return Number.isFinite(num) ? num : null;
};

const Calculator: React.FC<CalculatorProps> = ({ preset }) => {
    const [nmck, setNmck] = useState(1000000);
    const [reduction, setReduction] = useState(5);
    const [costMaterials, setCostMaterials] = useState(600000);
    const [costLogistics, setCostLogistics] = useState(50000);
    const [bankGuarantee, setBankGuarantee] = useState(15000);
    const [taxRate, setTaxRate] = useState(20);
    const [riskProb, setRiskProb] = useState(15);

    const [finalPrice, setFinalPrice] = useState(0);
    const [totalCost, setTotalCost] = useState(0);
    const [grossProfit, setGrossProfit] = useState(0);
    const [netProfit, setNetProfit] = useState(0);
    const [riskAdjustedProfit, setRiskAdjustedProfit] = useState(0);

    // Применяем пресет из анализа по кнопке
    const [lastPresetInfo, setLastPresetInfo] = useState<string | null>(null);

    useEffect(() => {
        const price = nmck * (1 - reduction / 100);
        const costs = Number(costMaterials) + Number(costLogistics) + Number(bankGuarantee);
        const gross = price - costs;
        const tax = gross * (taxRate / 100);
        const net = gross - tax;
        const riskCost = (price * 0.1) * (riskProb / 100);
        const riskAdj = net - riskCost;

        setFinalPrice(price);
        setTotalCost(costs);
        setGrossProfit(gross);
        setNetProfit(net);
        setRiskAdjustedProfit(riskAdj);
    }, [nmck, reduction, costMaterials, costLogistics, bankGuarantee, taxRate, riskProb]);

    const InputField = ({ label, value, onChange, icon: Icon, step = 1000 }: any) => (
        <div className="space-y-1">
            <label className="text-[#a8b5cc] text-xs font-bold uppercase tracking-wider">{label}</label>
            <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Icon className="h-4 w-4 text-[#4b5563] group-focus-within:text-[#00d4ff]" />
                </div>
                <input
                    type="number"
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    step={step}
                    className="block w-full pl-10 pr-3 py-2.5 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-white placeholder-[#4b5563] focus:outline-none focus:border-[#00d4ff] transition-all font-mono text-sm"
                />
            </div>
        </div>
    );

    const handleApplyPreset = () => {
        if (!preset) return;
        const nmckVal = parseAmountToNumber(preset.nmck);
        const estVal = parseAmountToNumber(preset.estimatedCost);

        if (nmckVal !== null) setNmck(nmckVal);
        if (estVal !== null) setCostMaterials(estVal);

        if (typeof preset.score === 'number') {
            const mappedRisk = Math.max(0, Math.min(100, 100 - Math.round(preset.score)));
            setRiskProb(mappedRisk);
        }

        const parts: string[] = [];
        if (preset.source === 'single') {
            parts.push('один документ');
        } else {
            parts.push('пакет документов');
            if (preset.packageId) parts.push(`ID пакета: ${preset.packageId.slice(0, 8)}...`);
        }
        if (preset.documentName) parts.push(`файл: ${preset.documentName}`);
        const info = parts.join(' · ');
        setLastPresetInfo(info);
        logEvent('Calculator', `Применён пресет из анализа (${info})`);
    };

    const handleResetBasicParams = () => {
        setNmck(1000000);
        setReduction(5);
        logEvent('Calculator', 'Сброшены базовые параметры НМЦК и снижения до значений по умолчанию');
    };

    return (
        <div className="animate-fade-in max-w-5xl mx-auto">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Тендерный Калькулятор</h2>
                    <p className="text-[#a8b5cc]">Расчет маржинальности с учетом коэффициента риска (Sinaps Score)</p>
                </div>
                        <div className="flex items-center gap-2">
                    {preset && (
                        <button
                            onClick={handleApplyPreset}
                            className="px-3 py-2 rounded-lg bg-[#00d4ff]/10 border border-[#00d4ff]/60 text-[#00d4ff] text-xs font-semibold hover:bg-[#00d4ff]/20 transition-all"
                        >
                            Заполнить из анализа
                        </button>
                    )}
                    <button
                        onClick={handleResetBasicParams}
                        className="p-2 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-[#a8b5cc] hover:text-white hover:border-[#00d4ff] transition-all"
                    >
                        <RefreshCw size={20} />
                    </button>
                </div>
            </div>

            {lastPresetInfo && (
                <div className="mb-4 text-xs text-[#a8b5cc] bg-[#1a1f2e] border border-[#2a3441] rounded-lg px-3 py-2">
                    Параметры загружены из анализа: {lastPresetInfo}. Проверьте числа перед расчетом — итог не является финансовой рекомендацией.
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <Briefcase size={20} className="text-[#00d4ff]" /> Параметры контракта
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <InputField label="НМЦК (Начальная цена)" value={nmck} onChange={setNmck} icon={DollarSign} />
                            <InputField label="Снижение (%)" value={reduction} onChange={setReduction} icon={Percent} step={0.5} />
                        </div>
                    </div>

                    <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-6">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <TrendingUp size={20} className="text-[#00d4ff]" /> Расходы
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <InputField label="Себестоимость товаров" value={costMaterials} onChange={setCostMaterials} icon={DollarSign} />
                            <InputField label="Логистика / Работы" value={costLogistics} onChange={setCostLogistics} icon={DollarSign} />
                            <InputField label="Банковская гарантия" value={bankGuarantee} onChange={setBankGuarantee} icon={DollarSign} step={100} />
                            <InputField label="Налоговая ставка (%)" value={taxRate} onChange={setTaxRate} icon={Percent} step={1} />
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-1">
                    <div className="bg-gradient-to-b from-[#1a1f2e] to-[#0f1419] border border-[#2a3441] rounded-2xl p-6 sticky top-6">
                        <h3 className="text-lg font-bold text-white mb-6">Финансовый итог</h3>

                        <div className="space-y-4 mb-8">
                            <div className="flex justify-between text-sm">
                                <span className="text-[#a8b5cc]">Цена контракта</span>
                                <span className="text-white font-mono font-bold">{finalPrice.toLocaleString()} ₽</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-[#a8b5cc]">Все расходы</span>
                                <span className="text-white font-mono">- {totalCost.toLocaleString()} ₽</span>
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-[#a8b5cc]">Налоги</span>
                                <span className="text-white font-mono">- {(grossProfit * (taxRate / 100)).toLocaleString()} ₽</span>
                            </div>
                            <div className="h-px bg-[#2a3441] my-2"></div>
                            <div className="flex justify-between text-base">
                                <span className="text-[#00d4ff] font-bold">Чистая прибыль</span>
                                <span className="text-[#00d4ff] font-mono font-bold">{netProfit.toLocaleString()} ₽</span>
                            </div>
                            <div className="flex justify-between text-xs text-[#4b5563]">
                                <span>ROI</span>
                                <span>{((netProfit / totalCost) * 100).toFixed(1)}%</span>
                            </div>
                        </div>

                        <div className="bg-[#0f1419] rounded-xl p-4 border border-[#2a3441]">
                            <div className="flex items-center gap-2 mb-2">
                                <div className={`w-2 h-2 rounded-full ${riskAdjustedProfit > 0 ? 'bg-[#00e648]' : 'bg-[#ff4444]'}`}></div>
                                <span className="text-xs font-bold uppercase text-[#a8b5cc]">С учетом рисков</span>
                            </div>
                            <div className={`text-2xl font-mono font-bold ${riskAdjustedProfit > 0 ? 'text-white' : 'text-[#ff4444]'}`}>
                                {riskAdjustedProfit.toLocaleString('ru-RU', { maximumFractionDigits: 0 })} ₽
                            </div>
                            <p className="mt-2 text-[10px] text-[#4b5563]">
                                Расчёт ориентировочный и зависит от точности введённых параметров и оценки риска. Не является инвестиционной или финансовой рекомендацией.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Calculator;