# ERCOT G-22 condition-responsive CT offer surface — design note (2026-07-06)

**Branch:** `claude/ercot-g22-offer-surface-owj77m` (lane L-12)
**Status:** DESIGN NOTE (first deliverable). Mechanism to be built default-off,
ERCOT-gated, with the pre-committed honesty gate in §5 and the full-span A/B in §6.
**Reads first:** the 2026-07-06 ercot34 calibration-log entry (the G-22 fold),
`docs/FINDING-ercot-priceshape-2026-07.md` §6 filed structural conclusion #1
(the sanctioned replacement this note builds) and §5/§6 (why the ercot33 wall was
REJECTED — the failure modes this design must not repeat).

---

## 1. The gap (G-22 wedge, as measured)

Keeper `ercot34-stage4-overlay-off` (AS co-opt endogenous; C1 PASS). In the **106
missed 2023 tail hours** (60 in Aug, HOD 14–20) the endogenous co-opt reserve
channel prices at ~zero (ORDC-family adder p50 $0.1; reserve MCPCs ~0) while the
energy dual sits at p50/p90 **$52/$75** — against the caught hours where the same
stack prices correctly (dual p50 $956, adder p50 $43, MCPC p50 $3.3k). Measured
RTOLCAP in the missed hours is p50 8.1 GW, above the ORDC knee: **the miss is not
reserve underpricing.** The G-22 fold established (calibration-log 2026-07-06) that
it is **energy-offer-carried scarcity against a ~3.2 GW P1 online-capability wedge —
"phantom sub-$200 spare."**

The wedge is a **peaker-offer** artifact. In P1 the model offers every online
CT/peaker MW at its flat marginal cost `heat_rate × gas + VOM` (~$50–150/MWh
depending on unit heat rate). So in the tail hours the model's peakers sit
*in-merit at sub-$200*, cap the energy dual at their marginal cost, and never let
the price climb to the scarcity level the real market cleared. The real fleet's
peakers had already offered themselves *out* of the money at the ERCOT offer-cap
band by those hours — which is exactly why the real price was high and the model's
was not.

## 2. Measured identification (60-Day DAM disclosure)

Source: `data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet`
— per-resource, per-hour, 10-point QSE-submitted energy offer curves
(MW/Price pairs), with HSL, LSL, Min Gen Cost, Resource Status, Awarded Quantity
and Settlement Point Price. Resource types map: `CCGT90/CCLE90`→CC, `SCGT90/SCLE90`→CT,
`GSREH/GSNONR/GSSUP`→ST_GAS, `CLLIG`→COAL. The metric is the **offer price at 90% of
HSL** (the price the unit puts on its last economic MW), for **ON** committed units,
indexed by a **net-load percentile** driver (`net-load = Σ awarded over
non-renewable dispatchable`, ranked within year — the same demand driver the West/Waha
gas-shape and the ST_GAS/CT reliability drags already key off).

Finding (scratchpad `char*.py`, to be committed as `scripts/derive_ct_offer_surface.py`):

| class | offer @90% HSL vs net-load percentile (2023) | 2024 / 2025 |
|---|---|---|
| **CT/peaker** | median **$150** below ~30th pct → **$1500** above; **$4000** above ~95th pct | median ~**$1500** across all deciles |
| CC | ~$17–18 flat (≈ marginal cost); <2% of hours >$100 even at top net-load | flat $15–23 |
| COAL / ST_GAS | ~$20–26 flat | flat |

Two facts drive the design:

1. **The CT/peaker offer sits in the ERCOT offer-cap band (~$1,500, cap-clamped
   near $4,000/$5,000 at the extreme), not at heat-rate×gas.** This is the
   ~10× gap between the measured peaker offer and the model's flat P1 peaker
   offer — the phantom-spare wedge, quantified from the offers themselves.
2. **It is condition-responsive.** In 2023 (the scarcity-tail year that carries
   the miss) the CT median offer *steps* from ~$150 to ~$1500 at ~the 30th
   net-load percentile. In 2024/2025 (milder tails) it is near-ubiquitously
   ~$1500 — i.e. peakers self-withhold across the board and only *set* price in
   the tight hours where they are marginal.

