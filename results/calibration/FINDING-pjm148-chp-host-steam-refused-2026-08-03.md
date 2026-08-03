# FINDING — pjm-148: the CHP host-steam holdout lane is REFUSED (no admissible identification), and the screen uncovers a path-dependence that makes every slim-scored keeper's D-2 under-report CHP and nuclear floor attribution

**Verdict: REFUSE. No LP solved, zero arms registered.** The named successor
lane from `FINDING-pjm147-measured-chp-heat-rates-2026-08-03.md` §8 has no
admissible arm: the one branch that survives the screen can only be moved by a
number sized by the residual, which rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`
forbid (the neiso-71 kill). The handoff licensed exactly this outcome — "if the
only identification available is gap-shaped, REFUSE and say so".

Pre-registration: `results/calibration/PREREG-pjm148-chp-host-steam-holdout-2026-08-03.md`,
committed at `6f14dbc` **before any measurement that decides a verdict**. (The
push of that commit failed transiently four times and landed later in-session;
the content was fixed before the first probe ran and was never edited after.)
Machine record: `results/calibration/_pjm148_screen.json`; Q1 detail
`results/calibration/_pjm148_floor_binding.json`.

Keeper `2026-08-03-pjm-147b-chp-heat` is **untouched**. Rule 25 `[R-ISO-SCOPE]`:
this lane was reached independently of nyiso-105, from PJM's own data.

---

## §0 — verdict table

| pre-registered question | result |
|---|---|
| **Q1** does the CC_CHP host-steam floor bind? | **SURVIVES — it binds, ~0.994 / 0.692 / 0.815 TWh.** *Both pre-registered limbs turned out to be invalid instruments; §4.* |
| **Q2** is CC_CHP capacity-bound (κ)? | **REFUTED.** κ = **0.0101 / 0.0404 / 0.0236** vs the ≤ 0.20 rule — and *strengthened* vs pjm-131's 0.0226 |
| **Q3** does a valid measured BTM share exist? | **DEAD on both limbs.** 35/35 rows degenerate **and zero CC_CHP coverage** |
| **Q4** is any non-gap-shaped identification available? | **NONE.** Both channels to a lower floor are closed; §5 |

**Net:** the only direction that could close the residual is a floor
*reduction*, and every route to one is either rule-23-frozen or Q3-dead. What
remains is a number chosen to fit. Refused.

## §1 — Q2: the capacity/BTM half is refuted, harder than before

pjm-131 refuted the grid-capacity pull-out on a pre-registered κ rule. This
session re-measured it on the **current** keeper (`pjm147_chp_B`), all three
years, via the same committed probe:

| year | κ | model CC_CHP | actual | mean class utilization |
|---|---|---|---|---|
| 2023 | **0.0101** | 8.606 | 6.115 | 72.3 % |
| 2024 | **0.0404** | 8.073 | 7.283 | 67.1 % |
| 2025 | **0.0236** | 6.835 | 6.445 | 60.0 % |

All three sit an order of magnitude below the 0.20 threshold. **κ in 2023 more
than halved** (0.0226 → 0.0101) because pjm-147 made CC_CHP ~7 % dearer, so the
class now clears even further from its ceiling. A capacity pull-out is absorbed;
the bench actual (which uses the identical share) falls in full; the overshoot
would **worsen**. The model/actual triple reproduces the pjm-147 finding to 3 dp,
so the reconstruction is faithful.

## §2 — Q3: the measured host share does not exist for PJM, and cannot be repaired into existence by fixing only the defect pjm-131 named

`chp-btm-share` re-curated this session for PJM (reads only `data/raw`):

* **35 rows, 35 degenerate** (`btm_share == 1.0`, `campd_net_mwh == 0`) — 100 %
  vs the ≥ 90 % DEAD rule.
* **Zero CC_CHP rows. Every one of the 35 is `ST_CHP`.** CC_CHP capacity
  coverage is **0.0 %** against the 50 % rule — so Q3 is dead on the coverage
  limb *independently* of degeneracy.

**Root cause, extended past pjm-131.** That session diagnosed limb one: the
cogen filter is `steam_load_klbh_sum > 0`, and at CEMS the steam load is metered
on a unit that carries no electricity — **1,754 of PJM's 1,755 steam-reporting
unit-years have `gross_mwh = net_mwh = 0`** — so the CAMPD term is zero by
construction. This session adds limb two, which pjm-131 did not record: the
steam-reporting units are **boilers** (dry-bottom wall-fired 655, other boiler
490, CFB 254, stoker 217, tangentially-fired 102; only 8 combustion turbines),
so `_chp_group_from_unit_type` labels **every** surviving row `ST_CHP`
(1,530 ST_CHP / 217 unmapped / 8 CT_CHP / **0 CC_CHP**).

**Consequence for any future repair:** finding the cogens' electrical channel —
the fix pjm-131 asked for — would resolve limb one and still leave **CC_CHP with
zero rows**. A repair must *also* attribute the plant's class off something
other than the steam-reporting unit's type. Until both limbs are fixed, no
measured BTM share can arm PJM's CC_CHP, and `CHP_BTM_PCT_BY_SECTOR['merchant']
= 35.0` — self-documented in the matrix as "residual-identified, no independent
source yet" — correctly stands as the only available input.

## §3 — Q1 SURVIVES: the floor binds, and the handoff's figure was right

The handoff cited "the `chp_steam` D-2 floor level (11.0/7.9/10.4 % of class
energy at PJM)". The **current keeper's** committed `legitimacy_diagnostics.json`
carries **no CC_CHP `chp_steam` row at all** — neither arm, no year — which
reads as 0.0 %. The pre-registration flagged that discrepancy (§6) and made Q1
measure bindingness directly rather than assume either number.

The handoff is **correct** and the keeper's artifact is **wrong**. The
11.0/7.9/10.4 % figure is reproduced exactly by the superseded keeper
`pjm143_hy_level_B` (0.1097 / 0.0794 / 0.1045 = **0.994 / 0.692 / 0.815 TWh**),
and the floor itself is **verified unchanged** between the two keepers —
436.4 MW mean / 485.3 MW max in 2023, identical to 1 dp. So the floor binds and
forces ~0.99 TWh; the current keeper simply fails to report it.

## §4 — both of Q1's pre-registered limbs were invalid instruments, and the reason is a real defect

Stated plainly rather than buried, because it means Q1's DEAD rule could not
legitimately have fired:

* **Limb (b), the hourly reconstruction, is insensitive.** Run against
  `pjm143_hy_level_B` — where D-2 demonstrably attributes 0.994 TWh — it reports
  **0 of 8,760 hours at the floor**, the same as on the current keeper. It
  compares the *class-aggregate* dispatch to the *summed* floor, so a unit
  sitting on its own floor is invisible whenever its neighbours run above
  theirs. It is not corroboration and is not used as any. What it *does*
  establish validly is the unchanged floor level above, and that the class runs
  at **1.94–2.29×** its aggregate floor across 2023–2025 on the current keeper
  (2.29 / 2.07 / 1.94; the superseded keeper's 2023 reads 2.42).
* **Limb (a), the committed D-2, is produced by a lossy path.**

**The defect (new, and not PJM-specific).** D-2's floor attribution is joined to
a dispatch series per plant (`scripts/legitimacy_diagnostics.py:2325-2327`; the
equivalent filter existed before caiso-155 and is not a regression from it).
That series comes from one of two sources:

1. `dispatch/<year>_<pass>.parquet` — every model plant; **not** in a committed
   bundle, and
2. the dashboard **run payload** — CAMPD-bench-keyed, **311 plants** for PJM 2023.

**Not one of PJM's 14 CC_CHP plant codes appears in the payload** (10030, 10061,
10633, 10805, 50326, 50410, 54333, 54832, 55216, 55801, 55990, 57908, 58207,
58933 — all absent). So on the payload path every CC_CHP plant is filtered out
and the class loses all D-2/D-4 attribution, silently, with no failure raised.

Proof it is the path and not the dispatch: running **current** code over
`pjm144_control_A` — the bundle whose *own committed file* records
`CC_CHP chp_steam 0.9938 TWh` — reproduces **zero CC_CHP rows**, and the log
confirms `model dispatch from run payload … (311 plants)`. Same bundle, same
dispatch, different path.

**Scope of the damage.** pjm-146 onward lost **10 D-2 rows** relative to
pjm-144: all CC_CHP attribution, `ST_CHP chp_steam`, a 2025 `COAL chp_steam`
row, and a **272 TWh `nuclear_mustrun`** row (empty class bucket) in every year.
The calibration protocol *mandates* scoring on the committed slim file set —
i.e. the lossy path — so this is expected to affect **every ISO's keeper scored
under it**, not just PJM's.

**Why this does not move any verdict, and why it still matters.** CC_CHP,
ST_CHP and nuclear are all exempt from the C8 forced-budget gate, so no
determination changes and no keeper is invalidated. But rule 18
`[R-FORCED-BUDGET]` is scored *entirely* from `legitimacy_diagnostics.json`, and
a mechanism that silently drops classes from that file is an attribution channel
nobody can see. **Not fixed here**: it is shared scoring infrastructure that six
concurrent ISO lanes depend on, the fix has to decide what dispatch a
payload-absent plant should carry, and that is its own charter — not a PJM
calibration session's to land unilaterally.

## §5 — Q4: why the surviving branch is still refused

Q1 survives, so the floor is a live lever. It fails on identification, not on
liveness:

* **Direction.** PJM CC_CHP is **over** actual in all three years, so only a
  floor **reduction** helps. Raising it — including deriving the WP-3
  `steam_level_cf` PJM's pre-WP-3 artifact lacks, which is a `max(level, p2)`
  swap — is wrong-signed by construction. Declared in the prereg §2 before
  anything was measured.
* **Channel one, `chp_pmin_cf`:** rule 23 `[R-FROZEN-DERIVE]`. It re-derives
  only when its source data changes, and the derive commit must cite that
  change. There is none.
* **Channel two, `btm_share`:** Q3-dead. No measured replacement exists, and
  §2 shows none can be produced by the repair pjm-131 scoped.
* **Anything else** is a level chosen because it closes 2.49 TWh — the neiso-71
  kill verbatim, forbidden by rules 21 / 24.
* **And the magnitude does not even reach.** Deleting the floor *entirely*
  releases at most ~0.99 TWh against a 2.49 TWh 2023 gap (40 %), and deleting a
  measured, rule-13-admissible host-steam input because it improves a fit is
  forbidden by rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]` independently.

