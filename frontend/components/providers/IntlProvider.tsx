"use client";

import { NextIntlClientProvider, AbstractIntlMessages } from "next-intl";
import { ReactNode, useEffect, useState } from "react";

// Import default messages statically for SSG/build compatibility
import defaultMessages from "../../messages/nl.json";

type Locale = "nl" | "en";

function getLocaleFromCookie(): Locale {
  if (typeof document === "undefined") return "nl";
  const match = document.cookie.match(/(?:^|; )locale=([^;]*)/);
  return (match?.[1] as Locale) || "nl";
}

export function IntlProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("nl");
  const [messages, setMessages] = useState<AbstractIntlMessages>(defaultMessages);

  useEffect(() => {
    const currentLocale = getLocaleFromCookie();
    setLocale(currentLocale);

    // Only load if different from default
    if (currentLocale !== "nl") {
      import(`../../messages/${currentLocale}.json`)
        .then((module) => setMessages(module.default))
        .catch(() => {
          // Keep default Dutch messages
        });
    }
  }, []);

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      {children}
    </NextIntlClientProvider>
  );
}
