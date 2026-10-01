# PRECOMMIT — R-CAISO-6: 2019–21 firm-import rows + MIC Malin repair; C4 midday import shape; C3c 2024 (2026-09-27)

Written before any shard. The parent spends zero LP (rule 32(a)). Keeper: `2026-09-26-caiso-r5-pastoria-co2`
(bundle `rcaiso5_XE_span`, 2022–25, pin `93a38eac`), CALIBRATED; 2019–21 folded as
`2026-09-27-caiso-r5-xe-keeper` (`rcaiso5_XE_tp_2019_2021`, reported only, rule 30(c)).

## 0. Housekeeping

No open CAISO PRs. Remote CAISO branches: `claude/r-caiso-5-XE-2019/2020/2021` (R-CAISO-5 leg bundles, already
composed into `rcaiso5_XE_tp_2019_2021` on `main`). Nothing to salvage; the owner can delete them.

## 1. Object 1 — C4 midday import shape (zero LP). Verdict: no admissible lever; STOP.

**Corridor split.** The committed sidecars carry imports as one class. The PNW hub has no tied tranches (floored
firm block + economic midC), so its delivery is identified from the hub dual; DSW = aggregate − PNW.
Probe `scripts/probes/_rcaiso6_corridor_split.py` → `results/calibration/_rcaiso6/corridor_mid_eve.json`.

h8–16 mean, model − EIA-930 corridor net import (MW):

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| PNW (model / 930) | 1,335 / 449 | 447 / −1,019 | 775 / −502 | 814 / −332 |
| DSW net (model / 930) | 3,485 / 2,809 | 2,484 / 1,903 | 2,809 / 1,938 | 2,914 / 2,194 |
| **excess PNW / DSW** | **+886 / +676** | **+1,466 / +581** | **+1,277 / +871** | **+1,146 / +720** |

- Measured PNW is a net **exporter** at midday. The model cannot export there: the P1 export route is
  adjudicated R/G (`caiso_p1_export_sink_seam`, `caiso_corridor_export_path`, `caiso_node_export_constraint`).
  That is DO-NOT-REDO.
- The rest is economic: midC and the DSW clean-depth tranches clear because the model's midday λ sits above the
  raw hub print. That is a clearing-price effect, not a lever.
- Tranche-level reconstruction from duals was validated on the 2019 leg's committed dispatch (economic tranches:
  0 hours violating complementary slackness), but it cannot split the clean-depth tranches, which tie with the
  hub dual. Hence the corridor-level form above.

**One measured-input boundary defect was found and censused, not armed.** The firm-block shape
(`measured_firm_import_shape`) is the TWO-corridor total, applied to both per-hub blocks, while the level is
corridor-split. caiso-138 named this and clipped around it. A per-corridor shape arm (same statistic, zero
parameters) was built and censused at zero LP (`fleet_only`, keeper recipe):

| total firm floor, h8–16 (MW) | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| keeper | 1,758 | 665 | 1,286 | 1,277 |
| per-corridor arm | 1,690 | 763 | 1,414 | 1,267 |

