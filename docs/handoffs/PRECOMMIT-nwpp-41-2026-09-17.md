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

---

# ADDENDUM 1 (2026-09-18) — the desk ruled; route (c) is built, and these are its expected numbers BEFORE the solve

**Owner ruling, this session, on the three questions §3 and §6 put:**

1. **C1 route → (c), the ISO-scoped PRB proxy.** The `src/` edit is routed.
2. **C4 → route it, do not attempt it here.** Leave C4 FAIL, reported at full magnitude, with the
   prerequisite named. No band multiplier is chosen on a value NWPP has not measured.
3. **Promotion → promote AFTER the C1 fix lands.** The corrected run becomes the first NWPP keeper;
   `2026-09-16-nwpp-1-cascade` is not designated as-is.

Everything below is fixed **before any LP runs**, so nothing here can be written to fit a result.

## A1.1 What was built

| # | change | why it is not a free parameter |
|---|---|---|
| 1 | `data/raw/_processed-legacy/coal_supply_NWPP.csv` — 17 rows, 9 `prb` / 6 `bituminous` / 2 `waste`, 0 unresolved | `derive_coal_supply.py --iso NWPP --census-vintage 2023 2024 2025`, the artifact every other coal ISO already has. md5 `4bc7f9a61724ec4562599230ca77e4c6`; reproducible in ~90 s |
| 2 | `data.coal.coal_supply_by_iso(iso)` — reads ONE ISO's rank file | new reader, no value. `_derived_coal_supply` unions every ISO's file, which is right for *resolving a plant* and wrong for *pooling a population* |
| 3 | `data.fuel.coal._prb_monthly_actuals(iso=None)` — `None` keeps today's ERCOT-pooled series byte-for-byte; an ISO pools its own reporters | quantity-weighted mean of that market's own filed EIA-923 receipts — the identical construction ERCOT already uses |
| 4 | `ScenarioConfig.coal_prb_proxy_own_iso: bool = False`, on `_CACHE_KEY_OPTIONAL_FIELDS` with frozen drop value `"False"`, `TIER_TAGS` 3 | a gate, not a number |
| 5 | armed in `pipeline/backcast_config.py` as `coal_prb_proxy_own_iso=(iso.upper() == "NWPP")` | same idiom as the adjacent `coal_takeorpay_from_data=(iso.upper() == "MISO")` |
| 6 | matrix row + a cell in all nine ISO shards | rule 28(c) |

**The arming seam was corrected mid-build and the reason is worth recording.** The first attempt armed
the flag through `iso_configs._nwpp_config.default_scenario_overrides`, copying the D57 / D67 / D75-R
pattern. That is a **forecast-only** seam: `runner.py`'s own docstring states that
`run_calibration_full.py` *"never applies `default_scenario_overrides` at all"*, so the arm would have
been **dead on the backcast path** — the lever would have looked armed in the config and changed
nothing in the solve. Those three precedents are all capacity-screen (forecast) arms. Reverted; the
arm is in `backcast_config`, which is the builder the backcast actually goes through.

## A1.2 Confinement and key-inertness — measured, zero LP

`scripts/probes/_nwpp41_coalrank_phase0.py 2023 2024 2025 --own-iso`, `run_year(..., fleet_only=True)`
on the registered bundle's own recipe:

| year | NON-COAL offer max&#124;Δ&#124; | coal rows moved | `pmax` max&#124;Δ&#124; | `availability` max&#124;Δ&#124; | coal cap-wtd mean offer Δ |
|---|---|---|---|---|---|
| 2023 | **$0.0000000000** (0 rows) | 7 | 0.0000000000 | 0.000000000000 | −$0.6528 |
| 2024 | **$0.0000000000** (0 rows) | 7 | 0.0000000000 | 0.000000000000 | −$0.8278 |
| 2025 | **$0.0000000000** (0 rows) | 11 | 0.0000000000 | 0.000000000000 | −$0.8857 |

