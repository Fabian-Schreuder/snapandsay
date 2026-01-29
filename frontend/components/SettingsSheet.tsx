"use client";

import { Settings } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { LanguageToggle } from "./LanguageToggle";
import { FeedbackSettingsToggle } from "./FeedbackSettingsToggle";

export function SettingsSheet() {
  const t = useTranslations("settings");

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={t("title")}>
          <Settings className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("title")}</SheetTitle>
          <SheetDescription>{t("description")}</SheetDescription>
        </SheetHeader>
        <div className="grid gap-6 py-6">
          <div className="space-y-4">
            <LanguageToggle />
          </div>
          <div className="space-y-4">
            <FeedbackSettingsToggle />
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
