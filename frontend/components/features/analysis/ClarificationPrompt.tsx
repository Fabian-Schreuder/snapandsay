"use client";

import React, { useState, useCallback, useEffect } from 'react'
import { VoiceCaptureButton } from '@/components/features/voice/VoiceCaptureButton'

interface ClarificationPromptProps {
  question: string
  options: string[]
  timeoutSeconds?: number
  onSubmit: (response: string, isVoice: boolean) => void
  onSkip: () => void
}

/**
 * ClarificationPrompt displays a clarification question from the AI agent
 * with large tap targets for quick selection and optional voice input.
 * 
 * Senior-friendly design:
 * - Large, readable text (20px+)
 * - Large tap targets for options
 * - Voice response option with hold-to-record
 * - Text input fallback
 * - 30-second timeout with friendly skip message
 */
export function ClarificationPrompt({
  question,
  options,
  timeoutSeconds = 30,
  onSubmit,
  onSkip,
}: ClarificationPromptProps) {
  const [textInput, setTextInput] = useState('')
  const [remainingSeconds, setRemainingSeconds] = useState(timeoutSeconds)
  const [showTextInput, setShowTextInput] = useState(false)

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [])

  const handleOptionClick = useCallback((option: string) => {
    onSubmit(option, false)
  }, [onSubmit])

  const handleTextSubmit = useCallback(() => {
    if (textInput.trim()) {
      onSubmit(textInput.trim(), false)
    }
  }, [textInput, onSubmit])

  const handleVoiceComplete = useCallback(async (blob: Blob) => {
    // Convert blob to text for voice input
    // The backend will handle transcription if needed
    // For now, we'll submit a placeholder
    onSubmit('[Voice Response]', true)
  }, [onSubmit])

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 animate-in fade-in duration-300">
      {/* Question */}
      <div className="max-w-md w-full text-center space-y-6">
        <div className="space-y-2">
          <p className="text-white/60 text-sm">Quick question...</p>
          <h2 className="text-white text-2xl font-semibold leading-relaxed">
            {question}
          </h2>
        </div>

        {/* Options as large tap targets */}
        {options.length > 0 && (
          <div className="flex flex-wrap justify-center gap-3 mt-6">
            {options.map((option, index) => (
              <button
                key={index}
                onClick={() => handleOptionClick(option)}
                className="px-6 py-4 min-w-[120px] bg-white/10 hover:bg-white/20 active:bg-white/30 
                           text-white text-lg font-medium rounded-2xl border border-white/20
                           transition-all duration-150 active:scale-95 touch-manipulation"
              >
                {option}
              </button>
            ))}
          </div>
        )}

        {/* Divider */}
        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 h-px bg-white/20" />
          <span className="text-white/40 text-sm">or</span>
          <div className="flex-1 h-px bg-white/20" />
        </div>

        {/* Voice or Text input */}
        {!showTextInput ? (
          <div className="space-y-3">
            <div className="flex justify-center">
              <VoiceCaptureButton onRecordingComplete={handleVoiceComplete} />
            </div>
            <p className="text-white/50 text-sm">Hold to speak</p>
            <button
              onClick={() => setShowTextInput(true)}
              className="text-white/40 hover:text-white/60 text-sm underline"
            >
              Type instead
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your answer..."
                className="flex-1 h-[60px] px-4 bg-white/10 border border-white/20 rounded-xl
                           text-white text-lg placeholder:text-white/30
                           focus:outline-none focus:border-white/40"
                onKeyDown={(e) => e.key === 'Enter' && handleTextSubmit()}
                autoFocus
              />
              <button
                onClick={handleTextSubmit}
                disabled={!textInput.trim()}
                className="px-6 h-[60px] bg-primary hover:bg-primary/90 disabled:bg-white/10
                           text-white font-medium rounded-xl transition-colors
                           disabled:text-white/30"
              >
                Send
              </button>
            </div>
            <button
              onClick={() => setShowTextInput(false)}
              className="text-white/40 hover:text-white/60 text-sm underline"
            >
              Use voice
            </button>
          </div>
        )}

        {/* Timeout indicator */}
        <div className="mt-8 space-y-2">
          <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-white/40 transition-all duration-1000 ease-linear"
              style={{ width: `${(remainingSeconds / timeoutSeconds) * 100}%` }}
            />
          </div>
          {remainingSeconds <= 10 && (
            <button
              onClick={onSkip}
              className="text-white/60 hover:text-white text-sm animate-pulse"
            >
              Taking too long? Tap to skip →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
