'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { logsApi } from '@/lib/api';
import type { DietaryLogListResponse, DietaryLog, LogUpdateRequest } from '@/types/log';

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

/**
 * Hook to fetch a single dietary log by ID.
 * 
 * @param logId - UUID of the log to fetch.
 * @returns Query result with log data, loading state, and error handling.
 */
export function useLog(logId: string) {
  return useQuery<DietaryLog, Error>({
    queryKey: ['log', logId],
    queryFn: () => logsApi.getById(logId),
    enabled: !!logId,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook for updating a dietary log with optimistic updates.
 * 
 * @returns Mutation object with mutate function and state.
 */
export function useUpdateLog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ logId, data }: { logId: string; data: LogUpdateRequest }) =>
      logsApi.update(logId, data),
    onMutate: async ({ logId, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['log', logId] });
      
      // Snapshot the previous value
      const previous = queryClient.getQueryData<DietaryLog>(['log', logId]);
      
      // Optimistically update to the new value
      if (previous) {
        queryClient.setQueryData<DietaryLog>(['log', logId], {
          ...previous,
          ...data,
        });
      }
      
      return { previous };
    },
    onError: (_err, variables, context) => {
      // Rollback on error
      if (context?.previous) {
        queryClient.setQueryData(['log', variables.logId], context.previous);
      }
      toast.error('Failed to update meal');
    },
    onSuccess: () => {
      toast.success('Meal updated');
    },
    onSettled: (_data, _error, { logId }) => {
      // Always refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['log', logId] });
      queryClient.invalidateQueries({ queryKey: ['logs'] });
    },
  });
}

/**
 * Hook for deleting a dietary log.
 * 
 * @returns Mutation object with mutate function and state.
 */
export function useDeleteLog() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (logId: string) => logsApi.delete(logId),
    onSuccess: () => {
      toast.success('Meal deleted');
      queryClient.invalidateQueries({ queryKey: ['logs'] });
    },
    onError: () => {
      toast.error('Failed to delete meal');
    },
  });
}
