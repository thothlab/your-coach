import { type JSX, type ParentComponent, Show } from "solid-js";
import { t } from "../lib/i18n";

interface Props {
  title: string;
  onBack: () => void;
  error?: string | null;
  submitting?: boolean;
  submitLabel?: string;
  onSubmit: () => void | Promise<void>;
}

export const FormShell: ParentComponent<Props> = (props) => {
  function handleSubmit(e: SubmitEvent): void {
    e.preventDefault();
    void props.onSubmit();
  }

  return (
    <main class="page">
      <button type="button" class="back" onClick={props.onBack}>
        {t("common.back")}
      </button>
      <h1>{props.title}</h1>
      <Show when={props.error}>
        <div class="banner-error">{props.error}</div>
      </Show>
      <form onSubmit={handleSubmit as unknown as JSX.EventHandler<HTMLFormElement, SubmitEvent>}>
        {props.children}
        <div style={{ "margin-top": "20px" }}>
          <button type="submit" disabled={props.submitting}>
            {props.submitting ? t("common.saving") : (props.submitLabel ?? t("common.save"))}
          </button>
        </div>
      </form>
    </main>
  );
};

export const Field: ParentComponent<{ label: string; error?: string | null }> = (props) => (
  <div style={{ display: "block", "margin-bottom": "12px" }}>
    <div style={{ display: "block", "margin-bottom": "4px", "font-size": "13px" }}>
      {props.label}
    </div>
    {props.children}
    <Show when={props.error}>
      <span style={{ color: "tomato", "font-size": "12px" }}>{props.error}</span>
    </Show>
  </div>
);
