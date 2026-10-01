# PRECOMMIT — ercot-175: the offered-vs-deliverable wedge at SCED grain (Phase 0)

**Session ercot-175, 2026-08-06. Charter: the ercot-173 Phase 0 re-pointing —
"what separates the offered curve from the cleared price at those hours (SCED
ramp/HDL limits, AS holdback, deliverability at 5-min grain)" — now that the
full delivery-2023 NP3-965 corpus (315 shards, 897 MB) carries HSL, HASL, HDL,
LSL, LASL, LDL, Telemetered Resource Status, Base Point, Telemetered Net
Output and per-product AS awards at 5-min grain. PHASE 0 FIRST, NO LP,
measure-then-charter.** This document is committed and pushed **before** any
wedge measurement. Every threshold, coverage bar, verdict branch, gate
assignment and prediction below is fixed here and may not be moved after
measurement, in either direction (the ercot-162…174 discipline). The kill
gates are **inherited verbatim from
`docs/PRECOMMIT-ercot172-maintenance-season-availability-2026-08-06.md` §5 and
are not renegotiable**; this document assigns them, it does not restate or
amend them. **G-COAL148 stays live even though this lane is not the ceiling
lane** (handoff directive).

## 0. Objects — identified from COMMITTED artifacts before this document was written

* **The gate object**: C3a-2023 **−29.9 % lw-hub / −32.2 % scorer** on the
  keeper `2026-08-05-run168b-year-curves`, the largest open load-bearing gate
  in the ERCOT fail set {C3a, C3b}.
* **Hour sets — IMPORTED VERBATIM, never re-derived**: **H123** (the 123
  missed >$200 hours) and **H61** (the 61 actual >$1000 hours) exactly as
  `scripts/probes/ercot173_depth_phase0.py::hour_sets()` constructs them from
  the committed keeper sidecar
  (`results/calibration/ercot168_yearcurves_B/hourly/system_2023.parquet`,
  P1, demand-weighted zonal mean) and
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet` — the function
  is imported and its own `len == 123` / `len == 61` asserts stand, so the two
  Phase 0s are comparable by construction.
* **Committed reference figures (read from the committed
  `results/calibration/ercot173_depth_phase0.json` + `FINDING-ercot173` §1,
  never re-measured here)**: V_r (market sub-$200 offered, online+startable)
  mean **56.5 GW** over H123; V_m (model sub-$200 capability) mean
  **55.2 GW**; **M(h)** (the model's undispatched sub-$200 capability — the
  MW that must not be there for the model price to cross $200) mean
  **3.30 GW / p50 2.22 GW** over H123; reality cleared **p50 $462** over the
  missed set. The ercot-173 refutation stands: the >$200 formation at H123 is
  NOT a supply-curve crossing; this session measures what separates the
  offered stack from the cleared price.
* **M(h) is consumed per-hour**: the per-hour M series is recomputed by the
  same committed construction (cheapest-first fill of the sidecar class
  dispatch against the capture-A bid stack — `face_tables`' own arithmetic,
  imported/reproduced, not re-designed) solely so ratios to M(h) can be taken
  per hour; its aggregate must reproduce the committed mean/p50 above to
  within 1 % (stop-the-session if not).

## 1. Instruments — imported or declared verbatim, fixed here

* **Corpus**: `data/raw/ercot/SCED/` (delivery = filename month − 2, the
  standing convention). Row scope **S** = the ercot-173 `RESTYPE_CLS` map
  verbatim (CLLIG→COAL; CCGT90/CCLE90→CC; SCGT90/SCLE90→CT;
  GSREH/GSNONR/GSSUP→ST_GAS). Status sets verbatim: ONLINE =
  {ON, ONRUC, ONTEST, ONREG, ONREGL, ONHOLD, ONOS, ONOSREG}; STARTABLE =
  {OFFQS, OFFNS}. Storage, renewables, nuclear OUT OF SCOPE (the standing
  adjudications; `ercot_storage_rt_offer_surface` R).
* **Clock**: CPT → fixed CST exactly as `ercot173_depth_phase0.market_stack`
  does it (tz-localize America/Chicago, convert Etc/GMT+6, drop tz); hour
  membership by CST hour-key; per-hour statistics are **interval-means over
  the hour's SCED intervals** (n_iv normalisation, the committed convention).
* **Offer curve**: the sub-$200 offered MW uses the **SCED1 Curve MW/Price
  segment construction verbatim** (per-step incremental MW = clipped diff of
  cumulative MW, summed where the step price is finite and < $200) — widened
  from the committed 10-step read to **all 35 SCED1 steps** (the corpus's full
  width; declared, not silent). The 10-step reconstruction is also computed as
  a comparability cross-check against the committed V_r and reported.
* **Wedge fields**: `HASL`, `HDL`, `Base Point`, per-product
  `Ancillary Service {REGUP, REGDN, RRS, RRSFFR, NSRS, ECRS}` — read as
  telemetered/award columns, numeric-coerced, used ONLY as measurement
  evidence (§5 fixes the rule-13 line).
* **Model side (committed sidecars only, no LP)**: the keeper's
  `reserve_family_2023.parquet` supplies the model's own AS quantity holdback
  at each hour — H_model(h) = Σ `held_mw` over the withheld-class families
  {RegUp_withheld, RRS_withheld, ECRS_withheld}, with NonSpin and
  `ercot_ordc_total` reported separately (NonSpin is carried by offline
  capability; the ORDC family is the pricing measure). This classification is
  a REPORT feeding the reconciliation — no gate rests on it.
* Rule 22 `[R-HOLDOUT]`: 2023 only (a training year). No year outside
  2023–2025 is read, solved or scored; ERCOT holds no `complete` marker.

## 2. The wedge decomposition — fixed HERE

Per SCED interval i, per ONLINE resource r ∈ S (all quantities MW ≥ 0):

```
O_r    = sub-$200 offered MW           (35-step SCED1 segment sum, clipped to [0, HSL])
A_r    = min(O_r, HASL_r)              (after AS holdback: HASL = HSL − AS responsibility)
R_r    = min(O_r, HASL_r, HDL_r)       (after ramp reachability: HDL = this-interval limit)
D_r    = min(O_r, HASL_r, HDL_r, BP_r) (delivered: Base Point against the sub-$200 block)

