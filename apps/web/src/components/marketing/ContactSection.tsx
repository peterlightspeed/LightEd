import { Mail, Phone } from "lucide-react";

import { SUPPORT_EMAIL, SUPPORT_PHONE_DISPLAY, SUPPORT_PHONE_TEL } from "@/lib/site";

/** Landing-page contact band (id="contact" is linked from the nav). */
export default function ContactSection() {
  return (
    <section id="contact" className="container-page scroll-mt-24 pb-20">
      <div className="rounded-3xl bg-navy-700 px-6 py-12 text-center sm:px-12">
        <h2 className="font-display text-3xl font-extrabold text-white">Questions? Talk to us</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-white/70">
          Whether you are a student, a teacher or a school that wants to try LightEd, our support team is happy to help.
        </p>
        <div className="mx-auto mt-8 grid max-w-2xl gap-4 sm:grid-cols-2">
          <a
            href={`mailto:${SUPPORT_EMAIL}`}
            className="flex items-center justify-center gap-3 rounded-2xl bg-white/10 px-5 py-4 text-left text-white transition hover:bg-white/20"
          >
            <Mail className="h-5 w-5 shrink-0 text-gold-300" />
            <span className="min-w-0">
              <span className="block text-[11px] font-bold uppercase tracking-wider text-white/60">Email</span>
              <span className="block truncate text-sm font-semibold">{SUPPORT_EMAIL}</span>
            </span>
          </a>
          <a
            href={`tel:${SUPPORT_PHONE_TEL}`}
            className="flex items-center justify-center gap-3 rounded-2xl bg-white/10 px-5 py-4 text-left text-white transition hover:bg-white/20"
          >
            <Phone className="h-5 w-5 shrink-0 text-gold-300" />
            <span>
              <span className="block text-[11px] font-bold uppercase tracking-wider text-white/60">Call / WhatsApp</span>
              <span className="block text-sm font-semibold">{SUPPORT_PHONE_DISPLAY}</span>
            </span>
          </a>
        </div>
      </div>
    </section>
  );
}
