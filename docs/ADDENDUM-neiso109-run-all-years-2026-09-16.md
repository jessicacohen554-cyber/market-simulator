# ADDENDUM — neiso-109: the OWNER directed the full span; the screen no longer gates it

**Session** neiso-109 · **Date** 2026-09-16 · **Written BEFORE the span shard reported.**
Amends `docs/PRECOMMIT-neiso109-gas-repair-screen-2026-09-16.md` §6 (THE PLAN).

## 1. THE INSTRUCTION

**Owner, 2026-09-16, verbatim: "Run all years".**

The PRECOMMIT staged this lane as rule 29 `[R-SCREEN]`: phase 0 → a ONE-YEAR screen on 2025 → the
full span **only if the screen clears**. That staging is now **superseded by owner direction**. The
six-year span (2020–2025) was launched immediately, in parallel with the screen, rather than after
it.

**This is recorded rather than quietly executed** because it changes the lane's own pre-registered
sequencing, and a session may not relax its own gate. The owner may; the session may not.

## 2. WHAT CHANGES, AND WHAT DOES NOT

| | status |
|---|---|
| The screen's **gating** role (rule 29 (2): "the full span only if the screen clears") | **WAIVED by the owner.** |
| The screen itself | **STILL RUNNING, and still worth its LP** — see §3. |
| G-1 … G-5 as **STOP** gates | **UNCHANGED.** They still bind on the span. A gate that fires is still a STOP, and the result is still reported at full magnitude. |
| "A screen may kill an arm; it may never promote one" | **UNCHANGED.** Nothing here promotes anything. Only the owner promotes (rule 31 `[R-RETAIN]`). |
| The pre-registered expectations (PRECOMMIT §3) | **UNCHANGED and unedited.** They were pushed before any solve and are not being rewritten now that more years are in flight. |
| Rule 16 `[R-ALLYEARS]` / 32(b) / 34(c) | **BETTER SERVED, not bypassed.** All six registry years, ONE invocation, ONE bundle — which is what those rules demand of a registrable run in the first place. |

## 3. WHY THE SCREEN SHARD WAS **NOT** CANCELLED

Its **control leg is the only control this lane will have**, and it is the instrument that settles
the open G-DRIFT question in PRECOMMIT §5 — where form 4 (the keeper's committed bundle as the
control) could NOT be validated, because the keeper's `git_sha 52a2f519` and
`basis_sha cfc6672...` both fail to resolve and the diff from the keeper's registration commit runs
to 57 files / +6,555 lines across the backcast path.

The screen solves control and arm **at one pinned SHA**, so:

* if the control leg reproduces the keeper's committed 2025 numbers, **HEAD drift for NEISO is
  measured at zero** and the keeper's committed bundle is a valid control for the other five years;
* if it does not, the drift is itself a finding, and the span's year-on-year differences against the
  keeper cannot be attributed to the gas repair alone.

Killing the screen to save one year of LP would have left the span with **no control at all**. The
two shards run in separate containers, so neither constrains the other's memory (rule 12's cap is on
concurrent invocations inside one box).

The screen's **arm** leg is admittedly redundant with the span's 2025 — kept because it is already
solving, and because an arm/control pair solved in the same container is the cleanest possible
differencing.

## 4. THE SHARDS IN FLIGHT

| shard | session | years | legs | budget |
|---|---|---|---|---|
| screen | `session_01YN2vFseWv7SfoPZA9SaBDv` | 2025 | control + arm | 90 min |
| span | `session_017AFvvXgAVw2BBoe55AgyLJ` | 2020–2025 | arm | 300 min |

Both pinned to `b6ded93731fec2a0680a6bb7bf30d6c7caab7656`, which is an ancestor of `main`
(PRs #6192 and #6194) and therefore permanently reachable.

## 5. A PRE-SOLVE CHECK THE SPAN NEEDED, AND PASSED

A six-year replay from a THREE-year keeper bundle is only sound if the recipe is year-invariant.
Checked at zero LP before the shard launched, against the folded touchpoint bundle
(`neiso108_fuelvintage_tp`, 2020–2022, the same recipe under rule 30 `[R-TOUCHPOINT-FOLD]`):

* `scenario_config` differs in **exactly two** fields, `gas_price_override` (2.54 vs 2.03) and
  `weather_year` (2023 vs 2020) — both of which are the **first solved year's** value echoed into
  the recorded config, not a configuration choice;
* `meta.json` differs in `gas_prices`, `shared_inputs`, `timestamp` and `years` — all year-indexed
  measured inputs or provenance;
* `gas_prices` is on `replay_keeper._IGNORE`, i.e. **recorded-only, never a solve kwarg**, and
  `pipeline/backcast_config.py:2239` resolves each year's measured Henry Hub level itself from the
  `year` argument.

So one invocation carries all six years' measured gas levels correctly. **Had this failed, the
six-year shard would have solved 2020–2022 at 2023's Henry Hub price** and the whole span would
have been wasted — which is why it was checked before the LP, not after.
