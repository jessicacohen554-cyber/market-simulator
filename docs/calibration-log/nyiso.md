# Calibration Log — NYISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for NYISO calibration work. Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — gas_daily_shape §3.7 fix A/B: NYISO exactly price-inert (Transco hub overlay supersedes); probes registered

Cross-ISO session (full entry: `docs/calibration-log/governance.md` 2026-07-19
gas_daily_shape §3.7). On the nyiso-62/63 recipe the fix is exactly
price-inert in all three years — the Transco Z6 NY / Iroquois hub-basis daily
overlay replaces every covered gas row. Registered
`2026-07-19-nyiso-gasshape-interpfix`(+`-base`) as the inertness record; no
keeper action (the NYISO keeper advanced mid-session to nyiso-64-outage-refix,
whose gas path uses the same overlay, so the inertness conclusion transfers).

## 2026-07-20 — phantom nyiso-65 keeper diagnosed + resync keeper nyiso-66-resync-base

The NYISO keeper `2026-07-19-nyiso-65-scr-edrp` was MIA on the Run Explorer and
scored "not calibrated" because it was a **phantom registration**: only the
registry sidecar + keeper pointer were committed; its run payload
(`runs/<id>.js`) and solve bundle (`results/calibration/nyiso65_scr_edrp/`)
appear in **0 commits** (register commit `b9caa32` said "remaining files
follow" — they never did). Tracked in `scripts/lib/known_unsynced_keepers.py`.
The nyiso-65 recipe is **not reproducible from the tree**: two of its three
defining ingredients were also never committed — the `nyiso_scr_edrp` SCR/EDRP
demand-response lever (`src/market_sim/data/nyiso_demand_response.py` is
orphaned: imported nowhere, not a `ScenarioConfig` field, not a
`solve_and_persist` param; its data-build `scripts/data/build_nyiso_scr_edrp.py`
is un-synced) and the 2,641-row corrected `campd-unit-outages-NYISO.csv` extract
(the tree carries 1,599 rows). Only the eastern-seam `Capital_Hudson 1,600 MW`
landing (code-level) is on the tree.

Action: removed the Frontier designation from the keeper shard; re-solved the
**reproducible on-tree base** — the nyiso-62 `cc_hr_regate` meta replay
(`replay_keeper.py`) across 2023-2025 — and registered
`2026-07-20-nyiso-66-resync-base` as the new keeper (real, committed artifacts:
payload + slim bundle + `hourly/` sidecars + attestation +
`legitimacy_diagnostics.json`). Deleted the phantom nyiso-65 sidecar; dropped
nyiso-65 from `known_unsynced_keepers`. **DETERMINATION NOT-YET**: C1 fuel-mix
FAIL (13/14, 2023 CC_REGULAR −3.76 TWh), C3b price-shape FAIL (2024 NRMSE
0.201), C3c tail FAIL; C3a mean-LMP PASS all years (2023 +8.8%, 2024 −7.2%,
2025 −8.1%); C2/C4 PASS; C6/C7/C8 PASS (C8 ST_GAS grounded-above-budget); C5a
CO₂ commercial-band caveat (2025 +9.5%). Closing C1/C3b requires **restoring the
un-synced nyiso-64/65 ingredients** (wire the DR lever into the engine +
re-derive the 2,641-row outage extract & ST reliability floors) — the named
follow-up.

## 2026-07-21 — nyiso-68 keeper: restored the un-synced nyiso-64/65 ingredients (corrected outages + SCR/EDRP DR); C1 fuel-mix CLOSED, 2023 reserve-formation gap named

Promoted `2026-07-21-nyiso-68-scr-edrp` (bundle `results/calibration/nyiso68_scr_edrp`,
DETERMINATION **NOT-YET** but **strictly more structurally faithful** than the
nyiso-66-resync-base predecessor). Restored BOTH previously-un-synced nyiso-64/65
ingredients and nothing else — zero residual tuning (rule 22), zero new residual DOF
(rule 18).

**Ingredient (a) — corrected outage extract (the #1 lever).** The tree carried a
stale 1,599-row `campd-unit-outages-NYISO.csv`; the frozen
`scripts/data/derive_campd_unit_outages.py --iso NYISO` deterministically produces
**2,641 rows** (the nyiso-64 extract). Regenerated + committed (rule-23 data re-sync,
cites the derive-script logic that PR #2641 committed but never re-ran, NOT a residual).
This makes solve-time availability consistent with the ST reliability-floor fracs that
were **already committed** in `reliability_floor_coeffs_NYISO.csv` (re-derived on the
2,641-row extract on 2026-07-19); `derive_nyiso_st_reliability_floor.py --no-fetch` on
the restored extract reproduces those committed coefficients byte-for-byte (NYC base_ev
0.533 / base_24h 0.496; LI 0.572 / 0.436). nyiso-66 had been applying the corrected
(higher) fracs against stale (inflated) availability → double-counted → **over-forced
downstate ST_GAS must-run**, crowding out CC. Restoring the extract lowers the forced
ST_GAS and frees CC volume: **C1 fuel-mix FAIL → PASS all years** (CC_REGULAR 2023
−3.76 → −2.35 TWh, 2024 −2.94 → −1.57, 2025 −1.12 → +0.43; ST_GAS falls correspondingly,
total thermal conserved). C7 shape and C8 forced-share still PASS.

**Ingredient (b) — SCR/EDRP demand response (wired into the engine).** The orphaned
`src/market_sim/data/nyiso_demand_response.py` (imported nowhere) is now live:
`FUEL_TYPE_MAP` gains `demand_response(16)` (excluded from generation-mix scoring in
`results/export.py` — avoided load, not generation); `ScenarioConfig.nyiso_scr_edrp` +
`nyiso_scr_edrp_strike` (default the published $500/MWh EDRP compensation floor) thread
through `solve_and_persist` → `run_year` to the fleet-build seam (per-zone
price-responsive supply blocks appended like the PJM virtual-bid units, seasonal
availability injected mirroring offshore wind), plus CLI flags `--nyiso-scr-edrp[-strike]`.
Committed `scripts/data/build_nyiso_scr_edrp.py` (byte-identical to the Gold-Book-transcribed
enrollment CSV; sha256 verified). Endogenous scarcity trigger, never pinned to event dates
(rule 13/17); Gold-Book capability (2023/24/25 summer 1.23/1.29/1.49 GW) + published strike =
**zero residual DOF** (n_residual stays 5, n_entries 11 → 12).

**Why still NOT-YET — the named root cause (issue #1344).** The corrected (physically-real)
outages regress 2023 price: C3a mean +17.8%, C3b NRMSE 0.215, C3c tail 31h vs RT 10h (2024
and 2025 C3a/b/c ALL PASS). Diagnosed from `system_2023` hourly: every one of the 57 >$300
zone-hours is **downstate (LI+NYC), summer (Jul-Sep), reserve-price-driven** (54/57 have
reserve_price>$50, price↔reserve r=0.79) with **zero unserved energy**. The corrected outages
thin downstate thermal reserve headroom in tight summer hours, and the energy+reserve co-opt
is **thermal+storage-only** — it lacks NYISO's real East-region hydro + pumped-storage
(Blenheim-Gilboa ~1160 MW) 10-min reserve supply and SCR/EDRP 30-min operating-reserve supply,
so the East-10min / SENY-30min ORDC shadow price spikes into the LBMP. Per **rule 1/11** the
correct measured mechanisms STAY IN even though 2023 fit regressed; reverting to the stale
outages to keep C3a passing (nyiso-66's only reason it passed) is exactly what rule 1 forbids.
The DR lever (30-min SCR, $500 strike) helps 2023 mean marginally (+19.8% → +17.8%) but cannot
touch the $300–500 reserve tail; the named fix is **lever #3 (hydro/PS + SCR/EDRP reserve
eligibility)**, which additionally requires ADDING Blenheim-Gilboa PS to the NYISO dispatch
fleet (it carries no hydro/PS units today) — a separate structural workstream, deferred with
owner sign-off, NOT a residual tune.

Scorecard (nyiso-68): C1 PASS · C2 PASS · **C3a FAIL (2023 +17.8%)** · **C3b FAIL (2023 0.215)** ·
**C3c FAIL (2023 31h)** · C4 PASS · C5 CO₂ CAVEAT (2025 +8.3% commercial band) · C6 governance
PASS · C7 shape PASS · C8 forced-share PASS. Also registered the isolation probe
`2026-07-21-nyiso-67-outage-resync` (corrected outages, NO DR) which shows the outage lever
alone closes C1 and exposes the same 2023 reserve tail.

## 2026-07-22 — lever 3 step 1: conventional-hydro reserve-supply eligibility (correct, marginal, insufficient); outage-source determination (keep CAMPD)

Two deliverables this session; nyiso-68 stays the keeper.

**Outage source — determination, no change.** Checked whether NYISO publishes a
native DAM/outage instrument to replace the CAMPD/CEMS proxy (the CAISO/PJM/MISO
pattern — `fetch_caiso_dam_outages.py` etc.). It does **not**: NYISO keeps
unit-level generator outages **confidential**, its DAM bid/award data is
**masked** (no unit identities), and the only public generator-outage product is
a non-archived system-aggregate forecast (MIS P-15). CAMPD/CEMS + NERC GADS + EIA
+ NRC remains the correct and only public stack. Recorded in
`docs/handoffs/nyiso-outage-source-determination-2026-07.md`.

**Confirmed the nyiso-68 baseline.** nyiso-68 already runs
`nyiso_dynamic_reserve_requirements=True` + SCR/EDRP + corrected outages (the
2026-07-10 Ask-B plan was executed by the 2026-07-21 session, not a pending
step). Its sole load-bearing miss is 2023 C3 (mean +17.1% by the demand-wt DA
recompute here, matching the logged +17.8%); 2024/2025 C3a/b/c all PASS. The
2023 tail is downstate, summer, reserve-price-driven — the co-opt's reserve
**supply** is thermal+storage-only.

**Lever 3 step 1 — hydro reserve-supply eligibility (nyiso-69, CANDIDATE).**
Added `nyiso_hydro_reserve_eligible` (GATED, default-off): NYISO's in-fleet
conventional hydro (154 units, ~4.6 GW — Capital_Hudson 554 MW East, Upstate_West
4,093 MW NYCA; no downstate hydro) joins the co-opt reserve-eligible set in both
the full (30-min) and quick-start (10-min) classes, the CAISO
`_caiso_reserve_eligible` precedent (NYPA Niagara/St-Lawrence + Capital hydro are
certified NYISO reserve providers; held reserve spends no water — the monthly
energy budget bounds only dispatched energy). A/B replay of the nyiso-68 recipe:

| year | C3a %err (68→69) | C3b NRMSE | C1 fuel-mix |
|---|---|---|---|
| 2023 | +17.1% → **+16.4%** | 0.630 → 0.632 | unchanged (PASS) |
| 2024 | +0.5% → **−0.0%** | 0.498 → 0.502 | unchanged (PASS) |
| 2025 | +6.4% → **+6.1%** | 0.359 → 0.353 | unchanged (PASS) |

Structurally correct (rule 1) and nudges every over-priced year toward actual
with **no fit regression** (dispatch essentially identical — ST_GAS −63 GWh /
CC +35 GWh in 2023, <0.1% of load), but the effect is **marginal** and the
determination stays **NOT-YET**: the hydro I made eligible sits in East/NYCA,
whereas the dominant 2023 residual is the **downstate SENY/NYC-30min** reserve
tail, which has no hydro. This closes the "East-10min" half of the named gap
(nyiso-68 root cause) but not the SENY-30min half. Registered
`2026-07-22-nyiso-69-hydro-reserve` as a candidate (kept default-off + nyiso-68
as keeper — a marginal, verdict-unchanged gain is better staged than promoted
into keeper churn; the flag is validated-correct and stays for the combined run).

**Named step 2 (the dominant 2023 lever):** SCR/EDRP 30-min operating-reserve
**supply** eligibility — the downstate DR already in the fleet (nyiso_scr_edrp,
$500 strike, energy-only today) made eligible for the SENY/NYC-30min reserve
families it can actually locate into. Then re-solve hydro+DR reserve together and
re-gate 2023 (leave-one-year-out within 2023–2025 before promoting a combined
keeper). Blenheim-Gilboa PS (Capital → East-10min, prime-mover PS, excluded from
`build_hydro_fleet`) is the remaining East-side piece, lower priority than the
SENY-30min DR lever.

## 2026-07-22 — nyiso-70 CANDIDATE: lever 3 step 2 (SCR/EDRP 30-min reserve supply, SENY tail) + hydro; C3b 2023 CLOSES, C3a/C3c improve, determination unchanged

Executed the named step 2. Added `nyiso_scr_edrp_reserve_eligible` (GATED,
default-off): the downstate SCR/EDRP demand response already in the fleet
(`nyiso_scr_edrp`, fuel `demand_response`, $500 strike, **energy-only** until
now) is made eligible to **supply** the 30-min operating reserve, unioned into
the FULL (30-min) reserve class **only** (never the 10-min quick-start class —
SCR responds on a 30-min activation, it is not spinning) and **scoped to the
downstate SENY zones** NYC + Long_Island + Lower_Hudson. SCR is a
NYISO-certified 30-min operating-reserve provider (Ancillary Services Manual §4 /
MST §15), so the union is a grounded market-design input (rules 1/13), **zero new
tunable** — n_residual stays 5. Modelled exactly like the hydro union in
`reserve_config._nyiso_design` (mask by fuel + downstate zone, `full_elig |=`);
threaded through `run_calibration{,_full}.py`; unit test
`tests/test_nyiso_reserve_eligibility.py` (covers 30-min-only, downstate-scope,
default-off, and composition with the hydro union — also backfills the
previously-untested hydro flag).

**Combined solve (nyiso-70).** Replayed the nyiso-68 recipe with BOTH lever-3
flags on (`--set nyiso_hydro_reserve_eligible=true`
`--set nyiso_scr_edrp_reserve_eligible=true`), all three years in one bundle
(`results/calibration/nyiso70_scr_edrp_reserve`, rule 16). Binding confirmed
**not** from run_config alone (the prb_overrides-stomp trap) but from the LP:
the flags route through both the solve kwarg and the prb_overrides channel with
the same value, and the price columns move (2023 max |Δ| $221). The added
downstate reserve headroom absorbs the SENY/NYC-30min ORDC over-spike that had
been leaking into the LBMP — **downstate reserve-shortage zone-hours collapse**
(2023 915→177, 2024 696→114, 2025 1215→255) and the >$300 downstate tail drops
every year — while **energy dispatch is essentially unchanged** (largest class
shift ST_GAS ±0.08 TWh ≈ 0.05% of load; C1 fuel-mix PASS, unchanged). The
reserve is held, not dispatched: the per-zone reserve-headroom row trades it
against the $500 strike, so nothing is forced.

Scorecard vs nyiso-68 (`calibration_verdict`, RT load-weighted basis):

| year | C3a mean LMP | C3b NRMSE | C3c >$300 tail |
|---|---|---|---|
| 2023 | +17.8% → **+15.9%** (FAIL) | 0.215 → **0.198 PASS** ✓ | 31h/10h 3.10× → **22h/10h 2.20×** (FAIL) |
| 2024 | +0.9% → −0.7% (PASS) | 0.177 → 0.177 (PASS) | 22h → 10h (PASS) |
| 2025 | +2.8% → +1.6% (PASS) | 0.132 → 0.148 (PASS) | 40h → 27h (PASS) |

C1 PASS · C5a CO₂ 2025 +8.5% CAVEAT (≈ nyiso-68's +8.3%, reserve-inert). **C3b
2023 closes** (C3b now PASS all years); C3a and C3c 2023 both improve materially
(C3c from 3.10× down to 2.20×, just over the 2× band) with **no 2024/2025
regression** — LOYO holds (the mechanism moves every year toward actual; no
cross-fold degradation). **Determination stays NOT-YET**: 2023 C3a (+15.9%) and
C3c (2.20×) still miss. Root cause of the residual: the 2023 C3a **mean-level**
gap is **not** reserve-driven — the entire reserve over-spike is only ~1.6% of
the system mean (38.06 → 37.44 $/MWh), so +15.9% remains after it is fully
absorbed. That is a broad 2023 energy-price **level** issue (offer surface / gas
basis / import pricing), a separate lever from reserve formation.

**Known C7 regression (recorded, not hidden).** The extra reserve supply lets
ST_GAS provide less reserve, so its 2023 **off-peak** dispatch flattens: the C7
diurnal-shape gate for ST_GAS 2023 flips PASS→FAIL (off-peak CV ratio 0.548 →
**0.483**, threshold 0.5). Marginal (0.483 vs 0.5), single-class, confined to the
already-NOT-YET 2023 (2024/2025 ST_GAS C7 PASS at 0.703/0.641). Same underlying
lever as the C3a mean-level gap — the 2023 energy-price-level workstream governs
ST_GAS off-peak dispatch shape and should resolve both.

**Disposition — PROMOTED to keeper (owner-directed 2026-07-22).** Per rule 1 the
keeper is the **most structurally faithful** run, not the one that crosses a
determination threshold — and both nyiso-68 and nyiso-70 are NOT-YET. nyiso-70
adds two real, grounded reserve mechanisms nyiso-68 lacks, closes the load-bearing
C3b 2023, and regresses only the marginal C7 ST_GAS-2023 shape. The owner
authorized the promotion with the C3b-close-for-C7-flip trade explicitly in view.
Swapped the keeper shard `frontend/data/backcast/keepers/NYISO.json` → nyiso-70,
rebuilt `status/NYISO`, generated the bundle's `calibration_attestation.json`
(DOF ledger n_residual **unchanged at 5** — both flags are eligibility unions,
zero tunable) + `legitimacy_diagnostics.json`, re-scored (C6 governance PASS).
The two flags stay **default-off** in `ScenarioConfig`; the keeper recipe enables
them explicitly (the standard keeper-lever pattern, as nyiso-68 does for
`nyiso_scr_edrp`). Named follow-up: the 2023 energy-price-level lever (closes C3a
and the ST_GAS C7 shape together); secondary, Blenheim-Gilboa PS into the dispatch
fleet for East-10min reserve.

## 2026-07-23 — nyiso-70 C3a 2023 residual RE-SCOPED: off-peak downstate-thermal price floor; handoff hypotheses (gas-basis, offer-markup) + 3 more levers ALL refuted; keeper unchanged

Picked up the nyiso-70 handoff (close 2023 C3a +15.9%). **No keeper change** —
this is a diagnostic-only session that conclusively re-scopes the residual. Full
write-up: `results/calibration/FINDING-nyiso-2023-c3a-offpeak-diagnosis-2026-07-23.md`.

**The residual is OFF-PEAK, not broadband.** Shoulder off-peak (hod 0–6) actual RT
$19.62 vs keeper $30.02 (+53%); on-peak +24%; the +15.9% C3a is the overnight
trough. Off-peak price is **uniform across all five zones** → not congestion.

**Five 2023-only A/Bs (`replay_keeper --set`), every one refuting a candidate:**

| lever | off-peak $ | Δ vs keeper | verdict |
|---|--:|--:|---|
| `energy_reserve_coopt=false` | 30.02 | 0.00 | reserve not the driver (confirms the 1.6% note) |
| `cc_intermediate_split=true` | 30.41 | **+0.39** | worse — NYISO `CC_REGULAR` already `econ_high=1.0` < MISO `CC_INTERMEDIATE` 1.08 |
| `gas_plant_monthly_fuel_pricing=false` | 30.02 | 0.00 | per-plant F923 gas not the driver |
| `nyiso_zonal_gas_basis=false` | 33.59 | **+3.57** | worse — zonal basis is net price-*lowering* |
| `reliability_floor=false` | 31.81 | **+1.79** | worse — downstate ST/CT floors supply *cheap* forced energy |

P0-vs-P1 decomposition: the startup markup adds only **+$0.55/MWh** (P0 already
+14.3%) → **not offer-markup** either. Both handoff hypotheses dead.

**What it actually is.** Off-peak price-setter = a **mid-efficiency downstate
CC** (`hr 8.24`, mc ≈ $29.2) because the efficient CC band (HR < 7.5) is
**outage-exhausted** (4,493 MW avail, 90% utilized off-peak — Ravenswood/Athens
etc. on CEMS-verified, settled outage windows). Reliability-floored ST_GAS
(HR 11.5) runs forced but sits *above* clearing. The model already imports MORE
off-peak (2,909 MW) than the measured schedule (2,324 MW) and still floors at
$30, so imports aren't the gap. Reality troughs ~$10 lower on *less* import → its
domestic off-peak marginal is genuinely cheaper.

**Surviving interpretation (labelled hypothesis, not a keeper lever).** With every
input measured/grounded and the efficient fleet legitimately exhausted, the gap is
most consistent with a **price-formation limit of the full-SRMC LP**: real
overnight LBMP is depressed by committed thermal bidding *below* SRMC to avoid
shutdown, which the LP cannot represent. That is a **cross-ISO methodology change**
(a below-SRMC overnight commitment-bid), not a NYISO knob, and would move every
ISO's trough — validate model-wide before any keeper use. It would address C3a and
the C7 ST_GAS off-peak shape together (as the handoff anticipated), but via
commitment bidding, not the named levers. Absent it, the 2023 off-peak residual is
a structural limit; **nyiso-70 holds as the most structurally-faithful NOT-YET
keeper (rule 1).** Do NOT re-chase reserve / CC-econ-ramp / gas-basis / reliability
floor for C3a 2023.

## 2026-07-23 — nyiso-72 KEEPER (owner override): gas-offer net-revenue margin — pre-registered refutation NOT met (C3b degrades all 3 years), promoted on rule-1 structural fidelity

Charter rollout of the `gas_offer_net_revenue_margin` mechanism (NEISO keeper
`neiso-61`) to NYISO. **Identification already landed** (branch
`claude/gas-offer-net-revenue-isos-1px5vg`, merged): NYISO `phys_*` keys on the
identifiable gas classes of `_NYISO_OFFER_CURVE` (cited to the measured
`nyiso_campd_marginal_hr_summary.csv` p50s) + anchor **3.9046 $/MMBtu**
(`GAS_OFFER_MARGIN_ANCHOR_BY_ISO`, mean of the 2023–2025 delivered-gas overlay
3.36/2.80/5.56). Default-OFF and byte-inert flag-off.

A/B: same-HEAD `replay_keeper` of the `nyiso-70-scr-edrp` recipe — BASE arm
(flag off) vs MARGIN arm (single delta `gas_offer_margin=true`), full 2023–2025,
RT-scored (`scripts/probes/netrev_margin_ab.py`; bundles `nyiso72_netrev_base` /
`nyiso72_netrev_margin`). **Structural check confirmed:** offers reduce EXACTLY
to the registered multipliers at anchor gas (`mc += markup_hr × (anchor −
fuel(t))`, zero at `fuel==anchor`); the only change is the markup gas-elasticity
1→0. Zero fitted scalars (markup LEVELS = registered surface; anchor = measured
delivered-gas mean; **n_residual UNCHANGED at 5**). 404–412 gas tranches
compressed (median fixed margin 6.04 $/MWh). BASE reproduces the nyiso-70 keeper
**byte-identically** (system-price maxΔ 0.0000 all years — drift control +
flag-off inertness confirmed).

| year | gas vs anchor | C3a base→margin | C3b dur-NRMSE base→margin |
|---|---|---|---|
| 2023 | 3.36 (< anchor, firm)     | +18.1 → +20.6 % | 0.5086 → **0.5260 (worse)** |
| 2024 | 2.80 (≪ anchor, firm)     | +1.0 → +3.6 %   | 0.3573 → **0.3781 (worse)** |
| 2025 | 5.56 (≫ anchor, compress) | +5.5 → +1.7 %   | 0.6155 → **0.6385 (worse)** |

**Verdict: by the pre-registered charter criteria this is a REJECT** — the bar is
"MARGIN C3b ≤ BASE C3b EVERY year" and C3b degrades in **all three** years (more
decisively than CAISO `caiso-112`, rejected the same day on 2/3). C3a leaves the
±10 % band further in the already-failing 2023 (below-anchor firm on top of the
known 2023 downstate-thermal energy-LEVEL residual); 2024 worsens in band; only
2025 improves (above-anchor compression). The two-sided mechanism works exactly
as designed — it is simply the wrong direction for NYISO's in-sample residual,
whose dominant miss is the 2023 energy LEVEL, not the offer form.

**Promoted anyway as the NYISO keeper on EXPLICIT OWNER OVERRIDE (2026-07-23),
rule 1 (most structurally faithful offer form).** The margin form is the real
market's offer construction ($ net-revenue start/no-load/scarcity hurdles held
across gas moves; the multiplicative markup scales with the fuel bill,
unidentified in the homogeneous 2023–25 window and refuted by the 2022 NEISO
rotation). **Consistent with the final CAISO decision:** CAISO's A/B `caiso-112`
also degraded, yet CAISO was ADOPTED the same day on the same owner directive /
rule 1 (`origin/main` 681c6de; keeper `2026-07-23-caiso-netrev-margin-keeper`) —
the net-revenue margin is now the go-forward offer form across ISOs. The owner
accepted the in-sample shape cost on the mechanism's expected **out-of-sample**
generalization advantage — which is **UNTESTED for NYISO** (2022 holdout NOT
touched: no calibration-complete marker) and is the open validation item.
Determination **NOT-YET** (as was nyiso-70), deciding criteria the unchanged
2023 C3a/C3b/C3c energy-LEVEL misses; DOF ledger +1 grounded (non-residual)
entry, n_residual still 5; C6 governance PASS; fuel-mix/volume unchanged.
**NO residual tuning taken (rule 1 / pre-registered refutation — the mechanism
was not adjusted to rescue the shape).** Both A/B arms registered on the
dashboard; keeper = `2026-07-23-nyiso-72-netrev-margin`.

Next number: nyiso-73.

## 2026-07-24 — nyiso-73 REJECTED probe: the ISO-neutral gas commitment bridge (ERCOT-63) is near-inert on the C3a 2023 off-peak trough; the prior findings' "only forward lever" is BUILT, TESTED, closed; keeper unchanged

Picked up the `claude/nyiso-backcast-c3a-2023` handoff (close the dominant open
miss, the 2023 C3a OFF-PEAK trough +58.7% on nyiso-72, model floors overnight
LBMP at ~$31 where reality troughs ~$19.6). **No keeper change** — diagnostic-only.
Full write-up: `results/calibration/FINDING-nyiso-2023-c3a-gas-bridge-2026-07-24.md`.

**Independently re-verified the miss on nyiso-72** (committed hourlies vs actuals,
shoulder load-weighted): off-peak (hod 0–6) +58.7%, on-peak +27.8%, full-year
+21.4% — off-peak-specific and wider than nyiso-70 (the margin form made 2023
marginally worse). Structural sharpening of the two prior 2026-07-23 findings: an
off-peak-SPECIFIC gap cannot be produced by any hour-symmetric input (gas basis,
HR, offer level, import price all shift every hour ~symmetrically) — so those
handoff-named levers are refuted *structurally*, not just empirically.

**Resolved the prior findings' open lever.** They named a below-SRMC overnight
commitment mechanism as the sole honest forward lever but called it an *unbuilt*
cross-ISO methodology change. It EXISTS: `ercot_gas_commitment_bridge` (ERCOT-63,
`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §7) — the ISO-neutral
CAISO RA bridge internals (`caiso_ra_mustoffer_min_gen`, P0-pattern + startup
economics, physics-gated rule 18) scoped to merchant gas-CC. Routed onto NYISO
2023 as a rule-16 throwaway (`scripts/probes/_nyiso73_gas_bridge_probe.py`,
`min_load_frac` 0.574 = ERCOT-measured LSL/HSL p50 physical proxy; nyiso-72 recipe
byte-faithful via `build_kwargs(meta)`). NEVER registered.

**The bridge fires but is near-inert on the trough.** Floored 6,492 unit-hours /
**0.573 TWh** / 895 bridged gaps (mostly 4–16h) — so NYISO CC *does* cycle off
overnight (the "baseload CC never idles" null is disproved). But the A/B vs the
committed nyiso-72 base:

| 2023 shoulder (lw) | actual | base | bridge | Δ |
|---|--:|--:|--:|--:|
| off-peak trough (hod 0–6) | 19.62 | 31.12 | 30.92 | **−0.20** |
| on-peak (hod 14–19) | 32.12 | 41.03 | 40.26 | −0.78 |
| full year | 30.28 | 36.78 | 36.34 | −0.44 |
| median daily spread | 26.39 | 8.72 | 8.08 | **−0.63 (worse)** |

C1 unchanged (CC_REGULAR +0.23 TWh, imports 0.00 annual — PASS-band); C7 ST_GAS
inert (−0.07 TWh). The trough moves −0.20 against an $11.5 gap (+57.6% remains)
and the spread compresses −0.63 — the SAME signature that refuted ERCOT's
price-side markdown.

**Mechanism (why inert here, worked on ERCOT).** In bridged off-peak hours the
floor raises CC_REGULAR +115 MW and displaces **imports** −142 MW (already
repriced to neighbor DA LMPs near the CC band), not a dearer domestic unit — so
the marginal price-setter stays a mid-CC ~$29–31 and the trough LMP holds. A STATE
mechanism (more units online at min-load) cannot fix a PRICE gap: the model's
cheapest available overnight marginal (mid-CC) is genuinely dearer than reality's
(which bids below SRMC). Fraction-independent — 0.35 TWh of non-CC was displaced
yet the marginal held. On ERCOT the bridged CC displaced a *more-expensive*
marginal (trough deepened); NYISO's overnight marginal is already a CC, so
flooring CC exposes nothing cheaper.

**Verdict — REJECT the bridge for NYISO; keeper stays nyiso-72 (rule 1).** The
dominant C3a miss is a **full-SRMC LP price-formation limit**, now confirmed on
both sides: STATE bridge near-inert + spread-compressing (this session), PRICE
markdown cross-ISO refuted. The "only forward lever" is BUILT, TESTED, and does
not close it — the residual is an instance of the cross-ISO overnight-trough
price-formation frontier problem (ERCOT's own trough still open at frontier), a
methodology-lane item requiring a below-SRMC *offer* form that lowers the marginal
bid WITHOUT compressing the spread (unfound across ERCOT + now NYISO), validated
model-wide — NOT a NYISO calibration task. NO residual tuning taken. The ST_GAS/C7
half remains a data-intake blocker (published NYC/LI in-city min-gen requirement),
per `FINDING-nyiso-stgas-underrun-diagnosis-2026-07-23.md`.

Next number: nyiso-74.

---

## 2026-07-24 — Lanes 1 & 2 reopened (owner order): import hour-assignment adjudicated, nuclear "over-run" refuted as a benchmark defect

**No solves run.** Everything below is measured from the nyiso-72 keeper's
committed `hourly/` sidecars and raw source data. Full write-up:
`docs/FINDING-nyiso-import-hour-assignment-and-nuclear-benchmark-2026-07-24.md`.
Next number still **nyiso-74** (none consumed).

**1. `interchange_shaping` — rule-13 FORBIDDEN as a keeper mechanism.**
`run_calibration.py:2402` → `import_nodes.py:746 inject_interchange_shape` →
`envelopes.py:223 measured_interchange_envelope`, which reads the **same-year**
EIA-930 `Total interchange` for the ISO itself, buckets (month × hod), and scales
import-tranche availability by it. It is a measured **outcome** (realized net
flow), not a capability envelope — the capability envelope is the published SIL,
which the model already carries. It returns `None` for a forecast year *by
construction*: there is no forward analogue. Diagnostic-only, never a keeper.
Also moot — see (3), the model already over-imports overnight.

**2. Overnight marginal setter = domestic thermal, NOT an import rung.** hod 0-6,
2023, n=2,555: the import node is pinned **exactly at** a rung cumulative
boundary in **69.7 %** of hours (import not marginal); in the 30.3 % interior
hours the price equals the partially-loaded rung's MC in only 6.3 % of them and
the median price sits **$2.23 BELOW** it (the rung runs on the firm-import floor,
not economics). Per-zone, the price equals *any* rung price in 0.4-0.8 % of
overnight hours. **Rung PRICES are not the C3a lever.**

**3. Cheap-overnight-depth hypothesis REFUTED on measured data.** Measured net
external import (four "SCH -" seams) overnight/evening-peak ratio = **0.806**
(2023) / **0.815** (2024); the model's = **1.278 / 1.334**. The model
**over**-imports overnight by **+523 / +531 MW** and under-imports at evening peak
by −717 / −548 MW. Reality imports *less* overnight, not more. Adding cheap
overnight depth moves away from the measurement — sub-lane closed on evidence.

*But the duration coupling IS defective, on method-correctness grounds (rule 21,
never the residual):* `pi_k = Quantile_DA(1 − P[net_import > L_k])` imposes rank
correlation ~1.0 between depth and price, where measured
`r(net import, DA LBMP)` = **+0.158 / +0.383 / +0.432**; and a distribution-match
carries no hour assignment — the signature is exactly the keeper's ~2 % annual
volume accuracy against 0.474 / 0.488 / 0.395 hourly r. Model overnight/peak
ratio is near-constant (1.28/1.33/1.36) while measurement swings 0.81→0.81→1.18:
the shape is insensitive to the year. Admissible replacement specified
(hour-conditioned/diurnal-block Q-Q, or coupling on the neighbour's own hourly
conditions). **Rule-1 warning: correcting it reduces overnight imports and makes
C3a 2023 WORSE. Build it anyway if built; do not revert on the residual.**

**4. Nuclear refuel outages are NOT missing — the BENCHMARK was wrong.** The
model carries outage structure (6-8 discrete MW levels, min 2,461 / max 3,326 MW,
24.9 % of 2023 hours below 90 % of max). Against **NYISO's own hourly fuel-mix
posting** the model is within **0.3 %** every year: 27.49 vs 27.57 / 26.96 vs
27.05 / 28.38 vs 28.48 TWh. Cause: NYIS EIA-930 codes `NG: NUC` filing gaps as
exact `0.0` — **1,275 h in 2023** (56 days, one 1,179-h block), 390 h 2024, 118 h
2025, worth 3.46 / 1.12 / 0.37 TWh. A 4-unit 3.4 GW baseload fleet cannot be at
0 MW; the NYISO posting never reads 0 and never drops below 1,989 MW. The
reported r-collapse is the same artifact — true r is **0.801 / 0.832 / 0.617**,
not 0.831 / 0.498 / 0.505.

*Gas under-run is REAL* (both benchmarks agree: −5.35 / −4.19 / −1.44 TWh vs the
posting). *Hydro is a real open defect* (+1.20 / +0.96 / **−3.20** TWh, r
0.62/0.58/0.41). *Wind is excellent* (r 0.993+).

**FIX APPLIED (rule 14).** `data/eia930/actuals.py`: new `_ZERO_CODED_GAP_SERIES`
registry (BA → columns whose exact zeros are filing gaps), masked to NaN in
`load_eia_hourly_benchmark` so existing interpolation bridges them. Repaired
totals land within −0.4 / −0.4 / −0.7 % of the NYISO posting (from −13.0 / −4.5 /
−2.0 % raw). Registry holds **NYIS `NG: NUC` only** — audited all BAs; ERCO
`NG: WAT` and ISNE `NG: COL` zeros are physically real and deliberately excluded.
Verified every other ISO byte-identical. **Scoring/reporting only — the LP is
untouched** (the LP-feeding envelope functions were not modified), so **no
re-solve is needed but a RE-SCORE of the nyiso-72 bundle IS owed** (C1/C4);
this session did not re-score. Tests:
`tests/test_eia930_zero_gap.py`, 61/61 file pass.
*Known limit:* the 1,179-h 2023 block interpolates energy correctly but not
shape (r 0.715 vs 0.801 against the posting); curating the NYISO fuel-mix posting
into the clean seam would fix shape — a data-intake task needing authorization.

**5. Where C3a 2023 actually lives.** It is a **trough miss, not a level miss**:
model − DA = **+1.62** $/MWh at evening peak (16-19) but **+7.62** overnight
(0-6), worst +9.66 at hod 2. At the model's own $3.09/MMBtu gas the implied
marginal HR is **13.38 model vs 12.86 actual at peak (4 % — calibrated)** but
**9.97 model vs 7.51 actual overnight (33 %)**. Reality's overnight marginal is
an efficient ~7.5 HR CCGT; the model's is a ~10 HR steam-band unit. This explains
why every refuted A/B failed — markup / per-plant gas / zonal basis / netrev
offer form all shift the *whole* curve, and the peak is already right. **New
named lane (untested, not in the refuted set): the heat-rate basis of the
marginal offer at low load** — incremental vs tranche-average HR for a committed
CC. Couples to C8 (ST_GAS 31.0 %/41.2 % forced, ~658 MW overnight): a forced unit
that is also price-setting is the first thing to check, via D-2 (rule 19 —
reconcile, never stack). Pinned reliability floor NOT touched.

**Keeper unchanged — nyiso-72.** Nothing registered on the dashboard.

---

## 2026-07-25 — the overnight price-setter identified: the hydro monthly-budget dual (nyiso-74)

Full write-up: `docs/FINDING-nyiso-overnight-marginal-is-hydro-water-value-2026-07-25.md`.
**Keeper unchanged — nyiso-72.** Nothing registered on the dashboard (scoping
probe). Next number: **nyiso-75**.

**Task 0 (owed re-score) — CLOSED, verdict UNCHANGED, and structurally it could
not have changed.** The nuclear zero-gap fix does not touch any gate:
`calibration_verdict` reads `bench.e930` only for `coal_cems` / `gas` / `coal` /
`gas_cems_grid` / `gas_cogen_grid`; **C1 takes nuclear from `classFull` on the
EIA-923 basis** (27.525 / 27.073 / 28.408 TWh — already within 0.05-0.07 of
NYISO's own posting), and **C4 scores only the gas and coal families**. Re-scored
the committed bundle before and after: byte-identical criteria. Determination
**NOT-YET**; C1/C2/C4/C6/C7/C8 PASS, C3a/C3b/C3c FAIL 2023, C5a commercial-band
CAVEAT. The corrupt value was DISPLAY-only; `bench.e930.nuclear` repaired
23.998 → 27.457 / 25.858 → 26.955 / 27.953 → 28.273 TWh via the guard-railed
`scripts/regen_nyiso_bench_nuclear.py` (no solve; an input-parity guard proves
every other raw 930 cell already reproduces exactly, so nuclear is the only cell
moved; direction guard forbids removing energy; deterministic gzip, idempotent).

**Lane A as chartered (low-load marginal heat rate) — REFUTED as the dominant
overnight mechanism, with the reason.** Measured from the keeper's `hourly/`
sidecars, `d(class MW)/d(demand)` over hod 0-6 demeaned within (month × hod):
**hydro +0.776 / +0.804 / +0.576** (2023/24/25) against CC_REGULAR +0.21 and
ST_GAS +0.14. Hydro absorbs 58-80 % of the marginal overnight MW. `data/hydro.py`
represents it as a **monthly energy budget** with month-long perfect foresight,
so when interior its optimality condition is `price = λ` — a per-month constant.
The keeper's prices show exactly that: Upstate_West overnight pins to one
cent-exact modal value for 32-86 % of each month's hours (p25=p50=p75 in five
months). The discriminator: the implied marginal heat rate of those modal prices
spans **3.58 → 18.49 (5.2×)** across 2023 while the price stays inside $26-38 and
gas moves 5.7× ($1.77 → $10.02). **A price invariant to a 5.7× move in its
supposed marginal fuel is not set by that fuel.** (The 2026-07-24 "overnight HR
9.97 → a ~10 HR steam unit" reading used the *annual* $3.09 gas price; 9.97 is
just where the middle of a 3.6-18.5 monthly range lands — an averaging artifact.)

This also explains every earlier refuted A/B on this residual — markup, per-plant
gas, zonal basis, the netrev offer form and the ERCOT-63 gas bridge all move the
**thermal** stack, and the trough is not on the thermal stack.

**Why the water value is too high — measured.** Model vs EIA-930 hydro
overnight/evening-peak ratio: **0.464 vs 0.682** (2023), 0.516 vs 0.664 (2024),
0.566 vs 0.569 (2025). The model withholds 462 MW overnight and over-runs the
evening peak by 683 MW in 2023. Real NYISO hydro is Niagara (~2.4 GW) +
St. Lawrence (~0.9 GW) — licensed, largely run-of-river, limited pondage; it
cannot move a month's energy from nights into evening peaks. **The one year whose
hydro shape matches (2025, 0.566 vs 0.569) is the one year C3a passes cleanly.**
Hydro carries no D-2 floor (0.0 % forced, all years), so this is pure LP
economics. Rule-19 enumeration: ST_GAS is floored by exactly ONE mechanism
(`reliability_floor`, 31.0/41.2/27.7 %); hydro by none — an unoccupied slot, not
a second floor.

**nyiso-74 (2023 scoping probe): `hydro_dispatch_envelope=True`, single delta.**
Flag confirmed bound from the LP output (`hydro deliverability envelope on 154
units (evening p95 4394 MW)`), not from run_config.

* hydro overnight 1,970 → **2,269 MW** (measured 2,432); evening peak 4,248 →
  **4,018** (measured 3,565); ratio 0.464 → **0.565**; **hourly r 0.638 → 0.717**.
* **The water value fell in ALL TWELVE months** (−$0.78 to −$5.21, mean −$3.1)
  with hydro deliverability as the only changed input. The trough's price-setter
  is established **experimentally**, not by inference.
* Trough −$0.79, peak +$3.61, **peak-trough spread 12.63 → 17.03 (+$4.40)**.
* Mean LMP 38.23 → 39.47, so **C3a 2023 +18.3 % → +22.2 % — worse**.

**NOT promoted; keeper stays nyiso-72 — and NOT rejected on the residual
(rule 1).** It is not a keeper candidate because it is a single-year scoping
probe (rule 16) and because the *instrument* is the wrong one: a p95 hourly
ceiling bounds the hoarding but leaves the monthly optimization intact (the modal
share collapses 72.4 % → 18.0 % in Jan, so the freed hours hand the margin back
to thermal at a higher price, nearly cancelling the −$3.1 water-value drop). The
mechanism is right, the instrument is loose. It is also the **first NYISO lever
to EXPAND the peak-trough spread** (+$4.40; the gas bridge compressed it −$0.63)
— that signature should be preserved by any successor.

**Named successor lane (needs a charter + owner sign-off):** shorten the hydro
budget period from monthly to **daily / pondage-duration** for run-of-river-
dominated fleets. Pondage volume is a licensed physical parameter, so it
regenerates forward and responds to changed conditions. Under rule 19 it must
**replace or reconcile with** `hydro_dispatch_envelope`, never stack.

**Consequence: the thermal lane is reinstated but demoted.** With hydro capped,
more overnight hours become thermal-set and the trough still does not fall — so
the C3a-2023 overnight residual has TWO components (over-high water value in
hydro-set hours; over-high thermal offer in the rest). The low-load incremental-
HR question is identifiable from measured data — `nyiso_campd_marginal_hr_summary.csv`
carries both bases, and the registered curve uses a deliberate MIXED basis
(`phys_committed = avg_committed_p50` 0.964 for CC_REGULAR, while
`phys_econ_low/high = marg_*_p50` 0.784/0.925; `marg_committed_p50` is 0.632) —
and now has a cleaner test bed.

**Governance note (not adjudicated):** `interchange_shaping` is confirmed
**False** in the keeper, so the 2026-07-24 rule-13 finding has no live exposure.
But `nyiso_import_reconciliation=True` logs "priced import node reconciled to
measured EIA-930 net interchange — annual band [22.98, 23.92] TWh". That is an
annual-level reconcile to a measured realized outcome and is flagged for owner
review; it was not re-adjudicated in this session.

**Probe bundle not retained.** `nyiso-74`'s slim bundle was lost to a branch
reset and was not re-solved (its numbers are all recorded above and in the
FINDING). It reproduces exactly from:
`scripts/replay_keeper.py results/calibration/nyiso72_netrev_margin --out-dir
results/calibration/nyiso74_hydro_envelope --years 2023 --set
hydro_dispatch_envelope=true` (~6 min).

---

## 2026-07-25 — delta-heatmap instrument landed end-to-end; the delta-shape finding's nuclear row WITHDRAWN; file-integrity guard repaired

**No solves run. No scorer, rubric-criterion or keeper change. No probe number
consumed** (the entry above holds nyiso-74; next is **nyiso-75**). Keeper
unchanged — **nyiso-72**. This session ran concurrently with the nyiso-74
hydro-water-value session above and is written after it; where the two overlap,
that entry governs and this one defers.

**1. The instrument is complete and verified in a real browser.** The 2026-07-24
session truncated `scripts/render_calibration_html.py` on main (1,911 → 1 lines,
PR #2866) and never pushed the frontend half at all. Restored the renderer from
the committed patch (`docs/handoffs/restore-render-calibration-html-nonfossilhr.patch`
→ blob `cc5d9ea`, 2,251 lines, exact match) and rebuilt the lost frontend — which
now lives in `docs/codebase-site/js/backcast-runs.js` after the Wave-5C inline-JS
extraction (`c17bad3`); all 13 hunks ported with zero fuzz. Added: a
`decAffine(b,lo,hi)` decoder, payload-driven `nfGroups()`/`nfPanels()`, a
non-fossil branch in `singleSeries()`, a two-optgroup class selector, the
plant selector hidden for non-fossil panels, and a **third canvas** in
`drawCfHeatmap` — *Delta (Model − actual)* — computed in **MW**, never CF%−CF%
(`drawHeat` normalizes each series to its OWN max, so a CF-space difference would
call two dispatches that differ by gigawatts "on target"). Suppressed exactly
where the actual map already is, with the reason NAMED, and a diverging legend
whose centre label says explicitly that white is 0 MW, not missing data.

Verified in Chromium over http on **two ISOs**, 7 cases: delta present and
painted for NYISO hydro / imports, ERCOT nuclear and a fossil class; correctly
suppressed-with-reason for NYISO solar and ERCOT hydro (no 930 leg); and an
**old pre-`nonfossilHr` PJM run still renders its fossil CAMPD delta and shows no
non-fossil optgroup**. Payloads regenerated for `nyiso-72` (2023-2025 only,
rule 22) and `ercot-110` — deterministic and idempotent (re-run, hash-compared).

**2. The delta-shape finding's NUCLEAR row is WITHDRAWN — same defect the
nyiso-74 session repaired in the bench.** `docs/FINDING-nyiso-class-delta-shape-2026-07-24.md`
ranked nuclear #4 at Σ|Δ| 7.46 TWh / **+5.02 TWh net**, citing a 2023 "actual
**Mar 13 + 50 d**" refuel outage the model missed. That window is the
**1,179-hour zero-coded `NG: NUC` filing gap**; the fix (`d13a3f2`) landed 27
minutes before that doc was committed, on a parallel branch, and so was not in
its tree. Regenerating against the repaired benchmark:

| year | model TWh | actual TWh (repaired) | net Δ | as published in the finding |
|---|---|---|---|---|
| 2023 | 27.489 | 27.457 | **+0.03** | 23.998 |
| 2024 | 26.958 | 26.955 | **+0.00** | 25.83 |
| 2025 | 28.381 | 28.273 | **+0.11** | 27.90 |

3-year net is **+0.14 TWh, not +5.02**. Re-running the finding's own ≥5-day
derate detector on the repaired series returns 2023: **Sep 02 + 6 d only** (the
"Mar 13 + 50 d" is gone); 2024 and 2025 reproduce its table unchanged. Nuclear is
closed as a calibration lever — now three independent lines of evidence agree
(NYISO's own fuel-mix posting, the repaired 930, and the derate detector). The
residual hourly r (0.715) is the interpolation's shape loss across the bridged
block, not a model error.

Corrected the doc in place (correction box, struck rank-4 row, §2 withdrawal,
renumbered §7) and repaired the canary that caught it,
`tests/test_nonfossil_hourly.py::test_known_nyiso_signatures` — its nuclear pins
were written against the pre-fix benchmark and were **failing on main** until
now. This is exactly the failure its own docstring predicted. 18/18 pass.

*Not re-done here:* the owed nyiso-72 re-score is **CLOSED by the nyiso-74 entry
above** (verdict unchanged, and structurally it could not have changed — C1 takes
nuclear from `classFull` on the EIA-923 basis and C4 scores only gas/coal). The
values this session derived independently match that session's bench repair
exactly (23.998 → 27.457 / 25.858 → 26.955 / 27.953 → 28.273 TWh).

**3. `file-integrity-guard` was failing OPEN — repaired (`0ea0da4`, on main).**
It reported **SUCCESS** on PR #2866, the very truncation it exists to block. Two
compounding defects, both reproduced locally against the real SHAs:
`base_lines=$(git show … | wc -l || echo 0)` yields the two-line string `"0\n0"`
for any path absent at base (because `wc -l` prints its own `0` even when git
fails, and `|| echo 0` appends a second); and feeding that to `(( ))` raises a
syntax error which, in bash 5.2, **abandons the whole loop** and resumes after it.
The scan therefore stopped at the first ADDED file — `backfill_nonfossil_hourly.py`
sorts before `render_calibration_html.py` — and the 1,911 → 1 shrink was never
examined, while the job exited 0. Fixed with a `git cat-file` helper that returns
a failure rather than a malformed number, explicit ADDED-path skipping,
empty-value guards before every `(( ))`, and a **scanned-vs-expected count so any
future early exit fails CLOSED**. Replaying PR #2866 through the fixed script now
emits `shrank 1911 -> 0 lines` and exits 1.

*Second, unfixed hole (not a code problem):* #2866 was **merged at 03:08:15 while
three other checks were still running** and later reported failure. No workflow
change can prevent that — it needs required-status-checks branch protection.
Flagged for the owner.

**4. Still open from the delta-shape finding (nuclear struck, hydro now owned by
the nyiso-74 lane):** the **solar flat-CF fallback** — NYISO model solar is a flat
block (12 distinct values in 8,760 h, midday/night ratio **1.00**) because
`NYIS NG: SUN` is all zeros → `_eia_hourly_cf_profile` returns `None` → the
`_eia930_cf` fallback reads a NYISO solar row in `eia_generation_profiles.parquet`
that is *itself* flat (1 distinct value; wind on the same path has 428). A flat
24-hour solar CF is physically impossible, so any shaped fallback is strictly more
faithful (rule 1), and it needs no new intake. **Fallback-path defect — wants an
all-six-ISO sweep for other degenerate rows.** Also still open: `other`
anti-correlation (r = −0.15) and oil day-placement.

## 2026-07-26 — nyiso-75: shaped solar fallback (STRUCTURAL FIX, rule 1) — flat NYISO solar repaired from the NEISO donor; all-six-ISO sweep done

Closes rank 4 of `docs/FINDING-nyiso-class-delta-shape-2026-07-24.md` — the last
open, unowned item of that finding. Dashboard:
`2026-07-26-nyiso-75-solar-shape`; bundle `results/calibration/nyiso75_solar_shape`.

**The defect.** EIA-930 NYIS files `NG: SUN` as all zeros, so
`_eia_hourly_cf_profile` returns `None` and NYISO solar falls through to the
EIA-930 generation-distribution parquet — whose NYISO solar row is a **single
repeated value across all 8760 hours**. Flat CF × the 12-step EIA-860 monthly
capacity ramp produced the observed 12-distinct-value block: the model generated
as much solar at 03:00 as at noon (midday/night 1.00).

**The all-six-ISO sweep the finding asked for — one live instance, two latent.**
Across six ISOs × {wind, solar} × 2023–2025, **NYISO solar is the ONLY cell that
both reaches this fallback and is degenerate**; everything else takes an HSL or
per-BA hourly path. Byte-identity confirmed for the other 30 ISO-year-mode cells.
Two *latent, unfixed* defects in the same parquet (unconsumed today, so no keeper
is affected): **MISO and SPP solar rows are UTC-stamped** (diurnal centroid h18.5
/ h19.4 vs h12.6–13.9 for the correctly-clocked ISOs, ~+6 h rotated) — a year
losing its hourly extract would silently inherit a rotated solar day — and
`solar_proxy` is **dead data**, zero code references, itself rotated (h17.3). The
new guard detects *flatness, not rotation*. The NEISO donor is verified
local-clock (h13.1), so the repair does not inherit the rotation.

**The mechanism** (`renewables._donor_shaped_distribution`, gated on a
distinct-value degeneracy test — keyed on the defect, not on NYISO, since this is
a fallback-path defect): rebuild the row from an adjacent same-clock BA (NEISO —
interconnected, both `America/New_York`, EIA-860 solar-fleet latitude 42.5 N vs
42.6 N, and the same 0.15 `RENEWABLE_AVG_CF`), which carries measured diurnal
timing, cloud variability and seasonality on the same weather year; then correct
for the fleets' different EIA-860 tracking mixes (NYISO 30.5 % single-axis vs
NEISO 13.3 %) by the clear-sky POA **ratio** `POA_iso / POA_donor`. The ratio form
is required, not cosmetic: `_clearsky_geometry` omits the longitude/EoT term and
its docstring sanctions only *relative* use, so the offset cancels between the two
ISOs. A phase-aligned roll (geometry used absolutely) was built, tested and
**rejected** — it mis-times the shoulders (zero at h05–06, inflated at h19).

**Level untouched; no residual consulted (rules 1, 13).** The distribution is
renormalized to sum to 1.0, so `derive_cf_profile` still sets the annual mean CF
from `RENEWABLE_AVG_CF` exactly as before — 0.1500 in all three years, zero
clipped hours. Forward-valid: the donor series and the EIA-860 tracking mix both
regenerate for any future year and respond to a changed fleet and weather year.

**Independent validation** against EIA-923 NYIS utility-scale solar monthly
netgen — data never used to build the shape. 2023 monthly-energy share:

| profile | MAE vs EIA-923 | r |
|---|---|---|
| flat (before) | 0.0304 | **−0.043** |
| donor shape only | 0.0076 | 0.977 |
| **shipped fix** | **0.0050** | **0.983** |

NYISO solar 2023 now resolves **4,576 distinct values (was 12)**, peaks **h13
(was h00)**, midday/night **83.9 (was 1.00)**. Browser-verified on the Run
Explorer: the Capacity Factor — Solar heatmap went from a uniform block to a real
solar day (summer-widening daylight band, weather streaks), and the CF
distribution from "every hour in the 80–100 % bin" to a night spike at 0–5 %
(~5,659 h) plus a full tail.

**Scoring — and why C1 is NOT a regression.** C7/C8 PASS, C2/C4 PASS,
C3a/C3b/C3c unchanged-FAIL (the known 2023 energy-LEVEL residual; C3a 2023
+17.9 %, C3b NRMSE 0.216). C1 flips PASS→FAIL on **one knife-edge cell**: 2024
ST_GAS −3.02 TWh against the ±3.0 TWh absolute band. But the fix moved model
ST_GAS by only **−0.056 TWh** (8.1060 → 8.0498, 0.7 % of the class), and the
`nyiso-72` keeper was **already at −2.964** — 0.036 TWh, 1.2 % of the band, inside
the edge. So this is a **pre-existing marginal ST_GAS level miss crossing a hard
threshold, not a regression introduced by the solar shape**. Per rule 1 the
mechanism stays in and the ST_GAS 2024 level residual is the root cause to chase.
(Attribution is measured, not asserted: both bundles resolve the *same* benchmark
hash `eia923-465c3e2cf4a5`, and the per-class 2024 energy delta is
ST_GAS −0.056 / CC_REGULAR +0.079 / import −0.047 TWh — total |Δ| well under
0.2 TWh.)

Determination **NOT-YET** on C6 UNATTESTED (probe bundle carries no governance
attestation; the deciding modelling criteria are unchanged from nyiso-72).

**Open for the owner — keeper/code mismatch.** This fix also changes NYISO solar
in **forecast** mode, and the standing keeper `nyiso-72` was solved on the flat
row, so its dispatch no longer matches what the code now produces. Whether
nyiso-75 supersedes it is a promotion decision left to the owner — nyiso-72 was
itself promoted on an explicit owner override, so `keepers/NYISO.json` was **not**
touched here.

Next number: nyiso-76.
## 2026-07-26 — nyiso-73: keeper re-audit on the guard-corrected CAMPD envelope — RE-TUNE REQUIRED (largest sensitivity of the six); keeper UNCHANGED (nyiso-72)

Charter execution (campd-economic-layup-fix-charter §8). The
nyiso-72-netrev-margin keeper recipe replayed verbatim on the adopted
guard-corrected extract (`2026-07-26-nyiso73-meritguard-a1`, 2023–2025 one
bundle; A0 = the keeper). NYISO booked 46 % of its CC capacity-year as outage —
the worst over-count of the six (neiso-63) — and shows the largest correction:
mean LMP −10 to −16 %. The keeper's worst year flips clean: 2023 C3a +18.3 %
FAIL → −0.4 % PASS, C3b 0.223 FAIL → 0.120 PASS, C3c 21/10 FAIL → 5/10 PASS —
the 2023 over-pricing WAS the phantom outage envelope. 2024–25 over-relieve
(C3a 2025 −11.2 % FAIL; tails 0.25×/0.31× FAIL): the offer margins were
calibrated against the inflated envelope throughout (rule 11). Re-tune in this
lane against the corrected envelope before any further NYISO structural work.
Standing caveat: NYISO has no published outage instrument, so the corrected
extract itself remains UNVERIFIED — this arm measures keeper sensitivity, not
extract correctness. Full numbers:
`results/calibration/RESULTS-neiso65-crossiso-reaudit-2026-07.md`.

## 2026-07-26 — nyiso-75 is a PRE-ADOPTION keeper: the §3c RE-TUNE verdict stands against it

Checked whether the parallel nyiso-76 promotion (PR #2916, merged 2026-07-26)
had already absorbed the guard-corrected CAMPD envelope, which would have closed
the neiso-65 §3c re-tune item. **It had not.** The promoted keeper
`2026-07-26-nyiso-75-solar-shape` records `meta.git_sha af74927`, which does
**not** contain the corrected-extract commit `6a8f285` (2026-07-26 00:36:26 UTC)
— so the bytes were produced against a tree carrying the **pre-adoption**
extracts, and the bundle carries A0 semantics.

**The evidence is `git_sha`, deliberately not `timestamp`.** The parallel
caiso-122 finding (`FINDING-caiso122-c3a-head-regression-2026-07-26.md` §1,
revised) establishes that `meta.timestamp` is a hybrid after any replay:
`scripts/replay_keeper.py` restores the ORIGINAL date and keeps the replay's
time-of-day, so a recorded date can predate the bytes by days. `git_sha` is not
subject to that — `replay_keeper` reads the freshly-written `meta.json` and
overwrites only `timestamp`, leaving `git_sha` as the solve's real basis (it is
in the `_IGNORE` provenance set, never a solve kwarg). caiso-122's other caveat
— that a recorded `git_sha` may resolve to nothing, having been a session-local
commit — does not bite here: `af74927` resolves ("Repair degenerate EIA-930
solar distribution rows from an adjacent BA", 2026-07-26 00:17:47 UTC) and is
reachable from `main`. nyiso-75's `timestamp` (`2026-07-26T00:24:27`) happens to
agree, but is not load-bearing for this conclusion.

Consequence: the §3c verdict is unchanged and still open against the current
keeper — NYISO showed the largest sensitivity of the six ISOs (mean LMP −10 to
−16 %; 2023 flips to PASS on all three price criteria, 2024–25 over-relieve).
The standing caveat also still holds: NYISO has no published outage instrument,
so its corrected extract remains UNVERIFIED, and the re-tune is being driven by
a keeper-sensitivity result rather than by a validated extract.

No solve was run in this session; this entry claims no lane number.

## 2026-07-26 — nyiso-81 KEEPER REINSTATED: reliability-floor re-derivation on the guard-corrected outage extract closes the nyiso-80 drift at its root

The keeper-reinstatement charter executed end-to-end. Branch
`claude/nyiso-floor-rederive-2olvql`; bundle
`results/calibration/nyiso81_floor_rederive`; registered
`2026-07-26-nyiso-81-floor-rederive` and PROMOTED to keeper (the lane had NO
keeper since the 2026-07-26 de-designation).

**Step 1 — the rule-23 re-derivation (source-data trigger, commit cites
`6a8f285`).** The four curated NYC/LI ST_GAS limbs re-derived via
`scripts/data/derive_nyiso_st_reliability_floor.py --no-fetch` — the bespoke
when-available construction those rows cite, NOT the generic
`derive_reliability_coeffs.py`, which the nyiso-76 session measured as
destructive (drops every curated limb, re-arms the R1-disabled NYC CT step).
New levels: NYC persistent 24 h base 0.496→**0.175**, evening-ramp base
0.533→**0.185** (cap still clamped at the 1.0 physical bound ≈38 °C, slope
0.0628/°C); LI persistent base 0.436→**0.262**, ramp base 0.572→**0.350**, cap
knot 37.51 °C/0.815→**37.55 °C/0.882** (the re-derived p97 is now reachable
below the LI max tmax 38.3 °C). Capital_Hudson's legacy `CH_ST_ev` knots left
as-is (evening Pearson r 0.041 on the corrected extract — unidentified; matches
the 2026-07-19 precedent's scope). NYC's own evening r weakened to 0.186 (LI
0.547) — recorded as an open item: if a future re-derivation still shows
r < 0.3, re-adjudicate the `NYC_ST_ev` family's enablement as its own mechanism
decision.

**The basis judgement call (charter §"decide deliberately") — AVAILABLE basis
KEPT**, reasoning in the FINDING doc §4.1 RESOLVED block: derive-on-avail /
apply-on-avail makes the floor's MW target extract-invariant to first order
(the availability definition cancels), so the nyiso-80 drift was a
derive/apply DESYNC, not a basis defect; an installed basis would break the
floor's response to real outages and silently under-place during multi-unit
events. Not a mechanism change — no A/B owed.

**LOYO (rule 22), two levels.** (a) Derivation folds: all three
leave-one-year-out re-derivations reproduce the correction (NYC base_24h folds
0.150–0.231 vs pooled 0.175; LI 0.247–0.291 vs 0.262; slopes/caps stable — no
fold reverses it). (b) Per-year gates vs the same-code control (nyiso-79):
D-1 and D-2 improve in EVERY year; C3b 2025 flips FAIL→PASS with no year
flipping the other way.

**Scorecard (vs the de-designated keeper nyiso-75 / the drifted control
nyiso-79):**

| gate | nyiso-81 | keeper-75 | control-79 |
|---|---|---|---|
| C7 D-1 ST_GAS cv_ratio | **0.835/0.948/0.826** all PASS | 0.542/0.658/0.606 | 0.439/0.489 FAIL /0.547 |
| C8 D-2 ST_GAS forced | **28.9/36.2/25.8 %** (2024 GROUNDED v2.2) | 31.4/41.7/28.2 | 43.0/53.8/40.5 |
| C1 | 13/14, free 9/10 (2023 CC_REGULAR −4.11 FAIL) | 13/14 (2024 ST_GAS −3.02 FAIL) | (2023 CC −9.5, ST +7.9 — far out) |
| C3a | **+4.7/−4.1/−8.4 % all PASS** | +17.8 FAIL/+1.2/−3.2 | −0.9/−9.1/−12.2 |
| C3b | **0.128/0.176/0.185 all PASS** | 0.216 FAIL/0.176/0.170 | 0.120/0.196/0.208 FAIL |
| C3c h>$300 (actual 10/12/42) | 3/0/9 FAIL | 19/6/17 | 3/0/9 FAIL |
| C5a CO₂ | +1.3/+2.0/+8.1 CAVEAT | ≈ same | ≈ same |
| determination | **NOT-YET** | NOT-YET | NOT-YET |

The keeper's sole C1 fail (2024 ST_GAS −3.02) is FIXED (−2.36 PASS); 2023
CC_REGULAR slipped −1.98→−4.11 vs ±2.94 — the known downstate ST/CC mix
boundary (open item 1, the in-city must-run gap), now the lane's dominant C1
item. C3c: the tail is thinner than the keeper's because the corrected extract
removed phantom outage-driven scarcity — nyiso-81's tail is IDENTICAL to the
control's (3/0/9), i.e. a current-main property, not a cost of the
re-derivation; scarcity formation remains the open supporting-tier lane.
`dual_fuel_oil_daily_parity` armed (the one genuine nyiso-76 improvement;
measured, mean-preserving, ~+$0.10/MWh on the 2025 mean).

**Governance.** Attestation seeded from nyiso-75, `build_dof_ledger.py` auto
entries (7) UNION'd with the 9 curated measured/published entries a blind
rebuild drops, + a new measured zero-scalar entry for the armed oil cap:
17 entries / 6 residual. C6 PASS. No out-of-training year touched (NYISO has
no calibration-complete marker). Keeper shard + status part rebuilt
(`build_status.py --iso NYISO`), `audit_keepers.py --iso NYISO` PASS.

## 2026-07-26 — nyiso-82: WINTER-SPREAD re-measured against the reconciled keeper — decisive winter fix, exported summer cost, PROBE (no keeper swap)

The nyiso-76 mechanism `nyiso_iroquois_winter_spread` — built and deliberately
NOT exercised because its documented value (winter −16.0 → −4.4) was measured
against a pre-drift baseline (FINDING-nyiso-ordc-span-reliability-floor §4) —
re-measured as the single-delta A/B the FINDING called for, now that the
reconciled keeper exists: `replay_keeper.py results/calibration/
nyiso81_floor_rederive --set nyiso_iroquois_winter_spread=true`, all three
years, one bundle. Registered `2026-07-26-nyiso-82-winter-spread`
(bundle `results/calibration/nyiso82_winter_spread`). Binding verified from
the LP, not run_config (the prb-stomp trap): max |ΔLBMP| $30–53/MWh, ~99 % of
zone-hours move, mean ΔP DJF +2.3/+6.2/+8.6 $/MWh by year against JJA
−0.3/−1.5/−3.9 — the annual-mean-preserving reallocation working as designed.

**Winter tail (the target): decisively toward actual** (monthly LW vs DA):
Feb-23 −24.1 → **−7.6 %**, Dec-24 −27.1 → **−6.3 %**, Feb-25 −16.8 →
**−5.1 %**. Jan-25 (the polar-vortex month; Transco Z6 NY $97.9/MMBtu
2025-01-17) moves only −18.7 → −15.1 % — same stubbornness as the pre-drift
measurement (−18.4 → −14.0): the Algonquin-citygate ceiling caps the Z2
allocation, so the vortex peak still cannot fully form. C7/C8 HOLD and
improve: D-1 ST_GAS cv_ratio 0.835/0.948/0.826 → **0.884/1.005/1.016** (all
PASS), D-2 forced share 28.9/36.2/25.8 → 28.9/35.9/24.6 % (2024 still
grounded-above-budget v2.2). C1 13/14 free 9/10 unchanged; the sole scored
fail improves 2023 CC_REGULAR −4.11 → −3.67 TWh (band ±2.94, still FAIL).
C3a all-PASS +2.2/−4.6/−7.1 %; C3b all-PASS; C3c 3/0/8 vs 10/12/42
(unchanged — the tail is a current-main property, not this lever's).
Determination NOT-YET (C1 + C3c + C6 unattested-probe), same class as keeper.

**No keeper swap — the session's swap bar (winter gain WITHOUT a
summer/shoulder cost) is not met.** The construction preserves the measured
SOM annual spread exactly, so what winter gains, other months surrender, and
on the reconciled keeper that cost lands on months that are already low:
2024 Jun/Jul/Aug worsen 3–5 pp (Jul −10.2 → −15.0 %) and Feb-24 overshoots
+6.1 → +14.0 %; 2025 Jun/Jul/Aug/Sep/Oct worsen 5–9 pp on the already-low
summer (Jul-25 −15.7 → −20.6 %, Aug-25 −8.9 → −17.6 %) and Dec-25 flips
−3.0 → **+7.5 %** (the same Dec-25 over-raise the pre-drift measurement
documented). 2023 improves nearly across the board (monthly-pct MAE
10.9 → 7.0; 2024 8.2 → 7.9; 2025 8.6 → 8.9). Rule-1 reading for the record:
the winter-concentrated Iroquois premium is real physics and the mechanism is
rule-13-clean (three measured series, no fitted constant); the exported
summer miss is the pre-existing summer under-price (the open C3c
scarcity-formation / NYCA reserve-supply lane) that the flat construction was
silently compensating (rule 14's exact signature). Disposition: PROBE on the
dashboard; **re-exercise this flag as a candidate keeper arm when the summer
scarcity lane moves** — the two mechanisms are complementary, and arming
winter-spread alone just trades a winter miss for a summer one.

## 2026-07-26 — nyiso-83: owner ADJUDICATES the in-city lane open; J/K obligation built, binds hard, and is REFUTED as a floor substitute; C3c closed off the J/K route by a $25/MW ceiling

**Owner adjudication (charter §3 / survey §2): YES, full J/K reopen.** The closed
NYISO C3a "reserve" lever was closed as a *pricing* lever (measured Δ$0.00 on the
2023 trough, nyiso-71); it does not extend to a commitment-obligation reading,
which addresses a different phenomenon. Zone-K ARR retrieval was authorized,
attempted, and **exhausted** → documented-NO.

**Two survey questions closed on primary sources.** (a) The vintage pin needed
**no change**: the three dated LRR versions already on disk show the **v2021
regime spans all of 2023–2025**, in which NYC is 500/1,000 — the values already
modelled; the 625/1,250 raise is a 2026 event. (b) What was actually missing was
**Zone K entirely** — no LI family in `NYISO_RCPF_LOCATIONAL` and none in the
measured #1344 intake — a rule-14 omission of a *published* requirement. (c) The
LI on/off-peak `DATA NEEDED` is closed from the tariff itself, **MST §2.15
Definitions-O** (7 a.m.–11 p.m. EPT, Mon–Fri, ex-NERC holidays) — a calendar
rule, hence rule-13 admissible and forward-regenerating. (d) The ARR table is
**login-walled**: current Manual 12 replaced Tables B.1–B.5 with links and its
Table B.5 now points at `nyiso.com/reports-information`, which reads "Log into
MyNYISO to view the Application of Reliability Rules".

**Built** (`fa9fc78`, default-off, byte-inert, 25 new tests):
`nyiso_li_locational_reserve` (published LI 10-min 120 MW; 30-min 270/540
diurnal; $25/MW curve per ASM §6.8 items 10/15) and
`nyiso_incity_commitment_obligation` (published NYC+LI 10-minute families
re-classed onto an online-gated in-pocket class, steam ∪ fast-start GT).
Rule 19 both ways: hard error against `nyiso_synchronised_reserve`, and the
NYC/LI `ST_GAS` floor limbs are dropped **automatically**
(`drop_obligation_owned_reliability_specs`, 8 limbs) rather than by a
hand-written override that could be forgotten into a stack.

**A/B (2024, probe vs same-HEAD zero-delta control — the environment's
solver/pandas differ from the keeper's recorded ones, so the registered keeper
metrics are not a valid baseline).**

*The gate works.* NYC reserve-dual hours >$0 **6 → 7,003**, mean $0.010 →
$10.96: online-gating takes the locational constraint from essentially never
binding to binding in ~80 % of hours. Idle capacity really had been satisfying
the load-pocket requirement for free.

*C3c does not move — and cannot.* Tail hours >$300: **0 → 0**; dual max only
$43.8. **The published NYC/LI demand curves are $25/MW** (ASM §6.8 items
9/10/14/15), so a J/K family can contribute at most ~$25/MW of scarcity rent
however short the pocket is. **The J/K ladders are structurally incapable of
producing the C3c tail** — a ceiling, not a calibration gap. The tail must come
from the tiers whose published penalties can reach it: NYCA ($750/$775) and East
($775). This CLOSES the load-pocket route to C3c and redirects the lane to
system/East-tier reserve-supply tightness. (2024 is also the weakest C3c test
year — the keeper's own tail is 0 there; 2025, 9 vs 42, is the informative one.)

*The obligation is NOT a substitute for the floor.* ST_GAS **8.710 → 5.810 TWh
(−2.90)** against a 2024 gap already at −3.02, with the displaced energy landing
exactly on `CC_REGULAR` +1.47 / `CT_CHP` +0.68 / `CC_CHP` +0.45 / `CT_PEAKER`
+0.11 (sum +2.90, a clean downstate ST→CC/CT merit substitution). Cause: the
obligation is written on the **pocket**, not on **steam** — its eligible set is
in-pocket steam ∪ fast-start GT (faithful to the instrument), so the LP meets
620 MW of published requirement with the cheapest in-pocket online capacity and
lets the boilers go. Shape nonetheless **improves** (evening/overnight 1.905 →
2.449, the direction acceptance criterion #3 asks for): shape-faithful,
level-insufficient.

**Disposition.** Exactly what the survey flagged as most likely — the published
reserve ladder is not the instrument that drives in-city steam; the real driver
is the non-public Con Edison load-pocket procedure the MMU itself cannot see.
The **rule-19 substitution is refuted** and the floor stays. This is **not** a
rule-1 [R-STRUCT] violation: the mechanism is not rejected because a residual
moved, but because it provably does not act on the class it was required to
replace — replacement was the charter's condition, and it has now been tested.
The published **LI ladder is a separate question** (a standalone rule-14 fix)
and is isolated by its own arm rather than judged through the substitution's
failure.

**Note for any promoter:** the obligation forces energy through a *reserve row*,
not a min-gen floor, so **D-2 does not stamp it**. C8 forced-share falls (the
floor limbs are gone) while real forcing continues un-attributed. Defensible —
co-optimized reserve is not a floor — but it must not be read as a forcing
reduction. Evidence:
`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §§4, 4a.

**Third arm — the published LI ladder ALONE is provably inert, and that is the
proof of the mechanism.** With `nyiso_li_locational_reserve=true` and the
obligation OFF (floor limbs retained), 2024 is unchanged to solver noise: every
class within 0.004 TWh, prices identical, and the Long Island reserve dual
**bit-identical** to control (6 h >$0, max $28.1, vs the obligation arm's
7,003 h). Reason, now demonstrated rather than hypothesised: without the online
gate the LI families are **idle-allowed**, so Zone K's idle capacity meets 120 MW
of 10-min and 270/540 MW of 30-min requirement free, every hour. The clean
decomposition: published ladder alone → inert; + online gate → binds ~80 % of
hours (the entire effect); but reachable price capped at the published $25/MW so
binding never becomes a tail; and the eligible set is the pocket not steam, so
binding never becomes steam commitment. `nyiso_li_locational_reserve` is
therefore a **correct but probe-adjudicated INERT** rule-14 fix — carried
default-off so no successor re-runs it expecting movement.

## 2026-07-27 — nyiso-84: the ASM pin flips the East-tier premise ($40, not $775); the published-spin gate binds massively and moves C3c by ZERO hours — the reserve-tier route to C3c is closed in full

**Keeper: `2026-07-26-nyiso-81-floor-rederive`, UNCHANGED.** Session scope: the
nyiso-83 handoff's redirect of the C3c lane at the NYCA/East tier (model tail
3/0/9 h >$300 vs RT actual 10/12/42). Registered runs (all three years, one
bundle each, vs a same-HEAD zero-delta control):
`2026-07-27-nyiso-84-{control,east-ladder,spin-gate,east-gate}`. Full write-up:
`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §6.

**The pin came first and flipped the premise.** The handoff assumed the two
missing East families (spin_10 330 MW, total_30 1,200 MW — LRR posting rows the
model never carried) sit "in a tier that CAN price to the gate" ($775). Pinned
from the ASM §6.8 itself before coding, as instructed: items 2 and 12 are
**$40/MW** (current May-2026 ASM; $25 in the July-2019 issue — the uplift is
the July-2021 procurement-enhancement package, corroborated in-force for the
training window by the 2023 SOM p. A-132). Only item 7 — the East 10-minute
total already in the model — is $775. The families are added anyway
(`nyiso_east_reserve_families`, rule-14 fix, default-off) and the ladder-only
arm is **bit-identical to control** — the East-tier repeat of nyiso-83 §4b.

**The mechanism arm binds and still cannot form the tail.**
`nyiso_spin_reserve_online` (default-off) generalizes the class-2 online gate
to the PUBLISHED spinning families — nyca_10min_spin (655 MW, **$775**) and
east_10min_spin — on the product-definition driver (spinning = synchronized;
hard-errors vs `nyiso_synchronised_reserve`, rule 19). Gate-only takes the
NYCA spin family from 22/6/66 reserve-dual hours to 652/800/1589; composed with
the ladder, 3,248/3,863/5,525 h (37–63 % of all hours) with real overnight GT
commitment forced (CT_CHP +0.2–0.3 TWh, ev/ng < 1). **C3c: 3/0/9 in every arm,
bit-identical.** Binding grows in breadth, never depth — dual max never exceeds
the control's own ($13.5/$63.4/$177.3): the published curves are shortfall
ramps and modeled synchronized supply never falls deep enough short to climb
them. With nyiso-83's $25 J/K ceiling and the $40 East pins, **no published
reserve demand curve forms the >$300 tail at hourly-LP granularity**. The
residual points at RT-interval (5-minute) shortage pricing the hourly LP
structurally cannot see, plus the 2025 LI steam OOM commitment driver
(carried, not chased, per the handoff).

**nyiso-82 consequence:** its winter-spread disposition waited on C3c
movement; C3c did not move → the winter-spread arm stays unarmed.

**Flag dispositions:** both default-off. The East ladder is
probe-adjudicated inert (same standing as `nyiso_li_locational_reserve`). The
spin gate is requirement-side sound but supply-side quick-start-scoped (real
NYISO spin is substantially online CC/steam governor headroom, which the class
taxonomy excludes) — widening the gated class to ramp-limited online CC/steam
headroom is the prerequisite for any future promotion case, and with C3c
unmoved there is none.

**Collateral repairs shipped this session:** (1) the pinned default cache_key
test on main was failing — fa9fc78's `nyiso_li_locational_reserve` /
`nyiso_incity_commitment_obligation` were never registered in
`_CACHE_KEY_OPTIONAL_FIELDS`; both registered (with the two new nyiso-84
fields), default key restored to `edbc1b103207170a`. (2) `write_derived_solve_inputs`
was called but never imported in `run_calibration_full.py` (a3eb7c0), so every
solve since silently skipped derived-input provenance capture; import added.

## 2026-07-27 — nyiso-85: C3c residual ATTRIBUTED — the tail is sustained, statewide, and blocked by an SRMC roof (no solve)

**No LP was run and the keeper is unchanged** (`2026-07-26-nyiso-81-floor-rederive`).
Scoring-side characterisation of committed actuals + the keeper's committed
hourlies (rule 14), reproducible via `scripts/probes/nyiso85_{tail_anatomy,
zonal_tail_basis,model_vs_tail}.py`. Full write-up:
`docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md` §7.

**The framing nyiso-84 handed forward is REFUTED.** All 64 actual tail hours
decomposed at native 5-minute resolution (raw NYISO zonal RTD LBMP; the rebuilt
11-zone hub reproduces `actual_lmp_hourly_NYISO.parquet` to MAE 0.0014–0.0055
$/MWh, so the decomposition is of the scored quantity itself): **52 SUSTAINED
(81 %) / 10 MIXED / 2 TRANSIENT (3 %)**. 2025 is 95 % sustained, with episodes up
to 7 consecutive hours. There is **no RT-interval-transient ceiling** and
therefore **no scorer-side C3c ceiling note to write** — the gap is reachable by
an hourly LP and is a model gap.

**The tail is statewide, not a load pocket:** median **11 of 11** internal zones
above $300 within the hub-tail hours, top-zone share 10.7–11.6 % vs 9.1 % flat.

**C3c's basis asymmetry flatters the model** (rubric note, no change proposed):
model side = max zonal dual, actual side = 11-zone mean. Like-for-like max-zonal
actual is **69/44/121 h**, not 10/12/42 — the true shortfall is 20–40×, not 3–5×.

**Attribution (§7d).** The model's four mainland zones price *identically* in the
tail hours (uncongested) and **never clear $258 in any of the 26,280 hours of
2023–2025** — annual maxima $134/$174/$255, which is the dual-fuel oil-parity cap
`model/lp/rows.py:211` documents. The mainland is structurally incapable of a
single C3c hour; all of 3/0/9 is Zone K congestion rent. It is **not** load or
timing (2025-06-24 19:00 EDT is the model's #1 load hour *and* an actual tail
hour, priced $205 mainland vs $1,365 actual), **not** dispatch level (model 15.9 GW
fossil vs actual 15.5 GW in the 2025 tail hours), and the LP is **not tight**
(`oil` 0–4 %, `import` 46–49 %, `CT_PEAKER` 49–75 %, `ST_GAS` 54–74 % utilisation;
zero slack ever). NYISO's tail forms *above* SRMC; the model prices *at* SRMC
under a ~$258 roof. The oil-budget dual that can lift price past that roof is a
cold-snap instrument and does not bind in June.

**Task 2 (LI steam OOM) closed as a C3c route.** The tail is **77 % summer**,
**89 % in hours 14–21**, **2 % in light-load hours 22–06**; the OOM driver is
light-load voltage-driven, so it targets the 2 %. No instrument built.

**Task 3 (spin supply widening) reframed, still unbuilt and unarmed.** The
"breadth, never depth" pathology is consistent with the reserve *supply* side
being too narrow — a family binds shallowly in thousands of hours because
modelled synchronized supply sits just short almost always rather than deeply
short occasionally. Widening class-2 to ramp-limited online CC/steam remains the
prerequisite, needs its own charter, and cannot on its own clear a $258 roof.
**Both nyiso-84 flags stay default-off; neither armed in any keeper.**

**Clock bug recorded for reuse:** the committed hourly parquet drops
local-standard Feb 29, so leap-year rows at/after index `(31+28)*24 = 1416` are 24
real hours later than a naive mapping — getting it wrong shifts all of 2024 by a
day (2024-04 corr 0.018 → 1.0000, MAE 9.77 → 0.00 once corrected).

**Open lane (§7g), in priority order:** (1) what NYISO's real summer peak offer
stack looks like above oil parity — the roof itself; (2) hot-hour capability —
the keeper runs `temp_dependent_derate=False` / `gt_ambient_derate=False` while
89 % of the tail is afternoon/evening on the hottest days (note the
`temp_dependent_derate` refutation is **ERCOT-scoped**, rule 24, and does not bind
NYISO); (3) import behaviour on regional heat events. Items 2–3 narrow the
headroom but cannot alone breach the roof.

## 2026-07-27 — nyiso-86: calibration RECONCILED — C1 is a demand-basis wedge plus a CHP miscosting, the interchange shape shares C3c's root cause, and the determination path is two named lanes (no solve)

**No LP was run and the keeper is unchanged** (`2026-07-26-nyiso-81-floor-rederive`,
NOT-YET). Adjudication session: classify every known defect as gated-failing /
ungated-but-wrong / by-construction, and state what a calibration-complete
determination actually requires. Scoring-side only (committed sidecars, bench
parts, EIA-930/pal/923 actuals, one `run_year(fleet_only=True)` fleet rebuild
for a heat-rate audit). Full write-up:
`docs/FINDING-nyiso-calibration-reconciliation-2026-07-27.md`.

**C1 2023 CC_REGULAR −4.11 TWh is NOT a vintage artifact and mostly NOT a
dispatch defect.** The model serves the EIA-930 NYIS Demand basis — verified
identical to NYISO's own pal zonal metered load (147.05 vs 147.04 TWh, monthly
±0.01) — with a lossless LP, while C1 scores against plant-metered EIA-923 +
tie-metered imports (150.11 TWh in 2023). The **+2.1–2.9 %-of-load basis wedge
(+3.06/+4.43 TWh in 2023/24) exceeds C1's entire ±2.0 %-of-load band** and is
absorbed ~100 % by the only free family (gas: −3.16/−4.53), landing on the
marginal class. 2024 passed only because the wedge split across two classes.
The registered instrument exists and is off: `td_loss_factor`
(scenarios.py:4412, keeper 0.0). The residual ~1 TWh of the 2023 cell is
within-gas misallocation: CC_CHP +1.87 over on steam-credited heat rates —
the fleet audit finds **27.8 % of NYISO CHP capacity at physically impossible
power-only HRs** (min 3.82; 209 MW @ 4.84, 325 MW @ 5.16) with NYISO absent
from `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` — while CT/ST_CHP under-run with
no steam-host floor (`thermal_tranches_NYISO.csv` predates WP-3; most
`chp_pmin_cf` are 0; `chp_steam_floor_p25` unarmed).

**Interchange r ≈ 0.40 decomposed: the monthly pin supplies ALL of it.**
Within-month hourly r is 0.01/0.13/0.21 (mean of 12 monthly r's); the 2023
diurnal profile is INVERTED (r −0.43: model imports 3,400–3,500 MW overnight,
2,090–2,140 at the evening peak; actual is mildly load-following). Cause is
the C3c root cause seen from the seam: the model's internal diurnal price
swing is **$7.4/$8.2/$16.5** hod-max-to-min against the real NYISO DA's
**$22.5/$25.1/$43.3** (PJM: $23.5/$27.9/$41.2), so the hub-priced seam spread
inverts at the peak (−$2…−$3) and the LP buys its pinned monthly quota
overnight — the real NYISO−PJM DA spread never inverts. Secondary: the
4,350 MW `NYISO_simultaneous_import` planning cap is exceeded by the measured
schedule in 287/314/145 h/yr (max 5,929 MW) — a rule-14 reconcile item.
**Coupling recorded:** fixing import shape before the §7g-1 roof is
rule-14-backwards (peak imports depress peak duals; the current peak-starved
allocation silently flatters C3c).

**Small classes adjudicated:** CT_PEAKER = correctly-windowed floor with
boxcar edges (model ~0 MW off-window vs a real 58→659 MW smooth ramp) —
cosmetic, ungated, would score grounded even if material. CT_CHP/ST_CHP
profile_r (0.13–0.73) is a DEGENERATE statistic on near-flat host-driven
actual profiles (off-peak CV 0.006–0.114) — do not chase r; the level defects
are the §4.2 pair above. Nuclear hourly r (0.56–0.82), wind/solar r = 1.0,
hydro and import levels: by construction (pinned), never quotable as skill.
2025 hydro −3.06 TWh is a preliminary-vintage artifact in the budget input,
self-healing at the final vintage.

**Determination:** still NOT-YET; no ledger path exists around either FAIL
(C3c is a proven model gap per nyiso-85 §7b; C1 is fixable and should be
fixed, not ledgered). Realistic target = CALIBRATED-WITH-CAVEATS (2025 SKIPs
cap it), blocked by exactly two lanes: **nyiso-87** (C1 closure:
td_loss_factor + CHP HR/floor pair, joint probes, LOYO, full-years keeper;
watch C5a 2025 +8.1 % → +10 % edge) and **§7g-1** (summer-peak offer
formation above oil parity — the long pole, now also carrying the interchange
shape payoff; the internal price swing must ~triple before the roof matters).
SIL reconcile rides along small. Nothing registered on the dashboard (no run).

---

## 2026-07-27 — nyiso-87: the h14-21 must-run replaced by min-run commitment (C1 CLOSES)

**Owner directive (2026-07-27), executed this session:** the h14-21 peak-hour
must-run is INACCURATE — turn it off; real NYISO gas runs through the
belly/peak because of RA commitment, AS provision and economic must-run with
MINIMUM RUN DURATIONS, so replace the windowed floors with commitment physics
and try increasing min-run. "Every floor we have added was a compensation for
this missing commitment drag."

**Headline: C1 — NYISO's load-bearing FAIL — CLOSES on commitment physics,
with `td_loss_factor` still 0.0.** The 2023 CC_REGULAR cell walks the arms
−4.11 (control) → −3.32 (A) → −3.20 (B) → −2.89 (C) → **−2.78 TWh (C-MEAS)**
against a ±2.94 band. That is the opposite of what nyiso-86 §2.1 expected: it
nominated `td_loss_factor` as the instrument, and the cell closed without it,
from re-timing gas the model was already free to dispatch.

**Mechanism.** `nyiso_gas_commitment_bridge` (default off, NYISO-only) — the
third P1-native commitment bridge, sharing the ISO-neutral detector with the
CAISO RA and ERCOT gas-CC legs, run ONCE PER CLASS because the two eligible
classes' measured min-loads differ by >2×. Three separately-gated legs:
physical restart bar, economic bridge on the restart inequality, and a NEW
**minimum-run-duration extension** (`min_run_hours` on the shared detector) —
the owner's named ask, which neither existing bridge had. Scope is rule-18
physics, verified on the rebuilt keeper fleet: CC_REGULAR (22 tranches, 3.14
GW, min-down 4–8 h, $50/MW) and ST_GAS (11, 1.22 GW, 8–12 h, $35/MW) qualify;
CT_PEAKER/CT_CHP (1 h, $20/MW) are unreachable by BOTH legs. D-2 id
`nyiso_gas_commitment_bridge`; D-4 windows declared for both floored classes.

**Measured identification (rule 23), new derive.** NYISO publishes no 60-Day-DAM
equivalent, so `scripts/data/derive_campd_gas_commitment_params.py` reconstructs
the ERCOT LSL/HSL statistic from CAMPD conduct via the WP-3 loading-when-on
construction → CC 0.523, ST_GAS 0.239 (artifact
`campd_gas_commitment_params_NYISO.csv`). The CC value lands within 9 % of
ERCOT's independently published 0.574 — an outside cross-check. Run lengths are
reported capacity-weighted (a min-run floors MW, not unit-count): CC p25/p50/p75
= 11/21/133 h, ST_GAS 3/13/89 h.

**The min-run answer cuts both ways.** The class tables disagree with NYISO's
own conduct in OPPOSITE directions — CC's 5–10 h is BELOW its measured p25 of
11 h (the owner's "increase" is what the data supports), gas steam's 24–48 h is
well ABOVE its measured p50 of 13 h. Arm C-MEAS sets both to the measured p50
and is better than arm C on every gate; its floor segments >24 h collapse
46/55/105 → 8/8/0 while the 16–24 h band grows 256/392/196 → 532/569/412, on
slightly MORE floored volume. The pathological steam over-hold is replaced by
genuine CC commitment blocks.

**The boxcar was hurting the shape it was meant to fix.** The h14-21 floor was
CT_PEAKER's ONLY forcing mechanism (D-2 81.3/86.1/48.3 % → 0.0/0.0/0.0 %), and
removing it improved the class's D-1 in every year: cv_ratio 5.12/4.24/2.37 →
**1.38/1.07/1.15** under C-MEAS, for a class the bridge NEVER floors. Arm D
(floors still on) stays at 4.52/3.51/1.80 — the control on that claim.
CT_PEAKER volume collapses 1.42 → 0.46 TWh vs a 2.26 actual: reported, not
patched; a peaker AS/commitment story is a separate rule-17 charter for the
owner.

**D-2: substitution with LESS total forcing.** 2023 merchant-gas forced energy
4.46 TWh (control) → 4.18 (C): `reliability_floor` gives up CT_PEAKER entirely
plus part of ST_GAS, the bridge id picks up CC_REGULAR — attribution shift, not
new forcing, and the total FALLS while C1 flips to PASS.

**Seam payoff, unwired.** The nyiso-86 §3 defect improves monotonically across
the ladder and converges from both ends: imports hod01-03 3,048 → 2,797
(actual 2,596), hod16-18 2,381 → 2,713 (actual 2,857), within-month r +0.072 →
+0.108. Nothing in the bridge touches the interchange node — §3's causal claim
confirmed by construction. The internal diurnal swing only reaches $8.36 vs the
real $22.5, which is why C3c stays open.

**Arm D — `td_loss_factor` REFUTED, with new corroboration.** nyiso-86 §2.1
deferred the value to a Gold Book cross-check; that cross-check already exists
(`docs/nyiso-td-loss-resolution-2026-06.md`): Table I-2 Note 1 makes NYCA
Annual Energy loss-INCLUSIVE and 2023's 147,050 GWh equals the EIA-930 demand
the model serves to the GWh, so a gross-up double-counts. Run as a labelled
probe anyway: at 0.0251 it flips C1 AND improves C3c more than any other arm
(2025 tail 9h → 18h) — but **C5a breaks, 2025 CO2 +8.1 → +14.2 %**. If the
extra 3.7 TWh were real load, burning it would not push measured-rate CO2 four
points past its band. Independent physical corroboration of the Gold Book. The
best-fitting arm is the wrong answer — the rule-1 case in its purest form.
**Open C1 item:** name a correctly-identified instrument for the wedge
(NYISO-invisible generation / BTM metered at the plant / station service / a
seam boundary — NOT losses).

**Two silent wiring defects found and closed by regression tests.** (1)
`run_energy_solve` has THREE call sites, each owning its own `p1_fleet_prep`
chain; the bridge was wired into two, so the backcast orchestrator — what every
arm and keeper runs — never fired it (`test_p1_prep_wiring.py`). (2) The
demand-threading seam read `td_loss_factor` off a pristine config that does not
carry `prb_overrides`, so a `--set` probe solved on RAW demand while
`run_config.json` recorded it armed — the bundle disagreeing with itself, and a
run that would have read as clean evidence for a conclusion it never tested.
Same defect class caiso-80 fixed for two CAISO demand flags
(`test_threaded_demand_overrides.py`). Both found only by asking why a result
looked too clean.

**Determination: still NOT-YET, now on C3c ALONE** (was C1 + C3c). All six arms
registered: `2026-07-26-nyiso-87-control`, `2026-07-27-nyiso-87-arm-floors`,
`-arm-b`, `-arm-c`, `-cmeas-measured`, `-arm-d`. **C-MEAS is the
structurally-faithful candidate** — less forcing, better shape, measured
parameters, C1 closed without touching demand — but is NOT promoted here: it
carries no governance attestation (C6 UNATTESTED caps the determination
regardless), and its C1 margin is thin (~0.16 of ±2.94 TWh). Promotion needs
`calibration_attestation.json` with the DOF ledger by UNION citing the two
`min_load_frac` and two min-run values to the CAMPD artifact. LOYO (rule 22) is
satisfied by construction: no parameter is fitted to any year, all three years
are scored in every bundle, and the direction is consistent in each.

## 2026-07-27 — nyiso-88: the peaker "missing mechanism" is a MEASURED-INPUT error — the model overcharges the fleet's heat rate by more than its whole margin; (c) refuted, no run registered (OOM)

**No LP solved, nothing registered.** A zero-delta keeper replay was started to
regenerate the dispatch a control/arm pair needs; it completed 2023 and was
**OOM-killed during 2024's persist** on this 15 GB container. Every result below
is no-LP, from committed artifacts and measured sources (rule 14), reproducible
via `scripts/probes/nyiso88_{peaker_price_coupling,peaker_economics}.py`. Full
write-up: `docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md`.

**(c) is refuted — and C3c cannot be this class's lever.** Stretching the
keeper's own diurnal price profile to the measured NYISO DA swing (granted free,
no offsetting cost — an upper bound) and re-evaluating CT_PEAKER's *revealed*
offer curve recovers **12.6 / 12.2 / 16.9 %** of the gap. Only 0.14–0.42 TWh of
the gap sits above the model's 90th price percentile against 1.05–1.22 TWh in
the p50–p90 belly; and the full 2,634 MW fleet running every one of 2025's 42
actual tail hours is 0.11 TWh, under 7 % of that year's gap.

**The real fleet is at the money, not uneconomic.** Priced on the KEEPER's own
seam (`nyiso_downstate_ct_gas_daily`: Transco Z6 daily + measured KEDNY/KEDLI
non-firm transport, nyiso-55/G-13) at CAMPD unit-level loaded heat rates, the
pure-CT downstate fleet earns **−$1.39 / +$5.82 / +$3.49 per MWh** over its own
SRMC, ~half its energy either side. Measured Zone J/K premia (+$1.23/+$7.42,
from the raw 5-minute zonal files) move it in the fleet's favour. **A correction
worth recording:** the first pass used the *superseded* statewide EIA firm
city-gate stand-in (`nyiso_downstate_ct_gas_premium`), which is ~$1.5–2.3/MMBtu
dearer and dearest in summer, and produced a spurious "92 % of energy below
SRMC, −$24.16/MWh" that would have sent the session to build direction (a)'s
non-spin product. Directions (a) and (b) both answer a question the measurement
does not pose — and this converges with nyiso-83, which built the in-city
obligation and measured **+0.11 TWh** on CT_PEAKER.

**The actual defect (rule 14 [R-ACCURATE]).** The non-ERCOT fleet carries an
**eGRID plant-average annual** heat rate, identical across every generator of a
plant (E F Barrett's GTs and its 188 MW boilers share 11.076). Against the CAMPD
unit-level **loaded** rate the model overstates by **9.3–15.7 %**, worth
**+$6.48 / +$6.70 / +$7.34 per MWh** at the keeper's own delivered gas — **more
than the entire margin the fleet earns, in every year.** An at-the-money fleet
charged that much too much never clears; no missing mechanism is needed to
explain the 0.46-vs-2.3 TWh collapse. The per-plant errors are source noise in
both directions (Bayswater 21.68 vs 10.58 measured = 2.05×; Barrett 0.74×), so
no multiplier substitutes for the measurement. Honest bound: correcting it lifts
in-merit hour-share 5.1→6.8 / 8.1→11.2 / 12.6→15.4 % against the actual price —
25–33 % relative, not 5×; the remaining residual is day-ahead block commitment
(measured CT run lengths: median 4 h, p90 14 h) and must be re-measured *after*
the input fix, per rule 1.

**Second, independent defect — the bench collapses multi-class plants.**
`render_calibration_html.py` keys `mw_p`/`grp_p` by `plant_code` while iterating
`(plant_code, klass)`, so a plant spanning two model classes is attributed
whole to the **alphabetically-last** class (6 of 6 NYISO cases) and the other
classes' model dispatch is dropped from the payload. Splitting both sides at
CAMPD `unitType`: CT_PEAKER 2.520 → **2.278** TWh (−0.24, so it does *not*
explain this class's gap), but ST_CHP 2.134 → 0.000, ST_GAS 11.912 → 9.686,
CC_REGULAR +2.468, CC_CHP +2.134. Cross-ISO exposure (energy on multi-class
plants ÷ benched fossil): **NYISO 13.9 %, MISO 9.2 %, ERCOT 8.8 %, PJM 2.6 %,
CAISO/NEISO 0.1 %**. Filed as a finding for its own lane — it is a scorer change
touching every ISO's D-1/C-class basis.

**Charter constraints honoured.** No floor re-armed; no windowed limb, boxcar or
CT-scoped `reliability_floor` row proposed. The NYCA/East spin gate and J/K
ladders stay closed and default-off — the at-the-money result removes the reason
to revisit them for this class. Keeper unchanged
(`2026-07-27-nyiso-87-cmeas-measured`).

**Next.** Build `scripts/data/derive_campd_ct_heat_rates.py` (frozen against
residuals, rule 24), wire it ahead of the eGRID plant-average, and register ONE
arm vs a same-HEAD zero-delta control across 2023–2025 in one bundle. Re-score
C1 **and** C5a: the C1 margin is thin (−2.78 of ±2.94 TWh) and 2025 CO2 is
already +7.6 % against +10 %, and this arm adds gas volume.

## 2026-07-27 — nyiso-89: measured CT loaded heat rates land; nyiso-88's bias was 2.5x overstated by a gross/net basis error; heat rate ELIMINATED as the peaker candidate

Built the measured input nyiso-88 §7 called for, wired it ahead of the eGRID
plant-average, and registered ONE arm against a same-HEAD zero-delta control
across 2023–2025 (rules 16 + 12). Keeper **unchanged**
(`2026-07-27-nyiso-87-cmeas-measured`); both new runs are PROBES, UNATTESTED on
C6, determination NOT-YET. Write-up:
`docs/FINDING-nyiso89-ct-heat-rate-2026-07-27.md`.

Registered: `2026-07-27-nyiso-89-control-zerodelta`
(`results/calibration/nyiso89_ctrl_zerodelta`) and
`2026-07-27-nyiso-89-ctmeas-hrloaded` (`results/calibration/nyiso89_hrmeas_ctloaded`).
The control reproduces the keeper exactly (CT_PEAKER 0.459/0.314/1.282 TWh vs
the keeper's 0.46/0.31/1.28; D-1 `profile_r` 0.876/0.928/0.949).

**THE INPUT.** `scripts/data/derive_campd_ct_heat_rates.py` →
`data/raw/_processed-legacy/campd_ct_heat_rates_NYISO.csv` (19 plants,
2,395/2,614 MW = 91.6 % of class capacity; + SOURCES sidecar). Per CAMPD unit,
`heatInput/grossLoad` over hours ≥ 80 % of that unit's own p95 gross load
(≥ 50 qualifying hours, pooled 2023–2025), restricted to `unitType ==
"Combustion turbine"` so a mixed steam/CT facility contributes only its
turbines instead of being dropped as unattributable, generation-weighted to the
plant. Applied under `ScenarioConfig.measured_ct_heat_rates` (default OFF) in
`fleet/eia860.py::_rows_to_generators` AFTER `plant_group` resolves, so only
CT_PEAKER rows are repriced. Rule 13 admissible (a machine's loaded heat rate
regenerates forward and responds to retrofits); rule 24 frozen (re-derives only
on a CAMPD vintage change).

**CORRECTION TO THE PREMISE — nyiso-88 §4 mixed bases.** CAMPD meters **gross**
load; eGRID's heat rate (the model's), the LP's dispatched MW and the
benchmark's own actual (`gross × parasitic_factor`) are all **net**. The dropped
station-service fraction is 1 % on a bare CT but **10.2 % at Bayonne**, the
largest plant in the class and 41 % of its energy (factor 0.898 audited this
session against matching EIA-923/CAMPD unit sets, consistent 0.88–0.92 across
2022–2025 — genuine, not a coverage artifact). Restated on a common net basis
(`scripts/probes/nyiso89_ct_heat_rate_basis.py`): generation-weighted SRMC bias
**+$1.37/+$1.49/+$2.50 per MWh**, not the published +$6.48/+$6.70/+$7.34.
Capacity-weighted the model **undercharges** the class by $0.91–$1.66/MWh.
nyiso-88's headline — "the cost error exceeds the margin the fleet actually
earns, in every year" — **does not survive**: against the measured margin
−$1.39/+$5.82/+$3.49 it is comparable only in 2023.

**A WIRING DEFECT CAUGHT BY EXACT-EQUALITY CHECKING.** The first arm was
**byte-identical** to its control (max abs diff exactly 0.0, every class and
hour of 2023) for a change moving plant heat rates by up to 10.9 MMBtu/MWh.
`scripts/run_calibration.py::run_year` does NOT call
`fleet.assembly.load_or_synthesize_bins` — it inlines its own
`fleet_to_bins(load_fleet_from_csv(...))` for the non-ERCOT per-plant ISOs, and
that call did not forward the flag; since CT_PEAKER plants are binned, the solve
ran on eGRID rates while `run_config.json` recorded the input as ON. This fails
as **"the mechanism is inert"**, not as a crash — reported without the equality
check it would have been a confident, wrong structural finding. Fixed, and
pinned by a test that parses `run_calibration.py` and asserts EVERY
`load_fleet_from_csv` call there forwards the flag. Re-solved arm's P0 pattern
differs from the control's (2023: 20,077 → 19,940 unit-hours floored).

**RESULT — nearly inert, and inconsistent in sign.** CT_PEAKER
0.459→0.443 / 0.314→0.394 / 1.282→1.407 TWh, i.e. **−0.016/+0.080/+0.125**
against gaps of 1.801/1.820/1.729 = **−0.9 % / +4.4 % / +7.2 %** of the gap.
**2023 moves the WRONG WAY** — the capacity-weighted arithmetic showing up in
dispatch: Barrett corrected UP (11.08→16.69 on 281 MW) removes more capacity
from merit than Bayswater (21.68→10.74 on 56 MW) and the in-city fleet add back.
Energy is a near-pure swap with ST_GAS (+0.025/−0.078/−0.087); system totals
unchanged to 3 dp.

**GATES — every criterion verdict IDENTICAL to the control.** C1 PASS (14/14,
free 10/10) both. C2/C3a/C3b/C4/C7/C8 PASS both. C3c FAIL both (2025 6→7 h vs
42). **C1's thin margin, as flagged:** 2023 CC_REGULAR −2.775 → **−2.784** TWh
against ±2.94 — margin 0.165 → 0.156 TWh, ~5 % of remaining headroom, still
PASS but marginally worse. **C5a measured, not assumed** (the brief warned CO2
moves twice — more gas volume, lower CT heat rate): the net is slightly
**POSITIVE**, 2025 system CO2 31.376 → 31.390 Mt vs 29.167 actual, **+7.57 % →
+7.62 %**, still inside the ±10 % commercial band; 2023/2024 nil. Mechanism: the
energy CT_PEAKER gains comes from ST_GAS/CC_REGULAR, which burn at lower heat
rates than a peaker, so volume dominates rate. Shape neutral: CT_PEAKER D-1
`profile_r` 0.876/0.928/0.949 → 0.878/0.914/0.947, `cv_ratio` 1.38/1.07/1.15 →
1.40/1.18/1.15; D-2 forced share 0.0 % throughout.

**VERDICT: the input STAYS, and is NOT promoted as a fix.** It stays on rules 1
and 14 — eGRID's value is a known-defective estimate (non-physical at Bayswater,
wrong-technology at Barrett) and a 0.156 TWh C1 margin instead of 0.165 is a
discovered root cause elsewhere, not grounds to restore a defective input. It is
not a fix because it does not behave like one. **The heat rate is now ELIMINATED
as CT_PEAKER's candidate rather than confirmed as one.**

**Charter constraints honoured.** No floor re-armed; no windowed limb, boxcar or
CT-scoped `reliability_floor` row. NYCA/East spin gate and J/K ladders untouched
and default-off. Years 2023–2025 only; P1 only. The nyiso-88 §5 bench
multi-class collapse is untouched and still needs its own cross-ISO lane.

**Next.** Day-ahead **block commitment** is the remaining candidate, to be judged
against the measured CT run-length distribution (median 4 h, mean 6.5–7.6 h, p90
14 h — `campd_ct_run_lengths_NYISO.csv`) rather than against the volume gap. The
input underneath it is now correct.

**PROMOTED (owner instruction, same session).** The arm became the NYISO keeper:
`2026-07-27-nyiso-89-ctmeas-hrloaded` replaces `2026-07-27-nyiso-87-cmeas-measured`,
on the standing rule that improved structural integrity can carry a keeper even
where gates regress. Determination **NOT-YET** — same determination class and
same sole blocking criterion (C3c) as its predecessor. C6 PASSES on a UNION'd
DOF ledger (19 entries, `n_residual` UNCHANGED at 6 — zero fitted scalars added;
the entry REPLACES a defective estimate rather than adding a degree of freedom).
`calibration-keeper-auditor --iso NYISO`: 0 failures, 0 repairs. **Promoted with
two adverse movements on the record:** C1's thin cell 2023 CC_REGULAR
−2.775 → −2.784 TWh of ±2.94 (margin 0.165 → 0.156), and CT_PEAKER's 2023 level
moving the wrong way. **LOYO on the DERIVED INPUT** (re-derive leaving each year
out, no LP): stable for 16/19 plants (<5 % spread), sign never reversed on any
plant carrying weight (Bayonne 0.5 %, Bayswater 1.0 %, Port Jefferson 2.8 %,
Barrett 6.1 % and never near the eGRID 11.08); NOT stable on the two thin-sampled
barge plants Gowanus (16.5 %) and Narrows (12.8 %), where dropping 2025 reverses
the sign — both sit far out of merit at every fold value so no gate moves. A
minimum-energy screen is the named follow-up, deliberately NOT added post-hoc
(rule 24).

---

## 2026-07-27 — nyiso-90: day-ahead BLOCK COMMITMENT eliminated — the model's CT runs are already the right LENGTH; what is missing is STARTS (2-5x too few)

**Keeper: `2026-07-27-nyiso-89-ctmeas-hrloaded`, UNCHANGED.** Registered runs
(all three years, one bundle each, same HEAD, one ScenarioConfig field apart):
`2026-07-27-nyiso-90-{control-zerodelta,ctblock-minrun}`. Full write-up:
`docs/FINDING-nyiso90-ct-block-commitment-2026-07-27.md`. Parameter choice
pre-registered before derivation: `docs/handoffs/nyiso90-preregistration.md`.

**The charter's premise does not survive the characterization.** The brief
expected "the model's starts are single-hour-ish" and asked that block
commitment be judged against the measured run-length distribution rather than
the volume gap. Judged exactly that way, the model **already reproduces it**:
mean plant-level run length **6.18 / 6.02 / 8.15 h** against a measured
**6.61 / 6.31 / 7.92 h**, with p25 = 3 h and p50 = 5-6 h coinciding on both
sides in every year — and the model's 2025 runs are *longer* than reality's.
This holds at both defensible online thresholds (each plant's own observed
maximum, and a common `max(1 MW, 0.05 x measured CAMPD HSL)` bar), so it is not
a threshold artifact. `scripts/probes/nyiso90_ct_run_lengths.py`.

**What is missing is starts.** Decomposing on `energy = online_hours x
MW_when_on` at the common bar (`nyiso90_ct_gap_decomposition.py`, identity
residual exactly 0): online-hour ratio **0.222 / 0.190 / 0.469**, loading ratio
**0.700 / 0.740 / 0.771**. Since mean run length is right to within 7 %, the
online shortfall is carried almost wholly by run COUNT — 1,138 / 937 / 2,061
model starts against 4,790 / 4,694 / 4,521 measured.

**The arm confirms it inside the solve.** `nyiso_gas_bridge_ct` (default off)
admits CT_PEAKER to the existing bridge, where a 1 h min-down means it can reach
the `min_run_hours` extension and NOTHING else — `RA_BRIDGE_ECON_MIN_DOWN_HOURS`
stays 4.0, so nyiso-87's exclusion of CTs from being *held across a gap* is
preserved (pinned by `test_long_idle_gap_is_never_bridged`). A new per-leg trace
reports the CT leg flooring **12 / 28 / 74 unit-hours** (0.0001/0.0002/0.0007
TWh) against the CC leg's 16,698 / 18,374 / 11,973 — live, with nothing to
extend. Arm vs control: max hourly delta 346 MW (so NOT byte-identical — the
nyiso-89 §4a check was run first), CT_PEAKER **+0.00011 / +0.00009 / +0.00051
TWh = +0.01 / +0.01 / +0.03 % of the gap**, plant-level run lengths and online
hours unchanged.

**Every criterion is identical between arm and control**, both NOT-YET
(UNATTESTED — probes). The two flagged guardrails were measured, not assumed:
**C1's knife edge is untouched** (2023 CC_REGULAR 32.513 vs 35.297 = -2.784 TWh
in both, the 0.156 TWh headroom unchanged; the arm moves CC_REGULAR by 0.00005
TWh), and **C5a 2025 stays +7.6 %** (31.390 vs 29.167 Mt) because there is no
volume to sign. The new `D4_WINDOWS` row for `nyiso_gas_commitment_bridge x
CT_PEAKER` is exercised and PASSES (h0-23, off-window binding 0.0); C7/C8 report
but do not gate the class (1.5/1.4/2.0 % of ISO load, under the 2 % floor).

**Inputs.** `derive_campd_gas_commitment_params.py --ct` extends the frozen
artifact to the CT class (`campd_ct_commitment_params_NYISO.csv`: 80 units,
2,454 MW, 34,024 runs; min_load_frac 0.238 cap-wtd p50, run hours cap-wtd
p25/p50/p75 = 2/4/8 h). Its equally-weighted p50 of 4.0 h reproduces the
independently-derived `campd_ct_run_lengths_NYISO.csv` class fallback exactly.
The default invocation is **byte-identical** (md5-verified) — adding CT to the
default target set would have made mixed steam/turbine plants ambiguous and
silently changed the CC/ST rows the keeper's own bridge reads. min_run = 2 h is
the cap-weighted **p25**, because an observed run bounds a min-run *constraint*
from above. *Recorded inconsistency, not folded in:* the CC/ST legs use
p50_capwtd (21/13 h).

**Verdict: PROBE, rejected as a mechanism, kept default-off.** Not rejected for
worsening the fit — it does not move the fit. Rejected because the phenomenon is
already in the model, so arming it would spend a mechanism, a D-2 row and two
parameters on 0.01-0.03 % of the residual (rules 19/21).

**The lane's question changes** from "why are the runs too short" (answered: they
are not) to **"why does the model start the CT fleet 2-5x less often"**. That
converges with nyiso-88 §3's at-the-money measurement (margin within ±$6/MWh,
50-68 % of measured energy *below* its own SRMC): a marginal fleet has its START
decisions flipped by small errors while run durations, once started, stay right —
exactly the asymmetry measured here. The below-SRMC half is the specific thing a
merit-order LP structurally cannot produce, and it is about the size of the gap.

---

## 2026-07-27 — nyiso-91: the missing CT starts are NOT energy-economic — not hourly, and not as blocks; no arm built

**Keeper: `2026-07-27-nyiso-89-ctmeas-hrloaded`, UNCHANGED.** Registered run:
`2026-07-27-nyiso-91-ctstart-control` (PROBE, `results/calibration/nyiso91_ctrl_zerodelta`,
`--year 2023 2024 2025`, one bundle, sequential). Full write-up:
`docs/FINDING-nyiso91-ct-start-frequency-2026-07-27.md`. The control reproduces
nyiso-90's control **exactly** (2023 CC_REGULAR 32.513 TWh, CT_PEAKER
0.443/0.394/1.407, gas-bridge legs 16,698 / 3,242 unit-hours), so it is a
faithful same-HEAD zero-delta baseline.

**The start deficit IS the level gap.** 98/98/92 % of the class's measured energy
sits inside runs the model never begins — **1.840 / 1.723 / 2.031 TWh** against
nyiso-90's class gap of 1.817/1.740/1.604. `nyiso91_ct_start_economics.py`, 18/18/17
pure-CT plants (nyiso-88 §3 convention), both sides on one common physical bar,
measured side from the BENCH (the only measured series on the model's 8760 clock —
every number here is hour-matched).

**The charter's three-way split, measured.** Of the 3,625/3,689/3,128 missing
starts, priced on the model's own P1 LMP against the plant's own model offer:
**(a) in merit and declined anyway 8.6/10.5/5.8 %**, **(b) out of merit by < $5/MWh
10.4/6.2/9.3 %**, **(c) deep 81.0/83.3/85.0 %** at a median of −$12.95/−$13.94/−$15.44
per MWh. Repricing on the market's own realized DA price only moves (c) to
79.4/71.4/73.4 %; adding the measured NYC/LI locational premium — the most generous
defensible reading — leaves 66.0/57.3/68.7 %.

**Two candidates fall out of the measurement itself.** (i) The model's cheapest CT
tranche is *measured* to bid at bare SRMC — offer intercept recovered from the solve
(a tranche loaded strictly interior is marginal, so its offer equals the zonal LMP)
comes back as VOM to the cent, `median offer − direct = +0.00` in all three years —
so there is **no offer-curve markup to repair**. (ii) The model's downstate zonal
spread already tracks measured (model NYC−LI −2.81/−3.15/−1.80 vs measured
−6.16/−2.83/−0.69), closing locational price formation.

**THE BLOCK TEST refutes start-cost recovery.** Integrating each missed run *whole* —
what a day-ahead commitment actually decides — only **21.7/30.0/36.1 %** are
profitable as blocks at realized DA against bare SRMC (34.3/41.8/39.0 % with the
locational premium), and the pooled margin over ~1.8–2.0 TWh is ≈ zero
(−$6.4M/+$5.2M/−$1.9M = −$3.50/+$3.02/−$0.93 per MWh). The median margin is negative
at **every** position h1–h7 inside the run (2023: −12.8 → −3.5), so there is no
loss-leading-start-then-earn-it-back shape — only 12.6/13.8/18.9 % of blocks have it.
This also reconciles nyiso-88 §3: the fleet's near-zero *annual energy-weighted*
margin is a pooling artifact — a profitable minority of blocks carries a loss-making
majority; at start-decision resolution the fleet is below the money, not at it.

**NO ARM WAS REGISTERED, deliberately.** Every mechanism that would reproduce the
start count is either refuted above (block commitment, start-cost recovery, offer
markup, price formation, locational price) or forbidden by the lane's guardrails
(windowed floor / CT `reliability_floor` limb, start subsidy, fitted start-cost
haircut, residual-tuned adder — rules 13/17). A forecast-vs-realized-price commitment
basis is refuted rather than permitted by the block test: it can change *which* hours
are chosen, not make 2,800 unprofitable blocks profitable. And a cost-basis
correction big enough to close band (c) would need **$1.3–1.5/MMBtu** at the median
and $2.5–3.7/MMBtu at p90 — 53–82 % of the keeper's entire delivered downstate gas
price (NYC $4.54/$4.91/$7.82, LI $3.70/$4.09/$7.25). Arming anything anyway would
spend a mechanism, a D-2 row and parameters on a phenomenon the evidence says it does
not model (rules 1/19/21).

**Gates, re-scored on the control (identical to nyiso-90's).** C1 PASS — **the 2023
CC_REGULAR knife edge is untouched at 32.513 TWh** (−2.784 of a ±2.94 band, 0.156 TWh
headroom), since nothing was armed. C2/C3a/C3b/C4/C7/C8 PASS; C3c FAIL (2023/2024/2025
MODEL MISS); **C5a CAVEAT 2025 +7.6 %** (unchanged — no CT volume was added, so there
was nothing to sign); C6 UNATTESTED (correct for a probe). Determination **NOT-YET**.
C7/C8 report but do not gate CT_PEAKER (1.5/1.4/2.0 % of ISO load, under the 2 % floor;
D-1 profile r 0.878/0.914/0.947, D-2 0.0 % forced).

**Caveat on 2025.** The offer-recovery self-test — the share of model on-hours whose
recovered offer exceeds the LMP — is 0.8 %/6.5 %/**35.5 %**. 2023–24 validate the
recovery cleanly; in 2025 a third of the model's CT on-hours are forced by the floors
and the gas bridge rather than price-driven, so 2025's offer-based bands are
indicative only. The conclusion does not rest on them.

**Probe-layer defect fixed.** `_dispatch_frame` relabels dual-fuel oil-switched
unit-hours as `klass == "oil"`, so filtering `klass == "CT_PEAKER"` silently returns a
short series (8,736 h for plant 2494 in 2023) — which cut the analysable fleet from 18
plants to 9 before it was caught. This probe resolves CT unit ids first and takes all
their rows whatever the hour's fuel label, reindexed onto the full clock. The nyiso-90
probes share the blind spot; harmless there (totals only), fatal here (hour-matched).

**What is left.** One candidate survives: the fleet is committed for **local
reliability, not for energy** — NYISO SCUC load-pocket security commitment inside
NYC / Long Island with BPCG make-whole, which is how a unit rationally runs at an
energy loss on two thirds of its runs. It is NOT the published reserve ladder
(nyiso-83 measured that at +0.11 TWh). Representing it is a data-intake and topology
question (sub-zonal load pockets) before it is a mechanism question, and it needs
owner scoping. Until then CT_PEAKER's level gap is a **diagnosed, unclosed structural
limitation of the five-zone representation**, not an open tuning target.

---

## 2026-07-28 — nyiso-92: the hourly-r decomposition finds hydro; the measured hydro capability envelope becomes the keeper

**Keeper: `2026-07-28-nyiso-92-hydro-envelope` (PROMOTED, owner instruction
in-session; replaces `2026-07-27-nyiso-89-ctmeas-hrloaded`).** Registered runs
(all three years, one bundle each, same HEAD, one mechanism-family apart):
`2026-07-28-nyiso-92-{control,hydro-envelope}`. Full write-up:
`docs/FINDING-nyiso92-hydro-capability-envelope-2026-07-28.md`. Probe:
`scripts/probes/nyiso92_hourly_r_decomposition.py`.

**The charter was dispatch matching ("hourly r for each asset class is pretty
abysmal"), and the decomposition localized the loss before any lever was
touched.** Per-class hourly r is lost at the DAY-PICKING layer (profile r
0.95+ everywhere C7 gates; CC_REGULAR r_day 0.742/0.566/0.534), it collapses
in winter (2024 CC_REGULAR DJF daily r 0.163), and the gas classes' residuals
are POSITIVELY cross-correlated — a common non-fossil driver, not merit-order
shuffling. Attributing against the measured EIA-930 components: **hydro is
the worst-tracking material input** (r_day 0.353/0.405/0.190 on 21–28 TWh)
and carries the exact CAISO parks-at-zero pathology — model 349/405/1,098
hours <100 MW vs measured 0/15/15, hourly p5 274/151/0 MW vs measured
2,072/1,969/1,526, day-to-day std 3× measured (the budget LP's
perfect-foresight hoarding). Nuclear (r_day 0.84 → 0.50/0.51 in 2024–25,
refuel timing) and imports (r_hr 0.40–0.49) are next; both queued, neither
this session's arm. The dramatic cold-snap gas↔oil daily swaps turned out to
be the `dual_fuel_oil_reattribution` RECORDING basis (0.80 TWh relabelled in
Jan-2025 vs 0.031 TWh measured `NG: OIL`; CLI has since pinned it
NEISO-only), not a dispatch error of that size.

**C3c re-anchored while we were in the tail data:** the measured >$300 RT
hours are SUMMER scarcity — 2025 Jun 23–25 alone is 18 of 42 h, July 15 more;
Jan-2024 (storm Gerri) produced ZERO. The winter-fuel lane therefore caps out
at ~4–5 h/yr and the C3c queue leader stays DA virtual depth
(`da_virtual_bids` N=U).

**The arm: `hydro_dispatch_envelope` + `hydro_min_flow_floor`** — the
caiso-72/124 keeper engines, one two-sided measured family (the floor
percentile is the ceiling's mirror; ZERO new fitted scalars, n_residual
stays 6), NYISO levels derived from NYISO's own EIA-930 NG:WAT at solve time
(floor 1.8–2.5 GW by month = 66 % of the 2023 budget — a fleet 72 %-by-MW
run-of-river SHOULD hold most of its energy in the sustained base; ceiling
evening p95 ~4.4 GW). `hydro_ror_split` DELIBERATELY UNARMED: the ORNL-EHA
completion rule is CAISO-reviewed only and would flatten Robert Moses Niagara
(52 % of fleet MW, hybrid label) whose diurnal pattern is treaty-structured —
its own NYISO review is a named follow-up. Rule-19 reconciliation:
`NYISO_HYDRO_TREATY_MIN_FLOW` is dead code in the production path (tests
only); the Q95 floor is the single live hydro floor and covers the ~1.06 GW
treaty-implied minimum.

**RESULT.** The pathology is eliminated (0 hours <100 MW in every year; p5
2,100/1,852/1,376 MW vs measured 2,072/1,969/1,526; day std 8.4/11.3/11.5 vs
measured 6.2/8.4/7.9 GWh; hydro r_day 0.353/0.405/0.190 → 0.517/0.701/0.328)
and **every material gas class's hourly r improves in every year** — TOTAL
fossil 0.861/0.836/0.788 → 0.915/0.896/0.819, CC_REGULAR 0.705/0.583/0.536 →
0.770/0.652/0.573, CC_CHP 0.728/0.700/0.647 → 0.790/0.781/0.676, ST_GAS
0.831/0.876/0.827 → 0.852/0.893/0.839 — with the measured import series'
hourly r rising 0.477/0.493/0.396 → 0.587/0.612/0.454 under a mechanism that
touches no seam wiring. Class energies move <0.5 TWh (a re-timing, not a
level change).

**GATES — promoted with a regression on the record (rules 1/14; owner
standing rule re-affirmed in-session).** C2/C3a/C3b/C4/C6/C7/C8 PASS (C6 on
the UNION'd 20-entry DOF ledger; C8 2024 ST_GAS IMPROVES 32.0 % → 30.9 %
forced, grounded). **C1 FAILS 13/14 (free 9/10):** the 2023 CC_REGULAR
knife-edge cell walks −2.784 → −3.045 TWh of ±2.94 — out by 0.105 TWh — the
exact cell the nyiso-89 note flagged as "one small adverse change from
flipping". The control's PASS was borrowing ~0.26 TWh of phantom overnight CC
that existed only because hydro could park at 0 MW; the accurate input
reveals the true downstate CC deficit rather than creating it, and re-burying
it under false hydro structure is forbidden. **C3c UNCHANGED 3/0/7 h vs
10/12/42** and remains the sole determination blocker. Honest adverse cells:
CT_PEAKER 2024 r_day 0.735 → 0.668; C7 CT_PEAKER 2025 off-peak cv_ratio
0.934 → 0.797 (both ungated, class under the 2 % floor). LOYO (rule 22): no
parameter fitted to any year — each year's bounds derive from that year's own
measured series. `calibration-keeper-auditor --iso NYISO`: 0 failures,
0 repairs. Determination **NOT-YET** — same class and same sole blocker as
every prior NYISO keeper.

**Matrix:** `hydro_dispatch_envelope` N U→K, `hydro_min_flow_floor` N U→K
(citations added); `hydro_ror_split` N stays U with the Niagara-review
caution; NYISO queue extended with the dispatch-matching lane
(nuclear_unit_availability, ror_split review, import shape, reattribution
lineage cleanup).

## 2026-07-28 — nyiso-93: measured unit-availability window family adjudicated INERT (ex-ante, no solve)

Lane task: derive + A/B the measured unit-availability window family
(`unit_outage_short_windows` + `unit_partial_outage_windows`) for NYISO,
matrix cell `U` → tested. **Stopped at the task's own branch point: both
extracts derive to ZERO rows, so the A/B arm was never solved.** The cell is
adjudicated **`I` (inert, ex-ante)**.

**Step 1 — the derive.** Both artifacts built on the frozen constants,
coal-only scope and when-operable baseload guard exactly as shipped (rule 23;
nothing loosened, no gas-CC scope extension):

```
scripts/data/derive_campd_unit_outages.py --iso NYISO --short-windows   --years 2023 2024 2025  -> 0 rows
scripts/data/derive_campd_unit_outages.py --iso NYISO --partial-windows --years 2023 2024 2025  -> 0 rows
```

Coverage: 0 windows/yr, 0 distinct units, 0 MW-days, no class mix, all three
years. Both CSVs are committed with full headers — a valid empty extract, not
a missing file.

**Why — the detector found no COAL, not no windows.** Two independent zeros:
(a) the short/partial guard is CAMPD `primaryFuelInfo ∈ {coal, coal refuse}`,
and NYISO's CAMPD states (NY, NJ) carry **0 coal unit-years** in 2023/2024/
2025 against 276/249/243 pipeline-gas unit-years; (b)
`unit_outage_short_derate_factors` re-filters to `plant_group == "COAL"`, and
the NYISO model fleet is **0.0 MW COAL** in all three years (of 30,253 MW;
78 % gas by capacity). Dated from repo data: the last NY coal MWh is
**Somerset/Kintigh (6082) unit 1, 160.4 GWh in 2020** (376.6 GWh 2019);
2021–22 are zombie CEMS registrations at 0.0 GWh; 2023+ absent entirely.

**Inert, not merely empty.** Both consumers return **0-key** multiplier dicts
for NYISO in every year while the standard ≥5-day overlay returns 39–41 keys
as a live control — so arming both flags derates nothing and the Step-2 arm
would be byte-identical to the keeper by construction. No solve spent; no
dashboard registration (rule 15 governs completed runs, and there is none).

**Rule 25 discipline:** ERCOT's `I` was NOT ported. ERCOT's cell is inert for
a different reason (ERCOT-126: day-scale windows vs an intraday cv gate, on a
fleet that *has* coal); NYISO's verdict is derived from NYISO's own data and
the two are non-transferable in either direction.

**Consequence.** NYISO queue item 5 (§5.5) is closed — the cheapest remaining
item, spent at no cost. C3c is untouched and the queue head remains item 1
(DA virtual depth), aimed where nyiso-92 dated the actual tail (summer RT).
Standing note for the forecast lane: NYISO has **no measured sub-5-day
availability channel at all** — its forced-outage representation rests
entirely on the statistical WEFOR/POF stack plus the standard ≥5-day extract.
Do not attribute a short-duration NYISO tightness miss to fleet availability
without remembering that.

**Matrix:** `unit_outage_short_windows` N `U`→`I` with citation; §5.5 queue
item 5 struck through as closed. Evidence:
`docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md`; probe
`scripts/probes/nyiso93_unit_window_census.py` reproduces every number.

**Rebase addendum (same session, after `origin/main` advanced 28 commits):**
NEISO ran the same lane task in parallel and adjudicated its own cell
`U`→`R` (neiso-69 — rejected on *provenance*, not fit: its single derived
window is unit-mismatched to an EIA-860-excluded Merrimack u2). Both verdicts
are preserved in the merged row, `cells: "IUKKIR"`. The row now carries three
mutually non-transferable negative verdicts for three unrelated causes —
ERCOT `I` (day-scale vs cv gate), NEISO `R` (unit-mismatch provenance), NYISO
`I` (empty population) — and none touches the PJM/MISO `K` cells. The derive
script, `outages.py`, `outage_detect.py` and the CAMPD unit-level extracts are
untouched by those 28 commits, so the NYISO artifacts stand without re-derive.

---

## 2026-07-28 — nyiso-94: DA virtual-bid lever REFUSED ex-ante (no solve, no run)

**Verdict: `da_virtual_bids` × NYISO `U` → `G`.** The charter's own Step-1
branch point fired: NYISO's published DA grain cannot identify a PJM-form
`net(λ)` without a fitted scalar, so **no A/B was solved and no run was
registered** (rule 15 governs completed runs; there is none — same posture as
nyiso-93). **No keeper candidate.** Keeper stays
`2026-07-28-nyiso-92-hydro-envelope` (`results/calibration/nyiso92_hydro_envfloor`),
untouched; its DOF ledger is unchanged at 20 entries / 6 residual because this
session added no parameter.

**The one-line reason.** PJM's mechanism is admissible because PJM publishes
the **submitted** bid curve (`hrl_da_incs_decs`). NYISO publishes only the
**cleared** volume, and publishes it **without a price**. One defect blocks
identification (rule 21 `[R-DOF]`), the other blocks admissibility (rule 13
`[R-MEASURED]`); each is disqualifying alone.

**Step 1 (data intake, no solve).** NYISO MIS P-59 `zonalBidLoad` (26,301 h ×
11 zones, 2023–2025), P-27 `biddata_loadbids`/`_genbids` (3-month lag), P-58B
`pal`, plus the in-repo 2025 SOM. Four findings:

1. **No price axis.** `zonalBidLoad` gives ONE MW per zone-hour for Virtual
   Load and Virtual Supply. The priced P-27 archive cannot separate virtual
   from physical price-capped load — corr 0.667 vs Virtual Load, 0.894 vs Price
   Cap Load, best 0.912 vs their SUM at 0.78× level; the 834 "financial
   signature" sinks (no `Forecast MW`, no `Fixed MW`) partition cleanly from the
   1,350 physical sinks yet total **2.46×** published Virtual Load — a mixture,
   not an identification. The archive also carries superseded submissions
   (`Forecast MW` 2.14× the official Energy Bid Load).
2. **Cleared, not submitted.** The virtual columns reproduce the IMM's published
   **cleared** MW/h (2025 SOM Fig 24) to within 1–2 MW: 1,090/1,275 vs
   1,089/1,275 (2024); 1,052/1,329 vs 1,051/1,327 (2025).
3. **Premise false.** Net virtual is **negative** in the mean hour
   (−230/−186/−277 MW) and only **+580/+293/+917 MW** in the measured RT>$300
   tail (2.5/1.3/3.3 % of RT load) against PJM's +7–11 GW. NYISO's whole DA book
   sits **846–869 MW below RT load** on the annual mean and 827–1,255 MW below
   in the tail hours — corroborated verbatim by the IMM (2025 SOM p.47: DA net
   scheduled load ≈ **96 %** of actual NYCA peak load).
4. **Roof-blocked, re-confirmed on the keeper's committed sidecars** (no
   re-solve): all five **mainland** zones share ONE identical annual max dual
   (149.9/194.5/255.1), **0 hours >$258**, and **zero load-shed slack** in all
   three years. Every model >$300 hour is **Long Island** (3/0/7 = the whole
   C3c count), where measured net virtual is only +211/+145/+249 MW. Demand
   added to a stack with no rung above $255 and GW of headroom cannot make a
   >$300 mainland hour — the nyiso-85 §7d roof, verified rather than re-derived.

**What the data DID produce — the successor lever.** NYISO's virtual market is
a **congestion play, not a depth play**: in the tail hours net virtual is
DEMAND downstate (NYC +264/+373/**+872**, Lower_Hudson +403/+358/+420,
Long_Island +211/+145/+249) and SUPPLY upstate (Capital_Hudson −255/−400/−403,
Upstate_West −43/−183/−221) — verbatim the IMM's own description (2025 SOM
p.21), traders *"purchasing load downstate and selling virtual energy
upstate."* That points at **Thunderstorm Alerts (TSAs)**: NYSRC rules force
NYISO to pre-secure the ConEd system as if the first contingency occurred,
cutting upstate→downstate transfer capability **1–2 GW, RT-only, never in the
DA market** (2025 SOM §D), in **hours 13–21 May–September** — exactly where
nyiso-92 dated the tail — costing **$300–500/MWh** on >26 GW days, with **50 of
1,377 hours carrying 99 %** of the cost. The keeper prices
`Lower_Hudson − Upstate_West` at **$0.5/$0.0/$0.0** and `NYC − Upstate_West` at
$13/$3/$27 in those very hours: the model has essentially **no downstate
congestion where NYISO says congestion is most expensive**. A weather-driven
interface derate is rule-13 admissible (physical availability event,
forward-reproducible — the IMM built its own forecast from public weather
data), and it targets the roof/congestion that blocks C3c rather than the
tightness the roof swallows. Caveats declared: needs a TSA-history intake that
does not exist in-repo, and must be argued on the **RT** side.

**Data deliberately NOT committed.** Cleared virtual volume is a market
*outcome*; parking it under `data/raw/` would leave a re-armable answer key
(rule 26 `[R-DELETE]` in spirit). The probe re-fetches from NYISO's public MIS
instead.

**Rule 25 discipline.** PJM's `K` was not ported and is unaffected (PJM's data
supports the mechanism; NYISO's does not). NEISO stays `U` — whether ISO-NE
publishes a *submitted* virtual curve is untested here.

**DO-NOT-REDO.** Re-opening requires **new evidence of a submitted, priced
NYISO virtual curve**. A price distribution assumed onto the cleared MW is not
new evidence — it is the fitted scalar this finding refused.

**Matrix:** `da_virtual_bids` N `U`→`G` with citation; §5.5 queue item 1 struck
through as closed and a new item 1b (TSA) added as the recommended head.
Evidence: `docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md`;
probe `scripts/probes/nyiso94_da_virtual_identifiability.py` reproduces every
number.

## 2026-07-28 — nyiso-95: TSA downstate transfer derate REFUSED ex-ante (no solve, no run)

**Verdict: new matrix row `tsa_transfer_derate` × NYISO `G`.** The charter's
Step-1 branch point fired — but through a different door than the charter
anticipated. The **event set is fine**; the **derate magnitude** cannot be
identified from published data without a fitted scalar, so **no A/B was solved
and no run was registered** (rule 15 governs completed runs; there is none —
same posture as nyiso-93/94). **No keeper candidate.** Keeper stays
`2026-07-28-nyiso-92-hydro-envelope`
(`results/calibration/nyiso92_hydro_envfloor`), untouched; its DOF ledger is
unchanged at 20 entries / 6 residual because this session added no parameter.

**Two charter premises are factually wrong — both in the model's favour.**

1. *"needs a TSA-history intake that does not exist in-repo"* — **it has existed
   since 2026-07-10.** NYISO MIS **P-35 Real-Time Events**
   (`mis.nyiso.com/public/csv/RealTimeEvents/`), fetched by
   `scripts/fetch_nyiso_operating_events.py`, raw at
   `data/raw/NYISO-AS/requirements/realtime-events/`, clean datatype
   `nyiso-operating-events` (`event_type=thunderstorm_alert`), coverage
   **2018-01 → 2026-06** under the session-logged owner authorization of
   2026-07-10 (`docs/out-of-sample-results-2026-07.md` §1.2). The feed carries
   the alert state directly — start / end / start-of-day-ACTIVE — so **no
   weather classifier is needed at all**. We hold something strictly better than
   the IMM's own instrument: the IMM built a classifier because the DA market
   cannot see the future; a backcast has the realized events.
2. *"The model has no TSA representation"* — **its published, quantified half is
   already armed on the keeper.** The LRR `tsa_reduced_to_zero` rule (a TSA
   zeroes NYC 10T/30T + SENY 30T) flows
   `nyiso_locational_reserve_requirements.csv` →
   `derive_nyiso_reserve_requirements_hourly.py::build_tsa_windows` →
   `NYISO_reserve_requirements_<year>.csv` → `nyiso_dynamic_reserve_requirements`,
   which is **`True` on nyiso-92** (verified in its `run_config.json`).

Reconstructed windows independently corroborate the IMM: 32/30/18 spans =
**187/272/477 TSA-active hours** (2.1/3.1/5.4 % of year), share in **h13–21**
61/55/42 %, share **May–Sep** 75/90/97 %, against the SOM's stated "afternoon
hours from 13 to 21 during the months of May through September."

**Step 1 (data intake, no solve) — the magnitude is the blocker. Four findings.**

1. **NOT in the published limits — measured, well-powered, null.** Declaration-
   instant event study on MIS **P-32** (`NYISO_interface_flows_hourly_<year>.csv.gz`,
   hourly posted limits), `limit[h+1] − limit[h−1]` over all **83** non-carryover
   TSA starts, **all 18 interfaces**: **SPR/DUN-SOUTH +0.0 MW** and **TOTAL EAST
   +0.0 MW** (0 % of events |Δ|>100 MW), **UPNY CONED −23.9 MW** (per-year
   −40.9/−19.5/−4.5, **median exactly 0.0 in all three years**, only 19/17/10 %
   of events negative), and **no interface exceeds |32| MW**. This is **not** a
   power failure: UPNY CONED posts **137–142 distinct values/yr**, hour-over-hour
   std ~80 MW, **max |Δ1h| 835–1,565 MW**, full range 2,440–2,945 MW. A 1–2 GW
   step would be plainly visible. It is absent.
2. **The SOM's "1–2 GW" is not a rating.** It is defined *"relative to
   **day-ahead scheduled levels**"* (2025 SOM p.50) and is a **range, not a
   value**. Picking a point inside it and scoring it on C3c **is** the fitted
   scalar (rule 21 `[R-DOF]`; rule 5 `[R-NO-MAGIC]` — no primary-source citation
   exists for any specific value).
3. **The real constraint is off our boundary (rule 14 misalignment clause,
   verbatim).** The TSA constraint carrying **71 % of July-2025 TSA uplift** is
   the **Lovett-Buchanan 345 kV** line limited under multi-contingency **CE40**,
   with the Pleasant Valley–Wood St.–Millwood/Pleasantville 345 kV lines as
   contingent elements. The IMM **explicitly separates it from the interface**:
   lines #5/#6 *"are not part of the TSA constraint itself but are key components
   of the UPNY-Con Ed interface."* Six lines carry the majority of Zone G→H/I
   flow; our five-zone network collapses that entire boundary into **one** link
   (`Capital_Hudson→Lower_Hudson`, TTC 5,150 — itself Tier-3 seeded). Rule 14
   prefers a *reconciled* real input over a guess, but reconciliation needs the
   line rating + its OTDF for the G→H/I transfer under CE40 + base-case loading:
   **NYISO publishes none of the three at that grain, and none is in-repo.**
4. **Even the IMM has no magnitude model.** Appendix III.J is a logistic
   regression on six ERA5 variables (CAPE, K-Index, Lifted Index, RH-500, V-500,
   VV-850), trained 2023–2024, AUC > 0.93 on 2025 — it predicts **P(occurrence)**,
   a binary. The congestion cost is then measured **ex post** from realized
   shadow prices. There is no published magnitude to adopt.

**What the data DID produce — a validation target, never an input.** TSA has a
real, statistically strong **flow** response. Difference-in-differences at the
declaration instant (`flow[h+1] − flow[h−1]`, net of the same 2-hour drift at
the same hour-of-day and month on TSA-free days): **UPNY CONED −57 (z −0.65) /
−412 (z −5.81) / −326 (z −3.87) MW**; **SPR/DUN-SOUTH −36 (z −0.57) / −330
(z −5.25) / −279 (z −4.40) MW**; TOTAL EAST −80/−205/−235; **CENTRAL EAST as a
clean placebo** (−27/−25/−143, mostly n.s.) — the effect is localized downstate,
the signature is right. Two consequences: (a) realized flow is a market
**outcome** that already embeds the dispatch response, so rule 13 `[R-MEASURED]`
forbids it as an input (same class as pinning a unit to observed CEMS); (b) the
**physical** reduction is **~280–410 MW** in 2024–25 and ~zero in 2023 — about a
**quarter of the IMM's low end** — which, read with the SOM's own "relative to
day-ahead scheduled levels", means the 1–2 GW is predominantly the **DA-vs-RT
schedule gap**, not a capability cut.

**A second, independent structural blocker.** The model has **no DA/RT split**
— P1 is a single clearing. There is no "day-ahead scheduled level" in our
formulation for a derate to be measured *relative to*, so the mechanism **as the
IMM defines it is not expressible here**, regardless of magnitude. The charter's
instruction to "argue it on the RT side, do not smuggle it in as a DA
constraint" is not available either: our P1 is the only side there is.

**Adjudicated on rule 1 `[R-STRUCT]`, not the residual.** Every route to a MW
number is disqualified: the posted-limit change is null (§1); the IMM's prose is
a range (rule 21/5); the observed flow is an outcome (rule 13); an N-1-1 share of
the link TTC (TTC ÷ 6) is a modelling choice that would be selected on C3c, on
top of a Tier-3 base; and the correct reconciliation (rating × OTDF under CE40)
is unpublished. A mechanism whose sole free parameter must be fitted **cannot
carry a DOF ledger entry**. Spending a three-year LP solve to select that scalar
is exactly what the branch point exists to prevent.

**C3c consequence.** The lane now has **no remaining congestion lever** — item 1
(DA virtual depth) and item 1b (TSA) are both closed on *identification*, not on
fit. §1's null additionally shows the model was **not** missing downstate
tightness that a published derate would have supplied; C3c stays **roof-blocked**
(all five mainland zones on one max dual 149.9/194.5/255.1, 0 h >$258, zero
load-shed slack, every model >$300 hour on Long Island). Queue head moves to
item 2 (CT start-frequency); surviving candidates are all offer/commitment-side
(items 2, 3, 6).

**Data deliberately NOT committed.** Nothing new was intaken — the event set was
already in-repo and already curated. No cleared/realized quantity was parked
under `data/raw/` (rule 26 `[R-DELETE]` in spirit); the probes read committed raw
data and the committed production parser
(`curate_nyiso_reserve_requirements.py::build_events_frame`) only.

**Rule 25 discipline.** Other ISOs stay `.` — TSA is a NYSRC/ConEd-specific
operating rule. Any analogous weather-driven derate elsewhere enters that ISO's
own cell as `U` and derives its own parameters from its own market's data.

**DO-NOT-REDO.** Re-opening requires **one** of: (a) NYISO publishing the
as-enforced TSA constraint set (limiting facility, contingency, MW limit) at
hourly/5-min grain — the open **B1** ask already logged in
`data/raw/NYISO-AS/requirements/README.md`; (b) line ratings **+ OTDFs** for the
Zone G→H/I 345 kV group under the named TSA contingencies, enabling the rule-14
reconciliation; or (c) a DA/RT split in the LP. **Not** new evidence: a point
value taken from the IMM's prose range, or a derate backed out of the observed
LBMP, observed flow, DA–RT spread, or the C3c residual.

**Matrix:** new row `tsa_transfer_derate` (cat `network`) N `G` with citation;
header re-stamped; §5.5 queue item 1b struck through as closed and the queue
head advanced to item 2. Evidence:
`docs/FINDING-nyiso95-tsa-derate-not-identifiable-2026-07-28.md`.

---

## 2026-07-29 — nyiso-96: fast-start amortization REJECTED despite flipping C1 to PASS; the NYISO C3c lane has no remaining buildable lever

**Keeper: `2026-07-28-nyiso-92-hydro-envelope`, UNCHANGED.** Registered runs
(all three years, one bundle each, same HEAD, one mechanism-family apart):
`2026-07-29-nyiso-96-{control-zerodelta,ctamort}`. Full write-up:
`docs/FINDING-nyiso96-ct-start-frequency-2026-07-29.md`. Parameter choice and
predictions pre-registered before the solve:
`docs/handoffs/nyiso96-preregistration.md`.

**STEP-1 characterisation, no LP spent** (`nyiso96_ct_start_characterization.py`,
`nyiso96_ct_offer_reveal.py`, both on the keeper's committed sidecars). The two
discriminating signatures both select the COMMITMENT family over start
economics, in all three years: run lengths already match measured (plant-grain
median 6 h model vs 5 h; mean 6.29/6.26/8.62 vs 6.62/6.40/7.83) so only block
COUNT is short (987/894/2,048 vs 3,737/3,796/3,528); **82–88 % of the missing
online-hours are hours the model prices BELOW the plant's own measured SRMC**;
and the measured below-SRMC energy is spread FLAT — the deepest 10 % of those
hours carry 3.3–6.6 % of it against a 2.5–4.4 % total-energy reference on the
same ranking. Two objections closed rather than assumed: the hub-vs-zonal price
(measured NYC/LI premium from the raw RTD files — **53–66 % of measured CT
energy still clears below its own SRMC at the fleet's own zonal price**, a
model-independent number) and availability (class derated ≤3 %). This
independently reproduces nyiso-90/91 on a different bar and a different keeper.

**A non-surviving reading, recorded so it is not rediscovered.** The per-tranche
capture rate is low (committed 0.05/0.05/0.08, econ 0.29–0.65), which reads as
an offer markup. It is not: the denominator is affordability at the PLANT SRMC
while each tranche carries its own heat-rate multiplier. nyiso-91 §(i) measured
the cheapest CT tranche bidding at bare SRMC (`median offer − direct = +0.00`);
this session does not contradict it and claims no offer-level defect.

**The arm.** `tranche_startup_amortization` + `tranche_startup_measured_runs`
(v3 measured basis on NYISO's OWN `campd_ct_run_lengths_NYISO.csv`: 22 plants +
a pooled 4.0 h class fallback over 34,057 runs; NREL start costs $20/MW CT).
Zero fitted scalars, nothing ported (rule 25), `n_residual` unchanged. Chosen
because it was the last **buildable, un-adjudicated, non-governance-blocked**
cell in the queue — every commitment-side candidate is already closed (J/K
obligation +0.11 TWh nyiso-83; reserve tiers nyiso-84; block commitment
+0.01–0.03 % nyiso-90; windowed floors forbidden by the 2026-07-27 owner
directive and rule 17).

**LIVE first** (the nyiso-89 §4a check): max |Δ| class 1,257/1,253/2,105 MW.

**Result. The arm flips C1 to PASS and is rejected anyway.**
CT_PEAKER on one common bar: 0.323/0.305/1.070 → **0.220/0.188/0.741 TWh**
(−32/−39/−31 %) against a measured 1.880/1.759/2.217; starts 987/894/2,048 →
**719/582/1,453** (−27/−35/−29 %) against 3,737/3,796/3,528, so the start ratio
DEGRADES 3.79x/4.25x/1.72x → **5.20x/6.52x/2.43x**. Median run 6→7/6→5/6→6 vs a
measured 5 — unmoved, as pre-registered, because there was no horizon defect to
correct. **C3c is BIT-UNCHANGED: 3/0/7 both arms** against an actual 10/12/42 —
the lever buys ZERO tail hours on the lane's own target. Displaced energy lands
on CC_REGULAR (+0.284/+0.496/+0.408) and ST_GAS (+0.159/+0.183/+0.175), and that
+0.284 walks the knife-edge cell from **−3.05 to −2.76** inside its ±2.94 band
— the control's ONLY failing C1 cell. Scored: control **C1 FAIL** (13/14 · free
9/10), arm **C1 PASS** (14/14 · free 10/10); C2/C3a/C3b/C4 PASS both; C3c FAIL
both; C6 UNATTESTED (correct for probes); C7/C8 SKIPPED.

**Verdict: REJECTED on rule 1 [R-STRUCT], not on the residual.** This is the
INVERSE of the owner's standing keeper clause — that clause admits structure-up
/ gates-down; this arm is **gates-up / structure-down**. It is not real for this
fleet and the measurement says so: a fleet clearing 53–66 % of its energy below
its own SRMC is not adding a ~$5/MWh start-recovery markup on top of SRMC;
nyiso-91's block test already refuted start-cost recovery (21.7/30.0/36.1 %
profitable whole, median margin negative at every position h1–h7); and the run
lengths were already right. The C1 pass is manufactured by moving energy between
**two classes that are both under-produced** — no class is better represented
afterwards. Banking it would bury the peaker defect a layer deeper. **Owner-
visible:** the arm is a strictly better scorecard than the keeper and is
registered and promotable if the owner prefers the gate — but the §2 peaker
diagnosis would then be a deliberately-accepted misrepresentation, not an open
item.

**Matrix (rule 28b):** `tranche_startup_amortization` NYISO `U` → **`R`**.
**With this the NYISO C3c lane has NO remaining buildable in-model lever.** The
surviving candidate is unchanged from nyiso-91 — NYISO SCUC load-pocket security
commitment with BPCG make-whole — a sub-zonal data-intake and topology question
needing owner scoping before it is a mechanism question.

**Reproducibility note.** The keeper does not replay in a fresh container until
`scripts/data/curate_capacity_deliverability.py` is run: `data/clean/` is
derived and gitignored, and `nyiso_li_lcr_tsl` defaults ON while living only in
`run_config.json` (not `meta.json`), so `--replay-bundle` hard-fails on the
missing Long Island import limit. Environment setup, not a keeper defect.

## 2026-07-29 — nyiso-97: OWNER PROMOTION of nyiso-96 + C3c load-pocket scoping (step 0)

**Session charter:** the C3c sub-zonal load-pocket scoping lane (the lane's only
surviving candidate, per nyiso-91/96). Step 0 put both standing owner questions
via `AskUserQuestion` before any building:

- **(a) Sub-zonal NYC/LI load-pocket topology: AUTHORIZED**, data-first — the
  session proceeds to establish whether the as-enforced Con Edison in-city
  reliability rule is publicly obtainable, and STOPS with no build and no solve
  if it is still MyNYISO login-walled (a pocket requirement backed out of the
  residual is rule 13/21 forbidden).
- **(b) nyiso-96 C1 trade: OWNER TOOK THE GATE.** `2026-07-29-nyiso-96-ctamort`
  is **PROMOTED to keeper** for its C1 PASS (14/14 · free 10/10), explicitly
  accepting the CT_PEAKER 27–39 % degradation. This is the owner-visible call
  FINDING-nyiso96 §5 surfaced; the building session's rule-1 rejection stands
  unedited as the structural adjudication.

**Promotion mechanics (this session):**

- `scripts/gen_nyiso96_attestation.py` builds the C6 attestation the promotion
  requires (rule 21): the nyiso-92 keeper's UNION'd 20-entry ledger carried
  forward + ONE measured entry (`tranche_startup_amortization` on the v3
  measured NYISO run-length basis — NREL start costs already cited, pooled
  CAMPD p50 horizon; zero fitted scalars, **n_residual stays 6**, 21 entries).
- Scorer confirms on the promoted run: C1 PASS 14/14 · free 10/10, C2/C3a/C3b/
  C4/C6/C7/C8 PASS (C8 2024 ST_GAS 30.4 % grounded above budget), **C3c FAIL
  3/0/7 h vs 10/12/42 — bit-unchanged, the SOLE determination blocker.
  DETERMINATION: NOT-YET.**
- `keepers/NYISO.json` promotion note records the trade as a **known,
  deliberately-accepted misrepresentation** (attestation `_open_items (0)`);
  the peaker diagnosis (nyiso-90/91/96 §2) is no longer an open mechanism item
  and may be un-accepted only by the load-pocket lane producing a
  published-primary-source mechanism — never a floor (rule 17; h14-21 windowed
  floors stay OFF by owner directive 2026-07-27).
- **Matrix (rule 28b):** `tranche_startup_amortization` NYISO `R` → **`K`** by
  owner decision, citation updated; header re-stamped (keeper →
  `2026-07-29-nyiso-96-ctamort`, NYISO gates → C3c alone).
- `build_status.py --iso NYISO` rebuilt; `check_mechanism_matrix.py` OK.

The keeper now reflects an owner gate-preference, NOT a claim of superior
structural fidelity over nyiso-92 — that comparison is adjudicated the other
way in the finding, and stays there.

**C3c identification (step 1) follows in this session** — outcome appended
below when reached.

**C3c identification outcome (step 1, same session): LANE CLOSED EX-ANTE, NO
SOLVE.** The as-enforced Con Edison AORR table remains MyNYISO login-walled
(nyiso-83 re-confirmed 2026-07-29; the nysrc.org posting promised by Manual 12
§2.1.5 does not exist). Decisively, a complete PUBLIC 2008-vintage Appendix B
was found this session (October-2017 Manual 12, mirrored at ercot.com) and it
settles the question on CONTENT: every Con Edison in-city commitment row is
qualitative and condition-triggered on TO contingency analysis, with the
operational parameters in unpublished Con Ed SO procedures (SO3-18) — no MW
level, no min-units-per-pocket table, no eligible-unit list exists to derive,
at any vintage. Rule 13's regeneration test fails outright; BPCG/SOM uplift
aggregates are outcomes, not requirements (pinning). **NYISO C3c is recorded
as a DIAGNOSED, UNCLOSED structural limitation of the five-zone
representation** and the lane handed back — per the owner's stop-if-walled
authorization, no build, no topology change, no data intake. Matrix: new row
`scuc_load_pocket_commitment` → NYISO `G` ex-ante; §5.5 C3c queue now EMPTY
(remaining live work: dispatch-matching items 7–10, hygiene item 6). Re-open
conditions and evidence:
`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`.

## 2026-07-29 — nyiso-98 `nuclear_unit_availability`: the queue's defect was a benchmark artifact; the real one closes, all gates PASS

Dispatch-matching lane, matrix §5.5 item 7 (queue head). Registered A/B:
`2026-07-29-nyiso-98-control-zerodelta` + `2026-07-29-nyiso-98-nucavail`,
2023+2024+2025 in one invocation. Pre-registration
`docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md` committed and pushed
**before** the extract was derived and before any solve; finding
`docs/FINDING-nyiso98-nuclear-availability-2026-07-29.md`.

**PREMISE CORRECTION — the queue entry was wrong, and it inverts.** "Nuclear
r_day drops 0.84 → 0.50/0.51 in 2024–25" reproduces exactly on the keeper
(0.839/0.504/0.511) but is scored against EIA-930 `NYIS` `NG: NUC`, which
posts **exactly 0.0 MW** in contiguous blocks — 1,179 h in 2023 (50 all-zero
days), 380 h in 2024, 117 h in 2025. Zeros **in the source parquet**: not NaN,
and not produced by the repo's `_eia_hourly_frame_filled` gap-bridging, which
emits NaN. **Falsified against NRC on all 81 gap days across the three years,
zero survivors** — every one has ≥1 NY reactor at **100 %** of licensed
thermal power (2023-04-14…20: FitzPatrick 100 % + Nine Mile Point 2 100 % =
2,127 MW online against a metered 0.0 MW for all 24 h). Gap-masked, the
ordering **inverts** to **0.446 / 0.833 / 0.534** — 2023 is the WORST year,
not the best, and the stated "2024–25 drop" does not exist. Second artifact,
same cause: nyiso-92's component table reads 2023 nuclear +14.5 %
over-produced (27.49/24.00 TWh); on gap-clean days it is **−2.1 %**. There is
no nuclear level defect. The lane stayed live on the real residual and the
target was re-based onto gap-clean r_day **in the pre-registration, before the
arm existed**.

**SOURCE (rule 13, adjudicated before the derive).** NRC daily Power Reactor
Status selected — public, per-reactor, 365/366-day coverage of all four NY
reactors every year. NYISO outage schedules are CEII; EIA-923 is the level
anchor and cannot see intra-month timing; nuclear is not in CAMPD; EIA-930
`NG: NUC` is forbidden as an input (it is the scored outcome, and it is the
contaminated series). Extract `data/raw/nuclear-availability-NYISO.csv`,
4,384 reactor-days; **all 36 months reconcile inside `WEDGE_TOL`** (worst
−0.62 %) so unlike PJM no month is dropped. **Zero fitted scalars** — deriver
constants frozen from ERCOT and unmodified; the PJM extract still reproduces
byte-for-byte under `--check` (rule 23).

**THE PJM PRECEDENT DOES NOT REPEAT, for the pre-registered reason.**
pjm-nuc-1b stopped at its build-time gate because the 923 anchor redistributes
event-day energy onto near-full pool days and PJM's target — the level at 22
scarcity tail hours — *is* those days (−72 MW vs a ≥ +75 MW commitment).
NYISO's target is within-month **timing**, which the anchor is neutral to.
Gate G2 was written to detect the PJM mode directly and it measured the
opposite: **104 % retention** where PJM's was negative.

**BUILD-TIME GATES (no LP), all PASS:** G1 raw-NRC lift **+0.304** 3-yr mean
gap-clean r_day (gate ≥ +0.10, no year regresses); G2 reconciled retention
**104 %**, worst year +0.126 (gate ≥ 70 %, > 0 every year); G3 max annual
|ΔTWh| **0.14 %** (gate < 0.5 %).

**LIVE-MECHANISM CHECK (nyiso-89 §4a) recorded BEFORE results were read:**
29,088 / 32,184 / 26,136 availability cells changed with **zero** changes
outside nuclear rows, `min_gen` tracking cell-for-cell, available nuclear
energy −0.01/−0.02/−0.14 %. In-solve the overlay applies 4 reactors in all
three years and the A/B diverges at the P0→P1 commitment seam. Disclosed: the
solve logs the overlay twice per year (0 reactors, then 4) — the 0-reactor
call is `bins_to_fleet`'s fossil-CAMPD-bins array build before
`build_base_fleet` adds nuclear, not the LP's fleet.

**RESULT — S2 closes in every year.** Gap-clean nuclear r_day
**0.446/0.833/0.534 → 0.885/0.960/0.917**, r_hr 0.418/0.819/0.502 →
0.834/0.941/0.836 — reproducing the build-time extract prediction to three
decimals. Displacement lands on imports (max |arm−control| 1,380/1,620/
2,272 MW), the signature of a must-run reactor going out and back.

**S1 holds — every criterion verdict identical to the control:** C1 **14/14 ·
free 10/10**, C2/C3a/C3b/C4/C7/C8 PASS. C6 UNATTESTED on **both** (probe
posture, not an arm effect). The control reproduces the keeper
criterion-for-criterion including its published knife-edge cell (−2.76).

**REPORTED ADVERSE, NOT PATCHED (rule 14).** 2023 `CC_REGULAR` walks
**−2.76 → −2.79 TWh** against ±2.94 — ~14 % of the remaining 0.18 TWh headroom
gone. **In band**, and the accurate measured input **stays in**: a thinner
margin is a discovered root cause elsewhere, never grounds to restore the
fleet-month smear. C8 2024 `ST_GAS` 30.43 → 30.47 % forced, grounded above
budget on both sides — the fragile cell does not flip. C3c (not the gate,
roof-blocked) 3/0/7 → 4/0/7 h vs actual 10/12/42.

**LOYO (rule 22):** no parameter is fitted to any year — the deriver constants
are frozen cross-ISO inheritances and each year's overlay derives from that
year's own NRC reports against that year's own 923 anchor; all three years are
scored in this one bundle and the direction is the same in each. No
out-of-training year touched (NYISO carries no calibration-complete marker).

**VERDICT: KEEPER-RECOMMENDED by the building session, then OWNER-PROMOTED the
same day** (AskUserQuestion, this session). **NYISO keeper →
`2026-07-29-nyiso-98-nucavail`**, DETERMINATION **NOT-YET** (C3c sole blocker,
the same determination class as every prior NYISO keeper). Promotion-built C6
attestation `scripts/gen_nyiso98_attestation.py` UNION's the nyiso-96 ledger →
**22 DOF entries, `n_residual` unchanged at 6** (the entry replaces an estimate
rather than adding a degree of freedom); C6 re-scores **PASS**. Matrix cell
`nuclear_unit_availability` N: U → **K**, matrix header re-stamped, keeper shard
+ `build_status.py --iso NYISO` rebuilt, `calibration-keeper-auditor --iso
NYISO` run on the promotion.

**Follow-up raised, deliberately not done here (rule 24):** the same
zero-block audit for the other EIA-930 component series this repo scores
against (`import`, `NG: WAT`, `NG: OIL`) and for the other five ISOs' BAs —
NYISO `NG: OIL` (r_day 0.07) is the obvious next suspect.

---

## 2026-07-29 — nyiso-99: item 9 (import shape) CLOSED as a C3c symptom; the EIA-930 zero-dropout found in the DEMAND INPUT and repaired

**Lane:** dispatch-matching, matrix §5.5 **item 9**. **Keeper unchanged at entry
and at exit of the adjudication** (`2026-07-29-nyiso-98-nucavail`).
**Pre-registration:** `docs/PREREG-nyiso99-import-audit-demand-dropout-2026-07-29.md`
(committed AND pushed before any solve). **Full write-up:**
`docs/FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29.md`.
**Instruments:** `scripts/probes/nyiso99_import_benchmark_provenance.py`
(census / falsify / baseline / attribute), `scripts/probes/nyiso99_ab_compare.py`.

**1. The audit ran first and CLEARED the target — unlike item 7, the queue's
premise survives.** nyiso-98 left the zero-block falsification open for every
other EIA-930 series; item 9's is `Total interchange`. Suspect hours (exactly-0.0
values plus bit-identical non-zero runs ≥4 h): **0 / 6 / 14** against `NG: NUC`'s
1,179 / 380 / 117. Every one falsified against **NYISO MIS P-32** external
schedules — an instrument that validates at hourly r **0.910 / 0.908 / 0.882** on
the clean hours before it is allowed to judge a gap. Gap-masking leaves the
item-9 statistic **bit-unchanged** (r_hr 0.598/0.624/0.454 → 0.598/0.624/0.458),
and scoring against P-32 instead reproduces it (0.612/0.611/0.495). `NG: WAT`
clean (0/1/1). `NG: OIL`'s many zeros are **confirmed genuine** by P-63
(3,074/6,285/7,343) — its weak agreement (r 0.068/0.330/0.867) is the dual-fuel
recording basis, item 10's lane, not a gap. **Item 9's defect is real.**
*Method note for the next session: align MIS feeds on **UTC**. Local-time
alignment collapses the DST fall-back hour into an 8,759-row year.*

**2. And it is not the import node's.** Three measurements on the keeper's own
sidecars: **[1]** the node tracks the spread *it is shown* at r
**+0.673/+0.686/+0.772**, so `inject_nyiso_import_hub_prices` is faithful;
**[2]** that spread is phase-inverted against the real one, r
**−0.401/−0.236/−0.600** (model peaks h21/h02/h22 vs real h17/h16/h17); **[3]**
the inversion is arithmetic with one bad term — the seam side is measured and
correct (neighbor DA LMP, hod swing 19.8/24.1/32.1 = reality) while NYISO's
**internal** swing is 12.95/13.17/19.75 against a real 22.45/25.13/43.27, a
ratio of **0.58/0.52/0.46**. Subtracting a correctly-peaked seam price from a
too-flat internal price puts the spread at its **minimum** exactly at the peak
(model −0.1/+1.8/+5.3 $/MWh at the real peak hour vs real +5.6/+9.7/+27.0), so
the LP stops importing in the hour NY imports most and buys its reconciled
monthly quota overnight. **That deficit is C3c.** This confirms nyiso-86 §3
quantitatively and adds what it could not: the seam mechanism is exonerated.

**Item 9 CLOSED, refused ex-ante on three grounds** (matrix row
`import_shape_lever` → G, `import_hub_pricing` N re-confirmed K):
identification — the only series saying "import more at h17" is the scored
outcome (rule 13); sign — nyiso-86 recorded that forcing peak imports
*depresses* peak duals, moving C3c the wrong way (rule-14-backwards); and rule
19, the phenomenon already has a mechanism. **Do not re-open while C3c is open.**

**Reported, NOT armed.** (a) The 4,350 MW `NYISO_simultaneous_import` cap is a
hand-set estimate measurement contradicts: model import tops out at **exactly
4,350 MW**, never above it in any hour of any year, on the cap in
**548/689/177 h/yr**, while measured net import exceeds it in **287/314/145 h**
(max 5,929 MW — nyiso-86's figures reproduce exactly) and P-32 *scheduled* flows
exceed it in **865/685/388 h** (max 7,078 MW). Held back because the P-32 limit
sum (~10 GW) is not a simultaneous limit but the sum of parallel paths our
five-zone network collapses — rule 14's misalignment clause — so it needs a
*reconciled* identification and its own charter. (b) 2,970 MW of the 6,580 MW
ladder (45 %) carries a per-year **constant** price; five of seven rungs sit at
their own cap or at zero in most hours. *Correction issued in-session: an
earlier draft claimed `import_scarcity` was never reached — it is, 1.182 TWh in
2023 and at its 2,230 MW cap in 27 h; the hourly repricer reorders the merit
list (it clears while `eastern_mid` is below cap in 1,209 h), which is itself
further evidence the seam works.*

**3. THE ARMED DELTA — the audit extended to INPUTS, and the artifact was
there.** EIA-930 posts reporting gaps as a literal `0.0` **value**, which
survives the NaN reindex and every loader's `interpolate().bfill().ffill()`.
Across all six modeled BAs × 2023–2025 the only affected series is `NYIS`
`Demand`: **2024 h403/6760/6761 and 2025 h354/355**, each bracketed by ~17–22 GW
— and each reproduced **1:1** in the keeper's solved sidecar as **0.0 MW of
served load**.

**The consequence was far larger than five hours of energy.** Those five hours
are **100 % of the NYISO keeper's overgeneration dump** (22,026.6 MWh in 2024,
15,587.7 MWh in 2025; 2023 has no dropout hour and no dump at all) and print
**−$26.001 in all five zones** — the dump-cost optimum. With demand pinned at
zero the must-run stack (nuclear, RoR hydro, the 900 MW firm HQ floor, wind,
solar) has nowhere to go. So the artifact was manufacturing five fabricated
floor-price hours and the keeper's entire dumped-energy total, which every
price-distribution statistic on that bundle carried.

**Mechanism:** `_screen_demand_dropouts` (`data/eia930/demand.py`), the low-side
twin of the existing `_screen_demand_spikes`, wired into all six per-BA loaders.
A whole BA's metered demand is never 0 MW, so it needs no threshold and adds
**zero DOF**. Scoped to **demand only, never interchange** — ERCO posts
187/140/113 legitimately-zero interchange hours on idle DC ties, and screening
those would delete real measurements (the rule-14 failure mode it exists to
avoid). Ungated by design: a source-data repair under rule 14 `[R-ACCURATE]` is
not a tunable, so there is no `ScenarioConfig` field.

**A/B — registered run `2026-07-29-nyiso-99-demandfix`** (`replay_keeper.py` on
the keeper's own `meta.json`, so the code fix is the only delta; the screen is a
proven no-op in 2023, making the arm's own 2023 year a same-recipe zero-delta
control). **EVERY PRE-REGISTERED GATE PASSES.**

* **G1** arm 2023 ≡ keeper 2023: max |Δ class MW| **0.000000**, max |Δ price|
  **0.000000** $/MWh. Also discharges two side questions — the container
  reproduces the keeper bit-for-bit, and caiso-139's `dump_cost_full_offer_domain`
  (which landed on `main` mid-session) is confirmed **byte-neutral for NYISO**.
* **G2** zero-served-demand hours **3 → 0** (2024), **2 → 0** (2025).
* **G3** served energy **+0.05624 / +0.04345 TWh**, matching the pre-registered
  figures exactly.
* **G4** C1 **14/14 · free 10/10**, unchanged. **2023 `CC_REGULAR` bit-unchanged
  at 32.5119 TWh** — the ISO's tightest cell (−2.79 of ±2.94) never moves.
  2024 +0.0121, 2025 +0.0090 TWh ≈ 0.4 % of band.
* **G5** C7 **PASS**, C8 **PASS**; the fragile 2024 `ST_GAS` cell moves
  30.5 % → **30.4 %**, *toward* the cap, grounded on both sides.
* **G6** C3c unchanged: hours > $300 **4/0/7 → 4/0/7**.
* **Headline:** dump **22,026.6 → 0.0** MWh (2024) and **15,587.7 → 0.0** (2025),
  *exactly* zero; the five fabricated −$26.001 hours gone; **slack stays 0.0 MWh
  in every year**, so the restored ~20 GW is served, not shed. Max |Δ price|
  $121.0 / $110.0 — the dropout hours repricing off the dump floor.
* **Import r_hr 0.624 → 0.623 / 0.454 → 0.453** — i.e. not at all. Stated
  because the pre-registration said it would be: this is NOT an item-9 fix.

Determination **NOT-YET** in both bundles, **C3c the sole FAIL** — the repair
changes no verdict, as pre-registered. The arm's C6 reads UNATTESTED only
because a non-promoted run builds no governance attestation.

**Pre-existing, unchanged, reported (rule 14):** D-5 forecast/backcast parity
FAILs on `nyiso_local_selfsupply` (not on the declared backcast-overlay list).
The keeper's own committed diagnostics carry the identical row — inherited, not
caused here; a declaration-list gap, not a dispatch defect. Own session.

**LOYO (rule 20):** nothing here is a fitted parameter, so there is no value to
overfit; the 2023 no-op *is* the held-out year and returns bit-identical. No
out-of-training year touched (NYISO carries no calibration-complete marker).

**VERDICT: KEEPER-RECOMMENDED — owner call** (NYISO lane convention since
nyiso-96). Every gate passes, the tightest C1 cell is untouched, protective
gates hold, and the bundle removes five fabricated floor-price hours plus 100 %
of the keeper's dumped energy. Not self-promoted. Matrix updated in-session:
new rows `import_shape_lever` (N → G) and `demand_dropout_screen` (N → K,
I elsewhere **by measurement** — byte-identical on 16 of 18 ISO-years), header
re-stamped, §5.5 item 9 struck with 9b added. Dashboard: run registered;
`2026-07-27-nyiso-87-arm-c` pruned by top-15 NYISO retention.

**PROMOTED 2026-07-29 (owner decision, same session).** NYISO keeper →
**`2026-07-29-nyiso-99-demandfix`**, DETERMINATION **NOT-YET** (C3c sole
blocker — the same determination class as every prior NYISO keeper). C6
attestation built by `scripts/gen_nyiso99_attestation.py`, UNION'ing the
nyiso-98 ledger → **23 DOF entries, `n_residual` unchanged at 6** (the entry
adds zero free parameters of any kind: a source-data repair is not a tunable,
and there is no `ScenarioConfig` field because there is nothing to arm); C6
re-scores **PASS**, and the full rubric is then identical to the outgoing
keeper's — C1/C2/C3a/C3b/C4/C6/C7/C8 PASS, C3c FAIL. Keeper shard +
`build_status.py --iso NYISO` rebuilt, matrix header re-stamped,
`calibration-keeper-auditor --iso NYISO` run on the promotion. **The promotion
rests on structural integrity, not fit** — the rubric does not move at all; what
moves is that five fabricated −$26.001 all-zone hours and 100 % of the keeper's
dumped energy leave the bundle.

---

## nyiso-100 (2026-07-30) — `NYISO_simultaneous_import` is a mis-attributed **internal** locality limit; retired. **KEEPER**

**Keeper → `2026-07-30-nyiso-100-silretire`** (bundle `results/calibration/nyiso100_silretire`),
promoted on the owner's in-session instruction that structural-integrity gains may
carry a keeper even where reported diagnostics regress. Determination **NOT-YET**,
**C3c the sole blocker** — the same determination class as every prior NYISO keeper.
Matrix row `nyiso_import_sil_retire` → **K**.

### The identification (this is the session's real result, and it took no LP)

The nyiso-99 charter carried this forward as "a hand-set estimate measurement
contradicts". **That framing was too generous.** 4,350 MW is a *real published
NYISO quantity measured on the wrong boundary*: it is exactly the **G-J locality**
Bulk Power Transmission Limit for capability year **2024/2025** (`data/raw/
capacity-deliverability/nyiso/nyiso.csv`, area `G-J`, `import_limit`) — an
**internal** New York transfer boundary (Load Zones G,H,I,J) — installed as the
**external** NYCA simultaneous-import cap.

Three corroborations that this is mis-attribution and not coincidence:

1. Exactly **one** row in the entire published `import_limit` table equals the
   constant, and it is the G-J row. The published G-J series **moves** by
   capability year (3,425 / 3,425 / 4,350 / 4,500 for 2022/23–2025/26) while the
   constant is frozen at the 2024/25 reading across all three solve years —
   including 2023, whose own value is 3,425.
2. The constant's **own** justification comment argued from *internal* downstate
   interfaces ("Dunwoodie-South 3.9 GW into NYC, cable-limited 1.65 GW into LI"),
   and its border-link arithmetic **omitted the `Capital_Hudson` link entirely**
   (it summed 5.2 GW against a real 6.8 GW).
3. **The cited source does not contain it.** Extraction over all three 2023–2025
   Gold Books on disk finds **zero** pages naming a simultaneous import or
   transfer limit, and **Table VI-1 is redacted as Critical Energy Infrastructure
   Information in every edition**. NYISO publishes no aggregate external
   simultaneous import limit available to this repo at all.

Measurement then falsifies 4,350 MW as an external bound: NYCA net import reached
**5,929 / 5,662 / 5,872 MW metered** (EIA-930) and **7,078 / 7,298 / 6,727 MW
scheduled** (MIS P-32), exceeding the cap in **287/314/145 h** and **865/685/388 h**.
The P-32 sum is cross-validated as NYCA net interchange rather than a double-count
of the three HQ rows — UTC-joined r **0.910/0.906/0.879**, bias **+17/−179/−262 MW**
on means of 2,677/2,322/2,612 MW (a double-count would bias ~+1,200 MW).

### Why it retires rather than raises

The naive measured replacement — the sum of posted per-interface P-32 limits,
**10,575 / 10,715 / 10,450 MW** — is *precisely* rule 14's named misalignment
exception: several parallel paths this five-zone network collapses into one link.
But the misalignment does **not** extend to every path. For the two links whose tie
sets are point-to-point HVDC converters there is no parallel-path ambiguity at all,
and the model is **already at the posted rating**:

| model link | posted P-32 ties | posted | model TTC |
|---|---|---|---|
| NYC | HTP 660 + Linden-VFT 315 | 975 | 1,000 |
| Long_Island | Neptune 660 + Cross-Sound 330 + NPX-1385 200 | 1,190 | 1,200 |

with the AC seams sitting behind the internal Central-East chain the topology
already carries (2,850 MW model vs a P-32 `CENTRAL EAST - VC` posted median of
2,865 MW). So retiring the scalar **introduces no new number and removes a free
parameter**: the aggregate becomes the border-link sum **6,800 MW**, *inside* the
measured admissible interval **[5,929 lower bound, 10,715 posted-rating upper
bound]**, where 4,350 lay *outside* it in all three years. Rule 19 `[R-ONE-MECH]`
reinforces it — shared-upstream-capacity limitation already has a mechanism here
(the internal interface chain); the scalar was a second one pointed at the wrong
boundary. **Rule-24 side effect:** the retired constant was solve-affecting but
carried **no DOF ledger entry**, so the retire also closes a registry gap.
`n_residual` stays **6** on a UNION'd **24-entry** ledger.

### The A/B — every pre-registered gate passes

PREREG committed **and pushed** before any LP ran; `replay_keeper.py` on the
keeper's own `meta.json`, so the flag is the only delta.

| gate | result |
|---|---|
| **G0** control identity | separate same-HEAD zero-delta control (`2026-07-29-nyiso-100-control-zerodelta`) reproduces the nyiso-99 keeper **bit-for-bit**, all three years: max abs Δ class MW **0.000000**, max abs Δ price **0.000000** |
| **G1** LIVE-mechanism | arm topology carries **zero** import-node interface limits, control exactly one at 4,350 MW — confirmed by topology rebuild **and** the arm's own solve log |
| **G2** releases | import max 4,350.0 → **6,518.9 / 6,470.0 / 6,075.0 MW**; hours pinned AT the old cap **548/689/176 → 0/2/0**; hours above it 0 → 436/587/161. Every max inside the pre-registered (4,350, 6,800] window |
| **G3** volume band-held | ±2 % monthly band holds every month of every year; upper-edge months **rise 10/11/11 → 12/12/11**; import energy moves only **+0.041/+0.070/+0.035 TWh** (+0.17/+0.34/+0.18 %) |
| **G4** C1 | **all 14/14 · free 10/10**, identical to the keeper. The knife-edge 2023 `CC_REGULAR` cell does move: **−2.79 of ±2.94 in the control** (32.512 TWh — the prior keeper's own value) **→ −2.80 in the arm** (32.497 TWh), a ~15 GWh/yr shift. Still passes, comfortably inside band |
| **G5** C7/C8 | both **PASS**. Fragile 2024 `ST_GAS` grounded-above-budget moves 30.4 → 30.6 % forced, but stays a **grounded** pass and its grounding evidence **improves on both legs** (D-1 profile r 0.954 → 0.958, off-peak CV ratio 0.957 → 0.972), every binding mechanism still clearing D-4 |

Slack and dump stay **exactly 0.0 MWh** in every year, both runs.

### Reported, not claimed — and one prediction recorded as wrong

Rule 1 `[R-STRUCT]` applies in **both** directions, so neither of these is offered
as support for the arm:

- **C3c** h>$300 **4/0/7 → 3/0/7** vs actual 10/12/42; mean LMP 33.56/36.32/58.98 →
  33.49/36.22/58.95. **The pre-registration predicted C3c would tick *up*** (a
  band-fixed quota reallocated overnight leaving less import at peak). It ticked
  *down*: volume was not in fact fixed, because hitting the band ceiling in two more
  months added ~0.15 TWh of supply. **That prediction is recorded as wrong rather
  than re-narrated.**
- **Import `r_hr`** 0.598/0.623/0.453 → **0.584/0.605/0.451**, worse in all three
  years — exactly as pre-registered, and for the reason given. The retired cap bound
  **54/59/62 % overnight** (h21–h03) and only **3/2/2 %** in h16–h18, and in
  **84/89/94 %** of cap-bound hours the real system imported **less** than the cap.
  It was flattering the statistic by truncating the model where reality was quieter.
  Item 9 is already CLOSED as an attributed C3c symptom with `import_hub_pricing`
  exonerated (nyiso-99), so a worse `r_hr` is not evidence against this arm.

### Open / follow-on

- **NOT armed here** (single-delta discipline): the G-J locality limit is a **real**
  constraint the topology does not represent *at its own boundary*, and retiring the
  scalar removes its only (misplaced) representative. It belongs on the **internal**
  G-J interface in the `nyiso_nyc_lcr_tsl` / `nyiso_li_lcr_tsl` family, and owes its
  own rule-14 boundary reconciliation first — the five-zone aggregation has no clean
  G-J cutset (G sits in `Capital_Hudson`, H+I in `Lower_Hudson`, J is `NYC`). Enters
  the matrix as **U**.
- **Pre-existing, unchanged, inherited not caused:** D-5 parity FAILs on
  `nyiso_local_selfsupply`, identical in the nyiso-99 keeper and this session's own
  control. A declaration-list gap, not a dispatch defect; needs its own session.
- **Method note re-confirmed:** align MIS/instrument feeds on **UTC, never
  positionally** — the model clock is 8,760 h even in leap-year 2024 while P-32 posts
  all 8,784, and positional alignment shears the series after Feb 29 (r 0.906 → 0.774).
- Carried forward: item 10 (`dual_fuel_oil_reattribution` still armed in the NYISO
  recipe metas, zero-dispatch-delta cleanup); the cross-ISO EIA-930 `NG:*` zero-block
  audit (only `Demand` was swept cross-ISO).

Evidence: `docs/FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30.md`,
`docs/PREREG-nyiso100-simultaneous-import-retire-2026-07-30.md`, probes
`nyiso100_simultaneous_import_identification.py` / `nyiso100_ab_compare.py`,
attestation `scripts/gen_nyiso100_attestation.py`.

---

## nyiso-101 — 2026-07-30 — G-J locality limit on its own boundary: REFUSED EX-ANTE

**Keeper UNCHANGED: `2026-07-30-nyiso-100-silretire`.** No flag added, no solve run,
no bundle produced (rule 15 satisfied vacuously — no run completed). The nyiso-100
follow-on (matrix item 9c) is **CLOSED**; matrix row `nyiso_gj_locality_tsl` → **G**.

**The premise survives; the boundary does not.** The G-J Bulk Power Transmission
Limit *is* real, published every capability year (3,425 / 3,425 / 4,350 / 4,500 MW
for 2022/23–2025/26), and the topology *does* represent it nowhere. But it cannot be
placed on any link of the five-zone network.

1. **Mechanical cutset test.** The G-J locality is NYISO zones G+H+I+J and
   `Capital_Hudson` = F+G **straddles** it. No model link is a valid
   import-direction G-J edge: `Upstate_West->Capital_Hudson` and
   `Capital_Hudson->Lower_Hudson` each have one straddling end;
   `Lower_Hudson->NYC` is **interior** to G-J — capping it is category-wrong, not
   merely a rule-19 stack, and it already hosts the NYC 2,875 MW cap;
   `NYC->Long_Island` is an edge only **reversed** and already carries
   `nyiso_li_lcr_tsl` in the same window.
2. **Two of four real legs are not LP quantities.** The **F→G AC cutset** is
   interior to `Capital_Hudson` (no column crosses it; Zone G holds 4,688/4,759/4,704
   MW of Gold Book summer capability). The **external ties landing in Zone G** (PJM
   Ramapo ~1,000 MW + ISO-NE New Scotland/Pleasant Valley ~600 MW) are lumped into
   the 1,600 MW `import_node->Capital_Hudson` link, whose F-vs-G split
   `interchange/spec.py` **itself** calls *"a modelling choice inside the topology"*.
   Leg 2 is what closes the door: the endogenous subset-sum form
   (`F_[CH->LH] - Σ_{g∈G} P[g,t] ≤ limit - load_G[t]`, buildable since NYISO runs
   `plant_level_fleet` and Zone G holds only ~80 MW of un-splittable hydro) dissolves
   leg 1 but still needs `ext_G`, which no measurement determines.
3. **No validating series exists, in principle.** P-32 posts seven internal
   interfaces (`CENTRAL EAST - VC`, `DYSINGER EAST`, `MOSES SOUTH`, `SPR/DUN-SOUTH`,
   `TOTAL EAST`, `UPNY CONED`, `WEST CENTRAL`) and **none is G-J**. Running the house
   pattern's own admissibility test shows the asymmetry: the accepted NYC cap sits
   essentially **at the p95** of `SPR/DUN-SOUTH` in-window flow (exceeded 1.8/5.0/6.9 %
   of HB14-21 hours), whereas G-J on `UPNY CONED` would sit at pctile 74.1/90.6/95.6
   (exceeded 25.9/9.4/4.4 %) and on `TOTAL EAST` at 67.9/81.5/83.4 (32.1/18.5/16.6 %).
4. **A static reconciled cap is unidentified — proven, not asserted.** Via the Zone-G
   balance `F_[F->G] + ext_G = load_G + F_[G->H] - gen_G`: `load_G` is measured
   (`HUD VL` in-window mean 1,168/1,207/1,231 MW), but `gen_G` is bounded only by
   [0, Zone-G capability], pinning the reconciled cap to an interval of width
   4,688/4,759/4,704 MW = **137 % / 109 % / 105 % of the limit itself**.
5. **Provably inert on the one uncontested edge**, no solve:
   `min(1,650 link TTC, 275–325 LI in-window cap, 3,425–4,500 G-J)` never selects G-J.

**Honesty note, recorded because it cuts against the refusal's rhetoric:** the
measured exceedance does **not** falsify the published limit. Required `gen_G` at the
in-window extremes — 2,010/1,487/1,180 MW at p95, 3,545/2,605/2,994 MW at max — stays
**inside** Zone-G capability (76 %/55 %/64 %) in every year, so the limit is
*consistent with* measurement for an unobservable Zone-G net position. The verdict is
**unidentified, not refuted**: the discrepancy and the missing term are the same size.

**Refused against its own incentive** (rule 1 `[R-STRUCT]`, both directions): a
binding G-J limit tightens downstate supply and would **raise** downstate peak prices
— the direction C3c, the sole NYISO determination blocker, wants. That was
pre-registered as grounds for *extra* scrutiny, and the boundary could not be
identified, so the limit stays out whatever it would have done to C3c.

**Budget spent: 0.00 TWh.** The ISO's tightest cell (2023 `CC_REGULAR`, −2.80 of
±2.94, 32.497 TWh) was budgeted ~0.14 TWh and is untouched. C1 14/14 · free 10/10,
C6 PASS (24-entry ledger, `n_residual` 6), C7/C8 PASS, C3c sole blocker,
DETERMINATION NOT-YET — all unchanged.

### Open / follow-on

- **Re-open condition (satisfiable, unlike C3c's):** split `Capital_Hudson` into Zone
  F and Zone G. That makes leg 1 a real link and forces leg 2 to be allocated
  explicitly, after which the house pattern applies unchanged. The F/G county split is
  already carried per-county in `zone_assignment.NYISO_CAPITAL_HUDSON_COUNTIES` and
  Gold Book Table III-2a carries the zone letter per unit, so the fleet side is ready.
  **But it is a topology change** — load shares, zonal shapes, reliability-floor limb
  keys (`Capital_Hudson:ST_GAS`), D-2 ids and every NYISO keeper's comparability move
  with it — the same class as the ERCOT West/Panhandle split, which is **CLOSED**. It
  needs its own owner-authorized charter and is **not** queued as a lever.
- Carried forward unchanged, none touched this session: D-5 parity FAIL on
  `nyiso_local_selfsupply` (declaration-list gap, own session); item 8
  (`hydro_ror_split`, blocked on the Robert Moses Niagara treaty-schedule classifier
  review); item 10 (`dual_fuel_oil_reattribution` in the NYISO recipe metas); the
  stale `frontend/data/backcast/status/NEISO.js` (different lane); the cross-ISO
  EIA-930 `NG:*` zero-block sweep (only `Demand` was swept cross-ISO).
- **Method note honoured, not re-derived:** the probe keeps both clocks — UTC for any
  join, local for the HB14-21 window (a local-clock definition) — since 2024 posts
  8,784 P-32 hours against the model's 8,760.

Evidence: `docs/FINDING-nyiso101-gj-locality-boundary-2026-07-30.md`, probe
`scripts/probes/nyiso101_gj_locality_boundary.py` (no LP; sections `provenance`,
`cutset`, `legs`, `split`, `falsify`, `reconcile`).

## nyiso-102 — 2026-07-30 — the D-5 parity FAIL was a **forecast-wiring gap**, not a declaration gap; fixed, keeper unchanged

**Keeper unchanged:** `2026-07-30-nyiso-100-silretire`. **No LP delta on the backcast.**
Scope: `src/market_sim/runner.py` + tests + matrix. C3c remains the sole determination
blocker; DETERMINATION NOT-YET, untouched.

The charter offered two candidate causes — "does `nyiso_local_selfsupply` belong on the
declared backcast-overlay list, or is its backcast-only gating itself the bug?" —
and **neither is quite right**.

### It is not a declaration gap

`nyiso_local_selfsupply` is **market design, not an overlay**, and its own definition
says so in exactly the terms rule 13 `[R-MEASURED]` asks for: *"FORWARD-REPRODUCIBLE
(scales with load, responds to conditions) and grounded in NYISO market design — NOT a
pin to measured LI generation."* It floors in-zone thermal at `frac × zonal load` in the
HB14-21 window, consumes no measured outcome, and regenerates for any forward year. Its
D-5 registry row already records that intent: `mode="both", declared=False`.

Declaring it would have asserted the opposite — that an LMIC self-supply rule is a
historical overlay with no forward analogue — **sanctioned the real gap permanently**,
and turned the gate green through a change that isn't the fix (rule 1 `[R-STRUCT]`).

### It IS a wiring gap — three mechanisms, not one

D-5 measures wiring by source text. Before this session:

| symbol | `scripts/run_calibration.py` | `src/market_sim/runner.py` |
|---|---|---|
| `inject_nyiso_local_selfsupply` | 3× | **0** |
| `apply_nyiso_li_tsl_import_cap` | present | **0** |
| `apply_nyiso_nyc_tsl_import_cap` | present | **0** |

The whole NYISO downstate family was reachable only from the backcast orchestrator.
This is a known defect class with a named precedent: `runner.py` already carries
`apply_neiso_coldsnap_derate` annotated *"orchestrator-unification Stage 6: previously
wired only in the backcast orchestrator, the plan's §2.2 accidental-drift row."*

**All three are now wired into `runner.py`**, each behind its existing default-off gate:
the floor after the availability derates (so its "never demand more than the fleet can
supply" clamp sees final availability — the backcast's own ordering), the two caps onto
`year_ttc` after the CAISO/transmission-expansion swaps.

### Why the caps had to travel with the floor

`nyiso_li_lcr_tsl` is **exactly what excludes `Long_Island`** — the *only* pocket in
`NYISO_LOCAL_SELFSUPPLY_FRAC` — from the floor (rule 19 `[R-ONE-MECH]`). Wiring the
floor alone would have turned D-5 green while leaving a forecast run on the keeper's
config with the floor excluded (flag on) and the cap never called: **neither mechanism
on the downstate pocket, gate reporting parity.** That is gate-gaming in the precise
sense rule 1 names. Pinned by
`TestD5NyisoDownstateParity::test_lcr_tsl_caps_travel_with_the_floor`.

### The nuance the charter did not anticipate: the named mechanism is INERT here

`NYISO_LOCAL_SELFSUPPLY_FRAC` holds exactly one pocket (`Long_Island: 0.45`), and the
keeper runs `nyiso_li_lcr_tsl=True`, which excludes it. So
`inject_nyiso_local_selfsupply` iterates one pocket, hits `continue`, and returns
`False` — **no floor at all**. The keeper's own committed D-2 confirms it: **zero rows,
zero forced energy** attributed to `nyiso_local_selfsupply` (0 of 20 D-2 rows, 0 of 15
D-4 rows).

D-5's `_toggle_on` reads the raw config flag, so it called a mechanism active that the
rule-19 exclusion had already reduced to nothing. **The FAIL was therefore a true defect
AND a false positive for this keeper simultaneously.** The gate coarseness is
**deliberately left alone**: teaching D-5 to excuse an inert mechanism would weaken a
legitimacy gate to silence a symptom, and would leave the forecast gap open for any
config with `nyiso_li_lcr_tsl=False`, where the floor *is* live in backcast. Recorded as
a known property, not patched.

### Byte-identity of the backcast — proved three ways, not asserted

- **Static:** no file in the backcast chain (`run_calibration_full.py`,
  `run_calibration.py`, `pipeline/solve.py`, `pipeline/commitment.py`) references
  `market_sim.runner`. The only module naming it is `pipeline/api.py`, the forecast
  facade, lazily.
- **Runtime:** `import scripts.run_calibration` → `'market_sim.runner' in sys.modules`
  is `False`. Pinned as a regression test.
- **Empirical:** a same-HEAD zero-delta control (`replay_keeper.py` on the keeper's own
  `meta.json`, 2023 2024 2025 in one sequential invocation, rule 16) reproduces the
  keeper **BIT-FOR-BIT**: `max |delta| = 0.0000000000` over `class_hourly` / `system` /
  `storage` × 3 years — 42 numeric columns, **2,417,760 value comparisons**, every shape
  matching. Not "within tolerance": exactly zero. The pass criterion was pre-registered
  and pushed (`a5fc1b8`) **while year 2025 was still solving**.

**No run registered; rule 15 satisfied vacuously.** The control reproduces an
already-registered keeper exactly, so registering it would put a numerically
indistinguishable duplicate on the run explorer — the nyiso-101 precedent (*"say so
explicitly rather than inventing a bundle"*). Unlike nyiso-100's registered control,
which was the A-side of a real A/B, here the A/B is A against A.

### Result

D-5 **PASS** on the keeper's config: 12 rows → 11, **every remaining row `declared`**,
`failures: []`. The `nyiso_local_selfsupply` row is *gone entirely* rather than
downgraded — `active_backcast == active_forecast` now holds, so the gate emits no row.
That is the correct shape of the fix: the difference stopped existing.

`legitimacy_diagnostics.json` regenerated in place (scorer-only, rule 20 — no re-solve,
diff confined to the D5 block). `audit_keepers.py --check`: **NYISO all checks passed**;
the single repo-wide failure remains the pre-existing stale
`frontend/data/backcast/status/NEISO.js` (different lane, not caused here).

**Forecast blast radius: none.** All three flags default `False` and no forecast driver
or recipe sets any of them, so every existing forecast run is byte-identical too — what
changed is that the mechanisms are now *reachable* in forecast mode instead of silently
dropped. Matrix `lcr_tsl_published` has always declared `mode: "BF"` while its forecast
half was unreachable **in code**; nyiso-102 makes the declared mode true and stamps
`fc: "..UUU."` (reachable, untested — **U**, not K).

**Budget spent: 0.00 TWh.** The ISO's tightest cell (2023 `CC_REGULAR`, −2.80 of ±2.94)
cannot move: the backcast dispatch is unchanged. C1 14/14 · free 10/10, C6, C7/C8 all
unchanged.

### Correction to the charter: item B was already done

Item B proposed arming `nyiso_gas_commitment_bridge` as "the only remaining armable
NYISO lever (default off)". That is the **`ScenarioConfig` default**, not the keeper's
state — `2026-07-30-nyiso-100-silretire` **already runs it**, at the measured
parameters, with the peak-window floors off exactly as the owner directive requires:
`nyiso_gas_commitment_bridge=true`, `cc_min_load_frac` 0.523 / `st_min_load_frac` 0.239
(ScenarioConfig defaults, WP-3 measured), `min_run=true` with 21 h / 13 h,
`startup=true`, and `reliability_floor_overrides` = the five
`NYISO_PEAK_WINDOW_FLOORS_OFF` limbs. Armed since `2026-07-29-nyiso-99-demandfix`.
Confirmed live in this session's control log: *"NYISO gas commitment bridge: 34998
unit-hours floored (2.32 TWh floor volume) … (min_run extension ON)"*. Re-arming it
would have been a no-op A/B against itself — **drop it from the NYISO lever queue.**

### Open / follow-on

- **D-5 `_toggle_on` coarseness** (flag-based, blind to rule-19 exclusions) is recorded,
  not patched — see above for why.
- **`_apply_iso_monthly_ttc`** (the NYISO Central-East measured seasonal envelope) is
  also backcast-only, but it is a *measured monthly limit series* — an overlay by
  nature, unlike the three fixed here — and it carries no D-5 registry row. Noted, not
  touched.
- Carried forward unchanged, none touched: item 8 (`hydro_ror_split`, blocked on the
  Robert Moses Niagara treaty-schedule classifier review); item 10
  (`dual_fuel_oil_reattribution` still in the NYISO recipe metas though the CLI pins it
  NEISO-only); the stale `frontend/data/backcast/status/NEISO.js` (different lane); the
  cross-ISO EIA-930 `NG:*` component zero-block sweep.
- **C3c** untouched and unaimed-at: diagnosed structural limitation of the five-zone
  representation, empty lever queue (nyiso-94/95/96/97).

Evidence: `docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md`;
`tests/scoring/test_legitimacy_diagnostics.py::TestD5NyisoDownstateParity`.

---

## nyiso-103 — the unregistered-field cache-key break (rule 24 [R-REGISTRY]); NO LP

**No solve. Zero dispatch delta. Rule 15 is satisfied VACUOUSLY — no run was
produced, so there is nothing to register** (the nyiso-101 / nyiso-102 precedent).
The NYISO keeper is **unchanged**: `2026-07-30-nyiso-100-silretire`.

### The defect

`ScenarioConfig().cache_key()` had moved off its pinned value:

```
        actual  2c8098e8e1684c7d
      expected  603c2498bf71d21d
```

**Blast radius was larger than the charter recorded** — not one failing test but
**five, across four files**: `test_persisted_identity` ×2
(`test_default_scenario_config_cache_key_is_pinned`,
`test_default_cache_key_is_checkout_path_invariant`),
`test_forecast_xyear_warmstart_flag`, `test_ramp_envelope_basis`, and the
`test_cc_committed_offer_margin` case the charter named.

### Identification — the culprit is NYISO's own field

Bisected by loading the pre-pin `scenarios.py` (commit `47e320b`, which set the pin)
alongside the current one and diffing the two post-drop-pass payload key sets. Exactly
one key differs:

| new field since the pin | registered in `_CACHE_KEY_OPTIONAL_FIELDS`? |
|---|---|
| `caiso_p1_export_sink_seam` | yes |
| `coal_peak_offer_gas_hr` / `_level` / `_margin` | yes |
| `ercot_gas_bridge_online_hours` | yes |
| **`nyiso_import_sil_retire`** | **NO** |

Dropping `nyiso_import_sil_retire` alone reproduces `603c2498bf71d21d` byte-exactly.
It landed with nyiso-100 (`2cc1179`) — the simultaneous-import retire — and was never
added to the drop-at-default registry, so it entered the digest **at its own default**.

### Which side was fixed, and why the drop list is the correct side

**Registered, not re-baselined.** The field belongs in the drop list because it is
byte-identical at its default, and that is *measured*, not merely asserted:

1. Its consumer (`model/interchange/spec.py:1878`) is gated —
   `if iso == "NYISO" and getattr(config, "nyiso_import_sil_retire", False)` — so at
   `False` the branch is never taken.
2. nyiso-100's own **G0 zero-delta control** (`2026-07-29-nyiso-100-control-zerodelta`)
   reproduced the prior keeper **bit-for-bit in all three years** at this default —
   max |Δ class MW| 0.000000, max |Δ price| 0.000000 $/MWh.

Re-baselining the literal would have buried a live rule-24 breach and left every
pre-nyiso-100 cache orphaned permanently.

### Cache-invalidation consequence — the fix RESTORES, it does not orphan

Verified against the pre-fix build:

| config | key before fix | key after fix |
|---|---|---|
| default (`False`) | `2c8098e8e1684c7d` | **`603c2498bf71d21d`** (restored) |
| armed (`True`, the keeper) | `604490693f01c1e2` | `604490693f01c1e2` (**unchanged**) |

So **the nyiso-100 keeper's cache key does not move**. Only default-valued configs
re-key, and they re-key *back* to the pre-nyiso-100 value — every cache orphaned since
`2cc1179` becomes live again. Armed runs stay a distinct scenario, which is what keeps
the keeper independent of its control on disk.

### Root cause, not just the instance

This is the **sixth documented recurrence** of the identical defect — the registry
table's own comments record `pjm_apsouth_interface_cut`,
`pjm_external_net_position_cut`, the four miso-101 `temp_derate_*` fields,
`coal_committed_takeorpay_sunk_fixed` and `pjm_zonal_loss_surface` all landing
unregistered and moving the pin. Every time, the failure message was an opaque hash
mismatch naming no field, and diagnosis meant hand-writing a bisect against the pre-pin
commit — which is exactly what this session had to do again.

`test_default_scenario_config_cache_key_is_pinned` now runs that bisect **in-process on
an already-failing pin** and names the culprit:

```
CULPRIT: 'nyiso_import_sil_retire' — dropping it from the payload restores
603c2498bf71d21d. It is a solve-affecting field that landed WITHOUT an entry in
scenarios.py::_CACHE_KEY_OPTIONAL_FIELDS … Register it; do NOT re-baseline the literal.
```

Zero maintenance and no false positives: it only executes when the pin already failed,
and it reports a field only when dropping that single field demonstrably restores the
pin. It deliberately does **not** assert "every default-off field must be registered" —
`miso_zonal_loss_surface` is correctly unregistered (it predates the pin and is already
inside it, so registering it would *move* the key rather than restore it).

### Verification

- All 5 previously-failing pinned tests green; 42 passed across the four files.
- Full `tests/unit` + `tests/regression` sweep: **3290 passed**, 19 skipped.
- `ruff` clean on both touched files; `check_mechanism_matrix.py` integrity OK.
- Matrix: no cell change — no mechanism was tested and no verdict moved.
  `nyiso_import_sil_retire` keeps its nyiso-100 `K`.
- Two failures in the sweep are **pre-existing and unrelated**, both confirmed by
  re-running them on stashed-clean main: `test_export.py::test_curtailment_never_negative`
  (fresh-container `data/clean/confirmed-retirements` gap — cleared by
  `curate_confirmed_retirements.py`) and
  `test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`
  (`availability` / `min_gen` drift; cannot be reached by a cache-key drop-list edit).

### Not touched

Item B (stale `frontend/data/backcast/status/NEISO.js`, `audit_keepers --check` S1) is
**still open** — single-delta discipline, and a different ISO lane. It remains the only
`audit_keepers` failure repo-wide.

---

## nyiso-104 — the `_apply_iso_monthly_ttc` D-5 registry gap: OVERLAY, declared (2026-07-30)

**No LP. No solve-affecting change. Keeper `2026-07-30-nyiso-100-silretire` UNCHANGED.**
Charter Item A. Item B (stale `status/NEISO.js`) deliberately not taken — single-delta.

### The gap

`pipeline/ttc.py::apply_iso_monthly_ttc` and `apply_iso_year_ttc` apply NYISO's
measured Central-East DAM TTC to `Upstate_West -> Capital_Hudson` from
`scripts/run_calibration.py` only (`:1871`, `:2021`); `runner.py` references
neither. Textbook D-5 mode difference — but **`D5_REGISTRY` had no row for
either**, so parity never saw them. D-5 was green on an incomplete inventory.

Scope note: the charter names only the monthly helper. `apply_iso_year_ttc` has
the identical gap on the identical source series, so both are covered by **one**
row (two aggregations of one series over one link — rule 19 `[R-ONE-MECH]`).

### The fork, resolved (a) — argued from the data, not by analogy

The source is the `TTC (DAM)` column of NYISO's MIS `ATC_TTC` postings for
`CENT EAST`, month-meaned and rounded to 25 MW — a **realized operational
series** carrying that day's approved transmission outages, not a rating table.

Discriminating test: a published seasonal rating is recomputed the same way
every year, so on an unchanged network its level-normalized monthly shape must
repeat. 2024 and 2025 share the post-AC-Transmission topology.

| | result |
|---|---|
| Pearson r (2024 vs 2025 shape) | **+0.209** |
| Spearman ρ | +0.155 |
| p vs dihedral calendar null | 0.250 |
| deepest-derate month | **Sep → Apr** |

The true calendar alignment fits no better than a rotated or reversed one.
**`constants.py`'s "recurring late-summer/shoulder derate" claim is FALSIFIED**
by the tables it describes (Aug–Nov: +7.9 % in 2024, **+0.0 %** in 2025);
corrected here, along with the same claim propagated into `pipeline/ttc.py`.

Variance: 82.0 % between-year (level/step), only **6.8 %** the post-upgrade
within-year shape (sd 162/199 MW on a 2,850 MW link). The disputed component is
non-reproducible *and* small.

Admissible in a backcast all the same — a year's transmission-outage schedule is
a physical availability event on the network, the same family as
`historic_outage_overlay` on a unit, and it enters as a constraint, not a pinned
outcome. So: declared overlay.

### Why NOT wired forward (fc = G, refused, not untested)

The forecast is missing nothing. The forward-reproducible component (the level)
already has its channel: `data/raw/transmission-expansion/nyiso.csv`
(`in_service_year` + ΔTTC, wired into `runner.py`) over the static 2,850 MW —
which **is** this series' measured post-upgrade annual mean. The registry's own
Smart Path Connect row already says so. Pushing the monthly numbers forward
would import one historical year's outage schedule into every forecast year.

### Changes

- `D5_REGISTRY` row `nyiso_central_east_measured_ttc` — `declared=True`,
  `mode="backcast_only"`, `iso="NYISO"`, `toggle=None`.
- `MechanismSpec` gains optional `iso`; `run_d5` skips non-matching ISOs.
  Required because the row has no toggle to scope it — an always-on
  ISO-exclusive overlay would otherwise claim to be active in all six ISOs.
- `constants.py` + `pipeline/ttc.py` provenance comments corrected.
- Declared-overlay list: new 2026-07-30 section in
  `docs/backcast-measured-data-audit-2026-06.md`.
- Keeper artifact `legitimacy_diagnostics.json` re-emitted (D-5 block only —
  `--only D5 --json-out` would have dropped D1/D2/D4/D9/D10, which need floor
  reconstruction from raw inputs absent here). 7-line pure insertion.

### Verification

- D-5 on the keeper: **PASS**, 11 → 12 rows, new row `declared`, 0 failures.
- Every other row unchanged, proved on two bundles: CAISO keeper re-scores 11 →
  11 (none added, none removed, order preserved); NYISO 11 → 12, the one add.
- Keeper artifact: D1/D2/D4/D9/D10 + `gates` + `schema` asserted equal before write.
- `tests/scoring/test_legitimacy_diagnostics.py` 68 passed (5 new);
  `test_fuel.py -k "ttc or monthly"` 9 passed; facade shims 12 passed.
- `check_mechanism_matrix.py` integrity OK. Matrix row + header stamp added.
- Rule 15 satisfied **vacuously** — no solve ran, nothing to register.

### Recorded, not fixed

- **`ordc_floor_active_mask` bleeds across ISOs** — an ERCOT mechanism with
  `toggle=None` and no `iso` scope, reporting itself active in every non-ERCOT
  bundle (visible in the NYISO keeper's own artifact). The new `iso` field is
  the fix, but applying it changes other ISOs' committed row sets — separate delta.
- **Binding frequency unmeasured** — how often the monthly envelope binds
  differently from the annual mean needs an LP replay (the `hourly/` sidecars
  carry no link flows). The classification does not turn on it.

Evidence: `docs/FINDING-nyiso104-central-east-ttc-classification-2026-07-30.md`,
probe `scripts/probes/nyiso104_central_east_ttc_classification.py`.

---

## nyiso-104b — FRONTIER + CALIBRATED-WITH-CAVEATS, and the holdout marker splits in two (2026-07-31)

**No LP. Keeper `2026-07-30-nyiso-100-silretire` UNCHANGED — scorer/governance-side only.**
Owner decision, conditional on exhaustion; the condition was **verified against the record**.

### 1. Determination: NOT-YET -> CALIBRATED-WITH-CAVEATS

C3c (`price_tail`) was the **sole** FAIL — C1/C2/C3a/C3b/C4/C6/C7/C8 all already PASS. It is now
one ledgered caveat (budget 3, 0 protective, 0 FAILs), added through
`scripts/gen_nyiso100_attestation.py` (the **generator** is the source of truth).

The caveat does **not** claim the benchmark is wrong. The miss is real: **model 3/0/7 h vs actual
10/12/42 h** above $300 (0.30x / 0.00x / 0.17x). It records an exhausted queue on a diagnosed
structural limit, in MISO's honest `price_tail` shape — `MODEL MISS (structural — representation-
frontier caveat, every admissible mechanism tried on record per rule 1)` — not a borrowed
measured-input excuse.

**Exhaustion, checked not assumed:** J/K-commitment + reserve tiers closed (nyiso-83/84); DA
virtual depth and TSA derate refused ex-ante on identification (nyiso-94/95); short outage windows
inert (nyiso-93); CT start-frequency closed and `tranche_startup_amortization` tested (nyiso-96);
the last surviving candidate — SCUC load-pocket + BPCG — closed ex-ante on **content**, not merely
access (nyiso-97); import shape refused as an attributed C3c symptom (nyiso-99); G-J locality
refused for want of a representable boundary (nyiso-101). The one nominally-open item,
`nyiso_iroquois_winter_spread`, conserves the annual spread and is blocked on a **joint summer
lever** — and summer is exactly what is exhausted (nyiso-92 dated the RT tail as summer: 2025
Jun 23-25 alone = 18 of 42 h; the Jan-2024 storm produced **zero** >$300 h). Rule 1 `[R-STRUCT]`
is why this is a ledger entry: every remaining way to lift the tail is fitted to the tail residual.
Re-open condition is the `Capital_Hudson -> Zone-F/Zone-G` topology split — its own owner charter.

### 2. The rule-22 holdout marker splits into two tiers

The load-bearing change. Previously ONE `complete` entry authorized **every** out-of-training year,
so declaring an ISO complete silently armed its **touch-once** locked test. Rule 22 admitted it:
*"the CI gate is tier-agnostic."*

| tier | years | block | semantics |
|---|---|---|---|
| validation | 2018, 2020, 2021, 2022 | `complete` | iterable, model-selection evidence |
| locked test | 2019, 2026 (H1) | **`final`** | touch-once, ever |

`scripts/lib/holdout_policy.py` owns the tier map; all three gates read it and **fail closed** (an
unenumerated year maps to locked). NEISO and NYISO hold `complete`; **`final` is empty** — NEISO's
locked test is already **SPENT** (2026-07-07, frozen neiso-53) and must never be re-granted, and
both files say so, because a blank must not read as an invitation.

NYISO's is a **RE-declaration**: its 2026-07-13 marker was withdrawn 2026-07-19 by the
phantom-outage re-audit, whose own prescribed path was "re-calibrate ... then re-declare". The
keeper here descends entirely from that post-correction re-calibration (nyiso-96 -> 98 -> 99 ->
100). The withdrawn record is annotated `superseded`, not deleted.

### 3. Nothing is spendable today

The **holdout spend freeze** (declared 2026-07-25, held 2026-07-26) is **ACTIVE** and outranks
every marker — verified by exercising the gate against the real repo, where the freeze fires ahead
of the marker check. NYISO's 2022 touchpoint opens only when the **owner** lifts it.

### 4. Verification

- Determination: `CALIBRATED-WITH-CAVEATS`, basis "1 ledgered measured-input caveat(s): C3c".
- Gate matrix: `[2019]`/`[2026]` now **BLOCKED** for NEISO and NYISO (allowed pre-split);
  mixed-tier blocked on the locked leg; `final`-only does not buy validation; `[2027]` blocked.
- D-6 `--keepers`: PASS, NEISO's two 2022 bundles correctly tiered validation/`complete`.
- `audit_keepers --check`: PASS 0/0 — after fixing the E5 drift it caught (the sidecar
  `definition` still asserted NOT-YET; rewritten).
- Tests: 96 passed across `test_holdout_year_gate` / `test_audit_keepers` /
  `test_legitimacy_diagnostics` — 8 new tier tests; 3 existing updated to assert the new
  tier-specific message rather than the superseded one.
- `check_mechanism_matrix.py --base origin/main`: integrity OK; matrix header re-stamped.

Evidence: `docs/FINDING-nyiso104-c3c-frontier-and-tiered-holdout-2026-07-31.md`.

## nyiso-105 — three no-solve closures, and `measured_chp_heat_rates` becomes the KEEPER (2026-07-31)

**Keeper `2026-07-30-nyiso-100-silretire` → `2026-07-31-nyiso105-chp-heat-rates`**
(bundle `results/calibration/nyiso105_chpheatrate_B`). Frozen HEAD `0852d5b`.
Pre-registration `results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md`,
committed **and pushed before either arm solved**. Scorer
`scripts/probes/_nyiso105_chpheatrate_ab.py`; no-LP probe
`scripts/probes/_nyiso105_seam_recipe_stgas.py`.

Four items were scoped. **Three closed on measurement alone, no LP** — the
nyiso-93/94/95/97/99/101 pattern. One solved and is the keeper.

### 1. Lever 1 `st_gas_mustrun_p25_level` — INERT ex ante, cell `U → I`, no solve

Four independent blockers, any one decisive. (a) The **single flag is a no-op by
construction** — `arrays.py:1750-1753` gates the p25 block on
`st_gas_mustrun_per_plant` too, which the keeper carries `False`, so the scope's
suggested `--set` arm would have solved a bit-identical control. **The arm is the
pair.** (b) The **pair is a no-op on today's artifact**:
`thermal_tranche_online_frac("NYISO")` returns **0 rows** — no `online_frac`
column exists — so 0 of 11 ST_GAS plants clear the `level>0 AND frac>0` gate.
Census: MISO 16/16 populated, CAISO 0/3, PJM 0/10, NYISO/NEISO no column. (c)
Making it fire is a **fleet-wide re-basing**: re-deriving at HEAD moves `p25_cf`
on 32/78 rows (max 83.6 pts), `committed_pct` 36/78, `median_cf` 37/78 — the
tranche shares the whole offer curve is built from — and emits **`p25_cf > 100 %`**
on two plants (S A Carlson 142.2, Astoria 101.7) against an accessor with **no
upper clamp**. (d) **The queue's premise was wrong**: "measured levels instead of
fitted fractions" describes MISO's incumbent; NYISO's surviving NYC/LI limbs are
*already* measured p25 (0.1750 / 0.2620, *"when-available cool-day CF p25"*). Rule
19 independently forbids the stack — ST_GAS already carries two mechanisms with
D-2 recording 2024 at 30.6 %.

### 2. Item A — the caiso-142 export-sink seam is CONFIRMED and **LIVE**, cell `U → O`

caiso-142 §F measured the *superseded* nyiso-99 keeper. Re-measured on nyiso-100:
705 fleet rows, exactly **1** absorption row (`NYISO_external_export_surplus`,
pmin −600 / pmax 0), driven to `min_gen` 0.0 by `_bridge_floored_fleet` with the
gate off and held at −600.0 with it on — 1 row differing, 0 others, availability
byte-identical. The NYISO call site (`commitment.py:888`) passes **no**
`preserve_absorption` argument at all, so the collapse is unconditional there.
**New over the CAISO finding: it is LIVE, not latent** — in the money against the
keeper's own node dual in **921 / 1,078 / 679 h**, max gap $164.80 / $148.20 /
$321.27, foregone export ≤ 0.553 / 0.647 / 0.407 TWh (first-order bound: the dual
was solved *with* the sink pinned off). **Nothing armed** — the fix is
CAISO-flag-gated, and the direction (off-peak λ up) *compresses* the diurnal
spread and does nothing for C3c's summer tail.

### 3. Item B — `dual_fuel_oil_reattribution`: dispatch delta zero, recording delta **not**

The CLI pin holds (`calibration_flags` = `None`) but the lineage carries the flag
through `prb_overrides`, so the solved config had it **on**. Dispatch delta proved
zero two ways: structurally (the mask's only consumers are the NEISO-gated winter
budget and `_dispatch_frame`'s post-solve relabel) and empirically — **every LP
input byte-identical** with the flag flipped, all three years. But the relabel
moves **0.1119 / 0.3511 / 1.1508 TWh** (53 / 155 / 715 h) into a recorded `oil`
class — 1.61 TWh, the order of an entire scored class. §5.5 item 10 is **struck as
written and re-opened as a scored cleanup**.

### 4. Lever 2 `measured_chp_heat_rates` — **KEEPER**, cell `U → K`

One boolean delta, **zero free parameters** (`n_residual` unchanged at 6). It
undoes eGRID's own CHP allocation on eGRID's own net denominator,
`(PLHTIAN + CHPCHTI) / PLNGENAN` — no gross-to-net factor, which is what blocked
the CEMS route. 18 of 31 rows applied: CC_CHP 11/17 plants (2,984 of 4,309 MW,
69.3 %) 6.82 → 8.50 MMBtu/MWh; CT_CHP 7/14 (384 of 446 MW, 86.2 %) 7.46 → 11.68.
CEMS-validated 16/18 at median ratio 1.00000. NYISO is **not** in
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS`, so unlike caiso-147 no hand factor is
involved — a pure rule-14 accuracy swap.

**Every pre-registered gate passes.** K2 passes on the **strict byte** basis, not
merely the scorecard one: control − committed keeper is **exactly 0.0** on every
class in all three years, so unlike caiso-146/neiso-69 **NYISO has no same-HEAD
drift** and the A/B is unconfounded. K3 liveness: CC_CHP 727.0/578.9/660.4 MW,
CT_CHP 160.7/157.3/160.7 MW. K6: free classes move too (CC_REGULAR, ST_GAS,
CT_PEAKER), so the verdict does not rest on D-10-pinned classes.

**No criterion regresses, and two things improve.** Determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, the same single ledgered caveat (C3c) — no new
slot spent. (i) Energy-weighted C1 |error| **9.458 % → 9.224 %** (7.66→7.60,
5.66→4.76, 15.06→15.31), more classes better than worse every year (4/3, 5/2,
4/3): CC_CHP +13.61→+10.75, +7.95→+2.74, +31.41→+28.21 %; CC_REGULAR −7.93→−6.61
and −1.87→+0.23 %; ST_GAS better in 2024/2025; CT_PEAKER better in all three.
(ii) **The previous keeper's own D-2 failure clears** — nyiso-100 carried
*"2024 ST_GAS: forced share 30.6 % > 30 %"*; this arm has no D-2 failures, because
ST_GAS dispatches more once CHP is priced honestly.

**Reported, not patched (rules 1 / 14).** CT_CHP deepens −49.3/−52.4/−38.6 % →
−67.9/−67.6/−62.0 %. An **open root-cause item**, not a defect of this mechanism:
CT_CHP was *already* 39–52 % under-dispatched before the arm, so a strictly more
accurate offer **exposes** a pre-existing miss rather than creating one. Named
successor lane: the BTM host-steam holdout (`chp_btm_pct` / `chp_grid_pmin_mw`)
and the CT_CHP must-run treatment — **not** the heat rate. Mean λ rises
34.660→35.078, 37.667→38.227, 61.974→62.837 $/MWh; C3a stays PASS.

**C3c is not targeted, not claimed and not moved.** The closed C3c queue stays
closed and the nyiso-104b frontier declaration stands.

Evidence: `results/calibration/FINDING-nyiso105-stgas-inert-seam-live-2026-07-31.md`;
`results/calibration/_nyiso105_chpheatrate_ab.json`.
Runs registered: `2026-07-31-nyiso105-control`, `2026-07-31-nyiso105-chp-heat-rates`
(top-15 retention pruned nyiso-87-cmeas and nyiso-89-control-zerodelta).

## nyiso-106 — the 2025 solar benchmark is a coverage artifact; two guards miss it; `p25_cf` clamped (2026-07-31)

**Keeper UNCHANGED: `2026-07-31-nyiso105-chp-heat-rates`.** Frozen HEAD `a209836`.
**Zero solves.** Both scoped no-solve items (A and B) closed on measurement alone —
the nyiso-93/94/95/97/99/101/105 pattern. No pre-registration was needed because no
arm was solved and no mechanism was tested. Probe:
`scripts/probes/_nyiso106_solar_benchmark_audit.py`; evidence
`results/calibration/_nyiso106_solar_benchmark_audit.json`.

### 1. Item A — `solar` 2025 +437.2 % is a SURVEY-COVERAGE ARTIFACT, falsified

**The scoped premise is moot.** The scope asked to gap-audit `NG: SUN` the
nyiso-98 way. There are no gap days: EIA-930 `NYIS` `NG: SUN` is **identically
zero** — 8,760/8,760 zero hours in 2023, 8,746/8,746 in 2024-25, all 2,190 midday
hours zero every year, max 0 MW. Structurally absent (NY grid solar is
overwhelmingly distribution-connected / net-metered), not zero-coded-gappy — which
is precisely why `results.calibration._EIA923_OVERRIDE` routes NYISO solar's
scoring to **EIA-923**. The audit's real target was the 923 vintage.

**The defect.** EIA-923 NYIS `SUN`: 441 plants / 2.0479 TWh (2023), 565 / 2.9008
(2024), **8 / 0.6617 (2025)**. A plant-coverage collapse, not a month one (all 8
report 12 months). The whole 2025 vintage is preliminary — 3,427 plants nationally
vs 13,210. **The 8 are a strict subset of 2024's 565 and on a like-for-like basis
they GREW: 0.2527 -> 0.6617 TWh** (Morris Ridge 20,861 -> 313,307 MWh). NY solar
did not fall; 557 plants stopped being counted.

**Independently falsified.** NYISO MIS P-63 publishes **no** separate solar
category — verified live against the source (seven categories; solar sits inside
`Other Renewables`). Decomposing per day into a night-hour baseline plus the
daylight bulge gives **0.212 / 0.577 / 0.994 TWh** — monotonic ~4.7x growth
against a 923 series claiming a 77 % collapse. (A lower bound on the 923
population, so it establishes direction, not level.)

**Two purpose-built guards both miss it.** `audit_eia923_completeness` audits
GAS+COAL only — *"renewables are scored on EIA-930"*, true for every ISO **except
the single `_EIA923_OVERRIDE` pair**; `solar` is absent from the committed NYISO
completeness part (which does correctly flag all six gas classes `incomplete`).
And `_backfill_renewables_eia930` opens with `if ann930 <= 0.0: continue`, keying
its repair on the very series that is zero. Everything else in NYISO 2025 **was**
repaired — wind 7.049 and hydro 24.104 (930 swap), biomass 0.672 (carry-forward),
all reproduced bit-for-bit — **solar 0.662 was the single unrepaired cell**.

**Blast radius.** Solar is not a C1-gated row (`score_fuelmix` scores only
GAS+COAL), so it never fired a FAIL; but it enters `_gen_totals`' `a_gen`, so
applying the repair moves `a_gen` +1.42 % and every fossil `share_pp` (CC_REGULAR
−0.37 pp, ST_GAS −0.17 pp, band ±3.0 pp). Material, not decisive.

**Fixed forward.** A class absent from CAMPD *and* EIA-930 *and* truncated by a
partial vintage is in biomass's position, so it now takes biomass's repair: the
prior complete year scaled by vintage completeness. Zero new parameters, gated on
the existing 0.90 threshold. **2023/2024 exact no-ops** (completeness 1.0495 /
1.0370); **2025 solar 0.6617 -> 2.5673 TWh**, so the statistic reads +38.5 %
instead of +437.1 %. Measured across 6 ISOs x {wind,solar,hydro} x 2023-25,
**NYISO solar is the ONLY zero-930-authority cell** — nothing else moves
(NEISO/PJM spot-checked identical). 4 tests added, 10 pass.

**The repair flatters the model, and that is not why it was made** (rules 1/13/21):
no free parameter, the byte-identical formula biomass already uses, a pre-existing
threshold, and an independent instrument established the old number was wrong
before the new one was computed. It is conservative — a carry-forward under-states
a growing class. **No committed keeper changes**: bench parts come from the
bundle's solve-time `eia923` input, so this applies to the next NYISO solve.

**Consequence for the queue.** The 2025 solar statistic is **barred from sizing or
judging any mechanism** — Item A's whole purpose. And **lever 2
(`hydro_budget_nameplate_aware`) is re-framed before it was ever sized**: NYISO
hydro's 2025 actual (24.104) comes from the **EIA-930 swap** while 2023's (28.031)
and 2024's (27.465) come from **EIA-923**, so the scope's "+1.3/+1.3/−12.7 %, a
miss ENTIRELY in 2025" is measured **across a benchmark-basis switch**. Any hydro
lever must first put all three years on one basis and re-measure what survives.
This is exactly the artifact shape the scope warned about, found before a solve.

**Found in passing — `OTHER` 2025 (+11.4 %) is a THIRD instance, REPORTED not
fixed.** `_reconciled_mustrun_class`'s docstring promises it is the single source
of truth for an injected residual class "**both the benchmark and the must-run
injection**" consume — but the benchmark half is hard-coded to `biomass`, so
`OTHER` is *injected* at the carry-forward level and *scored* against the raw
truncated vintage. NYISO 2025: model OTHER **1.9483** TWh = the carry
(2.2014 x 0.8850 = **1.9483**, exact to 4 dp) vs benchmark `classFull` **1.7487**
(10 plants vs 76). **On a consistent basis the error is exactly 0.0 %.** Not fixed
here because — unlike the solar repair, measured to a ONE-cell blast radius — it
moves **three** ISOs (CAISO +0.4173, NYISO +0.1996, NEISO +0.1618 TWh; ERCOT/PJM/
MISO sit above 0.90 completeness so nothing fires). A NYISO session should not
re-score CAISO and NEISO; named successor charter. **NYISO OTHER 2025 is likewise
barred from sizing or judging a mechanism.** ST_CHP 2025 (+85.0 %) needs nothing —
it is already audited `incomplete` (retention 0.667) and C1-**SKIPPED**.

### 2. Item B — `p25_cf` clamped, and nyiso-105 understated the defect

nyiso-105 reported the above-nameplate `p25_cf` as a property of the **refreshed**
artifact. It is **already live in every committed one**: MISO **17** rows, NEISO 3,
NYISO 2, PJM 3 (max 150.0; CAISO 0). Source:
`derive_thermal_tranches.py:555` clips available-CF at 1.5 for multi-unit CEMS
noise and `p25_cf` inherited that ceiling, while `committed_pct` / `mustrun_pct`
are capped at 0.70 / 0.60.

Clamped at **1.0 (nameplate)** in the deriver (`_P25_CAP`) **and** the accessor
(`campd_bins.thermal_tranche_p25_level`) — the latter so a *stale* artifact, which
is all of them, cannot inject an impossible floor without a re-derivation. The
ceiling is 1.0 and **not** `_COMMITTED_CAP`: the defect is physical impossibility,
not a large share, and since p25 >= p5 a 0.70 cap would collapse p25 onto the
committed level and destroy the mechanism it refines. Rule 23
`[R-FROZEN-DERIVE]`: physical-admissibility bug fix, not a residual re-derivation.

**Measured inert on every live keeper.** The only consumer is the ST_GAS per-plant
floor (`level > 0 AND online_frac > 0`). The sole breaching ST_GAS row anywhere
(NEISO Merrimack 150.0) sits in an artifact with **no `online_frac` column**;
MISO — the one ISO arming the `st_gas_mustrun_p25_level` + `st_gas_mustrun_per_plant`
pair — tops out at **67.4 %** across all 16 armable rows. After the clamp, **0
levels exceed nameplate in any ISO**; 149 tranche/binning tests pass.

**The artifact refresh itself is NOT done and stays chartered** — its prerequisite
is now met, but it still needs its own control arm and a solve.

### 3. What did NOT change

No mechanism tested; **no matrix verdict flips**; no `ScenarioConfig` field added
(so rule 28 duty (c) does not bite; `check_mechanism_matrix.py --base origin/main`
reports integrity OK). No keeper changed, no caveat slot spent, **zero fitted
parameters**. C3c untouched — not targeted, not claimed, not moved; the closed C3c
queue stays closed and the nyiso-104b frontier declaration stands. No run
registered on the dashboard, because no bundle was produced.

Evidence: `results/calibration/FINDING-nyiso106-solar-benchmark-vintage-2026-07-31.md`;
`results/calibration/_nyiso106_solar_benchmark_audit.json`.

Next shorthand: nyiso-107.

## nyiso-107 — the hydro miss is an INPUT truncation, not hydrology; `hydro_budget_nameplate_aware` provably inert; matrix keeper-stamp guard extended (2026-07-31)

**Keeper UNCHANGED: `2026-07-31-nyiso105-chp-heat-rates`** (CALIBRATED-WITH-CAVEATS,
0 FAILs, 1 ledgered caveat C3c — no slot spent). Measurement HEAD `3bfca72`,
rebased onto `b2192ef` before push; `data/hydro.py`, `config/constants.py`,
`run_calibration_full.py` and the NYISO keeper shard are all byte-unchanged
across that range, so no measured number moves. (`keepers/NEISO.json` did move —
neiso-71 promoted `2026-07-31-neiso-71-nucavail` and re-stamped its own header
correctly, so the new guard sees no additional drift.)
**Zero solves.** Scope Item B closed on measurement alone — the
nyiso-93/94/95/97/99/101/105/106 pattern. No pre-registration was needed because
no arm was solved. Probe: `scripts/probes/_nyiso107_hydro_basis_audit.py`;
evidence `results/calibration/_nyiso107_hydro_basis_audit.json`; finding
`results/calibration/FINDING-nyiso107-hydro-input-truncation-2026-07-31.md`.

The pending nyiso-106 header commit needed no action: `988dd47` had already
merged as PR #3222, so the NYISO stamp was correct on arrival. The ERCOT and
CAISO drifts were confirmed still open and **deliberately left to their lanes**.

### 1. Item B — the scoped question is answered, and its kill condition is NOT met

Item B's instruction was to put all three years on one basis and report what
survives, with "if little does, the lever is dead ex-ante". **The miss survives
every consistent benchmark basis:**

| benchmark basis | 2023 | 2024 | 2025 |
|---|---|---|---|
| as scored (mixed 923/923/930) | +1.26 % | +1.33 % | **-12.68 %** |
| all EIA-930 | +5.76 % | +3.93 % | **-12.68 %** |
| all EIA-923, carry-corrected | +1.26 % | +1.33 % | **-13.41 %** |

The basis switch is real and reproduced exactly (2025 vintage completeness
0.8850, 923/930 ratio 0.8529 < the 0.90 threshold, so only 2025 takes the swap).
But it is **not** the cause, because the benchmark is the **repaired** side.

### 2. The real defect: fed the truncated vintage, scored against the repaired one

The keeper carries `hydro_backfill_year=None` and `hydro_eia930_monthly=False`,
so **nothing repairs the input**:

| year | EIA-923 `HY` plants | LP units | **LP budget TWh** | max MW | model dispatch |
|---|---|---|---|---|---|
| 2023 | 157 | 154 | 28.4033 | 4,647.5 | 28.3833 |
| 2024 | 150 | 147 | 27.8750 | 4,587.1 | 27.8294 |
| **2025** | **4** | **3** | **21.0482** | 3,343.0 | **21.0482** |

The 2025 LP hydro fleet is **3 units** — 2.0 % plant retention — and the model
spends its budget **exactly** (21.0482 = 21.0482, 4 dp). So the scored -12.68 %
is arithmetically the truncation itself, `21.0482/24.1039 - 1`, with no dispatch
behaviour in it. Same one-sided-repair family as nyiso-106's solar and `OTHER`
findings, **inverted**: there the model was injected at the carried-forward level
and scored against the raw vintage; here it is fed the raw vintage and scored
against the repaired level.

**The benchmark is independently falsified as CORRECT.** NYISO MIS **P-63
publishes `Hydro` as its own category** — unlike solar, which forced nyiso-106
into a night-baseline/daylight-bulge decomposition — giving a direct
EIA-independent instrument: **27.1845 / 26.9763 / 24.2489 TWh**, agreeing with
EIA-930 to **+1.30 / +0.74 / +0.60 %** in every year. **NY hydro genuinely fell
~10 % in 2025**; the wrong number is the EIA-923 raw **20.5582**, 15 % below both
instruments.

### 3. The lever: `hydro_budget_nameplate_aware` NYISO `U -> I`, provably inert

**Structurally** — `load_hydro_budget:724` encloses the entire nameplate-aware
allocator in `if monthly_target_mwh is not None`, and `build_hydro_fleet:1084`
leaves `target=None` unless `eia930_monthly`/`forecast_budget`; both are `False`
on the keeper, so the flag is **never read** (its own docstring: *"Ignored when
`monthly_target_mwh` is `None`"*). **Empirically** — the hydro fleet built at the
keeper's exact settings is **BIT-IDENTICAL off vs on in all three years** (energy
sha `939797e1d578cee7` / `0e15d6a2cde4e79d` / `860247dfee9bd600`). Arming the flag
alone would have solved a bit-identical control.

Third ISO to reach `I` for the same structural reason after MISO (miso-109) and
PJM (pjm-143): **any ISO with no level target gets `I` by construction.** And it
stays trivial even after its prerequisite — under `--hydro-backfill-year 2024` the
allocator re-allocates 3,683.8 MWh over 10 clipped plant-months, **0.015 %** of a
24.06 TWh budget, annual total unchanged. The nyiso-105 item-6 lesson repeats:
**the arm is the pair, not the flag.**

### 4. NEW cross-ISO fact — NYISO is the sole material-hydro ISO running unrepaired

Every ISO's 2025 EIA-923 hydro vintage is truncated (2025 LP-unit retention:
ERCOT 8.3 / CAISO 16.2 / PJM 13.9 / MISO 8.8 / **NYISO 2.0** / NEISO 3.0 %), but
**four of six keepers arm the repair** — CAISO/PJM/MISO/NEISO all carry
`--hydro-backfill-year 2024` (PJM and MISO have the 930 pin internally refused for
the PS fold) — **and NYISO does not**. The only other holdout is ERCOT, whose
hydro is 0.017-0.463 TWh/yr and immaterial. **NYISO is the sole ISO running a
material hydro class (26.5 TWh/yr, ~18 % of generation) on an unrepaired truncated
input.**

Chartered, **not armed** (owner decision in-session). Two things a successor must
pre-register: the pair moves **all three years** (-1.5668 / -1.1287 / +3.0143 TWh,
since the flag is passed verbatim to every year), and a 930 level pin makes the
hydro **volume** statistic near-tautological (-0.17 % by construction once budget
and benchmark are the same series) — admissible under rule 13 as an inflow budget
that regenerates forward via `forecast_monthly_hydro`, but it must be **declared,
not banked as an improvement**; dispatch **shape** stays the free output. The
PJM/MISO posture (backfill without the pin) is a third option: 147 plants, input
and units on the same 923 `HY` population, at a +7.9 % 2025 overshoot.

Re-confirmed independently while there: NYISO's absence from
`EIA930_PS_FOLDED_INTO_WAT` is correct — `NG: WAT`/923-`HY` = **0.9448 / 0.9606**
(*below* 923 HY, opposite the MISO/PJM fold signature) and NYIS `PS` is net
**negative** (-0.372 / -0.410 / -0.490 TWh), so pumping is netted, not folded in
gross. The 2025 ratio inverts to 1.1452 purely by truncation — the
`hydro_level_923_hy` trap, re-verified and still not quotable.

### 5. Item A — put to the owner and DEFERRED

The cross-ISO `OTHER` basis asymmetry (matrix §5.5 item 11b) is fully measured
and one line in shape, but moves **three** ISOs' 2025 benchmark (CAISO +0.4173,
NYISO +0.1996, NEISO +0.1618 TWh). The owner declined the cross-ISO scope from a
NYISO lane; it stays chartered for a session that owns re-scoring CAISO and
NEISO. NYISO's `OTHER` 2025 +11.4 % remains barred from sizing or judging a
mechanism.

### 6. Found in passing and FIXED — the matrix keeper-stamp guard was blind

Rule 28 requires the promoting session to re-stamp `MECH_MATRIX.keepers[ISO]`,
but `check_mechanism_matrix.py` never compared that header against
`frontend/data/backcast/keepers/<ISO>.json`. **Three ISOs had drifted at once and
all three passed CI.** The guard now compares them, with a deliberate split:
pre-existing drift **WARNS** (it belongs to the owning ISO's lane — verified
`--base origin/main` reports ERCOT and CAISO and exits **0**, so main stays green),
while a PR that itself moves a keeper shard without re-stamping **FAILS** —
verified end-to-end on a throwaway commit touching `keepers/ERCOT.json`: ERCOT
escalated to `::error`, CAISO stayed `::warning`, exit **1**. 6 tests added
(`tests/unit/config/test_mechanism_matrix_keeper_stamp.py`), guard stays
stdlib-only.

### 7. What did NOT change

No mechanism armed; no `ScenarioConfig` field added (rule 28 duty (c) does not
bite); no keeper changed; no caveat slot spent; **zero fitted parameters**. C3c
untouched — not targeted, not claimed, not moved; the closed C3c queue stays
closed and the nyiso-104b frontier declaration stands. No run registered on the
dashboard, because no bundle was produced. The ERCOT and CAISO keeper-stamp
drifts were left open on purpose.

Next shorthand: nyiso-109.

---

## nyiso-108 — hydro input repair ARMED and PROMOTED; it exposed a real 2023 over-pricing (2026-07-31)

**2 solves** (same-HEAD zero-delta control + single-delta arm, three years each).
**Frozen HEAD `e1a4bc6`.** Keeper `2026-07-31-nyiso105-chp-heat-rates` ->
**`2026-07-31-nyiso108-hydro-input-repair`** (bundle `nyiso108_hydrorepair_B`).
Pre-registered and PUSHED (PR #3235) before either arm solved.

### 1. Scope Item A executed — the last material-hydro holdout is repaired

NYISO was the ONLY material-hydro ISO whose keeper ran on an unrepaired truncated
EIA-923 vintage. Its 2025 LP hydro fleet was **3 plants / 21.0482 TWh** against
147 / 27.8750 in 2024 on a 26.5 TWh class (~18 % of NYISO generation). Arming the
pair `--hydro-backfill-year 2024` + `--hydro-eia930-monthly` — a rule 14
[R-ACCURATE] input correction with **zero free parameters** (+1 DOF entry,
+0 residual), already armed on four of the six keepers — restores **147 plants /
24.0589 TWh**.

### 2. Construction adjudicated BEFORE the solve, against P-63

Level, against NYISO MIS P-63 (neither input nor benchmark): pinned
**-1.29/-0.88/-0.78 %** vs bare **+4.48/+3.33/-13.20 %** vs backfill-only
**+4.49/+3.33/+7.20 %**. Backfill-only was refused on **shape** as well: it
*degrades* the 2025 seasonal shape below the unrepaired keeper (P-63 shape r
**0.9251 -> 0.8265**) and puts the annual peak in March against P-63's May. The
PJM/MISO pin refusal does not transfer — it exists for a PS fold NYISO lacks.
Physically-unattainable plant-months fall **34/34/33 -> 14/20/10**.

### 3. Every construction gate passes; K2 on the STRICT BYTE basis

Control minus committed keeper = **exactly 0.0 MW** on every class in all three
years — no same-HEAD drift, so the A/B is unconfounded. K3: hydro moves
**-1.5505/-1.0904/+3.0107 TWh**. Fossil displacement is exactly 1:1
(2023 +1.5669, 2024 +1.1086, 2025 -3.2302 TWh). Slack and dump 0.0 in both arms.

### 4. THE COST: C3a 2023 +8.6 % -> +10.2 %, and NYISO regresses to NOT-YET

A **0.2 pp** breach of the ±10 % band. It is a **DISCOVERED** defect, not a created
one: EIA-923 raw 2023 sits **+3.11 % above** P-63 while the armed level sits
-1.29 % below it, so the keeper was carrying **~1.55 TWh of phantom zero-MC 2023
hydro that was SUPPRESSING a real 2023 fossil over-pricing**. Rule 14 forbids
reverting the accurate input to restore the PASS. Same signature PJM promoted at
pjm-143. **Promotion is an EXPLICIT OWNER OVERRIDE of this session's prereg §6**,
which pre-committed no-promotion-on-new-FAIL; recorded as an override, not as the
prereg's verdict.

Also explained and deliberately NOT corrected: the pinned level's consistent
-1.29/-0.88/-0.78 % residual vs P-63 is NYIS's netted pumping inside `NG: WAT`
(predicted -1.33/-1.49/-2.38 %, matching 2023 to 0.05 pt). A reconciliation factor
would be a fitted adjustment (rules 5/21).

### 5. The frontier: the C3c declaration STANDS, its PREMISE does not

C3c is **BIT-IDENTICAL** across arm and control (model 3/0/7 h vs actual
10/12/42 h >$300), so no C3c evidence moved, the exhausted-queue finding and its
re-open condition carry forward unchanged, and **no caveat slot is spent**. What
lapses is nyiso-104b's premise that *C3c was the SOLE blocker*. NYISO now has a
second, non-C3c, tractable blocker. **NYISO is no longer at a frontier in the
sense of "options exhausted" — it is back in active calibration.** Holdout
unaffected: `complete` kept, absent from `final`, spend freeze ACTIVE.

### 6. What did NOT change

C1 stays **14/14 all-class, 10/10 free-class** in both arms. C2/C3b/C4/C6/C7/C8
PASS in both. No ScenarioConfig field added. No out-of-training year touched.

### 7. Named successor

**nyiso-109: the NYISO 2023 fossil over-pricing, now visible at +10.2 %** — an
offer-stack / fuel-basis root cause, NOT the hydro input, which is now correct
and must not be re-tuned to bury the miss.

Recorded honestly: two measurement bugs in this session's own REPORTED (non-gating)
diagnostics — the A/B scorer's `hydro_lp_units` counts rows not distinct units, and
its `_tail_hours` returns 0 for a control whose committed C3c is 3/0/7 h, so it does
not reproduce the scorer's tail basis. The authoritative C3c comes from
`calibration_verdict.py`. Environment: a fresh container also needs a full
`scripts/regenerate_clean.py` (48 datatypes) beyond the two documented commands.

`results/calibration/FINDING-nyiso108-hydro-input-repair-2026-07-31.md`.

Next shorthand: nyiso-109.

---

## nyiso-109 — the 2023 C3a breach was an identification-GRAIN error; NYISO recovers to CALIBRATED-WITH-CAVEATS (2026-08-01)

**2 solves** (same-HEAD zero-delta control + single-delta arm, three years each).
**Frozen HEAD `1aad56a`** + this session's mechanism commit. Keeper
`2026-07-31-nyiso108-hydro-input-repair` -> **`2026-08-01-nyiso109-zonal-margin-anchor`**
(bundle `nyiso109_zonalanchor_B`). Pre-registered and PUSHED before either arm was
scored. **This promotion is the pre-registration's OWN verdict** — every construction
gate K1-K6 and every kill gate P1-P5 passed; no owner override was needed or used.

### 1. The lever: the margin anchor's identification GRAIN, not a tuning knob

`apply_gas_offer_margin` adds `markup_hr x (anchor - fuel)` and states its own
identity — *at `fuel == anchor` the reformed offer reduces EXACTLY to the registered
band multiplier* — which is a statement about a unit's **own** delivered fuel. But
`GAS_OFFER_MARGIN_ANCHOR_BY_ISO` is derived from `_gas_series`, which is **ISO-level**:
it carries the hub overlay but NOT the per-zone basis the solve applies afterwards on
the `(n_gen, T)` array. On the five ISOs without a zonal spread that is the same
series. On NYISO it is not: `apply_nyiso_zonal_gas_basis` leaves the REFERENCE zone
(Capital_Hudson / Iroquois Z2) unchanged and shifts every other zone strictly DOWN to
its own measured pipeline hub — NYC to Transco Z6 NY, Upstate_West to Tenn Z4 200L,
measured offsets **-1.34/-0.71/-1.38** and **-1.46/-1.07/-3.08** $/MMBtu. Two of five
zones, carrying **67.6 % of NYISO load**, were pricing their markup at a fuel level
they never pay and collecting an uplift their band multiplier never contained.

Zone anchors — **Upstate_West 2.0346, NYC 2.7612, reference zones 3.9046 unchanged** —
are the SAME measurement as the ISO anchor evaluated per zone, produced by the same
derive script (`derive_gas_offer_margin_anchor.py --by-zone`) applying the RUNTIME
zonal-basis transform to the same delivered series over the same 2023-2025 window.
**Zero free parameters** (+1 DOF entry, +0 residual; 26 -> 27 entries, `n_residual` 6).
Rule 19: a band-scoped rebasis anchor keeps precedence, so the channels never stack.
Rule 25: the registry carries NYISO ONLY and hard-fails elsewhere. In the solve,
**234 of 404** marked-up tranches move onto a zone anchor and the median fixed margin
falls **6.04 -> 5.39 $/MWh**.

### 2. TWO handoff premises CORRECTED by measurement

**(a) The defect is NOT 2023-specific.** The residual is a COMPRESSED price
distribution present in all three years: the model reproduces only **69/49/45 %** of
the measured trough->peak swing, the trough is over-priced by **+7.3/+5.5/+8.7 $/MWh**
and the peak under-priced in 2024/2025. 2023 failed alone only because it is the mild
year whose peak error is ALSO positive (+3.01), so nothing cancelled the trough excess.
Same defect PJM diagnosed at pjm-141 — measured here independently on NYISO's own data.

**(b) The congestion route is REFUSED ex-ante on NYISO's own measurement**, no solve
spent: `measured_interface_limits` NYISO **U -> G**. The premise is real (the model's
Upstate->Capital link separates in 12.0/1.3/1.1 % of hours against a real
60.3/54.8/38.2 %), but the REAL `CENTRAL EAST - VC` sits within 50 MW of its posted
limit in **0.8/0.1/0.2 %** of hours and TOTAL EAST / UPNY CONED / SPR-DUN-SOUTH in
**0.0 %**, while the model's monthly TTC already tracks the measured monthly mean limit
(2023 model 1950..2725 vs measured 1918..2699 MW) and the model's own link is AT that
envelope in 16.1/1.7/1.4 % of hours. The posted limit is not what produces the real
separation — marginal losses plus SUB-INTERFACE nodal constraints are, neither
representable at five-zone grain (rule 14's misalignment clause).

### 3. Every gate passes; K2 on the STRICT BYTE basis, and stronger than nyiso-108's

Control minus committed keeper = **exactly 0.0 MW** on every class-hour in all three
years — **despite four solve-path commits landing on main since that keeper's HEAD**
(`data/hydro.py`, `data/fleet/arrays.py`, `model/reserves/spec.py`), whose NYISO
inertness the prereg recorded as a falsifiable expectation and the control did not
falsify. K3: system lambda **-0.871/-0.609/-0.602 $/MWh**. K6 direction integrity: no
zone's lambda RISES anywhere, as the construction requires. Slack and dump 0.0 in both
arms, all years.

### 4. RESULT and the reported cost

**C3a 2023 +10.21 % -> +7.51 %**, inside the +/-10 % band; C3a PASSES in all three
years (2024 +1.05 -> -0.55, 2025 -8.73 -> **-9.64**). Determination **NOT-YET ->
CALIBRATED-WITH-CAVEATS** (7 target-grade / 1 FAIL -> **8 / 0 FAILs**, 1 ledgered).
C1 stays **14/14 all-class, 10/10 free-class**; C2/C3b/C4/C6/C7/C8 PASS in both arms;
**C3c bit-unchanged** (3/0/7 h vs actual 10/12/42).

**The cost is reported, not hidden:** C3a 2025 moves nearer the band edge. That is the
honest signature of §2(a) — this lever corrects the TROUGH half of a sign-symmetric
amplitude defect and the PEAK half stays open. The expected direction (weakly downward
by construction: every zone anchor <= the ISO anchor, every markup >= 0) was
**pre-registered as grounds for EXTRA scrutiny, not encouragement** (rule 1, both
directions); the lever is defended on the arithmetic of the mechanism's stated
identity and would have been correct had C3a not moved at all.

### 5. The frontier: C3c STANDS and its PREMISE is RESTORED

C3a passing in all three years makes C3c once again the SOLE miss, carried as ONE
ledgered caveat, so the nyiso-104b declaration's premise holds again. C3c evidence is
bit-unchanged, so no caveat slot is spent and the re-open condition (Capital_Hudson ->
Zone-F/Zone-G topology split, owner charter) is unchanged. **What is NOT restored is
the "options exhausted" reading** — the compressed-distribution defect is real, open,
and passes every current gate, so it is an open item rather than a blocker. Holdout
unaffected: `complete` kept, absent from `final`, spend freeze ACTIVE.

### 6. Cross-ISO exposure: measured, REPORTED, not acted on

ERCOT, PJM and MISO also arm a zonal gas basis on their keepers, so the same grain
mismatch exists in their lanes; their cells enter as **U** and each needs its own
derived table and A/B (rule 25). CAISO and NEISO arm none (n/a). ERCOT partially
self-corrects via the flat EP-basis level term `_gas_series` already adds. Nothing
outside NYISO is touched and no other keeper moves.

### 7. Recorded honestly rather than dropped

This session's OWN pre-registration §1.3 says the model's Upstate->Capital link
"separates in 0.0 % of hours in all three years". That is true only on the
covered-actual-hours subsample at a $1 threshold; full-year it is 12.0/1.3/1.1 %. The
refusal in §2(b) does not depend on it — it rests on the real-world flow-vs-limit
statistic — but the sentence was wrong as written and the `flows.parquet` measurement
that corrects it only became available once this session's own arms were solved.

### 8. The marginal-rung census confirms the diagnosis and names the term

The pjm-141 marginal-set test re-derived on NYISO's own fleet (no LP, detection
99.1-100 %): the trough marginal tranche is **`econ` 80.5/81.1/80.8 %**, dominated by
`CC_REGULAR:econ` 54.0/50.9/42.2 %, and the **peak control is the same family**
(84.5/83.5/85.2 %) — no floor rung, no part-load artifact at the margin. The marginal
trough rung's offer decomposes as burn + VOM + a **residual markup of
$6.84/$10.13/$9.24** at a fuel of 2.755/2.089/4.072 $/MMBtu: **the markup is largest
exactly where the fuel sits furthest below the 3.9046 ISO anchor**, which is
`markup_hr x (anchor - fuel)` read straight off the price-setting rung. Also measured
and reported: **within-day offer variation is EXACTLY zero** (sigma $0.000000; the
cap-weighted offer at trough equals the peak to the cent, 77.10/79.68/92.08), so all
diurnal amplitude must come from merit-order traversal — NYISO reproduces pjm-141's T6
finding on its own fleet; and the model does not lack a cheap offer (cheapest thermal
$1.40 against a measured trough p05 of 14.60/14.23/19.96) but lacks **depth**, with only
8.0/7.7/8.2 GW of 25.0-25.6 GW available below that target.

### 9. Test baseline at this HEAD

`tests/{curation,scoring,unit}` after a full `regenerate_clean`: **14 failed / 4419
passed / 14 skipped / 1 xfailed** in 11m56s — `test_measured_chp_heat_rates.py` 7, three
cache-key byte-stability tests, `test_consume_lmp.py` 1, `test_ff_readiness_battery.py`
1, `test_outages.py` 1, `test_clean_io.py::test_datatype_list_matches_schemas` 1. Thirteen
are nyiso-108's baseline verbatim; the fourteenth is a datatype/schema registry mismatch
on main and this branch touches no `clean_io`/schema/`regenerate_clean` file. **The three
cache-key failures were checked rather than assumed**, because this session adds two
`ScenarioConfig` fields: the default `ScenarioConfig().cache_key()` is
`0e9fce2fb55b889f` on BOTH `origin/main` and this HEAD, so the new fields are correctly
registered and the tests fail against a literal that was already stale on main. **11 new
tests** land with the mechanism, all passing.

`results/calibration/FINDING-nyiso109-zonal-margin-anchor-2026-08-01.md`.

Next shorthand: nyiso-110.

---

## nyiso-110 — the peak half DECOMPOSED: missing everyday reserve-price formation, dollar-for-dollar; the C3a PASS is a cancellation; the flag-only spin-online arm pre-registered (2026-08-02)

**Zero solves at diagnosis time; keeper UNCHANGED
(`2026-08-01-nyiso109-zonal-margin-anchor`).** The nyiso-109 named successor —
DIAGNOSIS + PREREG lane, solve only behind its own pre-registration. Probe:
`scripts/probes/_nyiso110_peak_half_decomposition.py` (A–D committed artifacts
only, seconds; E replays the keeper fleet per year, no LP). Machine output:
`results/calibration/_nyiso110_peak_half_decomposition.json`. Finding:
`results/calibration/FINDING-nyiso110-peak-half-decomposition-2026-08-02.md`.
Prereg: `results/calibration/PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md`
(committed and pushed BEFORE either arm solved).

### 1. The decomposition (task a)

The handoff asked how much of the peak-half miss is reserve/scarcity formation
vs offer-surface level vs the systemic amplitude signature. Answer, measured on
the keeper's own sidecars + NYISO's own posted AS prices (rule 25):

* **Reserve formation DOMINATES.** The keeper's co-opt reserve dual is > $0 in
  **17/6/34 hours** of 8,760 (peak-window mean $0.11/$0.06/$0.44); the measured
  DA spin price is > $1 in **100 %** of peak-window hours (LW mean
  $9.72/$8.62/$17.46, censoring at $200 moves it ≤ $1.2). The peak−trough
  reserve differential covers **64–89 %** (DA) / **97–131 %** (RT, upper bound)
  of the missing swing; hourly passthrough slope of the peak miss on the
  measured spin ≈ **1** (DA +1.15/+1.31/+0.75; RT censored +0.77/+1.02/+1.09).
* **The C3a PASS is a CANCELLATION.** Strip the measured spin content from the
  actual and the model's energy side over-prices BOTH ends (RT energy basis:
  trough +5.74/+3.52/+4.21, peak +7.29/+3.16/+5.33) with an energy-only swing
  ≈ 100 % of the reserve-stripped actual (RT). Full-content formation would
  land C3a-2023 ≈ +15 % — the level gate penalizes the structural repair. The
  sharpest input yet to the OPEN owner amplitude-criterion call (xiso-1 §6);
  surfaced, not decided, scorer untouched.
* **The energy-side/offer leg is the smaller DA residual (~10–35 %).** The
  actual DA peak is INSIDE the model's stack in 100.0 % of peak hours (top
  $410–475); 1.33/1.38/1.68 GW sits priced between the model's clearing price
  and the actual; the peak marginal set is `econ` **83.2/83.7/85.2 %** — the
  trough's own family (nyiso-109 §8 reproduced on the keeper). Model thermal
  at peak = **0.936/0.936/0.933 ×** measured (EIA-930 gas+oil,
  zero-dropout-screened): the LP's perfect-foresight hydro over-peak-shaves,
  §5.5 item 8's territory, not a new lane.
* **Winter surplus beyond reserve** (DJF DA miss +8.08/+11.27/+32.00 vs DJF
  peak spin 9.43/9.79/18.72) — item 4's blocked territory, sequenced behind
  the arm.

### 2. The adjudication (task b): pre-register ONE lever, off-queue with cause

The §5.5 queue holds no admissible peak-half lever. The E4 liveness census
(caiso-144 pattern, run to close the route ex-ante if dead) came back **LIVE**:
hydro's zero-cost headroom (armed reserve-eligible; held reserve spends no
water) covers the 655 MW NYCA spin requirement in only **51/36/39 %** of
peak-window hours (82–89 % of all hours) — so an online-gated spin family has a
formation channel concentrated exactly where the content is missing, and is
slack at the trough. **Pre-registered:** the flag-only
**`nyiso_spin_reserve_online`** single-delta arm on the keeper recipe — zero
new DOF, no code change. nyiso-84's adjudication is superseded on both grounds
by new evidence, cited against vintage: it scored C3c depth only (not
contested), and its census ran at the pre-hydro-repair HEAD (2025 hydro = 3
plants) — on the repaired keeper the recorded overnight-GT-forcing objection
no longer reaches the hours it fired in, and kill P4 re-kills the arm if the
signature reappears anyway. Kill P1 is the pre-registered C3a-2023
un-cancellation breach (> +10 %); K3's liveness floor (500 dual-hours/yr)
routes an under-forming arm to INERT, which would charter the nyiso-84
class-widening build with this arm as its control evidence.

### 3. Rule-28 duties discharged

Matrix: header re-stamped; `diurnal_price_amplitude` NYISO stays **O** (lane
ACTIVE behind the prereg), note + ev extended; `nyiso_rcpf_family` note
extended (re-open on new evidence, cell stays K); `energy_reserve_coopt` note
gains the NYISO dormancy sizing (cell stays K). §5.5 header + STATUS block +
item-4 note; §5.7 xiso-1 entry annotated. `check_mechanism_matrix.py
--base origin/main` passes. No dashboard registration from the diagnosis
itself (no run existed when it was written); the A/B that follows registers
BOTH arms whatever the verdict (rule 15), full span in one invocation each
(rule 16), post-steps in order, LOYO duty per rule 22.

### 4. OUTCOME (same session): the arm SOLVED — INERT by its own K3 rule; the family is exhausted

Both arms solved at the rebased HEAD (after the ercot-150 landing) and
registered: `2026-08-01-nyiso110-control-zerodelta` /
`2026-08-02-nyiso110-spin-online-inert` (retention pruned nyiso-92-control +
nyiso-92-hydro-envelope). Gate scorer
`scripts/probes/_nyiso110_spin_online_ab.py` →
`results/calibration/_nyiso110_spin_online_ab.json`. **K1/K4 pass** (exactly
one config delta, flag recorded); **K2 = 0.0 MW** max class-hour delta (the
control byte-reproduces the keeper — main's ercot-150 commits NYISO-inert, as
pre-registered); **K3 FAILS → INERT**: reserve-dual hours identical to control
(17/6/34 vs a 500/yr floor), C3a +0.006 pp, swing unchanged to 3 dp, class
deltas ≤ 4 GWh degenerate-vertex noise (K6's sub-$2 wobbles likewise). No kill
fired; nothing to kill.

**The E4 liveness reading is CORRECTED on the record** (the nyiso-109 §7
discipline): the census tested hydro *headroom* (the per-gen binder) while the
as-built class-2 gate is an **aggregate** ρ·output row — reserve-eligible
hydro's own output (2–5 GW × ρ ≥ 0.5) keeps it slack in every hour and idle
quick-start capacity stays admissible per-gen. The same arithmetic refutes the
nyiso-84 class-widening successor ex-ante (widening only adds slack; a per-gen
re-scoping stays slack on hydro's certified output; excluding NYPA hydro would
falsify real eligibility, rule 14). With reserve offers unpublished, MIP
forbidden, withholding a rule-19 stack and congestion G, **the in-LP
reserve-formation family at NYISO is exhausted** — the everyday reserve-price
content (64–131 % of the missing swing) forms only from availability offers
and sub-hourly co-opt dynamics an hourly LP cannot carry.

**`diurnal_price_amplitude` NYISO O → G** (the PJM/MISO no-build class);
re-opens behind the owner amplitude-criterion call (now carrying the
cancellation fact AND this exhaustion), an owner-funded reserve-offer /
sub-hourly intake, or item 8's Robert Moses resolution (the energy-side hydro
leg). **Keeper UNCHANGED** (`2026-08-01-nyiso109-zonal-margin-anchor`); the
arm is NOT a keeper candidate (live-inert — the owner's structural-integrity
license has nothing to attach to). Item 4 stays blocked (its candidate joint
summer lever died with the arm). FINDING §10 carries the full addendum.

Next shorthand: nyiso-111.

## (stub) caiso-155 — 2026-08-02 — NYISO: the HQ firm floor (7.884 TWh/yr) becomes D-2/D-4-visible; a latent G-06 false-FAIL averted

Cross-ISO scorer audit (main entry: `docs/calibration-log/caiso.md`
caiso-155). `NYISO_external_HQ_hydro` (900 MW flat, 7.884 TWh/yr,
MECH_FIRM_IMPORT) was dropped by the D-2/D-4 plant matrix — fixed
ISO-generically; the row appears on any faithfully-floored artifact
generation (the keeper's committed artifact is unchanged this session: both
regen instruments failed their pre-registered gates, see FINDING §D/§E).
Also fixed for NYISO's benefit: the G-06 recompute now subtracts the whole
P0-pattern bridge family — nyiso109's committed CC_REGULAR gated share
carries 5.31/3.14 pp of `nyiso_gas_commitment_bridge` forcing no fleet_only
rebuild can reproduce, so the RA-only carve-out would have false-failed a
faithful keeper on the full `--keepers` recompute. `MECH_NYISO_SELFSUPPLY`'s
missing D4_WINDOWS row is FILED, not minted (it rides real plants — not part
of this defect; non-thermal, never gated).

---

## nyiso-111 / nyiso-112 — the CROSS-ISO TRANSFER SWEEP: two candidates refused ex-ante on NYISO's own data, two keepers promoted, and the first C3c movement since the queue was declared exhausted (2026-08-02)

**Keeper `2026-08-01-nyiso109-zonal-margin-anchor` → `2026-08-02-nyiso111-ramp-envelopes`
→ `2026-08-02-nyiso112-ramp-plus-peaker`.** Both promotions are their
pre-registrations' own verdicts (`PREREG-nyiso111-ramp-envelopes-2026-08-02.md`,
`PREREG-nyiso112-nysdec-peaker-rule-2026-08-02.md`, both committed and pushed
before any arm solved). Finding:
`results/calibration/FINDING-nyiso111-ramp-envelopes-2026-08-02.md`.

### 1. Why the transfer candidates

nyiso-110 left the §5.5 queue with no admissible peak-half lever
(`diurnal_price_amplitude` NYISO `O → G`). So this session worked rule 28 §4:
the matrix cells where NYISO reads `U` and another ISO reads `K`.

### 2. Two refused ex-ante, on NYISO's own measurement (no solve spent)

* **`temp_dependent_derate` `U → G`.** The miso-101 identification re-run on NY
  CAMPD does not identify: 2 of 15 candidate cogens clear the floor, the
  capacity-weighted p50 within-day slope is **−0.00745/°C (wrong sign)**, the
  near-pinned plant measures −0.000086 at r = 0.006, and **phase validation
  fails at best lag −5 h** against MISO's confirmed 0. It is reading NYC's
  air-conditioning dispatch shape, not an ambient capability response.
* **`hydro_ror_split` `U → G`, queue item 8 CLOSED.** The committed classifier
  flat-pins **73.1 %** of NYISO conventional-hydro MW (Robert Moses Niagara
  alone 51.9 %), leaving a 1,261.6 MW shapeable bound that NY's own measured
  hour-of-day swing exceeds in every year (1,291.9 / 1,396.8 / 1,792.2 MW =
  1.02 / 1.11 / 1.42×; median-day 1.19–1.53×). EHA itself files the peaking
  machinery as a separate plant (Lewiston, EIA 2692, `Mode = Peaking`, 240 MW),
  so the hybrid label describes hydraulics, not shapeability. Direction is wrong
  too: the keeper over-peaks hydro by only +293 / +242 / +204 MW at h17–19.

### 3. nyiso-111 — the pjm-140 `ramp_envelopes` transfer, PROMOTED

NYISO's artifact derives for the first time (77 rows / 48 well-observed plants;
CC up-envelope median 0.49 × pmax, ST 0.42, CT 0.92). pjm-140's all-ISO lesson
was honoured, not rediscovered: the class-aggregate pre-check is reported
**uninformative** (1 hour of 26,280) and the bound-against-the-bound test is the
one quoted — the superseded keeper's own dispatch crosses the envelope in
0.96 / 1.26 / 0.75 % of ~543k group-transitions carrying 225,117 / 291,437 /
274,134 MWh/yr, a crossing rate **2.1–3.0× PJM's**. Arming cuts it to 3,888 /
4,717 / 7,062 MWh (**−98.27 / −98.38 / −97.42 %**). K2 control integrity is
**0.0 MW** on the strict byte basis. Price effect near-inert exactly as
pre-registered; promoted on rule 1 / rule 14, not on gate movement.

### 4. nyiso-112 — the NYSDEC 227-3 peaker rule, PROMOTED, and C3c moves

Off-queue with cause: the mechanism had **no matrix row at all** (rule 28(c)
gap), was armed exactly once at nyiso-46 inside a three-mechanism probe that
stayed a probe for unrelated reasons, and carries **no rejection anywhere in the
record** — every bundle since read `false`. Rule 19 checked by measurement: the
CAMPD outage overlay does not already zero these units.

**C3c 2025: 7 → 14 hours >$300 against a measured 42** (2023/2024 unchanged at
3/0), C3a in band all years with 2025 moving toward band centre, K4 window
fidelity exact (out-of-window delta 0.0 MWh every year), zero slack and dump.
The caveat is not retired; its worst year improves for the regulation's own
dated reason.

### 5. Standing lesson

The exhausted-queue finding was true of the queue, and the queue was
incomplete. **A solve-affecting field with no matrix row is a mechanism nobody
can see** — worth a sweep in every ISO lane.

Next shorthand: nyiso-113.

---

## nyiso-113 — THE RULE-28(c) MATRIX-GAP SWEEP: 13 rows added, three cells adjudicated with no solve, the 227-3 phase reading inverted, and the published Zone-K reserve ladder PROMOTED (2026-08-02)

**Keeper `2026-08-02-nyiso112-ramp-plus-peaker` → `2026-08-02-nyiso-113-li-locational`, CALIBRATED-WITH-CAVEATS.** Pre-registration
`PREREG-nyiso113-li-locational-reserve-2026-08-02.md` (committed and pushed
before either arm solved). Finding:
`results/calibration/FINDING-nyiso113-matrix-gap-sweep-2026-08-02.md`.
Registered: `2026-08-02-nyiso-113-control-zerodelta` +
`2026-08-02-nyiso-113-li-locational` (both non-keeper; retention pruned
nyiso-98-nucavail + nyiso-99-demandfix).

### 1. The sweep — the nyiso-112 lesson made mechanical

nyiso-112's standing lesson ("a solve-affecting field with no matrix row is a
mechanism nobody can see") became an instrument: every `ScenarioConfig` field
imported from the live class, crossed against `mechanism-matrix.js`, classified
`own_row` / `prose_only` / `absent` — matching on the **stem**, because the
matrix's own convention is that rows are ISO-neutral mechanism FAMILIES and a
per-ISO flag is that ISO's leg.

**25 `nyiso_*` fields absent, 5 prose-only, 17 of them ARMED ON THE KEEPER WITH
NO CELL ANYWHERE** — four of those declared in the keeper's own DOF ledger and
still cell-less. **CI never caught it because the diff gate only fires on fields
added in the same PR**: everything predating the gate is invisible to it. That
is a standing blind spot in every ISO column, and the sweep is cheap.
**13 rows added**, 1 cell updated.

### 2. Three cells adjudicated, NO SOLVE SPENT

* **`nyiso_east_reserve_families` → I.** Provably inert by domination algebra:
  `east_10min_spin` (330 MW, class 1) is dominated by `nyc_10min_total`
  (500 MW, NYC ⊂ East) by 170 MW and by `east_10min_total` (1,200 MW) by 870 MW;
  `east_30min_total` (1,200 MW, class 0) by `seny_30min_total` (1,300 MW,
  SENY ⊂ East) by 100 MW. Arithmetic on the family rows, not empirical.
* **`measured_ramp_capability` NYISO U → I.** Fleet 10-minute deliverable ramp
  12,318.4 MW = **18.8×** the 655 MW NYCA spin requirement.
* **`nyiso_spin_reserve_online` → I.** nyiso-110's solved verdict finally has a
  cell to live in.

### 3. `nyiso_li_locational_reserve` — SOLVED, LIVE, C3c unchanged

The published Zone-K ladder (120 MW 10-min; 270/540 MW 30-min at $25/MW),
absent from the model entirely — a rule 14 omission, zero DOF. It clears the
rule-19 gate on NYISO's own data: not dominated (no armed family is Zone-K
scoped), and the nyiso-110 hydro-slack refutation **cannot reach it** because
NYISO hydro is 100 % upstate (Upstate_West ~4.0–4.1 GW, Capital_Hudson ~0.55 GW)
while **Long Island carries exactly 0.0 MW**.

K1 PASS, **K2 PASS byte-identical** (0.0 MW over 122,640 class-hours × 3 years).
The family **binds exactly where its own requirement says it should**: Zone-K
headroom falls below the hourly requirement in exactly 5 hours of 2025
(h4193–4195, h4217–4218 — the June 24–25 event, the five highest LI prices) and
0 hours of 2023/2024 once the on/off-peak step is honoured; the solved reserve
dual moves in exactly those hours. Effect is small — **2025 LI max 483.37 →
489.62 (+$6.25)**, everything else unchanged, zero slack and dump. **C3c
UNCHANGED at 3/0/14.**

**PROMOTED (cell K).** Determination **CALIBRATED-WITH-CAVEATS**, C3c the sole
ledgered caveat. **No kill gate fires and every scored criterion is identical to
the same-HEAD control's** — C1 14/14 all / 10/10 free, C2, C3a, C3b, C4, C6, C7,
C8 all PASS in both arms; C3c FAILs in both at 3/0/14. Ledger 29 → 30 entries,
`n_residual` unchanged at 6, zero free parameters added. Promoted on rule 1
`[R-STRUCT]` / rule 14 `[R-ACCURATE]`, not on gate movement.

### 4. The 227-3 phase reading, INVERTED

The received read was that only the 2025 phase touches binding downstate
capacity. The opposite is true: the **2023-05-01 phase removes 203.1 MW of which
145.5 MW (72 %) is Long Island**; the **2025 increment is 14.5 MW, all NYC, none
on LI** (Astoria 1 and Arthur Kill GT1 are no-ops, absent from the fleet
vintage). And the 2023 phase did **not** do nothing — it moved 570 LI hours, all
inside the ozone window, lifted the LI max 400.07 → 503.74 and moved >$250 from
7 → 10. It simply did not cross the $300 line C3c counts. **2024 is the genuinely
inert year, and its three highest LI hours are pinned at $297.54 in both arms —
$2.46 below the gate.** C3c-2024 currently turns on $2.46.

### 5. Two corrections this session owes its own record

1. **The pre-registered K3/K4 instrument was invalid.** Both were specified on
   the per-zone `reserve_price` column, which is a **system-level `(T,)` series
   broadcast identically to every zone** (`run_calibration_full.py:925/1028`) —
   0.0 across zones by construction, incapable of observing a locational dual.
   The arm's first reading ("INERT") was an artifact. Gates re-run on unit-hourly
   headroom and the solved dual's timing. **This retracts the screen's "no
   locational family has ever bound" claim**; the east-families domination
   verdict is untouched.
2. **A capacity-vs-demand screen is not a headroom screen.** The prereg argued
   from LI peak demand (5,537 MW) exceeding Zone-K thermal nameplate
   (5,146.5 MW) to a headroom collapse. Invalid: class 1 is **idle-allowed**, and
   **Long Island imports a large share of its own peak**, so Zone-K quick-start
   headroom never falls below **3.2×** the 120 MW requirement. Generalises to
   every importing zone in every ISO.

### 6. Standing gap for every ISO

**No bundle persists a per-family reserve dual.**
`DispatchResult.reserve_price_by_family` exists in memory and is discarded at
persist time, so no locational reserve family's binding is observable from a
committed bundle in any ISO. Every claim of the form "family X never binds" rests
on the aggregate series or a re-solve. A per-family dual sidecar is the
prerequisite for adjudicating locational reserve mechanisms from bundles — and
the array already exists.

## 2026-08-03 — nyiso-114: the per-family reserve dual is PERSISTED (all-ISO gap closed); the census run in six lanes + a CI ratchet; two dead knobs removed

Keeper **UNCHANGED** at `2026-08-02-nyiso-113-li-locational`. This session
promotes nothing, demotes nothing and re-keys nothing.
`results/calibration/FINDING-nyiso114-reserve-family-sidecar-2026-08-03.md`;
`PREREG-nyiso114-reserve-family-sidecar-2026-08-03.md` pushed before any solve.

### 1. The instrument (item 1 of the brief) — §6's standing gap, closed

`hourly/reserve_family_<year>.parquet`, long form, one row per (family, hour):
`family`, `reserve_class`, `dual`, `requirement_mw`, **`held_mw`**,
`shortfall_mw`. Two new LP outputs: `shortfall_mw` partitions the family-major
ORDC block by an `(n_steps, n_fam)` membership matmul (`reduceat` collides
boundaries for a zero-step family), and `held_mw` is the **balance row's own
activity** minus that shortfall — taken from the activity rather than by
re-summing R columns, because the row's coefficients are layout-dependent
(per-class blocks, storage RS columns, per-generator product masks, ERCOT's
all-class family) and each layout is a chance to mislabel a family.

Together they make the LP row **checkable from the bundle**: `held + shortfall ≥
requirement`, tight exactly where the family prices. `held_mw` was added
mid-session precisely because the pre-registered G3 gate would otherwise have
been unmeasurable from committed artifacts — the same error class as nyiso-113's
K3/K4, caught before it shipped.

Instrument, not a lever: no `ScenarioConfig` field, no CLI flag, no LP row or
column, zero free parameters, read off the already-solved primal. The writer
refuses to emit a frame on a family-count mismatch (no sidecar beats a
mislabelled one). **46 KB per ISO-year.** Not backfilled — written forward.

### 2. What it shows, and the correction it forces

| family | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| `nyc_10min_total` | **17** | **6** | **29** |
| `nyc_30min_total` | **8** | **6** | **10** |
| `seny_30min_total` | **2** | 0 | **8** |
| `li_30min_total` | 0 | 0 | **5** |
| `li_10min_total`, all three `nyca_*`, `east_10min_total` | 0 | 0 | 0 |

NYISO's binding reserve constraint is **overwhelmingly the NYC locational pair**,
and **every NYCA-wide family is slack in every hour of all three years** — a
direct measurement of what nyiso-110 could only infer from the summed series.

**P1 CONFIRMED EXACTLY:** `li_30min_total` binds in exactly 2025 h4193–4195 and
h4217–4218 — the five hours nyiso-113's Zone-K headroom screen predicted *ex
ante* — and in no other hour of any year. **P3/P4/P2 CONFIRMED. P5 REFUTED:**
nyiso-113 §7 attributed 2023's two reserve-dual hours to the LI mechanism; the
per-family dual says the LI families bind in **zero** hours of 2023 and those two
were **`seny_30min_total`**. An error in reading a summed series, not a defect in
the keeper (whose promotion rested on rules 1/14, not on those hours) — and
exactly the error class the sidecar makes impossible.

**G1 FAILED, and the kill was discharged by measurement.** The replay does not
reproduce the keeper (max |Δprice| $9.0–10.6, mean LMP +0.012/+0.012/+0.055 %, a
CT_PEAKER↔ST_GAS tie reshuffle with total conserved). Pre-registered kill K-A
required attribution: a 2024 re-solve at the session's **base commit**, with the
entire session diff absent, reproduces the **identical** divergence (10.5637
$/MWh over 18,630 zone-hours, both). It belongs to the 58 commits between the
keeper's solve basis and this base — not to this session's code. **Standing
caveat: a keeper arming a P0-run-pattern mechanism cannot be re-solved into
byte-identity once main moves, so the sidecar cannot be backfilled faithfully.**

### 3. The census in all six lanes + a ratchet (item 2)

`scripts/mechanism_matrix_gap_sweep.py` (promoted from probe, `--iso`). Absent
from matrix / armed-on-keeper-with-no-cell: **ERCOT 64/35, CAISO 39/23, PJM 21/8,
NEISO 15/10, MISO 12/10, NYISO 10/9 — 161 and 95.** CI saw none: the diff gate
fires only on fields added in the same PR.

**NYISO's column is CLOSED (0/0/0)** — its nine were all `nyiso_gas_bridge_*`
sub-scalars, registered literally in the `gas_commitment_bridge` row's `def`;
`nyiso_iroquois_winter_spread` (named only in the matrix file's header comment)
now rides `gas_hub_basis_overlay`. The other five lanes are their own work (rule
25/28(d)). **What stops the backlog growing:** `mechanism-matrix-gaps.json`
enumerates the 146 remaining, and `check_mechanism_matrix.py` now FAILS any PR
whose ISO-scoped field is in neither the matrix nor that baseline. Shrink-only.

### 4. Hygiene (item 3), both closed

**(a) `ct_committed/econ/peak_hr_override` DELETED (rule 26).** Traced: two
readers, both inside the `else` of `if offer is not None` gated on
`group == "CT_CHP"`; CT_CHP resolves its offer curve plant-code-independently;
**all 119 bundles in all six ISOs arm the triple and all 119 carry a truthy
`offer_curve_by_group["CT_CHP"]`** — reachable on none. The curve is all-1.0, so
a future arm dropping CT_CHP would have silently re-armed 1.1/1.2/1.4.
**Rule 26 made affordable:** `_CACHE_KEY_RETIRED_FIELDS` re-inserts a deleted
field at its historical default *inside `cache_key()` only* — hash-only,
unassignable, unreadable by any solve path — so no cache is orphaned and no
pinned literal is re-pinned (the remedy the cache-key guard names wrong).

**(b) `caiso_ra_min_load_frac` is now CAISO-scoped (rule 25).** Confirmed inert
elsewhere (every reader behind `caiso_ra_mustoffer and iso == "CAISO"`), but a
CAISO-fitted 0.26 rode all 119 bundles' recorded recipes. Non-CAISO now records
the neutral 0.40; CAISO unchanged.

### 5. C3c — what sets the 2024 Long Island pin (item 4)

Measured, not proposed. **Both** LI import paths saturate together
(`NYC>Long_Island` 275/275 MW, `NYISO_external>Long_Island` 1200/1200 MW) while
the mainland clears at $72.11–74.57. The pin is **energy-side** (`reserve_price`
= 0.0; no LI reserve family binds in 2024). The marginal unit at $297.538777 is
**`7146_1`, an OIL tranche** (68.93 of 73.80 MW) — the only part-loaded LI
generator among 132 tranches / 106 running; the $279.966487 rung is a different
unit (`CT_PEAKER_Long_Island_p2511_peak`). **596.9 MW sits idle** at the annual
peak-price hour (561.6 MW oil + 35.3 MW DR).

**So 2024 is not a missing-mechanism year.** The same fleet and curves reach
$503.74 (2023) and $489.62 (2025), so the LI ladder extends far above $300; 2024
simply never calls the next oil rung. Closing it needs either genuinely tighter
Long Island load/imports/availability, or a different oil offer level — the
second being a residual tune rule 1 forbids absent measured oil-offer data. **No
lever proposed.**

### 6. Also repaired, not introduced here

`PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE` was added to `config/fuel_trajectories.py`
without its `constants.py` facade re-export, leaving `test_constants_facade` red
on main; restored to contract, no value touched. Five further failures
(`test_ff_readiness_battery`, `test_outages`) verified pre-existing on base and
left to their own lanes. The merge-conflict markers committed inside three NYISO
bundles' JSON by caiso-158 were already repaired upstream by caiso-159.

Next shorthand: nyiso-115.

## 2026-08-03 — nyiso-116: the C3c SETTLEMENT BASIS measured INERT, the $2.46 knife-edge retired as a target, and the unit/network layer COMMITTED

**Keeper UNCHANGED** (`2026-08-02-nyiso-113-li-locational`); nothing promoted,
demoted or re-keyed. **No lever proposed and no parameter introduced, changed or
fitted** (pre-registered kill K-C held). Pre-registration
`PREREG-nyiso116-c3c-unit-layer-2026-08-03.md` pushed before the solve; full
write-up `results/calibration/FINDING-nyiso116-c3c-unit-layer-2026-08-03.md`;
every number read from the committed `_nyiso116_c3c_unit_layer_gates.json`.

### 1. The settlement basis is INERT for C3c — and this is the first session that could test it

C3c scores the model's **energy-only** max-zonal LMP against an actual RT series
that at NYISO **embeds RCPF by market design** — `calibration_verdict.py`'s own
G-20a comment names it ("NYISO RCPF-into-LBMP"). Its designed remedy never fires
here: the keeper's payload carries `ordc.hoursGt200 = {model, actual}` with **no
`overlay`**, because the post-solve RCPF overlay is refused under rule 19
(matrix cell **G**). NYISO therefore sits in the gap between two individually
correct decisions.

The admissible route is not a second mechanism but the **co-opt's own locational
duals**, readable from a bundle only since nyiso-114 persisted
`reserve_family_<year>.parquet`. Rebuilt that way (zone adder = sum of duals of
every containing region), C3c is **3/0/14 — unchanged in every year**. **Proved,
not observed:** the best settlement price attainable in *any* hour the
energy-only series leaves below the gate is **$286.42 / $297.54 / $276.42**,
margins **$13.58 / $2.46 / $23.58**. The reserve families never arrive before the
energy price; in 2024 the adder is exactly **$0.00** in all three pinned hours
and every family-binding hour has max-zonal ≤ $250. Cell stays **G**, note
extended. **DO-NOT-REDO: the settlement-basis question for NYISO C3c is closed.**

### 2. The $2.46 knife-edge is not the gate, and closing it would score false positives

C3c bands within `[0.5×, 2.0×]` of the RT actual, so the model needs **5 / 6 / 21
hours**, and the hour that must clear sits at **$286.42 / $201.69 / $235.73** —
**+$13.58 (+4.7 %) / +$98.31 (+48.7 %) / +$64.27 (+27.3 %)**. Three consequences:
C3c fails in **all three years**, not just 2024; **2023 is the nearest miss, not
2024** (two sessions organised around the year farthest from its gate); and
closing the pin leaves 2024 at **0.25×**, still failing.

Worse, the pinned hours are **not real tail hours** — actual RT at h4528–4530 is
**$282.83 / $179.20 / $128.43** — while **h4526, which reality priced $511.30 and
which IS one of 2024's twelve tail hours, the model prices at $201.69** (it is
hour #6). A pin-sized lever books **three false positives** and still misses the
true hour inside its own range: the caiso-144 pattern, and a rule 1 `[R-STRUCT]`
violation by construction. This **corroborates** nyiso-85 §7d's "not timing" as a
rate — of the model's *own* tail hours, **67 % (2/3) in 2023 and 79 % (11/14) in
2025** are real — and refines it: inside the June 2024 episode the model's peak is
**phase-shifted ~2 h late and clipped**. The SRMC-roof attribution stands, and the
residual belongs to the owner-gated peak-half amplitude question (nyiso-110).

### 3. A globally-failing replay can still be a faithful instrument — per gate

| year | all zone-hours max \|Δp\| | top-20 tail max \|Δp\| | C3c keeper / arm |
|---|--:|--:|--:|
| 2023 | $10.5045 | **$0.000000** | 3 / 3 |
| 2024 | $10.5637 | $0.000000 | 0 / 0 |
| 2025 | $9.0424 | $4.744358 | 14 / 14 |

The G1 divergence is a marginal-tie reshuffle in the **body** of the
distribution; the tail is untouched. **Standing lesson for every ISO lane: G1 is
a PER-GATE property, not a bundle property** — a replay failing G1 globally may
still be the right instrument for one gate, but that must be *shown* for that
gate, never assumed.

### 4. The attribution was not reproducible; now it is

nyiso-114 §6 named a unit, an offer rung and two transmission limits — **none of
it reproducible from any committed artifact**, since `unit_hourly` / `network`
are gitignored. Both stated grounds for that exclusion measured **false**:
*"regenerable by a replay"* (nyiso-114 §2 measured that a P0-bridge keeper is not
replay-recoverable — so that layer is **permanently** unrecoverable) and
*"~58 MB/bundle"* (measured **920 KB/yr** unit + **170 KB/yr** network =
**3.2 MB** for the whole 3-year bundle, ~18× overstated; the figure predates the
`DELTA_BINARY_PACKED` encoding that took CAISO's unit frame 12.60 → 1.74 MB).
Layer committed via `git add -f`; the gitignore default stands for ordinary
bundles and its comment is corrected. New matrix row
`unit_network_layer_sidecar` (cells `IIIKKI`).

**All four §6 claims re-verified** from the committed layer: both LI import paths
saturated (275/275, 1200/1200), pin energy-side (`reserve_price` 0.0), **one**
part-loaded LI unit (`7146_1` oil, **68.9346 of 73.8 MW**) and **596.9 MW** idle
— reproducing §6 to the decimal. One honest divergence: this arm finds **1**
LI-family-binding hour in 2024 (h3762) where nyiso-114 reported 0 — the G1
divergence reaching the reserve layer; it does not touch the pin.

### 5. A disclosed post-hoc gate correction

**G3 and P4 first FAILED, and the fault was the gate's.** Both used an absolute
`1e-6` MW tolerance while `_unit_hourly_frame` stores `mw`/`cap_mw` as
**float32**, whose spacing is **7.6e-06 MW at 113 MW and 6.1e-05 MW at 838 MW** —
8–60× *below* representable precision, so no float32 column could satisfy it.
Measured: **131,038 cells (2.0 %)** read as over-cap with a **maximum excess of
1e-04 MW (1.2e-07 relative)**, and **15** units read as part-loaded of which
**14 sat exactly at their cap**. Corrected to **1e-3 MW (1 kW)** *after* seeing
the result; both readings are reported. This is the third instance in three
sessions of gating on an instrument that cannot observe the claim — the first two
(nyiso-113's K3/K4, nyiso-114's `held_mw`) were about a column's **semantics**;
this one is about its **dtype**, a distinct check: confirming the writer emits the
column is not enough, the column must be able to *represent* the tolerance.

### 6. Rule 28(c) census

Re-run for NYISO on current main: **0 absent / 0 prose-only / 0 armed-no-cell**,
unchanged. The ratchet baseline is **not widened**. The 12 "live-but-invisible"
fields are ISO-agnostic (`coal_prb_*`, `cc_*`, `gas_st_startup_spread`, …) and
belong to whichever lane owns them — rule 25/28(d) forbid minting them here.


---

## caiso-160 (2026-08-03) — CT meter screen re-based onto nyiso-113; **KEEPER PROMOTED**

**Keeper → `2026-08-03-nyiso160-ctmeter-screen-b`** (bundle
`nyiso160_ctmeter_screen_B`). Control `2026-08-03-nyiso160-ctmeter-control`.
Cross-ISO lane, run from the CAISO chair; closes caiso-159 §8 item 1, so the
caiso-156 CT heat-rate meter screen (`f6238a5`) is now promoted in **all four
ISOs that consume the artifact**.

**Promoted on rule 14 [R-ACCURATE], not on fit.** Zero recipe changes, zero free
parameters, DOF ledger carried verbatim at (30, 6). Determination
CALIBRATED-WITH-CAVEATS and **all nine criterion verdicts, the grade summary
(9/8, 1 ledgered, 0 fails), the C1 headline (all 14/14, free 10/10) and the
caveat list are IDENTICAL** to the superseded `2026-08-02-nyiso-113-li-locational`,
whose Zone-K ladder, ramp envelopes and NYSDEC 227-3 mechanisms all carry forward.

**Why nyiso-113 had to be the base.** The caiso-158 NYISO arm was controlled on
nyiso-112 and nyiso-113 promoted underneath it mid-solve, leaving it carrying
`nyiso_li_locational_reserve=False` against a keeper that arms it — promoting it
would have dropped a published Zone-K reserve requirement to gain an input
correction. Both arms here replay the nyiso-113 recipe via `replay_keeper.py`
with **no `--set`**, so the zero delta is structural.

**Artifact:** cap-weighted 12.0769 → 12.4355 (**+0.3586, the largest of the six
ISOs**) and **one-sided dearer** — 17 plants dearer, 0 cheaper, 2 unchanged,
19/19 applied, no flag changes, 80 → 79 unit rows. Only Gowanus
(15.2804 → 16.9538) and Narrows (15.7537 → 16.7814) move past 0.5.

**K3 reproduces caiso-158's independent prediction almost exactly** — predicted
CT_PEAKER −0.012/−0.005/−0.036 TWh and λ +0.028/+0.020/+0.080 % on the nyiso-112
base; measured −0.0121/−0.0047/−0.0359 TWh and +0.030/+0.024/+0.079 % on the
nyiso-113 base. C3c untouched (12/8/68 h > $200, identical max λ).

**K2 — a control was solved against the handoff's instruction, and it earned its
compute.** The handoff said none was needed because the committed keeper *is* the
control; that holds only if the keeper solved at this HEAD, and it did not (seven
`src/market_sim` commits landed after `3746eda`). The control reproduces the
committed nyiso-113 bundle **BIT-IDENTICALLY** — max |ΔMW| = 0.000000 on every P1
class-hour of all three years (147.1621/150.6234/151.7383 TWh). That makes the
A/B delta the artifact's alone **and answers the standing caiso-146 HEAD-drift
item in the negative for NYISO** (it stays open for CAISO, where the outgoing
keeper's sidecars diverged up to 3.2 GW on a class-hour).

**NEW GENERAL DEFECT — `config_drift` cannot see a moved default.** The premise
guard fired on four value diffs (`retirement_rule`, `entry_rate_limits`,
`entry_commissioning_lag`, `caiso_ra_min_load_frac`). None is a recipe choice:
every one is a **shipped default that moved on main** after the keeper solved
(`24b1602`, `3e33f15`, `a0fc302`), recorded identically by both arms.
Absence-awareness does not help — a moved default and a changed recipe are
byte-indistinguishable. Remedy: `gen_caiso160_attestation.DEFAULT_MOVES`, an
allowlist naming each field, its commit and why it cannot reach a backcast,
honoured **only when the K2 bit-identity holds**. **Any ISO promoted after a
default move will hit this**; it belongs in every lane's promotion path.

**Rule 22 D-5(b):** `calibration-complete.json` re-keyed with a determination
re-verified from committed artifacts only (no solve); every criterion verdict
matches, so the marker transfers a determination onto a run scored against it.
`locked_test_scored_on` untouched, NYISO stays absent from `final`, holdout spend
freeze ACTIVE. `audit_keepers --iso NYISO --check`: PASS, 0 failures, 0 warnings.

Evidence: `results/calibration/FINDING-caiso160-nyiso-ct-heat-rate-rebase-2026-08-03.md`,
`PREREG-caiso160-nyiso-ct-heat-rate-rebase-2026-08-03.md`.

Next shorthand: nyiso-117.
## 2026-08-03 — nyiso-115 keeper: the NYC RCPF demand curve as the PUBLISHED STEP; the shared-field ratchet; five transfer candidates adjudicated with zero solves

**Keeper `2026-08-02-nyiso-113-li-locational` → `2026-08-03-nyiso-115-nyc-rcpf`.**
Determination CALIBRATED-WITH-CAVEATS, C3c the sole ledgered caveat, UNCHANGED at
3/0/14 h >$300. One delta: `nyiso_nyc_rcpf_step_curve=true`. Zero free parameters
(ledger 30 → 31 entries, `n_residual` unchanged at 6).

**The lead nyiso-114's instrument opened, screened EX ANTE with no solve spent.**
The per-family reserve-dual sidecar showed NYISO's binding reserve constraint is
overwhelmingly the NYC pair, with 307–358 MW shortfalls of a 500 MW requirement
clearing at $15.63/$18.75. That is a rule 14 `[R-ACCURATE]` question about a
measured input, and NYISO's own posted **zonal** DA ancillary-service prices
answer it. The locational regions nest (NYCA ⊃ East ⊃ SENY ⊃ NYC), so differencing
zone J against a zone sharing every region *except* NYC isolates the NYC-only
shadow price; all three such references (DUNWOD/MILLWD/HUD VL) agree **exactly**
(max $25.00, the same 45/141 hours at $25.00, **zero** hours above) and the two
non-SENY controls do **not** ($65.00 = $25 NYC + $40 SENY), so the isolation is
checked rather than assumed.

**LEVEL CONFIRMED — the model's $25/MW is right.** The isolated adder never
exceeds $25.00 in any of 26,301 hours, and the 10-minute product stacks to exactly
$50.00 in precisely the hours the 30-minute one sits at $25.00 (5/5, 16/16,
98/98). A potential omission was checked and **closed** at the same time: no NYC
locational *spin* family is enforced (a 1,668–3,257 h continuum, max $20.91–29.72,
**zero** hours at the $40 ASM value), so the model is correct to omit it.

**SHAPE REFUTED.** The measured distribution is a smooth opportunity-cost
continuum below the ceiling plus **one atom exactly AT it** (17/45/141 h), with
essentially **no mass at the interior rungs** of the model's 8-step ramp (0/1/2 of
103/167/428 material hours). The model's own NYC duals sat on those rungs and
**never reached the published $25.00 in any of 26,280 hours**, under-pricing the
measured shortfalls by 2.20/1.55/2.39× (10-min) and 7.11/3.69/5.33× (30-min) — the
30-minute worse purely because its 1,000 MW requirement makes the same ramp
shallower, an artifact of the construction with no market basis. **Scope is the
measurement's own boundary:** NYC is the only locational region whose published
RCPF the market ever reaches (East's $775 never approached, LI no material adder
in any hour, SENY caps at the $40 #1344 increment — reported for
`nyiso_ordc_measured_step_span`'s lane, **not acted on**, rule 19).

**Gates.** G1 PASS (the families reach exactly $25.00 in 14/6/19 and 2/6/8 hours
and sit on an interior rung in **zero** hours of all three years), G3/G4/G5 PASS,
zero slack and zero dump in both arms. K-A discharged by construction of the
comparison — every attribution is against the same-HEAD zero-delta control
`2026-08-03-nyiso-115-control-zerodelta`, never the keeper bundle.

**G2 as pre-registered was MIS-SPECIFIED and FAILS — recorded, not redefined.**
It demanded byte-identity of `dual` and `held_mw` for every non-NYC family, but
those are **solved outputs of a co-optimization**, so the gate can only pass when
the mechanism does nothing. Decomposed onto the **construction** leg kill K-C
actually asks about: every non-NYC family's `requirement_mw` and `shortfall_mw`
are byte-identical in all three years (0.00e+00), and the solve logs
independently confirm only the NYC pair's steps changed (**73 → 59 ORDC steps** =
2 families × 7 lost rungs). K-C does not fire. *Standing lesson: a scope gate
belongs on the CONSTRUCTION (requirement + step vectors), never on the solved
duals — in a co-optimization those move by design.*

**The null was pre-registered.** Prereg §4 stated in advance that a step and a
ramp are *both* $0 at or above the requirement, so this changes the **level** in
hours a family already binds and **cannot add binding hours**. C3c is unchanged;
this does **not** reach nyiso-110's everyday-reserve-formation gap (17/6/34
model hours vs a measured DA spin price >$1 in 100 % of peak-window hours) and is
**not** reported as closing it. All twelve scored numeric fields are EQUAL to the
same-HEAD control's. Promoted on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`.

**Not a DO-NOT-REDO breach.** The June-2026 `nyiso 25 rcpf-steep` probe
transferred the NYCA-30min curve's `critical = 0.75 × requirement` anchor to the
locational products — a different parameterization from a different family —
carried **no matrix row**, and was rejected on the C3c tail **count**, i.e. on
fit, which rule 1 forbids as grounds for rejecting a structurally-correct
mechanism. This value is measured from NYISO's own locational prices.

**Rule 22 D-5(b):** NYISO's `complete` marker re-keyed with the determination
re-verified on committed artifacts only (identical, not worse);
`keeper_at_declaration` preserved; NYISO stays absent from `final`; the holdout
spend freeze is ACTIVE and untouched.

**Two further deliverables, no solve spent on either.**

**(a) The rule-28(c) ratchet now covers the SHARED-field class.** The ISO-scoped
census only ever looks at `<iso>_*` fields, so a shared mechanism armed on a
designated keeper with no matrix row was invisible to both the sweep and CI —
nyiso-114 closed NYISO's ISO-scoped column to 0/0/0 while **twelve** shared fields
sat armed on its keeper with zero matrix mention. The sweep gains a keeper-keyed
shared census with declared false positives in `SHARED_CENSUS_EXCLUSIONS` (only
`weather_year`, which a backcast pins by construction), and
`check_mechanism_matrix.py` gains a shared ratchet that stays stdlib-only by
parsing defaults from source and reading each keeper's committed `run_config.json`
— omitting anything it cannot read as a literal, so it is **conservative by
construction** and can never be stricter than the sweep that writes the baseline
(the failure mode that made nyiso-114's `\b`-vs-substring ratchet unsatisfiable).
Exclusions are single-sourced through the baseline and pinned by test.
**NYISO's shared column: 12 → 0** — six sub-scalars named literally on their
family rows, five given honest rows of their own (`coal_drop_pof`,
`gas_st_startup_spread`, `cc_duct_peaking`, `cc_nameplate_summer_derate`,
`cc_capacity_reconcile_path`), one declared false positive. A stricter prose-only
criterion surfaced three more, also closed — including `historic_outage_overlay`,
given a row recording that it is **INERT on the dispatch**, re-verified against
the tree rather than taken from its comment (four references total, no consumer
reads it back); its rule-26 deletion question is **raised, not acted on**, since
it touches all six ISOs' recipes. Because the minted rows are ISO-neutral, this
also closed NEISO (2 → 0) and shrank CAISO 6 → 5, MISO 18 → 17, PJM 19 → 18 — with
no other ISO's cell given a verdict (rule 25/28(d)).

**(b) The cross-ISO transfer queue: all five remaining candidates adjudicated,
zero solves.** `maxgen_emergency_tier_pricing` (MISO K) **→ I** — across 2023–2025
and 5,347 messages of NYISO's own published operational record there are **zero**
Maximum Generation declarations and **zero** emergency-energy alerts, so a
declared-*window* offer floor has no window to bind in (rule 17 applied before a
solve). `cc_committed_offer_margin` (ERCOT K) and `measured_offer_surface`
(ERCOT/CAISO K) **→ G** on identification — both derive from submitted unit-level
offer curves and NYISO publishes none at any grain, so the only route left is
importing the donor's fitted level (rule 25). `reference_price_interface`
(PJM/MISO K) **→ G** under rule 19 — NYISO already carries this phenomenon
**armed on the keeper** as `nyiso_import_hub_prices`, whose own definition names
it "the NYISO analogue of `miso_pjm_lmp_import_pricing` and
`caiso_import_hub_prices`". `storage_vintage_ramp` (ERCOT/CAISO/NEISO K) **→ I**
by magnitude — NYISO lithium-ion moves 200.5 → 252.7 MW across the whole window
and pumped storage is flat at 1,220 MW, so mis-placing the entire increment by
half a year mis-allocates at most 0.057 TWh against ~150 TWh of load.

Evidence: `results/calibration/FINDING-nyiso115-nyc-rcpf-step-curve-2026-08-03.md`,
`PREREG-nyiso115-nyc-rcpf-step-curve-2026-08-03.md`,
`nyiso115_nyc_rcpf_curve_screen.json`, `_nyiso115_stepcurve_gates.json`,
`nyiso115_transfer_queue_adjudication.json`.

## 2026-08-03 — nyiso-117: the NYC RCPF step curve composed onto the corrected CT artifact — KEEPER; and the supersession that ordered it never happened

**Keeper `2026-08-03-nyiso160-ctmeter-screen-b` → `2026-08-03-nyiso-117-nyc-rcpf`.**
Determination CALIBRATED-WITH-CAVEATS, C3c the sole ledgered caveat, unchanged at
3/0/14. One config delta (`nyiso_nyc_rcpf_step_curve`), **zero free parameters** —
DOF ledger 30 → 31 entries, `n_residual` unchanged at 6. Both arms registered
(`2026-08-03-nyiso-117-control-zerodelta` + the keeper), 2023–2025 in one bundle
each (rule 16). Pre-registered and pushed before either solve
(`PREREG-nyiso117-nyc-stepcurve-compose-2026-08-03.md`).

**What it does.** It composes the two orthogonal rule 14 `[R-ACCURATE]`
corrections that had been split across two lanes and neither of which contains
the other: caiso-160's CT heat-rate meter-artifact **input** fix (already on the
incumbent keeper) and nyiso-115's NYC locational RCPF demand-curve **shape**
mechanism. The mechanism was **not** re-derived, re-levelled or re-scoped (rule
23) — the $25/MW value is the published ASM §6.8 RCPF and the NYC-pair scope is
the measurement's own boundary. This was a re-solve on a corrected input.

**Gates — all pass.** G1: the NYC families reach exactly $25.00 in 14/6/19
(10-min) and 2/6/8 (30-min) hours and sit on an interior ramp rung in **zero**
hours. **G2a, the scope kill, is written on CONSTRUCTION**: all seven non-NYC
families' `requirement_mw` — the balance-row RHS, the one pure input in the
sidecar — are float32-**exactly** identical to control in all three years. That
inherits nyiso-115's lesson (its G2 demanded byte-identity of `dual` and
`held_mw`, solved outputs of a co-optimization, so it could only pass when the
mechanism did nothing) and nyiso-116's (equality asserted as `np.array_equal`,
not against a 1e-6 MW tolerance float32 cannot represent). **G2b** corroborates
from an instrument that never touches the parquet: solve-log ORDC steps 73 → 59
in each year, a drop of exactly 14 = 2 families × 7 rungs, family count unchanged
at 9. G3/G4/G5/G6 pass; zero slack and zero dump in both arms; **all 18 scored
numeric fields equal** between arms; K-A…K-E do not fire.

**The null was pre-registered, and K-E measures it directly.** A step and a ramp
are both $0 at or above the requirement, so this moves the **level** in hours a
family already binds and **cannot add binding hours** — binding hours *gained* =
**zero** in every family and year (the 30-min family loses 5 h in 2023 and 1 h in
2025, a shortfall crossing zero, also anticipated in advance). C3c is unchanged;
this does **not** reach nyiso-110's everyday-reserve-formation gap and is not
reported as closing it.

**The session's other result: the supersession premise was false.** nyiso-115's
arms were **already** on the post-fix CT artifact. This session's control is
bit-identical to nyiso-115's control *and* to the incumbent keeper, and its
treatment bit-identical to nyiso-115's treatment — `max |ΔMW| = 0.000000`,
`max |Δprice| = 0.000000`, every class-hour and zone-hour, all three years. That
is not a claim the CT fix is inert: caiso-160's own pre-fix vs post-fix arms
differ by max |ΔMW| 508.19/628.89/387.23 and max |Δprice| $10.50/$10.56/$9.04.
The artifact vintage had been *assumed* from commit ordering. Precisely: in a
fresh container `git merge-base --is-ancestor` cannot see other branches' commits
and **says so** (exit 128, `fatal: Not a valid object name`) — git does
distinguish that from a genuine negative (exit 1). What collapses the two is the
ordinary `cmd && yes || no` idiom, which maps every non-zero exit to "not an
ancestor"; the shortcut is unsound *as usually invoked*, the same failure mode as
reading a pipeline's exit status instead of the process's. Compare the dispatch
instead. Yielding the keeper at nyiso-115 was
therefore unnecessary; reasonable on what was known, but the record should say
nyiso-115's keeper was never stale. Relatedly, FINDING-nyiso114 §2's drift
caution did **not** fire here: control-vs-keeper drift measured exactly 0.0. The
same-HEAD control was still the right design — drift is not knowable in advance —
and its value is that it turned an assumption into a number.

**Task 2, ex ante, no solve — SENY is `S-OVER`, recorded not acted on.** The
isolated SENY-only 30-min adder (`DUNWOD − CAPITL`) caps at $23.92/$30.37/$40.00,
with 52 hours of 2025 at exactly the published $40 increment and **zero above in
any year**; the modelled $500 base is never reached in 26,301 hours. The model
prices SENY in 2/0/8 hours at $62.50–$125.00 — its first rung ($500/8) already
above the entire measured envelope, so 9 of 10 binding hours are **over**-priced,
the opposite direction to NYC. Span confirmed: measured requirement mean
1,602/1,594/1,613 MW (max 1,800) against static widths of 1,300, mis-spanned in
69 % of hours. `nyiso_ordc_measured_step_span` stays `U`; a SENY change needs its
own pre-registration and arm (rule 19). **Instrument honesty:** the screen's
intended negative control degenerates on the 30-min product (the East 30-min
adder is identically $0.00 in every hour), so it is reported as *uninformative,
not as a pass*, and the reference pair is validated instead on the 10-min product
where East does bind (4,603/6,993/6,611 hours, max $27.00/$36.05/$46.22).

**Task 3.** Nothing on NYISO's (empty) transfer queue was re-tested; the
shared-field ratchet still reports 0 for NYISO. The ERCOT/PJM/MISO/CAISO
backlogs are their lanes' work (rule 25 / 28(d)).

Rule 22: the holdout spend freeze is ACTIVE and untouched — no year outside
2023–2025 solved, scored or read. `complete.NYISO` re-keyed with a determination
re-verification on committed artifacts only (D-5(b)); identical, not worse.
Evidence: `results/calibration/FINDING-nyiso117-stepcurve-compose-2026-08-03.md`,
`_nyiso117_stepcurve_gates.json`, `nyiso117_seny_rcpf_curve_screen.json`.

## 2026-08-03 — nyiso-119: the published SENY $40 increment tier — **KEEPER**; and a price gate that failed on its own boundary

**Keeper `2026-08-03-nyiso-118-seny-span` → `2026-08-03-nyiso-119-seny-increment`.**
Determination CALIBRATED-WITH-CAVEATS, C3c the sole caveat, **unchanged**. One
delta (`nyiso_seny_rcpf_increment_step`, cell `U` → `K`), **zero free parameters**
(ledger 32 → 33, `n_residual` 6). Both arms registered.

**The mechanism.** The SOM states SENY 30-minute as a **$500/MW base over
1,300 MW plus a $40/MW increment above it**; the 2023 SOM p. A-132 prints the
pair as one object, "SENY $500+$40". `nyiso_dynamic_reserve_requirements` has
**always enforced** that increment — the measured #1344 series runs 1,550/1,800 MW
against the 1,300 MW base for most of the day — and **nothing ever priced it**.
The whole shortfall was charged against the base curve, whose first rung
($500/8 = **$62.50**) already sat above the entire measured $23.92/$30.37/$40.00
envelope. That is precisely why nyiso-118 was a partial: it re-spanned the
*widths*, and the RCPF penalties are requirement-independent.

**No new number** (rule 5), clearing the bar the NYC step curve cleared: the $40
is the same **ASM §6.8 item 12** already pinned for `east_30min_total`, whose
clause names **Southeastern explicitly**; the 1,300 MW breakpoint is read from
`NYISO_RCPF_LOCATIONAL`; the hourly requirement was already on the balance row.
The **$500 base, `critical_mw = 0` and `n_ramp = 8` are untouched** — the
posted-price instrument never reaches the base, so its shape stays *unidentified*
and keeps its ramp (nyiso-115's discipline). Rule 19 is reconciled by
**substitution**: the two-tier construction carries the hourly requirement
natively in the increment band, so SENY takes this branch *instead of* the span
branch, exactly as `li_30min_total` already opts itself out of the global flag.

**Every kill discharged ex ante, on construction, before the solve.** The probe
builds the `ReserveDesign` twice at one HEAD and diffs requirement, penalties and
widths — no LP, no dual. Blast radius **exactly one family**: the other eight are
byte-identical in all three vectors at **$0.000** reachable price delta, so the
rule-23 freezes on the NYC curve and the LI ladder hold. Steps **8 → 9**, first
rung **$62.50 → $40.00**, base-ramp penalties byte-identical, and **nyiso-118's
total-width == requirement identity survives at 0/0/0 violating hours in both
arms** — including the zero-requirement TSA hours. Solve-log ORDC steps
**59 → 60**, exactly +1 in one family. Zero slack, zero dump.

**G4 as pre-registered FAILED, and that is recorded rather than quietly
redefined** (the nyiso-115 G2 / nyiso-117 G2a lesson, now on a price gate rather
than a scope gate). It demanded an exact $40.00 dual on the **closed** interval
`(0, band]` — asymmetric, since it excluded the lower kink (`s > 0`) while
including the upper one (`s == band`). At either kink the LP is degenerate and
the dual sits legitimately between the adjacent bands' prices; that is exactly
why the zero-shortfall hours price $7.75/$17.31 rather than $0, which the
pre-registered form already tolerated. Re-specified onto what K-G actually asks:
the **strict interior** prices at the published increment — **2/0/4** hours, every
one at exactly **$40.00** — and the band **edge** is **bracketed**, $57.28 inside
[$40.00, $62.50]. The mechanism is unchanged; only the gate's boundary handling is.

**Structural corroboration the gates did not ask for.** In the treatment's
deepest 2025 hour the LP stops holding SENY reserve at **exactly
`held_mw = 1300.0` — the published base** — because past that point the $40 tier
no longer justifies holding more. In the control it stopped at **1575.0**, which
is 1800 minus one control band width and has no market meaning. The published
demand curve's own breakpoint is now where the dispatch stops.

**Effect, and the honest limit.** SENY max dual **62.50 → 40.00** (2023), no
binding hours (2024), **87.07 → 62.50** (2025). S-OVER is **narrowed, not closed**
and is reported rather than gated (rule 1): of 10 binding hours, those above the
year's *measured* ceiling go **8 → 4** and those above the *published* $40 go
**8 → 2**. It is not closed because 2023/2024's **realized** ceilings
($23.92/$30.37) sit **below** the published $40 cap — the market never drove those
years to full band saturation — so pricing *at* the cap is still above them. That
residual is an **incidence/depth** question, not a curve-construction one, and it
belongs with the open peak-half reserve-formation lane. **My own prereg §5 said
this would put SENY "inside the measured envelope"; that is right for 2025 only,
and the precise claim is that the model now prices at the published $40 cap and
never above it, where before its floor was $62.50.**

**All 18 scored numeric fields are equal** to the same-HEAD control's — the
pre-registered ISO-scope null, since SENY binds in only 2/0/8 hours and a demand
curve can only price where there is a shortfall. **C3c unchanged**, also
pre-registered; this does not reach nyiso-110's everyday-reserve-formation gap
and is not reported as closing it. Promotion rests on rule 1 `[R-STRUCT]` /
rule 14 `[R-ACCURATE]`.

**Task 2.** `mechanism_matrix_gap_sweep.py --iso NYISO` re-confirmed at **41
family / 0 / 0 / 0 / 0**, sole exclusion the declared `weather_year`; the 40 → 41
is this session's own new field and row, not drift. NYISO's column stays closed
and its transfer queue empty. No other ISO's cell adjudicated (rule 25 / 28(d)).

Rule 22: the holdout spend freeze is ACTIVE and untouched — no year outside
2023–2025 solved, scored or read. `complete.NYISO` re-keyed with a determination
re-verification on committed artifacts only (D-5(b)): identical to the superseded
keeper on all 18 fields, all 9 criterion verdicts and the grade summary — nothing
worse, so the promotion proceeded. Evidence:
`results/calibration/FINDING-nyiso119-seny-increment-2026-08-03.md`,
`PREREG-nyiso119-seny-increment-2026-08-03.md`, `nyiso119_gate_scores.json`,
`nyiso119_seny_increment_construction_probe.json`.

## 2026-08-04 — nyiso-120 (CROSS-ISO session): neither meter is wrong about East River — they AGREE, and what they agree on is that the model has been double-counting boiler fuel into a 306 MW NYC gas tranche

**Keeper UNCHANGED** (`2026-08-03-nyiso-118-seny-span`). Three runs registered:
`2026-08-04-nyiso-120a2-control-samehead` (the valid control),
`2026-08-04-nyiso-120b-scope-gate` (the treatment) and
`2026-08-04-nyiso-120a-control` (a SUPERSEDED first control, kept as the record
of why — see (5)).

**Why NYISO at all.** The session brief opened on **NEISO**, whose queue is
owner-gated end to end (§5.6: item 1 SPENT, items 3/4/6/7/8 closed, item 2
ceiling-bounded, items 5 / 5b / C3c-2023 all needing an owner green-light that
is not granted), and directed a cross-ISO cell. This one was minted **one day
earlier** by miso-122 §7 handoff item 1, which measured the defect, declined to
act under rule 25, and left one question: *"which meter is wrong about East
River's boundary, and it is not answerable from MISO's data."* It is answerable
from NYISO's, and the answer is **neither**.

**(1) THE MEASUREMENT, no LP, on NYISO's own data.** ORIS 2493 East River is a
hybrid one eGRID plant code cannot see: two `Combined cycle` units that generate
and two `Dry bottom wall-fired boiler` units (60, 70) reporting **exactly zero**
gross load in every hour of 2023–2025. **KE1** — eGRID's `CHPCHTI` (13,493,031
MMBtu) and the CAMPD dark-boiler fuel (13,629,047) are the **same object to
1.0 %** (ratio 1.0101). **KE2** — CAMPD's power-train fuel over eGRID's own
`PLNGENAN` is **7.3763** against eGRID's credited **7.4205**, ratio **0.9940**:
two independent meters agreeing to **0.6 %**. Therefore `PLHTIAN` is *already*
the power train's fuel, `PLHTRT = 7.4205` is *already* the power-only rate, and
the `(PLHTIAN + CHPCHTI)` add-back **double-counts boiler fuel into a power
tranche**. The keeper has been offering 306 MW of NYC `CT_CHP` at **11.8032**,
59 % above what the machine burns. **KE3** — 100.0 % of dark fuel is a boiler
`unitType` in all three years, share 37.51/30.79/30.64 %, max/min 1.22.
Corroborated from the *generation* side: CEMS gross 2,133,488 MWh vs eGRID net
3,078,707 (**0.693**) is miso-118's `G_gross < 1` physical impossibility —
~0.95 TWh/yr of HRSG steam-turbine output CEMS never meters, which is why 7.4
and not the naive CEMS-gross 10.6 is the right number.

**(2) The correction, zero free parameters.** miso-122's scope gate shipped
**unmodified** (no derive code was edited): East River goes `ok` →
`below_credited` and its **effective** offer rate falls **11.8032 → 7.4205
(−37.1 %)**. **KE4 exact**: one applied row changes, zero other flag changes,
zero other applied-rate changes. Direction is unambiguously downward only
because NYISO is **not** in `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` ({CAISO, PJM})
— in a hand-factor ISO the identical exclusion would push the rate **up**;
asserted in the scorer, not assumed. Rule 23 citation is miso-122's scope-gate
**logic change on measured grounds**, never a residual. DOF ledger unchanged
(32 entries, `n_residual` 6).

**(3) A/B — LIVE, and one gate regresses.** All six construction gates PASS, no
kill fires: max zonal |Δλ| **0.1287 / 0.1371 / 0.3875** $/MWh clears the 0.10
bar in **3 of 3** years, no zone's λ rises, `CT_CHP` gains **+0.3113 / +0.1921 /
+0.4214 TWh** displacing `ST_GAS` / `CC_REGULAR` / `CC_CHP`. **P1 free-class C1
does NOT regress** (14/14 all, 10/10 free in both arms); P3/P4/P5/P6 pass; C3c
**bit-unchanged** (CAVEAT both arms). **P2 fires**: C3a mean LMP FAILS on **2025
at exactly −10.0 %** against a control reading **−9.5 %** — a **0.5 pp
knife-edge crossing** worth **−$0.39/MWh** on a $60 mean, while **2023 IMPROVES**
(+7.6 % → +7.2 %) and 2024 stays deep inside band. The 2025 C3a gap is
**$6.68/MWh**, so this correction is **6 %** of it and **94 % is pre-existing**.
Determination control CALIBRATED-WITH-CAVEATS → treatment **NOT-YET**.

**(4) THE PROMOTION IS ESCALATED, NOT TAKEN — rule 22 D-5(b).** Arm B **is** the
recommended keeper candidate on the owner's standing standard (structural
integrity improves, the input was wrong and is now right, it moves the
worst-matched class — `CT_CHP`, −67.9/−67.6/−62.0 % on the incumbent keeper's
own `_open_items` — toward reality, and it closes a reproducibility seam since
the incumbent solved on the pre-gate artifact and is no longer reproducible from
HEAD). **But NYISO holds a `complete` marker**, and D-5(b) is explicit that a
re-verified determination that is *worse* **stops the promotion and escalates to
the owner; it is never silently written**. CALIBRATED-WITH-CAVEATS → NOT-YET is
worse and would change NYISO's published calibration status. **The corrected
artifact ships regardless** (rule 14); only the keeper designation is deferred.

**(5) Reported against interest — two self-inflicted errors.** (a) The **first
control is invalid**: it solved at a pre-rebase HEAD and main then added three
`ScenarioConfig` fields, so it read 3 differing config keys against the
treatment and failed KE5's same-HEAD requirement. It is superseded, no number is
quoted against it, and a same-HEAD control was re-solved — which turns out
**byte-identical to the committed keeper**, and that is what proves the three
new fields are inert at NYISO. (b) **Nine bundle JSONs reached `origin/main`
carrying unresolved rebase conflict markers** — five of them the **nyiso-119
lane's** — because a rename/rename conflict (git matched the top-15-pruned
`nyiso111_control_A` against both lanes' new bundles) was blanket-resolved on
the wrong assumption that each path was uniquely owned by one side. Found,
stopped for, repaired: the nyiso-119 files restored **byte-exactly** from
`4e1b1274`, mine by label-matched selection
(`scripts/probes/_nyiso120_resolve_rename_conflicts.py`, which refuses to guess).
Zero markers remain. (c) The prereg named **C3c** as the at-risk gate and **C3a**
is what moved — the anticipated mechanism was right, the criterion was not, and
that is recorded rather than re-narrated as a hit.

**Governance.** Rules 12/13/15/16/21/22/23/25/26/28 all honoured; training years
only; the holdout spend freeze is ACTIVE and untouched. Rule 25: **only NYISO's
artifact was re-derived** — NEISO 1595 Kendall (206 MW, −1.2 %) stays in NEISO's
lane and no cell outside NYISO is stamped. Rule 28 duty (b): the
`measured_chp_heat_rates` NYISO cell keeps its `K` (a scope refinement inside
the K mechanism, rule 19) and gains its citation this session.

**(6) OUTCOME — KEEPER PROMOTED, and the arms were re-solved on the RIGHT base
first.** After the above was written the keeper was found to have advanced
`2026-08-03-nyiso-118-seny-span` → **`2026-08-03-nyiso-119-seny-increment`**
*during* this session, after the arms were launched. A nyiso-118-based treatment
would have **silently disarmed `nyiso_seny_rcpf_increment_step`**, the mechanism
nyiso-119 armed and the owner promoted a day earlier — so the shard edit was
made, checked, and **reverted**, and both arms were re-solved on the nyiso-119
recipe: `2026-08-04-nyiso-120-c119-control` /
**`2026-08-04-nyiso-120-c119-scope`**. The promoted run carries
`nyiso_seny_rcpf_increment_step = True` (verified explicitly), and its control
reproduces the nyiso-119 keeper's C3a exactly (34.77 / 37.99 / 60.22).

**The result replicates on the correct base**, which is what shows the finding is
a property of the *input* rather than the recipe: six construction gates PASS,
verdict LIVE, max zonal |Δλ| **0.1278 / 0.1379 / 0.3887**, `CT_CHP`
**+0.3103 / +0.1927 / +0.4213 TWh**, C1 unchanged in both arms, P2 fires on C3a,
**2025 −9.5 % → −10.1 %** and **2023 +7.6 % → +7.2 %**.

**Owner ruled PROMOTE on the D-5(b) escalation.** NYISO keeper →
**`2026-08-04-nyiso-120-c119-scope`**, determination **NOT-YET**, written
explicitly into `calibration-complete.json` rather than softened;
`build_status --iso NYISO` rebuilt (`[NYISO:NOT-YET]`); `audit_keepers --iso
NYISO` **PASSES, 0 failures / 0 warnings**; matrix header re-stamped and the
NYISO column re-checked (rule 28). **The ledgered-caveat budget is UNSPENT at
1 of 3** — C3c remains the sole ledger entry and the C3a FAIL is a *criterion
failure*, deliberately **not** ledgered.

**The named open residual for nyiso-121** is NYISO's **2025 under-pricing**,
which this correction did not create: the C3a-2025 gap is **$6.68/MWh** and this
input fix moves **$0.38** of it, so **~94 % is pre-existing** and is now the
lane's target. A marker-hygiene note recorded in passing: `audit_keepers` M1b
extracts the **first** determination token appearing anywhere in the marker's
prose, so a marker must never spell out a second run's determination — doing so
makes it assert a status never scored against the run it names, exactly the
silent transfer D-5(b) exists to prevent.

* Next number: **nyiso-121**.

## 2026-08-04 — nyiso-122: NYISO's 2025 C3a failure is TWO seasonally-separable objects, and the winter half is LOCATIONAL, not fuel — queue item 4 refused ex ante, NO SOLVE

**Keeper UNCHANGED** (`2026-08-04-nyiso-120-c119-scope`, **NOT-YET**). **Zero
solves, zero runs registered** (there is none to register), zero `ScenarioConfig`
/ constant / derive / artifact changes. C3c's ledger budget stays **1 of 3,
unspent**. Session renumbered **nyiso-121 → nyiso-122** (the label was already
spent on main by the MISO-matrix-column session, which had itself renumbered off
nyiso-120).

**(1) THE TARGET, DECOMPOSED.** nyiso-120 handed this lane the 2025 C3a miss
(−10.1 %, $6.68/MWh, ~94 % pre-existing). Month × actual-price-band, on committed
artifacts only — the model side reproduces the scorer byte-for-byte (34.64 /
37.85 / 59.84): **Jan+Feb −3.58**, of which **−3.60** is the **$100–300 band** and
only −0.18 the tail; **Jun+Jul −3.76**, of which **−3.81** is the **>$300 tail**
(33 of 2025's 42 tail hours); all other months net **+0.81**. Counterfactuals:
tail-exact ⇒ **−3.51 % PASS**; every-non-tail-hour-exact ⇒ **−6.33 % still FAIL**.
**Two objects, neither sufficient alone.**

**(2) NO NEW DEFECT IN 2025 — A REMOVED MASK.** The compression is present in all
three years (p90/p10 model **2.697** vs actual **4.430**). The model's trough
over-pricing offset its peak miss while prices were low: the $0–25 band was
**39.1 %** of load in 2023 (+3.41) and is **7.2 %** in 2025 (+0.92). **Rule 19
`[R-ONE-MECH]` check, which the brief required: the peak half IS nyiso-110's
object** — the model's reserve price is **$0.00 in 99.7 %** of 2025 hours,
including **1,037 of the 1,041** hours the market cleared $100–200. No second
mechanism proposed.

**(3) THE WINTER HALF IS LOCATIONAL.** The model prices its four mainland zones
**IDENTICALLY in 100.0 %** of Jan+Feb 2025 hours; the actual all-5 zonal spread
was **$44.28** (Jan) / **$27.09** (Feb). Upstate_West January is nearly exact
(**−0.35**) while NYC is short **$44.63**, Capital_Hudson **$37.21**,
Long_Island **$39.15**. **NYC alone carries 49 %** of the winter gap. The model
has the marginal energy cost about right and the **location** entirely wrong.

**(4) ITEM 4 RE-OPENED LEGITIMATELY, THEN REFUSED EX ANTE — ON REACH, NOT
CONSTRUCTION.** Its old blocker ("re-arming alone just moves the miss to summer")
is inapplicable: summer's miss is entirely the >$300 tail, which a monthly
gas-basis reallocation cannot move either way. Its **construction gates PASS** —
annual conservation **Δ = 0.00000** in all three years, NYC delivered gas
unchanged in all 36 months, blast radius the eastern trio + Upstate_West. It is
refused because it **cannot reach the defect**: (a) NYC is unchanged **by
construction** and carries 49 % of the gap; (b) it **cuts** Upstate-January gas by
**$7.48/MMBtu**, the one zone that is right; (c) it lifts **December** by
**+$3.67/MMBtu**, the year's largest single monthly move, on a month already
accurate to **−0.06**; (d) the whole measured NYC−Upstate gas spread is worth
**$12.75–17.00/MWh** against a **$44.28** actual premium. Rule 1 `[R-STRUCT]`:
arming it would reach a better number through a mechanism that is not the real
one. **Deliberately NOT adjudicated `R`** — its standalone rule 14 `[R-ACCURATE]`
case survives untested by solve and is an **owner question**, since arming it
improves a measured input while degrading C3a-2025 (a rule 22 D-5(b) escalation).
**The NYISO lever queue is now EMPTY.**

**(5) REPORTED AGAINST INTEREST — my own successor hypothesis is refuted by the
same data, and I departed from my own prereg.** (a) Re-grounding the **Tier-3**
interface TTC estimates on NYISO's measured as-enforced limits is **not**
data-blocked (2023–2025 on disk, `positive_limit_mw` per interface-hour) but **is**
refuted: UPNY-CONED and SPR/DUN-SOUTH bind >95 % in **0.0 %** of 2025 hours at
medians (6385/4600 MW) **looser** than the model's own estimates (5150/3900), so
re-grounding would *loosen* them; only CENTRAL EAST binds (17.8 % of Jan+Feb
hours) and the model's 2850 is already tighter than the measured 3100. The
measured limits are **NOT adopted** (rule 14's misalignment clause: one reduced
link stands for several parallel paths). (b) **The prereg committed to a two-arm
A/B and I did not run it.** The zonal attribution that kills the arm was measured
**after** the prereg was committed and pushed; I stopped rather than spend the
solve, which is the nyiso-93/94/95/97 ex-ante-refusal discipline. The prereg's
§4.5 declared the C3a-2025 net direction **undetermined in advance** and that
declaration stands — it is **not** retro-fitted into a prediction of this outcome.
(c) The two aggregation bases (hub-hourly in §1, per-zone-monthly in §2) differ by
~0.87 $/MWh on the Jan+Feb total and are **named, not blended**.

**(6) WHAT THIS CONTRIBUTES.** The actual NYC-over-Upstate premium (**$44.28**)
exceeds any plausible fuel-spread × heat-rate (**$12.75–17.00**) by 2.6–3.5×
**with no interface flow-limited**, so the residual is **sub-zonal in-city price
formation** — the object nyiso-97 closed on identification. **Both halves of the
C3a-2025 failure therefore resolve to the SAME unrepresented object**, the
downstate locational boundary. The `Capital_Hudson` → Zone-F/Zone-G **topology
split** was chartered against **C3c (the summer tail) alone**; it now also owns
the **winter level miss**, which is the larger of the two in the months it
occupies and is **not** a scarcity phenomenon. **Any owner charter for the split
should be scoped to both halves, not just the tail.**

**Governance.** Rule 12: no solve. Rule 13: every measured price and flow is a
validation target; nothing entered a solve. Rule 15: no run produced, so none
registered; the keeper's dashboard entry is untouched. Rule 19: the peak-half
object confirmed to be nyiso-110's, no second mechanism. Rule 21: DOF ledger
unchanged. Rule 22: **training years only** — every probe hard-refuses any year
outside {2023, 2024, 2025}, which matters because the committed actual-LMP parquet
carries 2018–2022 and 2026 and the interface-flow directory carries 2018–2026; the
holdout spend freeze is **ACTIVE and untouched** and NYISO's `complete`/`final`
markers are unchanged. Rule 23: nothing re-derived — the construction probe only
*evaluates* a shipped function at two flag settings. Rule 25: **NYISO only**; no
other ISO's cell stamped. Rule 28(a)/(b): item 4 taken from the queue and its cell
stamped this session. Evidence:
`results/calibration/FINDING-nyiso122-c3a-2025-is-two-objects-2026-08-04.md`,
`PREREG-nyiso122-iroquois-winter-spread-2026-08-04.md`,
`_nyiso122_c3a_2025_decomp.json`, `_nyiso122_iroquois_construction.json`,
`_nyiso122_winter_zonal_spread.json`.

* Next number: **nyiso-123**.

## 2026-08-04 — nyiso-122 (closeout): the NYISO cross-ISO queue LANE IS CLOSED, with every remaining route typed as a blocker

**Keeper UNCHANGED** (`2026-08-04-nyiso-120-c119-scope`, **NOT-YET**). No solve, no
run registered, no `ScenarioConfig` / constant / derive / artifact change. C3c's
ledger budget stays **1 of 3, unspent**. This closes out the lane opened by the
nyiso-122 diagnosis above.

**Closure rests on four measured facts, not judgement.** (1) The **lever queue is
EMPTY** — item 4 was the last live item and was re-opened then refused ex ante on
reach; items 1/1b/2/3/5/6/7/8/9/9c/10/11/12 were already closed. (2) The
**rule-28(c) column census** re-confirms **41 family / 0 absent / 0 prose-only /
0 armed-no-cell / 0 invisible**, sole exclusion the declared `weather_year`.
(3) **Item 9b is not a queue item at all — it is SHIPPED**: `_screen_demand_dropouts`
is called unconditionally for `NYIS` at `src/market_sim/data/eia930/demand.py:396`,
no flag and no gate. (4) **Item 11b is owner-DEFERRED and out of lane** — it moves
CAISO +0.4173 / NYISO +0.1996 / NEISO +0.1618 TWh, so rule 25 `[R-ISO-SCOPE]`
forbids a NYISO session from acting on it and it needs its own cross-ISO charter.

**THE THREE BLOCKERS, TYPED so a later session can tell "not yet tried" from
"cannot be tried".** NYISO's open residual is the 2025 C3a FAIL, whose two halves
both resolve to the downstate locational boundary:

- **BLOCKER-A — GOVERNANCE.** The `Capital_Hudson` → Zone-F/Zone-G **topology
  split**, C3c's standing re-open condition, which nyiso-122 shows now **also**
  owns the winter level miss. Explicitly never a mechanism-flag lever. *Unblocks
  on* an owner charter — and that charter should now be **scoped to both halves**,
  not to the summer tail alone.
- **BLOCKER-B — DATA (access-walled, not un-fetched).** The sub-zonal in-city
  price formation the winter miss actually is. nyiso-97 closed it on **content,
  not merely access**: the as-enforced AORR is MyNYISO-walled and the public
  2008-vintage Appendix B carries **no derivable NYC parameter**. *Unblocks on* an
  authorized MyNYISO-grade intake; **not** by re-reading public postings.
- **BLOCKER-C — IDENTIFICATION (data exists and REFUTES the lever).** Re-grounding
  the **Tier-3** interface TTC estimates on NYISO's measured as-enforced limits is
  **not** data-blocked (2023–2025 on disk with `positive_limit_mw` per
  interface-hour) but **is** refuted: UPNY-CONED and SPR/DUN-SOUTH bind >95 % in
  **0.0 %** of 2025 hours at medians **looser** than the model's own estimates. The
  measured limits are **NOT adopted** (rule 14's misalignment clause). This route
  is closed on measurement and does not unblock.

**ONE ITEM IS LEFT OPEN ON PURPOSE.** `nyiso_iroquois_winter_spread` stays cell
**`O`**, default-**off**, **not** adjudicated `R`. Its standalone rule 14
`[R-ACCURATE]` case survives untested by solve and is an **owner question**, since
arming it improves a measured input while **degrading** C3a-2025 — a rule 22
**D-5(b)** escalation, not a session decision. Its construction gates already PASS
(annual conservation **Δ = 0.00000** in all three years).

**Standing instruction for a later NYISO assignment:** there is nothing actionable
on the C3a residual without BLOCKER-A's charter or BLOCKER-B's intake. A session
assigned to NYISO with neither should say so and take another ISO's queue (rule
28(a)) rather than manufacture a lever — which is exactly what item 4's refusal was
protecting against (rule 1 `[R-STRUCT]`).

* Next number: **nyiso-123** (blocked — see above). **UNBLOCKED at nyiso-123 by
  owner charter — see the entry below.**

## 2026-08-04 — nyiso-123: BLOCKER-A CHARTERED as a PAIR — the split is the right object for 2025 and would break both passing years alone, NO SOLVE

**Keeper UNCHANGED** (`2026-08-04-nyiso-120-c119-scope`, **NOT-YET**, re-verified
from committed artifacts at this HEAD with `scripts/calibration_verdict.py
--run-id`; `scripts/audit_keepers.py --iso NYISO` **PASS 0/0**). **Zero solves,
zero runs registered** (there is none to register), zero `ScenarioConfig` /
constant / derive / artifact changes, **no mechanism tested so no matrix cell
verdict changes**. C3c's ledger budget stays **1 of 3, unspent**. Holdout spend
freeze **ACTIVE and untouched**; training years only.

**(1) THE JOB.** nyiso-122 left the lever queue **EMPTY** with the only successor
an owner-charter item. This session (a) put the re-scoped charter question to the
owner, (b) surfaced item 4 as the second open owner question, and (c) produced the
**leave-one-year-out grounding rule 22 requires before any structural promotion** —
which nyiso-122 had measured for 2025 only. No lever was substituted to avoid
asking.

**(2) THE GROUNDING, EXTENDED TO 2023–2024.** On the keeper's committed `hourly/`
sidecars; **2025 reproduces nyiso-122's table exactly**. Two new facts. **(a) The
Jan+Feb window is a 2025 artifact** — 2024's winter miss is in **December**
(−1.130 of −1.690 in the $100–300 band; its Jan+Feb is **+1.053**), 2023's is in
**February** (−0.734; January +0.237). It is a **cold-snap** object, so any future
window must be **driver-derived, never a month range** (rule 17
`[R-FLOOR-WINDOW]`). **(b) The defect did not worsen — the exposure grew.** The
conditional per-hour miss in the $100–300 band **improved** −104.95 → −63.37 →
**−40.45** $/MWh while the band's load share grew **1.42 → 2.75 → 14.65 %**
(10.3×). On C3a's percentage basis, **2023→2024 is the mask removal** (−8.53 of
−8.83 pp is the ≤$100 credit collapsing) and **2024→2025 is exposure growth**
(−8.31 of −9.08 pp in the two upper bands). This **sharpens** nyiso-122's
accounting, which quoted the $0–25 band alone, and supports its conclusion more
strongly — the per-hour defect measurably improved every year.

**(3) THE IDENTITY SHARE — AND THE PART REPORTED AGAINST THE HYPOTHESIS.**
Whole-year mainland-4 price identity: **86.40 % (2023) / 95.88 % (2024) / 95.94 %
(2025)**. **2024 ≡ 2025 to 0.06 pp**, which is the comparison that carries the
argument and **confirms** the removed-mask reading. But **2023 is NOT ~100 %**, so
the "constant in all three years" form of the claim is **not supported** — only the
2024↔2025 form is, and that is how it is stated. Corroborating: **Feb 2023 ran a
$43.67 actual all-5 zonal spread**, within $0.61 of Jan 2025's $44.28, **in a year
that PASSED C3a**. The boundary is a standing gap, not a 2025 event.

**(4) THE CHARTER'S NUMBER — AN EXACT IDENTITY, ASSERTED IN PROBE CODE.**
Anchoring the model at its own upstate price and adding the **observed** basis
(diagnostic bound only, rule 13 `[R-MEASURED]` — it never enters a solve), every
actual term cancels and the counterfactual error collapses to **the model's
load-weighted `Upstate_West` pricing error**: **+$1.59 (2025) / +$3.25 (2024) /
+$7.93 (2023)**. C3a with the basis closed and nothing else changed: **2023
+8.10 % PASS → +24.74 % FAIL**, **2024 +0.07 % → +8.60 %** (in band, near the edge),
**2025 −7.86 % FAIL → +2.45 % PASS**.

**(5) STRENGTHENED AND WEAKENED — TWO DIFFERENT CLAIMS, BOTH REPORTED.**
**Strengthened as the object**: the split owns both halves, and in 2025 the
unconstrained marginal cost is right to +$1.59 so essentially all of the C3a
failure is the missing basis. **Weakened as a standalone promotion**: it converts a
passing year into a clear fail — in-sample gain with held-out degradation, exactly
what rule 22 `[R-HOLDOUT]` exists to catch, and invisible from 2025 alone. The
counterfactual is an **upper bound** on the lift (it holds upstate fixed), so the
2023/2024 breakage is a conservative warning, not an overstated one.

**(6) OWNER RULINGS.** Put with the numbers above: **charter both, paired** —
**Object A** the `Capital_Hudson` → Zone-F/Zone-G topology split, **Object B** the
upstate over-pricing (the "mask" nyiso-122 named as trough over-pricing, now
located exactly), promoted **only jointly**. Precommit written:
`docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md` — **nothing built,
armed, registered or solved**, with gates **G0 identifiability** and **G1 Object-B
diagnosis** both **no-LP and gating every solve**, and §6 pre-stating the three ways
the charter closes **without** a promotion. Second ruling: item 4
(`nyiso_iroquois_winter_spread`) **holds unadjudicated**, cell stays **`O`**,
default-off; its standalone rule 14 case still survives untested by solve.

**(7) ONE CORRECTION TO THE PRIOR RECORD.** nyiso-122 mapped hour → month with a
per-year `date_range`; the repo's canonical clock is a **fixed non-leap 8760
calendar keyed to 2023** (`build_ercot_as_withholding._CALENDAR`). Identical for
non-leap 2023/2025 — **every nyiso-122 number stands** — and one day off for
leap-2024 from Mar 1. nyiso-123 uses the canonical clock throughout.

**Standing instruction for a later NYISO assignment:** the lever queue is **still
EMPTY** and no lever may be manufactured. What is now available is the **chartered
pair**, and it must be worked **under the charter's pre-registered gates** — start
with **G0** and **G1**, both no-LP, both gating any solve. A chartered topology
change is **not** a queue item and must never be entered as one.

Evidence: `docs/handoffs/nyiso-123-downstate-boundary-2026-08-04.md`,
`docs/handoffs/nyiso-downstate-topology-split-charter-2026-08.md`,
`results/calibration/PREREG-nyiso123-downstate-boundary-2026-08-04.md`,
`_nyiso123_month_band_allyears.json`, `_nyiso123_zonal_identity_allyears.json`,
probes `scripts/probes/_nyiso123_month_band_allyears.py`,
`_nyiso123_zonal_identity_allyears.py`.


## 2026-08-04 — nyiso-124: the topology-split charter CLOSES AT G0 WITH CAUSE, and Object A is re-attributed to Central East — a boundary the model ALREADY HAS. NO SOLVE

**Keeper `2026-08-04-nyiso-120-c119-scope`, UNCHANGED.** Zero solves, zero years
outside 2023–2025, no `ScenarioConfig` field / constant / derive script / artifact
changed, **no run produced so none registered** (rule 15). No cell verdict moved —
no mechanism was tested. The lever queue is **still EMPTY** and no lever was
manufactured. Verified at HEAD `afe19a56`, committed artifacts only:
`calibration_verdict.py --run-id` returns **NOT-YET** (`price_mean` FAIL on 2025
−10.1 %, `price_tail` ledgered CAVEAT, seven PASS); `audit_keepers.py --iso NYISO`
PASS 0/0.

**(1) G0 — IDENTIFIABILITY: FAIL on 2 of 5 quantities → the charter closes under
its own §6(1).** NYISO publishes **no F/G (UPNY-SENY) transfer limit** anywhere
reachable: absent from the MIS P-32 posting (7 internal interfaces), absent from
the MIS ATC/TTC posting (7 internal interfaces read across all 36 training
months), and absent from **all four Gold Book editions** (0 hits for
SENY / UPNY / Central East / Total East / "transfer limit" — the Gold Book carries
no interface-limit table at all). Its only public trace is the 2025 SOM's record
that NYISO **ceased studying** the interface in the deliverability test in **2013**
after the G-J locality was created. The split also forces `ext_G`, the Zone-G
share of the 1,600 MW eastern seam, which is unchanged from nyiso-101 §3 leg 2 —
`interchange/spec.py` calls it "a modelling choice inside the topology". Boundary
definition, zonal load allocation and per-unit fleet membership all **PASS**.

**(2) INDEPENDENTLY, THE SPLIT TARGETS THE WRONG BOUNDARY.** Measured NYISO zonal
RT LBMP, annual eastward steps: **E|F (Central East) +$10.17 / +$5.09 / +$11.69**
against **F|G (UPNY-SENY) −$2.65 / −$0.36 / −$1.48**. Zone G prices **below** Zone
F, and furthest below in the charter's own cold-snap months (Feb-2023 −12.19,
Jan-2025 −8.91, Feb-2025 −15.41). The F|G separation is real, but it is a
G-cheaper-than-F object — not the downstate premium the charter chartered.

**(3) OBJECT A IS RE-ATTRIBUTED: A DIAGNOSABLE DEFECT, NOT A REPRESENTATION
FRONTIER.** `CENTRAL EAST - VC` is the **only** internal NYISO interface that binds
at all (≥95 % of posted limit in **4.4 / 2.5 / 3.6 %** of hours annually,
**22.0 / 17.2 / 26.9 %** of January hours); TOTAL EAST, UPNY CONED, SPR/DUN-SOUTH,
DYSINGER EAST, MOSES SOUTH and WEST CENTRAL bind in **0.0 %** of hours in every
month of every year — independently **confirming** nyiso-122's TTC-re-grounding
refutation, which is not re-opened. The model's own `Upstate_West→Capital_Hudson`
link sits on that same cutset and separates prices in **13.4 / 1.5 / 1.1 %** of
hours, reproducing **5.0 / 6.0 / 0.3 %** of the measured basis. January 2025: model
measured monthly TTC **3,175 MW** vs posted median **3,205 MW**, real interface
binding in **26.9 %** of hours, model link separating in **0.0 %**. Same cutset,
same limit, same hours. §7(1) answered too — 2023's 86.40 % mainland identity is
that year's tighter measured TTC override (1,450–1,950 MW monthly vs 2,525–3,175
later) — and **qualified**: the model's 2023 separation concentrates in Mar/Aug/Sep
(34.5 / 38.7 / 26.7 %), months the real interface bound in 5.2 / 1.6 / 1.1 %, while
January (real 22.0 %) gets 6.3 %. More dispersion, not the right dispersion.

**(4) G1 — OBJECT B, AND A CORRECTION TO THIS SESSION'S OWN FIRST READING.**
Reported against interest: the mirror-image reading (A and B one object) was
**falsified by this session's own quintile decomposition**. The model over-prices
upstate by **+$4.2–7.2/MWh in the quintiles where the market's own basis is $0–2**;
`corr(upstate error, measured basis)` = **+0.124 / −0.061 / −0.263**; CE-binding
hours carry only **13 / 31 / −344 %** of the load-weighted upstate error. The
+$18–24 conditional reading in binding hours was a **level artifact** and is
corrected, not carried. Object B is an **off-peak** object (+$8.37 / +$4.53 /
+$5.05 vs on-peak +$6.72 / +$1.87 / −$0.70) that applies to the **whole state**, so
**§7(2) is decided: it is the TROUGH HALF of nyiso-110's compression object**. Rule
19 `[R-ONE-MECH]` forbids a second mechanism for it; `diurnal_price_amplitude`
NYISO stays **G**. Diagnosis half PASSES, mechanism half FAILS — charter §6(2) is
satisfied alongside §6(1).

**(5) THE SUCCESSOR QUESTION IS ANSWERED IN THE SAME SESSION — AND THIS ENTRY'S
OWN FIRST CLAIM IS CORRECTED.** It said the question was unmeasurable from
committed artifacts because `system_<year>.parquet` carries no link flow. True of
the keeper bundle, **wrong about the repo**: `_network_frame` has always written
`hourly/network_<year>.parquet` (per-link hourly flow, reduced cost, bounds),
`.gitignore` merely excludes it by default, and NYISO **already has it committed**
— matrix row `unit_network_layer_sidecar` NYISO cell **K**, on
`nyiso116_c3c_unitlayer`. Measured there, with **no solve**: the three DOWNSTATE
border links sit **at their bound in 98–100 % of all hours of all three years**
(`external→Capital_Hudson` 1,600 MW, `external→NYC` 1,000 MW,
`external→Long_Island` 1,200 MW), delivering a flat **3,800 MW** against a
measured downstate median of **1,870 / 1,772 / 2,040 MW** (**2.03× / 2.14× /
1.86×**), while `external→Upstate_West` runs **net EXPORT** (−1,003 / −1,520 /
−1,689 MW p50) against a measured **import** of **+668 / +454 / +148 MW**. The
**net across all four links reconciles to 2–11 %** (model +2,797 / +2,280 /
+2,112 vs measured +2,538 / +2,226 / +2,188) — the signature of a seam whose
total is pinned by the monthly EIA-930 reconciliation band while its spatial
allocation is free. **That is why Central East stays slack:** ~1.8–2.0 GW of
surplus import lands EAST of the cutset and ~1.0–1.7 GW is drained from the west,
so the model's CE link carries 722.8 MW at the median (util **0.253**) where the
real interface carries util **0.591**. Provenance stated because it bounds the
claim: `nyiso116_c3c_unitlayer` is a replay of the **nyiso-113** recipe whose
**G1 fidelity FAILED** (max |Δp| $10.5/$10.6/$9.0), licensed by nyiso-116 for C3c
tail work on G2 — used here ONLY for link saturation and gross flow magnitude,
where a marginal-tie reshuffle cannot move a ~100 %-of-hours bound or a 2–3× flow
gap, and the measured side needs no model at all. **NOTHING IS ARMED AND NO LEVER
IS PROPOSED.** Which part of the seam construction is wrong — border-link
capacities, import-ladder tranche pricing, or the absence of any aggregate
downstate cap since nyiso-100 correctly retired the mis-attributed 4,350 MW
`NYISO_simultaneous_import` scalar — is **not** adjudicated, and nyiso-100 is
**not** re-opened (its provenance finding stands; this is a measured consequence
nobody had checked). Rule 25 binding both ways: this is PJM's
`pjm_seam_envelope_by_neighbor` object in kind, so `seam_flow_envelopes` NYISO
moves **`.` → `U`** and NYISO derives its own parameters from its own data.
Residual candidates NOT adjudicated: forced eastern generation (D-2 `ST_GAS
reliability_floor` 2.80 TWh / 21 % of class, `firm_import` 7.88 TWh in 2025) and
the zonal load allocation — both second-order against a 2× seam misallocation.

**(6) FLAGGED, NOT EDITED.** C3c's stated re-open condition ("a `Capital_Hudson` →
Zone-F/Zone-G topology split") is **falsified as written**. It lives in the keeper
attestation generator; correcting it removes C3c's only stated satisfiable re-open
route and is therefore an **owner disposition**, not a session edit.

**Standing instruction for a later NYISO assignment:** the lever queue stays
**EMPTY**, the chartered pair is **closed**, and the named successor is the §(5)
open blocker — which is an instrumentation/scoping question to put to the owner,
not a lever to enter as a queue item.

Evidence: `docs/handoffs/nyiso-124-charter-g0-g1-2026-08-04.md`, probe
`scripts/probes/_nyiso124_charter_g0_g1.py`, record
`results/calibration/_nyiso124_charter_g0_g1.json`.

* Next number: **nyiso-125**.

---

## nyiso-126 (2026-08-04) — the eastern seam is identified; C3a is two offsetting defects

**No solve. No mechanism armed. No parameter moved. No bundle, nothing registered.
Keeper unchanged at `2026-08-04-nyiso-125-seam-envelope`** (re-verified at this
session's own head: `calibration_verdict.py` → NOT-YET, sole FAIL `price_mean`,
C3a +7.7 / −0.8 / −10.2 %; `audit_keepers.py --iso NYISO` PASS 0/0; nyiso-125's
commit `956d612b` confirmed on `main`).

**(1) ITEM 1 — the eastern seam is no longer data-blocked.** nyiso-125 refused the
`Capital_Hudson` / `Upstate_West` envelope because nothing separated the
`SCH - PJ - NY` Zone-A and Zone-G legs. **NYISO's own posting does** — *"NY-NJ PAR
Interchange Percentages, Operational Base Flow (OBF), and other MW Offsets"* —
and it splits the row **three** ways with **zero free parameters**: Ramapo 32 % +
JK 15 % → **Zone G**, ABC 21 % → **Zone J**, residual 32 % over the free-flowing
western ties → **Zone A**, plus a PAR-outage reallocation rule that makes the
shares **availability-conditioned, not flat** (the Operating Study records Farragut
B/C **open** in Winter 2023-24, moving 14 points west). Zone landings are cited to
the Gold Book and the Operating Study, not assumed. P-34 `ParFlows` (5-min per-PAR
flow by PTID) is verified present for 2023–2025 and supplies the availability.
**REPORTED AGAINST INTEREST:** the published shares do **not** reproduce as
measured-flow regression slopes in aggregate (summed |slope| 0.45 / 0.12 / 0.20
vs a published 0.68) — they are a market-model **scheduling** convention, not a
metered flow share, and the construction says so. **ALSO NEW:** 21 % of the PJM AC
interchange lands in Zone J and the model has **no PJM AC path into NYC at all**.
**Nothing was intaken**; the lane is now gated on **owner authorisation**, not on
data. Pre-registration filed and **not executed**.

**(2) ITEM 2 — C3a-2025's −10.2 % decomposed, scorer-side, no solve.** The `rt_lw`
basis is reconstructed and validated first (−0.77 / −0.36 / −0.23 % vs the
committed bench). **It is not a level error.** It is two structurally distinct,
offsetting errors present in **all three years**: a **stable over-pricing of the
bottom 80 % of hours** (+$5.51 / +$3.79 / +$4.39 per MWh of contribution; mean
error +$7.18 / +$4.92 / +$5.71) against a **top-decile under-pricing that grows**
(−$2.95 → −$3.59 → **−$9.35**; decile 10 model $108.69 vs actual $187.98 in 2025).
**Only the second term moves between years, and it alone is 138 % of the 2025 net
residual.** h16–h18 carry **70.6 %** of the 2025 signed residual; Jun/Jan/Feb/Jul
carry **111 %**. Three consequences: **2024's C3a "PASS" (−0.8 %) is cancellation,
not agreement**; **no level lever can close C3a-2025** (it would worsen a bulk
over-pricing already +$4–7/MWh); and **C3a-2025 and C3c are one defect measured
twice**, not two independent misses. The 2025 model also shows **no zonal price
separation at all** (`NYC` $58.65 = `Upstate_West` $58.65).

**(3) ITEM 3 — FLAGGED, NOT EDITED (owner disposition).** The C3c ledger is stale
in **two** ways, now **three**: (a) its stated re-open condition (the F/G topology
split) is falsified as written — nyiso-124, `_nyiso124_charter_g0_g1.py`; (b) its
premise is partly falsified — nyiso-125 moved the tail 3/0/14 h → 18/2/21 h with a
seam-side input correction carrying **no scarcity parameter**
(`FINDING-nyiso125-seam-envelope-2026-08-04.md` §5.5); and (c) **new here** — if
C3a-2025 and C3c are the same object per §(2), then carrying C3c as a *supporting*
caveat while C3a is the *load-bearing* FAIL understates what is being carried.
**This session edited none of it.**

**Standing instruction for the successor:** the lever queue stays **EMPTY**. The
eastern-seam lane is **pre-registered and owner-gated**; do not open it without
explicit authorisation, and do not re-derive the nyiso-125 refusal — it is
discharged on identification.

Evidence:
`results/calibration/FINDING-nyiso126-seam-identification-and-c3a-decomposition-2026-08-04.md`,
`results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`,
probes `scripts/probes/_nyiso126_par_identification.py`,
`scripts/probes/_nyiso126_c3a_decomposition.py`.

* Next number: **nyiso-127**.

---

## nyiso-127 (2026-08-05) — NYISO is NOT READY to spend 2022; the freeze's own defect is still 1.7–2.9× the norm on this ISO — NO SOLVE

**Keeper UNCHANGED** `2026-08-04-nyiso-125-seam-envelope`. **No solve, no
mechanism armed, no parameter moved, no bundle, nothing registered** (rule 15: a
session that produces no run registers nothing). Verified at this session's own
head: `calibration_verdict.py --run-id` → **NOT-YET**, sole FAIL `price_mean`,
C3a **+7.7 / −0.8 / −10.2 %**, C3c CAVEAT (ledgered) 18/2/21 h vs 10/12/42 h
failing 2024 alone, ledger **1 of 3**; `audit_keepers.py --iso NYISO` **PASS
0/0**; nyiso-125 (`20127fd0`) and nyiso-126 (`25dbf462`, PR #3555) both on `main`.
**ITEM 1 (the eastern-seam PAR attribution) was NOT executed — owner-gated, no
authorisation given.** No out-of-training year was solved, scored, read or
registered; the freeze was checked first and is ACTIVE.

**(1) Q3 — THE FREEZE'S STATED REASON STILL BINDS FOR NYISO, WITH NUMBERS.** On
the CURRENT post-merit-order-guard extract, NYISO books **25.4 / 29.6 / 35.8 %**
of its CC_REGULAR capacity-year as mechanical outage (CC_ALL 26.7/28.0/31.1 %)
against the **~10–15 %** EFOR+planned norm the freeze cites — **1.7–2.9×**, and
**worst in 2025**, the failing C3a year. The guard's veto shrinks year over year
(15.9 → 11.1 → **6.7** pp), so the correction is smallest where the residual is
largest. neiso-63's own unit-year metric reproduced for like-for-like: baseline
47/47/44 % (validating against its quoted 46 %) → **37/37/37 %** post-guard.
**Reported against interest:** the obvious mechanism — a too-tight envelope
pinning the CC fleet so something dearer sets price, which would have attributed
nyiso-126's unattributed +$4–7/MWh bulk over-pricing — is **NOT supported** by the
keeper's own committed `class_hourly` sidecar (mean/max 58.4/71.5/68.3 %, hours
within 5 % of the annual max only 0.5/0.9/**4.5** %). Claimed narrowly: the
envelope is materially wrong in a known direction, so a 2022 miss would be
uninterpretable and a 2022 pass misleading. **No lever proposed; the queue stays
EMPTY.** Instrument `scripts/probes/_nyiso127_cc_outage_envelope.py`, record
`results/calibration/_nyiso127_cc_outage_envelope.json`.

**(2) Q5 — READINESS VERDICT: NOT READY**, on §(1) alone and independent of
everything else. Secondary reasons: the load-bearing C3a-2025 FAIL is unledgered
(determination NOT-YET), and a pre-registered keeper-changing candidate is queued
behind an owner authorisation. **Q4 ordering: (b) resolve ITEM 1 first** — its
§8 rule 2 promotes on structure even if C3a/C3c are unchanged or modestly worse,
so a successful arm changes the keeper by construction — **but the ordering
argument is not the binding reason to wait; §(1) is.** Restated: 2022 is
UNSPENDABLE until the owner lifts the freeze explicitly, and a validation number
is SELECTION EVIDENCE, never a certified out-of-sample skill number (rule 22).
NYISO stays ABSENT from `final`.

**(3) Q1 — THE FRONTIER DECLARATION HAS LAPSED; RECOMMEND RE-DECLARATION, NOT A
THIRD AMENDMENT.** It lapsed at **nyiso-120**, whose own log entry records
`determination control CALIBRATED-WITH-CAVEATS → treatment NOT-YET` on a 0.5 pp
knife-edge crossing (−9.5 % → −10.0 %, 94 % of the gap pre-existing), and has not
been restored — so the frontier block's **CALIBRATED-WITH-CAVEATS** label and the
live determination have disagreed for two days. Four load-bearing clauses of the
2026-07-31 note are now falsified or superseded: the sole-blocker premise, the
"cannot form the tail" strength claim, the F/G re-open condition, and the label.
The substantive frontier claim (the C3c lever queue is exhausted, nine items
adjudicated) survives and should be re-stated. **Not edited — owner disposition.**

**(4) Q2 — THE BLOCKERS ARE ONE OBJECT PHYSICALLY, BUT DO NOT COLLAPSE FOR THE
RUBRIC. RECOMMEND: DO NOT LEDGER C3a-2025.** Both sides stated in the finding.
Against, decisively: the rubric defines a ledgered caveat as `MEASURED_LIMIT`
("**the actual is the limitation**") and requires "its own named **measured-input**
reason", while nyiso-126 attributes C3a-2025 to a **model** defect on both halves;
explaining a miss does not stop it missing (nyiso-120 twice declined to ledger
this exact FAIL); and `price_mean` is **load-bearing** where the only precedent
(C3c) is *supporting*. If the owner ledgers it anyway, **broaden the existing C3c
entry rather than open a second slot** — one defect, one slot. **Not
re-classified here.**

**(5) ITEM 3 — NOW FOUR ITEMS, ONE DECISION PACKAGE, NONE EDITED.** (a) the F/G
re-open condition falsified as written (nyiso-124 G0); (b) the "cannot form the
tail" premise partly falsified (nyiso-125, 3/0/14 → 18/2/21 h on a seam-side
**input** correction with no scarcity parameter); (c) C3a-2025 and C3c are one
object, so carrying C3c as a supporting caveat understates what the single slot
covers (nyiso-126 §2.3(3)); and **(d) NEW HERE — a phantom DOF entry**:
`GAS_AVAILABILITY_FACTOR[NYISO] = 0.866` is ledgered as living in
`constants.py` with `identification: published`, but **no such symbol exists
anywhere in `src/market_sim/`** (its only other repo occurrence is
`market-sim-build-plan.md:406`, the pre-extraction `lmp_engine.py` manifest). An
over-count, not a hidden channel — a rule 20 provenance defect. All four live in
`scripts/gen_nyiso125_attestation.py`; editing the emitted JSON alone would be
reverted by the next generator run.

**Standing instruction for the successor:** unchanged. The lever queue stays
**EMPTY**; the eastern-seam lane is pre-registered and owner-gated; do not
re-derive the nyiso-125 refusal (discharged on identification at nyiso-126).

Evidence:
`results/calibration/FINDING-nyiso127-holdout-readiness-and-frontier-review-2026-08-05.md`,
probe `scripts/probes/_nyiso127_cc_outage_envelope.py`,
record `results/calibration/_nyiso127_cc_outage_envelope.json`.

* Next number: **nyiso-128**.

---

## nyiso-128 (2026-08-06) — NYISO grid solar is double-counted against the load series; correction LIVE, K6 fires because the keeper does not reproduce on main

**Keeper UNCHANGED** `2026-08-04-nyiso-125-seam-envelope`. **No promotion.** Both
pre-registered arms solved 2023–2025 and registered (rule 15):
`2026-08-06-nyiso-128-control`, `2026-08-06-nyiso-128-solar-basis`.

**(1) THE DEFECT (rule 14 `[R-ACCURATE]`, a DOUBLE COUNT).** The model takes NYISO
solar capacity from the EIA-860 utility-scale operable schedule, which includes
~2 GW of **distribution-connected NY-Sun community solar that is not a NYISO
market generator** and whose output is **already netted out of the EIA-930 `NYIS`
demand series used as load** (`NG: SUN` identically zero, 8,760/8,760 hours —
nyiso-106 measured this and recorded the reason without connecting it to the
supply side). Model capacity 1,645 / 2,566 / 2,930 MW and energy 1.94 / 2.64 /
3.55 TWh against a **registered** fleet of 174.4 / 573.4 / 573.4 MW producing a
published 0.23 / 0.50 / 1.08 TWh (Gold Book Table III-2a). Three NYISO
instruments agree on the registered level: the III-2a registry, the 2026 Gold
Book (**no PV market generator entered during 2025**), and nyiso-106's own MIS
P-63 daylight-bulge decomposition. **Zero free parameters** — membership is an
identity; `n_residual` unchanged at 6.

**(2) K6 FIRES, AND NOT BECAUSE OF THE MECHANISM.** The same-HEAD control runs the
keeper recipe with **all 680 `scenario_config` fields verified identical** and
still reads C3a **+6.2 / −1.7 / −7.0 %** against the keeper's recorded **+7.7 /
−0.8 / −10.2 %**. **THE KEEPER'S SOLE FAIL IS ABSENT AT CURRENT HEAD** —
C3a-2025 −10.2 % (FAIL) re-solves to −7.0 % (PASS) with no mechanism change. The
benchmark did not move (actual 66.53 both), so it is a **model-side** change from
main's advance and/or a from-scratch `data/clean` rebuild. PREREG §8-1 is
unconditional and is honoured **on a favourable result**. Owner-disposition event
of the same class as the recorded 2026-07-26 de-designation.

**(3) THE A/B IS VALID AND IS READ** (same HEAD, K1 confirms exactly one differing
field). K1/K2/K4/K5 **PASS**; K5 is the load-bearing one — import p50 moves only
+52 / 0 / +42 MW, so the removed solar is replaced by **in-state thermal**, not
imports. **P1 CONFIRMED**: JJA h16–h18 2025 CT_PEAKER **+109 MW**, ST_GAS
**+365 MW**, CC_REGULAR +142 MW against solar **−1,218 MW**. C3a +6.2/−1.7/−7.0 →
**+8.8/+0.8/−3.2 %**, all six PASS; the pre-registered adverse case (2023 crossing
+10 %) **did not** materialise.

**(4) REPORTED AGAINST INTEREST, TWICE.** **C3c REGRESSES** — 2023 18 h → **22 h**
against a measured 10 h (1.80× → **2.20×** over-produced), **PASS → FAIL**; 2024
2 h → 3 h vs 12 h still failing. And the PREREG §4 declared limitation bites: the
arm removes 2.80 TWh of 2025 solar where the registry implies ~2.47, so **~0.45 pp
of the +3.8 pp C3a-2025 gain is UNEARNED** and only ~3.35 pp is attributable to
the correction.

**(5) TWO OWNER DECISIONS ARE DUE, IN ORDER.** (a) Diagnose the
keeper-reproduction failure — until it is understood every NYISO A/B has an
unstable baseline. (b) Then the promotion: if the control is accepted as the true
current baseline, the treatment is the recommended keeper on rules 1/14, carrying
the C3c-2023 regression openly as its cost.

**Also found and committed for the next session:** the NYISO keeper is **not
reproducible from the documented CLI** — thirteen of its non-default fields have
no argparse path and reach the solve only through the generic `prb_overrides`
channel. `scripts/probes/_nyiso128_solve_ab.py` drives from the keeper's own
recorded provenance block and verifies fidelity on a 24-hour solve.

Evidence:
`results/calibration/FINDING-nyiso128-market-solar-basis-2026-08-06.md`,
`PREREG-nyiso128-market-solar-basis-2026-08-05.md`,
`_nyiso128_ab_gates.json`, probes `_nyiso128_solve_ab.py`, `_nyiso128_ab_gates.py`.

* Next number: **nyiso-129**.

---

## nyiso-128b (2026-08-06) — KEEPER PROMOTED `2026-08-06-nyiso-128-control`; determination NOT-YET → CALIBRATED-WITH-CAVEATS with NO mechanism armed

**OWNER RULING, and it is what unblocked this** (2026-08-06): *"We don't need to
investigate why the results are better if they're better now… fixes have been
made and this would make sense."* The nyiso-128 K6 failure — the incumbent
keeper not reproducing on main — is **adjudicated a STALE-BASELINE artifact, not
a defect owing a deep diagnosis**. The substantive basis: main advanced by dozens
of merged fixes since the incumbent's `git_sha 49aac023`, and nyiso-106's solar
benchmark repair states in its own finding that it *"applies to the next NYISO
solve"*. A baseline that **improved after fixes landed** is expected behaviour.
The PREREG's K6 assumed a **static** baseline; that assumption was wrong, not the
result. **Promoting the control resolves the staleness by construction** — the
designated keeper now reproduces on main.

**(1) THE PROMOTION.** NYISO keeper → **`2026-08-06-nyiso-128-control`**
(bundle `results/calibration/nyiso128_control`), superseding
`2026-08-04-nyiso-125-seam-envelope`. **NOTHING NEW IS ARMED** — this is the
superseded keeper's OWN recipe re-solved on current main, all **680**
`scenario_config` fields verified identical before the solve. **Determination
NOT-YET → CALIBRATED-WITH-CAVEATS.** C3a **PASSES all three years** at
**+6.2 / −1.7 / −7.0 %** against the incumbent's recorded +7.7 / −0.8 / −10.2 %,
whose 2025 FAIL was the sole blocker. C3c stays the **single** ledgered caveat
(2024 only, model 2 h vs RT actual 12 h, **0.17×** — a genuine under-production,
exactly what the ledger licenses), budget **UNSPENT at 1 of 3**.
C1/C2/C3b/C4/C6/C7/C8 all PASS. `audit_keepers --iso NYISO` **PASS 0/0**;
`calibration-complete.json` re-keyed with the determination re-verified from
committed artifacts (rule 22 D-5(b), no solve).

**(2) THE SOLAR-BASIS TREATMENT IS ESCALATED, NOT PROMOTED.**
`2026-08-06-nyiso-128-solar-basis` arms `nyiso_solar_market_generator_basis`, a
rule 14 `[R-ACCURATE]` input repair with **zero free parameters** correcting a
genuine **double count** (EIA-860's NY utility-scale population carries ~2 GW of
distribution-connected NY-Sun community solar that is not a NYISO market
generator and is already netted out of the EIA-930 `NYIS` demand series used as
load). It is **structurally the more faithful run**, moves C3a further
(**−7.0 → −3.2 %** in 2025, −1.7 → +0.8 % in 2024), passes **six of seven** kill
gates, and confirms P1 (JJA h16–h18 2025 CT_PEAKER **+109 MW**, ST_GAS
**+365 MW** against solar **−1,218 MW**), with the seam exonerated (K5: import
p50 +52 / 0 / +42 MW).

**It is not promoted because it costs a DETERMINATION DOWNGRADE against the new
baseline.** Its C3c-2023 goes 18 h → **22 h** against a measured 10 h — **2.20×
OVER-produced**, the **opposite sign** to the inherited caveat, whose own
classification licenses only an under-production (*"five-zone representation
CANNOT FORM the sub-zonal … scarcity"*). **The 2023 exception was WITHHELD rather
than laundered** — `scripts/gen_nyiso128_attestation.py` records that decision in
the artifact itself — so the treatment reads **NOT-YET**. Rule 22 D-5(b) says a
worse re-verified determination **stops the promotion and escalates**, so it is
escalated. Matrix cell stays **O**: LIVE, unrefuted, armed on no keeper.

**(3) THE NAMED SUCCESSOR.** The treatment's own declared limitation is the next
object: it swapped the capacity BASIS but kept the ISO-wide CF blend (~0.133)
while the registered fleet measures **~0.20 CF** on the Gold Book's own Net
Energy column, still leaving **0.33 TWh** of 2025 solar over-removed in the
**tightening** direction (~0.45 pp of its +3.8 pp C3a-2025 gain unearned).
Re-identifying the fleet CF from EIA-860 tracking mix + latitude is forward-native
and rule-13 clean, and is a **separate object** (rule 19) needing its own prereg.

Evidence:
`results/calibration/FINDING-nyiso128-market-solar-basis-2026-08-06.md`,
`PREREG-nyiso128-market-solar-basis-2026-08-05.md`, `_nyiso128_ab_gates.json`,
`scripts/gen_nyiso128_attestation.py`.

* Next number: **nyiso-129**.

---

## nyiso-129 (2026-08-06) — the escalated solar-basis treatment is PROMOTED on structure at the cost of the determination; the named CF successor is REFUTED as specified and the real object identified; the empty lever queue re-opens with two items

**KEEPER PROMOTED** → **`2026-08-06-nyiso-128-solar-basis`** (bundle
`results/calibration/nyiso128_treatment`), superseding
`2026-08-06-nyiso-128-control`. **Determination CALIBRATED-WITH-CAVEATS →
NOT-YET, carried openly.** **NO SOLVE** — both arms already existed and were
registered at nyiso-128; every number here is from committed artifacts,
published inputs, or the scorer read at this HEAD under **rubric v3.1**.
`audit_keepers --iso NYISO` **PASS 0/0**; `check_mechanism_matrix` exit 0.
Rule 22: 2023–2025 only, freeze checked and untouched.

**(1) THE OWNER RULING THAT RELEASED IT**, verbatim (session nyiso-129): *"Is
this a recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper."* The session's
recommendation was **YES** on rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`. Rule 22
D-5(b)'s worse-determination stop **did fire** at nyiso-128b; the owner is its
escalation target and released it, so the downgrade is **recorded, not
laundered**.

**(2) WHAT IS ARMED AND WHAT IT BUYS.** `nyiso_solar_market_generator_basis` —
**zero free parameters**, `n_residual` unchanged at 6 — replaces the EIA-860
utility-scale capacity basis with NYISO's own Gold Book Table III-2a registry
(15 units, 573.4 MW), removing a **double count** of ~2 GW of
distribution-connected NY-Sun community solar already netted out of the EIA-930
`NYIS` load series (`NG: SUN` identically zero, 8,760/8,760 h). C3a **PASSES all
three years at +8.8 / +0.8 / −3.2 %** against the superseded control's
+6.2 / −1.7 / −7.0 % (2025 +3.8 pp, 2024 +2.5 pp; 2023 −2.6 pp but in band, and
the pre-registered adverse case of 2023 crossing +10 % did NOT materialise).
C1/C2/C3b/C4/C6/C8 all PASS. The removed solar is replaced by **in-state
thermal**, not imports.

**(3) THE COST, LOCALIZED — AND WHY RULE 14 SAYS KEEP IT.** C3c-2023 18 h →
**22 h** vs a measured 10 h (**2.20× over**). Counted off both arms' committed
`hourly/system_2023.parquet`: **every one of the 22 tail hours is Long Island**,
h14–h19, on 08-21 plus the **Sept 4–9 heat wave**, and **all four added hours
sit in that episode** (09-04 16h, 09-07 15h, 09-09 14h/15h; none removed).
**Zone K is where the arm removes 97.7 of 152.1 MW.** Measured sensitivity: the
control carries ~800 MW more system solar and prices Long Island at **$286.4**
where the treatment prices it at **$386.7** — one to two steps up the published
Zone-K ladder. Rule 14's own words apply: a more accurate input that worsens the
fit is a **discovered bug elsewhere** — the phantom Zone-K solar was **masking**
an over-tight Long Island representation. **The 2023 exception stays WITHHELD**
(an over-production, the opposite sign to the caveat's classification;
in-training, so the 2026-08-06 C3c standing rule does not reach it). Ledger
budget **1 of 3**.

**(4) THE nyiso-128b NAMED SUCCESSOR IS REFUTED AS SPECIFIED — ex ante, NO SOLVE
SPENT.** That lever was *"re-identify the registered fleet's CF from EIA-860
tracking mix + latitude"*, premised on the ~0.20 vs ~0.133 gap being **geometry**.
Measured with the machinery the premise named: clear-sky POA ratio
registered-over-whole-fleet **1.0041 / 1.0322 / 1.0276** — the two populations
sit at the **same latitude** (42.54 vs 42.69 °N), differ only modestly in
tracking share (61 % vs 47 % single-axis), and the registered fleet's **DC:AC
ratio is LOWER** (1.340 vs 1.353). Geometry buys CF 0.133 → **0.137**, so the
lever as named is **INERT** and rule 26 `[R-DELETE]` forbids parking it.

**(5) THE REAL OBJECT, NEWLY IDENTIFIED.**
`RENEWABLE_AVG_CF["NYISO"]["solar"] = 0.15` is a **self-declared Tier-3
approximation** — `constants.py` carries *"needs-citation: verify against
EIA-923 ISO totals before quoting a forecast"* on that block — realized ~0.133,
against a **measured 0.1955** for the very fleet this keeper installs (2026 Gold
Book per-unit 2025 Net Energy: **981.8 GWh over 573.4 MW**, per-unit range
0.158–0.222). A **CF-LEVEL defect on a different input**, its own object under
rule 19. **Reported against interest:** this session extracts **981.8 GWh** where
nyiso-128 quoted **1,081.8 GWh** — exactly 100 GWh apart; the successor must
reconcile that first, since it moves the 2025 over-removal from 0.33 to
**0.23 TWh**. Nothing in this promotion depends on which is right.

**(6) THE LEVER QUEUE IS NO LONGER EMPTY** (it was, at nyiso-127/128). Two
items, each needing its own prereg: **(a)** the unmasked **Long Island scarcity
over-production**, whose owner is MEASURED — in **100 % of the 22 tail hours**
(both arms) BOTH LI import paths sit at their bound: `NYC>Long_Island` at
**325 MW** (at bound only 26.5 % of the year, so it binds precisely in the
scarcity episode) and `NYISO_external>Long_Island` at ~849 MW. The 325 MW is not
the link's TTC but the **published capacity-market LCR import limit**, applied by
the armed `nyiso_li_lcr_tsl` as an in-window **hourly energy** cap — a
deliverability quantity doing an energy job, a boundary mismatch
`model/interchange/nyiso.py` already documents. An existing armed mechanism to
RECONCILE (rule 19), not a new floor to stack — and the route back to
CALIBRATED-WITH-CAVEATS; **(b)** the
**NYISO solar CF level**, after the GWh reconciliation. Matrix cell
`vre_market_generator_basis` NYISO **`O` → `K`**; NYISO column and
`docs/mechanism-testing-matrix.md` §5.5 header re-stamped in-session (rule 28).

**(7) FRONTIER / `complete`.** The `complete` entry is re-keyed to the new
keeper with the determination re-verified from committed artifacts (rule 22
D-5(b)); `tier_authorized` and the absent `final` are untouched. **A frontier
re-declaration is NOT appropriate while NYISO reads NOT-YET** — the block lapsed
at nyiso-120, nyiso-127 §3 recommended re-declaration over a third amendment,
and the determination has now moved again; it becomes assessable once (6a)
lands. The nyiso-127 §5 four-item decision package — including the phantom DOF
entry `GAS_AVAILABILITY_FACTOR[NYISO] = 0.866`, ledgered as living in
`constants.py` but present nowhere in `src/market_sim/` — remains **open and
untouched**.

Evidence:
`results/calibration/FINDING-nyiso129-solar-basis-promotion-and-cf-successor-2026-08-06.md`,
`_nyiso129_cf_identification.json`, probe
`scripts/probes/_nyiso129_cf_identification.py`,
`FINDING-nyiso128-market-solar-basis-2026-08-06.md`,
`PREREG-nyiso128-market-solar-basis-2026-08-05.md`.


## nyiso-130 (2026-08-06) — the Long Island cap is a transfer limit MINUS a generation contingency; the bare number swap is REJECTED by its own kill gate, and the determination recovers to CALIBRATED-WITH-CAVEATS

**KEEPER UNCHANGED** (`2026-08-06-nyiso-128-solar-basis`). **DETERMINATION
NOT-YET → `CALIBRATED-WITH-CAVEATS`.** Rule 22: 2023–2025 only; the holdout
spend freeze was checked and not touched.

**(1) THE IDENTIFICATION — the durable result.** The armed `nyiso_li_lcr_tsl`
caps the model's only mainland→Zone-K AC link at NYISO's published Zone-K
"Locality Limit" (325/275/275 MW) as an **hourly energy** bound. NYISO's own
report says that is not a transfer limit. Locality Bulk Power Transmission
Capability Report **TABLE 1 note 2**, identical in the 2024-25, 2025-26 and
2026-27 editions: *"The true N-1-1 Transmission Security Limit is 940 in this
scenario, the Bulk Transfer Limit accounts for the loss-of-source of 660 MW"*
(Neptune HVDC). Downstream it is consumed as capacity-adequacy accounting — the
2023 LCR Report's TSL Floor Calculation enters it as `[B] = Studied 325` and
computes `UCAP requirement = [A] − [B]` against a **load forecast**. **And in
this model the 660 MW is already carried twice**: Neptune's *energy* on the
separate `NYISO_external>Long_Island` link (at bound 99.9/99.9/98.9 % of hours)
and the *reserve* against losing it in the armed Zone-K locational reserve
ladder — rule 19 `[R-ONE-MECH]`. Boundary is clean: the report's Appendix A
defines the Zone-K interface as Y49 + Y50 plus the two PAR-controlled 138 kV
J→K ties with the UDR cables counted separately, exactly the model's two-link
split.

**(2) MEASURED EX ANTE, NO SOLVE.** **100 % of the model's C3c tail hours in ALL
THREE years are Long Island**, inside HB14-21, with **both** Zone-K import paths
at their bound.

**(3) THE FIX AS SPECIFIED IS REJECTED BY ITS OWN PRE-REGISTERED KILL GATE.**
New field `nyiso_li_tsl_n11_security` (default off, zero free parameters, one
published number replacing another). Arms `2026-08-06-nyiso-130-control` /
`2026-08-06-nyiso-130-n11-tsl`, both registered. The control **reproduces the
keeper exactly** (22 h, all Zone K, bound 325) — the nyiso-128 stale-baseline
failure does not recur. K1–K5 all PASS (one differing field; zero slack/dump;
in-window bound reads exactly 940.0; no other link moves; the seam is exonerated
at 0.000/0.000/+0.047 %). **K6 FIRED.** C3c collapses **22/3/24 → 2/0/5** against
10/12/42 — all three years FAIL under-produced, **2024 forming zero scarcity
hours** — and the downstate ST_GAS reliability floor takes up the slack, forcing
**+0.22/+0.42/+0.23 TWh** more (share 20.4→22.2 / 22.0→26.0 / 15.4→17.0 %;
C8 still passes at 23.5/**27.9**/19.3 % against a 30 % cap). C1/C2/C3a/C3b/C4/C6/C8
PASS in **both** arms and the pre-registered C3a adverse case did **not**
materialise (mean LMP 33.855→33.604 / 37.043→36.937 / 61.113→61.113).

**(4) WHY THAT IS A REJECTION AND NOT RULE 1 IN REVERSE.** Not "the residual
didn't move" — a protective gate fired, substantively. The arm **relocates** a
proxy rather than removing one: Zone-K reliability here is carried by **two**
proxies (the too-tight transfer bound and the LI/NYC ST_GAS `min_gen` floor) and
relieving one loads the other, making the model *more* floor-driven — the
opposite of rule 20 `[R-FORCED-BUDGET]`. And it leaves the model forming
essentially no scarcity, a **mechanism** deficiency. **The incumbent's 2025 C3c
PASS is now understood as a right number produced by a number NYISO says is not
a transfer limit** — rule 1's second half. Matrix cell
`nyiso_li_tsl_n11_security` NYISO **`R`**. **Successor: a JOINT reconciliation of
the transfer bound AND the downstate ST_GAS floor (rule 19), one local-security
representation replacing both, with its own charter. Do NOT re-test the bare
swap.**

**(5) THE DETERMINATION RECOVERS, BY LEDGER NOT BY RESULT.** **Owner directive,
given in session, verbatim:** *"After this run if the only outstanding issue is
c3c scarcity tail of +12 hours in 2023 I want NYISO registered as calibrated
with caveats. C3c is an acceptable gate failure as a ledgered caveat."* The
condition is met exactly as stated on the incumbent — C3c is the **sole**
non-passing criterion and the 2023 miss is +12 h (22 vs 10). This supplies the
**in-training** authorization rule 22's C3c standing rule does not reach. **Two
disciplines kept, not waived:** the 2023 entry carries its **own correctly-signed
OVER-production classification** and does **not** ride under the inherited 2024
under-production caveat, and nyiso-129's withheld block is **preserved** as
`_withheld_exception_history` so the record shows the exception was AUTHORIZED,
not quietly widened; magnitude at full size. Ledgered caveats **1 of 1**.
`audit_keepers.py --iso NYISO` **PASS 0/0**; `complete` marker re-keyed with the
determination re-verified from committed artifacts (rule 22 D-5(b) — the label
IMPROVES, so the worse-determination stop does not fire).

**(6) PRIORITY 2 — the GWh reconciliation, DISCHARGED.** **981.8 GWh CONFIRMED;
nyiso-128's 1,081.8 GWh RETIRED.** An independent re-extraction reproduces
981.8 GWh over 573.4 MW / 15 units with no name-key collisions, and the capacity
total matches the separately-derived registry to 0.1 MW. The error is
**2025-only** — the 2024 and 2025 Gold Books reproduce nyiso-128's 2023
(229.9 GWh) and 2024 (503.2 GWh) exactly. nyiso-128's own third instrument
corroborates the reproduced figure: nyiso-106's MIS P-63 lower bound of
0.994 TWh sits **1.2 %** from 981.8 and **8.8 %** below 1,081.8. The 2025
over-removal is therefore **0.232 TWh**, not 0.332. **Reported against interest:**
the CF identification is *narrower* than inherited — measured CF against the
registry's own **monthly** capacity exposure is **0.1629 / 0.1468 / 0.1955**, a
33 % swing, so "measured 0.1955" is a **2025-only** statement. The swing selects
2025 for a non-fitted reason (2024 is the heavy build year and a monthly step
counts a commissioning plant as fully present; 2025 added no PV market
generator), making 2025 the only clean read of a mature fleet. The lever is
**identified, sized and NOT armed** — it pushes C3a and C3c the same direction as
the Priority-1 arm, so arming both on the same arms would make neither
attributable (rule 19).

**(7) FRONTIER / `complete`.** Marker re-keyed and determination re-verified;
`tier_authorized` and the absent `final` untouched. A frontier re-declaration
becomes assessable now that NYISO reads CALIBRATED-WITH-CAVEATS, but is **not
done here** — nyiso-127 §3 recommends RE-DECLARATION over a third amendment, and
the nyiso-127 §5 four-item decision package (including the phantom DOF entry
`GAS_AVAILABILITY_FACTOR[NYISO] = 0.866`, ledgered as living in `constants.py`
but present nowhere in `src/market_sim/`) remains **open and untouched**.

**(8) SESSION INTEGRITY NOTE, against interest.** The first recipe-fidelity check
ran without an explicit `--out-dir` and overwrote the committed
`results/calibration/nyiso128_control` bundle with a 24-hour solve. Caught
immediately, restored from git, and every tracked blob verified byte-identical to
`HEAD` before work continued. The A/B driver's default out-dir points at a
**committed** bundle — pass `--out-dir` always.

Evidence:
`results/calibration/FINDING-nyiso130-li-transfer-security-limit-2026-08-06.md`,
`PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md`,
`PREREG-nyiso130-solar-cf-level-2026-08-06.md`,
`_nyiso130_ab_gates.json`, `_nyiso130_li_tsl_identification.json`,
`_nyiso130_solar_gwh_reconciliation.json`, probes
`scripts/probes/_nyiso130_li_tsl_identification.py`,
`_nyiso130_ab_gates.py`, `_nyiso130_solar_gwh_reconciliation.py`.

* Next number: **nyiso-131**.

## 2026-08-06 — RECORD CORRECTION (owner decision D-23, cross-ISO): NEISO's locked test was NEVER GRANTED, not "SPENT"

**GOVERNANCE lane, committed artifacts only. No solve, no scoring, no year touched,
no NYISO lane state changed. Correct-by-addendum — the entry below is left intact.**

The tiered-holdout entry in this log (§ "locked test | 2019, 2026 (H1) | **`final`**")
states that **"NEISO's locked test is already SPENT (2026-07-07, frozen neiso-53) and
must never be re-granted"**, and uses that as the worked contrast against NYISO's
"never scored, not granted". **The NEISO half of that contrast is false.** No NEISO
2019 or H1-2026 year has ever been solved, scored or registered: every NEISO registry
sidecar ever committed declares years drawn only from {2022, 2023, 2024, 2025},
`bench/NEISO/` holds 2022–2025, `actual_tail.json` has no 2019 row, and the memo cited
as the authorization never mentions 2019. **NEISO is in the SAME category as NYISO —
never scored, not granted.**

Nothing about **NYISO's** posture changes: NYISO holds `complete` (validation only),
is absent from `final`, and `holdout_policy.authorized(NYISO, locked_test)` is still
`False`. The surviving general point is also unchanged and still correct — *a blank
`final` must never read as an invitation* — but the reason is now uniform across ISOs
rather than ISO-specific: **no ISO is currently in the "spent" state at all**, so every
blank today means "never authorized".

Citation chain: `results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
`docs/third-party-peer-review-2026-07.md` §6.3 item 1 → **owner decision D-23, SIGNED
at the 2026-08-06 sitting Addendum X.6**. Full record:
`docs/handoffs/neiso-record-correction-2026-08-06.md`.

## 2026-08-07 — nyiso-131: KEEPER → `2026-08-07-nyiso-131-taxgs-arm` (owner decision D-27, gas_st taxonomy)

**GOVERNANCE lane, committed artifacts only. NO SOLVE, no mechanism tested, no year touched,
no cell verdict moved, no matrix row added.**

**Owner decision D-27, SIGNED at the 2026-08-06 sitting Addendum AA.4 (2026-08-07)**, verbatim:
*"D-27 — SIGNED AS RECOMMENDED: NYISO promotes now, MISO defers."* This session executes the
NYISO half only; **MISO's paired `taxgs` arm stays registered-not-promoted** by the same decision,
pending its own lane settling the Addendum AA.2 rubric-v3.1 C3a re-score question, and no MISO
file was touched.

### What was promoted

`2026-08-06-nyiso-128-solar-basis` → **`2026-08-07-nyiso-131-taxgs-arm`**
(bundle `results/calibration/nyiso131_taxgs_arm`, years 2023–2025, registered at the
taxonomy session under the Addendum-D paired-control + HOLD-PROMOTION discipline).

**It is the incumbent's own recipe, not a new one.** The arm is a same-head `replay_keeper` of
the keeper's own bundle (`nyiso128_treatment`) with owner decision **D-25** applied. Verified,
not asserted: of the arm's 698 `scenario_config` fields, the **693 shared with the keeper are
identical (zero differing)**, and the 5 arm-only fields are entries that landed on `main` after
the keeper solved, **all five at default `False`** — including `nyiso_li_tsl_n11_security`, the
nyiso-130 lever rejected on its own kill gate, confirmed **not armed**. So the whole nyiso-128
lineage (nyiso-100 SIL retirement → 109 zonal gas-offer anchor → 117 NYC RCPF → 118 ORDC measured
step span → 119 SENY increment → 120 East River scope gate → 125 seam envelope → 128 solar basis)
stays armed and unchanged.

**What D-25 changes:** natural-gas steam turbines (EIA-860 prime mover `ST`, energy source `NG`)
map to the dedicated `gas_st` fuel — the fuel the CAMPD bin path always carried via
`BIN_GROUP_TO_FUEL` — instead of folding into `gas_ct`. A rule 14 `[R-ACCURATE]` correction: the
class structure was already right (`classify_plant` has had `ST_GAS`/`ST_CHP` all along) and only
the **fuel label on the loader record** was wrong, where it set the heat-rate fallback, VOM,
EFORd, CO2/NOx and the **scoring-target fuel**. NYISO's entire solve-affecting residue is **one
synthesized-bin heat rate** — RED-Rochester ST_CHP, 11.454 → 10.3 MMBtu/MWh on 119.6 MW. Zero
free parameters, zero `ScenarioConfig` fields (so rule 28(c) books no matrix row; CI's
`mechanism-matrix-guard` checks that half and there is no new field).

### Rule 22 D-5(b) re-key — determination RE-VERIFIED, stop does NOT fire

NYISO holds `complete`, so the marker's `keeper` field re-keys **and** its `determination` is
re-verified against the new run before the promotion commit lands. Run:
`scripts/calibration_verdict.py --run-id 2026-08-07-nyiso-131-taxgs-arm`, committed artifacts
only, **never a solve**.

| | incumbent `nyiso-128-solar-basis` | promoted `nyiso-131-taxgs-arm` |
|---|---|---|
| determination | CALIBRATED-WITH-CAVEATS | **CALIBRATED-WITH-CAVEATS** |
| C1 / C2 / C3a / C3b / C4 / C6 / C8 | PASS | **PASS** (identical) |
| C3c | lone ledgered caveat | **lone ledgered caveat** (identical) |
| ledger budget | 1 of 1 | **1 of 1** |

**The label is identical, so D-5(b)'s worse-determination stop does not fire and no escalation is
owed.** The re-verification is criterion-for-criterion, not label-only. The only difference across
the two scorer runs is an **ungated SKIPPED diagnostic line** (C3a-2023 DA diagnostic
+6.7 % → +6.6 %).

### Deltas, reported at full size

Verdict grain: nothing moves. Hourly grain: not byte-identical.

| year | class energy deltas (TWh, arm − control) | demand-wt ΔLMP | max zonal \|ΔLMP\| |
|---|---|--:|--:|
| 2023 | ST_CHP +0.037; ST_GAS −0.016; CC_REGULAR −0.011; CC_CHP −0.007 | −0.013 $/MWh | 1.25 |
| 2024 | ST_CHP +0.052; CC_REGULAR −0.023; CC_CHP −0.016; ST_GAS −0.012 | −0.023 $/MWh | 3.85 |
| 2025 | ST_CHP +0.005; CC_REGULAR −0.002; CC_CHP −0.001; ST_GAS −0.001 | −0.002 $/MWh | 2.71 |

34 of 188 numeric verdict fields move; **no gate is approached, let alone crossed**. Direction is
physical and follows from the sign of the correction: the corrected (cheaper, EIA Table 8.2) heat
rate lets the cogen bin run more, displacing merchant CC and the ST_GAS class.

### What this promotion does NOT do

* **Does not close, narrow or re-open C3c.** Tail counts are the incumbent's; the diagnosed owner
  is unchanged (100 % of the modelled tail in all three years is Long Island inside HB14-21 with
  both Zone-K import paths at their bound). The successor remains the **chartered joint
  reconciliation** of the Zone-K transfer bound and the downstate ST_GAS `min_gen` floor under
  rule 19 `[R-ONE-MECH]` — the bare 940 MW number swap was pre-registered, tested and **rejected**
  on kill gate K6 at nyiso-130, and must not be re-tested.
* **Does not restore frontier status.** NYISO's frontier was CLEARED 2026-08-06 and stays cleared.
* **Does not touch the holdout posture.** `complete` (validation only) untouched, NYISO stays
  **absent from `final`**, and the ACTIVE holdout spend freeze independently blocks every
  out-of-training solve. 2023–2025 only.
* **Does not change the lever queue:** (1) the joint Long Island transfer-bound / `min_gen`
  reconciliation, (2) the NYISO solar **CF level** (`RENEWABLE_AVG_CF` 0.15 Tier-3, realized
  ~0.133, vs a measured 0.1955 on the registered fleet).

### Artifacts changed

`frontend/data/backcast/keepers/NYISO.json` (keeper + promotion note),
`frontend/data/backcast/status/NYISO.js` (rebuilt, `build_status.py --iso NYISO`),
`frontend/data/backcast/calibration-complete.json` (D-5(b) re-key + `rekey_history`),
`docs/codebase-site/data/mechanism-matrix.js` (keeper stamp, header, NYISO gates clause),
`docs/mechanism-testing-matrix.md` (§5.5 prose header), this log, and
`docs/handoffs/nyiso-taxgs-promotion-2026-08-07.md`.

Gates run: `scripts/audit_keepers.py --iso NYISO` **PASS 0 failures / 0 warnings** (M1),
`scripts/check_mechanism_matrix.py` clean on all four checks.

Evidence: `docs/handoffs/taxonomy-gas-st-2026-08-07.md` §4.1,
`docs/handoffs/ffr-owner-sitting-2026-08-02.md` §§AA.3–AA.4,
`docs/handoffs/nyiso-taxgs-promotion-2026-08-07.md`.

* **Session numbering:** `nyiso-131` is consumed by this promotion (the run id
  `2026-08-07-nyiso-131-taxgs-arm` already carries it). Next number: **nyiso-132**.

## 2026-08-07/08 — nyiso-132: solar CF LEVEL armed and A/B'd (0.15 -> 0.1955). KEEPER UNCHANGED pending owner call

**Lever-queue item 2, the second of the two named successors.** Paired A/B on the
keeper recipe `2026-08-07-nyiso-131-taxgs-arm`, 2023-2025, both arms registered:
`2026-08-08-nyiso-132-cf-control` / `2026-08-08-nyiso-132-cf-arm`.
Charter: `PREREG-nyiso130-solar-cf-level-2026-08-06.md` §4; ex-ante settlement:
`PREREG-nyiso132-solar-cf-level-2026-08-07.md`; result:
`FINDING-nyiso132-solar-cf-level-2026-08-07.md`.

**Construction (owner decision, in session): UNGATED `constants.py` edit**, the
D-25 / caiso-175 pattern — zero `ScenarioConfig` fields, so the A/B runs on the
paired-control **tree** harness and its config-isolation gate is inverted
(configs must be identical). The gated-flag alternative was declined: a permanent
gate whose "off" position is the known-wrong value is the rule 26 `[R-DELETE]`
anti-pattern for a pure accuracy repair. Declared blast radius, stated before the
choice: this also moves the NYISO **forecast** lane, where 11 committed
`nyiso-*` hindcast sidecars exist.

### The control reproduces the keeper byte-identically

The replay flagged a toolchain drift (platform v18->v20, highspy 1.14.0->1.15.1,
pandas 3.0.3->3.0.5, pyarrow 24.0.0->25.0.0), so this was treated as
load-bearing, not a formality. Against the keeper's committed sidecars: **0.000
GWh** per class-year (14 classes x 3 years), **max |delta| 0.000000000 MW** over
122,640 hourly P1 rows x 3 years, and identical `reserve_family` duals. The
nyiso-128-class hazard — a control that fails to reproduce its keeper — does not
fire, so the arm's delta is attributable to the CF alone.

### Result: determination identical, both adverse cases refuted

`CALIBRATED-WITH-CAVEATS` in **both** arms, all 8 criterion statuses identical
(C1/C2/C3a/C3b/C4/C6/C8 PASS; C3c the lone ledgered caveat, budget 1 of 1).

| criterion | actual | control | arm |
|---|---:|---:|---:|
| C3a 2023 | 32.25 | 35.12 (+8.90 %) | **35.08 (+8.78 %)** |
| C3a 2024 | 38.13 | 38.50 (+0.97 %) | **38.40 (+0.71 %)** |
| C3a 2025 | 66.45 | 64.36 (-3.14 %) | **64.16 (-3.45 %)** |
| C3c 2023 | 10 h | 22 h (2.20x) | **21 h (2.10x)** |
| C3c 2024 | 12 h | 3 h | **3 h** |
| C3c 2025 | 42 h | 24 h PASS | **24 h PASS** |

Pre-registered adverse cases, both **refuted by measurement**: C3a-2025 did NOT
cross -10 % (largest mean-LMP move in any year 0.31 %), and C3c-2025 did NOT
fall through its 21 h floor (unchanged at 24 h). C3c-2023 improves by one hour.
Construction gates K1-K4 all PASS (K1 after folding six checkout-prefix `*_path`
artifacts the sibling control tree reports — the same fold
`_normalize_cache_key_paths` applies to the cache key).

### Reported against interest, and the defect it opened

Solar vs the published Gold Book registry: **-7.1 / +2.4 / -23.3 %** ->
**+20.9 / +33.2 / -0.1 %**. The arm buys an essentially exact mature year and
costs **two** advisory-band breaches instead of one. That band
(`calibration_verdict.VRE_TOL`, +/-10 %) is explicitly **report-only** and D-10
classes solar `delivered_pinned` — "advisory-only, excluded from skill claims" —
so no gated criterion moves on it; but it is not called a clean win.

The cause is named and is its **own object** (rule 19 `[R-ONE-MECH]`, not
bundled): **the model has NO COMMISSIONING CURVE.** The monthly capacity ramp
counts a plant fully from its in-service month, so one CF cannot track a fleet
whose realized CF runs 0.1629 / 0.1468 / 0.1955 (worst in 2024, the heavy build
year, mean-month/year-end 0.6800). Carried as an open item in the arm's
attestation.

### Falsified en route

The nyiso-130 prereg attributed the 0.15 -> 0.133 gap to "clipping and the donor
profile". **Both limbs refuted**: the distribution sums to 1.000000, the hourly
mean cf is **0.150000 exactly**, and **zero hours clip** in all three years. The
gap is entirely the year-end-capacity **denominator convention**; on the
registered basis in the flat 2025 fleet the model realizes **0.1500 exactly**.
This decided the sizing — off the constant, 2025 lands at 981.3 GWh vs a
published 981.8 (-0.1 %); off the reported 0.133 it would have over-shot the
fleet's own published output by **+12.3 %**.

### Status

**KEEPER UNCHANGED at `2026-08-07-nyiso-131-taxgs-arm`.** The session recommends
PROMOTE (structure improves, zero free parameters, `n_residual` unchanged at 6,
no gated criterion regresses), but promotion is the owner's call and the keeper
shard, the `complete` marker and the matrix keeper stamp are all untouched. The
matrix cell `vre_avg_cf_level` NYISO is **`O`** — built and adjudicated, armed on
no keeper. Rule 25: NEISO carries the identical Tier-3 0.15 and is **not**
covered (cell `U`).

Retention: the top-15-per-ISO sweep pruned `2026-08-04-nyiso-120-c119-scope` and
`2026-08-04-nyiso-120a-control`.

* Next number: **nyiso-133**.

## 2026-08-08 — nyiso-132 PROMOTION: keeper -> `2026-08-08-nyiso-132-cf-arm` (solar CF level)

**Owner ruling, session nyiso-132, verbatim:** *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper."* The session's recommendation was **YES** on rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]` — and the standing structure-over-gates clause
was **not needed**, because **no gate regresses**.

Keeper `2026-08-07-nyiso-131-taxgs-arm` -> **`2026-08-08-nyiso-132-cf-arm`**
(bundle `nyiso132_cf_arm`). Full A/B evidence is the entry above; this entry
records the promotion itself.

**Rule 22 D-5(b) re-key:** NYISO holds `complete`, so the marker's `keeper` field
re-keyed **and** its determination was re-verified against the new run on
committed artifacts (`calibration_verdict.py --run-id`, **no solve**). Result
**`CALIBRATED-WITH-CAVEATS` — IDENTICAL** to the superseded keeper, all 8
criterion statuses matching (C1/C2/C3a/C3b/C4/C6/C8 PASS; C3c the lone ledgered
caveat, budget 1 of 1), so the **worse-determination stop does not fire**.
`rekey_history` now carries 4 entries.

**Rule 28:** matrix keeper stamp re-pointed, header re-stamped, §5.5 prose header
re-stamped, and the `vre_avg_cf_level` cell moved **`O` -> `K`** for NYISO in the
same session that tested it. Guard clean on all four checks; `audit_keepers.py
--iso NYISO` **PASS 0/0** (M1).

**Lever queue after this promotion:**

* item 2 (solar CF level) — **CLOSED-with-keeper**
* item 1 (the chartered **joint** Zone-K transfer-bound + downstate ST_GAS
  `min_gen` reconciliation under rule 19) — **REMAINS OPEN**, unchanged
* **NEW**, opened by this session — **the model has no commissioning curve**
  (one CF cannot track a fleet whose realized CF runs 0.1468-0.1955); it is the
  declared cause of the solar advisory-band trade and is carried as an open item
  in the keeper's attestation

**Holdout posture UNCHANGED:** `complete` (validation only) untouched, NYISO stays
**absent from `final`**, and the ACTIVE holdout spend freeze independently blocks
every out-of-training solve. C3c is neither closed nor narrowed.

**Open cross-lane item, flagged not fixed:** because the construction is
**ungated**, the constant is on `main` and the NYISO **forecast** lane's 11
committed `nyiso-*` hindcast sidecars are stale with respect to HEAD. That was the
declared blast radius of the ungated choice and belongs to the forecast lane's own
governance (rule 15's separate namespace).

* Next number: **nyiso-133**.

## 2026-08-08 — nyiso-133: the commissioning-curve attribution is REFUTED; the defect is the in-service DATE basis. All seven gates PASS, KEEPER UNCHANGED pending the owner call

**Lever-queue item 2 as nyiso-132 named it, RE-POINTED BY MEASUREMENT before any
mechanism was built.** Paired single-delta A/B on the keeper recipe
`2026-08-08-nyiso-132-cf-arm`, 2023–2025, both arms registered:
`2026-08-08-nyiso-133-cod-control` / `2026-08-08-nyiso-133-cod-arm`.
Pre-registration: `PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md`;
result: `FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md`; records
`_nyiso133_commissioning_ramp.json`, `_nyiso133_ab_gates.json`. Rule 22:
2023–2025 only; the ACTIVE holdout spend freeze was checked and not touched.

### (1) The queue item is REFUTED, ex ante, with no solve spent

nyiso-132's named successor was *"THE MODEL HAS NO COMMISSIONING CURVE."*
Measured nationally first: 730 single-vintage EIA-860 `OP` PV plants ≥ 5 MW
(36.4 GW, COD 2019–2022) against their own EIA-923 monthly metered history,
two-way normalized by a mature-plant peer index per calendar month × each
plant's own permanent quality factor. A new utility PV plant runs at **0.723**
of mature in its COD month, **0.962** at month+1 and is **mature from month 2**;
a placebo cohort (age 36–47) reads **1.0072**, calibrating the estimator. The
whole commissioning shortfall is **0.321 month-equivalents** of nameplate —
≈ 18 GWh on NYISO's 399 MW 2024 build wave against a +167 GWh over-statement,
**~11 % of the effect it was named to explain**. No commissioning curve is
built. This is the durable result and it stands whatever happens to the arm.

### (2) What the same measurement found instead — the DATE basis

The Gold Book Table III-2a **"In-Service Date"** is a registration /
interconnection-service date and **leads** the plant's metered commercial start;
**EIA-860's `Operating Month` matches it — equal to the first metered EIA-923
month in 11 of the 12 uncensored plants.** The Gold Book leads **+2 months on
Morris Ridge (179 MW, 31 % of the 2025 fleet)**, +1 on High River (90 MW), East
Point (50 MW), Calverton, Puckett, Janis, Grissom and Long Island Solar Farm —
and **TRAILS by 1 and 3 months on Darby and Stillwater**. Signed **both ways**,
so it is a basis difference, not a correction aimed at the residual.

### (3) The mechanism

`ScenarioConfig.nyiso_solar_registry_cod_dates`, **gated, default off,
byte-identical**. The derive script emits both published bases as parallel
columns of the same artifact (`capacity_mw` / `capacity_mw_cod`); membership and
nameplate stay 100 % Gold Book and only the switch-on month moves. Rule 14
`[R-ACCURATE]`'s reconciled-real-data path, rule 13 admissible (an input that
regenerates forward through EIA-860M), **ZERO free parameters** — the crosswalk
is a 15-row identity between two registries, each row verified on nameplate
agreement and **dropped** rather than guessed when it fails. DOF ledger **36 →
37 entries, `n_residual` UNCHANGED at 6**, the new entry identified `published`.
The gated construction was chosen over nyiso-132's ungated pattern, before the
result was known, to keep the A/B a clean single delta and to avoid silently
re-staling the NYISO forecast lane's committed hindcast sidecars.

### (4) The control reproduces the superseded keeper EXACTLY

**Max |class-year energy delta| = 0.000 GWh** over 14 classes × 3 years — and
unlike nyiso-132 **no toolchain-drift excuse was available**: this session's
environment matches the keeper bundle's recorded one exactly (Python 3.11.15,
highspy 1.15.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.5, pyarrow 25.0.0,
pydantic 2.13.4, same platform).

### (5) ALL SEVEN pre-registered gates PASS; the determination is identical

K1 config isolation (exactly ONE differing field of 701), K2 feasibility, K3
liveness (**arm/control solar energy 1.0118 / 0.8746 / 1.0000 against ex-ante
predictions of 1.0118 / 0.8746 / 1.0000**, measured through
`load_renewable_profiles` before the solve), K4 scope (wind identical at 0.000
GWh), K5 no gated regression, K6 no scarcity collapse, K7 forcing budget — all
**PASS**. Determination **`CALIBRATED-WITH-CAVEATS` in both arms**, all 8
criterion statuses identical, C3c the same lone ledgered caveat (budget 1 of 1).

| criterion | actual | control | arm |
|---|---:|---:|---:|
| C3a 2023 / 2024 / 2025 | 32.25 / 38.13 / 66.45 | +8.8 / +0.7 / −3.4 % | **+8.8 / +0.8 / −3.4 %** |
| C3c 2023 / 2024 / 2025 | 10 / 12 / 42 h | 21 / 3 / 24 h | **21 / 3 / 24 h** |

Hourly grain at full size: demand-weighted ΔLMP **−0.0023 / +0.0345 / 0.0000
$/MWh**, max zonal |ΔLMP| 4.55 / 5.67 / 0.00, and **2025 is BIT-IDENTICAL (zero
hours move)** — the construction's own prediction, since the 2025 registry is
flat and the two bases coincide. 2024 solar −84.06 GWh is taken up by
CC_REGULAR +41.94, ST_GAS +21.28, CC_CHP +14.10; C1 moves four cells, all
staying PASS, with **ST_GAS-2024 moving TOWARD its actual** and CC_REGULAR-2024
away. C8 ST_GAS-2024 24.5 → 24.4 %.

### (6) Reported against interest

Solar vs the published registry: **+20.9 → +22.3 % (2023, WORSE)**, +33.2 →
**+16.5 % (2024)**, −0.1 % (2025, unchanged). **ADV-1 materialized exactly as
pre-registered** and was expressly ruled out ex ante as grounds for rejection —
the band is report-only and D-10 classes NYISO solar `delivered_pinned`. Rule 1
`[R-STRUCT]`: the accurate input stays. The signature that this is a repair and
not a fit is the **coherence**, not the level: the implied fleet CF goes from
0.1629 / 0.1473 (adjacent years disagreeing by 10 %) to **0.1613 / 0.1641**
(agreeing to 1.7 %), and nothing in the construction targets that quantity.
Second disclosed cost: 2023 year-end registered capacity rises 174.4 → 194.4 MW
because Stillwater's EIA-860 month is 2023-11 and EIA-923 records it metering
745 MWh that December.

### (7) A test that has been FAILING ON MAIN, found and repaired

`tests/test_nyiso_market_solar.py::test_flag_off_is_byte_identical_and_on_moves_only_solar`
asserts the armed 2024 energy at `approx(0.503, rel=0.10)`. That was right at
CF 0.15; **nyiso-132's ungated re-level to 0.1955 made the quantity 0.670 TWh
and the assertion was not updated**, so the test has been red on `main` since
that promotion. Confirmed against `origin/main`'s own artifacts, not inferred.

### (8) Status and the lever queue

**KEEPER UNCHANGED at `2026-08-08-nyiso-132-cf-arm`.** The session recommends
**PROMOTE** (structure improves, zero free parameters, `n_residual` unchanged,
no gated criterion regresses, the control reproduces exactly, 2025
bit-identical), but promotion is the owner's call and the keeper shard, the
`complete` marker and the matrix keeper stamp are all untouched. Matrix cell
`vre_registry_cod_date_basis` NYISO is **`O`** — built and adjudicated, armed on
no keeper. **If promoted, the gate should be collapsed to unconditional**
(rule 26 `[R-DELETE]`) — flagged, not taken.

**Lever queue after this session:**

* item 1 — the chartered **joint** Zone-K transfer-bound + downstate ST_GAS
  `min_gen` reconciliation (rule 19) — **REMAINS OPEN**, untouched
* item 2's stated cause (no commissioning curve) — **REFUTED**, §1
* **NEW, replacing it** — the **fleet-CF COMPOSITION** object: after the date
  repair 2023 and 2024 both imply ~0.162 against 2025's 0.1955, and the residual
  is measured per-plant mature CF (0.174–0.182 for the 2021–22 small fixed-tilt
  NY8 units vs 0.198–0.221 for the 2024 tracking plants). One ISO-wide
  `RENEWABLE_AVG_CF` cannot track a fleet going from 100 % fixed-tilt to 56 %
  large tracking across the span

**Holdout posture UNCHANGED:** `complete` (validation only) untouched, NYISO
stays **absent from `final`**, the ACTIVE spend freeze independently blocks
every out-of-training solve. C3c is neither closed nor narrowed — it is
bit-unchanged.

Retention: the top-15-per-ISO sweep pruned `2026-08-04-nyiso-120a2-control-samehead`
and `2026-08-04-nyiso-120b-scope-gate`.

* Next number: **nyiso-134**.

## 2026-08-14 — nyiso-134: the 2022 validation touchpoint is REFUSED on DATA READINESS — three silent input defects (RGGI, Central-East TTC, SCR/EDRP vintage); no LP solved

Phase-1-only session. Task: test the frozen keeper on the 2022 validation
touchpoint, **gated on first proving in writing** that every measured input 2022
needs is at the same standard as 2023-2025. The proof **failed**, so the solve
was never attempted. Full assessment:
`results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md`.

**Gate state.** The holdout spend freeze is **ACTIVE** at HEAD
(`holdout-freeze.json` `"active": true`, re-armed 2026-08-06; no lift in
`history` names a NYISO spend), and independently blocks the spend. NYISO holds
`complete` (validation only, keeper `2026-08-08-nyiso-132-cf-arm`) and stays
**absent from `final`**. Baseline re-verified from committed artifacts with no
solve — `calibration_verdict.py --run-id 2026-08-08-nyiso-132-cf-arm` →
**CALIBRATED-WITH-CAVEATS**, C3c the lone ledgered caveat, matching the marker.
All 15 registered NYISO runs are 2023-2025; NYISO has never solved 2022.
**The freeze is NOT the reason for the verdict** — the defects below would block
the solve even with a lift in hand.

**Three BLOCKING defects, all silent (no exception, no warning, no log line):**

* **D-1 — RGGI allowance cost is ZERO in 2022.**
  `STATE_CARBON_PRICE_BY_ISO["NYISO"]` = {2023, 2024, 2025} only;
  `state_carbon_price` returns `None` and the keeper's `carbon_price_path="zero"`
  catches it, so 2022 prices every in-state fossil unit with **no** allowance
  cost while each in-sample year carries one. From the model's own 2022
  `plant_emission_rates_v2` rows: fleet **0.4558 tCO2/MWh** → **$6.08/MWh**
  omitted at ~$13/tCO2, **8.1 % of the 2022 RT mean ($74.77)** — and **not a
  level shift**, the CC-to-steam spread is **2.9x** (CC $5.53, CT $7.21,
  tangential $8.04, dry-bottom wall $15.85), so it **re-orders the merit stack**.
  Fix is a 4-number transcription (RGGI auctions A55-A58) by the recipe
  `config/fuel_trajectories.py` already documents. Zero DOF.
* **D-2 — the 2022 solve would run on a transmission line built a year later.**
  `NYISO_INTERFACE_TTC_BY_YEAR` / `_BY_MONTH` cover 2023-2025 only and **both
  appliers silently return unchanged** on a missing year. Central-East
  (Upstate_West->Capital_Hudson) resolves to the **static 2,850 MW post-upgrade**
  value for 2022 — against the model's own pre-upgrade 1,750 MW (2023), that is
  **+1,100 MW / +63 %** of upstate->downstate capability that the NY Transco AC
  Transmission project did not deliver until **December 2023** — and 2022 also
  loses the monthly envelope entirely (flat, vs 2023's measured 1,450-2,725 MW).
  Direction is the damaging one: extra Central-East capability **relieves** the
  congestion that forms downstate scarcity, i.e. it lands directly on **C3c**,
  NYISO's sole open caveat. A 2022 C3c result on this input is uninterpretable.
  This is the precedent-(1) failure mode exactly.
* **D-3 — SCR/EDRP clamps to the wrong Gold Book** (bounded). `gb_year =
  min(max(year, _MIN_GB_YEAR), _MAX_GB_YEAR)` clamps 2022 **up** to the 2023
  vintage; the 2022 Gold Book is not on disk. ~1.23 GW of emergency DR placed at
  the wrong vintage, error bounded at ~60-190 MW by the observed drift
  (+4.9 %/+14.9 %) — modest, but at a **$500/MWh strike**, i.e. inside the
  scarcity band C3c measures.

**The highest-risk input PASSED.** The 2026-07-19 stale-detector defect (the
withdrawn marker; 1,598 vs 2,641 windows) **does not reproduce**. The extract is
one blob over a continuous 2018-2026 span, and a full re-derivation at HEAD
defaults proves the recipe exactly: `committed U layup == no-guard re-derivation`
and `committed ^ layup == {}`, with **zero** only-in-committed orphans in **every**
year. Per-year committed+layup == re-derived is exact 2018-2026 (2022:
533+317=850). 2022 is envelope-comparable on windows (533 vs 464-540), median
duration (14.30 vs 12.20-14.85 d) and units (92 vs 84-99).

**Also EQUIVALENT** (measured, not assumed): the gas chain — 2022 is on the
in-sample Iroquois-Z2-minus-HH construction, the **neiso-85 inversion does NOT
reproduce** (W-S +3.650, between 2023's +1.380 and 2025's +5.199), and the
SOM anchor ratio **0.944** sits inside the in-sample band 0.900-1.045; the LMP
bench (8,760 x 2 markets, zero nulls, DA $72.73 matching the register's
re-clocked value **exactly**, all five `_lw` fields at parity); emission rates v2
(382 rows / 120 plants, 90.8 % measured, reproducing the register's quoted means
exactly); reserve requirements (61,320 rows, **identical** to each in-sample
year); capacity deliverability on the path the keeper actually uses
(`import_limit`, since `nyiso_li_tsl_n11_security=False`); nuclear availability;
demand/zonal load/CAMPD/weather/neighbour LMPs/interface flows; and the LDC
transport rows, which are **real, not padded** — 24 rows each citing a distinct
correctly-numbered statement `statnfdr-5-eff-01-01-22` .. `-16-eff-12-01-22`.

**Two register statements CORRECTED by measurement:** the "firm-import floor
missing 2022" item names a **MISO** constant — NYISO uses the year-invariant
`NYISO_FIRM_IMPORT_FLOOR_FRAC`, so there is no gap; and the unit-outage "MISSING
2022 + DEGRADED vintage" item is resolved (§3.1 above). D-1/D-2/D-3 are **new** —
none appears in the register.

**Disclosed, non-blocking:** the Transco **Dec-2022 Elliott hole** (prints stop
2022-12-21) is EQUIVALENT on provenance and coverage — its 10-day trailing gap is
the **smallest** of 2022/2023/2024 (vs 11 d / 13 d) and 2022 has the most
December prints — but the same-sized hole *contains a real event* in 2022 where
in-sample it contains nothing, so the December/winter-tail limit must be declared
before quoting any such result. Import-tranche 2022 duration RMSE 719 MW vs
<=328 in-sample is carried forward from the register, **not** re-measured here.
`bench/NYISO/2022.json.gz` is **not independently buildable** — `build_payload`
reads the bundle's own solve artifacts, so the bench part is a **by-product of
registering a 2022 run**, not a prerequisite for one.

**Fix path** (all zero-DOF intake or a fail-loud guard; none is a parameter, none
touches the keeper recipe, and under the 2026-08-06 clarification — *what is held
out is the SCORE, never the DATA* — all of it is unrestricted, marker-free, and
must be applied consistently across 2019-2025): transcribe RGGI 2022 (and check
NEISO, same gap); land the 2022 Central-East limit + envelope **and separately
make both TTC appliers fail loud on a missing backcast year**, since a silent
fallback to a *later* topology is a latent trap for every out-of-training year;
fetch the 2022 Gold Book. Then the touchpoint needs only an owner lift.

**Nothing was registered, promoted or spent.** Keeper, `complete` marker,
`final` (still empty), the freeze, and every matrix cell verdict are unchanged;
2018 / 2019 / H1-2026 were not touched. No mechanism was tested.

* Next number: **nyiso-135**.

### UPDATE, same session — owner said "go get the data": ALL THREE DEFECTS CLOSED

Owner direction after the report above (*"Ok go get the data"*, then *"Get
2018-2021 while you're at it"*). Every fix uses the SAME producer and SAME
recipe as the incumbent years, and in each case **the recipe was verified
against the committed 2023-2025 values BEFORE the new years were written**.
ZERO free parameters. STILL NO LP SOLVED — the readiness objection is withdrawn,
so the freeze is now the only thing between here and the touchpoint.

* **D-1 RGGI — CLOSED 2018-2022.** Fetched RGGI, Inc.'s published prices/volumes
  table (the source already cited for A59-A70) and landed auctions **A39-A58**
  as per-auction rows. Recipe check: recomputing 2023/2024/2025 reproduces the
  committed 13.49/20.71/22.09 (NYISO) and 14.87/22.83/24.35 (NEISO) EXACTLY.
  New NYISO $/short ton: 2018 **4.41**, 2019 **5.42**, 2020 **6.41**,
  2021 **9.47**, 2022 **13.46**; NEISO x1.10231. So the 2022 omission is
  **$6.13/MWh** measured (the "~$13/tCO2" estimate was sound).
  **A blocker inside the fix:** `curate_carbon_auction_results.py` hard-coded
  `_QUARANTINED_YEARS = {2022, 2026}` and RAISED on those rows — the
  PRE-2026-08-06 regime the owner explicitly replaced, and the reason the
  constant had no 2022 key. Removed with the clarification quoted at the site;
  spend gates untouched. NEISO extended too (same auctions) — **declared blast
  radius: NEISO's registered 2026-08-06-neiso-2022-corrected-basis is now STALE
  w.r.t. HEAD**, a NEISO-lane call, flagged not actioned. CAISO NOT extended
  (CARB source blocks automated fetches; open CAISO-lane gap, rule 25).
* **D-2 Central-East TTC — CLOSED 2018-2022, and the trap is SHUT.** Fetched 96
  monthly MIS `atc_ttc` postings (2018-2025, 0 failures). Recipe check:
  re-deriving 2023/2024/2025 reproduces the committed annuals 1750/2850/2850
  **and every committed monthly value, exactly**. **THE FINDING WAS WORSE THAN
  REPORTED:** measured 2022 annual is **1,825 MW** (not the 1,750 proxy), so the
  silent static fallback overstated by **1,025 MW / +56 %** — and 2022 was
  mid-construction, so the monthly detail is the real damage: **Nov-2022 measured
  725 MW against a model 2,850 = 3.9x**, with Mar/Apr/May/Oct at 1.8-2.5x. New
  annuals 2018 2475, 2019 2475, 2020 2400, 2021 2025, 2022 1825 — a coherent
  decline into construction, then the post-upgrade step. **Structural half done:**
  both appliers now FAIL LOUD instead of silently no-opping, scoped to years at
  or beyond the table's span, so a year PAST the table still no-ops (there the
  static value is correct — it IS the measured post-upgrade annual mean, forward
  channel = the transmission-expansion registry). Forecasts unaffected; new test
  pins it; the existing forward-edge no-op test still passes.
* **D-3 SCR/EDRP — CLOSED 2019-2022; 2018 is a REAL SOURCE GAP.** The older Gold
  Books are NOT at the `20142/2226333/<year>-Gold-Book-Public.pdf` pattern (all
  404) — different Liferay document IDs and filenames. All five fetched and
  committed. Recipe check: a table parser reproduces the committed 2023/2024/2025
  transcriptions EXACTLY (33 zone-rows x 4 values, zero diffs) before being used
  on new years. **2018 has NO per-zone table at all** — NYCA totals only (p.39
  prose, Tables IV-1a/IV-1b); the zonal table first appears in 2019. Splitting the
  2018 total by another year's shares would be fabrication (rule 14), so it was
  NOT done; no practical loss since 2018 is locked-tier and unsolvable.
  **A SECOND HIDDEN DEFECT found while fixing this:** landing the vintages changed
  nothing, because `nyiso_demand_response` hard-coded `_MIN_GB_YEAR=2023` /
  `_MAX_GB_YEAR=2025` and the clamp still floored every earlier year at 2023 EVEN
  WITH THE DATA PRESENT. Bounds are now DERIVED from the CSV. Each year now
  resolves to its own vintage; 2022 moves **1234.4 -> 1169.8 MW**, a 64.6 MW
  correction inside the predicted 60-190 MW band, at a $500/MWh strike.

**Verification.** ruff clean; format clean; mechanism-matrix guard exit 0. Full
suite **6,849 passed / 21 failed**, and **all 21 are pre-existing or
test-isolation artifacts, none from this work** — established by re-running them
on a stashed pristine tree (18 reproduce identically, the 2 ERCOT
`retirement_rule='pipeline'` failures reproduce untouched, and the 1
`consume_phase3d` failure passes in isolation). New tests added for the TTC
fail-loud guard and per-vintage SCR/EDRP resolution.

**Still open:** the ACTIVE freeze (now the sole blocker); the import-tranche
719 MW duration RMSE disclosure, still NOT re-measured; the Transco Dec-2022
Elliott hole, unfixable from the free archive; CAISO's 2018-2022 CARB block; and
NEISO's now-stale 2022 touchpoint. Raw ATC/TTC postings (~17 MB) are gitignored
per the ATC_TTC.zip precedent, but the deriver prints the exact re-fetch command,
so the derivation is reproducible from a bare checkout.

## 2026-08-15 — nyiso-135 PROMOTION: keeper → `2026-08-08-nyiso-133-cod-arm` (market-solar in-service DATE basis)

**Owner ruling, verbatim:** *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a
keeper."* The nyiso-133 session's own recommendation was **PROMOTE**, and the
standing structure-over-gates clause is **not needed** — no gated criterion
regresses.

**NO SOLVE RAN.** This is a **governance promotion** over the A/B pair nyiso-133
registered, pre-registered and adjudicated, and then held pending the owner's
call. No new mechanism was tested; exactly **one cell verdict moves**
(`vre_registry_cod_date_basis` NYISO `O` → `K`).

**What is armed.** `nyiso_solar_registry_cod_dates` — the market-solar registry
ramps each plant on its **commercial operation** date (EIA-860 `Operating
Month`) instead of the Gold Book Table III-2a *"In-Service Date"*, which is a
**registration / interconnection-service** date that **leads** the metered
commercial start. Rule 14 `[R-ACCURATE]` in its reconciled-real-data form: two
published registries disagree on one field and a **third** published series
(EIA-923 first metered output) adjudicates — it agrees with EIA-860 in **11 of
the 12 uncensored plants**, and the lead is **signed both ways** (Darby −1,
Stillwater −3 against Morris Ridge +2, High River +1, East Point +1), so it is a
basis difference and not a one-directional correction toward the residual.
Membership and nameplate stay **100 % Gold Book**; only the switch-on month
moves. **Zero free parameters** — a 15-row registry identity, each row verified
on nameplate agreement and **dropped** (keeping its Gold Book date) rather than
guessed when it fails (Albany County Solar 2 is the one unmatched unit). DOF
ledger **36 → 37**, `n_residual` **unchanged at 6**, identification `published`.

**Verdict grain — nothing regresses.** Determination **UNCHANGED** at
`CALIBRATED-WITH-CAVEATS`, all 8 criterion statuses identical, **C3c the lone
ledgered caveat at 1 of 1 and BIT-UNCHANGED at 21 / 3 / 24 h** against actual
10 / 12 / 42, so no C3c evidence moved and no new slot is spent. Re-verified
2026-08-15 with `calibration_verdict.py --run-id` on **committed artifacts only,
no solve**, per rule 22 D-5(b) — the worse-determination stop does not fire.
C3a reads +8.8 / +0.8 / −3.4 %. All seven pre-registered gates PASS: K1 exactly
**one** differing `scenario_config` field of 703; K2 zero slack/dump; K3
liveness 1.0118 / 0.8746 / 1.0000 against *ex-ante* predictions of
1.0118 / 0.8746 / 1.0000; K4 wind identical; K5 no status regression; K6 C3c
bit-unchanged; K7 C8 PASS with no forced share rising (ST_GAS-2024 24.5 →
24.4 %). Hourly grain at full size: demand-weighted ΔLMP −0.0023 / +0.0345 /
0.0000 $/MWh, max zonal |ΔLMP| 4.55 / 5.67 / 0.00, and **2025 is
bit-identical** — the construction's own prediction, since the 2025 registry is
flat and the two bases coincide. The paired control reproduces the superseded
keeper **exactly** (max |class-year delta| 0.000 GWh) on a toolchain **matching**
the keeper bundle's recorded one, so unlike nyiso-132 there is no drift excuse
available and the delta is attributable to the armed field alone.

**Reported against interest.** Solar vs the published Gold Book Net Energy goes
+20.9 / +33.2 / −0.1 % → **+22.3 / +16.5 / −0.1 %**: 2024 improves by half and
**2023 gets worse**. That was written into the prereg as **ADV-1 before the
solve** and expressly ruled out as grounds for rejection — the band
(`calibration_verdict.VRE_TOL`) is **report-only** and D-10 classes NYISO solar
`delivered_pinned` ("advisory-only, excluded from skill claims"), so no gated
criterion moves on it (rule 1 `[R-STRUCT]`). **The signature that this is a
repair and not a fit is the coherence, not the level:** the implied fleet CF the
published energy demands goes from 0.1629 / 0.1473 (adjacent years disagreeing
by 10 %) to **0.1613 / 0.1641** (agreeing to 1.7 %) — a quantity nothing in the
construction targets. Second cost, disclosed: 2023 year-end registered capacity
rises **174.4 → 194.4 MW** (Stillwater meters 745 MWh in Dec-2023), so "year-end
capacity is invariant" holds for 2024 and 2025 only.

**Refuted and not built (rule 26 `[R-DELETE]`).** nyiso-132's named successor —
*"the model has no commissioning curve"* — was measured **nationally** before any
mechanism was written: 730 single-vintage EIA-860 `OP` PV plants ≥ 5 MW (36.4 GW,
COD 2019–2022) against their own EIA-923 monthly history, two-way normalized, give
age-0/1/2-month ratios **0.723 / 0.962 / 0.995** on a 36–47-month **placebo of
1.0072**. A new utility PV plant is at **mature output from its second month**;
the entire commissioning shortfall is 0.321 month-equivalents ≈ **11 %** of the
effect it was named to explain. No commissioning curve exists and none is built.

**What this promotion does NOT do.** It does not close, narrow or re-open C3c —
the tail is bit-unchanged, the diagnosed owner is unchanged (100 % of the
modelled tail is Long Island inside HB14-21 with both Zone-K import paths at
their bound), and the successor remains the **chartered joint reconciliation** of
the Zone-K transfer bound and the downstate ST_GAS `min_gen` floor under rule 19
`[R-ONE-MECH]`. **Do not re-test the bare number swap** —
`nyiso_li_tsl_n11_security` is `R`, killed on gate K6 at nyiso-130. It does not
restore frontier status (**cleared 2026-08-06, stays cleared**). It does not touch
the holdout posture: `complete` (**validation ONLY**), **absent from `final`**, and
the **ACTIVE spend freeze** independently blocks every out-of-training solve, score
and registration. This promotion **grants, spends and re-arms nothing**.

**Deferred, flagged, NOT done — first item for the next session.** nyiso-133 §9
recommends collapsing the gate to **unconditional** on promotion (rule 26: a
default-off gate whose *off* position is the **less accurate** basis is a
re-armable wrong answer). nyiso-135 did **not** do it, for two stated reasons:
(a) it is an owner decision nyiso-133 explicitly flagged and did not take, because
collapsing it **re-stales the NYISO forecast lane's 11 committed hindcast
sidecars** (rule 15's separate namespace, its own governance); and (b) this
session had **no `git fetch`** — the environment carries no git credentials — so
`src/market_sim/config/scenarios.py` could not be rebased onto a `main` that had
advanced **19 merged PRs**, and editing a >300-line core file off a stale base is
precisely the rule 27 `[R-PUSH]` hazard. **The promoted keeper carries the flag
`True` in its own `run_config.json`**, so the designated keeper is correct either
way; only the DEFAULT is deferred.

**Gates run (all green, committed artifacts only).**
`calibration_verdict.py --run-id 2026-08-08-nyiso-133-cod-arm` →
`CALIBRATED-WITH-CAVEATS`; `audit_keepers.py --iso NYISO` → 0 failures /
0 warnings; `check_mechanism_matrix.py` → integrity, anchors, keeper stamps and
§5.x prose headers all OK; `build_status.py --iso NYISO` rebuilt the shard
(NYISO `CALIBRATED-WITH-CAVEATS`). Only NYISO's shard, status and matrix column
were touched (rule 25 `[R-ISO-SCOPE]`).

**Lever queue after this promotion.** (1) the chartered **JOINT Zone-K
transfer-bound + downstate ST_GAS `min_gen` reconciliation** (rule 19) — open,
needs its own owner charter **and** pre-registration before any solve; (2) the
**FLEET-CF COMPOSITION** object this promotion's own finding opens, **replacing**
the refuted commissioning-curve item — after the date repair 2023 and 2024 both
imply fleet CF **~0.162** against 2025's **0.1955**, while measured mature
per-plant CF is 0.174–0.182 for the 2021–22 small fixed-tilt NY8 units and
0.198–0.221 for the 2024 tracking plants (Morris Ridge 0.1998, High River 0.1983,
East Point 0.2207), so a single ISO-wide `RENEWABLE_AVG_CF` cannot track a fleet
whose technology mix goes 100 % fixed-tilt → 56 % large tracking across the span.

**Still open and unchanged from nyiso-134:** the ACTIVE holdout freeze (the sole
blocker on the 2022 touchpoint, which is otherwise **data-ready**); the
import-tranche 719 MW duration RMSE disclosure, **still not re-measured** — grade
it before quoting any 2022 result; and the Transco Dec-2022 Elliott hole,
unfixable from the free archive — disclose before quoting any Dec-2022 or
winter-tail number.

* Next number: **nyiso-136**.

## 2026-08-15 — nyiso-136 RULE 26 [R-DELETE]: the market-solar in-service DATE basis gate is COLLAPSED TO UNCONDITIONAL

**Owner ruling, session nyiso-136, 2026-08-15:** collapse the gate, accepting the
forecast-lane re-stale. This is the item `ASSESSMENT-nyiso135-promotion-2026-08-15.md`
§4 listed as open #2, that nyiso-133 §9 recommended, and that both nyiso-133 and
nyiso-135 explicitly declined to take without an owner decision.

**NO SOLVE RAN. NO CELL VERDICT MOVES.** `vre_registry_cod_date_basis` NYISO went
`O` → `K` on the nyiso-135 promotion, which landed earlier in this same session.
What moves here is the **DEFAULT**, not a verdict.

**What changed.** `ScenarioConfig.nyiso_solar_registry_cod_dates` is **DELETED**.
`data/renewables.py` now calls `load_market_solar_monthly(..., cod_basis=True)`
unconditionally, so every NYISO run in **both lanes** ramps each registered
market-solar plant on its EIA-860 `Operating Month` — the metered commercial
start — and the Gold Book Table III-2a `In-Service Date` (a registration /
interconnection-service date that leads it) is no longer reachable from any solve
path. The CLI flags in `run_calibration.py` / `run_calibration_full.py`, the
config plumbing, and the default-off tests go with it. The matrix row's `def` and
the loader/deriver docstrings are re-pointed; the `fc` posture is **dropped**,
because with the gate gone there is no longer a forecast posture that differs.

**Why.** Rule 26 `[R-DELETE]`, in the words of the gate's own standing in-code
note: a default-off gate whose OFF position is the **less accurate** basis is a
re-armable wrong answer. nyiso-135 promoted the armed run to keeper; leaving the
DEFAULT on the superseded basis left the wrong answer one flag away.

**Declared cost, accepted by the owner in the same ruling.** This re-stales the
NYISO **forecast** lane's **11 committed `nyiso-*` hindcast sidecars** (rule 15's
separate namespace, its own governance). They stand as PRE-EPOCH evidence until
that lane re-runs them. This is exactly the cost nyiso-133 and nyiso-135 both
flagged and refused to incur unilaterally.

**The cache hazard, found and handled — this is the load-bearing part.** The flip
is **SAME-KEY**. The field was registered in `_CACHE_KEY_OPTIONAL_FIELDS` and held
its `False` default, so it was **already dropped from the hash**; deleting it
leaves the pinned default key `603c2498bf71d21d` **byte-stable**. The first
attempt retired it into `_CACHE_KEY_RETIRED_FIELDS` — the mechanism rule 26 points
at — and that was **WRONG and was caught by measurement, not by reasoning**: that
dict *re-inserts* a name into the payload, so it moved the key to
`6f8050582a752f5a`. Retirement is for fields that entered the hash at their
default; never for a registered-optional one. Both values are recorded at the
tombstone so the next deletion does not repeat it. Because the invalidation is
invisible in the key, it is written into the cache-epoch ledger in
`src/market_sim/results/cache.py` (entry **2026-08-15**), which names exactly what
is invalidated and what is not.

**Not affected.** The designated keeper `2026-08-08-nyiso-133-cod-arm` already
solved with the flag `True` in its own `run_config.json`, so it is **already on
the post-collapse basis**; its determination is untouched at
`CALIBRATED-WITH-CAVEATS` with C3c the lone ledgered caveat, bit-unchanged at
21 / 3 / 24 h. Its paired control is pre-epoch by construction and is kept as the
A/B baseline, not as a current-basis run. Rule 25 `[R-ISO-SCOPE]`: NYISO only —
the loader returns `None` for any other ISO, and NEISO carries the identical
Tier-3 posture and is explicitly NOT covered. Frontier stays **CLEARED**
(2026-08-06), not re-asserted.

**Verification.** Two independent cross-checks confirm the collapse reproduces the
**promoted** basis rather than drifting into a new one. Armed 2024 solar energy
moves 0.670 → 0.586 TWh, a ratio of **0.8748** against the nyiso-133 A/B's
recorded K3 liveness of **0.8746**; and 0.586 against NYISO's published 0.503 TWh
is **+16.5 %**, the exact 2024 advisory figure the promotion reported against
interest. Pinned default cache key `603c2498bf71d21d` re-measured and byte-stable;
`check_cache_key_registration.py` clean (713 fields, 166 registered, all declared
defaults match HEAD); `check_mechanism_matrix.py` integrity / anchors / keeper
stamps / §5.x headers all OK, with 228 base-file line anchors mechanically
repaired by `--fix-anchors` (provably digits-only: the file is byte-identical once
line-number digits are normalized) because deleting the field shifted
`scenarios.py`; ruff and ruff-format clean. Targeted suite **1,402 passed, 4
failed**, and the **same 4 fail identically on pristine `origin/main`** — they are
the gitignored `data/clean` partition absent in a fresh checkout, none from this
work. The two tests that legitimately moved were updated with the arithmetic above
written into them, not re-baselined silently.

**Holdout posture UNCHANGED, re-confirmed in session.** The owner was asked and
ruled **HOLD the freeze**: 2022 was not solved, scored or registered. `complete`
stays validation ONLY, NYISO stays ABSENT from `final`. The two disclosures that
must be graded before any 2022 result is quoted are **still ungraded**: the
import-tranche 719 MW duration RMSE (still not re-measured) and the Transco
Dec-2022 Elliott hole (unfixable from the free archive).

**Lever queue.** (1) the chartered **JOINT Zone-K transfer-bound + downstate
ST_GAS `min_gen` reconciliation** (rule 19) — open, still needs its own owner
charter AND pre-registration. (2) the **FLEET-CF COMPOSITION** object — the
owner's chosen lever for this session, pre-registration next.

* Next number: **nyiso-137**.

## 2026-08-15 — nyiso-136 REFUTES the FLEET-CF COMPOSITION object (no solve spent)

**The owner chose lever (a)** — nyiso-133's own named successor, carried in the
lever queue by `ASSESSMENT-nyiso135-promotion-2026-08-15.md` §2. Rule 19
`[R-ONE-MECH]` requires a pre-registration before any solve; the identification a
pre-registration must rest on was measured **first**, and it **refuted the
object**. No mechanism was written, no pre-registration filed, **no LP solved**,
no run registered, keeper unchanged, **no cell verdict moved**.

**All three factual premises fail on the registry's own published data.** The CF
*levels* the object quotes all reproduce; the *technology labels* attached to
them do not.

* **P1, falsified in part — HIGH RIVER IS FIXED TILT.** 90 MW, the
  second-largest plant in the registry and ~16 % of the 2025 fleet, named by the
  object as one of the three "2024 tracking" plants. EIA-860 records
  `Fixed Tilt? = Y`, `Single-Axis Tracking?` blank, **Tilt Angle 18°** — every
  genuinely tracking plant in the fleet reads 0° or blank.
* **P2, falsified — the span is ~35 % → ~56 % tracking, not 0 % → 56 %.**
  Branscomb (COD 2021-12) and Regan (COD 2022-12), two of the units the object
  calls *"2021–22 small fixed-tilt NY8"*, are single-axis tracking. Tracking
  share of capacity-months runs **34.8 / 41.7 / 56.1 %**. The end point is right;
  the start point — the half that makes the composition swing large — is not.
* **P3, falsified — the tracking flag has no explanatory power here.** Over
  mature (age ≥ 2, the nyiso-133 threshold) non-zero months: **FIXED n=7 mean
  0.1854** (0.1639–0.2170) vs **TRACKING n=5 mean 0.1856** (0.1515–0.2091) — the
  means differ by **0.0002**. The **highest-CF plant in the fleet is fixed tilt**
  (Calverton 0.2170) and the **lowest is tracking** (Regan 0.1515). The
  capacity-weighted gap that does exist is carried entirely by Morris Ridge and
  East Point being *large and recent* — a **vintage** covariate, not a mounting
  one. What the object grouped was COD vintage, labelled with an assumed
  technology its own registry contradicts.

**The ceiling — 38 %.** Granting strictly more than the mechanism asks (every
plant carrying its **own** measured mature CF, a superset of any per-technology
weighting), the capacity-month-weighted composite runs **0.1794 / 0.1869 /
0.1923** against implied **0.1613 / 0.1641 / 0.1955**: a **+0.0129** swing
against **+0.0342**, i.e. **38 % of the named effect**, while *over*-stating 2023
and 2024 by +11 % and +14 %. The same test retired nyiso-132's commissioning
curve at ~11 %.

**A hypothesis raised and killed in the same session, recorded because it was
tested.** The composite sitting ~11 % above the Gold Book's implied CF looks like
the benchmark-basis defect chartered for hydro at §5.5 item 11b. **False:** over
the same crosswalked plants the two published series **agree** where both are
complete — EIA-923 / Gold Book **1.001×** (2023) and **1.028×** (2024). 2025's
EIA-923 is a **preliminary vintage** (4 of 12 online plants filed) and is
**excluded**, not averaged in.

**What the same measurement found instead — named, sized, NOT built.** Against
each plant's own mature CF the shortfall is **10.2 %** (2023) and **5.5 %**
(2024), and its largest single identified component is **full-month zero output
at a mature plant**: **43 %** of 2023 (Regan, five consecutive months Mar–Jul)
and **30 %** of 2024 (Grissom, three consecutive months Mar–May). **The model
cannot represent that at all** — `derive_cf_profile` normalizes the EIA-930 shape
to a flat annual mean CF and applies it to the **full registered nameplate every
hour**, with no availability derate anywhere on the VRE path, while the thermal
fleet carries `THERMAL_AVAILABILITY` / WEFOR and a measured CAMPD outage layer.

**And the finding argues against spending a solve on it**, which is why it is
named rather than built: ~11 GWh on a 230 GWh fleet, on a band
`calibration_verdict.VRE_TOL` marks **report-only** for a class D-10 marks
`delivered_pinned`; deriving a solar EFOR from two observed plant-outages would
be fitting a parameter to two events (rule 21); and it leaves most of both
residuals unexplained anyway.

**Not done and not touched.** `RENEWABLE_AVG_CF["NYISO"]["solar"]` stays at
**0.1955** — it is the measured **mature-fleet** CF and nothing here gives an
admissible basis to move it. **No matrix row is added:** rule 28 stamps
mechanisms that exist, exactly as nyiso-133 added no row for the refuted
commissioning curve. Keeper unchanged at `2026-08-08-nyiso-133-cod-arm`,
`CALIBRATED-WITH-CAVEATS`, C3c the lone ledgered caveat at 21 / 3 / 24 h.
Frontier stays **CLEARED** (2026-08-06) and is **not** re-asserted — the queue is
not cleared, and this session **opened** an object while retiring another.
Holdout posture unchanged; the ACTIVE freeze was re-confirmed **HELD** by the
owner in this session and 2022 was not solved, scored or registered.

**Evidence.** `results/calibration/FINDING-nyiso136-fleet-cf-composition-refuted-2026-08-15.md`,
probe `scripts/probes/_nyiso136_fleet_cf_composition.py`, record
`results/calibration/_nyiso136_fleet_cf_composition.json`.

**Lever queue.** (1) the chartered **JOINT Zone-K transfer-bound + downstate
ST_GAS `min_gen` reconciliation** (rule 19) — still open, still needs its own
owner charter **and** pre-registration; do **not** re-test the bare number swap
(`nyiso_li_tsl_n11_security` is `R`, killed on K6 at nyiso-130). (2) **VRE
availability / forced-outage representation** — newly named and sized here, and
flagged low-value on a report-only band. (3) **FLEET-CF COMPOSITION is RETIRED**,
joining the commissioning curve.

* Next number: **nyiso-137**.

## 2026-08-15 — nyiso-136 DISCLOSURE carried forward: NYISO-RTD-CLOCK, and it now attaches to the CURRENT keeper

**No code changed, no product re-derived, no year re-scored, no cell verdict
moved.** This entry exists for two reasons. First, the disclosure was recorded in
a handoff **addendum** and **nowhere in this lane's governance** — not in
`keepers/NYISO.json`, not in `calibration-complete.json`, not in this log, not in
the matrix shard — so a session reading the NYISO lane would not have seen it.
Second, **this session superseded the only keeper it named.**

**The defect** (adjudicated 2026-08-15, session nyiso-rtd-clock; ADDENDUM to
`docs/handoffs/d32-f6fix-2026-08-13.md` §§A.1–A.7). NYISO's P-24A `Time Stamp` is
interval-**ENDING**. `scripts/data/derive_actual_lmp.py::_nyiso_wide` bins it as
interval-**BEGINNING** (plain `.floor("h")`), and it is the producer of the
committed `data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`. The
clean-side `curate_lmp.parse_nyiso_zip` is already **correct**.

It was adjudicated not from prose — NYISO publishes no definition of the column,
and the MPUG, Manual 12, Manual 14, A536 and the MIS index were all searched and
found silent — but from **NYISO's own arithmetic**: P-4A is published as the
hourly integration of the P-24A 5-minute prices (Manual 12 p. 136, Manual 14 §4,
A536 §3.2.2), so binning P-24A under each candidate convention and comparing
against P-4A *decides* the question. Over 11 zones and 9 months spanning
2022–2025 including both DST transitions: **ENDING** max |Δ| **0.0050** with
**zero** zone-hours outside 2-decimal rounding; **BEGINNING** mean 1.1575, max
151.67, **62,598 of 64,889 zone-hours wrong**. Corroborated three independent
ways (the daily file spans 00:05…24:00; ex-post posting is incompatible with
beginning-labels; a live 2026-08-14 fetch).

**Why it lands on this lane.** The scorer
(`render_calibration_html._actual_lmp_hourly` / `_actual_rt_padded`) loads that
parquet and **prefers the `rt` column** — the actual series C3a, the
demand-weighted monthly MAE and **the C3c scarcity tail** are scored against.
Measured read-only, input side only: 2022 moves **97.8 %** of hours at mean |Δ|
$1.98 and max $257.21, yet annual mean RT moves **−$0.024** and the top-100-hour
mean **−$0.49**. **Almost every hour moves and the level barely does** — one
sample in twelve swaps per hour, so *level* statistics are near-invariant and what
moves is **hour-by-hour alignment**: correlation-sensitive metrics and **any
per-hour tail count**.

**What is and is not at risk — stated, not absorbed.**

* **AT RISK — the ACTUAL side of the C3c ledgered caveat** (10 / 12 / 42 h
  >$300). It is a per-hour tail count taken from this series.
* **AT RISK — the chartered JOINT Zone-K reconciliation**, this lane's remaining
  lever. It is a C3c object and its nyiso-130 kill gate **K6 is itself a per-hour
  tail count**. A future session must **not** tune it against this series without
  saying so.
* **NOT at risk — the nyiso-133 A/B's C3c result.** It is **bit-unchanged**
  between arm and control, and both arms score against the *same* actual, so the
  comparison is invariant to the binning. The promotion's claim that no C3c
  evidence moved **stands**.
* **NOT at risk** — C3a levels (−$0.024 annual mean), and the **DA** block, so
  the `spec.py` import ladder needs no re-derivation.
* **NOT at risk** — this session's fleet-CF refutation, which is entirely
  input-side (EIA-860 registry + EIA-923 metered energy) and touches no LMP
  series.

**Keeper re-pointed.** The addendum names `2026-08-08-nyiso-132-cf-arm` as the
keeper scored against the mis-binned series. **This session superseded it**, so
the disclosure now attaches to **`2026-08-08-nyiso-133-cod-arm`**, which is
scored against the same parquet and inherits it unchanged.

**Not repaired, deliberately.** The fix is one line (`(idx − 1s).floor("h")`) but
it is **owner-gated and data-blocked**: re-deriving the parquet needs the NYISO RT
source zips re-staged, and only **22 monthly zips** are on disk against a
2018–2026 parquet. **Do not re-derive on partial coverage.** The owner decision
the addendum requests is unchanged and still outstanding — correct `_nyiso_wide`,
re-derive, then re-score the NYISO keeper and re-verify its determination (rule 22
/ D-5(b)). Rule 14 `[R-ACCURATE]` points at the repair: a worse fit after it would
be a **discovered bug**, not a reason to keep a mis-binned series.

**Instrument:** `scripts/probes/nyiso_rtd_clock_adjudication.py` (read-only; it
writes no product and solves nothing). Not re-run here — it fetches P-4A months
into a scratch cache, and nothing in this session turns on re-deriving a result
already adjudicated to the last published digit.

* Next number: **nyiso-137**.

## 2026-08-16 — nyiso-137: the RTD-clock disclosure GRADED against the joint Zone-K lever — gates clean, lever unblocked, but the C3c actual count is verdict-fragile and the adjudication under-stated it

Assigned lever (a), the chartered JOINT Zone-K reconciliation, with the handoff's
instruction to *"ask for the charter first; and grade the RTD-clock disclosure
against its K6 gate up front."* The grading is the session. **No LP solved, no
year scored, no run registered, no keeper moved, no cell verdict moved, no
pre-registration filed, no product re-derived** — the nyiso-136 shape,
identification before mechanism. Rule 22: 2023–2025 only; the twelve 2022 source
zips are on disk and were deliberately **not read** (spend freeze ACTIVE).

**The handoff's premise was false.** It states twice that the lever's *"K6 gate
is itself a per-hour tail count"*. K6 is the **forcing** gate — D-2 forced share
/ forced TWh plus a C8 flip — and what fired it at nyiso-130 was
`reliability_floor × ST_GAS` rising 2.784 → 3.002 / 2.797 → 3.216 / 2.371 →
2.598 TWh. The per-hour tail count is C3c, a *criterion*, and nyiso-130 §8
already fixed that the promote test runs *"whatever C3c does"*.

**All six kill gates are model-side and invariant.** K1 config diff, K2
slack/dump, K3 in-window `limit_up`, K4 other links' bounds, K5
control-vs-treatment external-link **energy**, K6 forced share + C8 — all read
from the arms' own bundles. K5 was the only candidate worth checking and is
clean twice over: `_nyiso130_ab_gates.k5_seam` sums link MW from each arm's
network parquet, and the import *pricing* path
(`model/interchange/nyiso.py:105-108`) reads only the PJM/NEISO neighbour series.
**So the disclosure does not block lever (a).**

**The promote criteria that do read the series are safe by three orders of
magnitude.** On 6,018 whole staged in-training hours, 94.0 % move but the pooled
mean shifts −0.0353 % (29.1725 → 29.1622) and the worst single month −0.5063 %,
against a C3a band of ±10 % with a nearest margin of 1.2 pp and a C3b monthly
NRMSE ceiling of 0.20.

**What *is* at risk is worse than ADDENDUM §A.6 said.** Its conclusion that *"the
C3c tail region moves by cents"* is **refuted**: the delta is heteroskedastic in
price — mean |Δ| $0.4237 over all hours, $17.22 above $100, $30.99 above $200 and
**$35.55 above $300**, an **84×** ratio. The addendum missed it because every
statistic it quoted is a **signed** mean (−$0.024 annual, −$0.49 top-100), and
signed means cancel. Zero staged hours crossed $300, but all three staged tail
hours started far from it ($450.22→$377.79, $593.16→$598.10, $392.26→$362.98).

**C3c verdict reachability — the durable result.** Staged months hold only 1 of
10, 3 of 12 and 2 of 42 actual tail hours, so a recount is impossible on present
coverage and was not attempted. A ceiling was measured instead: the population
within ±$72.43 (the tail region's own max) of the threshold bounds the count
movement at **[5, 21] / [10, 21] / [34, 82]** against committed 10 / 12 / 42.
Against the keeper's model 21 / 3 / 24, **2023 flips FAIL → PASS at actual 11 h —
one hour** — and **2025 flips PASS → FAIL at actual 49 h — seven**; 2024 is
stable. The 2023 edge is doubly sharp: actual 10 sits exactly on
`TAIL_SMALL_COUNT`, so one hour down also switches the scoring rule from ratio to
absolute difference. **Direction is not claimed** — the staged tail moves net
downward, which would preserve both verdicts, but n = 3 is not a rate (rule 21).

**Disposition.** Charter **requested, not granted**, at
`docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md`, with three decisions
for the owner (grant/refuse; the C3c reporting condition; whether the clock
repair goes first) and a session recommendation of *charter now, repair later,
with the condition attached*. The condition: an **arm-vs-control** C3c delta is
invariant and may be relied on; an **absolute** C3c band verdict may not. The
RTD-clock item on the 2022 touchpoint is now **graded for 2023-2025 and still
ungraded for 2022** — the year it was quantified on; the other two disclosures
(import-tranche 719 MW duration RMSE, Transco Dec-2022 Elliott hole) are
untouched. Keeper unchanged at `2026-08-08-nyiso-133-cod-arm`,
CALIBRATED-WITH-CAVEATS, C3c the lone ledgered caveat 1 of 1. Frontier stays
CLEARED and is not re-asserted.

Evidence:
`results/calibration/FINDING-nyiso137-rtd-clock-graded-against-zone-k-gates-2026-08-16.md`,
`docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md`, probe
`scripts/probes/_nyiso137_rtd_clock_c3c_grading.py`, record
`results/calibration/_nyiso137_rtd_clock_c3c_grading.json`. Next number:
**nyiso-138**.

**Inherited defect found while gating, flagged not fixed — the designated keeper
is UNREPLAYABLE at HEAD.** `test_replay_keeper_strict.py::...::
test_all_keeper_metas_build` fails with `meta.json keys not bound to
solve_and_persist kwargs: ['nyiso_solar_registry_cod_dates']`. **Confirmed
pre-existing on a stashed pristine tree**, so not caused by this session (whose
diff is documentation plus one standalone read-only probe). Cause: nyiso-136
deleted the `ScenarioConfig` field under rule 26, but the keeper was solved with
the flag armed so its committed `meta.json` still carries the key, and
`replay_keeper.build_kwargs` is strict by design (miso-50..53 regression class).
This was **not** among nyiso-136's declared costs. Recommended fix — an owner
call, raised as **D4** on the decision card — is to add the name to
`replay_keeper._IGNORE`: that table governs recipe reconstruction rather than
hashing and its semantics ("not a solve kwarg") are now true, since the collapse
made the flag's behaviour unconditional in both lanes. It is deliberately NOT the
`_CACHE_KEY_RETIRED_FIELDS` case nyiso-136 warned about, where retirement would
re-insert the name and move the pinned key.

## 2026-08-16 — nyiso-139: owner answers the charter card (D1 GRANT / D2 adopt / D3 **(b)**), and the ordered FIRST step lands — the NYISO RTD interval-convention repair, on a fully re-staged archive. Keeper determination UNCHANGED.

**Owner rulings** (`AskUserQuestion`, on
`docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md`): **D1 GRANTED**
("write, prereg, solve"); **D2 ADOPTED as requested**; **D3 = option (b)**,
*"re-stage the NYISO RT archive, repair first, then charter"* — **not** the
session-recommended (a). D4 stays withdrawn (nyiso-138). The card is now fully
answered and needs no further ruling.

D3(b) makes the clock repair the ordered first step, so that is what this
session did. **No LP solved, no year scored against model output, no run
registered, and the chartered lever is NOT yet written.**

**The blocker the card called (b)'s cost is GONE.** The card priced (b) as
"blocked on staging ~8 years of monthly zips". `mis.nyiso.com` is reachable, so
a new idempotent fetcher `scripts/data/fetch_nyiso_zonal_lmp.py` re-staged the
archive: **DA 0 → 102/102 months** (the outer container
`NYISO_zonal_hourly.zip` did not exist at all on a fresh clone — gitignored as
regenerable — so the DA half had no source) and **RT 21 → 102/102**, zero
failures. The 21 already-committed RT zips were skipped, not rewritten, so their
bytes (including the twelve 2022 rule-22 intake months) are untouched. Coverage
is total across the parquet's committed span, so the re-derivation was option
**(b)** and never the forbidden **(c)**. The 2026 window was deliberately NOT
extended past June even though `mis.nyiso.com` now serves 2026-07: the change
moves the **clock**, not the **span**.

**The repair.** `derive_actual_lmp._nyiso_wide` binned the 5-minute RT (P-24A)
stamps as interval-BEGINNING; they are interval-**ENDING**. One RT-scoped line
(`shift = 0 if kind == "da" else 1s`, subtracted in UTC so
`_localize_ordered`'s fall-back disambiguation is untouched). Adjudicated, not
assumed, against NYISO's OWN published time-weighted hourly product P-4A
(Manual 12 p. 136 / Manual 14 §4 state P-4A is built from these 5-minute
prices): **ENDING agrees within the $0.005 rounding bound on all 14,905 strict
zone-hours; BEGINNING is wrong on 14,174 of 14,828, by up to $50.01.**
Independently corroborated this session by the archive's own shape — a monthly
RT zip runs `00:05` day 1 → `00:00` day 1 of the next month, i.e. exactly the
intervals *ending* in that month. Rule 14 `[R-ACCURATE]`.

**Measured effect.** ~95 % of hours move, the level does not: annual mean RT
shifts −0.005 / −0.012 / −0.015 % in 2023/2024/2025 (full-population
reproduction of nyiso-137 §3's −0.0353 % pooled estimate), against C3a's
nearest band margin of 1.2 pp. **The `da` column changed in ZERO hours in every
one of the nine years**, which verifies rather than assumes disclosure §A.6
item 3 — the DA block, the `spec.py` import ladder derived from it, and the
DA-only `nyiso_proxy_lmp_hourly_NEISO.parquet` are all untouched (rule 25).

**C3c denominator.** `actual_tail.json` RT tail 2023 **10 → 10**, 2024
**12 → 13**, 2025 **42 → 42** (2022 97 → 101, input-side only; 2020/2021
unchanged). Only two values in the whole file changed and **both are NYISO** —
every other ISO's block is byte-identical. All three land inside the reachable
intervals nyiso-137 §5 computed ex ante, and **neither verdict-flip edge it
flagged fired** (2023 did not reach the 11 h that would have vacated its
caveat; 2025 did not reach the 49 h that would have broken its PASS).
nyiso-137 §4's correction is now demonstrated on the product: "the C3c tail
region moves by cents" was false — the tail moved enough to add an hour to 2024.

**Keeper: UNCHANGED.** `calibration_verdict --run-id
2026-08-08-nyiso-133-cod-arm` (committed artifacts, no solve) still reads
**CALIBRATED-WITH-CAVEATS**, C1/C2/C3a/C3b/C4/C6/C8 PASS, C3c the lone ledgered
caveat (budget 1 of 1). The only movement in the entire verdict is 2024's C3c
magnitude, `0.25× (12 h)` → `0.23× (13 h)`. Re-verified into
`calibration-complete.json` under rule 22 D-5(b) (label unchanged, so the
worse-determination stop does not fire); downstream artifacts refreshed for
self-consistency (`actual_lmp.json` `rt_lw*` via `--lw-retrofit` — `da_lw*`
unchanged; the three NYISO `bench/` parts; `status/NYISO.js`; `shared.js` NOT
touched).

**Holdout.** The freeze is ACTIVE and untouched; it lists `"data intake (no-LP,
rule 22 channel 1)"` under `not_frozen`, which is exactly what this was. Rule
22 as amended 2026-08-06 requires a measured input be applied consistently to
every year, which is why 2018-2022 and 2026 were repaired too — leaving them on
a clock now known wrong, while 2023-2025 use the right one, is the
inconsistency that amendment forbids. No out-of-training year was solved,
scored against model output, or registered.

**Discharged:** disclosure `docs/handoffs/d32-f6fix-2026-08-13.md` §A.6 items
1-3 in full; D2's conditionality **prospectively** (the C3c denominator is now
measured on the adjudicated-correct clock, so absolute band membership is
reliable for work that follows the repair — which is precisely what D3(b)
bought); and the third 2022-touchpoint disclosure. **Still open:** the two
other touchpoint disclosures (import-tranche 719 MW duration RMSE, Transco
Dec-2022 Elliott hole) remain ungraded; the `iso-model-unification-plan.md` §3
caveat is now satisfiable but is flagged, not edited, as another lane's doc;
and **the chartered joint Zone-K lever (D1) is still to be written** — D3(b)
put the repair first.

Evidence:
`results/calibration/FINDING-nyiso139-rtd-clock-repair-landed-2026-08-16.md`.

## 2026-08-16 — nyiso-139b: the chartered Zone-K joint lever is RE-SCOPED before writing — the floor limb the card pairs with the transfer bound is ALREADY DISABLED on the keeper, and K6 cannot adjudicate an import-relief lever

Follow-on to the same session, after the D3(b) clock repair merged (main
`f8c93afe7`). D1 is GRANTED, so the next step is "write, prereg, solve" — this
is the identification that must precede the writing, and it changes the arm.
**No solve spent, no mechanism written, no `ScenarioConfig` field added.**

**(a) The card's natural arm is a nullity on the floor side.** The keeper
carries `iso_configs.NYISO_PEAK_WINDOW_FLOORS_OFF` in full, so
`Long_Island:ST_GAS:tmax:LI_ST_ev` — the HB14-21 evening ramp family, the only
ST_GAS limb whose window coincides with the transfer bound's own HB14-21
application window — is **already disabled**. It was traded away deliberately:
the `nyiso_gas_commitment_bridge` (armed on the keeper) is its owner-directed
replacement (2026-07-27). An arm that disables it changes nothing.

**(b) What actually forces is a 24-hour base.** Of Long_Island × ST_GAS's three
limbs in `reliability_floor_coeffs_NYISO.csv`, exactly one is live: threshold
**−50 °C** (never not met ⇒ binds all 8,760 h) at **floor_pct 0.262**, basis
"persistent 24h base: base_24h (when-available cool-day CF p25)", rule-23
re-derived 2026-07-26 on the guard-corrected outage extract. The keeper's own
D-4 rows agree — `reliability_floor × ST_GAS` declares window **h0-23**, 2.7891
/ 2.8025 / 2.3869 TWh, off-window share 0.0 (D-2 class shares 20.5 / 22.1 /
15.6 %; C8's 30 % cap not approached, C8 PASSes).

**(c) So the two live representations are not one phenomenon.** They differ in
window (HB14-21 vs all-24 h), object (interface transfer capability vs
unit-level availability minimum), driver (NYISO's published N-1-1 TSL vs
measured CAMPD cool-day p25 CF) and meaning (contingency import capability vs
cable-islanded must-run). The pair that *would* have been one was already
separated, in the other direction, by the 2026-07-27 directive.

**(d) Why K6 fired at nyiso-130, then.** K6 reads "any D-2 mechanism's forced
share RISES", and *forced* = energy at a binding floor. Relieving a transmission
bound displaces the in-zone fleet out of merit, so a unit that sat in-merit
ABOVE its floor comes to sit out-of-merit AT it: the floor binds in more hours
and forced TWh rises **even when the class generates the same or less**. That is
a mechanical property of the forced-share definition under any import relief.
nyiso-130's K6 firing is therefore ambiguous between a genuine double
representation and a scoring artifact — and since the only limb that could have
carried the former is already off, the artifact is the better-supported reading.
**This is NOT a licence to disarm K6**: rule 17 `[R-FLOOR-WINDOW]` still demands
that an always-on 26.2 % downstate-steam floor justify its window. It means K6
cannot adjudicate THIS lever as written, so re-running the bare swap to watch it
fire again would learn nothing.

**Disposition — do not write the arm yet.** Two owner-level questions first:
(1) is the always-on LI ST_GAS 26.2 % base the right representation, i.e. should
a floor whose stated basis is a **cool-day** p25 CF be re-scoped to the hours its
own driver evidence supports (a rule-23 *source-data* question, never a tuning
one)? and (2) **what replaces K6 for an import-relief lever** — a gate firing on
forced *share* is structurally biased against any lever that relieves a
constraint; a defensible successor measures forced TWh at constant class energy,
or against the counterfactual merit order rather than the control's. Only then is
the joint arm writable, and it is likely NOT "940 MW + disable a floor limb" but
"940 MW + a re-scoped 24-hour base" with its own identification. Writing the
card's literal arm today buys a floor-side no-op plus an uninformative K6 firing.

Unchanged: keeper `2026-08-08-nyiso-133-cod-arm` **CALIBRATED-WITH-CAVEATS**,
C3c the lone ledgered caveat against the corrected actual tail **10 / 13 / 42**;
`complete` (validation only), ABSENT from `final`; frontier CLEARED 2026-08-06;
holdout spend freeze ACTIVE; NYISO cross-ISO queue CLOSED since nyiso-122.
Evidence:
`results/calibration/FINDING-nyiso139b-zone-k-joint-lever-rescoped-2026-08-16.md`.
Next number: **nyiso-140**.

## nyiso-140 — the LI ST_GAS floor has the right WINDOW and the wrong MEMBERSHIP (2026-08-16)

Settled the two owner questions nyiso-139b left blocking the chartered Zone-K
lever, then wrote, pre-registered and A/B-solved the resulting mechanism.

**Q1 — CLOSED, and the window survives.** The always-on `Long_Island × ST_GAS`
limb (`tmax` −50 °C ⇒ all 8,760 h, `floor_pct` 0.262, `pro_rata`) is
**identified** on a fleet-aggregate when-available CF but **applied** per unit.
Measured from the floor's own source (CAMPD conduct + the guard-corrected outage
extract; no residual, no metrics file, no solve): Barrett (2511) and Northport
(2516) genuinely run a persistent 24-hour baseline — cool-day median CF
0.254 / 0.313 at h00-05, zero in only 4–5 % of cool hours — so **the 24-hour
window is correct and was NOT narrowed**. Port Jefferson (2517, 385 MW) is
economically laid up: median CF **exactly 0.000 in every hour block of every
year**, 73 % of cool hours at zero, yet ~100 % model availability because the
2026-07-26 guard fix (`6a8f285`) correctly un-booked lay-up from the outage
extract. It absorbed **72.6 % of everything the limb forced** (1.87 of 2.57 TWh
over three years) on **7.2 %** of the fleet's output — rule 17
`[R-FLOOR-WINDOW]` verbatim. Its conduct is U-shaped in temperature
(P(on)=0.93 at tmax ≥ 30 °C, 0.73 below 0 °C, 0.24 in mild weather): the ramp
limbs' driver, not a persistent base. Correcting both **cancelling** basis errors
(a daily-mean statistic applied hourly; a fleet aggregate applied per unit) gives
0.2666 against the frozen 0.2620, so `floor_pct` is **unchanged** and the fix
adds **zero free parameters** (rule 21 `[R-DOF]`).

**Why the diagnostics were blind:** D-4 is **tautological** for an `h0-23` floor
(`offwindow_share = 0.0` by construction — it cannot fail), and D-2 is
class-aggregate, so one plant carrying 73 % of a class's forcing is invisible and
C8 still PASSes.

**Q2 — K6′ adopted (owner, 2026-08-16).** Bare K6 ("any D-2 mechanism's forced
share rises") is structurally biased against any lever that relieves a
constraint. K6′ makes a share rise **escalate to provenance + shape** (D-4 window
+ D-1 `profile_r`/`cv_ratio`) rather than kill, mirroring rule 20's own amended
C8 logic; the energy-normalised `Δforced` is reported, not gated. Adopted **with
the D-4 per-unit conduct rider** — not yet implemented, so K6′'s provenance leg
is currently unproven rather than passed.

**A/B (rule 15, both registered; rule 16, 2023 2024 2025 in one bundle each):**
control `2026-08-16-nyiso-140-control`, arm
`2026-08-16-nyiso-140-layup-exclusion`. **All six pre-registered kill gates
clean.** K3 liveness: the floor shed **0.602 / 0.560 / 0.625 TWh**, against the
~0.62 TWh/yr predicted from CAMPD *before any solve* — the identification sized
the object correctly. Both read `NOT-YET` only on `C6 UNATTESTED` (fresh probe
bundles carry no attestation), symmetric across the comparison.

**The arm does not improve the fit, exactly as pre-registered.** ST_GAS error
+2.679 → +2.263 (2023), −0.595 → −0.916 (2024), −3.379 → −3.737 (2025); summed
|error| 6.653 → 6.916 TWh; mean LMP firms +0.21 / +0.18 / +0.40 $/MWh. Registered
on rule 1 `[R-STRUCT]`. Under rule 14 `[R-ACCURATE]` the degradation is a
**discovered bug** — the manufactured 1.87 TWh was masking a real downstate
under-production (2025 ST_GAS was already −21 % before the fix) — and the
successor is that root cause, **never re-flooring the laid-up plant**.

**First application of K6′, and it earned its keep:** the surviving
`nyiso_gas_commitment_bridge` share ROSE (+0.0045 / +0.0118 / +0.0051) while
doing strictly less work; bare K6 would have killed the arm.

Also fixed a pre-existing defect found here: `--replay-bundle` could not replay
the designated NYISO keeper at HEAD, because `_RULE26_DELETED_UNCONDITIONAL`
strips a rule-26-deleted field from top-level meta keys but not from inside a
generic override dict splatted via `with_overrides(**d)` — and the keeper records
`nyiso_solar_registry_cod_dates` in `coal_prb_sigmoid_overrides`.

**PROMOTED, same session, on the owner's ruling** ("Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates regress
that may still be a keeper."). NYISO keeper
`2026-08-08-nyiso-133-cod-arm` -> **`2026-08-16-nyiso-140-layup-exclusion`**. No
new solve: the only artifact added was the arm's `calibration_attestation.json`,
which moved C6 UNATTESTED -> PASS and the determination NOT-YET ->
**`CALIBRATED-WITH-CAVEATS`** (C3c the lone ledgered caveat, criterion-for-criterion
identical to the superseded keeper). The structure-over-gates clause was not
needed for the gates themselves — none regresses — but it is what licenses the
volume degradation. Rule 22 D-5(b): `calibration-complete.json` re-keyed with the
determination re-verified from committed artifacts only; label unchanged, so the
worse-determination stop did not fire. `calibration-keeper-auditor` PASS, 0
failures, 0 warnings, no repairs. Matrix cell
`reliability_floor_plant_exclusions` NYISO **O -> K**, keeper stamp and §5.5
prose header updated (NYISO shard only). `complete` (validation
only), ABSENT from `final`; frontier CLEARED 2026-08-06; holdout spend freeze
ACTIVE and untouched (2023–2025 only). Evidence:
`results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md`,
`PREREG-nyiso140-li-st-floor-membership-2026-08-16.md`; probe
`scripts/probes/_nyiso140_li_st_floor_membership.py`.
Next number: **nyiso-141**.

## 2026-08-17 — nyiso-141: the downstate ST_GAS under-production is partly a MEASUREMENT artifact — Astoria's CEMS reports one generator twice, and in 2025 that doubled number IS the benchmark

Took up job (A) of the nyiso-141 prompt, the successor nyiso-140 §7 named.
**Identification only — no solve spent, no mechanism written, no
`ScenarioConfig` field added, no year outside 2023–2025 touched.**

Decomposing the ACTUAL ST_GAS rise (+7.299 TWh 2023→2025) by plant killed most
of the prompt's candidate list at once: the rise is broad-based across **six**
large steam plants in **three** zones (Northport +1.75, Astoria +1.13, Bowline
+1.09, Arthur Kill +1.04, Roseton +0.52, Ravenswood +0.21), so it is neither a
missing unit nor a Long Island story — not the LI import bound, not
Barrett/Northport loading. **Fuel switching refuted directly**: implied CO₂ per
MMBtu stays at ~54 (pure pipeline gas) at the plants that doubled. The model's
own trend is the tell — reality replaced a falling hydro year with **steam**
(CC_REGULAR +0.12), the model replaced it with **CC** (+4.85).

**THE OBJECT.** Astoria Generating Station (ORIS 8906, NYC) files units 30 and
50 as reheat/superheat pairs `31RH`/`32SH`, `51RH`/`52SH` — one generator each,
monitored on two flue paths. CAMPD repeats the generator's FULL `grossLoad` on
both rows while SPLITTING heat input and masses, so facility-summing
double-counts generation and halves every derived intensity. Three independent
channels, none a residual: **INTERNAL** — 51RH/52SH byte-identical in all 4,327
fired hours of 2025 (max |diff| exactly 0.000, corr 1.000000), and the control
group proves identity-of-output alone is not the signature (Gowanus / Narrows /
Holtsville / Barrett banks also hit 95–100 % identical hours but each carries its
OWN full heat input); **PHYSICAL** — 5,172–5,512 Btu/kWh counted alone is
impossible for a fired boiler, 10,436–10,764 counted once, matching peers;
**EXTERNAL** — EIA-923 net / CAMPD gross = 0.472 / 0.471 against a 0.88–0.96 peer
band, landing at 0.935 / 0.937 once the duplicate is dropped.

**A guard had already caught it and papered over it**: 0.472 is outside
`_PARASITIC_MIN`..`_PARASITIC_MAX`, so `compute_parasitic_factors` flagged the
plant implausible and substituted a class default — a fallback built for a
*missing* measurement, applied to a *wrong* one. Worth generalising from.

**BLAST RADIUS.** (a) the unit-level CEMS emission rates that feed dispatch
(279–322 kg CO₂/MWh against a 520–575 peer band — ~$6/MWh too cheap under RGGI);
(b) the parasitic reconciliation; (c) **the benchmark itself** in any year
EIA-923 has not published the plant — `_backfill_eia923_with_campd` fired for
Astoria in **2025 only** (`e_ann == c_ann == 2.6722`, the backfill signature)
and put 2.672 TWh of ST_GAS actuals on the books where the corrected series
gives 1.359. 2023/2024 used metered EIA-923 and were correct all along.
Cleared as unaffected: heat rates (eGRID-sourced), `retiree_availability_caps`,
and the `nyiso_gas_commitment_bridge` `min_load_frac`s (a p5/p99.5 **ratio**,
scale-invariant).

**THE FIX** — `campd.CAMPD_STACK_DUPLICATE_UNITS`, **zero new DOF** (rule 21), a
row-identity correction of exactly the kind `CAMPD_UNIT_PLANT_REMAP` already
carries for CAISO's El Segundo: drop the duplicate's `grossLoad` at plant grain,
additionally re-label it onto its primary at unit grain, and generalise the
loader's split-plant substitution to `_FACILITIES_NEEDING_UNIT_ROWS` because NY's
preferred facility-level extract has the double-count baked in with no unit
identity. Verified at the seam (gross 780,293 / 929,474 / 1,359,022 exactly as
hand-computed; intensities to 10,678–11,176 Btu/kWh and 578–625 kg CO₂/MWh).
Regression tests `tests/curation/test_campd.py::TestStackDuplicateCorrection`.

**SCOPE, STATED AGAINST MY OWN RESULT.** This accounts for ≈35 % of the 2025
under-production and **none** of 2023 or 2024. The remaining ≈ −2.4 TWh in 2025,
the +2.26 TWh 2023 over-production, and the CC-for-steam substitution are **all
still open** and remain the successor object. Governance consequence worth
flagging: because 2025's benchmark falls, **every NYISO run ever scored on 2025
was scored against an inflated ST_GAS target**, keeper included.

Keeper `2026-08-16-nyiso-140-layup-exclusion` UNTOUCHED and still designated.
`complete` (validation only), ABSENT from `final`, frontier CLEARED, holdout
spend freeze ACTIVE and untouched. Rule 25: the scan covered state **NY only**
and the table carries **one** facility; whether another ISO's fleet contains a
stack pair is that lane's measurement and is deliberately not adjudicated.
Evidence: `results/calibration/FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md`,
`PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md`; probe
`scripts/probes/_nyiso141_astoria_stack_duplication.py`.
Next number: **nyiso-142**.

## 2026-08-17 — nyiso-142: Astoria A/B executed (arm CALIBRATED-WITH-CAVEATS, all 6 gates clean, P7 refuted); `final` NOT READY; the ST_GAS successor localised to Zone J

Three jobs, one solve pair. Keeper `2026-08-16-nyiso-140-layup-exclusion`
UNCHANGED; `complete` held, ABSENT from `final`, frontier CLEARED, holdout spend
freeze ACTIVE and untouched. No year outside 2023-2025 solved, scored or
registered.

**JOB 1 — the pre-registered A/B, executed as written.** Registered
`2026-08-17-nyiso-142-control` (bundle `nyiso142_control`) and
`2026-08-17-nyiso-142-stackdup` (bundle `nyiso142_stackdup`). The blocker
cleared by the SURGICAL route: `scripts/data/repair_v2_stack_duplicate_rows.py`
folds Astoria's 18 stack-duplicate rows onto their primaries across 2018-2026
with every other row asserted byte-frozen — the default derive path is a REPLACE
and would have destroyed the 2018 rows (no longer buildable) and the 2022/2026
holdout-intake rows (unrepeatable). Validated MATCH against a freshly curated
`emissions-unit-annual` on every field for all six rebuildable years.
`chp-btm-share` is byte-identical across the correction in every ISO, so the
clean-tree channel is empty and the pair differs by exactly the source table and
those 18 rows.

**ALL SIX GATES CLEAN.** K1' as pre-registered: **718/718** `scenario_config`
fields identical, sorted-config sha256 identical, artifact diff **17 CSV lines
all keyed `NYISO,8906`**. K2 slack/dump 0.0 in all six run-years. K3 benchmark
2.6722 -> 1.3590 exactly. K4 **zero** other plants move. K5 identical criterion
statuses. K6' D-1/D-2/D-4 pass both arms with **no D-2 forced share moving at
all**. The arm re-scores **CALIBRATED-WITH-CAVEATS**, C3c the lone ledgered
caveat, criterion for criterion identical to the incumbent; C3c is bit-unchanged
at 21 / 3 / 24 h. The control's NOT-YET is C6 UNATTESTED (probe convention,
nyiso-140), NOT a model difference.

**P1-P6 CONFIRMED; the honest headline confirmed** — 2025's movement is mostly
the TARGET moving (benchmark -1.204 TWh) not the model improving (-0.213).
ST_GAS error 2023 +2.263 -> +2.178, 2024 -0.916 -> **-1.062 (WORSE**, the
pre-registered adverse case landing on a year whose target was already right),
2025 -3.737 -> -2.746; summed |error| 6.916 -> 5.986 TWh, which is a consequence
and not the argument (rule 1). LMP +0.06/+0.10/+0.21 $/MWh.

**P7 REFUTED, in the opposite direction.** It predicted NYISO CO2 metrics would
RISE; the 2025 benchmark eGRID total FELL 29.167 -> 28.335 Mt. The reasoning
error: the doubling was in GENERATION only — heat and masses always summed
correctly — so the class CO2 mass was never understated. C5a is reported-only
and gates nothing, but the prereg committed to disclosing this.

**NOT pre-registered, disclosed:** the 2025 correction moves SIX class
benchmarks. As ST_GAS falls 1.204 the others rise by the same total
(CC_REGULAR +0.787, CC_CHP +0.281, CT_PEAKER +0.066, CT_CHP +0.056, ST_CHP
+0.015) via the ISO-total reconciliation, flattering CC_REGULAR 2025 from +2.877
to +2.229. **Every NYISO run ever scored on 2025 was scored against an inflated
ST_GAS target**, so post-correction 2025 figures are not comparable to committed
pre-correction ones. 2023/2024 bench bytes change (`c_ann` 1.546 -> 0.780,
1.850 -> 0.930) while the SCORED target does not — P2 confirmed on substance.
Registering the control alone changed no bench file at all.

**JOB 2 — `final` readiness: NOT READY, on both locked-test years.** (1) Neither
builds on the frozen config: the armed `nyiso_dynamic_reserve_requirements` has
no 2019/2026 series and its loader RAISES rather than falling back; H1-2026 also
has no EIA-930 rows, so `load_demand` cannot build the LP's demand array at all
— it is unsolvable, not merely unscoreable. (2) 2019's fleet is not
representable: Indian Point 2/3 (~2,060 MW downstate, **17.4 TWh in 2019, 11 %
of NYISO load**) are absent from every `eia860_generator*.parquet` while the
fleet reads the 2025-operable snapshot; `constants.py` already says so. (3) 2019
cannot exercise C3c, the sole caveat — exactly **ONE** actual RT hour > $300.
(4) The instrument just changed and the keeper has not been re-scored on it.
Input audit: **0 blocked of 18 on the 2023 control, 9 on 2019, 10 on H1-2026.**
The asymmetry worth carrying forward: the year that could discriminate
(H1-2026, 85 tail hours in 4,343) cannot be solved, and the year that could be
solved cannot discriminate. NYISO's locked test is UNGRANTED and the record
already says so correctly at HEAD — unlike the NEISO case, no correction is
proposed. Assessment: `ASSESSMENT-nyiso142-final-readiness-2026-08-17.md`.

**JOB 3 — the successor is localised to Zone J, and three readings are REFUTED,
two of them this session's own.** The substitution is not ISO-wide: NYC is the
ONLY zone whose CC_REGULAR falls (-0.959 TWh) and it carries the largest ST_GAS
rise (+1.84 net of the double-count). Cause on the CC side is measured — the
three in-city CCs book **+536 unit-outage-days** in 2025 against 2023 and
Astoria Energy's metered gross falls 8.29 -> 6.33 TWh. Refuted: (a) plumbing —
the outages DO reach the LP (Astoria Energy availability 0.868 -> 0.552); (c)
the Ravenswood `_FLEET_GROUP_OVERRIDE` over-derating in-city steam with CC/CT
rows — contamination is 4.5 of 256.7 equivalent full-outage days, under 2 %; (b)
the transfer bound — `nyiso_nyc_lcr_tsl` is armed and working (binding 29/29,
215/237, 138/138 in-window) but `Lower_Hudson>NYC` binds in only 0.3/2.7/1.6 %
of hours and sits far below its cap. What survives is a COMMITMENT question:
in-city ST_GAS FALLS 1.33 TWh in the model over the span the market's rose,
while Lower-Hudson import rises +2.89 TWh and Ravenswood's steam bin never uses
its 4.49 TWh ceiling. Zone J clears on economics alone. Named successor:
`nyiso_incity_commitment_obligation` (matrix cell **U**) — **named, not armed,
not pre-registered, no parameter derived, no cell verdict moved.** Finding:
`FINDING-nyiso142-incity-cc-outage-substitution-2026-08-17.md`.

Matrix: only `plant_emission_rates_v2`'s NYISO cell is touched — evidence
citation added, verdict UNCHANGED at `K` (a data correction is not a lever).
Next number: **nyiso-143**.

## 2026-08-17 — NYISO IS DECLARED CALIBRATED (rubric v3.3 owner amendment; no solve, no mechanism change)

Keeper **`2026-08-16-nyiso-140-layup-exclusion` now reads `CALIBRATED`**, up from
`CALIBRATED-WITH-CAVEATS`. Nothing about the run moved: same bundle, same
committed artifacts, no solve, no mechanism change, and every criterion status
identical — 0 FAILs, C1/C2/C3a/C3b/C4/C6/C8 all PASS, C3c the same lone
**ledgered** caveat at the same magnitude (model 21/3/24 h vs RT actual 10/13/42 h
> $300; 2023 and 2024 are the caveated years at 2.10× and 0.23×, 2025 PASSes at
0.57×), grade summary scored 8 / target-grade 7 / commercial-grade 0 / ledgered 1.

What changed is the rubric: under the owner's 2026-08-17 amendment (**v3.3**) a
ledgered caveat is **reported** but no longer **downgrades** the determination.
C3c still reads `CAVEAT`, never `PASS`; the miss is still printed at full
magnitude and is now named on the determination basis of a `CALIBRATED` run. The
C3c lever queue, the open successor lane (the compressed price distribution /
`nyiso_incity_commitment_obligation`) and the holdout posture are all untouched —
NYISO keeps `complete` only, stays absent from `final`, and the **active** holdout
spend freeze still blocks every out-of-training solve.

Cross-ISO context, the amendment record and the measured 6-run effect (NEISO's
keeper flipped too, as an unavoidable consequence of a single shared scorer) are
in `docs/calibration-log/governance.md`, 2026-08-17. Matrix: NYISO's `gates` stamp
re-stamped; **no cell verdict moved** (rule 28b/28d — no mechanism was tested).
Next number: **nyiso-143**.

## 2026-08-17 — PROMOTION: keeper → `2026-08-17-nyiso-142-stackdup` (the Astoria stack-duplicate intake correction). No solve.

Owner ruling this session, verbatim: *"Is this a recommended keeper candidate? If
so plz promote. If structural integrity improves but gates regress that may still
be a keeper."* The recommendation was PROMOTE — and the structure-over-gates
clause is **not needed**, because **no gated criterion regresses**.

**NO NEW SOLVE.** The A/B was pre-registered, solved and adjudicated at nyiso-142
(control `2026-08-17-nyiso-142-control`) and held pending the owner's call. The
promotion moves the keeper pointer only.

**What is corrected — rule 14 `[R-ACCURATE]`, zero free parameters.** CAMPD/CEMS
reports **one Astoria generator twice**, and in 2025 that doubled number **was
the benchmark**. `campd.CAMPD_STACK_DUPLICATE_UNITS` is live and
`scripts/data/repair_v2_stack_duplicate_rows.py` folds the 18 stack-duplicate
`plant_emission_rates_v2` rows onto their primaries across 2018–2026 with every
other row asserted byte-frozen. The surgical route was **required**: the default
derive path is a REPLACE and would have destroyed the 2018 rows (no longer
buildable) and the 2022/2026 holdout-intake rows (unrepeatable). Rule 23
`[R-FROZEN-DERIVE]`: the trigger is CAMPD's own duplicate stack rows, never a
residual.

**It is not a lever, and no cell verdict moves (rule 28b/28d).** `718/718`
`scenario_config` fields identical, sorted-config sha256 identical — the arm
changes no model parameter. `plant_emission_rates_v2` stays `K`.

**All six pre-registered gates clean.** K1′ artifact diff 17 CSV lines **all**
keyed `NYISO,8906`; K2 slack/dump 0.0 in all six run-years; K3 benchmark
2.6722 → 1.3590 exactly; K4 **zero** other plants move; K5 identical criterion
statuses; K6′ D-1/D-2/D-4 pass both arms with **no D-2 forced share moving at
all**. `chp-btm-share` byte-identical in **every** ISO (rule 25 `[R-ISO-SCOPE]`).

**Determination `CALIBRATED`**, re-verified from committed artifacts only (rule 22
D-5(b), no solve), criterion for criterion identical to the superseded keeper —
0 FAILs, C3c the lone ledgered caveat **bit-unchanged at 21 / 3 / 24 h**, grade
scored 8 / target 7 / commercial 0 / ledgered 1. D-5(b)'s worse-determination
stop does not fire.

**DO-NOT-MISREAD, carried from the prereg.** 2025's movement is **mostly the
target moving** (benchmark −1.204 TWh) not the model improving (−0.213); 2024
ST_GAS gets **worse** (−0.916 → −1.062), the pre-registered adverse case landing
on a year whose target was already right. Summed |error| 6.916 → 5.986 TWh is a
*consequence*, not the argument (rule 1 `[R-STRUCT]`). **The real reason the
promotion matters:** the superseded keeper's solve inputs embedded the artifact
while the benchmark has since been corrected — the promoted run is the internally
consistent pair. And the standing warning stands: the 2025 correction moves **six**
class benchmarks via the ISO-total reconciliation, so **every NYISO run ever
scored on 2025 was scored against an inflated ST_GAS target** and post-correction
2025 figures are not comparable to committed pre-correction ones.

**Successor unchanged:** `nyiso_incity_commitment_obligation` (cell `U`) — named,
not armed, no parameter derived. **Frontier still CLEARED**; `complete` held,
**absent from `final`** (nyiso-142 found it NOT READY on both locked-test years on
grounds no further testing fixes); holdout spend freeze ACTIVE and untouched — no
year outside 2023–2025 solved, scored or registered.

Gates: `audit_keepers.py --check` **0 failures / 0 warnings** · `build_status.py
--iso NYISO` → `NYISO:CALIBRATED` · `check_mechanism_matrix.py` integrity +
anchors + keeper stamps + §5.x prose OK. Next number: **nyiso-143**.

---

## nyiso-144 (2026-08-18) — the C3c tail is **NYCA-wide, not Long-Island locational**; `online_rho` measured; and the bridge's lay-up membership correction **PROMOTED**

**KEEPER → `2026-08-18-nyiso-144-layup-exclusion`**, superseding
`2026-08-18-nyiso-143-n11tsl-arm`. Determination **CALIBRATED** (rubric v3.4),
C3c the lone ledgered caveat, **bit-unchanged at 2/0/5 h** against RT actuals
10/13/42 — no gated criterion moves at all, so the structure-over-gates clause
is neither invoked nor needed.

*Log-continuity note: nyiso-143 promoted a keeper but left no entry here, so the
previous section's "Next number: **nyiso-143**" is the last marker on file. This
entry follows nyiso-143's promotion, whose full record lives in
`RESULT-nyiso143-zone-k-transfer-bound-ab-2026-08-18.md` and the keeper shard.*

### The headline finding — the successor object was misidentified, and it is not downstate

nyiso-143 named "build a downstate scarcity mechanism" as its critical path,
having measured that 100 % of the **model's** C3c tail hours are Long_Island.
This session measured what the **real** tail is before building anything, from
NYISO's own posted RT ancillary prices (full 11-zone, 8,760 h coverage) in
exactly the actual C3c tail hours:

| year | tail h | NYCA-wide reserve price (mean) | share of tail h > $50 | LI *locational* adder (mean) |
|---|---:|---:|---:|---:|
| 2023 | 10 | **$306.74** | **100 %** | $116.00 |
| 2024 | 13 | $31.74 | 15 % | $5.36 |
| 2025 | 42 | **$393.31** | **95 %** | $152.12 |

The tail is a **control-area reserve-shortage pricing event** that Long Island
participates in, not a Zone-K separation. **A downstate-scoped mechanism could
not have reproduced it.** The instrument that would price it already exists —
`nyca_10min_spin`, published 655 MW at a **$775** RCPF — and binds in **zero
hours of all three years**, as do both Long Island families, because the classes
are idle-allowed. Same object nyiso-110 named from the reserve side and
nyiso-124 located as a downstate price-formation gap: **one gap, control-area
wide.** Record: `FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md`;
probe `scripts/probes/_nyiso144_tail_anatomy.py`.

### `online_rho` — measured for the first time, and it lands below its own code's band

`scripts/data/derive_campd_online_reserve_rho.py` +
`src/market_sim/data/online_reserve_rho.py`. Measured `incity_obligation`
**0.3014** (min-load sensitivity 1.2462) over 401,361 online unit-hours at 95.5 %
CAMPD coverage; `nyc_spin` **0.2011** (1.1247) at 80.5 %.

**Settled:** the downstate gated family is LIVE — `rho*` for inertness is ~3.0,
far above the entire admissible band, so rho decides how *hard* the row binds,
never *whether*. **Not settled:** both values fall **below the code's own
`RHO_CLIP` floor of 0.5**, a band inherited from the legacy path with **no
primary citation anywhere in the repo**, so `rho_used` returns the floor rather
than the measurement. The band was left **unchanged** rather than widened to fit
the measurement. Both gated flags stay `U` on an owner D-5(b) call.

`nyiso_spin_reserve_online` keeps its `I`, **confirmed rather than overturned**:
`rho*` is 0.3426 / 0.3635 / 0.4619, *below* nyiso-110's own stated 0.5 floor, and
the eligible output is dominated by hydro, which has no CEMS and **no
`RAMP10_FRAC_*` entry at all** — a coverage gap, not a measured zero. No
NYCA-wide rho row was derived, deliberately: measuring through that gap would
manufacture a binding constraint out of missing data. **Re-open condition, now a
single purchasable object: a defensible 10-minute deliverable-ramp capability for
NYISO hydro.**

### The promotion — all six pre-registered kill gates PASS

One differing field, `nyiso_gas_bridge_plant_exclusions` False → True, giving
the commitment bridge the lay-up **membership** channel that existed only on the
reliability floor (nyiso-140 repaired one *mechanism*, not the plant; rule 19
`[R-ONE-MECH]`). Identification is the nyiso-140 criterion **verbatim** — median
CAMPD plant gross load zero in every (year, 4-hour block) cell of 2023–2025 —
derived **blind to the mechanism's own D-4 verdicts**, which is what makes its
selection of **7 of the bridge's 8 D-4 failures** evidence rather than fitting.
The per-cell quantifier is load-bearing: a *pooled* median of zero also catches
ordinary cyclers, and the qualifying set stops at 18/18 zero cells against a
nearest non-qualifier at 16/18.

**K2's prediction was made before either solve and landed within 1.3 %:** shed
0.1201 / 0.1406 / 0.3099 TWh against a predicted 0.1186 / 0.1396 / 0.3089 (±50 %
band). **K3:** zero stray losses, zero residuals. **K4:** D-4 unit-conduct
failures **17 → 3**, zero new. **K6′ never escalated** — every material class's
forced share *falls* (ST_GAS 20.2→19.7 / 24.9→23.9 / 16.7→14.7 %), the opposite
of nyiso-140. **Zero new free parameters** (DOF ledger 39 → 40, `n_residual`
unchanged at 6 — the entry is a plant-code *set*, `n_scalars` 0).

**What it does not buy, plainly:** no fit improvement, and none was expected.
Across both full `calibration_verdict` reports the **only** difference is a
skipped, non-gated day-ahead diagnostic line. What it buys is legitimacy: ~0.57
TWh over three years no longer manufactured at plants whose own meter says they
were mothballed.

**Two plants deliberately left in**, both named in the pre-registration before
the solve: **7314** (the eighth D-4 FAIL, 77.1 % of its floored hours metered at
zero) fails the lay-up test — it is a cycler the model's own P0 over-runs, so its
forcing is an **offer/economics** defect and excluding it would bury that error
in a membership list (rules 1 / 14); it is the **named successor**. And **2517
Port Jefferson** stays in the bridge population (D-4 verdict `pass` all three
years) though correctly excluded from the reliability floor.

**Record correction:** the nyiso-144 handoff's Port Jefferson figures (0.1495
TWh / 4,623 h / 0.000 MW / 71.2 % in 2024) do **not** match the keeper's own
committed `legitimacy_diagnostics.json` (0.0616 TWh / 1,716 h / 45.222 MW /
44.7 % / **pass**). Roseton's row matches exactly; 2517's and 7314's do not. The
committed artifact is the source of truth and the arm was scoped to it.

### Posture

Frontier **still NOT-YET**, but changed in kind: all four open items are now
enumerable and none is open investigation — (1) NYISO hydro's 10-minute ramp
(**data intake**, the new critical path), (2) the uncited `RHO_CLIP` band
(**owner D-5(b)**), (3) plant 7314's bridge over-run (**lane-sized**,
offer/economics), (4) `nyiso_iroquois_winter_spread` (**owner** ×2).
`complete` **held and re-keyed** with the determination re-verified from
committed artifacts (rule 22 D-5(b); the superseded keeper re-scores CALIBRATED,
so the worse-determination stop does not fire). **Absent from `final`** —
nyiso-142's NOT-READY stands, unchanged. Holdout spend freeze **ACTIVE**: every
year solved, scored or read this session is 2023–2025.

Gates: `audit_keepers.py --iso NYISO` **0 failures / 0 warnings** ·
`build_status.py --check` 6/6 in sync → `NYISO:CALIBRATED` ·
`check_mechanism_matrix.py` integrity + anchors + keeper stamps OK · 1,927 tests
pass. Next number: **nyiso-145**.

## 2026-08-19 — nyiso-146: per-plant measured min-run — REJECTED on its own gates; the rejection is the finding

Pre-registered (PREREG-nyiso146-perplant-min-run-2026-08-19.md, committed
before either solve, two pre-solve amendments) A/B of
`nyiso_gas_bridge_plant_min_run`: fill each slow-start row's minimum-run from
its own plant's measured CAMPD run-length p25 (plant-summed series; artifact
campd_perplant_min_run_NYISO.csv), replacing the class scalars. Phase 0
refuted the class scalar as a population description (CC per-plant p25 spans
7-646 h vs 21 h). The arm delivered the floors EXACTLY (Bethlehem 685->1,329
GWh 2023; all 15 per-plant ratios in band) and the object did not move:
Bethlehem P1 starts -7.6/-9.5/-4.6% vs bars >=50/>=10/>=10%, plus one new D-4
conviction (Saranac 2024). K5 clean — the arms' production verdicts are
line-identical (C3c bit-identical 2/0/5) — so the rejection is on the
pre-registered object gates, not fit. Diagnosis: every bridge floor covers
only P0-OFF hours; the fragmentation lives in P1's bid-cost pass shutting
committed plants INSIDE P0-on hours — the ercot141 `floor_online_hours` state
leg's exact domain, never tested on NYISO. Both arms registered
(2026-08-19-nyiso-146-control / -perplant-minrun); keeper unchanged.
RESULT-nyiso146-perplant-min-run-ab-2026-08-19.md.

## 2026-08-19 — nyiso-146b/c (same session): KEEPER PROMOTED — the duty-scoped LSL state floor closes the CC over-cycling object

Three more pre-registered arms in the same session, chained single-delta from
the registered control. Arm B (`nyiso_gas_bridge_online_hours`, the ercot141
state leg, gas_cc-scoped): REJECTED-AS-ARMED — it repairs the near-baseload
cohort exactly AND over-glues the 7-20 h-p25 cyclers (Athens-2025 9 vs 63
metered starts; one new D-4 at Saranac); the two cohorts are the two sides of
the phase-0 6.6x run-length gap. Arm B2 (+`nyiso_gas_bridge_state_floor_min_run`,
membership = the frozen min-run artifact over
constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS=100 h): PASSES EVERY GATE →
**KEEPER `2026-08-19-nyiso-146c-state-scoped`, CALIBRATED**, C3c lone
ledgered caveat bit-identical 2/0/5. Bethlehem 327/526/262 P1 starts (6-7
metered) → 41/10/15, medians 12/7/14 h → 68/144/319 h; Caithness lands on
metered; zero new D-4/D-1; zero new scalars; `complete` re-keyed under
D-5(b); auditor PASS. Arm C (`cc_reserve_duty_split`, the duty-role mirror
split): REJECTED — Sterling/Massena/Batavia repair at ≥88 % but Allegany
only −64/−50 % and C3a-2023 +9.0 → +11.3 % (the ~1.4 TWh phantom cheap
upstate energy was price-relevant); its first solve was INERT (seam clobbered
by pct_peaking/cc_duct_peaking; fixed, disclosed, both solves registered).
Defect B is now a JOINT object with the 2023 upstate price level.
RESULT-nyiso146bc-state-floor-keeper-2026-08-19.md.

## 2026-08-20 — nyiso-147: the 2023 upstate price root cause FOUND (the CHP BTM carve) — measured repair REJECTED-AS-ARMED; keeper unchanged

Phase 0 (no LP): C3a-2023's +9.2 % decomposed **entirely into Upstate_West**
(+9.46 pp contribution; +30.8 % zone error, year-round, present all three
years but cancelled by downstate under-pricing in 2024/25 — the missing
zonal gradient of nyiso-126 §2.3(4), now zone-attributed). Fuel basis
refuted (west marginal gas $1.79–1.96 vs SOM Z4 $1.82); the $8.1 "markup"
is ~$7.4 RGGI; the real object is the marginal unit's identity (a ~10-HR
unit where reality clears a ~7.2–7.5-HR CC). Root cause: the
`chp_steam_following` merchant 35 % BTM carve — self-described
"residual-identified … no independent source yet" — is REFUTED by the
plants' own meters: Sithe Independence (54547) delivers 100.3 % of its
EIA-923 net to the NYISO grid (Gold Book Table III-2a, three years), BNY's
carved capacity implies CF 1.07, Independence-2024 needs CF 0.93 of its
carved 753 MW. New rule-23 artifact `chp_btm_share_measured_NYISO.csv`
(16 plants, two published meters, zero fitted scalars); new default-off
`nyiso_chp_btm_measured` consumed by all three share legs (LP carve,
add-back, bench classFull).

The A/B (prereg first; control replay byte-identical to the keeper): the
single delta moves lw C3a **+8.7 → +1.5 % (2023)** and lands upstate within
$1 of actual in 2024/2025 (+0.89 / −0.38 eqh err) — the object CONFIRMED —
and is **REJECTED-AS-ARMED** because the carve was masking three defects
that become visible with the capacity restored: Selkirk dispatches 7.9× its
meter (idle-cogen phantom energy, CHP-side merit-order inversion), CC_CHP
over-runs +5.0 TWh against its OWN corrected bench (offer-implied CF vs the
class's real 0.4–0.7 conduct), and 2025 breaks the band at −12.2 % (the
control's −2.2 % "pass" was ~$6/MWh of masked under-pricing). Owner
structure-over-gates clause considered, not applied. Artifact and wiring
ship default-off (the pjm-146 disposition). Arm B (`cc_reserve_duty_split`
re-arm) did not solve — conditioned on arm A passing. Successors: CHP
idle/lay-up membership + CC_CHP conduct; the 2025 level object. Runs
`2026-08-20-nyiso-147-control` / `2026-08-20-nyiso-147a-chp-btm`; evidence
`RESULT-nyiso147-chp-btm-ab-2026-08-20.md`,
`FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md`,
`_nyiso147_ab_gates.json`.

## 2026-08-21 — nyiso-148: frontier re-statement; the CHP lay-up duty split REJECTED-AS-ARMED, and the 2025 level proven NOT a CHP object

**Keeper unchanged** (`2026-08-19-nyiso-146c-state-scoped`), re-verified
**CALIBRATED** at HEAD on committed artifacts and on the miso-171 scorer
(`audit_keepers --iso NYISO` PASS 0/0; the unit-grain attribution repair adds
three `ST_CHP × chp_steam` rows — forcing previously mis-credited to `CT_CHP` —
and shifts bridge shares ≤ 0.3 pp, flipping no C8 record and no determination).
Holdout freeze ACTIVE; 2023–2025 only.

**Part 1 — frontier.** `ASSESSMENT-nyiso148-frontier-2026-08-21.md` supersedes
nyiso-145 as NYISO's live frontier statement. **Still NOT-YET, but the queue
changes in KIND**: nyiso-145's two lane-sized objects collapse to ONE with a
PROVEN cause (the 35 % residual-identified merchant CHP BTM carve, refuted by
the plants' own market meters) blocked on an unbuilt representation of CHP
conduct. Recorded for the first time, and it governs how the keeper's own
numbers may be read: the keeper's C3a-2025 **“pass” (−2.2 %) is ~$6/MWh of
MASKED under-pricing**, and the model carries essentially **no zonal gradient**
(< $1.5 across five zones in 2024/2025 against actual $9–15) — Upstate_West
+11.4/+10.8 % cancelled by NYC −4.4/−7.4 % and LI −9.5/−11.4 %. True as scored
on the load-weighted mean; no longer quotable as a validated 2024/2025 level.
`complete` HELD and correctly not re-keyed (no promotion); `final` **NOT-YET on
the merits** — no 2026 reserve-requirements file, no 2019 NYISO LMP file and
2019 carries one actual RT hour > $300 so it cannot discriminate on C3c, and
the fleet a touch-once spend would burn is now known to be misspecified.

**Part 2 — the lever.** Phase 0 (`_nyiso148_chp_conduct_phase0.json`, no LP)
measured the CHP fleet's own CAMPD/EIA-923 conduct **before** the construction
was chosen. The nyiso-140/144 zero-cell criterion applied beyond the bridge's
`(CC_REGULAR, ST_GAS)` population selects 10 of 20 CAMPD-covered CHP plants —
and the measurement **forced a guard**: three of those ten (RED-Rochester 10025,
Ticonderoga 54099, Cornell 50368) are **CAMPD-INVISIBLE, not idle** (p99.5 HSL
= 0.0 MW against 439–950 GWh of EIA-923 net), so the census must ABSTAIN where
the meter is silent. That is a degeneracy test, not a threshold, so the leg
stays zero-DOF. Seven qualifiers remain, separating 18/18 against a nearest
non-qualifier of 13/18.

New default-off `ScenarioConfig.chp_layup_duty_split` (+ census artifact and
derive script) routes that cohort's CHP tranches to the class peak band — the
`cc_reserve_duty_split` construction, disjoint by class scope, zero new scalars.
**REJECTED-AS-ARMED** on its own gates: D-K1/D-K2/D-K4 PASS; D-K3 (overkill),
D-K5 (C1-2024 `CC_REGULAR` PASS → FAIL at share **+3.04 pp** vs ±3 pp; the TWh
leg still passes at +3.22 of ±3.98) and D-K6 (2025 recovers **18.9 %** of the
base's −12.2 %, bar ≥ 40 %) FAIL.

**What it buys** — substantial, and why the rejection is worth reading: CC_CHP
volume lands **+0.23 TWh (2023) / +0.03 TWh (2024)** against a base of
+1.52/+1.53; CC_REGULAR-2023 share goes to −0.0 pp; against the base **C3a-2025
FAIL→PASS, C3b-2025 FAIL→PASS and C8 FAIL→PASS** (the base's D-2 `ST_GAS`-2024
30.4 % forced-share failure is cleared); C3a-2023 reads **+3.4 %** against the
keeper's +8.7 %, i.e. the nyiso-147 upstate repair carried.

**The two findings that reject it.** (1) **Energy is CONSERVED**: removing
1.29/1.50/1.68 TWh of CC_CHP moves the gas family total by −0.01/−0.11/−0.02 TWh
— the load is re-served by CC_REGULAR (+0.60/+0.76/+0.76), ST_GAS
(+0.46/+0.48/+0.61), CT_PEAKER and imports at almost the same offer — so the
price moves only +$0.63/+$0.79/+$1.50 and **the 2025 −12.2 % survives removing
the entire CHP phantom**. The 2025 dear-gas level is therefore an **OFFER-LEVEL**
object, not a capacity or membership one: $1.50 of the $8.07 gap is recoverable
here, **$6.57 is a different object** (owner card
`docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`). Do not scope
CHP membership work against the 2025 level. (2) **One band cannot make a graded
response**: the cohort goes bang-bang — essentially OFF in 2023/2024 (Selkirk
2.01×/6.78× → 0.03×/0.04× of its own meter) and STILL OVER in the dear year
(Lockport 3.96×, Yerkes 2.15×, Oswego 1.92× in 2025) — while the real plants run
1.6–18.6 % of hours in 10–43 h runs and scale *with* price (Selkirk metered
gross 156.9 → 107.7 → 384.8 GWh). The successor identification is a
**price-conditional on-share** (a duty curve), not a band level; the membership
is sound and must not be re-derived (rule 23).

**Seam lesson, second lane in a row.** The first ARM D solve was **inert by
half** — the leg was wired at `fleet_to_bins` and mirrored in `offer_curves` but
not at `assembly.py::bins_to_fleet`, so `pct_peak` was clobbered back by the
tranche artifact / duct-burner map (verbatim the nyiso-146b defect). Caught by
the arm's own **D-K2 anti-inert gate**, which tests band composition rather than
a price delta; disclosed in PREREG §9 before the corrected solve and registered
as a plumbing probe. *Standing note: wire `bins_to_fleet` FIRST and prove
liveness on band composition before reading a price.*

Arm E (`cc_reserve_duty_split` re-arm) did **not** solve — conditioned on ARM D
passing; `PREREG-nyiso146b §ARM C` untouched. Runs
`2026-08-21-nyiso-148-chp-layup` / `2026-08-21-nyiso-148-inert-plumbing`;
evidence `ASSESSMENT-nyiso148-frontier-2026-08-21.md`,
`RESULT-nyiso148-chp-layup-duty-2026-08-21.md`,
`PREREG-nyiso148-chp-layup-duty-2026-08-21.md`, `_nyiso148_ab_gates.json`,
`_nyiso148_chp_conduct_phase0.json`.

### 2026-08-21 addendum — STOP-THE-LINE: NYISO's committed benchmark part was STALE

Surfaced by nyiso-148's own registration and escalated to the owner **without
writing any determination**. `frontend/data/backcast/bench/NYISO/{2023,2024,2025}.json.gz`
had not changed since 2026-08-17; this session was the first NYISO registration
since then whose bundle carried the benchmark inputs, so it was the first to
**regenerate** the part. On the regenerated part **every registered NYISO run —
the keeper included — reads `NOT-YET`**, on the same new failure: C1-2024
`CC_REGULAR` (keeper +5.18 TWh, share +4.5 pp against ±3 pp).

**It is not caused by anything this session armed.** Rebuilding the part at this
HEAD with `nyiso_chp_btm_measured` OFF and ON gives **byte-identical
`classFull`** in all three years. The per-plant `plants` rows are identical apart
from two measured-BTM values, and `Σ (e_ann − btm)` is the same in both parts —
the ~4 TWh moves entirely inside the benchmark's EIA-923
vintage-reconciliation / CAMPD-backfill layer (CC_REGULAR-2024 backfill +8.00 →
+4.02). The raw EIA-923 parquet is unchanged since 2026-08-17.

**Nothing was written**: `calibration-complete.json`, `keepers/NYISO.json` and
`status/NYISO.js` are byte-untouched and still assert CALIBRATED (rule 22
D-5(b) — a worse re-verified determination stops and escalates, never silently
lands). The regenerated part is **kept** rather than reverted (rule 14
`[R-ACCURATE]`: reverting would bury a discovered defect inside a stale input).
`audit_keepers --iso NYISO` consequently FAILS on three text-vs-verdict
mismatches, and **that failure is the intended signal**, to be resolved by the
owner's ruling, not by editing the text.

This session's own affected claims were corrected rather than left standing:
`ASSESSMENT-nyiso148-frontier` §1 carries a CORRECTION block, and
`RESULT-nyiso148-chp-layup-duty` §1a withdraws its D-K5 FAIL (on the
regenerated bench the keeper fails C1-2024 too, and by more, so the gate's
condition is not met). **The arm's verdict is unchanged — REJECTED-AS-ARMED on
D-K3 and D-K6.** Root cause (which commit moved the backfill, and which
reconciliation is right) and the cross-ISO exposure are OPEN and chartered to
the owner. Evidence:
`FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md`.

### 2026-08-21 addendum 2 — the owner's ruling landed; cross-ISO sweep; the mechanism fixed

**Owner ruling** (`AskUserQuestion`, session nyiso-148): (1) the **regenerated
benchmark is authoritative**; (2) **sweep and fix the mechanism**.

**Ruling landed.** NYISO's determination restated to **NOT-YET** in the three
places that asserted the superseded one — the keeper sidecar, the
`calibration-complete` marker (prior value preserved in
`determination_at_prior_rekey`; new `marker_reexamination_open` records the
second question the ruling opened, whether validation-tier authorization
survives a NOT-YET determination) and `status/NYISO.js`. **The run remains the
designated keeper** — still NYISO's most structurally faithful run, with no
successor — it is now a NOT-YET keeper. The marker is **left in place**, not
withdrawn: withdrawal is a separate owner decision, and it authorizes nothing
spendable today because the holdout spend freeze outranks every marker.
`audit_keepers --iso NYISO` passes 0/0.

**Sweep (read-only, nothing regenerated or committed).** A faithful cross-ISO
regeneration would need every ISO's raw data hydrated and a bundle carrying
benchmark inputs; the sweep instead measures the exposure at git's own
resolution — a part is potentially stale iff the code that produces it changed
after the part was written, an **upper bound**, reported as one. **Five of six
ISOs are exposed**: CAISO, ERCOT, MISO, NEISO and PJM all sit on parts written
2026-08-17, behind **22 engine commits**; only NYISO is current. Two refinements
keep the bound honest: the single builder-script commit since then (`01db36d`,
nyiso-147) is **provably gated** to NYISO-with-the-flag and so explains neither
the NYISO drift nor any other ISO's part — which is why the root cause stays
OPEN — and the exposure is carried by the ENGINE import closure (class map, CHP
shares, EIA-923 reconciliation), consistent with the delta having been localized
to the vintage-reconciliation layer rather than the meters.

**Fix, three pieces.** (a) `scripts/lib/bench_stamp.py` stamps every part with
`meta.builderFingerprint`, a hash of the builder sources — **content-derived
only**, because a timestamp or HEAD sha would rewrite every part on every
registration and destroy the byte-determinism that let the staleness hide;
verified to move nothing else (re-rendering NYISO's parts left `classFull`
identical in all three years). (b) `scripts/check_bench_freshness.py` gates in
two tiers: HARD on a fingerprint mismatch or absence, SOFT (reported, never
gating) on engine commits since the part was written — folding the engine into
the hash would mark every part stale after any lane's edit and train everyone to
ignore it. (c) `calibration_verdict.py` prints a loud `[!] STALE BENCHMARK` line
naming the parts and the fix; it **warns and never fails**, verified silent on
NYISO and loud on PJM with the verdict untouched.

**Deliberately NOT done: the checker is not wired into CI as a hard gate here.**
Nineteen of twenty parts are stale, so gating now would red-light every PR for
defects only each ISO's own lane can fix. Sequence: each ISO regenerates and
re-verifies, then the gate goes on. OPEN after this session: the benchmark root
cause (chartered BEFORE any NYISO re-calibration), the five ISO regenerations,
turning the gate on, and the `complete`-marker question. Evidence:
`FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md` §§8–11,
`_nyiso148_bench_staleness_sweep.json`.

## 2026-08-22 — nyiso-149: the benchmark root cause CLOSED (it was the flag through the ±3% reconcile) and the duty curve PROMOTED — the first keeper CALIBRATED on the authoritative benchmark

**Job 1 (owner-chartered, blocking).** The 2026-08-17→08-21 benchmark drift is
fully attributed with an exact closure
(`FINDING-nyiso149-bench-root-cause-2026-08-22.md`,
`_nyiso149_bench_reconcile_closure.json`): the EIA-923
vintage-reconciliation/CAMPD-backfill layer **never moved** — the benchmark
frame rebuilt at HEAD hashes to `920c8b8bc1b1`, the identical shared-input
name every registered NYISO bundle meta declares — and the whole classFull
delta is commit `01db36d`'s flag-dependent BTM subtrahend: the 35 % sector
carve left the gas family 6.5–15.9 % below the EIA-930 target so
`reconcile_vintage_classes` scaled every gas class ×1.069/×1.117/×1.189
(CC_REGULAR-2024's +3.98 TWh exactly), and the measured subtrahend lands the
family inside the ±3 % deadband so the scale stands down. Both committed
parts reconstruct EXACTLY (every gas/coal class, all years) from one frame +
the two btm bases. nyiso-148 §2's "none of it is the flag" is corrected by
addendum — its flag-flip test was blind to `btm.parquet`, which
`rebuild_benchmark` does not rebuild. **RULING: the regenerated (measured)
reconciliation is CORRECT** — the subtrahend is the plants' own meters
(rule 14), EIA-923+CAMPD agrees with EIA-930 unscaled only under it, the old
part's extra CC_REGULAR mass traces to no measurement, and the exposed keeper
C1-2024 failure is the real over-dispatch nyiso-147/148 diagnosed from the
other side. **PINNED**: `_btm_frame` now emits `btm_bench_twh`
(measured-when-artifact-exists, flag-INDEPENDENT — the bench subtrahend) next
to the run-basis `btm_twh` (the model add-back); the render's bench-part
writers consume the bench basis; the committed parts reproduce byte-for-value
with the flag OFF and ON alike (unit-pinned,
`tests/regression/test_btm_bench_basis_pin.py`).

**Job 2 (the CHP conduct successor).** `chp_layup_duty_curve` — the graded
price-conditional duty nyiso-148 named when it rejected the single band: per
frozen-census plant, on-share by own-zone RT price band (p40–p80/≥p80,
declared a priori) × loading-when-on × HSL, measured **conditional on
envelope-live hours** so the availability envelope and the offer never
double-count the same mothball spells (rule 19; phase 0 measured the envelope
tracking metered live share within ~0.02 for six of seven plants, Lockport
the exception whose lay-up the offer carries whole). Offered as **MW** at the
class's existing band multipliers, remainder withheld from energy and
reserves; zero new free parameters. All pre-registered gates pass
(`PREREG-nyiso149-chp-duty-curve-2026-08-22.md`,
`_nyiso149_duty_curve_gates.json`): base replay bit-identical to registered
147a; single delta; LP-entry composition exact to 0.01 MW; graded conduct
in-band on all 21 plant-years (Selkirk 0.54×/1.76×/0.85× of its own meter;
cohort 291→413→988 GWh matching the metered climb into dear 2025); zero new
D-rows with the base's D2 ST_GAS-2024 failure CLEARED; C1 **14/14** incl.
CC_REGULAR-2024. vs the base: C3a-2025 −12.2 % → −8.8 % PASS, C3b-2025 →
PASS, C8 → PASS. The first solve applied pct fractions to the wrong capacity
basis — **caught by gate F-K2 before any scoring**, disclosed in PREREG §7,
fixed by the MW contract, registered as `2026-08-22-nyiso-149-basis-probe`.

**PROMOTED: keeper → `2026-08-22-nyiso-149-duty-curve`, determination
CALIBRATED** (C3c the single ledgered caveat, 1/0/0 h vs RT 10/13/42);
D-5(b) re-key executed (label improves, stop does not fire);
`audit_keepers --iso NYISO` PASS 0/0; shard + §5.5 header re-stamped
(`chp_btm_measured` R→K — the named successor arrived). OPEN and not claimed:
the 2025 offer-level object ($6.57, owner card pending), C3c, the zonal
gradient, Flynn starts. Records: `RESULT-nyiso149-duty-curve-keeper-2026-08-22.md`.

## 2026-08-22 — nyiso-150: the frontier directive session — both live arms tested and REJECTED on their own gates, the gradient object PROVEN LOCATIONAL, four standing items closed

**Owner directive (verbatim): "Is NYISO at frontier? If not, please continue
working thru and finalizing to reach frontier."** Keeper
`2026-08-22-nyiso-149-duty-curve` re-verified CALIBRATED at HEAD before
anything ran (`audit_keepers --iso NYISO` 0/0); read with the Q1 card
(`DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`, recommendation
A), the directive charters the 2025-level/gradient object and the queue.
Prereg committed and pushed before any arm solved
(`PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md`,
Amendment 1 mapping the nyiso-122 refusal grounds to kill gates).

**Phase 0** (`_nyiso150_gradient_phase0.json`): the model carries essentially
no zonal gradient (annual eqh max−min $2.21/$1.47/$0.80 vs actual
$15.73/$9.17/$14.83); the 2025 downstate miss is ~2/3 winter event months,
~1/3 the summer heat-wave months — and the summer face is the LEDGERED C3c
limitation measured in the mean (Jun 22–26 alone carries $24.0/MWh of the
June system monthly mean). The winter-spread construction evaluated at both
flag settings: NYC's gas is bit-identical on/off in every month (the annual
offset cancels the Iroquois column's built-in spread exactly), and the
flag-off construction gives Upstate_West PHANTOM gas at both ends (Jan-2025
$11.01/MMBtu vs the ~$3.5 measured Tenn Z4 world; summer-2025 $0.16–0.64).

**The A/Bs** (control = keeper replay, IDENT PASS max |Δprice| = 0.0 ×3
years; both arms registered, rule 15):

- **ARM C′ `cc_reserve_duty_split` re-arm** (`2026-08-22-nyiso-150-reserve-rearm`)
  — REJECTED-AS-ARMED on C-K2, **Allegany 7784 ALONE** (70 %/60 % falls vs
  ≥80 %; Sterling/Batavia/50744 collapse 93–98 %); every other gate passes
  and **the nyiso-146b rejection leg (b) is RESOLVED** (C3a-2023 +5.2 % in
  band on the arm — the CHP repair moved the root cause exactly as the
  queue conditioned). Successor: the nyiso-149 graded-duty pattern applied
  to the reserve cohort.
- **ARM W `nyiso_iroquois_winter_spread`** (`2026-08-22-nyiso-150-winter-spread`)
  — REJECTED-AS-ARMED, and **the rejection is the decisive measurement**: the
  whole state rises together in the winter event months (Dec-24 47.8→61.9
  statewide, UW landing ~exact on its actual; Feb-25 UW exact 87.4 vs 87.1)
  while the downstate−upstate spread stays ≤$1.1 against $11–27 actual — an
  $8–13/MMBtu measured zonal gas spread produces <$1 of zonal price spread,
  so **the winter downstate premium is PROVEN LOCATIONAL at the LP** (the
  internal west→east cutset never binds; nyiso-122's static read and
  nyiso-124's flow-side finding confirmed from the price side). Also fails
  W-K4 (2 new D-4 conduct rows) and W-K5 (C1-2024 CC_REGULAR +3.63 TWh
  PASS→FAIL). Cell `O → R`; re-open ONLY as the companion of a locational
  mechanism that lets the cutset bind.

**Closed without solves**: the D-4 ct_only VINTAGE GUARD
(`legitimacy_diagnostics.ct_only_span_union`, protective-only, unit-tested,
live-verified on the control — the regenerated D-4 fail set is the keeper's
committed set minus exactly the 7314-2025 vintage-artifact row); the
`nyiso_iroquois_winter_spread` TAXONOMY SPLIT (card nyiso-143 D1 executed:
own base row + cells in all six shards); the ASTORIA attribution adjudicated
NON-BLOCKING (both campuses CC_REGULAR × NYC — class×zone targets invariant
to the split; plant-grain hygiene, chartered); FLYNN re-measured and
RE-POINTED (3/2/4 starts vs 4/6/8 metered in months-long runs — the recorded
over-starting premise no longer reproduces; Bethlehem drift 42/14/29 vs 6–7
recorded alongside). Parity allowlist: the three nyiso-150 dirs plus the
omitted `nyiso149_armF_recipe` entry (pre-existing gap, repaired).

**FRONTIER: STILL NOT-YET** — three testable lane objects remain (the
reserve-cohort graded duty, the hydro RAMP10 seams, the `online_rho`
identification) plus the re-pointed start-conduct residual; the
2025-level/gradient object moves to owner court (blocked on identification —
the BLOCKER-B intake class). Full statement:
`ASSESSMENT-nyiso150-frontier-2026-08-22.md` (supersedes nyiso-148's as the
live frontier statement). No promotion; keeper, marker, shard and status
untouched; holdout freeze ACTIVE, every year touched 2023–2025.

### 2026-08-22 addendum — the ARM C′ successor identified to the root: Allegany's heat rate is a class default behind an ORISPL split

Same session, no solve. `FINDING-nyiso150-allegany-hr-identity-2026-08-22.md`:
the "cohort's most efficient" hr 7.5 is `HEAT_RATE_BINS["gas_cc"]["older"]`
(the class default) — the plant's own measured rate lives in eGRID under
**ORISPL 10619** (7.99–8.68 across SEVEN vintages, pooled 8.42; identity
proven by exact eGRID-PLNGENAN == EIA-923-7784 netgen equality in all seven
years), and NYISO's only per-plant measured-HR channel is CAMPD, which the
plant is absent from. The named successor is DEMOTED from a graded-duty
mechanism build to: (1) the identity heat-rate repair (measured artifact at
the existing `heat_rate` preference seam, default-off, NYISO-scoped, zero
free parameters) then (2) a `cc_reserve_duty_split` re-gate on the repaired
control. A general CAMPD-less eGRID-HR channel was sized and REFUTED on its
own population (57 NY plants, mostly BTM cogens and micro-peakers with
realized rates 5.7–118 MMBtu/MWh — threshold-screening it would be a rule-21
construction). EIA-923's CHP flag is `N` every year, closing the
CHP-framework route; Schedule-5 fuel costs 0 rows. Matrix cell record
appended on `offer_curve_by_group`; assessment queue row 3 re-typed.

## 2026-08-22 — nyiso-151: the identity heat-rate repair PROVEN INERT in both postures, the merit-order residual RE-TYPED to reserve-provision dispatch, and the offer-side lane CLOSED

The nyiso-150 successor executed end-to-end
(`PREREG-nyiso151-egrid-identity-hr-and-regate-2026-08-22.md` + Amendment 1,
committed before any arm solved). NEW MECHANISM (rule 28c, row + six cells in
the same PR): `egrid_identity_heat_rates` — the threshold-free two-registry
identity discovery rule (exact PLNGENAN == EIA-923 netgen in every
overlapping eGRID vintage, ≥2 overlaps; NYISO: 108 candidates × 7 vintages →
exactly Allegany 7784↔10619, pooled 8.4209, LOYO [8.3434, 8.5266]); derive +
artifact + loader seam + 5 unit tests + CLI. Mid-session, PR #4193 (the
nyiso-150 work) MERGED and the branch auto-deleted; the unmerged commit was
rebased onto the new main per the merged-branch rule, and the control
re-solved at the post-merge HEAD — **IDENT PASS (max |Δprice| = 0.0 ×3
years)**, proving the concurrently-merged ERCOT-gated reserve changes
NYISO-inert.

**ARM H** (repair alone): REJECTED-AS-ARMED on the H-K3 direction leg —
**BIT-IDENTICAL to the control everywhere** despite the bins frame provably
carrying 7.5→8.4209. Allegany runs ~96 % CF deeply inframarginal; +$2.3/MWh
crosses no LP vertex. The rule-14 accurate-input case is intact and FREE
(zero measured cost anywhere); arming is an owner disposition (the ercot-202
arm-on-legitimacy class). Cell `egrid_identity_heat_rates` NYISO = **I**.

**ARM HC** (repair + `cc_reserve_duty_split`): REJECTED on HC-K2 — Allegany
70 %/60 % falls vs ≥80 %, **BIT-IDENTICAL to
`2026-08-22-nyiso-150-reserve-rearm`** across a hr_peak 11.625→13.052 armed
offer shift. Two offer levels, one armed outcome, at machine precision.
**THE RE-TYPE (the session's finding):** under the split Allegany runs
3,524 h (40 %) with HALF its on-hours at 27–34 MW mid-load on 64.7 MW —
reserve-posture, ~30 MW of 10-min headroom held online. The residual is
RESERVE-PROVISION dispatch the energy offer cannot price away, and its root
chains to the standing hydro RAMP10 seams (~5.69 GW of EIA-860 10M-capable
NY hydro zeroed by the `_ramp10_capability` frac>0 guard + the missing
NYISO ramp module — the co-opt leans on small gas CCs for headroom instead).
**The offer-side lane for the merit-order object is CLOSED** (rule 1: two
levers proven insensitive); the successor is the RAMP10 seams, then
re-measure. Neither arm separately registered (bit-identical replays of
registered runs — the nyiso-149 convention; `_nyiso151_ab_gates.json` +
`RESULT-nyiso151-identity-hr-and-regate-2026-08-22.md` are the record; both
bundles committed). Keeper, marker, status untouched; freeze ACTIVE; years
2023–2025 only. OWNER ITEMS QUEUED: the ARM H arming disposition; the
RHO_CLIP band card (re-verified live: both NYISO measured rhos 0.3014/0.2011
sit below the 0.5 floor, so the clip — not the meter — is the coefficient).

### 2026-08-22 addendum 2 — OWNER SITTING (three rulings) and the ARM H promotion executed

The owner ruled in-session on the queued cards: **(1) RHO_CLIP option A** —
the 0.5 floor is DELETED (`(0.0, 4.0)`; card nyiso-145 annotated; every
measured `online_rho` now solves at its own measurement; both NYISO gated
reserve flags become admissible on data-identified coefficients; the MISO
re-gate consequence flagged in `docs/calibration-log/governance.md`, rule
25). **(2) ARM H PROMOTED** on the arm-on-legitimacy standard (ercot-202
class): registered as `2026-08-22-nyiso-151-identity-hr` — DETERMINATION
**CALIBRATED** on its own registration verdict (bit-identical artifacts +
fresh attestation, DOF 8→9 with the identity artifact at n_scalars 0,
n_residual 6 unchanged) — keeper shard swapped, D-5(b) re-key executed
(worse determination impossible by construction), `build_status` NYISO:
CALIBRATED, `audit_keepers` PASS 0/0, matrix cell I→K with the I record
preserved, shard + §5.5 headers re-stamped. The mechanical direction-leg
rejection stands unrewritten alongside. **(3) RAMP10 chartered** as the next
session. Housekeeping: PR #4196 (the nyiso-151 gates work) merged mid-flow
and the branch auto-deleted — recreated from the new main per the
merged-branch rule; a category-vocabulary typo the merged ERCOT row carried
(`cat: "commitment"`) fixed to `commit` so the matrix checker runs clean for
every lane.

## 2026-08-23 — OWNER RATIFICATION OF NYISO FRONTIER STATUS (records lane; no solve, no merits re-adjudicated)

**OWNER DECISION, 2026-08-23, in session with the program director: "Ratify
NYISO."** The act ratifies the §3 recommendation of
`results/calibration/ASSESSMENT-nyiso154-frontier-2026-08-22.md` ("AT FRONTIER
ON THE MERITS … This assessment RECOMMENDS ratification and is written to be
citable as its basis"), which deliberately edited no `frontier` field because
the declaration is an owner act. **This session records the act and nothing
else:** no LP solve, no re-scoring, no bundle regeneration, no registration, no
determination change, no keeper change, no mechanism armed, disarmed or
re-verdicted, and no other ISO's files touched (rule 25 `[R-ISO-SCOPE]`; the
per-ISO keeper lane of `frontend/data/backcast/keepers/README.md`).

**Recorded.** A `frontier` block added to
`frontend/data/backcast/keepers/NYISO.json` (`declared` 2026-08-23; the owner
act quoted with its director-session attribution; the basis, keeper, open set,
scope and genealogy in the note). `frontier` is attached by
`scripts/build_status.py` *after* `determine()` runs — purely declarative,
never gating, never touching the verdict — and renders as the FRONTIER badge
plus note on the Calibration Status page.

**Keeper and determination UNCHANGED.** `2026-08-22-nyiso-152-duty-complete`,
determination **CALIBRATED** (C1 14/14 free 10/10; C2/C3a/C3b/C4/C6/C8 PASS;
C3a +5.3 %/−2.7 %/−8.1 %; C3c the lone ledgered caveat at 1/0/0 h vs RT
10/13/42). `build_status.py --iso NYISO` then `--check`: in sync,
`[NYISO:CALIBRATED]`. `audit_keepers.py --iso NYISO`: **PASS 0/0**. Independent
`calibration-keeper-auditor` scoped `--iso NYISO`: **PASS, 0 repairs**, which
also confirmed against disk that `final` is empty and the freeze is `active`.

**What the ratification claims (§4):** the NYISO backcast lane has exhausted
its admissible mechanism set at the current representation, and the keeper is
the most structurally faithful configuration tested (rule 1 `[R-STRUCT]`).
**What it does not claim (§4):** *not* that C3c is closed — it is LEDGERED,
1/0/0 against RT 10/13/42, reported at full magnitude on every determination;
*not* that the winter downstate locational premium is represented — blocked on
identification; *not* that any out-of-training year has been touched — none
has; *not* that `final` readiness follows — it does not.

**FRONTIER IS NOT `final`.** Ratifying frontier grants **no locked-test
authorization of any kind**. `frontend/data/backcast/calibration-complete.json`
and `holdout-freeze.json` were **not touched**: `final` stays EMPTY (`_note`
only, NYISO absent), the holdout spend freeze stays ACTIVE, and NYISO's 2019
and H1-2026 remain **NEVER GRANTED and unspent**, as they are for every ISO.
Assessment §2 item 6 is unchanged — `final` readiness is **NOT-YET on the
merits**, because 2019 is unsolvable at HEAD and cannot discriminate on C3c.
No year outside 2023–2025 was solved, scored or read (rule 22 `[R-HOLDOUT]`,
fail-closed). No future session should read the badge as a locked-test green
light.

**Remaining open set (§2), every item owner-court or ledgered:** (1) the summer
downstate scarcity C3c face — model-class, LEDGERED under the rule-22 standing
rule; (2) the winter downstate locational premium, proven locational by solve at
nyiso-150 — owner-court intake, blocked on identification (BLOCKER-B class);
(3) the Q2 2025-level decomposition annotation — owner-court, pending; (4) the
hydro 10-min AS certification + hour-by-hour water limit — owner-funded intake,
now scoped only as the future `nyiso_spin_reserve_online` unlock, the
reserve-supply half having dissolved at nyiso-152; (5) CC cycling-cost
identification (new at nyiso-154) — owner-court identification intake, adopting
it is an identification decision and never a residual fit (rule 13
`[R-MEASURED]`); (6) the `final` grant — owner decision, NOT-YET on the merits.

**Re-declaration genealogy — this SUPERSEDES the 2026-08-06 clearing.** NYISO
held frontier from the nyiso-104 declaration (2026-07-31) until the owner
CLEARED it on 2026-08-06 (session nyiso-130), because nyiso-130 opened a new,
named, untested object that falsified the exhaustion premise: NYISO's Table 1
note 2 of the Locality Bulk Power Transmission Capability Reports publishes that
the Zone-K "Locality Limit" the model used as an hourly bound is NET of a 660 MW
generation loss-of-source ("the true N-1-1 Transmission Security Limit is 940 in
this scenario"), and 100 % of the model's C3c tail hours in all three years form
at that one in-window bound. **That object is CLOSED** — which is why
ASSESSMENT-nyiso154 does not carry it as an open item, and why the exhaustion
premise stands again. Verified at this session's head in
`docs/codebase-site/data/mechanism-matrix/NYISO.js`:
`nyiso_li_tsl_n11_security` = **K** (nyiso-130
`PREREG-nyiso130-li-transfer-security-limit` + `_nyiso130_li_tsl_identification.json`;
nyiso-143 `PREREG`/`RESULT-nyiso143-zone-k-transfer-bound` + `_nyiso143_ab_gates.json`),
`nyiso_gj_locality_tsl` = **G**, `lcr_tsl_published` = **K**,
`tsa_transfer_derate` = **G**. The `frontier_cleared` block is **preserved
verbatim and in place** as that genealogy — byte-identical, verified against
`HEAD` before and against the pushed blob after — and itself preserves the
nyiso-104 declaration note inside `withdrawn_note_preserved_verbatim`; this
ratification is the third layer of that record, not a replacement for it.

**Matrix (rule 26 `[R-MECH-MATRIX]`).** NYISO's shard header re-stamped
(`updated` → 2026-08-23; the `gates` narrative gains the ratification stamp with
the 152 stamp preserved verbatim) and the single `### 5.5` prose header plus its
FRONTIER STATUS block re-stamped from "recommended, not declared" to ratified.
**Zero cell verdicts moved** — the shard's entire `cells` block is
byte-identical to `HEAD`, verified programmatically, because this lane tested
nothing. `check_mechanism_matrix.py` clean on all four legs. NYISO's shard and
§5.5 block only.

---

## 2026-08-25 — nyiso-155: the chartered hydro truncation repair RE-ARMED and A/B'd; it had been armed at nyiso-108 and SILENTLY LOST from the lineage; the re-arm is ESCALATED on a determination downgrade (C3a-2025)

**2 solves** (zero-delta control + the pair, three years each, concurrent per
rule 12). **HEAD `ac194ba`.** **KEEPER UNCHANGED**
(`2026-08-22-nyiso-152-duty-complete`) — the promotion is **ESCALATED TO THE
OWNER** under the prereg's pre-committed rule. Prereg pushed + blob-verified
BEFORE any measurement (`PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md`).
Registered (rule 15): `2026-08-25-nyiso-155-hydro-control` (**CALIBRATED**),
`2026-08-25-nyiso-155-hydro-repair` (**NOT-YET**). Full write-up:
`docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md`; gates record
`results/calibration/_nyiso155_hydro_repair_ab.json`.

### (1) Discovered before measurement: nyiso-108's arm was SILENTLY DE-ARMED

The charter (nyiso-107's carried item) was already executed once — nyiso-108
(2026-07-31) armed the pair and was promoted by owner override. The pair then
fell out of the keeper lineage with **no de-arm decision anywhere**: in the
recipe at nyiso-114 (2026-08-02), gone by nyiso-144 (2026-08-18). Mechanism:
the two flags are `solve_and_persist` **kwargs, not ScenarioConfig fields**, so
the "all 680 scenario_config fields identical" lineage-fidelity checks were
structurally blind to them (miso-50..53 lossy-reconstruction class, in the
keeper lineage itself). The keeper's own sidecars confirm unrepaired hydro
(28.3833 / 27.8294 / **21.0482** TWh — the truncated 3-plant 2025 budget spent
exactly). Matrix cell `hydro_vintage_input_repair` **K → O** (record-truth: K
cited a keeper arm no keeper carries; the nyiso-128 solar-basis convention).

### (2) The A/B reproduces nyiso-108 exactly; the trade lands on 2025 this time

Hydro Δ **−1.5505 / −1.0904 / +3.0107 TWh** — nyiso-108's measured deltas to
4 dp; 2025 fleet **3 → 147 units**. Volume lands **−4.28 / −2.64 / −0.19 %**
— **TAUTOLOGICAL BY CONSTRUCTION** under the 930 pin (declared, never banked;
vs P-63: −1.29 / −0.88 / −0.78 %). **SHAPE (the only load-bearing hydro
evidence): 2025 improves on every statistic** — hourly r 0.562 → 0.712,
daily r 0.316 → 0.437, monthly-vs-P-63 r 0.925 → **0.994**, hod swing
1,049 → 1,903 MW vs measured 1,830 (the 3-plant fleet physically could not
produce the real diurnal swing); 2023/2024 hourly r degrade moderately
(0.739 → 0.691, 0.795 → 0.756), reported at full magnitude.

### (3) THE COST: C3a-2025 −8.1 → −10.8 % FAIL; determination NOT-YET; ESCALATED

Removing phantom 2023/24 hydro lifts those years (+5.3 → +6.8 in-band — the
nyiso-109 anchor holds; 2024 **improves** −2.6 → −1.7). Restoring the real
3.01 TWh of 2025 hydro softens 2025 by −$1.79/MWh, crossing the band. **The
truncated input was masking ~2.7 pp of the real, already-owner-court 2025
offer-level object** (`DECISION-CARD-nyiso148-2025-level-remainder`, Q1
pending) — its true magnitude is ~$1.79/MWh larger than the truncated
baseline showed. C3c counts BIT-IDENTICAL (1/0/0); it reads FAIL on the arm
only because the standing rule's lone-failure guard is silenced by C3a. C1/C2/
C3b/C4/C6/C8 PASS both arms; zero new D-rows; fossil displacement 1:1. Rule
14 in both directions: the accurate input is right and stays right; the 2025
miss is a **discovered defect** of the price level; and neither reverting the
input nor overwriting a CALIBRATED frontier-ratified keeper is this lane's
call — the exact nyiso-108 precedent, transposed to 2025, back to the owner.

### (4) G1 drift, reported: the keeper does not reproduce bit-identically at HEAD

The zero-delta control differs from the committed keeper in 2023/2024 (max
hourly |Δλ| 2.18 / 2.61 $/MWh, annual mean +0.016 / +0.018; **2025 exactly
0.0**) with all nine pinned inputs content-identical, demand + reserve
requirements bit-identical, identical package environment — the degenerate
alternative-optima reshuffle class, and **determination-identical**
(CALIBRATED, criterion for criterion). Owner options framed in the finding §5:
promote the arm (nyiso-108 precedent), hold + charter the 2025 level object
first, and/or re-key to the control (nyiso-128b stale-baseline precedent).

Rule 22: every solved year ∈ {2023, 2024, 2025}; the spend freeze untouched.
Zero fitted scalars; DOF ledger +1 measured entry (n_residual unchanged at 6).

Next shorthand: nyiso-156.

---

## 2026-08-25 — nyiso-155b: OWNER RULED PROMOTE on the escalation — keeper → `2026-08-25-nyiso-155-hydro-repair`, determination NOT-YET written explicitly

**NO SOLVE.** Owner decision, verbatim: *"If structural integrity improves but
gates regress that may still be a keeper.."* — the nyiso-108/nyiso-120
override class. Keeper re-keyed (152 → 155-hydro-repair), promotion note
chained, `calibration-complete.json` NYISO entry re-keyed with the **explicit
NOT-YET** (D-5(b) stop fired → escalated → resolved by this ruling; never
silently written). Matrix cell `hydro_vintage_input_repair` **O → K**; shard
keeper/gates stamps + §5.5 prose header re-stamped (priors preserved
verbatim); `build_status --iso NYISO` [NOT-YET]; keeper-auditor run. Frontier:
the 2026-08-23 ratification's basis keeper is superseded — status returns to
the owner; record preserved. **Named successor: the 2025 offer-level object**
(`DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending) — now measured
~$1.79/MWh larger than the truncated baseline showed; the hydro input is
correct and stays (rule 14). Freeze ACTIVE, untouched; no locked-test grant of
any kind. `docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md` §7.

Next shorthand: nyiso-156.

---

## 2026-08-25 — nyiso-156: the 2025 offer-level object measured to COMPLETION on the promoted keeper — no third component; either adjudicated face alone would restore the band; sharpened decision card filed

**NO SOLVE.** Precommit pushed + blob-verified BEFORE any measurement
(`PRECOMMIT-nyiso156-offer-level-phase0-2026-08-25.md`); every number read
from the two registered nyiso-155 bundles (same-HEAD pair — arm−control is
exactly the hydro repair, no G1 drift inside it) and the committed actuals.
Probe `scripts/probes/_nyiso156_offer_level_phase0.py`, record
`_nyiso156_offer_level_phase0.json`; model lw anchors reproduce the recorded
61.04 / 59.24 exactly.

**The C3a-2025 gap (−$7.19 lw, −10.8 %) decomposes to the two
already-adjudicated faces and NOTHING ELSE:** Jan+Feb winter downstate
**−3.92** (whole-month, sustained; upstate near-exact — Jan UW 87 vs 90,
NYC 87 vs 134; gradient $0.81 vs $14.83 actual) + **ten summer
scarcity-event days −3.94** (Jun 22–26: model 86.89 vs actual **214.25** lw;
Jul 1/25/28–30: 80.47 vs 159.71) − a +0.59 shoulder over-pricing offset.
**Both faces pre-exist the repair** (control −3.49/−3.87); the hydro
increment's −$1.79 spreads across ALL twelve months (−0.04..−0.27 gap
contribution each) — the repair unmasked, it did not create. **New
load-conditional typing:** the model−actual error is monotone in demand
decile in ALL THREE years (2025 +6.9 → −33.7 $/MWh, top two deciles = the
whole gap; 2023 +6.8 → −5.2; 2024 +4.9 → −6.8, whose eqh hub gap is −$0.03)
— 2023/2024 pass by trough/peak cancellation the dear-gas year outgrows.

**The decisive arithmetic (new):** the band edge is −$6.64; each face is
~$3.9; closing EITHER alone puts 2025 at ≈ −5.3 % — IN BAND — whereupon C3c
reverts to the lone failure and its ledgered CAVEAT, i.e. the determination
returns CALIBRATED through structure. **Card filed:**
`docs/DECISION-CARD-nyiso156-2025-offer-level-2026-08-25.md` — supersedes
the nyiso-148 card's numbers; Q2 (the −2.2 % cancellation annotation)
DISSOLVED (its subject no longer exists); Q1 restated as **authorize the
BLOCKER-B winter identification intake (recommended) vs leave the keeper
standing NOT-YET** — "charter a lane" is overtaken: the summer face is the
closed/ledgered C3c queue, the winter face is access-walled (nyiso-97/122/150
adjudications standing), the offer-side queue stays closed (nyiso-151), and
no admissible lane lever exists until new data does.

Rule 22: years read ∈ {2023, 2024, 2025}; freeze ACTIVE, untouched. Matrix
UNTOUCHED (no mechanism tested — phase-0 measurement only). Zero fitted
scalars; hydro input pair untouched (rule 14; volume statistics quoted
nowhere).

Next shorthand: nyiso-157.

---

## 2026-08-30 — nyiso-156b: Q1 RULED — OPTION A, the winter identification intake AUTHORIZED; spec filed; the seam leg's stale "unidentifiable" record corrected

**NO SOLVE.** Owner ruling on the nyiso-156 card's Q1, delivered in-session
on the §5 options as presented: **"A: Authorize winter intake"** (option text
named both sources — the MyNYISO as-enforced AORR access AND "a source
splitting the Capital_Hudson seam leg"). Executed as
`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`, two legs:

* **Leg 1 (SESSION-EXECUTABLE — the nyiso-126 owner gate is LIFTED):** the
  eastern-seam PAR attribution under the STANDING
  `PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md` (published NY-NJ
  PAR shares 47/21/32, zero free parameters; new NYC AC border path). Intake:
  NYISO MIS P-34 `ParFlows` 2023–2025 (~87 MB, public, verified fetchable)
  under the data contract. K6 baseline re-specified onto the CURRENT keeper
  with the original reported alongside (nyiso-115/117/119 discipline); P3
  honesty stands — the seam alone is NOT predicted to close C3a-2025. If the
  arm passes AND lets the west→east cutset bind, `nyiso_iroquois_winter_spread`
  (R) becomes re-testable on its recorded companion condition — new evidence,
  DO-NOT-REDO satisfied.
* **Leg 2 (OWNER-EXECUTABLE ONLY):** MyNYISO → Reports & Info → the
  current-vintage as-enforced AORR (successors of Table B.4 LRR 1–3, ARR
  37/66/28). On receipt the nyiso-97 §4 content test re-runs against the
  current vintage — PASS yields a commitment-bridge-class prereg; FAIL closes
  the leg with cause exactly as nyiso-97 closed. No parameter is ever backed
  out of the residual to fill a qualitative row.

**Record correction (spec §0, card banner, same commit):** nyiso-150 §4's
"seam half UNIDENTIFIABLE from public data — nyiso-125's rule-20 refusal,
standing", inherited by the nyiso-156 card §3, was STALE when written: the
refusal was discharged on identification the same day (nyiso-126, log
2026-08-04: "it is discharged on identification"); the lane was
authorization-blocked, not identification-blocked. Originals preserved
unedited; no measurement or verdict changes.

Q2 remains dissolved. Keeper UNCHANGED (`2026-08-25-nyiso-155-hydro-repair`,
NOT-YET); no determination touched; no cell verdict moves (nothing tested);
freeze ACTIVE, untouched; zero fitted scalars.

Next shorthand: nyiso-157 (the Leg-1 executor).

---

## 2026-08-30 — nyiso-157: Leg 1 EXECUTED — the seam PAR attribution re-tested and PROMOTED by owner ruling; the iroquois companion re-tested on its recorded condition and REJECTED; the nyiso-127 execution record restored

**Keeper → `2026-08-30-nyiso-157-par-attribution`** (bundle
`results/calibration/nyiso157_pararm_B`), superseding
`2026-08-25-nyiso-155-hydro-repair`. Three solves, all registered (rule 15):
`2026-08-30-nyiso-157-par-control` (zero-delta), `-par-attribution` (the seam
arm), `-iroquois-companion` (rejected). Freeze ACTIVE; every solved year ∈
{2023, 2024, 2025}.

**(0) RECORD CORRECTION FIRST (EXECNOTE §1, pushed before any solve).** The
nyiso-156b §0 correction was itself incomplete: the seam lane was not merely
authorization-blocked — it was EXECUTED AND REJECTED at nyiso-127 on
2026-08-05 under an owner authorization given that day (PRs #3570 intake /
#3582 wiring / #3584 both solved arms / #3586 "REJECTED — kill gate K3
fires"; runs `2026-08-05-nyiso-127-{control,par-attribution}`, registered
then retention-pruned 2026-08-15 — the keeper shard's own site_retention_note
lists them). A session-number collision (the caiso-186 class) kept the
execution out of this log: the holdout-readiness sitting wrote the nyiso-127
entry ("NOT executed — owner-gated") before the authorization landed, and no
entry for the execution sitting was ever written. Handoff steps 1–2 (intake,
build) were therefore ALREADY DONE at HEAD; this session verified them
(zone_shares reproduces `_nyiso127_par_phase0.json` to 4dp) and re-tested.

**(1) THE RE-TEST IS LICENSED, NOT RE-LITIGATED.** DO-NOT-REDO on the R cell
is satisfied by (a) the 2026-08-30 owner ruling itself (postdates the R,
orders exactly this execution), and (b) the moved baseline: the nyiso-128/129
solar-basis repair moved the exact quantity K3 fired on (ST_GAS volume), and
the nyiso-125-era HEAD stopped reproducing one day after the rejection.
Measured this session: **K3 does NOT re-fire** — C1 14/14 · free 10/10 on
BOTH arms.

**(2) THE A/B (standing preregs nyiso-126 + nyiso-127 addenda; K6
re-specified per EXECNOTE §3).** Control BIT-IDENTICAL to the committed
keeper in zonal prices in all three years (max |Δprice| 0.0 — no G1 drift;
K6 passes exactly: C3a +6.81/−1.74/−10.82 vs committed +6.8/−1.7/−10.8).
Every standing kill gate SILENT (K1–K9; two scorer-instrument artifacts
corrected and documented in `_nyiso157_par_ab_gates.json`: the K1
dual-channel echo of the single `--set` flag, and a session-authored K5
conservation leg that penalized the arm for landing CLOSER to the measured
EIA-930 annual net than the control — the prereg-text K5 passes). LOYO
consistent, no flips. **P1 CONFIRMED**: external>Capital_Hudson
permanently-bound share 1.000 → 0.596 (2025), CE utilisation 0.381 → 0.784
vs measured 0.591 (overshoot reported: 2023 0.975 vs 0.807); the model's
first real zonal separation — Jan+Feb-2025 CH−UW binding hours 34 → 435,
NYC−UW winter gradient 0.24 → 4.60 $/MWh vs measured 14.83. **P3 CONFIRMED**:
C3a-2025 −10.8 → −12.0 % (the seam alone was never predicted to close it).
C3a-2023 +6.8 → **+1.0 %**; 2024 −1.7 → −2.0. **Reported against interest:**
C3b-2025 monthly NRMSE 0.1973 → 0.2034 crosses the 0.20 bar (the control
itself sits 0.0027 under it) — a NEW load-bearing knife-edge FAIL. C3c
bit-identical 1/0/0 h. Zero new failing D-rows (the three FAIL D-4 rows are
the keeper's own).

**(3) PROMOTION BY OWNER RULING (in-session, verbatim: "Is this a
recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper..").** Recommended and
promoted on rules 14+1: measured attribution over hand statics, zero free
parameters (+1 DOF entry, 0 scalars, n_residual 6; attested, C6 PASS).
Determination **NOT-YET on {C3a, C3b, C3c}, written explicitly on the
ruling** (D-5(b) resolved by it — the nyiso-120/155 precedent class; the
worse basis is never silently written). `calibration-complete.json` re-keyed
with the re-verified determination; `audit_keepers --iso NYISO` PASS 0/0
(E11 recipe delta declared: exactly `nyiso_seam_par_attribution`
False→True through both recording channels). The deepened 2025 miss is the
winter face of the nyiso-156 two-face object measured on an honest seam —
the statics were masking part of it, exactly as rule 14 predicts.

**(4) THE COMPANION CHAIN RAN AND CLOSED.** The seam arm met nyiso-150's
recorded re-open condition (the cutset binds), so
`nyiso_iroquois_winter_spread` was re-tested as its pre-registered companion
(`PREREG-nyiso157-iroquois-companion-2026-08-30.md`, blob-verified BEFORE the
solve; nyiso-150 W-gates verbatim, control re-based to the seam arm) and
**REJECTED on its own gates** (`_nyiso157_iroq_gates.json`): W-K3a recovery
0.07–0.16 in Dec-2024/Feb-2025 vs ≥0.30 — while Feb-2023, where the cutset
binds ~98 % of winter hours, recovers 0.54–1.65. **The decisive measurement:
the fuel-side flag transmits exactly where the cutset binds HARD; 18–31 %
winter binding is not enough.** W-K3b annual gradient unmoved (3.71 → 3.67 vs
actual 14.83); W-K3c UW-2023 worsens; W-K3d relocation; W-K5 C1 PASS→FAIL.
Cell stays R with the re-open condition sharpened by measurement. **The
2024/2025 winter face needs more than seam+fuel: Leg 2 (the owner-executable
MyNYISO as-enforced AORR access, spec §2) is the remaining identified
route.** The EXECNOTE §5 conjunction's control-leg (<6 h) mis-modeled
"effectively none" (control binds 34 h); both readings reported.

Matrix: `nyiso_seam_par_attribution` R → **K** (nyiso-127 rejection record
preserved in the ev); `nyiso_iroquois_winter_spread` stays **R** (companion
outcome appended); `seam_flow_envelopes` K annotated superseded-at-runtime
(rule 19); shard keeper/gates stamps + §5.5 prose header re-stamped;
`check_mechanism_matrix` clean. Zero fitted scalars anywhere; hydro input
pair untouched (rule 14); no scarcity parameter (rule 19); C3c queue closed
(nyiso-137 clock caveat honoured — only arm-vs-control deltas read).

Next shorthand: nyiso-158.

## 2026-08-30 — nyiso-158: post-seam phase-0 — the binding-depth differential IS the measured Transco step, the sharpened iroquois re-open bar is UNREACHABLE BY ANY MEASURED DRIVER, C3b-2025 is WHOLLY the two faces, and the CE-util overshoot is NOT an envelope defect

**NO SOLVE.** Committed-artifacts-only diagnosis of the three rubric failures
on the nyiso-157 keeper (`2026-08-30-nyiso-157-par-attribution`, NOT-YET).
Records: `results/calibration/FINDING-nyiso158-winter-binding-depth-phase0-2026-08-30.md`
+ `_nyiso158_winter_phase0.json`. Zero fitted scalars; freeze ACTIVE; nothing
armed, disarmed, rescaled or scoped; no cell verdict moves (nothing tested —
one evidence append on the standing iroquois R, below).

**(1) The winter binding-depth differential decomposed.** The west base
surplus (nuclear+hydro+wind+attributed-UW-envelope−UW demand) is ~3.0–3.6 GW
in EVERY winter month of all three years — near-constant. What moved is the
denominator: the applied measured CE TTC steps 1,875–1,950 (Jan/Feb-2023) →
3,050–3,175 MW (object months), the NY Transco upgrade, +1,200–1,300 MW =
80–107 % of the headroom change alone (2025 hydro decline −290/−560 MW and
UW demand growth deepen it; envelope/wind offset part). Measured against
P-32's own conduct, **Feb-2023-like ~98 % binding does not exist in reality
anywhere**: real Feb-2023 sat ≥95 % of its limit only 14.6 % of hours (mean
util 0.904) — the model's 96–100 % is LP bang-bang saturation of the small
pre-Transco pipe — and the object months measure bind95 6.5–26.9 % vs the
keeper's 13.2–41.9 %, i.e. the keeper's object-month binding FREQUENCY is
inside the measured bracket. **Driver search verdict: NONE** — measured RT
limits would LOOSEN the object months (BLOCKER-C direction reproduced, not
re-opened), the measured seam envelope/hydro/demand all move the wrong way,
and reality itself is partial-binding. The sharpened re-open condition's
first leg is closed on measurement; the condition reduces to its second leg:
**Leg 2 (owner-executable AORR intake) is the only identified route to the
winter face.** Supporting: the companion dose-response (W-K3a recovery tracks
binding fraction 13 %→0.07–0.14 … 96–100 %→0.54–1.65) and Feb-2024 (the one
winter month with hourly LMP+P-32 on disk): ~96 % of the real CH−UW premium
mass forms OUTSIDE bind95 hours — a cutset-binding mechanism of any depth
cannot produce it.

**(2) C3b-2025 has no third component.** Scorer-exact reproduction (payload
pMon·dMon vs bench rt_lw_mon): arm 0.2034 / control 0.1973 to the digit. The
four face months carry **98.4 %** of the squared error (Jan 27.3 / Feb 25.7 /
Jun 35.6 / Jul 9.8; the other eight months 1.6 % combined, max |err| $3.4).
Month-replacement counterfactuals: winter face closed → 0.1394, summer face
closed → 0.1503, both → 0.0255 — **either adjudicated face alone returns
C3b-2025 under the 0.20 bar**. The arm's knife-edge crossing is the same two
faces deepening ~$1–2/month; no new month enters. C3b closes with the faces
and needs no lever of its own.

**(3) The CE-utilisation overshoot (0.975/0.763/0.784 vs 0.807/0.616/0.591)
is NOT an identification defect in the attributed UW envelope.** The measured
object reproduces exactly (median hourly flow/limit; complete P-32 sample, no
availability conditioning; K7 shares to 4dp; the p90×(month×hod) caps track
realized p90 faithfully). Decomposition: denominator artifact small
(0.053/0.008/0.009 — monthly-mean DAM TTC vs hourly RT limits); the numerator
is the object — the LP moves +355/+439/+577 MW more across CE at the median
than the measured interface, from (a) LP pinning with zero operating margin
(reality bind98 ≤1.5 % in every month; model-class family of the ledgered
C3c), (b) placement freedom under the EIA-930-pinned monthly total, and
(c) **missing east-side commitment — the BLOCKER-B/Leg-2 object seen from the
flow side**. PREREG-nyiso126 §8-3 honoured: nothing rescaled, nothing scoped,
no mechanism proposed from this residual.

Matrix: `nyiso_iroquois_winter_spread` stays **R** — evidence appended to the
cell (first re-open leg closed on measurement; condition now effectively
Leg-2-only). No other cell touched. Keeper, determination, frontier
disposition all unchanged. Leg 2 remains owner-court; if the AORR files land,
the nyiso-97 §4 identifiability gate runs BEFORE any mechanism prereg
(INTAKE-SPEC-nyiso156 §2, fail-closed).

Next shorthand: nyiso-159.

## 2026-08-30 — Q5-W: the `complete` marker WITHDRAWN by owner r#12 ruling (CAISO precedent, uniform) — keeper nyiso-157 UNTOUCHED; records lane, no solve

**What moved and what did not.** The owner re-ruled Q5 at the capx director's
refresh-#12 decision card (verbatim option label: *"Withdraw the marker (CAISO
precedent)"*, superseding the r#8 WAIT; `capx-director-ledger-2026-08.md`
§0i.2/§3 Q5): NYISO's `complete` marker is **withdrawn** — a `complete` marker
cannot stand on a NOT-YET keeper, applied uniformly — while
**`2026-08-30-nyiso-157-par-attribution` REMAINS the designated keeper**. The
structural-integrity formula still governs keeper promotions (nyiso-155/157
stand); it no longer sustains a marker. Trigger: the recurrence — nyiso-157
re-keyed the marker onto a second consecutive NOT-YET keeper with the fail set
widened ({C3a-2025 −12.0 %, C3b-2025 0.203, C3c silenced-lone}).

**The record** (form mirrors the CAISO 2026-08-06 withdrawal):
`calibration-complete.json` `withdrawn.NYISO` — declared 2026-07-31, withdrawn
2026-08-30, keeper_at_declaration nyiso-100-silretire preserved, the 11-entry
`rekey_history` and the prior 2026-07-19 withdrawal nested verbatim, nothing
erased. **Nothing was ever spent** (verified: all 15 NYISO sidecars ⊂
{2023, 2024, 2025}; bench 2023–2025 only), so nothing is lost; the
validation-tier (2020–2022) authorization **lapses** with the marker
(`holdout_policy.authorized(NYISO, 2022)` → False, verified), the locked test
was never authorized, `holdout-freeze.json` untouched. Forecast board flipped in
the same session: gate **(a) fail on the marker · (b) PASS (untouched bare
verdict) · (c) fail · (d) none** — the lead position is dissolved.

**Re-entry** is a NEW explicit owner declaration once the keeper again scores
CALIBRATED — the live route is this lane's own successor, **winter intake Leg 2**
(`INTAKE-SPEC-nyiso156-winter-locational-2026-08-30`, owner-executable AORR
access; intake needs no marker and is unaffected). `audit_keepers` clean. Full
record: `docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md`; cross-ISO
entry: `governance.md` 2026-08-30.

Next shorthand: nyiso-159 (unchanged from the nyiso-158 entry above — Q5-W
is a governance lane, not an nyiso-N session).

## 2026-08-30 — nyiso-159 (execution): the zonal loss surface DERIVED, ARMED and PROMOTED by owner ruling — load-bearing C3b RETURNS TO PASS, the fail set narrows to {C3a-2025, C3c}

Executes `PREREG-nyiso159-zonal-loss-surface-2026-08-30.md` (filed with the
phase-0 finding by this session's earlier commit, PR #4352). Zero fitted
scalars end to end; freeze ACTIVE (2023–2025 only). Records:
`scripts/data/derive_nyiso_loss_surface.py` (frozen rule 23) →
`data/raw/iso-specific-transmission/NYISO_loss_surface.csv`;
`scripts/probes/_nyiso159_loss_ab_gates.py` → `_nyiso159_loss_ab_gates.json`;
runs `2026-08-30-nyiso-159-loss-control` / `2026-08-30-nyiso-159-loss-surface`
(bundles `nyiso159_lossctl_A` / `nyiso159_lossarm_B`);
`scripts/gen_nyiso159_attestation.py`.

**(1) Identification and offline acceptance (§2–§3).** The 36-month RT
component record re-staged byte-identically to the phase-0 record
(8,759/8,783/8,757 usable hours; E-identity max $0.0150 vs the $0.02
publication-rounding bound). The derive reproduces the committed phase-0 dev
surface to 6 dp, and the §3 acceptance gate held **12/12 pair-years in
[0.5×, 1.5×]** (ratios 0.93–1.02×) before any solve was spent.

**(2) Mechanism.** `ScenarioConfig.nyiso_zonal_loss_surface` (default off,
registered at introduction — pinned default key `603c2498bf71d21d` unmoved),
step 10 of the interchange transform ladder
(`interchange.nyiso.apply_nyiso_zonal_loss_links` + `build_nyiso_link_loss`),
`NYISO_LOSS_LINK_TIEBREAK_EPS = 1e-3` (the rule-9 ε class, declared in
NYISO's own module per rule 25). Unit suite 12/12
(`tests/iso/nyiso/test_nyiso_zonal_loss_surface.py`); NYISO directory sweep
242 passed.

**(3) The A/B (§4–§5).** Control replays the keeper **bit-identically**
(max zonal |Δprice| 0.0 in all three years — K5/K6 at zero distance). Gates:
K1/K2/K6/ADVERSE **PASS**; **P1 10/12 pair-years in band** — meeting the ≥10
bar — with ONE outer miss (0.23× vs the 0.25 floor) on the
smallest-denominator pair (NYC→LI 2024, measured ΔMCL $0.19/MWh, where the
measured July gradient flip clamps the fraction and the 1,650 MW cable's
congestion dominates); LOYO breaks only through that same cell. **W-K3d fires
on magnitude** (UW annual mean −1.22/−1.71 $ in 2024/2025 vs the 0.75 bound)
and is adjudicated against its own premise by the actual-anchored
decomposition (`WK3d_actual_anchor`): the arm moves UW **toward** the
measured relative gradient in both years (UW-below-LW 6.6→10.5 % vs measured
13.3 % in 2024; 8.8→12.2 % vs measured 16.4 % in 2025) and 2024's absolute UW
error improves ($1.86→$0.64) — in unbound hours the lossless LP's east–west
parity WAS the bias the phase-0 premise ("UW's dual is set by its own
balance") assumed away. Reported at full magnitude, never patched.

**(4) Effect and promotion.** C3a +1.00→+2.35 / −1.96→−1.21 / −12.01→−11.48
(2025 uplift +$0.36 LW, below the phase-0 upper bound because the surface
moves west zones down as it moves downstate up — the LW-weighted net is
smaller than the downstate-only bound). **Load-bearing C3b returns to PASS**
— the 0.203 knife-edge the nyiso-157 promotion accepted is recovered
(probe-basis NRMSE 0.2268→0.2224). C3c deltas only (not lone — C3a also
fails — so the standing rule stays silent and both stand). Determination
verified from committed artifacts (`calibration_verdict --run-id`):
**NOT-YET on {C3a-2025 −11.5 %, C3c}** — strictly narrower than the
superseded keeper's {C3a, C3b, C3c}; not worse, so D-5(b) does not stop it
(and NYISO holds no `complete` marker since Q5-W). **OWNER RULED PROMOTE**
(in-session, the standing-disposition formula of nyiso-155/157): keeper →
`2026-08-30-nyiso-159-loss-surface`. `audit_keepers --iso NYISO` PASS 0/0.
Matrix: `zonal_loss_surface` NYISO cell `·` → **K**; keeper + gates stamps
and the §5.5 prose header re-stamped.

**(5) What stays open, unchanged.** C3a-2025's faces stay routed exactly as
nyiso-158 adjudicated: the winter face to **Leg 2** (the owner-executable
AORR intake, `INTAKE-SPEC-nyiso156` §2 identifiability gate first,
fail-closed) and the summer face to the ledgered model-class C3c. The loss
surface is the restored measured FLOOR, not object-month work; no cutset,
TTC, seam or C3c parameter moved.

Next shorthand: nyiso-160.

## 2026-08-30 — nyiso-160: Leg 2 (the MyNYISO AORR intake) STOPPED WITH CAUSE at access — the winter face is identification-blocked on both legs; the touchpoint-prep audit run in its place proves the keeper replays BIT-IDENTICALLY at HEAD

Executes the Leg-2 charter (`INTAKE-SPEC-nyiso156-winter-locational-2026-08-30`
§2) to its Step-1 gate and stops there, exactly as the handoff pre-committed.
Records: `results/calibration/FINDING-nyiso160-leg2-stop-and-tpaudit-2026-08-30.md`;
`scripts/probes/_nyiso160_tpaudit.py` → `_nyiso160_tpaudit.json`;
run `2026-08-30-nyiso-160-tpaudit-replay` (bundle `nyiso160_tpaudit_replay`);
`scripts/gen_nyiso160_attestation.py`. Freeze ACTIVE (2023–2025 only, no
`--holdout-authorized` — NYISO holds no `complete` marker since Q5-W).

**(1) The stop.** The AORR artifacts had not landed in `data/raw` (verified:
none anywhere in tree or history), and the owner, asked in-session, answered
**"Cannot produce them"** (no MyNYISO access). The leg closes at ACCESS — the
nyiso-97 stop-if-walled class; the §2 identifiability gate never ran because
its input never existed, so the stop record stands in place of a gate verdict.
NO substitute winter mechanism invented (nyiso-158 §1.4 measured that no
admissible driver reaches the winter face; the nyiso-97 §5 re-open bar binds
verbatim through the spec). With Leg 1 executed (nyiso-157) and its companion
chain closed on measurement (nyiso-158), **the winter face of C3a-2025 is now
identification-blocked on both legs**; the summer face stays the ledgered
model-class C3c. Determination consequence: none — the keeper already reads
NOT-YET on exactly {C3a-2025 −11.5%, C3c}. Re-open = the nyiso-97 conditions
only (public AORR posting restored / FERC-PSC docket / owner-supplied access
whose rows carry derivable parameters, gate first, fail-closed). Matrix:
no cell verdict moves (nothing tested); `scuc_load_pocket_commitment` stays
**G** with this stop appended to its evidence; §5.5 carries the dated
annotation.

**(2) The audit (the handoff's designated fallback).** Zero-delta replay of
keeper `2026-08-30-nyiso-159-loss-surface` at HEAD (`replay_keeper.py`, years
2023 2024 2025 sequential, no `--set`), audited by the committed-bytes probe:
**A1** max abs divergence **0.0** on every hourly-sidecar value column, all
three years (max zonal |Δprice| 0.0 ×3); **A2** C3a +2.35/−1.21/−11.48 vs
committed +2.35/−1.21/−11.48 (Δ 0.00 pp; lw-λ identical to 4 dp); **A3** zero
differing levers — the two differing recorded keys
(`entry_forward_reserve_leg`, `ercot_offer_surface_cleared_share_rt_room`)
are post-recording rule-24 schema growth at registered default `False`,
proven inert by A1 (adjudicated fail-closed against the live ScenarioConfig
defaults, never hardcoded). Legitimacy diagnostics regenerate gate-identical.
**Verdict: NO G1-class drift** (contrast nyiso-155 §4) — the touchpoint-prep
condition (recipe frozen, reproducible at HEAD, nothing left to prepare) is
SATISFIED. Environment note: the audit's only repairs were disposable
`data/clean` regenerations (capacity-deliverability, nyiso-interface-flows
fail loudly when absent — the clean-tree contract working, not drift).

**(3) Posture.** Keeper UNCHANGED; nothing armed, disarmed or re-tuned; the
loss-surface derive stays frozen (rule 23); the replay run is registered as
an audit probe (rule 15; retention pruned `2026-08-22-nyiso-149-basis-probe`)
and is NEVER a keeper candidate — it is the keeper itself, re-established at
HEAD. The lane's live route to CALIBRATED remains exactly the nyiso-158/159
routing: the winter face waits on an identification source that now requires
a nyiso-97 re-open event; the summer face is the ledgered C3c.

Next shorthand: nyiso-161.

## 2026-08-31 — nyiso-162: owner ruling R-C EXECUTED — the "parked leg2 winter-locational candidate" RE-VERIFIED against the live keeper: NO candidate exists, and the object that does scores IDENTICALLY to keeper 159 on every criterion, every year (zero solve)

Executes owner ruling **R-C** (2026-08-31 director sitting: *re-verify the
parked leg2 candidate against the LIVE keeper before any promote-or-archive is
served; nothing promotes on a stale comparison*). Zero-solve, committed
artifacts only (the Card-3 standing-rule pattern). Record:
`docs/FINDING-nyiso-leg2-reverify-2026-08-31.md`. **Keeper, shard, marker,
determination and matrix all UNTOUCHED; this lane rules nothing.**

**(1) There is no candidate.** The named session is **nyiso-160** (branch
`claude/nyiso-leg2-winter-locational-wymoa4`, #4385 + #4393 — both merged, the
remote branch deleted, nothing unmerged). Leg 2 stopped with cause **at
ACCESS, at Step 1, before any mechanism was designed**: no prereg, no armed
field, no `--set`, no derive, **no A/B pair and no control run**. Its sole
registered run is `2026-08-30-nyiso-160-tpaudit-replay` — a zero-delta HEAD
replay of the keeper's own recipe, registered under rule 15 as an audit probe
and declared in its own records *"NEVER a keeper candidate."* What is parked is
a **disposition question about an audit registration**, not a promotion
question about a mechanism.

**(2) The re-verification (four independent legs, no LP solve, all years
in-training).** Against the live keeper `2026-08-30-nyiso-159-loss-surface`
(`audit_keepers --iso NYISO` PASS 0/0 at this head): **R1 scorecard** —
`calibration_verdict --json` on both, 60 records each, diffed on status /
model / actual / magnitude / classification / share_pp → **ZERO record-level
differences**; `reasons`, `caveats`, `ledger_entries`, `grade_summary`,
`free_class_score` identical objects; the only difference anywhere is the C6
attestation **prose**. **R2 recipe** — recursive flatten of both
`run_config.json` (978/981 leaves), volatile provenance excluded → **0
solve-affecting levers differ**; 0 keeper-only leaves; 3 candidate-only leaves
(`entry_forward_reserve_leg` False, `ercot_offer_surface_cleared_share_rt_room`
False, `..._path` None — registered ScenarioConfig defaults, rule-24 schema
growth, all ERCOT/entry-side with no NYISO reach). **R3 hourly** — decoded
value comparison of every value column of every sidecar, all three years:
**max |Δ| = 0 over 1,043,280 rows**, label columns matching element-wise.
**R4 `metrics.json`** — 58/60 leaves identical, the 2 differing being `run_id`
and `label`.

*Two corrections to the nyiso-160 record, neither material to its verdict:*
it named **two** post-recording schema-growth keys where there are **three**
(it omitted `ercot_offer_surface_cleared_share_rt_room_path`); and the two
bundles also differ in **package versions incl. HiGHS 1.15.1 vs 1.14.0**
(plus pandas/pyarrow/pydantic) — unreported there, and *strengthening*: the
value-identity held across a solver-version change. Note also that the parquet
**files** are not byte-identical (equal sizes, differing hashes — the writer
version string in the footer), so the identity claim rests on the decoded
value comparison, not on hashes.

**(3) The verdict: neither improvement, regression, nor mixed — exact
equality.** C1 all 14/14 free 10/10; C2 PASS; **C3a +2.3 / −1.2 / −11.5 %**;
C3b NRMSE 0.114 / 0.174 / 0.198; **C3c 1/0/1 h vs actual 10/13/42 h > $300**;
C4 gas r 0.938 / 0.904 / 0.842; C6 PASS; C8 PASS; determination **NOT-YET on
{C3a-2025, C3c}** — **identical on both runs, Δ = 0 everywhere**. The equality
is structural: the run cannot improve or worsen the keeper's scorecard because
it *is* the keeper's recipe and dispatch, re-established at HEAD. For the
owner's decision (not made here): promotion would be a formal no-op that swaps
the nyiso-159 A/B promotion basis for a replay with no control and no
mechanism; archiving costs nothing evidentially (the audit verdict is durable
in `_nyiso160_tpaudit.json`, the nyiso-160 finding, this log and the R-C
finding); the genuine open choice is **dashboard retention, not promotion**.

**(4) R-C's premise, checked.** The ruling's trigger — *the candidate's
baseline is superseded by the 157 → 159 promotion* — **does not hold for this
session**: 157 → 159 happened at **nyiso-159, the session before leg2**, and
nyiso-160 audited **against 159 throughout** (its own finding header names 159
as the keeper under audit). The keeper has not moved since; nyiso-161 (#4420,
the winter-face waiver decision card) is records-only. The ruling is executed
in full regardless and returns a **null candidate on a baseline that was
already current**; §3's measurement is fresh at today's head either way.

**(5) Matrix.** No cell moves — rule 26 duty (b) is not triggered, because the
object carries no mechanism to adjudicate. `scuc_load_pocket_commitment` stays
**G** with the nyiso-160 access-stop already on its evidence line; duty (c)
not triggered (no new `ScenarioConfig` field).

Next shorthand: nyiso-163.

## 2026-08-31 — nyiso-163: the Leg-2 access route VERIFIED and sharpened, the on-receipt identifiability gate BUILT AND VALIDATED before use, and the nyiso-97 verdict RE-CONFIRMED at IN-SPAN vintage from a PUBLIC source (zero solve)

Access-retry + harness lane. Zero solve, committed artifacts and public
documents only. Record:
`docs/FINDING-nyiso163-aorr-access-and-gate-2026-08-31.md`. **Keeper, shard,
marker, frontier, determination and matrix all UNTOUCHED; this session rules
nothing and promotes nothing.** State re-verified in-session, not taken on
trust: `calibration_verdict --run-id 2026-08-30-nyiso-159-loss-surface` →
**NOT-YET on exactly {C3a-2025 −11.5 %, C3c}** (C3c not lone, so the rule-22
standing rule stays silent and both failures stand); `audit_keepers --iso
NYISO` → **PASS 0/0**. `DECISION-CARD-nyiso161` is **FILED AND UNDECIDED** (no
ruling commit after `d8b0ea8`), so this proceeds under its §6: the MyNYISO
stakeholder route needs no ruling.

**(1) The access route holds and is MORE CONCRETE than nyiso-161 recorded.**
The Salesforce article is a JS shell that returns only a "CSS Error" placeholder
to a non-browser fetch and could not be read directly; the route was confirmed
from NYISO's indexed content and the form itself. The correction that matters:
the **CEII/NDA form IS the account application, not a contingency** — nyiso-161
had it as conditional ("if the table is CEII-classed"). Actual path: submit the
CEII Request Form + NDA (`nyiso.com/public/webdocs/markets_operations/services/
customer_relations/CEII_Request_Form/CEII_Request_Form_and_NDA_complete.pdf`)
selecting the "MyNYISO.com UserID and Password" option → NYISO **Legal** review →
on approval, a link to apply for the account → access to the secure sections
where Operating Committee/Planning documents reside. Contacts:
`stakeholder_services@nyiso.com` / 518.356.6060;
`customer_registration@nyiso.com` / 518.356.6060 opt 3. Eligibility to
**stakeholders**, not only market participants, confirmed. A single ready-to-send
request is in the finding §2.1, naming the INTAKE-SPEC §2 list (a)–(c) by the
**current** identifiers plus a new item (d), each with its usability test stated
so a partial fetch is caught at the counter.

**(2) The gate is built, and it was built BEFORE any current-vintage rows were
read** — deliberate ordering, recorded, because it is what makes §3 an
application of a pre-committed test rather than one shaped around its input.
`scripts/probes/_nyiso163_aorr_gate.py`: seven fail-closed tests (T0 vintage,
T1 Zone-J pocket, T2 MW/min-units, T3 eligible unit set, T4 observable trigger,
T5 rule-13 forward story, T6 provenance), PASS iff ≥1 row passes all seven.
Every test defaults to failure; a missing field, null, unparseable number,
unrecognised enum, empty input or raising test is a FAIL, never a skip. **The
anti-inference guard is the substance:** each of the three quantities must carry
a `quote` that is a **verbatim substring of the row's own published text**, so a
number absent from the document cannot pass — rule 13 enforced by the program
rather than by a future session's diligence. `derivation_basis` additionally
hard-fails conduct / BPCG / make-whole / LBMP / residual / inference **by name**
(the nyiso-97 §5 bar). Exit 0=PASS, 2=FAIL, 3=unreadable (distinct, so a
transcription error is never misread as an adjudication).

**(3) Validation — three legs, all required, all passing** (`--self-test`
exit 0; `results/calibration/_nyiso163_gate_acceptance_negcontrol.json`).
**Leg 1 negative control:** the public 2008 Appendix B → **FAIL**, and row by
row for nyiso-97's own reasons, not one blanket cause: LRR 1 {T0,T2,T3,T4,T5},
LRR 2 {T0,T2,T4,T5}, **LRR 3 {T0 ONLY}**, ARR 37 {T0,T2,T3,T4,T5}, ARR 66
{T0,T2,T4,T5}, ARR 28 {T0,T1}. The fixture encodes each row **as generously as
the published text honestly allows** — a control that withheld quantities would
prove nothing. **LRR 3 failing on vintage alone is the informative result:** it
is the one 2008 row carrying a load threshold, a min-units count and an
enumerated unit set, so its current-vintage successor is the likeliest to clear.
**Leg 2 discrimination:** a synthetic identifying row → **PASS**, without which
leg 1 would be worthless (a constant-FAIL function also "fails" the control).
**Leg 3 fail-closed:** 7/7 adversarial cases FAIL, including a fully-specified
row whose parameter is **not quotable** from its own text, and one with
`derivation_basis: residual`.

**(4) UNPLANNED AND THE REAL EVIDENTIARY GAIN — nyiso-97 RE-CONFIRMED at
IN-SPAN vintage from a PUBLIC source.** Verifying the access route surfaced the
**current Manual 12 (issued July 2026)**, whose Attachment B splits the former
Appendix B in a way nyiso-97 did not have: **Table B.5 (ARR/AORR) →
`nyiso.com/reports-information`, still walled**; but **Table B.4 (Local
Reliability Rules) → the NYSRC Reliability Rules — PUBLIC** (the URL Manual 12
prints is 404; live successor
`nysrc.org/documents/nysrc-reliability-rules-compliance-monitoring/`). nyiso-97
§2 checked NYSRC for an **AORR** posting and correctly found none — the **LRR**
half lives there, in a different document. Rows fetched, transcribed
(`scripts/probes/_nyiso163_aorr_current_public_2026.json`) and run
(`results/calibration/_nyiso163_gate_current_public.json`) from **NYSRC RRC
Manual V48 (final, 7-17-2026) Section G**. **Vintage established from the
source's own Version History** — exactly what INTAKE-SPEC §2 item (c) demands of
a current snapshot: v46 (2022-06-10) in force at span start; v47 (2024-06-14)
changed only RR B.5/B.1/Tables B-1,B-3; v48 changed only RR A.2; **last Section-G
change v42 (2018-02-09)**. So the quoted G.1/G.2 text was in force for the whole
of 2023–2025. **VERDICT FAIL, 5 rows / 0 qualifying, and it fails on CONTENT** —
every row clears T0/T1/T6 and fails T2/T3/T4/T5. G.1 R2 — *"Unit commitment in
the New York City (NYC) zone shall be based on second contingency operation…"* —
**is the row the winter face would need**, in current force, and carries no MW,
no min-units, no unit set, no observable trigger. G.2 §D is decisive: *"There are
applications, approved by the NYISO for implementing this Reliability Rule, which
specify minimum oil burn requirements for select generators in New York City"* —
the public rules layer states **in terms** that the operative parameters live in
the **Applications**. **What this settles:** nyiso-97's blocker 2 ("the public
vintage is not the as-enforced rule") **no longer carries the verdict** — the
verdict now rests on blocker 1, content, at in-span vintage. **What it does NOT
settle: Leg 2 is NOT discharged** — the rules layer is not the artifact §2 asks
for (Applications are, per NYSRC §1.2.8, *"operating procedures"* — the SO3-18
class), so this is a FAIL on the wrong document. Only the walled Applications
table can close or open Leg 2; the gate stands ready unchanged.

**(5) One judgment call SURFACED rather than silently made — G.1 R3.2**
(*"A percentage of the ten (10) minute NYCA operating reserves equal to the ratio
of the NYC zone peak load to the statewide peak load…"*). The closest the public
layer comes to identifying, and the one place the verbatim-number requirement
does real work: it states a **derivation rule**, not a level — no MW in the text,
and the NYCA reserve it scales is set by another rule. Fails T2/T4. A session
holding the NYCA constant *could* re-encode it as derived — but it is a
**locational reserve** requirement, **not** the in-City **commitment** formation
the winter face needs, and arming it would be a reserve lever, which rule 19
`[R-ONE-MECH]` and the closed ledgered-C3c queue forbid. **Flagged for the owner;
nothing armed.**

**(6) A dead end pre-adjudicated so nobody re-walks it.**
`nyiso.com/documents/20142/3035389/A-B-References-2023.pdf` reads like an
"Appendix A–B" document; "A-B" is **Accounting and Billing** (Training Reference
v1.0, 11/18/2024). Useful for one fact — **LRR I-R3 & I-R5 (Min Oil Burn) are
LIVE settlement charge codes in 2023–2025** (MOB payment daily bill code 328, MOB
charge 839), so the obligation is enforced today and its requirement genuinely
exists to be requested — and barred for everything else: it carries only the
**make-whole OUTCOME**, which rule 13 and the §5 bar exclude as a requirement
substitute. **Do not mine it for parameters.**

**(7) The standing watch is RECORDED, not re-run** (finding §6): the three
nyiso-97 re-open conditions, the exact source that would satisfy each, last-checked
source+date, and a cadence. Condition 1 **not satisfied** (both NYISO URLs are JS
shells; the reachable public layer is the NYSRC rules, which fail on content;
NYSRC 2026 postings PRR 157/158/159/161 — no AORR restoration, per nyiso-161
2026-08-30). Condition 2 **not satisfied** (NY PSC 25-E-0764 planning-genre,
nyiso-161). Condition 3 **OPEN — the live leg**; route verified, request not yet
sent. New watch item: the **published MOB dual-fuel unit list** NYSRC G.2 R3
obliges the NYISO to publish, not locatable publicly as of 2026-08-31 — item (d)
of the request. Cadence: condition 1 quarterly or on a Manual 12 re-issue /
NYSRC version bump (the Version History is the cheapest single check); condition
2 opportunistically only, it has failed twice; condition 3 on the owner's word.
Three checks on 08-30 and a fourth on 08-31 is already past diminishing returns.

**(8) Not a keeper candidate, and nothing to register.** No run was produced —
zero solve, no mechanism, no prereg, no A/B, no control. Rule 15 is not triggered
(no run exists to register); rule 16 is not engaged (no solve years). No holdout
spend: the freeze is ACTIVE, NYISO holds **no** `complete` marker (withdrawn
2026-08-30, Q5-W) and is absent from `final`. **Matrix: NO cell moves** — rule 26
duty (b) is not triggered because no mechanism was tested;
`scuc_load_pocket_commitment` stays **G** and `diurnal_price_amplitude` stays
**G**; duty (c) not triggered (no new `ScenarioConfig` field). The §4 evidence
strengthens the existing `G` justification rather than changing the cell.

**Where the lane stands.** The winter face remains identification-blocked and the
determination remains **NOT-YET on {C3a-2025, C3c}**. What changed: the block is
now precisely located (parameters live in the Applications layer; the public
rules layer has been checked at in-span vintage and does not carry them), the
owner's action is one request, and the test that will adjudicate whatever comes
back is committed and pre-validated. If registration succeeds the leg resumes at
full speed; if the gate then returns FAIL on the real Applications rows, the leg
closes with cause a second time — a legitimate outcome, to be recorded
unrewritten.

Next shorthand: nyiso-164.

## 2026-08-31 — nyiso-163b: OWNER CLOSED the AORR access route PERMANENTLY; the nyiso-161 card left UNRULED; and the C3c lane RE-OPENED cross-ISO, where NYISO's own reserve timing CONTRADICTS the ledger it carries (zero solve)

Continuation of nyiso-163 under two in-session owner rulings. **Keeper, shard,
marker, determination and matrix all UNTOUCHED.**

**(1) OWNER RULING — the MyNYISO/AORR access request is KILLED.** Verbatim:
*"I'm not getting new data access so just kill that request on 1."* Leg 2 of
`INTAKE-SPEC-nyiso156` §2 is therefore **PERMANENTLY CLOSED BY OWNER DECISION**,
not stalled and not awaiting a fetch. The nyiso-163 access package (finding
§2.1) is **not to be sent**; it stays on the record as the specification of what
was foregone, never as a pending action. The winter face of C3a-2025 (−$3.92) is
now **permanently unidentifiable from obtainable data**: nyiso-158 §1.4 measured
that no admissible driver in the repo reaches it, nyiso-163 re-confirmed the
nyiso-97 content verdict at IN-SPAN vintage from the public NYSRC rules layer,
and the only identified route was the walled Applications table. The nyiso-97 §5
re-open conditions 1 and 2 remain live as passive watch items (finding §6);
condition 3 (owner-supplied access) is **withdrawn by the owner** and its watch
line is closed. The nyiso-163 gate (`scripts/probes/_nyiso163_aorr_gate.py`)
stays committed and validated — it now guards a route nobody is walking, which
is the correct end state for a pre-committed test whose input never arrives.

**(2) The nyiso-161 winter-face waiver card is UNRULED and STAYS OPEN.** Put to
the owner with the three options costed (A NOT-YET stands / B CWC / C
CALIBRATED), plus two findings the card itself does not carry: **B is dominated**
— marker re-entry requires CALIBRATED not CWC (Q5-W), so B pays the full
rubric-amendment and precedent cost and buys nothing downstream — and the
precedent surface is **not NYISO-only**, since CAISO's standing C3a residual has
both lever routes CEII-blocked (caiso-218/219) and would have an immediate claim
on any access-blocked caveat class. The owner ruled **neither A nor C**, electing
instead to open the C3c question. **NYISO's determination therefore stays NOT-YET
on {C3a-2025 −11.5 %, C3c} by default**, and the card remains filed and
undecided.

**(3) OWNER RULING — "Open c3c scarcity question."** Scoped and costed, zero
solve, in `docs/CHARTER-c3c-scarcity-program-2026-08-31.md`. The cross-ISO
measurement **falsifies the blanket framing** several ledgers carry ("an hourly
LP with $0 reserve offers cannot form the RT scarcity tail"): **PJM PASSES C3c
at 0.67/0.56/0.54× in the same LP, same solver, same code path**, while
CAISO and NEISO form 0.00× in every year. That spread is not one phenomenon.

**(4) THE NYISO-SPECIFIC FINDING — this lane's C3c caveat inherited a diagnosis
its own evidence does not support.** New measurement from the keeper's committed
`reserve_family_<year>.parquet` sidecars against
`actual_lmp_hourly_NYISO.parquet` (artifact
`results/calibration/_nyiso163b_c3c_reserve_timing.json`): **in 2025 the model
goes reserve-short in 24 hours and 20 of them (83 %) are hours reality priced
above $300**, covering 48 % of reality's 42-hour tail; 2023 is 5/20 overlapping
50 % of the actual tail; 2024 is 0/7. The overlapping hours are **June–July 2025
and September 2023 — the summer scarcity days that constitute C3a-2025's summer
face.** This is the OPPOSITE of the CAISO failure mode on which the cross-ISO
closure rests: caiso-144 §C/§D measured 1.6–10.5 GW of model reserve slack in
reality's tail hours and an overlay-to-reality overlap of 1/47, 0/35, 0/8.
**NYISO is short in the right hours; it cannot PRICE them.** Only the cheap
locational families ever bind (`nyc_10min_total`/`nyc_30min_total` $25/MW,
`seny_30min_total` $40/MW); the NYCA-level products (`nyca_10min_total` $750,
`nyca_10min_spin` $775, `east_10min_total` $775) **never bind in any hour of any
year**, capping the total available reserve adder at **$90** against an actual
tail mean of $505/$517/$659. The open question is therefore a **quantity**
question — was reality short at the NYCA level in those hours? — and explicitly
NOT a price knob: the $25/$40/$750/$775 values are SOM-published and cited in
`model/reserves/spec.py`, and raising one to reach a residual would be a fitted
scarcity adder (rule 13 `[R-MEASURED]`, rule 1 `[R-STRUCT]`) of exactly the kind
ERCOT had to remove at ercot-214/215 when its tail gains were measured to ride a
phantom AS-product shortfall-ramp channel.

**(5) The charter's ranked questions, both zero-solve, neither run here.** **Q1
(first):** audit PJM's reserve duals for the ercot-214 phantom signature — PJM
passes on duals to $187.90 with ZERO shortfall in every hour, and that audit has
never been run; if the channel is phantom, a CALIBRATED keeper rests on it, which
outranks everything else in the charter. **Q2 (only if Q1 returns REAL):** the
NYISO product-level question above, with an explicit kill gate — if reality shows
no NYCA-level shortage, NYISO's C3c ledger is CONFIRMED rather than corrected.
**Q3:** the probabilistic-RT-premium class is an ARCHITECTURE decision (it
collides with rules 4 `[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint), NOT a
calibration lane, and is not recommended as one.

**(6) DO-NOT-REDO restated for the next session** (rule 26): the naive "port
PJM's scarcity formation" program is dead on three records — CAISO closed on
model STATE (`energy_reserve_coopt` CAISO **I**, caiso-144: ≥854 MW family slack
in all 26,280 hours; backcast overlay refused on measurement, §D), ERCOT closed
on its exhaustion record plus the caught phantom, and MISO/NEISO ledgered to the
probabilistic-premium class. Cells adjudicated: `ordc_scarcity_overlay` CAISO K /
NEISO K / PJM G / MISO G / ERCOT R; `dynamic_reserve_requirements` NEISO R;
`reserve_deliverability_scoping` CAISO/PJM I.

**(7) Matrix.** NO cell moves — rule 26 duty (b) is not triggered: nothing was
tested, armed or adjudicated; §4's finding is a measurement on committed
artifacts, and the ledger-inheritance question it raises is routed to the
charter's Q2 rather than settled here. Duty (c) not triggered (no new
`ScenarioConfig` field).

Next shorthand: nyiso-164.

## 2026-09-01 — nyiso-164: charter Q2 ANSWERED ON MEASUREMENT — reality was NOT NYCA-short in its own price tail, the model is not either, and NYISO's C3c ledger is CONFIRMED on NYISO's own evidence (zero solve)

**Kill gate FIRES on BOTH pre-registered clauses. Determination unchanged; no
keeper, marker, shard or matrix cell moves.** Records:
`docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`, artifact
`results/calibration/_nyiso164_nyca_shortage_check.json`, probe
`scripts/probes/nyiso164_nyca_shortage_check.py`.

**(0) State verified at open and close** (committed artifacts, no solve):
`calibration_verdict.py --run-id 2026-08-30-nyiso-159-loss-surface` → **NOT-YET**
on {C3a-2025 −11.5 %, C3c}; `audit_keepers.py --iso NYISO` → **PASS 0/0**. NYISO
holds no `complete` marker and is absent from `final`; freeze respected, years
2023–2025 only. The nyiso-161 winter-face card stays filed and unruled; the AORR
access route stays permanently closed (nyiso-163b).

**(1) The question, and why it was a QUANTITY question.** nyiso-163b found the
keeper reserve-short *in* the hours reality priced above $300 (overlap 5/10,
0/13, 20/42) — the opposite of the CAISO measurement the cross-ISO C3c closure
rests on (caiso-144 §C/§D) — yet only the cheap locational families ever bind
(`nyc_10min_total`/`nyc_30min_total` $25, `seny_30min_total` $40; max $90/MWh of
adder against tail means $505/$517/$659), while every NYCA-level product never
binds. So: in reality's tail hours, was NYISO short at the **NYCA** level, or
only **locationally**?

**(2) Method — nested differencing on PUBLISHED reserve prices, one tier up from
the construction `spec.py` already uses.** NYISO's regions nest (NYCA ⊃ East F–K
⊃ SENY G–K ⊃ NYC J / LI K), so zones **A–E** (WEST, GENESE, CENTRL, NORTH,
MHK VL) — outside East/SENY/NYC/LI — price the **NYCA tier alone**. Source:
`data/raw/NYISO-AS/NYISO_as_rt_<year>.csv` (MIS RT AS clearing prices, in-repo,
nothing fetched), corroborated by the P-35 Real-Time Events feed's NYCA-wide
**reserve pick-up** declarations (`.../requirements/realtime-events/`). Reserve
prices are the VALIDATION TARGET only, never an input (rule 13 `[R-MEASURED]`).
**The construction validates itself:** A–E price identically to
**0.000000 $/MW** for all three products in all 26,280 hours.

**(3) A clock repair that changes the answer — worth carrying forward.**
`actual_lmp_hourly_NYISO.parquet` is on the model's fixed **standard-time**
8760 clock (`derive_actual_lmp._STD_TZ["NYISO"] = Etc/GMT+5`); the NYISO-AS and
event feeds are naive Eastern **prevailing** wall-clock. They differ by one hour
through the whole DST season, which is where every tail hour sits — a naive
positional join is an hour off and gives a materially wrong answer. Timestamps
are localized to `America/New_York` and re-indexed with the repo's own
`_std_hour_index`; an offset scan (−3…+3 h) peaks at **0** in every year
(2023 306.74 vs 65.61/131.97; 2024 254.62 vs 105.66/89.97; 2025 393.31 vs
307.00/302.35).

**(4) The headline measurement — and why the first reading of it was WRONG.**
Tail-hour NYCA-tier price means $306.74/$254.62/$393.31, with 10/11/41 of
10/13/42 tail hours ≥ $40 against an all-year baseline of only 67/45/181 of
8,760 hours. Read alone that looks like a correction. It is not: a nonzero
upstate price means the NYCA constraint **bound**, not that its **demand curve
activated**. Three separations, and all three say opportunity cost:
**(a) ceiling** — a reserve-holder's opportunity cost is bounded by LMP, an RCPF
price is not; the NYCA price exceeds the concurrent LMP in **0 of 65** tail
hours (median ratio 0.573/0.536/0.654, max 0.936);
**(b) quantization** — demand-curve pricing pins to rungs; tail-hour values are
**10/10, 13/13, 33/42** distinct with **one** exact rung hit in three years
(weakened by 5-min→hourly averaging, so reported not relied on alone);
**(c) the operator record** — a declared NYCA reserve pick-up covers **8 of 65**
tail hours (pick-ups are frequent, 35/40/26 a year, but are short contingency
responses spread across all months, not a tail phenomenon).
A stable ~0.5–0.65 × LMP ratio under a hard sub-LMP ceiling is the signature of
**energy** scarcity dragging reserve opportunity costs up — not a NYCA reserve
shortage the model fails to see.

**(5) The model side.** `nyca_10min_spin` / `nyca_10min_total` /
`nyca_30min_total` carry a **zero dual and zero ORDC shortfall in all 8,760
hours of every year** (26,280 total). Reserve-carrying thermal headroom in
reality's tail hours, **lower bound**: **5,078 / 3,915 / 2,986 MW** mean against
a 2,620 MW NYCA 30-minute requirement (min 0 in the tightest 2023/2025 hour,
where the bound is uninformative rather than tight). **Method note — the naive
headroom figure is wrong and was rejected mid-session:** summing per-class
*annual* peaks gives 26.1/26.5/30.3 GW, badly overstated because the peaks are
non-coincident (`oil` alone peaks at 11.1 GW on 1.26 TWh/yr in 2025, never with
the CC peak); the fleet's maximum **simultaneous** thermal output is
18.3/17.4/18.9 GW and that is what the bound uses. The rejected number is kept
in the artifact as `sum_of_class_peaks_mw_NOT_USED`.

**(6) THE REVERSAL, reported rather than buried** (the charter asked for this
explicitly). nyiso-163b's overlap measurement is not wrong; its *interpretation*
was. Split by tier the picture inverts: at the **locational** tier the model
binds in reality's tail hours and so does reality (positive NYC increment in
9/13/42 hours) — **agreement**, and the genuine difference from CAISO, whose
model had slack in every family; at the **system (NYCA)** tier neither the model
nor reality is short — **also agreement**, and that is the tier that would have
to be short for a system-wide price tail to be a reserve phenomenon. NYISO's
position IS closer to CAISO's than the timing overlap alone implied: it differs
on *which* tier binds and agrees on the tier that governs the residual.

**(7) Consequence — CONFIRM, and the lane closes.** The residual above the
model's $90 locational adder is **not a missing reserve product**. C3c stands as
a ledgered model-class limitation on **NYISO's own evidence** rather than by
inheritance from CAISO/MISO/ERCOT; the inheritance question is settled. Per the
charter a CONFIRM is the equally-valuable outcome, and no correction was reached
for. This does **not** close C3c and does **not** move C3a-2025.

**(8) Governance.** Zero solve, zero holdout spend, no mechanism/prereg/scalar/
`ScenarioConfig` field. A NYISO mechanism prereg would have required this gate
cleared **and** pjm-164 (charter Q1) returning REAL; the gate CONFIRMS, so the
route does not open. **No SOM-published RCPF value ($25/$40/$750/$775) is
proposed for change in any form, including as a sensitivity** — the ercot-214
failure that guard exists to prevent (rules 13 `[R-MEASURED]`, 1 `[R-STRUCT]`).
`docs/calibration-log/governance.md` deliberately untouched (pjm-164 may be
running in parallel; the cross-ISO synthesis is a later, separate step).

**(9) Limits.** Hourly averaging dilutes the quantization test (a); the headroom
figure is a lower bound and is 0 MW in the single tightest tail hour of 2023 and
2025; the NYCA 30-minute curve's 9 interior rungs are not enumerated in-repo
(model carries a single $750 step), so only $40/$750/$775 were testable; one
fall-back hour a year is lost to the AS feed's collapsed duplicate hour and one
spring-forward hour does not exist — neither carries a tail hour in 2023–2025.

**(10) Matrix.** **NO cell moves** — rule 26 duty (b) not triggered (nothing
tested, armed or adjudicated; this is a measurement on committed artifacts and
published raw), duty (c) not triggered (no new `ScenarioConfig` field).
DO-NOT-REDO honoured, none re-tested: `nyiso_ordc_measured_step_span` **K**,
`nyiso_li_locational_reserve` **K**, `nyiso_east_reserve_families` **I**,
`energy_reserve_coopt` **K**, `ordc_scarcity_overlay` NYISO **·**,
`scuc_load_pocket_commitment` **G**, `diurnal_price_amplitude` **G**. Newly
retired by this session (do not re-open without new evidence): arming a
NYCA-level family/requirement so the tail can price (refuted — reality's NYCA
tier was never on its demand curve); "the model lacks tail headroom" (refuted —
3.0–5.1 GW LB against a 2,620 MW requirement); "NYISO's C3c caveat is inherited
and unsupported by its own evidence" (answered — it is supported).

Next shorthand: nyiso-165.

## 2026-08-31 — OWNER RULINGS R-F and R-G (director REFRESH sitting): the nyiso-161 winter-face waiver card is DEFERRED with a dated re-serve trigger (and the trigger is ALREADY MET at this pin); nyiso-160/leg2 is CLOSED BY ARCHIVE, retiring the promote-or-archive item for good (records act; zero solve)

Two owner rulings from the 2026-08-31 director REFRESH sitting, recorded by the
dispatched audit-program rulings-records lane under the standing recorded
deviation (the director pushes nothing; records land through the lane; the owner
merges). **ZERO SOLVE; NYISO surfaces only (rule 25 `[R-ISO-SCOPE]`). Keeper,
shard, marker, determination, freeze and every matrix cell UNTOUCHED.** State
verified at the pin `d44446e0`: keeper **`2026-08-30-nyiso-159-loss-surface`**,
`audit_keepers.py` **PASS 0 failures / 0 warnings**, NYISO holds **no `complete`
marker** and is absent from `final`, years read are 2023–2025 only.

---

**RULING R-F — the nyiso-161 WINTER-FACE WAIVER CARD: DEFERRED, WITH A DATED
RE-SERVE TRIGGER.** **Neither option A (NOT-YET stands) nor option C (declare
CALIBRATED) is ruled.** The card **stays filed** and its state moves from
*open-undecided* to **PARKED — re-serve when the C3c program's Q1/Q2 report
lands.** The R-E lane's finding is the trigger; had Q1 returned **PHANTOM** the
re-serve would have happened **immediately on that finding** instead of waiting
for Q2.

**NYISO's determination is UNCHANGED and restated: NOT-YET on {C3a-2025
−11.5 %, C3c}.** Nothing about the deferral moves it in either direction.

**🟠 RE-DERIVED AT THIS PIN, NOT CARRIED FROM THE DISPATCH: THE TRIGGER IS
ALREADY SATISFIED.** The dispatch that produced this record described the C3c
Q1/Q2 report as pending. At `d44446e0` **both questions have already reported**,
and Q1 returned **REAL**, not PHANTOM:

* **Q1 = REAL** (pjm-164, #4456, `docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`,
  zero solve) — PJM's reserve-dual channel is **not** the ercot-214 phantom, so
  the determination-integrity branch does not open and no PJM card is owed.
* **Q2 = CONFIRM** (nyiso-164, #4459,
  `docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`, zero solve) — the
  pre-registered kill gate fires on **both** clauses and **NYISO's C3c ledger is
  CONFIRMED on NYISO's own evidence** rather than by inheritance from
  CAISO/MISO/ERCOT.

**So the card is PARKED-AND-RE-SERVABLE: servable at the next sitting, not
waiting on a report.** Recorded this way deliberately — recording it as "waiting"
would leave a later reader expecting a report that has already arrived. **The
deferral itself is not re-opened by this**: the owner deferred, and only the
owner un-defers. **This lane rules nothing and adjudicates neither option.**

**What the re-served card must be read with, unchanged since nyiso-163b.** The
**AORR access route is PERMANENTLY CLOSED by owner decision** (verbatim: *"I'm
not getting new data access so just kill that request on 1"*), so the winter face
of C3a-2025 (−$3.92) is **permanently unidentifiable from obtainable data** —
nyiso-158 §1.4 measured that no admissible driver in the repo reaches it, and
nyiso-163 re-confirmed the nyiso-97 content verdict at IN-SPAN vintage from the
public NYSRC rules layer. **nyiso-97 §5 re-open condition 3 (owner-supplied
access) is WITHDRAWN by the owner** and its watch line is closed; conditions 1
and 2 remain live passive watch items. **Option B (CALIBRATED-WITH-CAVEATS) is
dominated** — marker re-entry requires CALIBRATED, not CWC (Q5-W), so B pays the
full rubric-amendment and precedent cost and buys nothing downstream. **The
precedent surface is not NYISO-only**: CAISO's standing C3a residual has both
lever routes CEII-blocked (caiso-218/219) and would have an immediate claim on
any access-blocked caveat class.

---

**RULING R-G — nyiso-160 / leg2: CLOSED BY ARCHIVE.** On
`docs/FINDING-nyiso-leg2-reverify-2026-08-31.md` (nyiso-162, #4431, executing
owner ruling R-C zero-solve on committed artifacts only), the owner ruled
**archive**.

**The re-verification dissolved the question it was ordered to answer: THERE IS
NO CANDIDATE.** The leg2 session (nyiso-160) produced a **stop with cause at
access**, not an object — **no** pre-registration, **no** armed mechanism, **no**
`ScenarioConfig` field, **no** A/B pair and **no** control. Its sole registered
run, **`2026-08-30-nyiso-160-tpaudit-replay`**, is the keeper's own recipe
re-established at HEAD, and its own records already declared it *"NEVER a keeper
candidate — it is the keeper itself"*. Re-verified against the **live** keeper on
four independent legs at that session's pin:

* **R1 scorecard** — 60 scored records each; **ZERO record-level differences**.
  The single difference anywhere in either scorecard is the **C6 governance
  attestation narrative string**. `reasons`, `caveats`, `ledger_entries`,
  `grade_summary`, `free_class_score`, `scorable_years` and `data_blocked_years`
  are identical objects; determination **NOT-YET {C3a-2025, C3c}** on both.
* **R2 recipe** — **0 solve-affecting levers differ** (3 candidate-only leaves are
  post-keeper rule-24 surface widening at registered defaults, all ERCOT/entry-side
  with no NYISO reach).
* **R3 hourly sidecars** — **max |Δ| = 0 (exactly zero) over 1,043,280 data rows**,
  every label column matching element-wise. (The parquet *files* are not
  byte-identical — a pyarrow writer-version string in the footer — so the identity
  rests on the decoded value comparison, which is the load-bearing test.)
* **R4 `metrics.json`** — 60 leaves each, **58 identical**; the 2 that differ are
  `run_id` and `label`.

**The equality is structural, not coincidental** — it is the keeper's own recipe
and the keeper's own dispatch. Two strengthening details the re-verification
added: the value-identity held **across a solver-version change** (HiGHS 1.15.1
keeper vs 1.14.0 replay, plus pandas/pyarrow/pydantic differences), and the
ruling's stated staleness premise did **not** hold for this session — nyiso-160
opened with nyiso-159 already designated and audited against 159 throughout. The
re-verification stands on its own regardless, as a fresh measurement at head.

**Why archive is the right disposition, on that record.** Promotion would have
been a **formal no-op** — same config, same dispatch, same determination — that
**replaced** the keeper designation's evidentiary basis (the nyiso-159 A/B against
`2026-08-30-nyiso-159-loss-control`, with its prereg, gates JSON and promotion
note) with an audit replay that has **no control and tests no mechanism**: nothing
gained, promotion basis weakened. **Archiving costs nothing evidentially** — the
touchpoint-prep verdict is durable in `results/calibration/_nyiso160_tpaudit.json`,
the nyiso-160 finding, the nyiso-162 finding and the log entries, none of which
depend on the run staying registered.

**The parked session is already archived; this entry records the closure.** The
**registered runs and both findings stay on the record.** The
**promote-or-archive item is retired FOR GOOD** — it is not re-servable, because
the object it named does not exist as a candidate.

**No matrix cell moves** (rule 26 duty (b) not triggered — nothing was tested,
armed or adjudicated; duty (c) not triggered — no `ScenarioConfig` field added).
`scuc_load_pocket_commitment` stays **G**, already carrying the nyiso-160
access-stop on its evidence line.

---

**Governance and scope.** Both rulings are recorded cross-ISO in
`docs/calibration-log/governance.md` (the sitting's four-ruling entry, which also
carries R-D and R-E), and on the audit plan §8 ledger + board v17. **Zero solve,
zero holdout spend, zero rubric motion, no scorer change, no keeper/shard/marker/
determination/matrix movement in this ISO.**

**Next shorthand: nyiso-165.**

## 2026-08-31 — nyiso-165: charter Q2 re-executed in parallel, reached the OPPOSITE answer, and is WRONG — nyiso-164's CONFIRM reproduced exactly; two live defects found in a committed calibration reference (zero solve)

Executes Q2 of `docs/CHARTER-c3c-scarcity-program-2026-08-31.md` §5 under owner
ruling R-E. **Zero solve; committed artifacts and in-repo published data only; no
holdout year touched (2023–2025).** Keeper re-verified at open and close:
`2026-08-30-nyiso-159-loss-surface`, NOT-YET on {C3a-2025 −11.5 %, C3c}. Record:
`docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`.

**CONCESSION, up front. `nyiso-164` had already executed this question at HEAD and
returned CONFIRMED. This lane ran in parallel, reached the OPPOSITE answer
("reality WAS NYCA-short"), found their record afterwards, re-derived the
measurement independently from the raw CSVs, and REPRODUCED THEIR NUMBERS
EXACTLY** — NYCA-tier tail-hour mean **$306.74 / $254.62 / $393.31**, median
$248.22 / $239.96 / $403.74, max $761.73 / $552.89 / $1,101.85, and the ceiling
test **0 of 65**, ratio medians 0.573 / 0.536 / 0.654. **nyiso-164 is right; this
lane's first reading was wrong. The verdict is theirs and the kill gate FIRES.**

**(1) Why they are right.** A nonzero upstate (A–E) price means the NYCA
constraint *bound*, not that its demand curve *activated*. A reserve holder's
opportunity cost is bounded by LMP; an RCPF shortage price is not. The NYCA-tier
price **never exceeds the concurrent LMP in any of the 65 tail hours**, at a
stable ~0.54–0.65× — energy scarcity dragging reserve opportunity cost up, not a
reserve shortage the model misses. Independently confirmed here: A–E price
identically (max spread 0.000000 $/MW, all hours, all years), and the three NYCA
families carry zero dual and zero shortfall in all 26,280 hours with `held_mw` at
exactly the requirement.

**(2) How this lane got it wrong — TWO DEFECTS, BOTH IN A COMMITTED ARTIFACT.**
The first pass read `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`
(`nyca_reserve_adder`) instead of the raw CSVs, and reported 40/42 tail hours
NYCA-priced, 21/42 at ≥$750, tail mean $925. All wrong:
- **Defect A (aggregate, the substantive one).**
  `process_nyiso_as.py::build_reference` computes `stack = spin_10 + nonsync_10 +
  op_30`. NYISO's products are a **cumulative cascade**: `spin_10 ≥ nonsync_10 ≥
  op_30` holds in **100.0000 % of 289,344 rows** (all 11 zones, all three years),
  all three exactly equal in 82–84 %. A 10-min spinning MW earns `spin_10`, not
  the sum; summing triple-counts (exactly 3.0× in 28.1/73.2/79.1 % of priced
  hours). Worked case 2023-09-05 17:00 EDT WEST: true $661.77, summed $1,985.32.
  **This is what broke the ceiling test** — on the summed basis the "NYCA price"
  exceeds LMP in 46/65 hours at median 1.14–1.96; on the correct basis, 0/65.
- **Defect B (clock).** `build_reference` maps naive **prevailing** timestamps
  positionally onto the model's 8760 index while the model's NYISO clock is
  `Etc/GMT+5` — off by one hour in **5,710/8,760 h (65.2 %)**, where every tail
  hour sits. (nyiso-164 found and repaired this independently, their §3.)
- Verified in the file: the committed `nyca_reserve_adder` reproduces the naive
  positional SUM in **8,759/8,759 hours of every year**.

**(3) Blast radius of the defect — NO keeper, NO scored result, NO determination.**
The sole consumer is `derive_nyiso_rcpf_overlay.py`, the post-solve RCPF comparator
for co-opt-off runs; `nyiso_rcpf_enabled` is False by default and in the keeper,
and rule 19 makes enabling it alongside the armed `energy_reserve_coopt` a hard
error. **It is a trap for diagnostic sessions, not a defect in any result — and it
caught this one.** A repair is cheap and needs no fetch (`build_reference` reads
the committed per-year CSVs): take the cascade max, and localize prevailing →
`Etc/GMT+5` before indexing. **NOT done here** — zero-solve measurement charter,
and rewriting a committed calibration reference on the strength of the audit it
misled is scope creep. Filed for a data lane / owner grant (rule 14).

**(4) The probe is kept, marked.** `scripts/probes/c3c_q2_nyiso_nyca_shortage.py`
ships with a SUPERSEDED/DEFECTIVE docstring, prints a warning, and stamps a
`SUPERSEDED` key into `results/calibration/_c3c_q2_nyiso_nyca_shortage.json`. Cite
`scripts/probes/nyiso164_nyca_shortage_check.py` for the correct measurement.

**(5) nyiso-161 waiver card — stated, not ruled** (R-F: parked on this report, the
DIRECTOR re-serves). Our corrected result **strengthens** the card's
characterisation of its summer face. Had the first reading stood, the −$3.94
summer face would have been a published reserve-shortage quantity the model fails
to bind — a defect, contradicting the card's "the ledgered C3c limitation seen in
the mean". It does not stand: on the corrected measurement the summer face **is**
that ledgered limitation. Bears on the summer half only (the winter face's AORR
block is untouched); it is a statement about characterisation, not arithmetic,
caveat budget or the standing rule. **We rule nothing and change nothing.**

**(6) Matrix.** **No cell moves, no shard edited** — duty (b) not triggered
(nothing tested, armed or adjudicated), duty (c) not triggered. nyiso-164's
DO-NOT-REDO list is honoured and reinforced, not re-opened: "arming a NYCA-level
family/requirement so the tail can price" is now refuted twice, independently.

Next shorthand: nyiso-166.

## 2026-08-31 — nyiso-166: the committed RT-reserve calibration reference is REPAIRED — both defects fixed at source, all nine years regenerated, and the artifact now reproduces the measurement of record hour by hour (zero solve)

**Charter:** rule 14 `[R-ACCURATE]`. **Zero solve**, committed artifacts + committed
raw only. No holdout spend, no mechanism, no prereg, no scalar, no `ScenarioConfig`
field, no keeper/shard/marker/frontier/determination change, no RCPF value touched.
The nyiso-161 winter-face waiver card stays **FILED AND UNRULED**; `governance.md`
untouched. Full record: `docs/FINDING-nyiso166-as-reference-repair-2026-08-31.md`.

**(0) State verified first, and re-verified after.** Keeper
`2026-08-30-nyiso-159-loss-surface` → **NOT-YET** on exactly {C3a-2025 −11.5 %,
C3c 2023/24/25}; `audit_keepers.py --iso NYISO` → **PASS 0/0**. Both re-read
**identically** after the repair. NYISO holds no `complete` marker, is absent from
`final`, freeze active, {2023,2024,2025} only — all untouched.

**(1) Executed the repair nyiso-165 §3 filed.** `process_nyiso_as.py::build_reference`
carried two independent defects in every column and every year:
- **A — cascade summed.** `stack = spin_10 + nonsync_10 + op_30`. The products
  nest by duration, so the posted prices are **cumulative**: `spin_10 ≥
  nonsync_10 ≥ op_30` in **100.0000 %** of rows (96,360 / 96,624 / 96,360 rows,
  11 zones, 2023/24/25), all three exactly equal in 82.73 / 83.56 / 82.11 %. A
  10-min spinning MW earns `spin_10`, not the sum. **Now the cascade MAX.** The
  nested-**region** stacking (NYCA + East + SENY + NYC) is real and is already
  inside each posted zonal price — it is the **duration** products that are not
  additive.
- **B — naive positional clock.** The CSV's prevailing-Eastern `Time Stamp` was
  mapped positionally onto the model's std-time 8760 index; measured disagreement
  **5,712 / 8,760 h (65.2 %)** in each of the three years — the whole DST season,
  where the tail sits. **Now localized to `America/New_York` and re-indexed with
  the repo's own `derive_actual_lmp._std_hour_index` on `Etc/GMT+5`**, the same
  conversion nyiso-164 uses. Two side effects, both improvements: the per-year
  CSV's Jan-1-of-next-year boundary-spill row is now dropped (it had been folded
  onto hour 0), and the DST fall-back hour is honestly NaN (std 7393/7345/7321),
  matching nyiso-164's coverage exactly at 8,759 mapped hours.

Regenerated for **every year the artifact carries — 2018–2026**, not just the
training window (rule 22: data prep is unrestricted and applies consistently
across all years; only *looking at the answer* is the spend, and none was).

**(2) VALIDATION — the mandatory one, and it passes.** The repaired reference
reproduces `scripts/probes/nyiso164_nyca_shortage_check.py`, which measures the
same quantity from the raw CSVs by a *different* construction (min across A–E,
which price identically — max spread 0.000000 $/MW). NYCA tier in the C3c tail:
**mean $306.74 / $254.62 / $393.31, median $248.22 / $239.96 / $403.74, max
$761.73 / $552.89 / $1,101.85, ceiling test 0/65** — every figure matched. Beyond
the tier summaries: **hour-by-hour parity in both tiers, all 8,759 mapped hours ×
3 years, `allclose(rtol=1e-6, atol=1e-3)` with identical NaN patterns**; residual
is the reference's float32 storage (max |diff| 1.2e-4 on values to $2,568). The
probe re-run against the repaired tree returns a byte-identical JSON — it reads
raw, so it is genuinely independent.

**(3) Magnitude — levels overstated 1.8×–2.9×, incidence untouched.** 2023 NYCA
mean $2.20 → **$1.25** / NYC $6.37 → **$3.52**; 2024 $2.51 → **$1.02** / $7.64 →
**$3.59**; 2025 $10.99 → **$3.97** / $28.73 → **$11.69**. Hours >$0 are unchanged
(629/3,020; 338/3,082; 876/4,007→4,006). **The 2025 NYC max of $5,568 should have
been the tell** — above any attainable RCPF cascade; corrected to $2,146.50.

**(4) Blast radius re-confirmed nil.** Sole consumer
`derive_nyiso_rcpf_overlay.py`, and there it feeds **only printed validation
reports** — checked call-site by call-site; never the written overlay parquet,
never a parameter, never an LP. Which is why (0) re-reads identically.

**(5) Regression test + two secondary repairs in the same class.**
`tests/test_nyiso_as_reference_repair.py`, **9 tests passing**, pins the
cascade-monotonicity invariant, the cascade-MAX end-to-end behaviour on synthetic
CSVs, the std-clock identity (DST hour lands one hour earlier, winter hour
unmoved, >60 % disagreement on real data, index injective), and hourly parity
with nyiso-164; the data-backed half skips without the `nyiso` profile. Also:
`_actual_zone_reserve`'s raw-CSV **fallback re-implemented both defects** and is
**deleted** (rule 23 `[R-DELETE]` — a defective duplicate that still parses is a
re-armable wrong answer); and the emitted column order is now deterministic, so
the artifact is byte-reproducible (sha256 `60be007f…d0a52156`, identical across
two regenerations). Names and dtypes unchanged.

**(6) Records corrected.** `docs/nyiso-rcpf-overlay.md`'s "Measured validation"
section quoted the pre-repair levels; corrected, with a dated note that the
model-vs-measured mean comparisons earlier in that doc have a **superseded
measured side** (model side unchanged — the modelled adder is *closer* to the
measured level than those lines read). `scripts/probes/c3c_q2_nyiso_nyca_shortage.py`'s
superseded-marker is dated to this repair: re-run at HEAD it no longer reproduces
its own committed JSON (deliberately **not** re-run — that record stays the frozen
artifact of the false positive) and it stays superseded regardless, its verdict
having been wrong on the merits.

**(7) Matrix.** Duty (a) discharged against `mechanism-matrix/NYISO.js`: **no cell
moves, no shard edited** — a data-reference repair is not a mechanism, so duties
(b) and (c) are not triggered. `nyiso_ordc_measured_step_span` **K**,
`nyiso_li_locational_reserve` **K**, `nyiso_east_reserve_families` **I**,
`energy_reserve_coopt` **K**, `ordc_scarcity_overlay` **·** all stand. The
twice-refuted lines ("arm a NYCA-level family so the tail can price"; "the model
lacks tail headroom") are **reinforced, not re-opened** — the corrected reference
is exactly what nyiso-164 measured.

**(8) Honest EV.** No gate moved; C3a-2025 and C3c are untouched, and NYISO's
rubric-moving path stays owner-gated on the nyiso-161 card. What is delivered is a
committed measured input that is now correct, agrees with the measurement of record
by construction, is byte-reproducible, and is guarded by a test — and the removal of
a trap that had already walked one audit to the wrong answer.

Next shorthand: nyiso-167.

## 2026-09-01 — nyiso-167: C3a-2025 is NOT a year-specific miss — it is a year-invariant PRICE-RESPONSE GAIN of ~0.70, and 87 % of the "winter face" is that gain (zero solve)

**Object:** the single load-bearing rubric failure between NYISO and CALIBRATED —
**C3a mean LMP 2025, −11.5 %** on the keeper `2026-08-30-nyiso-159-loss-surface`.
**No solve, no LP, no `ScenarioConfig` field, no cell verdict, no keeper, no
shard verdict, no marker, no determination.** Rule 22: every year read is
2023/2024/2025; no marker requested; freeze untouched. Record:
`docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md`, probe
`scripts/probes/nyiso167_price_gain_attribution.py` →
`results/calibration/_nyiso167_price_gain_attribution.json`.

**(1) The attribution.** The keeper's price response over all 36 training months
is ONE stable affine law, read off the same `pMon`/`dMon` fields the scorer
weights: **model = 0.7032 × actual_RT + $11.03** (R² 0.910, resid sd $4.93) and
**0.7236 × actual_DA + $10.06** (R² 0.947, resid sd $3.80). Each year's own
monthly law reproduces that year's gated C3a mean to **$0.17 or better**
(0.7118/0.6550/0.6704 gains — they move by less than the fit's scatter while
the price level doubles). The same gain appears independently in the
price-vs-load decile gradient (**0.752 / 0.662 / 0.664**, R² ≥ 0.99, off the
keeper's own `system_<year>.parquet`) and in the gas passthrough slope (model
6.38 vs actual-DA 8.94 $/MWh per $/MMBtu → **0.714**).

**(2) Why 2025 fails and 2023/2024 pass — arithmetic, not physics.** With gain
< 1 the error is `(g−1)·A + c`, monotone in the year's price level, so C3a's
±10 % is cleared only for an annual actual mean inside **$27.79 … $56.03/MWh**.
2023 $32.25 ✓, 2024 $38.12 ✓, **2025 $66.43 — 19 % above the upper edge**. The
two passes are the crossover, not accuracy: three observations of one defect at
three price levels.

**(3) THE WINTER FACE IS NOT A COMPONENT — this answers the nyiso-161 card's own
eligibility test (a) NO AS WRITTEN.** Annual load-weighted contributions on the
gated RT basis: whole-year raw −$7.870 = law −$8.763 + residual **+$0.893**;
**winter face raw −$4.072 = law −$3.558 + residual −$0.514 (87.4 % is the
system-wide gain)**, and neither Jan-2025 nor Feb-2025 is an outlier off the
pooled law (z −0.32, −0.92). The card's test (a) says *"a component that merely
helps does not qualify"* — removing Jan+Feb does return the year to band, but
only by removing the two months where a level-dependent error is largest. On the
DA basis the winter share is 79.4 %. The **summer** face behaves exactly as its
ledger says: on DA it has no residual at all (June model $52.80 vs DA $53.12,
−0.6 %), and on RT June is the **one** genuine 2025 outlier (z −2.71) — the
ledgered C3c limitation, which also proves the probe detects a real separate
component when one exists. **This rules nothing: the nyiso-161 card stays FILED
AND UNRULED and this is evidence for the owner**, who should also weigh that the
AORR intake could not have closed C3a-2025 alone — the **upstate** passthrough
leg (0.799, on 34 % of ISO load) is outside any in-city mechanism's reach.

**(4) Two lines CLOSED, one bounded and declined.** The "2025 needs a
year-specific driver" hypothesis is falsified (2025's whole-year residual off
the law is **positive**). The prompt's DA−RT premium sign-flip clue is a MARKET
fact, not an instrument defect: **excluding June alone, 2025's premium is
+$1.15/MWh**, same sign and family as 2023 (+$0.69) / 2024 (+$0.62) — the entire
−$1.16 flip is one month, and the nyiso-165 §5 cascade-defect class is ruled out
by direct measurement. The offer-side `gas_offer_net_revenue_margin` line is
**bounded at roughly a third of the passthrough deficit and declined**: the
compression makes `d(mc)/d(fuel)` `phys × HR` instead of `mult × HR`, but its
anchor is the rule-23 frozen identification point derived on the SAME pooled
window the band multipliers were calibrated on, so a per-year re-anchor would be
a derivation-vs-dispatch basis mismatch with the residual as its only motive
(rule 1). DO-NOT-REDO written onto the cell's evidence; **verdict stays K**.

**(5) The gain is a cross-ISO model-class property, and NEISO is the in-repo
counterexample.** Same fit on every ISO's designated keeper (a MEASUREMENT —
rule 25, no verdict transfers, no other shard touched): ERCOT 0.347, MISO 0.500,
PJM 0.668, **NYISO 0.703**, CAISO 0.837, **NEISO 0.986**. Every keeper but
NEISO's carries a bounded C3a pass window in price level. The four gates NEISO
arms and NYISO does not are all supply-side capability contraction at physical
extremes and read `·` here; each is a NYISO-lane question entering as `U` on
NYISO's own data (rule 28(d)), never a transfer. `temp_dependent_derate` stays
**`G`** — refused ex-ante at nyiso-111 on NYISO's own measured conduct, and
nothing here is new evidence on it (rule 28(a), do not re-test).

**(6) No lever solved, and why.** The object handed forward is the
price-response gain, not the winter face. Every candidate for it is already
adjudicated or blocked: in-city commitment `G`/`R` and access-walled; the
Iroquois winter spread `R` twice (this finding makes the winter face SMALLER,
which strengthens the rejection — it is not a re-open); `temp_dependent_derate`
`G`; the offer-side line bounded and not a defect. Building a steepener because
the residual wants one is what rule 1 forbids, and no measured NYISO driver in
the repo identifies one today. So the session delivers the attribution and stops
rather than spending a solve on a lever it can already predict fails. **No run
was registered because none was produced** (rule 15 governs completed solves).

**(7) SIDE REPAIR — the NYISO matrix shard did not parse.** The duty-(a) check
found `docs/codebase-site/data/mechanism-matrix/NYISO.js` invalid JavaScript at
HEAD: the nyiso-151 `egrid_identity_heat_rates` entry (line 143) lost its
trailing comma, so `window.MECH_MATRIX_SHARDS.NYISO` was never assigned and
**NYISO's entire column has been missing from the rendered
`mechanism-matrix.html`** since `c66a595d`. Verified with `node --check` against
the HEAD blob before any edit of this session; the other five shards and the
base file compile. Repaired (one character); all seven now pass.
`scripts/check_mechanism_matrix.py` reports "integrity OK" both before and after
— it parses the shards Python-side and never asks a JS engine. A `node --check`
leg over the site data files is FILED as a governance-round guard change, not
built here.

**Open gates unchanged: C3a-2025 −11.5 % and C3c. Determination still NOT-YET.**

Next shorthand: nyiso-168.

## 2026-09-01 — nyiso-168: the gain deficit LOCATED in the ordinary 50–90 load band (73 % of 2025's), the market's steepness measured ~80 % NON-PHYSICAL, and the one new mechanism it points at KILLED EX ANTE (zero solve)

Successor session to nyiso-167 on the named object — the **price-response gain**
(model = 0.7032 × actual_RT + $11.03). **ZERO SOLVE**; committed artifacts plus
one clean-tree fleet read. Keeper, shard determination, marker, freeze and every
matrix verdict but one UNTOUCHED. Rule 22: every year read is 2023–2025; no
marker requested. nyiso-167's probe was re-run first and **reproduces
bit-identically**, so the same object is measured.
Full record: `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md`.

**(1) THE OBJECT IS THE ORDINARY BAND, NOT THE TAIL.** On the DA basis, 2025's
−$4.91/MWh decomposes by load percentile as **0–50 +$1.75 (contrib +0.87)**,
50–80 −$6.20 (**−1.86**), 80–90 −$17.11 (**−1.71**), 90–95 −0.93, 95–99 −0.65,
99–99.9 −0.58, 99.9–100 −0.06. **The 50–90 band carries 73 %; the top 1 %
carries 1.2 %.** The bottom half is OVER-priced in all three years (+2.31 /
+2.70 / +1.75) while gas doubles — a fuel-invariant component. This is the
independent confirmation that C3c is a separate limitation and that a C3c lever
would not have touched C3a.

**(2) FOUR CANDIDATE CAUSES KILLED ON MEASUREMENT.** *Floors* cannot raise the
overnight price at all — a floor adds supply and moves the marginal unit DOWN
the stack (framing (1)'s first suspect, interrogated and structurally
impossible). *Reserves* contribute **exactly $0.00** below the 90th percentile.
*Storage* buys ~$1.4 of the bottom and ~$0.35 of the top, and the model's PS
under-cycles rather than over-cycles. *Mix/availability*: the model's top-decile
dispatch matches EIA-930 NYIS to within 3 % (2025 gas −716 MW on 23.9 GW).

**(3) THE DECISIVE ONE — the market's steepness is NOT physical.** NY CAMPD
unit-level hourly `grossLoad`+`heatInput`, pooled and first-differenced, gives
the fleet's OWN incremental heat rate rising **7.06 → 8.64 (+22 %)** low-to-high
output in 2025 (+21 % 2023, +29 % 2024), while the price-implied marginal heat
rate rises **13.33 → 29.02 (+118 %)** for actual DA and 15.33 → 23.71 (+55 %)
for the model. **Only ~a fifth of the market's revealed steepness is physical
heat-rate dispersion.** This CLOSES the merit-order/heat-rate family as the
explanation — the model already prices more curvature than physics justifies —
and re-points the search at markup and congestion.

**(4) ZONAL SPLIT, and the gradient is not consistently signed.** Load-weighted
deficit = gradient + level: 2023 −0.69 = **+0.96** + −1.65; 2024 −1.43 = −1.49 +
**+0.07**; 2025 −6.59 = −2.32 + **−4.27**. The model OVER-shoots the zonal
gradient in 2023. Only the LEVEL component tracks the year's price level — the
gain law's own signature — and in 2025 it is 65 % of the deficit, measured in
**Upstate_West itself**, where no downstate/in-city/seam mechanism reaches
(reproducing nyiso-167 §2.3's 0.799 upstate passthrough ratio).

**(5) THE ONE NEW MECHANISM, AND ITS EX-ANTE KILL — `reserve_pergen` `·` → `I`.**
Verified in source first: `_nyiso_design` returns `supply_cap=None`,
`headroom_eligible=None`, no `pergen_*` — **NYISO is the only ISO with the
machinery and none of it armed** (`_ercot_design`, `_ercot_multiproduct_design`,
`_pjm_design` all set `supply_cap`). Motivating gap, newly measured: NYISO
clears reserves **above zero in 100.0 % of DAM hours in every zone including
Niagara's own** (2025 zonal means WEST $6.27 → N.Y.C. $12.17; load bands $6.78 →
$13.37 → $34.34) against keeper duals of exactly zero below the 90th percentile.
**Pre-registered kill, fired before any build:** the ramp10 CEILING
(Σ ramp10_frac × pmax) clears every NYCA family on the capacity basis alone —
**4.90× / 5.01× / 10.01×** in 2025 **with hydro excluded entirely**, stable
across all three years. The QUICK_START class alone (gas_ct 3,091 + oil
3,468 MW, both at fraction 1.00) is ten times the 655 MW spinning requirement.
**PROVABLY LP-INERT; no solve spent; the mechanism is not built.**

**(6) WHAT THIS ADDS TO nyiso-144/145 WITHOUT OVERTURNING EITHER.**
`nyiso_spin_reserve_online` stays `I`, untouched and not re-tested — its rho
construction gates on **dispatch** (where hydro does dominate), while nyiso-168
adjudicated only the **capacity** construction. Two additions: nyiso-145's named
purchasable object (a defensible 10-min ramp for NYISO hydro) **would buy nothing
on the capacity basis**, since the thermal-only ceiling is already 10× the spin
requirement; and the reserve-price gap is now measured to be **general, not
tail-confined**. The remaining blocker is unchanged and still owner-funded (AS
certification + hourly water limit), and rule 13 `[R-MEASURED]` bars using the
measured reserve price as an input. `measured_ramp_capability` stays `I` with its
value for the reserve lane specifically now bounded at zero.

**(7) FRAMING (2) CLOSED ON EVIDENCE.** The brief required establishing first,
from NEISO's own record, that the four gates nyiso-167 §4 associated with NEISO's
0.986 gain are what closes it. Census of every committed NEISO bundle:
**4 of 4 arm all five gates — no arm without them exists**, so the attribution
cannot be made from the committed record at all. No NEISO verdict was read and no
NYISO cell filled from one (rule 25, rule 28(d)). Separately, NYISO's four `·`
cells are correct on the merits: its own equivalents are armed under native names
(`nyiso_rcpf_family`, `nyiso_nyc_rcpf_step_curve`, `nyiso_ordc_measured_step_span`,
`nyiso_seny_rcpf_increment_step`, `dual_fuel_switching`,
`nyiso_downstate_ct_gas_basis`, all `K`).

**(8) BRIEF-PREMISE CORRECTION.** The brief carried `DECISION-CARD-nyiso161` as
"FILED AND UNRULED" and directed a check. **It has been ruled:** owner ruling
**R-H**, **OPTION A — NOT-YET STANDS**, recorded at board D-7 in the v18b
completion (PR #4498, `9e4291b6`) after the brief was written. Nothing here plans
around the card or re-litigates it.

**WHAT DID NOT MOVE.** No gate. C3a-2025 still −11.5 %, C3c still fails,
determination still **NOT-YET on {C3a-2025, C3c}**, NYISO still not CALIBRATED.
No solve ran, so rule 15 registers nothing — the dashboard is untouched by
design. One cell moves (`reserve_pergen` `·` → `I`); two carry added evidence
without moving. The gain itself is unmeasured against any arm, because no arm was
built. Honest read: every admissible NYISO-measured lever for the gain is now
adjudicated or blocked on an intake the owner has closed, and the standing
$27.8–$56.0/MWh C3a pass window should be planned around rather than solved away.

**Evidence:** `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md`;
`scripts/probes/nyiso168_gap_anatomy.py` → `_nyiso168_gap_anatomy.json`;
`scripts/probes/nyiso168_reserve_supply_slack.py` →
`_nyiso168_reserve_supply_slack.json`;
`docs/codebase-site/data/mechanism-matrix/NYISO.js` (one cell moved, two
annotated; `node --check` clean on all six shards + the base file).

## 2026-09-01 — nyiso-169 PHASE 0, ZERO SOLVE: the zonal-gradient half is four consistently-signed link terms that CANCEL, and NO binding constraint carries any of it (≥98.3 % forms off-limit) — `measured_interface_limits` `G` re-confirmed and generalised

Chartered to decompose the one leg nyiso-168 measured but did not break down:
the **zonal-gradient component** of C3a (`+0.96 / −1.49 / −2.32 $/MWh` for
2023/24/25), with the standing instruction *"if no constraint carries it in all
three years, say so and stop."* **It does not, and this stops.** Keeper
`2026-08-30-nyiso-159-loss-surface` untouched; determination still **NOT-YET on
{C3a-2025 −11.5 %, C3c}**. No LP ran, so rule 15 registers nothing — by design,
not omission. Full record:
`docs/FINDING-nyiso169-congestion-gradient-anatomy-2026-09-01.md`.

**Predecessor probes re-run first.** `nyiso167_price_gain_attribution` and
`nyiso168_gap_anatomy` reproduce **bit-identically**;
`nyiso168_reserve_supply_slack` reproduces to **1e-15 relative** (float
summation order off a locally-regenerated `fleet` partition; every cover ratio
and verdict identical, committed record left unmodified).

**The decisive measurement.** NYISO's posted cutsets sit within 50 MW of their
limits in **0.0–0.8 %** of hours (CENTRAL EAST - VC 0.75/0.13/0.21 % —
reproducing nyiso-109 to the digit off an independent instrument; TOTAL EAST,
UPNY CONED, SPR/DUN-SOUTH **0.00 %** in every year), while NYISO's own posted
congestion component is non-zero in **4–64 %** of them. **At most 1.7 % of each
model link's annual mean congestion arises in a posted-binding hour, and on
three of the four links it is exactly 0.00 %.** The CENTRAL EAST conditional
mean barely moves ($8.98 all-hours vs $8.89 non-binding, 2023). The congestion
is real, large, general — and sub-interface.

**The kill generalises past posted limits.** A chain link's dual is non-zero
only when its own flow is at TTC, and the model **over**-separates the link it
under-prices (`Upstate_West→Capital_Hudson`, 82–99 % of hours vs a market
congested 15–55 %) while **under**-separating the three it misses (0.3–30 % vs
4–64 %). The aggregate-TTC mechanism is the wrong *shape*, not the wrong
*number*, so no re-estimation of a limit reaches the object. The gradient half
of C3a is therefore a **representation limit at five-zone grain**, not a missing
mechanism: at the 2025 80–90th load percentile the market prices Capital_Hudson
**$23.29 above** Upstate_West **and $7.54 above** Lower_Hudson — a non-monotone
surface a four-link radial chain cannot produce at any setting.

**Premise correction carried forward.** nyiso-168 §5's *"the gradient component
is not even consistently signed"* is true of the **aggregate** and **false of
every component**. Decomposed exactly along the radial chain (identity error
`0.00e+00` in all three years, asserted not assumed), it is **four per-link
terms each consistently signed across 2023–2025 that partially cancel**. Two
clear the pre-registered carry test with **opposing** signs —
`Capital_Hudson→Lower_Hudson` (+1.75/+0.40/+1.53, a model **sign inversion**)
and `NYC→Long_Island` (−0.78/−0.43/−0.39, the model reproduces 13/18/15 % of the
measured LI premium) — and the largest 2025 term
(`Upstate_West→Capital_Hudson`, −2.605) fails it only because 2023 matches to
$0.05. **The aggregate sign flip is a cancellation artifact, not evidence of
absence.**

**Composition.** Off NYISO's published identity `LBMP = E + MCL − MCC` (gated:
the recovered reference energy price is uniform to $0.02 DA / $0.01 RT against a
$0.05 rounding tolerance, every year), the missing content is **congestion, not
losses** — 90–93 % of the Long Island premium and 59–87 % of the Central-East
spread. Independent confirmation that the armed `nyiso_zonal_loss_surface` (`K`)
prices a real, correctly-sized component rather than a residual sink.

**Expected value, priced rather than asserted.** Closing the **entire** gradient
— an unattainable upper bound — moves the DA-basis error to −5.10 / +0.18 /
−6.84 % from −2.13 / −3.79 / −10.56 %. It **costs 2023 nearly three points** and
leaves 2025's level half (the other 65 %) untouched.

**Hypothesis checked and closed en route:** misplaced imports as the
`Capital_Hudson→Lower_Hudson` inversion — the keeper already attaches ties per
landing zone via `nyiso_seam_par_attribution` (`K`).

**Rule 28 (b).** `measured_interface_limits` stays **`G`** with the strengthened
evidence recorded; `nyiso_central_east_measured_ttc` stays **`K`** with an
annotation that the measured limit is correct (rule 14) and it is the
mechanism's *reach* that is annotated. **No verdict moves.** Guard passes
(`check_mechanism_matrix.py` exit 0), shard passes `node --check`.

**Not opened.** A zonal congestion adder is the rule 13 `[R-MEASURED]` forbidden
move (posted MCC is a measured *outcome*) — **not built, not proposed**;
tightening a TTC below its measured value is refused on rule 1 `[R-STRUCT]`.
Phase (2) of the brief (pre-registered kills + a required move in the 0.7032
gain) is **not reached**, because phase (1) returned the stop condition the
brief specified. Rule 22: every year read is 2023/2024/2025; NYISO holds no
`complete` marker, none was requested, the freeze is untouched.

**Data intake (unrestricted per rule 22 as clarified 2026-08-06).** All 36
months of NYISO MIS RT and DA zonal LBMP **component** archives re-fetched with
the frozen `scripts/data/fetch_nyiso_zonal_lmp.py`; the repo tracks only 21 RT
months, the rest being gitignored/regenerable. Probe:
`scripts/probes/nyiso169_congestion_gradient_anatomy.py` → 
`results/calibration/_nyiso169_congestion_gradient_anatomy.json`, **committed at
`bccf58f4` before it was run** so its decision rule is verifiably
pre-registered.

## 2026-09-01 — nyiso-169b ZERO SOLVE: the CC_CHP over-run is a low-end dynamics object, NOT the duct-burner band; CT_PEAKER / ST_GAS / hydro measured alongside

Diagnostic addendum to nyiso-169, answering a raised proposal — that CC_CHP's
duct-burner (`peak`) offer band is priced too low, letting the class over-run at
high capacity factor. **FALSIFIED, unanimously across 2023–2025.** Keeper
`2026-08-30-nyiso-159-loss-surface` and its NOT-YET determination unchanged; no
LP ran, so rule 15 registers nothing. Probe:
`scripts/probes/nyiso169b_gas_class_dispatch_anatomy.py` →
`results/calibration/_nyiso169b_gas_class_dispatch_anatomy.json`.

**The test.** A too-cheap peak band can bid a class in only where that band is
marginal — the **top** of its own duration curve. The over-run is monotonically
at the **bottom**: 2025 top-1 % **−3.3 %** (model BELOW measured) rising to
**+37.4 %** in the bottom quartile; 2023 reads **−14.9 %** at the top. Measured
series = CAMPD combined-cycle units at EIA-860 CHP plants (the model's own CHP
determination), level-anchored to the committed benchmark so only shape is
compared.

**Recorded against the adjudication, because the proposal names a real soft spot
even though it is not this signature's carrier.** NYISO's registered `peak` 2.25
is an F-class **physical** constant with **no NYISO measurement behind it** —
`nyiso_campd_marginal_hr_summary.csv` carries committed / econ_low / econ_high
columns only, **no peak column** — and because the keeper arms `gas_offer_margin`
with `phys_peak == peak` the band earns **exactly zero markup** at runtime.

**What the signature actually names.** A low-end dynamics object: model CC_CHP
p05 **869 / 892 / 817 MW** vs measured **531 / 732 / 648** (+63.6 / +21.8 /
+26.1 %), p25 **+26 / +38 / +47 %** — while at p01 the model drops to near zero
in **96 hours of 2025** where the measured fleet **never falls below ~280 MW and
is never off**. Both directions are wrong: the model treats CC_CHP as freely
dispatchable where reality is a steam-host-following resource with a hard floor.
Successor candidates: the CHP steam-host floor, `chp_layup_duty_curve`, class
min-gen.

**The frame the other objects belong in.** Total NYISO gas volume is right to
~1 % while the split inside it is not — 2025 TWh vs benchmark: CC_CHP **+2.77**,
CC_REGULAR **+2.15**, ST_CHP **+0.69** against CT_PEAKER **−1.82**, ST_GAS
**−3.92**, CT_CHP **−0.55**. A within-gas **merit-order** object.

**Also measured.** CT_PEAKER **−81.5 / −86.2 / −63.7 %** — a year-round deficit,
**NOT winter-specific**: in 2025 it is present in eleven months of twelve, worst
in **May (−93 %)**, mildest in summer, and **December flips to +94 %**. ST_GAS
**+40.9 / −6.0 / −28.6 %**, the 2025 deficit worst in **October** with a genuine
cold-season lean. Hydro volume matched (**−0.2 %** in 2025) with hourly
**r = 0.677 / 0.766 / 0.715** and model dispersion above measured in every year —
a shape object, and the hour-of-day swing is close (2025: 1,774 vs 1,833 MW).

**Why C1 passes anyway, stated so it is not mistaken for a clean bill.** The
criterion floors its band at 3 % of total generation, so a −64 % relative miss on
a 2.9 TWh class is only −1.8 TWh absolute. **The misses are real; the gate does
not charge for them at this size.**

**Rule 28 (b).** `offer_curve_by_group` stays **`K`**, annotated with the
falsification and the un-grounded-`peak` record; **no verdict moves** and no band
value was changed. Guard passes (`check_mechanism_matrix.py` exit 0), shard
passes `node --check`. Rule 22: every year read is 2023/2024/2025.

## 2026-09-01 — nyiso-170 PHASE 0, ZERO SOLVE: the within-gas merit-order split is NOT an hourly displacement (matched-share at or below its own null in all three years, ANTI-coincident in 2025 once load is controlled) — the lane STOPS at the brief's own stop condition, and a CEMS identification limit is established

Phase 0 of the within-gas merit-order object nyiso-169b handed forward, opened as
the last live in-lane C3a-2025 lead on the hypothesis that the model clears cheap
CC (offer-band HR 6.29–8.67) in the high-load hours where the market cleared CT /
gas steam (11.95 / 11.15–11.99). **The brief's stop condition is met and the lane
stops WITHOUT touching a parameter.** Keeper `2026-08-30-nyiso-159-loss-surface`
and its NOT-YET determination on {C3a-2025 −11.5 %, C3c} unchanged; no LP ran, so
rule 15 registers nothing. Full record:
`docs/FINDING-nyiso170-merit-order-displacement-2026-09-01.md`.

**THE KILL.** On the four classes CAMPD can identify, the over-run
{CC_CHP, CC_REGULAR} and the under-run {CT_PEAKER, ST_GAS} are **not the same
hours**: matched-share **0.164 / 0.313 / 0.474** sits **at or below its own
999-fold circular-shift null p95** (0.167 / 0.314 / 0.525) in every year, Pearson r
**+0.022 / +0.016 / −0.212**; and with the load channel removed (within-load-decile
r) 2025 is **anti-coincident** at mean **−0.153 with 1 of 10 deciles positive**.
Phase (2) was therefore not entered — no cost separation identified, no band swept,
no solve manufactured.

**WHAT SURVIVES, AND IS NOT THE SAME CLAIM.** The *aggregate* composition error is
real: the model's share of a rising-load gas increment is more CC-heavy than the
market's by **+0.086 (2024)** and **+0.130 (2025)**, and 2025's class errors are
**95 % / 90 % within-gas MIX** rather than total-gas LEVEL under the exact identity
`delta = s_meas·dG + ds·G_model` (residual 0.0 TWh every class-year). It is simply
not built out of hour-local substitutions, so a merit-order re-level is **not
identified** as its mechanism — arming one would have been a rule-1 `[R-STRUCT]`
steepener adopted because the residual wants one.

**AN INSTRUMENT LIMIT, ESTABLISHED AND CITABLE.** CAMPD cannot identify NYISO
**ST_CHP** conduct **at all** (5 CEMS-registered units reporting **0.000 TWh** in
2025 against a 0.800 TWh benchmark) nor **CT_CHP** (**ONE** unit, 0.483 of
2.383 TWh, anchor 4.93); only CC_CHP / CC_REGULAR / CT_PEAKER / ST_GAS anchor in
range (1.07 / 0.99 / 1.50 / 0.91). This **contaminated this probe's own first
pass** — with measured ST_CHP identically zero the over-run group carried the
model's entire ST_CHP output as error (+1.492 TWh) — and the pre-registered
validity gate caught it *before* the verdict; the repair onto the admissible four
**strengthened** the kill rather than rescuing it. It also **confirms nyiso-169b
rather than impeaching it**: because NY's CHP boilers report exactly zero, that
probe's pooled `fired|boiler` ST_GAS series equals its non-CHP series identically,
so its numbers stand unrepaired — do not "fix" a non-bug.

**THE ONE POSITIVE FINDING, HELD TO ITS TRUE STRENGTH.** Within narrow load slices
the hours the model runs a higher CC share of its gas are the hours it under-prices
— and it survives four pre-registered attacks: partial r given load **−0.243 /
−0.316 / −0.257** (**stronger** than the raw −0.217 / −0.268 / −0.214, so load
suppresses rather than creates it), retaining **0.76 / 0.74 / 0.62×** after further
residualising on gas price, net imports and renewables, Spearman **−0.159 / −0.248
/ −0.206**, and beating a 199-fold within-decile permutation null in **8 / 9 / 9 of
10** deciles, with within-decile spreads monotone in load (2025: −$2.66 at decile 0
to −$22.08 at decile 8) — i.e. in the 50–90 band nyiso-168 showed carries 73 % of
the 2025 deficit. It is handed forward as a **named ASSOCIATION, explicitly NOT a
demonstrated mechanism and NOT a lever**.

**Guardrails honoured.** The un-grounded `peak` 2.25 was **not** swept against C3a
and stays un-grounded; no C3c lever opened; none of the brief's twelve closed lines
re-tested. Rule 22: every year read is 2023/2024/2025, no marker requested, nothing
out-of-training touched. All five briefed probes re-run first — four bit-identical,
`nyiso168_reserve_supply_slack` to 1e-15 as documented and **not** repaired.
Operational note: `nyiso169`'s components need the **gitignored** NYISO DA/RT LBMP
archives, so a fresh container degrades it silently to `available=false` / 1,464 h;
re-staging via `fetch_nyiso_zonal_lmp.py` restores bit-identical reproduction (the
degraded output was never committed).

**Rule 28 (b).** `offer_curve_by_group` stays **`K`**, annotated with the
falsification, the instrument limit and the surviving association; **no verdict
moves** and no band value was changed. `node --check` passes on the NYISO shard and
`check_mechanism_matrix.py` exits 0.

## 2026-09-01 — nyiso-171 PHASE 0, ZERO SOLVE: the CC_CHP "hard floor" is a PORTFOLIO ARTIFACT (16 of 17 cogens hit exactly zero), its target hours are an availability event where a floor is inert by construction, and the class OVER-runs in 80 % of 2025 — every floor mechanism refused, four independent ways

Phase 0 of the CC_CHP low-end dynamics object nyiso-169b handed forward and
nyiso-170 did not touch, opened on the brief's reading that the model treats a
steam-host-following resource as freely dispatchable (model p05 +63.6/+21.8/
+26.1 % over measured, yet near-zero in 96 hours of 2025 the measured fleet
never spends off). Keeper `2026-08-30-nyiso-159-loss-surface` and its NOT-YET
determination on {C3a-2025 −11.5 %, C3c} **unchanged**; no LP ran, so rule 15
registers nothing. Probe
`scripts/probes/nyiso171_chp_floor_identification.py` →
`results/calibration/_nyiso171_chp_floor_identification.json`, committed with
`PREREG-nyiso171-chp-floor-identification.md` at `138fe2ea` **before** either
was run. Full record:
`docs/FINDING-nyiso171-chp-floor-portfolio-artifact-2026-09-01.md`.

**THE STOP CONDITION IS MET.** A fleet floor is a mechanism only if it is a
per-plant property; the discriminator `Σ_p min_t(gen_p,t)` vs
`min_t(Σ_p gen_p,t)` was pre-registered at 0.50 coverage in all three years. It
reads **0.253 / 0.502 / 0.313** — clearing in one year by two thousandths.
Sum-of-plant-minima is **0.0 / 81.0 / 85.0 MW** against fleet minima of
**282 / 368 / 184 MW**, and **0 of 17 plants are never off in 2023** (1 of 17 in
2024/2025). On-shares run from **0.080** (Lockport) to 1.000, and every large
cogen — Sithe 996 MW, Selkirk 597 MW, Empire 580 MW, Brooklyn Navy Yard 260 MW —
hits exactly zero. The measured fleet is "never off" only because its plants are
never all off **at once**, so a per-plant `min_gen` would force machines to run
in hours their own meters say they were off: rule 17 `[R-FLOOR-WINDOW]` violated
**by construction**.

**Three further kills, any one sufficient.** (1) **The target hours are an
availability event, not dispatch** — in all three years they carry price at
**1.60/2.96/3.00×** the annual mean while **total gas output falls to
0.428/0.242/0.009×** normal across all six gas classes (2025: one contiguous
96 h January block, whole gas fleet at 0.0 MW, $168.72 vs $56.19, 70th-percentile
demand). `min_gen` is clipped to `pmax × availability`, so a steam floor **cannot
bind in a single hour it was proposed to repair**. This was measured as **A5b
alongside**, not in place of, A5's weaker pre-registered contiguity proxy, which
had split the years. (2) **The sign forbids it** — the model **over-runs**
CC_CHP in **51/69/80 %** of the remaining hours (mean gap **+37.8/+184.1/+347.3
MW**, nyiso-170 anchored basis); every floor is a lower bound, so **no floor of
any shape** — steam-host, lay-up, commitment-bridge extension, class min-gen —
can address an over-run. (3) **Sizing**: the measured candidate floor would force
**0.013–0.044 %** of class energy.

**Rule 19 `[R-ONE-MECH]` discharged from committed artifacts.** `chp_steam` is
the **sole** mechanism forcing CC_CHP, at **0.05/0.14/0.10 %** of class energy —
and its level source measures **zero on every plant CAMPD can see**: 14 of 17
plants and **77.6 %** of the 4,309 MW class carry `chp_pmin_cf = 0.0`, the whole
381 MW structural floor being one CEMS-invisible plant (Linden, 360.6 MW). The
WP-3 repair is separately **provably inert** for NYISO — `thermal_tranches_NYISO.csv`
is a pre-WP-3 artifact with neither `steam_level_cf` nor `p25_allhr_cf`, so the
loader returns `{}` and `chp_steam_floor_p25` changes nothing.

**The one genuine exception, and the model already has it.** **East River
(2493)**, Con Edison's Manhattan steam/electric station, is online **100 %** of
2025 at a hard **85 MW** minimum — the only NYISO cogen behaving as the brief's
premise describes. The model floors it, under **ST_CHP** at `chp_pmin_cf 30.0`.

**CARRY-FORWARD (measured, not repaired).** East River is `ST_CHP` in the model
artifact but lands in **`CC_CHP`** under the CAMPD `unitType` construction
nyiso-169b/170/171 share, carrying **2.13–2.19 TWh** into the comparison series
while the model's whole ST_CHP class makes 0.07–0.09 TWh — beside nyiso-170 §3's
finding that NYISO's five CEMS ST_CHP units report **0.000 TWh**. A
measurement-construction defect that slightly inflates the measured CC_CHP
low-end percentiles all three sessions compared against; not repaired here
because it would change the basis of three committed findings.

**Brief guardrails honoured.** The un-grounded `peak` 2.25 was neither swept nor
touched; no C3c lever opened; none of the fourteen closed lines re-tested. All
six inherited probes re-run first — five reproduce directly (gain **0.703**,
offset **$11.03**, R² **0.910**; deficit **−$6.59 = −$2.32 + −$4.27**; reserve
ceiling **10.01×**; 169b `False`; 170 `proceed_to_phase_2: false`), and the sixth
hit the documented trap (b) and was repaired per the brief (36 DA months staged,
`nyiso-interface-flows` regenerated) before reproducing at **≥98.3 %** off-limit
congestion. The degraded JSON was never committed.

**Rule 28 (b).** `chp_steam_following` stays **`K`**, annotated with the full
adjudication and a DO-NOT-REDO; **no verdict moves** and no field was changed.
Guard passes (`check_mechanism_matrix.py` exit 0), shard passes `node --check`.
Rule 22: every year read is 2023/2024/2025; NYISO holds no `complete` marker, is
absent from `final`, and **no marker was requested**.

## 2026-09-01 — nyiso-172 PHASE 0, ZERO SOLVE: the ST_GAS deficit is NOT a price-conditional dropout — its SIGN FLIPS (+40.9 % over-run in 2023), it is a between-year RESPONSE deficit whose growth is 99 % downstate, and its counterpart is a ONE-SIDED-PROVABLE CC availability over-statement reaching 13.8 % of 2025's hours

Phase 0 of the ST_GAS level deficit — model **9.7866 vs 13.7121 TWh** in 2025
(**−28.63 %**), the largest absolute class error in the failing year and
nyiso-170 §4's "third thing" (a composition error that is not an hour-local
swap). Keeper `2026-08-30-nyiso-159-loss-surface` and its NOT-YET determination
on {C3a-2025 −11.5 %, C3c} **unchanged**; no LP ran, so rule 15 registers
nothing. Probe `scripts/probes/nyiso172_st_gas_level_deficit.py` →
`results/calibration/_nyiso172_st_gas_level_deficit.json`, committed with
`PREREG-nyiso172-st-gas-level-deficit.md` at `8c3e9b6c` **before** either was
run. Full record:
`docs/FINDING-nyiso172-st-gas-response-deficit-2026-09-01.md`.

**THE STOP CONDITION FIRES, BY SIGN REVERSAL.** S2 asked whether the deficit is
price-conditional — whether the model's ST_GAS turn-on threshold sits right of
the market's in **all three** years, binned on the market's own implied marginal
heat rate (actual DA price ÷ Transco Z6, exogenous to the model). It does in
2024/2025 (T50 21.21 vs 20.47; 18.66 vs 17.03) but **not in 2023, where the
model OVER-runs ST_GAS by +40.9 %, the deficit is POSITIVE in all ten deciles,
and the threshold is LEFT of the market's** (16.20 vs 17.67). No dropout story
holds both ends of the training window. **The brief's premise — "exits too
readily as fuel rises" — is refuted on its own pre-registered gate.**

**WHAT IT ACTUALLY IS: a between-year RESPONSE deficit.** Measured ST_GAS
**9.75 → 11.67 → 15.14 TWh (+55.3 %)** against model **11.47 → 9.32 → 9.79
(−14.7 %)**; ST_GAS share of gas measured **0.169 → 0.179 → 0.225** (rising)
against model **0.183 → 0.138 → 0.141** (falling). Total gas is roughly right in
both (+16.5 % measured, +10.8 % model): **the market's incremental gas went to
steam, the model's went to CC.** And **the model is doing correct isolated
physics** — at ~10.9 heat rate for steam against ~7 for CC the cost gap widens
from ~$7.6 to ~$18.2/MWh as gas goes $1.95 → $4.66, so a pure-economic stack
must push steam back. **The missing driver is therefore not a cost-stack
quantity, which is what rules out the whole offer/startup family rather than
merely declining it.**

**THE BRIEF'S NAMED TRAP REFUSED TWICE.** `gas_st_startup_cost` is (1) refused
on **DIRECTION, proven on the code**: `_amortized` returns
`startup / max(avg_run, 1.0)`, non-negative (`commitment.py:280`), and
`mc_bid = mc_base + markup` is **P1-only** (`solve.py:308`) so P0 run lengths and
every seam-injected `min_gen` floor are unchanged — raising a generator's bid
cost in a pure LP can only weakly **decrease** its output, so arming it
**deepens** a −28.6 % under-run; and (2) **not groundable** — the only
direction-safe model/measured instrument is the class aggregate and it is
**degenerate** (both series on in all 8,760 hours, one run each,
`model_starts = measured_starts = 1`), while per-unit model dispatch is not in
the sidecar. The measured side alone is well behaved (29 units, median-of-median
run **42/61/63 h**, 12–13 starts/unit/yr, **23 of 29** at median run ≥ 24 h in
2025, so the 24/48 h constants are not absurd for this fleet) but one-sided.
The price-side reading is refused separately on nyiso-168 §4 (**+55 %** modelled
vs **+22 %** physical curvature) and rule 1 `[R-STRUCT]`.

**THREE MORE KILLS.** **S3**: not an input defect — required CF **0.176** against
**1,575 MW** of headroom at the model's own 2025 peak (82.3 % of nameplate).
**S7**: the population is clean — off-model measured volume **0.63/0.49/0.68 %**,
one trivial plant (2594), every other non-model steam plant at 0.0000 TWh.
**S6**: the annual gas-price association does not survive at monthly grain —
per-year slopes **+0.116 / −0.0695 / −0.0138**, not one sign, so the pooled
negative is a between-year level artifact and must not be quoted as a mechanism.

**S1, rule 19 `[R-ONE-MECH]`, from committed D-2.** Exactly two mechanisms force
ST_GAS: `reliability_floor` **16.70/22.67/18.43 %** plus
`nyiso_gas_commitment_bridge` **0.82/1.46/1.21 %**. Recorded basis caveat: D-2's
`class_total_twh` (13.6894/11.5181/12.3843) is the LP dispatch frame while the P1
sidecar reads 11.4707/9.3209/9.7866 — different bases, non-constant ratio, so
shares are quoted on D-2's own denominator and no cross-basis share is computed.
Also recorded: the keeper **disables** five downstate `tmax` limbs
(`NYC:ST_GAS`, `NYC:CT_PEAKER`, `Long_Island:ST_GAS`, `Long_Island:CT_PEAKER`,
`Capital_Hudson:ST_GAS`) as the bridge's owner-directed **replacement**
(2026-07-27) — re-arming them alongside it violates rule 19 by construction, and
a `tmax` window cannot carry an all-twelve-months deficit anyway.

**WHAT IS HANDED FORWARD — the one result with a proof.** 99 % of the measured
growth is downstate (**NYC +2.354, Capital_Hudson +1.609, Long_Island +1.382,
Upstate_West +0.004 TWh**), and the counterpart class carries a **one-sided**
defect: the measured CC fleet's **within-month maximum** is a strict lower bound
on its availability, and the model's CC exceeds it in **93 / 773 / 1,211 hours =
1.06 / 8.82 / 13.82 %**, growing monotonically with the ST_GAS error, CC mean gap
**+224/+495/+636 MW**, while matching the measured CC **peak** to 0.99–1.03× —
so the miss is **mid-distribution, not at the peak** (2025 p95 8,471 vs 7,918
MW) and a flat capacity haircut is the wrong instrument. **+636 MW × 8,760 h =
5.57 TWh** against the 2025 ST_GAS (−3.93) + CT_PEAKER (−1.82) = **−5.75 TWh**.
Conservative twice over (CAMPD gross vs delivered basis; a monthly max is the
loosest within-month bound). Concentrated in winter (2025 Jan 432, Feb 343, Dec
161 h) but present Mar–May too, so **not a winter-only lane**. ST_GAS itself
violates the same bound in **100 / 0 / 0** hours. A cause is **hypothesised, not
established**: `UNIT_OUTAGE_MIN_DAYS = 5` (`data/outages.py:239`) makes sub-5-day
derates invisible to the main overlay. Filed as a rule 14 `[R-ACCURATE]`
measured-input question. **Instrument limits travelling with it:** model-side
**zonal** dispatch is not observable from `class_hourly`, and per-unit model
dispatch is not observable at all.

**Brief guardrails honoured.** No offer-level change proposed; the un-grounded
`peak` 2.25 neither swept nor touched; no C3c lever opened; none of the eighteen
closed lines re-tested. All seven inherited probes re-run first and all seven
reproduce (gain **0.703** / offset **$11.03** / R² **0.910**; deficit **−$6.59 =
−$2.32 + −$4.27**; reserve ceiling **10.01×**; 169b `False` with ST_GAS −28.6 % /
all-months-negative `True`; 170 `proceed_to_phase_2: false`; 171 coverage
**0.253/0.502/0.313**). All three documented traps hit and handled: (a) the
reserve-slack float churn was **reverted, not committed**; (b) the container had
**0 DA months** against 21 RT, repaired per the brief (36 DA months staged,
`nyiso-interface-flows` regenerated), after which DA coverage reads **8760 h/yr**
— not the degraded 1,464 — and the probe reproduces at **≥99.2 %** off-limit
congestion; (c) `Etc/GMT+5` throughout.

**Rule 28 (b).** Two cells annotated, **no verdict moves and no field changed**:
`p1_bidcost_pass` stays **`K`** (the two-pass structure is armed; its
class-scoped sub-scalar `gas_st_startup_cost` is the thing refused, with a
DO-NOT-REDO), and `campd_outage_windows` stays **`K`** carrying the one-sided CC
bound. Guard passes (`check_mechanism_matrix.py` exit 0), shard passes
`node --check`. Rule 22: every year read is 2023/2024/2025; NYISO's `complete`
marker was withdrawn 2026-08-30, it is absent from `final`, and **no marker was
requested**.

## 2026-09-02 — nyiso-173: the CC availability over-statement is REAL as a bound violation but PROVABLY INERT as a lever — the armed overlay already carries 56 %, the model never reaches its own CC envelope, and 2.0–2.7 GW sits unused in the violating hours

**Zero solves. No parameter touched, no band swept, no run registered.** Keeper
unchanged: `2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}. Full record:
`docs/FINDING-nyiso173-cc-availability-envelope-not-binding-2026-09-02.md`;
gates `results/calibration/PREREG-nyiso173-cc-availability-anatomy.md`, committed
with the probe **before either ran** (`278ddf37`).

**The object.** nyiso-172 §3.4's one-sided-provable CC availability
over-statement — model CC above the measured fleet's within-month max in
**93 / 773 / 1,211 h** (1.06 / 8.82 / 13.82 %), mean gap **+224 / +495 / +636 MW**
— with `UNIT_OUTAGE_MIN_DAYS = 5` (`data/outages.py:239`) **named but explicitly
not established** as its cause. The probe reproduces §3.4 exactly off an
independent per-unit construction (93 / 773 / 1,211 h; +223.9 / +494.6 /
+635.7 MW) before anything else is measured.

**P1a FAILS — the stop condition fires against the hypothesis.** Decomposing the
measured CC fleet's shortfall from its own demonstrated capability inside the
violating hours, the **armed ≥ 5-day overlay already carries 0.565 / 0.560 /
0.562** of it — a majority, stable to half a point across three years — against
**0.373 / 0.350 / 0.372** overlay-blind. **P1b fails too**: within the blind
remainder the carrier is **partial derates** (0.260 / 0.234 / 0.242), about twice
the sub-5-day full stops the hypothesis named (0.113 / 0.116 / 0.130). NY CC
off-episodes are overwhelmingly sub-day (2025: 1,852 under 24 h vs 427 ≥ 120 h),
which is why the CC detector is event-based to begin with.

**S3, the decisive measurement (reported in addition to the gates).** The overlay
is working hard — it derates the CC fleet in **100 % of hours**, to mean
availability **0.740 / 0.770 / 0.762** of 13,092 MW — and **the model never once
reaches that envelope**: 0 hours at it in any year, peak utilisation 0.794 /
0.821 / 0.839. In the violating hours the model runs 7,384 / 7,500 / 7,749 MW
against an envelope of 10,129 / 10,129 / 10,112 MW, leaving **2,745 / 2,630 /
2,363 MW of already-derated headroom UNUSED**, still **2,391 / 2,275 / 2,010 MW**
net of a 3.5 % CC WEFOR (0 hours at that envelope either). **The whole
measured-availability-input family is therefore provably inert against this
object, ex ante and for any construction**: an input can only lower the envelope
and would have to remove **> 3× the entire gap** before binding. Validated
against its two likeliest artifacts — the envelope is **not** over-tight (the
measured fleet exceeds it in **0** hours of all three years, with and without
East River) and the omitted WEFOR changes nothing. Routing delivers: 2,880 of
2,928 CC rows land on a fleet bin; the 48 dropped (1.64 %) are all plant **2682**
S A Carlson, the `_FLEET_GROUP_OVERRIDE` class at 87 MW — named, out of scope.

**P3 FAILS: the inherited object is DOWNGRADED to portfolio-only.** The model
exceeds the **additive per-plant** bound `Σ_p M_p,m` in **0 hours** in every year
(coverage `M_fleet / Σ_p M_p` = 0.807 / 0.831 / 0.803) — it never exceeds what
NYISO's CC plants individually demonstrated, only what they demonstrated
*simultaneously*. Same discriminator nyiso-171 used; §3.4 must be quoted at that
strength from here on. **P2 is the one gate that PASSES** — the gap is not a
shape artifact in 2025 (positive in all ten price deciles, all ten load deciles,
all five online-unit-count quintiles; 2023 fails the on-count leg at −6.4 MW and
is reported as such) — which buys nothing once S3 holds.

**Lines closed.** (u) the 5-day floor as the cause of the CC bound violation —
refuted on its own pre-registered gate by a stable 56 % majority; (v) the entire
measured-availability-input family as a lever against this object, with a
**measurable re-open condition**: a future keeper whose CC utilisation actually
reaches its envelope; (w) `unit_outage_short_windows` /
`unit_partial_outage_windows` / `unit_outage_maxgen_events` for NYISO on
**measured** grounds rather than argued — the first two extracts are **0 data
rows** (coal-only detectors, NYISO has no coal) and no NYISO maxgen registry
exists (`data/raw/maxgen-events/` is `miso` only), so arming any of the three is
a literal no-op. **The rule 14 `[R-ACCURATE]` framing does not survive the
measurement**: there is no estimate to swap — the accurate availability data is
already in, already applied and already the sole armed channel; the question was
sufficiency, and the envelope is not binding.

**Handed forward, none scoped here.** (1) The unrepaired nyiso-171 §5 **East
River (2493)** crosswalk defect is **materially larger than recorded** — it
inflates the measured CC series, loosening this bound, and removing it raises the
violation count **93 → 208, 773 → 1,500, 1,211 → 1,864**, about a third of the
object. (2) The plant-2682 routing drop. (3) `wefor_residual = null`, so the
caiso-186 rule 19 statistical-WEFOR double count is live here too — recorded, not
proposed, since resolving it makes CC **more** available and points away from
this object. Standing limits unchanged: per-unit and zonal model dispatch are
both unobservable from `class_hourly`, so the S3 envelope is a class aggregate.

**Brief guardrails honoured.** No capacity or nameplate change proposed
(`cc_winter_capability_basis` refused ex ante in the prereg §4); no derate fitted
to the bound (rule 13 — the bound is a diagnostic, never a target); no C3c lever
opened; none of the twenty closed lines re-tested. All **eight** inherited probes
re-run first and all eight reproduce (gain **0.703** / offset **$11.03** / R²
**0.910**; deficit **−$6.59 = −$2.32 + −$4.27**; reserve ceiling **10.01×**; 169b
`False` with ST_GAS −28.6 %; 170 `proceed_to_phase_2: false`; 170b/c/d survival
`True`; 171 coverage **0.253/0.502/0.313**; 172 all six gates false). All three
documented traps hit and handled: (a) the reserve-slack float churn **reverted,
not committed**; (b) the container had **0 DA months** against 21 RT, repaired
per the brief, after which DA coverage reads **8760 h/yr**; (c) `Etc/GMT+5`
throughout. One instrument defect of this session's own was found and repaired
**before any result was read** — CAMPD reports `grossLoad` NULL for a
non-operating unit-hour (52 % of 2025 CC unit-hours) and the first pass
propagated rather than zeroed them; the exact reproduction of §3.4 above is what
validates the repair.

**Rule 28 (b).** Two NYISO cells annotated, **no verdict moves and no field
changed**: `campd_outage_windows` stays **`K`** (the overlay is armed, correctly
routed, demonstrably not over-tight — the successor lane it carried is closed on
measurement) and `unit_outage_short_windows` stays **`I`** (inertness converted
from argued to measured, for all three window shapes that row registers). Guard
passes (`check_mechanism_matrix.py` exit 0), shard passes `node --check`.
**Rule 15:** no solve ran, so nothing is registered on the dashboard — by design,
not omission. **Rule 22:** every year read is 2023/2024/2025; NYISO's `complete`
marker was withdrawn 2026-08-30, it is absent from `final`, and **no marker was
requested**.

## 2026-09-02 — nyiso-174 PHASE 0, ZERO SOLVE: the East River crosswalk defect is a ONE-PLANT defect at 97.8 % of the misclassed volume, the wrong side is the PROBE-SIDE measured construction, the repair moves NOTHING on C1 — and it FLIPS nyiso-170 §3's CT_CHP identification blocker

**Keeper unchanged:** `2026-08-30-nyiso-159-loss-surface`, determination
**NOT-YET** on {C3a-2025 −11.5 %, C3c}. **No parameter touched, no band swept,
no arm pre-registered, no run registered.** Finding:
`docs/FINDING-nyiso174-east-river-class-crosswalk-2026-09-02.md`; probe
`scripts/probes/nyiso174_class_crosswalk_audit.py` →
`results/calibration/_nyiso174_class_crosswalk_audit.json`.

**(a) WHICH SIDE IS WRONG — the CAMPD `unitType` construction, on three
independent primary records that agree.** EIA-860 codes East River (2493)
`GT`×2 (180 MW, 2005) + `ST`×2 (156.2 / 200 MW, 1951/1955) with **no
combined-cycle prime mover (`CA`/`CT`/`CS`) anywhere**. EIA-923 files its net
generation under **two** prime movers every year (`GT` 2.022/2.149/2.079 TWh,
`ST` 1.057/0.745/0.674). And CAMPD's own meters refute CAMPD's own label: the
two units it tags `"Combined cycle"` burn at a measured **10.51–10.89
MMBtu/MWh** — simple-cycle, ~45 % above the CC band — and export **zero**
steam, while all the steam sits on two boilers that generate **0.000 TWh**. The
model's bins reproduce EIA-860's summer split **to the megawatt** (`CT_CHP`
306.0 = 152.1+153.9; `ST_CHP` 309.5 = 132.7+176.8), and a **fourth**
corroboration closes it: the committed `classFull` benchmark runs through the
same `plant_taxonomy.classify_plant`, so the thing C1 is scored against
**already** places the plant in `CT_CHP` + `ST_CHP`. **No per-unit
`_FLEET_GROUP_OVERRIDE` is warranted — the model already has the split.**
*Brief-premise correction:* the tranches CSV carries only the `ST_CHP` row, but
the fleet and `bin_assignments_NYISO.csv` carry **both** bins.

**(b) HOW MANY OTHER PLANTS — ONE.** 228 of 773 NY CAMPD unit-years disagree,
but by volume East River is **6.5811 of 6.7292 TWh = 97.8 %** of the misclassed
energy 2023–2025. Next: S A Carlson (2682) **0.142 TWh** (confirming nyiso-173
S1's 87 MW case as the same family), then Arthur Kill 0.0029, Astoria 0.0022,
Ravenswood 0.0008, Northport 0.0001 — 0.148 TWh in aggregate, 0.07 % of
measured NY energy. A separate 0.578 TWh sits at plants absent from the model
fleet (largest Oswego Harbor 0.222), a **population** question consistent with
nyiso-172 S7's < 0.7 %, not a new object. **This is a one-plant repair, not a
systematic crosswalk defect.**

**(c) WHAT THE REPAIR MOVES — nothing scored; four probe-side bases, one flip.**
**C1 does not move, and that was measured rather than assumed:** nyiso-169b
measurement A reproduces exactly (2025 CC_CHP **+16.30**, CC_REGULAR **+6.40**,
CT_PEAKER **−63.73**, ST_GAS **−28.63**) because both its inputs — the keeper's
P1 `class_hourly` and `classFull` — were always on the prime-mover basis. **The
defective construction never touched a scored quantity, so there is no
model-side, data-side or config-side arm to pre-register.** What does move:
**nyiso-170 §3's `CT_CHP` "NOT identifiable" FLIPS** (anchor **4.933 → 0.892**,
1 → 3 CEMS units, 0.483 → 2.672 TWh gross against a 2.383 TWh benchmark) —
CT_CHP hourly conduct IS identifiable from CAMPD; its **`ST_CHP` blocker
SURVIVES** at 0.000 TWh; its **`CC_CHP` anchor WORSENS 1.070 → 1.241**, so that
verdict was itself partly an artifact. **nyiso-171 A3 is STRENGTHENED TO
UNANIMITY** — all 16 remaining CC_CHP plants reach zero in every year,
sum-of-plant-minima **0.0 MW** in all three (vs its own 0.0/81.0/85.0), 0 plants
never off, while the class floor is still 182/277/81 MW; East River **was** its
single counter-example. **nyiso-172 §3.4 is RESTATED ~60 % larger** — 93 → 219,
773 → 1,523, 1,211 → 1,926 h (2.50/17.39/21.99 %), still portfolio-only.
**nyiso-173's adjudication SURVIVES untouched** — its decisive S3 was taken with
and without East River, and 2.0–2.7 GW of unused envelope dwarfs the growth.

**(d) RULE 19 `[R-ONE-MECH]` ENUMERATION for 2493**, off the engine: `chp_steam`
(`chp_pmin_cf = 30.0`) reaches the **`ST_CHP` bin only** (no `CT_CHP` tranches
row exists); the outage overlay reaches **`ST_CHP` only**, because
`_generic_unit_outage_target` returns `None` for `CT_CHP`/`CT_PEAKER` by design,
so the 306 MW turbine bin takes **no derate at all**; the commitment bridge
(`CC_REGULAR` + `ST_GAS`) and the reliability-floor limbs do not reach it; and
there is **no `_FLEET_GROUP_OVERRIDE` entry and none should be added**.

**Phase 2: NOT ENTERED, and that is the correct outcome, not a punt.** The
brief made phase 2 conditional on (1) establishing which side is wrong. It did —
and the wrong side turns out to be entirely measurement-side, with no
`ScenarioConfig` field, data input or LP quantity behind it. The repair
delivered is therefore the corrected construction itself,
`scripts/lib/campd_measured_classes.py` (19 tests,
`tests/unit/data/test_campd_measured_classes.py`), which costs no solve and
stops session 175+ re-introducing the defect.

**Handed forward, none scoped here.** (1) A real zero-DOF **model-input**
defect: `_resolve_unit_group`'s `fac_group` short-circuit (last-writer-wins over
the fleet iteration) writes East River's two `GT`s into
`campd-unit-outages-NYISO.csv` as `ST_CHP`, so their windows derate the steam
bin — the same short-circuit neiso-99 already carved a rule 14 exception out of.
**Two windows, both 2023**; not repaired because it is solve-affecting, its
direction makes the steam bin *more* available (deepening the +86.55 % ST_CHP
over-run), and it sits inside (2). (2) **The successor object: which half of
East River carries the must-run.** The model floors the **steam** bin at
92.85 MW and leaves the turbine bin unfloored and un-derated, while the market's
must-run is measurably in the **turbine** half (7,183–7,698 op-hours each, a
hard 85 MW plant floor in 2025, boilers at 0.000 TWh); C1 2025 reads `ST_CHP`
**+86.55 %** against `CT_CHP` **−23.37 %**, with East River **65.8 %** of the
model's `ST_CHP` capacity and **68.6 %** of its `CT_CHP`. (3) **A
diagnostics-integrity limit that BLOCKS (2)** and is far larger than the
`ST_GAS` one on record: D-2's `class_total_twh` vs the P1 `class_hourly`
sidecar disagree **13–17×** on `ST_CHP` (0.0712/0.0913/0.0931 vs
1.196/1.185/1.492) and 1.6–1.8× on `CT_CHP` in the **opposite** direction, while
agreeing on the CT+ST **total** to within 2.2 % — and D-2's `ST_CHP`
`share_of_class` is consequently **> 1** (2.847 / 1.795), a live hazard for the
rule 20 `[R-FORCED-BUDGET]` gate. (4) The model's East River `heat_rate` is
**7.4205** on all four units against a measured **10.51–10.89** on the two
turbine stacks — **recorded, NOT proposed**, because the right electric heat
rate for a cogen is a fuel-allocation question and (3) blocks the model-side
check.

**All twelve inherited probes re-run first and all twelve reproduce** — 168
gap (−$6.59 = −$2.32 + −$4.27), 168 reserve slack (**trap (a)**: max *relative*
delta **3.6e-16** over 309 leaves, zero structural or verdict differences,
churn **reverted not committed**), 169 (**trap (b)** handled: DA months
re-fetched and `nyiso-interface-flows` regenerated, DA `hours_covered` **8760/yr**
after), 169b (+16.3 / +6.4 %), 170 (`proceed_to_phase_2: false`), 170b/c/d
(`survives_all_years: true`), 171 (0.253/0.502/0.313), 172
(`proceed_to_arm: false`), 173 (773 / 1,211 h, coverage 0.831), 173b (0.794 /
0.821 / 0.839, headroom 2,745 / 2,630 / 2,363 MW). **Eleven produced zero git
churn.** **A NEW TRAP, same family as (b), documented for successors:**
`nyiso168_reserve_supply_slack` **silently degrades** without the
`ancillary-services` clean partition — it drops its entire `DAM` and `RTM`
measured reserve-price blocks (127 lines) and still **exits 0**, so committing
its output would silently delete a committed measurement. It fails *loudly*
without `fleet`; the loud mode is the safe one. Regenerate **both**, and diff
structurally, not just numerically.

**Reproduction discipline.** The construction was verified against **three**
committed sessions before restating any of them: nyiso-171 A3 exactly (17
plants, 0.0/81.0/85.0 MW, fleet minima 282/368/184, plants-never-off `[2493]` in
2024/2025), nyiso-172 §3.4's violation-hour counts exactly (93/773/1,211), and
nyiso-173 S3's violating-hour means exactly (2025 model − measured
**1,646.5 MW** vs its 7,749 − 6,102). One item is left **unreconciled and said
so**: nyiso-172 §3.4's reported *"CC mean gap"* column (+224/+495/+636 MW) could
not be reconstructed from any of four natural definitions; it is a reported
column, not a gate, and nothing here depends on it. Trap (c) (`Etc/GMT+5`) and
trap (d) (CAMPD `grossLoad` NULL filled to zero explicitly) both handled.

**Rule 28 (b).** Two NYISO cells annotated, **no verdict moves and no field
changed**: `campd_outage_windows` stays **`K`** (mechanism armed and correct;
the routing defect is named, sized and handed forward) and
`chp_steam_following` stays **`K`** (nyiso-171's stop condition strengthened to
unanimity on the corrected basis). Guard passes
(`check_mechanism_matrix.py` exit 0), shard passes `node --check`.
**Rule 15:** no solve ran, so nothing is registered on the dashboard — by
design, not omission. **Rule 22:** every year read is 2023/2024/2025; NYISO's
`complete` marker was withdrawn 2026-08-30, it is absent from `final`, and **no
marker was requested**. **No C3c lever opened**; none of the twenty-three closed
lines re-tested; **C3a-2025 did not move and none was available** — §4.2 is the
measurement that explains why this lane never could.

## 2026-09-02 — nyiso-175 PHASE 0, ZERO SOLVE: the D-2 blocker is a GRAIN difference (not a defect) and UNBLOCKS its successor; the "CT deficit" is TWO objects with opposite signatures; and BOTH East River gates fail on their own pre-registered thresholds, so nothing is armed

Chartered to clear nyiso-174 §6 item 3's D-2 vs `class_hourly` blocker and then
spend the `CT_CHP` instrument nyiso-174 unlocked. Both done; **no arm was
pre-registered and no LP ran**, so rule 15 registers nothing — by design, not
omission. Keeper `2026-08-30-nyiso-159-loss-surface` and its **NOT-YET**
determination on {C3a-2025 −11.5 %, C3c} **unchanged**. Prereg
`results/calibration/PREREG-nyiso175-ct-conduct-and-d2-basis.md` + probe
`scripts/probes/nyiso175_ct_conduct_and_d2_basis.py` committed at `6c3f0cf7`
**before either was run**. Full record:
`docs/FINDING-nyiso175-ct-deficit-two-objects-2026-09-02.md`.

**Predecessor probes re-run first — all fifteen.** Fourteen reproduce
**bit-identically**; `nyiso168_reserve_supply_slack` to a max relative delta of
**1.94e-16** over 309 numeric leaves with **zero** structural difference (trap
(a); the churn was **not** committed). Traps (b)–(f) all hit and all handled:
the gitignored DA LBMP container was re-staged and `nyiso169` then reproduces
bit-identically at DA `hours_covered` **8760/8760/8760**; `ancillary-services`
was regenerated first and the reserve-slack JSON diffed **structurally** as well
as numerically (both measured DAM/RTM blocks intact). **One new environment
trap, recorded:** the D-2 floor rebuild needs the `capacity-deliverability`
clean partition or `apply_nyiso_li_tsl_import_cap` raises — it is not on the
brief's phase-0 list.

**(A) THE BLOCKER IS CLEARED, AND NEITHER ARTIFACT WAS WRONG.** Gate A1 as
pre-registered **FAILS** — and the failure identifies the basis. The committed
D-2 was built at solve time on the run's own `dispatch/<year>_P1.parquet`;
that file is gitignored, so a HEAD recompute falls **silently** to the 100-plant
run payload and moves `CC_CHP` **+28.9 %**, `CT_CHP` **+34.3 %**, `ST_CHP`
**+95.3 %**, `hydro` **+37.3 %** (2025). Two identities off committed bytes
settle what the committed denominator IS: D-2's `hydro` equals `class_hourly`'s
**to four decimals in all three years** (26.6134 / 26.7390 / 24.0589) and its
`''` bucket equals `nuclear` + the 7.884 TWh HQ pseudo-unit to **0.005 %**; and
the `CT_CHP` / `ST_CHP` deltas are **equal and opposite** to a residual of
**0.0084 / 0.0271 / 0.0746 TWh**. **The 13–17× disagreement is a GRAIN
difference**: D-2's row is the **plant** and its label is the plant's
most-common **LP-unit** `plant_group` — East River carries **4 `CT_CHP`
tranches against 3 `ST_CHP`** (floors arrays), so the plant is labelled
`CT_CHP` and its `ST_CHP` energy lands in D-2's `CT_CHP` denominator (gate A2's
sign falsifier, **PASS**). `class_hourly` is the identified per-class model
artifact and **nyiso-174 §6 item 2 is UNBLOCKED**.

**The brief's rule 20 `[R-FORCED-BUDGET]` hazard is WITHDRAWN ON THE CODE.**
`ST_CHP`'s `share_of_class` > 1 is a unit-grain numerator over a plant-grain
denominator — the pathology `run_d2`'s own docstring discloses — and it can
never gate, because `CC_CHP` / `CT_CHP` / `ST_CHP` are in `D2_EXEMPT_CLASSES`;
the keeper's own D-2 summary carries `CC_REGULAR`, `CT_PEAKER`, `ST_GAS`,
`hydro` and nothing else. **A different number in the same family is corrected
UPWARD**: `chp_steam`'s forced share of `CT_CHP` is **12.5 / 39.2 / 11.3 %** of
class energy, not the recorded 7.6 / 21.3 / 6.3 % — **~1.8× larger**, because
the recorded figure divided by D-2's plant-rollup denominator.

**(B) THE INSTRUMENT SPEND SPLITS THE OBJECT IN TWO, unanimously across three
years.** On the pre-registered B5 rule `CT_PEAKER` is **LEVEL**-limited (q90
model ÷ q90 anchored-measured **0.050 / 0.053 / 0.369**; starts **102 / 93 /
156** against **399 / 457 / 293** with run medians still MATCHING at 8/7/7 vs
9/7/10 h; only **37.8 / 28.2 / 43.2 %** of measured class energy in an hour the
model runs the class) while `CT_CHP` is **RESPONSE**-limited (q90 ratio **0.739
/ 0.870 / 0.756**, hourly **r = 0.016 / 0.258 / 0.395**) — a class online
**8,760 h** in the market and 8,592–8,736 h in the model, below the market at
**every decile** of its own duration curve, with **88 / 100 / 88 %** of its
deficit in the bottom 80 % of load hours. **The −2.4 TWh "CT deficit" is not one
object**, and only `CT_PEAKER` was ever the load-pocket story — whose diagnosis
this independently **CONFIRMS** on a different construction, bar and keeper than
nyiso-90/91/96 used. Guard S4 honoured: **no `CT_PEAKER` lever opened**.

**THE ONE OBVIOUS `CT_CHP` SUCCESSOR IS CLOSED BEFORE IT IS BUILT.** CAMPD
meters East River's district-steam send-out directly, and it sits **entirely**
on units 60/70 — two direct-fired boilers generating **0 MWh** of electricity in
all three years (nyiso-120 KE3, reproduced independently here) — with units 1/2
exporting **zero** steam. `r`(measured plant turbine MW, plant steam klb/h) =
**−0.016 / +0.309 / +0.077**. **There is no hourly steam profile to give
`chp_steam_following` at this plant.** The model's `CT_CHP` tracks system load
at r = 0.724/0.759/0.644; the market's tracks load at 0.29–0.40, steam at ~0,
and runs a **maintenance** shape (2023: 271/256 GWh Jan–Feb against 114/69 GWh
Apr/Oct) no armed mechanism can produce.

**(C) BOTH EAST RIVER GATES FAIL, SO NOTHING IS ARMED.** S2 needs all three:
(a) turbine-family share of the plant's CAMPD `grossLoad` **1.000/1.000/1.000**
PASS; **(b) EIA-923 GT:ST 1.914 / 2.885 / 3.083 — FAIL** (below the 2:1 bar in
2023, where the steam half carried **34 %** of the plant's electricity);
(c) inversion 1.212/2.007/2.082 PASS. **S3 also FAILS**: East River is **43.2 %**
of the misattributed energy (**6.581 of 15.233 TWh**) — **Ravenswood (2500) is
bigger at 8.509 TWh**, its `ST_GAS` 1,724.8 MW primary group losing to a 222.2 MW
`CC_REGULAR` bin that carries 64–73 % of the energy. The object is real, named
and sized, and it is a **fleet-wide derive question**, handed forward.

**FOUR CORRECTIONS TO THE COMMITTED RECORD**, all measured. (1) nyiso-174 §5's
"the turbine bin has no floor" is **WRONG** — East River's `CT_CHP` bin carries
a `chp_steam` floor of **90.08 MW in all 8,760 hours of every year**, MORE hours
than the ST bin's 92.82 MW binds (7,272/8,040/7,872); the tranches CSV has no
`CT_CHP` row but the EIA-923 CHP-pmin route floors it anyway. (2) nyiso-174 §6
item 2's premise **"its boilers having generated 0.000 TWh" conflates CAMPD's
direct-fired boilers with the EIA-860 steam TURBINES**, which generate **1.057 /
0.745 / 0.674 TWh** a year on EIA-923 — which is what fails S2(b). (3)
nyiso-174 §1's heat-rate leg (10.51–10.89 MMBtu/MWh) divides the whole power
train's fuel by GT-only gross load; nyiso-120 KE2 measured the power-train rate
at **7.3763** against eGRID's **7.4205** (0.6 %), in the CC band — the label
conclusion stands on prime movers, the heat-rate leg does not support it.
(4) the forced-share correction above.

**THE NAMED OBJECT, handed forward with its expected value stated honestly.**
`derive_thermal_tranches._fleet_nameplate_and_group` attributes a plant's
facility-summed CAMPD net to its **largest-nameplate** group; at East River that
is decided by **3.5 MW (1.1 %)** and puts 2.1–2.3 TWh/yr of turbine conduct onto
the steam row (`online_hours` 26,253, `committed_pct` 32.0, `median_cf` 98.5 on
a 309.5 MW steam denominator) while the 306.0 MW turbine bin gets no row.
Same defect family as nyiso-174 §6 item 1 and neiso-99's rule 14 exception; the
corrected per-unit construction exists and is tested. Zero DOF. Closing East
River's split moves C1 `CT_CHP` by **+0.378 / +0.965 / +0.402 TWh** and `ST_CHP`
by **−0.064 / −0.343 / −0.713 TWh** — but its **C3a expectation is ~ZERO**
(both bins carry heat rate 7.4205 and the same delivered gas), so it is a rule 1
`[R-STRUCT]` representation repair and **must never be proposed as a C3a lever**.
Re-open condition: a session that can carry a full three-year re-solve, in the
same commit as nyiso-174 §6 item 1.

**ALSO HANDED FORWARD: the keeper's committed D-2 is not re-derivable from
committed artifacts** (§A above) — `dispatch_source` is already computed in
`legitimacy_diagnostics.py` and used only in a coverage note; stamping it into
the D-2 block closes the gap. Cross-ISO, zero solve.

**Rule 28 (b).** Five NYISO cells re-stamped, **no verdict moves**:
`chp_steam_following` **K** (ex-ante adjudication of its one successor route),
`thermal_tranche_artifact_coverage` **O** (the attribution defect),
`scuc_load_pocket_commitment` **G** (independent confirmation),
`diagnostics_plant_set` **I** (the reproducibility gap),
`measured_chp_heat_rates` **K** (correction 3). NYISO shard only; `node --check`
passes and `check_mechanism_matrix.py` exits 0. **Rule 22:** every year read is
2023/2024/2025; NYISO holds no `complete` marker, none was requested, the freeze
is untouched. **No C3c lever opened; none of the twenty-six closed lines
re-tested.**

## 2026-09-02 — nyiso-175b: the per-unit attribution repair is BUILT and VALIDATED at artifact level (both artifacts), it RESOLVES nyiso-174 §6 item 2, and a NEW blocker — BOTH NYISO solve inputs are non-reproducible at HEAD — is why no LP ran

Second charter of session nyiso-175, taken after the first was found discharged
and merged. Chartered to land nyiso-175 §4.4's handed-forward item 1 (the
fleet-wide tranche-attribution defect) together with nyiso-174 §6 item 1 (the
outage-extract routing defect), with the three-year re-solve those needed.
**The repair is delivered; the re-solve is BLOCKED, on evidence, by an object
neither brief knew about.** Keeper `2026-08-30-nyiso-159-loss-surface` and its
**NOT-YET** determination on {C3a-2025 −11.5 %, C3c} **unchanged**; no LP ran,
so rule 15 registers nothing — correct, not an omission. Prereg
`results/calibration/PREREG-nyiso175b-tranche-attribution-repair.md` committed
at `22bfe37a` **before** the probe or any derivation was run (the seventh
consecutive session to honour this). Full record:
`docs/FINDING-nyiso175b-tranche-attribution-repair-2026-09-02.md`.

**ALL FOUR PRE-SOLVE GATES PASS — and K2 earned its keep.** **K1**: the
corrected per-unit attribution re-seats **13.7577 TWh** of NYISO CAMPD energy
over 2023-2025 (bar 4.0), 4.5293/4.5612/4.6672 by year, across **six** plants —
East River 6.5811 onto `CT_CHP` (a **3.5 MW, 1.1 %** nameplate margin decides
it), Ravenswood 5.8467 onto `CC_REGULAR` (a 1,502.6 MW margin picks a bin
carrying a third of the energy), then Bethpage/E F Barrett/Port Jefferson/S A
Carlson. **K2 FAILED as first constructed**: three `ST_GAS`-only plants (2490,
8906, 2516 Northport) have CAMPD combustion turbines correcting to `CT_PEAKER`,
a bin they do not carry, so 0.0051 TWh would have been silently dropped out of
the `ST_GAS` denominator — a reclassification, not a crosswalk repair. **The
CONSTRUCTION was amended, never the threshold** (nyiso-175 §4.5's own
discipline): a unit stays on the plant's primary group wherever the plant
carries no bin in its prime-mover family. Re-run **PASS**, and K1 tightens
13.7628 → 13.7577 over 11 → 6 plants. **K3** (rule 19 `[R-ONE-MECH]`, measured
by CALLING the production resolver, not reading it): the existing miso-200
`mixed_gas_routing` gate **cannot** reach East River — `_GAS_BIN_GROUPS`
excludes both CT classes, so `{CT_CHP, ST_CHP}` intersects at size 1 — **and is
actively WRONG where it does fire**, routing Ravenswood's block CTs
`CT0001/0010/0011` to `CT_PEAKER` (dropped from the overlay) although those are
three of the 27 units the neiso-99 liquid-fuel guard's own evidence names as
gas-fired block members. Arming the existing flag for NYISO would have traded
one mis-routing for another. **K4**: all three carrier bins genuinely lack a
tranche row today.

**THE REPAIR, both artifacts, one crosswalk.**
`derive_thermal_tranches --per-unit-attribution` and
`derive_campd_unit_outages --per-unit-crosswalk`, both default-off, both
writing `-perunit-` companions (never an overwrite — the `-unitroute-`
discipline), both routing through the SAME
`campd_measured_classes.corrected_unit_class`, so they cannot disagree about
which bin a machine belongs to. Zero free parameters (rule 21), static
forward-regenerable inputs (rule 13), a crosswalk repair citing the attribution
defect rather than a data change (rule 23). `campd` gains
`plant_group_hourly_net` plus `prefer_unit_level`, and **two guards that were
earned, not designed**: it raises without unit identity, and raises when every
`unit_id` is blank — a FACILITY-level extract. Without the second, the first
derivation **silently reproduced facility attribution under a per-unit name**
(NY resolves facility-first because it exists in both directories), which is the
repaired defect made invisible.

**ARTIFACT DELTA, unconfounded (both legs derived at HEAD).** Tranches: **13 of
85 rows**, seven plants. **nyiso-174 §6 item 2 is RESOLVED in the artifact** —
East River's `ST_CHP` measured row correctly disappears (its boilers generate
0.000 TWh in all three years) and a **`CT_CHP` row appears at 306.0 MW / 26,251
online hours / committed 30.1 / `chp_pmin_cf` 28.4**, moving the must-run to the
half the meters say is running. Ravenswood `ST_GAS` 23,472 → 7,293 h with a new
222.2 MW `CC_REGULAR` row at committed 70.0. S A Carlson's 120-hour `ST_GAS` row
is replaced by a 3,913-hour `CT_PEAKER` row — **recovering the committed
artifact's own `online_hours` on the correct bin**. Outages: **22 units
re-routed, zero added** — East River 1/2 `ST_CHP`→`CT_CHP` (8+8 windows),
Ravenswood 10/20/30 `CC_REGULAR`→`ST_GAS` (25+23+22), and E F Barrett's 16
`U000xx` combustion turbines (~590 windows) correctly leaving the overlay, since
`CT_PEAKER` is outside `QUALIFYING_PLANT_GROUPS` **by existing design**. That
last is the largest single effect and its direction is ADVERSE to the CT
deficit: today 16 CTs derate that plant's STEAM bin, and removing them makes
`ST_GAS` *more* available. It is proposed because the routing is wrong, not
because it helps.

**ONE NEGATIVE RESULT, at full strength.** The physically-impossible
`median_cf > 100` census improves only **11 → 10**: the repair removes the two
it causes (2493/`ST_CHP` 118.3, 2682/`ST_GAS` 150.0) and Ravenswood's new
`CC_REGULAR` row adds one at 113.9. **Above-nameplate CEMS gross is NOT a
signature of this defect** and must not be quoted as evidence for it.

**THE BLOCKER, and it is the session's real headline. BOTH NYISO solve inputs
are non-reproducible at HEAD.** `thermal_tranches_NYISO.csv` — the keeper's
input, sidecar `derive_invocation: null`, vintage unknown, and its own text
says it "makes no claim about what HEAD would emit" — differs from a fresh
unrepaired HEAD derivation on **46 of 78 rows**: `online_hours` by up to
**26,271**, `median_cf` 65.6, `committed_pct` 27.2. The outage extract is worse
in proportion: **4,423 → 2,632 windows, −40 %, from nothing but re-running the
deriver**. Consequently a fully re-derived arm carries the repair AND 40 rows of
unadjudicated drift at plants the repair never touches, and cannot attribute
either — the confound miso-200 refused. **The obvious escape also fails**: a
minimal-delta arm keeping committed values except at the seven affected plants
does not work, because at **two of those seven the drift EXCEEDS the repair**
(Bethpage `CC_REGULAR` drift −2,337 h against repair −217; E F Barrett `ST_GAS`
drift +3,050 against repair −736). A clean A/B therefore needs a HEAD control
leg — **two** three-year solves — and even then the arm is **not promotable**,
because promoting it would import the drift as an unadjudicated change.

**HANDED FORWARD, in priority order.** (1) **The reproducibility gap is now the
precondition for everything else** — adjudicate the drift and re-baseline the
keeper's inputs at HEAD, then land the repair on top as a clean delta; that is
strictly better than paying for a control leg to work around it. (2) The A/B is
otherwise **ready**: both companions are committed, and the two flags must land
**together**, because the repaired `CT_CHP` tranche row is currently derived
against an **un-derated** denominator (every East River window still routes to
`ST_CHP` in the extract the tranche deriver reads). (3) **The solve-side
selector is NOT built**: nothing in `src/` reads the `-perunit-` tranche
companion — the path is hardcoded at **11 call sites** (`campd_bins.py` ×9,
`coal.py`, `chp.py`), 9 of which take only `iso` and no config, so wiring it
needs a resolver plus a `ScenarioConfig` field threaded through those callers
(rule 24). The outage half is already wired via `unit_outage_csv_for_iso`.
(4) S A Carlson's 120-hour control row with `median_cf` 150.0 is a good place to
start diagnosing the drift.

**CORRECTIONS.** nyiso-174 §6 item 1's "two windows, both in 2023" **understates
it**: the committed extract carries **21** windows on East River units 1/2,
spanning 2018-2026; 2023 is where the training window clips it. And the
mis-routing is **not East-River-specific** — all **185** Ravenswood windows sit
on `CC_REGULAR`, its three steam boilers included. nyiso-175 §4.4's 15.233 TWh
and this session's 13.7577 TWh are **different statistics, not a disagreement**
(whole-plant conduct vs the units actually re-seated).

**Rule 28 (b).** `thermal_tranche_artifact_coverage` **O → K** (the repair is
built, validated at artifact level, default-off) and `campd_outage_windows`
re-stamped with the routing evidence; NYISO shard only. **Rule 25**: the code is
ISO-agnostic but **only NYISO's artifacts were derived** — every other ISO's
committed tranche and outage CSVs are byte-untouched. **Rule 22**: every year
read is 2023/2024/2025; NYISO holds no `complete` marker, none was requested.
**Tests**: 167 campd + 758 tranche/outage/fleet pass; the single failure
(`test_capacity_evolution_changes_fleet`) reproduces on a clean stash of HEAD
and is pre-existing. **No C3c lever opened; none of the twenty-six closed lines
re-tested.**

## 2026-09-02 — nyiso-176: the "−40 % artifact drift" that blocked nyiso-175b is an INVOCATION-SPAN ARTIFACT whose SIGN IS WRONG; the real drift is three channels of which only ONE is a defect (already repaired); the repair is WIRED and SOLVED — and the A/B FAILS its own pre-registered gate, closing C3a-2025 while breaking three other criteria

Chartered to attribute the input-artifact reproducibility gap nyiso-175b handed
forward as "the precondition for everything else", and to decide the
re-baseline. **Both done, and the attribution changes what the object is.**
Keeper `2026-08-30-nyiso-159-loss-surface` and its **NOT-YET** determination on
{C3a-2025 −11.5 %, C3c} **untouched**; no parameter, band, floor or offer value
changed; **no C3c lever opened**. Prereg
`results/calibration/PREREG-nyiso176-input-artifact-reproducibility.md` +
probe `scripts/probes/nyiso176_input_artifact_reproducibility.py` committed at
`60653b59` **before either was run** (the ninth consecutive session to honour
this). Full record:
`docs/FINDING-nyiso176-input-artifact-reproducibility-2026-09-02.md`.

**THE HEADLINE IS A CORRECTION TO THE COMMITTED RECORD.** nyiso-175b §4.1
reported `campd-unit-outages-NYISO.csv` drifting **"4,423 → 2,632 windows,
−40 %, from nothing but re-running the deriver."** **That comparison is an
INVOCATION-SPAN ARTIFACT AND ITS SIGN IS WRONG.** The committed extract spans
**2018–2026**; `derive_campd_unit_outages.py --years` defaults to
**2023–2025**; the figure put nine years against three. Re-derived at HEAD over
the committed span the count is **6,455**, and on a like-for-like 2023–2025
basis the direction **REVERSES** to **1,495 → 2,632, +76 %**. Pre-registered
gate **R1 therefore FAILS** on its own bar and is reported as a failure — but
the failure re-sizes the object rather than dissolving it: **3,767 of the
committed 4,423 windows (85.2 %) reproduce EXACTLY at HEAD**, and **3,674 of
the 3,802 NON-2018 windows (96.6 %)** reproduce exactly under the repaired
routing. **The 621 missing 2018 windows have a NAME, not a mystery:** BLOAT-S2
(2026-08-17) untracked the `campd-unit-level` 2018 vintage and the 2026-08-16
rewrite stripped it, so `data/raw/campd-unit-level/` carries NY_2019…NY_2026
only and recovery is **re-fetch, never a pin**.

**THE REMAINING 2023–2025 GAP DECOMPOSES ORTHOGONALLY, measured as a 2×2 of
HEAD re-derivations against the committed 1,495:** incumbent routing + override
**2,632**; override OFF **1,645**; per-unit routing **1,996**; both **1,344**.
So of the **+1,137**: the **full-stop duration override carries +987 (87 %)**
and the **`fac_group` routing short-circuit carries +636** at override-on
(+301 at override-off), the two overlapping on the same idle-peaker windows.
**ONLY ONE IS A DEFECT, AND IT IS THE ONE ALREADY REPAIRED.** E F Barrett
(2511)'s 16 `U000xx` combustion turbines alone explode **18 committed 2023–2025
windows into 610 at HEAD** and collapse back to **20** under nyiso-175b's
per-unit crosswalk — **54 % of the entire gap, one plant, the exact defect
nyiso-174 §6 item 1 named.** **THE OVERRIDE IS NOT A DEFECT AND IS NOT PROPOSED
FOR CHANGE**, and it survives its own falsifier rather than being excused: of
the **60,024** unit-hours its 2024 windows cover across five affected plants,
only **622 (1.0 %)** show ANY metered generation (committed 0.1 %) — the
windows are not asserting unavailability against a running meter. It is a
deliberate, cited detector feature (`FULL_STOP_OVERRIDE_DAYS`/`_CF`) that the
committed extract simply predates.

**TWO SUSPECTS ELIMINATED BY MEASUREMENT, both recorded because either could
have gone the other way.** (1) **Parasitic factors are EXACTLY INERT** — 0 of
78 tranche rows move under ablation. (2) **The in-merit revealed-availability
filter is INTACT at HEAD**: the attractive silent-degradation story
(`high_load_mask` returns `None` on a missing EIA-930 BA file, and BLOAT-S2
untracked "the eia-930 per-BA long files") is **REFUTED** — `NYIS
hourly.parquet` is present, covers 2015–2026, and returns 1,172/1,194/1,233/
1,225 high-net-load hours for 2019/2023/2024/2025.

**ON THE TRANCHE ARTIFACT: R3 MULTI-CHANNEL, R4 BIT-EXACT.** The pre-registered
R3 metric (rows matching committed `online_hours` within 24 h, of 78; dominant
at ≥ 60) returns control **44**, no-derate **47**, no-parasitic **44** —
**MULTI-CHANNEL**, reported at the bar set in advance. But **R4 PASSES
EXACTLY**: ablating the outage-derate overlay restores S A Carlson (2682)
`ST_GAS` to the committed **3,913 online hours and `median_cf` 84.4 — the
committed values bit-for-bit** — from a control reading **120 h at the
physically meaningless clip cap of 150.0**. `avail_cap = nameplate × avail_mult`
feeds BOTH the online test and the `finite` mask, so a derate deletes hours
outright; the committed tranche artifact was derived when the extract carried
**no (2682, ST_GAS) windows** and the committed extract now carries **55**.
**THE TWO COMMITTED INPUTS ARE MUTUALLY INCONSISTENT — the tranche artifact is
derated against an OLDER outage extract than the one the solve reads.** That,
not "drift", is the real blocker. Channel C is **3 rows** of HEAD's own fleet
reconciliation (7314, 10190, 56196, "corrupt summer-capacity rows — reconciled"),
where **HEAD is right**.

**R5 DISCHARGED AS PRE-REGISTERED, WITH NO SCORE CONSULTED IN CHOOSING THE
BRANCH.** R5-(iii) for the tranche artifact (MULTI-CHANNEL → re-baseline) and
R5-(i) for the routing channel (a nameable defect → repair and re-derive) land
in the SAME act, and better than either alone: **the `-perunit-` companions ARE
the re-baselined inputs, selected by a DEFAULT-OFF gate rather than by
overwriting the incumbents** — so the incumbent artifacts stay byte-untouched,
the keeper is unchanged, and the re-baseline is an ADJUDICATED single delta
rather than a silent import.

**WHAT WAS BUILT — nyiso-175b's handed-forward item 3, which it listed as NOT
BUILT.** `ScenarioConfig.campd_per_unit_attribution`, default-off, **ONE gate
over BOTH artifacts** (rule 19 `[R-ONE-MECH]`: a tranche row's statistics are
computed over an outage-derated denominator, so the two must move together, and
a single field makes that structural rather than a discipline a successor could
forget). `campd_bins.thermal_tranche_csv_for_iso` is the single resolver and
**all 11 hardcoded call sites** now route through it, threaded from config via
`assembly.py` / `arrays.py` / `offer_curves.py` / `reserves/spec.py`;
`unit_outage_csv_for_iso` gains `per_unit_crosswalk`, which **takes precedence
over** the narrower `-unitroute-` companion (measurably wrong where the two
disagree, nyiso-175b K3). `--campd-per-unit-attribution` reaches both
`solve_and_persist` and `run_replay_bundle`, and lands in `run_config.json`
(rule 24). **COMPLETENESS IS CI-ENFORCED, NOT ASSERTED**
(`tests/unit/data/test_campd_per_unit_attribution.py`, 10 tests): no `src/`
module may read the tranche artifact outside the resolver, and no resolver-using
reader may lack the selector — the invariant that stops a solve reading **two
artifact vintages inside one LP**, a failure mode nothing in the output would
reveal.

**THE COUPLING GAP nyiso-175b DISCLOSED IS CLOSED IN THE DERIVER**, not in
prose: `derive_thermal_tranches` now sources its derate from the per-unit outage
companion under `--per-unit-attribution`. **BOTH NYISO COMPANIONS REGENERATED
ON THE CONSISTENT BASIS** (rule 23, citing the defect and never a residual):
the outage companion over the committed extract's own **2019–2026** span,
**1,996 → 4,928 windows** (the 2023-2025-only companion would have silently lost
every window beginning in 2022 and running into 2023, since
`unit_outage_derate_factors` clips to the run year), **byte-identical on
re-derivation**; and the tranche companion against that repaired extract,
moving **15 of its 85 rows** (8906 `ST_GAS` 17,027 → 8,823 h). **ONE NEGATIVE
RESULT AT FULL STRENGTH:** the physically-impossible `median_cf > 100` census
goes **10 → 11** (50978 `CC_REGULAR` enters at 141.4 as the derate bites at a
sparsely-metered plant). Rule 14 `[R-ACCURATE]` binds: the accurate construction
is KEPT and the artefact RECORDED, never reverted.

**AND THE REPRODUCIBILITY GAP IS STRUCTURALLY CLOSED GOING FORWARD, FOR EVERY
ISO:** `derive_campd_unit_outages` now writes a **provenance sidecar** beside
every extract it emits — year span, `min_outage_days`, routing flags, in-merit
and full-stop thresholds, row count, year histogram. **The absence of exactly
this record is why the session's headline comparison was ambiguous in the first
place.**

**EXPECTED VALUE, UNCHANGED AND NOT OVERSOLD.** The per-unit repair's C3a-2025
expectation is **~ZERO** — both East River bins carry heat rate 7.4205 and the
same delivered gas, so moving energy between them changes no unit's marginal
cost and no marginal price — and nyiso-175b's gate **K5, which FAILS a large
favourable C3a move, is carried forward verbatim as R6**. This is a rule 1
`[R-STRUCT]` C1 / representation repair plus an input-integrity repair, **never
a C3a lever**. The re-baseline itself has **no pre-registered sign**.

**THE A/B WAS SOLVED, SCORED AND REGISTERED — AND IT FAILS ITS OWN
PRE-REGISTERED GATE.** Two three-year bundles, one invocation each:
`2026-09-02-nyiso-176-rebaseline-control` (gate OFF) and
`2026-09-02-nyiso-176-perunit-attribution` (gate ON). **THE CONTROL IS A RESULT
IN ITSELF AND PREVIOUSLY UNMEASURED: a byte-faithful replay of the keeper at
HEAD reproduces it BIT-IDENTICALLY — 0 of 52,560 hourly zonal prices differ in
EVERY year, max absolute class-energy delta 0.000 TWh.** HEAD has not drifted
for NYISO since 2026-08-30, the keeper is reproducible from its own recipe, the
A/B is an unambiguous single delta, and nyiso-175b's stated reason for a control
leg is retired. **R6 (carried verbatim from K5) FAILS a large FAVOURABLE C3a
move, and that is exactly what the arm produces.** C3a-2025 — the keeper's SOLE
load-bearing failure — goes **−11.5 % → −6.7 % and PASSES** (58.81 → 61.96
against an actual 66.43), paid for with **C3a-2023 blowing out to +17.4 %**
(37.86 vs 32.25, a FAIL where the keeper PASSED), a **NEW load-bearing C1 MODEL
MISS** (CC_REGULAR 2024, 38.77 vs 34.06) and a **NEW C3b failure** (2023 NRMSE
0.215). **Target grade 5 → 3, fails 2 → 4.** Class energy moves `ST_GAS`
−5.28 / −2.39 / −1.05 TWh into `CC_REGULAR` +3.29 / +1.56 / +0.32 and `CC_CHP`
+1.22 / +0.96 / +0.44; load-weighted price +14.71 / +7.32 / +5.36 %. **REJECTED
AS A KEEPER CANDIDATE — and explicitly NOT rejected as an input.** Rule 14
`[R-ACCURATE]` binds, as this session's own prereg stated before any of it was
measured: a more accurate input that makes the backcast worse is a **discovered
bug elsewhere**, never a reason to revert. Something was silently compensating
for the mis-attribution and the A/B has exposed it. **Leading suspect:
Ravenswood (2500)** — its 1,724.8 MW `ST_GAS` bin loses its committed share
(10.7 → 20.3) to a NEW 222.2 MW `CC_REGULAR` bin at committed 70.0, while its
three steam boilers' outage windows move `CC_REGULAR` → `ST_GAS` so the steam
bin takes its own derates for the first time; both push the same way, and
`ST_GAS` is where the −5.28 TWh comes from. **The year signature is itself
diagnostic and unexplained**: 2023 is the only year that OVERSHOOTS, and it
overshoots hardest, while 2025 — the year the keeper misses low — improves. Both
determinations read NOT-YET; the governance gate is UNATTESTED (a replay bundle
carries no attestation) but the arm's load-bearing failures do not depend on
that. **Keeper `2026-08-30-nyiso-159-loss-surface` UNTOUCHED.** DISCLOSED: both
bundles' `run_config.resolved_inputs` predate this branch's provenance fix, so
the arm's block names the incumbent extract though it read the `-perunit-`
companion; the four consumed shas are recorded in the finding §8a.4, and the
gate's effect is independently corroborated (arm derates 305 plant-tranches in
2023 vs the control's 278; East River's committed share moves from the steam bin
32.0 to the turbine bin 30.1 with `chp_pmin_cf` 30.0 → 1.5).

**HANDED FORWARD.** (1) **The root cause of the arm's degradation** — start at
Ravenswood and at the 2023-only overshoot; the cheapest instrument is arming the
two halves SEPARATELY as a diagnostic (forbidden for a keeper by the single-gate
design, legitimate for attribution), and no control leg is needed since the
keeper reproduces bit-identically.
(2) **The cross-ISO question, deliberately not opened here (rule 25):** nothing
in the diagnosis is NYISO-specific — the `fac_group` short-circuit's own
docstring calls it "a deliberate pjm-75 conservatism" and **neiso-99 already
carved a rule 14 exception out of it**, so the defect family is known in at
least two other ISOs and was handled per-plant rather than by the general rule.
Each `U` cell states its own transfer question and **all four are answerable
from committed bytes without a solve.** (3) Every other ISO's tranche artifact
still has the xiso-6 descriptive-backfill sidecar that makes no claim about what
HEAD would emit; the outage half is now self-recording and the tranche half is
not. (4) `--fix-anchors` on the shared matrix — the standing governance round;
this session's new field adds to the existing drift and deliberately did not run
the fixer, which would rewrite every row of a file five other lanes edit.

**Tests:** `tests/unit` + `tests/iso/nyiso` **1,792 passed / 17 skipped**. The
**14** `tests/regression` + `tests/scoring` failures **reproduce identically on
a clean stash of HEAD** (the brief named one; there are fourteen). Matrix:
`check_mechanism_matrix.py` no errors; `campd_per_unit_attribution` added to the
base file and to **all six** ISO shards (rule 28 duty c), NYISO at **R**
(tested here and rejected on the pre-registered gate), ERCOT **n/a** (no
thermal-tranche artifact), the other four **U** (rule 28(d) — no verdict crosses
an ISO boundary).


## 2026-09-02 — nyiso-177: the accurate CAMPD attribution is EXONERATED — nyiso-176's degradation is 100 % the AVAILABILITY basis the same gate imports alongside it, and the merit-order-guarded companion reproduces the keeper's envelope `np.array_equal`; still not promotable, and the real object (a 0.50–0.56 over-booked ST_GAS envelope, IN THE KEEPER) is sized for the first time

**Two solves, both registered, NEITHER PROMOTED.** Keeper unchanged:
`2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}. Full record:
`docs/FINDING-nyiso177-availability-basis-root-cause-2026-09-02.md`; gates
`results/calibration/PREREG-nyiso177-degradation-root-cause.md`, committed
(`966da189`) **before any measurement** and amended (`499430f4`) **before any
solve**, with no score of any kind consulted in the amendment.

**THE OBJECT, ANSWERED.** nyiso-176 armed `campd_per_unit_attribution` — the
accurate per-unit attribution — the backcast got worse, and rule 14
`[R-ACCURATE]` handed the degradation forward as a discovered bug. **The
accurate input is not the bug.** That gate is ONE field over TWO artifacts, and
arming it imports the attribution repair **together with an unguarded HEAD
re-derivation of the availability envelope**. Separating them convicts the
second of **all** of it.

**THE MEASUREMENT (phase 0, zero solve).** `(2500, ST_GAS)` Ravenswood,
1,724.8 MW, falls from **0.772 → 0.129** mean availability in 2023 — about
**9.7 TWh of capacity-hours removed** against an ISO-wide `ST_GAS` fall of
−5.28 TWh — with Port Jefferson 0.925→0.289, Arthur Kill 0.855→0.360 and five
plants going 1.000 → 0.008–0.54. **nyiso-176's "unexplained year signature" is
explained and closed**: the absolute monthly price delta is $4.14 / $2.51 /
$2.95 on base levels of $31.73 / $36.27 / $55.81 (a denominator, not a
mechanism), and the residual heterogeneity is the keeper's own Ravenswood
availability path 0.772 / 0.465 / 0.297.

**G1 PASSES — a rule-19 `[R-ONE-MECH]` stack, repaired.**
`outages._FLEET_GROUP_OVERRIDE = {2500: "ST_GAS"}` enumerates per plant the very
defect the general crosswalk repairs, and under the arm it still fires on the
repaired rows: it pins `(2500, CC_REGULAR)` at availability **1.000** in every
year where the repaired routing measures **0.823 / 0.918 / 0.923**, while
`(2500, ST_GAS)` moves by at most 0.012. Disarmed on the per-unit path and
**only** there — on the incumbent extract it is load-bearing (without it
`(2500, ST_GAS)` reads 1.000 and the whole plant's downtime lands on a 222.2 MW
CC bin). Rule 24 `[R-REGISTRY]` names hardcoded per-plant dicts in `data/`
explicitly; this removes one on the repaired path.

**G2 FIRES, ON THE KEEPER TOO — and this is the session's largest result.** The
NYISO `ST_GAS` overlay books **0.536 / 0.560 / 0.501** of the bin-capacity-year
as mechanical outage **in the keeper** (0.794 / 0.742 / 0.688 under the
unguarded arm), against a documented EFOR+planned norm of **0.10–0.15**. The
model still runs the remaining capacity at ~3× the fleet's measured annual CF.
**The overlay is carrying economic idling the offer curves should be
producing.** Nothing here repairs it; it is sized and handed forward.

**G3 IS RECORDED FAILED, on both legs, and the consequence is honoured.** Leg
(a) asked for "strictly between" and the guarded extract lands **ON** the
keeper's value to 16 significant figures. Leg (b)'s 0.40 threshold **measures a
pre-existing keeper property**, so no guarded construction could have passed it
— a defect in the gate's own construction, disclosed in the amendment. **The
merit-order guard is NOT armed as a repair of the availability envelope and no
such claim is made.**

**THE BRIEF'S OWN ITEM-(1) INSTRUMENT IS REFUTED, for zero solves.** A
`--no-fullstop-override` companion was derived and measured: its availability
envelope sits **FURTHER** from the keeper's (nameplate-weighted L1 **0.1055**)
than the unguarded arm's (**0.0943**), moving 41 bins by >0.02 in 2023 in both
directions. The `--merit-order-guard` companion sits at **0.0006** and is
`np.array_equal` to the keeper on `(2500, ST_GAS)` in all three years. **The
confound is ECONOMIC LAY-UP, not the full-stop override.** G3′ (metric and both
thresholds fixed before any solve) qualifies the guarded companion and
disqualifies the other two.

**THE A/B — a 2 × 2, every cell a single delta from a neighbour.** Control = the
committed keeper (bit-identical at HEAD per nyiso-176 §8a.1; no control leg
solved).
`2026-09-02-nyiso-177-destack-unguarded` (`nyiso177_destack_B1`) reproduces
nyiso-176's arm at the criterion level **exactly** — grade 3, fails 4, price
38.01 / 40.49 / 62.00 against the arm's 37.86 / 40.42 / 61.96. **Repair 1 is not
LP-inert** (37,557 of 52,560 hourly zonal prices move in 2023, max $7.84) but it
moves **no criterion**. `2026-09-02-nyiso-177-vintage-matched`
(`nyiso177_vintage_B1p`) adds the guard: **grade 4, fails 3**, load-bearing
**C3b RETURNS TO PASS**, price returns to the keeper's (32.97 / 37.79 / 58.99 vs
33.01 / 37.66 / 58.81; actual RT 32.25 / 38.12 / 66.43), C2 / C4 / C8 PASS
throughout.

**GATE R6 / K5 IS SILENT, and that is the point.** B1′'s C3a-2025 is **−11.2 %**
against the keeper's −11.5 %. The representation repair's ~ZERO C3a expectation
— carried verbatim from nyiso-175b K5 through nyiso-176 R6 — **is confirmed by
the one leg that could test it cleanly**. Against the keeper B1′ moves ~80 % of
hourly zonal prices at a mean |Δ| of only $0.23 / $0.27 / $0.27: a real
redistribution at an unchanged level.

**NEITHER IS PROMOTED, and the reason is stated rather than deferred.** B1′
fails the promotion bar's leg (a) — it is three objects (attribution + repair 1
+ guard), not one — and it is **strictly worse than the keeper** (grade 4 vs 6,
fails 3 vs 2) on one load-bearing cell: **C1 2023 `ST_GAS` +3.86 TWh against the
keeper's +3.33**, marginally outside a band the keeper sits marginally inside.
Its mechanism IS stated: the repaired attribution measures a **higher committed
share** on Northport (10.7→15.3), Bowline Point (16.5→20.1), Danskammer
(9.9→17.8) and Astoria (`online_hours` 11,405→17,027), outweighing Ravenswood's
10.7→6.5 — the incumbent artifact diluted each plant's conduct across a
facility-summed denominator including its non-steam units. Under rule 14 that
measured change **stays**; under rule 1 the promotion is an owner call, not this
session's, and it is put forward as a candidate rather than taken.

**BUILT.** `ScenarioConfig.campd_outage_merit_order_guard` (GATED default off,
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + the default-string registry in the
same commit, reaching `run_config.json`), selecting the `-perunitmerit-` pair
through the new `campd_attribution_selectors` accessor, which returns the
`(per_unit, merit_guard)` PAIR so no call site can take one without the other
(rule 19 — a tranche row's statistics sit on an outage-derated denominator).
`derive_thermal_tranches --merit-order-guard`. **Zero free parameters**:
`MERIT_OOM_FRAC` / `MERIT_RCC_PCTL` / `FULL_STOP_OVERRIDE_*` untouched at their
committed values (stop condition S1). CI contract extended by 12 tests pinning
the same five properties the per-unit gate has, plus repair 1's two-sided
scoping.

**LINES CLOSED.** (x) the nyiso-176 attribution rejection, **corrected on its
facts** — the cell moves R → O and the repair is exonerated; (y) the
"unexplained year signature", explained as a denominator plus the keeper's own
Ravenswood availability path; (z) `--no-fullstop-override` as a confound-removal
instrument, refuted at artifact level with a stated metric.

**HANDED FORWARD, none scoped here.** (1) **The over-booking** — 0.50–0.56 of
the `ST_GAS` capacity-year booked as outage in the keeper against a 0.10–0.15
norm, with the model running the remainder at ~3× measured CF: an **offer-side**
object, not an availability-side one. (2) **The missing rung, one solve**: a leg
arming the guard **alone** on incumbent routing would make it a true single
adjudicated object and satisfy promotion-bar leg (a); that companion does not
exist yet and deriving it is unrestricted data prep. (3) **C1 2023 `ST_GAS` is
now a named, sized, single object** — the keeper passes that criterion by ~0.5
TWh of margin the attribution defect was supplying. (4) The four `U` cells
transfer without a solve. (5) `mustrun_layup_window_mask` now has a matched
companion the resolver cannot yet reach.

**Rule 22 `[R-HOLDOUT]`**: every solved, scored and registered year is
2023 / 2024 / 2025. Deriving multi-year inputs is data prep, which the rule does
not gate. NYISO's `complete` marker was **not** requested; NYISO remains absent
from both markers and the holdout spend freeze is untouched.

### 2026-09-02 — nyiso-177 ADDENDUM: the owner rules, and `2026-09-02-nyiso-177-vintage-matched` IS PROMOTED

The entry above was written and pushed recommending **against** a promotion this
session could take on its own authority (its promotion-bar leg (a) fails: the
arm is three objects, not one). The owner then ruled, in session and verbatim:

> *"Is this a recommended keeper candidate? If so plz promote. If structural
> integrity improves but gates regress that may still be a keeper.."*

— the standing-disposition formula of the nyiso-155 / -157 / -159 promotions.
**NYISO keeper → `2026-09-02-nyiso-177-vintage-matched`** (bundle
`results/calibration/nyiso177_vintage_B1p`), superseding
`2026-08-30-nyiso-159-loss-surface`. **The recommendation against it is left
standing, unedited, in the entry above and in §6 of the finding**; the ruling is
recorded as an **OVERRIDE**, never as the pre-registration's own verdict.

**DETERMINATION NOT-YET, target grade 5, fails 3** {C1, C3a-2025 −11.2 %, C3c},
against the superseded keeper's grade 6 / fails 2. **The promotion narrows
nothing and costs one load-bearing cell** — C1 2023 `ST_GAS` +3.86 TWh against
+3.33 — and the honest reading is the **nyiso-155 precedent exactly**: the
superseded keeper passed that cell on **~0.5 TWh of margin the attribution
defect was supplying**. Mechanism stated, not residual (Northport committed
10.7→15.3, Bowline 16.5→20.1, Danskammer 9.9→17.8, Astoria `online_hours`
11,405→17,027, outweighing Ravenswood 10.7→6.5). C2 / C3b / C4 / C6 / C8 PASS;
same six D-4 rows, identical gates, zero new forcing mechanisms; DOF 13 /
`n_residual` 6 carried verbatim (both repairs are zero-scalar).

**THE FOUR STRUCTURAL GAINS the promotion rests on**, each independent of any
score — and the last two are ones the pre-ruling write-up **under-weighted**,
corrected in finding §10.2: (1) **accuracy** (East River's `ST_CHP` row carried
the *turbine* half's conduct on the *steam* half's denominator and correctly
disappears; S A Carlson `ST_GAS`→`CT_PEAKER`; Ravenswood's steam/CC split
becomes real); (2) **no off-registry channel** — the hardcoded
`_FLEET_GROUP_OVERRIDE` per-plant dict is disarmed on the repaired path, where
it was a rule-19 stack pinning `(2500, CC_REGULAR)` at 1.000; (3)
**REPRODUCIBILITY** — the superseded keeper's outage extract has a **null
`derive_invocation`** and cannot be reproduced at HEAD at any flag setting
(nyiso-176 §4); (4) **INTERNAL CONSISTENCY** — nyiso-176 R4 proved bit-exactly
that the committed tranche and outage artifacts sat on **different availability
bases**, and `campd_attribution_selectors` now makes one basis structural rather
than a discipline a successor could forget.

**GATE R6/K5 STAYED SILENT**: C3a-2025 −11.2 % vs −11.5 %. No price claim is
made or banked, and C3a-2025 remains the lane's standing open gate, unmoved.

**C6 was attested AT the promotion with every premise COMPUTED, never typed**
(`scripts/gen_nyiso177_attestation.py`, which refuses to write on any failed
leg): **G-CONTROL** re-measures the same-HEAD control's bit-identity to the
superseded keeper (0 of 52,560 hourly zonal prices differ in all three years,
max |Δp| 0.0) — the premise that licenses using that control as the delta
baseline; **G-DELTA** confirms the config delta is exactly the two fields with
nothing riding along; **G-INPUTS**, **G-DOF**, **G-ENGAGE** pass. With C6
attested both legs re-score one grade higher than first reported.

**NO MARKER DUTY**: NYISO holds no `complete` marker (declared 2026-07-31,
**withdrawn** 2026-08-30), so rule 22 D-5(b) imposes no re-key and none was
performed. NYISO stays absent from both markers; the holdout spend freeze is
untouched; every solved, scored and registered year is 2023–2025.

**OPEN GATES AFTER THE PROMOTION**: C3a-2025 (unchanged, owner-court), the
ledgered-class C3c (not lone, so it stands), **NEW — C1 2023 `ST_GAS`**, and the
**outage over-booking this session sized for the first time** (`ST_GAS`
`booked_share` 0.53–0.56 of the capacity-year *in the keeper*, against an
EFOR+planned norm of 0.10–0.15; PREREG gate G3 **recorded FAILED** on it). The
over-booking is the lane's next lever and it is an **OFFER-side** object.

## 2026-09-02 — nyiso-178: the `ST_GAS` availability envelope is NOT BINDING IN ANY YEAR IN EITHER DIRECTION — nyiso-177's offer-side type is CONFIRMED on the LP's own envelope, the merit guard's non-effect is DIAGNOSED to a single cause, and the natural offer-shape successor is REFUTED for zero solves

**ZERO SOLVES. Keeper UNCHANGED:** `2026-09-02-nyiso-177-vintage-matched`,
determination **NOT-YET**, target grade 5, fails 3 {C1-2023 `ST_GAS`,
C3a-2025 −11.2 %, C3c}. **No parameter touched, no band swept, no arm built, no
run registered — by the pre-registration's own stop condition S3, which fired.**
Full record: `docs/FINDING-nyiso178-offer-side-idling-2026-09-02.md`; gates
`results/calibration/PREREG-nyiso178-offer-side-idling.md`, committed with the
probe (`31180c9b`) **before either ran**; probe
`scripts/probes/nyiso178_offer_side_idling.py` →
`results/calibration/_nyiso178_offer_side_idling.json`.

**THE OBJECT, AND WHY THE TYPE WAS TESTED RATHER THAN INHERITED.** nyiso-177 §7.1
sized an over-booked `ST_GAS` outage envelope (0.50–0.56 of the bin-capacity-year
against a 0.10–0.15 EFOR+planned norm) and handed it forward with a **stated
type** — "an offer-side question, not an availability-side one". The type is the
whole disposition, because the two have disjoint lever sets, so this session
gated it.

**G1 ⇒ OFFER-SIDE, and the instrument had to be REPAIRED to say so honestly.**
PREREG §5.3 had already corrected §5.2's envelope from a difference to a product
(`availability = (1 − WEFOR(age) − DERATE(age)) × ufac`, `arrays.py:1097`) by code
reading, before any execution — a correction that mattered, because the additive
form would have biased G1 toward the brief's preferred answer. **The corrected
reconstruction was still invalid and its own output said so**: model `ST_GAS`
EXCEEDED it at p99 (1.025 / 1.062 / 1.065), which a ceiling cannot do. Rather
than gate on a falsified bound, the envelope was rebuilt by CALLING THE ENGINE
(`load_or_synthesize_bins` → `bins_to_fleet` → `generators_to_fleet_arrays` on
the keeper's own `ScenarioConfig`) — and the exact envelope is TIGHTER than the
overlay-only bound, i.e. the swap makes OFFER-SIDE harder to reach, not easier.
On it: mean availability **0.384 / 0.364 / 0.416**, envelope 29.96 / 28.40 /
32.43 TWh, model 12.00 / 9.80 / 10.01 against actual 8.14 / 9.91 / 13.71, and the
model sits at its own ceiling in **0 / 0 / 4 hours of 8,760** (0.00 / 0.00 /
0.05 %), mean utilisation **0.391 / 0.315 / 0.286**.

**THE DECISIVE LINE — it does not bind in the SCARCITY hours either.** By actual
RT LBMP decile, the model is at its envelope in **zero hours of the top decile of
any year**. In 2025's top decile (**\$176.25** mean) the envelope is **3,658 MW**
and the model runs **1,442 MW** — **2.2 GW of already-derated, in-envelope steam
goes unoffered or over-priced**, while the measured fleet averages ~2,597 MW
(CAMPD gross). Across the top three deciles the model is FLAT (1,603 → 1,429 →
1,442 MW) as price runs \$70 → \$176. **The whole measured-availability-input
family is therefore provably inert against `ST_GAS`, ex ante and in BOTH
directions**: tightening cannot cure the 2023 +3.86 TWh over-run (60 % slack) and
loosening cannot cure the 2025 −3.70 TWh under-run (the slack is already there).
The nyiso-173 CC disposition, now established for steam. **Re-open condition,
measurable: a keeper whose `ST_GAS` utilisation actually reaches its envelope.**
**ROBUSTNESS, reported because it could have flipped the gate:** the LP's
`ST_GAS` bins carry a **stamped `online_year` of 2010**, so
`THERMAL_AVAILABILITY`'s 30-year age escalation never fires for a 1951–1977 NY
steamer; re-scaling to true EIA-860 vintages tightens availability to
0.312 / 0.294 / 0.338 and hours-at-envelope to 154 / 234 / 296 (1.76 / 2.67 /
3.38 %) — **`MIXED`, never `AVAILABILITY-SIDE`.**

**G2 DISCHARGED — the guard is working exactly as designed, and that is WHY it
removes nothing.** Attributing the `ST_GAS` window-hours the keeper-armed guard
KEPT across the three fail-safe exits its own code defines: **0.8083** are PRICED
windows whose `out_of_merit_share` falls below `MERIT_OOM_FRAC` = 0.9, 0.1917 are
panel-unidentified units (`2480:2`, `2682:9`, `2682:10`, `8906:CT0001`), 0.0000
unpriceable, 0.0000 no-panel — a single cause at 0.81 against a 0.80 bar. The
guard is not idling: it **REMOVED 449 windows / 221,016 window-hours at mean
out-of-merit 0.989**. What it KEPT is 450 windows / 362,736 window-hours at mean
**0.173, MEDIAN 0.000** — in the median kept window the unit was in merit in
every priceable hour and was off anyway, which against a fail-safe test reads
mechanical. **The residual over-booking is NOT reachable by this guard at its
committed constants, and it is not a defect in the guard.** No constant touched
or swept (rule 23).

**G3 NEITHER — THE NATURAL SUCCESSOR IS REFUTED FOR ZERO SOLVES, and S3 fires.**
The arm was pre-specified in full: an `ST_GAS` duty curve, the class sibling of
the adjudicated keeper `chp_layup_duty_curve` (nyiso-149), disjoint by class
scope, zero new price constants, whole-class membership so no cohort DOF. It was
conditional on the defect being one of offer SHAPE. Measured on shares within
actual-RT-LBMP bands: model bottom-half share 0.383 / 0.358 / 0.365 against the
measured fleet's 0.345 / 0.319 / 0.317 — a ratio of only **1.108 / 1.121 /
1.152** against a ≥ 2.0 bar — and the model is **LESS** top-heavy in every year
(0.156 / 0.146 / 0.126 vs 0.190 / 0.181 / 0.150), not more. The LEVEL branch
fails too (max per-band departure 0.181 / 0.190 / **0.389**). **Not a duty-role
defect; a duty curve is the wrong instrument and no solve was spent finding out.**

**G4′ DISCHARGED — no unattributed `ST_GAS` forcing channel.** Eleven armed
candidates from the list fixed before the cross-check; every one either carries an
`ST_GAS` D-2 row (`reliability_floor`, `nyiso_gas_commitment_bridge` + six legs)
or is inert by class scope (`chp_steam_following`, `chp_layup_duty_curve` — CHP
groups only). No D-2 `ST_GAS` mechanism was missing from the list either. Forced
share, **report only**: 0.177 / 0.237 / 0.198 — **~80 % of the class's energy is
economic clearing**, which is what makes the headroom an offer statement.

**G5 — a rule 19 `[R-ONE-MECH]` availability STACK is FLAGGED, and is also
PROVABLY INERT.** `ST_GAS` unavailability is derived by two mechanisms for one
phenomenon, **multiplied**: the age-escalated statistical NERC-GADS layer
(`THERMAL_AVAILABILITY["ST_GAS"]`, the one `arrays.py:690` calls "fitted to
ERCOT's once-through steamers and > 2× every other thermal class") and the
measured CAMPD overlay, with **all three relief fields `None`**
(`wefor_residual`, `gas_st_wefor_base_override`, `wefor_residual_groups`).
Composed 2023 by plant: Roseton 0.050, Bowline 0.124, Astoria 0.155, Danskammer
0.181, Northport 0.433, E F Barrett 0.567, Ravenswood 0.641, Arthur Kill 0.693,
Port Jefferson 0.750, Greenidge 0.780. Both things are reported: it is a genuine
stack, **and** G1 makes relieving it move ZERO `ST_GAS` energy. **Stop condition
S6 forbade an availability-loosening arm ex ante; G1 converts that guardrail from
an argument into a measurement.** Nothing touched (rules 21, 23).

**LINES CLOSED.** (a) the measured-availability-input family against `ST_GAS`, in
both directions, with a stated re-open condition; (b) the merit-order guard as a
repair for the residual over-booking, on a measured single-cause attribution;
(c) the `ST_GAS` duty curve as this object's successor.

**HANDED FORWARD, none scoped here.** (1) **The object, RE-TYPED**: an offer
**POSITION** object — 2023 near-uniformly multiplicative (band ratios 1.23 →
1.01, converging at the top), 2025 top-weighted deficit (0.92 → 0.555), class
saturating flat at ~1,450 MW above \$70/MWh against a ~3,650 MW envelope and a
~2,500 MW measured fleet. Enumerate first (rule 19): downstate zonal gas basis +
`dual_fuel_switching` in the dear hours, the UN-GROUNDED `ST_GAS` `peak` 4.2
multiplier, `gas_st_committed_hr_mult` 1.32. `gas_st_startup_cost` stays
DO-NOT-REDO. (2) **The missing rung is STILL UNSPENT and its cost is now
specified**: it is not a flag flip — `campd_attribution_selectors` forces
`merit_guard` False without `per_unit` by design and both resolvers name only a
`-perunitmerit-` companion, so it needs a `-merit-` PAIR on incumbent routing,
both resolvers extended, and the selector relaxed while preserving the pairing
invariant. (3) **`mustrun_layup_window_mask`'s NYISO census is now measured** —
449 `ST_GAS` windows / 221,016 window-hours at mean out-of-merit 0.989 — but
`unit_layup_csv_for_iso` still resolves only the unsuffixed name, and G4′ bounds
what the mask can move on a class that is 80 % economic. (4) **A newly named
data-fidelity gap**: the LP's `ST_GAS` bins carry a stamped `online_year` of 2010
against EIA-860's 1951–1977. (5) C3a-2025 unmoved, owner-court, not opened.

**WHAT IS NOT DELIVERED, stated without softening.** No keeper, no candidate, no
run, no repair. C1-2023 `ST_GAS` is exactly where nyiso-177 left it. **The
over-booking is shown INERT, which is a lesser result than fixing it** — it is
still 3.5–5× a documented norm and remains wrong on the merits even though
nothing downstream currently depends on it. §9's re-typed object is a
**specification, not an identification**.

**Rule 15:** no solve ran, so nothing is registered on the dashboard — by design
(S3), not omission. **Rule 22 `[R-HOLDOUT]`:** every year read is 2023 / 2024 /
2025; NYISO is absent from both `complete` and `final`; **no marker was
requested**; the holdout spend freeze is untouched. **Rule 25:** NYISO only.
**Rule 28 (b):** four NYISO cells annotated — `campd_outage_windows` stays **`K`**,
`campd_outage_merit_order_guard` stays **`K`**, `offer_curve_by_group` stays
**`K`**, `mustrun_layup_window_mask` stays **`U`** — **no verdict moves and no
field changed**; guard exit 0, shard passes `node --check`. Also re-stamped
`docs/mechanism-testing-matrix.md` §5.5, whose prose header still named the
nyiso-159 keeper (the promoting session's duty, missed; CI was warning on it) and
whose NYISO lever queue now carries this session's three closed lines — the prior
header is preserved beneath, unedited.

---

## 2026-09-03 — nyiso-179: the `ST_GAS` offer POSITION is refuted as the governing object; all three of the brief's starting points close; ZERO SOLVES

**Keeper UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`**, determination
**NOT-YET**, target grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
No parameter touched, no band swept, no arm built, no run registered — by the
pre-registration's own stop conditions **S1, S2 and S3, all three of which
fired**. Gates: `results/calibration/PREREG-nyiso179-st-gas-offer-position.md`,
committed with the probe at `15f2d3e8` **before either ran**; §8 amendment at
`5264cff2` **before the corrected run**. Evidence:
`docs/FINDING-nyiso179-st-gas-offer-position-2026-09-03.md`, machine records
`_nyiso179_st_gas_offer_position.json` + `_nyiso179_g1_robustness.json`.

**THE INSTRUMENT.** The **exact LP marginal-cost array**, rebuilt by calling the
engine — nyiso-178's validated `lp_fleet` → `resolve_fuel_prices` →
`assemble_mc` on the keeper's own `run_config.json`. `resolve_fuel_prices`
applies the F923 overlay, the NYISO zonal basis and the dual-fuel oil cap inside
one call in that order (read from the code, not assumed), and the keeper carries
`carbon_price = nox_price = so2_price = 0`, so `mc = hr × delivered fuel + vom`
exactly. Zero solves.

**THE THREE STARTING POINTS, ALL CLOSED ON MEASUREMENT.**
**(1) G0 `INERT`** — `gas_st_committed_hr_mult` 1.32 is consumed at exactly one
site, `offer_curves.split_gas_tranches`, reachable only from the non-CAMPD limb
(`assembly.py:1912`, the limb whose coal sibling was deleted as unreachable at
ercot-188); this keeper is `use_campd_bins=True`, so it cannot price a single MW.
Every committed band measures `base_hr × 1.05`. The caiso-239 transfer is
declined twice over — NYISO has **0 of 11** `ST_GAS_PEAKER_PLANTS` members, and
its own `avg_committed_p50` 1.104 is **already registered** as `phys_committed`.
A NYISO registry entry would be an unreachable entry (rule 24), so none added.
**(2) G3 `PEAK-EXONERATED`** — in 2025's top decile the un-grounded `peak` 4.20
holds 0.336 of the class's out-of-the-money MW (bar 0.40) and is OOM in 0.806 of
hours (bar 0.90). At mean mc \$415.9 against a \$176.25 price it is 2.4× the
price and never was the carrier, while **700 MW of econ-band steam sits OOM at
\$112**. It stays un-grounded (no peak column exists to ground it from); the
prereg's pre-declared refusal to pick a value from the residual held.
**(3) G2 `LINE CLOSED`** — rule 19 `[R-ONE-MECH]` executed: the **armed**
oil-parity cap reaches **0.834** of `ST_GAS` capacity (7,424 / 8,902 MW) and
bites hardest exactly where predicted — 2025's top decile, 0.0875 of bin-hours
capped at **\$2.371/MMBtu** relief, delivered gas \$11.76 → \$9.39. No new
fuel-side mechanism proposed.

**G1 `NOT-OFFER-GOVERNED` — the type itself is refuted.** Against its own P1
zonal prices the model dispatches only **0.767 / 0.522 / 0.740** of the `ST_GAS`
its own offer puts in the money (median R 0.775 / **0.448** / 0.816 against a
0.70 floor) — **3.84 / 9.09 / 3.99 TWh a year** of in-the-money steam unrun.
Robust four ways: **not** a marginal-tranche artifact (marginal capacity is
3.1–4.6 % of ITM; no ε in 0–\$5 rescues it), **not** reserve holding (a family
binds in 21 / 11 / 38 h of 8,760 against 6,008 / 7,911 / 5,144 withholding
hours, overlap 0 / 2 / 0 — independently reproducing nyiso-152), **not** the
P0/P1 bid-cost gap (`commitment.py:312` skips the `gas_st` limb and the keeper
carries `gas_st_startup_cost=False`, so the ST_GAS markup is **identically
zero** and the reconstruction **is** the P1 bid cost — a structural close), and
coherent in the zero-ITM hours.

**THE SUBSTANTIVE RESULT — the 2025 top-decile decomposition** (measured 2,597
MW vs model 1,442 MW): **62.4 %** of the 1,155 MW gap is capacity the model's
own offer clears at the ACTUAL price but not at its own lower price — i.e.
**downstream of C3a-2025, which is owner-court** — **24.6 %** is offer position
proper, **13.0 %** is in the money at its own price and still unrun. An
**accounting** identity at fixed offer, not a causal one, but it identifies the
`ST_GAS` C1 lane and the C3a-2025 lane as **one object** and sizes the
offer-position component at a quarter — which is why no solve was spent.
G4's between-year channels: FUEL **−740.8 MW**, PRICE **+1,163.1 MW**, AVAIL
−239.9 MW on a net of +182 (band hr/vom drift exactly 0.0); the pre-registered
`CARRIER IDENTIFIED`/`PRICE` label is disclosed as an artifact of the small net
denominator and the MW contributions are led instead.

**SEVEN CONSTRUCTION DEFECTS caught and disclosed before they could affect a
conclusion** — four by CODE READING before the probe was committed (PREREG §7:
the band-suffix vocabulary, which would have hollowed out G3 *toward the brief's
own preferred answer*; a VOM omission in G4; G4's "bands are constant" premise
made measured; and V1, which was wrong on the code because a third pricing route
exists), three by the probe's own OUTPUT before the finding was written
(PREREG §8: V1 checked zero bins because NYISO `ST_GAS` has no `econlo`/`econhi`
band at all; G1's top-decile mean-of-ratios read 58.5 against MW levels implying
0.906; G4's shares are not fractions). **In every case the instrument was
replaced and no bar was moved.**

**WHAT IS NOT DELIVERED, stated without softening.** No keeper, no candidate, no
run, no repair. C1-2023 `ST_GAS` is exactly where nyiso-177 and nyiso-178 left
it — named, sized at +3.86 TWh, open. **Why** in-the-money steam goes
un-dispatched is **bounded but not answered** (three candidates named in finding
§6.1; the settling instrument is per-generator model dispatch, absent from every
keeper artifact — the nyiso-172 §2.5 limit, now binding a third session). The
§7 decomposition's dominant term routes into an owner-court decision, so **the
`ST_GAS` lane is BLOCKED pending Q1 of
`DECISION-CARD-nyiso148-2025-level-remainder`** — a real constraint on the next
session, not a hand-off with work in it. The missing rung is still unspent.

**Rule 15:** no solve ran, so nothing is registered on the dashboard — by design
(S1/S2/S3), not omission. **Rule 22 `[R-HOLDOUT]`:** every year read is 2023 /
2024 / 2025; NYISO is absent from both `complete` and `final`; **no marker was
requested**; the holdout spend freeze is untouched. **Rules 21/23:** zero
parameters touched; `THERMAL_AVAILABILITY`, `MERIT_*`, every band and every
hr-mult READ and never written or swept; no artifact re-derived. **Rule 25:**
NYISO only; the CAISO 1.683 was read as a *derivation pattern* and its value
transferred nowhere. **Rule 28 (b):** five NYISO cells annotated —
`offer_curve_by_group`, `dual_fuel_switching`, `zonal_gas_basis`,
`gas_hub_basis_overlay` stay **`K`** and `st_gas_committed_measured_bypass`
stays **`.`** — **no verdict moves and no field changed**; guard exit 0, shard
passes `node --check`. The §5.5 NYISO lever queue is updated with this session's
three closed lines and the new blocked status.

---

## nyiso-180 (2026-09-03) — all four candidate explanations for the un-dispatched in-the-money `ST_GAS` CLOSE, the object's inherited PREMISE is corrected, and the nyiso-172 §2.5 per-generator-dispatch limit is LIFTED

**Keeper UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`**, determination
NOT-YET, target grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**ZERO SOLVES against the object. NO LEVER OPENED — pre-declared in all three
stop conditions** (`PREREG-nyiso180-st-gas-undispatch.md` §4, committed with the
probe at `fbf93e50` before either ran).

**All three of nyiso-179 §6.1's candidates close, and a fourth it never named
closes with them.** (a) The `nyiso_zonal_loss_surface` is **refuted
structurally**: the `link_loss` coefficient lands on the receiving-end incidence
of **Flow** columns only (`lp/rows.py:1448-1465`), so a generator's own
energy-balance incidence is `+1` and there is no `δ_z` on injection — the right
figure is exactly zero, not "a few percent". (b) A post-solve price transform is
**refuted structurally and on the artifact**: `price = prices[z] + total_overlay`
exists, but all three overlay terms are assigned only inside
`if iso == "ERCOT":`, and none of the three audit columns appears in any of the
keeper's three years. (c) The capacity/label-basis mismatch is **real, fixed, and
an order of magnitude too small** — `dual_fuel_oil_reattribution` relabels
oil-switched generator-hours to a POOLED `oil` class so `class_hourly`'s `ST_GAS`
genuinely undercounts, but crediting `ST_GAS` with **100 %** of that class moves
the median ratio only 0.775→0.775 / 0.448→**0.448** / 0.816→0.821 against the
inherited 0.70 floor (switching in just 24/72/192 h of 8,760). G1 = `SURVIVES`.
(d) The armed `ramp_envelopes`, found by reading the keeper's own flags: G2 was
declared **ONE-SIDED before it ran** and reads `INCONCLUSIVE — PENDING SIDECAR`,
explicitly **not** an exoneration — but a post-hoc report settles it on the
merits, because the withholding is **SUSTAINED, not transient** (max unbroken run
137/**2,650**/270 h; 85/99/81 % of withheld hours in runs > 6 h) while every
`ST_GAS` ramp group traverses cold-to-full in **1.5–3.0 h**. A ramp row bounds
the RATE, not the LEVEL.

**The instrument was checked before it was believed.** The no-oil leg reproduces
nyiso-179's published medians to **0.0001** in all three years, and the switch
mask is reconstructed exactly with no re-derivation (`apply_dual_fuel_pricing`
writes `min(gas, oil)` in place, so a switched hour is precisely pre-min >
post-min). One premise was checked rather than assumed: the committed
`system_<year>.parquet` carries **six** zones against `get_iso_config`'s five, so
the probe's name mapping is valid only if the solve-time list keeps the base five
in order — `apply_interchange_topology`'s `extend_node` step **appends** the
external zone, and the measured `ST_GAS` zone distribution corroborates.

**THE PREMISE ITSELF IS WRONG, and that is the session's most durable result.**
§6.1 reasons from *"in a pure LP, capacity with `mc` below its own zone's dual
and below its bound should run"*. Under the keeper's eleven armed mechanisms an
LP generator's optimality condition is its **reduced cost**, which collapses to
`mc − price_z` only for a generator whose sole row is the energy balance. **"In
the money and below its bound" is therefore not by itself an anomaly.** Seven of
the eleven are ruled out on sign or scope (the reliability floor and commitment
bridge are `min_gen` LOWER bounds that push dispatch UP; the LCR/TSL and seam
rows act on links and import generators; the loss surface on Flow columns;
`local_capacity_constraints` builds no rows at all).

**DELIVERABLE — the nyiso-172 §2.5 limit is LIFTED.**
`hourly/class_band_hourly_<year>.parquet` carries
`(year, pass, klass, band, hour, mw, mw_oil)`. The per-unit-hour frame it
aggregates is already written every solve and merely gitignored, so this is an
aggregation choice, not new plumbing; it is general, not an `ST_GAS` special
case. **Sized before it was built, as pre-declared:** per-unit-hour is
**4,187,280** rows/yr and grows with fleet size, against **306,600** for
per-(klass, band), which is bounded by classes × bands and so stays committable
in ERCOT/PJM. `klass` is the **pre-re-attribution** plant group (a new
`klass_base` column captured before the dual-fuel overwrite), which is what makes
(c)'s defect un-repeatable in any ISO. Six regression tests; no LP row, price or
dispatch value touched.

**IT SHIPS IN THE KEEPER'S OWN BUNDLE.** Produced by a full 3-year replay of the
keeper recipe (one invocation, years sequential) and verified before
installation: **0 of 122,640 class-hour cells and 0 of 52,560 hourly zonal prices
differ in every year** — the nyiso-177 G-CONTROL result reproduced, so the
sidecar records the keeper's own dispatch and no calibration result changed.
~255 KB/year, 376,680 rows, 12 bands. **It is an instrument, not a run, so it is
NOT registered on the dashboard** (rule 15), and the scratch replay bundle is
deleted. The round-trip holds exactly (residual 4.9e-4 MWh is float32 rounding on
~10⁷ MWh sums, ~5 × 10⁻¹¹ relative).

**The (c) defect is now quantified from committed artifacts:** `class_hourly`
under-reports `ST_GAS` by exactly the oil-switched energy — 11.999 → 12.020 TWh
(2023), 9.799 → 9.833 (2024), 10.014 → **10.169** (2025). Every `ST_GAS` figure
in nyiso-178/179, and every C1 `ST_GAS` energy comparison reading `class_hourly`,
carries this bias. It is small against the C1-2023 gate (+3.86 TWh) and does not
move it, but it is **not zero in 2025** and is now correctable without a replay.

**WHAT IS NOT DELIVERED, stated without softening.** **The object is NOT
explained.** Four candidates are closed; the sustained ~1,000 MW gap is not
attributed. What the session delivers is a **correctly posed** question in place
of a mis-posed one — not "why doesn't in-the-money capacity run" but **"what
carries a sustained ~1,000 MW LEVEL gap in 59–90 % of hours"**, whose two
surviving named carriers are LP degeneracy at a price plateau (nyiso-179 R1:
excluding capacity within $5/MWh lifts 2024 from 0.448 to 0.678) and the reserve
rows (R2 bounds these tightly). **Degeneracy is the stronger and would make the
signature an artifact of the ITM statistic rather than a dispatch defect.** G2 is
not an exoneration and per-group ramp duals remain unmeasured. The sidecar does
**not** reach per-group grain, so it cannot see the `ramp_limits` rows. Nothing
here moves C1-2023, C3a-2025 or C3c. **The lane wall stands: nyiso-179 §7 puts
62.4 % of the 2025 top-decile deficit downstream of the owner-court C3a-2025, and
this session bottomed out against it and stopped rather than manufacturing a
lever.** The missing rung is still unspent.

**Rule 15:** no solve ran against the object, so nothing is registered on the
dashboard — by design (S3), not omission; the keeper replay was run solely to
produce and verify the new sidecar and is not a calibration result. **Rule 22
`[R-HOLDOUT]`:** every year read is 2023 / 2024 / 2025; NYISO is absent from both
`complete` and `final`; **no marker was requested**. **Rules 21/23:** zero
parameters touched; the ramp envelopes, `THERMAL_AVAILABILITY`, every band and
every hr-mult READ and never written or swept; nothing re-derived. **Rule 24:**
no new tunable — the sidecar adds an artifact column, not a knob. **Rule 25:**
NYISO only; the sidecar is ISO-agnostic and carries no NYISO-specific logic.
**Rule 28 (b):** two NYISO cells annotated — `ramp_envelopes` and
`dual_fuel_switching`, **both stay `K`, no verdict moves**; guard exit 0, shard
passes `node --check`. The §5.5 NYISO lever queue is updated with the four closed
lines, the premise correction and the re-posed object.

---

## 2026-09-03 — nyiso-181: the un-dispatched in-the-money `ST_GAS` object is an artifact of the offer reconstruction

**Keeper unchanged at entry and exit:** `2026-09-02-nyiso-177-vintage-matched`
(`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target
grade 5, fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**. No
keeper, determination, gate, score or parameter moved. `src/market_sim/`
untouched.

**Chartered object:** nyiso-180 §12.3's re-posed question — *what carries a
sustained ~1,000 MW LEVEL gap in 59–90 % of hours* — with LP degeneracy at a
price plateau ranked first. **Pre-registration**
(`results/calibration/PREREG-nyiso181-itm-degeneracy.md`) committed with its
probes before either ran, disclosing nine prior reads in §0.

**The reconciliation, and it was itself a result.** The parallel nyiso-180 lane
(PR #4650) delivered the `mc`/`red_cost` instrument and a complete pre-registered
probe but **never ran the adjudication**: `unit_hourly` is gitignored
(`.gitignore:541`), no committed NYISO bundle carries it, and no
`_nyiso180_unit_dispatch.json` exists in any commit on any branch. Every
prediction in that lane's PREREG §2 stood unmeasured — its own S2 stop condition,
fired silently. This session regenerated the instrument by a **bit-identical
control replay** of the keeper recipe (gate I1: **0 of 52,560** hourly zonal
prices and **0 of 122,640** class-hour cells differ, all three years — an
instrument, not a run, **not registered**, rule 15) and executed that
pre-registration **verbatim and unmodified**.

**THE RESULT.** nyiso-179's `build_year()` reconstructs the `ST_GAS` offer
outside the solve and omits **two armed, keeper-registered terms**: the measured
**RGGI allowance price** (\$13.49 / \$20.71 / \$22.09 per tCO₂, armed via
`state_carbon_pricing=True`; the probe hardcodes `0.0`) and
**`apply_gas_offer_margin`** (the mc-side half of
`gas_offer_net_revenue_margin=True`, zonal anchor \$2.03–3.90/MMBtu, applied at
`runner.py:2494` **after** `assemble_mc`). Restoring both reproduces the LP's
installed `mc` to **`max|d| = 0`** on every one of 88 units × 8,760 hours in all
three years — an identity with zero free parameters and zero thresholds. The
capacity basis was never in doubt (`max|d|` **1.7e-05 MW**; envelope exact to the
decimal). The omission under-states the offer by a median **\$9.57 / \$15.39 /
\$11.98 per MWh**, putting **23.8 % / 46.2 % / 20.4 %** of bin-hours
(**804 / 1,433 / 744 MW**) in the money that the LP's own offer puts
**\$4.76–\$7.87 above** the clearing price.

**Consequence.** The nyiso-179 §6.1 object (3.84 / 9.09 / 3.99 TWh/yr, `R`
0.767 / 0.522 / 0.740) and nyiso-180 §7's re-posed ~1,000 MW level gap are
**substantially an artifact of the instrument**. On the LP's own offer the
matched-population `R` is **0.9925 / 0.9913 / 0.9918** and the un-run
in-the-money capacity is **0.073 / 0.061 / 0.070 TWh** — **8.4 / 7.0 / 8.0 MW**
on average, **52× / 149× / 57×** smaller. **A second, independent defect:**
repairing the offer does not rehabilitate `R`, which then **exceeds 1** (median
1.409 / 2.421 / 1.747), because its numerator is the class's **total** dispatch
over every bin while its denominator is the capacity of the **in-the-money bins
only** — different populations, so it is not *"the share of in-the-money capacity
that runs"* at any offer basis. **RETIRE THE STATISTIC.** Instrument validated
like-for-like: on the defective basis this session reproduces nyiso-179's
published `median_R` to **0.0000 / 0.0001 / 0.0046**, and the 2025 gap is itself
explained (no dual-fuel oil undercount in this numerator — nyiso-180 §5).

**The parallel lane's predictions, executed for the first time.** **P-c PASS**;
**P-d FALSIFIED** in all three years (un-run MW at a lower bound
**0.058 / 0.165 / 0.298** against its own ≥ 0.70 bar — the MW sits **interior**,
0.942 / 0.835 / 0.702, which is the degeneracy signature); **§2.4 STOP does not
fire** (0 unit-hours). **P-a/P-b:** median leg PASS (median `mc − price` exactly
**0.0**), **mean leg FAILS** 2023/2025 (−0.0714 / +0.0141 / −0.1266 against
±\$0.05). P-c passes yet did **not** detect the defect, because it compares the
LP to **itself** (`mw` vs its own `cap_mw`); a basis test must compare the
**reconstruction** to the LP.

**S1 FIRED, and this session's own headline gates are UNADJUDICATED.** P-b is
nyiso-181's pre-registered instrument check I3, so PREREG §4 S1 withholds the
G-D and G-P verdict words. They are reported as **measured only** — `Dshare` at
the inherited \$1.00 rung **0.977 / 0.974 / 0.943**, `Pshare`
**0.960 / 0.891 / 0.764** — and would have read `DEGENERACY-CARRIES` / `PLATEAU`.
Disclosed rather than argued around: **I3's mean leg is a poorly-chosen
statistic** over a heavy-tailed residual, and the substance it screens for is
refuted **exactly** by the `max|d| = 0` identity. The bar was mine and it was not
reinterpreted after the fact. An `adjudication_status` block was added to the
probe **after** the gates ran to record S1 in the artifact; the `years` block is
**byte-identical** before and after and **no bar moved** (the nyiso-180 §8.1
discipline).

**G-R (carrier 2, the reserve rows) — ONE-SIDED BY CONSTRUCTION, INCONCLUSIVE,
explicitly NOT an exoneration.** Mean held reserve 11,764 / 11,752 / 11,750 MW
against mean un-run in-the-money 8.4 / 7.0 / 8.0 MW, Pearson r
+0.010 / +0.025 / −0.007. Independently, the net rent **all** non-energy rows
charge the class is `Ω` p50 **0.0**, p95 **3e-06 / 3e-06 / 4e-06**, non-zero in
**0.68 % / 1.12 % / 1.01 %** of unit-hours.

**What is NOT delivered.** The C1-2023 `ST_GAS` +3.86 TWh gate is not moved — a
false explanation is removed, not a true one supplied. `Ω` is not decomposed per
row (the parallel lane's §3 limit, inherited). nyiso-179's **G3, G4 and the
62.4 / 24.6 / 13.0 split of the 2025 top-decile deficit** read the same defective
`mc` and are **flagged, not re-derived** — no claim is made about which way they
move. **The lane wall stands and is untouched:** C3a-2025 −11.2 % is a scored
price metric from the keeper's own `metrics.json`, independent of any probe, and
stays owner-court; **no `ST_GAS` offer lever was opened.** §4 is **post-hoc** and
labelled so throughout; its strength is that it is an identity, not a threshold.
The `unit_hourly` frame is **16.4 / 17.4 / 17.4 MB/yr**, 3.3× the parallel lane's
own 5 MB commit threshold, so it stays gitignored and every result here needs the
~15-minute control replay to reproduce.

**Handed forward.** (1) Retire `R = mo / itm`; the well-formed replacement is the
matched-population ratio. (2) **Repair `nyiso179_st_gas_offer_position.build_year()`
before reusing it** — it is cited as a reusable instrument in the standing brief
and under-states the NYISO gas offer by \$9.6–15.4/MWh; the two-line repair and
its closure proof are in `nyiso181_offer_reconstruction_repair.py`. This session
deliberately did **not** edit it, since that would silently rewrite the basis of
the published nyiso-179 record. (3) Re-derive nyiso-179's G3/G4 and the 2025
decomposition. (4) **Audit the defect class cross-ISO** — a probe reconstructing
the LP's offer outside the solve and omitting a term the runner installs;
`unit_hourly.mc` makes the check exact and cheap, and **CAISO and NEISO also
carry state carbon programs**, so the RGGI/CARB limb is not NYISO-specific. Rule
25 kept this session inside NYISO.

**Rule 15:** no non-control solve ran, so nothing is registered — by design, not
omission. **Rule 16:** one invocation, all three years from the bundle's own
`meta.json`, sequential. **Rule 22 `[R-HOLDOUT]`:** every year is
2023 / 2024 / 2025; NYISO absent from both `complete` and `final`; **no marker
requested**; the spend freeze untouched. **Rules 21/23/24:** zero parameters
touched, zero swept, nothing re-derived, no new tunable. **Rule 27:** no existing
source file modified — all three probes are new files and the parallel lane's
probe was run unmodified. **Rule 28 (b):** two NYISO cells annotated —
`unit_network_layer_sidecar` (also discharging the stamp PR #4650 missed) and
`energy_reserve_coopt`, **both stay `K`, no verdict moves**; `node --check` and
`scripts/check_mechanism_matrix.py` both clean (exit 0). The §5.5 lever queue is
rewritten with the retired statistic and the four handed-forward items.

**Evidence:** `docs/FINDING-nyiso181-itm-degeneracy-2026-09-03.md`,
`results/calibration/PREREG-nyiso181-itm-degeneracy.md`,
`scripts/probes/nyiso181_itm_degeneracy.py` + `nyiso181_replay_identity.py` +
`nyiso181_offer_reconstruction_repair.py` →
`results/calibration/_nyiso181_itm_degeneracy.json` +
`_nyiso181_replay_identity.json` + `_nyiso181_offer_reconstruction_repair.json` +
`_nyiso181_unit_dispatch_nyiso180gates.json`.

## 2026-09-03 — nyiso-182: the offer reconstruction is REPAIRED, and the load-bearing premise it carried is CONFIRMED and STRENGTHENED — the 2025 split is 107.2 / 14.6 / −21.8, not 62.4 / 24.6 / 13.0

**ZERO NON-CONTROL SOLVES.** One bit-identical control replay (the instrument),
**not registered** (rule 15). Keeper `2026-09-02-nyiso-177-vintage-matched`,
determination NOT-YET, target grade 5, fail set {C1-2023 `ST_GAS` +3.86 TWh,
C3a-2025 −11.2 %, C3c} — **all UNCHANGED**. `src/market_sim/` untouched; the one
edited file is a probe.

**THE REPAIR (nyiso-181 §11 item 2), made non-silently.**
`nyiso179_st_gas_offer_position.build_year()` omitted two armed,
keeper-registered offer terms — the measured RGGI allowance price
($13.49 / $20.71 / $22.09 per tCO₂) and `apply_gas_offer_margin` (anchor
$3.9046/MMBtu). The repaired form is now the **default**; an explicit
`legacy_defective_offer=True` reproduces the published form and `main()` is
**pinned to it**, so `_nyiso179_st_gas_offer_position.json` and every number in
the nyiso-179 finding stay byte-reproducible. **Gate I3 confirms it:
`max|d| = 0.0` MW and 0.0 on shares, all three years, every band, every G3/G4
field.**

Three downstream callers (`nyiso180_ramp_report`, `nyiso180_st_gas_undispatch`,
`nyiso179_g1_robustness`) called `build_year` with the default and are **pinned
to the legacy path** with a citation comment, so **no published probe changes its
output**.

**INSTRUMENT GATES — ALL PASS, S1 DID NOT FIRE.** **I1** replay identity: 0 of
52,560 prices, 0 of 122,640 class-hour cells, all three years (bar inherited from
nyiso-181). **I2** — the repaired reconstruction equals the LP's own installed
`mc` at **`max|d|` 2.7e-05 / 1.5e-05 / 3.0e-05 $/MWh** over 88 units × 8,760 h
against an inherited 1e-4 bar; capacity basis 1.7e-05 MW. This is the check
**nyiso-180's P-c could not be** — P-c compared the LP to ITSELF — and it
independently reproduces nyiso-181 §4's identity from a fresh instrument.
**I2b** — the ITM anchor by two routes agrees to ≤ 2.3e-05 MW.

**G-S, THE LOAD-BEARING GATE — `PREMISE-CONFIRMED` on both legs.** 2025
top-decile split, on the LP's own `unit_hourly` frame and with the trap-(j)
dispatch undercount corrected (+140.5 MW): **`T1` price level +1,087.1 MW
(107.2 %), `T2` offer position +148.1 MW (14.6 %), `T3` own signal −220.8 MW
(−21.8 %) on a gap of 1,014.5 MW** — against the published 721 / 284 / 150 on
1,155 MW. G-S1 dominance 1.0717 vs the inherited 0.60 bar; G-S2 plurality
threshold-free. **The *"C1 `ST_GAS` and C3a-2025 are ONE OBJECT"* identification
STANDS on a repaired instrument and is STRONGER** (the offer-position component
is a seventh of the gap, not a quarter); **the standing DO-NOT-OPEN on `ST_GAS`
offer levers STANDS; the brief's task-2 conditional did NOT arm; no lever was
opened.**

**`T3` CHANGED SIGN, and its matched-population repair is a NEW UNATTRIBUTED
OBJECT.** Of the −220.8 MW, only **+14.1 MW** is un-run in-the-money capacity
(consistent with nyiso-181's 8 MW mean) and **−234.9 MW is dispatch of
out-of-the-money bins**. The model **over**-dispatches against its own offer in
the 2025 top decile. Attributing that 235 MW per mechanism (reliability floor vs
`nyiso_gas_commitment_bridge`) is the named successor — a **D-2 diagnostic**, not
a lever (rule 19: this is the enumeration).

**G-3R — `PEAK-EXONERATED` SURVIVES, but every leg moved and the reason changed.**
2023/2024 `peak` OOM-hours **crossed** the 0.90 bar (0.8912 → 0.9343,
0.8628 → 0.9252) while 2025's fell **away** from it (0.8062 → 0.7676), share leg
0.3659 vs 0.40. `p179.g3_band_attribution` run **unmodified**, both bars
inherited verbatim.

**G-4R — a REAL fourth channel.** RGGI is `emission_rate × carbon_price` and both
factors move (CO₂-rate drift `max|d|` 0.0825 t/MWh, measured); on full Shapley
over 24 orderings **CARBON = −148.2 MW, larger in magnitude than AVAILABILITY
(−109.6 MW)**. PRICE stays the carrier in all four basis × method grid cells and
`share_denominator_is_small` is TRUE in every one, so the MW contributions are
the output and the verdict word is not load-bearing. `heat_rate` / `vom` /
`markup_hr` drift exactly 0.0.

**A PRE-REGISTERED EXPECTATION OF MINE WAS FALSIFIED and is reported at full
magnitude.** PREREG §2 G-3R predicted *"the repair raises every band's `mc`"*. It
does not: the margin term is `markup_hr × (anchor − fuel)`, **negative wherever
delivered fuel exceeds the $3.9046 anchor**, so in the 2025 top decile it
**lowers** `peak` by $188/MWh while **raising** `committed` by $12/MWh. No bar was
moved and nothing was rescued — but nyiso-181's class-median $9.57 / $15.39 /
$11.98 under-statement is a median over a **signed** distribution, and that is new.

**Rule 15:** no non-control solve ran, so nothing is registered — by design, not
omission. **Rule 16:** one invocation, all three years from the bundle's own
`meta.json`, sequential. **Rule 22 `[R-HOLDOUT]`:** every year is
2023 / 2024 / 2025; NYISO absent from both `complete` and `final`; **no marker
requested**; the spend freeze untouched. **Rules 21/23/24:** zero parameters
touched, zero swept, nothing re-derived from a residual, no new tunable (the one
new argument is a probe-local reproducibility switch). **Rule 27:** the one
edited existing file (`scripts/probes/nyiso179_st_gas_offer_position.py`,
748 → 839 lines) was edited locally and its pushed blob verified. **Rule 28 (b):**
three NYISO cells annotated — `unit_network_layer_sidecar`,
`gas_offer_net_revenue_margin`, `state_carbon_pricing` — **all stay `K`, no
verdict moves**; `node --check` and `scripts/check_mechanism_matrix.py` both
clean. The §5.5 lever queue is rewritten with the repaired split and the new
`T3b` object.

**Environment note:** this container's `data/clean` tree was empty, so the replay
needed `capacity-deliverability` and `nyiso-interface-flows` curated from
`data/raw` first. `data/clean` is derived, disposable and gitignored by design;
I1 proves the resulting solve is the keeper.

**Evidence:** `docs/FINDING-nyiso182-offer-repair-rederivation-2026-09-03.md`,
`results/calibration/PREREG-nyiso182-offer-repair-rederivation.md`,
`scripts/probes/nyiso182_offer_repair_rederivation.py` →
`results/calibration/_nyiso182_offer_repair_rederivation.json` +
`_nyiso182_replay_identity.json`.

## 2026-09-03 — nyiso-181 (`stgas-floor` lane): the C1-2023 `ST_GAS` over-generation is ONE PLANT, it is ECONOMIC not forced, and the class aggregate that hid it also hides a ~1 TWh/yr under-count in the committed D-2 row

**Keeper at entry and exit `2026-09-02-nyiso-177-vintage-matched` — NOT-YET,
target grade 5, {C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}. UNCHANGED.
Solves run: ZERO. NO LEVER OPENED — PREREG §4 S2 fired on its own pre-declared
terms.** Pre-registration
`results/calibration/PREREG-nyiso181-stgas-floor-overgeneration.md`, pushed to
origin at `a1f717b5` **before the first measurement**, with §0 disclosing all
eight reads held at writing time.

**The instrument.** The LP's **own installed offer and reduced cost** at unit
grain (`unit_hourly_stgas_<year>.parquet`, PR #4656's bundle), the keeper's own
zonal `price`, and the floor matrices imported from
`legitimacy_diagnostics.load_or_rebuild_floors` / `at_floor_mask` so every
measured number is on the D-2/D-4 gate's own basis. All three instrument checks
PASS: **I1** the unit bundle IS the keeper (0 / 122,640 class-hour cells and
0 / 52,560 zonal prices differ — PR #4656's bit-identity claim verified, not
inherited); **I2** the slice closes on `class_hourly` + the dual-fuel `oil`
undercount, **reproducing nyiso-180 §5 to the fourth decimal** (0.021 / 0.034 /
0.154) from a different artifact; **I3** p95 |Ω| ≤ 6.2e-06 $/MWh, which licenses
reading `mc > price` as out-of-the-money. One population trap was caught before
any gate ran: the committed slice is cut on FUEL, so it carries `ST_CHP` too and
reads 13.281 TWh unfiltered against the class's 12.020.

**Rule 19 `[R-ONE-MECH]`, discharged before anything was proposed and then
confirmed numerically: there is ONE mechanism.** 97 % of the class's
out-of-the-money energy sits at a `reliability_floor` cell. Three enabled limbs —
the NYC and Long_Island **persistent 24 h bases** (`tmax` @ −50 °C so every day
is flagged, `floor_pct` 0.175 / 0.262, `pro_rata`) and the Capital_Hudson `tmax`
31.1 step; the three evening ramp families are disarmed by the keeper's
`reliability_floor_overrides`.

**The gates: P1a / P1c / P2b PASS, P1b / P2a FAIL, P3 CONFIRMED.** The rule-17
violation is real and reported at full magnitude — **0.316 / 0.268 / 0.049 TWh a
year of floored energy lands in hours the floored plant's own CAMPD meter reads
exactly zero**, 9.2 % / 7.5 % / 1.7 % of the mechanism against D-4's own 0.05 bar,
**55 % of it on Arthur Kill (2490)**, which sits on the NYC persistent-base limb,
the one enabled `ST_GAS` limb that has **never had a membership review**. But it
is **8.2 % of the miss**, not its carrier, and **no plant on that limb meets
nyiso-140's evidentiary standard**, so **no repair was proposed**. P3 is
confirmed decisively: the forced term explains **−4.1 %** of the between-year
swing — it moves the wrong way.

**Why both hypotheses failed (POST-HOC, gates byte-identical before and after,
verified programmatically): the class aggregate is a CANCELLATION.** At plant
grain, **Ravenswood (2500) runs +5.472 / +2.787 / +1.618 TWh above its own
meter** — in 2023 more than the entire class miss from one machine — while the
other ten plants net **−2.365 TWh** (gross basis). Its excess is **ECONOMIC**:
5.631 of its 6.328 TWh clears in or at the money, and the floor touches
0.699 TWh at unit grain / 0.0099 at plant grain. Model availability **0.700 /
0.425 / 0.280** against measured CF **0.062 / 0.049 / 0.077** — ratio **11.3**,
the largest in the class by capacity. **This is nyiso-177 §6's open object with
its dispatch consequence attached**, plus one sharpening: **that session's G2
over-booking is not uniform, it is INVERTED against measured conduct** — the
availability ÷ measured-CF ratio runs 39.2× Danskammer, 11.3× Ravenswood, 7.8×
Port Jefferson, 4.8× Arthur Kill against 1.07× Greenidge and 1.3× Barrett, so
the class is over-derated in aggregate while the plants that barely ran carry the
highest availability. **P2a was a badly-chosen statistic — a class aggregate over
a population that cancels — the bar was mine, it stands as FAILED, and the plant
grain is disclosed as post-hoc.**

**And the floor is doing the OPPOSITE job at the plants that did run.** Northport
and Barrett take **1.920 of the floor's 3.454 TWh** and are **−3.415 TWh short
economically**; Port Jefferson takes **exactly 0.000** in all three years, so
**nyiso-140's membership correction is verified live at unit grain** from an
artifact that did not exist when it was made. **Deleting or narrowing this floor
to close C1-2023 would break 2024 (−0.081 → −3.774) and 2025 (−3.544 → −6.583)** —
the nyiso-140 no-volume-buying warning in mirror image.

**Second result, escalated and NOT acted on — the D-2 / C8 grain under-count.**
At its native **unit** grain the floor forces **3.454 / 3.562 / 2.934 TWh**,
**0.96 / 0.80 / 0.57 TWh (27.8 / 22.3 / 19.4 %) MORE** than the committed
plant-grain row, because `aggregate_floors_by_plant` nets a pinned unit against a
free one at the same site (Ravenswood 0.699 unit vs 0.0099 plant, **70×**).
Instrument validated: re-aggregating the same unit data under D-2's own plant-sum
convention reproduces the committed total to **0.8 / 1.2 / 3.8 %**, so the gap is
**grain, not method**. `ST_GAS`'s C8 forced share is therefore **0.287 / 0.362 /
0.289 as LOWER bounds** against rule 20's **0.30** cap (committed: 0.177 / 0.237 /
0.198) — **2024 is above the cap** — and a second grain effect compounds it: the
committed denominator exceeds the class's own dispatch by **1.98 / 1.97 /
2.25 TWh** — all eleven `ST_GAS` plants take an `ST_GAS` plant-grain majority
label and four are mixed, **Ravenswood carrying 7 `CC_REGULAR` LP units** beside
its 8 steam units, so with the whole model `CT_PEAKER` class at only 0.350 /
0.242 / 1.010 TWh the balance is Ravenswood's CC output inside the steam row.
**Not repaired here**: the defect is in `scripts/legitimacy_diagnostics.py` and is
**code-generic across all six ISOs**, so it belongs to the scorer/governance lane
(rule 25 `[R-ISO-SCOPE]`, PREREG §4 S4). A re-based breach would not auto-fail —
rule 20 escalates to D-4 + D-1, and **NYISO's D-4 already reads `passed: false`**.

**Handed forward.** (1) The object is **Ravenswood's availability**, not the
floor; take it in nyiso-177 §6, and note it is an accounting identity, not a
causal proof — no A/B here separates availability from offer. (2) **Do not delete
or narrow the `ST_GAS` reliability floor to close C1-2023.** (3) The deficit
object spans all three years: holding Ravenswood out, the economic shortfall is
**−5.197 / −6.776 / −7.957 TWh**, so **2023's class-level sign flip is
arithmetic, not a separate phenomenon** — which AMENDS the parallel lane's "2023
is a separate, opposite-signed object" reading. (4) The **NYC persistent-base
limb has never had a membership review**; a lane that re-derives it should look,
from source data, never at a residual. (5) The D-2/C8 grain under-count is
escalated. (6) **Merge PR #4656 or these numbers do not reproduce from `main`.**

**Rule 15:** zero solves, so nothing is registered — by design, not omission
(the nyiso-180 / nyiso-181 zero-solve precedent). **Rule 22 `[R-HOLDOUT]`:**
every year is 2023 / 2024 / 2025; NYISO absent from both `complete` and `final`;
**no marker requested**; the spend freeze untouched. **Rules 5/21/23/24:** zero
parameters touched, zero swept, nothing re-derived, no new tunable. **Rule 13:**
measured CAMPD conduct used only to diagnose; PREREG §4 S4 pre-emptively forbade
the same-year availability gate that would close this gate and has no forward
analogue, and it was not built. **Rule 27:** no existing source file modified —
the probe is a new file. **Rule 28 (b):** four NYISO cells annotated —
`reliability_floor`, `reliability_floor_plant_exclusions`,
`campd_outage_merit_order_guard`, `campd_per_unit_attribution` — **all stay `K`,
no verdict moves**; `scripts/check_mechanism_matrix.py` clean. The §5.5 lever
queue is rewritten, with the prior lane's queue preserved verbatim beneath it.

**Evidence:** `docs/FINDING-nyiso181b-stgas-floor-overgeneration-2026-09-03.md`,
`results/calibration/PREREG-nyiso181-stgas-floor-overgeneration.md`,
`scripts/probes/nyiso181b_stgas_floor_overgeneration.py` →
`results/calibration/_nyiso181b_stgas_floor_overgeneration.json`.

## nyiso-183 — the availability hypothesis is REFUTED on its own gate; the C1-2023 carrier is the OFFER, and it is ONE TERM (2026-09-03)

**Session nyiso-183, `ravenswood-availability` lane, ZERO SOLVES.** Keeper
`2026-09-02-nyiso-177-vintage-matched` **UNCHANGED** — determination NOT-YET,
target grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}. No parameter
touched, no band swept, no constant moved or swept, no `ScenarioConfig` field,
no CLI flag, no arm built; `src/market_sim/` byte-untouched. **PREREG
§6 S2 AND S3 BOTH FIRED**, on their own pre-declared terms.
Pre-registration pushed to `origin` at `53767546` **before the first
measurement**, amended at `3085f253` **before any gate below G0 was read**.

**Rule 19 `[R-ONE-MECH]`, discharged from the code before any proposal:**
`campd_outage_merit_order_guard` (stage 3 of the deriver's per-unit loop) OWNS
the outage-vs-lay-up decision for NYISO `ST_GAS`, and owns it LAST — stages 1,
2 and 2b can only *propose* a window as mechanical. Every other availability
gate is off on this keeper.

**G0 — the bar as first written FAILED, and the failure is a stale inherited
number.** `0.772 / 0.465 / 0.297` is the **SUPERSEDED nyiso-159** keeper's
`(2500, ST_GAS)` availability (nyiso-177 §2.1 labels the row *"L0 keeper
(incumbent + override)"*); the promoted recipe replaces both the incumbent
extract and `_FLEET_GROUP_OVERRIDE`. **The CURRENT keeper reads
`0.786 / 0.478 / 0.309`.** Re-anchored on two harder published anchors — L0
(0.7715 / 0.4645 / 0.2968) and L2 (0.1412 / 0.0967 / 0.1212) — both **PASS** at
max |Δ| **0.0005**. The correction makes the object LARGER, i.e. cuts against
this session's own hypothesis.

**G1 — HYPOTHESIS A (mis-booking) REFUTED, 3/3 years.** The guard's own evidence
statistic separates at Ravenswood: guard-removed windows read `out_of_merit`
**0.9954 / 0.9336 / 0.9581** while the plant's RUNNING hours read only
**0.6669 / 0.2928 / 0.1531** — separation **+0.33 / +0.64 / +0.81** against a bar
of `MERIT_OOM_FRAC` itself. **G2 fires** (the guard hands back
**0.645 / 0.381 / 0.188** of the capacity-year, bar 0.40) but materiality without
discrimination grounds nothing, and **G3 blocks both admissible zero-constant
repair forms independently**: `sel_fleet` **0.8674** (R2) and **0.9235** (R1)
against a 0.75 bar — each IS nyiso-177's already-rejected unguarded arm in
disguise. **DO-NOT-REDO the availability route.**

**G4 — HYPOTHESIS B (offer) FIRES, 3/3 years, on its pre-registered leg (ii).**
G4c was scored **in full** rather than left PARTIALLY TESTED: PR #4656 is closed
unmerged and the keeper's invocation is recorded nowhere, but
`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` yields the keeper's own
`mc_base` **with no LP**, behind a fidelity guard. The model prices Ravenswood
**3rd cheapest of 11** `ST_GAS` plants every year while its measured SRMC ranks
it **8th / 8th / 6th of 10** — \$23.35 / \$18.85 / \$25.37 below the
downstate-steam peer model-`mc` median with its measured SRMC ABOVE the peer
measured median.

**G4d (POST-HOC locator, no bar) puts it in ONE TERM.** Model heat rate ÷
CAMPD-measured is a tight **1.596–1.749** cluster across eight peers (median
**1.699 / 1.685 / 1.685**) and **1.382 / 1.417 / 1.454** at Ravenswood; base heat
rate **9.50 against a measured 10.71** — ~11 % MORE efficient than its own meter
where every peer's basis is 8–12 % LESS efficient than theirs, a **~20 pp
relative error on 1,725 MW** worth **\$11.38 / \$7.88 / \$13.08 per MWh**. `vom`
is a uniform \$4.00 and the tranche multipliers are class-uniform, so neither can
carry it. **Astoria (8906) is the mirror-image outlier at 3.365 / 3.419 / 3.464**,
unexplained.

**Upstream cause NAMED, explicitly NOT adjudicated:** `fleet/eia860.py:624`
reads **plant-grain** eGRID `PLHTIAN`/`PLNGENAN`/`PLHTRT`, and Ravenswood is the
class's only large mixed steam+CC site (facility blend 8.24 vs steam-only 10.71,
model 9.50 between) — the same facility-summed-denominator family nyiso-177
repaired on the OUTAGE and TRANCHE paths, surviving in the HEAT-RATE path.
The unexplained `CC_REGULAR`/`ST_GAS` base split (8.80 vs 9.50) means a second
term is at work.

**Three defects in this session's own instruments, disclosed rather than argued
around:** the G0 bar cited the wrong keeper (above); G4c's leg (i) was
uninformative by construction (model `mc` carries VOM/CO2/tranche multipliers
that measured SRMC does not, so it sits above measured everywhere, and the gate
was carried by the rank-based leg (ii) alone); and the first cut of the measured
population averaged **every** unit at an `ST_GAS`-labelled plant, pulling in
Ravenswood's combined cycle (`UCC001`, measured HR 7.137) and Astoria's four
heat-recovery halves — nyiso-181 §3's population trap in mirror image. The
population repair (to the keeper's own `campd_measured_classes` crosswalk) was
triggered by an **internal contradiction between two of this session's own
measurements**, not by a gate outcome; it MOVED G4c's 2024 and 2025 verdicts
`False → True`, and **no bar was touched**.

**Rule 15:** zero non-control solves, so nothing is registered — by design, not
omission (the nyiso-179 / -180 / -181 precedent). **Rule 22 `[R-HOLDOUT]`:**
every year is 2023 / 2024 / 2025; NYISO absent from both `complete` and `final`;
**no marker requested**; the spend freeze untouched. **Rules 5 / 21 / 23 / 24:**
zero parameters touched, zero swept, nothing re-derived, no new tunable — every
`MERIT_*`, `FULL_STOP_OVERRIDE_*`, `HIGH_LOAD_PCTL`, `MIN_INMERIT_HOURS`,
`UNIT_OUTAGE_MIN_DAYS`, `REAL_RUN_CF` and `ST_GAS_CF_PEAK` READ at its committed
value. **Rule 13:** measured conduct diagnoses only; PREREG §5 F6 pre-emptively
forbade the same-year availability gate that would close C1-2023 and has no
forward analogue, and it was not built. **Rule 27:** no existing source file
modified — the three probes are new files. **Rule 28 (b):** three NYISO cells
annotated — `campd_outage_merit_order_guard` (stays `K`, now positively
corroborated), `campd_per_unit_attribution` (stays `K`, annotated: the repair
does not reach the heat-rate path) and `offer_curve_by_group` (stays `K`, with
the new open defect recorded inside it) — **no verdict moves**;
`scripts/check_mechanism_matrix.py` clean. The §5.5 lever queue is rewritten,
with the prior lane's queue preserved verbatim beneath it.

**Tests:** `tests/unit` + `tests/iso/nyiso` — 4,475 passed, 28 skipped, 1
xfailed, 200 subtests passed; the 4 failures in `tests/unit/results/test_export.py`
are the pre-existing missing-`confirmed-retirements`-partition failure nyiso-177
§9 recorded, **proved rather than asserted**: after regenerating that clean
partition the file runs 14 passed / 0 failed, i.e. **4,489 passed, 0 failed**.

**Side effect, disclosed:** `data/clean/` (gitignored, derived, disposable) was
regenerated for `capacity-deliverability`, `nyiso-interface-flows` and
`confirmed-retirements` — the first two because the no-LP reconstruction requires
them and they were absent in this container, the third to discharge the test
question above. No raw input was written.

**Evidence:** `docs/FINDING-nyiso183-ravenswood-availability-2026-09-03.md`,
`results/calibration/PREREG-nyiso183-ravenswood-availability.md`,
probes `scripts/probes/nyiso183_ravenswood_availability.py`,
`nyiso183_g4c_offer_position.py`, `nyiso183_g4d_offer_anatomy.py` →
`results/calibration/_nyiso183_ravenswood_availability.json`,
`_nyiso183_g4c_offer_position.json`, `_nyiso183_g4d_offer_anatomy.json`.

## nyiso-184 — the 9.50 is a HAND NUMBER in a per-plant dict lifting a PLANT-GRAIN eGRID blend; Astoria is a measured-side artifact; the zero-parameter repair is built default-off and NOT proposed (2026-09-04)

**Branch:** `claude/nyiso-184-stgas-heat-rate-90z3qr`. **Solves: ZERO.**
**Keeper unchanged:** `2026-09-02-nyiso-177-vintage-matched`, NOT-YET on
{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}. **Pre-registration**
`results/calibration/PREREG-nyiso184-stgas-heat-rate-basis.md` pushed at
`19d809d9` before the first gate measurement.

**What was proved (G0/G1, identities not assertions).** Ravenswood's
`CC_REGULAR` base 8.80 IS eGRID-2023 `PLNT23.PLHTRT` for ORISPL 2500 joined at
PLANT grain to all five of its EIA-860 rows (parquet == `PLHTRT`/1000 to 0.0;
`PLHTIAN`/`PLNGENAN` == `PLHTRT` to 1.2e-8). Its `ST_GAS` base 9.50 IS
`fleet.models.MIXED_FACILITY_STEAM_HR[2500] = 9.5` — a hardcoded per-plant
dict, always on, no `ScenarioConfig` field, lifting only the steam rows of the
same blend (committed ÷ 1.05 = peak ÷ 4.20 = 9.50; CC committed ÷ 0.90 =
8.8004). Its 9.5 is derived in its own comment from ASSUMED capacity factors
that put 66 % of the site's energy on the steam; CAMPD 2023 puts 31 % there.
nyiso-183 §8's unexplained CC/ST split is closed: it is the dict.

**Astoria (G3, FIRES 2 of 3).** The 5.39–5.55 "measured" HR was the CAMPD
stack-duplicate double count (`campd.CAMPD_STACK_DUPLICATE_UNITS`), unmerged in
nyiso-183's helpers; merged it reads 11.01 / 10.88 / 10.60 and the G4d ratio
1.697 / 1.717 / 1.761 sits inside the peer cluster. Two objects; Astoria closed
as a model-side object. **G3b (sized, not repaired):** the merit-order guard's
panel reads the raw halves too, so it prices Astoria's SRMC at ~half its
physical value (281 extract rows / 70 lay-up rows on the keeper) — handed to
the outage-derive lane.

**The repair (R1, `egrid_family_heat_rates`), built default-off and NOT
proposed.** eGRID at prime-mover-family grain (Σ`HTIAN`/Σ`GENNTAN` per family
from the same vintage and window the join reads; zero parameters; supersedes
the dict where it covers) puts the steam at **12.29**: G2a (window) and G2b
(≥ the meter's 10.707) hold, **G2c FAILS** — like-for-like `r` 1.148 against
the eight peers' [1.059, 1.121]. S2 fired: no solve. Post-hoc (no bar): heat
side exact; annual/loaded 1.029 ordinary; the entire excess is gross→net, and
at generator grain it is unit 30's EIA-923 net ÷ CAMPD gross 0.862 (sisters
0.913 / 0.933; peers 0.923–0.959) — idle-period house load at CF 4.2 %. The
per-vintage record rises 11.47 (2018) → 12.57 (2021) → 12.29 (2023) as the
steam's generation falls. G4 footprint: 7 plants / 24 generator rows /
6,238 MW; off path byte-identical (460 generators).

**Rules.** 1: nothing adopted or rejected on a residual; the repair was not
proposed when its own gate failed. 5/21/23: zero parameters; the join's inline
3,000–30,000 window named once (`process_eia860.EGRID_HR_WINDOW_BTU_KWH`).
13: the meter diagnoses; the construction reads published eGRID fields and
regenerates per vintage. 15: zero solves, nothing to register. 19: discharged
from the code, then proved; superseded not stacked. 22: 2023–2025 only, no
marker requested. 24: one registered boolean, no per-plant dict added.
25/28: NYISO shard verdicts only; the new field's row + a `U` cell in every
shard (28c); `check_mechanism_matrix.py` clean. 27: on-disk bytes pushed,
≥300-line blobs verified.

**Disclosed instrument repairs (nyiso-183 §8 standard, no bar moved):** the
first G1 read divided the already-MMBtu/MWh ratio by 1,000 again and read
FAILED (preserved as `_nyiso184_heat_rate_basis_prefix_g1unit.json`); the first
G0 CC base used the `ST_GAS` multiplier. The brief's "Astoria has zero extract
rows" was an id-column grep on a name-first CSV.

**Evidence:** `docs/FINDING-nyiso184-stgas-heat-rate-basis-2026-09-04.md`,
`results/calibration/PREREG-nyiso184-stgas-heat-rate-basis.md`,
`_nyiso184_heat_rate_basis.json`, probe
`scripts/probes/nyiso184_heat_rate_basis.py`, derive
`scripts/data/derive_egrid_family_heat_rates.py`, artifact
`data/raw/_processed-legacy/egrid_family_heat_rates_NYISO.csv` (+ `_vintages`),
tests `tests/unit/data/test_egrid_family_heat_rates.py`.

## nyiso-185 — the family heat-rate A/B is SOLVED; registered as a KEEPER CANDIDATE, disposition to the owner (2026-09-04)

**Branch:** `claude/nyiso-185-stgas-family-hr-ab`. **Solves: TWO** — arm
`2026-09-04-nyiso-185-family-hr` (`results/calibration/nyiso185_family_hr`,
registered) and the same-HEAD control (`nyiso185_control`, BIT-IDENTICAL to
the committed keeper in all three years — an instrument, registers nothing).
**Keeper unchanged:** `2026-09-02-nyiso-177-vintage-matched`. **Owner ruling
carried:** "If structural integrity improves but gates regress that may still
be a keeper.." — authorizing the A/B nyiso-184's S2 withheld; not a promotion.
**Pre-registration** `PREREG-nyiso185-stgas-family-hr-ab.md` pushed at
`588aa141` before the first measurement (its §0 discloses the author holds
nyiso-184's post-hoc numbers).

**Grounding (G1, all legs fire):** the bar gates what the join controls —
Ravenswood's annual/loaded heat-side factor 1.029 inside the eight peers'
[1.0006, 1.0707]; eGRID ST-family heat input == CEMS heat to 1e-9;
plant-level EIA-923 net ÷ CAMPD gross 0.948 inside the peers' [0.888, 0.959].
EIA-923's denominator convention (unit 30 net/gross 0.862 at CF 4.2 %) is
reported, not gated. G0: the armed no-LP reconstruction moves exactly the
nyiso-184 footprint at the expected ratios (1.29387 ST, 0.83517 CC).

**A/B, keeper = baseline:** NOT-YET, grade 5, fails 3 on both, with a
different C1 cell. C1-2023 `ST_GAS` +3.86 → **+2.16 TWh (FAIL → PASS)**;
C1-2024 `CC_REGULAR` +3.34 → **+3.87 TWh, share 2.78 → 3.18 pp (PASS →
FAIL)**; C3a-2025 −11.2 → −10.5 % (FAIL, owner-court); C3a-2023 +2.2 → +4.7 %;
C3b 0.122 / 0.173 / 0.191 PASS; C2 / C4 / C8 PASS (`ST_GAS` D-2 0.192 / 0.253 /
0.203); C3c identical; C6 attested (`gen_nyiso185_attestation.py`, computed
G-CONTROL / G-DELTA / G-INPUTS / G-DOF / G-ENGAGE); DOF 13 / 6 verbatim.
Energy: Ravenswood `ST_GAS` 6.328 → 4.181 / 3.468 → 2.317 / 2.688 → 1.851 TWh;
other ten steam plants +0.44 / +0.17 / +0.18; Ravenswood's own CC +0.004 /
+0.034 / +0.010 (already ~82 % CF); `CC_REGULAR` ex-Ravenswood +0.79 / +0.50 /
+0.31. 2024 / 2025 `ST_GAS` deepen as pre-declared. D-4: the same five rule-17
rider rows on both; Ravenswood's share 0.004 → 0.018 / 0.008 → 0.021.

**Verdict rule (pre-registered):** no PASS → FAIL on C2 / C3a / C3b / C8, G1
fired ⇒ **KEEPER CANDIDATE**, disposition to the owner. Session
recommendation: promote (rules 14 + 1). Not promoted here.

**Rules.** 1 / 5 / 13 / 14 / 19 / 21 / 22 / 23 / 24 / 25 / 28 as the finding
§6. 15: arm registered; retention pruned `2026-08-22-nyiso-152-duty-complete`.
16 / 12: one invocation each, years sequential, two concurrent solves.
27: on-disk bytes pushed, ≥300-line blobs verified.

**Evidence:** `docs/FINDING-nyiso185-stgas-family-hr-ab-2026-09-04.md`,
`results/calibration/PREREG-nyiso185-stgas-family-hr-ab.md`,
`_nyiso185_grounding.json`, `scripts/probes/nyiso185_grounding.py`,
`scripts/gen_nyiso185_attestation.py`, the arm bundle's
`calibration_attestation.json` / `metrics.json` / `legitimacy_diagnostics.json`.

**ADDENDUM 2026-09-04 — PROMOTED BY OWNER RULING** (verbatim: "Is this a
recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."). NYISO keeper →
`2026-09-04-nyiso-185-family-hr`; keeper shard + `status/NYISO.js`,
`audit_keepers --iso NYISO` all checks passed, forecast gate-(a) stamp
re-keyed (R-T), NYISO matrix shard re-stamped (cell `egrid_family_heat_rates`
O → K), §5.5 header re-stamped. Fail set now {C1-2024 `CC_REGULAR` share,
C3a-2025 −10.5 %, C3c}; top of queue: the 2024 `CC_REGULAR` over-run as a
class object.

## 2026-09-04 — nyiso-186 (`cc-regular-2024-class` lane): the 2024 `CC_REGULAR` excess attributed; the Astoria merged-identity heat rate A/B-solved and PROMOTED

**Keeper at entry:** `2026-09-04-nyiso-185-family-hr` (NOT-YET, grade 5,
{C1-2024 `CC_REGULAR` +3.87 TWh / +3.18 pp, C3a-2025 −10.5 %, C3c}).
**Solves: two** — the same-HEAD control (bit-identical, registers nothing;
slim files committed as the instrument) and the arm
`2026-09-04-nyiso-186-astoria-identity` (bundle
`results/calibration/nyiso186_astoria_identity`).

**Attribution (PREREG §3, bars fixed before measurement):** CONCENTRATED in
every year at Cricket Valley 57185, Zeltmann 56196, Astoria Energy II 57664
(C3 0.875 / 0.745 / 0.853); no plant-level bar fires; gas family EXACT (67.80
vs 67.80 TWh) — the class is the within-family fill of `CT_PEAKER` −1.66 /
`CT_CHP` −1.29 / `ST_GAS` −1.09; carriers load flat when on (Zeltmann 0.96 vs
0.68) or stay on (Cricket Valley 0.995 vs 0.878).

**The repair (rule 14, found on inputs):** eGRID files both Astoria blocks
under 55375; 57664 has no eGRID row; `PLNGENAN(55375)` == netgen(55375) +
netgen(57664) to < 0.5 MWh in all seven vintages. The identity derive gains a
MERGED-identity leg (one pair found in 187 plants); 57664 6.70 → 7.3792.
ZERO config fields, one artifact row, zero DOF.

**A/B, full magnitude:** 57664 −0.154 / −0.112 / −0.103 TWh; class −0.098 /
−0.073 / −0.048; C1-2024 `CC_REGULAR` +3.87 → +3.80 TWh, 3.2 → 3.1 pp (still
FAIL); C3a-2025 −10.5 → −10.4 %; C3a-2023 +4.7 → +4.8 % (in band); C3b / C2 /
C4 / C8 PASS; C3c identical; D-4 the same five rows. NOT-YET, grade 5, fails
3. **Verdict rule: KEEPER CANDIDATE. PROMOTED BY OWNER RULING** (verbatim: "Is
this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."): keeper
shard + `status/NYISO.js`, `audit_keepers --iso NYISO` PASS, gate-(a) stamp
re-keyed (R-T), NYISO matrix shard re-stamped, §5.5 rewritten. Retention
pruned `2026-08-22-nyiso-153-incity-obligation`.

**Handed forward:** the CT-class / steam merit position in NYC and
Capital-Hudson (top of queue); the Astoria availability half (outage-derive
lane); `cc_capacity_reconcile` (U, Zeltmann H-B1 in 2023 / 2025); Bethlehem's
eGRID vintage artifact. Evidence:
`docs/FINDING-nyiso186-cc-regular-2024-class-2026-09-04.md`,
`results/calibration/PREREG-nyiso186-cc-regular-2024-class.md`.

## 2026-09-04 — nyiso-187 (`ct-steam-merit` lane): the CT / steam-vs-CC merit position decomposed (owner = out-of-market commitment); the Astoria routing A/B-solved and PROMOTED

**Keeper at entry:** `2026-09-04-nyiso-186-astoria-identity` (NOT-YET, grade 5,
{C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.4 %, C3c}).
**Solves: two** — the arm `2026-09-04-nyiso-187-astoria-routing` (bundle
`results/calibration/nyiso187_astoria_routing`) and the same-HEAD control on
the committed artifacts (bit-identical, registers nothing; slim files committed).

**Object 1 (PREREG §3, no LP, keeper sidecars 2024):** every NYC / LI / CH
`CT_PEAKER` / `CT_CHP` / `ST_GAS` deficit MW filled from the cheapest un-run
capacity at the LP's installed offer and bucketed against the model price and
the actual RT price: out of the money at BOTH 0.57–0.89 in every cell;
in-the-money-yet-unrun nil; no measured input wrong on its source. Owner =
out-of-market commitment (G). Post-hoc: with every markup removed 96 % (NYC) /
73 % (LI) of the `CT_PEAKER` deficit would clear at the model's own price — the
owner-accepted markup stack (nyiso-96 trade) is the separator; `CT_CHP` /
`ST_GAS` are out of merit on bare cost. **No CC lever; the 2024 cell is an
owner disposition.**

**Object 2 (rule 14):** `campd.CAMPD_UNIT_PLANT_REMAP` gains (55375, CT3 / CT4)
→ 57664 (caiso-196 form); the `-perunitmerit-` outage extract and tranche
artifact re-derived under their committed invocations (G-DELTA: only 55375 /
57664 rows; ramp envelopes excluded by the pre-registered stop; pooled
emissions not re-derived — footprint recorded). Zero config fields, zero DOF.
**A/B:** Astoria Energy II 4.679 → 4.275 / 4.683 → 4.229 / 4.661 → 3.067 TWh
(its 2025 outage now visible; EIA-923 2.116); Astoria Energy I 4.134 → 4.503 /
4.064 → 4.503 / 2.617 → 4.068 (EIA-923 4.078 / 4.150 / 3.900); class −0.016 /
−0.003 / −0.064. No criterion moves (C3a-2025 −10.4 → −10.3 %; C3b-2025 0.190 →
0.192). NOT-YET, grade 5, fails 3. **KEEPER CANDIDATE → PROMOTED BY OWNER
RULING** (standing formula): keeper shard + `status/NYISO.js`, `audit_keepers
--iso NYISO` PASS, gate-(a) stamp re-keyed (R-T), NYISO shard re-stamped
(`campd_per_unit_attribution`, `scuc_load_pocket_commitment`,
`tranche_startup_amortization` annotated), §5.5 rewritten. Retention pruned
`2026-08-22-nyiso-154-da-horizon`. Correction to nyiso-186 §3 / §5.2 appended
(the remap DOES reach the derives).

**Handed forward:** the 2024 cell as an owner disposition; the ramp-envelope
and emission-rate footprints of the routing (own A/B); `cc_capacity_reconcile`
(U); Bethlehem's vintage artifact; the merit-panel defect. Evidence:
`docs/FINDING-nyiso187-ct-steam-merit-position-2026-09-04.md`,
`results/calibration/PREREG-nyiso187-ct-steam-merit-position.md`.

## 2026-09-04 — nyiso-188 (`backcast-calibration` lane): the Astoria routing's remaining footprint carried, `cc_capacity_reconcile` tested and PROMOTED, Bethlehem attributed — the first NYISO keeper to read CALIBRATED

**Keeper at entry:** `2026-09-04-nyiso-187-astoria-routing` (NOT-YET, grade 5,
{C1-2024 `CC_REGULAR` +3.80 TWh / +3.1 pp, C3a-2025 −10.3 %, C3c}).
**Solves: five** — the same-HEAD control on the committed artifacts
(`nyiso188_control`, bit-identical, registers nothing; slim files committed),
Arm 1R `2026-09-04-nyiso-188-ramp`, Arm 1RE `-ramp-emis`, Arm 2 `-ccrecon`,
and the combined candidate `2026-09-04-nyiso-188-combined`. Pre-registration
pushed at `40536e07` before any arm was solved.

**Object 1 (the routing's footprint, zero parameters):** the ramp artifact
reproduces byte-identically from its committed invocation with the remap
stripped; re-derived, 55375 splits 1,252 → 626 + 626 MW obs (469 / 622 →
372 / 449 and 416 / 454) and the `(0, CC)` fallback moves 0.4907 / 0.5623 →
0.5000 / 0.5904 (14 CC groups / 1,355 MW read it). Arm 1R: engaged but inert
(318 / 2,565 / 5,307 price hours differ, largest per-plant annual |Δ| 0.0005
TWh, every criterion identical). The v2 emission curate did not apply the
remap (57664 at the 0.4206 default); repaired at the curate seam (+ derive
`--merge` / `--out`): 12 rows move, everything else exact / float noise;
57664 0.3947 / 0.3981 / 0.4144, 55375 0.3618 / 0.3639 / 0.3672. Arm 1RE −
1R: Astoria II mc −0.34 / −0.50 / −0.13 $/MWh, +0.024 / +0.028 / +0.002
TWh; no criterion moves.

**Object 2 (`cc_capacity_reconcile`, U → K):** the table reproduces exactly +
the 55375 raise row the routing creates (15 rows). The flag bounds final LP
capacity at CAMPD p99.9: −740 MW (Cricket Valley 1,266.6 → 1,048.9, Athens
1,178.8 → 1,027.4, Zeltmann 602.0 → 540.4, Valley, Flynn …); class
`CC_REGULAR` −1.47 / −1.76 / −1.99 TWh onto `ST_GAS` / `CC_CHP`; price +3.0 /
+3.3 / +3.7 %. **NOT-YET → CALIBRATED (grade 7, fails 0, C3c ledgered):**
C1-2024 `CC_REGULAR` +3.80 → +2.04 TWh PASS, C3a-2025 −10.3 → −6.9 % PASS;
regressions in band: C3a-2023 +4.8 → +7.9 %, C3a-2024 +0.5 → +3.8 %,
C3b-2023 0.123 → 0.134, C1-2023 `ST_GAS` +2.21 → +2.98. Cost of the pooled
p99.9 stated: Zeltmann 21 h / 2,268 MWh above its cap in 2024.

**Object 3 (Bethlehem 2539, measured, no solve):** the applied eGRID 2023
`PLHTRT` 9.665 is an EIA-923 generator-filing artifact — the steam
generator's net generation collapses to 6 % (2023) / 0.0 (2024) of its
2018–2022 share while the CTs run ~8,000 h; heat per CT-MWh invariant
(10.26–10.44); eGRID 2018–2021, CAMPD 2024–2025 full-block and the CT-heat
identity agree at ≈ 6.9–7.0 (+40 % applied). No threshold-free
source-internal identity reaches the applied vintage (S4); handed to the
owner as a two-form decision (pooled-vintage basis 7.85 vs CT-heat identity
with a cited steam share).

**Combined candidate → KEEPER (owner's standing formula):** CALIBRATED, grade
7, fails 0, C3c ledgered; keeper shard + `status/NYISO.js`, `audit_keepers
--iso NYISO`, gate-(a) stamp re-keyed, NYISO shard re-stamped
(`cc_capacity_reconcile` U → K; `ramp_envelopes`, `plant_emission_rates_v2`,
`egrid_identity_heat_rates`, `campd_per_unit_attribution` annotated), §5.5
rewritten. Retention pruned `2026-08-25-nyiso-155-hydro-control`,
`-hydro-repair`, `2026-08-30-nyiso-157-iroquois-companion`,
`-par-attribution`. **No marker requested** (NYISO holds neither `complete`
nor `final`; freeze active; the `complete` question is the owner's).

**Handed forward:** Bethlehem (owner decision, top); the 2024 residual as
nyiso-187's disposition at +2.05 TWh; C3a-2025 −6.9 % (Q1); Zeltmann's 2024
cold-weather record vs the pooled cap; the v2 artifact's frozen 2018 / 2022 /
2026 rows (forecast lane); NYISO parasitic factors absent. Evidence:
`docs/FINDING-nyiso188-astoria-footprint-cc-reconcile-bethlehem-2026-09-04.md`,
`results/calibration/PREREG-nyiso188-astoria-footprint-cc-reconcile-bethlehem.md`.

## 2026-09-04 — nyiso-189 (`backcast-calibration` lane): the steam-generator collapse census (Step 0 of the Bethlehem object) — ZERO SOLVE, owner decision card

**Keeper:** `2026-09-04-nyiso-188-combined` (CALIBRATED, grade 7, fails 0,
C3c ledgered), untouched. **Pre-registration** pushed at `65dc4094` before the
census ran. **Census (38 NYISO CCs with a filed CA generator):** T1 — steam
generator at exactly zero net generation while the CTs run — fires at
Bethlehem 2539 (2024 only), World Generation X 54131 (2023 only; applied
9.807 vs a 7.0–7.3 block), and chronically at Flynn 7314, Ravenswood 2500,
Lederle 10521. Bethlehem's APPLIED 2023 vintage (ST/CT 0.065 against its own
0.49–0.52) is not reached by the zero test; where filings are intact the
CT-heat identity reproduces eGRID's `PLHTRT` within 0.1 (its validation).
**Decision card** (`docs/DECISION-CARD-nyiso189-bethlehem-vintage-form-2026-09-04.md`):
A (pooled-vintage basis, fleet-wide, 2539 → 7.85) vs B1 (identity, T1-admitted,
misses Bethlehem 2023) vs B2 (identity admitted by the plant's own T1-clean
steam-share minimum; 2539 → 6.89, 54131 → 7.00); recommendation B2 with the
plant's own median share; expected direction if built: Bethlehem −$7.5/MWh,
C3a down in every year. Nothing built. Rule 28: `egrid_identity_heat_rates`
annotated, §5.5 top bullet updated. Evidence:
`results/calibration/_nyiso189_gen_collapse_census/`,
`scripts/probes/nyiso189_gen_collapse_census.py`.

## 2026-09-05 — nyiso-189 (`backcast-calibration` lane, second sitting): the owner-chosen form B2 built, A/B-solved and PROMOTED — `egrid_steam_collapse_heat_rates`, Bethlehem 2539 at its CT-heat identity

**Owner ruling (this sitting, `AskUserQuestion` on the decision card's three
questions):** form B2, the plant's own T1-clean median steam share, the
plant-history bound authorized. **Pre-registration**
`results/calibration/PREREG-nyiso189-steam-collapse-identity-ab.md` pushed
BEFORE the build and before any solve; it fixes the operational bound (the
literal "below the plant's own minimum" fires at 35 of 38 plants — the
mechanism reads the record's minimum minus the record's own range) and the
CT-side guard. **Built:** ONE field (default off), the derive over all 38
NYISO CCs (`egrid_steam_collapse_heat_rates_NYISO.csv`, `--check` reproduces;
applied-vintage reach EXACTLY Bethlehem 2539 9.665 → 6.877 and World
Generation X 54131 9.807 → 6.996), the identity-seam apply, CLI + replay
plumbing, tests, matrix row + six shard cells. **Solved:** the same-HEAD
control (BIT-IDENTICAL to the keeper, 0 of 52,560 prices differ ×3) and the
arm `2026-09-05-nyiso-189-steam-identity` (G-DELTA exactly the one field;
attestation with computed premises). **Result:** CALIBRATED → CALIBRATED
(grade 7, fails 0, C3c ledgered), no rejection-rule flip; Bethlehem 2.448 →
4.898 / 4.171 → 5.951 / 4.110 → 5.815 TWh, load-weighted price −2.8 / −2.0 /
−1.5 %; C3a +7.9 / +3.8 / −6.9 → +4.9 / +1.7 / −8.3 %; C3b 0.134 / 0.175 /
0.171 → 0.119 / 0.166 / 0.177; C1-2024 `CC_REGULAR` +2.05 → +3.33 TWh /
+2.8 pp (band 3.0 pp — the closest cell, nyiso-187's disposition at a larger
magnitude); C8 `ST_GAS` 19.7 / 23.6 / 18.3 %. **PROMOTED** under the owner's
standing formula: keeper shard, `status/NYISO.js`, `audit_keepers --iso
NYISO`, gate-(a) stamp re-keyed (R-T), NYISO matrix shard (cell
`egrid_steam_collapse_heat_rates` O → K, keeper + gates re-stamped), §5.5
header + queue. No marker requested; D56 (NYISO `complete`) is issued and
not landed — if it lands before this PR merges the merging session re-keys
`complete.NYISO` (D-5(b)). Evidence:
`docs/FINDING-nyiso189-steam-collapse-identity-2026-09-05.md`,
`results/calibration/_nyiso189_ab_report.json`,
`scripts/gen_nyiso189_attestation.py`, `scripts/probes/nyiso189_ab_report.py`.

### 2026-09-05 — nyiso-190 (`backcast-calibration`): the nyiso-189 promotion's one unmeasured justifying clause is measured on pre-registered bars and **REFUTED** — ZERO SOLVES, keeper unchanged

**Object:** the single clause standing between C1-2024 `CC_REGULAR` (+3.33 TWh
/ +2.8 pp, 0.2 pp inside its band) and a fail — FINDING-nyiso189 §3.1's *"the
NYC steam it displaces is what the market committed anyway"*. **Solves: ZERO.**
Bars pushed to `origin` before the first number
(`results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md`).
**Instrument:** the registered arm payload against `2026-09-04-nyiso-188-combined`
(the nyiso-189 sitting established its same-HEAD control BIT-IDENTICAL to it,
0 of 52,560 prices differing in every year) and the bench's per-plant CAMPD /
EIA-923 record. V1 verified both payloads reproduce the FINDING's own class
columns to ≤ 0.01 TWh before any bar was read.

**Result.** **B1 SUPPORTED** — the market *did* have the displaced units on
(`s_online` 0.750 / **0.839** / 0.834 of removed MWh at the 2 % bar).
**B2 REFUTED** — the model was running them harder than the market did:
**78.1 % of the 2024 displaced TWh moved TOWARD the plants' measured annual**
(`w_away` 0.139 / **0.219** / 0.375 on CAMPD; 0.216 on EIA-923, both bases
agreeing). The displacement *relieved a model over-run*; it did not deepen a
market-committed deficit. **B3 HOLDS** — the arm moves the six-class gas family
by 0.042 TWh at +1.87 from actual against ±3.82, so it is a genuine
within-family reallocation. **B4 fails the naming bar** — only **0.42** of the
2024 displaced TWh is downstate steam/cogen (0.76 `CC_CHP` / 0.46 `CC_REGULAR`
/ 0.30 `ST_GAS`; NYC 0.74 / Capital-Hudson 0.71 / Upstate-West 0.21), so the
set is not what the clause names. Every mover the lane was sent to check —
Ravenswood 2500, Arthur Kill 2490, East River 2493, Empire 56259, Cricket
Valley 57185 — is a plant the model was **over**-running on both actual bases.

**Consequence, pre-committed in PREREG §4 and executed:** on the `B2 < 0.50`
branch **no cell-G question goes to the owner** — the "re-open G vs accept"
card rested on a premise the evidence refutes. `scuc_load_pocket_commitment`
stays **`G`**; the nyiso-97 §5 bar and the nyiso-160 access closure stand, and
stop S2 records why this session could never identify it (the bar forbids
inferring the requirement from observed unit conduct — which this measurement
is). The CT half of the nyiso-187 disposition stands verbatim.

**What the measurement surfaced instead (POST-HOC, labelled, not a bar):** on
the keeper, 72 benched plants carry **+11.25 TWh of over-run against −8.18 TWh
of under-run** (net +3.07) — ~±8 TWh of offsetting plant-grain misallocation
inside a family the class totals say is pinned (±7.4 in 2023, ±9.3 in 2025).
The top of it is `CC_CHP` in all three years — Sithe Independence 54547 at an
annual **CF 0.93 against a measured 0.62** (9.478 vs 6.286 CAMPD / 6.158
EIA-923 TWh, 2024; 0.97 vs 0.62 in 2025), Brooklyn Navy Yard 54914 held at
≥95 % of nameplate for **8,172 / 6,226 / 6,714 hours against ZERO measured
hours** at that level, Empire 56259 2,041 h against 65 — and
`cc_capacity_reconcile` (cell **K**), the mechanism that bounds exactly this at
each plant's own CAMPD demonstrated peak, **is scoped to `CC_REGULAR` by
construction**; its committed 15-row NYISO table contains no `CC_CHP` plant.
**Neither built nor proposed here** (stops S1/S3): its direction on C1-2024 is
UNKNOWN and could go either way, so it is put to the owner as one question in
`docs/DECISION-CARD-nyiso190-cc2024-cell-disposition-2026-09-05.md` §4.

**Governance.** Keeper `2026-09-05-nyiso-189-steam-identity` unchanged — no
promotion, demotion, re-score or registration; no run was produced, so rule 15
has nothing to register and the dashboard is untouched. No mechanism tested, so
no matrix cell moves status; the NYISO shard's `scuc_load_pocket_commitment`
and `cc_capacity_reconcile` evidence lines and the §5.5 queue are updated, and
no other ISO's shard is touched. **No marker requested** — D56 has NOT landed
(NYISO still in `calibration-complete.json`'s `withdrawn` block at `c9f1d26e`),
so no rule-22 D-5(b) re-key applies. C3a-2025 untouched
(`DECISION-CARD-nyiso148` Q1 confirmed still pending). Evidence:
`docs/FINDING-nyiso190-cc2024-displacement-provenance-2026-09-05.md`,
`results/calibration/_nyiso190_displacement_provenance.json`,
`_nyiso190_plant_grain_posthoc.json`, probes
`scripts/probes/nyiso190_displacement_provenance.py` /
`nyiso190_plant_grain_posthoc.py`.

## 2026-09-05 — D56-R (capx governance records lane, ZERO SOLVES): NYISO `complete` RE-DECLARED on `2026-09-05-nyiso-189-steam-identity` — owner ruling Q38, executed per the withdrawn block's own `reentry` clause; validation tier returns, nothing spent; `frontier` NOT re-asserted (card C-10 / Q39 pending)

**Keeper:** `2026-09-05-nyiso-189-steam-identity`, untouched (no shard edit;
`frontier` stays withdrawn 2026-08-30). **Re-verified first, artifact-only**
(`scripts/calibration_verdict.py --run-id`, at origin/main `921bb4cd`):
CALIBRATED — C1 14/14 (free 10/10), C2 / C3a (+4.9 / +1.7 / −8.3 %) / C3b
(0.119 / 0.166 / 0.177) / C4 / C6 / C8 PASS; C3c the lone ledgered caveat
(RT >$300 h: 3 / 0 / 4 vs 10 / 13 / 42), grade 7, fails 0. **The ruling:**
Q38 (2026-09-04, capx r#35 card C-9, verbatim option "Re-declare now via a
records lane", ledger §0af amendment 1 / §3) was made on nyiso-188; D56 never
launched and the keeper moved to nyiso-189 (CALIBRATED → CALIBRATED), so the
charter's stop clause re-ran step 1 on the new id before anything was written
(D56-R, ledger §0ag.3). Cross-desk record: audit ruling R-AG (22:20Z) routed
the question to the calibration director for a recommendation; Q38 (23:18Z)
ruled the execution without sight of it; both the owner's, coexisting; card
C-10 is the recommendation R-AG asked for. **Written:** `complete.NYISO`
(declared 2026-09-05, keeper = keeper_at_declaration = nyiso-189, `by` = Q38
verbatim, determination as above, validation-only tier, locked test NOT
AUTHORIZED, `frontier_basis` NONE CLAIMED pending C-10, D-5(b) re-key policy,
THIRD-grant genealogy) with the 2026-08-30 withdrawal record moved WHOLE
beneath it (`prior_withdrawal_2026_08_30`, one dated `superseded` field added,
nothing deleted); `withdrawn` now holds CAISO alone; dated sentence appended
to the file note; `final`, `intake_log`, `withdrawn.CAISO`, the three other
`complete` entries and the freeze file byte-identical (asserted).
`audit_keepers --iso NYISO` PASS (M1a/M1b hold), `--check` PASS 0/0;
`holdout_policy.authorized(NYISO, validation)` False → True, locked False
unchanged, `frozen_tiers` = {locked_test}. **Forecast board:** NYISO gate (a)
FAIL → PASS on the literal §2.1b(2)(a) test (pass-form detail with the Q38
citation, derivation stamp `read_live_at`/`corrected_by` — never
forecast-provenance names), `closed_on` ['a'] → [], `marker_complete` true,
keeper display re-keyed, gate note / headline / gate_reading rewritten by
prepend + in-place annotation (the D19 text kept verbatim), two sources,
`gate_a_provenance` re-stamped (passers {ERCOT, NEISO, NYISO, PJM}),
`d56r_nyiso_redeclaration` records block; every other ISO's block and NYISO's
legs (b)/(c)/(d) byte-identical (asserted). `check_gate_a_provenance` OK 6/6;
`check_forecast_staleness` exit 0; `legitimacy_diagnostics --keepers` D-6/D-9
PASS. NYISO reads (a) PASS · (b) PASS · (c) PASS · (d) none — its §2.1b
candidacy re-opens; a campaign is a SEPARATE owner grant (D52 landed, C-12
arming; D59 issued). **Rule 28d:** NYISO matrix shard keeper/gates stamp
carries the marker state; no cell verdict moved; the shard's pre-existing
missing comma at the `egrid_steam_collapse_heat_rates` line (the nyiso-172
class — the file did not `node --check`, so the NYISO column was not
rendering) repaired by one character, disclosed. **Test pin moved with the
marker:** `test_marker_state_reflects_committed_markers` (NYISO withdrawn →
complete). **Pre-existing, not this lane's:**
`test_walk_inputs_trivial_single_year` (integration-marked) fails identically
at HEAD. **Spent: NOTHING. Solved: NOTHING.** Record:
`docs/handoffs/FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md`.

### 2026-09-05 — nyiso-191 (`backcast-calibration`): the `CC_CHP` scope extension of `cc_capacity_reconcile` is TESTED and **REJECTED on rule 19** — keeper unchanged, artifact reverted

**Markers:** D56 had landed at entry; `complete.NYISO` was already keyed to the
current keeper with its determination re-verified without a solve by the D56-R
records lane and `audit_keepers --iso NYISO` PASS, so the **rule-22 D-5(b) duty
was already discharged** — nothing re-keyed, no marker requested. Training years
only.

**Solves: TWO** — `nyiso191_control` (registered `2026-09-05-nyiso-191-control`,
**BIT-IDENTICAL to the keeper**: 0 of 52,560 P1 zonal prices differ in each of
2023/2024/2025) and the arm `nyiso191_ccchp_scope` (registered
`2026-09-05-nyiso-191-ccchp-capacity`, **a REJECTED PROBE**). Bars pushed before
the derive was edited and before any solve
(`results/calibration/PREREG-nyiso191-ccchp-capacity-scope.md`).

**Phase 0 refuted the session's own premise before the build.** The frozen
population rule reaches none of the three over-runners nyiso-190 named: **Sithe
Independence 54547** gets a **RAISE** (demonstrated peak 1,170 MW *exceeds* its
1,157.8 MW model capacity — its +3.19 TWh over-run is a **DUTY** defect, not a
capacity one), **Brooklyn Navy Yard 54914** is declined by the frozen CT-only
guard, **Empire 56259** sits inside the frozen 1.10 margin. The widening reaches
8 small/mid cogen rows, net −542.5 MW, and phase 0 predicted energy-inertness in
advance (model energy above the caps 0.0000 / 0.0143 / 0.0000 TWh). It was run
anyway on a rule 14 + rule 13 licence stated before the build.

**Every bar came back as pre-registered.** V1 control bit-identical; V2 no other
ISO's table moves (NEISO/CAISO/PJM/MISO byte-identical at the default; ERCOT's
raise-path filter proven identical); G-DELTA the artifact alone; B1 engaged
(19 caps / −1,282 MW vs 12 / −740 MW); **B2's falsifiable prediction HELD**
(worst gas-family movement **0.0034 TWh** vs a 0.05 TWh bar); **B3 no
criterion-level status flip** — CALIBRATED, grade 7, C3c ledgered on both sides,
every magnitude ≤ 0.01 TWh (C1-2024 `CC_REGULAR` +3.33 → +3.34 TWh).

**REJECTED ON RULE 19 `[R-ONE-MECH]`, NOT on the residual.** Chasing why only
2 of 8 plants' LP capacity moved found the cause: **`chp_layup_duty_curve`**
(row `offer_curve_by_group`, NYISO cell **K**, keeper-armed, nyiso-149) already
withholds those plants to a **measured price-conditional duty that binds tighter
than the demonstrated-peak cap at every one of its 6 cohort members** — Selkirk
199.4 vs 378.0 MW, Lockport 48.9 vs 142.3, Yerkes 28.2 vs 54.6, Oswego 37.1 vs
58.5, Beaver Falls 34.1 vs 84.6, Olean 45.5 vs 80.9. The widening would stack a
second bound on an owned phenomenon. The two rows outside the cohort pull
**opposite** ways: World Generation X improves (CF 0.675 → 0.523 vs a measured
0.353) while **Sithe's raise pushes the worst over-runner further out** (0.932 →
0.939 vs 0.618). **Structural integrity does not improve** — the plant-grain
offsetting misallocation is unchanged (7.38 / 8.18 TWh) and 0.07 TWh *worse* in
2025 — so it fails the *antecedent* of the owner's standing formula, not its
consequent.

**Disposition.** Keeper unchanged. The canonical
`cc_capacity_reconcile_NYISO.csv` is **reverted** to the `origin/main` blob
`e0b1610` (hash-verified) so the keeper reads its own table; both solves' tables
are preserved bundle-local. The derive's `--classes` argument is **kept**
(default `CC_REGULAR`, V2-proved a no-op for every ISO) with tests asserting no
committed table carries a widened scope. NYISO matrix shard + §5.5 queue updated
in-session.

**Handed forward.** (1) **Sithe 54547 is an un-owned DUTY object** — CF 0.93 /
0.97 vs a measured 0.62, outside both mechanisms' reach, the largest single
per-plant over-run in the fleet. (2) **`ST_GAS` is a ZONAL placement error**
(measured, no lever proposed): sign stable in all four zones, all three years —
NYC over (+4.26 / +2.24 / +0.41), Long Island under (−1.65 / −2.26 / −2.28),
Capital-Hudson under (−0.95 / −1.03 / −1.66), Upstate-West under; the class net
hides 3.28 / 2.53 / 0.84 TWh of offsetting misallocation. (3) **The derive's
CT-only test is pooled** and was diluted by World Generation X's zero 2025
EIA-923 row — the bench's per-year test flags it at 1.378× — affecting exactly
the one row that bound; a cross-ISO rule-23 repair.

Evidence: `docs/FINDING-nyiso191-ccchp-capacity-scope-2026-09-05.md`,
`results/calibration/PREREG-nyiso191-ccchp-capacity-scope.md`,
`_nyiso191_ccchp_scope_phase0.json`, `_nyiso191_stgas_placement.json`,
`scripts/gen_nyiso191_attestation.py`, probes
`scripts/probes/nyiso191_ccchp_scope_phase0.py` / `nyiso191_stgas_placement.py`,
`tests/curation/test_derive_cc_capacity_reconcile_scope.py`.

## 2026-09-05 — D56-R2 (capx governance records lane, ZERO SOLVES): NYISO `frontier` RE-DECLARED on `2026-09-05-nyiso-189-steam-identity` — owner ruling Q39 (card C-10), both instruments back as the 2026-08-30 withdrawal removed both; four-instrument alignment reads {ERCOT, NEISO, NYISO, PJM} on every leg; nothing spent

**Keeper:** `2026-09-05-nyiso-189-steam-identity`, untouched (no promotion field
edited). **Re-verified first, artifact-only** (`scripts/calibration_verdict.py
--run-id`, at origin/main `ee7754c1` and again at `8342d74d` after the rebase):
CALIBRATED — C1 14/14 (free 10/10), C2 / C3a (+4.9 / +1.7 / −8.3 %) / C3b
(0.119 / 0.166 / 0.177) / C4 / C6 / C8 PASS; C3c the lone ledgered caveat
(model 3 / 0 / 4 h vs RT 10 / 13 / 42 h > $300, rubric v3.3 standing rule, NOT a
PASS). **The ruling, verbatim** (capx ledger §3 Q39): "RULED 2026-09-05 (r#37) —
RE-DECLARE FRONTIER ON nyiso-189 (both instruments, as the withdrawal removed
both)." — card C-10 option A, the recommendation R-AG asked for. **Shard:**
`keepers/NYISO.json` gets a live `frontier` block (declared 2026-09-05,
`keeper_at_declaration` nyiso-189, `by` = Q39 verbatim, `basis` = Q39 restoring
ASSESSMENT-nyiso154-frontier-2026-08-22.md §3/§2/§4, `not_final`, `recorded_by`);
the reverted 2026-08-23 ratification block (its 2026-08-30 currency annotation
and `reverted_2026-08-30` inside it) moves WHOLE to `frontier_withdrawn_2026_08_30`
with one dated `superseded` field appended, nothing deleted; `frontier_cleared`
(2026-08-06) untouched beneath — the five-layer genealogy declared 07-31 →
cleared 08-06 → ratified 08-23 → reverted 08-30 → re-declared 09-05. **Marker:**
`complete.NYISO.frontier_basis` NONE CLAIMED → the declaration (keeper + date +
Q39 citation), prior text carried as a dated "WAS:" clause; a dated append to the
file-level note; every other byte of the entry, every other ISO, `withdrawn`,
`final`, `intake_log` asserted identical. `status/NYISO.js` rebuilt because the
auditor's S1 check asked (only `keeper.frontier` + timestamp moved).
**Auditor / guards:** `audit_keepers --iso NYISO` PASS 0/0; `check_gate_a_provenance`
OK 6/6 with NO gate-(a) leaf moved (frontier is not a gate-(a) input;
`program-status.json` untouched); `check_mechanism_matrix` OK, no re-stamp
asked; `legitimacy_diagnostics --keepers` D-6/D-9 PASS; 100 scoring tests pass.
**Four-instrument alignment at `8342d74d`:** frontier · `complete` · gate-(a) ·
ISO-level determination ALL read {ERCOT, NEISO, NYISO, PJM} — the split D56-R
recorded on the frontier leg alone is closed by the owner's choice; stated for
the audit desk (Z-4), whose board this lane does not edit. **Frontier is NOT
`final`:** `final` still empty, the freeze untouched (locked tier frozen for
every ISO), 2019 / H1-2026 never granted. **Spent: NOTHING. Solved: NOTHING.**
Record: `docs/handoffs/FINDING-capx-d56r2-nyiso-frontier-2026-09-05.md`.
### 2026-09-05 — nyiso-192 (`backcast-calibration`, frontier adjudication for card C-10 / Q39): the two nyiso-191 hand-forwards decomposed with NO LP, a dashboard-payload defect found and repaired, the Astoria merit-panel repair A/B-solved — keeper unchanged, frontier NOT declared

**Result.** Keeper `2026-09-05-nyiso-189-steam-identity` unchanged (CALIBRATED,
grade 7, fails 0, C3c ledgered; re-verified artifact-only after its payload was
re-rendered). Two solves: the keeper replayed IN PLACE as the control (every
committed sidecar byte-identical) and ONE arm, `2026-09-05-nyiso-192-astoria-panel`
— the Astoria merit-panel stack-duplicate repair (nyiso-184 §4.1, the last live lever in the record), which moves the WHOLE steam fleet's availability (106 Astoria windows out, 155 windows at fifteen other plants in; Ravenswood 2024 0.478 → 0.260). Every B2 prediction held; C2 / C3a / C3b / C8 no flip (C3a-2025 −8.3 → −7.3 %); **C1-2024 `CC_REGULAR` flips PASS → FAIL (+3.33 → +3.68 TWh, +3.0 pp)**; NOT-YET; structural integrity better in 2024 / 2025, worse in 2023. Not rejected under the pre-registered rule — OWNER CALL (card nyiso192-Q1); promoting it would put a NOT-YET keeper under `complete` (Q5-W).

**The instrument defect.** `render_calibration_html`'s model-payload CHP add-back
used the 35 % sector share while the LP held out the MEASURED share (0 % at Sithe
Independence): 6.6 TWh of flat phantom energy across the 2024 `CC_CHP` class,
2.14 TWh at Sithe. Repaired at the call site (the run's own hold-out map; pinned
by `tests/scoring/test_render_chp_addback_measured.py`), the keeper's payload
re-rendered under its own id (non-CHP plants byte-identical; CHP identity closes
to ≤ 0.0001 TWh). **nyiso-190 §3's ±8 TWh plant-grain misallocation reads
8.4 / 7.0 / 6.9 TWh; nyiso-191's Sithe over-run +3.19 / +3.48 reads +1.04 /
+1.31.** Fourteen older NYISO payloads still carry the defect (flagged).

**Object 1 — Sithe 54547:** INADMISSIBLE / IDENTIFICATION-BLOCKED. The census rule
declines it correctly (0 of 18 zero-median cells, online 0.844); the corrected
residual is level-when-on (four trains at 80 % of HSL), half of 2024's in
trough-flip hours (the owner-court compression object), the rest unidentifiable
in-repo (no F923 filing; no regulation product; NYCA reserves hydro-saturated).
**Object 2 — `ST_GAS` zonal placement:** NYC over ← the zonal delivered-gas basis
(Transco Z6 NY hub vs Iroquois Z2; plant-level receipts unfiled) → identification
intake, with the one in-repo alternative (the CT leg's LDC index) REFUSED EX ANTE
(shifts NYC steam +$34–53/MWh to 0.4–1.3 % in-merit → ~100 % floor-forced → C8 by
construction → cell G); LI / CH under ← out-of-market commitment (G) + C3a-2025
(Q1). Ravenswood's HR term is closed (nyiso-185 K).

**Measured, not acted on:** on the current keeper, `ST_GAS` is forced **0.393 /
0.414 / 0.305** at UNIT grain (D-2's own `at_floor_mask`) against the committed
plant-grain C8 0.197 / 0.236 / 0.183 and the 0.30 cap — the C8 PASS is
instrument-dependent (scorer lane, cross-ISO; nyiso-181 §6's escalation now
measured).

**Frontier:** mechanism set EXHAUSTED at the current representation (YES — every object since nyiso-154 dispositioned); a declaration NOT recommended until the owner rules the C8 grain and the Astoria arm (card C-10 / Q39, options A/B/C; nyiso192-Q1). Records:
`results/calibration/ASSESSMENT-nyiso192-frontier-2026-09-05.md`,
`docs/DECISION-CARD-nyiso192-frontier-2026-09-05.md`,
`docs/FINDING-nyiso192-frontier-adjudication-2026-09-05.md`,
`results/calibration/PREREG-nyiso192-frontier-adjudication.md` (+ Amendment 1),
`_nyiso192_*.json`, probes `scripts/probes/nyiso192_*.py`,
`scripts/gen_nyiso192_attestation.py`, bundle `nyiso192_astoria_panel`.

### 2026-09-05 — nyiso-193 (`backcast-calibration`, records only, ZERO SOLVE): Q39 found RULED and executed; the arm question re-labelled; two owner-court records filed

Keeper unchanged. **Q39 was ruled at r#37 (card C-10, option A) and executed by D56-R2 —
`frontier` is DECLARED on `2026-09-05-nyiso-189-steam-identity`**; the nyiso-192 assessment's
"not recommended now" stands as the lane's record, its two conditions (the D-2 / C8 grain;
the Astoria-panel arm) now conditions on the declared frontier's durability. The arm question
is re-labelled **nyiso192-Q1** (the ledger's Q40 is MISO's C-11) and is UNRULED — the arm is
not promoted (rule 22 D-5(b): a promotion that worsens a `complete` ISO's determination stops
and escalates). The fourteen-payload records item is MOOT after the r#38 keeper-only site
prune. Filed: `docs/INTAKE-SPEC-nyiso193-nyc-steam-delivered-gas-2026-09-05.md` and
`docs/DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md`.
### 2026-09-05 — nyiso-193 (`backcast-calibration`, PROMOTION, zero new solve): the nyiso-192 Astoria merit-panel arm PROMOTED by owner ruling (nyiso192-Q1 (i)); NOT-YET — `complete` + `frontier` WITHDRAWN under the Q5 uniform rule; next lever ruled
**Keeper → `2026-09-05-nyiso-192-astoria-panel`** (bundle `nyiso192_astoria_panel`), superseding
`2026-09-05-nyiso-189-steam-identity`. Owner ruling in session, verbatim: *"Ok promote it ugh how does this keep happening with NYISO? Promote it and then tune the cc regular offer curve up for the duct burner peaking tranche because it's merit order is wrong it runs more often at lower CF and is running hot over 80% CF in all years"*
**What it is:** the nyiso-189 recipe, ZERO `scenario_config` changes, on the `-perunitmerit-`
outage extract re-derived after the merit-panel stack-duplicate repair (Astoria 8906's paired flue
paths priced as one generator at physical SRMC; 106 Astoria windows out, 155 in at fifteen other
plants — the whole steam fleet's availability moves). The repaired extract is now the COMMITTED
`data/raw/campd-unit-outages-perunitmerit-NYISO.csv` (+ layup companion, `.meta.json`; sha256
58799099…), matching the keeper's `resolved_inputs` pin (rule 23: the panel repair is the cited
data change). **Determination NOT-YET** (artifact-only `calibration_verdict`): grade 6 of 8, fails 2
— C1-2024 `CC_REGULAR` +3.33 → +3.68 TWh / +2.8 → +3.0 pp (the cell-G fill; the D-5(b) stop FIRED
and was escalated on the card; the owner chose it with the cost), C3c 3 / 0 / 4 h (unchanged, FAIL
because no longer lone); C2 / C3a (+4.8 / +3.2 / −7.3 %) / C3b (0.118 / 0.172 / 0.167) / C4 / C6 /
C8 (`ST_GAS` 17.1 / 23.8 / 18.6 %) PASS. **Records act, one commit:** `keepers/NYISO.json`
(keeper, promotion / determination notes, `superseded` chain, `frontier` → `frontier_withdrawn_2026_09_05`),
`calibration-complete.json` (complete.NYISO → withdrawn.NYISO, the D56-R entry nested whole,
`reentry` clause naming the ruled lever), `program-status.json` (gate (a) pass → fail, keeper
display, `nyiso193_promotion_withdrawal` block; Q45 campaign footing FLAGGED for the director),
`status/NYISO.js` rebuilt, matrix shard + §5.5 header re-stamped, sidecar relabelled KEEPER;
nyiso-189 pruned from the site under the r#38 keeper-only retention (`--force-uncite`, as
ercot-248). `audit_keepers --iso NYISO` PASS; matrix guard PASS; parity PASS; `check_gate_a_provenance`
NYISO row PASS (the MISO row fails on a pre-existing miso-217 stamp drift — not this lane's).
**Also repaired (stop-the-line, rule 27):** six committed JSON files carried unresolved
rebase-conflict markers on `main` — the arm bundle's `meta.json` / `metrics.json` / `run_config.json`
(my nyiso-192 rebase paired them with unrelated files by rename detection),
`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing{,-headbasis}/run_config.json` and
`results/calibration/ercot248_two_config_keeper/metrics.json` — each restored byte-for-byte from
its last legitimate blob (`6c695a57` / `5bb70047` / `4b7a515e`), all six parse. `calibration_verdict`
could not read the arm at all before this. **Next lever (owner-ruled, top of §5.5 queue):** the
`CC_REGULAR` duct-burner peaking tranche offer tuned UPWARD from measured duct-firing conduct —
phase 0 → pre-registration → rule-29 one-year screen (this keeper's committed bundle the control) →
full span. **Marker consequence at full magnitude:** the third NYISO structure-over-gates promotion
to take the marker down (07-19, 08-30, today); `complete` = {ERCOT, NEISO, PJM}; nothing spent;
`final` untouched.
### 2026-09-05 — nyiso-194 (`backcast-calibration`, phase 0 + TWO one-year screens, rule 29): the owner-ruled `CC_REGULAR` duct-burner peaking-tranche lever — symptom CONFIRMED, both arms KILLED on frozen structural gates, keeper unchanged
Keeper `2026-09-05-nyiso-192-astoria-panel` unchanged; nothing registered; no full span.
**Phase 0 (zero LP, `scripts/probes/nyiso194_cc_peak_phase0.py`):** the owner's two claims hold at
full magnitude — the class's MW-weighted 80–90 % loading share is 27.9 / 33.0 / 26.8 % vs CAMPD
6.0 / 5.8 / 7.1 %, 90–100 % 18.6 / 19.7 / 16.6 vs 27.6 / 33.9 / 27.1, online plant-hours +20–25 k
in 2024/2025. But no measurement identifies a HIGHER peak offer (CAMPD top-band incremental HR
1.0–1.5× base; duct firing appears at the LBMP the model's peak tranche already clears); the band
SIZE is what disagrees with conduct (860 gap 22.6 / 28.2 / 16.9 % vs CAMPD reach 5.7 / 5.8 / 0.6 %).
**PREREG pushed `aa3038d1` before the solves; screen year 2024 (largest footprint, 1.15 TWh); control =
keeper (form 4; G-DRIFT `d5bba63b..HEAD` all INERT).** **Arm S** `cc_duct_peaking_cap_pct=8.0`: S-1/S-2
PASS, **S-3 FAIL** — class 80–90 % share 33.0 → 36.3 % (plants park under the new 92 % wall).
**Arm D** peak 2.25 → 2.50 (diagnostic): D-1 PASS, **D-2 shape AWAY from CAMPD** as predicted —
peak energy 1,253 → 680 GWh, 90–100 % share 19.8 → 17.2 %, `CC_REGULAR` −0.45 TWh (would put
C1-2024 in band by the wrong shape — rule 1). **What both locate:** the econ ramp's marginal slice
is the parking point; NYISO's registered `phys_econ_low 0.784 → phys_econ_high 0.925` slopes the
other way from the registered 0.95 → 1.0. **Next (top of §5.5 queue, U, needs its own PREREG):**
the econ block at its measured marginal basis. Records: `docs/FINDING-nyiso194-cc-peak-tranche-screens-2026-09-05.md`,
`results/calibration/PREREG-nyiso194-cc-peak-tranche-screen.md`, `_nyiso194_*.json`,
`scripts/probes/nyiso194_*.py`; matrix cells `cc_duct_peaking` (cap R) / `offer_curve_by_group`
(upward-peak direction R) updated. Screen bundles local, never registered.

### 2026-09-05 — nyiso-195 (`backcast-calibration`, phase 0 + ONE one-year screen, rule 29): the `CC_REGULAR` econ ramp at its own measured marginal basis — phase 0 REFUTES the marginal-slice premise, the 2024 screen is KILLED on E-3, C1-2024 WORSENS; keeper unchanged
Owner (in session): *"Only run 2024 to see if it fixes the c1 gas cc miss. C3c is an acceptable
caveat and known limitation of this model type."* / *"No control arm just use the last keeper."*
Keeper `2026-09-05-nyiso-192-astoria-panel` unchanged; nothing registered; no full span; no control solve.
**Phase 0 (zero LP, `scripts/probes/nyiso195_econ_basis_phase0.py`, keeper committed artifacts only —
its `dispatch/` is gitignored-absent, so the control is the on-recipe `fleet_only` rebuild + the
payload-decoded per-plant hourlies + the hourly sidecars):** under the armed `gas_offer_net_revenue_margin`
the econ ramp is the ONLY `CC_REGULAR` band carrying a markup (a falling 4.03 → 2.10 $/MWh fixed
margin), and it cancels the rising phys basis so the keeper's ramp is FLAT within $0.25/MWh (the six
slices carry 2.78–2.80 TWh each). Of the class's 28,778 plant-hours in 80–90 %, 71.8 % sit at the
top of the AVAILABLE econ ramp, 27.4 % in partial duct dispatch, 0.7 % on a marginal slice — the
nyiso-194 §3 premise does not hold. CAMPD ramp sign confirmed (10/14 plants rising; cap-weighted
marginal/avg-full HR 0.833 → 1.056). **PREREG pushed `9a0b80fe` before the solve with the prediction
written in it (E-3 fails; `CC_REGULAR` +≤0.95 TWh; C1-2024 worsens); G-DRIFT `d5bba63b..HEAD` all
INERT.** **Screen 2024** (`replay_keeper --offer-curve-json '{"CC_REGULAR": {"econ_low": 0.784,
"econ_high": 0.925}}'`, `scripts/probes/nyiso195_screen_gates.py`): E-1/E-2 PASS (exactly the 96
`CC_REGULAR` econ rows change; arm `mc` = keeper `mc` − markup × anchor to 2e-5; nothing else
moves); **E-3 FAIL** — 80–90 % share 33.0 → 33.5 (CAMPD 16.5), 90–100 % 19.8 → 19.6 (33.9);
E-4 no flip (C3a-like −0.72 → −1.63 %, NRMSE 0.183 → 0.181, gas family 68.22 → 68.25 TWh).
**C1-2024 `CC_REGULAR` +3.68 → +4.34 TWh / +3.0 → +3.5 pp (now out on volume AND share)** —
the owner's question answered: a pure price cut on an over-running class cannot lower its energy.
Direction R (matrix `offer_curve_by_group`, `gas_offer_net_revenue_margin` annotated; cells K).
**Next (top of §5.5, U):** the AVAILABILITY side of the wall — the partial-derate / outage series
at the pile-up CC plants vs CAMPD's hours above 90 % — a rule-14 data question, phase 0 first.
Records: `docs/FINDING-nyiso195-cc-econ-basis-screen-2026-09-05.md`,
`results/calibration/PREREG-nyiso195-cc-econ-basis-screen.md`, `_nyiso195_*.json`,
`scripts/probes/nyiso195_*.py`. Screen bundle `results/calibration/nyiso195_screen_2024` local, never registered.

### 2026-09-05/06 — nyiso-196 (`backcast-calibration`, decomposition + ONE rule-29 2024 screen + ONE 2023–2025 bundle, NO control solve): the C1-2024 `CC_REGULAR` over-run is an AVAILABILITY object at Cricket Valley — an EIA-860 id collision halves its unit-outage derate; repaired with the zero-DOF `unit_outage_extract_basis_share`, screen CLEARED, full span CALIBRATED, PROMOTED
Owner (in session): *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."* — plus the nyiso-194/195
instructions (2024 screen first, the keeper as the control).
**Steps 1–3 (zero LP, `scripts/probes/nyiso196_cc_overrun_decomp.py`, `nyiso196_rebuild_checks.py`):**
buckets (a) model-on/meter-off +1.18 / +1.47 / +2.27 TWh, (b+) +4.05 / +3.62 / +3.99, (b−) −3.77 /
−3.33 / −3.56, (c) −0.84 / −0.58 / −1.15 (2023 / 2024 / 2025); the class net's growth is bucket (a),
466 of 1,471 GWh at Cricket Valley 57185 in 2024, flat by hour-of-day, in its outage months, 97.1 % of
its hours with the zone LMP above the committed offer — plain economics on the availability the LP was
GIVEN: **99.9 % of it in hours the LP was handed more availability than the committed extract states**
(671 h in all-blocks-out windows). Bridge binds 40 h; no reliability floor; delivered gas equals the
measured hub monthly (CH / LI / NYC ratio 1.000 in 11 of 12 months); import capability never binds
below the measured flow (0 h); the `ST_GAS` deficit is the cell-G object. **The defect:** CAMPD stack
ids `U001`–`U003` match EIA-860 generator ids `U001`–`U003`, the plant's STEAM turbines (CA, 174.2 MW;
the CTs are `U004`–`U006`), so the deriver writes each 1×1 block at 174.2 MW (`eia_exact`, plant 522.6)
and the loader divides by the 1,016.8 MW net-summer bin — 17.1 % per block vs 33.3 %; three blocks out
leave 48.6 % available. **The repair:** `ScenarioConfig.unit_outage_extract_basis_share` (default off,
registered, matrix row + 6 shard cells, unit tests) — the removed fraction on the extract's own basis
for CC bins (steam keeps `unit_outage_st_capacity_basis`); census 17 CC bins move in 2024, 0 steam;
57185 −1.83, Selkirk −1.58, Linden +0.33, Athens +0.27 TWh available. **PREREG pushed `64cc970b`
before the screen (G-DRIFT `d5bba63b..5b5af5ab` all INERT).** **Screen 2024 CLEARED:** F-1/F-2 PASS
(128 CC units move, mc/pmax byte-identical, ratio identity 3.6e-6), S-3 PASS (Cricket Valley dark-window
energy 257 → 0 GWh, 5,038 → 3,706 GWh vs 4,241 meter, Selkirk 261 → 48), S-4 PASS (no load-bearing
flip). **Full span `2026-09-06-nyiso-196-extract-basis`: NOT-YET (grade 6, fails 2) → CALIBRATED (grade 7,
fails 0, C3c ledgered); C1 14/14 free 10/10; C1-2024 `CC_REGULAR` +3.68 → +3.01 TWh / +3.0 → +2.5 pp;
2023 +1.08 → +0.83; C3a +4.8/+3.2/−7.3 → +4.6/+4.7/−6.9 %; C3b 0.118/0.172/0.167 → 0.119/0.175/0.154;
C8 `ST_GAS` 17.1/23.8/18.6 → 16.6/22.4/18.2 %.** Attested (`gen_nyiso196_attestation.py`: G-DELTA
exactly the flag, same extract sha `58799099…`, DOF 13/6 verbatim); `audit_keepers --iso NYISO` PASS
(the capx D60 `ccs_retrofit_capex_co2_scaling` HEAD-default flip declared as a non-delta). **PROMOTED**
(keeper shard, `status/NYISO.js`, matrix stamp); the former keeper stays on the dashboard (protected by
governance citations). Regressions at full magnitude: Linden 50006 `CC_CHP` 6.2 → 5.2 TWh vs a 7.3 meter
every year (availability up); Cricket Valley now 0.53 TWh UNDER in 2024; C3a-2024 +1.5 pt. `complete`
NOT re-declared — owner court (withdrawn-block re-entry clause). Records:
`docs/FINDING-nyiso196-cc-outage-share-basis-2026-09-05.md`, `PREREG-nyiso196-cc-outage-share-basis-screen.md`,
`_nyiso196_*.json`, `scripts/probes/nyiso196_*.py`.

## 2026-09-06 — nyiso-197: the Linden 50006 regression is VOID (a CHP add-back basis mismatch); the real object has the opposite sign; ZERO solves, keeper unchanged

**Keeper unchanged:** `2026-09-06-nyiso-196-extract-basis` (CALIBRATED, grade 7, fails 0, C3c
ledgered). **Nothing registered, no PREREG, no LP run** — phase 0 only, on committed artifacts
plus two `fleet_only` rebuilds of the keeper's own `meta.json`.

**The premise is refuted.** The nyiso-196 hand-forward — *"Linden 50006 falls ~1.0 TWh in every
year away from a 7.2–7.4 TWh meter although its own availability ROSE"* — is not in the committed
artifacts. Decoding both registered payloads on the same basis, Linden goes **6.325 → 6.549 /
6.197 → 6.440 / 6.162 → 6.390 TWh: it GAINED +224 / +243 / +227 GWh**, exactly what its own
availability census (+302 / +326 / +314 GWh available) predicts, and it is the second-largest
gainer of the energy Cricket Valley released in all three years. The §4.2 row mixed two bases —
*keeper* column = the prior keeper's **payload** (full plant, carrying the measured 1.25 TWh/yr
CHP add-back), *arm* column = the arm's **LP grid** series (no add-back). Linden is the only plant
in that table with a non-zero measured BTM hold-out, so it is the only row the mismatch can move;
every other row reproduces to the digit, `CC_CHP` control Sithe 54547 (measured share 0.0 %)
included. Provenance is nyiso-196's own record: `_nyiso196_screen_gates.json`
`S3_direction.moved_plants[1]` carries `keeper_gwh` 6196.9 (payload) against `screen_gwh` 5235.5
(LP) — the 5.24 printed in §4.2. The row is self-refuting: an availability RISE producing a 15 %
energy fall at a plant online 8,760/8,760 h has no mechanism.

**Step 2 — no measured object survives**, so no arm was pre-registered and no LP was spent.
(a) Availability is the extract's own scale-invariant share and the plant is **not capacity-bound**
(at its envelope only 896 / 586 h; 416 / 467 GWh of headroom unused). (b) LP `pmax` 757.76 MW is
within 2.8 % / 1.3 % of NYISO's registered net capability (737.1 / 748.2 MW summer, Gold Book
Table III-2a), and the 22.21 % hold-out is itself the Gold-Book ÷ 923 measurement;
`chp_layup_duty_curve` is armed but its census deliberately abstains at Linden. (c) The VFT limb is
refuted — the Gold Book carries Linden Cogen as an **internal NYCA Zone-J station** (PTID 23786),
and nyiso-196's I-1 already measured 0 of 8,760 h of binding import capability. (d) Delivered gas
is a real unrepaired mismatch (a Linden **NJ** plant on Transco Z6 **non-NY** charged the NYC
citygate, matched 11/12 months in both years) but there is **no committed Z6 non-NY series** to
swap and the direction is wrong for the residual — an intake ask, not a screen.

**The cell, RE-SPECIFIED with the opposite sign (owner court).** Against NYISO's Gold Book net
energy for the station (4,390.7 / 4,288.7 GWh, CY2023 / CY2024) the keeper's LP grid dispatch is
**+904.9 / +901.8 GWh OVER (+20.6 % / +21.0 %)** — the extract-basis repair *increased* it (prior
keeper +680.9 / +658.8) — and Linden alone is **+0.814 of the `CC_CHP` class's +2.327 TWh** 923
over-run in 2024. It is an **offer-position** object: the committed band's assembled `mc_base`
($23.36 / $27.19) clears the modelled NYC LMP in **99.8 % / 98.7 %** of below-envelope hours, and
the LP runs the plant at **79.8 % / 78.2 %** CF where the market ran the station at
**68.0 % / 65.4 %**. A `CC_CHP` band multiplier may only be pre-registered on an owner ruling with
an ex-ante, non-residual ground (rule 1 carve-out (a)–(e)); this session proposes no value.

**Also filed.** (i) A scorer-side card: the run-page plant table compares a 923-net-basis model
reconstruction to a CEMS-**gross** meter; at Linden the CAMPD series peaks 27–34 % above NYISO's
registered station capability and the repo's own `parasitic_load_factors.parquet` flags plant
50006 **`out_of_band`** in every year (net/gross 0.743, 0.97 class default substituted). No LP
consequence — the shares CAMPD feeds the LP are scale-invariant. (ii) An add-back-basis assertion
for the screen-gate probe pattern (both sides of a plant-grain comparison must declare their
basis; `_nyiso192_payload_addback_audit.json` is the mirror defect). (iii) Cricket Valley 57185's
part-load bucket (b−) is untouched and is now the queue's live plant-grain item.

**Record corrections made (annotated, never rewritten):** `FINDING-nyiso196` §4.2 + §6 item 1;
`docs/mechanism-testing-matrix.md` §5.5 (new nyiso-197 queue block; the nyiso-196 top-of-queue item
struck); `docs/codebase-site/data/mechanism-matrix/NYISO.js` (the `gates` stamp and the
`unit_outage_extract_basis_share` evidence — **cell stays K, no verdict moves, no field touched**).
Records: `docs/FINDING-nyiso197-linden-addback-basis-2026-09-06.md`,
`results/calibration/_nyiso197_linden_phase0.json`, `_nyiso197_linden_rebuild_{2023,2024}.json`,
`scripts/probes/nyiso197_linden_phase0.py`, `scripts/probes/nyiso197_linden_rebuild.py`.

## 2026-09-06 — nyiso-198: Cricket Valley's (b−) is a duct-BAND-MEMBERSHIP object; the 2024 screen's own S-4 gate STOPPED the arm; keeper unchanged

**Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`** (CALIBRATED, grade 7 of 8, fails 0,
C3c the lone ledgered caveat). **Nothing registered, nothing promoted.** ONE solve — the rule-29
2024 screen, deleted before merge (29(c)). No control solve (form 4; G-DRIFT `5b5af5ab..982ba9aa`
all INERT, re-checked after rebasing onto `821c11c5`: the 31 new commits touch zero solve-path
files). Full record: `docs/FINDING-nyiso198-duct-peaking-row-scope-2026-09-06.md`; PREREG
`results/calibration/PREREG-nyiso198-duct-peaking-row-scope-screen.md` (+ Addendum A), both pushed
before the work they govern.

**Phase 0 closed the queue item.** Cricket Valley 57185's part-load bucket (b−), 906.1 GWh in 2024,
resolves against the LP's own bounds with no solve: CAP_SCOPE **0**, FLOOR **≤ 6.6 GWh** (the
bridge's own committed D-4 row — 29 binding hours), CAP_OUTAGE 100.5, **MERIT 805.6 (88.9 %)**,
with the LP dispatching 444.7 MW of a 451.9 MW mean in-the-money capacity. So the brief's
availability and min-load limbs are dead and it is an **offer-position** object — 56.6 % of the
deficit is envelope headroom sitting in the duct/peak band.

**The object is the band's MEMBERSHIP, not its price.** `peak` 2.25 = `phys_peak` 2.25 (markup 0,
untouchable under rule 1). `cc_duct_peaking_pct` sets the share as the whole plant's
nameplate-minus-net-summer gap whenever any row is flagged `Duct Burners = Y` — but EIA-860 reports
that attribute only on CA/CS rows and reads **`X` on every one of the 1,213 CT rows in the operable
population (`CT ∧ Y` = 0 of 1,213)**, so the CT rows' ambient derate is booked as duct capability.
Cricket Valley: 203.7 of 296.4 MW (**69 %**) on X rows → 245.64 MW of 1,086.9 at 15.78 MMBtu/MWh
against a $35.50 mean LMP. Fleet-wide **726.5 MW, 68 % of NYISO's CC peak band**. `assembly.py`
already names the conflation; its remedy is `cc_duct_peaking_cap_pct`, a **chosen** 8.0 for PJM and
`None` elsewhere. The arm (`cc_duct_peaking_row_scoped`, default off, **zero DOF**) chooses nothing.

**The pre-solve F-gates STOPPED first, and the failure was the PREREG's census.** The mover
classifier ignored `peak_cap = grid_cap × pct_peak / (100 − pct_mr)` and misfiled four CHP plants.
Addendum A replaced F-1/F-2 with a **strictly harder forward prediction** — Set B (the
`chp_layup` / `chp_duty_curve` / `reserve_duty` cohorts, 14 plants) unchanged exactly, Set A scaling
by `peak_off × pct_row / pct_cur` — which the rebuild satisfies with **residual 0.000 MW at all 31
plants**. One identity exception reported at full magnitude: Riverbay 52168 loses 1.2122 MW
(0.011 % of the CC fleet) to the builder's small-band filter.

**Screen (2024, named by footprint before the solve and re-derived on the corrected MW before it):
S-3 PASS, C8/D-4 PASS, S-4 STOP.** Cricket Valley **3,706.1 → 4,081.5 GWh** (+375.4 against a
622.1 bound, **70 % of the plant's gap to its 4,240.9 meter closed**); fleet CC +1,238.1 (bound
3,047.0); prices **−4.2 %** (same-weights C3a-2024 indicator +4.7 % → +0.3 %). And
**C1-2024 `CC_REGULAR` +3.01 → +4.13 TWh, +2.5 → +3.4 pp, PASS → FAIL**, because the cheaper CC
stack takes **0.71 TWh from `ST_GAS`** and 0.06 from `CT_PEAKER` — both already *under*. Span not
spent.

**The reading is rule 14 `[R-ACCURATE]`'s own:** the mis-classified band was the only thing holding
the CC stack back and was silently compensating for a different error. **The next lever is the
`CC_REGULAR` vs `ST_GAS` / `CT_PEAKER` merit order**, not the duct band. Two measurements for the
standing owner-ruled duct-tranche lever, from committed artifacts: on this keeper the `CC_REGULAR`
peak band runs at **12.8 % CF** and carries **3.5 %** of class energy, and 69 % of it is not duct
capability — so raising its offer moves little energy and raises a mis-classified band.

**Matrix:** `cc_duct_peaking_row_scoped` base row + a cell in every shard (rule 26c); NYISO **O**
(filed to the owner court, so DO-NOT-REDO does not close it), the other five **U** with their own
zero-LP census named as the transfer question (rule 25). **nyiso-197 §8 item 4 DISCHARGED** — the
screen-gate probe now removes the payload's CHP add-back so both sides of a plant-grain comparison
are LP grid; it caught a fabricated −898 GWh fall at Linden on this session's first pass (truth
+351). `complete` remains withdrawn; no marker requested.

## 2026-09-06 — nyiso-198 (cont.): the span under the owner ruling reads NOT-YET (fails 3); recommendation DO NOT PROMOTE; keeper unchanged

**Owner ruling, in session, verbatim:** *"Is this a recommended keeper candidate? If so plz promote.
If structural integrity improves but gates regress that may still be a keeper.."* — recorded in the
PREREG's **Addendum B** and pushed at `a8f42835` **before the span solve**, together with the
G-DRIFT re-check on the rebased base (`821c11c5..1ce47fc0`, 42 commits, 3 on the solve path, all
INERT) and, in §B.2, the arm's most likely second failure **named in advance**.

**Run `2026-09-06-nyiso-198-duct-row`** (bundle `nyiso198_duct_rowscope`, `--year 2023 2024 2025` in
ONE invocation, rule 16; registered the same session, rule 15). Attestation computed and PASSING on
every check: G-CONTROL max |Δprice| disk-vs-git **0.0** all three years, G-DELTA **exactly the one
flag**, G-INPUTS the EIA-860 sheet pinned with `CT ∧ Y = 0 of 1,213` recomputed, G-DOF 13 /
`n_residual` 6 verbatim with **0 added**, G-ENGAGE the solved fleet carrying the predicted band.

**DETERMINATION: CALIBRATED (grade 7, fails 0) → NOT-YET (grade 5, FAILS 3).** C1 13/14 free 9/10,
**C1-2024 `CC_REGULAR` +3.01 → +4.13 TWh / +2.5 → +3.4 pp FAIL**; **C3a-2025 −6.9 % → −10.3 % FAIL**
— exactly the risk §B.2 named before the solve; **C3c FAIL** as collateral (the standing rule
reclassifies it only when it is the LONE failure; magnitude unchanged at 3 / 1 / 4 h vs 10 / 13 /
42). C2 / C3b / C4 / C6 / C8 PASS. Span, same signature every year: `CC_REGULAR` +1.147 / +1.121 /
+1.383 TWh, `ST_GAS` −0.918 / −0.706 / −0.801, `CT_PEAKER` −0.080 / −0.061 / −0.309, prices −3.10 /
−4.20 / −3.68 %.

**RECOMMENDATION: DO NOT PROMOTE.** The owner's formula is *"may still be a keeper"* — permissive,
not automatic. The structural half is not in doubt (zero DOF; the mechanism lands on the builder's
own predicted value at all 31 plants with residual 0.000 MW). But the determination does not
regress, it **collapses**: both load-bearing families the keeper held are lost. The precedents
differ in kind — nyiso-193 promoted a NOT-YET whose arm carried **zero `ScenarioConfig` deltas** and
fixed a keeper that could not be reproduced at all; nyiso-196 **improved** the determination. Rule
14 `[R-ACCURATE]` governs the disposition and **both** its clauses bind: the error is not buried
back in the inaccurate input (`cc_duct_peaking_row_scoped` stays in the codebase, default off,
measured, registered and documented) and the half-repair is not shipped either — the root cause it
exposed is unfixed. **Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`.** Matrix cell **R**
with the re-test condition stated: re-arm it **paired** with the merit-order repair, never alone.

**What is now known regardless of disposition.** The keeper's C1-2024 `CC_REGULAR` PASS stands on
**726.5 MW of mis-classified capacity** — the cell is an over-run currently held in band by a
construction defect, not by physics. The merit-order object is sized: `ST_GAS` −0.7 to −0.9 TWh plus
`CT_PEAKER` −0.06 to −0.31 TWh. And ~3–4 % of price level rides on this one mechanism, which is the
scale of the C3a budget in both directions (2024 +4.7 %, 2025 −6.9 %) — so C3a-2025's headroom is
not independent slack.

## 2026-09-06 — nyiso-199: the merit-order object is `CT_PEAKER`'s own band basis, and the pre-registered screen KILLED the arm on a bridge interaction, not on the pre-named price risk

**Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`.** Nothing registered, nothing promoted,
the 2023–2025 span **never spent**. Two solves, both one-year rule-29 screens, both deleted before
merge (29(c)). `complete` remains withdrawn; no marker requested; 2023–2025 only.

**Phase 0 (zero LP) split nyiso-198's handed-forward queue item in two.** Decomposed against the
LP's own bounds on the keeper's committed artifacts:

* **`ST_GAS` is CLOSED to this lane.** 73/88/84 % of its deficit is interior, but the gap lives
  **below $40/MWh** where no steam offer clears — the out-of-market-commitment signature the
  `scuc_load_pocket_commitment` cell (**G**) already owns, and nyiso-97 §5 forbids identifying the
  pocket requirement from the only instrument available (unit conduct). Stop proposing it as a
  merit lever.
* **`CT_PEAKER` is the live object and it is unambiguous: 100.0 % INTERIOR in all three years** —
  0.0 % at the availability envelope, 0.0 % at a floor, forced floor 0.000 TWh, D-2 0.0 %. Model at
  **2.04 / 2.03 / 7.03 %** of its OWN available capacity against a meter of **11.16 / 10.85 /
  14.29 %**.

**The object, localised.** `_NYISO_OFFER_CURVE`'s `CT_PEAKER` `econ` = 1.0 is a DE-LEAK placeholder
the config declares an **OPEN ROOT CAUSE** by name; `committed` = 1.35 is "the start hurdle …
~$25/MWh fixed commitment margin" charged on a keeper that **already runs
`tranche_startup_amortization`** ($20/MW NREL SR-5500-55433 ÷ the measured P0 run length, same
tranche) — a rule 19 `[R-ONE-MECH]` double count live today. Both carry NYISO's own registered
measured counterpart, unused: **0.843 / 0.661 / 0.658** (n = 70).

**Owner ruling 2026-09-06** (PREREG Addendum A, pushed before the field existed): arm both bands,
screen 2023 + 2025. New field **`nyiso_ct_peaker_bands_measured`** (gated, default off,
NYISO-scoped, `_CACHE_KEY_OPTIONAL_FIELDS` + pinned default + base matrix row + a cell in all six
shards, all in the same commit). Zero literals, zero free parameters, no DOF entry.

**F-gates all PASS on the built field:** 101/103/103 rows move, every one `CT_PEAKER`
econ+committed, ZERO elsewhere; `pmax`/`availability` max‖Δ‖ exactly 0.0; the delta is a
**fuel-invariant −$17.41 committed / −$13.68 econ, identical to the cent** across three years whose
CT offers differ by $22–30/MWh; `peak` Δ 0.00.

**SCREEN A (2023, footprint year) CLEARS all four gates**: `CT_PEAKER` 0.421 → 1.418 TWh
(C1 −1.69 → −0.70, **59 % of the gap closed**), `ST_GAS` +1.81 → +1.18, `CC_REGULAR` +0.83 → +0.56,
`CC_CHP` +0.95 → +0.86 — **every moved class toward its actual**; gas family −0.023 TWh;
C3a **+4.6 % → +2.9 %** PASS; C3b 0.119 unchanged; no C1 flip; no new D-4 row.

**SCREEN B (2025, exposed year) STOPS — and not on the pre-named risk.** C3a **−6.9 % → −9.1 %,
degraded but still PASS** (0.9 pp of margin inside ±10 %); `CT_PEAKER` 1.356 → 2.672 against a
2.851 actual, **93.7 % of the gap closed**. **C8/D-4 stops it**: two plants the keeper never floors
enter the `nyiso_gas_commitment_bridge × CC_REGULAR` binding set — **7314 (0.0669 TWh over 3,210
binding hours, measured median 0.0 MW, 76.2 % of those hours at zero)** and 50978 (352 h, 0.0 MW,
69.9 %). Floors binding where the meter says the units are offline is what rule 17
`[R-FLOOR-WINDOW]` calls a bug by definition. **Mechanism, and it is not the band:** cheaper CT
displaces `CC_REGULAR` in the **P0** pass, so a plant with no prior committed run shows a short P0
run that `nyiso_gas_bridge_min_run` extends to the class min-run and floors — a **P0-pattern
dependence in the bridge**; the arm changes no floor and touches no bridge parameter.

**RECOMMENDATION: DO NOT PROMOTE** on this evidence. The structural half is strong and undisputed;
the pre-named price risk was screened and survived; but a protective-tier gate fires on a fabricated
commitment, which is not a residual regression. **Matrix cell → R** with the re-test condition
stated: re-arm **only paired** with a bridge repair. **New top of queue:**
`nyiso_gas_bridge_min_run`'s P0-pattern dependence — condition eligibility on the unit's own
measured conduct in the window (the D-4 statistic the diagnostic already computes), then screen the
three-way pairing with `cc_duct_peaking_row_scoped` (also **R**, also awaiting a merit partner, and
pushing the opposite way) on 2023 + 2025 with the gates already written.

Records: `docs/FINDING-nyiso199-ct-peaker-band-basis-2026-09-06.md` (§1–§8),
`results/calibration/PREREG-nyiso199-ct-peaker-measured-bands-screen.md` (+ Addendum A),
`_nyiso199_{meritorder,zone_offer_census,ct_band_basis}_phase0.json`,
`_nyiso199_screen_gates_{2023,2025}.json`, `scripts/probes/nyiso199_*.py`.

## nyiso-200 — 2026-09-06 — the bridge's P0-pattern dependence: commitment-real run screen built (zero DOF), the nyiso-199 stop re-attributed to a one-year scorer artifact, both screens STOPPED at their own gates on 2023, keeper UNCHANGED

**Keeper: `2026-09-06-nyiso-196-extract-basis` — UNCHANGED.** Two one-year rule-29 screens, both
deleted before merge (29(c)); no span spent; nothing registered or promoted.

**Phase 0 (zero LP).** The nyiso-199 §8.3 C8/D-4 STOP fired on two plants (7314, 50978) the span
scorer SKIPS by construction: both are `ct_only` CEMS reporters in the complete 2023/2024
vintages, un-flagged only by the preliminary 2025 vintage (the nyiso-145 §3 artifact); the
nyiso-150 union guard restores the flag over the scored span, and a ONE-YEAR screen bundle's span
was {2025} alone. 2 of 2 of that screen's failures are on restored plants; 0 survive. **Scorer-only
repair landed:** `legitimacy_diagnostics.ct_only_guard_years` unions over the ISO's training span
whatever the bundle's years (protective direction only; keeper byte-identical; test added). The
object is nonetheless real: every bridge leg anchors on a P0 pattern a base-cost LP manufactures.

**The repair — `nyiso_gas_bridge_startup_aware`** (gated, default off, registered in every sibling
registry and on the `gas_commitment_bridge` base row): the shared detector's G-61 path (b)
commitment-real run screen, wired for NYISO for the first time — a P0 run anchors any leg only when
its P0 margin per MW repays the unit's own published startup cost ($50 CC / $35 ST, the bridge's
own constant). Zero free parameters. The measured-conduct gate the nyiso-199 handoff named is
refused on rule 13 (an in-solve hourly meter pin with no forward analogue) and by nyiso-144's own
7314 ruling. Detector gains an optional census out-param; the wiring logs runs dropped per leg.

**Screen A1-2023 (repair alone): STOP on C8/D-4 count.** Census 1,173 / 1,576 CC and 351 / 422
steam runs dropped; bridge forced **1.0034 → 0.3439 TWh**; zero C1 flips (`CC_REGULAR` +0.83 →
+0.37 TWh); C3a +4.6 → +5.7 % PASS; C3b unchanged. The one new D-4 row is Astoria 8906's
conviction migrating from the bridge (1,400 → 34 h) to the reliability floor beneath (4,140 →
5,400 h, median 81 → 0 MW); the plant's total forcing FELL 0.2501 → 0.2282 TWh. A1-2025 not spent.

**Screen A3-2023 (three-way: + `nyiso_ct_peaker_bands_measured` + `cc_duct_peaking_row_scoped`):
STOP on the named-plant gate, with every companion gate clear.** `ST_GAS` +1.81 → **+0.46 TWh**,
`CT_PEAKER` −1.69 → **−0.99**, `CC_REGULAR` +0.83 → +1.43 (PASS), C3a **+4.6 → +0.9 %**, C3b
unchanged, zero flips, **no new D-4 row at the span guard**; bridge floors at 7314 542 h / 10 GWh
and 50978 153 h / 5 GWh remain, all on runs that repaid their start — the gate demanded zero.
A3-2025 (the exposed year) not spent; the pairing's 2025 price exposure is UNMEASURED.

**Handed forward:** re-screen A3 on 2025 under corrected gates (forced energy per dark-meter plant
like-for-like, not a row count; named-plant STOP on dropped-run anchors, not on any floor); the
reliability floor's own membership question at Astoria 8906 (the floor under the floor, rule 19);
the run screen alone as a keeper-change candidate. Records:
`docs/FINDING-nyiso200-bridge-run-screen-2026-09-06.md`,
`results/calibration/PREREG-nyiso200-bridge-run-screen.md` (+ Addendum A),
`_nyiso200_bridge_phase0.json`, `_nyiso200_screen_gates_{a1,a3}_2023.json`,
`scripts/probes/nyiso200_*.py`.

## nyiso-201 — the corrected gates CLEAR, the pairing STOPS on 2025's price, and the NYC persistent-base membership question is answered NEGATIVE (2026-09-06)

**Keeper UNCHANGED: `2026-09-06-nyiso-196-extract-basis`. Nothing registered, nothing promoted,
no span spent.** ONE LP (a one-year rule-29 screen, deleted before merge, 29(c)).

**The two gate constructions nyiso-200 §7 handed forward were both mis-built, and correcting them
was worth doing — both CLEAR.** (a) The C8/D-4 companion is now forced energy at **dark-meter**
plants over every mechanism, not a D-4 failure-row COUNT (a count rises whenever the higher of two
composed floors is removed at a plant the lower one also floors). It reads **0.0010 → 0.0000 TWh**:
the arm *removes* the keeper's only dark conviction (Roseton 8006) and the screen's failure list is
empty. The new function reproduces nyiso-200 §5.1's published 2023 number (0.2515 TWh) exactly,
which is the check that it is that section's construction. (b) The named-plant gate is now "a floor
**anchored on a DROPPED run**, or a new D-4 conviction", never "zero floor": 7314 carries 803
unit-hours / 16.14 GWh and 50978 231 / 9.09, every one on a **kept** run (per-plant census 120 of
333 and 47 of 86 kept), and neither draws a conviction. **Under (a) as corrected, nyiso-200's A1
stop is retired** — A1-2023's own reading (8906 total forcing 0.2501 → 0.2282 TWh, a FALL) passes.

**The arm dies anyway, on the risk this lane named in writing before the solve.** **C3a-2025:
−6.9 % → −11.7 %**, outside ±10 % (mean 61.84 → 58.69 vs actual 66.43; system mean 58.86 → 55.72).
The two price-lowering fields dominate the run screen's price-raising one. S-1 (`CT_PEAKER`
+0.858 TWh inside its 2.1417 bound), S-2, C3b and G-ENGAGE all pass; the run screen is live and
large in 2025 too (951/1,528 CC, 355/455 steam runs dropped; bridge volume 0.5701 → 0.1540 TWh).
**2023's structural story does not reproduce on 2025**: only `CT_PEAKER` moves toward its actual;
`ST_GAS` moves 1.56 TWh further below an already −4.1 TWh actual. Reported, not gated — 2025 SKIPS
every C1 cell **and** C2 gas on the preliminary EIA-923 vintage, declared in the PREREG §0.5 before
the solve so the gates' teeth were known ex ante.

**Not promoted, and for a stronger reason than nyiso-200's:** C3a is load-bearing and unledgerable
(the C3c standing rule needs a LONE C3c; the v3.0 guard refuses `model-class` on C1/C2/C3a/C3b), so
a span carrying it reads **NOT-YET** and promoting would **decertify NYISO**. The owner's formula
admits gates regressing; it does not reach a decertification.

**Second object, zero LP — the NYC persistent-base limb's first-ever membership review** (the log's
own open item: *"the NYC persistent-base limb has never had a membership review"*). **Astoria 8906
answers NEGATIVE from source data.** On nyiso-140's criterion (median gross load 0.000 in **18 of
18** (year, 4-hour block) cells) 8906 is **0 of 18** — the maximum distance from qualifying, pooled
median **166 MW**, online **66.7 %**, in the same bucket as Ravenswood and Northport; the nearest
non-qualifier is 50978 at 16/18. Widening the test to admit it would dissolve the lay-up/cycler
distinction and reach the whole 0/18 bucket, and naming it would be the per-plant list rules 1/14
and the nyiso-144 7314 ruling forbid. **The real object is the limb's BASIS, not its membership:**
NYC `ST_GAS` `tmax` −50 °C (all 8,760 h), `floor_pct` 0.175, `pro_rata`, `exclude_plant_codes`
**empty** — and across all 46 NYISO limbs the exclusion channel carries exactly one entry
(Long_Island excludes 2517), so the keeper's armed `reliability_floor_plant_exclusions` arms
**nothing on NYC**. Its basis is a fleet-aggregate when-available cool-day CF p25 applied per unit
to a fleet spanning 0.667–0.956 online — nyiso-140's Long_Island diagnosis, never run for NYC. At
8906 in 2025 the composition runs the *opposite* way to 2023: total forcing **RISES** 0.2725 →
0.3061 TWh (reliability row 3,512 → 4,834 h) while the bridge row goes to zero, and the D-4 rider
convicts in neither case (median 80.976 MW) — so the 2023 conviction was a year-specific tip, not a
standing property.

**Handed forward:** the three-way pairing is REFUTED — both pre-registered screen years (2023
nyiso-200, 2025 nyiso-201) are spent, do not re-screen it; **`nyiso_gas_bridge_startup_aware` ALONE
is the live candidate and its 2025 screen has still never been spent** (it is the only one of the
three that *raises* price); and the NYC persistent-base **basis** review is the source-data object.

**Rules:** 29 (phase 0 → F-gates → ONE named screen year → span only if clear; bundle deleted
before merge, 29(c)); 29(b) G-DRIFT empirical at HEAD — the committed keeper-sha rebuild record
reproduces 0 of 42 differing leaves, no control solve; 1 (no gate read the target residual, in
either direction); 13 (the refused measured-conduct eligibility gate was not built); 21 **G-DOF
+0**; 22 (2023–2025 only, no marker requested, `complete` stays withdrawn); 26 (three NYISO shard
cells re-stamped this session: `gas_commitment_bridge`, `nyiso_ct_peaker_bands_measured`,
`cc_duct_peaking_row_scoped`); 15 (zero registrations because zero span runs — by design). The one
code change is diagnostics-only (a per-unit/per-plant run census; the floor arithmetic never reads
it, guarded byte-identical). Records:
`docs/FINDING-nyiso201-threeway-2025-screen-2026-09-06.md`,
`results/calibration/PREREG-nyiso201-threeway-2025-screen.md` (+ Addendum A),
`_nyiso201_screen_gates_a3_2025.json`, `scripts/probes/nyiso201_screen_gates.py`.

## nyiso-202 — 2026-09-06

**KEEPER PROMOTED: `2026-09-06-nyiso-196-extract-basis` → `2026-09-06-nyiso-202-startup-aware`.**
The one live candidate nyiso-201 handed forward — `nyiso_gas_bridge_startup_aware` **alone**, whose
2025 screen had never been spent — cleared **every** pre-registered gate and the span it earned was
registered and promoted. **Two LPs:** one rule-29 screen on 2025 (deleted before merge, 29(c)) and
one span `--year 2023 2024 2025` in ONE invocation and ONE bundle.

**The screen (2025), all gates CLEAR.** S-1 was the only gate re-pointed, and it is a narrowing:
nyiso-201's *"`CT_PEAKER` rises inside the CT band's newly-in-the-money bound"* has no subject in an
arm that does not arm the CT band, so S-1 became this arm's own arithmetic — nyiso-200's A1 form,
*"the bridge's D-2 volume must NOT RISE, fall inside the keeper's own 0.5701 TWh"* — and read
**0.5701 → 0.1434 TWh**. Gate (a) dark-meter forcing 0.0010 → 0.0010 (Δ 0.0000); gate (b) 7314
977 unit-h / 19.617 GWh with **134 of 347** runs kept and 50978 228 unit-h / 9.011 GWh with **40 of
66** kept, so no floor anchors on a dropped run and neither draws a D-4 conviction; S-3 confinement
clean (no non-gas non-import class moves > 0.005 TWh); C3a **−6.9 → −6.3 %** and C3b 0.154 both
PASS → PASS; G-ENGAGE 939/1,554 CC, 95/164 state, 386/508 steam runs dropped. Gate (a) and (b) are
nyiso-201's corrected constructions reused **byte-identically**, and this session changed **no
solve-path code at all**.

**The span: DETERMINATION CALIBRATED, grade 7 of 8, fails 0, C3c the lone ledgered caveat —
IDENTICAL to the superseded keeper's headline with ZERO criterion flips in either direction.** The
promotion therefore rests entirely on the structural half, which is measured and large:
**dark-meter forced energy 0.5963 → 0.2336 TWh** across the span (2023 0.2515 → 0.2296; 2024 0.3438
→ **0.0030**, eliminating Astoria 8906's 0.3436 TWh conviction; 2025 0.0010 unchanged); **C8 forced
share down on every class-year** (`CC_REGULAR` 2.8/0.8/1.2 → 1.1/0.3/0.4 %, `ST_GAS` 16.6/22.4/18.2
→ 15.5/19.9/17.2 %); C1 `CC_REGULAR` toward its actual in both scored years (+0.83 → +0.37, +3.01 →
+2.39 TWh). G-DELTA computed = exactly the one field (both refuted partners recorded FALSE), G-DOF
+0, control = the keeper's committed bundle (form 4; G-DRIFT **empirical** — the committed
`_nyiso198_rebuild_checks_2024.json` regenerates byte-identically, 0 of 42 differing leaves — so no
control solve was spent).

**Regressions at full magnitude, none a flip, all inside band:** `CC_CHP` is the away class and was
**named in the PREREG before the span was solved** (+0.95 → +1.18, +2.31 → +2.65 TWh; share +1.9 →
+2.1 pp vs ±3); `ST_CHP` +0.17 → +0.21, +0.21 → +0.29; `ST_GAS` 2023 +1.81 → +1.92 (2024 improves);
C3a 2023 +4.6 → +5.7 %, 2024 +4.7 → +6.5 % vs ±10 %; **C3b-2024 0.175 → 0.185 vs ≤0.20 is the
tightest remaining margin in the model** (0.015 of room, was 0.025) and is the successor's first
watch item.

**Reported and not hidden:** the D-4 failure-ROW count rises 5 → 6 while the forcing it purports to
measure falls 61 % — the attribution artifact nyiso-201 §7(4) established. At 8906 in 2023 the
bridge row shrinks 0.0463 → 0.0011 TWh and the `reliability_floor` row beneath it now convicts at
0.2271, total 0.2501 → 0.2282, a **fall**; D-2 adds no failure and C8 PASSES. **That new row is the
handed-forward object:** with the bridge floor gone at 8906 the NYC persistent-base limb is its sole
remaining forcer, and nyiso-201 §5.3 already named that limb's **BASIS** — a fleet-aggregate
when-available cool-day CF p25 applied per unit across a fleet spanning 0.667–0.956 online — as the
open, source-data-only, zero-LP object (its membership question is closed negative; never type a
per-plant list).

`complete` is NOT re-declared — NYISO stays in `calibration-complete.json`'s `withdrawn` block, so
no D-5(b) re-key is owed and no holdout year was touched (2023–2025 only). Registered, status page
and matrix shard + §5.5 prose header re-stamped, `audit_keepers --iso NYISO` PASS, parity OK, the
superseded `nyiso-198` run pruned under keeper-only retention. Records:
`docs/FINDING-nyiso202-bridge-startup-aware-2026-09-06.md`,
`results/calibration/PREREG-nyiso202-bridge-startup-aware-2025-screen.md` (pushed with zero solves,
+ Addendum A), `_nyiso202_screen_gates_a1_2025.json`, `scripts/probes/nyiso202_screen_gates.py`,
`scripts/gen_nyiso202_attestation.py`.

## nyiso-203 — 2026-09-06

**NYC persistent-base limb basis review — CLEAN NEGATIVE: the basis is SOUND AS BUILT.
ZERO LP spent. Keeper UNCHANGED at `2026-09-06-nyiso-202-startup-aware`** (CALIBRATED,
grade 7/8, fails 0, C3c the lone ledgered caveat). No arm built, no `ScenarioConfig` field
added, no coefficient edited, no solve-affecting file touched, nothing registered (rule 15
registers runs; there is no run). 2023–2025 only; no held-out year touched (rule 22).

nyiso-202 §8 handed forward one object: repeat nyiso-140's Long_Island analysis for the NYC
`ST_GAS` persistent-base limb (`tmax` −50 °C so it binds all 8,760 h, `floor_pct` 0.175,
`pro_rata`, `exclude_plant_codes` EMPTY), which with the bridge floor gone at Astoria 8906 is
that plant's sole remaining forcer and draws the keeper's 2023 D-4 conviction at 0.2271 TWh.
Rule 29 phase 0 is entirely zero-LP and it returned a negative, so no arm reached a solve and
none was pre-registered. Step 0 reproduces the frozen coefficient (0.17485 vs 0.17500), so
every gap is a basis difference. **Three things could have been wrong and each is measurably
right.** WINDOW: all three plants positive in every cool-day hour block (Ravenswood 2500
0.283/0.287/0.288/0.290, Astoria 8906 0.323/0.326/0.326/0.325, Arthur Kill 2490
0.111/0.119/0.184/0.112 — minimum cell 0.111, against Port Jefferson's 18-of-18 exact zeros).
MEMBERSHIP: no laid-up member, confirming nyiso-201 §5 on an independent statistic; no
per-plant list typed. OPERATOR: in the fleet's lowest-quartile cool hours the gen/avail ratios
are 1.22 / 1.25 / 0.57 (robust 0.57–1.43 over {cool, all} × {q10, q25}), so all three share the
base — and the same numbers **refute** `cheapest_first`, which would put 100 % of the 616.8 MW
zonal target on Ravenswood alone at 0.358 of its own capacity (above its own measured p50
0.288) and zero the other two. The 586.1 MW fleet-p25 vs 347.1 MW sum-of-unit-p25 gap is
Jensen on a percentile, not a defect.

**ONE real gap, REPORTED AND NOT TAKEN:** the coefficient is a daily-mean statistic applied
hourly, 0.1750 → **0.1663** basis-matched (−5.0 %, −0.133 TWh of forced energy over three
years, 1.510 → 1.377). Refused on three independent grounds: rule 23 has **no source-data
trigger** (nyiso-140's did — the 6a8f285 guard fix); it would **move** the coefficient where
nyiso-140's did not (that correction was zero-DOF precisely because `floor_pct` was unchanged
at 0.262), so rule 21 admissibility is an **owner call**; and it **provably cannot reach the
object** — the measured band between the two coefficients covers **0.13 %** of 8906's hours
against its 5,400 binding hours. NYISO reads fails 0 and no residual was consulted (rule 1).

**Object handed forward, correctly re-specified:** 8906's D-4 conviction is a fact about
**which hours** an always-on floor selects, not about level, membership or operator. The rider
scores conduct *conditional on binding*: unconditionally 8906 is a cycler online 70 % of the
year with median CF 0.330, but over its 5,400 binding hours its median is **0.0 MW**
(zero-share 0.521) — because the floor binds where the LP puts it out of merit, and it is the
dearest of the three (HR 11.949). **The level is not the instrument.** Also corrected: the
NYISO matrix shard's stale *"the adopted D-4 per-unit rider is NOT yet implemented"* clause —
the rider has since landed (`legitimacy_diagnostics.py` `check="unit-conduct"`, scored over
each plant's own binding hours) and is the very check that convicts 8906. G-DRIFT
re-validated empirically: `_nyiso198_rebuild_checks_2024.json` regenerates byte-identically at
this HEAD. Records: `docs/FINDING-nyiso203-nyc-persistent-base-basis-2026-09-06.md`,
`results/calibration/_nyiso203_nyc_base_phase0.json`,
`scripts/probes/_nyiso203_nyc_persistent_base_basis.py`.

## nyiso-203b — 2026-09-06

**The TWO items standing before a `complete` / `frontier` re-declaration, MEASURED. Keeper
UNCHANGED at `2026-09-06-nyiso-202-startup-aware`** (CALIBRATED, grade 7/8, fails 0 — re-verified
this session from committed artifacts, no solve). **ONE LP: an identity-verified replay of the
keeper's own recipe** (`--replay-bundle`), run solely to recover the gitignored
`hourly/unit_hourly_<year>.parquet` + `floors/<year>_P1.npz` the committed bundle does not carry
— **0 of 157,680 zonal prices differ across 2023–2025 and class energy is identical to
0.000000 MWh over 14 classes**, so the numbers are the keeper's. No arm, no `ScenarioConfig`
change, no scorer edit, nothing registered; **the replay bundle is DELETED BEFORE MERGE** (the
parity sweep treats an unregistered bundle dir as a gate RED). 2023–2025 only.

**(1) D-2 UNIT-GRAIN C8 — the UNRULED nyiso-193 card's option (C) NYISO row, re-taken on the live
keeper.** `ST_GAS` **0.351 / 0.343 / 0.268** against the 0.30 cap, versus the committed
plant-grain **0.155 / 0.199 / 0.172** (PASS). The defect is unchanged in kind and **reduced in
extent — 2 of 3 years breach, against 3 of 3** on the `nyiso-189` keeper the card measured
(0.393 / 0.414 / 0.305). No other class breaches (`CC_REGULAR` 0.097–0.099, `CT_PEAKER` 0.000,
`CC_CHP` 0.207–0.273 and exempt). Rule 20's escalation is **confirmed on the committed
diagnostics**: leg (b) shape `D1.passed=True`, leg (a) provenance `D4.passed=False`, so a
unit-grain re-base fails NYISO `ST_GAS` in 2023/2024 exactly as §2 of the card predicted.
**NEW, and it narrows the ruling's cost:** 5 of the 6 D-4 FAIL rows carry ≤0.0028 TWh, and **in
2024 the ONLY `ST_GAS` failure is Danskammer 2480 at 0.0002 TWh — 0.007 % of that class-year's
3.0294 TWh of unit-grain forced energy.** A CAMPD census against nyiso-140's criterion finds
**2480 (12/12 zero cells, 2.9 % online)** and **Roseton 8006 (12/12, 14.6 % online)** qualify
**a fortiori** against the already-excluded Port Jefferson 2517 (38.6 % online), while Astoria
8906 (0/12, 166 MW median, 70.4 % online) and Saranac 54574 (9/12) do **not** — confirming
nyiso-201 §5 a third time. Excluding 2480 + 8006 would leave **zero `ST_GAS` D-4 failures in 2024
and 2025**, with only 2023's 8906 row (0.2271 TWh) left — whose limb basis this session measured
**sound as built**, so it is not reachable by a basis change. **NOT ARMED:** that entry is a new
arm owing its own PREREG, rule-29 screen and span, and the D-4 gate is per bundle so the leg-(a)
consequence must be measured, not read off the row list. The card stays **UNRULED**; the other
five ISOs stay unmeasured (rule 25).

**(2) THE OWNER-RULED DUCT-TRANCHE LEVER** — the `withdrawn.NYISO.reentry` clause's named route
back to `complete` — **is measured and does not reach its target.** The premise is **RIGHT at
plant grain**: `CC_REGULAR` runs hot (model CF >0.80 at 3/2/1 plants vs actual 0/1/0; Astoria
Energy 55375 0.851/0.845 vs 0.764/0.777; Zeltmann 56196 0.827/0.825 vs 0.694/0.750; Bethlehem
2539 +0.294/+0.291). But the named tranche is the wrong one: the peak (duct) band is **1,158 MW
at CF 0.041 / 0.052 / 0.112 carrying 1.23 / 1.44 / 3.19 % of class energy**, while the over-run
lives in `committed` (3,214–3,219 MW, CF 0.656–0.695) and the six ~507 MW `econ` tranches
(CF 0.53–0.62). **THE BOUND: C1-2024 `CC_REGULAR` over-runs by +2.39 TWh and the entire peak band
dispatches 0.529 TWh, so displacing every MWh of it closes at most 22 %** (14 % at the
withdrawal, when the over-run was +3.68 TWh). Second reason: **80.7 % of the band (934.53 of
1,158.46 MW, row-scope coverage 100 %) is not duct capability** — CT rows EIA-860 flags `X` — so
raising it mostly raises the offer on ambient-derated capacity, the misclassification
`cc_duct_peaking_row_scoped` was **rejected** for trying to repair. Its target is also already met
by other means (C1-2024 `CC_REGULAR` +3.68 TWh / +3.0 pp at the withdrawal → +2.39 / +2.1 pp now).
**Stated for the owner court, not decided:** the successor inside the SAME authorized channel is
the `offer_curve_by_group` multiplier on `committed` / `econ_low` / `econ_high`, which rule 1's
carve-out condition (c) requires be declared ex ante in a PREREG and never swept — an owner act.

**MARKERS: neither item blocks either on the merits.** The keeper reads CALIBRATED and the
`reentry` clause asks only for a new explicit owner declaration; the forecast board's gate (a)
already reads *"an OWNER ACT, not a calibration task"*; the `frontier` mechanism-set limb was
never retracted. Card **C-19 / Q51** is PARKED at owner direction (capx refresh #46) with its
re-serve condition (*"nyiso-197 lands AND the keeper is CALIBRATED"*) **met**. No marker was
edited by this lane. Records:
`docs/FINDING-nyiso203b-unit-grain-and-duct-lever-2026-09-06.md`,
`docs/DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` §5 addendum,
`results/calibration/_nyiso203_c8_unit_grain.json`,
`_nyiso203_duct_lever_disposition.json`, `_nyiso203_d4_layup_census.json`,
`scripts/probes/_nyiso203_duct_lever_disposition.py`, `_nyiso203_d4_layup_census.py`.

---

## nyiso-209 — 2026-09-06

**Two halves, one session. Keeper `2026-09-06-nyiso-202-startup-aware` UNCHANGED throughout.**

**Half 1 (zero LP, clean negative).** Reproduce-from-source test of the gas-commitment-bridge
parameter artifact `campd_gas_commitment_params_NYISO.csv` (four keeper-live values: CC 0.523 /
ST_GAS 0.239 min-load fractions, 21 h / 13 h capacity-weighted p50 min-run). The shipped
`derive_campd_gas_commitment_params.py`, run with its own defaults against the committed CAMPD
NY+NJ 2023–2025 extracts, regenerates the class summary, the 78-row per-unit table AND the CT
sibling artifact **byte-identically** at HEAD. Pre-registered **VERDICT R — REPRODUCES**; the
session's own counter-prediction (CC-side roster drift from the nyiso-187/188/189/192/196 fleet
repairs) REFUTED — the HEAD roster carries three CC codes with no CEMS hours under their own id
(7784, 54808, 57664) and drops Ravenswood 2500 as mixed-class exactly as the 2026-07-27 derivation
did. Reported, not acted on: (O1) no DOF-ledger entry for this artifact while
`campd_ct_run_lengths_NYISO.csv` is ledgered; (O2) Ravenswood, the largest ST_GAS plant, is
excluded from the ST_GAS statistic by the script's declared ambiguity rule (bears on pending rulings
(i)/(ii); not ruled). Records: `docs/FINDING-nyiso209-gas-bridge-params-reproduce-2026-09-06.md`,
`results/calibration/PREREG-nyiso209-gas-bridge-params-reproduce.md`,
`_nyiso209_gas_bridge_params_reproduce.json`, `scripts/probes/_nyiso209_gas_bridge_params_reproduce.py`;
NYISO matrix shard `gas_commitment_bridge` cell evidence appended (K unchanged).

**Half 2 (owner ruling, one LP).** The owner asked whether NYISO was at `complete` / `frontier` and
whether 2022 could run; the lane answered "not yet on the record, yes on the merits, one owner
declaration away". **OWNER RULING, verbatim: "Ok declare it and run 22."** Executed in one records
commit: `complete.NYISO` RE-DECLARED (FOURTH grant) on nyiso-202 per the withdrawn block's own
`reentry` clause, determination re-verified artifact-only at `2a243bf9` (CALIBRATED, grade 7 of 8,
fails 0, C3c the lone ledgered caveat — not worse, D-5(b) stop did not fire); the 2026-09-05
withdrawal nested WHOLE as `prior_withdrawal_2026_09_05`, `withdrawn` = CAISO alone; `frontier`
re-declared with it (both instruments, Q39 precedent; `keepers/NYISO.json` `frontier`, the
2026-09-05 withdrawn block retained with a `superseded` field); forecast gate (a) fail → pass in
the same commit (rule R-T); `test_ff_readiness_battery` marker pin moved with the marker; NYISO
shard `gates` stamp (rule 28(d)). Card C-19 / Q51 DISCHARGED by the ruling. `audit_keepers --iso
NYISO` PASS 0/0; D-9 / D-6 quarantine PASS over every registered bundle. **Validation tier
re-authorized; the 2022 touchpoint SPENT on the frozen keeper recipe** (`--replay-bundle`,
`--holdout-authorized`; recipe identity computed PASS, +0/−0 solve-surface drift), registered as
`2026-09-06-nyiso-209-2022-touchpoint` and STAMPED to the keeper (rule 30 fold). **2022 reads
NOT-YET**: C1 CC_REGULAR +4.35 TWh / +3.3 pp, C3a −11.2 %, C3b NRMSE 0.227; C3c 15 vs 101 h
(caveat, rubric v3.6); C2 / C4 / C6 / C8 PASS — **every degraded number smaller than the
un-registered nyiso-189 diagnostic** (+5.19 / +3.9 pp, −12.2 %, 0.240, 17 h). Under rule 30(c)
**NYISO stays CALIBRATED**; the rung is reported on the keeper's card and the status ladder.
Reading (loop step 2): a gas-year level miss — CC_REGULAR over-dispatched while the system price
sits 11 % low in a $6.45 HH year — the same cell-G CC_REGULAR sign the keeper carries in-sample,
scaled by the 2022 fuel regime; the named objects are nyiso-201 §5.3 / `DECISION-CARD-nyiso193`
§5/§5.1 and `INTAKE-SPEC-nyiso156` Leg 2. 2020 / 2021 NOT spent; `final` untouched; freeze
untouched; nothing identified against 2022. Reported, not fixed: CAISO's gate-(a) stamp is stale
(cites `caiso-257` while the shard names `caiso-260`), another lane's. Record:
`docs/FINDING-nyiso209-redeclaration-and-2022-touchpoint-2026-09-06.md`.

## nyiso-210 — 2026-09-06

**Touchpoint loop step 2, completed: the 2022 CC_REGULAR over-run DECOMPOSED, and nyiso-209 §2.4's
reading REPLACED. ZERO LP. Keeper `2026-09-06-nyiso-202-startup-aware` UNCHANGED; no marker, gate,
parameter, offer curve, cell verdict or determination moved.**

Pre-registered at `f520bd1f` before the probe was written
(`results/calibration/PREREG-nyiso210-cc-regular-2022-overrun-attribution.md`), with one
construction addendum at `c30612c5` (`ADDENDUM-nyiso210-band-vocabulary-2026-09-06.md`: the
committed sidecar emits CC_REGULAR's economic region as six `econc*` tranches, not the registry's
`econ_low`/`econ_high` pair, so the partition was reassembled three-way — no threshold moved and no
verdict value had been read).

**The pre-registered verdict fired and this session reports its mechanism REFUTED on the same
artifacts.** P2 — declared as the prediction that would falsify the lane's preferred answer — fires:
the `committed` band is **+0.855 TWh** above its in-sample mean. But the bundles' own D-2 puts
CC_REGULAR forced energy at **0.0774 TWh in 2022, the LOWEST of the four years** (in-sample mean
0.1880), so `nyiso_gas_commitment_bridge` moved the *opposite* way and cannot carry it. The PREREG's
mapping of forcing onto the `committed` band was a construction error — `committed` is an **offer**
tranche — and `class_band_hourly` carries no measured side and no zone, so the band axis could not
have answered the question at any threshold. Stated at full strength rather than repaired.

**THE ANSWER IS ZONAL, AND IT IS AN IN-SAMPLE PROPERTY.** On a CAMPD-consistent basis the class gap
deteriorates **+2.136 TWh** from its in-sample mean to 2022: **Capital_Hudson +1.592 (74.5 %, a SIGN
FLIP from −1.104 to +0.488)** and **NYC +1.032 (48.3 %)**, Upstate_West −0.623, Long_Island +0.135
(sums exactly). NYC's gap is **positive in all four years and winter-loaded in all four**
(+1,062 / +795 / +294 / +479 GWh). **In-sample C1 PASSES BY CANCELLATION** — NYC +0.884 against
Capital_Hudson −1.104 nets to +0.223 TWh at class grain — **and both legs GROW across the training
window** (NYC +0.945 → +1.296; CH −0.641 → −1.564). **2022 creates no new error; it removes the
offset.** Same five plants every year — over: Bethlehem 2539, Zeltmann 56196, Astoria Energy 55375;
under: Cricket Valley 57185, CPV Valley 56940, the two newest H-class units — so **no new plant
object**, and a **merit-order inversion inside CC_REGULAR** that is worsening at Cricket Valley
(−0.441 → −0.608 → −1.010).

**Three mechanisms refuted, each independently.** Forcing (D-2, above). **Availability**: the
committed overlay's 2022 CC_REGULAR coverage is 654.2 GW-days against 698.3 / 645.0 / 721.0, and
Bethlehem (40.1 vs 21.1) and Zeltmann (52.1 vs 29.4) carry **nearly double** the in-sample derate in
2022 and over-run anyway — the neiso-85/86 thin-input hypothesis returns a clean negative. A
**fleet-wide fuel-level merit effect**: the economic share moves +1.05 pp against a declared 3.0 pp
bar. P4 does not fire and its falsifier fires twice — **disclosed as a defect in the pre-registered
statistic** (it ranked by |gap|, mixing over- and under-dispatch) and not repaired into a pass. P5
falsified and reported: the model burns 0.353 TWh of CC_REGULAR oil in 2022 and 0.673 in 2025, so
`dual_fuel_switching` needs no attention from this result.

**Basis stated:** C1 scores against the bench `classFull` series (+4.35 TWh) while this session
reads CAMPD consistently on both sides in all four years (+2.36 TWh); the `classFull`-minus-CAMPD
offset itself swings −2.0 / −0.4 / −2.4 / −0.3 TWh, reported and claimed as nothing.

**Rule 22:** 2022 was already spent by nyiso-209; only its committed sidecars and payload were read,
and **nothing is identified against 2022** — the object is present and repairable entirely within
2023–2025, which is what unblocks step 3. 2020 / 2021 not spent, `final` and the freeze untouched.
**Objects 1 and 2 of the charter are NOT reached** (both are `ST_GAS` mechanisms; CC_REGULAR's D-2
forcing is an order of magnitude too small to move a ~1 TWh zonal gap), so no DO-NOT-REDO cell was
re-tested and the five owner cards stay unruled. Reported, not fixed (rule 25): MISO's stale gate-(a)
stamp fails `test_gate_a_provenance::test_live_board_passes`, and the six charter files read 36
failed / 69 passed at HEAD. Record:
`docs/FINDING-nyiso210-cc-regular-2022-zonal-cancellation-2026-09-06.md`,
`results/calibration/_nyiso210_cc_overrun_attribution.json`,
`scripts/probes/nyiso210_cc_overrun_attribution.py`; NYISO matrix shard `gates` stamp (rule 28(d)),
no cell verdict letter moved, key set verified identical to `main` (306).

## nyiso-213 — 2026-09-07

**KEEPER PROMOTED: `2026-09-07-nyiso-213-summer-seam` (CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat), superseding `2026-09-06-nyiso-202-startup-aware`.** The arm is that keeper's
recipe plus ONE registered field, `cc_summer_derate_reconciled_basis` — a rule-19 `[R-ONE-MECH]`
construction repair of the seam between `cc_capacity_reconcile` (which removes MW a plant's fleet
rows over-state) and `cc_nameplate_summer_derate` (which then derates the REMAINING capacity by a
ratio referenced to the FULL nameplate). The two composed multiplicatively and removed the same MW
twice. **Zero free parameters, zero new DOF entries, `authorized_price_tuning` NONE.**

**The defect is physical and measured, not a residual:** at Cricket Valley 57185 the CAMPD meter
EXCEEDED the LP's own monthly summer ceiling in **7 of 36 scored months** — a model forbidding
generation the plant demonstrably produced. The arm takes that **7 → 1** (2023 `[7]`→`[]`, 2024
`[7,8,9]`→`[8]`, 2025 `[6,7,8]`→`[]`), max dispatch above ceiling 0.0000 MW.

**What this session actually did.** nyiso-212 built the mechanism, screened it on 2025, and **killed
its own arm** on the literal reading of two gates whose wording was its own — leaving the span
unspent. This session wrote those two gates correctly in a PREREG **pushed before any new number was
read** (S-1 excludes the two `--year` selection keys and classifies the armed flag as the live delta;
S-2(c) is written on the MEASURED ceiling direction over ALL 15 plants, **stricter in coverage** than
the 3-plant `mode`-label bar it replaces), re-screened, and **CLEARED all five gates**. The PREREG's
§0 discloses that this session had seen nyiso-212's numbers and states plainly that a re-screen with
them in hand is weaker evidence than a blind one.

**The PREREG's declared disjoint third outcome did not fire.** The re-solve ran on a solve-path tree
11 files (+1 docstring) removed from nyiso-212's and reproduced its numbers **6 of 6** to the declared
tolerances, so the G-DRIFT audit is an empirical result rather than a reading — corroborated by the
whole zero-LP phase-0 chain regenerating **byte-identically** at HEAD for all three years.

**Reported at full magnitude, and NOT the reason for the promotion (rule 1 `[R-STRUCT]`).** The arm
IMPROVES both load-bearing price criteria in 2023 (C3a +5.7→+4.3 %, C3b 0.124→0.122) and 2024
(+6.5→+5.3 %, 0.185→0.179) and DEGRADES both in 2025 (−6.3→−7.3 %, 0.152→0.160); all six still PASS.
**My PRED-B was wrong in sign for two of three years** — it generalised the single screen year — and
that is recorded as an error, not absorbed. C1 CC_REGULAR moves FURTHER ABOVE actual in 2023
(+0.37→+0.79 TWh) and 2024 (+2.39→+2.91) and stays PASS in every class.

**STATED AT THE GATE, NOT ABSORBED.** (i) Aug 2024 remains over-ceiling — **predicted** by the
committed phase-0 record before any PREREG existed. (ii) 55375 Astoria Energy's 2024 summer dispatch
falls **7.65 GWh more than its own ceiling tightening** (0.48 % of its keeper summer) while its
off-summer rises +37.61 GWh — seasonal merit re-allocation, reported as a real breach of the
confinement bound at one plant in one year. (iii) **THE 2022 VALIDATION TOUCHPOINT DEGRADES on all
three of its failing criteria** (C1 CC_REGULAR +4.35→+5.01 TWh, C3a −11.2→−12.5 %, C3b 0.227→0.229)
at an unchanged NOT-YET grade 4/8 — live selection evidence AGAINST the arm. Rule 30(c) forbids
letting a held-out year downgrade the ISO (NYISO stays CALIBRATED on the train tier) and rule 22
forbids re-tuning against a touchpoint year, so it is handed forward, not answered.

**THE HANDED-FORWARD OBJECT: CC_REGULAR AGGREGATE OVER-PRODUCTION** — the counterpart of the still-open
**object (B)**, in which 57185 under-runs its OWN meter by ~0.75 TWh in 2025 at corrected
availability while the class as a whole over-runs. The seam repair separated these two cleanly;
closing the aggregate half is the next lever, on the training tier.

**Records (all in one PR):** keeper shard + promotion prose (nyiso-202's audit-E11 declaration carried
forward; both `ccs_retrofit_*` fields are byte-identical between the two keepers and forecast-only);
`calibration-complete.NYISO` re-keyed under D-5(b) after an artifact-only re-verification that read
CALIBRATED (not worse ⇒ no stop, no escalation), `keeper_at_declaration` preserved, `final` untouched;
`status/NYISO.js` rebuilt with the 2022 rung in the per-year holdout ladder (rule 30(b)); the 2022
touchpoint `2026-09-07-nyiso-213-tp2022` registered and stamped to the keeper (rule 30(a)); forecast
gate (a) re-keyed in the SAME PR (rule R-T / Q34), **verdict unmoved** pass→pass, prior detail
preserved verbatim by sha; NYISO matrix shard cell `cc_summer_derate_reconciled_basis` **O → K** with
keeper + gates stamps and the §5.x prose header re-stamped (rule 28). Screen bundle deleted before
merge (rule 29(c)). The superseded 2022 touchpoint is NOT pruned — its id is cited in the preserved
nyiso-209 owner-declaration record, and pruning would dangle a citation inside an owner ruling.

**Re-measured, not repeated (rule 25):** `test_gate_a_provenance::test_live_board_passes`, which
nyiso-210 / -211 / -212 all recorded as FAILING on MISO's stale gate-(a) stamp, now **PASSES** —
`main` repaired it. 29 passed / 0 failed over that file, the mechanism's own guard and rule 30's
holdout-render guard.

**Markers:** `final` still ABSENT, the locked-test freeze untouched, 2019 and H1-2026 **not granted
and not spent**, 2020 and 2021 **unspent** (a separate owner spend). **The five pending owner rulings
are untouched and no new card is opened.**

Record: `docs/FINDING-nyiso213-summer-seam-rescreen-2026-09-07.md`,
`results/calibration/PREREG-nyiso213-summer-seam-rescreen.md`,
`results/calibration/_nyiso213_screen_gates_2025.json`,
`scripts/probes/nyiso213_screen_gates.py`.
## nyiso-214 — 2026-09-07

**ZERO LP. No solve, no bundle, no year spent. Keeper unchanged
(`2026-09-07-nyiso-213-summer-seam`, CALIBRATED, grade 7/8, fails 0, C3c the lone ledgered
caveat). There are NO in-sample rubric failures.** PREREG
(`results/calibration/PREREG-nyiso214-duct-gap-double-reading.md`) pushed before P1–P4 were read;
**all four fire**, including the limb declared to hurt and the reproduction bar that would have
voided the census.

**The nyiso-213 hand-forward object (B) is moved off a refuted hypothesis onto a measured one.**
The efficiency reading is **refuted at zero LP**: Cricket Valley 57185's model/CAMPD heat-rate
ratio is 1.023 / 1.031 / 1.043, inside the band every material CC occupies, so a per-plant
measured heat-rate repair is not this object's lever. Base heat rates span ±4 % across the eight
material `CC_REGULAR` plants while the **peak-band share spans 0.0 %–22.6 %** — the band, not the
heat rate, is the within-class merit allocator.

**The measured result: one EIA-860 quantity, two contradictory readings.** `cc_duct_peaking_pct`
assigns a peak band from the `nameplate − net_summer` gap gated on `Duct Burners == Y`, while
`cc_nameplate_summer_derate` (on nyiso-213's reconciled basis) reads the same gap at the same
plants as ambient derate — **11 plants / 819.462 MW of peak band carry both** (P1), and at 57185
the two are proved to read one pair to **0.0 pp** and **4 × 10⁻⁵** (P4). A rule 19 `[R-ONE-MECH]`
collision of the nyiso-212/213 family. **The flag does not track the physics** (P2, the
load-bearing prediction whose < 4.0 % limb would have refuted the framing): Athens 55405 carries a
**19.417 %** gap and receives **0.0 MW** of band — the second-largest gap of any material CC,
larger than five of the six flagged plants that do get one — and Zeltmann 56196 10.227 % / 0.0 MW,
against 57185's 22.583 % / 245.6 MW. P3 reproduction bar (> 50 % would have VOIDED): 92.7 of 296.4
MW (31.275 %) on `Y` rows, i.e. **203.7 MW on `X` rows — reproducing nyiso-198 exactly** at this
HEAD. And the allocator does not track the meter: over the five boundary-clean material plants,
band size vs the plants' own share of online hours **above** their published net-summer rating
reads **ρ = −0.10, no relationship** — 57185 has the largest band and the *smallest* reach
(7.56 % mean), 55405 has none and 13.23 %.

**Handed to the owner as a SIXTH decision card**, five membership forms sized over the 16
multi-tranche plants (A status quo 716.8 MW / B row-scoped 203.4 / C symmetric-none 0.0 / D
symmetric-all 1,065.8 / E demonstrated headroom 688.5). **Nothing built, armed, screened or
promoted**; no form recommended. Form E's within-class redistribution is **reported and explicitly
not a reason** (rule 1 — the only dispatch evidence that exists, nyiso-200's form-B screen, points
the other way), and **E′ (CAMPD demonstrated peak − net_summer) is refuted as constructed** on
plant-boundary contamination (694.0 MW at 55375, 1,669.5 at 2500). `cc_duct_peaking_row_scoped`'s
own `R` re-test condition was **not** re-opened.

**Named, not pursued:** seven small `CC_REGULAR` plants (441.7 MW) are represented by a **single
tranche labelled `_peak`**, so their whole capacity is offered at 2.25 × base HR all year, and two
of them carry no `Y` row at all — a different path from the duct mechanism. Six plants are
boundary-contaminated and excluded from every measured-side statistic.

**Rule 22:** training-tier only; no out-of-training year solved, scored or registered. `final` not
granted, locked test not spent, 2020/2021 unspent; no marker moved; the five pending owner rulings
untouched. **Re-measured, not inherited (rule 25):** the named test set
(`test_gate_a_provenance.py`, `test_cc_summer_derate_reconciled_basis.py`,
`test_holdout_render_parity.py`, `test_campd_bins.py`) reads **75 passed / 0 failed**, and
`ruff format --check .` / `ruff check` pass. Record:
`docs/FINDING-nyiso214-duct-gap-double-reading-2026-09-07.md`,
`results/calibration/_nyiso214_duct_gap_census.json`,
`scripts/probes/nyiso214_duct_gap_census.py`; NYISO matrix shard `gates` stamp plus the
`cc_duct_peaking` and `cc_nameplate_summer_derate` cells annotated (rule 28(b)), **no cell verdict
letter moved**.

## nyiso-215 — 2026-09-07

**ZERO LP. Keeper UNCHANGED (`2026-09-07-nyiso-213-summer-seam`, CALIBRATED, grade 7/8, fails 0,
C3c the lone ledgered caveat — re-verified this session at HEAD, artifact-only). Nothing
promoted, armed, screened or registered; no marker moved; 2020/2021 unspent.**

Took nyiso-214 §7's named-not-pursued object: the seven small `CC_REGULAR` plants (10621, 54034,
7784, 10620, 54592, 50744, 54593 — 441.7 MW) represented by a **single `_peak` tranche**, and
asked which binning path builds them, whether it is a small-band-filter artifact, and whether any
measured conduct justifies offering their base load at a scarcity multiplier.

**Answer: the path is `cc_reserve_duty_split` (nyiso-146), it is deliberate, its MEMBERSHIP
survives audit, and its LEVEL does not.**

* **P1 FIRES** — the seven are exactly the `reserve_duty = True` cohort; the keeper's own
  `fleet_only` rebuild reproduces nyiso-214's **441.700 MW** to 0.0 % and its 716.8 MW duct
  population to **0.039 MW**.
* **P2** — causation established beyond doubt (flag off ⇒ **7 of 7** regain 7–8 tranches, 0 remain
  single), so it is **not** a builder artifact. Its 400 MW magnitude limb missed by **2.252 MW**
  and **the gate was reported as written, not restated**; the pre-registered outcome partition was
  additionally not exhaustive, disclosed in the finding.
* **P3(a) FIRES / P3(b) HOLDS** — the cohort's one 0.10 threshold rides **two** statistics (CAMPD
  online share at 19 plants, EIA-923 pooled CF at 3), median ratio **0.473** all-plant / **0.418**
  boundary-clean, one-sided toward inclusion **empirically, not analytically** (19 of 20 < 1; the
  sole ratio > 1 is boundary-contaminated 2500 Ravenswood at CF 1.383). The one plant riding the
  fallback (7784 Allegany) qualifies on **every** reconciliation (0.037 / 0.041 / 0.059). A real
  construction defect, quantified, **non-load-bearing**. `derive_reserve_duty_cc.py` **audited,
  never re-derived** (rule 23).
* **P4 FIRES / P5 mean limb fires, exceedance limb misses** — the split routes the cohort to the
  **class** peak band `2.25 × base`, i.e. **duct-firing physics borrowed to express a duty role**
  (explicitly, to avoid a new scalar under rule 21). A multiplier fixed in heat-rate space is a
  fixed **cost** offer, so the protection **erodes as the price level rises**: implied economic
  on-share **0.042 → 0.167 → 0.521** (2023/24/25) against a measured 0.036 online / **0.00144 CF**
  (ratios 1.18 / 4.66 / 14.54) while Upstate_West mean LMP goes **$24.48 → $35.83 → $53.91** and
  the cohort's own `mc` rises only ~30 %. The keeper's **own committed** `class_band_hourly` puts a
  **strict lower bound of 4.778 GWh — 0.855× the cohort's entire 2023 measured annual energy —
  through in 38 hours**.
* **Reported at full magnitude, not averaged:** 54034 Rensselaer runs the mechanism the **opposite**
  way (implied 0.004–0.010 vs measured 0.064) in all three years — the level is *un*-levelled, not
  merely mis-levelled. C3a −7.3 % in 2025 means the erosion is **worse** against actual prices.
* **NEW OWNER CARD (the seventh pending, prejudging none — including nyiso-214 §6's membership
  card, which is a different mechanism at a disjoint cohort):** should a duty-role offer position
  be expressed in **cost** space or in **price-percentile** space? The band's price stays closed in
  both directions (nyiso-194 up, nyiso-195 down; `phys_peak == peak`), so a successor gives the
  cohort its own basis or routes it elsewhere. **Nothing built, armed, screened or sized.**
* **Found on the way, reported not repaired:** the keeper bundle's committed `metrics.json` reads
  `determination: NOT-YET` on a stale in-run *"no governance attestation in bundle"* reason while
  the scorer's `--run-id` path (the rule-22 D-5(b) route) returns **CALIBRATED**. Systemic across
  at least four ISOs (`neiso105`, `neiso99`, `nyiso202`, `nyiso213_tp2022`, `pjm169`,
  `pjm_debugb`); out of this lane to fix. Read the scorer, not the file.

Instrument validated: `nyiso196_rebuild_checks.py --year 2024` reproduces its committed record
**byte-identically**, `git status --porcelain -uno` empty. G-DRIFT `51f2fc2d → dcb609f4` audited
hunk-by-hunk in the PREREG before measurement: 10 INERT, 1 LIVE-but-out-of-scope
(`eia930/actuals.py` `_screen_fuel_spike_columns` — recorded for any lane that re-scores C1/C4).
Tests named rather than inherited: `test_gate_a_provenance`,
`test_cc_summer_derate_reconciled_basis`, `test_holdout_render_parity`, `test_campd_bins` —
**75 passed, 0 failed**; `ruff format --check .` 1,405 files formatted, `ruff check` passes.
Record: `docs/FINDING-nyiso215-reserve-duty-band-erodes-2026-09-07.md`,
`results/calibration/PREREG-nyiso215-reserve-duty-single-peak.md` (pushed before any number was
read), `results/calibration/_nyiso215_reserve_duty_census.json`,
`_nyiso215_band_energy_bound.json`, `scripts/probes/nyiso215_reserve_duty_census.py`,
`nyiso215_band_energy_bound.py`; NYISO matrix shard `offer_curve_by_group` cell annotated
(rule 28(b)), **no cell verdict letter moved**.

## nyiso-216 — 2026-09-07

**ZERO LP. Keeper unchanged (`2026-09-07-nyiso-213-summer-seam`, CALIBRATED, grade 7/8, fails 0,
C3c the lone ledgered caveat). Nothing built, armed, screened, sized, recommended or registered;
no marker moved; `final` never granted, locked test frozen, 2020/2021 unspent. The seven pending
owner rulings are untouched and none is prejudged — and NO eighth card is opened.**

**Finding:** `docs/FINDING-nyiso216-duty-role-protection-scales-with-zonal-gas-basis-2026-09-07.md`.
**PREREG:** `results/calibration/PREREG-nyiso216-rensselaer-counterexample.md`, pushed at
`1b3795e5` before any gated number was read. **Machine record:**
`results/calibration/_nyiso216_rensselaer_counterexample.json`. **Instrument:**
`scripts/probes/nyiso216_rensselaer_counterexample.py`.

**Object:** nyiso-215 §4's named-not-pursued intra-cohort counter-example — 54034 Rensselaer Cogen
runs `cc_reserve_duty_split` the *opposite* way to the cohort's other six in all three years
(implied economic on-share 0.0038 / 0.0064 / 0.0098 against a measured 0.0635). Is the sign flip a
**zone**, a **heat-rate**, or a **fleet-representation** effect, and does 54034 belong?

**Answer: a ZONE effect, through the zonal GAS BASIS rather than the zonal LMP — which was none of
the three as the question framed them.**

* **P2 fires, COST 3 of 3.** A 2×2 swap of {54034, the cap-weighted six} × {Capital_Hudson,
  Upstate_West} on the keeper's own committed P1 prices puts **99.7–103.2 %** of the gap on the
  cost leg, with the price leg **negative** every year. The LMP channel is excluded in the *strong*
  direction: `S(cohort, CH) > S(cohort, UW)` in every year, so Capital_Hudson is the **more**
  favourable zone and moving 54034 to Upstate_West would push it *further* out of merit.
* **P3's prediction FAILED and its declared "hurts" limb FIRED, at full strength.** Predicted
  HEAT-RATE; measured **FUEL 3 of 3** (shares 1.081 / 1.144 / 1.063), with the heat-rate term
  **negative** every year — 54034's base heat rate **8.8975** is **2.3 % below** the cap-weighted
  cohort's **9.1090**, i.e. mid-cohort physics. `F_A / F_B = 1.75 / 1.61 / 2.10`. **P3 additionally
  VOIDS on its own declared identity bar** (2025 residual **$0.0463** against a **$0.01** bar; 2023
  $0.0079 and 2024 $0.0017 close) and **the gate was not rewritten**. The residual is 0.09 % of Δ;
  its source was **not isolated and is not claimed**.
* **The object (D4, post-hoc).** 54034 is `gas_cc`, the same fuel type as all six, and its price is
  its **zone's**, not its own: every Capital_Hudson `gas_cc` unit pays ~**5.23 $/MMBtu** in 2025
  against ~**2.21** in Upstate_West — **2.37×**. 54034 is an ordinary Capital_Hudson combined
  cycle; the cohort is six Upstate_West plants plus one across that basis.
* **The unifying identity (D2, post-hoc, verified numerically to 1e-3).** The class peak multiplier
  buys out-of-merit protection of `(2.25 − 1) × HR_base × F_local`, so
  `protection(A)/protection(B) = (F_A/F_B) × (HR_base ratio)`; the HR ratio is a constant **0.9768**,
  so **the protection ratio simply IS the fuel-price ratio** — **$56.24/MWh** at 54034 against
  **$27.41** for the six in 2025. **One cause for both halves of nyiso-215's "un-levelled"
  observation**: over-correction where gas is dear (cost 2.05× while the zone LMP is only 1.10×),
  erosion where gas is cheap and the price level rose 120 %.
* **P4's prediction FAILED: MARGINAL, not ROBUST.** On `derive_reserve_duty_cc`'s own construction
  54034's per-year CAMPD online share is **0.04189 / 0.03085 / 0.11792** — **above the 0.10
  threshold in 2025**, i.e. not a duty-role plant that year, while the split routes its whole
  capacity to the peak band regardless. The pooled 2023–2025 `duty_stat` of 0.0635 conceals it.
  Basis-robust (identical on the derive's pooled p99.5 HSL and on 2025's own) and **CAMPD 2025 is
  complete, 8,760 h for every cohort plant**; deliberately not an EIA-923 number (preliminary
  vintage returns 0.0 for these plants — undefined, never a measurement).
* **D3 (post-hoc, beyond P4's declared scope):** 54034 is the only member crossing in any year, but
  **every** member's 2025 share is its three-year high by 2.0–4.8×, and 10621 reaches **0.0903**.
  The pooled denominator understates 2025 duty **cohort-wide**; 54034 is where it first changes an
  answer.
* **P5 COHERENT** on both declared limbs (intensity-when-on 0.865 within 0.773–0.908; mean run
  length 37.133 h within 9.697–38.741) — its conduct *shape* is cohort-like. **An ungated third
  statistic is disclosed as outside range**: pooled online share **0.06353** against
  **0.01217–0.04695**. The classification stands as written and is not restated.
* **P1 reproduction bar fires** over all 21 plant-years (max on-share diff **5 × 10⁻⁶**, max `mc`
  diff **0.001 %**), which discharges the one **LIVE** G-DRIFT hunk
  (`data/eia930/actuals.py::_screen_fuel_spike_columns`) **by execution**. G-DRIFT `51f2fc2d` →
  `71e62675` is 14 files (three more than nyiso-215 audited), 13 INERT with per-file reasons. **The
  C1/C4 benchmark half is passed forward, not absorbed** — a NYISO lane that re-solves or re-scores
  C1/C4 still owes it a check.

**The measured input is NOT the defect.** A Capital_Hudson CC genuinely pays more for gas than an
Upstate_West one; the zonal basis is measured and rule 14 `[R-ACCURATE]` protects it. Nothing here
proposes to weaken, haircut or rescale it. **`2.25` is not moved** (nyiso-194 killed it UP on shape,
nyiso-195 killed the econ ramp DOWN on direction, `phys_peak == peak`, rule 1's carve-out conditions
unmet).

**Handed INTO the owner's pending card (vii)** (nyiso-215 §6, cost space vs price-percentile space),
which this sharpens from *time*-varying to **also zone-varying**. A separate eighth card was
deliberately **not** opened: the pooled membership denominator and the cost-space level are the same
mechanism's two faces, and splitting them would invite deciding one without the other.

**Governance/environment.** Rule 29 step 0 only — no screen, no control (29(b) form 4: the keeper's
committed bundle IS the control), no bundle, nothing to delete under 29(c). Rule 22 training tier
only. Rule 23: `derive_reserve_duty_cc.py` **audited, never re-derived**. Rule 28: NYISO shard
stamped this session (`offer_curve_by_group`, where `cc_reserve_duty_split` is registered), failed
predictions included; no cell letter moves. Keeper `cache_key` re-measured at HEAD `71e62675` is
**`95d4d8d167373eb7`**; no solve spent, so it is recorded, not used. Tests named rather than
inherited — `test_gate_a_provenance.py`, `test_cc_summer_derate_reconciled_basis.py`,
`test_holdout_render_parity.py`, `test_campd_bins.py` — **75 passed, 0 failed**;
`ruff format --check .` 1,405 files already formatted; `ruff check` passes. **No pre-existing
failure at this HEAD.** nyiso-215's stale-`metrics.json` trap is unchanged and was not walked into;
still no unit test covers `cc_reserve_duty_split`'s split behaviour, and this session deliberately
does not add one — a guard encoding the current membership would now lock in the pooled-statistic
defect P4 measured.

## nyiso-217 — 2026-09-07

**The C1/C4 benchmark debt on `_screen_fuel_spike_columns` is PAID and CLOSED. A clean negative,
measured rather than argued.** Keeper unchanged (`2026-09-07-nyiso-213-summer-seam`); nothing
promoted, armed, screened, registered or regenerated; no marker moved. **ZERO LP.** Finding:
`docs/FINDING-nyiso217-eia930-fuel-spike-screen-bench-debt-2026-09-07.md`. PREREG:
`results/calibration/PREREG-nyiso217-eia930-fuel-spike-screen-bench-debt.md` (`d27b3705`, pushed
before the first number was read). Machine record:
`results/calibration/_nyiso217_screen_bench_debt.json`. Instrument:
`scripts/probes/nyiso217_screen_bench_debt.py`. **No in-sample rubric failure exists or is targeted.**

nyiso-215 §7 flagged the SPP-41 seam and was out of scope; nyiso-216 §1 discharged its **fleet** half
by execution and explicitly passed the **benchmark** half forward. This session pays it.

* **P1 FIRES — provenance by EXECUTION, not by reading.** The keeper scores **byte-identically**
  (43,261 chars, rc 0) with the screen live and with it monkey-patched to the identity (patch
  verified in force by two in-child assertions). `calibration_verdict.py` scores from **committed
  artifacts** — `bench/NYISO/<year>.json.gz` for C1/C2, the run payload's `fuelRows` for C4 — and
  never reaches the live loader. **A screen change cannot move a keeper score until a bundle
  regenerates the part**, and the slim keeper bundle carries no `inputs/` with which to do so. That
  is the direct answer to the handoff's question (a).
* **P2 FIRES exactly as declared.** Over 2022–2025 × every series, the moved set is
  **`{2024: other}` and nothing else**: `3.3846 → 3.3197 TWh`, one flagged hour (h6759, `NG: OTH`,
  16,117 MW vs a p99.9 of 3,290), reproducing SPP-41's declared NYISO effect to **0.0000 TWh**
  against a ≤ 0.001 bar. 2022/2023/2025 byte-identical in every series. The hurts limb (any other
  series or year, especially gas/coal/wind/solar) does **not** fire.
* **P3 FIRES, sub-case (3a) — C1 UNMOVED.** The one route from `e930.other` to `classFull` is
  `reconcile_vintage_classes`, gated by two switches in series. In 2024 **both are shut**: the
  `max(0, OTHER+biomass − other)` clamp holds with **0.3590 TWh** headroom at the tighter (screened)
  end (2.9611 vs 3.3197), so `∂_tgt/∂e930.other = 0` **exactly**, and the reconcile **provably did
  not fire**. Per-class `classFull` move **0.000000000 TWh** in all four years.
* **P4 FIRES — C2 unmoved** (0.000000000 TWh), by the same clamp, on the tighter test that has no
  band in its way.
* **P5 FIRES on both declared counts — C4 unmoved.** `NYISO ∉ CEMS_GAS_ANCHOR_ISOS` (`{CAISO}`,
  onset 2023), so C4 reads a committed payload value; **and** the screen flags **zero** hours in
  `NG: NG` / `NG: COL` in every year.
* **§8, un-pre-registered and labelled as such:** the third consumer the screen's own docstring
  names — the delivered VRE profile feeding the LP's wind bound — is **0 hours changed, max delta
  0.0** in every year. With nyiso-216 §1's fleet check, **all three declared consumers are now
  measured inert for NYISO.**

**Verdict: outcome-partition branch (B) — QUANTIFIED NULL. THE DEBT IS DISCHARGED AND CLOSED.**
No escalation is owed to another lane (branch (D) not reached).

**Reported at full magnitude, including against myself.** All five predictions fired and **no**
hurts limb did — stated plainly rather than dressed as a discovery: paying a verification debt
usually confirms, and what makes it evidence is that P1 was settled by execution and P2/P4 by exact
arithmetic, not by trusting the docstring under test. **My PREREG carried a construction defect
(§4.2):** P3's fired/did-not-fire test asserted a mutual exclusivity that does **not** hold (firing
forces `post == _tgt`, which is trivially in-band). Corrected in the instrument, reported as a
defect, and **the gate was not rewritten after the number was seen**. **What I did not isolate:**
whether the reconcile fired in 2022 and 2025 — pre-reconcile `classFull` is unrecoverable from a
slim bundle. It changes nothing (Δ`other` = 0 in both).

**TWO LATENT CHANNELS THE CLAMP DOES NOT PROTECT — named, not absorbed.** "Doubly protected" is a
fact about **2024**, not a structural property. (i) **2022's clamp is OPEN**: `OTHER+biomass =
3.2438` vs `e930.other = 3.2030`, headroom **−0.0408 TWh**, so `∂_tgt/∂other = +1` there; the screen
happens to move nothing in 2022. (ii) **NYISO's `wind` mirror is a 1:1 unclamped channel**
`classFull.wind ← e930.wind` — verified by execution (`actuals_source("wind","NYISO") == "eia930"`,
`solar → "eia923"`); a single `NG: WND` flag would move `a_gen` in full. Neither is a lever; both
are flagged so a future lane knows the channel is open before it starts. Also recorded: **2024's
fossil total sits only 0.1777 TWh (0.26 %) inside the 3 % reconcile band**, and the screen pushes it
**further inside**, never toward firing.

**Ungated statistic, reported whatever it says.** Committed bench `e930` vs HEAD's screen-on loader
agrees to **≤ 0.0005 TWh on every series in every year**, except (a) `solar`, a **basis** difference
verified by execution (NYISO's 930 extract has no solar; the render mirrors the EIA-923 total into
the `e930` slot by design), and (b) 2024 `other` at −0.0653 — **which is the screen**. So the
committed part *is* what HEAD would produce, and the screen is the only thing between them.

**Rule 14 `[R-ACCURATE]`: the screen is not weakened, haircut, bypassed or proposed for reversion**
under any outcome, and none was needed. **No bench part regenerated** (that would change what every
registered NYISO run is scored against — not a lane decision). Rule 22: **no out-of-training year
solved, scored or registered**; 2022 appears only as a loader-input diff and arithmetic on a
committed benchmark *input*, which "what is held out is the SCORE, never the DATA" leaves
unrestricted; 2020/2021 unspent, `final` never granted, freeze untouched. Rule 25: **no other ISO's
bench touched, read for comparison or regenerated.** Rule 28: `_screen_fuel_spike_columns` is a
**data-loader repair, not a solve-affecting mechanism** — no `ScenarioConfig` field, no CLI flag, no
`cache_key` membership, hence no matrix row and none invented; no cell verdict moves. **No eighth
owner card opened**; the seven pending rulings are untouched.

**Governance/environment.** G-DRIFT **re-measured** `51f2fc2d` → `12e71b89`: **22 files, +9,879/−23**
(eight more than nyiso-216 audited), **21 INERT** with per-file reasons, **1 LIVE** —
`data/eia930/actuals.py`, *this session's object*, measured rather than argued. Rule 29(b) scope
limit: the keeper's committed artifacts were the **object of study**, never a control for an arm.
Fleet instrument validated (`nyiso196_rebuild_checks.py --year 2024` exit 0, `git status
--porcelain -uno` **EMPTY**). Keeper `cache_key` re-measured at HEAD `12e71b89` is
**`95d4d8d167373eb7`** — unchanged from nyiso-216's reading, so capx D79's solve-surface fingerprint
did not move NYISO's key; recorded, not used. Tests named rather than inherited —
`test_gate_a_provenance.py`, `test_cc_summer_derate_reconciled_basis.py`,
`test_holdout_render_parity.py`, `test_campd_bins.py`, plus `test_bench_stamp_ast.py` (added because
this session's object is the bench chain) — **83 passed, 2 skipped, 1 FAILED**;
`ruff format --check .` 1,406 files already formatted; `ruff check` passes. **THE ONE FAILURE IS
PRE-EXISTING AT `main` AND IS SPP'S**: `test_gate_a_provenance::test_live_board_passes` cites SPP's
superseded keeper `2026-09-07-spp-2-crosswalk-hydro` against the designated
`2026-09-07-spp-3-screened-input`. Verified pre-existing **by execution** (`git stash -u` to a clean
`main` reproduces it identically: 1 failed, 12 passed); **not repaired here** — rule 25, the SPP
lane's (audit board F-5). The stale-`metrics.json` trap is unchanged and was not walked into (P1
read the scorer, twice). Still no unit test covers `cc_reserve_duty_split`'s split behaviour; this
session adds no test at all, because it changed no behaviour — the instrument is the re-checkable
record and it re-runs in seconds.

## nyiso-220 — 2026-09-08

**Object.** The licensed operating range and the period length it identifies — the FERC-licence half
of the owner's Q1 that NID could not serve (`CHARTER-nyiso219-hydro-budget-period-2026-09-07.md`
§10a), and the blocker behind Q2's phase-0 overlap arithmetic. **ZERO LP.** Keeper
`2026-09-07-nyiso-213-summer-seam` untouched; nothing armed, screened, solved or registered; no
`ScenarioConfig` field; no `src/market_sim/` change; no marker moved; no matrix cell letter changed;
**no held-out year spent.** PRECOMMIT `results/calibration/PRECOMMIT-nyiso220-hydro-operating-ranges.md`
committed and pushed **before any substantive document was read**. Full result:
`docs/FINDING-nyiso220-hydro-instrument-and-operating-ranges-2026-09-08.md`; instrument
`scripts/probes/nyiso220_hydro_instrument_index.py` → `_nyiso220_hydro_instrument_index.json`
(deterministic, byte-identical on re-run).

**Result — the instrument question nyiso-219 left open is SETTLED for 100 % of the fleet, and the
answer is NOT FERC.** For **both** dominant projects and **both** quantities (water entitlement,
operating band) the governing instrument is international. **Niagara P-2216 (51.89 % of fleet MW):**
the 1950 Niagara Diversion Treaty (Art. III–VII — a recurring time-of-day schedule of *instantaneous
minimum flow rates* over the Falls, not a volumetric budget) plus the **INBC 1993 Directive**
(rev. 2017) over the Chippawa-Grass Island Pool (operational long-term average **171.16 m / 561.55 ft
IGLD 1985**, tolerances at the Material Dock gauge, max accumulated deviation **±0.91 meter-months**;
measured 1973–2023 deviation 0.13). **NEITHER states any energy or volume conservation period** —
verified *mechanically* against the full treaty text (zero occurrences of *elevation, reservoir,
storage, pondage, forebay, pool, monthly, weekly, accounting, average*). **St. Lawrence P-2000
(19.48 %):** the **IJC 2016-12-08 Supplementary Order of Approval** with **Regulation Plan 2014**
(Bv7) — flows set "normally as specified by the approved **weekly** flow regulation plan"; J limit
700/1,420 m³/s week-to-week; M limit **weekly mean** Long Sault ≥ **72.60 m**; I limit ≥ **71.8 m** —
and, for within-week variation, the Commission's **directive on peaking and ponding** (Addendum No. 3
to the Operational Guides for Plan 1958-D; IJC letter 1983-10-13; renewed 2016-11-04 and 2021-11-30,
**the current term 2021-12-01…2026-11-30 spanning every scored year**). That directive states its
conservation periods **in words**: ILOSLRB glossary *"Ponding — variation in the day-to-day flows
over the course of a week"*, *"Peaking — variations in the hourly flows over the course of a day"*,
preserving *"the total weekly flow"* and *"the total daily flow"* respectively. **⇒ a 168 h budget
period for St. Lawrence from a published categorical duration class, ZERO fitted scalars** (rule 21
`[R-DOF]` case 2 — NYISO's own instrument, **not** NEISO's taxonomy; rule 25 `[R-ISO-SCOPE]` clean).
**Neither project's governing instrument contains anything resembling the LP's monthly period.**
Rule 13 `[R-MEASURED]` test applied **in writing** (finding §3): forward-producible from a standing
instrument, responds to conditions through the existing budget, not outcome-derived, **never swept**
— rule 21 case 3 and rule 1 `[R-STRUCT]` undisturbed.

**A FERC pull would have returned the wrong document for 71.38 % of fleet MW.** nyiso-219's flagged
caution is confirmed, and the reachable corpus (`ijc.org` 200 where FERC is 403) is the right one.

**P4, the self-falsification test aimed at the lane's own headline — CONFIRMED, three legs.**
Lewiston is EIA plant **2692** (HILARRI, mode *Pumped storage*, NID `NY00689`), distinct from Robert
Moses Niagara **2693** though under the same docket P-2216; the hydro budget excludes it on **both**
legs (`HYDRO_PRIME_MOVER = "HY"` excludes `PS` by construction; NYISO is in neither
`EIA930_PS_FOLDED_INTO_WAT` `{MISO, PJM}` nor `EIA930_PS_SPLIT_COMPLETE_FROM` `{NEISO: 2025}`); and
the model **already carries it separately** as `Upstate_West_eia860_pumped_storage`, **220 MW /
2,200 MWh = 10.0 h**, in Niagara's own zone. **The charter's 0.244 h headline stands and is
strengthened** — the 41× separation is the model's own independent corroboration.

**Thresholds reported as written, not restated.** **T1 MET** (both instruments, both quantities,
both projects, cited). **T2 MISS** — what was recovered is *level constraints*, not a band: a
long-term-average target (Niagara) and *floors* (St. Lawrence); a floor is not a band. **T3 NOT MET
AS WRITTEN** — its precondition was T2, which failed; the period was identified by a route T3 did
not contemplate (categorical, in words), reported as a **separate labelled result**, not a T3 pass.
**P3 MISS** — derived 168 h > the 73.07 h NID bound, because the prediction **conflated a
conservation period with a storage bound**; scored as a miss with the diagnosis given and the
prediction not rescued. P1/P4/P5 confirmed; **P2 — the prediction written to hurt — had its
mechanism confirmed exactly** (level + flow, no volume, stage–storage unpublished), which is *why*
T2 missed, and its feared consequence **landed in full for Niagara**. **A gap in my own partition is
reported rather than relabelled:** O3 said "band retrieved but not convertible"; Niagara is instead
"the instrument settles it by containing nothing", for which the partition had no cell.

**Traps.** A search for the peaking-and-ponding directive returned the **Lake Superior** Board's
St. Marys River directive (`/en/lsbc/`), not the St. Lawrence — nyiso-219's wrong-register trap class
in a new form, caught only because verbatim provisions were demanded. Cross-checks before
publishing: 71.376 % reconciled against nyiso-219's independent 71.38 %; NID `NY00678` surface area
37,500 acres ≈ 151.8 km² against the published ~150 km²; treaty silence checked by term scan, not
summary. Precision noted against my own convenience: the treaty *does* say "each day between the
hours of…", so the claim made is the narrower "no volumetric accounting period".

**Q2 — still blocked, but NARROWED.** St. Lawrence now has a period (168 h, 19.48 % of MW); **Niagara
at 51.89 % has none, and none exists in its instruments.** The overlap arithmetic is **not
attempted** — running it while the dominant plant has no period would produce a number that looks
like an answer and is not one. The blocker is no longer "FERC is unreachable" (a corpus problem) but
the narrower **modelling** question of the right representation for a plant whose instruments impose
no conservation period at all. **No mechanism proposed, designed or costed.**

**Governance/environment.** No mechanism tested ⇒ rule 28 `[R-MECH-MATRIX]` duty (b) **not engaged**;
no cell letter moves and none invented. **No eighth owner card opened** — the seven pending rulings
(nyiso-206, -207, -203, DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched. Access
re-measured here: `www.ferc.gov`/`cms.ferc.gov` **403** (also via `WebFetch`, a route nyiso-219 did
not have), eLibrary shell **200/22,464 B** reproducing nyiso-219's byte size, `example.com` **200**
(so the 403 is FERC's edge), Chromium **untested** (no `playwright` package; `playwright install`
forbidden — reported as untested, not failed). **A sharper FERC negative recorded so it is not
re-spent:** eLibrary's own `assets/config/app-settings.json` declares a real API base
`/eLibraryWebAPI/api/` with named endpoints, but its `Search`/`Document`/`DocFamily` controllers
**404** and `Docket`/`File` return ASP.NET scaffold stubs — a *characterized* dead end; and the
bundle's `"/api/v2/"` is **Datadog RUM telemetry**, not FERC's API. FERC's bot protection was not
attempted. Fleet instrument validated (`nyiso196_rebuild_checks.py --year 2024` exit 0,
`git status --porcelain -uno` **EMPTY**). Keeper `cache_key` re-measured at HEAD `7486cb9b` is
**`95d4d8d167373eb7`** — unchanged. `ruff format --check .` 1,417 files formatted; `ruff check`
passes; `check_mechanism_matrix.py` exit 0 with the pre-existing anchor warnings. Tests re-measured
rather than inherited: the five named files give **84 passed, 2 skipped, 0 failed** — **the
`test_gate_a_provenance::test_live_board_passes` failure the handoff reported at `ad78cc3e` is GONE
at this HEAD**, repaired by the ERCOT lane; nothing was inherited or "fixed" here.

## 2026-09-09 — nyiso-fuelvintage-1: the retiree window is provably in-sample-inert, the EP-level fuel seam is provably inert outright, and BOTH verdicts cost zero LP

Session `nyiso-fuelvintage-1` (PROMPT 3 of
`docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md` + ADDENDUM A1–A4).
Pre-registration: `results/calibration/PRECOMMIT-nyiso-fuelvintage-1.md` (`7f211902`, written
before every number below). Full record: `docs/FINDING-nyiso-fuelvintage-1-2026-09-09.md`.

**G-DRIFT, and a method a later NYISO lane will need.** The keeper's recorded `git_sha`
`51f2fc2d` is **permanently unreachable** — its branch `claude/nyiso-backcast-calibration-b6er34`
was squash-merged and deleted, so the commit survives only under `refs/pull/*`; `cat-file`, a
direct `fetch` of the sha and a fetch of the branch ref all fail. (nyiso-220 could still resolve it
on 2026-09-06.) The base was therefore anchored **by content**: recomputing the capx D79
`solve_surface.surface_rows("NYISO")` over `origin/main`'s last 400 commits reproduces the bundle's
recorded `48353917f7510af3` / 206 rows **exactly at `2084dc8a` and at no later state**, which is a
conservative superset base. The fingerprint alone proves **zero shared registry rows changed value**
for NYISO, closing all seven `SURFACE_MODULES` in one step; three new names entered and were
classified individually.

**TWO LIVE hunks, both then MEASURED rather than assumed.** (L1)
`f923_gas_price_plausibility_screen` defaults `True` since 2026-09-08 and its `__post_init__`
coercion does **not** fire for this keeper (`mode="backcast"` **and**
`gas_plant_monthly_fuel_pricing`), so the screen is armed where the keeper solved without it —
but it examined **68,919 rows and moved NONE**: every own-reported NYISO gas plant-month already
sits inside `[0.5, 2.0] ×` its state N3045 reference. (L2) `_apply_simple_cycle_hr_floor` (SPP-49)
is unconditional by design and **fires on 3 plants / 10 rows**: Greenport 2681 8.000→9.000,
Chautauqua LFGTE 57186 6.053→9.000, Albany Medical Ctr Cogen 59453 5.773→9.000. Everything else is
INERT with its reason cited — including `_PARTIAL_EXIT_WINDOW_START 2023→2019` (ercot-261), gated
on `partial_plant_exit_carry`, which is **`False`** here, so the handoff's double-count question
cannot arise for NYISO. **Consequence declared before any number existed:** the committed keeper is
not a valid control for a zero-delta claim, and **no control solve was spent** (rule 29(b)).

**CARD 1 — the fuel seam is PROVABLY LP-INERT; SHARD F was never spent.** Pre-registered: *"C3b
unchanged to three decimals, and more strongly the assembled generator gas price expected
byte-identical."* Measured with `gas_electric_power_monthly_level` armed on the keeper recipe:
`fuel_prices` **and** `mc_base` are **byte-identical in 2023, 2024 and 2025**, max |Δ| = 0.0 each
year. Those arrays are the LP's input, so the LP is byte-identical and no dispatch answer needed
buying (rule 29 `[R-SCREEN]` clause (0)). The reason is the seam, not the residual: `resolve.py`
applies the EP seam at `:151`, the F923 prints at `:228` and `apply_hub_basis_overlay` at **`:229`**,
and Transco Z6 covers **12/12 months in all seven years 2019–2025** (hub − N3045 blend, annual:
+0.040 / −0.034 / +0.533 / +1.377 / +0.432 / +0.106 / +1.180; max month 5.107, Jan-2025). **This is
the same finding, for the same reason, as the 2026-07-19 `gas_daily_shape` entry above** ("NYISO
exactly price-inert (Transco hub overlay supersedes)") — a third mechanism now dies on the same
overlay. Two corrections to the handoff's account: the overlay supersedes the **prints** as well as
the seam, and the print path alone would **not** have sufficed — the ADDENDUM-A2 written-cell census
measures it at **56.738 % of NYISO gas capacity-hours** (265 of 492 gas units; 35.982 % of all
cells), **not** the ~100 % MISO shows. Matrix cell moved **O → I** with a DO-NOT-REDO condition
naming what could reopen it: a month the hub index does not cover, not a re-run.

**GATE T3 / charter task 3 — PASS in all three training years, after I corrected my own test.** The
first formulation demanded an identical `n_gen`, which is wrong: the charter itself says the COD
ramp never touches `pmax`, so the added units are *supposed* to enter `FleetArrays`. The correct
test — artifact swapped (not one call site, since `load_retired_within_window` is reached from
`runner`, `outages` and the COD map) at identical code — requires strict additivity, added columns
**pinned to zero**, common columns byte-identical in matched order, and non-generator-axis inputs
byte-identical. Result: 812→870 / 809→867 / 809→867 gens, **58 added columns at 3,694.643 MW with
max availability 0.0 and max `min_gen` 0.0**, **0 removed**, all common columns and inputs identical.
A non-negative-cost column with upper bound 0 contributes exactly 0 to any optimum, so this **forces**
`max |class-hour delta| = 0.000000 MW` by construction where a dispatch comparison could merely
coincide — and it cancels L1/L2, which are identical in both arms. The pre-change reconstruction is
exact (477 rows / 141 plants / 2023–2024 only). Grains reconcile: the loader injects **45** gens /
4,187.600 MW on the shipped window vs **14** / 491.900 MW on the reconstruction — a difference of
**31 gens / 3,695.700 MW / 16 plants**, i.e. the handoff's 31 units on a nameplate rather than
net-summer basis, becoming 58 LP columns under CAMPD per-plant binning.

**Charter task 4 — the `NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']` caveat is RETIRED, and REPLACED.** "A
2018-2021 solve is short that capacity regardless of this overlay" is now false; the CF overlays are
intensive and never could have restored capacity, and the fleet channel did. Not a deletion: reading
the seam produced the successor caveat, now in the file — the table is still **derived** on the
operable fleet (`derive_nuclear_monthly_cf.py` builds from `load_fleet_from_csv`, which the retiree
injection does not feed, so every value is byte-unchanged and `--check` still passes), while
`fleet/arrays.py` **applies** the CF uniformly to every nuclear row, so the restored Indian Point
units carry the upstate fleet's measured monthly CF rather than their own metered output — presence
and retirement timing measured, within-year shape not. Re-deriving over the injected fleet is a
change to the derive's **fleet definition**, not a rule-23 data refresh, so it is **routed back to
the charter, not absorbed**.

**Gate baselines re-measured on this tree** (not inherited): `pytest tests/scoring` **16 failed /
1,532 passed / 12 skipped** — exactly A3's corrected baseline, so this branch adds none;
`check_cache_key_registration --base origin/main` RED on `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`
(the named pre-existing red); `check_mechanism_matrix` **exit 0**, still 0 after the cell edit.
`constants.py` blob verified against the server after push (5,580 lines, sha `a53e74f6`, rule 27).

**Operational finding for every lane:** `data/clean/` is gitignored, derived and **absent in a fresh
container**, and a NYISO solve dies deep in `run_year` on a hard `FileNotFoundError`
(capacity-deliverability, then `nyiso-interface-flows`) rather than no-opping.
`scripts/regenerate_clean.py` must precede any solve and took **well over 30 minutes** here.

## nyiso-fuelvintage-1 — 2026-09-09

**BOTH PROMOTED. Keeper `2026-09-07-nyiso-213-summer-seam` → `2026-09-09-nyiso-221-fuelvintage-span`
(CALIBRATED, C3c the lone ledgered caveat, criterion table BYTE-IDENTICAL to the superseded keeper
— zero flips in either direction).** Owner ruling 2026-09-09, verbatim: *"these should be promoted
as keepers on both 860 and gas shape counts regardless of inertness."*

**What is in the keeper that was not before.** ONE registered field —
`gas_electric_power_monthly_level` False → True, carried through `coal_prb_sigmoid_overrides` (44
entries → 45, none dropped or re-valued) — plus the 2019–2022 EIA-860 retiree-window artifact,
which carries no field at all. **ZERO free parameters**; the DOF ledger (13 entries, `n_residual`
6) is carried verbatim and `scripts/gen_nyiso214_attestation.py` refuses to write the attestation
if it is not. `authorized_price_tuning` NONE.

**The fleet is the headline, and the measurement is two-sided.** The window restores 31 units /
3,671.9 MW to NYISO's 2019–2022 fleets (Indian Point 2 + 3 = 2,050.9 MW nuclear; 1,487.0 MW coal).
Restored coal carries **exactly 0.000000 TWh in 2023, 2024 and 2025** and **0.655400 TWh in 2022**
(Dunkirk, 0 → 460.7 MW peak, Jan–Apr, displacing 0.5459 TWh of CC_CHP with the system total
conserved at +0.0073 TWh). A channel demonstrably live where it should be and dead where it should
be is stronger than "the residual is small". Charter task 3 is discharged at the array level by the
v3 artifact-swap GATE T3; charter task 4 (the `NUCLEAR_MONTHLY_CF_BY_YEAR['NYISO']` caveat) was
retired by the v3 run and replaced with its honest successor rather than deleted.

**The gas seam is promoted AND inert, and both halves are the result.** `fuel_prices` and `mc_base`
are byte-identical with the flag on in 2021, 2022, 2023, 2024 and 2025 — the Transco Z6 hub overlay
covers 12/12 months of every year and is applied last (`resolve.py` :151 seam → :228 F923 prints →
:229 hub). What arming buys is a **fallback level** under the rule 19 ordering, not a number, and
it is claimed as nothing more. Matrix cell `gas_electric_power_monthly_level` **I → K**, with the
DO-NOT-REDO condition unchanged: only a month the hub index does not cover reopens it.

**Reported at the gate, not absorbed.** The 2022 touchpoint on the corrected fleet is **worse on
price** — C3a −12.5 % → **−13.8 %**, C3b NRMSE 0.229 → **0.242** — because the restored Dunkirk
coal pushes model prices further below actual. Rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`: the
accurate input **stays** and the worse fit is a **discovered root cause** — a fleet missing Dunkirk
was silently compensating for a NYISO 2022 price level that is too low for another reason. Rule
30(c): a held-out year never downgrades the ISO, whose determination is the train-tier verdict.

**NYISO's validation ladder is 2022 ALONE, and nothing is spent.** 2020 is data-blocked
(`eia_generation_profiles.parquet` starts at 2021; NYISO alone of seven reaches that fallback,
reporting zero utility-scale solar to EIA-930). **2021 is data-blocked too, found by attempting
it**: `data/raw/NYISO-AS/requirements/` starts at 2022 and `nyiso_dynamic_reserve_requirements`
fail-closes rather than reverting to the static requirements it replaces. Disarming it for one year
was **refused** — a per-year recipe variant is not a touchpoint. Neither block is a governance
state; both authorizations remain real and **unspent**. `final` NOT granted; the locked test
(2019 / H1-2026) NOT spent.

**No control solve** (rule 29(b)). G-DRIFT was anchored **by content** — the keeper's `git_sha`
`51f2fc2d` is unreachable (squash-merged branch), so the capx D79 solve-surface fingerprint
`48353917f7510af3` / 206 rows was recomputed over `main`'s history and reproduces exactly at
`2084dc8a` and no later state. **Any later NYISO lane should expect the same and use that method.**
It found two LIVE hunks, so the committed keeper is **not** a valid control for a zero-delta
dispatch claim; the residual difference is entirely the SPP-49 simple-cycle heat-rate floor (3
NYISO plants clamped to 9.000 MMBtu/MWh), CT_PEAKER losing 0.0030 / 0.0039 / 0.0139 TWh in
2023/2024/2025 with the energy reappearing in the gas classes and 2025 hydro annual energy
identical to six decimals.

**Operational, for every lane.** Cloud solve shards that finish and are archived **without pushing
lose their bundles** — this session's v3 run lost T1 and T2 that way (~2 h of LP), so v4 re-solved
everything in its own container. Two contributing gotchas, both fixed here: `data/clean/` is
gitignored and absent in a fresh container (a NYISO solve hard-fails without it; a full
`regenerate_clean.py` takes 30+ minutes), and an untracked `results/_shared/` makes the tree dirty,
which **refuses `--reuse-solved`** on the next shard — now gitignored.

Record: `docs/RESULT-nyiso-fuelvintage-1-2026-09-09.md`,
`docs/FINDING-nyiso-fuelvintage-1-2026-09-09.md`,
`docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md`,
`docs/ADDENDUM-nyiso-fuelvintage-1-promotion-2026-09-09.md`.

## nyiso-225 — 2026-09-10 — the topology split is CLOSED AT PHASE 0, the nyiso-224 arm is REJECTED by owner ruling, and the queue it sent this lane to is STALE

**ZERO LP. Zero shards launched. Keeper `2026-09-09-nyiso-221-fuelvintage-span` UNCHANGED.** No
`ScenarioConfig` field, constant, derive script or model artifact changed; no run produced, so none
registered (rule 15 registers runs). Control = the committed keeper bundles `nyiso_fuelvintage_A` /
`nyiso_fuelvintage_H2` plus the preserved nyiso-224 arm bundle on `claude/nyiso224-cutset-2022` —
rule 29(b) **form 4** throughout, **no control solve spent**. Records:
`docs/FINDING-nyiso225-topology-split-closed-2026-09-10.md`,
`scripts/probes/_nyiso225_topology_phase0.py`, `results/calibration/_nyiso225_topology_phase0.json`.

**OWNER RULING 2026-09-10, two questions put with their costs and both answered:** *accept the
phase-0 kill and go to the queue* (over *charter the seam* / *charter F|G anyway*), and *reject the
nyiso-224 arm as constructed* (over *promote on the C3a gain* / *hold open*). Both executed here;
`nyiso_total_east_cutset_ttc` stays `False`, armed by nobody, cell **R**, and rule 31 `[R-RETAIN]`'s
promotion question is CLOSED.

**THE SUCCESSOR IS DEAD ON THREE INDEPENDENT LEGS, any one sufficient, all zero LP.**
**(a) There is no nested PAIR of constraints to separate, because only ONE of the pair is ever a
constraint.** The binding census over every posted internal interface, **both directions, all four
years** (MIS P-32, ≥95 % of each hour's own posted limit): `CENTRAL EAST - VC` **10.01 / 4.36 / 2.50
/ 3.62 %** and **nothing else binds** — `TOTAL EAST`, the boundary the successor was built around,
is **0.01 / 0.00 / 0.00 / 0.00 %**; `MOSES SOUTH` 0.00 % positive **and** negative; `DYSINGER EAST`
0.02 / 0.00 / 0.00 / 0.00; `UPNY CONED` 0.31 / 0.00 / 0.00 / 0.00; `SPR/DUN-SOUTH` 0.00 / 0.03 /
0.01 / 0.00; `WEST CENTRAL` carries the ±9,999 MW sentinel in 100 % of hours. The model already
carries the one boundary that binds. **(b) The split that COULD separate the legs is already closed
at G0.** The non-CE leg is **1,626 / 1,677 / 1,461 / 1,465 MW**, stable while `MOSES SOUTH` swings
**+1,352 → −188 MW** (corr 0.238 / 0.107 / 0.183 / 0.182), so it is **not** Moses South; it bypasses
zone F into zone G, and **both legs leave the same upstate zone**, so no split of A–E separates them
— the separation is at **F|G**, which nyiso-124 §2.1 closed with cause (no F/G transfer limit in MIS
P-32, in 36 months of MIS ATC/TTC, or in any of the four Gold Books; `ext_G` unrecoverable).
**DO-NOT-REDO discharged:** the new 2022 incidence evidence — **F is the dearest zone in New York**
(97.02 vs G 84.65) and F−G widens to **32.86** in the market's own CE-binding hours against the
0.36–2.65 nyiso-124 measured in 2023–25 — is a bigger basis, and **a bigger basis does not create a
published limit**. **(c) The split that IS identifiable is provably inert:** splitting inside A–E
along `DYSINGER EAST` / `MOSES SOUTH` (both posted, so G0 quantity 2 passes there) creates links
binding in **0.00–0.02 %** of hours. There **is** real congestion inside A–E (**$13.66/MWh** of the
$17.28 mean max–min spread is the *published* congestion component, not losses) but **no posted
limit produces it** — nyiso-124's quantity-2 failure again, upstate.

**THE ARM'S FREQUENCY MATCH WAS A COINCIDENCE OF AGGREGATES.** nyiso-224 recorded the armed link
binding in 12.47 % of hours against a market sub-cutset at 10.0 % and **carefully declined to claim
it as a pass**; measured hour by hour it should not have been. Arm binds **1,122 h (12.81 %)**,
market CENTRAL EAST **877 h (10.01 %)**, **both 71 h** against **112.3 expected if independent** —
**lift 0.63×**, precision **6.3 %**, recall 8.1 %. **The arm congests in the wrong hours and slightly
avoids the right ones**, and no re-quantiling repairs hour-level **anti-correlation** — a stronger
reason than rule 1 `[R-STRUCT]` (c)'s governance refusal, and a measurement rather than a rule.
**The rent is 14× short:** measured (F,G)−(A–E) in the market's own binding hours **$82.54**, the
arm's **$6.03**, on a mean |dual| of **$3.36/MWh** at 67.4 % loading.

**RECORDED, NOT CHARTERED.** The 2022 driver reproduces nyiso-124 §6.1's 2023–25 seam diagnosis on
the arm's own bundle: `NYISO_external>Long_Island` at bound **99.6 %**, `>NYC` **98.6 %**,
`>Capital_Hudson` **93.7 %** — ~**2,040 MW east of the cutset as a flat, price-insensitive block** —
against measured east-side schedules of **1,476 MW net**, a net including `SCH - NE - NY` at
**−400.3 MW** (New York *exporting* to New England, a direction the model's east-side seam never
takes), while `>Upstate_West` sits at bound only **12.6 %**. The seam cells are already `K` and
nyiso-125's identification refusal on the `Capital_Hudson` / `Upstate_West` border links is
load-bearing and unmoved, so this is evidence, not a lever.

**THE QUEUE IS STALE — ALL THREE ITEMS nyiso-224 NAMED AS LIVE ARE SPENT** (finding §7; §5.5
corrected this session). **(1)** the three-way re-screen is **SPENT and REFUTED** by nyiso-201,
which *is* that re-screen — both corrected gates cleared, the arm died on **C3a-2025 −6.9 → −11.7 %**,
and its hand-forward reads *"do not re-screen it"*; promoting would have **decertified** NYISO.
**(2)** "the run screen alone" is `nyiso_gas_bridge_startup_aware`, **SPENT and PROMOTED** by
nyiso-202 and in the current keeper. **(3)** Astoria 8906 is **ANSWERED NEGATIVE TWICE** — membership
(nyiso-201: **0 of 18** cells, the maximum distance from qualifying) and basis (nyiso-203: **clean
negative, sound as built**) — and the conviction is not even a standing property (2025 runs the
opposite way; the D-4 rider convicts in neither year). The list survived because nyiso-201/-202/-203
recorded outcomes in the keeper header and this log rather than as `QUEUE STATUS UPDATE` blocks.

**WHAT IS ACTUALLY OPEN — no live screenable lever.** No in-training rubric failure exists: the
keeper reads **CALIBRATED**, grade 7 of 8, **fails 0**, C3c the lone ledgered caveat. **2022 C3a is
validation-tier and can neither certify nor decertify** (rule 30(c); since `[R-HOLDOUT]`'s removal no
year certifies), its three routes now limit `R` / topology **closed** / seam `K`. **One OWNER CALL is
outstanding and is not a lane** (nyiso-203, reported and not taken): the NYC persistent-base
coefficient is a **daily-mean statistic applied hourly**, basis-matched **0.1750 → 0.1663** (−5.0 %,
−0.133 TWh over three years) — refused because rule 23 has no source-data trigger, because it would
**move** the coefficient where nyiso-140's correction did not (rule 21 admissibility is an owner
question), and because it **provably cannot reach** the 8906 object (0.13 % of that plant's hours
against its 5,400 binding hours). The hydro **Q2 stays blocked on evidence** (nyiso-220).

**Rules:** 1 `[R-STRUCT]` (structure decided this, not the residual — the arm was rejected holding an
11-point C3a gain and the successor killed on a binding census; `authorized_price_tuning` **NONE**);
13/14 (every number measured off committed postings; the F|G refusal is identifiability, which a
larger basis cannot cure); 21 `[R-DOF]` (zero free parameters proposed); **29 `[R-SCREEN]` — phase 0
did its whole job**, an arm with a computable pre-solve gate never reached a solve and the gate
killed the route for ~0 LP against a ~17-min span, G-CTRL form 4 throughout, no control solve;
30 `[R-MECH-MATRIX]` (NYISO shard stamped, no new row, §5.5 corrected); 31 `[R-RETAIN]` (nothing
deleted, promotion question put and RULED); 32 `[R-SHARD]` (parent ran no LP; nothing earned a
shard, so none was launched).

## nyiso-228 — 2026-09-12 — the 2022 LMP miss and the fleet-`r` decay are ONE object, and it is NEITHER the seam NOR the offer surface

**Three shards, three containers, ~5 solve-years of LP. The parent ran ZERO LP (rule 32
`[R-SHARD]`). Keeper `2026-09-09-nyiso-221-fuelvintage-span` UNCHANGED; nothing promoted.**
Records: `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` (pushed at `55cd0a6c` before the first
LP), `docs/ADDENDUM-nyiso228-the-2022-tail-is-MISTIMED-not-absent-2026-09-12.md`,
`docs/RESULT-nyiso228-2026-09-12.md`. Bundles `nyiso228_control_span`, `nyiso228_tail_span`,
`nyiso228_seamr_span`.

**THE DIAGNOSIS, measured off committed artifacts at phase 0.** 2022's price miss is a **WINTER**
miss: Jan −24.0, Feb −23.4, Dec −40.9 $/MWh carry **77 %** of the annual −9.55, and four Winter
Storm Elliott days carry **34 %**. **The same months fail in the TRAINING years** (2025 Jan −13.3 /
Feb −17.8; 2024 Dec −15.4), so this is a standing defect that 2023's mild winter hid — not a
holdout-year anomaly. The "bad fleet `r`" is the same object: interchange `r` 0.794 / 0.660 / 0.679
/ **0.473** falls in lockstep with D-A amplitude 62.7 / 61.2 / 52.6 / **41.8 %** of measured, the
chain nyiso-99 identified and refused the shape lever over.

**ADDENDUM 1 — I CORRECTED MY OWN §1.2, AND THE CORRECTED FINDING IS STRONGER.** I had written "the
model has no upper tail, ceiling ~$200–315"; that was measured on 2023–2025 and wrongly generalised.
In 2022 the model reaches **$1,429.99**, sheds firm load at VOLL, and drives `east_10min_total` to
its full published **$775** and `seny_30min_total` to its full **$500**. The real finding: the
model's **8 hours >$300 ALL fall on ONE DAY, 31 May**, against a market whose 101 fall in Jan 28 /
Feb 8 / Dec 34 / Aug 15 — **overlap ZERO, precision 0 %, recall 0 %**. The model produces a
*different, spurious* scarcity and none of the real one. **The 31-May event is an availability
artifact and the VOLL hour proves it**: on the 18th-busiest day of 365 the model sheds 125/236 MW at
VOLL while **5,412 MW** — Ravenswood 1,828, Bowline Point 1,242, Roseton 1,242, Empire 654, Selkirk
446 — dispatches **exactly zero** all day and runs at the true annual peak. In a VOLL hour every
*available* MW dispatches by construction, so that is proof, not inference. **What survives
unchanged: the three NYCA-wide reserve families bind in 0 hours of ALL FOUR years.**

**ARM C (CONTROL) — a control solve EARNED by G-DRIFT, and its prediction lands.** G-CTRL form 4 was
**falsified**: `data/raw/reference/reliability_floor_coeffs_NYISO.csv` (the nyiso-227 NYC ST_GAS
re-basing) landed on `main` after the keeper solved, so the committed keeper was not a valid
control. Arm C reproduces the keeper at **+$0.0255 / +$0.0284 / +$0.0237** on 2023/24/25 against
nyiso-227's independently measured **+0.026 / +0.028 / +0.025** — agreement to the third decimal in
all three years. It also reproduces ADDENDUM 1 on a fresh solve (2022 max $1,429.99, 8 h >$300, 2
VOLL hours).

**ARM A (`offer_curve_by_group` peak band ×1.50) — KILLED AT THE SCREEN BY ITS OWN G-MAG GATE, and
the reason is the finding.** Model p99 rose only **+$3.06** against a pre-registered $5–$120 band,
so the other three years were never spent (rule 29 `[R-SCREEN]` doing exactly its job). **The peak
band does not price higher — it LEAVES**: peak-band energy **3.2307 → 1.6531 TWh, −48.8 %**
(CC_REGULAR −74.5 %, CC_CHP −52.6 %, CT_CHP −52.6 %), with every cheaper band of every class rising
to replace it and served demand identical (151.5898 TWh both, zero slack, zero dump). A 50 % lift
makes the top tranche uneconomic and the stack refills from below at nearly the same clearing price:
`h>$300` 3 → 4, model max 313.94 → 315.75. **NYISO's model price ceiling is NOT set by the offer
surface, so rule 1's authorized price-tuning channel cannot reach this defect.** The ×1.50 was
frozen ex ante and was **not re-cut or swept** (condition (c)); the arm is reported as it landed.
**One gate was MIS-SPECIFIED BY ME and is NOT stacked against the arm**: G-ENERGY reads −0.0629 TWh
against ±0.05, but served demand is identical and the delta is storage round-trip (−0.0055) plus
flow-dependent transmission losses (−0.0574) — I wrote the gate on generation, which is not
conserved under a redispatch. G-MAG is the kill.

**ARM B (`nyiso_import_reconciliation` off) — the seam band is EXONERATED.** Both pre-registered
§3.2 legs fail: net interchange vs the EIA-930 measured total moves control → arm **−1.63 → −14.65
%** (2022), −0.49 → +2.21 % (2023), **+1.76 → +24.40 %** (2024), **+1.40 → +19.76 %** (2025) — 3 of
4 years blow ±5 % — and interchange hourly `r` improves in **0 of 4** years. **What the negative
buys: the wrong-hours allocation SURVIVES the band's removal**, so the band is not the cause of
nyiso-99's standing "quota met at the WRONG HOURS" caveat. Rule 14 `[R-ACCURATE]`: the measured band
is KEPT because removing it degrades a measured level.

**WHERE THIS LEAVES NYISO.** Two live hypotheses entered and **both are closed by measurement**, not
argument. What remains is **scarcity-price formation**, where phase 0 found every structural route
already adjudicated shut (`nyiso_spin_reserve_online` **I** — ρ\* 0.3426/0.3635/0.4619 with hydro's
10-minute headroom a coverage gap; `nyiso_synchronised_reserve` **G**; `nyiso_east_reserve_families`
**I**; `measured_ramp_capability` **I**; `temp_dependent_derate` **G**), plus the named successor:
**availability-window PLACEMENT**. That successor is **not** the sub-5-day family nyiso-227 closed,
has **no registered `ScenarioConfig` flag**, and therefore needs a code change and its own phase 0 —
it is recorded, not launched blind. **2022's C3c must never be quoted as a bare count**: at 0 %
precision a move from 8 to 20 hours need not contain one real scarcity hour.

**Also landed:** `curate_lmp.py` died with `KeyError: 'MGHG'` because the CAISO 2021/2022 DAM files
carry no GHG column, which aborted the **whole** `lmp` datatype for **every ISO** — the reason
nyiso-223 could not compute C3b at all. One `num_optional()` helper on the optional GHG component;
the four load-bearing components stay strict. Scoring path only, no LP path, no NYISO row touched.

**Matrix (rule 28):** `offer_curve_by_group` stays **K** with the peak-band-only lift recorded
REFUTED and DO-NOT-REDO; `nyiso_import_reconciliation` stays **K**, re-confirmed by direct
falsification, with nyiso-99's caveat attribution moved OFF the row.

## nyiso-230 — 2026-09-12

**KEEPER UNCHANGED: `2026-09-12-nyiso229-hourgrain-span`.** Nothing promoted, nothing
registered. **Phase 0 at ZERO LP, then ONE registered field BUILT and ONE screen shard
launched** (rule 32 `[R-SHARD]`: the parent ran no LP).

**THE HEADLINE IS A CORRECTION TO THE PREMISE THIS SESSION WAS GIVEN. NYISO HAS NO
PRICE-*LEVEL* DEFECT.** The owner asked for an upward offer-curve shift ("we have 6 % space
to keep everything within 10 % on c3a"). Measured instead: the in-sample geometric-mean
price bias is **−1.19 %** against an in-sample MAE of 4.90 % and a **12.2 pp spread**. The
level is already right and the **dispersion is 4× larger than the level**, so a uniform lift
cannot fix what is wrong — it slides all years by the same dollars.

**THE RESIDUAL IS A GAS-SLOPE DEFECT, r² = 0.9955 OVER FOUR YEARS.**
`gas_offer_net_revenue_margin` is armed and prices every band's markup at a **frozen
2023–2025** anchor (3.9046 $/MMBtu), so the offer moves by `markup_hr × (anchor − fuel)` —
linear, unsaturated. Against the keeper's own `_gas_series` (which reproduces the registered
anchor to 2×10⁻⁵):

| year | delivered gas | anchor − fuel | C3a | bias $/MWh |
|---|---:|---:|---:|---:|
| 2024 | 2.7969 | +1.1077 | +3.3 % | +1.240 |
| 2023 | 3.3566 | +0.5480 | +2.5 % | +0.820 |
| 2025 | 5.5602 | −1.6556 | −8.9 % | −5.920 |
| 2022 | 8.4431 | −4.5385 | −16.6 % | −13.460 |

**slope 2.6911 $/MWh per $/MMBtu · intercept −1.2766 · Pearson r = 0.99777.** The slope is
**independently corroborated, not fitted**: the mechanism predicts it equals the
marginal-weighted `markup_hr = base_HR × max(0, mult − phys)`, and 2.691 lands between
`CC_REGULAR`'s econ ladder (0.58–1.29) and `ST_GAS`'s (2.65–3.21) with `CT_PEAKER` above.
The intercept says that **at** the anchor the model is unbiased. *Honest limit recorded in
the finding: gas and price level are collinear, so correlation alone cannot separate this
from generic variance compression; the A/B is the decisive test.*

**C1-2024 MISSES BY 0.0458 pp.** `CC_REGULAR` share_pp **3.0458** against a ±3.0 band, while
the VOLUME leg **PASSES** (+3.132 TWh against ±4.05, 0.92 TWh of room). The flip needs
**60.3 GWh** displaced in-fleet — **0.162 %** of the class. Deficit classes: `CT_PEAKER`
−1.62, `ST_GAS` −1.38, `CT_CHP` −1.20 TWh, the merit disposition nyiso-187 attributed.

**THE OFFER BANDS *WERE* SHIFTED DOWN — AND A LIFT IS NOT A REVERSAL.** They live in
`pipeline/backcast_config.py::_NYISO_OFFER_CURVE`, not in any recipe, which is why the
keeper's `authorized_price_tuning` reads NULL and the provenance had gone untraced.
`CC_REGULAR.econ_high` **1.21 → 1.00**, `CT_PEAKER.econ` 1.27/1.98 → 1.00, `CT_PEAKER.peak`
13.15 → 4.0, `CT_CHP` all four → 1.0 — every one a **rule-25 `[R-ISO-SCOPE]` de-leaking of
ERCOT-borrowed values**, and NYISO's own `marg_econ_high_p50` (0.925) does not support the
old number. The code carries a **standing prohibition**: *"Do NOT re-arm this markup to
close C3a (rule #26, rule #1)."* **Open zero-LP object:** `ST_GAS`'s stated basis still cites
*"CC econ_high 1.21 / native CC marginal 0.925 = 1.31×"* — a **stale cross-reference** to a
value the same file records as removed; on the current reach the construction gives 0.897,
not 1.08, and `ST_GAS` under-runs 1.378 TWh.

**THE +5 % LIFT WAS ALREADY SOLVED IN SEPTEMBER.** `2026-09-09-nyiso-222-offer-plus5` is a
uniform ×1.05 on all four bands of all five gas classes against `2026-09-09-nyiso-221-
fuelvintage-span`. Read at zero LP it yields **NYISO's own full-span pass-through 0.66685**
(geometric; 0.7667 / 0.6824 / 0.5519 per year, declining with gas — the neiso-104/105/106
signature). Its dollar move is gas-invariant (+1.29 / +1.37 / +1.70), and it moves C1-2024
share_pp **−0.10 pp**. So a future level scalar needs **no screen**: both halves of the
neiso-106 division now exist.

**OWNER RULED ROUTE B** (2026-09-12, put with both options and their costs): the solve-year
anchor, not an offer-curve lift. **BUILT THIS SESSION:
`gas_offer_margin_zonal_anchor_vintage`** — the composition of `gas_offer_margin_zonal_anchor`
(zone) and `gas_offer_margin_anchor_vintage` (year), which hard-exit against each other under
rule 19, leaving a zonal ISO with **no route to the year index at all**. **Zero free
parameters**: `derive_zonal_anchors` already computes `{zone: {year: mean}}` and averages the
year index away; only the index moves. **The identity is pinned by test** — averaging the
runtime resolution over 2023–2025 reproduces `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` to the 4 dp it
is stored at (worst 4.7×10⁻⁵). 15 tests; cache keys hold (15 more); capacity-weighted ISOs
(PJM/ERCOT/MISO) are **refused** rather than mis-measured. Threaded into **both** runners and
guarded by a plumbing test, and **honouring the config field as well as the kwarg** — because
`replay_keeper.py --set` writes the field, so a kwarg-only gate would let an A/B silently
solve the control.

**Rule 28(a) DO-NOT-REDO is clear:** NYISO's cell was `U` and the row reserves it for this
lane. PJM's `R` came from its **S4 coal-displacement** gate (`COAL_BIT` +3.28 %); **NYISO's
coal is 0.000 TWh in every scored year**, so that kill reason cannot fire — a per-ISO
argument, not a transfer.

**SCREEN LAUNCHED, one shard, 2022** — named on **footprint** (|Δanchor| 4.5385 vs 1.6556 /
1.1077 / 0.5480), never on residual. Four structural stop-only gates, none reading C1/C3a/
C3b/C3c; the per-tranche prediction is fixed in the PRECOMMIT before the solve. **G-DRIFT
audited and all five solve-path hunks INERT** — including the one shared hunk
(`plant_taxonomy` PS/WAT), verified on NYISO's own registry rather than cited: it is
ERCOT-only with zero `PS` rows. Recorded honestly: **the keeper's `git_sha` `36ed7981` does
not resolve** — its shard branch is gone, rule 33(d)'s hazard realized — so the audit is
anchored on the keeper's solve timestamp and the last commit it provably contains.

**HOUSEKEEPING.** `nyiso227_rebasis_span` **PRUNED** on the owner's ruling (declined
promotion), clearing NYISO's leg of the Class-E parity gate; recoverable at
`06ab1e74d184d4dcd8c291fab88c553a9756c86a`. **Nothing structural was lost**: nyiso-227's
re-basing carries **no config field** (the bundle's config differed from the keeper's by
exactly 1 of 842 fields, and that one is nyiso-229's), the re-based row is live at HEAD, and
`scripts/score_bundle_price_shape.py` is untouched on `main`. Also discharged nyiso-229's
missed rule-28 promoting-session duty: the NYISO matrix shard and §5.5 header re-stamped to
the current keeper (nyiso-178 precedent, no verdict moved).

**Records:** `docs/FINDING-nyiso230-phase0-the-anchor-slope-2026-09-12.md`,
`results/calibration/PRECOMMIT-nyiso230-zonal-anchor-vintage.md`,
`src/market_sim/data/fuel/zonal_anchor.py`,
`tests/unit/data/test_gas_offer_zonal_anchor_vintage.py`.

**ADDENDUM (2026-09-13) — THE 2022 SCREEN STOPS, AND THE DEFECT IS IN THIS SESSION'S OWN
MIRROR, NOT IN THE MECHANISM.** Record: `docs/RESULT-nyiso230-the-2022-screen-2026-09-13.md`;
gates `results/calibration/_nyiso230_screen_gates_2022.json`. Two shard containers, one arm.

| gate | measured | verdict |
|---|---|---|
| G-CONF | three fields moved; recorded anchors off by a uniform **−1.3868 $/MMBtu** | **STOP** |
| G-SCOPE | **0** band multipliers / `phys_*` / `peak` / shares moved | PASS |
| G-PRED | ratios 0.585 / 0.694 / 0.694 / 0.645 / 0.694 vs [0.95, 1.05] | **STOP** |
| G-DEMAND | served demand **152.68167 TWh** both legs, dump **0.000**, slack **0.000** both | PASS |

**The gates were NOT re-cut and the remaining years were NOT spent** (rule 29 `[R-SCREEN]`).
The five recorded anchors miss the PRECOMMIT prediction by a **constant** −1.3868 in every zone,
which localises the cause upstream of the zone split; a zero-LP bisect over every gas flag lands
on exactly one — **`gas_hub_basis_overlay=False` reproduces the solved 7.0563 to 0.0000**. The
`run_calibration_full._recorded_config` mirror is called where `recorded_cfg` does not yet carry
the Transco Z6 hub overlay, while `run_calibration.run_year`'s own resolution is correctly placed
(overlay line 1960, resolution line 2565) — **so the two halves disagree.** The sibling
`gas_offer_margin_anchor_vintage` (pjm-169 F4) computes its mirror at the same point and carries
the same latent seam; nothing is armed on it anywhere.

**OPEN AND NOT GUESSED AT: which anchor the LP actually priced against.** If `run_year` recomputed
and overwrote, the LP solved on the correct 8.4431 while `run_config.json` records 7.0563 — the
FFR-2E class, and the **cache key then claims a resolution the solve never performed** (rule 24
`[R-REGISTRY]`). **The arm's +5.470 $/MWh (67.6573 → 73.1275, direction as declared ex ante) is
therefore NOT attributable and must not be quoted as the mechanism's effect.** Nothing promoted,
nothing registered, keeper unchanged.

**Retrievable, zero re-solves for 2022** (rule 34 `[R-SHARD-PROMOTABLE]` (e)): 17 files at
`90475b1c2b56283018396504e39ad638ac367c97`; the first shard's blocker record at
`9f11d68e16707b47732e43474af46811867fb640`. Both shards archived (rule 33).

**INFRASTRUCTURE FIX LANDED THIS SESSION, and it is worth more than the screen.**
`scripts/regenerate_clean.py` put only `<repo>` on its subprocesses' `PYTHONPATH`, but
`scripts/lib/clean_io.py` then imports `market_sim`, which needs `<repo>/src` — half the chain.
On any container without an editable install every curation script died with
`ModuleNotFoundError: No module named 'market_sim'`, raised from INSIDE `clean_io`, in a traceback
naming neither `PYTHONPATH` nor the caller. **That opaque failure has now cost three NYISO shards,
each mis-diagnosing it differently** — nyiso-228 concluded `capacity-deliverability` was INERT and
recorded it as such (**it is not**; that matrix note is wrong), a nyiso-229 shard blocked on the
datatype being absent, and this lane's first shard reported it as an OOM at 29 s plus a missing
`data/clean` write permission. Neither. With `src/` on the path the datatype regenerates in
**0.7 s**, verified in the shards' exact condition.

## nyiso-229 — 2026-09-12

**KEEPER PROMOTED: `2026-09-12-nyiso229-hourgrain-span`** (bundle
`results/calibration/nyiso229_hourgrain_span`), superseding
`2026-09-09-nyiso-221-fuelvintage-span`. 2022 touchpoint
`2026-09-12-nyiso229-arm-y2022` folded to it (rule 30 `[R-TOUCHPOINT-FOLD]`).

**ONE registered field: `unit_outage_window_hour_grain` False → True.** The CAMPD
unit-outage window is read at its **detected hour grain** instead of re-expanded to
`outage_start` 00:00 → `outage_end` 23:00. The detector has always worked in hours while
the extract stored **dates**, so the loader asserted up to 23 h at *each edge* it never
detected — exactly where the event-based contract guarantees the neighbouring hour was
**running**. That is the caiso-181 seam; caiso-183 built the carriage and CAISO's extract
already carried it, NYISO's did not. Basis is rules 14 `[R-ACCURATE]` + 1 `[R-STRUCT]`:
the same measured input at its own resolution. **Zero free parameters**, DOF ledger carried
verbatim (13 / n_residual 6, zero new entries), `authorized_price_tuning` NONE.

**Measured at zero LP before any solve:** the day-grain reconstruction asserts
9,872 / 10,167 / 8,529 / 8,144 unit-hours unavailable in 2022–2025 while the meter shows
`grossLoad > 0`, carrying 1,376.9 / 1,332.5 / 1,075.9 / 952.7 GWh; **~95 %** of those hours
lie within 23 h of a window boundary and carry **~99.9 %** of the energy — the schema
rounding windows, not the detector misplacing them. It also takes **293** same-unit 24.0 h
boundary-day overlaps to **zero** (MISO's `unit_outage_per_unit_clip` fingerprint, which is
deliberately *not* co-armed — rule 19 `[R-ONE-MECH]`).

**What it buys.** 2022's spurious 31-May VOLL event is **gone**: firm-load slack
**360.472 → 0.000 MWh**, both VOLL hours cleared from 124.894 and 235.577 MW against
3,657 MW of restored availability. Reserve shortfall falls in **all four** years
(−71 / −59 / −55 / −21 %), both Long Island families to zero in 2022. **Served demand is
identical to 4 dp in every year and dump is zero everywhere** (computed and asserted in the
attestation, not claimed). **C3b improves in 2024, 0.179 → 0.174 — the tightest-margin year
of the three.** C3a improves 2023 (+5.00 → +3.18) and 2024 (+5.29 → +3.23).

**THE COST IS A DETERMINATION DOWNGRADE, and it is the headline half of this entry:**
**CALIBRATED (grade 7/8, fails 0) → NOT-YET (grade 6/8, fails 2).** The deciding criterion
is **not** C3c — **C1-2024 `CC_REGULAR` goes +3.13 TWh / share +3.0 pp, out of band**, a
PASS → FAIL flip in the class that absorbs the restored CC availability. Because C1 then
also fails, C3c loses lone-failure status and the rule-22 standing rule stays silent by its
own guard (a), so the ledgered caveat that carried the superseded keeper to CALIBRATED is
unavailable and **both failures stand**. Also degrading: C3a-2025 −7.15 → −8.79,
C3a-2022 −12.96 → −15.82, C3b-2025 0.160 → 0.169. The 2022 C3c tail goes **8 → 4 h** above
$300 with **precision still 0.000** — all four on 31 May, the wrong day, against the
market's 101 hours in Jan/Feb/Aug/Dec — so it removes most of a spurious event and creates
**none** of the real one. **It does not touch the winter object** (Jan/Feb/Dec, 77 % of the
2022 miss).

**The D-5(b) worse-determination stop fired and was escalated** (the nyiso-192 precedent).
**A correction is on the record:** the session first reported *"no criterion flips
PASS→FAIL anywhere"* — that was measured on C3a/C3b only, C1 was never scored, and C1 does
flip. The owner's first approval was given on that wrong statement; the record was
corrected, the promotion re-put, and the owner ruled *"Flip it to keeper"* with the
downgrade known.

**G-CTRL** rule 29(b) form 4, validated **empirically**: a day-grain control leg reproduced
the committed 2022 touchpoint **identically** on slack, served demand, annual max and the
h>$300 count, differing only **+0.0355 $/MWh** on the mean — the one LIVE hunk the G-DRIFT
audit named (`reliability_floor_coeffs_NYISO.csv`, nyiso-227's re-basing).

**Cost in LP:** nine shard containers for four bundles. One OOM-killed; one died on a
`TypeError` that was this session's own plumbing bug (the field threaded through
`run_calibration_full` but not into `scripts/run_calibration.run_year` — the precedent's own
comment says *"an override missing here would solve the control twice"*, so the crash was
the good outcome); one interrupted for the same bug; one blocked on `capacity-deliverability`
being absent from `data/clean` (which nyiso-228 had recorded as **inert** — it is not).

**Records:** `docs/FINDING-nyiso229-phase0-the-outage-window-grain-2026-09-12.md`,
`docs/RESULT-nyiso229-the-2022-screen-2026-09-12.md`,
`results/calibration/PRECOMMIT-nyiso229-outage-window-hour-grain.md` + three addenda,
`results/calibration/_nyiso229_screen_gates_2022.json`,
`scripts/gen_nyiso229_attestation.py`,
`docs/handoffs/FINDING-nyiso229-arm-y2024-blocked-2026-09-12.md`.
**New rule this session:** 33 `[R-SHARD-ARCHIVE]` (owner instruction).

## nyiso-231 — 2026-09-13

**KEEPER PROMOTED: `2026-09-13-nyiso231-anchor-span`** (bundle
`results/calibration/nyiso231_anchor_span`), superseding `2026-09-12-nyiso229-hourgrain-span` AND
its folded 2022 touchpoint `2026-09-12-nyiso229-arm-y2022` — **both pruned in this session**
(rule 35 `[R-PROMOTE]` (a)). **ONE bundle now carries all four registered years 2022–2025** where the
incumbent needed two registered runs. Promoted under the owner's standing formula, put in this
session verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."* — **and both halves clear**:
structure improves AND essentially every gate improves.

**ONE REGISTERED FIELD MOVES: `gas_offer_margin_zonal_anchor_vintage` False → True.**
`gas_offer_net_revenue_margin`'s identification point resolved on **(ZONE, SOLVE YEAR)** instead of
the frozen 2023–2025 window mean. **ZERO free parameters**, DOF ledger verbatim,
`authorized_price_tuning` NONE, and **zero** band multipliers / `phys_*` / `peak` / shares move in
any year — so this is **not** the rules 1/13 carve-out. Basis is rules 13 `[R-MEASURED]` + 14
`[R-ACCURATE]` + 1 `[R-STRUCT]` on a measured construction defect, not the residual.

**DETERMINATION, ISO tier (2023–2025, rule 30(c)): NOT-YET (grade 6/8, 2 fails) → CALIBRATED**, C3c
the lone ledgered caveat. **C1 13/14 → 14/14** (free 10/10): the incumbent's open cell, C1-2024
`CC_REGULAR` share_pp **3.05 → 2.7** against a ±3.0 pp band, **closes**.

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **C3a** | −16.6 → **−9.9 %** (FAIL→PASS) | +2.5 → **+0.6** | +3.3 → **+1.1** | −8.9 → **−5.9** |
| **C3b** | 0.249 → **0.209** (still FAIL) | 0.122 → 0.122 | 0.174 → **0.176** ← the one regression | 0.169 → **0.149** |
| **C3c** h>$300 | 4 → **7** / 101 | 0 → 0 / 10 | 0 → 0 / 13 | 2 → **4** / 42 |
| **C1** `CC_REGULAR` | +5.25 → **+5.20** TWh (still FAIL) | pass | **FAIL → PASS** | (923 preliminary) |

**Every criterion in every year improves or holds, with exactly one exception** — C3b-2024
0.174 → 0.176 against a 0.20 band, 0.024 of room, reported at full magnitude.

**REPORTED AND NOT ABSORBED.** The **four-year** bundle reads **NOT-YET**, on 2022's C1
(+5.20 TWh, +3.9 pp) and C3b (0.209). That is **not a regression**: the incumbent's own 2022
touchpoint read NOT-YET on **three** failures (C1, C3a, C3b) and this run fails two of the same
three, each by less. Under rule 30(c) the ISO's determination is the 2023–2025 verdict; both
surfaces state that in place.

**AND THE PREDICTION OVERSHOT.** PRECOMMIT Addendum A predicted the C3a spread would collapse to
**~2 pp**; it lands at **11.0 pp** across four years (19.9 pp before). **The anchor explains roughly
HALF the measured slope** — phase 0's disclosed collinearity caveat bites, and the remaining half is
the handed-forward object. The r² = 0.9955 regression was real but it was not all mechanism.

**THE STRUCTURAL CASE FOR THE COMPOSITION, measured this session: `Δanchor(zone, year)` does NOT
factorize.** The Upstate_West / Capital_Hudson ratio runs **0.7356 / 0.2518 / 0.2778 / 0.2691**
across 2022–2025 and the zone **ordering flips** between 2023 and 2024. So neither
`gas_offer_margin_zonal_anchor` (zone only, year averaged away) nor `gas_offer_margin_anchor_vintage`
(year only, zone averaged away) can reach the level — the argument for the composition made on
measurement rather than tidiness.

---

### The session's other half: a RECORDING defect, settled and repaired

**nyiso-230's screen STOPPED on two gates, and the cause was in the record, not the mechanism.**
`run_calibration_full._recorded_config`'s mirror resolved the per-zone anchors ~144 lines **above**
the block that sets `gas_hub_basis_overlay`, while `run_year` sets the overlay **before** it
resolves — so `run_config.json` recorded `Capital_Hudson 7.0563` where the LP priced **8.4431**, a
uniform −1.3868 in every zone, and the recorded config was internally inconsistent
(`gas_hub_basis_overlay: true` beside anchors that reproduce only at `overlay=False`).

**Settled at zero LP** (`run_year` takes no config object; `recorded_cfg` reaches `write_run_config`
and nothing else), and then **confirmed by the span itself**: its 2022 leg reproduces nyiso-230's
arm price to **0.0000 $/MWh** while its recorded anchor moves 7.0563 → 8.4431 — **an unmoved LP
beside a moved record**, which is exactly what a write-only defect predicts. nyiso-230's
+5.470 $/MWh is therefore attributable after all, at the full anchor delta.

**Repaired structurally, not positionally:** one shared resolver,
`run_calibration_full.mirror_solve_year_gas_anchors`, **fused to `_recorded_config`'s `return`**, so
a future `if flag:` block lands *above* it. Both inline mirrors deleted, not zeroed (rule 26). The
PJM sibling `gas_offer_margin_anchor_vintage` carried the same seam **plus** a kwarg-only gate that
would have let a `replay_keeper --set` A/B solve the CONTROL while recording an armed anchor; both
fixed together, PJM told in `governance.md`, **no PJM cell edited** (rule 28). Guard:
`tests/unit/data/test_recorded_config_gas_anchor_mirror.py`, 12 tests.

### Two open objects CLOSED at zero LP

1. **Massena 54592's "200 % of plant" is REDUNDANT BOOKKEEPING, not an energetic defect — RETIRED,
   not handed on.** All **30** `eia923_netzero` rows in NYISO's extract are `unit_pct_of_plant`
   100.0 for 365.0 days; only **two** plant-years also carry a detected row (54592/2022,
   50368/2025); `outages.py:1570` clips at `[0,1]`. Verified empirically: `cap_mw` **0.0000 in every
   hour** and `mw` **0.0 MWh** in both legs. At 50368/2025 the netzero row is in fact *adding*
   accurate information — `CT1`/`CT2` are 50 % each and their windows miss the summer.
   *(Noted in passing: 15 of the 30 netzero rows are dated **2026** — inert for a 2022–2025 backcast,
   live for any hindcast that reads 2026.)*
2. **`ST_GAS`'s stale cross-reference is a stale DERIVATION INPUT, not a stale comment** — and that
   is what makes it the next lever. Its stated basis cites *"CC econ_high **1.21** / native CC
   marginal 0.925 = 1.31×"*, a CC value the **same file** records as removed, and **the registered
   1.08 matches that CITED construction to 0.2 %** (1.0857). So the rule-25 `[R-ISO-SCOPE]` de-leak
   should have propagated to `ST_GAS` and did not. On the current reach the same construction gives
   **0.8973** — `ST_GAS` sits **20.4 %** above its own stated basis — and correcting it moves
   `markup_hr` econ_low **2.6535 → 0.7143** (−73 %) and econ_high **3.2054 → 1.1764** (−63 %).
   Direction is right for C1 (`ST_GAS` under-runs 1.38 TWh in 2024) but pushes price **down**, so it
   is **not** co-armed with the anchor gate (rule 19). **Top of the queue.**

### A governance finding, and a correction to my own claim

**The incumbent keeper was solved OFF-PIN** (highspy 1.15.1 against the repo's long-standing
`==1.14.0`). Auditing all 41 committed bundles: **5 are off-pin**, and exactly **one designated
keeper** was affected — NYISO's, both its registered runs. *(Three off-pin ERCOT bundles are not the
ERCOT keeper; reported, not touched — rule 25.)* The standing handoff note was **wrong on all three
clauses**: deps are `==` pinned not floor-pinned, all 41 bundles **do** record `environment.packages`,
and all 41 **do** record their HiGHS.

**I then wrote that the keeper "is not reproducible at HEAD". That was a prediction and it is
wrong.** A control re-solved on-pin reproduces the off-pin one **exactly**: all **52,560** hourly
zonal prices and all **6,648,840** unit-hours (`mw`, `mc`, `cap_mw`) identical to **1e-9**, every
class energy to 10 dp. So the degeneracy worry is measured inert for this model and version pair,
**rule 29(b) form 4 is vindicated rather than broken**, and nyiso-230's differencing was never
contaminated. What survives is narrow: the keeper's *environment record* was off-pin. This promotion
closes it — the new keeper is on-pin. **Suggested durable fix, for whoever owns `audit_keepers.py`:
a check that every designated keeper's recorded package set matches `requirements.txt`.** Nine lines,
and it would have caught this the day it happened.

**Also corrected, for the next lane:** rule 31 `[R-RETAIN]` states that *"the parity gate only ever
sees committed dirs, so an ignored bundle can sit on local disk indefinitely without turning anything
red."* Measured: `check_registry_payload_parity.py` scans the **working tree**, so a gitignored
local bundle DOES turn a local run red. It is green in CI (where the working tree is the committed
tree), so the rule's conclusion holds where it matters — but the mechanism is not what the rule says,
and a lane that reads the local red as a real failure will chase it. NYISO's leg is clear: 0 of the
three probe dirs are tracked in HEAD.

### Operational, measured — do not rediscover

* **The clean-data list for a NYISO solve is EIGHT datatypes, not one.** The inherited note said
  `capacity-deliverability` "and NOTHING broader"; NYISO's solve path also needs
  `nyiso-interface-flows` (it dies in `nyiso_par_attributed_ttc_hourly`), and the verified list —
  `capacity-deliverability nyiso-interface-flows nyiso-reserve-requirements nyiso-downstate-gas
  nyiso-renewable-curtailment reserve-requirements ramp-capability unit-outage-events` — regenerates
  from a cold `data/clean` in **61 s**. A bare `regenerate_clean.py` with no arguments is ~30 minutes
  and mostly other ISOs.
* **A shard that backgrounds its solve and "queues the push on process exit" can strand.** Two did
  this session; one lost a finished bundle. **There is no tool in this session that can message a
  cloud shard** (`create_session` / `interrupt_session` / `archive_session` only), so a stranded
  shard is unrecoverable. Run the solve in the FOREGROUND so the turn cannot end before the push.
* **A four-year NYISO per-plant span is ~6 min/year, ~25 min total** — far under the 90–150 min this
  session budgeted.
* **Push the keeper bundle in two commits** (sidecars 83.4 MB, dispatch 81 MB); the dispatch layer
  needs a `.gitignore` **negation** of both the directory and its contents, plus a plain `git add`
  (`git add -f` is refused by the permission classifier).
* `git commit --amend` is refused as **[Git Destructive]** — make a follow-up commit instead. And use
  `-F -` for messages containing backticks; `-m` lets the shell eat them.

## nyiso-232 — 2026-09-13

**KEEPER UNCHANGED: `2026-09-13-nyiso231-anchor-span`.** The session's arm was **SCREENED AND
STOPPED** on a pre-registered gate. A screen may kill an arm; it may never promote one, and the gate
was not re-cut after the fact.

**THE DEFECT IS CONFIRMED AND IS NOT IN DISPUTE.** `_NYISO_OFFER_CURVE`'s `ST_GAS` `econ_low`/
`econ_high` are DERIVED as the measured native steam marginal HR × the block's own cited *"CC class
reach ratio (CC econ_high **1.21** / native CC marginal 0.925 = 1.31×)"* — and **1.21 is the ERCOT
keeper value the same file records as REMOVED under rule 25** (audit C-13, B-NYI-1). So ST_GAS
carries ERCOT's 1.21 **multiplicatively**: the de-leak removed it from the cell where it was
*written* and left it standing in the cell where it had been *multiplied in* (rule 26 `[R-DELETE]`,
one derivation step removed). The registered 1.08 reproduces the CITED construction to
**0.531 / 0.288 / 0.075 %** on the file's own two recorded native-steam triples — every reading
within 1 % — while the **current** reach gives **0.8973, 16.9 % away**, so the band is not
reproducible from the file's own inputs today. *(The handoff's "0.2 %" is not any of the three
readings; corrected.)*

**BOTH GATING QUESTIONS SETTLED AT ZERO LP, BEFORE ANY ARITHMETIC WAS APPLIED.**
*(i)* **NOT a rule 23 `[R-FROZEN-DERIVE]` re-derivation** — the ST_GAS source data is untouched and
the `phys_*` keys keep it; what moves is a borrowed multiplier on top, and rule 23's trigger ("never
because a residual moved") is not engaged since no residual moved and the change pushes price the
**wrong** way. It is an **incomplete rule 25 enforcement**. *(ii)* Of the block's **two**
identifications the **CONSTRUCTION is load-bearing** and the outcome-based one ("reproduces measured
steam volume") **cannot be promoted to rescue it** — the block itself calls that *"validating the
level a priori, **not** residual-fitted"*, and re-reading a corroboration as **the** identification
is rule 13 `[R-MEASURED]`'s forbidden move and fails its forward test.

**THE CONSTRUCTION BUILT — narrower than the handoff proposed, and MEASUREMENT is why.**
`econ_low`/`econ_high := 1.0`, the rule-24/25 **neutral** — the identical remedy this file applied to
`CC_REGULAR.econ_high` and to `CT_PEAKER`'s econ bands in the SAME audit. **Zero new literals, zero
free parameters, no DOF entry.** The handoff's propagate-the-reach arithmetic was **refused**: the
current reach's numerator is a declared **neutrality placeholder**, not a measurement. `committed`
and `peak` **excluded** as nyiso-199 excluded them — and `committed` was caught by the probe rather
than assumed: its markup clips to 0 in both legs, so at markup 0 the multiplier only scales **fuel**,
and moving it to 1.0 would price steam min-load **9.4 % below its own measured burn** (−$4.09/MWh).

**PHASE 0 (zero LP, all four years).** Non-ST_GAS offer max|Δ| **$0.0000000000/MWh** over 665–671
matched rows; non-ST_GAS `pmax` max|Δ| 0.0; ST_GAS `pmax` total unchanged 8902.4000 MW; `committed`
and `peak` byte-identical. Econ offer **−$8.61 / −$3.17 / −$2.80 / −$5.41** per MWh. **Declared
before the solve:** the flat ramp collapses the 6-slice `econc00..05` ladder to `econlo`/`econhi`,
ST_GAS **88 → 44 rows**; the solved arm reads **exactly 44**. Screen year **2022** named on
**FOOTPRINT** (38.1 vs 31.2 / 20.1 / 16.0), never the residual. **G-DRIFT recorded BEFORE the arm** —
all six changed paths INERT for NYISO — so form 4 held and **no control solve was spent**.

| gate | verdict | measured |
|---|---|---|
| G-CONFINE | PASS | worst non-ST_GAS move CT_PEAKER −0.416 TWh vs a 0.763 budget |
| G-DEMAND | PASS | served 152.68167 both legs, dump 0, slack 0 |
| G-MAGNITUDE | PASS | ST_GAS 6.6384 → 7.3090 TWh (+0.6706), inside the 1.574 ceiling |
| G-ROWS | PASS | 44 |
| **G-NONTARGET** | **STOP** | **C3a-2022 −9.86 % → −11.61 %, PASS → FAIL** |

**ON THE MERITS, reported in full because it is the case FOR the arm.** Price cost only
**$1.42/MWh (−1.94 %)**, materially smaller than the PRECOMMIT's own worry. **ST_GAS −1.148 →
−0.477 TWh (58 % of the gap closed)**; **CC_REGULAR, the failing C1 cell, +5.196 → +5.038 TWh** and
share 3.93 → 3.83 pp; gas family total conserved (−0.029 TWh), C2 PASS → PASS. Against it:
CT_PEAKER +0.077 → −0.339 and CC_CHP −0.225 → −0.308, both worse, both well in band.

**AN UNRESOLVED FLAG, NOT resolved in the arm's favour.** D-2/**C8** reads FAIL on the arm (2022
ST_GAS forced share 33.6 % > 30 %) — **protective** tier, and **not** among the pre-registered gates,
which is a **gap in the gate set** and is stated as such rather than used as an exemption. The flip
is driven **entirely by the denominator** (forced energy 1.9803 → 1.9187 TWh, −3 %; D-2 class total
8.571 → 5.705 TWh, −33 %), and that denominator reconciles with **no** dispatch-side measurement in
either leg — `class_hourly`, `class_band_hourly`, the dispatch parquet's `klass`, and a `unit_id`
join to the rebuilt fleet's `plant_group` **all** show ST_GAS **rising**. D-2's basis is internally
consistent on the control across all four years (ST_GAS ×1.29/1.20/1.24/1.27 of the dispatch-side
total) and **inverts to ×0.78** on the arm. On every basis that reconciles, the forced share **falls**
(26.3 % vs the control's 29.8 %). **Not diagnosed, not claimed to be a bug**; the bounded claim is
that the C8 flip is uncorroborated and that D-2's denominator behaves anomalously under a change to a
class's **tranche structure** — which generalises to any mechanism that collapses or expands a
smoothing ladder.

**COMPANION FINDING — NYISO's C3a residual is TWO separable objects, and a zero-LP test separates
them.** Progressively removing each year's highest-**actual**-price hours leaves the year-to-year
spread **invariant** (10.23 → 10.09 pp while 5 % of hours are removed, r vs gas −0.92 to −0.99),
while the **level** lifts ~+13 pp in every year and **flips sign**: with the tail gone the model is
**over-priced by +4.1 to +14.2 % in all four years**. So (A) a level error carried by the extreme
tail — the model compensates for the tail it cannot form by pricing ordinary hours too high, and the
two errors partly cancel in the annual mean, which is why C3a passes in 2023/2024 while both
components are large; this is C3c / issue #1344 — and (B) a gas-monotone tilt of ~10.1–10.8 pp that
**survives removing the tail** and is a real, separate, still-open object. *(A correction kept
visible: on the monthly regression alone I first concluded the leftover slope "is not a gas object"
and recommended spending nothing on it; the tail-removal test falsified that and the recommendation
is reversed. A year-constant regressor cannot explain more than the between-year share of a monthly
series, so a low monthly r² was never evidence about the year-level tilt.)*

**RE-TEST CONDITION (matrix cell → `R`): pair the de-leak with a mechanism that restores the scarcity
tail (#1344) and re-screen.** A real pairing, not a formality — the headline C3a is a difference of
two large errors of opposite sign, and this arm moves the **ordinary-hour level the right way**,
charged only because the tail is absent.

**PROMOTION QUESTION PUT TO THE OWNER (rule 31 `[R-RETAIN]`, pre-committed in PRECOMMIT §8).** The
bundle is **pushed and retrievable** — `git checkout 451fa7f32ffacacbc85083aa30873842d06a19de --
results/calibration/nyiso232_arm_y2022` — so a "yes" costs **zero** re-solves for 2022 and ~25 min
for the remaining three years.

Records: `docs/RESULT-nyiso232-st-gas-deleak-screen-2026-09-13.md`,
`docs/FINDING-nyiso232-c3a-is-two-objects-2026-09-13.md`,
`results/calibration/PRECOMMIT-nyiso232-st-gas-deleak.md`,
`scripts/probes/_nyiso232_{st_gas_phase0,screen_gates,c3a_two_objects}.py`.
One shard (5m23s solve), archived after fetch + checkout + signature verification; its branch is
**kept** because it carries a bundle a promotion would register (rule 33(f)(3)).

---

### nyiso-232 CODA — OWNER RULED "ARM IT"; KEEPER PROMOTED TO `2026-09-13-nyiso-232-st-gas`

**KEEPER: `2026-09-13-nyiso-232-st-gas`** (bundle `results/calibration/nyiso232_deleak_span`),
superseding `2026-09-13-nyiso231-anchor-span`, **pruned in this session** (rule 35 `[R-PROMOTE]` (a),
`--force-uncite` per 35(d)). All four registered years 2022–2025 in ONE `--years` invocation and ONE
bundle. Year union enumerated **before** the prune (35(b)) = `{2022,2023,2024,2025}`, covered
exactly. `audit_keepers --iso NYISO` post-prune: **PASS, 0 failures**. C6 **PASSES**.

**The gate was NOT re-cut.** The rule-29 screen STOPPED this arm on C3a-2022 and the PRECOMMIT put
the promotion question to the owner, who ruled **"Arm it"**. A screen can kill an arm and never
promote one; it did not promote this one — the **owner** did, on the evidence the screen produced.

**ONE REGISTERED FIELD MOVES:** `nyiso_st_gas_econ_bands_deleaked` False → True. Zero free
parameters, zero new literals, `authorized_price_tuning` NONE. Two band multipliers **do** move and
the attestation states that in full rather than denying it — it is not the rules 1/13 carve-out,
which governs a band **identified by the price residual**, and this one moves price **down** in all
four years.

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **C3a** | −9.86 → **−11.61 %** (PASS→**FAIL**) | +0.59 → −1.26 | +1.05 → **−0.75** | −5.95 → **−7.99** (PASS) |
| **C1 ST_GAS** vs actual | −1.148 → **−0.477** TWh | +1.989 → **+3.326** ← the pre-registered exception | −1.064 → **−0.462** | −4.677 → **−4.006** |
| **C8** ST_GAS forced | 23.1 → **33.6 % FAIL** | 16.5 → **34.3 % FAIL** | 21.4 → **36.6 % FAIL** | 19.0 → 28.5 % pass |
| C8 on a **stable** vote | **20.8 %** | **14.8 %** | **20.6 %** | **18.1 %** — all pass, all **below** the incumbent |

**DETERMINATION: registered full span NOT-YET; ISO tier (2023–2025, rule 30(c)) NOT-YET — a
DOWNGRADE from CALIBRATED.** **Every load-bearing criterion PASSES** (C1/C2/C3a/C3b/C4/C6). The
downgrade is **C8 alone**, and C8 failing is *also* what strips C3c of lone-failure status under
rule 22 guard (a), reverting it from a ledgered caveat to a FAIL. Remove C8 and **both** resolve.

**C8's failure is a SHARED-SCORER ARTIFACT, proved not asserted**
(`docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md`): D-2 labels a plant by its most
common unit group counted in **LP ROWS**, so this mechanism's declared smoothing-ladder collapse
(ST_GAS 88 → 44 rows) flips **Ravenswood (2500) on an 8–7 margin** and 2511 on a 4–4 tie. The
numerator moves within ±2 %; the denominator collapses 33–52 %; every dispatch-side measure of
ST_GAS **rises**. D-4 provenance failures are pre-existing (9 rows on both legs). **Reported at full
magnitude and NOT re-scored**, and the one-line fix is **not** landed here — the census shows
SPP/SOCO is the most exposed ISO (23–25 flippable plants) and rule 25 forbids a NYISO lane deciding
that.

**PRE-REGISTRATION HELD.** Addendum A, written before the span solved, predicted C3a-2022 ≈ −11.6 %
(landed −11.61), the at-risk 2025 "near −7 to −8 %" (landed **−7.99**, PASS), 2023/2024 toward zero
(both did), and named **2023 ST_GAS as the C1 exception that would get worse** (it did).

**AGAINST THE ARM, not buried:** C3b-2022 worsens 0.209 → 0.218; CT_PEAKER worsens in **all four
years** (well inside band); C1-2022 CC_REGULAR still fails (+5.20 → +5.07 TWh).

**OPEN QUESTION FOR THE OWNER** (RESULT §11.5): the ruling answered a question framed on C3a-2022,
not on NYISO's headline moving to NOT-YET on a scorer defect. Either leave it documented, or
authorise the D-2 capacity-weighted vote as a **cross-ISO** change measured on SPP/SOCO/CAISO first.

Records: `docs/RESULT-nyiso232-st-gas-deleak-screen-2026-09-13.md` §11,
`results/calibration/PRECOMMIT-nyiso232-st-gas-deleak.md` Addendum A,
`scripts/gen_nyiso232_attestation.py` (six computed checks, aborts on a false premise).
Span shard archived after fetch + checkout + signature verification; bundle retrievable at
`git checkout fc545728636b40d402f5fcba4cae4f6edc42c19e -- results/calibration/nyiso232_deleak_span`.

---

## nyiso-233 — 2026-09-13

**KEEPER UNCHANGED: `2026-09-13-nyiso-232-st-gas`. NO SOLVE, NO RE-KEY, NO CONFIG FIELD, NO OFFER
CURVE — and NYISO's ISO tier goes NOT-YET → CALIBRATED**, because the SCORER changed. Session
nyiso-232 proved a shared-scorer defect and was not authorized to fix it; this session measured it
across every ISO and LANDED the repair on the **owner's explicit ruling** (a shared scorer reaches
every ISO column, which rule 25 `[R-ISO-SCOPE]` forbids a NYISO lane deciding alone), with the
owner's disposition that a verdict change elsewhere is a **CORRECTION, not a regression**.

**THE REPAIR.** `legitimacy_diagnostics.aggregate_floors_by_plant` labelled each plant by its most
common non-empty unit group counted in **LP ROWS**. Row count is a property of the **offer curve's
band structure**, not of the plant. The vote is now weighted by **capacity (`pmax`)**: bands
partition a class's capacity however many of them there are, so the vote is band-invariant *by
construction*, and `pmax` depends on no dispatch outcome, so a plant's class denominator is a
property of the plant rather than of the solve. **Energy weighting was considered and REJECTED** —
also band-invariant and it would have needed no fleet rebuild, but arm and control would legitimately
label a plant differently whenever dispatch moved. **Zero free parameters, zero new literals.**

**THE CASE THAT NAMES IT.** Ravenswood (plant 2500), identical in all four years: **1724.8 MW
`ST_GAS` vs 268.5 MW `CC_REGULAR` — 6.4:1** — yet its rows read 4 vs 7, so an 87 %-steam site was
labelled `CC_REGULAR`. Plant 2517 is the same at 4.7:1 on a 4–4 row tie broken alphabetically. The
cleanest statement is SPP plant 165, where the classes are within 2 MW and the vote is decided
**entirely by `COAL` carrying a `mustrun` band that `CC_REGULAR` does not**.

**MEASURED — a controlled A/B, identical inputs, only the weight differs. 10 bundle-years, 3 ISOs,
11,328 floor rows.** Harness validated first: the refactored accumulator reproduces the superseded
row-count labels **bit-for-bit on all 10 bundle-years** with no `pmax` (0 label diffs), and the
control arm reproduces the **committed** `legitimacy_diagnostics.json` on **all D-2 numerics, 0 diffs
across 17 rows**.

| ISO | mixed | flips | D-2 gate | verdict changes |
|---|---:|---:|---|---|
| **NYISO** (the keeper) | 7 | **6**, every year | **FAIL → PASS** | **3** — `ST_GAS` 2022/2023/2024 |
| **CAISO** | 1 | 0 | PASS → PASS | **0** — byte-identical on every row |
| **SPP** | 23–25 | 5–6 | PASS → PASS | **0** |

**EVERY NUMERATOR IS BIT-IDENTICAL to 4 dp in all 20 rows, in every ISO.** Only the denominator moves:
NYISO `ST_GAS` 5.7046 → 9.2318, 5.8134 → 13.4962, 6.4861 → 11.5421, 7.7309 → 12.1256 TWh, so the
forced share reads **20.78 / 14.79 / 20.59 / 18.15 %** against the 30 % cap instead of
33.63 / 34.33 / 36.64 / 28.46 %. That independently reproduces nyiso-232's predicted
20.8 / 14.8 / 20.6 / 18.1 to the second decimal, and all four sit **below** the superseded
nyiso-231 keeper's 23.1 / 16.5 / 21.4 / 19.0 — which is what physics demands, since the same floors
are a smaller share of a class that now runs more. **The pass is NOT vacuous**: `ST_GAS` is material
on both arms (load share 11.2–13.1 % before, 15.9–18.8 % after, floor 2 %).

**SPP is NOT INERT, just not verdict-changing** — its denominators move (`COAL` 68.83 → 72.44 TWh in
2023) and the distinction is not blurred. **A CORRECTION TO nyiso-232's OWN FRAMING, recorded rather
than dropped:** its census called 23–25 SPP plants "flippable", meaning a hypothetical halving of the
winner's row count would lose it the vote. Under the actual capacity repair only **5–6** flip.
"Flippable" measured fragility to an arbitrary band change and was never a prediction of this repair.

**All four pre-registered stop conditions cleared**: S1 0 zero-capacity plants, S2 0 labels lost to
`''`, S3 11,328/11,328 rows backfilled, S4 blast radius confined to D-2/D-4 (one non-test call site,
no price / dispatch / determination path but C8).

**DETERMINATION. ISO tier (2023–2025, rule 30(c)): CALIBRATED** — C1/C2/C3a/C3b/C4/C6/C8 PASS, C3c the
lone failing criterion and therefore a ledgered caveat under rule 22 `[R-C3C]`, non-downgrading since
rubric v3.3. C8 failing was *also* what stripped C3c of lone-failure status, so both resolved
together exactly as nyiso-232 predicted. Per-year: 2022 NOT-YET, 2023 CALIBRATED, 2024 CALIBRATED,
2025 CALIBRATED-WITH-CAVEATS. **The four-year bundle still reads NOT-YET** on 2022's C3a −11.6 %
(pre-registered as the accepted cost of the nyiso-232 arming), C1 CC_REGULAR +5.07 TWh / +3.8 pp and
C3b 0.218 — reported, not absorbed. D-4's provenance failures are **pre-existing and unchanged by the
repair: 9 unit-conduct rows, IDENTICAL failure set on both vote bases.**

**ERCOT / PJM / MISO / NEISO carry no committed `floors/*.npz`** (checked on `main` and all four live
`claude/soco-15-*` branches) and are **UNMEASURED, not shown to be clean**. Each re-scores on the
capacity basis the next time its lane regenerates diagnostics, through the same backfill; the new
per-year `plant_class_vote_basis` field of `legitimacy_diagnostics.json` records which basis a run
actually got, so a row-count fallback can never again be silent.

**OBJECT A — NYISO's price tail is an AVAILABILITY object, not a price-formation one.** In the top
1 % of hours by **ACTUAL** RT price the model carries **3,390–6,247 MW of idle thermal capacity
(16.3–29.6 %), slack EXACTLY 0.00, and near-zero reserve shortfall** while the real market cleared at
$573 (2022) and $446 (2025). Robust across depth (0.5 / 1 / 2 / 5 %, slack 0.00 in all 16 cells;
tightest case 2025's top 0.5 % still 2,414 MW idle). **And the stack is not the limit** — max thermal
`mc` is $1,229 (2022) / $1,890 (2025), and **83–96 % of the idle capacity is offered at or below the
price the real market actually paid**. So the model is **not mispricing scarcity, it is not
experiencing scarcity**, and a steeper ORDC/RCPF curve would price nothing because nothing binds. The
events are both winter (2022 Dec 23–24 Elliott; 2023 Feb 3–4; 2024 Dec 21–23) and summer (2025
Jun 23–25 heat dome; 2023 Sep 5–6), so no single-season story covers them.
**Rule 28(a) honoured: nothing re-opened.** `temp_dependent_derate` sits at **G** (nyiso-111, ex-ante
refusal, no solve); `gas_coldsnap_derate` / `winter_fuelsec_posture` / `correlated_forced_outage` /
`ordc_scarcity_overlay` all sit at `.`; `nyiso_iroquois_winter_spread` was tested and rejected
(nyiso-150); `dual_fuel_switching` closed (nyiso-179). The disciplined claim is that §2–§3 is **new
evidence that did not exist when the G cell was refused ex-ante**, and that refusal should be
**re-read against it** — the owner's call, and a separate session's work.

**ALSO DISCHARGED: a rule-28 duty nyiso-232 left undone** — the NYISO matrix shard still named
`2026-09-13-nyiso231-anchor-span` as keeper. Re-stamped to `2026-09-13-nyiso-232-st-gas` with the
current open gates. **No mechanism cell moves** on account of the scorer repair: no `ScenarioConfig`
field was added or changed, no solve path touched, and it cannot move a price.

**HANDED FORWARD, NOT ACTED ON:** Object B, the ~10.1–10.8 pp gas-monotone C3a tilt that survives tail
removal (r vs gas −0.92 to −0.99); 2022's C1/C3a/C3b; and CT_PEAKER's consistent drift away from
actual in all four years, whose matrix partner `nyiso_gas_bridge_startup_aware` is now armed on the
keeper, so `ct_peaker_bands_measured`'s re-test condition is closer than its `R` cell reads.

Records: `docs/FINDING-nyiso233-d2-capacity-weighted-vote-2026-09-13.md`,
`docs/FINDING-nyiso233-tail-is-an-availability-object-2026-09-13.md`,
`results/calibration/PRECOMMIT-nyiso233-d2-capacity-weighted-vote.md`,
`scripts/probes/_nyiso233_{d2_capacity_vote_measure,tail_mechanism_census}.py`.
**ZERO LP this session** (rule 32 `[R-SHARD]` (a)): no shard was launched and none was needed.

## 2026-09-14 — nyiso-234: the availability family is closed by ARITHMETIC; the tail sits on gas the model never observed

**ZERO LP. Nothing armed, no cell promoted, keeper UNCHANGED at
`2026-09-13-nyiso-232-st-gas`. No shard launched — there is nothing to solve until an
intake lands.** Records: `docs/FINDING-nyiso234-tail-gas-is-unobserved-2026-09-14.md`,
`docs/DECISION-CARD-nyiso234-tail-gas-coverage-2026-09-14.md`. Probes
`scripts/probes/_nyiso234_tail_season_reach.py` and `_nyiso234_gas_coverage_tail.py`
(argument = tail depth %).

**1 — the `temp_dependent_derate` G cell was re-read on the handoff's instruction and HELD AT
`G`, on two independent legs.** (a) *Identification, nyiso-111's own basis, undefeated*: it
refused because NYISO's CAMPD conduct cannot MEASURE an ambient slope (2 of 15 plants identify;
sign inverts at −0.00745/°C; the near-pinned plant shows no response, r = 0.006; phase
validation fails at lag −5 h). nyiso-233 measured a **residual**, which is motive, not an
instrument — and nyiso-111's own re-open condition (a DMNC record or a plant pinned at
capability) is **unmet**. (b) *A new reach bar no slope can rescue*: the committed curve is
**identically 1.0 in cold hours** (hinge form flat at/below `temp_derate_ref_c = 15.0 °C`;
mean-anchored form clipped by `np.clip`), so it cannot touch **79.8 / 49.4 / 38.4 / 15.8 %** of
the 2022–2025 tail gap at any slope — stable across depth, and **worst (77–86 %) in 2022, the
only year failing C3a**. The object is both-seasons (DJF 76.2 / 46.0 / 36.1 / 15.3 % of the
gap); a hot-weather-only instrument cannot cover it.

**2 — and the `.` neighbours are not a route around it: the whole availability family is closed
on ARITHMETIC.** Putting nyiso-227 beside nyiso-233 for the first time — NYISO's **entire**
measured sub-5-day gas outage family peaks at **1,653–2,351 MW** against **3,390–6,247 MW** of
idle thermal in the tail hours (2–3× too small, and it must eat that headroom *before* removing
one MW the model uses; nyiso-227 measured ST_GAS binding hours at 0/0/0 of 8,760 and put the
shortfall at ~20×). The ≥5-day extract cannot fill it either: `min(duration_days) = 5.000`,
**zero of 3,717 windows shorter**, and every event nyiso-233 named (Elliott Dec 23–24 2022,
Feb 3–4 2023, Dec 21–23 2024, Jun 23–25 2025) is **shorter than that minimum detectable
window**. nyiso-233's §5 pointer at availability is right about the *kind* of object and does
**not** survive as a lever recommendation.

**3 — that forces the fork nyiso-233 §6 flagged and declined to test, and it measures as an
INPUT defect.** **69.8 / 29.0 / 66.8 / 15.8 %** of each year's tail gap falls on calendar dates
for which `data/raw/gas-prices/transco_z6_ny_daily.csv` **has no row at all** (stable across
tail depth). The model burns **$8.05/MMBtu — its own annual median — flat for eleven days,
Dec 21–31 2022**, straight through Elliott, whose **Dec 24 (33.8 %) + Dec 23 (13.9 %)** carry
47.7 % of that year's tail gap between them. The holes are systematic (a **14–15 day
Christmas–New Year hole every year**, 7-day Thanksgiving holes, multi-day summer holes) and they
track which events the calendar hid — 2024's Dec 21–23 sit inside the December hole (66.8 %),
2025's covered Jun 23–25 give the lowest year (15.8 %). **No committed source can cross-check
it**: `transco_z6_iroquois_monthly.csv` is *not* independent (its Dec-2022 value **7.3200** is
exactly the mean of the 15 surviving dailies) and `algonquin_citygate_daily.csv` has the **same
hole** (last print $6.51 on Dec 21). The repair is a **data intake**, carded to the owner, not a
mechanism this lane may arm; **magnitude deliberately NOT estimated** (rule 5 `[R-NO-MAGIC]`) —
the intake must land before the effect can be measured.

The candidate has the property nyiso-232 proved a tail lever must have: because the hub overlay
**supersedes** the monthly level in covered months, a repair raises the **tail** and leaves
ordinary hours alone — structurally, not by tuning. (A tidier story in which the monthly anchor
also explained the ordinary-hour over-pricing was hypothesised and is **false**; the code
contradicts it and it was dropped rather than told.) It is bounded by machinery already armed:
`dual_fuel_switching` caps downstate units at oil parity *after* the overlay.

**4 — the handoff's 2022 budget question, answered: no, and on rule 14 rather than cost.**
69.8 % of 2022's tail gap sits on dates the gas input does not observe, so spending a solve on an
offer-curve or availability lever for 2022 now would tune a mechanism to compensate for a
known-missing input — *"do not bury the error back inside an inaccurate input"* (rule 14
`[R-ACCURATE]`). The correct order is: land the input, then re-screen under rule 29.

Cells moved: none. `temp_dependent_derate` **re-stamped at `G`** with the new reach bar
(rule 28(b)). Class-E parity remains RED for `caiso279_ablate_dswcouple_span` and
`soco15_spp_arm` — both pre-existing, both tracked on main, **neither NYISO's** (rule 25);
reported, not touched. NYISO's leg is clean.

**Addendum (same session) — the repair is bounded, and the bound is MEASURED.** Through the repo's
own `dual_fuel_oil_price_series`, the model's delivered **oil parity on Dec 23–24 2022 is
$24.85/MMBtu** against the **$8.05** gas fill — **3.1×**. The model burns $8.05 there only because
`min(8.05, 24.85) = 8.05`; at any observed gas above $24.85 the downstate dual-fuel fleet flips to
oil at parity, a hard ceiling already armed that needs no new parameter. Stated as a bound, not a
prediction (the non-dual-fuel fleet has no such cap; no $/MWh figure is derived from it). And the
gap is a **source property, not an unavoidable fact about holidays**: the model's other fuel series
`ny_harbor_ulsd_daily.csv` **does** print Dec 22 ($3.132/gal) and **Dec 23 ($3.246/gal)** — ULSD is
NYMEX-traded and quotes through the holiday week; the physical gas index does not.

**Suite:** `tests/scoring` 18 failed / 1,524 passed (`-p no:randomly`). The failure SET is a strict
**subset** of the handoff's 19-failure baseline — `test_backcast_artifacts` now **passes 15/15**
(verified in isolation, not a collection error); no new failures, none NYISO's, none from this
session's changes. `check_mechanism_matrix.py --base origin/main` passes every gate (integrity,
anchors, keeper stamps, §5.x headers, all three ratchets).

**Addendum 2 (same session) — the standing undone item is CLOSED: `audit_keepers` E14,
solve-environment pin currency.** The handoff carried it as *"STILL UNDONE and it would have caught
the off-pin keeper: a check in audit_keepers.py that each designated keeper's recorded
`environment.packages` matches requirements.txt. Nine lines."* Landed as **E14** with two pure,
unit-testable helpers (`_requirements_pins`, `solve_pin_findings`) and 8 tests
(`tests/scoring/test_audit_keepers_solve_pin.py`). Nothing else in the audit read the
`environment` block at all — E1 checks the keeper's three stores exist, E11 diffs the *recipe*;
neither can see the environment the recipe was solved in, which is how `nyiso-231` reached the
dashboard off-pin.

**Severity is WARN, never FAIL, and deliberately so** (rule 25 `[R-ISO-SCOPE]`): an off-pin keeper
is a provenance fact to surface, not grounds to retroactively invalidate a committed result whose
numbers are already on the site — and a pin bump is a repo-wide event that would otherwise red six
lanes that did nothing wrong. Promotable to FAIL on an owner ruling if a re-solve-on-drift policy is
ever adopted. A package the repo does not pin, and a bundle predating the `environment` block, come
back **unverifiable** rather than silently passing.

**Measured green on all SEVEN designated keepers** (CAISO / ERCOT / MISO / NEISO / NYISO / PJM /
SPP all ON-PIN), so it lands as a no-op guard. Verified it changes nothing else: `audit_keepers`
reports **"FAIL: 1 failure(s), 4 warning(s)" both with and without the change** — the MISO E3
metadata warning, the three stale `status/` parts (ERCOT/CAISO/NEISO, S1) and NYISO's own
pre-existing E11 baseline gap are all untouched and **none are this session's** (rule 25; reported,
not touched). `audit_keepers --iso NYISO` passes **0 failures**. The audit test family is 59 passed
/ 1 failed, that one being `test_e11_set_mirrors_replay_ignore` — a named member of the handoff's
19-failure baseline and unrelated to E14.

## nyiso-235 — 2026-09-14

**THE RULE-29 `[R-SCREEN]` SCREEN OF THE REPAIRED DELIVERED-GAS SERIES CLEARS (G-1…G-5), AND THE
FULL SPAN IS SOLVED. KEEPER UNCHANGED — PROMOTION IS THE OWNER'S CALL AND IS OPEN.**
Full record: `docs/RESULT-nyiso235-gas-repair-screen-2026-09-14.md`. Pre-registration:
`docs/PRECOMMIT-nyiso234-gas-repair-screen-2026-09-14.md` +
`docs/PRECOMMIT-nyiso235-gas-repair-screen-ADDENDUM-2026-09-14.md`, both pushed before any solve.

**What was tested: an INPUT, not a mechanism.** Zero `ScenarioConfig` fields moved, no flag armed,
DOF ledger untouched, `authorized_price_tuning` NONE. The arm is the keeper's frozen recipe replayed
byte-faithfully (`replay_keeper.py`) with the nyiso-234b repaired gas series as the only difference.
Its `run_config` differs from the keeper's in exactly two fields, **both propagation not choice**:
`committed_band_measured_basis` `None`→`False` (the PJM Route-A field materializing at its default —
same posture, frozen cache-key drop value `"False"`), and `gas_offer_margin_anchor_by_zone`, whose
delta **equals the signed annual-mean change in delivered gas to 1e-15** and which `meta.json`
carries only as the boolean `gas_offer_margin_zonal_anchor: True` — i.e. derived at solve time.

**G-DRIFT had to be re-run and the answer was not free.** The parent PRECOMMIT's "zero LIVE hunks"
was measured at nyiso-234's head; this session's head carries **37 changed solve-path files,
+2,144/−58** (NWPP onboarding, PJM Route-A, CAISO intake). Verdict survives on measurement: every
hunk classified INERT; the deletion census finds only the `ba_codes` refactor, docstrings and sets
keeping NYISO's membership; `ba_codes("NYISO")==("NYIS",)` so `.isin` selects what `==` did; the new
NERC gate keys `{"NWPP":"WECC"}` only; the new eGRID HR repair plant **7350 is PGE/Oregon**, not
among NYISO's 1,088. Confirmed by `moved_rows("NYISO")=0` and the keeper's own recorded
`solve_surface.fingerprint bd2b4657f9b5df7e` **reproducing byte-identically at HEAD**. Form 4 valid,
**no control solve spent**.

**The gates.** G-1 decided PRE-SOLVE on the delivered gas array: it moves 1,464 h across a
contiguous 61-day run (2022-11-01…12-31, the mean-preserving monthly renormalization) and **0 hours
outside the two months the repaired inputs touch** — 10 daily dates plus basis rows 2022-11
`0.7490→1.3122`, 2022-12 `3.5705→5.5376`. G-2 Dec 22–23 load-weighted price **69.20→169.86
(+100.67 $/MWh)**. G-3 inside the band pre-registered before the arm solved (207.38…410.36); max
single zone-hour **+193.17**. G-4 **slack and dump exactly 0.000000 in all four years, both arms**.
G-5 passes the Δmc review its own text requires: oil **+76.7 %** is **99.71 %** confined to the
**72 hours** where repaired gas crosses the measured $24.85 oil-parity cap (**the control had ZERO
such hours**), substitutes one-for-one against the gas family (**+0.4848 vs −0.4825 TWh**) and rises
in **72 of 72**. `dual_fuel_oil_daily_parity` was already armed on the keeper — the repair merely
pushed gas past parity for the first time, a possibility the ADDENDUM named in advance.
Rule 25 re-verified on the shared basis file: **30 of 940 rows moved, every one NYISO**.

**THE SPAN RESULT IS MIXED ON PRICE AND NO BAND VERDICT FLIPS.** C3a: 2022 −11.60→**−10.51 %**
(FAIL→FAIL), 2023 −1.26→−1.76, 2024 −0.74→**−0.13**, 2025 −7.98→**−9.19 %** (all PASS→PASS).
C3b 0.2175→**0.1990**, 0.1221→0.1233, 0.1788→**0.1619**, 0.1619→0.1670. The PRECOMMIT pre-registered
that C3a might get WORSE and that this would not justify reverting; 2022 got BETTER, and the
symmetric discipline binds — **a better C3a is not grounds to promote, and none of these is a gate.**

**The mixed direction is explained, and it is NOT the tail repair.** C3a tracks the **sign of the
annual-mean gas change in 4 of 4 years** (2022 **+0.2134** UP→better, 2023 **−0.0195** DOWN→worse,
2024 **+0.0251** UP→better, 2025 **−0.0975** DOWN→worse). The model is under-priced every year, so a
higher anchor moves prices toward actual. **The annual C3a number is dominated by a LEVEL effect
transmitted through the annual-mean anchor, not by the tail hours the repair was about.**

**OPEN STRUCTURAL FINDING, SURFACED AND DELIBERATELY NOT ACTED ON.**
`gas_offer_margin_anchor_by_zone` is anchored to the **annual mean** delivered gas, so a 61-day
winter repair shifts gas offers — and prices — in **all twelve months**, including the ~7,300 hours
where the gas array itself did not move: Jan–Oct signed mean price delta **+0.21762 $/MWh**, **ratio
to the anchor delta 1.020**, near-uniform by month, with **17.3 %** of hours exactly unchanged (the
non-gas-marginal ones). This does **not** fail G-1, which is written over the gas array in $/MMBtu,
and it is **not introduced by this repair** — it is a standing property the repair made visible.
Whether an offer anchor with annual reach is right when the driver is seasonal is the question
handed forward. Containing it here would have been a compensating tune.

**Physical fidelity moves toward measured and never away.** Oil error 2022 −1.212→**−0.727**, 2025
+0.224→**+0.143**, 2023/2024 unchanged — exactly the footprint pattern. Gas family 2022
+5.155→**+4.673**. CC_REGULAR 2022 +5.494→**+5.178**.

**No legitimacy regression:** D-4's failing set is **identical** in control and arm (9 rows across
the span, same floors and plants), and D1/D2/D5/D9/D10 pass in both. The shards' "legitimacy FAIL"
lines report the keeper's standing state, not a finding about the arm.

**RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e)) — a promotion costs ZERO re-solves.**
Span: commit **`99f7015445fc0e271b4cd197227bdf34fd5dd38e`** (branch `claude/nyiso-235-span`), 47
files incl. `dispatch/{2022,2023,2024,2025}_P1.parquet` and root `system.parquet`; recover with
`git archive 99f7015445fc0e271b4cd197227bdf34fd5dd38e results/calibration/nyiso235_gasrepair_span | tar -x`.
Screen (2022): commit **`750e4a72421e4548a5d82b71ccf13e6254cc3b87`**, 17 files.
Both bundles are **gitignored, kept on local disk** under rule 31 `[R-RETAIN]` — not deleted,
because the owner has not ruled on promotion.

**A defect this session made and fixed:** commit `3bfb1cd7` swept the 17 screen-bundle files onto
the branch, because `git checkout <shard sha> -- <bundle>` **stages** what it checks out and the
RESULT commit picked up that index. An unregistered bundle dir on `main` is the Class-E parity RED
rule 29(c) exists to prevent. Untracked with `git rm -r --cached` (bytes kept on disk per rule 31),
both bundle paths added to `.gitignore`. **Caught before it reached `main` — `origin/main` carried 0
of those files.** The span bundle was then extracted with `git archive | tar -x`, which never
touches the index.

**FLAG TO THE OWNER — NEISO, and worse than the handoff described** (rule 25: NEISO's lane, measured
read-only here only to make the flag concrete). `algonquin_citygate_daily.csv` carries the identical
Elliott hole — last print **2022-12-21 $6.51**, next **2023-01-04** — **and is not a daily series at
all**: its own `source` column reads `wednesday`/`last_wednesday`, with **37 gaps longer than 7
days** across 2018–2025.

**STILL OPEN:** Object B (the gas-monotone tilt) is **not** re-measured — the committed
`tail/actual_tail.json` carries only tail hour counts, not the hourly series, so it cannot
reconstruct the actual's non-tail mean; the re-measurement needs the raw NYISO RT LMP series
tail-stripped on the same threshold on both sides. No Object B number is claimed here.

### nyiso-235 PROMOTION — 2026-09-16

**THE OWNER RULED: PROMOTE.** NYISO keeper → **`2026-09-14-nyiso-235-gas-repair`** (bundle
`results/calibration/nyiso235_gasrepair_span`), superseding `2026-09-13-nyiso-232-st-gas`. The ruling
answered the rule 31 `[R-RETAIN]` promotion question this session put after the screen cleared; **the
screen did not promote this arm — a screen may kill an arm and never promote one — the owner did.**

**Rule 35 `[R-PROMOTE]` executed in its required order.** (b) The year union was enumerated from the
registry **before** anything was pruned — `{2022, 2023, 2024, 2025}`, one registered run — and (c)
this bundle covers it **exactly**, so no stamped companion is needed. (e) The incoming keeper was
registered and **verified** (`audit_keepers --iso NYISO`) **before** the outgoing one was deleted.
(a,d) The superseded keeper's three stores were then pruned with
`prune_iso_runs.py --iso NYISO --force-uncite` — the intended route, since the guard blocks on the
governance citations that rule 35(d) says must **stay** as history.

**Final state: `audit_keepers --iso NYISO` PASS, 0 failures**, one warning, the pre-existing E11
lineage gap (the `nyiso-231` bundle was pruned by an earlier session, so the recipe diff has no
baseline). Registry/payload parity carries **no NYISO entry**; the two reds that remain
(`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) are pre-existing and another lane's (rule 25).

**THE DETERMINATION DID NOT MOVE — this promotion buys fidelity, not a grade.** The registered
four-year run still reads **NOT-YET on 2022 alone**, and the ISO tier (2023–2025, rule 30(c)) still
reads **CALIBRATED with C3c the lone ledgered caveat**. What did improve is the span's failing set,
which **shrinks** from `{fuelmix, price_mean, price_shape, price_tail}` to
`{fuelmix, price_mean, price_tail}` — C3b drops out. **No C3a or C3b band verdict flips in either
direction.**

**Attestation.** `calibration_attestation.json` was authored for the new bundle with the DOF ledger
**carried over byte-identical** (sha256 `926e744b…` on both), because the recipe is byte-identical;
`authorized_price_tuning` is **NONE**. The attestation records the rule-14 basis, the re-run G-DRIFT,
the rule-25 verification, and the open anchor finding, and states plainly that the C3a improvement
was **not** treated as promotion evidence.

**Sidecar.** Carries a `market_story` (rule 15 / skill step 4) telling the oil story: downstate gas at
$32–36/MMBtu above the $24.85 oil-parity price sent NYC and Long Island dual-fuel units to oil during
Elliott, which is what they actually did and why 2022's oil burn is three times a normal year's — a
story the model could not tell while its gas series carried $8.05 flat through the storm. Its
`definition` leads with the **run-level** verdict (NOT-YET), with the tier stated separately; leading
with the tier tripped `audit_keepers` E5, correctly.

**Housekeeping.** The 2022 **screen** bundle was removed from local disk under rule 31 trigger (i) —
the owner has now ruled — with every cited number already in the RESULT doc and the bytes recoverable
at the immutable shard sha `750e4a72421e4548a5d82b71ccf13e6254cc3b87`. The branch was rebased onto
`origin/main` (38 commits) at the owner's instruction and force-pushed; the rebase was clean and the
promotion state was re-verified after it.

**Still open, unchanged by the promotion:** the `gas_offer_margin_anchor_by_zone` annual-mean reach
(§6 of the RESULT), and Object B, which is still not re-measured.

## nyiso-236 — 2026-09-16

**ZERO LP.** Orchestrator-only (rule 32 `[R-SHARD]` (a)). The keeper
`2026-09-14-nyiso-235-gas-repair` is **unchanged**; no `ScenarioConfig` field moved, so no mechanism
cell moves (rule 28 `[R-MECH-MATRIX]` (b)) and no run was registered. Record:
`docs/FINDING-nyiso236-the-anchor-grain-and-the-gas-slope-2026-09-16.md`; probes
`scripts/probes/nyiso236_anchor_grain_phase0.py` and `nyiso236_gas_slope_phase0.py`.

**G-DRIFT re-run at this head** (`edd40943` vs the keeper's solve sha `2ebc58df`): `moved_rows("NYISO")`
is `{}` and `surface_stamp("NYISO").fingerprint` reproduces the keeper's recorded `bd2b4657f9b5df7e`.
The diff moves **35 solve-path files, +2,500/−19**, and every hunk classifies **INERT** — SOCO
registration and NWPP onboarding, with the single NYISO-executed edit (`_eia860_ba_zones`)
behaviour-identical for a non-SOCO ISO. **Rule 29(b) form 4 valid; no control solve spent or owed.**

**Object C — the annual-mean offer anchor. REAL, AND STOPPED AT PHASE 0 ON IDENTIFICATION.** Located
to `data/fuel/zonal_anchor.py:145` (`np.nanmean` over 8,760 h, resolved per `(zone, solve-year)` because
the keeper carries `gas_offer_margin_zonal_anchor_vintage`). The defect is confirmed and is larger than
the one nyiso-230 closed: the **within-year** delivered-gas spread is 6.51 / 2.48 / 3.89 / 10.86 $/MMBtu
against a **between-year** spread of 5.83. It is nonetheless **not screened**, and the stop is structural
rather than residual-driven: the anchor's grain is the mechanism's own claim about markup
fuel-elasticity, not a measurement detail; the extrapolation argument that justified the year index has a
limit (`anchor = fuel(t)`) that restores the multiplicative form **rejected on measured evidence** by
neiso-45/46/47; the year index is *forced* by rule 13's forward test while month/quarter/season are not;
the markup `(mult − phys)` is a **fitted** quantity so its fuel-elasticity is unidentified by
construction; and NYISO publishes no 60-Day-DAM equivalent and has no offer corpus, so a grain could be
chosen **only** against the gates — rule 1 `[R-STRUCT]` condition (c). Disposition `G`, not `R`.
**Re-open condition:** a published NYISO unit-level energy-offer book, or any measured NYISO conduct
series identifying the markup's fuel-elasticity directly.
*(ANNOTATED 2026-09-20, nyiso-243 — "has no offer corpus" is now **false**: NYISO MIS P-27 masked
generator bid data is intaken at `data/raw/nyiso-bid-data` (2022-2025). **The `G` STANDS**, because
this re-open condition asks for a **unit-level** book and P-27 is masked — no unit, class, fuel or
zone — so it cannot identify a per-class markup's fuel-elasticity. "NYISO publishes no 60-Day-DAM
equivalent" also stands as written: what NYISO withholds is the *unit identity*, not the offer data,
which is why the nyiso-87 gas-bridge CAMPD reconstruction is untouched. The cell that DOES re-open on
this corpus is `measured_offer_surface` (`G` -> `U`), which needs a distribution rather than a unit:
`docs/RESULT-nyiso243-the-tail-is-not-an-availability-object-2026-09-20.md`.)*

**Object B — RE-MEASURED CORRECTLY FOR THE FIRST TIME.** nyiso-235's dead end was a wrong-file problem:
the actual hourly RT LMP series is committed at
`data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` (2018–2026, 8,760 h/yr), already read by
`derive_actual_amplitude.py`. Stripping the top 1 % **by actual price from both sides** leaves a
**9.50 pp** bias spread (2022 −3.57 / 2023 +5.93 / 2024 +5.85 / 2025 −2.18 %), and it resolves into
**two numbers**: over 48 month-points the actual's non-tail price is `7.481 × gas + 11.05` and the
model's is `6.432 × gas + 16.29` — a **slope 14.0 % too shallow** and an **intercept 47.4 % too high**,
crossing at **$5.00/MMBtu**, with bootstrap 95 % CIs `[−1.506, −0.500]` and `[+3.18, +6.91]` both
excluding zero. The annual-resolution fit agrees (6.708 vs 7.550, crossover $5.02). The model side of
every year reproduces the scorer exactly; only the actual's weighting basis differs (0.03–0.9 %).

**Object B is NOT Object C, measured pre-solve.** A month-grain anchor changes the load-weighted annual
price by `markup_hr × (gas_load_weighted − gas_annual)` = +0.290 / +0.003 / +0.064 / +0.353 $/MWh, a
slope contribution of **+0.049** against a deficit of **−1.049** — **4.7 %**. Fixing Object C would not
close Object B. (Reported as a separation result only; the §2.2 stop rests on identification alone.)

**Handed forward.** The successor to Object B is a **marginal-unit** question, not an offer-markup one:
`phys_*` is the measured *average* heat rate over committed hours so it already carries no-load burn,
which leaves the markup above full physical burn with no physical reason to scale with gas — so the
−14 % slope gap points at *which unit sets price*. The handoff's CT_PEAKER drift is the visible end of
the same chain (2.449 TWh model vs 2.687 actual in 2022, drifting away in all four years; share of
gas-family energy 3.91 / 0.41 / 0.45 / 1.08 % at $8.66 / $3.34 / $2.82 / $5.46 gas). **Not tested here.**
`gas_offer_margin_anchor_vintage` stays `U` — §2.2 applies to it identically.

## nyiso-237 — 2026-09-16

**ZERO LP.** Orchestrator-only (rule 32 `[R-SHARD]` (a)); no shard launched, no bundle written, no run
registered. Keeper `2026-09-14-nyiso-235-gas-repair` **unchanged**. Record:
`docs/RESULT-nyiso237-hydro-negative-price-phase0-2026-09-16.md`; probe
`scripts/probes/nyiso237_hydro_negprice_phase0.py`.

**G-DRIFT at `a3df8337`**: `moved_rows("NYISO") == {}`, fingerprint `bd2b4657f9b5df7e` reproduces —
rule 29(b) form 4 valid, no control solve owed.

**Phase 0 — the "cannot withhold" hypothesis is REFUTED on the meter.** EIA-930 `NG: WAT` against the
real zonal RT price, (month × hod)-matched, 2022: WEST ≤ $5 (n 277) **0.834** of matched (−461 MW);
five-zone mean ≤ $0 (n 127) **0.866** (−387 MW); ≤ $10 / ≤ $15 0.850 / 0.862; within-month price
quintiles Q1 → Q5 **−208 … +198 MW** (demand quintiles −65 … +154). The one cut that "held up" (WEST
≤ $0, 0.979) is 21 scattered hours. Real hydro backs off ≈ 15 % at the bottom. **The equality floor
was not built**; the rule-19 reconciliation with `hydro_min_flow_floor` is moot.

**The nyiso-236 G2 kill is a PRICE defect.** Keeper `Upstate_West` ≤ $0 in **498 h** of 2022 (real:
**21** WEST / **127** five-zone mean; ≤ $5: **2,855 vs 508**); Apr/May/Jun/Oct/Nov model means
−0.8 / 2.5 / 8.3 / 4.7 / 0.5 $ vs 32.3 / 31.9 / 57.5 / 39.1 / 22.4 measured; 2023: 214 h (May 170).
2024 / 2025: **0 h ≤ $5**. The arm's hydro loss lands exactly in those months (2022 Mar −19.1 / Apr −10.1 /
Nov −23.6; 2023 Oct −17.8 / Nov −6.9 GWh; 2024/25 0.000). In every fabricated hour the Central-East link
is at its monthly measured cap (100 % of hours, 9 of 12 months of 2022) and 217 of 498 clear at exactly
−$26 = the wind PTC offer. Real system in the same hours: net imports −405 MW, hydro −393 MW, West
price positive (p1 $1.97). Zonal error keeper−actual 2022 `Upstate_West` **−26.9 $/MWh** (NYC +9 to +16
in the same months); all 2023–25 zone-months with data +0.9 to +5.8.

**Matrix (rule 28(b))**: `hydro_budget_period_by_instrument` **`U` → `R`** — killed at G2, root-caused,
re-open condition = a Central-East seam repair that brings the model's 2022 ≤ $0 count to the measured
order; the 24 h / 168 h lengths are never swept. Shard `keeper:` field and the §5.5 header re-stamped to
`2026-09-14-nyiso-235-gas-repair` (a nyiso-235 rule-28 duty the CI guard was warning on).

**Successor**: the Central-East seam in 2022–23 (nyiso-224's owner-gated topology change; nyiso-169's
measured-TTC-correct / wrong-shape reading) — this session adds its price-floor half. Hydro remains
unscored by C1 (handed forward, unchanged). Rule 31: nothing new to retain or delete; nyiso-236's legs
stay at their pinned SHAs. Rule 33: no shards to archive.

## nyiso-240 — 2026-09-19

**ZERO LP. Keeper UNCHANGED** (`2026-09-17-nyiso239-bench-oil-basis`, years {2022,2023,2024,2025},
`CALIBRATED`, grade 7, fails 0, C3c the lone ledgered caveat). Nothing armed, screened, solved,
promoted or registered; no mechanism-matrix cell moves. Record:
`docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md`; probe
`scripts/probes/nyiso240_c1_margin_bench_phase0.py` →
`results/calibration/_nyiso240_c1_margin_bench_phase0.json`.

**The handoff's winter/deliverability lead is WITHDRAWN on evidence.** Against NYISO's own published
hourly fuel mix the model's total fossil is **+2.0 % in February and +0.8 % in November** 2022
(−1.1 % for the year); the month-grain outliers are January −7.6 % and December −10.6 %, both
*under*-runs. The `CC_REGULAR` over-run is intra-fossil misallocation, not a fuel-delivery event.

**Two benchmark defects named, both shared across every ISO, neither landed (rule 25).**
**R1** — EIA-923 drops whole months and its *published annual* drops them with it: Bethlehem Energy
Center (2539) is absent for Feb and Nov 2022, CAMPD meters 596.0 GWh there (879.6 GWh scaled by the
plant's own measured ten-month ratio), and `_backfill_eia923_with_campd` cannot see it because it
gates on a 50 GWh **annual** floor against Bethlehem's 4,262 GWh. **67 plant-years across nine BAs.**
**R2** — `_classify_f923` routes 100 % of DFO/RFO/JF/KER/WO/PC to the `oil` class while the model
books every MWh of Astoria Energy / Astoria II / Zeltmann as `CC_REGULAR/gas_cc` (the model's whole
`oil`-fuel fleet is 11.1 GWh against a bench `oil` class of 1,843.7 GWh).

**Margin**: 2022 `CC_REGULAR` **+2.95 → +1.93 pp** against ±3.0 (headroom 0.05 → 1.07 pp). **Cross-ISO
verdict census — every ISO's keeper re-scored: 42 C1 rows move ≥ 0.05 pp, ZERO change status, ZERO of
the eight determinations flip.** Stated at full magnitude: 2023 `ST_GAS` (+2.85 → +2.70) and 2024
`CC_REGULAR` (+2.46 → +2.44) are barely touched and +2.26 TWh of the 2022 over-run is real.

**Cost**: nyiso-239's four shard SHAs still resolve — all four legs retrieved with `dispatch/` and
`unit_hourly/`, so the NYISO realisation is a `--rebuild-benchmark` re-render at **zero LP**.

**Successor**: `CT_PEAKER` collapses out of merit from 2023 (model 2.43 → 0.25 / 0.30 / 0.77 TWh
against a flat ~2.1–2.8 actual) with capacity intact, and the displaced energy is exactly 2023
`ST_GAS` +3.40 and 2024 `CC_REGULAR` +2.94 — the two C1 rows the bench repairs do not touch.
Recommended lever: `ct_peaker_committed_measured` (cell **U**, NYISO's own 0.843 vs the transferred
1.35). `nyiso_ct_peaker_bands_measured` stays **R** and was not re-tested. Rule 31: nothing new to
retain or delete. Rule 33: no shards launched.

## nyiso-240 (promotion) — 2026-09-19

**KEEPER → `2026-09-17-nyiso240-bench-attribution`** (bundle `results/calibration/nyiso240_benchfix_span`),
all four registered years 2022-2025, superseding `2026-09-17-nyiso239-bench-oil-basis` (pruned this
session, rule 35 `[R-PROMOTE]` (a)). Owner ruling, verbatim: *"Is this a recommended keeper candidate?
If so plz promote. If structural integrity improves but gates regress that may still be a keeper.."*
Record: `docs/RESULT-nyiso240-bench-attribution-promotion-2026-09-19.md`.

**ZERO LP, and the dispatch is bit-for-bit the superseded keeper's.** nyiso-239's four per-year shard
bundles were re-fetched by full SHA (`5802986a` / `0f03dd49` / `ce299f37` / `9859790c` — all still
resolving), re-composed and re-rendered with `--rebuild-benchmark`. `solve_surface.fingerprint`
`bd2b4657f9b5df7e` unchanged; zero `ScenarioConfig` fields move; the 14-entry DOF ledger and
`authorized_price_tuning` NONE carry over byte-identical. nyiso-239 §7's ~18 min four-shard re-solve
assumption is **falsified** — a bench-construction repair needs no solve if the shard SHAs were recorded.

**Two benchmark boundary repairs landed in the shared bench path, on rule 14 `[R-ACCURATE]`.**
**R1** `_backfill_eia923_missing_months`: EIA-923 drops months a respondent withheld and EIA's own
published *annual* is the sum of the months filed, so the withheld block is absent from the annual class
benchmark; `_backfill_eia923_with_campd` gates on a 50 GWh **annual** floor and cannot see it. Bethlehem
Energy Center (2539) filed no Feb and no Nov 2022; +0.880 TWh, against a phase-0 prediction of 879.6 GWh.
**R2** `_reattribute_dual_fuel_oil`: 1.668 TWh moved from the `oil` class into the classes the units
dispatch in, matching the prediction exactly.

**DETERMINATION UNCHANGED — `CALIBRATED`, grade 7, fails 0, C3c the lone ledgered caveat, zero C1 status
flips.** The gain is margin: 2022 `CC_REGULAR` **+2.95 → +1.93 pp** of a ±3.0 pp band (headroom 0.05 →
1.07 pp); 2023 `ST_GAS` +2.85 → +2.70; 2024 `CC_REGULAR` +2.46 → +2.44. **Rule 25 discharged before
landing**: every ISO's keeper re-scored, 42 C1 rows move ≥ 0.05 pp, **zero change status, zero of the
eight determinations flip**.

**Reported at full magnitude**: R2 moves 2022 `ST_GAS` −0.61 → −1.17 pp and 2025 `ST_GAS` −2.74 → −3.15 pp
(SKIPPED/ungated); +2.26 TWh of the 2022 `CC_REGULAR` over-run is real. D-4 reads False before **and**
after on an identical row set — pre-existing, not a regression. G2 hydro stays a ledgered OPEN
ROOT-CAUSE ISSUE (rule 21), not a caveat.

**Successor**: the `CT_PEAKER` merit collapse from 2023 (model 2.43 → 0.25 / 0.30 / 0.77 TWh against a
flat ~2.1-2.8 actual, capacity intact), which plausibly owns both remaining tight rows. Recommended
lever `ct_peaker_committed_measured` (**U**). `nyiso_ct_peaker_bands_measured` stays **R**, not re-tested.
Rule 31: the four retrieved nyiso-239 legs stay on disk, gitignored, never `rm`'d. Rule 33: no shards.

## nyiso-240 (MER control) — 2026-09-19

**G-DRIFT FORM 4 CONFIRMED EMPIRICALLY, AT BYTE IDENTITY.** The keeper's dispatch was solved at
`3edb8ad8`; the solve path has moved 14 files / +3,176 lines since. Replayed at HEAD
(`1fdcc69c`), **`dispatch/<yr>_P1.parquet` is byte-identical by sha256 in all four years**, as is
`unit_hourly`; `class_hourly` deviates by **0.000e+00** on every class and every hour; `system`
prices are identical. The only differences anywhere are ADDED COLUMNS. Record:
`docs/RESULT-nyiso240-bench-attribution-promotion-2026-09-19.md` **Addendum A**.

**Why a control was owed despite the arm being promoted**: the promotion was zero-LP, so the keeper's
bundle is nyiso-239's 2026-09-17 dispatch and predates the emissions dual (`2ec09663`, 2026-09-18).
The owner's skip-clause assumes the arm carries the column; it does not.

**Per-year fan-out on the OWNER'S EXPLICIT INSTRUCTION, and rule-32(b)-legal**: 32(b) bans fanning
out a run that must recombine FOR REGISTRATION and names the diagnostic carve-out this never-
registered control sits in. Four legs, one per year, ~15 min wall instead of ~45.

**Marginal emission rate** (per zone-hour, tCO2/MWh, load-weighted mean): 2022 **0.4508**, 2023
**0.4753**, 2024 **0.5219**, 2025 **0.5310**; zero-share falls 10.92 % → 1.27 %; zero NaN. The level
is a gas CC at the margin and sits far above NYISO's average grid intensity, which is what a
marginal rate should do in a nuclear+hydro-diluted system.

**Retrievability** (rule 34(d), verified 17 files per leg BEFORE archiving; branch names die, SHAs
do not): 2022 `93eb1aa918c039a01d6e5ba6265eedd7f69fdb03`, 2023 `24a75c15f0b08ccb51c59107f1f36163a02a5fef`,
2024 `0573d6382a2526cb482d544567c967767f50556e`, 2025 `5633d28698ee5bd07a2afccab63e02d2d8b70382`;
composed at `results/calibration/nyiso_mer_2026-09-19`. **OPEN for the owner**: the control is
unregistered by instruction, so these live only on shard branches — a marginal-abatement page needing
them durably needs a registration or allowlist decision (RESULT §A.3).

**SEPARATE FINDING, wants an owner**: `legitimacy_diagnostics.py` is **not reproducible** on its
measured columns — nine rows (seven D-1, two D-4 plant 2500) wobble at the 3rd decimal, and re-running
it on the IDENTICAL bundle twice reproduces exactly the same nine wobbles. Not drift. No verdict moves
today, but C8 and rule 20's conditional-pass path both read this gating artifact (RESULT §A.6).

Nothing registered, no dashboard id minted, keeper unchanged. Rule 31: nothing deleted; the legs and
the composed span are gitignored, not removed. Rule 33: all five shards archived after verification.

## nyiso-244 — 2026-09-20

**ZERO LP, ZERO SHARDS, keeper `2026-09-19-nyiso241-ct-committed-measured` UNCHANGED, nothing
armed or registered.** Executes the `RESULT-nyiso243` §6 design pass on `measured_offer_surface`.
Gates fixed in `docs/PRECOMMIT-nyiso244-measured-offer-surface-design-2026-09-20.md` at
`2e5097a5` **before any conditioned number**. Record:
`docs/RESULT-nyiso244-the-object-is-in-the-body-not-the-top-2026-09-20.md`.

**REFUSED AT THE GATE, and the refusal is the useful part.** The shared conditional-surface
kernel prices **peak rungs only**. In the 70 missed winter hours of 2022 the idle sub-$300
capacity — the only capacity whose offer can move the energy dual (nyiso-242 phase 0D) — sits
**74.5 % on ECON rungs (3,839.3 MW)** against **14.5 % on peak (745.7 MW)**: **15.8 %** of the
4,715.7 MW object against a pre-registered 50 % bar, and **0.1 % (6.1 MW)** on the CT family
P-27's masking can identify. The model's peak rungs are not idle below the gate **because they
are already offered above it** (`CT_PEAKER` peak 4.000, `ST_GAS` 4.200) — it is missing a
**body**, not a wall.

**Both nyiso-243 blockers discharged.** Rule 19 `[R-ONE-MECH]` **CLEARS**:
`gas_offer_net_revenue_margin` is **provably inert on every CC peak rung**
(`phys_peak == peak == 2.250` → markup exactly **0.0**), and where live (`CT_PEAKER` 3.000,
`ST_GAS` 3.200) it prices `(m − phys)` at the anchor while a surface prices `(M − m)` at fuel —
disjoint increments, **overlap 0 by construction**. Masking **FAILS its own validation**:
NYISO's own 10-Min Non-Synch product selects 51 gens / 2,374.0 MW against a model CT family of
58 plants / 3,404.7 MW — V1 scope PASSES at 0.043, V2 MW 0.303 > 0.25 and V3 sorted-capacity
fingerprint **1.328** > 0.25 FAIL. No fleet-wide substitute taken (rule 1). Rule 13
conditioning now holds on **3 of 4** keeper years, not the 2 nyiso-243 measured.

**THE SUCCESSOR IS LOCATED AND MEASURED COHORT-FREE.** A class-free **system offer curve**,
differenced missed-vs-ordinary winter so the two fleets' constant ~9.4 GW level gap cancels,
puts the object at **+4,989 MW at $200** and **+4,064 MW at $150** — a **5.8 % match** to the
4,715.7 MW object — and only **+907 MW above $300**. The market lifts **6,203 MW** out of
sub-$200 when the event arrives; the model lifts **1,213 MW**. `measured_offer_surface`
**`U` → `G`** with a two-limb re-open condition (an econ/midcurve form — reach measured at
74.5 % — **and** a validated cohort or a form needing none).

**Correction to the record**: `nyiso243_offered_availability.py` Leg 3 reads AS offers from
P-27 columns that are **100 % null** for all four reserve products, so its 866 / 794 MW are
**regulation only**. Leg 3 was a diagnostic, never a gate; **no nyiso-243 verdict moves**.

`tests/scoring` re-measured on this session's clean checkout: **22 failed / 1,553 passed /
18 skipped** — the handoff's unowned baseline, reproduced and still unowned. This session wrote
no solve-path code and adds zero.

## nyiso-245 — 2026-09-20

**ORCHESTRATOR, zero LP in the parent** (rule 32 `[R-SHARD]` (a)). Base `origin/main` `5c0bec8b`,
**rebased mid-session onto `e8b80102`** at the owner's instruction. PRECOMMIT
`docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md` committed at **`398f0437`**
(`5cbf4fef` post-rebase, content unchanged) before any gated number. RESULT
`docs/RESULT-nyiso245-the-object-is-level-dispersion-not-shape-2026-09-20.md`.
**Keeper UNCHANGED** (`2026-09-19-nyiso241-ct-committed-measured`); NYISO still **CALIBRATED** on
its ISO tier with C3c the lone ledgered caveat. Nothing registered, nothing promoted.

**1. The shape-only offer surface is REFUSED, and nyiso-244's re-open condition is SPENT.** Both of
its limbs were satisfied — the econ/midcurve form exists (`miso_offer_surface_measured`, a
within-unit price RISE on a within-unit position coordinate) and it **needs no cohort by
construction**, which is that condition's second branch. Reach clears decisively at **78.5 %**
(3,702.3 of 4,715.7 MW) against the 50 % bar carried over unchanged, because
`gas_offer_net_revenue_margin` is **LIVE on NYISO's ECON bands** — 298 of 715 rows carry the tag and
they are econ-dominated, which nyiso-244's peak-only scope could not see. Rule 19 clears (five armed
non-base writers, zero tagged rows also base, an assignment form). **G3a refuses it**: the measured
Δ ladder is non-monotone in **12 of 12** populated cells against an 80 % bar, and its largest value
anywhere is **$7.28/MWh**. A corpus-shape test on the derived artifact — not a residual (rule 1).

**2. The refusal locates the object: it is cross-unit DISPERSION of the conditional LEVEL.**
Within-unit differences over gens present in both windows (so the ~9.4 GW scope gap cancels), missed
minus ordinary winter 2022, cap-weighted median $/MWh — market curve BOTTOM **+26.66** / within-unit
RISE **+0.12**; multi-block only (every price taker excluded) **+19.01** / **+1.03**; model **+40.00**
/ **+11.34**. **The market does not steepen and the model already steepens 11× more than it does**, so
a shape-only form is blind to the object by construction. What the market does is disperse: level
response +$19 median, **+$112.05 p75, +$231.59 p90**, against a model that moves nearly every unit by
the same ~$40 and none by more. Successor class: `miso_offer_spread_anchored` /
`miso_offer_level_dispersion`, entering NYISO as **`U`** under rule 28(d).

**3. NYISO does NOT carry the rule 36 `[R-YEAR-ISOLATION]` (f) warm-start artifact.** Four control
shards (one year each) replayed the keeper's recipe at HEAD with both knobs OFF. **All four
years — 2022, 2023, 2024, 2025: max |Δ class TWh| = 0.0000 and 0 of 43,800 zonal price cells moved,
in every one.** Not
vacuous — the keeper was solved as ONE four-year span with both knobs ON, so 2024/2025 were its
third and fourth years, the position where MISO's defect bit hardest (7.16 / 24.18 / 4.00 TWh).
**Rule 36(f)'s "unmeasured outside MISO" exposure is CLOSED for NYISO**, and the G-DRIFT `LIVE` hunk
`cb1e60b7` is thereby **INERT for NYISO, measured rather than assumed** — the committed keeper IS a
valid form-4 control and a successor need not re-spend this. (The 2023 shard took two attempts: the
first backgrounded its solve and stalled unreachable; the replacement was told to run it in the
foreground and completed.)

**4. The stale `legitimacy_diagnostics.json` (the handoff's object 2) is regenerated and is a
NO-OP for NYISO.** Rebuilt through the current scorer from the control bundle and compared
row-for-row against the keeper's committed artifact (2022): **zero numeric moves** across
D1/D2/D4/D5/D9/D10, identical row sets, identical `passed` verdicts, identical thresholds. The only
structural change is the new `dispatch_source` stamp. No determination moves. *Not claimed*: this
does not close nyiso-240 §A.6's nine-row reproducibility wobble, which was measured on an identical
bundle rather than a fresh solve.

**Rule 26 `[R-DELETE]`.** The `ScenarioConfig` fields and the `apply_nyiso_offer_surface` applier
written for the refused form were **REVERTED, not committed default-off** — a refused mechanism that
still parses is a re-armable answer key. `scenarios.py` and `offer_curves.py` are byte-identical to
`origin/main`. The derive, its artifact and the probes stay as the measurement record.
