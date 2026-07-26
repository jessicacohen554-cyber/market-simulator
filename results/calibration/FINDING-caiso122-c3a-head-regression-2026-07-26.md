# FINDING — caiso-122 STEP 1: the C3a-2025 HEAD regression is **NOT a code regression and NOT in `src/market_sim/`** — it is the arrival of the **measured CAISO CAMPD unit-outage extract** (`data/raw/campd-unit-outages-CAISO.csv`, created by `59f8bc30d` 6 h 16 m AFTER the keeper solved). The keeper ran `outage_source="historic"` with **zero unit outages applied**, because `unit_outage_derate_factors` **silently returns `{}` when the file is absent**. Verdict: the new behaviour is **CORRECT** (rules 1 `[R-STRUCT]`, 14 `[R-ACCURATE]`) — **the keeper is STALE, and must NOT be reverted to recover C3a** (2026-07-26)

**Blocker status: RESOLVED.** The CAISO lane is unblocked. The keeper
`2026-07-23-caiso-netrev-margin-keeper` is superseded on data grounds, not on
merit: its headline **C3a-2025 PASS (+9.97 %, a 0.03 pp margin) was obtained
with the measured CAISO outage overlay silently missing**, and is not
reproducible with that overlay present.

---

## §1 — why the prescribed bisect could never have found it

caiso-121 recommended bisecting `abb0fcd..HEAD` over `src/market_sim/`. Two
reasons that search terminates empty:

1. **`abb0fcd` is not in the repository.** The keeper's recorded
   `meta.git_sha = "abb0fcd"` resolves to no object even after
   `git fetch --unshallow` (8,839 commits, all `origin` refs). It was a
   session-local commit on a branch that did not survive to `main`. The
   reachable proxy for "the keeper's basis" is therefore its **timestamp**,
   `2026-07-23T22:29:35`; the container clock is `Etc/UTC` (`date` == `date -u`),
   so that is 2026-07-23 22:29:35 **UTC**.
2. **The moving part is not code.** Every `src/market_sim/` commit in the
   window is either ISO-scoped away from CAISO or gated default-off:

   | commit | change | why CAISO-inert |
   |---|---|---|
   | `31035427f` | DAM-first/CAMPD-fallback outage overlay in `fleet/arrays.py` (names CAISO) | reads `getattr(config, "caiso_dam_outages", False)`; the field lands later (`43d6d37b6`) as `caiso_dam_outages: bool = False`, and the keeper's `meta.json` carries no such key |
   | `3babe5f8a` | eGRID co-located heat-rate reconciliation | self-verified blast radius "3 rows, 1 plant, MISO only" — reproduced here: the only repair logged is MISO plant 55641 |
   | `af7492706` | EIA-930 degenerate solar-distribution repair | keyed on a degeneracy test; NYISO solar is the only cell that reaches the fallback and fails it, other 30 ISO-year-mode CF arrays byte-identical |
   | `e411d1fd9` | wave-4C retirement revenue attribution | `capacity_evolution/retirements.py`; not on the backcast path |
   | `518084e70`, `da3e97900`, `87b95868d` | ERCOT coal / DAM / wind-shape | ERCOT-gated |
   | `826eac749`, `d4dfe0199` | MISO outage composition / `lru_cache` probe | MISO-gated / instrumentation |
   | `439cb0329`, `e19ed0368`, `738aef35a` | PJM interface overlays, pjm-121, pjm-123 | PJM-gated |
   | `d13a3f2c6` | EIA-930 zero-coded filing gaps treated as missing | **scorer/benchmark only**, not the solve |

## §2 — what actually changed: the file did not exist

`data/raw/campd-unit-outages-CAISO.csv` is **created**, not modified, by:

```
59f8bc30d  2026-07-24 04:45:10 +0000  campd-outage-backfill 2018-2026 (all six ISOs) + EIA-923 non-CAMPD fallback
```

— **6 h 16 m after the keeper finished solving.** Two later commits refine it:

