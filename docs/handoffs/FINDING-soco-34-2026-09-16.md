# FINDING — SOCO-34: SOCO wired into the site, the nine-region surface closed, and two accent-agnostic WCAG fixes

**Lane** SOCO-34 · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-16 ·
**Branch** `claude/soco-34-site-docs-pxkmb5` · **Base** `edd409434ea9c77e8a5bbf9f95c0ed70417aab2f`
(= `origin/main` at launch) · **Data profile** `code` · **Solves** none (zero-LP lane).

## 0. THE COUNT, AND THE `index.html` ARITHMETIC THE CHARTER ASKED FOR

The charter told me to CHECK whether `index.html`'s "47 zones" already counts SOCO's three and not to
assume either way. **It does. `index.html:297` needed no change.** Recomputed twice, independently:

| | zones | carry load | links |
|---|---:|---:|---:|
| the seven prior regions | 39 | 36 | 47 |
| **+ NWPP** | 5 | 5 | 9 |
| **+ SOCO** | 3 | 3 | 2 |
| **nine regions** | **47** | **44** | **58** |

`39 + 5 + 3 = 47` · `36 + 5 + 3 = 44` · `47 + 9 + 2 = 58`. The committed line already reads
"Nine regions, 47 zones (44 carry load), 58 transmission links", so NWPP-35 had already counted SOCO
into the prose *before* SOCO's data block existed — the prose ran ahead of the data by two days, and
this lane closed the gap rather than moving a number.

Measured two ways so the agreement is not one function trusted twice: (1) summing `get_iso_config` over
`SUPPORTED_ISOS`, and (2) re-summing the **committed `iso-topologies.json` after my edit**. Both give
47 / 44 / 58. The nine-region set is `ERCOT CAISO MISO PJM NYISO NEISO SPP NWPP SOCO`; `len(SUPPORTED_ISOS) == 9`.

