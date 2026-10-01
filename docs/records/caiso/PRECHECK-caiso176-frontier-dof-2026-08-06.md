# PRECHECK — caiso-176: the frontier re-assessment on caiso-175, and the `battery_dispatch_adder` DOF closure

**Session:** caiso-176 · branch `claude/caiso-176-frontier-dof-s2i7qi` · 2026-08-06
**Keeper at session start:** `2026-08-06-caiso-175-tac-intake` (CALIBRATED-WITH-CAVEATS,
0 FAILs, 9/9 scored, DOF `n_entries` 11 / `n_residual` 8).
**CAISO ONLY.** No other ISO's keeper shard, registry entry or status part is touched.

---

## 0. What this session may not do (stated first, so nothing below can quietly override it)

* **The HOLDOUT SPEND FREEZE is ACTIVE** (`frontend/data/backcast/holdout-freeze.json`,
  declared 2026-07-25, held 2026-07-26, narrowly lifted-and-**re-armed** 2026-08-05) and it
  **outranks CAISO's `complete` marker**. Solve years are **2023 / 2024 / 2025 only**, in ONE
  bundle per arm (rule 16), years sequential, arms sequential (rule 12). `--holdout-authorized`
  is not used and would refuse anyway.
* **`holdout-freeze.json` and `calibration-complete.json` are OWNER ACTS.** The only write this
  session may make to the latter is the rule-22 D-5(b) re-key that a promotion requires — and
  only if a promotion actually happens.
* **`final` is NEVER AUTHORIZED for CAISO.** This session produces a **recommendation with its
  basis**. It does not write the marker, and it touches no locked-test year.
* **Both ledgered caveats are WALLED and stay walled.** C3a on non-public hourly pumped-storage
  data (caiso-141 A2); C3c on the SoCalGas OFO declaration record. Neither may be re-opened with
  an adder, haircut or overlay (rules 1 / 13; caiso-142 §H generalises the refusal to the whole
  export/absorption family; caiso-144 §D refuses the LOLP overlay on measurement).
* **An N–S topology lever against KNOWN-OPEN 1 stays FORBIDDEN** (caiso-164 §0/§6).

---

## 1. TASK 1 — frontier re-assessment (NO LP, committed artifacts + live wall re-verification)

caiso-173 was the last full frontier assessment and it ran on a keeper two promotions old.
Re-run it against caiso-175: resolve the §5.2 queue live from `keepers/CAISO.json` → registry
rather than from pinned ids, re-run `mechanism_matrix_gap_sweep --iso CAISO`, re-census the
CAISO matrix column, re-verify every §5.2 evidence document resolves on disk, and re-verify
the two walls **live** rather than assuming them.

Then answer the one declaration question actually open: **does CAISO's evidence support
RECOMMENDING `final`?**

**The criterion this session applies to that question, fixed here before the answer is
written.** `final` authorizes a **touch-once, never-regrantable** score of 2019 and H1-2026.
A recommendation is therefore justified only if **all four** hold:

* **F-a — the tier is EXECUTABLE.** Both locked-test years must actually be scoreable from
  committed benches. A one-shot that cannot be scored is not a test, and a one-shot spent on a
  partial score is a one-shot destroyed.
* **F-b — the tier ORDER is respected.** Validation (2022) exists to catch problems *before*
  the unrepeatable test is spent. Recommending `final` while the iterable tier is entirely
  unspent inverts the ladder.
* **F-c — the input envelope the keeper is calibrated against is SETTLED.** The freeze's own
  stated reason is that a locked-test year scored on a known-defective availability envelope
  yields a MISS that is uninterpretable and a PASS that is actively misleading.
* **F-d — the model is at its frontier**, which is the `complete` criterion and is expected to
  hold; it is necessary, not sufficient.

Any one of F-a…F-c failing ⇒ **recommend NO**, with the failing condition named and the route
to clearing it stated. This rule is fixed before any of the four is evaluated.

---

## 2. TASK 2 — the `battery_dispatch_adder` DOF closure

