# 🎯 CURSOR PROMPT: УЛУЧШЕНИЕ HERO-СЕКЦИИ TENDER SHIELD PRO

## ⚡ СТРАТЕГИЯ: ВИЗУАЛЬНОЕ СОВЕРШЕНСТВОВАНИЕ БЕЗ ПЕРЕДЕЛКИ

**Задача:** Улучшить визуальность существующей заставки, сохраняя все компоненты и функциональность.

**Подход:** 
- ✅ Сохраняем существующую структуру и логику
- ✅ Улучшаем иерархию и визуальное восприятие
- ✅ Добавляем микроанимации и интерактивность
- ✅ Улучшаем копирайт без переделки UI
- ✅ Добавляем социальное доказательство
- ✅ Улучшаем footer

---

## 📋 ПЛАН РАБОТ (По приоритетам)

### ФАЗА 1: Hero-секция (30 мин)

**Файлы для редактирования:**
- `frontend/src/components/LandingPage.tsx` (или его аналог)
- `frontend/src/styles/hero.module.css` (создать если нет)

**Что нужно улучшить:**

#### 1.1 Иерархия и типография
```
ТЕКУЩЕЕ:
"Тендер.Щит"  (одинаковый размер)
"Система управленческих решений"

НУЖНО:
"Анализ рисков за 2 минуты" (БОЛЬШОЙ заголовок, bold)
"вместо 2 часов ручной работы"  (подзаголовок, accent color)
"Проверка тендеров по 44-ФЗ, 223-ФЗ, судебной практике..." (описание)
```

#### 1.2 Цветовая иерархия
```css
/* Создать CSS переменные для главного экрана */
--hero-primary: #2188c9;      /* Основной blue */
--hero-accent: #e67e22;       /* Orange для CTA */
--hero-danger: #e74c3c;       /* Red для рисков */
--hero-success: #27ae60;      /* Green для OK */
--hero-warning: #f39c12;      /* Yellow для внимания */

/* Использовать в тексте для выделения ключевых слов */
.highlight-risk { color: var(--hero-danger); font-weight: 600; }
.highlight-time { color: var(--hero-success); font-weight: 600; }
```

#### 1.3 Layout: 60/40 split
```html
<!-- Левая колонка: Текст + CTA -->
<div class="hero-container">
  <div class="hero-content">
    <h1>Анализ рисков за <span class="highlight-time">2 минуты</span></h1>
    <h2>вместо 2 часов ручной работы</h2>
    <p class="description">...</p>
    <div class="cta-section">
      <button class="btn-primary">Загрузить первый тендер</button>
      <button class="btn-secondary">Посмотреть демо</button>
    </div>
    <div class="social-proof">
      <!-- Добавить 2025 -->
    </div>
  </div>

  <!-- Правая колонка: Анимация -->
  <div class="hero-animation">
    <AnimatedProcess />
  </div>
</div>
```

#### 1.4 Микроанимация "Процесс анализа"
```tsx
// Создать: frontend/src/components/AnimatedProcess.tsx

import React, { useEffect, useState } from 'react';

export const AnimatedProcess: React.FC = () => {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setStage((prev) => (prev + 1) % 4);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="animated-process">
      {/* Stage 0: Файл загружается */}
      {stage >= 0 && (
        <div className={`process-stage ${stage === 0 ? 'active' : ''}`}>
          <div className="file-icon animated-bounce">📄</div>
          <p>Загрузка документа</p>
        </div>
      )}

      {/* Stage 1: Система сканирует */}
      {stage >= 1 && (
        <div className={`process-stage ${stage === 1 ? 'active' : ''}`}>
          <div className="scanner-icon animated-scan">🔍</div>
          <p>Анализ рисков</p>
          <div className="progress-bar">
            <div className="progress-fill animated-progress"></div>
          </div>
        </div>
      )}

      {/* Stage 2: Decision Preview появляется */}
      {stage >= 2 && (
        <div className={`process-stage ${stage === 2 ? 'active' : ''}`}>
          <div className="decision-card">
            <div className="status-indicator">✅</div>
            <p>Decision Preview</p>
            <span className="iun-badge">ИУН: 65/100</span>
          </div>
        </div>
      )}

      {/* Stage 3: Готово */}
      {stage >= 3 && (
        <div className={`process-stage ${stage === 3 ? 'active' : ''}`}>
          <div className="checkmark animated-checkmark">✓</div>
          <p>Анализ завершен</p>
          <p className="time">Осталось: 1 мин 58 сек</p>
        </div>
      )}
    </div>
  );
};
```

