"use client"
import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQueryClient } from '@tanstack/react-query'
import CameraCapture from '@/components/features/camera/CameraCapture'
import ImagePreview from '@/components/features/camera/ImagePreview'
import ThinkingIndicator from '@/components/features/analysis/ThinkingIndicator'
import { ClarificationPrompt } from '@/components/features/analysis/ClarificationPrompt'
import { VoiceCaptureButton } from '@/components/features/voice/VoiceCaptureButton'
import { uploadFile, generateUploadPath, deleteFile } from '@/services/upload-service'
import { analysisApi } from '@/lib/api'
import { supabase } from '@/lib/supabase'
import { useAgent } from '@/hooks/use-agent'

export default function SnapPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [step, setStep] = useState<'capture' | 'preview' | 'record' | 'streaming' | 'clarifying'>('capture');
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const { 
    status, 
    thoughts, 

    error: agentError,
    clarification,
    startStreaming, 
    reset, 
    submitClarificationResponse,
    skipClarification
  } = useAgent();

  // Completion Handling
  React.useEffect(() => {
    if (status === 'complete') {
        const handleCompletion = async () => {
             // Refresh logs to get the final analyzed result
             await queryClient.invalidateQueries({ queryKey: ['logs'] });
             // Wait for animation
             setTimeout(() => {
                 router.push('/');
             }, 1500);
        };
        handleCompletion();
    }
  }, [status, router, queryClient]);

  // Error Handling
  React.useEffect(() => {
    if (agentError) {
        setErrorMessage(agentError);
    }
  }, [agentError]);

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

  const handleRecordingComplete = async (blob: Blob) => {
    await handleUpload(blob);
  };

  const handleUpload = async (currentAudioBlob: Blob) => {
    if (!capturedImage) return;

    setIsUploading(true);
    setErrorMessage(null);

    // Define paths outside try block for access in cleanup
    let imagePath: string | undefined;
    let audioPath: string | undefined;

    try {
      // 1. Get User
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("No authenticated user found");

      // 2. Prepare Files
      const imageBlob = await (await fetch(capturedImage)).blob();
      
      imagePath = generateUploadPath(user.id, 'image');
      audioPath = generateUploadPath(user.id, 'audio');

      // 3. Parallel Uploads
      await Promise.all([
        uploadFile('raw_uploads', imagePath, imageBlob),
        uploadFile('raw_uploads', audioPath, currentAudioBlob)
      ]);

      // 4. API Call
      const response = await analysisApi.upload({
        image_path: imagePath,
        audio_path: audioPath,
        client_timestamp: new Date().toISOString()
      });
      const newLogId = response.log_id;


      // 5. Success - invalidate logs query so dashboard refreshes
      await queryClient.invalidateQueries({ queryKey: ['logs'] });
      
      // Transition to Streaming
      setStep('streaming');
      // Force non-null assertion since we just created them
      startStreaming(newLogId, imagePath!, audioPath!); 

    } catch (error) {
      console.error("Upload sequence failed:", error);
      // Only set error message if agent didn't already capture it
      if (!agentError) {
          setErrorMessage("We couldn't save that. Please try again.");
      }
      
      // Cleanup: Delete any files that might have been uploaded
      const cleanupPromises: Promise<void>[] = [];
      if (imagePath) cleanupPromises.push(deleteFile('raw_uploads', imagePath));
      if (audioPath) cleanupPromises.push(deleteFile('raw_uploads', audioPath));
      
      if (cleanupPromises.length > 0) {
          Promise.allSettled(cleanupPromises).then(() => console.log("Cleanup attempted"));
      }

    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="h-[100dvh] w-full bg-black flex flex-col relative">
      {/* Error Overlay */}
      {errorMessage && (
        <div className="absolute top-8 left-4 right-4 z-50 bg-red-500/90 text-white p-4 rounded-xl text-center shadow-lg backdrop-blur animate-in slide-in-from-top">
          <p className="font-medium">{errorMessage}</p>
          <button 
            onClick={() => {
              setErrorMessage(null);
              reset();
              setStep('capture');
            }}
            className="mt-2 text-sm bg-white/20 px-4 py-1 rounded-full hover:bg-white/30"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading/Thinking State */}
      {/* Uploading State */}
      {isUploading && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center space-y-4 animate-in fade-in duration-300">
          <div className="relative w-20 h-20">
            <div className="absolute inset-0 border-t-4 border-primary rounded-full animate-spin"></div>
            <div className="absolute inset-2 border-b-4 border-white/50 rounded-full animate-spin direction-reverse"></div>
          </div>
          <p className="text-white text-xl font-medium animate-pulse">Uploading...</p>
        </div>
      )}

      {/* Streaming/Thinking State */}
      {step === 'streaming' && !clarification && (
        <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300">
           <ThinkingIndicator 
              status={status === 'clarifying' ? 'streaming' : status as "idle" | "connecting" | "streaming" | "complete" | "error"}  
              thoughts={thoughts} 
           />
        </div>
      )}

      {/* Clarification Prompt */}
      {clarification && (
        <ClarificationPrompt 
          question={clarification.question}
          options={clarification.options}
          onSubmit={submitClarificationResponse}
          onSkip={skipClarification}
        />
      )}

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
               <p className="text-white/90 font-medium">What&apos;s in this meal?</p>
            </div>
          </div>

          <div className="flex flex-col items-center gap-4">
             {/* Disable button while uploading */}
             {!isUploading && (
                 <VoiceCaptureButton onRecordingComplete={handleRecordingComplete} />
             )}
             <p className="text-zinc-400 text-sm">Hold to record</p>
          </div>
        </div>
      )}
    </div>
  )
}
