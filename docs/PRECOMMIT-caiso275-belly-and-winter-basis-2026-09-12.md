# PRECOMMIT — caiso-275: the CAISO price level is TWO separable import-offer defects, and both are solved as parallel per-year shards

**Session caiso-275, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
**Written and pushed BEFORE any LP is spent.** Parent spends ZERO LP (rule 32 `[R-SHARD]` (a)).
Keeper / control: `2026-09-10-caiso-271-egrid-family` (`caiso271_egrid_family_span` +
`caiso271_egrid_family_2022`), `git_sha` `9ee5319bcd48a025aa3cd126283c895fcc72fa65`.

---

## §0 — The owner instruction this session serves

> *"Do a comprehensive assessment of 2022 LMP miss for CAISO, diagnose, and run an LP solve with
> shards for each years including holdouts to move all years toward calibrated. Run more than one
> solve and launch parallel shards on it if you can diagnose multiple issues with separate
> variables."*

Two arms, two separately-diagnosed objects, two independent `ScenarioConfig` variables, four years
each, eight parallel shards. **The owner directed the full span up front**, so rule 29
`[R-SCREEN]`'s screen-then-span sequencing is served in FORM (each arm names its screen year ex
ante, §5) rather than by withholding the other years. That is a spend the owner authorized, stated
plainly rather than dressed up as a screen.

## §1 — The measurement (new, and it is the whole case)

Model load-weighted price against the committed RT actual, **decomposed by net-load decile** — an
instrument no prior CAISO session ran. Model hourly from the keeper's own committed sidecars;
actual LMP from `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`; actual generation
and interchange from `data/raw/eia-930-hourly/CISO hourly.parquet`.

| 2024 decile | net load | model $ | RT $ | gap | model imports | **actual net** | model gas | **actual gas** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 0 (belly) | 1.9 GW | −3.4 | −9.6 | **+6.2** | 1,998 | **−1,037** | 1,498 | **7,235** |
| 1 | 6.8 | 25.0 | 12.4 | **+12.6** | 4,112 | 1,471 | 2,274 | 8,337 |
| 2 | 10.9 | 35.5 | 25.5 | **+10.0** | 4,645 | 2,557 | 2,990 | 9,273 |
| … | | | | | | | | |
| 9 (peak) | 28.9 | 49.1 | 55.4 | −6.4 | 4,423 | 4,835 | 13,599 | 15,449 |

The identical shape holds in 2025 (dec 0: model +$4.8, imports 1,881 vs actual **−174**, gas 1,601
vs **9,177**) and in 2022 (dec 0 +$5.0, dec 1 +$20.1). **In the belly the real CAISO is a NET
EXPORTER running 7–9 GW of its own gas, and the model is a NET IMPORTER of ~2 GW running 1.5 GW of
gas.** The gap is monotone in net load and changes sign at the peak.

Caveat carried at full magnitude (caiso-142): the model's `import` klass is GROSS while EIA
`Total interchange` is NET. That inflates the model side by the model's own small export volume
(0.58/2.21/2.31 TWh/yr) and no more — the actual side is already net, so the ~3 GW belly divergence
in **direction of flow** survives the correction.

## §2 — What sets the model's belly price, and why it cannot go where the market goes

`interchange_config.IMPORT_TRANCHES["CAISO"]` prices six import blocks at **six hand numbers —
$28 / $36 / $48 / $68 / $110 / $180 — identical in every year**; only the MW are re-derived per
year (`IMPORT_TRANCHES_BY_YEAR`). `caiso_import_hub_prices`'s own docstring calls this ladder
"re-fit in bundle mode against the model's OWN solved price". The armed `caiso_dsw_*_clean` family
changes the **capability and carbon rung** of the corridor, never the offer LEVEL, so it can push
the marginal import down to the clean rung and **no further — never below zero**.

That is the mechanism behind §1: with a flat ≥$28 floor under every import block, the model's
cheapest belly resource is an import (or the gas just above it) at ~$27–29, so it decommits its own
gas, imports, and stays balanced at a positive price. The real market keeps that gas online, goes
long, exports, and clears negative.

## §3 — ARM A — `caiso_import_solar_shape` (the belly negative tail)

