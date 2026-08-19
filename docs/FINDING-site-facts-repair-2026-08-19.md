# FINDING — codebase-site factual repair (WS5 Job 1, pre-G3)

**Session:** `claude/site-facts-repair-f3tkm1`, 2026-08-19.
**Charter:** `docs/model-audit-release-plan-2026-08.md` §0/§3 WS5 (SITE); AUDIT-A gap-register row S1.
**Scope:** statements on `docs/codebase-site/` that are **factually false at HEAD** and would still be
false after G3. Not SITE-A (plan §7.6) — no restructure, no signed-disposition work.

**This is not a style pass.** Every number and claim touched below was re-derived from
`src/market_sim/`, `scripts/`, or committed data under `frontend/data/backcast/`. Where a defect
needed a judgement about *presentation* rather than *fact*, it was left and is listed in §4.

---

## 0. Headline

Twelve of the repairs are ordinary staleness. **Three are governance-grade** and are broken out in
§2 — the worst asserted, on the Model Validity page, that a **locked-test holdout year had been
scored and stood**. It had not. No ISO has ever spent one, and that specific claim had already been
corrected on the record by owner decision D-23 on 2026-08-06; the site never followed.

---

## 1. Repairs, with the source each was verified against

### 1.1 `index.html`

| Was | Is | Source |
|---|---|---|
| `7` ISOs — "…NYISO, NEISO, **SPP**" | `6` ISOs, SPP removed | `iso_configs.py:1204-1217` — `_ISO_BUILDERS` has exactly six entries and `SUPPORTED_ISOS` is that tuple. SPP occurs only in MISO seam comments (`:557`, `:630-639`) as an external contract path the model *wheels across*, and in `paths.py:221` where "SPP" is ERCOT's **Settlement Point Price** — a different noun entirely. |
| "Seven ISOs, 34 zones, 50+ transmission links" | "Six ISOs, 37 zones (34 carry load), 46 transmission links" | Counted over the six builders (§3 for the convention). **50+ was never true.** |
| "Ten pages, 26 visualizations" | "Sixteen pages, 19 visualizations" | 22 `.html` files − `index.html` − 5 data-driven dashboards = 16 narrative pages. 19 `viz-*.js` modules are included by a page (21 exist; two are orphaned — §5). |
| "Twelve pages built around the narrative arc" | "Ten pages … plus three live dashboards" | The Explore section shows the 01–10 numbered arc plus three unnumbered Backcast dashboard cards. The two counts contradicted each other **in the same file**; each now states what it counts. |
| "P0→P1→P2 three-solve sequence" (card + system-diagram tooltip) | two-solve | §1.7 |

### 1.2 `network.html` + `js/iso-configs-table.js`

| Was | Is | Source |
|---|---|---|
| stat cards "32 Total zones", "38 Transmission links" | 37 / 46 | Counted from the config. (Its ISO count was already right at 6.) |
| CAISO simultaneous import cap **8,300 MW** (4 places) | **7,500 MW** | `iso_configs.py:500-509`, `InterfaceLimit(name="WECC_import_simultaneous", cap_mw=7500.0)`. 8,300 is the naive published figure the config comment explicitly steps *down* from ("the p01 extreme rarely sustains across both corridors simultaneously"). |
| `SP15` (4 places) | `SP15_rest` | The caiso-172 split replaced SP15 with LA_BASIN / SDGE / SP15_rest and re-pointed Path 46 (West-of-River) onto SP15_rest. |
| interface table: CAISO the only ISO with aggregate limits; "ERCOT, **MISO**, PJM, NYISO, **NEISO** — no aggregate interface limits modeled" | MISO and NEISO rows added; footer now names ERCOT, PJM, NYISO only | MISO has **five** per-zone CIL/CEL groups (asymmetric, 6,025–9,635 MW in / 3,991–10,330 MW out); NEISO has `HQ_import_simultaneous` at 3,850 MW over three paths. |
| CAISO "NP15, ZP26, SP15"; MISO "Three regions (North/Central/South)"; NEISO "Five zones **plus** HQ import node" | corrected | The NEISO phrasing counted six — `HQ_import` is one of the five. |

### 1.3 `data/iso-topologies.json` — re-serialized

The Network page's topology data had drifted from the config since its 2026-06-29 serialization, so
the page **rendered a topology the model does not have**:

