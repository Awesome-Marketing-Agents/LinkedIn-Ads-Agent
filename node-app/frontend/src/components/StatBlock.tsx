interface StatBlockProps {
  label: string;
  value: string | number;
  meta?: string;
}

export function StatBlock({ label, value, meta }: StatBlockProps) {
  return (
    <div className="stat-block">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {meta && <div className="stat-meta">{meta}</div>}
    </div>
  );
}
