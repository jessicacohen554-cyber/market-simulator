# FINDING — ercot-226: the 2023 held-sequestration factor program — F1/F1b/F3/F4 REFUTED-P0 on the measured record, F2 (held-location) built and probed, and THE 3-year design bundle

**Session ercot-226 (owner-dispatched program; the dispatch IS the owner,
waivers W-1..W-5), 2026-08-22, branch
`claude/ercot-2023-summer-scarcity-9lg3nm`. Keeper at open:
`2026-08-20-ercot223-arm-eventrelease` (NOT-YET, {C3a-2023 −39.7 %,
C3b-2023 0.729}, C3c ledgered ×3). Precommit
`docs/PRECOMMIT-ercot226-held-sequestration-2026-08-22.md` pushed +
blob-verified (519 lines, blob-sha-verified against the remote) BEFORE any
measurement or solve; Amendment 1 (§5.10) landed before any probe was
scored. Executed hub-and-spokes per the owner's mid-session parallelization
instruction (precommit §0/§6).**

## 0. Directive-premise corrections (recorded per precommit §0b)

1. **B-1 is SIGNED and SPENT, not unsigned** (signature-by-dispatch of
   ercot-219, commit `ecbad28`; refuted-as-armed there). The UNSIGNED card
   is **B-2** (DO-NOT-SIGN). W-5's substance is honored exactly: Stage 1
   (`ercot_capability_reconciliation`) stays unarmed, B-2 stays unsigned,
   and nothing in this program touches either.
