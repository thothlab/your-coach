import {
  type Component,
  ErrorBoundary,
  Match,
  Show,
  Suspense,
  Switch,
  createEffect,
  createResource,
  createSignal,
  onCleanup,
} from "solid-js";
import { TrainBeatApi, type User } from "./api";
import type { Page } from "./lib/navigation";
import { getInitData, getWebApp, setBackButton } from "./lib/telegram";
import { AthleteHome } from "./pages/AthleteHome";
import { BroadcastCompose } from "./pages/BroadcastCompose";
import { ExerciseCreate } from "./pages/ExerciseCreate";
import { Exercises } from "./pages/Exercises";
import { GroupCreate } from "./pages/GroupCreate";
import { SessionCreate } from "./pages/SessionCreate";
import { SessionDetail } from "./pages/SessionDetail";
import { TrainerHome } from "./pages/TrainerHome";
import { WorkoutTemplateCreate } from "./pages/WorkoutTemplateCreate";
import { Workouts } from "./pages/Workouts";

async function bootstrap(): Promise<{ api: TrainBeatApi; user: User }> {
  const initData = getInitData();
  if (!initData) {
    throw new Error("Open this app inside Telegram.");
  }
  const api = new TrainBeatApi(initData);
  await api.authenticate();
  const me = await api.me();
  return { api, user: me };
}

function applyTheme(): void {
  const app = getWebApp();
  if (!app) return;
  const set = (name: string, value?: string) => {
    if (value) document.documentElement.style.setProperty(name, value);
  };
  set("--tg-theme-bg-color", app.themeParams.bg_color);
  set("--tg-theme-text-color", app.themeParams.text_color);
  set("--tg-theme-button-color", app.themeParams.button_color);
  set("--tg-theme-secondary-bg-color", app.themeParams.secondary_bg_color);
}

export const App: Component = () => {
  applyTheme();
  const [session] = createResource(bootstrap);
  const [stack, setStack] = createSignal<Page[]>([{ kind: "home" }]);

  const top = (): Page => stack()[stack().length - 1];

  function navigate(page: Page): void {
    setStack((prev) => [...prev, page]);
  }

  function back(): void {
    setStack((prev) => (prev.length > 1 ? prev.slice(0, -1) : prev));
  }

  function home(): void {
    setStack([{ kind: "home" }]);
  }

  createEffect(() => {
    const isRoot = stack().length === 1;
    const cleanup = setBackButton(!isRoot, back);
    onCleanup(cleanup);
  });

  return (
    <ErrorBoundary
      fallback={(err: unknown, reset) => (
        <main class="page">
          <h1>Something went wrong</h1>
          <p>{err instanceof Error ? err.message : String(err)}</p>
          <button type="button" onClick={reset}>
            Try again
          </button>
        </main>
      )}
    >
      <Suspense
        fallback={
          <main class="page">
            <h1>Loading TrainBeat…</h1>
          </main>
        }
      >
        <Show when={session()} keyed>
          {(s) => (
            <Switch>
              <Match when={top().kind === "home"}>
                <Switch>
                  <Match when={s.user.role === "trainer"}>
                    <TrainerHome api={s.api} user={s.user} navigate={navigate} />
                  </Match>
                  <Match when={s.user.role === "athlete"}>
                    <AthleteHome api={s.api} user={s.user} navigate={navigate} />
                  </Match>
                </Switch>
              </Match>
              <Match when={top().kind === "group-new"}>
                <GroupCreate api={s.api} onBack={back} onCreated={home} />
              </Match>
              <Match when={top().kind === "exercises"}>
                <Exercises
                  api={s.api}
                  onBack={back}
                  onNew={() => navigate({ kind: "exercise-new" })}
                />
              </Match>
              <Match when={top().kind === "exercise-new"}>
                <ExerciseCreate api={s.api} onBack={back} onCreated={back} />
              </Match>
              <Match when={top().kind === "workouts"}>
                <Workouts
                  api={s.api}
                  onBack={back}
                  onNew={() => navigate({ kind: "workout-new" })}
                />
              </Match>
              <Match when={top().kind === "workout-new"}>
                <WorkoutTemplateCreate api={s.api} onBack={back} onCreated={back} />
              </Match>
              <Match when={top().kind === "session-new"}>
                <SessionCreate api={s.api} onBack={back} onCreated={home} />
              </Match>
              <Match when={top().kind === "broadcast"}>
                <BroadcastCompose api={s.api} onBack={back} />
              </Match>
              <Match when={(() => top().kind === "session-detail")()}>
                <SessionDetail
                  api={s.api}
                  user={s.user}
                  sessionId={(top() as { sessionId: number }).sessionId}
                  onBack={back}
                />
              </Match>
            </Switch>
          )}
        </Show>
      </Suspense>
    </ErrorBoundary>
  );
};
