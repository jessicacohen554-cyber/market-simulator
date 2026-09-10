# PRECOMMIT — SPP-62: R-ay, the coal supply-class census vintage repair

**Lane** SPP-62 · **Base** `bba0904ddcae387b730e77c4329c70c663d94a85` ·
**Predecessor** `docs/handoffs/FINDING-spp-61-2026-09-10.md` (its §8 successor card R-ay is
this lane's object) · **Control** SPP keeper 5 `2026-09-09-spp-52a-fossil-offer`, bundle
`results/calibration/spp52a_fossil93` — rule 29(b) **form 4**, the committed keeper IS the
control and **no control solve is spent** (§6) · **DATA PROFILE** `spp`.

**Pushed BEFORE any solve.** Every number below is re-derived in this session from the
committed artifacts and the scorer at HEAD; none is quoted from a predecessor lane's prose.

---

## 1. The object, and the seam (ONE)

`scripts/data/derive_coal_supply.py::_coal_supply_table` built its coal **census** — which
plants get a rank row — from

```python
{int(g.plant_code) for g in load_fleet_from_csv(iso, iso_config)   # <- no year, NO VINTAGE
 if g.fuel_type == "coal" and int(g.plant_code) > 0}
```

i.e. from the canonical 2025-Early-Release snapshot, **for every solved year**. A plant that
burned coal in the solved year but had been re-fuelled by the snapshot's vintage is therefore
absent from the census, gets no rank, and falls through the entire four-step resolution ladder
to `''` — which `_coal_class_for` turns into a **bare `COAL` class the SPP EIA-923 benchmark
has no row for**.

**The seam is that census expression and nothing else.** It is replaced by
`_coal_census(iso, iso_config, census_vintages)`: the UNION of the canonical snapshot and each
solved year's own `vintage_<year>/` release, reached through a new `--census-vintage` CLI
argument whose **default is `None` — the canonical snapshot alone, i.e. today's construction
byte-for-byte** (§5).

## 2. Rule 23 `[R-FROZEN-DERIVE]` admissibility — the argument, made explicitly

Rule 23 freezes measured-behaviour parameters against **residuals**: they "re-derive only when
their *source data* updates — never because a residual moved," and the re-derivation commit
must cite the data change.

**The cited trigger is a change in the DERIVE'S OWN INPUT, not a residual.** The derive's
input is a *plant census*, and the census reads an EIA-860 registry that SPP-61 measured to be
**wrong for the solved year**: Harrington's three units read `NG` in the canonical snapshot,
while the 2023 release reads all three `SUB`, the 2024 release reads two of three `SUB`, and
the units' own filed repower dates are 2/2025, 3/2025 and 6/2025. The corrected registry for
each solved year is *already committed on disk* (`data/raw/eia-860/vintage_2023/`,
`vintage_2024/`). Reading the right one is rule 14 `[R-ACCURATE]` in its plainest form.

**Three independent facts make this argument stand on its own rather than lean on the residual:**

1. **The rank the repair produces is not a choice.** EIA-923 reports fuel code `SUB` for plant
   6193 in 2023 and 2024, `_COAL_SOURCE_TO_SUPPLY['SUB'] == 'prb'`, and the benchmark's own
   resolver maps `SUB` → `COAL_PRB`. The derive reaches `prb` at **100 %** of the plant's
   ranked weight (`n_ranks=1`), by the same arithmetic that ranks the other 29 plants. There is
   no free value to set (§7).
2. **The repair is INERT for the keeper**, so it cannot have been selected on the keeper's
   residual: it moves nothing the control scores (§4).
3. **It moves the target residual the WRONG WAY** once the vintage arm is on (§8). A change
   fitted to a residual does not do that.

**What rule 23 would forbid and this is not:** re-deriving because a number moved, re-deriving
with a different `--year` span (which *would* re-rank incumbents by changing the weights), or
hand-adding a plant. The `--year` span is untouched — the pre-patch script at HEAD reproduces
the committed `coal_supply_SPP.csv` **byte-identically** (md5 `5a71bd95bf10a732af980086e541ffa3`),
which is this lane's anchor and is what makes the 29-row census below exact rather than
approximate.

## 3. Phase 0 — the 29-row impact census, MEASURED (zero LP)

**The census, per registry** (`load_fleet_from_csv`, `fuel_type == "coal"`):

| registry | coal plants | adds vs canonical |
|---|---|---|
| canonical (2025 ER) — today's construction | **29** | — |
| `vintage_2023` | 31 | **6193** (Harrington), **10862** (ADM Lincoln) |
| `vintage_2024` | 30 | 6193 |
| `vintage_2025` | *no committed directory* → canonical stands | — |
| **UNION over the solved span 2023–2025** | **31** | **6193, 10862** |

**ALL 29 INCUMBENT ROWS ARE BYTE-IDENTICAL.** The whole diff of the re-derived CSV is two
pure additions — `2 insertions(+), 0 deletions`:

```
+6193,prb,generation,26193400.3,1,prb:100%
+10862,prb,generation,156101.0,1,prb:100%
```

Zero re-ranks, zero weight changes, zero source changes. This is not luck: the census is a
**membership filter**, and each plant's rank is computed from its own EIA-923 rows independent
of every other plant, so widening the census can only ADD rows. The measurement confirms the
construction.

**6193's weight is checkable by hand**: EIA-923 `SUB` net generation 4,754,027.8 + 3,677,455.5
+ 3,293,687.4 + 4,848,193.7 + 4,383,491.1 + 3,177,542.5 + 2,059,002.3 = **26,193,400.3 MWh**
over 2018–2024, `SUB` 100 % of ranked weight.

**Rule 19 `[R-ONE-MECH]` — reconciled with the existing ladder, not stacked on it.** The four
resolvers are (1) the curated ERCOT `COAL_PLANT_SUPPLY`, (2) the EIA-923-derived per-ISO CSV,
(3) the EIA-860 retiree fallback, (4) the flag-gated partial-exit registry. **No fifth is
added.** Both new rows enter resolver (2), and both plants are measured **unresolved by all
four today** (`coal_supply_class(6193) == coal_supply_class(10862) == ''`), so **no existing
resolution changes hands**:

| plant | before | after | resolver |
|---|---|---|---|
| 6193 Harrington | `''` → class `COAL` | `prb` → class `COAL_PRB` | (2), was unresolved |
| 10862 ADM Lincoln | `''` → class `COAL` | `prb` → class `COAL_PRB` | (2), was unresolved |
| 7902 Pirkey | `lignite` → `COAL_LIGNITE` | **unchanged** | (3), untouched |
| 57937 W. Sugar | `''` | **unchanged** | still unresolved |

7902 and 57937 are coal only in `vintage_2020`, **outside** the solved span, so the span-scoped
union leaves them alone — deliberately. An all-vintages union would have pulled 7902 up from
resolver (3) to resolver (2) (at the same value, `lignite`); the span union avoids even that
hand-over.

## 4. R-ay is INERT for the keeper and for every committed run — MEASURED

- **SPP fleet, canonical registry, every `Generator` field of all 1,012 generators:
  BYTE-IDENTICAL** between the committed CSV and the re-derived one. Harrington is `ST_GAS`
  and ADM Lincoln is `ST_CHP` in the snapshot the keeper reads, so their new coal ranks are
  never consulted (`assembly.py` guards the lookup on `fuel == "coal"`).
- **All seven ISOs' fleets byte-identical** (ERCOT 1,450 · CAISO 782 · PJM 1,922 · MISO 1,975 ·
  NYISO 460 · NEISO 431 · SPP 1,012), and plant codes 6193 / 10862 appear in **SPP's fleet
  only** (3 and 1 generators) and in **no other ISO's fleet at all** — even though
  `_derived_coal_supply()` globs every ISO's CSV into one national map.
