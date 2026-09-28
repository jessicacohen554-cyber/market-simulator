# FINDING — PJM-NEXT-7 phase 0: where the COAL_BIT surplus sits (zero LP)

**Keeper** `2026-09-28-pjm-next-6-f2` (bundle `results/calibration/pjmnext6_sp_span`). **Zero LP.**
**Probe** `scripts/probes/_pjmnext7_coal_phase0.py` reads the committed run payload (per-plant model MW),
bench `PJM/<y>.json.gz` (CAMPD net hourly, EIA-923 annual), per-unit CAMPD `data/raw/campd-unit-level`
(hydrated `--profile pjm`) and the keeper's outage extracts (`resolved_inputs.campd_unit_outages.path` =
`campd-unit-outages-rederive-peakerkeep-unitfuel-PJM.csv`, plus `-short-rederive-PJM.csv`,
`outages.py:642`). Question: rule 14 `[R-ACCURATE]` — is there a MEASURED availability/commitment input the
model gets wrong vs CAMPD? Not re-tested: the gas/coal price-ratio channel (matrix `da_virtual_bids`, pjm-166)
and DA virtuals (separate lane).

## 1. Per-plant surplus (COAL_BIT bench plants, TWh)

C1 is class model − EIA-923 `classFull`: 2019 186.77 − 169.48 = +17.29; 2021 177.92 − 159.00 = +18.92.
On the bench plants alone (model − CAMPD net) the surplus is **+25.56 (2019) / +17.43 (2021) / −0.84 (2023)**;
2019's plant-level figure exceeds C1 because `classFull` carries ~9.0 TWh of COAL_BIT at plants outside the
CEMS bench (169.48 vs Σ plant e923 160.50). **Top-10 plants carry 78 % (2019, +19.86) and 75 % (2021, +13.12)**
of the net surplus; in 2023 the top 10 carry +7.82 against a −0.84 net (offset by under-runners).

| 2019 plant | npl MW | model | CAMPD | Δ | hrs m/a | Δ above synced | Δ within synced |
|---|---|---|---|---|---|---|---|
| Bruce Mansfield 6094 | 2741 | 4.88 | 0.83 | **+4.05** | 8016/1669 | 3.64 | 0.40 |
| W H Sammis 2866 | 2468 | 7.63 | 3.75 | **+3.89** | 8760/6964 | 2.41 | 1.47 |
| John E Amos 3935 | 2933 | 11.59 | 9.76 | +1.82 | 7464/7530 | 0.17 | 1.65 |
| Gavin 8102 | 2600 | 15.69 | 13.91 | +1.78 | 8760/8577 | 0.99 | 0.79 |
| Chalk Point 1571 (coal) | 728 | 2.17 | 0.48 | **+1.69** | 7087/1481 | 2.12 | −0.44 |
| Rockport 6166 | 2600 | 9.67 | 8.02 | +1.64 | 7272/7302 | 0.13 | 1.52 |
| Homer City 3122 | 2012 | 7.94 | 6.36 | +1.57 | 8088/8137 | 0.17 | 1.40 |
| Birchwood 54304 | 258 | 1.33 | 0.07 | +1.26 | 8520/591 | 1.19 | 0.07 |
| Pleasants 6004 | 1368 | 6.02 | 4.89 | +1.13 | 7344/6747 | 0.56 | 0.57 |
| Chambers cogen 10566 | 285 | 1.59 | 0.56 | +1.03 | 8760/8758 | (no CEMS gross) | |

2021 top 5: Rockport +2.12, Keystone +1.67, Gavin +1.62, Fort Martin +1.34, Conemaugh +1.22 — every one with
model online hours within ±1 % of CAMPD and ≥80 % of its Δ **within synced capacity**.

## 2. Decomposition: availability vs loading (TWh, model − CAMPD, bench COAL_BIT plants)

"Above synced" = model MWh above the net capacity of the plant's coal units CAMPD shows synchronised
(`opTime>0`) that hour, attributed to the dark state of the offline units.

