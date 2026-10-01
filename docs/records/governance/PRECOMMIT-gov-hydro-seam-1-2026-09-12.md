# PRECOMMIT (gov-hydro-seam-1): the hydro benchmark seam and the `classify_plant`
# WAT/PS short-circuit — decided on STRUCTURE, before any effect number

**Session** `gov-hydro-seam-1` · **Scope** CROSS-ISO GOVERNANCE · **Date** 2026-09-12
**Base** `origin/main` @ `fb73c4f6` (the handoff cites 5327e60d; main moved, and this
document is written against what is actually at HEAD).
**ZERO LP by default.** Committed artifacts + measured sources only. The parent never
solves (rule 32 `[R-SHARD]` (a)), and nothing here earns a solve.
**Commissioned by** `docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md` §7 and §9.

---

## 0. THE DECISIONS, STATED BEFORE THE EFFECT IS MEASURED

### Decision 1 — take pjm-h1 §7 option **(a)**, **UNCONDITIONALLY** (no gate, no flag)

Gate the `hydro` limb of `_backfill_renewables_eia930`'s EIA-930 swap on
`not data.hydro.eia930_wat_level_folded(iso, year)`.

**The structural argument, which is the whole basis:**

1. **The two sides of the comparison are different populations.** The LP's hydro units
   are EIA-923 prime mover `HY` — conventional inflow hydro — **by construction and not
   by convention**: `data/hydro.py::_load_hydro_generation` filters
   `prime_mover == HYDRO_PRIME_MOVER` **directly**, never through the classifier. A BA in
   `EIA930_PS_FOLDED_INTO_WAT` files no `NG: PS`, so its `NG: WAT` is conventional hydro
   **plus pumped-storage gross discharge**. Scoring the first against the second is a
   unit mismatch. Rule 14 `[R-ACCURATE]`.
2. **The predicate already exists and is already owner-adjudicated.** `eia930_wat_level_folded`
   is the repo's own answer to *"is this ISO-year's `NG: WAT` an admissible LEVEL for a
   conventional-only unit population?"*, adjudicated three times (miso-109 standing fold,
   miso-110 forward climatology, neiso-72 time split). Rule 19 `[R-ONE-MECH]`: reuse the one
   mechanism at the other end of the same comparison; do not build a second.
3. **`pjm-143` already moved the MODEL onto the clean population** and its §7 open list does
   not name the benchmark. This is that decision's unactioned complement, not a new lever.

**Zero new parameters, zero new registry, zero new constants, zero new `ScenarioConfig`
fields.** UNCONDITIONAL because rule 26 `[R-DELETE]` — a flagged both-ways path is a
re-armable wrong construction — and because the model side landed unconditionally. A
`ScenarioConfig` field would also be a scenario knob over a *benchmark* construction that
has no scenario meaning, and would trip rules 24 and 28(c) for no gain.

**THE COST, NAMED BEFORE IT IS MEASURED.** A folded ISO-year's hydro actual then rests on
EIA-923's own completeness. In an early-release vintage that filing is severely truncated
(PJM 2025 `HY` = 2.29 TWh against a modal ~8.9), so the repair is only admissible if such a
year falls through to something defensible.

**The early-release design decision, and its rationale:** a folded ISO-year takes the
**existing** `ann930 <= 0.0` branch — the prior complete year's class total scaled by
vintage completeness, monthly shape reused (the nyiso-106 repair). **An INADMISSIBLE
authority is treated as an ABSENT authority, because that is what it is.** The class is then
in exactly biomass's and NYISO-solar's position: absent from CAMPD, with no usable EIA-930
series, truncated by a partial vintage. **No new machinery, no new threshold, no new
parameter**, and conservative by construction — a carry-forward under-states a truncated year
rather than fitting it (rules 13 / 21). The alternative — a bespoke branch for the folded
case — is refused as a second mechanism for one phenomenon (rule 19).

### Decision 2 — fix the `classify_plant` WAT/PS short-circuit, and it is a **PRECONDITION**
### for decision 1, which pjm-h1 did not state

`classify_plant('WAT','PS',…) -> 'hydro'`, two lines under a comment asserting the opposite.
Repair: `PS` returns `OTHER` before the WAT test.

**pjm-h1 §7 says "(a) is not needed for it, and it is not needed for (a)". That is true only
in the sense that each compiles alone. It is false as a correctness claim:** under (a) ALONE
a folded ISO-year's hydro actual becomes the EIA-923 `hydro` **bucket**, which today carries
PS **net** — negative. PJM 2023 would land on **6.4513 TWh** where the conventional `HY`
population is **8.9763 TWh**: (a) alone trades a **+73 %** error for a **−28 %** error and
lands on a third population that is neither side of the comparison. **(a) is a repair only if
the bucket it falls back to is conventional-only, and decision 2 is what delivers that.**

