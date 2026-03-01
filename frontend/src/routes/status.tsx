import { createFileRoute } from "@tanstack/react-router";
import { useStatus } from "@/hooks/useReport";
import { PageHeader } from "@/components/layout/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/status")({
  component: StatusPage,
});

function StatusPage() {
  const { data, isLoading } = useStatus();

  if (isLoading) {
    return (
      <>
        <PageHeader title="System" />
        <div className="p-6 max-w-2xl space-y-3">
          <Card>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-4 w-20" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <Skeleton className="h-4 w-28" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-20 w-full" />
            </CardContent>
          </Card>
        </div>
      </>
    );
  }

  const token = data?.token ?? ({} as Record<string, unknown>);
  const db = data?.database ?? {};
  const audit = data?.active_campaign_audit ?? [];
  const connected = (token as { authenticated?: boolean }).authenticated ?? false;

  return (
    <>
      <PageHeader title="System" />
      <div className="p-6 max-w-2xl space-y-3">
        {/* Token health */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-[13px]">Token Health</CardTitle>
              <Badge
                variant="outline"
                className={cn(
                  connected
                    ? "border-signal-positive/30 bg-signal-positive/10 text-signal-positive"
                    : "border-signal-error/30 bg-signal-error/10 text-signal-error",
                )}
              >
                {connected ? "Healthy" : "Disconnected"}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            {connected ? (
              <div className="grid grid-cols-2 gap-3">
                <TokenStat
                  label="Access token"
                  value={`${(token as { access_token_days_remaining?: number }).access_token_days_remaining ?? 0}d`}
                />
                {(token as { refresh_token_days_remaining?: number | null })
                  .refresh_token_days_remaining != null && (
                  <TokenStat
                    label="Refresh token"
                    value={`${(token as { refresh_token_days_remaining?: number }).refresh_token_days_remaining}d`}
                  />
                )}
              </div>
            ) : (
              <p className="text-[13px] text-muted-foreground">
                No active token. Visit Connection to authenticate.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Database */}
        <Card>
          <CardHeader>
            <CardTitle className="text-[13px]">Database</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-[10px] font-semibold uppercase tracking-[0.08em]">
                    Table
                  </TableHead>
                  <TableHead className="text-[10px] font-semibold uppercase tracking-[0.08em] text-right">
                    Rows
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(db).map(([table, count]) => (
                  <TableRow key={table}>
                    <TableCell className="text-[13px]">{table}</TableCell>
                    <TableCell className="text-[13px] text-right tabular-nums">
                      {(count as number).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Campaign audit */}
        <Card>
          <CardHeader>
            <CardTitle className="text-[13px]">Campaign Audit</CardTitle>
          </CardHeader>
          <CardContent>
            {audit.length === 0 ? (
              <p className="text-[13px] text-muted-foreground">
                No active campaigns to audit.
              </p>
            ) : (
              <Accordion type="multiple">
                {audit.map((entry, i) => (
                  <AccordionItem key={i} value={`audit-${i}`}>
                    <AccordionTrigger className="py-2 text-[13px] hover:no-underline">
                      <div className="flex items-center justify-between flex-1 pr-2">
                        <span className="font-medium">{entry.name}</span>
                        {entry.issues.length > 0 ? (
                          <Badge variant="outline" className="border-signal-warning/30 bg-signal-warning/10 text-signal-warning text-[10px]">
                            {entry.issues.length} issue{entry.issues.length > 1 ? "s" : ""}
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="border-signal-positive/30 bg-signal-positive/10 text-signal-positive text-[10px]">
                            OK
                          </Badge>
                        )}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      {entry.issues.length > 0 ? (
                        <ul className="space-y-1 text-[12px] text-muted-foreground pl-4">
                          {entry.issues.map((issue, j) => (
                            <li key={j} className="list-disc">{issue}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-[12px] text-muted-foreground">No issues found.</p>
                      )}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function TokenStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-elevated px-3 py-2">
      <div className="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
        {label}
      </div>
      <div className="text-lg font-semibold tabular-nums leading-tight mt-0.5">
        {value}
      </div>
    </div>
  );
}