| component | 2019 | 2021 | 2023 | reading |
|---|---|---|---|---|
| above synced — units inside a keeper outage window | 5.77 | 1.56 | 0.50 | window present but not biting (§3 a, b) |
| above synced — unit dark ALL year, no window | 3.35 | 0.17 | 0.00 | (c) exit cohort (§3 c) |
| above synced — unwindowed dark run 1–5 d | 3.09 | 3.03 | 0.76 | reserve shutdowns (§4) |
| above synced — unwindowed dark run ≥5 d / <24 h | 1.49 | 0.50 | 0.11 | in-merit filter judged economic |
| within synced (loading) | 10.20 | 11.36 | −1.49 | (d) economic dispatch |
| cogen, no CEMS gross (Chambers, Logan) | 1.66 | 0.80 | −0.72 | PURPA cogens, retired 2022 |
| **total** | **+25.56** | **+17.43** | **−0.84** | |

Floors are not the driver — (b) is rejected: model system-minimum COAL_BIT output is *below* CAMPD in 2019
(6,762 vs 7,324 MW), and the 2019 surplus *rises* with model price quartile (+3.91 / +6.13 / +7.47 / +8.05
TWh, West_APS LMP), the opposite of a low-price floor signature (2021 flat +3.95…+4.57). Within synced, 11.3
(2019) / 13.4 (2021) TWh sits *below* the unit's own ±3-day CAMPD maximum — i.e. capability-feasible
part-load the plant chose not to run, not a partial derate (above-envelope 6.8 / 3.4 / 1.9 TWh, an upper bound).

## 3. The measured defects (all in the CAMPD unit-outage layer, all on 2019–2021 exiting coal)

Zero-LP call of `unit_outage_derate_factors(2019, iso="PJM", <keeper flags>)` (`outages.py:1460`):

- **(a) Chalk Point 1571 — unit capacity cross-walked to the wrong generator.** CAMPD coal units `1`/`2`
  (355 MW each, dark 313 / 290 days of 2019, windows present) carry `unit_capacity_mw` **16.0 / 35.0**
  (`capacity_source=eia_digits`) — the nameplates of combustion turbines **GT1 / GT2**. The trailing-digit
  match (`derive_campd_unit_outages.py:376-382`) is unique only because the deriver's EIA-860 snapshot no
  longer lists ST1/ST2 (retired 6/2021). Derate = `ucap/denom` (`outages.py:1929,1964`) = 51/728 MW, so the
  model plant's availability is **0.924 through Apr–Jun 2019** while CAMPD shows it fully dark.
- **(b) Bruce Mansfield 6094 — dated-bin dilution.** Units 1–2 retired 2/2019, unit 3 11/2019 (EIA-860 2020
  vintage). `mid_vintage_exit_carry` splits them into dated bins (`campd_bins.py:3047`), but the outage factor
  is keyed `(plant, group)` with the WHOLE-plant denominator (2,741 MW) and applied to every bin, so unit 3's
  Mar 9–Jul 15 / Sep 14–Dec 31 windows leave its bin at **0.639** availability. Model Mar–Nov 2.73 TWh vs
  CAMPD 0.46 (**+2.27**).
- **(c) Dark-all-year units with no window.** Mansfield 1–2 (1,827 MW) report every hour of 2019 with
  `opTime=0` yet carry no window → model Jan–Feb 2.14 TWh vs CAMPD 0.37 (**+1.77**). Sammis 1–2 (381 MW
  nameplate) likewise; Sammis 3–4's full-year windows are sized at `observed_peak` 62 / 152 MW vs EIA 190.4.
  The deriver skips never-producing units by design; the SOCO-61 `--dark-unit-years` construction
  (`derive_campd_unit_outages.py:1429`, `ScenarioConfig.campd_dark_unit_year_windows`, `scenarios.py:16672`,
  predicated on `campd_per_unit_attribution` at `arrays.py:1349`) exists to close exactly this and is off.

