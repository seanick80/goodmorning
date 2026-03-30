import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiFetch } from '../client';

function mockResponse(overrides = {}) {
  return {
    ok: true,
    status: 200,
    statusText: 'OK',
    json: () => Promise.resolve({ key: 'value' }),
    ...overrides,
  };
}

beforeEach(() => {
  globalThis.fetch = vi.fn().mockResolvedValue(mockResponse());
});

afterEach(() => {
  vi.restoreAllMocks();
  document.cookie = 'csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
});

describe('apiFetch', () => {
  it('prepends /api base URL to path', async () => {
    await apiFetch('/weather/');

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/weather/',
      expect.any(Object),
    );
  });

  it('includes Content-Type application/json header', async () => {
    await apiFetch('/weather/');

    const callArgs = globalThis.fetch.mock.calls[0][1];
    expect(callArgs.headers['Content-Type']).toBe('application/json');
  });

  it('throws with status property on error response', async () => {
    globalThis.fetch.mockResolvedValue(
      mockResponse({ ok: false, status: 404, statusText: 'Not Found' }),
    );

    const error = await apiFetch('/missing/').catch((e) => e);

    expect(error).toBeInstanceOf(Error);
    expect(error.message).toContain('404');
    expect(error.status).toBe(404);
  });

  it('returns parsed JSON on success', async () => {
    globalThis.fetch.mockResolvedValue(
      mockResponse({ json: () => Promise.resolve({ temp: 72 }) }),
    );

    const data = await apiFetch('/weather/');

    expect(data).toEqual({ temp: 72 });
  });

  it('includes CSRF token on POST requests', async () => {
    document.cookie = 'csrftoken=abc123';

    await apiFetch('/submit/', { method: 'POST' });

    const callArgs = globalThis.fetch.mock.calls[0][1];
    expect(callArgs.headers['X-CSRFToken']).toBe('abc123');
  });

  it('does not include CSRF token on GET requests', async () => {
    document.cookie = 'csrftoken=abc123';

    await apiFetch('/weather/');

    const callArgs = globalThis.fetch.mock.calls[0][1];
    expect(callArgs.headers['X-CSRFToken']).toBeUndefined();
  });

  it('merges custom headers with defaults', async () => {
    await apiFetch('/weather/', {
      headers: { Authorization: 'Bearer token123' },
    });

    const callArgs = globalThis.fetch.mock.calls[0][1];
    expect(callArgs.headers['Content-Type']).toBe('application/json');
    expect(callArgs.headers['Authorization']).toBe('Bearer token123');
  });
});
