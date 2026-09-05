# PRE-DECLARATION ADDENDUM — capx D57: the PJM clearing half, BUILT, on the posture found at HEAD — pushed before any solve

**Lane:** capx D57 (director r#36), the BUILD lane for DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md.
Branch `claude/capx-d57-pjm-clearing-build-gsdypm`, fresh off `origin/main` (`c9f1d26e` at
session start, rebased onto `db057c5d` — four merges landed mid-session: caiso-247, miso-214,
nyiso-190 backcast lanes and PERF-B s3; none touches a PJM forecast surface). Build commit
`4e8877fb` (pushed, blob-verified). This addendum restates PREDECL-capx-d54 §2–§4 on the posture
the build actually found, resolves the two arm keys through the harness path, and fixes the
STOP-4 falsifier — BEFORE the first solve. The D54 pre-declaration is not superseded; every
number in it stands and is graded in the D57 finding alongside the rows added here.

**DATA PROFILE: pjm** (full clone; `data/clean` absent at session start and regenerated in full
from `data/raw` before the solves — the D48 §1 discipline, so both arms and the control ran on
the same input surface).

---

## 0. The posture at HEAD, stated

| item | state at build HEAD | consequence |
|---|---|---|
| **D53** (`retirement_sector_gate`, the merchant/IPP screen partition) | **NOT merged.** `origin/claude/capx-d53-sector-gate-redt3y` exists (merge-base `8f98399b`); `retirement_sector_gate` appears nowhere on `origin/main` | Design §4.7 is not exercised: no sector-gated units enter `Q_0`. The offer stack is the whole screened thermal fleet, exactly as the D54 instrument had it. D53 merging mid-lane cannot move the bare key (its field is default-off and registered); if it merges before the solves, this addendum's keys are re-resolved and re-declared (charter STOP addendum) |
| **D48's two fields** (`pjm_accreditation_design_vintage`, `pjm_demand_response_supply`) | landed, **default OFF** (PR #4707); the bare `pjm-t1h` key is D45-R's | Arm A arms both + supply clearing (the D48 §8 configuration); arm B arms supply clearing alone on HEAD's basis |
| CR-1 curve gate for PJM | shipped ON (`capacity_market_clearing_by_iso["PJM"] = True`) | the supply-clearing predicate's precondition holds in every arm without a flag |
| fossil dates channel (Q30 / D44) | default ON; `hindcast_verified_announced_exits` ON | step 0/1 removes the dated units before the screen; they are absent from the stack (design §3.2 / §4.2) |
| `capacity_deliverability_limits` | OFF in every PJM arm | the `_zone_is_long` $0 settlement branch never fires; the settlement is price-only |
| `retirement_rule` | `pipeline` (the harness default) | the identity §3.5 is read off `pipeline_events` rows (`decided` / `entry_capped` / `re_confirmed` carry `capacity_cleared`) |

## 1. Keys — resolved through the harness path before any solve

Resolution: `run_capacity_hindcast.build_config("PJM", 2021, 2025, "realized", vintage=2020,
entry_screen_diagnostics=True, …)` → `apply_iso_scenario_defaults` → `cache_key()` — the D45-R /
D48 known-answer path.

| leg | posture | key | run id → suffixed verdict key |
|---|---|---|---|
| control | bare `pjm-t1h` at build HEAD (D48 fields OFF, supply clearing OFF) | **`c6091bd5b62bbc3f` — UNMOVED** (D45-R's value; STOP 2 clear; not re-solved — D45-R's rule needs a re-solve only if the key moved) | `pjm-2021-2025-realized-t1h-d45r` → `pjm-t1h` (existing) |
| D48 arm (the fourth cell of the 2×2) | D48 both fields ON, supply clearing OFF | `bbe13b3f7b659d36` (reproduced) | `pjm-t1h-d48-devintage` (existing) |
| **arm A (primary)** | D48 both fields ON + supply clearing ON | **`f0e050e820c1159a`** | `pjm-2021-2025-realized-t1h-d57-clearing` → `pjm-t1h-d57-clearing` |
| arm B (isolating) | D48 fields OFF + supply clearing ON | **`ccee17a4c1563727`** | `pjm-2021-2025-realized-t1h-d57-clearing-headbasis` → `pjm-t1h-d57-clearing-headbasis` |

Neither arm key occurs anywhere under `results/`, `frontend/`, `docs/`, `scripts/` or `src/`
(grep at build HEAD) — no collision with any committed bundle. Every other ISO's default key is
untouched (the field is registered at `"None"`; `check_cache_key_registration.py --base
origin/main` green). Plain-backcast coercion verified by keeper replay: the PJM keeper's
`run_config.json` (`pjm_debugb_inputclock_A`, key `8e59efa3de2e77c2`) re-loads with the field
`None` and the SAME key even when the row is forced `{"PJM": True}` in the file.

## 2. Phase 0 — the instrument reproduced in code (STOP 1 clear, I5)

`docs/handoffs/d57/phase0-reproduction-2026-09-05.{py,json,txt}`: the code's
`clear_capacity_supply_stack` + `capacity_supply_curve` (the registry vintage curves through the
same `MarketDesign.capacity_price_per_firm_mw_yr` seam the solve prices) fed the D54 instrument's
stack off the committed `pjm-t1h` and `pjm-t1h-d48-devintage` ledgers:

| basis | DY | code price $/MW-day | code position | instrument | Δ |
|---|---|---:|---:|---|---|
| D48 (arm A) | 2022/23 · 2023/24 · 2024/25 · 2025/26 | 82.81 · 82.81 · 157.98 · 451.61 (cap) | 1.0445 · 1.0454 · 1.0293 · 0.9546 | identical | **0.000 $ / 0.000 pt in every row** |
| HEAD (arm B) | same | 95.89 · 95.89 · 175.11 · 451.61 | 1.0412 · 1.0423 · 1.0256 · 0.9520 | identical | **0.000 / 0.000** |

Both bundles' ledgers give the same rows (the D48 arm's screen economics are byte-identical to
the control's, D48 §3.3(a)). The one visible difference from the instrument is inside the
whole-unit convention: the code sorts ties by `(offer, unit_id)` while the instrument kept
ledger order, so WHICH coal unit is marginal in 2024/25 differs and the uncleared firm reads
12,482 MW (code) vs 11,729 / 12,412 (instrument) — price and cleared quantity are identical,
as the rule guarantees.

## 3. Construction points the design left implicit — decided, stated, sized

The build re-decides nothing in design §4. Three quantities the zero-solve instrument could
only reconstruct are now the runner's own, and the direction of each difference is fixed here:

1. **`Q_0` is the SCREEN fleet's ledger, not the entering fleet's.** Design §3.2 / §4.2: "a
   unit dated out by step 0/1 is not in the fleet and is absent from the stack". The screen runs
   on the post-step-0/1/2 fleet, so `Q_0 = accredited_firm_capacity_mw(screen fleet, pools, …)
   − Σ A_g` (structural I1 on that fleet), while the ledger's `capacity_reserve_position` and the
   D48 instrument's `firm_mw` (which the D54 instrument's `Q_0` used) are on the ENTERING fleet.
   The gap is the year's step-0/1 exits on the accreditation basis — from the committed
   control ledgers: announced exits of **3,478 MW** nameplate in the 2022 bridge screen (coal
   3,301), **1,796** in 2023 (coal 1,006 · gas_st 790), **244** in 2024, **1** in 2025 — i.e.
   **≈ 2.0 / 1.1 / 0.15 / 0.0 pts** of position on `R` = 162.6 / 160.9 / 166.8 / 150.6 GW.
   Consequence (a fixed curve, a stack shifted left): in 2022/23 and 2023/24 the crossing lands
   slightly further into the stack — **price UP by $0–15 from the instrument's $82.81** (the
   gas_cc upper tail runs to $86.5, the coal tail sits at $78.7–174), **cleared position DOWN by
   ≤ 0.5 pt** — and nothing in 2024/25 (0.15 pt sits inside the coal plateau at $158) or 2025/26
   (short, census). The ledger's new `capacity_clearing.census_position` will read ~2.0 / 1.1 /
   0.15 / 0.0 pts BELOW `capacity_reserve_position` for exactly this reason; both are recorded.
