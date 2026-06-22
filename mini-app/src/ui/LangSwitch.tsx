import { type Component, For } from "solid-js";
import { type Locale, locale, setLocale } from "../lib/i18n";

const LOCALES: Locale[] = ["ru", "en"];

export const LangSwitch: Component = () => (
  <div class="lang-switch">
    <For each={LOCALES}>
      {(l) => (
        <button
          type="button"
          aria-pressed={locale() === l}
          classList={{ active: locale() === l }}
          onClick={() => setLocale(l)}
        >
          {l.toUpperCase()}
        </button>
      )}
    </For>
  </div>
);
