# MISO CC_REGULAR merit-order overrun (G-23) — ranked root-cause audit

**Date:** 2026-07-07. **Lane:** L-14 MISO, gap register G-23 deep diagnostic.
**Baseline:** keeper `2026-07-06-miso-44-wefor-neutral` — CC_REGULAR **+20.0 /
+19.1 / +3.1 TWh** vs EIA-923 (2023/24/25). This report audits the eight
candidate boxes from the task brief, states clean/broken with evidence, and
ranks each box's contribution to the overrun. The structural fix landed from
this audit is the **per-plant CC demonstrated-capacity cap** (box 8), solved
full-span as `miso-45-cc-capacity-cap` with a zero-forcing ablation twin.

## Where the +20 TWh sits (keeper decomposition)

Displaced buckets vs actual (TWh, keeper miso-44):

| bucket | 2023 | 2024 | 2025 |
|---|---|---|---|
| **CC_REGULAR** | **+20.0** | **+19.1** | +3.1 |
| ST_GAS | −8.5 | −11.0 | −10.5 |
| net imports | −7.4 | −9.9 | −17.7 |
| CT_PEAKER | −6.2 | +0.6 | −3.1 |
| coal family (BIT+PRB+LIG) | −3.7 | −5.4 | **+28.1** |
| ST_CHP / CT_CHP / OTHER_FOSSIL | −8.0 | −10.2 | −5.9 |
| hydro + oil | −1.7 | −2.1 | −9.3 |
| CC_CHP | +3.0 | +1.2 | +2.4 |

The decisive instrument: **within the CAMPD-covered CC_REGULAR plant set
(32 plants, 25.2 GW bench nameplate) the model aggregate matches the actual
almost exactly** — 127.6 model vs 128.1 CAMPD TWh (2023), 134.3 vs 130.7
(2024). The class-level overrun therefore lives in the *capacity
representation*, not in class-wide merit-order placement: the model's
CC_REGULAR fleet carries **30.1 GW** against the bench's 25.2 GW, and the
overrun concentrates at exactly the plants whose modeled pmax exceeds
anything they ever generated (Union Power modeled at a 109.7% capacity factor
of its true nameplate in 2023).

## Ranked verdicts

### 1. Box 8 — EIA-860 capacity accuracy: **BROKEN (the driver)** — ~13–15 TWh/yr

Root cause: EIA-860's combined-cycle reporting convention. For several CC
plants the steam (prime mover `CA`) row's **Summer Capacity is reported at
the power-block level** while Nameplate stays component-level. The fleet
loader prefers net summer capacity (`fleet.py:3433-3435`,
`pmax = net_summer_capacity_mw or nameplate`), so summing CT-nameplate rows
(whose summer field is blank) with block-level CA-summer rows **double-counts
the CTs**. Nationwide this affects 745 units / +11.5 GW; in MISO it lands
almost entirely on the Entergy South CC fleet.

Worked example — Union Power Station (55380): 8 CTG × 176 MW nameplate +
4 STG × 255 MW nameplate = 2,428 MW; the four STG rows carry Summer Capacity
508.7–513.9 MW ( ≈ one full 2×1 block each). Model pmax = 8×176 + Σ(512.4,
508.7, 513.6, 513.9) = **3,457 MW**, +42% over nameplate. EIA-860 *winter*
capacity (2,354 MW) and the CAMPD demonstrated peak (p99.9 = 2,318 MW)
corroborate the true value. The model dispatched 23.3 TWh from this plant in
2023 vs 13.7 actual — +9.7 TWh at one plant.

Plants capped (from `scripts/data/derive_cc_capacity_reconcile.py --iso MISO
--mode cap` — CAMPD p99.9 sustained peak, ×1.10 cap-margin guard, EIA-923
CF-feasibility guard, pure-play-CC gate):

| plant | model MW | CAMPD p99.9 | EIA-860 winter | Δ |
|---|---|---|---|---|
| Union Power Station (55380) | 3,457 | 2,318 | 2,354 | −33% |
| Hot Spring (55418) | 957 | 582 | 634 | −39% |
| Attala (55220) | 812 | 517 | 514 | −36% |
| Hinds (55218) | 811 | 532 | 557 | −34% |
| Ouachita (55467) | 1,257 | 841 | 836 | −33% |
| Harry L. Oswald (55221) | 548 | 438 | 548 | −20% |
| Greater Des Moines (7985) | 504 | 404 | 591 | −20% |

Total **−2,714 MW phantom CC_REGULAR capacity**; upper-bound direct energy
shave 14.7 / 13.2 / 12.2 TWh (2023/24/25) at the keeper's per-plant
utilizations. Six of seven plants are MISO-South — matching the keeper's
zonal signature (~73% of the CC overrun in South,
`results/calibration/FINDING-miso-cc-decomposition-2026-07.md` §2).