2. **Per-unit firm MW, not the class-EFORd reconstruction.** `A_g = _thermal_firm_mw(g)` is the
   runner's per-unit UCAP (arm A, through DY 2024/25) / ELCC class (arm B, and arm A from
   2025/26); the D48 instrument's `firm_mw` was a class-EFORd reconstruction that D48 §2
   measured at **+0.15 / +0.66 pt** on the position. Same order as item 1, opposite sign in
   the years the runner's fleet is firmer than the class average. Net of items 1–2 the build's
   census position is pre-declared within **±1.0 pt** of the instrument's per year.
3. **The internal-supply ratio in `A_g`.** `A_g` carries `resolve_internal_supply_accounting_ratio`
   so `Q_0 + Σ A_g` is the ledger's own sum for every ISO (rule 19); PJM's ratio is 1.0 — inert
   here, stated so a later MISO lane sees the seam.

Also stated: the marginal unit is paid exactly its cap `GFC − EAS` (indifference by definition;
the rounding guard `_CLEARING_INDIFFERENCE_RTOL = 1e-9` absorbs ~1e-12 of the bar and is not a
parameter); the deliverability `_zone_is_long` branch settles $0 as on the census path and is
never reached in a PJM arm.

## 4. The per-delivery-year pre-declaration — restated on the HEAD posture (P1–P5)

