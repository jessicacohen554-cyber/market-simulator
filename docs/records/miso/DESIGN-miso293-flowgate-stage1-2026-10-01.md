# DESIGN — miso-293: flowgate program Stage 1 (zero LP). Recommend KILL. The 2022 pair is a comparator-geography question, and the rubric already defines the fix.

```
LANE    : miso-293 (owner rulings "Generic network anyway" + "Continue chain", CHARTER-miso292 §9)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none
PROBES  : scripts/probes/_miso293_flowgate_ceiling.py      -> results/phase0/miso/_miso293_flowgate_ceiling.json
          scripts/probes/_miso293_zone_resolved_basis.py   -> results/phase0/miso/_miso293_zone_resolved_basis.json
CELLS   : internal_congestion_split stays O pending the owner's go/kill ruling (evidence appended)
```

## 1. Answer

| question | answer |
|---|---|
| Can any reduced network move the **scored** C3a 2022 number up? | **Not through congestion prices.** The scored model price is the demand-weighted mean over all MISO zones. The same weighting applied to the published hub congestion + losses is **−1.64 $/MWh** in 2022 (Indiana alone: +8.72). A perfect zonal network would *lower* the scored price. |
| Which representation can carry the hub-to-hub spreads? | Only **flowgates on zone injections (PTDF rows) on the existing zones**. miso-79's "88–99.7 % intra-LBA" is about where the monitored element sits; it rules out zone-boundary limits, not PTDF flowgates. |
| Can that representation be built on public data without fitting? | **Only in form.** HIFLD gives line topology and voltage, nothing electrical. Every reactance, rating and contingency is a convention (≥ 16 declared values), and the convention decides what binds. |
| What explains the 2022 pair instead? | The scorer compares a MISO-wide model average with **one hub (INDIANA)**, which in 2022 sat at the top of the West→East gradient. Rubric v2.4 already says the actual is "zone-resolved where a zonal archive exists"; only ERCOT implements it. On that basis 2022 C3a/C3b both PASS, and **C3a 2020 newly FAILS** (+11.6 %). |

**Recommendation: kill the flowgate program** (kill conditions 1–2 hold in substance, and the objective cannot be reached through the scored object). Put the basis question to the owner separately (§5).

## 2. What a network can add to the scored price (zero LP, hub components as a ceiling only)

Hub MCC + MLC, weighted the way the scorer weights the model (zone demand across zones, system demand over hours; 2022 Jan–Oct):

| year | Indiana hub (comparator) | zone-demand-weighted (what the model can gain) | of which MCC | Indiana − MINN MCC |
|---|---:|---:|---:|---:|
| **2022** | **+8.72** | **−1.64** | −1.42 | +19.45 |
| 2023 | +2.35 | −0.31 | −0.22 | +1.11 |
| 2024 | +2.28 | −0.73 | −0.61 | +1.63 |
| 2025 | +2.44 | −0.90 | −0.83 | +1.00 |

