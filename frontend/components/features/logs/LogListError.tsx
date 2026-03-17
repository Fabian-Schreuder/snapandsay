"use client";

import { AlertCircle } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";

interface LogListErrorProps {
  onRetry: () => void;
}

/**
 * Error state shown when fetching logs fails.
 * Displays a user-friendly error message with a retry button.
 */
export function LogListError({ onRetry }: LogListErrorProps) {
  const t = useTranslations();

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="mb-4 rounded-full bg-destructive/10 p-4">
        <AlertCircle className="h-8 w-8 text-destructive" />
      </div>
      <h3 className="mb-2 text-xl font-semibold">{t("snap.logError.title")}</h3>
      <p className="mb-6 text-muted-foreground text-lg">
        {t("errors.generic")}
      </p>
      <Button onClick={onRetry} variant="outline" size="lg" className="text-lg">
        {t("common.retry")}
      </Button>
    </div>
  );
}
