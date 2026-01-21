import { getRequestConfig } from "next-intl/server";
import { cookies } from "next/headers";

// Default locale - Dutch for senior users
export const defaultLocale = "nl";
export const locales = ["nl", "en"] as const;
export type Locale = (typeof locales)[number];

export default getRequestConfig(async () => {
  // Get locale from cookie, default to Dutch
  const cookieStore = await cookies();
  const locale = (cookieStore.get("locale")?.value as Locale) || defaultLocale;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
