# PRE-REGISTRATION — neiso-99: the legacy-P2 scoring basis and the Stony Brook outage routing

**Date:** 2026-08-17 · **Session:** neiso-99 · **Branch:** `claude/neiso-99-p2-basis-routing-f8asmp`
(off `origin/main` @ `6cc332e`) · **Incumbent keeper:** `2026-08-17-neiso-97-dstrepair`

**Written and committed BEFORE either arm solved.** Both arms were launched after this file was
on disk; neither had produced a bundle when the predictions below were fixed.

---

## 1. The two defects, and why they are settled in ONE re-solve

**(a) O5 — the archived-P2 scoring basis.** NEISO is the only ISO of six whose keeper runs the
archived P2 commitment pass, and neiso-98 established by two independent routes that the
registered payload — hence every published NEISO number and the scored determination — is
**rendered from P2**. CLAUDE.md "Dispatch & Commitment" states P0/P1 are the only production
passes and that no keeper uses P2.

**(b) Stony Brook plant 6081 outage routing.** `_resolve_unit_group`'s `fac_group` short-circuit
hands a liquid-fuel combustion turbine's outage window to a sibling gas bin.

They are solved together, in one re-solve span (`--year 2023 2024 2025`, one invocation, years
sequential), because settling them separately would leave whichever went second confounded by the
other. The movement is **decomposed** by a two-arm design, below.

## 2. Arms

Both arms replay the incumbent's own `meta.json` recipe through `scripts/replay_keeper.py` with
`--set commitment=false`, i.e. the production P1 basis. They differ in exactly one input.

| arm | bundle | outage extract | isolates |
|---|---|---|---|
| **A** | `neiso99_basis_A` | the **committed** (pre-fix) `campd-unit-outages-NEISO.csv`, via a `MARKET_SIM_DATA_ROOT` shadow root | the **P2 → P1 basis change** alone; also the same-HEAD control |
| **B** | `neiso99_joint_B` | the **re-derived** (post-fix) extract | basis **+** routing |

**Routing effect = B − A. Basis effect = A − the incumbent keeper. Joint = B − keeper.**

Arm A's extract differs from arm B's, within the solve years, by **exactly the 236 mis-routed
rows and nothing else** — measured, 0 non-flagged row changes in 2023/2024/2025 (§3).

## 3. What is already measured (committed before the solves)

* **The mis-routed population, all six ISOs** — `scripts/probes/neiso99_routing_blast_radius.py`
  → `_neiso99_routing_blast_radius.json`. 35 CAMPD units filed "Combustion turbine" sit in a
  non-CT bin; **27 are gas-fired members of a genuine block** and must keep inheriting it (ERCOT
  Sand Hill SH1–SH7, Colorado Bend CT-4A/4B, CAISO Glenarm GT3/GT4, MISO Zeeland CC1/CC2, NYISO
  Ravenswood CT0001/0010/0011, Bethpage GT3, …). **8 are liquid-only** and are the mis-routed
  peakers. `unitType` alone therefore does NOT separate the populations; `primaryFuelInfo` does.
* **NEISO's four:** 6081 Stony Brook 004/005 (Diesel Oil, 83 MW each, 74 rows each), 568
  Bridgeport Harbor BHB4 (Other Oil, 11), 1588 Mystic MJ-1 (Diesel Oil, 24), 1595 Kendall S6
  (Diesel Oil, 53) — 236 rows. **Cross-ISO, filed not acted on (rule 25):** PJM 593 Edge Moor 10
  (33 rows), MISO 2001 New Ulm 7 (114) and 8056 Waterford 4 (103), NYISO 2516 Northport UGT001
  (42). Only NEISO's extract is re-derived here.
* **The derate the mis-routed rows impose** — `neiso99_routing_derate_magnitude.py` →
  `_neiso99_routing_derate_magnitude.json`, at the keeper's own `cc_steam_part_reclass=True`:

  | bin | year | capacity-year lost WITH | WITHOUT |
  |---|---|---|---|
  | 6081 CC_REGULAR | 2023 | 1.0000 | 0.9955 |
  | 6081 CC_REGULAR | **2024** | **0.4872** | **0.0000** |
  | 6081 CC_REGULAR | **2025** | **0.5600** | **0.0000** |
  | 1595 CC_CHP | 2023 | 0.1160 | 0.0192 |
  | 1595 CC_CHP | 2024 | 0.1506 | 0.0685 |
  | 1595 CC_CHP | 2025 | 0.1374 | 0.0548 |

  In 2024 and 2025 the Stony Brook CC units 001/002/003 have **no outage windows of their own** —
  the entire derate of a 305.1 MW block is imposed by two diesel peakers that are not in it.
