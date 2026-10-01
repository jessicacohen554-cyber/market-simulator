# FINDING (miso-108): MISO's hydro LEVEL pin is PS-inclusive — the flagged
# `NG: PS` exposure is a CONFIRMED DEFECT, and it gates the
# `hydro_budget_nameplate_aware` transfer

**Session:** miso-108 (lever queue §5.4 item 6)
**Date:** 2026-07-30
**Verdict:** `NG: PS` pin audit → **DEFECT CONFIRMED for MISO**.
`hydro_budget_nameplate_aware` → **NOT armed, no solve** (blocked by the defect
below, rules 14 `[R-ACCURATE]` + 19 `[R-ONE-MECH]`). MISO cell stays `U`.
**Rule 25:** derived entirely from MISO's own data; no CAISO/PJM verdict
transferred.

---

## 1. What was audited and why

The mechanism matrix flags `hydro_budget_nameplate_aware` (`.KKUUU` — CAISO `K`,
PJM `K`, MISO `U`) as *the* live cross-ISO transfer, and records a **disclosed
defect** surfaced by that transfer:

> RELATED DISCLOSED DEFECT: PJM's hydro pin is PS-inclusive EIA-930 `NG: WAT`
> (+6.5–7 TWh/yr vs the 923 budget) — audit EVERY hydro ISO whose BA omits
> `NG: PS`.

MISO is such a BA. The audit is a prerequisite, not a side quest: the mechanism
is an *allocation* refinement that distributes a monthly hydro **level** more
faithfully across hours. If the level itself is contaminated, arming the
allocation distributes a wrong number more precisely.

## 2. The defect

Three facts, each independently checkable:

**(a) The LP units are conventional-hydro only.** `data/hydro.py` builds the
hydro budget family from EIA-923 prime mover `HY`; pumped storage (`PS`) is
explicitly excluded — "pumped storage is a storage resource, not inflow hydro"
(`hydro.py:704`), mirrored by the plant-registry filter at `hydro.py:290`.

**(b) The MISO keeper pins the monthly LEVEL to EIA-930 `NG: WAT`.**
`results/calibration/miso101_tempgrain_B/meta.json` carries
`hydro_eia930_monthly = True` (keeper `2026-07-28-miso-101b-tempgrain`).

