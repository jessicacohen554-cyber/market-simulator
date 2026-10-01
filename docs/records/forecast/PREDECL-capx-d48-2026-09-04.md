# PRE-DECLARATION — capx D48: the PJM accreditation-design devintage + DR-as-supply A/B (D45 §2.3 items 1–2)

**Pushed BEFORE any solve.** Graded at full magnitude, misses included, in
`FINDING-capx-d48-<date>.md` §7 (Phase 1). Phase 1 is GATED: the A/B's
control is D45-R's bare `pjm-t1h` (HEAD replay, key `c6091bd5b62bbc3f`), and
at this push `origin/main` (`f71031f5`) still carries the D45 L1 record
(`pjm-2021-2025-realized-t1h-d45`, key `ea767a6254b8e4af`) under `pjm-t1h` and
no `pjm-t1h-d45r-fixed` — so **no solve was launched in Phase 0**, by charter.

**Lane:** capx D48 — the PJM per-ISO repair lane D45's §2.2/§2.3 identified
with published sources and zero free parameters (D45's §9 close-out, written
by D45-R, names it as successor work). Branch
`claude/capx-d48-pjm-accreditation-devintage-asnklu`, fresh off `origin/main`.
**NOTHING ARMS.** Two `ScenarioConfig` fields land DEFAULT-OFF
(`pjm_accreditation_design_vintage`, `pjm_demand_response_supply`), the A/B
arm registers SUFFIXED (`pjm-t1h-d48-devintage`), the bare `pjm-t1h` verdict
key is untouched, no keeper / shard / marker, backcast namespace untouched. The
owner arms or declines on the flip condition in §5.

**Rule 13 / 14 / 21 discipline (binding).** Every value is a published
auction PARAMETER (a market-design input on file at every hindcast
information cutoff — the D42/D44 vintage gate): PJM's CIFP design switch at
delivery year 2025/26 (ER24-99, accepted 2024-01-30), the four pre-CIFP FPRs
already committed in `demand-curve/pjm/pjm.csv` (1.0898 / 1.0868 / 1.0901 /
1.0894), and the BRA reports' own per-delivery-year OFFERED DR UCAP series
(2027/28 BRA Report Table 5, cross-checked per year; committed at
`data/raw/capacity-market/auction-supply/pjm/pjm.csv`). The CLEARED DR rows
and every auction price are committed alongside as validation observables and
enter nothing. Nothing below was sized, tuned or sequenced by any residual;
the two published sign readings of D45 (§2.3: item 1 moves the position
TOWARD the curve, item 2 AWAY from it) are the identification, and where the
consistent construction contradicts D45's restated magnitudes (§3) the
contradiction is stated here, before the solve, not narrated after it.

---

## 0. What is being measured

`pjm_accreditation_design_vintage=True` + `pjm_demand_response_supply=True`
(the arm, ONE leg) vs D45-R's bare `pjm-t1h` (both False — the shipped
posture at HEAD, fossil dates ON per Q30/D44). Same recipe otherwise:
`run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025
--vintage 2020 --fuel-variant realized --entry-screen-diagnostics`, plus
`--pjm-accreditation-design-vintage --pjm-demand-response-supply`.

Armed, PJM's adequacy accounting follows the design each delivery year's
auction actually cleared on:

| half | delivery years ≤ 2024/25 (pre-CIFP) | delivery years ≥ 2025/26 (CIFP) |
|---|---|---|
| thermal accreditation (`resolve_thermal_accreditation_basis`) | UCAP = pmax × (1 − EFORd) — Manual 18 §4.2.1 | ELCC class ratings (HEAD's registry, unchanged) |
| pool requirement (`gross_adequacy_requirement_mw`) | published pre-CIFP FPR × peak (`FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO`) | published post-CIFP FPR × peak (HEAD's table, unchanged) |
| Demand Resources (`resolve_demand_response_supply_mw`) | published BRA OFFERED DR UCAP ADDED to the accredited ledger; the peak is NOT netted (`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` bypassed) | same, in-table through 2027/28; hold-last beyond as 7,298.6 / 152,400 × gross requirement |

One seam: `accredited_firm_capacity_mw(config=…, accreditation_year=…)`, so the
CR-1 position, the reliability floor (aggregate test, per-unit retention,
merit key), the reserve-margin backstop (and its new-CT credit), the runner's
ledger `firm_mw` and the per-unit capacity payment
(`capacity_revenue_per_mw_yr`) all move together, or not at all.

## 1. Byte-inertness, keys, guards — measured at this branch's HEAD

| item | value |
|---|---|
| bare `pjm-t1h` recipe key, fields at default | **`c6091bd5b62bbc3f`** |
| same recipe, both fields explicitly `False` | **`c6091bd5b62bbc3f`** (identical) |
| D45-R's pre-declared bare `pjm-t1h` key (`PREDECL-capx-d45r-2026-09-04.md` §1.1) | `c6091bd5b62bbc3f` — **match** |
| pinned global default key | `4c6b03ae098b6e3e` — **unmoved** |
| **the A/B arm key** (both fields `True`) | **`bbe13b3f7b659d36`** (no collision with any committed bundle; re-verified at solve time — a later-landing field changes it) |
| vintage-only / DR-only keys (NOT solved; recorded so a future single-field probe is recognisable) | `a0ff4a31b27d2748` / `c79fc92aaaac53cc` |
| `check_cache_key_registration.py --base origin/main` | ok: 2 new fields registered at `"False"` |
| `check_mechanism_matrix.py --base origin/main` | integrity OK; 2 base rows + 12 cells (`--fix-anchors` digits-only repair of the 13-line shift my registrations caused) |
| `validate_parameters.py` | OK (18 new entries) |
| new tests | `TestPjmAccreditationDesignVintage` (7) + `TestPjmDemandResponseSupply` (6) + `test_real_committed_pjm_csv_curates`; other-ISO inertness, backcast coercion, hindcast keep, distinct keys asserted |

Method: `run_capacity_hindcast.build_config` → `apply_iso_scenario_defaults`
→ `ScenarioConfig.cache_key()`, the D45-R path, which reproduces D45-R's own
pre-declared key on the known answer above.

## 2. The prediction — read off the committed D45 L1 ledgers with HEAD's own resolvers (zero-solve)

Instrument: `docs/handoffs/d48/devintage-positions-2026-09-04.py` (+ rows JSON,
stdout). It evaluates the SAME resolvers the solve will use
(`thermal_accreditation_fraction` with config/year threaded,
`resolve_adequacy_requirement_mw`, `resolve_demand_response_supply_mw`, the R2
vintage curves) on the committed `pjm-2021-2025-realized-t1h-d45` ledgers
(the last committed PJM live-posture T1-H; D45-R's HEAD replay differs by the
D44 dates flip, ~7.8 GW of filed exits over 2021–2025, and had not landed).
Entering fleets (`fleet_by_fuel_before`) at class EFORd; VRE / hydro / storage
/ tie on HEAD's ledger basis (these are NOT devintaged — see §3). OFF
reproduces the ledger's own `capacity_reserve_position` to +0.15 pt (2023) /
+0.65 pt (2024): a class-EFORd reconstruction, stated.

**Entering position, requirement and curve price per screen year** (BOTH = the A/B posture)

| screen | arm | thermal firm | DR counted | firm | requirement | **position** | $curve | published cleared / offered | zero-cross | exit budget (firm − req) |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 2022 (bridge; 2021 fleet, 2021 peak) | OFF | 137,574 | 0 | 148,553 | 130,295 | 1.140 | $0 | 1.051 / 1.220 | 1.066 | +18,257 |
| | V only | 164,364 | 0 | 175,342 | 156,126 | 1.123 | $0 | | | +19,216 |
| | D only | 137,574 | 10,513 | 159,066 | 135,677 | 1.172 | $0 | | | +23,389 |
| | **BOTH** | 164,364 | 10,513 | 185,855 | 162,574 | **1.143** | **$0** | | | +23,281 |
| 2023 | OFF | 139,716 | 0 | 150,695 | 128,566 | 1.172 (ledger 1.171) | $0 | 1.055 / 1.141 | 1.065 | +22,129 |
| | V only | 167,115 | 0 | 178,095 | 154,522 | 1.153 | $0 | | | +23,572 |
| | D only | 139,716 | 10,117 | 160,812 | 133,876 | 1.201 | $0 | | | +26,936 |
| | **BOTH** | 167,115 | 10,117 | 188,211 | 160,904 | **1.170** | **$0** | | | +27,307 |
| 2024 | OFF | 140,614 | 0 | 152,473 | 133,371 | 1.143 (ledger 1.137) | $0 | 1.056 / 1.126 | 1.064 | +19,102 |
| | V only | 168,268 | 0 | 180,128 | 160,194 | 1.124 | $0 | | | +19,934 |
| | D only | 140,614 | 10,146 | 162,620 | 138,879 | 1.171 | $0 | | | +23,740 |
| | **BOTH** | 168,268 | 10,146 | 190,274 | 166,810 | **1.141** | **$0** | | | +23,464 |
| 2025 (post-CIFP: V inert by construction) | OFF | 125,560 | 0 | 137,679 | 144,632 | 0.952 (ledger 0.962) | $164.84 (cap) | 1.005 / 1.005 | 1.067 | −6,953 |
| | **BOTH** (= D) | 125,560 | 6,085 | 143,764 | 150,605 | **0.955** | **$164.84** (cap) | | | −6,841 |

**Pre-declared expectations, P1–P9 (each graded in the finding):**

- **P1 — direction of each half (rule 14, D45's signs): CONFIRMED on the
  ledgers before the solve.** The devintage moves the entering position
  DOWN (−1.7 / −1.9 / −1.9 pts in 2022 / 2023 / 2024); DR-as-supply moves it
  UP (+3.2 / +2.9 / +2.8 pts). Expected in the A/B in the same directions.
- **P2 — the two halves nearly cancel; BOTH sits within ±0.3 pt of HEAD in
  2022–2024** (1.143 / 1.170 / 1.141 vs 1.140 / 1.172 / 1.143). This is the
  headline prediction and it CONTRADICTS the charter's "1.077 / 1.077 /
  1.095, 2–4 points past the zero-cross" — §3 states why, with the
  arithmetic. Expected: the A/B's ledger `capacity_reserve_position` in
  2023 / 2024 reads 1.17 ± 0.01 / 1.14 ± 0.01 (D45-R's post-D44 fleet is
  ~1–4 GW smaller in those years, so the absolute level may sit 0.5–2 pts
  lower in BOTH arms alike; the DELTA arm − control is the graded quantity:
  **|Δ| ≤ 0.5 pt**).
- **P3 — capacity revenue direction: $0 → $0 in every 2022–2024 screen**
  (every arm's position is 7–11 pts past its vintage zero-cross). NOT "UP",
  which the charter expected: the pre-declaration says so now. In 2025 the
  curve pays its cap in both arms ($164.84, position 0.95–0.96).
- **P4 — exit direction: UNCHANGED, not HARDER.** With a $0 capacity leg in
  both arms, the 2022 decision cohort (18,137 MW coal decided; 93.6 GW
  fossil failing-but-capped) is re-tested identically; the zero-solve
  re-screen at each arm's own position passes **0 MW** in every arm. The
  reliability floor cannot bind more (exit budgets GROW: +5.0 / +5.2 / +4.4
  GW in 2022–2024 under BOTH). Expected FC-3 rows (`retire.total_gw`, by
  fuel, `unit_recall_gt300`, `false_retire`): **byte-identical or within
  the D44 noise** to the control. G3 is expected to read the SAME, not
  worse — the rule-14 "worse G3" signature the charter anticipated does not
  arise because the mechanism does not reach the price.
- **P5 — entry: unchanged in 2022–2024** (capacity term $0 both arms);
  2025's gas_ct entry (1,012.8 MW in L1) may re-size slightly because the
  D half raises the 2025/26 requirement by +5,973 MW AND adds +6,085 MW of
  DR supply (net +112 MW of budget) — expected |Δ add.gas_ct| < 200 MW.
- **P6 — the ledger fields that DO move, in every year:**
  `adequacy_requirement_mw` (+20 % in 2021–2024 under V: 130.3 → 156.6 GW
  at the 2021 peak; +4.1 % under D in every year incl. 2025+: the netting
  removed), `reserve_margin` (the identity `firm = peak × (1 + rm)`
  includes DR and the UCAP thermal fleet), `capacity_reserve_position` as
  tabled. FC-1 invariants I7 / I12 read the armed requirement and may move
  (I7 `accredited ≥ requirement` is expected to PASS in every year it
  passes today — the budget grows).
- **P7 — forward edge (golden/t1f, NOT solved here):** V is inert for every
  delivery year ≥ 2025/26; D changes the 2026/27–2027/28 requirement by
  +4.1 % and adds the in-table 5,530.6 / 7,298.6 MW, then the 4.79 % held
  ratio — at PJM's own peak the algebra reproduces the netting to within
  the FRR-DR wedge (~0.2 pts). Expected t1f effect if ever armed: < 1 pt
  of position, no $-cap year flips.
- **P8 — wall / memory:** one PJM T1-H solve, ~16–21 min, ~8.8 GB (D45-R's
  L1 measurement); solo per rule 12.
- **P9 — the LOYO (rule 22) on a mechanism with zero free parameters is a
  sign test:** the A/B's per-year |position − published cleared| under BOTH
  vs control, folds over 2021–2025. Expected: the D half degrades every
  fold (position moves AWAY from the cleared quantity), the V half improves
  every fold, BOTH is within ±0.5 pt — **an honest "inert on the residual"
  read**, which under rule 1 is NOT a reason to reject a structurally
  correct basis.

## 3. Why the prediction is NOT D45 §2.2's 1.077 / 1.077 / 1.095 — stated before the solve

D45 §2.2 restated L1's fleet on UCAP (175,788 MW in 2021) and divided by the
**published RTO Reliability Requirement (166,355 MW)**. Three things differ
from the consistent construction the field builds, and together they are
the whole gap:

1. **Peak.** The published requirement is PJM's 50/50 forecast peak
   (152,647 MW, filed three years ahead) × 1.0898; the model's requirement is
   its OWN weather-year peak (149,590 MW in 2021) × 1.0898 = 163,023 MW. The
   model's peak is the rule-13-correct denominator (it responds to load) and
   is 2.0 % lower. Effect: +2.0 pts of position.
2. **DR convention.** D45's ratio put NO DR in the numerator against an
   UN-netted requirement — the net-supply-over-raw-requirement mis-pairing
   the PJM shard's D40 note routed. HEAD nets 3.97 % of the peak from the
   requirement (the V-only arm keeps that: requirement 156,557 MW); the
   consistent raw convention (BOTH) adds the published 11,887 MW of offered
   DR to supply and un-nets the requirement. Effect vs D45's ratio: +7.1 pts
   (11,887 / 166,355) of position.
3. **VRE / hydro basis.** D45 restated wind/solar at Manual 21's 14.7 % /
   38 % and hydro at 0.95 × dispatched nameplate; the field devintages
   THERMAL and the REQUIREMENT only (the charter's two seams). At HEAD's
   ledger credits (wind 0.41, solar 0.106, hydro 0.38 accredited) the
   difference is +447 MW, +0.3 pt — immaterial, and recorded as the
   not-built VRE/storage limb (PJM's VRE ELCC began in 2023/24, not 2025/26,
   so that limb is a separate two-date construction).

So: 1.057 (D45, 2021 post) + 2.0 + 7.1 + 0.3 ≈ 1.15 = BOTH's 1.149. The
charter's "2–4 points past the zero-cross" was the mis-paired reading; the
consistent reading is **7–11 points past it**, i.e. the model's CENSUS
position sits between the market's committed position (1.05, the
(1+RM)/(1+IRM) row) and its OFFERED position (1.13–1.22) — which is exactly
where a census-of-everything-installed should sit, and why the price forms
at the cleared quantity, not at the census (D45 §2.3 item 3, the clearing
half, **explicitly NOT built here** and routed). The devintage is therefore
expected to be structurally correct and numerically near-inert on FC-3 in
2021–2024; its value is that the accounting is now on the auction's own
basis, so the clearing-half lane inherits a position it can clear against.

## 4. FC rows expected to move, and which way

| FC row | expectation (arm vs control) |
|---|---|
| FC-3 `retire.total_gw`, by-fuel, `unit_recall_gt300`, `false_retire` | unchanged (within D44 noise; P4) |
| FC-3 `add.by_tech` | unchanged 2022–2024; gas_ct 2025 |Δ| < 200 MW (P5) |
| FC-1 I7 / I12 (requirement-implied rows) | requirement +20 % (2021–2024) / +4 % (all years); I7 still PASS wherever it passes (P6) |
| ledger `capacity_reserve_position` 2023 / 2024 / 2025 | 1.17 / 1.14 / 0.955 ± 0.01 (P2) |
| ledger `adequacy_requirement_mw` 2023 / 2024 / 2025 | 160.9 / 166.8 / 150.6 GW at L1's peaks (P6) |
| capacity term in `entry_screen_diagnostics` | $0 in 2022–2024 both arms; 2025 cap both arms (P3) |
| FC-2 / FC-4 / FC-5 / FC-6 | not reached by the mechanism; expected byte-identical |

## 5. Arming recommendation — the pre-stated flip condition (P9-style)

The lane will RECOMMEND ARMING `pjm_accreditation_design_vintage` as the PJM
hindcast default (and leave `pjm_demand_response_supply` to the owner as a
convention choice) iff ALL of: (a) the A/B keys at its pre-declared key and
every FC-3 row is within the D44 noise of the control (P4 — the mechanism
must not be found to reach the price through a path this pre-declaration did
not name); (b) the requirement and position rows land within P2/P6's bands;
(c) no LOYO fold of the V half degrades the position residual (P9). If (a)
fails — i.e. FC-3 moves — the finding stops and routes: a position-neutral
basis change that moves exits means a second mechanism is reading the ledger
(the floor's merit key or the backstop), and that is diagnosed, never
absorbed. The default flip is an OWNER decision either way; this lane only
recommends.

## 6. What Phase 1 registers (frozen)

`pjm-2021-2025-realized-t1h-d48-devintage` → suffixed **`pjm-t1h-d48-devintage`**
(never the bare key), scored `forecast_verdict.py --tier t1h` like-for-like
against D45-R's `pjm-t1h`, LOYO within 2021–2025 (P9), the finding
`FINDING-capx-d48-<date>.md` with the position table on both bases, the
decomposition (V / D / BOTH on the D45-R ledgers via the §2 instrument), every
FC row that moved, D45 §2.3 item 3 explicitly routed, and the PJM shard cell
re-stamped. STOP conditions: key ≠ `bbe13b3f7b659d36` unexplained; any
collision; anything beyond the suffixed key and the PJM shard moving.