```
ERCOT  zones 7 -> 7   links  9 -> 10   interface limits 0 -> 0
CAISO  zones 4 -> 6   links  4 ->  6   interface limits 1 -> 1
MISO   zones 3 -> 6   links  3 ->  8   interface limits 0 -> 5
PJM    zones 8 -> 8   links 11 -> 11   interface limits 0 -> 0
NYISO  zones 5 -> 5   links  4 ->  4   interface limits 0 -> 0
NEISO  zones 5 -> 5   links  7 ->  7   interface limits 0 -> 1
```

This file is **committed static data for a narrative page** — not a dashboard surface, not
deploy-generated — and its own `_meta` declares the contract used here: *"Serialized from the live
config in `src/market_sim/config/iso_configs.py`; re-serialize if `iso_configs.py` changes."*
Schema held byte-for-byte: no field added or removed. The regenerated totals (37 / 34 / 46)
reproduce §1.1's counts **derived independently**, which is the cross-check that they are right.

### 1.4 `calibration-rubric.html` — rubric version currency

| Was | Is | Source |
|---|---|---|
| `RUBRIC_VERSION = 3.1` | `3.4` | `scripts/calibration_verdict.py:346` |
| "`CALIBRATED` iff there are *zero* caveats **of any kind**" | zero *downgrading* caveats | `calibration_verdict.py:2686-2688` counts `protective + band` only. Under **v3.3** a ledgered caveat (only C3c is ledgerable) is reported at full magnitude without downgrading. |
| v3.1 badged **current** | v3.2 / v3.3 / v3.4 entries added, badge moved to v3.4 | `docs/calibration-determination-rubric.md` §9 |
| page title / meta: "the v2.x rubric" | v3.x | — |
| `frontend/data/backcast/keepers.json` (`frontier` map) | `keepers/<ISO>.json` (per-ISO `frontier` block) | **The cited file does not exist** — the map was sharded per ISO. |

### 1.5 `scarcity-deep-dive.html`

"Keeper `2026-07-23-ercot100-netrev-margin-keeper`, unchanged" was a present-tense claim. ERCOT's
keeper at HEAD is **`2026-08-17-ercot215-arm-decontam`** (`frontend/data/backcast/keepers/ERCOT.json`).

The page's *numbers* are a faithful record of the ercot107-108 probe against the
`ercot_netrev_margin` bundle and are left as that record; the caption now names which keeper the
analysis ran against, names the current one, and says the analysis has not been re-run. **This
matters here specifically:** ercot215 deliberately re-exposed the 2023 C3a/C3b price misses that
earlier ERCOT keepers were carrying, so this page's 2023 scarcity figures are *not* the current
keeper's behaviour. Re-running the probe against ercot215 is a calibration-lane call, not this
lane's — see §4.

### 1.6 `results-calibration.html` — the retired ablation twin

The page presented the **zero-forcing ablation twin** as a live keeper obligation. Rule 21
`[R-DOF]` was amended by the owner on **2026-07-14**: the twin is no longer required and no keeper
builds or registers one.

- *"Both are required of every keeper under CLAUDE.md rule 21 ('Every keeper carries a DOF ledger
  **and an ablation twin**')"* — the rule text no longer contains the twin.
- *"today all current keepers carry registered twins"* — **none does.** No `ablation_twin` key
  appears in any of the six keeper shards.
- E9 was described as failing a keeper that *lacks* a resolvable twin link.
  `audit_keepers.py:105-110` + `ablation_twin_finding()` say the opposite: a keeper with no link
  can never FAIL E9; only a **declared-but-dangling** link fails. The grandfather list was deleted
  with the requirement.

The section is kept behind a `Retired 2026-07-14` badge and a status paragraph rather than removed —
its mechanics are still accurate about the code, and the twins already on the dashboard were
produced this way. *Whether it should stay at all is §4.*

The rule-numbering footnote was refreshed to quote the current rule text and to point at the stable
`[R-*]` IDs and `docs/governance/rule-history.md`. **Its `audit rule 20 = CLAUDE.md rule 21` mapping
was checked and is correct** — that footnote was right and stays.

### 1.7 P2 — "the three-solve sequence" (4 pages)

`index.html`, `mental-model.html`, `lp-core.html` and `solving-pricing.html` all presented **P2 as a
live third solve and an available option**. At HEAD, P0 and P1 are the only two passes; P1 is the
production/forecast path and what every run is scored on. P2 is **archived**:
`run_calibration_full.py::_enforce_legacy_p2_gate` (`:8072`) hides its flags from `--help` and
hard-errors on any of them unless `--enable-legacy-p2` is passed — its own docstring: *"so P2 is
never a silent calibration option."* No keeper uses it.

