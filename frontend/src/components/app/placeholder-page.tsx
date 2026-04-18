import Link from "next/link";


type PlaceholderPageProps = {
  eyebrow: string;
  title: string;
  description: string;
};


export function PlaceholderPage({
  eyebrow,
  title,
  description,
}: PlaceholderPageProps) {
  return (
    <main className="px-5 py-8 sm:px-8">
      <div className="grid min-h-[calc(100vh-8rem)] place-items-center rounded-[2rem] border border-shell-border bg-shell px-6 py-10">
        <section className="w-full max-w-3xl rounded-[2rem] border border-shell-border bg-panel p-8 text-center shadow-[0_24px_80px_rgba(86,50,21,0.12)]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
            {eyebrow}
          </p>
          <h1 className="mt-4 font-display text-5xl font-semibold tracking-tight text-foreground">
            {title}
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-foreground/75">
            {description}
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              href="/chat"
              className="rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white transition hover:bg-accent-strong"
            >
              Open chat planner
            </Link>
            <Link
              href="/"
              className="rounded-full border border-shell-border px-6 py-3 text-sm font-semibold text-foreground transition hover:bg-background"
            >
              Back home
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
