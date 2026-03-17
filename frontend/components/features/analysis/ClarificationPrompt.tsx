"use client";
import React, { useState, useCallback, useEffect } from "react";
import { useTranslations } from "next-intl";
import { VoiceCaptureButton } from "@/components/features/voice/VoiceCaptureButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Mic, Keyboard, ArrowRight, Loader2 } from "lucide-react";
import { uploadFile, generateUploadPath } from "@/services/upload-service";
import { supabase } from "@/lib/supabase";

export interface ClarificationQuestion {
  item_name: string;
  question: string;
  options: string[];
}

export interface ClarificationAnswer {
  item_name: string;
  response: string;
  is_voice?: boolean;
  audio_path?: string;
}

interface ClarificationPromptProps {
  questions: ClarificationQuestion[];
  timeoutSeconds?: number;
  onSubmitAll: (answers: ClarificationAnswer[]) => void;
  onSkip: () => void;
}

/**
 * ClarificationPrompt displays clarification questions one at a time
 * as sequential pages. Collects all answers then submits as a batch.
 *
 * Senior-friendly design:
 * - Large, readable text (20px+)
 * - Large tap targets
 * - Voice response option with hold-to-record
 * - Progress indicator (1/2, 2/2)
 */
export function ClarificationPrompt({
  questions,
  timeoutSeconds = 30,
  onSubmitAll,
  onSkip,
}: ClarificationPromptProps) {
  const t = useTranslations();
  const tc = useTranslations("snap.clarification");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<ClarificationAnswer[]>([]);
  const [textInput, setTextInput] = useState("");
  const [remainingSeconds, setRemainingSeconds] = useState(timeoutSeconds);
  const [showTextInput, setShowTextInput] = useState(false);
  const [isUploadingVoice, setIsUploadingVoice] = useState(false);

  const currentQuestion = questions[currentIndex];
  const totalQuestions = questions.length;
  const isLastQuestion = currentIndex === totalQuestions - 1;

  // Reset text state when moving to next question
  useEffect(() => {
    setTextInput("");
    setShowTextInput(false);
  }, [currentIndex]);

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

  const advanceOrSubmit = useCallback(
    (answer: ClarificationAnswer) => {
      const updatedAnswers = [...answers, answer];
      if (isLastQuestion) {
        onSubmitAll(updatedAnswers);
      } else {
        setAnswers(updatedAnswers);
        setCurrentIndex((prev) => prev + 1);
      }
    },
    [answers, isLastQuestion, onSubmitAll],
  );

  const handleOptionClick = useCallback(
    (option: string) => {
      advanceOrSubmit({
        item_name: currentQuestion.item_name,
        response: option,
      });
    },
    [advanceOrSubmit, currentQuestion],
  );

  const handleTextSubmit = useCallback(() => {
    if (textInput.trim()) {
      advanceOrSubmit({
        item_name: currentQuestion.item_name,
        response: textInput.trim(),
      });
    }
  }, [textInput, advanceOrSubmit, currentQuestion]);

  const handleVoiceComplete = useCallback(
    async (audioBlob: Blob) => {
      setIsUploadingVoice(true);
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();
        if (!user) throw new Error("No authenticated user");

        const audioPath = generateUploadPath(user.id, "audio");
        await uploadFile("raw_uploads", audioPath, audioBlob);

        advanceOrSubmit({
          item_name: currentQuestion.item_name,
          response: audioPath,
          is_voice: true,
          audio_path: audioPath,
        });
      } catch (err) {
        console.error("Failed to upload voice clarification:", err);
        advanceOrSubmit({
          item_name: currentQuestion.item_name,
          response: "[Voice Response]",
          is_voice: true,
        });
      } finally {
        setIsUploadingVoice(false);
      }
    },
    [advanceOrSubmit, currentQuestion],
  );

  if (!currentQuestion) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex flex-col items-center justify-center p-4 animate-in fade-in duration-300">
      <Card className="max-w-md w-full p-6 space-y-6 bg-zinc-900 border-zinc-800 shadow-2xl">
        {/* Progress indicator */}
        {totalQuestions > 1 && (
          <div className="flex items-center justify-between">
            <div className="flex gap-1.5">
              {questions.map((_, i) => (
                <div
                  key={i}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    i < currentIndex
                      ? "w-6 bg-indigo-500"
                      : i === currentIndex
                        ? "w-6 bg-indigo-400"
                        : "w-3 bg-zinc-700"
                  }`}
                />
              ))}
            </div>
            <span className="text-zinc-500 text-xs font-medium">
              {currentIndex + 1}/{totalQuestions}
            </span>
          </div>
        )}

        <div className="space-y-4 text-center">
          <p className="text-zinc-400 text-sm font-medium uppercase tracking-wide">
            {tc("quickQuestion")}
          </p>
          <h2 className="text-white text-2xl font-semibold leading-relaxed">
            {currentQuestion.question}
          </h2>
        </div>

        {/* Options as large tap targets */}
        {currentQuestion.options.length > 0 && (
          <div className="flex flex-wrap justify-center gap-3">
            {currentQuestion.options.map((option, index) => (
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
          <span className="text-zinc-500 text-sm font-medium">
            {t("common.or")}
          </span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div>

        {/* Voice or Text input */}
        {!showTextInput ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              {isUploadingVoice ? (
                <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
              ) : (
                <VoiceCaptureButton onRecordingComplete={handleVoiceComplete} />
              )}
            </div>
            <p className="text-zinc-400 text-sm text-center">
              {tc("holdToSpeak")}
            </p>
            <div className="text-center">
              <Button
                variant="link"
                onClick={() => setShowTextInput(true)}
                className="text-zinc-400 hover:text-white"
              >
                <Keyboard className="w-4 h-4 mr-2" />
                {tc("typeAnswer")}
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
                placeholder={tc("typePlaceholder")}
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
              {isLastQuestion ? tc("sendAnswer") : `${t("common.next")} →`}
            </Button>
            <div className="text-center">
              <Button
                variant="link"
                onClick={() => setShowTextInput(false)}
                className="text-zinc-400 hover:text-white"
              >
                <Mic className="w-4 h-4 mr-2" />
                {tc("useVoice")}
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
                {tc("skipPrompt")} <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