**(c) MISO's `NG: WAT` is PS-inclusive.** `data/raw/eia-930-hourly/MISO
hourly.parquet` carries `NG: COL, NG, NUC, WAT, SUN, WND, BAT, OTH` — **there is
no `NG: PS` column**, though the model's own series map expects one
(`data/eia930/actuals.py:134`, `("pumped_storage", "NG: PS")`). MISO's PS output
has nowhere else to go.

So the level being pinned counts conventional hydro **plus pumped-storage
discharge**, while the units it pins are conventional hydro alone.

## 3. Proof that (c) is real, not inferred

**Nameplate overshoot — the physical impossibility.** MISO's entire conventional
hydro fleet is **2,478.4 MW** of nameplate (EIA-860, BA = MISO, `Hydroelectric`
excluding `Pumped Storage`). `NG: WAT` exceeds that total in hundreds of hours a
year:

| year | `NG: WAT` max | excess over conv nameplate | hours > nameplate | TWh above nameplate |
|------|--------------:|---------------------------:|------------------:|--------------------:|
| 2023 | 3,535 MW | **+1,057 MW** | 580 (6.6 %) | 0.180 |
| 2024 | 3,964 MW | **+1,486 MW** | 827 (9.4 %) | 0.424 |
| 2025 | 3,674 MW | **+1,196 MW** | 332 (3.8 %) | 0.075 |

Conventional hydro cannot exceed its own nameplate. The overshoot is almost
exactly the size of MISO's pumped-storage fleet — **2,416.8 MW**: Ludington
1,978.8 MW (6 × 329.8, plant 1713), Taum Sauk 408 MW (2 × 204, plant 2108),
Degray 30 MW (plant 187). MISO's PS fleet is ~97 % the size of its conventional
hydro fleet, so this is not a rounding-scale contaminant.

**Direction — one-way inflation.** There are **zero negative-`NG: WAT` hours** in
every year 2018–2026. Pumping load is therefore *not* netted into `WAT`: the
series carries PS **discharge** gross, and the contamination only ever adds.
Independent confirmation from the other filing: EIA-923 PS net generation for
MISO is **negative** every year (−0.840 / −1.033 / −0.692 TWh for 2023/24/25, the
expected round-trip loss), so a genuinely net-of-pumping series would have pulled
the pin *down*, not up. The observed sign proves the 930 series is gross
discharge — the same mechanism as PJM's disclosed case.

## 4. Magnitude — the PJM-comparable number

`NG: WAT` (the pin) against EIA-923 `HY` (what the LP units actually are):

| year | 930 `NG: WAT` | 923 `HY` | gap | inflation |
|------|--------------:|---------:|----:|----------:|
| 2023 | 9.979 TWh | 8.789 TWh | **+1.190 TWh** | **+13.5 %** |
| 2024 | 10.742 TWh | 9.041 TWh | **+1.701 TWh** | **+18.8 %** |
| 2025 | 9.872 TWh | *(excluded)* | — | — |

**2025 is deliberately not quoted.** Its EIA-923 filing is an early release
carrying only **14 MISO `HY` plants against 165** in 2023/2024 (0.970 TWh), so the
naive gap (+8.902 TWh, +918 %) is a coverage artifact of the *source*, not a
measurement of the defect. Quoting it would misstate the exposure by ~5×. The
2023/2024 rows are full 12-month, 165-plant filings on both sides.

MISO's exposure (+1.2–1.7 TWh/yr) is smaller than PJM's disclosed +6.5–7 TWh/yr,
consistent with the smaller PS fleet, but it is **13–19 % of the pinned hydro
energy** — not immaterial.

## 5. Why `hydro_budget_nameplate_aware` was NOT armed

Not a refusal of the mechanism — a sequencing call forced by the rules:

1. **Rule 14 `[R-ACCURATE]`.** The accurate input for a conventional-hydro budget
   is the 923 `HY` series (or a PS-decontaminated 930 series), not PS-inclusive
   `NG: WAT`. The defect is in the *level*; that is the accurate-input fix, and it
   comes first. Arming an allocation refinement now would let a more precise
   distribution of a **13–19 % inflated** budget absorb the error — the exact
   "bury the error inside an inaccurate input" pattern rule 14 prohibits.
2. **Rule 19 `[R-ONE-MECH]`.** Level and allocation are two mechanisms acting on
   the same phenomenon (monthly hydro energy placement). Stacking the new
   allocation on the unexplained residual of a contaminated level is the stacking
   this rule bars. Reconcile the level, *then* test the allocation.
3. **Rule 1 `[R-STRUCT]`.** Either arm would move the residual. Neither number
   would mean anything until the level is right, so a fit change here would be
   uninterpretable evidence.

A solve was therefore not run, and no arm was registered — there is no run to
register (rule 15 applies to produced runs; this session produced an audit).

## 6. Prescription for the follow-on session

The fix is a **level** correction, and it is data-side:

- **Preferred:** pin MISO's monthly hydro level to EIA-923 `HY` directly (the
  series `hydro.py` already uses for the per-plant budgets), making the level and
  the units the same population. Forward-reproducible: 923 `HY` regenerates every
  year and responds to hydrology (rule 13 `[R-MEASURED]` — it is the same
  admissibility class the per-plant budget already relies on).
- **Alternative if the 930 hourly *shape* is wanted:** keep `NG: WAT` for shape
  but rescale to the 923 `HY` annual/monthly level, i.e. decontaminate the level
  while retaining the measured intra-month pattern. Document the reconciliation
  explicitly — this is rule 14's "reconciled version of the real data" clause,
  and it is what the boundary-misalignment exception was written for.
- **Do NOT** subtract a fitted constant, and do NOT tune the correction against
  any price/dispatch residual (rules 13/23).
- **Then** test `hydro_budget_nameplate_aware` on the corrected level, deriving
  MISO's own classifier parameters from MISO's own fleet (rule 25 — CAISO's and
  PJM's `K` do not transfer; MISO enters as `U`).
- **2025 caveat carries forward:** any year-by-year 923 work must gate on plant
  coverage (165 vs 14) before differencing, or it will read the early-release
  filing as a collapse in generation.

## 7. Cross-ISO note

The matrix's standing audit item — "`NG: PS` hydro-pin audit (PJM disclosed;
every hydro BA to check)" (§5.7) — can be marked **MISO: audited, defect
confirmed**. The same three-step check (no `NG: PS` column → `NG: WAT` exceeds
conventional nameplate → zero negative hours) is mechanical and portable;
NYISO and NEISO remain unaudited. NEISO is known to have begun filing `NG: PS`
in Nov 2024 (`eia930/actuals.py:139`), so its exposure is likely time-split
rather than total — a different shape of the same question.
