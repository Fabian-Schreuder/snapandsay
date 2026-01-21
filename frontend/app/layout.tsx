import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";
import AuthGuard from "@/components/AuthGuard";
import { QueryProvider } from "@/components/providers/QueryProvider";
import { IntlProvider } from "@/components/providers/IntlProvider";
import { cookies } from "next/headers";
import { Toaster } from "@/components/ui/sonner";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Snap and Say",
  description: "Conversational dietary assessment tool",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const cookieStore = await cookies();
  const locale = cookieStore.get("locale")?.value || "nl";
  return (
    <html lang={locale}>
      <body className={`${geistSans.variable} ${geistMono.variable}`}>
        <QueryProvider>
          <IntlProvider>
            <AuthGuard>{children}</AuthGuard>
            <Toaster position="top-center" duration={6000} richColors closeButton />
          </IntlProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
