# CHARTER — CAMPD economic-layup discrimination (merit-order guard)

**Opened** 2026-07-25 by owner instruction, out of `neiso-63`
(`results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md`).
**Status:** ADOPTED-AS-IMPROVEMENT (owner verdict 2026-07-26, §8) — freeze HELD.
**Scope:** all six ISOs.
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

## 3a. FROZEN DESIGN (neiso-64, 2026-07-25) — owner sign-off 2026-07-25

Answers to all four questions, with the no-solve evidence each rests on. Probes
read committed artifacts only (`campd-unit-outages-<ISO>.csv`,
`campd-unit-level/<ST>_<YYYY>.parquet`, `gas_basis_by_iso_month.csv`,
`gas-prices/henry_hub_{daily,monthly}.csv`,
`_processed-legacy/eia923_monthly_fuel_costs.parquet`, and each ISO's published
outage instrument). No LP solve was run and no keeper was touched.

### D1 — the out-of-merit test: SRMC vs the *revealed marginal cost* (Q1 option 1)

Per unit `u`, hour `t`:

* **Measured heat rate** `HR_u = Σ heatInput / Σ grossLoad` over the unit's
  running hours (`CF ≥ REAL_RUN_CF`), pooled over the years of the derive
  invocation. CAMPD-measured; clipped to `[4, 20]` MMBtu/MWh against meter noise.
  A unit with fewer than `MIN_REAL_RUN_HOURS` (24) running hours has no
  identified heat rate and is excluded (see D4).
* **Delivered fuel price** `px(u, t)`, by the unit's own fuel:
  * *gas* — the ISO's delivered hub: measured Henry Hub **daily** re-centred on
    the measured Henry Hub **month**, plus the ISO's measured monthly basis
    (`gas_basis_by_iso_month.csv`; all six ISOs, 2015–2026). Mean-preserving at
    the monthly hub level, so only the within-month shape is added.
  * *coal* — F923 delivered, plant-month → state-month (volume-weighted) →
    ISO-month (volume-weighted).
  * *anything else* (oil, other) — no series; unit excluded (D4).
* `SRMC_u(t) = HR_u × px(u, t)`. **No VOM adder**: a per-class additive would be
  a free parameter (rule 20) with no discriminating power, since every unit is
  ranked through the identical construction.
* **`RCC(t)` — the revealed clearing cost** — the capacity-weighted
  `RCC_PCTL = 0.90` quantile of `SRMC` over the units **measured running** at
  `t` (`CF ≥ REAL_RUN_CF`), **excluding cogeneration** (measured non-zero CAMPD
  `steamLoad` — heat-driven, not economically dispatched, so it carries no merit
  information; keyed on the measured quantity, not a class name, per rule 17).
  p90 rather than the max so a single reliability-committed unit cannot set the
  band.
* A window's **out-of-merit share** = the fraction of its hours with
  `SRMC_u(t) > RCC(t)`.
* **A window is ECONOMIC LAYUP iff its out-of-merit share ≥ `OOM_FRAC = 0.90`**
  — "for essentially the whole window, cheaper capacity than this unit was
  setting the revealed margin."

Every input is measured CEMS operation or a delivered fuel price. There is no
LMP, no cleared price, no cleared quantity and no residual anywhere in the
construction (rules 11/13/26).

**Why this and not the alternatives.** The self-referential variant (compare the
window's fuel price to a percentile of the unit's *own* running-hour price
distribution) was probed first and is **rejected**: the unit's heat rate cancels
out of a within-unit percentile comparison, so it can only see the
*fuel-cost-blowout* half of out-of-merit. It fixed NEISO DJF but left JJA
untouched (1.93× → 1.93×) and, in the mild 2024 winter, its NEISO gain sat
**inside the placebo band** (r +0.55 vs placebo p95 +0.56). Cross-unit ranking
against `RCC` is what puts the heat rate back in, and it is the only variant
that moves all four seasons.

**Evidence — NEISO 2023/24/25, detector ÷ published ISO-NE Section 3 line C:**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| baseline level / monthly r | 1.52× / +0.53 | 1.57× / +0.47 | 1.22× / +0.70 |
| guard on, level / monthly r | **1.36× / +0.71** | **1.29× / +0.61** | **0.92× / +0.78** |
| placebo p95 (same GW-days dropped at random, 30 draws) | +0.63 | +0.55 | +0.78 |

Level and shape improve **together** — unlike unit-frequency filtering (shape
+0.84 but level collapsed to 410 MW) and unlike common-mode (shape worse than no
filter). The guard beats the placebo p95 in 2023 and 2024 and sits exactly at it
in 2025 (the year whose baseline shape was already good), so the gain is
discrimination, not the mere removal of MW.

