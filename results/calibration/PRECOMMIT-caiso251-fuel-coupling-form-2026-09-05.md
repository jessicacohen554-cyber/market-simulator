# PRECOMMIT — caiso-251: THE CAISO GAS-OFFER FUEL-COUPLING FORM

**Session caiso-251, 2026-09-05.** Branch
`claude/caiso-251-backcast-calibration-7tci3e` off `main` `ee7754c1`. Keeper
**`2026-09-05-caiso-246-b1-spot`** (`caiso246_b1_spot_coverage`, `git_sha`
`900402b`), **NOT-YET**, C3a the sole load-bearing FAIL at **+3.9 / +12.3 /
+11.4 %** (2023 PASSES).

**Pushed to `origin` BEFORE the estimator is coded, before any cell of the
object is measured, and before any arm is coded or solved.** Rule 22
`[R-HOLDOUT]`: 2023–2025 only, fail-closed; CAISO holds no `complete` and no
`final` marker; the holdout freeze is ACTIVE.

---

## §0 — THE OBJECT

Queue item A (the CC-hot / CT-cold split) taken at its **functional form**, not
its level, exactly as the handoff requires. The form in question is already
named by two committed findings and has never been charted:

**The keeper arms `gas_offer_net_revenue_margin` (anchor $4.7964/MMBtu).** Every
CAMPD gas tranche whose band declares a measured physical basis is priced

```
offer = phys · HR_base · fuel(t)  +  (mult − phys) · HR_base · anchor
```

so the above-physical markup is a **fuel-INVARIANT $/MWh margin**. On the keeper
this compresses **1,285 tranches at a median fixed margin of $14.37/MWh** (max
$62.27; the 2025 rebuild log).

**CAISO's own OASIS record contradicts that form.** `caiso-242 §3.5`, measured
on `caiso_offer_curve_measured.json::_provenance.per_year_band_mults` across a
**1.93× fuel swing**:

| class · band | measured multiplier range | armed-implied range | ratio |
|---|--:|--:|--:|
| CT_PEAKER `econ_low` | **0.013** | 0.2775 | **21.3×** |
| CT_PEAKER `econ_high` | 0.040 | 0.2756 | 6.9× |
| CT_PEAKER `peak` | 0.026 | 0.1004 | 3.9× |
| CC_REGULAR `econ_low` | 0.058 | 0.1391 | 2.4× |

A multiplier that is FLAT in fuel is the signature of the **multiplicative**
form (margin scales with the fuel bill). The armed form books **40 % of
CT_PEAKER's econ offer as fuel-invariant margin ($27.26/MWh at the anchor) on
82.1 % of the class's capacity.** caiso-242 recorded this as structural and
explicitly left it un-armed and un-proposed, *"a different object … needs its
own charter"*. **This is that charter.**

