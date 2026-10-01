# FFR-3A-4 — the last battery leg measured, and FFR-3A-3's instrument debt closed

**Session.** FFR Wave 3, battery-close lane, **fourth and final pass**. This
document is an **addendum** to both predecessors. Neither is rewritten; where a
number or a claim moves, it is stated here and a pointer left behind (the
Addenda A–G convention).

* `docs/handoffs/ffr-3a2-battery-close-2026-08-03.md` — the 14-leg battery and
  its self-recorded **provenance ceiling**.
* `docs/handoffs/ffr-3a3-battery-close-2026-08-04.md` — the six-leg post-fix
  re-measurement that corrects it. **Its §§2–5 are FINAL and are not revisited
  here.**

**Nothing is promoted. Nothing is tuned.** No `ScenarioConfig` default moved, no
band widened, no damper unarmed, no parameter adjusted in response to any score.
Owner Addendum D.1 (*HOLD PROMOTION, FIND ROOT CAUSE*; D-1 and D-2 stay ARMED)
and Addendum G.1 (the D-8 `exit_rate_limits` ships default-OFF) are honoured
throughout, verified in the **resolved** config rather than the request (§2.1).

---

## 1. What this session was for

FFR-3A-3 closed its lane except for **one unmeasured leg and four instrument
blockers**. This session finishes exactly that list and adds nothing to it.

| item | status |
|---|---|
| MISO T1-X — the one unmeasured leg | **MEASURED, scored, registered** (§2) |
| Blocker 1 — `ScenarioConfig.from_yaml` is strict | **FIXED** + 2 tests (§3.1) |
| Blocker 2 — run-id collision unguarded | **FIXED** + 6 tests (§3.2) |
| Rule 28(b) — D-1/D-2 matrix citations | **CLOSED** for PJM/MISO/NYISO/NEISO (§4) |
| Blockers 3–5 (413 push, OOM contention, FC-7) | **carried, not closed** (§6) |

## 2. MISO T1-X — measured, and the prediction held

