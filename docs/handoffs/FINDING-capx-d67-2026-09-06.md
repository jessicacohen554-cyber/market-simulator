# FINDING — capx D67: the PJM adequacy requirement, read from PJM's own published RTO Reliability Requirement — the operand repair is BUILT, phase 0 reproduces D66's arithmetic to 0.000 MW, and the G-DRIFT audit the charter asked for came back **LIVE** on a hunk that has roughly DOUBLED the very error this card repairs

**Lane:** capx D67 (director r#44), the REQUIREMENT successor D66 §8 card A named and D62 §8 routed
ahead of its own arm. Branch `claude/capx-d67-pjm-requirement-operand-18wzjf`.
Pre-registered in `PRECOMMIT-capx-d67-pjm-requirement-operand-2026-09-06.md`, **pushed before any
solve** (commit `905cce42`, merged to `main` as PR #5012). Instruments:
`docs/handoffs/d67/gdrift_peak_probe.{py,json}` (G-DRIFT, zero LP) and
`docs/handoffs/d67/phase0_reproduction.{py,json}` (phase 0, zero LP).
**Nothing arms.** DATA PROFILE: `pjm`.

---

## 0. Verdict in one paragraph

The mechanism is built exactly as chartered — one per-ISO `{iso: bool}` gate in the D57 family,
default `None`, **zero scalar fields**, injected at the single seam
(`gross_adequacy_requirement_mw`) that the reliability floor, the reserve-margin build backstop and
the CR-1 position all reach through one resolver, so arming moves **one** object (rule 19). Its
vintage rule and its hold-last rule were both fixed in the PRECOMMIT before any solve and neither
is selectable by a result. Phase 0 (zero LP) passes all four checks to **0.000 MW**: the
requirement path at HEAD reproduces the D57 arm A ledger exactly with the gate off, D66's
zero-residual decomposition re-derives through the shipped resolvers, the armed requirement is the
published MW independent of the peak, and every year outside the published table is byte-identical.
**The lane's substantive finding, however, is the G-DRIFT audit rule 29(b) requires** — and it does
not come back clean. `DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` moved **0.036 → 0.064645** in the
SCN-LOAD refresh, and because the capacity screen's seam peak is built from `_scale_demand` on the
**growth** path rather than from the hindcast's measured load, that one line moves the PJM T1-H
screen peak by **−10,819 / −7,574 / −3,977 / 0 / +4,386 MW** across 2021–2025. So G-CTRL **form 4
is void** (the committed arm A was solved on a different requirement operand than HEAD produces
unarmed, in four of five years), a control solve at HEAD is earned, and **the 2025/26 operand error
this card repairs has roughly doubled** — from D66's measured 4,635.5 MW of excess peak to
9,021.6 MW. The charter's pre-declared magnitudes are re-derived at HEAD accordingly, with the
divergence predicted ex ante rather than discovered after the fact. A second defect is surfaced,
reported and **routed rather than absorbed**: at HEAD this recipe synthesizes its 2021–2023 screen
peaks by de-growing 2024's measured load 10.8 / 7.6 / 4.0 GW below the load PJM actually served,
while the LP dispatches the measured load in the same year.

---

## 1. Two charter corrections, made in the open

**(a) `f0e050e820c1159a` is a CACHE KEY, not a git sha.** The charter's G-DRIFT instruction reads
`git diff f0e050e820c1159a HEAD`; `git rev-parse` rejects that string, because it is the D57 arm A
*recipe key* (the bundle directory name). Two git anchors exist and **neither is an ancestor of the
other**: `5bb70047` is the commit that landed the bundle (the D57 promotion/merge), and `a30696a0`
is the sha D62 records the solve itself at. Both windows were audited — `5bb70047..HEAD` (67 files,
+6,308/−865) and the wider `a30696a0..HEAD` (74 files, +7,639/−890). The wider window adds exactly
four files (`new_entry.py`, `storage.py`, two `__init__` export lines), all capx D59 locality-curve
and retirement-sector-gate work; **both gates resolve `False` on this recipe**, so nothing LIVE is
added and the verdict is unchanged.

**(b) The charter's STOP names a key that `main` had already moved before this lane opened.** The
STOP reads "the bare `pjm-t1h` key `c6091bd5b62bbc3f` moving". Measured at HEAD the PJM explicit
all-off control key is **`7297dcb3b92be3fb`** — moved by capx D60's declared default flip of
`ccs_retrofit_capex_co2_scaling` (owner ruling Q42). The STOP was therefore re-based in the
PRECOMMIT to the values live at this lane's base, and the attribution is **proven, not assumed**:

| key | D57 arm A / D45-R | at this lane's base | with the D60 flip reverted |
|---|---|---|---|
| bare `pjm-t1h` | `f0e050e820c1159a` | `aef81c84c4609c76` | **`f0e050e820c1159a`** ✔ |
| explicit all-off control | `c6091bd5b62bbc3f` | `7297dcb3b92be3fb` | **`c6091bd5b62bbc3f`** ✔ |

---

## 2. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — **VERDICT: LIVE**

### 2.1 Config axis — one field moved, and it is INERT on this horizon

The bare PJM T1-H payload differs from arm A's by **exactly one field** (the table above proves it:
reverting that one flag restores *both* pre-flip keys digit for digit). It is INERT structurally,
not by argument: `ccs.py::apply_ccs_retrofit` opens with
`if year < config.ccs_retrofit_available_year: return fleet, []`, and that year is **2028**, so
every solved year of a 2021–2025 hindcast returns at the first line. Neither the D50 capex-scaling
flip nor D65's `ccs_retrofit_fixed_cost_co2_scaling` can reach the fleet. **Every ScenarioConfig
field added in the window resolves at its off/None default on this recipe** —
`capacity_going_forward_bar_published_by_iso` (D62) `None`, `federal_ces_target_by_year` /
`federal_ces_acp_usd_per_mwh` `None`, `miso_intermediate_gas_offer_margin` `False` (and
`iso == "MISO"`-gated besides), `unit_outage_extract_basis_share` `False` — so every hunk gated
behind one is INERT.

### 2.2 Code axis — the LIVE hunk, and why it is first-order for *this* card

```
 constants.py, DEMAND_GROWTH_RATES["PJM"]:
-        "mid": {"near": 0.036,    "long": 0.024},
+        "mid": {"near": 0.064645, "long": 0.023830},
```

**Why it is LIVE here rather than merely present.** The capacity screen's seam peak is *not* the
hindcast's measured load. `runner.py` builds it at the top of the year loop as
`_scale_demand(base_demand, wx_config, year)` + `add_load_layers(...)` — the **growth** path — and
only the LP's own `year_demand`, further down, takes the measured hindcast branch. This recipe
resolves `crossover_solve_year_weather = False`, `weather_year = 2024` and
`demand_growth_vintage = None`, so the Arm-R per-year weather rebind never fires, `_scale_demand`
compounds and de-grows across the span 2024↔Y, and `scenario_resolvers` returns the **current**
table rather than a frozen vintage. The moved rate lands directly on the operand this lane repairs.

**Measured** (`gdrift_peak_probe.py`, zero LP — reproduces the runner's preamble and seam exactly):

| year | screen peak @HEAD | D57 arm A committed | Δ MW |
|---|---:|---:|---:|
| 2021 | 126,887.926 | 137,706.833 | **−10,818.907** |
| 2022 | 135,090.596 | 142,664.279 | **−7,573.683** |
| 2023 | 143,823.528 | 147,800.193 | **−3,976.665** |
| 2024 | 153,121.000 | 153,121.000 | **0.000** ✔ |
| 2025 | 163,019.507 | 158,633.356 | **+4,386.151** |

The 2024 row is the weather year, where the growth factor is 1.0 by construction — so it doubles as
the probe's own faithfulness check. The implied rates settle the attribution without further
argument: arm A's committed peaks are reproduced by **3.60 %** compounding (153,121 ÷ 1.036³ =
137,706.8, its 2021 row to the digit), HEAD's by **6.4645 %**.

**Consequence.** G-CTRL form 4 is **VOID**, and under rule 29(b) — "a LIVE hunk is the only thing
that earns a control solve, and then only for the years the screen needs" — this lane solves a
**control at HEAD on the screen year alongside its arm**. Arm A is no longer the control.

### 2.3 What this audit does NOT claim

The remaining ~3,900 non-comment added lines were cleared **by class, not line by line**: the four
`policy/` files and the D62 additions sit behind the §2.1 gates; `offer_curves.py` is
`iso == "MISO"`-gated; `outages.py` is `unit_outage_extract_basis_share`-gated;
`scripts/lib/load_forecast/*` (1,133 lines, the single largest block) is **not imported anywhere
under `src/market_sim/`**; `data/raw/_validation-source/actual_lmp.json` is a scoring comparator,
never a solve input. `lp/rows.py`, `runner.py`, `results/*`, `egrid_sheets.py`, `cod_ramp.py`,
`fleet/eia860.py` and `matrix.py` were **not** individually cleared. That is a deliberate stop, not
an omission: once §2.2 earns a control solve at HEAD, the control absorbs every code hunk by
construction and further classification buys no decision. It is stated here so this section is not
later read as a completeness claim it never made.

---

## 3. The build (rule 21 `[R-DOF]` / rule 24 `[R-REGISTRY]`: zero scalar fields)

| # | what | where |
|---|---|---|
| 1 | `capacity_adequacy_requirement_published_by_iso: dict[str, bool] \| None = None`, resolved through ONE predicate `capacity_market.py::resolve_capacity_adequacy_requirement_published` — the FOURTH member of that module's per-ISO capacity-gate family. Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"` and `TIER_TAGS` 1 **in the same commit as the field**; coerced to `None` in a plain backcast. **NOT armed** — no `_pjm_config` override. | `config/scenarios.py`, `config/capacity_market.py` |
| 2 | `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO`, digitized from the committed `data/raw/capacity-market/demand-curve/pjm/pjm.csv` `reliability_requirement` rows and **reconciled against them byte-for-byte by test** — the same provenance discipline `NET_ICR_REQUIREMENT_MW_BY_ISO` carries for NEISO. | `config/capacity_market.py` |
| 3 | `resolve_published_reliability_requirement_mw` + the seam in `gross_adequacy_requirement_mw`, ahead of the FPR product. | `model/capacity_evolution/retirements.py` |
| 4 | CLI on `run_capacity_hindcast.py` and `run_full_horizon.py` (+ `--no-` forms), recorded in `run_config.json` through the RESOLVED predicate beside the raw mapping. | `scripts/` |
| 5 | Matrix row + a cell in **every** ISO shard (rule 28c). `check_mechanism_matrix.py --base origin/main`: *"1 new field(s) all registered"*. | `docs/codebase-site/data/` |

**The published MW is GROSS of demand response** — the same basis `peak × FPR` returns at that seam
— so the D48 DR-as-supply branch decides netting **unchanged**. This card moves the requirement's
*operand*, never its netting convention, its peak, or its accreditation.

### 3.1 The vintage rule (fixed in the PRECOMMIT, before any solve)

The model's requirement for screen year `Y` is the published **whole-RTO** `reliability_requirement`
for delivery year `Y/Y+1`. It is **not** `reliability_requirement_frr_adj + ee_addback` — that pair
reproduces PJM's published *cleared position* to four decimals in four years (D66 §1.2) and is
exactly therefore the **RPM-only comparator**, basis-mismatched to a model that runs the entire RTO
while RPM is net of a 31.0 / 31.3 / 32.1 / 10.9 GW FRR block. Selecting between the two by result
would be rule-21 territory. **A test asserts the registry does not carry the comparator**, so a
later lane cannot quietly swap the column.

### 3.2 The hold-last rule (likewise fixed before any solve)

In-table delivery years return the published MW. Pre-table years, the **in-table gap** (2026/27 and
2027/28 publish an FPR but no Reliability Requirement row) and every year strictly past the 2028/29
forward edge **fall through to the FPR path**, which itself holds-last the published FPR. That
fall-through *is* the ratio hold-last NEISO's Net-ICR sibling implements explicitly: for PJM the
last published RR-to-forecast-peak ratio **is** the FPR, because PJM constructs `RR = forecast peak
× FPR` by definition, and the arithmetic closes on the committed rows (144,450 ÷ 0.9380 =
153,997.9; 156,012.885 ÷ 0.9401 = 165,953.7). So no absolute MW is ever held over a forward horizon
(rule 13's forward test), **no new constant is introduced**, the held bar still scales with load,
and the mechanism's footprint is exactly the delivery years the published table covers — every
forecast year past 2028/29 is byte-identical to the off path.

---

## 4. Phase 0 — **PASS**, all four checks to 0.000 MW

| check | what it establishes | result |
|---|---|---|
| **A** | gate OFF, the resolver reproduces arm A's committed `screen_adequacy_requirement_mw` on arm A's own committed peak | **0.000** for 2022–2025 |
| **B** | D66's decomposition, re-derived through the shipped resolvers: `FPR × (peak_model − peak_implied) = R_model − R_published` | **zero residual, all five years** |
| **C** | armed, the requirement is the published MW, independent of the peak it is handed | exact, all six in-table DYs |
| **D** | gap + pre-table + forward edge fall through to the FPR path | **byte-identical** |

Check **A** is the targeted G-DRIFT measurement: it isolates the requirement path from the demand
path §2.2 measured LIVE and shows **the operand's own code has not drifted**. 2021 is skipped
because the first solved year has no `prior_results`, so no screen runs — which is also why the
charter's 2021 footprint is not a screenable year.

Check **B**'s table, which is the heart of the card:

| yr | FPR | R_published | implied peak | model peak | R_model | FPR×Δpk | ΔR | residual |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 1.0898 | 166,355.1 | 152,647.4 | 137,706.8 | 150,072.9 | −16,282.2 | −16,282.2 | **−0.000** |
| 2022 | 1.0868 | 163,268.9 | 150,229.0 | 142,664.3 | 155,047.5 | −8,221.4 | −8,221.4 | **0.000** |
| 2023 | 1.0901 | 163,166.2 | 149,680.0 | 147,800.2 | 161,117.0 | −2,049.2 | −2,049.2 | **−0.000** |
| 2024 | 1.0894 | 164,107.6 | 150,640.4 | 153,121.0 | 166,810.0 | **+2,702.4** | +2,702.4 | **0.000** |
| 2025 | 0.9380 | 144,450.0 | 153,997.9 | 158,633.4 | 148,798.1 | **+4,348.1** | +4,348.1 | **0.000** |

D66's own figures land exactly: Δpeak **+2,480.6** (2024) and **+4,635.5** (2025) against D66's
2,481 and 4,636.

---

## 5. The screen (rule 29 clause (a))

**Screen year 2025**, named in the PRECOMMIT before any solve and **re-justified at HEAD rather
than inherited**. The charter cited "delta-peak 4,636 MW vs 2024's 2,481"; both reproduce against
arm A exactly, but §2.2 moved them. At HEAD:

| screen year | Δ(model peak − PJM's implied peak) @HEAD | screen live? |
|---|---:|---|
| 2021 | −25,759.4 | **no** — first solved year, no `prior_results` |
| 2022 | −15,138.4 | yes, but the peak is a **de-grown artifact** of the §2.2 hunk |
| 2023 | −5,856.5 | yes, same contamination |
| 2024 | +2,480.6 | yes — the weather year |
| **2025** | **+9,021.6** | **yes — the largest footprint of any year not distorted by §2.2** |

2025 stands: it is the charter's ex-ante choice, it is the largest-footprint year among the two
whose seam peak is not synthesized by de-growth, and the operand's footprint there has roughly
**doubled** at HEAD — a stronger screen than the charter assumed, not a weaker one. It was not
chosen on any residual.

**Minimum screenable span.** A single-year 2025 solve produces **no screen at all** (the first
solved year has no `prior_results` — the same reason 2021's ledger carries a null requirement), so
the screen is solved as `--start-year 2024 --end-year 2025`: one screen, on 2025, pricing delivery
year 2025/26. Both arms share the span, so the A/B is exact; the structural gate (§6) is fully
gradeable on it, and the position *magnitudes* are graded on the full span only if the screen
clears.

**Arms** (both at HEAD, the control solved because §2.2 voided form 4), keying distinctly:

| arm | key |
|---|---|
| control (gate off) | `6d058c186839457b` |
| arm (`--capacity-adequacy-requirement-published`) | `4bdd3e7cfdc6ceee` |

Both arms solved at HEAD on the recorded keys (`data/clean` was rebuilt first — 56 datatypes; the
harness hard-fails on the confirmed-exits partition rather than silently degrading to the economic
screen). **They cannot be run concurrently**: two PJM LPs at ~9 GB each OOM a 15 GB box, so the
first attempt lost the control to the kernel and it was re-solved alone (rule 12's "cap at ~2
simultaneous runs" is an upper bound, not a target, on this footprint).

---

## 6. The screen gate — STRUCTURAL, pre-registered, a **STOP gate only**

Pre-registered in the PRECOMMIT §6. It may kill the arm; it may never promote it; it contributes to
no determination; it is **never** read against the target residual.

| # | gate | pass condition |
|---|---|---|
| **G1** | identity | `screen_adequacy_requirement_mw` (arm, 2025) **= 144,450.0 MW to 0.000** |
| **G2** | direction & magnitude | the arm's requirement is **8,462.3 MW below** the control's, to 0.000 |
| **G3** | confinement | peak, entering firm, entering census, fleet-by-fuel and the cap arrays **byte-identical** to the control |
| **G4** | one requirement | `capacity_clearing.requirement_mw` **=** `screen_adequacy_requirement_mw`, as in the control (rule 19) |
| **G5** | no collateral flip | no non-target load-bearing criterion flips PASS → FAIL |
| **G6** | the D62 invariant | the 2024/25 price must not move on the census (a full-span observation; carried forward, not dropped) |

### 6.1 Result — **SCREEN PASSES**, G1–G5

| gate | verdict | measured |
|---|---|---|
| **G1** | **PASS** | arm requirement **144,450.000 MW** vs the published 144,450.0 — delta **+0.0000** |
| **G2** | **PASS** | control 152,912.298 − arm 144,450.000 = **8,462.298 MW**; declared 8,462.3, miss **−0.002 MW** |
| **G3** | **PASS** | every entering-side field byte-identical: `screen_peak_demand_mw`, `screen_entering_firm_mw`, `fleet_by_fuel_before`, `wind_cap_mw`, `solar_cap_mw`, `storage_firm_mw` |
| **G4** | **PASS** | arm clearing 144,450.0 = ledger 144,450.0 = screen 144,450.0; control clearing 152,912.298 = its screen (rule 19 holds in both arms) |
| **G5** | **PASS** | the pre-screen year 2024 is identical in both arms |

The screen peak the solve used, **163,019.507 MW**, reproduces the zero-LP G-DRIFT probe's figure
to the digit — a third independent confirmation that §2.2's measurement is faithful.

**RECORDED AGAINST INTEREST — a correction I made to my own instrument, not to the gate.** The
first grading script carried four fields beyond the PRECOMMIT §6 G3 enumeration
(`peak_demand_mw`, `firm_clean_*`, `storage_power_mw`, `reserve_margin`) and reported **G3 FAIL** on
`reserve_margin`. That field is `firm_mw / peak − 1` computed **after** fleet evolution
(`runner.py:4760`) — an **exiting**-side quantity, not an entering-side one. G3's trailing sentence
("the gate changes the requirement operand and nothing else") cannot coherently mean the solve
produces an identical fleet: **G2 requires** the requirement to change and §7's P1/P2 **pre-declare**
that the position moves, so a gate reading "nothing downstream moved" would contradict the rest of
the pre-registration. The **script** was corrected to the pre-registered enumeration; the gate text
was **not** relaxed to fit the result, and everything the over-specified list caught is reported at
full magnitude immediately below.

### 6.2 The exiting side — reported at full magnitude, deliberately not gated

| field | identical? |
|---|---|
| `retirements` | **yes** — the same 8 rows in both arms; **no exit decision changed** |
| `floor_retained` | **yes** — empty in both; the reliability floor binds in neither |
| `fleet_by_fuel_after` | no — **one fuel**, `gas_ct`, **−1,012.8 MW** in the arm |
| `thermal_additions`, `entry_decided_mw_by_tech` | no — the same 1,012.8 MW of gas-CT |
| `reserve_margin` | no — **entirely** the arithmetic consequence of that 1,012.8 MW |

The whole downstream effect is **one channel and one fuel**: the arm's 8.46 GW smaller requirement
lifts the census position 0.9929 → 1.0511, which takes the capacity market from short to long — the
clearing price falls from **$150,383.65 to $69,389.55** per firm-MW-yr and `how` moves from
`all_offers_clear_curve_sets_price` (0 uncleared) to `marginal_offer_sets_price` (21 uncleared) — so
1,012.8 MW less new gas-CT clears the entry screen. **Retirements and floor retention are
untouched.** That is the mechanism doing exactly what §3 says it does, through the one seam it was
built at, and nothing else moved.

---

## 7. Pre-declared signs, to be graded at full magnitude

Computed pre-solve from the published table and the §2.2-measured HEAD peaks, holding the entering
firm census fixed (G3-invariant, so the position moves as `1/ΔR`). **The charter's own numbers are
reported beside them and the divergence is attributed, not hidden.**

| DY | model R @HEAD | published RR | ΔR (arm − control) | sign | ≈ magnitude @HEAD | charter's |
|---|---:|---:|---:|---|---:|---:|
| 2022/23 | 146,816.5 | 163,268.9 | **+16,452.4** | **FALL** | ≈ −9.7 pts | FALL |
| 2023/24 | 156,782.0 | 163,166.2 | **+6,384.2** | **FALL** | ≈ −3.8 pts | FALL |
| 2024/25 | 166,810.0 | 164,107.6 | **−2,702.4** | **RISE** | ≈ +1.6 pts | RISE ~1.7 |
| **2025/26** | **152,912.3** | **144,450.0** | **−8,462.3** | **RISE** | ≈ **+5.6 pts** | RISE ~2.9 |

- **P1** — 2024/25 and 2025/26 RISE; 2022/23 and 2023/24 FALL. *The charter's signs, unchanged: this
  card is **not** a one-way residual improver, which is exactly why it is screened structurally.*
- **P2** — the 2025/26 magnitude is ≈ **+5.6 pts, roughly double the charter's ~2.9**, while 2024/25
  is ≈ **+1.6, essentially the charter's ~1.7**. **This asymmetry is predicted here ex ante from
  §2.2 alone**: 2024 is the weather year (peak unmoved, so the charter's figure survives) and 2025
  is one growth-year above it. A 2024/25 far from +1.6, or a 2025/26 near +2.9, falsifies this
  reading of the drift.
- **P1/P2 on the screen year — HIT.** The 2025/26 census position moves **+5.82 pt** (0.992896 →
  1.051063) against the pre-declared **≈ +5.6**, and against the charter's arm-A-sized **~2.9**. The
  sign is the charter's; the magnitude is the one this lane predicted **ex ante from §2.2 alone**,
  and it is roughly double the charter's for exactly the stated reason — 2025 is one growth-year
  above the weather year, so the drift nearly doubled the operand error. The remaining three
  delivery years are graded on the full span.
- **P3** — the requirement becomes independent of the model's peak in every in-table delivery year
  (`∂R/∂peak = 0`). Already **confirmed** by phase 0 check C.
- **P4** — every year outside the published table is byte-identical. Already **confirmed** by check D.
- **P5** — no other ISO moves, and the PJM plain-backcast key is unmoved. Already **confirmed**: all
  six ISOs' bare T1-H keys and the PJM explicit all-off control are byte-identical with the field
  present, and `check_cache_key_registration.py` is green (800 fields, 255 registered, all declared
  defaults matching HEAD).

---

## 8. What this lane surfaces and ROUTES, rather than absorbing

**(a) The de-grown hindcast screen peak — a demand-path defect, not this card's.** At HEAD the PJM
T1-H recipe synthesizes its 2021–2023 screen peaks by de-growing 2024's measured load at 6.46 %/yr,
putting them **10.8 / 7.6 / 4.0 GW below the load PJM actually served**, while the LP in the same
year dispatches the measured load. Whatever the merits of the new rate as a *forward* number, using
it to back-cast a *historical* screen peak is a construction this lane did not introduce and will
not bury inside its own result. It belongs to the demand path (rule 19), and it plausibly reaches
every ISO's T1-H recipe whose `weather_year` differs from its solve years — not just PJM's.

**(b) Not attempted here, deliberately.** D66 §8 **card B** (the VRE ELCC vintage — its own card,
opposite sign) and **card C** (the `data/clean` rebuild that makes row S10 attributable). **The gas
row is not attempted**: it is the already-chartered steam over-exit (D61 §4 card (c)) seen one year
downstream, and repairing it here would double-count a chartered mechanism (rule 19).

**Nothing arms without an owner ruling.**