**The two orderings cross, and both are correct.** NWPP is the **eighth builder** (merged first on
2026-09-14) but the **ninth matrix column**; SOCO is the **ninth builder** but the **eighth matrix
shard** (SOCO-21 landed 2026-09-13, a day before NWPP's). That is why SOCO's lever queue is
`docs/mechanism-testing-matrix.md` **§5.8** and NWPP's is §5.9 — I verified this against the file
rather than inferring it, having first written "§5.10" from memory and caught it.

## 1. EVERY FILE CHANGED — before → after

| file | before | after |
|---|---|---|
| `docs/codebase-site/data/iso-topologies.json` | 8 region blocks; `_meta.description` said *"eight are serialized here. SOCO registered the same day as NWPP and its block is owed by the SOCO desk's own site lane, not by this one."* | **NEW `SOCO` block** appended last in builder order — 3 zones (shares summing to exactly 1.000000), 2 links, `voll: 61900.0`, `interface_limits: []`. `_meta` rewritten: nine serialized, the 47/44/58 totals, the not-an-ISO statement, SOCO's non-$2,000 VOLL and the Tier-3/fallback caveats. The eight existing blocks are **byte-unchanged**. |
| `docs/codebase-site/data-completeness.html` | `ISOS` list of 9; comment said SOCO's entry *"is owed by that program's own site lane and is deliberately not added here"* | `ISOS` list of **10** (`all` + 9 regions); comment rewritten, and it now states plainly that selecting any post-census region shows an empty table — *"that is the honest state, not a rendering fault"* |
| `docs/codebase-site/config-reference.html:404` | "…carries nine registered regions; **the eight** serialized into `iso-topologies.json` render below." | "…carries nine registered regions, and **all nine** are now serialized … — 47 zones, 44 of them carrying load, over 58 transmission links" + the NWPP-pool / SOCO-single-BA statement |
| `docs/codebase-site/index.html:297` | "Nine regions, 47 zones (44 carry load), 58 transmission links." | **UNCHANGED — already correct.** See §0. |
| `docs/codebase-site/js/viz-iso-topology.js` | `ISO_ORDER` 8; no SOCO colour; no SOCO `GEO_HINTS`; comment said SOCO *"is left to the SOCO desk's own lane rather than pre-empted"* | `SOCO` in `ISO_ORDER` and `ISO_COLORS` (`#6366F1`, mirroring the existing `--iso-soco` token — **no new hue**), and a `GEO_HINTS` block on real geography: `SOCO_MS [0.12,0.72]` (Mississippi Power's south-eastern service area), `SOCO_AL [0.46,0.50]`, `SOCO_GA [0.84,0.34]` (Atlanta-weighted). MS→AL→GA is a chain because **Mississippi reaches the system through Alabama, not Georgia**, so AL is the middle node carrying both links. Coordinate convention verified off ERCOT/MISO: x west→east, y north→south. |
| `docs/codebase-site/js/iso-configs-table.js` | `isoOrder` 8; no SOCO colour or description | `SOCO` in `isoOrder` + `ISO_COLORS`, and an `ISO_DESCRIPTIONS` entry stating the single-BA fact, the three geographic zones, both Tier-3 links, the fleet-MW fallback and the $61,900 VOLL |
| `docs/codebase-site/css/site.css` | tab accents for 7 regions | `+ .tabs__tab[data-iso="SOCO"] { --iso-accent: var(--iso-soco); }`, **plus the dark-section contrast guard of §3** |
| `docs/codebase-site/forecast-runs.html` | `ISO_ORDER` = 7 + `ALL` | `+ SOCO` before `ALL`. **This fixed a latent bug, not just an omission** — see §2. |
| `scripts/build_status.py:59` | `ISO_ORDER` 7 | `+ "SOCO"` (8). Comment records that unlisted regions fall to the alphabetical tail, so the list is presentation and never a gate |
| `scripts/lib/keeper_store.py:37` | `DEFAULT_ISO_ORDER` 6 | `+ "SOCO"` (7). Comment records that `iso_list` **appends** unlisted shards rather than dropping them (verified at `keeper_store.py:77-78, 81-82`), and that the module is contractually **stdlib-only** so it cannot import `SUPPORTED_ISOS` |
| `scripts/render_data_dictionary.py:49` | `ISO_ORDER` 7 | `+ "SOCO"` (8), reflowed |
| `data/dictionary/data-dictionary.md` | 7 ISO coverage columns | **Regenerated.** 8 columns. See §4 — the delta is provably one appended column and nothing else |
| `docs/codebase/08-config-reference.md` | SOCO row said **"VOLL $2,000"**; summary said **"VOLL is $2,000/MWh for all eight non-ERCOT regions"** | **Both were FALSE.** Corrected to $61,900 with the full ICE-2 derivation; SOCO row expanded; three per-region mechanism lists given SOCO entries; `MARKET_DESIGN` and PRM registry lines corrected. See §5 |
| `docs/multi-iso/README.md` | "eight registered regions with ERCOT"; "all eight regions are now registered"; SOCO row said **"as the eighth registered region"** and **"SOCO stays unregistered until its W2 lane lands"** | nine regions + 47/44/58; SOCO row re-stamped as **registered 2026-09-14, the ninth builder**, with the rubric-v3.8 class, the Tier-3 links, the $61,900 VOLL and "no keeper yet — first solve is SOCO-40"; card count corrected S1–S10 → **S1–S12** (verified at plan §3) |
| `docs/README.md` | already "nine registered regions" (NWPP-35); living-log line named only the frozen `calibration-log.md` | count **unchanged**; living-log line now also names the per-region continuations `calibration-log/<iso>.md` + `governance.md`, which is where `soco.md` actually lives |
| `docs/calibration-log/soco.md` | 11-line header, title `# SOCO calibration log`, listing **Southern Power as a member** | **HEADER ONLY replaced** (121 insertions, 7 deletions). See §6 — all nine existing entries byte-identical |

## 2. `forecast-runs.html` — PROVING A REGION WITH NO FORECAST RUNS RENDERS, and a latent bug found

The charter asked me to prove this. I extracted the **real lines from the page** (rather than retyping
the logic) and ran them in Node against four `META` shapes. `ISO_ORDER` there is **only a sort
comparator**; the chip SET is `META.isos`, so a registered region with no forecast run never appears:

| case | `META.isos` | chips rendered | verdict |
|---|---|---|---|
| 1 — LIVE state | the 7 + `ALL` (SOCO absent) | `ERCOT CAISO PJM MISO NYISO NEISO SPP ALL`, header "7 ISOs" | **renders, no SOCO chip, no throw — PASS** |
| 2 — `{isos: []}` (the line-540 fallback) | empty | `[]`, count 0 | no throw — PASS |
| 3 — `{}` (no `isos` key) | absent | `[]`, count 0 | no throw — PASS |
| 4 — SOCO present, **after** this fix | 7 + SOCO + `ALL` | `… SPP SOCO ALL` | correct position |
| 4′ — SOCO present, **before** this fix | same | **`SOCO ERCOT CAISO …`** | **SOCO sorted AHEAD of ERCOT** |

**The latent bug:** `Array.indexOf` returns `-1` for an unlisted region, and `-1 < 0`, so an unlisted
region sorts to the **front**, not the back. Adding SOCO is therefore a correctness fix that happens to
be inert today (SOCO has no forecast run) and would have surfaced the moment W6 gave it one.
`frontend/data/forecast/program-status.json` carries `iso_order` of 7 and is **untouched** — it is W6's,
routed to the capx director as card S10. `isoColor('SOCO')` resolves to `var(--iso-soco, var(--hydro))`
and `shared.css` **is** loaded by that page (line 8), so the accent resolves rather than falling back.

**NWPP is still unlisted and still carries the `-1` behaviour.** That is an NWPP-desk gap; I routed it
and noted it in the code comment rather than filling it (§8).

## 3. ACCESSIBILITY AUDIT — full output, and TWO REAL DEFECTS FIXED

Contrast computed with a WCAG-2 relative-luminance implementation. **Validated against the committed
record before use**: it reproduces `FINDING-spp-34-2026-09-07.md` §7 S-2's figures exactly (ERCOT 2.28,
CAISO 2.15, SPP 2.49, PJM 2.77, MISO 2.80, NYISO 4.35, NEISO 6.30). Backdrops are the **real layered
stack**, not an assumed flat colour.

### 3.1 Where SOCO already passes — the existing accent-agnostic machinery covers it

| surface | mechanism | SOCO | verdict |
|---|---|---:|---|
| `.iso-badge` (config-reference.html + `bc-pages.css`) | SPP-34's 88 %-white overlay ⇒ accent@12 % + `--text-primary` | **17.19:1** | PASS |
| `.badge--iso-soco` | `#4338CA` on `rgba(99,102,241,0.12)` | **6.81:1** (white card) / **6.47:1** (`--bg-page`) | PASS — **the highest of all nine** |
| `.iso-btn.active--soco` | same pair | same | PASS |
| `.ff-run-iso` 8 px dot | raw accent on white | 4.47:1 (3:1 bar) | PASS — one of only 4 of 9 that clear it |
| my new `<p>` in config-reference.html | `--text-secondary` on white | 14.63:1 | PASS |
| `ISO_DESCRIPTIONS` text | `--text-muted` on `--bg-page` | 5.84:1 | PASS |

Worth recording: **white-on-SOCO would have been 4.47:1 — a FAIL, and a near-miss one** (bar 4.5),
exactly the kind that survives eyeballing. SPP-34's overlay is what prevents it, and its comment had
already anticipated SOCO by name.

### 3.2 DEFECT 1 (High/Critical, pre-existing, 7 of 9 regions) — active tab label on dark · **FIXED**

The topology tab bar lives in `network.html:326`'s `section-dark`, and `viz-iso-topology.js` sets the
active tab's text to the **raw accent, inline**. Against the real backdrop (navy `#1A2744` +
`.glass-chart-panel` 0.06 + `.tabs__tab.active` 0.05 = `#333E58`):

