# FINDING — soco-73: no admissible lever for the two failing rows (zero LP, no solve)

Lane soco-73, 2026-09-27. Keeper `2026-09-26-soco72-gas-basis-window` (bundle `soco72_span`), unchanged. No
PRECOMMIT, no shard, no registration: Task 1 found no lever that meets rules 17 / 19 / 21, so the lane stops here
as its handoff instructs.

- **Probes:** `scripts/probes/_soco73_phase0.py` (modes `conduct`, `c4shape`, `campaign-greedy`), and
  `scripts/probes/_soco73_gdrift_identity.py`.
- **Inputs:** the seven soco-72 legs, fetched by full SHA from unreachable commits (the `claude/soco72-<Y>` branches
  are gone). Unit hourly data is available per leg.
  - 2019 `8b416e9f6061f1ff74b376b95ed0f790abb4cac5`
  - 2020 `5882a26510bc12fb0cbc7ee8eb954f6ada9b49dd`
  - 2021 `5bb0272d5ce7f5c1d51d98742aaa1f7e10222e46`
  - 2022 `1184b5711be4f779d0cb57e647a3b85d39ccc589`
  - 2023 `a99009655325854890af91914952db089a86b566`
  - 2024 `291d85e1fd1566b63df69129e79fb30c3596c91d`
  - 2025 `1f10c7a01a3fed36be8d541572800b68e3f9e309`

## 1. G-DRIFT vs `19159a0c` (rule 29(b))

**Verdict: ALL LP INPUTS BIT-IDENTICAL.** Instrument 3 rebuilt `fleet_only` for all seven years at both SHAs.

Hand classification of every changed backcast-path hunk on `main` (HEAD `bd2839ae`). All are INERT for SOCO.

| change | where | why inert for SOCO |
|---|---|---|
| `nwpp_path76_alturas_link` + `pipeline/ttc.py` + `iso_configs` link | NWPP | returns the same object for `iso != "NWPP"`; default off |
| `neiso_winter_fuelsec_conduct_roster` + `winter_fuel_inventory.py` + `WINTER_FUELSEC_CONDUCT_MIN_ONLINE_SHARE` | NEISO | default off; absent from the SOCO recipe |
| `campd_bins.py` committed share now reads `_mg` | NYISO guard | only differs when `campd_outage_merit_order_guard` is on; SOCO recipe `false` |
| `data/raw` changes: NWPP CT heat rates; NYISO `perunitmerit` tranches and outages; NEISO winter conduct | other ISOs | none is SOCO's artifact |
| ScenarioConfig `*_path` defaults | all | absolute-path repr of the worktree; instrument 3 shows the arrays identical |

## 2. Measured coal commitment conduct vs the soco-72 legs, 2019–2022 (`conduct`)

The three plants with no must-run tranche, the "cyclers":

| year | plant | EIA-923 / model TWh | CEMS starts · run p25/p50/p75 h · min-load p5 | CEMS synced h | model on h · starts · run p50 | synced, price < own offer, model off (h) |
|---|---|---|---|---|---|---|
| 2019 | Barry 3 | 4.175 / 0.087 | 26 · 110/283/476 · 0.455 | 8,312 | 267 · 51 · 4 | 7,941 |
| 2019 | Crist 641 | 2.668 / 0.984 | 48 · 3/88.5/381 · 0.331 | 7,638 | 1,597 · 144 · 7 | 6,309 |
| 2019 | Wansley 6052 | 1.816 / 0.413 | 22 · 6/143.5/303 · 0.381 | 3,849 | 505 · 81 · 4 | 3,602 |
| 2020 | Barry 3 | 2.821 / 0.310 | 13 · 195/301/579 · 0.454 | 6,552 | 559 · 25 · 15 | 5,884 |
| 2020 | Crist 641 | 1.100 / 0.510 | 27 · 6/26/377 · 0.349 | 5,215 | 884 · 100 · 7 | 4,780 |
| 2021 | Barry 3 | 3.678 / 0.876 | 31 · 34/186/562 · 0.546 | 6,862 | 2,045 · 253 · 8 | 4,769 |
| 2021 | Wansley 6052 | **1.115 / 6.140** | 16 · 24/82.5/122 · 0.193 | 2,174 | 4,981 · 324 · 13 | 769 |
| 2022 | Barry 3 | **3.314 / 5.293** | 26 · 24/96.5/411 · 0.365 | 7,278 | 6,627 · 136 · 9 | 1,566 |

- **The model does not start the cyclers at all.** In 2019, Barry is on for 267 h against 8,312 h synchronized in
  CEMS.
- **Price, not run length, keeps them off.** Their cheapest available P1 offer sits above the zone price in 96 % of
  their synchronized hours. The median offer-minus-price is +$6.36, +$4.16 and +$4.98/MWh.
- **The same plants over-run elsewhere.** Wansley 2021 is +5.0 TWh and Barry 2022 is +2.0 TWh. Any commitment floor on
  these plants has a sign problem across years.
- **The must-run plants' commitment is already right.** Bowen, Miller, Scherer, Gaston and Daniel match CEMS synced
  hours to within about 1–3 %.

## 3. 2020 C4 coal: a fleet-wide second-half LEVEL deficit, not cycler shape (`c4shape`)

- **Size.** NRMSE 0.304, r 0.925. Mean bias is −926 MW: 31.03 TWh model against 39.14 TWh EIA-930.
- **Season.** 78 % of the squared error falls in July–December, and August alone is 28 %. The monthly bias runs from
  −1.7 to −2.2 GW in July–August.
