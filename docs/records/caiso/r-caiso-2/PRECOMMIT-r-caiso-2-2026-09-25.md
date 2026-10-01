# PRECOMMIT — R-CAISO-2: 2019–2021 gate check, and the CC gross-net identity repair (2026-09-25)

Lane R-CAISO-2. Keeper `2026-09-24-caiso-r-inputs-vintage` (bundle `rcaiso_inputs_span`, 2022–2025, basis
`18bb99b1`), DETERMINATION NOT-YET on one row: C1 2023 CC_REGULAR −5.36 TWh vs ±5.27. The parent solves
nothing (rule 32(a)); every number below is zero LP.

## 0. TASK A — 2019–2021: STOPPED at phase 0 (no shard launched)

PR #6588 (I-CAISO intake) is MERGED (2026-09-25 01:45Z). Blocker status at HEAD `013aeaef`, read from code and data:

| blocker (R-CAISO PRECOMMIT §0) | status at HEAD | evidence |
|---|---|---|
| `caiso_supply_consistent_demand` 2019–21 artifact | **OPEN — HARD.** No artifact written; the derive stopped at its pre-registered guard (wedge −8.55 / −6.03 / −3.82 TWh vs floor −1.5). `YEARS = (2022, 2023, 2024, 2025)` still. A 2019–21 solve raises `FileNotFoundError` at `eia930/demand.py:274-278`. | `INTAKE-i-caiso-2019-2021-2026-09-24.md` §1; `derive_caiso_supply_consistent_demand.py:67`; `data/raw/reference/caiso-supply-consistent-demand/` holds 2022–2025 only |
| CA carbon price 2019–21 | closed (16.84 / 17.04 / 22.04 $/t) | INTAKE §2 |
| EIA-930 CISO hydro gap 2019–20 | closed (Outlook fill, +4.85 / +11.67 TWh) | INTAKE §3 |
| nuclear per-unit 2019–21 | closed | INTAKE §4 |
| intertie hub series | **2019–20: no source**; 2021 5,976 h, below the injector's 75 % bound → static ladder | INTAKE §5 |
| LMP + tail references | **2019–20: no source** (C3a/C3b/C3c unscorable); 2021 partial with coverage vectors | INTAKE §6 |

**The hard blocker is an owner decision the intake itself routed** (INTAKE §1): (a) accept the construction for
2019–21 with a guard rebuilt on the measured EIA-930 basis (the 930 NG cell equals Outlook natural gas alone in
2019–22, so the fold-in premise the guard encodes does not hold there), or (b) re-derive the fold-in treatment
for every year, which moves the committed 2022–25 artifacts and therefore the keeper. Either is a
construction decision this lane may not take on the residual. **No 2019–21 shard is launched**; the keeper
span stays 2022–2025.

## 1. TASK B — the lever, chosen from structure

**Where the 2023 miss lives (zero LP; committed payload + bench).** 2023 CC_REGULAR model − actual by zone:
NP15 −1.92, LA_BASIN +0.43, **SP15_rest −4.90**, ZP26 −0.04, SDGE +1.19. By month, −4.79 of it sits in
Jan–Mar. Net imports model 39.0 vs actual 28.9 TWh. By plant, **Pastoria 55656 (779 MW, SP15_rest) is
−2.93 TWh of the −5.19 plant-sum** (model 1.41 vs EIA-923 4.34). It is also −2.00 TWh in 2022 and −2.98 TWh in
2024: the largest standing CC miss in every year.

**Where R-CAISO's own CC loss went.** Against the prior keeper (`caiso-290-leftedge`, git `ef1c8d17^`),
the −0.96 TWh 2023 CC delta is mostly Alamitos −1.14, Huntington Beach −0.91 and El Segundo −0.44. All three
were OVER-dispatched before and moved toward actuals, which is the new inputs working. Pastoria moved
−0.35 TWh AWAY from its actual.

