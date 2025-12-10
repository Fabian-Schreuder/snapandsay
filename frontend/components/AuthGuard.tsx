"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { signInAnonymously, supabase } from "@/lib/supabase";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const isSigningIn = useRef(false);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log("Auth state change:", event, session?.user?.id);

      if (event === 'SIGNED_IN' && session) {
        if (pathname === '/login') {
            router.replace('/');
        }
      } else if (event === 'SIGNED_OUT' || (!session && event === 'INITIAL_SESSION')) {
        if (!isSigningIn.current) {
            isSigningIn.current = true;
            try {
                await signInAnonymously();
            } catch (err) {
                console.error("Auto-login failed:", err);
            } finally {
                isSigningIn.current = false;
            }
        }
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [router, pathname]);

  return <>{children}</>;
}
