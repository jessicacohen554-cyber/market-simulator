# FINDING — NWPP-35: the region count is **NINE**, not seven and not eight — SOCO registered too

**Lane** NWPP-35 · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-14 ·
**Branch** `claude/nwpp-35-site-docs-a7f2` · **Base**
`d54cd9c571359b85cb1a8e1cd5cab68c080a6b0c` (= `origin/main` at launch) ·
**Data profile** `code` · **Solves** none (zero-LP lane).

## 0. THE MEASURED COUNTS, FIRST

Re-counted at my own base sha per plan §0 / gate G15, **before any prose was edited**. The charter
told me to expect EIGHT builders against NINE matrix columns. **That intermediate state is already
gone**: SOCO-20 merged after the desk's r#5 pin, so at `d54cd9c5` the two agree at **nine**.

| object | measured at `d54cd9c5` | charter expected | how measured |
|---|---:|---:|---|
| `config/iso_configs._ISO_BUILDERS` | **9** | 8 | `sed -n '2352,2379p' … \| grep -cE '^\s+"[A-Z]+": _'` |
| `SUPPORTED_ISOS` | **9** (`tuple(_ISO_BUILDERS)`) | 8 | same object, one line below |
| mechanism-matrix `isos[]` | **9** | 9 ✓ | `mechanism-matrix.js:1460` |
| `mechanism-matrix/<ISO>.js` shards | **9** | 9 ✓ | `ls` |
| `--iso-*` colour tokens, `css/shared.css` | **9** | — | `shared.css:78-86` |
| `frontend/data/backcast/keepers/*.json` | **7** | — | `ls` (no NWPP, no SOCO) |
| `docs/calibration-log/<iso>.md` | **8** + `governance.md`, **`nwpp.md` absent** | — | `ls` |

Registration order: **ERCOT · CAISO · MISO · PJM · NYISO · NEISO · SPP · NWPP · SOCO.** NWPP
registered 2026-09-14 (lane NWPP-20, `FINDING-nwpp-20-2026-09-14.md`); SOCO registered the same day
(lane SOCO-20) and merged second, which is why `iso_configs.py:2364` still calls NWPP "the EIGHTH
builder" (true when written, and correct as registration-order narrative) while its own
`SUPPORTED_ISOS` comment at `:2378` already says nine.

**Derived topology totals, recomputed rather than incremented** (default posture; CAISO's FSNO
partition is `topology_variant._caiso_fsno_partition = False`, so CAISO is its 6-zone build):

| | zones | carry load | links |
|---|---:|---:|---:|
| the seven prior regions | 39 | 36 | 47 |
| **+ NWPP** | 5 | 5 | 9 |
| **+ SOCO** | 3 | 3 | 2 |
| **nine regions** | **47** | **44** | **58** |

The old site figure "39 zones (36 carry load), 47 transmission links" reproduced exactly on the seven
prior regions, so the base was sound and only the two new regions move it.

## 1. EVERY FILE WHOSE COUNT CHANGED — before → after

