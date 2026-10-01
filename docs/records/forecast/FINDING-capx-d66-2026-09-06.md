# FINDING — capx D66: the PJM supply census, reconciled against PJM's own BRA record — the 2024/25–2025/26 residual D61 routed here is NOT a one-sided missing-supply object: it is the small net of a REQUIREMENT leg (the model's peak forecast, 78 % / 67 % of the gap) against a supply census that is 9.3 / 3.1 GW BELOW PJM's own RTO-wide offered supply, and the largest single closable item found is that the model applies PJM's **2026/27-vintage** VRE ELCC ratings to delivery years whose published accreditation regime was the Dec-2021 class-average one (wind 41 % vs the published 16 %, solar 10.64 % vs the published 36–54 %) — the VRE half of the repair D48 made for thermal

**Lane:** capx D66 (director r#44), the CENSUS successor D61 §4 card (a) named. Branch
`claude/capx-d66-pjm-supply-census-wet2pd`. **ZERO LP — no solve of any kind was run, and none is
authorized in this lane.** Every model number is read from committed artifacts; every market number
is a published observable (rule 13). Instrument and output:
`docs/handoffs/d66/supply-census-2026-09-06.{py,json}`. **Nothing built, nothing armed, no field, no
default, no matrix cell, no board byte, no keeper, no bundle** (§5).

DATA PROFILE: `pjm` (full clone; `data/clean` is EMPTY in this session and was deliberately NOT
rebuilt — §3.4 records the one model quantity that costs).

---

## 0. The answer in one paragraph

The census question as D61 posed it — "how much and what kind of capacity does the model bring to
the auction" — has a two-sided answer, and the side D61 could not see is the larger one. Put the
model and PJM on ONE definition of position (§1.2: the published position D57/D61 quote is
`cleared UCAP ÷ (RTO Reliability Requirement adjusted for FRR + the EE add-back)`, reproduced to
four decimals in all four years), and the gap decomposes EXACTLY and additively into a supply leg
and a requirement leg (§3.1). On the like-for-like whole-RTO basis — which is the right one,
because the model runs the entire RTO while RPM is net of ~32 GW of FRR — **2024/25's +2.19 pt gap
is +2,848 MW of REQUIREMENT (78 %) and +802 MW of supply (22 %); 2025/26's +4.38 pt is +4,391 MW
requirement (67 %) and +2,125 MW supply (33 %)**. The requirement leg is *entirely* the peak: the
model's screen peak is 2,481 MW (1.6 %) and 4,636 MW (3.0 %) above the peak implied by PJM's own
published Reliability Requirement ÷ FPR, and `FPR × Δpeak` reproduces `R_model − R_published` to the
MW with zero residual. The supply leg's small NET conceals large offsetting rows (§3.2): the model
is short **6,870 MW of gas** and **3,748 MW of solar** while over-counting **2,767 MW of wind**,
**1,973 MW of DR** and **4,548 MW** of the storage/hydro/biomass block. Measured against PJM's
*offered* RTO-wide supply rather than its *cleared* — the honest census comparator, since the model
clears essentially everything it brings — **the model's census is 9,332 MW short in 2024/25 and
3,147 MW short in 2025/26**, and the cleared comparison flatters it only because PJM left 8,530 MW
uncleared where the model leaves 406. Of the named buckets, exactly one is a clean, closable
representation gap whose data is **already in the repo**: PJM's ELCC regime broke at the 2025/26
CIFP reform, D48 vintaged the THERMAL side of that break and the VRE side was never vintaged, so
every delivery year 2022/23–2025/26 is accredited at the 2026/27 ratings — wind at 0.41 against the
published 2024/25 rating of **0.16**, solar at 0.1064 against the published **0.36 (fixed) / 0.54
(tracking)** (§4.5). Correcting it moves the census **DOWN** by 0.6–1.4 GW (§4.5), i.e. it widens
the residual — rule 14's signal that the estimate was compensating, not that the accurate input is
wrong. **Nothing here is proposed as a parameter and nothing arms; §8 names two chartered repairs
and their costs, and states which bucket is large enough to explain D57's remaining position error
(the peak, not the census).**

---

## 1. The two sides, put on one definition

### 1.1 Instrument check — the 2022/23 row D62's screen recorded (charter step 1)

| quantity | D62-recorded | D66 measured from `evolution_2022.json` | |
|---|---:|---:|---|
| `requirement_mw` | 155,048 | **155,047.538** | ✔ |
| `price_takers_mw` (`Q_0`) | 30,578 | **30,577.888** | ✔ |
| `census_position` | 1.17019 | **1.17019** | ✔ |

**PASS** on all three. The reconstruction is the model's, not a re-derivation: `census_mw` =
`offered_mw` + `price_takers_mw` = 150,857.184 + 30,577.888 = 181,435.072 exactly, and
`cleared_mw` = `Q_0` + the cleared stack. The charter's STOP is not triggered.

### 1.2 The published position's definition, recovered (and it is exact)

D57/D61 quote published cleared positions 1.0510 / 1.0552 / 1.0555 / 1.0049 without stating the
denominator. It is `reliability_requirement_frr_adj + ee_addback` — both already in
`data/raw/capacity-market/demand-curve/pjm/pjm.csv`:

| DY | RR (RTO) | RR adj. FRR | EE add-back | **R_published** | cleared (Table 1/2 RTO) | position | D57's |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022/23 | 163,268.9 | 132,256.6 | 5,205.0 | 137,461.6 | 144,477.3 | **1.05104** | 1.0510 |
| 2023/24 | 163,166.2 | 131,820.4 | 5,471.1 | 137,291.5 | 144,870.6 | **1.05520** | 1.0552 |
| 2024/25 | 164,107.6 | 132,055.7 | 7,667.2 | 139,722.9 | 147,478.9 | **1.05551** | 1.0555 |
| 2025/26 | 144,450.0 | 133,563.6 | 1,459.8 | 135,023.4 | 135,684.0 | **1.00489** | 1.0049 |

Four decimals in four years. **This is a BASIS-MISMATCHED comparator, and that is why it must be
stated rather than used blind:** the model runs the whole RTO (all load, all resources, no FRR
carve-out), while RPM is net of an FRR block that is 31.0 / 31.3 / 32.1 / 10.9 GW across these
years. Both the model's requirement and its census are whole-RTO, so the like-for-like published
comparator is **RPM + committed FRR** (2024/25 BRA Report Table 9, p.14; the 2025/26 column from
the 2027/28 BRA Report Table 6, p.11, because the 2025/26 report's own copy is an image). Frame A
below is D57/D61's; **Frame B is the one this finding reads**. They land within 0.16–0.50 pt of
each other because the FRR legs largely cancel — the robustness check that says the conclusion does
not turn on the frame.

### 1.3 Published sources, with verified identity

Fetched through the session proxy 2026-09-06; **sha256 matches the identities already recorded in
`data/raw/capacity-market/auction-supply/pjm/README.md` byte-for-byte** for all four reports that
README covers. Payloads are NOT committed — the corpus posture that README already sets for PJM
publication PDFs.

| report | sha256 | used for |
|---|---|---|
| 2022/2023 BRA Report | `ca9d51b9…1e28b69a` | context |
| 2023/2024 BRA Report | `ef82660e…6b54e1c0f51f` | context |
| 2024/2025 BRA Report | `00ddf7c9…2fc05a1807816` | **Tables 5, 6, 7, 9, 11, 12** — the 2022/23–2024/25 columns |
| 2025/2026 BRA Report | `6d47fb09…2db1b8350` | narrative + Table 7 imports (its Tables 4–6 are IMAGES) |
| 2027/2028 BRA Report | `d2280c61…5890219c5f570` | **Table 5** (RTO trend) + **Table 6** — the 2025/26 column |

Restatements between vintages are recorded, not reconciled (instrument `restatements` block): the
2024/25 rows read from both the 2024/25 and 2027/28 reports agree within **≤ 15 MW** per row
(Gas cleared 83,243 vs 83,258; grand total 172,961 vs 172,951; DR cleared 7,985.2 vs 7,992.7 —
the 7.5 MW the auction-supply README already records).

### 1.4 The four-year table (Frame B, whole-RTO, UCAP)

| DY | model census | model `R` | model pos | pub **offered** | pub **cleared** | pub `R` (=RR) | pub pos | **gap** | census vs pub OFFERED |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022/23 | 181,435 | 155,048 | 1.1702 | 193,551 | 171,263 | 163,269 | 1.0490 | −12.12 pt | **−12,116** |
| 2023/24 | 175,318 | 161,117 | 1.0881 | 182,875 | 171,605 | 163,166 | 1.0517 | −3.64 pt | **−7,557** |
| **2024/25** | **172,159** | **166,810** | **1.0321** | **181,491** | **172,961** | **164,108** | **1.0539** | **+2.19 pt** | **−9,332** |
| **2025/26** | **143,758** | **148,798** | **0.9661** | **146,905** | **145,883** | **144,450** | **1.0099** | **+4.38 pt** | **−3,147** |

Two readings the D61 frame could not produce:

1. **The model's census is BELOW PJM's own offered RTO-wide supply in EVERY year** — by 12.1 / 7.6
   / 9.3 / 3.1 GW. The 2024/25 cleared comparison reads only −802 MW because PJM left **8,530 MW
   uncleared** where the model left **406**. The census shortfall is real and it is roughly an
   order of magnitude larger than the residual it produces.
2. **2022/23 and 2023/24 read the gap with the opposite sign** (model position 12.1 / 3.6 pts
   ABOVE published) because the model's requirement is *below* PJM's there — the 2022 bridge
   year's screen peak is 7.6 GW under PJM's implied peak (D57 §3.2's object). The sign flip across
   the window is itself the tell that the requirement leg, not the census, is driving.

---

## 2. Composition, by resource type

Model side: the `capacity_clearing.offer_stack` accredited MW by fuel (exact — every screened unit,
cleared or not) plus the price-taker block `Q_0`. Published side: Table 9 / Table 6, offered UCAP.

| bucket | 2024/25 model | 2024/25 pub **offered** | Δ | 2025/26 model | 2025/26 pub **offered** | Δ |
|---|---:|---:|---:|---:|---:|---:|
| Coal | 32,411.0 | 35,114 | −2,703 | 28,874.2 | 30,081 | −1,207 |
| Gas (CC+CT+ST) | 76,373.0 | 85,469 | **−9,096** | 56,080.7 | 66,354 | **−10,273** |
| Nuclear | 31,691.9 | 31,835 | −143 | 31,038.5 | 30,549 | +490 |
| Oil (distillate + residual) | 3,722.8 | 5,269 | −1,546 | 3,764.2 | 2,986 | +778 |
| *thermal + nuclear subtotal* | *144,198.9* | *157,687* | *−13,488* | *119,757.6* | *129,970* | *−10,212* |
| Non-thermal (`Q_0`) | 27,959.7 | 23,803 | **+4,157** | 24,000.2 | 16,935 | **+7,065** |
| **TOTAL** | **172,158.6** | **181,491** | **−9,332** | **143,757.8** | **146,905** | **−3,147** |

`Q_0`'s interior, model side — five components pinned exactly from committed artifacts, one not:

| `Q_0` component | source | 2024/25 | 2025/26 |
|---|---|---:|---:|
| Demand response | `DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO["PJM"]` (D48, armed in arm A) | 10,146.4 | 6,084.8 |
| Firm imports | `ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]` | 1,281.7 | 1,281.7 |
| Storage (firm) | D45-R control ledger `storage_firm_mw` | 3,801.5 | 3,801.5 |
| Wind | pool × `renewable_credit_applied["wind"]` = 10,153.9 / 11,653.9 × 0.41 | 4,163.1 | 4,778.1 |
| Solar | pool × `renewable_credit_applied["solar"]` = 4,549.8 / 6,990.4 × 0.1064 | 484.1 | 743.8 |
| **UNPINNED residual** — hydro + biomass + screen-exempt thermal | **not decomposable from committed artifacts** | **8,082.9** | **7,310.3** |
| `Q_0` (ledger) | | **27,959.7** | **24,000.2** |

VRE/storage pools come from the **D45-R control** bundle's ledgers (`c6091bd5b62bbc3f`), which
record `wind_cap_mw` / `solar_cap_mw` / `storage_firm_mw` that the D57 arm-A ledgers dropped. The
control is the same recipe up to the three D48/clearing gates, and those gates move the **thermal**
accreditation basis and the DR term only (`accredited_firm_capacity_mw` docstring) — never the VRE
or storage pools. The pool entering screen year *Y* is the 2021 base plus every addition decided in
2021…*Y*−1, from the arm-A ledgers' own `renewable_additions`.

---

## 3. The additive decomposition (charter step 3)

### 3.1 The identity

With `C` supply, `R` requirement, `m` model, `p` published, the position gap in MW at the model's
own requirement splits **exactly**:

    (C_p/R_p − C_m/R_m) · R_m  =  (C_p − C_m)  +  C_p · (R_m − R_p)/R_p
                                   └─ SUPPLY ─┘    └──── REQUIREMENT ────┘

| DY | gap | = supply leg | + requirement leg | requirement share |
|---|---:|---:|---:|---:|
| **2024/25** | +2.189 pt = **+3,651 MW** | **+802** | **+2,848** | **78 %** |
| **2025/26** | +4.379 pt = **+6,516 MW** | **+2,125** | **+4,391** | **67 %** |

Frame A (D57/D61's RPM-only comparator) gives the same net through two enormous offsetting legs —
2024/25 supply −24,680 / requirement +28,591; 2025/26 −8,074 / +13,842 — because the FRR block sits
on both sides. **That is the artifact D61's "3.9 GW of accredited supply the model does not count
(or requirement it overstates)" was reading**: the parenthetical was the operative half, and on the
basis-matched frame it is 78 % of the answer.

### 3.2 Rows that sum to the gap — 2024/25 (Frame B, MW at `R_m`)

| # | bucket | model | published (cleared) | **row** |
|---|---|---:|---:|---:|
| **REQUIREMENT LEG — exact +2,848.2** | | | | |
| R1 | Peak forecast × FPR | screen peak 153,121.0 | PJM implied peak 150,640.4 | **+2,848.2** |
| | *requirement unattributed* | | | **0.0** |
| **SUPPLY LEG — exact +802.4** | | | | |
| S1 | Gas (CC+CT+ST) | 76,373.0 | 83,243 | **+6,870.0** |
| S2 | Solar | 484.1 | 4,232 | **+3,747.9** |
| S3 | Oil (distillate + residual) | 3,722.8 | 4,916 | +1,193.2 |
| S4 | Aggregate Resource | 0.0 | 503 | +503.0 |
| S5 | Nuclear | 31,691.9 | 31,629 | −62.9 |
| S6 | Coal | 32,411.0 | 31,532 | −879.0 |
| S7 | Demand response | 10,146.4 | 8,173 | −1,973.4 |
| S8 | Firm imports (classification adjustment) | 1,281.7 | 0 | −1,281.7 |
| S9 | Wind | 4,163.1 | 1,396 | −2,767.1 |
| S10 | **Storage + hydro + biomass + screen-exempt thermal** | 11,884.4 | 7,336 | **−4,548.4** |
| | *supply unattributed* | | | **+1.0** |
| | **TOTAL** | | | **+3,650.6** |

### 3.3 Same, 2025/26

| # | bucket | model | published (cleared) | **row** |
|---|---|---:|---:|---:|
| R1 | Peak forecast × FPR | 158,633.4 | 153,997.9 | **+4,391.2** |
| S1 | Gas (CC+CT+ST) | 56,080.7 | 66,354 | **+10,273.3** |
| S2 | Solar | 743.8 | 1,337 | +593.2 |
| S3 | Aggregate Resource | 0.0 | 273 | +273.0 |
| S4 | Demand response | 6,084.8 | 6,342 | +257.2 |
| S5 | Nuclear | 31,038.5 | 30,549 | −489.5 |
| S6 | Oil | 3,764.2 | 2,986 | −778.2 |
| S7 | Coal | 28,874.2 | 30,081 | +1,206.8 |
| S8 | Firm imports (classification adjustment) | 1,281.7 | 0 | −1,281.7 |
| S9 | Wind | 4,778.1 | 1,676 | −3,102.1 |
| S10 | **Storage + hydro + biomass + screen-exempt thermal** | 11,111.8 | 6,286 | **−4,825.8** |
| | *supply unattributed* | | | **−1.0** |
| | **TOTAL** | | | **+6,516.4** |

**The unattributed rows are ±1.0 MW**, the rounding of PJM's integer-MW table rows. Nothing is
distributed across the named buckets.

### 3.4 The one model quantity this lane could not decompose, stated

Row **S10**'s model side (11,884.4 / 11,111.8 MW) is `storage_firm` (3,801.5, exact) plus the
**unpinned** `Q_0` remainder (8,082.9 / 7,310.3). That remainder is hydro + biomass + any
screen-exempt thermal, and it is not separable from committed artifacts: the hydro pool resolves
through `modelled_hydro_nameplate_mw` → `load_hydro_budget` → `data/clean`, which is **gitignored
and empty in this session**. Its year-to-year swing (10,334.5 / 16,528.0 / 8,082.9 / 7,310.3 across
2022–2025) is far larger than hydro or biomass can move, so it demonstrably carries screen-exempt
thermal — in 2023 the whole 4,136.5 MW oil fleet and ~4 GW of gas-CC sit off the stack (the 2023
stack carries 907 offers against 2022's 1,370). **This is reported as its own row at full magnitude
and is NOT attributed.** Cost to close it: a `fleet_only` / `data/clean` rebuild, zero LP, ~90 s of
compute plus the clean-data build — named in §8 as part of the census repair, not done here.

---

## 4. Per-bucket disposition (charter step 4)

Classification: **(i)** a representation gap this model could close; **(ii)** a deliberate scope
exclusion; **(iii)** already handled, mis-attributed by the comparison.

### 4.1 R1 — the peak forecast (+2,848 / +4,391 MW; the largest bucket) → **(i), but it is a LOAD object, not a capacity-market one**

`R_m − R_p` is reproduced to the MW by `FPR × (screen peak − PJM implied peak)` with **zero
residual** in both years: 1.0894 × 2,480.6 = 2,702.4 and 0.9380 × 4,635.5 = 4,348.1. The model uses
PJM's own published FPR; the entire difference is the peak operand. Two honest halves: PJM's
Reliability Requirement is built on a **forecast** peak set ~17 months ahead (both BRAs ran on the
compressed schedule), while the model's is its own simulated weather-year peak — so part of this is
definitional, not error. What is *not* definitional is that the model's peak runs 1.6 % / 3.0 % hot
in these two years, and it is the same operand the LP's demand uses, so it cannot be adjusted in the
requirement alone without decoupling requirement from dispatch (rule 19). **The closable form is
different: read PJM's own published Reliability Requirement as the hindcast requirement instead of
reconstructing it from the model's peak.** It is rule-13 admissible (a published planning parameter
that regenerates for a forward year from PJM's load forecast + IRM), rule-14 preferred (measured
over reconstructed), and already on disk in `demand-curve/pjm/pjm.csv`. §8 card A.

### 4.2 S1 — gas, +6,870 / +10,273 MW → **(iii) mostly already handled, and mis-attributed here**

In the 2022 screen — before the model's own exits bite — the gas gap is only **−2,531 MW**. By 2024
it is −9,096. The 6.6 GW of growth is the model's own cumulative gas-steam over-exit (D57 §3.5:
economic `gas_st` 9.465 GW against 2.702 GW actual, every steam unit uncleared at a zero-E&AS full
bar in every year). **This bucket is therefore not an input census gap; it is the D57/D61 steam
over-exit re-entering the census one year later**, and its object is D61 §4 card (c), the below-cap
offer convention for regulated/self-supplied steam. The genuine input residue is the ~2.5 GW visible
in 2022. Counting it as a census repair would double-count a mechanism already chartered (rule 19).

### 4.3 S10 — storage + hydro + biomass + exempt thermal, −4,548 / −4,826 MW → **(i), but not measurable here**

The model credits 11.9 / 11.1 GW where PJM's Water + Battery/Hybrid + Other is 7.3 / 6.3 GW. Note
the classification: PJM books pumped storage under **Water**, and the model splits it between its
`storage` pool (3,801.5 MW firm, from 5,357.6 MW of power at an implied 0.710) and its hydro pool.
PJM's published 2024/25 storage ratings are **82 % (4-hr) / 97 % (6-hr) / 100 % (8-hr and 10-hr)**,
so the model's 0.710 is if anything LOW — which means the over-count sits in the hydro/biomass/exempt
part, exactly the part §3.4 cannot separate. **Disposition (i) with a measurement precondition.**

### 4.4 S7 — demand response, −1,973 / +257 MW → **(ii) deliberate, correctly attributed**

The model carries PJM's **offered** DR (10,146.4 / 6,084.8 UCAP), by D48's design: the offered rows
are "the market's recurring qualified-DR supply census, the analogue of the model's installed-fleet
census", and "the CLEARED rows are validation observables … never a target"
(`auction-supply/pjm/README.md`). PJM cleared 8,173 / 6,342. The −1,973 MW in 2024/25 is the DR that
offered and did not clear — a market outcome the model should not reproduce on the supply side. **No
repair.** The FRR-committed DR the RPM-only series excludes (264.4 MW in 2026/27) is the same
README's documented conservatism.

### 4.5 S9 + S2 — wind −2,767 / −3,102 and solar +3,748 / +593 MW → **(i), the one clean closable gap, and its data is already in the repo**

The model applies `renewable_credit_applied = {wind: 0.41, solar: 0.1064}` in **every** delivery
year. Those are `RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]`, and the registry states their provenance
plainly: *"PJM 2026/27 + 2027/28 BRA final ELCC class ratings"*. PJM's accreditation regime **broke**
at the 2025/26 CIFP reform, and its pre-reform published class-average ratings are already on disk
in `data/raw/capacity-market/elcc/pjm/pjm.csv` under the vintage label *"2024/2025 BRA (Dec 2021
ELCC Report, predecessor/narrower methodology)"*:

| class | model credit, all years | PJM published, **2024/25 BRA** | PJM published, 2026/27 BRA | ratio |
|---|---:|---:|---:|---:|
| Onshore wind | **0.41** | **0.16** | 0.41 | model **2.6× high** |
| Solar (fixed) | **0.1064** | **0.36** | 0.08 | model **3.4× low** |
| Solar (tracking) | (same 0.1064) | **0.54** | 0.11 | model **5.1× low** |

**This is precisely the defect D48 repaired for the THERMAL classes and left unrepaired for VRE.**
`pjm_accreditation_design_vintage` resolves the thermal basis per delivery year — "UCAP before PJM's
2025/26 reform, the registry basis after" — and its docstring scopes it to thermal; the VRE curves
carry no vintage axis at all. Cross-check that the break is real and not a mis-reading: PJM's own
2027/28 report says the 2025/26+ figures "were significantly impacted by the marginal ELCC
accreditation changes [so] it is difficult to simply compare delivery year over delivery year",
and across the break Table 9's wind offered RISES 1,396 → 2,618 while solar FALLS 4,234 → 1,337 —
both directions consistent with the ratings table above, and neither explicable by fleet change.

**What correcting it does, arithmetically (a measurement, not a proposal):** on 2024/25's own pools,
wind 10,153.9 × 0.16 = 1,624.6 (−2,538.5 vs the ledger's 4,163.1) and solar 4,549.8 × 0.36…0.54 =
1,637.9…2,456.9 (+1,153.8…+1,972.8), a **net −1,384.7 to −565.7 MW** — the census moves **DOWN** and
the residual **WIDENS**. Under rule 14 that is the discovered root cause, not a reason to keep the
estimate: the two wrong credits were partially cancelling, and the accurate pair says the model's
VRE census is shorter still. Note also that neither credit closes the *nameplate* half — PJM's
2024/25 solar cleared 4,232 UCAP, which at the published 0.36–0.54 implies a solar fleet several GW
larger than the model's 4,549.8 MW pool.

### 4.6 S8 — firm imports, −1,282 MW both years → **(iii) mis-attributed by the comparison, no defect**

The model credits imports as a separate block (`ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]` = 1,281.7)
while PJM books them **inside** its resource-type rows, so the row exists only to keep the table
additive. On its own terms the model is right: PJM's Table 11 shows 2024/25 imports **offered
1,527.1 / cleared 1,397.6 UCAP**, and the 2025/26 report's Table 7 shows **1,268.5 MW cleared** —
the model's 1,281.7 sits inside both. **No repair.**

### 4.7 S4/S3 — Aggregate Resource +503 / +273 → **(ii)**; S5/S6 nuclear and coal → small, and read differently on the two comparators

PJM's "Aggregate Resource" is a mixed-type aggregation with no model analogue — a scope exclusion.
Nuclear is within 143 / 490 MW either way, the closest class in the census. **Coal reads −879 MW
against published *cleared* but −2,703 MW against published *offered*** (2024/25), because 3.6 GW of
PJM coal offered and did not clear; the offered comparison is the census-relevant one and the model
is short there.

### 4.8 Which bucket, if any, explains D57's remaining position error

**The peak (R1), not the census.** It is 78 % / 67 % of the gap, it reconciles to zero residual
against PJM's own published FPR, and it is the only bucket large enough on its own. No single supply
bucket is: the largest, gas (S1), is 6.9 / 10.3 GW but is the D57 steam over-exit re-entering, and
the largest genuine input bucket (S10) cannot be measured without the rebuild §3.4 names. **D61 §4
card (a) as written — "3.9 / 5.8 GW of accredited supply the model does not count" — is answered
NO on its own terms**: the model does under-count supply, by 9.3 / 3.1 GW against PJM's offered
record, but that under-count is *offset*, not *added to*, by a requirement that is 2.7 / 4.3 GW too
large, and the residual D57 measured is the small difference between two much larger errors.

---

## 5. Matrix (rule 28), records, collision

- **Lever-queue check (28a):** the PJM backcast queue is EMPTY and closed (pjm-153/155); this is a
  forecast-lane MEASUREMENT routed through the capx director's queue as D61 §4 card (a). No cell
  adjudicated `R`/`I`/`G` is re-tested.
- **Cells (28b):** **no mechanism was tested — no probe, no candidate, no keeper, no solve — so no
  cell moves.** `capacity_market_supply_clearing` PJM stays `fc: "K"` on the D57 §8.1 ruling.
- **New mechanism (28c):** none added. The §8 cards add their own rows in their own build PRs.
- **Records:** this finding + `docs/handoffs/d66/supply-census-2026-09-06.{py,json}`. No bundle, no
  registry sidecar, no board row, no keeper, no marker, no shard, no `data/raw` file (§8 names the
  intake as a successor rather than doing it, so the lane's "changes NOTHING" holds literally).
- **Collision:** docs only, and this lane wrote **no source file at all** — disjoint by construction
  from D62 (`retirements.py`, `capacity_market.py`, `avoidable_cost_rate.py`, `scenarios.py`) and
  from D60-R3 (the forecast board). The D57 arm-A and D45-R ledgers were read, never written.

## 6. Governance attestation

- **Rule 13 / 14.** Every published figure — BRA Tables 1/2/5/6/7/9/11/12, the Reliability
  Requirement, FPR, IRM, EE add-back, ELCC class ratings — is an observable compared against; none
  entered any model path. The published number is preferred throughout, and every discrepancy is
  reported at full magnitude on its own row, including the two that move the residual the WRONG way
  (§4.5's VRE correction and §4.2's gas attribution) and the ±1.0 MW rounding residual.
- **Rule 19.** No mechanism proposed; §4.2 explicitly refuses to charter a census repair that would
  double-count the already-chartered steam over-exit.
- **Rule 21.** **Zero parameters proposed.** Every §8 candidate is a published operand with its own
  vintage rule, not a fitted value.
- **Rule 22.** Nothing out-of-training solved, scored or registered. Solve years read are the D57
  arm's own {2021, 2023, 2024, 2025}; 2022 is the bridge the harness already declares.
- **Rule 25.** PJM's own rules, record and data throughout; no other ISO's shard, verdict or
  constant touched.
- **Rule 27.** Docs and one new instrument only; no existing source file edited, nothing ≥300 lines
  rewritten.
- **Rule 29.** ZERO LP. No screen solve, no control solve; the committed ledgers and the published
  reports are the two sides, and where they cannot answer a question (§3.4) that is written down.

## 7. What this lane deliberately did NOT do

- **Did not rebuild `data/clean`** to decompose row S10 (§3.4) — it is not free and the charter is a
  reconciliation, not a build. The residual is reported instead.
- **Did not intake the by-resource-type BRA series** into `data/raw/capacity-market/auction-supply/`.
  It would be additive and safe, but the charter's "changes NOTHING" is read literally; the series
  lives in the instrument with full source-doc + page citations and §8 card C names the intake.
- **Did not re-solve anything** to "check" a number, and did not substitute a proxy for any absent
  published figure. The only report whose tables would not extract (2025/26, images) was replaced by
  **the same table one report later**, not by an estimate, with the ≤15 MW restatement recorded.

## 8. What should become a chartered repair, and what it would cost

Three cards, in descending order of what they explain. **None is proposed for arming here.**

**Card A — the requirement operand (explains 78 % / 67 % of the residual).** Read PJM's own
published RTO Reliability Requirement as the hindcast adequacy requirement instead of reconstructing
it as `model peak × FPR`. One per-ISO gate in the `{iso: bool}` form the clearing half already uses,
default `None`, PJM armed via `iso_configs._pjm_config.default_scenario_overrides` only after an A/B
(the D57 §8.1 pattern). Zero free parameters — the values are DATA and already on disk
(`demand-curve/pjm/pjm.csv`, `reliability_requirement` rows, with the FRR-adjusted and EE-add-back
companions for the RPM-basis variant). **Vintage rule must be fixed BEFORE the solve** and stated in
the PRECOMMIT: whole-RTO `reliability_requirement` pairs with the model's whole-RTO census; the
`_frr_adj + ee_addback` pair is the RPM-only comparator and is NOT the model's requirement.
**Cost:** one seam (`resolve_adequacy_requirement_mw`), a G-DRIFT audit against arm A's
`f0e050e820c1159a`, and a rule-29 screen on **2025** (the year the operand's footprint is largest:
Δpeak 4,636 MW vs 2,481) before any full-span solve. **Pre-declared sign:** the 2024/25 and 2025/26
census positions rise by ~1.7 and ~2.9 pts; the 2022/23 and 2023/24 positions FALL (their requirement
is currently too *small*), so this card is not a one-way residual improver — which is why it must be
screened structurally, never on the residual (rule 1).

**Card B — the VRE accreditation vintage (the one clean closable census gap).** Give
`RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]` the delivery-year vintage axis D48 gave the thermal classes,
so DY 2024/25 reads the Dec-2021 class-average ratings (wind 0.16; solar the MW-weighted
fixed/tracking blend of 0.36/0.54) and DY ≥ 2025/26 reads the marginal-ELCC ratings already wired.
Those values are on disk (`elcc/pjm/pjm.csv`), so zero free parameters; the fixed/tracking MW split
for the pre-reform blend is the one new operand and must come from PJM's own Table 5 mix, never
chosen. **Scope limit, stated rather than papered over: PJM's ELCC regime BEGAN with the 2024/25
BRA**, so 2022/23 and 2023/24 sit in a THIRD, pre-ELCC capacity-value regime that this repo has not
intaken — the card covers 2024/25 and later on published data, and 2022/23–2023/24 need their own
intake before they can be vintaged. The published record shows the break plainly: wind offered
2,595 → 1,608 → 1,396 UCAP across 2022/23 → 2023/24 → 2024/25 on a GROWING fleet. **Cost:** small — a registry vintage axis plus the existing `resolve_renewable_
capacity_credit` seam. **Pre-declared sign, stated now so it cannot be written to fit: the census
moves DOWN 0.6–1.4 GW in 2024/25 and the residual WIDENS.** Under rule 14 that is the point.

**Card C — the census measurement precondition (prerequisite for any S10 work).** A zero-LP
`fleet_only` / `data/clean` rebuild on arm A's recipe that emits the model's accredited MW by
resource class — hydro, biomass, storage and screen-exempt thermal separated — so row S10 becomes
attributable, plus the additive intake of the BRA by-resource-type series (`auction-supply`, new
`metric` values, source doc + page per row) through the `data-intake` skill. **Cost:** the clean-data
build (D57 measured 55 datatypes) plus ~90 s; no LP. **Card C should precede any attempt on S10**;
without it a repair there would be sized against a residual, which rule 21 forbids.

**Not chartered, by name:** any per-class supply adder, requirement haircut, or credit sized to the
3.9 / 5.8 GW residual — the residual is a measurement, never an input; and any census repair aimed
at the gas row (S1), which is the already-chartered steam over-exit (D61 §4 card (c)) seen one year
downstream.
