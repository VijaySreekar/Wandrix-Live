"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";

type AuthMode = "signin" | "signup";

type AuthShellProps = {
  nextPath: string;
};

export function AuthShell({ nextPath }: AuthShellProps) {
  const router = useRouter();
  const supabase = useMemo(() => createSupabaseBrowserClient(), []);
  const onboardingPath = `${nextPath}${nextPath.includes("?") ? "&" : "?"}onboarding=1`;
  const [mode, setMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setMessage(null);
    setError(null);

    try {
      if (mode === "signin") {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

        if (signInError) {
          throw signInError;
        }

        router.replace(nextPath);
        router.refresh();
        return;
      }

      const emailRedirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(onboardingPath)}`;
      const { data, error: signUpError } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          emailRedirectTo,
        },
      });

      if (signUpError) {
        throw signUpError;
      }

      if (data.session) {
        router.replace(onboardingPath);
        router.refresh();
        return;
      }

      setMessage(
        "Account created. Check your email to confirm it, then finish your account setup before planning.",
      );
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Authentication failed.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="min-h-[calc(100vh-var(--nav-height))] bg-background px-4 py-10 sm:px-6 sm:py-16">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-center">
        <div className="relative w-full max-w-md rounded-[2rem] border border-shell-border bg-background p-6 shadow-sm sm:p-8">
          <div className="relative">
            <span className="inline-flex items-center gap-2 rounded-full border border-shell-border bg-panel px-3 py-1 text-sm text-foreground/70">
              <span className="h-2 w-2 rounded-full bg-[color:var(--brand-ocean)]" />
              Authentication
            </span>

            <h1 className="mt-5 text-3xl font-semibold tracking-tight text-foreground">
              {mode === "signin"
                ? "Log in to reopen your trip workspace."
                : "Create your Wandrix account."}
            </h1>
            <p className="mt-3 text-sm leading-7 text-foreground/72">
              Conversation, board, and brochure stay connected to the same saved
              trip, and first-time setup lets Wandrix start with better context.
            </p>
          </div>

          <div className="relative mt-6 flex items-center gap-2 rounded-full border border-shell-border bg-panel p-1">
            <ModeButton
              active={mode === "signin"}
              label="Log in"
              onClick={() => setMode("signin")}
            />
            <ModeButton
              active={mode === "signup"}
              label="Create account"
              onClick={() => setMode("signup")}
            />
          </div>

          <form className="relative mt-6 grid gap-4" onSubmit={handleSubmit}>
            <label className="grid gap-2 text-sm text-foreground/82">
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-12 rounded-[1.25rem] border border-shell-border bg-background px-4 text-foreground outline-none transition focus:border-[color:var(--brand-ocean)]"
                placeholder="you@example.com"
                required
              />
            </label>

            <label className="grid gap-2 text-sm text-foreground/82">
              Password
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete={
                    mode === "signin" ? "current-password" : "new-password"
                  }
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="h-12 w-full rounded-[1.25rem] border border-shell-border bg-background px-4 pr-16 text-foreground outline-none transition focus:border-[color:var(--brand-ocean)]"
                  placeholder={
                    mode === "signin"
                      ? "Enter your password"
                      : "Create a password"
                  }
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((current) => !current)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-foreground/60 transition hover:bg-panel hover:text-foreground"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            {message ? (
              <p className="rounded-[1.25rem] border border-shell-border bg-panel px-4 py-3 text-sm leading-7 text-foreground/80">
                {message}
              </p>
            ) : null}

            {error ? (
              <p className="rounded-[1.25rem] border border-[color:var(--brand-ocean)]/20 bg-[color:var(--brand-ocean)]/8 px-4 py-3 text-sm leading-7 text-foreground/80">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex h-12 items-center justify-center rounded-[1.25rem] bg-[linear-gradient(135deg,var(--brand-ocean),var(--brand-sun))] px-6 text-sm font-semibold text-white shadow-[0_18px_40px_rgba(29,78,216,0.2)] transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isLoading
                ? mode === "signin"
                  ? "Logging in..."
                  : "Creating account..."
                : mode === "signin"
                  ? "Log in"
                  : "Create account"}
            </button>
          </form>

          <div className="relative mt-6 flex items-center justify-between gap-4 text-sm text-foreground/68">
            <p>
              {mode === "signin"
                ? "Need an account? Switch to create account."
                : "Already signed up? Switch back to log in."}
            </p>
            <Link href="/" className="font-semibold text-[color:var(--brand-ocean)]">
              Back home
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}

function ModeButton({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "flex-1 rounded-full px-4 py-2.5 text-sm font-semibold transition",
        active
          ? "bg-[linear-gradient(135deg,var(--brand-ocean),var(--brand-sun))] text-white shadow-[0_12px_30px_rgba(29,78,216,0.2)]"
          : "text-foreground/68 hover:bg-white/70 hover:text-foreground",
      ].join(" ")}
    >
      {label}
    </button>
  );
}
