# FINDING — capx D62: PJM's own published default gross ACR, substituted for the ATB FOM proxy as the retirement screen's going-forward bar (and, through the D57 identity, as the sell-offer cap), plus the tariff's reactive component as the single out-of-market leg — BUILT, GATED DEFAULT-OFF, and MEASURED against the committed `pjm-t1h`

**Lane:** capx D62 (director r#43, re-issue of the r#41 charter). Branch
`claude/capx-d62-pjm-acr-bar`. Base `fca3b656`, rebased onto main before the final push.
DATA PROFILE `pjm`. Model Opus.
**Binding charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` §D62 +
`FINDING-capx-d61-2026-09-05.md` §4. **Pre-registration:**
`docs/handoffs/PRECOMMIT-capx-d62-pjm-acr-bar-2026-09-06.md`, committed and pushed
(`1f4a548f`) **before** the first line of build and every solve.
**Instruments:** `docs/handoffs/d62/phase0-2026-09-06.{py,json}` (the zero-LP gate),
`docs/handoffs/d62/screen-2026-09-06.json` (every screen number),
`docs/handoffs/d62/full-window-2026-09-06.json` (every full-window number).
**Nothing arms in this lane.**

---

## 0. The answer in one paragraph

**PJM's own published default gross Avoidable Cost Rate is the operand the model's ATB FOM proxy was
standing in for, and substituting it moves the 2022/23 capacity price from 1.52× the published
Resource Clearing Price to 0.936× with the cleared position +0.27 pt from the published — at zero
free parameters, no scalar field, and a vintage rule fixed in code before any solve. It also removes
a spurious +4.0 GW of 2023 gas-CC entry (FC-2 `gas_cc` FAIL → PASS). It is nonetheless NOT
recommended for arming: the lane's own pre-registered STOP 5 fired — the 2024/25 price moved 165.84
→ 188.57 $/MW-day, through the CENSUS (the arm's earlier exits left 1,582 MW fewer standing) rather
than the offer side, a channel D61's fixed-fleet zero-solve instrument could not see — and FC-3 gets
worse where it was already failing (`retire.total_gw` 18.70 → 20.14 against 15.06 actual, recall
0.60 → 0.55), largely because 4.137 GW of oil over-exits: oil's published bar falls only
$1.64/kW-yr while the clearing price falls $29.32, so a class whose bar falls less than the price
does is left above it. Phase 0 reproduced the committed control to 0.0000 $/MW-day and 0.0000 pt;
the screen gate passed on all five legs on the pre-named year; the G-DRIFT audit found no LIVE hunk
across 54 changed solve-path files, so no control solve was spent. §8 is DO-NOT-ARM as it stands,
with the oil/steam offer convention (D67, whose scope this lane widens to include oil) and the
2024/25 census (D66) routed ahead of it.**

---

## 1. What was built

**One object, two seams** (rule 19 `[R-ONE-MECH]`), gated default-off for every ISO.

| # | Piece | Where |
|---|---|---|
| 1 | `capacity_going_forward_bar_published_by_iso: dict[str, bool] \| None = None`, resolved through ONE predicate `config/capacity_market.py::resolve_capacity_going_forward_bar_published`. **No scalar field, and none may be added** (rule 24 `[R-REGISTRY]`) — the values are DATA with source doc and page. Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"`, `TIER_TAGS` 1, coerced to `None` in a plain backcast. CLI on `run_capacity_hindcast.py` and `run_full_horizon.py` (+ `--no-` forms), recorded in `run_config.json` through the RESOLVED predicate (`Derived`) beside the raw mapping (`FromConfig`). **Not armed:** no `_pjm_config` override. | `config/scenarios.py` (placed at the END of the field list, outside the D50 block, outside SCN-WS1a's D34-guard region and outside SCN-WS2a/2b's `federal_ces_*` block), `config/capacity_market.py` |
| 2 | **Seam 1 — THE BAR.** `retirements.py::resolve_going_forward_bar_per_kw_yr(config, fuel_type, year) -> (bar $/kW-yr nameplate, basis)`. Gate off: `fixed_om_<fuel> × retirement_fom_multiplier_<fuel>`, basis `atb_fom`. Gate on: the ISO's published default gross ACR for the delivery year the screen prices, basis `published_acr` (or `published_acr_first_published` on the vintage rule's "n/a" limb). | `retirements.py` |
| 3 | **THREE sites read that one operand**, so no second construction of the same quantity can exist: the screen's `going_forward_cost`; the D57 clearing's sell offer, which is built from that same `going_forward_cost` (identity below); and `_floor_retention_merit`'s $/firm-MW-yr retention key — a floor that ranked "cheapest firm adequacy" on the proxy while the screen tested the published bar would be exactly the two-mechanisms-one-phenomenon rule 19 forbids. capx D55's class-constant form is preserved exactly, so same-fuel units still tie bit-for-bit on key 1. | `retirements.py` |
| 4 | **Seam 2 — REACTIVE.** The published reactive component enters `net_revenue` ONCE, as `pmax_mw × rate`, BEFORE the capacity leg, so the offer inherits it exactly as the screen does. The SOLE out-of-market credit — no uplift, no regulation, no black start, no AS annual rate, each refused by name under rule 13's forward test (D61 §2b). | `retirements.py` |
| 5 | **Data.** One `reactive_offset` row added to `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` with source doc + page; the new `cost_component` value in the schema and both READMEs; the consumption seam `src/market_sim/data/avoidable_cost_rate.py`, which **hard-errors rather than degrading** when the gate is armed and the published table cannot be read (a silent fallback to the proxy under an armed gate would run a different mechanism than the run declares). | `data/`, `scripts/lib/…`, `src/market_sim/data/` |
| 6 | **Ledger:** additive `going_forward_bar_basis`, `going_forward_bar_per_kw_yr`, `reactive_credit_usd` on every `pipeline_events` margin row. Diagnostic only. | `retirements.py` |