- Zone map: MINN→West, ILLINOIS→Illinois, INDIANA→Indiana, MICHIGAN→East, mean of ARKANSAS/LOUISIANA/MS/TEXAS→South, mean of MINN/ILLINOIS→Plains (the staging's own proxy).
- Why it nets near zero: MISO prices energy at a load-weighted reference, so congestion components roughly cancel on load weights. The West sink (−18.29) offsets the East premium.
- **Additive reading:** C3a 2022 would go from −18.5 % to about −20.7 %. The charter's §1 estimate (≈ −10 %) added Indiana's own congestion to the model, which is not what the scorer weights.
- **What this does not bound:** redispatch around a binding flowgate raises the system energy price, and no public series measures that. Only a solve would. miso-291 puts the 2022 model − MEC energy gap at −4.02, mostly the closed coal line.

Rank of hourly hub MCC (8 hubs): first component 0.52 / 0.60 / 0.70 / 0.60 of squared norm (2022–25). In 2022–24 it is the North–South (RDT) direction, which the keeper already carries (`rdt_tcdc` K). The West–East step is the second component.

## 3. Candidate representations

| candidate | expresses West–East hub spread? | topology | limit | distribution factor | DOF | verdict |
|---|---|---|---|---|---:|---|
| A. Real limits on links L1–L6 | partly, but boundary mass ≤ 3.8 % (miso-79) | — | none at our grain (`measured_interface_limits` R) | n/a | 6 | **dead** |
| B. PTDF flowgates on the 6 existing zones | **yes** (one hub per zone) | HIFLD lines | voltage-class convention | DC reduction of HIFLD with per-km reactance convention | ≥ 16 | **form only** (§4) |
| C. Hub-bus split of Indiana | no effect on the scored system average | HIFLD | as B | as B | B + load split | **dead** |
| D. Flowgates on ~12 sub-zones | same as B | as B | as B | as B | B + split | **dominated by B** |

## 4. Kill conditions 1–2 on public data (candidate B)

HIFLD Electric Power Transmission Lines, checked live this session (ArcGIS feature service, reachable):

| fact | value |
|---|---|
| lines (US) | 52,244 |
| fields | VOLTAGE, VOLT_CLASS, SUB_1, SUB_2, OWNER, length, INFERRED, STATUS |
| reactance, rating, conductor | **none** |
| transformers | **none** (lines only). miso-79: 99.4 % of the West ToCA-`*` rows are transformers |
| attributes inferred | 34,035 (65 %) |
| endpoint missing (SUB = NOT AVAILABLE) | 2,126 |
| vintage | one (last edit 2023-09); no 2019–2022 state |
| contingency set | none (MISO's `bc_HIST` records a contingency on each binding constraint) |

What a buildable B needs, every item a declared convention, counted at full value (rule 20):

| item | source | count |
|---|---|---:|
| reactance per km, by voltage class (~7 classes) | textbook table | 7 |
| thermal rating, by voltage class | textbook / SIL multiple | 7 |
| flowgate set (which reduced branches are monitored) | choice | 1 |
| bus → zone assignment, load allocation to buses | rule (e.g. county population) | 1 |
| contingency treatment | none available → base case only | 1 |
| **total** | | **≥ 17** |

- Each convention is admissible **in form** under the owner ruling.
- In substance, the published conventions differ materially (thermal ampacity vs. SIL-based loadability; not quantified this session). That choice alone decides whether a reduced branch binds, so it acts as a free parameter on the outcome.
- The only check of where congestion lands is hub MCC. Iterating conventions against it would be fitting (rules 1, 13).
- Rule 17: driver real (thermal limits), window state-dependent, forward story weak (no forward ratings or outages on the public path).

**Reading:** conditions 1–2 are met only as a set of un-identified conventions, without contingencies or transformers, and the representation cannot raise the scored object (§2). That is the kill.

## 5. The basis question (owner decision, not a lever)

`derive_actual_lmp._lw_fields` builds a zone-resolved actual for ERCOT only. Every other ISO is scored against one system hub. MISO has a committed zonal archive (`actual_lmp_hourly_zonal_MISO.parquet`, 8 hubs → 5 zones). Below, the keeper is re-scored through `calibration_verdict` with the zone-resolved actual patched in memory (ERCOT's construction, mirrored; nothing written):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C3a, single hub (now) | +2.8 % | +6.6 % | −8.9 % | **−18.5 % F** | −0.3 % | −4.7 % | −8.3 % |
| C3a, zone-resolved | +8.7 % | **+11.6 % F** | −5.6 % | −5.1 % | +8.4 % | +5.1 % | −1.1 % |
| C3b, single hub (now) | 0.080 | 0.106 | **0.252 F** | **0.224 F** | 0.059 | 0.106 | 0.124 |
| C3b, zone-resolved | 0.114 | 0.165 | **0.201 F** | 0.122 | 0.104 | 0.101 | 0.083 |

(Plains dropped instead of proxied: same pass/fail pattern; C3a 2020 +10.2 % F.)

- Price failures go from {C3a 2022, C3b 2021, C3b 2022} to {**C3a 2020**, C3b 2021}. The full span stays **NOT-YET**, and C1 ST_GAS 2019 is unchanged. 2023–25 stay PASS, but C3a 2023 moves to +8.4 %, near the band edge.
- **Against interest:** the single hub had been flattering 2019/2020/2023/2024. On the zone basis the model's MISO-wide level runs +5 to +12 % high in low-congestion years.
- Rule 14 basis: the rubric's own v2.4 definition, applied to every year regardless of result. **The risk:** adopting it for MISO alone, in the session where it clears 2022, reads as basis-shopping. The clean route is a cross-ISO governance lane that measures every ISO with a zonal archive before anything is adopted.

## 6. PRECOMMIT (binding only if the owner overrides the kill and orders Stage 2)

1. Representation B only, on the six existing zones. A, C, D are not built.
2. Conventions frozen before any code: one published reactance table and one published rating table, each cited, with no alternative evaluated. HIFLD at the 2023-09 vintage for every year (rule 14 time-misalignment declared). Base case only, no contingencies. Load allocation by a declared population rule; generators at EIA-860 coordinates.
3. Flowgate set = the reduced branches whose base-case loading under the keeper's 2023 dispatch exceeds 100 % of the conventional rating. That is computed from model flows only, never from MCC.
4. Gate `ScenarioConfig.miso_public_flowgates` (default off), a matrix base row plus a cell in every ISO shard, rule-2 vectorised rows in `model/transmission.py`.
5. Screen: one shard per year 2019–2025 (rules 32–36), full bundle pushed, parent composes.
6. **Localization check (reported, single shot):** the sign of the model West−Indiana spread in hours where the measured spread exceeds $10. If it fails, the program stops. No second convention.
7. All ≥ 17 conventions in the DOF ledger. Rule 1: if the structure is kept, it is kept for being real, not for the fit.

Cost if ordered: 2 code sessions plus 7 shards (~20 min each), and a re-registration.

## 7. Where MISO stands

Keeper unchanged. Full span NOT-YET on C1 ST_GAS 2019, C3a 2022 (−18.5 %), C3b 2021 (0.252), C3b 2022 (0.224). Train 2023–25 CALIBRATED (C3c ledgered). No frontier.

## 8. Owner rulings (2026-10-01)

| card | ruling |
|---|---|
| Flowgates | **Kill.** `internal_congestion_split` O → **G**. This design is its record. Reopens only on RO-1 (MISO publishes shift factors or zone-aligned limits). §6 PRECOMMIT is void. |
| Basis | **Adopt the zone-resolved C3a/C3b actual for MISO now** (rubric v2.4 wording). Implemented by miso-294; expected result is §5's table, to be reproduced exactly. |
| Next lane | **C3b 2021** (fails on both bases). miso-294. |