The arm moves the midday floor by −68 / +98 / +128 / −10 MW against a +1.5 to +2.3 GW excess. It swaps weight
between corridors (DSW's own shape carries more midday weight than the total), and the envelope clip strips
0.1–1.4 TWh of PNW capability (2023 PNW peak weight 7.6: its median net import is ≈ 0 most of the year). Not a
C4 lever and not a clean structural gain; the code was reverted and no LP is spent on it.

## 2. Object 2 — 2019–21 firm-import rows + a MIC intake defect (zero-LP intake; 3 shards)

**MIC intake defect (found this session).** `curate_caiso_mic.py`'s row regex required an `_ITC/_ISL/_BG`
suffix. The 2018–2020 filings code Malin as a bare `MALIN500`, so the largest branch group was silently dropped:

| delivery year | committed total | filing Total row | Malin 500 |
|---|--:|--:|--:|
| 2019 | 12,154 | 15,208 | 3,054 |
| 2020 | 12,394 | 15,524 | 3,130 |
| 2018 | 11,724 | 14,852 | 3,008 (120 MW residual gap, not a keeper year) |

The fix makes the suffix optional. `--verify` over 2018–2025: only Malin changes; 2021–25 MATCH unchanged.

**Consequence.** The keeper recipe arms `capacity_deliverability_limits`, so the 2019/2020 fold legs solved with
a seam-import cap of 12,154 / 12,394 MW instead of 15,208 / 15,524 (recorded in the fold bundle's
`resolved_inputs.seam_import_cap`). 2021–25 are unaffected.

**Firm rows 2019–21.** Same zero-parameter construction as 2022 (DMM `Imports` RA row × MIC north share),
re-proved first: it reproduces 2022/23/24/25 to the MW.

| year | DMM table, `Imports` | north share | PNW / DSW (was static 1,566 / 1,805) |
|---|---|--:|---|
| 2019 | 10.1 (210 top-load h), 4,704 | 7,312 / 15,208 = 0.48080 | **2,262 / 2,442** |
| 2020 | 9.1 (210 top-load h), 4,699 | 7,401 / 15,524 = 0.47675 | **2,240 / 2,459** |
| 2021 | 9.4 (Alert+ h), 2,771 (MSS 336 excluded) | 7,451 / 15,820 = 0.47099 | **1,305 / 1,466** |

Declared misalignment (rule 14): the 2019/20 tables have no MSS split, so their `Imports` row probably includes
MSS (~300 MW, ~7 % high). The 210-hour window also differs from Alert+. The published row still beats the static
2025 block it replaces.

**LA Basin / San Diego-IV peak_load 2019–21** (the `caiso_per_year_import_caps` inputs; the flag was a no-op
there). Transcribed from each year's Final LCT report (2023 reproduced first: 19,537 / 4,768 ✓): LA Basin 19,266 /
19,261 / 18,930; SD-IV 4,412 / 4,613 / 4,523; plus 2019 SP26/NP26 26,995 / 20,082 (p24; the "no zonal table in
2019" note was wrong). Import caps: LA 11,150 / 11,897 / 12,803; SD 386 / 718 / 635 MW.
**2022 rows exist (18,929 / 4,580) and are NOT landed:** they would move the keeper's 2022 leg (SD cap 587 vs the
static 1,436). Routed to the owner.

## 3. G-DRIFT (rule 29(b)), zero LP

`scripts/probes/_rcaiso6_gdrift_identity.py` → `results/calibration/_rcaiso6/gdrift_input_identity.json`.
`fleet_only` rebuilds of both keeper bundles, all 7 years, three arms sharing one `data/`:

- **pin `93a38eac` → main `92479835`: all 14 LP-visible fleet arrays, `mc_base`, demand and topology
  byte-identical in all 7 years.** The changed "constants" are SOCO's gas-basis rows and set-ordering reprs; the
  arrays prove them inert. New fields (`neiso_winter_fuelsec_conduct_roster`, `nwpp_path76_alturas_link`,
  `unit_outage_coal_extract_basis_share`) are default-off and absent from the recipe.
- **main → working tree (this intake): 2022–25 byte-identical; 2019–21 move only `pmax` / `availability` /
  `min_gen`** (the firm blocks). The seam cap is resolved from the rebuilt clean partition: 15,208 / 15,524 /
  15,820 MW.

Form 4 is valid for 2022–25 (no keeper change). 2019–21 need re-solving.

## 4. Shards (rules 32, 34, 36)

One shard per year, at the SHA of this commit. Recipe: `scripts/replay_keeper.py
results/calibration/rcaiso5_XE_tp_2019_2021 --years <Y> --out-dir results/calibration/rcaiso6_O2_<Y>`, no
`--set`. The change is data and code only.

**Hard stops:** `run_config.json` `resolved_inputs.seam_import_cap.by_year.<Y>.cap_mw` = 15208 / 15524 / 15820;
the log line `firm import blocks shaped` present; the XE recipe flags as in R-CAISO-5.

**Pre-registered read (report only, rule 30(c): these years cannot certify or decertify):**
- G-IDENT: config equals the fold recipe except `git_sha`.
- G-LIVE: seam cap and firm levels as above.
- Direction stated before solving: 2019–20 carry +1.33 GW of firm import and +3.05 / +3.13 GW of seam cap, so
  CC_REGULAR should FALL; 2021 carries −0.60 GW of firm import, so CC_REGULAR should RISE. These are
  predictions, not gates.

## 5. Object 3 — C3c 2024 (report only)

2024 has 35 RT hours above $200; the model has 0 (max load-weighted price $180).

- **25 of 35 hours fall on 13–16 Jan 2024** (the cold / gas-price event). Model $145–183 against RT $203–571 and
  DA $137–254. The model sits at 70–85 % of RT and 75–95 % of DA, with CC fully loaded and CT_PEAKER nearly idle.
- **The other 10 are isolated RT spikes:** 22 Mar, 26 May, 22–23 Jul (RT $642 / $897 / $235 / $330), 6 Oct, and
  11 Dec. DA sat far below RT in 8 of 10 (e.g. 22 Jul h18: RT $897, DA $282, model $66). That is real-time
  scarcity the perfect-foresight LP cannot produce.
- No measured-input defect identified. The ledgered C3c caveat stands.

## 6. Routed, owner decision (not taken)

- 2022 LA Basin / SD-IV peak_load rows (would move the keeper's 2022 leg).
- `EIA930_GAS_FOLD_REFUTED` for CAISO (carried from R-CAISO-5 §6).
- Stale comments at `envelopes.py` ~l.614–622 and `calibration_verdict.py` ~l.2131 (carried).
