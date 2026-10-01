# RESULT — NYISO-NEXT-6: Long Island seam posted-limit sub-clip; promoted — 2026-09-27

**Session:** NYISO-NEXT-6 (orchestrator; no LP in this container, rule 32 (a)).
**PRECOMMIT:** `docs/records/nyiso/PRECOMMIT-nyiso-next5-li-tie-posted-limit-2026-09-27.md` §6–§7, plus its §9
addendum (G-DRIFT and zero-LP G-1), written before any solve.
**Arm pin:** `671fa815d40aa57a8a18232994fe6176d1daea35`.
**New keeper:** `2026-09-27-nyisonext6-li-cap-span` (bundle `results/calibration/nyisonext6_span`, 2022–2025).
**Stamped held-out run:** `2026-09-27-nyisonext6-li-cap-2021` (bundle `results/calibration/nyisonext6_2021`).
**Superseded and pruned (rule 35):** `2026-09-26-nyisonext3-tranche-basis-span` and its stamped 2021 run.

## 1. Headline

- **One new field, zero free parameters:** `nyiso_li_seam_posted_limit_cap`. Each hour, the Long Island
  import cap = min(envelope, posted import limit of Neptune + CSC + 1385). Backcast only, NYISO only.
  It never raises a cap and never touches another link.
- **Wiring correction to the brief.** The keeper arms `nyiso_seam_par_attribution`, which supersedes
  `nyiso_seam_envelope.py`. A clip placed only inside `seam_envelope_by_zone` would never have run.
  The clip is therefore applied in `run_year` after whichever envelope is armed. The two envelope
  paths give byte-identical LI caps in all five years.
- **Promoted on structure** (PRECOMMIT §7: G-1, G-2 and G-3 pass). The owner's pre-ruling applies:
  *"If structural integrity improves but gates regress that may still be a keeper."*
- **Determination unchanged:** span NOT-YET (C3a 2022 −11.5 %, 2025 −10.9 %; C3c not lone). 2021
  CALIBRATED.

## 2. Gates (arm vs the keeper's committed bundle, form 4)

Record: `results/phase0/nyiso/_nyisonext6_gates.json`, `results/phase0/nyiso/_nyisonext6_compare_span.txt`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** hours cut / TWh removed | 860 / 0.160 | 1,468 / 0.343 | 1,688 / 0.268 | 969 / 0.269 | 1,734 / 0.308 |
| G-1 vs §4 | exact | exact | exact | +1 h / −0.001 TWh ¹ | exact |
| **G-2** LI load-weighted price Δ ($/MWh) | +0.10 | +0.32 | +0.22 | +0.07 | +0.12 |
| **G-3** max \|Δ class\| (TWh) | 0.09 | 0.20 | 0.07 | 0.02 | 0.04 |
| G-3 Δ total energy (TWh) | +0.002 | +0.018 | +0.008 | +0.011 | +0.009 |
| G-3 determination change | none | none | none | none | none |
| **G-4** C3a (keeper → arm) | −6.5 → −6.6 % | **−10.8 → −11.5 %** | −2.6 → −2.6 % | −1.0 → −1.0 % | −10.9 → −10.9 % |
| G-4 system load-weighted price Δ ($/MWh) | −0.05 | −0.53 | +0.00 | −0.00 | −0.00 |

¹ The NEXT-5 probe indexed hours from 1 Jan without dropping Feb 29, so its 2024 limit and cap
arrays were a day apart after 28 Feb. The clip uses the model's non-leap clock. See addendum §9.2.

- G-1 was verified two ways: each shard's hard stop required the log line, and the parent rebuilt it
  at zero LP from each leg's own recorded config. No other link moved in any year.
- D-4 unit-conduct FAIL rows are identical to the keeper's in every year: 2480 in all years, plus
  54574 in 2022/2024, 8906 in 2024 and 8006 in 2025.
- C1, C2, C3b, C4, C6 and C8 PASS every scored year; C3b moves by 0.001 or less.

## 3. G-4 investigated: why 2022 moves the wrong way

- G-4 expected [0, +0.4] $/MWh. 2022 moves −0.53, so it was investigated as a defect.
- **It is not the clip.** Long Island rises in every year, as G-2 requires, and downstate zones rise
  +0.23 to +0.26 in 2022.
- **It is the topology.** Upstate_West falls −2.02 $/MWh (load-weighted) across ~3,000 hours of 2022,
  and the NYISO_external node falls with it. Every NYISO seam sits on one external star node, so
  import that Long Island can no longer take is re-sold to Upstate_West over the same node's supply
  ladder. Physically, Neptune's and CSC's PJM and ISO-NE supply cannot reach Zone A that way.
- The clip is correct locally. It exposes that a single external node lets import move freely
  between neighbours. That is routed to the next lane (§5).

## 4. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `07c1450c3fcfc452833e9f97e87afc5cd11c9ece` | 17 |
| 2022 | `d3554b099d504456c2ce9f7096853252c5b25f4a` | 17 |
| 2023 | `5f5362d232e6913a612b0a8a9191bfa89db068e2` | 17 |
| 2024 | `c0adf74aefb3459f7514c0dc6538ff949fe328f6` | 17 |
| 2025 | `23766db14d36f7e833e724b800a12635cf2d8b11` | 17 |

- Every leg passed S0–S2 (pin, keeper flags + the new field, offer block, NEXT-3 input sha256s).
- The legs carry no `solve.log`, because the shard prompt didn't ask for one. G-1 was re-verified at
  zero LP instead (`scripts/probes/nyisonext6_compose_span.py --no-log`).
- 2022–2025 were composed at zero LP, then the benchmark was rebuilt and legitimacy regenerated.
  2021 had its shared inputs restored, hash-verified.
- All five shards are archived.
- Retrievability: the registered keeper bundle and the 2021 bundle land on `main` with this PR. The
  per-year legs are gitignored (rule 32 (d)).

## 5. What remains, and the next lane

1. **C3a 2022 / 2025** (−11.5 / −10.9 %). This lever was bounded ex ante at about 2 % of the miss.
   It closes none of it, and 2022 moved 0.7 pp the wrong way through §3's star-node leak.
2. **The external star node.** Import capacity moves freely between Long Island / NYC (PJM and ISO-NE
   DC ties) and Upstate_West (IESO, HQ and the PJM AC tie). A per-neighbour external split is the
   structural object. The P-32 rows are already attributed per neighbour (`SEAM_ROW_ZONE`); only
   `SCH - PJ - NY` needs the PAR split, and the PAR attribution already carries it.
3. **Leftover branch:** `claude/nyiso-next5-li-tie-gap` is fully on `main`. The owner can delete it.
