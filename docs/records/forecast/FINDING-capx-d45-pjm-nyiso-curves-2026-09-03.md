# FINDING — capx D45: the once-only PJM + NYISO clearing-half + curve-ON charter — PJM's "$0 where the model sits" is a BASIS artifact (ELCC-class supply over a mixed-vintage composite requirement: restated on the auction's own UCAP basis the model sits 2–4 points past the zero-cross, at the market's committed quantity), the curve-ON over-fire does NOT survive the market's own price (13.0 of 18.1 GW of the 2022 coal decisions would pass at $21/kW-yr), and NYISO's latent flip is a POSITION artifact (the requirement 2 GW low on the realized-peak basis; the NYC/LI/G-J locality un-represented) that fires at +189 % when the published curve is consulted — do not arm (filled 2026-09-04 by D45-R, §5–§6)

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
| L2 | `nyiso-2021-2025-realized-t1h-d45` | `212eb1c57251fdc6` | live (curve-OFF, flat $110) + diagnostics | `6b7b8fba` | never ran (Q33) — see the correction below; the realized leg is in §5 |
| L3 | `nyiso-2021-2025-realized-t1h-d45-curveon` | `88f39cbe48b958c3` | L2 + `--capacity-market-clearing` | `6b7b8fba` | never ran (Q33) — realized leg in §5 |
| L4 | `pjm-2021-2025-realized-t1h-d45-fixed` | `8d4e574cb496bd01` | L1 + `--fixed-net-cone` | `6b7b8fba` | never ran (Q33) — realized leg in §4 |

**Posture vintage per leg (the D44 collision, a fact):** every leg records
`fossil_announced_exits_enabled=False` and `hindcast_verified_announced_exits=True` — the
pre-D44 fossil-dates posture; D44 had not landed at any launch. L1 solved at the branch
point `86e676c2`; the branch was merged mid-session (PR #4643) and the remaining legs
solved at the merged `6b7b8fba`. The only solve-path diff between the two HEADs is the
miso-202 `unit_outage_per_unit_clip` field, GATED default-OFF and registered in the
cache-key-optional set at `"False"`, so the default posture is byte-equivalent — proven
by L2 keying at exactly the pre-declared `212eb1c57251fdc6`. The four keys were
pre-declared and every realized key matched.

*Correction appended 2026-09-04 by capx D45-R (owner ruling Q33 — D45 died after L1): the L2 / L3 / L4 rows above describe legs D45 never ran; their bundles do not exist and their `VERDICT_MAP` rows were re-pointed in place to this lane's run ids. The legs that exist are `nyiso-2021-2025-realized-t1h-d45r` (`91686abe7a744a88`, 12.2 min), `nyiso-2021-2025-realized-t1h-d45r-curveon` (`cad77112c804881d`, 11.8 min) and `pjm-2021-2025-realized-t1h-d45r-fixed` (`896da48960560a29`, 20.5 min), all at HEAD `334be8c2` with `fossil_announced_exits_enabled=True` (the POST-D44 posture, not the pre-D44 one the paragraph above records) and keepers PJM `2026-08-15-pjm-162-inputclock` / NYISO `2026-09-04-nyiso-186-astoria-identity`; L1 was replayed at the same HEAD as `pjm-2021-2025-realized-t1h-d45r` (`c6091bd5b62bbc3f`, 23.2 min) and holds the bare `pjm-t1h`, with the pre-D44 L1 preserved at `pjm-t1h-pre-d45r`. Every key was re-declared in `PREDECL-capx-d45r-2026-09-04.md` before its solve and every one matched. §4–§9 below are filled by D45-R; §0–§3 stand as D45 wrote them, with dated corrections where a HEAD result changes a reading (§4.0).*

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
at 1.005. **NYISO.** (Filled 2026-09-04 by D45-R.) The live curve-OFF posture decides nothing — every L2 exit is exogenous — and the model's SUPPLY is the market's within 0.6 GW; the +6.5 / +5.2-point position excess in 2023 / 2024 is entirely the REQUIREMENT half (the realized weather-year peak in place of the NYSRC ICAP-market forecast peak, 1.9–2.2 GW; the single 2025-26 vintage factor, 2.1 points in 2024). Consulting the published curve at that position fires the D28 latent flip at **+189 %** (3.5 GW of downstate steam at $0, then a one-year cobweb), while the same curve at the PUBLISHED position reproduces the real spot within 4–10 %: a position artifact first, the curve second; none of the three pre-stated arming conditions is met (§5). **No default moves in either ISO** (§6); this was the once-only
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

**(b) L4, the one-field fixed-anchor control** — filled in §4.1 (2026-09-04, D45-R): at the flat $77.43 the screen fails nothing (6.543 GW, all dated exits) against the curve-ON replay's 17.958 GW; the pair brackets the clearing half from both sides and confirms (a).

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

*Filled 2026-09-04 by capx D45-R. D45 died before L4 (owner ruling Q33), so the pair
below is L4 against THIS lane's L1 replay at HEAD (`pjm-2021-2025-realized-t1h-d45r`,
key `c6091bd5b62bbc3f`, post-D44 posture, keeper `2026-08-15-pjm-162-inputclock`) —
one field apart (`capacity_market_clearing_by_iso` PJM-ON vs `None`), same HEAD
`334be8c2`, same dated-exit set. L4 key `896da48960560a29` (pre-declared, matched),
20.5 min / 9.6 GB, registered suffixed as `pjm-t1h-d45r-fixed`. The L1 replay's own
result — which is also PJM's first measurement of the D44 dates channel — is in §4.0
because it changes what L4 is compared against.*

### 4.0 The L1 replay at HEAD: the dates channel RE-ROUTES coal out of the cap-bound cohort

| row | D45 L1 (pre-D44, `pjm-t1h-pre-d45r`) | **L1 replay (post-D44, bare `pjm-t1h`)** | actual |
|---|---:|---:|---:|
| `retire.total_gw` | 18.147 (+20.5 %, FAIL) | **17.958 (+19.2 %, FAIL)** | 15.062 |
| coal — economic / announced / derates | 18.137 / 0 / 0 | **11.415 / 4.551 / 1.023** | 10.299 |
| gas_st / gas_cc / oil / gas_ct | 0 / 0 / 0 / 0 | **0.833 / 0.075 / 0.051 / 0** (all announced) | 2.702 / 0.434 / 0.613 / 0.808 |
| `unit_recall_gt300` | 16/20 = 0.80 PASS | **17/20 = 0.85 PASS** | — |
| `false_retire` | 7.839 GW (0.432) FAIL | **6.691 GW (0.373) FAIL** | — |
| LOYO −2023 / −2024 / −2025 recall | 12/12 / 0/19 / 15/19 | 12/12 / **8/19** / 16/19 | — |
| entering CR-1 position 2023 / 2024 / 2025 | 1.1706 / 1.1367 / 0.9617 | **1.1398 / 1.0964 / 0.9617** | — |
| curve pays | $0 / $0 / $164.84 (cap) | **$0 / $0 / $164.84** | — |
| 2022 screen: decided / admission-capped coal | 18,137 / 14,729 MW | **11,415 / 10,999 MW** | — |
| additions wind / solar / gas_cc / gas_ct / storage | 3.0 / 9.762 / 8.118 / 1.013 / 0.0 | **identical to the decimal** | — |

