'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
/* ... imports ... */
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
  const t = useTranslations('logs.edit');
  const tCommon = useTranslations('common');
  const updateLog = useUpdateLog();
  
  // Form state
  const [title, setTitle] = useState(log.title || '');
  const [description, setDescription] = useState(log.description || '');
  const [calories, setCalories] = useState(log.calories?.toString() || '');
  const [protein, setProtein] = useState(log.protein?.toString() || '');
  const [carbs, setCarbs] = useState(log.carbs?.toString() || '');
  const [fats, setFats] = useState(log.fats?.toString() || '');

  // Reset form when log changes or sheet opens
  useEffect(() => {
    if (open) {
      setTitle(log.title || '');
      setDescription(log.description || '');
      setCalories(log.calories?.toString() || '');
      setProtein(log.protein?.toString() || '');
      setCarbs(log.carbs?.toString() || '');
      setFats(log.fats?.toString() || '');
    }
  }, [log, open]);

  // Check if form has changes
  const isDirty =
    title !== (log.title || '') ||
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
    (title?.length || 0) <= 100 &&
    description.length <= 500 &&
    (caloriesNum === null || (!isNaN(caloriesNum) && caloriesNum >= 0 && caloriesNum <= 5000)) &&
    (proteinNum === null || (!isNaN(proteinNum) && proteinNum >= 0 && proteinNum <= 500)) &&
    (carbsNum === null || (!isNaN(carbsNum) && carbsNum >= 0 && carbsNum <= 500)) &&
    (fatsNum === null || (!isNaN(fatsNum) && fatsNum >= 0 && fatsNum <= 500));

  const handleSave = () => {
    const data: LogUpdateRequest = {};

    // Check title
    if (title !== (log.title || '')) {
      data.title = title || null;
    }
    
    // Check description
    if (description !== (log.description || '')) {
      data.description = description || null;
    }

    // Helper to process numeric fields
    const processNumeric = (
      currentVal: string, 
      originalVal: number | null | undefined
    ): number | null | undefined => {
      // If current is empty string...
      if (!currentVal) {
        // ...and original was not null/undefined, we want to clear it (send null)
        if (originalVal != null) return null;
        // ...and original was already null/undefined, no change needed (return undefined)
        return undefined;
      }
      // If current has value, parse it
      const numVal = Number(currentVal);
      // If different from original, return new value
      if (numVal !== originalVal) return numVal;
      // No change
      return undefined;
    };

    const caloriesUpdate = processNumeric(calories, log.calories);
    if (caloriesUpdate !== undefined) data.calories = caloriesUpdate;

    const proteinUpdate = processNumeric(protein, log.protein);
    if (proteinUpdate !== undefined) data.protein = proteinUpdate;

    const carbsUpdate = processNumeric(carbs, log.carbs);
    if (carbsUpdate !== undefined) data.carbs = carbsUpdate;

    const fatsUpdate = processNumeric(fats, log.fats);
    if (fatsUpdate !== undefined) data.fats = fatsUpdate;

    // Only mutate if we have updates
    if (Object.keys(data).length > 0) {
      updateLog.mutate(
        { logId: log.id, data },
        {
          onSuccess: () => {
            onOpenChange(false);
          },
        }
      );
    } else {
      // No changes detected (or reverted to original), just close
      onOpenChange(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="bottom" className="h-[85vh] overflow-y-auto">
        <SheetHeader className="text-left">
          <SheetTitle className="text-xl">{t('title')}</SheetTitle>
          <SheetDescription>
            {t('description')}
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title" className="text-base">
              {t('labels.title')}
            </Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              className="h-14 w-full rounded-lg border bg-background px-4 text-lg focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('placeholders.title')}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description" className="text-base">
              {t('labels.description')}
            </Label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              className="h-24 w-full rounded-lg border bg-background px-4 py-3 text-lg resize-none focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder={t('placeholders.description')}
            />
            <p className="text-sm text-muted-foreground text-right">
              {t('errors.maxChars', { count: description.length })}
            </p>
          </div>

          {/* Calories */}
          <div className="space-y-2">
            <Label htmlFor="calories" className="text-base">
              {t('labels.calories')}
            </Label>
            <Input
              id="calories"
              type="number"
              value={calories}
              onChange={(e) => setCalories(e.target.value)}
              min={0}
              max={5000}
              className="h-14 text-lg"
              placeholder={t('placeholders.zero')}
            />
            {caloriesNum !== null && (caloriesNum < 0 || caloriesNum > 5000) && (
              <p className="text-sm text-destructive">{t('errors.range')}</p>
            )}
          </div>

          {/* Macros Grid */}
          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="protein" className="text-base">
                {t('labels.protein')}
              </Label>
              <Input
                id="protein"
                type="number"
                value={protein}
                onChange={(e) => setProtein(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder={t('placeholders.zero')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="carbs" className="text-base">
                {t('labels.carbs')}
              </Label>
              <Input
                id="carbs"
                type="number"
                value={carbs}
                onChange={(e) => setCarbs(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder={t('placeholders.zero')}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fats" className="text-base">
                {t('labels.fats')}
              </Label>
              <Input
                id="fats"
                type="number"
                value={fats}
                onChange={(e) => setFats(e.target.value)}
                min={0}
                max={500}
                className="h-14 text-lg"
                placeholder={t('placeholders.zero')}
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
              {tCommon('cancel')}
            </Button>
            <Button
              onClick={handleSave}
              disabled={!isDirty || !isValid || updateLog.isPending}
              className="h-14 flex-1 text-lg"
            >
              {updateLog.isPending ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  {t('saving')}
                </>
              ) : (
                t('save')
              )}
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
