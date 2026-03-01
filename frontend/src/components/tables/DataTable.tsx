import { cn } from "@/lib/utils";

interface Column {
  key: string;
  label: string;
  align?: "left" | "right";
}

interface DataTableProps {
  columns: Column[];
  rows: Record<string, unknown>[];
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export function DataTable({
  columns,
  rows,
  page,
  totalPages,
  onPageChange,
}: DataTableProps) {
  return (
    <div>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn(
                    "sticky top-0 bg-elevated px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground whitespace-nowrap border-b border-border",
                    col.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="text-center py-10 text-muted-foreground text-[13px]"
                >
                  No data available
                </td>
              </tr>
            ) : (
              rows.map((row, i) => (
                <tr
                  key={i}
                  className="hover:bg-accent-muted/50 transition-colors"
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-3 py-1.5 text-[13px] tabular-nums border-b border-edge-soft/50 text-card-foreground",
                        col.align === "right" ? "text-right" : "text-left",
                      )}
                    >
                      {String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {page != null && totalPages != null && totalPages > 1 && onPageChange && (
        <div className="flex items-center justify-between mt-3">
          <span className="text-[11px] tabular-nums text-muted-foreground">
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              className="rounded-md border border-border px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-accent-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              Prev
            </button>
            <button
              className="rounded-md border border-border px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-accent-muted disabled:opacity-40 disabled:pointer-events-none transition-colors"
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
