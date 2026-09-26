# PRECOMMIT neiso-118 — Canal 3's 2019 heat rate: CT-derive membership repair + NEISO CT re-derive (2026-09-26)

Keeper (precondition verified): `2026-09-26-neiso-117-coal-yard`, bundle `results/calibration/neiso117_span`,
years 2019–2025. Train tier 2023–2025 CALIBRATED (C3c ledgered); full span NOT-YET on ONE line: C1 CC_REGULAR
2019 model 41.491 vs actual 43.841 TWh (−2.35, in the ±2.81 volume band), share **−3.46 pp** (band ±3).

## 1. Phase 0 (zero LP) — who carries 2019's excess

`phase0_2019_attribution.py` → `phase0_2019_attribution.json`: 2019 is rebuilt with `run_year(fleet_only=True)` on
`replay_keeper.run_year_kwargs(neiso117_span/meta.json)` and joined to the registered payload's per-plant P1 TWh
and EIA-923 net generation.

| class | model | actual | excess | who |
|---|---|---|---|---|
| CT_PEAKER | 1.633 | 0.457 | +1.18 | **1599 Canal 3: 1.242 vs 0.196**, no floor (economic); every other plant ≤ 0.16 |
| ST_GAS | 1.066 | 0.228 | +0.84 | 562 0.615 / 8002 0.255 / 1642 0.163; **0.562 TWh of it is the winter fuel-security floor** (mech 14) |
| COAL_BIT+PRB | 1.035 | 0.468 | +0.57 | 2364 / 568, fuel-bounded since neiso-117 |

**Root cause of the CT excess: an impossible heat rate.** Canal 3 (330 MW 7HA simple cycle, COD Apr 2019) carries
**3.95 MMBtu/MWh** in 2019 (econ tranches; eGRID plant rate 4.14 × tranche multipliers) — below any combustion
turbine, so its offer ($16–32/MWh) undercuts every CC and the LP baseloads it. eGRID-2019's Canal row is a boundary
mismatch: `PLHTIAN` 810,044 MMBtu = exactly the sum of CAMPD 2019 heat input over units 1+2+3 (partial year; Canal 3
reports 135 op-hours), while `PLNGENAN` 195,626 MWh is EIA-923's full-year net generation (EIA-923 2019 plant fuel
2.08 M MMBtu → ≈ 10.6). eGRID 2020/2021/2022 read 17.9 / 13.6 / 10.5.

**Why nothing caught it.** (a) The measured-CT artifact should replace eGRID for Canal 3, but
`scripts/lib/heat_rate_years.union_fleet` keeps each unit's LATEST-vintage record, and Canal 3 is `CT_PEAKER` in the
2019–2022 vintages and oil (`''`) in 2023–2025 — so it never entered the CT derive's population. The same defect drops
ST_GAS 8002 / 6156 and CC_CHP 10726 from their derives. (b) The SPP-49 simple-cycle floor (9.0) clamps only plants
whose operating rows are ALL GT/IC; Canal is mixed steam + GT.

**Deferred levers re-evaluated against this attribution:** none targets the Canal defect. (i) tranche re-derive —
reshapes offer bands, cannot move an offer priced off a 4 MMBtu/MWh base; (ii) committed measured basis — CT_PEAKER
committed 1.289 → 0.985, the wrong way (neiso-116 §4); (iii) Merrimack price — ≈ 0.02 TWh in 2019 (neiso-116 §2(d)).

## 2. Owner ruling (2026-09-26, asked before any solve)

**"CT only"**: repair the membership defect and re-derive the NEISO **CT** artifact only. ST_GAS / CC_CHP re-derives
(which the same bug affects — ST would make 8002 17.4 → 13.0 and 6156 23 → 11.5 MMBtu/MWh, i.e. MORE 2019 ST_GAS)
are the named successor, not this arm.

## 3. Change (this commit) — zero free parameters

