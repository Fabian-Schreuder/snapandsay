'use client';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Loader2 } from 'lucide-react';

interface DeleteLogDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isDeleting: boolean;
}

/**
 * DeleteLogDialog - Confirmation dialog for deleting a meal.
 * Follows accessibility best practices with destructive styling.
 */
export function DeleteLogDialog({
  open,
  onOpenChange,
  onConfirm,
  isDeleting,
}: DeleteLogDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-xl">Delete this meal?</AlertDialogTitle>
          <AlertDialogDescription className="text-base">
            This action cannot be undone. This will permanently delete your meal
            entry and all associated data.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="flex-col gap-3 sm:flex-row">
          <AlertDialogCancel
            className="h-14 w-full text-lg sm:w-auto"
            disabled={isDeleting}
          >
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              onConfirm();
            }}
            disabled={isDeleting}
            className="h-14 w-full bg-destructive text-destructive-foreground hover:bg-destructive/90 text-lg sm:w-auto"
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Deleting...
              </>
            ) : (
              'Delete'
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
