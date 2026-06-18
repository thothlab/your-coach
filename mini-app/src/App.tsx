import {
  type Component,
  ErrorBoundary,
  Match,
  Show,
  Suspense,
  Switch,
  createResource,
  createSignal,
} from "solid-js";
import { TrainBeatApi, type User } from "./api";
import { getInitData, getWebApp } from "./lib/telegram";
import { AthleteHome } from "./pages/AthleteHome";
import { SessionDetail } from "./pages/SessionDetail";
import { TrainerHome } from "./pages/TrainerHome";

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
  const [openSessionId, setOpenSessionId] = createSignal<number | null>(null);

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
            <Show
              when={openSessionId() !== null}
              fallback={
                <Switch>
                  <Match when={s.user.role === "trainer"}>
                    <TrainerHome api={s.api} user={s.user} onOpenSession={setOpenSessionId} />
                  </Match>
                  <Match when={s.user.role === "athlete"}>
                    <AthleteHome api={s.api} user={s.user} onOpenSession={setOpenSessionId} />
                  </Match>
                </Switch>
              }
            >
              <SessionDetail
                api={s.api}
                user={s.user}
                sessionId={openSessionId() as number}
                onBack={() => setOpenSessionId(null)}
              />
            </Show>
          )}
        </Show>
      </Suspense>
    </ErrorBoundary>
  );
};
