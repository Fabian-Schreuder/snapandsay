import { useState, useRef, useCallback, useEffect } from "react";

export interface UseAudioReturn {
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
  isRecording: boolean;
  audioBlob: Blob | null;
  error: Error | null;
  isPermissionDenied: boolean;
}

export const useAudio = (): UseAudioReturn => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isPermissionDenied, setIsPermissionDenied] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    mediaRecorderRef.current = null;
  }, []);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  const startRecording = useCallback(async () => {
    setError(null);
    setIsPermissionDenied(false);
    setAudioBlob(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Determine mimeType
      let mimeType = "audio/webm"; // Default
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mimeType = "audio/webm;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        mimeType = "audio/mp4"; // iOS Safari fallback
      }

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        setAudioBlob(blob);
        chunksRef.current = [];
        cleanup(); // Cleanup stream after stop
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err: unknown) {
      const error = err instanceof Error ? err : new Error(String(err));
      console.error("Error starting recording:", error);
      setError(error);
      if (
        error instanceof DOMException &&
        (error.name === "NotAllowedError" || error.name === "PermissionDeniedError")
      ) {
        setIsPermissionDenied(true);
      }
      cleanup();
    }
  }, [cleanup]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      // Prevent onstop from firing and saving the blob
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setAudioBlob(null);
      chunksRef.current = [];
      cleanup();
    }
  }, [cleanup]);

  return {
    startRecording,
    stopRecording,
    cancelRecording,
    isRecording,
    audioBlob,
    error,
    isPermissionDenied,
  };
};
