# FINDING — nyiso-100: `NYISO_simultaneous_import` is a mis-attributed *internal* locality limit

**Date:** 2026-07-30 · **ISO:** NYISO · **Lane:** backcast calibration
**Matrix row:** `nyiso_import_sil_retire` (network) · **Rule:** 14 `[R-ACCURATE]` reconcile
**Instrument:** `scripts/probes/nyiso100_simultaneous_import_identification.py` (no LP)
**Keeper under study:** `2026-07-29-nyiso-99-demandfix` (`results/calibration/nyiso99_demandfix`)

---

## 0. Headline

`interchange.spec.EXTERNAL_SIMULTANEOUS_LIMITS["NYISO"] = 4,350 MW` is **not a
hand-set estimate and not an external seam limit**. It is *exactly* the
published NYISO **G-J locality** Bulk Power Transmission Limit for capability
year **2024/2025** — an **internal** New York transfer boundary (Load Zones
G, H, I, J) — installed as the **external** NYCA simultaneous-import cap and
frozen at one capability year's value.

The prior charter (nyiso-99) framed this as "a hand-set estimate measurement
contradicts". That framing was too generous: the number is a real published
NYISO quantity, measured on the wrong boundary. That changes the reconcile
from *"find the right number"* to *"remove a constraint that was never about
this boundary"* — and it is why the answer is **not** to raise the constant.

---

## 1. Provenance — where 4,350 actually comes from

`data/raw/capacity-deliverability/nyiso/nyiso.csv`, `metric == import_limit`:

| delivery_year | area | value_mw | source |
|---|---|---|---|
| 2022/2023 | G-J | 3,425 | LCR2022-Report.pdf |
| 2023/2024 | G-J | 3,425 | 2023-Locality-Bulk-Power-Transmission-Capability-Report.pdf |
| **2024/2025** | **G-J** | **4,350** | **2024-25-Locality-Bulk-Power-Transmission-Capability-Report.pdf p.7** |
| 2025/2026 | G-J | 4,500 | 2025-26-Locality-Bulk-Power-Transmission-Capability-Report_Final.pdf |

Exactly **one** row in the whole published table equals the model constant, and
it is the G-J locality row. Three corroborations that this is mis-attribution
rather than coincidence:

**(a) The published series moves; the constant does not.** G-J runs
3,425 / 3,425 / 4,350 / 4,500 across 2022/23–2025/26. The model applies 4,350
to *all three* solve years — including 2023, whose own capability-year value is
3,425. A genuine external limit would not be pinned to one internal locality's
2024/25 reading.

**(b) The constant's own justification argues from internal boundaries.** The
superseded comment justified the external cap by "the downstate import
interfaces (Dunwoodie-South 3.9 GW into NYC, cable-limited 1.65 GW into LI)
share upstream transmission" — i.e. an *internal* deliverability rationale
attached to an *external* seam limit. That is the mis-attribution stated in
prose. The same comment's arithmetic is also stale: it sums the border links as
"Upstate_West 3.0 + NYC 1.0 + Long_Island 1.2 = 5.2 GW", **omitting the
Capital_Hudson link (1.6 GW)** added later. The real border-link sum is 6.8 GW.

**(c) The cited source does not contain it.** The comment cited "NYISO Gold
Book; IRM/LCR studies". Extraction over all three Gold Books on disk
(2023/2024/2025, `data/raw/NYISO/*-Gold-Book-Public.pdf`) finds **zero** pages
naming a simultaneous import or simultaneous transfer limit, and **Table VI-1
(Existing Transmission Facilities) is redacted as Critical Energy
Infrastructure Information in every edition**. The Gold Book publishes ICAP
*capacity purchases* from external control areas (Table V-1: 1,584.7 MW net,
summer 2024) and IRM/LCR percentages (Table V-3) — neither is an energy
transfer limit. **NYISO publishes no aggregate external simultaneous import
limit in any source available to this repo.**

---

## 2. The measured envelope — 4,350 MW is falsified as an external bound

Two independent instruments, both already intaken and both rule-13 admissible
as *falsifiers* (posted ratings and measured flows, never dispatch inputs):

| year | P-32 scheduled max | EIA-930 metered max | h > 4,350 (sched) | h > 4,350 (metered) |
|---|---|---|---|---|
| 2023 | 7,078 | 5,929 | 865 | 287 |
| 2024 | 7,298 | 5,662 | 685 | 314 |
| 2025 | 6,727 | 5,872 | 388 | 145 |

**The P-32 sum is NYCA net interchange, not a double-count of the three HQ
rows.** Cross-validated on UTC-joined timestamps: r = 0.910 / 0.906 / 0.879
with bias +17 / −179 / −262 MW on means of 2,677 / 2,322 / 2,612 MW. A
double-count of HQ would show a bias of order +1,200 MW; it does not.

> **Method note (carried forward from nyiso-99).** The cross-validation must
> join on **UTC timestamps, never positionally**: the model clock is 8,760 h
> even in leap-year 2024 while P-32 posts all 8,784, so positional alignment
> shears the series after Feb 29 and degrades r from 0.906 to 0.774. The probe
> keeps two accessors on purpose (`_metered_utc` for the join,
> `_metered_net_import` for model-clock statistics).

