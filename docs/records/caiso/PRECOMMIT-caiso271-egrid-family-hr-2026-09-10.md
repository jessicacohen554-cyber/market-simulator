# PRECOMMIT — caiso-271: eGRID prime-mover-FAMILY heat rates for CAISO, and the honest answer on the rubric

**Session caiso-271, 2026-09-10. Branch `claude/caiso271-lowgas-belly`. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
Keeper: **`2026-09-10-caiso-269-lateevening-clean`**, **CALIBRATED**, single ledgered C3c. Its bundle is
committed again (caiso-270), so **G-CTRL form 4 differences against it with NO control solve.**
Arm: **`ScenarioConfig.egrid_family_heat_rates`**, default off, matrix cell **U (untested for CAISO)**.
**Pushed before the first LP of any shard.**

---

## §0 — READ THIS FIRST: THIS ARM IS **NOT** A RUBRIC-CLOSING LEVER, AND I FOUND NONE

The session was asked for an LP with potential to close CAISO's open rubric failure (2022 C3a **+12.90 %**
against ≤ +10, C3b **0.2402**). Closing it needs **−2.45 $/MWh** of load-weighted 2022 price.
**Phase 0 could not find a groundable lever that reaches that, and this arm is not one.** Its direction is
against the residual and its predicted price effect is small. It is launched on **rule 14 `[R-ACCURATE]`**
(measured over a blended estimate) and on the owner's standing ruling that *"if structural integrity
improves but gates regress that may still be a keeper"* — not on a claim it will close anything.

**Every registered candidate, checked and why each is dead** (rule 28(a) DO-NOT-REDO honoured throughout):

| candidate | status | measured reason |
|---|---|---|
| negative renewable / dump floor family | **KILLED** by caiso-266 | floor-regime hours carry −0.287/+0.102/−0.129 $/MWh of the annual gaps; the residual is **thermal-marginal** |
| import price ladder, hub level | **~inert** (caiso-269) | imports already price at the **measured** MALIN/PALOVRDE nodal LMP + real wheel + CARB border carbon |
| corridor ATC percentile | **refused** | free parameter; sweeping it is rule 1 `[R-STRUCT]` fitted selection |
| `cc_steam_part_capacity` | **too small** | CAISO footprint is **20 MW at one plant** (54912 Martinez STG1), per the cell's own handoff note |
| CT_PEAKER volume | **closed** | owner ruling caiso-261, declared permanent residual |
| `reference_price_interface` | **unavailable** | gated to `INTERFACE_NEIGHBORS` (PJM only) |
| `cc_committed_hr_mult` / `cc_econ_hr_mult` | **frozen + cross-ISO** | measured from OEM IO curves + CEMS; shared by every ISO, so rules 23 `[R-FROZEN-DERIVE]` and 25 both bar this lane |
| `offer_curve_by_group` band multipliers | **not exercised** | the authorized channel exists, but caiso-267/268's arms were owner-**refused**, and selecting a factor that makes a criterion pass is exactly what rule 1 condition (c) forbids |

**What phase 0 did establish, as measurement:** the residual is thermal-marginal and broad. In the hours
where the CC econ stack reaches its deepest band (`econc05` active — **6,924 h, 81.8 % of 2022 load**) the
model carries **+6.63 of the +9.32 $/MWh** annual gap, at implied marginal heat rate **10.33 vs 9.52
actual**. It is **not** a CC capacity constraint: CC runs at **55.2 % of its own annual max** in those hours
and clears 95 % of max in only 315 of them. And CT_PEAKER is **under**-run (model 3.047 TWh vs 4.479
actual), so the model is not simply over-using peakers. **The object is a broad ~1 heat-rate-point
marginal-unit bias with no single registered mechanism behind it**, which is what
`FINDING-caiso270` §4 already named and what a successor lane must charter properly.

## §1 — THE LEVER, AND ITS EXTERNAL DRIVER NAMED BEFORE ANY NUMBER

**Driver.** The fleet's heat rate is joined from eGRID at **PLANT** grain
(`process_eia860._join_egrid_heat_rate` reads `PLNT<yy>.PLHTRT`). A plant hosting two or more prime-mover
families — a 1960s steam station beside a modern combined cycle — therefore hands **both halves one
generation-weighted blend**, which is a measured number for neither of them. eGRID publishes the per-family
inputs in the **same vintage the join already reads** (`UNT<yy>.HTIAN`, `GEN<yy>.GENNTAN`), so the family
rate is arithmetic on published fields. **Rule 14 `[R-ACCURATE]`: a measured per-family rate beats a blend.**

