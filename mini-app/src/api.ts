// Empty default → fetch hits same origin as the served Mini-App. In production
// this is https://trainbeat.devipad.ru/api/...; in dev set VITE_API_BASE to
// the local FastAPI URL (e.g. http://localhost:8000) when serving Vite separately.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export interface User {
  id: number;
  telegram_id: number;
  name: string;
  role: "trainer" | "athlete";
}

export interface AuthResponse {
  user_id: number;
  telegram_id: number;
  name: string;
  role: "trainer" | "athlete";
}

export interface ApiError {
  status: number;
  detail: string;
}

export class TrainBeatApi {
  constructor(private readonly initData: string) {}

  private async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": this.initData,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const json = await response.json();
        if (typeof json?.detail === "string") detail = json.detail;
      } catch {
        // ignore
      }
      throw { status: response.status, detail } satisfies ApiError;
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  authenticate(): Promise<AuthResponse> {
    return this.request<AuthResponse>("POST", "/api/auth/telegram");
  }

  me(): Promise<User> {
    return this.request<User>("GET", "/api/me");
  }

  listGroups(): Promise<
    Array<{ id: number; name: string; type: string; active_member_count: number }>
  > {
    return this.request("GET", "/api/groups");
  }

  listSessions(
    from: string,
    to: string,
  ): Promise<
    Array<{
      id: number;
      group_id: number;
      scheduled_at: string;
      duration_min: number;
      status: string;
      recurrence_rule: string | null;
    }>
  > {
    const params = new URLSearchParams({ from, to });
    return this.request("GET", `/api/sessions?${params}`);
  }

  setAttendance(sessionId: number, status: "confirmed" | "declined"): Promise<{ status: string }> {
    return this.request("POST", `/api/sessions/${sessionId}/attendance`, { status });
  }

  appendLog(
    sessionId: number,
    body: {
      exercise_id: number;
      set_index: number;
      actual_reps?: number;
      actual_weight?: number;
      actual_seconds?: number;
      note?: string;
    },
  ): Promise<unknown> {
    return this.request("POST", `/api/sessions/${sessionId}/log`, body);
  }

  getSessionLog(sessionId: number): Promise<
    Array<{
      id: number;
      session_id: number;
      athlete_id: number;
      exercise_id: number;
      set_index: number;
      actual_reps: number | null;
      actual_weight: number | null;
      actual_seconds: number | null;
      note: string | null;
    }>
  > {
    return this.request("GET", `/api/sessions/${sessionId}/log`);
  }
}
