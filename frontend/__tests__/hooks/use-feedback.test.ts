import { renderHook, act } from "@testing-library/react";
import { useFeedback } from "@/hooks/use-feedback";

// Mock navigator.vibrate
const mockVibrate = jest.fn();
Object.defineProperty(navigator, "vibrate", {
  value: mockVibrate,
  writable: true,
  configurable: true,
});

// Mock Audio class
const mockPlay = jest.fn().mockResolvedValue(undefined);
const mockAudioInstances: MockAudio[] = [];

class MockAudio {
  src: string = "";
  preload: string = "";
  volume: number = 1;
  currentTime: number = 0;
  
  constructor(src?: string) {
    if (src) this.src = src;
    mockAudioInstances.push(this);
  }
  
  play = mockPlay;
}

(global as unknown as { Audio: typeof MockAudio }).Audio = MockAudio;

// Mock localStorage
const mockLocalStorage: Record<string, string> = {};
const localStorageMock = {
  getItem: jest.fn((key: string) => mockLocalStorage[key] ?? null),
  setItem: jest.fn((key: string, value: string) => {
    mockLocalStorage[key] = value;
  }),
  removeItem: jest.fn((key: string) => {
    delete mockLocalStorage[key];
  }),
  clear: jest.fn(() => {
    Object.keys(mockLocalStorage).forEach((key) => delete mockLocalStorage[key]);
  }),
};

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
  writable: true,
});

describe("useFeedback", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockAudioInstances.length = 0;
    localStorageMock.clear();
  });

  describe("initialization", () => {
    it("should initialize with default preferences enabled", () => {
      const { result } = renderHook(() => useFeedback());

      expect(result.current.preferences.soundEnabled).toBe(true);
      expect(result.current.preferences.vibrationEnabled).toBe(true);
    });

    it("should load preferences from localStorage", () => {
      mockLocalStorage["feedback_sound_enabled"] = "false";
      mockLocalStorage["feedback_vibration_enabled"] = "false";

      const { result } = renderHook(() => useFeedback());

      expect(result.current.preferences.soundEnabled).toBe(false);
      expect(result.current.preferences.vibrationEnabled).toBe(false);
    });

    it("should preload all sound files", () => {
      renderHook(() => useFeedback());

      // Should create 5 audio instances (success, error, start, stop, tap)
      expect(mockAudioInstances.length).toBe(5);
      expect(mockAudioInstances.every((a) => a.preload === "auto")).toBe(true);
    });
  });

  describe("feedback methods", () => {
    it("should trigger vibration and sound on success()", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.success();
      });

      expect(mockVibrate).toHaveBeenCalledWith([20, 50, 20]);
      expect(mockPlay).toHaveBeenCalled();
    });

    it("should trigger vibration and sound on error()", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.error();
      });

      expect(mockVibrate).toHaveBeenCalledWith([100, 50, 100]);
      expect(mockPlay).toHaveBeenCalled();
    });

    it("should trigger vibration and sound on start()", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.start();
      });

      expect(mockVibrate).toHaveBeenCalledWith(50);
      expect(mockPlay).toHaveBeenCalled();
    });

    it("should trigger vibration and sound on stop()", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.stop();
      });

      expect(mockVibrate).toHaveBeenCalledWith([20, 30, 40]);
      expect(mockPlay).toHaveBeenCalled();
    });

    it("should trigger vibration and sound on tap()", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.tap();
      });

      expect(mockVibrate).toHaveBeenCalledWith(30);
      expect(mockPlay).toHaveBeenCalled();
    });
  });

  describe("preference controls", () => {
    it("should not vibrate when vibration is disabled", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.setVibrationEnabled(false);
      });

      act(() => {
        result.current.success();
      });

      expect(mockVibrate).not.toHaveBeenCalled();
      expect(mockPlay).toHaveBeenCalled(); // Sound should still play
    });

    it("should not play sound when sound is disabled", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.setSoundEnabled(false);
      });

      jest.clearAllMocks();

      act(() => {
        result.current.success();
      });

      expect(mockPlay).not.toHaveBeenCalled();
      expect(mockVibrate).toHaveBeenCalled(); // Vibration should still work
    });

    it("should not trigger any feedback when both are disabled", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.setSoundEnabled(false);
        result.current.setVibrationEnabled(false);
      });

      jest.clearAllMocks();

      act(() => {
        result.current.success();
      });

      expect(mockPlay).not.toHaveBeenCalled();
      expect(mockVibrate).not.toHaveBeenCalled();
    });

    it("should persist sound preference to localStorage", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.setSoundEnabled(false);
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "feedback_sound_enabled",
        "false"
      );
    });

    it("should persist vibration preference to localStorage", () => {
      const { result } = renderHook(() => useFeedback());

      act(() => {
        result.current.setVibrationEnabled(false);
      });

      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "feedback_vibration_enabled",
        "false"
      );
    });
  });

  describe("edge cases", () => {
    it("should handle missing navigator.vibrate gracefully", () => {
      const originalVibrate = navigator.vibrate;
      Object.defineProperty(navigator, "vibrate", {
        value: undefined,
        writable: true,
        configurable: true,
      });

      const { result } = renderHook(() => useFeedback());

      // Should not throw
      expect(() => {
        act(() => {
          result.current.success();
        });
      }).not.toThrow();

      // Restore
      Object.defineProperty(navigator, "vibrate", {
        value: originalVibrate,
        writable: true,
        configurable: true,
      });
    });

    it("should handle audio play rejection gracefully", async () => {
      mockPlay.mockRejectedValueOnce(new Error("Autoplay blocked"));

      const { result } = renderHook(() => useFeedback());

      // Should not throw
      expect(() => {
        act(() => {
          result.current.success();
        });
      }).not.toThrow();
    });
  });
});
