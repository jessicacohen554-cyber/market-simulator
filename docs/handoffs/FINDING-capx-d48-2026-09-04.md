# FINDING — capx D48 Phase 1: the PJM accreditation-design devintage + DR-as-supply A/B (D45 §2.3 items 1–2), measured

**Lane:** capx D48 Phase 1 (Fable; rule-14 sign adjudication). Phase 0 (PR #4707,
`d850eac1`) landed the two DEFAULT-OFF `ScenarioConfig` gates, the DR intake, the
matrix rows and `docs/handoffs/PREDECL-capx-d48-2026-09-04.md`. This finding grades
that pre-declaration at full magnitude (§7) after ONE solve: the A/B arm
`pjm-2021-2025-realized-t1h-d48-devintage` (both fields ON) against D45-R's bare
`pjm-t1h` (`pjm-2021-2025-realized-t1h-d45r`, key `c6091bd5b62bbc3f`, both fields
absent = OFF). **NOTHING ARMS.** The arm registers SUFFIXED as `pjm-t1h-d48-devintage`;
the bare `pjm-t1h` verdict key, every keeper / shard / marker and the backcast namespace
are untouched. The arming recommendation (§8) returns to the owner on the §5 flip
condition the pre-declaration fixed before the solve — and that condition **fails on
its limb (a)**, so this finding STOPS and ROUTES exactly as §5 said it would.

**Gate (verified on `origin/main` `8f5cb32c` before anything ran):**
`ff-verdicts.json[pjm-t1h].provenance.run_id == pjm-2021-2025-realized-t1h-d45r`
(cache_epoch `c6091bd5b62bbc3f`) and `pjm-t1h-d45r-fixed` present — both true.

---

## 0. Verdict (one paragraph)

