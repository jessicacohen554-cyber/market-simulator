# ADDENDUM to PRECOMMIT-spp-58 — two defects of MINE, both found before any arm existed

**Session:** ercot-266 (SPP lane). **Date:** 2026-09-10. **Written BEFORE the arm is
re-solved**, and both items below were surfaced by the screen shard's report and by the
CONTROL's own numbers — **no arm result exists, so nothing here is a gate re-cut in the
light of the result it would decide.** That is the whole reason this is being written now
rather than in the RESULT.

Amends `docs/handoffs/PRECOMMIT-spp-58-wind-curtailment-ceiling-2026-09-10.md`.

---

## 1. THE SCREEN SHARD DID NOT SOLVE THE ARM. IT SOLVED THE CONTROL, AND IT CAUGHT ME.

The first screen shard (pinned `f5389aa2cd646c32781761f7b9bde34bc62940ea`) stopped at its
**HARD STOP 2** and produced no bundle. The cause was a plumbing bug in **my** commit:
`scripts/run_calibration_full.py` **parsed** `--spp-curtailment-ceiling` and
`--spp-curtail-depth-wind` and then **never read `args.spp_curtailment_ceiling` into either
`solve_and_persist` call site**. Both flags were accepted silently and dropped, so the
invocation reduced to the keeper recipe — i.e. **the control**.

**The shard's proof is the part worth carrying forward, because it did not rely on reading
my code.** Its evidence was the solve's own log line 46:

> `SPP wind 2024 oversupply curtailment allocation: 11675.9 GWh over 3173 hour(s) …`

The rule 19 `[R-ONE-MECH]` supersession in `data/renewables.py` **skips**
`_oversupply_uncurtailed_cf` whenever the ceiling is armed. The allocation fired, therefore
`config.spp_curtailment_ceiling` was **False inside the solve** — an empirical fact
independent of any source reading. It then killed the process at ~6 minutes rather than
spend ~25 more producing a control solve that PRECOMMIT §6/§7 and rule 29(b) say must not
be spent, and refused to patch `scripts/` itself because a shard that repairs
infrastructure is a failure. That is exactly right on all three counts.

### Why this failure mode is dangerous, stated plainly

There is **no error, no warning, and a bundle that looks like a solved arm.** Had the shard
not been told to grep the log for a message the mechanism must emit, this would have come
back as a clean, complete, **null-effect** arm — 0.000 TWh moved — and the honest reading
of that would have been *"the mechanism is inert; the cell goes `I`"*. A verdict would have
been minted about a mechanism that never ran. The `U` cell stays `U`: **this shard tested
the CLI, not the mechanism.**

### The repair, and it is verified two-sided at zero LP

The missing hop is added at both call sites, mirroring the adjacent
`vre_curtailment_oversupply_allocation` line. Verified by intercepting
`solve_and_persist` — the seam the CLI actually calls — and reading what arrives:

| build | `spp_curtailment_ceiling` | `spp_curtail_depth_wind` |
|---|---|---|
| before the fix | **`<<< NOT DELIVERED >>>`** | **`<<< NOT DELIVERED >>>`** |
| after the fix | `True` | `None` → dataclass default `0.288137` |

**Guarded against recurrence**: `tests/unit/data/test_spp_curtailment_ceiling.py::
test_cli_flags_reach_the_solve_seam` intercepts that same seam and asserts delivery. It is
confirmed to FAIL against the un-fixed file and PASS against the fixed one — a guard that
has never been shown to fail is not a guard.

### Routed, not absorbed: the general case

The shard asked for a guard covering *every* parsed-but-undelivered flag. A crude static
sweep (does `<dest>=args.<dest>` appear anywhere in the file?) reports **31 of 244**
ScenarioConfig-named flags without that literal — but most are certainly delivered by other
routes (`iso`, `hours`, and `ercot_ep_gas_basis_receipts_fallback`, which demonstrably
worked in the ercot-265 keeper, are all in that 31). Separating a real silent drop from a
different delivery pattern needs the **runtime** probe above run across all 244, which is
its own lane. **Measured and named here; not fixed here**, and the number is stated so
whoever takes it knows the size of what they are opening.

## 2. MY GATE G-4 WAS UNSATISFIABLE AS WRITTEN — BY THE CONTROL

PRECOMMIT §5 **G-4** reads: *"slack and dump stay exactly 0.0."* The shard recomputed the
control from the keeper's committed bundle and found:

| 2024, keeper `2026-09-09-spp-52a-fossil-offer` | value |
|---|---:|
| `slack_MWh` | **177.596** |
| `dump_MWh` | 0.000 |

**The incumbent already carries 177.596 MWh of slack, so G-4 as written fails the control.**
A gate no run can pass — the arm, the control, or any other — discriminates nothing. This
is my error: I carried the clause forward from the predecessor PRECOMMIT without measuring
the incumbent's own baseline in phase 0, which is precisely what phase 0 is for.

**G-4 is re-cut to the strictest form that is satisfiable** (the miso-245 precedent — repair
to the strictest satisfiable form, never to whatever the arm happens to do):

> **G-4 (no new forcing), re-cut.** `dump_MWh` stays exactly **0.000**, unchanged from the
> control. `slack_MWh` does not exceed **2× the control's 177.596 MWh** (i.e. ≤ 355.19 MWh)
> — displaced wind must be picked up by economic dispatch, not by unserved energy. And no
> `min_gen` floor gains binding hours. A slack rise beyond that bound means the ceiling is
> removing energy the fleet cannot replace, which kills the arm.

The 2× bound is set **now, before any arm number exists**, and is deliberately loose on the
side of *not* killing the arm for a rounding-scale move on a quantity that is 0.0006 % of
SPP's annual load — while still failing any rise that is materially unserved energy. Every
other gate (G-1, G-2, G-3, G-5) and every sealed prediction (P1–P4) is **UNCHANGED**.

## 3. Control numbers, now independently reproduced

The shard recomputed the three control values it was handed, from the committed keeper
bundle at the pinned SHA, and **all three reproduce**:

| quantity, SPP 2024 | handed | shard's own recomputation |
|---|---:|---:|
| wind dispatch | 120.7227 TWh | **120.722687** |
| wind bound | 120.9925 TWh | **120.992461** |
| re-curtailment | 0.223 % | **0.222968 %** |

Corroborated a third way: the killed run's own log printed `annual potential 120.992 TWh`
on the identical recipe at HEAD. The control's full 2024 class table is in the shard's
`METRICS-spp58-2024.json` on `main`.

Separately, the parent re-scored the keeper at HEAD (PRECOMMIT §7) and **every criterion
status is identical to its committed `metrics.json`** — the `_validation-source` bench move
recorded in the G-DRIFT table does not reach SPP, so G-CTRL form 4 holds cleanly.

## 4. What changes about the lane

Nothing structural. No cell verdict is minted, the screen year stays 2024, the mechanism,
its share table and its depth are untouched, and the arm is relaunched verbatim against the
new SHA. The only cost is one shard's wall-clock, which the shard's early kill kept to
~6 minutes instead of ~30.