### 1.1 The vintage rule — fixed in the PRECOMMIT before any solve (rule 21 `[R-DOF]`)

DY ≤ 2025/26 reads the *"Through the 2025/2026 Delivery Years"* column (2022/23 $, nameplate);
DY ≥ 2026/27 the second column; a class printed **"n/a"** in the first — **Steam Oil & Gas** —
reads the **first published value**, with the substitution NAMED in its ledger basis. Screen year Y
prices DY Y/Y+1. **No column, escalation or UCAP/nameplate convention may be selected by a result**;
the rule lives in code (`data/avoidable_cost_rate.py`) and an ambiguous table hard-errors rather
than being resolved by picking.

| model fuel class | M18 technology class | DY ≤ 2025/26 $/kW-yr | DY ≥ 2026/27 | model ATB bar | ratio |
|---|---|---:|---:|---:|---:|
| `coal` | Coal | **29.20** | 34.31 | 58.50 | 2.00× |
| `gas_cc` | Combined Cycle | **20.44** | 41.25 | 30.00 | 1.47× |
| `gas_ct` | Combustion Turbine | **18.25** | 18.98 | 21.00 | 1.15× |
| `gas_st` | Steam Oil & Gas † | **23.36** | 23.36 | 35.00 | 1.50× |
| `oil` | Steam Oil & Gas † | **23.36** | 23.36 | 25.00 | 1.07× |
| `nuclear` | Nuclear – Multi Unit | **162.43** | 196.01 | 130.00 | **0.80×** |
| `gas_cc_ccs` | *(no published class)* | — | — | 65.00 | ATB kept |

† the "n/a" limb. **Nuclear is the one class whose published bar is ABOVE the proxy** — the model's
bar is 0.80× PJM's. That is reported, not adjusted; §3.2 measures what it does (nothing: nuclear's
offers are censored at zero on both sides).

Reactive: **$2,199/MW-yr** = $2.199/kW-yr, PJM's own capacity demand-curve E&AS-offset input (2024
SOM §10). Two things stated at the row rather than buried: it is computed for PJM's **reference
resource** and this lane applies it to every screened thermal class; and the same section's reactive
TOTAL charges ($380.7 M in 2024 over a ~185 GW fleet ≈ $2,060/MW-yr) **corroborate the scale and
identify nothing**.

---

## 2. G-DRIFT — the code-level drift audit, in place of a control solve (rule 29(b))

Full table: PRECOMMIT §2. Summary and the two facts that matter:

**Control = the committed bare `pjm-t1h`** (`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/`, D57 arm A, registered as the `pjm-t1h` recipe), solved at `git.sha = a30696a0`, which **is an ancestor of HEAD**. `git diff a30696a0 fca3b656 -- src/market_sim scripts/run_full_horizon.py scripts/run_capacity_hindcast.py scripts/lib` = **54 files, +3,904 / −539**, classified **HUNK BY HUNK** — never at file level, because that is what let D55's `_floor_retention_merit` through D65's audit, and `retirements.py` is this lane's own seam-1 file.

- **`retirements.py`: 10 hunks, all INERT** — 8 are D59 locality plumbing at a `None` default, 1 is D53's new `sector_gated_unit_ids` (a new symbol whose only caller is gated off for PJM), 1 is a ledger field. The file's **only deleted code line** is a re-wrapping of the same `capacity_revenue_per_mw_yr(...)` call with a `None` kwarg added.
- **Every other file INERT**, with four claims verified empirically rather than asserted:
  1. SCN-WS1a's **ungated** `carbon_price → carbon_mc_column(...)` at runner.py's `assemble_mc` seam: measured `resolve_carbon_price(cfg, y) == 0.0` for y ∈ 2021…2025 and `carbon_mc is carbon_price` → `True` in all five years (gate 1 returns the identical object);
  2. SCN-WS2a's clean-tier restructure: `_rps_region_grain_active(cfg,"PJM") = False` and `_clean_region_arrays_for_year(cfg,"PJM",2023,…) = None` — neither row family builds anything for PJM, and `_build_rps_region_rows` builds `data_r` in lock-step with `groups_r` so `coeff=None` ⇒ `concatenate(data_groups) ≡ np.ones(cols.size)` anyway;
  3. the wall-clock A-1 **ungated** vectorization of `_load_cod_map`: its shipped dict-equality gate against the pre-vectorization loop, **46 passed / 8 subtests**, 127 s;
  4. the wall-clock A-2 **ungated** eGRID parquet mirror: all three solve-path reads **IDENTICAL** on values, column order and dtypes (PLNT23 ×2 at 12,612×6, UNT23 at 26,186×3).
- **NO LIVE HUNK ⇒ G-CTRL form 4 is valid and no control solve was spent.**

**The one thing that DID move, and it is D60's, not this lane's.** The PJM T1-H recipe's cache key advanced `f0e050e820c1159a → aef81c84c4609c76`. Measured cause, isolated: forcing `ccs_retrofit_capex_co2_scaling` back to `False` reproduces the committed key **exactly**; it is the only value difference between the seam-resolved HEAD config and the committed `scenario_config` (the seven other new fields are all registered and drop at their defaults). **A key move with a provably nil value effect on this horizon**: `ccs.py::apply_ccs_retrofit` returns at its first statement, `if year < config.ccs_retrofit_available_year` (2028), before any read of the flag, and the window ends in 2025 — which is what the cache-epoch ledger itself says of every hindcast horizon ending before 2028.

