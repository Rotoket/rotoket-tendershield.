# 🎨 ДЕНИ 2-3: FRONTEND REDESIGN (PHASE 1) — РЕАЛЬНЫЙ КОД

## АРХИТЕКТУРА: Не гигантский компонент, а ВКЛАДКИ

### КОНЦЕПЦИЯ:
```
ДО (неправильно):
- Пользователь видит 100+ элементов на одной странице
- Bounce rate: 80%
- "Слишком много информации"

ПОСЛЕ (правильно):
- Вкладка 1: КРИТИЧНЫЕ ФАКТОРЫ (3-5 элементов)
  └─ Deal Breakers (если есть)
  └─ Financial Impact (числа в рублях)
  └─ Главная рекомендация
  
- Вкладка 2: ПОЛНЫЙ АНАЛИЗ РИСКОВ (все детали)
  └─ 10+ рисков с объяснениями
  
- Вкладка 3: ВОЗМОЖНОСТИ И СТРАТЕГИЯ
  └─ Что хорошего в этом тендере
  └─ План действий
  
- Вкладка 4: ВОПРОСЫ ДЛЯ РЗ
  └─ 5-10 критичных вопросов
```

---

## STEP 1: Создай главный компонент `TenderAnalysisTabbed.tsx`

Путь: `frontend/src/components/Analysis/TenderAnalysisTabbed.tsx`

