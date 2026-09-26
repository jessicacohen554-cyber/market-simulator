# PRECOMMIT — R-CAISO-4: the thin margins and Pastoria's 2024–25 residual (2026-09-26)

Lane R-CAISO-4. The keeper is `2026-09-25-caiso-r3-abc-import` (bundle `rcaiso3_ABC_span`, 2022–2025, legs pinned
at `d666fd94d031123138761b58ef31b32beffac70c`). It is CALIBRATED under rubric v3.9 with a single ledgered C3c 2024,
on thin margins: C3a 2023 +9.7 % against ±10 %, and C4 2025 gas NRMSE 0.299 against ≤0.30. The parent solves
nothing (rule 32(a)). **Every number below is zero LP and was written before any shard launched.**

Lever queue (rule 28(a)): both levers below are **off-queue**. Neither is in §5.2. Each is a measured-input
defect found by phase 0 from data, and neither re-tests an R/I/G cell. D is the measured-data successor to the
R-CAISO-3 cell `caiso_intertie_gap_fill_measured_gas`, which stays K. E is the rule-19 completion of R-CAISO-3
lever C.

## 1. C3a 2023 +9.7 %: the Jan–Feb 2023 intertie gap is filled by formula where measured prints exist

**Decomposition** of the load-weighted gap, from the committed payload against the bench `rt_lw_mon`. Share of
the +9.71 % by month: Jan **+3.55 pp** (model 152.9 vs RT 129.7 $/MWh), Feb **+1.57** (78.1 vs 66.4), May +1.67,
Jun +0.97, Aug +0.97. Every other month is under +0.7 pp, and Apr, Jul and Oct are negative. The gap is flat
across zones: LA_BASIN / NP15 / SDGE / SP15_rest / ZP26 sit at 59.3 / 59.4 / 61.0 / 59.3 / 58.6.

**The Jan–Feb 2023 hours ARE in the RT benchmark.** The committed `CAISO_rtm_hourly_2023.csv` carries TH_NP15 /
SP15 / ZP26 for 696 h in January and 672 h in February, and the bench `rt_lw_mon` has all 12 months, so C3a
scores Jan–Feb unmasked. Two comments are therefore false for C3a:

- `measured_import_hub_prices` says of the filled hours that they "are the same hours absent from the
  actual-LMP benchmark";
- R-CAISO-3 PRECOMMIT §5 said the same.

Correcting those comments is routed to a doc sync; it is not changed here.

**The cause.** The main intertie series (`wecc_intertie_lmp_hourly_CAISO.parquet`) is a **DA** series. That was
verified on 2022: it is identical to the committed DAM aggregate at MAD 0.0 / 0.028 $/MWh, against RT, which gives
a corr of only 0.56–0.81. The series has a 2,040-h retention gap from 2023-01-01 to 03-26. R-CAISO-3 lever B
fills that gap with `(N3045 state delivered gas) × HR × shape`. **But the tracked `CAISO_dam_hourly_2023.csv`
aggregate still PRINTS MALIN / CAPTJACK / PALOVRDE with MCE/MCC/MCL for 1,488 of those hours** (January 672,
February 648, March 1–7 168). In those hours B's formula runs far above the prints, because the monthly state
delivered gas lags the January spot collapse:

| $/MWh, month mean | measured DAM print | B fill (keeper) | forward fill |
|---|--:|--:|--:|
| Malin Jan / Feb / Mar(1–7) | **138.1 / 72.0 / 90.5** | 237.4 / 80.4 / 64.0 | 34.5 / 33.5 / 33.2 |
| Palo Verde Jan / Feb / Mar(1–7) | **134.0 / 65.1 / 73.9** | 216.7 / 90.2 / 46.0 | 39.3 / 36.5 / 35.2 |

Paired over the 1,488 hours, B's error is MAE 59.4 / 55.8 $/MWh with a bias of +45 / +45, at corr 0.70 / 0.80.

**Lever D — `caiso_intertie_gap_fill_measured_dam`** (new, CAISO-only, default off). Rule 14: use the measured
data over an estimate.

- `fetch_caiso_intertie_lmp.py --from-hourly-aggregate --fill-gaps --years 2023` writes a **sibling artifact**,
  `wecc_intertie_lmp_hourly_CAISO_gapfill_dam.parquet` (sha256 `22f79da7…`, 2,976 rows = 2 hubs × 1,488 h).
  It holds only the hours the main series leaves NaN and the aggregate prints, and it uses the main series' own
  construction (i-caiso proved that route byte-identical on 2022, max |diff| 1e-4).
