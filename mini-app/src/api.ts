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

export interface Exercise {
  id: number;
  name: string;
  unit: string;
  media_type: string | null;
  media_url: string | null;
  media_file_unique_id: string | null;
}

export interface MediaInfo {
  media_type: string | null;
  media_url: string | null;
  media_file_unique_id: string | null;
}

export interface WorkoutTemplateItem {
  exercise_id: number;
  position: number;
  sets: number;
  target_reps: number | null;
  target_weight: number | null;
  target_seconds: number | null;
}

export interface WorkoutTemplate {
  id: number;
  name: string;
  items: WorkoutTemplateItem[];
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

  createGroup(
    name: string,
    type: "group" | "personal",
  ): Promise<{ id: number; name: string; type: string; active_member_count: number }> {
    return this.request("POST", "/api/groups", { name, type });
  }

  sendBroadcast(groupId: number, text: string): Promise<{ recipient_count: number }> {
    return this.request("POST", `/api/groups/${groupId}/broadcast`, { text });
  }

  createInvite(groupId: number): Promise<{ token: string; url: string; expires_at: string }> {
    return this.request("POST", `/api/groups/${groupId}/invites`);
  }

  listExercises(): Promise<Array<Exercise>> {
    return this.request("GET", "/api/exercises");
  }

  createExercise(name: string, unit: "reps" | "seconds" | "meters" | "kg"): Promise<Exercise> {
    return this.request("POST", "/api/exercises", { name, unit });
  }

  updateExercise(
    id: number,
    patch: { name?: string; unit?: "reps" | "seconds" | "meters" | "kg" },
  ): Promise<Exercise> {
    return this.request("PATCH", `/api/exercises/${id}`, patch);
  }

  clearExerciseMedia(exerciseId: number): Promise<MediaInfo> {
    return this.request("DELETE", `/api/exercises/${exerciseId}/media`);
  }

  async uploadExerciseMedia(exerciseId: number, file: File): Promise<MediaInfo> {
    const form = new FormData();
    form.append("file", file);
    // No Content-Type header — the browser sets the multipart boundary.
    const response = await fetch(`${API_BASE}/media/exercise/${exerciseId}`, {
      method: "POST",
      headers: { "X-Telegram-Init-Data": this.initData },
      body: form,
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
    return (await response.json()) as MediaInfo;
  }

  attachExerciseLink(exerciseId: number, url: string): Promise<MediaInfo> {
    return this.request("POST", `/api/exercises/${exerciseId}/media/link`, { url });
  }

  sendExerciseMedia(exerciseId: number): Promise<{ ok: boolean }> {
    return this.request("POST", `/api/exercises/${exerciseId}/media/send`);
  }

  mediaFileUrl(fileUniqueId: string): string {
    return `${API_BASE}/media/file/${fileUniqueId}`;
  }

  listWorkoutTemplates(): Promise<Array<WorkoutTemplate>> {
    return this.request("GET", "/api/workouts");
  }

  createWorkoutTemplate(
    name: string,
    items: Array<{
      exercise_id: number;
      sets: number;
      target_reps?: number;
      target_weight?: number;
      target_seconds?: number;
    }>,
  ): Promise<{ id: number; name: string }> {
    return this.request("POST", "/api/workouts", { name, items });
  }

  updateWorkoutTemplate(
    id: number,
    name: string,
    items: Array<{
      exercise_id: number;
      sets: number;
      target_reps?: number;
      target_weight?: number;
      target_seconds?: number;
    }>,
  ): Promise<{ id: number; name: string }> {
    return this.request("PUT", `/api/workouts/${id}`, { name, items });
  }

  createSession(body: {
    group_id: number;
    workout_template_id?: number;
    scheduled_at: string;
    duration_min: number;
    recurrence_rule?: string;
  }): Promise<
    Array<{
      id: number;
      group_id: number;
      scheduled_at: string;
      duration_min: number;
      status: string;
      recurrence_rule: string | null;
    }>
  > {
    return this.request("POST", "/api/sessions", body);
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