- **Time of day.** The bias is deepest at midday (−1.30 GW at 13:00) and shallowest overnight (−0.67 GW).
- **By plant** (share of the error, using each plant's own EIA-923/CEMS scaling):

  | plant | Bowen | Barry | Scherer | Miller | Gaston | Daniel | Crist | Wansley |
  |---|---|---|---|---|---|---|---|---|
  | share | 0.20 | 0.19 | 0.15 | 0.10 | 0.09 | 0.08 | 0.03 | 0.02 |

  The cyclers carry only 24 %. The measured-must-run plants carry 62 %, and their deficit is ECONOMIC dispatch above
  must-run.

- **Consequence.** No commitment object scoped to the cyclers can move 2020 C4.

## 4. Candidate levers

### (i) The soco-53d campaign construction, scoped to coal by parameters — REFUSED (inert, and fails rule 17)

**How it was scoped.** The existing derive was retargeted with `TARGET_FUEL = "coal"` and pooled over 2019–2025, all
other parameters unchanged (scratch output only, not committed). Scope was set by parameters:

- the plant has no must-run tranche (rule 19: the must-run plants are committed by `coal_mustrun_requires_measured_row`
  K);
- the plant's `flag == ok`, using the gas derive's ex-ante 0.50 campaign-duty gate.

That leaves Barry (min-run 28 h, LSL 0.173) and Crist (min-run 11 h). Crist's min-run is contaminated: the pooled series
includes its post-conversion gas-fired boiler conduct. Wansley falls out at sync share 0.233.

**Greedy result** (the detector's min-run extension and online-hours LSL legs, on the leg's P1 pattern standing in for
P0, with price-taker displacement):

| year | COAL_BIT Δ TWh | failing / thinnest rows (keeper → arm) | C4 coal NRMSE | floored h while CEMS-off |
|---|---|---|---|---|
| 2019 | +0.133 | COAL_BIT −4.24 → −4.19 FAIL; CC_REGULAR 2.86 → 2.86; CT_PEAKER 2.71 → 2.71 | 0.263 → 0.262 | 387 |
| 2020 | +0.069 | COAL_BIT −2.36 → −2.33; CC_REGULAR 2.26 → 2.26 | **0.304 → 0.304 FAIL** | 643 |
| 2021 | +0.394 | ST_GAS −2.73 → −2.79 (thinner) | 0.208 → 0.204 | 93 |
| 2022 | +0.156 | COAL_PRB +2.69 → +2.69; COAL_BIT +1.16 → +1.22 | 0.240 → 0.240 | 1,311 |
| 2023 | 0 | CT_PEAKER 2.40 → 2.40 | = | 0 |
| 2024 | +0.234 | — | 0.256 → 0.253 | **3,203** |
| 2025 | +0.033 | — | — | **6,622** |

- **Size.** 2019 moves +0.13 TWh against the +3.62 TWh needed to reach the band. Even at soco-72's measured ×3 LP/greedy
  ratio, that is about +0.4 TWh.
- **Why it cannot reach.** The floor extends only runs the LP already makes, and the LP makes almost none (§2).
- **Rule 17 failure.** A pooled sync share hides Barry's 2024–2025 layup (synced 1,795 and 2,096 h). The floor would
  bind thousands of hours when the plant was metered offline. Per-year membership would repair that, but it cannot
  repair the reach.

### Enumerated under rule 19: the coal synchronization family — NOT ADMISSIBLE here

The family is `coal_mustrun_online_pmin` + `coal_sync_srmc_tranche`, with the `coal_sync_ensemble_level` repair. All are
U for SOCO.

- **Scope.** It restructures every coal plant's tranches, including the three measured must-run plants under a K cell.
  No parameter scopes it to the cyclers.
- **Placement.** It uses the degenerate top-k window (SPP-71's own construction-error verdict). The ensemble repair
  instead floors every hour, and that binds 4,911 / 8,224 / 6,586 / 6,951 h at Wansley in 2019–2022 while CEMS shows it
  offline. That is a rule-17 failure by definition.
- **Verdict.** It is a multi-part Thread-D rebuild (a take-or-pay pairing is also required), not a zero-parameter lever.
  The cells stay U, and nothing was solved.

### (ii) Coal P1 start markup on the no-must-run cyclers — NOT ARMED

- Its ceiling is about +0.4 TWh, far short of the +3.62 TWh needed.
- It remains gated on the open owner question SOCO-64/65.

## 5. What the evidence says the object is

- **2019 COAL_BIT.** The cyclers are priced out: their offers sit above the clearing price in 96 % of their measured
  synchronized hours. A cost-minimizing LP with no start cost and no min-down has no reason to keep them on.
  - The real plants ran multi-day campaigns anyway. The driver is not in the model and is not a measured cost:
    fuel (F923), heat rate (CAMPD) and gas basis (EIA-923) are all measured as of soco-72.
  - A floor that places the units where the meter says they ran would pin outcomes, which rule 13 forbids.
  - What is left are the commitment economics a binary UC would carry: start cost plus min-down across a cheap trough.
    In a pure LP those enter only as the start markup, which is question (ii).
- **2020 C4.** It is a fleet-wide July–December coal level deficit, 62 % of it at the measured must-run plants' economic
  tranches. It sits next to 2020 CC_REGULAR +2.26 pp and CT_PEAKER +2.22 pp, a gas-over-coal merit-order split in the
  second half of 2020.
  - The next zero-LP object is a price decomposition of July–December 2020 on the soco72-2020 leg: the marginal class,
    and Bowen/Scherer econ-tranche offer minus price. That would show whether the coal offer or the gas offer is off in
    that half-year.

## 6. Retrievability

No solve was run, so nothing is promotable. The soco72 legs sit gitignored on this container's disk and are recoverable
at the full SHAs above.