Conservative skips, logged: Perryville (55620, CT/CC mixed site), Nine Mile
Point LA (1403, CC unit at an ST_GAS plant), Edwardsport (1004, coal-IGCC
mixed) fail the pure-play-CC gate (plant-summed CEMS would overstate the CC
peak); Noblesville (1007) fails the EIA-923 feasibility guard (CEMS extract
incomplete — implied CF 0.93 at the would-be cap). Residual phantom at those
sites ≈ 0.3–0.9 GW; class-level phantom outside CC is small (COAL +146 MW at
the mixed Edwardsport site, CT_PEAKER +49 MW).

Fix (structural, measured, per-ISO — rules 13/24/25): the existing
`ScenarioConfig.cc_capacity_reconcile` seam (`fleet._reconcile_cc_capacity`,
`fleet.py:5289`; applied in the per-plant path at `fleet.py:5879`), the same
mechanism the PJM keeper carries for its own phantom-CC table. New per-ISO
artifact `data/raw/_processed-legacy/cc_capacity_reconcile_MISO.csv` +
`--cc-capacity-reconcile` flag on `scripts/run_calibration_full.py`
(resolves the invoking ISO's table; generic override channel, recorded in
`run_config.json`/`meta.json`). Admissibility: a demonstrated-capability cap
is a measured physical input that regenerates for a forward year from the
rolling CEMS record and responds to changed conditions (uprates appear as
new demonstrated peaks); it pins capacity to *capability*, never dispatch to
*outcome*.

### 2. Box 3/7 — must-run / RA floors for ST_GAS, CT, coal: **STRUCTURALLY OPEN under G-25, not a floor gap** — ~8–11 TWh/yr (ST_GAS), bounded

