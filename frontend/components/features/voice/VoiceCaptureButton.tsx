"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAudio } from "../../../hooks/use-audio";
import { useFeedback } from "../../../hooks/use-feedback";
import { Mic } from "lucide-react";
import { AlertDialog, AlertDialogContent, AlertDialogTitle } from "@/components/ui/alert-dialog";
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
  const feedback = useFeedback();

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
      feedback.success();
      onRecordingComplete(audioBlob);
    }
  }, [audioBlob, onRecordingComplete, feedback]);

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
        feedback.start();
        await startRecording();
      } catch (err) {
        // Error is handled by hook state
        console.error("Failed to start recording", err);
      }
    }
  }, [
    isRecording,
    isPermissionDenied,
    stopRecording,
    startRecording,
    feedback,
  ]);

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
          <AlertDialogTitle className="sr-only">Microphone Permission Required</AlertDialogTitle>
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
        aria-label={
          buttonState === "recording"
            ? "Stop voice recording"
            : buttonState === "processing" || buttonState === "success"
              ? "Processing voice recording"
              : "Start voice recording"
        }
        aria-describedby="tap-to-toggle-text"
        icon={<Mic className="w-8 h-8" />}
      />

      {error && !isPermissionDenied && (
        <p className="text-xs text-red-500 text-center max-w-[150px]">
          Error: {error.message}
        </p>
      )}
    </div>
  );
};
