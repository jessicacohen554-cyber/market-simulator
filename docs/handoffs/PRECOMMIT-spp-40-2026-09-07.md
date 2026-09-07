# PRECOMMIT — SPP-40: the first SPP solve, the rule-29 screen, and the first keeper

**Lane** SPP-40 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-40-first-solve-pvanrx` · **Data profile** `spp` ·
**Charter** plan §8 W4 (`docs/multi-iso/spp-addition-plan-2026-09.md`), §3 card **P7** as ruled
(*"Control = none; screen 2024, structural STOP gate only"*), §5 row SPP-40, §7 G4 / G5 / G13.
**Predecessors** `FINDING-spp-30/31-2026-09-07.md`, the SPP-32 commits (`6d74a154` `6ab584ef`
`67dca44f` `7cdd7497` `bd2c48f7` `ed44a18c` — no FINDING doc was committed for SPP-32),
`FINDING-spp-53-2026-09-07.md` §0 / §4 / §5.4 / §6.

**Pushed before any solve.** Every number below is zero-LP: a 168-hour smoke, a 24-hour
full-pipeline recipe dump (its `run_config.json` is the recipe), and three on-recipe
`run_year(fleet_only=True)` rebuilds (rule 29(0)). The STOP gate, the screen year, the recipe and
the ledger are fixed here; nothing is revised after a solve is read, and a miss of any declared
condition is reported at full magnitude in the FINDING.

---

## 0. THE PIN and the preconditions

```
fbe0e83ff0a438508811009e470094ded0efbc40   origin/main at PRECOMMIT time (branch base)
a24da78f                                   this lane's one pre-solve code commit (§2.2)
```

| precondition | check | result |
|---|---|---|
| SPP-30 landed | `git log origin/main --grep=SPP-30` | `502d8be9` `0f3e54e4` `ecd10c7f` — **yes** |
| SPP-31 landed | `--grep=SPP-31` | `6f8910ca` `3b676963` `42231a86` `75a7563c` — **yes** |
| SPP-32 landed | `--grep=SPP-32` | six commits (above) — **yes**; no FINDING doc exists for it |
| SPP-53 landed (P13) | `--grep=SPP-53` | `5486b46f` `74bbad03` — **yes** |
| **P13 asserted**: `get_iso_config("SPP").links[0].ttc_mw` | run in-session | **3400.0** (SPP-North ↔ SPP-South), never 48,700 |
| rule 22 markers | `calibration-complete.json` | SPP in neither `complete` nor `final` — the training window 2023–2025 is the whole spend; no held-out year is touched |
| rule 12 concurrency | `ps` for `run_calibration` | **0** other per-plant solves running in this environment |
| data hydrated | `hydrate_data.py --list` | `spp` profile present (1,748 files, 1.3 GB); the smoke found every input |
| machine | `free -g` / `nproc` | 15 GB RAM, 4 CPUs, 20 GB free disk |

STOP condition G4 (*"solving before outages / benchmarks / zonal shares exist"*) does **not**
fire: the 24-hour full-pipeline run resolved `campd-unit-outages-SPP.csv` (sha256 `735d27fe…`),
`thermal_tranches_SPP.csv` (`fdeadb1a…`), the per-zone wind shape
(`spp_2024_wind_zone_shape.parquet`, night/afternoon ratio N 0.96 / S 1.06), the served EIA-930
interchange (+186 MW avg 2024), the zonal sub-BA demand shapes, and SPP's blocks in
`calibration_reference.json` / `actual_lmp.json` / `actual_tail.json`.

---

## 1. The screen year: **2024** (P7 as ruled) — and why nothing overrides it

P7's zero-LP statistic is the largest mean |N−S| hub spread. SPP-14 §3.2 computed it from the
per-hub hourly parquet; re-computed here from the committed
`actual_lmp_hourly_zonal_SPP.parquet`:

| year | mean \|S−N\| RT | hours S > N+$5 | hours N > S+$5 | signed mean (S−N) |
|---|---:|---:|---:|---:|
| 2023 | $12.13 | 2,655 | 1,696 | +$1.95 |
| **2024** | **$17.23** | **2,951** | 1,751 | +$8.42 |
| 2025 | $15.18 | 2,634 | 2,454 | +$0.15 |

2024 is first on the mean and on the p90 (SPP-14: $41.36 vs $28.49 / $36.25), in both markets.
The margin over 2025 is 13 % (thin, as SPP-14 §3.3 qualified), and 2025's near-zero signed spread is
two-sided cancellation, not absence of separation. **Screen year = 2024.** It is also the year the
N↔S mechanism's own measured footprint is largest, which is what rule 29(a) asks for — never the
year with the largest residual (there is no residual yet).

**The hub-spread limitation, stated as P7 requires (audit §6.1):** `SPPNORTH_HUB` is a cluster of
pricing nodes *"generally in Nebraska"* and `SPPSOUTH_HUB` *"generally in central Oklahoma"* (SPP's
own hub definitions, transcribed in `docs/multi-iso/spp-data-audit.md` §6.1). The N−S hub spread is
therefore a **Nebraska-vs-central-Oklahoma two-point spread**, not a zone-vs-zone price difference,
and the model's `SPP-North`/`SPP-South` zonal duals are load-weighted bubble prices over 12 and 5
sub-BAs. The spread screens the link's **direction and season** here and is never read as a zonal
price validation; `actual_lmp.json`'s per-hub `zones` records carry the same caveat in every entry
(SPP-31 §1.3).

---

## 2. The recipe — every value fixed before the solve

### 2.1 The invocation

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2024 \
    --out-dir results/calibration/_spp40_screen --note "spp-40 screen 2024 (rule 29(a); deleted before merge)"
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 2024 2025 \
    --out-dir results/calibration/spp40_baseline_B --note "spp-40 first SPP solve: all-defaults baseline, N<->S link 3,400 MW (SPP-53), served EIA-930 interchange (P2)"
```

