"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAudio } from "../../../hooks/use-audio";
import {
  AlertDialog,
  AlertDialogContent,
} from "@/components/ui/alert-dialog";
import PermissionErrorState from "../camera/PermissionErrorState";
import { VoiceButton, VoiceButtonState } from "@/components/ui/voice-button";

interface VoiceCaptureButtonProps {
  onRecordingComplete: (audio: Blob) => void;
  className?: string;
}

export const VoiceCaptureButton: React.FC<VoiceCaptureButtonProps> = ({
  onRecordingComplete,
  className,
}) => {
  const {
    startRecording,
    stopRecording,
    isRecording,
    audioBlob,
    error,
    isPermissionDenied,
  } = useAudio();

  const [buttonState, setButtonState] = useState<VoiceButtonState>("idle");
  const [showPermissionDialog, setShowPermissionDialog] = useState(false);

  // Sync hook state to button state
  useEffect(() => {
    if (isPermissionDenied) {
      setButtonState("error");
      setShowPermissionDialog(true);
    } else if (audioBlob) {
      setButtonState("success");
    } else if (isRecording) {
      setButtonState("recording");
    } else {
      setButtonState("idle");
    }
  }, [isPermissionDenied, audioBlob, isRecording]);

  // Handle successful recording completion
  useEffect(() => {
    if (audioBlob) {
      // Vibrate for success
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([20, 50, 20]);
      }
      onRecordingComplete(audioBlob);
    }
  }, [audioBlob, onRecordingComplete]);

  // Click-to-toggle handler
  const handleToggleRecording = useCallback(async () => {
    // If permission blocked, ensure dialog is shown
    if (isPermissionDenied) {
      setShowPermissionDialog(true);
      return;
    }

    if (isRecording) {
      // Stop logic
      stopRecording();
    } else {
      // Start logic
      try {
        if (typeof navigator !== "undefined" && navigator.vibrate) {
          navigator.vibrate(50); // Single bump for start
        }
        await startRecording();
      } catch (err) {
        // Error is handled by hook state
        console.error("Failed to start recording", err);
      }
    }
  }, [isRecording, isPermissionDenied, stopRecording, startRecording]);

  const handleRetry = () => {
    window.location.reload();
  };

  return (
    <div className="flex flex-col items-center gap-2">
      <AlertDialog
        open={showPermissionDialog}
        onOpenChange={setShowPermissionDialog}
      >
        <AlertDialogContent className="p-0 border-none bg-zinc-900 max-w-none w-screen h-screen rounded-none flex items-center justify-center">
          <PermissionErrorState
            mediaType="microphone"
            errorType="permission"
            onRetry={handleRetry}
            className="bg-zinc-900 border-none"
          />
        </AlertDialogContent>
      </AlertDialog>

      <VoiceButton
        state={buttonState}
        onClick={handleToggleRecording}
        className={`${className} w-20 h-20 rounded-full`}
        waveformClassName="rounded-full"
        size="icon"
        variant="default" 
        // We use size="icon" to keep it compact, but we could allow a label if desired.
        // The original was a circle (w-20 h-20), VoiceButton size="icon" might be smaller (w-10 h-10).
        // If we want it larger, we can override className.
      />

      {error && !isPermissionDenied && (
        <p className="text-xs text-red-500 text-center max-w-[150px]">
          Error: {error.message}
        </p>
      )}
    </div>
  );
};
