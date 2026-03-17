"use client";
import React from "react";
import { Camera, AlertCircle, RefreshCcw, ArrowLeft, Mic } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { cn } from "@/lib/utils";

interface PermissionErrorStateProps {
  errorType: "permission" | "device" | "unknown";
  errorMessage?: string;
  onRetry: () => void;
  mediaType?: "camera" | "microphone";
  className?: string; // Allow overriding container styles
}

export default function PermissionErrorState({
  errorType,
  errorMessage,
  onRetry,
  mediaType = "camera",
  className,
}: PermissionErrorStateProps) {
  const router = useRouter();
  const t = useTranslations();
  const tc = useTranslations("snap.camera");

  const handleCancel = () => {
    router.push("/");
  };

  const isPermissionError = errorType === "permission";
  const mediaLabel = mediaType === "camera" ? "Camera" : "Microphone";

  return (
    <div
      className={cn(
        "h-full w-full bg-zinc-900 flex flex-col items-center justify-center p-6 text-center space-y-5 animate-in fade-in duration-300",
        className,
      )}
    >
      <div className="h-16 w-16 shrink-0 rounded-full bg-red-500/10 flex items-center justify-center mb-2 ring-1 ring-red-500/20">
        {isPermissionError ? (
          mediaType === "camera" ? (
            <Camera className="h-8 w-8 text-red-500" />
          ) : (
            <Mic className="h-8 w-8 text-red-500" />
          )
        ) : (
          <AlertCircle className="h-8 w-8 text-red-500" />
        )}
      </div>

      <div className="space-y-2 max-w-sm">
        <h3 className="text-xl font-bold text-white">
          {isPermissionError
            ? tc("accessBlocked", { media: mediaLabel })
            : tc("mediaError", { media: mediaLabel })}
        </h3>
        <p className="text-zinc-400 text-base leading-relaxed">
          {isPermissionError
            ? tc("needAccess", {
                media: mediaType,
                purpose:
                  mediaType === "camera"
                    ? tc("purposeCamera")
                    : tc("purposeMicrophone"),
              })
            : errorMessage || tc("deviceError", { media: mediaType })}
        </p>
      </div>

      {isPermissionError && (
        <div className="bg-zinc-800/50 rounded-xl p-4 text-left w-full max-w-sm border border-zinc-800">
          <p className="text-zinc-300 text-sm font-medium mb-2">
            {tc("howToFix")}
          </p>
          <ul className="text-zinc-400 text-sm space-y-2 list-disc pl-4">
            <li>{tc("checkBrowser", { media: mediaType })}</li>
            <li dangerouslySetInnerHTML={{ __html: tc("tapSettings") }} />
            <li>{tc("tapRetry")}</li>
          </ul>
        </div>
      )}

      <div className="flex flex-col w-full max-w-xs gap-3 pt-4">
        <button
          onClick={onRetry}
          className="w-full h-14 bg-primary text-primary-foreground rounded-xl font-bold text-lg hover:opacity-90 transition-all flex items-center justify-center gap-2"
        >
          <RefreshCcw className="w-5 h-5" />
          {isPermissionError ? tc("reloadRetry") : t("snap.retry")}
        </button>

        <button
          onClick={handleCancel}
          className="w-full h-14 bg-zinc-800 text-white rounded-xl font-medium text-lg hover:bg-zinc-700 transition-colors flex items-center justify-center gap-2"
        >
          <ArrowLeft className="w-5 h-5" />
          {t("common.goBack")}
        </button>
      </div>
    </div>
  );
}