CC/COAL/ST_GAS energy offers at 90% HSL are ~marginal-cost and essentially flat
in net-load — **the mechanism must touch only the CT/peaker tranches.** CC scarcity
rent lives in the top few % of its curve (the peak tranche), not the 90% point,
and is out of scope here (touching it is what moved measured volumes in ercot33).

## 3. Why this is NOT the rejected ercot33 offer wall

The ercot33 "tuned offer wall" (`docs/FINDING-ercot-priceshape-2026-07.md` §6,
REJECTED under rules 13/26) was a **static** peak-band quantile ladder posted in
*every* hour, over *all* gas classes. It failed for two reasons this design fixes
by construction:

- **Static over-withholding.** ~240 MW ≥$200 in an average hour vs 1.3–2.7 GW in
  anticipated-tight hours — a static wall over-withholds ~1.7 GW *every mild day*,
  lifting the mild years broadly to FAIL (2025 C3a +3.8%→+7.7%). **This design is
  condition-responsive:** it is inert (near-marginal-cost) in the sub-hinge hours
  and steepens only in the top net-load-percentile hours where the tail miss lives.
- **CT↔ST startup-amortization coupling.** Repricing 40% of the peak bands over
  *all* classes perturbed P0 run lengths → re-amortized startup into P1 committed
  bids → the documented −0.25 CT↔ST offer coupling flipped ~8 TWh of mid-merit
  energy off CAMPD-measured (D-8). **This design touches only the CT/peaker
  economic+peak tranches** (leaving CC/ST/coal offer curves untouched), and §6's
  volume-neutrality gate is a hard promotion condition.

`docs/FINDING-ercot-priceshape-2026-07.md` §6 explicitly pre-registers this as
filed structural conclusion #1 — *"bin delivery-days by their net-load percentile;
the model selects the curve by its own day-state — forward-derivable,
condition-responsive, rule-13-admissible. This is the right form of the wall."*

## 4. The mechanism (`ercot_ct_offer_surface`, default-off)

A new ScenarioConfig gate `ercot_ct_offer_surface: bool = False`
(CLI `--ercot-ct-offer-surface`; requires `iso == "ERCOT"`), applied as a
**post-assembly, in-place `mc_base` modifier** in the ERCOT offer path — the same
seam and idiom as `apply_ercot_west_netload_gas_shape` (fuel.py) and
`apply_coal_tranches` (fleet.py), hooked in `runner.py` right after
`apply_coal_tranches` (runner.py:1015), with the ERCOT net-load computed inline
exactly as the CAISO import-solar-shape does (`year_demand.sum − Σ solar − Σ wind`).

`apply_ercot_ct_offer_surface(mc_base, dispatch_fleet, fleet_arrays, config, year,
net_load_mw)`:

1. Identify CT/peaker **economic + peaking** tranche rows (by class + tranche
   suffix — physics/label, no per-plant dict; rule 24).
2. Rank `net_load_mw` to a per-hour percentile `q[t]` (within-year; forward-native).
3. Look up the **measured** per-percentile-regime offer level `L(q[t])` from the
   frozen derive table (§5). Set
   `mc_base[ct_rows, t] = max(mc_base[ct_rows, t], L(q[t]))`
   — the offer is raised to the measured self-withholding level only where the
   measured curve is above the unit's marginal cost; in slack hours `L` is at/below
   marginal cost and the `max` leaves the merit order untouched (`np.maximum`,
   fully vectorized — no hour loop, rule 2).

Regime structure mirrors the two-regime West/Waha gas-shape: a small number of
net-load-percentile regimes (default two, hinge ≈ measured 30th pct), each carrying
the measured p50 top-of-curve offer for the CT/peaker class, ERCOT-cap-clamped.
Flag-off ⇒ byte-identical (the function early-returns unless the gate and
`iso=="ERCOT"`).

**Application point (design decision, gated by §6):** applied to `mc_base` (the
P1 bid basis). Because it only *raises* the CT peaker offer in tight hours, and
only for the peaker class, the expected P0 run-length perturbation is confined to
peakers in the very hours they should be marginal — but this is precisely the
ercot33 coupling risk, so §6's volume-neutrality gate is the arbiter. If the A/B
shows the coupling moving CC/ST volumes off CAMPD, the fallback is to apply the
surface to the **P1 bid cost only, after P0 run-length discovery** (leaving P0
unperturbed) — a one-line move of the call site, pre-registered here so it is not
a residual-chasing change.

