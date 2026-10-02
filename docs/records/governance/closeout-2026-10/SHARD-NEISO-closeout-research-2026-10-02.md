# NEISO (ISO-NE) close-out research shard — 2026-10-02

Read-only. Zero LP. Keeper `2026-09-26-neiso-119-anchor-fuelsec`, bundle `results/calibration/neiso119_span`
(2019–2025, one shard per year, rubric v3.13, status part generated 2026-09-30). Determination **CALIBRATED** on
all registered years (`frontend/data/backcast/status/NEISO.js`: scored 8 / target 7 / ledgered 1 / fails 0;
`determination_scopes[0].failing = []`). The lane is closed; this report answers the four questions in the task
(robustness, regression exposure, 2025 re-score, the C3c tail) and gives the standard sections in compressed form.

## 1. Status table (year × criterion, from the committed status part)

| year | C1 fuelmix | C2 sysvol | C3a mean | C3b shape | C3c tail (RT >$300) | C4 gas r/NRMSE | C8 forced | determination |
|---|---|---|---|---|---|---|---|---|
| 2019 | PASS 7/7 (worst CC_REGULAR −1.8 pp) | PASS | PASS +7.9 % | PASS 0.112 | PASS 0 vs 0 | 0.934 / 0.145 | PASS 0.7 % | CALIBRATED |
| 2020 | PASS 7/7 | PASS | PASS −0.2 % | PASS 0.110 | PASS 0 vs 0 | 0.960 / 0.118 | PASS 1.6 % | CALIBRATED |
| 2021 | PASS 7/7 | PASS | PASS +4.0 % | PASS 0.123 | PASS 0 vs 2 | 0.959 / 0.108 | PASS 1.2 % | CALIBRATED |
| 2022 | PASS 6/6 | PASS | PASS +3.5 % | PASS 0.094 | **CAVEAT 0 vs 117** (DA 27) | 0.940 / 0.133 | PASS 1.1 % | CALIBRATED |
| 2023 | PASS 6/6 | PASS | PASS −1.9 % | PASS 0.097 | **CAVEAT 0 vs 15** (DA 5) | 0.939 / 0.103 | PASS 0.4 % | CALIBRATED |
| 2024 | PASS 6/6 (CT_PEAKER +0.59 TWh) | PASS | PASS +1.0 % | PASS 0.154 | PASS 0 vs 8 (small-count) | 0.951 / 0.092 | PASS 0.6 % | CALIBRATED |
| 2025 | SKIPPED (prelim. EIA-923: 13/30 CC_REGULAR, 3/7 CC_CHP plants missing) | SKIPPED (+0.9 %) | PASS +6.6 % | PASS 0.088 | **CAVEAT 0 vs 20** (DA 12) | 0.899 / 0.145 | PASS 0.4 % | CALIBRATED-WITH-CAVEATS |

Coal C2/C4 SKIPPED every year (immaterial, <5–10 TWh). Legitimacy diagnostics (`legitimacy_diagnostics.json`):
D2/D5/D9/D10 PASS; D1 FAIL on coal rows 2020–2023 (profile_r 0.71–0.79) and CT_PEAKER 2025 (cv_ratio 0.36); D4 FAIL on one
2021 `chp_steam` row (plant 54605, 2 binding hours, measured median 0 MW). Nothing blocks the determination.

**Hygiene flag.** The status part labels the 2022 caveat `ACCEPTED MODEL-CLASS LIMITATION` and 2023/2025
`ACCEPTED MEASURED-INPUT LIMITATION`, while `calibration_attestation.json.exceptions` carries 2023/2024/2025
`price_tail` entries all classified `MODEL MISS` (carried from neiso-72/99) and **no 2022 entry at all**. The
labels come from the C3c standing-rule auto-ledger, not an owner-signed `"kind": "model-class"` entry
(rubric v3.0, `docs/calibration-determination-rubric.md:624`). The 2022 and 2023 tails are not measured-input
limitations (see §4); the three labels should be reconciled to one owner-signed classification when the attestation
is next regenerated.