Registered, default-off, CAISO-only. Collapses the two MARGINAL long-neighbour import blocks
(`DSW_solar_PV` @ $48 Palo Verde, `PNW_midC` @ $36 Mid-C) toward `−renewable_keep_running_value`
as CAISO net load enters its annual belly:
`s(t) = clip((nl_hi − nl)/(nl_hi − nl_lo), 0, 1)`, `mc = base·(1−s) + floor·s`.
The firm `PNW_hydro_base` block is deliberately NOT collapsed (must-take floor, not a glut block).

**Zero new fields, zero new fitted levels.** `caiso_solar_shape_nl_lo_pct` 10.0 /
`_nl_hi_pct` 30.0 are already in `ScenarioConfig`, derived and cited to
`scripts/data/derive_caiso_solar_shape_band.py` (deep-belly median annual net-load rank
10.0/5.6/6.0, p75 ≤ 16.6) — a net-load-distribution object, rule 23 `[R-FROZEN-DERIVE]`-clean.
Depth is the existing `renewable_keep_running_value = 20.0`.

### PHASE-0 GATE A — PASSED (zero LP)

Computed on the keeper's OWN committed net load:

| year | nl_lo | nl_hi | hours s>0 | hours s=1 | PNW_midC fired mean | DSW_solar_PV fired mean |
|---|--:|--:|--:|--:|--:|--:|
| 2022 | 8.69 GW | 16.33 GW | 2,628 (30.0 %) | 876 | $36 → **−0.22** | $48 → **+4.02** |
| 2023 | 6.69 | 14.38 | 2,628 | 876 | → **−2.26** | → **+1.54** |
| 2024 | 4.67 | 13.04 | 2,628 | 876 | → **−1.30** | → **+2.70** |
| 2025 | 1.91 | 10.45 | 2,628 | 876 | → **−2.10** | → **+1.73** |

**The decisive property: the window is defined by net load and has never seen a price, yet it lands
on the defective hours.** Fired hours are hod median 11, months Mar–Jun; the price gap inside the
window is **+15.13 / +8.89 / +9.78 / +5.97** against **+10.44 / −1.49 / −0.46 / −0.01** outside it.
The mechanism's own driver selects the hours three prior sessions found from three other directions
(caiso-266 §4, caiso-272 §3.1, caiso-273 §3).

Liveness: the injector matches through `_caiso_import_tranche_of`, which IS per-hub aware, so it
reaches `WECC_PNW_PNW_midC` and `WECC_DSW_DSW_solar_PV` under the keeper's armed
`caiso_per_hub_intertie = True`. Headroom exists — belly imports total ~1.9–2.0 GW against
`PNW_hydro_base` 1,558–1,566 MW alone, so the marginal block is ~440 MW into a 1,800 MW tranche.

## §4 — ARM B — `caiso_import_gas_coupling` (the Dec-2022 SoCal-basis blowout)

Registered, default-off, CAISO-only. Shifts the gas-set import blocks (`DSW_solar_PV`, `DSW_CCGT`,
`DSW_CT`) by the MEASURED commodity delta `(iso_hub_monthly_gas_prices − iso_monthly_gas_prices) ×
heat rate`, so desert-SW gas imports track the same spot the armed `gas_hub_basis_overlay` already
applies to in-state gas. Per-hub aware (verified). Zero new fields; the shift is ~0 at the baseline
gas level, so it is self-limiting.

The object: **December 2022 is 44.8 % of the 2022 annual price failure** (caiso-273 §2; this
session measures the monthly gap at **+63.17 $/MWh** for Dec-2022 against +2.9 to +11.9 for every
other month of that year).

### PHASE-0 GATE B — PASSED (zero LP), and it was sized from the GAS series alone

`hub_spot − F923 delivered`, $/MMBtu, and the resulting $/MWh offer shift:

| month | 2022 hub | 2022 F923 | delta | DSW_CCGT shift | DSW_CT shift |
|---|--:|--:|--:|--:|--:|
| **Dec-2022** | 11.42 | **23.10** | **−11.68** | **−81.40** | **−121.00** |
| Jan-2023 | 27.62 | 38.68 | −11.06 | −77.10 | −114.60 |
| typical 2024/25 month | — | — | −0.7 to −1.4 | −5 to −10 | −7 to −15 |

**December 2022 is the SoCal citygate blowout**: CAISO's delivered gas went to $23.10/MMBtu while
the WECC hub spot stayed at $11.42. The static ladder prices DSW_CCGT at a flat $68 and DSW_CT at a
flat $110 in every month of every year and cannot represent that event at all — so the model has no
cheap import to substitute and clears on in-state gas at the blown-out price. The real market
imported against that basis.