- **46 of 46 committed `run_config.json` carry `eia860_vintage_tracks_solve_year: false` and
  `eia860_vintage_year: null`** — no committed run in any ISO reads a non-canonical registry,
  so no committed bundle's inputs can move.

**Therefore R-ay requires no re-solve of anything, and the keeper's committed bundle remains a
valid control.**

## 5. Rule 25 `[R-ISO-SCOPE]` — and a hazard found in the shared script, ROUTED not touched

`coal_supply_<ISO>.csv` is per-ISO but `derive_coal_supply.py` is SHARED, so the default path
was measured for all four ISOs that have a CSV: **with the patch applied and no flag passed,
SPP / PJM / MISO / NEISO all re-derive byte-identically to the pre-patch script at HEAD.** The
new behaviour is reachable only by passing `--census-vintage`, which only SPP does.

**LOUD, and not caused by this lane:** re-deriving PJM or MISO at HEAD **with no code change at
all** already re-ranks plants, because the raw `f923_*.zip` receipt corpus that produced their
committed CSVs is gone from `data/raw` and the generation fallback disagrees with it —
**5 PJM plants** (594, 876, 879, 3149, 6166) and **10 MISO plants** (1082, 1091, 1733, 2107,
4041, 4078, 6034, 7343, 8023, 56068, all `prb` → `bituminous`). SPP is the clean case precisely
because its CSV was derived after the zips were gone (every row `source=generation`).
**No ISO may re-derive its coal supply CSV at HEAD without reconciling that lost source first.**
This lane does not touch it; it is each desk's own card (rule 28(d)).