## 2. (a) Is the closure structurally faithful, or carried by a tuned band?

**DOF ledger** (`calibration_attestation.json.free_parameters`, 9 entries, 6 residual-identified):

| entry | value | identification | reviewer reading |
|---|---|---|---|
| `offer_curve_fossil_level_scalar` | 0.9547 (−4.53 % on 12 fossil bands) | price residual, rule-1 authorized channel (owner 2026-09-05/06) | the ONE price-tuned knob; sized once on the measured full-span pass-through (neiso-106), never swept against gates; properly declared in `governance.authorized_price_tuning` |
| `offer_curve_by_group` | 88 scalars | residual, in-sample 2023–25, ≥43 solves | the elephant: the band surface itself is fitted; the ledger says so (`root_cause: identified in-sample only`) |
| `offer_curve_committed_below_floor[NEISO]` | ST_GAS 0.79 | residual | open issue #1302 |
| `offer_curve_smoothing` | n=6, exp=1.0 | residual | shape of the econ ramp |
| `COAL_SIGMOID_DEFAULTS[NEISO]` | 4 scalars | residual, "weakly identified" | immaterial here (coal <1 % of load) |
| `wefor_multiplier` | 0.7 | residual | audit C-15 open |
| `reliability_floor` coeffs, `IMPORT/EXPORT_TRANCHES`, `st_gas_bands_corrected_class` | — | measured-physical | fine |

The two mechanisms the keeper armed on 2026-09-26 carry **zero new DOF** and are the right kind of fix:

* `gas_offer_margin_anchor_vintage` re-evaluates the frozen formula `phys×HR×fuel + (mult−phys)×HR×anchor` on the
  solve year's own delivered-gas mean instead of the 2023–25 mean 4.0763 (`scenarios.py:18276-18330`;
  `PRECOMMIT-neiso119 §1(d)`). At `fuel == anchor` the offer collapses to the registered band, so a year-matched anchor
  restores the condition under which the 88 bands mean what they were calibrated to mean; it is the same object class
  as `gas_prices`, forward-regenerable (rule 13). An expert would accept it and would note that it moved 2019 C3a from
  +10.03 % to +7.9 % — i.e. it corrected a linear-extrapolation defect, it did not tune a residual.
* `neiso_winter_fuelsec_conduct_roster` is a rule-17 repair: the floor bound plants CEMS shows offline in its own
  window (Middletown 0 %, Newington 1 %, West Springfield 0 % in 2019). The leave-one-year-out roster resolves to
  **nothing in 2019 and Schiller 2367 only in 2020–25** (`PRECOMMIT-neiso119 §3`), forced energy 0 / ≤0.037 TWh. The
  whole `neiso_winter_fuel_*` family (inventory, must-run, oil budget, coldsnap derate) is therefore **effectively
  dormant on every year** — the attestation already says "DORMANT on 2023–2025, unchanged vs the zero-forcing twin".
  Faithful, but a reviewer will ask why four armed mechanisms produce nothing; the honest answer (the record's own,
  `FINDING-neiso110 §3`) is that ISO-NE's winter oil burn is an availability/contract phenomenon the price-parity LP
  cannot generate.

**Where the closure is thinner than the grid suggests.** C3a passes in all 7 years but with a +3.0 % mean bias (5 of 7
positive) and a documented compensating structure: in EVERY year the model lifts RT ≤ $25 hours by +$1–5 and
under-prices RT > $60 hours (`PRECOMMIT-neiso119 §1(d)`: 2019 +4.93 / −1.98; 2022 +1.11 / −8.74; p5 model 20.6 vs RT
13.3). C3b is a monthly load-weighted NRMSE, blind to hour-of-day; the model's diurnal amplitude is 24–30 % of
measured (`FINDING-neiso74`, `diurnal_price_amplitude` **O**, not gated). 2022 monthly biases run +$15.9 (Jan) to
−$11.5 (Jul) and −$9.0 (Dec) (`neiso119/phase0_price_2022.json`). An expert reviewer would accept the level
calibration and flag that the within-day/within-month price structure is the un-scored residual that the band surface
was fitted around. Verdict: structurally faithful at the level the rubric scores, with one declared tuned scalar; the
88-band surface remains the unavoidable in-sample fit the ledger reports.