Full record: `results/ffr3a4/RESULT-miso-t1x-2026-08-04.md`, scored against
`results/ffr3a4/PREREG-miso-t1x-2026-08-04.md`, which was committed **before the
bundle existed** (`00b0637c`, merged as PR #3494) per rubric §4.

Run `miso-2023-2027-crossover-ffr3a4` · key `46954f417b6e18e2` · solved
`[2023, 2024, 2025, 2026, 2027]`. It completed in ~20 min at ~6.5–7.2 GB peak,
**solo**, with all bookkeeping done before launch and none during.

### 2.1 Posture

All six solve-affecting flags omitted. **`run_config.json` records the CLI
REQUEST — every one reads `None` — and is NOT the resolved posture**; this is
the FFR-3A-2 §1.2 request-vs-resolved trap in a new place, and it is worth a
successor's attention. Read from `run_config.yaml` and independently from the
runner's startup log, they agree: `retirement_rule=pipeline`,
`entry_rate_limits=True`, `entry_commissioning_lag=True`,
`entry_lookahead_reprice=True`, `correlated_forced_outage=True`,
`exit_rate_limits=False`.

Rule 22 re-read at this head, not inherited: `HINDCAST_SOLVE_YEARS={2021,2023,
2024,2025}`, `HINDCAST_BRIDGE_YEARS={2022,2026}`, scoring bounded to 2023–2025.
The freeze is **ACTIVE**; no marker spent, no out-of-training year solved,
scored or registered.

### 2.2 Result — every banded metric reproduces at +0.0000

All ten banded rows are identical to the pre-fix comparator
`miso-2023-2027-crossover-ffr3a2` to three decimals: price `0.1360 / 0.1385 /
0.2743`, co2 `0.6333 / 0.5887 / 0.7546`, gas_twh `0.0950 / 0.1510`, coal_twh
`0.0099 / 0.0158`. 2025 gas/coal remain uncovered (preliminary EIA-923 vintage).

**The T1-X half of the battery is now complete, and all three legs — ERCOT, PJM,
MISO — are completely unmoved by the G3 cap-grain fix `2adfb49`.**

### 2.3 The mechanism, not just the number

The PREREG fixed a discriminator in advance precisely so an unchanged score
could be distinguished from cancelling errors. Executed retirements:

| 2023 | 2024 | 2025 | 2026 | 2027 |
|---|---|---|---|---|
| 0 | 0 | 0 | **3 economic / 432.8 MW** | 4 announced |

**Zero executed economic retirements anywhere in the scored window**; the exits
land in 2026, solved but never scored. A fix to the screen's *admission* set has
nothing to act on inside 2023–2025, so the null is **structural**.

This reproduces in MISO the pattern FFR-3L established for ERCOT's crossover, on
**MISO's own evidence** (rule 25 clean, nothing imported). It also answers the
tension the dispatching prompt flagged — *MISO's T1-H moved most of the four, so
this is not free*: T1-H seeds from 2020 over 2021–2025 and executes exits inside
its scored window; T1-X seeds from the 2023 vintage over 2023–2027 and does not.
Same fix, different decision set, different fleet — the PJM precedent exactly.

### 2.4 Determination — HOLD

FC-4 FAIL (co2 63.3/58.9/75.5 %; gas_twh 2024 15.1 %; price 13.6/13.9/27.4 %
CAVEAT) + FC-7 FAIL. Scored **without** `--run-config`, like-for-like, for the
reason FFR-3A-3 §6.3 records. Same category pattern as all six of its legs.
**No determination moved; the §2.1b gate stays closed for all six ISOs on
criterion (b).**

## 3. The instrument fixes

### 3.1 Blocker 1 — `from_yaml` was strict, so a rule-26 deletion stranded bundles

A bare `cls(**data)` meant any rule-26 `[R-DELETE]` field removal made every
bundle config written before it permanently unloadable with `TypeError:
unexpected keyword argument`. It had already bitten: collapsing
`pjm_seam_envelope_by_neighbor` at `2ca08ed9` made **all six FFR-3A-3 bundles
unregisterable**, worked around by hand-stripping the key from 12 configs.

`from_yaml` now **drops unknown keys with a loud `RuntimeWarning`**. Dropping is
safe in the only direction that matters — a key this codebase no longer has is a
knob that no longer influences a solve — but the warning is deliberately loud,
because an unknown key still means the loaded config is **not** a byte-faithful
reconstruction of the writer's. Two tests pin both halves (drops + warns; silent
on a clean load).

That the fix was needed is visible in this session's own window: the
`pjm_seam_envelope_by_neighbor` deletion appears in the 218-commit
`941f4983..origin/main` diff.

### 3.2 Blocker 2 — the run-id collision is now refused

The id is the bundle directory basename, so out-dirs named `pjm` under `t1h/`
and `t1x/` resolve to one sidecar and the second registration **silently
overwrites** the first. FFR-3A-2 logged it as blocker 9; FFR-3A-3 reproduced it
(six registrations → five sidecars, caught by counting outputs, not by an error).

`build_sidecar` now refuses an id already held by a run with a different
`(iso, kind, start_year, end_year)`, printing both identities and the fix.
Re-registering the **same** run stays legal — re-scores and
`--preserve-invariants` refreshes are routine. The check runs **before** the lazy
invariant import, so a refused registration does no work. Six tests, including
one asserting the guard is actually wired into the id-derivation path rather
than merely defined.

## 4. Rule 28(b) — the matrix debt, closed

FFR-3A-3 re-measured D-1/D-2 behaviour across four ISOs and did not update the
matrix. Citations added to `economic_retirement_screen` (PJM/MISO/NYISO/NEISO)
and `entry_dampers`, plus this session's own MISO T1-X structural null.

