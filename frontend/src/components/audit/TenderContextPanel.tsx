import React from 'react';
import type { AnalysisResult } from '../../types';
import ExplanationPopover from '../ExplanationPopover';

interface TenderContextPanelProps {
  passport?: AnalysisResult['passport'] | null;
  passportValidation?: AnalysisResult['passportValidation'] | null;
  passportEvidence?: AnalysisResult['passportEvidence'] | null;
  documentsCount?: number;
  decisionRecorded?: boolean;
  /** Если нужно пояснить пользователю, откуда взят паспорт (например, "по выбранному документу") */
  subtitle?: string;
}

type PassportFieldKey =
  | 'tenderNumber'
  | 'customer'
  | 'nmck'
  | 'deadlineApp'
  | 'deadlineExecution'
  | 'fz'
  | 'region';

const fieldLabelRu: Record<PassportFieldKey, string> = {
  tenderNumber: 'Номер закупки',
  customer: 'Заказчик',
  nmck: 'НМЦК',
  deadlineApp: 'Дедлайн подачи заявок',
  deadlineExecution: 'Срок исполнения',
  fz: 'Закон',
  region: 'Регион',
};

const missingFieldLabelRu: Record<string, string> = {
  tenderNumber: 'номер закупки',
  customer: 'заказчик',
  nmck: 'НМЦК',
  deadlineApp: 'дедлайн подачи заявок',
  deadlineExecution: 'срок исполнения',
};

const isMissingField = (missingFields: string[], key: PassportFieldKey) =>
  missingFields.includes(key);

const FieldItem: React.FC<{
  label: string;
  value?: string;
  isMissing?: boolean;
  evidenceText?: string;
  evidenceTitle?: string;
  explanationQuestion?: string;
  explanationContext?: { lawCode?: string; term?: string };
  decisionRecorded?: boolean;
}> = ({ label, value, isMissing, evidenceText, evidenceTitle, explanationQuestion, explanationContext, decisionRecorded }) => {
  const display = (value || '').trim();
  const shown = display.length > 0 ? display : '—';

  return (
    <div className="flex flex-col gap-0.5 min-w-0">
      <span className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</span>
      <div className="flex items-center gap-2 min-w-0">
        <span
          className={`text-sm font-medium truncate ${isMissing ? 'text-yellow-300' : 'text-slate-200'}`}
          title={shown}
        >
          {shown}
        </span>
        {evidenceText && (
          <span
            className="text-[10px] text-slate-500 whitespace-nowrap"
            title={evidenceTitle}
          >
            {evidenceText}
          </span>
        )}
        {explanationQuestion && (
          <ExplanationPopover
            question={explanationQuestion}
            context={explanationContext}
            sourceBlock={label.toLowerCase().includes('закон') ? 'law' : 'term'}
            contourState={decisionRecorded ? 'after_decision' : 'before_decision'}
            decisionRecorded={!!decisionRecorded}
            position="bottom"
          >
            <span className="text-[10px] text-slate-500">пояснить</span>
          </ExplanationPopover>
        )}
      </div>
    </div>
  );
};

const TenderContextPanel: React.FC<TenderContextPanelProps> = ({
  passport,
  passportValidation,
  passportEvidence,
  documentsCount,
  decisionRecorded = false,
  subtitle,
}) => {
  if (!passport) return null;

  const missingFields = passportValidation?.missing_fields || [];

  const formatEvidence = (fieldKey: string): { text?: string; title?: string } => {
    const ev = passportEvidence?.[fieldKey]?.[0];
    if (!ev) return {};
    const parts: string[] = [];
    parts.push(ev.document_name);
    if (ev.page_reference) parts.push(`стр. ${ev.page_reference}`);
    if (ev.section_reference) parts.push(ev.section_reference);
    const text = `Источник: ${parts.join(', ')}`;
    const title = ev.quote ? `Цитата: ${ev.quote}` : text;
    return { text, title };
  };

  const law = passport.fz || '—';
  const region = passport.region || '—';
  const lawCode = law.match(/(\d+)-?ФЗ/i)?.[1]
    ? `${law.match(/(\d+)-?ФЗ/i)?.[1]}-ФЗ`
    : undefined;

  // НМЦК может приходить строкой или быть "Не найдено"
  const nmck = passport.nmck || '—';

  return (
    <div className="bg-[#0f1419] border border-[#2a3441] rounded-2xl p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-bold text-white">Паспорт тендера</h3>
          <p className="text-[11px] text-slate-500">
            {subtitle || 'Ключевые параметры для проверки перед решением.'}
          </p>
        </div>
        {typeof documentsCount === 'number' && (
          <div className="text-[11px] text-slate-400 whitespace-nowrap">
            Документов: <span className="text-slate-200 font-semibold">{documentsCount}</span>
          </div>
        )}
      </div>

      {passportValidation && !passportValidation.is_complete && (
        <div className="mt-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-3">
          <div className="text-xs text-yellow-200 font-semibold">
            Внимание: паспорт заполнен не полностью
          </div>
          <div className="text-[11px] text-slate-300 mt-1">
            Не найдены поля:{' '}
            <span className="text-yellow-200">
              {missingFields
                .map((f) => missingFieldLabelRu[f] || f)
                .filter(Boolean)
                .join(', ')}
            </span>
            . Это может означать, что данные находятся в другом файле/разделе или не распознаны.
          </div>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        <FieldItem
          label={fieldLabelRu.tenderNumber}
          value={(passport as any).tenderNumber}
          isMissing={isMissingField(missingFields, 'tenderNumber')}
          evidenceText={formatEvidence('tenderNumber').text}
          evidenceTitle={formatEvidence('tenderNumber').title}
        />
        <FieldItem
          label={fieldLabelRu.customer}
          value={(passport as any).customer}
          isMissing={isMissingField(missingFields, 'customer')}
          evidenceText={formatEvidence('customer').text}
          evidenceTitle={formatEvidence('customer').title}
        />
        <FieldItem
          label={fieldLabelRu.nmck}
          value={nmck}
          isMissing={isMissingField(missingFields, 'nmck')}
          evidenceText={formatEvidence('nmck').text}
          evidenceTitle={formatEvidence('nmck').title}
          explanationQuestion="Что такое НМЦК (начальная (максимальная) цена контракта)?"
          explanationContext={{ term: 'nmcd' }}
          decisionRecorded={decisionRecorded}
        />
        <FieldItem
          label={fieldLabelRu.deadlineApp}
          value={passport.deadlineApp}
          isMissing={isMissingField(missingFields, 'deadlineApp')}
          evidenceText={formatEvidence('deadlineApp').text}
          evidenceTitle={formatEvidence('deadlineApp').title}
        />
        <FieldItem
          label={fieldLabelRu.deadlineExecution}
          value={passport.deadlineExecution}
          isMissing={isMissingField(missingFields, 'deadlineExecution')}
          evidenceText={formatEvidence('deadlineExecution').text}
          evidenceTitle={formatEvidence('deadlineExecution').title}
        />
        <FieldItem
          label={fieldLabelRu.fz}
          value={law}
          explanationQuestion={lawCode ? `Что означает ссылка на ${lawCode} в документации?` : undefined}
          explanationContext={lawCode ? { lawCode } : undefined}
          decisionRecorded={decisionRecorded}
        />
        <FieldItem label={fieldLabelRu.region} value={region} />
      </div>
    </div>
  );
};

export default TenderContextPanel;