**Forward story (rule 13 `[R-MEASURED]`).** The identical construction regenerates from any eGRID vintage
and re-classifies a plant whose families change. **Zero free parameters** (rules 21/24) — no threshold, no
scalar, no per-plant carve; admission is a population rule (≥ 2 live families, each with heat input and net
generation > 0, inside the join's own 3,000–30,000 Btu/kWh window). **Rule 19 `[R-ONE-MECH]`:** applied at
the eGRID-input seam so every class-scoped measured mechanism keeps its precedence, and the hand number
`fleet.models.MIXED_FACILITY_STEAM_HR` is **SKIPPED** at covered plants rather than stacked — so this also
retires an off-registry hand value (rule 24 `[R-REGISTRY]`).

**The CAISO artifact is derived in this commit** (rule 25: each ISO derives from its own market's data),
`scripts/data/derive_egrid_family_heat_rates.py --iso CAISO` →
`data/raw/_processed-legacy/egrid_family_heat_rates_CAISO.csv` (+ `_vintages.csv`): **8 (plant, family) rows
over 4 covered plants, vintage 2023.**

## §2 — PRE-SOLVE FOOTPRINT, MEASURED, INCLUDING THE PART AGAINST THE ARM

Fleet rebuild, **zero LP**, control vs arm. **6 units, 1,451.8 MW, 4.54 % of the 31,979 MW CAISO fleet:**

| unit | plant | name | fuel | MW | HR control | HR arm | ΔHR |
|---|--:|---|---|--:|--:|--:|--:|
| 315_5 | 315 | AES Alamitos | gas_st | 480.0 | 11.850 | 14.138 | **+2.288** |
| 315_4 | 315 | AES Alamitos | gas_st | 335.0 | 11.850 | 14.138 | **+2.288** |
| 315_3 | 315 | AES Alamitos | gas_st | 327.0 | 11.850 | 14.138 | **+2.288** |
| 335_2 | 335 | AES Huntington Beach | gas_st | 225.8 | 11.850 | 11.494 | −0.356 |
| 422_GT5 | 422 | Glenarm | gas_cc | 68.0 | 10.390 | 9.029 | −1.361 |
| 422_ST1 | 422 | Glenarm | gas_cc | 16.0 | 10.390 | 9.029 | −1.361 |

**DEARER 1,142.0 MW; CHEAPER 309.8 MW; capacity-weighted ΔHR +1.666 MMBtu/MWh.**
**THE DIRECTION IS AGAINST THE RESIDUAL AND THAT IS STATED BEFORE THE SOLVE**, not after it. Rule 1
`[R-STRUCT]` is explicit that a structurally-correct mechanism is never judged by whether it improves the
fit, and rule 14 is explicit that a worse fit from an accurate input is a signal to look elsewhere for the
root cause — which §0 does.

**Vintage stability** (rule 23 `[R-FROZEN-DERIVE]` / rule 13): the CC families — the halves that matter for
merit order — are stable across vintages (315 CC 7.244 → 6.980; 335 CC 7.098 → 6.954, 2023 → 2024). The ST
families move more (16.184 / 12.982 in 2024), which is the collapsing-steam signature the mechanism exists
to expose.

## §3 — SCREEN YEAR, NAMED BEFORE THE SCREEN (rule 29 `[R-SCREEN]` clause d)

**2022** — the year the affected class's **own measured footprint is largest**, not the year with the
biggest residual: model ST_GAS energy **0.3814 TWh** (max 3,872 MW, 1,735 h > 0) against 0.1187 (2023),
0.1871 (2024) and 0.0223 TWh (2025). The 1,142 MW of dearer capacity is ST_GAS, so 2022 is where the
mechanism is most live. Rule 16 `[R-ALLYEARS]` is satisfied by solving all four years as four parallel
shards, so the screen and the span are the same spend.

## §4 — PREDICTIONS, PRE-REGISTERED

**P1.** ST_GAS energy **FALLS** in every year — 1,142 MW of it is repriced +2.288 MMBtu/MWh dearer.
**P2.** The price effect is **SMALL**: ST_GAS averages **55 MW** in the 2022 residual hours and 0.02–0.38
TWh a year, so the repriced block is rarely marginal. I predict **|ΔC3a| < 0.5 pp in every year**, and
**2022 C3a stays FAIL** (it needs −2.45 $/MWh; nothing here supplies that).
**P3.** Glenarm's 84 MW of gas_cc gets cheaper, which is a rounding-level effect on an 16.4 GW CC fleet.
**P4 — THE EXPOSURE, STATED IN ADVANCE.** C1 ST_GAS is a **small class** (< 2 % of CAISO load), so rule 18
`[R-FORCED-BUDGET]`'s materiality floor keeps it un-gated; but C2 (system volume, gas family) and C4 (gas
hourly fit) are load-bearing/supporting and **can** move. If a load-bearing criterion flips PASS → FAIL,
G-NOFLIP kills the arm and it is not promoted.
**P5.** C3c may move and is exempt from G-NOFLIP (rubric v3.6); reported at full magnitude either way.

## §5 — GATES. ALL STOP-ONLY. NONE READS THE TARGET RESIDUAL

| gate | pre-registered condition |
|---|---|
| **G-IDENT** | the ONLY differing `ScenarioConfig` field is `egrid_family_heat_rates` — **verified pre-solve on the keeper's own recorded config** |
| **G-FOOT** | exactly the **6 units / 1,451.8 MW** of §2 change heat rate; no other fleet row moves, and the unit-id list is otherwise identical |
| **G-DIR** | the three Alamitos ST rows' offers **RISE** and the Glenarm rows' **FALL**, in the ratio the ΔHR table implies; ST_GAS energy falls |
| **G-NOFLIP** | no non-target load-bearing criterion (C1, C2, C3a, C3b, C6, C8) flips PASS → FAIL. C3c exempt |
| **G-CTRL** | **form 4** — the committed keeper bundle `results/calibration/caiso269_lateevening_span` (+ `caiso269_lateevening_2022`) is the control. **NO CONTROL SOLVE.** |

A gate may KILL this arm; none may promote it.

## §6 — G-DRIFT (rule 29(b)) AND THE TWO MANDATORY ZERO-LP CHECKS

* **G-DRIFT.** caiso-270 audited the keeper's arm SHA → HEAD and classified every hunk INERT for CAISO, then
  **confirmed it by measurement**: the four-year re-solve reproduced the published C3a to
  0.0006/0.0009/0.0041/0.0000 pp and C3b to 0.0000. Form 4 is valid on measurement, not just on reading.
* **BIND CHECK (verified).** Applying the keeper's fully-resolved recorded config with the flag yields
  **exactly ONE differing `ScenarioConfig` field**, `egrid_family_heat_rates`, and the fleet diff is the §2
  table — so the flag reaches the fleet, not just the config.
* **PARTITION CHECK (verified, the caiso-270 lesson).** `check_clean_partitions(cfg, "CAISO", strict=True)`
  passes after `PYTHONPATH=.:src python3.11 scripts/data/curate_capacity_deliverability.py`, and the seam
  import cap resolves `source='mic_partition'` (2022 `cap_mw` 15780.0). `data/clean/` is derived and
  gitignored, so **every shard must build it before solving** or the strict guard is fatal by design.

## §7 — SHARD PLAN (rule 32 `[R-SHARD]`). THE PARENT NEVER SOLVES

| shard | year | branch | out-dir |
|---|--:|---|---|
| Y2022 | 2022 | `claude/caiso271-family-2022` | `results/calibration/caiso271_family_2022/` |
| Y2023 | 2023 | `claude/caiso271-family-2023` | `results/calibration/caiso271_family_2023/` |
| Y2024 | 2024 | `claude/caiso271-family-2024` | `results/calibration/caiso271_family_2024/` |
| Y2025 | 2025 | `claude/caiso271-family-2025` | `results/calibration/caiso271_family_2025/` |

`results/calibration/caiso271_family_*/` is **added to `.gitignore` in THIS commit** so an auto-merged shard
branch cannot put a per-year bundle on `main` — the caiso-270 incident (373.3 MB across 60 files, including
184.8 MB of `dispatch/`) that cost a follow-up un-merge.

## §8 — WHAT IS NOT DONE HERE

No offer-curve multiplier of any size (rules 1/13 carve-out **not** exercised; no `authorized_price_tuning`
block). No adder, offset, haircut, load proxy or pin to actuals. No corridor-percentile sweep. No re-opening
of the CT_PEAKER volume residual, the renewable floor family, or the import ladder. No other ISO's keeper
shard, matrix shard, status part or calibration log is touched. `egrid_identity_heat_rates` and
`egrid_steam_collapse_heat_rates` are **not** armed — their derives are `--iso NYISO`-scoped at HEAD and
extending them is a separate lane's work (rule 19: one mechanism at a time).
