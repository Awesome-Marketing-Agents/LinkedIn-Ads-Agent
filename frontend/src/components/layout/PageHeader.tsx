interface PageHeaderProps {
  title: string;
  children?: React.ReactNode;
}

export function PageHeader({ title, children }: PageHeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-12 items-center justify-between border-b border-border bg-background/80 backdrop-blur-sm px-6">
      <h2 className="text-[13px] font-semibold">{title}</h2>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </header>
  );
}