## 3. (b) What could regress NEISO when the EIA-860 vintage / capacity settlement lands

Capacity enters the NEISO solve through these armed paths (`run_config.json`, 80 True flags):

| mechanism (armed) | what it reads | exposure |
|---|---|---|
| `eia860_vintage_tracks_solve_year` | `data/raw/eia-860/vintage_2018…2024`; **no `vintage_2025`** → 2025 uses the canonical 2025 Early Release (`paths.py:114`) | a settlement that replaces the canonical snapshot or adds vintage_2025 re-keys 2025 (and 2019 if Pilgrim handling changes) |
| `mid_vintage_exit_carry`, `partial_plant_exit_carry` | retired-within-window parquet; vintage_2023/2024 ship no retired sheet (`eia860.py:3295`) | **Mystic 1588 (1,493 MW, retired 2024-05)** and **Pilgrim 1590 (736 MW, retired 2019-05)** are injected only through this patch (`r-neiso/PRECOMMIT §5`); any re-cut of the retiree parquet moves 2019 nuclear (2.18 TWh) and 2024 CC |
| `cc_nameplate_summer_derate` | EIA-860 nameplate vs net-summer per CC plant (`scenarios.py:16684-16708`) | a nameplate/net-summer reconciliation changes CC winter capability directly; CC_REGULAR C1 share sits at −1.8 pp (2019), the band is ≈ ±3 pp (neiso-118 moved 2019 from −3.46 FAIL to −2.3 PASS) |
| reserve co-opt rows (`energy_reserve_coopt`) | `cap[g,t] = pmax × availability` on fuel-name eligibility | dormant dual today, so capacity moves are invisible — unless response scoping (§5) is armed |
| `reliability_floor`, winter fuel-sec floor | pro-rata on `pmax` (`winter_fuel_inventory.py:541-581`) | dormant/near-dormant |
| measured heat-rate artifacts (`measured_cc/ct/st/coal_heat_rates`) | CAMPD unit → EIA-860 generator joins | the NEISO CT artifact was re-derived with a **class-preserving** `union_fleet` because Canal 3 (1599) flips to oil in the 2023–25 vintages (neiso-118); a settlement that re-maps units must preserve this |
| `gas_plant_monthly_fuel_pricing` | per-plant F923 delivered gas | Mystic 8&9 priced at their own F923 (Everett LNG) cost while carried — keep plant grain |

Known reconciliation facts in the records: Kendall 1595 CC_CHP — CAMPD gross 278–299 MW vs EIA-860 213/206 MW is a
metering-basis **artifact**, EIA-860 is correct (`FINDING-neiso73 §2`); GenConn Middletown 57068 (oil, 188–194 MW)
carries a class heat rate in every year (no eGRID row); Canal 3 filed OA/DFO-primary 2023–25 but burns gas
(`PRECOMMIT-neiso119 §1(c)`); the 2021 EIA-930 ISNE net-interchange wedge peaks at 12,307 MW ≈ 2.8× tie capability —
a corrupt TI hour (`FINDING-neiso111 §2.4`). Years at risk under any capacity change: **2019 (C3a +7.9 %) and 2025
(+6.6 %)** are the closest to the ±10 % line.

ISO-NE's own capacity ledger for the reconciliation program: the **Seasonal Claimed Capability** monthly workbook
(`scc_<month>_<year>.xlsx`, sheet `SCC_Report_Current`, per-asset summer/winter CC, fuel, zone) — the repo already has
the fetch path and the JS-tree workaround (`scripts/data/fetch_isone_scc_hydro.py` docstring), so extending it from
hydro to the whole fleet is a scripting task, not a data gap; and the **CELT report** (annual, May) for the
ICR/tie-benefit numbers already cited in `_neiso_config`.

## 4. (d) The C3c tail: anatomy, what is in representation, what is not

