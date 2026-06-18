import { type Component, For, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi, User } from "../api";
import type { Navigate } from "../lib/navigation";

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
      <h1>Hi, {props.user.name}</h1>

      <section>
        <h2>Upcoming sessions</h2>
        <Show when={sessions.loading}>Loading…</Show>
        <Show when={!sessions.loading && (sessions()?.length ?? 0) === 0}>
          <p>No upcoming sessions. Enjoy the rest day.</p>
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
                    Confirm
                  </button>{" "}
                  <button
                    type="button"
                    disabled={pending() === session.id}
                    onClick={() => confirm(session.id, "declined")}
                  >
                    Decline
                  </button>{" "}
                  <button
                    type="button"
                    onClick={() =>
                      props.navigate({ kind: "session-detail", sessionId: session.id })
                    }
                  >
                    Open
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
