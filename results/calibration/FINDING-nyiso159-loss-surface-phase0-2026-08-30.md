# FINDING nyiso-159 phase-0 — the NYISO loss component measured on the completed 36-month record: a sign-stable, monotone, material downstate floor the lossless model omits; identification derived; MATERIAL, proceed to prereg

**Session:** nyiso-159, 2026-08-30. **NO SOLVE** — every number is measured
from the curated NYISO MIS component record plus committed keeper/bench
artifacts. Freeze ACTIVE; no year outside {2023, 2024, 2025} solved or scored
(the 2022 numbers cited from nyiso-158 are that finding's, re-quoted, not
re-measured). Zero fitted scalars. Machine-readable record:
`results/calibration/_nyiso159_loss_phase0.json` (probe
`scripts/probes/_nyiso159_loss_phase0.py`).

**Keeper under diagnosis:** `2026-08-30-nyiso-157-par-attribution` (NOT-YET on
{C3a, C3b, C3c}, owner ruling 2026-08-30).

---

## §0 — The intake this session performed (data prep, rule 22 clause: unrestricted)

On-disk RT zonal LBMP coverage was 21 committed months (2022 full + 9
scattered 2023–2025). This session staged the 27 missing 2023–2025 months via
the frozen idempotent fetcher (`scripts/data/fetch_nyiso_zonal_lmp.py --kind
rt --start 202301 --end 202512`; committed months untouched byte-for-byte) and
re-curated through the existing `lmp` contract (`scripts/data/curate_lmp.py`).
`data/clean/lmp/NYISO/RTM/lmp_<yr>.parquet` now carries all 36 months of
2023–2025, 11 internal zones, with the posted `loss_usd_per_mwh` +
`congestion_usd_per_mwh` components. The zips remain gitignored/regenerable
per the standing `data/raw/lmp-data/README.md` convention; the durable
committed artifacts are the derive output (once filed) and this phase-0
record.

## §1 — Contract checks: the posted decomposition is exact and the reference is uniform

* **Identity** `LBMP = E + MCL − MCC` ⇒ `Δtotal = Δloss − Δcong` holds to
  publication rounding on every zone-month of all three years: max absolute
  residual on hourly means **$0.009** (2023) / $0.008 (2024) / $0.009 (2025).
* **Reference-energy uniformity:** E recovered per zone-hour
  (`LBMP − MCL + MCC`) agrees across all 11 internal zones to p99 ≤ $0.0075,
  max ≤ $0.015 — the same-quality identity CAISO's derive asserts at
  `MCE_IDENTITY_TOL`. The decomposition is usable as published.