PREDECL-capx-d54 §2's tables stand as the instrument's rows. On the build's own `Q_0` (§3), the
solved arms are pre-declared as:

| DY | published price $/MW-day · cleared pos (observables) | **arm A price** | arm A pos | **arm A ratio** | **arm B price** | arm B pos | arm B ratio |
|---|---|---:|---:|---:|---:|---:|---:|
| 2022/23 | 50.00 · 1.0510 | **82.8–98** | 1.039–1.046 | **1.7–2.0×** | 95.9–110 | 1.036–1.042 | 1.9–2.2× |
| 2023/24 | 34.13 · 1.0552 | **82.8–95** | 1.040–1.046 | **2.4–2.8×** | 95.9–105 | 1.037–1.043 | 2.8–3.1× |
| 2024/25 | 28.92 · 1.0555 | **150–165** | 1.026–1.033 | **5.2–5.7×** | 168–182 | 1.022–1.029 | 5.8–6.3× |
| 2025/26 | 269.92 · 1.0049 | cap (451.61 = 164.84 $/kW-yr) ≡ census | 0.95–0.99 | 1.67× | cap ≡ census | 0.95–0.99 | 1.67× |

- **P1 — cleared position:** arm A within ±1.5 pts of the published cleared position in 2022/23
  and 2023/24, ±3.5 in 2024/25; arm B ±2.0 / ±2.0 / ±4.0; BELOW the published position in every
  long year; inside the offered–cleared band everywhere. (Unchanged from D54.)
- **P2 — price sign, band, and how it forms:** > $0 (the census control) and > the published price
  in every long year, by the ratios above; `capacity_clearing.how` reads
  `marginal_offer_sets_price` in every long year (the marginal unit a gas_cc in 2022/23–2023/24,
  a coal unit in 2024/25) and `all_offers_clear_curve_sets_price` in 2025/26.
- **P3 — the 2025 identity:** no unit fails the 2025 screen in either arm ⇒ every offer $0 ⇒ the
  clearing is the census evaluation on the screen fleet: `cleared_mw == census_mw`, price = the
  cap, `n_uncleared = 0`. (The entering 2025 fleet differs from the control's by the 2022–2024
  decisions — §5.)
- **P4 — the identity I2:** in every solved screen the failing set (`decided` + `entry_capped` +
  `re_confirmed` rows) equals the uncleared set to the unit, marginal unit excepted; every such
  row carries `capacity_cleared: false`, `capacity_revenue_usd: 0.0`; every cleared screened unit
  passes. A single violation is STOP 3 (wired wrong).
