# FINDING — ercot-204: the chartered published-RTORPA lever is **NON-VIABLE ON PREMISE**; the rule-26 `[R-DELETE]` successor is executed in its place

**Session ercot-204, 2026-08-15, branch
`claude/ercot-204-published-adder-gap-5nvuuw`.** Precommit pushed before any
solve: `docs/PRECOMMIT-ercot204-rtorpa-gate-and-rule26-successor-2026-08-15.md`.
Keeper at session start and at this session's HEAD:
**`2026-08-14-ercot202-arm-plantphysics`**, determination **NOT-YET**, fail set
**{C3a-2023, C3b-2023}**, C3c the single ledgered **CAVEAT ×3**. ERCOT holds no
`complete` and no `final` marker; only 2023/2024/2025 were solved, scored, read
or registered.

---

## PART A — the chartered lever: NON-VIABLE ON PREMISE

### A.0 Verdict

The dispatch chartered *"the single overlay-completeness delta"* — complete the
2024 published-adder overlay by adding the missing published **RTORPA**
(+0.237 $/MWh dw, ercot-198) — as a **measured-input completeness repair** under
rules 13/14. The dispatch also ordered the **T-1 discipline**: verify the
keeper's actual effective values from the committed record *before* chartering.
That verification was performed first and **falsified this charter's premise**.

**No lever was substituted** (dispatch standing instruction), no
`ScenarioConfig` field was added, no A/B was pre-registered for Part A, no cell
verdict changed, and no LP was built for it.

Probe: `scripts/probes/ercot204_rtorpa_admissibility.py` →
`results/calibration/ercot204_rtorpa_admissibility.json`.

### A.1 The three gates, decided direction-blind and before any residual

**G1 — ARMED STATE**, read from the keeper's **resolved** `run_config.json`
(what the LP actually ran, rule 24 `[R-REGISTRY]`) and its `meta.json`
`coal_prb_sigmoid_overrides`, never from `scenarios.py` defaults:

| field | keeper value |
|---|---|
| `ercot_ordc_total_reserve` | **True** |
| `energy_reserve_coopt` | **True** |
| `ordc_multistep_floor` | **True** |
| `ercot_multiproduct_as_coopt` | **True** |
| `ercot_rtordpa_overlay` (calibration flag) | **True** |
| **any `*rtorpa_overlay*` channel** | **DOES NOT EXIST** |

The model's RTORPA counterpart is **armed**: the LP enforces the published ORDC
total-reserve demand curve and **its dual *is* the model's RTORPA** (sidecar
`ordc_adder`). The chartered delta is not a flag that is off — it is a channel
that would have to be **built**.

**G2 — rule 19 `[R-ONE-MECH]`.** Building it stacks a **second** mechanism for
one phenomenon on the **unexplained residual of an armed first** — the precise
construction rule 19 forbids. Independently adjudicated on `main` the same day:
ercot-203b (2026-08-15) filed the RTORPA item as *"a **mechanism** question
about the co-optimized reserve dual, not overlay completeness, and rule 19 bars
overlaying the published series on top of the mechanism meant to produce it."*
This session reached the reading from the keeper's config before reading that
entry, and records the agreement rather than claiming independence for it.

**G3 — rule 13 `[R-MEASURED]` forward-analogue test**, the charter's own cited
justification turned on the charter: *"could this same quantity be produced for
a forward year from forward drivers, and would it respond to changed
conditions?"* **No.** RTORPA is not an independent market datum — it is a
deterministic function of realized reserve levels through the published ORDC
curve (`adder = LOLP(R) × (VOLL − λ)`, Nodal Protocols §6.5.7.3). **Its forward
analogue *is* the endogenous computation the model already performs.**
Overlaying the measured 2024 series would substitute a measured **outcome** for
the mechanism under validation, in hours the model's own reserves do not price:
the forbidden half of rule 13, not the permitted one.

**The asymmetry that makes this a rule and not a preference.** RTORDPA *is*
armed as an overlay and is right to be: it prices **discretionary out-of-market
RUC/ECRS deployments**, an operator action with **no endogenous counterpart** in
the model. RTORPA has one, armed. One overlay is admissible and the other is
not, for a structural reason rather than a fit reason.

### A.2 What was measured anyway, at full magnitude

