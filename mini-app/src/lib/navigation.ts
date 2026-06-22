export type Page =
  | { kind: "home" }
  | { kind: "group-new" }
  | { kind: "exercises" }
  | { kind: "exercise-new" }
  | { kind: "workouts" }
  | { kind: "workout-new" }
  | { kind: "session-new" }
  | { kind: "broadcast" }
  | { kind: "invite"; groupId: number; groupName: string }
  | { kind: "session-detail"; sessionId: number };

export type Navigate = (page: Page) => void;