**Also stated, not absorbed:** `coal_supply_*.csv` is a solve-affecting registry table that the
capx-D79 solve-surface fingerprint does **not** cover (the surface is seven config *modules*),
and it carries no `resolved_inputs` sha256 stamp in `run_config.json` the way
`campd-unit-outages-SPP.csv` and `thermal_tranches_SPP.csv` do. For this lane the gap is
harmless — inertness is proven directly in §4 — but it is a real hole and is routed rather than
quietly relied on.

## 6. G-DRIFT — the control is the keeper, no control solve is spent (rule 29(b) form 4)

Keeper anchor: `git.basis_sha` **`fc927c2f439a4e00207bab7c35abd10dc556142b`** (its `git.sha`
`c1393878` is a squashed branch commit that does not resolve).

- **Mechanical instrument (capx D79):** SPP solve-surface fingerprint at HEAD
  **`7ab7e3b0c4741dc3`, 182 rows, `moved: {}`** — byte-identical to the value recorded in the
  keeper's `run_config.json`. `constants.py` (+120 lines) and `plant_taxonomy.py` are both ON
  that surface, so their drift is *proved* not to reach SPP's projected values.
- **Scoring inputs:** of the two `_validation-source` files that changed,
  `actual_lmp.json` has **54 changed leaves, all under `ERCOT`, zero SPP**, and
  `calibration_reference.json` has **198 changed leaves, 197 under `MISO` plus one
  `generated` timestamp, zero SPP**. `actual_lmp_hourly_zonal_SPP.parquet` did not change in
  this window at all.
- **Code hunks**, 23 changed files on the audited paths, every one INERT for an SPP backcast
  solve: `fleet/eia860.py` = the `_PARTIAL_EXIT_WINDOW_START` 2023→2019 move behind
  `partial_plant_exit_carry` (**`false` in the recipe**); `fleet/floors.py` = pjm-177
  `netload_drag_min_run_persistence` (**absent from the recipe**, default `None`);
  `data/outages.py` = the PJM ST_GAS membership registry, per-ISO keyed;
  `fuel/{resolve,trajectories,electric_power,__init__}.py` + `reference/iso-gas-capacity-
  state-weights.csv` = the `gas_electric_power_monthly_level` family (**absent from the
  recipe**); `fuel/hubs.py` = `nyiso_hub_gap_month_level` (default off);
  `fuel/basis/ercot.py`, `interchange/caiso.py` = other ISOs' branches;
  `interchange/spec.py` = MISO's seam ladder — its SPP-hub series is consumed only by
  `interchange/miso.py::measured_miso_spp_hub_prices("MISO", …)`, i.e. by **MISO's** solve
  reading SPP's hub, never by SPP's own; `MISO_2020_renewable_capacity.csv` = MISO;
  `run_calibration*.py`, `lib/holdout_policy.py`, `lib/key_provenance.py`,
  `solve_surface_declared.py` = the `[R-HOLDOUT]` removal plumbing.
- **End-to-end corroboration:** re-scoring the committed keeper with
  `scripts/calibration_verdict.py` at HEAD `bba0904d` reproduces its published determination
  exactly — **NOT-YET**, grade **6 of 8**, **2 fails** (`fuelmix`, `price_tail`),
  `protective 0 / ledgered 0 / commercial_band 0` — and every C1 row, including
  **2024 ST_GAS model 11.970 / actual 20.101 / −8.13 TWh**.