| NEISO | SOCO | NYISO | NWPP | MISO | PJM | SPP | ERCOT | CAISO |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **1.69** | **2.39** | **2.45** | 3.45 | 3.80 | 3.84 | 4.28 | 4.68 ✓ | 4.96 ✓ |

Seven of nine failed the 4.5:1 bar; NEISO at 1.69:1 is **Critical** by the skill's own scale.
**Fix** (`css/site.css`): `.section-dark .tabs__tab.active[data-iso] { color: #fff !important; }` →
**10.66:1** (gradient top) / **12.73:1** (gradient end) **for every region**. The accent stays on the
2 px bottom border and on the graph nodes, and the active state is independently carried by the border,
the 5 % background wash and `aria-selected`, so no affordance is lost. `!important` is required to beat
the inline `btn.style.color`; the same cascade trick, for the same reason, as SPP-34's overlay.

### 3.3 DEFECT 2 (Critical, pre-existing, **all 9** regions) — graph node labels · **FIXED**

`viz-iso-topology.js` drew each zone label in `color` — the **same accent as the circle it sits on**,
whose fill is that accent at 0.18. A label can never contrast with its own background. At 9–10 px/600
this is normal text (4.5:1 bar) and **all nine failed**: NEISO 1.63, SOCO 2.05, NYISO 2.26, NWPP 2.72,
PJM 2.91, MISO 2.97, SPP 3.18, ERCOT 3.39, CAISO 3.60. **Fix:** label fill `#FFFFFF` at 0.95 →
**8.04–10.09:1** on the circle and ~10.7:1 where a label overhangs onto the backdrop; worst case across
all nine rises from **1.63:1 to 8.04:1**. The circle's accent fill and accent stroke are untouched.

### 3.4 DEFECT 3 (High, pre-existing, all chips) — `dc-chip.active` · **FIXED**

