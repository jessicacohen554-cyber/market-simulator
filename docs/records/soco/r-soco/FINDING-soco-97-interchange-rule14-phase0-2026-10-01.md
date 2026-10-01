# FINDING soco-97 — SOCO-56 priced interchange: rule-14 transfer-limit reconciliation, phase 0 (zero LP)

**Scope.** Zero LP. No solve, no code or config edit, no registration, so no matrix cell moves. Keeper unchanged:
`2026-09-30-soco96-measured-oil-burn` (`results/calibration/soco96_span`), NOT-YET (ledgered C1, C3a, C3b, budget 3/1).
Owner question (d): is SOCO-56 buildable as a structural lane, starting from the rule-14 limit reconciliation?

## Verdict

**The reconciliation is done, and it removes 70–88 % of the refused throughput (81–88 % in 2023–25) with zero free parameters. The price reference
is now available for free for 6 of 8 seams. Even so, a spread-cleared priced seam is the wrong structure for SOCO
(rule 1), and it has no selective reach on any open row. Do not arm it. Two zero-DOF data steps are worth landing.**

1. **Limits.** The published Avg TC is an *import-direction*, *economy (non-PPA)* capability *per simulation region*.
   It was being applied as a symmetric per-tie thermal bound. Matching direction and aggregating the regions cuts the
   refused throughput from 10.66 / 12.81 / 14.21 TWh to 1.99 / 1.97 / 1.64 TWh (2023–25). What is left is all TVA.
2. **Price.** FERC-714 Sch. 6 lambdas for TVA, DEC, DEP, Santee Cooper, DEF, TAL, JEA and MISO were fetched free from
   the same Zenodo archive soco-83 used. They cover Elliott at full hourly grain. Dominion SC (SCEG, the largest export
   seam) files **zeros** in every hour. FPL's lambda runs ~40 % below SOCO's (17.3 vs 25.7 $/MWh in 2019), a basis
   question that is not resolved here.
3. **Structure.** Measured flows do not follow lambda spreads: correlation r is between −0.44 and +0.40 on every seam
   and year. SOCO's λ sits *above* TVA's and DEC's in every year, yet SOCO is a net **exporter** of 4–13 TWh. The book
   is dominated by firm, contract, JOU and loop flow. A seam that clears on spread would reverse SOCO's measured
   net-export direction.
4. **Reach.** The price pull-down is not selective. It hits 2021–25 at least as hard as the over-priced 2019/20. In
   Elliott, every neighbour's λ is above the model price in 78–81 of 96 h, so the seam would *export*. That adds
   quantity through a mechanism the meter contradicts, since SOCO actually imported −156 MW mean (rule 1).

## 1. The mismatch

**Model inputs.** `model/interchange/spec.py` `INTERFACE_NEIGHBORS["SOCO"]` contains eight default-off blocks. Their
`interface_limit_mw` values are the 2024 Reserve Margin Study's **Winter Avg TC** (Table I.2), transcribed by SOCO-12
in `data/raw/soco-planning/README.md` §4c. The study defines this as the *"Average Transfer Capability into Southern
Company System"*, calibrated to *"eight-year average, non-PPA market transactions"*, with a separate CBM.

**What the keeper does now.** The keeper does not use these blocks. It serves the measured EIA-930 `Total interchange`
as a **fixed hourly quantity** (`soco_net_interchange`, card S4): `reference_price_interface=False`, and no import node.

**Measured flows.** Source: `eia-930-interchange/SOCO interchange hourly.parquet`, 2019–2025. Sign convention: + = SOCO
exports. Per-year rows are in the scratch CSV; the envelope over 2019–25 is below.