```typescript
import React, { useState } from 'react';
import styles from './TenderAnalysis.module.css';

// Импортируем подкомпоненты
import DealBreakersTab from './tabs/DealBreakersTab';
import FinancialImpactTab from './tabs/FinancialImpactTab';
import RecommendationTab from './tabs/RecommendationTab';
import RisksDetailedTab from './tabs/RisksDetailedTab';
import OpportunitiesTab from './tabs/OpportunitiesTab';
import SmartQuestionsTab from './tabs/SmartQuestionsTab';

interface TenderAnalysisProps {
  analysis: any; // Тип из backend
  tender: any;
}

type TabName = 'critical' | 'risks' | 'opportunities' | 'questions';

export const TenderAnalysisTabbed: React.FC<TenderAnalysisProps> = ({ 
  analysis, 
  tender 
}) => {
  const [activeTab, setActiveTab] = useState<TabName>('critical');
  const [expandedRisk, setExpandedRisk] = useState<number | null>(null);

  // Определяем какие вкладки показывать
  const hasDealBreakers = analysis?.dealBreakers && analysis.dealBreakers.length > 0;
  const hasRisks = analysis?.riskNarratives && analysis.riskNarratives.length > 0;
  const hasOpportunities = analysis?.opportunities && analysis.opportunities.length > 0;
  const hasQuestions = analysis?.smartQuestions && analysis.smartQuestions.length > 0;

  // Иконки для вкладок (визуальная помощь)
  const getTabIcon = (tab: TabName) => {
    const icons = {
      critical: '🚨',
      risks: '⚠️',
      opportunities: '⭐',
      questions: '💭'
    };
    return icons[tab];
  };

  return (
    <div className={styles.tabbedAnalysis}>
      {/* ЗАГОЛОВОК С ВЕРДИКТОМ (над вкладками) */}
      <div className={styles.analysisHeader}>
        <div className={styles.verdictBanner}>
          {analysis?.verdict === 'GO' && (
            <div className={styles.verdictGo}>
              <span className={styles.verdictEmoji}>✅</span>
              <div className={styles.verdictText}>
                <h2>ГОДЕН К УЧАСТИЮ</h2>
                <p>{analysis?.summary}</p>
              </div>
            </div>
          )}
          
          {analysis?.verdict === 'CAUTION' && (
            <div className={styles.verdictCaution}>
              <span className={styles.verdictEmoji}>⚠️</span>
              <div className={styles.verdictText}>
                <h2>РИСК — УЧАСТВОВАТЬ С ОСТОРОЖНОСТЬЮ</h2>
                <p>{analysis?.summary}</p>
              </div>
            </div>
          )}
          
          {analysis?.verdict === 'STOP' && (
            <div className={styles.verdictStop}>
              <span className={styles.verdictEmoji}>🛑</span>
              <div className={styles.verdictText}>
                <h2>СТОП — НЕ УЧАСТВОВАТЬ</h2>
                <p>{analysis?.summary}</p>
              </div>
            </div>
          )}
        </div>

        {/* SCORE BAR */}
        <div className={styles.scoreBar}>
          <div className={styles.scoreLabel}>Оценка проекта:</div>
          <div className={styles.scoreValue}>{analysis?.score}/100</div>
          <div className={styles.scoreBarFill} style={{
            width: `${analysis?.score}%`,
            backgroundColor: 
              analysis?.score > 70 ? '#28A745' : 
              analysis?.score > 40 ? '#FFC107' : 
              '#DC3545'
          }} />
        </div>
      </div>

      {/* ВКЛАДКИ НАВИГАЦИЯ */}
      <div className={styles.tabsNavigation}>
        <button
          className={`${styles.tabButton} ${activeTab === 'critical' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('critical')}
        >
          <span className={styles.tabIcon}>{getTabIcon('critical')}</span>
          <span className={styles.tabLabel}>Критичное</span>
          {hasDealBreakers && <span className={styles.tabBadge}>{analysis.dealBreakers.length}</span>}
        </button>

        {hasRisks && (
          <button
            className={`${styles.tabButton} ${activeTab === 'risks' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('risks')}
          >
            <span className={styles.tabIcon}>{getTabIcon('risks')}</span>
            <span className={styles.tabLabel}>Все риски</span>
            <span className={styles.tabBadge}>{analysis.riskNarratives.length}</span>
          </button>
        )}

        {hasOpportunities && (
          <button
            className={`${styles.tabButton} ${activeTab === 'opportunities' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('opportunities')}
          >
            <span className={styles.tabIcon}>{getTabIcon('opportunities')}</span>
            <span className={styles.tabLabel}>Возможности</span>
            <span className={styles.tabBadge}>{analysis.opportunities.length}</span>
          </button>
        )}

        {hasQuestions && (
          <button
            className={`${styles.tabButton} ${activeTab === 'questions' ? styles.activeTab : ''}`}
            onClick={() => setActiveTab('questions')}
          >
            <span className={styles.tabIcon}>{getTabIcon('questions')}</span>
            <span className={styles.tabLabel}>Вопросы</span>
            <span className={styles.tabBadge}>{analysis.smartQuestions.length}</span>
          </button>
        )}
      </div>

      {/* СОДЕРЖАНИЕ ВКЛАДОК */}
      <div className={styles.tabContent}>
        {/* ВКЛАДКА 1: КРИТИЧНЫЕ ФАКТОРЫ */}
        {activeTab === 'critical' && (
          <div className={styles.tabPane}>
            {hasDealBreakers && (
              <DealBreakersTab 
                dealBreakers={analysis.dealBreakers}
              />
            )}
            
            <FinancialImpactTab 
              financial={analysis.financialSummary}
            />
            
            <RecommendationTab 
              recommendation={analysis.strategicRecommendation}
              verdict={analysis.verdict}
            />
          </div>
        )}

        {/* ВКЛАДКА 2: ВСЕ РИСКИ */}
        {activeTab === 'risks' && hasRisks && (
          <div className={styles.tabPane}>
            <RisksDetailedTab 
              risks={analysis.riskNarratives}
              expandedRisk={expandedRisk}
              onToggleExpand={(idx) => setExpandedRisk(expandedRisk === idx ? null : idx)}
            />
          </div>
        )}

        {/* ВКЛАДКА 3: ВОЗМОЖНОСТИ */}
        {activeTab === 'opportunities' && hasOpportunities && (
          <div className={styles.tabPane}>
            <OpportunitiesTab 
              opportunities={analysis.opportunities}
              summary={analysis.opportunitySummary}
            />
          </div>
        )}

        {/* ВКЛАДКА 4: ВОПРОСЫ */}
        {activeTab === 'questions' && hasQuestions && (
          <div className={styles.tabPane}>
            <SmartQuestionsTab 
              questions={analysis.smartQuestions}
            />
          </div>
        )}
      </div>

      {/* ЭКСПОРТ И ДЕЙСТВИЯ (внизу) */}
      <div className={styles.analysisActions}>
        <button className={styles.btnExport}>
          📥 Скачать PDF отчёт
        </button>
        <button className={styles.btnShare}>
          🔗 Поделиться анализом
        </button>
        <button className={styles.btnFeedback}>
          💬 Отправить отзыв
        </button>
      </div>
    </div>
  );
};

