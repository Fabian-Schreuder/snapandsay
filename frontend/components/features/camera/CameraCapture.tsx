"use client"
import React, { useRef, useCallback, useState, useEffect } from 'react'
import Webcam from 'react-webcam'
import { Camera } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CameraCaptureProps {
  onCapture: (imageSrc: string) => void;
}

const videoConstraints = {
  facingMode: "environment"
};

export default function CameraCapture({ onCapture }: CameraCaptureProps) {
  const webcamRef = useRef<Webcam>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [isFlashing, setIsFlashing] = useState(false);

  const capture = useCallback(() => {
    // 1. Visual Flash Effect
    setIsFlashing(true);
    setTimeout(() => setIsFlashing(false), 150); // Short flash

    // 2. Haptic Feedback
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(50);
    }

    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      // Small delay to allow flash to register visually before unmounting/transitioning
      setTimeout(() => {
        onCapture(imageSrc);
      }, 100);
    }
  }, [webcamRef, onCapture]);

  const handleUserMediaError = useCallback((error: string | DOMException) => {
    console.error("Camera Error:", error);
    setPermissionDenied(true);
    setError("We need camera access to see your meal.");
  }, []);

  const handleUserMedia = useCallback(() => {
    setError(null);
    setPermissionDenied(false);
  }, []);

  const handleRetry = useCallback(() => {
    // Reset state to try re-mounting/re-initializing the camera
    setError(null);
    setPermissionDenied(false);
    // Force a re-render of the Webcam component might be needed if it internalizes error state,
    // but React key change or state toggle is usually enough. 
    // If simple state reset doesn't work with react-webcam, we might need a key.
  }, []);

  // Standard HD landscape, but 'environment' facing mode is key
  const videoConstraintsWithResolution = {
    ...videoConstraints,
    width: { min: 1280, ideal: 1920 },
    height: { min: 720, ideal: 1080 }
  };

  if (error || permissionDenied) {
    return (
      <div className="h-full w-full bg-zinc-900 flex flex-col items-center justify-center p-8 text-center space-y-6">
        <div className="h-20 w-20 rounded-full bg-red-100 flex items-center justify-center mb-4">
           <Camera className="h-10 w-10 text-red-600" />
        </div>
        <h3 className="text-xl font-semibold text-white">Camera Access Needed</h3>
        <p className="text-zinc-300 text-lg max-w-xs">{error || "We need permission to use your camera so you can snap your meal."}</p>
        <button 
          onClick={handleRetry}
          className="px-8 py-4 bg-primary text-primary-foreground rounded-full font-bold text-lg hover:opacity-90 transition-opacity"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full bg-black flex flex-col items-center justify-center overflow-hidden">
      <Webcam
        key={permissionDenied ? 'error' : 'active'} // Force re-mount on state recover
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        videoConstraints={videoConstraintsWithResolution}
        onUserMedia={handleUserMedia}
        onUserMediaError={handleUserMediaError}
        className="absolute inset-0 h-full w-full object-cover"
      />
      
      {/* Visual Flash Overlay */}
      <div 
        className={cn(
          "absolute inset-0 bg-white pointer-events-none transition-opacity duration-150 ease-out z-20",
           isFlashing ? "opacity-100" : "opacity-0"
        )}
      />

      {/* Shutter Button Overlay */}
      <div className="absolute bottom-10 z-10 w-full flex justify-center pb-8">
            <button
            onClick={capture}
            aria-label="Shutter button"
            className={cn(
              "h-20 w-20 rounded-full bg-white border-4 border-gray-300",
              "flex items-center justify-center",
              "hover:bg-gray-100 active:scale-95 transition-all shadow-lg",
              "focus:outline-none focus:ring-4 focus:ring-primary/50"
            )}
            >
             <Camera className="h-8 w-8 text-black opacity-80" />
            </button>
      </div>
    </div>
  )
}
