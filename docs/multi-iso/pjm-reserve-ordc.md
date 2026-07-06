# PJM reserve / ORDC scarcity-pricing overlay

**Status:** implemented (post-solve overlay + measured-MCP validation), default
off. PJM. Measured & real for the backcast (measured requirement + plant-level
online reserve + published step curve), a published rule for the forecast.
**Zero parameters fitted to the price residual.**
**Code:** `src/market_sim/results/scarcity.py` (PJM section),
`scripts/derive_pjm_ordc_overlay.py`.
**Curve (cited):** `data/raw/_validation-source/pjm_ordc_curve.csv` +
`docs/multi-iso/pjm-reserve-curve-source.md`.
**Data:** `data/raw/PJM-AS/` (rules PDFs + measured RT/DA reserve markets
2023–2025 + `pjm_<yr>_as_up_mw.parquet`, the withholding series from
`scripts/build_pjm_as_withholding.py`). **Bundles:** `results/calibration/pjm_26`
(keeper), `results/calibration/pjm_27_aswh` (reserve-withholding probe — see
"Reserve-withholding recalibration" below).

This is the PJM analogue of `docs/ordc-overlay.md` (ERCOT), not a copy: ERCOT's
adder is a *smooth* LOLP curve; PJM's is a *vertical two-step* demand curve, so
the honesty gate is sharper and the conclusion is different.

## Why (the gap this closes — or doesn't)

`docs/multi-iso/pjm-lmp-residual.md` localized the PJM model's miss as a missing
**$75–200 afternoon reserve-scarcity regime** (energy-only annual LMP −1/−7/−17%
for 2023/24/25; the 11:00–18:00 ramp carries the gap, p90+ of the duration curve
explodes). PJM's real RT price = energy LMP + a reserve price component from the
co-optimized Operating Reserve Demand Curve (ORDC). The energy-only LP cannot
produce that component. This overlay reconstructs it from PJM's published market
design and adds it post-solve, leaving the LP's volumes/emissions untouched.

## The published mechanism (provenance)

PJM jointly clears energy and three nested reserve products (Synchronized ⊆
Primary ⊆ 30-Minute/Secondary) in two Reserve Zones (RTO and the
Mid-Atlantic/Dominion sub-zone), DA and RT, against **vertical two-step ORDCs**
(Manual 11 sec 4.3.3; established by the Reserve Price Formation reform, FERC
EL19-58/ER19-1486, order 2020-05-21, implemented **2022-10-01**). Per product:

```
reserves R, requirement REQ:
  R <  REQ           -> $850/MWh   (Step 1)
  REQ <= R < REQ+190 -> $300/MWh   (Step 2)
  R >= REQ+190       ->   $0       (no shortage)
```

The reserve clearing prices cascade the nested requirement shadow prices
(Manual 11 sec 4.4.1): `SRMCP = SP_SR+SP_PR+SP_30`, `NSRMCP = SP_PR+SP_30`,
`SecRMCP = SP_30`. The penalty factor enters the **energy** LMP because energy
and reserves are co-optimized. Full per-value citations (PDF + section) are in
`docs/multi-iso/pjm-reserve-curve-source.md`. Nothing is fitted to a residual.

## Model mapping

- **Requirement** — backcast uses the **measured** `as_req_mw` from
  `reserve_market_results_{yr}.parquet` (RT, aggregated to hourly) / `da_*`
  directly; forecast uses the Manual-11 rule (below).
- **Reserves** — the model's **plant-level online (synchronized) reserve**: a
  plant is synchronized when any of its tranches dispatch, and its reserve is
  the unused headroom across all its thermal tranches, net of the AS plan
  (`scarcity.pjm_online_reserve`, the shared online-reserve primitive the ERCOT
  AS-withholding work also builds). Reconstructed (not re-solved) from the
  bundle's `meta.json` via `run_year(..., fleet_only=True)`, cached as
  `pjm_availability.parquet`.
- **Adder** — `scarcity.pjm_reserve_cascade_mcp` applies the cited step curve
  to the online reserve vs the measured requirement; the binding reserve price
  (`energy_adder` = the Synchronized cascade) is added to every zone's LMP.
  Written to `scarcity.parquet[year, hour, scarcity_adder, ...]`, consumed by
  `analyze_lmp_residual.py --with-scarcity`. Dispatch/system parquets are
  byte-identical (verified: the deriver writes only the two new parquets); the
  adder never gates volumes.

