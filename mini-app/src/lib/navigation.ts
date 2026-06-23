import type { Exercise, WorkoutTemplate } from "../api";

export type Page =
  | { kind: "home" }
  | { kind: "group-new" }
  | { kind: "exercises" }
  | { kind: "exercise-new" }
  | { kind: "exercise-edit"; exercise: Exercise }
  | { kind: "workouts" }
  | { kind: "workout-new" }
  | { kind: "workout-edit"; template: WorkoutTemplate }
  | { kind: "session-new" }
  | { kind: "broadcast" }
  | { kind: "invite"; groupId: number; groupName: string }
  | { kind: "session-detail"; sessionId: number };

export type Navigate = (page: Page) => void;
