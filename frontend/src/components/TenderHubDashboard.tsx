import React from 'react';
import type { AnalysisResult, TenderHubSummary } from '../types';
import { AlertTriangle, CheckCircle, Info, ShieldAlert, FileText, Clock, Banknote, Scale, ClipboardList } from 'lucide-react';
import { logEvent } from '../utils/logger';

interface TenderHubDashboardProps {
  result: AnalysisResult;
  hub: TenderHubSummary;
}

const severityColor = (severity: string): string => {
  const s = severity.toUpperCase();
  if (s.includes('HIGH') || s.includes('ВЫС')) return 'text-red-400 bg-red-500/10 border-red-500/40';
  if (s.includes('MED') || s.includes('СРЕД')) return 'text-amber-300 bg-amber-500/10 border-amber-500/40';
  return 'text-emerald-300 bg-emerald-500/10 border-emerald-500/40';
};

export const TenderHubDashboard: React.FC<TenderHubDashboardProps> = ({ result, hub }) => {
  const { redFlagsTop, baseInfo, specsSummary, timeline, payments, guarantees, financial, recommendation } = hub;

  return (
    <div className="space-y-4 mb-6">
      {/* Верхняя плашка с красными флагами и вердиктом */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col gap-3">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
            <ShieldAlert className="text-red-400" size={18} />
            Красные флаги и ключевые риски
          </div>
          {redFlagsTop.length === 0 ? (
            <p className="text-xs text-slate-400">
              Явные критичные нарушения не выделены. Всё равно проверьте условия по 44-ФЗ/223-ФЗ и проект договора.
            </p>
          ) : (
            <ul className="space-y-2 text-xs">
              {redFlagsTop.map((rf, idx) => (
                <li
                  key={idx}
                  className={`flex items-start gap-2 px-2 py-1.5 rounded border ${severityColor(rf.severity)}`}
                >
                  <AlertTriangle size={14} className="mt-0.5" />
                  <div>
                    <div className="font-semibold">{rf.title}</div>
                    {rf.lawReference && (
                      <div className="text-[10px] text-slate-300 mt-0.5">Норма: {rf.lawReference}</div>
                    )}
                    {rf.explanation && (
                      <div className="text-[11px] text-slate-200 mt-0.5">{rf.explanation}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-4 flex flex-col justify-between">
          <div>
            <div className="text-xs text-slate-400 mb-1">Индекс безопасности</div>
            <div className="text-3xl font-bold text-white mb-1">{result.score}</div>
            <div className="text-[11px] text-slate-400">
              Вердикт системы: <span className="font-semibold text-slate-100">{result.verdict}</span>
            </div>
          </div>
          <p className="mt-3 text-[10px] text-slate-500 flex items-start gap-1">
            <Info size={12} className="mt-0.5" />
            <span>
              Оценка носит предварительный аналитический характер и не является юридической консультацией. Решение об
              участии принимает специалист.
            </span>
          </p>
        </div>
      </div>

      {/* Грид ключевых карточек */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        {/* Базовая инфо */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <FileText size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Базовая информация</span>
          </div>
          <div className="text-[11px] text-slate-300">
            <div>НМЦК: <span className="font-mono text-slate-100">{baseInfo.nmck}</span></div>
            <div>Закон: {baseInfo.fz}</div>
            <div>Регион: {baseInfo.region}</div>
            <div>Подача заявки: {baseInfo.deadlineApp}</div>
            {baseInfo.deadlineExecution && <div>Исполнение: {baseInfo.deadlineExecution}</div>}
          </div>
        </div>

        {/* Спецификации */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <ClipboardList size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Спецификация</span>
          </div>
          <div className="text-[11px] text-slate-300">
            <div>Позиций: {specsSummary.totalPositions}</div>
            <div>Высокий риск по позициям: {specsSummary.highRiskCount}</div>
          </div>
        </div>

        {/* Сроки */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <Clock size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Сроки</span>
          </div>
          <div className="text-[11px] text-slate-300">
            <div>
              Оценка сроков:{' '}
              <span className="font-semibold text-slate-100">
                {timeline.riskLevel === 'ok' ? 'Нормально' : timeline.riskLevel === 'tight' ? 'Жёстко' : 'Критично'}
              </span>
            </div>
            <div className="mt-0.5">{timeline.comment}</div>
          </div>
        </div>

        {/* Платежи */}
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <Banknote size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Платежи</span>
          </div>
          <div className="text-[11px] text-slate-300">
            <div>Аванс: {payments.advance}</div>
            {payments.mainPayment && <div>Основной платёж: {payments.mainPayment}</div>}
            <div className="mt-0.5">{payments.scheduleComment}</div>
          </div>
        </div>
      </div>

      {/* Второй ряд карточек: гарантии + финансы + резюме */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <CheckCircle size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Гарантии</span>
          </div>
          <div className="text-[11px] text-slate-300">
            <div className="mb-1">{guarantees.text}</div>
            <div>
              Уровень риска:{' '}
              <span className="font-semibold text-slate-100">
                {guarantees.riskLevel === 'low'
                  ? 'Низкий'
                  : guarantees.riskLevel === 'medium'
                    ? 'Средний'
                    : 'Повышенный'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col gap-1">
          <div className="flex items-center gap-2 text-slate-200 mb-1">
            <Scale size={14} className="text-[#00d4ff]" />
            <span className="font-semibold">Финансовая оценка</span>
          </div>
          <div className="text-[11px] text-slate-300">
            {financial.marginPercentApprox != null && (
              <div className="mb-1">
                Ориентировочная маржа:{' '}
                <span className="font-semibold text-slate-100">~{financial.marginPercentApprox}%</span>
              </div>
            )}
            <div className="mb-1">{financial.marginComment}</div>
            <div>
              Риск убытка:{' '}
              <span className="font-semibold text-slate-100">
                {financial.lossRiskLevel === 'low'
                  ? 'Низкий'
                  : financial.lossRiskLevel === 'medium'
                    ? 'Средний'
                    : 'Высокий'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-[#111827] border border-[#1f2937] rounded-xl p-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-slate-200 mb-1">
              <AlertTriangle size={14} className="text-[#00d4ff]" />
              <span className="font-semibold">Резюме и действия</span>
            </div>
            <div className="text-[11px] text-slate-300 mb-2">{recommendation.summaryShort}</div>
          </div>
          <div className="flex gap-2 mt-2">
            <button
              type="button"
              onClick={() => {
                logEvent('TenderHubDashboard', `Принято решение: УЧАСТВОВАТЬ. Вердикт: ${recommendation.verdict}, Индекс безопасности: ${result.score}`, 'info', {
                  verdict: recommendation.verdict,
                  score: result.score,
                  nmck: result.passport.nmck,
                });
                // В будущем здесь будет навигация к сбору документов или экспорт решения
              }}
              className="flex-1 py-1.5 rounded-lg bg-emerald-500 text-[#020617] text-xs font-semibold hover:bg-emerald-400 transition-colors"
            >
              Участвовать
            </button>
            <button
              type="button"
              onClick={() => {
                logEvent('TenderHubDashboard', 'Нажата кнопка: Запрос разъяснений', 'info', {
                  nmck: result.passport.nmck,
                });
                // В будущем здесь будет открытие формы запроса разъяснений
              }}
              className="flex-1 py-1.5 rounded-lg bg-slate-800 text-slate-100 text-xs font-semibold hover:bg-slate-700 transition-colors"
            >
              Запрос разъяснений
            </button>
            <button
              type="button"
              onClick={() => {
                logEvent('TenderHubDashboard', `Принято решение: НЕ УЧАСТВОВАТЬ. Причина: ${recommendation.summaryShort.substring(0, 50)}...`, 'info', {
                  verdict: recommendation.verdict,
                  score: result.score,
                  reason: recommendation.summaryShort,
                });
                // В будущем здесь будет возможность подачи жалобы в ФАС или экспорт решения
              }}
              className="flex-1 py-1.5 rounded-lg bg-red-500/90 text-[#020617] text-xs font-semibold hover:bg-red-400 transition-colors"
            >
              Не участвовать
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TenderHubDashboard;