**The defect (a physical identity, found by reading the input, not tuned).** `derive_campd_cc_heat_rates.py`'s
boundary guard admits a plant when CAMPD gross ÷ EIA-923 net ∈ [0.90, 1.25]. Gross = net + station service,
so a fully metered plant cannot read below 1.0. Pastoria reads **1.029 in 2019 and 0.927–0.946 in 2020–2025**
with its EIA-923 output unchanged. Per unit, CT001/CT002 gross heat rate goes 7.19/7.07 → 8.84/8.76 from 2020,
while CT004 holds 7.12 → 7.45. From 2020 the Phase-1 steam turbine's output left those two units' CEMS gross
load. The applied net rate is therefore **8.49 MMBtu/MWh** (committed; econ tranches 9.06–9.10). Its true
rate, heat input ÷ EIA-923 net, is **7.69**, which equals eGRID's 7.69. In the rebuilt 2023 offer surface
(`probe_cc_offer_census.py`) Pastoria is the most expensive CC in SP15: in the money 21–27 % of hours, against
51–76 % for High Desert.

The guard's docstring claims "no value in [0.75, 1.00] would change the partition". That was measured on
**SOCO**, which has zero rows there. CAISO's artifact has **12 `ok` rows below 1.0**: Pastoria 2020–25 and its
pooled row, Carson 10169 pooled (0.9005), Sanger 57564 2024 (0.9008), Huntington Beach 62116 2020 (0.940),
Desert Star 55077 2024 (0.946), Alamitos 62115 2020 (0.986, commissioning year). Every consistent row reads
≥ 1.008.

**The repair.** A new flag, `gross_below_net`, for ratio ∈ [0.90, 1.0) (`_GROSS_NET_IDENTITY_MIN = 1.0`, the
identity). A refused row falls back exactly as every refused row already does: year row → pooled row → eGRID
(`campd_bins._measured_rate_map`). **Zero new ScenarioConfig fields, zero free parameters, no threshold swept.**
Rule 23: the re-derivation is justified by a defect in the derive's own data-integrity premise, shown by a
physical identity and by per-unit CEMS. It is not justified by the residual. The residual is where the lane
looked; the identity is what decides. Rule 25: **CAISO's artifact only is re-derived.** Other ISOs carry
`ok` rows below 1.0 at HEAD (ERCOT 14, MISO 10, NEISO 6, NWPP 5, NYISO 6, PJM 23, SPP 1, SOCO 0). They are
routed to their own lanes, not touched.

Matrix: `measured_cc_heat_rates` CAISO cell (evidence updated). The CAISO lever queue (§5.2) is empty in-model.
This is an input correction on the path the keeper already arms, so it is taken off-queue for that stated reason
(rule 28(a)). No R/I/G cell is re-tested: `zonal_gas_basis` (R, caiso-221) and every CC commitment/loading cell
stay as adjudicated.

## 2. Artifact delta (zero LP)

**Re-derive.** `derive_campd_cc_heat_rates.py --iso CAISO --egrid-family-heat-rates --measured-ct-heat-rates`
(the keeper's provenance posture). **Baseline first, unpatched:** every APPLIED column (`heat_rate`, `flag`,
`boundary_gross_over_net`, per-year rows) reproduces the committed file exactly (`DataFrame.equals`). The only
cells that differ are 8 provenance-only `model_heat_rate_egrid` / `model_over_measured` cells (Glenarm 422,
Carson 10169). The derive's own help text says these "move model_heat_rate_egrid and nothing that is
applied"; the difference is HEAD provenance-fleet drift since `cbdf0c44`. **Patched:** exactly the 12 rows
of §1 flip `ok → gross_below_net`, and nothing else applied moves.
New sha256 `0d5e457c77eb1d2439c10ad7504c4875bfca4c5557cc7337d066a9988e7bfb38`.

**Offer-array delta** (fleet-only rebuild of `rcaiso_inputs_span`, `probe_cc_offer_census.py`):

| year | plant | before → after (committed-tranche net HR) | why |
|---|---|---|---|
| 2023 | Pastoria 55656 (779 MW) | 8.490 → **7.691** (econ 9.06–9.10 → 8.20–8.24); in-money share vs keeper price 0.27 → 0.39 | year + pooled refused → eGRID |
| 2023 | Carson 10169 (56 MW) | 9.839 → 8.688 | pooled refused → eGRID |
| 2024 | Pastoria / Desert Star 55077 / Sanger 57564 / Carson | → 7.671 / 7.587 (pooled) / 9.197 (eGRID) / 8.541 | as above |
| 2022, 2025 | Pastoria (+ Carson) | → eGRID 7.678 / 7.671 | as above |

