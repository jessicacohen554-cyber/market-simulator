# FINDING — SPP-109: the sub-5-day gas outage gap (zero LP), 2026-10-03

- **Lane:** closeout-SPP-2, branch `claude/closeout-spp-2`. Closeout plan §3.4 rows 1b and 1c.
- **PRECOMMIT:** `docs/records/spp/PRECOMMIT-spp-109-subfiveday-gas-outage-2026-10-03.md`, pushed at 723f79ee before any
  number below existed.
- **Keeper:** `2026-10-02-w0-spp107r` (`results/calibration/w0_sppr_span`).
- **Probes:** `scripts/probes/_spp109_subfiveday_gas_phase0.py` (R1–R6, B1, Z1, Z2) and `scripts/probes/_spp109_robustness.py`
  (reported, not gating).
- **Numbers:** `results/phase0/spp/_spp109_subfiveday_gas_phase0.json` and `_spp109_robustness.json`.
- **No LP, no shard, no `src/` edit, no `ScenarioConfig` field.**

## 0. Verdict

**The arm fails at zero LP. No shards were launched.**

- Bar B1 passes by a wide margin.
- Two pre-fixed kills fire:
  - **Z1:** the rule-14 gap to SPP's published gas outage worsens;
  - **Z2:** the family's daily MW is negatively correlated with SPP's own outage record.
- **SPP-105's objection is now measured, and only partly upheld:**
  - On **ST_GAS**, the measured sub-5-day family recovers **0.24 / 0.27 / 0.35 GW** (2023 / 24 / 25). R-29 removed
    **0.65 / 0.73 / 0.71 GW** of statistical WEFOR, so the family recovers 37–49 % of it.
  - On **CC_REGULAR**, the family is **0.88–1.57 GW**, which is **4–7× the statistical WEFOR** it would replace
    (0.18–0.23 GW). It is 30–40 % of all CC CAMPD dead time and anti-correlates with SPP's outage record within the
    month. That is cycling conduct, not outage. This is the failure mode SPP-32 §7 pre-registered and its solve hit
    (slack at VOLL).
- The family has no per-class scope, so the CC economics come with any ST recovery.
- **Cell `unit_outage_short_windows_gas` stays R, with new SPP-own evidence.**

## 1. Companion artifact (Z3: PASS)

- **Built with:** `build_campd_split_remap_companions.py --iso SPP --family shortgas`, 4 min 18 s. It wrote
  `data/raw/campd-unit-outages-shortgas-splitremap-SPP.csv` (6,422 rows; incumbent 6,909).
- **Non-remap rows:** all 6,177 are byte-identical to the incumbent.
- **Remap delta (the SPP-98 identity):**
  - Ponca 762 units 3 / 4: 219 ST_GAS rows out, 58 Ponca City 7546 CC_REGULAR rows in.
  - Arsenal Hill 1416 CTG-6A / 6B: 16 ST_GAS rows out, 30 J Lamar Stall 56565 CC_REGULAR rows in.
  - Anadarko 3006 units 7 / 8: 497 → 157 rows. The plant is CC_REGULAR; the units move to WFEC GenCo 55655, a CT
    plant outside the short groups.
- The file is committed. Any future SPP gas short-window arm needs it: the keeper arms `campd_split_remap_companions`,
  and without the companion the loader raises.

## 2. Readings

### R1. Extract grain: unit capacity × window hours, GWh

`S` is the merit-order-guarded short family. `L` is the ≥ 5-day family the keeper reads. `lay` is the guard-rejected
economic layup set.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CC_REGULAR S / L | 11,029 / 25,104 | 13,460 / 22,428 | 18,494 / 27,394 | 16,963 / 25,379 | 13,172 / 19,173 | 10,600 / 23,939 | 12,322 / 24,955 |
| CC_REGULAR sub-5-day share | 0.305 | 0.375 | 0.403 | 0.401 | 0.407 | 0.307 | 0.331 |
| ST_GAS S / L | 1,671 / 60,743 | 2,152 / 58,766 | 2,459 / 63,333 | 2,691 / 57,202 | 3,052 / 49,547 | 3,449 / 44,911 | 4,472 / 52,513 |
| ST_GAS sub-5-day share | 0.027 | 0.035 | 0.037 | 0.045 | 0.058 | 0.071 | 0.078 |
| ST_GAS guard-rejected layup | 4,461 | 3,498 | 3,925 | 4,524 | 3,782 | 3,748 | 4,607 |

- CC_CHP is 134–230 GWh and ST_CHP is 0.
- **ST_GAS** stops are dominated by the ≥ 5-day family: only 3–8 % of its measured dead time falls in sub-5-day stops.
  The guard rejects more ST_GAS short time as economic layup than it keeps.