`battery_dispatch_adder = 5.0` is CAISO's last genuinely free residual-identified parameter
(attestation `free_parameters`, `identification: "residual"`). Derive it from **CAISO's own
market data** — never transfer ERCOT's $10 or any other ISO's value (rule 25 `[R-ISO-SCOPE]`),
never fit it to a price residual (rule 13 `[R-MEASURED]`).

### 2a. DO-NOT-REDO — what this session establishes is already spent, before proposing anything

The DOF ledger names the forward-valid replacement as *"the measured AS power reservation
(`storage_as_commitment`) + an ATB-derived degradation cost"*. **Both halves are already
adjudicated on CAISO** and rule 28's DO-NOT-REDO discipline forbids re-testing either without
new evidence:

| half | adjudication | where |
|---|---|---|
| measured AS power reservation | `caiso_storage_as_reservation` probe-adjudicated **INERT**; whole AS-award family then refuted by arithmetic (overnight upward award 334–713 MW against 2.1–3.1 GW of remaining headroom) | caiso-74 (run `2026-07-11-caiso-74-storage-as`); caiso-127/129 |
| ATB-derived degradation cost | built at $14.25/MWh and A/B-solved → **REJECTED PROBE** on caiso-100 FINDING §6's pre-registered two-sided ±15 % battery-only throughput guard (2024 chg 6.77 < 7.40 TWh; 2025 10.28 < 11.07; discharge under floor in all three years) plus 2025 evening discharge moving 0.64 TWh away from measured | caiso-100 / caiso-101 (run `2026-07-19-caiso-100-cycling-cost`) |

Recomputing the ATB value on **today's** committed constants gives
`452.6 $/kWh × 1000 / 5000 cyc × 0.25` = **$22.63/MWh** — the capex constant moved from
285 $/kWh since caiso-101, so the derived value is now **further** in the direction the volume
guard rejected, not nearer. Re-arming it is refused *a fortiori*, and this session does not
solve it.

Also refused as a closure route, and stated so it is not mistaken for one: routing the LP
through `_degradation_cost_per_mwh` would import
`STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25`, which its own constant block documents as
*"a modeling simplification … tunable."* That is **DOF substitution, not DOF closure** — one
soft parameter for another — and it is not attempted.

### 2b. The one un-read CAISO-own instrument, and the gate on it

The single storage instrument CAISO publishes that no session has read is the **`bid_stack`
sheet of the Daily Energy Storage Report** — committed at
`data/raw/storage-as-awards/CAISO/storage-report-*.xlsx` and recorded in that directory's
README as *"retained but not curated"*. It is the as-submitted bid volume of the whole storage
fleet bucketed by offer price: a direct market measurement with **no model in the loop**.

The economic content is **one-sided and is declared as such before it is used**: a rational
participant does not offer energy below its own marginal cost — the premise CAISO's own DEB
market-power-mitigation machinery rests on — so the lowest price bucket carrying material
discharge volume bounds the fleet's throughput cost **from above**. The instrument can
therefore **refute** a candidate value; it cannot confirm one.

**Instrument:** `scripts/probes/_caiso176_bidstack_reservation.py` (committed).
**Gates, fixed in that probe's module docstring before it was executed:**

* **G1 RESOLUTION** — a published bucket edge must fall strictly between the two candidate
  values, so they land in different buckets. **Neither candidate was chosen by this session:**
  5.0 is the keeper's committed field and 22.63 is arithmetic on committed constants, so G1
  carries no free choice.
