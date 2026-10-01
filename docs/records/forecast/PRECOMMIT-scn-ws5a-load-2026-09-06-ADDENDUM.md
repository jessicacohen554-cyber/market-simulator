# ADDENDUM to PRECOMMIT SCN-WS5A-LOAD — pin re-audit and FREEZE

**Date** 2026-09-06 · **Written before the first solve** (0 of 16 legs solved at write time) ·
**Supersedes only the PRECOMMIT's `Pin` line**; §2 (G-DRIFT), §3 (phase 0), §4 (the reading),
§5 (predictions), §6 (STOP gate) are **unchanged and re-verified**, not revised.

## 1. Why this exists

`main` advanced **20 commits** between the PRECOMMIT's pin (`821c11c5`, merged as `2093456e`)
and this addendum, and unlike the previous refresh **three of them touch the solve path**
(+420 / −8 across 9 files). A campaign's legs must all be solved at ONE base — that is the
whole lesson of §2's G-DRIFT audit — so the base is chosen once, now, before any LP, and
then frozen.

## 2. The re-audit — every new solve-path hunk is INERT for a forecast leg

`git diff 2093456e origin/main -- src/market_sim scripts/run_ces_leg.py
scripts/run_full_horizon.py scripts/lib configs/`

| lane | files | verdict | why INERT |
|---|---|---|---|
| **capx D67** (PJM published-requirement gate) | `capacity_market.py` +156 (new), `scenarios.py` +118, `retirements.py` +60, `run_full_horizon.py` +41, `constants.py` +1 | **INERT** | Gated on the new `capacity_adequacy_requirement_published_by_iso: dict[str,bool] \| None = None`. Verified **not armed in any ISO's `default_scenario_overrides`** (`grep` over `iso_configs.py` at the new pin returns nothing), and this campaign's cases override only `demand_growth_path` / `datacenter_load_path`. Unlike D57, which *was* armed for PJM, this one ships unarmed. |
| **nyiso-198** (`cc_duct_peaking_row_scoped`) | `campd_bins.py` +33 | **INERT** | `cc_duct_peaking_row_scoped: bool = False`; the refactor keeps the prior numerator when off, and the docstring states it verbatim: *"Off by default and byte-inert while off."* |
| **caiso-254** (class-partition repair) | `offer_curves.py`, `assembly.py`, `backcast_config.py` | **INERT** | A backcast-calibration repair; the lane's own commit records its ST_GAS half as *"provably inert in the LP"*. `backcast_config.py` is not on a `mode="forecast"` path. |

**No LIVE hunk ⇒ no control solve is earned** (rule 29(b)), and the choice of base is
physically a no-op on the forecast path. It is taken anyway so the campaign's recorded pin is
its real one.

## 3. Phase 0 re-verified at the new pin — bit-for-bit

Re-ran the §3 census through `matrix_configs` at `1cc45bb2`. Every number is **identical**:

| ISO | max abs(LOAD-HI − LOAD-HI-ORGANIC) block MW | arm |
|---|---|---|
| ERCOT | 50,421.0 | spend |
| CAISO | 2,618.0 | **spend** (WS-4b's `high := mid` still superseded) |
| MISO | 7,067.0 | spend |
| NYISO | 851.0 | spend |
| PJM | 0.0 | degenerate |
| NEISO | 0.0 | degenerate |

So the 16-leg list, prediction **P-1** (ERCOT stays in the relocate regime) and predictions
**P-2 – P-6** all stand exactly as pre-registered.

## 4. THE FREEZE

**Every one of the 16 legs is solved at `1cc45bb2` and the pin is not moved again.** `main` is
advancing at roughly 20 commits/hour on other lanes; chasing it would mean never solving, and
worse, would risk legs at differing bases — the exact defect §2 exists to prevent. Anything
landing after this SHA is **recorded in the FINDING as post-freeze**, never retro-fitted into
the campaign and never used to re-read a result.

---

## 5. Post-hoc integrity check — the legs record SIX different shas, and that is not drift

Written after the first eight legs, before the campaign completed. Recorded here rather than
in a FINDING because it is a statement about §4's FREEZE, and a reviewer reading the committed
`run_config.json` files would otherwise reasonably suspect the campaign drifted.

Each leg stamps `git.sha` at **its own start time**, and this lane commits its docs, sidecars
and slim artifacts *while later legs are still solving*. So the eight legs solved so far
record six distinct shas — `20f9ce9f`, `73c109cb`, `1ffd11b7`, `29b1c757`, `e10efc05`,
`e15f61b5` — none of which is the declared pin `1cc45bb2` itself.

**Verified, for every one of them:**

| check | result |
|---|---|
| `git merge-base --is-ancestor 1cc45bb2 <sha>` | **yes** for all six — every leg is a descendant of the frozen pin |
| `git diff 1cc45bb2 <sha> -- src/market_sim scripts/run_ces_leg.py scripts/run_full_horizon.py scripts/lib configs/` | **0 lines** for all six |
| `git.dirty` | **False** on every leg |

So every leg solved on a **byte-identical solve path**, and the recorded shas differ only by
this lane's own docs/artifact commits. The FREEZE holds in substance; what varies is the
bookmark, not the code.

Also verified at the same time, since `set_overrides` reads `{}` on every leg and could be
mistaken for "the case never applied": the campaign's case overrides ride
`matrix_configs`, **not** `--set`, so they are baked into the resolved config rather than
recorded as CLI overrides. Confirmed in the committed configs — `LOAD-HI` resolves
`demand_growth_path=high` + `datacenter_load_path=high`, `LOAD-HI-ORGANIC` resolves
`high` + `mid`, and `electrification_path=off` in every arm, which is exactly the committed
matrix and exactly what SCN-WS4b states the cases are.