* Coverage: 12/12 months, all zones, every year (8,759/8,783/8,757 hourly
  rows; DST-correct via the curator's UTC hour binning).

## §2 — The measured object: the loss component of the downstate gradient

Annual mean spread vs `Upstate_West` (model-zone aggregation = simple mean of
member A–K zones — `derive_actual_lmp.NYISO_ZONE_MAP`, the scoring actuals'
own convention), split on NYISO's own posted components, against the keeper's
model spread:

| year | zone | measured total | **measured loss** | measured cong | model total |
|---|---|---|---|---|---|
| 2023 | Capital_Hudson | 9.26 | **1.12** | 8.14 | 9.96 |
| 2023 | NYC | 8.15 | **1.74** | 6.40 | 10.00 |
| 2023 | Long_Island | 15.73 | **2.05** | 13.68 | 10.68 |
| 2024 | Capital_Hudson | 3.73 | **1.69** | 2.04 | 1.39 |
| 2024 | NYC | 6.46 | **2.62** | 3.85 | 1.60 |
| 2024 | Long_Island | 9.18 | **2.81** | 6.37 | 2.25 |
| 2025 | Capital_Hudson | 7.93 | **2.92** | 5.01 | 3.08 |
| 2025 | Lower_Hudson | 7.64 | **3.72** | 3.92 | 3.08 |
| 2025 | NYC | 11.63 | **4.14** | 7.49 | 3.27 |
| 2025 | Long_Island | 14.82 | **4.26** | 10.56 | 3.71 |

Three structural readings:

1. **In 2024–2025 the measured LOSS component alone equals or exceeds the
   model's ENTIRE zonal spread.** 2025 NYC: measured loss $4.14 vs model
   total $3.27. The model's lossless internal links have no representation of
   this component in any hour — the same measured copper-plate-residual class
   as pjm-136 M1a and caiso-164 §0.
2. **The gradient is monotone and sign-stable.** The delivery-factor
   deviation `dev_z,m = ΣMCL_z/ΣE` is monotone increasing down the chain
   UW < CH < LH < NYC < LI in **every one of the 36 months** (dev spread
   UW→LI ≈ 0.075–0.12 winter, 0.06–0.09 summer; UW itself negative, i.e.
   west of the load-weighted reference — the persistent physical gradient
   class, PJM's 12/12 sign-stability analogue).
3. **2023 is the one year the model's CH/NYC spread already overshoots**
   (model 9.96/10.00 vs measured 9.26/8.15 — the Feb-2023 pre-Transco
   saturation overshoot nyiso-158 §1.3 measured). The loss floor adds on top
   of that overshoot in 2023; this is a named adverse case in the prereg, not
   a surprise to discover later.

## §3 — Loss share of each rubric-failure face

Load-weighted (keeper zonal demand weights) downstate premium over UW, loss
part vs total, on the faces the owner's NOT-YET names:

| face | measured LW total premium | **LW loss premium** | face miss (nyiso-158 §2) | loss share of miss |
|---|---|---|---|---|
| Jan-2025 (winter) | 26.70 | **6.07** | −23.8 | ~26 % |
| Feb-2025 (winter) | 15.81 | **5.17** | −23.1 | ~22 % |
| Jun-2025 (summer) | 8.73 | **2.72** | −27.1 | ~10 % |
| Jul-2025 (summer) | 10.91 | **2.11** | −14.3 | ~15 % |
| 2025 annual (C3a) | 7.30 | **2.54** | −7.98 $/MWh (−12.0 %) | ~32 % |
| 2024 annual | 4.06 | **1.59** | (−2.0 %, in band) | — |
| 2023 annual | 6.37 | **1.08** | (+1.0 %, in band) | — |

The winter-face loss premium ($5–11/MWh zonal, Jan/Feb-2025) confirms and
sharpens the nyiso-158 §1.5 reading on same-year data (its $5–8 was 2022):
a quarter of the winter face is the additive loss floor, **and none of it
requires the cutset to bind** — it exists in every flowing hour, exactly the
non-binding-hour premium mass §1.5 measured (~96 % of the real premium mass
forms outside bind95 hours).

## §4 — Materiality verdict and the honest bound

**MATERIAL — proceed to prereg (handoff step 1c).** The measured annual LW
loss premium ($1.08 / $1.59 / $2.54) bounds the arm's LW price effect from
above; ~60–100 % of it should be realizable as model LW uplift (southbound
flow is near-permanent; in link-binding hours the loss ratio adds to — not
replaces — the congestion dual; in the reverse-flow minority the clamp
contributes zero). Ex-ante honest predictions, stated before any solve:

* **C3a-2025** −12.0 % → **≈ −8.2 to −9.7 %** (closes ~2–4 pp of the 12).
  That may re-enter a ±10 band — as the restored FLOOR, not as object-month
  work. The winter/summer faces stay Leg-2 / ledgered-C3c work exactly as
  nyiso-158 routed them; congestion still dominates every face.
* **C3b-2025** 0.203: face errors shrink by the per-month loss premium →
  upper-bound arithmetic lands ≈ 0.16–0.19. Knife-edge either way; no
  C3b-specific lever is opened (nyiso-158 verdict 2 stands — this is the
  gradient/C3a lane, C3b moves only as a passenger).
* **C3a-2023** +1.0 % pushes UP by ≤ +3.3 pp (worst case, full premium
  realized) → ≤ +4.3 %, inside the +10 band with ~5.7 pp margin. Named
  adverse case with a hard gate in the prereg.
* **Upstate relocation:** UW's dual is set by its own balance as the
  persistent sender; the surface must leave it within noise (gate ±$0.75
  annual mean vs control — W-K3d class).

## §5 — What this does NOT reopen

No cutset-binding claim, no TTC change, no seam mechanism touched
(`nyiso_seam_par_attribution` stays armed; `nyiso_seam_deliverability_envelope`
stays armed-but-shadowed, rule 19), no C3c parameter, no floor/bridge change.
The DO-NOT-REDO cells stand: iroquois (R), Tier-3 TTC re-grounding (closed),
F/G split, bare Zone-K swap, §8-3 rescales. The loss surface is the
`zonal_loss_surface` shared row's NYISO test (cell currently `·`), off the
nyiso-145 queue with cause: every determination-moving queue item is
owner-court (Leg 2, CC cycling-cost id, hydro AS certification) or ledgered
(C3c); this lane addresses the annual-gradient/C3a face with measured physics
under an existing cross-ISO construction (PJM K, pjm-136; CAISO variant
caiso-164; MISO R by its own market's data — verdicts strictly per-ISO,
rule 25/28(d), nothing transfers but the estimator's algebra).