The devintage does exactly what its pre-declaration said it would do to the
accounting — the ledger requirement rows land on the instrument's numbers to the MW
(160,904 / 166,810 / 150,605 MW in 2023 / 2024 / 2025), the entering CR-1 position moves
by +0.10 / +0.26 pt (P2's ±0.5 pt band), the curve pays $0 / $0 / cap in both arms and
every entry-screen capacity term and every addition is byte-identical (P3, P5 HIT). But
**FC-3 moved**: `retire.total_gw` 17.958 → 19.361 GW (+1.403 GW, all economic coal),
`false_retire` 6.691 → 8.094 GW, recall 17/20 unchanged — with every screen candidate's
net revenue, going-forward cost and capacity leg byte-identical between the arms. The
mover is the one the pre-declaration's §5 named and its P4 reasoned past: the pipeline
**admission cap** (`_apply_reliability_floor` at the cap horizon) is a firm-MW budget,
`accredited(cap fleet) − requirement`, that a position-neutral basis change does NOT
leave neutral (both sides scale ×1.25: +5.0 GW at the entering 2022 fleet, +1.2 GW at the
2024 cap horizon), and its $/firm-MW merit key re-ranks the coal cohort on per-unit
1 − EFORd instead of one class rating (38 coal units swap, net +1,403 MW admitted in the
2022 screen, executed in 2024). The zero-solve decomposition (§2) attributes almost all
of the budget growth to the **DR half** (+5.1 GW) and almost none to the accreditation
half (+0.9 GW). Reading (rule 14): a structurally correct basis over the still-unrepaired
$0 clearing half — the published curve at the published cleared position pays
$15–21/kW-yr — makes G3 read worse, which is the expected signature, not a defect in the
devintage; but the §5 condition (a) fails as written, so **the lane does not recommend
arming now** and routes the recommendation together with D45 §2.3 item 3 (the clearing
half, explicitly NOT built here). Determination on the suffixed key: HOLD (FC-3 FAIL),
unchanged from the control.

## 1. Keys, environment, cost — measured before and after the solve

| item | pre-declared | realized |
|---|---|---|
| bare `pjm-t1h` recipe key (control, fields absent/False) | `c6091bd5b62bbc3f` | `c6091bd5b62bbc3f` (re-resolved at HEAD `8f5cb32c` and again after the rebase onto `1cde85df`, via `build_config` → `apply_iso_scenario_defaults` → `cache_key()`) |
| A/B arm key (both fields True) | `bbe13b3f7b659d36` | `bbe13b3f7b659d36` — **match** (`run_scenario_iso start … cache_key=bbe13b3f7b659d36`); no collision with any committed bundle (grep over `results/`, `frontend/`, `docs/`: the only prior occurrence is the pre-declaration itself) |
| single-field keys (recorded, NOT solved) | `a0ff4a31b27d2748` (V) / `c79fc92aaaac53cc` (D) | same |
| posture in the resolved arm config | `fossil_announced_exits_enabled=True`, `hindcast_verified_announced_exits=True`, `entry_screen_diagnostics=True`, `capacity_market_clearing_by_iso[PJM]=True` (shipped) | verified in the launch banner; solved [2021, 2023, 2024, 2025], bridged [2022], SOLVE-YEAR PARITY held, no leakage-guard violation |
| wall / peak RSS | ~16–21 min / ~8.8 GB (P8) | **14.7 min / 9.85 GB** (solo, 4 cores / 15 GB / no swap) |

No field landed on `origin/main` between Phase 0 and this solve that moves either key
(the bare key still reproduces D45-R's pre-declared value — the known-answer check on the
resolution path — and the one merge that landed mid-session, nyiso-188, touched no `src/`).

**Environment (stated, not absorbed):** full clone with `data/raw` present; `data/clean`
ABSENT at session start. `uv sync`, then the five partitions the solve's capacity-market
seams read were curated first (`confirmed-retirements`, `capacity-market-auction-supply`,
`-auction-price`, `capacity-deliverability`, `capacity-market-demand-curve`), then the
full `regenerate_clean.py` tree (54 datatypes, ~65 min, 0 failures) so the arm is solved
on the SAME input surface D45-R's control was — a partial clean tree can silently change a
loader's fallback and confound a one-field A/B. There is no separate "input-readiness
check" in the harness beyond the pre-solve forward-driver guard, which passed.

## 2. The zero-solve decomposition, refreshed on D45-R's ledgers (post-D44 fleet)

Instrument: `docs/handoffs/d48/devintage-positions-2026-09-04.py`, re-run on
`pjm-2021-2025-realized-t1h-d45r` (outputs `devintage-positions-d45r-2026-09-04.json` /
`-stdout-…txt` beside the Phase-0 run on the D45 L1 ledgers). Same construction as
PREDECL §2: entering fleet (`fleet_by_fuel_before`) at class EFORd; VRE / hydro /
storage / tie on the ledger basis; four arms OFF / V (devintage only) / D (DR-as-supply
only) / BOTH. OFF reproduces the ledger's own `capacity_reserve_position` to +0.15 pt
(2023) / +0.66 pt (2024) — a class-EFORd reconstruction, stated.

| screen | arm | thermal firm | DR | firm | requirement | **position** | Δ vs OFF (pts) | $curve | published cleared / offered | zero-cross | exit budget (firm − req) | Δ budget |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 2022 (bridge; 2021 fleet + peak) | OFF | 137,055 | 0 | 148,033 | 130,295 | 1.1361 | — | $0 | 1.051 / 1.220 | 1.066 | +17,738 | — |
| | V | 163,772 | 0 | 174,750 | 156,126 | 1.1193 | −1.68 | $0 | | | +18,624 | **+886** |
| | D | 137,055 | 10,513 | 158,546 | 135,677 | 1.1686 | +3.25 | $0 | | | +22,869 | **+5,132** |
| | **BOTH** | 163,772 | 10,513 | 185,263 | 162,574 | **1.1396** | **+0.35** | $0 | | | +22,689 | +4,951 |
| 2023 | OFF | 135,757 | 0 | 146,737 | 128,566 | 1.1413 (ledger 1.1398) | — | $0 | 1.055 / 1.141 | 1.065 | +18,170 | — |
| | V | 162,702 | 0 | 173,681 | 154,522 | 1.1240 | −1.73 | $0 | | | +19,159 | +989 |
| | D | 135,757 | 10,117 | 156,853 | 133,876 | 1.1716 | +3.03 | $0 | | | +22,977 | +4,807 |
| | **BOTH** | 162,702 | 10,117 | 183,798 | 160,904 | **1.1423** | **+0.10** | $0 | | | +22,894 | +4,724 |
| 2024 | OFF | 135,244 | 0 | 147,103 | 133,371 | 1.1030 (ledger 1.0964) | — | $0 | 1.056 / 1.126 | 1.064 | +13,732 | — |
| | V | 162,195 | 0 | 174,054 | 160,194 | 1.0865 | −1.65 | $0 | | | +13,860 | +128 |
| | D | 135,244 | 10,146 | 157,249 | 138,879 | 1.1323 | +2.93 | $0 | | | +18,370 | +4,638 |
| | **BOTH** | 162,195 | 10,146 | 184,201 | 166,810 | **1.1043** | **+0.13** | $0 | | | +17,391 | +3,659 |
| 2025 (post-CIFP: V inert) | OFF | 125,567 | 0 | 137,686 | 144,632 | 0.9520 (ledger 0.9617) | — | $164.84 (cap) | 1.005 / 1.005 | 1.067 | −6,946 | — |
| | **BOTH** (= D) | 125,567 | 6,085 | 143,770 | 150,605 | **0.9546** | **+0.26** | $164.84 (cap) | | | −6,835 | +111 |

Three readings, all stated before the solve's numbers are read against them:

1. The two halves' signs and magnitudes are fleet-independent to the decimal (Phase-0 on
   the D45 L1 fleet: V −1.7 / D +3.0; here V −1.65…−1.73 / D +2.93…+3.25), so BOTH is
   within +0.10…+0.35 pt of OFF in every pre-CIFP screen and every arm stays 3–9 pts past
   its vintage zero-cross — the curve is $0 whatever the basis.