**The structural reading.** κ = 0.010 and a floor forcing ~11 % together say
PJM's CC_CHP is neither capacity-bound nor floor-bound: ~89 % of its energy is
**voluntary economic clearing** between the two. That is a merit-order finding —
pjm-131 reached it and pjm-147 tightened it by measuring the offer. The residual
is what remains after an accurate offer, so the next move is on *what the class
competes against*, not on its own floor or holdout.

## §6 — what PJM needs next

1. **DO-NOT-REDO.** Do not re-derive a CC_CHP host-steam floor or BTM share for
   PJM against this residual, and do not arm `chp_steam_floor_p25` for PJM (its
   artifact is pre-WP-3, so the flag is inert — the NEISO position — and
   deriving the column is wrong-signed anyway).
2. **The `chp-btm-share` artifact needs a two-limb repair or retirement**, and it
   remains wired into the **forecast** path (`runner.py`), where a curated
   partition would pull every covered CHP plant 100 % behind the meter. pjm-131
   flagged this; it is still live, and §2 shows the repair is larger than
   previously scoped.
3. **The D-2 payload path-dependence (§4) deserves its own cross-ISO charter.**
4. **This lane is closed; the queue's next-best PJM cells are unchanged** —
   `hydro_ror_split` (ORNL EHA, ~1.1 % of load, needs a PJM classifier review)
   and `storage_vintage_ramp` (71/190/634 MW in-year CODs). Neither was opened
   here.