- **The main parquet is untouched** (`b44acc27…`).
- Armed, both loaders fill those hours first:
  - `measured_import_hub_prices`, which is the per-hub price;
  - `measured_intertie_hub_price_raw`, which is the clean-depth evidence. A DAM print is evidence of a market
    state; a formula fill is not.
- The remaining 552 gap hours (the unprinted January/February days and Mar 8–26) keep B's fill.
- **Zero parameters.** D is inert outside 2023 by construction, because no other year has a gap.

**Zero-LP footprint** (fleet rebuild, 2023, arm − HEAD): only `WECC_*` rows move, and only January–March.

| Δ mc_base, month mean ($/MWh) | Jan | Feb | Mar | Apr–Dec |
|---|--:|--:|--:|--:|
| PNW_midC, export_MALIN | −89.7 | −7.8 | +5.9 | 0 |
| DSW_CCGT / CT / scarcity / clean tranches, export_PALOVRDE | −75.1 | −24.0 | +6.4 | 0 |

The four clean-depth tranches (`surplus`, `overnight`, `daytime`, `lateevening`) also change **availability**,
because they now arm in the newly measured hours. **Every in-state row is byte-identical.**

**Not a lever, reported:**

- **In-state gas, Jan–Feb 2023.** The model's committed CCs clear at about 127–134 $/MWh in January; the
  in-state operand is `N3050CA3` + HH. With D, the January import stack falls toward the measured hub, so the
  in-state gas level is left untouched and is not opened here.
- **The Dec-2022 N3050 11.42 vs N3045CA 27.7 $/MMBtu gap** stays routed.
- **The static DSW_solar_PV block's Dec/Jan coupling** stays as R-CAISO-3 §2 recorded it.

## 2. Pastoria 2024–25: the refused CEMS record re-enters through the carbon cost

**Census** (fleet rebuild, keeper recipe). Pastoria and High Desert are built identically:

- tranche structure: committed ≈ measured HR, and 6 econ tranches at +6.6 %;
- availability: Pastoria's annual capability is 5.99 / 5.56 TWh in 2024 / 2025, against 2.37 / 2.14 dispatched,
  so **availability is not binding**;
- gas price: identical.

The difference is **the committed tranche's mc**: Pastoria **38.49** against High Desert **36.56** $/MWh in 2024,
even though Pastoria's heat rate is 7.039 against 7.201. In 2023 the figures are 56.56 against 55.52. Solved on
the 2024 committed tranches, gas is about 3.22 $/MMBtu and carbon about 30 $/t, and Pastoria's emission rate is
the residual:

| plant | HR applied | CO2 rate (v2) | CO2 / HR (t/MMBtu) |
|---|--:|--:|--:|
| Pastoria 55656 (2023–25) | 7.04–7.08 | **0.446** | **0.063** |
| High Desert 55518 | 7.14–7.24 | 0.374–0.380 | 0.053 |
| Moss Landing 260 | 7.28–7.34 | 0.357–0.360 | 0.049 |

`plant_emission_rates_v2` books CO2 = CEMS CO2 ÷ CEMS load. For Pastoria from 2020 on that is 8.28 MMBtu of CEMS
heat input per MWh × 53.9 kg/MMBtu. It inherits both of the defects R-CAISO-2 and R-CAISO-3 refused: the ×1.09
heat input, and gross < net. Lever C moved the **heat rate** onto EIA-923 fuel ÷ net, but the **CO2 rate** stayed
on the refused record. The result is **about +2.2 $/MWh on every Pastoria tranche** at CA allowance prices. That
is a rule-19 defect: one refused measurement enters through a second channel.

**Corroboration (not a criterion).** `plant_emission_rates_v2` has **no 2022 CAISO rows**, so in 2022 every
plant carries the proportional default (er/hr = 0.057 t/MMBtu) and Pastoria has no wedge. 2022 is exactly the
year its dispatch matched actual (3.39 against 3.29 TWh). In 2023–25, with the wedge, it runs at 2.14–3.58
against 3.62–4.34.

**Lever E — `cc_eia923_identity_emission_basis`** (new, default off; inert in any ISO whose CC artifact has no
`eia923_identity` row).

- A CC_REGULAR row whose applied measured-CC row is flagged `eia923_identity` books
  CO2 = identity HR × the plant's own pooled CEMS CO2 per MMBtu.