- **CC_REGULAR** has 30–40 % of its dead time in sub-5-day stops. That is the signature of a cycling fleet: SPP CC
  ran at about 49 % CF.

### R2–R4. LP grain, annual-mean GW (fleet_only rebuilds, outage-type basis)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| R2: S_g, four classes (recovered) | 1.098 | 1.309 | 1.782 | 1.719 | **1.403** | **1.157** | **1.395** |
| B1 bar (0.5 × SPP-105 gap) | — | — | — | — | 0.395 | 0.420 | 0.405 |
| S_g, CC_REGULAR | 0.964 | 1.123 | 1.574 | 1.495 | 1.147 | 0.877 | 1.036 |
| S_g, ST_GAS | 0.120 | 0.175 | 0.201 | 0.210 | 0.244 | 0.270 | 0.349 |
| R3: CC/CHP WEFOR removed by the companion | 0.218 | 0.227 | 0.196 | 0.212 | 0.248 | 0.242 | 0.239 |
| R3: ST_GAS WEFOR removed at R-29 (K0 − K) | 0.531 | 0.542 | 0.468 | 0.530 | 0.648 | 0.728 | 0.711 |
| R4: net, arm − keeper | +0.880 | +1.082 | +1.586 | +1.508 | +1.156 | +0.914 | +1.155 |
| R4: net, upper tercile | +0.754 | +0.928 | +1.299 | +1.119 | +0.979 | +0.706 | +0.984 |
| R4: net, peak hour | 4.35 | 3.86 | 4.59 | 4.60 | 4.33 | 3.69 | 4.14 |

**B1 passes in every train year.** But the arm is not a replacement in magnitude:

- it removes 0.9–1.6 GW more gas capacity, net, than the keeper does;
- up to 4.6 GW in an hour;
- almost all of it on CC.

### R5. Rule 14: gas unavailability vs SPP's published Natural Gas outage, all hours, GW

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | pooled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| keeper − SPP (mean) | +0.49 | +1.18 | +2.02 | +3.51 | +1.06 | +0.20 | +2.21 | |
| keeper mean \|gap\| | 1.284 | 2.006 | 2.945 | 3.728 | 1.738 | 2.208 | 2.866 | **2.396** |
| arm mean \|gap\| | 1.848 | 2.678 | 4.205 | 5.140 | 2.634 | 2.641 | 3.729 | **3.268** |

- **Z1 KILL:** the pooled gap rises from 2.396 to 3.268 GW, and it is worse in every year.
- **Robustness (not gating).** On a basis without the SPP-107 MMU offer-side bands, the keeper is below SPP in 2024
  (−1.02 GW), and the arm moves the 2024 mean to −0.07. Even there, the hourly \|gap\| still rises (2.39 → 2.48),
  and pooled it rises from 2.058 to 2.629. The kill does not depend on the basis.

### R6. Identification: daily correlation of the short family's MW with SPP's published gas outage

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | pooled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| four classes, raw | −0.064 | +0.175 | −0.106 | −0.138 | −0.132 | −0.148 | −0.157 | **−0.135** |
| four classes, within month (robustness) | −0.244 | −0.048 | −0.152 | −0.176 | −0.130 | −0.071 | −0.216 | −0.147 |
| CC_REGULAR, within month | −0.27 | −0.08 | −0.17 | −0.17 | −0.16 | −0.15 | −0.23 | |
| ST_GAS, raw / within month | −0.04 / +0.08 | −0.00 / +0.07 | −0.32 / +0.04 | −0.21 / −0.07 | −0.31 / +0.05 | −0.19 / +0.16 | −0.22 / −0.04 | −0.19 raw |

- **Z2 KILL:** the pooled correlation is −0.135.
- **Caveat on the test.** SPP's published series is untyped and dominated by planned outages: 12–16 GW in Apr and
  Oct–Nov against 3–4 GW in Jul–Aug. A forced-outage family could anti-correlate with it seasonally. Two things
  separate the classes:
  - **De-seasonalised,** ST_GAS turns weakly positive (+0.04 to +0.16 in 5 of 7 years). CC_REGULAR stays negative in
    every year (−0.08 to −0.27).
  - **Monthly profile:** the family is flat across the year at 0.5–2.3 GW, even in July–August, when SPP's entire gas
    outage is 2.7–4.6 GW.
- **Reading:** the CC part is cycling conduct that the merit-order guard did not filter, and it carries most of the
  family's MW. The ST part has a weak outage-like signal.

## 3. What this says about SPP-105's objection

- **It holds in direction on ST_GAS.** The measured sub-5-day ST stops are real, at 0.12–0.35 GW. They are now
  unrepresented: the keeper carries neither the statistical term nor the family.
