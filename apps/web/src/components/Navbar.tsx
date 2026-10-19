import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-lg font-bold text-brand-600">
          LightEd
        </Link>
        <div className="flex items-center gap-4 text-sm">
          <Link href="/dashboard" className="hover:text-brand-600">
            Dashboard
          </Link>
          <Link href="/dashboard/teacher" className="hover:text-brand-600">
            Teacher
          </Link>
          <Link
            href="/login"
            className="rounded-lg bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700"
          >
            Log in
          </Link>
        </div>
      </div>
    </nav>
  );
}