- Only the MMBtu/MWh basis moves; the measured fuel CO2 factor is kept.
- **Zero parameters.** It requires `measured_cc_heat_rates` and `use_plant_emission_rates_v2`.

**Zero-LP footprint** (arm − HEAD): only identity-plant CC rows that carry a v2 rate move, as follows.

| committed tranche | 2023 | 2024 | 2025 |
|---|---|---|---|
| Pastoria er, t/MWh | 0.4463 → **0.3793** | 0.4462 → **0.3795** | 0.4464 → **0.3815** |
| Pastoria mc, $/MWh | 56.56 → **54.35** | 38.49 → **36.14** | 38.91 → **37.09** |
| Sanger 57564 | not in the identity set | er 0.5505 → 0.4836 | not in the identity set |
| Carson 10169 (49 MW) | Δmc −0.8 | Δmc −0.1 | Δmc −0.8 |

2022 is byte-identical (no v2 rows). Desert Star's 2024 identity row carries no v2 rate, so it is untouched.
High Desert and every other plant are byte-identical.

## 3. C4 2025 0.299: a midday-commitment shape, not a level, and no lever taken

Recomputed on the CEMS basis from committed artifacts, the result reproduces the scorer: r 0.880, NRMSE 0.2987.

- **Bias** is 2 % of the MSE, so **98 % is shape**.
- **By hour of day:** the model runs 1,000–1,250 MW too little gas in h8–h16 and 600–700 MW too much in h18–h23.
  The same signature appears in 2023 (−1,200 midday, +900 evening).
- **By month:** August–December carries 59 %.
- **By plant:** Moss Landing is over by 1.5 TWh, Pastoria under by 1.24, Alamitos / Huntington Beach over,
  Colusa / Gateway under.

This is the midday loading defect caiso-135 named, and raising `min_load_frac` is do-not-redo. **No lever is
taken for C4.** E moves Pastoria, which is the second-largest plant contributor, so C4 moves as a consequence and
is reported at full magnitude.

## 4. CEMS vs EIA-923 heat-input census: report only

Ratios of CEMS heat input to EIA-923 fuel (via eGRID ÷ identity) outside ±5 % in 2022–25:

| plant | ratio | effect |
|---|--:|---|
| Mountainview 358 | 0.94–0.95 | applied 7.27–7.52 vs EIA-923 7.77–8.07, so priced about 6 % cheap |
| El Segundo 57901 | 0.71–0.75 | applied 8.4 vs EIA-923 9.3 |
| Moss Landing 260 | 1.02–1.05 | — |
| Blythe 55295 | 1.03–1.05 | — |
| Desert Star 55077 | 2024 0.93, 2025 0.91 | — |

None is refused by the CC derive's gross-net identity, so **no physical-identity basis applies**. A tolerance on
this ratio would be a fitted threshold, so none is proposed.

## 5. G-DRIFT (rule 29(b)): keeper pin `d666fd94d031…` → this lane's base

- **Code audit.** Every hunk in `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib` and `data/raw`
  from the pin to HEAD is **INERT for CAISO**:
  - `nwpp_demand_plant_basis` (NWPP);
  - `coal_committed_nested_on_mustrun` and `wefor_residual_short_screened_coal` (NWPP / MISO, off, absent
    from the recipe);
  - `unit_outage_membership_repair` and `pjm_zonal_gas_basis_skip_923_priced` (PJM);
  - `nuclear_dormancy_defers_to_vintage_exit` (off);
  - `nyiso_ldc_generator_delivered_gas` (NYISO);
  - data files for PJM / MISO / NYISO / NWPP only;
  - no CAISO data change.
- **Mechanical proof.** The fleet was rebuilt from the keeper bundle at the pin (its own code, via `git archive`)
  and at HEAD with this lane's code and both new flags off, for 2022–2025. `pmax`, `pmin`, `availability`,
  `min_gen`, `heat_rate`, `vom`, `emission_rate`, `nox_rate`, `zone_idx`, `mc_base`, `demand` and the VRE arrays
  are **byte-identical in all four years**. That also proves D and E are byte-identical off.

**Form 4 is valid. The keeper's committed bundle is the control, and no control solve is spent.**

## 6. Shard plan (rules 32, 34, 36)

Recipe: `scripts/replay_keeper.py results/calibration/rcaiso3_ABC_span --years <Y>`, plus `--set` for each flag.
There is one year per shard, and each shard pushes its full bundle.

