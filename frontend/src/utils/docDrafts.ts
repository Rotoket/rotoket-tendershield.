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

export interface ProtocolDraftParams {
  tenderNumber: string;
  customer: string;
  subject: string;
  ref: string;
  rows: ProtocolRowForm[];
}

export interface ComplaintDraftParams {
  to: string;
  from: string;
  tenderNumber: string;
  customer: string;
  topic: string;
  ref: string;
  violations: ViolationForm[];
}

export function buildProtocolDraft(params: ProtocolDraftParams): string {
  const { tenderNumber, customer, subject, ref, rows } = params;
  const lines: string[] = [];

  lines.push('ПРОТОКОЛ РАЗНОГЛАСИЙ К ПРОЕКТУ КОНТРАКТА');
  lines.push('');
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
  lines.push(
    'Настоящий протокол разногласий составлен в целях приведения условий проекта контракта в соответствие с требованиями законодательства РФ о контрактной системе и фактическими договорённостями сторон.',
  );
  lines.push(
    'Просим рассмотреть предложения и при отсутствии возражений учесть их при формировании итоговой редакции контракта.',
  );
  lines.push('');
  lines.push('Подпись уполномоченного лица участника закупки: _______________________ /________________/');

  return lines.join('\n');
}

export function buildComplaintDraft(params: ComplaintDraftParams): string {
  const { to, from, tenderNumber, customer, topic, ref, violations } = params;
  const lines: string[] = [];

  lines.push('ЖАЛОБА В АНТИМОНОПОЛЬНЫЙ ОРГАН НА ДОКУМЕНТАЦИЮ ЗАКУПКИ');
  lines.push('');
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
  lines.push('4. Дополнительно');
  lines.push(
    'Настоящая жалоба подана в установленные сроки. К жалобе прилагаются копии документов, подтверждающих изложенные доводы (при наличии).',
  );
  lines.push('');
  lines.push('Подпись уполномоченного лица заявителя: _______________________ /________________/');

  return lines.join('\n');
}