Fixed: "Why Three Solves?", "Three passes break this circularity", the **"3 LP solves per
ISO-year"** stat, "P2 inherits P1's" basis, "P1 and P2 are cached separately", the meta
description, the index card + tooltip, and `lp-core`'s three `P0→P1→P2` references. `mental-model`
had said the P2 screen "is off by default" — that **understates** it; off-by-default reads as a
supported option you may switch on. The pass table keeps its P2 row, marked archived, with a
callout naming the gate and the three **P1-native commitment bridges** that carry live commitment
structure into P1 as a `min_gen` floor at the P0→P1 seam.

---

## 2. GOVERNANCE-GRADE — read this section

Three claims were not staleness. They misstated the holdout program's *state* in the direction that
flatters the model, on the page whose entire subject is out-of-sample discipline.

### 2.1 The site claimed a locked-test year had been spent. None ever has. 🔴

`model-validity.html` §4, "Current state", asserted verbatim:

> Only **NEISO** carries a complete marker (declared 2026-07-07); **its 2019 + H1-2026 one-shot was
> scored once with the then-frozen `neiso-53` config and stands.**

**Both halves are false, and the second is the serious one.** `calibration-complete.json`'s `final`
block carries only its `_note` — it is deliberately empty, and **no locked-test year has ever been
solved, scored or registered for any ISO.** NEISO's locked test is **NEVER GRANTED**, not spent.

This is not a new discovery. It is exactly the claim **owner decision D-23 corrected on
2026-08-06**: the artifact record carries no NEISO 2019 or H1-2026 solve of any kind, every NEISO
registry sidecar ever committed declares years drawn only from {2022, 2023, 2024, 2025},
`bench/NEISO/` holds 2022–2025, `actual_tail.json` has no 2019 row to score against, and
`2026-07-07-neiso53-winter-fuelsec-coldsnap` — the config named as the frozen one-shot — is a
**train-tier 2023–2025 config**. The correction is recorded in `calibration-complete.json`
(`final._note`, `locked_test_scored_on_WITHDRAWN`), in `holdout-freeze.json`, and in CLAUDE.md rule
22. **The site was never updated, so a reader of the public site would have concluded the model had
a certified out-of-sample result that does not exist.**

Figure MV2's caption carried the same claim independently ("as of 2026-07-11 only NEISO has a
calibration-complete marker and an actually-scored one-shot").

Repaired by *stating the correction explicitly* rather than silently swapping the text, so the page
now carries the same disclosure the JSON does.

### 2.2 The freeze was invisible. 🔴

Nothing on the site mentioned `frontend/data/backcast/holdout-freeze.json`, which is **`active:
true`** and is checked **before** the marker, failing closed. While it stands, **no out-of-training
year is spendable for any ISO — validation tier included, marker or not.** A reader could reasonably
have concluded that the three `complete` ISOs were free to spend 2022 today. They are not. Added to
§4 of `model-validity.html`.

### 2.3 Marker state was wrong on two pages. 🟠

`complete` at HEAD holds **NEISO** (2026-07-07), **NYISO** and **PJM** (both 2026-07-31); CAISO's
was withdrawn 2026-08-06.

- `model-validity.html` listed **NEISO only**, and pilled PJM and NYISO as "quarantined".
- `calibration-rubric.html` listed **NEISO only** for `complete`, and — in the other direction —
  said *"NYISO carries a frontier designation but **no** complete marker."* **Both halves are
  backwards at HEAD:** NYISO holds `complete` and has **no** frontier (withdrawn 2026-07-19).
  Frontier at HEAD is **NEISO + PJM**; ERCOT's was removed 2026-07-26. The paragraph was rewritten
  so NYISO illustrates the orthogonality it now actually demonstrates, and the NYISO frontier bullet
  replaced with PJM's own basis — PJM reached the label by a *different route* (lever queue
  exhausted with **every criterion passing**), so the shared "the residual is the C3c tail" framing
  was itself wrong.

### 2.4 Two further holdout-rule misstatements (same page)

- *"Intake … under explicit, session-logged owner authorization."* Rule 22 as amended **2026-08-06**
  requires **no** per-ISO or per-window grant and no marker: *what is held out is the score, never
  the data or the architecture.* The amendment explicitly records the former per-window regime as
  having had it backwards. **Conflict noted:** `holdout-freeze.json`'s own prose still says intake
  "remains permitted under session-logged owner authorization" — that file predates the amendment
  and now disagrees with the governing rule. **Not repaired here** (it is committed governance data,
  not site content); flagged in §4 for the governance lane.
