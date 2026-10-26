import AppShell from "@/components/layout/AppShell";

/** Every page inside (app) requires a signed-in user. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
