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

*(filled at close — see §8.)*

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

## 5. THE FULL WINDOW — 2021–2025 realized, one bundle

*(filled at close.)*

---

## 6. Against the pre-declared signs, at full magnitude

*(filled at close.)*

---

## 7. STOPs — none fired

*(filled at close.)*

---

## 8. §8 RECOMMENDATION

*(filled at close.)*

---

## 9. What this lane does NOT close, and what it routes

*(filled at close.)*
