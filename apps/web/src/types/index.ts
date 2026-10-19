export type Role = "student" | "teacher" | "admin";

export interface User {
  id: number;
  full_name: string;
  email: string;
  role: Role;
}

export interface Course {
  id: number;
  title: string;
  description: string;
  owner_id: number;
}

export interface Topic {
  id: number;
  course_id: number;
  title: string;
  order_index: number;
}

export interface Lesson {
  id: number;
  topic_id: number;
  title: string;
  content: string;
}

export interface Quiz {
  id: number;
  lesson_id: number;
  questions: QuizQuestion[];
}

export interface QuizQuestion {
  id: number;
  prompt: string;
  options: string[];
  answer_index: number;
}

export interface Attempt {
  id: number;
  quiz_id: number;
  user_id: number;
  score: number;
  created_at: string;
}