Re-measured on the **current** keeper rather than inherited from run192.
ercot-198 reproduces where the bases agree:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| published RTORPA dw $/MWh | 1.2675 | **0.2368** | 0.0787 |
| published RTORPA non-zero hours | 1,705 | **560** | 253 |
| endogenous `ordc_adder` dw | 0.4067 | **0.0000** | 0.0000 |
| `ordc_adder` non-zero hours | 42 | **2** | 1 |
| `rtordpa_overlay` vs published RTORDPA, max abs diff | 4.6e-13 | 2.8e-14 | 1.4e-14 |

The armed overlay half is **exact** in all three years — ercot-198's
completeness verdict on RTORDPA is confirmed on the current keeper.

*Basis caveat, stated not buried:* this probe reports the **raw** NP6-905-CD
archive; ercot-198 applied a settlement-closure guard rejecting one uncorrected
print (2025 h4334, archive RTORPA $414.12/h against a settled hub RTSPP of
$54.96). That single hour is the entire 0.0787-vs-0.015 distance in 2025. 2024
is unaffected. **Neither number changes the gate**, which turns on
admissibility, not magnitude.

### A.3 THE OBJECT THE GATE LEAVES STANDING — measured, handed over, NOT chartered

**The armed endogenous mechanism is not broken.** In 2023 it fires in **42
hours** at up to **$1,920/h**, and **all 42 fall inside** the 1,705 hours the
published RTORPA priced (overlap 42/42), with the model's held ORDC-total
reserve within **0.2 %** of published RTOLCAP (8,122 vs 8,108 MW).

In 2024/2025 it reads ~zero across 560/253 published-fired hours — and **the
simplest explanation is falsified**. The model does not see a comfortable
system: it holds materially **less** reserve than the real one did
(2024 **6,955 vs 8,854 MW**; 2025 **6,638 vs 9,654 MW**) and still does not
price, while its own ORDC-total row records non-zero shortfall in **40** (2024)
and **4** (2025) of those hours.

*Caveat:* the model family's `held_mw` and published `RTOLCAP` are constructed
differently and are **not an identity** — the model quantity is the LP's online
reserve balance row, RTOLCAP is ERCOT's telemetered on-line reserve capacity.
The comparison is **indicative** of where each system's reserve sits, not a
like-for-like reconciliation. It is reported because it **falsifies** the
simplest explanation, not because it identifies anything.

**Where the ORDC pricing region sits relative to the model's reserve
representation is the open object.** It is a mechanism question, it is **handed
to the owner un-chartered**, and this session prepared no lever on it — the
adjacent L-SCAR tightness identification is **DO-NOT-REDO** (V0 adjudication,
ercot-195).

### A.4 Record note, carried not resolved

`main` carries a **duplicated `## ercot-202` heading** in
`docs/calibration-log/ercot.md` (line 8063, the owner sitting record; line 8212,
the T-1 non-viability entry), and the 198–205 shorthand ledger is tangled across
parallel branches — ercot-203b's own collision note records two lanes taking
`ercot-203` simultaneously. **Noted, nothing renamed: it is an owner call.**
197/199/200 remain unspent.

Also carried: ercot-202's log entry frames T-3b's positive result as *"the
committed adder overlay is incomplete by RTOFFPA"*, which ercot-203b has already
corrected from primary sources (RTOFFPA is not in RTSPP; ercot-198 stands). This
session's measurement is consistent with the corrected reading and adds nothing
to that dispute.

---

## PART B — the rule-26 `[R-DELETE]` successor: **EXECUTED, ALL GATES PASS, PROMOTION RECOMMENDED**

**Run registered: `2026-08-15-ercot204-rule26-delete`**, bundle
`results/calibration/ercot204_rule26_delete`, years 2023 + 2024 + 2025 in one
invocation, solved sequentially.

### B.0 Authorization and object

Authorized by the dispatch verbatim: *"Rule 26 `[R-DELETE]` successor already
NAMED by the current keeper and available as a smaller second item if this lane
stalls."* The lane stalled on premise, so Part B executed. **Not a lever
substituted on my own authority** — the named second item, adding no mechanism
and no degree of freedom.

The obligation was created by the ercot-202 precommit (§2/§7), which bound the
promoting commit to delete the transitional flag and the pre-repair branch. The
promotion did not, for a reason that is **measured, not preferential** and that
this session re-verified: `ScenarioConfig.with_overrides` is
`dataclasses.replace`, which **raises on an unknown key**, and the keeper's
`meta.json` carries `ercot_faststart_pool_plant_physics: True` inside
`coal_prb_sigmoid_overrides` (the `prb_overrides` replay channel). Deleting the
field without a re-solve makes the **keeper unreplayable** and breaks every
future control and re-gate.