2. **The exit budget is NOT position-neutral, and the growth is the D half's.** BOTH
   enlarges `firm − requirement` by +3.7…+5.0 GW, of which V contributes +0.1…+1.0 GW and D
   +4.6…+5.1 GW: the offered-DR series adds ~10.1–10.5 GW of counted supply against a
   requirement un-netting of only ~5.4 GW (3.97 % of peak). The pre-declaration tabulated
   this growth and read it as "the floor cannot bind more" (P4) — true of the floor's
   retention verb, false of its admission verb (§3.3).
3. The zero-solve re-screen at each arm's own position passes **0 MW** of the failing pool
   in every arm (88,602 MW in 2022 / 73,441 in 2023 / 87,132 in 2024 — smaller than the
   D45 L1 pools because the dated plants are exempt, D45 §4.0): the screen economics
   cannot move under a $0 leg, so anything that moves FC-3 is downstream of the screen.

## 3. What the solve measured — the A/B on the live stack

Instrument: `docs/handoffs/d48/ab-compare-2026-09-04.py` (+ `.json`, `-stdout-…txt`),
read entirely off the two committed bundles.

### 3.1 The ledger rows (both arms, the D45 observability keys)

| year | arm | peak | `capacity_reserve_position` (entering) | `adequacy_requirement_mw` | `reserve_margin` (post-evolution) | implied firm after | gap to published cleared (pts) |
|---|---|---:|---:|---:|---:|---:|---:|
| 2021 (seed) | control | 149,590 | — | 130,295 | −0.0104 | 148,040 | — |
| | **arm** | 149,590 | — | **163,023** | **+0.2477** | **186,643** | — |
| 2023 | control | 147,605 | 1.1398 | 128,566 | −0.0093 | 146,228 | +8.46 |
| | **arm** | 147,605 | **1.1408** | **160,904** | **+0.2418** | **183,296** | +8.56 |
| 2024 | control | 153,121 | 1.0964 | 133,371 | −0.1025 | 137,426 | +4.09 |
| | **arm** | 153,121 | **1.0990** | **166,810** | **+0.1245** | **172,183** | +4.35 |
| 2025 | control | 160,560 | 0.9617 | 144,632 | −0.1405 | 138,009 | −4.32 |
| | **arm** | 160,560 | **0.9566** | **150,605** | **−0.1098** | **142,929** | −4.83 |

The requirement rows are the instrument's to the MW (P6 HIT). The 2021 post-evolution firm
(186,643) is the instrument's BOTH firm (186,637) to 6 MW — the class-EFORd reconstruction
is validated on the seed year, where the fleets are identical. The 2025 position moves
−0.51 pt where the instrument said +0.26: the arm ENTERS 2025 with 1.4 GW less coal (§3.2),
so the P4 miss propagates into the last screen year.

### 3.2 FC-3 — the rows that moved (arm vs control; everything else byte-identical)