**Disclosed non-decision output diffs** (so no reader mistakes them for drift): every margin row gains `locality_price_per_kw_yr: 0.0` (D59) and this lane's three D62 fields; each annual summary gains SCN-WS0's six emissions-grain / cap-price keys, and `DispatchResult.emissions` is populated on parquet read instead of `None`.

**Director-verified facts, re-verified here, not assumed:** D58's PJM sector-gate arming has **not** landed (`_pjm_config.default_scenario_overrides` = the three D57/D48 gates only); `git diff --stat d66d5e6b fca3b656 -- src/market_sim` is **empty**.

---

## 3. PHASE 0 — the zero-LP STOP gate: **PASS**

`docs/handoffs/d62/phase0-2026-09-06.py` re-clears the committed arm-A offer stacks **through the
code path** — the new resolver under a real `ScenarioConfig` feeding the code's own
`clear_capacity_supply_stack` / `capacity_supply_curve`.

### 3.1 S0 — the committed clearing, reproduced

| DY | ledger price · position | code price · position | Δprice | Δposition |
|---|---|---|---:|---:|
| 2022/23 | 76.1035 · 1.046232 | 76.1035 · 1.046232 | **0.0000** | **0.0000 pt** |
| 2023/24 | 82.8112 · 1.045421 | 82.8112 · 1.045421 | **0.0000** | **0.0000 pt** |
| 2024/25 | 165.8365 · 1.027607 | 165.8365 · 1.027607 | **0.0000** | **0.0000 pt** |
| 2025/26 | 451.6100 · 0.966127 | 451.6100 · 0.966127 | **0.0000** | **0.0000 pt** |

### 3.2 S6 / S6R — the published bar, and the arm's own arithmetic

| scenario | 2022/23 ratio · Δpos | 2023/24 | 2024/25 | 2025/26 |
|---|---|---|---|---|
| **S6** published bars only (D61's row: 1.06 / 1.56 / 5.04) | **1.0638 · +0.10** | **1.5585 · −0.27** | **5.0373 · −2.34** | cap · −3.88 |
| **S6R** bars **+ the reactive leg** — what THIS arm computes | **0.9356 · +0.27** | **1.3705 · −0.12** | 5.0373 · −2.34 | cap · −3.88 |

**Two things the instrument records against interest**, neither of which D61's could:

1. **The committed ledger's `offer_stack` 5th element is a `cleared` flag, not nameplate.** A first
   pass read it as `pmax` and produced a plainly wrong S6 (1.52× — the price barely moving). The
   error was mine, in the instrument, and it is written here rather than silently corrected: the
   nameplate is now recovered through the **code's own** `thermal_accreditation_fraction` on the
   class EFORd — the same resolver `_thermal_firm_mw` priced `accredited_mw` with — so the
   reconstruction inverts the ledger's own construction instead of a hand table. A unit-level
   identity check (max |plateau offer − `bar × 1000/(af × 365)`| ≤ 4.5e-5 $/MW-day across all four
   years) gates it.
2. **D61's censored-unit convention is an approximation, and it is nuclear's alone.** A unit
   offering 0 tells the ledger only that `EAS ≥ GFC`; under a bar that RISES its offer is bounded by
   `(GFC_new − GFC_old)/(A × 365)`, not zero — and nuclear is the one class whose published bar
   rises (130.0 → 162.43). Both are reported: at the bound the 2022/23 price reads $91.58 instead of
   $53.19. **The solve settles it** (§4.2): all 31 nuclear units still offer exactly 0 under the
   published bar, so the bound is loose and the S6/S6R rows are the right ones. The approximation is
   the reconstruction's alone — the model never inverts an offer; it computes E&AS in the screen and
   applies the bar directly.

---

## 4. THE SCREEN — DY 2022/23, the year named in the PRECOMMIT before it ran: **GATE PASS**

Screen year chosen as the year the mechanism's own measured footprint is **largest** (every CT / ST
/ oil offer on the bar plateau: 330 CT, 115 gas_st, 421 oil units at exactly zero E&AS; coal's ATB
gap widest at 2.0×) — **not** the year with the biggest residual. One solve year (2021 solved, 2022
the rule-22 bridge). **No control solve**: the committed `evolution_2022.json` is the control.
Every number: `docs/handoffs/d62/screen-2026-09-06.json`.

| | control (committed `pjm-t1h`) | arm (published bar + reactive) | pre-solve prediction (S6R) |
|---|---:|---:|---:|
| price $/MW-day | 76.1035 | **46.7823** | 46.78 |
| ratio vs published $50.00 | 1.522× | **0.936×** | 0.94 |
| cleared position | 1.046232 | **1.053672** | 1.0537 |
| Δ vs published 1.0510 | −0.477 pt | **+0.267 pt** | +0.27 |
| `how` · marginal unit | marginal offer · oil `7779_5` | marginal offer · `CT_PEAKER_PJM_EMAAC_p7318_econ` | — |
| offers / uncleared | 1,370 / 429 | 1,370 / **649** | — |
| uncleared firm MW | coal 5,368 · CC 2,052 · ST 8,802 · oil 2,996 | coal **238** · CC 2,052 · **CT 3,236** · ST 8,802 · oil 3,723 | coal 238 · CC 2,052 · ST 8,802 · oil 3,723 |
| requirement · price takers · census pos | 155,048 · 30,578 · 1.17019 | **identical** | — |