## §7 — rule compliance

* **Rule 15 `[R-DASHBOARD]`:** no solve completed ⇒ no bundle to register (the
  pjm-131 / neiso-71 precedent for a no-LP screen).
* **Rule 16 `[R-ALLYEARS]`:** no bundle produced; every measurement that has a
  year spans **2023 / 2024 / 2025**.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only. `holdout-freeze.json` untouched and
  not lifted; the `chp-btm-share` curation excludes 2022/2026 by construction.
* **Rules 1 / 19 / 20 / 21 / 23 / 24:** nothing tuned. No offer band, sigmoid,
  floor, derive output or registry value was touched, and no mechanism was
  invented. The one candidate parameter was refused *because* it would have been
  fitted.
* **Rule 27 `[R-PUSH]`:** no existing file ≥ 300 lines modified; new code is one
  probe. Nothing regenerated from response content.
* **Keeper `2026-08-03-pjm-147b-chp-heat` untouched**; no keeper shard edited, so
  no `calibration-complete.json` re-key is due (rule 22 D-5(b) triggers on
  promotion).

## §8 — reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/regenerate_clean.py \
    transfer-interface-limits ramp-capability lmp
PYTHONPATH=. .venv/bin/python scripts/data/curate_chp_btm_share.py --isos PJM
PYTHONPATH=. .venv/bin/python scripts/probes/pjm131_chp_btm_precheck.py \
    --bundle results/calibration/pjm147_chp_B --year 2023        # and 2024, 2025
PYTHONPATH=. .venv/bin/python scripts/probes/_pjm148_floor_binding.py \
    --bundle results/calibration/pjm147_chp_B --years 2023 2024 2025 \
    --json-out results/calibration/_pjm148_floor_binding.json
# the path-dependence, §4 — same bundle, zero CC_CHP rows on the payload path:
PYTHONPATH=. .venv/bin/python scripts/legitimacy_diagnostics.py \
    --bundle results/calibration/pjm144_control_A --iso PJM --years 2023 \
    --only D2 --rebuild-floors --json-out /tmp/pjm148_d2_recompute.json
```
