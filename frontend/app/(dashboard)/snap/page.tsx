"use client"
import React, { useState } from 'react'
import CameraCapture from '@/components/features/camera/CameraCapture'
import ImagePreview from '@/components/features/camera/ImagePreview'

export default function SnapPage() {
  const [capturedImage, setCapturedImage] = useState<string | null>(null);

  const handleCapture = (imageSrc: string) => {
    setCapturedImage(imageSrc);
  };

  const handleRetake = () => {
    setCapturedImage(null);
  };

  const handleConfirm = () => {
    // TODO: Navigate to next step or handle confirm action (Story 2.2/2.3)
    // Removed verbose logging for performance
  };

  return (
    <div className="h-[100dvh] w-full bg-black">
      {!capturedImage ? (
        <CameraCapture onCapture={handleCapture} />
      ) : (
        <ImagePreview 
          imageSrc={capturedImage} 
          onRetake={handleRetake} 
          onConfirm={handleConfirm} 
        />
      )}
    </div>
  )
}