### B.1 The construction — a deletion, not a mechanism

* `config/scenarios.py` — the field, its `_CACHE_KEY_OPTIONAL_FIELDS`
  registration, its registered default and its tier tag are **removed**.
* `data/fleet/offer_surfaces.py` — both pool bodies (stepped and the
  ercot-178/180 `contpct` form) compute `plant_md` **unconditionally**; the
  retained pre-repair row-grain branches, live only under `plant_md is None`,
  are **deleted outright** — not zeroed (rule 26: a deprecated parameter that
  still parses is a re-armable answer key); the provenance labels lose their
  dead "row (pre-repair, vacuous)" arm.
* `tests/iso/ercot/test_ercot_faststart_pool_offer.py` — the three tests that
  passed the flag now exercise the single unconditional path. The test asserting
  the **pre-repair vacuous behaviour** lost its object with the branch and was
  replaced by a **regression test on its premise**: that assembly still stamps
  the UC-coupling tags on the committed anchor alone, so a row-grain read would
  still be vacuous. If assembly ever starts stamping bid rows, that test says so
  rather than the plant-grain read silently becoming redundant.
* **Zero fitted scalars. Zero new fields. A field is REMOVED**, so the registry
  surface shrinks. `FASTSTART_POOL_MIN_DOWN_HOURS = 2.0` is untouched; no band,
  composition, ladder or boundary moves.

Test sweep at HEAD before the solve: **4,055 passed, 25 skipped, 1 xfailed**
(`tests/iso/ercot` + `tests/unit`, fast lane).

### B.2 SOLVE ENVIRONMENT — pinned to the keeper's own record

The container's `uv.lock` environment differs from the environment the keeper
was solved in, and `replay_keeper.py` said so on the first launch (**highspy
1.14.0 vs 1.15.1**, pandas 3.0.3 vs 3.0.5, pyarrow 24.0.0 vs 25.0.1). A
different HiGHS build can return a different equally-optimal vertex, which would
have made **G-REPRO uninterpretable** — a byte difference attributable to the
solver rather than to the deletion under test.

That first launch was **killed** and the three packages pinned to the bundle's
recorded versions (`run_config.json` `environment.packages`) before re-launching;
the re-launch emits **no environment warning**. Recorded here because it is a
precondition of the primary gate, not an incidental. *(Operational note for
successors: `uv run` re-syncs from `uv.lock` and silently reverts the pin — the
solve and every downstream read must use `./.venv/bin/python` directly.)*


### B.3 G-REPRO — the PRIMARY gate: **PASS, 12/12 sidecars byte-identical**

`scripts/probes/ercot204_repro.py` → `results/calibration/ercot204_repro.json`.
Every one of the 12 committed hourly sidecars (`class_hourly`, `system`,
`storage`, `reserve_family` × 2023/2024/2025) has a **sha256 identical to the
keeper's**.

**Prediction P-1 holds exactly.** This is simultaneously the deliverable and the
proof: the keeper already ran the armed path, so removing the flag removed only
a dead branch. It also means every price criterion is unmoved **by identity**,
not by measurement error — `system_<year>.parquet`, the series every price
criterion is computed from, is byte-identical in all three years.

### B.4 The remaining kill gates — measured explicitly, not inferred

Measured against the keeper with the same harnesses the ercot-202 lane used
(`scripts/probes/_ercot173_ab.py` → `ercot204_ab.json`;
`scripts/probes/ercot185_coal148.py` → `ercot204_coal148.json`):

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| C3a hub % (keeper → re-solve) | −24.38 → **−24.38** | +7.88 → **+7.88** | +0.73 → **+0.73** | — |
| C3b NRMSE | 2.9122 → **2.9122** | 2.4218 → **2.4218** | 0.9527 → **0.9527** | — |
| **G-SHED** shed hours | 4 → **4** | 1 → **1** | 0 → **0** | **PASS** (identical hour lists: 5490/5682/5802/5994; 3067; —) |
| **G-C3c** model tail >$200 (actual) | 57 → **57** (181) | 22 → **22** (53) | 1 → **1** (31) | **PASS** |
| **G-SPUR** spurious mid-band | 9 → **9** | 11 → **11** | 0 → **0** | **PASS** |
| **G-SPAN** max class energy Δ | **0.0 %** | **0.0 %** | **0.0 %** | **PASS** |
| **G-COAL148** coal above ceiling (TWh) | 0.1213 → **0.1213** | 0.1838 → **0.1838** | 0.1095 → **0.1095** | **PASS** (rise 0.0 vs the 0.5 bar) |
| **G-OWNER** | — | C3a-2024 **PASS**, C3b-2024 **0.135** | C3a-2025 **PASS** | **PASS** |
| **G-DOF** | `n_entries` **18**, `n_residual` **6** — unchanged; one field REMOVED | | | **PASS** |
| **G-D2** | D1/D2/D4 diagnostics **byte-identical**; the **same 3** pre-existing `reliability_floor × CT_PEAKER` D-4 failures (96.8 / 98.1 / 98.3 % off-window), **no new row** | | | **PASS** |