1. `scripts/lib/heat_rate_years.union_fleet(fleets, klass=None)`: with `klass`, a unit in that class in ANY year keeps
   its latest in-class record. `None` = the old latest-record behaviour, byte-identical for every other caller
   (coal / ST / CC / CHP derives untouched). Test: `tests/curation/test_heat_rate_years_union.py` (3).
2. `scripts/data/derive_campd_ct_heat_rates.py` passes `klass=TARGET_CLASS`.
3. `data/raw/_processed-legacy/campd_ct_heat_rates_NEISO{,_units}.csv` re-derived (`--iso NEISO --detail`). Diff:
   **+6 plant rows, +1 unit row, all Canal 1599; every other row byte-identical.** Pooled net 10.7588 (gross 9.394 ×
   the committed parasitic factor 0.873); own-year rows 2020 10.68, 2021 10.76, 2022 10.89, 2024 10.70, 2025 10.77.
   No 2019 own-year row (2019's CAMPD `unitType` carries a "(Started Apr 04, 2019)" suffix and 135 hours) → 2019 reads
   the pooled row. sha256 `12306dae…` → **`f57df14e6e506dc1e06b7174510c98b6fb64aec0d0b5737baf5666cdb06dd9f9`**.
   Rule 23: re-derived because the derive's membership CODE was wrong (the corrected-fleet membership the F1 audit
   intended), never because a residual moved; other ISOs' artifacts are not re-derived (rule 25).

**LP-input diff (fleet_only rebuild, keeper recipe, old vs new artifact, all seven years):** unit ids identical; the
ONLY arrays that move are Canal 3's three tranches in 2019–2022 — econ HR 3.95 → 10.27 (2019), 17.09 → 10.20
(2020), 12.98 → 10.27 (2021), 9.98 → 10.39 (2022). **2023–2025: zero changed units** (Canal 3 is not CT_PEAKER in those
vintages).

**Price-taker estimate (keeper P1 Central LMP, offers scaled):** reproduces the keeper's 2019 Canal dispatch (1.238
vs LP 1.2425 TWh). Measured rate: 2019 **1.24 → 0.08** (actual 0.20), 2020 0.00 → 0.25 (0.18), 2021 0.14 → 0.37
(0.18), 2022 0.67 → 0.35 (0.53; LP had 0.20).

## 4. G-DRIFT (rule 29(b)) — ZERO hunks

The keeper's pins `17402f35` (2019–2024) / `d52b1d71` (2025) were rebased away; the landed commit carrying the same
solve code is `3d132124` (the 2025 floor-reconcile commit, inert 2019–2024 per neiso-117 §9).
`git diff 3d132124 HEAD -- src scripts/lib scripts/run_calibration.py scripts/run_calibration_full.py
scripts/replay_keeper.py data/raw configs` is **empty** at HEAD `91497567`. Form 4: the keeper is the control.

**Rebase window `91497567` → `a151c5b1`** (main moved before the pin): 18 files. INERT for NEISO, every hunk:
`unit_outage_netload_mask_repair` (SPP-85; `scenarios.py`, `data/fleet/arrays.py`, `data/outages.py`,
`data/resolved_inputs.py`) — new field, default False, frozen drop value `"False"`, absent from the keeper recipe, and
no NEISO `-netloadmask-` companion exists; `scripts/lib/bundle_io.py` captures those companions by name and skips an
absent file; `unit_outage_active_units(hour_grain=)` (R-ERCOT-6) — its only caller passes `iso="ERCOT"`;
`scripts/lib/outage_detect._ISO_TO_BA` gains `SPP`; data files are SOCO tranches, SPP outage companions and CAISO
demand. Form 4 stands for every year.

## 5. Recipe — declared before any solve

Every leg: `uv run python scripts/replay_keeper.py results/calibration/neiso117_span --years <Y>
--out-dir results/calibration/neiso118_<Y>` — the keeper recipe **unchanged**; the arm is the committed CT artifact at
this SHA. Offer curve byte-identical (no authorized-price-tuning change). DOF: zero new.

## 6. Gates — declared before any solve (structural; rule 1)

