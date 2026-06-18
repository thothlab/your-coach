import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { errorMessage } from "../lib/api-error";
import { Field, FormShell } from "../ui/FormShell";

interface Props {
  api: TrainBeatApi;
  onBack: () => void;
  onCreated: () => void;
}

const WEEKDAYS: Array<{ code: string; label: string }> = [
  { code: "MO", label: "Mon" },
  { code: "TU", label: "Tue" },
  { code: "WE", label: "Wed" },
  { code: "TH", label: "Thu" },
  { code: "FR", label: "Fri" },
  { code: "SA", label: "Sat" },
  { code: "SU", label: "Sun" },
];

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
      setError("Pick a group");
      return;
    }
    if (!start()) {
      setError("Pick a start time");
      return;
    }
    let rrule: string | undefined;
    if (recurring()) {
      const picked = [...days()];
      if (picked.length === 0) {
        setError("Pick at least one weekday");
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
      title="New session"
      onBack={props.onBack}
      error={error()}
      submitting={submitting()}
      onSubmit={submit}
    >
      <Field label="Group">
        <select
          value={groupId() ?? ""}
          onChange={(e) => setGroupId(e.currentTarget.value ? Number(e.currentTarget.value) : null)}
        >
          <option value="">— pick —</option>
          <For each={groups()}>{(g) => <option value={g.id}>{g.name}</option>}</For>
        </select>
      </Field>
      <Field label="Workout template (optional)">
        <select
          value={templateId() ?? ""}
          onChange={(e) =>
            setTemplateId(e.currentTarget.value ? Number(e.currentTarget.value) : null)
          }
        >
          <option value="">— none —</option>
          <For each={templates()}>{(t) => <option value={t.id}>{t.name}</option>}</For>
        </select>
      </Field>
      <Field label="Start">
        <input
          type="datetime-local"
          value={start()}
          onInput={(e) => setStart(e.currentTarget.value)}
        />
      </Field>
      <Field label="Duration (min)">
        <input
          type="number"
          min="5"
          max="600"
          value={duration()}
          onInput={(e) => setDuration(Number(e.currentTarget.value))}
        />
      </Field>
      <Field label="Recurring weekly">
        <input
          type="checkbox"
          checked={recurring()}
          onChange={(e) => setRecurring(e.currentTarget.checked)}
        />
      </Field>
      <Show when={recurring()}>
        <Field label="Weekdays">
          <div>
            <For each={WEEKDAYS}>
              {(d) => (
                <label style={{ "margin-right": "8px" }}>
                  <input
                    type="checkbox"
                    checked={days().has(d.code)}
                    onChange={() => toggleDay(d.code)}
                  />{" "}
                  {d.label}
                </label>
              )}
            </For>
          </div>
        </Field>
      </Show>
    </FormShell>
  );
};