- **In magnitude it is under half** of what R-29 removed (37–49 % in the train years). The rest of the statistical
  ST_GAS WEFOR (about 0.4 GW) had no measured counterpart in either family. G1's X ≥ W reading (R-29 PRECOMMIT)
  already said that.
- **On CC it does not hold.** The CC statistical WEFOR (0.18–0.25 GW) is the smaller object. The CAMPD sub-5-day CC
  dead time (0.9–1.6 GW) is economics.
- **The only form this evidence would support is an ST-only gas short scope.** That needs a new field (the family has no
  per-class scope), its own PRECOMMIT and its own identification. The within-month ST signal is weak (≤ +0.16), and
  ST_GAS's measured short share is 3–8 %, so the expected price effect is small: the ST recovery is +0.24–0.35 GW
  against the 0.84 GW gap the R-29 solve opened in 2024. **Not recommended as the next lever. Listed for the owner.**

## 4. Row 1c: SPP-81b re-run on the new keeper (zero LP)

- **Method:** `scripts/probes/_spp81b_upper_tercile_marginal_unit.py`, which gains a `--bundle` argument, on
  `w0_sppr_span`, for 2019, 2020 and 2023–25 (output: `results/phase0/spp/_spp109_spp81b_rerun_w0_sppr.txt`).
- **Hour set:** SPP-80's, unchanged.
- **Comparison base:** the old figures are from the R-SPP keeper `rspp_span`. The diff therefore mixes every keeper
  change from SPP-85 to W0 + relief.

| upper tercile, ex-scarcity | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| RT gas-independent level shift at the 2019–20 base slope, $/MWh | +13.82 | +17.09 | +20.85 |
| (old keeper, SPP-81b) | +13.8 | +17.1 | +20.9 |
| RT MEC − keeper price, $/MWh (new) | 10.67 | 12.80 | 11.57 |
| (old keeper rspp_span) | 9.90 | 11.18 | 10.83 |
| keeper setter gas share | 79.8 % | 82.2 % | 87.8 % |
| keeper gas-setter offer HR | 9.99 | 10.04 | 9.39 |
| MEC above every running CAMPD gas unit's cost | 9.2 % | 14.3 % | 7.9 % |
| class-aware donor pool, merit re-clear shift | +0.05 | +0.14 | −0.20 |

- **The RT level shift is unchanged, by construction.** It is a property of SPP's real MEC against delivered gas, and
  the keeper does not enter it.
- **The keeper's gap to it widened** by +0.8 / +1.6 / +0.7 $/MWh. That is consistent with W0 + relief lowering train
  prices (C3a 2024 −8.2 → −11.2 %).
- **The gap is still uniform across setter classes** (leg E: ST_GAS 10.7 / 12.5 / 12.0, CT_PEAKER 10.7 / 12.4 / 9.9,
  CC 8.5 / 10.6 / 11.6, coal 13.1 / 15.0 / 14.9). That is a level signature, not a class defect.
- **Offer heat rates still track CAMPD** at the 0.93 channel for CC and CT (leg C, 0.92–0.94) and at 1.00 for ST_GAS.
  Part-load still goes the wrong way: incremental HR 8.0–8.2 against average 9.0–9.1.
- **No measured, forward-reproducible driver owns the level:**
  - the setter mix and its fuel track the real shift;
  - the class-aware pool is inert (±0.2);
  - timing is flat (HE17–21 share 29–30 %).
  - SPP-81b's leg G (the market's offer-stack position) reads SPP's portal offer files and was not re-run. It does not
    depend on the keeper except for the keeper-position column.
- **Rule 13: no lever is proposed.** SPP-81b's reading stands: "offered supply that does not set price". Its
  candidates (offline offers, 5-minute ramp or dispatch limits, distributed-reference pricing) are not measured
  forward inputs today.

## 5. Matrix

`docs/codebase-site/data/mechanism-matrix/SPP.js` is updated in this session:

- **`unit_outage_short_windows_gas`:** stays R, with the SPP-109 evidence prepended. The stale "UNTESTED here" seed
  sentence is now marked superseded by SPP-32's own solve.
- **`wefor_residual`:** stays K. SPP-105's open objection is measured: ST recovery 37–49 %, CC not upheld.

## 6. Rules

- **1:** nothing tuned.
- **13:** the CC family is not identified as outage (Z2).
- **14:** rule-14 gap measured (Z1).
- **19:** the arm was written as a replacement. It fails as one, because the measured object is 4–7× the statistical
  one on CC.
- **23:** the companion is a remap-identity splice, not a re-derivation.
- **28:** the cell was adjudicated before compute.
- **29:** zero LP first.
- **32:** no LP in this session.
