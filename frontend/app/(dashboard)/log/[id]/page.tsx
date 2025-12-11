'use client';

import { useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Image from 'next/image';
import { ArrowLeft, Pencil, Trash2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useLog, useDeleteLog } from '@/hooks/use-logs';
import { EditLogSheet } from '@/components/features/logs/EditLogSheet';
import { DeleteLogDialog } from '@/components/features/logs/DeleteLogDialog';

/**
 * Get public URL for an image stored in Supabase Storage.
 */
function getImageUrl(path: string): string {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  return `${supabaseUrl}/storage/v1/object/public/raw_uploads/${path}`;
}

/**
 * Format timestamp to human-readable date and time.
 */
function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString([], {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * Log Detail Page - displays full meal entry with edit/delete options.
 */
export default function LogDetailPage() {
  const router = useRouter();
  const params = useParams();
  const logId = params.id as string;
  
  const { data: log, isLoading, error } = useLog(logId);
  const deleteLog = useDeleteLog();
  
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  const handleDelete = () => {
    deleteLog.mutate(logId, {
      onSuccess: () => {
        router.push('/');
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !log) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 p-4">
        <p className="text-lg text-destructive">Failed to load meal</p>
        <Button onClick={() => router.back()} variant="outline" className="h-14">
          Go Back
        </Button>
      </div>
    );
  }

  const displayText = log.description || log.transcript || 'Meal logged';
  const imageUrl = log.image_url || getImageUrl(log.image_path);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.back()}
          className="h-12 w-12"
          aria-label="Go back"
        >
          <ArrowLeft className="h-6 w-6" />
        </Button>
        <h1 className="text-xl font-semibold">Meal Details</h1>
      </header>

      {/* Content */}
      <main className="flex-1 p-4 pb-24">
        {/* Full-size Image */}
        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-muted">
          <Image
            src={imageUrl}
            alt={displayText}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 768px"
            priority
          />
        </div>

        {/* Meal Info */}
        <div className="mt-6 space-y-4">
          <div>
            <h2 className="text-2xl font-semibold leading-snug">{log.title || displayText}</h2>
             {/* Show Description if we have a specific title to disambiguate */}
            {log.title && (log.description || log.transcript) && (
              <p className="mt-2 text-base text-muted-foreground">{log.description || log.transcript}</p>
            )}
            <p className="mt-1 text-lg text-muted-foreground">
              {formatDateTime(log.created_at)}
            </p>
          </div>

          {/* Nutritional Breakdown */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <NutritionCard label="Calories" value={log.calories} unit="cal" primary />
            <NutritionCard label="Protein" value={log.protein} unit="g" />
            <NutritionCard label="Carbs" value={log.carbs} unit="g" />
            <NutritionCard label="Fats" value={log.fats} unit="g" />
          </div>
        </div>
      </main>

      {/* Fixed Bottom Actions */}
      <div className="fixed bottom-0 left-0 right-0 flex h-20 items-center gap-4 border-t bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <Button
          onClick={() => setIsEditOpen(true)}
          className="h-14 flex-1 gap-2 text-lg"
          variant="outline"
        >
          <Pencil className="h-5 w-5" />
          Edit
        </Button>
        <Button
          onClick={() => setIsDeleteOpen(true)}
          className="h-14 flex-1 gap-2 text-lg"
          variant="destructive"
        >
          <Trash2 className="h-5 w-5" />
          Delete
        </Button>
      </div>

      {/* Edit Sheet */}
      <EditLogSheet
        log={log}
        open={isEditOpen}
        onOpenChange={setIsEditOpen}
      />

      {/* Delete Dialog */}
      <DeleteLogDialog
        open={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        onConfirm={handleDelete}
        isDeleting={deleteLog.isPending}
      />
    </div>
  );
}

/**
 * Nutrition info card component.
 */
function NutritionCard({
  label,
  value,
  unit,
  primary = false,
}: {
  label: string;
  value: number | null;
  unit: string;
  primary?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-4 ${
        primary
          ? 'bg-primary text-primary-foreground'
          : 'bg-muted text-foreground'
      }`}
    >
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="text-2xl font-bold">
        {value != null ? value : '—'}
        <span className="text-lg font-normal opacity-70"> {unit}</span>
      </p>
    </div>
  );
}
