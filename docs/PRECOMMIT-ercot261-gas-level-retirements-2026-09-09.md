# PRECOMMIT — ercot-261: the delivered-gas LEVEL becomes a corroborated monthly series, and the 2021–2022 EIA-860 retirements are backfilled

> Rule 29 `[R-SCREEN]` PRECOMMIT. Written and committed **before any LP is spent**.
> Scope: **ERCOT only** (owner instruction, 2026-09-09 — the other ISOs' retiree
> window is owned by a separate session). One bundle, both cards armed together
> (owner instruction: *"fix BOTH in ONE solve … No A/B, no attribution ablation"*).

## 0. What changed between the handoff and this document

The handoff specified Card A as "replace the annual gas LEVEL with the measured
monthly series … keep the daily/within-month shape if it is already armed."
**Phase 0 (§1) shows that construction fails the handoff's own pre-registered
February gate**, at zero LP. The owner was shown the measurement and ruled
(2026-09-09): *monthly level, with February 2021 held out by a rule declared
before the solve.* §2 is that rule. §1 is the evidence that forced it.

**One correction to the record.** The option text put to the owner said the
maximum two-series disagreement outside 2021-02 was $0.85/MMBtu. That is wrong:
**2021-12 disagrees by $3.47** (§1c). The corroborating mass is **82** of 84
months, not 83, and the declared rule therefore holds out **two** months, not
one. The December hold-out is immaterial in magnitude and is reported in §2c.

---

## 1. PHASE 0 — zero LP, and it is a STOP gate on the mechanism as specified

### 1a. The composition the keeper actually solves

`delivered[h] = (HH_annual + scalar) × HH_monthly_shape[m] × HH_daily_shape[d]
              + zone_spread[z] + level_corr`

`level_corr` is the measured TX electric-power gas basis, and it is **annual**:
`+5.278 $/MMBtu` in 2021 against `+0.004 / −0.086 / −0.463` in 2023/2024/2025.
`gas_daily_shape` is **already armed** in the keeper's 2021–2022 recipe, so the
"keep the daily shape" half of the handoff is already true today.

### 1b. Every monthly-resolution construction breaks February 2021

Measured on the committed series (`henry_hub_daily.csv`, `henry_hub_monthly.csv`,
`eia_delivered_gas_TX_monthly_*.csv`), 2021, ERCOT hub level, no fleet:

| construction | Feb 2021 $/MMBtu (mean, range) | Feb h with fuel > $200/MWh-equiv |
|---|---|---|
| **A — keeper today (annual basis)** | 10.202  (8.09 … 26.55) | **0** |
| **B — ercot-254 (monthly, additive)** | 59.300  (57.19 … 75.65) | **672 / 672** |
| **C — the handoff's spec (monthly LEVEL × the armed daily shape)** | 59.730  (**31.26** … 280.42) | **672 / 672** |

Construction **C is exactly what the handoff asked for**, and its *cheapest*
February day still prices gas at **$31.26/MMBtu ≈ $234/MWh** at a CC heat rate.
The Henry Hub daily shape's within-February dynamic range (≈9:1) cannot rescue a
$59.73 monthly mean. The handoff's gate — *"Feb 2021 must STAY right (−3.3 %
today). If the monthly level breaks Uri, the fix is wrong"* — **fails before the
solve, for both B and C.**

**Why, physically.** EIA's monthly print is a **cost ÷ volume ratio**, not a
price. Texas gas traded ≈$3/MMBtu for ~24 days of February 2021 and $100–1,200
for ~4 (EIA's own NG Weekly Update, 2021-02-18: Waha $4.54 on Feb 10 → $64.22 on
Feb 17, peak >$206/MMBtu on Feb 16). No monthly statistic represents that
distribution, and **no free daily Texas index exists** to replace it: the EIA
weekly archive carries Waha in narrative prose only (verified by fetch, this
session — the structured daily table is Henry Hub / New York / Chicago / Cal.
comp. avg. only), and `docs/calibration-log/ercot.md:4853` already records that
ERCOT's settlement Fuel Index Price "is not a data product". A daily
delivered-gas series remains ercot-254 §6's successor and a **procurement
decision**, not a session task.