**Positive control — the two populations land in the two buckets ISO-NE itself
publishes.** ISO-NE's Morning Report Section 3 reports mechanically unavailable
capacity (`gen_outages_reductions_mw`) *separately* from available-but-not-
committed capacity (`uncommitted_available_gen_nonfast_mw`) — i.e. the published
instrument measures the layup population directly. Monthly correlation, 2023 /
2024 / 2025:

| window set | vs published OUTAGES | vs published UNCOMMITTED |
|---|---|---|
| baseline (all windows) | +0.53 / +0.47 / +0.70 | +0.34 / +0.45 / +0.48 |
| **KEPT** (guard: mechanical) | **+0.71 / +0.61 / +0.78** | +0.08 / +0.28 / +0.31 |
| **VETOED** (guard: layup) | −0.26 / +0.01 / +0.24 | **+0.77 / +0.71 / +0.67** |

The vetoed windows are anti-correlated (or uncorrelated) with published outages
and strongly correlated with published uncommitted-available capacity. That is
the charter's identification requirement met against a published instrument, not
a residual.

### D2 — RECLASSIFY, not drop and not shorten

The vetoed windows are a real, separately-measured population (D1 positive
control), so the information is preserved rather than discarded:

* the mechanical extract `campd-unit-outages-<ISO>.csv` keeps only the
  non-vetoed windows — an economically laid-up unit **is available**, and the LP
  must decide not to run it on its own economics;
* the vetoed windows are written to a labelled companion
  `campd-unit-outages-layup-<ISO>.csv`, same schema plus the measured
  `out_of_merit_share` that carried the call, which **no loader reads by
  default** — an audit artifact and the validation series, following the
  existing `-e923-` / `-maxgen-` / `-short-` companion convention.

**Not shortened.** There is no evidence of a "genuinely-down core" inside a
layup window; a sub-window classifier would be a fitted answer key with nothing
to identify it against. **No new LP mechanism** (rule 18): mechanical
unavailability stays in the outage overlay, and economic non-commitment stays
where it already lives — the dispatch economics.

### D3 — one ISO-agnostic, class-agnostic rule

Both knobs (`RCC_PCTL`, `OOM_FRAC`) are structural percentiles over per-ISO
self-referential distributions; **no scalar fitted on one ISO's residual is
carried into another** (rule 24). Class enters only through two *physical*
facts, not tuning: cogeneration is excluded from the `RCC` panel (measured
`steamLoad`), and the unit's fuel selects its price series. The knobs are
identified **jointly across the ISOs with published instruments**, never per
ISO, and only against those published outage series — rule 14 reconciliation of
an input to its own measurement, never rule 13 fitting to a dispatch outcome.
They re-derive only on a source-data change (rule 23). The window-grain
out-of-merit share is close to binary (NEISO: p25 = 0.00, p75 = 1.00), so
`OOM_FRAC` is not load-bearing — 0.70 → 1.00 moves the NEISO veto count only
560 → 412.

### D4 — thin fuel data: INERT, fail-safe, no fabricated basis

The guard can only ever **remove** windows, so every gap degrades to
current behaviour:

* no measured heat rate (< `MIN_REAL_RUN_HOURS` running hours) → unit excluded
  from the `RCC` panel **and** from the guard; its windows are kept.
* no delivered price for the unit's fuel (oil, "other", a coal plant outside
  every F923 ladder rung, a year outside the basis table) → same exclusion.
* an ISO-year with no `RCC` hours at all → extract byte-identical.
* **Henry Hub is never substituted for a missing ISO basis.** For NEISO the
  basis *is* the signal; a Henry-Hub fallback would silently switch the test off
  while appearing to run.

### Gate

`MERIT_ORDER_GUARD_ENABLED = False` in `scripts/lib/outage_detect.py`, surfaced
as `--merit-order-guard` on `scripts/data/derive_campd_unit_outages.py`.
Byte-inert when off, **proven at full extract scale**: a full 2018–2026
re-derive without the flag reproduces every committed extract blob exactly
(NEISO `a95c0928`, CAISO `3dc01fae`, NYISO `181fefb9`, ERCOT `b4b48f5a`).

## 4. Validation protocol — binding

- **Anchor: the published instrument, never the price residual.** The four
  DAM-first gates wired 2026-07-24 (`caiso_dam_outages`,
  `miso_native_outage_source`, `neiso_operable_capacity_availability`,
  `pjm_dam_availability`) give CAISO / MISO / NEISO / PJM a published
  outage/availability series. The corrected extract is scored against **that**,
  on both level and seasonal shape, at **no solve cost**. ERCOT and NYISO have
  no native gate and need a separately-identified cross-check before their
  extracts can be declared fixed.
  **Amended 2026-07-25 (owner):** ERCOT *does* carry a published anchor —
  `data/raw/ercot-thermal-dam-availability.csv` (60-day DAM disclosure, daily
  class `rating_mw − live_mw`), already consumed by the ERCOT overlay. It is
  adopted as ERCOT's validation series **with the caveat** that DAM
  offered-capacity conflates mechanical unavailability with a unit that simply
  did not offer, so it carries some layup itself. **NYISO alone remains
  unverified.**
