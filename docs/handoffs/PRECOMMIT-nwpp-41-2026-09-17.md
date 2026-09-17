# PRECOMMIT — lane NWPP-41: the C1 coal-taxonomy seam is CLOSED zero-LP; C4's root cause is measured and ROUTED

**Lane** NWPP-41 (Fable) · **DATA PROFILE** `nwpp` · **Base** `origin/main` @ `73281357` (after PR #6257)
· **Predecessor** `docs/handoffs/FINDING-nwpp-40-2026-09-16.md`, whose §7.1 (C1) and §7.2 (C4) are this
lane's object · **Run under study** `2026-09-16-nwpp-1-cascade`, bundle `results/calibration/nwpp40_span_A`
· **LP SPENT BY THIS SESSION: ZERO.** Every number below is a `fleet_only` rebuild, a committed-sidecar
read, or a benchmark re-derive. The parent never solved (rule 32 `[R-SHARD]` (a)).

**Owner ruling on promotion of `2026-09-16-nwpp-1-cascade`: STILL OPEN.** NWPP has no
`frontend/data/backcast/keepers/NWPP.json` and is absent from `keepers/index.json`, so the registered
run is this lane's only NWPP baseline and is treated as the rule-29(b) control.

---

## 0. Result first

1. **C1 IS A PURE PLUMBING SEAM AND IT IS CLOSED, WITH THE DISPATCH BYTE-IDENTICAL.** Landing the
   missing derived artifact `data/raw/_processed-legacy/coal_supply_NWPP.csv` takes C1 from **5 FAIL
   rows to 0** across 2023–2024 (2025 stays SKIPPED on the preliminary-923 rule). Not one MW of
   dispatch moves in the measurement: the committed `dispatch/<year>_P1.parquet` are relabelled and
   re-scored. C2 and C4 are **byte-identical** in both legs.
2. **The seam was bigger than the coal rows.** `calibration_verdict._gen_totals` computes the model's
   generation total as `sum(gmModel[g] for g in classFull)` — over the BENCHMARK's class keys. The
   benchmark has no bare `COAL` key, so **the model's entire 38.5 / 26.5 / 26.4 TWh of coal was
   excluded from its own share denominator**, inflating every other class's share by ~14 %. That, not
   a gas defect, is why FINDING-nwpp-40 §0.2 recorded a 2024 `CC_REGULAR` share of +3.6 pp: it reads
   **+1.4 pp** once coal is counted, and the row goes FAIL → PASS untouched.
3. **The derive is NOT free: as written it imports an ERCOT price onto three Montana plants.**
   `fuel/coal.py::apply_coal_supply_pricing` reprices every `prb`-tagged plant with
   `_prb_monthly_actuals()`, which is built from `COAL_PLANT_SUPPLY` — **all ten of whose plants are in
   Texas** (Limestone, W A Parish, Martin Lake, Coleto Creek, Fayette, Oak Grove, San Miguel, Major
   Oak, J K Spruce, Sandy Creek). Landing the derive alone therefore prices **Colstrip, Hardin and
   Western Sugar** (and TS Power in 2025) at ERCOT's railed-PRB delivered cost — a rule 25
   `[R-ISO-SCOPE]` breach, and the reason this lane stops for a ruling rather than solving.
4. **C4's root cause is measured and it is NOT an over-aggressive floor.** The NWPP coal offer stack is
   **bimodal with nothing in between** — `mustrun` at **$4.50/MWh** (VOM-only, in the money 100 % of
   hours) and `committed`/`econ`/`peak` at a capacity-weighted **$37.7–$42.8/MWh**, against a mean
   zonal price of **$26.15**. So 2,165 MW runs flat in all 8,760 h and ~4,600 MW of AVAILABLE coal is
   out of merit in 87 % of hours. The flat shape and the 8–23 TWh volume shortfall are **one defect**,
   not two. Availability is ruled out as the cause by measurement (§4).
5. **C4 is ROUTED, not guessed.** The physically-grounded successor — pricing an already-synchronised
   unit's next MWh at its **measured CEMS incremental heat rate** (0.77–0.90 × base HR where it has
   been derived: PJM 0.771, MISO 0.798, ERCOT 0.867) — cannot be identified for NWPP today:
   `scripts/data/derive_campd_marginal_hr.py` needs `data/raw/_processed-legacy/bin_assignments_NWPP.csv`,
   which **does not exist** (no legacy-bin ISO has one). Rule 25 forbids borrowing another ISO's number.
   The prerequisite is named in §6; no value is proposed here.

---

## 1. C1 — the defect, located exactly

Both sides of the scorer call the SAME resolver, but with different arguments:

