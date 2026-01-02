import React, { useState, useEffect } from 'react';
import { FileText, Calendar, User, AlertCircle, Download } from 'lucide-react';
import { logEvent } from '../utils/logger';
import { getAuthHeaders } from '../services/authService';

/**
 * Тип записи в журнале управленческих решений (ШАГ 11 — Decision Record v1.0)
 * 
 * Канонические 7 полей:
 * 1. Tender ID
 * 2. Объект (кратко)
 * 3. Принятое решение
 * 4. Основание решения (1–3 причины)
 * 5. Индекс управленческой нагрузки (одно число)
 * 6. Ответственный
 * 7. Дата фиксации
 */
export interface DecisionRecord {
  id: string;
  tender_id: string;  // 1. Tender ID
  tender_object: string;  // 2. Объект (кратко)
  decision: 'PARTICIPATE' | 'DO_NOT_PARTICIPATE' | 'PARTICIPATE_WITH_CONDITIONS' | 'POSTPONE';  // 3. Принятое решение
  decision_reasons: string[];  // 4. Основание решения (1–3 причины)
  management_load_index: number;  // 5. Индекс управленческой нагрузки (0-100)
  responsible_person: string;  // 6. Ответственный
  fixed_at: string;  // 7. Дата фиксации
  analysis_id?: number;
  package_id?: string;
}

/**
 * Журнал управленческих решений v1.0
 * 
 * Экран отображает ЗАФИКСИРОВАННЫЕ РЕШЕНИЯ, а не аналитику.
 * 
 * Режимы:
 * - PREVIEW MODE: показывает пример записи до входа / без решений
 * - LIVE MODE: показывает реальные записи после фиксации решений
 */
