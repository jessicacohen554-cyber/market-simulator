# GATESPEC — caiso-195 (lane 5): pumped-storage cited-physical parameters — six plants, one bundled arm, C3a-blind

**Authored by caiso-191 on 2026-08-11, BEFORE any lane-5 measurement exists.** These
gates are fixed and fail-closed. Authorization: owner ruling 7 (conditional), made
effective by caiso-191's adjudication verdict **GO WITH SCOPE RESTRICTIONS**
(`FINDING-caiso191-campaign-adjudication-2026-08-11.md` §3 — the two-fence
adjudication against caiso-140 §D/§G and caiso-141 §G, argued both ways). The
restrictions in §1 and §4 below ARE the conditions of the grant; a build that cannot
satisfy them has no authorization.

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

The favorable direction here is REDUCED belly pumping (caiso-140 §B measures the
model's unrestrained PS pumping ~700 MW through the Sep–Dec belly; less pumping
lowers belly λ). Every ambiguity rule below therefore resolves toward MORE pumping
capability, not less.

## 1. Objective and scope — what this arm IS and IS NOT

The model runs CAISO's 2,077.6 MW PS fleet as ONE aggregate NP15 `StorageUnit` with
fleet-average duration and RTE constants (`storage.py::load_eia860_pumped_storage`;
caiso-127 §B2's "one entirely unrestrained arbitrageur"). This arm replaces that
aggregate with per-plant CITED-PHYSICAL parameterizations for the six plants —
Helms, Eastwood, Gianelli, Hyatt, Thermalito, O'Neill:

* per-plant **pump-power ratings** (public FERC / CEC / EIA-860 documents);
* per-plant **durations** (energy capacity from cited reservoir/license figures);
* per-plant **zone assignment** — **pure geography** (plant location vs the model
  zone map), never an electrical or economic choice;
* **Hyatt's primarily-conventional-release mode**, expressed ONLY as static cited
  parameter bounds INSIDE the storage block (e.g. its cited pump-back capability
  rating, which the public record shows is the minority mode — caiso-141 §B's own
  words: "Hyatt is primarily a conventional-release plant; pump-back is the minority
  mode"). Hyatt is NOT removed from the storage block, and NO energy is re-allocated
  into the conventional-hydro budget under any shape.

**ONE BUNDLED ARM** (single mechanism, rule 19): the per-plant PS parameterization,
whole. No per-plant sub-arms, no sequential unbundling, no subset chosen after a
result.

**What this arm adds: ZERO MW.** Total fleet capability reconciles to the EIA-860
aggregate (G-AGG); the arm re-attributes physical parameters, it does not add
supply. That fact is load-bearing for the caiso-140 §G fence discharge (FINDING §3).

## 2. Exogenous instrument closure

Public FERC documents (license/relicensing filings, e.g. the Helms docket), the CEC
power-plant database, EIA-860 — all citable by document. **FORBIDDEN: any LMP/price
series, any measured hourly/daily/monthly hydro or PS OUTPUT series, any model
output, any residual.** The caiso-141 wall is untouched: this arm claims NO intake
and builds NO shape.

## 3. Numeric gates — each with its written anchor

| gate | bar | anchor |
|---|---|---|
| **G-CITE** | EVERY parameter value (each plant's pump rating, duration, zone, Hyatt's pump-back bound) is committed in the PRECHECK **before any solve**, each with its public document citation, quoted so a reviewer reproduces the table from the citations alone. No value from any model output; no post-solve adjustment. | Rule 13's admissibility test: static physical plant parameters regenerate for a forward year from the same public documents and respond to changed conditions (re-rating, retirement). Rule 5 `[R-NO-MAGIC]`: every value cited. |
| **G-ZONE** | Zone assignment is mechanical geography: plant coordinates/county vs the model zone map, shown in the PRECHECK. Any zone choice that requires an economic argument FAILS this gate. | The model's own zone-assignment convention (`build_zone_lookup`) — a pre-existing repo mechanism; geography is the only zero-DOF assignment axis. |
| **G-NOSHAPE** | The arm's diff contains NO time-profile input for PS: no hourly water state, no monthly-to-hourly allocation, no assumed pumping schedule, no SOC trajectory input. The LP remains the unrestrained optimizer within the cited static bounds. | caiso-141 §G verbatim: an hourly PS shape derived from monthly nets, the model's own profile, or any assumed/fitted allocation is a rule-13 outcome-pin wearing a data costume. Owner ruling 4 re-affirmed the wall. |
| **G-AGG** | Σ per-plant generating capability reconciles to the EIA-860 PS aggregate (2,077.6 MW basis) within the documented source differences, each difference itemized in the PRECHECK; the arm's total may not EXCEED the EIA-860 sum by more than the itemized, cited differences. Zero MW of net supply added. | EIA-860 is the model's own fleet basis (the shipped loader) — a pre-existing repo input; conservation against it is arithmetic, not judgment. |
| **G-DOF** | Every parameter enters identified `measured` (cited); no fitted scalar anywhere in the arm; the ledger does not increase. `PUMPED_STORAGE_DURATION_HOURS` / `PUMPED_STORAGE_RTE` stay untouched for every other ISO (rule 25); the per-plant table is registered per rule 24 (in config/constants with citation comments, its matrix row added in the same PR per rule 28(c)) — no hardcoded dict in a `data/` module, no env knob. | Rules 21/24/25 — standing; the committed ledger 11/8 is the baseline. |
| **G-ENGAGE** | The arm's LP differs from control and the per-plant units are present in the built storage fleet (verified by a fleet-build probe, the `fleet_only=True` machinery — a build, never a solve). A bit-identical arm ⇒ INERT, reported as such. | caiso-188 §7 item 5 (check the data the gate resolves through), and the G-CTRL precedent for what "inert" looks like. |

## 4. Conservative-default rules (bias AGAINST the C3a-favorable direction)

1. Where public sources conflict on a pump rating or duration, take the value that
   preserves MORE pumping capability (higher pump rating, longer duration) — i.e.
   closer to the incumbent unrestrained aggregate. Reduced pumping is the flattering
   direction and never wins an ambiguity.
2. **Hyatt's mode carries the strongest citation burden.** Reclassifying pump-back to
   a minority-mode bound REMOVES pump capability — the flattering direction — so the
   bound must be a directly cited public figure (FERC/CEC/DWR published rating or
   license term). If the citation is not airtight, **Hyatt keeps full PS treatment**
   (the conservative default), and the arm proceeds without the Hyatt component.
3. If any component turns out at build time to require a synthesized hourly shape or
   an energy re-allocation into conventional hydro, that component is DROPPED; if it
   cannot be separated from the bundle, the whole arm is killed (G-NOSHAPE is
   structural, not negotiable).

## 5. Kill criteria

* Any parameter uncited at PRECHECK time ⇒ that component out; core plants
  (Helms/Eastwood, 60.3 % of the fleet) uncitable ⇒ arm dead, null-FINDING.
* Any shape/profile input in the diff ⇒ session void (caiso-141; rule 13).
* Any zone assignment argued on anything but geography ⇒ fail.
* DOF increase or any fitted scalar ⇒ automatic fail.
* Acceptance may not cite C3a in either direction (§0).

## 6. A/B protocol

* **CONTROL** — the caiso-188 keeper recipe re-solved per integration protocol §3
  (`--replay-bundle results/calibration/caiso188_d1_micseam`;
  capacity-deliverability partition materialized, log-verified; `hydro_ror_split`
  explicitly False, disclosed). Ratified tolerance met, noise floor quoted first.
* **ARM** — control + the per-plant PS parameterization (one bundled mechanism).
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms sequential
  (rule 12); both registered (rule 15) with `legitimacy_diagnostics.json`.
* Acceptance basis: **citation integrity (G-CITE/G-ZONE/G-NOSHAPE/G-AGG/G-DOF) +
  engagement (G-ENGAGE), C3a-blind.**
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is
  the six-plant cited-physical PS parameterization; no other input differs."

## 7. Required artifacts

* `results/calibration/PRECHECK-caiso195-ps-physical-<date>.md` — the full cited
  parameter table, committed before any solve.
* Record: `results/calibration/_caiso195_ps_citations.json` — per-plant values,
  document citations, the G-AGG reconciliation arithmetic.
* Run bundles `caiso195_l5_control`, `caiso195_l5_psphys`.
* `results/calibration/FINDING-caiso195-ps-physical-<date>.md` with gate tally, the
  direction-hazard clause quoted, the caiso-140/141 fence discharge restated, and
  the matrix duties (b)+(c) in-session (the new registered parameter surface needs
  its matrix row in the same PR).