| DIBA | Winter / summer Avg TC (MW) | p50 \|f\| | p99 \|f\| | max export | max import | net TWh/yr (range) | % h exporting | max\|f\| / winter TC | max import / winter TC |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| TVA | 478 / 480 | 574 | 1,874 | 3,007 | 3,150 | −2.9 … −6.5 | 10–28 | **6.6** | **6.6** |
| MISO | 2,374 / 1,791 | 485 | 1,247 | 1,780 | 800 | +3.3 … +4.8 | 86–99 | 0.75 | 0.34 |
| DUK | 407 / 34 | 464 | 1,405 | 863 | 2,219 | −3.6 … −5.3 | 1–12 | 5.5 | 5.5 |
| SCEG | 126 / 59 | 673 | 1,490 | 2,123 | 140 | +3.8 … +9.8 | ~100 | **16.9** | 1.1 |
| SC | 533 / 280 | 465 | 1,021 | 1,242 | 569 | +3.4 … +4.8 | 96–100 | 2.3 | 1.1 |
| FPL (incl. FPLNW) | 1,317 / 642 | 340 | 1,725 | 2,843 | 1,575 | +1.7 … +4.1 | 64–86 | 2.2 | 1.2 |
| FPC | 50 / 31 | 77 | 369 | 692 | 354 | −0.4 … +1.4 | 25–97 | 13.8 | 7.1 |
| TAL | 20 / 12 | 81 | 191 | 294 | 91 | +0.6 … +0.8 | 89–99 | 14.7 (24.5 summer) | 4.6 |
| SEPA (not a priced seam) | — | 231 | 660 | 217 | 984 | −1.9 … −2.7 | 0–3 | — | — |
| AEC (to 2021-09) | — | 81 | 371 | 496 | 526 | ~0 | — | — | — |

**Reproducing the "3–25×" figure.** It is max|flow| divided by Avg TC across seams. The range runs from about 2× (SC,
FPL), through 6.6× (TVA) and 16.9× winter (SCEG), to 24.5× (TAL against its 12 MW summer TC). soco-33's refused
throughput also reproduces exactly: **10.66 / 12.81 / 14.21 TWh = 35.6 / 39.0 / 41.7 %** of gross for 2023–25. It is
8.35 / 7.86 / 9.85 / 12.04 TWh for 2019–22.

**Elliott**, 2022-12-23..26 CST, 96 h. Columns are mean / min / max MW.

| TVA | MISO | DUK | SCEG | SC | FPL | FPC | TAL | SEPA | **Total** |
|---|---|---|---|---|---|---|---|---|---|
| −1,303 / −2,244 / +779 | +37 / −441 / +733 | −441 / −1,770 / +352 | +945 / 315 / 1,319 | +740 / 276 / 1,103 | +83 / −1,039 / +724 | −94 | +135 | −259 | **−156 / −1,650 / +1,395** |

In the top 24 λ hours (mean $746), net was −378 MW, with TVA −1,403 and DUK −453. SOCO kept exporting about 1.4 GW
into the Carolinas corridor the whole time. The largest SOCO net import, 1,650 MW, is about 20 % of the ~8 GW Elliott
quantity gap.

## 2. Root cause under rule 14's misalignment exception

| Candidate | Finding | Seams affected |
|---|---|---|
| **Direction (sign)** | Avg TC is an *into-SOCO* figure, and the study publishes no export capability. SCEG, SC, TAL, MISO and FPL export in 64–100 % of hours. Matched to the import direction, they read 0.34–1.2× (TAL 4.6×). | SCEG, SC, TAL, MISO, FPL: **mostly resolved** |
| **Boundary (region vs tie)** | The study's "Simulation Regions" are areas modelled with transport flows (SERVM), not tie lines. Power to the Duke region wheels physically through SCEG and SC. Aggregated by corridor and matched to import, Carolinas (407+126+533 = 1,066) reads 1.0–2.7× max but refuses ≤0.03 TWh/yr, and Florida (1,317+50+20 = 1,387) reads 0.64–1.07×. | DUK, SCEG, SC, FPL, FPC, TAL: **resolved** |
| **Boundary (BA membership)** | Gulf Power → FPL BA on 2022-07-13. The FPL tie's mean moves −94 → +559 MW across that date, because former internal Gulf supply becomes interchange. The 2024 study's FPLNW 1,164 MW applies only *after* the exit, so pre-exit years need FPL 153 alone. AEC/PowerSouth enters the BA 2021-09, when the AEC leg ends. Both are already handled for demand (`ISO_BA_EXITS`, the AEC entry). MEAG/OPC/Dalton are "Unlimited" (inside the BA), so the Vogtle/Scherer co-owner shares are internal, not seams. | FPL: a **date-gated limit** is needed |
| **Limit type** | Avg TC is the *average economy* capability, net of firm reservations and CBM (TVA CBM 250). EIA-930 ID is *metered* flow, which includes firm PPAs, JOU dynamic schedules and parallel (loop) flow. §3 shows the flows are not spread-driven. | **TVA: unresolved.** Import up to 3,150 vs 478 MW; refuses 0.93–3.66 TWh/yr |
| **Units** | All values are MW, both sides. No issue. | — |