**No cell moved and no verdict was minted.** FFR-3A-3 ran no control arm, no
determination moved, all six legs are HOLD; and a crossover whose scored window
executes no exits is a null by construction (the FFR-3C §3.2 pattern), which is
evidence for neither rule. Matrix integrity verified: **221 warnings / 0 errors
before and after** — the anchor drift is pre-existing, not introduced here.

## 5. Verification discipline used here

* Every push blob-verified (rule 27): local vs remote hash and line count.
  `scenarios.py` confirmed at **11,422 lines**, not truncated.
* The "218 commits carried zero default-ON additions" claim was **re-derived for
  this session's own window**, not inherited — and extended, because the
  prompt's grep catches only *additions*: checked for *flips* of existing
  defaults too. Four new bool fields, all default-OFF; zero flips.
* An unrelated formatter reflow of
  `scripts/data/derive_chp_power_only_heat_rates.py` appeared twice and was
  reverted both times rather than ridden along in an unrelated commit.
* `program-status.json` was first rewritten wholesale by an `ensure_ascii=False`
  round-trip (133-line diff); reverted and redone to match the file's existing
  encoding, giving a **6-insertion targeted diff**.

## 6. Blockers carried forward, NOT closed

1. **`git push` cannot create a branch through this remote — HTTP 413
   regardless of pack size.** Reconfirmed. Working recipe unchanged:
   `mcp__github__create_branch` first, then ordinary `git push`. The branch was
   auto-merged and deleted mid-session **again**, so this recurs every session.
2. **Heavy crossover legs OOM under concurrent work.** Respected rather than
   retested: MISO T1-X peaked ~7.2 GB with 7–8 GB free, and every git/scoring
   operation was kept strictly outside its window. It survived.
3. **A `pgrep -f <script>` check false-positives on its own command line.** This
   session hit it twice and misreported a solve as running once. The documented
   trap is that pgrep returns the `uv` wrapper at ~0.03 GB; this is a second,
   distinct failure mode of the same check. **Use `ps -eo rss,args | grep
   "[r]un_..."` with a bracket pattern.** Both modes were observed in one output:
   wrapper 0.03 GB alongside the real process at 7.17 GB.
4. **FC-7 fails on every leg by construction** — FFR-3A-2 blocker 5, unchanged.

## 7. Standing disclosure list

Carried verbatim from `docs/forecast-readiness-peer-review-2026-07.md` §4:

> This forecast is produced by a chronological full-8760 LP dispatch model with a
> one-pass annual capacity-evolution loop. It does not include: MIP unit commitment;
> intertemporal capacity optimization or within-year entry/exit convergence;
> inter-hour ramp constraints; intra-ISO hurdle rates; demand-responsive fuel
> pricing. Unless produced by the weather ensemble, results are conditional on a
> single pinned weather year (stated in the run config). Uncertainty bands are
> dispatch-conditional: the fleet-path (capacity-expansion) component of structural
> error is unmeasured and excluded. Deterministic scenario cases are a range, not a
> probability distribution.

## 8. For the successor

1. **The FFR-3A battery is CLOSED.** All 14 legs measured; T1-X complete across
   ERCOT, PJM and MISO. Do not re-run any of them without new evidence.
2. **Do not attribute a scored MISO T1-X movement to the retirement rule.** Its
   scored window executes zero economic exits — the instrument cannot test D-1.
   The standing candidate for testing an exit mechanism remains the T1-H
   2021–2025 vintage-2020 posture, where exits actually execute (FFR-3F §10.1).
3. **The depth residuals remain G-31's**, not a tuning target. PJM over-retires
   and MISO under-retires; one throughput story will not explain both.
4. **Two backcast-lane facts remain open and are NOT this lane's**: NYISO's
   criterion (a) reads `NOT-YET`, and MISO's determination is still **not
   parseable** (no `complete` marker, and its promotion note carries no
   determination string), so MISO renders blank on the §2.1b board's (a) column.
5. **Criterion (d) is the owner's.** `final` is empty by design; nothing here
   touches it.