*The C3c attestation tail counts re-measured on the scorer's max-zonal basis are
**58 / 22 / 1** against actual 181 / 53 / 31 — the ledgered values exactly.*

**Determination: NOT-YET, fail set {`price_mean`, `price_shape`} = {C3a-2023,
C3b-2023} — IDENTICAL to the keeper**, verified by running the scorer on both
run ids. The C3c CAVEAT ×3 stands, its magnitudes re-measured and carried.

**LOYO** is structurally N/A and was declared so pre-solve: the change is
year-agnostic and byte-identity holds in **all three** years, which is the
held-out evidence — a deletion that changes nothing anywhere cannot buy
in-sample gain.

**No gate failed, so the adverse branch (§2.5 of the precommit) did not fire.**
The retained pre-repair branch was **not** reachable on the keeper's armed path,
which is what the deletion asserted.

### B.5 Rule 26 is DISCHARGED — verified on the artifact, not asserted

The new bundle carries the deleted flag in **no config surface**:

| surface | flag present? |
|---|---|
| `meta.json` (what `replay_keeper.py` reads) | **0 occurrences** |
| `run_config.json` → `scenario_config` | **absent** |
| `run_config.json` → `calibration_flags` | **absent** |

Two textual hits remain and both are **deliberate provenance prose** — the
`model_changes_note` and the attestation's `attested_by`, which name the deleted
flag to record what was removed. Neither is a config key, so the bundle is fully
replayable against the post-deletion `ScenarioConfig`. **That is exactly the
condition ercot-202 could not meet in place, and it is now met.**

### B.6 Retention and registration

ERCOT stood at **15** registered runs with one protected (the keeper).
Registering this run displaced **`2026-08-08-run178-continuous-grain`** — the
single oldest unprotected run, **named ex ante in the precommit §2.7** and
confirmed by `dashboard_add_run.py`'s own protected-set check. ERCOT is back at
15.

### B.7 PROMOTION RECOMMENDATION

Under the precommit's **direction-blind decision rule** (§2.6), which reads only
the kill gates and LOYO: **all live gates PASS ⇒ RECOMMEND PROMOTION** of
`2026-08-15-ercot204-rule26-delete`.

**The recommendation rests on rule-26 discharge alone. No metric gain is claimed
and none exists — by byte-identity, not by argument.** The keeper's numbers are
this run's numbers, to the sha256. What changes is that the model no longer
carries a transitional flag and a dead branch that could be re-armed, and no
bundle references either.

**The keeper is NOT changed in-session** (dispatch): no keeper shard, registry
keeper field, or `calibration-complete.json` entry was edited. ERCOT holds no
`complete` marker, so no D-5(b) re-key applies.

Should the owner promote, two follow-ons are named, not done here: the ercot-202
bundle (`ercot202_plantphysics_B`) becomes unreplayable against HEAD's
`ScenarioConfig` — its `meta.json` still carries the deleted key — which is the
expected and intended cost of the deletion, and is precisely why the successor
required a re-solve rather than an in-place edit.

### B.8 What Part B does NOT claim or touch

* **No claim on C3a-2023 or C3b-2023** (Q-B final; card R-A). There is no
  movement to report: the series are byte-identical.
* **No C3c ledger change, no rubric amendment.** The CAVEAT ×3 stands.
* **No mechanism added, no band moved, no artifact re-derived.**
  `FASTSTART_POOL_MIN_DOWN_HOURS = 2.0` untouched; rule 23 not engaged.
* **No holdout marker granted or spent**; `--years` never left {2023, 2024, 2025}.
* **INHERITED NAMED PERMANENT LIMITATION (ercot-188/E2, unexpired):**
  `ercot_econ_curve_top_refine` writes heat rates into the P0 objective on this
  keeper, so the offer-surface family's **P0 bit-identity proof stays
  forfeited**. Stated so B.3 is not over-read: it is a whole-solve reproduction,
  not a seam proof.

**Next shorthand: ercot-205.**