The reliability-floor registry (`data/raw/reference/
reliability_floor_coeffs_MISO.csv`) carries derived limbs for **every**
fossil class in every MISO zone (ST_GAS, COAL, CT_PEAKER, CC, CHP; hot-day
`tmax` and cold-day `tmin` drivers, CT limbs windowed h15–21). Only four
limbs pass the enable gate and they force <0.6 TWh total (keeper
attestation). These are *design-day commitment* floors; they are not — and
per rules 15/19/20 must not become — a channel for the everyday 8–17 TWh/yr
that real MISO ST_GAS/CT units earn through self-commitment and uplift-backed
out-of-merit operation. That wedge is the P1 commitment-fidelity gap
(G-25): the DP-1 MIP crossbench measured P1 carrying +34% committed CC energy
vs a min-load/min-run MIP, and the pooled-SA commitment-posture lever built
for it was probed this cycle (`miso-43-commitment-posture`) and
**honesty-gate rejected** against the measured MISO ASM series (postured
online headroom 3.7–4.2× measured cleared reserve; CC row unchanged). No
MISO-specific LP-level RA must-offer exists (the `caiso_ra_mustoffer`
mechanism is CAISO's); MISO's LMR/RA construct does not entail an energy
must-offer of that form. Verdict: floors present and rule-15-compliant;
the ST_GAS/CT underrun is real, quantified, and stays open under G-25 —
adding a floor against it would be residual-stacking (rule 19).

### 3. Box 5 — import/export seam prices & limits: **MECHANISM PRESENT, RESIDUAL DOWNSTREAM** — ~7–18 TWh/yr, expected to close partially with box 8

Keeper carries priced interchange with the measured seam envelope
(`miso_firm_imports`, `miso_seam_flow_limit`, `miso_seam_export_limit`,
`miso_pjm_border_anchor`, `reference_price_interface`). Net imports remain
short: model −30.5 vs actual −37.9 TWh (2023), −13.2 vs −23.1 (2024), −1.2
vs −19.0 (2025). The 2026-07-06 adjudication
(`FINDING-miso-cc-decomposition-2026-07.md` §3) stands: priced imports clear
only when the neighbor beats the internal LMP, and the internal level was
depressed (C3a −9.8/−15.6/−19.5% at miso-41; −8→−13% at miso-44) — largely
*by the phantom South CC supply itself*. Import-price levers were re-examined
and not touched (a measured-LMP import pricing against a too-low internal
level imports even less; `miso_firm_import_floor` forces a measured outcome —
rule 13). Re-audit after the box-8 cap: removing 2.7 GW of phantom South
supply raises the internal price and South's export pressure falls, both of
which pull the priced seams toward the measured envelope.

### 4. Box 2 — coal sigmoids / PRB passthrough: **PARTIALLY CLEAN, LEDGERED DOF** — ≤5 TWh/yr on 2023/24 CC; owns much of 2025's +28 coal

The MISO curves are MISO-fitted (`COAL_SIGMOID_DEFAULTS[("MISO","bituminous"
/"prb"/"prb_follower")]`, `scenarios.py:4106-4135` — run-30 series), so no
rule-24/25 cross-ISO violation. The marginal-tranche discount was already
removed by `coal_econ_srmc_bound` (miso-42): econ/peak coal offers are
clamped ≥1.0× the plant's measured F923 incremental delivered SRMC; the
committed/must-run bands keep the contracted take-or-pay discount. Remaining
coal underrun 2023/24 is modest (−3.7/−5.4 TWh family) and the committed-band
sizing from measured EIA-923 Schedule-5 contract volumes remains the open
item flagged at miso-42 registration. The 2025 flip (+28 TWh coal overrun,
dear-gas year) is the same supply-surplus problem the import shortfall
carries (−17.7 TWh in 2025) plus the sigmoids' cheap-gas-keyed discounts —
re-scored after the box-8 cap before any curve is touched (rule 21: derive
scripts frozen against residuals).

### 5. Box 1 — citygate / delivered gas prices: **CLEAN** — ≤2–3 TWh, sign-inconsistent

Measured F923 delivered gas for MISO CC plants (quantity-weighted,
37 plants, ~1,000 M MMBtu/yr coverage) vs the model's delivered level
(HH annual + `GAS_BASIS_DIFFERENTIAL["MISO"]`=+0.30, monthly seasonality,
mean-zero zonal spread `apply_miso_zonal_gas_basis`):

| year | F923 wavg | model | Δ |
|---|---|---|---|
| 2023 | $3.07 | $2.84 | −$0.23 (−7%) |
| 2024 | $2.59 | $2.49 | −$0.10 |
| 2025 | $3.68 | $3.82 | +$0.14 |

At CC heat rates the 2023 miss is ~$1.6/MWh — too small to re-order CC vs
$28–30 coal, and the sign flips by 2025. The measured zonal gradient
(South $2.71 / East $3.49 in 2023) is carried by the mean-zero zonal basis.
The flat +0.30 blend slightly understates 2023 (+0.53 measured) and
overstates 2025 (+0.16 measured); a measured per-year basis would be a
data-intake refinement, not a CC-overrun lever.

### 6. Box 6 — take-or-pay / mine-mouth coal economics: **CLEAN**

`coal_takeorpay_MISO.csv` (EIA-923 Schedule-5 purchase-type shares,
`scripts/data/derive_coal_takeorpay.py`) exists and the keeper runs
`coal_takeorpay_from_data: true` — the contracted-fuel share anchors the
cheap committed band per plant from measured data; the marginal tranche pays
full delivered SRMC (box 4 above). Mine-mouth economics enter through the
plant-specific F923 delivered cost (`coal_plant_monthly_pricing: true`).

### 7. Box 4 — internal TTC: **CLEAN (documented design)**

The six internal Midwest bilateral links are deliberately non-binding
placeholders (`iso_configs.py:419-433`); internal congestion is carried by
the *measured* per-zone CIL/CEL directional interface groups (MISO LOLE
study, per-season hourly caps in backcast via
`transmission.build_miso_deliverability_groups`) and the JOA RDT contract
path encoded verbatim as an asymmetric one-way pair (3,000 N→S / 2,500 S→N,
`iso_configs.py:470-489`). No seed guess governs; decomposing zone CILs into
bilateral TTCs would be an invented apportionment. The RDT correctly capped
South's export path while South carried the phantom-CC surplus.

### 8. Box 8-adjacent checks — COD ramp / retirements: **CLEAN**

The backcast fleet is the year-matched EIA-860 vintage (retired units drop
with the vintage; 54 within-window retiree units carried explicitly).
Model-only CC plants vs the bench set are legitimate: West Riverside
(64020, COD 2020) and Magnolia Power (67005, COD 2025, 0.28 TWh in 2025 —
ramped correctly) are real units; CAMPD-covered fleet totals match actuals.
No retired-CC-still-dispatching case found.

## Expected effect of the box-8 fix

Upper-bound direct shave at keeper utilizations: **14.7 / 13.2 / 12.2 TWh**
(2023/24/25) against CC overruns of +20.0/+19.1/+3.1. The LP rebalances:
remaining CC headroom, coal, and the priced seams absorb some of the removed
energy — in 2025, where the shave exceeds the CC overrun, the expectation is
higher internal prices pulling the import channel toward the measured
envelope (the structurally correct direction; actual 2025 was a 19 TWh
net-import year the model currently serves domestically). Residual CC
overrun after the cap is the G-25 commitment wedge plus the conservative
skips above. Whatever the residual does, the cap stays: it is measured
capability (rule 14 — never revert accurate data because the fit moved).

## Fix inventory (this session)

- `data/raw/_processed-legacy/cc_capacity_reconcile_MISO.csv` — derived,
  committed (7 plants, −2,714 MW, mode=cap).
- `scripts/run_calibration_full.py` — `--cc-capacity-reconcile` flag
  (per-ISO table resolution through the generic ScenarioConfig override
  channel; recorded in the bundle's run_config/meta).
- Run `miso-45-cc-capacity-cap` (2023 2024 2025, one invocation, rule 16)
  + zero-forcing ablation twin (rule 20) — registered on the dashboard.
- DOF ledger: **no new free parameter** (the cap value is the plant's own
  measured CAMPD p99.9; thresholds `_CAP_MARGIN`/`_CAP_FEASIBLE_CF` are the
  pre-existing derive-script guards shared with the PJM artifact).