A passing gate does not promote and a failing one does not kill; both are reported at full magnitude.

- **G1 recipe:** `docs/handoffs/neiso118/shard_check.py` PASS on every leg (config delta `{}`, offer curve, std
  extract, CT artifact sha256 `f57df14e…`); log line `coal per-yard budget (NEISO <Y>)` present (3/3/2/2/1/1/2 yards).
- **G2 mechanism:** Canal 3 (1599 CT_PEAKER) 2019 P1 ≤ 0.30 TWh. **2023, 2024, 2025: every class TWh equal to the
  keeper's within 0.01 TWh** (identical LP inputs).
- **G3 no silent breakage:** full span and train tier re-scored with `calibration_verdict.py --run-id`; train tier
  must stay CALIBRATED for a promote recommendation.
- **Predictions:** 2019 CT_PEAKER −≈1.1 TWh; C1 CC_REGULAR 2019 share −3.46 → ≈ −2.3 pp (**PASS**) if CC absorbs
  most of it (≥ 0.45 TWh into CC is enough); 2020 / 2021 CT_PEAKER up ≤ 0.4 TWh, CC_REGULAR stays in band (headroom
  0.22 / −1.46 pp); 2022 moves ≤ 0.5 TWh either way.

## 7. Shard plan (rule 36 — one shard per year; rule 34 — full bundle pushed)

Seven shards `neiso118_<Y>`, 2019–2025 (the keeper's whole year set, rule 34(c)), pinned to this doc's commit SHA
(§8). Branch `claude/neiso118-<Y>`. Each curates `coal_stocks`, `coal_receipts`, `hydro_plant_modes --iso NEISO` before
solving. Full bundle incl. `dispatch/<Y>_P1.parquet` pushed via `.gitignore` negation + plain `git add`. Parent
composes (`docs/handoffs/neiso118/compose_span.py`), attests, registers `--no-prune`, scores; it never solves
(rule 32(a)). Per-year dirs gitignored in the parent's tree.

## 8. Launch record

All seven pinned to **`faa5bd591040e58e31a33e3c3369c1de7d4f31ea`** (this doc's commit on `a151c5b1`), created
2026-09-26 14:01 UTC, tag `neiso118`. Branch `claude/neiso118-<Y>`, out-dir `neiso118_<Y>`.

| year | shard session |
|---|---|
| 2019 | `session_01WmMzLRD35E2ektbF2KChzu` |
| 2020 | `session_01EteN82GKiDFSuPYpqb9PXv` |
| 2021 | `session_01XJnVYr7TbRhpNadnQMqz2M` |
| 2022 | `session_015k2zCro2xcGaeBC2bZAsSm` |
| 2023 | `session_014DUBDmJt9jYnXrCovsvoSv` |
| 2024 | `session_01XEFYqtCNCJ63KNYbunRNTS` |
| 2025 | `session_01RJ2fAJrxporgn694kG7svP` |

**Relaunch (14:18 UTC).** All seven first-launch shards stopped cleanly at hard stop 1: the container clone
ignored the SHA `source_revision` and landed on `main` (`a151c5b1`). Nothing solved, nothing pushed; all seven
archived. Relaunched with `source_revision` = this branch and an explicit step 0 (`git fetch origin <sha> && git
checkout --detach <sha>`); the pin and every other instruction are unchanged.

| year | shard session (v2) |
|---|---|
| 2019 | `session_01V8Mgijkrzcis5dG3Uektvo` |
| 2020 | `session_01DCWUoQ7VGrW2XSACEs3ria` |
| 2021 | `session_01Ktm8dZq1mgB3puqFhHSsu8` |
| 2022 | `session_01YVSjZWbPz8YTmRLjiR3DTt` |
| 2023 | `session_0141P1GkNf8WTv53362tNLV6` |
| 2024 | `session_01QdmHTq6ueFyNcJivjEBYS7` |
| 2025 | `session_01GWcK4V5PxyjpL64shTFQjm` |
