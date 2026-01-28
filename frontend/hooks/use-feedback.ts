"use client";

import { useRef, useCallback, useEffect, useState } from "react";

// Sound file paths
const SOUNDS = {
  success: "/sounds/success.mp3",
  error: "/sounds/error.mp3",
  start: "/sounds/start.mp3",
  stop: "/sounds/stop.mp3",
  tap: "/sounds/tap.mp3",
} as const;

// Vibration patterns (milliseconds) - gentle for older adults
const VIBRATION_PATTERNS: Record<FeedbackType, number | number[]> = {
  success: [20, 50, 20], // Double tap: success confirmation
  error: [100, 50, 100], // Longer double: attention needed
  start: 50, // Single short: action started
  stop: [20, 30, 40], // Ascending: completion
  tap: 30, // Very short: button feedback
};

// localStorage keys
const STORAGE_KEYS = {
  sound: "feedback_sound_enabled",
  vibration: "feedback_vibration_enabled",
} as const;

export type FeedbackType = keyof typeof SOUNDS;

export interface FeedbackPreferences {
  soundEnabled: boolean;
  vibrationEnabled: boolean;
}

export interface UseFeedbackReturn {
  /** Trigger success feedback (e.g., meal logged, analysis complete) */
  success: () => void;
  /** Trigger error feedback (e.g., operation failed) */
  error: () => void;
  /** Trigger start feedback (e.g., recording started) */
  start: () => void;
  /** Trigger stop feedback (e.g., recording stopped) */
  stop: () => void;
  /** Trigger tap feedback (e.g., button pressed, shutter) */
  tap: () => void;
  /** Current feedback preferences */
  preferences: FeedbackPreferences;
  /** Update sound enabled preference */
  setSoundEnabled: (enabled: boolean) => void;
  /** Update vibration enabled preference */
  setVibrationEnabled: (enabled: boolean) => void;
}

/**
 * Read preference from localStorage with SSR safety
 */
function getStoredPreference(key: string, defaultValue: boolean): boolean {
  if (typeof window === "undefined") return defaultValue;
  try {
    const stored = localStorage.getItem(key);
    if (stored === null) return defaultValue;
    return stored === "true";
  } catch {
    // localStorage not available (private browsing, etc.)
    return defaultValue;
  }
}

/**
 * Write preference to localStorage with SSR safety
 */
function setStoredPreference(key: string, value: boolean): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, String(value));
  } catch {
    // localStorage not available
  }
}

/**
 * Centralized feedback hook for haptic and sound feedback.
 * 
 * Provides semantic feedback methods that combine vibration + sound.
 * Respects user preferences stored in localStorage.
 */
export const useFeedback = (): UseFeedbackReturn => {
  // Audio refs for preloaded sounds
  const audioRefs = useRef<Map<FeedbackType, HTMLAudioElement>>(new Map());

  // Preferences state
  const [soundEnabled, setSoundEnabledState] = useState<boolean>(() =>
    getStoredPreference(STORAGE_KEYS.sound, true)
  );
  const [vibrationEnabled, setVibrationEnabledState] = useState<boolean>(() =>
    getStoredPreference(STORAGE_KEYS.vibration, true)
  );

  // Preload all sounds on mount
  useEffect(() => {
    if (typeof window === "undefined") return;

    const entries = Object.entries(SOUNDS) as [FeedbackType, string][];
    const currentAudioRefs = audioRefs.current;
    
    for (const [type, path] of entries) {
      try {
        const audio = new Audio(path);
        audio.preload = "auto";
        audio.volume = 0.5; // Gentle volume for older adults
        currentAudioRefs.set(type, audio);
      } catch (err) {
        console.warn(`Failed to preload sound: ${path}`, err);
      }
    }

    // Cleanup on unmount
    return () => {
      currentAudioRefs.clear();
    };
  }, []);

  /**
   * Trigger vibration if supported and enabled
   */
  const vibrate = useCallback(
    (pattern: number | number[]) => {
      if (!vibrationEnabled) return;
      if (typeof navigator === "undefined") return;
      if (!navigator.vibrate) return;

      try {
        navigator.vibrate(pattern);
      } catch (err) {
        console.warn("Vibration failed:", err);
      }
    },
    [vibrationEnabled]
  );

  /**
   * Play sound if supported and enabled
   */
  const playSound = useCallback(
    (type: FeedbackType) => {
      if (!soundEnabled) return;
      
      const audio = audioRefs.current.get(type);
      if (!audio) return;

      try {
        // Reset to start if already playing
        audio.currentTime = 0;
        audio.play().catch((err) => {
          // Ignore autoplay policy errors - user interaction required
          if (err.name !== "NotAllowedError") {
            console.warn(`Failed to play sound: ${type}`, err);
          }
        });
      } catch (err) {
        console.warn(`Sound playback error: ${type}`, err);
      }
    },
    [soundEnabled]
  );

  /**
   * Trigger feedback (vibration + sound) for a given type
   */
  const triggerFeedback = useCallback(
    (type: FeedbackType) => {
      vibrate(VIBRATION_PATTERNS[type]);
      playSound(type);
    },
    [vibrate, playSound]
  );

  // Preference setters with persistence
  const setSoundEnabled = useCallback((enabled: boolean) => {
    setSoundEnabledState(enabled);
    setStoredPreference(STORAGE_KEYS.sound, enabled);
  }, []);

  const setVibrationEnabled = useCallback((enabled: boolean) => {
    setVibrationEnabledState(enabled);
    setStoredPreference(STORAGE_KEYS.vibration, enabled);
  }, []);

  // Semantic feedback methods
  const success = useCallback(() => triggerFeedback("success"), [triggerFeedback]);
  const error = useCallback(() => triggerFeedback("error"), [triggerFeedback]);
  const start = useCallback(() => triggerFeedback("start"), [triggerFeedback]);
  const stop = useCallback(() => triggerFeedback("stop"), [triggerFeedback]);
  const tap = useCallback(() => triggerFeedback("tap"), [triggerFeedback]);

  return {
    success,
    error,
    start,
    stop,
    tap,
    preferences: {
      soundEnabled,
      vibrationEnabled,
    },
    setSoundEnabled,
    setVibrationEnabled,
  };
};