| side | call | NWPP result |
|---|---|---|
| benchmark | `classify_plant(fuel, pm, chp, pid, coal_class_resolver=_coal_supply_class)` — the 923 row's **own fuel code** is passed | `COAL_PRB` / `COAL_BIT` / `COAL_WC` via `coal_code_to_class(fuel)` |
| model | `run_calibration_full.py:414` `_coal_supply_class(int(plant_codes[g]))` — **no fuel code** | `coal_supply_class(code)` → `""` → bare **`COAL`** |

`coal_supply_class` resolves in four steps: the curated ERCOT map, `_derived_coal_supply()` (globs
`coal_supply_<ISO>.csv`), a mid-backcast-retiree EIA-860 fallback, and a gated partial-exit registry.
**NWPP hits none of them, because `coal_supply_NWPP.csv` was never derived** — MISO, NEISO, PJM, SOCO
and SPP all have one. With the model's `fuel_code` empty, the third arm of `_coal_supply_class` is
dead, so the asymmetry is total: the bench splits, the model cannot.

This is the SPP-62 defect one layer deeper (`docs/handoffs/FINDING-spp-62-2026-09-10.md`: a *census*
gap left 4.36 TWh in a bare `COAL` class "in no C1 row at all"). NWPP's whole coal fleet is in that
state.

**The derive, run on NWPP's own data** (`--iso NWPP --census-vintage 2023 2024 2025`): census 17
plants from the canonical snapshot, `vintage_2023` and `vintage_2024` add nothing, no `vintage_2025`;
**17 of 17 classified, 0 unresolved** — 9 `prb`, 6 `bituminous`, 2 `waste`. No raw `f923_*.zip` on
disk, so every row is classified from the committed Page-1 generation parquet — the same
energy-source-code signal the benchmark uses. **Zero free parameters.**

**Rule 25 collision check, mechanical:** the 17 plant codes intersect `coal_supply_{MISO,NEISO,PJM,SOCO,SPP}.csv`
and the curated ERCOT `COAL_PLANT_SUPPLY` in **zero** codes, so landing the file cannot move any other
ISO's fleet.

## 2. What C1 reads after the fix — measured, dispatch unchanged

Committed `dispatch/<year>_P1.parquet` relabelled by the derived rank (17/17 plants resolve, zero
residual `COAL`), sidecars and benchmark re-derived, `score_fuelmix` re-run:

| year | control | armed |
|---|---|---|
| 2023 | `COAL_PRB` **−25.28 TWh / −9.0 pp FAIL**, `COAL_BIT` **−13.90 / −5.0 pp FAIL** | `COAL_PRB` −2.44 / −0.6 pp **PASS**, `COAL_BIT` +1.38 / +0.7 pp **PASS**, `COAL_WC` −0.13 **PASS** |
| 2024 | `COAL_PRB` **−20.96 / −7.2 pp FAIL**, `COAL_BIT` **−12.78 / −4.4 pp FAIL**, `CC_REGULAR` **+3.6 pp FAIL** | `COAL_PRB` −2.18 / −0.5 pp **PASS**, `COAL_BIT` −5.29 / −1.7 pp **PASS**, `CC_REGULAR` **+1.4 pp PASS** |
| 2025 | 8 rows SKIPPED (preliminary 923) | unchanged — 8 SKIPPED |

**C1: 5 FAIL → 0 FAIL.** `score_dispatch_corr` (C4) and `score_sysvol` (C2) are **byte-identical** in
both legs — C4 coal still `r=0.511 / 0.535 / 0.475`, FAIL — so nothing is being smuggled through the
relabel. C2's "C1 flags" annotations clear.

**Benchmark-side movement, reported at full magnitude.** Arming the derive also changes how the
BENCHMARK splits coal, because `_coal_supply_class` is its first resolution step too: a mixed-rank
plant (Centralia 60 % bit / 40 % prb, Dave Johnston 67/33, North Valmy 63/37) stops splitting
per-923-row and goes wholly to its dominant rank. `COAL_BIT` +4.67 / +3.36 / +3.30 TWh and `COAL_PRB`
the same amount negative; **the coal FAMILY total is unchanged** (44.074 → 44.074 in 2023). This is
not a free choice: the model carries ONE class per plant (`_coal_class_for` is per-plant), so
plant-dominant rank is the only rule both sides can express, and it is the rule `coal_class_resolver`
was built for.

**Byte-reproduction anchor:** re-running `--rebuild-benchmark` on the untouched bundle reproduces the
committed hashes exactly (`eia923-b651a5f68862`, `eia930-e539ed483b64`, `campd-a5fde7813755`), so §2's
armed-leg deltas are exact, not approximate.

## 3. The rule-25 side effect, and the three routes