**All hunks INERT ⇒ form 4 is valid. NO CONTROL SOLVE IS SPENT.**

## 7. DOF ledger (rule 21 `[R-DOF]`) — ZERO free parameters added

R-ay adds **no** `ScenarioConfig` field, no constant, no per-plant dict and no tunable value.
`--census-vintage` selects *which committed registry files are read*, by calendar year; it is
declared here as **2023 2024 2025** — the ISO's own scored span, a fact of the program — and
recorded in the derive commit message. The two new ranks are `prb` at 100 % of ranked weight,
computed by the same arithmetic as the other 29 rows. **The keeper's DOF ledger is unchanged**
(`n_residual` 2, entries 3), and its `offer_curve_by_group` authorized-tuning block (rule 1
`[R-STRUCT]` carve-out) is replayed **verbatim at 0.93** on all four bands of the ten fossil
classes.

## 8. What R-ay unblocks, and the PRE-SOLVE PREDICTION (zero LP)

SPP-61 screened `eia860_vintage_tracks_solve_year` on 2023 and **G3's identity limb killed it**:
4.3551 TWh landed in a bare `COAL` class. With R-ay in place that limb is now satisfied **by
construction, at zero LP**, measured on the same registries the solve reads:

| registry | class | control (committed CSV) | R-ay (re-derived CSV) |
|---|---|---|---|
| canonical (**the keeper's own**) | bare `COAL` | **0.0 MW** | **0.0 MW** — inert |
| `vintage_2023` | bare `COAL` | **1,025.9 MW** | **0.0 MW** |
| `vintage_2023` | `COAL_PRB` | 17,451.3 MW | **18,477.2 MW** (+1,025.9) |
| `vintage_2024` | bare `COAL` | **679.0 MW** | **0.0 MW** |
| `vintage_2024` | `COAL_PRB` | 17,611.0 MW | **18,290.0 MW** (+679.0) |

`COAL_LIGNITE` is 1,560.0 MW in every cell. The bare class is eliminated **exactly** — 1,018.0 MW
of Harrington plus 7.9 MW of ADM Lincoln in 2023, 679.0 MW of Harrington units 2+3 in 2024 —
and every megawatt lands in the class the benchmark books.

## 9. THE SCREEN (rule 29 `[R-SCREEN]`)

**Phase 0 did not kill the arm; it cleared the gate that killed it.** The arm therefore earns
one screen solve.

**SCREEN YEAR = 2023, named here before the screen runs, by the mechanism's own MEASURED
FOOTPRINT and never by a residual.** The repair's footprint is **1,025.9 MW / 3 of 3 Harrington
units** in 2023 against **679.0 MW / 2 of 3** in 2024, and Harrington's measured coal is
**3.1775 TWh** in 2023 against **2.0590 TWh** in 2024 — both strictly larger in 2023, while the
**failing C1 row is in 2024**. The choice is the opposite of residual-chasing.

**THE GATE IS STRUCTURAL, IT IS A STOP GATE ONLY, AND IT IS NOT GATED ON C1.** C1 is the target
criterion and is deliberately excluded (rule 1 `[R-STRUCT]`): a structurally-correct mechanism
is never judged by its own residual. It may kill the arm; it may never promote one.

| gate | asks | PASS band | on FAIL |
|---|---|---|---|
| **G1** config identity | solved `run_config.json` shows `eia860_vintage_tracks_solve_year: true`, ten fossil classes at 0.93 on all four bands, `--year 2023` | exact | STOP |
| **G2** identity — the limb that killed SPP-61 | model class set contains **no bare `COAL`** row with any energy | `COAL` energy ≤ 0.001 TWh | **STOP** |
| **G3** magnitude | `COAL_PRB` **rises** by an amount of order Harrington's measured 3.1775 TWh | ΔCOAL_PRB ∈ **[+1.0, +5.0] TWh** vs the control's 63.4651 | STOP |
| **G4** conservation | class energies sum to within the system-volume move | \|Σ Δclass − Δsystem\| ≤ 0.10 TWh | STOP |
| **G5** no NON-target load-bearing criterion flips PASS → FAIL | C2 `sysvol`; C3a mean price; **C3b monthly NRMSE — the limb SPP-61 left unmeasured** | C3a within ±10 % of 25.13; C3b ≤ 0.20 | STOP |

Control values for the differencing, from the keeper's own committed `hourly/` sidecars
(rule 29(b) form 4), 2023 P1: `COAL_PRB` **63.4651**, `COAL_LIGNITE` **7.8875**, `ST_GAS`
**8.3546**, `CT_PEAKER` **17.8622**, `CC_REGULAR` **42.4753**, bare `COAL` **absent**;
**C3a 25.4689** (scorer 25.47), **C3b 0.1647** (scorer 0.165). Both C3 figures are reproduced
in this session from `hourly/system_2023.parquet` + the committed
`data/raw/_validation-source/actual_lmp.json` `rt_lw_mon`, and the same reproduction matches
the scorer in **all three years** (2024 25.2967/0.1761 vs 25.29/0.176; 2025 29.6357/0.1755 vs
29.63/0.176), so the shard reports raw numbers and the parent scores them.

**Rule 32 `[R-SHARD]`:** this session is an ORCHESTRATOR and runs **no LP in its own
container**. One shard per year, ≤ 20 min each, pinned to this PRECOMMIT's full 40-char SHA.
Every shard **pushes only a small markdown report to its own branch — never a bundle** (the
SPP-61 lesson: the parent could not read its shard's transcript or disk).

## 10. REPORTED AGAINST THE REPAIR, BEFORE ANY NUMBER IS READ

**The honest repair is expected to make the fit WORSE, and it stays in anyway (rules 1 / 14).**

- **2023 will likely BREAK a currently-passing row.** C1 2023 `ST_GAS` passes at
  **model 8.073 / actual 15.020 = −6.95 TWh** against a **±8.00 TWh** band — **1.05 TWh of
  headroom**. The arm removes all three Harrington units from `ST_GAS`, and SPP-61 measured
  `ST_GAS` dispatch falling **1.27 TWh** (8.3546 → 7.085) under exactly this arm, which puts
  the scored row at roughly **−8.2 TWh, outside the band**.
- **2024, the target row, moves the WRONG WAY.** C1 2024 `ST_GAS` fails at
  **model 11.970 / actual 20.101 = −8.13 TWh**; it needs the model to **rise** by ≥ 0.13 TWh.
  The arm moves 679.0 MW of Harrington **out of** `ST_GAS`, so the model falls further and the
  row fails harder. **The benchmark's actual cannot move to meet it** — SPP-61 established the
  EIA-923 bench frame is completely inert to the EIA-860 vintage, and the 2024 `ST_GAS` actual
  carries only 0.175 TWh of Harrington.
- **Therefore the CALIBRATED target is unlikely by this route**, and this lane will not chase
  it. No band is widened, no row reclassified, no second repair added to offset the first.
- **The arm is wider than one plant** — SPP-61 measured a whole-registry swap of −2,715.4 MW
  (2023) / −3,175.3 MW (2024) with 94 / 63 plants moving and 0 unexplained. That width is real
  and is owned, not waved through on Harrington's account.
- **R-ay stands regardless of what the screen does to the arm.** It is inert for every committed
  run (§4), rule-14 owed, and carries zero free parameters; its warrant does not depend on the
  arm's verdict.

## 11. Deliverables

1. This PRECOMMIT, pushed before any solve; its SHA pins every shard.
2. `scripts/data/derive_coal_supply.py` — the one seam, default-path byte-identical for all
   four ISOs.
3. `data/raw/_processed-legacy/coal_supply_SPP.csv` — 29 → 31 rows, 2 insertions, 0 deletions.
4. The 2023 screen (one shard), gated in the parent on §9.
5. Full span 2023/2024/2025 **only if** the screen clears, as per-year shards composed into ONE
   registered bundle (rules 16 / 32(d)); registration, scoring, the SPP.js cell, the spp-22 log
   entry and the rule-31 promotion question all happen in the parent.
6. Screen and per-year shard bundles are **gitignored, never `rm`'d** — rule 29(c) is about what
   reaches `main`, and rule 31 `[R-RETAIN]` names `.gitignore` as what discharges it.
