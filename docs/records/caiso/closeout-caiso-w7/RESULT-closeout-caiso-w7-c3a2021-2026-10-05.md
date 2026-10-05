# RESULT closeout-CAISO-w7: C3a 2021, L1 adjudicated I (rule 13); no admissible lever; ledgered (2026-10-05)

**Records.**
- `FINDING-closeout-caiso-w7-c3a2021-phase0-2026-10-05.md` (phase 0 + Addendum A, the circularity check).
- `PRECOMMIT-closeout-caiso-w7-intertie-rt-basis-2026-10-05.md` (never launched).

**Solves:** none. Zero LP throughout.

**Build on the lane branch only.** `caiso_intertie_print_rt_basis` and the RTM sibling artifact
(`claude/closeout-caiso-w7` @ `34d35456`) stay there as evidence. They do **not** land on `main` (desk ruling, rule
26: an inadmissible knob does not enter the registry). The OASIS RTM intake was stopped.

## 1. L1 `caiso_intertie_print_rt_basis` → I (desk ruling 2026-10-05, rule 13)

**What it was.** Price the hub-priced CAISO import ladder at the measured RTM intertie print instead of the DAM print.

**Why it is I.**
- The PALOVRDE / MALIN intertie LMPs are outputs of the same CAISO RT market C3a scores.
- In 2021 the RTM intertie mean sits within $1–2 of the scored hub mean.
- The rung is marginal in 80 % of hours, so L1 would price the margin at about the answer's level exactly where it binds.
- In 2022 the RTM print runs $10–12 below the hub, which would break the C3a low-side kill.

**Not circular by correlation.** The RTM intertie is not more correlated with the scored hub than the incumbent DAM
print is:

| Year | Series | Pearson r | Spearman | Mean gap vs hub |
|---|---|--:|--:|--:|
| 2021 | PV RTM | 0.614 | 0.903 | −1.07 |
| 2021 | MALIN RTM | 0.868 | 0.853 | −1.90 |
| 2021 | PV DAM | 0.523 | 0.859 | +4.76 |
| 2021 | MALIN DAM | 0.503 | 0.835 | +7.48 |
| 2022 | PV RTM | 0.663 | 0.881 | −12.04 |
| 2022 | MALIN RTM | 0.739 | 0.683 | −10.25 |
| 2022 | PV DAM | 0.838 | 0.900 | +3.88 |
| 2022 | MALIN DAM | 0.837 | 0.883 | +7.31 |

**No admissible external substitute:**
- EIA's ICE workbook is daily DA bilateral, peak block only.
- Hourly RT Palo Verde / Mid-C indices (Powerdex, ICE) are licensed.
- SRP, APS and BPA publish no LMP.
- WEIM ELAP prices are CAISO-market outputs.
- A structural RT import-offer discount would be an offset sized to the DART residual, which rule 13 forbids.

## 2. The bounded deeper look at the 2021 overnight level (desk, ≤ 1 h, zero LP)

**Volumes match.** Overnight (h0–5, Apr 27–Dec) the model's gas + geothermal + biomass is 8.67 GW against EIA-930
CISO gas 8.67 GW (CISO's NG cell folds geothermal and biomass). Imports are 8.1 GW model vs 7.6 GW EIA-930. The
overnight gap is **price, not volume**.

**Fuel is already measured.** The CC offers already sit on the measured daily CA citygate spot (`caiso_citygate_spot_level`,
`caiso_citygate_flow_date`, `gas_daily_shape`) and measured CEMS CC heat rates (`measured_cc_heat_rates`). Their monthly
path is gas × HR + carbon: SDGE CC econ bands run $39 in January to $63 in September.

**The wedge is about 1.4 MMBtu/MWh.** Market-implied overnight heat rate (hub RT net of about $8 carbon, over the
measured CA composite spot + $0.46 transport):

| Month | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| market | 7.11 | 6.30 | 6.46 | 7.88 | 6.80 | 6.88 | 7.34 | 7.21 | 6.36 |
| model | 9.49 | 8.56 | 8.02 | 8.60 | 8.01 | 7.93 | 8.17 | 8.10 | 7.71 |

**What explains the wedge:**
- About 0.5 of it is the authorized CC offer bands (econ_low ×1.066, econ_high ×1.072). That is the owner's one
  price-tuning channel (rule 1): set ex ante, one value across years, never swept against the gates. Not a lane lever.
- Testing a low-load heat-rate effect needs 2021 CEMS hourly heat input. It is not on disk: the shared CAMPD frame
  carries only `net_mw`, and `campd-facility-level` starts in 2023.
- No other measured substitution was found.

## 3. Disposition

**C3a 2021 is ledgered as a reference-premium / data-limited residual.**
- The model sits between DA and RT in every year (2021: −5.0 % vs DA, +10.6 % vs RT).
- 2021 carries CAISO's widest measured intertie DA−RT spread.
- The admissible levers are spent:
  - the hub-vs-DLAP basis (caiso-203 ruling 1);
  - the DSW own-BA shape (w2 / w4);
  - the zonal gas basis (in the keeper);
  - two-settlement (caiso-170);
  - L1 (I).
- The one remaining channel is the owner's offer-band channel.

**Where it is recorded.** L1's verdict is in the CAISO lever queue (`docs/mechanism-testing-matrix.md` §5.2). Because
the field does not land, neither does its matrix row (`check_mechanism_matrix.py` pairs rows to fields).

**Lane state.** Idle, awaiting the w6 promotion slot.
