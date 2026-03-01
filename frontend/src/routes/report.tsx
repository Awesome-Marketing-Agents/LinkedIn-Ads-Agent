import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { DataTable } from "@/components/tables/DataTable";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useCampaignMetrics,
  useCreativeMetrics,
  useDemographics,
} from "@/hooks/useReport";

export const Route = createFileRoute("/report")({
  component: ReportPage,
});

const fmtNum = (v: unknown) => Number(v ?? 0).toLocaleString();
const fmtDollar = (v: unknown) => `$${Number(v ?? 0).toFixed(2)}`;
const fmtPct = (v: unknown) => `${Number(v ?? 0).toFixed(2)}%`;

const campaignColumns = [
  { key: "campaign_name", label: "Campaign" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impr.", align: "right" as const, format: fmtNum },
  { key: "clicks", label: "Clicks", align: "right" as const, format: fmtNum },
  { key: "spend", label: "Spend", align: "right" as const, format: fmtDollar },
  { key: "ctr", label: "CTR", align: "right" as const, format: fmtPct },
  { key: "cpc", label: "CPC", align: "right" as const, format: fmtDollar },
];

const creativeColumns = [
  { key: "campaign_name", label: "Campaign" },
  { key: "content_name", label: "Content" },
  { key: "date", label: "Date" },
  { key: "impressions", label: "Impr.", align: "right" as const, format: fmtNum },
  { key: "clicks", label: "Clicks", align: "right" as const, format: fmtNum },
  { key: "spend", label: "Spend", align: "right" as const, format: fmtDollar },
  { key: "ctr", label: "CTR", align: "right" as const, format: fmtPct },
];

const demoColumns = [
  { key: "pivot_type", label: "Pivot" },
  { key: "segment", label: "Segment" },
  { key: "impressions", label: "Impr.", align: "right" as const, format: fmtNum },
  { key: "clicks", label: "Clicks", align: "right" as const, format: fmtNum },
  { key: "ctr", label: "CTR", align: "right" as const, format: fmtPct },
  { key: "share_pct", label: "Share %", align: "right" as const, format: fmtPct },
];

function CampaignTab() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useCampaignMetrics(page);
  const rows = (data as Record<string, unknown> | undefined)?.rows as Record<string, unknown>[] ?? [];
  const totalPages = (data as Record<string, unknown> | undefined)?.total_pages as number ?? 1;

  return (
    <DataTable
      columns={campaignColumns}
      rows={rows}
      page={page}
      totalPages={totalPages}
      onPageChange={setPage}
      loading={isLoading}
      exportFilename="campaign-metrics"
    />
  );
}

function CreativeTab() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useCreativeMetrics(page);
  const rows = (data as Record<string, unknown> | undefined)?.rows as Record<string, unknown>[] ?? [];
  const totalPages = (data as Record<string, unknown> | undefined)?.total_pages as number ?? 1;

  return (
    <DataTable
      columns={creativeColumns}
      rows={rows}
      page={page}
      totalPages={totalPages}
      onPageChange={setPage}
      loading={isLoading}
      exportFilename="creative-metrics"
    />
  );
}

function DemographicsTab() {
  const [pivotType, setPivotType] = useState<string | undefined>();
  const { data, isLoading } = useDemographics(pivotType);
  const rows = (data as Record<string, unknown> | undefined)?.rows as Record<string, unknown>[] ?? [];

  return (
    <div className="space-y-3">
      <Select
        value={pivotType ?? "all"}
        onValueChange={(v) => setPivotType(v === "all" ? undefined : v)}
      >
        <SelectTrigger className="w-[200px] h-8 text-[12px]">
          <SelectValue placeholder="All pivot types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all" className="text-[12px]">All pivot types</SelectItem>
          <SelectItem value="MEMBER_COMPANY_SIZE" className="text-[12px]">Company Size</SelectItem>
          <SelectItem value="MEMBER_INDUSTRY" className="text-[12px]">Industry</SelectItem>
          <SelectItem value="MEMBER_SENIORITY" className="text-[12px]">Seniority</SelectItem>
          <SelectItem value="MEMBER_JOB_FUNCTION" className="text-[12px]">Job Function</SelectItem>
          <SelectItem value="MEMBER_COUNTRY_V2" className="text-[12px]">Country</SelectItem>
          <SelectItem value="MEMBER_REGION_V2" className="text-[12px]">Region</SelectItem>
        </SelectContent>
      </Select>
      <DataTable
        columns={demoColumns}
        rows={rows}
        loading={isLoading}
        exportFilename="demographics"
      />
    </div>
  );
}

function ReportPage() {
  return (
    <>
      <PageHeader title="Tables" />
      <div className="p-6">
        <Tabs defaultValue="campaigns">
          <TabsList>
            <TabsTrigger value="campaigns" className="text-[13px]">Campaigns</TabsTrigger>
            <TabsTrigger value="creatives" className="text-[13px]">Creatives</TabsTrigger>
            <TabsTrigger value="demographics" className="text-[13px]">Demographics</TabsTrigger>
          </TabsList>
          <TabsContent value="campaigns" className="mt-4">
            <CampaignTab />
          </TabsContent>
          <TabsContent value="creatives" className="mt-4">
            <CreativeTab />
          </TabsContent>
          <TabsContent value="demographics" className="mt-4">
            <DemographicsTab />
          </TabsContent>
        </Tabs>
      </div>
    </>
  );
}
