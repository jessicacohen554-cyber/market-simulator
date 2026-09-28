# FINDING — NYISO-NEXT-10: neighbour-price intake + per-seam spread identification (ZERO LP, ZERO SHARDS)

- **Question.** With each neighbour's own price in hand (NEXT-7 §3(c)), does each NYISO seam's
  hourly flow follow its **own spread**, so a per-neighbour seam construction is identifiable at
  zero DOF?
- **Verdict: STOP, under the ex-ante rule.** 4 of 8 seam groups are spread-identified (IESO,
  PJM_HTP, NE_AC, NE_1385). 4 are not (PJM_AC, PJM_VFT, PJM_NEPTUNE, NE_CSC). The rule required
  NE_AC **and** the downstate DC groups carrying the NYC/LI excess; VFT, Neptune and CSC fail.
  No PRECOMMIT for a solve, no shard, no keeper change.
- **Rule.** `docs/PRECOMMIT-nyiso-next10-seam-spread-phase0-2026-09-28.md`, committed at
  `c635751a` before any spread statistic was computed.
- **Probe.** `scripts/probes/nyisonext10_seam_spread_phase0.py` →
  `results/calibration/_nyisonext10_phase0.json`. Reads raw inputs only.

## 1. Intake (`seam-neighbour-price`, new clean datatype)

| publisher | nodes | markets | coverage | committed |
|---|---|---|---|---|
| NYISO MIS | 11 zones + 12 proxy buses (`O H`, `H Q`, `PJM`, `NPX`, HQ/PJM/NPX gen proxies) | DA | 2021–2025, every hour, 23 points | yes (12 MB gz) |
| PJM DataMiner2 | `NYIS`, `HUDSONTP`, `LINDENVFT`, `NEPTUNE` | DA, RT | 2021–2025, every hour | **no** (licence §4; SHA256 only) |
| ISO-NE histRpts | Roseton 4011, Shoreham 4014, Northport 4017, hub 4000 | DA, RT | 2021–2025, 1,826/1,826 days | yes |
| IESO reports-public | HOEP; Ontario + New-York intertie MCP (hourly mean of 5-min) | RT | 2021-01-01 → **2025-04-30** | yes |
| Bank of Canada | FXUSDCAD daily | — | 2020-12 → 2025-12 | yes |

- **Data gap.** IESO May–Dec 2025 is not obtainable from any public source today: Market Renewal
  (2025-05-01) ended HOEP/MCP, and the successor XML archive rolls at ~90 days (oldest file
  2026-06-28). IESO 2025 statistics use Jan–Apr (2,880 h).
- **Two source defects handled.** PJM rejects a `pnode_id` filter on archived rows and any
  window straddling the archive boundary (HTTP 400); the fetcher pulls `type=INTERFACE` and falls
  back per day. PJM RT carries superseded versions (2022-02: 1,344 doubled hours, 286 with
  different prices); only `row_is_current` rows are kept.
- `fetch_neiso_smd_zonal_lmp.py` gained an optional `locations` / `stem` argument; defaults are
  unchanged and its tests pass.

## 2. Phase 0 — Spearman ρ, hourly net import vs NY price / vs own spread

Spread = NY landing-zone DA LBMP − neighbour price (PJM_AC: NY `PJM` proxy − PJM `NYIS`, since its
PAR landing spans zones). Entries: **ρ_NY / ρ_spread**.