`data-completeness.html`'s active filter chip was `background: var(--hydro)` with white text =
**2.77:1**, failing at both the 4.5:1 and the 3:1 bar for 0.76 rem/600 text — and I had just added a
tenth chip to that set. **Fix:** background `var(--hydro-text, #0369A1)`, the design system's **own
existing WCAG-safe blue** → **5.93:1**. Same hue family, no new colour, no new token.

**All three fixes are deliberately ACCENT-AGNOSTIC**: they encode no per-region value, so no ISO's
number crosses into another's (rule 25 `[R-ISO-SCOPE]`), and they repair all nine regions at once
rather than only the one whose lane happened to measure it. Each carries its measurements in a code
comment so the next lane sees the evidence, not just the conclusion.

**Not fixed, reported:** in a *light* section `.tabs__tab.active[data-iso]` also renders accent-on-white
(ERCOT 2.28:1 …), but no `data-iso` tab bar currently exists in a light section — the only one is
`network.html`'s, which is dark. Left alone rather than changing appearance for a case that does not ship.

## 4. THE DATA DICTIONARY — regenerated, and the delta PROVEN to be one column

`data/clean/` is **empty** under the `code` profile, and the coverage matrix is built from `data/clean`
Parquet provenance — so a naive re-render risked wiping real coverage. I diffed a **dry** `--stdout`
render before writing anything. The committed matrix was **already all `—`** for every region, so the
render loses nothing. Verified cell-by-cell in Python rather than by eye: of 2,102 lines, **50 changed,
and every one is "identical cells plus exactly one appended cell"** — appended values are exactly
`{SOCO, ---, —}` (header, separator, 48 data rows). `--check` then reports up to date, and the
render-equality test passes.

## 5. `08-config-reference.md` — TWO FALSE STATEMENTS CORRECTED AGAINST THE CODE

Both introduced when SOCO's row was written without reading `_soco_config`'s VOLL:

1. SOCO's table row said **"VOLL $2,000"**. `iso_configs.py:2348` is `voll=61_900.0`.
2. The summary said **"VOLL is $2,000/MWh for all eight non-ERCOT regions"** — false for the same reason.

Now: **$2,000 for seven of the eight**, with two exceptions that both follow from a region not being an
ISO — NWPP's interim ledgered $2,000, and SOCO's **$61,900**, stated with its full derivation (ICE
Calculator 2, OSTI 3021993, 2-hour column, EIA-861 2024 customer mix over the 85 `SOCO` BA-code rows:
`0.4009 × 5,030 + 0.5991 × 100,000 = 61,926.527 → 61,900`, arithmetic re-checked here), its honest width
(8 h → $32,384, 24 h → $19,447) and its stated national-pooled-model misalignment. Because this is the
**slack penalty** at ~31× the $2,000 regions', I noted that unserved energy dominates a SOCO objective
far more sharply — that is a thing to know before reading a SOCO dual.

Also corrected in the same file, each verified against source, not memory:

- **`MARKET_DESIGN` carries six keys** (ERCOT CAISO PJM NYISO NEISO MISO — measured), so *all three*
  regions registered since 2026-09-06 resolve `reserve_margin_build_enabled` OFF through
  `DEFAULT_MARKET_DESIGN`: SPP, NWPP and SOCO. The line had named only SPP.
- **PRM registry** was missing two rows: measured `NWPP 0.144`, `SOCO 0.26` (SOCO's is the **winter**
  margin, the binding season for a winter-peaking footprint).
- **Three per-region mechanism lists** given SOCO entries: scarcity/reserve overlays (**none, and
  structurally so** — no reserve market, no offer cap, no administrative scarcity price, so no ladder
  for an ORDC/RCPF analogue to reproduce); reliability floors (**none** — no
  `reliability_floor_coeffs_SOCO.csv` exists, so the registry list is empty; I flagged that a cost-based
  pooled system is commitment-heavy by construction, so the temptation to floor it is real and rule 17
  `[R-FLOOR-WINDOW]` governs any later one); transmission/interchange (SOCO in
  `_SCALAR_INTERCHANGE_ISOS` via `soco_net_interchange`, a net **exporter** so the served series
  *raises* internal generation — the opposite sign to NWPP — plus the eight default-off neighbour
  blocks, enumerated from source: `SOCO_TVA SOCO_MISO SOCO_DUK SOCO_SCEG SOCO_SC SOCO_FPL SOCO_FPC SOCO_TAL`).

## 6. `docs/calibration-log/soco.md` — HEADER ONLY, WITH THE ENTRIES PROVEN UNTOUCHED

