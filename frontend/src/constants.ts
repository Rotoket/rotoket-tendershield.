import { Tender, TenderStatus } from './types';

export const MOCK_TENDERS: Tender[] = [
  {
    id: 't-123456',
    title: 'Поставка серверного оборудования и СХД для нужд Министерства Цифрового Развития',
    customer: 'Минцифры России',
    price: 15430000,
    deadline: '2023-11-15',
    fz: '44-ФЗ',
    status: TenderStatus.NEW,
    winRate: 85,
    riskScore: 12,
    description: 'Закупка серверов архитектуры x86-64, систем хранения данных. Требуется наличие в реестре Минпромторга.',
    requirements: ['Реестр РЭП', 'Лицензия ФСТЭК', 'Обеспечение заявки 5%']
  },
  {
    id: 't-987654',
    title: 'Оказание услуг по разработке и внедрению информационной системы мониторинга транспорта',
    customer: 'АО "РЖД"',
    price: 8750000,
    deadline: '2023-11-20',
    fz: '223-ФЗ',
    status: TenderStatus.ANALYZING,
    winRate: 45,
    riskScore: 78,
    description: 'Разработка ПО, интеграция с существующими системами, техподдержка 12 мес.',
    requirements: ['Опыт работы от 3 лет', 'Наличие ISO 9001', 'Штрафы за просрочку 0.5% в день']
  },
  {
    id: 't-555111',
    title: 'Выполнение работ по капитальному ремонту кровли административного здания',
    customer: 'ГБУ "Жилищник"',
    price: 4200000,
    deadline: '2023-11-10',
    fz: '44-ФЗ',
    status: TenderStatus.READY,
    winRate: 62,
    riskScore: 45,
    description: 'Демонтаж старого покрытия, укладка мембраны, ремонт водостоков.',
    requirements: ['СРО Строительство', 'Опыт исполнения контрактов']
  }
];

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Дашборд', icon: 'LayoutDashboard' },
  { id: 'tenders', label: 'Поиск тендеров', icon: 'Search' },
  { id: 'applications', label: 'Мои заявки', icon: 'FileText' },
  { id: 'analytics', label: 'Аналитика', icon: 'BarChart3' },
  { id: 'lawyer', label: 'Правовой контроль', icon: 'Scale' },
];