**Refused throughput** (TWh) under each reading:

| Year | A: symmetric per seam (registered) | B: import-only per seam | C: import-only per corridor | of C, TVA | Corridor-hours over |
|---|---:|---:|---:|---:|---:|
| 2019 | 8.35 | 3.34 | 2.03 | 2.01 | 5,304 |
| 2020 | 7.86 | 3.15 | 0.94 | 0.93 | 3,345 |
| 2021 | 9.85 | 3.91 | 2.30 | 2.27 | 5,048 |
| 2022 | 12.04 | 5.36 | 3.66 | 3.66 | 5,848 |
| 2023 | 10.66 | 3.15 | 1.99 | 1.99 | 4,254 |
| 2024 | 12.81 | 3.34 | 1.97 | 1.97 | 4,655 |
| 2025 | 14.21 | 3.76 | 1.64 | 1.63 | 3,795 |

**A reconciled limit from real data, and its DOF cost:**

- **Corridor, import side.** Use the region Avg TC summed per corridor (TVA, MISO-South, Carolinas, Florida), with FPLNW
  dated to 2022-07-13. This has **zero free parameters** and is the published number on its own definition. It bounds
  only the *economy* increment, never the metered total.
- **Export side.** No published value exists. Options: the measured directed-flow envelope (the MISO
  `miso_seam_flow_percentile` precedent) adds **1 DOF** (the percentile, p90 registered for MISO, not transferable
  under rule 25). The measured maximum (p100) has no DOF but is a measured outcome, so it is outlier-sensitive and close
  to pinning (rule 13).
- **TVA.** No public TTC was reachable. The SOCO OASIS (`oasis.oati.com/SOCO`) fails with an upstream TLS-chain error
  through the proxy, and historical TTC postings are unverified in any case. The NERC/SERC audits and the SEEM report
  carry no path rating (SOCO-12 §4b). Without the firm/economy split, the TVA residual stays open.

## 3. Price reference

**Fetch test.** Zenodo record 21738524 (PUDL raw FERC-714) returned HTTP 200. The sha256 of `ferc714.zip` and
`ferc714-xbrl-2022.zip` matches the ferc-714 README; 2021, 2023, 2024 and 2025 were also fetched. `www.ferc.gov`
returns 403 and the PUDL S3 returns 200. **The cost is zero, so this is within "Don't buy".** The parser reproduces
SOCO's committed lambda means for every year. The CSV era's CPT clock was read prevailing, versus fixed CST in the
committed file, so individual hours can differ by up to ±1 h (max|Δ| $31.6).

Hourly coverage is 8,753–8,784 non-NaN hours per year. Mean $/MWh by year:

| Year | SOCO | TVA | DEC | DEP | SC (Santee) | DEF (FPC) | FPL | TAL | JEA | MISO | DESC (SCEG) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 25.72 | 22.12 | 25.30 | 24.89 | 31.08 | 21.46 | 17.31 | 14.56 | 22.89 | — (CSV era) | not filed |
| 2020 | 20.90 | 16.80 | 17.22 | 16.05 | 24.40 | 16.32 | 13.68 | 11.76 | 19.54 | — | 0 every hour |
| 2021 | 37.64 | 32.76 | 34.08 | 30.67 | 34.05 | 31.58 | 17.29 | 23.34 | 32.08 | 36.51 | 0 |
| 2022 | 74.26 | 62.94 | 77.56 | 69.46 | 70.71 | 60.47 | 38.37 | 44.47 | 60.12 | 62.10 | 0 |
| 2023 | 29.35 | 22.13 | 24.68 | 22.47 | 36.93 | 22.00 | 15.40 | 19.28 | 24.05 | 29.33 | 0 |
| 2024 | 27.97 | 23.31 | 24.44 | 21.55 | 37.82 | 21.21 | 14.34 | 16.83 | 23.49 | 28.47 | 0 |
| 2025 | 38.10 | 33.86 | 38.81 | 35.72 | 37.16 | 30.58 | 20.99 | 25.29 | 30.78 | 40.40 | 0 |
| Elliott mean / max | 384.7 / 1,657 | 526.3 / 3,300 | 393.9 / 990 | 271.8 / 624 | 351.3 / 910 | 54.0 / 104 | 39.5 / 50 | 54.1 / 64 | 74.3 / 141 | 238.5 / 2,168 | 0 |

This closes soco-96's blockers (1) and (2): there is now a neighbour price inside Elliott, and TVA/Duke/FPL lambdas
are on disk-reachable for free. The exceptions are SCEG (no usable lambda) and FPL (suspect basis). **Not intaken
here**; that is a data lane.

**Do flows follow spreads?** No. Spread is λ_nbr − λ_SOCO; flow is + export.

| Seam | r (by year) | Sign agreement % | Exports while the neighbour is cheaper by >$2, TWh/yr |
|---|---|---|---|
| TVA | 0.02–0.29 | 58–77 | 0.04–0.90 |
| DUK (DEC) | 0.17–0.40 | 50–81 | ≤0.05 |
| SC | −0.12–0.12 | 34–82 | 0.38–2.50 |
| FPL | −0.17–0.09 | 16–37 | **2.3–3.9** |
| FPC (DEF) | −0.10–0.18 | 18–71 | 0.06–1.00 |
| TAL | **−0.44 … −0.32** | 3–19 | 0.47–0.80 |
| MISO (2021+) | −0.06–0.03 | 33–43 | **2.3–2.8** |

**soco-energy-auction.** This is Southern's *own* sell-side hour-ahead clearing price, not the neighbour's side of the
seam, and it cleared only 4 Elliott hours ($117–439). **The EQR store** (2023–25 only) carries LT-firm sales from
Southern to TVA (11.1 TWh over 3 yr) and to Santee Cooper (4.2 TWh), consistent with a firm-dominated book. But its LT
rows have quantity defects (Black Warrior EMC 102 TWh in 2025), so it cannot carry an hourly firm/economy split.

**Rule 13.** Fed hourly as the seam price, a neighbour's λ is a measured **outcome** of the neighbour's dispatch. In a
forecast it would itself have to be modelled, so it fails the forward-regenerability test. The NYISO NE-AC node used it
under an explicit "backcast-only, forward anchor not wired" label, but that is a diagnostic posture, not a keeper
input. The admissible use is the established one: a **per-year `hr_by_year` anchor** for the
`(HH + basis) × HR × load-shape` reference-price construction, which regenerates from forward gas. That would extend
SOCO-33's one anchorable seam (MISO) to six: TVA, DUK, SC, FPC, TAL and JEA. FPL is pending its basis check; SCEG
cannot be anchored.

## 4. Reach on the open rows (zero-LP bounds)

**Keeper prices.** Demand-weighted P1 price over the committed `hourly/system_<y>.parquet`, against the FERC-714 λ,
reproduces C3a to within ~0.7 pts: +14.3 / +14.5 / −2.4 / **−12.0** / +2.6 / −3.0 / −1.1 % for 2019–25.

The table gives an upper bound for an unconstrained economy seam: the model price is clamped to the neighbour's λ +
$2 hurdle wherever it sits above it. Values are C3a %.

