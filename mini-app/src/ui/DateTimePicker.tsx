import { type Component, For, Index, Show, createMemo, createSignal } from "solid-js";
import { locale, t } from "../lib/i18n";

interface Props {
  value: string; // "YYYY-MM-DDTHH:mm" (local) or ""
  onChange: (value: string) => void;
}

const pad = (n: number): string => String(n).padStart(2, "0");
const WEEKDAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"];

interface Parts {
  y: number;
  m: number; // 0-based
  d: number;
  h: number;
  min: number;
}

function parse(value: string): Parts | null {
  if (!value) return null;
  const [date, time] = value.split("T");
  const [y, m, d] = date.split("-").map(Number);
  const [h, min] = (time ?? "00:00").split(":").map(Number);
  if (!y || !m || !d) return null;
  return { y, m: m - 1, d, h: h || 0, min: min || 0 };
}

const compose = (p: Parts): string =>
  `${p.y}-${pad(p.m + 1)}-${pad(p.d)}T${pad(p.h)}:${pad(p.min)}`;

function monthCells(y: number, m: number): (number | null)[] {
  const startDow = (new Date(y, m, 1).getDay() + 6) % 7; // Monday-first
  const days = new Date(y, m + 1, 0).getDate();
  const cells: (number | null)[] = Array.from({ length: startDow }, () => null);
  for (let d = 1; d <= days; d++) cells.push(d);
  return cells;
}

export const DateTimePicker: Component<Props> = (props) => {
  const now = new Date();
  const sel = createMemo(() => parse(props.value));
  const [view, setView] = createSignal({
    y: sel()?.y ?? now.getFullYear(),
    m: sel()?.m ?? now.getMonth(),
  });

  function shiftMonth(delta: number): void {
    setView((v) => {
      const d = new Date(v.y, v.m + delta, 1);
      return { y: d.getFullYear(), m: d.getMonth() };
    });
  }

  function pickDay(day: number): void {
    const s = sel();
    const { y, m } = view();
    props.onChange(compose({ y, m, d: day, h: s?.h ?? 8, min: s?.min ?? 0 }));
  }

  function setTime(part: "h" | "min", val: number): void {
    const s = sel();
    const base: Parts = s ?? {
      y: now.getFullYear(),
      m: now.getMonth(),
      d: now.getDate(),
      h: 8,
      min: 0,
    };
    props.onChange(compose({ ...base, [part]: val }));
  }

  const monthLabel = createMemo(() => {
    const { y, m } = view();
    return new Date(y, m, 1).toLocaleDateString(locale() === "ru" ? "ru-RU" : "en-US", {
      month: "long",
      year: "numeric",
    });
  });

  const isSelected = (day: number): boolean => {
    const s = sel();
    const { y, m } = view();
    return !!s && s.y === y && s.m === m && s.d === day;
  };

  const hours = Array.from({ length: 24 }, (_, i) => i);
  const minutes = Array.from({ length: 12 }, (_, i) => i * 5);

  return (
    <div class="dtp">
      <div class="dtp-head">
        <button type="button" onClick={() => shiftMonth(-1)} aria-label="prev">
          ‹
        </button>
        <span style={{ "text-transform": "capitalize" }}>{monthLabel()}</span>
        <button type="button" onClick={() => shiftMonth(1)} aria-label="next">
          ›
        </button>
      </div>

      <div class="dtp-grid">
        <For each={WEEKDAY_CODES}>
          {(code) => <div class="dtp-dow">{t(`weekday.${code}`)}</div>}
        </For>
        <Index each={monthCells(view().y, view().m)}>
          {(cell) => (
            <Show when={cell() !== null} fallback={<div />}>
              <button
                type="button"
                class="dtp-day"
                classList={{ selected: isSelected(cell() as number) }}
                onClick={() => pickDay(cell() as number)}
              >
                {cell()}
              </button>
            </Show>
          )}
        </Index>
      </div>

      <div class="dtp-time">
        <select value={sel()?.h ?? 8} onChange={(e) => setTime("h", Number(e.currentTarget.value))}>
          <For each={hours}>{(h) => <option value={h}>{pad(h)}</option>}</For>
        </select>
        <span>:</span>
        <select
          value={sel()?.min ?? 0}
          onChange={(e) => setTime("min", Number(e.currentTarget.value))}
        >
          <For each={minutes}>{(mm) => <option value={mm}>{pad(mm)}</option>}</For>
        </select>
      </div>
    </div>
  );
};