- **Explicitly inadmissible:** trimming, scaling, or thresholding the extract
  until model *prices* match actuals. Rule 14 permits reconciling an input to
  its own published measurement; rule 13 forbids reconciling it to a dispatch
  outcome. The published outage MW is the target, the LMP residual is not.
- **Rule 22:** structural mechanism change ⇒ leave-one-year-out within
  2023–2025 before any keeper promotion.
- **Rule 15:** both arms registered whatever the verdict.
- **Rule 23:** any re-derived constant cites the source-data change, not a
  residual.

**Scope caveat on level ratios (2026-07-25).** The CAMPD extract covers only the
CEMS-reporting fossil fleet (coal / CC / gas-steam); several published series
are whole-fleet (MISO, PJM, CAISO). A level *ratio* is therefore only
interpretable where the thermal-only extract **exceeds** a whole-fleet published
total — an unambiguous over-count, as in NEISO. The robust cross-ISO axis is the
**monthly correlation** against the published series, plus the placebo test.

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

## 8. VERDICT — ADOPTED-AS-IMPROVEMENT, freeze HELD (owner, 2026-07-26)

The owner adopted the merit-order guard as a **genuine measured improvement,
not a closure of the neiso-63 finding**, choosing adopt-and-hold over
adopt-and-lift and over close-with-cause:

- **Adopted.** The guard patches merge (still default-off,
  `MERIT_ORDER_GUARD_ENABLED = False`); each ISO's committed extract is
  re-derived guard-on and committed together with its
  `campd-unit-outages-layup-<ISO>.csv` companion — the availability envelope
  every keeper reads now excludes the reclassified economic-layup windows.
- **Freeze HELD.** `frontend/data/backcast/holdout-freeze.json` stays
  `active=true`. The residual over-count survives the guard — NEISO 2023–24
  still runs 1.29–1.36× a whole-fleet published total on a thermal-only
  extract — so out-of-training years remain preserved until that residual is
  either explained (scope) or fixed. Only the owner lifts the freeze; §6's
  clause that no session lifts it by inference stands.
- **Keeper re-audits proceed** (§5 blast radius): NEISO is done
  (fix-in-place, `2026-07-25-neiso-64-meritguard-a1`); ERCOT / PJM / MISO /
  CAISO / NYISO replay their keepers in-sample (2023–2025, one bundle,
  rule 16) on the corrected envelope, both arms registered (rule 15).
- **Definition-of-done status:** the §7 "Adopted" leg is satisfied except its
  final clause ("freeze lifted by the owner"), which is deliberately deferred
  to the residual-over-count investigation. The charter stays open on that
  single item plus the outstanding re-audits.

