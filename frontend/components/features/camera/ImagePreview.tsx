"use client"
import React from 'react'
import { X, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ImagePreviewProps {
  imageSrc: string;
  onRetake: () => void;
  onConfirm: () => void;
}

export default function ImagePreview({ imageSrc, onRetake, onConfirm }: ImagePreviewProps) {
  return (
    <div className="relative h-full w-full bg-black flex flex-col items-center justify-center">
      {/* Image Preview - using <img> because imageSrc is a base64 data URL from camera capture */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img 
        src={imageSrc} 
        alt="Captured preview" 
        className="absolute inset-0 h-full w-full object-contain"
      />
      
      {/* Controls Overlay */}
      <div className="absolute bottom-10 z-10 w-full flex justify-between px-12 pb-8">
        
        {/* Retake Button */}
        <button
            onClick={onRetake}
            aria-label="Retake"
            className={cn(
              "h-16 w-16 rounded-full bg-white/20 backdrop-blur-md border border-white/30",
              "flex items-center justify-center text-white",
              "hover:bg-white/30 active:scale-95 transition-all"
            )}
        >
            <X className="h-8 w-8" />
        </button>

        {/* Confirm Button */}
        <button
            onClick={onConfirm}
            aria-label="Confirm"
            className={cn(
              "h-20 w-20 -mt-2 rounded-full bg-white text-primary",
              "flex items-center justify-center shadow-xl",
              "hover:bg-gray-100 active:scale-95 transition-all"
            )}
        >
            <Check className="h-10 w-10 text-black" />
        </button>

         {/* Spacer to balance layout if needed, or just 2 buttons */}
         <div className="w-16"></div> 
      </div>
    </div>
  )
}