2. **"W-3" namespace**: the owner waiver W-3 (ercot-226) is distinct from
   card-W's vacant W-3 instrument slot (ercot-200 §5); the card-W fence
   (IMM's own quantification is never identification) was honored — every
   factor identifies from measured quantities, never from the IMM's effect
   estimates.
3. **Environment pins**: requirements.txt trails the keeper environment
   (highspy 1.14.0/pandas 3.0.3/pyarrow 24.0.0 vs the keeper's
   1.15.1/3.0.5/25.0.1); every solving session pinned the keeper versions
   explicitly and verified before its control replay.

## 1. THE FACTOR TABLE — verdicts

| factor | object | Phase-0 measurement | verdict |
|---|---|---|---|
| **F1** held-depth (rigid products) | `max(plan, held)` from NP3-965 telemetered responsibilities | delta `max(0, held−plan)` ≡ **0.0 MW p50 at the keeper miss set** (114 h); monthly held/plan: RRS ~1,100/2,900, ECRS 600–930/1,450–2,130, REGUP 260–380/344–454 | **REFUTED-P0** — no solve, no field built |
| **F1b** NSPIN held-depth | same, NSRS column | delta ≡ 0.0 MW p50 at miss set (held 520–1,080 vs plan 2,206–5,051) | **REFUTED-P0** |
| **F2** held-location (per-class carve) | measured per-class allocation of the rigid holds | **1,051 MW p50** of rigid-product holds on online thermal at the miss hours (gas_st 543 / coal 221 / gas_cc 155; storage 1,762 already armed) | **PROCEED-BUILD → probed (§3)** |
| **F3** RUC/OOM MW | measured RUC commitment MW | no 2023 series on disk (RUC AS disclosure is 2025/2026-only); sign ~0/negative; price side owned by `ercot_rtordpa_overlay` K (rule 19) | **REFUTED-P0** |
| **F4** load-forecast conservatism | operator DA-forecast bias | no measured series in repo; procurement-sizing entry double-counts the armed plan; ORDC entry channel-forbidden (RTORPA ≈ $1 at target hours) | **REFUTED-P0** |
| **F5** deployment-design depth | anything beyond rigid-at-VOLL | armed representation already maximal; storage AS measured-credited (telemetered/award means: regup 205/269, rrs 882/844, ecrs 127/120, nonspin 16/15 MW); LR-RRS armed; online-NSPIN → F1b | **ALREADY-CARRIED** |

Committed record: `results/calibration/ercot226_helddepth_phase0.json`
(kill checks, margins, location screen), the derive's printed validations
(HASL ≈ HSL − Σresp median dev **0.00 MW** on 26,052 sample rows), and
`results/calibration/ercot226_probe_f2.json` (the F2 A/B).

**Why F1's zero is itself a finding.** The Gen-resource ONLINE telemetered
basis is a *subset* of the plan's provider space — Load Resources and
offline Non-Spin are outside the corpus — so held < plan by construction
wherever LR/offline provision is material. The conservatism depth is NOT in
the system-level gen-side quantity: the operator's conservative product IS
the plan, already armed. What the plan does not carry is WHERE the holds
sat — which is exactly F2, and exactly the ercot-217 §5 slack-dual wedge
("the model holds the full measured plan and still carries more responsive
headroom than the real grid retained").

## 2. THE F2 MECHANISM (built; `ercot_as_held_location`, default off)

Per measured thermal class (gas_cc / coal / gas_st): a new reserve class +
class-scoped headroom row `Σ_{g∈C∩z} P + R[c_C,z] ≤ cap(C,z)` (storage room
excluded via the new `headroom_storage` per-row opt-out — None ⇒
byte-identical legacy path), a rigid VOLL-step family requiring the class's
measured held MW clipped at the class's own pmax×availability (data-vs-data,
zero fitted scalars), and a CONSERVING credit on the product requirements —
total held quantity unchanged (rule 19: location only). Held series are
zero outside published coverage ⇒ uncovered years byte-identical to
flag-off (the 2024/2025 invariance is by construction). Registered per the
nyiso-119 discipline in the same commit (cache-key, defaults table,
`_BACKCAST_ONLY_OVERLAY_FIELDS`, TIER_TAGS), D5 row + D-4
no-row-by-construction declaration in `scripts/legitimacy_diagnostics.py`,
matrix base row + cells in every ISO shard, 10 hermetic tests
(`tests/iso/ercot/test_ercot_as_held_location.py`). Implementation:
`model/reserves/spec.py` (`ERCOT_HELD_CLASS_GROUPS`, `_ercot_rigid_end`
behavior-identical refactor, the class-family block),
`results/scarcity.py::ercot_as_held_by_class_mw`,
`lp/{reserve_rows,rows,model}.py` (`headroom_storage` threading).

**Amendment 1 (gate correction, before any probe):** the keeper's own rigid
families engage their VOLL steps in 21 hours of 2023 (ECRS 11 / RRS 9 /
RegUp 11 shortfall hours — the designed scarcity expression at caught
hours), so the no-manufactured-shortage rule is the G-SHED subset form (arm
shortfall hour-set ⊆ control's per family), never absolute zero
(precommit §5.10; `ercot226_gates.py` G-SHORTFALL).

## 3. THE F2 PROBE (2023-only A/B vs the keeper config, hub-executed) —
**REJECTED-AS-ARMED, direction NEGATIVE**

Committed record: `results/calibration/ercot226_probe_f2.json` +
`ercot226_f2_gates_hub.json` (full hour lists). Control G-REPRO: the hub
control replay reproduces the keeper's committed 2023 sidecars to
**numeric identity** (max|Δ| = 0.0 on every numeric column; the sha256
difference is parquet file-layout only) and the official scorer to the
printed digit.

| official (2023) | control | arm |
|---|---|---|
| C3a (load-weighted vs RT 64.32) | **−39.7 %** (38.81) | **−45.5 %** (35.04) |
| C3b monthly NRMSE | **0.729** | **0.842** |
| C3c tail h > $200 (RT actual 181) | **74** | **66** |

Gates: G-CAP/G-SPUR (banded 11→11; lidless S_nolid 11, S_top 0)/G-SHED/
G-BAT/G-D2 all PASS; **G-SHORTFALL FAIL** — the class families engage
their VOLL steps in NEW hours (coal_held 21, gas_st_held 13, gas_cc_held
4; Amendment 1's manufactured-shortage signature). Summer block: Δprice at
the miss set p50 **−$1.28**; caught 67→62; window concentration 0.985 (the
movement is in-episode, downward); calm fortnight 15.44 → 15.01 %.

**The mechanism story, in three measured facts:**
1. The conserving credit RELIEVES exactly the families doing the keeper's
   scarcity work: the system withheld families' requirements fall (ECRS
   742→559, RRS 1,263→1,053, RegUp 241→158 MW mean) and their VOLL-dual
   engagement HALVES (21 → 12 hours each). Those 21 engagement hours were
   the keeper's deep-scarcity pricing at its caught tail hours.
2. The class families engage VOLL in new hours instead (the classes are
   fully dispatched at the tightest hours, so a rigid class-hold cannot be
   met there without the ORDC step) — engagement MOVED between families
   and summed LOWER: mean price −$3.8/MWh, tail −8 h.
3. **The armed adaptive conduct mechanism starves to zero: 7 → 0 spike
   days.** The carve smooths the model's own settle path below the $1,000
   event threshold, so `ercot_storage_adaptive_expectation` — the depth
   mechanism this program meant to FEED — expresses nothing on the arm.

The ercot-217 §5 slack-dual reading is thereby SHARPENED, not merely
confirmed: re-allocating the measured holds onto the real holding classes
does not tighten the energy stack the way the wedge hypothesis wanted —
it substitutes class-located engagement for the system-family engagement
the co-opt already priced, at a net LOWER scarcity expression. The
2.7 GW wedge is not a mis-located AS carve.

## 4. PROGRAM DISPOSITION — the precommit §5.8 else-branch

**No factor cleared the adoption criteria** (F1/F1b/F3/F4 REFUTED-P0 on
the data; F2 REJECTED-AS-ARMED on the solve), so per the precommit there
is **NO combined run, NO 3-year bundle, NO registration and NO
promotion**. The keeper stays `2026-08-20-ercot223-arm-eventrelease`,
untouched. `ercot_as_held_location` remains built, default-off,
registered and tested — an adjudicated R cell, not an armed mechanism.

**What the program establishes** (the owner's conservatism-depth question,
answered by measurement): the 2023 operator-conservatism object is
carried COMPLETELY on the quantity side — the level is the plan (F1 ≡ 0
against it), the design is rigid-at-VOLL (F5), and the location carve —
the last admissible quantity-side object — moves prices DOWN and
manufactures shortage where it binds (F2). The 2023 residual is the
CONDUCT/OFFER object, exactly as the Door-D adjudication held — now with
the quantity-side alternatives measured dead rather than presumed dead,
which is what W-1's set-aside bought: the lane's governance posture is
re-derived as a measurement result.

**Infrastructure findings** (recorded for successors): (a) the armed LP
(+3 reserve classes, ~+10M nnz) OOM-killed twice at the ~13.9 GB memcg
ceiling the control fits under; a 6G swapfile (cgroup swap uncapped)
carried it — future ERCOT mechanisms that grow the LP should budget for
this, and boxes ship with zero swap. (b) Three construction-seam defects
were caught by the real solve that hermetic design tests cannot see: a
__post_init__ cross-field guard fires on the calibration channels' staged
config construction (guards on kwargs-channel flags belong at design
time); `np.inf` sentinel rows break shared int()-logging (use the
standing 1e9 `_RESERVE_SUPPLY_CAP_UNCAPPED_MW`); a new dispatch kwarg
must be threaded through FOUR seams (design → kwargs builder →
`solve_dispatch` wrapper → `DispatchModel` → rows). (c) The fleet's coal
plant_group token is `COAL`; the sidecar's `COAL_LIGNITE/COAL_PRB` is
reporting vocabulary.

## 5. THE 2022 DUAL-CONFIG STANDING PROTOCOL (recorded, NOT executed)

When the 2022 validation touchpoint is authorized (ERCOT holds no
`complete` marker today; 2022 stays untouched), 2022 is scored under BOTH
the 2023 regime config and the 2024–2025 keeper config; whichever clears
calibration becomes the config for the remaining holdout years, while 2023
itself remains tested single-year under its own regime config. ECRS-keyed
factors are naturally zero in 2022 (no ECRS before 2023-06-10), so the
comparison isolates the non-ECRS conservatism factors — the RRS/RegUp
held-location leg, whose 2022 driver would come from a 2022 NP3-965 intake.

## 6. Session hygiene

Probes NOT dashboard-registered (owner waiver W-2); their record is the
committed JSONs + this table. Matrix stamps centralized in the hub
(recorded deviation from rule 28(b) same-session-stamps under the owner's
parallelization instruction — every spoke verdict stamped by the hub
same-day from the committed spoke JSON). Mid-program, PR #4186 merged this
branch into main and auto-deleted it (the owner's merge cadence); the
branch was recreated from the new tip with the unmerged work rebased on,
per the merged-branch protocol.
