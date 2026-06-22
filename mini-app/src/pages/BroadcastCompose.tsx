import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage, isApiError } from "../lib/api-error";
import { t } from "../lib/i18n";
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
      setError(t("validation.pickGroup"));
      return;
    }
    if (!text().trim()) {
      setError(t("validation.messageRequired"));
      return;
    }
    setSubmitting(true);
    try {
      const result = await props.api.sendBroadcast(groupId() as number, text().trim());
      setSuccess(t("broadcast.sent", { count: result.recipient_count }));
      setText("");
    } catch (err) {
      if (isApiError(err) && err.status === 429) {
        setError(t("broadcast.rateLimit"));
      } else {
        setError(errorMessage(err));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title={t("trainer.broadcast")}
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      submitLabel={t("common.send")}
      onSubmit={submit}
    >
      <Show when={success()}>
        <div class="banner-success">{success()}</div>
      </Show>
      <Field label={t("field.group")}>
        <select
          value={groupId() ?? ""}
          onChange={(e) => setGroupId(e.currentTarget.value ? Number(e.currentTarget.value) : null)}
        >
          <option value="">{t("common.pick")}</option>
          <For each={groups()}>{(g) => <option value={g.id}>{g.name}</option>}</For>
        </select>
      </Field>
      <Field label={t("field.message")}>
        <textarea
          value={text()}
          onInput={(e) => setText(e.currentTarget.value)}
          rows="5"
          placeholder={t("placeholder.broadcast")}
        />
      </Field>
      <div>
        <small>{t("broadcast.charCount", { len: text().length })}</small>
      </div>
    </FormShell>
  );
};
