import { renderHook, act } from '@testing-library/react';
import { useAgent } from '../use-agent';
import * as nextIntl from 'next-intl';

// Mock dependencies
jest.mock('next-intl', () => ({
  useLocale: jest.fn(),
}));

jest.mock('@tanstack/react-query', () => ({
  useQueryClient: jest.fn(() => ({
    invalidateQueries: jest.fn(),
  })),
}));

// Mock fetch global
global.fetch = jest.fn();

describe('useAgent Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      body: {
        getReader: () => ({
          read: jest.fn().mockResolvedValue({ done: true, value: undefined }),
          cancel: jest.fn(),
        }),
      },
    });
  });

  it('should pass language="nl" to stream endpoint when locale is "nl"', async () => {
    (nextIntl.useLocale as jest.Mock).mockReturnValue('nl');

    const { result } = renderHook(() => useAgent());

    await act(async () => {
      await result.current.startStreaming('log-123', 'img.jpg');
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/stream'),
      expect.objectContaining({
        body: expect.stringContaining('"language":"nl"'),
      })
    );
  });

  it('should pass language="en" to stream endpoint when locale is "en"', async () => {
    (nextIntl.useLocale as jest.Mock).mockReturnValue('en');

    const { result } = renderHook(() => useAgent());

    await act(async () => {
      await result.current.startStreaming('log-456', 'img.jpg');
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/stream'),
      expect.objectContaining({
        body: expect.stringContaining('"language":"en"'),
      })
    );
  });

  it('should fallback to "nl" when locale is unknown', async () => {
    (nextIntl.useLocale as jest.Mock).mockReturnValue('fr'); // Unsupported

    const { result } = renderHook(() => useAgent());

    await act(async () => {
      await result.current.startStreaming('log-789', 'img.jpg');
    });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/analysis/stream'),
      expect.objectContaining({
        body: expect.stringContaining('"language":"nl"'),
      })
    );
  });
});
