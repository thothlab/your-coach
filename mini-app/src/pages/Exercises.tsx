import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { Exercise, TrainBeatApi } from "../api";
import { t } from "../lib/i18n";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onNew: () => void;
  onEdit: (exercise: Exercise) => void;
}

export const Exercises: Component<Props> = (props) => {
  const [exercises] = createResource(() => props.api.listExercises());
  const [sent, setSent] = createSignal<number | null>(null);

  async function watch(id: number): Promise<void> {
    await props.api.sendExerciseMedia(id);
    setSent(id);
    setTimeout(() => setSent((cur) => (cur === id ? null : cur)), 3000);
  }

  return (
    <main class="page">
      <button type="button" class="back" onClick={props.onBack}>
        {t("common.back")}
      </button>
      <h1>{t("trainer.exercises")}</h1>
      <button type="button" onClick={props.onNew}>
        {t("exercises.new")}
      </button>
      <Show when={exercises.loading}>{t("common.loading")}</Show>
      <ul>
        <For each={exercises()}>
          {(ex) => (
            <li>
              <div style={{ display: "flex", "align-items": "center", gap: "8px" }}>
                <strong>{ex.name}</strong> · <small>{ex.unit}</small>
                <button
                  type="button"
                  class="secondary"
                  style={{ "margin-left": "auto" }}
                  onClick={() => props.onEdit(ex)}
                >
                  {t("common.edit")}
                </button>
              </div>
              <Show when={ex.media_type === "photo" && ex.media_file_unique_id}>
                <div>
                  <img
                    src={props.api.mediaFileUrl(ex.media_file_unique_id ?? "")}
                    alt={ex.name}
                    style={{ "max-width": "100%", "border-radius": "10px", "margin-top": "8px" }}
                  />
                </div>
              </Show>
              <Show when={ex.media_type === "video"}>
                <div>
                  <button type="button" class="secondary" onClick={() => watch(ex.id)}>
                    {sent() === ex.id ? t("exercise.sent") : t("exercise.watch")}
                  </button>
                </div>
              </Show>
              <Show when={ex.media_type === "link" && ex.media_url}>
                <div>
                  <a href={ex.media_url ?? ""} target="_blank" rel="noreferrer">
                    {t("exercise.openLink")}
                  </a>
                </div>
              </Show>
            </li>
          )}
        </For>
      </ul>
    </main>
  );
};
