import React from 'react';
import { AppView, User } from '../types';
import { Shield, FileSearch, BookOpen, Clock, FileText, LogOut, Zap, Calculator, Settings, BarChart3, HelpCircle } from 'lucide-react';

interface SidebarProps {
  currentView: AppView;
  onChangeView: (view: AppView) => void;
  user: User | null;
  onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ currentView, onChangeView, user, onLogout }) => {
  const menuItems = [
    { id: AppView.AUDIT, label: 'Анализ тендера', icon: FileSearch },
    { id: AppView.GENERATOR, label: 'Генератор', icon: FileText },
    { id: AppView.CALCULATOR, label: 'Калькулятор', icon: Calculator },
    { id: AppView.HISTORY, label: 'История проверок', icon: Clock },
    { id: AppView.KNOWLEDGE, label: 'База знаний', icon: BookOpen },
    { id: AppView.ANALYTICS, label: 'Аналитика', icon: BarChart3 },
    { id: AppView.HELP, label: 'Помощь', icon: HelpCircle },
  ];

  return (
    <aside className="w-[280px] bg-[#0f1419] border-r border-[#2a3441] h-screen flex flex-col fixed left-0 top-0 z-30 hidden md:flex">
      {/* Logo */}
      <div className="p-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#00d4ff] to-[#0088cc] rounded-xl flex items-center justify-center text-[#0f1419] shadow-[0_0_15px_rgba(0,212,255,0.3)]">
            <Shield size={24} strokeWidth={2.5} />
          </div>
          <div>
            <h1 className="font-bold text-white text-lg tracking-tight">Тендер.Щит.AI</h1>
            <p className="text-[#a8b5cc] text-[10px] font-mono tracking-widest uppercase">Защита бизнеса</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 space-y-2">
        <div className="text-[#4b5563] text-xs font-bold uppercase tracking-widest px-4 mb-4 mt-4">
          Рабочая зона
        </div>

        {menuItems.map(item => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onChangeView(item.id)}
              className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-xl text-sm font-medium transition-all duration-200 border ${isActive
                  ? 'bg-[rgba(0,212,255,0.1)] text-[#00d4ff] border-[#00d4ff]/30 shadow-[0_0_15px_rgba(0,212,255,0.1)]'
                  : 'text-[#a8b5cc] border-transparent hover:bg-[#1a1f2e] hover:text-white'
                }`}
            >
              <Icon size={20} />
              {item.label}
            </button>
          )
        })}

        <div
          onClick={() => onChangeView(AppView.PROFILE)}
          className="mt-8 mx-4 p-4 rounded-xl bg-gradient-to-br from-[#1a1f2e] to-[#0f1419] border border-[#2a3441] relative overflow-hidden group cursor-pointer hover:border-[#00d4ff] transition-colors"
        >
          <div className="absolute top-0 right-0 w-16 h-16 bg-[#00d4ff] opacity-5 blur-xl group-hover:opacity-10 transition-opacity"></div>
          <div className="flex items-center gap-2 mb-2 text-[#00d4ff]">
            <Zap size={16} fill="currentColor" />
            <span className="text-xs font-bold uppercase">Тариф {user?.tariff || 'START'}</span>
          </div>
          <p className="text-xs text-[#a8b5cc] mb-3">Осталось: 85 / 100 проверок</p>
          <div className="w-full h-1 bg-[#2a3441] rounded-full overflow-hidden">
            <div className="w-[85%] h-full bg-[#00d4ff]"></div>
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-[#2a3441]">
        <div className="flex items-center justify-between px-2">
          <button
            onClick={() => onChangeView(AppView.PROFILE)}
            className="flex items-center gap-3 hover:bg-[#1a1f2e] p-2 rounded-lg transition-colors flex-1 text-left"
          >
            <div className="w-8 h-8 rounded-full bg-[#2a3441] flex items-center justify-center text-white text-xs font-bold ring-2 ring-[#0f1419]">
              {user?.name.charAt(0)}
            </div>
            <div className="text-sm overflow-hidden">
              <p className="text-white font-medium truncate">{user?.name}</p>
              <p className="text-[#a8b5cc] text-xs truncate">{user?.company}</p>
            </div>
          </button>
          <button onClick={onLogout} className="text-[#4b5563] hover:text-[#ff4444] transition-colors p-2">
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;