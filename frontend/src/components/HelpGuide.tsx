import React from 'react';
import {
  FileSearch,
  FileText,
  Calculator,
  BookOpen,
  Clock,
  Bot,
  Zap,
  CheckSquare,
  AlertTriangle,
  Star,
  ArrowLeft,
} from 'lucide-react';

interface HelpGuideProps {
  onBack?: () => void;
}

const HelpGuide: React.FC<HelpGuideProps> = ({ onBack }) => {
  return (
    <div className="animate-fade-in max-w-5xl mx-auto pb-12 overflow-y-auto h-full pr-2 custom-scrollbar">
      {/* Кнопка назад */}
      {onBack && (
        <button
          onClick={onBack}
          className="mb-6 flex items-center gap-2 text-[#00d4ff] hover:text-[#00b3e0] transition-colors"
        >
          <ArrowLeft size={20} />
          <span className="text-sm font-medium">Вернуться к анализу</span>
        </button>
      )}
      {/* Header */}
      <div className="mb-10 text-center">
        <h2 className="text-4xl font-bold text-white mb-4">Справочный центр Tender.Щит.AI</h2>
        <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
          Этот раздел подскажет, как быстро пройти путь от загрузки тендерной документации до
          готовых решений: аудита, документов и расчёта маржи.
        </p>
      </div>

      {/* Section 1: Анализ одного документа */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#00d4ff]/10 rounded-2xl flex items-center justify-center text-[#00d4ff]">
            <FileSearch size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">1. Умный аудит одного документа</h3>
            <p className="text-slate-400">
              Главный инструмент для экспресс‑проверки проекта контракта, ТЗ или одного файла из
              пакета.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="font-bold text-white text-lg mb-3">Как запустить проверку</h4>
            <ol className="list-decimal list-inside space-y-3 text-slate-200 text-base leading-relaxed">
              <li>Откройте вкладку «Анализ документа» в левом меню.</li>
              <li>
                В блоке справа сверху выберите <strong>сферу тендера</strong>:
                «Универсальный», «IT», «Строительство» или «Медицина». От этого зависят чек‑листы.
              </li>
              <li>
                Загрузите файл через большую область в центре: поддерживаются{' '}
                <span className="font-mono bg-[#0f1419] px-1.5 rounded">
                  .pdf, .doc, .docx, .txt, .rtf, .xls, .xlsx
                </span>
                .
              </li>
              <li>
                Дождитесь завершения шагов анализа (полоска прогресса сверху). Обычно это занимает
                от 10 до 40 секунд.
              </li>
              <li>
                Изучите:
                <br />
                – «Паспорт тендера» (НМЦК, аванс, обеспечение, сроки, регион)
                <br />– «Глубокий аудит» — раскрывающиеся блоки с рисками и рекомендациями.
              </li>
            </ol>
          </div>

          <div className="bg-[#0f1419] p-6 rounded-xl border border-[#2a3441]">
            <h4 className="font-bold text-white mb-4 flex items-center gap-2">
              <Zap size={18} className="text-[#f59e0b]" /> Индекс безопасности (0–100)
            </h4>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-3">
                <span className="font-bold text-[#00e648] min-w-[90px]">0–50 (Зелёный)</span>
                <span className="text-slate-300">
                  Низкий риск. Условия в целом стандартные, можно идти дальше к расчёту маржи.
                </span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#f59e0b] min-w-[90px]">51–80 (Жёлтый)</span>
                <span className="text-slate-300">
                  Есть спорные штрафы, сроки или требования. Рекомендуется доработка условий или
                  запрос разъяснений.
                </span>
              </li>
              <li className="flex gap-3">
                <span className="font-bold text-[#ff4444] min-w-[90px]">81–100 (Красный)</span>
                <span className="text-slate-300">
                  Высокий риск убытков или попадания в РНП. Просмотрите красные блоки в «Глубоком
                  аудите» и подумайте о протоколе разногласий или жалобе.
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Section 2: Комплексный аудит пакета */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#6366f1]/10 rounded-2xl flex items-center justify-center text-[#6366f1]">
            <FileSearch size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">2. Комплексный аудит пакета</h3>
            <p className="text-slate-400">
              Проверка сразу нескольких файлов (ТЗ, контракт, проект заявки, сметы) с единой
              сводкой по рискам.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h4 className="font-bold text-white text-lg mb-3">Когда использовать</h4>
            <ul className="list-disc list-inside space-y-2 text-slate-200 text-base leading-relaxed">
              <li>Перед подачей заявки, когда есть полный пакет документов.</li>
              <li>Если нужно увидеть, как условия «играют вместе»: штрафы + сроки + обеспечение.</li>
              <li>Когда в тендере много файлов и сложно понять, где именно главный риск.</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white text-lg mb-3">Что вы получите</h4>
            <ul className="space-y-2 text-slate-200 text-sm leading-relaxed">
              <li>– Общий индекс безопасности по пакету.</li>
              <li>– Список глобальных рисков с пояснениями.</li>
              <li>– Подсветку самых опасных документов и позиций.</li>
              <li>– Рекомендации: участвовать, уточнить, готовить разногласия или жалобу.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Section 3: Генератор документов */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#00e648]/10 rounded-2xl flex items-center justify-center text-[#00e648]">
            <FileText size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">3. Генератор документов</h3>
            <p className="text-slate-400">
              Помогает быстрее подготовить черновики юридических документов на основе анализа.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 border border-[#2a3441] rounded-xl bg-[#0f1419]">
            <div className="flex items-center gap-2 font-bold text-white mb-2">
              <CheckSquare size={20} className="text-[#00d4ff]" /> Протокол разногласий
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              Заполните, с чем конкретно вы не согласны в проекте контракта, — система соберёт
              таблицу разногласий и сформирует связный текст, который можно приложить к ответу
              заказчику.
            </p>
          </div>

          <div className="p-4 border border-[#2a3441] rounded-xl bg-[#0f1419]">
            <div className="flex items-center gap-2 font-bold text-white mb-2">
              <FileText size={20} className="text-[#f59e0b]" /> Жалоба в ФАС
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              Подходит, когда выявлены грубые нарушения (ограничение конкуренции, избыточные
              требования и т.п.). Результат — структурированный черновик, который нужно проверить
              с юристом.
            </p>
          </div>

          <div className="p-4 border border-[#2a3441] rounded-xl bg-[#0f1419]">
            <div className="flex items-center gap-2 font-bold text-white mb-2">
              <BookOpen size={20} className="text-[#22c55e]" /> Как использовать безопасно
            </div>
            <p className="text-slate-300 text-sm leading-relaxed">
              Все тексты, которые формирует Tender.Щит.AI, — это <strong>черновики</strong>.
              Перед отправкой заказчику или в ФАС обязательно проверьте формулировки и реквизиты.
            </p>
          </div>
        </div>
      </div>

      {/* Section 4: Калькулятор маржинальности */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#f59e0b]/10 rounded-2xl flex items-center justify-center text-[#f59e0b]">
            <Calculator size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">4. Калькулятор маржинальности</h3>
            <p className="text-slate-400">
              Помогает понять, сколько вы реально заработаете с учётом рисков по контракту.
            </p>
          </div>
        </div>

        <div className="text-slate-200 leading-relaxed space-y-4">
          <p>
            После завершения анализа вы можете открыть «Калькулятор» и нажать кнопку{' '}
            <span className="font-mono bg-[#0f1419] px-2 rounded">«Заполнить из анализа»</span>. Мы
            подтянем НМЦК и ориентировочную себестоимость.
          </p>
          <p>
            Обычный подход: <span className="font-mono bg-[#0f1419] px-2 rounded">
              Цена − Расходы = Прибыль
            </span>
            .
          </p>
          <p>
            В Tender.Щит.AI дополнительно учитывается{' '}
            <span className="text-[#ff4444] font-bold">риск потерь</span>, связанный с условиями
            контракта (штрафы, обеспечение, сроки). Если система оценила риск высоко,{' '}
            <strong>скорректированная прибыль</strong> может уйти в минус — это повод пересмотреть
            участие или условия.
          </p>
        </div>
      </div>

      {/* Section 5: История, база знаний и демо‑режим */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#38bdf8]/10 rounded-2xl flex items-center justify-center text-[#38bdf8]">
            <Clock size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">5. История и база знаний</h3>
            <p className="text-slate-400">
              Все ваши проверки и юридические материалы доступны прямо в интерфейсе.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-bold text-white text-lg mb-3 flex items-center gap-2">
              <Clock size={18} className="text-[#38bdf8]" /> История проверок
            </h4>
            <p className="text-slate-300 text-sm leading-relaxed mb-3">
              Вкладка «История проверок» позволяет вернуться к предыдущим аудитам, скачать отчёты и
              сравнить условия по разным тендерам.
            </p>
          </div>
          <div>
            <h4 className="font-bold text-white text-lg mb-3 flex items-center gap-2">
              <BookOpen size={18} className="text-[#22c55e]" /> База знаний
            </h4>
            <p className="text-slate-300 text-sm leading-relaxed mb-3">
              Вкладка «База знаний» содержит подборку материалов, шаблонов и подсказок, которые
              помогают разбираться в типовых рисках и требованиях по 44‑ФЗ и 223‑ФЗ.
            </p>
          </div>
        </div>
      </div>

      {/* Section 6: Триал, тарифы и лимиты */}
      <div className="bg-[#1a1f2e] border border-[#2a3441] rounded-2xl p-8 mb-8 shadow-sm">
        <div className="flex items-center gap-4 mb-6 border-b border-[#2a3441] pb-6">
          <div className="w-14 h-14 bg-[#22c55e]/10 rounded-2xl flex items-center justify-center text-[#22c55e]">
            <Star size={32} />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-white">6. Триал, тарифы и ограничения</h3>
            <p className="text-slate-400">
              Мы даём возможность спокойно «пощупать» систему, но одновременно защищаем сервис от
              злоупотреблений.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-slate-200">
          <div>
            <h4 className="font-bold text-white mb-2">7 дней бесплатного триала</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>После регистрации вы автоматически получаете 7 дней полного доступа.</li>
              <li>За это время можно провести реальные проверки, посмотреть отчёты и понять, подходит ли вам инструмент.</li>
              <li>По окончании триала аккаунт переводится на базовый тариф с ограниченными лимитами.</li>
            </ul>
          </div>
          <div>
            <h4 className="font-bold text-white mb-2">Защита от злоупотреблений</h4>
            <ul className="list-disc list-inside space-y-1">
              <li>Мы ограничиваем количество бесплатных регистраций, которые можно создать с одного IP‑адреса.</li>
              <li>Если вы видите сообщение о том, что «лимит бесплатных регистраций исчерпан», используйте существующий аккаунт или свяжитесь с нами для разблокировки.</li>
              <li>Такая защита не влияет на обычную работу действующих пользователей, но помогает сохранить стабильность сервиса.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Footer Tip */}
      <div className="bg-gradient-to-r from-[#1a1f2e] to-[#0f1419] border border-[#00d4ff]/30 rounded-2xl p-8 flex items-start gap-6">
        <div className="bg-[#00d4ff] text-[#0f1419] p-3 rounded-full shrink-0">
          <Bot size={32} />
        </div>
        <div>
          <h4 className="text-xl font-bold text-white mb-2">Как общаться с AI‑юристом</h4>
          <p className="text-slate-300 leading-relaxed text-sm mb-3">
            В правой части экрана «Анализ документа» всегда доступен чат с SINAPS AI. Вы можете
            скопировать любой пункт из документации и спросить, насколько он законен и какие риски
            несёт.
          </p>
          <p className="text-slate-400 text-xs flex items-start gap-2">
            <AlertTriangle size={14} className="text-amber-400 mt-0.5" />
            <span>
              Ответы ИИ не заменяют работу юриста, но помогают быстро ориентироваться в рисках и
              находить проблемные места в документации.
            </span>
          </p>
        </div>
      </div>
    </div>
  );
};

export default HelpGuide;



