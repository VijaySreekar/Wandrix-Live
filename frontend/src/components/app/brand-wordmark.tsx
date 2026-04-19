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
      <svg
        viewBox="0 0 24 24"
        className={markClassName}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          x="3"
          y="7"
          width="18"
          height="13"
          rx="2.5"
          fill="currentColor"
          opacity="0.34"
          stroke="currentColor"
          strokeWidth="2.2"
        />
        <path
          d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
          stroke="currentColor"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
        <line
          x1="12"
          y1="7"
          x2="12"
          y2="20"
          stroke="currentColor"
          strokeWidth="2.2"
          opacity="0.58"
        />
        <rect x="10" y="11.5" width="4" height="3.5" rx="0.8" fill="currentColor" />
      </svg>

      <span className="flex items-baseline gap-0 [font-family:var(--font-brand)] text-[1.26rem] font-semibold tracking-[-0.03em] sm:text-[1.38rem]">
        <span className="text-foreground">WAND</span>
        <span className="text-[color:var(--accent)]">RIX</span>
      </span>
    </span>
  );
}
