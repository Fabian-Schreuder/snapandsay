"use client"
import React, { useState } from 'react'
import CameraCapture from '@/components/features/camera/CameraCapture'
import ImagePreview from '@/components/features/camera/ImagePreview'
import { VoiceCaptureButton } from '@/components/features/voice/VoiceCaptureButton'

export default function SnapPage() {
  const [step, setStep] = useState<'capture' | 'preview' | 'record'>('capture');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const handleCapture = (imageSrc: string) => {
    setCapturedImage(imageSrc);
    setStep('preview');
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setStep('capture');
  };

  const handleConfirm = () => {
    setStep('record');
  };

  const handleRecordingComplete = (blob: Blob) => {
    setAudioBlob(blob);
    console.log("Recording complete", blob);
    // TODO: Proceed to upload (Story 2.3)
  };

  return (
    <div className="h-[100dvh] w-full bg-black flex flex-col">
      {step === 'capture' && (
        <CameraCapture onCapture={handleCapture} />
      )}
      
      {step === 'preview' && capturedImage && (
        <ImagePreview 
          imageSrc={capturedImage} 
          onRetake={handleRetake} 
          onConfirm={handleConfirm} 
        />
      )}

      {step === 'record' && (
        <div className="flex-1 flex flex-col items-center justify-center p-4 space-y-8 animate-in fade-in duration-300">
          <div className="relative w-full max-w-md aspect-square rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10">
            {capturedImage && (
              // eslint-disable-next-line @next/next/no-img-element
              <img 
                src={capturedImage} 
                alt="Captured meal" 
                className="w-full h-full object-cover"
              />
            )}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent pointer-events-none" />
            <div className="absolute bottom-4 left-0 right-0 text-center">
               <p className="text-white/90 font-medium">What's in this meal?</p>
            </div>
          </div>

          <div className="flex flex-col items-center gap-4">
             <VoiceCaptureButton onRecordingComplete={handleRecordingComplete} />
             <p className="text-zinc-400 text-sm">Hold to record</p>
          </div>
        </div>
      )}
    </div>
  )
}