**caiso-229 §5 measured the consequence and named the cause.** The model's CC
floor couples to the CA citygate at a Theil-Sen slope of **2.18 / 2.18 / 4.34
MMBtu/MWh** against CAISO's **MEASURED DAM body coupling of 6.7–7.4** — the
model is **UNDER-coupled to fuel** — *"because the affine measured-marginal-HR
+ fixed-margin form is ALREADY armed (`gas_offer_net_revenue_margin`)"*.
caiso-229 refuted the OPPOSITE hypothesis ("the marginal rung over-propagates
fuel", DO-NOT-REDO) and did not pursue the under-coupling.

### §0.1 — Admissibility

The arm is **disarming an out-of-ISO form on the ISO whose own measured record
refutes it**, and it is one flag with **zero new parameters and zero new
fields**:

* **Rule 14 `[R-ACCURATE]`** — CAISO publishes its own as-submitted DAM bid
  curves; the frozen derive of them says full fuel passthrough with a near-zero
  fixed margin. Preferring the measured representation is the rule, and a worse
  backcast is explicitly *not* a reason to keep the estimate.
* **Rule 25 `[R-ISO-SCOPE]`** — the affine form's identification is **NEISO's**
  (the 2022 holdout rotation, neiso-45/46/47). CAISO inherited the form, not the
  evidence. Its own evidence points the other way.
* **Rule 1 `[R-STRUCT]`** — this is a mechanism question decided on which form
  the market actually uses, never on the residual. **See §0.2: C3a is excluded
  from the promotion basis before any measurement.**
* **Rule 24 `[R-DELETE]` / rule 21 `[R-REGISTRY]`** — disarming REMOVES a
  degree of freedom (the anchor) rather than adding one. Under
  `caiso_offer_surface_measured` (armed) the restored form is
  `offer = mult · HR_base · fuel(t)` with `mult` the **MEASURED OASIS**
  multiplier, which is precisely the form the OASIS record identifies. The
  `phys_*` keys become neutral by construction (the shipped fallback).
* **Rule 19 `[R-ONE-MECH]`** — nothing is stacked; one mechanism is removed.
* **Rule 13 `[R-MEASURED]`** — the restored multipliers are the POOLED
  2023–2025 measured surface already armed, applied identically to every year.
  **A per-year measured multiplier is rule-13 inadmissible (a same-year measured
  OUTCOME pin, PREREG-miso146 §9) and is NOT proposed here** even though the
  per-year values sit in the same artifact.

**What this session does NOT do:** it does not touch NEISO or any other ISO's
arming of the same flag (rule 25 cuts both ways — CAISO's record is CAISO's);
it does not re-derive, re-anchor, blend, class-scope or band-scope the form; it
does not touch the measured band multipliers, the conditional ladder, the
`phys_*` keys, or `caiso_offer_surface_measured_ungrounded`.

### §0.2 — THE DIRECTION HAZARD, DECLARED BEFORE MEASUREMENT

The offer delta is exactly `(mult − phys) · HR_base · (fuel − anchor)`. CAISO's
delivered gas sits **below** the $4.7964 anchor through most of 2023–2025, so
the arm **lowers** most offers — and the C3a failure is that the model is
**too high**. **This would be the SIXTH CONSECUTIVE FAVOURABLE DIRECTION**
(caiso-241/242/243/246 and the caiso-246 §5.2 fifth). It is declared here, in
advance, as a hazard:

* **C3a IS EXCLUDED FROM THE PROMOTION BASIS ENTIRELY.** No C3a movement — in
  either direction, in any year — is evidence for or against this arm.
* **The promotion rule, registered in advance** (the owner's standing
  instruction that structural integrity may outrank gate movement): this run is
  a keeper candidate **iff** (a) **G-COUPLE passes** — the disarmed model's
  fuel coupling lands inside CAISO's MEASURED DAM band (§1.2) — **and** (b) no
  load-bearing criterion other than C3a regresses to a NEW failure, **and**
  (c) the governance gates (C6 attested, C8, DOF) hold. **If those hold, the
  run is the keeper even if C3a gets WORSE** — that is rule 1 and it is
  registered before the number is known. **If G-COUPLE fails, the run is NOT a
  keeper even if C3a improves**, and the session says so.

### §0.3 — G-CTRL

The arm is **live in every hour of every year** (delivered gas equals the anchor
on a measure-zero set), so **G-CTRL form 2 is unavailable**. Form 4 is **VOID**
(solve-path files have changed since `900402b`). This session therefore spends
**ONE control solve**: the keeper recipe replayed at HEAD, 2023–2025 in one
invocation, against which the arm is differenced. Two 3-year solves total, run
**sequentially** (rule 12: never two CAISO solves at once).

---

## §1 — THE ESTIMATOR, NAMED, WITH ITS FALSIFIERS

### §1.1 — Phase 0 (zero LP, on-recipe): the offer-delta footprint

`scripts/probes/_caiso251_fuel_coupling_form.py`. Rebuild the keeper fleet
on-recipe (`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`, the
caiso-248 repair; `rebuild_plus` from the caiso-250 probe), and rebuild it a
second time with the single flag disarmed. Both are `fleet_only=True`, no LP.
Measure, per class and per band, the offer delta, its hour distribution, and its
load-weighted size against the required C3a move.

### §1.2 — G-COUPLE, the load-bearing structural gate

The whole rule-14 claim is that the armed form leaves the model **under-coupled
to fuel**. It is testable without an LP and it is the gate this arm lives or
dies on:

> Theil-Sen slope of the class's cheapest available econ offer on the measured
> CA-composite citygate daily series, per year, ARMED vs DISARMED.

* **caiso-229's measured armed value: 2.18 / 2.18 / 4.34 MMBtu/MWh.**
* **CAISO's MEASURED DAM body coupling: 6.7–7.4 MMBtu/MWh** (0.9–1.0 × the
  measured base HR 7.442; `derive_caiso_offer_surface` docstring, caiso-153).
* **G-COUPLE PASSES** iff the disarmed slope lands in **[6.0, 8.0]** in all
  three years. Landing **short** (< 6.0) means disarming does not restore the
  measured coupling; landing **over** (> 8.0) means the multiplicative form
  over-couples and is not the measured form either. **Either way the arm is not
  a rule-14 repair, no solve is spent, and the session reports the negative.**

The estimator is **Theil-Sen**, the repo's own choice for this regression
(caiso-153: OLS is levered on the Jan-2023 citygate tail and attenuates), and
the regressor is the same daily CA-composite citygate series on gas FLOW days
(trade+1 staircase, caiso-90 semantics) the derive used. Neither is chosen here.

### §1.3 — Phase 1 (the solves)

Control = `--replay-bundle results/calibration/caiso246_b1_spot_coverage`, years
`2023 2024 2025` sequentially, ONE bundle. Arm = the same plus the single flag
`--no-gas-offer-margin`. Nothing else differs.

### §1.4 — Gates

