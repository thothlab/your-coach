import { type Component, For, Index, Show, createResource, createSignal } from "solid-js";
import type { Exercise, TrainBeatApi, WorkoutTemplate } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onSaved: () => void;
  /** When set, the form edits this template instead of creating a new one. */
  template?: WorkoutTemplate;
}

interface ItemDraft {
  exercise_id: number | null;
  sets: number;
  target_reps: number | null;
  target_weight: number | null;
  target_seconds: number | null;
}

const emptyItem = (): ItemDraft => ({
  exercise_id: null,
  sets: 3,
  target_reps: null,
  target_weight: null,
  target_seconds: null,
});

function mediaIcon(ex: Exercise | undefined): string {
  switch (ex?.media_type) {
    case "photo":
      return "📷";
    case "video":
      return "🎥";
    case "link":
      return "🔗";
    default:
      return "";
  }
}

export const WorkoutTemplateCreate: Component<Props> = (props) => {
  const [exercises] = createResource(() => props.api.listExercises());
  const editing = (): WorkoutTemplate | undefined => props.template;
  const initialItems = (): ItemDraft[] => {
    const tpl = props.template;
    if (!tpl) return [emptyItem()];
    return tpl.items.map((it) => ({
      exercise_id: it.exercise_id,
      sets: it.sets,
      target_reps: it.target_reps,
      target_weight: it.target_weight,
      target_seconds: it.target_seconds,
    }));
  };
  const [name, setName] = createSignal(editing()?.name ?? "");
  const [items, setItems] = createSignal<ItemDraft[]>(initialItems());
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  function exerciseOf(id: number | null): Exercise | undefined {
    if (id == null) return undefined;
    return exercises()?.find((e) => e.id === id);
  }

  function unitOf(id: number | null): string | undefined {
    return exerciseOf(id)?.unit;
  }

  function updateItem(index: number, patch: Partial<ItemDraft>): void {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function removeItem(index: number): void {
    setItems((prev) => prev.filter((_, i) => i !== index));
  }

  async function submit(): Promise<void> {
    setError(null);
    if (!name().trim()) {
      setError(t("validation.nameRequired"));
      return;
    }
    const drafts = items();
    if (drafts.some((it) => it.exercise_id == null)) {
      setError(t("validation.pickExerciseEvery"));
      return;
    }
    setSubmitting(true);
    try {
      const payload = drafts.map((it) => ({
        exercise_id: it.exercise_id as number,
        sets: it.sets,
        target_reps: it.target_reps ?? undefined,
        target_weight: it.target_weight ?? undefined,
        target_seconds: it.target_seconds ?? undefined,
      }));
      const target = editing();
      if (target) {
        await props.api.updateWorkoutTemplate(target.id, name().trim(), payload);
      } else {
        await props.api.createWorkoutTemplate(name().trim(), payload);
      }
      props.onSaved();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title={editing() ? t("workouts.editTitle") : t("workouts.newTitle")}
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label={t("field.name")}>
        <input type="text" value={name()} onInput={(e) => setName(e.currentTarget.value)} />
      </Field>

      <Show when={!exercises.loading} fallback={<p>{t("workouts.loadingExercises")}</p>}>
        <h2>{t("workouts.items")}</h2>
        <p class="hint">{t("workouts.mediaHint")}</p>
        <Index each={items()}>
          {(item, index) => {
            const unit = () => unitOf(item().exercise_id);
            const picked = () => exerciseOf(item().exercise_id);
            return (
              <div style={{ "border-bottom": "1px solid #ccc", padding: "8px 0" }}>
                <Field label={t("workouts.itemExercise", { n: index + 1 })}>
                  <select
                    value={item().exercise_id ?? ""}
                    onChange={(e) =>
                      updateItem(index, {
                        exercise_id: e.currentTarget.value ? Number(e.currentTarget.value) : null,
                      })
                    }
                  >
                    <option value="">{t("common.pick")}</option>
                    <For each={exercises()}>
                      {(ex) => (
                        <option value={ex.id}>
                          {`${mediaIcon(ex)} ${ex.name} (${ex.unit})`.trim()}
                        </option>
                      )}
                    </For>
                  </select>
                </Field>
                <Show when={picked()?.media_type === "photo" && picked()?.media_file_unique_id}>
                  <img
                    src={props.api.mediaFileUrl(picked()?.media_file_unique_id ?? "")}
                    alt={picked()?.name}
                    style={{ "max-width": "100%", "border-radius": "10px", "margin-bottom": "8px" }}
                  />
                </Show>
                <Show when={picked()?.media_type === "video"}>
                  <p class="hint">🎥 {t("exercise.hasVideo")}</p>
                </Show>
                <Field label={t("field.sets")}>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    value={item().sets}
                    onInput={(e) => updateItem(index, { sets: Number(e.currentTarget.value) })}
                  />
                </Field>
                <Show when={unit() === "reps" || unit() === "kg" || unit() === "meters"}>
                  <Field label={t("field.targetReps")}>
                    <input
                      type="number"
                      min="1"
                      value={item().target_reps ?? ""}
                      onInput={(e) =>
                        updateItem(index, {
                          target_reps: e.currentTarget.value ? Number(e.currentTarget.value) : null,
                        })
                      }
                    />
                  </Field>
                </Show>
                <Show when={unit() === "kg"}>
                  <Field label={t("field.targetWeight")}>
                    <input
                      type="number"
                      min="0"
                      step="0.5"
                      value={item().target_weight ?? ""}
                      onInput={(e) =>
                        updateItem(index, {
                          target_weight: e.currentTarget.value
                            ? Number(e.currentTarget.value)
                            : null,
                        })
                      }
                    />
                  </Field>
                </Show>
                <Show when={unit() === "seconds" || unit() === "meters"}>
                  <Field label={t("field.targetSeconds")}>
                    <input
                      type="number"
                      min="1"
                      value={item().target_seconds ?? ""}
                      onInput={(e) =>
                        updateItem(index, {
                          target_seconds: e.currentTarget.value
                            ? Number(e.currentTarget.value)
                            : null,
                        })
                      }
                    />
                  </Field>
                </Show>
                <Show when={items().length > 1}>
                  <button type="button" onClick={() => removeItem(index)}>
                    {t("workouts.removeItem")}
                  </button>
                </Show>
              </div>
            );
          }}
        </Index>
        <button type="button" onClick={() => setItems((p) => [...p, emptyItem()])}>
          {t("workouts.addItem")}
        </button>
      </Show>
    </FormShell>
  );
};
