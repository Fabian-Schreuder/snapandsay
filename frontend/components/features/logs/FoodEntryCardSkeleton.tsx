import { Skeleton } from '@/components/ui/skeleton';

/**
 * Skeleton loading state for FoodEntryCard.
 * Matches the layout of the actual card for smooth transition.
 */
export function FoodEntryCardSkeleton() {
  return (
    <div className="flex w-full items-center gap-4 p-4 min-h-[100px] rounded-xl bg-card shadow-sm">
      {/* Thumbnail skeleton */}
      <Skeleton className="h-20 w-20 flex-shrink-0 rounded-lg" />

      {/* Content skeleton */}
      <div className="flex flex-1 flex-col gap-2">
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-1/4" />
      </div>

      {/* Badge skeleton */}
      <Skeleton className="h-8 w-16 rounded-full flex-shrink-0" />
    </div>
  );
}
