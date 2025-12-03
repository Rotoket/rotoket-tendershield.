/**
 * Отраслевые builder'ы для построения хаба тендерного специалиста
 * для различных сфер: IT, MEDICINE, CONSTRUCTION
 * 
 * Согласно требованиям из warp.md и файла "3 сферы Изучить и применить.md"
 */

import type {
  AnalysisResult,
  TenderHubSummary,
  RequirementItem,
  LegalViolationItem,
  ActionItemVm,
} from '../types';
import { logEvent } from './logger';

/**
 * Специфичные данные для IT сферы
 */
export interface ITIndustryData {
  techStack?: {
    language?: string;
    framework?: string;
    database?: string;
    cloud?: string;
    performance?: string;
    security?: string;
    scalability?: string;
  };
  functionalRequirements?: string[];
  nonFunctionalRequirements?: {
    reliability?: string;
    performance?: string;
    security?: string;
    maintainability?: string;
  };
  sla?: {
    uptime?: string;
    responseTime?: string;
    support?: string;
  };
  developmentStages?: Array<{
    name: string;
    duration: string;
    deliverables: string;
  }>;
}

/**
 * Специфичные данные для Медицины
 */
export interface MedicineIndustryData {
  licenses?: {
    roszdravnadzor?: string;
    ru?: string; // Регистрационное удостоверение
    iso13485?: boolean;
    gost?: string[];
    sanpin?: string[];
  };
  storage?: {
    temperature?: string;
    humidity?: string;
    specialConditions?: string;
  };
  expiry?: {
    required?: boolean;
    minimumRemaining?: string;
  };
  documentation?: {
    instructionsRussian?: boolean;
    certificates?: string[];
  };
  service?: {
    serviceCenter?: string;
    responseTime?: string;
    spareParts?: string;
  };
}

/**
 * Специфичные данные для Строительства
 */
export interface ConstructionIndustryData {
  sro?: {
    required: boolean;
    number?: string;
    expiry?: string;
  };
  materials?: Array<{
    name: string;
    gost?: string;
    requirement: string;
    risk: 'low' | 'medium' | 'high';
  }>;
  stages?: Array<{
    name: string;
    duration: string;
    workType: string;
    penalty?: string;
  }>;
  hiddenWorks?: {
    mentioned: boolean;
    actsRequired?: boolean;
  };
  guarantees?: {
    general?: string;
    roofing?: string;
    defectsPeriod?: string;
  };
}

/**
 * Построение хаба для IT сферы
 */