`apply_coal_supply_pricing` is gated by `coal_supply_repricing` (**True** in this run) and overwrites
every `prb`-tagged plant's delivered fuel price with `_prb_monthly_actuals()`. Measured offer-array
delta (`scripts/probes/_nwpp41_coalrank_phase0.py`, `run_year(..., fleet_only=True)` on the bundle's
own recipe via the sanctioned `replay_keeper` path):

```
2023  COAL n=88  offer max|d| $16.6687/MWh  7 rows moved   NON-COAL max|d| $0.0000000000  0 rows
2024  COAL n=88  offer max|d| $18.2921/MWh  7 rows moved   NON-COAL max|d| $0.0000000000  0 rows
2025  COAL n=88  offer max|d| $20.9783/MWh 11 rows moved   NON-COAL max|d| $0.0000000000  0 rows
```

`pmax` and `availability` max|Δ| are **exactly 0** everywhere. The movers are the plants that file no
EIA-923 fuel price (FINDING-nwpp-40 §5 line 9): **6076 Colstrip** and **55749 Hardin** in every year,
**62319 Western Sugar** always, **56224 TS Power** in 2025 only (its 2025 price is not yet filed).
Their delivered cost goes **$2.843 → $1.752/MMBtu** (2024), i.e. Colstrip's committed band
$34.55 → $23.02/MWh.

**$1.752 is ERCOT's number.** `_prb_monthly_actuals` pools the EIA-923 coal-cost reporters in
`COAL_PLANT_SUPPLY`, and every one of them is in Texas. NWPP has **four of its own PRB reporters**
covering all 36 months of the span — 4158 Dave Johnston, 4162 Naughton, 6101 Wyodak, 8066 Jim Bridger:

| year | ERCOT proxy (what the derive would import) | NWPP's OWN qty-weighted PRB cost |
|---|---|---|
| 2023 | 1.818 | **2.463** |
| 2024 | 1.760 | **2.134** |
| 2025 | 1.622 | **2.066** |

Texas railed PRB is **$0.44–0.65/MMBtu cheaper** than what NWPP's own PRB plants actually paid.
Importing it would under-price Colstrip — the largest plant in the fleet — on another market's data.

**The three routes, with the cost of each stated:**

- **(a) land the derive as written.** C1 closes; a Texas price lands on three Montana plants.
  **Not recommended — rule 25 `[R-ISO-SCOPE]`, rule 28(d).**
- **(b) land the derive + `coal_supply_repricing=False` for NWPP.** Config only, no `src/` edit.
  **PROVEN EXACTLY INERT**: with this leg the probe reads `offer max|d| $0.0000000000/MWh, 0 rows
  moved` on **coal and non-coal alike, in all three years** — so the LP solution is unchanged by
  construction and **C1 closes with ZERO LP**. Cost: Colstrip, Hardin and Western Sugar keep the
  undifferentiated generic $2.843/MMBtu, which is itself a cross-class average.
- **(c) land the derive + make `_prb_monthly_actuals()` ISO-scoped** so a PRB non-reporter takes its
  OWN region's measured PRB cost. Rule 14 `[R-ACCURATE]` best, NWPP's own data, zero free parameters
  (four reporters, quantity-weighted, the identical construction already used for ERCOT). Cost: a
  `src/market_sim/data/fuel/coal.py` edit — **the desk must route it** — and a full-span solve.

**This lane recommends (c)**, on rule 14 alone: a plant that burns PRB should pay a measured PRB
delivered cost, and NWPP has one. Its effect on C4 (Colstrip's committed band falls ~$0.71/MMBtu
rather than the $1.09 route (a) would give) is **reported as a consequence, never as the reason** —
rule 1 `[R-STRUCT]`.

**Not fixed by any route, named rather than absorbed:** `apply_coal_supply_pricing` prices only
`lignite` and `prb`, so **3845 Centralia** (bituminous, 670 MW) and **10784 Colstrip Energy LP**
(waste) stay on the generic $2.843 whatever is decided. Centralia files no EIA-923 price and the model
runs it at cf 0.045–0.156. A bituminous/waste delivered-cost trajectory is a separate object and is
not invented here.

## 4. C4 — the root cause, measured

**Availability is ruled out.** Rebuilt for 2024: coal nameplate 9,675 MW, **mean available 7,606 MW**
(min 4,694, max 9,299) — and the availability profile is FLAT across the hour of day. The model
dispatches ~3,019 MW average. **~4,600 MW of available coal sits idle**; the measured fleet averages
5,222 MW.

**The offer stack, 2024, capacity-weighted, against a $26.15 mean zonal price:**

| band | n | pmax MW | avail MW | offer $/MWh | fraction of hours in the money |
|---|---|---|---|---|---|
| `mustrun` | 14 | 2,630 | 2,165 | **4.50** | **1.000** |
| `committed` | 16 | 2,733 | 2,138 | 37.72 | 0.241 |
| `econlo` | 15 | 1,418 | 1,184 | 42.80 | 0.133 |
| `econhi` | 15 | 1,160 | 968 | 42.80 | 0.133 |
| `peak` | 16 | 162 | 132 | 39.63 | 0.200 |

