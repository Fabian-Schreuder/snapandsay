"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, Check } from "lucide-react";
import { useAudio } from "../../../hooks/use-audio";
import { cn } from "@/lib/utils";

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

  const [isSuccess, setIsSuccess] = useState(false);
  const [a11yStatus, setA11yStatus] = useState(""); // For screen reader announcements
  const buttonRef = useRef<HTMLButtonElement>(null);
  const isPressed = useRef(false); // Track physical press state to prevent race conditions

  // Handle successful recording
  useEffect(() => {
    if (audioBlob) {
      setIsSuccess(true);
      setA11yStatus("Recording stopped. Voice note captured.");
      // Vibrate for success: short, pause, short
      if (typeof navigator !== "undefined" && navigator.vibrate) {
        navigator.vibrate([20, 50, 20]);
      }
      onRecordingComplete(audioBlob);

      // Reset success state after a delay
      const timer = setTimeout(() => {
        setIsSuccess(false);
        setA11yStatus(""); // Clear status
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [audioBlob, onRecordingComplete]);

  // Handle start (Touch/Mouse Down)
  const handleStart = async (e: React.PointerEvent | React.TouchEvent | React.MouseEvent) => {
    // Prevent default context menus or selection on long press
    if (e.cancelable) e.preventDefault(); 
    
    isPressed.current = true;

    if (isRecording) return;

    if (typeof navigator !== "undefined" && navigator.vibrate) {
      navigator.vibrate(50); // Single bump for start
    }

    try {
        await startRecording();
        setA11yStatus("Recording started. Release to stop.");
        
        // RACE CONDITION FIX:
        // If the user release the button while `startRecording` (getUserMedia) was pending,
        // we must stop immediately after it starts.
        if (!isPressed.current) {
            stopRecording();
            setA11yStatus("Recording cancelled.");
        }
    } catch (err) {
        // Error is handled by hook state
        setA11yStatus("Error starting recording.");
    }
  };

  // Handle stop (Touch/Mouse Up/Leave)
  const handleStop = (e: React.PointerEvent | React.TouchEvent | React.MouseEvent) => {
    if (e.cancelable) e.preventDefault();
    
    isPressed.current = false;
    
    if (isRecording) {
      stopRecording();
    }
  };

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Hidden live region for screen readers */}
      <div role="status" aria-live="polite" className="sr-only">
        {a11yStatus}
      </div>

      <button
        ref={buttonRef}
        type="button"
        onMouseDown={handleStart}
        onMouseUp={handleStop}
        onMouseLeave={handleStop}
        onTouchStart={handleStart}
        onTouchEnd={handleStop}
        aria-label="Hold to record voice note"
        className={cn(
          "relative flex items-center justify-center w-20 h-20 rounded-full transition-all duration-300 shadow-lg focus:outline-none focus:ring-4 focus:ring-primary/50",
          isRecording ? "bg-red-500 scale-110 animate-pulse" : "bg-primary hover:bg-primary/90",
          isSuccess && "bg-green-500",
          isPermissionDenied && "bg-gray-400 cursor-not-allowed opacity-70",
          className
        )}
        disabled={isPermissionDenied}
      >
        {isSuccess ? (
            <Check className="w-8 h-8 text-white" />
        ) : (
            <Mic className={cn("w-8 h-8 text-white", isRecording && "animate-bounce")} />
        )}
        
        {/* Ripple effect rings when recording */}
        {isRecording && (
          <span className="absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75 animate-ping"></span>
        )}
      </button>

      {isPermissionDenied && (
        <p className="text-xs text-red-500 text-center max-w-[150px]">
          Please enable microphone access in your browser settings to record.
        </p>
      )}
      
      {error && !isPermissionDenied && (
         <p className="text-xs text-red-500 text-center max-w-[150px]">
          Error: {error.message}
        </p>
      )}
    </div>
  );
};
