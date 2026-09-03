# FINDING — capx D45: the once-only PJM + NYISO clearing-half + curve-ON charter — PJM's "$0 where the model sits" is a BASIS artifact (ELCC-class supply over a mixed-vintage composite requirement: restated on the auction's own UCAP basis the model sits 2–4 points past the zero-cross, at the market's committed quantity), the curve-ON over-fire does NOT survive the market's own price (13.0 of 18.1 GW of the 2022 coal decisions would pass at $21/kW-yr), and NYISO's latent flip is [FILLED IN §5]

**Lane:** capx D45 — director r#31, the once-only cross-ISO clearing-half + curve-ON charter
(D6 + D28 R3). Branch `claude/capx-d45-pjm-nyiso-curves-f3dn56`; the pre-declaration
`PREDECL-capx-d45-pjm-nyiso-curves-2026-09-03.md` was pushed (and merged, PR #4643) before
the first solve started and is graded at full magnitude in §7, misses included.
**Four solves, one ISO at a time** (rule 12; PJM ~8 GB peak on this 15 GB host), years
sequential inside each. **NOTHING ARMS**: no `ScenarioConfig` field added or moved, no
matrix row (rule 28 not triggered), no keeper / shard / marker, backcast namespace
untouched. Rule-14 sign discipline held: nothing below was sized by a residual; every
identified repair names its published source.

| leg | run id | cache key | posture | HEAD | wall |
|---|---|---|---|---|---|
| L1 | `pjm-2021-2025-realized-t1h-d45` | `ea767a6254b8e4af` | live (curve-ON) + diagnostics | `86e676c2` | 16.4 min |
| L2 | `nyiso-2021-2025-realized-t1h-d45` | `212eb1c57251fdc6` | live (curve-OFF, flat $110) + diagnostics | `6b7b8fba` | [§5] |
| L3 | `nyiso-2021-2025-realized-t1h-d45-curveon` | `88f39cbe48b958c3` | L2 + `--capacity-market-clearing` | `6b7b8fba` | [§5] |
| L4 | `pjm-2021-2025-realized-t1h-d45-fixed` | `8d4e574cb496bd01` | L1 + `--fixed-net-cone` | `6b7b8fba` | [§4] |

**Posture vintage per leg (the D44 collision, a fact):** every leg records
`fossil_announced_exits_enabled=False` and `hindcast_verified_announced_exits=True` — the
pre-D44 fossil-dates posture; D44 had not landed at any launch. L1 solved at the branch
point `86e676c2`; the branch was merged mid-session (PR #4643) and the remaining legs
solved at the merged `6b7b8fba`. The only solve-path diff between the two HEADs is the
miso-202 `unit_outage_per_unit_clip` field, GATED default-OFF and registered in the
cache-key-optional set at `"False"`, so the default posture is byte-equivalent — proven
by L2 keying at exactly the pre-declared `212eb1c57251fdc6`. The four keys were
pre-declared and every realized key matched.

## 0. Verdict (one paragraph)

**PJM.** The charter's D6/D28 object — the live curve pays $0 in every hindcast screen —
is confirmed on the first diagnostics-on live-posture solve (entering positions 1.171 /
1.137 in 2023 / 2024, $0 both years) **and is a BASIS artifact, not a census one**: HEAD
accredits PJM's 2021–2024 fleet on the 2025/26 ELCC-class design (thermal 137.6 of
172.9 GW nameplate) and tests it against a mixed-vintage composite requirement
(0.871 × peak = 130.3 GW), where the auctions those years actually cleared on the
pre-CIFP UCAP design (thermal at 1 − EFORd) against a published 166.4 GW UCAP
requirement. Restated on the auction's own basis the SAME fleet sits at **1.057** in 2021
against the market's committed **1.049**, and its entering screens sit at **1.077 /
1.077 / 1.095** — 2–4 points past each vintage's published zero-cross (1.064–1.074), still
$0, but **8–14 points BELOW the published OFFERED position** (1.13–1.22) the pre-declaration
guessed it would match. So PJM's clearing-half question is a 2–4-point question on the
right basis, not a 10-point one: the model's census is the market's committed quantity
plus the DR it nets instead of counting, and the price forms where a 2–4-point-shorter
cleared stack meets a curve that is steepest exactly there ($15–21/kW-yr at 1.05, $0 at
1.066). **The curve-ON over-fire (the original D6 signal) does not survive the market's
own price:** re-screening L1's 2022 decision cohort at the published cleared position's
curve price ($20.86/kW-yr, i.e. $17.3 per accredited coal kW) passes **13.0 of the 18.1 GW
of coal the screen decided**, because the cohort's median margin gap to its $58.5 bar is
$14.8/kW-yr — the D6 object is the clearing half plus the basis devintage, not a curve
shape. In 2025 the object inverts: the 2024 wave leaves the model 4 points SHORT
(0.962) and the 2025/26 vintage pays its cap ($164.84/kW-yr) where the market paid $98.5
at 1.005. **NYISO.** [§5]. **No default moves in either ISO** (§6); this was the once-only
clearing-half charter (§9).

## 1. What the PJM live posture actually did (L1)

Score (committed `score.json`, bands per the T1-H rubric) — **identical to the decimal
to the last committed PJM live-posture leg** (`pjm-2021-2025-realized-verified-exits`,
2026-08-22, key `4c2c7907805e679b`): HEAD moved ~200 commits between them and none of it
touched a PJM default solve.

| row | model | actual | band |
|---|---:|---:|---|
| `retire.total_gw` | 18.147 | 15.062 | **FAIL +20.5 %** |
| coal | 18.137 | 10.299 | +76 % |
| gas_cc / gas_ct / gas_st / oil | 0.000 each | 0.434 / 0.808 / 2.702 / 0.613 | −100 % each |
| `unit_recall_gt300` | 16/20 = 0.80 | band 0.70 | PASS |
| `false_retire` | 7.839 GW (43 %) | band 0.15 | **FAIL** |
| `add.by_tech` wind / solar / gas_cc / gas_ct / storage | 3.0 / 9.762 / 8.118 / 1.013 / 0.0 | 1.619 / 13.066 / 8.525 / 0.442 / 0.283 | FAIL / FAIL / PASS / FAIL / FAIL |
| LOYO recall folds (−2024 / −2025) | 0/19 / 15/19 | — | FAIL / PASS |

**The mechanism, read off the committed ledgers** (`docs/handoffs/d45/positions-from-ledgers-2026-09-03.json`):

| screen yr | peak | HEAD requirement | entering position (ledger) | curve pays | coal decided / executed | failing-but-capped (all fossil) |
|---|---:|---:|---:|---:|---|---:|
| 2022 (bridge) | — | — | (> zero-cross; every row $0) | $0 | **decided 18,137 MW** (86 units) | 93,595 MW |
| 2023 | 147,605 | 128,566 | **1.1706** | $0 | re-confirmed 18,137 | 89,457 |
| 2024 | 153,121 | 133,371 | **1.1367** | $0 | **executed 18,137** | 92,879 |
| 2025 | 160,560 | 144,632 (FPR 0.938) | **0.9617** | **$164.84** (2025/26 cap) | none fails | 0 |

Three readings. (i) The 2022 decision screen fails essentially the entire fossil fleet
(111.7 GW of candidates: coal 32.9, gas_cc 38.5, gas_ct 25.8, gas_st 10.4, oil 4.2 GW)
at a $0 capacity leg; the pipeline's exit-rate cap converts that into an 18.1 GW all-coal
cohort and throttles the rest (`entry_capped`). The zero non-coal exits are therefore a
CAP artifact on top of a $0 artifact: gas_ct / gas_st / oil candidates carry **exactly
zero energy margin** (their gap equals their bar: $21 / $35 / $25 per kW-yr), so at $0
capacity revenue they all fail and the cap decides which class exits — coal first. (ii)
The coal cohort's margin gap is SMALL: net revenue $45.3 vs a $58.5/kW-yr bar, gap
median $14.8 (p25 $3.7, p75 $28.3). (iii) After the 2024 wave the model is SHORT of its
own 2025 bar (0.962 — the FPR path steps the requirement +11 GW while the fleet lost
18 GW) and the 2025/26 curve pays its cap; the entry screen then sees a $99–122k/MW-yr
capacity term (the diagnostics dumps' first strictly-positive PJM capacity terms) and
decides gas_ct.

## 2. PJM stage 2 — the position and evaluation-quantity reconciliation (published data only)

### 2.1 Where the RPM really sat

Instrument: `docs/handoffs/d45/published-positions-2026-09-03.py/.json`. Sources: the
six BRA reports fetched in-session (sha256 in §8; Table 6 UCAP offered by type, Table 1/2
cleared UCAP, price and Total Reserve Margin, Table 5 ICAP supply ledger), the committed
`auction-price/pjm/pjm.csv` and `demand-curve/pjm/pjm.csv` rows.

| DY | RTO reliability requirement (UCAP) | FRR-adj + EE (RPM denominator) | offered (RPM, UCAP) | cleared (RPM, UCAP) | pos offered | pos cleared | (1+RM)/(1+IRM) | real $/kW-yr | HEAD curve @ cleared | zero |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021/22 | 166,355.1 | 157,073.7 | 186,504.8 | 163,627.3 | 1.187 | 1.042 | 1.049 | 51.10 | 57.37 | 1.074 |
| 2022/23 | 163,268.9 | 137,461.6 | 167,698.4 | 144,477.3 | 1.220 | 1.051 | 1.047 | 18.25 | 20.86 | 1.066 |
| 2023/24 | 163,166.2 | 137,291.5 | 156,614.5 | 144,870.6 | 1.141 | 1.055 | 1.048 | 12.46 | 15.30 | 1.065 |
| 2024/25 | 164,107.6 | 139,722.9 | 157,362.7 | 147,478.9 | 1.126 | 1.056 | 1.050 | 10.56 | 14.46 | 1.064 |
| 2025/26 | 144,450.0 | 135,023.4 | 135,692.3 | 135,684.0 | 1.005 | 1.005 | 1.006 | 98.52 | 104.48 | 1.067 |
| 2026/27 | 146,105 | — | 135,191.8 | 134,205.3 | — | — | 0.998 | 120.15 | — | 1.045 |

HEAD's vintage curves reproduce the real clearing price at the cleared position to
+6 % … +37 % (and +6 % at 2025/26 once the published EE addback is kept in the
denominator, which the committed vintage does) — D28's "published-faithful shape" verdict
stands; nothing in the shape is this lane's object.

### 2.2 The model's position on ONE basis — the reconciliation

HEAD's PJM position is `ELCC-class firm ÷ [(1 − 0.0397) × 1.178 × 0.7699 × peak]` for
2021–2024 (the composite; `resolve_forecast_pool_requirement` deliberately returns None
for pre-2025 delivery years) and `÷ [(1 − 0.0397) × 0.938 × peak]` for 2025. Both halves
of the pre-2025 fraction are on the 2025/26+ design: the thermal fleet is accredited at the
2026/27 ELCC class ratings (`THERMAL_ACCREDITATION_BASIS_BY_ISO["PJM"] = "elcc_class_rating"`,
no vintage axis), and the requirement's 0.7699 is the 2026/27 FPR/(1+IRM). The auctions
the model is hindcasting cleared on the pre-CIFP UCAP design: thermal at 1 − EFORd,
against a published UCAP FPR of 1.0898 / 1.0868 / 1.0901 / 1.0894 — rows that are ALREADY
in `demand-curve/pjm/pjm.csv` and that the resolver skips by construction.

Restating L1's own ledger fleet on the pre-CIFP basis (thermal 1 − EFORd by class,
hydro 1 − EFORd, wind/solar at Manual 21's 14.7 % / 38 % class values, storage and the
tie as the ledger carries them) against the PUBLISHED RTO reliability requirement:

| yr | ELCC-basis firm (ledger) | HEAD requirement | **HEAD position** | UCAP-restated firm | published RTO requirement | **restated position** | market (1+RM)/(1+IRM) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 (post-evolution, base fleet) | 148,559 | 130,295 | 1.140 | 175,788 | 166,355 | **1.057** | **1.049** |
| 2023 (post) | 151,599 | 128,566 | 1.179 | 179,696 | 163,166 | 1.101 | 1.048 |
| 2024 (post, after the wave) | 137,419 | 133,371 | 1.030 | 164,170 | 164,108 | 1.000 | 1.050 |
| entering 2022 screen | | | (> zero) | 175,788 | 163,269 | **1.077** | cleared 1.051 |
| entering 2023 screen | | | 1.171 | 175,788 | 163,166 | **1.077** | cleared 1.055 |
| entering 2024 screen | | | 1.137 | 179,696 | 164,108 | **1.095** | cleared 1.056 |

Readings. (i) **In the base year the model's census IS the market's committed quantity
on the right basis**: 1.057 vs 1.049, under one point. (ii) The HEAD reading of 1.14–1.18
is the ratio of two mis-based halves — ELCC supply understates the UCAP fleet by 15 %,
the composite requirement understates the published bar by 22 % — and lands, by
coincidence, on the market's OFFERED position; the pre-declaration's P4 read that
coincidence as a census fact and is graded a MISS on the mechanism (§7). (iii) On the
restated basis the ENTERING screens sit 2–4 points past the vintage zero-crosses, so the
$0 readings SURVIVE the basis correction — but now the gap to the cleared quantity is
2–4 points, on the steepest stretch of the curve. (iv) By category (2021/22, UCAP): the
model's restated internal generation 174.5 GW vs the RPM's offered generation 171.7 + FRR
commitments ~12.8 = 184.5 (−5 %) and cleared generation 150.4 + 12.8 = 163.2 (+7 %); DR
is the missing supply category — the model nets 5.9 GW from the peak where 11.1 GW UCAP of
DR CLEARED as supply (a documented reconciliation, `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`).

### 2.3 Identified PJM repairs (named with source, NOT built)

1. **Accreditation-design devintage (both halves together).** For delivery years
   ≤ 2024/25, accredit thermal at UCAP (1 − EFORd — the registry default every other
   UCAP ISO uses) and resolve the requirement from the PUBLISHED pre-CIFP FPR
   (1.0898 / 1.0868 / 1.0901 / 1.0894, in-repo rows, PJM Planning Period Parameters
   2021/22–2024/25); switch to the ELCC-class ratings + post-CIFP FPR from 2025/26
   exactly as the published design did. Source: PJM Manual 18 / the per-DY Planning
   Period Parameters workbooks (committed) + the 2025/26 CIFP ELCC filing (ER24-99). One
   vintage axis on the existing `THERMAL_ACCREDITATION_BASIS_BY_ISO` +
   `resolve_forecast_pool_requirement`; zero free parameters. Sign (rule 14): moves the
   2021–2024 positions DOWN 6–9 points — toward the curve — i.e. capacity revenue UP and
   retirements HARDER in exactly the years the model over-retires.
2. **DR as supply, not a peak netting, for PJM.** Published: BRA Table 3A/6 DR offered /
   cleared UCAP per DY (11.9/11.1 GW 2021/22 … 10.1/8.1 2023/24; 6.0/5.9 2025/26). Sign:
   +5 GW of counted supply, positions UP ~3 points (the one repair that moves AWAY from
   the curve; it is nonetheless the market's own accounting and enters formulaically).
3. **The clearing half (the R3 object, PJM instance).** On the corrected basis the
   census exceeds the cleared quantity by 2–4 points and the price forms at the cleared
   quantity. PJM's own mechanism is a supply curve of sell offers capped at each unit's
   avoidable cost net of E&AS (Manual 18 §6 / the MSOC), cleared against the VRR curve
   — the model already carries every ingredient (per-unit going-forward cost and E&AS
   margin are the retirement screen's own operands), so a faithful representation is
   "clear the VRR curve against the fleet's net-ACR offer stack" rather than "evaluate
   the curve at the census". Identification source: the BRA reports' offered-vs-cleared
   quantities per DY (validation observables, never targets). Successor per-ISO lane;
   not built here.
4. **The exit-rate cap's class ordering** (§1 (i)): a separate, D32/D42-class object
   (the missing non-coal channel) — routed, not this lane's.

## 3. PJM stage 3 — does the curve-ON over-fire survive the corrected position?

The D6 signal was FFR-2E's shipped-vs-fixed pair (33.7 vs 4.1 GW at the 2026-08-02
epoch). Adjudicated here two ways.

**(a) Zero-solve re-screen of L1's own failing candidates at the market's price**
(`counterfactual_at_published_position`, HEAD vintage curve at the published cleared
position, thermal accreditation on the screen's own ELCC seam; a bound — year-to-year
dynamics not replayed):

| screen | model price | counterfactual price (cleared pos) | decided coal | of which would PASS | capped coal / gas_cc that would pass |
|---|---:|---:|---:|---:|---|
| 2022 | $0 | $20.86 (× 0.83 = $17.3 per coal kW) | 18,137 MW | **13,019 MW (72 %)** | 10,438 / 14,248 MW |
| 2023 (re-confirm) | $0 | $15.30 | 18,137 (re-confirmed) | — (10,243 capped coal + 12,084 gas_cc pass) | |
| 2024 (execute) | $0 | $14.46 | — | (12,989 gas_cc pass) | |
| at the market's (1+RM)/(1+IRM) position instead | | $26.4 / $26.4 / $24.1 | | 2022: 25,342 coal + 26,448 gas_cc pass | |

**(b) L4, the one-field fixed-anchor control** — [§4, filled after L4].

Adjudication (a): **the over-fire does not survive the market's own price.** A $15–21/kW-yr
capacity leg — the published curve at the published cleared position — flips the majority
of the 2022 coal decisions, because PJM coal's screen gap is a median $14.8/kW-yr, not the
~$40 the pre-declaration assumed (P9, MISS). And it is the CLEARING HALF, not the curve:
at the model's own entering position the curve is $0 whether the basis is HEAD's or the
restated one (§2.2 (iii)); at the market's cleared position it is $15–21. The 2025 half of
P9 is moot rather than confirmed: after the wave nothing fails in 2025 and the curve pays
its cap. **No PJM default moves** — the curve stays ON (it is the published design and the
2028/29+ floor makes $0-at-long impossible forward, D28 §4), and the repair is §2.3 items
1–3 in that order, per-ISO.

## 4. L4 — the fixed-anchor control (PJM one-field A/B)

[filled after L4]

## 5. NYISO — L2 (live, curve-OFF) and L3 (curve-ON probe)

[filled after L2/L3]

## 6. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

[filled]

## 7. The pre-declaration, graded at full magnitude

[filled]

## 8. Sources fetched in-session (sha256), governance attestation

[filled]

## 9. Close-out

[filled]
