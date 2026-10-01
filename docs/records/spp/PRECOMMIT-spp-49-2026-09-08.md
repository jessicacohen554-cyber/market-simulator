# PRECOMMIT — SPP-49: the two measured-input seam repairs (EIA-923 own-month gas-price plausibility screen; simple-cycle heat-rate floor), repo-wide, adjudicated and censused at zero LP BEFORE either seam file is edited

**Lane** SPP-49 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-08 ·
**Branch** `claude/spp-49-input-seam-repairs-arx1x2` (base `origin/main` `4e4ad90d`; `origin/main` had advanced to
`1cb976f4` by the time this was written — the branch is rebased onto it before the PR, §8.0 rule 3) · **Data profile** `shared`
(the checkout is a full clone; every ISO's keeper fleet was rebuilt) · **Charter** owner ruling **P19** (2026-09-08, SPP desk
r#13: *repo-wide, both seams, one lane*); `FINDING-spp-46-2026-09-07.md` §0.1 and §6 R-1 / R-2 / R-6 / R-7; playbook §6.2
(fuel prices before bands); plan §8.0.

**Written and committed before `plant_prices.py` or `eia860.py` is touched.** Every number below was computed on the
UNEDITED tree (`4e4ad90d` + this lane's data intake and instruments, commit `HEAD~0` of the branch at writing) from the
seven keepers' own fleet-only rebuilds and the committed sidecars. **No LP is solved by this lane, in any phase.** The
re-baseline is SPP-50 (and each other desk's own lane); this lane touches no keeper shard, status file, bench part,
registry sidecar or calibration log.

---

## 0. THE PIN, the controls, the baseline

```
4e4ad90d   origin/main when the branch was cut (the tree every ex-ante number was measured on)
1cb976f4   origin/main at PRECOMMIT time (rebase target)
623184f3   SPP keeper-3 `2026-09-07-spp-3-screened-input` / results/calibration/spp43_screened_B (git.sha in run_config.json)
```

The seven designated keepers (`frontend/data/backcast/keepers/<ISO>.json` → registry sidecar → bundle), each rebuilt
`fleet_only` on its own recipe through `replay_keeper.run_year_kwargs` + `derived_run_year_inputs` — the only sanctioned
fleet-only reconstruction (caiso-243 §7.3):

| ISO | keeper | bundle | years rebuilt | `gas_plant_monthly_fuel_pricing` | `measured_ct_heat_rates` | note |
|---|---|---|---|---|---|---|
| CAISO | 2026-09-06-caiso-260-b1-demand | caiso260_demand_vintage | 2023–2025 | True | True | |
| ERCOT | 2026-09-08-ercot256-drag-layup-mask | ercot256_five_year_keeper | 2024, 2025 | **False** | False | composite five-year keeper; meta carries gas prices for 2024/2025 only, 2023 is the carve-out config and was not rebuilt |
| MISO | 2026-09-07-miso-243-spp-pairing | miso243_sppair_K | 2023–2025 | True | True | |
| NEISO | 2026-09-06-neiso-106-fossil-offer | neiso106_offerlevel | 2023–2025 | True | True | |
| NYISO | 2026-09-07-nyiso-213-summer-seam | nyiso213_summer_seam | 2023–2025 | True | True | |
| PJM | 2026-08-15-pjm-162-inputclock | pjm_debugb_inputclock_A | 2023–2025 | True | True | rebuilt with `pjm_da_virtual_bids=False`: the gitignored DataMiner2 virtual-bid corpus is absent from this checkout; it is a demand-side overlay cleared in the LP and reaches neither the fleet, the fuel prices nor the heat rates this census reads (`census.py::REBUILD_OVERRIDES`) |
| SPP | 2026-09-07-spp-3-screened-input | spp43_screened_B | 2023–2025 | True | False | |

**Baseline gates at `4e4ad90d`** (`scratch/gates/pre_*.log`): `audit_keepers --check` 0 · `check_registry_payload_parity` 0 ·
`check_gate_a_provenance` **1** (ERCOT and MISO `gate.a_keeper_marker` cite superseded keepers — the two the charter names;
neither is this lane's) · `check_bench_freshness` 0 · `check_golden_manifest` 0 · `ci_refactor_guards` 0 ·
`check_mechanism_matrix` 0 · `check_key_provenance --no-fetch` 0 (230 committed run configs: 183 reproduce, 32 carry no key,
15 mismatch — all 15 the known, recipe-verified exceptions).

**No control solve and no G-DRIFT is needed**: this lane solves nothing and differences nothing against a keeper's output;
its instrument is the input arrays, rebuilt on each keeper's own recipe at HEAD.

---

## 1. THE ONE OPEN ADJUDICATION — construction or registered gate, decided per seam before any measurement

The owner's criterion, verbatim: *a construction is right where the repaired value is the only defensible reading of the
measured record and no run would ever want the unrepaired one; a registered gate is right where a desk could legitimately
want its ISO's raw series.* Decided here, argued here, and the measurements below were designed AFTER the decision, not
the other way round.

### 1.1 SEAM 2 — the simple-cycle heat-rate floor: a CONSTRUCTION

Unconditional at the fleet seam, the form `_egrid_boundary_hr_repairs` already uses, no `ScenarioConfig` field, no new
scalar. Three reasons, in order of weight:

1. **There is no defensible reading of the raw value.** A plant whose every operating row is a simple-cycle prime mover
   (EIA-860 `GT` or `IC` — no steam cycle anywhere on site) has no heat recovery, so its annual net heat rate cannot sit
   below the best bare turbine's. eGRID's `PLHTRT` is `PLHTIAN / PLNGENAN`; Pioneer 57881 reads **3.43** because its
   EIA-923 net generation is ~3× its CEMS gross load (SPP-46 §3.1) — a ratio across mismatched boundaries, exactly the
   class of arithmetic the CC ceiling repairs on the other side of the physics. A desk cannot "legitimately want" a
   thermodynamic impossibility; a desk that wants a *measured* CT rate has `measured_ct_heat_rates` (registered, CAMPD
   loaded rates, which win over the eGRID value in the row loop and are untouched by this repair).
2. **It introduces no value that could be wanted either way.** The floor is the existing cited constant
   `HEAT_RATE_BINS["gas_ct"]["aero"]` = 9.0 (EIA Table 8); the reconciled value is the floor itself (§2.2), so the only
   choice a gate could offer is "impossible or possible".
3. **Precedent form.** The CC ceiling (miso-88) landed as a construction on the identical rule-14 reasoning ("measured data
   on a different boundary than our representation, reconciled rather than replaced by a guess"); the floor is its
   mirror and belongs beside it.

What a construction costs, stated (§3.2): it moves no cache key by arithmetic, so it is a **same-key invalidation** for
every ISO whose fleet carries a clamped row — all seven — and the ledger entry / `SolveEpoch` that records it live in
files outside this lane's region (`results/cache.py`, `config/solve_surface.py`); the entry text is written in the FINDING
and ROUTED. That is a cost of the construction route, not a reason to choose a gate: the criterion is not convenience.

### 1.2 SEAM 1 — the EIA-923 own-month plausibility screen: a REGISTERED GATE, default ON

`ScenarioConfig.f923_gas_price_plausibility_screen: bool = True`, declared through the (b′-1) route (frozen drop value
`"False"`, a `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry, `__post_init__` coercion to the frozen declaration wherever
the seam is unreachable for the whole run). The owner ruled it repo-wide and default-ON; the question was only whether a
desk could ever legitimately want its raw series, and the answer is **yes, in one real and named case**:

1. **A plant that buys at a hub the state blend misrepresents.** The reference is the state's volume-weighted delivered
   price to ALL electric generators. Texas's blends Gulf Coast with Permian; a Waha-connected plant in 2024 paid near
   zero or negative for gas that the TX series prices at $1.4–3.9. This repository's own `SOURCES_spp_gas.md` records
   New Mexico's negative prints as *real Permian/Waha episodes, not data errors*. Under the screen, Mustang Station's
   seven negative 2024 months and Elk Station's $0.16–0.41 read as implausible against the TX blend (§4) — and the
   owner has ruled that reading (SPP-46 §0.2: the six plants run 12.3 TWh against CAMPD's 4.2). But the ERCOT desk,
   whose West zone carries a measured Waha basis (`ercot_zonal_gas_basis`), or a future Permian-aware SPP-South basis
   lane, could legitimately prefer the raw print for that cohort. A gate keeps that door open **per ISO, per lane,
   under rule 25** without re-opening the scope ruling.
2. **Rule 14's own precedence.** The raw own-reported print is the measured input rule 14 says to prefer wherever it is
   NOT misaligned. The screen encodes a judgement about WHEN it is misaligned (the band). A construction would make that
   judgement unrevisable in place; a gate leaves the measured series reachable — the same reason `gas_plant_monthly_fuel_pricing`
   itself is a gate and not a construction.
3. **The band is a declared threshold, and thresholds are registered.** [0.5, 2.0] lives in `constants.py` with its
   citation; it is NOT tunable (rule 1 (c): never swept against a gate), but a registered mechanism with a registered
   constant is what rule 24 asks of anything that changes a solve.

What a gate costs, stated: the mechanism enters the matrix (rule 28(c): base row + a `·` cell in every shard); every
config that resolves `True` and can reach the seam re-keys (§3.1 — 18 keys, every one a backcast config that arms
per-plant gas pricing, zero off-target); the CLI `--no-…` flag lives in `scripts/run_calibration*.py`, outside this lane's
region, so a desk reaches the pre-repair posture through the existing generic `--set f923_gas_price_plausibility_screen=false`
override channel (the `prb_overrides` bag, applied last) until the desk lands the flag — ROUTED.

**Why not the same answer for both.** The two seams differ on exactly the criterion: a sub-9.0 simple-cycle rate has no
reading under which it is the plant's efficiency; a sub-reference gas print has one (a cheaper hub than the state blend),
and the repository's own data notes say so.

---

## 2. THE CONSTRUCTIONS, declared before they ran

### 2.1 Seam 1 — the screen (`plant_prices.py::apply_plant_monthly_fuel_prices`), as SPP-46 R-1 specifies it and no wider

- **Scope.** `fuel_group == "Natural Gas"` rows only; only under `gas_plant_monthly_fuel_pricing` (the seam's own gate);
  backcast/hindcast only (the seam's existing mode gate); `year` rows only.
- **Reference** `R[s, y, m]`: EIA `N3045<ST>3` ($/Mcf) ÷ **1.036** — the repository's registered `_MCF_TO_MMBTU`
  (`data/fuel/basis/ercot.py`), not SPP-46's 1.037; the 0.1 % difference cannot move a 2× band. The plant's state `s`
  is the F923 frame's own `state` column (populated on 100 % of the frame's 41,957 gas rows) — **never the fleet row**
  (SPP-46 R-7: every SPP fleet row's `state` is empty; so is every plant-level fleet's without `fleet_state_from_eia860`).
- **Band** [`LOW`, `HIGH`] = **[0.5, 2.0]** × `R`, `F923_GAS_PRICE_PLAUSIBILITY_BAND` in `constants.py`, cited to SPP-46
  PRECOMMIT §3(E) and P19. A reported month `p` with `p < 0.5 R` (a negative print always qualifies when `R > 0`) or
  `p > 2.0 R` is **replaced by `R`** (the prompt's "falls back to that reference"; SPP-46 R-1's parenthetical "the pool is
  built from screened months" is honoured by screening the FRAME the nearby pool reads, so an own-reported month and the
  pool it donates to see the same value). An in-band print is kept byte-for-byte.
- **Unpublished state-month** → `N3045US3` for that month (the documented fallback; counted and logged per run).
  Neither published → the month is not screened (counted).
- **`R ≤ 0`** (real negative-basis months: NM 2024-08, 2025-10; AZ 2026-04; WY 2022-02) → the band is undefined; the
  month is left as reported (counted). The screen never floors a real negative reference to zero.
- **The reference file** `data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv` (this
  branch's first commit) — absent → the screen cannot run, logs a WARNING naming the file and passes the frame through,
  the same absent-input posture the F923 parquet itself has at this seam.
- **Not screened by this lane, stated**: `iso_monthly_gas_prices` / `_iso_monthly_fuel_prices` (the ISO-month
  volume-weighted series the CAISO interchange model reads) consumes the same frame unscreened — a third consumer of the
  seam, ROUTED, because P19 names the `apply_plant_monthly_fuel_prices` seam and no wider.

### 2.2 Seam 2 — the floor (`eia860.py`, beside `_egrid_boundary_hr_repairs`)

- **Predicate**: a plant is *simple-cycle-only* iff every OP row of the plant in the fleet frame has `prime_mover` in
  `{GT, IC}`. (SPP-46 wrote "CT-only"; Pioneer carries 3 GT + 12 IC rows in 2024 and reads 3.43 on all of them, so the
  physical statement — no steam cycle anywhere on site — is the predicate, and "GT-only" would have missed the plant that
  motivated the repair.) Any `CA` / `CT` / `CS` / `ST` row makes the plant mixed and OUT of scope: its blend rate is the
  `egrid_family_heat_rates` object (SPP-46 R-3), a different mechanism (rule 19).
- **Floor** `EGRID_CT_HR_PHYSICAL_FLOOR = HEAT_RATE_BINS["gas_ct"]["aero"]` (9.0), a named alias in `constants.py` beside
  `EGRID_CC_HR_PHYSICAL_CEILING`, no new number.
- **Reconciled value = the floor** (`max(heat_rate, floor)` on the plant's rows): the smallest repair that resolves the
  impossibility — the CC ceiling's condition 4 applied at the bound. The alternative, "treat the eGRID value as absent and
  fall to the vintage bin", was considered and refused: it discards the measured information that the plant is
  efficient (Groton 56238 at 8.21 would become 10.5), and it is not what SPP-46 predicted with.
- **Precedence unchanged**: applied at the frame seam right after the boundary repair, so `egrid_family_heat_rates`
  (frame, later), `measured_ct_heat_rates` (row loop) and the CHP measured rates keep exactly their present precedence —
  a measured CAMPD loaded rate still wins over the clamped eGRID value where armed (CAISO, MISO, NEISO, NYISO, PJM
  keepers), which is why those ISOs' clamped MW are small (§4).
- Every mode, every ISO, every fleet read path that passes `_rows_to_generators` (the canonical snapshot, the per-year
  vintages, the mothball re-carry). The ERCOT CAMPD-bin path carries CEMS-measured TRANCHE rates and inherits the eGRID
  plant rate only where it has no measured tranche; the ex-post rebuild measures exactly which rows move there.

### 2.3 What is deliberately NOT built

- No CLI flag (scripts outside the region — routed). No change to `iso_monthly_gas_prices` (routed). No epoch entry
  (routed with text). **Harrington 6193's fuel vintage (SPP-46 R-4) is not this lane's**; §6 reports what the screen does
  to its rows. Pioneer's 763 MW of rows against a 427 MW nameplate (2025-vintage units in the 2024 fleet — SPP-46's
  second question) is reported, not fixed.

---

## 3. THE EX-ANTE CACHE-KEY CENSUS (`spp49/key_census.py`, `key_census_pre.json`; `scenarios.py` untouched)

Every committed `run_config.json` (230, by `git ls-files`) hashed under the live HEAD rules — validated against its own
recorded `cache_key` exactly as `scripts/check_key_provenance.py` does (183 reproduce, 32 carry no key, 15 are the known
exceptions) — and under the post-edit seam-1 rule applied arithmetically (the field inserted at the value the coercion
would resolve, dropped at the frozen `False`).

### 3.1 Seam 1 (registered gate, default ON, coerced to the frozen declaration where unreachable)

**18 keys move; 0 off-target.** Every move is a `mode == "backcast"` config with `gas_plant_monthly_fuel_pricing: true`
— the exact set the screen can reach; every forecast and every hindcast config is unmoved, and so is every ERCOT
config (the ERCOT keeper never arms per-plant gas pricing).

| ISO / lane | committed configs | keys that move |
|---|---|---|
| CAISO/backcast | 2 | 2 |
| CAISO/forecast | 20 | 0 |
| CAISO/hindcast | 1 | 0 |
| ERCOT/backcast | 7 | 0 |
| ERCOT/forecast | 28 | 0 |
| ERCOT/hindcast | 3 | 0 |
| MISO/backcast | 1 | 1 |
| MISO/forecast | 25 | 0 |
| MISO/hindcast | 9 | 0 |
| NEISO/backcast | 5 | 5 |
| NEISO/forecast | 50 | 0 |
| NEISO/hindcast | 6 | 0 |
| NYISO/backcast | 7 | 7 |
| NYISO/forecast | 23 | 0 |
| NYISO/hindcast | 5 | 0 |
| PJM/backcast | 2 | 2 |
| PJM/forecast | 22 | 0 |
| PJM/hindcast | 12 | 0 |
| SPP/backcast | 1 | 1 |
| SPP/hindcast | 1 | 0 |

| ISO | lane | bundle | key |
|---|---|---|---|
| NYISO | backcast | `_nyiso114_baseattrib_2024` | `1aa2f0cb0dc53c22` → `55948ebbda2ceca6` |
| CAISO | backcast | `caiso260_demand_vintage` | `33d8599a22ad1eea` → `e476ce1d5d05748c` |
| CAISO | backcast | `caiso262_2022_touchpoint` | `aaa66e663acdf761` → `fc07ce8c27ef4c5a` |
| MISO | backcast | `miso243_sppair_K` | `f130587822fbf565` → `1eabe48cd61dc5ab` |
| NEISO | backcast | `neiso105_offerlevel` | `628411395fbd4c71` → `67f444bff7756372` |
| NEISO | backcast | `neiso106_offerlevel` | `38b460ca08f63a01` → `a34a0ddb098d2526` |
| NEISO | backcast | `neiso106_touchpoints` | `bcc967ecfc9aad39` → `6d75d52d35cee9c7` |
| NEISO | backcast | `neiso99_joint_B` | `be3ebfbbae26ea54` → `01ce1803a338e957` |
| NEISO | backcast | `neiso_tp2022_k99` | `f6c66ec6d22dcfe8` → `0bae242f95dec408` |
| NYISO | backcast | `nyiso192_astoria_panel` | `0ac15036eacc3d22` → `eb79e63c33995244` |
| NYISO | backcast | `nyiso196_extract_basis` | `cc529eedb3383829` → `7170dd68d697d2a4` |
| NYISO | backcast | `nyiso202_startup_aware` | `942480d844dfeaa1` → `ee92088a7e4c2142` |
| NYISO | backcast | `nyiso209_2022_touchpoint` | `a053702708677ac3` → `1e9461d68cc47784` |
| NYISO | backcast | `nyiso213_summer_seam` | `95d4d8d167373eb7` → `43501a08d8fb1245` |
| NYISO | backcast | `nyiso213_tp2022` | `58bb05ceb94368b8` → `c17241d7ad9a17dc` |
| PJM | backcast | `pjm169_tp2022_2021_f2arm` | `5325f29942fcb327` → `fe23d777dc9ec637` |
| PJM | backcast | `pjm_debugb_inputclock_A` | `159733571efa869b` → `d55c714ebf47b81e` |
| SPP | backcast | `spp43_screened_B` | `392dcca76cd6156f` → `8529c679f9365b7e` |

Of the 18, **six are the designated keepers** of CAISO, MISO, NEISO, NYISO, PJM and SPP; the other twelve are their
lineage / touchpoint bundles. A moved key is a one-time cache miss, never a wrong answer: nothing can be served at a key
that moved. The seven `*-plain-backcast` pinned literals and the forecast default (`tests/regression/test_persisted_identity.py`)
are non-armed / non-backcast configs: coerced to the frozen declaration, dropped, **unmoved** (asserted after the edit).

### 3.2 Seam 2 (construction)

**0 keys move by arithmetic** — no field, and the two new `constants.py` names (`F923_GAS_PRICE_PLAUSIBILITY_BAND`,
`EGRID_CT_HR_PHYSICAL_FLOOR`) are declared at their live hash in `solve_surface_declared.py` by the registration script
(CI check 5 forces it), so an ADDED name moves nothing (D79's design). The change is therefore a **same-key invalidation**,
in scope for every ISO whose fleet carries a clamped row (§4: all seven, from 11 MW in CAISO to 1,297 MW in SPP). The
ledger entry and the scoped `SolveEpoch` text are in the FINDING §7, ROUTED; until they land, the seven keepers' committed
bundles are pre-repair evidence under unmoved keys, which the FINDING says in so many words.

---

## 4. THE FLAGGED-ROW CENSUS PER ISO (`spp49/census.py`, `census_pre_<ISO>_<year>.json`, `seam1_plant_months_<ISO>_<year>.csv`)

Read off each keeper's rebuilt fleet: "gas plants / MW" is the keeper's gas fleet; "own-reporting plants" are those with
at least one own EIA-923 Natural Gas month in the year (the ONLY rows seam 1 can touch); "rows / MW touched" are fleet
rows at a flagged plant. **"armed = NO" (ERCOT) means the seam is unreachable on that keeper: the plant-month counts are
reported for the desk ("if armed") and the touched MW is zero.**

## Seam 1 — plant-month census (own-reported Natural Gas months of the ISO's gas plants)

| ISO | year | armed | gas plants / MW | own-reporting plants | plant-months | in band | low | negative | high | US-ref months | no-band (ref<=0) | flagged plants | rows / MW touched (share) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CAISO | 2023 | yes | 181 / 29,271 | 7 | 79 | 76 | 0 | 0 | 3 | 0 | 0 | 3 | 36 / 1,702 (5.8 %) |
| CAISO | 2024 | yes | 181 / 29,275 | 7 | 82 | 75 | 0 | 0 | 7 | 0 | 0 | 2 | 19 / 929 (3.2 %) |
| CAISO | 2025 | yes | 181 / 29,278 | 7 | 84 | 78 | 0 | 0 | 6 | 0 | 0 | 1 | 12 / 370 (1.3 %) |
| ERCOT | 2024 | NO | 141 / 59,890 | 22 | 259 | 196 | 2 | 0 | 61 | 0 | 0 | 11 | 0 / 0 (0.0 %) |
| ERCOT | 2025 | NO | 141 / 59,890 | 25 | 292 | 241 | 3 | 2 | 46 | 0 | 0 | 10 | 0 / 0 (0.0 %) |
| MISO | 2023 | yes | 332 / 67,736 | 103 | 1140 | 1023 | 3 | 0 | 114 | 0 | 0 | 22 | 139 / 10,890 (16.1 %) |
| MISO | 2024 | yes | 331 / 67,847 | 100 | 1128 | 1003 | 2 | 0 | 123 | 0 | 0 | 29 | 173 / 16,464 (24.3 %) |
| MISO | 2025 | yes | 330 / 67,271 | 99 | 1131 | 1044 | 1 | 0 | 86 | 373 | 0 | 18 | 104 / 8,703 (12.9 %) |
| NEISO | 2023 | yes | 99 / 17,448 | 2 | 13 | 12 | 0 | 0 | 1 | 0 | 0 | 1 | 7 / 372 (2.1 %) |
| NEISO | 2024 | yes | 100 / 17,437 | 2 | 14 | 13 | 0 | 0 | 1 | 0 | 0 | 1 | 7 / 372 (2.1 %) |
| NEISO | 2025 | yes | 100 / 17,437 | 2 | 18 | 18 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 (0.0 %) |
| NYISO | 2023 | yes | 101 / 23,676 | 5 | 60 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 (0.0 %) |
| NYISO | 2024 | yes | 101 / 23,684 | 5 | 60 | 60 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 (0.0 %) |
| NYISO | 2025 | yes | 101 / 23,684 | 5 | 59 | 59 | 0 | 0 | 0 | 0 | 0 | 0 | 0 / 0 (0.0 %) |
| PJM | 2023 | yes | 270 / 98,977 | 27 | 307 | 282 | 1 | 0 | 24 | 0 | 0 | 9 | 64 / 8,575 (8.7 %) |
| PJM | 2024 | yes | 270 / 98,991 | 26 | 302 | 288 | 0 | 0 | 14 | 0 | 0 | 5 | 35 / 4,128 (4.2 %) |
| PJM | 2025 | yes | 270 / 98,991 | 23 | 271 | 258 | 0 | 0 | 13 | 39 | 0 | 7 | 50 / 4,932 (5.0 %) |
| SPP | 2023 | yes | 179 / 32,660 | 55 | 648 | 609 | 5 | 0 | 34 | 0 | 0 | 14 | 66 / 5,865 (18.0 %) |
| SPP | 2024 | yes | 179 / 32,677 | 55 | 642 | 544 | 60 | 11 | 25 | 0 | 2 | 19 | 90 / 10,409 (31.9 %) |
| SPP | 2025 | yes | 179 / 32,677 | 48 | 555 | 505 | 37 | 5 | 6 | 227 | 2 | 11 | 48 / 5,445 (16.7 %) |

**F923 own-reporting coverage is THIN in NYISO (5 of 101 gas plants), NEISO (2 of 100), CAISO (7 of 181) and PJM (27 of
270; the frame carries NO Pennsylvania, New Jersey, Delaware, Connecticut, Rhode Island, Maine or Vermont gas rows at
all).** In those ISOs the seam prices almost every gas row from the nearby pool, and the screen's reach is bounded by the
few own-reporting plants — NYISO is INERT (60/60 months in band, 0 rows touched) and NEISO nearly so (one plant, 372 MW).
The state column itself is complete wherever a row exists.

## Seam 2 — simple-cycle-only plants below the floor

| ISO | year | simple-cycle-only plants | below 9.0 | of which < 6.0 | 8.0–9.0 | rows / MW clamped (share of gas MW) |
|---|---|---|---|---|---|---|
| CAISO | 2023 | 105 | 37 | 20 | 2 | 1 / 11 (0.04 %) |
| CAISO | 2024 | 105 | 37 | 20 | 2 | 1 / 11 (0.04 %) |
| CAISO | 2025 | 105 | 37 | 20 | 2 | 1 / 11 (0.04 %) |
| ERCOT | 2024 | 58 | 13 | 6 | 3 | 59 / 855 (1.43 %) |
| ERCOT | 2025 | 58 | 13 | 6 | 3 | 59 / 855 (1.43 %) |
| MISO | 2023 | 173 | 34 | 22 | 12 | 46 / 230 (0.34 %) |
| MISO | 2024 | 173 | 34 | 22 | 12 | 46 / 230 (0.34 %) |
| MISO | 2025 | 172 | 34 | 22 | 12 | 46 / 230 (0.34 %) |
| NEISO | 2023 | 27 | 12 | 7 | 0 | 14 / 30 (0.17 %) |
| NEISO | 2024 | 27 | 12 | 7 | 0 | 14 / 30 (0.17 %) |
| NEISO | 2025 | 27 | 12 | 7 | 0 | 14 / 30 (0.17 %) |
| NYISO | 2023 | 32 | 8 | 6 | 1 | 10 / 10 (0.04 %) |
| NYISO | 2024 | 32 | 8 | 6 | 1 | 9 / 11 (0.05 %) |
| NYISO | 2025 | 32 | 8 | 6 | 1 | 9 / 11 (0.05 %) |
| PJM | 2023 | 130 | 23 | 12 | 8 | 24 / 54 (0.05 %) |
| PJM | 2024 | 130 | 23 | 12 | 8 | 24 / 54 (0.05 %) |
| PJM | 2025 | 130 | 23 | 12 | 8 | 24 / 54 (0.05 %) |
| SPP | 2023 | 109 | 9 | 3 | 5 | 32 / 1,297 (3.97 %) |
| SPP | 2024 | 109 | 9 | 3 | 5 | 32 / 1,297 (3.97 %) |
| SPP | 2025 | 109 | 9 | 3 | 5 | 32 / 1,297 (3.97 %) |

### Seam 2 plants (latest keeper year), clamp 9.0

| ISO | plant | eGRID rate | nameplate MW | fleet MW at plant | fleet MW below floor | vintage |
|---|---|---|---|---|---|---|
| CAISO | 52107 | 4.98 | 48.8 | 10.4 | 0.0 | 1988-1988 |
| CAISO | 52169 | 5.09 | 234.0 | 142.3 | 0.0 | 1989-1989 |
| CAISO | 52086 | 5.15 | 13.6 | 1.1 | 0.0 | 1986-1987 |
| CAISO | 52085 | 5.19 | 12.4 | 1.2 | 0.0 | 1982-1982 |
| CAISO | 55851 | 5.20 | 49.9 | 13.6 | 0.0 | 2002-2002 |
| CAISO | 52081 | 5.21 | 6.8 | 0.5 | 0.0 | 1988-1988 |
| CAISO | 58914 | 5.30 | 16.4 | 10.5 | 0.0 | 2003-2014 |
| CAISO | 52104 | 5.31 | 12.4 | 1.1 | 0.0 | 1982-1982 |
| CAISO | 50115 | 5.41 | 48.2 | 11.7 | 0.0 | 1984-1984 |
| CAISO | 50751 | 5.46 | 24.0 | 3.4 | 0.0 | 1989-1989 |
| CAISO | 50622 | 5.49 | 18.0 | 3.8 | 0.0 | 1986-1986 |
| CAISO | 50170 | 5.53 | 38.7 | 8.3 | 0.0 | 1986-1986 |
| CAISO | 57585 | 5.60 | 29.0 | 8.7 | 0.0 | 1986-1986 |
| CAISO | 52147 | 5.63 | 19.2 | 2.6 | 0.0 | 1983-1983 |
| CAISO | 52096 | 5.66 | 42.8 | 9.5 | 0.0 | 1990-1990 |
| CAISO | 10496 | 5.79 | 300.0 | 187.2 | 0.0 | 1985-1985 |
| CAISO | 50752 | 5.81 | 94.2 | 14.2 | 0.0 | 1985-1986 |
| CAISO | 54477 | 5.91 | 7.7 | 2.3 | 0.0 | 1990-1990 |
| CAISO | 50537 | 5.94 | 6.0 | 0.7 | 0.0 | 1987-1987 |
| CAISO | 50134 | 5.99 | 300.0 | 195.0 | 0.0 | 1987-1987 |
| CAISO | 10206 | 6.07 | 10.4 | 0.6 | 0.0 | 1989-1989 |
| CAISO | 57977 | 6.32 | 6.2 | 0.6 | 0.0 | 2010-2010 |
| CAISO | 50464 | 6.51 | 68.7 | 21.3 | 0.0 | 1982-1989 |
| CAISO | 10650 | 6.53 | 46.0 | 29.9 | 0.0 | 1991-1991 |
| CAISO | 52077 | 6.56 | 7.0 | 1.2 | 0.0 | 1985-1985 |
| CAISO | 50963 | 6.57 | 5.3 | 0.6 | 0.0 | 2003-2003 |
| CAISO | 50865 | 6.62 | 38.9 | 21.4 | 0.0 | 1991-1991 |
| CAISO | 10649 | 6.64 | 46.0 | 29.9 | 0.0 | 1995-1995 |
| CAISO | 50985 | 6.84 | 2.8 | 0.5 | 0.0 | 1989-2004 |
| CAISO | 50612 | 7.33 | 46.0 | 29.9 | 0.0 | 1991-1991 |
| CAISO | 50003 | 7.37 | 46.0 | 29.9 | 0.0 | 1990-1990 |
| CAISO | 54410 | 7.42 | 27.7 | 4.9 | 0.0 | 1990-1990 |
| CAISO | 54768 | 7.42 | 46.0 | 29.9 | 0.0 | 1992-1992 |
| CAISO | 52186 | 7.80 | 49.9 | 32.4 | 0.0 | 1990-1990 |
| CAISO | 56080 | 7.89 | 14.0 | 2.9 | 0.0 | 2020-2020 |
| CAISO | 7449 | 8.73 | 50.0 | 49.3 | 11.3 | 1996-1996 |
| CAISO | 246 | 8.75 | 167.0 | 163.4 | 0.0 | 2010-2011 |
| ERCOT | 10298 | 4.62 | 318.4 | 95.5 | 0.0 | 2014-2016 |
| ERCOT | 10154 | 5.14 | 141.0 | 42.3 | 42.3 | 1985-2020 |
| ERCOT | 10790 | 5.35 | 102.4 | 30.7 | 30.7 | 1987-1987 |
| ERCOT | 10692 | 5.37 | 381.8 | 114.5 | 114.5 | 1989-2004 |
| ERCOT | 57504 | 5.39 | 98.0 | 34.3 | 34.3 | 2010-2024 |
| ERCOT | 57322 | 5.39 | 15.0 | 4.5 | 4.5 | 2009-2009 |
| ERCOT | 55015 | 6.45 | 572.0 | 371.8 | 0.0 | 1997-2000 |
| ERCOT | 52176 | 7.62 | 169.8 | 149.5 | 0.0 | 1987-1987 |
| ERCOT | 55052 | 7.87 | 1.8 | 0.6 | 0.6 | 1981-2017 |
| ERCOT | 50475 | 7.96 | 41.0 | 12.3 | 2.1 | 1989-1989 |
| ERCOT | 3612 | 8.49 | 244.0 | 1,138.0 | 625.9 | 2010-2010 |
| ERCOT | 61643 | 8.59 | 225.6 | 225.6 | 0.0 | 2018-2018 |
| ERCOT | 59391 | 8.72 | 224.4 | 224.4 | 0.0 | 2016-2016 |
| MISO | 10690 | 4.97 | 85.3 | 24.1 | 24.1 | 1990-1990 |
| MISO | 50389 | 5.05 | 7.6 | 2.1 | 2.1 | 1990-1990 |
| MISO | 55799 | 5.06 | 21.2 | 5.3 | 5.3 | 1995-1995 |
| MISO | 54637 | 5.08 | 73.8 | 18.3 | 18.3 | 1992-1992 |
| MISO | 10568 | 5.11 | 38.4 | 9.1 | 9.1 | 1988-1988 |
| MISO | 58265 | 5.18 | 3.0 | 0.9 | 0.9 | 2006-2006 |
| MISO | 55051 | 5.21 | 306.0 | 67.5 | 67.5 | 1997-1997 |
| MISO | 58428 | 5.22 | 19.6 | 7.2 | 7.2 | 2004-2004 |
| MISO | 55122 | 5.22 | 83.2 | 21.0 | 21.0 | 2001-2001 |
| MISO | 56248 | 5.25 | 80.0 | 20.7 | 20.7 | 2002-2002 |
| MISO | 54918 | 5.25 | 4.8 | 0.6 | 0.6 | 1995-1995 |
| MISO | 54240 | 5.25 | 7.5 | 1.9 | 1.9 | 2004-2004 |
| MISO | 56787 | 5.27 | 83.9 | 21.8 | 21.8 | 2000-2000 |
| MISO | 58330 | 5.28 | 8.1 | 1.8 | 1.8 | 2016-2016 |
| MISO | 55857 | 5.29 | 23.5 | 6.7 | 6.7 | 1999-1999 |
| MISO | 54604 | 5.30 | 3.0 | 0.8 | 0.8 | 1989-1989 |
| MISO | 58138 | 5.37 | 7.5 | 0.7 | 0.7 | 2004-2004 |
| MISO | 59452 | 5.38 | 7.8 | 1.1 | 1.1 | 2018-2018 |
| MISO | 54851 | 5.44 | 31.3 | 5.5 | 0.0 | 1971-2013 |
| MISO | 60102 | 5.65 | 3.2 | 0.9 | 0.0 | 1990-1990 |
| MISO | 10195 | 5.69 | 25.0 | 6.0 | 6.0 | 1984-1984 |
| MISO | 59467 | 5.91 | 12.9 | 12.9 | 12.0 | 2015-2015 |
| MISO | 2068 | 8.22 | 28.4 | 22.6 | 0.0 | 2020-2020 |
| MISO | 60564 | 8.37 | 46.5 | 46.5 | 0.0 | 2018-2018 |
| MISO | 61391 | 8.43 | 56.4 | 56.5 | 0.0 | 2019-2019 |
| MISO | 6558 | 8.45 | 65.1 | 60.2 | 0.0 | 2016-2016 |
| MISO | 61392 | 8.53 | 131.6 | 131.6 | 0.0 | 2019-2019 |
| MISO | 60559 | 8.55 | 51.3 | 50.1 | 0.0 | 2017-2017 |
| MISO | 1980 | 8.55 | 28.4 | 28.9 | 0.0 | 2013-2019 |
| MISO | 66059 | 8.60 | 131.6 | 131.6 | 0.0 | 2023-2023 |
| MISO | 7818 | 8.62 | 173.0 | 164.3 | 0.0 | 1999-2016 |
| MISO | 60647 | 8.80 | 46.5 | 30.2 | 0.0 | 2017-2017 |
| MISO | 7399 | 8.96 | 15.4 | 15.0 | 0.0 | 1993-1993 |
| MISO | 7806 | 8.98 | 7.7 | 7.7 | 0.0 | 2020-2020 |
| NEISO | 50621 | 4.12 | 9.0 | 1.8 | 1.8 | 2004-2015 |
| NEISO | 58184 | 5.14 | 16.5 | 5.0 | 5.0 | 2005-2005 |
| NEISO | 58166 | 5.17 | 5.3 | 0.5 | 0.5 | 2008-2008 |
| NEISO | 54907 | 5.26 | 43.4 | 12.4 | 12.4 | 2021-2021 |
| NEISO | 54605 | 5.35 | 25.8 | 8.4 | 8.4 | 1992-1992 |
| NEISO | 60276 | 5.58 | 4.1 | 0.6 | 0.6 | 2015-2015 |
| NEISO | 10408 | 5.86 | 2.0 | 0.5 | 0.0 | 2013-2013 |
| NEISO | 10108 | 6.07 | 5.0 | 1.1 | 0.0 | 2000-2000 |
| NEISO | 56928 | 6.38 | 4.5 | 0.7 | 0.0 | 2007-2007 |
| NEISO | 58327 | 6.45 | 5.8 | 1.4 | 1.4 | 2002-2010 |
| NEISO | 54937 | 6.59 | 3.8 | 1.2 | 0.0 | 2021-2021 |
| NEISO | 58158 | 7.05 | 2.4 | 0.5 | 0.0 | 2009-2009 |
| NYISO | 58167 | 4.84 | 2.6 | 0.8 | 0.8 | 2004-2004 |
| NYISO | 57789 | 5.56 | 6.3 | 1.6 | 0.0 | 2010-2010 |
| NYISO | 50203 | 5.60 | 5.8 | 1.5 | 1.5 | 1986-1986 |
| NYISO | 57798 | 5.70 | 4.6 | 2.7 | 2.7 | 2010-2010 |
| NYISO | 59453 | 5.77 | 4.1 | 3.7 | 3.7 | 2024-2024 |
| NYISO | 50427 | 5.87 | 2.6 | 0.5 | 0.5 | 1991-1995 |
| NYISO | 54149 | 6.02 | 47.0 | 44.5 | 0.0 | 1995-1995 |
| NYISO | 61488 | 8.13 | 7.5 | 1.8 | 1.8 | 2016-2016 |
| PJM | 58375 | 3.95 | 3.6 | 1.1 | 1.1 | 1998-2015 |
| PJM | 59860 | 5.00 | 15.0 | 4.5 | 4.5 | 2015-2015 |
| PJM | 10123 | 5.06 | 10.6 | 2.5 | 2.5 | 2004-2004 |
| PJM | 58195 | 5.09 | 7.0 | 2.2 | 2.2 | 2011-2011 |
| PJM | 58140 | 5.22 | 13.2 | 4.1 | 3.5 | 2003-2004 |
| PJM | 52149 | 5.32 | 70.7 | 18.9 | 18.9 | 1989-2001 |
| PJM | 54044 | 5.36 | 52.5 | 16.9 | 14.5 | 1993-2002 |
| PJM | 54829 | 5.39 | 9.5 | 2.6 | 2.6 | 1992-1992 |
| PJM | 50411 | 5.59 | 10.5 | 3.6 | 0.0 | 1989-1989 |
| PJM | 58328 | 5.67 | 12.4 | 3.5 | 2.9 | 2003-2005 |
| PJM | 59794 | 5.85 | 3.5 | 1.1 | 0.0 | 2003-2003 |
| PJM | 10129 | 5.98 | 24.4 | 7.8 | 0.0 | 1988-1988 |
| PJM | 55247 | 6.65 | 564.0 | 480.0 | 0.0 | 2001-2002 |
| PJM | 50094 | 6.97 | 6.0 | 0.6 | 0.0 | 1983-1983 |
| PJM | 66393 | 7.95 | 4.8 | 4.5 | 0.0 | 2021-2021 |
| PJM | 63478 | 8.28 | 4.6 | 1.1 | 1.1 | 2016-2016 |
| PJM | 58811 | 8.43 | 22.0 | 21.0 | 0.0 | 2016-2016 |
| PJM | 59056 | 8.43 | 3.8 | 3.8 | 0.0 | 2013-2013 |
| PJM | 60387 | 8.47 | 380.0 | 314.0 | 0.0 | 2023-2023 |
| PJM | 63483 | 8.56 | 5.5 | 1.6 | 0.0 | 2012-2012 |
| PJM | 56462 | 8.67 | 29.5 | 27.0 | 0.0 | 2005-2005 |
| PJM | 63485 | 8.81 | 5.6 | 2.5 | 0.0 | 1997-1997 |
| PJM | 58813 | 8.98 | 21.0 | 20.4 | 0.0 | 2017-2017 |
| SPP | 57881 | 3.43 | 897.3 | 763.0 | 763.0 | 2013-2025 |
| SPP | 55064 | 4.81 | 243.9 | 141.9 | 141.9 | 1999-2005 |
| SPP | 56478 | 4.96 | 13.3 | 7.3 | 7.3 | 2007-2007 |
| SPP | 1137 | 7.93 | 15.6 | 13.6 | 13.6 | 1946-1969 |
| SPP | 56606 | 8.07 | 108.2 | 85.0 | 85.0 | 2010-2010 |
| SPP | 56238 | 8.21 | 216.4 | 170.0 | 170.0 | 2006-2008 |
| SPP | 52122 | 8.51 | 23.4 | 5.5 | 5.5 | 1988-1988 |
| SPP | 65295 | 8.67 | 69.0 | 55.2 | 55.2 | 2022-2022 |
| SPP | 59726 | 8.92 | 56.1 | 56.1 | 56.1 | 2017-2017 |

The per-plant list (eGRID rate, nameplate, fleet MW, MW actually below the floor on the carried rows — the CAMPD loaded
rates already sit above 9.0 wherever `measured_ct_heat_rates` is armed): `summary_pre.md` §"Seam 2 plants". Pioneer 57881
(3.43, 763 MW carried against 897 MW nameplate in the 2025 vintage / 427 MW in 2024) is the largest single row in the
repository; Groton 56238 (8.21), Culbertson 56606 (8.07) and the 8.5–8.9 plants are the near-floor cohort — reported
separately so the desk can see that the floor also touches plausibly-efficient plants, at ≤ 0.9 MMBtu/MWh.

---

## 5. THE PREDICTED MARGINAL-COST DELTA PER ISO (zero LP, from the arrays alone)

`mc' = mc + hr × (fuel' − fuel) + (hr' − hr) × fuel'` on the touched rows. "Δmc cap-wtd (class)" is the availability-
weighted mean over the WHOLE class (what the merit order sees); "on touched rows" is the same over the rows that move.
"predicted ΔTWh" is the pooled-zone re-clearing predictor — the keeper's hourly thermal dispatch (committed sidecar)
re-cleared against the re-priced stack; it reproduces each keeper's class totals to a few TWh and is read for DIRECTION
and ORDER OF MAGNITUDE only, never matched. The ERCOT row is seam 2 alone (seam 1 unreachable).

## Predicted marginal-cost delta and re-clearing response (zero LP)

| ISO | year | class | rows / MW | rows / MW touched | Δmc cap-wtd (class) $/MWh | Δmc on touched rows | keeper TWh | predicted ΔTWh |
|---|---|---|---|---|---|---|---|---|
| CAISO | 2023 | CC_CHP | 129 / 1,689 | 0 / 0 | +0.00 | +0.00 | 8.48 | +0.00 |
| CAISO | 2023 | CC_REGULAR | 266 / 15,285 | 36 / 1,702 | +0.00 | +0.02 | 48.40 | +0.00 |
| CAISO | 2023 | CT_CHP | 195 / 991 | 0 / 0 | +0.00 | +0.00 | 1.24 | +0.00 |
| CAISO | 2023 | CT_PEAKER | 828 / 7,528 | 1 / 11 | +0.01 | +4.44 | 2.04 | -0.00 |
| CAISO | 2023 | ST_GAS | 25 / 3,777 | 0 / 0 | +0.00 | +0.00 | 0.12 | +0.00 |
| CAISO | 2023 | COAL | — | — | — | — | 0.09 | +0.00 |
| CAISO | 2023 | import | — | — | — | — | 37.37 | +0.00 |
| CAISO | 2023 | nuclear | — | — | — | — | 17.63 | +0.00 |
| CAISO | 2023 | oil | — | — | — | — | 0.00 | +0.00 |
| CAISO | 2024 | CC_CHP | 129 / 1,689 | 0 / 0 | +0.00 | +0.00 | 7.53 | -0.00 |
| CAISO | 2024 | CC_REGULAR | 266 / 15,285 | 19 / 929 | +0.00 | +0.03 | 46.10 | +0.00 |
| CAISO | 2024 | CT_CHP | 194 / 989 | 0 / 0 | +0.00 | +0.00 | 1.23 | +0.00 |
| CAISO | 2024 | CT_PEAKER | 834 / 7,535 | 1 / 11 | +0.00 | +2.33 | 1.67 | -0.00 |
| CAISO | 2024 | ST_GAS | 25 / 3,777 | 0 / 0 | +0.00 | +0.00 | 0.19 | +0.00 |
| CAISO | 2024 | COAL | — | — | — | — | 0.05 | +0.00 |
| CAISO | 2024 | import | — | — | — | — | 39.15 | +0.00 |
| CAISO | 2024 | nuclear | — | — | — | — | 18.19 | +0.00 |
| CAISO | 2024 | oil | — | — | — | — | 0.00 | +0.00 |
| CAISO | 2025 | CC_CHP | 129 / 1,689 | 0 / 0 | +0.00 | +0.00 | 7.56 | +0.00 |
| CAISO | 2025 | CC_REGULAR | 266 / 15,285 | 12 / 370 | -0.00 | -0.11 | 40.33 | +0.00 |
| CAISO | 2025 | CT_CHP | 193 / 988 | 0 / 0 | +0.00 | +0.00 | 1.20 | +0.00 |
| CAISO | 2025 | CT_PEAKER | 840 / 7,539 | 1 / 11 | +0.00 | +2.67 | 0.79 | -0.00 |
| CAISO | 2025 | ST_GAS | 25 / 3,777 | 0 / 0 | +0.00 | +0.00 | 0.02 | +0.00 |
| CAISO | 2025 | COAL | — | — | — | — | 0.08 | -0.00 |
| CAISO | 2025 | import | — | — | — | — | 39.16 | -0.00 |
| CAISO | 2025 | nuclear | — | — | — | — | 17.48 | +0.00 |
| CAISO | 2025 | oil | — | — | — | — | 0.00 | +0.00 |
| ERCOT | 2024 | CC_CHP | 258 / 5,714 | 0 / 0 | +0.00 | +0.00 | 28.64 | +0.07 |
| ERCOT | 2024 | CC_REGULAR | 643 / 33,120 | 0 / 0 | +0.00 | +0.00 | 144.19 | +0.35 |
| ERCOT | 2024 | CT_CHP | 162 / 965 | 55 / 228 | +1.13 | +4.83 | 5.20 | -0.39 |
| ERCOT | 2024 | CT_PEAKER | 700 / 8,378 | 1 / 1 | +0.00 | +0.03 | 8.05 | +0.09 |
| ERCOT | 2024 | ST_CHP | 2 / 9 | 0 / 0 | +0.00 | +0.00 | 0.07 | +0.00 |
| ERCOT | 2024 | ST_GAS | 205 / 12,391 | 3 / 626 | +0.08 | +2.53 | 19.09 | -0.26 |
| ERCOT | 2024 | COAL | — | — | — | — | 57.04 | +0.13 |
| ERCOT | 2024 | nuclear | — | — | — | — | 38.29 | +0.00 |
| ERCOT | 2024 | oil | — | — | — | — | 0.01 | -0.00 |
| ERCOT | 2025 | CC_CHP | 258 / 5,714 | 0 / 0 | +0.00 | +0.00 | 28.19 | +0.06 |
| ERCOT | 2025 | CC_REGULAR | 626 / 32,984 | 0 / 0 | +0.00 | +0.00 | 141.66 | +0.36 |
| ERCOT | 2025 | CT_CHP | 162 / 965 | 55 / 228 | +1.60 | +6.83 | 4.86 | -0.43 |
| ERCOT | 2025 | CT_PEAKER | 717 / 8,514 | 1 / 1 | +0.00 | +0.08 | 6.98 | +0.01 |
| ERCOT | 2025 | ST_CHP | 2 / 9 | 0 / 0 | +0.00 | +0.00 | 0.07 | +0.00 |
| ERCOT | 2025 | ST_GAS | 205 / 12,391 | 3 / 626 | +0.03 | +3.33 | 15.50 | -0.04 |
| ERCOT | 2025 | COAL | — | — | — | — | 64.87 | +0.04 |
| ERCOT | 2025 | nuclear | — | — | — | — | 41.30 | +0.00 |
| ERCOT | 2025 | oil | — | — | — | — | 0.00 | +0.00 |
| MISO | 2023 | CC_CHP | 68 / 3,833 | 0 / 0 | +0.00 | +0.00 | 19.32 | -1.29 |
| MISO | 2023 | CC_REGULAR | 333 / 27,993 | 40 / 3,284 | -0.24 | -2.18 | 138.60 | -4.07 |
| MISO | 2023 | CT_CHP | 114 / 896 | 44 / 218 | +1.95 | +7.97 | 5.51 | -0.67 |
| MISO | 2023 | CT_PEAKER | 757 / 22,654 | 81 / 3,830 | -27.10 | -164.46 | 14.05 | +13.35 |
| MISO | 2023 | ST_CHP | 88 / 710 | 0 / 0 | +0.00 | +0.00 | 2.66 | -0.13 |
| MISO | 2023 | ST_GAS | 127 / 11,650 | 20 / 3,788 | -10.88 | -45.82 | 19.89 | -1.22 |
| MISO | 2023 | COAL | — | — | — | — | 180.53 | -3.16 |
| MISO | 2023 | import | — | — | — | — | 44.22 | -2.80 |
| MISO | 2023 | nuclear | — | — | — | — | 86.99 | +0.00 |
| MISO | 2023 | oil | — | — | — | — | 0.00 | +0.00 |
| MISO | 2024 | CC_CHP | 64 / 3,621 | 0 / 0 | +0.00 | +0.00 | 20.63 | -1.42 |
| MISO | 2024 | CC_REGULAR | 341 / 28,316 | 68 / 6,293 | +0.01 | +0.07 | 150.12 | -4.56 |
| MISO | 2024 | CT_CHP | 114 / 896 | 44 / 218 | +1.77 | +7.24 | 5.71 | -0.71 |
| MISO | 2024 | CT_PEAKER | 757 / 22,654 | 72 / 4,350 | -16.58 | -83.65 | 17.46 | +11.50 |
| MISO | 2024 | ST_CHP | 87 / 704 | 3 / 73 | -0.27 | -8.73 | 2.89 | -0.10 |
| MISO | 2024 | ST_GAS | 131 / 11,657 | 32 / 5,760 | -11.31 | -25.12 | 18.74 | +0.21 |
| MISO | 2024 | COAL | — | — | — | — | 168.77 | -2.56 |
| MISO | 2024 | import | — | — | — | — | 28.92 | -2.36 |
| MISO | 2024 | nuclear | — | — | — | — | 90.02 | +0.00 |
| MISO | 2024 | oil | — | — | — | — | 0.02 | -0.00 |
| MISO | 2025 | CC_CHP | 64 / 3,621 | 0 / 0 | +0.00 | +0.00 | 18.56 | -1.03 |
| MISO | 2025 | CC_REGULAR | 341 / 27,747 | 37 / 3,244 | -0.21 | -1.99 | 135.96 | -2.74 |
| MISO | 2025 | CT_CHP | 114 / 896 | 44 / 218 | +2.68 | +10.95 | 5.72 | -0.64 |
| MISO | 2025 | CT_PEAKER | 755 / 22,650 | 50 / 2,972 | -13.71 | -100.06 | 19.01 | +8.52 |
| MISO | 2025 | ST_CHP | 87 / 700 | 3 / 73 | -0.21 | -5.19 | 1.99 | -0.07 |
| MISO | 2025 | ST_GAS | 131 / 11,657 | 16 / 2,426 | -3.55 | -29.06 | 18.41 | -0.11 |
| MISO | 2025 | COAL | — | — | — | — | 201.93 | -2.67 |
| MISO | 2025 | import | — | — | — | — | 21.06 | -1.26 |
| MISO | 2025 | nuclear | — | — | — | — | 90.45 | +0.00 |
| MISO | 2025 | oil | — | — | — | — | 0.02 | -0.00 |
| NEISO | 2023 | CC_CHP | 19 / 321 | 0 / 0 | +0.00 | +0.00 | 0.66 | +0.00 |
| NEISO | 2023 | CC_REGULAR | 230 / 15,651 | 7 / 372 | +0.00 | +10.17 | 52.70 | +0.08 |
| NEISO | 2023 | CT_CHP | 40 / 72 | 14 / 30 | +4.58 | +10.87 | 0.45 | -0.08 |
| NEISO | 2023 | CT_PEAKER | 95 / 1,209 | 0 / 0 | +0.00 | +0.00 | 0.29 | +0.00 |
| NEISO | 2023 | ST_CHP | 10 / 23 | 0 / 0 | +0.00 | +0.00 | 0.17 | +0.00 |
| NEISO | 2023 | ST_GAS | 32 / 173 | 0 / 0 | +0.00 | +0.00 | 0.13 | +0.00 |
| NEISO | 2023 | COAL | — | — | — | — | 0.07 | +0.00 |
| NEISO | 2023 | nuclear | — | — | — | — | 23.16 | +0.00 |
| NEISO | 2023 | oil | — | — | — | — | 0.31 | +0.00 |
| NEISO | 2024 | CC_CHP | 19 / 321 | 0 / 0 | +0.00 | +0.00 | 0.97 | +0.00 |
| NEISO | 2024 | CC_REGULAR | 230 / 15,651 | 7 / 372 | +0.01 | +0.32 | 56.87 | +0.07 |
| NEISO | 2024 | CT_CHP | 43 / 75 | 14 / 30 | +4.65 | +11.51 | 0.47 | -0.07 |
| NEISO | 2024 | CT_PEAKER | 92 / 1,199 | 0 / 0 | +0.00 | +0.00 | 0.78 | +0.01 |
| NEISO | 2024 | ST_CHP | 12 / 24 | 0 / 0 | +0.00 | +0.00 | 0.17 | +0.00 |
| NEISO | 2024 | ST_GAS | 25 / 168 | 0 / 0 | +0.00 | +0.00 | 0.05 | +0.00 |
| NEISO | 2024 | COAL | — | — | — | — | 0.12 | +0.00 |
| NEISO | 2024 | nuclear | — | — | — | — | 26.48 | +0.00 |
| NEISO | 2024 | oil | — | — | — | — | 0.25 | +0.00 |
| NEISO | 2025 | CC_CHP | 19 / 321 | 0 / 0 | +0.00 | +0.00 | 0.55 | +0.00 |
| NEISO | 2025 | CC_REGULAR | 230 / 15,651 | 0 / 0 | +0.00 | +0.00 | 58.65 | +0.09 |
| NEISO | 2025 | CT_CHP | 43 / 75 | 14 / 30 | +9.31 | +23.06 | 0.45 | -0.10 |
| NEISO | 2025 | CT_PEAKER | 92 / 1,199 | 0 / 0 | +0.00 | +0.00 | 1.61 | +0.01 |
| NEISO | 2025 | ST_CHP | 12 / 24 | 0 / 0 | +0.00 | +0.00 | 0.10 | +0.00 |
| NEISO | 2025 | ST_GAS | 25 / 168 | 0 / 0 | +0.00 | +0.00 | 0.06 | +0.00 |
| NEISO | 2025 | COAL | — | — | — | — | 0.21 | +0.00 |
| NEISO | 2025 | nuclear | — | — | — | — | 27.61 | +0.00 |
| NEISO | 2025 | oil | — | — | — | — | 1.63 | +0.00 |
| NYISO | 2023 | CC_CHP | 108 / 3,654 | 0 / 0 | +0.00 | +0.00 | 15.91 | +0.00 |
| NYISO | 2023 | CC_REGULAR | 122 / 7,406 | 0 / 0 | +0.00 | +0.00 | 33.80 | +0.00 |
| NYISO | 2023 | CT_CHP | 25 / 371 | 10 / 10 | +0.11 | +5.70 | 1.53 | -0.01 |
| NYISO | 2023 | CT_PEAKER | 128 / 3,020 | 0 / 0 | +0.00 | +0.00 | 0.40 | +0.00 |
| NYISO | 2023 | ST_CHP | 5 / 324 | 0 / 0 | +0.00 | +0.00 | 1.37 | +0.00 |
| NYISO | 2023 | ST_GAS | 88 / 8,902 | 0 / 0 | +0.00 | +0.00 | 9.81 | +0.00 |
| NYISO | 2023 | demand_response | — | — | — | — | nan | +0.00 |
| NYISO | 2023 | import | — | — | — | — | 23.34 | +0.01 |
| NYISO | 2023 | nuclear | — | — | — | — | 27.49 | +0.00 |
| NYISO | 2023 | oil | — | — | — | — | 0.15 | +0.00 |
| NYISO | 2024 | CC_CHP | 107 / 3,649 | 0 / 0 | +0.00 | +0.00 | 19.57 | +0.00 |
| NYISO | 2024 | CC_REGULAR | 129 / 7,417 | 0 / 0 | +0.00 | +0.00 | 36.97 | +0.01 |
| NYISO | 2024 | CT_CHP | 22 / 368 | 7 / 7 | +0.11 | +5.55 | 1.20 | -0.01 |
| NYISO | 2024 | CT_PEAKER | 130 / 3,024 | 2 / 4 | +0.00 | +9.64 | 0.37 | -0.00 |
| NYISO | 2024 | ST_CHP | 5 / 324 | 0 / 0 | +0.00 | +0.00 | 1.13 | +0.00 |
| NYISO | 2024 | ST_GAS | 88 / 8,902 | 0 / 0 | +0.00 | +0.00 | 8.54 | +0.00 |
| NYISO | 2024 | demand_response | — | — | — | — | nan | +0.00 |
| NYISO | 2024 | import | — | — | — | — | 20.71 | +0.01 |
| NYISO | 2024 | nuclear | — | — | — | — | 26.95 | +0.00 |
| NYISO | 2024 | oil | — | — | — | — | 0.44 | +0.00 |
| NYISO | 2025 | CC_CHP | 107 / 3,649 | 0 / 0 | +0.00 | +0.00 | 20.39 | +0.01 |
| NYISO | 2025 | CC_REGULAR | 129 / 7,417 | 0 / 0 | +0.00 | +0.00 | 35.33 | +0.01 |
| NYISO | 2025 | CT_CHP | 22 / 368 | 7 / 7 | +0.21 | +10.58 | 1.68 | -0.01 |
| NYISO | 2025 | CT_PEAKER | 130 / 3,024 | 2 / 4 | +0.03 | +18.26 | 1.33 | -0.02 |
| NYISO | 2025 | ST_CHP | 5 / 324 | 0 / 0 | +0.00 | +0.00 | 1.45 | +0.00 |
| NYISO | 2025 | ST_GAS | 88 / 8,902 | 0 / 0 | +0.00 | +0.00 | 9.33 | +0.00 |
| NYISO | 2025 | demand_response | — | — | — | — | nan | +0.00 |
| NYISO | 2025 | import | — | — | — | — | 19.36 | +0.01 |
| NYISO | 2025 | nuclear | — | — | — | — | 28.34 | +0.00 |
| NYISO | 2025 | oil | — | — | — | — | 1.28 | +0.00 |
| PJM | 2023 | CC_CHP | 71 / 1,539 | 0 / 0 | +0.00 | +0.00 | 8.58 | -0.03 |
| PJM | 2023 | CC_REGULAR | 543 / 59,857 | 32 / 5,331 | -0.13 | -1.63 | 322.29 | -0.57 |
| PJM | 2023 | CT_CHP | 105 / 313 | 24 / 54 | +0.47 | +2.73 | 1.29 | -0.12 |
| PJM | 2023 | CT_PEAKER | 838 / 25,996 | 24 / 1,994 | -1.15 | -14.69 | 19.36 | -0.85 |
| PJM | 2023 | ST_CHP | 38 / 178 | 0 / 0 | +0.00 | +0.00 | 0.99 | -0.00 |
| PJM | 2023 | ST_GAS | 64 / 11,094 | 8 / 1,250 | -17.02 | -247.99 | 10.83 | +2.08 |
| PJM | 2023 | COAL | — | — | — | — | 112.61 | -0.42 |
| PJM | 2023 | import | — | — | — | — | -27.47 | -0.08 |
| PJM | 2023 | nuclear | — | — | — | — | 272.02 | +0.00 |
| PJM | 2023 | oil | — | — | — | — | 0.00 | +0.00 |
| PJM | 2024 | CC_CHP | 71 / 1,539 | 0 / 0 | +0.00 | +0.00 | 8.05 | -0.03 |
| PJM | 2024 | CC_REGULAR | 543 / 59,857 | 15 / 2,430 | -0.06 | -1.40 | 335.65 | -0.49 |
| PJM | 2024 | CT_CHP | 102 / 309 | 24 / 54 | +0.42 | +2.42 | 1.54 | -0.09 |
| PJM | 2024 | CT_PEAKER | 845 / 26,003 | 16 / 1,239 | -0.87 | -17.93 | 20.56 | -0.10 |
| PJM | 2024 | ST_CHP | 37 / 177 | 0 / 0 | +0.00 | +0.00 | 1.10 | -0.00 |
| PJM | 2024 | ST_GAS | 68 / 11,106 | 4 / 460 | -6.86 | -91.57 | 10.85 | +0.95 |
| PJM | 2024 | COAL | — | — | — | — | 114.18 | -0.20 |
| PJM | 2024 | import | — | — | — | — | -20.45 | -0.03 |
| PJM | 2024 | nuclear | — | — | — | — | 270.59 | +0.00 |
| PJM | 2024 | oil | — | — | — | — | 0.00 | -0.00 |
| PJM | 2025 | CC_CHP | 71 / 1,539 | 0 / 0 | +0.00 | +0.00 | 6.78 | -0.03 |
| PJM | 2025 | CC_REGULAR | 543 / 59,857 | 30 / 3,188 | -0.03 | -0.58 | 334.33 | -0.43 |
| PJM | 2025 | CT_CHP | 103 / 310 | 24 / 54 | +0.62 | +3.56 | 1.23 | -0.09 |
| PJM | 2025 | CT_PEAKER | 844 / 26,002 | 16 / 1,284 | -0.57 | -11.35 | 27.40 | -0.31 |
| PJM | 2025 | ST_CHP | 37 / 177 | 0 / 0 | +0.00 | +0.00 | 0.94 | -0.00 |
| PJM | 2025 | ST_GAS | 68 / 11,106 | 4 / 460 | -5.17 | -76.14 | 17.08 | +1.04 |
| PJM | 2025 | COAL | — | — | — | — | 142.77 | -0.14 |
| PJM | 2025 | import | — | — | — | — | -23.23 | -0.03 |
| PJM | 2025 | nuclear | — | — | — | — | 269.33 | +0.00 |
| PJM | 2025 | oil | — | — | — | — | 0.03 | -0.00 |
| SPP | 2023 | CC_CHP | 4 / 271 | 0 / 0 | +0.00 | +0.00 | 1.88 | +0.04 |
| SPP | 2023 | CC_REGULAR | 85 / 10,048 | 11 / 869 | -0.09 | -1.05 | 41.43 | +1.64 |
| SPP | 2023 | CT_CHP | 31 / 240 | 15 / 197 | +7.83 | +9.46 | 1.27 | -0.77 |
| SPP | 2023 | CT_PEAKER | 383 / 11,707 | 57 / 3,794 | -1.81 | -5.30 | 19.99 | -3.38 |
| SPP | 2023 | ST_CHP | 14 / 113 | 3 / 82 | +0.90 | +1.23 | 0.37 | -0.03 |
| SPP | 2023 | ST_GAS | 124 / 10,281 | 12 / 2,220 | -3.11 | -22.13 | 7.53 | +0.27 |
| SPP | 2023 | COAL | — | — | — | — | 70.62 | +2.23 |
| SPP | 2023 | nuclear | — | — | — | — | 16.93 | +0.00 |
| SPP | 2023 | oil | — | — | — | — | 0.00 | +0.00 |
| SPP | 2024 | CC_CHP | 4 / 271 | 0 / 0 | +0.00 | +0.00 | 1.81 | +0.07 |
| SPP | 2024 | CC_REGULAR | 85 / 10,048 | 23 / 2,747 | -2.88 | -10.90 | 37.66 | +5.00 |
| SPP | 2024 | CT_CHP | 23 / 210 | 11 / 155 | +7.85 | +10.64 | 1.21 | -0.40 |
| SPP | 2024 | CT_PEAKER | 389 / 11,754 | 60 / 4,299 | +0.77 | +2.00 | 25.97 | -7.47 |
| SPP | 2024 | ST_CHP | 14 / 113 | 0 / 0 | +0.00 | +0.00 | 0.38 | +0.06 |
| SPP | 2024 | ST_GAS | 124 / 10,281 | 28 / 4,504 | +2.47 | +4.79 | 14.99 | -3.98 |
| SPP | 2024 | COAL | — | — | — | — | 61.03 | +6.71 |
| SPP | 2024 | nuclear | — | — | — | — | 15.02 | +0.00 |
| SPP | 2024 | oil | — | — | — | — | 0.00 | -0.00 |
| SPP | 2025 | CC_CHP | 4 / 271 | 0 / 0 | +0.00 | +0.00 | 2.03 | +0.04 |
| SPP | 2025 | CC_REGULAR | 85 / 10,048 | 8 / 587 | +0.65 | +10.58 | 32.57 | +3.72 |
| SPP | 2025 | CT_CHP | 23 / 210 | 11 / 155 | +8.60 | +11.64 | 1.18 | -0.50 |
| SPP | 2025 | CT_PEAKER | 389 / 11,754 | 45 / 3,267 | +3.11 | +11.49 | 22.35 | -8.68 |
| SPP | 2025 | ST_CHP | 14 / 113 | 0 / 0 | +0.00 | +0.00 | 0.21 | +0.02 |
| SPP | 2025 | ST_GAS | 124 / 10,281 | 16 / 2,733 | +1.38 | +5.19 | 9.83 | -1.03 |
| SPP | 2025 | COAL | — | — | — | — | 83.20 | +6.44 |
| SPP | 2025 | nuclear | — | — | — | — | 15.78 | +0.00 |
| SPP | 2025 | oil | — | — | — | — | 0.00 | +0.00 |

| ISO | year | load-weighted marginal-price ratio (predictor) |
|---|---|---|
| CAISO | 2023 | 1.0001 |
| CAISO | 2024 | 1.0001 |
| CAISO | 2025 | 1.0000 |
| ERCOT | 2024 | 1.0020 |
| ERCOT | 2025 | 1.0012 |
| MISO | 2023 | 0.9687 |
| MISO | 2024 | 0.9610 |
| MISO | 2025 | 0.9749 |
| NEISO | 2023 | 1.0004 |
| NEISO | 2024 | 1.0005 |
| NEISO | 2025 | 1.0005 |
| NYISO | 2023 | 1.0000 |
| NYISO | 2024 | 1.0001 |
| NYISO | 2025 | 1.0002 |
| PJM | 2023 | 0.9951 |
| PJM | 2024 | 0.9972 |
| PJM | 2025 | 0.9980 |
| SPP | 2023 | 1.0162 |
| SPP | 2024 | 1.0558 |
| SPP | 2025 | 1.0575 |

**Reading, per ISO** (the line every desk acts on; a re-solve is owed wherever a keeper's inputs move):

- **SPP** — the SPP-46 object, reproduced: 2024 CT **−7.5 TWh**, ST_GAS −4.0 (Harrington's $1.48 months screened),
  CC +5.0, COAL +6.7 at a **+5.6 %** load-weighted level (SPP-46: CT −6.82 / ST −3.80 / CC +5.11 / COAL +5.34 at +4.4 %);
  2025 CT −8.7 (SPP-46 −8.70); 2023 CT −3.4. Both seams live; re-solve owed (SPP-50).
- **MISO** — the largest exposure in the repository and the OPPOSITE sign to SPP: MISO's flagged months are the HIGH tail
  (114 / 123 / 86 plant-months on 22–29 plants, median own print $8.7 against ~$3, up to $159 — fixed charges over
  low-burn months, the Riverside class), so the screen makes 4.5–5.1 GW of CT and 2.4–5.8 GW of ST_GAS **cheaper** by
  $70–140/MWh on the touched rows: predicted CT **+13.3 / +11.5 / +8.5 TWh**, CC −4 / −4.6 / −2.7, COAL −3.2 / −2.6 / −2.7,
  at a **−3.1 / −3.9 / −2.5 %** level. Seam 2: 46 rows / 230 MW. Re-solve owed; the MISO desk should read
  `seam1_plant_months_MISO_<year>.csv` before it does.
- **PJM** — 24 / 14 / 13 high months on 9 / 5 / 7 plants, 4.1–8.6 GW touched; ST_GAS cheaper by $76–248/MWh on 460–1,250 MW:
  predicted ST_GAS +2.1 / +1.0 / +1.0 TWh, CT −0.9 / −0.1 / −0.3, level ≈ −0.3 %. Seam 2: 24 rows / 54 MW. Re-solve owed
  (small, but the keeper's inputs move).
- **CAISO** — 3 / 7 / 6 high months on ≤ 3 plants, 1.7 / 0.9 / 0.4 GW touched (all CC), Δmc on touched rows −$16 / −$42 / −$13;
  predicted class energy moves < 0.1 TWh. Seam 2: 1 row / 11 MW. Re-solve owed on the letter (inputs move), inert in
  substance — the CAISO desk decides its cadence.
- **NEISO** — one plant (372 MW CC, one high month) in 2023–2024, nothing in 2025; seam 2: 14 rows / 30 MW of CT_CHP.
  Predicted moves < 0.1 TWh. Re-solve owed on the letter, inert in substance.
- **NYISO** — seam 1 INERT (all 60 own-reported months in band); seam 2: 9–10 rows / 10–11 MW. Predicted < 0.02 TWh.
  Re-solve owed on the letter only.
- **ERCOT** — seam 1 UNREACHABLE (keeper does not arm per-plant gas pricing; 61 / 46 high and 2 / 3 low months on
  10–11 plants reported "if armed"). Seam 2: **59 rows / 855 MW** below the floor at 13 simple-cycle-only plants (six
  below 6.0), predicted CT +0.4 / +0.1 TWh at a −0.5 / −0.3 % level. Re-solve owed for seam 2.

---

## 6. SPP-46's ATTRIBUTION, reproduced on the PRE arrays (`spp49/attribution.py`, `attribution_pre_<year>_<class>.csv`)

Same construction (model in-merit energy at keeper-3's own P1 prices, strict + ½ marginal, minus CAMPD gross), flags read
against THIS lane's reference (own state, US fallback, 1.036). 2024, GWh:

| class | group | SPP-46 (plants / MW / Δ) | this lane, pre (plants / MW / Δ) |
|---|---|---|---|
| CT_PEAKER | HR (Pioneer 57881) | 1 / 763 / **+5,013** | 1 / 763 / **+5,013** |
| CT_PEAKER | fuel_low | 6 / 1,894 / **+8,121** | 7 / 2,065 / **+8,963** (Elk +4,333, Mustang 4 +1,674, Jones +1,593, Cunningham +559, Maddox +515 — one more plant flagged under the own-state reference) |
| CT_PEAKER | clean | 110 / 7,080 / **−244** | 113 / 7,834 / −1,174 (the two lanes' clean cohorts differ by the plants each reference flags) |
| ST_GAS | fuel_low (Harrington) | 5 / 1,994 / **+6,136** | 5 / 1,994 / **+6,136** |
| ST_GAS | fuel_high | 3 / 2,751 / −3,801 | 2 / 2,511 / −3,688 |
| ST_GAS | clean | 23 / 5,536 / **−5,949** | 24 / 5,776 / **−6,062** |
| CC_REGULAR | fuel_low (Mustang CC, Redbud) | 2 / 1,898 / +2,222 | 2 / 1,898 / +2,222 |

The named rows reproduce to the GWh (Pioneer, Harrington, Mustang CC) or within the reference difference (the CT
fuel_low cohort). **What the repair must do, pre-registered**: on the POST arrays the HR group's Pioneer rows move by
≈ −5.0 TWh (3.43 → 9.0 on 763 MW), the CT fuel_low group by ≈ −8 TWh and ST_GAS fuel_low by ≈ −6 TWh (their $0.11–1.48
months → the TX/NM reference), while the clean cohorts move by < 0.5 TWh. If the post arrays do not move those rows by
roughly those amounts, the repair is not the one SPP-46 identified and the FINDING says so.

**Harrington (SPP-46 R-4, NOT this lane's)**: the screen replaces its eight 2024 own months at $0.32–1.52 by the TX
reference ($1.45–2.97), which removes the $1.48 "gas" that ran 5.8 TWh of coal-fired steam as ST_GAS — it does NOT
change the fuel the plant burns, the bench's ST_GAS grouping of its coal generation, or the 2025 conversion date. Reported
in the FINDING at full magnitude; the vintage seam stays with the desk (R-ax).

---

## 7. THE STOP CONDITIONS (this lane has no screen solve; these are its own kill rules)

| # | condition | bar | consequence |
|---|---|---|---|
| S1 | ex-post key census (after the edit, `--check-live`) | 18 moves, 0 off-target, pinned default / backcast literals unmoved | any other count → the edit is wrong, fix before push |
| S2 | ex-post arrays reproduce the ex-ante arithmetic on own-reported rows | every touched own-reported cell equals `R`; every in-band cell byte-identical | a mismatch is an implementation defect |
| S3 | SPP-46 rows move as §6 pre-registers | Pioneer ≈ −5 TWh, CT fuel_low ≈ −8, ST fuel_low ≈ −6, clean < 0.5 | else "not the repair SPP-46 identified", said plainly |
| S4 | the seven gates at their baseline exit codes | all 0 except `check_gate_a_provenance` 1 on ERCOT + MISO only | a third ISO or any new red → fix before the PR |
| S5 | full unit suite (fast lane) green, plus the new tests | green | red → fix |

Nothing here is a criterion on any residual; no C1/C3 number is read by this lane.