**The sizing, the sign and the month all come from the gas series and NEVER from the price
residual.** That the largest shift lands in the month carrying 44.8 % of the failure is a
prediction this gate makes, not a fit it performs.

## §5 — Screen years, named ex ante (rule 29 `[R-SCREEN]` (1))

Each arm's screen year is **the year its own measured footprint is largest**, from phase 0 — never
the year with the biggest residual:

* **Arm A → 2023.** Fired-hour count is percentile-fixed at 2,628 in every year, so the footprint
  discriminator is offer magnitude: `DSW_solar_PV` delta mean **−46.46** (2023) vs −45.30 (2024) /
  −46.27 (2025) / −43.98 (2022).
* **Arm B → 2022.** Unambiguous: annual mean shift −15.6 to −23.1 $/MWh vs −6.0 to −9.6 in
  2024/2025, and the Dec-2022 point value is 8–16× any other month in the file.

## §6 — G-DRIFT (rule 29 `[R-SCREEN]` (b)) — ALL HUNKS INERT, so NO CONTROL SOLVE IS SPENT

`git diff 9ee5319b origin/main -- src/market_sim scripts/run_calibration*.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference`
= 10 files, 781 insertions. Classification:

| file | classification | reason |
|---|---|---|
| `data/fleet/arrays.py` | INERT | pjm-d4-4 `unit_outage_short_windows_gas` + spp-27 `mustrun_window_commitment_grain`, both default-off and absent from the keeper recipe |
| `data/outages.py` | INERT | same pjm-d4-4 gate, behind `gas_scope` |
| `model/interchange/spec.py` | INERT | miso-252 MISO 2022 seam ladder — another ISO's branch |
| `model/lp/model.py` | INERT | miso-253 memory-lifetime fix, documented bit-identical |
| `config/scenarios.py` | INERT | see the round-trip test below |
| `scripts/replay_keeper.py` | INERT | adds `composed_from` to a dropped-keys list |
| `scripts/run_calibration*.py` | INERT | CLI surface; no keeper-reachable default moved (round-trip) |
| `scripts/lib/spp63_g5.py` | INERT | new SPP file |
| `reference/reliability_floor_coeffs_NYISO.csv` | INERT | another ISO's artifact |

**Stronger than a hunk read — the round-trip test.** Rebuilding `ScenarioConfig` at HEAD from the
keeper's 838 recorded fields: **0 fields fail to round-trip.** HEAD carries 3 new fields
(`mustrun_chp_btm_holdout`, `mustrun_window_commitment_grain`, `unit_outage_short_windows_gas`),
all `False`, all absent from the keeper recipe.

⇒ **G-CTRL form 4 is VALID. The committed keeper bundle IS the control. Zero control solves.**

## §7 — Pre-registered STRUCTURAL gates (STOP-only; they may kill an arm, never promote one)

Per arm, per year. **None is gated on the target residual** — a gate reading "did C3a improve" is
the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids.

* **G-1 LIVENESS.** The arm must move the LP. Arm A: ≥ 1,000 hours in which the CAISO
  load-weighted price differs from the control by > $0.50. Arm B: the same, concentrated in the
  months phase 0 says carry the delta. A dead arm is reported as dead and its remaining years are
  not re-read.
* **G-2 CONFINEMENT.** Arm A's price change must be confined to the `s>0` window: |mean price
  change| in `s == 0` hours < 25 % of |mean price change| in `s > 0` hours. Arm B's must be
  monotone in |delta_h|: the month-ranked correlation between |offer shift| and |price change|
  must be positive.
* **G-3 DIRECTION AND ORDER OF MAGNITUDE.** The dispatch response must have the sign and rough
  size the pre-solve delta implies. Arm A: belly imports UP and/or belly price DOWN, with the
  belly price change bounded by the offer move (no overshoot past −$20 as a load-weighted window
  mean). Arm B: Dec-2022 price DOWN, by less than the $81–121/MWh offer shift.
* **G-4 NO LOAD-BEARING COLLATERAL FLIP.** No non-target load-bearing criterion (C1/C2/C4) may go
  PASS → FAIL. C6/C8 protective must stay PASS.
