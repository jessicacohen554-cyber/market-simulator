# PRECOMMIT miso-230 — MISO's OWN CT_PEAKER net-load drag: derived window **[10, 21)**, derived curve, screened on 2023

**Pushed BEFORE the screen solve.** Everything a gate reads — the window, the three
coefficients, their derivation, the G-DRIFT audit, the pre-solve arithmetic and the five gates
with their numeric bars — is fixed in this document and in the committed artifacts it cites, so
no number here can have been written to fit a result.

**KEEPER (the control, rule 29(b) form 4): `2026-09-05-miso-220-nonsteam-lift`**
(`miso220_nonsteamlift_B`, git sha `4545300d`), CALIBRATED, C3c the single ledgered caveat.
Rule 22: **2023–2025 only**. DOF ledger unchanged at 41/2 — this mechanism adds **no free
parameter** (§2).

Continues miso-229 under the owner's standing decision of 2026-09-06: **fix CT_PEAKER, then
promote the seam pair.**

---

## 0. What this session is, and the one thing it is not

miso-227 solved the seam arm full-span and registered it as `miso227_seamneighbour_K`. It scores
**NOT-YET on one cell** — CT_PEAKER-2023 at −8.29 TWh against the ±8.00 C1 band. The arm did not
create that cell: the keeper misses CT_PEAKER by **5.4–8.0 TWh in every year** and sat 0.015 TWh
inside the band, so MISO's CALIBRATED status hinged on 0.19 % of a band on a cell wrong by eight.
The seam cannot promote alone, and all six ISO keepers currently read CALIBRATED.

