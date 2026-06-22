import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { t } from "../lib/i18n";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onCreated: () => void;
}

// Codes only — labels are resolved through t() so they react to a locale switch.
const WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"];

export const SessionCreate: Component<Props> = (props) => {
  const [groups] = createResource(() => props.api.listGroups());
  const [templates] = createResource(() => props.api.listWorkoutTemplates());
  const [groupId, setGroupId] = createSignal<number | null>(null);
  const [templateId, setTemplateId] = createSignal<number | null>(null);
  const [start, setStart] = createSignal<string>("");
  const [duration, setDuration] = createSignal(60);
  const [recurring, setRecurring] = createSignal(false);
  const [days, setDays] = createSignal<Set<string>>(new Set());
  const [submitting, setSubmitting] = createSignal(false);
  const [error, setError] = createSignal<string | null>(null);

  function toggleDay(code: string): void {
    setDays((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
  }

  async function submit(): Promise<void> {
    setError(null);
    if (groupId() == null) {
      setError(t("validation.pickGroup"));
      return;
    }
    if (!start()) {
      setError(t("validation.pickStart"));
      return;
    }
    let rrule: string | undefined;
    if (recurring()) {
      const picked = [...days()];
      if (picked.length === 0) {
        setError(t("validation.pickWeekday"));
        return;
      }
      rrule = `FREQ=WEEKLY;BYDAY=${picked.join(",")}`;
    }
    setSubmitting(true);
    try {
      await props.api.createSession({
        group_id: groupId() as number,
        workout_template_id: templateId() ?? undefined,
        scheduled_at: new Date(start()).toISOString(),
        duration_min: duration(),
        recurrence_rule: rrule,
      });
      props.onCreated();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <FormShell
      title={t("trainer.newSession")}
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label={t("field.group")}>
        <select
          value={groupId() ?? ""}
          onChange={(e) => setGroupId(e.currentTarget.value ? Number(e.currentTarget.value) : null)}
        >
          <option value="">{t("common.pick")}</option>
          <For each={groups()}>{(g) => <option value={g.id}>{g.name}</option>}</For>
        </select>
      </Field>
      <Field label={t("field.workoutTemplateOpt")}>
        <select
          value={templateId() ?? ""}
          onChange={(e) =>
            setTemplateId(e.currentTarget.value ? Number(e.currentTarget.value) : null)
          }
        >
          <option value="">{t("common.none")}</option>
          <For each={templates()}>{(tpl) => <option value={tpl.id}>{tpl.name}</option>}</For>
        </select>
      </Field>
      <Field label={t("field.start")}>
        <input
          type="datetime-local"
          value={start()}
          onInput={(e) => setStart(e.currentTarget.value)}
        />
      </Field>
      <Field label={t("field.durationMin")}>
        <input
          type="number"
          min="5"
          max="600"
          value={duration()}
          onInput={(e) => setDuration(Number(e.currentTarget.value))}
        />
      </Field>
      <Field label={t("field.recurringWeekly")}>
        <input
          type="checkbox"
          checked={recurring()}
          onChange={(e) => setRecurring(e.currentTarget.checked)}
        />
      </Field>
      <Show when={recurring()}>
        <Field label={t("field.weekdays")}>
          <div>
            <For each={WEEKDAY_CODES}>
              {(code) => (
                <label style={{ "margin-right": "8px" }}>
                  <input
                    type="checkbox"
                    checked={days().has(code)}
                    onChange={() => toggleDay(code)}
                  />{" "}
                  {t(`weekday.${code}`)}
                </label>
              )}
            </For>
          </div>
        </Field>
      </Show>
    </FormShell>
  );
};
