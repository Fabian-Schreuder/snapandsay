import { cn } from "@/lib/utils";

/**
 * Skeleton loading placeholder component.
 * Uses pulse animation to indicate loading state.
 */
function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}

export { Skeleton };
