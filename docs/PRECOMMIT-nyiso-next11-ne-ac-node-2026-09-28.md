# PRECOMMIT — NYISO-NEXT-11: the NE AC tie as its own two-way node

Written and committed **before any solve**. Phase 0 is zero LP. Owner ruling Q-a (2026-09-28) chose this scope after seeing NEXT-10's phase 0, so the gates below are fresh and the promotion is on structure only (rule 1), never on C3a.

- **Probe:** `scripts/probes/nyisonext11_ne_ac_node_phase0.py` → `results/calibration/_nyisonext11_phase0.json`.
- **Producer:** `scripts/data/derive_nyiso_ne_ac_ladder.py` (the two committed tables).
- **Keeper (control):** `2026-09-28-nyisonext9-hq-floor-span` (2022–2025) + stamped `2026-09-28-nyisonext9-hq-floor-2021`, basis `7900ac51`.

## 1. The object

- The pooled `NYISO_external` node cannot hold NE's measured net **export** and HQ/IESO's import at once. So `Capital_Hudson` imports at its cap where NYISO's own schedule exports (NEXT-7 §2: excess +4.65 / +4.00 / +3.80 / +2.79 / +2.33 TWh, 2021–2025).
- NE AC is the one seam whose hourly flow follows its **own** spread (CAPITL DA − ISO-NE Roseton DA): Spearman +0.43 / +0.24 / +0.27 / +0.40 / +0.40, against −0.25 to −0.36 on the NY price (NEXT-10 §2, S1–S3 pass).
- The measured tie is **interior**: it sits at a posted limit in 0–4 h/yr. So the flow is set by the spread, not by the rating.

## 2. Construction (flag `nyiso_ne_ac_node`, default off, NYISO, backcast only)

| piece | what | source |
|---|---|---|
| node | zone `NYISO_NE_AC` (zero load), **one** link to `Capital_Hudson` | Gold Book landing (F-G), `SEAM_ROW_ZONE` |
| link bounds | hourly **posted** import limit (forward) and −negative limit (reverse), P-32 `SCH - NE - NY` | measured rating under outage (rule 13, outage-window class) |
| bands | 8 import + 8 export, sized on the year's **median** posted limit (1,400 / 1,600 MW every year) | `SEAM_FLOW_TRANCHES` (existing constant) |
| price | band k = Roseton DA(t) + offset_k | `seam-neighbour-price` clean datatype |
| offsets | PJM neighbour-hourly Q-Q coupling (`_derive_one_spread`) transferred **in kind** (rule 25), on NYISO's own tie flow vs its own spread; no-wash clamp (0 fired) | `NYISO_NE_AC_LADDER_BY_YEAR` |
| pooled ladder | incumbent formula (`derive_nyiso_import_tranches.derive`) on net import **without** the NE row | `NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR` |
| pooled Capital_Hudson envelope | PAR attribution with the NE row excluded (PJM-Ramapo share only) | `nyiso_par_attributed_ttc_hourly(exclude_rows=)` |
| pooled hub repricing | NEISO excluded: `ISONE_tie` keeps its ladder price; scarcity / export use PJM only | `inject_nyiso_import_hub_prices(exclude_neighbours=)` |
| P1 bridge | the node's sinks keep their range; the pooled sink does **not** | `_bridge_floored_fleet(preserve_absorption=<mask>)` |
| reconciliation band | unchanged; the node's rows join it (the band is NYISO's **total** net interchange, which includes NE) | `build_import_node_reconciliation` |

**Rule 19, counted once.** The NE row leaves every pooled object: ladder, Capital_Hudson envelope and hub repricing. It enters the model only on its node.

**Why the P1 sink exemption is scoped to the node.** NYISO's gas bridge composes a zero floor that pins every `pmin<0` row to 0 in P1 (the caiso-138 §D defect). Without the exemption the node could not export in the scored pass. Reviving the **pooled** sink is refused. The keeper's `NYISO_external` price sits below PJM − $1 in 6,862 / 7,425 / 3,672 / 1,229 / 1,102 h (2021–2025), so a revived pooled sink would buy cheap static rungs and resell to the sink: a phantom wheel. The node cannot do this: every export offset is below every import offset, and it hosts nothing else.

**Forward story (rule 13).** In a forecast the anchor would be a modeled ISO-NE price at Roseton (the NEISO model), or the reference-price formula; the offsets are the structural Q-Q ladder. That anchor is **not wired**: `get_interchange_spec` refuses the flag outside a backcast rather than serving an unpriced node.

## 3. DOF ledger (rule 21): 0 free parameters

| item | class | identification |
|---|---|---|
| 16 offsets / year | derived | frozen Q-Q formula on measured flow + spread |
| pooled ladder / year | derived | incumbent frozen formula, one input row removed |
| link bounds | measured | P-32 posted limits |
| band count 8 | existing structural constant | `SEAM_FLOW_TRANCHES`, shared with every priced seam |
| band size = median posted limit | declared construction choice, fixed here | a statistic of a measured rating; not swept, no residual reaches it |
| sink exemption scope = the node | structural | the no-wash property (§2) |

## 4. Footprint (zero LP, first order: keeper prices, no feedback)