| file | before | after |
|---|---|---|
| `docs/codebase-site/index.html:297` | "Seven ISOs, 39 zones (36 carry load), 47 transmission links." | "Nine regions, 47 zones (44 carry load), 58 transmission links." |
| `docs/codebase-site/network.html:8` | `content="7-ISO topology visualization…"` | `"Multi-region topology visualization…"` |
| `docs/codebase-site/network.html:324,331` | `SECTION 2: 7-ISO TOPOLOGIES` / `<h2>7-ISO Topologies</h2>` | `REGION TOPOLOGIES` / `<h2>Region Topologies</h2>`, **plus a new paragraph carrying the nine/47/44/58 figures and the "NWPP is a pool, SOCO is a BA, neither is an ISO" statement** |
| `docs/codebase-site/network.html:464` | "ERCOT, PJM, NYISO, SPP — no aggregate interface limits modeled" | "ERCOT, PJM, NYISO, SPP, **NWPP, SOCO** — …" (measured: only `_caiso_config`, `_miso_config`, `_neiso_config` construct `InterfaceLimit`s) |
| `docs/codebase-site/config-reference.html:402` | "Seven-ISO topology: …" | "Per-region topology: … `_ISO_BUILDERS` carries nine registered regions; the eight serialized into `iso-topologies.json` render below." |
| `docs/codebase-site/config-reference.html:215` | "failed WCAG AA on five of the seven accents" | "…of the seven accents **then registered**" + a sentence naming NWPP/SOCO's later accents and stating the overlay is accent-agnostic. **The measurement itself is untouched** — it was a true reading of seven accents and is not restated as nine. |
| `docs/codebase-site/config-reference.html:219` | "ISO_COLORS, the same seven hues as shared.css --iso-*" | "ISO_COLORS, mirroring shared.css --iso-*" (the count was false: shared.css carried 9, the JS 7) |
| `docs/codebase-site/data-pipeline.html:633` | "one LP serve seven ISOs" | "one LP serve nine registered regions" |
| `docs/codebase-site/data-pipeline.html:726` | `lmp-data` — "six — SPP under `spp-lmp-alt`" | + "; NWPP and SOCO publish no LMP at all" (the *six* is correct and stayed) |
| `docs/codebase-site/data-pipeline.html:778` | `zone-specific-demand` — "all seven" | "seven of nine — no NWPP" (measured off the tree: CAISO ERCOT MISO NYISO PJM SOCO SPP present, **no NWPP**) |
| `docs/codebase-site/data-completeness.html:360-365` | `ISOS` filter list of 8; comment naming SPP as the only post-census region | `ISOS` list of 9 (+NWPP); comment naming **all three** post-census regions and stating `_ISO_BUILDERS` carries nine |
| `docs/codebase-site/results-calibration.html:882` | "none of the **six** per-ISO keeper shards declares an `ablation_twin`" | "none of the **seven** …" + "(NWPP and SOCO, registered 2026-09-14, have no keeper yet)". Measured: 7 shards, `grep -l ablation_twin` returns none — the claim's *substance* was right, its count was stale by one ISO (SPP). |
| `docs/codebase/README.md:22` | "Seven ISOs share one ISO-agnostic LP: … NEISO, SPP." | "Nine registered regions … SPP, NWPP and SOCO" + the not-an-ISO statement |
| `docs/codebase/08-config-reference.md:210` | "The seven registered ISOs:" + a 7-row table | "The **nine registered regions**" + **NWPP and SOCO rows added**; see §2 for the SPP correction the same table needed |
| `docs/codebase/08-config-reference.md:227` | "for PJM, MISO and SPP carry an ISO prefix" | "for PJM, MISO, SPP, NWPP and SOCO carry a region prefix" |
| `docs/codebase/08-config-reference.md:231` | "VOLL is $2,000/MWh for all non-ERCOT ISOs" | "for all **eight** non-ERCOT regions" + NWPP's interim caveat |
| `docs/README.md:95` | "protocol & reference index (seven ISOs)" | "(nine registered regions)" |
| `docs/README.md:176` | "the seven-ISO topology & protocol" | "the region topology & protocol" |

**Where I deliberately did NOT change a count.** `data-completeness.html:303`'s row label
"Daily zone temp (all 6 ISOs)" and the census-time wildcard matching around it are a **correct
historical scoping** of a 2026-07-10 census of six ISOs — SPP, NWPP and SOCO are excluded on purpose
so the page cannot over-claim coverage nobody verified. I extended the comment to name all three and
left the label alone. Likewise the WCAG contrast measurement above: re-labelling a measurement of
seven accents as nine would falsify its own citation.

## 2. NON-COUNT CORRECTION MADE IN PASSING (code is the source of truth)

`docs/codebase/08-config-reference.md`'s SPP row asserted the N↔S link's TTC is **48,700 MW, a
Tier-3 placeholder that cannot bind**. `iso_configs.py` has carried **3,400 MW** since lever
**SPP-53** — `_ns_corridor_ttc = 3400.0`, the rule-14 `[R-ACCURATE]` reconciled corridor limit,
which the code's own comment says **replaced** the 48,700 placeholder and which *can* bind
(`3,400 < B_plaus 23,300 < B_hard 37,400`). The committed `iso-topologies.json` and
`js/iso-configs-table.js` already said 3,400; only this doc lagged. Corrected to the code.

## 3. NWPP WIRING NWPP-21 DID NOT LAND (all additive, NWPP-only)

