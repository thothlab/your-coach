import { render } from "solid-js/web";
import { App } from "./App";

// TEMP diagnostics — declared by the inline beacon in index.html.
declare global {
  interface Window {
    __beacon?: (m: string) => void;
  }
}
window.__beacon?.("module-start");

const root = document.getElementById("root");
if (!root) {
  throw new Error("#root not found");
}
render(() => <App />, root);
window.__beacon?.("render-returned");
