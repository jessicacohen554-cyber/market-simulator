# PRECOMMIT — caiso-236: LEDGER-INTEGRITY audit of the keeper's seven residual-identified free parameters

**Registered 2026-09-02, session caiso-236. Branch
`claude/caiso-dof-residual-audit-7nvz6x`, cut fresh from `origin/main`
(`4692598f`). PUSHED BEFORE ANY CLASSIFICATION WAS COMPUTED** — not merely before
the solve. Nothing in `src/`, `scripts/` or the keeper's hourly sidecars has been
read for liveness at the moment this file is pushed; the only objects read are the
keeper's `calibration_attestation.json` (the ledger under audit — it is the *object*,
not evidence about it) and the directory listing of its `hourly/`.

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`** (bundle
`results/calibration/caiso231_b1_ungrounded`), determination **NOT-YET**, **C3a the
SOLE load-bearing FAIL** (+4.1 / +12.5 / +15.6 %, 2023 passes); C3b PASS; C3c the
single ledgered caveat; C6 attested; C8 PASS; `audit_keepers --iso CAISO` PASS 0/0.
CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**. Every read in this session stays inside **2023–2025**.

---

## §0 — WHAT THIS SESSION IS, AND WHAT IT MAY NOT BECOME

**§0.1 — The CAISO lane is RESTED AT NOT-YET by owner ruling (caiso-201,
2026-08-17).** No further CAISO calibration session without new funded data; neither
standing object is funded; the in-model lever queue is EMPTY (exhausted by
measurement at caiso-200, last named object +0.003 TWh); all three named exits are
closed (public-bid SPENT AND CLOSED at caiso-178; degradation-split SPENT AND
REFUTED at caiso-179).

**§0.2 — This session is admissible under that ruling because it is NOT a lever
hunt.** It is a rule-21 `[R-DOF]` / rule-26 `[R-DELETE]` **ledger-integrity** lane.
Rule 26 is explicit that *"a deprecated parameter that still parses is a re-armable
answer key"*, and rule 21 requires every free parameter to carry an identification
source. The attestation claims `n_entries=11, n_residual=7`. The deliverable is an
**honest ledger** — not a better residual.

**§0.3 — C3a IS NEVER THIS SESSION'S OBJECTIVE.** No result of this session may be
argued from the price residual (rule 1 `[R-STRUCT]`). If a mechanism that could move
C3a is proposed, the charter has been left and the session stops and says so. A
(b)-class action that turns out to move ANY scored number is, by this document's own
stop rule (§4.3), evidence the parameter was material — it is reverted and
re-classified, never kept.

**§0.4 — DO-NOT-REDO acknowledged (rule 28(a)).** None of the following is re-opened
by this charter and none is proposed here: the import-depth object (CLOSED as NOT
IDENTIFIABLE after three pre-registered estimator failures — caiso-233 CV 0.550 /
LOYO 491.7 %; caiso-234 0.120 / 34.2 %; caiso-235 on 2019–2025 0.266 / 55.0 %, the
obstacle established as a 2022/23 **regime break**, not sample length — DOF
`spot_capacity` permanently declared to the owner); the price Q-Q route
`derive_caiso_import_tranches.py` (LOYO 30.5 % vs a 25 % bar, caiso-83/86b — its
`RUNGS` map covers all five priced rungs **including the two firm ones**, so the firm
PRICES are adjudicated by that same failure); re-grounding CC_CHP / CT_CHP / ST_GAS
or the two committed bands; `caiso_solar_cap_at_delivered`; `ramp_envelopes`;
`caiso_corridor_export_path`; `caiso_p1_export_sink_seam`; `caiso_da_rt_two_settlement`;
`cc_committed_offer_margin`; `storage_daily_cycling`; the sub-zonal congestion route
(CEII-blocked); the two standing owner objects (PS water-state; the 8,800 MW re-open
on assertion).

---

## §1 — THE TAXONOMY, FIXED IN ADVANCE

Every one of the seven entries is assigned to exactly one of three classes. **The
class determines the action; the action is not chosen after the fact.**

| class | definition | permitted action |
|---|---|---|
| **(a) DEAD FALLBACK** | the code path that reads the value is **gated off** under the keeper's own `run_config.json` gates, so no keeper solve can consult it | **DELETE** (rule 26) — not zeroed, not left parsing |
| **(b) LIVE BUT IMMATERIAL** | the value **is** read, but the quantity it governs cannot move any gated criterion, bounded **arithmetically** (§2) | **NEUTRALIZE** to the generic fallback so the CAISO path carries no fitted value, **proved byte-identical** by the §4 A/B |
| **(c) LIVE AND MATERIAL** | anything else | **REPORT ONLY.** Naming it for the owner is the whole action. Grounding a live residual is a funded-object question under the resting ruling, not this session's to take. |

**Decision rule, fixed here so the taxonomy cannot be drawn around what is found:**

1. Read the code path from the ScenarioConfig / constants symbol to its consumer.
2. If every read of the CAISO value sits under a gate that `run_config.json` records
   as **off** for this keeper → **(a)**. The gate must be read from the keeper's own
   `run_config.json`, never asserted.
3. Else the entry is LIVE. Compute the §2 materiality bound. Bound satisfied → **(b)**;
   bound not satisfied, or not computable from committed artifacts → **(c)**.
4. **Ties, ambiguity and any inability to establish (a) or (b) resolve to (c).** (c) is
   the fail-closed class: its action is "report and do not touch", which is never
   harmful.

**§1.1 — Deletion safety clause.** If an (a)-class deletion cannot be done without
touching a shared cross-ISO code path, the session **stops at the report** rather than
half-deleting, and says so. Removing a **per-ISO key from a cross-ISO registry dict**
(e.g. one ISO's entry in a `{ISO: …}` mapping) is NOT a shared-path edit and is
permitted; deleting the dict, its consumer, or a `ScenarioConfig` field read by other
ISOs is.

**§1.2 — Rule 28(c) clause.** A DELETED `ScenarioConfig` field requires its base
mechanism-matrix row retired **plus** the cell line removed from **every** shard — the
one deliberately non-parallel edit. `scripts/check_mechanism_matrix.py` is run before
pushing. A deletion confined to a constants-module dict key touches no matrix row.

---

## §2 — THE MATERIALITY BOUND: ITS FORM, FIXED IN ADVANCE

For an entry whose value governs a **generator class** X (this is the only shape any
of the seven takes), the bound is computed **arithmetically from the keeper's own
committed P1 class hourlies** (`hourly/class_hourly_<year>.parquet`) — **never** from
an LP result, and never from a re-solve:

* `E_X(y)` = X's modelled annual energy, TWh, and its share of total modelled
  dispatch;
* `H_X(y)` = the count of hours in year `y` in which X's modelled output is
  **strictly greater than zero**.

`H_X` is a **necessary** upper bound on the hours in which X's offer can enter the
energy-balance dual at all: a class at exactly zero output in an hour is not a
generating unit in that hour, so its offer price is not the marginal cost of a
strictly-interior column in that hour's basis.

**The entry passes the bound (⇒ candidate (b)) iff, in ALL THREE of 2023/2024/2025:**

* energy share ≤ **0.10 %** of total modelled dispatch, **AND**
* `H_X / 8760` ≤ **1.0 %** of hours.

Both thresholds are fixed now and are not adjusted after measurement. **The bound is
necessary, not sufficient** — it is a screen, and the §4 byte-identity A/B is the
actual proof. An entry passing the bound but failing byte-identity is (c), per §4.3.

For an entry governing a **transmission/seam limit**, the bound is instead a
**binding-hour count** read from the keeper's committed system hourlies: the entry is
IMMATERIAL only if the modelled quantity it caps **never attains** the capped value in
any of the three years. A limit that is attained in even one hour is **(c)**.

---

## §3 — PER-ENTRY PRE-REGISTERED PREDICTIONS

**Committing to a per-entry prediction is what stops the taxonomy being drawn around
whatever is found.** Each row states the predicted class, the reasoning available
*before* any code reading, and the specific observation that would falsify it.

| # | entry | keeper value | **PREDICTED CLASS** | falsifier |
|---|---|---|---|---|
| 1 | `offer_curve_by_group` | 112 scalars, 13 groups | **(c) LIVE AND MATERIAL** | the CAISO gas groups are unread under the keeper's `caiso_offer_surface_measured*` gates |
| 2 | `offer_curve_committed_below_floor[CAISO]` | `ST_GAS: 0.81` | **(c) LIVE AND MATERIAL** | ST_GAS committed tranche carries ≤0.10 % of dispatch **and** <1 % of hours |
| 3 | `offer_curve_smoothing` | `n=6, exp=1.0, mid=None` | **(c) LIVE AND MATERIAL** | the smoothing consumer is gated off, or `n`/`exp` at these values is a provable identity transform |
| 4 | `COAL_SIGMOID_DEFAULTS[CAISO]` | passthrough 1.0, sigmoid True | **(b) LIVE BUT IMMATERIAL** — *conditional*: **(a)** if no CAISO unit carries the PRB coal key at all | coal clears **either** §2 threshold in any year; or the §4 A/B is not byte-identical |
| 5 | `battery_dispatch_adder` | `5.0` $/MWh | **(c) LIVE AND MATERIAL** | CAISO storage discharge is ≤0.10 % of dispatch (it is not — CAISO storage is one of the largest fleets in the model) |
| 6 | `WECC_import_simultaneous.cap_mw` | `7500.0` | **(c) LIVE AND MATERIAL** — **AGAINST THE CHARTER'S OWN EXPECTATION** (§3.1) | net import never attains 7,500.0 MW in any of the three years on the keeper's committed hourlies |
| 7a | `IMPORT_TRANCHES[CAISO]` | 6 fitted scalars | **(c) LIVE AND MATERIAL, and already DECLARED** (§3.2) | the import ladder is unread under `caiso_per_hub_intertie=True` |
| 7b | `EXPORT_TRANCHES[CAISO]` | export ladder | **(a) DEAD FALLBACK** (§3.3) | the export leg reads the ladder under `caiso_per_hub_intertie=True` |
| + | `CAISO_BIDIR_EXPORT_CAP_MW` | `4361.0` | **(a) DEAD FALLBACK** (§3.4) | `caiso_bidir_intertie` is not the sole gate on its read path |

**§3.1 — Entry 6 is predicted (c), i.e. the charter's "prime candidate for (a)" is
predicted WRONG, and this is registered before it is checked.** The charter reasons
that `capacity_deliverability_limits=True` supersedes the fitted 7,500 with the
published branch-group MIC sum, making the fallback dead. The keeper's own ledger text
records the opposite as a **measurement**: caiso-188 found every CAISO bundle from
caiso-175 onward — the then-keeper included — pinning total net import at **exactly
7,500.0 MW in 764 / 477 / 809 hours** of 2023/24/25 while `run_config.json` records
`capacity_deliverability_limits: true`, because Part A resolves through the
**gitignored, disposable** clean partition `data/clean/capacity-deliverability/` that
no solve auto-builds. If that silent no-op still holds at this keeper, the flag being
`true` proves nothing and the scalar is on the binding path. **The test is the
binding-hour count of §2 on THIS keeper's committed system hourlies, not caiso-188's
older bundle** — a prior bundle's pin is not this bundle's. If the pin is absent here,
the prediction is falsified and the entry is (a); that outcome is reported as a
prediction miss, not quietly absorbed.

**§3.2 — Entry 7a is DECLARED, not open.** The import-depth object is closed as NOT
IDENTIFIABLE and returned to the owner permanently declared (§0.4). It is classified
(c) — live, material, and already owner-held — and this session proposes **no fourth
construction, no further widening, and no regime-aware form**. Its treatment here is
purely to record the class.

**§3.3 — Entry 7b is predicted (a) on the ledger's own words.** The committed entry
states: *"EXPORT_TRANCHES[CAISO] is NOT on this keeper's binding path at all — the
per-hub export legs are bounded by the published corridor link ratings (COI 4,800 /
Path-46 10,623 MW)."* With `caiso_per_hub_intertie=True`, the ladder's export half is
predicted unread. **But the ledger sentence is an assertion until the code path is
read** — exactly the failure mode caiso-188 caught on entry 6 ("the earlier 'not in
the keeper binding path' text was an assertion, not a measurement"). It is therefore
re-established from code here, not cited.

**§3.4 — `CAISO_BIDIR_EXPORT_CAP_MW` is audited in this pass although it is classed
`measured-physical`, not `residual`.** Rule 26 is about *re-armable dead knobs*, not
about identification class: `caiso_bidir_intertie` is **FALSE** on this keeper and the
ledger's own note calls the constant *"fallback-only (superseded by
`caiso_per_hub_intertie`) … or R5-delete the `caiso_bidir_intertie` mechanism (rule
26)"*. It is checked under the same logic. **Note the §1.1 stop clause applies with
force here**: `caiso_bidir_intertie` is a `ScenarioConfig` field with a
mechanism-matrix row, so deleting *the mechanism* is a rule-28(c) all-shard edit,
whereas neutralizing only the constant would leave the mechanism parsing. The action
taken will be stated explicitly against §1.1/§1.2 and, if the mechanism itself must
go, that is done in full or not at all.

**§3.5 — Prior probability stated honestly.** Predicted counts: **(a) = 2**
(7b, `CAISO_BIDIR_EXPORT_CAP_MW`), **(b) = 1** (entry 4), **(c) = 5** (1, 2, 3, 5, 6,
7a — six items over five ledger entries). Predicted honest residual count after the
pass: **7 → 6** ledger residual entries if entry 4's CAISO key is removed and entry 7
is re-scoped to its import half; **`n_entries` 11 → 10** if
`CAISO_BIDIR_EXPORT_CAP_MW` is deleted. These numbers are predictions, not targets;
the ledger is rebuilt by `scripts/build_dof_ledger.py` and whatever it emits is
reported.

**§3.6 — The all-live outcome is a real result and is pre-authorized as the stopping
point.** If Phase 0 finds all seven LIVE AND MATERIAL, the FINDING is written and the
session STOPS with zero code changes. That says the ledger is already honest. It is
reported as such and **not padded into an action**.

---

## §4 — THE ONLY SOLVE THIS SESSION MAY RUN, AND ITS ACCEPTANCE TEST

**§4.1 — A solve happens if and only if at least one entry classifies (b).** No
(a)-class deletion requires a solve (a dead path cannot change a solve; the deletion's
own proof is the code reading). No (c)-class entry is touched.

**§4.2 — The A/B, fixed in advance.** Single same-HEAD pair, `--year 2023 2024 2025`
in **ONE** invocation, years **sequential** (rules 12 `[R-PARALLEL]` / 16
`[R-ALLYEARS]`), scored on **P1**:

* **A0** — `--replay-bundle results/calibration/caiso231_b1_ungrounded`, **zero
  delta**. The control.
* **B1** — the neutralization as the **ONLY** delta.

**§4.3 — Acceptance is BYTE-IDENTITY, defined now:**

* `max |Δ|` over every (hour × zone) of the P1 zonal price series = **exactly 0.0**;
* `max |Δ|` over every (hour × class) of the P1 class dispatch = **exactly 0.0**;
* every scored metric in `metrics.json` identical at full stored precision, all three
  years.

**If it is NOT byte-identical, the parameter was material after all: B1 is REVERTED,
the entry is RE-CLASSIFIED (c), and that is reported AGAINST INTEREST** as a failed
prediction — not re-argued, not partially kept, and above all not evaluated on whether
the difference improved anything (rule 1 `[R-STRUCT]`; §0.3).

**§4.4 — Registration.** If any A/B runs, **BOTH ARMS** are registered on the backcast
dashboard (rule 15 `[R-DASHBOARD]`) in this session, keeper or not.

---

## §5 — DELIVERABLES

1. **This PRECOMMIT**, pushed before classification — done at push time of this commit.
2. **`FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md`** in
   `results/calibration/`: the per-entry classification with its evidence line, every
   prediction scored hit/miss, and the honest residual count.
3. **The classification instrument** under `scripts/probes/`, so every class call is
   re-checkable from committed artifacts.
4. **The rebuilt DOF ledger** (`scripts/build_dof_ledger.py <bundle> --iso CAISO`).
5. Dashboard registration for **both arms** of any A/B (rule 15).
6. A `docs/calibration-log/caiso.md` entry.
7. **CAISO-shard-only** mechanism-matrix updates (rule 28(b)) on any cell whose field
   is deleted or neutralized; a deleted `ScenarioConfig` field additionally retires its
   base row and its cell line in **every** shard (rule 28(c)), with
   `scripts/check_mechanism_matrix.py` run before pushing.
8. If a keeper is re-registered: `keepers/CAISO.json` re-stamped and
   `calibration-keeper-auditor --iso CAISO` run.

---

## §6 — THE STOP CONDITIONS

The session stops and reports, without acting, if any of these fire:

* an (a)-class deletion would touch a shared cross-ISO path (§1.1);
* a (b)-class neutralization fails byte-identity (§4.3) — revert, re-class (c);
* all seven classify (c) (§3.6);
* any proposed action could move C3a (§0.3).

*Pre-registered 2026-09-02 by session caiso-236 before any classification was
computed. Amendments are additive and dated; nothing above is edited in place.*