**The solve lands on its own pre-solve arithmetic to the cent** ($46.7823 vs $46.78; position
1.053672 vs 1.0537). That is what gate G1 asks.

### 4.1 The gate, leg by leg

| leg | question | result |
|---|---|---|
| **G1** | direction + order of magnitude | **PASS** — ratio 1.522 → 0.936, inside the declared 0.87–1.06; position −0.48 → +0.267 pt, inside the declared +0.1…+0.3; matches S6R to the cent |
| **G2** | footprint confined to the bar rows | **PASS** — see §4.2 |
| **G3** | offer == exit identity (I2) | **PASS with one disclosed boundary case** — see §4.3 |
| **G4** | reactive enters ONCE | **PASS** — 1,180 rows carry `reactive_credit_usd`; max relative error of `pmax × 2199` is **3.6e-16**; zero rows on the control |
| **G5** | no non-target load-bearing criterion flips | **PASS** — `requirement_mw`, `price_takers_mw`, `census_position`, `entry_decided_mw_by_tech` (solar 2,440.6 / wind 1,500.0), `renewable_additions`, `floor_retained` (0) and the exogenous coal exit (−3,983.1 MW) are **identical** in both arms |

### 4.2 G2 — the footprint is the arithmetic, class by class

Every offer delta is exactly `(ATB bar − published bar + 2.199) × 1000 / (af × 365)`:

| class | units | moved | delta $/MW-day (min … max) | arithmetic check |
|---|---:|---:|---|---|
| `gas_ct` | 404 | 404 | −14.424 (uniform) | (21.00−18.25+2.199)×1000/(0.94×365) = **−14.424** ✓ |
| `oil` | 421 | 421 | −11.686 (uniform) | (25.00−23.36+2.199)×1000/(0.90×365) = **−11.686** ✓ |
| `gas_st` | 115 | 115 | −40.769 (uniform) | (35.00−23.36+2.199)×1000/(0.93×365) = **−40.769** ✓ |
| `gas_cc` | 234 | 168 | −33.912 … 0 | (30.00−20.44+2.199)×1000/(0.95×365) = **−33.912** ✓ (0 for units already at offer 0) |
| `coal` | 165 | 103 | −93.803 … 0 | (58.50−29.20+2.199)×1000/(0.92×365) = **−93.803** ✓ |
| **`nuclear`** | 31 | **0** | 0 | censored at 0 on BOTH sides — its real E&AS exceeds the higher published bar too |
| VRE / hydro / storage / imports / DR | — | — | — | not in the stack; `price_takers_mw` identical |

Nothing outside the classes with a published row moves, and `Q_0 + Σ A_g` is unchanged.

### 4.3 G3 — the identity, and the one boundary case, reported at full magnitude

On the ledger's own `cleared` flag: **control 429 uncleared == 429 `decided`/`entry_capped`/`re_confirmed` rows, exactly.** Arm: **649 uncleared, all 649 present in the event set**, plus **5 extra event rows** carrying `capacity_cleared: true`.

Those 5 are **one to two ULPs of double precision**, not a mechanism:

| unit | event | offer − price | `net_revenue − going_forward_cost` | relative |
|---|---|---:|---:|---:|
| `CT_CHP_PJM_EMAAC_p52149_econ` | entry_capped | +2.1e-05 | −1.16e-10 USD on a $637,555 bar | **−1.8e-16** |
| `CT_PEAKER_PJM_West_APS_p3132_econ` | entry_capped | +2.1e-05 | −1.16e-10 on $704,945 | −1.7e-16 |
| `CT_PEAKER_PJM_EMAAC_p7138_econ` | entry_capped | +2.1e-05 | −1.16e-10 on $819,699 | −1.4e-16 |
| `CT_CHP_PJM_EMAAC_p54829_econ` | entry_capped | +2.1e-05 | −1.46e-11 on $101,178 | −1.4e-16 |
| `CT_PEAKER_PJM_ATSI_p2933_peak` | entry_capped | +2.1e-05 | −3.64e-12 on $22,229 | −1.6e-16 |

All five sit on the marginal CT plateau, where D57's settlement pays a cleared marginal unit exactly
`GFC − EAS` (indifference by definition) and `eas + (gfc − eas)` returns one ULP below `gfc` through
ordinary catastrophic cancellation — after which the screen's strict `net_revenue < going_forward_cost`
reads them as failing. **It is a pre-existing property of the D57 settlement's indifference guard,
not something this arm introduced**: the control's marginal unit is a lone oil unit with no plateau
*at* the price, so the guard is never exercised there; the published bar puts 330 CT units on a
plateau at the clearing price and exercises it 5 times.

**Decision effect: exactly zero.** All five are `entry_capped` — held back by the admission cap, so
none is admitted to the pipeline and none produces an exit. Total 125.2 MW nameplate.

**NOT FIXED IN THIS LANE, deliberately.** The repair belongs to D57's settlement (compare with the
same relative tolerance the settlement used, rather than a strict `<`), it would change the control's
behaviour too, and changing a second mechanism inside an A/B is precisely what rule 29's screen gate
exists to prevent. **Routed as a successor** (§9).

### 4.4 Composition in the screen year, and the cost the arm carries