## Honesty gate — settled first (and it bites the overlay, by design)

PJM's step is **vertical**: the adder is *exactly $0* unless reserves drop below
`REQ+190` (~3.3 GW). Three candidate reserve measures, on `pjm_26`:

| reserve measure | 2023 | 2024 | 2025 | usable? |
|---|---|---|---|---|
| TOTAL thermal headroom | ~38.3 GW | ~38.2 GW | ~37.6 GW | no — never < REQ → adder always $0 |
| per-tranche online headroom | ~0 | ~0 | ~0 | no — LP runs tranches bang-bang → always "short", always $850 |
| **PLANT-LEVEL online (synchronized)** | 15.5 GW | 16.1 GW | 14.6 GW | **the defensible measure** |

Only plant-level online reserve is meaningful — but it sits **~5× above the
~3.3 GW requirement** even in the hours reality was short. Against the measured
Primary requirement the curve bites on plant-online reserve in only:

| year | curve bites (step1 / step2) | measured RT shortage hrs (mcp≥$300) | model online reserve in those hrs (median) |
|---|---|---|---|
| 2023 | 8 h / 0 h | 15 | 12.7 GW (overall 14.9 GW) |
| 2024 | 20 h / 0 h | 18 | 14.6 GW (overall 15.4 GW) |
| 2025 | 3 h / 2 h | 38 | 11.7 GW (overall 14.0 GW) |

**The perfect-foresight LP is not thin when reality was thin.** In PJM's real RT
shortage hours the model still holds 12–15 GW of online reserve — far above the
~3.3 GW step breakpoint — so the published curve produces ~$0 there. The actual-
minus-model residual *is* monotone in online reserve (2024: +30 $/MWh in the
6–8 GW band, +5 in 13–16 GW, −2 above 20 GW; 2025: +800 in the <4 GW band), so
the signal is real and correctly localized — but the model's online-reserve
**floor (~6–8 GW)** sits above where the vertical step engages, so the step
never fires for those residual hours.

