import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage, isApiError } from "../lib/api-error";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
}

export const BroadcastCompose: Component<Props> = (props) => {
  const [groups] = createResource(() => props.api.listGroups());
  const [groupId, setGroupId] = createSignal<number | null>(null);
  const [text, setText] = createSignal("");
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);
  const [success, setSuccess] = createSignal<string | null>(null);

  async function submit(): Promise<void> {
    setError(null);
    setSuccess(null);
    if (groupId() == null) {
      setError("Pick a group");
      return;
    }
    if (!text().trim()) {
      setError("Message text is required");
      return;
    }
    setSubmitting(true);
    try {
      const result = await props.api.sendBroadcast(groupId() as number, text().trim());
      setSuccess(`Sent to ${result.recipient_count} member(s)`);
      setText("");
    } catch (err) {
      if (isApiError(err) && err.status === 429) {
        setError("Rate limit reached — try again later");
      } else {
        setError(errorMessage(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title="Broadcast"
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      submitLabel="Send"
      onSubmit={submit}
    >
      <Show when={success()}>
        <div class="banner-success">{success()}</div>
      </Show>
      <Field label="Group">
        <select
          value={groupId() ?? ""}
          onChange={(e) => setGroupId(e.currentTarget.value ? Number(e.currentTarget.value) : null)}
        >
          <option value="">— pick —</option>
          <For each={groups()}>{(g) => <option value={g.id}>{g.name}</option>}</For>
        </select>
      </Field>
      <Field label="Message">
        <textarea
          value={text()}
          onInput={(e) => setText(e.currentTarget.value)}
          rows="5"
          placeholder="Bring water, see you at 7."
        />
      </Field>
      <div>
        <small>{text().length} / 4000</small>
      </div>
    </FormShell>
  );
};
