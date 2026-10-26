import Link from "next/link";

import { Logo } from "@/components/ui";
import { SUPPORT_EMAIL, SUPPORT_PHONE_DISPLAY, SUPPORT_PHONE_TEL } from "@/lib/site";

export default function Footer() {
  return (
    <footer className="border-t border-line bg-white">
      <div className="container-page grid gap-10 py-14 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <Logo />
          <p className="mt-4 max-w-sm text-sm leading-6 text-muted">
            AI-assisted personalized learning for students and teachers. Built for the
            TechCrush Buildathon.
          </p>
        </div>
        <div>
          <h4 className="text-sm font-bold text-ink">Product</h4>
          <ul className="mt-4 space-y-2 text-sm text-muted">
            <li><a href="#features" className="hover:text-brand-600">Features</a></li>
            <li><a href="#how-it-works" className="hover:text-brand-600">How it works</a></li>
            <li><Link href="/register" className="hover:text-brand-600">Create account</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-bold text-ink">Contact</h4>
          <ul className="mt-4 space-y-2 text-sm text-muted">
            <li><a href={`mailto:${SUPPORT_EMAIL}`} className="break-all hover:text-brand-600">{SUPPORT_EMAIL}</a></li>
            <li><a href={`tel:${SUPPORT_PHONE_TEL}`} className="hover:text-brand-600">{SUPPORT_PHONE_DISPLAY}</a></li>
          </ul>
        </div>
        <div>
          <h4 className="text-sm font-bold text-ink">Account</h4>
          <ul className="mt-4 space-y-2 text-sm text-muted">
            <li><Link href="/login" className="hover:text-brand-600">Log in</Link></li>
            <li><Link href="/forgot-password" className="hover:text-brand-600">Reset password</Link></li>
            <li><Link href="/dashboard" className="hover:text-brand-600">Dashboard</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-line py-6">
        <p className="container-page text-xs text-muted">
          © {new Date().getFullYear()} LightEd. MVP build — design recreated from the Figma source.
        </p>
      </div>
    </footer>
  );
}
