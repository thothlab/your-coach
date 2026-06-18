import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi, User } from "../api";

interface Props {
  api: TrainBeatApi;
  user: User;
  sessionId: number;
  onBack: () => void;
}

interface LogRow {
  id: number;
  session_id: number;
  athlete_id: number;
  exercise_id: number;
  set_index: number;
  actual_reps: number | null;
  actual_weight: number | null;
  actual_seconds: number | null;
  note: string | null;
}

export const SessionDetail: Component<Props> = (props) => {
  const [logs, { refetch }] = createResource<LogRow[]>(
    () => props.api.getSessionLog(props.sessionId) as unknown as Promise<LogRow[]>,
  );
  const [openExerciseId, setOpenExerciseId] = createSignal<number | null>(null);
  const [reps, setReps] = createSignal<string>("");
  const [weight, setWeight] = createSignal<string>("");
  const [saving, setSaving] = createSignal(false);

  function uniqueExercises(): number[] {
    const set = new Set<number>();
    for (const log of logs() ?? []) set.add(log.exercise_id);
    return [...set];
  }

  async function saveSet(exerciseId: number) {
    const ownLogs = (logs() ?? []).filter(
      (l) => l.exercise_id === exerciseId && l.athlete_id === props.user.id,
    );
    const nextIndex = ownLogs.length + 1;
    setSaving(true);
    try {
      await props.api.appendLog(props.sessionId, {
        exercise_id: exerciseId,
        set_index: nextIndex,
        actual_reps: reps() ? Number(reps()) : undefined,
        actual_weight: weight() ? Number(weight()) : undefined,
      });
      setOpenExerciseId(null);
      setReps("");
      setWeight("");
      refetch();
    } finally {
      setSaving(false);
    }
  }

  return (
    <main class="page">
      <button type="button" onClick={props.onBack}>
        ← back
      </button>
      <h1>Session #{props.sessionId}</h1>

      <Show when={props.user.role === "athlete"}>
        <section>
          <h2>Confirm attendance</h2>
          <div>
            <button
              type="button"
              onClick={() => props.api.setAttendance(props.sessionId, "confirmed")}
            >
              Confirm
            </button>{" "}
            <button
              type="button"
              onClick={() => props.api.setAttendance(props.sessionId, "declined")}
            >
              Decline
            </button>
          </div>
        </section>
      </Show>

      <section>
        <h2>Sets</h2>
        <Show when={logs.loading}>Loading…</Show>
        <Show when={!logs.loading && (logs()?.length ?? 0) === 0 && uniqueExercises().length === 0}>
          <p>No sets logged yet.</p>
        </Show>

        <For each={uniqueExercises()}>
          {(exerciseId) => (
            <div>
              <h3>Exercise #{exerciseId}</h3>
              <ul>
                <For each={(logs() ?? []).filter((l) => l.exercise_id === exerciseId)}>
                  {(log) => (
                    <li>
                      set {log.set_index} · athlete #{log.athlete_id}
                      <Show when={log.actual_reps != null}> · {log.actual_reps} reps</Show>
                      <Show when={log.actual_weight != null}> · {log.actual_weight} kg</Show>
                      <Show when={log.actual_seconds != null}> · {log.actual_seconds} s</Show>
                    </li>
                  )}
                </For>
              </ul>
              <Show when={props.user.role === "athlete"}>
                <Show
                  when={openExerciseId() === exerciseId}
                  fallback={
                    <button type="button" onClick={() => setOpenExerciseId(exerciseId)}>
                      Add set
                    </button>
                  }
                >
                  <div>
                    <input
                      type="number"
                      placeholder="reps"
                      value={reps()}
                      onInput={(e) => setReps(e.currentTarget.value)}
                    />{" "}
                    <input
                      type="number"
                      placeholder="kg"
                      value={weight()}
                      onInput={(e) => setWeight(e.currentTarget.value)}
                    />{" "}
                    <button type="button" disabled={saving()} onClick={() => saveSet(exerciseId)}>
                      Save
                    </button>
                  </div>
                </Show>
              </Show>
            </div>
          )}
        </For>

        <Show when={props.user.role === "athlete" && uniqueExercises().length === 0}>
          <button
            type="button"
            onClick={() => {
              const id = Number(prompt("Exercise id?") ?? 0);
              if (id) setOpenExerciseId(id);
            }}
          >
            Log a set by exercise id
          </button>
          <Show when={openExerciseId() !== null}>
            <div>
              <input
                type="number"
                placeholder="reps"
                value={reps()}
                onInput={(e) => setReps(e.currentTarget.value)}
              />{" "}
              <input
                type="number"
                placeholder="kg"
                value={weight()}
                onInput={(e) => setWeight(e.currentTarget.value)}
              />{" "}
              <button
                type="button"
                disabled={saving()}
                onClick={() => saveSet(openExerciseId() as number)}
              >
                Save
              </button>
            </div>
          </Show>
        </Show>
      </section>
    </main>
  );
};
