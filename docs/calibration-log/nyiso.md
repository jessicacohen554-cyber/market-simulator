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

**Disposition.** Per the step-2 promotion gate ("if it closes 2023, promote"),
2023 does **not** fully close → registered `2026-07-22-nyiso-70-scr-edrp` as a
**CANDIDATE**, both flags kept **default-off**; **nyiso-68 remains the keeper**
(no keeper-shard edit, no keeper churn — the nyiso-69 staging precedent). Both
reserve-eligibility flags are validated-correct and stay armed for the follow-up
that attacks the 2023 C3a mean-level gap. Remaining East-side piece unchanged:
Blenheim-Gilboa PS into the dispatch fleet (helps East-10min, secondary).