NWPP-21 landed `--iso-nwpp: #65A30D` in `css/shared.css` plus its badge/button rules, the NWPP matrix
shard and the §5.9 lever queue; `js/backcast-runs.js:123` already carried the NWPP and SOCO hexes. It
did **not** reach the two ISO-enumerating visualisations, so NWPP was registered but invisible on the
Network and Config-Reference pages. Landed here, all derived from `iso_configs.py`, zero new facts:

- `data/iso-topologies.json` — a **new NWPP block**: 5 zones with their load shares (sum exactly
  1.000000), 9 links with TTCs and directionality, `voll` 2000.0, `interface_limits: []`. The
  existing seven blocks are byte-unchanged (87 insertions, 2 deletions — the 2 are `_meta`).
- `js/viz-iso-topology.js` — `NWPP` in `ISO_ORDER`, `#65A30D` in `ISO_COLORS` (mirroring the CSS
  token, no new hue), and a `GEO_HINTS` block placing the five zones on real geography.
- `js/iso-configs-table.js` — `NWPP` in `isoOrder` and `ISO_COLORS`, plus an `ISO_DESCRIPTIONS`
  entry stating the pool-of-BAs fact and the Tier-3 NW↔OR placeholder.

Both renderers already skip any key `iso-topologies.json` does not carry (`if (!data[iso]) return;`),
so this is fail-safe. **SOCO is deliberately not added to either** — see §5.

## 4. `docs/calibration-log/nwpp.md` — CREATED, HEADER ONLY

New file, 116 lines, **zero `## <lane>` log entries** (§8.0 rule 1: the desk appends every lane's
`## Log entry` section from its FINDING; a lane never writes this file, and this lane did not).
Template is `docs/calibration-log/spp.md` with the SOCO file's house style. What it carries:

- The pool framing, program/ledger/audit pointers, the "ledger wins" precedence, the lever-queue and
  matrix-shard pointers, the "no keeper exists / first solve is NWPP-40, gated on NWPP-36" state, the
  2023–2025 window and rule 16 `[R-ALLYEARS]`, and the measured nine-region counts from §0.
- Seven inherited facts stated so no later session rediscovers one in a residual: **card N2 / the
  NWPP-13 NO** (gate D3 failed every year, WEIM on-peak −37.5 / −22.6 / −23.6 % vs Mid-C against a
  ±10 % bar, daily r 0.74 / 0.95 / 0.67; volume was never the problem at 5.5–6.2 % net); the
  **rubric v3.8 `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`** class that serves limb (b), keyed on the
  absence of an `actual_lmp.json` block, landed from **SOCO-22** — which is why NWPP-22's identical
  branch was withdrawn rather than doubled (rule 19 `[R-ONE-MECH]`); **owner ruling N3** (cascade
  coupling before the first keeper); the **BPAT identity failure** (−3,206 MW mean, 81.5 % of hours,
  20.26 % of footprint load); the **CAISO `PNW_hydro_base` double-count** (routed, rule 25, never
  fixed here); **VOLL $2,000 interim and ledgered**; the **Tier-3 NW↔OR placeholder**; the **scorer
  closed to this program** after N11's single carve; and the **two-regime seasonality** (8 winter /
  6 summer / 1 flipping BAs; NWPP-NW summer÷winter 0.86 / 0.80 / 0.82 vs NWPP-SNV 1.95 / 2.06 / 1.87,
  r = 0.048 between them) against one scalar PRM on a coincident summer peak.

**One correction against my own first draft, made before commit**: I had written "ten winter-peaking
BAs" and mis-stated NWPP-NW's ratio denominator. `_nwpp_config`'s docstring says **8** winter, 6
summer, 1 flipping, and the 0.86 / 0.80 / 0.82 is summer ÷ winter. Fixed to the source.

## 5. ROUTED TO NWPP-DESK — four items, none of them mine to touch

1. **`docs/mechanism-testing-matrix.md` §5.9's header is stale in two ways.** It reads "**NOT YET
   REGISTERED** … `_ISO_BUILDERS` carries seven keys at the sha this section was written, `b485b6af`
   — NWPP is the **ninth** matrix column". NWPP-20 superseded the first clause on 2026-09-14, and the
   builder count is now nine. NWPP is the ninth matrix *column* but the **eighth registered builder**
   (SOCO is ninth), so the sentence is worth re-stamping with both ordinals rather than one. The file
   is the desk's under §8.0 rule 1; I did not edit it.
