"use client";

import { useTranslations } from "next-intl";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect } from "react";

type Locale = "nl" | "en";

function getLocaleFromCookie(): Locale {
  if (typeof document === "undefined") return "nl";
  const match = document.cookie.match(/(?:^|; )locale=([^;]*)/);
  return (match?.[1] as Locale) || "nl";
}

function setLocaleCookie(locale: Locale) {
  // Set cookie with 1 year expiry
  const expires = new Date();
  expires.setFullYear(expires.getFullYear() + 1);
  document.cookie = `locale=${locale};expires=${expires.toUTCString()};path=/`;
}

export function LanguageToggle() {
  const t = useTranslations("settings");
  const [locale, setLocale] = useState<Locale>("nl");

  useEffect(() => {
    setLocale(getLocaleFromCookie());
  }, []);

  const handleLanguageChange = (newLocale: Locale) => {
    setLocale(newLocale);
    setLocaleCookie(newLocale);
    // Reload to apply new locale
    window.location.reload();
  };

  return (
    <div className="space-y-2">
      <Label htmlFor="language-select">{t("language")}</Label>
      <p className="text-sm text-muted-foreground">{t("languageDescription")}</p>
      <Select value={locale} onValueChange={handleLanguageChange}>
        <SelectTrigger id="language-select" className="w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="nl">{t("dutch")}</SelectItem>
          <SelectItem value="en">{t("english")}</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
