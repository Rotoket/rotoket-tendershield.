import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, AreaChart, Area } from 'recharts';
import { ArrowUp, Clock, FileCheck, AlertTriangle, TrendingUp } from 'lucide-react';
import { MOCK_TENDERS } from '../constants';

const Dashboard: React.FC = () => {
  const data = [
    { name: 'Пн', value: 4 },
    { name: 'Вт', value: 3 },
    { name: 'Ср', value: 7 },
    { name: 'Чт', value: 5 },
    { name: 'Пт', value: 6 },
    { name: 'Сб', value: 2 },
    { name: 'Вс', value: 1 },
  ];

  const StatCard = ({ title, value, trend, icon: Icon, color, trendUp, subtext }: any) => (
    <div className="bg-white p-6 rounded-xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] border border-slate-100 hover:shadow-lg transition-shadow duration-300 relative overflow-hidden group">
      <div className={`absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity ${color.replace('bg-', 'text-')}`}>
         <Icon size={64} />
      </div>
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <h3 className="text-3xl font-bold text-slate-900 mt-1 tracking-tight">{value}</h3>
        </div>
        <div className={`p-3 rounded-xl ${color} shadow-sm`}>
          <Icon size={24} className="text-white" />
        </div>
      </div>
      <div className="flex items-center text-sm relative z-10">
        <span className={`flex items-center font-bold px-1.5 py-0.5 rounded ${trendUp ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'}`}>
          <ArrowUp size={14} className={`mr-1 ${trendUp ? '' : 'rotate-180'}`} />
          {trend}
        </span>
        <span className="text-slate-400 ml-2 font-medium">{subtext || "к прошлой неделе"}</span>
      </div>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Центр Управления</h2>
          <p className="text-slate-500">Обзор активности и ключевые метрики</p>
        </div>
        <div className="flex gap-3">
             <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 text-sm font-medium hover:bg-slate-50 transition-colors">
                <Clock size={16} /> История
             </button>
            <span className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-lg shadow-blue-200 cursor-default">
                <TrendingUp size={16} /> Win Rate: 68%
            </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Активные заявки" 
          value="12" 
          trend="+15%" 
          icon={FileCheck} 
          color="bg-blue-600" 
          trendUp={true} 
        />
        <StatCard 
          title="Срочные дедлайны" 
          value="3" 
          trend="-2" 
          icon={Clock} 
          color="bg-amber-500" 
          trendUp={false} 
          subtext="критический уровень"
        />
        <StatCard 
          title="Потенциал (млн ₽)" 
          value="45.2" 
          trend="+8%" 
          icon={TrendingUp} 
          color="bg-indigo-600" 
          trendUp={true} 
        />
         <StatCard 
          title="Рискованные лоты" 
          value="2" 
          trend="+1" 
          icon={AlertTriangle} 
          color="bg-red-500" 
          trendUp={false} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] border border-slate-100">
          <div className="flex justify-between items-center mb-6">
             <h3 className="text-lg font-bold text-slate-900">Динамика подачи заявок</h3>
             <select className="text-sm bg-slate-50 border-none rounded-lg px-3 py-1 text-slate-600 font-medium outline-none cursor-pointer">
                 <option>За неделю</option>
                 <option>За месяц</option>
             </select>
          </div>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 12}} />
                <Tooltip 
                  cursor={{stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4'}}
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)' }}
                />
                <Area type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Tenders (Mini List) */}
        <div className="bg-white p-6 rounded-xl shadow-[0_2px_10px_-3px_rgba(6,81,237,0.1)] border border-slate-100 flex flex-col">
          <h3 className="text-lg font-bold text-slate-900 mb-4">Ближайшие дедлайны</h3>
          <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
            {MOCK_TENDERS.slice(0, 3).map(tender => (
              <div key={tender.id} className="p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-blue-200 hover:shadow-md transition-all cursor-pointer group">
                <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-500 uppercase">
                        {tender.fz}
                    </span>
                    <span className="text-xs font-bold text-red-500 flex items-center bg-red-50 px-2 py-0.5 rounded-full">
                        <Clock size={12} className="mr-1" />
                        {tender.deadline}
                    </span>
                </div>
                <h4 className="text-sm font-bold text-slate-800 line-clamp-2 group-hover:text-blue-600 mb-2 leading-snug">
                    {tender.title}
                </h4>
                <div className="text-sm font-bold text-slate-700">
                    {(tender.price / 1000000).toFixed(1)} млн ₽
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-4 py-3 text-sm font-bold text-blue-600 bg-blue-50 rounded-xl hover:bg-blue-100 transition-colors flex items-center justify-center gap-2">
            Смотреть все <TrendingUp size={16}/>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;