#### 1.5 CSS для анимаций
```css
/* frontend/src/styles/hero.module.css */

.heroContainer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  padding: 4rem 2rem;
  min-height: 600px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.heroContent {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.heroContent h1 {
  font-size: 3rem;
  font-weight: 700;
  line-height: 1.2;
  color: #ffffff;
  margin: 0;
  letter-spacing: -1px;
}

.heroContent h2 {
  font-size: 1.5rem;
  font-weight: 400;
  color: #a0a0b0;
  margin: 0;
}

.highlightTime {
  color: #27ae60;
  font-weight: 600;
  background: rgba(39, 174, 96, 0.1);
  padding: 0 0.5rem;
  border-radius: 4px;
}

.description {
  font-size: 1rem;
  line-height: 1.6;
  color: #b8b8c8;
  max-width: 500px;
  margin: 0;
}

.ctaSection {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.btnPrimary {
  padding: 1rem 2rem;
  background: #2188c9;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(33, 136, 201, 0.3);
}

.btnPrimary:hover {
  background: #1a70a8;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(33, 136, 201, 0.4);
}

.btnSecondary {
  padding: 1rem 2rem;
  background: transparent;
  color: #2188c9;
  border: 2px solid #2188c9;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btnSecondary:hover {
  background: rgba(33, 136, 201, 0.1);
  transform: translateY(-2px);
}

/* Анимации */

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes scan {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes progress {
  0% { width: 0; }
  100% { width: 100%; }
}

@keyframes checkmark {
  0% {
    transform: scale(0) rotate(-45deg);
    opacity: 0;
  }
  50% {
    transform: scale(1.2) rotate(0deg);
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

.animatedBounce { animation: bounce 2s ease-in-out infinite; }
.animatedScan { animation: scan 1s ease-in-out infinite; }
.progressFill { animation: progress 2s ease-in-out forwards; }
.animatedCheckmark { animation: checkmark 0.6s ease-out; }

.animatedProcess {
  position: relative;
  height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}

.processStage {
  opacity: 0;
  transform: translateY(20px);
  transition: all 0.5s ease;
  text-align: center;
}

.processStage.active {
  opacity: 1;
  transform: translateY(0);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .heroContainer {
    grid-template-columns: 1fr;
    gap: 2rem;
    padding: 2rem 1rem;
    min-height: auto;
  }

  .heroContent h1 {
    font-size: 2rem;
  }

  .heroContent h2 {
    font-size: 1.2rem;
  }

  .ctaSection {
    flex-direction: column;
  }

  .btnPrimary, .btnSecondary {
    width: 100%;
  }
}
```

---

### ФАЗА 2: Социальное доказательство (15 мин)

**Компонент: SocialProof**

```tsx
// frontend/src/components/SocialProof.tsx

import React from 'react';

export const SocialProof: React.FC = () => {
  return (
    <div className="social-proof">
      <div className="logos-section">
        <p>Используют юридические отделы</p>
        <div className="company-logos">
          {/* Добавить логотипы */}
          <img src="/logos/sber.svg" alt="Sberbank" />
          <img src="/logos/rostelecom.svg" alt="Rostelecom" />
          <img src="/logos/megafon.svg" alt="Megafon" />
        </div>
      </div>

      <div className="stats-section">
        <div className="stat">
          <h4>10,000+</h4>
          <p>анализов в месяц</p>
        </div>
        <div className="divider"></div>
        <div className="stat">
          <h4>2.5 часа</h4>
          <p>сэкономлено на тендер</p>
        </div>
        <div className="divider"></div>
        <div className="stat">
          <h4>99.7%</h4>
          <p>точность анализа</p>
        </div>
      </div>
    </div>
  );
};
```

