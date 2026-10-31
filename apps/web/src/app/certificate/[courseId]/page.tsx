"use client";

/** Printable course-completion certificate. "Save as PDF" in the print dialog gives the student a file. */
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Award, ArrowLeft, Printer } from "lucide-react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface Cert {
  certificate_id: string;
  student_name: string;
  course_title: string;
  teacher_name: string;
  completed_on: string;
  avg_score: number | null;
  lessons_completed: number;
}

export default function CertificatePage() {
  const { courseId } = useParams<{ courseId: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [cert, setCert] = useState<Cert | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api
      .get<Cert>(`/courses/${courseId}/certificate`)
      .then(setCert)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load your certificate."));
  }, [courseId, user, loading, router]);

  const date = cert ? new Date(cert.completed_on).toLocaleDateString(undefined, { day: "numeric", month: "long", year: "numeric" }) : "";

  return (
    <main className="min-h-screen bg-mist px-4 py-6 print:bg-white print:p-0">
      <style>{`@page { size: A4 landscape; margin: 0 } @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact } }`}</style>
      <div className="mx-auto mb-4 flex max-w-4xl items-center justify-between gap-3 print:hidden">
        <Link href={`/courses/${courseId}`} className="inline-flex min-h-[44px] items-center gap-2 text-sm font-semibold text-navy-700">
          <ArrowLeft className="h-4 w-4" /> Back to course
        </Link>
        {cert && (
          <button onClick={() => window.print()} className="inline-flex min-h-[44px] items-center gap-2 rounded-2xl bg-brand-600 px-5 text-sm font-semibold text-white hover:bg-brand-700">
            <Printer className="h-4 w-4" /> Print / Save as PDF
          </button>
        )}
      </div>

      {error && (
        <div className="mx-auto max-w-md rounded-3xl border border-line bg-white p-6 text-center">
          <p className="font-display text-lg font-bold text-ink">Certificate not available yet</p>
          <p className="mt-2 text-sm text-muted">{error}</p>
        </div>
      )}
      {!cert && !error && <p className="py-20 text-center text-sm text-muted">Preparing your certificate…</p>}

      {cert && (
        <section className="mx-auto w-full max-w-4xl sm:aspect-[1.414/1] print:aspect-[1.414/1] rounded-3xl border-[10px] border-double border-[#c9a24b] bg-white p-6 text-center shadow-lg print:max-w-none print:rounded-none print:shadow-none sm:p-12">
          <div className="flex h-full flex-col items-center justify-between gap-6 sm:gap-0">
            <div>
              <Award className="mx-auto h-10 w-10 text-[#c9a24b] sm:h-14 sm:w-14" />
              <p className="mt-2 text-xs font-bold uppercase tracking-[0.3em] text-brand-600 sm:text-sm">LightEd</p>
              <h1 className="mt-2 font-display text-2xl font-extrabold text-ink sm:mt-4 sm:text-5xl">Certificate of Completion</h1>
            </div>
            <div>
              <p className="text-xs text-muted sm:text-base">This certifies that</p>
              <p className="mt-1 font-display text-2xl font-extrabold text-navy-700 sm:mt-3 sm:text-5xl">{cert.student_name}</p>
              <p className="mt-2 text-xs text-muted sm:mt-4 sm:text-base">has successfully completed all {cert.lessons_completed} lessons of</p>
              <p className="mt-1 font-display text-lg font-bold text-ink sm:mt-2 sm:text-3xl">{cert.course_title}</p>
              {cert.avg_score !== null && <p className="mt-1 text-xs text-muted sm:mt-2 sm:text-sm">Average quiz score: {cert.avg_score}%</p>}
            </div>
            <div className="grid w-full grid-cols-3 items-end gap-2 text-[10px] text-muted sm:text-sm">
              <div><p className="border-t border-line pt-1 font-semibold text-ink">{date}</p>Date completed</div>
              <div className="font-mono text-[9px] sm:text-xs">ID {cert.certificate_id}</div>
              <div><p className="border-t border-line pt-1 font-semibold text-ink">{cert.teacher_name}</p>Instructor</div>
            </div>
          </div>
        </section>
      )}
      {cert && <p className="mx-auto mt-4 max-w-4xl text-center text-xs text-muted print:hidden">Anyone can confirm this certificate is genuine using its ID.</p>}
    </main>
  );
}