No other flag. The W4 charter text says `--commitment`; that flag is the ARCHIVED P2 pass, hidden
and inert unless `--enable-legacy-p2` is passed (CLAUDE.md "Dispatch & Commitment"; the CLI help
says so verbatim), and no keeper uses it — so it is **omitted**, and the run is the production P0→P1
pair like every other ISO's keeper (`passes: ["P1"]`, `commitment: false`). Years run
**sequentially in one invocation** (rule 12), one bundle (rule 16).

### 2.2 What the recipe is (the 24-hour dump, `run_config.json` at `a24da78f`)

818 `ScenarioConfig` fields; **28 differ from the dataclass defaults**, every one of them set by the
calibration CLI's ISO-agnostic backcast construction (`pipeline/backcast_config.py`) — none by this
lane, except the one rule-25 item below:

| field | recipe value | dataclass default | why |
|---|---|---|---|
| `mode` / `iso` / `hours` | backcast / SPP / 8760 | forecast / ERCOT / 8760 | the backcast construction |
| `plant_level_fleet`, `cc_committed_per_plant`, `cc_peaking_per_plant`, `cc_duct_peaking`, `coal_mustrun_per_plant`, `chp_steam_following` | true | false | per-plant fleet + measured CAMPD tranche structure (SPP-30's `thermal_tranches_SPP.csv`, 118 plant-groups) |
| `outage_source` / `historic_outage_overlay` / `coal_drop_pof` / `correlated_forced_outage` | historic / false / true / false | statistical / true / false / true | measured unit-level outage windows (SPP-30: 85.3 % of qualifying plants, 97.9 % of MW) in place of statistical draws |
| `gas_plant_monthly_fuel_pricing`, `nearby_fuel_price_fallback`, `gas_st_startup_spread` | true | false | measured EIA-923 delivered fuel (F923: 462 generators own-plant, 749–872 gap-filled from state/zone) |
| `gas_price_override` | 2.54 / 2.19 / 3.52 by year | None | measured Henry Hub |
| `coal_prb_passthrough_sigmoid`, `coal_prb_passthrough_tiered` | true | false | CLI defaults; **inert for SPP** — SPP coal carries `plant_group` `COAL` (no `COAL_PRB` class), the DOF builder lists no engaged sigmoid, and the must-run tranche prices at VOM only (§2.3) |
| `cc_capacity_reconcile_path` | `cc_capacity_reconcile_SPP.csv` | ERCOT file | ISO-keyed |
| `rps_enabled` / `datacenter_load_path` / `entry_lookahead_reprice` / `storage_entry_*` / `capacity_market_clearing_by_iso` | false / off / false / false / None | forecast defaults | forecast-only machinery a backcast never enters |
| `wefor_multiplier` | **0.7** | 1.0 | the CLI's non-MISO default (`backcast_config.py:1499`); an inherited generic value — ledgered in §6, **not** re-chosen here |
| `offer_curve_by_group` | 13 groups | {} | **every band SPP carries is 1.0** — see §2.3 |

The complete field set is carried by the bundle's committed `run_config.json`; the table is the
delta from the dataclass so a reader can audit it without diffing 818 keys.

### 2.3 Offer arrays — rule 25 measured at the LP's own objective, and the one correction

The phase-0 offer census reads `mc_base` (the assembled P0 objective the LP solves on) per tranche
and divides by the plant's `heat_rate × delivered fuel + VOM`; and, independently, each coal plant's
tranche heat rates against its must-run tranche (the unscaled base):

| class (SPP-carried) | bands present | multiplier measured | at `fbe0e83f` (main) |
|---|---|---|---|
| CC_REGULAR, CC_CHP, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP | committed / econlo / econhi / peak | **1.0 exactly** on every band, every plant | 1.0 (the generic gas neutralization, `_neutralize_generic_gas_bands`) |
| COAL (214 units, 19,846 MW) | mustrun / committed / peak / unit | committed **0.90×**, peak **1.45×** the plant's base heat rate — the generic ERCOT-fitted `COAL` entry, applied through the tranche heat-rate scaling | **≠ 1.0 — rule 25 breached** |

SPP-30's rule-25 verification ("1.0 on every band") listed the five gas classes and did not
reach coal. The generic `COAL` bands are ERCOT-fitted (the `_MISO_OFFER_CURVE` comment names them
"the generic ERCOT-fitted coal bands" and MISO replaced them for MISO on 2026-07-10). Rule 25 —
*"generic fallbacks carry neutral (1.0) bands"* — and this charter — *"no offer_curve_by_group band
!= 1.0"* — are unambiguous, so this lane's ONE pre-solve code change (`a24da78f`) adds
`_SPP_OFFER_CURVE = {"COAL": committed/econ_low/econ_high/peak = 1.0}` deep-merged for
`iso == "SPP"` only, beside the NYISO/CAISO/MISO/NEISO merge curves. Verified after the change:
config `COAL` bands 1.0/1.0/1.0/1.0; coal tranche heat-rate ratio vs the must-run tranche median
**1.00** on committed / peak / unit (a few plant-specific residual ratios 0.95–1.55 remain from the
per-plant tranche derive's own measured heat rates, not from any band); every gas band still 1.0.
It is the identity, declared before any solve, read against no residual: **zero DOF**. Every other
ISO is byte-identical — `solve_surface_register.py --diff origin/main HEAD`: `297 -> 297 names; 0
value(s) moved`; the generic entry is untouched because PJM / CAISO / NEISO / NYISO keep it by
design. Unit test `tests/unit/pipeline/test_backcast_config.py::TestSppNeutralCoalBands` pins both
halves; `tests/unit/config` + `tests/unit/pipeline` 1,076 passed.

The coal must-run tranche offers at VOM only (mc $4.50/MWh, fuel treated as sunk on the measured
must-run share) — the `coal_mustrun_per_plant` construction every ISO shares; the must-run /
committed / peak **shares** are SPP-30's measured CAMPD values (rule 23) and are not bands.

**`authorized_price_tuning = NONE.`** No band is tuned on price; there is nothing to declare under
rule 1's carve-out, and the attestation says so explicitly (C6 reads the declaration).

### 2.4 Fleet census (zero-LP, 2024 rebuild; 2023/2025 differ only by COD/retirement masks)

| class | units | MW | North MW | South MW |
|---|---:|---:|---:|---:|
| COAL | 214 | 19,844 | 12,724 (19 plants) | 7,120 (11) |
| CC_REGULAR | 85 | 10,048 | 2,324 (7) | 7,724 (16) |
| CT_PEAKER | 389 | 11,755 | 7,888 (96) | 3,867 (29) |
| ST_GAS | 124 | 10,281 | 878 (12) | 9,403 (19) |
| nuclear | 2 | 1,945 | 1,945 (Wolf Creek, Cooper) | — |
| hydro (LP budget) | 22 | 3,078 | 2,580 | 498 |
| CC_CHP / CT_CHP / ST_CHP (grid tranches) | 4 / 23 / 14 | 271 / 210 / 113 | | |
| oil | 335 | 1,780 | 1,723 | 57 |
| wind (cap, EIA-860) | | 33,851 | 16,870 | 16,981 |
| solar (cap) | | 879 | 382 | 497 |

Demand served 2023/24/25: **284.5 / 290.9 / 301.8 TWh** (North 146.5 / 149.2 / 153.9; South 138.0 /
141.7 / 147.9), peak 54.6 / 53.9 / 57.2 GW. The served series equals EIA-930 `Demand` + the
measured `Total interchange` (+3.9 / +1.6 / +2.4 TWh net export) — P2's served schedule is live
(the 2023 identity holds once the P9 slip hour in `Demand` is removed: 280.6 + 3.9 = 284.5).
Wind potential 114.1 / 121.0 / 122.3 TWh (North 55.0 / 59.7 / 62.1; South 59.0 / 61.3 / 60.1) —
the uncurtailed HSL analogue from SPP-32's reference curtailment rate. Wind dispatch offer
**−$26/MWh** (the standing IRA/PTC dispatch credit every ISO's wind carries; `wind_ptc_vintage_offers`
default-off), solar $0. Nuclear is the only material `min_gen` floor (15.0–16.9 TWh/yr, mechanism 1);
CHP grid floors 1.25–1.28 TWh; **no coal or gas floor of any kind** — SPP-40 carries no reliability
floor, no commitment bridge, no ORDC seed (P4/P5 deferred).

The 2025 hydro budget reads **0.023 TWh** (one 7 MW unit vs 22 plants / 8.7 TWh in 2023–24): SPP-31
§1.2 already identified this as an EIA-923 preliminary-vintage artifact, not a dry year. It is an
input defect **stated here, not repaired**: 2025 hydro (8.8 TWh actual in EIA-930) will be missing
from the 2025 dispatch and C1 `hydro` 2025 will read at full magnitude.

---

## 3. The P7 STOP gate — structural, kill-only, residual-blind

The screen (2024) is graded on the four legs below and nothing else. It may kill the arm; it can
never promote it; no leg reads C1–C8. Each leg is written so that a reader could grade it from the
committed `hourly/` sidecars and `flows.parquet` alone.

**Leg A — the N↔S link binds, in the measured direction.** The residual-blind footprint
(phase-0, no LP): hours in which North's coal + nuclear capability (availability-weighted `pmax`)
plus its wind and solar potential exceeds North demand by more than the 3,400 MW TTC *while* the
South is in deficit on the same basis — **1,669 / 1,519 / 1,955 h** (2023/24/25), concentrated in
Sep–Apr (2024: Mar 276, Dec 202, Jun 145, Nov 138) and lightest in Jul (73–84 h); the reverse
(South surplus > TTC, North deficit) **38 / 27 / 44 h**. North carries 14,669 MW of coal+nuclear
against 11,242 MW of gas; South 7,119 vs 21,434. The corridor's measured hub separation is
South-dearer in 2,951 vs 1,751 hours (2024). So the arithmetic and the market agree on the sign:
**N→S is the dominant direction.**
- **STOP** if the link's N→S flow sits at the 3,400 MW bound in fewer than **1 % of 2024 hours
  (< 88 h)** — the link "never binds", the FINDING-spp-53 §5.4 case, routed to SPP-DESK card O-2
  (identification width 2,645–11,121 MW) — **the TTC is not moved**.
- **STOP** if S→N binding hours **exceed** N→S binding hours in 2024 — wrong direction, routed to
  O-1 (the asymmetric pair) / O-2.
- Reported, not gating: binding hours in each direction; the pooled mean and p90 of the link dual;
  where 2024's binding count falls against the 1,519 h footprint prediction (a direction-of-effect
  and order-of-magnitude check on the arithmetic above, not a target).

**Leg B — the season is the measured one.** The measured 2024 monthly mean RT (S−N) spread is
positive and largest in **Oct (+$32.2), Sep (+$24.0), Apr (+$12.0), Aug (+$10.3), Jan (+$9.0)**, and
negative in **Mar (−$4.0), Feb (−$1.1), Jul (−$0.5)**.
- **STOP** if the Spearman rank correlation between the model's monthly N→S binding-hour count (or
  monthly mean link dual, N→S positive) and the measured monthly (S−N) spread over the 12 months of
  2024 is **negative** — the link is binding in the wrong season.
