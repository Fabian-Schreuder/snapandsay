/**
 * Type definitions for dietary log responses.
 */

export interface DietaryLog {
  id: string;
  image_path: string;
  transcript: string | null;
  description: string | null;
  calories: number | null;
  protein: number | null;
  carbs: number | null;
  fats: number | null;
  needs_review: boolean;
  created_at: string;
}

export interface LogUpdateRequest {
  description?: string | null;
  calories?: number | null;
  protein?: number | null;
  carbs?: number | null;
  fats?: number | null;
}

export interface LogListMeta {
  total: number;
}

export interface DietaryLogListResponse {
  data: DietaryLog[];
  meta: LogListMeta;
}