| year | measured NE TWh | measured-driven bands TWh (ρ) | model-driven bands TWh | h at import / export cap | pooled CH import env, keeper → arm (MW) | pooled CH import added (TWh) | CH net external change (TWh) | NEXT-7 excess (TWh) |
|---|---|---|---|---|---|---|---|---|
| 2021 | −5.17 | −4.94 (0.46) | −3.41 | 112 / 731 | 236 → 487 | +2.20 | −1.22 | +4.65 |
| 2022 | −3.51 | −3.41 (0.24) | −4.44 | 40 / 991 | 280 → 465 | +1.62 | −2.81 | +4.00 |
| 2023 | −4.47 | −4.44 (0.27) | −4.05 | 1 / 663 | 406 → 596 | +1.43 | −2.62 | +3.80 |
| 2024 | −5.84 | −5.78 (0.41) | −3.40 | 166 / 822 | 369 → 680 | +2.43 | −0.97 | +2.79 |
| 2025 | −5.76 | −5.65 (0.40) | −5.70 | 9 / 889 | 464 → 722 | +1.75 | −3.94 | +2.33 |

- **The pooled Capital_Hudson envelope rises.** With NE's exports out of the netted attribution, the link carries PJM-Ramapo alone, whose p90 import is larger. That partly offsets the node's exports. The last column is the net first-order move.
- **Pooled ladder, net import mean** without NE: 3,697 / 3,480 / 3,057 / 3,026 / 2,854 MW (was 3,108 / 3,080 / 2,546 / 2,360 / 2,197). The re-derived rungs are cheaper at each depth (2025 `ISONE_tie` 153.51 → 93.04).
- **Stated risk.** Driven by the keeper's Capital_Hudson price, the bands sit at full export depth in 663–991 h. The measured tie almost never does. This is the keeper's Capital_Hudson under-pricing (C3a −11 %) showing through, and it is first order.
- **Integration check (zero LP, real inputs, 2021 and 2025).** Off-arm link caps reproduce the keeper (Capital_Hudson 235.7 MW). With the arm, the pooled Capital_Hudson export envelope falls 718 → 20 MW (2021) and 656 → 7 MW (2025); the node link carries 1,247 / 1,496 MW (2021) mean posted import / export limits.

## 5. G-DRIFT (keeper basis `7900ac51` → pin)

See §9 (appended before the pin, from the audit of every changed hunk).

## 6. Gates (fixed now; arm vs the keeper's committed bundles, form 4)

- **G-1 leg acceptance** (shard hard stop + parent check), each of 2021–2025:
  - solved at the pinned SHA;
  - `scenario_config` equals the keeper's except `nyiso_ne_ac_node: true`, plus `nyiso_firm_imports` absent (rule-26 retired, recorded `false` in the keeper, hash-inert);
  - the leg log carries `nyiso_ne_ac_node — 16 NE AC bands priced`;
  - `dispatch/<y>_P1.parquet` carries exactly 16 `NYISO_NE_AC_*` rows.
- **G-2 structure.**
  - **(a) Two-way and live.** In P1 the node exports (sum of its sink rows < 0) in ≥ 1 h **and** imports in ≥ 1 h, every year. If the node never exports, the sink exemption failed: not promoted, investigated.
  - **(b) Counted once.** Parent zero-LP reconstruction at the pin: the leg's pooled ladder equals `NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR[y]` and the pooled Capital_Hudson envelope excludes the NE row (§4 integration check, repeated for all five years).
  - **(c) The monthly band holds.** |Δ annual net import TWh| (class `import`, all rows) ≤ 4 % of the keeper's in every year (two ±2 % band half-widths).
- **G-3 protective.** C6 and C8 PASS every year. The D-4 FAIL row set is reported against the keeper's.
- **G-4 reported, NOT a criterion:** C1, C2, C3a, C3b, C3c per year and the determination; Δ load-weighted price per zone; the node's net TWh against the measured tie; the Capital_Hudson net external flow against NEXT-7's excess; hours the node sits at a posted bound.

## 7. Promotion rule (ex ante)

- **Promote iff G-1 is exact in all five legs, G-2 (a), (b), (c) hold, and G-3 holds.**
- The basis is rules 14 and 19: a seam the pooled node mis-locates is represented where it physically lands, at its own measured price and posted rating, with zero free parameters.
- C3a moving in either direction neither promotes nor blocks (rule 1).
- If G-3 fails, the response is investigated and the owner is asked (rule 31).
- **Year set.** The union of `years` over the NYISO sidecars is {2021, 2022, 2023, 2024, 2025}. All five are solved, one shard per year (rules 34 (c), 35 (b), 36).

## 8. Solve plan

- One shard per year, pinned to a full 40-character SHA **on `main`** after this PRECOMMIT and the code merge.
- Arm: `replay_keeper.py results/calibration/nyisonext9_span --years <y> --out-dir results/calibration/nyisonext11_<y> --set nyiso_ne_ac_node=true` (2021 from `results/calibration/nyisonext9_2021`).
- Each shard pushes its full bundle, `dispatch/<y>_P1.parquet` included (rule 34 (a)).
- Parent: compose, gates, benchmark rebuild, legitimacy diagnostics, attestation, registration; promotion per §7.
