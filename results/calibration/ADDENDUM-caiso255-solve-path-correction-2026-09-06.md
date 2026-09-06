# ADDENDUM to PRECOMMIT-caiso255 — the arm's SOLVE DRIVER, and a correction to §6.1's mechanism (the substance is unchanged and STRONGER; the stated means was wrong)

**Session caiso-255, 2026-09-06.** Pushed **before any LP is spent** and before
the corpus finishes downloading. Keeper `2026-09-05-caiso-252-b1-notrim`
(`git_sha` `fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22: 2023–2025
only; no `complete`/`final` marker; freeze ACTIVE.

---

## §A.1 — THE CORRECTION

PRECOMMIT §6.1 registered: *"This session solves every arm with
`--no-p1-basis-seed`."* **That names a flag the arm's driver does not have**,
and it is corrected here rather than discovered in the FINDING.

The arm's delta is a **changed measured artifact on disk**
(`data/raw/_validation-source/caiso_offer_curve_measured.json`), which
`pipeline/backcast_config.py` merges into `offer_curve_by_group` at
config-build time under the keeper's already-armed
`caiso_offer_surface_measured` / `_ungrounded`. It is **not** a
`ScenarioConfig` override. So the arm is the keeper's own byte-faithful
replay with the artifact swapped underneath it:

```
# with the repaired artifact in place at data/raw/_validation-source/
PYTHONPATH=.:src uv run python scripts/replay_keeper.py \
    results/calibration/caiso252_b1_notrim \
    --out-dir results/calibration/<arm> --years <year(s)> --note "<...>"
```

**`replay_keeper.py` has no `--no-p1-basis-seed` flag, and needs none.**

**Explicitly NOT used: `--offer-curve-json`.** It exists on this driver and
would have been the convenient route, but it replaces the keeper's
`offer_curve_overrides` — a **different channel** from the measured-artifact
merge the repair actually lives in. Routing a measured-surface change through
the override bag would misrepresent the mechanism in `run_config.json` and in
the DOF ledger (rules 24 `[R-REGISTRY]` and 1 `[R-STRUCT]`). The artifact swap
is the honest representation, and it is the same seam
`_caiso254_partition_footprint_phase0.py::_arm` already uses for phase 0.

---

## §A.2 — WHY THE SEED IS OFF ANYWAY, TWICE OVER — READ FROM THE CODE, NOT ASSUMED

| # | mechanism | evidence |
|---|---|---|
| 1 | **The driver pins the cross-year gate OFF.** `replay_keeper.DETERMINISM_ENV = {"MARKET_SIM_WARMSTART_XYEAR": "0"}` and `main()` applies it at `replay_keeper.py:623`. In `pipeline/solve.py:456` that makes `_xwarm = False`, and `_p1_seed` at `:473` requires `_xwarm` — so the seed is unreachable whatever the env var says. | `replay_keeper.py:48, 603, 623`; `solve.py:454-477` |
| 2 | **The CLI default-flip is never executed.** `replay_keeper` calls `run_calibration_full.solve_and_persist` **directly, not through the CLI** (its own module docstring, line 4), so `resolve_p1_basis_seed_default` — the function that flips `MARKET_SIM_P1_BASIS_SEED` ON for a fresh calibration solve — never runs. Its docstring states the same boundary from the other side: the direct `solve_and_persist` callers "keep the global default OFF." | `replay_keeper.py:4, 46-48`; `run_calibration.py:6694-6721` |

**This is STRONGER than the flag would have been, not weaker.** A flag is a
thing I have to remember on every invocation; the pin is a property of the
driver, and it is the **same** pin the keeper's own replay path carries — so
the arm and the control share an identical solve path **by construction**.
PRECOMMIT §6.1's substance is untouched: the P1 basis seed is **UNREACHED**
rather than asserted-inert, and **G-CTRL FORM 4 STANDS with no control solve
spent**.

**Verification duty this creates, discharged at solve time, not asserted:** the
FINDING records the arm's resolved `MARKET_SIM_WARMSTART_XYEAR` and
`MARKET_SIM_P1_BASIS_SEED`, and the solve log's `p1_seeded` / cold-P1 line, so
the claim is evidenced by the run rather than by this document. **If either
reads armed, the arm is discarded and re-solved** — a seeded P1 is not
form-4 comparable to `caiso252_b1_notrim`.

**The §6.1 governance observation is UNCHANGED and still open:** the seed is
default-ON for any ISO's next *CLI* calibration solve and is validated on
ERCOT alone. A CAISO-side neutrality A/B remains an owner ask, not this
session's work.

---

## §A.3 — RULE 12 `[R-PARALLEL]` / RULE 16 `[R-ALLYEARS]`: how the full span is invoked

Rule 16 requires ONE bundle over `2023 2024 2025`; rule 12 requires the years
**sequential**. `replay_keeper` offers both shapes and the choice is recorded
here in advance:

* **Preferred:** one invocation, `--years 2023 2024 2025`, which solves them
  sequentially in one process — one bundle, one recipe, nothing to reconcile.
* **Fallback if that OOMs on the 15 GB box:** the driver's own per-year
  invocation chain (`--years <y>` + `--reuse-solved <prior bundle>`), which
  the help text documents as the rule-12 shape and which still lands **ONE**
  bundle. Reused years are byte-copies, not fresh evidence, and the FINDING
  says so if this route is taken.

Either way it is one bundle and one registration. **The screen (§7 of the
PRECOMMIT) is a separate, throwaway single-year bundle, deleted before the PR
merges** (rule 29(c)).

Nothing else in the PRECOMMIT is amended. Its predictions P-1…P-9, its stop
rule, its screen gate and its promotion basis §5(8) stand exactly as written.