| shard | year | flags | out-dir |
|---|--:|---|---|
| r-caiso-4-DE-2022 | 2022 | D + E | `results/calibration/rcaiso4_DE_2022` |
| r-caiso-4-DE-2023 | 2023 | D + E | `results/calibration/rcaiso4_DE_2023` |
| r-caiso-4-DE-2024 | 2024 | D + E | `results/calibration/rcaiso4_DE_2024` |
| r-caiso-4-DE-2025 | 2025 | D + E | `results/calibration/rcaiso4_DE_2025` |
| r-caiso-4-E-2023 | 2023 | E | `results/calibration/rcaiso4_E_2023` |

- **Candidate DE span** = the four DE legs.
- **Attribution:** D (2023) = DE-2023 − E-2023; E = E-2023 − keeper, and DE − keeper in 2024–25 (where D is
  inert).
- 2022 is fleet-identical to the keeper, so its leg must reproduce the keeper's 2022 to solver precision. That
  is **G-REPRO**, a free control on the composition, not a spent control solve.

## 7. Stated before the solve

**Direction, not a gate.**

- **D:** January 2023 import offers fall 75–90 $/MWh, so January imports rise, CC_REGULAR falls and the January
  price falls. Expect C3a 2023 to move down from +9.7 % and C1 CC_REGULAR 2023 to move down from +1.60 TWh,
  giving back part of B's CC gain. B's January fill was above the measured hub, and that pushed CC up by more
  than the measured hub warrants.
- **E:** Pastoria rises in 2023–25 and displaces other SP15 / LA_BASIN CC, so the CC_REGULAR total moves little.

**Size is not a criterion, and neither flag is resized against any result (rule 1 (c)).**

**Named risks:**

- C1 CC_REGULAR 2023 has a margin of 3.67 TWh and D moves it down.
- C3b 2023 (0.162) could move either way.
- C4 2025 sits at 0.299, and E reshuffles plants there.

**Stop gates (they can kill an arm; none promotes one):**

- **G-IDENT.** Each leg's `run_config.json` differs from the keeper leg only in the declared flag(s).
- **G-FOOT.** In the leg's rebuilt fleet only the rows in §1/§2 move, within ±0.5 $/MWh of the tables.
- **G-LIVE.** Pastoria's committed-tranche mc is below High Desert's in 2023–25, and January 2023 DSW hub
  prices in the leg match the measured prints.
- **G-REPRO.** The DE-2022 class TWh equals the keeper's 2022 to within 0.01 TWh.

**Not a keeper if** any of these happen:

- a load-bearing criterion (C1/C2/C3a/C3b) flips PASS → FAIL in any year;
- C6 or C8 fails;
- a second ledgered caveat appears;
- any leg's signature differs.

The owner may still promote on structure (rules 1, 31).

Offer-curve multipliers are unchanged, the DOF ledger stays 9/6, and there is no `authorized_price_tuning` block.

## 8. Routed, report only (rule 25)

- **Other ISOs' CC artifacts** inherit the CEMS heat-input basis and carry gross < net rows: ERCOT 14, MISO 10,
  NEISO 6, NWPP 5, NYISO 6, PJM 23, SPP 1. **Their `plant_emission_rates_v2` CO2 rates carry the same basis**, so
  if a lane lands its own EIA-923 identity rows, E applies there once that lane arms it. The EIA-923 intake
  `data/raw/eia-923-generation-fuel` is ISO-neutral.
- **D's side-effects on frozen derives (rule 23).** D does not change the main parquet, so no committed constant
  moves. Two derives would change on re-run, and neither is re-derived by this lane:
  - `derive_caiso_import_tranches.py` (`IMPORT_TRANCHES_BY_YEAR["CAISO"]`) would move 2023 PNW_midC 90.5 → 143.2
    if re-run over a filled series, and would FAIL its own stability gate on three rungs;
  - the 2023 MALIN annual mean behind NWPP's interface constant (40.076) would also change on re-derive.
- **Stale comments** (§1) in `envelopes.py` and `calibration_verdict.py`: the Jan–Feb 2023 hours are in the RT
  benchmark.

## 9. Owner decision still owed (2019–2021)

The supply-consistent demand guard needs one of two choices: (a) rebuild the guard on the measured EIA-930 basis
for 2019–21, or (b) re-derive the fold-in for all years, which moves the 2022–25 keeper inputs.
`docs/handoffs/i-caiso/INTAKE-i-caiso-2019-2021-2026-09-24.md` §1. 2019–21 is not solved until the owner rules.