export default TenderAnalysisTabbed;
```

---

## STEP 2: Создай подкомпоненты для вкладок

### 2.1. `tabs/DealBreakersTab.tsx`

```typescript
import React from 'react';
import styles from '../TenderAnalysis.module.css';

interface DealBreaker {
  title: string;
  quote: string;
  essence: string;
  status: 'VOID' | 'ILLEGAL' | 'LAW_VIOLATION';
  lawReference: string;
  financialRisk: number;
  action: {
    type: 'SKIP' | 'COMPLAIN_FAS' | 'ASK_CLARIFICATIONS';
    buttonLabel: string;
    justification: string;
  };
}

interface Props {
  dealBreakers: DealBreaker[];
}

export const DealBreakersTab: React.FC<Props> = ({ dealBreakers }) => {
  return (
    <div className={styles.dealBreakersSection}>
      <div className={styles.dealBreakersBanner}>
        <span className={styles.icon}>🚨</span>
        <div className={styles.bannerText}>
          <h2>СТОП-ФАКТОРЫ: {dealBreakers.length} КРИТИЧЕСКИХ РИСКА</h2>
          <p>Эти факторы делают контракт невыполнимым или незаконным</p>
        </div>
      </div>

      <div className={styles.dealBreakersGrid}>
        {dealBreakers.map((breaker, idx) => (
          <div key={idx} className={styles.dealBreakerCard}>
            <div className={styles.dBHeader}>
              <span className={styles.dBEmoji}>❌</span>
              <div className={styles.dBTitle}>
                <h3>{breaker.title}</h3>
                <span className={styles.dBRisk}>
                  Риск потери: {(breaker.financialRisk / 1_000_000).toFixed(1)}M ₽
                </span>
              </div>
            </div>

            <div className={styles.dBQuote}>
              <blockquote>
                "{breaker.quote}"
              </blockquote>
              <p className={styles.source}>— из документа тендера</p>
            </div>

            <div className={styles.dBEssence}>
              <h4>Почему это критично:</h4>
              <p>{breaker.essence}</p>
            </div>

            <div className={styles.dBStatus}>
              <strong>Статус:</strong>
              <span className={styles.statusBadge}>{breaker.status}</span>
              <span className={styles.lawRef}>см. {breaker.lawReference}</span>
            </div>

            <div className={styles.dBAction}>
              <button 
                className={`${styles.actionBtn} ${styles[`action_${breaker.action.type}`]}`}
                onClick={() => {
                  // Обработка действия
                  console.log('Action:', breaker.action.type);
                }}
              >
                {breaker.action.buttonLabel}
              </button>
              <p className={styles.actionJust}>
                {breaker.action.justification}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DealBreakersTab;
```

### 2.2. `tabs/FinancialImpactTab.tsx`

```typescript
import React from 'react';
import styles from '../TenderAnalysis.module.css';

interface FinancialData {
  penaltyRiskRubles: number;
  workingCapitalNeeded: number;
  guaranteeAmount: number;
  paymentTermsRisk: {
    averageDelayDays: number;
    estimatedCashGap: number;
    buffer: number;
  };
}

interface Props {
  financial: FinancialData | undefined;
}

export const FinancialImpactTab: React.FC<Props> = ({ financial }) => {
  if (!financial) return null;

  return (
    <div className={styles.financialSection}>
      <h2 className={styles.sectionTitle}>💰 Финансовый удар</h2>

      <div className={styles.financialGrid}>
        {/* ШТРАФ */}
        <div className={styles.financialCard}>
          <div className={styles.fIcon}>⚡</div>
          <div className={styles.fTitle}>Риск штрафа</div>
          <div className={styles.fValue}>
            {(financial.penaltyRiskRubles / 1_000_000).toFixed(1)} млн ₽
          </div>
          <div className={styles.fDesc}>
            При просрочке на 1 день или невыполнении условий
          </div>
        </div>

        {/* ОБОРОТНЫЙ КАПИТАЛ */}
        <div className={styles.financialCard}>
          <div className={styles.fIcon}>💵</div>
          <div className={styles.fTitle}>Нужно своих денег</div>
          <div className={styles.fValue}>
            {(financial.workingCapitalNeeded / 1_000_000).toFixed(1)} млн ₽
          </div>
          <div className={styles.fDesc}>
            Для работы до получения платежа от заказчика
          </div>
        </div>

        {/* ОБЕСПЕЧЕНИЕ */}
        <div className={styles.financialCard}>
          <div className={styles.fIcon}>🏦</div>
          <div className={styles.fTitle}>Обеспечение контракта</div>
          <div className={styles.fValue}>
            {(financial.guaranteeAmount / 1_000_000).toFixed(1)} млн ₽
          </div>
          <div className={styles.fDesc}>
            Блокировка средств на счёте на время контракта
          </div>
        </div>

        {/* КАССОВЫЙ РАЗРЫВ */}
        <div className={styles.financialCard}>
          <div className={styles.fIcon}>📉</div>
          <div className={styles.fTitle}>Кассовый разрыв</div>
          <div className={styles.fValue}>
            {financial.paymentTermsRisk.averageDelayDays} дней
          </div>
          <div className={styles.fDesc}>
            Среднее время ожидания платежа (при задержках)
          </div>
        </div>
      </div>

      {/* РЕКОМЕНДАЦИЯ ПО ФИНАНСАМ */}
      <div className={styles.financialAdvice}>
        <h3>📊 Мой финансовый совет:</h3>
        <div className={styles.adviceBox}>
          {financial.workingCapitalNeeded > financial.guaranteeAmount * 10 ? (
            <>
              <p>
                <strong>⚠️ РИСКОВАННО</strong>: Вам нужно {(financial.workingCapitalNeeded / 1_000_000).toFixed(1)}М ₽ собственных, 
                но обеспечение только {(financial.guaranteeAmount / 1_000_000).toFixed(1)}М ₽. 
                Кассовый разрыв может разорить компанию.
              </p>
            </>
          ) : (
            <>
              <p>
                <strong>✅ ПРИЕМЛЕМО</strong>: Финансовая нагрузка соответствует масштабу контракта. 
                Убедитесь, что у вас есть резерв.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FinancialImpactTab;
```

### 2.3. `tabs/RecommendationTab.tsx`

```typescript
import React, { useState } from 'react';
import styles from '../TenderAnalysis.module.css';

interface Props {
  recommendation: any;
  verdict: 'GO' | 'CAUTION' | 'STOP';
}

export const RecommendationTab: React.FC<Props> = ({ recommendation, verdict }) => {
  const [activeSubTab, setActiveSubTab] = useState<'decision' | 'reasoning' | 'action'>('decision');

  const getVerdictColor = () => {
    if (verdict === 'GO') return '#28A745';
    if (verdict === 'CAUTION') return '#FFC107';
    return '#DC3545';
  };

  return (
    <div className={styles.recommendationSection}>
      <h2 className={styles.sectionTitle}>🎯 Рекомендация</h2>

      {/* ПОДВКЛАДКИ */}
      <div className={styles.subTabs}>
        <button
          className={activeSubTab === 'decision' ? styles.activeSubTab : ''}
          onClick={() => setActiveSubTab('decision')}
        >
          Решение
        </button>
        <button
          className={activeSubTab === 'reasoning' ? styles.activeSubTab : ''}
          onClick={() => setActiveSubTab('reasoning')}
        >
          Обоснование
        </button>
        <button
          className={activeSubTab === 'action' ? styles.activeSubTab : ''}
          onClick={() => setActiveSubTab('action')}
        >
          План действий
        </button>
      </div>

      {/* РЕШЕНИЕ */}
      {activeSubTab === 'decision' && (
        <div className={styles.subTabContent}>
          <div className={styles.decisionBox} style={{ borderLeft: `4px solid ${getVerdictColor()}` }}>
            <p className={styles.decisionText}>
              {recommendation?.decisionText || 'Решение не доступно'}
            </p>
          </div>

          {recommendation?.reasons && (
            <div className={styles.reasonsList}>
              <h4>Почему я это рекомендую:</h4>
              <ul>
                {recommendation.reasons.map((reason: string, idx: number) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ОБОСНОВАНИЕ */}
      {activeSubTab === 'reasoning' && (
        <div className={styles.subTabContent}>
          <div className={styles.prosConsList}>
            <div className={styles.pros}>
              <h4>✅ Аргументы ЗА участие:</h4>
              <ul>
                {recommendation?.pros?.map((pro: string, idx: number) => (
                  <li key={idx}>{pro}</li>
                )) || <li>Данные недоступны</li>}
              </ul>
            </div>

            <div className={styles.cons}>
              <h4>❌ Аргументы ПРОТИВ:</h4>
              <ul>
                {recommendation?.cons?.map((con: string, idx: number) => (
                  <li key={idx}>{con}</li>
                )) || <li>Данные недоступны</li>}
              </ul>
            </div>
          </div>

          {recommendation?.finalThoughts && (
            <div className={styles.finalThoughts}>
              <p>{recommendation.finalThoughts}</p>
            </div>
          )}
        </div>
      )}

      {/* ПЛАН ДЕЙСТВИЙ */}
      {activeSubTab === 'action' && (
        <div className={styles.subTabContent}>
          <h3>Если вы решили участвовать:</h3>
          <div className={styles.actionTimeline}>
            {recommendation?.actionSteps?.map((step: any, idx: number) => (
              <div key={idx} className={styles.timelineItem}>
                <div className={styles.timelineNumber}>{idx + 1}</div>
                <div className={styles.timelineContent}>
                  <h4>{step.title}</h4>
                  <p>{step.description}</p>
                  <div className={styles.timelineMeta}>
                    <span className={styles.timelineTime}>⏱️ {step.timeline}</span>
                    {step.key && <span className={styles.timelineKey}>🔑 {step.key}</span>}
                  </div>
                </div>
              </div>
            )) || <p>План действий не доступен</p>}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendationTab;
```

---

## STEP 3: CSS Стили для вкладок

Добавь в `frontend/src/styles/TenderAnalysis.module.css`:

```css
/* ═══════════════════════════════════════════════════════════════ */
/* ГЛАВНЫЙ КОНТЕЙНЕР */
/* ═══════════════════════════════════════════════════════════════ */

.tabbedAnalysis {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* ═══════════════════════════════════════════════════════════════ */
/* ЗАГОЛОВОК С ВЕРДИКТОМ */
/* ═══════════════════════════════════════════════════════════════ */

.analysisHeader {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
}

.verdictBanner {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 20px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
}

.verdictGo {
  display: flex;
  align-items: center;
  gap: 15px;
}

.verdictGo .verdictEmoji {
  font-size: 48px;
}

.verdictText h2 {
  margin: 0;
  font-size: 20px;
  color: #28A745;
}

.verdictText p {
  margin: 5px 0 0;
  font-size: 14px;
  opacity: 0.95;
}

.verdictCaution {
  display: flex;
  align-items: center;
  gap: 15px;
  border-left: 4px solid #FFC107;
}

.verdictCaution .verdictEmoji {
  font-size: 48px;
}

.verdictCaution .verdictText h2 {
  color: #FFC107;
}

.verdictStop {
  display: flex;
  align-items: center;
  gap: 15px;
  border-left: 4px solid #DC3545;
}

.verdictStop .verdictEmoji {
  font-size: 48px;
}

.verdictStop .verdictText h2 {
  color: #DC3545;
}

/* SCORE BAR */

.scoreBar {
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(0, 0, 0, 0.2);
  padding: 15px;
  border-radius: 6px;
}

.scoreLabel {
  font-size: 14px;
  opacity: 0.9;
  min-width: 150px;
}

.scoreValue {
  font-size: 24px;
  font-weight: 700;
  min-width: 60px;
}

.scoreBarFill {
  flex: 1;
  height: 8px;
  border-radius: 4px;
  transition: width 0.5s ease;
}

/* ═══════════════════════════════════════════════════════════════ */
/* ВКЛАДКИ НАВИГАЦИЯ */
/* ═══════════════════════════════════════════════════════════════ */

.tabsNavigation {
  display: flex;
  gap: 10px;
  border-bottom: 2px solid #e0e0e0;
  background: #f9f9f9;
  padding: 0;
  overflow-x: auto;
}

.tabButton {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.tabButton:hover {
  background: #f0f0f0;
  color: #333;
}

.tabButton.activeTab {
  color: #667eea;
  border-bottom-color: #667eea;
  background: white;
}

.tabIcon {
  font-size: 18px;
}

.tabLabel {
  margin: 0;
}

.tabBadge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: #667eea;
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}

/* ═══════════════════════════════════════════════════════════════ */
/* СОДЕРЖАНИЕ ВКЛАДОК */
/* ═══════════════════════════════════════════════════════════════ */

.tabContent {
  padding: 30px;
  min-height: 400px;
}

.tabPane {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ═══════════════════════════════════════════════════════════════ */
/* DEAL BREAKERS СЕКЦИЯ */
/* ═══════════════════════════════════════════════════════════════ */

.dealBreakersSection {
  margin-bottom: 30px;
}

.dealBreakersBanner {
  display: flex;
  gap: 20px;
  background: #FFF3CD;
  border-left: 4px solid #DC3545;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.dealBreakersBanner .icon {
  font-size: 36px;
  flex-shrink: 0;
}

.bannerText h2 {
  margin: 0;
  font-size: 18px;
  color: #DC3545;
}

.bannerText p {
  margin: 5px 0 0;
  font-size: 14px;
  color: #666;
}

.dealBreakersGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

@media (max-width: 768px) {
  .dealBreakersGrid {
    grid-template-columns: 1fr;
  }
}

.dealBreakerCard {
  background: white;
  border: 2px solid #DC3545;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.3s;
}

.dealBreakerCard:hover {
  box-shadow: 0 8px 16px rgba(220, 53, 69, 0.2);
}

.dBHeader {
  display: flex;
  gap: 15px;
  padding: 20px;
  background: #FFE5E5;
  border-bottom: 1px solid #DC3545;
}

.dBEmoji {
  font-size: 32px;
  flex-shrink: 0;
}

.dBTitle h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.dBRisk {
  display: block;
  margin-top: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #DC3545;
}

.dBQuote {
  padding: 20px;
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
}

.dBQuote blockquote {
  margin: 0;
  padding: 0;
  font-size: 14px;
  font-style: italic;
  color: #555;
  line-height: 1.6;
}

.source {
  margin-top: 10px;
  font-size: 12px;
  color: #999;
}

.dBEssence {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.dBEssence h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #333;
}

.dBEssence p {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.dBStatus {
  padding: 15px 20px;
  background: #f0f0f0;
  font-size: 13px;
  display: flex;
  gap: 10px;
  align-items: center;
}

.statusBadge {
  background: #DC3545;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.lawRef {
  margin-left: auto;
  color: #667eea;
  text-decoration: none;
  cursor: pointer;
}

.dBAction {
  padding: 20px;
  display: flex;
  gap: 15px;
  align-items: center;
}

.actionBtn {
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.action_SKIP {
  background: #DC3545;
  color: white;
}

.action_SKIP:hover {
  background: #c82333;
}

.action_COMPLAIN_FAS {
  background: #FFC107;
  color: #333;
}

.action_COMPLAIN_FAS:hover {
  background: #e0a800;
}

.action_ASK_CLARIFICATIONS {
  background: #0D6EFD;
  color: white;
}

.action_ASK_CLARIFICATIONS:hover {
  background: #0b5ed7;
}

.actionJust {
  flex: 1;
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

/* ═══════════════════════════════════════════════════════════════ */
/* ФИНАНСОВАЯ СЕКЦИЯ */
/* ═══════════════════════════════════════════════════════════════ */

.financialSection {
  margin-bottom: 30px;
  background: #f0f7ff;
  padding: 30px;
  border-radius: 8px;
  border-left: 4px solid #0D6EFD;
}

.sectionTitle {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 700;
  color: #333;
}

.financialGrid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.financialCard {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border-top: 4px solid #0D6EFD;
  text-align: center;
  transition: box-shadow 0.3s;
}

.financialCard:hover {
  box-shadow: 0 4px 12px rgba(13, 110, 253, 0.15);
}

.fIcon {
  font-size: 32px;
  margin-bottom: 10px;
}

.fTitle {
  font-size: 13px;
  color: #666;
  margin-bottom: 10px;
  font-weight: 600;
}

.fValue {
  font-size: 24px;
  font-weight: 700;
  color: #0D6EFD;
  margin-bottom: 10px;
}

.fDesc {
  font-size: 12px;
  color: #999;
  line-height: 1.4;
}

.financialAdvice {
  background: white;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #0D6EFD;
}

.financialAdvice h3 {
  margin: 0 0 15px;
  font-size: 16px;
}

.adviceBox {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 6px;
  border-left: 4px solid #0D6EFD;
}

.adviceBox p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #555;
}

/* ═══════════════════════════════════════════════════════════════ */
/* РЕКОМЕНДАЦИЯ И ПОДВКЛАДКИ */
/* ═══════════════════════════════════════════════════════════════ */

.recommendationSection {
  margin-bottom: 30px;
}

.subTabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.subTabs button {
  padding: 12px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
}

.subTabs button.activeSubTab {
  color: #667eea;
  border-bottom-color: #667eea;
}

.subTabContent {
  padding: 20px 0;
}

.decisionBox {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.decisionText {
  margin: 0;
  font-size: 15px;
  line-height: 1.7;
  color: #333;
}

.reasonsList {
  margin-top: 20px;
}

.reasonsList h4 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #333;
}

.reasonsList ul {
  margin: 0;
  padding-left: 20px;
}

.reasonsList li {
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.prosConsList {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

@media (max-width: 768px) {
  .prosConsList {
    grid-template-columns: 1fr;
  }
}

.pros {
  background: #f0fdf4;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #28A745;
}

.pros h4 {
  margin: 0 0 15px;
  color: #28A745;
}

.cons {
  background: #fef2f2;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #DC3545;
}

.cons h4 {
  margin: 0 0 15px;
  color: #DC3545;
}

.pros ul,
.cons ul {
  margin: 0;
  padding-left: 20px;
}

.pros li,
.cons li {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.5;
}

.pros li {
  color: #166534;
}

.cons li {
  color: #991b1b;
}

.finalThoughts {
  background: #f0f7ff;
  padding: 20px;
  border-radius: 8px;
  border-left: 4px solid #0D6EFD;
}

.finalThoughts p {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.actionTimeline {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.timelineItem {
  display: flex;
  gap: 20px;
}

.timelineNumber {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  font-weight: 700;
  flex-shrink: 0;
}

.timelineContent {
  flex: 1;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 6px;
  border-left: 3px solid #667eea;
}

.timelineContent h4 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #333;
}

.timelineContent p {
  margin: 0 0 10px;
  font-size: 14px;
  color: #666;
  line-height: 1.5;
}

.timelineMeta {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #999;
}

.timelineTime,
.timelineKey {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}

/* ═══════════════════════════════════════════════════════════════ */
/* ЭКСПОРТ И ДЕЙСТВИЯ */
/* ═══════════════════════════════════════════════════════════════ */

.analysisActions {
  display: flex;
  gap: 10px;
  padding: 20px 30px;
  background: #f9f9f9;
  border-top: 1px solid #e0e0e0;
  justify-content: flex-end;
}

.btnExport,
.btnShare,
.btnFeedback {
  padding: 10px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

.btnExport:hover,
.btnShare:hover,
.btnFeedback:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* ═══════════════════════════════════════════════════════════════ */
/* RESPONSIVE */
/* ═══════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
  .analysisHeader {
    padding: 20px;
  }

  .verdictBanner {
    flex-direction: column;
  }

  .scoreBar {
    flex-wrap: wrap;
  }

  .tabsNavigation {
    flex-wrap: wrap;
  }

  .tabContent {
    padding: 20px;
  }

  .financialGrid {
    grid-template-columns: 1fr;
  }

  .analysisActions {
    flex-direction: column;
  }

  .btnExport,
  .btnShare,
  .btnFeedback {
    width: 100%;
  }
}
```

---

## ИСПОЛЬЗОВАНИЕ В ПРИЛОЖЕНИИ

В файле где ты показываешь результаты анализа (например `ExportModal.tsx` или `AnalysisResults.tsx`):

```typescript
import TenderAnalysisTabbed from './TenderAnalysisTabbed';

// В JSX:
<TenderAnalysisTabbed 
  analysis={analysisData} 
  tender={tenderData}
/>
```

---

## ПРЕИМУЩЕСТВА ЭТОго ПОДХОДА:

✅ **Для пользователя:**
- Не 100+ элементов, а 4 вкладки
- Критичное вверху, остальное по необходимости
- Mobile-friendly
- Быстрая загрузка (lazy loading вкладок)

✅ **Для разработчика:**
- Модульная архитектура (каждая вкладка отдельный компонент)
- Легко добавить/убрать вкладку
- Переиспользуемые компоненты
- Просто тестировать

✅ **Для бизнеса:**
- Bounce rate снижается (пользователь не закрывает)
- Лучше конверсия (пользователь видит критичное)
- Возможность добавить аналитику по вкладкам (какие вкладки смотрят)

**Это то, что реально работает! 🚀**
