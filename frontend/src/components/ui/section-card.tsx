import type { ReactNode } from "react";


type SectionCardProps = {
  title?: string;
  eyebrow?: string;
  children: ReactNode;
  className?: string;
};


export function SectionCard({
  title,
  eyebrow,
  children,
  className = "",
}: SectionCardProps) {
  return (
    <section
      className={`rounded-[1.75rem] border border-panel-border bg-white/75 p-6 shadow-sm dark:bg-black/10 ${className}`.trim()}
    >
      {(eyebrow || title) && (
        <header className="mb-5 space-y-2">
          {eyebrow && (
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
              {eyebrow}
            </p>
          )}
          {title && <h2 className="text-2xl font-semibold text-foreground">{title}</h2>}
        </header>
      )}
      {children}
    </section>
  );
}