Measured anatomy (this shard, SMD `ISO NE CA` sheet, hourly RT hub > $300):

| year | RT h | DA h | months (RT) | event days | model h |
|---|---|---|---|---|---|
| 2022 | 117 | 27 | Dec 52 · Jul 15 · Feb 14 · Jan 11 · Mar 10 · Nov 7 · Aug 5 · May 2 · Jun 1 | Dec 23–26 **46 h** (Elliott; max $2,254 Dec-24 HE18), Mar-29 9, Feb-1/7 5+5, Jul-20 5, Nov-20/21 7, Jan-28 4 | 0 |
| 2023 | 15 | 5 | Feb 10 · Jul 1 · Sep 4 | Feb-3/4 arctic blast ×9, Feb-26, Jul-5 ($1,162 RT vs $129 DA), Sep-5/6 | 0 |
| 2025 | 20 | 12 | Jun 8 · Jan 5 · Jul 2 · Nov 2 · Feb/Aug/Dec 1 each | Jun-24 ×5 (PFP event, max $1,110), Jun-23/25, Jan-17/20/22, Nov-23 (PFP event) | 0 |

Primary-source facts (ISO-NE IMM): 2022 had **1.4 h** of negative Total30 margin, 0.1 h Total10, 48.1 h spinning;
2023 0.5 / 0.3 / 6.8; 2024 2.2 / 1.1 / 3.7; 2025 3.6 / 0.3 / 30.3 (2025 AMR Table 4-6, RCPFs $1,000 TMOR / $1,500 TMNSR /
$50 TMSR). Dec 24 2022: capacity scarcity ~1½ h, RT > $2,000 for 2.5 h, PFP event of 17 five-minute intervals moving
$35.9 M; "the leading cause of gas resource under-performance was high gas prices … over $30/MMBtu … relatively
cheaper oil generation was scheduled in the day-ahead" (2022 AMR p.6, p.11); Dec 24–27 Algonquin daily average
**$35.37/MMBtu** (2022 AMR p.29). Fast-start pricing lifted the 2022 system LMP by $5.68 (7 %) and reserve-pricing
intervals from 7.5 % to 13.5 % (2022 AMR Table 3-1). 2025: two shortage events (Jun-24, Nov-23), both PFP; oil marginal
for 3 % of load; DA A/S (DASI) from 2025-03-01 (2025 AMR §4.6, §3.3.1).

**Reading.** Only ~2–4 h/yr of the RT tail are RCPF-driven reserve shortages; the rest is energy-offer formation on
cold/hot days (oil-steam and fast-start offers above cost, fast-start pricing, five-minute transients). Two things ARE
in representation and are wrong today:

