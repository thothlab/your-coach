import { type Component, For, Show, createResource } from "solid-js";
import type { TrainBeatApi, User } from "../api";
import type { Navigate } from "../lib/navigation";

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
      <h1>TrainBeat · {props.user.name}</h1>

      <nav>
        <button type="button" onClick={() => props.navigate({ kind: "group-new" })}>
          Create group
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "session-new" })}>
          New session
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "exercises" })}>
          Exercises
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "workouts" })}>
          Workouts
        </button>
        <button type="button" onClick={() => props.navigate({ kind: "broadcast" })}>
          Broadcast
        </button>
      </nav>

      <section>
        <h2>Groups</h2>
        <Show when={groups.loading}>Loading…</Show>
        <Show when={!groups.loading && (groups()?.length ?? 0) === 0}>
          <p>No groups yet. Tap "Create group" above to make your first one.</p>
        </Show>
        <ul>
          <For each={groups()}>
            {(group) => (
              <li>
                <strong>{group.name}</strong>{" "}
                <small>
                  ({group.type}, {group.active_member_count} active)
                </small>
              </li>
            )}
          </For>
        </ul>
      </section>

      <section>
        <h2>Upcoming (14 days)</h2>
        <Show when={sessions.loading}>Loading…</Show>
        <Show when={!sessions.loading && (sessions()?.length ?? 0) === 0}>
          <p>No scheduled sessions in the next 14 days.</p>
        </Show>
        <ul>
          <For each={sessions()}>
            {(session) => (
              <li>
                <div>
                  {new Date(session.scheduled_at).toLocaleString()} · {session.duration_min} min
                  <Show when={session.recurrence_rule}>
                    {" "}
                    <small>· recurring</small>
                  </Show>
                </div>
                <button
                  type="button"
                  onClick={() => props.navigate({ kind: "session-detail", sessionId: session.id })}
                >
                  Open
                </button>
              </li>
            )}
          </For>
        </ul>
      </section>
    </main>
  );
};
