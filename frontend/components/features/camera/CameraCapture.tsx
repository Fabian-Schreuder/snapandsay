"use client"
import React, { useRef, useCallback, useState, useEffect } from 'react'
import Webcam from 'react-webcam'
import { Camera } from 'lucide-react'
import { cn } from '@/lib/utils'

interface CameraCaptureProps {
  onCapture: (imageSrc: string) => void;
}

const videoConstraints = {
  facingMode: { ideal: "environment" }
};

export default function CameraCapture({ onCapture }: CameraCaptureProps) {
  const webcamRef = useRef<Webcam>(null);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [isFlashing, setIsFlashing] = useState(false);
  
  // Refs for cleanup
  const flashTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const captureTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
      if (captureTimeoutRef.current) clearTimeout(captureTimeoutRef.current);
    };
  }, []);

  const capture = useCallback(() => {
    // 1. Visual Flash Effect
    setIsFlashing(true);
    // Shorter, snappier flash (75ms)
    flashTimeoutRef.current = setTimeout(() => setIsFlashing(false), 75); 

    // 2. Haptic Feedback
    if (typeof navigator !== 'undefined' && navigator.vibrate) {
      navigator.vibrate(50);
    }

    const imageSrc = webcamRef.current?.getScreenshot();
    
    if (imageSrc) {
      // Wait for flash peak before transitioning
      captureTimeoutRef.current = setTimeout(() => {
        onCapture(imageSrc);
      }, 100);
    }
  }, [webcamRef, onCapture]);

  const handleUserMediaError = useCallback((error: string | DOMException) => {
    console.error("Camera Error:", error);
    setPermissionDenied(true);
    
    // Distinguish between permission and constraint errors
    if (typeof error === 'object' && 'name' in error && error.name === 'OverconstrainedError') {
         setError("Camera resolution not supported. Please try a different device.");
    } else if (typeof error === 'object' && 'name' in error && error.name === 'NotAllowedError') {
         setError("Camera permission denied. Please allow access in settings.");
    } else {
         setError("We need camera access to see your meal.");
    }
  }, []);

  const handleUserMedia = useCallback(() => {
    setError(null);
    setPermissionDenied(false);
  }, []);

  const handleRetry = useCallback(() => {
    setError(null);
    setPermissionDenied(false);
  }, []);

  // Relaxed constraints: Use ideal instead of strict min to prevent OverconstrainedError on low-end devices
  // while still preferring high resolution.
  const videoConstraintsWithResolution = {
    ...videoConstraints,
    width: { ideal: 1920 },
    height: { ideal: 1080 }
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
        key={permissionDenied ? 'error' : 'active'}
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
          "absolute inset-0 bg-white pointer-events-none transition-opacity duration-75 ease-out z-20",
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
