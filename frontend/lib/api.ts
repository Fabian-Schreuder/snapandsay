import { supabase } from "@/lib/supabase";
import type {
  DietaryLogListResponse,
  DietaryLog,
  LogUpdateRequest,
} from "@/types/log";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const analysisApi = {
  upload: async (payload: {
    image_path: string;
    audio_path?: string | null;
    client_timestamp: string;
    language: "en" | "nl";
  }) => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/analysis/upload`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Upload analysis failed");
    }

    return response.json();
  },
};

export const logsApi = {
  /**
   * Fetch dietary logs for a specific date.
   * @param date - Optional ISO date string (YYYY-MM-DD). Defaults to today.
   */
  getByDate: async (date?: string): Promise<DietaryLogListResponse> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const url = date
      ? `${API_BASE_URL}/api/v1/logs?date=${date}`
      : `${API_BASE_URL}/api/v1/logs`;

    const response = await fetch(url, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to fetch logs");
    }

    return response.json();
  },

  /**
   * Fetch a single dietary log by ID.
   * @param logId - UUID of the log to retrieve.
   */
  getById: async (logId: string): Promise<DietaryLog> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to fetch log");
    }

    return response.json();
  },

  /**
   * Update a dietary log entry.
   * @param logId - UUID of the log to update.
   * @param data - Partial update data.
   */
  update: async (
    logId: string,
    data: LogUpdateRequest,
  ): Promise<DietaryLog> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to update log");
    }

    return response.json();
  },

  /**
   * Delete a dietary log entry.
   * @param logId - UUID of the log to delete.
   */
  delete: async (logId: string): Promise<void> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/logs/${logId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to delete log");
    }
  },
};

export const adminApi = {
  getLogs: async (params: {
    page: number;
    limit: number;
    user_id?: string;
    start_date?: string;
    end_date?: string;
    min_calories?: number;
    max_calories?: number;
  }): Promise<DietaryLogListResponse> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      limit: params.limit.toString(),
    });

    if (params.user_id) queryParams.append("user_id", params.user_id);
    if (params.start_date) queryParams.append("start_date", params.start_date);
    if (params.end_date) queryParams.append("end_date", params.end_date);
    if (params.min_calories)
      queryParams.append("min_calories", params.min_calories.toString());
    if (params.max_calories)
      queryParams.append("max_calories", params.max_calories.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/admin/logs?${queryParams}`,
      {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to fetch admin logs");
    }

    return response.json();
  },

  exportLogs: async (params: {
    format: "csv" | "json";
    user_id?: string;
    start_date?: string;
    end_date?: string;
    min_calories?: number;
    max_calories?: number;
  }): Promise<Blob> => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      throw new Error("No active session");
    }

    const queryParams = new URLSearchParams({
      format: params.format,
    });

    if (params.user_id) queryParams.append("user_id", params.user_id);
    if (params.start_date) queryParams.append("start_date", params.start_date);
    if (params.end_date) queryParams.append("end_date", params.end_date);
    if (params.min_calories)
      queryParams.append("min_calories", params.min_calories.toString());
    if (params.max_calories)
      queryParams.append("max_calories", params.max_calories.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/admin/export?${queryParams}`,
      {
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || "Failed to export logs");
    }

    return response.blob();
  },
};
