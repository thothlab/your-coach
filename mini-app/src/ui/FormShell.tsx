import { type JSX, type ParentComponent, Show } from "solid-js";

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
      <button type="button" onClick={props.onBack}>
        ← back
      </button>
      <h1>{props.title}</h1>
      <Show when={props.error}>
        <div class="banner-error">{props.error}</div>
      </Show>
      <form onSubmit={handleSubmit as unknown as JSX.EventHandler<HTMLFormElement, SubmitEvent>}>
        {props.children}
        <div style={{ "margin-top": "20px" }}>
          <button type="submit" disabled={props.submitting}>
            {props.submitting ? "Saving…" : (props.submitLabel ?? "Save")}
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
