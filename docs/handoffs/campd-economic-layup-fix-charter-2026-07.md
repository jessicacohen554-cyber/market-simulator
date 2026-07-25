# CHARTER — CAMPD economic-layup discrimination (merit-order guard)

**Opened** 2026-07-25 by owner instruction, out of `neiso-63`
(`results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md`).
**Status:** OPEN — design NOT yet frozen. **Scope:** all six ISOs.
**Model assignment:** Opus or Fable (writes `scripts/lib/outage_detect.py`, a
core-infrastructure path — CLAUDE.md rule 27).

## 1. The defect

`scripts/lib/outage_detect.py::filter_revealed_outages` keeps a detected down
span when EITHER (a) the unit was down through ≥ `MIN_INMERIT_HOURS` (24) local
high-net-load hours, OR (b) it is a ≥ `FULL_STOP_OVERRIDE_DAYS` (5) full stop
below `FULL_STOP_OVERRIDE_CF` (0.02). The override's docstring states the
premise:

> *economic idling backs down but does not fully stop for weeks*

That premise fails for a gas CC priced out of merit for weeks — which is the
normal New England winter state and, per the cross-ISO screen, common
everywhere. A sustained economic layup satisfies **both** surviving branches, so
it is booked as a mechanical outage and its capacity is deleted from the
availability envelope.

Measured consequence: every ISO books **23–46 % of its CC capacity-year** as
outage against a real EFOR + planned-maintenance norm of ~10–15 %.

## 2. What the audit already settled (do not re-litigate)

- **The contamination is window-level, not unit-level.** Keeping only units with
  ≤3 windows/unit-year fixes the seasonal shape (monthly r +0.53→+0.84,
  +0.47→+0.75, +0.70→+0.96 for NEISO 2023/24/25) but collapses the level
  (410 vs 4,575 MW). Real outages live inside high-frequency units' records too.
  **Any fix must classify each window, not each unit.**
- **Common-mode / class-simultaneity discrimination is ruled out.** At every
  τ ∈ [0.30, 0.50] the seasonal correlation is *worse than applying no filter*,
  because genuine shoulder maintenance is itself strongly clustered.
- **The detector is not broadly broken.** It reproduces ISO-NE's published
  series in autumn (0.86–1.06×), when real maintenance dominates. The defect is
  specific to periods when units are out of merit.

## 3. The candidate mechanism

A **merit-order guard**: a window is not credited as an outage when the unit was
plausibly *out of merit* across it. The phenomenon is fuel-economic, so the
discriminator should be too.

Inputs available and admissible (rule 13 — delivered fuel prices are an
explicitly allowed physical input; the detector already carries class economic
guards `ST_GAS_CF_PEAK` and `SHORT_BASELOAD_CF`):

- delivered fuel price on the unit's own basis (the ISO's hub/citygate series
  the model already loads),
- the unit's heat rate (CAMPD marginal-HR artifacts exist per ISO),
- measured net load / the existing `high_load_mask`.

**Design questions the charter must settle before any build:**

1. What is the out-of-merit test — the unit's own SRMC against a fuel-only
   proxy for the marginal price, or against a class-relative rank? It must not
   use LMP, cleared price, or any MWh residual (rules 11/13/26).
2. Does the guard *drop* a window, *shorten* it to its genuinely-down core, or
   *reclassify* it into a separate non-outage column the fleet builder treats
   differently?
3. Per-class parameters or one ISO-agnostic rule? Rule 24 forbids a scalar
   fitted on one ISO's residual leaking into another's.
4. What happens where fuel-price data is thin (pre-2020, non-gas classes)?

## 4. Validation protocol — binding

- **Anchor: the published instrument, never the price residual.** The four
  DAM-first gates wired 2026-07-24 (`caiso_dam_outages`,
  `miso_native_outage_source`, `neiso_operable_capacity_availability`,
  `pjm_dam_availability`) give CAISO / MISO / NEISO / PJM a published
  outage/availability series. The corrected extract is scored against **that**,
  on both level and seasonal shape, at **no solve cost**. ERCOT and NYISO have
  no native gate and need a separately-identified cross-check before their
  extracts can be declared fixed.
- **Explicitly inadmissible:** trimming, scaling, or thresholding the extract
  until model *prices* match actuals. Rule 14 permits reconciling an input to
  its own published measurement; rule 13 forbids reconciling it to a dispatch
  outcome. The published outage MW is the target, the LMP residual is not.
- **Rule 22:** structural mechanism change ⇒ leave-one-year-out within
  2023–2025 before any keeper promotion.
- **Rule 15:** both arms registered whatever the verdict.
- **Rule 23:** any re-derived constant cites the source-data change, not a
  residual.

## 5. Blast radius — every keeper is implicated

The NEISO keeper's offer curves are demonstrably co-dependent on the
over-count: relieving it moved mean LMP −7 to −9 % and halved h>$200 (70→26 in
2023, 102→42 in 2025). That is the ERCOT-79 / nyiso-63 condition (rule 11 — the
estimate was silently compensating). Expect the same class of dependency
wherever a keeper was calibrated against the inflated envelope, and expect some
keepers to need re-tuning rather than a fix-in-place.

Sequencing note: the `neiso-62` operable-capacity denominator band
**[0.737, 0.849]** is **secondary to this charter**. Reconciling that overlay
matters only if it is load-bearing; the correct order is to fix the detector
first and let the fleet-grain published series serve as the *validation
instrument* it is suited to be, since a fleet aggregate cannot carry per-unit
availability.

## 6. Governance state while this charter is open

**Holdout spending is FROZEN across all ISOs**
(`frontend/data/backcast/holdout-freeze.json`, declared 2026-07-25, enforced in
`run_calibration_full.py::enforce_holdout_year_gate`). No validation or
locked-test year may be solved, scored, or registered until this charter reaches
a decision. Data intake is unaffected.

No marker or frontier has been withdrawn on this finding. Unlike nyiso-63 the
NEISO determination held and the fit improved, so the evidence does not yet meet
the withdrawal bar — but the NEISO frontier (2026-07-11) and calibration-complete
marker (2026-07-07) are **open questions** pending this charter.

## 7. Definition of done

Either:

- **Adopted** — corrected detector merged, each ISO's extract re-derived and
  scored against its published instrument, affected keepers re-audited on the
  corrected envelope (fix-in-place or re-tune, per ISO), freeze lifted by the
  owner; or
- **Closed with cause** — the merit-order guard is shown not to separate the
  populations (as common-mode was), the extract is confirmed fit for purpose on
  evidence, and the freeze is lifted.

A charter that stalls without either outcome leaves the freeze in place. That is
the intended failure mode, not an accident.
