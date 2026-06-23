import { type Component, Show, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onCreated: () => void;
}

type Unit = "reps" | "seconds" | "meters" | "kg";

export const ExerciseCreate: Component<Props> = (props) => {
  const [name, setName] = createSignal("");
  const [unit, setUnit] = createSignal<Unit>("kg");
  const [file, setFile] = createSignal<File | null>(null);
  const [link, setLink] = createSignal("");
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  async function submit(): Promise<void> {
    setError(null);
    if (!name().trim()) {
      setError(t("validation.nameRequired"));
      return;
    }
    setSubmitting(true);
    try {
      const ex = await props.api.createExercise(name().trim(), unit());
      const picked = file();
      if (picked) {
        await props.api.uploadExerciseMedia(ex.id, picked);
      } else if (link().trim()) {
        await props.api.attachExerciseLink(ex.id, link().trim());
      }
      props.onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title={t("exercises.newTitle")}
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label={t("field.name")}>
        <input
          type="text"
          value={name()}
          onInput={(e) => setName(e.currentTarget.value)}
          placeholder={t("placeholder.exerciseName")}
        />
      </Field>
      <Field label={t("field.unit")}>
        <select value={unit()} onChange={(e) => setUnit(e.currentTarget.value as Unit)}>
          <option value="kg">{t("unit.kg")}</option>
          <option value="reps">{t("unit.reps")}</option>
          <option value="seconds">{t("unit.seconds")}</option>
          <option value="meters">{t("unit.meters")}</option>
        </select>
      </Field>
      <Field label={t("exercise.mediaFile")}>
        <input
          type="file"
          accept="image/*,video/*"
          onChange={(e) => setFile(e.currentTarget.files?.[0] ?? null)}
        />
      </Field>
      <Show when={!file()}>
        <Field label={t("exercise.mediaLink")}>
          <input
            type="url"
            value={link()}
            onInput={(e) => setLink(e.currentTarget.value)}
            placeholder="https://…"
          />
        </Field>
      </Show>
    </FormShell>
  );
};
