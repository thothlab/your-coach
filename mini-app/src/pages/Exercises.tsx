import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi } from "../api";
import { t } from "../lib/i18n";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onNew: () => void;
}

export const Exercises: Component<Props> = (props) => {
  const [exercises] = createResource(() => props.api.listExercises());

  return (
    <main class="page">
      <button type="button" onClick={props.onBack}>
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
              <strong>{ex.name}</strong> · <small>{ex.unit}</small>
            </li>
          )}
        </For>
      </ul>
    </main>
  );
};
