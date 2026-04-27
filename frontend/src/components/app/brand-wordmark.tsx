import { BriefcaseBusiness } from "lucide-react";

type BrandWordmarkProps = {
  className?: string;
  iconClassName?: string;
};

export function BrandWordmark({
  className,
  iconClassName,
}: BrandWordmarkProps) {
  const rootClassName = [
    "inline-flex items-center gap-2.5 leading-none",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const markClassName = [
    "h-[1.65rem] w-auto text-[color:var(--accent)] sm:h-[1.8rem]",
    iconClassName,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={rootClassName} aria-label="Wandrix">
      <BriefcaseBusiness className={markClassName} strokeWidth={2.15} />

      <span className="font-display text-[1.52rem] leading-none font-semibold text-[color:var(--nav-brand-text)] sm:text-[1.68rem]">
        Wandrix
      </span>
    </span>
  );
}