| | control | arm |
|---|---|---|
| `pipeline_events` | decided 77 · entry_capped 352 · executed 38 | decided 535 · entry_capped 119 · executed 526 |
| executed MW by fuel | gas_st 7,334 | gas_st **8,265** · oil **4,137** |
| fleet delta MW | coal −3,983 · gas_cc +2,829 · gas_st −7,377 · oil −51 · biomass −8 | coal −3,983 · gas_cc +2,829 · gas_st **−8,308** · oil **−4,188** · biomass −8 |

**The oil result is the mechanism, not a defect, and it was pre-declared.** Oil's bar FALLS
(25.00 → 23.36) and it gains the reactive credit, so its offer drops $11.69/MW-day — but the
CLEARING PRICE drops $29.32, because coal's bar falls 29.30 and the CT plateau it lands on is
$18.25-based. A class whose bar falls **less** than the price does is left above it: oil goes from
2,996 MW uncleared to **3,723 MW** (its whole fleet), is paid $0, fails, and exits. The
pre-declaration named exactly this — *"oil 3.7 GW uncleared unless reactive+energy clears it"* — and
it does not clear it. Reported at full magnitude as a composition cost of the arm.

### 4.5 Resource envelope

Matrix build 14.2 s; 2021 P0 solve 272.6 s cold, P1 82.5 s warm; peak RSS **7.18 GB**. Inside the
D57 envelope (14 min / 9.3 GB). STOP 7 not fired.

---

## 5. THE FULL WINDOW — 2021–2025 realized, ONE bundle, arm vs the committed control

**Arm** `results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/PJM/b98060898fceb3da/` — the D57
recipe **plus** `--capacity-going-forward-bar-published`, one
`--start-year 2021 --end-year 2025` invocation, years sequential. Solved [2021, 2023, 2024, 2025],
2022 the rule-22 bridge — the control's own span. **Control:** the committed `pjm-t1h`
(`f0e050e820c1159a`), differenced, never re-solved (§2). Key `b98060898fceb3da`, pre-computed and
matched. Every number: `docs/handoffs/d62/full-window-2026-09-06.json`.

### 5.1 The clearing, per delivery year

| DY | control price · ratio · Δpos | **arm price · ratio · Δpos** | control `how` / uncleared | **arm `how` / uncleared** |
|---|---|---|---|---|
| 2022/23 | 76.10 · 1.522× · −0.48 pt | **46.78 · 0.936× · +0.27 pt** | marginal offer / 429 | **marginal offer / 649** |
| 2023/24 | 82.81 · 2.426× · −0.98 | **54.72 · 1.603× · −0.31** | marginal offer / 168 | **marginal offer / 15** |
| 2024/25 | 165.84 · 5.734× · −2.79 | **188.57 · 6.520× · −3.29** | marginal offer / 8 | **curve at census / 0** |
| 2025/26 | 451.61 (cap) · 1.673× · −3.88 | **451.61 (cap) · 1.673× · −5.04** | curve at census / 0 | curve at census / 0 |

`R` (requirement) and `Q_0` (the price-taking block) are **identical to the MW in every year** —
155,047.5 / 30,577.9, 161,117.0 / 32,652.3, 166,810.0 / 27,959.7, 148,798.1 / 24,000.2. Nothing
outside the screened fleet moved in any year.

**2022/23 is the headline.** The published bar plus the reactive leg put the model's PJM capacity
price at **$46.78 against the market's $50.00 — 0.936×, a 6.4 % miss** where the ATB proxy read
1.522×, and the cleared position lands **+0.27 pt** from the published 1.0510 where the control sat
−0.48 pt away. That is the D61 §2d measurement confirmed in a real solve, and it is the largest
single improvement the D57 clearing half has taken since it was built.

**2023/24 improves and misses its bracket.** 2.426× → **1.603×**, against a pre-declared 1.28–1.56:
**outside the top of the band by +0.043**. Position −0.98 → **−0.31 pt** against a declared
−0.3…0: **outside by 0.01 pt**. Both misses are reported at full magnitude and neither is smoothed;
the arm's 2023 census is 4.6 GW smaller than the control's (1.0881 → 1.0597) because of §5.3's
2022 exits, which is why the zero-solve bracket — computed on the control's fleet — did not hold.

### 5.2 **STOP 5 FIRED** — the 2024/25 price moved

The PRECOMMIT's STOP 5 reads, verbatim: *"The 2024/25 price moving — every offer already clears
there; if it moves, something other than the chartered mechanism moved."* **It moved: 165.84 →
188.57 $/MW-day, +13.7 %, and the ratio went the wrong way, 5.734× → 6.520×.** The STOP is recorded
as FIRED on its own text. It is not reinterpreted to pass.

What the evidence says the cause is, stated separately from the verdict:

| 2024/25 | control | arm |
|---|---:|---:|
| `how` | marginal offer sets price | **curve at census sets price** |
| offers / uncleared | 769 / **8** | 835 / **0** |
| `R` requirement MW | 166,810.0 | **166,810.0** (identical) |
| `Q_0` price takers MW | 27,959.7 | **27,959.7** (identical) |
| census MW | 172,158.6 | **170,576.6** (−1,582) |
| census position | 1.0321 | **1.0226** |

Every offer clears in the arm — **more completely than in the control**, where 8 were uncleared — so
the offer side behaves exactly as D61 predicted for this year, and the curve is read at the census.
The requirement and the price-taking block are identical to the MW. The only thing that moved is
the **census**, and it moved because the arm's own 2022–2023 exits (§5.3) left 1,582 MW fewer
screened MW standing in 2024; on a downward-sloping VRR curve a smaller census is a higher price.

