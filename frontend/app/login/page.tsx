"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if already authenticated, redirect to app
    const checkUser = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        router.replace("/app");
      }
    };
    checkUser();
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4">
      <div className="w-full max-w-md space-y-8 text-center">
        <h1 className="text-2xl font-bold">Welcome to SnapAndSay</h1>
        <p className="text-gray-600">Signing you in anonymously...</p>
        {error && <p className="text-red-500">{error}</p>}
        {/* AuthGuard in layout will handle the actual auto-sign-in logic */}
        <div className="mt-4 flex justify-center">
             <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
        </div>
      </div>
    </div>
  );
}