The movers are only the PRB plants that file no delivered cost: **6076 Colstrip** and **55749 Hardin**
every year, **56224 TS Power** in 2025 only. `62319 Western Sugar` is repriced too but carries 0.655 MW
and contributes no distinct offer row.

| plant · band | 2023 ctl → arm | 2024 | 2025 |
|---|---|---|---|
| Colstrip `committed` / `peak` | 34.252 → **27.226** | 34.550 → **25.640** | 34.850 → **25.640** |
| Colstrip `mustrun` | 4.500 → 4.500 (VOM-only, unmoved) | same | same |
| Hardin `committed` / `econlo` / `econhi` / `peak` | 49.093 → **38.562** | 49.539 → **36.186** | 49.989 → **36.186** |
| TS Power (2025 only) | — | — | 56.272 → **53.973** |

**The scoping is the point, and it is worth $2–4/MWh.** Under the unscoped route (a) Colstrip would
have gone to 23.766 / 23.016 / 21.560 — i.e. route (c) prices it **$3.5 / $2.6 / $4.1 higher**, which is
exactly the Texas-rail discount rule 25 refuses.

**Cache keys.** Every one of the **19 committed `run_config.json`** reconstructs with
`coal_prb_proxy_own_iso = False`, the frozen drop value — including `nwpp40_span_A` itself — so **no
existing bundle re-keys** and no other ISO's keeper moves. A fresh armed NWPP run earns a distinct key
(`4e9a865340b97c0b` → `71eab0fef3bb3ecb` on a bare NWPP config).

## A1.3 Expected result of the solve, pre-registered

- **C1: 5 FAIL → 0 FAIL.** §2's relabel measurement holds by construction for the taxonomy half; the
  repricing half moves coal volumes, so the exact rows will differ from §2's table. **Pre-registered
  direction and bound:** Colstrip and Hardin get cheaper, so model coal can only rise or hold —
  2023 `COAL_BIT` +1.38 TWh is the only row with headroom to spare (band ±8 TWh, ±3 pp), and the
  2024/2025 coal rows are all currently NEGATIVE (−5.29, −2.18, −0.33), so a rise moves them toward
  zero. C1 is expected to pass in 2023 and 2024; 2025 stays SKIPPED.
- **C2 coal, 2024:** model 26.49 vs 34.32 actual today. Expected to rise; **no target is named** and
  C2 already PASSes on the family band, so this is a report line, not a criterion.
- **C4: still FAIL, and that is the expected outcome.** The repricing lowers two plants' *level*; it
  does not put a band between $4.50 and $37.7 (§4). A 2025 coal peak/trough of 1.02 → anything below
  ~1.2 leaves `cv_ratio` short of the 0.5 gate. **If C4 passes, that is a surprise and this lane will
  say so rather than claim it.**
- **C3a/C3b/C3c: UNSCORED**, unchanged — NWPP has no `actual_lmp.json` block, so the run certifies no
  price level, shape or tail, and its determination names that basis (owner ruling N2).
- **Expected determination: `NOT-YET`**, with **C4 coal shape as the single remaining failure** where
  the registered run has five. That is the promotion the desk authorised, and it is not `CALIBRATED`.
- **Report-only items carried unchanged, not absorbed:** CO2 −55 to −66 %; energy balance −7 to
  −10 TWh/yr; NWPP-SNV VOLL hours 23 + 34; Chief Joseph 2025 coupling dual −325.17 for 5,808 h.

## A1.4 The shard

ONE shard, ONE `--year 2023 2024 2025` invocation, years sequential inside it (rules 12 / 16 / 32(b)),
**600-minute budget** (NWPP-40 measured 551 min; peak 4.35 GiB against a 13.36 GiB cgroup). It pushes
its own bundle to its own branch via a `.gitignore` negation and a **plain `git add`** (rule 34(a)), and
it must show the armed signature — `coal_prb_proxy_own_iso: true`, `coal_supply_NWPP.csv` present with
md5 `4bc7f9a61724ec4562599230ca77e4c6`, `hydro_cascade_coupling true`, `hydro_backfill_year 2024` — or
STOP without pushing. The parent registers, promotes and prunes (rules 15 / 32(d) / 35).

