export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

export interface TelegramBackButton {
  show: () => void;
  hide: () => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: { user?: { id: number; first_name?: string } };
  version: string;
  themeParams: TelegramThemeParams;
  colorScheme: "light" | "dark";
  BackButton: TelegramBackButton;
  ready: () => void;
  expand: () => void;
  onEvent: (event: string, cb: () => void) => void;
}

export function setBackButton(visible: boolean, onTap: () => void): () => void {
  const app = getWebApp();
  if (!app?.BackButton) {
    return () => {};
  }
  if (visible) {
    app.BackButton.show();
    app.BackButton.onClick(onTap);
    return () => {
      app.BackButton.offClick(onTap);
      app.BackButton.hide();
    };
  }
  app.BackButton.hide();
  return () => {};
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

export function getWebApp(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function getInitData(): string {
  const app = getWebApp();
  if (!app) {
    // Standalone dev mode — Mini-App opened directly in browser.
    return "";
  }
  app.ready();
  return app.initData;
}