const HistoryView: React.FC = () => {
  const [records, setRecords] = useState<DecisionRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Загрузка Decision Records из API (ШАГ 11)
    const loadRecords = async () => {
      try {
        const response = await fetch('/api/decision-records', {
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders(),
          },
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        setRecords(data.records || []);
        logEvent('HistoryView', `Загружено Decision Records: ${data.records?.length || 0}`, 'info');
      } catch (error) {
        logEvent('HistoryView', 'Ошибка загрузки Decision Records', 'error', error);
        setRecords([]);
      } finally {
        setIsLoading(false);
      }
    };

    loadRecords();
  }, []);

  // Пример записи для PREVIEW режима (канонический формат с 7 полями)
  const previewRecord: DecisionRecord = {
    id: 'preview-001',
    tender_id: '252253600872825360100100450018010244',
    tender_object: 'Поставка серверного оборудования для системы мониторинга',
    decision: 'DO_NOT_PARTICIPATE',
    decision_reasons: [
      'Блокирующее условие ответственности за простой',
      'Неограниченные штрафные санкции',
      'Отсутствие лимитов по гарантийным обязательствам',
    ],
    management_load_index: 75,
    responsible_person: 'Генеральный директор',
    fixed_at: '2024-12-24T10:00:00',
  };

  // Определяем режим: если нет реальных записей, показываем PREVIEW
  const isPreviewMode = records.length === 0;
  const displayRecords = isPreviewMode ? [previewRecord] : records;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
        <div className="text-slate-400">Загрузка журнала...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F14]">
      {/* Header */}
      <div className="border-b border-[#1F2933] bg-[#111821] px-8 py-6">
        <div className="max-w-[1600px] mx-auto">
          <h1 className="text-2xl font-semibold text-slate-100">Журнал управленческих решений</h1>
          <p className="text-sm text-slate-400 mt-2">
            Неизменяемый реестр зафиксированных управленческих решений и оснований их принятия.
          </p>
        </div>
      </div>

      {/* Статусная строка для PREVIEW */}
      {isPreviewMode && (
        <div className="bg-[#1A0F0A] border-b border-[#F97316]/20 px-8 py-3">
          <div className="max-w-[1600px] mx-auto">
            <div className="flex items-center gap-2 text-sm text-[#F97316]">
              <AlertCircle size={16} />
              <span>Вы просматриваете пример формата Decision Record (Журнал управленческих решений). Реальные записи появятся после фиксации решений.</span>
            </div>
          </div>
        </div>
      )}

      {/* Список записей */}
      <div className="max-w-[1600px] mx-auto px-8 py-6">
        <div className="space-y-6">
          {displayRecords.map((record) => (
            <DecisionCard key={record.id} record={record} />
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Карточка записи решения (Decision Record Card)
 * 
 * Канонический формат:
 * - ТЕНДЕР
 * - РЕШЕНИЕ (визуально акцентирован)
 * - ОСНОВАНИЯ (маркерный список)
 * - ЗАФИКСИРОВАНО (ответственный, дата)
 * - СТАТУС
 */
interface DecisionCardProps {
  record: DecisionRecord;
}

const DecisionCard: React.FC<DecisionCardProps> = ({ record }) => {
  const handleExportBoardPack = async (recordId: string) => {
    try {
      const response = await fetch(`/api/board-pack/${recordId}`, {
        headers: {
          ...getAuthHeaders(),
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `board_pack_${record.tender_id}_${new Date(record.fixed_at).toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      logEvent('HistoryView', `Board Pack экспортирован для записи ${recordId}`, 'info');
    } catch (error) {
      logEvent('HistoryView', `Ошибка экспорта Board Pack: ${recordId}`, 'error', error);
      alert('Ошибка экспорта Board Pack. Убедитесь, что вы авторизованы.');
    }
  };

  const formatDecisionLabel = (decision: string): string => {
    switch (decision) {
      case 'PARTICIPATE':
        return 'УЧАСТВОВАТЬ';
      case 'DO_NOT_PARTICIPATE':
        return 'НЕ УЧАСТВОВАТЬ';
      case 'PARTICIPATE_WITH_CONDITIONS':
        return 'УЧАСТВОВАТЬ С УСЛОВИЯМИ';
      case 'POSTPONE':
        return 'ОТЛОЖИТЬ РЕШЕНИЕ';
      default:
        return decision;
    }
  };

  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'DO_NOT_PARTICIPATE':
        return 'text-[#F97316] border-[#F97316]/30 bg-[#1A0F0A]';
      case 'PARTICIPATE':
        return 'text-[#4A6F85] border-[#4A6F85]/30 bg-[#0E1318]';
      case 'PARTICIPATE_WITH_CONDITIONS':
        return 'text-[#CBD5F5] border-[#CBD5F5]/30 bg-[#0E1318]';
      case 'POSTPONE':
        return 'text-slate-400 border-slate-400/30 bg-[#0E1318]';
      default:
        return 'text-slate-300 border-[#1F2933] bg-[#111821]';
    }
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('ru-RU', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="bg-[#111821] border border-[#1F2933] rounded-[3px] p-6">
      {/* ТЕНДЕР */}
      <div className="mb-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.15em] mb-1">
          ТЕНДЕР ID
        </p>
        <p className="text-sm font-mono text-slate-400 mb-2">{record.tender_id}</p>
        <p className="text-lg font-semibold text-slate-100">
          {record.tender_object}
        </p>
      </div>

      {/* РЕШЕНИЕ (визуально акцентирован) */}
      <div className={`border-l-4 rounded-[2px] p-5 mb-5 ${getDecisionColor(record.decision)}`}>
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.15em] mb-2">
          РЕШЕНИЕ
        </p>
        <p className="text-2xl font-bold">{formatDecisionLabel(record.decision)}</p>
      </div>

      {/* ОСНОВАНИЯ */}
      <div className="mb-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.15em] mb-3">
          ОСНОВАНИЯ
        </p>
        <div className="space-y-2">
          {record.decision_reasons.map((reason, index) => (
            <div key={index} className="text-sm text-slate-300 leading-relaxed">
              — {reason}
            </div>
          ))}
        </div>
      </div>

      {/* ИНДЕКС УПРАВЛЕНЧЕСКОЙ НАГРУЗКИ */}
      <div className="mb-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.15em] mb-2">
          ИНДЕКС УПРАВЛЕНЧЕСКОЙ НАГРУЗКИ (ИУН)
        </p>
        <p className="text-3xl font-bold text-[#00d4ff]">{record.management_load_index}</p>
      </div>

      {/* ЗАФИКСИРОВАНО */}
      <div className="mb-5 pb-5 border-b border-[#1F2933]">
        <div className="flex items-center justify-between mb-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-[0.15em]">
            ЗАФИКСИРОВАНО
          </p>
          <button
            onClick={() => handleExportBoardPack(record.id)}
            className="flex items-center gap-2 px-4 py-2 bg-[#00d4ff] text-[#0f1419] rounded-lg text-sm font-medium hover:bg-[#00b8e6] transition-colors"
            title="Экспортировать Board Pack (PDF)"
          >
            <Download size={16} />
            Экспорт Board Pack
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <User size={16} className="text-[#4A6F85] flex-shrink-0" />
            <span className="font-medium">Ответственный:</span>
            <span>{record.responsible_person}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <Calendar size={16} className="text-[#4A6F85] flex-shrink-0" />
            <span className="font-medium">Дата:</span>
            <span>{formatDate(record.fixed_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HistoryView;