1. **The model never sees the Elliott gas price.** `data/raw/gas-prices/algonquin_citygate_daily.csv` (repaired at
   neiso-109) holds Wednesday prints only: Dec-21 $6.51, next print Jan-4; the daily shape interpolates across the
   gap (`hubs.py:1550` docstring), so the model's delivered gas on Dec 24–27 reads **$12.5–15.1** (`FINDING-neiso110
   §3`) against a measured **$35.37** daily average. January 2022 (prints $18.96 / $22.69 / $20.71) is flattened the
   same way — the model over-prices the January MEAN (+$15.9) and prints zero tail hours. This is a measured-input
   resolution gap, admissible to fix under rule 14, and it is why the 2022 caveat should not be labelled "measured-input
   limitation" without the input being fixed first.
2. **Reserve eligibility is a fuel-name test** (`model/reserves/spec.py::_neiso_design`): 2,855 MW of oil STEAM
   boilers count as ten-minute reserve and 98.95 % of the Elliott-hour headroom is cold iron (`FINDING-neiso111 §5`).
   Rule 18 violation; the LP already carries `online_gated` / `reserve_supply_cap` machinery that PJM/MISO/CAISO use
   and NEISO does not.

What is NOT closable in the model class: 14/15 (2023) and 14/20 (2025) tail hours are RT-only (DA < $300); the real DA
cleared ≥ $300 in only 5 h of 2023 against a gate floor of 8 (`CHARTER-neiso75 §2.4`); 2022's 46 Elliott hours would
need sustained $1,000-RCPF shortage the system itself had for 1.4 h. **Pay-for-Performance** is a capacity-market
settlement ($3,500/MWh rate through May 2024, $5,455 from June 2024, $9,337 from June 2025 — 2025 AMR fn.) that changes
offer incentives, not the LMP; the **Inventoried Energy Program** (Dec–Feb 2023/24 and 2024/25, $92.51 and $79.00/MWh,
$79 M / $78 M) pays for inventory, not dispatch; the **Mystic COS** (Jun 2022–May 2024, Mystic 8&9 retired 2024-05-31)
kept 1.7 GW in the fleet — already carried by `mid_vintage_exit_carry`. None of the three is an LMP mechanism, so none
is a rule-13 route to the tail. Ledger C3c as model-class in all three years **after** items 1–2 are fixed for accuracy.

## 5. Retest candidates (rule 28: only with new evidence)

| cell | prior verdict / evidence | why the premise changed | target | direction | cost |
|---|---|---|---|---|---|
| `dynamic_reserve_requirements` | R — neiso-57 (2026-07-10) as a price-formation lever; re-sized neiso-111 2026-09-17 | (i) rule 22 removed 2026-09-09, the 2019–22 windows are fetchable (`fetch_neiso_reserve_requirements.py` probed OK); (ii) published columns are NESTED (spin ⊂ 10-min ⊂ 30-min), so the three static rows (3,600 MW) overstate the aggregate by 1,246 MW at Elliott — the mechanism is a loosening, not the tightening neiso-57 tested; (iii) with response scoping it crosses at Elliott by 82.5 MW | C3c 2022/2025 fidelity | prints single hours on Dec-24-2022 and Jun-24-2025 (neiso-57: $397 at Jun-24 18:00); gate stays unmet | data intake (7 yrs) + full span |
| `dam_availability_rebasis` (ISO-NE Morning Report operable capacity) | R — neiso-62 (2026-07-24): source restores capacity, C3a improves every year, NOT adopted on a fleet-wide denominator applied thermal-only; found CAMPD extract over-counts thermal outages ~15 pp | the CAMPD outage chain has since been re-derived (unit-fuel routing, short gas windows K at R-NEISO 2026-09-24, per-unit clips); the denominator objection is addressable with the per-class thermal basis now in `unit_marginal` | Elliott headroom (2,275 MW real outages Dec-24) | neutral-to-up on winter prices | probe (zero-LP denominator check) then full span |
| `gas_coldsnap_derate` (K, dormant) | kept; "removes too little capacity" | neiso-110 established the switch is availability- not price-driven; a derate re-identified on the Morning Report outage series (above) replaces it (rule 19) | 2022 Dec | — | folds into the row above |

Not retested (premise unchanged): `measured_offer_surface` I (neiso-58: tail forms while the model holds GW of cheaper
headroom), `da_virtual_bids` R (neiso-76: book flat/moves the wrong way), `pumped_storage_cycling_depth` G (blocked
until amplitude closes), `neiso_rcpf_postsolve_overlay` G (rule-19 hard error under co-opt).

## 6. New levers

| name | mechanism | measured driver | forward story | gate | expected | risk |
|---|---|---|---|---|---|---|
| **Algonquin daily completion** | fills the Wednesday-only gaps in the AGT daily basis so `iso_hub_daily_gas_prices` places real event-day prices | free partial sources only: EIA NG Weekly narrative (on disk), EIA Today-in-Energy event notes, FERC/NERC Elliott final report (daily Northeast prices, Nov 2023); full daily index is ICE/NGI (paid) | same class as `gas_prices`; forward shape from the forward trajectory | C3c 2022 (Dec/Jan), C3a Jan-2022 bias | Dec 24–27 model gas $15 → ~$35; CC offers → ~$250, oil parity $21 binds; tail hours still 0 unless reserves bind; January level bias falls | partial coverage; must be mean-preserved against the F923 monthly level the keeper already uses |
| **Response-scoped reserve eligibility** (`reserve_deliverability_scoping` U → NEISO field) | offline units count toward 10/30-min reserve only if fast-start (CT classes; oil GT/IC by EIA-860 prime mover); online units contribute headroom | EIA-860 prime mover + class; zero scalars | pure physics (rule 18) | C3c 2022/2025 | alone: 0 short hours (class-1 min 1,494.9 MW vs 1,200); with measured requirements: −82.5 MW at Elliott → RCPF stacks for ~1–2 h | the 30-min family goes short 27 h in 2022 against the static 1,800 MW — must be armed WITH the measured requirement, never alone (neiso-111 §6) |
| **NY Harbor ULSD daily oil shape** (`dual_fuel_oil_daily_parity`) | mean-preserving within-month daily oil parity | `data/raw/oil-prices/ny_harbor_ulsd_daily.csv` (2022–25); EIA series `EER_EPD2F_PF4_Y35NY_DPG` is daily back to 1986, so 2019–21 is a free download | measured, forward daily shape | accuracy (rule 14), not a gate | small; neiso-110 §2.1 refused to arm it on 2022–25 only because that would look like residual-shaving | arm only with full-span coverage and its own accuracy PRECOMMIT |
| Mystic LNG pricing check | verify Mystic 8&9 (1588) take their own F923 delivered gas (Everett LNG) 2019–May 2024 under `gas_plant_monthly_fuel_pricing` | EIA-923 Schedule 5 plant rows | plant-grain fuel is forward-regenerable | C1 CC_REGULAR 2019–23, winter price | small; zero-LP check | none if already true |
| `admit_standby_units` (U) | SB generators by status | EIA-860 status | — | C1 | NWPP sized its own footprint; NEISO's unknown | probe only |

Not admissible, named so nobody proposes them: any oil-steam or fast-start offer adder sized to the tail; pinning oil
burn to CAMPD (`dual_fuel_measured_oil_burn` — the F923 receipts budget was already rejected as "a measured answer",
`coal_receipts.py:14`); an RCPF overlay stacked on the co-opt.

## 7. External research — primary vs inference

Confirmed from primary sources: 2022 AMR (https://www.iso-ne.com/static-assets/documents/2023/06/2022-annual-markets-report.pdf)
pp. 6, 11, 29, 82, 187; 2025 AMR (https://www.iso-ne.com/static-assets/documents/100035/2025-annual-markets-report.pdf)
§1 (No. 2 oil $14/MMBtu 2025), §3.3.1 (DA A/S one-year review), §4.6 Table 4-6, §7.3 (PFP June and November 2025),
DA premium $5.93 (highest in five years); ISO Newswire winter 2022/23 recap (RT avg $79.53, Dec-24 PFP $36 M, Feb-4 RT
≈ $500, 13.5 M gal oil → 165 GWh): https://isonewswire.com/2023/04/06/winter-2022-2023-recap-wholesale-prices-drop-during-warm-season-marked-by-cold-snaps/;
winter 2024/25 (RT avg $114.80, coldest in a decade, IEP $78 M): https://isonewswire.com/2025/06/11/cold-winter-drove-higher-energy-prices-market-monitor-finds/;
IEP page (rates $92.51 / $79.00): https://www.iso-ne.com/markets-operations/markets/inventoried-energy-program;
Mystic COS Jun 2022–May 2024, units retired 2024-05-31: https://www.constellationenergy.com/about/locations/mystic-generating-station.html;
DASI live 2025-03-01, four products TMSR/TMNSR/TMOR/EIR as call options on RT energy: https://www.iso-ne.com/participate/support/participant-readiness-outlook/day-ahead-ancillary-services-initiative;
SCC monthly report tree: https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/seasonal-claimed-capability;
CELT: https://www.iso-ne.com/system-planning/system-plans-studies/celt; FERC/NERC Elliott final report (Nov 2023):
https://www.ferc.gov/news-events/news/ferc-nerc-release-final-report-lessons-winter-storm-elliott.

My inference: the 2022 tail outside Elliott (Jan–Mar 35 h, Jul/Aug 20 h, Nov 7 h) is oil-steam/fast-start offer conduct
plus fast-start pricing on $20–30 gas days, not reserve shortage (Table 4-6 shows 1.4 h Total30 for the whole year);
the model's oil parity (~$258/MWh) saturates just under $300, so even a perfect fuel input prints few of those hours.
How other models treat this: ISO-NE's own IMM uses the DA/RT clearing engines with RCPF demand curves; NREL/EIA-class
dispatch models (ReEDS, NEMS) do not score tail-hour counts at all (rubric §C3c cites the same). The model's co-opt
with RCPF-shaped scarcity (`ordc_scarcity_overlay` K, `energy_reserve_coopt` K) is the right structure; what is missing
is the supply-side physics (§6 row 2) and event-day fuel prices (§6 row 1).

## 8. (c) What the 2025 full-year re-score needs

| input | state on disk | action |
|---|---|---|
| EIA-923 2025 per-plant monthly (`data/raw/_processed-legacy/eia923_monthly_generation.parquet`) | preliminary vintage: 13/30 CC_REGULAR and 3/7 CC_CHP plants missing → C1/C2 SKIPPED | fetch the 2025 **final** release (`https://www.eia.gov/electricity/data/eia923/` → `f923_2025.zip`; a PUDL PR dated 2026-09-29 reports the final 2025 release is out — verify on the EIA page), rebuild the parquet, `run_calibration_full.py --rebuild-benchmark --iso NEISO`, `check_bench_freshness`; the neiso-113/116 recipe. The Page-1 annual CSV (`eia-923-generation-fuel`, fetched 2026-09-25) is a separate artifact and only feeds heat-rate fallbacks |
| EIA-930 ISNE 2025 | `EIA930_BALANCE_2025_Jan_Jun` + `Jul_Dec` parquets present; 2025 solved on it | none |
| ISO-NE SMD 2025 | `2025_smd_hourly.xlsx`, 8,760 hub hours parsed here (RT 20 h > $300) | none |
| EIA-860 2025 final vintage | absent (`vintage_2018…2024` only; 2025 on the 2025 Early Release) | add `vintage_2025` when the settlement program fetches it; expect 2025 re-key |
| CAMPD 2025 Q4 (outage windows, heat rates, CEMS rates) | not verified in this shard | confirm the NEISO CAMPD artifacts cover Oct–Dec 2025 before re-scoring |