Basis: rule 26 `[R-DELETE]` — fix it, do not flag it both ways — plus the dead
`_pumped_storage_plant_ids` guard, which asserts a behaviour the code does not have.

---

## 1. PRE-REGISTERED STOP GATES — these are STOP gates only, and none reads a residual

Failing any of G1–G4 stops the change and the session reports that as its result
(rule 29 `[R-SCREEN]`: a screen may kill an arm, never promote one).

| id | gate | stop condition |
|---|---|---|
| **G1** | **Solve-path purity of decision 2.** The ONLY thing the repair may move is EIA-923 `WAT`/`PS` rows from `hydro` to `OTHER`. | Any non-`PS` row moves class; any `PS` row does not; any dominant-class flip reaches `_GAS_BIN_GROUPS` (the ERCOT bin-override solve path); any `mixed_fossil_plants` membership moves. |
| **G2** | **The injected `OTHER` must-run class — a SOLVE INPUT — is unchanged.** `_pumped_storage_plant_ids()` becomes LIVE for the first time and filters by **plant id, not by row**, so a plant carrying both a PS generator and a non-PS `OTHER` unit would lose the non-PS energy too. | `_reconciled_mustrun_class("OTHER", …)` moves by more than float noise in ANY (ISO, year). A move here makes the change SOLVE-AFFECTING and it becomes an owner card, not a landing. |
| **G3** | **Cache-key identity.** `check_cache_key_registration --base origin/main` clean, and no edited file contributes a module-level surface value. `plant_taxonomy` IS in `solve_surface.SURFACE_MODULES`, so this is checked, not assumed. | Any key moves. |
| **G4** | **All seven keepers hold their determination**, re-scored before and after from committed artifacts. | Any determination flips **in either direction** — a flip toward PASS is not a win, it is evidence the change does more than it claims. |

**Bench regeneration is measured CONTROL-vs-ARM.** Committed bench parts may be stale for
reasons that are not mine (the nyiso-148 flipset defect), and
`check_bench_freshness`'s PAYLOAD_SOURCES **does not include `run_calibration_full.py`**, so a
benchmark-construction change does not move the stamp at all. Every part is therefore
regenerated **twice** — once at `origin/main` (control) and once at the arm — and only the
**difference** is attributed to this change. Pre-existing drift is reported, never absorbed.

---

## 2. WHAT IS EXPLICITLY NOT CLAIMED

* **This is gate-neutral and is not expected to move a determination.** pjm-h1 §4 measured
  the C1 volume band moving **0.000 TWh** in all six PJM years (the 8 TWh cap binds either
  way) and zero C1 cells flipping; `hydro` is not a C1 row. Its value is (i) a published
  per-class number that is currently wrong in both directions, (ii) forecast credibility on
  the same `NG: WAT`-vs-`923 HY` choice, (iii) retiring a shared classifier that contradicts
  its own comment.
* **±0.9 % like-for-like on PJM hydro is PLUMBING, NOT SKILL** (pjm-h1 §3): the model's hydro
  level is pinned to EIA-923 `HY` by `hydro_level_923_hy`, and hydro is a declared D-10 free
  class. Nothing here is quoted as forecast skill.
* **No hydro DISPATCH mechanism is proposed.** An accounting mismatch cannot be repaired by a
  dispatch lever, and arming one against a seam-inflated gap would be fitting to a measurement
  error (rule 1 `[R-STRUCT]`). PJM's `pumped_storage_cycling_depth` stays `G`.
* **No keeper is promoted, demoted or re-keyed** — out of scope for this session by charter.

---

## 3. RULES

* **Rule 1 / 13 / 14** — decided on construction (two populations), never on a residual. The
  repair's direction is set by which population the LP's units are, which is fixed by
  `_load_hydro_generation`'s `HY` filter and cannot be chosen by a result.
* **Rule 19 `[R-ONE-MECH]`** — one predicate (`eia930_wat_level_folded`) at both ends of the
  comparison; the early-release fall-through reuses the existing carry rather than adding a
  branch.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the commit cites the construction repair and
  `EIA930_PS_FOLDED_INTO_WAT`. No residual is cited anywhere.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing fitted on one ISO reaches another; the change is one
  shared predicate applied identically, with no per-ISO number.
* **Rule 27 `[R-PUSH]`** — `run_calibration_full.py` (13,954 lines) and `plant_taxonomy.py`
  (321) are both ≥ 300. Edited LOCALLY with Edit; exact on-disk bytes pushed; blob verified
  (line count + sha) immediately after each push.
* **Rule 32 `[R-SHARD]`** — the parent never solves. `--rebuild-benchmark` is explicitly a
  post-processing step over persisted dispatch parquets ("no LP re-solve needed"), so it is
  zero-LP and stays here.