export const buildITHub = (
  result: AnalysisResult,
  industryData?: ITIndustryData
): Partial<TenderHubSummary> => {
  logEvent('IndustryHubBuilders', 'Построение IT хаба для анализа', 'info', {
    filename: result.passport?.nmck || 'unknown',
  });

  const baseHub: Partial<TenderHubSummary> = {};

  // Red Flags специфичные для IT
  const itRedFlags: TenderHubSummary['redFlagsTop'] = [];

  // Проверка на технологический lock-in
  const techStackIssues = result.issues?.filter(
    (issue) =>
      issue.title.toLowerCase().includes('ограничение конкуренции') ||
      issue.title.toLowerCase().includes('бренд') ||
      issue.title.toLowerCase().includes('только ')
  );

  techStackIssues?.forEach((issue) => {
    itRedFlags.push({
      title: issue.title,
      severity: issue.severity || 'HIGH',
      lawReference: 'ст. 33 44-ФЗ',
      explanation: issue.description,
    });
  });

  // Проверка на смешение товара и ПО
  const mixedLotIssue = result.issues?.find(
    (issue) => issue.title.toLowerCase().includes('смешение')
  );
  if (mixedLotIssue) {
    itRedFlags.push({
      title: mixedLotIssue.title,
      severity: mixedLotIssue.severity || 'HIGH',
      lawReference: 'практика ФАС по 44-ФЗ',
      explanation: mixedLotIssue.description,
    });
  }

  // Требования к участнику для IT (согласно файлу "3 сферы Изучить и применить.md")
  const itRequirements: RequirementItem[] = [];

  // Опыт разработки
  itRequirements.push({
    code: 'EXPERIENCE',
    title: 'Опыт разработки ПО',
    description: 'Требуется опыт выполнения аналогичных проектов. Проверьте наличие портфолио с кейсами, выполненных аналогичных проектов, резюме команды.',
    level: 'strict',
  });

  // Квалификация и компетенции команды
  itRequirements.push({
    code: 'TEAM_QUALIFICATION',
    title: 'Квалификация команды',
    description: 'Требуется наличие ключевого персонала: Lead Developer, DevOps Engineer, Архитектор. Проверьте наличие резюме команды.',
    level: 'strict',
  });

  // Технический стек
  if (industryData?.techStack) {
    if (industryData.techStack.language) {
      const isStrict = result.issues?.some((i) =>
        i.title.toLowerCase().includes('только') &&
        i.description.toLowerCase().includes(industryData.techStack?.language?.toLowerCase() || '')
      );

      itRequirements.push({
        code: 'TECH_STACK',
        title: 'Технологический стек',
        description: `Требуемый язык программирования: ${industryData.techStack.language}. Проверьте соответствие вашим компетенциям.${isStrict ? ' ВНИМАНИЕ: Указано "только" без "или эквивалент" - возможное ограничение конкуренции.' : ''}`,
        level: isStrict ? 'strict' : 'normal',
      });
    }

    if (industryData.techStack.framework) {
      const isStrict = result.issues?.some((i) =>
        i.title.toLowerCase().includes('только') &&
        i.description.toLowerCase().includes(industryData.techStack?.framework?.toLowerCase() || '')
      );

      itRequirements.push({
        code: 'FRAMEWORK',
        title: 'Фреймворк',
        description: `Требуемый фреймворк: ${industryData.techStack.framework}. Убедитесь в совместимости с вашими технологиями.`,
        level: isStrict ? 'strict' : 'normal',
      });
    }

    if (industryData.techStack.database) {
      itRequirements.push({
        code: 'DATABASE',
        title: 'База данных',
        description: `Требуемая БД: ${industryData.techStack.database}. Проверьте возможность использования или адаптации.`,
        level: 'normal',
      });
    }

    if (industryData.techStack.cloud) {
      itRequirements.push({
        code: 'CLOUD',
        title: 'Облачная платформа',
        description: `Требуемое облако: ${industryData.techStack.cloud}. Проверьте наличие сертификатов и опыта работы.`,
        level: 'normal',
      });
    }
  }

  // Нефункциональные требования
  if (industryData?.nonFunctionalRequirements) {
    if (industryData.nonFunctionalRequirements.performance) {
      itRequirements.push({
        code: 'PERFORMANCE',
        title: 'Требования к производительности',
        description: `Производительность: ${industryData.nonFunctionalRequirements.performance}. Проверьте возможность обеспечения требуемых параметров.`,
        level: 'strict',
      });
    }

    if (industryData.nonFunctionalRequirements.security) {
      itRequirements.push({
        code: 'SECURITY',
        title: 'Требования к безопасности',
        description: `Безопасность: ${industryData.nonFunctionalRequirements.security}. Могут требоваться сертификаты ФСТЭК, соответствие требованиям защиты данных.`,
        level: 'strict',
      });
    }
  }

  // SLA и поддержка
  if (industryData?.sla) {
    itRequirements.push({
      code: 'SLA',
      title: 'SLA и гарантийные обязательства',
      description: `Требуемые SLA: uptime ${industryData.sla.uptime || 'не указан'}, время реакции ${industryData.sla.responseTime || 'не указано'}. Проверьте возможность выполнения.`,
      level: 'strict',
    });
  }

  // Сертификаты
  itRequirements.push({
    code: 'CERTIFICATES',
    title: 'Сертификаты и квалификация',
    description: 'Могут потребоваться сертификаты (AWS Solution Architect, Microsoft Certified Developer, ISO, ФСТЭК и т.д.). Проверьте требования в документации.',
    level: 'normal',
  });

  // Reference-клиенты
  itRequirements.push({
    code: 'REFERENCES',
    title: 'Reference-клиенты',
    description: 'Требуется предоставить примеры выполненных проектов с контактами заказчиков для проверки. Проверьте наличие готовности дать рекомендации.',
    level: 'normal',
  });

  // Спецификации для IT
  const itSpecsExamples = result.specs?.slice(0, 3).map((spec) => {
    let riskLevel: 'low' | 'medium' | 'high' = 'medium';
    let riskReason = 'Проверьте технические характеристики на соответствие вашим возможностям.';

    // Проверка на жесткие требования
    if (
      spec.details?.toLowerCase().includes('только') ||
      spec.details?.toLowerCase().includes('обязателен') ||
      spec.details?.toLowerCase().includes('исключительно')
    ) {
      riskLevel = 'high';
      riskReason = 'Жесткое требование к конкретной технологии - возможное ограничение конкуренции.';
    }

    return {
      name: spec.name,
      riskLevel,
      riskReason,
    };
  }) || [];

  // Timeline для IT
  const timelineComment = (result as any).timelineSummary?.timelineRisk ||
    industryData?.developmentStages
    ? `Разработка разбита на ${industryData.developmentStages.length} этапов. Проверьте реалистичность сроков для каждого этапа.`
    : 'Сроки требуют проверки на соответствие объему функционала и ресурсам команды.';

  // Гарантии для IT
  const guaranteeText = industryData?.sla?.uptime
    ? `SLA: uptime ${industryData.sla.uptime}, поддержка ${industryData.sla.support || 'не указана'}`
    : 'Условия SLA и поддержки требуют уточнения.';

  // Финансовая оценка для IT
  const marginComment = (result as any).financialSummary?.marginComment ||
    'Учтите расходы на команду разработчиков, инфраструктуру, лицензии ПО и долгосрочную поддержку.';

  baseHub.redFlagsTop = itRedFlags;
  baseHub.requirements = itRequirements;
  baseHub.specsSummary = {
    totalPositions: result.specs?.length || 0,
    highRiskCount: itSpecsExamples.filter((s) => s.riskLevel === 'high').length,
    examples: itSpecsExamples,
  };
  baseHub.timeline = {
    riskLevel: timelineComment.toLowerCase().includes('нереальн') ||
      timelineComment.toLowerCase().includes('сжатые')
      ? 'critical'
      : 'ok',
    comment: timelineComment,
  };
  baseHub.guarantees = {
    text: guaranteeText,
    riskLevel: industryData?.sla ? 'low' : 'medium',
  };
  baseHub.financial = {
    marginComment,
    lossRiskLevel: 'medium',
  };

  return baseHub;
};

