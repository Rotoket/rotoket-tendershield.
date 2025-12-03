import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationsPanel } from './NotificationsPanel';

// Мок для fetch
global.fetch = vi.fn();

describe('NotificationsPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('не должен отображаться, если нет уведомлений', () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    const { container } = render(<NotificationsPanel />);
    // Компонент должен быть скрыт, если нет уведомлений
    expect(container.firstChild).toBeNull();
  });

  it('должен отображать уведомления', async () => {
    const user = userEvent.setup();
    const mockNotifications = [
      {
        type: 'warning',
        title: 'Приближается лимит',
        message: 'Осталось 5 анализов',
        priority: 'high',
      },
      {
        type: 'info',
        title: 'Триал скоро закончится',
        message: 'Осталось 3 дня',
        priority: 'medium',
      },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockNotifications,
    });

    render(<NotificationsPanel />);

    // Ждем загрузки уведомлений
    await waitFor(() => {
      expect(screen.getByText('2')).toBeDefined(); // Счетчик
    });

    // Кликаем на кнопку уведомлений, чтобы открыть панель
    const button = screen.getByRole('button');
    await act(async () => {
      await user.click(button);
    });

    // Ждем появления уведомлений в панели
    await waitFor(() => {
      expect(screen.getByText('Приближается лимит')).toBeDefined();
      expect(screen.getByText('Триал скоро закончится')).toBeDefined();
    }, { timeout: 3000 });
  });

  it('должен показывать счетчик непрочитанных', async () => {
    const mockNotifications = [
      { type: 'warning', title: 'Уведомление 1', message: 'Текст', priority: 'high' },
      { type: 'info', title: 'Уведомление 2', message: 'Текст', priority: 'medium' },
      { type: 'error', title: 'Уведомление 3', message: 'Текст', priority: 'critical' },
    ];

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => mockNotifications,
    });

    render(<NotificationsPanel />);

    await waitFor(() => {
      expect(screen.getByText('3')).toBeDefined(); // Счетчик
    });
  });

  it('должен обрабатывать ошибки загрузки', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<NotificationsPanel />);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });
});