| group | 2021 | 2022 | 2023 | 2024 | 2025 | S1 | S2 | median | identified |
|---|---|---|---|---|---|---|---|---|---|
| IESO | +0.08 / +0.24 | +0.29 / +0.37 | +0.07 / +0.37 | +0.22 / +0.31 | +0.46 / +0.49 | ✓ | ✓ | 0.37 | **yes** |
| PJM_AC | +0.50 / +0.59 | +0.30 / +0.64 | +0.33 / +0.44 | +0.21 / +0.09 | +0.35 / +0.12 | ✓ | ✗ | 0.44 | no |
| PJM_HTP | +0.55 / +0.48 | +0.22 / +0.47 | +0.38 / +0.49 | −0.05 / +0.14 | +0.08 / +0.08 | ✓ | ✓ | 0.48 | **yes** |
| PJM_VFT | +0.21 / +0.35 | +0.11 / +0.27 | +0.03 / +0.25 | +0.04 / +0.29 | +0.13 / +0.23 | ✓ | ✓ | 0.27 | no (S3) |
| PJM_NEPTUNE | +0.07 / −0.22 | +0.11 / −0.18 | +0.02 / +0.00 | +0.10 / +0.05 | +0.24 / +0.35 | ✗ | ✗ | 0.00 | no |
| NE_AC | −0.25 / +0.43 | −0.31 / +0.24 | −0.36 / +0.27 | −0.25 / +0.40 | −0.33 / +0.40 | ✓ | ✓ | 0.40 | **yes** |
| NE_CSC | −0.12 / +0.04 | −0.07 / +0.25 | +0.04 / −0.01 | −0.03 / +0.31 | −0.22 / +0.16 | ✗ | ✓ | 0.16 | no |
| NE_1385 | +0.05 / +0.52 | −0.10 / +0.46 | −0.01 / +0.45 | −0.14 / +0.46 | −0.33 / +0.40 | ✓ | ✓ | 0.46 | **yes** |

HQ is not tested (no market price). Measured net import, TWh/yr 2021–2025: NE_AC
−5.17 / −3.51 / −4.47 / −5.87 / −5.76; Neptune 2.73 / 4.21 / 5.53 / 5.41 / 5.42; VFT 2.25–2.52;
CSC 1.36–1.94; HTP 2.81–3.95; 1385 0.74 → −0.07.

## 3. What the numbers say

- **NE_AC is the clean result.** Anti-monotone in the NY price every year, monotone in its own
  spread (CAPITL − Roseton) every year. It is a genuine two-way economic tie, and a net
  **exporter** of 3.5–5.9 TWh/yr. This is the tie NEXT-7 found the star node cannot represent
  (Capital_Hudson imports at cap).
- **The unidentified downstate lines are rating-bound, not spread-bound.** Hourly p10 / p50 / p90:
  Neptune 375 / 375 / 375 (2021) then 560–633 / 660 / 660 (2023–25); VFT ≈ 75–210 / 315 / 315;
  CSC 0 / 154–327 / 330. They sit at their line ratings or off. Their flow is set by
  availability and long-term contract scheduling (Neptune and CSC are LIPA-contracted), which a
  spread ladder cannot represent and should not try to.
- **PJM_AC weakens after 2023** (ρ_spread 0.09 / 0.12 in 2024 / 2025, below its NY-price ρ). The
  proxy-to-proxy spread is not what schedules it in those years.
- **Why STOP is correct, not just rule-bound.** A construction limited to the four identified
  groups would leave Neptune + VFT + CSC (6.92 / 8.53 / 9.24 / 9.48 / 9.33 TWh/yr, 2021–2025) on a fungible star node that can
  still re-route whatever the split removes, which is the NEXT-7 failure mode.

## 4. Successor objects (not tested here)

1. **NE_AC as its own two-way node, priced at its own spread** — the identified piece of the
   location defect (NEXT-7: Capital_Hudson excess 2.3–4.65 TWh/yr). Chartering it **alone** is a
   rule chosen **after** seeing this table, so it needs an owner ruling and its own ex-ante gates.
2. **Rating-bound downstate lines as availability blocks.** Neptune, VFT and CSC at their
   published ratings × a measured availability, landed on NYC / LI. Rule 13 applies: the rating
   and the contract are forward inputs; the hourly schedule is an outcome and cannot be pinned.
3. **IESO 2025 May–Dec** stays a data gap unless IESO republishes a yearly OZP file.

## 5. Record

- Matrix shard `NYISO.js`: `seam_neighbour_anchored_ladder` stays **G** (intake now done;
  refused on the ex-ante identification rule); `seam_neighbour_hourly_ladder` U → **G**, same
  evidence.
- Retrievability: nothing solved; nothing to promote. Intake, probe, JSON and this record land on
  `main` with the lane PR.
