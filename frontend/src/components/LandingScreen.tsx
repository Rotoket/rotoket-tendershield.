import React, { useState } from 'react';
import { Play, LogIn, BookOpen } from 'lucide-react';
import { bootstrapDemoSession } from '../utils/demoBootstrap';
import Tooltip from './Tooltip';
import TenderShieldLogo from './TenderShieldLogo';

interface LandingScreenProps {
  onStartAnalysis: () => void;
  onShowAuth?: () => void;
  onShowHistory?: () => void;
}

const LandingScreen: React.FC<LandingScreenProps> = ({ onStartAnalysis, onShowAuth, onShowHistory }) => {
  type LegalDocKey =
    | 'terms'
    | 'privacy'
    | 'personalDataPolicy'
    | 'personalDataConsent';

  const [activeLegalDoc, setActiveLegalDoc] = useState<LegalDocKey | null>(null);

  const handleStartAnalysis = () => {
    console.log('[LandingScreen] handleStartAnalysis called');
    try {
      bootstrapDemoSession();
      console.log('[LandingScreen] Demo session created');
    } catch (error) {
      console.error('[LandingScreen] Ошибка при создании demo-сессии:', error);
    }
    
    onStartAnalysis();
  };

  return (
    <div className="h-screen bg-[#0B0F14] flex flex-col" style={{ overflow: 'auto' }}>
      {/* Основной контент */}
      <div className="flex-1 flex items-center justify-center px-6 py-6 overflow-visible" style={{ overflow: 'visible' }}>
        <div className="max-w-[1600px] mx-auto w-full h-full">
          <div className="grid grid-cols-1 lg:grid-cols-[1.2fr,2.6fr,1.2fr] gap-4 h-full items-center">
            {/* ЛЕВАЯ КОЛОНКА: Профиль риска */}
            <div className="hidden lg:flex flex-col h-full max-h-[80vh]" style={{ overflow: 'visible' }}>
              <div className="bg-[#111821] border border-[#1F2933] border-l-4 border-l-[#F97316] rounded-[3px] px-5 py-6 flex flex-col h-full shadow-lg">
                <div className="border-b border-[#1F2933] pb-3 mb-4">
                  <p className="text-xs font-semibold text-slate-200 uppercase tracking-[0.2em]">
                    Профиль риска
                  </p>
                </div>
                <div className="space-y-4 flex-1 flex flex-col">
                  {/* Система позволяет */}
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-[0.1em] mb-2">Система позволяет:</p>
                    <div className="space-y-1.5 text-base text-slate-300 leading-tight">
                      <div>— проанализировать тендерную документацию;</div>
                      <div>— выявить критические стоп-факторы;</div>
                      <div>— отделить контролируемые риски от некритичных рыночных условий;</div>
                      <div>— сформировать управленческое решение;</div>
                      <div>— зафиксировать основания и контекст принятия решения.</div>
                    </div>
                  </div>

                  {/* Применение */}
                  <div className="bg-[#0E1318] border border-[#1F2933] rounded-[2px] p-3">
                    <p className="text-xs text-slate-300 leading-tight">
                      Система применяется там, где участие в тендере является управленческим риском.
                    </p>
                  </div>

                  {/* Фиксация решения */}
                  <Tooltip
                    content="Зафиксированное решение становится неизменяемым корпоративным актом. Любое изменение условий требует создания новой записи в журнале аудита, не отменяющей предыдущую."
                  >
                    <div className="bg-[#1A0F0A] border border-[#F97316]/20 rounded-[2px] p-3 cursor-help mt-auto">
                      <p className="text-xs text-[#F97316] leading-tight font-medium">
                        Решение фиксируется. <span className="font-bold">Ответственность — за директором</span>.
                      </p>
                    </div>
                  </Tooltip>
                </div>
              </div>
            </div>

            {/* ЦЕНТРАЛЬНАЯ ЗОНА: Hero */}
            <div className="flex flex-col justify-center space-y-5 h-full max-h-[80vh] px-4 overflow-visible">
              {/* Логотип и название (вместо header) */}
              <div className="flex items-center justify-center gap-3 mb-2">
                <TenderShieldLogo className="w-10 h-10 flex-shrink-0" />
                <div className="border-l border-[#2A3441] pl-3">
                  <h1 className="text-2xl font-semibold text-slate-100 tracking-tight">Тендер.Щит</h1>
                  <p className="text-base text-slate-400">Система управленческих решений</p>
                </div>
              </div>

              {/* Разделитель */}
              <div className="hidden lg:block border-t border-[#1F2933] w-16 mx-auto"></div>

              {/* Смысловой якорь */}
              <div className="text-center">
                <h2 className="text-3xl md:text-4xl lg:text-5xl font-semibold text-slate-50 leading-tight tracking-tight">
                  Решение важнее анализа
                </h2>
              </div>

              {/* Подзаголовок */}
              <h3 className="text-xl md:text-2xl text-slate-300 text-center leading-tight">
                Управленческое решение по тендеру<br />
                на основе зафиксированных факторов риска
              </h3>

              {/* Краткий абзац */}
              <Tooltip
                content="Принцип &quot;Decision &gt; Analysis&quot;: Мы исключаем субъективные советы AI, чтобы предоставить директору только проверенные факты для самостоятельного, юридически значимого решения."
              >
                <div className="bg-[#111821] border border-[#1F2933] rounded-[3px] p-4 max-w-2xl mx-auto cursor-help">
                  <p className="text-sm text-slate-400 text-center leading-relaxed">
                    Система выявляет <span className="text-slate-300 font-medium">блокирующие факторы</span>, объясняет причины решения, обеспечивает воспроизводимость вывода и фиксирует <span className="text-slate-300 font-medium">журнал аудита</span>.
                    Итоговое <span className="font-medium text-slate-200">управленческое решение</span> всегда остаётся за директором.
                  </p>
                </div>
              </Tooltip>

              {/* CTA-зона */}
              <div className="space-y-3 pt-2">
                <button
                  type="button"
                  onClick={handleStartAnalysis}
                  className="w-full max-w-md mx-auto px-6 py-3.5 bg-[#4A6F85] hover:bg-[#3A596B] text-[#E2E8F0] text-base font-medium rounded-[3px] transition-colors flex items-center justify-center gap-2 shadow-lg border border-[#3A596B]/50"
                >
                  <Play size={20} />
                  Инициировать анализ
                </button>

                {onShowHistory && (
                  <button
                    type="button"
                    onClick={onShowHistory}
                    className="w-full max-w-md mx-auto px-6 py-3.5 bg-[#1F2933] hover:bg-[#2A3441] border border-[#2A3441] hover:border-[#3A4A5A] text-slate-200 text-base font-medium rounded-[3px] transition-all flex items-center justify-center gap-2"
                  >
                    <BookOpen size={20} />
                    Журнал управленческих решений
                  </button>
                )}

                {onShowAuth && (
                  <div className="text-center pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        console.log('[LandingScreen] onShowAuth button clicked');
                        onShowAuth();
                      }}
                      className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                    >
                      Войти в систему
                    </button>
                  </div>
                )}
              </div>

              {/* Разделитель */}
              <div className="hidden lg:block border-t border-[#1F2933] w-16 mx-auto"></div>
            </div>

            {/* ПРАВАЯ КОЛОНКА: Контур управленческого решения */}
            <div className="hidden lg:flex flex-col h-full max-h-[80vh]" style={{ overflow: 'visible' }}>
              <div className="bg-[#111821] border border-[#1F2933] rounded-[3px] px-5 py-6 flex flex-col h-full shadow-lg">
                <div className="border-b border-[#1F2933] pb-3 mb-4">
                  <p className="font-semibold uppercase tracking-[0.15em] text-slate-300 text-xs">
                    Контур управленческого решения
                  </p>
                </div>
                <div className="space-y-5 flex-1 flex flex-col">
                  {/* 1. ВОЗМОЖНЫЕ РЕШЕНИЯ */}
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-[0.1em] mb-2">
                      Возможные решения
                    </p>
                    <div className="space-y-1.5">
                      <div className="text-xs text-slate-300 leading-tight">— УЧАСТВОВАТЬ</div>
                      <div className="text-xs text-slate-300 leading-tight">— НЕ УЧАСТВОВАТЬ</div>
                      <div className="text-xs text-slate-300 leading-tight">— УЧАСТВОВАТЬ С УСЛОВИЯМИ</div>
                      <div className="text-xs text-slate-300 leading-tight">— ОТЛОЖИТЬ РЕШЕНИЕ</div>
                    </div>
                  </div>

                  {/* 2. ОСНОВАНИЯ РЕШЕНИЯ */}
                  <div>
                    <p className="text-xs font-medium text-slate-400 uppercase tracking-[0.1em] mb-2">
                      Основания решения
                    </p>
                    <div className="space-y-1.5">
                      <div className="text-xs text-slate-300 leading-tight">— Блокирующие факторы</div>
                      <Tooltip
                        content="Анализ трансформируется в Индекс управленческой нагрузки — показатель сложности и объёма управленческого контроля, необходимого для принятия решения."
                      >
                        <div className="text-xs text-slate-300 leading-tight cursor-help">— Индекс управленческой нагрузки</div>
                      </Tooltip>
                      <div className="text-xs text-slate-300 leading-tight">— Противоречия условий договора</div>
                      <Tooltip
                        content="Неизменяемый цифровой след (append-only log). Фиксирует управленческие решения и формирует доказательную базу для совета директоров, аудита и защиты ответственности."
                      >
                        <div className="text-xs text-slate-300 leading-tight cursor-help">— Журнал аудита</div>
                      </Tooltip>
                    </div>
                  </div>

                  {/* 3. ФИКСАЦИЯ */}
                  <div className="mt-auto pt-4 border-t border-[#1F2933]">
                    <p className="text-xs text-slate-400 leading-tight italic">
                      Решение фиксируется и не пересматривается задним числом
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer: Полные юридические тексты */}
      <footer className="flex-shrink-0 border-t border-[#1F2933] py-6 px-8 bg-[#0E1318]">
        <div className="max-w-[1600px] mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-sm text-slate-500">
            {/* Блок 1: Документы */}
            <div className="space-y-3">
              <p className="uppercase tracking-[0.16em] text-xs text-slate-400">
                Документы
              </p>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => setActiveLegalDoc('terms')}
                  className="block text-left hover:text-slate-300 transition-colors"
                >
                  Пользовательское соглашение
                </button>
                <button
                  type="button"
                  onClick={() => setActiveLegalDoc('privacy')}
                  className="block text-left hover:text-slate-300 transition-colors"
                >
                  Политика конфиденциальности
                </button>
                <button
                  type="button"
                  onClick={() => setActiveLegalDoc('personalDataPolicy')}
                  className="block text-left hover:text-slate-300 transition-colors"
                >
                  Политика обработки персональных данных
                </button>
                <button
                  type="button"
                  onClick={() => setActiveLegalDoc('personalDataConsent')}
                  className="block text-left hover:text-slate-300 transition-colors"
                >
                  Согласие на обработку персональных данных
                </button>
              </div>
            </div>

            {/* Блок 2: Юридическая информация и дисклеймеры (152-ФЗ и разъяснения) */}
            <div className="space-y-3">
              <p className="uppercase tracking-[0.16em] text-xs text-slate-400">
                Юридическая информация
              </p>
              <div className="space-y-2 leading-relaxed text-sm">
                <p>
                  Система «Тендер.Щит» обрабатывает персональные данные в соответствии с
                  Федеральным законом от 27.07.2006 № 152-ФЗ «О персональных данных» и
                  иными применимыми нормами законодательства Российской Федерации.
                </p>
              </div>
            </div>

            {/* Блок 3: Служебная информация */}
            <div className="space-y-3 md:text-right">
              <p className="uppercase tracking-[0.16em] text-xs text-slate-400">
                Служебная информация
              </p>
              <div className="space-y-2">
                <p>© 2025 Тендер.Щит</p>
                {onShowAuth && (
                  <button
                    type="button"
                    onClick={() => {
                      console.log('[LandingScreen] footer auth link clicked');
                      onShowAuth();
                    }}
                    className="text-slate-400 hover:text-slate-200 underline transition-colors"
                  >
                    Вход в систему
                  </button>
                )}
                <p className="text-xs text-slate-500">
                  Язык интерфейса: <span className="text-slate-300">RU</span> / EN
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>

      {/* Модальное окно для юридических документов */}
      {activeLegalDoc && (
        <div
          className="fixed inset-0 bg-black/60 flex items-center justify-center z-40"
          aria-modal="true"
          role="dialog"
          onClick={() => setActiveLegalDoc(null)}
        >
          <div 
            className="bg-[#0B0F14] border border-[#1F2933] rounded-[4px] max-w-2xl w-full mx-4 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#1F2933]">
              <h3 className="text-sm font-semibold text-slate-100 tracking-wide">
                {activeLegalDoc === 'terms' && 'Пользовательское соглашение'}
                {activeLegalDoc === 'privacy' && 'Политика конфиденциальности'}
                {activeLegalDoc === 'personalDataPolicy' && 'Политика обработки персональных данных'}
                {activeLegalDoc === 'personalDataConsent' && 'Согласие на обработку персональных данных'}
              </h3>
              <button
                type="button"
                onClick={() => setActiveLegalDoc(null)}
                className="text-slate-400 hover:text-slate-200 text-xs uppercase tracking-[0.16em] transition-colors"
              >
                Закрыть
              </button>
            </div>
            <div className="px-5 py-4 max-h-[70vh] overflow-y-auto text-sm text-slate-300 space-y-3">
              {activeLegalDoc === 'terms' && (
                <>
                  <p className="font-semibold">Пользовательское соглашение</p>
                  <p>
                    Настоящее Пользовательское соглашение (далее — «Соглашение») регулирует порядок использования
                    информационной системы «Тендер.Щит» (далее — «Система»).
                  </p>
                  <p>
                    Система предназначена для аналитической поддержки и фиксации управленческих решений по тендерам и
                    закупочным процедурам.
                  </p>
                  <p>Система:</p>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    <li>не принимает управленческих решений;</li>
                    <li>не формирует обязательных рекомендаций;</li>
                    <li>не является юридической, финансовой или иной профессиональной консультацией;</li>
                    <li>не гарантирует выигрыш, юридическую чистоту, отсутствие рисков или рыночный успех.</li>
                  </ul>
                  <p>
                    Все решения, принимаемые с использованием Системы, остаются в исключительной ответственности
                    руководителя организации либо иного уполномоченного лица.
                  </p>
                  <p>Используя Систему, пользователь подтверждает, что:</p>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    <li>понимает вспомогательный характер аналитических материалов;</li>
                    <li>принимает на себя полную ответственность за принимаемые решения;</li>
                    <li>использует Систему в рамках действующего законодательства Российской Федерации.</li>
                  </ul>
                  <p className="text-slate-400 text-xs">
                    Администрация Системы оставляет за собой право вносить изменения в функциональность и содержание
                    Системы без предварительного уведомления пользователей.
                  </p>
                </>
              )}

              {activeLegalDoc === 'privacy' && (
                <>
                  <p className="font-semibold">Политика конфиденциальности</p>
                  <p>
                    Настоящая Политика конфиденциальности определяет порядок обработки и защиты информации, получаемой
                    при использовании Системы «Тендер.Щит».
                  </p>
                  <p>Система обрабатывает информацию исключительно в целях:</p>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    <li>аналитической оценки тендерной документации;</li>
                    <li>формирования управленческого контура решений;</li>
                    <li>фиксации контекста и оснований управленческих решений.</li>
                  </ul>
                  <p>
                    Система не передаёт данные третьим лицам, за исключением случаев, предусмотренных законодательством
                    Российской Федерации.
                  </p>
                  <p className="text-slate-400 text-xs">
                    Все технические и организационные меры по защите информации принимаются в соответствии с
                    требованиями действующего законодательства Российской Федерации.
                  </p>
                </>
              )}

              {activeLegalDoc === 'personalDataPolicy' && (
                <>
                  <p className="font-semibold">Политика обработки персональных данных</p>
                  <p>
                    Обработка персональных данных в Системе «Тендер.Щит» осуществляется в соответствии с Федеральным
                    законом от 27.07.2006 № 152-ФЗ «О персональных данных».
                  </p>
                  <p>Обрабатываемые персональные данные могут включать:</p>
                  <ul className="list-disc list-inside space-y-1 text-slate-300">
                    <li>фамилию, имя, отчество;</li>
                    <li>должность;</li>
                    <li>рабочие контактные данные;</li>
                    <li>иную информацию, предоставляемую пользователем в рамках использования Системы.</li>
                  </ul>
                  <p>
                    Обработка персональных данных осуществляется исключительно в целях функционирования Системы и
                    исполнения её заявленного назначения.
                  </p>
                  <p className="text-slate-400 text-xs">
                    Персональные данные не используются для маркетинговых целей и не передаются третьим лицам без
                    законных оснований.
                  </p>
                </>
              )}

              {activeLegalDoc === 'personalDataConsent' && (
                <>
                  <p className="font-semibold">Согласие на обработку персональных данных</p>
                  <p>
                    Пользователь, используя Систему «Тендер.Щит», выражает согласие на обработку своих персональных
                    данных в соответствии с Политикой обработки персональных данных.
                  </p>
                  <p>
                    Согласие предоставляется на срок использования Системы и может быть отозвано пользователем в
                    порядке, предусмотренном законодательством Российской Федерации.
                  </p>
                </>
              )}

              <p className="text-xs text-slate-500">
                Тексты правовых документов и дисклеймеров являются базовой редакцией и подлежат уточнению в рамках
                юридической экспертизы.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LandingScreen;
