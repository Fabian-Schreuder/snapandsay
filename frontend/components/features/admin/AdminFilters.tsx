"use client";

import { useState } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export function AdminFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Initialize local state from URL params
  const [userId, setUserId] = useState(searchParams.get('user_id') || "");
  const [startDate, setStartDate] = useState(searchParams.get('start_date') || "");
  const [endDate, setEndDate] = useState(searchParams.get('end_date') || "");

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams(searchParams.toString());
    
    if (userId) params.set('user_id', userId);
    else params.delete('user_id');
    
    if (startDate) params.set('start_date', startDate);
    else params.delete('start_date');
    
    if (endDate) params.set('end_date', endDate);
    else params.delete('end_date');
    
    params.set('page', '1'); // Reset page on filter change
    
    router.push(`${pathname}?${params.toString()}`);
  };
  
  const clearFilters = () => {
     setUserId("");
     setStartDate("");
     setEndDate("");
     router.push(pathname);
  };

  return (
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
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
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
  );
}
