import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi, WorkoutTemplate } from "../api";
import { t } from "../lib/i18n";
import { PencilIcon } from "../ui/icons";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onNew: () => void;
  onEdit: (template: WorkoutTemplate) => void;
}

export const Workouts: Component<Props> = (props) => {
  const [templates] = createResource(() => props.api.listWorkoutTemplates());

  return (
    <main class="page">
      <button type="button" class="back" onClick={props.onBack}>
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
              <div class="row-line">
                <span>
                  <strong>{tpl.name}</strong> <small>({tpl.items.length})</small>
                </span>
                <button
                  type="button"
                  class="secondary icon-btn"
                  style={{ "margin-left": "auto" }}
                  aria-label={t("common.edit")}
                  onClick={() => props.onEdit(tpl)}
                >
                  <PencilIcon />
                </button>
              </div>
            </li>
          )}
        </For>
      </ul>
    </main>
  );
};
