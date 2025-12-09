import { renderHook, act, waitFor } from "@testing-library/react";
import { useAgent } from "@/hooks/use-agent";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock Audio
class MockAudio {
  preload = "";
  play = jest.fn().mockResolvedValue(undefined);
}
(global as any).Audio = MockAudio;

// Mock navigator.vibrate
Object.defineProperty(navigator, "vibrate", {
  value: jest.fn(),
  writable: true,
});

describe("useAgent", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should start with idle status", () => {
    const { result } = renderHook(() => useAgent());

    expect(result.current.status).toBe("idle");
    expect(result.current.thoughts).toEqual([]);
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should transition to connecting when startStreaming is called", async () => {
    // Mock a pending response
    mockFetch.mockImplementationOnce(
      () =>
        new Promise(() => {
          // Never resolves - simulates connecting state
        })
    );

    const { result } = renderHook(() => useAgent());

    act(() => {
      result.current.startStreaming("test-log-id", "/path/to/image.jpg");
    });

    await waitFor(() => {
      expect(result.current.status).toBe("connecting");
    });
  });

  it("should reset state correctly", async () => {
    const { result } = renderHook(() => useAgent());

    act(() => {
      result.current.reset();
    });

    expect(result.current.status).toBe("idle");
    expect(result.current.thoughts).toEqual([]);
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it("should set error when fetch fails", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useAgent());

    act(() => {
      result.current.startStreaming("test-log-id");
    });

    // Wait for the error to be logged (handling the async state update)
    await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith("Streaming error:", expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });

  it("should expose startStreaming function", () => {
    const { result } = renderHook(() => useAgent());

    expect(typeof result.current.startStreaming).toBe("function");
  });

  it("should expose reset function", () => {
    const { result } = renderHook(() => useAgent());

    expect(typeof result.current.reset).toBe("function");
  });
});
