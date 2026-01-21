'use client';

import { useLogs } from '@/hooks/use-logs';
import { DailySummary } from '@/components/features/logs/DailySummary';
import { FoodEntryCard } from '@/components/features/logs/FoodEntryCard';
import { FoodEntryCardSkeleton } from '@/components/features/logs/FoodEntryCardSkeleton';
import { EmptyLogState } from '@/components/features/logs/EmptyLogState';

import { LogListError } from '@/components/features/logs/LogListError';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Plus } from 'lucide-react';

/**
 * Dashboard page showing today's meal logs.
 * Handles loading, empty, error, and success states.
 */
export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useLogs();

  return (
    <div className="flex flex-col min-h-[100dvh] p-4 pb-24">
      {/* Daily Summary - show skeleton or real data */}
      {isLoading ? (
        <div className="mb-6">
          <div className="h-8 w-48 bg-muted animate-pulse rounded mb-2" />
          <div className="h-6 w-32 bg-muted animate-pulse rounded" />
        </div>
      ) : data?.data ? (
        <DailySummary logs={data.data} />
      ) : null}

      {/* Log List */}
      <div className="flex flex-col gap-3">
        {/* Loading State */}
        {isLoading && (
          <>
            <FoodEntryCardSkeleton />
            <FoodEntryCardSkeleton />
            <FoodEntryCardSkeleton />
          </>
        )}

        {/* Error State */}
        {isError && <LogListError onRetry={refetch} />}

        {/* Empty State */}
        {!isLoading && !isError && data?.data.length === 0 && (
          <EmptyLogState />
        )}

        {/* Success State - Log Cards */}
        {!isLoading && !isError && data?.data && data.data.length > 0 && (
          data.data.map((log) => (
            <FoodEntryCard key={log.id} log={log} />
          ))
        )}


        {/* Log Another Meal Button - Only show when we have logs */}
        {!isLoading && !isError && data?.data && data.data.length > 0 && (
          <Button asChild size="lg" className="w-full mt-4 text-lg py-6 sticky bottom-4 shadow-lg">
            <Link href="/snap">
              <Plus className="mr-2 h-5 w-5" />
              Log Another Meal
            </Link>
          </Button>
        )}
      </div>
    </div>
  );
}