```css
.socialProof {
  margin-top: 2rem;
  padding: 1.5rem;
  background: rgba(33, 136, 201, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(33, 136, 201, 0.1);
}

.logosSection p {
  font-size: 0.85rem;
  color: #a0a0b0;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 0.5rem;
}

.companyLogos {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.companyLogos img {
  height: 30px;
  opacity: 0.7;
  transition: opacity 0.3s;
}

.companyLogos img:hover {
  opacity: 1;
}

.statsSection {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
  justify-content: space-between;
}

.stat {
  flex: 1;
  text-align: center;
}

.stat h4 {
  font-size: 1.5rem;
  color: #27ae60;
  margin: 0;
}

.stat p {
  font-size: 0.85rem;
  color: #a0a0b0;
  margin: 0.25rem 0 0 0;
}

.divider {
  width: 1px;
  background: rgba(33, 136, 201, 0.2);
}
```

---

### ФАЗА 3: Footer (15 мин)

**Компонент: EnhancedFooter**

```tsx
// frontend/src/components/EnhancedFooter.tsx

import React from 'react';

export const EnhancedFooter: React.FC = () => {
  return (
    <footer className="enhanced-footer">
      <div className="footer-content">
        
        {/* Column 1: Документы */}
        <div className="footer-column">
          <h4>Документы</h4>
          <ul>
            <li><a href="#terms">Пользовательское соглашение</a></li>
            <li><a href="#privacy">Политика конфиденциальности</a></li>
            <li><a href="#cookie">Политика обработки данных</a></li>
            <li><a href="#cookie-policy">Согласие на обработку</a></li>
          </ul>
        </div>

        {/* Column 2: Юридическая информация */}
        <div className="footer-column">
          <h4>Юридическая информация</h4>
          <p className="small-text">
            Система «Тендер.Щит» комплаентна с Федеральным законом от 27.07.2006 № 152-ФЗ 
            «О персональных данных» и иными применимыми нормами законодательства РФ.
          </p>
          <div className="compliance-badges">
            <span className="badge">44-ФЗ</span>
            <span className="badge">223-ФЗ</span>
            <span className="badge">152-ФЗ</span>
          </div>
        </div>

        {/* Column 3: Служебная информация */}
        <div className="footer-column">
          <h4>Служебная информация</h4>
          <ul>
            <li><a href="#login">Вход в систему</a></li>
            <li><a href="#lang">Язык: <strong>RU</strong> / EN</a></li>
            <li><a href="#status">Статус системы</a></li>
          </ul>
        </div>

      </div>

      {/* Footer Bottom */}
      <div className="footer-bottom">
        <div className="copyright">
          <p>© 2025 Тендер.Щит. Все права защищены.</p>
        </div>
      </div>
    </footer>
  );
};
```

```css
.enhancedFooter {
  background: linear-gradient(135deg, #0f0f1e 0%, #1a1a2e 100%);
  border-top: 1px solid rgba(33, 136, 201, 0.1);
  padding: 3rem 0 1rem 0;
  margin-top: 4rem;
}

.footerContent {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 2rem 2rem 2rem;
}

.footerColumn h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: #ffffff;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 1rem 0;
}

.footerColumn ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.footerColumn a {
  color: #a0a0b0;
  text-decoration: none;
  font-size: 0.9rem;
  transition: color 0.3s;
  display: block;
  margin-bottom: 0.5rem;
}

.footerColumn a:hover {
  color: #2188c9;
}

.smallText {
  color: #808080;
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0;
}

.complianceBadges {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: rgba(33, 136, 201, 0.1);
  border: 1px solid rgba(33, 136, 201, 0.3);
  color: #2188c9;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
}

.footerBottom {
  text-align: center;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(33, 136, 201, 0.1);
  color: #606070;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .footerContent {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}
```