There is **nothing between $4.50 and $37.72**. A real coal unit's cycling happens inside that gap.
Consequently the band profiles are:

| band | 2023 TWh (peak/trough of hour-of-day) | 2024 | 2025 |
|---|---|---|---|
| `mustrun` | 18.16 (**1.01**) | 18.97 (**1.00**) | 17.85 (**1.00**) |
| `committed` | 10.85 (1.02) | 4.69 (1.04) | 5.68 (1.01) |
| econ + peak | 9.53 (1.04–1.05) | 2.83 (1.17–1.21) | 2.83 (1.12–1.23) |

In 2025, `mustrun` + `committed` are **90 % of model coal and flat to within 1 %**. Every plant is
flat: hour-of-day peak/trough 1.00–1.12 for all 17.

**What the fleet actually does** (CEMS, the 17 plants, summed):

| | h10–12 trough | h19–20 peak | peak/trough |
|---|---|---|---|
| 2023 measured | 5,276 | 6,361 | 1.21 |
| 2024 measured | 4,624 | 6,110 | 1.32 |
| 2025 measured | 4,753 | 6,647 | **1.40** |
| 2025 model | 2,975 | 3,043 | **1.02** |

The measured trough is at **midday** and it deepens as NWPP solar grows 13.0 → 17.2 → 20.1 TWh. The
missing behaviour is specifically the **midday solar de-load and evening re-ramp of coal**, and the
model cannot express it because 90 % of its coal is price-insensitive.

**Rule 20's C8 gate is structurally blind to this** and reads 0.0 % forced in every class: the
`mustrun` tranche is an OFFER-PRICE band, not a `min_gen` floor, so nothing counts it as forcing. That
is worth the desk's attention independently of NWPP.

## 5. Gates and hygiene

- `git status` clean apart from the new probe; `results/calibration/nwpp40_span_A/meta.json` restored
  byte-identical after the benchmark re-derives (`git checkout HEAD --`).
- Nothing deleted (rule 31 `[R-RETAIN]`). The full 36-file bundle was fetched from the shard branch
  `claude/nwpp-40-span-b` @ `fe09a98e72efe473b4e5f1a3ea0ecbedd9178f0a` and is in this container's
  working tree; the committed slim set on `main` is unchanged.
- Scratch artifacts (the derived CSV, the relabelled bundle copy, the armed benchmark parquet) were
  removed after measurement; **the derived CSV is reproducible in ~90 s** by the command in §1 and is
  NOT a solved result.
- Rule 28 `[R-MECH-MATRIX]` (a): the NWPP lever queue (`docs/mechanism-testing-matrix.md` §5.9,
  levers NWPP-55…59) targets TTC, priced seams, WRAP, zones and the retirement sector gate. **This
  lane goes off-queue and says so**: the queue was seeded before any NWPP solve existed, and neither
  of the two failures the first solve actually produced (C1 taxonomy, C4 coal shape) is on it.
  No cell is moved by this PRECOMMIT because no mechanism has been tested yet.
- Rule 29 `[R-SCREEN]`'s screen regime is REMOVED as of 2026-09-16, so §5.9's "one-year screen then
  the span" text is spent; any solve this lane launches goes straight to `--year 2023 2024 2025`
  (rules 16 / 34(c)).

## 6. Routed, with the prerequisite named

1. **C4's successor needs `data/raw/_processed-legacy/bin_assignments_NWPP.csv`.**
   `derive_campd_marginal_hr.py --iso NWPP` is the measured, per-ISO, zero-DOF identification of what a
   committed coal unit's next MWh costs, and it exits 2 without that crosswalk. No legacy-bin ISO
   (NWPP, SPP, SOCO) has one. Building it is a data-intake task, not a calibration one.
2. **Centralia and Colstrip Energy LP have no delivered fuel price under any route** (§3).
3. **C8 does not see an offer-price must-run band** (§4) — a cross-ISO governance question.
4. FINDING-nwpp-40 §7 items 3–7 (CO2 coverage, the energy-balance seam, Chief Joseph 2025, the
   NWPP-SNV VOLL hours, per-year cache keys) are **untouched by this lane** and stay routed as
   written.

## 7. What this lane will do once the desk rules

- **(b)** → relabel and re-score in place, register the corrected run, **no shard**.
- **(c)** → land the derive + the ISO-scoped PRB proxy, PRECOMMIT addendum with the expected numbers,
  then ONE shard, ONE `--year 2023 2024 2025` invocation, 600-min budget (measured 551 min), bundle
  pushed with a `.gitignore` negation and a plain `git add` (rules 32 / 34).
