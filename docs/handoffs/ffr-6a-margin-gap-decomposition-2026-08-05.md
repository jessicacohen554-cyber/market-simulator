# FFR-6A — Margin-gap decomposition of the repaired retirement screen vs the Potomac-SOM net-revenue benchmark

**Session.** FFR Wave 6, MEASUREMENT lane (owner decision D-20(a), sitting Addendum U.4/U.5,
signed 2026-08-05). Branch `claude/ffr-6a-margin-gap-decomposition-f9suco`, off `origin/main`
`57120845`. **This lane tunes nothing, arms nothing, fixes nothing** — the deliverable is a
measured decomposition of the FFR-5D-M finding plus an admissibility verdict per candidate
fix; any fix is a separate charter on these findings. NO lift recommendation (U.2's
determination is the manager's).

**The measured fact this starts from** (FFR-5D-M, `docs/handoffs/ffr-5d-price-object-2026-08-05.md`
§3, probe `docs/handoffs/ffr-5d/paired-arm-probe-2026-08-05.json`, registered arms
`ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}`): under the unified+repaired price object
the retirement screen fails essentially the whole ERCOT merchant fleet (entry_capped 564 /
63.0 GW in 2024, 554 / 66.1 GW in 2025), the adequacy admission cap does ALL retention work,
and the model retires 10.9 GW of gas_st pre-window (actual gas_st exits in the scored
actuals: 0.0) instead of the real 1.534 GW. Either the screen object is missing a real
revenue leg or the bar is mis-leveled. This doc says which, with measured decomposition.

---

## 1. The benchmark (intaken this session, rule 13: validation only, never an input)

Potomac Economics ERCOT State-of-the-Market net-revenue estimates, transcribed under the
data contract into `data/raw/som-competitive-conduct/som_competitive_conduct.csv` (ERCOT
rows, source PDFs committed under `data/raw/ERCOT/`; every row carries source_doc +
source_page):

| year | new CT net rev ($/kW-yr) | new CC net rev ($/kW-yr) | CONE ($/kW-yr) | stack notes |
|---|---|---|---|---|
| 2023 | 224–257 | 228–272 | ~80–130 | ~HALF of net revenue = ECRS price effects (monitor's own attribution); stack = Reserves + Energy + ECRS Effects |
| 2024 | 68 | 89 | CT 102–106, CC 116–121 | stack = Reserves + Energy Sales |
| 2025 | 52.59 (Houston ~59, West up to 177) | 82.96 | planning 140 (legacy PNM 105) | PNM 2025 ≈ $79/kW |

Existing-unit cost benchmarks the SOM itself cites (2024 SOM PDF p.119–120): existing-coal
FOM **$61.60/kW-yr** (EIA), coal VOM $6.40/MWh, ERCOT coal fuel ~$8.50/MWh → coal marginal
cost **≈$23.18/MWh** ("profitable to run in many hours" at 2024 zonal averages
$29.58–35.33/MWh); nuclear total generating cost ≈$31.76/MWh (NEI 2023) vs 2023 average
price $65/MWh ("highly profitable").

SOM's net-revenue construction is the **same pro-forma as the screen's**: attainable
`max(0, price − mc, reserve)` against generation-weighted real-time settlement prices, new-unit
proxy assumptions (CT HR 10.5 / CC 7.0 MMBtu/MWh, VOM $4/MWh, 10 % outage). The standing
replica (`docs/handoffs/fom-scarcity-revenue-audit-2026-07-05.json`) reproduces the published
SOM values within 0.89–0.97 from measured hub RT prices + Henry Hub gas — i.e. **the screen's
pro-forma CONSTRUCTION is validated against its own external observable; what varies between
arms is the PRICE OBJECT it consumes.**

## 2. PRE-REGISTERED READS (written and committed BEFORE the re-run's ledgers were read)

**Committed-artifact base (already in hand, no solve):** the probe JSON's cohort bar
decompositions (shipped coal at the 2021/2024 screens; unified gas_st at the 2021 screen and
coal at the 2024 screen); FFR-5A §3's per-fuel into-2025 unrepaired-lookahead revenue stack
(coal 296.7 / cc 329.9 / ct 267.0 / st 216.1 / nuclear 522.8 $/kW-yr); the bars (ATB FOM ×
multiplier: gas_ct 21, gas_cc 30, gas_st 35, coal 45×1.3=58.5, nuclear 130 $/kW-yr); the SOM
rows of §1.

**The one read NOT persisted in committed artifacts** (charter's re-run condition, stated):
the **per-fuel bar decomposition of the entry_capped fleet at the repaired 2024/2025
screens** (and the non-cohort fuels at the 2021 screen). `_apply_pipeline_retirements`
attaches `margin_detail` to every `entry_capped` row (`retirements.py:1506`), but those rows
live only in the evolution ledgers (`evolution_<year>.json`), which were never committed —
the FFR-5D-M slim bundle carries only `crossover_score.json` + meta + run_config, and
`results/` died with that container. The probe JSON summarizes entry_capped as n/MW by fuel
only. **Therefore ONE re-run of the unified arm is permitted and performed** — invocation
verbatim from ffr-5d handoff §2 + its one flag (`--capacity-screen-unified-lookahead`),
single invocation, years sequential (rule 12), cold. The shipped arm is NOT re-run: its two
objects are already characterized per-fuel (raw-duals screens fail the entire merchant
fleet with cohort-level margins recorded; unrepaired-lookahead screens clear every fuel with
the per-fuel stack recorded above).

Reads fixed now, computed after the ledgers land:

* **R1 — per-fuel repaired-level margin table.** Cap-weighted over each fuel's
  `entry_capped` + `decided` rows at the 2024-ledger and 2025-ledger screens:
  `net_revenue`, `energy_margin`, `reserve_uplift`, `attribute_revenue`,
  `capacity_revenue`, `as_annual_credit`, bar, `screen_price_mean/max`,
  `reserve_signal_mean`, `mc_mean`, `availability_mean`. Expectation stated in advance:
  the probe's coal rows show `reserve_signal_mean = 0.0` and `reserve_uplift = $0.0` at the
  repaired screens — if that holds fleet-wide, the repaired object's AS/reserve leg is
  literally zero while SOM's stack is materially Reserves in every year.
* **R2 — measured-price replica per fuel (the "what should the object produce" column).**
  Extend the standing replica construction (same `Σ_t max(0, p_t − mc) × 0.9 / 1000`
  pro-forma, measured hourly ERCOT RT prices from
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`) to the screen's fuel-class
  mc levels: gas_cc / gas_ct at the SOM proxy assumptions (already validated 0.89–0.97 vs
  SOM), coal at the SOM-cited mc ≈ $23.18/MWh (2024; 2023/2025 via the same PRB
  fuel-cost basis), gas_st at HR ~10.5 × gas price + VOM. This is rule-13-admissible as a
  *diagnostic benchmark* (it consumes measured outcomes, so it can never be a screen input —
  it exists to size the gap between the model's price object and the measured price level).
* **R3 — the identity split of the gap.** For each fuel-year: gap(total) = [SOM or replica]
  − [screen margin] split into (i) price-level term (replica at measured prices minus screen
  energy margin — the price-object gap), (ii) reserve-leg term (SOM reserves share vs screen
  `reserve_uplift`), (iii) bar term (bar vs SOM-cited going-forward benchmarks). Attribution
  claim to test: the price-object term dominates and the reserve term is the whole remainder;
  the bar term is small.
* **R4 — the actual-exits bound (question c).** The scored actual exits decoded from
  `data/raw/_validation-source/capacity_actuals_ercot.csv` (2021–2025 window): J T Deely 1–2
  (plant 6181, 486+446 MW coal, EIA retirement year 2023 — physically ceased operation
  end-2018, CPS Energy municipal decision announced years ahead), Decker Creek 2 (plant
  3548, 405 MW gas steam, Austin Energy municipal, 2022), plus <100 MW small units; V H
  Braunig 1–2 (477 MW gas_st, NSO-confirmed 2025-03 exits) are ABSENT from the scored
  actuals (EIA status OS, not RE). Read: against measured prices (R2), were ANY of these
  margin-negative vs their bars in their exit years? Expectation stated in advance: no —
  2021–2023 were high-revenue years for every thermal class (SOM §1), so the real exits are
  instrument/announcement-driven, not margin-driven, and no admissible margin screen can
  catch them.

**Comparability caveat, stated in advance:** SOM's CT/CC numbers are *new-unit proxies*
(HR 10.5/7.0); the screen's fleet rows carry unit heat rates (worse), so fleet-average screen
margins should sit BELOW the SOM new-unit numbers even at a correct price level. The replica
(R2) at matched assumptions is the like-for-like column; SOM anchors the level and the
reserves share.

## 3. Measured results

*(filled after the re-run's ledgers were read; nothing above this line changed after)*

TBD

## 4. The three answers (a)–(c)

TBD

## 5. Admissibility verdict per candidate fix

TBD

## 6. Governance position

TBD
