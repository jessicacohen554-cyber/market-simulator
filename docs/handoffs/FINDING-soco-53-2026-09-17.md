# FINDING — SOCO-53 (2026-09-17): the `CT_PEAKER` / `ST_GAS` lever is not a price lever

**Lane** SOCO-53 · **Model** Opus 5 · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53-2026-09-17.md`, pushed and pinned at
`0f6bd1215b13dcc5a0fc4be5b5ab17dcb74330b1` **before** the arm was solved.
**Arm** run `2026-09-17-soco53-measured-ct-hr`, bundle `results/calibration/soco53_measured_ct_hr`.
**Control (rule 29 `[R-SCREEN]` (b) form 4 — no control solve spent)**
`2026-09-16-soco-1-baseline`, bundle `results/calibration/soco40_coalsplit_B`,
basis `71884144abf4f08a4063d3c7a32e03a2c2f5d04d`.

---

## 1. HEADLINE

**SOCO's one gating C1 failure is not a merit-order or offer-construction defect, and this lane
refutes that framing with measurement rather than argument.** The arm it solved — the rule 14
`[R-ACCURATE]` repair the evidence pointed to — was **predicted ex ante to make the target row
worse, and did**. That is the result, and it is a clean one: it closes off the entire cost-side
family of explanations.

> ### Determination: **NOT-YET** — rubric v3.8, **PRICE UNSCORED**
> Unchanged from the control. C2 / C4 / C6 / C8 **PASS**; C3a / C3b / C3c **UNSCORABLE**;
> 0 ledgered, 0 protective caveats; DOF unchanged at n_entries 3 / n_residual 1.
> **C1 moves from ONE failing row to TWO.**

| | control | arm |
|---|---|---|
| C1 failing rows | **1** — 2023 `CT_PEAKER` +8.22 TWh, +3.4 pp | **2** — 2023 `CT_PEAKER` **+9.85 TWh, +4.1 pp**; 2023 `ST_GAS` **−7.34 TWh, −3.1 pp** |
| C1 all / free | 13/14 · 9/10 | **12/14 · 8/10** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| determination | NOT-YET (PRICE UNSCORED) | NOT-YET (PRICE UNSCORED) |
| model mean LMP (MODEL-ONLY, UNVERIFIED) | 33.32 / 31.14 / 199.34 | 32.37 / 30.51 / 198.06 |

---

## 2. WHAT THE LANE ESTABLISHES — four measured findings, all zero-LP

These stand independently of any solve, and they are the lane's real product.

### 2.1 Every offer-curve lever is inert for SOCO **by construction**

`backcast_config._SOCO_OFFER_CURVE` sets all four bands to the identity **1.0 on all 13 groups**.
A SOCO tranche offers at its own measured heat rate × delivered fuel + VOM, so **each class
collapses to a single flat price block** — the tranche shares still partition capacity, nothing
prices it differently. Confirmed in the control's own committed `class_band_hourly` sidecar:

| 2023 class | committed | econ_low | econ_high | peak | total |
|---|---|---|---|---|---|
| `ST_GAS` | 1.117 | 1.138 | 1.141 | 0.600 | 3.996 TWh |

Flat across all four bands — the all-or-nothing signature of one price point, not a rising curve.
**Consequence, and it is a program-level fact about SOCO:** every curve-*shaped* lever routes to a
curve that is also all-1.0, so `ct_intermediate_split`, `st_gas_intermediate_split` and their kin
are **provably inert for SOCO**. **SOCO's only available levers are physics and data levers.**

### 2.2 The model already **over-separates** the two classes by 2.8×

Measured from CAMPD unit-level (AL+GA+MS, 2023–2025 pooled, loaded hours, net of the 0.99
parasitic factor):

| | model (eGRID plant blend) | measured (CAMPD) |
|---|---|---|
| `CT_PEAKER` cap-wtd HR | 12.798 | **10.911** |
| `ST_GAS` cap-wtd HR | 10.815 | **10.198** |
| **CT − ST separation** | **+1.983** | **+0.713** |

At $2.54 gas the measured separation is ~$1.3/MWh net of the VOM difference — and the real system
separates the classes by a **7× capacity-factor ratio** (measured 2023 `CT_PEAKER` CF ~5.4 % vs
`ST_GAS` ~38 %). **No cost-side change can turn a $1.3/MWh gap into a 7× CF split**, and the model
is already overshooting the gap. This is positive evidence that the missing object is not price.

### 2.3 The real separation is **commitment**, at unit grain

Plant grain is unsound for SOCO — its facilities are multi-class under one CEMS facility id (Barry
carries gas boilers *and* coal *and* four CC blocks; Greene County and Watson each carry boilers
*and* turbines). Split on CAMPD `unitType`:

| | gas boilers | combustion turbines |
|---|---|---|
| median run length | **94 – 144 h** | **8 – 9 h** |
| mean run length | 299 – 366 h | 9.7 – 10.6 h |
| starts / unit / yr | **8.9 – 11.4** | **57 – 60** |

**The model gives both classes `min_run_hours = 0` and `min_down_hours = 0`**, and with
`tranche_startup_amortization` off the `CT_PEAKER` **econ and peak tranches carry zero startup
cost** — the tranches holding **10.9 of the class's 12.755 TWh** in 2023.

### 2.4 Two mechanisms refused on SOCO's own evidence — zero LP spent

- **`gas_commitment_bridge` → `R`.** The NYISO/SPP-shaped bridge holds a unit across a gap shorter
  than its min-down. Of 386 boiler downtime gaps, **68.7 % exceed 72 h** and account for
  **169,303 of 171,734 gap-hours (98.6 %)**; only **150 unit-hours across three years** fall inside
  the 8 h `ST_GAS` min-down. SOCO's boilers do not two-shift. **Inert by measurement** — refused
  rather than solved, so no successor spends a span on it.
- **`tranche_startup_amortization` → `G`, no reopen condition.** It is the FERC Order-825
  **fast-start pricing** object (bid markup only), and **SOCO has no clearing price, no offers and
  no market**. Arming a market-design pricing rule on a footprint with no market is rule 1
  `[R-STRUCT]` verbatim. Derived from SOCO's own market design, not transferred from CAISO's `G`
  (rule 28(d)).

*(Also recorded, not acted on: `gas_st_startup_spread` is `True` in the keeper's recipe and is a
**dead flag** — `compute_monthly_markup` skips every `gas_st` row before reading it, because
`gas_st_startup_cost` is `False`.)*

---

## 3. THE ARM — armed, predicted adverse, confirmed adverse, and kept

`measured_ct_heat_rates = True` on this lane's own derive of SOCO's CAMPD record
(`campd_ct_heat_rates_SOCO.csv`, **19 of 26 plants, 8,452.5 / 9,634.2 MW = 87.7 %** of `CT_PEAKER`
capacity, MMBtu per **net** MWh). eGRID publishes **one** rate per plant, so **Greene County's nine
combustion turbines and two gas boilers carried the identical 10.482689**. The errors run in **both
directions**, which is why no multiplier substitutes for the measurement:

| plant | MW | model | measured | ratio |
|---|---|---|---|---|
| Greene County (10) | 740.0 | 10.483 | **12.849** | 0.816 |
| Watson CT (2049) | 33.0 | 10.418 | **14.266** | 0.730 |
| Washington County (55332) | 623.4 | **17.185** | 10.702 | 1.606 |
| Calhoun (55409) | 704.0 | **17.099** | 10.422 | 1.641 |
| McIntosh (6124) | 657.6 | **18.740** | 12.494 | 1.500 |

**Rule 19 `[R-ONE-MECH]`, machine-verified:** `CT_PEAKER` cap-wtd HR **12.6921 → 11.2666** and
**every other class is byte-identical** (`CC_REGULAR` 7.4109, `COAL` 10.7834, `ST_GAS` 10.8151,
`CC_CHP` 5.8766, `CT_CHP` 6.0594, `ST_CHP` 5.6845 all unchanged).

### 3.1 The prediction, registered before the solve, and what was delivered

PRECOMMIT §2.2 registered: cap-wtd CT heat rate **12.909 → 11.284 (−12.6 %)**, and **+1,821.3 MW**
of CT capacity crossing below the marginal `ST_GAS` plant in all three years — *"So this lane
PREDICTS, before solving, that `CT_PEAKER` energy RISES and the one gating C1 row this lane was
opened to fix gets WORSE."*

Delivered, against the control's committed sidecars (TWh):

| year | `CT_PEAKER` ctl → arm | Δ | `ST_GAS` ctl → arm | Δ | CT error ctl → arm |
|---|---|---|---|---|---|
| 2023 | 12.755 → **14.388** | **+1.633** | 3.996 → 3.143 | −0.853 | +8.221 → **+9.854** |
| 2024 | 9.717 → **11.104** | **+1.387** | 3.883 → 3.482 | −0.401 | +4.932 → **+6.319** |
| 2025 | 13.009 → **14.217** | **+1.209** | 4.325 → 3.752 | −0.573 | +7.868 → **+9.076** |

Sign and mechanism match the prediction in every year, so the construction is **confirmed rather
than rationalised**. The offsetting decreases are spread across `ST_GAS`, `CC_REGULAR`, `COAL_PRB`
and `COAL_BIT` — the merit order re-sorted, exactly as a cost change should.

**It is kept**, per rule 14's own words: a worse fit after swapping an estimate for real data is a
**discovered bug**, not a reason to revert — the eGRID plant blend was silently compensating for
the missing commitment physics of §2.3. Nothing was reverted and no band was touched.

**A caveat on the gated evidence (inherited disclosure R-v):** seven 2025 C1 rows are SKIPPED on
the preliminary EIA-923 vintage — **including `CT_PEAKER` and `ST_GAS`**, the two rows this lane
moves most. The 2025 column above is **reported but not gated**; the gated evidence is 2023–2024.

---

## 4. A/B INTEGRITY — the comparison is clean, and that is verified not assumed

- **All eight `shared_inputs` content hashes are IDENTICAL** between arm and control
  (`eia923-c6e433cd9eb4`, `eia930-af1df2c6e425`, `campd-eecf72fbab56`, and the five
  `unit_outages*`). The two runs consumed byte-identical measured inputs.
- The shared store was rebuilt locally via `--rebuild-benchmark` (**no re-solve**) and reproduced
  **the same three content hashes**, confirming determinism and that the benchmark did not move.
- **SOCO's bench parts were deliberately NOT rebuilt.** `check_bench_freshness` reports **44 of 44
  parts STALE across every ISO** — pre-existing and another lane's: commit `ed96378e` (caiso-284)
  edited `scripts/render_calibration_html.py`, a `PAYLOAD_SOURCE`. This lane touched no fingerprint
  source. Rebuilding SOCO's bench would score the arm against a different benchmark from the
  control's and destroy the form-4 comparison. **Routed, not absorbed.**

### 4.1 G-DRIFT (rule 29(b)) — recorded before the solve, all six hunks INERT

`71884144… → HEAD`, 6 files, +246/−6: `run_calibration.py`, `config/scenarios.py`,
`data/fleet/floors.py`, `model/interchange/neiso.py` (all the NEISO-only cold-snap dual-fuel scope
correction, default-off, `iso != "NEISO"` guarded, cache-key registered **at its default** so
SOCO's key does not move); `model/interchange/spec.py` (2020/2021 vintages appended to MISO's
`MISO_SEAM_LADDER_BY_YEAR` — SOCO solves 2023–2025 on served measured EIA-930 interchange with no
priced `NeighborInterface`); `run_calibration_full.py` (the same NEISO flag plus NWPP-40's pool
branch — **verified mechanically**: `_is_pool_region("SOCO")` is `False`, `_POOL_HOURLY_MEMBERS` has
the single key `NWPP`, SOCO's bench is truthy in all three years, and the genuine 2025 `NG: NG`
spike repair still fires on exactly the four hours the control's own log names).
**All INERT ⇒ form 4 valid, the committed keeper is the control, no control solve spent.**

---

## 5. A REGISTRY GAP THIS LANE REPAIRED (rule 24 `[R-REGISTRY]`)

`ScenarioConfig.measured_ct_heat_rates` is registered, cache-key-registered, has a derive script, a
live consumer, and is carried `True` by **five ISOs' keepers** (CAISO / MISO / NEISO / NYISO / PJM)
— **and it had no CLI flag in `scripts/run_calibration_full.py`, the orchestrator every keeper is
solved with.** `default_scenario_overrides` does not reach `backcast_config` (verified on NEISO: all
six overrides differ from the built config), so the mechanism was **unreachable for SOCO, NWPP and
SPP**.

Wired along the identical eight-site path `egrid_identity_heat_rates` already takes, with
`BooleanOptionalAction` / `default=None`, so **unset is byte-identical** for every other ISO and
every existing keeper. `scripts/check_cache_key_registration.py` passes (851 fields, 306 registered,
all resolve). Both edited files' pushed blobs were verified byte-identical to local (rule 27).

---

## 6. THE REPAIR IS ONLY PARTIAL — and that is the promotion question

The eGRID plant-blend defect reaches **far beyond `CT_PEAKER`**, and this arm repairs only the CT
slice. Measured on the model's own binned fleet:

> **11,777 MW — 26.0 % of SOCO's thermal capacity — sits at NINE multi-technology plants, and at
> EIGHT of the nine EVERY unit carries a SINGLE blended heat rate regardless of technology.**

| plant | blended HR | what it prices at that rate |
|---|---|---|
| Barry (3) | **8.994965** | 1,118.5 MW coal + 1,821.2 MW gas CC + 160.0 MW gas steam |
| Jack McDonough (710) | 6.724 | 2,471.0 MW gas CC + 64.0 MW oil |
| Victor J Daniel Jr (6073) | **8.399** | 1,004.0 MW coal + 1,132.4 MW gas CC |
| E C Gaston (26) | 11.551 | 832.0 MW coal + 1,020.0 MW gas steam + 16.0 MW oil |
| Greene County (10) | 10.483 | 740.0 MW gas CT + 516.1 MW gas steam |
| Jack Watson (2049) | 10.418 | 33.0 MW gas CT + 721.0 MW gas steam |

**A coal unit at 8.399 MMBtu/MWh is not physically attainable** — Daniel's 1970s subcritical coal
measures ~10.3. Barry's coal at 8.995 is the same defect. Both are priced far too cheap and run
ahead of their merit, which is consistent with the control's 2025 coal over-run (+16–17 % on C2's
ungated 2025 row).

The **completing** mechanism is **`egrid_family_heat_rates`** — already registered and already
reachable from the CLI. Its derive was **run in this session as evidence and its output deliberately
NOT committed** (an unarmed artifact on the standard path is a trap for the next lane). For SOCO it
produces **18 (plant, family) rows over 9 plants, 12 applied**:

| plant | family | model → family rate |
|---|---|---|
| Barry (3) | ST | 8.995 → **12.610** |
| Barry (3) | CC | 8.995 → **7.821** |
| Victor J Daniel Jr (6073) | ST | 8.399 → **12.895** |
| Victor J Daniel Jr (6073) | CC | 8.399 → **7.553** |
| Greene County (10) | GT | 10.483 → **14.105** |
| Greene County (10) | ST | 10.483 → 10.256 |
| Jack Watson (2049) | GT | 10.418 → **21.925** |

Six rows flag `out_of_window` (paper-mill cogens with non-physical rates — the mechanism's own
guard). It was **not armed here** because rule 19 `[R-ONE-MECH]` forbids stacking a second
mechanism on the same phenomenon in the same run.

---

## 7. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — OPEN, AND IT IS THE OWNER'S

**The incumbent keeper `2026-09-16-soco-1-baseline` is UNCHANGED. Nothing was pruned and nothing
was deleted.** SOCO's registered year union was enumerated **before** any prune (rule 35(b)) and is
**{2023, 2024, 2025}** — one registered run, the keeper. The arm covers the same three years.

**The case FOR promoting the arm** — and it is the case the rules as written make:
rule 14 `[R-ACCURATE]` says an accurate measured input is **kept** even when the fit worsens,
because the estimate was silently compensating; rule 1 `[R-STRUCT]` says a keeper is the most
structurally faithful run, not the lowest-MAE one. On the CT slice the arm is unambiguously more
faithful: Calhoun's turbines are no longer priced at a non-physical 17.099, and Greene County's nine
turbines no longer wear their boilers' heat rate.

**The case AGAINST promoting it today** — and it is **not** "the residual got worse", which rule 14
forbids as a reason: the repair is **half of one defect**. Promoting it registers a keeper whose
fleet is knowingly inconsistent — turbines measured, the coal and CC at the *same* plants still
plant-blended — and it moves the ISO's headline from one failing C1 row to two. The completing
mechanism is one cheap lane away and would land a single coherent keeper instead of two partial
ones.

**Recommendation: HOLD the promotion and complete the repair first.** Run one follow-on lane that
arms the plant-blend repair across all families, on the evidence in §6, and promote **that** —
rather than promoting a half-repair now and a second half later. If the owner prefers the letter of
rule 14 — accurate input in immediately, completion to follow — the arm is registered, scored and
ready to promote today.

**Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e)) — a promotion from here costs ZERO re-solves:**

| bundle | full SHA | files | recovery |
|---|---|---|---|
| `soco53_measured_ct_hr` (the arm) | **`3f477ec55ffb2cafc29df6121203c5b8f75611ef`** | 33 (incl. all three `dispatch/<year>_P1.parquet`) | `git archive 3f477ec55ffb2cafc29df6121203c5b8f75611ef results/calibration/soco53_measured_ct_hr \| tar -x` |
| `soco40_coalsplit_B` (the control / incumbent keeper) | `dcb03c6bd346f9ab0d4356d5166b18c4ad42a214` | 34 | `git archive dcb03c6bd346f9ab0d4356d5166b18c4ad42a214 results/calibration/soco40_coalsplit_B \| tar -x` |

The arm's slim files + `hourly/` sidecars are committed on this lane's branch, so a later lane
differences against it with no re-solve. **The shard branch `claude/soco-53-measured-ct-hr` is kept
alive until the owner rules** (rule 33(f)(3)).

---

## 8. COST AND MEMORY

One shard, one `--year 2023 2024 2025` invocation, years sequential (rules 12 / 16 / 32(b)).
Wall clock well inside the 20-minute ceiling; the parent ran **no LP of any length** (rule 32(a)) —
every number in §2 is zero-LP, from the control's committed sidecars, the CAMPD corpus and the
fleet loaders called directly.

## 9. GATES

| gate | exit | result |
|---|---|---|
| `audit_keepers.py --check --iso SOCO` | **0** | PASS, 0 failures 0 warnings |
| `check_mechanism_matrix.py` | **0** | PASS (warnings pre-existing: anchor drift on ten unrelated rows, NEISO prose-header drift — another ISO's lane) |
| `check_golden_manifest.py` | **0** | OK |
| `check_cache_key_registration.py` | **0** | ok — 851 fields, 306 registered, all resolve |
| `check_bench_freshness.py` | **1** | **RED, 44/44 parts STALE across EVERY ISO — pre-existing, caused by `ed96378e` (caiso-284) editing a `PAYLOAD_SOURCE`.** Not this lane's, and deliberately not repaired here (§4) |
| `check_registry_payload_parity.py` | **1** | **RED on exactly two pre-existing unmapped bundle dirs — `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`. NAMED, NEITHER DELETED** (rule 31) |
| `check_gate_a_provenance.py` | **1** | RED on other ISOs' superseded keeper markers. SOCO's only line is the NOTE *"has a keeper shard but no entry on the forecast board"*, which is **correct and deliberate** — card S10 routes the forecast namespace to the capx director. **No gate-(a) stamp was created for SOCO** |

**One pre-existing test failure, named and not silently fixed:**
`tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name`
is **red at HEAD without any of this lane's files** (verified by removing them and re-running). It
asserts every `soco`-named `data/raw` segment starts with `soco` or contains `_soco_`, which the
repo's own `<datatype>-SOCO.csv` convention violates (`campd-unit-outages-SOCO.csv`,
`coal_supply_SOCO.csv`, `thermal_tranches_SOCO.csv`, all pre-dating this lane). The remedy is a
judgement about the profile-token contract and is **routed to the SOCO desk**, not patched here.

## 10. ROUTED ITEMS

| item | to |
|---|---|
| **`egrid_family_heat_rates` — the completing plant-blend repair**, with its SOCO numbers already measured (§6) | SOCO desk — recommended as the next lane, ahead of SOCO-54/55/56/57 |
| **A commitment mechanism for multi-week campaigns** — not a gap bridge (§2.4 refutes that), not a pricing rule (§2.4 refuses that). SOCO boilers run 94–144 h and start ~10×/yr; the model has `min_run = min_down = 0` | SOCO desk — the real root cause of the `CT_PEAKER`/`ST_GAS` split |
| 2025 EIA-923 hydro input hole (5 plants / 0.327 TWh vs 6.012 measured); unchanged and byte-identical in both runs | SOCO-53b data-intake, as SOCO-40 routed it |
| `gas_st_startup_spread = True` is a **dead flag** in the keeper's recipe | SOCO desk |
| 44/44 bench parts STALE repo-wide from `ed96378e` | cross-ISO / caiso-284's lane |
| `test_soco_token_collides_with_no_other_raw_name` red at HEAD | SOCO desk |
| `soco15_spp_arm` — dead committed bundle holding parity RED in CI; **not deleted** (rule 31) | SOCO desk / owner |
| `peak_gb` re-key: SOCO registered at 6.0, measured 2.65 GiB | desk / infra |

---

## Log entry

## soco-53 — 2026-09-17 — the CT/ST lever is not a price lever

SOCO's one gating C1 failure is not a merit-order defect, and this lane establishes that by measurement rather than argument. Four findings do the work, all of them zero-LP and all of them independent of any solve. First, every offer-curve lever is inert for SOCO by construction: `_SOCO_OFFER_CURVE` sets all four bands to the identity 1.0 on all thirteen groups, so each class collapses to a single flat price block — visible in the keeper's own committed sidecar, where 2023 ST_GAS runs 1.117 / 1.138 / 1.141 / 0.600 TWh across committed, econ_low, econ_high and peak, flat. Every curve-shaped lever therefore routes to a curve that is also all-1.0, and SOCO's only available levers are physics and data levers. Second, the model already over-separates the two classes by 2.8×: the measured CAMPD separation is +0.713 MMBtu/MWh while the model's is +1.983, and CT_PEAKER still over-runs by 8.221 TWh — no cost-side change can close a gap the model is already overshooting, still less turn ~$1.3/MWh into the 7× capacity-factor ratio the real system shows. Third, the real separation is commitment: at unit grain SOCO's gas boilers run 94–144 hour campaigns and start about ten times a year, its combustion turbines run 8–9 hour blocks and start about fifty-eight times a year, and the model gives both classes min_run_hours 0 and min_down_hours 0 while the CT econ and peak tranches — which hold 10.9 of the class's 12.755 TWh — carry zero startup cost. Fourth, the bridge that would supply that physics is inert on SOCO's own data and was refused rather than solved: 68.7 % of boiler downtime gaps exceed 72 hours and account for 98.6 % of all gap-hours, and only 150 unit-hours across three years fall inside the 8 hour ST_GAS min-down. SOCO's boilers do not two-shift. `gas_commitment_bridge` is recorded R and `tranche_startup_amortization` G — the latter because it is the FERC Order-825 fast-start pricing object and SOCO has no clearing price at all, which is rule 1 verbatim.

The arm the lane did solve is the rule 14 repair the evidence pointed to: `measured_ct_heat_rates` on SOCO's own CAMPD derive, nineteen of twenty-six plants and 87.7 % of CT capacity. eGRID publishes one heat rate per plant, so Greene County's nine combustion turbines and two gas boilers carried the identical 10.482689, Calhoun's turbines carried a non-physical 17.099, and the errors run in both directions. The PRECOMMIT registered the effect before the solve — cap-weighted CT heat rate 12.909 → 11.284 and +1,821.3 MW of CT capacity crossing below the marginal ST_GAS plant — and stated plainly that the one gating row would get worse. It did: CT_PEAKER +1.633 / +1.387 / +1.209 TWh with ST_GAS −0.853 / −0.401 / −0.573, so 2023 CT_PEAKER moves +8.221 → +9.854 TWh and C1 goes from one failing row to two, the second being 2023 ST_GAS at −7.34 TWh. Determination is NOT-YET both ways, C2/C4/C6/C8 still pass, C3a/b/c remain unscorable, the DOF ledger is unchanged at three entries and one residual, and every offer band is still exactly 1.0 with `authorized_price_tuning` declared NONE. Sign and mechanism match the prediction, so the construction is confirmed rather than rationalised, and the accurate input is kept under rule 14 rather than reverted.

The comparison itself is clean and that is verified, not assumed: all eight `shared_inputs` content hashes are identical between arm and control, and the shared store rebuilt locally reproduced the same three hashes with no re-solve. SOCO's bench parts were deliberately not rebuilt, because `check_bench_freshness` is red on 44 of 44 parts across every ISO from another lane's edit to a payload source, and rebuilding SOCO's would have destroyed the form-4 comparison. The G-DRIFT audit classified all six changed solve-path files INERT for SOCO, mechanically rather than by assertion.

Two things larger than the lever came out of it. `measured_ct_heat_rates` was unreachable: registered, cache-key-registered, carried True by five ISOs' keepers, and with no CLI flag in the orchestrator every keeper is solved with — now wired along the identical eight-site path the eGRID flags take, byte-identical unset. And the plant-blend defect reaches far beyond CT: 11,777 MW, 26.0 % of SOCO's thermal fleet, sits at nine multi-technology plants, and at eight of them every unit carries one blended heat rate — Barry prices coal, gas CC and gas steam all at 8.994965, and Daniel prices 1,004 MW of coal at 8.399, which no coal unit can attain. The completing mechanism is `egrid_family_heat_rates`, already reachable; its derive was run as evidence and its output deliberately not committed.

The promotion is open and is the owner's. The incumbent keeper is unchanged, nothing was pruned, SOCO's registered year union was enumerated before any prune and is 2023–2025, and both bundles are retrievable by immutable SHA so a promotion costs zero re-solves. The lane recommends holding and completing the plant-blend repair in one follow-on lane rather than promoting a half-repair now. Record: `docs/handoffs/FINDING-soco-53-2026-09-17.md`.
