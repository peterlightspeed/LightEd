/** Shared API types. Mirrors the FastAPI Pydantic schemas. */

export type Role = "student" | "teacher" | "admin";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: Role;
  avatar_url?: string | null;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LessonSummary {
  id: number;
  title: string;
  summary: string;
  duration_minutes: number;
  order_index: number;
  completed: boolean;
  quiz_id: number | null;
}

export interface Topic {
  id: number;
  title: string;
  order_index: number;
  lessons: LessonSummary[];
}

export interface Course {
  id: number;
  title: string;
  description: string;
  subject: string;
  level: string;
  accent: string;
  owner_id: number;
  owner_name: string;
  lesson_count: number;
  topic_count: number;
  enrolled: boolean;
  progress: number;
}

export interface CourseDetail extends Course {
  topics: Topic[];
}

export interface LessonDetail {
  id: number;
  title: string;
  content: string;
  summary: string;
  duration_minutes: number;
  order_index: number;
  topic_id: number;
  topic_title: string;
  course_id: number;
  course_title: string;
  quiz_id: number | null;
  completed: boolean;
  next_lesson_id: number | null;
  prev_lesson_id: number | null;
}

export interface QuizQuestion {
  prompt: string;
  options: string[];
}

export interface Quiz {
  id: number;
  lesson_id: number;
  title: string;
  questions: QuizQuestion[];
}

export interface QuestionResult {
  prompt: string;
  selected: number | null;
  correct_index: number;
  is_correct: boolean;
  explanation: string;
}

export interface AttemptResult {
  id: number;
  quiz_id: number;
  score: number;
  correct_count: number;
  total: number;
  results: QuestionResult[];
  created_at: string;
}

export interface Attempt {
  id: number;
  quiz_id: number;
  quiz_title: string;
  lesson_title: string;
  course_title: string;
  score: number;
  created_at: string;
}

export interface StudentStats {
  enrolled_courses: number;
  lessons_completed: number;
  lessons_total: number;
  avg_score: number;
  streak_days: number;
}

export interface ContinueLearning {
  course_id: number;
  course_title: string;
  lesson_id: number;
  lesson_title: string;
  topic_title: string;
  progress: number;
}

export interface FocusArea {
  course_id: number;
  label: string;
  mastery: number;
}

export interface Recommendation {
  course_id: number;
  title: string;
  subject: string;
  level: string;
  accent: string;
  reason: string;
}

export interface StudentDashboard {
  user: User;
  stats: StudentStats;
  continue_learning: ContinueLearning | null;
  courses: (Course & { lessons_completed: number })[];
  focus_areas: FocusArea[];
  recommendations: Recommendation[];
  recent_attempts: Attempt[];
  weekly_activity: { day: string; lessons: number }[];
}

export interface TeacherDashboard {
  user: User;
  stats: {
    total_students: number;
    active_courses: number;
    avg_score: number;
    at_risk: number;
  };
  courses: {
    id: number;
    title: string;
    subject: string;
    accent: string;
    students: number;
    lessons: number;
    avg_progress: number;
  }[];
  students: {
    id: number;
    name: string;
    email: string;
    avg_score: number;
    lessons_completed: number;
    status: "at_risk" | "on_track";
  }[];
}

export interface AdminDashboard {
  stats: {
    users: number;
    students: number;
    teachers: number;
    courses: number;
    attempts: number;
  };
  users: User[];
  courses: { id: number; title: string; subject: string; published: boolean }[];
}

export interface ProgressData {
  lessons_completed: number;
  lessons_total: number;
  overall_progress: number;
  avg_score: number;
  streak_days: number;
  courses: {
    course_id: number;
    title: string;
    progress: number;
    lessons_completed: number;
    lessons_total: number;
  }[];
  recent_lessons: {
    lesson_id: number;
    title: string;
    course_title: string;
    completed: boolean;
    completed_at: string | null;
  }[];
}

/* ------------------------------------------------------------ v3: teacher / planner / audit */
export interface Risk {
  band: "low" | "medium" | "high";
  score: number;
  factors: string[];
}

export interface RosterStudent {
  id: number;
  name: string;
  email: string;
  courses: string[];
  avg_score: number | null;
  attempts: number;
  completion: number;
  lessons_completed: number;
  last_active: string | null;
  risk: Risk;
}

export interface StudentDetail extends RosterStudent {
  course_progress: {
    id: number;
    title: string;
    completion: number;
    lessons_completed: number;
    lessons_total: number;
    avg_score: number | null;
  }[];
  topic_scores: { topic_id: number; topic: string; course_id: number; score: number; attempts: number }[];
  recent_attempts: { id: number; lesson: string; quiz: string; score: number; created_at: string | null }[];
}

export interface PlanItem {
  lesson_id: number;
  title: string;
  topic: string;
  minutes: number;
  kind: "learn" | "revise";
  reason: string;
}

export interface StudyPlan {
  course: { id: number; title: string };
  exam_date: string;
  minutes_per_day: number;
  weak_topics: string[];
  total_minutes: number;
  unscheduled: number;
  days: { date: string; total_minutes: number; items: PlanItem[] }[];
}

export interface DraftQuestion {
  prompt: string;
  options: string[];
  answer_index: number;
  explanation?: string;
}

export interface AuditEntry {
  id: number;
  action: string;
  actor: string;
  detail: string;
  ip: string;
  created_at: string | null;
}
