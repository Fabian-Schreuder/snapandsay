"use client";
import { useSearchParams } from "next/navigation";
import AdminGuard from "@/components/AdminGuard";
import { AdminLogsTable } from "@/components/features/admin/AdminLogsTable";
import { AdminFilters } from "@/components/features/admin/AdminFilters";
import { ExportDataButton } from "@/components/features/admin/ExportDataButton";
import { adminApi } from "@/lib/api";
import { PagePagination } from "@/components/page-pagination";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import type { DietaryLogListResponse } from "@/types/log";

import { Suspense } from "react";

function AdminDashboardContent() {
  const searchParams = useSearchParams();
  
  const page = Number(searchParams.get('page')) || 1;
  const limit = Number(searchParams.get('size')) || 20;

  const { data, isLoading, error } = useQuery<DietaryLogListResponse>({
    queryKey: ['admin-logs', page, limit, searchParams.toString()], // Include searchParams string to trigger refetch on filter change
    queryFn: () => adminApi.getLogs({
      page,
      limit,
      user_id: searchParams.get('user_id') || undefined,
      start_date: searchParams.get('start_date') || undefined,
      end_date: searchParams.get('end_date') || undefined,
      min_calories: searchParams.get('min_calories') ? Number(searchParams.get('min_calories')) : undefined,
      max_calories: searchParams.get('max_calories') ? Number(searchParams.get('max_calories')) : undefined,
    }),
    placeholderData: keepPreviousData
  });

  const logs = data?.data || [];
  const meta = data?.meta || { total: 0, page: 1, limit: 20, pages: 0 };

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          <ExportDataButton />
      </div>
      
      <AdminFilters />

      {error && (
          <div className="rounded bg-red-100 p-4 text-red-700">
              {error instanceof Error ? error.message : 'Failed to fetch logs'}
          </div>
      )}

      <div className="space-y-4">
            {isLoading ? (
                <div className="p-8 text-center text-muted-foreground">Loading logs...</div>
            ) : (
              <>
                  <AdminLogsTable logs={logs} onView={() => {}} />
                  <PagePagination 
                      currentPage={page}
                      totalPages={Math.ceil(meta.total / limit)}
                      pageSize={limit}
                      totalItems={meta.total}
                      basePath="/admin"
                    />
              </>
            )}
      </div>
    </div>
  );
}

export default function AdminDashboardPage() {
  return (
    <AdminGuard>
      <Suspense fallback={<div className="p-8 text-center">Loading dashboard...</div>}>
         <AdminDashboardContent />
      </Suspense>
    </AdminGuard>
  );
}