W_AS_r    = O_r − A_r      (AS-holdback wedge)
W_RAMP_r  = A_r − R_r      (ramp/HDL wedge)
W_RESID_r = R_r − D_r      (residual: 5-min congestion, dispatch economics, other)
```

Identity per resource: `O = W_AS + W_RAMP + W_RESID + D`, every term ≥ 0 by
the monotone min-chain. ERCOT telemetry orders `HDL ≤ HASL ≤ HSL` and
`BP ≤ HDL` by construction; violation rates are counted (§3 L3). STARTABLE
resources are reported as their own single term **W_START** = their sub-$200
offered MW (they cannot deliver within the interval; their non-delivery is
start latency — the ercot-151 offline-increment lane's object, NOT this
session's), alongside their Base Point if any. The online/startable split of
the committed V_r is reported.

Aggregation: per hour h ∈ H123 (and H61, descriptive), interval-mean of the
per-class and total sums; mean and p50 over hours. Report each step's GW
(O, A, R, D) and each wedge term, per class {COAL, CC, CT, ST_GAS} and total,
against the committed V_m 55.2 GW / M(h) series, plus the model-side
H_model(h) reconciliation column.

## 3. Licensing — fixed here

* **L1 (corpus coverage)** — ≥1 online row of S resolves at **≥ 0.90** of
  H123 (the ercot-173 bar, verbatim; the same corpus read 1.0000 there).
  Below: FILED-UNLICENSED.
* **L2 (field completeness)** — per wedge field {HASL, HDL, Base Point}: the
  share of online-S resource-intervals at H123 with the field finite must be
  **≥ 0.90**, else THAT step is unlicensed — its term merges into W_RESID and
  is reported UNLICENSED. An unlicensed HDL unlicenses the ramp face and no
  charter verdict may rest on it (branch 1 fires for the verdict-bearing
  face).
* **L3 (chain sanity)** — the share of online-S resource-intervals violating
  `HDL ≤ HASL + 1 MW` or `BP ≤ HDL + 1 MW` is reported; if **> 0.05** for a
  boundary, the term on that boundary carries a construction caveat and any
  charter verdict resting on it is withheld pending a construction re-read
  (stop-the-line, not a silent proceed).

## 4. Decision rule — PRE-REGISTERED, branches in order, first to fire wins

The verdict-bearing statistics, fixed now (all on H123): the per-hour ratio
series `w_ramp(h) = W_RAMP(h) / M(h)` and the wedge-composition share
`s_ramp = p50_h[ W_RAMP(h) / (W_AS(h) + W_RAMP(h) + W_RESID(h)) ]`.

1. **FILED-UNLICENSED** — L1 fails, or L2 fails on HDL (the verdict-bearing
   face). Name the blocking data; no verdict rests on the unlicensed face.
2. **FILED-REDIRECTED** — licensed, but **p50_h[w_ramp(h)] < 0.60**: the ramp
   wedge does not principally own the model's sub-$200 margin. Name which
   term does carry the wedge (W_AS / W_START / W_RESID), file the owner
   question(s) of §6, and stop — no mechanism is built.
3. **CHARTER-RAMP** — **p50_h[w_ramp(h)] ≥ 0.60 AND s_ramp ≥ 0.60** (the
   majority-plus-margin standard, twice, the ercot-170…173 form): the ramp
   wedge both covers the model's margin and principally owns the measured
   wedge. Then the named mechanism is the **existing `ramp_limits` gate armed
   for ERCOT** (one default-off gate, zero fitted scalars, the CAMPD-measured
   envelope — §5 fixes its rule-13 side), subject to BOTH: (a) an explicit
   **in-session owner adjudication** — the ERCOT envelope artifact is
   deliberately parked at the probe path and its loader-path promotion is
   recorded as the owner's call (matrix `ramp_envelopes` note), and the
   ERCOT cell's standing `R` (ERCOT-127, scoped to the coal dispatch-band
   object) is re-opened only on this Phase 0's new evidence at a NEW object
   (rule 28a); and (b) the seam proof in the ercot-173/174 SP pattern passing
   BEFORE any solve. Then ONE LP pair (control + arm, `--year 2023 2024
   2025`, SAME-HEAD, no rebase between the two solves), both registered
   whatever the outcome (rules 15/16). Absent the owner adjudication →
   **ACTIONABLE-SPECIFIED**: the charter and its gates are specified for a
   successor and nothing is built.
4. **FILED-SPLIT** — p50_h[w_ramp(h)] ≥ 0.60 but s_ramp < 0.60: the wedge is
   real and big enough, but principally owned by a term this session cannot
   charter (§6). Report the full decomposition, file the owner question, no
   build.
5. **FILED-NULL** — otherwise.

Why 0.60 twice: below it a mechanism premise rests on an unattributed
aggregate (the ERCOT-163 §3 prohibition) and a "correction" would be tuned to
a residual, not a measured fault (rule 13).

## 5. THE RULE-13 [R-MEASURED] LINE — fixed BEFORE measurement

* **FORBIDDEN, whatever the wedge reads**: injecting HDL, HASL, Base Point,
  or ANY telemetered per-interval limit into the model as an availability
  cap, dispatch pin, or per-hour bound. These are measured *outcomes* of the
  2023 dispatch with no forward analogue — the same object ercot-172's C3 was
  refused for, and the same class as the standing fences (no per-hour
  telemetered-HSL cap, no aggregate capability cap). They are used here ONLY
  to measure whether and where the wedge exists.
* **ADMISSIBLE (the structure that PRODUCES the wedge)**:
  * **Thermal ramp limits** — the existing `ramp_limits` LP rows
    (`model/lp/rows.py::_build_ramp_rows`), parameterized from the
    CAMPD-measured per-plant-group max observed 1-h up/down move
    (`scripts/data/derive_campd_ramp_envelopes.py`, gross→net rebased at the
    loader per ERCOT-132 leg A). Passes the rule-13 test: regenerates for a
    forward year from the CAMPD pipeline for any vintage, responds to fleet
    change, never reads a residual. **The LP constraint never reads SCED HDL.**
  * **AS-holdback reservation on the offered stack from the co-opt's own
    awards** — named by the handoff as the other admissible side. It passes
    the rule-13 test in form, BUT at ERCOT it is **reserve-side, and the
    reserve family is CLOSED** (ERCOT-107/108 completed 2×2; ERCOT-102
    refuted the AS-holdout premise — the measured-plan holdout is already in
    place and SLACK at the missed hours; the keeper's withheld families are
    the in-place structure). **This session will therefore NOT charter an
    AS-side mechanism regardless of what W_AS reads** — a dominant W_AS
    yields branch 2/4 with the measured reconciliation (W_AS vs H_model)
    filed as an owner question, never a build. Stated now so a large W_AS
    cannot be read as a licence.
* The proposed branch-3 mechanism sits on the ADMISSIBLE side: measured
  physical capability in, LP produces the wedge endogenously.

## 6. Owner items carried (surfaced, NOT decided here; no solve needed)

Inherited from ercot-174 §3b/§5 and the handoff, reported to the owner in the
FINDING whatever Phase 0 reads: (1) the ERCOT-148/149 product ceiling vs the
pervasive double-count — the event-cap CEILING LANE IS FROZEN pending that
ruling and this session does not enter it; (2) the finer-grain-wins variant,
named not built; (3) ercot-172 fault 3 (multi-week flat plateau as hourly
ceiling) as the sole remaining structural route to the 2024 object; (4) the
run168b keeper's non-reproduction at current main (re-key vs re-solve at
HEAD). This session adds, if Phase 0 lands there: (5) the W_AS-vs-closed-
reserve-family reconciliation question, and (6) loader-path promotion of the
ERCOT ramp envelope artifact (the branch-3 precondition).

## 7. Known limitation — stated now

**Full-span SCED exists for 2023 ONLY**; 2024/2025 carry sample days only
(`60_DAY_SCED_DISCLOSURE_*_ercot74/75/86_*`). The wedge is measured on 2023.
The branch-3 mechanism carries **no corpus-identified parameter** — the
envelope derives from CAMPD (available every year 2018–2026, applied
consistently per rule 22's data-consistency clause), and the corpus supplies
only the Phase-0 licence — so no 2023-fitted scalar enters (rule 23:
identified on source data, never on the residual). The 2024/25 out-of-sample
story for any arm is the rule-22 LOYO within 2023–2025 before promotion, plus
the sample-day corpus as a qualitative cross-check (reported, never gating).

## 8. Kill gates — inherited VERBATIM (PRECOMMIT-ercot172 §5), assigned now

Reached only under branch 3 with the owner adjudication. **G-BIT is declared
N/A now, pre-solve**: a ramp arm is a year-agnostic physical rule touching
all three years (§3c(a) of the ercot-172 record forbids a year scope), so
**G-SPAN replaces it**, exactly as ercot-172/173 fixed. Live gates on any
arm: G-SPAN, G-SHED (no year's shed count may rise; there is no 2024-shed
target here — the clause "2024 must fall" applies to ceiling-lane arms, and a
ramp arm is judged on "no rise" in every year plus its own pre-registered
predictions), G-SPUR, G-C3c (61/181, 25/53, 3/31 must not degrade —
honest pre-statement: a ramp arm can only REMOVE model supply at ramp-bound
hours, so tail counts should move TOWARD actual; a fall in caught hours would
fire this gate as written), **G-COAL148** (live, per the handoff, though this
is not the ceiling lane), G-DOF (zero new fitted scalars), G-D2, LOYO.
Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such, run still
registered.

## 9. Predictions — recorded NOW, before measurement

* **P-W (required by the standing record)**: the total online wedge
  `O − D = W_AS + W_RAMP + W_RESID` is materially positive at H123 (p50 ≥
  2 GW). If it is ~0, the ercot-173 refutation and this measurement are in
  tension and BOTH are re-examined before any verdict (stop-the-line).
* **P-AS**: W_AS reads **2–6 GW** (the 2023 AS plan is ~5–7 GW; ECRS launched
  Jun-2023; thermal carries most of REGUP/RRS/ECRS, storage a growing share).
  H_model is the same order — the model already withholds the measured plan —
  so the NET unmodeled AS wedge (W_AS − H_model) is predicted SMALL relative
  to W_AS. Reported per hour; no gate.
* **P-RAMP**: honest uncertainty — W_RAMP is the unknown this Phase 0 exists
  to measure; no credible magnitude prior is claimed. Direction: expected
  concentrated in the evening net-load-ramp hours (the H123 calendar is Aug
  60 / Sep 20, hours 17–20 dominant). The decision bar (p50 w_ramp ≥ 0.60,
  i.e. W_RAMP covering ≥ 0.60 of M ≈ 2.2 GW p50) is fixed in §4 and stated
  here so it cannot be read as tuned after the fact.
* **P-START**: the startable sub-$200 offered block W_START is expected
  GW-scale (the ercot-151 DAM-instrument analogue read ~13.5 GW at its 91
  missed hours) — it is REPORTED and expressly NOT chartable here (the
  offline-increment re-pricing lane is its own chartered, owner-gated lane).
* **P-L**: L1 passes (~1.00, the same corpus resolved 1.0000 at ercot-173);
  L2 passes for HASL/Base Point; HDL completeness is genuinely unknown
  (never read from this corpus by any committed instrument) — if HDL fails
  L2, branch 1 fires for the ramp face, stated now.

## 10. Governance

Rule 25: ERCOT-scoped throughout. Rules 15/16: if a solve happens, control +
arm full-span in one bundle each, both registered whatever the outcome; if no
solve happens, that is stated explicitly in the FINDING (the ercot-174
precedent). Rule 22: training span only; no clean-partition regeneration
unless a solve is reached. Rule 23: no derive is re-run against a residual;
the CAMPD envelope derive is frozen and is not re-valued by this session.
Rule 24: any armed flag is a registered `ScenarioConfig` field recorded in
`run_config.json`. Rule 27: every push touching a ≥300-line file is
blob-verified; no bulk rewrite of core files. Rule 28: matrix §5.1 gains
**item 18** and the touched cells (`ramp_envelopes` ERCOT at minimum) are
re-stamped with this session's outcome in the same session, rejections and
FILED verdicts included. Bookkeeping in-session:
`FINDING-ercot175-*.md`, `docs/calibration-log/ercot.md`.

**DO-NOT-REDO honoured (all stand)**: the event-cap ceiling lane is FROZEN
(no composition-rule work, no C1/C2/unit-scoped re-test, no partial-layer
retirement; blanket min() R, unit-scoped R); the 2023 depth/excess-cheap-depth
premise is REFUTED at the aggregate and is not re-litigated; the reserve-side
scarcity family is CLOSED (ERCOT-107/108) — §5 turns this into a hard fence
on any AS-side build; `ercot_storage_rt_offer_surface` R;
`energy_online_capability_cap` R; the CC-headroom per-unit crosswalk
FILED-UNLICENSED; ALL coal offer-curve lanes CLOSED; per-year CT
re-identification REFUSED; West/Panhandle topology CLOSED; ercot-172's C3
REFUSED (rule 13); no per-hour telemetered-HSL cap, no aggregate capability
cap.

**Next shorthand: ercot-176.**
