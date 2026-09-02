# Silent Roar — Wildlife Intelligence Platform (Frontend)

A frontend-only demonstration build of an AI-powered wildlife trafficking
intelligence platform. Everything runs against local mock data — there is no
real backend, database, authentication, scraping, messaging, or AI pipeline.

## Recent changes

- **Light theme**: the color palette (`tailwind.config.js`) was flipped from
  dark to light. All components use semantic tokens (`base-*` for surfaces,
  `ink-*` for text) so the whole app re-themes from that one file.
- **Larger type**: base font size and most text-size utility classes were
  bumped up a step across the app.
- **Real map**: the Intelligence Map (`src/components/map/IntelligenceMapCanvas.tsx`)
  now renders an actual Leaflet map (light CARTO basemap) with real lat/lng
  markers and route lines, instead of the earlier stylized SVG map. Run
  `npm install` to pull in the new `leaflet` / `react-leaflet` dependencies
  before starting the dev server.
- **Branding**: the sidebar logo, favicon, and page title now use the
  provided Silent Roar logo.
- **Dashboard chart**: a reference seizure-trends chart image was added to
  the Dashboard as a decorative "Seizure Trends Overview" panel.

## Stack

React + TypeScript + Vite + Tailwind CSS + React Router + Recharts + Leaflet
+ Lucide icons.

## Running locally

```bash
npm install
npm run dev       # start the dev server
npm run build      # production build to dist/
npm run preview    # preview the production build
```

## Project structure

```
src/
  components/   UI building blocks, grouped by feature area
    layout/       Sidebar, header, global search, app shell
    dashboard/    Stat cards, priority intelligence panel, explainable AI panel
    map/          Intelligence map canvas + layer controls
    network/      Network graph, entity drawer, Find Hidden Links animation
    timeline/     Investigation timeline
    evidence/     Evidence cards
    signalwatch/  Channel list, conversation window, linguistic analysis panel
    reports/      Report preview
    ui/           Badges, risk indicators, loading/empty/error states
  pages/        One component per route (Dashboard, IntelligenceMap, ...)
  services/     mockApi.ts + per-domain mock service files
  data/         Structured, cross-referenced mock datasets
  types/        Shared TypeScript interfaces
  utils/        Formatting helpers, graph layout, map intelligence aggregation
```

## Connecting a real backend

The UI never reads mock data directly — every page calls into
`src/services/mockApi.ts`, which exposes one async function per resource
(`getIncidents`, `getEntity`, `findHiddenLinks`, `generateBrief`, etc.) and
already returns Promises, matching a real fetch/axios client.

To point the app at a real API:

1. Replace the function bodies in `mockApi.ts` with real HTTP calls (or swap
   the whole module for one that calls your API client) — the exported
   function names and return shapes are the contract the UI already expects.
2. The TypeScript interfaces in `src/types/index.ts` describe the exact
   shape each page expects back. Keep your API responses compatible with
   these, or add a thin mapping layer in `mockApi.ts`.
3. Search and the "Find Hidden Links" / "Generate Investigation Brief"
   flows are already isolated behind `mockApi.search`, `mockApi.findHiddenLinks`,
   and `mockApi.generateBrief` — these are the natural place to call a real
   search index or AI pipeline.
4. No component reaches into `src/data/*` directly outside of `services/` and
   a couple of small aggregation helpers in `utils/` (`graph.ts`,
   `mapIntel.ts`) — those can also be moved server-side once real
   relationship data exists.
5. `src/components/network/FindHiddenLinksButton.tsx` and
   `src/pages/Reports.tsx` already model the "call an async job, show a
   staged progress animation, render the result" pattern a real long-running
   backend job (correlation analysis, report generation) would need — swap
   the `mockApi` calls inside them for real polling/streaming calls without
   touching the animation logic.

## Notes

- All incident, entity, route, and message data is fictional demonstration
  data clearly marked as such (see the "DEMO MODE" indicator in the header
  and the synthetic-data notice on the SignalWatch page).
- AI-generated conclusions are consistently phrased as hypotheses
  ("possible entity match", "AI-generated hypothesis") rather than confirmed
  fact, per the platform's investigative use case.
- No emoji are used anywhere in the UI — all iconography is Lucide React
  icons for a consistent, professional look.