- Reported: the correlation itself, and the model's monthly (South − North) zonal dual beside the
  measured hub spread (sign by month), with the two-point-spread caveat of §1 attached.

**Leg C — fuel mix within an order of magnitude of EIA-923.** EIA-923 2024 (calibration
reference): coal 65.09, gas_cc 46.25, gas_ct 15.28, gas_st 19.85, nuclear 15.30, wind 108.49
(EIA-930 basis), hydro 8.70, solar 1.65 TWh.
- **STOP** if any class with an actual ≥ 5 TWh lands outside **[0.1×, 10×]** of it (the charter's
  literal wording), or a class with units carries zero energy, or a zone carries zero load.
- Reported: every class ratio, and the factor-3 band as information (a factor-3 miss is a
  structural finding for the lever queue, never a kill and never a tuning target).

**Leg D — no unserved energy / negative-price absurdity.** Measured 2024 RT: 1,172 of 8,748 hours
negative (13.4 %), 212 below −$20, min −$36.03; 59 hours > $200, 1 hour > $1,000. The model's
negative-price floor is the wind offer (−$26) less the dump-cost ε.
- **STOP** if unserved energy (`Slack`) exceeds **0.05 % of annual load** or occurs in more than
  **50 hours** (VOLL $2,000 hours at that scale are a data absurdity, not scarcity).
