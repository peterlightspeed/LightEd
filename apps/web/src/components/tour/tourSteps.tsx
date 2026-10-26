import { SUPPORT_EMAIL, SUPPORT_PHONE_DISPLAY, SUPPORT_PHONE_TEL } from "@/lib/site";
import type { Role } from "@/types";
import type { TourStep } from "./ProductTour";

/** Role-specific tour content. Targets map to data-tour attributes in AppShell. */
export function getTourSteps(role: Role, firstName: string): TourStep[] {
  const menu = ["nav", "menu-btn"]; // on phones the sidebar is hidden, so point at ☰

  const overview: Record<Role, string> = {
    student: "Your home base: what to continue, your quiz average, and the topics that need practice.",
    teacher: "See class averages, which students are at risk, and how each course is doing.",
    admin: "Platform-wide numbers and the list of all users, at a glance.",
  };

  const steps: TourStep[] = [
    {
      title: `Welcome to LightEd, ${firstName}! 👋`,
      body: "Take a 30-second tour so you know where everything is. You can skip anytime and replay it from the ? button.",
    },
    {
      target: menu,
      title: "Your menu",
      body: (
        <>
          Everything for your <b>{role}</b> workspace lives here. {" "}
          <span className="text-xs">(On a phone, tap the ☰ button.)</span>
        </>
      ),
    },
    { target: ["nav-overview", "menu-btn"], title: "Overview", body: overview[role] },
    {
      target: ["nav-courses", "menu-btn"],
      title: "Courses",
      body:
        role === "student"
          ? "Browse courses, enroll, then open lessons and take quizzes to build your progress."
          : "See all courses, their lessons and how students are engaging with them.",
    },
  ];

  if (role === "student") {
    steps.push({
      target: ["nav-progress", "menu-btn"],
      title: "Progress",
      body: "Charts of your quiz scores and strongest/weakest topics — so you know exactly what to practise.",
    });
  }

  steps.push(
    {
      target: ["ai-tutor", "menu-btn"],
      title: "AI Tutor",
      body: "Stuck on something? Ask the AI tutor for a clear, step-by-step explanation.",
    },
    {
      target: "search",
      title: "Search",
      body: "Jump straight to a course or lesson. Press Enter to search.",
    },
    {
      target: "user-menu",
      title: "Your account",
      body: "Open your dashboard, replay this tour, get support, or log out from here.",
    },
    {
      title: "Need help? We're here",
      body: (
        <>
          Email{" "}
          <a className="font-semibold text-brand-600" href={`mailto:${SUPPORT_EMAIL}`}>
            {SUPPORT_EMAIL}
          </a>{" "}
          or call{" "}
          <a className="font-semibold text-brand-600" href={`tel:${SUPPORT_PHONE_TEL}`}>
            {SUPPORT_PHONE_DISPLAY}
          </a>
          . Happy learning!
        </>
      ),
    }
  );
  return steps;
}
