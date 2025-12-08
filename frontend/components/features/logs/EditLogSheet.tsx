'use client';

import { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { useUpdateLog } from '@/hooks/use-logs';
import type { DietaryLog, LogUpdateRequest } from '@/types/log';

interface EditLogSheetProps {
  log: DietaryLog;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/**
 * EditLogSheet - Bottom drawer for editing meal details.
 * Senior-friendly with large inputs and clear labels.
 */
export function EditLogSheet({ log, open, onOpenChange }: EditLogSheetProps) {
  const updateLog = useUpdateLog();
  
  // Form state
  const [description, setDescription] = useState(log.description || '');
  const [calories, setCalories] = useState(log.calories?.toString() || '');
  const [protein, setProtein] = useState(log.protein?.toString() || '');
  const [carbs, setCarbs] = useState(log.carbs?.toString() || '');
  const [fats, setFats] = useState(log.fats?.toString() || '');

  // Reset form when log changes or sheet opens
  useEffect(() => {
    if (open) {
      setDescription(log.description || '');
      setCalories(log.calories?.toString() || '');
      setProtein(log.protein?.toString() || '');
      setCarbs(log.carbs?.toString() || '');
      setFats(log.fats?.toString() || '');
    }
  }, [log, open]);

  // Check if form has changes
  const isDirty =
    description !== (log.description || '') ||
    calories !== (log.calories?.toString() || '') ||
    protein !== (log.protein?.toString() || '') ||
    carbs !== (log.carbs?.toString() || '') ||
    fats !== (log.fats?.toString() || '');

  // Validation
  const caloriesNum = calories ? Number(calories) : null;
  const proteinNum = protein ? Number(protein) : null;
  const carbsNum = carbs ? Number(carbs) : null;
  const fatsNum = fats ? Number(fats) : null;

  const isValid =
    description.length <= 500 &&
    (caloriesNum === null || (caloriesNum >= 0 && caloriesNum <= 5000)) &&
    (proteinNum === null || (proteinNum >= 0 && proteinNum <= 500)) &&
    (carbsNum === null || (carbsNum >= 0 && carbsNum <= 500)) &&
    (fatsNum === null || (fatsNum >= 0 && fatsNum <= 500));

  const handleSave = () => {
    const data: LogUpdateRequest = {};
    
    if (description !== (log.description || '')) {
      data.description = description || undefined;
    }
    if (calories !== (log.calories?.toString() || '')) {
      data.calories = calories ? Number(calories) : undefined;
    }
    if (protein !== (log.protein?.toString() || '')) {
      data.protein = protein ? Number(protein) : undefined;
    }
    if (carbs !== (log.carbs?.toString() || '')) {
      data.carbs = carbs ? Number(carbs) : undefined;
    }
    if (fats !== (log.fats?.toString() || '')) {
      data.fats = fats ? Number(fats) : undefined;
    }

    updateLog.mutate(
      { logId: log.id, data },
      {
        onSuccess: () => {
          onOpenChange(false);
        },
      }
    );
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="h-[85vh] overflow-y-auto">
        <SheetHeader className="text-left">
          <SheetTitle className="text-xl">Edit Meal</SheetTitle>
          <SheetDescription>
            Update the meal details below. Tap Save when done.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-base">
              Description
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              className="h-24 w-full rounded-lg border bg-background px-4 py-3 text-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Describe your meal..."
            />
            <p className="text-sm text-muted-foreground text-right">
              {description.length}/500
            </p>
          </div>

          {/* Calories */}
          <div className="space-y-2">
            <Label htmlFor="calories" className="text-base">
              Calories
            </Label>
            <Input
              id="calories"
              type="number"
              value={calories}
              onChange={(e) => setCalories(e.target.value)}
              min={0}
              max={5000}
              className="h-14 text-lg"
              placeholder="0"
            />
            {caloriesNum !== null && (caloriesNum < 0 || caloriesNum > 5000) && (
              <p className="text-sm text-destructive">Must be 0-5000</p>
            )}
          </div>

          {/* Macros Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="protein" className="text-base">
                Protein (g)
              </Label>
              <Input
                id="protein"
                type="number"
                value={protein}
                onChange={(e) => setProtein(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="carbs" className="text-base">
                Carbs (g)
              </Label>
              <Input
                id="carbs"
                type="number"
                value={carbs}
                onChange={(e) => setCarbs(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder="0"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fats" className="text-base">
                Fats (g)
              </Label>
              <Input
                id="fats"
                type="number"
                value={fats}
                onChange={(e) => setFats(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder="0"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <Button
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="h-14 flex-1 text-lg"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={!isDirty || !isValid || updateLog.isPending}
              className="h-14 flex-1 text-lg"
            >
              {updateLog.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
