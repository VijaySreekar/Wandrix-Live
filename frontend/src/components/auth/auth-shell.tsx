"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { createClient as createSupabaseBrowserClient } from "@/lib/supabase/client";


type AuthMode = "signin" | "signup";


type AuthShellProps = {
  nextPath: string;
};


export function AuthShell({ nextPath }: AuthShellProps) {
  const router = useRouter();
  const supabase = useMemo(() => createSupabaseBrowserClient(), []);
  const [mode, setMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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

      const emailRedirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(nextPath)}`;
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
        router.replace(nextPath);
        router.refresh();
        return;
      }

      setMessage(
        "Account created. Check your email to confirm the account before continuing.",
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
    <main className="flex min-h-screen items-center px-6 py-10 sm:px-10">
      <div className="mx-auto grid w-full max-w-6xl gap-6 lg:grid-cols-[1.05fr_0.95fr]">
        <section className="rounded-[2rem] border border-panel-border bg-panel p-8 shadow-[0_24px_80px_rgba(86,50,21,0.18)] backdrop-blur md:p-10">
          <div className="space-y-5">
            <span className="w-fit rounded-full border border-accent/20 bg-accent/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-accent-strong">
              Authentication
            </span>
            <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
              Sign in to open your trip workspace.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-foreground/75 sm:text-lg">
              Wandrix keeps each conversation tied to your saved trips. Sign in
              first so the assistant, trip board, and brochure all stay attached
              to your account.
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {[
              "Each conversation becomes a saved trip.",
              "The live board updates from the same draft the chat uses.",
              "Your brochure and trip history stay attached to your account.",
              "This auth flow uses the Supabase setup already wired into the app.",
            ].map((item) => (
              <div
                key={item}
                className="rounded-[1.5rem] border border-panel-border bg-background px-4 py-4 text-sm leading-7 text-foreground/75"
              >
                {item}
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-[2rem] border border-panel-border bg-panel p-8 shadow-[0_24px_80px_rgba(86,50,21,0.18)] backdrop-blur md:p-10">
          <div className="flex items-center gap-2 rounded-full border border-panel-border bg-background p-1">
            <ModeButton
              active={mode === "signin"}
              label="Sign in"
              onClick={() => setMode("signin")}
            />
            <ModeButton
              active={mode === "signup"}
              label="Create account"
              onClick={() => setMode("signup")}
            />
          </div>

          <form className="mt-6 grid gap-4" onSubmit={handleSubmit}>
            <label className="grid gap-2 text-sm text-foreground/80">
              Email
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="rounded-[1.25rem] border border-panel-border bg-background px-4 py-3 text-foreground outline-none transition focus:border-accent"
                placeholder="you@example.com"
                required
              />
            </label>

            <label className="grid gap-2 text-sm text-foreground/80">
              Password
              <input
                type="password"
                autoComplete={mode === "signin" ? "current-password" : "new-password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="rounded-[1.25rem] border border-panel-border bg-background px-4 py-3 text-foreground outline-none transition focus:border-accent"
                placeholder="Enter your password"
                required
                minLength={6}
              />
            </label>

            {message && (
              <p className="rounded-[1.25rem] border border-panel-border bg-background px-4 py-3 text-sm leading-7 text-foreground/80">
                {message}
              </p>
            )}

            {error && (
              <p className="rounded-[1.25rem] border border-panel-border bg-background px-4 py-3 text-sm leading-7 text-foreground/80">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-3 font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-70"
            >
              {isLoading
                ? mode === "signin"
                  ? "Signing in..."
                  : "Creating account..."
                : mode === "signin"
                  ? "Sign in"
                  : "Create account"}
            </button>
          </form>

          <div className="mt-6 flex items-center justify-between gap-4 text-sm text-foreground/70">
            <p>
              {mode === "signin"
                ? "Need an account? Switch to create account."
                : "Already have an account? Switch back to sign in."}
            </p>
            <Link className="font-semibold text-accent-strong" href="/">
              Back home
            </Link>
          </div>
        </section>
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
      className={`flex-1 rounded-full px-4 py-2 text-sm font-semibold transition ${
        active
          ? "bg-accent text-white"
          : "text-foreground/70 hover:bg-panel"
      }`}
    >
      {label}
    </button>
  );
}