### 1c. The corroboration measurement (new; this is what makes §2 possible)

Two **independent** measured series for the same quantity — EIA N3045TX3 (state
survey, $/Mcf ÷ 1.036) and EIA-923 Schedule-5 TX plant receipts, quantity-
weighted — compared for all 84 months 2019-01 … 2025-12:

| | months | max \|disagreement\| |
|---|---|---|
| corroborating mass | **82** | **$0.85/MMBtu** |
| outliers | **2** | 2021-02 **$13.77**, 2021-12 **$3.47** |

The gap between the corroborating mass ($0.85) and the nearest outlier ($3.47)
is a factor of **4.1**, with no month in between. The two series agree in every
month of 2019, 2020, 2022, 2023, 2024 and 2025 — the disagreement is confined
entirely to Uri and its December cost-recovery tail.

**Corollary already banked:** N3045TX3's December 2021 print (basis **+5.055**)
is contradicted by plant receipts (**+1.589**). That is why ercot-254's December
barely improved (+138.8 % → +134.5 %) — it applied a basis its own corroborator
rejects.

---

## 2. THE MECHANISM — `ercot_ep_gas_basis_corroborated`

A **sub-gate inside the existing `ercot_ep_gas_basis_monthly` mechanism**, not a
mechanism beside it (rule 19 `[R-ONE-MECH]`): the predicate requires
`ercot_ep_gas_basis_monthly`, which requires `ercot_zonal_gas_basis`, so the
monthly level is never applied un-corroborated and the two never stack.

### 2a. The declared rule (pre-registered; never swept)

```
level_monthly[m] = EP[m]/1.036 − HH[m]                          # ercot-254, unchanged
admissible[m]    = |EP[m]/1.036 − F923_TX_qtywtd[m]| ≤ TOL
level_used[m]    = level_monthly[m]                    if admissible[m]
                 = mean(level_monthly[admissible])     otherwise
```

applied exactly as ercot-254 applies it — additively, per hour by calendar month,
through the same `_expand_monthly_to_hourly` seam, on top of the daily-shaped
commodity. **No change to the commodity path, the daily shape, the zonal spread,
or the applier's ordering.**

**`TOL = 1.00 $/MMBtu`.** Identification source: the observed disagreement
distribution of two independent measured series over 84 months — above the
corroborating mass's maximum ($0.85) and 3.5× below the nearest outlier ($3.47).
It is **set from the data's own gap structure, ex ante, and is never swept
against a gate**. It is a **ledgered free parameter** under rule 21 `[R-DOF]`
(§6) and it is the *only* one this card adds.

