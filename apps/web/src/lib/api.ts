/**
 * Tiny typed fetch wrapper.
 *
 * - Reads the JWT from localStorage on every request (client only).
 * - Normalises FastAPI error payloads into a readable `ApiError`.
 * - Uses NEXT_PUBLIC_API_URL so the same build works locally and on Render.
 */
import { clearSession, getToken } from "./auth";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

type Options = Omit<RequestInit, "body"> & { body?: unknown; auth?: boolean };

export async function apiFetch<T>(path: string, options: Options = {}): Promise<T> {
  const { body, auth = true, headers, ...rest } = options;
  const token = auth ? getToken() : null;

  const res = await fetch(`${API_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });

  if (res.status === 401 && auth) {
    // Expired/invalid token: drop it so the app shell can redirect to login.
    clearSession();
  }

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
      else if (Array.isArray(data.detail)) message = data.detail[0]?.msg ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, res.status);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Convenience helpers used across pages. */
export const api = {
  get: <T>(path: string, auth = true) => apiFetch<T>(path, { auth }),
  post: <T>(path: string, body?: unknown, auth = true) =>
    apiFetch<T>(path, { method: "POST", body, auth }),
  patch: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "PATCH", body }),
};