* **Extract-diff accounting, exact** (post-fix vs committed, after re-fetching the BLOAT-S2-untracked
  CAMPD 2018 vintage): standard 3,189 → 2,932, **0 rows added**; dropped 257 = **236 the fix** +
  **21 reclassified standard → layup**, the latter in 2019/2020/2026 only. A **pre-fix control
  re-derivation at HEAD** reproduces those same 21 and drops **zero** flagged rows, so they are
  ambient HEAD drift, not this change. All 2,932 surviving rows are byte-identical on every column.
  **Within 2023–2025 the only change is the 236 rows.**

## 4. Predictions

**P1.** Arm A's `hourly/` sidecars will be **bit-identical** to the incumbent's committed **P1**
sidecars in all three years. Rationale: P2 runs *after* P1, so removing it cannot move P1. A
failure of P1 is a finding in its own right — it would mean the archived pass feeds back into the
production one.

**P2.** Arm A's scored numbers will be the incumbent's **P1** numbers, not its P2 ones — in
particular the annual maximum of the max-across-zones price **248.97 / 218.24 / 280.85** $/MWh
against the incumbent's published **249.50 / 256.93 / 280.85**. The 2024 figure moves
**−18 %**. This is a **price-formation statistic and is reported, never tuned around**.

**P3.** Arm B − arm A: Stony Brook's CC block regains a full availability year in 2024 and 2025
and Kendall recovers ~8 pp in every year, so **CC_REGULAR / CC_CHP energy rises**, oil and peaker
energy falls, and **prices fall**. 2023 is near-null at 6081 (the block is already ~fully derated
by its own units) and moves only through Kendall.

**P4 — the standing risk, declared in advance.** If NEISO's model mean LMP already sits at or
below actual, P3's downward push **degrades C3a / C3b**. **Rule 14 `[R-ACCURATE]` governs: the
routing fix is the accurate input and stays in regardless.** A degradation is a *discovered bug* —
the estimate was silently compensating for something else — and the response is a root-cause
investigation, never reverting to the inaccurate input. **Rule 1 `[R-STRUCT]`: neither arm is
judged on MAE.** A keeper that trades a gate regression for a correct scoring basis and a correct
availability envelope is still a keeper, and the regression will be shown at full magnitude.

**P5.** The C3c frontier declaration is expected to survive the P1 basis — the model tail is 0 h
> $300/MWh on **both** passes today — but this is **re-measured on the new keeper's own sidecars**,
not assumed, and the declaration is re-verified rather than carried forward.

## 5. Committed in the same change, and why it is not a third arm

`run_replay_bundle` and `replay_keeper.main` both rebuild their kwargs from a bundle's `meta.json`
**after** `_enforce_legacy_p2_gate` has run on parsed CLI args, so `commitment=true` re-armed the
archived pass invisibly on every replay — which is how it propagated across three keeper
generations with no operator decision. `enforce_legacy_p2_kwargs` now gates the **reconstructed
recipe** at both entry points and **hard-fails** rather than silently rewriting it (a silent
rewrite is the miso-50..53 lossy-reconstruction class). Verified: the incumbent bundle now refuses
to replay without either `--enable-legacy-p2` or `--set commitment=false`. It changes no solve
that does not arm P2, so it is a guard, not an arm.

## 6. Scope refusals

No C3c lever is opened (the frontier is declared; DO-NOT-REDO on every `R`/`I`/`G` cell in the
NEISO shard). **No out-of-training year is solved, scored or registered** — the holdout spend
freeze stays ACTIVE and the tier map is fail-closed. No 2022 re-iteration is requested (neiso-98
showed the DST repair cannot move that touchpoint's determination). The CAMPD 2018 re-fetch is
**data preparation**, which rule 22 as amended 2026-08-06 leaves unrestricted ("what is held out
is the SCORE, never the DATA"); 2018 is outside the working span and no solve reads it.
