"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import type { DietaryLog } from "@/types/log";

interface AdminLogsTableProps {
  logs: DietaryLog[];
  onView: (log: DietaryLog) => void;
}

export function AdminLogsTable({ logs, onView }: AdminLogsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>User ID</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Calories</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                No logs found.
              </TableCell>
            </TableRow>
          ) : (
            logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="font-mono text-xs text-muted-foreground">{log.user_id}</TableCell>
                <TableCell className="whitespace-nowrap font-medium">
                  {new Date(log.created_at).toLocaleString()}
                </TableCell>
                <TableCell className="max-w-[300px] truncate" title={log.description || ""}>
                  {log.description || "-"}
                </TableCell>
                <TableCell>{log.calories ?? "-"}</TableCell>
                <TableCell>
                    {/* Status badge - simplistic for now */}
                  <span className="capitalize">{log.status}</span>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="sm" onClick={() => onView(log)}>
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
