import { describe, it, expect, vi } from 'vitest';
import { apiFetch } from '../client';
import {
  fetchAuthStatus,
  fetchGoogleCalendars,
  fetchGooglePhotosAlbums,
  createPhotosPickerSession,
  pollPhotosPickerSession,
  fetchPhotosPickerMedia,
  patchDashboard,
} from '../auth';

vi.mock('../client', () => ({
  apiFetch: vi.fn(),
}));

describe('auth API', () => {
  it('fetchAuthStatus calls /auth/status/', () => {
    fetchAuthStatus();
    expect(apiFetch).toHaveBeenCalledWith('/auth/status/');
  });

  it('fetchGoogleCalendars calls /auth/google/calendars/', () => {
    fetchGoogleCalendars();
    expect(apiFetch).toHaveBeenCalledWith('/auth/google/calendars/');
  });

  it('fetchGooglePhotosAlbums calls /auth/google/photos/albums/', () => {
    fetchGooglePhotosAlbums();
    expect(apiFetch).toHaveBeenCalledWith('/auth/google/photos/albums/');
  });

  it('createPhotosPickerSession sends POST to picker endpoint', () => {
    createPhotosPickerSession();
    expect(apiFetch).toHaveBeenCalledWith('/auth/google/photos/picker/', {
      method: 'POST',
    });
  });

  it('pollPhotosPickerSession includes session id in URL', () => {
    pollPhotosPickerSession('sess-42');
    expect(apiFetch).toHaveBeenCalledWith(
      '/auth/google/photos/picker/sess-42/',
    );
  });

  it('fetchPhotosPickerMedia includes session id in URL', () => {
    fetchPhotosPickerMedia('sess-42');
    expect(apiFetch).toHaveBeenCalledWith(
      '/auth/google/photos/picker/sess-42/media/',
    );
  });

  it('patchDashboard sends PATCH with JSON body', () => {
    patchDashboard({ theme: 'dark' });
    expect(apiFetch).toHaveBeenCalledWith('/dashboard/', {
      method: 'PATCH',
      body: JSON.stringify({ theme: 'dark' }),
    });
  });
});
