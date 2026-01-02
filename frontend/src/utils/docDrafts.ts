export interface ProtocolRowForm {
  clause: string;
  customerVersion: string;
  supplierVersion: string;
  justification: string;
}

export interface ViolationForm {
  point: string;
  argument: string;
  law: string;
}

export interface UserDecision {
  decision: 'participate' | 'participate_with_conditions' | 'do_not_participate' | 'postpone';
  comment?: string;
  timestamp: string;
}

export interface ProtocolDraftParams {
  tenderNumber: string;
  customer: string;
  subject: string;
  ref: string;
  rows: ProtocolRowForm[];
  decision?: UserDecision;
}

export interface ComplaintDraftParams {
  to: string;
  from: string;
  tenderNumber: string;
  customer: string;
  topic: string;
  ref: string;
  violations: ViolationForm[];
  decision?: UserDecision;
}

const formatDecisionLabel = (decision: string): string => {
  switch (decision) {
    case 'participate':
      return 'Участвовать';
    case 'participate_with_conditions':
      return 'Участвовать с условиями';
    case 'do_not_participate':
      return 'Не участвовать';
    case 'postpone':
      return 'Отложить решение';
    default:
      return decision;
  }
};

const formatDateTime = (iso: string): string => {
  try {
    const d = new Date(iso);
    return d.toLocaleString('ru-RU');
  } catch {
    return iso;
  }
};

export function buildProtocolDraft(params: ProtocolDraftParams): string {
  const { tenderNumber, customer, subject, ref, rows, decision } = params;
  const lines: string[] = [];

  lines.push('ПРОТОКОЛ РАЗНОГЛАСИЙ К ПРОЕКТУ КОНТРАКТА');
  lines.push('');
  
  // Секция решения (если есть)
  if (decision) {
    lines.push('## Решение по тендеру');
    lines.push(`Статус: ${formatDecisionLabel(decision.decision)}`);
    lines.push(`Дата решения: ${formatDateTime(decision.timestamp)}`);
    if (decision.comment) {
      lines.push(`Комментарий: ${decision.comment}`);
    }
    lines.push('');
  }
  
  if (tenderNumber) lines.push(`По результатам закупки: ${tenderNumber}`);
  if (subject) lines.push(`Предмет закупки: ${subject}`);
  if (customer) lines.push(`Заказчик: ${customer}`);
  if (ref) lines.push(`Ссылка на извещение / контракт: ${ref}`);
  lines.push('');
  lines.push('Таблица разногласий:');
  lines.push('№ | Пункт проекта контракта | Редакция заказчика | Редакция участника | Обоснование изменений');
  lines.push('---|--------------------------|---------------------|---------------------|----------------------');

  rows.forEach((row, idx) => {
    if (!row.clause && !row.customerVersion && !row.supplierVersion && !row.justification) return;
    lines.push(
      `${idx + 1} | ${row.clause || '-'} | ${row.customerVersion || '-'} | ${row.supplierVersion || '-'} | ${
        row.justification || '-'
      }`,
    );
  });

  lines.push('');
  
  // Адаптируем заключение в зависимости от решения
  if (decision) {
    switch (decision.decision) {
      case 'participate_with_conditions':
        lines.push('Настоящий протокол разногласий составлен в рамках решения об участии с условиями.');
        lines.push('Просим рассмотреть предложения и при отсутствии возражений учесть их при формировании итоговой редакции контракта.');
        lines.push('Участие в закупке возможно только при учёте указанных условий.');
        break;
      case 'do_not_participate':
        lines.push('Настоящий протокол разногласий составлен в рамках решения об отказе от участия в закупке.');
        lines.push('Указанные разногласия являются основанием для отказа от подачи заявки.');
        break;
      default:
        lines.push(
          'Настоящий протокол разногласий составлен в целях приведения условий проекта контракта в соответствие с требованиями законодательства РФ о контрактной системе и фактическими договорённостями сторон.',
        );
        lines.push(
          'Просим рассмотреть предложения и при отсутствии возражений учесть их при формировании итоговой редакции контракта.',
        );
    }
  } else {
    lines.push(
      'Настоящий протокол разногласий составлен в целях приведения условий проекта контракта в соответствие с требованиями законодательства РФ о контрактной системе и фактическими договорённостями сторон.',
    );
    lines.push(
      'Просим рассмотреть предложения и при отсутствии возражений учесть их при формировании итоговой редакции контракта.',
    );
  }
  
  lines.push('');
  lines.push('Подпись уполномоченного лица участника закупки: _______________________ /________________/');

  return lines.join('\n');
}

export function buildComplaintDraft(params: ComplaintDraftParams): string {
  const { to, from, tenderNumber, customer, topic, ref, violations, decision } = params;
  const lines: string[] = [];

  lines.push('ЖАЛОБА В АНТИМОНОПОЛЬНЫЙ ОРГАН НА ДОКУМЕНТАЦИЮ ЗАКУПКИ');
  lines.push('');
  
  // Секция решения (если есть)
  if (decision) {
    lines.push('## Решение по тендеру');
    lines.push(`Статус: ${formatDecisionLabel(decision.decision)}`);
    lines.push(`Дата решения: ${formatDateTime(decision.timestamp)}`);
    if (decision.comment) {
      lines.push(`Комментарий: ${decision.comment}`);
    }
    lines.push('');
  }
  
  if (to) lines.push(`В: ${to}`);
  if (from) lines.push(`От: ${from}`);
  lines.push('');
  if (tenderNumber) lines.push(`Закупка (извещение): ${tenderNumber}`);
  if (customer) lines.push(`Заказчик: ${customer}`);
  if (ref) lines.push(`Ссылка на закупку / площадку: ${ref}`);
  lines.push('');

  lines.push('1. Суть жалобы');
  lines.push(
    topic ||
      'Просим признать документацию о закупке содержащей положения, нарушающие законодательство РФ о контрактной системе и ограничивающие конкуренцию.',
  );
  lines.push('');

  lines.push('2. Описание нарушений');
  const nonEmpty = violations.filter((v) => v.point || v.argument || v.law);
  if (!nonEmpty.length) {
    lines.push(
      'Конкретные нарушения необходимо подробно описать (пункты документации, аргументация и нормы закона).',
    );
  } else {
    nonEmpty.forEach((v, idx) => {
      lines.push(`(${idx + 1}) Пункт документации: ${v.point || '-'}`);
      if (v.argument) lines.push(`    Описание нарушения: ${v.argument}`);
      if (v.law) lines.push(`    Нарушенные нормы: ${v.law}`);
      lines.push('');
    });
  }

  lines.push('3. Просим');
  lines.push(
    '1) Признать положения документации, указанные выше, не соответствующими законодательству РФ о контрактной системе.',
  );
  lines.push('2) Обязать Заказчика внести изменения в документацию либо отменить закупку в установленном порядке.');
  lines.push('');
  
  // Адаптируем дополнительную информацию в зависимости от решения
  lines.push('4. Дополнительно');
  if (decision && decision.decision === 'do_not_participate') {
    lines.push('Настоящая жалоба подана в рамках решения об отказе от участия в закупке.');
    lines.push('Указанные нарушения являются основанием для отказа от подачи заявки.');
  } else {
    lines.push(
      'Настоящая жалоба подана в установленные сроки. К жалобе прилагаются копии документов, подтверждающих изложенные доводы (при наличии).',
    );
  }
  lines.push('');
  lines.push('Подпись уполномоченного лица заявителя: _______________________ /________________/');

  return lines.join('\n');
}
