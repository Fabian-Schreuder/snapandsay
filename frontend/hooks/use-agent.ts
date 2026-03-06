"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useFeedback } from "./use-feedback";

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

interface ClarificationItem {
  item_name: string;
  question: string;
  options: string[];
}

interface AgentClarification {
  questions: ClarificationItem[];
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
  startStreaming: (
    logId: string,
    imagePath?: string,
    audioPath?: string,
    options?: { force_clarify?: boolean; force_finalize?: boolean },
  ) => void;
  submitClarificationResponse: (
    responses: Array<{
      item_name: string;
      response: string;
      is_voice?: boolean;
      audio_path?: string;
    }>,
  ) => Promise<void>;
  submitText: (text: string) => Promise<void>;
  skipClarification: () => void;
  reset: () => void;
}

// Ding sound for completion feedback
// (UseFeedback hook imported at top)

const MAX_RETRIES = 3;
const RETRY_DELAYS = [1000, 2000, 4000]; // Exponential backoff
const CLARIFICATION_TIMEOUT_MS = 30000; // 30 seconds

// Define API Base URL to match api.ts logic, but inclusive of NEXT_PUBLIC_API_URL from env
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

import { supabase } from "@/lib/supabase";
import { analysisApi } from "@/lib/api";

export const useAgent = (): UseAgentReturn => {
  const queryClient = useQueryClient();
  const locale = useLocale();
  const statusLocale = locale === "en" || locale === "nl" ? locale : "nl"; // Type guard
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [result, setResult] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clarification, setClarification] = useState<AgentClarification | null>(
    null,
  );

  const eventSourceRef = useRef<EventSource | null>(null);
  const retryCountRef = useRef(0);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const clarificationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentRequestRef = useRef<{
    logId: string;
    imagePath?: string;
    audioPath?: string;
    options?: { force_clarify?: boolean; force_finalize?: boolean };
  } | null>(null);

  // Use centralized feedback hook
  const feedback = useFeedback();

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
        const { logId, imagePath, audioPath, options } =
          currentRequestRef.current;
        // Reset and retry after brief delay
        setTimeout(
          () =>
            startStreamingInternal(logId, imagePath, audioPath, options),
          1000,
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    feedback.success();
  }, [feedback]);

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
        const { logId, imagePath, audioPath, options } =
          currentRequestRef.current;
        retryCountRef.current++;
        const delay = RETRY_DELAYS[retryCountRef.current - 1] ?? 4000;
        setTimeout(
          () => startStreamingInternal(logId, imagePath, audioPath, options),
          delay,
        );
      }
    }, 20000); // 15s heartbeat + 5s buffer
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    async (
      logId: string,
      imagePath?: string,
      audioPath?: string,
      options?: { force_clarify?: boolean; force_finalize?: boolean },
    ) => {
      cleanup();
      setStatus("connecting");
      setError(null);

      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();

        // We're using POST for SSE, which EventSource doesn't support natively.
        // Use fetch with ReadableStream instead.
        const response = await fetch(`${API_BASE_URL}/api/v1/analysis/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(session?.access_token
              ? { Authorization: `Bearer ${session.access_token}` }
              : {}),
          },
          body: JSON.stringify({
            log_id: logId,
            image_path: imagePath,
            audio_path: audioPath,
            language: statusLocale,
            force_clarify: options?.force_clarify,
            force_finalize: options?.force_finalize,
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
                  queryClient.invalidateQueries({ queryKey: ["logs"] });
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
            delay,
          );
        } else {
          setError(err instanceof Error ? err.message : "Connection failed");
          setStatus("error");
          cleanup();
        }
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      cleanup,
      resetHeartbeatTimer,
      triggerCompletionFeedback,
      skipClarification,
      statusLocale,
    ],
  );

  const submitClarificationResponse = useCallback(
    async (
      responses: Array<{
        item_name: string;
        response: string;
        is_voice?: boolean;
        audio_path?: string;
      }>,
    ) => {
      if (!clarification) return;

      try {
        setStatus("connecting");
        const logId = clarification.log_id;
        setClarification(null);

        if (clarificationTimeoutRef.current) {
          clearTimeout(clarificationTimeoutRef.current);
        }

        const {
          data: { session },
        } = await supabase.auth.getSession();

        // Submit all clarification responses in one batch POST
        const res = await fetch(
          `${API_BASE_URL}/api/v1/analysis/clarify/${logId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(session?.access_token
                ? { Authorization: `Bearer ${session.access_token}` }
                : {}),
            },
            body: JSON.stringify({
              responses: responses.map((r) => ({
                item_name: r.item_name,
                response: r.response,
                is_voice: r.is_voice ?? false,
                ...(r.audio_path ? { audio_path: r.audio_path } : {}),
              })),
            }),
          },
        );

        if (!res.ok) {
          throw new Error(`Failed to submit clarification: ${res.status}`);
        }

        // Re-trigger streaming for the log to get updated analysis
        const data = await res.json();
        if (data.status === "processing") {
          const currentRequest = currentRequestRef.current;
          await startStreamingInternal(
            logId,
            currentRequest?.imagePath,
            currentRequest?.audioPath,
            currentRequest?.options,
          );
        } else {
          setStatus("complete");
          triggerCompletionFeedback();
        }
      } catch (err) {
        console.error("Clarification submission error:", err);
        setError("Failed to submit clarification. Try again.");
        setStatus("error");
      }
    },
    [clarification, triggerCompletionFeedback, startStreamingInternal],
  );

  const startStreaming = useCallback(
    (
      logId: string,
      imagePath?: string,
      audioPath?: string,
      options?: { force_clarify?: boolean; force_finalize?: boolean },
    ) => {
      // Store current request for potential retries
      currentRequestRef.current = { logId, imagePath, audioPath, options };
      retryCountRef.current = 0;
      setThoughts([]);
      setResult(null);
      setClarification(null);
      startStreamingInternal(logId, imagePath, audioPath, options);
    },
    [startStreamingInternal],
  );

  const submitText = useCallback(async (text: string) => {
    try {
      cleanup();
      setStatus("connecting");
      setError(null);

      // 1. Upload/Create Log
      const response = await analysisApi.upload({
        text_input: text,
        client_timestamp: new Date().toISOString(),
        language: statusLocale,
      });

      const newLogId = response.log_id;

      // 2. Start Streaming
      // We pass undefined for image/audio paths as this is text-only
      startStreaming(newLogId, undefined, undefined);
    } catch (err) {
      console.error("Text submission failed:", err);
      // Use feedback hook for error sound if available or just set error state
      setError("Failed to submit text. Please try again.");
      setStatus("error");
    }
  }, [cleanup, statusLocale, startStreaming]);

  return {
    status,
    thoughts,
    result,
    error,
    clarification,
    startStreaming,
    submitClarificationResponse,
    submitText,
    skipClarification,
    reset,
  };
};
