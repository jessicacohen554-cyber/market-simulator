# PRECOMMIT — CAISO storage AS revenue: identification method, then value

_2026-08-25 · CAISO value-stack lane (D-9's missing AS credit). Charter:
`docs/FINDING-entry-signal-disarm-2026-08.md` §5.4/§6 ("CAISO's storage miss is
not signal-bound, so the CAISO queue's next rung is the value stack");
`docs/FINDING-entry-screen-t1h-2026-08.md` §4/§6 D-9._

This document is pushed in two stages so the identification can never be
steered by the answer (rule 13 `[R-MEASURED]`, rule 21 `[R-DOF]`):

* **Stage 1 (this commit): the method, pre-registered before any full-year
  number exists.** The prices were still mid-fetch from OASIS when this stage
  was written; no year's rate had been computed.
* **Stage 2 (a later commit, before ANY effect-on-entry arithmetic): the
  measured value, appended under §3 with no change to §1–§2.** Only after
  stage 2 is pushed does the lane compute what the credit does to the storage
  entry gap.

---

## 1. The identification, pre-registered

**Object:** the CAISO analogue of `constants.AS_REVENUE_PER_KW_YR_BY_ISO["ERCOT"]["storage"]`
(the exogenous per-kW-yr storage AS revenue credited by
`model.ancillary.as_revenue_per_mw_yr` in the capacity screens, gated on
`as_revenue_enabled`, default off). The registry's own intake note
(`capacity_market.py:2754-2775`) requires: the ISO's measured AS-market
revenue at a reference-fleet year, plus the reference fleet GW.

**Method (probe `scripts/probes/caiso_storage_as_revenue_phase0.py`, committed
at stage 1):**

    rate(year) = Σ_products Σ_hours DAM_award_mw × DAM_ASMP  ÷  fleet_avg_mw ÷ 1000

* **Awards**: `data/clean/storage-as-awards/CAISO` — CAISO Daily Energy
  Storage Report quarterly xlsx (re-fetched 2026-08-25, all 12 files
  sha256-identical to the tracked `SHA256SUMS.txt` identity record), curated
  through the frozen schema seam. Battery (LESR) + hybrid (HYBD), products
  RU/RD/SR/NR, hourly IFM.
* **Prices**: `data/raw/CAISO-AS/asprc_ALL_*.csv` — OASIS `PRC_AS` DAM per
  AS region and product, 2023–2025. CAISO's nested AS regions publish
  per-constraint shadow-price contributions; a resource's settlement ASMP is
  the sum over its containing regions. The award series is system-level, so
  the sub-regional adders are bracketed **LOW / CENTRAL / HIGH** (min adder /
  AS_REQ-requirement-share-weighted / max adder) — a rule 14 `[R-ACCURATE]`
  documented reconciliation, never an estimate replacing the data.
* **Denominator**: measured EIA-860 CAISO battery fleet via the model's own
  loader (`model.storage.load_eia860_storage`, monthly vintage ramps, li-ion
  only), averaged over the year. The same basis the model's own CAISO storage
  accounting uses.
* **Cross-validation (anchor, never input)**: DMM 2023/2024 Special Reports on
  Battery Storage — net market revenue $103 → $78 → $53/kW-yr (2022→2023→2024),
  energy share ~62% (2023) / ~82% (2024), RT-BCR 7% / 4% ⇒ AS + other ≈
  $24 (2023) / $7/kW-yr (2024). The DA-leg measurement must land at or below
  those remainders and reproduce the collapse, or the identification fails and
  is reported as failed.

**Known omissions, both conservative (undercount), reported not corrected:**
real-time incremental AS settlement (RT AS prices not intaken; RTM-vs-DAM
award deltas reported to size it) and regulation mileage (no mileage award MW
in the DESR).

## 2. Pre-registered decision rules

1. **The base rate is the 2023 CENTRAL rate at the 2023 average fleet**, the
   reference-fleet year matching the ERCOT registry's own 2023 calibration
   point. 2024/2025 rates are the saturation check, not free parameters.
2. **The saturation reference is the 2023 average fleet (GW)**; the decline
   exponent stays the shared `ERCOT_AS_SATURATION_EXPONENT = 2.5` unless the
   measured 2023→2025 implied exponent contradicts it, in which case the
   discrepancy is REPORTED and escalated — not silently refit (a CAISO-fitted
   exponent would be a new DOF needing its own identification).
3. **No value in this lane may change after the entry-gap effect is seen.**
   If the identified credit does not close the gap, that is the result
   (charter: "SAY SO AND STOP THERE").
4. **Nothing is armed in this lane.** Whether a CAISO row enters
   `AS_REVENUE_PER_KW_YR_BY_ISO` (default-off behind `as_revenue_enabled`,
   forecast-lane only) is an owner decision; this lane delivers the
   measurement and the reconciliation.
5. **Rule 19 `[R-ONE-MECH]` posture, stated ex ante:** in the T1-H CAISO lane
   nothing prices storage AS (`caiso_reserve_coopt=False`,
   `energy_reserve_coopt=False`, `as_revenue_enabled=False` — verified in the
   registered `run_config.json`). An exogenous credit would be THE single AS
   mechanism for CAISO storage entry, with the existing endogenous-flag
   suppression seam (`ancillary.py` module docstring) already reconciling any
   future co-opt arming. The RA capacity value is a SEPARATE revenue stream
   (the RA attribute), not a second pricing of AS — the reconciliation
   argument and its bounds go in the FINDING.

## 3. Stage 2 — the measured value

_Appended by the stage-2 commit; absent in stage 1 by construction._
