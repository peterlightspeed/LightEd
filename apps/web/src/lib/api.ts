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

type Options = Omit<RequestInit, "body"> & { body?: unknown; auth?: boolean; retry?: boolean };

export const NETWORK_MESSAGE =
  "Can't reach the server right now. It may be waking up (free hosting can take up to a minute) — please try again shortly.";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * fetch() that survives a cold-starting backend: on a network-level failure
 * (TypeError — no response at all) we retry a couple of times before giving up.
 * Only used for idempotent calls (GETs, login, google) — never for register.
 */
async function fetchWithRetry(url: string, init: RequestInit, retry: boolean): Promise<Response> {
  const attempts = retry ? 3 : 1;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fetch(url, init);
    } catch {
      if (i === attempts - 1) throw new ApiError(NETWORK_MESSAGE, 0);
      await sleep(3000);
    }
  }
  throw new ApiError(NETWORK_MESSAGE, 0); // unreachable, keeps TS happy
}

export async function apiFetch<T>(path: string, options: Options = {}): Promise<T> {
  const { body, auth = true, headers, retry, ...rest } = options;
  const isGet = !rest.method || rest.method === "GET";
  const token = auth ? getToken() : null;

  const res = await fetchWithRetry(`${API_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  }, retry ?? isGet);

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
  post: <T>(path: string, body?: unknown, auth = true, retry = false) =>
    apiFetch<T>(path, { method: "POST", body, auth, retry }),
  patch: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "PATCH", body }),
};
