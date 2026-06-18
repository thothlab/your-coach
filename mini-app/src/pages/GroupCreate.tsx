import { type Component, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onCreated: () => void;
}

export const GroupCreate: Component<Props> = (props) => {
  const [name, setName] = createSignal("");
  const [type, setType] = createSignal<"group" | "personal">("group");
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
      await props.api.createGroup(name().trim(), type());
      props.onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title="Create group"
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
          placeholder="Monday strength"
        />
      </Field>
      <Field label="Type">
        <select
          value={type()}
          onChange={(e) => setType(e.currentTarget.value as "group" | "personal")}
        >
          <option value="group">Group</option>
          <option value="personal">Personal (1 athlete)</option>
        </select>
      </Field>
    </FormShell>
  );
};