/**
 * Построение хаба для Медицины
 */
export const buildMedicineHub = (
  result: AnalysisResult,
  industryData?: MedicineIndustryData
): Partial<TenderHubSummary> => {
  logEvent('IndustryHubBuilders', 'Построение хаба для медицины', 'info', {
    filename: result.passport?.nmck || 'unknown',
  });

  const baseHub: Partial<TenderHubSummary> = {};

  // Red Flags для медицины
  const medicineRedFlags: TenderHubSummary['redFlagsTop'] = [];

  // Проверка на РУ
  const ruIssue = result.issues?.find(
    (issue) => {
      const titleLower = issue.title.toLowerCase();
      return titleLower.includes('регистрационное удостоверение') ||
        (titleLower.includes('ру') && (titleLower.includes('(ру') || titleLower.includes('ру)') || titleLower.includes('ру ')));
    }
  );
  if (ruIssue) {
    medicineRedFlags.push({
      title: ruIssue.title,
      severity: ruIssue.severity || 'HIGH',
      lawReference: 'Федеральный закон "Об основах охраны здоровья граждан"',
      explanation: ruIssue.description || 'Для медицинских изделий обязательно наличие действующего РУ. Это критичный регуляторный риск.',
    });
  } else if (!industryData?.licenses?.ru) {
    // Если нет явного указания РУ в industryData, создаем предупреждение
    medicineRedFlags.push({
      title: 'Отсутствие требования к регистрационному удостоверению (РУ)',
      severity: 'HIGH',
      lawReference: 'Федеральный закон "Об основах охраны здоровья граждан"',
      explanation: 'Для медицинских изделий обязательно наличие действующего РУ. Это критичный регуляторный риск.',
    });
  }

  // Проверка температурного режима
  const tempIssue = result.issues?.find(
    (issue) => issue.title.toLowerCase().includes('температурный режим')
  );
  if (tempIssue || !industryData?.storage?.temperature) {
    medicineRedFlags.push({
      title: tempIssue?.title || 'Не указан температурный режим хранения/транспортировки',
      severity: 'MEDIUM',
      lawReference: 'СанПиН, ГОСТ',
      explanation: 'Для медицинских изделий/лекарств важно указывать температурный режим хранения и перевозки.',
    });
  }

  // Требования к участнику для медицины
  const medicineRequirements: RequirementItem[] = [];

  medicineRequirements.push({
    code: 'LICENSE',
    title: 'Лицензия на медицинскую деятельность',
    description: 'Требуется лицензия Росздравнадзора на деятельность, связанную с медицинскими изделиями.',
    level: 'blocking',
  });

  if (industryData?.licenses?.ru) {
    medicineRequirements.push({
      code: 'RU',
      title: 'Регистрационное удостоверение (РУ)',
      description: `Требуется действующее РУ: ${industryData.licenses.ru}. Проверьте срок действия.`,
      level: 'blocking',
    });
  }

  medicineRequirements.push({
    code: 'CERTIFICATES',
    title: 'Сертификаты качества',
    description: 'Требуются сертификаты ISO 13485, соответствие ГОСТ и СанПиН. Проверьте наличие у производителя/дистрибьютора.',
    level: 'strict',
  });

  // Команда (согласно файлу)
  medicineRequirements.push({
    code: 'TEAM',
    title: 'Ключевой персонал',
    description: 'Требуется медицинский консультант (обязателен!), технический инженер, специалист по регуляциям. Проверьте наличие в команде.',
    level: 'strict',
  });

  // Представительство в РФ
  medicineRequirements.push({
    code: 'RUSSIAN_OFFICE',
    title: 'Представительство в РФ',
    description: 'Требуется юридический адрес в РФ, сервис-центр или партнеры по регионам. Если только в Москве - выезды в другие регионы будут дороже!',
    level: 'normal',
  });

  medicineRequirements.push({
    code: 'EXPERIENCE',
    title: 'Опыт поставок медицинского оборудования',
    description: 'Требуется опыт поставки медицинского оборудования аналогичного типа. Необходимы референсы и портфолио.',
    level: 'strict',
  });

  // Спецификации с учетом медицины
  const medicineSpecsExamples = result.specs?.slice(0, 3).map((spec) => {
    let riskLevel: 'low' | 'medium' | 'high' = 'medium';
    let riskReason = 'Проверьте соответствие медицинским стандартам и наличие необходимых сертификатов.';

    if (
      spec.name?.toLowerCase().includes('медицинск') ||
      spec.details?.toLowerCase().includes('ру') ||
      spec.details?.toLowerCase().includes('росздравнадзор')
    ) {
      riskLevel = 'high';
      riskReason = 'Требуется проверка наличия РУ и медицинских сертификатов у товара.';
    }

    return {
      name: spec.name,
      riskLevel,
      riskReason,
    };
  }) || [];

  // Timeline для медицины
  const timelineComment = industryData?.storage
    ? 'Учитывайте сроки доставки с соблюдением температурного режима. Проверьте логистические возможности.'
    : 'Сроки поставки и установки медицинского оборудования требуют дополнительной проверки.';

  // Гарантии для медицины
  const guaranteeText = industryData?.service?.serviceCenter
    ? `Гарантийное обслуживание: ${industryData.service.serviceCenter}. Время реакции: ${industryData.service.responseTime || 'не указано'}`
    : 'Требуется уточнение условий гарантийного обслуживания и наличия сервисного центра.';

  baseHub.redFlagsTop = medicineRedFlags;
  baseHub.requirements = medicineRequirements;
  baseHub.specsSummary = {
    totalPositions: result.specs?.length || 0,
    highRiskCount: medicineSpecsExamples.filter((s) => s.riskLevel === 'high').length,
    examples: medicineSpecsExamples,
  };
  baseHub.timeline = {
    riskLevel: timelineComment.toLowerCase().includes('риск') ? 'tight' : 'ok',
    comment: timelineComment,
  };
  baseHub.guarantees = {
    text: guaranteeText,
    riskLevel: industryData?.service?.serviceCenter ? 'low' : 'medium',
  };

  return baseHub;
};

