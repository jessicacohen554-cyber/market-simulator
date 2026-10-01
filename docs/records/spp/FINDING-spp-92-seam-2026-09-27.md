# FINDING — SPP-92: the keeper's North–South seam under-separates because of what the bubbles hold, not because the pipe is too wide. No admissible, material change.

**Lane** SPP-92 · **ZERO LP** · keeper `2026-09-26-spp-86-coal-extract` (bundle `spp86_arm_span`, basis_sha `d72e5f10`) ·
probes `scripts/probes/_spp92_seam_probe.py`, `_spp92_load_lmp_fetch.py`, `_spp92_bubble_spread.py`, `_spp92_psi_repair.py` ·
records `docs/records/spp/spp92/` (`_spp92_seam_probe.json`, `_spp92_bubble_spread.json`, `psi_repair.json`, `tstar_*.csv`,
`PREDECLARE-psi-repair.md` committed at `48711d25` **before** the ψ re-run was computed).
Nothing solved, registered or promoted. Keeper unchanged. No promotion question (rule 31).

## 0. Bottom line

| hypothesis | verdict | the measurement that decides it |
|---|---|---|
| (a) link rating too wide | **Not supported** | SPP-53's own construction, repaired to the model's object (bubble spread, correct clock), gives **4,100 MW — wider, not tighter**. All four construction cells sit inside SPP-53's stated width. SPP-58's independent DC-PTDF also pointed wider (11,022). |
| (b) bubble contents | **Main cause** | The actual price divide runs **West-cheap / East-dear inside both bubbles**. The within-North area range ($9–40/MWh) exceeds the bubble-to-bubble spread ($2–11) in every year. The keeper's hourly spread is essentially uncorrelated with the actual bubble spread (r 0.02–0.27). |
| (c) congestion inside the zones | **Real, secondary** | The Nebraska→Oklahoma **hub** spread overstates the **bubble** spread by 15–38 %. SPP-53's corridor elements (Franklin KS, Sibley MO, KC area, Cooper–St Joe) lie **inside** the North bubble, not on its KS/OK cut. |

- **No admissible, material change.** By the pre-declared rule, the ψ repair is not material. No measured input exists that REPLACES the seam (rule 19). A West/East re-partition would be a new topology, not a repair: it needs its own lane and an owner call (§6).
- **The 2019–22 validation failures are mostly not the seam** (§1). At most the North half of the 2021–22 coal-over / gas-under miss is seam-shaped.

## 1. Validation tier 2019–22: what fails, by how much (calibration_verdict.py, rubric v3.9)

| year | criterion (scorer key) | model | actual | miss | plausibly the seam? |
|---|---|---:|---:|---|---|
| 2019 | `price_mean` | 23.25 | 20.85 | +11.5 % (band ±10 %) | No. Model is high in both bubbles. |
| 2020 | `price_mean` | 19.43 | 16.52 | +17.6 % | No, same reason. |
| 2020 | `price_shape` | NRMSE 0.259 | — | band ≤ 0.20 | No. It is a level/shape miss. |
| 2021 | `fuelmix` COAL_PRB | 91.78 TWh | 80.35 | +11.43 TWh, +4.0 pp | **Partly** (see below) |
| 2021 | `fuelmix` CC_REGULAR | 25.03 | 34.57 | −9.54 TWh, −3.6 pp | **Partly** |
| 2021 | `dispatch_corr` gas | r 0.955, NRMSE 0.326 | — | band NRMSE ≤ 0.30 | Partly (gas volume) |
| 2022 | `fuelmix` COAL_PRB | 91.63 | 78.14 | +13.49 TWh, +4.3 pp | **Partly** |
| 2022 | `fuelmix` CC_REGULAR | 25.48 | 35.79 | −10.31 TWh, −3.8 pp | **Partly** |
| 2022 | `dispatch_corr` gas | r 0.962, NRMSE 0.365 | — | band NRMSE ≤ 0.30 | Partly |

- C3c reads CAVEAT in 2019–22 (rule 22 / v3.6); `co2` 2020 +13.7 % is reported-only.
- Train tier 2023–25 is unchanged: CALIBRATED with a lone ledgered C3c.

**How much of the 2021–22 miss could a seam carry?** The run payload's per-zone monthly volumes (`volErr.zoneMon`), in TWh, model − actual:

| year | North coal | North gas | South coal | South gas |
|---|---:|---:|---:|---:|
| 2019 | +4.2 | +0.9 | −3.3 | −3.1 |
| 2020 | −3.1 | +0.5 | −1.8 | −2.9 |
| 2021 | **+7.0** | +1.3 | **+2.6** | **−17.0** |
| 2022 | **+6.8** | −1.8 | **+6.5** | **−17.0** |
| 2023 | +4.0 | −0.9 | +0.0 | −4.7 |
| 2024 | +4.7 | −0.9 | −0.8 | −5.3 |
| 2025 | +7.6 | −0.6 | +4.6 | −11.7 |