The charter warned that this file already carries landed entries and that removing one is a
stop-the-line event. I treated it as a hash-verified operation, not a careful edit:

- **Before:** entry region (`## soco-10` → EOF) = 365 lines, 9 headings,
  `sha256 11c17984decc03b3ecbe91ac0886bc2d9ed72967f594220ab29401a99f8155f9`.
- **After:** 365 lines, 9 headings, **`sha256 11c17984…` — identical**. `git diff --numstat` is
  **121 insertions / 7 deletions**, and all 7 deletions are old header lines. A `diff` of the two
  heading lists is empty: none added, none removed, none reworded.

The new header matches `miso.md`'s format (`# Calibration Log — SOCO`, the frozen-archive date, the
entry-format and newest-at-bottom statement, the per-ISO-lane convention) and adds what `spp.md`/
`nwpp.md` carry: program/handoff/ledger/audit pointers with **"the ledger wins"**, the lever-queue and
matrix-shard pointers, a `## Lane state` block, and the **`Next shorthand: soco-35`** line the charter
asked for — with the convention stated, since SOCO heads its entries by *lane* number, so plan-chartered
lanes (SOCO-30/31/32/33, SOCO-40, SOCO-54–57) keep their own numbers.

Two things I got right only by checking: **§5.8, not §5.10** (§0), and the **Southern Power error** —
the old header listed Southern Power as a footprint member, but SOCO-14 returned a *documented NO* on
whether respondent 186's planning-area load sits in the BA. The header now names the **five** FERC-714
respondents (Alabama Power 2, Georgia Power 183, Mississippi Power 184, Oglethorpe 107, MEAG 210), says
186 is excluded, and records that 186's 1.3–1.4 % is named on the first keeper's determination basis.

**Every cross-reference in the new header was checked to resolve** (10/10 files exist), and I confirmed
`keepers/SOCO.json` correctly does **not** exist (7 shards on disk).

**On `[R-HOLDOUT]`:** I did **not** replicate `spp.md`'s "Holdout tiers (rule 22 `[R-HOLDOUT]`)" block,
which predates that rule's removal on 2026-09-09. The header instead states the post-removal position
honestly — any year may be solved with no authorization, and therefore **no SOCO number will be a
certified out-of-sample number**; every run is model-*selection* evidence.

## 7. GATES — all run at my own base sha, each RED proven independent of this diff

- **`scripts/check_registry_payload_parity.py` — RED, and byte-identically RED without my changes.**
  The same two bundles NWPP-35 reported: `results/calibration/caiso279_ablate_dswcouple_span` and
  `results/calibration/soco15_spp_arm`. Proven by `git stash`: identical failure list with and without
  the diff, and `git diff --name-only` touches **nothing** under `results/` or `frontend/`. One is a
  SOCO artifact, and clearing it means **deleting a solve's results** — rule 31 `[R-RETAIN]` forbids
  that before the owner has ruled on promotion, and I cannot establish from here that SOCO-15's arm has
  been ruled on. **Reported, not repaired (§8).**
- **`scripts/check_mechanism_matrix.py` — EXIT 0**, plain and `--base edd40943`. Every warning is
  labelled by the tool itself "(pre-existing, not this PR)": nine anchor-line drifts, plus NYISO keeper
  stamp + prose-header drift from yesterday's `nyiso-235` promotion. I added no `ScenarioConfig` field
  and moved **no matrix cell**, so rule 28 duties (b) and (c) do not fire.
- **`ruff format --check` + `ruff check`** on the three `.py` files: *3 files already formatted*,
  *All checks passed!*
- **`tests/curation/test_data_dictionary_sync.py`** — 4 passed, 144 subtests passed, **1 pre-existing
  failure** (`coal-stocks` schema has no `DATATYPE_ORDER` section — unrelated to ISO columns; identical
  with and without my diff by `git stash`). The render-equality assertion **passes**.
