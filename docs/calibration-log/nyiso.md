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
(`calibration_verdict.VRE_TOL`, +/-10 %) is explicitly **report-only** and D-1
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