- North fossil is over in 6 of 7 years and South fossil under in all 7. That is the signature of too much N→S energy.
- But in 2021–22 **South's own coal is over too** (+2.6 / +6.5 TWh), against South gas −17 TWh. That swap is inside one bubble, and no seam reaches it.
- A seam that trapped North coal perfectly could address about half of the 2022 PRB miss. It could not clear the band on its own.

## 2. The seam, measured (keeper duals vs actual prices, 2019–25)

The committed sidecars carry no link flow. Because the LP has one link, **|p_S − p_N| > $0.01 ⇔ the 3,400 MW link is at bound**, and the sign gives the direction (S dearer ⇒ N→S).

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| keeper at bound, h (N→S / S→N) | 480 / 31 | 257 / 176 | 2,213 / 2 | 2,786 / 23 | 875 / 183 | 823 / 298 | 1,721 / 79 |
| keeper mean S−N when bound N→S | 1.3 | 3.8 | 9.7 | 15.1 | 7.8 | 13.0 | 10.5 |
| keeper mean \|S−N\| | 0.08 | 0.16 | 2.47 | 4.84 | 0.84 | 1.42 | 2.25 |
| **actual bubble** mean \|S−N\| | 5.09 | 5.62 | 14.02 | 14.92 | 9.44 | 11.92 | 12.89 |
| actual **hub** mean \|S−N\| | 6.85 | 6.71 | 19.06 | 24.09 | 12.13 | 17.23 | 15.18 |
| actual bubble mean S−N | +2.30 | +2.61 | +11.02 | +10.79 | +2.76 | +6.43 | +6.56 |
| hours actual bubble S dearer ≥ $5 | 1,772 | 1,834 | 4,005 | 5,152 | 2,526 | 3,035 | 3,244 |
| hours keeper S dearer ≥ $5 | 12 | 24 | 1,071 | 2,114 | 277 | 314 | 755 |
| r(keeper S−N, actual bubble S−N), hourly | 0.13 | 0.05 | 0.02 | 0.27 | 0.10 | 0.08 | 0.05 |
| keeper − bubble, **South** mean ($/MWh) | −0.9 | −1.5 | −10.6 | −12.2 | −4.8 | −6.2 | −8.0 |
| keeper − bubble, **North** mean ($/MWh) | +1.4 | +1.1 | −2.0 | −6.1 | −2.8 | −0.8 | −3.3 |
| share of actual-S-dearer hours the keeper binds N→S | 0.14 | 0.11 | 0.36 | 0.42 | 0.20 | 0.17 | 0.32 |

Readings:

- **When the keeper binds, its direction is right.** In keeper N→S hours, the actual hub spread averages +$8 to +$26. What is missing is binding in the right hours, and the size of the spread.
- **The South price is the side that is short.** The keeper's South is $1–12 below the actual South bubble. Its North is within about $3, except in 2022.
- **SPP-91's "−28 vs −0" framing picked 2021 / 2022 / 2024.** In the ≥ $30 slice, the actual hub N−S spread is only −2.5 / −2.3 in 2023 / 2025. The seam gap is largest in the high-gas years.

**Bubble prices** come from RTBM monthly settlement-location LMPs at all 112 LOAD locations (`_spp92_load_lmp_fetch.py`, the SPP-91 route):
- each area price is the mean over its load locations;
- each bubble price weights areas by their annual EIA-930 sub-BA energy, over the keeper's own load partition;
- the clock is GMT HE − 7 h, verified against the committed hub series: r = 1.000, zero error in 5 of 7 years, r = 0.9996 in the two DST/leap years.

## 3. (a) Is the 3,400 MW rating too wide? The repaired construction says no

SPP-53 named its own misalignment (iii): ψ was fitted on the hub pair, not the bubble pair. It also read the RTBM `Interval` stamp on local time, which is 1 h off the CST model clock in DST months. The re-run changes only those two things (`_spp92_psi_repair.py`; the rule was pre-declared at `48711d25`). Otherwise it uses SPP-53's spec and L_f tables verbatim.

| cell | R² | identified N→S | TTC (weighted-median T*) | p25 / p75 |
|---|---:|---:|---:|---|
| SPP-53 as committed | 0.17 | 12 | 3,400 (3,355) | 3,355 / 6,437 |
| local clock, hub spread (my reproduction) | 0.37 | 16 | 2,600 | 2,618 / 6,951 |
| GMT clock, hub spread | 0.43 | 16 | 2,900 | 2,868 / 7,194 |
| **GMT clock, bubble spread (the repair)** | 0.32 | 11 | **4,100** | 4,043 / 4,101 |