The channel armed 33 live rows / 13,169 MW (2021–2028; the in-window 7.8 GW of §1.5 of
the pre-declaration plus 5.3 GW dated 2026–2028). What it did is the MISO reading, not the
addition the pre-declaration expected: a plant carrying a pending filed date — in-window
OR post-window — is exempt from the economic screen (rule 19), so ~10.4 GW of coal leaves
the 2022 failing pool (decided + admission-capped coal 32.9 → 22.4 GW) and the cap-bound
decision cohort shrinks 18.1 → 11.4 GW, while the channel itself executes 4.55 GW of coal
(+1.02 GW derates) and 0.96 GW of steam/CC/oil. Net coal −1.15 GW, net total −0.19 GW,
recall +1 unit, false-retire −1.15 GW, non-coal classes open off exactly zero (gas_st
0.833 GW: Yorktown-class dated steam), the −2024 LOYO fold moves 0/19 → 8/19 (the dated
units are exactly the fold's targets). The entry side is blind to all of it (additions
byte-identical). Entering positions fall 3–4 points with the dated exits but stay past
each vintage's zero-cross, so the curve's $0 / $0 / cap reading — the D6/D28 object — is
unchanged at HEAD.

**A dated correction to §2.2 (iii)**, appended rather than edited: restated first-order
on the auctions' own UCAP basis (§2.2's 175,788 / 148,559 = 1.183 UCAP-per-ELCC ratio
applied to the replay's entering ELCC firm of 146,541 / 146,228 MW), the HEAD entering
screens now sit **≈ 1.063 (2023) and ≈ 1.054 (2024)** against the published RTO
reliability requirement — at the 2023/24 zero-cross and AT the market's cleared position
(1.055 / 1.056) — where §2.2 had 1.077 / 1.095 for the pre-D44 fleet. The "2–4 points
past the cleared quantity" of §0 is therefore **0–1 point at HEAD** in 2023–2024: with the
filed dates honored, PJM's $0 is a pure basis artifact in those years, and the market's
own curve at the restated position pays $14–20/kW-yr. The ratio is a first-order scaling
(coal's UCAP/ELCC ratio differs from the fleet mean); §2.3 item 1 is the exact repair.

### 4.1 L1 vs L4 — the one-field pair

| | **L1 replay (curve-ON, $0 / $0 / cap)** | **L4 (fixed $77.43/kW-yr × UCAP)** |
|---|---:|---:|
| economic screen: candidates failed, any year | 2022: decided coal 11,415 MW + 77 GW admission-capped fossil | **none — `pipeline_events` empty in every solve year** |
| coal economic / announced / derates | 11.415 / 4.551 / 1.023 GW | **0.000** / 4.551 / 1.023 |
| `retire.total_gw` | 17.958 (+19.2 %, FAIL) | **6.543 (−56.6 %, FAIL)** |
| `unit_recall_gt300` | 17/20 = 0.85 PASS | **8/20 = 0.40 FAIL** |
| `false_retire` | 6.691 GW (0.373) FAIL | **0.000 PASS** |
| LOYO −2023 / −2024 / −2025 recall | 12/12 / 8/19 / 16/19 | 6/12 / 8/19 / 8/19 (all FAIL) |
| rm after 2024 / 2025 | −0.103 / −0.140 | −0.041 / −0.067 |
| gas_ct backstop 2025 | 1,012.8 MW fires | **does not fire** |
| additions otherwise | — | identical |

**Reading.** The D6 signal — "the curve-ON leg over-fires relative to the fixed leg" — is
reproduced on the live stack at +11.4 GW (17.96 vs 6.54; FFR-2E's 2026-08-02 pair read
33.7 vs 4.1). But the pair now brackets the truth from **both** sides: $0 over-fires coal
by 6.7 GW against the 10.3 GW actual, and a flat $77.43 under-fires it by 4.7 GW, because
$77 × 0.83 ≈ $64/kW-yr clears the entire cohort's $14.8/kW-yr median gap and the screen
fails nothing at all — L4's 8/20 recall is the dates channel alone. The published curve at
the published CLEARED position pays $15–21/kW-yr in 2022–2024 (§2.1), and §3(a)'s
zero-solve re-screen at that price passes 13.0 of the 18.1 GW the $0 screen decided;
the pair confirms from the live stack that the answer lies between the two arms, at the
price a clearing half would form. **P3′ grades:** direction HIT (L4 < L1 by 11.4 GW,
inside the 10–18 GW band), L4 economic coal 0 (inside 0–5), L4 total 6.5 GW **below** the
8–13 GW band (MISS — the dated set is 5.6 GW of coal-equivalent, not the 7.8 GW nameplate
the band was built on), and L4 recall 0.40 (**MISS** — the pre-declaration's amendment
of D45 P3 was wrong and D45's original "falls below 0.70" was right: the dated channel
carries only 8 of the 20 large targets).

**(b) of §3, filled:** the fixed-anchor control confirms §3(a). No PJM default moves.

## 5. NYISO — L2 (live, curve-OFF) and L3 (curve-ON probe)

*Filled 2026-09-04 by capx D45-R (owner ruling Q33: D45 died after L1; this lane ran the
owed legs AT HEAD — post-D44 posture, keeper `2026-09-04-nyiso-186-astoria-identity`,
HEAD `334be8c2`). Both keys were re-declared in `PREDECL-capx-d45r-2026-09-04.md` and
both realized exactly: L2 `91686abe7a744a88` (12.2 min / 3.5 GB), L3 `cad77112c804881d`
(11.8 min / 3.5 GB), solved concurrently on a clean tree. L2 registers as the bare
`nyiso-t1h` (the FFR-3A-2-vintage record preserved verbatim at `nyiso-t1h-pre-d45r` —
D45 never reached L2, so no `-pre-d45` preserve ever existed for NYISO); L3 registers
suffixed as `nyiso-t1h-d45r-curveon`. One vintage correction against this lane's own
pre-declaration, stated here rather than hidden: the PREDECL named the NYISO keeper as
`nyiso-185`; `nyiso-186` was promoted (PR #4698) between the pre-declaration push and the
rebase the legs solved on. The keys did not move (re-verified at `334be8c2`); the keeper
id in every record is 186.*

### 5.1 What the live posture actually did (L2) — the screen decided nothing

| row | model | actual | band |
|---|---:|---:|---|
| `retire.total_gw` | 1.457 | 1.711 | **FAIL −14.9 %** |
| nuclear (announced, 2022) | 1.036 | 1.012 | — |
| gas_ct (the D44 dates channel, 2023) | 0.420 | 0.189 | +122 % |
| oil / biomass / gas_cc | 0.000 each | 0.390 / 0.064 / 0.057 | −100 % each |
| economic retirement events, any year | **0** | — | — |
| `unit_recall_gt300` | 1/1 | band 0.70 | PASS |
| `false_retire` | 0.256 GW (0.176) | band 0.15 | **FAIL** |
| `add.by_tech` wind / solar / gas_cc / gas_ct / storage | 1.902 / 1.782 / 2.0 / 0.5 / **0.000** | 0.890 / 2.197 / 0.0 / 0.072 / 0.184 | FAIL / FAIL / SKIP / FAIL / FAIL |
| LOYO folds −2023 / −2024 / −2025 | recall 1/1 each; false 0.024 / 0.274 / 0.353 | — | PASS / FAIL / FAIL |

Three readings. (i) **At the flat $110/kW-yr anchor the retirement screen is inert**:
`pipeline_events` is the empty list in every solve year and every exit is exogenous —
Indian Point 3 (1,036 MW, the announced nuclear date, executed in the 2022 bridge) and
420 MW of 2023 gas_ct through the D44 dates channel, which is the ONLY in-window fossil
date NYISO's vintage-2020 EIA-860 holds (16 rows / 512 MW ex-ante, 507 MW of it a single
2023 CT plant; nothing else in the NYISO channel before 2027). (ii) The total-band FAIL is
a **target move, not a model move**: against the 1.488 GW target the 2026-07-14 leg was
scored on, 1.457 would PASS (−2 %); the scoring target was rebuilt to 1.711 GW on
2026-09-02 (PR #4615, oil 0.39 + biomass 0.064 + gas_cc 0.057 GW joining the actuals), and
those three classes are exactly the ones the model cannot reach at $110. (iii) The entry
side is bounded now where it was not on 2026-07-14: wind 4.0 → 1.9, solar 8.0 → 1.8,
gas_cc 3.0 → 2.0, gas_ct 4.0 → 0.5 GW — the entry-rate ladders (`binding_cap:
growth_ladder` on every 2024/2025 diagnostics row) — while storage stays at **exactly
0.000 GW** (the D37-class shut channel, predicted to recur and recurring). The
diagnostics dumps' capacity term is `104,500 $/MW-yr` for every thermal candidate in
every year — the flat anchor × the UCAP fraction, never a curve.

### 5.2 NYISO stage 2 — the position and evaluation-quantity reconciliation (published data only)

Instruments: `docs/handoffs/d45/published-positions-2026-09-03.py/.json` (D45's, NYISO
block — every Table D.2 row re-verified this session against the fetched NYSRC 2026-27
IRM Study Appendices, sha256 in §8, and the Potomac SOM summer-margin rows for 2023 and
2024 re-verified the same way) and this lane's
`docs/handoffs/d45/nyiso-reconciliation-2026-09-04.py/.json` (zero solves; reads the L2/L3
ledgers beside the published record and the committed LCR rows).

**5.2.1 Where the NYCA really sat, and where the model sat.** The published position is
the Potomac SOM "UCAP Margin (Summer), % of Requirement" over the NYSRC-adopted UCAP
requirement (`ICAP requirement × (1 − derate)` on the NYSRC ICAP-market forecast peak);
the model's is `firm ÷ requirement` from the ledger identity `firm = peak × (1 + rm)`
against HEAD's `adequacy_requirement_mw`:

| CY | NYSRC peak | adopted IRM | derate | pub UCAP req | pub UCAP supplied | **pub pos** | model peak | model req | model firm entering | **model pos entering** | Δ pts | spot $/kW-yr | HEAD curve @ pub pos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 (base, post-evolution) | 32,333 | 20.7 | 0.0877 | 35,604 | 37,349 | 1.049 | 30,919 | 33,382 | 36,145 (after) | 1.083 (after) | +3.4 | 50.16 | flat vintage |
| 2023 | 32,049 | 20.0 | 0.1014 | 34,559 | 36,045 | 1.043 | 30,206 | 32,612 | 36,145 | **1.108** | **+6.5** | 49.32 | 47.57 |
| 2024 | 31,542 | 22.0 | 0.1321 | 33,397 | 35,334 | 1.058 | 28,990 | 31,300 | 34,745 | **1.110** | **+5.2** | 41.64 | 37.38 |
| 2025 | 31,469 | 24.4 | 0.1300 | 34,059 | 36,034 | 1.058 | 31,857 | 34,395 | 35,829 | **1.042** | **−1.6** | 51.36 | 26.12 |

**5.2.2 The decomposition — the excess is the REQUIREMENT half, and the requirement half
is mostly the PEAK basis, not the factor.**

| CY | requirement gap (model − published) | of which the factor (model 1.0797 vs published UCAP-req ÷ NYSRC peak) | of which the peak (model weather-year peak vs NYSRC ICAP-market forecast peak) | supply gap (model firm entering − published UCAP supplied) | model firm on the PUBLISHED requirement | published supply on the MODEL requirement |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | **−2,222** | 1.0797 vs 1.1012: −2.2 pts ≈ −690 | −1,414 × 1.08 ≈ −1,530 | −1,204 (after) | 1.015 (after) | 1.119 |
| 2023 | **−1,947** | 1.0797 vs 1.0783: **+0.1 pts** ≈ +45 | −1,843 × 1.08 ≈ −1,990 | **+100** | **1.046** | 1.105 |
| 2024 | **−2,097** | 1.0797 vs 1.0588: **+2.1 pts** ≈ +605 | −2,552 × 1.06 ≈ −2,700 | −589 | **1.040** | 1.129 |
| 2025 | **+336** | 1.0797 vs 1.0823: −0.3 pts ≈ −80 | +388 × 1.08 ≈ +420 | −205 | **1.052** | 1.048 |

Readings. (i) **The model's supply is the market's supply, within 0.6 GW in every scored
screen year** (+0.10 / −0.59 / −0.21 GW entering 2023 / 2024 / 2025, on a 36 GW base) —
the pre-declaration's un-signed "supply half" is essentially zero; the base-year fleet
is 1.2 GW light (under-accredited hydro / uncounted SCRs, as D45 P7 hedged), and the
extcap intake (`ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]` = 2,749.9 MW UCAP, capx-D2)
carries the rest. (ii) **The requirement is 1.9–2.2 GW LOW in 2021–2024** — the
pre-declared 1.5–4 GW band — but D45 P7 / D45R P7′ named the wrong cause. The
single-vintage factor (1.244 × 0.8679 = 1.0797) is within 0.3 pts of the published
`UCAP req ÷ NYSRC peak` in 2023 and 2025 and only 2.1 pts high in 2024 (the year NYSRC
adopted 22.0 % where the 2025-26 vintage carries 24.4 %); **the dominant term is the peak
basis**: the hindcast sets the requirement on the model's realized weather-year peak
(30,206 / 28,990 MW in 2023 / 2024 — the mild summers) where the NYSRC requirement is set
on the ICAP-market FORECAST peak (32,049 / 31,542). The same absolute-vs-ratio class
D33/D40 measured for NEISO, but on the demand side rather than the tie side. (iii) On the
published requirement the SAME fleet sits **1.046 / 1.040 / 1.052** — within 0.3 / 1.8 /
0.6 points of the market's 1.043 / 1.058 / 1.058. In 2025 the model is 1.6 points
SHORT of the market on its own bar (the falsifier of P7′, tripped — the 2025 weather
peak is 388 MW above NYSRC's forecast, so the model's bar is the higher one that year).

**5.2.3 The locality half the model does not represent.** The published locational
record (committed, `data/raw/capacity-deliverability/nyiso/nyiso.csv`, LCR reports sha256
in §8): NYC 0.817 / 0.804 / 0.785, Long Island 1.052 / 1.053 / 1.065, G-J 0.854 / 0.810 /
0.788 of locality peak (2023/24 · 2024/25 · 2025/26), with bulk import limits NYC 2,875,
LI 325 → 275, G-J 3,425 → 4,500 MW; and the locality spot prices that record the
binding: NYC **$15.97 / $11.76 / $10.98** per kW-month against the NYCA $4.11 / $3.47 /
$4.28 (2023/24 · 2024/25 · 2025/26). At default HEAD represents NYISO adequacy as one
NYCA-wide position (`capacity_deliverability_limits` off; the NYISO LCR/TSL crosswalk
exists and is unvalidated in any keeper, CLAUDE.md §Locational deliverability), so a
downstate steam unit is paid the NYCA price where the market pays it 3–4× that in Zone J.
This is not a stage-2 residual — it is the mechanism §5.3 turns on.

**5.2.4 Identified NYISO repairs (named with source, NOT built).**
1. **Requirement on the published ICAP-market peak in a hindcast.** Set the NYCA
   requirement on the NYSRC forecast peak for the capability year (Table D.2 column 1 —
   a published market-design input that regenerates forward from the Gold Book forecast,
   the NYISO analogue of the published PJM RTO reliability requirement §2.3 item 1
   already names), not on the realized weather-year peak the dispatch runs. Source: NYSRC
   IRM Study Appendices Table D.2 (2026-27 edition, all years 2011–2025). Sign (rule 14):
   requirement UP 1.5–2.7 GW in 2021–2024 ⇒ positions DOWN 5–8 points toward the market
   ⇒ capacity revenue UP and retirements HARDER under any curve; in 2025 the correction
   goes the other way by 0.4 GW. Zero free parameters.
2. **Per-capability-year adopted IRM + derate factor** in place of the single 2025-26
   vintage (the committed `demand-curve/nyiso/nyiso.csv` already carries the study IRMs
   and translation factors 2020–2025; the ADOPTED values for 2023-24 / 2024-25 are 20.0 /
   22.0, Table D.2). Sign: 2024 requirement DOWN 2.1 pts (the one year the vintage factor
   is high), 2021 UP 2.2 pts, 2023 / 2025 unchanged within 0.3. A vintage axis on
   `PLANNING_RESERVE_MARGIN_BY_ISO` / `…ICAP_TO_UCAP_RATIO_BY_ISO`, the same axis D40
   built for NEISO; zero free parameters.
3. **The locality requirement (NYC / LI / G-J LCRs + import limits) as the NYISO
   instance of `capacity_deliverability_limits`.** Published rows are committed; the
   crosswalk exists. Sign: downstate capacity revenue UP (the NYC locality clears at
   3–4× NYCA), retirements of downstate steam HARDER — exactly the class L3 retires at
   $0. Successor per-ISO lane; the structural half of the D28 R3 object for NYISO.
4. **The base-year 1.2 GW supply gap** (hydro accreditation / SCR counting) — a D2-class
   intake, separately identifiable from the NYISO Gold Book Table III / the ICAP Manual;
   the smallest of the four and the only supply-side one.

### 5.3 NYISO stage 3 — the curve-ON adjudication (L3, one field from L2)

| | L2 (flat $110) | **L3 (published curve, force-ON)** |
|---|---:|---:|
| entering CR-1 position 2023 / 2024 / 2025 | 1.108 / 1.110 / 1.042 (identity) | **1.137** (ledger) / **1.006** / **1.028** |
| capacity leg the screen saw, $/kW-yr | 110 (flat) × UCAP | **$0.00** / $68.62 / $38.63 |
| published curve at the PUBLISHED position | — | $47.57 / $37.38 / $26.12 (real spot $49.32 / $41.64 / $51.36) |
| `retire.total_gw` | 1.457 | **4.953** (+189 %, FAIL) |
| gas_st economic | 0.000 | **3.496 GW** — decided AND executed in the 2023 screen (1-yr gas_st lag) |
| `false_retire` | 0.256 (0.176) | **3.752 GW (0.758)** |
| `unit_recall_gt300` | 1/1 | 1/1 |
| LOYO −2024 / −2025 tr10 | PASS / PASS | **FAIL / FAIL** |
| entry gas_cc / gas_ct | 2.0 / 0.5 | 1.0 / 0.0 |
| position after the 2023 wave | 1.065 | **0.966** (the fleet goes SHORT and pays $69 then $39) |

**Adjudication.** The +123 % latent flip D28 read off the 2026-07-18 probe is **+189 %
on the live stack**, and it is a **position artifact first, the curve second** — in the
exact sense the pre-stated conditions were written to detect. At the model's own 2023
entering position (1.137, past the 1.12 zero-cross) the curve pays $0 and 3.5 GW of
downstate steam fails; at the **published** position (1.043) the same curve pays $47.57,
within 4 % of the real $49.32 spot — the shape is published-faithful and would not have
collapsed the 2023 screen. The 9.4-point gap between the two positions is §5.2's
requirement half (peak basis + the 2024 vintage factor), and the class that fails is the
class §5.2.3 says the NYCA-wide representation underpays by 3–4×. The over-fire is
therefore not evidence that the published curve is wrong for NYISO; it is evidence that
consulting a faithful curve at an unfaithful position produces a faithful-looking cobweb
(short by 2024, cap-side prices, entry frozen). **Pre-stated arming conditions (D45 P9,
re-affirmed verbatim as D45R P9′, all three required):** (a) L3 total within ±10 % —
**NO** (+189 %); (b) L3 `false_retire` in band — **NO** (0.758); (c) L3 entering
positions within ±3 points of the published NYCA positions in every scored year — **NO**
(+9.4 / −5.2 / −3.0). None of three. The recommendation §6 returns is **do not arm**; the
FF-3D flip stays withheld behind repairs 1–3 of §5.2.4, in that order.

## 6. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

*Filled 2026-09-04 by capx D45-R. Both recommendations are made on the conditions D45's
pre-declaration fixed before any solve (P9) and this lane re-affirmed verbatim (P9′),
with one addition (P9′(d)). NOTHING ARMS in this lane; every line below returns to the
owner.*

**NYISO — consult the published ICAP demand curve at default? RECOMMEND: DO NOT ARM
(the FF-3D flip stays withheld).** The pre-stated condition was ALL of (a) L3's
`retire.total_gw` within ±10 %, (b) L3's `false_retire` in band, (c) L3's entering
positions within ±3 points of the published NYCA positions in every scored year — "any
two of three is not enough". Measured (§5.3): (a) **+189 %**, (b) **0.758**, (c) **+9.4 /
−5.2 / −3.0 points** — none of three. The honest reading is the one D45 predicted:
**position artifact first, curve second.** The curve is published-faithful (at the
published position it reproduces the real NYCA spot within 4 % in 2023 and 10 % in 2024)
and the model's SUPPLY is the market's within 0.6 GW; what is unfaithful is the
REQUIREMENT the position is measured against (§5.2.2: the realized weather-year peak in
place of the NYSRC ICAP-market forecast peak, 1.9–2.2 GW; the single 2025-26 vintage
factor, 2.1 points in 2024) and the NYCA-wide representation of a locational market
(§5.2.3: downstate steam paid the NYCA price where Zone J clears at 3–4×). Consulting a
faithful curve at that position is how a 3.5 GW downstate-steam wave and a one-year
cobweb arise from a fleet whose real position never left the 1.04–1.06 band. **P9′(d)
applies too:** L2's own retirement rows are NOT evidence for the curve-OFF posture —
the flat $110 decided nothing, every L2 exit is exogenous, and the total-band miss is a
target move (§5.1) — so the curve-OFF recommendation rests on the position reading
alone. **Route, in order:** §5.2.4 repairs 1 (requirement on the published ICAP-market
peak) and 2 (per-capability-year adopted IRM + derate), then 3 (the locality half), then
re-run this probe; the curve question re-opens only after the position lands within
the ±3-point condition it was written to test.

**PJM — does the curve-ON over-fire survive the corrected position? ANSWERED: NO, and
no PJM default moves either way.** Adjudicated three ways, all agreeing: (i) §3(a)'s
zero-solve re-screen at the market's own price (13.0 of 18.1 GW of the 2022 coal
decisions pass at $20.86/kW-yr); (ii) §4.1's live-stack one-field pair, which brackets
the truth from both sides — $0 over-fires coal by 6.7 GW, a flat $77.43 under-fires it
by 4.7 GW and fails nothing at all; (iii) §4.0's dated correction to §2.2, under which
the HEAD entering screens restated on the auctions' own UCAP basis sit AT the market's
cleared position in 2023–2024 (≈ 1.063 / 1.054 vs 1.055 / 1.056), where the published
curve pays $14–20/kW-yr. The curve stays ON (it is the published design, and the
2028/29+ price floor makes $0-at-long impossible forward, D28 §4); the fixed anchor is
not a candidate (it is the arm that fails nothing); and the D6 object is closed as
**clearing half + basis devintage**, not a curve shape. **Route:** §2.3 items 1 (the
accreditation-design devintage, both halves) and 3 (clear the VRR curve against the
fleet's net-ACR offer stack rather than evaluate it at the census), per-ISO; item 2 (DR
as supply) with them; item 4 (the exit-rate cap's class ordering) to the D32/D42 lane.

## 7. The pre-declaration, graded at full magnitude

*Filled 2026-09-04 by capx D45-R. Two pre-declarations are graded here: D45's original
(`PREDECL-capx-d45-pjm-nyiso-curves-2026-09-03.md`, whose L2/L3/L4 predictions were
never tested by D45 itself) and this lane's (`PREDECL-capx-d45r-2026-09-04.md`). D45's
P1/P2/P4 were graded by D45 on its own L1 (§1–§2: P1 HIT on $0 in 2023/2024 and MISS
on 2025; P2 HIT; P4 MISS on the mechanism) and are not re-graded; its P3/P5/P6/P7/P9
are graded on this lane's legs, which is the only way they can be.*

**Cache keys: 8 pre-declared, 8 realized exactly** (`c6091bd5b62bbc3f`,
`91686abe7a744a88`, `cad77112c804881d`, `896da48960560a29`, `d6c0137e37bf3200`,
`cc7d1050a8090c76`, `321f04e9060787f0`, `8d8bc63a0d4378a9`). Postures as declared on
every leg. One vintage line wrong in the D45-R PREDECL: NYISO keeper `nyiso-185` was
named; `nyiso-186` had landed (PR #4698) by the rebase the legs solved on. Keys did not
move; the records carry 186.

### 7.1 D45's original pre-declaration — the untested half

| # | prediction | outcome |
|---|---|---|
| P3 | L4 coal lower than L1 by 4–15 GW; L4 total 3–12 GW; L4 recall FALLS below 0.70 | **HIT** on all three — coal 16.99 → 5.575 (−11.4), total 6.543, recall 0.40. (D45's reading was right; D45-R's amendment of it, P3′, was wrong.) |
| P5 | L2 total 0.9–1.2 GW (central 1.04), FAIL ≈ −30 %; zero economic events; storage exactly 0 | **SPLIT** — economic events exactly 0 (HIT), storage 0.000 (HIT); total 1.457 (MISS on magnitude: the dates channel's 420 MW CT was not in D45's posture, and the target moved 1.488 → 1.711). |
| P6 | L3 total 2.0–4.5 (central 3.0), gas_st ≥ 1.5, false_retire FAIL; positions 1.10–1.30 past the zero-cross in ≥ 2 of 3 years | **SPLIT** — gas_st-led (3.496) HIT, false FAIL HIT, total 4.953 above the band (MISS), past the zero-cross in ONE year only (2023: 1.137; then 1.006 / 1.028 SHORT — MISS: the cobweb was not predicted). |
| P7 | L2 positions exceed published by +5 to +20 pts in 2023–2025; requirement 1.5–4 GW low; supply sign uncommitted | **SPLIT** — +6.5 / +5.2 (HIT), 2025 −1.6 (falsifier tripped, MISS); requirement −1.95 / −2.10 GW (HIT), +0.34 in 2025 (MISS); supply within 0.6 GW (the uncommitted half reads ≈ zero). Named cause (the single-vintage factor) MISS — the peak basis dominates (§5.2.2). |
| P8 | both bare keys HOLD before/after; FC-7 FAIL → CAVEAT on NYISO as an instrument change | **HIT** |
| P9 (NYISO) | none of (a)/(b)/(c) met; "position artifact first" | **HIT, exactly** |
| P9 (PJM) | the over-fire survives in 2022–2024 at the cleared price, not in 2025 | already graded MISS by D45 §3 (13.0 of 18.1 GW pass at $20.86); L4 confirms the direction of that miss on the live stack |

### 7.2 This lane's pre-declaration

| # | prediction | conf | outcome |
|---|---|---|---|
| P1′ | L1: $0 in 2023 and 2024, cap in 2025; entering 1.11–1.15 / 1.07–1.12 | HIGH | **HIT** — $0 / $0 / $164.84; 1.1398 / 1.0964 / 0.9617 |
| P2′ | L1 total 20–28 GW (dates ADD to a re-filled cap-bound cohort); coal 18–26; gas_st 0.7–1.2; recall ≥ 0.80; false LARGER than 7.839 | HIGH | **MISS on the mechanism** — total 17.958 (below the band), coal 16.99, false 6.691 (SMALLER). The channel RE-ROUTES (§4.0): the rule-19 exemption shrinks the failing pool and the decision cohort with it. Recall 0.85 HIT; gas_st 0.833 HIT; non-coal off zero HIT. |
| P3′ | L4 total 8–13 GW, lower than L1 by 10–18; L4 economic coal 0–5; L4 recall STAYS ≥ 0.70 | MED | **SPLIT** — lower by 11.4 (HIT), economic coal 0 (HIT), total 6.543 below the band (MISS), recall 0.40 (MISS — D45's original P3 was right) |
| P4′ | restated entering screens 1.04–1.07, at/within a point of the cleared position (a §2.2 correction) | MED | **HIT (first-order)** — ≈ 1.063 / 1.054 vs cleared 1.055 / 1.056; appended to §4.0 as a dated correction |
| P5′ | L2 total 1.45–1.60 (central 1.54) and PASS on the ±10 % band; zero economic events; gas_ct 0.45–0.55; recall 1/1; false ≤ 0.15 PASS; storage 0.000 | MED | **SPLIT** — total 1.457 inside the range (HIT) but FAIL (MISS: scored against 1.711, the 2026-09-02 target, not the 1.488 the range was built on — a records miss, the target file was in the checkout); economic 0 HIT; gas_ct 0.420 (MISS, just under); recall HIT; false 0.176 FAIL (MISS); storage HIT |
| P6′ | L3 total 2.0–4.5, gas_st ≥ 1.5, false FAIL; positions 1.12–1.35 past the zero-cross in ≥ 2 years | MED | **SPLIT** — as D45 P6: gas_st-led HIT, false HIT, total 4.953 (MISS), past the zero-cross in one year then SHORT (MISS) |
| P7′ | L2 positions +5 to +25 pts; requirement 1.5–4 GW low; base year BELOW published (0.95–1.05) | MED | **SPLIT** — +6.5 / +5.2 HIT, 2025 −1.6 MISS; requirement HIT in 2021–2024, MISS in 2025; base year 1.083 (MISS — the base fleet is 1.2 GW light but the requirement is 2.2 GW lighter) |
| P8′ | all T1-H keys HOLD; nyiso-t1h FC-7 FAIL → CAVEAT; NYISO t1f PROMOTE holds; PJM t1f HOLD (I7 + I12); MISO t1f HOLD (I3) | HIGH | **HIT** on determinations (5/5 T1-H HOLD, FC-7 as declared; NYISO t1f PROMOTE caveats []; PJM t1f HOLD on {I7, I12}; MISO t1f HOLD) — the MISO failing set is {I7, I12}, not I3 (graded under P14) |
| P9′ | NYISO: none of (a)/(b)/(c) — do not arm; PJM: L4 retires less, recall holds, no default moves | HIGH | NYISO **HIT**; PJM **SPLIT** (retires less HIT; recall holds MISS; no default moves HIT) |
| P10 | L5 total 6–9 (central 7.5), band FAIL flipping under → over; gas_cc ≥ 4; coal economic 0.0; recall 3–4/6; false ≥ 0.5 | MED | **SPLIT** — total 6.763 HIT (+35 %, sign flipped HIT); gas_cc 4.107 HIT; coal economic 0.534 (MISS); recall 4/6 HIT; false 0.470 (MISS, just under 0.5) |
| P11 | L5 vs d37-control: coal economic 0.791 → 0.0; gas_cc economic UP; oil off zero; total DOWN from 7.566 | MED | **SPLIT** — coal 0.791 → 0.534 (MISS: falls, does not vanish); gas_cc economic 3.978 → 2.632 (MISS: DOWN); oil 0.547 HIT; total 7.566 → 6.763 HIT. The D46 re-routing sign reproduces in direction, not in the coal-to-zero magnitude — the armed lever's higher bar was doing part of D46's coal effect. |
| P12 | NYISO t1f PROMOTE holds; all 14 PASS; I7 ≥ +2 GW; backstop 0 %; CCS read only | — | **HIT** — all 14 PASS, backstop 0.0 %, PROMOTE caveats []; CCS 37 / 18 / 8 rows, cap binding every year (read) |
| P13 | PJM t1f HOLD; I7 FAIL ≥ 3 yrs, plausibly 4; 2030 miss ≥ 8 GW; I12 deeper; backstop > 25.3 %; zero CCS; 15–40 min | MED | **SPLIT** — HOLD HIT; I7 FAIL in **four** years HIT (2027 joins at a 250 MW miss; 2028 / 2029 / 2030 misses 6,226 / 5,800 / 5,647); 2030 miss ≥ 8 GW **MISS** (5,647 — unchanged, because the ladder-bound gas_ct backstop absorbs the dated exits one-for-one: 734 / 1,469 / 2,937 / 3,874 MW in 2027–2030); I12 deeper HIT (−13.5 % in 2028 vs −11.7 %); backstop share > 25.3 % HIT — **43.9 %**, crossing the 30 % bar (CAVEAT → FAIL); zero CCS **MISS** (16 rows / 2,833 MW in 2028, 3 / 752 in 2029 on the corrected constants — thinned from the preserved record's cap-bound 26 / 9 / 10 rows at 900 / 25; the reconciliation with D41 §4.3 is routed); wall 28.2 min HIT |
| P14 | MISO t1f HOLD; I3 grows; I7 joins ≥ 1 yr; I12 out ≥ 1 yr; backstop off zero; zero CCS; 20–45 min | MED | **SPLIT** — HOLD HIT; I7 joins **four** years (2026–2029, misses 11.4 / 12.1 / 12.6 / 5.7 GW) HIT; I12 out of band in four years (−8.1 / −8.6 / −8.9 / −3.6 %) HIT; backstop off zero HIT — **33.6 %**, FAIL (2,049 / 4,049 / 10,000 MW gas_ct in 2028–2030, storage 4,000 MW/yr from 2027); I3 grows **MISS** (I3 now PASSES; the failing set is {I7, I12}); zero CCS **MISS** (12 / 18 rows, 2,985 / 1,646 MW in 2028 / 2029); wall 20–45 min **MISS** (65.2 min; 2030 alone 28 min as the 10 GW backstop lands). The base-year accredited firm 140.3 → 118.1 GW is not the channel's (the preserved record predates D31's 0.8546 accounting ratio; 140,263 × 0.8546 = 119,869) — the delta is multi-axis and unattributed |
| P15 | no leg > 2× price; neither F2 nor F3 near the 2 h STOP; 8/8 keys | HIGH | **HIT** — 8/8 keys; PJM 28.2 min (price 20–40), MISO 65.2 min (1.5× its 45-min price ceiling, under the 2× kill line, and 0.54× the 2 h STOP); L1 23.2 / L4 20.5 / L2 12.2 / L3 11.8 / L5 6.8 / F1 16.0 min. No leg killed |

**Tally, D45-R (P1′–P15, 16 gradable items incl. P9′ × 2): 6 HITs (P1′, P4′, P8′, P9′-NYISO, P12, P15), 9 SPLITs (P3′, P5′, P6′, P7′, P9′-PJM, P10, P11, P13, P14), 1 MISS (P2′). D45's untested half (P3, P5, P6, P7, P8, P9): 3 HITs, 3 SPLITs.** Cache keys 8/8.

**The one clean miss is the one worth keeping.** P2′ predicted the PJM dates channel would ADD exits on top of a re-filled cap-bound cohort; it re-routes them out of the cohort instead, because the rule-19 exemption removes the dated plants from the failing pool *before* the admission cap sizes the decision — D46's MISO reading, which the pre-declaration had in hand and reasoned past. **The recurring split is the same lesson from the other side:** every "the bar moves X" prediction (P5′'s PASS on a 1.488 target that had been rebuilt to 1.711 in the checkout; P13's 8 GW 2030 miss against a ladder that absorbs dated exits one-for-one; P14's I3) was built from the preserved record rather than from the artifacts at HEAD. Both are process misses — a committed-artifact query before the solve would have caught each — not model surprises. **Three predictions were wrong in the same direction on CCS**: PJM and MISO both clear retrofits at carbon = 0 on the corrected constants (thinned, not zeroed), against a MED-confidence zero built on D41 §4.3's screen-grain reading; D46 §4.5 had already recorded the same miss at ERCOT. Routed, not inferred.

## 8. Sources fetched in-session (sha256), governance attestation

*Filled 2026-09-04 by capx D45-R. D45's session fetched the six BRA reports and the NYSRC
appendices but died before recording their hashes; every document below was RE-FETCHED
by this lane from the publisher (the primary URL, redirects followed) and hashed, so the
published record §2.1 / §5.2 rest on is reproducible from a checkout. Where the exact
document type D45 cited does not exist for a year, the closest publisher document is
listed and marked SUBSTITUTE — none of those three is load-bearing for any number in
this finding (the pre-2024 NYCA curve vintages are read from the committed
`demand-curve/nyiso/nyiso.csv` rows). Transcriptions re-verified from the fetched
PDFs this session: NYSRC Table D.2 (every 2021–2025 row of §1.1 / §5.2.1, page 86 of
the appendices) and the Potomac SOM "UCAP Margin (Summer)" NYCA rows for 2023 (4.3 %)
and 2024 (5.8 %); the 2025 SOM's extracted table row reads 5.8 / 16.4 / 5.7 / 11.7 %,
identical to the 2024 row, and is carried as D45 transcribed it with that flag.*

| label | document | sha256 | bytes |
|---|---|---|---:|
| `pjm-bra-report-2021-2022` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2021-2022/2021-2022-base-residual-auction-report.ashx | `800e4b3a86058ad80fc9be55e530c0e78f931471cd23ebaa2c3cf8514c8720f4` | 492,361 |
| `pjm-bra-report-2022-2023` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2022-2023/2022-2023-base-residual-auction-report.ashx | `ca9d51b9246e988e24d0beb3bae23d201fac6ecf7116ddad8575dc4e1e28b69a` | 844,297 |
| `pjm-bra-report-2023-2024` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2023-2024/2023-2024-base-residual-auction-report.ashx | `ef82660e4204c4148d7402ff80ff1ac48ee830c117b30f4c336b6b54e1c0f51f` | 585,093 |
| `pjm-bra-report-2024-2025` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2024-2025/2024-2025-base-residual-auction-report.ashx | `00ddf7c9c8fcbda69d251df76db00720a633156afd27454e8fcf2c05a1807816` | 762,397 |
| `pjm-bra-report-2025-2026` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2025-2026/2025-2026-base-residual-auction-report.pdf | `6d47fb09d2052b102279ecf0e8748a4186a93e37d11bdf5b1bbf02d0db1b8350` | 1,834,375 |
| `pjm-bra-report-2026-2027` | https://www.pjm.com/-/media/DotCom/markets-ops/rpm/rpm-auction-info/2026-2027/2026-2027-bra-report.pdf | `15effa7b903d026468cdea0b7eb2654eeb1f70d02a436c92289bff062fd257be` | 1,192,786 |
| `nysrc-2026-27-irm-appendices` | https://www.nysrc.org/wp-content/uploads/2025/12/2026-IRM-Study-Technical-Report-Appendices.pdf | `714aeeb9156795108147982f93cf90f885ed110835e0a6f2fa257f809da419d5` | 3,659,026 |
| `nysrc-2026-27-irm-report` | https://www.nysrc.org/wp-content/uploads/2025/12/2026-IRM-Study-Technical-Report.pdf | `520f4ed8f4f362325f52ad5435ad91d3a6c7812a0046e2278ed4e8f0f25db75d` | 1,262,632 |
| `nysrc-2025-26-irm-report` | https://www.nysrc.org/wp-content/uploads/2024/12/2025-IRM-Study-Technical-Report_Final_12062024_clean.pdf | `d9c2f3d4cd2b8f250b8d31b7a410d6aca7e17ea1ecb9e8fca2cfb2dba30c96af` | 730,864 |
| `potomac-nyiso-som-2021` | https://www.potomaceconomics.com/wp-content/uploads/2022/05/NYISO-2021-SOM-Full-Report_5-11-2022-final.pdf | `13e05381b37d315ee9aa2ab463d62e0f298e2e2840c949f3461f31dfe5b9c4ad` | 6,201,641 |
| `potomac-nyiso-som-2022` | https://www.potomaceconomics.com/wp-content/uploads/2023/05/NYISO-2022-SOM-Full-Report__5-16-2023-final.pdf | `48b6dcad96b049a71188cfb2f493f75c7afaef26884cf7b61513c46fd0e645f1` | 10,643,331 |
| `potomac-nyiso-som-2023` | https://www.potomaceconomics.com/wp-content/uploads/2024/05/NYISO-2023-SOM-Full-Report__5-13-2024-Final.pdf | `e240893a62c6f49a1d44fbe090c502501972d8db6333d609f49b3905d0f25167` | 7,091,626 |
| `potomac-nyiso-som-2024` | https://www.potomaceconomics.com/wp-content/uploads/2025/05/NYISO-2024-SOM-Full-Report_5-14-2025-final.pdf | `d2b27a93269dbf4d54ffad9ba3d4b721784b7b9c75ad80780c12aad94d3b3a04` | 6,454,531 |
| `potomac-nyiso-som-2025` | https://www.potomaceconomics.com/wp-content/uploads/2026/05/NYISO-2025-SOM-Report__5-19-2026-final.pdf | `80c27d0b75e4c0ecb3c1ad69b3b6e2bea6797f1c0b4c9abce37f6fefaf4e218c` | 14,425,051 |
| `nyiso-lcr-2022` | https://www.nyiso.com/documents/20142/27428389/LCR2022-Report.pdf/ | `252487f16419b6b314010a3801198e75e81a308809df20fc1843d21cc405647e` | 245,036 |
| `nyiso-lcr-2023` | https://www.nyiso.com/documents/20142/35886565/2023-LCR-Report.pdf | `d8c2489694c00af17f41f0b5a283beff3320affa8a01ce549d255ac3953f92aa` | 237,570 |
| `nyiso-lcr-2024-25` | https://www.nyiso.com/documents/20142/42519933/2024-2025-LCR-Report.pdf/04ee02a1-3a67-f4df-ff8a-0c1a5c9cf7da | `6ca1017f3c0a5f5747df0d7910c9123c59553cce0ee5252b6c4d40fa0e78ba46` | 226,801 |
| `nyiso-lcr-2025-26` | https://www.nyiso.com/documents/20142/49410485/2025-2026-LCR-Report-Clean.pdf/c8c65acd-0979-a67a-9fa8-f322536fc156 | `97c357287863e9e98305d0985244e252114a794df08f939fe9d153e0d2257039` | 393,113 |
| `nyiso-lcr-2025-26-results-icapwg` | https://www.nyiso.com/documents/20142/48947506/Final%202025-2026%20LCR%20Results%20-%2001072025%20ICAPWG_FINAL.pdf/0dcb9f35-3aaf-7858-23cc-51eb67039d27 | `1c4f5ab9ad839fd6e75dea6f22ee57ed7a5bfe87c91573f01f0ed6106a83b7a0` | 417,884 |
| `nyiso-dc-params-2025-26` | https://www.nyiso.com/documents/20142/50430248/Demand-Curve-Parameters-2025-2026.pdf/d7122e6a-eae1-36eb-8670-ab6f18a78085?t=1742221315568 | `175492d0037ce8d6c3f99de59746505818647df5a67448af20e51cd399b7280c` | 87,064 |
| `nyiso-dc-params-2024-25` | https://www.nyiso.com/documents/20142/40286656/Demand-Curve-Parameters-CY-2024-2025.pdf/5c2430ae-9f28-d5a3-cf0c-364142365d4c?t=1699912152978 | `28677e167f2a90bb667bcab02cdf858115131f0439f7ec9fa24ebb508c552e27` | 164,357 |
| `nyiso-dc-params-2023-24` **SUBSTITUTE** | https://www.nyiso.com/documents/20142/34388803/2023-2024%20Annual%20Update%2011142022%20ICAPWG_Final.pdf/50cfedae-cd3d-95c3-c93a-e736a70094e2 | `89d6ce92ba9e009814e9fba79e07bc4b120f47e407ef69ecec773340a9db76f5` | 1,008,087 |
| `nyiso-dc-params-2022-23` **SUBSTITUTE** | https://www.nyiso.com/documents/20142/26269980/2022-2023%20Annual%20Update%2011182021%20ICAPWG_final.pdf/3dbd9c0d-0b6e-6c65-e454-5ce520bc07d2 | `f68b7e9ad5be2047ba94d2023790380e5d3fbdfe0b5eedfec9e0fbca87d635ed` | 1,818,900 |
| `nyiso-dc-params-2021-22` **SUBSTITUTE** | https://www.nyiso.com/documents/20142/15473217/2021-2022%20ICAP%20Demand%20Curve%20Supp%20Information.pdf/4f3dfe5a-68a2-7ae1-8333-e69ff1aaf3ed | `2f0ebb9443cbd4c638b820d51c6aa0c3e2b3c2c5d8f0ef4d2555f7edae56edc7` | 671,221 |

Committed rows the instruments read, unchanged by this lane:
`data/raw/capacity-market/demand-curve/{pjm,nyiso}/*.csv`,
`data/raw/capacity-market/auction-price/{pjm,nyiso}/*.csv`,
`data/raw/capacity-deliverability/nyiso/nyiso.csv` (LCR / import-limit rows, each row
citing its LCR / Bulk Power Transmission Capability report and page),
`data/raw/_validation-source/capacity_actuals_{pjm,nyiso,neiso}.csv` (scoring targets;
NYISO's rebuilt 2026-09-02, PR #4615).

### Governance attestation (D45-R)

- **Scope.** Eight solves (five T1-H, three T1-F), every one pre-declared with its cache
  key, keeper, posture and predictions BEFORE launch and every realized key matching
  (§7). **NOTHING ARMS**: no `ScenarioConfig` field added or moved (rule 28 not
  triggered; no matrix row); no parameter value changed (rules 21/23); no keeper /
  shard / marker; the backcast namespace untouched; `capacity_market_clearing_by_iso`
  ships unchanged with NYISO absent; `neiso_net_icr_requirement` ships `False`.
- **Rule 22.** T1-H solves {2021, 2023, 2024, 2025} with 2022 bridged (never solved,
  never read), scored 2023–2025 only; T1-F 2026–2030 on forward drivers with no
  measured H1-2026 actual read; the holdout freeze untouched; no marker spent.
- **Rules 13/14.** The published NYCA / RPM quantities and the SOM margins are
  validation observables; nothing in any leg targets them; every identified repair
  names a published source and states its rule-14 sign (§2.3, §5.2.4).
- **Rule 12.** Years sequential in every invocation; L2 ∥ L3 and L5 ∥ F1 were the only
  concurrent pairs (≤ 3.5 GB each); PJM and MISO solved solo (9.6–9.9 GB peak).
- **Rule 25.** Four ISOs, four readings; no parameter or verdict transferred.
- **Rule 27.** Every file ≥ 300 lines (`register_forecast_run.py`, `ff-verdicts.json`,
  `program-status.json`, the matrix shards, each `run_config.json`, this finding) was
  edited locally and its remote blob fetched back and hash-compared after every push.
- **Rule 15.** Every leg registered through `register_forecast_run.py` in the session
  that produced it, preserve-then-overwrite, on the FORECAST namespace only.
- **Environment cost, stated.** A cold container: `uv sync` + `regenerate_clean.py`
  (54 datatypes, ~75 min here — the `emissions` datatype alone ~30 min) before the
  first solve; recorded, not absorbed.

## 9. Close-out

**This was the once-only clearing-half charter (D6 + D28 R3), and it is closed.** Both
ISOs' clearing-half questions are adjudicated on record: PJM's $0 is a basis artifact
sitting at the market's cleared quantity once the auctions' own UCAP design and the
filed dates are honored (§2, §4), and NYISO's latent curve-ON flip is a requirement-basis
and locality artifact, not a curve defect (§5). Neither adjudication moves a default, and
neither can be re-read into an arming without the repairs named above landing first.
**Successor work is per-ISO repair lanes** — PJM §2.3 items 1–3, NYISO §5.2.4 items 1–3 —
each with a published source, a stated rule-14 sign and zero free parameters, and each
re-tested against the SAME pre-stated conditions this finding graded. **The
mechanism-class question does not reopen without new evidence**: a future lane that
wants to re-litigate "should the published curve be consulted / should the clearing
half be a supply-stack intersection" must bring a measurement this finding does not
already hold, not a re-run of these legs. The director re-releases nothing behind this
line. Records: the six bare keys (`pjm-t1h`, `nyiso-t1h`, `neiso-t1h`, `nyiso-t1f`,
`pjm-t1f`, `miso-t1f`) are current at HEAD `334be8c2` with every prior preserved at
`-pre-d45r`; the two probe legs registered suffixed; both pre-declarations graded at
full magnitude in §7; the board and the four matrix shards refreshed; the §0ac.7 stale
set CLOSED for every key except CAISO's (the CAISO lane's, by the ledger's own standing
clause).
