# FINDING — ercot-242 (2026-08-30): the room-axis extension of the armed RT wall is REJECTED-AS-ARMED — K-SPUR fires (74 → 75 lidless, churn 12 new / 11 dissolved), the officials collapse out of PASS on the overshoot side (C3a −7.3 % → +7.6 %, C3b 0.102 → 0.256, ≥$1,000 tail 59 → 71 vs 61), and the declared reach is NOT achieved (2 of 12 object hours cross $200, to $200/$238 vs actual ~$540; one new missed hour minted) — the §1.5 double-counting risk REALIZED, and the structural adjudication reads AGAINST the mechanism

**Session ercot-242, branch `claude/ercot-242-sced-phase1-sb3zj7`.** Executes
Phase-1 of the SCED room-conduct lane under
`docs/PRECOMMIT-ercot242-room-axis-phase1-2026-08-30.md` (pushed +
blob-verified 4a26a261 BEFORE any derive or solve; **no amendments** — every
declared construction ran as written; the only deviations were two
environment-dependency installs, `openpyxl` and `tzdata`, both hit before any
solve started). ONE armed 2023-only solve on the k33 carve-out
(`replay_keeper` on `ercot236_k33_clip`, single delta
`ercot_offer_surface_cleared_share_rt_room=true`; keeper-recorded env highspy
1.15.1 / pandas 3.0.5 / pyarrow 25.0.1 verified before solving). Control =
the committed keeper bundle, V-0k validated zero-solve
(`ercot226_official_score.py --validate-keeper`: −7.3 % / 0.102 / 180
reproduced exactly — no drift; the contingency replay was never needed).
Registered `2026-08-30-run242-room-axis` (REJECTED PROBE) per rule 15; A/B
record `results/calibration/ercot242_room_ab.json`; the two-config keeper is
UNTOUCHED.

## 0. Verdict in five lines

1. **The artifact built exactly as declared:** the room-binned derive's
   ungrouped parent ladders reproduce the frozen stepped artifact
   BYTE-EXACTLY for both classes (the §1.2 corpus-integrity anchor passed on
   the first run); 55 of 64 (class × nl-bin × room-bin) cells measured per
   class, per-cell `tail_support` tails, embedded measured hourly room-bin
   index (8,760 hours, zero NaN — every 2023 hour carries a measured room
   bin). Zero fitted scalars held (K-DOF never approached).
2. **Mechanical verdict: REJECTED-AS-ARMED on K-SPUR** — lidless spur 74 →
   75 against the no-increase bar. The honest decomposition is CHURN: 12 new
   spur hours (mid-band hours lifted from ~$75–150 to ~$170–226 at
   loose-to-mid measured room) against 11 dissolved (old spur hours pulled
   DOWN by loose-room cells below the year-level ladder — the
   replace-even-downward semantics working as declared). Banded spur is flat
   at 68/68. Every other kill is clean: zero new shed, off-season intact
   (all 8 off-season months inside the +$5 bar), coal +0.324 TWh (< 0.5),
   CT_PEAKER +0.41 / ST_GAS +0.92 TWh (< 1.0).
3. **The officials collapse out of PASS, on the OVERSHOOT side:** C3a
   −7.3 % → **+7.6 %** (model annual lw $59.60 → $69.18 vs actual $64.32 —
   the first ERCOT config in this lineage to overshoot the year), C3b 0.102
   → **0.256** (band ≤ 0.20 FAILED), C3c 180 → 190 h (actual 181; the tail
   now overshoots), ≥$1,000 count 59 → 71 vs actual 61 (12 new deep-tail
   hours, none lost), August lw $221.18 → $265.42 vs actual $220.16
   (+$45 over a previously-exact month), 2 clip-saturated hours (control 0).