- **STOP** if any zonal price falls below **−$30/MWh** (below the PTC floor — a dump-cost
  degeneracy) or negative-price hours exceed **3×** the measured 2024 count (> 3,516 h).
- Reported: slack TWh and hours; negative hours by zone; hours > $200 and > $1,000 (the C3c object,
  reported only).

Kill ⇒ the FINDING reports it as the session's result and the remaining years are **not** spent.
Pass ⇒ the full span runs unchanged (the screen bundle is then re-solved inside it and deleted).

---

## 4. Known input artifacts named before the solve (P9, and one new one)

| hour | what the served series reads (phase-0) | status |
|---|---|---|
| **2023-06-12 21:00** (EIA-930 `Demand` = 3,621,097 MW; `NG: WND` = 3,589,445 MW, a 100× unit slip) | `Demand`: **repaired** by the live 2.5× spike screen (`_screen_demand_spikes`, `eia930/demand.py`) — served demand 31,511 MW, smooth. **`NG: WND`: NOT repaired on the model's wind-input path** — the delivered-profile CF for local hour index 3909 reads **0.96** (potential 31,604 MW vs 4,700 / 3,540 MW in the neighbouring hours): **+27 GWh of phantom wind in one hour** (0.024 % of 2023 wind potential). The benchmark side was screened by SPP-31 (`calibration_reference.json` 106.63 → 103.05 TWh) but NOT on the C1/bench `e930.parquet` path (SPP-31 §3.3/§5a, still open): **C1 `wind` 2023 will be scored against an actual inflated by 3.59 TWh**, and `net_gen` 2023 (288.1 TWh) carries the same +3.6 TWh | **NEW routing** (wind-input side) → SPP-DESK: the same 2.5× screen the demand loader runs belongs on the `_eia_hourly_cf_profile` path; repo-wide `src/` change with cache-key risk, the P9 class. The C1-2023 wind number is reported at full magnitude AND beside the screened actual in the FINDING; nothing is tuned |
| **2024-07-19 00:00** (audit: partial low-side dropout) | the served series shows a **9-hour plateau** at 43,094–43,105 MW (local index 4791–4800, 7/18 15:00–7/19 00:00) followed by a 10 GW step to 32,912 MW — a stuck/forward-filled meter rather than a dip; EIA-930 `net_gen` shows the identical plateau | P9 routed (audit track); passes through; reported |
| **2025-06-21 05:00** (audit: 1,505 MW) | **not present** in the served series — the ±12 h window reads 34,446–49,118 MW with a smooth overnight trough; 2025 global minimum 24,265 MW (Apr 26 04:00). The demand-profile curator's physical-bounds screen (SPP-31 §5c) has evidently repaired it on the path the model reads; the `demand.py` docstring's "both hours pass through" is not what the served series shows | reported; nothing to do |

