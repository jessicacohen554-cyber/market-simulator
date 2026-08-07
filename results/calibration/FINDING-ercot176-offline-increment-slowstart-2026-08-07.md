# FINDING — ercot-176: the offline-increment SLOW-START tier is BUILT, measured, and **PROVABLY INERT** — the charter's CC object does not exist in RT conduct; the physics gate's grain is a defect found in an armed keeper mechanism; keeper RE-KEYED to the control replay

**Session ercot-176, 2026-08-07.** Charter: the ERCOT-151 §3 design round,
owner-authorized in-session 2026-08-07 (the ercot-175 decision card), discharging
that document's §4 ask (2). Object: **C3a-2023** (−29.9 % lw-hub / −32.2 %
scorer), fail set {C3a, C3b}.

Pre-registration: `docs/PRECOMMIT-ercot176-offline-increment-2026-08-07.md`,
pushed **before** any derive or measurement, with **three pre-solve amendments**
(all pushed before the solve, none after).

---

## 0. Verdict

| | |
|---|---|
| **Mechanism** | `ercot_offline_commit_offer` — BUILT, default-off, zero fitted scalars |
| **Artifact** | `ercot_faststart_pool_condbinned.json` gains a `CC` block (2023/2024/2025) by the ERCOT-88 construction |
| **Derive integrity (SP-6)** | CT sub-tree **byte-identical** across the extension, all three years (sha256 `7f02b6f5…`) |
| **Seam proof** | `ALL_ASSERTIONS_PASS = true` (SP-1, SP-2a/b, SP-6 pass; SP-3/4/5 vacuous with reason) |
| **Arm verdict** | **PROVABLY INERT** — builder returns `None` for 2023, 2024 and 2025 on the real keeper fleet with 213 physics-eligible bid rows |
| **Arm solved?** | **NO — and no arm run is registered.** It is not a different run: `None` ⇒ `p1_bid_max_target` stays `None` ⇒ byte-identical code path. Stated explicitly so the absence is not read as a skipped registration (rules 15/16), the ercot-175 §0 precedent. |
| **Control** | SOLVED and REGISTERED, full span `--year 2023 2024 2025` — `2026-08-07-run176-control-offline-increment` |
| **Keeper** | **RE-KEYED to the control replay** per the owner ruling; run168b non-reproduction item **RETIRED — it reproduces** (§2b) |
| **Kill gates** | G-DOF satisfied outright (zero scalars created); every other gate requires a solved arm — **NOT REACHED** |

## 1. The charter premise this session did NOT rest on

The handoff cited ERCOT-151 §0.2 as THE CHARTER: *"18.1 GW startable-OFF CC+CT,
~13.5 GW of it submitted-DAM ≤ $200."* **That figure is refuted**, by the
ERCOT-163 correction banner carried at the head of the very diagnosis the handoff
points to: measured on the delivery-2023 SCED corpus at the committed gap hours,
ERCOT's CC fleet was **96.4 % committed and 98.0 % loaded**, with **0.020 GW**
offline-startable. ercot-175 §2 corroborates from the other side (~0.9 GW of
sub-$200 startable offered). The precommit §0 said so before anything was built
and withdrew ERCOT-151's expected-magnitude arithmetic with it.

The justification that survived, and that this session tested:

> The model prices its own uncommitted increment at base cost **as if no start
> were required** (availability is only-OUT-is-out — correct, rule 13), while
> measured SCED conduct prices that capability **start-inclusive**. P1's startup
> amortization is the only start term and is the wrong identification by ~30×
> ($20–30/MWh against a CT-tier ladder whose p50 is $271–707).

That defect is real. What this session establishes is that **the CC half of it
carries no MW.**

## 2. The measurement — why the slow-start tier is inert