/**
 * Построение хаба для Строительства
 */
export const buildConstructionHub = (
  result: AnalysisResult,
  industryData?: ConstructionIndustryData
): Partial<TenderHubSummary> => {
  logEvent('IndustryHubBuilders', 'Построение хаба для строительства', 'info', {
    filename: result.passport?.nmck || 'unknown',
  });

  const baseHub: Partial<TenderHubSummary> = {};

  // Red Flags для строительства
  const constructionRedFlags: TenderHubSummary['redFlagsTop'] = [];

  // Проверка СРО
  if (!industryData?.sro?.required || !industryData?.sro?.number) {
    constructionRedFlags.push({
      title: 'Отсутствие требования к СРО или не указан номер',
      severity: 'CRITICAL',
      lawReference: 'Градостроительный кодекс РФ',
      explanation: 'Для строительных работ обязательно наличие действующего свидетельства СРО. Без этого участие невозможно.',
    });
  }

  // Проверка на жесткие штрафы
  const penaltyIssues = result.issues?.filter(
    (issue) =>
      issue.title.toLowerCase().includes('штраф') ||
      issue.title.toLowerCase().includes('неустойка') ||
      issue.severity === 'HIGH'
  );

  penaltyIssues?.forEach((issue) => {
    constructionRedFlags.push({
      title: issue.title,
      severity: issue.severity || 'HIGH',
      lawReference: 'ст. 34 44-ФЗ',
      explanation: issue.description,
    });
  });

  // Проверка на скрытые работы
  if (industryData?.hiddenWorks?.mentioned && !industryData.hiddenWorks.actsRequired) {
    constructionRedFlags.push({
      title: 'Скрытые работы без процедуры оформления актов',
      severity: 'MEDIUM',
      lawReference: 'практика ФАС и строительные нормы',
      explanation: 'Упоминаются скрытые работы, но нет явного описания порядка оформления актов освидетельствования.',
    });
  }

  // Требования к участнику для строительства
  const constructionRequirements: RequirementItem[] = [];

  constructionRequirements.push({
    code: 'SRO',
    title: 'Свидетельство СРО',
    description: industryData?.sro?.number
      ? `Требуется свидетельство СРО: ${industryData.sro.number}. Проверьте актуальность и срок действия.`
      : 'Требуется действующее свидетельство СРО строительного профиля. Это обязательное требование.',
    level: 'blocking',
  });

  constructionRequirements.push({
    code: 'EXPERIENCE',
    title: 'Опыт строительных работ',
    description: 'Требуется опыт выполнения аналогичных строительных работ. Нужны примеры объектов и референсы.',
    level: 'strict',
  });

  constructionRequirements.push({
    code: 'CERTIFICATES',
    title: 'Сертификаты и лицензии',
    description: 'Могут требоваться сертификаты ISO 9001, лицензии на виды работ (электромонтаж, водопровод и т.д.).',
    level: 'normal',
  });

  // Спецификации материалов
  const constructionSpecsExamples = result.specs?.slice(0, 3).map((spec) => {
    let riskLevel: 'low' | 'medium' | 'high' = 'medium';
    let riskReason = 'Проверьте соответствие ГОСТ, наличие материалов и возможность поставки в срок.';

    // Проверка на жесткие требования к маркам без эквивалентов
    if (
      spec.details?.toLowerCase().includes('только') ||
      spec.details?.toLowerCase().includes('исключительно')
    ) {
      if (!spec.details.toLowerCase().includes('или эквивалент')) {
        riskLevel = 'high';
        riskReason = 'Жесткое требование к конкретной марке без допуска эквивалентов - возможное ограничение конкуренции.';
      }
    }

    return {
      name: spec.name,
      riskLevel,
      riskReason,
    };
  }) || [];

  // Timeline для строительства
  const stagesCount = industryData?.stages?.length || 0;
  const timelineComment = stagesCount > 0
    ? `Работы разбиты на ${stagesCount} этапов. Проверьте реалистичность сроков с учетом сезонности и погодных условий.`
    : 'Сроки выполнения строительных работ требуют проверки на соответствие объемам и сезонности.';

  // Гарантии для строительства
  const guaranteeText = industryData?.guarantees?.general
    ? `Гарантия: ${industryData.guarantees.general}${industryData.guarantees.roofing ? `, кровля: ${industryData.guarantees.roofing}` : ''}`
    : 'Требуется уточнение гарантийных обязательств, особенно для скрытых работ.';

  baseHub.redFlagsTop = constructionRedFlags;
  baseHub.requirements = constructionRequirements;
  baseHub.specsSummary = {
    totalPositions: result.specs?.length || 0,
    highRiskCount: constructionSpecsExamples.filter((s) => s.riskLevel === 'high').length,
    examples: constructionSpecsExamples,
  };
  baseHub.timeline = {
    riskLevel: timelineComment.toLowerCase().includes('сжатые') ||
      timelineComment.toLowerCase().includes('риск')
      ? 'critical'
      : 'ok',
    comment: timelineComment,
  };
  baseHub.guarantees = {
    text: guaranteeText,
    riskLevel: industryData?.guarantees ? 'low' : 'medium',
  };

  return baseHub;
};