This session attacks the **root cause** (rule 1 `[R-STRUCT]`'s own prescription), not the band.

**It is NOT `ct_mustrun_per_plant`.** That lever floors each plant at its **observed EIA-923 net
generation** — rule 13 `[R-MEASURED]`'s *named* forbidden case — and is formally **D-9
QUARANTINED** in `scripts/legitimacy_diagnostics.py`, machine-asserted `False`. It would close C1
by forcing the observed energy, i.e. for the worst possible reason. It is not re-opened here.

## 1. A correction to this session's own charter, reported rather than quietly worked around

The charter's task (2) instructed: *"rule 28(c): `ct_netload_drag` has NO base row in ANY ISO
shard. Mint the base row … plus a cell line in all six shards, same PR."*

**That premise is false, and minting the row would have been the wrong action.**
`ct_netload_drag` **is** registered in `docs/codebase-site/data/mechanism-matrix.js`, in the
`netload_drag_floors` row, which names it and all five of its coefficients literally
(`ct_netload_drag :10381`, `ct_drag_slope_per_gw :10382`, `ct_drag_intercept :10383`,
`ct_drag_cap :10384`, plus the ramp window) — that literal registration was done deliberately by
the xiso-3 census under rule 28(c). The miso-229 finding this session was told to read cites the
MISO cell by that very row id (`netload_drag_floors: { cell: "U" }`). `scripts/check_mechanism_matrix.py`
passes at HEAD with no `ct_netload_drag` finding.

The charter appears to have carried across the miso-228 finding's statement about a **different**
field — `ct_mustrun_per_plant`, which genuinely has no row in any shard, and which this session
refuses on rule-13 grounds anyway.

**Duty (c) therefore does not fire: this session adds no new `ScenarioConfig` field.** Duty (b)
does, and is discharged — the existing `netload_drag_floors` cell in
`docs/codebase-site/data/mechanism-matrix/MISO.js` is updated with this session's verdict and
citation, in this session. Minting a duplicate `ct_netload_drag` row beside `netload_drag_floors`
would have split one mechanism across two rows, which is the condition rule 19 `[R-ONE-MECH]`
exists to prevent in the ledger as well as in the model.

## 2. The derive — `scripts/data/derive_miso_ct_netload_drag.py` (rule 23 `[R-FROZEN-DERIVE]`)

Modelled on `derive_pjm_ct_netload_drag.py` (the PJM cell is `K`; PJM is the closest analogue),
changing the ISO and its **clock — CST = UTC − 6**, not PJM's EST. Frozen artifact:
`data/raw/reference/miso_ct_netload_drag.json`, ISO-stamped per rule 25.

**Rule 25 `[R-ISO-SCOPE]` is honoured on both axes.** What is carried from PJM is the
**estimator** — pure-play plant selection (≥ 90 % of plant model capacity is CT_PEAKER), the
CAMPD-gross→net factor, the CF denominator being the same nameplate the floor multiplies back
onto, the median-per-2-GW-bin binning, and the exact-grid-search hinge fit (no `scipy.optimize`,
which is FORBIDDEN). What is **not** carried is every number PJM and ERCOT fitted — **and their
window**.

### 2a. The window is DERIVED, with zero free parameters

miso-229 established that ERCOT's/CAISO's `[15, 22)` is justified by *solar collapse* producing a
sharp evening ramp, and that **MISO's midday block is as strongly driven as its evening**. So the
window is derived by a rule that has nothing in it to choose:

> the maximal **contiguous** run of local-standard hours whose pooled mean CF is **at or above the
> fleet's OWN 24-hour mean CF** — the data's own daily average, not a level anyone picked — and
> whose Spearman ρ(CF, net load) is positive.

Measured, pooled 2023–2025 over 127 pure-play plants / 19.54 GW (88 % of class nameplate):

| | h00 | h05 | h09 | **h10** | h13 | h17 | **h20** | h21 | h23 |
|---|---|---|---|---|---|---|---|---|---|
| mean CF | 0.0284 | 0.0453 | 0.0802 | **0.0926** | 0.1253 | **0.1567** | **0.1082** | 0.0740 | 0.0340 |
| ρ(CF, net load) | +0.443 | +0.441 | +0.666 | **+0.695** | +0.754 | +0.723 | **+0.686** | +0.636 | +0.485 |

Threshold = 0.0850. **DERIVED WINDOW = `[10, 21)` CST** (end exclusive, the `ScenarioConfig`
convention). ρ is positive in **every** hour of the day and ≥ 0.686 across the whole window.

**Year-stability check, by the identical rule applied per year: `[9, 21)` / `[10, 21)` /
`[11, 22)`** — stable to ±1 h. Reported, not smoothed.

The window is itself forward-native: it regenerates from a forward CT diurnal profile and moves
with changed conditions (more solar shifts the profile and the window with it).

### 2b. The curve

Hinge fit of the **applied** functional form `clip(slope·netGW + intercept, 0, cap)` on the window
sample; cap = 95th percentile of window CF. SSE **0.08416** against the unclipped ERCOT-recipe
line's 0.13738 (printed for the record, not applied).

```
ct_drag_slope_per_gw  0.01303      ct_drag_ramp_start  10
ct_drag_intercept    -0.8108       ct_drag_ramp_end    21   (EXCLUSIVE)
ct_drag_cap           0.4394
```

Zero-crossing 62.2 GW. **DOF: zero.** Every value is a statistic of measured CAMPD + EIA-930
data under a pre-specified estimator; none is identified against a price or volume residual, and
rule 23 freezes the script against residuals — it re-derives only when its source data updates.

### 2c. Energy cross-check — the floor is a MINIMUM, not a pin

| year | floor energy | measured (pure-play) | floor ÷ measured |
|---|---:|---:|---:|
| 2023 | 8.406 TWh | 15.037 TWh | 0.56 |
| 2024 | 7.311 | 13.791 | 0.53 |
| 2025 | 7.469 | 14.804 | 0.50 |

The floor sits at about **half** the measured energy, which is what distinguishes it from an
actuals pin. **Reported against the mechanism:** the *floored total* (`max(floor, measured)`)
exceeds measured by 1.81 / 1.45 / 0.92 TWh, i.e. the floor is above measured output in some hours
— unavoidable for a curve fit through the median, but it is a real overshoot channel and it is
named here rather than discovered at the gate.

## 3. Rule 19 `[R-ONE-MECH]` — REPLACE, and it is machine-enforced. **MEASURED, zero LP.**

The named risk was stacking. MISO's `reliability_floor` **already** carries net-load-driven
CT_PEAKER limbs in all six zones (`reliability_floor_coeffs_MISO.csv`, `enabled=True`, driver
"MISO system p70 daily-peak net-load", window h15-21), and the keeper's own D-2 attributes
**100 %** of CT_PEAKER's forced energy to that one mechanism.

`iso_configs.drop_drag_owned_reliability_specs` drops exactly those limbs when the drag is armed.
This session **measured** it rather than asserting it, by rebuilding the keeper's own fleet both
ways through `run_year(fleet_only=True)` — `scripts/probes/_miso230_ct_drag_phase0.py` →
`_miso230_ct_drag_phase0.json`, **zero LP**:

```
MISO 2023: reliability floor — dropped 18 drag-owned limb(s) (rule 19)

  keeper  reliability_floor × CT_PEAKER : 2.6231 TWh floor, 770 h
  ARM     reliability_floor × CT_PEAKER : 0.0000 TWh          <- replaced, not stacked
  ARM     ct_netload_drag               : 8.8578 TWh floor, 2203 h
  total CT_PEAKER min_gen  keeper 2.6231 -> arm 8.8578 TWh   (delta +6.2347)
```

Mean floor MW by hour-of-day, arm — **zero outside `[10, 21)` by construction**:

```
h00-h09: 0     h10:1744 h11:1971 h12:2158 h13:2278 h14:2359
h15:2448 h16:2540 h17:2599 h18:2462 h19:2108 h20:1602     h21-h23: 0
```

## 4. The D-4 window declaration — changed EX ANTE, and why that is not scoring to fit

`D4_WINDOWS` declared `(MECH_CT_NETLOAD_DRAG, None): (15, 22)` **globally**. Scoring MISO's
derived `[10, 21)` against ERCOT's declaration would count h10–h14 — carrying 1,744–2,359 MW, the
largest part of the footprint — as **off-window binding**, i.e. would fail the drag for binding in
exactly the hours MISO's own driver evidence says it should. That is a defect in the declaration,
not in the mechanism.

This session adds `D4_WINDOWS_BY_ISO` + `resolve_d4_windows(iso)` and declares **MISO `[10, 21)`**
with the §2a evidence cited in place. Guards on the change:

- **It is a no-op for every other ISO and every registered run.** `resolve_d4_windows` returns
  `D4_WINDOWS` itself when an ISO has no override (verified: `is D4_WINDOWS` → `True`); ERCOT
  still reads `(15, 22)`; the MISO keeper arms no drag, so the row it touches carries zero floored
  energy and is skipped. **No committed bundle's score moves.**
- **It is a declaration, not an escalation path** — like every other windowed row in that
  registry. The drag is zero outside its configured window *by construction*
  (`apply_netload_reliability_floor`'s `ramp_window` gate), so an off-window bind is structurally
  impossible. What the row buys is that rule 18's conditional-pass leg (a) scores the mechanism
  against **MISO's** driver evidence instead of another market's.
- **It is pushed before the solve**, in this commit, with the window fixed by §2a's zero-DOF rule.
  It cannot be re-chosen after seeing a gate.

## 5. G-DRIFT (rule 29(b)) — **ALL HUNKS INERT. Form 4 valid. NO control solve.**

`git diff 4545300d HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` = **87 files, +11,083 / −1,072**. Every
hunk on the MISO backcast path classified, with its reason:

| changed area | class | reason |
|---|---|---|
| `scripts/lib/load_forecast/*`, `config/capacity_market.py`, `capacity_evolution/{retirements,ccs,new_entry,adequacy,evolve}.py`, `policy/{cap_and_trade,carbon,clean_tiers,federal_ces,voluntary_demand}.py`, `data/{datacenter,avoidable_cost_rate}.py` | **INERT** | forecast-only path; a `mode="backcast"` run never enters capacity evolution or the capacity market |
| `config/constants.py` (+986) | **INERT** | changes are CCS-retrofit HR penalty + load-growth rate tables — forecast constants only |
| `model/lp/rows.py` (+224) | **INERT** | federal-CES clean-tier crediting; the vector form is new, and its own docstring records that the tuple form — "every MISO keeper's" — stays byte-identical (ones vector) |
| `data/fuel/resolve.py`, `data/fuel/basis/miso.py`, `pipeline/backcast_config.py` | **INERT** | `miso_gas_marginal_commodity` default-off ⇒ `spot_cells is None` ⇒ the pre-existing `apply_miso_winter_citygate_daily` call is taken unchanged |
| `pipeline/backcast_config.py` seam limb | **INERT** | `miso_seam_neighbour_anchored_ladder` is **off in the keeper recipe** ⇒ `neighbour=False` ⇒ `inject_miso_seam_ladder_prices` called exactly as before |
| `data/outages.py`, `data/fleet/assembly.py` | **INERT** | new `extract_basis_share` parameter, `ScenarioConfig.unit_outage_extract_basis_share` default `False` |
| `data/fleet/eia860.py`, `data/fleet/assembly.py` | **INERT** | `cc_duct_peaking_row_scoped` default `False`; the function is byte-inert while off |
| `data/fleet/campd_bins.py` | **INERT** | CO2 booked `× (1 − ccs_capture_fraction)`; that fraction is 0.0 on every unabated unit, and a 2023 MISO backcast has no CCS cohort — exact no-op |
| `pipeline/backcast_config.py` NYISO limb | **INERT** | `nyiso_ct_peaker_bands_measured` default `False`, and NYISO-scoped (rule 25) |
| `data/reserve_requirements.py` | **INERT** | deletes an unused convenience wrapper; the solve path imports the per-ISO loaders by name |
| `data/egrid_sheets.py` + `data/zone_assignment.py` | **INERT** | content-addressed parquet mirror of the **same** eGRID sheet — pure I/O acceleration, same frame. The only substitution hunk on the path; named explicitly |
| `model/commitment.py`, `scripts/run_calibration_full.py` | **INERT** | `screen_stats` diagnostics accumulator + meta/recording plumbing |
| `scripts/lib/{bench_stamp,holdout_policy,invariant_ledger,mech_matrix,forecast_parity_registry}.py` | **INERT** | governance / scoring / registration tooling, not the solve path |
| `data/raw/_validation-source/caiso_*`, `actual_lmp.json` | **INERT** | CAISO artifacts (rule 25); `actual_lmp` is a scoring benchmark, not a solve input |
| `data/raw/reference/miso_gas_variable_transport*.csv` | **INERT** | consumed only by `miso_gas_variable_transport`, default-off and absent from the keeper recipe |

**Conclusion: the keeper's committed bundle IS the control (form 4). No control solve is spent.**
This audit is recorded here, before the arm is solved, so it cannot be written to fit the result.

## 6. Pre-solve arithmetic — the G-1 operand

From `_miso230_ct_drag_phase0.json`, differencing the arm's floor against the **keeper's own
committed** `class_hourly_2023` CT_PEAKER dispatch:

```
keeper CT_PEAKER dispatch          9.0554 TWh
arm    CT_PEAKER floor             8.8578 TWh
PREDICTED LIFT (class lower bound) 3.6544 TWh   in 1,522 hours
keeper C1 gap to EIA-923 actual    7.9826 TWh   (actual 17.038)
```

The lift is a **lower bound** (class-aggregate shortfalls cannot cancel against per-unit
surpluses). On it, CT_PEAKER-2023 lands near **−4.3 TWh**, inside the ±8.00 band with the seam
arm's +0.30 TWh push still inside.

## 7. THE SCREEN (rule 29): **2023, ONE LP, bundle DELETED before merge**

**Screen year = 2023, named here before the solve, and chosen on FOOTPRINT, not residual.** The
mechanism's own measured floor energy is largest in 2023 (**8.406** vs 7.311 / 7.469 TWh, §2c) and
its measured CT energy is largest there (15.037 TWh). 2023 also happens to be the year the seam
arm failed; that is **not** the reason for the choice and must not be read as one.

Command (single delta on the keeper recipe; `replay_keeper --set` routes both the solve kwarg and
the `ScenarioConfig` channel):

```
python3 scripts/replay_keeper.py results/calibration/miso220_nonsteamlift_B \
  --years 2023 --out-dir results/calibration/miso230_ctdrag_S \
  --set ct_netload_drag=true \
  --set ct_drag_overrides='{"ct_drag_slope_per_gw":0.01303,"ct_drag_intercept":-0.8108,
                            "ct_drag_cap":0.4394,"ct_drag_ramp_start":10,"ct_drag_ramp_end":21}' \
  --note "miso-230 screen: MISO-derived CT net-load drag [10,21)"
```

### The five gates — STRUCTURAL, and STOP-ONLY

They ask whether the mechanism does what its own arithmetic says. **They may kill the arm; they
may never promote it**, none is gated on the target residual, and none contributes to a
determination.

| gate | bar | fails if |
|---|---|---|
| **G-1 response** | CT_PEAKER-2023 model energy rises by **+1.8 to +5.5 TWh** (0.5×–1.5× the §6 lower bound) | wrong sign, under 1.8 (the floor is not reaching dispatch), or over 5.5 (doing more than its arithmetic implies ⇒ wiring error) |
| **G-2 replacement** | solved D-2: `reliability_floor × CT_PEAKER` forced = **0.000 TWh**, and `ct_netload_drag` is the **sole** CT_PEAKER forcing mechanism | any residual reliability_floor CT forcing ⇒ a stack, rule 19 |
| **G-3 confinement** | drag D-4 off-window share = **0.0000** against MISO `[10, 21)`; slack and dump both **0.0000 TWh** | any off-window binding, or a feasibility artifact |
| **G-4 no collateral flip** | no **non-target** load-bearing criterion flips PASS→FAIL vs the keeper's committed scores (C1 non-CT cells, C2, C3a, C3b, C6). C3c excluded — ledgered caveat, rubric v3.3 | any such flip |
| **G-5 forced budget** (the NAMED RISK) | **C8 PASSES** — at budget, or above it through rule 18's grounded conditional route (D-4 clean **and** D-1 `profile_r` / `cv_ratio` gates pass) | C8 FAIL |

**G-5 is the gate most likely to kill this arm, and it is named as such in advance.** C8 already
puts MISO CT_PEAKER at **27.6 / 18.6 / 15.6 %** forced — the fleet's largest share — against rule
18's 15 % peaker cap, passing today only through the grounded conditional route. §3 raises the
CT floor from 2.62 to 8.86 TWh, so the arm's forced share will rise steeply (order 70 %) and the
conditional route becomes the **only** available path. It is available on the merits — the window
is `[10, 21)` derived from the class's own conduct (§2a), declared in D-4 (§4), and the floor is
shaped by measured CF-vs-net-load so D-1 shape should hold — but if D-1 or D-4 misses, **the arm
dies here and the remaining years are never spent.**

## 8. If the screen clears

Full span **2023 2024 2025, ONE invocation, ONE bundle** (rule 16 `[R-ALLYEARS]`), **with
`miso_seam_neighbour_anchored_ladder` armed** — the pair is what promotes, per the owner's
standing decision. Scored with `scripts/calibration_verdict.py`. Promote on CALIBRATED /
CALIBRATED-WITH-CAVEATS; on a **load-bearing NOT-YET, report and escalate to the owner rather
than decertifying the ISO** (the miso-227 decision rule, unchanged).

The screen bundle `miso230_ctdrag_S` is **DELETED before merge** (rule 29(c)); every number this
session will ever cite from it lands in the FINDING. Git history is the record.

## 9. Governance

Rule 13 `[R-MEASURED]`: the trigger (net load) and the magnitude (a physical min-gen) both
regenerate for a forward year and respond to changed conditions — admissible in backcast **and**
forecast; the quarantined actuals pin is refused, not revived. Rule 17 `[R-FLOOR-WINDOW]`: driver,
window and forward story all stated (§2a, §2b, §4). Rule 19: replace, measured (§3). Rule 21
`[R-DOF]`: **no free parameter added**, ledger stays 41/2. Rule 22: 2023–2025 only. Rule 23: the
derive is frozen against residuals. Rule 25: no ERCOT/PJM coefficient and no ERCOT window carried;
the artifact is ISO-stamped and the D-4 override is MISO-scoped. Rule 27 `[R-PUSH]`: edited
locally, pushed as on-disk bytes, blobs verified. Rule 28: duty (c) does not fire (§1); duty (b)
is discharged on the existing `netload_drag_floors` cell. Rule 29: zero-LP phase 0 ran first (§3,
§6), the screen year is named on footprint (§7), and the bundle is deleted before merge.
