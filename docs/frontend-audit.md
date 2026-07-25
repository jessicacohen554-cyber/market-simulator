# Frontend audit — web trees, build paths, overlap & orphans

> Status: SUPERSEDED — investigation record (2026-06-19); frontend/site organization now governed by docs/refactor-consolidation-plan-2026-07.md §7-G.
>
> **The §4 "Decide" items were executed on 2026-07-25 (Wave 5C). See
> [§0 Executed](#0-executed--wave-5c-2026-07-25) immediately below for what was
> actually done and what the audit got wrong; the body from §1 on is the
> unmodified 2026-06-19 record and is now stale in several places.**

## 0. Executed — Wave 5C (2026-07-25)

The recommendations this document left open have been decided and carried out.
The body below was **not** rewritten, so read it as a dated snapshot.

### D-7 — dormant `frontend/` scenario app: **ARCHIVED**

Owner decision D-7 (`docs/refactor-consolidation-plan-2026-07.md` §9), approved
and executed 2026-07-25. §3 orphan 3 and the §4 "keep, but hide/label the card"
recommendation are **superseded**: the app is archived rather than relabelled.

Moved to `docs/archive/frontend-scenario-app/` (see its README for the revival
recipe): `index.html`, `decisions.html`, `parameters.html`, and
`js/{app,charts,data-loader,decisions}.js`. **Pages and JS only.**

Deliberately NOT moved:

- **`frontend/data/**`** — the live dashboard data path. `frontend/data/backcast/`
  is a CLAUDE.md rule-15 frozen surface that concurrent calibration sessions
  register into; `frontend/data/parameters.json` is still written by
  `scripts/generate_parameter_registry.py` and checked by
  `scripts/validate_parameters.py`.
- **`frontend/css/style.css`** — still the live design system for the root
  `index.html` and `model-updates.html` (§1 was right about this).
- **`scripts/export_results.py`** — untouched; reviving the app is a matter of
  running it.

Dead links removed in the same change: the "Results Dashboard" card on the root
`index.html` and the "Dashboard" nav entry on `model-updates.html` (the latter
now points at Calibration Status). `docs/archive/` is outside the deploy's
sparse checkout, so the archived pages are no longer staged into `_site`.

### Vendored libraries — pinned, not vendored (with a live defect fixed)

Not an audit recommendation, but discovered in the same lane and worth
recording here because this is the frontend record.

The 21 codebase-site pages loaded d3 from **three** sources (cdnjs 7.9.0,
jsdelivr `d3@7`, `d3js.org/d3.v7`) and gsap from **three** (cdnjs 3.12.2, cdnjs
3.12.5, jsdelivr `gsap@3`) — floating majors included. Worse, six pages carried
an `integrity` attribute whose hash did **not** match the file it guarded (two
different fabricated sha384 values for the same `d3js.org` URL, plus wrong
sha512 for gsap/ScrollTrigger 3.12.2). A wrong SRI hash makes the browser
refuse to execute the script, so d3 was blocked outright on `config-reference`,
`data-pipeline`, `fleet-offer-curves`, `lp-core`, `mental-model` and
`results-calibration`, and gsap on five of those.

Every page now loads one build of each, from cdnjs, with an integrity hash
computed from the bytes the CDN actually serves and cross-checked against the
cdnjs-published SRI:

| Library | URL | Verified SRI |
|---|---|---|
| d3 7.9.0 | `https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js` | `sha512-vc58qvvBdrDR4etbxMdlTt4GBQk1qjvyORR2nrsPsFPyrs+/u5c3+1Ct6upOgdZoIl7eq6k3a1UPDSNAQi/32A==` |
| gsap 3.12.5 | `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js` | `sha512-7eHRwcbYkK4d9g/6tD/mhkf++eoTHwpNM9woBxtPUBWm67zeAfFC+HrdoE2GanKeocly/VxeLvIqwvCdk7qScg==` |
| ScrollTrigger 3.12.5 | `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js` | `sha512-onMTRKJBKz8M1TnqqDuGBlowlH0ohFzMXYRNebz+yOcc5TQr/zAKsthzhuv0hiyUKEiQEQXEynnXCvNTOk50dg==` |

**Vendoring into `docs/codebase-site/js/vendor/` remains the preferred
end-state** — it matches the site's self-contained data design and survives a
CDN outage — and is deliberately deferred, not rejected. The blocker is the push
path: the sanctioned `mcp__github__push_files` carries file content through the
model response, and d3 alone is 280 KB, which is exactly the response-budget
truncation hazard CLAUDE.md rule 27 exists to prevent. A session with a
byte-carrying push path can finish it in minutes — download the three URLs
above, check them against those hashes, drop them in `js/vendor/`, and swap the
33 `src=` attributes to the local paths. The deploy already copies
`docs/codebase-site` wholesale, so no workflow change is needed.

Still split, reported not fixed (outside the d3/gsap scope): **KaTeX** —
jsdelivr `0.16.8` on `lp-core.html`, cdnjs `0.16.9` on `policy-scarcity.html`,
neither pinned.

### Other body claims that have since gone stale

- **`offer-curve-grounding.html` no longer exists** on the tree; §1/§3/§4's
  keep-or-link recommendation for it is moot.
- **`backcast-results.html` is a static redirect stub**, not the generated
  dashboard. The live surfaces are `docs/codebase-site/backcast-runs.html` and
  `calibration-status.html`, and `build_manifest.py` now writes only the shared
  data files (`manifest.js`, `benchmark.js`, `completeness.js`, and since Wave
  5C `rubric-consts.js`) — it no longer renders a shell.
- **`scripts/probes/_backcast_shell.py` was deleted**; §2's description of the
  shell text coming from it is historical.
- The deploy's sparse checkout is now `frontend`, `learning-hub`,
  `docs/codebase-site`, `scripts` — §2 predates the codebase-site entry.

**Date:** 2026-06-19 · **Scope:** investigation only — nothing is moved, merged, or
deleted by this document. Every "orphan" and "build path" claim below was verified
by `grep`/file-reference search (commands noted inline); git history was *not* usable
because this checkout is squashed to a single commit.

## TL;DR

The repo serves **one** static site from GitHub Pages, assembled by `deploy-pages.yml`
out of three roots: the loose root `*.html`, `frontend/`, and `learning-hub/`. There are
**four** distinct surfaces in that site, plus **two abandoned/aspirational trees that
nothing links to and the deploy never stages**:

| Surface (live) | Entry | Status |
|---|---|---|
| Landing page | `index.html` | Live, hub of the site |
| Results Dashboard | `frontend/index.html` (+ decisions/parameters) | Live shell, but **data-empty** (no scenarios exported) |
| Learning Hub | `learning-hub/**` | Live, self-contained |
| Backcast Results dashboard | `backcast-results.html` (committed; refreshed at deploy) | Live, the actively-used calibration surface |
| Model Updates | `model-updates.html` | Live changelog |
| Offer-Curve Grounding | `offer-curve-grounding.html` | **Orphan** — deployed but linked by nothing |
| `dashboard/` design system | `dashboard/{js,styles}` | **Orphan** — referenced only by `docs/DESIGN_SYSTEM.md`; no HTML includes it; deploy never stages it |

Two parallel "design systems" exist and **do not share a single file**: the live one is
`frontend/css/style.css` (Plotly/d3, inline-hardcoded nav); the orphan one is
`dashboard/styles/shared.css` + `dashboard/js/*` (Chart.js, JS-injected nav) described by
`docs/DESIGN_SYSTEM.md`. The learning hub uses a third, `learning-hub/shared/scrollytell.css`.

---

## 1. File-by-file purpose

### Root HTML (`*.html`) — staged verbatim by deploy (`cp ./*.html _site/`)

| File | Renders / audience | Links to | Linked from |
|---|---|---|---|
| `index.html` | Site landing page: 4 cards → Results Dashboard, Learning Hub, Backcast Results, Model Updates. General audience. | `frontend/index.html`, `learning-hub/index.html`, `backcast-results.html`, `model-updates.html` | every `learning-hub/*/index.html` (`← Hub`/footer links resolve to `../index.html` = hub, but the hub links back to root via card hrefs); de-facto root of the site |
| `model-updates.html` | Hand-written changelog of model improvements with before/after impact tables (e.g. unit-level outages run31 vs run32). Stakeholder/reviewer audience. | `frontend/index.html`, `backcast-results.html`, `model-updates.html`, `index.html` | `index.html` |
| `offer-curve-grounding.html` | One-off ERCOT deep-dive: 60-Day DAM offers vs run124 offer-curve bands. Calibration/analyst audience. | `frontend/index.html`, `backcast-results.html`, `index.html` | **nothing** (only its own active nav link) — see Orphans |
| `backcast-results.html` | The calibration comparison dashboard. **Committed**, and re-assembled by `build_manifest.py` (the deploy workflow is the single writer that refreshes it on `main`). Calibration audience — this is the team's working surface. | self-assembled; loads `frontend/data/backcast/{manifest,benchmark}.js` + lazy `runs/<id>.js` | `index.html`, `model-updates.html`, `offer-curve-grounding.html` |

Verification: `grep -rn "offer-curve-grounding" *.html` → only `offer-curve-grounding.html`
line 43 (its own `nav-link active`). `backcast-results.html` **is committed** (`git ls-files`
lists it, `git check-ignore` reports it not-ignored): `.gitignore` lines 31–39 are a *comment*
explaining that these generated files (`backcast-results.html`, `manifest.js`, `benchmark.js`)
"ARE committed (so GitHub Pages serves the dashboard even on a raw-branch build, not just the
Actions deploy)", with the deploy workflow as their single writer (pushing via `GITHUB_TOKEN`).