The CC block derives by the **identical** construction as the ERCOT-88 CT block
(above-LSL SCED2 segments of OFFQS/OFFNS rows; MW-weighted quantile ladder as
effective-HR multiplier; `pool_frac` = interval-mean offline-startable MW over
the class's own non-OUT live capability), against `CCGT90`/`CCLE90`:

| year | `pool_frac_CC` by net-load bin | ladder p70 (× gas) |
|---|---|---|
| 2023 | 0.0002 – 0.0006 | 36.6 – 39.7 |
| 2024 | 0.0002 – 0.0006 | 54.1 – 77.8 |
| 2025 | 0.0004 – 0.0007 | 24.1 – 33.5 |

Two independent facts, either of which alone makes the tier inert:

1. **Quantity.** The measured slow-start offline share is **0.02–0.07 %** of CC
   live capability — against the pre-registered inertness threshold of 2 %, i.e.
   **~30× below it**. The resulting boundary `1 − pool_frac` = **0.9993–0.9994**
   sits **above** the largest within-plant share midpoint the model's tranche
   geometry can produce, **0.9984**. *The measured CC offline increment is finer
   than the model's finest bid tranche*, so no row can clear the boundary in any
   hour of any year.
2. **Price.** The ladder is **cheap** — p70 multiplier 24–40 × gas ≈ $100/MWh,
   nowhere near the CT tier's p50 $271–707. Even a fleet with the granularity to
   express this increment would not be repriced into scarcity by it.

This is the pre-registered **P-2** falsifier firing exactly as written, and it is
a *third* independent corroboration of ERCOT-163 (DAM instrument) and ercot-175
(SCED sub-$200 slice), now on the full-year RT conduct of the CC class itself.

**The structural reading (rule 1).** ERCOT's merchant CC fleet does not sit
offline-and-cheap at tight hours; it self-commits into real time and is already
loaded. There is no slow-start OFF increment to reprice. The start-economics
identification remains correct in principle — but its MW live in the **fast-start
CT** pool (already armed, ERCOT-88) and, if anywhere else, in **commitment
state** rather than in the offered-capability share this construction can see.

## 2b. The control — the run168b non-reproduction item is RETIRED

The control is the run168b recipe replayed at HEAD with **zero deltas**
(`scripts/replay_keeper.py`, no `--set`), full span solved in-session. ercot-173
§5 had disclosed that run168b "does not reproduce at current main". **It does.**

| | run168b (committed) | ercot-176 control @ HEAD |
|---|---|---|
| C3a 2023 | −32.2 % | **−32.4 %** |
| C3b 2023 | 0.6043 | **0.602** |
| C3b 2024 | 0.206 | **0.205** |
| C3c tail counts | 61/181, 25/53, 3/31 | **identical** |
| determination | NOT-YET {C3a, C3b} | **NOT-YET {C3a, C3b}** |
| C1 / C2 / C4 / C6 / C8 | PASS | **PASS** |
| DOF ledger | 13 entries / 6 residual | **inherited unchanged** |

The residual drift is **0.2 pp on C3a-2023** and sub-0.002 on both C3b legs, with
the ledgered tail counts bit-stable — i.e. the recipe is reproducible at HEAD and
the ercot-173 observation was a transient of that session's base, not a defect in
the keeper. `audit_keepers --iso ERCOT` PASS (0 failures, 0 warnings), with the
scorer re-run independently against the committed artifacts.

ERCOT holds **no `complete` and no `final` marker**, so no
`calibration-complete.json` re-key applies (rule 22 D-5(b) does not fire).

## 3. The defect found in an armed keeper mechanism (rule 18, reported not acted on)

The seam proof's first run returned `n_physics_eligible_rows = 0`. Cause: **fleet
assembly records unit physics on the `committed` tranche only.** Every
`econ*`/`peak*` row — the bid rows every offer surface prices — carries
`min_down_hours = min_run_hours = 0`:

| group | tranche | (min_down, min_run) |
|---|---|---|
| CC_REGULAR | committed | (4,4) (4,6) (4,8) (6,16) |
| CC_REGULAR | econc / peak | **(0, 0)** |
| CT_PEAKER | econc / peak | **(0, 0)** |

At tranche-row grain a physics test is therefore **vacuous in both directions**.
This session fixed its own tier (Amendment 2: physics read per plant, inherited
by the plant's bid rows — 42 CC plants → **23 eligible, 213 bid rows**, 17
excluded by the pre-registered 12 h min-run bound, which was deliberately **not**
widened after seeing what it excluded).

**The same defect sits in `ercot_faststart_pool_offer`, which is ARMED IN THE
CURRENT KEEPER (`K`).** Its gate is `skip if min_down > 2`, so with every bid row
reading 0 it **admits every CT bid row regardless of physics** — its effective
scope is the `CT_PEAKER` class map, i.e. precisely the class tuple rule 18
`[R-PHYSICS]` forbids, rather than the intended min-down test.

**Not acted on here, by design:** out of charter, it would move the keeper, and
it needs its own pre-registered round. Filed as owner item §5.1. Note this does
**not** by itself invalidate ERCOT-88 — CT physics is uniform (min-down 1 h), so
the admitted set likely coincides with the intended one; what is wrong is that
the gate *is not testing anything*, so it provides no protection if CT physics
ever becomes heterogeneous.

## 4. Predictions adjudicated (pre-registered §8)

* **P-1 (C3a-2023 improves).** **NOT TESTED** — no arm was solved because none
  exists to solve. No magnitude was claimed and none is reported.
* **P-2 (inertness, "the likeliest failure").** **FIRED, exactly as written.**
  The pre-registered trigger was `pool_frac` < 0.02 in the top bin; measured
  0.0004–0.0006. Reported as the finding.
* **P-3 (C3c formation matched, not invented).** Vacuous — no formation occurred.
* **P-4 (C3b).** Vacuous — no arm.
* **P-5 (D-2/D-4 zero forced energy).** Satisfied by construction and confirmed:
  the tier touches no bound, and it owns no row-hour in any case.

## 5. Owner items — filed, NOT decided

1. **The rule-18 physics-gate grain defect in `ercot_faststart_pool_offer`**
   (§3), an armed keeper mechanism. Needs its own pre-registered round; fixing it
   moves the keeper.
2. **The min-run bound and the 17 excluded CC plants.** Assembled CC min-run
   reads {4, 6, 8, 16} h, and the pre-registered 12 h bound excludes the 16 h
   group. It was not moved in-session. A successor wanting those plants must
   pre-register that band itself — and should note the bound's §1 rationale was
   framed against `ST_GAS_COMMITMENT_PARAMS`' 24/48 h while **assembled** ST_GAS
   physics reads (8, 8), so the bound is not what excludes gas steam here (the
   class-scoped row universe is, leaving the ERCOT-91-`R` cell closed either
   way).
3. **Where the start-economics object goes next.** Bounded away from the CC
   offered-capability share by this session, from aggregate depth by ercot-173,
   from reserve/AS by ERCOT-102/107/108, and from SCED-grain deliverability by
   ercot-175. What remains untested is **commitment state** rather than offered
   share — but note ERCOT-163 already measured the CC fleet 96.4 % committed at
   the gap hours, so that route needs a new premise, not a new mechanism.
4. **The ERCOT-148/149 double-count memo**
   (`docs/handoffs/DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md`) stays
   **PENDING**; the ceiling lane was not entered.

## 6. Governance

* **Rules 15/16:** the control is registered, all three years, one bundle. The
  arm is not solved and not registered — §0 states this explicitly.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. ERCOT holds no `complete` and no
  `final` marker; 2022 / 2019 / H1-2026 were not solved, scored, read or
  registered. No `calibration-complete.json` re-key applies.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the re-derive is licensed by a source-data
  change (the ERCOT-157 delivery-2023 corpus) plus a new class scope — never by a
  residual. CT byte-identity proves the extension changed nothing incumbent.
* **Rule 24 `[R-REGISTRY]`:** one `ScenarioConfig` field (+ path override), in
  `run_config.json`. No env-var knob, no per-plant dict.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-gated; SP-1 confirms non-ERCOT returns
  `None`.
* **Rule 27 `[R-PUSH]`:** every push touching a ≥300-line file blob-verified
  against the **remote** blob sha (`offer_surfaces.py` 2841 lines,
  `fed766bc…`, matched). Mid-session the branch was auto-deleted by the merge of
  PR #3690; the three merged commits were left in main and the one unmerged
  commit rebased onto the new default branch, per the merged-PR protocol.
* **Rule 28 `[R-MECH-MATRIX]`:** matrix §5.1 gains **item 19**; the
  `ercot_offline_commit_offer` row was added in the same PR as the field (duty c)
  and carries the final `I` verdict (duty b); the `ercot_faststart_pool_offer`
  cell is annotated with the §3 grain defect without changing its status.
* **GitHub Actions:** no workflow added; the solve ran in-session.

**DO-NOT-REDO honoured in full** — the event-cap ceiling lane was not entered
(its memo stays PENDING and was not acted on); the depth premise was not
re-litigated; the reserve family was not re-opened; no ramp mechanism; no storage
offer surface; no per-hour or aggregate capability cap; no coal offer lane;
West/Panhandle stayed closed; ercot-172's C3 not attempted; the CC-headroom
crosswalk stays FILED-UNLICENSED; per-year CT re-identification not attempted.

**Next shorthand: ercot-177.**
