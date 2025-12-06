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

  const capture = useCallback(() => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      onCapture(imageSrc);
    }
  }, [webcamRef, onCapture]);

  return (
    <div className="relative h-full w-full bg-black flex flex-col items-center justify-center overflow-hidden">
      <Webcam
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
        videoConstraints={videoConstraints}
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