Every other CC_REGULAR unit in 2023: byte-identical HR and pmax (28 plants compared).

## 3. G-DRIFT (rule 29(b)) — keeper basis `18bb99b1` → this lane's base `013aeaef`

A read-only audit of every hunk in `git diff 18bb99b1 013aeaef` over `src/market_sim`,
`scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source` and `data/raw/reference` (32 files).
**ALL INERT for a CAISO 2022–25 backcast replay:**

* I-CAISO intake (#6588): the hydro backfill loads only where `fuelsource_<Y>` exists (2019–21). Carbon,
  nuclear-CF and intertie/LMP rows are added for 2019–21 only, and the 2022–25 rows are `DataFrame.equals`
  (INTAKE §0).
* SOCO BA-membership and interchange-sign repairs return the same object for CISO.
* `mid_vintage_exit_carry` is False in the keeper.
* `resolve_bin_heat_rates` is ERCOT-guarded.
* Cache-ledger prose; key-provenance tooling not imported by the runners.

CAISO's cache key moves (the solve-surface rows `NUCLEAR_MONTHLY_CF_BY_YEAR`, `STATE_CARBON_PRICE_BY_ISO` and
`RGGI_MEMBER_STATES_BY_YEAR` gained 2019–21 rows), but the 2022–25 inputs do not.

**Excluded by pinning:** `origin/main` has since moved to `5f8d153c` (COAL-SUB, PR #6611, commits marked WIP
with the byte-identity proof "to follow"). It relabels CAISO plant 10684 (Argus Cogen, 15 MW) `COAL → COAL_BIT`,
and the keeper recipe's bare `COAL` key would raise `BareCoalClassError`. This lane's commit is cut from
`013aeaef` and the shards pin THIS commit, so COAL-SUB is not on their path. Form 4 is valid: the keeper's
committed bundle is the control, and the only LIVE delta is §2.

## 4. Recipe and shard plan (rule 32(c), 34, 36)

`scripts/replay_keeper.py results/calibration/rcaiso_inputs_span --years <Y>`, **no `--set`**. The arm IS the
re-derived `campd_cc_heat_rates_CAISO.csv` on the pinned SHA; everything else is the keeper recipe. One year per
shard, full bundle pushed:

| shard | year | out-dir | branch |
|---|--:|---|---|
| r-caiso-2-2022 | 2022 | `results/calibration/rcaiso2_ccid_2022` | `claude/r-caiso-2-2022` |
| r-caiso-2-2023 | 2023 | `results/calibration/rcaiso2_ccid_2023` | `claude/r-caiso-2-2023` |
| r-caiso-2-2024 | 2024 | `results/calibration/rcaiso2_ccid_2024` | `claude/r-caiso-2-2024` |
| r-caiso-2-2025 | 2025 | `results/calibration/rcaiso2_ccid_2025` | `claude/r-caiso-2-2025` |

Control = the keeper's committed bundle (G-CTRL form 4).

## 5. Stated before the solve

* **Direction, not a gate.** Pastoria's offers fall ~9.5 % in 2022–25, so CC_REGULAR should rise and imports/CT
  fall in every year. Sanger 2024, Desert Star 2024 and Carson are small. **The size is not predicted and is not a
  criterion**: the repair stays in whatever the C1 row does (rule 1). If 2023 CC_REGULAR still misses ±5.27, the
  row stays open and routes to Pastoria's remaining gap. The prior keeper had Pastoria at eGRID 7.69 and still
  dispatched 1.76 vs 4.34 TWh, so this repair is expected to close only a small part of Pastoria's standing miss.
* NOT a keeper if: a load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL in any year; C6 or C8 fails; a
  second ledgered caveat appears; any leg's config signature differs from §4.
* Offer-curve multipliers unchanged; DOF ledger unchanged at 9/6; no `authorized_price_tuning` block.
