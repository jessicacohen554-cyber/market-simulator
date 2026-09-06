# PRECOMMIT — capx D67: the PJM adequacy requirement read from PJM's OWN published RTO Reliability Requirement, instead of reconstructed as `model peak × FPR`

**Lane:** capx D67. Charter: `FINDING-capx-d66-2026-09-06.md` §8 card A, over
`DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` + `FINDING-capx-d57-2026-09-05.md` (the clearing
half whose requirement operand this repairs) + `FINDING-capx-d61-2026-09-05.md`.
Branch `claude/capx-d67-pjm-requirement-operand-18wzjf`, fresh off `origin/main` **4e3cabad**.
**DATA PROFILE: pjm.** MODEL: Opus (rule 27 — this lane writes core infrastructure).

**Pushed BEFORE any solve.** Every number below is measured from committed artifacts and the code
at HEAD; no LP has been run in this lane at the time of this commit. Instrument:
`docs/handoffs/d67/gdrift_peak_probe.{py,json}`.

---

## 0. What this document fixes, and the two charter corrections it must make first

This PRECOMMIT fixes ex ante, before any solve: the **G-DRIFT verdict** (§1), the **vintage rule**
(§3), the **hold-last rule** (§4), the **screen year** (§5), the **structural screen gate** (§6),
the **pre-declared signs** (§7) and the **STOPs** (§8).

Two things in the charter do not survive contact with the repository, and both are corrected here
rather than silently worked around:

**(a) `f0e050e820c1159a` is a CACHE KEY, not a git sha.** The charter's G-DRIFT instruction reads
`git diff f0e050e820c1159a HEAD`; that string is the D57 arm A *recipe key* (the bundle directory
name), and `git rev-parse` rejects it. The git anchor for the committed control is **`5bb70047`**
("capx D57: the A/B measured, the finding, and the PJM clearing configuration PROMOTED"), the
commit that landed `results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/`.
The audit in §1 is run against `5bb70047..HEAD`.

**(b) The charter's STOP names a key that main had already moved before this lane opened.** The
STOP reads "the bare `pjm-t1h` key `c6091bd5b62bbc3f` moving". Measured at HEAD, the PJM explicit
all-off control key is **`7297dcb3b92be3fb`**, not `c6091bd5b62bbc3f` — moved by capx D60's
declared default flip of `ccs_retrofit_capex_co2_scaling` (owner ruling Q42), which advanced every
resolved key by one field. The STOP is therefore **re-based to the values live at this lane's
base** (§8), and the attribution is proven rather than assumed: setting
`ccs_retrofit_capex_co2_scaling=False` restores **both** pre-flip keys exactly.

| key | D57 arm A / D45-R | at HEAD (4e3cabad) | with the D60 flip reverted |
|---|---|---|---|
| bare `pjm-t1h` (shipped posture) | `f0e050e820c1159a` | **`aef81c84c4609c76`** | **`f0e050e820c1159a`** ✔ |
| explicit all-off control | `c6091bd5b62bbc3f` | **`7297dcb3b92be3fb`** | **`c6091bd5b62bbc3f`** ✔ |

---

## 1. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — **VERDICT: LIVE.** Form 4 is VOID.

`git diff 5bb70047 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference`: **67 files, +6,308 / −865**, of which
**4,100 added lines are non-comment**. Audited on two axes.

### 1.1 CONFIG axis — exactly ONE field moved, and it is INERT on this horizon

The bare PJM T1-H payload at HEAD differs from arm A's by **exactly one field**:
`ccs_retrofit_capex_co2_scaling` `False → True`. Reverting it alone restores arm A's key AND the
D45-R control key, digit for digit (table in §0(b)) — so **no other config field on the PJM T1-H
path has moved since arm A**.

