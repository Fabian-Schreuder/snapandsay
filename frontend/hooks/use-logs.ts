'use client';

import { useQuery } from '@tanstack/react-query';
import { logsApi } from '@/lib/api';
import type { DietaryLogListResponse } from '@/types/log';

/**
 * Hook to fetch dietary logs for a specific date.
 * Uses React Query for caching and automatic refetching.
 * 
 * @param date - Optional ISO date string (YYYY-MM-DD). Defaults to today.
 * @returns Query result with logs data, loading state, and error handling.
 */
export function useLogs(date?: string) {
  return useQuery<DietaryLogListResponse, Error>({
    queryKey: ['logs', date ?? 'today'],
    queryFn: () => logsApi.getByDate(date),
    staleTime: 30000, // 30 seconds
  });
}