A C1/C2 re-score on the final 923 can move the 2025 CC_REGULAR share (model 60.04 TWh forced-share basis); 2025 C3a is
already +6.6 %. Re-score is zero-LP unless a benchmark-side builder change is classed LIVE under G-DRIFT.

## 9. Data gaps (FREE)

| what | gate | source | directions | lands in | effort |
|---|---|---|---|---|---|
| EIA-923 2025 final | C1/C2 2025 | https://www.eia.gov/electricity/data/eia923/ | `f923_2025.zip`, Schedules 2–5 M_12 Final; same loader as 2019–24 | `data/raw/eia923/` (existing path) | low |
| EIA-860 2025 final | 2025 vintage | https://www.eia.gov/electricity/data/eia860/ | `eia8602025.zip` → `vintage_2025/` | `data/raw/eia-860/vintage_2025/` | low |
| ISO-NE reserve requirements 2019–2022 (ROS location 7000, 10/30-min, nested) | §5 row 1 | ISO Express (`fetch_neiso_reserve_requirements.py --years 2019 2020 2021 2022`, isox_token bootstrap) | 15-day windows, CSV | `data/raw/NEISO-AS/requirements/` | low |
| NY Harbor ULSD daily 2019–2021 | §6 row 3 | https://www.eia.gov/dnav/pet/hist/EER_EPD2F_PF4_Y35NY_DPGD.htm | extend `ny_harbor_ulsd_daily.csv` to 2019-01-01 | `data/raw/oil-prices/` | low |
| Algonquin daily spot on event days | §6 row 1 | FERC/NERC Elliott report (link §7); EIA Today in Energy Elliott/Jan-2022 notes; ISO-NE Winter QMR charts (figures, not tables) | hand-transcribe event-week dailies with page citations; full daily index is paid (NGI/ICE) — list as partial | `data/raw/gas-prices/algonquin_citygate_daily.csv` (source tag) | medium, partial |
| SCC monthly workbooks (full fleet) | §3 reconciliation | SCC tree (link §7); fetcher pattern exists | Jan/Jun vintages 2019–2025, `SCC_Report_Current` | `data/raw/capacity-market/scc/neiso/` | low |
| ISO-NE Morning Report operable capacity | §5 row 2 | already committed 2018–2026 (`data/raw/neiso-operable-capacity/`) | none — wiring patch `neiso-operable-capacity-cli-flag.patch` was applied at neiso-62 | — | none |