So the moving part is **the chartered mechanism propagating through capacity evolution** — a channel
D61's zero-solve instrument could not represent at all, because it re-clears a FIXED committed stack
and cannot let year *t*'s exits change year *t+2*'s fleet. The STOP's *literal text* is met; its
*stated reason* ("something other than the chartered mechanism moved") is not. **Both halves are
reported, and the arm is not promoted on the strength of the second** (§8).

2025/26 shows the same channel without the price: the price is unchanged at the cap in both arms
(451.61), but the position falls 0.9661 → 0.9545, so Δpos vs the published widens −3.88 → −5.04 pt.

### 5.3 What the arm retires, and why 2024's census is smaller

Economic (pipeline-executed) exits over the window, GW:

| | control | arm |
|---|---|---|
| `gas_st` | 9.464 | **9.464** (identical, to the MW) |
| `oil` | 0.000 | **4.137** |
| `coal` | 0.441 | **0.000** |
| `gas_cc` | 2.254 | **0.000** |

Two large composition moves, in opposite directions, both traceable to one thing — **the clearing
price falls further than most bars do**:

* **Oil over-exits by 4.137 GW.** Oil's bar falls only $1.64/kW-yr (25.00 → 23.36) and it gains the
  $2.199 reactive credit, so its offer drops $11.69/MW-day — but the clearing price drops $29.32,
  because coal's bar falls $29.30 and the CT plateau the price lands on is $18.25-based. A class
  whose bar falls **less** than the price does is left above it: oil's whole 3.72 GW goes uncleared,
  is paid $0, fails, and exits in 2022. **This was pre-declared** — *"oil 3.7 GW uncleared unless
  reactive+energy clears it"* — and reactive+energy does not clear it.