- **`tests/scoring/`** keeper_store + audit_keepers + pointers: **41 passed**.
  `test_gate_a_provenance.py::test_live_board_passes` fails **identically** with and without my diff
  (NYISO and SPP `gate.a_keeper_marker` rows cite superseded keepers after yesterday's promotions);
  my diff touches no keeper shard and no `calibration-complete.json`.
- **Syntax** — `iso-topologies.json` parses and **all nine blocks round-trip against `get_iso_config`
  with ZERO per-value mismatches** (name, voll, zone names, load shares to 1e-12, link counts); both
  edited JS files parse as ES modules; `site.css` braces balanced (153/153), guard present exactly once.
- **Rule 27 `[R-PUSH]`** — eleven changed files are ≥ 300 lines (`data-dictionary.md` 2102,
  `render_data_dictionary.py` 1485, `config-reference.html` 1012, `build_status.py` 862,
  `iso-topologies.json` 766, `site.css` 617, `forecast-runs.html` 567, `soco.md` 491,
  `data-completeness.html` 483, `viz-iso-topology.js` 460, `08-config-reference.md` 352). **None
  shrank.** Every edit is a surgical in-place replacement of exact on-disk bytes — the one scripted edit
  asserted `count(old) == 1` before writing — never regenerated file content from a model response.
  `data-dictionary.md` is the single exception by design: it is a **generated** artifact written by its
  own renderer, and §4 proves its delta.

## 8. ROUTED — not mine to touch, each with the measured consequence

1. **`CLAUDE.md:19` still says "seven ISOs registered"** — the most-read line in the repo, and now
   false by two. It also says "CAISO (3 zones + WECC import node)"; CAISO has **6** zones (measured:
   `NP15 ZP26 LA_BASIN SDGE SP15_rest WECC_import`), i.e. 5 load zones + the import node — stale since
   the caiso-172 SP15 split. NEISO's "4 zones + HQ import node" **is** correct. Suggested replacement:
   *"Multi-ISO: nine regions registered in `config/iso_configs.py` — ERCOT (7 zones, 6 carry load; the
   calibrated reference), CAISO (5 zones + WECC import node), PJM (8 zones), MISO (6 zones), NYISO
   (5 zones), NEISO (4 zones + HQ import node), SPP (2 zones), NWPP (5 zones; a POOL of ~17 balancing
   authorities), SOCO (3 zones; a SINGLE balancing authority) — sharing one ISO-agnostic LP."*
   Not in my charter's file list; editing the governing rules file as a side effect of a site lane is
   the collision §8.0 rule 5 exists to prevent, so I deliberately left it.
2. **`docs/multi-iso/00-iso-addition-protocol.md` is stale in six places** — line 59 says **SOCO
   "NOT REGISTERED"**, line 60 says the same of NWPP, line 72 says *"TWO further regions are chartered
   but NOT registered — `SOCO` and `NWPP`"*, and lines 10 / 18 / 65 say "all seven". A reader of the
   protocol doc would conclude SOCO is not registered. The file is **SOCO-10's** under the SOCO plan and
   **NWPP-10's** under NWPP's; NWPP-35 routed line 60 rather than editing it, and I route line 59 for
   the same reason (§8.0 rule 5).
3. **`CHANGELOG.md` — NOT appended, deliberately.** The `sync-docs` skill's step 6 says always append,
   but plan §8.0 rule 1 names `CHANGELOG.md` as a shared record **a lane never touches**. The plan rule
   wins; the DESK writes the entry from this FINDING. Flagging the conflict so it is a decision, not an
   omission.
4. **`soco-addition-plan-2026-09.md:43`** — this lane's own definition-of-done row still reads *"docs/site
   prose says eight regions"*. It should read **nine**. Plan text, §8.0 rule 1, the desk's.
5. **`plan §5 row SOCO-34 → LANDED`** — the charter's exit item, but the plan is a shared record
   (rule 1), so the desk marks it.
6. **NWPP's share of the region lists I extended.** `build_status.ISO_ORDER`,
   `keeper_store.DEFAULT_ISO_ORDER` (also missing SPP), `render_data_dictionary.ISO_ORDER` and
   `forecast-runs.html`'s `ISO_ORDER` still omit NWPP, and `css/site.css` has no
   `.tabs__tab[data-iso="NWPP"]`. Consequences measured, not assumed: `keeper_store.iso_list`
   **appends** rather than drops (fail-safe); `build_status` sorts unknowns to the alphabetical tail
   (cosmetic); the CSS rule is inert while JS sets `--iso-accent` inline; but `forecast-runs.html`
   sorts an unlisted region to the **front** (§2). Each is noted in the code comment I added, so the
   NWPP desk can close them without re-deriving the analysis.
7. **`keeper_store.py` cannot import `SUPPORTED_ISOS`** — it is contractually stdlib-only, so its
   "mirrors `build_status.ISO_ORDER`" comment must be hand-maintained and had already drifted (missing
   SPP). `render_data_dictionary.py` **does** already import `market_sim.config.paths`, so it *could*
   import `SUPPORTED_ISOS` — `iso_configs.py`'s own comment says scripts should — but that would add a
   `pydantic` dependency to a Pages-deploy script, which is out of scope for a docs lane. Noted in the
   file; routed as a cleanup.
