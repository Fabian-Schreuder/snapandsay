import { supabase } from '@/lib/supabase';
import type { DietaryLogListResponse } from '@/types/log';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export const analysisApi = {
  upload: async (payload: {
    image_path: string;
    audio_path?: string | null;
    client_timestamp: string;
  }) => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
        throw new Error('No active session');
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/analysis/upload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${session.access_token}`
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload analysis failed');
    }
    
    return response.json();
  }
};

export const logsApi = {
  /**
   * Fetch dietary logs for a specific date.
   * @param date - Optional ISO date string (YYYY-MM-DD). Defaults to today.
   */
  getByDate: async (date?: string): Promise<DietaryLogListResponse> => {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('No active session');
    }

    const url = date 
      ? `${API_BASE_URL}/api/v1/logs?date=${date}` 
      : `${API_BASE_URL}/api/v1/logs`;
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${session.access_token}`
      }
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to fetch logs');
    }
    
    return response.json();
  }
};