4. **The declared reach is NOT achieved.** Of the 12-hour object family
   (actuals $537–2,014): h5484 $166.75 → $200.37 and h5777 $91.50 → $238.07
   cross the $200 census line (still $300+ short of their actual band);
   every other object hour moves +$2–37 and stays < $130. One NEW missed
   hour is minted (h5344: control $200.4 → armed $195.7 vs actual $1,517 —
   a marginal downward crossing at an extreme hour, by a loose-room cell).
   Net family 14 → 13. h2058 unmoved as predicted (out of CC/CT scope).
5. **The §1.5 double-counting risk is REALIZED, and it is the adjudication:**
   where the model already prices at the wall (August, the ≥$1,000 tail),
   conditioning the ladder on measured tight room STACKS the position effect
   the LP's endogenous dispatch already produces — prices inflate past
   actuals. Where the family's misses live (storage-carried shoulder hours,
   Phase-0 M-1), the CC/CT econ rows are not the marginal supply, so the
   room-conditioned wall cannot carry them — exactly what M-1's composition
   census said. The gate miss is the verdict, unrewritten.

## 1. Gates and constructions (all as declared)

* **Derive:** `derive_ercot_sced_offer_wall.py --room-binned --years 2023` —
  parent-identity assert PASS on both classes (no corpus drift; the frozen
  artifact untouched); artifact committed
  (`data/raw/_validation-source/ercot_sced_offer_wall_roombinned.json`,
  blob 333190e3).
* **V-0k PASS** (zero-solve): the committed control reproduces its
  registered officials to the digit; the ercot-239 r2 same-day replay is the
  freshness basis; no drift evidence arose at any point, so the declared
  contingency control replay was never run — the round stayed at ONE solve.
* **Seam guards exercised in tests** (21 passing): room-without-rt /
  room-without-wall / vintage-tag / parent-drift hard errors; NaN-room and
  unmeasured-cell hours byte-identical; year-scoping byte-identical;
  sub-p90 tail invariant.
* **Legitimacy diagnostics** regenerated on the armed bundle: **D-4 FAIL
  rows inherited-identical** — the same 22 (mechanism, class, year) rows as
  the keeper's own committed artifact, none new; D-9 overlay quarantine
  PASS; D-10 free-class PASS.
* **Registration:** `2026-08-30-run242-room-axis`, sidecar marked REJECTED
  PROBE — escalated; determination line reads NOT-YET (governance
  UNATTESTED — no attestation is written for a rejected probe; the scored
  regressions above are the substance). Retention auto-pruned
  `2026-08-16-ercot213-arm-pubanchor` (oldest beyond top-15, superseded
  ex-keeper). Parity check OK.

## 2. The A/B table (control = committed k33 keeper; full record in ercot242_room_ab.json)

| measure | control | armed | actual |
|---|---|---|---|
| C3a annual lw | $59.60 (−7.3 %) | $69.18 (**+7.6 %**) | $64.32 |
| C3b monthly NRMSE | 0.102 | **0.256** | ≤ 0.20 band |
| C3c tail hours | 180 | 190 | 181 |
| bands 200–500 / 500–1000 / ≥1000 | 103 / 18 / 59 | 102 / 17 / **71** | 77 / 43 / 61 |
| lidless spur (K-SPUR) | 74 | **75** (12 new / 11 gone) | — |
| banded spur | 68 | 68 | — |
| August lw | $221.18 | **$265.42** | $220.16 |
| new shed hours (K-SHED) | — | 0 | — |
| coal rise (K-COAL148) | — | +0.324 TWh | ≤ 0.5 |
| CT / ST_GAS Δ (K-CTST) | — | +0.411 / +0.918 TWh | ≤ 1.0 |
| missed-event family | 14 | 13 (−5484, −5777, **+5344**) | — |

