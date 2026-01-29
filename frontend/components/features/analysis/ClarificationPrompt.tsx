"use client";
import React, { useState, useCallback, useEffect } from "react";
import { VoiceCaptureButton } from "@/components/features/voice/VoiceCaptureButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Mic, Keyboard, ArrowRight } from "lucide-react";

interface ClarificationPromptProps {
  question: string;
  options: string[];
  timeoutSeconds?: number;
  onSubmit: (response: string, isVoice: boolean) => void;
  onSkip: () => void;
}

/**
 * ClarificationPrompt displays a clarification question from the AI agent
 * with large tap targets for quick selection and optional voice input.
 *
 * Senior-friendly design:
 * - Large, readable text (20px+)
 * - Large tap targets (Senior variant)
 * - Voice response option with hold-to-record
 */
export function ClarificationPrompt({
  question,
  options,
  timeoutSeconds = 30,
  onSubmit,
  onSkip,
}: ClarificationPromptProps) {
  const [textInput, setTextInput] = useState("");
  const [remainingSeconds, setRemainingSeconds] = useState(timeoutSeconds);
  const [showTextInput, setShowTextInput] = useState(false);

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleOptionClick = useCallback(
    (option: string) => {
      onSubmit(option, false);
    },
    [onSubmit],
  );

  const handleTextSubmit = useCallback(() => {
    if (textInput.trim()) {
      onSubmit(textInput.trim(), false);
    }
  }, [textInput, onSubmit]);

  const handleVoiceComplete = useCallback(async () => {
    // Placeholder for voice response handling
    onSubmit("[Voice Response]", true);
  }, [onSubmit]);

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-4 animate-in fade-in duration-300">
      <Card className="max-w-md w-full p-6 space-y-6 bg-zinc-900 border-zinc-800 shadow-2xl">
        <div className="space-y-4 text-center">
          <p className="text-zinc-400 text-sm font-medium uppercase tracking-wide">
            Quick question...
          </p>
          <h2 className="text-white text-2xl font-semibold leading-relaxed">
            {question}
          </h2>
        </div>

        {/* Options as large tap targets */}
        {options.length > 0 && (
          <div className="flex flex-wrap justify-center gap-3">
            {options.map((option, index) => (
              <Button
                key={index}
                variant="secondary"
                size="senior"
                onClick={() => handleOptionClick(option)}
                className="flex-1 min-w-[140px] whitespace-normal h-auto py-4 text-left justify-center text-lg hover:bg-zinc-700 hover:text-white transition-all bg-zinc-800 text-zinc-100 border-zinc-700"
              >
                {option}
              </Button>
            ))}
          </div>
        )}

        {/* Divider */}
        <div className="flex items-center gap-4">
          <div className="flex-1 h-px bg-zinc-800" />
          <span className="text-zinc-500 text-sm font-medium">or</span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div>

        {/* Voice or Text input */}
        {!showTextInput ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <VoiceCaptureButton onRecordingComplete={handleVoiceComplete} />
            </div>
            <p className="text-zinc-400 text-sm text-center">Hold to speak</p>
            <div className="text-center">
              <Button
                variant="link"
                onClick={() => setShowTextInput(true)}
                className="text-zinc-400 hover:text-white"
              >
                <Keyboard className="w-4 h-4 mr-2" />
                Type answer instead
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex gap-2">
              <Input
                type="text"
                size="senior"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your answer..."
                className="bg-zinc-800 border-zinc-700 text-white placeholder:text-zinc-500"
                onKeyDown={(e) => e.key === "Enter" && handleTextSubmit()}
                autoFocus
              />
            </div>
            <Button
              onClick={handleTextSubmit}
              disabled={!textInput.trim()}
              size="senior"
              className="w-full"
            >
              Send Answer
            </Button>
            <div className="text-center">
              <Button
                variant="link"
                onClick={() => setShowTextInput(false)}
                className="text-zinc-400 hover:text-white"
              >
                <Mic className="w-4 h-4 mr-2" />
                Use voice instead
              </Button>
            </div>
          </div>
        )}

        {/* Timeout indicator */}
        <div className="space-y-2 pt-4">
          <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500/50 transition-all duration-1000 ease-linear"
              style={{ width: `${(remainingSeconds / timeoutSeconds) * 100}%` }}
            />
          </div>
          {remainingSeconds <= 10 && (
            <div className="text-center">
              <Button
                variant="ghost"
                onClick={onSkip}
                className="text-zinc-400 hover:text-white hover:bg-zinc-800/50 h-auto py-2"
              >
                Taking too long? Tap to skip{" "}
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
