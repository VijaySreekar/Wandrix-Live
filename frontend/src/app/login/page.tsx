import { redirect } from "next/navigation";

type LoginPageProps = {
  searchParams: Promise<{
    next?: string;
  }>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const params = await searchParams;
  const nextPath =
    params.next && params.next.startsWith("/") ? params.next : "/chat";

  redirect(`/auth?next=${encodeURIComponent(nextPath)}`);
}
