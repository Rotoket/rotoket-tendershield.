import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css'; // Добавляем стили, если они есть
import { UserRoleProvider } from './context/UserRoleContext';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);

// Обработка ошибок рендеринга
try {
  root.render(
    <React.StrictMode>
      <UserRoleProvider>
        <App />
      </UserRoleProvider>
    </React.StrictMode>
  );
} catch (error) {
  console.error('[Root] Error rendering app:', error);
  rootElement.innerHTML = `
    <div style="padding: 20px; color: white; background: #0f1419; min-height: 100vh;">
      <h1>Ошибка загрузки приложения</h1>
      <p>Пожалуйста, обновите страницу или свяжитесь с поддержкой.</p>
      <pre style="background: #1a1a1a; padding: 10px; border-radius: 4px; overflow: auto;">
${error instanceof Error ? error.stack : String(error)}
      </pre>
    </div>
  `;
}