* **Coal and gas-CC stop exiting economically at all.** Coal's bar halves (58.50 → 29.20), so coal
  clears at the lower price in every year and never fails the screen: economic coal exits go
  **0.441 → 0.000 GW**. This is the **opposite** of the pre-declared sign (*"economic coal exits UP
  from 0.44 GW"*), which D61 §2d item 5 derived by holding the price fixed while halving the bar;
  in a real solve the price falls with the bar and coal clears instead.

### 5.4 FC-3 (retirements) and FC-2 (additions), at full magnitude

| FC-3 | actual | control | **arm** |
|---|---:|---:|---:|
| `retire.total_gw` | 15.062 | 18.702 (**FAIL**, +24.2 %) | **20.144 (FAIL, +33.7 %)** — moves AWAY |
| coal GW | 10.299 | 6.016 (−41.6 %) | **5.575 (−45.9 %)** |
| gas_cc GW | 0.434 | 2.328 (+437 %) | **0.075 (−82.8 %)** — large improvement |
| gas_st GW | 2.702 | 10.297 (+281 %) | **10.297 (+281 %)** — unchanged, as declared |
| oil GW | 0.613 | 0.051 (−91.6 %) | **4.188 (+584 %)** — the over-exit |
| gas_ct / biomass GW | 0.808 / 0.207 | 0.000 / 0.009 | 0.000 / 0.009 (unchanged) |
| unit recall ≥300 MW | 20 | 12/20 = 0.60 (**FAIL**) | **11/20 = 0.55 (FAIL)** |
| plant recall | | 0.70 | 0.70 (unchanged) |
| release precision, economic | | 0.116 | **0.171** (improves) |
| release precision, all | | 0.407 | **0.423** (improves) |
| T-R10a / T-R10b | | PASS / PASS | **PASS / PASS** |
| BLK-10 backstop fired | | 1.013 GW | 1.013 GW (unchanged) |

| FC-2 | actual GW | control | **arm** |
|---|---:|---:|---:|
| gas_cc additions | 8.525 | 12.118 (**FAIL**, +42.1 %) | **8.118 (PASS, −4.8 %)** |
| wind / solar / gas_ct / storage | 1.619 / 13.066 / 0.442 / 0.283 | 3.000 / 9.762 / 1.013 / 0.000 | **unchanged** |
| wind SHARE band | | delta 0.049 pp (**PASS**) | **delta 0.070 pp (FAIL)** |

**A non-target load-bearing criterion flipped PASS → FAIL:** the wind *share* band. It is arithmetic,
not a wind effect — wind's absolute build is identical in both arms, and its share rose only because
the 4.0 GW of gas-CC entry disappeared from the denominator. Reported because the flip is real.

**CO2 is untouched**, as a capacity-side mechanism should leave it: 274.98 / 277.34 / 320.35 Mt
(control) vs **274.68 / 276.83 / 320.24** (arm) for 2023–2025, against actuals of 407.14 / 420.61 /
448.67 — a −0.1 % to −0.2 % move on a −33 % standing gap.

### 5.5 Resource envelope

Four solve years sequential; per-year P0 107–273 s cold, P1 27–83 s warm; peak RSS **7.18 GB**.
Inside the D57 envelope (14 min / 9.3 GB). **STOP 7 not fired.**

---

## 6. Against the pre-declared signs, graded at full magnitude

The PRECOMMIT §5 declarations, verbatim, each with its measured outcome. **7 HIT · 2 NEAR-MISS ·
3 MISS · 1 STOP.**

| # | pre-declared | measured | grade |
|---|---|---|---|
| 1 | 2022/23 ratio 1.52 → ≈1.06 (0.87–1.06) | **0.936** | **HIT** (inside) |
| 2 | 2022/23 position −0.48 → +0.1…+0.3 pt | **+0.267 pt** | **HIT** (inside) |
| 3 | 2022/23 coal uncleared 5.4 → ≤ 0.2 GW | **0.238 GW** | **NEAR-MISS** (+0.038; D61's own S6 row rounds the same 238 MW to "0.2") |
| 4 | 2022/23 steam 8.8 GW UNCHANGED | **8,801.9 MW, identical** | **HIT** |
| 5 | 2022/23 oil 3.7 GW uncleared unless reactive+energy clears it | **3,722.8 MW uncleared; it does not clear it** | **HIT** |
| 6 | 2023/24 ratio 2.43 → ≈1.56 (1.28–1.56) | **1.603** | **MISS** (+0.043 above the band) |
| 7 | 2023/24 position −0.98 → −0.3…0 pt | **−0.31 pt** | **NEAR-MISS** (0.01 outside) |
| 8 | 2024/25 5.73 → 5.04 then FROZEN (all offers clear) | **6.52; all offers DO clear (0 uncleared vs the control's 8)** | **STOP 5 FIRED** (§5.2) |
| 9 | 2025/26 unchanged | **price identical at the cap; position −1.16 pt** | **HIT on price, partial on position** |
| 10 | FC-3 economic coal exits UP from 0.44 GW | **0.441 → 0.000 GW** | **MISS, opposite direction** (§5.3) |
| 11 | FC-3 gas-steam 9.5 GW unchanged | **9.464 → 9.464 GW, to the MW** | **HIT** |
| 12 | FC-3 gas-CC 2023 entry below +4 GW | **the +4.0 GW entry is gone; FC-2 gas_cc FAIL → PASS** | **HIT** |
| 13 | FC-3 `retire.total_gw` toward 15.06 actual | **18.702 → 20.144, away** | **MISS** |
| 14 | determination expected to STAY HOLD | **HOLD** (thermal-retire band FAIL, recall band FAIL in both arms) | **HIT** |

---

## 7. STOPs — one fired, six did not

| # | STOP | outcome |
|---|---|---|
| 1 | Phase 0 mismatch | **NOT FIRED** — 0.0000 $/MW-day and 0.0000 pt in all four years (§3.1) |
| 2 | bare `pjm-t1h` key moved by THIS lane | **NOT FIRED** — HEAD's bare key `aef81c84c4609c76` unmoved with the field absent and with an explicit `None`; the default pin `e5ecd4105ada3e58` and the bare-backcast pin `6a2845e50951394e` unmoved. Independently re-verified by capx D60-R3 at the merge HEAD: **17 of 17 keys unmoved**, both pinned defaults included. *(Stated precisely: a hand-written `{"PJM": False}` mapping IS a non-default value and keys distinctly, exactly as every registered optional field does and as the cache-key ledger intends so control arms stay separable. The CLI's `--no-` form sets the mapping to `None`, which is key-neutral — that is the path a control arm takes.)* |
| 3 | any other ISO's key moved | **NOT FIRED** — the gate is a `{iso: bool}` mapping absent for every other ISO, and the five non-PJM ISOs have no intaken table, so the resolver returns the ATB path for every unit (tested) |
| 4 | a residual-selected column or convention (rule 21) | **NOT FIRED** — the vintage rule was fixed in the PRECOMMIT and in code before any solve, is asserted from `pjm.csv` by test, and was not revisited after any number was seen |
| 5 | **the 2024/25 price moving** | **FIRED** — 165.84 → 188.57 $/MW-day (§5.2). Cause identified: the arm's own earlier exits shrank the 2024 census by 1,582 MW while `R` and `Q_0` stayed identical to the MW |
| 6 | the price landed through any scalar not in `pjm.csv` | **NOT FIRED** — every number the arm uses is a row of `pjm.csv` with source doc and page; no scalar field exists for them and `check_cache_key_registration` confirms none was added |
| 7 | wall/RSS beyond the D57 envelope | **NOT FIRED** — 7.18 GB peak, inside 9.3 GB |

---

## 8. §8 RECOMMENDATION — **DO NOT ARM, as it stands**

**The mechanism is right and the arm is not ready.** Both halves, plainly:

**What the measurement establishes.** PJM's published default gross ACR *is* the operand the model's
ATB FOM proxy was standing in for, and substituting it is rule 14 `[R-ACCURATE]` in its plainest
form. In 2022/23 it puts the model's capacity price **within 6.4 % of the market's** (0.936× against
1.522×) with the cleared position **inside a quarter-point of the published** (+0.27 pt against
−0.48 pt), at **zero free parameters** — no adder, haircut, shading factor or per-class cap, no
scalar field, and a vintage rule fixed in code before any solve. It also fixes a real FC-2 defect:
the spurious +4.0 GW of 2023 gas-CC entry disappears and `additions.gas_cc` goes **FAIL → PASS**.
Nothing about that is undone by §8's verdict.

**Why it is still DO-NOT-ARM.** Three things, in order of weight:

1. **STOP 5 fired** (§5.2). A STOP written before the solve fired on its own text, and this lane
   does not promote past its own pre-registration. That the cause turns out to be the chartered
   mechanism's multi-year propagation rather than an unchartered channel is the right thing to
   *record*; it is not a licence to re-read the STOP as passing.
2. **FC-3 gets worse where it was already failing.** `retire.total_gw` moves 18.702 → 20.144 against
   an actual 15.062, and unit recall 0.60 → 0.55. The arm trades a large price-formation gain for a
   composition loss, and the composition is what FC-3 grades.
3. **The oil over-exit is a real defect of the joint posture, not noise.** 4.137 GW of oil exits
   because its published bar falls less than the clearing price does. It is arithmetically correct
   given the mechanism, and it is still 6.7× the actual oil retirement.

**Draft owner card text** *(the director's to serve or not; nothing here arms anything)*:

> **Card — capx D62: arm the published going-forward bar for PJM?**
> capx D62 built `capacity_going_forward_bar_published_by_iso` (GATED default-off, zero DOF, no
> scalar field) and measured it against the committed `pjm-t1h`. **For:** the 2022/23 clearing price
> goes 1.52× → **0.936×** the published RCP and the cleared position −0.48 → **+0.27 pt**, on PJM's
> own published operand replacing an ATB proxy that is 1.15–2.0× it, with the spurious +4 GW of 2023
> gas-CC entry removed (FC-2 `gas_cc` FAIL → PASS). **Against:** the lane's own pre-registered STOP 5
> FIRED (the 2024/25 price moved 165.84 → 188.57 through the census, not the offer side);
> `retire.total_gw` 18.70 → 20.14 against 15.06 actual; recall 0.60 → 0.55; and 4.1 GW of oil
> over-exits because its bar falls less than the clearing price does. **The lane's own recommendation
> is DO-NOT-ARM as it stands**, and to route the oil convention (D67) and the 2024/25 census (D66)
> first — the two objects D61 named and this arm did not touch. A narrower question the owner may
> prefer to put instead: *should the published bar be armed for the classes PJM publishes a
> technology-class default for, with the steam/oil class held on its own convention until D67?* —
> which is a partition, not a level, and would need its own A/B.

---

## 9. What this lane does NOT close, and what it routes

1. **D66 — the 2024/25–2025/26 supply CENSUS.** Confirmed as the residual it was named as: in both
   arms every offer clears in those years and the curve is read at the census, so **no offer-side
   operand of any size can move them.** This arm makes the point sharper, not weaker — it moved the
   2024/25 price by moving the census, and in the wrong direction.
2. **D67 — the below-cap offer convention for regulated / self-supplied steam.** Unmoved and
   unmovable here: gas-steam is 8,801.9 MW uncleared and 9.464 GW economically exited in **both**
   arms, to the MW. **And this lane adds OIL to that card's scope** — the two share PJM's single
   "Steam Oil & Gas" published class, and §5.3 shows the class's bar is the one whose relationship
   to the clearing price the published table does not repair.
3. **The D57 settlement's indifference guard** (§4.3). Five rows read as failing at ~1 ULP because
   `eas + (gfc − eas)` lands below `gfc` after cancellation. Zero decision effect here (all five
   `entry_capped`, 125.2 MW, none admitted), but it is a latent boundary defect that the published
   bar makes reachable by putting a 330-unit CT plateau at the clearing price. The repair belongs to
   D57's settlement, not to a bar lane: compare with the same relative tolerance the settlement used.
4. **Nuclear's published bar is ABOVE the model's proxy** (162.43 vs 130.00 $/kW-yr, §1.1) — the one
   class where the ATB estimate is *below* the published operand. It is inert on this horizon (all 31
   units' offers are censored at 0 under both bars, §4.2), and it will not be inert in a forecast
   where nuclear margins compress. Recorded, not adjusted.
5. **`gas_cc_ccs` has no published PJM class** and keeps the ATB path under an armed gate (basis
   `atb_fom_unpublished`). Inert before `ccs_retrofit_available_year` (2028); a forecast lane that
   arms this gate past 2028 owes that class its own identification.
6. **Every other ISO stays `U`** (rule 25). ERCOT is `n/a` by market design; CAISO, MISO, NYISO and
   NEISO each cap offers against a going-forward-cost concept but publish **no generic
   technology-class default an owner may elect**, so each would need its own intake and its own
   identification in its own lane. No verdict transfers.

## 10. Governance attestation

**Rule 1 `[R-STRUCT]`** — structure first: the published bar is the market's own operand, not a level
tuned to a residual; the arm is refused promotion despite improving the headline price. **Rule 5** —
no magic numbers; every value is a `pjm.csv` row with source doc and page. **Rules 13 / 14** — both
inputs pass the forward test (each regenerates from the next filing and responds only to the tariff);
the SOM's uplift, regulation and black-start rows FAIL it and are refused by name; every published
price, position and SOM figure in this document is a validation observable and enters nothing.
**Rule 19 `[R-ONE-MECH]`** — one bar at three sites (screen, offer cap, floor merit key), one
out-of-market leg. **Rule 21 `[R-DOF]`** — zero free parameters; the vintage rule was fixed in code
and in the pushed PRECOMMIT before any solve and was never revisited. **Rule 22** — 2021–2025
realized hindcast, forecast mode, only; no out-of-training year solved or scored. **Rule 24** — no
scalar knob exists or may be added; `check_cache_key_registration` green. **Rule 25 `[R-ISO-SCOPE]`**
— PJM's data and PJM's cell only. **Rule 27 `[R-PUSH]`** — edited locally, pushed as exact on-disk
bytes, every ≥300-line file blob-verified after each push. **Rule 28** — one base row and a cell in
all six shards; `check_mechanism_matrix.py` green (and the 239 line anchors this lane's own
`scenarios.py` insertions shifted were measured — 0 at base, 49 with the change — and repaired).
**Rule 29** — G-DRIFT in place of a control solve, the screen year named before it ran, the screen
gate structural and STOP-only; the screen bundle was written outside the repository and never
reached `results/`, so clause (c) is satisfied by construction. **Nothing armed.**
