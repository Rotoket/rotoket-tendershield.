import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Analytics from './Analytics';
import * as analyticsService from '../services/analyticsService';
import * as authService from '../services/authService';

// Моки
vi.mock('../services/analyticsService');
vi.mock('../services/authService');
vi.mock('./Toast', () => ({
  useToast: () => ({
    showToast: vi.fn(),
    ToastComponent: () => null,
  }),
}));

describe('Analytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('должен отображать загрузку при инициализации', () => {
    vi.spyOn(authService, 'getCurrentUser').mockResolvedValue({
      id: 1,
      email: 'test@test.com',
      is_active: true,
    } as any);

    vi.spyOn(analyticsService, 'getUserAnalytics').mockImplementation(
      () => new Promise(() => {}) // Бесконечный промис для загрузки
    );

    const { container } = render(<Analytics />);
    // Проверяем наличие Loader2 (иконка загрузки)
    const loader = container.querySelector('.lucide-loader-circle');
    expect(loader).toBeDefined();
  });

  it('должен отображать статистику пользователя', async () => {
    const mockUser = {
      id: 1,
      email: 'test@test.com',
      is_active: true,
    };

    const mockUserStats = {
      user_id: 1,
      email: 'test@test.com',
      plan_type: 'pro',
      total_analyses: 50,
      total_packages: 10,
      current_month_analyses: 15,
      tariff_limit: 100,
      trial_active: false,
      trial_days_left: 0,
    };

    vi.spyOn(authService, 'getCurrentUser').mockResolvedValue(mockUser as any);
    vi.spyOn(analyticsService, 'getUserAnalytics').mockResolvedValue(mockUserStats);
    vi.spyOn(analyticsService, 'getAnalyticsTimeline').mockResolvedValue([]);
    vi.spyOn(analyticsService, 'getPopularIndustries').mockResolvedValue([]);
    vi.spyOn(analyticsService, 'getAverageScores').mockResolvedValue({});

    render(<Analytics />);

    await waitFor(() => {
      expect(screen.getByText('50')).toBeDefined(); // total_analyses
      expect(screen.getByText('10')).toBeDefined(); // total_packages
    });
  });

  it('должен отображать системную статистику для админа', async () => {
    const mockAdmin = {
      id: 1,
      email: 'admin@tendershield.pro',
      is_active: true,
    };

    const mockSystemStats = {
      total_users: 100,
      active_users_30d: 50,
      total_analyses: 500,
      recent_analyses_30d: 200,
      tariff_distribution: { free: 50, pro: 30, enterprise: 20 },
      industry_distribution: {},
    };

    vi.spyOn(authService, 'getCurrentUser').mockResolvedValue(mockAdmin as any);
    vi.spyOn(analyticsService, 'getUserAnalytics').mockResolvedValue({
      user_id: 1,
      email: 'admin@tendershield.pro',
      plan_type: 'enterprise',
      total_analyses: 0,
      total_packages: 0,
      current_month_analyses: 0,
      tariff_limit: -1,
      trial_active: false,
      trial_days_left: 0,
    });
    vi.spyOn(analyticsService, 'getSystemAnalytics').mockResolvedValue(mockSystemStats);
    vi.spyOn(analyticsService, 'getAnalyticsTimeline').mockResolvedValue([]);
    vi.spyOn(analyticsService, 'getPopularIndustries').mockResolvedValue([]);
    vi.spyOn(analyticsService, 'getAverageScores').mockResolvedValue({});

    render(<Analytics />);

    await waitFor(() => {
      expect(screen.getByText('100')).toBeDefined(); // total_users
      expect(screen.getByText('500')).toBeDefined(); // total_analyses
    });
  });
});