Object-hour reach (the declared grading, report-only): armed − control =
+$34 (5484), +$147 (5777), +$37 (5369), +$24 (2058), +$17 (4626), +$13
(5943), +$8 (4623), +$6 (2971, 4578, 7001), +$5 (7480), +$2 (5945) — every
hour still $300–1,830 below its actual. The two "repaired" hours exit the
family by crossing an administrative $200 line, not by reaching the event
band.

## 3. The structural adjudication ([R-STRUCT], the owner's standing note applied honestly)

The owner's standing note says a gate regression on a structurally-correct
mechanism is not by itself disqualifying. **This session's read is that the
structure case runs AGAINST the room axis, so no such defense is entered:**

* Phase-0's own composition-free measure (M-3) established that resources do
  NOT reprice with room (paired Δ +$0.20/+$0.52). The measured tight-room
  surface elevation is position/participation — Base Points riding deep into
  unchanged curves. In the LP, position is ENDOGENOUS: as load and room
  tighten, dispatch rides up the SAME ladder and the marginal price walks the
  tail without any room conditioning. Feeding the measured tail STATE back
  in as a room-conditioned offer therefore prices the position effect twice.
  The solve confirms it in both directions: the already-at-the-wall hours
  overshoot (August +$45, tail 59 → 71), and the loose-room cells pull
  mid-band hours below the year-ladder read (the 11 dissolved spur hours and
  h5344's downward crossing — the LP was using headroom the room cell says
  was priced higher/lower than the year pool at those states).
* The object family stays unreached because its clearing is not on the CC/CT
  spare at all (M-1: storage-carried in the July/Sep core; the shoulder
  hours' gas mass is real but the model's econ rows there sit below the
  cleared-share boundary this mechanism conditions).
* Conclusion: **the room-conditioned offer surface is the WRONG structural
  home for the measured room dependence** — the dependence is an emergent
  property of dispatch position that the LP already carries, not an offer
  property. This is a measurement result, not a fit judgment: the mechanism
  is refuted as armed (`R`), not shelved as "correct structure, regressed
  gates".

## 4. Disposition and queue

* **Outcome rule 1 executed:** run registered (REJECTED PROBE), ERCOT matrix
  cell `ercot_offer_surface_cleared_share_rt_room` stamped **R** with this
  citation, calibration-log entry ercot-242, keeper and `config_partition`
  untouched. **ESCALATED to the owner** with §2–§3 side by side per the
  standing note; the session's recommendation is NO promotion and the cell
  verdict R as recorded — a fit gain was never on offer, and the structure
  case is negative.
* **The lane's honest residue:** the 11-hour conduct core remains the
  standing 2023 carve-out blemish-free-config's missed-event family, now
  with THREE adjudicated negatives on its offer-surface side (graded ladder
  R, room axis R, and the ercot-161/217 closures). The Phase-0 record stands
  unchanged: the dependence is position/participation-carried. Any further
  repair direction for these hours points at the POPULATIONS that carry
  their λ-band (storage conduct — Door A/D CLOSED; participation/commitment
  state), not at CC/CT offer re-pricing.
* **Forward span (§6 of the precommit):** unchanged — its own per-regime
  zero-solve identification round, its own corpus intake (owner-visible),
  and after this result the forward charter should weigh that the 2023
  room-axis arm was refuted before proposing the same form on 2024/2025.
* **Mechanism disposal:** the ScenarioConfig field stays registered,
  default-off, byte-identical off (the rule-26 deletion question — remove
  vs keep the refuted gate — is the owner's, noted in the escalation; the
  artifact and derive mode remain as the measured record either way).

## 5. Hygiene

Years ⊂ {2023}; no `--holdout-authorized`; freeze respected; ERCOT surfaces
only (rule 25); ONE armed solve (the precommit's license), zero control
solves; frozen artifacts untouched; zero fitted scalars; matrix row + cells
landed with the field (rule 28(c)), cell stamped in-session (28(b));
deliverables pushed in the precommit's §4 order with blob verification on
every ≥300-line file; no workflows, no CI solves; capx-* untouched.
