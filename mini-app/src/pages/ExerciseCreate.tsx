import { type Component, Show, createEffect, createSignal, onCleanup } from "solid-js";
import type { Exercise, TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onSaved: () => void;
  /** When set, the form edits this exercise instead of creating a new one. */
  exercise?: Exercise;
}

type Unit = "reps" | "seconds" | "meters" | "kg";

export const ExerciseCreate: Component<Props> = (props) => {
  const editing = (): Exercise | undefined => props.exercise;
  const [name, setName] = createSignal(editing()?.name ?? "");
  const [unit, setUnit] = createSignal<Unit>((editing()?.unit as Unit) ?? "kg");
  const [file, setFile] = createSignal<File | null>(null);
  const [link, setLink] = createSignal("");
  const [removeMedia, setRemoveMedia] = createSignal(false);
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  // Local preview of the freshly-picked file (revoked when it changes / unmounts).
  const [previewUrl, setPreviewUrl] = createSignal<string | null>(null);
  createEffect(() => {
    const f = file();
    const url = f ? URL.createObjectURL(f) : null;
    setPreviewUrl(url);
    onCleanup(() => {
      if (url) URL.revokeObjectURL(url);
    });
  });

  const hasExistingMedia = (): boolean =>
    !!editing()?.media_type && !file() && !link().trim() && !removeMedia();

  async function submit(): Promise<void> {
    setError(null);
    if (!name().trim()) {
      setError(t("validation.nameRequired"));
      return;
    }
    setSubmitting(true);
    try {
      const target = editing();
      const ex = target
        ? await props.api.updateExercise(target.id, { name: name().trim(), unit: unit() })
        : await props.api.createExercise(name().trim(), unit());
      const picked = file();
      if (picked) {
        await props.api.uploadExerciseMedia(ex.id, picked);
      } else if (link().trim()) {
        await props.api.attachExerciseLink(ex.id, link().trim());
      } else if (target && removeMedia()) {
        await props.api.clearExerciseMedia(ex.id);
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
      title={editing() ? t("exercises.editTitle") : t("exercises.newTitle")}
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
        <select
          value={unit()}
          onChange={(e) => setUnit(e.currentTarget.value as Unit)}
          disabled={submitting()}
        >
          <option value="kg">{t("unit.kg")}</option>
          <option value="reps">{t("unit.reps")}</option>
          <option value="seconds">{t("unit.seconds")}</option>
          <option value="meters">{t("unit.meters")}</option>
        </select>
      </Field>

      {/* Existing media (edit mode) with the option to remove it. */}
      <Show when={hasExistingMedia()}>
        <Field label={t("exercise.currentMedia")}>
          <Show when={editing()?.media_type === "photo" && editing()?.media_file_unique_id}>
            <img
              src={props.api.mediaFileUrl(editing()?.media_file_unique_id ?? "")}
              alt={editing()?.name}
              style={{ "max-width": "100%", "border-radius": "10px" }}
            />
          </Show>
          <Show when={editing()?.media_type === "video"}>
            <p>🎥 {t("exercise.hasVideo")}</p>
          </Show>
          <Show when={editing()?.media_type === "link" && editing()?.media_url}>
            <a href={editing()?.media_url ?? ""} target="_blank" rel="noreferrer">
              {editing()?.media_url}
            </a>
          </Show>
          <button type="button" class="secondary" onClick={() => setRemoveMedia(true)}>
            {t("exercise.removeMedia")}
          </button>
        </Field>
      </Show>

      <Show when={removeMedia()}>
        <Field label={t("exercise.currentMedia")}>
          <p>{t("exercise.mediaWillBeRemoved")}</p>
          <button type="button" class="secondary" onClick={() => setRemoveMedia(false)}>
            {t("common.undo")}
          </button>
        </Field>
      </Show>

      <Field label={editing() ? t("exercise.replaceMediaFile") : t("exercise.mediaFile")}>
        <input
          type="file"
          accept="image/*,video/*"
          onChange={(e) => setFile(e.currentTarget.files?.[0] ?? null)}
        />
        <Show when={previewUrl()}>
          <div style={{ "margin-top": "8px" }}>
            <Show
              when={file()?.type.startsWith("video/")}
              fallback={
                <img
                  src={previewUrl() ?? ""}
                  alt={t("exercise.preview")}
                  style={{ "max-width": "100%", "border-radius": "10px" }}
                />
              }
            >
              {/* biome-ignore lint/a11y/useMediaCaption: user-supplied exercise demo */}
              <video
                src={previewUrl() ?? ""}
                controls
                style={{ "max-width": "100%", "border-radius": "10px" }}
              />
            </Show>
            <button type="button" class="secondary" onClick={() => setFile(null)}>
              {t("exercise.clearSelection")}
            </button>
          </div>
        </Show>
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