| row | control (`pjm-t1h`) | **arm** | actual |
|---|---:|---:|---:|
| `retire.total_gw` | 17.958 (+19.2 %, FAIL) | **19.361 (+28.5 %, FAIL)** | 15.062 |
| coal (all channels) | 16.990 | **18.393** | 10.299 |
| coal — economic / announced / derates | 11.415 / 4.551 / 1.023 | **12.818** / 4.551 / 1.023 | — |
| gas_st / gas_cc / oil / gas_ct / biomass | 0.833 / 0.075 / 0.051 / 0 / 0.009 | identical | 2.702 / 0.434 / 0.613 / 0.808 / 0.207 |
| `unit_recall_gt300` | 17/20 = 0.85 PASS | **17/20 = 0.85 PASS** | — |
| plant-exact recall (report-only) | 14/20 | 14/20 | — |
| `false_retire` | 6.691 GW (0.373) FAIL | **8.094 GW (0.418) FAIL** | — |
| LOYO −2023 / −2024 / −2025 recall | 12/12 / 8/19 / 16/19 | **identical** | — |
| LOYO −2023 / −2024 / −2025 false-retire | 8.09 / 0.0 / 6.795 | **9.493 / 0.0 / 8.198** | — |
| additions wind / solar / gas_cc / gas_ct / storage | 3.0 / 9.762 / 8.118 / 1.013 / 0.0 | **identical to the decimal** (2025 gas_ct backstop 1,012.8 MW fires in both) | — |
| system CO2 2023 / 2024 / 2025 (Mt, report-only) | 274.9 / 259.6 / 291.2 | 274.9 / 259.8 / **287.5** | — |
| determination | HOLD (FC-3 FAIL, FC-7 CAVEAT) | **HOLD (FC-3 FAIL, FC-7 CAVEAT)** | — |

The whole delta is ONE event: the 2022 screen (the bridge year's screen on the 2021
dispatch) decides 61 coal units / 12,818 MW in the arm where the control decides 47 /
11,415 MW; both cohorts re-confirm in 2023 and execute in 2024 (coal lag 3). Nothing else
in the pipeline differs — dated exits, derates, the 2025 backstop, every addition.

### 3.3 Why — the admission cap is the second mechanism, diagnosed (PREDECL §5)

Instrument: `docs/handoffs/d48/admission-cap-budget-2026-09-04.py` (+ `.json`,
`-stdout-…txt`).

**(a) The screen economics are byte-identical.** Every one of the 1,211 candidate rows in
the 2022 screen has the same `net_revenue_usd`, `going_forward_cost_usd` and
`capacity_revenue_usd` (all $0) in both arms; the same 88,602 MW fails the bar. The
capacity leg the screen prices is $0 in both arms in 2022–2024 (§3.1: 3–9 pts past the
zero-cross either way) and the 2025/26 cap in both. **The price never moved.**

**(b) What moved is admission.** `_apply_pipeline_retirements` sizes the decision cohort by
calling the reliability floor at the cap horizon on the counterfactual fleet with the WHOLE
scheduled exit set removed, retaining candidates cheapest-firm-first until
`accredited ≥ requirement`. The admitted set therefore carries, on the arm's own basis,
firm MW ≈ `accredited(cap fleet) − requirement(cap_year, cap_peak)` — a **firm-MW budget**,
and both of its terms are on the devintaged seam:

| | control (ELCC-class + composite requirement) | **arm (UCAP + published FPR, DR counted)** | Δ |
|---|---:|---:|---:|
| cap horizon | 2024 (coal lag 3), peak 160,554 (2021 peak × 1.036²) | same | — |
| entering 2022: firm / requirement / budget | 148,033 / 130,295 / **17,738** | 185,263 / 162,574 / **22,689** | **+4,951** |
| at the cap horizon (dated 2022–2024 exits netted, D42): firm / requirement / budget | 143,538 / 139,845 / 3,692 | 179,810 / 174,908 / 4,902 | **+1,210** |
| position at the cap horizon | 1.0264 | 1.0280 | +0.16 pt |
| admitted (decided) coal | 11,415 MW (47 units) | **12,818 MW (61 units)** | **+1,403 MW** |
| admitted firm on own basis (class fraction 0.830 ELCC / 0.920 UCAP) | 9,474 | ~11,793 (upper bound: the arm admits the HIGH-EFORd units, whose per-unit UCAP is below the class value) | +1.4…+2.3 GW |