2. **`docs/multi-iso/00-iso-addition-protocol.md` still says NWPP is "NOT REGISTERED"** (line 60) and
   its §0 status line still reads "topology landed for all SEVEN registered ISOs" (line 17); its
   EIA-930 note says "all seven ISOs" (line 10). That file is **NWPP-10's** under plan §5
   ("FILES YOU OWN", plan line 622), so §8.0 rule 5 applies — routed, not edited. SOCO's row (line
   59) is stale the same way and is that desk's.
3. **CROSS-DESK OVERLAP, and it is real.** SOCO's lane **SOCO-34** is chartered for "site JS/CSS
   prose … eight-region prose" (soco plan lines 246 / 278 / 718) — the *same files* this lane owns.
   I landed first, so SOCO-34 will find the region-count prose already correct at nine and should
   verify rather than re-edit; what it still owes is the **SOCO half of the wiring** I deliberately
   left: a `SOCO` block in `data/iso-topologies.json` and `SOCO` in `viz-iso-topology.js` /
   `iso-configs-table.js` / `data-completeness.html`'s filter. I named SOCO in shared *prose* where
   omitting it would have created a false statement (the interface-limits list, the corpus notes, the
   `08-config-reference.md` table row), and touched **no** `soco*` file (§8.0 rule 9). The desks
   should dedupe the two charters.
4. **`docs/calibration-log/soco.md` carries a stray orphan line** between its `soco-11` and `soco-12`
   entries — `record this lane must not edit, plan §8.0 rule 1.)*` — evidently a truncated append.
   Another region's log; not touched, routed to the SOCO desk via ours.

## 6. GATES

- **`scripts/check_registry_payload_parity.py` — RED at my own base sha, unchanged by this lane.**
  Two bundle dirs fail Class-E point 4: `results/calibration/caiso279_ablate_dswcouple_span` and
  `results/calibration/soco15_spp_arm`. Verified by `git stash` that the output is **identical**
  with and without my changes; my diff touches no bundle, no sidecar and nothing under
  `frontend/data/`. Per §8.0 rule 6 I re-verified at my own sha and report rather than repair —
  and one of the two is a SOCO artifact I must not touch. **Routed.**
- **`scripts/check_mechanism_matrix.py` — EXIT 0**, both plain and `--base d54cd9c5`. Every warning
  is anchor-line drift the tool itself labels "(pre-existing, not this PR)". No `ScenarioConfig`
  field was added and no matrix cell value was touched, so duties (b) and (c) of rule 28 do not fire.
- **Syntax** — `node --check` clean on both edited JS files; `json.load` clean on
  `iso-topologies.json`; NWPP load shares sum to exactly 1.000000.
- **Rule 27 `[R-PUSH]`** — every edit is a surgical in-place replacement of exact on-disk bytes (each
  scripted as an assert-count-then-replace), never a regenerated full file. Seven changed files are
  ≥ 300 lines (`config-reference.html` 1012, `results-calibration.html` 1190, `data-pipeline.html`
  1037, `network.html` 852, `iso-topologies.json` 731, `index.html` 684, `data-completeness.html`
  474, `viz-iso-topology.js` 432); none shrank, and the pushed blobs are fetch-back verified.

## 7. WHAT THIS LANE DID NOT TOUCH

`src/`; `frontend/data/**`; any keeper shard, calibration log or matrix shard of another region; any
matrix **cell value**; the NWPP plan; the desk ledger; `docs/mechanism-testing-matrix.md`;
`CHANGELOG.md`; `scripts/`; any `soco*` file. No solve was run and no `ScenarioConfig` default moved.

## Log entry

*(appended verbatim to `docs/calibration-log/nwpp.md` by the NWPP ADDITION DESK — plan §8.0 rule 1;
this lane did not write it into that file.)*

## nwpp-35 — 2026-09-14 — region-count prose, NWPP site wiring, log header (zero-LP)

