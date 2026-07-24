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