The reconstruction's ABSOLUTE level at the cap horizon under-reads the cap's real ledger
(the control admitted 9.5 GW of firm against a reconstructed budget of 3.7 GW — the
runner's per-unit fleet, its pools and its `peak_demand_used` are not reproduced at the
MW here); the DELTA is the graded quantity, as in §2, and its sign and order of magnitude
(+1.2 GW of budget → +1.4 GW of admitted nameplate at ~0.9 firm/MW) are consistent.
**Position-neutral is not budget-neutral**: the arm's position is +0.16 pt at the cap
horizon and +0.35 pt entering, while the budget in MW grows 7 % (entering, +5.0 GW)
because both sides scale by ~×1.25 and the DR half adds more supply than un-netted
requirement (§2 reading 2).

**(c) The merit key re-ranks the cohort.** `_floor_retention_merit` sorts candidates by
going-forward cost per FIRM MW, where firm = `_thermal_firm_mw` = pmax ×
`thermal_accreditation_fraction(…, config, year)` — the devintaged resolver. Under HEAD's
basis every coal unit gets the SAME class ELCC rating, so within coal the key collapses to
$58.5/kW-yr ÷ 0.830 for every unit and the order falls to the CO2 and heat-rate
tie-breaks; under UCAP the denominator is each unit's own 1 − EFORd, so the order is by
EFORd first. Result: **38 coal units swap** (5,376 MW `entry_capped → decided`, 3,973 MW
`decided → entry_capped`), every one at the identical $58.5/kW-yr going-forward cost, no
other fuel touched. The arm retains the more reliable coal per dollar and admits the
less reliable — a physically sensible ordering, and one HEAD's single class rating cannot
express.

**(d) What this is and is not.** It is exactly the §5 clause: "a position-neutral basis
change that moves exits means a second mechanism is reading the ledger (the floor's merit
key or the backstop)". The reader is the floor's admission verb, through both its budget
and its merit key; the realized-year floor (retention) binds in neither arm
(`floor_retained` empty in every year), and the backstop is byte-identical. It is not a
defect in the devintage: the cap reading the auction's own basis is rule 19 working
(one seam, `accredited_firm_capacity_mw`, every consumer moves together — the PREDECL
§0's own sentence), and on that basis PJM's adequacy accounting genuinely says ~1.2 GW
more firm capacity can leave by 2024. What makes the row read WORSE is that the cohort it
admits is priced at $0 — the clearing half D45 §2.3 item 3 names, where the published curve
at the published cleared position pays $15–21/kW-yr and D45 §3(a) passes 13.0 of 18.1 GW.
A larger budget under a faithful price would admit exits the price then pays to stay; under
a $0 price it admits exits the price cannot retain. That is the rule-14 signature of a
faithful basis over an unfaithful price, and it is the reason the recommendation is
routed with item 3 rather than absorbed.

### 3.4 Entry, capacity revenue, the backstop

Byte-identical (P3, P5 HIT). Every `entry_screen_diagnostics` row carries
`capacity_revenue_per_mw_yr = 0.0` in 2022–2024 in both arms and the 2025/26 cap
($121.98/kW-yr gas_cc, $98.90 gas_ct) in both; the 2025 reserve-margin backstop fires
1,012.8 MW of gas_ct in both (the arm is 0.5 pt SHORTER entering 2025 after the extra coal
exit, and the ladder-bound backstop sizes identically). The P5 "|Δ add.gas_ct| < 200 MW"
band is met at exactly 0.

## 4. The P9 sign test (rule 22, zero free parameters)

Per-year |position − published cleared| under BOTH vs the control, on the solved
ledgers (folds = the three scored screens):

| fold | control |gap| | arm |gap| | Δ | read |
|---|---:|---:|---:|---|
| 2023 | 8.46 | 8.56 | +0.10 | degrades |
| 2024 | 4.09 | 4.35 | +0.26 | degrades |
| 2025 | 4.32 | 4.83 | +0.51 | degrades (the P4 miss propagating: 1.4 GW less coal enters) |

Decomposed zero-solve (§2, the only place the halves are separable): the **V half moves
TOWARD the cleared quantity in every fold** (−1.65…−1.73 pt), the **D half AWAY in every
fold** (+2.93…+3.25 pt), and BOTH nets +0.10…+0.35 pt away. §5 limb (c) — "no LOYO fold of
the V half degrades the position residual" — HOLDS. BOTH is "within ±0.5 pt" in 2023 / 2024
and at 0.51 in 2025. The residual is inert to the mechanism, as P9 said it would be; the
FC-3 rows are NOT (P4), which is the finding.

## 5. Explicitly NOT built, routed

1. **D45 §2.3 item 3 — the clearing half.** On the auction's own basis the model's
   CENSUS position (§2/§3) still sits between the market's committed position ((1+RM)/(1+IRM)
   ≈ 1.05) and its OFFERED position (1.13–1.22), and the price forms at the CLEARED
   quantity, not at the census — so the curve pays $0 at the census in 2022–2024 under
   every arm while the published curve at the published cleared position pays $15–21/kW-yr
   (D45 §2.1). The faithful representation is "clear the VRR curve against the fleet's
   net-ACR offer stack" (Manual 18 §6 / MSOC; every ingredient — per-unit going-forward cost
   and E&AS margin — is already the retirement screen's own operand). **NOT BUILT HERE**,
   deliberately: it is a second mechanism with its own identification (the BRA reports'
   offered-vs-cleared quantities as validation observables, rule 13) and its own
   pre-declaration; stacking it into this A/B would make the devintage's own sign
   unreadable (rule 19). Routed to the director as the successor PJM lane. §3.3(d) makes it
   the precondition for arming the devintage, not merely its successor: the admission cap
   converts the consistent basis into exits that only a faithful price can retain.
