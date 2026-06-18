import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi } from "../api";

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
        ← back
      </button>
      <h1>Workout templates</h1>
      <button type="button" onClick={props.onNew}>
        + New template
      </button>
      <Show when={templates.loading}>Loading…</Show>
      <ul>
        <For each={templates()}>
          {(t) => (
            <li>
              <strong>{t.name}</strong> · <small>{t.items.length} exercises</small>
            </li>
          )}
        </For>
      </ul>
    </main>
  );
};
