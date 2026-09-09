# PRECOMMIT — capx D88 screen: fleet-id uniqueness guard + vintage-stamped re-mint

**Lane:** capx D88 · **Branch:** `claude/capx-d88-fleet-id-uniqueness-x31hi6` (fresh off `origin/main`
`d1b8d1bf`) · **Date:** 2026-09-08 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso` + `code`
**Authority:** OWNER RULING **Q62** (2026-09-08, capx ledger §0bf.3(a)) — *"Fix first, flag the verdict now."*
**Source of scope:** `docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md` §2.6.

**This document is written BEFORE the screen arm is solved.** The G-DRIFT audit (§3) and the STOP
gates (§4) are pre-registered here so neither can be written to fit a result (rule 29 `[R-SCREEN]`).

---

## 1. What lands

**(a) The guard** — `data/fleet/arrays.py::generators_to_fleet_arrays` raises `ValueError` naming the
duplicated ids (with multiplicity, ISO and year) when `unit_id` is not unique. Placed at the TOP of
the function rather than at the `unit_ids=` line the read cites: the detected set is identical (the
list is the same list), and failing before ~400 lines of array work makes the raise cheap and the
message clean. One `set` build per call. **Changes no decision.**

**(b) The re-mint** — in `apply_ccs_retrofit`'s conversion block (`ccs.py`), a **non-CAMPD legacy
representative** whose id equals `f"gas_cc_{efficiency_bin}_{zone}"` **exactly** is re-minted
`f"gas_cc_ccs_{efficiency_bin}_{zone}_r{year}"`, and the ledger row gains an **additive**
`to_unit_id` beside the unchanged `unit_id`. `exit_exempt_unit_ids` carries the NEW id; `loss_tracker`
is popped on the **OLD** id (they are different keys and addressing both with one silently mis-targets
one of them — see §2). CAMPD per-plant ids are untouched (`is_campd_bin`).

**Zero `ScenarioConfig` fields, zero constants** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`). Nothing is
transferred between ISOs (rule 25 `[R-ISO-SCOPE]`): one shared seam, no per-ISO number.

**Why the vintage stamp, and why the obvious form is wrong.** `gas_cc_ccs_{bin}_{zone}` alone is
**insufficient**: the T3 record shows one zone converting a second, third and fourth representative
(`bau-prera`: 2031/2040/2042/2044 — reproduced independently at §2 below), and `gas_cc_ccs` is not
aggregatable, so two converted representatives would collide **with each other**. `_r{year}` mirrors
`new_entry.py`'s `{tech}_new_{year}_{seq}`: deterministic, order-independent, unique by construction
once the guard holds (one id converts at most once per year).

**Out of scope, per the charter:** `_AGGREGATABLE_FUELS`; any consumer refactor; the I5 forecast
invariant's own keying (routed to the forecast desk, with this guard named as the fix).
**Boundaries respected:** `ccs.py:475-476` and `evolve.py:664` (concurrent D87 lane) and the
evolution-ledger adequacy-block writer (concurrent D83 lane) are **untouched**. No overlap reached.

---

## 2. Phase 0 and the zero-LP census (COMPLETE BEFORE THE ARM — results in the FINDING)

**Guard silence** is measured on all seven backcast keepers, every solved year (§4 of the FINDING).
**Rule 29 clause (0)** is honoured: the census below is a zero-LP pre-solve gate over the committed
record, and it is what makes the screen year selection non-residual.

**Independent re-census of all 72 committed evolution bundles** (`rename_census.py`, zero LP) —
reproduces the design read exactly:

| class | rows | bundles |
|---|---|---|
| **A. COLLIDING** (the defect fires) | 12 | **all 9 NEISO T3 golden variants** (`bau` 2032·2040; `bau-d46` + its 4 `fc6` arms; `bau-d60`; `bau-d65br`; `bau-prera` 2031·2040·2042·2044) + **ERCOT `ff-t1f-d65br`** 2030 |
| **B. RENAME-ONLY** (no collision; only the id string moves) | 14 | NYISO `d45r`/`d60`/`d65br`, CAISO `d46`/`d60`/`d65br`, MISO `s123/verify`, PJM `s6-pjm/ledger`, ERCOT `d65br` 2029 |
| **C. untouched** | — | 54 of 72 bundles carry no legacy-form retrofit at all |

**In every one of the 26 rows the renamed id appears in NO other decision row in any year** — no
retirement, no floor retention, no thermal addition (`other-rows=NONE`, all 26). That is the
byte-identity evidence the charter asked for on one bundle, obtained on **all** of them.

**`bau-d65br` collides from 2037**, not 2032: its 2031 conversion of `gas_cc_h_class_Central`
(1,000.0 MW = exactly the 2030 economic build) is followed by Central `gas_cc` builds in
**2037, 2039, 2047, 2049**. The chartered 2026–2040 horizon therefore contains the conversion year,
six clean years, and **four colliding years**. Screen-year selection is by the mechanism's own
measured footprint, never by a residual (rule 29 (1)).

**Two `unit_id` tiebreaks are enumerated here BEFORE the solve, because a rename can move a unit
across an exact tie** (both are pre-existing properties of HEAD, not introduced here):