2. **The VRE / storage ELCC devintage** (PREDECL §3 item 3). PJM's VRE ELCC began at
   delivery year 2023/24 (not 2025/26), so wind/solar/storage carry a SEPARATE two-date
   construction (Manual 21 class values 14.7 % / 38 % before 2023/24; ELCC class ratings
   after). At HEAD's ledger credits (wind 0.41, solar 0.106, hydro 0.38 accredited) the
   whole limb is worth +447 MW / +0.3 pt on the 2021 fleet — immaterial to any row here —
   and it is NOT part of either D48 field. Routed as a not-built limb with its own dates.
3. **The DR convention — offered vs cleared.** The D half counts the published OFFERED DR
   UCAP; the BRA reports also publish CLEARED DR, 2.0–2.5 GW lower in 2022/23–2024/25
   (11.9 / 11.1 GW 2021/22 … 10.1 / 8.1 2023/24; D45 §2.3 item 2). §2 shows the D half
   carries almost all of the budget growth that moved FC-3. Counting offered DR is the same
   census-vs-cleared choice on the demand side that the generation census is on the supply
   side; the shipped netting (3.97 % of peak, ~5.9 GW) sits nearer the cleared quantity.
   This is the "convention choice" the PREDECL §5 left to the owner, now with a measured
   consequence attached. A **D-only probe** (key `c79fc92aaaac53cc`) and a **V-only probe**
   (key `a0ff4a31b27d2748`) are the natural next zero-DOF measurements; neither was solved
   (one arm, by charter).
4. **Beyond the table (2028/29+) the DR series holds the last published ratio** (7,298.6 /
   152,400 of the gross requirement, 4.79 %) — the forward-edge convention P7 names; not
   solved in this lane (T1-H only).

## 6. Matrix (rule 28) and registration

- **Registered** `pjm-2021-2025-realized-t1h-d48-devintage` → suffixed
  **`pjm-t1h-d48-devintage`** (`VERDICT_MAP` row; `register_forecast_run.py --bundle`;
  canonical sidecar `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d48-devintage.json`;
  report `docs/hindcast-reports/pjm-2021-2025-realized-t1h-d48-devintage-2026-09-04.md`;
  `ff-verdicts.json` gains the one key, purely additive — 114 insertions, 0 deletions —
  with `provenance.run_id` / `session=capx-D48` and the measured note). Scored
  `forecast_verdict.py --tier t1h --hindcast-score … --run-config …` after
  `score_capacity_hindcast.py --bundle` and `--flip-gate-extras` (the LOYO folds), the
  D45-R sequence. The bare `pjm-t1h` is untouched; the board (`program-status.json`) is
  untouched (a suffixed probe moves no gate row).
