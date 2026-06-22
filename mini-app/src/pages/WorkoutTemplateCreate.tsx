import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onCreated: () => void;
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

export const WorkoutTemplateCreate: Component<Props> = (props) => {
  const [exercises] = createResource(() => props.api.listExercises());
  const [name, setName] = createSignal("");
  const [items, setItems] = createSignal<ItemDraft[]>([emptyItem()]);
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  function unitOf(id: number | null): string | undefined {
    if (id == null) return undefined;
    return exercises()?.find((e) => e.id === id)?.unit;
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
      await props.api.createWorkoutTemplate(
        name().trim(),
        drafts.map((it) => ({
          exercise_id: it.exercise_id as number,
          sets: it.sets,
          target_reps: it.target_reps ?? undefined,
          target_weight: it.target_weight ?? undefined,
          target_seconds: it.target_seconds ?? undefined,
        })),
      );
      props.onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title={t("workouts.newTitle")}
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
        <For each={items()}>
          {(item, index) => {
            const unit = () => unitOf(item.exercise_id);
            return (
              <div style={{ "border-bottom": "1px solid #ccc", padding: "8px 0" }}>
                <Field label={t("workouts.itemExercise", { n: index() + 1 })}>
                  <select
                    value={item.exercise_id ?? ""}
                    onChange={(e) =>
                      updateItem(index(), {
                        exercise_id: e.currentTarget.value ? Number(e.currentTarget.value) : null,
                      })
                    }
                  >
                    <option value="">{t("common.pick")}</option>
                    <For each={exercises()}>
                      {(ex) => (
                        <option value={ex.id}>
                          {ex.name} ({ex.unit})
                        </option>
                      )}
                    </For>
                  </select>
                </Field>
                <Field label={t("field.sets")}>
                  <input
                    type="number"
                    min="1"
                    max="99"
                    value={item.sets}
                    onInput={(e) => updateItem(index(), { sets: Number(e.currentTarget.value) })}
                  />
                </Field>
                <Show when={unit() === "reps" || unit() === "kg" || unit() === "meters"}>
                  <Field label={t("field.targetReps")}>
                    <input
                      type="number"
                      min="1"
                      value={item.target_reps ?? ""}
                      onInput={(e) =>
                        updateItem(index(), {
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
                      value={item.target_weight ?? ""}
                      onInput={(e) =>
                        updateItem(index(), {
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
                      value={item.target_seconds ?? ""}
                      onInput={(e) =>
                        updateItem(index(), {
                          target_seconds: e.currentTarget.value
                            ? Number(e.currentTarget.value)
                            : null,
                        })
                      }
                    />
                  </Field>
                </Show>
                <Show when={items().length > 1}>
                  <button type="button" onClick={() => removeItem(index())}>
                    {t("workouts.removeItem")}
                  </button>
                </Show>
              </div>
            );
          }}
        </For>
        <button type="button" onClick={() => setItems((p) => [...p, emptyItem()])}>
          {t("workouts.addItem")}
        </button>
      </Show>
    </FormShell>
  );
};