* **G2 MASS + STABILITY** — the implied upper bound (upper edge of the lowest priced bucket
  carrying ≥ 1 % of the year's priced discharge volume) must be **stable across 2023/2024/2025**
  to be a parameter rather than a yearly outcome. Reported at a 5 % threshold too, so the
  answer cannot be an artifact of one threshold.
* **G3 CONTAMINATION** — a storage energy bid is an OPPORTUNITY-COST object, which the LP
  already generates endogenously through SOC + RTE. Report the `SELF-SCHED` share (price-taking,
  expresses no cost, excluded from the priced stack before any bound is read) and the share
  priced at or below \$0.

### 2c. THE VERDICT RULE — both branches, fixed before the outcome is read

* **BRANCH I — the instrument IDENTIFIES a value** (bounds tight enough that a single value
  follows from the data without a further choice). Then: derive it, and A/B it —
  **Arm A CONTROL**, the caiso-175 keeper recipe replayed unchanged at *this session's head*;
  **Arm B TREATMENT**, identical but for the one derived scalar. Both arms solve
  **2023/2024/2025 in one bundle** (rule 16), arms sequential (rule 12), both **REGISTERED**
  (rule 15) with `legitimacy_diagnostics.json` generated for each so C7/C8 stay SCORED.
  Promote on the **rule-14 `[R-ACCURATE]`** basis: determination holds + no new FAIL + no new
  caveat ⇒ PROMOTE.
  **THE BRANCH THAT ACTUALLY BINDS:** a **DEGRADED criterion does NOT revert a correct measured
  input.** Rule 14 makes a worse fit on accurate data a **discovered bug**, not grounds to
  restore the estimate — the residual is then an open root-cause issue, and the input stays.
  The caiso-101 volume guard is additionally re-imposed as a **reported** quantity on any arm
  that is solved, because it is the gate that killed the last attempt on this same parameter.
* **BRANCH II — the instrument BOUNDS BUT DOES NOT IDENTIFY** (or is refuted by G1/G2/G3).
  Then: **FILE THE WALL** with the instrument committed so it is re-checkable, leave
  `battery_dispatch_adder = 5.0` exactly as it is, and record the bound as the new evidence it
  is. **No arms, no solve, no bundle, nothing registered** — because nothing was run. This is a
  result, not a failure to produce one.

**A CONTROL ARM IS MANDATORY IF ANY ARM IS SOLVED.** caiso-175 measured incidental code drift at
**+0.168 / +0.049 / +0.115 \$/MWh** on load-weighted mean LMP — *larger in every year than its
own treatment* — so differencing against the keeper's committed metrics would misattribute.

---

## 3. Pre-registration ordering — stated plainly rather than implied

The G1/G2/G3 gates and the two-branch verdict rule were fixed in
`scripts/probes/_caiso176_bidstack_reservation.py`'s module docstring **before that probe was
executed**, and this document reproduces them unchanged. That ordering is asserted by this
session; the probe and its result land in the same push, so git history does not independently
prove it. What *is* independently checkable, and is the reason the claim has force: **both
candidate values the gates discriminate between were fixed by artifacts that predate this
session** — 5.0 by the committed keeper `run_config.json`, 22.63 by committed
`constants.py`/`capacity_market.py` arithmetic — so no gate in §2b had a free parameter this
session could have set to reach a preferred answer.

The requirement that pre-registration precede **the arms solve** is satisfied unconditionally:
at the time this document is written, no LP has been constructed, solved or scored in this
session, and under Branch II none will be.

## 4. Housekeeping fixed in advance

* Any completed run is **REGISTERED** (rule 15), keeper and probe alike, with
  `legitimacy_diagnostics.json` generated per bundle — caiso-175 closed that gap and this
  session does not let it reopen.
* The CAISO **mechanism-matrix cell and the §5.2 header are updated in this same session**
  (rule 28 duty b), including the caiso-100/101 adjudication that the
  `battery_dispatch_adder` cell note currently does not carry.
* KNOWN-OPEN 1 (the N–S congestion majority) and KNOWN-OPEN 2 stay named and uncharted.
* The `run_d1` / `score_shape` gating inconsistency (the diagnostic screens on class list
  alone, the rubric on class list **and** load share, so `legitimacy_diagnostics.json` reads
  `Overall: FAIL` on CAISO ST_GAS where C7 correctly reads PASS at 0.6/0.4/0.1 % of load) is
  **carried forward untouched** — it is a clean scorer-only fix, but this session's keeper
  question must not depend on the answer, so it is not made here.
