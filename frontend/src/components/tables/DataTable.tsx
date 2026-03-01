import { useState, useMemo, useCallback } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown, Search, Download, Inbox } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface Column {
  key: string;
  label: string;
  align?: "left" | "right";
  format?: (value: unknown) => string;
}

interface DataTableProps {
  columns: Column[];
  rows: Record<string, unknown>[];
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  pageSize?: number;
  onPageSizeChange?: (size: number) => void;
  loading?: boolean;
  searchable?: boolean;
  exportable?: boolean;
  exportFilename?: string;
}

type SortDir = "asc" | "desc" | null;

export function DataTable({
  columns,
  rows,
  page,
  totalPages,
  onPageChange,
  pageSize,
  onPageSizeChange,
  loading = false,
  searchable = true,
  exportable = true,
  exportFilename = "export",
}: DataTableProps) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDir>(null);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : sortDir === "desc" ? null : "asc");
      if (sortDir === "desc") setSortKey(null);
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const filteredRows = useMemo(() => {
    if (!search.trim()) return rows;
    const q = search.toLowerCase();
    return rows.filter((row) =>
      columns.some((col) => String(row[col.key] ?? "").toLowerCase().includes(q)),
    );
  }, [rows, search, columns]);

  const sortedRows = useMemo(() => {
    if (!sortKey || !sortDir) return filteredRows;
    return [...filteredRows].sort((a, b) => {
      const aVal = a[sortKey] ?? "";
      const bVal = b[sortKey] ?? "";
      const aNum = Number(aVal);
      const bNum = Number(bVal);
      if (!isNaN(aNum) && !isNaN(bNum)) {
        return sortDir === "asc" ? aNum - bNum : bNum - aNum;
      }
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filteredRows, sortKey, sortDir]);

  const exportCsv = useCallback(() => {
    const header = columns.map((c) => c.label).join(",");
    const body = sortedRows
      .map((row) =>
        columns
          .map((col) => {
            const v = String(row[col.key] ?? "");
            return v.includes(",") ? `"${v}"` : v;
          })
          .join(","),
      )
      .join("\n");
    const blob = new Blob([`${header}\n${body}`], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${exportFilename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [columns, sortedRows, exportFilename]);

  if (loading) {
    return (
      <div className="rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col.key}>
                  <Skeleton className="h-3 w-16" />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={i}>
                {columns.map((col) => (
                  <TableCell key={col.key}>
                    <Skeleton className="h-3 w-20" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {(searchable || exportable || onPageSizeChange) && (
        <div className="flex items-center gap-2 flex-wrap">
          {searchable && (
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 h-8 text-[13px]"
              />
            </div>
          )}
          <div className="flex items-center gap-2 ml-auto">
            {onPageSizeChange && (
              <Select
                value={String(pageSize ?? 50)}
                onValueChange={(v) => onPageSizeChange(Number(v))}
              >
                <SelectTrigger className="h-8 w-[80px] text-[12px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[10, 25, 50, 100].map((n) => (
                    <SelectItem key={n} value={String(n)} className="text-[12px]">
                      {n} rows
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {exportable && (
              <Button variant="outline" size="sm" onClick={exportCsv} className="text-[12px] gap-1.5">
                <Download className="h-3.5 w-3.5" />
                CSV
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="rounded-md border border-border">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead
                  key={col.key}
                  className={cn(
                    "text-[10px] font-semibold uppercase tracking-[0.08em] cursor-pointer select-none hover:text-foreground",
                    col.align === "right" && "text-right",
                  )}
                  onClick={() => handleSort(col.key)}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {sortKey === col.key && sortDir === "asc" ? (
                      <ArrowUp className="h-3 w-3" />
                    ) : sortKey === col.key && sortDir === "desc" ? (
                      <ArrowDown className="h-3 w-3" />
                    ) : (
                      <ArrowUpDown className="h-3 w-3 opacity-30" />
                    )}
                  </span>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-32">
                  <div className="flex flex-col items-center justify-center gap-2 text-muted-foreground">
                    <Inbox className="h-8 w-8 opacity-40" />
                    <span className="text-[13px]">No data available</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              sortedRows.map((row, i) => (
                <TableRow key={i}>
                  {columns.map((col) => (
                    <TableCell
                      key={col.key}
                      className={cn(
                        "text-[13px] tabular-nums",
                        col.align === "right" && "text-right",
                      )}
                    >
                      {col.format
                        ? col.format(row[col.key])
                        : String(row[col.key] ?? "")}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {page != null && totalPages != null && totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between">
          <span className="text-[11px] tabular-nums text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="text-[11px]"
            >
              Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="text-[11px]"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
