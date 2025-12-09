"use client";
import { useState, useEffect, useCallback } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import AdminGuard from "@/components/AdminGuard";
import { AdminLogsTable } from "@/components/features/admin/AdminLogsTable";
import { adminApi } from "@/lib/api";
import type { DietaryLog, LogListMeta } from "@/types/log";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PagePagination } from "@/components/page-pagination";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function AdminDashboardPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [logs, setLogs] = useState<DietaryLog[]>([]);
  const [meta, setMeta] = useState<LogListMeta>({ total: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters State (for inputs)
  const [userIdObj, setUserIdObj] = useState(searchParams.get('user_id') || "");
  const [startDate, setStartDate] = useState(searchParams.get('start_date') || "");
  const [endDate, setEndDate] = useState(searchParams.get('end_date') || "");
  
  const page = Number(searchParams.get('page')) || 1;
  const limit = Number(searchParams.get('size')) || 20;

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await adminApi.getLogs({
        page,
        limit,
        user_id: searchParams.get('user_id') || undefined,
        start_date: searchParams.get('start_date') || undefined,
        end_date: searchParams.get('end_date') || undefined
      });
      setLogs(response.data);
      setMeta(response.meta);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || 'Failed to fetch logs');
      } else {
         setError('Failed to fetch logs');
      }
    } finally {
      setLoading(false);
    }
  }, [searchParams, page, limit]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    
    if (userIdObj) params.set('user_id', userIdObj);
    else params.delete('user_id');
    
    if (startDate) params.set('start_date', startDate);
    else params.delete('start_date');
    
    if (endDate) params.set('end_date', endDate);
    else params.delete('end_date');
    
    params.set('page', '1'); // Reset page
    
    router.push(`${pathname}?${params.toString()}`);
  };
  
  const clearFilters = () => {
     setUserIdObj("");
     setStartDate("");
     setEndDate("");
     router.push(pathname);
  };

  return (
    <AdminGuard>
      <div className="container mx-auto py-8 space-y-8">
        <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        </div>
        
        {/* Filters */}
        <Card>
            <CardHeader>
                <CardTitle className="text-lg">Filters</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleFilterSubmit} className="flex flex-wrap gap-4 items-end">
                    <div className="space-y-2">
                        <Label htmlFor="userId">User ID</Label>
                        <Input 
                            id="userId" 
                            placeholder="UUID..." 
                            value={userIdObj}
                            onChange={(e) => setUserIdObj(e.target.value)}
                            className="w-[300px]"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="start">Start Date</Label>
                        <Input 
                            id="start" 
                            type="date" 
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="end">End Date</Label>
                        <Input 
                            id="end" 
                            type="date" 
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-2">
                        <Button type="submit">Apply Filters</Button>
                        <Button type="button" variant="ghost" onClick={clearFilters}>Clear</Button>
                    </div>
                </form>
            </CardContent>
        </Card>

        {error && (
            <div className="rounded bg-red-100 p-4 text-red-700">
                {error}
            </div>
        )}

        <div className="space-y-4">
             {loading ? (
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
    </AdminGuard>
  );
}