## 5. Pre-committed honesty gate (rules 1, 11, 13, 20, 24, 25, 26)

Committed **before** any A/B solve, so no result can retro-justify a parameter:

1. **Parameters are the measured DAM-disclosure p50 top-of-curve offers per
   net-load-percentile regime**, pooled 2023–2025, produced by
   `scripts/derive_ct_offer_surface.py` → `data/raw/_processed-legacy/
   ercot_ct_offer_surface.csv` + a JSON the mechanism reads. Every number traces
   to the offer data. **None is fitted to a price or volume residual** (rule 13).
2. **Frozen against residuals (rule 20).** The table re-derives *only* when the
   60-Day disclosure data updates; a re-derive commit must cite the data change,
   never a residual. The hinge percentile and regime levels are measured, not swept.
3. **If the A/B degrades the backcast, the parameters do NOT move (rules 1, 11).**
   A worse fit is a discovered root-cause signal, not a tuning target — we keep the
   measured surface and investigate, or register it as a REJECTED probe (rule 15).
   We never retune `L` or the hinge to recover MAE.
4. **Volume-neutrality is a hard promotion condition (D-8 / ercot33 lesson).**
   CT_PEAKER / ST_GAS / CC class TWh must not move off CAMPD-measured beyond the
   keeper's own deviation. A price improvement bought by moving mid-merit energy
   off the measured allocation is a FAIL, whatever it does to the residual (rule 1).
5. **No broad elevation (anti-F1 / G-3).** Max monthly Δ vs the same-code
   surface-off arm must stay ~$0 outside the tail hours — the condition-responsive
   design's whole claim. A broad lift reproduces the ercot33 mild-year FAIL and
   is disqualifying.
6. **Forced-energy budget (rule 19).** The surface *raises* offers (withholds); it
   adds no floor. Confirm it creates no de-facto floor and peakers stay <10% of
   energy at any binding constraint.
7. **No cross-ISO leakage (rule 25).** Levels are the ERCOT offer-cap regime and
   ERCOT-gated; every other ISO carries the neutral (mechanism off). No generic
   fallback inherits an ERCOT-fitted band.
8. **Full-span A/B registered whatever the outcome (rules 15, 16).**

## 6. A/B plan

Base config = the `ercot34` recipe with the **four un-persisted gas-geography
fields restored from the bundle `run_config.json`** (`ercot_zonal_gas_basis`,
`ercot_west_netload_gas_shape`, `ercot_west_gas_delivered_floor=0.4`,
`oil_primary_bin_fuel` — the keeper REPLAY CONTRACT CAVEAT, calibration-log
2026-07-06). P1-only, `--year 2023 2024 2025`, one bundle per arm, years sequential.

- **Arm A (control):** ercot34 config, `ercot_ct_offer_surface=False`
  (expected byte-identical to a faithful ercot34 replay — the flag-off attribution twin).
- **Arm B (treatment):** same, `ercot_ct_offer_surface=True`.

Gates (all vs RT actuals, same-code A baseline): G-3 no broad elevation (§5.5),
G-1 acute-day tail (the 106 missed 2023 hours — the target), G-4 tail structure,
D-8 volume-neutrality (§5.4), D-2 forced-energy (§5.6). Both arms registered on the
dashboard (rule 15); keeper swap is an owner decision (not taken in this lane).

## 7. Scope guards (per the L-12 brief)

- Do **not** touch `model/capacity.py` (parallel capacity-economics lane) or
  `run_calibration_full.py`'s meta writer (orchestrator lane owns the replay-gap fix).
- Do **not** fold WS-B (G-37 storage-AS duration gate) — still below its acceptance band.
- Do **not** add any floor for C8 CT 12.4% (inherited named family; rule 19).
- Mechanism (b) *commitment thinness* (the `pipeline`/`dispatch.py` posture lever with
  CEMS-measured mlf) is the **other** G-22 remedy and lives in shared code a
  concurrent PJM port is building — **not built here**; coordinate via rebase, do
  not fork it. This lane ships mechanism (a) only, in the ERCOT offer namespace.
