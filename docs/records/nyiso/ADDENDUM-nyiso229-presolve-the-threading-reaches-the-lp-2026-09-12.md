# ADDENDUM 2 to PRECOMMIT-nyiso229 — the threading REACHES the LP, verified at ZERO LP before the arm returned

**Session:** nyiso-229 · **Date:** 2026-09-12 · **ZERO LP.** Written while the screen shard was still
solving and **before** any arm number existed, so it cannot be shaped to a result.

This adds **no gate and changes no gate**. It closes the one failure mode that would have made the
screen uninterpretable: an arm that silently solves as the control.

---

## 1. THE RISK, named

`PRECOMMIT-nyiso229` §7 says a surviving VOLL hour "means the restored capacity is not reaching the
LP — a threading defect in this session's own change, not a fact about the market." That is the right
thing to have written, but it puts the diagnosis *after* the solve. Two failure modes could have
produced a silent no-op, and both are cheaper to exclude than to diagnose:

1. **`replay_keeper --set` might not inject a key ABSENT from the bundle's `meta.json`.** The control
   basis `nyiso_fuelvintage_H2` predates the field, so the key is not in its snapshot.
2. **The config → loader threading might not reach the availability arrays**, in which case the arm's
   `run_config.json` would read `true` while the LP solved the day-grain extract.

## 2. BOTH ARE EXCLUDED

**(1) `--set` cannot silently no-op.** `replay_keeper.py` routes each override by membership in
`solve_and_persist`'s signature **and** in `ScenarioConfig`'s dataclass fields, and **raises
`SystemExit` if a key is in neither** (*"neither a solve_and_persist kwarg nor a ScenarioConfig field
— nothing would consume it"*). `unit_outage_window_hour_grain` is in **both** after this session's
change, so it routes twice to the same value — as an explicit kwarg and through `prb_overrides` — and
an unroutable key is a hard stop rather than a dropped flag.

**(2) The threading reaches the availability arrays.** `unit_outage_derate_factors` called both ways
on 2022, on the real NYISO fleet, with the keeper's own flags
(`per_unit_crosswalk`, `merit_order_guard`, `extract_basis_share`):

| | |
|---|---|
| `(plant, group)` keys whose hourly availability MOVED | **42 of 44** |
| total restored availability | **5,797.8 multiplier-hours** |
| largest single key | `(54076, CC_CHP)` **+374.0** multiplier-hours |
| summed multiplier restored at hours **3616 / 3617** | **11.7837** |
| **monotonicity** | **the hour grain never REMOVED availability at any key-hour** — asserted in the check, passed |

The monotonicity assertion is the load-bearing one: it is the loader-level counterpart of the
deriver's own subset invariant, so the repair is proven to only ever *restore* availability at both
layers — the artifact and the consumer.

## 3. WHAT THIS DOES AND DOES NOT LICENCE

It licenses exactly one inference: **if the arm's 2022 VOLL hours do not clear, that is not a
threading defect.** The restored capacity demonstrably reaches the LP's availability arrays, at the
two hours in question, in the right direction.

It licenses **nothing about the dispatch**. Availability is an upper bound; the LP decides what runs.
G-MAG remains the test, and phase 0's 15.5–29.3× margin remains the reason to expect it to clear
rather than a claim that it will.

It is **not** a gate and **not** evidence for promotion. A screen may kill an arm; it may never
promote one (rule 29 `[R-SCREEN]`).

## 4. RULES

21 `[R-DOF]` — no parameter enters; this is a verification, not a knob. 29 `[R-SCREEN]` — clause (0),
zero-LP work done before spending a solve, and no gate was added, removed or re-cut. 32 `[R-SHARD]` —
the parent ran no LP: `unit_outage_derate_factors` is a loader, not a solve.