/**
 * Извлечение отраслевых данных из AnalysisResult
 * Использует эвристический анализ на основе issues, specs, redFlags и других полей
 */
export const extractIndustryData = (
  result: AnalysisResult,
  industry: 'IT' | 'CONSTRUCTION' | 'MEDICINE' | 'UNIVERSAL'
): ITIndustryData | MedicineIndustryData | ConstructionIndustryData | undefined => {
  if (industry === 'IT') {
    const data: ITIndustryData = {};

    // Извлекаем технический стек из specs и issues
    const allText = [
      ...(result.specs || []).map((s) => `${s.name} ${s.details}`),
      ...(result.issues || []).map((i) => `${i.title} ${i.description}`),
    ].join(' ').toLowerCase();

    // Поиск языков программирования
    const languages = ['python', 'java', 'javascript', 'typescript', 'golang', 'rust', 'php', 'c#', 'c++'];
    const foundLanguage = languages.find((lang) => allText.includes(lang));
    if (foundLanguage) {
      data.techStack = { language: foundLanguage };
    }

    // Поиск фреймворков
    const frameworks = ['django', 'fastapi', 'react', 'vue', 'angular', 'spring', 'laravel'];
    const foundFramework = frameworks.find((fw) => allText.includes(fw));
    if (foundFramework) {
      data.techStack = { ...data.techStack, framework: foundFramework };
    }

    // Извлекаем этапы разработки из timelineSummary
    if ((result as any).timelineSummary) {
      // Можно добавить парсинг этапов, если они структурированы
    }

    return data;
  }

  if (industry === 'MEDICINE') {
    const data: MedicineIndustryData = {};

    const allText = [
      ...(result.specs || []).map((s) => `${s.name} ${s.details}`),
      ...(result.issues || []).map((i) => `${i.title} ${i.description}`),
    ].join(' ').toLowerCase();

    // Поиск упоминаний РУ
    if (allText.includes('регистрационное удостоверение') || allText.includes('ру ')) {
      data.licenses = { ru: 'Требуется РУ' };
    }

    // Поиск температурного режима
    const tempMatch = allText.match(/(температур[^\s]+ режим|хранени[^\s]+ при|2-8[°с]|15-25[°с])/i);
    if (tempMatch) {
      data.storage = { temperature: tempMatch[0] };
    }

    // Поиск срока годности
    if (allText.includes('срок годност') || allText.includes('остаточный срок')) {
      data.expiry = { required: true };
    }

    return data;
  }

  if (industry === 'CONSTRUCTION') {
    const data: ConstructionIndustryData = {
      sro: {
        required: true,
      },
    };

    const allText = [
      ...(result.specs || []).map((s) => `${s.name} ${s.details}`),
      ...(result.issues || []).map((i) => `${i.title} ${i.description}`),
    ].join(' ').toLowerCase();

    // Поиск упоминаний СРО
    if (allText.includes('сро ') || allText.includes('саморегулируем')) {
      data.sro = { required: true };
    }

    // Поиск скрытых работ
    if (allText.includes('скрыт') || allText.includes('скрытые работы')) {
      data.hiddenWorks = {
        mentioned: true,
        actsRequired: allText.includes('акт освидетельствования'),
      };
    }

    // Извлекаем материалы из specs
    if (result.specs && result.specs.length > 0) {
      data.materials = result.specs.slice(0, 5).map((spec) => ({
        name: spec.name,
        requirement: spec.details,
        risk: spec.details?.toLowerCase().includes('только') && !spec.details?.toLowerCase().includes('или эквивалент')
          ? 'high' as const
          : 'medium' as const,
      }));
    }

    return data;
  }

  return undefined;
};

