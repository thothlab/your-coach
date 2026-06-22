import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi } from "../api";
import { t } from "../lib/i18n";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onNew: () => void;
}

export const Workouts: Component<Props> = (props) => {
  const [templates] = createResource(() => props.api.listWorkoutTemplates());

  return (
    <main class="page">
      <button type="button" onClick={props.onBack}>
        {t("common.back")}
      </button>
      <h1>{t("workouts.title")}</h1>
      <button type="button" onClick={props.onNew}>
        {t("workouts.new")}
      </button>
      <Show when={templates.loading}>{t("common.loading")}</Show>
      <ul>
        <For each={templates()}>
          {(tpl) => (
            <li>
              <strong>{tpl.name}</strong> ·{" "}
              <small>{t("workouts.exerciseCount", { n: tpl.items.length })}</small>
            </li>
          )}
        </For>
      </ul>
    </main>
  );
};