- **P5 — uncleared composition (direction only):** gas_st over-represented (~8.8 GW firm in
  2022/23–2023/24 vs the record's total gas uncleared 6.2 / 3.6 GW), coal under-represented
  (~4.1 GW vs 6.5 / 5.4) in 2022/23–2023/24 and over-represented in 2024/25 (~12 GW vs 3.6),
  nuclear absent (the MOPR artifact); gas_ct fully cleared in arm A (the CT plateau at $61.2 sits
  below $82.81) and PARTLY uncleared in arm B (the ELCC-basis plateau at $95.9 IS the marginal
  offer). The E&AS operand's signature, reported at full magnitude.

**The E&AS operand — measured, not moved (rule 21; PREDECL-d54 §4).** The finding will report,
per DY and per fuel, the firm MW of offers ABOVE the published price (instrument: 66.2 / 64.9 /
79.8 GW; gas_ct 24.2, gas_st 8.8, oil 3.7 GW at their FULL bars in every year) and the E&AS margin
per unit that would put the cleared position AND the price on the published pair — a statement
about the operand, never a value applied.

## 5. Expected FC-3 consequence (P6–P12; the build grades every row)

Against the control `pjm-t1h` (retire.total 17.958 GW; coal 16.990 = economic 11.415 + announced
4.551 + derates 1.023; gas_st 0.833 announced; recall 17/20; false_retire 6.691) and the D48 arm
(19.361; coal economic 12.818; false_retire 8.094):

- **P6** the 2022 decision cohort shrinks from ~88.6 GW nameplate failing at $0 to the uncleared
  set (**~16 GW** arm A / **~17.5 GW** arm B, ±3 GW on the §3 shifts); `entry_capped` 0–8 GW
  (control 77 GW); `decided` 10–16 GW nameplate.
- **P7 — coal economic DOWN, toward the record:** coal economic executed 2024 **2.5–5.0 GW** (arm
  A) / **0.8–2.5 GW** (arm B) vs 11.415 (control) / 12.818 (D48 arm); coal total **8–11 GW** vs
  actual 10.3. **The D48 arm's +1.4 GW of cap-admitted coal is RETAINED** — the D48 §3.3(d)
  reading tested: a faithful price pays the cohort the consistent budget admitted.
- **P8 — gas steam economic UP, past the record (the sign that reads AGAINST the design):** gas_st
  economic executed 2023 **4–9 GW** (lag 1) vs 0 in every prior arm and 2.7 GW actual; gas_cc
  economic 0–2.2 GW (arm A; mostly `entry_capped` by the floor's cheapest-firm retention);
  gas_ct **0** (arm A) / **0–3 GW** (arm B). This is the E&AS operand made visible, NOT a reason
  to haircut an offer.
- **P9 — totals and gates:** `retire.total_gw` **14–21 GW** (arm A, central ~17) vs 15.06 actual
  — the band may PASS on the total with the COMPOSITION wrong; `unit_recall_gt300` DOWN to
  9–15/20; `false_retire` **5–11 GW**; determination **HOLD (FC-3 FAIL)** in both arms — this
  design is not expected to flip the PJM T1-H gate and says so.
- **P10 — 2025 only through the entering fleet:** entering position 0.95–0.99 (SHORT, the cap
  segment), the curve at/near the cap; the 2025 gas_ct backstop 0.5–1.1 GW (1,012.8 MW in every
  prior arm). Additions byte-identical to the control in 2022–2024 (the entry screen's capacity
  term is $30–58/kW-yr instead of $0 — no thermal candidate crosses its LCOE at that level;
  `add.by_tech` unchanged; storage entry may gain ≤ 0.2 GW). **Any 2025 FC-3 move beyond the
  entering-fleet consequence of the 2022–2024 decisions is STOP 5.**
- **P11 — LOYO (rule 22):** every fold's |design position − published cleared| improves on the
  census control (+8.5 / +4.1 / −4.3 pts → within ±3), a zero-parameter mechanism doing what the
  market does; not a fit.
- **P12 — wall / memory:** two PJM T1-H legs, **15–25 min and 9.5–10.5 GB** each, solo, years
  sequential (STOP 6 at > 2× the control's 14.7 min or > 12 GB).

## 6. STOP conditions (design §7.7 verbatim; the falsifier restated)

1. Phase 0 miss > $1 / > 0.1 pt — **CLEARED (§2)**. 2. The bare key or any other ISO's default key
moves — **CLEARED at build HEAD (§1)**; re-checked at every rebase. 3. I2 fails in any solved year.
**4. THE FALSIFIER: any arm's clearing price within ±20 % of the published price in a long year
(2022/23–2024/25 — i.e. inside $40–60 / $27–41 / $23–35 per MW-day) means an OPERAND moved: stop,
find it, re-declare. The instrument says the committed operands cannot produce it; a price that
lands there because a coefficient moved is the answer key.** The design is NOT refused for missing
the published price — that miss is the measurement. 5. FC-3 moves in 2025 beyond the
entering-fleet consequence. 6. Wall > 2× control or RSS > 12 GB. 7. Anything beyond the suffixed
keys, the PJM shard cell, the matrix row and the tests moving. Plus: D53 merges mid-lane and moves
the bare key → re-resolve, re-declare, say so.

## 7. Records this lane commits before the solve

`docs/handoffs/d57/phase0-reproduction-2026-09-05.{py,json,txt}`; this addendum; the build
(`4e8877fb`). After the solves: the two suffixed bundles' slim committed sets (the D45-R / D48
template), their registrations, `FINDING-capx-d57-2026-09-05.md`, and the PJM shard's cell
stamped with the measured verdict. Nothing arms; no keeper / shard-stamp of another ISO / marker.