| commit | when (UTC) | effect on the CAISO extract |
|---|---|---|
| `59f8bc30d` | 2026-07-24 04:45 | **creates** it (+4,497 rows) |
| `49e85fb4a` | 2026-07-24 05:50 | "re-derive CAISO in full (owner instruction)" (+642) |
| `6a8f285c5` | 2026-07-26 00:36 | neiso-65 guard-corrected extracts: −810 rows split out to `campd-unit-outages-layup-CAISO.csv` (economic layup ≠ outage) |

Inventory at the keeper's basis vs HEAD makes it unambiguous — at
`59f8bc30d^` the only `campd-unit-outages*` files in the tree are
`-maxgen-MISO`, `-short-MISO`, `-short-PJM`. **There is no CAISO extract of any
kind.**

**It was not gitignored.** The `.gitignore` at `59f8bc30d^` carries no pattern
matching the path (`/*.csv` is root-level only; the `data/raw` exclusions are
specific directories — `eia-860/*.csv`, `pjm-energy-offers/*`, …). The file was
absent, not hidden, so no locally-derived copy is implied.

## §3 — the defect that let it pass silently

`src/market_sim/data/outages.py`, `unit_outage_derate_factors`:

```python
csv_path = unit_outage_csv_for_iso(iso)
df = _load_unit_outage_events(csv_path, iso)
if df is None:
    return {}          # <- missing file == "no outages", indistinguishable from a clean fleet
```

The keeper's recipe sets `outage_source: "historic"` — it **asked for** the
measured CAMPD availability overlay. It received an empty dict. Nothing in the
run log, `meta.json`, `run_config.json` or the attestation records that the
requested overlay resolved to nothing.

This is the same class of defect `439cb0329` fixed for PJM three days earlier
("pjm-119: measured interface/ramp overlays **hard-fail instead of silently
degrading**"). The CAISO/`outages.py` path had not yet been converted.

## §4 — magnitude, and why it lands on 2025 hardest

Measured at HEAD (`unit_outage_derate_factors(year, iso="CAISO")`, the ≥5-day
full-stop path), against the keeper's implicit zero:

| year | plant-tranches derated | Σ(1 − availability) over hours | keeper's CA λ drift (caiso-121 §0) |
|---|---|---|---|
| 2023 | 30 | 96,233 | +0.47 % |
| 2024 | 28 | 86,933 | +0.88 % |
| 2025 | **35** | **143,828** | **+1.35 %** |

2025 carries **1.5–1.7× the outage mass of either earlier year** and the largest
λ drift. The sign chain is exactly the caiso-121 §0 signature: outages remove
CAISO thermal capability → **gas down** (CC_REGULAR −1.24 %) → **imports up**
(+0.93 %) → **λ up** (+1.35 %) → C3a-2025 breaches the +10 % band.

## §5 — verdict (rule 1 / rule 14): CORRECT BEHAVIOUR, STALE KEEPER

Measured CAMPD unit-outage windows are the canonical rule-13-admissible
physical-availability input — CLAUDE.md names "CAMPD outage windows" as a
legitimate backcast overlay, and they satisfy the rule-13 test (a physical
availability event, reproducible for a forward year, responsive to changed
conditions). Their arrival is **more accurate data replacing a silent absence**.

Rule 14 `[R-ACCURATE]` is directly on point: *"If swapping a hand estimate for
real data (… actual outages …) makes the backcast worse, that is a signal that
something else in the model is miscalibrated … Treat the worse fit as a
discovered bug: keep the accurate input, find and fix the real root cause. Do
not bury the error back inside an inaccurate input."* Rule 1 `[R-STRUCT]`
forbids rejecting the mechanism because the residual moved.

Therefore:

- **The outage extract stays.** No revert, no gating-off, no pin to the
  keeper-era data state.
- **The keeper's C3a-2025 PASS is retired.** It was a property of a missing
  input, not of the recipe. The honest post-overlay number is the measured one.
- **The C3a-2025 breach becomes an open root-cause item**, and it points at
  ground caiso-120/121 already broke: outages push CAISO short, the model
  covers short positions with **imports priced $7–14 above the hub**, which is
  precisely the surplus-regime corridor/export defect (caiso-121 §2: 59–101 %
  of the belly wedge is DSW→CA congestion rent). The outage overlay did not
  create that defect — it **loaded** it.
