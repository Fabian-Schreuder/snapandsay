'use client';

import type { DietaryLog } from '@/types/log';

interface DailySummaryProps {
  logs: DietaryLog[];
}

/**
 * Format current date for display (e.g., "Sunday, December 8").
 */
function formatDate(): string {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Daily summary header showing today's date and total calories.
 */
export function DailySummary({ logs }: DailySummaryProps) {
  const totalCalories = logs.reduce((sum, log) => sum + (log.calories || 0), 0);

  return (
    <div className="mb-6">
      <h1 className="text-2xl font-bold">{formatDate()}</h1>
      <p className="text-lg text-muted-foreground">
        {logs.length > 0 ? (
          <>Total: <span className="font-medium text-foreground">{totalCalories} calories</span></>
        ) : (
          'Start tracking your meals'
        )}
      </p>
    </div>
  );
}
