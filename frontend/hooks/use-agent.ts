"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useQueryClient } from '@tanstack/react-query';

// SSE Event Types
type AgentEventType =
  | "agent.thought"
  | "agent.response"
  | "agent.error"
  | "agent.clarification";

interface AgentThought {
  step: string;
  message: string;
  timestamp: string;
}

interface AgentResponse {
  log_id: string;
  nutritional_data: Record<string, unknown>;
  status: string;
}

interface AgentError {
  code: string;
  message: string;
}

interface AgentClarification {
  question: string;
  options: string[];
  context: Record<string, unknown>;
  log_id: string;
}

interface SSEEvent {
  type: AgentEventType;
  payload: AgentThought | AgentResponse | AgentError | AgentClarification;
}

export type AgentStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "clarifying"
  | "complete"
  | "error";

export interface UseAgentReturn {
  status: AgentStatus;
  thoughts: string[];
  result: AgentResponse | null;
  error: string | null;
  clarification: AgentClarification | null;
  startStreaming: (logId: string, imagePath?: string, audioPath?: string) => void;
  submitClarificationResponse: (response: string, isVoice?: boolean) => Promise<void>;
  skipClarification: () => void;
  reset: () => void;
}

// Ding sound for completion feedback
const DING_SOUND_URL = "/sounds/ding.mp3";
const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff
const CLARIFICATION_TIMEOUT_MS = 30000; // 30 seconds

// Define API Base URL to match api.ts logic, but inclusive of NEXT_PUBLIC_API_URL from env
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import { supabase } from "@/lib/supabase";