The real system simultaneously imported **more than 4,350 MW in every one of the
three years**, by up to 1,579 MW metered and 2,948 MW scheduled. Whatever
NYCA's true external simultaneous transfer capability is, **4,350 MW is below
its measured lower bound.** Falsified.

---

## 3. Why the reconcile RETIRES the scalar instead of raising it

Rule 14's exception clause is live here and the prior charter named it
correctly: the naive measured replacement — the **sum of posted per-interface
P-32 limits, 10,575 / 10,715 / 10,450 MW** — is *precisely* "one of several
parallel paths our reduced network collapses into one link". It must not be
used literally.

But the misalignment does **not** extend to every path. The eleven `SCH -`
external schedules crosswalk to the model's four border links, and for the two
links whose tie sets are **point-to-point HVDC converters** there is no
parallel-path ambiguity at all — and the model is *already* at the posted
rating:

| model link | posted P-32 ties | posted MW | model TTC |
|---|---|---|---|
| NYC | PJM_HTP 660 + PJM_VFT 315 | **975** | 1,000 |
| Long_Island | PJM_NEPTUNE 660 + NPX_CSC 330 + NPX_1385 200 | **1,190** | 1,200 |
| AC seams (Upstate_West + Capital_Hudson) | HQ ×3 + OH-NY + PJ-NY + NE-NY | 8,410–8,550 | 4,600 |

The AC seams are the only lumped links, and they sit behind the **internal
Central-East chain the topology already represents** (Upstate_West →
Capital_Hudson at 2,850 MW, against a P-32 CENTRAL EAST - VC posted median of
2,865 MW — already reconciled).

So: the per-path object *is* identified and *is* already in the model. What is
not identified — and cannot be, given CEII redaction — is an aggregate scalar.
**Retiring it introduces no new number and removes a free parameter** (rule 22
`[R-DOF]`). The resulting aggregate is the border-link sum, **6,800 MW**, which
lies **inside** the measured admissible interval:

| year | lower bound (metered simultaneous max) | upper bound (posted-rating sum) | 6,800 | 4,350 |
|---|---|---|---|---|
| 2023 | 5,929 | 10,575 | **inside** | **outside** |
| 2024 | 5,662 | 10,715 | **inside** | **outside** |
| 2025 | 5,872 | 10,450 | **inside** | **outside** |

Rule 19 `[R-ONE-MECH]` reinforces this: shared-upstream-capacity limitation on
imports already has a mechanism in this topology (the internal interface
chain). The scalar was a second one, stacked on the first — and pointed at the
wrong boundary.

---

## 4. What the cap has actually been doing (the coupling, pre-registered)

Read off the committed keeper sidecars — **no re-solve**:

| year | h at cap | of those h21–h03 | of those h16–h18 | cap-bound hours where reality imported LESS |
|---|---|---|---|---|
| 2023 | 548 | 296 (54%) | 14 (3%) | 461/548 = **84%** |
| 2024 | 689 | 406 (59%) | 12 (2%) | 616/689 = **89%** |
| 2025 | 176 | 109 (62%) | 4 (2%) | 166/176 = **94%** |

**The cap does not bound import volume.** The ±2% monthly reconciliation band
(`NYISO_IMPORT_RECON_BAND_FRAC = 0.02`) is pinned at its **upper edge in 10 / 11
/ 11 of 12 months** in 2023 / 2024 / 2025. Monthly energy is therefore fixed by
the band; the cap only redistributes it across hours within the month.

This is the honest statement of the risk, and it cuts **both** ways:

- The cap binds almost entirely in the model's *wrong-phase* overnight peak
  (the nyiso-99 C3c attribution: model import peaks h21/h02/h22 vs a real
  h17/h16/h17). Retiring it lets the LP concentrate more of its fixed monthly
  quota overnight — **item-9 `r_hr` should get worse or stay flat.**
- Because volume is band-fixed, importing more overnight means importing
  **less** at peak, which *raises* peak duals. So the nyiso-86 sign warning
  ("forcing peak imports depresses peak duals") does **not** apply in reverse
  here: this arm is not forcing peak imports.

Both directions are pre-registered in
`docs/PREREG-nyiso100-simultaneous-import-retire-2026-07-30.md`. Per rule 1
`[R-STRUCT]`, the arm is **not** judged on whether either residual moves.

---

## 5. Scope boundary — what this finding does NOT do

The published **G-J locality limit is a real NYISO constraint that the topology
does not represent at its own boundary.** Retiring the scalar removes its only
(misplaced) representative. That is deliberate: a constraint on the internal
G-J boundary belongs in the `nyiso_nyc_lcr_tsl` / `nyiso_li_lcr_tsl` family — a
published locality limit applied to an internal link inside its design-condition
window — **not** on the external seam, and not as a by-product of this session's
single-delta arm. It enters the matrix as `U` (untested) and the NYISO lever
queue as a chartered follow-on.

Note the model's five-zone aggregation does not carry a clean G-J cutset
(Zone G sits in `Capital_Hudson`, H+I in `Lower_Hudson`, J is `NYC`), so that
follow-on owes its own rule-14 boundary reconciliation before it can be armed.

---

## 6. Reproduction

```
PYTHONPATH=.:src python scripts/probes/nyiso100_simultaneous_import_identification.py \
    --sections all --bundle results/calibration/nyiso99_demandfix
```

Requires `uv sync && python scripts/data/curate_capacity_deliverability.py` in a
fresh container (`data/clean/` is derived and gitignored).