### `frontend/` — the Scenario Results Dashboard (a 3-page SPA-ish static app)

| File | Purpose |
|---|---|
| `frontend/index.html` | Results Dashboard page: scenario picker + year slider → 4 Plotly panels (gen mix, emissions, price-duration, capacity). Loads `js/data-loader.js`, `js/app.js`, `js/charts.js`. |
| `frontend/decisions.html` | Decision-tracker: open build-plan §5 modeling choices, radio options + notes, persisted to `localStorage`. Loads `js/decisions.js`. |
| `frontend/parameters.html` | Parameter citation browser: searchable/filterable table over `data/parameters.json`. JS is inline in the page. |
| `frontend/js/app.js` | Minimal in-memory app state + nav-active detection across the 3 pages. Global `window.App`. |
| `frontend/js/data-loader.js` | Fetches `data/scenarios.json` index + lazy per-scenario result JSON from `data/results/`. Global `window.DataLoader`. |
| `frontend/js/charts.js` | Plotly renderers for the 4 dashboard panels; pulls resource colors live from `css/style.css` custom properties. Global `window.Charts`. |
| `frontend/js/decisions.js` | Decision catalogue + render/persist logic for `decisions.html`. |
| `frontend/css/style.css` | **The live design system** (21 KB): variables, nav, cards, tables, controls. Used by all root HTML, all `frontend/` pages, and the generated `backcast-results.html` shell. |
| `frontend/data/parameters.json` | 516 KB committed citation registry → feeds `parameters.html`. |
| `frontend/data/scenarios.json` | **Placeholder** index (`"scenarios": []`) → the Results Dashboard renders "No scenarios exported yet". Populated by `scripts/export_results.py` (`DEFAULT_INDEX_PATH = frontend/data/scenarios.json`), which has not been run/committed. |
| `frontend/data/results/` | Empty (`.gitkeep` only) — per-scenario result JSON would land here. |
| `frontend/data/backcast/` | Backcast dashboard's committed parts: `registry/<id>.json` sidecars, `runs/<id>.js` payloads, `bench/<ISO>/<year>.json.gz`. ~40+ registered runs present. The generated `manifest.js`/`benchmark.js` here are **also committed** (refreshed only by the deploy workflow, never hand-committed by calibration runs). |
| `frontend/js/.gitkeep`, `frontend/css/.gitkeep`, `frontend/data/.gitkeep` | placeholders |