| gate | passes iff |
|---|---|
| **G-IDENT** | the measured offer delta equals `(mult − phys)·HR_base·(fuel − anchor)` on every compressed tranche to ≤ 1e-6 $/MWh — the arm is the identity, not an approximation |
| **G-FOOTPRINT** | the compressed-tranche count reproduces the keeper's own solve log (1,285 in 2025) exactly, and **zero** non-gas tranches move |
| **G-COUPLE** | §1.2, all three years |
| **G-CTRL** | the control solve reproduces the keeper's committed 2023–2025 load-weighted prices to ≤ 0.01 $/MWh; a larger drift is reported as HEAD drift and the arm is differenced against the CONTROL, never against the committed keeper |
| **G-HOLDOUT** | every solved/scored year ∈ {2023, 2024, 2025} |
| **G-C6/G-C8/G-DOF** | attested C6, C8 PASS, and the DOF ledger's residual count does not RISE (disarming must not add a free parameter) |

---

## §2 — PREDICTIONS, WRITTEN TO BE UNCOMFORTABLE

| # | prediction |
|---|---|
| **P-1** | G-IDENT holds to ≤ 1e-6 $/MWh in all three years |
| **P-2** | G-FOOTPRINT: 1,285 compressed tranches in 2025 exactly, and zero non-gas tranches move |
| **P-3** | the arm is **LARGE, not marginal**: the load-weighted mean offer delta on CC_REGULAR econ rungs is between **−$3.00 and −$9.00/MWh** in 2024 and 2025 — 4–18× the required C3a move (−0.805 / ≈−0.50). **An OVERSHOOT is the live risk, not a shortfall.** |
| **P-4** | 2023 is different in SIGN for part of the year: the delta is **positive in ≥ 5 %** of 2023 hours (the January citygate spike above the anchor), and 2023's load-weighted delta is **at least $2/MWh less negative** than 2024's |
| **P-5** | **G-COUPLE passes**: the disarmed CC econ coupling lands in **[6.0, 8.0]** MMBtu/MWh in all three years, up from caiso-229's armed 2.18/2.18/4.34 |
| **P-6** | the solve **OVERSHOOTS**: at least one of 2024 / 2025 lands with a **NEGATIVE** C3a gap (model below actual) |
| **P-7** | **2023 C3a gets WORSE** (more positive than +3.9 %) and **2023 FAILS** its C3a band — a currently-passing year is broken |
| **P-8** | CT_PEAKER 2025 dispatch **rises by ≥ 0.5 TWh** from the keeper's 0.348 TWh — the caiso-244 CT volume miss partially closes, because CT carries the largest markup fraction |
| **P-9** | **at least one non-C3a scored criterion regresses** (C1 free count, C2, C3b, C4, C8) — a $5–8/MWh move on 1,285 tranches cannot be invisible everywhere else |
| **P-10** | the determination does **NOT** flip: it stays **NOT-YET** |

**Register the estimator's own weighting, not just the market's** (the caiso-247
P-4 lesson): the phase-0 offer deltas are reported **three ways** — unweighted
per tranche, capacity-weighted, and model-dispatch-weighted — because a
tranche-mean and a dispatch-mean of the same delta differ by the merit order,
and the caiso-247 P-4 error was exactly that confusion. The prediction bands in
P-3 are stated on the **capacity-weighted** basis; the other two are reported
alongside and are not scored.

---

## §3 — STOP RULE

1. **If G-COUPLE FAILS at phase 0, NO SOLVE IS SPENT.** The arm is not a
   rule-14 repair, the session reports the negative, nothing is armed, and the
   keeper is unchanged. This stop rule is the reason phase 0 runs first.
2. **No tuning of the anchor**, no blended/partial form, no class scoping, no
   band scoping, no per-year multipliers (rule 13), no second flag — under ANY
   outcome. If the arm overshoots, that is the result.
3. **No gate is re-run to a pass** and no gate is redefined after seeing its
   result. If a registered prediction fails, it is reported at full size.
4. **C3a is excluded from the promotion basis entirely** (§0.2), in both
   directions. The promotion rule is the one registered in §0.2 and nowhere
   else.
5. **The arm is CAISO-scoped.** No other ISO's arming of the same flag is
   touched, examined, or proposed on (rule 25).
6. If the control solve does not reproduce the keeper (G-CTRL), the session
   reports HEAD drift as its own finding and differences the arm against the
   CONTROL — it does not quietly compare to the committed keeper.

---

## §4 — DELIVERABLES

This PRECOMMIT (pushed first);
`scripts/probes/_caiso251_fuel_coupling_form.py` +
`results/calibration/_caiso251_fuel_coupling_form.json`; if the stop rule does
not fire, the control and arm bundles with their `hourly/` sidecars, the
legitimacy diagnostics, the attestation, the DOF ledger, the verdict, and the
dashboard registration of the arm run **in this session** (rule 15);
`FINDING-caiso251-fuel-coupling-form-2026-09-05.md`; the
`docs/calibration-log/caiso.md` entry; the CAISO matrix shard cell
`gas_offer_net_revenue_margin` updated with its tested verdict (rule 28(b)); and,
**only if the §0.2 promotion rule is satisfied**, the keeper promotion with all
of its re-stamps (rule 28 + `keepers/README.md` step 4).
