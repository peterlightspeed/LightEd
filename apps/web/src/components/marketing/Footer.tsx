import Link from "next/link";
import { Mail, Phone } from "lucide-react";

import { Logo } from "@/components/ui";
import { SUPPORT_EMAIL, SUPPORT_PHONE_DISPLAY, SUPPORT_PHONE_TEL } from "@/lib/site";

/** Deep brand-navy footer: it closes the page with a clear contact prompt, then simple link columns. */
export default function Footer() {
  return (
    <footer className="bg-navy-900 text-white">
      <div className="h-1 bg-gradient-to-r from-brand-500 via-gold-400 to-brand-500" />
      <div className="container-page py-12 sm:py-14">
        {/* Contact prompt */}
        <div className="flex flex-col gap-6 border-b border-white/10 pb-10 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-md">
            <h2 className="font-display text-2xl font-extrabold">Questions? We&apos;re here to help.</h2>
            <p className="mt-2 text-sm leading-6 text-white/65">
              Students, teachers and schools: reach our support team any time.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className="inline-flex min-h-[48px] items-center gap-3 rounded-2xl bg-white/10 px-5 text-sm font-semibold transition hover:bg-white/20"
            >
              <Mail className="h-5 w-5 shrink-0 text-gold-300" />
              <span className="break-all">{SUPPORT_EMAIL}</span>
            </a>
            <a
              href={`tel:${SUPPORT_PHONE_TEL}`}
              className="inline-flex min-h-[48px] items-center gap-3 rounded-2xl bg-gold-400 px-5 text-sm font-bold text-navy-900 transition hover:bg-gold-300"
            >
              <Phone className="h-5 w-5 shrink-0" />
              {SUPPORT_PHONE_DISPLAY}
            </a>
          </div>
        </div>

        {/* Links */}
        <div className="grid gap-10 pt-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <Logo variant="light" />
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/60">
              AI-assisted personalized learning for students and teachers. Built for the TechCrush Buildathon.
            </p>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Get started</h3>
            <ul className="mt-4 space-y-2.5 text-sm text-white/65">
              <li><Link href="/register" className="hover:text-gold-300">Create account</Link></li>
              <li><Link href="/login" className="hover:text-gold-300">Log in</Link></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Help</h3>
            <ul className="mt-4 space-y-2.5 text-sm text-white/65">
              <li><Link href="/forgot-password" className="hover:text-gold-300">Reset password</Link></li>
              <li><a href={`mailto:${SUPPORT_EMAIL}`} className="hover:text-gold-300">Contact support</a></li>
            </ul>
          </div>
        </div>
      </div>
      <div className="border-t border-white/10 py-5">
        <p className="container-page text-xs text-white/45">© {new Date().getFullYear()} LightEd. All rights reserved.</p>
      </div>
    </footer>
  );
}