---

# ADDENDUM 2 (2026-09-18) — the shard's budget is raised 600 → 780 min on its OWN measured P0 rate

**Recipe unchanged. Pin unchanged (`666343a2bf86f204c5ca6c672a680da32150a640`). Only the time
budget moves**, and it moves *before* the shard could hit the old ceiling rather than after.

**The measurement.** The shard's first status report, at 04:35:48Z:
`2023 P0 complete (1512.4s, 515K iterations); now in P1`.

| | NWPP-40 (registered run) | NWPP-41 shard | ratio |
|---|---|---|---|
| 2023 P0 seconds | 1,236.5 | **1,512.4** | **1.22×** |
| 2023 P0 HiGHS iterations | 523,199 | ~515,000 | 0.98× |

**The same LP on a slower container, not a regression.** The iteration count is within 2 % of
NWPP-40's, so the problem HiGHS is solving is the same size and shape — which is what the
offer-array probe already proved from the other direction (non-coal max&#124;Δ&#124; exactly
$0.0000000000; only 7 coal rows move). What differs is seconds per iteration.

**The projection, and why waiting would have been the expensive choice.** NWPP-40's span was
33,038.5 s = 550.6 min. At 1.22× that projects to **≈672 min**, which overruns the 600-min budget
Addendum 1 §A1.4 set — and rule 32(b)'s stop rule is unambiguous: *"A shard approaching 20 minutes
with no artifact stops and reports; it never pushes a half-written bundle."* Applied to a 600-min
budget that means the shard would have stopped somewhere inside 2025 P1, with two years solved and
nothing pushed. **780 min** carries the projection with ~16 % margin. Precedent: NWPP-40 re-budgeted
twice by exactly this route (150 → 480 min on its own measured 2023 rate, then → 600 min), its
Addenda 1 and 2.

**Mechanics, recorded because the first attempt failed.** A routine's prompt can only be edited from
the conversation it posts into, so the two keep-alive pokes were **deleted and recreated** rather
than updated: `trig_01EPuqbN1HZ4HSc7EYQ6eotf` / `trig_015e6z1RbJ75tuWqGwk9X9hA` →
**`trig_016ykqCP9jmUezNDBJu6BCE1`** (minute 5) and **`trig_01EBYncSmmRn77caEo3W33i5`** (minute 35).
Both carry the 780-min budget and state that it supersedes the 600 in the shard's original prompt.
**These two are the triggers the promoting check-in must delete** (rule 33), not the deleted pair.