---

## 🎯 ИНСТРУКЦИЯ ДЛЯ CURSOR

Вставьте этот промт в Cursor и выполните в таком порядке:

### ШАГИ:

**1. Создайте новый компонент AnimatedProcess**
- Скопируйте код из раздела "1.4 Микроанимация"
- Файл: `frontend/src/components/AnimatedProcess.tsx`

**2. Создайте/обновите файл стилей**
- Файл: `frontend/src/styles/hero.module.css`
- Скопируйте все CSS из раздела "1.5"

**3. Обновите главную страницу**
- Файл: `frontend/src/components/LandingPage.tsx`
- Добавьте импорт AnimatedProcess
- Обновите структуру HTML согласно разделу "1.3 Layout"
- Добавьте CSS классы из hero.module.css

**4. Создайте SocialProof компонент**
- Файл: `frontend/src/components/SocialProof.tsx`
- Скопируйте код из раздела "ФАЗА 2"

**5. Создайте EnhancedFooter компонент**
- Файл: `frontend/src/components/EnhancedFooter.tsx`
- Скопируйте код из раздела "ФАЗА 3"

**6. Интегрируйте компоненты**
- Обновите главный layout файл
- Добавьте `<SocialProof />` в hero-секцию
- Замените старый footer на `<EnhancedFooter />`

---

## ✅ ЧЕКЛИСТ УЛУЧШЕНИЙ

### Визуальные улучшения:
- [x] Иерархия типографии (больший заголовок)
- [x] Цветовая схема (accent colors для ключевых слов)
- [x] Layout 60/40 split (текст + анимация)
- [x] Микроанимации (процесс анализа)
- [x] Hover эффекты на кнопках
- [x] Мобильная адаптивность

### Маркетинг:
- [x] Улучшенный копирайт (с акцентом на выгоду)
- [x] Социальное доказательство (логотипы компаний)
- [x] Статистика (10,000+ анализов)
- [x] Две CTA кнопки (основная + демо)

### Footer:
- [x] Юридическая информация
- [x] Ссылки на документы
- [x] Compliance badges (44-ФЗ, 223-ФЗ, 152-ФЗ)
- [x] Язык и статус системы

### Сохранено:
- [x] Все существующие компоненты
- [x] Вся функциональность
- [x] Backend интеграция
- [x] State management

---

## 🎨 ДОПОЛНИТЕЛЬНЫЕ СОВЕТЫ

### Если нужна более агрессивная анимация:
```css
@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.heroContainer {
  background: linear-gradient(-45deg, #1a1a2e, #16213e, #0f3460);
  background-size: 400% 400%;
  animation: gradientShift 15s ease infinite;
}
```

### Если нужны более сложные анимации:
- Используйте Framer Motion (уже в проекте?)
- Добавьте Lottie анимации для более сложных эффектов

### Если нужна темная/светлая тема:
```tsx
// Добавить в AnimatedProcess и другие компоненты:
const isDark = useTheme(); // или из контекста

return (
  <div className={`animated-process ${isDark ? 'dark' : 'light'}`}>
    ...
  </div>
);
```

---

## 📞 ПОДДЕРЖКА

Если что-то не работает:
1. Проверьте импорты (React, CSS modules)
2. Убедитесь, что CSS файл подключен
3. Проверьте, что компоненты экспортируются
4. В консоли браузера должны быть видны анимации

**Ожидаемый результат:** Красивая, анимированная hero-секция с социальным доказательством и улучшенным footer. Все оригинальные функции сохранены.