This is the gate result, reported per the brief ("If reserves can't yet be
measured online, stop and report; do not substitute a load proxy"): reserves
**are** measured online, and the honest answer is that the published vertical
step cannot self-target the $75–200 residual on this LP. We do **not** lower the
breakpoint, net a load proxy, or inflate the penalty to manufacture scarcity
(claude.md #11). The residual lives in the 6–13 GW online-reserve band, which in
PJM's market is the **opportunity-cost** reserve price (the marginal unit's lost
energy margin, set by AS co-optimization) plus congestion/uplift — not the
penalty-factor shortage regime. That is the AS co-optimization this overlay,
like the ERCOT one, explicitly does **not** attempt.

## Validation — the curve itself, against measured MCP

The primary measured check (`derive_pjm_ordc_overlay.py --validate-mcp`, no model
involved) confirms the published curve reproduces measured reserve pricing in the
regime an energy-only overlay can represent:

**(1) Penalty levels match the cascade** — measured RT maxima are exact multiples
of $850 (Manual 11 sec 4.4.1):

| year | SR max | Primary (NSR) max | 30-min (Sec) max |
|---|---|---|---|
| 2023 | $1,700 (2×850) | $850 (1×850) | $0 |
| 2024 | $1,700 (2×850) | $850 (1×850) | $0 |
| 2025 | **$2,550 (3×850)** | $1,700 (2×850) | $850 (1×850) |

**(2) Deficiency → shortage price** — in every RT 5-min interval where cleared
Synchronized reserves fell below the requirement (`total_mw < as_req_mw`: 18 /
2 / 22 intervals in 2023/24/25), the measured `mcp` was at the penalty level
(**100%** ≥ $300). The reverse direction (penalty-priced intervals at apparent
surplus: 1 / 13 / 50) is the **heavy-load requirement extension** (Manual 11
sec 4.3 Step 2 "+ additional reserves … in anticipation of heavy load") — the
binding curve used a requirement above the posted `as_req_mw`. The curve is
correct; the posted column is the base requirement.

The sub-penalty DA reserve MCP (max $187/$126/$370) is the opportunity-cost
component (no DA shortage in the window) and is **not** something the energy-only
overlay reproduces — the same boundary the ERCOT overlay draws at AS
co-optimization.

### Consequence check (energy LMP residual)

`analyze_lmp_residual.py --with-scarcity` on `pjm_26` — the overlay adds the step
adder in only 8 / 20 / 5 hours, so it closes **essentially none** of the
afternoon residual (Jul/Aug 2024 stays −7.7 $/MWh; hours >$75: model 0/0/3 →
+overlay 0/1/7 vs **actual 147/297/712**). Per claude.md #11 this points the
finger at the **reserve measurement / commitment**, not the curve: the LP's
perfect-foresight commitment keeps too much capacity synchronized and idle, so
its online reserve never thins to PJM's step. Closing the residual needs a
reserve **co-optimization** (the marginal-unit opportunity cost in the 6–13 GW
band) — out of scope here, exactly as for ERCOT — or a commitment model that
reproduces PJM's tighter real-time online posture. The curve and the measured-MCP
validation stand; the overlay is honest about not papering over the commitment
gap with a fitted parameter.

## Reserve-withholding recalibration — the re-solve the overlay deferred

**Status:** implemented, **bundle `results/calibration/pjm_27_aswh`** (`pjm_26`
config + `as_reserve_withholding` on, 2023–25 re-solved). This is **retained
structure**, not a probe to accept/reject by fit: PJM genuinely holds its
Primary Reserve out of the energy stack, so the model should too (claude.md #1 —
right structure first; backcast match is not the keeper criterion). The level
calibration (offer curves) is retuned *after* the reserve price structure is
complete, not by reverting the structure.

**What it does and does not do.** Withholding alone is **~inert on the energy
LMP** — necessary structure, but not sufficient to price the residual. The
afternoon $75–200 band is the reserve **opportunity-cost price**, whose correct
structure is energy+reserve **co-optimization in the LP** (the next build, below)
— a pre-solve headroom haircut cannot produce a reserve shadow price. So the
withholding stays on as the structural baseline; co-optimization is what carries
the band; offer-curve tuning then calibrates the level.

**What it does.** `ScenarioConfig.as_reserve_withholding` (the ERCOT primitive,
now generalized to PJM — shared `fleet._withdraw_top_of_merit`, per-ISO pool +
loader) removes a measured hourly reserve MW from the gas + flexible-oil
top-of-merit headroom before the energy supply curve clears. PJM's withheld
series is the **measured RT Primary Reserve requirement** (`as_req_mw`, service
`PR`, locale `PJM_RTO`, the binding upward 10-min product that nests
Synchronized — Manual 11 sec 4.4.1), 5-min→hourly on the non-leap 8760 clock,
~3 GW/yr, written by `scripts/build_pjm_as_withholding.py` to
`data/raw/PJM-AS/pjm_<yr>_as_up_mw.parquet`. Provenance: the same
Data Miner reserve-market parquets cited in `pjm-reserve-curve-source.md`. DA
(`da_reserve_market_results`) was considered as the basis for our single-clearing
(day-ahead-style) model: the Primary requirement is a reliability quantity
(≈1.5×LSC), basis-independent to ~3% (DA/RT means agree every year), so the
choice is immaterial to dispatch — RT was used because it has complete year
coverage while DA is truncated at year-end. We withhold the **requirement**, not
cleared `total_mw`, because cleared total includes Tier-1 synchronized headroom
that is not actually withdrawn from energy.

**What happened (the honest result).** Withholding the real ~3 GW reserve moves
the energy LMP by **~$0.1**:

| Jul/Aug residual ($/MWh) | 2023 | 2024 | 2025 |
|---|---|---|---|
| `pjm_26` energy-only | −6.24 | −8.82 | −11.25 |
| `pjm_27_aswh` energy-only | −6.20 | −8.81 | −11.07 |
| full-year mean | −0.86→−0.73 | −2.98→−2.95 | −8.62→−8.24 |
| full-year p50 (gate, no overshoot) | +1.81→+2.12 | +0.53→+0.56 | −1.51→−1.11 |

Hours >$75 (Jul/Aug) stay **0** vs actual 147/297/712. Volumes/emissions are
unchanged (annual generation identical to `pjm_26`; class shifts <0.6% — CC a
hair down, peaking/coal a hair up, the expected withholding direction), so the
calibration gates do not regress. The full-year p50 is preserved (no
overnight/shoulder overshoot).

**Why it is inert — the diagnosis (claude.md #11, root cause not buried).** The
top-of-merit withdrawal removes the **most expensive** headroom first, which in
PJM's comfortable afternoons (~$30–75, ~12 GW slack) is **idle** oil/CT-peaker
capacity sitting at zero dispatch. Lowering the upper bound of a non-dispatching
unit is a no-op for the LP, so the marginal afternoon unit (a part-loaded gas CC)
is unchanged and the price barely moves. Confirmed on the re-derived honesty
gate: the 3 GW withdrawal thins **total** reserve by ~3 GW (38→35 GW) but
**online** reserve by only ~1–2 GW (15→14 GW), because most of the withdrawal
lands on idle plants that were never part of online reserve. Online reserve stays
~14 GW — still ~4–5× the ~3 GW requirement, deep in the **opportunity-cost band**
where PJM's vertical ORDC step is $0. The residual is the sub-shortage reserve
*price* (the marginal unit's lost energy margin from AS co-optimization), which a
pre-solve headroom haircut cannot produce: thinning reserve further only makes
the vertical step bite at **penalty** levels ($850+), which *overshoots* the
actual $75–200 (overlay+withholding Jul/Aug 2024 swings to **+14.3**). The right
structure is **energy+reserve co-optimization** in the LP: a reserve-requirement
constraint whose dual is the reserve price, with reserve limited to deliverable
(10-min-ramp / synchronized) headroom so the requirement binds — the marginal
unit's offer then carries its reserve opportunity cost and the band is priced
*inside* the solve. That is the next structural build; withholding is its
pre-condition (it removes the must-hold MW from the energy stack), and
offer-curve tuning calibrates the level afterward. `pjm_27_aswh` is the
structural baseline — matching the residual is not what makes a run a keeper
(claude.md #1).

**Consistency fix (a real bug found en route).** `derive_pjm_ordc_overlay.py`'s
`_run_year_kwargs` did not forward `as_reserve_withholding`, so on a withholding
bundle it reconstructed the fleet at *full* availability while reading the
*withheld* dispatch — over-stating reserve by the withdrawn MW (it reported
online reserve unchanged at ~15 GW). The reconstruction now mirrors the solve.

## Campaign: build the reserve price structure, then tune (claude.md #1)

User-set methodology: **right market structure first, offer-curve tuning second;
backcast match is not the objective.** The afternoon $75–200 band is a
price-formation structure the energy-only LP lacks, built in sequence (not by
fitting an adder or a haircut to the residual).

**Targeting (Jul/Aug afternoon peak, 2024, from `pjm_27_aswh`, via
`scripts/probes/_pjm_online_headroom_breakdown.py`).** Online plants are already ~91%
loaded; the 13.4 GW of online headroom is CT_PEAKER 4.8 (75% loaded) + COAL 3.4 +
CC_REGULAR 2.9 + baseload 1.8 + ST_GAS 0.5. Two findings reframe the build:

1. The honesty gate's "14 GW online vs 3 GW" compares the model's **total**
   online headroom to PJM's **synchronized-reserve product** (the 10-min slice) —
   different quantities. PJM's online fleet also carries ~10 GW of slower
   unloaded capacity; reserve scarcity (requirement binding) is genuinely rare in
   both. So the band is the reserve **opportunity-cost price in non-shortage
   hours**, not a shortage.
2. **Why the pre-solve withholding is inert, exactly:** top-of-merit removes the
   *expensive* CT/oil headroom, but the clearing price is set by the *cheap*
   CC/coal headroom *below* it, so the margin is unchanged. Reserve is real but
   must come off the **marginal** headroom to move price — which a pre-solve
   availability haircut cannot target.

**Phase 1 — commitment posture.** The LP's energy pass (P1, no unit commitment)
part-loads many CCs rather than fully loading fewer, so cheap headroom is
abundant at the margin. Tighten the online posture (startup/min-run economics, or
the P2 screen) so the marginal afternoon unit reflects PJM's real commitment.

**Phase 2 — energy+reserve co-optimization (the lever that prices the band).**
Add reserve decision vars `R[g,t] ≥ 0` for the reserve-eligible thermal pool with
`P+R ≤ pmax·avail`, `R ≤ ramp10[g]` (10-min deliverable — the cap that makes the
requirement bind), and per-reserve-zone `Σ R ≥ REQ[t]` (the measured Primary
requirement). The requirement's **dual is the reserve price**; because reserve is
held on the cheapest-opportunity-cost (marginal) MW, holding ~3 GW displaces
cheap energy and lifts the afternoon LMP by the offer-curve slope over 3 GW —
priced *inside* the solve, no overlay, no haircut. (This is the structure the
pre-solve withholding only approximated; withholding is its pre-condition.)
Note: adds `R` columns for the reserve pool — memory-heavy at PJM plant-level
(energy-only already nears the box limit), so solve serially / profile first.

**Phase 2 build status & the bind gate (2026-06-22).** The co-opt inputs and the
runner branch are built (`scarcity.pjm_reserve_coopt_inputs`, the PJM analogue of
`ercot_reserve_coopt_inputs`: measured `pr_req_mw`+190 RHS, published Primary/RTO
two-step curve, generic thermal eligibility; `runner.py` `iso=="PJM"` branch;
`reserve_price` persisted in `system.parquet`; `tests/test_reserve_coopt.py`). The
mechanism is unit-validated (slack headroom → reserve $0; tight → $300 lifting the
energy LMP +$300). **But the as-built reserve rows reuse the existing
zone-aggregate `dispatch._build_reserve_rows`, which caps a zone's reserve at its
TOTAL eligible thermal headroom — and that is the measure the honesty gate already
showed is ~38 GW, far above the ~3.3 GW step.** The bind-gate probe
(`scripts/probes/_pjm_coopt_bindgate.py`, no LP re-solve — it reads the
energy-only `pjm_38` dispatch) confirms it empirically for 2024:

| reserve measure (2024) | system-wide GW, min / p50 | hours < req (3.6 GW) | verdict |
|---|---|---|---|
| zone-aggregate total headroom (as-built) | 7.34 / 50.5 | 0 / 8760 | clears at **$0** every hour |
| plant-level online headroom | 0.81 / 21.6 | 16 | tail only |
| online + 10-min ramp-deliverable | 0.54 / 10.3 | 49 | tail only, at penalty |

So the published vertical step **never fires** under the as-built co-opt (finding
#2: idle eligible headroom ≫ requirement). A deliverable/ramp cap (finding #3)
thins reserve enough to cross the requirement in only ~49 h/yr — and those bind at
the **penalty** step ($300–850), the shortage regime that *overshoots* the $75–200
band, while the broad afternoon band still sits on free deliverable headroom
(median 10.3 GW, 2.9× the requirement). The $75–200 **opportunity-cost** middle
therefore needs the *per-gen* `R[g] ≤ ramp10[g]` reserve rows (so reserve competes
with energy on the marginal unit) **plus** the Phase-1 commitment tightening — not
the ramp cap alone. The per-gen build is **memory-infeasible on the 15 GB box**
(the zone-aggregate co-opt already OOMs at ~16 GB; per-gen reserve vars at PJM
plant scale are heavier) and is **blocked on ramp-rate data absent from
`FleetArrays`**. Reported per claude.md #11 — breakpoint not lowered, penalty not
inflated. Commitment posture (Phase 1) is the prerequisite lever, coupled with the
cheap-marginal-coal suppression (`docs/multi-iso/pjm-coal-offer-handoff-2026-06.md`).

**Phase 2 re-gate (2026-06-28, pjm-price-compression-61 branch).** Two of the
three blockers above have since cleared, but the binding one has not:

1. **Ramp-rate data is no longer absent.** `FleetArrays.ramp10` now exists and is
   populated (`data/fleet.py`: `RAMP10_FRAC_BY_GROUP`/`RAMP10_FRAC_BY_FUEL` ×
   `pmax`, wired at build, regenerates for a forecast year). The
   `R[g] ≤ ramp10[g]` deliverable cap is therefore now buildable from fleet
   data — the data blocker the 2026-06-22 note recorded is resolved.
2. **The deliverable/online reserve-scoping mechanisms now exist.**
   `dispatch._build_reserve_rows` gained an `online_gated`/`online_rho` path
   (`R[c,z] − ρ·ΣP ≤ 0`, idle capacity contributes no reserve) and a
   `reserve_supply_cap` re-scope (cap cleared reserve at a measured/deliverable
   capability instead of full-fleet headroom). ERCOT uses both
   (`ercot_rtolcap_supply_cap_mw`); PJM's `pjm_reserve_coopt_inputs` + runner
   branch still pass only the bare `(req, eligible, penalties, widths)`, so PJM
   is **wired but un-scoped** — it still draws on total zone headroom.
3. **The memory blocker stands, and it now gates everything.** The zone-aggregate
   co-opt OOMs above ~16 GB; the 15 GB calibration box cannot run *any* co-opt
   variant (zone-aggregate or per-gen). So even the cheap re-scope in #2 cannot
   be exercised here, let alone the per-gen rows.

And the analytical conclusion from the bind-gate table above is unchanged by #1/#2:
**no zone-aggregate scoping can price the $75–200 band, because the model is not
tight.** Online-gating bounds reserve at `ρ·ΣP`, and a deliverable supply cap
bounds it at `Σ ramp10` — both are ≫ the ~3.3 GW requirement on a 180 GW fleet,
so the balance still clears at $0 from free headroom. The opportunity-cost band
requires reserve to compete with energy on the *same marginal unit* (per-gen
`R[g] ≤ ramp10[g]` with `P[g]+R[g] ≤ cap[g]`), which is the heavier build, **and**
the Phase-1 commitment tightening so the model's online reserve thins from ~14 GW
toward PJM's real ~3 GW (the perfect-foresight over-commitment is what keeps free
headroom abundant). Net: the top-tail decompression is now blocked only on
(a) hardware (a box that fits the per-gen co-opt LP) and (b) the commitment
posture — not on data or on the reserve-row primitives, both of which are ready.

**Phase 2 re-gate, EMPIRICAL (2026-06-28, pjm-62-price-duration-curve branch).**
The 2026-06-28 re-gate above made two claims that are now tested with code, not
asserted — one is **falsified**, the other **confirmed**:

1. **The memory blocker (#3 above) is WRONG — the zone-aggregate co-opt FITS the
   15 GB box.** A single-year memtest (pjm 61 config + `energy_reserve_coopt`,
   2024) peaked at **~13.9 GB**, and the full 3-year `pjm 62` run below peaked at
   **~14.5 GB** (year 2025, the tightest), well under the 15 GB ceiling. Years
   solve sequentially with memory released between them, so the per-year peak —
   not a 3-year sum — is what matters. The earlier "OOMs above ~16 GB / cannot run
   *any* co-opt variant on 15 GB" was stale (likely a heavier earlier config). So
   the cheap zone-aggregate re-scope was always runnable here; only the **per-gen**
   `R[g] ≤ ramp10[g]` build remains plausibly memory-heavy (untested).

2. **The deliverable/online scoping (#2 above) was wired and run — and clears
   $0, exactly as the analytical conclusion predicted.** `pjm 62` (bundle
   `results/calibration/pjm62_coopt_deliverable`, dashboard
   `2026-06-28-pjm-62-coopt-deliverable`, registered PROBE) completes the PJM
   co-opt to ERCOT parity: new `scarcity.pjm_reserve_deliverable_supply_cap_mw`
   (Σ ramp10[eligible], availability-scaled) + `pjm_reserve_supply_cap` /
   `pjm_reserve_online_gated` (ρ=1.0) config flags, wired into the
   `run_calibration` PJM co-opt branch. Run with both on, 2023–2025:

   | year | pjm 62 avg/max $/MWh | pjm 61 energy-only avg/max | reserve_price |
   |---|---|---|---|
   | 2023 | 26.42 / 56.50 | 26.42 / 56.50 | $0 every hour |
   | 2024 | 24.89 / 58.66 | 24.89 / 58.66 | $0 every hour |
   | 2025 | 35.06 / 76.97 | 35.06 / 76.97 | $0 every hour |

   Identical to the cent. The logged deliverable cap is **~50 GW** (Σ ramp10 over
   ~2,650 eligible units — CT peakers contribute 100% of pmax, CCs 40%) and the
   online-gated bound ρ·ΣP is larger still; both sit **~15× above** the ~3.4 GW
   measured Primary requirement, so the balance row never binds and the published
   vertical ORDC step never fires — `reserve_price` is $0 in all 8,760 hours of
   every year (verified in `system.parquet`). This is the empirical confirmation
   the older note reached by analysis: **no zone-aggregate scoping can price the
   $75–200 band, because the perfect-foresight LP is not tight.** No breakpoint
   was lowered and no penalty inflated to force a non-zero (claude.md #11); the
   honest result is a clean $0.

   Net unchanged: the top-tail decompression is blocked **only** on (a) the
   per-gen `R[g] ≤ ramp10[g]` co-opt (reserve competing with energy on the same
   marginal unit) and (b) Phase-1 commitment tightening (so online reserve thins
   from ~14 GW toward PJM's real ~3 GW). The reserve-row primitives, the
   deliverable-cap data, AND the 15 GB box are all ready — the remaining blocker
   is the per-gen build's memory (untested) plus commitment posture, not the box.

**Phase 2 per-gen memtest (2026-07-02, pjm-pergen-reserve-memory branch).**
The per-gen co-opt code is merged (PR #1251, commit 48cc0bd,
`pjm_reserve_pergen`, `ScenarioConfig` field default `False`) and produces the
correct LP: 257 R columns (one per eligible unit per balance family), 2,624
member units, 2 balance families (RTO + MAD), yielding a PJM-2024 LP of
**2,506,224 rows × 27,655,320 columns, 56M nnz** — roughly 3× the zone-aggregate
LP in each dimension. Memtest results on the 16.86 GB calibration box:

- **2024 single-year (P0):** solved successfully, VmHWM **~15.10 GB**. After
  `addRows` the working set was ~6.0 GB; P0 simplex grew it to ~15.1 GB.
- **2024 single-year (P1 warm-start):** **OOM-killed** at RSS ~14.6 GB. The P1
  re-solve on the warm-started basis pushed past the available headroom (~15.7 GB
  after OS/other processes on the 16.86 GB box) and the kernel OOM-reaper killed
  the process. The P1 solve's memory profile is not monotonic — RSS oscillates
  between ~14–15 GB during basis updates — so the OOM fires on a transient spike,
  not a sustained climb.
- **HiGHS LEAN mode** (`MARKET_SIM_HIGHS_LEAN=1`, `simplex_scale_strategy=0`):
  saves **~10 MB** — negligible. The solve workspace is dominated by basis
  factorization, not the scaling vectors LEAN removes.
- **Dantzig pricing** (`simplex_dual_edge_weight_strategy=0`): tested and
  **rejected**. On this degenerate LP (reserve vars mostly at zero), Dantzig does
  fewer operations per iteration but needs dramatically more iterations. P1
  warm-start took 10+ minutes without completing (vs ~3-4 min with default DSE).
  Removed from the LEAN path.

Conclusion: the per-gen co-opt is **memory-infeasible on the 16.86 GB box** (the
P0 fits but P1 does not — both passes are required for bid-cost pricing). The
merged code stays gated `default off`. Phase 2 requires either a larger box
(≥20 GB to provide safe headroom) or an LP-size reduction (e.g. tier the 257
R columns by unit size, dropping small units that never bind). The pjm-76 keeper
runs the zone-aggregate co-opt only.

**Phase 2 UNBLOCKED (2026-07-06, pjm-c3-reserve-phase2 lane).** Both remaining
blockers cleared; the full-span probe is `pjm-81` (bundle
`results/calibration/pjm81_coopt_pergen`, pjm-78 baseline recipe + the two
Phase-2 flags):

1. **Memory (blocker a): re-tiered to the MISO keeper's pooling.** The
   merged plant-in-MAD tier (257 R columns → 2.25 M joint rows; P0 15.1 GB,
   P1 OOM-killed — the 2026-07-02 memtest) is replaced by the
   **(zone, fuel-class) pooling everywhere** that the `miso-39` KEEPER runs
   (`_miso_design` pergen branch, `miso-reserve-coopt.md`): on the real 2024
   fleet, **39 R columns, 341,640 joint rows (~6.6× fewer)**, hourly
   availability-scaled deliverable caps (the MISO convention — outages thin
   the pool's cap in exactly the hours capacity is out). Cross-ISO memory
   evidence: ERCOT's `ercot34` keeper co-opt is zone-aggregate pooled
   headroom rows (no R-per-unit) and fits the box; MISO's class-tier pergen
   fits with a swapfile for transients; only PJM's finer plant tier OOM'd.
   Same published two-step ORDC, same nested RTO+MAD measured families —
   the tier is a documented memory scope-down, never a breakpoint/penalty
   change (rules 1/11). Reserve still competes with energy at the marginal
   *pool* (joint Σ P + R ≤ Σ cap per pool-hour).
2. **Ramp data (blocker b): measured intake replaces the class estimate.**
   New `ramp-capability` clean datatype (schema
   `data/dictionary/schema/ramp-capability.schema.yaml`, curation
   `scripts/curate_ramp_capability.py`, PJM/MISO registered): **EIA-860
   Schedule 3.1 "Time from Cold Shutdown to Full Load" = "10M"** fast-start
   thermal capacity per plant (the measured 10-minute-deliverable flag;
   ~3.0 GW in the PJM BA) and the **CAMPD CEMS maximum observed 1-hour
   plant gross-load up-ramp** (pooled 2023–2025; holdouts excluded, rule
   22). `market_sim.data.ramp_capability.measured_ramp10_frac` reconciles
   them onto `FleetArrays.ramp10` behind GATED
   `measured_ramp_capability` (default off): fast-start floor, envelope
   ceiling on the NREL class rate (CEMS is hourly, so the envelope is a
   ceiling, never the 10-minute quantity itself), class-frac fallback for
   uncovered plants (rule 14). On the 2024 fleet the measured
   reconciliation thins the deliverable cap ~50 → ~40 GW (p50).

**Phase 3 — retune offer curves** to the corrected structure (the level), only
after phases 1–2 are in.

## Forecast rule (no measured requirement available)

Forecast years have no `as_req_mw`, so the requirement is the **Manual 11 sec 4.3
rule** = f(Largest Single Contingency, load):

- Synchronized Reserve Requirement = Largest Single Contingency (LSC).
- Primary Reserve Requirement ≈ 1.5 × LSC (the measured RTO `PR/SR` requirement
  ratio is **1.45** in 2023 — the 150%-of-contingency convention).
- 30-Minute (Secondary) Requirement from the largest gas contingency.
- On-peak Hot/Cold-Weather-Alert hours extend all three (sec 4.3).

LSC is the largest online unit's EcoMax; in the forecast fleet that is the single
largest generator (a nuclear unit, ~1,300 MW RTO-wide). The plant-level online
reserve and the step curve then price scarcity to fundamentals.

## Reform / regime gating

The two-step `$850/$300/+190 MW` curve has been **stable** across the backcast
(Manual 11 Rev 127 → 129 → 136, all identical), in force since the Reserve Price
Formation reform went live **2022-10-01** (FERC EL19-58). So unlike ERCOT (whose
ORDC was *replaced* by RTC+B AS demand curves on 2025-12-05), PJM has **no
regime switch** inside the 2023–2026 horizon: the same cited curve governs the
backcast and the near-term forecast. Pre-reform (< 2022-10-01) is out of scope —
the backcast does not reach it — and is deliberately not encoded; the CSV's
`effective_date` is `2022-10-01` for every row. Any future PJM ORDC change is a
CSV edit (a new dated block), never a code change.

## Scope notes

- **Opportunity-cost reserve price / AS co-optimization** — the sub-shortage
  reserve MCP that carries the $75–200 residual — is the **next structural build**
  (energy+reserve co-optimization in the LP; see "Reserve-withholding
  recalibration" above), not a permanent boundary. The post-solve overlay only
  prices the shortage (penalty) regime.
- The overlay never enters the LP objective or constraints.
- PJM is a capacity-market ISO; resource fixed-cost recovery runs through the
  capacity market (`capacity_revenue_per_mw_yr`), so — unlike ERCOT — the
  scarcity adder is **not** wired into the capacity-economics screens here. The
  overlay is a price-formation / residual-diagnosis series, not a revenue stream.

## How to run

```bash
# PRIMARY measured validation (curve vs measured MCP — no model, fast):
python scripts/derive_pjm_ordc_overlay.py results/calibration/pjm_26 --validate-mcp

# Honesty gate (model online vs total reserve vs measured requirement):
python scripts/derive_pjm_ordc_overlay.py results/calibration/pjm_26 --diagnostic

# Build the overlay (writes scarcity.parquet; no LP re-solve):
python scripts/derive_pjm_ordc_overlay.py results/calibration/pjm_26

# Localize the residual with the overlay applied:
python scripts/analyze_lmp_residual.py results/calibration/pjm_26 \
    --with-scarcity --months 7 8

# --- Reserve-withholding recalibration (the re-solve) ---
# 1. Build the measured withholding series (RT Primary Reserve requirement):
python scripts/build_pjm_as_withholding.py            # 2023 2024 2025
# 2. Re-solve the keeper config + withholding, one year per parallel job
#    (claude.md #45; cap ~2 concurrent — 2 PJM plant-level solves peak >15 GB):
python scripts/probes/_pjm_aswh_run.py 2023 results/calibration/pjm_27_aswh_2023
python scripts/probes/_pjm_aswh_run.py 2024 results/calibration/pjm_27_aswh_2024
python scripts/probes/_pjm_aswh_run.py 2025 results/calibration/pjm_27_aswh_2025
python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_27_aswh \
    results/calibration/pjm_27_aswh_202{3,4,5}
# 3. Re-derive + re-check the residual (result: ~inert — see section above):
python scripts/derive_pjm_ordc_overlay.py results/calibration/pjm_27_aswh --diagnostic
python scripts/analyze_lmp_residual.py results/calibration/pjm_27_aswh --months 7 8
```
