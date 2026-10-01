# FINDING — lane SOCO-10 (Phase-0 data audit, registry-values table, protocol correction)

**Lane** SOCO-10 · **Date** 2026-09-13 · **Model** Opus `claude-opus-5` ·
**Branch** `claude/soco-10-audit-k3m9` · **Base** `origin/main` `2c2fc065` ·
**DATA PROFILE** `shared` · **Charter** `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-10.

**Status: DONE.** Zero solves (this lane runs no LP). Zero `src/` / `scripts/` / `configs/` /
`tests/` / `frontend/` / `data/` edits. Zero mechanism-matrix cells moved (rule 28). Zero
parameters derived (rule 23 `[R-FROZEN-DERIVE]`). No shared record touched (collision rule 1).

## Deliverables

| File | Action |
|---|---|
| `docs/multi-iso/soco-data-audit.md` | **NEW** — the Phase-0 census |
| `docs/multi-iso/00-iso-addition-protocol.md` | §0 SOCO row + §0 narrative note + the §3 ISO-count sentence |
| `docs/multi-iso/01-data-needs-and-upload-manifest.md` | SOCO rows in §2 (EIA-930), §3 (CEMS + note), §4 (gas), §5 (zonal), §8 (status note) |
| `docs/handoffs/FINDING-soco-10-2026-09-13.md` | this file |

---

## 1. The three headline results

### 1.1 The census reconciles — and the charter's headline total is off by the row it flags

EIA-860 `Balancing Authority Code == "SOCO"`, joined operable-generator: **336 plants /
788 generators / 70,667.2 MW nameplate** (66,161.2 summer, 69,096.8 winter).

The charter's **335 / 786 / 70,665.7** is that figure **minus the 1.5 MW Massachusetts
plant** — while the charter's own per-state list (`GA 41,284.4 · AL 24,494.0 · MS 4,577.7 ·
FL 309.6 · MA 1.5`) sums to **70,667.2**. Both are right about different sets; only one is
labelled. **Every per-state and per-technology figure confirms to 0.1 MW.**

**Adjudications** (audit §2.6), under a stated **two-key consistency rule** — a SOCO-coded
plant is admitted only if **both** its `NERC Region` is SERC **and** its state is
AL/GA/MS/FL-panhandle:

* **MA — REJECTED.** Plant 67241 "401 South", Berkshire County MA, 42.464 N / −73.184 W,
  **NERC region NPCC**, 1.0 MW battery + 0.5 MW PV. Fails both keys; an EIA-860 BA-field
  mis-entry. Costs 1.5 MW / 1 of 788 generators.
* **FL — KEPT.** All six plants (309.6 MW) are **NERC SERC**, western Florida panhandle,
  contiguous with Alabama Power. Caveat routed, not resolved: **generation membership ≠
  load membership** — Gulf Power still files its own FERC-714 (id 185), so whether the
  former Gulf Power *load* is inside `SOCO hourly.parquet::Demand` is **SOCO-11's**.

**Reconciled to Southern's 10-K on a stated bridge** (Form 10-K FY2024, Item 2 Properties,
pp. I-30–I-33): AP 12,942.4 + GP 14,789.1 + MP 3,517.9 + SEGCO 1,019.7 = 32,269.1 MW
**ownership share**, vs EIA-860's **whole-unit** 70,667.2 MW. The wedge is demonstrated on
one line: 10-K system nuclear **4,786.7 MW** vs EIA-860 SOCO nuclear **8,282.4 MW** — a
3,495.7 MW difference that is exactly the Oglethorpe 30 % / MEAG 22.7 % / Dalton 2.2 %
co-ownership of Vogtle and Hatch.

### 1.2 The missing-CEMS list — the critical path, twice as severe as SPP's

`data/raw/campd-unit-level/` carries **no `AL_*`, no `GA_*`, no `FL_*` for any year.** MS is
present 2019–2026.

**Missing for the window: `AL_2023`, `AL_2024`, `AL_2025`, `GA_2023`, `GA_2024`, `GA_2025`**
(6 files) — the charter's expectation is **confirmed exactly**. Plus `AL_2026`/`GA_2026` on
the SPP-11 precedent, and `FL_2023..2025` recommended (§2.3 priority 3).

| | Total MW | Present (MS) | Missing | Missing % |
|---|---:|---:|---:|---:|
| CEMS-eligible fossil | 50,005.0 | 4,207.7 | **45,797.3** | **91.6 %** |
| Conventional steam coal | 12,234.7 | 1,096.6 | 11,138.1 | **91.0 %** |
| Natural gas CC | 20,702.8 | 1,972.4 | 18,730.4 | **90.5 %** |

SPP's equivalent gap at its own Phase-0 audit was **44.9 %**.
**`campd.ISO_STATES["SOCO"]` should read `("AL", "GA", "MS", "FL")`.**

### 1.3 GATE G19 — CLOSED. The convention is `America/Chicago`, DST-aware, hour-ending

**Measured, not assumed**, over all 26,304 rows of the committed `SOCO hourly.parquet`:

| Candidate | Mismatching hours |
|---|---:|
| **`America/Chicago`, DST-aware** | **0** |
| `America/New_York`, DST-aware | 26,301 |
| fixed UTC−6 (CST) | 9,171 |
| fixed UTC−5 (EST) | 17,133 |

Corroborated by: exactly two UTC offsets (−6 / −5, a Central pair); the offset switching on
the correct US DST dates in each year; and **three duplicate `Local time` values**, one per
year, at the fall-back hours 2023-11-05 / 2024-11-03 / 2025-11-02 01:00 — absent from
`UTC time`, which has zero duplicates.

**`Hour` is EIA's hour-ENDING 1..24 (25 on the fall-back day); `Local date` is the date the
hour BEGINS in** — which accounts for all 1,096 rows where `Local date != Local time.date()`.

**The convention every downstream SOCO series must adopt:** `America/Chicago`, DST-aware,
hour-ending, **joined on `UTC time` and never on `Local time`** (non-unique once a year by
construction). **If card S3 lands 3 zones, all three are Central** — the timezone is a
property of the balancing authority, not of the zone; splitting Georgia onto Eastern would
put one zone's hour *t* against another's *t+1* in the same LP row.

**The charter's premise needed one correction and one addition.** `convert_eia930.py::BA_TIMEZONES`
**already carries `"SOCO": "US/Central"`** — that is the route that wrote the committed file.
But **two sibling dicts have no SOCO key and both default to `America/New_York`**:
`fetch_eia930_hourly.BA_TIMEZONE` and `build_eia930_hourly_from_raw.BA_TIMEZONE`. And
`fetch_eia930_interchange.py` **imports the first of those** — so **SOCO-11's interchange
pull (manifest row 3) will write Eastern local columns**, one hour off the committed demand
file for most of the year, with no error raised. Routed R-1/R-2.

---

## 2. The finding the charter did not anticipate — card S8 is worse than it assumed

`cod_ramp.effective_cod` **always** prefers the plant-collapsed COD over the generator's own
`Operating Month` for the **online** date; the per-unit preference exists only for
**retirement** (the Homer City seam). And `_load_cod_map` collapses a plant to a
**capacity-weighted mean** of its units' CODs. Measured by calling the live code:

```
load_cod_map()[649] -> (2005, 5, ...)   Vogtle   -> mask 111111111111 in 2023, 2024, 2025
load_cod_map()[3]   -> (1991, 3, ...)   Barry    -> mask 111111111111 in 2023
load_cod_map()[56]  -> (2023, 9, ...)   Lowman   -> mask 000000001111 in 2023  <- greenfield DOES ramp
```

So the ramp is **not broken — it is bypassed for exactly the units that need it**: brownfield
additions at multi-vintage plants.

Quantified against **measured** EIA-923 unit CFs (Vogtle 3 **88.6 %** Jul–Dec 2023;
Vogtle 4 **89.1 %** Apr–Dec 2024):

| Year | Phantom | TWh | vs measured `NG: NUC` |
|---|---|---:|---|
| 2023 | Vogtle 3 Jan–Jun + Vogtle 4 Jan–Dec | **12.979** | **+24.8 %** on 52.435 |
| 2024 | Vogtle 4 Jan–Mar | **2.167** | **+3.4 %** on 62.989 |

**A 2023 SOCO backcast would show ≈ 65.41 TWh of nuclear — above the measured 2025 value of
64.17 TWh — inverting the observed 52.4 → 63.0 → 64.2 commissioning step entirely**, and
displacing ~13 TWh of gas (≈10 % of the measured gas year) one-for-one. Barry A3 adds
**774 MW available 10 months early**, worth **2.3–4.6 TWh** (measured SOCO 2023 gas-fleet CF
40.7 % → measured Barry 2024 CC CF 81.3 %) — and **not independently checkable today,
because `AL_2023.parquet` does not exist**.

**Blast radius, measured across all eight footprints** (units with 2023–2025 CODs whose
plant-collapsed COD year is earlier):

| SOCO | SPP | ERCOT | CAISO | MISO | PJM | NYISO | NEISO |
|---:|---:|---:|---:|---:|---:|---:|---:|
| **3,040.3 MW** | 1,127.4 | 1,091.4 | 1,037.2 | 927.4 | 177.2 | 72.9 | 50.0 |

**SOCO is 2.7× the next-worst footprint, and Vogtle 3 and 4 are the two largest trapped
units in the national fleet.** The defect is general; it is material only where a GW-scale
brownfield addition lands inside a backcast window, and SOCO is the only such footprint.

**ROUTED AS AN OWNER CARD (R-4).** Options with blast radius are in audit §4.4. This lane
recommends **preferring the unit's own online date** (symmetric with the retirement seam
`effective_cod` already contains) — rule 14 `[R-ACCURATE]` points that way, the unit's
`Operating Month` being the accurate measured input and the plant mean the estimate — with
the cross-ISO A/B run as **its own lane, not inside SOCO-20**, because it moves results
(not cache keys) for all seven registered keepers. **Whatever the desk rules, the floor is
that the bias is stated on SOCO's first keeper's determination basis.**

---

## 3. Other findings, in brief

* **The 2025 "7 hours short" is NOT missing data.** The file is a complete UTC block
  (26,304 consecutive hours, zero gaps, zero duplicate UTC hours). Converting to Central
  spills 7 hour-ending labels onto local-date 2022-12-31 and leaves hours-ending 18–24 of
  2025-12-31 unfetched. `7 + 8,760 + 8,784 + 8,753 = 26,304` exactly. **Extend the fetch by
  7 UTC hours; never pad or interpolate** (the plan's own "explained, not padded").
* **`NG: PS` is a taxonomy cut-over, and the charter's framing hides a bigger problem.**
  `BAT`/`PS`/`SNB`/`OES` have byte-identical null patterns, all starting **2024-07-15 01:00**.
  Crucially, **`NG: WAT` never goes negative before that date** (min +32 MW over 13,470 h),
  so PS charging was **not** folded into hydro — it was **not reported at all**. **For 2023
  and most of 2024 SOCO's 1,306.6 MW of pumped storage is unobservable in EIA-930**, a hard
  constraint on the C1 `fuelmix` benchmark SOCO-31 builds. Routed R-6.
* **The median-ratio screen finds one real fuel defect and misses two others.** Four
  `NG: NG` hours in 2025 post **≈70,000 MW** against a **36,336 MW total gas nameplate**
  (1.95×, physically impossible); the `Demand + TI = NetGen` identity closes to 0.0000 TWh in
  2023 and 2024 and breaks in **2025 only** (595 h, max 13,120 MW, +0.696 TWh, with
  `Net generation` the corrupted side — it repeats 34,413 MW on two different days); and
  `Demand` notches to 12,638 MW for one hour on 2025-10-23 16:00 between neighbours of
  23,065 and 23,653. **`_screen_demand_spikes` (high side only) and `_screen_demand_dropouts`
  (exact 0.0 only) catch none of them, and no repo screen touches a fuel column at all.**
  Note also that `screen_physical_bounds` applied to `NG: SUN` flags ~4,000 h/yr — **a
  category error, not a defect**: it was derived on demand series and a diurnal series'
  noon peak is naturally ~100× its night-dominated median. Routed R-5. **No new screen
  constant is recommended here** — setting one after seeing the outliers would be a fitted
  threshold.
* **Independent validation of the extract.** EIA-930 `NG: NUC` vs EIA-923 monthly generation
  over the three nuclear plants agrees to **+0.58 % / −0.11 % / −0.10 %** — validating both
  the fuel attribution and the BA-code fleet filter.
* **SOCO is winter-peaking in 2 of 3 backcast years** — 47,368 MW on 2024-01-17 07:00 and
  46,490 MW on 2025-01-22 08:00, vs 45,558 MW on 2023-08-25 16:00; in 2025 summer sits
  0.25 % below winter. A **scalar** `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"]` would
  misrepresent this system. Georgia Power's own TRM is stated by season for that reason:
  **26 % winter / 20 % summer** (raised from 16.25 % summer), Docket 56002.