**The poke mechanism is confirmed working, by measurement.** The shard ran no turn between 03:51:48Z
and the first poke; the deleted offset trigger's `last_run` reads
`SUCCEEDED, fired_at 2026-09-18T04:35:37.968Z`, and the shard's `updated_at` moved to 04:35:48Z with
a fresh per-pass status detail. That matters because a cloud shard is **not** reachable by
`SendMessage` from the parent (`ListAgents` shows no peers; a direct send returns *"No agent named …
is reachable"*), so the persistent-session routine is the ONLY channel the parent has — and a shard
that never wakes never pushes, which is the rule-34 `[R-SHARD-PROMOTABLE]` stranding this lane's
whole 780-minute budget rides on.

**Unchanged by this addendum:** every expected number in §A1.3, the hard-stop signature the shard
must show, the registration and promotion sequence, and the rule-35 year-set enumeration.

---

# ADDENDUM 3 (2026-09-18) — budget raised again, 780 → 1,020 min; 2023 is solved and the ratio is WORSE than Addendum 2 projected

**Recipe unchanged. Pin unchanged (`666343a2bf86f204c5ca6c672a680da32150a640`). Only the ceiling moves.**

**Observed.** At 06:35:56Z: `span_A solve in progress (2024 P0, 2025 pending)` — so 2023 is complete
on both passes and the run is in 2024 P0. The two interim reports were
`2023 P0 complete (1512.4s, 515K iterations)` at 04:35:48Z and
`LP pass 2023 P1 in progress (63 min)` at 05:36:09Z.

**The problem: 2023 P1's completion time was never reported, only bracketed.** The status prose
carried no per-pass seconds for it, so the ratio has to be inferred from when 2024 P0 appeared. On an
LP start of ~04:08Z (2023 P0 = 1,512.4 s, finishing just before its 04:35:48Z report):

| 2023 done at | 2023 elapsed | ratio vs NWPP-40's 81.8 min | projected 2024+2025 | TOTAL from shard start | vs 780 |
|---|---|---|---|---|---|
| ~05:50Z | 102 min | 1.25× | ~583 min | ~718 min | inside |
| ~06:05Z | 117 min | 1.43× | ~668 min | ~818 min | **OVER** |
| ~06:20Z | 132 min | 1.61× | ~754 min | ~919 min | **OVER** |
| ~06:35Z | 147 min | 1.80× | ~840 min | ~1,020 min | **OVER** |

2024 + 2025 are **85 %** of NWPP-40's span (467.6 of 549.5 min), so the remaining work is where the
ratio bites. **Three of the four brackets overrun 780 min**, and only the most optimistic survives.

**Decision: 1,020 min.** It covers even the 1.80× bracket. The asymmetry is the whole argument — a
shard that finishes early simply finishes early and costs nothing, while a shard that stops at its
ceiling has two years solved, nothing pushed, and rule 32(b) forbids pushing the partial bundle. This
is the second re-budget of the lane and it is again made *before* the ceiling is approached, on
measurement rather than on a stop.

**The reporting gap is closed at the same time.** Both recreated pokes now REQUIRE the finished
passes as an explicit seconds-and-iterations table grepped from the log
(`2023 P0 1512.4s/515K, P1 5820.3s/612K; 2024 P0 in progress 12 min`) rather than prose, because a
bracket four brackets wide is not a measurement and this lane should not be re-deriving it from
timestamps. That the gap existed at all is the finding: a shard prompt that asks for per-pass numbers
"in the final report" gets prose in the interim status, and the parent's budget decisions depend on
the interim.

**Live trigger IDs, superseding BOTH earlier pairs** — these are the two the promoting check-in must
delete (rule 33), and the four earlier IDs are dead:
**`trig_01RmFVXvCgL71mHpipuv3pz1`** (minute 5) and **`trig_019jRppxsbiZdiF5o5wfsfxa`** (minute 35).
Dead: `trig_01EPuqbN1HZ4HSc7EYQ6eotf`, `trig_015e6z1RbJ75tuWqGwk9X9hA` (Addendum 2's pair),
`trig_016ykqCP9jmUezNDBJu6BCE1`, `trig_01EBYncSmmRn77caEo3W33i5`. Every delete-and-recreate is forced
by the same platform constraint Addendum 2 recorded: a routine's prompt cannot be edited from outside
the conversation it posts into. All four earlier pokes fired `SUCCEEDED` before deletion (last:
06:14:26Z and 06:35:29Z), so the wake channel has never missed.

**Unchanged:** every expected number in §A1.3, the hard-stop signature, the registration and
promotion sequence, and the rule-35 year-set enumeration. **A slower container is not a different
LP** — the 2023 P0 iteration count was 0.98× NWPP-40's, and the offer-array probe already bounded the
arm to 7 coal rows with non-coal max|Δ| exactly $0.0000000000.

---

# ADDENDUM 4 (2026-09-18) — budget 1,020 → 1,320 min; and a CORRECTION to Addendum 3's successor reading

**Recipe unchanged. Pin unchanged (`666343a2bf86f204c5ca6c672a680da32150a640`). Only the ceiling moves.**

## A4.1 The correction, stated first because a wrong number was acted on

At 08:35:54Z the shard reported `98 min P1 done; P2025 pending`. **This lane read that as "2024 P1
finished in 98 min" and concluded the run had SPED UP to 0.72× of NWPP-40, with a cumulative ratio of
1.05×.** That was wrong. The phrase meant *98 minutes **of** 2024 P1 done* — the pass was still
running. The next two reports settle it beyond doubt: `2024 P1 @129m` at 09:06:53Z and
`2024 P1 still running (189 min)` at 10:06:54Z.

**The retracted claims, named so they are not carried forward:** there was no 0.72× pass, no
cumulative 1.05×, and no "the arm makes the coal merit order less degenerate, which simplifies the
basis" story. That last one was an *explanation invented for an artefact of a misparse*, and it is
withdrawn in full. It is also exactly the kind of claim rule 1 `[R-STRUCT]` exists to refuse: solve
time is not a criterion, and a mechanism is never credited for one.

**The surviving measurement** is Addendum 3's anchor, unchanged: LP start ~04:08Z → 2024 P1 start
~06:58Z = 170 min for work NWPP-40 did in 119.1 min, i.e. **~1.43×**.

## A4.2 Why the ceiling moves again

2024 P1 passed **189 min against NWPP-40's 135.9 (1.39×) and was still running**, so it has no
measured upper bound — and 2025 P1, the single biggest pass in the span (263.9 min on NWPP-40), has
not started. Gridding the two unknowns against the 1,020 ceiling (`+20 min` for verify and push):

| 2024 P1 ends at | 2025 at 1.43× | 1.60× | 1.80× | 2.20× |
|---|---|---|---|---|
| 194 min (1.43×) | 838 | 888 | 947 | **1,065** |
| 220 min (1.62×) | 864 | 914 | 973 | **1,091** |
| 250 min (1.84×) | 894 | 944 | 1,003 | **1,121** |
| 290 min (2.13×) | 934 | 984 | **1,043** | **1,161** |

**Five of sixteen cells overrun 1,020**, and the survivors include several with under 50 min of slack.
Against that, raising the ceiling costs **nothing** — a shard that finishes early simply finishes
early — while being wrong costs the entire ~13-hour span, because rule 32(b) forbids pushing a
half-written bundle. **1,320 min** (expires ~01:35Z on the 19th) clears every cell in the grid.

**This is the third raise (600 → 780 → 1,020 → 1,320), and the honest summary is that this lane's
projections have been optimistic three times running.** The ratio estimate has moved 1.22× → 1.43× →
(a spurious 1.05×) → ≥1.39× unbounded. That pattern, not any single datapoint, is the argument for a
ceiling with real headroom rather than one fitted to the current best guess.

## A4.3 Live trigger IDs, superseding all three earlier pairs

**`trig_017Kh9n7aHcbrZWkhpZePA7y`** (minute 5) and **`trig_01Gi7KPLxx2zm66CDe6LcYA4`** (minute 35) —
these are the two the promoting check-in must delete (rule 33). Dead: `trig_01EPuqbN1HZ4HSc7EYQ6eotf`,
`trig_015e6z1RbJ75tuWqGwk9X9hA`, `trig_016ykqCP9jmUezNDBJu6BCE1`, `trig_01EBYncSmmRn77caEo3W33i5`,
`trig_01RmFVXvCgL71mHpipuv3pz1`, `trig_019jRppxsbiZdiF5o5wfsfxa`. Every one fired `SUCCEEDED` before
deletion (last: 10:06:34Z and 09:35:48Z), so the wake channel has never missed a beat across six
routines.

## A4.4 The reporting fix, sharpened

Both recreated pokes now require the per-pass table to say **FINISHED or STILL RUNNING explicitly**,
with seconds and HiGHS iterations grepped from the log. The A4.1 misread is the whole reason: a status
of the form `N min P1 done` is ambiguous between elapsed and total, and this lane resolved it the
favourable way. The next check-in is instructed that when a reading is ambiguous it must treat the
pass as still running and **say the reading is ambiguous** rather than pick the flattering branch.

**Unchanged:** every expected number in §A1.3, the hard-stop signature, the registration and promotion
sequence, and the rule-35 year-set enumeration. The FINDING will carry the ACTUAL per-pass seconds and
iteration counts from the shard's log — the interim status never supplied them — and will state the
realised span ratio rather than any of the running estimates above.
