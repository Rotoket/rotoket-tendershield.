import { describe, it, expect } from 'vitest';
import {
  buildProtocolDraft,
  buildComplaintDraft,
  ProtocolRowForm,
  ViolationForm,
} from './docDrafts';

describe('docDrafts', () => {
  it('buildProtocolDraft формирует шапку и строки таблицы', () => {
    const rows: ProtocolRowForm[] = [
      {
        clause: 'п. 3.2.1',
        customerVersion: 'Заказчик вправе...',
        supplierVersion: 'Участник предлагает...',
        justification: 'Во избежание нарушения ст. 34 44-ФЗ...',
      },
    ];

    const text = buildProtocolDraft({
      tenderNumber: '0445300000123000123',
      customer: 'УФК по г. Москве',
      subject: 'Поставка серверного оборудования',
      ref: 'https://zakupki.gov.ru/..',
      rows,
    });

    expect(text).toContain('ПРОТОКОЛ РАЗНОГЛАСИЙ К ПРОЕКТУ КОНТРАКТА');
    expect(text).toContain('По результатам закупки: 0445300000123000123');
    expect(text).toContain('Поставка серверного оборудования');
    expect(text).toContain('1 | п. 3.2.1 | Заказчик вправе... | Участник предлагает... | Во избежание нарушения ст. 34 44-ФЗ');
  });

  it('buildComplaintDraft формирует структуру жалобы с нарушениями', () => {
    const violations: ViolationForm[] = [
      {
        point: 'п. 1.2.3 ТЗ',
        argument: 'Требование конкретного бренда без фразы "или эквивалент" ограничивает конкуренцию.',
        law: 'ч.1 ст.33 44-ФЗ; ст.15 135-ФЗ',
      },
    ];

    const text = buildComplaintDraft({
      to: 'УФАС по г. Москве',
      from: 'ООО "Участник"',
      tenderNumber: '0445300000123000123',
      customer: 'УФК по г. Москве',
      topic: 'Жалоба на ограничение конкуренции по бренду в документации аукциона',
      ref: 'https://zakupki.gov.ru/..',
      violations,
    });

    expect(text).toContain('ЖАЛОБА В АНТИМОНОПОЛЬНЫЙ ОРГАН НА ДОКУМЕНТАЦИЮ ЗАКУПКИ');
    expect(text).toContain('В: УФАС по г. Москве');
    expect(text).toContain('От: ООО "Участник"');
    expect(text).toContain('Закупка (извещение): 0445300000123000123');
    expect(text).toContain('Заказчик: УФК по г. Москве');
    expect(text).toContain('Жалоба на ограничение конкуренции по бренду');
    expect(text).toContain('п. 1.2.3 ТЗ');
    expect(text).toContain('ч.1 ст.33 44-ФЗ; ст.15 135-ФЗ');
  });
});
