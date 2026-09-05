# FINDING — capx D57: the PJM clearing half, built and measured — the design does what the market does on the QUANTITY (cleared position within 0.5 / 1.0 / 2.8 pts of the published), and the PRICE reads 1.5–6.4× the published because the gas-CT / gas-ST / oil fleets offer at their full bars: the E&AS operand, measured at full magnitude

**Lane:** capx D57 (director r#36), the BUILD lane for `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`.
Branch `claude/capx-d57-pjm-clearing-build-gsdypm`; pre-declared in
`PREDECL-capx-d57-2026-09-05.md` (pushed before any solve; the D54 pre-declaration stands beneath
it). Instruments and outputs: `docs/handoffs/d57/phase0-reproduction-2026-09-05.{py,json,txt}`
(Phase 0) and `docs/handoffs/d57/ab-compare-2026-09-05.{py,json}` + `-stdout-2026-09-05.txt`
(the A/B, zero solves after the two arms). **Nothing arms.** Records: §7.

**DATA PROFILE: pjm** (full clone; `data/clean` regenerated in full — 55 datatypes, the one OOM
retried and green — before the solves, so every leg ran on the input surface of D45-R / D48).

---

## 0. Verdict (one paragraph)

The mechanism is built exactly as designed (§3.2–§3.5 of the design; every §4 seam decision
honoured, none re-decided), gated default-off with zero free parameters, byte-inert unarmed (the
bare `pjm-t1h` key `c6091bd5b62bbc3f` unmoved, every other ISO's key untouched, the PJM keeper
replay byte-identical), and its Phase 0 reproduces the D54 instrument to **0.000 $/MW-day and
0.000 pt** on both bases. Solved on the live stack in two suffixed arms (keys pre-declared and
matched), the clearing puts the model's **cleared position within −0.48 / −0.98 / −2.79 pts** of
the published BRA cleared position for 2022/23–2024/25 (arm A; arm B −0.98 / −1.29 / −3.18) — the
census evaluation sat +8.5 / +4.1 / −4.3 pts away — and the **§3.5 identity holds in all eight
solved screens** (the failing set IS the uncleared set, to the unit). The **price** reads
**1.52× / 2.43× / 5.73×** the published Resource Clearing Price (arm A; arm B 1.92× / 2.81× /
6.35×), set by a marginal offer in every long year, never within the ±20 % falsifier band — the
pre-declared signature: **the gas-CT (404 units / 24.2 GW firm), gas-ST (115 / 8.8 GW) and oil
(421 / 3.7 GW) fleets carry exactly zero E&AS margin in the hindcast prices and offer at their
full bars**, a 37 GW plateau at $61–103/MW-day above the published $29–50, and an E&AS margin
of **≥ 3.8 / 18.0 / 8.6 $/kW-yr** per CT / ST / oil unit (2022/23) would put those offers AT
the published price. The operand is measured, not moved. FC-3 moves the way the operand
dictates: the 2022 decision cohort shrinks from 88.6 GW failing at $0 to the 19.2 GW uncleared
set, the coal cohort is **retained** (economic coal 11.4 → 0.44 GW; the D48 arm's +1.4 GW
retained and then some) while the zero-E&AS **gas-steam fleet exits in full** (9.5 GW vs 2.7
actual) and the entry screen, reading a $28.7/kW-yr clearing price instead of $0, builds **+4 GW
of gas CC in 2023**; `retire.total_gw` 18.70 (control 17.96, actual 15.06), recall 17 → 12/20,
`false_retire` 6.69 → 9.49, determination **HOLD** in both arms, as pre-declared. The two arms
converge to the SAME executed set (the D48 basis moves the price and which units are marginal,
not who leaves). Grading: 14 HIT / 4 SPLIT / 6 MISS over 24 pre-declared rows (§6). Arming
recommendation §8: the rule-1 case for the JOINT flip is made and the cost is stated.

## 1. Keys, environment, cost — measured before and after the solves

| item | pre-declared | realized |
|---|---|---|
| bare `pjm-t1h` recipe key (control; D48 fields OFF, supply clearing OFF) | `c6091bd5b62bbc3f` | **`c6091bd5b62bbc3f`** — unmoved at build HEAD and after every rebase (`build_config` → `apply_iso_scenario_defaults` → `cache_key()`; `check_cache_key_registration.py --base origin/main` green). Not re-solved (D45-R's rule: only if the key moved). STOP 2 clear |
| D48 arm key (reproduced) | `bbe13b3f7b659d36` | `bbe13b3f7b659d36` |
| **arm A** (D48 both fields ON + supply clearing ON) | `f0e050e820c1159a` | **`f0e050e820c1159a`** — match (`run_scenario_iso start … cache_key=f0e050e820c1159a`) |
| **arm B** (D48 OFF + supply clearing ON) | `ccee17a4c1563727` | **`ccee17a4c1563727`** — match |
| posture in the resolved arm configs | curve gate PJM ON (shipped), fossil dates ON, verified exits ON, `entry_screen_diagnostics` ON, `retirement_rule=pipeline` | verified in both launch banners; solved [2021, 2023, 2024, 2025], bridged [2022]; no leakage-guard violation |
| wall / peak RSS (P12: 15–25 min, 9.5–10.5 GB) | — | **arm A 837 s (14.0 min) / 9.10 GB; arm B 802 s (13.4 min) / 9.29 GB** — solo, 4 cores / 15 GB / no swap (under the control's 14.7 min; STOP 6 clear) |
| D53 | unmerged at start | **still unmerged at the final rebase**; `retirement_sector_gate` absent from `origin/main`; design §4.7 not exercised |

## 2. Phase 0 — the instrument reproduced in code (I5; STOP 1 clear)

`docs/handoffs/d57/phase0-reproduction-2026-09-05.{py,json,txt}`: the code's
`clear_capacity_supply_stack` + `capacity_supply_curve` (the registry vintage curves through the
SAME `MarketDesign.capacity_price_per_firm_mw_yr` seam the solve prices) on the D54 instrument's
stack off the committed `pjm-t1h` and `pjm-t1h-d48-devintage` ledgers, both bases, four delivery
years each: **Δprice = 0.000 $/MW-day and Δposition = 0.000 pt in every one of the 16 rows**
(D48 basis 82.81 / 82.81 / 157.98 / 451.61 at 1.0445 / 1.0454 / 1.0293 / 0.9546; HEAD basis
95.89 / 95.89 / 175.11 / 451.61 at 1.0412 / 1.0423 / 1.0256 / 0.9520). The only visible
difference is inside the whole-unit convention (ties sorted by `(offer, unit_id)` in code vs
ledger order in the instrument): WHICH coal unit is marginal in 2024/25, hence the uncleared firm
reads 12,482 vs 11,729 / 12,412 MW — price and cleared quantity identical, as the rule guarantees.

## 3. What the solves measured — the clearing, per delivery year, beside the published record

Published rows are VALIDATION OBSERVABLES (rule 13); nothing below entered the model.

### 3.1 Arm A — `pjm-t1h-d57-clearing` (D48 basis: UCAP through DY 2024/25, DR counted, pre-CIFP FPR)

| screen → DY | `R` (screen seam) | census pos (screen fleet) | `Q_0` | offers / uncleared | **price $/MW-day ($/kW-yr)** | **cleared pos** | published price · pos | ratio · Δpos | how · marginal unit | uncleared firm by fuel |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 2022 → 2022/23 | 155,048 | 1.1702 | 30,578 | 1,370 / 429 | **76.10 (27.78)** | **1.0462** | 50.00 · 1.0510 | **1.52×** · −0.48 pt | marginal offer · an oil unit (the oil plateau, 25 ÷ 0.90) | coal 5,368 · gas_cc 2,052 · gas_st 8,802 · oil 2,996 = 19,218 |
| 2023 → 2023/24 | 161,117 | 1.0881 | 36,375 | 907 / 168 | **82.81 (30.23)** | **1.0454** | 34.13 · 1.0552 | **2.43×** · −0.98 | marginal offer · a coal unit (AEP Ohio, committed tranche) | coal 2,465 · gas_cc 2,141 · gas_st 1,982 = 6,588 |
| 2024 → 2024/25 | 166,810 | 1.0321 | 27,960 | 769 / 8 | **165.84 (60.53)** | **1.0276** | 28.92 · 1.0555 | **5.73×** · −2.79 | marginal offer · a coal unit (Dominion, economic tranche) | coal 406 |
| 2025 → 2025/26 | 148,798 | 0.9661 | 24,000 | 761 / 0 | 451.61 (164.84) = the cap | 0.9661 ≡ census | 269.92 · 1.0049 | 1.67× · −3.88 | every offer clears · census (I1 live) | none |

### 3.2 Arm B — `pjm-t1h-d57-clearing-headbasis` (HEAD's basis: ELCC class every year, DR netted, composite requirement)

| screen → DY | census pos | `Q_0` | offers / uncleared | **price** | **cleared pos** | published | ratio · Δpos | how · marginal | uncleared firm by fuel |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| 2022 → 2022/23 | 1.1636 | 19,224 | 1,370 / 310 | **95.89 (35.00)** | **1.0412** | 50.00 · 1.0510 | **1.92×** · −0.98 | marginal · a CT peaker (the CT plateau, 21 ÷ 0.60) | coal 1,014 · gas_cc 1,598 · gas_ct 5,675 · gas_st 6,909 = 15,196 |
| 2023 → 2023/24 | 1.0628 | 24,794 | 756 / 38 | **95.89 (35.00)** | **1.0423** | 34.13 · 1.0552 | **2.81×** · −1.29 | marginal · a CT peaker | coal 1,014 · gas_cc 73 · gas_ct 1,534 = 2,621 |
| 2024 → 2024/25 | 1.0306 | 17,325 | 768 / 9 | **183.57 (67.00)** | **1.0237** | 28.92 · 1.0555 | **6.35×** · −3.18 | marginal · a coal unit | coal 860 |
| 2025 → 2025/26 | 0.9634 | 17,915 | 760 / 0 | cap | 0.9634 ≡ census | 269.92 · 1.0049 | 1.67× · −4.15 | census (I1 live) | none |

**Against the instrument (PREDECL-d54 §2 / D57 addendum §4).** Arm B lands ON the instrument's
rows in 2022/23 and 2023/24 (95.89 / 1.0412; 95.89 / 1.0423 — to four decimals) and +$8.46 /
−0.19 pt in 2024/25. Arm A lands ON it in 2023/24 (82.81 / 1.0454), +$7.86 / −0.17 pt in 2024/25,
and **$76.10 / 1.0462 in 2022/23 vs the instrument's $82.81 / 1.0445** — below the addendum's
82.8–98 band. The reason is the one the addendum §3 sized with the wrong sign: the 2022 bridge
screen's requirement is the runner's own seam requirement (**155,048 MW** on the seam peak
142,664 — the D52 finding's growth-scaled weather-year peak), not the D48 instrument's 162,574
(reconstructed on the ledger's LP peak); `R` 7.5 GW lower against an accredited census only 3.8
GW lower (181,435 vs 185,263) puts the screen fleet's census position at **1.1702, +3.1 pts
ABOVE** the instrument's entering census (1.1396), not 2.0 pts below — so the crossing lands one
plateau LOWER (the oil plateau at $76.10) at a slightly higher position. In 2023–2025 the seam
requirement is within 0.1–1.2 % of the ledger's (161,117 vs 160,904; 166,810 exact — the weather
year; 148,798 vs 150,605) and the rows agree. This is the reconstruction limit D48 §3.3 and the
D54 PREDECL §0 both stated; the runner's own numbers govern.

### 3.3 The identity (I2 / P4) — asserted from the ledgers in all eight screens

In every solved screen of both arms the set of `decided` + `entry_capped` + `re_confirmed`
`pipeline_events` rows equals the set of uncleared offers on the `capacity_clearing.offer_stack`
to the unit (429 / 168 / 8 / 0 in arm A; 310 / 38 / 9 / 0 in arm B), every such row carries
`capacity_cleared: false` and `capacity_revenue_usd: 0.0`, and no cleared unit fails
(`ab-compare` "IDENTITY: HOLDS" × 8). STOP 3 is not triggered: the settlement is wired as
designed — the screen no longer decides "who fails at one price"; it decides "who the market did
not clear".

### 3.4 What the admission cap does now that the budget is priced (design §4.1)

| 2022 screen | control (census, $0) | D48 arm ($0) | **arm A** | **arm B** |
|---|---:|---:|---:|---:|
| candidate pool (failing = uncleared) | 1,211 units / 88.6 GW nameplate | 1,211 / 88.6 | **429 / 19.2 GW firm** | **310 / 15.2 GW firm** |
| admitted (`decided`), nameplate | coal 11,415 | coal 12,818 | coal 5,835 + gas_st 7,334 = **13,169** | coal 1,222 + gas_cc 2,160 + gas_ct 133 + gas_st 9,464 = **12,979** |
| trimmed (`entry_capped`) | 77.2 GW (coal 11.0 · gas_cc 26.8 · gas_ct 25.8 · gas_st 9.5 · oil 4.1) | 75.8 GW | gas_cc 2,160 + gas_st 2,131 + oil 3,329 = **7,620** | gas_ct **9,325** |
| cap's role | selects 13 % of an 89 GW pool, coal first | same | trims 37 % of a 21 GW pool | trims 42 % of a 22 GW pool |
| realized-year floor (`floor_retained`) | 0 | 0 | 0 in every year | 0 in every year |

The cap can no longer manufacture a class ordering out of a $0-priced pool (D45 §2.3 item 4):
its pool is the market's uncleared set, and its worst-first-depth admission + cheapest-firm
retention now orders zero-E&AS gas steam (depth = its full $35 bar) and the deepest coal first,
retains gas_cc first ($31.6/firm-kW-yr) — exactly the ordering design §4.1 pre-stated. The
2022 `entry_capped` gas_st (2,131 MW, arm A) and gas_cc (2,160) are admitted the NEXT screen and
executed at lag 1, so the cap only delays them a year.

### 3.5 FC-3 — every row, both arms, against the control AND the D48 arm

| row (actual) | control `pjm-t1h` | D48 arm | **arm A** | **arm B** |
|---|---:|---:|---:|---:|
| `retire.total_gw` (15.062) | 17.958 FAIL +19 % | 19.361 FAIL +29 % | **18.702 FAIL +24 %** | **18.707 FAIL +24 %** |
| coal (10.299) | 16.990 (economic 11.415) | 18.393 (12.818) | **6.016 (economic 0.441)** | **6.016 (0.441)** |
| gas_st (2.702) | 0.833 (announced only) | 0.833 | **10.297 (economic 9.465)** | **10.297 (9.465)** |
| gas_cc (0.434) | 0.075 | 0.075 | **2.328 (economic 2.254)** | **2.333 (2.258)** |
| gas_ct (0.808) · oil (0.613) | 0 · 0.051 | 0 · 0.051 | 0 · 0.051 | 0 · 0.051 |
| `unit_recall_gt300` (band 0.70) | 17/20 PASS | 17/20 PASS | **12/20 FAIL** | **12/20 FAIL** |
| `false_retire` GW (band 0.15) | 6.691 FAIL | 8.094 FAIL | **9.490 FAIL** | **9.494 FAIL** |
| `add.by_tech` gas_cc (8.525) | 8.118 PASS | 8.118 | **12.118** (+4,000 decided in the 2023 screen) | **12.118** |
| add wind / solar / gas_ct / storage | 3.0 / 9.762 / 1.013 / 0 | same | same | same |
| 2025 entering position · backstop | 0.9617 · 1,012.8 MW | 0.9566 · 1,012.8 | 0.9661 · 1,012.8 | 0.9634 · 1,012.8 |
| LOYO recall (−2023 / −2024 / −2025) | 1.00 / 0.42 / 0.84 | 1.00 / 0.42 / 0.84 | 0.58 / 0.58 / 0.58 | 0.58 / 0.58 / 0.58 |
| LOYO false-retire raw GW | 8.09 / 0.00 / 6.80 | 9.49 / 0.00 / 8.20 | 7.24 / 9.50 / 9.51 | 11.17 / 9.50 / 9.51 |
| determination | HOLD | HOLD | **HOLD** | **HOLD** |

**The path (from `pipeline_events`, arm A):** the 2022 bridge screen decides coal 5,835 + gas_st
7,334 (the steam executes at lag 1, in 2022); the 2023 screen clears the coal cohort at $82.81
— 3,156 MW **reversed** (the soft latch: a cleared unit re-clears its bar), 2,679 re-confirmed —
and admits + executes the previously capped gas_cc 2,254 and gas_st 2,131; the 2024 screen at
$165.84 reverses a further 2,238 MW of coal and executes the 441 MW that stayed uncleared; 2025
fails nothing. Arm B takes a different 2022 cohort (coal 1,222 admitted, gas_ct 9,325 capped
then 2,557 decided in 2023 and reversed in 2024) and reaches the SAME executed set. **The D48
arm's +1.4 GW of cap-admitted coal is retained — and so is the rest of the coal cohort:** a
faithful price that pays $28–60/kW-yr to a cleared unit keeps every coal unit whose
zero-E&AS gap is below it, which is all but 0.44 GW. The steam over-exit is the same operand
seen from the other side: at zero E&AS its offer is its whole bar ($103/MW-day on UCAP), above
every clearing price the window forms, so every steam unit is uncleared and paid $0 in every
year — 9.5 GW economic against 2.7 GW actual (of which 0.8 GW is announced-class).

**Entry (P10's miss).** The thermal-entry screen reads the clearing price as a price taker: in
the 2023 screen a new gas CC's capacity term is **$28,715/MW-yr** ($30.23/kW-yr × 0.95 UCAP)
instead of $0, its margin flips from −$17,947 to **+$10,768/MW-yr** and it builds to its 4,000
MW per-tech cap (control: 0 in 2023, 4,000 in 2025 at the cap price; both arms build 4,000 in
2025 too). The pre-declaration's premise ("no thermal candidate crosses its LCOE at $30–58/kW-yr")
was wrong by a margin of ~$11k/MW-yr; the actual PJM CC additions in the window are 8.5 GW
(model now 12.1). Storage entry stays at 0 in every leg; wind / solar / gas_ct additions are
byte-identical to the control.

## 4. THE E&AS OPERAND — measured, not moved (rule 21; PREDECL-d54 §4)

Read off the arm ledgers' `capacity_clearing.offer_stack` (every screened unit, cleared or not):

| DY (published price) | firm MW of offers ABOVE the published price, by fuel | units / firm MW AT THE FULL BAR (zero E&AS) | E&AS margin per zero-margin unit that puts its offer AT the published price ($/kW-yr) |
|---|---|---|---|
| **arm A (UCAP basis)** | | | |
| 2022/23 ($50.00) | coal 7,110 · gas_cc 22,357 · **gas_ct 24,244 · gas_st 8,802 · oil 3,723** = 66,235 | gas_ct **404 / 24,244** · gas_st **115 / 8,802** · oil **421 / 3,723** · gas_cc 40 / 1,145 · coal 2 / 30 | gas_ct **≥ 3.8** · oil **≥ 8.6** · gas_cc ≥ 12.7 · gas_st **≥ 18.0** · coal ≥ 41.7 |
| 2023/24 ($34.13) | coal 8,873 · gas_cc 22,932 · gas_ct 24,243 · gas_st 1,982 = 58,029 | gas_ct 403 / 24,243 · gas_st 77 / 1,982 · gas_cc 1 / 73 | gas_ct ≥ 9.3 · gas_cc ≥ 18.2 · gas_st ≥ 23.4 · coal ≥ 47.0 |
| 2024/25 ($28.92) | coal 32,411 · gas_ct 23,980 · oil 3,723 = 60,118 | oil 8 / 3,723 (the CT fleet's 2024 margin is small but non-zero) | gas_ct ≥ 8.9 · oil ≥ 15.5 · coal ≥ 48.4 |
| **arm B (ELCC-class basis)** | | | |
| 2022/23 | coal 6,415 · gas_cc 17,573 · gas_ct 15,475 · gas_st 6,909 · oil 3,764 = 50,136 | gas_ct 330 / 14,507 · gas_st 115 / 6,909 · oil 421 / 3,764 | gas_ct ≥ 10.1 · oil ≥ 8.4 · gas_cc ≥ 16.5 · gas_st ≥ 21.7 · coal ≥ 43.4 |
| 2023/24 | 41,345 | gas_ct 330 / 14,507 | gas_ct ≥ 13.5 · gas_cc ≥ 20.8 · coal ≥ 48.2 |
| 2024/25 | 48,479 | oil 8 / 3,764 | gas_ct ≥ 14.7 · oil ≥ 15.4 · coal ≥ 49.7 |

**Reading.** The stack is too dear by construction of ONE operand: the pro-forma E&AS margin of
the peaking and steam fleets is exactly zero in the hindcast prices (D45 §1 (i) — their gap
equals their bar), so their offers are their gross bars, which sit $11–53/MW-day above the
published price. The published record shows those fleets clearing (Table 7: gas offered 75.5 GW
UCAP, cleared 69.3 GW in 2022/23) — i.e. earning enough E&AS that their net ACR fell below $50.
The margins in the last column are what that E&AS must be per unit, stated per class; they are
small for CTs and oil on the UCAP basis (**$3.8 and $8.6/kW-yr** in 2022/23) and larger for
steam (**$18.0**). They are the D12 scarcity-basis object seen from the capacity side (the
hindcast prices carry no reserve / scarcity rent a peaker lives on), and the external check is
PJM's own IMM net-revenue table (Monitoring Analytics SOM §7, "Net Revenue" for a new CT / CC / CP
— NOT in-repo; not quoted here, rule 13). **Nothing in this lane changes the operand**: no
haircut, adder or coefficient was applied, and the price mismatch is reported at full
magnitude. The second, smaller reason the stack is dear — coal's bar at 2.0× PJM's default gross
ACR (design §6 item 2) — shows in the 2024/25 column (coal ≥ $48/kW-yr) and is rule-23-frozen.

**For the cleared POSITION to land on the published pair as well:** at the published cleared
position the stack's marginal offer is **$76.10** (arm A, 2022/23) / **$95.89** (arm B) — the oil
and CT plateaus respectively; lowering those two plateaus (and steam's) by the per-class margins
above moves the crossing into the coal / gas-CC tails at ~$50, which is where the record's
uncleared set (coal 6.5, gas 6.2 GW UCAP) sits. That is a statement about the operand; whether the
tails then land the position within 0.5 pt is the successor lane's measurement.

## 5. STOP conditions — every one checked

1. Phase 0 — CLEARED (0.000 / 0.000, §2). 2. Bare / other-ISO keys — CLEARED (§1). 3. I2 — HOLDS in
all eight screens (§3.3). **4. The falsifier — NOT triggered:** no arm's price is within ±20 % of the
published price in any long year (arm A 1.52× / 2.43× / 5.73×, arm B 1.92× / 2.81× / 6.35×; the
band is 0.8–1.2×). No operand moved; the design is not tuned. 5. 2025 — moves only through the
entering fleet (§3.5: position 0.9661 / 0.9634 vs the control's 0.9617, the backstop identical
at 1,012.8 MW, no 2025 screen failure); CLEARED. 6. Wall / RSS — CLEARED (§1). 7. Nothing beyond
the suffixed keys, the PJM cell, the matrix row and the tests moved (§7). D53 did not merge.

## 6. The pre-declaration, graded at full magnitude (PREDECL-capx-d57 §4–§5 over PREDECL-d54)

| # | prediction | arm A | arm B | grade |
|---|---|---|---|---|
| P1 | cleared position within ±1.5 / ±1.5 / ±3.5 pts (A), ±2 / ±2 / ±4 (B) of the published; BELOW it in every long year; inside the offered–cleared band | −0.48 / −0.98 / −2.79 | −0.98 / −1.29 / −3.18 | **HIT** (both, every year, every clause) |
| P2a | price > $0 and > published in every long year; `how` = marginal offer | yes; marginal offer × 3 | yes; × 3 | **HIT** |
| P2b | ratios A 1.7–2.0× / 2.4–2.8× / 5.2–5.7×; B 1.9–2.2× / 2.8–3.1× / 5.8–6.3× | **1.52** / 2.43 / **5.73** | 1.92 / 2.81 / **6.35** | **SPLIT** — 2023/24 HIT both; 2022/23 A MISS low (§3.2's requirement reading), B HIT; 2024/25 both a hair above (+0.03 / +0.05) |
| P2c | the marginal unit a gas_cc in 2022/23–2023/24, coal in 2024/25 (A) | oil / coal / coal | CT / CT / coal | **SPLIT** (2024/25 HIT; the 2022/23–2023/24 marginal sits one plateau away from the instrument's) |
| P3 | 2025 identity: no failure, clearing ≡ census, cap | yes | yes | **HIT** |
| P4 | I2 in every screen; every failing row `capacity_cleared: false` | 8/8 | 8/8 | **HIT** |
| P5 | uncleared composition: gas_st over-represented, coal under in 2022/23–2023/24 and over in 2024/25, nuclear absent, gas_ct cleared (A) / partly uncleared (B) | steam 8.8 GW (all) ✓; coal 5.4 < 6.5 ✓; **2024/25 coal 0.4 GW, not ~12** ✗; nuclear absent ✓; CT cleared ✓ | steam 6.9 ✓; coal 1.0 ✓; 2024/25 coal 0.9 ✗; CT 5.7 GW uncleared ✓ | **SPLIT** — the 2024/25 coal miss: the instrument's 12 GW was the CONTROL's 2024 screen (11.4 GW of coal already decided, the stack thinner); on the arm's intact coal fleet the whole cohort clears at $166–184, and only 0.4–0.9 GW sits above the curve |
| P6 | 2022 cohort ≈ 16 / 17.5 GW ± 3; `decided` 10–16 GW; `entry_capped` 0–8 GW | 19.2 GW firm; 13.2; 7.6 | 15.2; 13.0; 9.3 | **HIT** (A); **SPLIT** (B: capped 9.3 > 8) |
| P7 | coal economic 2.5–5.0 (A) / 0.8–2.5 (B); coal total 8–11; the D48 +1.4 GW retained | **0.44**; 6.0; retained | 0.44; 6.0; retained | **MISS** on the bands (LOW — the cohort reverses under the cleared price), HIT on the retention |
| P8 | gas_st 4–9 GW (2023, lag 1); gas_cc 0–2.2; gas_ct 0 (A) / 0–3 (B) | **9.47**; 2.25; 0 | 9.47; 2.26; 0 | **MISS** (steam above the band by 0.5 GW: ALL of it exits; the gas_cc 2.25 a hair above) |
| P9 | total 14–21 GW; recall 9–15/20; false_retire 5–11; HOLD | 18.70; 12; 9.49; HOLD | 18.71; 12; 9.49; HOLD | **HIT** (all four; the total FAILs its band as the row said it might) |
| P10a | 2025 entering 0.95–0.99; backstop 0.5–1.1 GW; storage ≤ 0.2 GW | 0.9661; 1,012.8; 0 | 0.9634; 1,012.8; 0 | **HIT** |
| P10b | additions byte-identical to the control in 2022–2024 | **+4,000 MW gas_cc decided 2023** | same | **MISS** — the premise was wrong (§3.5) |
| P11 | LOYO position residual improves in every fold vs the census control | +8.5 / +4.1 / −4.3 → −0.5 / −1.0 / −2.8 (2025 −4.3 → −3.9) | → −1.0 / −1.3 / −3.2 | **HIT** on the position; FC-3 LOYO recall 1.00 / 0.42 / 0.84 → 0.58 × 3 (one fold up, two down) — reported |
| P12 | 15–25 min; 9.5–10.5 GB | 14.0 min; 9.10 GB | 13.4 min; 9.29 GB | **HIT** (faster and lighter than the band) |
| §3.1 | census(screen fleet) ≈ 2.0 / 1.1 / 0.15 / 0 pts BELOW the entering census; price UP $0–15 in 2022/23 | census 1.1702 (+3.1 pts vs the instrument's entering); price DOWN $6.71 | on the rows | **MISS** — the requirement, not the fleet, moved (§3.2); the SIGN of the construction point was wrong |
| keys | bare unmoved; A / B as declared | ✓ | ✓ | **HIT** |

**Tally: 14 HIT, 4 SPLIT, 6 MISS (P7 bands, P8, P10b, §3.1, and the two halves of P5's 2024/25
coal row counted once).** Every miss has its mechanism named in §3, none is absorbed, and two of
them (P7, P8) are the E&AS operand's signature exceeding its own pre-declared magnitude: the
cleared price retains the coal cohort MORE completely and the zero-E&AS steam exits MORE
completely than the addendum's bands allowed.

## 7. Matrix (rule 28), registration, records

- **Registered** `pjm-2021-2025-realized-t1h-d57-clearing` → **`pjm-t1h`** (the shipped
  posture after the §8.1 ruling; it was pre-declared as the suffixed `pjm-t1h-d57-clearing`
  and re-pointed in the same session) and `pjm-2021-2025-realized-t1h-d57-clearing-headbasis` →
  **`pjm-t1h-d57-clearing-headbasis`**; D45-R's `pjm-2021-2025-realized-t1h-d45r` re-registered
  under **`pjm-t1h-pre-d57`** (`VERDICT_MAP` rows; `register_forecast_run.py --bundle` after the
  final rebase, so every `scored_at_sha` names a commit on the merged history; canonical
  sidecars `frontend/data/hindcast/<run_id>.json`; reports
  `docs/hindcast-reports/<run_id>-2026-09-05.md`; `ff-verdicts.json` moves one key and gains
  two). Scored `score_capacity_hindcast.py --bundle` + `--flip-gate-extras` + `forecast_verdict.py
  --tier t1h`. The board's PJM T1-H row reads HOLD as before.
- **Committed slim sets** (the D45-R / D48 template): `meta.json`, `run_config.json`,
  `forecast_verdict.json`, the five `evolution_<year>.json` ledgers (carved out of `.gitignore`
  per bundle — they carry the `capacity_clearing` blocks and the per-row settlement fields, the
  sole evidence for §3–§4), `score.json`, the two `screen_signal_diag_*.npz`. Parquets,
  `config.yaml`, `run_config.yaml` and the floor-retention sidecars stay ignored.
- **Matrix:** base row `capacity_market_supply_clearing` + a cell in every shard landed in the
  build commit (rule 28c; `check_mechanism_matrix.py --base origin/main` green). The PJM shard's
  cell is re-stamped here with the measured verdict — letter **`fc: "O"`, backcast `·`** — the
  mechanism is neither rejected (structurally correct, identity exact, position validated) nor
  inert (FC-3 moved) nor a keeper (the owner arms or declines): OPEN on a measured record. No
  other shard touched (rule 25).
- **Docs:** `model-methodology-spec.md` §5.9 carries the supply-clearing mode paragraph
  (doc-sync of the built mechanism).
- **Scope discipline:** every file this lane pushes is either new or one of the seams design
  §7.2 lists (`retirements.py`, `adequacy.py`, `evolve.py`, `runner.py`, `capacity_market.py`,
  `scenarios.py`, the harness, the registry map, the test file, the matrix, `.gitignore`,
  `parameters.json`, the spec). No keeper, no other ISO's shard, no marker. The one
  pre-existing red noticed and NOT touched: `validate_parameters.py` reports
  `scenario.miso_zonal_gas_basis_skip_923_priced` missing a registry entry on `origin/main`
  (another lane's field).

## 8. Arming recommendation — on the pre-stated condition for the JOINT flip

The condition the chain pre-stated for this flip is D48 §8's, re-routed: D48's two fields were
NOT to be armed alone because "the admission cap prices a consistent budget at an inconsistent
$0 until the market clears"; arming them WITH the clearing half is "the configuration in which
the same budget is priced at the published curve's $15–21/kW-yr and the D45 §3(a) re-screen says
most of the cohort then stays". Measured: the budget is now priced (§3.4), the cohort stays
(§3.5: economic coal 12.8 → 0.44 GW; the +1.4 GW retained), and the design reproduces the market's
cleared QUANTITY (§3.1–3.2: within 0.5–1.3 pts in the two long years where the record is
cleanest) with the identity exact (§3.3) and the falsifier clear (§5). On rule 1 the structural
case is complete: the census evaluation was a mechanism the real market does not have, and this
is the one it has.

What the joint flip costs, stated at full magnitude: the price it forms is **1.5–6.4× the
published** because the CT / ST / oil E&AS operand is zero, and that same zero pushes the
executed set the wrong way on COMPOSITION — steam over-exits (+7.6 GW vs the record), coal
under-exits (−4.3 GW), recall 17 → 12/20, `false_retire` +2.8 GW — while the total (18.7 vs 18.0
GW) and the determination (HOLD) barely move. Rule 1 says a structurally-correct mechanism is
never rejected for that, and rule 14 says the worse fit is the discovered root cause, not a
reason to revert: the root cause is named (§4), it is the D12 scarcity-basis / peaker-E&AS lane's
object, and this design is the instrument that will show that lane landing (the price ratio
falling toward 1× WITHOUT a coefficient).

**Recommendation: ARM the joint configuration — `pjm_accreditation_design_vintage` +
`pjm_demand_response_supply` + `capacity_market_supply_clearing_by_iso["PJM"]` — as the PJM
forecast default, with the E&AS-operand repair named as its successor and the FC-3 composition
reading worse until it lands.** The lane recommends this over HOLD because holding keeps a
mechanism known to pay $0 where the auction paid $10.6–18.3/kW-yr, and because the two halves
are not separable (D48 §8: never the devintage alone; and the clearing alone on HEAD's basis —
arm B — reaches the same executed set at a dearer price, so the basis adds no risk). The owner
may reasonably decline on the FC-3 composition — that is exactly the trade the card must state.
**Nothing arms in this lane.** Two zero-DOF measurements sharpen the card and are NOT solved
here: (i) the three-year E&AS offset (design §4.8) — it tempers the 2024 coal offers and is the
one admissible alternative operand; (ii) a re-run of both arms after the D12 lane's peaker E&AS
lands — the first solve in which the price ratio can move toward 1× legitimately.

### 8.1 OWNER RULING (in-session, 2026-09-05) — PROMOTED

The owner ruled on §8 in-session ("if structural integrity improves but gates regress that may
still be a keeper … plz promote"). Executed, in this lane, as the JOINT flip and nothing else:

- **How it is armed.** `config/iso_configs.py::_pjm_config` now carries
  `default_scenario_overrides = {pjm_accreditation_design_vintage: True,
  pjm_demand_response_supply: True, capacity_market_supply_clearing_by_iso: {"PJM": True}}`
  — the ERCOT D-30 / MISO D-26 pattern — **not** a flip of the three shared `ScenarioConfig`
  defaults (which stay `False` / `False` / `None`, so no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`
  entry is needed and no other ISO's key moves). An explicit caller value still wins
  (OVERRIDE-FIX): `--no-pjm-accreditation-design-vintage --no-pjm-demand-response-supply
  --no-capacity-market-supply-clearing` reaches the D45-R control key `c6091bd5b62bbc3f`
  (the harness passes the supply gate's explicit `None` OUTSIDE its None-drop dict for exactly
  this reason). Asserted by `TestPjmCapacitySupplyClearing::test_pjm_iso_override_arms_
  forecast_only`: the bare PJM T1-H recipe now resolves to **arm A's own key
  `f0e050e820c1159a`** (the same payload arm A hashed explicitly — the solved bundle IS the
  shipped posture, no re-solve), the D48-off posture resolves to arm B's `ccee17a4c1563727`,
  MISO's bare key `eff2c890746ec966` and every other ISO's resolved fields are untouched, and a
  PJM plain backcast is coerced back to the off posture with its key unmoved (every backcast
  keeper byte-identical; the D44 flip, by contrast, advanced the backcast pin).
- **Registration re-pointed** (`VERDICT_MAP`): `pjm-2021-2025-realized-t1h-d57-clearing` →
  **`pjm-t1h`** (the shipped posture; determination HOLD, as before);
  `pjm-2021-2025-realized-t1h-d45r` → **`pjm-t1h-pre-d57`** (the census leg preserved verbatim,
  its own verdict standing — the D45-R convention); arm B keeps `pjm-t1h-d57-clearing-headbasis`.
  The board's PJM T1-H row still reads HOLD.
- **Matrix:** the PJM shard's `capacity_market_supply_clearing`, `pjm_accreditation_design_
  vintage` and `pjm_demand_response_supply` cells read **`fc: "K"`** with this ruling; every
  other shard's cell is untouched (rule 25 — the mechanisms are generic in form, PJM-scoped by
  data; another ISO arms on its own evidence).
- **What the ruling does NOT do, stated.** It does not move `ScenarioConfig` defaults, the
  backcast namespace, any keeper, or any other ISO. The PJM **T1-F** bundle
  (`pjm-2026-2030-d45r-remeasure` → `pjm-t1f`, key `321f04e9060787f0`) was solved at the
  pre-ruling posture and now carries a SUPERSEDED posture; per the D44 precedent it joins the
  director's batched re-measure decision — this lane re-ran nothing forward (the T1-H arms are
  the measured record). The named successor stands: the CT / ST / oil E&AS operand (§4).

## 9. Governance attestation

- **Rules 13 / 14.** The published Resource Clearing Prices, cleared positions and Table 7
  offered / cleared UCAP entered nothing; they are compared against. The signs were stated before
  the build (D54 §5) and again before the solve (D57 addendum §4–§5); every miss is reported at
  full magnitude with its mechanism.
- **Rule 19.** One capacity-revenue mechanism per unit (the census evaluation is REPLACED under
  the gate); one clearing per screen year; one requirement; entry and storage are price takers
  through the one seam; no second cap, floor or price path.
- **Rule 21.** Zero free parameters; the E&AS operand is measured (§4) and never moved; the
  indifference guard is a rounding guard (1e-9 relative), not a parameter.
- **Rule 22.** T1-H 2021–2025 only; 2022 bridged and never scored; LOYO within 2023–2025 is the
  scorer's; nothing out-of-training read.
- **Rule 24 / 27 / 28.** The field is registered (guard green); every ≥300-line file was edited
  locally, pushed as its on-disk bytes and blob-verified after each push; the matrix row and six
  cells landed in the build commit.
- **Rule 25.** PJM's own rules and record; the gate is generic in form and PJM-scoped by data; no
  other ISO's shard or verdict touched.
- **Collision.** D53 unmerged throughout; this lane's `retirements.py` diff is the import, the
  loop's deferred capacity leg, the post-loop settlement call and the new helper — disjoint from
  D53's hunks (`dated_plant_unit_ids`, the requirement resolvers, `_apply_reliability_floor`);
  `test_capacity.py` gained one class beside `TestPjmAccreditationDesignVintage`. D58 stays held
  until this lands.
