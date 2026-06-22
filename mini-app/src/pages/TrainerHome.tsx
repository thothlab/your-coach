import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi, User } from "../api";
import { t } from "../lib/i18n";
import type { Navigate } from "../lib/navigation";
import { LangSwitch } from "../ui/LangSwitch";

interface Props {
  api: TrainBeatApi;
  user: User;
  navigate: Navigate;
}

export const TrainerHome: Component<Props> = (props) => {
  const [groups] = createResource(() => props.api.listGroups());
  const today = new Date();
  const in14 = new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000);
  const [sessions] = createResource(() =>
    props.api.listSessions(today.toISOString(), in14.toISOString()),
  );

  return (
    <main class="page">
      <LangSwitch />
      <h1>TrainBeat · {props.user.name}</h1>

      <nav>
        <button type="button" onClick={() => props.navigate({ kind: "group-new" })}>
          {t("trainer.createGroup")}
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "session-new" })}>
          {t("trainer.newSession")}
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "exercises" })}>
          {t("trainer.exercises")}
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "workouts" })}>
          {t("trainer.workouts")}
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "broadcast" })}>
          {t("trainer.broadcast")}
        </button>
      </nav>

      <section>
        <h2>{t("trainer.groups")}</h2>
        <Show when={groups.loading}>{t("common.loading")}</Show>
        <Show when={!groups.loading && (groups()?.length ?? 0) === 0}>
          <p>{t("trainer.noGroups")}</p>
        </Show>
        <ul>
          <For each={groups()}>
            {(group) => (
              <li>
                <strong>{group.name}</strong>{" "}
                <small>
                  {t("trainer.groupMeta", {
                    type: t(`groupType.${group.type}`),
                    count: group.active_member_count,
                  })}
                </small>
              </li>
            )}
          </For>
        </ul>
      </section>

      <section>
        <h2>{t("trainer.upcoming")}</h2>
        <Show when={sessions.loading}>{t("common.loading")}</Show>
        <Show when={!sessions.loading && (sessions()?.length ?? 0) === 0}>
          <p>{t("trainer.noSessions")}</p>
        </Show>
        <ul>
          <For each={sessions()}>
            {(session) => (
              <li>
                <div>
                  {new Date(session.scheduled_at).toLocaleString()} ·{" "}
                  {t("common.minutes", { n: session.duration_min })}
                  <Show when={session.recurrence_rule}>
                    {" "}
                    <small>· {t("session.recurring")}</small>
                  </Show>
                </div>
                <button
                  type="button"
                  onClick={() => props.navigate({ kind: "session-detail", sessionId: session.id })}
                >
                  {t("common.open")}
                </button>
              </li>
            )}
          </For>
        </ul>
      </section>
    </main>
  );
};