## 10. Recommended close-out sequence

1. **Zero-LP, now:** reconcile the three C3c caveat labels into one owner-signed `model-class` entry (§1); confirm
   Mystic 1588 per-plant LNG pricing (§6); fetch EIA-923 2025 final and re-score 2025 C1/C2 (§8). Probability the
   determination changes: low (it is CALIBRATED either way); probability 2025 loses "with-caveats": high.
2. **Zero-LP accuracy repairs (rule 14, no gate claim):** extend ULSD daily to 2019; transcribe Elliott-week and
   Jan-2022 Algonquin dailies from the free primary sources; fetch 2019–22 reserve-requirement windows. Each is an
   input change with a `[R-FROZEN-DERIVE]` citation to the data, not to the residual.
3. **One full-span shard set (7 legs):** `gas_daily_shape` on the completed AGT series + ULSD daily + response-scoped
   reserve eligibility + measured nested requirements, pre-registered together as the ISO-NE scarcity-physics arm
   (rule 19: the measured requirement REPLACES the three static rows; scoping is a sub-gate of the co-opt). Pre-fixed
   readings: Dec 24–27 2022 model price rises to oil parity; 1–3 RCPF hours on Dec-24-2022 and Jun-24-2025; C3a 2022
   Jan bias falls; no C1/C3b status change. Probability it closes any C3c gate: **low** (2022 needs ≥ 59 h, 2023 ≥ 8 h
   of which the real DA had 5, 2025 ≥ 10 h vs ~3.6 h of real shortage). Probability it improves structural fidelity
   and removes the rule-18 defect: high. Promote on rule 1 if nothing regresses.
