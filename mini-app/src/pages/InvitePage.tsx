import QRCode from "qrcode";
import { type Component, Show, createResource, createSignal } from "solid-js";
import type { TrainBeatApi } from "../api";
import { t } from "../lib/i18n";

interface Props {
  api: TrainBeatApi;
  groupId: number;
  groupName: string;
  onBack: () => void;
}

export const InvitePage: Component<Props> = (props) => {
  const [invite, { refetch }] = createResource(() => props.api.createInvite(props.groupId));
  const [qr] = createResource(
    () => invite()?.url,
    (url) => QRCode.toDataURL(url, { width: 240, margin: 1 }),
  );
  const [copied, setCopied] = createSignal(false);

  async function copy(): Promise<void> {
    const url = invite()?.url;
    if (!url) return;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard may be blocked in some webviews — the link stays selectable on screen.
    }
  }

  return (
    <main class="page">
      <button type="button" onClick={props.onBack}>
        {t("common.back")}
      </button>
      <h1>{t("invite.title", { group: props.groupName })}</h1>

      <Show when={invite.loading}>{t("common.loading")}</Show>
      <Show when={invite.error}>
        <div class="banner-error">{t("error.title")}</div>
      </Show>

      <Show when={invite()}>
        {(inv) => (
          <>
            <p>{t("invite.hint")}</p>

            <Show when={qr()}>
              <div style={{ "text-align": "center", margin: "12px 0" }}>
                <img src={qr()} alt="QR" width="240" height="240" />
              </div>
            </Show>

            <div
              style={{
                "word-break": "break-all",
                "font-size": "13px",
                margin: "8px 0",
                "user-select": "all",
              }}
            >
              {inv().url}
            </div>

            <button type="button" onClick={copy}>
              {copied() ? t("invite.copied") : t("invite.copy")}
            </button>
            <button type="button" onClick={() => refetch()}>
              {t("invite.regenerate")}
            </button>

            <p style={{ "font-size": "12px", opacity: "0.7", "margin-top": "12px" }}>
              {t("invite.expires", { date: new Date(inv().expires_at).toLocaleString() })}
            </p>
          </>
        )}
      </Show>
    </main>
  );
};
