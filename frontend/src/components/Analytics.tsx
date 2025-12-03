import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } from 'recharts';
import { TrendingUp, Award, AlertTriangle, Briefcase, Download, Loader2, Users, FileText, BarChart3, Activity } from 'lucide-react';
import { 
  getUserAnalytics, 
  getSystemAnalytics, 
  getAnalyticsTimeline, 
  getPopularIndustries, 
  getAverageScores,
  type UserStats,
  type SystemStats,
  type TimelineData,
  type PopularIndustry
} from '../services/analyticsService';
import { getCurrentUser } from '../services/authService';
import { useToast } from './Toast';

const COLORS = ['#00d4ff', '#0891b2', '#f59e0b', '#64748b', '#8b5cf6', '#ec4899'];

const Analytics: React.FC = () => {
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [popularIndustries, setPopularIndustries] = useState<PopularIndustry[]>([]);
  const [averageScores, setAverageScores] = useState<Record<string, { average_score: number; analyses_count: number }>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const { showToast, ToastComponent } = useToast();

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setIsLoading(true);
      const user = await getCurrentUser();
      
      if (user) {
        // Загружаем статистику пользователя
        try {
          const stats = await getUserAnalytics(user.id);
          setUserStats(stats);
        } catch (error) {
          console.error('Error loading user stats:', error);
        }

        // Проверяем, является ли пользователь админом
        if (user.email === 'admin@tendershield.pro') {
          setIsAdmin(true);
          try {
            const sysStats = await getSystemAnalytics();
            setSystemStats(sysStats);
          } catch (error) {
            console.error('Error loading system stats:', error);
          }
        }
      }

      // Загружаем публичные данные
      try {
        const [timelineData, industries, scores] = await Promise.all([
          getAnalyticsTimeline(30),
          getPopularIndustries(5),
          getAverageScores()
        ]);
        setTimeline(timelineData);
        setPopularIndustries(industries);
        setAverageScores(scores);
      } catch (error) {
        console.error('Error loading public analytics:', error);
        showToast('error', 'Ошибка загрузки аналитики');
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
      showToast('error', 'Ошибка загрузки данных');
    } finally {
      setIsLoading(false);
    }
  };

  const exportReport = async (format: 'csv' | 'excel' = 'excel') => {
    try {
      showToast('info', `Экспорт отчета в ${format.toUpperCase()}...`);
      
      const user = await getCurrentUser();
      const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/analytics/export/${format}`;
      
      const { getAuthHeaders } = await import('../services/authService');
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          ...getAuthHeaders(),
        },
      });
      
      if (!response.ok) {
        throw new Error('Ошибка экспорта');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `analytics_${new Date().toISOString().split('T')[0]}.${format === 'csv' ? 'csv' : 'xlsx'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
      
      showToast('success', `Отчет успешно экспортирован в ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export error:', error);
      showToast('error', 'Ошибка при экспорте отчета');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-[#00d4ff] animate-spin" />
      </div>
    );
  }

  // Форматируем данные для графиков
  const timelineChartData = timeline.map(item => ({
    date: new Date(item.date).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' }),
    count: item.count
  }));

  const industryChartData = popularIndustries.map(item => ({
    name: item.industry === 'UNIVERSAL' ? 'Универсальный' : 
          item.industry === 'IT' ? 'IT и ПО' :
          item.industry === 'CONSTRUCTION' ? 'Строительство' :
          item.industry === 'MEDICINE' ? 'Медицина' : item.industry,
    value: item.count
  }));

  const totalIndustryCount = industryChartData.reduce((sum, item) => sum + item.value, 0);
  const industryPercentages = industryChartData.map(item => ({
    ...item,
    percentage: totalIndustryCount > 0 ? Math.round((item.value / totalIndustryCount) * 100) : 0
  }));

  return (
    <>
      <ToastComponent />
      <div className="space-y-6 animate-fade-in">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-white mb-1">Аналитика и метрики</h2>
            <p className="text-slate-400 text-sm">Статистика использования системы</p>
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => exportReport('csv')}
              className="flex items-center gap-2 px-4 py-2 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-[#00d4ff] text-sm font-medium hover:bg-[#2a3441] transition-colors"
            >
              <Download size={16} /> CSV
            </button>
            <button 
              onClick={() => exportReport('excel')}
              className="flex items-center gap-2 px-4 py-2 bg-[#1a1f2e] border border-[#2a3441] rounded-lg text-[#00d4ff] text-sm font-medium hover:bg-[#2a3441] transition-colors"
            >
              <Download size={16} /> Excel
            </button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {userStats && (
            <>
              <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
                <div className="flex justify-between items-start mb-2">
                  <div className="p-2 bg-[#00d4ff]/20 text-[#00d4ff] rounded-lg">
                    <FileText size={24} />
                  </div>
                  <span className="text-xs font-bold text-[#00d4ff] bg-[#00d4ff]/10 px-2 py-0.5 rounded">
                    {userStats.current_month_analyses} / {userStats.tariff_limit}
                  </span>
                </div>
                <div className="text-3xl font-bold text-white">{userStats.total_analyses}</div>
                <div className="text-sm text-slate-400">Всего анализов</div>
                {userStats.trial_active && (
                  <div className="text-xs text-[#f59e0b] mt-2">
                    Триал: {userStats.trial_days_left} дней
                  </div>
                )}
              </div>

              <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
                <div className="flex justify-between items-start mb-2">
                  <div className="p-2 bg-green-500/20 text-green-400 rounded-lg">
                    <Award size={24} />
                  </div>
                </div>
                <div className="text-3xl font-bold text-white">{userStats.total_packages}</div>
                <div className="text-sm text-slate-400">Пакетных анализов</div>
              </div>
            </>
          )}

          {systemStats && isAdmin && (
            <>
              <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
                <div className="flex justify-between items-start mb-2">
                  <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                    <Users size={24} />
                  </div>
                  <span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
                    +{systemStats.active_users_30d}
                  </span>
                </div>
                <div className="text-3xl font-bold text-white">{systemStats.total_users}</div>
                <div className="text-sm text-slate-400">Всего пользователей</div>
              </div>

              <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
                <div className="flex justify-between items-start mb-2">
                  <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
                    <Activity size={24} />
                  </div>
                  <span className="text-xs font-bold text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded">
                    {systemStats.recent_analyses_30d}
                  </span>
                </div>
                <div className="text-3xl font-bold text-white">{systemStats.total_analyses}</div>
                <div className="text-sm text-slate-400">Всего анализов в системе</div>
              </div>
            </>
          )}

          {!userStats && !systemStats && (
            <div className="col-span-4 text-center py-8 text-slate-400">
              Загрузите данные для отображения статистики
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Timeline Chart */}
          <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-6">Динамика анализов</h3>
            {timelineChartData.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timelineChartData}>
                    <defs>
                      <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a3441" />
                    <XAxis dataKey="date" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1a1f2e', 
                        border: '1px solid #2a3441',
                        borderRadius: '8px',
                        color: '#fff'
                      }} 
                    />
                    <Area 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#00d4ff" 
                      strokeWidth={2}
                      fill="url(#colorCount)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-80 flex items-center justify-center text-slate-400">
                Нет данных за выбранный период
              </div>
            )}
          </div>

          {/* Industries Pie Chart */}
          <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-6">Популярные отрасли</h3>
            {industryPercentages.length > 0 ? (
              <>
                <div className="h-64 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={industryPercentages}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {industryPercentages.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#1a1f2e', 
                          border: '1px solid #2a3441',
                          borderRadius: '8px',
                          color: '#fff'
                        }} 
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-4 flex-wrap mt-4">
                  {industryPercentages.map((entry, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{backgroundColor: COLORS[index % COLORS.length]}}
                      ></div>
                      <span className="text-sm text-slate-400">
                        {entry.name} ({entry.value}, {entry.percentage}%)
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-400">
                Нет данных по отраслям
              </div>
            )}
          </div>
        </div>

        {/* Average Scores */}
        {Object.keys(averageScores).length > 0 && (
          <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
            <h3 className="text-lg font-bold text-white mb-4">Средние оценки по отраслям</h3>
            <div className="space-y-4">
              {Object.entries(averageScores).map(([industry, data]) => (
                <div key={industry}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="font-medium text-white">
                      {industry === 'UNIVERSAL' ? 'Универсальный' : 
                       industry === 'IT' ? 'IT и ПО' :
                       industry === 'CONSTRUCTION' ? 'Строительство' :
                       industry === 'MEDICINE' ? 'Медицина' : industry}
                    </span>
                    <span className="text-slate-400">
                      {data.average_score.toFixed(1)} / 100 ({data.analyses_count} анализов)
                    </span>
                  </div>
                  <div className="w-full bg-[#2a3441] rounded-full h-2.5">
                    <div 
                      className="bg-[#00d4ff] h-2.5 rounded-full transition-all" 
                      style={{ width: `${data.average_score}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* System Stats (Admin only) */}
        {systemStats && isAdmin && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
              <h3 className="text-lg font-bold text-white mb-4">Распределение по тарифам</h3>
              <div className="space-y-3">
                {Object.entries(systemStats.tariff_distribution).map(([tariff, count]) => (
                  <div key={tariff} className="flex justify-between items-center">
                    <span className="text-slate-400">{tariff}</span>
                    <span className="text-white font-bold">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[#1a1f2e] border border-[#2a3441] p-6 rounded-xl">
              <h3 className="text-lg font-bold text-white mb-4">Активность за 30 дней</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Активных пользователей</span>
                  <span className="text-white font-bold">{systemStats.active_users_30d}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Выполнено анализов</span>
                  <span className="text-white font-bold">{systemStats.recent_analyses_30d}</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default Analytics;
