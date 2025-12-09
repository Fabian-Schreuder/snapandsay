
"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { adminApi } from "@/lib/api";
import { toast } from "sonner";
import { Download, Loader2 } from "lucide-react";

export function ExportDataButton() {
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: "csv" | "json") => {
    try {
      setLoading(true);
      toast.info(`Generating ${format.toUpperCase()} export...`);

      const blob = await adminApi.exportLogs({
        format,
        user_id: searchParams.get("user_id") || undefined,
        start_date: searchParams.get("start_date") || undefined,
        end_date: searchParams.get("end_date") || undefined,
        min_calories: searchParams.get("min_calories") ? Number(searchParams.get("min_calories")) : undefined,
        max_calories: searchParams.get("max_calories") ? Number(searchParams.get("max_calories")) : undefined,
      });

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      
      // Generate filename matching backend format: snapandsay_export_YYYYMMDD_HHMM
      const now = new Date();
      const pad = (n: number) => n.toString().padStart(2, '0');
      const timestamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}`;
      link.setAttribute("download", `snapandsay_export_${timestamp}.${format}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast.success("Export downloaded successfully");
    } catch (error) {
      toast.error("Failed to export data");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" disabled={loading}>
          {loading ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-2 h-4 w-4" />
          )}
          Export Data
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleExport("csv")}>
          Export as CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport("json")}>
          Export as JSON
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
