# Decision 03 — Mini-App stack

**Date:** 2026-06-18
**Status:** Accepted

## Decision

Mini-App is **SolidJS 1.x + Vite 5 + TypeScript**, routed with `@solidjs/router`, styled with vanilla CSS (no UI kit for MVP), linted+formatted by **Biome**.

## Rationale

- SolidJS compiles to highly optimized DOM updates with **no virtual DOM** and a runtime of ~10 KB gz — directly underwrites the 250 KB gz initial bundle budget from PRD-01.
- JSX-like syntax keeps the learning surface familiar to React devs.
- Vite gives instant HMR and tiny prod builds.
- Biome is one binary for lint + format + import sort — replaces ESLint+Prettier with much less config drift.

## Rejected

- **React + Vite** — base React+ReactDOM eats ~40 KB gz before any feature code; we'd be permanently fighting the budget once router + form libs land.
- **Svelte 5** — close runner-up; Solid wins on community size for our use case and on a more conventional component model.

## Consequences

- Solid's fine-grained reactivity means signals/stores, not React-style component-tree re-render. Engineers new to Solid should read the [reactivity docs](https://www.solidjs.com/guides/reactivity) before writing complex state.
- CI enforces the 250 KB gz budget via `mini-app/scripts/check-bundle-size.mjs` — see Decision 04 and Task 09 for details.
- Component library: none for MVP; design tokens live in `mini-app/src/styles/tokens.css`.
