import { type Component, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
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
      setError(t("validation.nameRequired"));
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
      title={t("trainer.createGroup")}
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label={t("field.name")}>
        <input
          type="text"
          value={name()}
          onInput={(e) => setName(e.currentTarget.value)}
          placeholder={t("placeholder.groupName")}
        />
      </Field>
      <Field label={t("field.type")}>
        <select
          value={type()}
          onChange={(e) => setType(e.currentTarget.value as "group" | "personal")}
        >
          <option value="group">{t("groupType.group")}</option>
          <option value="personal">{t("groupType.personalOption")}</option>
        </select>
      </Field>
    </FormShell>
  );
};