The test reads **fuel series only**. It never touches a price, a load, a
dispatch or any model output — so it is not an input rescaled to a residual
(rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`).

### 2b. Fallback choice, stated and defended

An inadmissible month falls back to the **mean over that year's admissible
months**, *not* to the annual form. The annual form is contaminated by the very
month being replaced (2021's +5.278 **is** February), so using it would be
circular and would re-break Uri. The corroborated-months mean is the year's own
uncontaminated central value.

### 2c. Measured effect of the rule, per year (zero LP)

| year | inadmissible months | annual basis (today) | corroborated mean (the fallback) |
|---|---|---|---|
| 2019 | none | −0.218 | −0.218 |
| 2020 | none | +0.044 | +0.044 |
| **2021** | **2 (13.77), 12 (3.47)** | **+5.278** | **+0.390** |
| 2022 | none | −0.301 | −0.301 |
| 2023 | none | +0.004 | +0.004 |
| 2024 | none | −0.086 | −0.086 |
| 2025 | none | −0.463 | −0.463 |

**In six of seven years the rule holds out nothing** and the mechanism reduces
exactly to ercot-254's monthly form, whose 2023/2024/2025 footprint was measured
there as near-inert. **2021 is the only year the corroboration filter fires.**

December's hold-out is immaterial: it moves that month's basis +5.055 → +0.390,
where its own corroborator (F923) says +1.589 — i.e. the fallback **undercharges
December by ≈$1.2/MMBtu**. Reported at the gate as a known residual, not absorbed.

### 2d. The resulting 2021 hub gas series

| construction | annual | Feb mean | Feb range | ex-Feb mean | h > $200/MWh-equiv |
|---|---|---|---|---|---|
| A — keeper today | 8.998 | 10.202 | 8.09 … 26.55 | 8.898 | 0 |
| B — ercot-254 | 8.648 | 59.300 | 57.19 … 75.65 | 4.439 | 672 |
| **D — this card** | **4.110** | **5.315** | **3.21 … 21.66** | **4.010** | **0** |

The eleven-month repair is delivered in full (ex-Feb **−$4.89/MMBtu**, ≈ **−$37/MWh**
at a CC heat rate — the FINDING's measured +$33…+97 non-Uri miss) **and Uri is not
broken by fuel cost** (zero February hours above the C3c threshold on fuel alone).

---

## 3. CARD B — the 2021–2022 retiree backfill, ERCOT-scoped

`eia860_generator_retired_within_window.parquet` carries **zero rows before 2023**
(`RETIREMENT_WINDOW_START = 2023`), so a unit that ran in 2021 and retired in
2021–2022 is absent from the 2025 operable snapshot **and** from the injection —
missing from the fleet entirely, biasing capacity short and price high.

**The blast radius is larger than the handoff assumed and is contained by design.**
`load_retired_within_window` applies **no solve-year filter**: every row in the
parquet is injected into every backcast year of every ISO. Simply lowering the
constant would therefore add zero-availability rows to *all six* other ISOs'
2023–2025 fleets and move their LP dimensionality. Per the owner's ERCOT-only
instruction, the widening is delivered **config-gated**:

* the parquet is rebuilt with the window opened to 2021 (it now carries 2021–2024);
* `load_retired_within_window` filters on a window-start read from the config,
  **defaulting to `RETIREMENT_WINDOW_START` (2023)** — so every other ISO and every
  un-armed run is **byte-identical**;
* ERCOT's recipe alone opens it to 2021.

Included because it is **correct** (rule 14 `[R-ACCURATE]`), not because it moves a
residual: ERCOT's share is small and the handoff says so.

**Regression test (the one real risk):** a unit present in BOTH the operable
snapshot and the injection must not be double-counted. The builder's existing
whole-plant filter (`~plant_id.isin(operable_plant_ids)`) is the guard; the test
pins it at the widened window.

---

## 4. G-DRIFT — the audit, and why it earns a CONTROL SOLVE

Rule 29(b) default is form 4 (the keeper's committed bundle is the control).
**Form 4 is VOID here, and the audit says which line does it.**

Base: `ffc25ece` (the merge that landed the keeper; the bundle's own `git_sha`
`92dee13c` is a pre-squash branch commit and is not reachable in this clone —
recorded here rather than silently substituted). Diff over `src/market_sim`,
`scripts/run_calibration*.py`, `scripts/lib`: **30 files, 2,788 insertions.**

| commit(s) | classification |
|---|---|
| `ee2275d2`, `0fb40252`, `f2a834de` PJM seam ladder | **INERT** — PJM-only, default-off |
| `cd9d69e1` ruff format (AST-verified identical) | **INERT** |
| `0d4b434b` pjm-177 ST_GAS drag min-run sub-gate | **INERT** — default-off, absent from the ERCOT recipe |
| `18f52fbb` ercot-260 two-config replay | **INERT for a fresh solve** — replay-path only (and it is this session's prereq) |
| `78edeeb7` SPP LMP sidecar UTC | **INERT** — SPP scoring data |
| `01c3baeb` capx D88 unit_id uniqueness | to verify at implementation; treated LIVE until shown otherwise |
| `c0efa7ad`, `5df6192f` hydro budget period | to verify; ERCOT hydro is trivial |
| `d6cbc03a` netload_drag_merit_allocation | **INERT** — default-off, ercot-259 refused it, absent from the recipe |
| `e1c7bc08`, `32f0110a`, `f0d6ba2d`, `815a0066` capx D83/D87 CCS + ledger | **INERT** — forecast-only capacity evolution; a `mode="backcast"` run never enters it |
| `663f5967` miso-245 seam ladder | **INERT** — MISO |
| `203c031e` spp-49 **seam 1** (F923 gas plausibility screen, default ON) | **INERT for this keeper** — the spp-49 lane's own census marks `ercot256_five_year_keeper` `"reachable": false` (`docs/handoffs/spp49/key_census_post.json`); ERCOT does not arm `gas_plant_monthly_fuel_pricing` |
| `203c031e` spp-49 **seam 2** (simple-cycle eGRID HR floor) | **LIVE** |

**The LIVE hunk, measured.** Seam 2 is **ungated and unconditional** ("same seam,
unconditional, so every read path…"). Loading the ERCOT fleet at HEAD clamps
**5 plants — 3612, 52176, 55052, 59391, 61643 — 34 operating rows in total**,
from 7.624–8.721 up to the 9.000 MMBtu/MWh floor. That is a real change to
ERCOT's CT merit order in **every** year, present in HEAD and absent from the
keeper's committed legs.

**Therefore: a same-HEAD control is solved for every year, one flag apart from the
arm.** This is the rule's own LIVE-hunk provision, not a discretionary extra, and
it is the same call ercot-254 made and recorded as having earned its cost.

---

## 5. PRE-REGISTERED PREDICTIONS AND GATES

Registered **before** the solve. Reported at full magnitude, hits and misses alike.

### 5a. STOP gates (may kill the arm; may never promote it)

| id | gate | STOP bar |
|---|---|---|
| **G-1** | 2023/2024/2025 hub gas: arm − control, annual mean | > $0.40/MMBtu |
| **G-2** | corroboration filter fires in any year other than 2021 | any |
| **G-3** | Feb 2021 model LW LMP error | outside −15 % … +5 % |
| **G-4** | any non-target load-bearing criterion (C1/C2/C3b) PASS → FAIL in **2023/2024/2025** | any |
| **G-5** | shed: slack or dump MWh in any year | > 1.0 MWh |
| **G-6** | Card B double-count: any unit in both the operable snapshot and the injection | any |

### 5b. Directional predictions (scored, not gates)

| # | prediction |
|---|---|
| **P1** | 2021 C3a falls **a lot** — ex-Feb hub gas −$4.89/MMBtu ≈ −$37/MWh; annual model LMP 187.29 → **$120–150** vs actual 148.19 |
| **P2** | 2021 ex-Feb monthly bias falls from +160.8 % to **under +40 %** (ercot-254's monthly form reached +79.1 % while still carrying the contaminated December and a broken February) |
| **P3** | **Feb 2021 stays right and moves slightly MORE negative** — gas $10.20 → $5.32 mean removes ≈$37/MWh from ~600 non-scarcity hours, so −3.3 % → **−4 % … −8 %**. Uri is scarcity-priced, so the move is small |
| **P4** | **C3c 2021 does NOT regress** — this is the criterion ercot-254 broke (234 → 688 h vs 258 actual). Zero February hours are pushed over $200 by fuel here, so I predict **150–300 h**, i.e. still PASS-or-caveat, and I predict the direction is **down**, not up, because eleven months of gas get cheaper |
| **P5** | **C3b 2021 improves** — ercot-254 took it 0.361 → 0.501 *because* February broke; with February intact I predict **0.28–0.38**. This is the criterion that killed ercot-254 and it is the honest risk: if C3b degrades anyway, the level is not the whole story |
| **P6** | 2023/2024/2025 move **near-zero** — the corroboration filter fires in none of them and their monthly-vs-annual basis spread is ≤ $0.35/MMBtu. I predict every criterion holds its status and \|Δ LW LMP\| < $0.50/MWh |
| **P7** | 2022 moves **modestly** (monthly basis spans −0.847 … +0.675 against an annual −0.301) — C3a improves slightly; Card B's 510 MW lands here, its largest year |
| **P8** | Card B alone is **immaterial to 2021** (35.8 MW ≈ 0.05 % of peak) and is included for correctness, not effect |

### 5c. Reported, never gated

C8 forced-share and every C1 class bar at full magnitude; the December
undercharge of §2c; and the 2021 zonal-spread and West `neg_day_freq` defects
ercot-254 §6 named, which this card does **not** touch.

---

## 6. DOF LEDGER (rule 21 `[R-DOF]`)

| parameter | value | identification source |
|---|---|---|
| `F923_CORROBORATION_TOL` | **1.00 $/MMBtu** | the observed disagreement distribution of two independent measured fuel series over 84 months (corroborating max $0.85; nearest outlier $3.47). Set ex ante from the data's gap structure; never swept against a gate. |
| retiree window start (ERCOT) | **2021** | the EIA-860 "Retired and Canceled" schedule's own coverage; a data-window selector, not a fitted value |

No other free parameter is added. `TOL` closes no residual by itself — it selects
which **measured** month is admissible, and the measurement it admits carries zero
DOF.

## 7. Governance

Rule 31 `[R-RETAIN]`: **no solved bundle is deleted until the owner rules on
promotion.** Bundles are written outside `results/calibration/` and gitignored, so
rule 29(c) and the parity sweep are satisfied without `rm`. This container is
ephemeral and the bundles will **not** survive it — the promotion question is put
explicitly in the session's final report.

Rule 22: 2021 and 2022 are validation-tier spends under ERCOT's `complete` marker
(declared 2026-08-31; the holdout freeze is locked-test-scoped only). Nothing is
identified on, fitted to, or selected against 2021 — `TOL` is identified on the
fuel series alone, across all seven years, and is registered above the solve.

Rule 15 / 28 / 30: the run registers on the dashboard in this session; a
touchpoint year is stamped to the keeper rather than carded separately.

---

# ADDENDUM 2 (2026-09-09, after the rebase onto `main`) — **CARD B AS WRITTEN ABOVE IS WITHDRAWN. It was superseded mid-session by better work, and the ten in-flight solves were invalidated and stopped.**

Written the moment the collision was found, **before any re-launch**, so the
record shows what was abandoned and why rather than quietly re-scoping.

## 1. What landed on `main` while this session was solving

Two commits from the cross-ISO fleet/fuel lane, both authored ~03:33 on
2026-09-09, i.e. **after** this session's PRECOMMIT and **during** its solves:

| commit | what it does |
|---|---|
| `7934e92c` | **Widens the within-window retiree snapshot to 2019**, globally and additively (`RETIREMENT_WINDOW_START` 2023 → 2019) |
| `7648daa0` | Builds `gas_electric_power_monthly_level`, an **ISO-agnostic measured monthly delivered-gas LEVEL** seam |

## 2. Card B is superseded, and its replacement is better on every axis

`7934e92c` does what §3 above set out to do, and does it better:

| | §3 (this session) | `7934e92c` (main) |
|---|---|---|
| window | 2021 | **2019** |
| source | the current vintage's retired sheet only | **multi-vintage, source-agnostic reader** |
| scope | ERCOT, config-gated | global, ungated |
| ERCOT 2021 recovered | 7 units / **9.8 MW** | 9 units / **222.8 MW** |
| additivity | append-only, verified | append-only, verified, **plus** a shipped-hash STOP test |

It also found something §3 did not: EIA **prunes older retirements from each
release**, so a bare rebuild loses 161 real units (Indian Point 2+3, Pilgrim,
Palisades). §3's append-only construction avoided that trap by accident;
`7934e92c` diagnosed it and pinned it with a test.

**Withdrawn accordingly**: `ScenarioConfig.retiree_window_start_year` and its four
cache-key registrations, `paths.set_retiree_window_start` /
`active_retiree_window_start`, the `runner` call site, the
`--retiree-window-start-year` CLI flag, `process_eia860.append_retired_window_from_parquets`
and its CLI, the `load_retired_within_window` window filter,
`tests/unit/data/test_retiree_window_append.py`, the parquet append, and the
matrix row + seven cells. Main's versions are taken wholesale.

## 3. What SURVIVES from Card B, because main left it open

`7934e92c` widened the **whole-plant** half only.
`data/fleet/eia860.py::_PARTIAL_EXIT_WINDOW_START` stayed at **2023** even though
its own comment says it mirrors `RETIREMENT_WINDOW_START` — so after that commit a
plant's whole-plant exits reach back to 2019 while its **unit-grain** exits are
stranded at 2023. This session moves it to 2019 and restores the mirror.

That is not a cosmetic tidy: it is exactly what hides **Decker Creek** (plant
3548, 405 MW gas ST, retired 2022) — **98 % of ERCOT's 2021–2022 affected
capacity**, invisible to both halves, and still absent from main's widened
parquet (ERCOT 2022 = 0 rows there). The finding and its declared footprint in
`docs/ADDENDUM-ercot261-partial-plant-scope-2026-09-09.md` stand unamended; only
the *delivery mechanism* changed, from a new gated field to a one-line mirror
repair.

## 4. The ten in-flight solves were STOPPED, not harvested

Main's widening is **ungated**, so it changes the ERCOT fleet for every backcast
year: 2021 goes from this branch's 9.8 MW of retirees to **222.8 MW**, plus
2019/2020 units the COD ramp masks. Both the arm and the control were therefore
solving a fleet that does not exist post-rebase, and **neither leg would have
been valid evidence for a merge-ready branch**.

All ten shard sessions were archived mid-solve (~5 minutes in). No result was
harvested, none is quoted anywhere, and no bundle survives. One shard did report
`partial-plant exit fired` before it was stopped, which is consistent with §3 but
is **not** evidence and is not relied on.

**Nothing was lost that rule 31 `[R-RETAIN]` protects**: no solve completed, so
there was no result to retain. The rule's cost clause is honoured instead — the
re-solve cost is stated up front in §5 rather than silently incurred.

## 5. What the re-launch costs, stated before it is spent

Ten shards × ~30–40 min of LP, run in parallel containers ≈ **35–45 min wall
clock**. The control legs are still earned: the SPP-49 simple-cycle heat-rate
floor (§4 of the PRECOMMIT) is unchanged on main and still ungated and LIVE for
ERCOT, so G-CTRL form 4 remains void.

## 6. Card A is UNCHANGED — and a rule-19 relationship is now on the record

`ercot_ep_gas_basis_corroborated` survives the rebase untouched: different seam
(`data/fuel/basis/ercot.py`, the ERCOT zonal-basis `level_corr`), different
object (a per-month admissibility test on a measured basis), ERCOT-gated.

**Rule 19 `[R-ONE-MECH]`, declared now rather than discovered later.** Main's
`gas_electric_power_monthly_level` sets the delivered-gas LEVEL in
`data/fuel/resolve.py`; ERCOT's `ercot_zonal_gas_basis` adds its own measured
statewide `level_corr` in `data/fuel/basis/ercot.py`. **Arming BOTH on one ERCOT
run would carry the statewide level twice** — the identical double-carry defect
ercot-255 fixed for the zonal SPREAD. They are not stacked in this arm (main's
flag is brand-new and default-off, and no ERCOT recipe arms it), so nothing is
wrong today; but the two are alternatives, not complements, and whichever ERCOT
ends up on, the other must be off. Flagged to the fleet/fuel lane rather than
resolved unilaterally here, since `gas_electric_power_monthly_level` is theirs.
