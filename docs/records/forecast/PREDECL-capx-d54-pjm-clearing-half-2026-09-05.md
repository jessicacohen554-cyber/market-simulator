# PRE-DECLARATION — capx D54: the PJM clearing half, zero-solve, against the published BRA record

**Pushed with the design (`DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`) BEFORE any
code exists.** Docs-only lane: nothing below was solved; every number is computed by the
committed instrument `docs/handoffs/d54/clearing-predecl-2026-09-05.py` (D48 basis) and
`clearing-predecl-headbasis-2026-09-05.py` (HEAD basis) from the committed D45-R and D48
ledgers, the D48 position instrument and the D45 published-positions instrument — outputs
`clearing-predecl[-headbasis]-2026-09-05.{json,txt}` beside them. The build lane grades this
document at full magnitude in its finding, misses included, and reproduces §2 with the
code's own clearing function BEFORE its first solve (design §3.6 I5 / §7.7 item 1).

**Rule 13 / 14 discipline.** The published Resource Clearing Prices, cleared positions and
Table 6/7 uncleared quantities are VALIDATION OBSERVABLES; they enter nothing. The instrument
uses only the screen's own operands (per-unit `going_forward_cost_usd`, `net_revenue_usd −
capacity_revenue_usd`, `mw`, `fuel` from `pipeline_events`), the D48 accreditation basis
(class EFORd through DY 2024/25, ELCC class from 2025/26; per-unit EFORd in the runner — a
first-order reconstruction, stated) and the committed vintage VRR curves. Zero free
parameters. The signs and the falsifier are fixed here, before the build.

---

## 0. What is pre-declared

For each screen year of the 2021–2025 T1-H (2022 bridge, 2023, 2024, 2025 — delivery years
2022/23 … 2025/26), the clearing price, the cleared quantity (as a position), the uncleared
set by fuel, and the resulting failing set, under the design of §3 of the design doc, on
two bases: **the D48 basis** (arm A of the A/B — `pjm_accreditation_design_vintage` +
`pjm_demand_response_supply` ON) and **HEAD's basis** (arm B — both OFF). The control is
the census evaluation ($0 / $0 / $0 / cap). Beside each: the published BRA record.

Reconstruction limits, stated: (i) passing units are absent from the ledgers, so the
price-taking block `Q_0` is `firm(BOTH or OFF from the D48 instrument) − Σ failing A_g`
rather than a per-unit sum — the build's `Q_0` is the per-unit sum and will differ at the
sub-GW level where the D48 instrument's class-EFORd firm differs from the runner's per-unit
firm (D48 §2 measured that reconstruction at +0.15 / +0.66 pt on the position); (ii) the
2022 bridge screen is the 2021 dispatch on the 2021 fleet at the 2021 peak, as the runner
does it; (iii) the marginal unit is treated as cleared (design §3.4 rule 4).

## 1. The stack, read off the committed 2022 screen (D48 basis) — why the price lands where it does

| fuel | failing units | failing firm MW | offer q25 / q50 / q75 $/MW-day | max | what the numbers are |
|---|---:|---:|---|---:|---|
| coal | 103 | 20,621 | 9.3 / 9.3 / 78.7 | 174.2 | the cap-bound cohort's small gaps (D45 §1 (ii)) then the zero-margin tail; 174.2 = the full bar 58.5 ÷ 0.92 |
| gas_cc | 168 | 25,456 | 53.1 / 53.1 / 67.8 | 86.5 | 86.5 = the full bar 30 ÷ 0.95 |
| gas_ct | 404 | 24,244 | 61.2 / 61.2 / 61.2 | 61.2 | **every CT at its full bar**: zero E&AS (D45 §1 (i)); 21 ÷ 0.94 |
| gas_st | 115 | 8,802 | 103.0 / 103.0 / 103.1 | 103.1 | every steam unit at its full bar: 35 ÷ 0.93 |
| oil | 421 | 3,723 | 76.1 / 76.1 / 76.1 | 76.1 | every oil unit at its full bar: 25 ÷ 0.90 |
| price takers (`Q_0`) | — | 102,418 | 0 | 0 | passing thermal (nuclear, the covering coal/CC), VRE, hydro, storage, tie, offered DR, dated exempt |

Read: the stack has a **37 GW plateau of zero-margin peakers and steam between $61 and
$103/MW-day**, above the published $50 (2022/23) and far above $34 / $29 (2023/24,
2024/25). The curve reaches the stack's marginal offer at $82.81 (a gas_cc unit's net ACR)
at position 1.0445; the published auction cleared at 1.0510 for $50.00. The cleared
QUANTITY is therefore nearly right and the PRICE is not, and the reason is the operand, not
the mechanism: the real CT/steam/oil fleets offered below their gross ACR because they
earned E&AS.

## 2. The pre-declaration — design vs the published record, per delivery year

### 2.1 Arm A — the D48 basis (`pjm_accreditation_design_vintage` + `pjm_demand_response_supply` ON, supply clearing ON)

| screen → DY | requirement `R` | firm (stack) | price takers `Q_0` | failing firm / nameplate | **design price $/MW-day ($/kW-yr)** | **design cleared pos** | published price $/MW-day ($/kW-yr) | published cleared pos | published offered pos | Δpos (pts) | price ratio design ÷ published |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 → 2022/23 | 162,574 | 185,263 | 102,418 | 82,845 / 88,602 (1,211 units) | **82.81 (30.23)** | **1.0445** | 50.00 (18.25) | 1.0510 | 1.2200 | −0.65 | 1.66× |
| 2023 → 2023/24 | 160,904 | 183,798 | 104,304 | 79,494 / 84,856 (792) | **82.81 (30.23)** | **1.0454** | 34.13 (12.46) | 1.0552 | 1.1407 | −0.98 | 2.43× |
| 2024 → 2024/25 | 166,810 | 184,201 | 92,292 | 91,909 / 98,547 (852) | **157.98 (57.66)** | **1.0293** | 28.92 (10.56) | 1.0555 | 1.1262 | −2.62 | 5.46× |
| 2025 → 2025/26 | 150,605 | 143,770 | 143,770 | 0 (no failing unit) | **451.61 (164.84) = the cap; clearing ≡ census** | **0.9546** | 269.92 (98.52) | 1.0049 | 1.0049 | −5.03 | 1.67× |

Uncleared set (the design's failing set) vs the BRA record's uncleared by type
(2024/2025 BRA Report Table 7, RPM-only UCAP, offered − cleared):

| DY | design uncleared firm MW (nameplate) | BRA uncleared UCAP |
|---|---|---|
| 2022/23 | coal 4,121 · gas_cc 2,048 · gas_st 8,802 — total **14,970 (16,099 nameplate)** | coal 6,524 · gas 6,234 · nuclear 5,805 · oil 148 · DR 1,701 — generation total 18,711 |
| 2023/24 | coal 4,121 · gas_cc 2,141 · gas_st 8,802 — **15,064 (16,197)** | coal 5,353 · gas 3,574 · nuclear 0 · oil 81 · DR 2,021 — generation 9,008 |
| 2024/25 | coal 11,729–12,412 (control / D48 ledgers) — **11,729–12,412 (12,748–13,492)** | coal 3,582 · gas 2,225 · nuclear 206 · oil 251 · DR 2,161 — generation 6,264 |
| 2025/26 | none | 8.3 MW (135,692.3 offered vs 135,684.0 cleared) |

Model offers ABOVE the published price (firm MW): 2022/23 **66,235** (coal 7,110 · gas_cc
22,357 · gas_ct 24,244 · gas_st 8,802 · oil 3,723); 2023/24 **64,850**; 2024/25 **79,777**
(coal 32,411 — the whole coal fleet at near-zero 2024 margin). The model stack's marginal
offer AT the published cleared position: 82.81 / 82.81 / 171.72 $/MW-day.

### 2.2 Arm B — HEAD's basis (D48 fields OFF, supply clearing ON)

| screen → DY | `R` | firm | `Q_0` | failing firm / nameplate | **design price $/MW-day ($/kW-yr)** | **design cleared pos** | published price | published cleared pos | Δpos | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022 → 2022/23 | 130,295 | 148,033 | 83,452 | 64,581 / 88,602 | **95.89 (35.00)** | **1.0412** | 50.00 | 1.0510 | −0.98 | 1.92× |
| 2023 → 2023/24 | 128,566 | 146,737 | 85,631 | 61,106 / 84,856 | **95.89 (35.00)** | **1.0423** | 34.13 | 1.0552 | −1.29 | 2.81× |
| 2024 → 2024/25 | 133,371 | 147,103 | 74,010 | 73,093 / 98,547 | **175.11 (63.91)** | **1.0256** | 28.92 | 1.0555 | −3.00 | 6.06× |
| 2025 → 2025/26 | 144,632 | 137,686 | 137,686 | 0 | **451.61 (164.84) = cap; ≡ census** | **0.9520** | 269.92 | 1.0049 | −5.29 | 1.67× |

Uncleared (HEAD basis): 2022/23 coal 1,014 · gas_cc 1,598 · gas_ct 2,785 · gas_st 6,909 —
12,307 firm (17,488 nameplate); 2023/24 coal 1,014 · gas_cc 1,671 · gas_ct 3,116 · gas_st
6,909 — 12,710 (18,137); 2024/25 coal 9,829 (11,842). On the ELCC basis the CT plateau moves
to 95.9 $/MW-day (21 ÷ 0.60) and becomes the marginal offer, which is why arm B's price is
$95.89 and part of the CT fleet is uncleared there where arm A clears it.

### 2.3 Tolerances (pre-stated; graded HIT / SPLIT / MISS)

- **P1 — cleared position.** Arm A within **±1.5 pts** of the published cleared position in
  2022/23 and 2023/24 and within **±3.5 pts** in 2024/25; arm B within ±2.0 / ±2.0 / ±4.0.
  The design's cleared quantity is expected to land BELOW the published cleared position in
  every long year (the model's stack above the curve is larger than the record's), and
  within the offered–cleared band (1.05–1.22) everywhere.
- **P2 — price sign and band.** In every long year (2022/23–2024/25) the design's price is
  **> $0** (the census control) and **> the published price** — arm A by 1.4–2.0× in
  2022/23 and 2023/24 and by 4–7× in 2024/25; arm B by 1.6–2.3× and 5–8×. The price is set
  by a MARGINAL OFFER (design §3.4 rule 4), not by the curve between offers, in every long
  year — i.e. the build's ledger `how` reads `marginal_offer_sets_price`.
- **P3 — the 2025 identity.** No unit fails the 2025 screen in the control (D48 §3.1); if
  that holds in the arms' entering 2025 fleet the clearing reduces to the census evaluation
  and the 2025 ledger row is byte-identical in price and position to the control's census
  values on the same entering fleet — the design's I1 exercised on a live year. (The
  entering fleet itself differs by the 2022–2024 decisions — §3.)
- **P4 — the identity I2.** Failing set ≡ uncleared set in every solved screen, marginal
  unit excepted; the ledger's `entry_capped + decided` nameplate equals the uncleared
  nameplate of §2.1 / §2.2 to within one unit.
- **P5 — the uncleared composition vs the record (direction only, no band).** The design's
  uncleared set is coal-and-steam where the record's is coal-and-gas: gas_st **over-
  represented** (8.8 GW firm uncleared vs the record's total gas uncleared of 6.2 / 3.6 /
  2.2 GW), coal **under-represented** in 2022/23–2023/24 (4.1 vs 6.5 / 5.4 GW) and
  **over-represented** in 2024/25 (11.7–12.4 vs 3.6 GW), nuclear absent (the MOPR
  artifact, design §2 item 6). These are the E&AS operand's signature (design §6 item 1)
  and are reported at full magnitude, not banded.

## 3. Expected FC-3 consequence (the A/B, graded in the build's finding)

Read off §2 and the pipeline's own rules (worst-first depth admission, cheapest-firm
retention, coal lag 3 / gas_st lag 1 / gas_cc lag 1), against the control `pjm-t1h`
(17.958 GW total; coal 16.990 = economic 11.415 + announced 4.551 + derates 1.023; gas_st
0.833 announced; recall 17/20; `false_retire` 6.691) and the D48 arm (19.361; coal economic
12.818; `false_retire` 8.094):

- **P6 — the decision cohort shrinks by an order of magnitude.** The 2022 screen's candidate
  pool falls from 88.6 GW nameplate failing at $0 to the uncleared **16.1 GW** (arm A) /
  **17.5 GW** (arm B). The admission cap (design §4.1) trims it toward the D48 arm's
  realised firm budget (~11.8 GW firm ≈ 12–13 GW nameplate): expected `decided` **10–16 GW**
  nameplate in the 2022 screen, `entry_capped` **0–6 GW** (vs 77 GW in the control).
- **P7 — coal economic exits DOWN, toward the record.** The uncleared coal is 4.1 GW firm
  (arm A) / 1.0 GW (arm B) in 2022 → coal economic **2.5–5.0 GW** (arm A) / **0.8–2.5 GW**
  (arm B) executed in 2024, against 11.4 (control) / 12.8 (D48 arm). Coal total (with the
  4.55 GW announced + 1.02 derates) **8–11 GW** vs actual 10.3. The D48 arm's +1.4 GW
  cap-admitted coal is retained (the D48 §3.3(d) reading, confirmed or refuted here).
- **P8 — gas steam economic exits UP, past the record (the rule-14 sign that reads
  against the design).** gas_st uncleared 8.8 GW firm (9.5 GW nameplate) in 2022, admitted
  after coal by depth and retained by the floor only after gas_cc: gas_st economic
  **4–9 GW** executed in 2023 (lag 1) vs 0 in every prior arm and 2.7 GW actual (all
  announced-class in the record). gas_cc economic 0–2.2 GW (arm A) — the floor retains it
  first ($31.6/firm-kW-yr), so most of its 2.2 GW is `entry_capped`; gas_ct 0 (arm A,
  cleared at $82.81) / 0–3 GW (arm B, part of the plateau uncleared at $95.89).
- **P9 — totals and gates.** `retire.total_gw` **14–21 GW** (arm A; central ~17) against
  15.06 actual — the band may PASS on the total while the COMPOSITION is wrong (coal
  under, steam over); `unit_recall_gt300` **DOWN**, 9–15/20 (the 20 large targets are
  coal-heavy and only the zero-E&AS coal exits — the D45 L4 lesson at a less extreme
  price); `false_retire` **5–11 GW** (coal false-retire falls, steam false-retire rises);
  determination stays **HOLD** (FC-3 FAIL) in both arms — this design is not expected to
  flip the PJM T1-H gate, and says so.
- **P10 — 2025.** The entering 2025 fleet keeps ~7–8 GW more coal (×0.83 ELCC) and loses
  ~5–8 GW of gas steam (×0.73) relative to the D48 arm: net firm **−1 to +3 GW**, entering
  position **0.95–0.99** (still SHORT, on the cap segment), curve at or near the cap
  ($150–165/kW-yr), the 2025 gas_ct backstop **0.5–1.1 GW** (1,012.8 MW in every prior
  arm; smaller if the position rises). Additions otherwise byte-identical to the control in
  2022–2024 (the entry screen's capacity term is $30–58/kW-yr instead of $0 — no thermal
  candidate crosses its LCOE at that level; `add.by_tech` unchanged; storage entry may
  gain ≤ 0.2 GW from the non-zero RA value).
- **P11 — LOYO (rule 22).** A zero-parameter mechanism: the scorer-side sign test of D48 P9
  on |design position − published cleared| per fold; expected: every fold moves TOWARD the
  cleared quantity relative to the census control (+8.5 / +4.1 / −4.3 pts → −0.7 / −1.0 /
  −2.6 / −5.0), i.e. the residual improves in every fold. This is NOT a fit; it is the
  design doing what the market does.
- **P12 — wall / memory.** Two PJM T1-H legs, 15–25 min and 9.5–10.5 GB each, solo, years
  sequential; the clearing adds one sort per screen year, < 1 s.

## 4. The falsifier (fixed here, before any code)

A build is **refused as tuned** if any arm's clearing price lands within **±20 %** of the
published price in any of 2022/23–2024/25 while the instrument above says the committed
operands produce 1.4–8× — unless the move is traced to a NAMED operand change with its own
identification (a peaker/steam E&AS repair from the D12 scarcity-basis lane; a bar
re-identification from source data under rule 23; the three-year offset of design §4.8),
re-declared in its own PREDECL before the solve. A price that moves because a coefficient
moved is the answer key, not the mechanism. Conversely the design is **not** refused for
missing the published price: the miss is the measurement. And it is refused as **wired
wrong** (not tuned) if P3 or P4 fails.

## 5. What changes if D48's result changes, and what does not

D48 landed (Phase 1, 2026-09-04) with HOLD and the recommendation to arm its two fields
only together with this mechanism. That changes nothing in the design's §3–§4 (the
operands are byte-identical across bases, D48 §3.3(a)); it fixes the A/B's primary arm as
the joint configuration (arm A) and adds arm B as the isolating control. If the owner
declines D48's fields outright before the build, arm B becomes the primary arm and §2.2 the
governing table; if the owner arms them, arm A. If D53 (the sector gate) lands first, its
gated units enter `Q_0` and §2's failing pools shrink to the merchant subset — the build
re-runs the committed instrument on D53's ledgers and re-declares §2 before solving.

## 6. Records this lane commits

`docs/handoffs/DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`, this document, and
`docs/handoffs/d54/clearing-predecl-2026-09-05.py` / `-headbasis-2026-09-05.py` with their
`.json` and stdout `.txt`. Nothing else: no code, no field, no matrix row, no solve, no
registration, no keeper / shard / marker.