Lane NWPP-35, Opus claude-opus-5, branch claude/nwpp-35-site-docs-a7f2, base d54cd9c5.
FINDING `docs/handoffs/FINDING-nwpp-35-2026-09-14.md`. No solve, no src/ edit, no
matrix cell, no shared record.

THE COUNT IS NINE, NOT EIGHT. Re-counted at this lane's own base sha per plan §0 /
gate G15: `_ISO_BUILDERS` carries NINE — ERCOT CAISO MISO PJM NYISO NEISO SPP NWPP
SOCO — because SOCO-20 merged after the desk's r#5 pin. The charter's expected
8-builders-vs-9-matrix-columns intermediate state no longer exists; matrix columns,
matrix shards and `--iso-*` colour tokens all read nine too. Keeper shards: 7
(neither NWPP nor SOCO has one). Derived topology totals recomputed from scratch,
not incremented: 47 zones, 44 carrying load, 58 links — the old site figure
(39/36/47) reproduced exactly on the seven prior regions, so only the two new ones
move it.

EIGHTEEN COUNT SITES CORRECTED across 8 site files and 3 docs: index.html,
network.html (x4), config-reference.html (x3), data-pipeline.html (x3),
data-completeness.html, results-calibration.html (six→seven keeper shards),
codebase/README.md, codebase/08-config-reference.md (x4, incl. new NWPP and SOCO
table rows), docs/README.md (x2). TWO counts deliberately LEFT: the
data-completeness "all 6 ISOs" census label (a correct 2026-07-10 scoping that must
not over-claim) and the WCAG "five of the seven accents" measurement (re-labelling
it nine would falsify its own citation) — both got a clarifying sentence instead.

NON-COUNT CORRECTION: 08-config-reference.md's SPP row said the N↔S TTC is 48,700 MW
Tier-3-cannot-bind; the code has carried SPP-53's 3,400 MW rule-14 reconciled limit,
which CAN bind. Doc corrected to the code.

NWPP WIRING NWPP-21 DID NOT LAND: NWPP was registered but invisible on the Network
and Config-Reference pages. Added an NWPP block to data/iso-topologies.json (5 zones,
shares summing to 1.000000, 9 links, voll 2000, no interface limits) and NWPP to
ISO_ORDER/ISO_COLORS/GEO_HINTS in viz-iso-topology.js and to isoOrder/ISO_COLORS/
ISO_DESCRIPTIONS in iso-configs-table.js. All derived from iso_configs.py; both
renderers already skip unknown keys, so it is fail-safe. SOCO's half deliberately
left to SOCO-34.

docs/calibration-log/nwpp.md CREATED — header only, zero log entries (§8.0 rule 1).
Carries the measured counts and seven inherited facts: the NWPP-13 NO (gate D3
failed every year, WEIM on-peak −37.5/−22.6/−23.6 % vs Mid-C against a ±10 % bar;
volume was fine at 5.5–6.2 % net), the rubric v3.8 PHYSICALLY-CALIBRATED (PRICE
UNSCORED) class that serves card N2 limb (b) and came from SOCO-22 (NWPP-22's twin
withdrawn, rule 19), ruling N3, the BPAT identity failure (−3,206 MW, 81.5 % of
hours, 20.26 % of load), the CAISO PNW_hydro_base double-count (routed, rule 25),
interim ledgered VOLL, the Tier-3 NW↔OR placeholder, the closed scorer, and the
two-regime seasonality against one scalar PRM.

ROUTED: (1) matrix §5.9's header still says NOT YET REGISTERED and "seven keys" —
NWPP is the ninth matrix column but the EIGHTH builder; (2) 00-iso-addition-protocol
still says NWPP is NOT REGISTERED and "all SEVEN registered ISOs" — NWPP-10's file,
rule 5; (3) SOCO-34 is chartered for the SAME site-prose files as this lane — it will
find the counts already right and owes only SOCO's wiring; the desks should dedupe;
(4) calibration-log/soco.md has a stray orphan line mid-file. GATE: registry payload
parity is RED at this lane's own base sha on two unrelated bundles
(caiso279_ablate_dswcouple_span, soco15_spp_arm) — verified byte-identical output
with and without this diff, reported not repaired (rule 6; one is a SOCO artifact).
check_mechanism_matrix EXIT 0 plain and --base.