Gross model energy on this phantom capacity: **2019 ≈ 8.3 TWh** (Mansfield 4.05, Sammis ≈2.4, Chalk Point
≈1.9), **2021 ≈ 0.4** (Sammis 0.35 — units 1–4 gone by the 2021 vintage; Chalk Point coal exits 6/2021),
**2023 ≈ 0.1**. Birchwood 54304 (+1.26 in 2019) is *not* in this family: its dark spans were rejected by the
in-merit filter (`min_inmerit_hours 24`, `high_load_pctl 0.85`, extract meta) — economic, like §4.

## 4. Year-consistency check (step 3)

The exit-cohort defect is **not** year-consistent in effect because its footprint is the 2019–2021 exit
cohort (Mansfield, Sammis 1–4, Chalk Point coal); 2023 has no such plant (its only dark-all-year unwindowed
unit, Homer City 2, draws 0.00). It is year-consistent in **construction** — any year with an exiting
multi-unit coal plant hits it — which is what rule 14 requires. The 2021 surplus is something else: loading
within synced capacity (+11.36) plus 1–5-day unwindowed shutdowns (+3.03), both ≈0 in 2023 (−1.49, +0.76).
Those 1–5-day spans are 38–40 % weekend unit-hours (base 28.6 %) and only 11–13 % in top-15 %-load hours
(base 15 %): **reserve shutdowns, not forced outages**. Feeding them as availability would pin a commitment
outcome (rule 13 `[R-MEASURED]`); they are a pure-LP commitment-economics gap (startup/min-down), a structural
lever (rule 1), not a measured operand. The same holds for the within-synced loading, whose year pattern
(2019/2021 high, 2023 ≈0) follows the fuel-price regime — the channel pjm-166 already adjudicated.

## 5. Verdict

**Most likely measured rule-14 operand: the CAMPD unit-outage layer's treatment of the coal EXIT cohort** —
one construction, three measured corrections, all regenerable for any year from CAMPD `opTime` + the
year's own EIA-860 vintage: (a) unit capacity from the year's own vintage nameplate (not a post-retirement
snapshot's digit match), (b) derate share against the dated bin's own capacity when `mid_vintage_exit_carry`
splits a plant, (c) full-year windows for dark-all-year units (`campd_dark_unit_year_windows`, SOCO-61).

| predicted C1 COAL_BIT effect | 2019 | 2021 | 2022 | 2023–2025 |
|---|---|---|---|---|
| gross phantom energy removed | −8.3 | −0.4 | ≤ −0.3 (unmeasured) | ≈ 0 |
| net class move (40–70 % retained; other synced coal backfills, not saturated) | **−3.3 to −5.8** | **−0.2 to −0.3** | ≈ 0 | ≈ 0 |
| C1 after | +11.5 to +14.0 (still FAIL) | ≈ +18.7 (still FAIL) | | unchanged |

It is real and admissible but **does not clear C1 in either failing year and does nothing for 2021**.
For 2021 (and ~60 % of 2019) **no measured operand was found**: the surplus is economic loading and
weekend reserve-shutdown commitment on correctly-available units (category d), not availability.

**What a solve would test:** a one-shard-per-year 2019–2025 span (rule 36) arming (a)–(c) — a zero-LP
re-derive of the outage extract with vintage-matched unit capacity and `--dark-unit-years`, plus the dated-bin
denominator — predicted: COAL_BIT 2019 −3.3…−5.8 TWh concentrated at Mansfield/Sammis/Chalk Point (each
plant's model hours → within 10 % of CAMPD's 1,669 / 6,964 / 1,481), 2021 ≤ −0.3, 2023–2025 byte-near-identical.
A 2023–2025 move > 0.3 TWh would falsify the footprint claim. The 2021 gap needs a separate structural card
(pure-LP weekend commitment), not a rule-14 input.
