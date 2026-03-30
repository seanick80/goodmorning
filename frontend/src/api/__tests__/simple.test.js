import { describe, it, expect, vi } from 'vitest';
import { apiFetch } from '../client';
import { fetchWeather } from '../weather';
import { fetchStocks } from '../stocks';
import { fetchCalendar } from '../calendar';
import { fetchNews } from '../news';
import { fetchDashboard } from '../dashboard';

vi.mock('../client', () => ({
  apiFetch: vi.fn(),
}));

describe('simple API wrappers', () => {
  it('fetchWeather calls /weather/', () => {
    fetchWeather();
    expect(apiFetch).toHaveBeenCalledWith('/weather/');
  });

  it('fetchStocks calls /stocks/', () => {
    fetchStocks();
    expect(apiFetch).toHaveBeenCalledWith('/stocks/');
  });

  it('fetchCalendar calls /calendar/', () => {
    fetchCalendar();
    expect(apiFetch).toHaveBeenCalledWith('/calendar/');
  });

  it('fetchNews calls /news/', () => {
    fetchNews();
    expect(apiFetch).toHaveBeenCalledWith('/news/');
  });

  it('fetchDashboard calls /dashboard/', () => {
    fetchDashboard();
    expect(apiFetch).toHaveBeenCalledWith('/dashboard/');
  });
});