* **There is no wind in the SOCO fleet at all** — zero generators, `NG: WND` ≡ 0.000 TWh in
  all three years. Any wind-keyed registry entry describes an empty set. Routed R-12.
* **Card S7 (CAES):** map McIntosh on its **25 MW summer/winter rating**, not its 110 MW
  nameplate — a 77 % derate the source itself states. Routed R-8.
* **Data-profile token `soco` is collision-free**, but a `soco` profile does **not** pull
  `eia-930-hourly/SOCO hourly.parquet`, which lives under a `shared` directory. Routed R-10.

---

## 4. Card S3 — the zone recommendation, and the part that matters

**Recommend 3 zones (SOCO-Alabama / SOCO-Georgia / SOCO-Mississippi), split on the fleet's
state FIPS, Tier-3 non-binding TTCs — provided SOCO-11 delivers a reconciled hourly load
series per zone. If that reconciliation fails, register 1 zone and say why.**

**The fleet side is the cleanest of any registered ISO**: every generator carries an
unambiguous FIPS state, no plant straddles, no zone is a rump (GA 58.4 % / AL 34.7 % /
MS 6.5 % / FL 0.4 % of MW). **Name the zones geographically, not for the operating company** —
Georgia Power owns 241.6 MW *in Alabama*, and Oglethorpe + MEAG own 7.1 GW in Georgia that is
not Georgia Power's.