**Amendment to the CAISO re-audit cell (2026-07-26, caiso-123).** The CAISO
"RE-TUNE REQUIRED" verdict (`2026-07-26-caiso120-meritguard-a1`, C3a-2025
+10.0 → +11.1 %) was measured against a confounded A0: the CAISO extract was
derived-not-committed until 07-24, the keeper's committed bytes carry a
session-local PARTIAL derivation, and the 07-24 backfill (#2842/#2844)
committed a heavier FULL derivation independent of — and two days before —
the guard. Same-HEAD isolation puts the guard's own effect at **−0.18 %
(favourable)** and the extract-content change at **+1.24 % λ / CC_REGULAR
−0.49 TWh / import +0.42 TWh**. The re-tune trigger is accordingly
**withdrawn as stated and re-derived**: the keeper's C3a-2025 PASS was
calibrated against a non-reproducible partial envelope (rule-11 class), and
on any honest full derivation C3a-2025 fails by ~+1.1 pp. Sequencing of the
CAISO re-tune against the §8 residual-over-count investigation (the
extract's absolute level, freeze lift condition) is an owner call. Full
record: `results/calibration/FINDING-caiso123-c3a-drift-attribution-2026-07-26.md`.

**MISO re-audit cell RESOLVED (2026-07-26, miso-93): RE-TUNE REQUIRED.** Arm
`2026-07-26-miso-93-meritguard-a1` (2023/2024/2025, one bundle) takes the
`2026-07-25-miso-88-egrid-hr` keeper from `CALIBRATED-WITH-CAVEATS` to
**`NOT-YET`** on one newly-failing gate: **C3a-2024 −8.7 % → −10.1 %**, past the
±10 % veto by 0.1 pp. C1/C2/C4/C5a/C6/C7/C8 hold; C3b/C3c stay ledgered
(C3b-2025 0.208 → 0.214). Unlike the CAISO cell this verdict is **not**
confounded: the MISO extract blob is byte-identical across the keeper's own
`git_sha`, changes exactly once (at `6a8f285`) and not since, and a same-HEAD
isolation probe on the failing year puts the post-keeper **code** drift at
**exactly $0.000** — A0′ reproduces the keeper's committed sidecar to three
decimals — so the guard/extract accounts for **100 %** of the −$0.445
(−1.38 pp) move. Direction and mechanism are as this charter predicted: the
guard removes **11,614 GW-days and adds zero**, **73.5 % of it ST_GAS**, and the
added supply lowers the clearing price (C8 ST_GAS forced share rises in step,
still grounded). A rule-11 discovered-bug signal — the keeper's offer curves
were compensating for the inflated envelope, as at NEISO but milder (−1.4 pp vs
−7…−9 %). **No tuning applied; MISO's ledger is 3/3 saturated, so the re-tune
must close by structure.** Keeper designation unchanged (owner call). Evidence:
`results/calibration/FINDING-miso93-keeper-reaudit-meritguard-2026-07.md`;
charter `docs/handoffs/miso-93-keeper-reaudit-charter-2026-07.md`. Remaining
open re-audit cells: **ERCOT, NYISO** (PJM targets `pjm121_ccbelt` per §3e).

## 9. Residual-over-count investigation — CLOSED on evidence; the freeze-lift decision is now the owner's

The single item §8 deferred the freeze to. Three ordered steps were set by
`results/calibration/FINDING-neiso66-overcount-rootcause-2026-07-26.md` §6; all
of the *measurement* is now done, and no LP solve was run for any of it.

| step | status | evidence |
|---|---|---|
| 1 — re-measure NEISO on a sound published-side build | **DONE, PASSED** | neiso-66 §5b — the residual tracks ISO-NE's published `uncommitted_available_gen_nonfast_mw` at +0.70 to +0.85 and is **anti**-correlated with published outages (−0.85 to −0.86) |
| 2 — test the commitment-economics mechanism directly | **DONE, NEGATIVE** | `FINDING-neiso67-commitment-test-2026-07-26.md` — per-unit AUC 0.47–0.57 across 18 configuration-years, **below** the marginal test in every one; on the seam population the sign inverts (AUC 0.39–0.41, and 89–93 % of seam days already repay the published start cost); the commitment band identifies nothing against the published series (−0.51 / +0.26 / +0.05) |
| 3 — disposition | **OWNER DECISION, recommendation below** | — |

**What is now settled.** The residual over-count is a **definitional seam**
(CNOG/ISO-NE publish *unavailability*; the CEMS detector measures
*non-operation*), confirmed against a published instrument — and it is **not
recoverable by any discriminator the admissible inputs support**. Both of the
re-audit's original candidate directions were refuted by measurement
(neiso-66 §3, §4); the marginal test has no power on this population (§4); and
the commitment test now has none either, with its only novel band
(`0 ≤ R < 1`) carrying no signal and rule 19 `[R-ONE-MECH]` forbidding it
stacking on the guard that already owns the `R < 0` half.

**Recommendation to the owner — carry the seam explicitly, then lift.**

- Take **disposition (b)**: leave the availability envelope alone. Option (a),
  a commitment-aware second discriminator in the detector, is not buildable on
  the evidence (neiso-67 §6) and would be a mechanism with no measured
  discriminating power — what rule 1 `[R-STRUCT]` forbids reaching for.
- The §7 **"Closed with cause"** leg is the one that now fits the residual: the
  over-count is explained, quantified, bounded to a definitional scope
  difference, and shown not to be closable by a detector change. That is a
  cause, not a stall.
- **The freeze-lift is still the owner's act and no session takes it by
  inference** (§6, and `holdout-freeze.json` `lifts_when`). What has changed is
  that its stated condition — "the residual is explained or fixed" — is now met
  on the *explained* branch, with the measurement committed and re-runnable.

**Not settled, and deliberately left open:** whether the seam should be closed
on the LP side rather than the detector side (neiso-66 §5b argues on rule-1
grounds that these units belong in the envelope as *available*, with the LP
declining them on its own commitment economics; CAISO's `caiso_ra_mustoffer`
already owns that capacity's commitment, so rule 19 makes it a replace-or-
reconcile question, never a stack). That is a separate lane on a different
instrument and is **not** a freeze-lift blocker.
