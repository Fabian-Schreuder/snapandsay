"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { signInAnonymously, supabase } from "@/lib/supabase";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      console.log("Auth state change:", event, session?.user?.id);

      if (event === 'SIGNED_IN' && session) {
        // If we are on login page, redirect to app
        if (pathname === '/login') {
            router.replace('/app');
        }
      } else if (event === 'SIGNED_OUT' || (!session && event === 'INITIAL_SESSION')) {
        // If no session, try to sign in anonymously
        console.log("No session, attempting anonymous sign in...");
        signInAnonymously().catch((err) => {
            console.error("Auto-login failed:", err);
        });
      }
    });

    // Initial check just in case onAuthStateChange doesn't fire immediately for existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
        if (!session) {
            signInAnonymously().catch(console.error);
        } else if (pathname === '/login') {
            router.replace('/app');
        }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router, pathname]);

  return <>{children}</>;
}