export const useAgent = (): UseAgentReturn => {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clarification, setClarification] = useState<AgentClarification | null>(
    null
  );

  const eventSourceRef = useRef<EventSource | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const retryCountRef = useRef(0);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const clarificationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentRequestRef = useRef<{
    logId: string;
    imagePath?: string;
    audioPath?: string;
  } | null>(null);

  // Preload the ding sound
  useEffect(() => {
    audioRef.current = new Audio(DING_SOUND_URL);
    audioRef.current.preload = "auto";
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (heartbeatTimeoutRef.current) {
        clearTimeout(heartbeatTimeoutRef.current);
      }
      if (clarificationTimeoutRef.current) {
        clearTimeout(clarificationTimeoutRef.current);
      }
    };
  }, []);

  // Network state detection
  useEffect(() => {
    const handleOnline = () => {
      // If we were streaming and went offline, retry
      if (status === "connecting" && currentRequestRef.current) {
        const { logId, imagePath, audioPath } = currentRequestRef.current;
        // Reset and retry after brief delay
        setTimeout(
          () => startStreamingInternal(logId, imagePath, audioPath),
          1000
        );
      }
    };

    const handleOffline = () => {
      if (status === "streaming" || status === "connecting") {
        setError("Waiting for connection...");
      }
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [status]);

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
    if (clarificationTimeoutRef.current) {
      clearTimeout(clarificationTimeoutRef.current);
      clarificationTimeoutRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    cleanup();
    setStatus("idle");
    setThoughts([]);
    setResult(null);
    setError(null);
    setClarification(null);
    retryCountRef.current = 0;
    currentRequestRef.current = null;
  }, [cleanup]);

  const triggerCompletionFeedback = useCallback(() => {
    // Play ding sound
    if (audioRef.current) {
      audioRef.current.play().catch(() => {
        // Ignore audio play errors (autoplay policies)
      });
    }

    // Haptic feedback on supported devices
    if (navigator.vibrate) {
      navigator.vibrate(50);
    }
  }, []);

  const resetHeartbeatTimer = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
    }
    // Expect heartbeat every 15s + some buffer
    heartbeatTimeoutRef.current = setTimeout(() => {
      // Heartbeat missed - connection may be stale
      if (
        status === "streaming" &&
        currentRequestRef.current &&
        retryCountRef.current < MAX_RETRIES
      ) {
        cleanup();
        const { logId, imagePath, audioPath } = currentRequestRef.current;
        retryCountRef.current++;
        const delay = RETRY_DELAYS[retryCountRef.current - 1] ?? 4000;
        setTimeout(
          () => startStreamingInternal(logId, imagePath, audioPath),
          delay
        );
      }
    }, 20000); // 15s heartbeat + 5s buffer
  }, [status, cleanup]);

  const skipClarification = useCallback(() => {
    if (clarification && currentRequestRef.current) {
      // Clear clarification state and continue with analysis
      setClarification(null);
      setStatus("streaming");
      // The backend will handle max attempts and proceed to finalize
    }
  }, [clarification]);

  const startStreamingInternal = useCallback(
    async (logId: string, imagePath?: string, audioPath?: string) => {
      cleanup();
      setStatus("connecting");
      setError(null);

      try {
        const { data: { session } } = await supabase.auth.getSession();
        
        // We're using POST for SSE, which EventSource doesn't support natively.
        // Use fetch with ReadableStream instead.
        const response = await fetch(`${API_BASE_URL}/api/v1/analysis/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(session?.access_token ? { "Authorization": `Bearer ${session.access_token}` } : {})
          },
          body: JSON.stringify({
            log_id: logId,
            image_path: imagePath,
            audio_path: audioPath,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        setStatus("streaming");
        resetHeartbeatTimer();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE messages (ending with \n\n)
          const messages = buffer.split("\n\n");
          buffer = messages.pop() ?? ""; // Keep incomplete message in buffer

          for (const message of messages) {
            if (!message.trim()) continue;

            // Handle heartbeat comments
            if (message.startsWith(":")) {
              resetHeartbeatTimer();
              continue;
            }

            // Parse data lines
            if (message.startsWith("data: ")) {
              const jsonStr = message.slice(6);
              try {
                const event = JSON.parse(jsonStr) as SSEEvent;
                resetHeartbeatTimer();

                if (event.type === "agent.thought") {
                  const thought = event.payload as AgentThought;
                  setThoughts((prev) => [...prev, thought.message]);
                } else if (event.type === "agent.response") {
                  const response = event.payload as AgentResponse;
                  setResult(response);
                  setStatus("complete");
                  triggerCompletionFeedback();
                  // Invalidate logs query to update dashboard
                  queryClient.invalidateQueries({ queryKey: ['logs'] });
                  cleanup();
                  return;
                } else if (event.type === "agent.error") {
                  const err = event.payload as AgentError;
                  setError(err.message);
                  setStatus("error");
                  cleanup();
                  return;
                } else if (event.type === "agent.clarification") {
                  const clarify = event.payload as AgentClarification;
                  setClarification(clarify);
                  setStatus("clarifying");

                  // Start clarification timeout
                  clarificationTimeoutRef.current = setTimeout(() => {
                    // Auto-skip after timeout
                    skipClarification();
                  }, CLARIFICATION_TIMEOUT_MS);

                  cleanup();
                  return;
                }
              } catch (parseError) {
                console.error("Failed to parse SSE event:", parseError);
              }
            }
          }
        }

        // Stream ended without response - check if complete
        if (status !== "complete" && status !== "error") {
          setStatus("complete");
          cleanup();
        }
      } catch (err) {
        console.error("Streaming error:", err);

        // Retry with exponential backoff
        if (retryCountRef.current < MAX_RETRIES) {
          retryCountRef.current++;
          const delay = RETRY_DELAYS[retryCountRef.current - 1] ?? 4000;
          setError("Reconnecting...");
          setTimeout(
            () => startStreamingInternal(logId, imagePath, audioPath),
            delay
          );
        } else {
          setError(err instanceof Error ? err.message : "Connection failed");
          setStatus("error");
          cleanup();
        }
      }
    },
    [cleanup, resetHeartbeatTimer, triggerCompletionFeedback, skipClarification]
  );

  const submitClarificationResponse = useCallback(
    async (response: string, isVoice = false) => {
      if (!clarification) return;

      try {
        setStatus("connecting"); // Show connecting instead of generic streaming during transition
        const logId = clarification.log_id;
        setClarification(null);

        // Clear clarification timeout
        if (clarificationTimeoutRef.current) {
          clearTimeout(clarificationTimeoutRef.current);
        }

        const { data: { session } } = await supabase.auth.getSession();

        // Submit clarification to backend
        const res = await fetch(`${API_BASE_URL}/api/v1/analysis/clarify/${logId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(session?.access_token ? { "Authorization": `Bearer ${session.access_token}` } : {})
          },
          body: JSON.stringify({
            response,
            is_voice: isVoice,
          }),
        });

        if (!res.ok) {
          throw new Error(`Failed to submit clarification: ${res.status}`);
        }

        // Re-trigger streaming for the log to get updated analysis
        const data = await res.json();
        if (data.status === "processing") {
           // Reuse current image/audio paths if available
           const currentRequest = currentRequestRef.current;
           await startStreamingInternal(
             logId, 
             currentRequest?.imagePath, 
             currentRequest?.audioPath
           );
        } else {
             // Fallback if status isn't processing (unexpected)
             setStatus("complete");
             triggerCompletionFeedback();
        }

      } catch (err) {
        console.error("Clarification submission error:", err);
        setError("Failed to submit clarification. Try again.");
        setStatus("error");
      }
    },
    [clarification, triggerCompletionFeedback, startStreamingInternal]
  );

  const startStreaming = useCallback(
    (logId: string, imagePath?: string, audioPath?: string) => {
      // Store current request for potential retries
      currentRequestRef.current = { logId, imagePath, audioPath };
      retryCountRef.current = 0;
      setThoughts([]);
      setResult(null);
      setClarification(null);
      startStreamingInternal(logId, imagePath, audioPath);
    },
    [startStreamingInternal]
  );

  return {
    status,
    thoughts,
    result,
    error,
    clarification,
    startStreaming,
    submitClarificationResponse,
    skipClarification,
    reset,
  };
};