**INERT, structurally, not by argument:** `ccs.py::apply_ccs_retrofit` opens with
`if year < config.ccs_retrofit_available_year: return fleet, []`, and
`ccs_retrofit_available_year = 2028` on this config. Every solved year of a 2021–2025 hindcast
returns at that first line, so neither the D50 capex-scaling flip nor D65's
`ccs_retrofit_fixed_cost_co2_scaling` (default off, and requiring D50) can reach the fleet. This is
the same claim CLAUDE.md already makes of the flip ("Inert below `ccs_retrofit_available_year`
(2028) by construction, so every backcast, hindcast and crossover horizon is byte-identical") and
that `results/cache.py`'s epoch ledger records.

**Every ScenarioConfig field added in the window resolves at its OFF/None default on this recipe**
— so every hunk gated behind one is INERT:

| new field | resolved on `pjm-t1h` | gate |
|---|---|---|
| `capacity_going_forward_bar_published_by_iso` (D62) | `None` | off ⇒ ATB FOM path, unchanged |
| `federal_ces_target_by_year` / `federal_ces_acp_usd_per_mwh` (SCN-WS2a) | `None` / `None` | no row, no escape |
| `miso_intermediate_gas_offer_margin` (miso-217) | `False` | also `iso == "MISO"`-gated (rule 25) |
| `unit_outage_extract_basis_share` (nyiso-196) | `False` | off |

### 1.2 CODE axis — **one hunk is LIVE, and it is first-order for THIS lane**

`constants.py`, `DEMAND_GROWTH_RATES["PJM"]`, moved in the SCN-LOAD refresh:

```
-        "mid": {"near": 0.036,    "long": 0.024},
+        "mid": {"near": 0.064645, "long": 0.023830},
```

**Why it is LIVE here and not merely present.** The capacity screen's seam peak is NOT the
hindcast's measured load. `runner.py` computes it at the top of the year loop as
`_scale_demand(base_demand, wx_config, year)` + `add_load_layers(...)` — the *growth* path — and
only the LP's own `year_demand` (further down, line ~2517) takes the measured hindcast branch.
This recipe resolves `crossover_solve_year_weather = False`, `weather_year = 2024` and
`demand_growth_vintage = None`, so (i) the Arm-R per-year weather rebind never fires, (ii)
`_scale_demand` compounds/de-grows across the span 2024↔Y, and (iii) `scenario_resolvers` returns
the **current** `DEMAND_GROWTH_RATES` table, not a frozen vintage. The moved PJM rate therefore
lands directly on the operand this lane repairs.

**Measured** (`docs/handoffs/d67/gdrift_peak_probe.py`, zero LP — reproduces the runner's preamble
and seam exactly; the 2024 row is the weather year, where the growth factor is 1.0 by construction
and the reproduction is therefore also the probe's own faithfulness check):

| year | screen peak @HEAD | D57 arm A committed | Δ MW |
|---|---:|---:|---:|
| 2021 | 126,887.926 | 137,706.833 | **−10,818.907** |
| 2022 | 135,090.596 | 142,664.279 | **−7,573.683** |
| 2023 | 143,823.528 | 147,800.193 | **−3,976.665** |
| 2024 | 153,121.000 | 153,121.000 | **0.000** ✔ |
| 2025 | 163,019.507 | 158,633.356 | **+4,386.151** |

The implied rates confirm the attribution exactly: arm A's committed peaks are reproduced by a
**3.60 %** compounding (153,121 ÷ 1.036³ = 137,706.8 = its 2021 row, to the digit), HEAD's by
**6.4645 %**. Nothing else is needed to name the cause.

**Consequence, stated plainly.** G-CTRL form 4 — differencing this lane's arm against the committed
D57 arm A — is **VOID**: arm A was solved on a different requirement operand than HEAD produces
unarmed, in four of five years. Under rule 29(b) a LIVE hunk "is the only thing that earns a
control solve, and then only for the years the screen needs", so **this lane solves a control at
HEAD on the screen year (2025) alongside its arm**, and the control — not arm A — is the baseline.

### 1.3 What this audit does NOT claim

The remaining ~3,900 non-comment added lines were cleared **by class, not line by line**: the four
`policy/` files and the D62 `retirements.py`/`capacity_market.py`/`avoidable_cost_rate.py` addition
sit behind the §1.1 gates; `offer_curves.py` is `iso == "MISO"`-gated; `outages.py` is
`unit_outage_extract_basis_share`-gated; `scripts/lib/load_forecast/*` (1,133 lines, the single
largest block) is **not imported anywhere under `src/market_sim/`** and so is not on the solve path
at all; `data/raw/_validation-source/actual_lmp.json` is a scoring comparator, never a solve input.
I did **not** individually clear every hunk in `lp/rows.py`, `runner.py`, `results/*`,
`egrid_sheets.py`, `cod_ramp.py`, `fleet/eia860.py` or `matrix.py`. That is a deliberate stop, not
an omission: once §1.2 earns a control solve at HEAD, the control absorbs every code hunk by
construction, and further classification buys no decision. It is recorded here so that the FINDING
does not later read as a completeness claim it never made.

### 1.4 A defect this audit surfaces that is NOT this lane's to fix

At HEAD the PJM T1-H recipe synthesizes its 2021–2023 screen peaks by **de-growing** 2024's
measured load at 6.46 %/yr, putting them 10.8 / 7.6 / 4.0 GW below the load PJM actually served,
while the LP in the same year dispatches the measured load. Whatever the merits of the new rate as
a *forward* number, using it to back-cast a *historical* screen peak is a construction this lane
did not introduce and will not silently absorb into its own result. It is reported in the FINDING
and routed, not repaired here (rule 19 — one mechanism per phenomenon; this is the demand path's).

---

## 2. THE BUILD (fixed here; zero scalar fields, rule 21 / rule 24)

1. **ONE per-ISO gate**, in the `{iso: bool}` form the clearing half uses:
   `ScenarioConfig.capacity_adequacy_requirement_published_by_iso: dict[str, bool] | None = None`
   (dataclass default `None` ⇒ every ISO off ⇒ byte-identical), registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` **in the same commit as the
   field** (the nyiso-119 discipline), and resolved by
   `capacity_market.resolve_capacity_adequacy_requirement_published(config, iso)` — the fourth
   member of that module's per-ISO capacity-gate family, written exactly like its three siblings.
   **PJM is armed via `iso_configs._pjm_config.default_scenario_overrides` ONLY after the A/B and
   an owner ruling** (the D57 §8.1 pattern): the shared defaults stay `None`, every other ISO and
   every backcast keeper stays byte-identical, and an explicit `--no-…` reaches the control.
2. **Registry**: `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO: dict[str, dict[str, float]]` in
   `config/capacity_market.py`, keyed by delivery-year label `"YYYY/YYYY+1"` → MW, digitized from
   the committed `data/raw/capacity-market/demand-curve/pjm/pjm.csv` rows (`metric =
   reliability_requirement`, RTO area) and **reconciled against that CSV byte-for-byte by a test** —
   the identical construction and provenance discipline `NET_ICR_REQUIREMENT_MW_BY_ISO` already
   carries for NEISO. The values are DATA with source doc and page; **no scalar field exists for
   them and none may be added** (rule 24), and a different requirement is a change to the published
   table.
3. **Seam**: `retirements.gross_adequacy_requirement_mw`, ahead of the FPR product. The published
   RTO Reliability Requirement is **gross of DR** (PJM counts DR as supply-side UCAP), which is the
   same basis `peak × FPR` returns at that seam, so the existing D48 DR-as-supply branch in
   `resolve_adequacy_requirement_mw` decides netting **unchanged** — this lane touches the
   requirement's *operand*, never its netting convention.
4. **One requirement, three verbs (rule 19).** The reliability floor, the reserve-margin build
   backstop and the CR-1 position all reach the requirement through
   `resolve_adequacy_requirement_mw`, which calls `gross_adequacy_requirement_mw`; injecting at
   that seam is what makes "the floor and the backstop read the SAME requirement" true by
   construction rather than by convention (D54 §3).

---

## 3. VINTAGE RULE — FIXED HERE, BEFORE ANY SOLVE (charter step 3)

**The model's requirement for screen year `Y` is the published WHOLE-RTO `reliability_requirement`
for delivery year `Y/Y+1`.**

- **NOT `reliability_requirement_frr_adj + ee_addback`.** That pair is the **RPM-only comparator**
  (D66 §1.2 — it is the denominator that reproduces PJM's published cleared position to four
  decimals in four years), and it is basis-mismatched to this model: the model runs the entire RTO,
  all load and all resources, with no FRR carve-out, while RPM is net of an FRR block of 31.0 /
  31.3 / 32.1 / 10.9 GW across these years. The model's census is whole-RTO, so its requirement
  must be whole-RTO. **Selecting between the two by result would be rule-21 territory and stops the
  lane; it is fixed here instead.**
- The delivery-year label is built by `capdel.resolve_delivery_year(iso, year)` — the SAME helper
  the FPR path uses (PJM's June-start delivery year: model calendar `Y` → `"Y/Y+1"`), so the two
  constructions can never key differently.
- The gate changes **which published quantity is read**, never the netting, never the peak, never
  the accreditation.

---

## 4. HOLD-LAST RULE — FIXED HERE, BEFORE ANY SOLVE (charter step 3)

The published series covers 2021/22, 2022/23, 2023/24, 2024/25, 2025/26 and 2028/29. It has **an
in-table gap (2026/27, 2027/28 — both publish an FPR but no Reliability Requirement row)** and a
forward edge at 2028/29.

- **In-table delivery year** → the published MW.
- **In-table gap** → **fall through to the FPR path.** A mid-table hole is a data problem, and the
  established convention in this codebase is that hold-last must not paper over one (the FPR
  resolver's own docstring; the NEISO Net ICR resolver's step 5).
- **Strictly beyond the last published row** → **also fall through to the FPR path**, which itself
  holds-last the published FPR.
- **Pre-table** → fall through, as every sibling resolver does.

**Why fall-through IS the hold-last rule here, and why it costs zero DOF.** NEISO's analogue holds
a *ratio* rather than an absolute MW, because "an absolute MW held over a 2028–2050 horizon would
fail the rule-13 forward test". For PJM the last published RR-to-forecast-peak ratio **is the
published FPR** — PJM constructs `RR = forecast peak × FPR` by definition, and the arithmetic
closes on the committed rows (2025/26: 144,450 ÷ 0.9380 = 153,997.9; 2028/29: 156,012.885 ÷ 0.9401
= 165,953.7). So "hold the last published RR/peak ratio" and "hold the last published FPR" are the
**same object**, and the second is already in the code. No new constant, no new held MW, and the
held bar still scales with load.

**The mechanism's footprint is therefore exactly the delivery years the published table covers:**
every forecast year past 2028/29 — the entire 2029–2050 horizon — is byte-identical to today.

---

## 5. SCREEN YEAR — **2025**, named here, before any solve (rule 29 clause (a))

The charter names 2025 and cites "delta-peak 4,636 MW vs 2024's 2,481". **Both of the charter's
figures reproduce exactly against arm A** (+4,635.5 and +2,480.6, §7 table) — but they were sized
on arm A's peaks, and §1.2 moved them. The footprint at HEAD is re-measured and the choice is
re-justified rather than inherited:

| screen year | Δ(model peak − PJM's implied peak) @HEAD | screen live? |
|---|---:|---|
| 2021 | −25,759.4 | **no** — first solved year, no `prior_results`, so `screen_adequacy_requirement_mw` is null in the committed ledger |
| 2022 | −15,138.4 | yes, but the peak is a **de-grown artifact** of the §1.2 LIVE hunk |
| 2023 | −5,856.5 | yes, same contamination |
| 2024 | +2,480.6 | yes — the weather year (growth factor 1.0) |
| **2025** | **+9,021.6** | **yes — the largest footprint of any year not distorted by §1.2** |

**2025 stands.** It is the charter's ex-ante choice; it is the largest-footprint year among the two
(2024, 2025) whose seam peak is not synthesized by de-growth; and the operand's footprint there has
roughly **doubled** at HEAD (4,635.5 → 9,021.6 MW), which makes it a stronger screen than the
charter assumed, not a weaker one. **It is not chosen on any residual**, and no other year's
outcome was consulted in choosing it.

---

## 6. THE SCREEN GATE — STRUCTURAL, PRE-REGISTERED, AND A **STOP GATE ONLY**

It may kill the arm; it may never promote it; it contributes to no determination; and it is
**never** read against the target residual (rule 1 `[R-STRUCT]`; rule 29). Graded on the 2025
screen, arm vs the HEAD control:

| # | gate | pass condition |
|---|---|---|
| **G1** | **identity** | `screen_adequacy_requirement_mw` (arm, 2025) **= 144,450.0 MW to 0.000** — the published 2025/26 RTO Reliability Requirement, exactly. The requirement stops depending on the model's peak. |
| **G2** | **direction & magnitude** | the arm's requirement is **below** the control's by **8,462.3 MW to 0.000** — the pre-solve delta of §7, reproduced by the solve. |
| **G3** | **confinement** | the delta appears in the requirement rows ONLY. `screen_peak_demand_mw`, `screen_entering_firm_mw`, `fleet_by_fuel_before`, `wind_cap_mw`/`solar_cap_mw`/`storage_firm_mw` and the entering census are **byte-identical** to the control. The gate changes the requirement operand and nothing else. |
| **G4** | **one requirement** | `capacity_clearing.requirement_mw` **=** `screen_adequacy_requirement_mw` in the arm, as in the control — the floor, the backstop and the clearing still read one object (rule 19). |
| **G5** | **no collateral flip** | no non-target load-bearing criterion flips PASS → FAIL. |
| **G6** | **the D62 invariant** | the 2024/25 **price** must not move on the census. *(Charter: "The 2024/25 price must not move on the census … if it moves for any other reason, STOP." Recorded as declared; note that the 2025 screen prices DY 2025/26, so the 2024/25 delivery year is a FULL-SPAN observation, gradeable only if §5's screen clears and the span is spent — it is carried forward, not silently dropped.)* |

Any of G1–G4 missing ⇒ **the arm is killed and the remaining years are never spent**, and that is
reported as the session's result.

---

## 7. PRE-DECLARED SIGNS — declared here, to be graded at FULL MAGNITUDE

Computed pre-solve from the published table and the §1.2-measured HEAD peaks, holding the entering
firm census fixed (the census is G3-invariant, so the position moves as `1 / ΔR`). **The charter's
own numbers are reported beside them**, and the divergence is attributed, not hidden.

| DY | model R @HEAD (peak × FPR) | published RR | ΔR (arm − control) | position sign | ≈ magnitude @HEAD | charter's (arm-A-sized) |
|---|---:|---:|---:|---|---:|---:|
| 2022/23 | 146,816.5 | 163,268.9 | **+16,452.4** | **FALL** | ≈ **−9.7 pts** | FALL |
| 2023/24 | 156,782.0 | 163,166.2 | **+6,384.2** | **FALL** | ≈ **−3.8 pts** | FALL |
| 2024/25 | 166,810.0 | 164,107.6 | **−2,702.4** | **RISE** | ≈ **+1.6 pts** | RISE ~1.7 pts |
| **2025/26** | **152,912.3** | **144,450.0** | **−8,462.3** | **RISE** | ≈ **+5.6 pts** | RISE ~2.9 pts |

**P1** — 2024/25 and 2025/26 census positions **RISE**; 2022/23 and 2023/24 **FALL**. *(The charter's
signs, unchanged: this card is not a one-way residual improver, which is why it is screened
structurally and not on the residual.)*
**P2** — the 2025/26 magnitude is ≈ **+5.6 pts, roughly double the charter's ~2.9**, and the
2024/25 magnitude is ≈ **+1.6 pts, essentially the charter's ~1.7**. The asymmetry is **predicted
here, ex ante, from §1.2 alone**: 2024 is the weather year (peak unmoved by the LIVE hunk, so the
charter's figure survives) and 2025 is one growth-year above it (peak +4,386 MW, so the operand
error nearly doubles). A 2024/25 magnitude far from +1.6, or a 2025/26 magnitude near +2.9, would
falsify this reading of the drift.
**P3** — the requirement becomes **independent of the model's peak** in every in-table delivery
year: `∂R/∂peak = 0` (G1). This is the mechanism's defining property, not a size claim.
**P4** — every year outside the published table (2026/27, 2027/28, and 2029/30 onward) is
**byte-identical** to the control (§4).
**P5** — **no other ISO moves**: every non-PJM cache key is unchanged, and the PJM plain-backcast
key is unchanged (the gate is coerced off in a backcast, as its two siblings are).

---

## 8. STOPs (re-based to this lane's base per §0(b); any one fires ⇒ stop and report)

1. **Phase-0 mismatch** — the code path fails to reproduce D66's requirement arithmetic to 0.000 MW.
2. **The PJM control key moves.** Re-based: the explicit all-off key must stay **`7297dcb3b92be3fb`**
   and the bare `pjm-t1h` key **`aef81c84c4609c76`** with the gate unarmed. *(The charter's
   `c6091bd5b62bbc3f` is the pre-D60-flip value of the same key and is unreachable at this base; it
   is restored exactly by reverting that flip, §0(b), which is how the STOP is honoured in substance.)*
3. **Any other ISO's key moves.**
4. **A residual-selected column, convention or hold-last rule** — §3 and §4 are fixed above and may
   not be revisited against a result.
5. **Wall / RSS beyond the D57 envelope** (14 min / 9.3 GB for a five-year run; the 2025 screen and
   its control are one year each).
6. **The 2024/25 price moves on the census** (§6 G6).

## 9. NOT THIS LANE

D66 §8 **card B** (the VRE ELCC vintage — its own card, and its sign is opposite) and **card C**
(the `data/clean` rebuild that makes row S10 attributable). **The gas row is not attempted:** it is
the already-chartered steam over-exit (D61 §4 card (c)) seen one year downstream, and repairing it
here would double-count a chartered mechanism (rule 19). The §1.4 demand de-growth defect is
reported and routed, not repaired.

**Nothing arms without an owner ruling.**
