import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi, User } from "../api";
import { t } from "../lib/i18n";

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
      <button type="button" class="back" onClick={props.onBack}>
        {t("common.back")}
      </button>
      <h1>{t("session.title", { id: props.sessionId })}</h1>

      <Show when={props.user.role === "athlete"}>
        <section>
          <h2>{t("session.confirmAttendance")}</h2>
          <div>
            <button
              type="button"
              onClick={() => props.api.setAttendance(props.sessionId, "confirmed")}
            >
              {t("common.confirm")}
            </button>{" "}
            <button
              type="button"
              onClick={() => props.api.setAttendance(props.sessionId, "declined")}
            >
              {t("common.decline")}
            </button>
          </div>
        </section>
      </Show>

      <section>
        <h2>{t("session.sets")}</h2>
        <Show when={logs.loading}>{t("common.loading")}</Show>
        <Show when={!logs.loading && (logs()?.length ?? 0) === 0 && uniqueExercises().length === 0}>
          <p>{t("session.noSets")}</p>
        </Show>

        <For each={uniqueExercises()}>
          {(exerciseId) => (
            <div>
              <h3>{t("session.exerciseTitle", { id: exerciseId })}</h3>
              <ul>
                <For each={(logs() ?? []).filter((l) => l.exercise_id === exerciseId)}>
                  {(log) => (
                    <li>
                      {t("session.setLine", { n: log.set_index, id: log.athlete_id })}
                      <Show when={log.actual_reps != null}>
                        {t("session.repsSuffix", { reps: log.actual_reps ?? 0 })}
                      </Show>
                      <Show when={log.actual_weight != null}>
                        {t("session.weightSuffix", { weight: log.actual_weight ?? 0 })}
                      </Show>
                      <Show when={log.actual_seconds != null}>
                        {t("session.secondsSuffix", { seconds: log.actual_seconds ?? 0 })}
                      </Show>
                    </li>
                  )}
                </For>
              </ul>
              <Show when={props.user.role === "athlete"}>
                <Show
                  when={openExerciseId() === exerciseId}
                  fallback={
                    <button type="button" onClick={() => setOpenExerciseId(exerciseId)}>
                      {t("session.addSet")}
                    </button>
                  }
                >
                  <div>
                    <input
                      type="number"
                      placeholder={t("placeholder.reps")}
                      value={reps()}
                      onInput={(e) => setReps(e.currentTarget.value)}
                    />{" "}
                    <input
                      type="number"
                      placeholder={t("placeholder.kg")}
                      value={weight()}
                      onInput={(e) => setWeight(e.currentTarget.value)}
                    />{" "}
                    <button type="button" disabled={saving()} onClick={() => saveSet(exerciseId)}>
                      {t("common.save")}
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
              const id = Number(prompt(t("session.promptExerciseId")) ?? 0);
              if (id) setOpenExerciseId(id);
            }}
          >
            {t("session.logByExerciseId")}
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
                {t("common.save")}
              </button>
            </div>
          </Show>
        </Show>
      </section>
    </main>
  );
};
