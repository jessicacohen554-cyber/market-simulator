# PRECOMMIT — nyiso-229: the DETECTED-HOUR outage window, 2022 screen

**Session:** nyiso-229 · **ISO:** NYISO · **Date:** 2026-09-12
**Pre-registration under rule 29 `[R-SCREEN]`.** Pushed **before any LP.** Nothing in this document
may be re-cut after a number lands.
**Arm:** `unit_outage_window_hour_grain` `False` → `True` — ONE registered field.
**Keeper `2026-09-09-nyiso-221-fuelvintage-span` UNCHANGED until the owner rules.**
Phase 0 (zero LP, complete): `docs/FINDING-nyiso229-phase0-the-outage-window-grain-2026-09-12.md`.

---

## 1. Phase 0 is DONE, and it is the reason this arm exists

Rule 29 clause (0) — the zero-LP phase must run first, and it did, in full:

* The defect is **measured**, not inferred: 8,144–10,167 unit-hours per year in which the loader
  asserts a unit unavailable while CAMPD's own meter shows `grossLoad > 0`, carrying **0.95–1.38 TWh**;
  **~95 %** of those hours lie within 23 h of a window boundary and carry **~99.9 %** of the energy.
  The schema is rounding the windows; the detector is not misplacing them.
* The **2022 target is arithmetically identified**: on 2022-05-31 the day grain asserts a flat
  **10,053 MW** offline for all 24 h; the detected windows leave **3,657 MW** available at hours 16–17,
  the two hours the model shed **124.9 / 235.6 MW** at VOLL — **29.3× / 15.5×** the shortfall.
* The repair is **verified against the meter** unit by unit (Bowline 2625 u1 available 6–22 vs metered
  6–22, EXACT; Roseton 8006 u1 and u2 each 1 h residual at an 8/10 MW sub-threshold ramp hour).
* **Zero DOF.** The deriver's two stop-the-line assertions prove the grain cannot MOVE a detected
  window, only narrow it, and the new extract's base columns are byte-identical to the committed
  extract on 2022–2025 and 2026 (1,984 rows, hash `aa5e39b967d057f2`).

## 2. Screen year: **2022** — chosen on FOOTPRINT and LIVENESS, never on residual

Rule 29 requires the screen year be where the mechanism's **own measured footprint is largest**, and
forbids choosing it by residual. 2022 is largest on both available footprint measures, both computed
in phase 0 with no reference to any residual:

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| restored capacity, GWh-cap | **3,104.1** | 2,902.8 | 2,405.8 | 2,473.2 |
| restored MW in the control's own tight hours | **1,825** | 1,408 | 681 | 482 |
| firm-load slack in the control | **2 h** | 0 | 0 | 0 |

2022 is also the **only** year in which the arm's headline claim — that the 31-May VOLL event is an
artifact — is testable at all. `[R-HOLDOUT]` was removed 2026-09-09, so 2022 needs no authorization,
no marker and no one-shot; rule 30(c) still binds, and a 2022 number is model-SELECTION evidence,
never a skill claim.

## 3. G-CTRL: **form 4**, no control solve, and the control is already on disk

Rule 29(b): the incumbent's committed bundle is the control. Better here — the **nyiso-228 arm-C
control span covers 2022–2025 at HEAD** and is recovered on local disk (gitignored, untracked):

```
git checkout ed8c60c5 -- results/calibration/nyiso228_control_span    # git_sha d4f97391
```

nyiso-228 §2 validated it to the third decimal against the keeper plus the single LIVE G-DRIFT hunk
(`reliability_floor_coeffs_NYISO.csv`). **G-DRIFT is OWED and is an ADDENDUM to this document,
written before the arm is solved, never after**: audit
`git diff d4f97391 <arm SHA> -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` and
classify **every** changed hunk INERT-with-reason or LIVE. This session's own `src/` changes are
expected to appear and must be classified like any other: the field's off path is byte-inert by test,
but that is a claim the audit states explicitly rather than assumes.

## 4. THE SCREEN GATES — STRUCTURAL, and a STOP gate only

Rule 29: the screen **may kill the arm; it may never promote one**, and it is **never** gated on the
target residual. Every gate below asks whether the mechanism does what its own arithmetic says.

| gate | test | kill condition |
|---|---|---|
| **G-CONF** | exactly one config field moves (`unit_outage_window_hour_grain` F→T); the arm reads `campd-unit-outages-perunitmerithour-NYISO.csv` (sha256 `ee778a87…`) and the control reads `-perunitmerit-` | any second field moves, or either leg reads the wrong extract |
| **G-DIR** | 2022 firm-load slack must **FALL** | slack rises, or is unchanged at 360.5 MWh |
| **G-MAG** | 2022 slack must fall to **0.0 MWh** and the VOLL hours 3616/3617 must clear | any firm-load shed survives — 3,657 MW against 235.6 MW is 15.5× of margin, so a survivor means the mechanism is not doing what §1 says |
| **G-CONF-2** | the dispatch response is **confined to hours the extract changed**: no hour outside the union of the 12,547 restored unit-hours may move a class by >1 MW | a move outside the mechanism's own footprint |
| **G-OVERLAP** | same-unit window overlaps in the arm's extract = **0** (day grain: 293, all 24.0 h) | any overlap survives |
| **G-DEMAND** | **served demand** identical between arms to 4 dp, and dump = 0 in both | served demand moves |
| **G-NONTARGET** | no non-target **load-bearing** criterion (C1/C2/C3b) flips PASS→FAIL on 2022 | a flip |

**G-DEMAND is specified on SERVED DEMAND, not generation**, per nyiso-228 §3.3 / §9: generation is
not conserved when a redispatch changes flow-dependent losses, and that mis-specification failed
spuriously on both nyiso-228 arms (−0.06 and +0.17 / +0.10 TWh). This gate does not repeat it.