4. **Ledger what remains:** C3c 2022/2023/2025 as model-class (RT-only formation, oil-offer conduct, five-minute
   transients) and the diurnal-amplitude residual (O, unscored) — unless the owner adds a hour-of-day criterion.
5. **Regression guard for the EIA-860 program:** before any NEISO re-key, run the `lp_input_diff.py` census
   (neiso-119 pattern) on 2019 and 2025 fleets and require Pilgrim/Mystic carries, Kendall basis and Canal 3 class to be
   byte-stable; a C3a move of > 2 pp in 2019 or 2025 is the tripwire.

## 11. Open questions for the owner

1. Sign one C3c classification for 2022/2023/2025 (model-class) now, or hold until step 3 has run?
2. May the ISO-NE scarcity-physics arm be built (new field `neiso_reserve_response_scoped`, one PR, matrix row + 9
   cells), given it is unlikely to move a gate and is justified on rules 14/18 alone?
3. Is hand-transcribing event-week Algonquin dailies from FERC/EIA reports acceptable provenance, or must a daily
   series come from one continuous published source (which does not exist for free)?
4. Should the dormant `neiso_winter_fuel_*` family stay armed in the keeper recipe (faithful but inert) or be removed
   from the recipe under rule 26 with its dormancy recorded?
5. For the EIA-860 settlement: adopt ISO-NE SCC (seasonal claimed capability) as the NEISO capacity reference and EIA-860
   as the vintage/COD reference, with the per-plant reconciliation table committed under `data/raw/capacity-market/scc/`?