- *"quarantined until that ISO carries a `calibration-complete` marker. **Even then, only the
  frozen-config one-shot is permitted.**"* The tiers carry **separate** markers since 2026-07-31
  (`holdout_policy.TIER_MARKER_BLOCK`: validation → `complete`, locked → `final`), and a validation
  year is **iterable**, not a one-shot. Only the locked test is touch-once.
- The insight box claimed *"the CI gate is tier-agnostic … the validation-vs-locked distinction is
  deliberately **not** machine-enforced."* It **is** enforced:
  `enforce_holdout_year_gate` (`run_calibration_full.py:7981-8071`) resolves the tier through
  `holdout_policy.tier_for_year` and demands that tier's marker, failing closed. What genuinely
  stays discipline is the **spend history** — CI checks the grant, not whether a one-shot was
  already used — and the box now says that instead.
- Validation tier listed as "2022 (ladder → 2020–2022 → **earlier**)". `VALIDATION_YEARS` is
  `{2020, 2021, 2022}`; the ladder **bottoms out at 2020**, and 2018-and-earlier are dropped,
  falling through `tier_for_year`'s fail-closed default to locked-test tier.
- "The **two** logged intakes to date" — `intake_log` has **17** entries.

Source line numbers in that section were also stale (the gate was cited at `:5217`/`:5221-5267`;
it lives at `:7969`/`:7981-8071`) and were refreshed.

---

## 3. Conventions I had to choose, stated

**Zones.** The config defines **37** `Zone` objects, of which **34** have `load_share > 0`. The three
that do not are ERCOT `Panhandle` (a generation pocket), CAISO `WECC_import` and NEISO `HQ_import`
(import nodes). Both numbers are defensible; the site now says **"37 zones (34 carry load)"** so the
reader does not have to guess. This also reconciles the old "34 zones" — that figure was right under
the load-carrying convention and wrong only in being unlabelled. It matches `viz-iso-topology.js`'s
own stat bar, which already counted "N load zones".
*CLAUDE.md's prose ("CAISO 3 zones + WECC import node") is itself stale — CAISO has 5 load zones
plus the import node. Not corrected here: CLAUDE.md is out of this lane's scope.*

**Links.** 46 `TransferLink` objects. Counted twice — statically via `ast` and by importing the
config — with identical results, then a third time by the re-serialized JSON.

**Pages.** Narrative pages = all `.html` under `docs/codebase-site/` **excluding** `index.html`
(a hub) and the five data-driven dashboards (`backcast-runs`, `calibration-status`,
`forecast-runs`, `forecast-status`, `mechanism-matrix`). **Dashboards do not count as narrative
pages** — they render from generated data and are explicitly outside this lane. That gives 16.

**Visualizations.** = `viz-*.js` modules actually included by a page: **19**. The site has no
consistent figure convention to count instead (only 5 pages use `<strong>Figure` labels at all,
and `.fig` blocks appear on 9 of 16 pages while `lp-core.html` draws its diagrams in pure CSS), so
this is the one mechanically verifiable definition available.

---

## 4. Deferred — SITE-A or another lane

1. **`forecast-validation.html` is not in `nav.js`** — orphaned, reachable only by direct URL. This
   is a signed §7.6 SITE-A disposition ("forecast-validation.html → nav"). **Left alone.**
2. **`model-updates.html` → pointer** — signed §7.6 disposition. Untouched (the file is not present
   under `docs/codebase-site/`).
3. **`scarcity-deep-dive.html` has not been re-run against ercot215.** Its figures are the
   ercot107-108 probe's record. Re-running is a *calibration-lane* decision (it needs a solve or at
   minimum a re-read of ercot215's sidecars); the page now says so rather than implying currency.
4. **Whether the ablation-twin section should exist at all.** It documents a retired obligation. Now
   correctly labelled; deleting or shrinking it is a presentation call.
5. **`solving-pricing.html` section 2 is still built around a `P0 → P1 → P2` walkthrough** with a
   3-panel animation (`viz-p012-sequence.js`). Section 1 now states plainly that P2 is archived, so
   the page is not misleading, but restructuring that walkthrough (and the viz) to a two-pass
   narrative is SITE-A's.
6. **`config-reference.html`'s P2 field descriptions** ("Master gate for P2 optional commitment
   screen") are left: those `ScenarioConfig` fields still exist and the descriptions are accurate
   *about the fields*. Whether the page should mark them archived is a presentation call.
