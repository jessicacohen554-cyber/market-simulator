# PRECOMMIT — ercot-215 (G-SPUR lane Phase-1, owner-answered fork): the ercot-214 counterpart decontamination (`ercot_ordc_adder_family_counterpart`), armed A/B on the keeper recipe, with promotion OWNER-INSTRUCTED IN ADVANCE over the known G-C3c kill

**Session ercot-215, 2026-08-17, branch
`claude/ercot-215-ordc-decontamination-xsbhwn`. PUSHED BEFORE ANY SOLVE.**
Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json`:
**`2026-08-16-ercot213-arm-pubanchor`**, determination NOT-YET, fail set
{C3b-2023} ALONE, C3c-2025 the single ledgered CAVEAT.

This is Phase-1 of the fork `docs/FINDING-ercot214-gspur-phase0-2026-08-17.md`
§5 escalated to the owner, entered on the owner's answer (below). The lever is
the ONE lever ercot-214 identified (§3), unchanged; its full-span consequences
are already EXACTLY measured pre-solve
(`results/calibration/ercot214_gspur_phase0.json`), because the delta is
post-solve additive and moves no MW.

## §0 THE OWNER AUTHORIZATION, GIVEN IN ADVANCE — recorded verbatim so the promotion is honest ex ante

At the ercot-214 session close (2026-08-17) the owner asked: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper."* The ercot-214
recommendation was YES on the structural standard. **Promotion of the armed
member is therefore OWNER-INSTRUCTED over the known gate regression** — the
ercot-188/213 pattern: the direction-blind mechanical verdict is recorded
UNREWRITTEN (expected **REJECTED-AS-ARMED on G-C3c**, known ex ante from the
counterfactual, §3 below), and the promotion executes on the owner's standing
structural standard on top of it. **Both records stand.** Nothing in §4's
mechanical rule is weakened by this: the kill is pre-registered, will be
reported as a kill, and the promotion note will carry it unrewritten, exactly
as the ercot-213 promotion carried its G-SPUR kill.

## §1 The delta — the keeper recipe + ONE boolean, zero fitted scalars

**`ercot_ordc_adder_family_counterpart=true`** (NEW, default **False** —
keeper-reproducing). Inside the already-armed published-anchor branch of
`run_calibration_full._system_frame`, and nowhere else: write the ORDC
component of the all-tier cap dual instead of the contaminated sum,

```
gamma'(t) = min( gamma_all(t), gamma_ordc_family(t) )
adder(t)  = min( gamma'(t) * (VOLL - lambda(t)) / VOLL , VOLL - lambda(t) )
```

where `gamma_all` is the all-tier reserve-supply-cap row dual (the ercot-213
single counterpart, unchanged) and `gamma_ordc_family` is the
`ercot_ordc_total` family's own balance-row dual —
`result.reserve_price_by_family[:, -1]`, the same per-hour series every keeper
bundle already persists to the `reserve_family` sidecar, threaded to the
writer in-memory. **Anchor, single-counterpart form, protocol cap and netting
UNTOUCHED.** The min form (not `gamma_fam` verbatim) keeps the
protocol-capped hours exact: where the written adder saturates at
`VOLL - lambda` both operands sit at or above the cap and the min changes
nothing (pinned as a test).

**Identification source (rules 1/5/13/23), no scalar anywhere:**

* **The 2023-25 market-design fact** (`model/reserves/spec.py`, the
  `ercot_ordc_only_scarcity` citation block, spec.py:1420 at ercot-214's
  reading): ERCOT 2023-25 has NO real-time per-product scarcity pricing — RT
  reserve scarcity prices via the ORDC on REALIZED TOTAL online reserves; a
  product-vs-capability squeeze triggers RUC commitment, not a price. The
  AS-product shortfall-ramp step (`VOLL / ercot_as_n_ramp` = $416.67) is
  model scaffolding for the DAM award's physical withholding; its export into
  the RT energy price manufactures a channel the design cannot emit.
* **The measured decomposition** (ercot-214 §0-§2): in **808/808**
  adder-writing hours across 2023-25,
  `gamma_all = k x (VOLL/12) + gamma_ordc_family` with integer k, and the
  family's own dual matches published settled RTORPA in BOTH regimes
  (rank-corr 0.709/0.807/0.758, better than the contaminated sum in every
  year; the 9 spill hours are k=1 with family at cents while published RTORPA
  read $0.11-$1.32).

The flag is a boolean `solve_and_persist` kwarg recorded in `meta.json` with a
matching `--ercot-ordc-adder-family-counterpart` CLI flag, exactly like its
sibling `ercot_ordc_adder_published_anchor` — registered as the **THIRD LEG**
on the `ercot_multiproduct_as` matrix row (the nyiso-121 census convention).
Reachable only inside `iso == "ERCOT"` + `ercot_reserve_supply_cap` + the ORDC
regime + `ercot_ordc_cap_dual_adder` + **the armed
`ercot_ordc_adder_published_anchor` branch**; armed alone it is provably inert
(tests `test_flag_is_inert_without_the_published_anchor_branch`,
`test_flag_is_inert_without_the_cap_dual_branch` — the ercot-213 pattern).
`reserve_price_by_family=None` under the armed flag is a loud `ValueError`,
never a silent fallback to the contaminated sum (rule 5). The ramp's IN-LP
role — physical withholding of the DAM AS plans — is untouched; only its
export into the written price stops.

## §2 The expected landing, stated ex ante — and here it is EXACT, not a band

Because the delta is post-solve (it moves no MW), the ercot-214 counterfactual
(`ercot214_gspur_phase0.json` `counterfactual_repoint`) IS the armed member's
scorecard, by construction rather than by prediction:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| G-SPUR (keeper → armed) | 17 → **9** = the control set exactly | 13 → **11** = the control set exactly | 0 → **1** (h3355, energy-made, un-masked) |
| tail > $200 (actual 181/53/31) | 123 → **67** | 33 → **22** | 3 → **1** |
| adder h > $100 (published 17/4/0) | 117 → **37** | 16 → **3** | 3 → **0** |
| adder nonzero / > $1 | 564 / 175 | 177 / 36 | 67 / 5 |
| max adder | **$4,701.14** (the VOLL-cap hour, untouched) | $355.98 | $14.61 |
| G-CAP violations | 0 | 0 | 0 |

The 2023 mid-band restores to the energy-made baseline (the shared Aug hours),
the deep-adder incidence lands at the published order of magnitude (37 vs 17
published h > $100), and every dispatch-side quantity is unchanged BY IDENTITY.

**Pre-registered kill, known ex ante: G-C3c KILLS in all three years**
(123→67 away from 181; 33→22 away from 53; 3→1 away from 31) — the keeper's
tail is measured to ride the same phantom ramp channel (ercot-214 §2: 116/117
of 2023's deep adder hours are contaminated; published RTORPA p50 $14.2 there;
the real tail was conduct-made, adjudicated to the C3c model-class ledger at
ercot-209/211). C3a-2023 gives back ~31 pp on the probe basis
(+0.40 → −30.38 %). Under §4's mechanical rule this is REJECTED-AS-ARMED; the
promotion then executes on §0. Q-B/R-A: all 2023 movement is side-effect
reporting at full magnitude, never a basis.

## §3 Kill gates — direction-blind, inherited from ercot-213 §3 verbatim, PLUS G-EXACT

Measured on the armed member vs the control replay; ANY kill ⇒ the mechanical
verdict is **REJECTED-AS-ARMED** (recorded unrewritten; §0 then applies).

| gate | rule |
|---|---|
| **G-REPRO′** | control-vs-armed at the same HEAD on the pinned true solve env; control-vs-keeper drift reported at full magnitude alongside. (Since ercot-213 solved at `7246272` and the tree has advanced, the control may or may not byte-reproduce the keeper; its DETERMINATION must reproduce, and any byte drift is reported.) |
| **G-SHED** | shed hours must not INCREASE in any year (control basis). Expected: unchanged by identity (post-solve delta). |
| **G-C3c** | tail must not move AWAY from actual in any year. **Expected kill, pre-registered in §2.** |
| **G-SPUR** | spurious mid-band hours ≤ +5 in any year — **the object's own gate**. Expected: 17→9 / 13→11 / 0→+1, PASS in every year. |
| **G-SPAN** | max per-class annual energy delta ≤ 2.0 % of ISO load. Expected 0.0 by identity. |
| **G-COAL148** | coal-above-ceiling rise ≤ 0.5 TWh per year. Expected 0.0 by identity. |
| **G-OWNER** | C3a-2024, C3a-2025, C3b-2024 remain PASS on the armed member's own official scorecard. |
| **G-DOF** | zero new tuned scalars; ledger `n_residual` stays 6; the new flag is a boolean. |
| **G-D2** | no NEW D-4 off-window-binding FAIL row (the 3 pre-existing `reliability_floor × CT_PEAKER` h14-21 rows carry). |
| **G-CAP** | no written `ordc_adder(t)` may exceed `VOLL − λ(t)` in any hour (inherited as standing from ercot-213). Expected: 0 violations (§2). |

**One ADDED gate, unique to this object because the delta is post-solve:**

| gate | rule |
|---|---|
| **G-EXACT** | The armed member must reproduce the ercot-214 counterfactual **EXACTLY**: (a) the §2 table's spurious counts **with the listed hour sets** (2023 repointed = {5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822}; 2024 = {336-339, 345-349, 2540, 2829}; 2025 = {3355}); (b) adder incidence nonzero/>$1/>$100 = 564/175/37, 177/36/3, 67/5/0; (c) max adders $4,701.14 / $355.98 / $14.61 (to the cent); (d) G-CAP 0 violations; (e) the armed member's **non-system hourly sidecars (class_hourly / storage / reserve_family × 3 years) byte-identical to the keeper's committed bundle** (`results/calibration/ercot213_anchor_B/hourly/`) — the dispatch is untouched by construction, so ANY dispatch-side difference means either HEAD drift or a build defect. **ANY G-EXACT mismatch is a BUILD DEFECT — stop the line**: no registration, no promotion, diagnose first. (If (e) fails from measured score-inert HEAD drift while (a)-(d) hold against the CONTROL's own bytes, that is reported and escalated in the finding before any promotion, not absorbed.) |

**LOYO:** parameter-free rule (no fitted value exists to identify) —
structurally N/A, per-year deltas reported in its place (ercot-173/188/213
precedent).

## §4 Decision rule (direction-blind), and what §0 adds on top

The mechanical rule reads ONLY the §3 gates: any kill ⇒ REJECTED-AS-ARMED,
recorded unrewritten. **G-C3c is expected to kill (§2), so the expected
mechanical verdict is REJECTED-AS-ARMED — pre-registered here.** On top of
that verdict, per §0, the promotion executes on the owner's standing
structural standard (the ercot-188/213 pattern; both records stand). G-EXACT
is NOT part of this fork: a G-EXACT failure is a build defect that stops the
line before any verdict or promotion.

**Expected post-promotion official scorecard, stated so nobody is surprised**
(from the counterfactual + the ercot-213 control/arm scorecards): the official
scorer (`scripts/calibration_verdict.py`, committed artifacts only) will
**re-fail C3a-2023 and C3b-2023** and re-fail the C3c bands in all three
years, which **re-ledger** as the C3c model-class caveat
(ACCEPTED MODEL-CLASS LIMITATION ×3, magnitudes 67/181, 22/53, 1/31 at full
magnitude) per the attestation this session generates; the lone-C3c standing
rule stays SILENT because other criteria fail. **Determination NOT-YET with a
wider fail set than the current keeper's {C3b-2023}** — expected
{C3a-2023, C3b-2023} — accepted by the §0 owner instruction as the price of
removing a phantom price-formation channel. G-SHED keeps 0/1/0 (the netting's
volume effects are untouched). This scorecard is the honest cost, named
before the solve.

## §5 Roster effects, named ex ante

ERCOT's registry holds three runs (keeper `2026-08-16-ercot213-arm-pubanchor`,
its control `2026-08-16-ercot213-ctl-headbase`, superseded
`2026-08-15-ercot204-rule26-delete`). Both ercot-215 members register with
payloads → 5 runs, no eviction (top-15 honoured). Intended ids:
**`2026-08-17-ercot215-ctl-headbase`** / **`2026-08-17-ercot215-arm-decontam`**
(bundles `results/calibration/ercot215_control_A` /
`ercot215_decontam_B`). On promotion the ercot-213 arm becomes the
immediate-prior keeper and is RETAINED (the ercot-204→213 precedent); whether
the deeper roster (`-ctl-headbase`, `ercot204-rule26-delete`) stays is flagged
for the owner in the finding, not decided quietly.

## §6 Execution

* **Solve environment PINNED BEFORE THE CONTROL** to the keeper's TRUE solve
  env — python 3.11.15, **highspy 1.15.1 / numpy 2.4.6 / scipy 1.17.1 /
  pandas 3.0.5 / pyarrow 25.0.1 / pydantic 2.13.4** (the keeper bundle's
  `meta.environment`) — in a venv **OUTSIDE the project directory**
  (`/root/ercot215-venv`): the repo's own `.claude/hooks/ruff-autofix.sh`
  PostToolUse hook runs `uv run ruff`, and `uv run` re-syncs
  `$CLAUDE_PROJECT_DIR/.venv` to `uv.lock` first, so `.venv` cannot hold a
  pin (the ercot-213 §3 standing note; ercot-204 §B.2 trap).
* `data/clean/gtc-limits` regenerated from `data/raw` before any replay (the
  keeper arms `ercot_gtc_limits_measured`; the partition is gitignored).
* Control: `scripts/replay_keeper.py results/calibration/ercot213_anchor_B
  --out-dir results/calibration/ercot215_control_A` — full span
  `2023 2024 2025` in ONE invocation, years sequential (rule 12).
* Armed: same + `--set ercot_ordc_adder_family_counterpart=true`,
  `--out-dir results/calibration/ercot215_decontam_B`.
* The two invocations run **sequentially, not concurrently** (RAM: ~12.7 GB
  peak RSS per member on this keeper's LP, ercot-188 G-COST).
* Both runs register on the BACKCAST registry with payloads (rules 15/16; run
  payloads over `git push`, HTTP/1.1 fallback on a hung push). **PROMOTE** per
  §0: `frontend/data/backcast/keepers/ERCOT.json` → the armed id,
  `build_status.py --iso ERCOT`, the `calibration-keeper-auditor` agent
  (`--iso ERCOT`). ERCOT holds no `complete`/`final` marker, so no
  `calibration-complete.json` re-key (rule 22 / D-5(b)). Matrix: the 28c
  third-leg registration on the `ercot_multiproduct_as` base row + the 28b
  cell verdict in `mechanism-matrix/ERCOT.js`, same landing;
  `check_mechanism_matrix.py` exit 0. Log entry under **ercot-215**
  (ercot-199 remains unclaimed).

## §7 Fences

Rule 22: {2023, 2024, 2025} only, no marker sought, no out-of-training year
solved or scored. Rule 25: ERCOT only — the flag gates on the ERCOT
multiproduct ORDC stack alone. Rule 27: edits local, exact on-disk bytes
pushed, ≥300-line pushed files blob-verified. Rules 5/24: the field is a
registered `solve_and_persist` kwarg recorded in `meta.json`; no env-var knob,
no off-registry channel. No new workflows, no cron, solves run in-session. No
PR (push-and-stop on the designated branch; the owner merges).

**Standing rulings cited, never re-litigated.** Q-B FINAL + R-A: every
C3a/C3b-2023 number here is side-effect reporting at full magnitude, never a
gate basis, never spent — the §4 mechanical rule reads only the §3 gates, and
the promotion rests on §0's owner instruction plus the measured structural
identification, not on any residual's direction. ercot-206 B0: no LOLP-table
arming. ercot-211: Door A closed, no conduct work — the 2023 tail RETURNS to
the C3c model-class ledger where ercot-209/211 put it; it is not chased here.
28a: the bare netting stays `R`; nothing here re-tests it (the netting rides
armed and untouched inside the keeper recipe). V0/ercot-201 DO-NOT-REDO: no
tightness-conditioned identification. The G-SPUR band-top blindness
(FINDING-ercot214 §5 flag) is NOT a gate change this session — noted for a
future owner gate revision only.
