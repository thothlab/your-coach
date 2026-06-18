import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi } from "../api";

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
        ← back
      </button>
      <h1>Exercises</h1>
      <button type="button" onClick={props.onNew}>
        + New exercise
      </button>
      <Show when={exercises.loading}>Loading…</Show>
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