**NOT a gate, in either direction — reported only:** C3a, C3b's *value*, and C3c. Phase 0 §6 declared
ex ante that the arm pushes prices **down** (helping C3a-2023/24, hurting C3a-2025 and C3a-2022) and
**lowers** the 2022 C3c count 8 → ~0. Gating on any of those would be the fitted-mechanism selection
rule 1 `[R-STRUCT]` forbids.

**2022 C3c REPORTING RULE (inherited, nyiso-228 §4b): NEVER a bare count.** Every C3c number is
reported with **precision and recall against the market's own 101 hours above $300** (Jan 28 /
Feb 8 / Dec 34 / Aug 15). The control's 8 hours score **0 % precision, 0 % recall**. A count falling
to 0 is therefore **not** a regression, and a count rising is **not** progress unless precision rises.

## 5. IF THE SCREEN CLEARS

The full span as **one** `--year 2022 2023 2024 2025` invocation and **one** bundle (rule 16
`[R-ALLYEARS]`; 2022 is included because the keeper's own touchpoint covers it). The screen bundle is
a **throwaway diagnostic probe** — never registered, never a keeper, never quoted as a keeper number
— and its year is re-solved inside the full bundle. Per rule 31 `[R-RETAIN]` it is **gitignored, not
deleted**, and nothing is removed until the owner has ruled on promotion.

## 6. SHARD CHARTER (rule 32 `[R-SHARD]`) — the parent runs ZERO LP

One shard, one year, ≤20 min. Non-negotiables for its prompt, each earned the hard way in nyiso-228:

1. **`source_revision` is the full 40-char SHA of the commit carrying this PRECOMMIT.** Never a
   branch name — branches here auto-merge and are deleted within minutes. First hard stop:
   `git rev-parse HEAD` must equal that SHA. **Never rebase, never `git pull`, never "sync".**
2. **`DATA PROFILE: nyiso`**, and `pip install -e .` before anything (src/ layout; `PYTHONPATH=.`
   alone leaves `regenerate_clean` subprocesses without `market_sim`).
3. **No `regenerate_clean` datatype list.** Launch the solve and regenerate **only** the partition a
   `DegradedInputError` actually names. A generous list cost nyiso-228 over an hour and two steers.
4. **Its own everything**: `--out-dir results/calibration/nyiso229_hourgrain_y2022/`, branch
   `claude/nyiso229-hourgrain-2022`, and `git add -f <that path>` only — `git status --short` MUST
   show nothing outside it. **`git add -A` / `git add .` are FORBIDDEN by name** (nyiso-228 swept 183
   unrelated files onto `main` that way). **Gitignore the bundle BEFORE the branch can merge.**
5. **Config signature hard stop**: `campd_per_unit_attribution=True`,
   `campd_outage_merit_order_guard=True`, `unit_outage_window_hour_grain=True`, and
   `run_config.json` naming `campd-unit-outages-perunitmerithour-NYISO.csv`. **A shard that sees
   otherwise STOPS and does not push.**
6. **FORBIDDEN by name**: `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
   `prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under `src/` or
   `scripts/`, opening a PR, and deleting any result (rule 31).
7. **Memory**: run the runner unmodified, never pass `--no-container-preflight`, and REPORT the
   `container preflight:` and `memory peak:` lines. Never read `free` or MemTotal.
8. **"A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
   FAILURE."**
9. **Also commit `hourly/unit_hourly_2022.parquet`** (~920 KB) so the parent can score and register
   without a replay — the nyiso-227 lesson.
10. **Report in numbers**, in the final message: 2022 slack MWh and hours, the hours 3616/3617
    values, load-weighted mean/max price, h>$150/200/300, served demand, dump, and the D-2 / C8 rows.
    The parent may never read its disk.

## 7. WHAT WOULD MAKE ME WRONG

Stated now so it cannot be reframed later:

* **Firm-load slack survives on 2022.** With 3,657 MW restored against 235.6 MW shed, a surviving
  VOLL hour means the restored capacity is not reaching the LP — a threading defect in this session's
  own change, not a fact about the market. That kills the arm at G-MAG **and** indicts the code.
* **The response is not confined** to the restored hours (G-CONF-2), which would mean the extract
  swap moved something else.
* **A load-bearing criterion flips on 2022** (G-NONTARGET).
* **The overlap survives** (G-OVERLAP), which would falsify the 293 → 0 phase-0 measurement.

## 8. RULES

1 `[R-STRUCT]` — structure first; the price direction is declared in §4 and is not a gate.
13/14 — the detected hour is the **same measured input at its own resolution**; the day-grain version
is a rounding of it. 16 `[R-ALLYEARS]` — the span is one invocation, one bundle. 19 `[R-ONE-MECH]` —
one artifact, one seam; `unit_outage_per_unit_clip` is **not** co-armed because this gate removes the
artifact the clip caps. 21 `[R-DOF]` — zero free parameters, no new ledger entry. 23
`[R-FROZEN-DERIVE]` — the re-derive cites a construction repair (caiso-183), not a residual.
24 `[R-REGISTRY]` — a registered field precisely so the grain appears in `run_config.json` and
`cache_key()`. 25 `[R-ISO-SCOPE]` — nothing crosses from CAISO. 28 `[R-MECH-MATRIX]` — row minted
with the field, cells in all seven shards. 29 `[R-SCREEN]` — phase 0 first, screen year named here,
gates structural and stop-only, control form 4. 30(c) — a 2022 result cannot decertify NYISO.
31 `[R-RETAIN]` — nothing deleted; the promotion question goes to the owner. 32 `[R-SHARD]` — the
parent runs no LP.
