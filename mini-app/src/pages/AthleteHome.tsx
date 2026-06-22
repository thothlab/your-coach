import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi, User } from "../api";
import { t } from "../lib/i18n";
import type { Navigate } from "../lib/navigation";
import { LangSwitch } from "../ui/LangSwitch";

interface Props {
  api: TrainBeatApi;
  user: User;
  navigate: Navigate;
}

export const AthleteHome: Component<Props> = (props) => {
  const today = new Date();
  const in14 = new Date(today.getTime() + 14 * 24 * 60 * 60 * 1000);
  const [sessions, { refetch }] = createResource(() =>
    props.api.listSessions(today.toISOString(), in14.toISOString()),
  );
  const [pending, setPending] = createSignal<number | null>(null);

  async function confirm(sessionId: number, decision: "confirmed" | "declined") {
    setPending(sessionId);
    try {
      await props.api.setAttendance(sessionId, decision);
      refetch();
    } finally {
      setPending(null);
    }
  }

  return (
    <main class="page">
      <LangSwitch />
      <h1>{t("athlete.greeting", { name: props.user.name })}</h1>

      <section>
        <h2>{t("athlete.upcoming")}</h2>
        <Show when={sessions.loading}>{t("common.loading")}</Show>
        <Show when={!sessions.loading && (sessions()?.length ?? 0) === 0}>
          <p>{t("athlete.noSessions")}</p>
        </Show>
        <ul>
          <For each={sessions()}>
            {(session) => (
              <li>
                <div>{new Date(session.scheduled_at).toLocaleString()}</div>
                <div>
                  <button
                    type="button"
                    disabled={pending() === session.id}
                    onClick={() => confirm(session.id, "confirmed")}
                  >
                    {t("common.confirm")}
                  </button>{" "}
                  <button
                    type="button"
                    disabled={pending() === session.id}
                    onClick={() => confirm(session.id, "declined")}
                  >
                    {t("common.decline")}
                  </button>{" "}
                  <button
                    type="button"
                    onClick={() =>
                      props.navigate({ kind: "session-detail", sessionId: session.id })
                    }
                  >
                    {t("common.open")}
                  </button>
                </div>
              </li>
            )}
          </For>
        </ul>
      </section>
    </main>
  );
};