8. **`frontend/data/backcast/keepers/index.json`** carries 7 regions and is the runtime source of truth
   for dashboard order. **Untouched** — the first-solve lane adds SOCO at registration, per charter.
9. **`docs/calibration-log/soco.md:143` still carries the stray orphan line** NWPP-35 reported
   (`record this lane must not edit, plan §8.0 rule 1.)*`, between the soco-11 and soco-12 entries). It
   sits **inside an entry body**, which is the desk's territory under §8.0 rule 1 and outside my
   header-only scope. Left byte-identical; re-routed.

## 9. WHAT THIS LANE DID NOT TOUCH

`src/market_sim/` (nothing — no `ScenarioConfig` field, no default flip, no solve path);
`scripts/ff_readiness_battery.py`; anything under `frontend/data/forecast/` (W6, card S10) **or**
`frontend/data/backcast/`; any keeper shard; `keepers/index.json`; any mechanism-matrix shard or **cell
value**; `docs/mechanism-testing-matrix.md`; the plan; the desk ledger; `CHANGELOG.md`;
`docs/calibration-log/soco.md`'s entries; any other region's log; `CLAUDE.md`;
`00-iso-addition-protocol.md`; `index.html` (verified correct, §0); `results/` and every bundle.
**No solve was run.** Nine site/docs files and three scripts changed, plus one generated artifact.

## Log entry