* `retirements.py:2864` — joint entry-competition candidate sort, key `(-depth, unit_id)`;
* `adequacy.py:726` — the D57 sell-offer clearing stack, key `(offer, unit_id)` (PJM-armed only).

Both require **bit-identical** floats to bite. `interchange/miso.py:846` parses `int(uid.rsplit("#"))`
but filters on `_ref{imp,exp}_` first, which a renamed id never matches — **safe by construction**.
`legacy_bins.py:599/679` are coal-only; `eia860.py:2925` runs at base-fleet build, before any
conversion exists. These are named so the arm's ledger diff can be read against a stated
expectation rather than an open one.

---

## 3. G-DRIFT (rule 29 (b) form 4) — the committed bundle IS the control. **NO CONTROL SOLVE.**

Basis is the bundle's **RECORDED CACHE KEY**, not `git diff <git_sha> HEAD` (dead for anything
predating the 2026-08-16 history rewrite).

```
control bundle          results/ff-t3-neiso-golden/bau-d65br/NEISO/0fc42cb56c24d544
recorded key (dir name)                                        0fc42cb56c24d544
recomputed at HEAD + D88                                       0fc42cb56c24d544   ← IDENTICAL
unknown config keys dropped in the reconstruction              0  (zero)
```

**Form 4 is VALID.** Corroborating, from the code: `solve_surface.SURFACE_MODULES` names seven
`config/` + `pipeline/offer_curve_base` modules and excludes `data/fleet` and
`model/capacity_evolution` entirely, and ids are not hashed (`scenarios.py:18691-18717`) — so the
three edited files cannot move a key by either route. **No LP is spent on a control.**

**Horizon truncation is confound-free, verified not assumed.** `config.end_year` reaches only
`runner.py:1380` (the year-loop bound) and two *warning-message* builders in `policy/carbon.py`
(:303, :390). It enters no price, no screen and no decision, so solving 2026–2040 yields the same
2026–2040 decisions as the control's 2026–2050. The arm writes to a redirected `cache_root()` so it
can neither cache-hit nor clobber the control.

---

## 4. STOP GATES — structural only, STOP-ONLY, pre-registered

The gate **may kill the arm; it may never promote it**. It contributes to no determination and is
**never read against a residual** (rule 29; rule 1 `[R-STRUCT]`).

| # | gate | pass condition |
|---|---|---|
| **G1** | guard silent | the `ValueError` does not fire in **any** year 2026–2040 |
| **G2** | pre-conversion identity | ledgers **2026–2030 BYTE-IDENTICAL** to the control |
| **G3** | conversion year is rename-only | **2031** differs from the control in **exactly one way**: the additive `to_unit_id` key on the one legacy-form `ccs_retrofits` row. **No decision moves** — same retrofit set, same MW, same retirements, same additions |
| **G4** | pre-collision years | **2032–2036** carry **no decision delta** (retirements, thermal/renewable additions, retrofits, floor retentions all equal) |
| **G5** | the defect is gone | from **2037** the fleet carries **no duplicate `unit_id`**, and every `ccs_retrofits` row carries a **distinct** `to_unit_id` |
| **G6** | scope | **no NON-GAS ledger row moves in any year** |

**G2/G3 CORRECT THE CHARTER'S LITERAL TEXT, and the correction is stricter, not looser.** The charter
pre-registered "2026–2031 ledgers byte-identical". That is unsatisfiable *by construction* on this
recipe and would have been a false gate: the conversion — and therefore the rename and its additive
ledger key — **lands in 2031**, six years before the first collision. Splitting it into G2 (2026–2030
byte-identical) + G3 (2031 rename-only, no decision delta) + G4 (2032–2036 no decision delta) tests
the charter's actual intent — *nothing decided moves before the first colliding year* — over a
**five-year-wider** span than "2026–2031" did. Recorded here, before the solve, rather than
reconciled after it.

**A G3/G4 decision delta is a KILL**, not a finding to explain away: with no duplicate in those years
there is no mechanism by which the repair may move a decision, so a delta means the rename reached
something the §2 enumeration missed.

**What the screen deliberately does NOT test:** whether the corrected 2037–2040 decisions are
*better*. The size and direction of the decision delta are **UNMEASURED** and this lane does not
assert one; the screen measures that the collision is gone and that nothing outside its window moved.
Scoring the corrected NEISO T3 run is **not this lane's** — it routes to the D63/D65-B batch on
repaired code.

---

## 5. Retention (rule 31 `[R-RETAIN]`)

The screen bundle family is **gitignored the moment it is written** and **NOT deleted** — rule 29 (c)
is discharged by keeping it out of `main`, never by `rm`. It sits on local disk, which is ephemeral:
the promotion question is asked explicitly in the session's close.

## 6. Owed deliverables

The cache-epoch entry naming the nine NEISO T3 variants + ERCOT `d65br`; the NEISO matrix shard's
`ccs_retrofit_screen` cell (rule 28 duty b); the additive `ff-verdicts.json` provenance flag on
`neiso-t3` (Q62's second half); and `FINDING-capx-d88-2026-09-08.md`.
