"use client"
import React, { useRef, useCallback, useState, useEffect } from 'react'
import Webcam from 'react-webcam'
import { Camera } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useFeedback } from '@/hooks/use-feedback'
import PermissionErrorState from './PermissionErrorState'

interface CameraCaptureProps {
  onCapture: (imageSrc: string) => void;
}

const videoConstraints = {
  facingMode: { ideal: "environment" }
};

export default function CameraCapture({ onCapture }: CameraCaptureProps) {
  const webcamRef = useRef<Webcam>(null);
  const [errorType, setErrorType] = useState<'permission' | 'device' | 'unknown' | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isFlashing, setIsFlashing] = useState(false);
  const feedback = useFeedback();
  // Refs for cleanup
  const flashTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const captureTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Proactively check permission status if available
    let status: PermissionStatus | undefined;

    if (typeof navigator !== 'undefined' && navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: 'camera' as PermissionName })
        .then((permissionStatus) => {
          status = permissionStatus;
          // Initial check
          if (permissionStatus.state === 'granted') {
             setErrorType(null);
          }
          
          permissionStatus.onchange = () => {
            // If permission is granted after being denied, we might want to auto-recover
            if (permissionStatus.state === 'granted') {
              setErrorType(null);
            }
          };
        })
        .catch(() => {
          // Firefox doesn't fully support 'camera' in permissions API yet, just ignore
        });
    }

    return () => {
      // Cleanup listener if needed, though browser handles this mostly
      if (status) {
          status.onchange = null;
      }
      if (flashTimeoutRef.current) clearTimeout(flashTimeoutRef.current);
      if (captureTimeoutRef.current) clearTimeout(captureTimeoutRef.current);
    };
  }, []);

  const capture = useCallback(() => {
    // 1. Visual Flash Effect
    setIsFlashing(true);
    // Shorter, snappier flash (75ms)
    flashTimeoutRef.current = setTimeout(() => setIsFlashing(false), 75); 

    // 2. Haptic Feedback via feedback hook
    feedback.tap();

    const imageSrc = webcamRef.current?.getScreenshot();
    
    if (imageSrc) {
      // Wait for flash peak before transitioning
      captureTimeoutRef.current = setTimeout(() => {
        onCapture(imageSrc);
      }, 100);
    }
  }, [webcamRef, onCapture, feedback]);

  const handleUserMediaError = useCallback((error: string | DOMException) => {
    console.error("Camera Error:", error);
    
    // Distinguish between permission and constraint errors
    if (typeof error === 'object' && 'name' in error) {
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
         setErrorType('permission');
         setErrorMessage(null); // Use default message in UI
      } else if (error.name === 'OverconstrainedError') {
         setErrorType('device');
         setErrorMessage("Camera resolution not supported. Please try a different device.");
      } else if (error.name === 'NotFoundError') {
        setErrorType('device');
        setErrorMessage("No camera found on this device.");
      } else if (error.name === 'NotReadableError') {
        setErrorType('device');
        setErrorMessage("Camera is currently in use by another application.");
      } else {
         setErrorType('unknown');
         setErrorMessage("We encountered an error accessing your camera.");
      }
    } else {
         setErrorType('unknown');
         setErrorMessage("We need camera access to see your meal.");
    }
  }, []);

  const handleUserMedia = useCallback(() => {
    setErrorType(null);
    setErrorMessage(null);
  }, []);

  const handleRetry = useCallback(() => {
    if (errorType === 'permission') {
       // Hard reload is often required to re-trigger permission prompt after a denial
       // or at least force the browser to re-evaluate the permission state
       window.location.reload();
    } else {
       // Soft retry for other errors
       setErrorType(null);
       setErrorMessage(null);
    }
  }, [errorType]);

  // Relaxed constraints: Use ideal instead of strict min to prevent OverconstrainedError on low-end devices
  // while still preferring high resolution.
  const videoConstraintsWithResolution = {
    ...videoConstraints,
    width: { ideal: 1920 },
    height: { ideal: 1080 }
  };

  if (errorType) {
    return (
      <PermissionErrorState 
        errorType={errorType}
        errorMessage={errorMessage || undefined}
        onRetry={handleRetry}
      />
    )
  }

  return (
    <div className="relative h-full w-full bg-black flex flex-col items-center justify-center overflow-hidden">
      <Webcam
        key={errorType ? 'error' : 'active'}
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