| Year | Keeper | Clamp to TVA+2 | Clamp to min(TVA, DEC, SC[, MISO])+2 |
|---|---:|---:|---:|
| 2019 | **+14.3** | −8.9 | −12.9 |
| 2020 | **+14.5** | −12.3 | −20.6 |
| 2021 | −2.4 | −15.3 | −26.7 |
| 2022 | **−12.0** | −25.7 | −35.2 |
| 2023 | +2.6 | −20.4 | −27.0 |
| 2024 | −3.0 | −17.9 | −27.7 |
| 2025 | −1.1 | −15.5 | — |

- **2019/20 over-pricing is not selective.** The mean SOCO − TVA λ gap is +3.6 / +4.1 $ in 2019/20, *smaller* than
  +4.9 / +11.3 / +7.2 / +4.7 / +4.2 in 2021–25. Any import pull strong enough to close +14 % pushes the five passing
  or near-passing years negative and deepens 2022. The real bound, with limits ≤ Σ corridor Avg TC of about 5.3 GW,
  is a fraction of these numbers but has the same sign pattern.
- **Elliott.** The keeper already serves the measured schedule (mean −156 MW). The model price (soco-95: $86.7 mean)
  is below TVA's λ in 78 of 96 h and below DEC's in 81 of 96 h, so a priced seam *exports*. Up to ~5.3 GW of extra
  load could raise the model price toward λ, but by the wrong mechanism: SOCO actually imported, and TVA and Duke shed
  firm load on Dec 24. That reaches the number through a mechanism that is not real (rule 1). The ~8 GW quantity gap
  is SOCO's own supply side, not the seam.
- **C3b 2022 and C1 2019 COAL_BIT.** No pathway beyond the above. C1 would move only through import-displaced coal,
  and that has the same non-selectivity.

## 5. Verdict and minimum plan

**A structural priced-interchange lane is not buildable as a calibration lever now.** The blocker is no longer data. It
is structure: SOCO's metered interchange is contract-dominated and spread-insensitive (§3), and no public hourly
firm/economy decomposition exists to separate the economy increment that a priced seam represents (rule 19: pricing
the whole metered book double-counts the firm schedules that are already served).

The structurally faithful form is **served measured schedule (firm, card S4) + a priced economy band ± corridor Avg
TC**. That carries 0 DOF on the import side and 1 DOF on the export side (or none at p100). It would still be
non-selective (§4), and in backcast it double-counts the realized economy trades already inside the schedule, by up to
Σ Avg TC. Its reach on the open rows is wrong-signed in 2021–25 and wrong-mechanism in Elliott.

**Zero-DOF steps worth landing, as data and spec only (no arming):**

1. **Data intake.** Add the FERC-714 Sch. 6 neighbour lambdas (TVA 263, DEC 157, DEP 233, DEF 234, FPL 171, SC 251,
   TAL 140, JEA 186; MISO from XBRL) to `data/raw/ferc-714/`, REPORTED-ONLY, using the same Zenodo archive and an
   extended `fetch_ferc714_system_lambda.py`. Flag DESC (zeros) and FPL (basis).
2. **Spec re-registration (inert).** Restate the SOCO block limits as corridor import-direction Avg TC with FPLNW
   dated 2022-07-13. Label the export side "unpublished". Record TVA as an open limit-type misalignment.
3. **Anchors.** Derive `hr_by_year` for the six λ-anchorable seams. This needs the `NEIGHBOR_LMP_ANCHORS` SOCO entry
   (SOCO-33 R-2) and the `derive_neighbor_hr_elasticity` name-map fix (R-1). It is a forecast-lane input, not a
   backcast lever.

**Matrix.** SOCO-56 stays `U`, because no arm was solved. The recommended cell note is "phase 0: structurally
non-selective; contract-dominated book; do not arm".

*Method:* the scratch probes (not committed) are `s1.py` (seam stats), `f714p.py` and `panel.py` (λ fetch and parse),
`spread.py`, `el.py` and `reach.py`. They read only `data/raw/eia-930-interchange`, `data/raw/ferc-714`, the Zenodo
zips and `results/calibration/soco96_span/hourly/system_<y>.parquet`.