7. **`calibration-rubric.html` is still written to a v3.1 skeleton.** The false constants, the
   determination rule and the version history are repaired, but a full re-read of the page against
   v3.4 was not in scope.
8. **`holdout-freeze.json`'s intake clause contradicts CLAUDE.md rule 22** as amended 2026-08-06
   (§2.4). Governance data, not site content — for the governance lane.
9. **`GEO_HINTS` seed positions.** §5.

---

## 5. Also found, not acted on

- **`js/viz-sankey.js` and `js/viz-sparsity.js` are orphaned** — present in `js/` but included by no
  page. `data-pipeline.html` and `lp-core.html`, the pages they were presumably written for, draw
  their figures inline instead. Dead code, not a false claim.
- **The one layout call I made.** Re-serializing the topology data introduced 8 zones with no
  `GEO_HINTS` entry in `viz-iso-topology.js`; unseeded nodes all start stacked at the canvas centre
  (`x: W/2, y: H/2`), which would have been a visible regression. Seeds were placed on the real
  state geography the config docstrings name (MISO-West = MN/ND/SD/MT, Plains = IA/MO, Illinois =
  IL, Indiana = IN/KY, East = WI/MI, South = AR/LA/MS/E-TX; the CAISO three north-to-south down
  SP26), and the dead `SP15`, `MISO-North`, `MISO-Central` seeds deleted. Verified: every zone in
  every ISO has a seed and no seed names a zone that no longer exists. **This is the only
  presentation judgement in the lane** — flagged so SITE-A can revisit the placement.

---

## 6. Verification

**Nothing data-driven was touched.** No edit went near `backcast-runs.html`,
`calibration-status.html`, `forecast-runs.html`, `forecast-status.html`, `mechanism-matrix.html`,
their generated manifests (`manifest.js` / `benchmark.js` / `completeness.js`), the forecast
namespace, or any mechanism-matrix shard.

**Dead links:** swept every `href="*.html"` across all 22 pages — **none broken**. Swept every
`<code>`-quoted repo path — the only dead one was `keepers.json` (§1.4, fixed); the rest resolve
(`data/*.json` are site-relative, `data/clean/` is gitignored-derived, `data/floor_mechanisms.py` is
the page's usual shorthand for `src/market_sim/data/`).

**Accessibility (skill: `accessibility-audit`):** every element introduced this session sits in a
`.section-light` section — checked by walking back to the nearest enclosing `<section>` for each
insertion — so the site's characteristic dark-section token trap does not apply to any of them.
Measured contrast, all **PASS** at WCAG AA (4.5:1 for normal text):

| Element | Ratio |
|---|---|
| `--text-muted` #566370 on `--bg-page` / `--bg-card` | 5.84 / 6.15 |
| MISO badge #C2410C on its tint (new row) | 4.58 |
| NEISO badge #7E22CE on its tint (new row) | 5.77 |
| CAISO badge #B45309 (pre-existing control) | 4.58 |
| `.rs-badge.st-caveat` #92400E | 5.96 |
| `.iso-pill.complete` #166534 | 6.21 |
| `.insight-box.warn` body / title | 13.04 / 6.32 |
| `Retired` + `archived` muted badges on the table row tint | 5.89 |

A scan of all nine edited pages for light-theme colour tokens used inside a `.section-dark`
returned **zero** hits. No regressions introduced.

**Rendering:** all nine edited pages were validated for HTML well-formedness (zero unclosed tags,
zero mismatches), both edited JS files pass `node --check`, and all nine were loaded in Chromium off
a local server: **zero page errors, zero local 404s, nav and content present on every one.**

The regenerated topology was then *exercised*, not just loaded. The sandbox blocks the browser's CDN
requests, so on the first pass d3 never loaded and `viz-iso-topology.js` never ran — the check that
mattered most was the one not being made. Re-run with the CDN assets fetched and served locally, the
topology viz renders per-ISO zone circles:

```
ERCOT 7    CAISO 6    PJM 8    MISO 6    NYISO 5    NEISO 5      (= 37)
```

which is the config's own per-ISO zone count, ISO for ISO — CAISO now drawing 6 where it drew 4 and
MISO 6 where it drew 3. Every ISO tab was clicked and re-rendered. The only remaining console error
on any page is the sandbox blocking `fonts.googleapis.com`, which is environmental and unrelated to
these changes.

**Rule 27 `[R-PUSH]`:** every push was byte-verified — the pushed blob fetched back and its line
count and SHA-256 compared to the local file — before the next commit. All matched. No file was
regenerated from model output; every edit was a targeted local `Edit`.