* **G-5 OVERSHOOT HAZARD, stated in advance.** Arm A moves 30 % of hours by −$36 to −$46. The
  named risk is that the model's belly goes *more* negative than the market's. If C3b degrades
  while C3a improves, **that is a FAIL of the arm, not a trade to take** — a level bought by
  wrecking the shape is the thing rule 1 exists to refuse.

## §8 — Years, and why 2020/2021 are not among them

Years solved: **2022, 2023, 2024, 2025** — every year CAISO can score. 2022 is the held-out rung and
folds to the keeper under rule 30 `[R-TOUCHPOINT-FOLD]`. **2020 and 2021 are BLOCKED**, not skipped:
caiso-274 established there is no committed 2020 CAISO LMP at all and only 2021-08-12 onward for
2021, with the OASIS re-fetch boundary since moved past the missing head — and a bench part cannot
be built without a solved bundle. Neither is deliverable here.

Rule 22 `[R-C3C]` / `[R-HOLDOUT]` removal: any year may be solved with no authorization and no
marker. Rule 30(c): a held-out year never downgrades the ISO.

## §9 — Shard plan (rule 32 `[R-SHARD]`)

Eight shards, launched in parallel; the parent solves nothing.

| shard | arm | `--set` | year | out-dir | branch |
|---|---|---|---|---|---|
| A-2022 … A-2025 | A | `caiso_import_solar_shape=true` | 2022/23/24/25 | `results/calibration/caiso275_A_solarshape_<y>` | `claude/caiso275-a-<y>` |
| B-2022 … B-2025 | B | `caiso_import_gas_coupling=true` | 2022/23/24/25 | `results/calibration/caiso275_B_gascoupling_<y>` | `claude/caiso275-b-<y>` |

Base bundle: `caiso271_egrid_family_2022` for the 2022 shards, `caiso271_egrid_family_span` for
2023–2025. Driver: `scripts/replay_keeper.py <bundle> --set <flag>=true --years <y> --out-dir <dir>`
— the caiso-271 single-delta A/B pattern, one flag on the committed keeper recipe.

Each shard: pins this doc's SHA and stops if `git rev-parse HEAD` differs; never rebases, pulls or
syncs; commits ONLY its own bundle's slim file set; never touches `src/`, `scripts/`,
`frontend/data/backcast/**`, `dashboard_add_run.py`, `build_manifest.py`, `build_status.py` or
`prune_iso_runs.py`; opens no PR; deletes no result (rule 31 `[R-RETAIN]`); and stops with a numeric
report rather than running past 20 minutes.

## §10 — Disclosures against interest

1. **Arm A is a large intervention.** 30 % of hours, −$36 to −$46 on two blocks. G-5 exists because
   overshoot is the likely failure mode and it must not be traded against a better C3a.
2. **Arm B's 2025 coverage is partial.** The hub gas series is NaN in Sep/Oct/Nov 2025 and the code
   zeroes the delta there, so 2025 is a partial test of B. Stated, not hidden.
3. **The measured intertie LMP is only 76.7 % complete in 2023** (MALIN and PALOVRDE both;
   2022/2024/2025 are 100 %). That degrades the armed `caiso_dsw_*_clean` family in 2023 and is a
   data-intake defect neither arm repairs.
4. **`caiso_import_hub_prices` is PROVABLY INERT on this keeper and must not be armed as a bare
   flag.** `inject_caiso_import_hub_prices` matches import rows with a raw
   `uid.startswith(f"{IMPORT_ZONE[iso]}_")` — i.e. `WECC_import_` only — while its two siblings
   (`inject_caiso_import_gas_coupling`, `inject_caiso_import_solar_shape`) were repaired to go
   through the per-hub-aware `_caiso_import_tranche_of`. Under the keeper's armed
   `caiso_per_hub_intertie = True` the rows live in `WECC_PNW` / `WECC_DSW`, so the injector
   matches zero rows and returns `False`. This is a real code defect, it is recorded here, and
   **repairing it is NOT in this session's scope** — it would be a solve-path code change, which
   rule 32(c)6 keeps out of shards and which deserves its own charter.
5. **No arm addresses the peak-decile UNDER-price** (2024 dec 9: model $49.1 vs RT $55.4). That is
   the standing C3c tail object and stays open.
6. **Neither arm is the commitment object.** §1 shows a 5.7–7.6 GW belly gas deficit. Both arms work
   on the import offer, i.e. on what the model substitutes INSTEAD of its own gas. If the price
   closes while the gas deficit does not, that is a partial repair and must be reported as one.