*(appended verbatim to `docs/calibration-log/soco.md` by the SOCO ADDITION DESK — plan §8.0 rule 1;
this lane wrote only that file's HEADER and did not write this entry into it.)*

## soco-34 — 2026-09-16 — SOCO site wiring, nine-region prose, log header, 3 WCAG fixes (zero-LP)

Lane SOCO-34, Opus claude-opus-5, branch claude/soco-34-site-docs-pxkmb5, base
edd40943. FINDING `docs/handoffs/FINDING-soco-34-2026-09-16.md`. No solve, no
src/ edit, no ScenarioConfig field, no matrix cell, no shared record.

THE index.html ARITHMETIC, CHECKED NOT ASSUMED: 47/44/58 ALREADY counted SOCO's
three zones, so index.html needed NO change. 39+5+3=47, 36+5+3=44, 47+9+2=58,
recomputed twice (get_iso_config over SUPPORTED_ISOS, and re-summed off the
committed JSON after the edit). NWPP-35's prose had run two days ahead of the
data; this lane closed the gap rather than moving a number. Both orderings cross
and both are right: NWPP is the 8th builder but 9th matrix column, SOCO the 9th
builder but 8th matrix shard (SOCO-21 landed a day earlier) — which is why
SOCO's lever queue is matrix §5.8, not §5.10 as first written and caught.

THE FOUR CHARTERED DEBTS CLOSED. (a) iso-topologies.json carries a SOCO block —
3 zones summing to exactly 1.000000, 2 links, voll 61900, no interface limits —
with the eight existing blocks byte-unchanged and _meta re-stated at nine; all
nine blocks round-trip against get_iso_config with ZERO per-value mismatches.
(b) data-completeness.html filter now lists all nine. (c) config-reference.html
"the eight serialized" → all nine + the 47/44/58 totals. (d) index.html left
alone, arithmetic reported. Plus SOCO into viz-iso-topology.js
(ISO_ORDER/ISO_COLORS/GEO_HINTS on real geography — MS→AL→GA a chain because
Mississippi reaches the system through Alabama), iso-configs-table.js
(isoOrder/ISO_COLORS/ISO_DESCRIPTIONS), the site.css tab accent,
build_status.ISO_ORDER, keeper_store.DEFAULT_ISO_ORDER,
render_data_dictionary.ISO_ORDER, and the regenerated data dictionary — whose
delta was PROVEN cell-by-cell to be one appended column and nothing else (the
committed matrix was already all-dashes, so the empty code-profile data/clean
cost nothing).

forecast-runs.html PROVEN to render for a region with no forecast runs, by
running the page's own extracted lines against four META shapes: the chip set is
META.isos so SOCO never appears, empty/absent META do not throw. It also fixed a
LATENT BUG — indexOf returns -1 for an unlisted region and -1 < 0, so before the
fix SOCO sorted AHEAD of ERCOT. NWPP still carries that behaviour (routed).

TWO FALSE STATEMENTS CORRECTED against the code in 08-config-reference.md: SOCO's
row said "VOLL $2,000" and the summary said "$2,000 for all eight non-ERCOT
regions". SOCO is $61,900 (iso_configs.py:2348) — the LBNL/DOE ICE-2 customer-mix
derivation, restated with its 8h/24h width and its national-pooled-model
misalignment, and with the note that at ~31x the $2,000 regions' slack penalty
unserved energy dominates a SOCO objective far more sharply. Also corrected
there: MARKET_DESIGN has six keys so SPP/NWPP/SOCO all resolve the build
backstop OFF (the line named only SPP); the PRM registry was missing NWPP 0.144
and SOCO 0.26 (winter); and SOCO entries added to the scarcity, reliability-floor
and interchange mechanism lists (none / none / net EXPORTER + eight default-off
neighbours). multi-iso/README.md: SOCO was "the eighth registered region" and
"stays unregistered until its W2 lane lands" — both now false, re-stamped to the
ninth builder, registered 2026-09-14, cards S1–S12.

THREE ACCESSIBILITY DEFECTS FIXED, ALL PRE-EXISTING AND ALL ACCENT-AGNOSTIC (so
no per-region value is encoded, rule 25, and all nine regions are repaired at
once). The calculator was first validated against FINDING-spp-34 §7 S-2's
committed figures. (1) The dark-section active tab drew its label in the raw
accent: 7 of 9 failed, NEISO 1.69:1 CRITICAL, SOCO 2.39:1 — now #fff at
10.66-12.73:1 with the accent kept on the border. (2) Graph node labels were
drawn in the same accent as the circle they sit on, so ALL NINE failed
(1.63-3.60:1) — now white at 0.95, worst case 8.04:1. (3) dc-chip.active was
white on --hydro at 2.77:1 — now the design system's own --hydro-text at
5.93:1. Where SOCO was already covered it passes best-in-class: .iso-badge
17.19:1 and .badge--iso-soco 6.81:1, the highest of the nine, via SPP-34's
overlay — which matters because white-on-SOCO would have been a 4.47:1
near-miss FAIL.

calibration-log/soco.md HEADER ONLY, entries PROVEN untouched: the entry region
(## soco-10 → EOF) is byte-identical, sha256 11c17984… before and after, 365
lines and 9 headings each time, 121 insertions / 7 deletions with all 7
deletions old header lines. New header matches miso.md's format plus spp/nwpp's
pointers, carries "Next shorthand: soco-35" with the lane-number convention
stated, and fixes the old header's claim that Southern Power is a footprint
member — SOCO-14 returned a documented NO on respondent 186, so the five-set
(2/183/184/107/210) is named instead. It deliberately does NOT replicate spp.md's
rule-22 [R-HOLDOUT] block, removed 2026-09-09; it states instead that no year is
protected, so no SOCO number will be a certified out-of-sample number.

GATES: registry payload parity RED on the same two bundles NWPP-35 reported
(caiso279_ablate_dswcouple_span, soco15_spp_arm) — proven byte-identically RED
via git stash, and my diff touches nothing under results/ or frontend/; one is a
SOCO artifact whose clearing means deleting a solve's results, which rule 31
[R-RETAIN] forbids before the owner rules, so REPORTED not repaired.
check_mechanism_matrix EXIT 0 plain and --base (all warnings self-labelled
pre-existing). ruff format+check clean on 3 files. Dictionary sync: 4 passed /
144 subtests, 1 pre-existing coal-stocks failure identical via stash. Scoring:
41 passed; test_gate_a_provenance fails identically without this diff (NYISO/SPP
superseded-keeper rows from yesterday's promotions). Eleven changed files are
≥300 lines, none shrank, all surgical (rule 27).

ROUTED: (1) CLAUDE.md:19 STILL SAYS "seven ISOs registered" and also
mis-states CAISO as 3 zones (it is 6) — replacement text supplied, deliberately
not edited by a site lane; (2) 00-iso-addition-protocol.md stale in SIX places
incl. line 59 "SOCO NOT REGISTERED" and line 72 "TWO further regions … NOT
registered" — SOCO-10's/NWPP-10's file, rule 5; (3) CHANGELOG.md NOT appended:
sync-docs step 6 says always, plan §8.0 rule 1 forbids a lane touching it — the
plan wins, the desk writes it, conflict flagged rather than silently skipped;
(4) plan line 43's own definition-of-done still says "eight regions"; (5) plan §5
row SOCO-34 → LANDED is the desk's, rule 1; (6) NWPP still missing from four of
the region lists this lane extended plus its site.css tab accent, consequences
measured (fail-safe append / alphabetical tail / inert CSS, but front-sorting in
forecast-runs); (7) keeper_store is stdlib-only so it cannot import
SUPPORTED_ISOS and its "mirrors build_status" comment had already drifted;
(8) keepers/index.json untouched — the first-solve lane adds SOCO at
registration; (9) soco.md:143's stray orphan line sits inside an entry body, the
desk's, re-routed.
