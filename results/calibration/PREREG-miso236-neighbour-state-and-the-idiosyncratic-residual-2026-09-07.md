# PREREG miso-236 — is MISO's missing seam variation a MISSING MEASURED INPUT, an UNUSED one, or genuinely IDIOSYNCRATIC? And is the model's own seam residual a diurnal template?

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a pre-registration
and correctly forfeited its right to close or re-open anything on its own numbers; miso-235 did
and was entitled to close a queue item on its own rule. This session follows miso-235.

**Keeper `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF 41/2. **MISO HAS NO FAILING
GATE**, and there is no rubric failure anywhere in the program, so nothing here targets one.
Rule 22: 2023–2025 only; MISO holds no `complete` marker and no out-of-training year will be
solved, scored or registered. MISO carries exactly ONE registered run (rule 15).

**ZERO LP IS PLANNED.** No `ScenarioConfig` field is created or armed, no bundle is produced, no
run is registered or pruned, the keeper is not replayed and not touched. If a measurement below
licensed a screen, that screen would be chartered in a successor with its own PREREG — it is
**not** chartered here.

---

## 0. Lever-queue selection (rule 28(a))

This session takes the handoff's **item 2** — *"THE THREE NON-PJM SEAMS' MISSING IDIOSYNCRATIC
VARIATION (miso-235's named successor)"* — together with its **item 3** (PJM's residual price
alignment), because **one instrument answers both**: each is a question about what explains a
seam residual, on the same OLS decomposition of the same committed artifacts.

The handoff's own instruction on item 2 is the charter and is quoted so it binds:

> *"THE FIRST QUESTION IS A DATA QUESTION AND IT IS ZERO-LP: does a measured non-price series
> with a forward analogue exist for MISO's DIBAs — scheduled/net-scheduled interchange, tie or
> neighbour outage windows, neighbour state? Settle that BEFORE proposing anything. A noise term,
> a variance inflator, or anything tuned to this sigma is rule-13 forbidden."*

And on item 3:

> *"the reconstruction has exactly two inputs (the ladder-vs-spread merit test and the measured
> (month x hod) deliverability envelope), and the envelope is a deterministic diurnal template —
> price-aligned by construction — where the real seam's non-spread variation is idiosyncratic.
> Measure it; do not assume it."*

**§2 is the settlement of item 2's data question and §3 measures item 3's named hypothesis.**
Handoff item 1 (the C3c charter) and item 4 (CC_REGULAR 2024→2025 shape) are **not** taken and
stay where they are filed.

### 0a. What was established BEFORE this PREREG was written — disclosed, not claimed

Four facts, all **existence reading** of on-disk data and code. **No adjudicating quantity is
among them**, and none is a statistic about a seam residual:

1. `data/raw/eia-930-interchange/MISO interchange hourly.parquet` — the measured seam record the
   lane already scores against — carries **ten** DIBAs: `AECI IESO LGEE MHEB PJM SOCO SPA SWPP
   TVA SIKE`. `MISO_SEAM_DIBA` (`src/market_sim/model/interchange/spec.py:1237`) pools them into
   the keeper's four seams: PJM ← (PJM, IESO); SPP ← (SWPP, SPA); South ← (SOCO, TVA, AECI, LGEE,
   SIKE); Manitoba ← (MHEB).
2. `data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet` (2023–2025 both halves present) carries
   **62 US balancing authorities**, each with hourly `Demand (MW) (Adjusted)`, `Net Generation
   (MW) (Adjusted)` and **net generation by fuel** (Wind, Solar, Hydropower and Pumped Storage,
   Coal, Natural Gas, Nuclear, …), on both a local and a UTC clock. The 62 include **`PJM`,
   `SWPP`, `SPA`, `SOCO`, `TVA`, `AECI`, `LGEE`** and `MISO` itself. They do **not** include
   `MHEB`, `IESO` or `SIKE` — MHEB and IESO are Canadian entities outside EIA's US-BA universe.
3. `data/raw/MISO/` holds only Potomac SOM/IMM **PDFs** (payload gitignored). There is **no MISO
   scheduled- or net-scheduled-interchange series on disk**, and misoenergy.org's workbooks are
   allowlist-blocked at HTTP 403 (`docs/multi-iso/miso-data-audit.md`). The only per-DIBA MISO
   seam series this repository holds is the EIA-930 **actual** interchange in (1).
4. The MISO `BALANCE` rows' `Local Time at End of Hour` is the **same wall clock** as the
   interchange parquet's `local_time` (both read `01/01/2023 1:00:00 AM` for the first 2023 hour),
   and the BALANCE file carries the matching `UTC Time at End of Hour` — so a local→UTC map can be
   read **from the data** for MISO and every neighbour BA joined on UTC, with no timezone guessed.

Fact (3) is the reason this session's answer to the handoff's "scheduled/net-scheduled
interchange" limb is settled by **absence** rather than by measurement, and it is stated here
before anything is computed.

### 0b. Basis discipline (carried from miso-234 §0a / miso-235 §0b — it bit a first draft)

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. The lane's scored basis; the price `P` wherever a price appears below.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the basis
  of **every regressor** in the §1 OLS, exactly as miso-235 §3 fixed it.

They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured
decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

---

## 1. The object, and the provenance gate that must clear before any new number is read

The object is `r_meas,s(t)` — the **measured** seam flow's residual from the miso-235 §3 OLS,
per seam `s` and year:

    x_s(t) = alpha_s + beta_s * z_s(t) + r_s(t)

with the pre-registered regressors `z_s`, unchanged and **fixed here** (all DA basis, sign
convention import-positive): PJM ← Indiana DA **−** PJM border; SPP ← Indiana DA **−** SPP NORTH
hub DA; South ← Indiana DA (level); Manitoba ← Indiana DA (level).

This residual carries **78.5 / 79.4 / 83.5 %** of MISO's interchange σ deficit, **100 %** of it on
SPP, South and Manitoba (miso-235 §4). Its σ is 43–63 % of the measured seams'.

**PROVENANCE GATE, fixed ex ante.** The probe recomputes miso-235's `sigma_resid_measured_mw` and
`sigma_measured_mw` for all four seams and all three years on its own code path. **If any value
differs from the committed `_miso235_seam_variance_decomposition_phase0.json` by more than
0.5 MW, the instrument is declared BROKEN and NOTHING in §2 or §3 is read or published.** A
repair measured against itself is the miso-235 §1 standard and this session holds itself to it.

## 2. Q-A — THE ADJUDICATING QUESTION. Missing input, unused input, or idiosyncratic?

### 2a. Census (REPORTED, non-adjudicating)

Per seam: which of its `MISO_SEAM_DIBA` members appear in EIA-930 BALANCE for 2023–2025, their
hourly coverage of the fixed 8,760 grid, and the share of that seam's measured **gross** flow
magnitude (`Σ|mw|` over its DIBAs) carried by the covered members.

A seam **HAS A NEIGHBOUR-STATE INSTRUMENT** iff, in **all three years**, at least one of its DIBAs
is present with **≥ 95 %** hourly coverage **and** the covered DIBAs carry **≥ 50 %** of that
seam's gross flow magnitude. A seam without one is reported as **NO INSTRUMENT** and §2b is not
computed for it — its leg of item 2 is then answered by data absence, not by a statistic.

### 2b. The three-way variance split (THE DELIVERABLE)

Two nested OLS blocks on `r_meas,s(t)`, on the same `ok` hour mask, every regressor z-scored:

* **Block B — MISO-OWN STATE (information the model ALREADY HAS).** `nl_MISO(t)` = MISO
  `Demand (Adjusted)` − Wind − Solar; `vre_MISO(t)` = MISO Wind + Solar. Both are EIA-930 BALANCE
  MISO rows. **The model already carries this information** (measured zonal load and measured VRE
  CFs are keeper inputs), so variance Block B explains is variance the model *could* produce and
  does not.
* **Block A — NEIGHBOUR STATE (information the model DOES NOT HAVE).** Summed over the seam's
  **covered** DIBAs: `nl_nbr,s(t)` = Σ(Demand − Wind − Solar); `vre_nbr,s(t)` = Σ(Wind + Solar);
  `hyd_nbr,s(t)` = Σ(Hydropower and Pumped Storage).

`R²_B` = R² of `r_meas,s` on B alone. `R²_AB` = R² on A ∪ B. **`ΔR²_A = R²_AB − R²_B`** is the
incremental explanatory power of information the model does not have.

**THE HYDRO LIMB IS DECLARED WEAK HERE, BEFORE IT IS COMPUTED.** Neighbour hydro is dispatchable
and can itself respond to the tie, so it is Block A's least cleanly admissible member. Block A is
therefore fit **twice** — with and without `hyd_nbr` — and **the GATED value is the NO-HYDRO one**
(the conservative block). The with-hydro value is reported beside it and can move no verdict.
Fixed here so the choice cannot be made after seeing either number.

**DECISION RULE, per seam, fixed ex ante:**

* **ADMISSIBLE NEIGHBOUR-STATE DRIVER IDENTIFIED** iff `ΔR²_A ≥ 0.10` in **all three years**.
* **NO NEIGHBOUR-STATE DRIVER** iff `ΔR²_A < 0.05` in **all three years**.
* **MIXED** otherwise — reported as mixed, closing and licensing nothing.

**DECISION RULE D-4, the idiosyncratic floor, fixed ex ante:** with `U_s = 1 − R²_AB`, a seam
whose `U_s ≥ 0.75` in **all three years** is declared **PREDOMINANTLY IDIOSYNCRATIC**: its
non-price residual is not reachable by *any* measured-state input of this class, and that seam's
leg of handoff item 2 **closes as NO ADMISSIBLE MECHANISM**.

**FRAGILITY QUALIFIER (confirmation leg, fixed ex ante).** Block coefficients are fit on one year
and `ΔR²_A` evaluated on the other two (mean out-of-year value). A seam reading **ADMISSIBLE** is
**QUALIFIED AS FRAGILE** if its mean out-of-year `ΔR²_A` is below **0.5 ×** its mean in-year
`ΔR²_A`. A fragile verdict **closes nothing and licenses nothing** — it is reported as a
per-year fit artifact.

### 2c. The rule-13 `[R-MEASURED]` admissibility argument, stated BEFORE the numbers

Neighbour **net load** and neighbour **VRE** pass the rule-13 test on their face and the argument
is fixed here so it cannot be assembled to fit a result: *could this same quantity be produced for
a forward year from forward drivers, and would it respond to changed conditions?* **Yes** — it is
the identical construction the model already performs for its **own** zones (a weather-year load
shape scaled by growth, plus VRE capacity × CF), applied to a neighbouring balancing authority.
It is a driver, not an outcome.

**What is INADMISSIBLE and is named here so no successor mistakes it for this:** the measured
DIBA **interchange series itself** (that is the outcome the LP computes — feeding it back is the
pinning rule 13 forbids absolutely); neighbour **Net Generation (Adjusted)** as a whole (it is
tied to the neighbour's demand by its own total interchange, which contains the MISO tie, so it
smuggles the outcome); and any noise term, variance inflator or scalar tuned to this σ, whatever
this session measures. **Nothing below can license any of those.**

## 3. Q-B — handoff item 3, the named and explicitly-unmeasured hypothesis

The model's seam flow has exactly two inputs: the ladder-vs-spread merit test (price) and the
measured **(month × hour-of-day) deliverability envelope** — a deterministic diurnal template.
The hypothesis is that the model's residual is that template, where the real seam's is
idiosyncratic.

**Measurement, fixed here.** A deterministic **(month × hod) template block** — 12 × 24 = 288
group means — is fit to each side's residual and its R² read as the between-cell variance share.
Because 288 cells on ~8,760 hours inflates a raw in-sample R² by ~3 %, the **gated** statistic is
the degrees-of-freedom **ADJUSTED** value `1 − (1 − R²)(n − 1)/(n − k)`, `k = 288`; the raw value
is reported beside it.

**DECISION RULE for PJM (the seam the handoff named), all three years:**

* **CONFIRMED** iff `R²_tmpl(r_model) ≥ 0.50` **and** `R²_tmpl(r_model) ≥ 3 × R²_tmpl(r_meas)`.
* **REFUTED** iff `R²_tmpl(r_model) < 0.25` in **any** year.
* **PARTIAL** otherwise, reported as partial and closing nothing.

The other three seams are **reported, not gated**. The model-side residual `r_model,s` is the
miso-235 four-seam reconstruction's residual on the same OLS — a **reconstruction** number, and
labelled as one everywhere, exactly as miso-235 §7.2 requires.

## 4. What this session cannot do, stated before the numbers

1. **No lever is proposed and none can be licensed here.** A measurement that reads ADMISSIBLE
   names an object for a successor's charter; it does not charter one, and it does not arm
   anything.
2. **No damping factor, no re-derive.** The PJM and SPP `delta_k` ladders are derived, frozen and
   pinned to their derive by test (rule 23 `[R-FROZEN-DERIVE]`); a factor swept against this
   residual is the rule 1 `[R-STRUCT]` fitted mechanism. Nothing measured below can license one,
   whatever it says.
3. **No re-test of an adjudicated cell** (rule 28(a) DO-NOT-REDO): `miso_south_firm_export_block`
   **G**, `miso_south_export_ladder_rt_tail` **R**, `internal_congestion_split` **G**,
   `vre_reference_rate_curtailment_grossup` **K**, `measured_interface_limits` **R**,
   `miso_rdt_measured_limit` **R**, `miso_south_gas_delivered_cost_basis` **R**. Where a number
   here touches one it **corroborates** it; the standing adjudication remains the finding.
   Manitoba's price response stays **CLOSED as already-armed** (miso-235 §3) and is not re-opened
   — this session measures its *residual*, which is the object miso-235 handed forward.
4. **No cell verdict moves in either direction.** This session tests no mechanism, so rule 28(b)
   attaches only in its **evidence-appending** form (the miso-206 / miso-234 / miso-235 /
   neiso-100 / caiso-206 no-solve precedent). Evidence is appended to `seam_flow_envelopes` and
   `seam_neighbour_hourly_ladder` in **MISO's shard only** (rule 25).
5. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not trade
   a passing gate for anything (miso-227 promotion rule).
6. **C3c is untouched** and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification and an owner ruling; no LP is authorized there under this
   handoff and none is sought.

## 5. Deliverables

* `scripts/probes/_miso236_neighbour_state_residual_phase0.py` →
  `results/calibration/_miso236_neighbour_state_residual_phase0.json`.
* `results/calibration/FINDING-miso236-*.md` carrying **every number this session will ever
  cite**.
* Evidence appended to MISO's matrix shard + the §5.4 queue stamp (rule 25, rule 28(b) evidence
  form).
* `docs/calibration-log/miso.md` entry.

## 6. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed or selected.
Rule 12 `[R-PARALLEL]`: no LP is solved; nothing runs on CI. Rule 13 `[R-MEASURED]`: measurement
only — no input changes, no measured outcome enters any solve, and §2c fixes the admissibility
argument and the named inadmissible forms in advance. Rule 14 `[R-ACCURATE]`: no input changed.
Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO keeps exactly one
registered run and the keeper's `hourly/` sidecars stay committed. Rule 19 `[R-ONE-MECH]`: no
mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22 `[R-HOLDOUT]`: 2023–2025 only.
Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run. Rule 24 `[R-REGISTRY]`: no field created.
Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section and lane only. Rule 27 `[R-PUSH]`: every pushed
blob verified against local. Rule 28: queue item named in §0; evidence-append form only.
Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0 first, and this session is that phase 0.
