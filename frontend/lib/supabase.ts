import { createBrowserClient } from '@supabase/ssr';

if (!process.env.NEXT_PUBLIC_SUPABASE_URL) {
  throw new Error('Missing env.NEXT_PUBLIC_SUPABASE_URL');
}
if (!process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
  throw new Error('Missing env.NEXT_PUBLIC_SUPABASE_ANON_KEY');
}

export const supabase = createBrowserClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

export const signInAnonymously = async () => {
  const { data, error } = await supabase.auth.signInAnonymously();
  if (error) {
    console.error('Error signing in anonymously:', error);
    throw error;
  }
  return data;
};
