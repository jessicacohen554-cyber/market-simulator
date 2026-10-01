# ADDENDUM to PRECOMMIT-caiso255 — the phase-0 instrument was blind to HALF the repair, and the G-DRIFT chain is extended past the container loss. **Pushed BEFORE the derive is run and before the repaired artifact exists.**

**Session caiso-255 (continuation), 2026-09-06.** Branch
`claude/caiso-backcast-calibration-x5v8uq`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** (`caiso252_b1_notrim`, `git_sha`
`fa23c1f7`) UNCHANGED, DETERMINATION **CALIBRATED**. Rule 22 `[R-HOLDOUT]`:
2023–2025 only; CAISO holds no `complete`/`final` marker; the holdout spend
freeze is ACTIVE.

**Continuity.** The first caiso-255 instance obtained the owner's grant of
FINDING-caiso254 §4 **OPTION 1**, pre-registered it
(`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md`, merged), landed
`--st-split-report-only` (`f721b582`) and the consolidated G-DRIFT audit
(`9c921d91`, PRECOMMIT §9) — then lost its container with the corpus
un-refetched. **The grant was re-confirmed by the owner at the start of this
continuation** before any artifact work resumed. Nothing in the PRECOMMIT is
relaxed here; this document adds two things and takes nothing away.

---

## §A — THE PHASE-0 INSTRUMENT WAS MEASURING ONE OF THE TWO ARTIFACTS THE REPAIR MOVES

Found by **code inspection**, before the corpus finished downloading and
therefore **before the repaired artifact existed** — the caiso-254 §5.1
precedent, where three instrument divergences were fixed by reading the derive
against the probe rather than by comparing a number to its target.

`scripts/probes/_caiso254_partition_footprint_phase0.py` swapped exactly one
file, `caiso_offer_curve_measured.json`. **The derive writes two, and the
keeper consumes both:**

* `run_config.json` carries **`caiso_offer_surface_conditional = True`**;
* `data/fleet/offer_surfaces.py::_COND_SURFACE_SPECS["CAISO"]` reads
  **`caiso_offer_surface_condbinned.json`** for groups
  `("CC_REGULAR", "CT_PEAKER")`;
* the derive rewrites that ladder from the **same repartitioned buckets** — the
  CT bucket's population changes, so its ladder changes.

Two defects follow, and both are fixed:

1. **Arm B was a HYBRID.** Repaired static bands over the FROZEN conditional
   ladder is a configuration **no solve would ever run**, so the footprint was
   not the footprint of the thing that would be screened. Both artifacts are
   now swapped together, and the probe **refuses** a static-only swap outside
   the null control.
2. **The footprint was blind to the P1 channel.** `mc_base` — the array the
   probe differences — is the assembled **P0** objective; `run_calibration.py`
   builds the conditional markup at **:4333**, *after* the `fleet_only` exit at
   **:4999**, as a **P1-only** bid adjustment. **P1 is THE main run and the pass
   every run is scored on** (CLAUDE.md, Dispatch & Commitment), so a footprint
   computed on P0 alone cannot see half of what the repair moves.

### §A.1 — WHAT IS NOT CHANGED: the screen-year rule, fixed as registered

`F` keeps its registered definition (ADDENDUM-caiso254 §3.1) and
**`argmax_y F` still names the screen year**. The extension reports `F_p1`
(`mc_base` + the conditional markup) **beside** it, never in place of it.

**If the two argmaxes DISAGREE, the registered statistic still governs** and the
divergence is recorded as a **power caveat** on the screen. Choosing the other
year after seeing both is precisely the selection §3.1 exists to forbid, and
this clause is written **before either number exists** so that it cannot be
decided by the answer. The probe prints and persists the caveat itself
(`channels_agree`, `screen_year_p1_channel`).

The null control tightens with the instrument: F, `F_p1` **and** X must all come
back exactly 0 with both arms pointed at the frozen pair.

---

## §B — G-DRIFT: the chain is extended past the audited sha

PRECOMMIT §9 discharged the consolidated audit `fa23c1f7` (keeper) →
`173d0a78`, closing the input side by **measurement**: two `fleet_only` rebuilds
per year with `market_sim` imported from a sparse worktree at the keeper sha vs
HEAD, every LP-visible array **bit-identical** in all three years
(`_caiso255_gdrift_input_identity.json`). That result stands and is not re-done.

`main` advanced while the container was lost. The delta **`173d0a78` →
`d8b64997`** in the rule-29(b) scope is **4 files, +269 / −52**:

| file | Δ | verdict | reason |
|---|--:|---|---|
| `src/market_sim/config/constants.py` | +1 | **INERT** | one name added to an existing `from market_sim.config.capacity_market import (…)` block (`resolve_capacity_adequacy_requirement_published`). A re-export made available; no constant **value** changes, and §9.2 already compared every top-level constant by value. |
| `src/market_sim/pipeline/solve.py` | −12 | **INERT** | the `malloc_trim()` call at the P0→P1 seam is **REMOVED**. Its own inertness argument runs in both directions: it returned heap the allocator already considered free and could not reach a live object, so adding it changed no LP row, bound or objective — and neither does taking it away. |
| `src/market_sim/utils/heap.py` | −40 | **INERT** | the `ctypes` helper for the above, deleted with it. |
| `scripts/lib/invariant_ledger.py` | +268 (new) | **INERT** | forecast-registration governance tooling; nothing on the solve path imports it. |

**⇒ Every hunk INERT. G-CTRL form 4 STANDS; `caiso252_b1_notrim`'s committed
bundle is the control; NO control solve is spent.** §9's `co2` restriction is
unchanged: `import_co2_tons` remains the one LIVE hunk on the whole chain, it
touches a stream that is not in `CRITERIA`, and **this session never differences
`co2` against the keeper**.

**A consequence worth naming rather than discovering.** The `malloc_trim`
removal is inert for *values* and live for *peak RSS*: the P1 build now starts
on top of P0's high-water heap. This box has **15 GB**. It is not a correctness
risk and it does not touch the gate table, but if a solve dies on memory that is
the first place to look — not a mis-specified arm.

**Final re-audit.** Per PRECOMMIT §6.2 the audit that BINDS is the one against
the sha the arm is **solved at**. `main` is still advancing, so this section is
extended once more immediately before the LP, and the solve-time sha is recorded
in the FINDING.

---

## §C — WHAT THIS DOCUMENT DOES NOT DO

1. **No gate is relaxed, re-scoped or redefined.** G4 keeps its 0.05 tolerance
   and ST_GAS keeps its FAIL (PRECOMMIT §5.3).
2. **No threshold in the derive is retuned**, `hr_cut = 8.5` and the antimode
   locator included (§5.4).
3. **The screen gate of PRECOMMIT §7.2 is untouched** — S-1/S-2 structural and
   STOP-ONLY, S-3/S-4 escalating, **C3a excluded in both directions**, neither
   C3a nor C4 able to promote, `co2` excluded.
4. **P-1…P-9 stand exactly as written.** Nothing here adds a prediction or
   softens one.
5. **No `complete` marker is declared**; the stale
   `frontend/data/forecast/program-status.json` top-level `isos.CAISO.keeper`
   stamp is **not touched** (owner asks open, §5.6–§5.7).
6. **No solve is earned by this document.**