### `learning-hub/` — scrollytelling explainers (self-contained)

| File | Purpose |
|---|---|
| `learning-hub/index.html` | Hub landing: 5 cards → the 5 explainers. Links back to root via the explainers' framing. |
| `learning-hub/{lp-dispatch,capacity-evolution,storage-cooptimization,transmission-pricing,scenario-uncertainty}/index.html` | The 5 scrollytelling stories. Each links `../index.html` (hub) in its `← Hub` + footer. Uses d3 + Google Fonts + `../shared/scrollytell.{css,js}`. |
| `learning-hub/shared/scrollytell.css` / `scrollytell.js` | Shared scrollytelling engine + styling for all 5 stories (the hub's own design system). |

Verification: `grep "<script\|<link" learning-hub/**/*.html` → every story links only
`shared/scrollytell.*`, d3 CDN, Google Fonts. **No** reference to `frontend/css/style.css`
or to `dashboard/`.

### `dashboard/` — orphaned design-system component library

| File | Intended purpose (per `docs/DESIGN_SYSTEM.md`) | Actual use |
|---|---|---|
| `dashboard/styles/shared.css` | "Single source of truth for ALL visual styles… every page links to this file" (53 KB, Chart.js-oriented, `.header`/`.chart-panel`/etc). | **Referenced by no HTML.** |
| `dashboard/js/nav.js` | JS-injected shared nav bar / mega-menu. | none |
| `dashboard/js/shared-header.js` | Injects SVG/canvas waveform header banner. | none |
| `dashboard/js/canvas-banners.js` | Canvas header-banner variants for `shared-header.js`. | none |
| `dashboard/js/chart-colors.js` | `RESOURCE_COLORS`/`ISO_COLORS`/`SEMANTIC_COLORS` constants for Chart.js. | none |
| `dashboard/js/scroll-observer.js` | Scroll fade-in observer. | none |
| `dashboard/js/shared-footer.js` | JS-injected shared footer. | none |

Verification: `grep -rn "dashboard/(js|styles)"` → **only** `docs/DESIGN_SYSTEM.md`.
`grep -rn "nav.js|shared-header|chart-colors|canvas-banners|scroll-observer|shared-footer|shared.css"`
→ matches only inside `dashboard/` itself (self-references) and `docs/DESIGN_SYSTEM.md`.
The live pages all hardcode their `<nav>` inline and link `frontend/css/style.css`, not these files.
`DESIGN_SYSTEM.md` also cross-references `PIPELINE.md`, `SPEC.md`, `CLAUDE.md` — **none of
which exist** (the repo's instructions file is lowercase `claude.md`), reinforcing that this
tree documents an architecture the live site never adopted (Chart.js vs the live Plotly/d3).

---

## 2. Build / deploy path per surface

There is **one** publish pipeline: `.github/workflows/deploy-pages.yml` (GitHub Pages).
Triggers: push to `main` touching `*.html`/`frontend/**`/`learning-hub/**`/the workflow, plus
`workflow_run` chaining off "Calibration run" / "Bulk-merge auto runs". Steps:

1. **Sparse, blobless checkout** of only `frontend`, `learning-hub`, `scripts` (cone mode also
   pulls root files like `index.html`). The ~GB of model bundles/inputs are never downloaded.
2. **Stage:** `cp ./*.html _site/`; `cp -r frontend _site/`; `cp -r learning-hub _site/`; `touch _site/.nojekyll`.
3. **Assemble backcast dashboard:** `python3 scripts/build_manifest.py --site-dir _site` → writes
   `_site/backcast-results.html` + `_site/frontend/data/backcast/{manifest,benchmark}.js`.
4. Configure Pages → upload `_site` → deploy.

Consequence — **`dashboard/` is *not* in the sparse-checkout list and is *never* copied into
`_site`.** Even if something linked it, it would 404 in production. The deploy path confirms the
orphan status structurally, not just by link-graph.

Per-surface build path:

| Surface | How it gets to the live site |
|---|---|
| `index.html`, `model-updates.html`, `offer-curve-grounding.html` | Committed static HTML → copied verbatim (`cp ./*.html`). No build. |
| `frontend/` Results Dashboard | Committed static HTML/JS/CSS → copied. Data is **expected** from `scripts/export_results.py` writing `frontend/data/scenarios.json` + `frontend/data/results/*.json`; that step is unrun, so the dashboard is live-but-empty. |
| `learning-hub/` | Committed static HTML/JS/CSS → copied. No build. |
| `backcast-results.html` | **Generated at deploy** by the stdlib-only `scripts/build_manifest.py`, which reduces the committed `frontend/data/backcast/{registry,runs,bench}` parts into `manifest.js`/`benchmark.js` + the shell (shell text from `scripts/probes/_backcast_shell.py`, styled with `frontend/css/style.css`). The three shared files are committed but refreshed only by the deploy workflow (single writer); conflict-free because each calibration run only ADDs its own namespace files (`registry/<id>.json`, `runs/<id>.js`, `bench/` parts). |

Supporting scripts (read for this audit):

- `scripts/build_manifest.py` — **the CI reducer.** stdlib-only, no model deps/bundles. Unions
  per-ISO bench metas, merges year payloads, lists runs whose payload exists, writes the 3 shared
  files. Used both at deploy (`--site-dir _site`) and locally (repo-root preview).
- `scripts/regen_dashboard.py` — **local heavy full rebuild.** Globs every registry sidecar and
  re-renders the whole set via `render_backcast.generate` (needs every bundle + the model package).
  "CI never runs it." For full refreshes after relabel/schema change.
- `scripts/render_backcast.py` — generator behind `regen_dashboard`: writes the deployable
  JSON-driven shell + the gzip+base64 `runs/<id>.js`, `bench/<ISO>/<year>.json.gz` parts. Defines
  the "newest bundle covering the year wins" rule and the committed-but-deploy-refreshed-files
  contract (the three shared files are committed; only the deploy workflow rewrites them).
- `scripts/dashboard_add_run.py` — registers a **single** new run (sidecar + payload + bench part);
  the everyday "add to dashboard" path (per `claude.md` rule 13 / `calibration-report` skill).
- `scripts/render_calibration_html.py` — **separate, standalone** self-contained calibration report
  (no external JS/CSS, everything embedded). Writes a one-off `--out FILE`. **Not** part of the Pages
  deploy and **not** the deployable `backcast-results.html` (its own docstring contrasts itself with
  "the deployable, JSON-driven backcast dashboard"). Referenced by `docs/calibration-report.md`,
  `tools/launcher.py`.
- `scripts/export_results.py` — would populate the `frontend/` Results Dashboard data (unrun).

---

## 3. Overlap / duplication & orphans

### Overlap between `frontend/` and `dashboard/`

**No file is shared.** The two trees are *divergent*, not duplicated copies — they implement the
same *concepts* with incompatible stacks:

| Concern | `frontend/` (live) | `dashboard/` (orphan) |
|---|---|---|
| CSS | `frontend/css/style.css`, 21 KB | `dashboard/styles/shared.css`, 53 KB |
| Nav | hardcoded inline `<nav>` in every page | JS-injected `dashboard/js/nav.js` |
| Chart colors | CSS custom properties read live in `charts.js` | JS constants `dashboard/js/chart-colors.js` |
| Charts | Plotly + d3 (CDN) | Chart.js (per `DESIGN_SYSTEM.md`) |
| Header banner | none | SVG/canvas via `shared-header.js`/`canvas-banners.js` |

So the "duplication" is conceptual (two answers to nav/colors/styling), and only the `frontend/`
answer is wired into anything. There is **no drift to reconcile in shipped code** because
`dashboard/` ships nowhere.

### Orphans (referenced by nothing live, and/or never built/staged)

1. **`dashboard/` (entire tree: 6 JS + 1 CSS).** Referenced only by `docs/DESIGN_SYSTEM.md`; no
   HTML includes it; not in the deploy sparse-checkout; never copied to `_site`. Strongest orphan.
   `docs/DESIGN_SYSTEM.md` itself points at non-existent `PIPELINE.md`/`SPEC.md`/`CLAUDE.md`.
2. **`offer-curve-grounding.html`.** Deployed (it's a root `*.html`) but **linked from nothing** —
   no nav anywhere points to it; it's reachable only by typing the URL. Self-contained one-off.
3. **`frontend/` Results Dashboard data path is dormant** (not an orphan file, a dormant feature):
   `scenarios.json` is a placeholder and `data/results/` is empty, so `frontend/index.html` shows
   "No scenarios exported yet". The page, `app.js`, `charts.js`, `data-loader.js` all ship but have
   nothing to render until `export_results.py` is run and its output committed.

(Not orphans, for the record: `model-updates.html`, `frontend/{decisions,parameters}.html` and their
JS, all of `learning-hub/`, and every `frontend/data/backcast/**` part are reachable and/or consumed.)

---

## 4. Recommended consolidation (recommend only — execute nothing)

### Retire

- **`dashboard/` (whole tree) + `docs/DESIGN_SYSTEM.md`.** Nothing links it, the deploy can't serve
  it, and it documents a Chart.js architecture the site never adopted. Retiring removes a misleading
  "single source of truth for ALL styles" that contradicts the actual one (`frontend/css/style.css`).
  - *Risk / before acting:* (a) Confirm no in-flight branch/PR is mid-migration onto this design
    system (this checkout is squashed, so history can't prove it — check open PRs). (b) `chart-colors.js`
    and the canonical color tables in `DESIGN_SYSTEM.md` are the most reusable assets; if any future
    Chart.js work is planned, preserve those color constants (e.g. fold the hex table into
    `style.css`/a doc) before deleting. (c) It's the only place some ISO/resource hexes are written
    down — grep `RESOURCE_COLORS`/`ISO_COLORS` consumers (currently none) before removal.

### Decide (keep-or-retire) — needs a human call

- **`offer-curve-grounding.html`.** Either (i) **keep + link it** (add a nav entry from
  `model-updates.html`/`index.html` so it's discoverable, matching its siblings), or (ii) **retire**
  it if it was a single-use analysis now captured in `docs/ercot-dam-offer-grounding-2026-06.md`
  (which it cites). Recommendation: **link it** — it's polished, deployed, and complements the
  backcast surface; orphaning a finished page is the worse outcome.
  - *Risk:* it pins specific run124 numbers; if kept, it needs a "snapshot as of run124" note so it
    isn't read as current once offer curves are re-derived (the page itself flags a gated re-derivation).

- **`frontend/` Results Dashboard (index + app.js/charts.js/data-loader.js + scenarios.json/results).**
  Either **activate** (run/commit `export_results.py` output so the forecast dashboard actually
  renders) or **demote** the card on `index.html` until it has data. Recommendation: **keep, but
  hide/label the landing-page card** as "coming soon" until `scenarios.json` is populated, so the
  live site doesn't advertise an empty page.
  - *Risk:* the landing page currently sells four destinations; one silently dead-ends. Low-effort fix
    is the card label; the real fix is the data export.

### Keep as-is

- **`index.html`, `model-updates.html`** — live, linked, correct.
- **`backcast-results.html` generation chain** (`build_manifest.py` at deploy; `dashboard_add_run.py`
  to add runs; `regen_dashboard.py`/`render_backcast.py` for local full rebuilds). This is the mature,
  conflict-free, well-documented surface; no change recommended.
  - *Risk if touched:* the deploy-refreshed-shared-files + per-run-additive-parts contract is what gives
    concurrent calibration sessions zero merge conflicts (`claude.md` rule 13). The three shared
    files (`manifest.js`/`benchmark.js`/`backcast-results.html`) are committed but must never be
    *hand*-committed by a calibration session — only the deploy workflow refreshes them — and the
    per-run parts must not be moved.
- **`learning-hub/`** — self-contained, linked, its own `scrollytell.*` design system. Leave it on its
  own CSS; **do not** try to merge it into `frontend/css/style.css` (different visual language, and
  it's working). The one consolidation worth noting is purely conceptual — three CSS systems exist
  (`style.css`, `scrollytell.css`, the orphan `shared.css`); retiring `shared.css` reduces that to the
  two that are actually load-bearing.

### Net effect of the recommendation

Retiring `dashboard/` + `DESIGN_SYSTEM.md`, resolving `offer-curve-grounding.html` (link it), and
labeling/activating the Results Dashboard would leave a site with **one** live design system
(`frontend/css/style.css`) for the landing/results/changelog/backcast surfaces and **one** for the
learning hub (`scrollytell.css`), every deployed page reachable, and no tree that the pipeline can't
serve — with **no behavioural change to the calibration dashboard**, which is the surface in active use.
