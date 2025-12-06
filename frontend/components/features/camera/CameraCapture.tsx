"use client"
import React, { useRef, useCallback } from 'react'
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
  const [error, setError] = React.useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = React.useState(false);

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      onCapture(imageSrc);
    }
  }, [webcamRef, onCapture]);

  const handleUserMediaError = useCallback((error: string | DOMException) => {
    console.error("Camera Error:", error);
    // Check for specific permission errors if possible, standardizing fallback
    setPermissionDenied(true);
    setError("We need camera access to see your meal.");
  }, []);

  const handleUserMedia = useCallback(() => {
    setError(null);
    setPermissionDenied(false);
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
           {/* Fallback icon if lucide fails, but we know it's there */}
           <Camera className="h-10 w-10 text-red-600" />
        </div>
        <h3 className="text-xl font-semibold text-white">Camera Access Needed</h3>
        <p className="text-zinc-300 text-lg max-w-xs">{error || "We need permission to use your camera so you can snap your meal."}</p>
        <button 
          onClick={() => window.location.reload()} // Simple retry for now
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
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        videoConstraints={videoConstraintsWithResolution}
        onUserMedia={handleUserMedia}
        onUserMediaError={handleUserMediaError}
        className="absolute inset-0 h-full w-full object-cover"
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
