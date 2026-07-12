## 2026-07-12 — MISO-57: RDT S→N congestion lane executed — external-bus wheel bypass severed + published 92% derate/TCDC pricing; RDT flows and binding frequency now match measured; score flat-to-marginally-better; 2025 separation gap re-attributed to the Midwest supply-cost gradient (lane 1), not transmission

**Registered `2026-07-12-miso-57-rdt-congestion` + rule-20 twin (rubric v2.4:
NOT-YET, FAIL set {fuelmix, sysvol, price_mean, price_tail} — co2 now a
commercial-band CAVEAT on today's scoring basis for both miso-56 and miso-57).**
Bundle `results/calibration/miso57_rdt_congestion{,-ablation}`; miso-56 keeper
meta.json strict replay + exactly two structural transmission changes (FINDING
§10 pointer 1, the $9.31-vs-$0.19 RDT lane):

1. **`miso_south_seam_split`** — the shared `MISO_external` bus linked to all
   five border zones, so the LP wheeled South energy South→external→Midwest
   around the RDT for free (2025 diagnostic: 1,255 MW summer-mean bypass, 7.7
   TWh/yr, while the RDT S→N link carried 54 MW). The South seam
   (SOCO/TVA/AECI — electrically south of the RDT per the MISO/SPP JOA) now
   lands on its own `MISO_external_South` zone. Structural topology fix
   (rule 1); the bypass was silently compensating the mid-merit split
   (rule 14 discovered-bug pattern).
2. **`miso_rdt_tcdc`** — the static JOA contract caps (3,000 N→S / 2,500 S→N)
   become MISO's published operating representation: 92% default derate as the
   free tier ("MISO derates the RDT limit to 92 percent of the contract limit
   by default", 2024 SOM §III.B) + the published two-step TCDC ($40/MWh at the
   modeled limit, $500/MWh from 102%, hard bound at contract) as priced
   one-way tiers. Zero fitted scalars (`constants.MISO_RDT_*`; MISO-SPP JOA /
   FERC 20151013-5444; RTOP RSC deck 2023-10-03). The deliberately
   conservative choice is the 92% DEFAULT derate, not the 84%-of-contract
   binding-hour average the SOM measures (403/390 MW below contract 2023/24) —
   deeper operator derates are real but have no published hourly series
   (adjudicated this session: RT Data Broker RDT endpoint deprecated without
   archive; Data Exchange key-gated; da_pbc/rt_pbc carry the binding record +
   shadow prices but no limit MW).

**Mechanism verification (vs measured, not residual):** RDT S→N mean
1,139/1,035/322 MW (2023/24/25) vs measured 917/1,108 (2023/2024 SOM §IV.E/
II.E); binds at the derated 2,300 MW in 2,359/2,184 h (≈25% of hours) vs the
IMM's "more than one quarter of RT intervals" (2024); 2024 gains the model's
first DA >$200 tail hours (Aug-26 HE15/17/18, Midwest-wide with South
decoupled below — RDT congestion price formation). Same-basis score deltas vs
miso-56 all flat-to-better: C2-2025 gas −11.0→−10.1 / coal +8.8→+7.6; C3a-2024
DA-diag −3.3→−3.0 (2023 +0.1, 2025 −13.3 flat); C3c-2024 0→3 h; C1 rows within
±0.4 TWh (4 better / 3 worse); C5a −8.5/−8.5→−9.0/−8.8 (both in-band). Twin
near-identical (CT_PEAKER ≤+0.6 TWh, COAL_PRB ≤−0.29) — fit carried
economically. LOYO note: no parameter is fit to any year (published constants
only); per-year movements uniform.

**Decisive diagnostic for the remaining 2025 gap:** the model's 2025 RDT
direction is INVERTED vs measured — N→S-dominant (mean 1,350 MW N→S, 2,559 h
at the N→S derated cap) where the IMM measured a predominantly S→N summer with
$9.31/MWh separation; model Jun-Aug separation +$0.02. With the transmission
lane now structurally faithful, the 2025 residual (C3a −13.3%) is pinned on
the Midwest supply-cost gradient — the COAL_BIT/CC mid-merit split + import
under-run lane (lane 1), which this run's severed bypass now exposes at full
size instead of hiding behind a non-physical wheel. Next admissible increment
in THIS lane if ever needed: the RPE constraint (published $200/MWh demand
value holding post-contingency RDT headroom; IMM Summer-2025 RDT+RPE $41M,
unintended additive $700 spreads) — not built here (one mechanism per
phenomenon; the energy-lane evidence is now clean).

**Recommendation to owner:** miso-57 supersedes miso-56 on structural
grounding (a non-physical free bypass removed; the RDT priced as the real
market prices it) at a flat-to-marginally-better same-basis score — the same
promotion pattern as miso-55→56. Keeper stays miso-56 pending decision;
keepers.json untouched. Retention: miso-44-wefor-neutral (+ twin) displaced
(16th main, oldest first). New primary series secured for this lane's
validation (not yet intaken): `docs.misoenergy.org/marketreports/
YYYYMMDD_{da,rt}_pbc.csv` (2023–2025, no auth) — the RDT binding record
(direction-specific constraint names `RDT_SO_MW (South_North)` /
`RDT_MW_SO (North_South)`, 5-min RT / hourly DA timestamps, shadow prices,
live TCDC breakpoints confirming $40/$500 + RPE $200).
