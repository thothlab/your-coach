import { type Component, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
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
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  async function submit(): Promise<void> {
    setError(null);
    if (!name().trim()) {
      setError("Name is required");
      return;
    }
    setSubmitting(true);
    try {
      await props.api.createExercise(name().trim(), unit());
      props.onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title="New exercise"
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label="Name">
        <input
          type="text"
          value={name()}
          onInput={(e) => setName(e.currentTarget.value)}
          placeholder="Back squat"
        />
      </Field>
      <Field label="Unit">
        <select value={unit()} onChange={(e) => setUnit(e.currentTarget.value as Unit)}>
          <option value="kg">kg (weighted)</option>
          <option value="reps">reps (bodyweight)</option>
          <option value="seconds">seconds (timed)</option>
          <option value="meters">meters (distance)</option>
        </select>
      </Field>
    </FormShell>
  );
};