The two 2023/2024 hours are 1-in-8,760 artifacts and are reported, never repaired in-lane (P9: *"no
new ScenarioConfig parameter in W2–W4"*).

---

## 5. Control, memory, and what this bundle becomes

**Control = none** (P7). There is no SPP keeper, so rule 29(b) form 4 is vacuous and no control solve
is spent. **This bundle becomes the 29(b) control for every later SPP lane** (SPP-51 … SPP-57,
SPP-60): its committed numbers are what each lever is differenced against.

Memory class registered for the `spp` profile: `per_plant=True`, `co_opt=False`,
`peak_gb=<measured on the screen, then on the full span>` (plan §3, the two further defaults); the
wall-clock and children's peak RSS are captured by a `resource.getrusage` wrapper around each
invocation and reported in the FINDING. The 168-hour smoke solved in 0.32 s (1,441 simplex
iterations; 1,212 LP units, 2 zones) and the 24-hour full pipeline in ~90 s end-to-end, so an
8760-hour year is expected in single-digit minutes and well inside 15 GB — a two-zone LP is a
fraction of MISO's six-zone footprint.

**Rule 15 / 16 / 22 / 29(c):** the full bundle is registered whatever the determination reads
(`2026-09-07-spp-1-baseline`, `results/calibration/spp40_baseline_B/` + `hourly/`), becomes
`keepers/SPP.json`'s keeper because it is the most structurally faithful SPP run that exists, and
the screen bundle `_spp40_screen` is **deleted before the PR merges** — every number this lane will
ever cite from it is in the FINDING.

---

## 6. The DOF ledger — declared before the solve

`scripts/build_dof_ledger.py` on the recipe lists **three config-derived entries and nothing
else** (no per-ISO curated constant is keyed on SPP; no floor, bridge, adder, seam ladder, or
scarcity overlay is armed):

| entry | value in this recipe | identification, stated honestly | residual-identified on SPP? |
|---|---|---|---|
| `offer_curve_by_group` | 1.0 on every band of every class SPP carries (§2.3) | the **identity** — every tranche offers at its own measured heat rate × measured delivered fuel + VOM; the only non-identity values in the dict are on classes SPP has no unit in (`CC_INTERMEDIATE`, `CT_INTERMEDIATE`, `ST_GAS_INTERMEDIATE`, `COAL_PRB/BIT/LIGNITE/WC`) and are provably inert; ledgered as measured-physical with **0 tuned scalars** | **no** |
| `offer_curve_smoothing` (n = 6, exp = 1.0) | generic | the econ-ramp interpolation between `econ_low` and `econ_high`; with both at 1.0 the ramp has **zero span** — inert for SPP; ledgered with 0 scalars | **no** |
| `wefor_multiplier` | 0.7 | the CLI's non-MISO default, an inherited generic scalar the audit (C-15) classifies as residual-identified on ERCOT; it scales the statistical forced-outage rate that sits on top of SPP's measured unit-outage overlay. **Neither 0.7 nor 1.0 has an SPP identification**, so the default is kept, NOT re-chosen, and it is ledgered `residual` with its open root cause (the overlay/statistical double-count that `wefor_residual` names as the successor — an SPP-desk lever, not this lane's) | **inherited, not identified here** — the one entry that keeps the ledger from reading literally zero residual-sourced rows, reported rather than relabelled |

Also disclosed (not ledger entries, no scalar chosen here): `SUMMER_WEFOR_SHARE = 0.30` (the
uncited generic constant MISO replaced for MISO only), the −$26/MWh wind PTC dispatch credit, and
the coal must-run-at-VOM construction — all inherited defaults shared by every ISO's backcast.

**No parameter in this recipe was set by looking at an SPP residual, because none existed.** Every
value is either a dataclass/CLI default, a measured SPP input from SPP-30/31/32/53, or the identity.

---

## 7. What the screen is NOT allowed to do

- It never reads C1–C8 as a gate (rule 29: "did C3a improve" is the forbidden form).
- It never moves the TTC, a band, a floor or an adder — a structural miss opens a lever from
  SPP's queue (SPP-57 Oklahoma pocket first, then SPP-54, SPP-55 VRL scarcity, SPP-56 co-opt) as a
  NEW chartered lane.
- A lone C3c failure on the full span is the rule-22 standing-rule ledgered caveat; every other
  failing criterion is reported at full magnitude and the run is still registered as the keeper.