- **Verdict by the pre-declared rule: 4,100 lies inside SPP-53's width [2,645, 11,121], so the repair is not material. No change, no solve.**
- The direction is itself informative. Once ψ is measured against the model's own object, the link gets **wider**, not tighter. This agrees with SPP-58's DC-PTDF (11,022 like-for-like). Nothing supports tightening the pipe, and rule 14 forbids moving it for the fit.
- **Two defects are recorded, not acted on.**
  1. **Reproducibility.** From the committed inputs, SPP-53's own cell reproduces as 2,600 MW at R² 0.37, not 3,355 at R² 0.17. The per-constituent ψ differ too, e.g. Smoky Hills–Summit TMP501 is −0.031 in SPP-53 vs +0.088 here. SPP-53's scratch H matrix is not committed, so the cause is not identifiable. Every cell still lands inside the stated width.
  2. **Fragility.** In every cell the weighted median is the **Franklin 161/69 kV transformer**: T* = 100 MW / ψ_Franklin, with 4,103 of the corridor's binding hours. The N↔S rating is one sub-transmission transformer's regression coefficient. SPP-58 R-23 already found it unresolvable from public line data.

## 4. (b) Bubble contents: the real divide is West / East

Annual mean RT LMP by sub-BA load area, $/MWh:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **North** range (min area – max area) | 17.7–27.0 | 13.8–23.8 | 29.7–53.3 | 28.8–68.3 | 15.2–30.4 | 12.6–30.4 | 17.9–38.0 |
| **South** range | 21.0–25.8 | 18.6–21.3 | 43.0–51.1 | 42.1–58.6 | 22.7–30.4 | 25.4–31.3 | 30.8–36.5 |
| bubble-to-bubble mean S−N | 2.3 | 2.6 | 11.0 | 10.8 | 2.8 | 6.4 | 6.6 |

- The cheapest North areas are the western wind areas (SECI, NPPD, LES, WAUE).
- The dearest North areas are the eastern load pockets: SPRM (Springfield, MO) and EDE (Joplin). In each of 2019–22 the dearer of the two exceeds every South area.
- In the South, SPS (Texas Panhandle, west) is the cheap area, and OKGE and CSWS (east) are dear.
- The N/S cut therefore puts a cheap-west + dear-east mix into **each** bubble. Averaging each mix dilutes the divide the two-zone seam can carry.
- This is the structural reason the keeper's zonal prices sit together 76–87 % of hours (SPP-64) at any plausible rating. It also fits the South-side price miss in §2: the keeper's South holds the Panhandle's untrapped wind and coal (SPP-57b/54 measured SPS as an overnight exporter).

## 5. (c) Congestion inside the zones

- The hub spread exceeds the bubble spread by 15–38 % of |S−N|: the bubble/hub ratio is 0.74 / 0.84 / 0.74 / 0.62 / 0.78 / 0.69 / 0.85 across 2019–25. That part is intra-bubble and no zonal seam carries it.
- In actual S-dearer hours, RTBM binding constraints were grouped with SPP-14's rules:
  - the Kansas-corridor group binds in 55–82 % of those hours, and Oklahoma-internal in 44–81 %;
  - in 17–45 % of them no corridor constraint binds at all;
  - the hourly correlations of the spread with each group's |shadow price| are weak (r ≤ 0.63, mostly < 0.2).
- The corridor elements SPP-53 rated the link from are Kansas/Missouri facilities, which sit **inside** the model's North bubble (North = KS, MO, NE, … by the state map). The model's cut is the KS/OK line. The element limits govern a Nebraska→Kansas-City transfer the two-bubble model does not represent.

## 6. Verdict and routing

- **No admissible, material change.** No PRECOMMIT, no G-DRIFT, no shard, no ScenarioConfig field.
  - (a): not supported, and the ψ repair is not material.
  - (b): the cause, but the only seam that fixes it is a **re-partition**, i.e. a new topology. That is a structural lane with its own screen, not a phase-0 repair.
  - (c): real, and out of reach of any zonal seam.
- **New evidence for `internal_congestion_split` (U).** Before any re-partition lane:
  - the West/East divide inside both bubbles is measured here for 2019–25;
  - SPP-57's Oklahoma pocket, killed, was a South-internal cut that left the North's east/west mix in place;
  - SPP-54's SPS pocket, designed but not landed, is the South half of a West/East split.
  - **Opening a West/East re-partition lane is an owner decision** (asked as a decision card, not decided here).
- The multipliers were not touched (rule 1(c)). Nothing was selected on the residual (rule 1). The TTC was not moved (rule 14).

## 7. Status against `complete` / `frontier`

- `complete` is already declared for SPP; the train tier 2023–25 is CALIBRATED with a lone ledgered C3c.
- **`frontier` is NOT reached.** Validation tier 2019–22 reads NOT-YET (reported, not gating, rule 30(c)), with the failures in §1. Most SPP matrix cells are still untested (SPP-31 §1).