- **Committed slim set** (the D45-R / D46 template): `meta.json`, `run_config.json`,
  `forecast_verdict.json`, the five `evolution_<year>.json` ledgers (carved out of
  `.gitignore` per bundle, as D45's were — they are the sole committed evidence for §3),
  `score.json`, the two `screen_signal_diag_*.npz` dumps. Parquets, `config.yaml`,
  `run_config.yaml` and the floor-retention sidecars stay ignored.
- **Matrix:** the PJM shard's `pjm_accreditation_design_vintage` and
  `pjm_demand_response_supply` cells re-stamped with the measured verdict and evidence.
  Letter unchanged — `fc: "O"`, backcast `·` — because the mechanism is neither rejected
  (structurally correct, reproduces its rows) nor inert (FC-3 moved) nor a keeper (the
  owner arms or declines): it is OPEN on a measured record. `check_mechanism_matrix.py
  --base origin/main` green. No other shard touched (rule 25).

## 7. The pre-declaration, graded at full magnitude

| # | prediction | outcome |
|---|---|---|
| P1 | V moves the position DOWN, D UP (rule-14 signs) — confirmed zero-solve before the solve | **HIT** (zero-solve on both fleets: V −1.65…−1.73, D +2.93…+3.25; the solve carries only BOTH, whose +0.10 / +0.26 pt matches the instrument's +0.10 / +0.13) |
| P2 | BOTH within ±0.3 pt of HEAD in 2022–2024; graded |Δ arm − control| ≤ 0.5 pt; absolute 1.17 ± 0.01 / 1.14 ± 0.01 with "0.5–2 pts lower in both arms alike" | **HIT on the delta** (+0.10 / +0.26 pt in 2023 / 2024); **MISS on the absolute qualifier** (1.1408 / 1.0990 — the post-D44 fleet sits 3.0 / 3.8 pts lower than the D45 L1 ledgers, not 0.5–2: D45-R's §4.0 had not landed when the band was written); 2025 −0.51 pt, outside the years the band named, sign opposite to the instrument's +0.26 because of the P4 miss |
| P3 | capacity revenue $0 → $0 in every 2022–2024 screen; 2025 pays the cap in both arms | **HIT** (every `entry_screen_diagnostics` and `pipeline_events` capacity term $0 in 2022–2024 both arms; 2025 $121.98 / $98.90 both) |
| P4 | exit direction UNCHANGED: FC-3 rows byte-identical or within D44 noise; recall SAME; "the floor cannot bind more (budgets GROW)" | **MISS — the headline.** `retire.total_gw` +1.403 GW (17.958 → 19.361; D44 noise was 0.19), coal +1.403, `false_retire` +1.403 GW, LOYO false-retire folds +1.4 GW; recall 17/20 SAME (sub-item HIT). The mechanism is the one §5 named: the floor's ADMISSION verb converts the grown budget into more exits (§3.3); the pre-declaration reasoned only about its RETENTION verb |
| P5 | entry unchanged 2022–2024; 2025 gas_ct |Δ| < 200 MW | **HIT** (identical to the decimal; Δ = 0) |
| P6 | `adequacy_requirement_mw` 160.9 / 166.8 / 150.6 GW; `reserve_margin` identity moves; I7 still PASS wherever it passes | **HIT** on the rows (160,904 / 166,810 / 150,605 exact; rm −0.009 → +0.242 etc.); I7 / I12 **ungradable** (FC-1 SKIPPED at t1h — no invariant record, as on the control) |
| P7 | forward edge (t1f): V inert ≥ 2025/26; D +4.1 % requirement; < 1 pt if ever armed | **not solved** (T1-H lane; ungraded) |
| P8 | ~16–21 min, ~8.8 GB, solo | **SPLIT** — 14.7 min (under the band), **9.85 GB** (MISS by +1.0 GB; D45-R's own L1 measured 9.6, the band was the older D45 estimate) |
| P9 | LOYO as a sign test: D degrades every fold, V improves every fold, BOTH within ±0.5 pt — "inert on the residual" | **HIT on the halves** (zero-solve: D away, V toward, every year); **HIT on BOTH** in 2023 / 2024 (+0.10 / +0.26), 2025 at +0.51 (marginal MISS, P4-driven); the residual IS inert — FC-3 is not, which is P4's miss, not P9's |

**Tally: 4 HITs (P1, P3, P5, P6-rows), 2 SPLITs (P2, P8), 1 MISS (P4), P9 HIT-with-a-marginal,
P7 unsolved. Cache key 1/1.** The one clean miss is the one that matters and it was
pre-named: §5 wrote "if FC-3 moves — a second mechanism is reading the ledger (the floor's
merit key or the backstop)", and P4 in the same document argued the floor could not bind
more because the budget grows. Both were written by the same hand; the second forgot that
the floor has two verbs and that the admission verb reads a bigger budget as room for MORE
exits. The instrument tabulated the +5.0 GW budget growth in its own table and labelled it
"exit budget"; the reading, not the number, was wrong.

## 8. Arming recommendation — on the pre-stated §5 condition

§5 required ALL of (a) key match AND every FC-3 row within the D44 noise of the control;
(b) requirement and position rows within P2/P6's bands; (c) no LOYO fold of the V half
degrading the position residual.

| limb | result |
|---|---|
| (a) key | **match** (`bbe13b3f7b659d36`) |
| (a) FC-3 within D44 noise | **FAILS** — `retire.total_gw` +1.403 GW, `false_retire` +1.403 GW (noise 0.19) |
| (b) requirement / position bands | **holds** (§3.1; the 2025 position at −0.51 pt is outside P2's named years) |
| (c) V half never degrades a fold | **holds** (§4) |

**Recommendation: DO NOT ARM `pjm_accreditation_design_vintage` now, and do not arm
`pjm_demand_response_supply`; route both with D45 §2.3 item 3.** The condition fails on
the limb whose failure §5 pre-committed to "diagnosed, never absorbed", and the diagnosis
(§3.3) says the devintage is structurally right and its FC-3 effect is the admission cap
pricing a consistent budget at an inconsistent $0. Arming it alone would make the
hindcast read worse for a reason the model cannot yet retain against; arming it WITH the
clearing half is the configuration in which the same budget is priced at the published
curve's $15–21/kW-yr and the D45 §3(a) re-screen says most of the cohort then stays.
Two zero-DOF probes would sharpen the owner's choice before that lane lands and are NOT
solved here: V-only (`a0ff4a31b27d2748`; expected: position −1.7 pt toward the cleared
quantity, budget +0.9 GW, FC-3 near the control) and D-only (`c79fc92aaaac53cc`;
expected: the whole +1.4 GW). The default flip remains an OWNER decision either way;
this lane only recommends, and it recommends HOLD.

## 9. Governance attestation

- **Scope.** One solve, pre-declared with its cache key, keeper, posture and predictions
  before launch; realized key matched. **NOTHING ARMS**: both `ScenarioConfig` fields stay
  default-OFF; no parameter value changed (rules 21 / 23); no keeper / shard / marker; the
  backcast namespace untouched; the bare `pjm-t1h` verdict, `program-status.json` and every
  other ISO's records untouched.
- **Rule 22.** Solved {2021, 2023, 2024, 2025}, 2022 bridged (never solved, never read),
  scored 2023–2025; the holdout freeze active and untouched; no marker spent; LOYO is the
  scorer-side sign test of §4 within 2021–2025, no re-solve.
- **Rules 13 / 14.** The published RPM positions and the BRA offered / cleared DR are
  validation observables; nothing targets them; the signs were stated before the solve
  and graded after it, the miss included.
- **Rule 12.** Solo solve; years sequential.
- **Rule 19.** The admission cap reads the same `accredited_firm_capacity_mw` seam as
  every other consumer — no second floor was added and none is proposed; the finding
  diagnoses the existing one.
- **Rule 25.** PJM only; the PJM shard only.
- **Rule 27.** Every file ≥ 300 lines this lane pushes (`register_forecast_run.py`,
  `ff-verdicts.json`, the PJM shard, `run_config.json`, the ledgers, the sidecar, this
  finding) was edited locally and its remote blob fetched back and hash-compared after
  the push.
- **Rule 15.** Registered through `register_forecast_run.py` in the session that produced
  it, on the FORECAST namespace only.
- **Environment cost, stated.** `uv sync` + the full `regenerate_clean.py` (~65 min) before
  the 14.7-min solve.