**The load side needs a scope correction to SOCO-11, before it starts (R-3).** The charter
says three FERC-714 respondents; measured off PUDL's `core_ferc714__respondent_id` there are
**eight**: Alabama Power (2), Georgia Power (183), Mississippi Power (184), **Gulf Power
(185)**, **Oglethorpe (107)**, **MEAG (210)**, **PowerSouth (1)**, **"Southern company"
(142, `eia_code` 18195)**. The three OpCos **structurally cannot** sum to the BA — Oglethorpe
and MEAG serve Georgia load inside the same BA that Georgia Power's planning area excludes,
and Georgia Power's own winter peak is **16,284 MW** against a BA winter peak of **47,368 MW**.
**Check respondent 142 first**: if it is the whole-BA filer, SOCO-11 has a direct
cross-check instead of a sum that cannot close.

**The part that matters — and it is why SOCO differs in kind, not degree.** Every prior
addition validates a zonal topology on the **price spread between zones**. Card S2
establishes SOCO has **no price at all**. So a SOCO zone split **can** be validated against
per-zone load (if SOCO-11's reconciliation closes), per-zone monthly generation from EIA-923,
and per-zone hourly fossil generation from CEMS **once AL and GA land** — and **cannot** be
validated against any zonal price or spread, any congestion measure (no shadow prices, no
binding-constraint archive, no congestion rent is published for this footprint and none will
be), or the TTCs themselves in either direction.

Two consequences, whichever way S3 goes:

1. **A zone split must not be sold as improving accuracy.** With non-binding TTCs, 3-zone
   and 1-zone SOCO produce **the same dispatch** until a TTC binds. Choose 3 zones for
   structure (rule 1 `[R-STRUCT]`) and say the fit is unchanged by construction — anything
   else invites a later lane to tune a TTC against a residual.
2. **Lever SOCO-54 (the inter-OpCo TTC derive) has no public source.** Pre-declare it with
   its evidence problem stated, so nobody discovers that in W5.

---

## 5. Routed items (full table in audit §7)

| # | To | Item |
|---|---|---|
| R-1 | SOCO-20 | Add `"SOCO": "America/Chicago"` to `fetch_eia930_hourly.BA_TIMEZONE` **and** `build_eia930_hourly_from_raw.BA_TIMEZONE` — both default to Eastern today |
| R-2 | **SOCO-11, NOW** | Don't fetch SOCO interchange before R-1, or join on `UTC time` and re-derive the local columns |
| R-3 | **SOCO-11, scope** | FERC-714 has **eight** footprint respondents, not three; check respondent 142 first |
| R-4 | **DESK → owner card** | `cod_ramp.effective_cod` online-date precedence — cross-ISO, SOCO worst-affected |
| R-5 | SOCO-20 / SOCO-31 | Seven unscreened EIA-930 artifact hours; no existing screen reaches any |
| R-6 | SOCO-31 / SOCO-40 | Pumped storage unobservable in EIA-930 for 2023 + most of 2024 |
| R-7 | SOCO-20 | `campd.ISO_STATES["SOCO"] = ("AL","GA","MS","FL")`; splitter must **fail loud**, not fall back |
| R-8 | SOCO-20 | CAES maps on its 25 MW rating, not 110 MW nameplate |
| R-9 | SOCO-20 | PSH summer capacity **exceeds** nameplate (EIA convention) — 9 rows will trip a `summer ≤ nameplate` assumption |
| R-10 | SOCO-20 | `soco` profile token is clean, but does not hydrate `eia-930-hourly/SOCO hourly.parquet` (gates G3/G18) |
| R-11 | `/sync-docs` | `cod_ramp.py` docstring says "earliest unit"; the code computes a capacity-weighted mean |
| R-12 | SOCO-20 / SOCO-30 | No wind in the footprint — any wind-keyed registry entry is an empty set |

---

## 6. Compliance

| Rule | How |
|---|---|
| 5 `[R-NO-MAGIC]` | Every registry-values row is a cited value or an explicit `pending <lane>`; nothing is blank and nothing is invented |
| 13 `[R-MEASURED]` | Every recommended input is a reproducible physical/market quantity. The **only** cross-market number quoted (Brattle ERCOT VOLL) is cited as **method, never value**, with the rule-25 prohibition stated inline |
| 14 `[R-ACCURATE]` | The card-S8 recommendation follows this rule explicitly: the unit's own `Operating Month` is the accurate input, the plant mean the estimate |
| 23 `[R-FROZEN-DERIVE]` | Nothing derived. The queue-cap **basis** (demonstrated peak annual COD) is reported; the **cap** is left to SOCO-20. No screen constant proposed |
| 25 `[R-ISO-SCOPE]` | No number is transferred between footprints |
| 27 `[R-PUSH]` | New file; existing files edited in place via targeted `str.replace` with `assert count == 1`, pushed as exact on-disk bytes, fetch-back verified (§7) |
| 28 `[R-MECH-MATRIX]` | No mechanism tested, proposed or armed. `mechanism-matrix/SOCO.js` does not exist yet — collision rule 2 is vacuous for this lane |
| Collision rule 1 | No shared record touched: not the plan, not the ledger, not `docs/calibration-log/`, not `CHANGELOG.md`, not the matrix |
| Gate G16 | `frontend/data/forecast/` untouched |
| CI | No workflow added (private repo, billed minutes) |

---

## 7. Verification

```
docs/multi-iso/soco-data-audit.md                      1174 lines, 86,618 bytes  (NEW)
docs/multi-iso/00-iso-addition-protocol.md             +18 / −1
docs/multi-iso/01-data-needs-and-upload-manifest.md    +39 / −0
```

All four files are **≥ 300 lines**, so rule 27 `[R-PUSH]`'s fetch-back verification applies.
It was performed after the push — remote blob line count + SHA-256 compared to local — and
**all four MATCH**:

| File | lines | sha256 (first 16) |
|---|---:|---|
| `docs/multi-iso/soco-data-audit.md` | 1,174 | `85dd8b5e524047a7` |
| `docs/multi-iso/00-iso-addition-protocol.md` | 304 | `e2dea1829bf2e4ab` |
| `docs/multi-iso/01-data-needs-and-upload-manifest.md` | 307 | `b45bfeafdcaf44e5` |
| `docs/handoffs/FINDING-soco-10-2026-09-13.md` | 401 | `997acfe786ad735a` (this table's own edit re-hashes it; the verified value is the pre-edit blob) |

Transport: `git push` (rebased onto `origin/main`, so the pack carries only this lane's
objects — ~95 KB of text, well inside the small-pack case CLAUDE.md licenses).

Every number in the audit is reproducible from the repo at `2c2fc065` with the eight
commands in `soco-data-audit.md` §8. Container prep: `python3 -m pip install pandas pyarrow
pydantic` (none preinstalled).

---

## Log entry

*(for `docs/calibration-log/soco.md`, appended verbatim by the DESK — collision rule 1)*

```
## soco-10 — 2026-09-13 — Phase-0 data audit (zero-LP)

Lane SOCO-10, Opus claude-opus-5, branch claude/soco-10-audit-k3m9, base 2c2fc065.
Deliverable: docs/multi-iso/soco-data-audit.md (NEW) + 00-iso-addition-protocol.md
§0/§3 + 01-data-needs-and-upload-manifest.md SOCO rows. No solve, no src/ edit,
no matrix cell, no shared record.

CENSUS. EIA-860 BA "SOCO": 336 plants / 788 gens / 70,667.2 MW nameplate
(66,161.2 summer / 69,096.8 winter). Charter's 335/786/70,665.7 is that MINUS the
1.5 MW MA row, while its own per-state list INCLUDES it and sums to 70,667.2 —
both right about different sets, one labelled. Per-state and per-technology all
confirm to 0.1 MW. MA row (plant 67241 "401 South", Berkshire MA, NERC NPCC)
REJECTED as an EIA-860 BA-field mis-entry under a stated two-key rule (SERC +
AL/GA/MS/FL-panhandle). Six FL plants (309.6 MW, all NERC SERC, panhandle) KEPT;
the load-side question (former Gulf Power, own FERC-714 respondent 185) routed to
SOCO-11. Reconciled to Southern's FY2024 10-K Item 2 (pp. I-30..I-33) on a stated
whole-unit-vs-ownership-share bridge; the wedge is exact on nuclear (10-K 4,786.7
MW vs EIA-860 8,282.4 MW = the Oglethorpe 30 / MEAG 22.7 / Dalton 2.2 % share of
Vogtle+Hatch).

CEMS GAP — THE CRITICAL PATH. No AL_*, GA_* or FL_* parquet for ANY year; MS
present 2019-2026. Missing for the window: {AL,GA} x {2023,2024,2025} = 6 files,
exactly as chartered. Worth 91.6 % of CEMS-eligible fossil MW (45,797.3 of
50,005.0), incl. 91.0 % of coal and 90.5 % of gas-CC. SPP's gap was 44.9 %.
ISO_STATES["SOCO"] should read ("AL","GA","MS","FL").

GATE G19 CLOSED. Committed SOCO hourly.parquet Local time == America/Chicago
DST-aware wall clock in 26,304 of 26,304 hours (New_York 26,301 mismatches, fixed
CST 9,171, fixed EST 17,133); two offsets only (-6/-5) switching on the correct
DST dates; 3 duplicate Local time values (fall-back hours), 0 duplicate UTC hours.
Hour is EIA hour-ENDING 1..24 (25 on fall-back day). CONVENTION FOR EVERY
DOWNSTREAM SERIES: America/Chicago, hour-ending, JOIN ON UTC time. All zones are
Central if S3 lands 3. convert_eia930.BA_TIMEZONES ALREADY carries
"SOCO": "US/Central" — but fetch_eia930_hourly.BA_TIMEZONE and
build_eia930_hourly_from_raw.BA_TIMEZONE do NOT and both default to Eastern, and
fetch_eia930_interchange imports the first — so SOCO-11's interchange pull writes
EASTERN unless fixed first (routed R-1/R-2).

CARD S8 — WORSE THAN THE CARD ASSUMED. cod_ramp.effective_cod always prefers the
plant-collapsed COD over the unit's own Operating Month for the ONLINE date (the
per-unit preference is retirement-only, the Homer City seam), and _load_cod_map
collapses a plant to a capacity-weighted MEAN. Measured live: load_cod_map()[649]
= (2005,5) so Vogtle 3 AND 4 are online all 12 months of 2023/24/25; [3] = (1991,3)
so Barry A3 is online all of 2023; [56] = (2023,9) so a GREENFIELD plant does ramp
— the bug is brownfield-only. Phantom energy at measured EIA-923 unit CFs (V3 88.6 %,
V4 89.1 %): +12.979 TWh in 2023 (+24.8 % on 52.435) and +2.167 TWh in 2024 (+3.4 %).
Modelled 2023 nuclear would read ~65.41 TWh, ABOVE measured 2025's 64.17 — inverting
the 52.4 -> 63.0 -> 64.2 step. Barry A3: 774 MW ten months early, 2.3-4.6 TWh.
Blast radius: SOCO 3,040.3 MW vs SPP 1,127.4 / ERCOT 1,091.4 / CAISO 1,037.2 /
MISO 927.4 / PJM 177.2 / NYISO 72.9 / NEISO 50.0 — SOCO worst by 2.7x and Vogtle
3/4 are the two largest trapped units nationally. ROUTED AS AN OWNER CARD (R-4);
recommendation is to prefer the unit's own date (rule 14), cross-ISO A/B as its own
lane, with "state the bias on the determination basis" as the floor.

EIA-930. All charter energy figures confirmed. TI is positive = NET EXPORT;
Demand + TI = NetGen closes to 0.0000 TWh in 2023 and 2024. 2025's "7 missing
hours" is a UTC-bounded fetch, not missing data (7+8760+8784+8753 = 26,304) —
extend by 7 h, never pad. NG: PS/BAT/SNB/OES nulls are an EIA taxonomy cut-over at
2024-07-15, and NG: WAT never goes negative before it (min +32 MW), so pumped
storage is UNOBSERVABLE for 2023 and most of 2024 (C1 constraint, routed R-6).
Defect screen: Demand is clean (max/median 1.79-1.84, both screens no-ops); four
NG: NG hours post ~70 GW against a 36,336 MW gas fleet; the netgen identity breaks
in 2025 only (595 h, max 13,120 MW, +0.696 TWh, netgen the corrupted side); one 1-h
partial demand dropout at 2025-10-23 16:00 (12,638 MW). NO EXISTING SCREEN CATCHES
ANY OF THEM (routed R-5); no new constant proposed (rule 23). Independent check:
EIA-930 NG: NUC vs EIA-923 agrees to +0.58 / -0.11 / -0.10 %.

CARD S6 EVIDENCE. SOCO is WINTER-peaking in 2 of 3 years (47,368 MW 2024-01-17
07:00; 46,490 MW 2025-01-22 08:00) and summer-peaking in 2023 (45,558 MW
2023-08-25 16:00); 2025's summer peak is 0.25 % below its winter peak. A scalar PRM
misrepresents this system. Georgia Power 2025 IRP (Docket 56002): 26 % winter /
20 % summer TRM, raised from 16.25 % summer.

CARD S3 RECOMMENDATION (recommend only). 3 zones on state FIPS (AL/GA/MS, FL->AL,
no MA key), Tier-3 non-binding TTCs, IF SOCO-11's load reconciliation closes; else
1 zone. Fleet side is the cleanest of any registered ISO. Load side needs a scope
correction: FERC-714 has EIGHT footprint respondents, not three (Gulf Power 185,
Oglethorpe 107, MEAG 210, PowerSouth 1, "Southern company" 142 alongside the three
OpCos), and the three OpCos structurally cannot sum to the BA — GP's own winter
peak is 16,284 MW against a BA peak of 47,368 MW. Check respondent 142 first
(routed R-3). THE PART THAT MATTERS: with no price, a SOCO zone split can be
validated on load, monthly per-zone generation and (once AL/GA CEMS land) hourly
fossil generation — and can NEVER be validated on price spread, congestion or the
TTCs themselves. 3-zone and 1-zone SOCO produce the SAME dispatch until a TTC
binds, so the split must be chosen for structure and never sold as accuracy.

CARD S5 NOTE. $2,000/MWh is FERC Order 831's OFFER cap. SOCO takes no offers —
cost-based dispatch, no DA market, no LMP, no capacity market. Recommend an
economic VOLL from the DOE/LBNL ICE calculator on the SERC/Southeast class mix
(pending SOCO-12); the Brattle ERCOT study is cited as METHOD only, never value
(rule 25). If nothing citable survives Phase 0, $2,000 is acceptable ONLY with the
misalignment written on the field and the value ledgered under rule 21.

OTHER: no wind anywhere in the SOCO fleet (R-12); CAES maps on 25 MW not 110 MW
(R-8); PSH summer capacity exceeds nameplate, 9 rows (R-9); `soco` profile token is
collision-free but does not hydrate eia-930-hourly/SOCO hourly.parquet (R-10);
cod_ramp.py docstring is stale vs its own code (R-11). Registry-values table: 18
rows, every cell a citation or an explicit pending. Manual manifest: 12 items with
exact URLs.
```
