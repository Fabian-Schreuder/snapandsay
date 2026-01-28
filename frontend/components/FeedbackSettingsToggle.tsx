"use client";

import { useTranslations } from "next-intl";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useFeedback } from "@/hooks/use-feedback";
import { Volume2, Vibrate } from "lucide-react";

/**
 * Settings component for toggling sound and vibration feedback.
 * Persists preferences to localStorage.
 */
export function FeedbackSettingsToggle() {
  const t = useTranslations("settings");
  const { preferences, setSoundEnabled, setVibrationEnabled } = useFeedback();

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium">{t("feedback")}</h3>
        <p className="text-sm text-muted-foreground">
          {t("feedbackDescription")}
        </p>
      </div>

      <div className="space-y-3">
        {/* Sound Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Volume2 className="h-4 w-4 text-muted-foreground" />
            <Label htmlFor="sound-toggle" className="text-sm">
              {t("soundEnabled")}
            </Label>
          </div>
          <Switch
            id="sound-toggle"
            checked={preferences.soundEnabled}
            onCheckedChange={setSoundEnabled}
          />
        </div>

        {/* Vibration Toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Vibrate className="h-4 w-4 text-muted-foreground" />
            <Label htmlFor="vibration-toggle" className="text-sm">
              {t("vibrationEnabled")}
            </Label>
          </div>
          <Switch
            id="vibration-toggle"
            checked={preferences.vibrationEnabled}
            onCheckedChange={setVibrationEnabled}
          />
        </div>
      </div>
    </div>
  );
}
