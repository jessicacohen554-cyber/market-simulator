# FINDING — SOCO-53c (2026-09-19): the plant-blend repair lands, and its own artifact needed repairing first

**Lane** SOCO-53c · **Model** Opus 5 · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53c-2026-09-19.md`, pushed and pinned at
`0f8ebad9d71d19a30bd020359d5b86ffb7576850` **before** anything was solved ·
**ADDENDUM** `docs/handoffs/ADDENDUM-soco53c-marginal-carbon-2026-09-19.md`.
**Arm** run `2026-09-19-soco53c-egrid-family-hr`, bundle `results/calibration/soco53c_family`.
**Control** `results/calibration/soco53c_control` — the keeper's own recipe **re-solved at the same
pinned SHA**, not form 4 (§4).

---

## 1. HEADLINE

> ### Determination: **NOT-YET** — rubric v3.8, **PRICE UNSCORED**. **PROMOTED to SOCO's keeper.**
> **The gates did not regress.** C1 all **12/14** · free **8/10** on both sides, the **same two rows**
> fail, C2/C4/C6/C8 PASS on both, **0 ledgered and 0 protective** caveats on both, `grade_summary`
> identical, and **no row changed status in either direction**.

| | superseded keeper | **this keeper** |
|---|---|---|
| determination | NOT-YET (PRICE UNSCORED) | NOT-YET (PRICE UNSCORED) |
| C1 all / free | 12/14 · 8/10 | **12/14 · 8/10** |
| C1 failing rows | 2023 `CT_PEAKER` +9.85 TWh; 2023 `ST_GAS` −7.34 | 2023 `CT_PEAKER` **+10.09**; 2023 `ST_GAS` **−7.36** |
| C2 / C4 / C6 / C8 | PASS | PASS |
| C2 2025 coal (ungated) | +16.0 % | **+12.4 %** — improves |
| DOF ledger | 3 entries / 1 residual | **unchanged** |
| model mean LMP (MODEL-ONLY, UNVERIFIED) | 32.37 / 30.51 / 198.06 | 32.42 / 30.34 / 197.81 |

**Why it is the keeper — rule 14 `[R-ACCURATE]` and rule 1 `[R-STRUCT]`, never the residual.** eGRID
joins heat rate at PLANT grain, so every generator at a multi-technology plant inherits one blend.
**Victor J Daniel Jr (6073) priced 1,004.0 MW of coal at 8.399 MMBtu/MWh — a rate no coal boiler can
physically attain; its own meter reads 12.895.** Barry (3) priced 1,118.5 MW of coal, 1,821.2 MW of
gas CC and 160.0 MW of gas steam all at 8.994965. The arm gives each prime-mover family its own
Σ`UNT23.HTIAN` ÷ Σ`GEN23.GENNTAN` from the **same eGRID vintage the plant-grain join already reads**
— zero free parameters, a finer read of the identical source. It moves **24 rows / 6,473.2 MW at
four plants**.

---

## 2. THE LANE'S REAL PRODUCT: the mechanism's own artifact was wrong at five of nine plants

The derive's docstring claims the family rate replaces the blend **"on the identical net-annual
boundary"**. That is not a description, it is an **identity** — `PLHTRT` is the same ratio over the
union of the families — so it can be *checked*:

```
Σ_families HTIAN ÷ Σ_families GENNTAN  ==  PLHTRT
```

It partitions SOCO's nine covered plants **perfectly, with three orders of magnitude to spare**:

| plant | recomposed | published `PLHTRT` | ratio | |
|---|---|---|---|---|
| 3 Barry · 10 Greene County · 2049 Jack Watson · 6073 Daniel | = | = | **1.000** | same boundary |
| 10416 Pensacola Florida Plant | 22.5366 | 5.5680 | **4.048** | *** DIFFERENT *** |
| 54004 WestRock Southeast | 30.4697 | 5.5634 | **5.477** | *** DIFFERENT *** |
| 54802 Mead Coated Board | 31.6880 | 5.5119 | **5.749** | *** DIFFERENT *** |
| 54096 International Paper Riverdale Mill | 41.3008 | 5.5147 | **7.489** | *** DIFFERENT *** |
| 10361 Savannah River Mill | 50.5987 | 6.0210 | **8.404** | *** DIFFERENT *** |

**The five failures are cogeneration paper mills, and the cause is eGRID's own convention**:
`PLHTRT`'s numerator is STEAM-CREDITED at a CHP plant, while the unit sheet's `HTIAN` is raw fuel. A
family rate there **charges the host's process steam to the electric output**.

**The pre-existing `out_of_window` guard was not sufficient, which is why this matters.** It is a
per-FAMILY plausibility test (3,000–30,000 Btu/kWh) and it caught only the steam halves (35.3–134.1).
The **turbine halves landed INSIDE the window and were being applied** — Pensacola GT 11.655,
WestRock GT 13.643, Mead GT 15.906, Riverdale CC 16.348: **four rows, 160.0 MW, onto `CT_CHP` and
`CC_CHP`**, the latter a scored C1 row.

That is **rule 14's misalignment exception verbatim**, so a per-PLANT `boundary_mismatch` flag now
refuses them. SOCO's artifact goes **12 applied → 8**.

**Derive-side, never consumer-side, and that was a rule-25 decision.** A guard inside
`_apply_egrid_family_heat_rates` is default-on and would have **moved CAISO's keeper fleet from this
lane**. **No `src/market_sim` file is touched** and no solve-path file moves: the artifact schema is
unchanged and `egrid_family_heat_rates_for` already reads only `flag == "ok"`.

`BOUNDARY_IDENTITY_TOL = 0.005` is a rounding allowance for a published figure and is **incapable of
being a tuned threshold**: over all 26 covered plants in the three ISOs carrying an artifact the
passing side sits at 1.0000 (max deviation 5e-6) and the failing side starts at 2.800, so **every
value in (0.001, 1.8) yields the identical partition**. Declared ex ante, never swept. Guarded by two
new tests.

---

## 3. RULE 19 `[R-ONE-MECH]` — the precedence is STRUCTURAL, not declared

`_apply_egrid_family_heat_rates` runs at FRAME level in `_rows_to_generators` (`eia860.py:1215`);
`measured_ct_heat_rates` is applied INSIDE the row loop (`eia860.py:1394`), gated on
`group == "CT_PEAKER"`. The row loop runs last, so the measured rate **overwrites the family rate on
every CT row and never the reverse**.

> **Precedence: measured CAMPD loaded rate ▸ eGRID prime-mover-family rate ▸ eGRID plant blend.**
> One row, one final rate, never a sum.

Machine-verified on the built fleet: `CT_PEAKER` cap-weighted HR is **byte-identical at 11.2666 on
both sides**, so Greene County's computed GT family rate (14.105) and Watson's (21.925) are **both
entirely overwritten**. `CC_CHP` / `CT_CHP` / `ST_CHP` heat rates are byte-identical too, by §2's
guard. Nothing is priced twice.

---

## 4. A CONTROL SOLVE WAS SPENT, AND IT ANSWERED A CROSS-ISO QUESTION

G-DRIFT (PRECOMMIT §3) classified **13 of 14** changed solve-path files INERT and **one LIVE**:
commit `fba0ecd7` (2026-09-18) adds an emissions-dual re-pricing that runs **unconditionally at the
end of every solve for every ISO** — it freezes the cost-optimal basis, swaps the LP objective to the
CO2 rate vector, and calls `run()` again at zero iterations. Its commit message claims every keeper
re-scores byte-identically, **but that is a SCORER claim over committed artifacts**: no ISO had been
re-solved to test it. Rule 29 `[R-SCREEN]` (b) earns a control solve for exactly that, so one was
spent.

> ### RESULT: `fba0ecd7` **IS** byte-identical. **0.000000 TWh** on every class in every year.

Largest absolute drift across **15 classes × 3 years = 0.000000 TWh**, and the two `run_config`s
differ by **exactly one field sitting at its default** (`coal_prb_proxy_own_iso`, an NWPP-only field
that did not exist at the keeper's basis). That single-field isolation is what makes the numeric
agreement attributable to code rather than config. **Form 4 was valid and the control was strictly
unnecessary in hindsight** — reported because the claim had never been verified by a re-solve, and
now has been, on a real ISO.

---

## 5. THE EX-ANTE PREDICTION — confirmed, including the part that is unflattering

PRECOMMIT §2.2 registered, **before the solve**, that this arm would be **adverse-to-neutral** and
**would not fix SOCO's headline defect**.

| class | 2023 | 2024 | 2025 | predicted |
|---|---|---|---|---|
| `COAL` (family) | **−0.665** | **−1.855** | **−1.528** | falls ✓ (**F1 passes**) |
| `CC_REGULAR` | +0.468 | +1.915 | +1.947 | rises ✓ |
| `CT_PEAKER` | +0.234 | +0.399 | +0.157 | \|Δ\| < 1.0 TWh ✓ (**F2 passes**) |
| `ST_GAS` | −0.019 | −0.384 | −0.529 | roughly flat — **marginally outside** the 0.5 TWh wording in 2025 |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | +0.000 | ≤ 0.003 | ≤ 0.001 | see F3 below |

**Two of this lane's own predictions were imprecise, and they are recorded as such rather than
quietly dropped:**

- **The coal fall was OVER-predicted.** 2–5 TWh was registered; 0.7–1.9 TWh was delivered.
- **The flagged 2024 `CC_REGULAR` break did NOT occur.** It lands at +5.38 TWh against a ±7.47 band.
- **F3 was worded too strictly by this lane.** It said *"if any CHP class moves at all, the guard did
  not hold"*. The CHP classes move by **≤ 0.003 TWh**, which is second-order LP **re-dispatch**, not
  repricing — the guard's actual object, the CHP **heat rates**, are byte-identical. F3 holds on its
  substance and was badly phrased; the substance is what the guard is verified on.

**Why `CT_PEAKER` barely moves — measured, not asserted.** Its own heat rate is byte-identical under
this mechanism, and it is not running because the CC fleet is exhausted: **`CC_REGULAR` sits at ≥ 99 %
of its own annual maximum in only 44 of the 7,305 hours `CT_PEAKER` runs in 2023** (3 of 6,447 in
2024; 15 of 7,343 in 2025). SOCO's `CT_PEAKER`/`ST_GAS` misallocation is a **COMMITMENT defect**,
exactly as SOCO-53 concluded, and no cost change at four other plants can reach it.

---

## 6. WHAT THIS DOES NOT REACH — stated at the gate

FINDING-soco-53 §6 named nine multi-technology plants / 11,777 MW. **The mechanism reaches four of
them**, and the others are not oversights:

- **E C Gaston (26) — NOT COVERED and NOT FIXABLE BY THIS CONSTRUCTION.** Its only live family is
  `ST` (its single `GT4` generator files 108 MWh and no heat input), so its plant rate 11.551
  **already is** its ST family rate. But that family is itself a **fuel** blend — **coal 12.111
  (54.2 %) against gas steam 10.887 (45.8 %)** — and a prime-mover construction cannot separate two
  boilers. **A fuel-subfamily rate is a DIFFERENT mechanism** with its own field and matrix row;
  stacking it here is what rule 19 forbids. **Routed, numbers measured.**
- **Jack McDonough (710) — NOT COVERED, correctly.** Its `GT` generators file **−52.0 MWh** each (net
  station service), so the family is not live; its plant rate 6.724 is already essentially its CC rate.
- **The five cogens** — covered by the derive, refused by §2's guard.

**Barry's ST family is itself a fuel blend, and it was CHECKED rather than assumed.** Coal 11.699
(79.6 %) and gas steam 16.159 (20.4 %) blend to the applied 12.610. It is **kept** because it moves
**both** halves toward their own truth **monotonically, with no trade**: coal error −2.704 → **+0.911**
(3.0× closer) and gas steam −7.164 → **−3.549** (2.0× closer) against the control's 8.995. Rule 14's
exception applies only where the accurate data makes results *less* faithful; here it makes both
halves more so. Daniel raises no such question — its ST family is its two SUB coal units alone.

---

## 7. MARGINAL CARBON (owner instruction, 2026-09-19)

The pinned SHA already contained `2ec09663`, so **no re-pin and no wasted shard**, and the extra
`replay_keeper` control was skipped on the instruction's own condition (this lane expected
promotion). Both bundles carry the column.

`hourly/system_<year>.parquet`, 26,280 rows/year (3 zones × 8,760), **present and non-zero**:

| year | load-wtd mean | p10 | median | p90 | share exactly 0.0 |
|---|---|---|---|---|---|
| 2023 | 0.633 | 0.419 | 0.594 | 1.090 | **0.00 %** |
| 2024 | 0.616 | 0.383 | 0.585 | 1.009 | **0.00 %** |
| 2025 | 0.635 | 0.383 | 0.585 | 1.090 | **0.15 %** |

**This CORRECTS this lane's own ex-ante expectation.** The ADDENDUM predicted SOCO's export-heavy
served-interchange posture would produce a **material** zero share; it does not. The documented
boundary caveat still stands *as a caveat* — zero-carbon **and import pseudo-units** carry rate 0 by
design, so an import-marginal hour understates true system consequence — it simply does not bite in
SOCO's solved hours.

**Memory, stated as a limit rather than as reassurance:** SOCO is a 3-zone, ~393-generator,
**non-per-plant** LP. A clean run here is a **weak** test of the dual's unvalidated cost at per-plant
MISO/PJM scale and does **not** clear it.

---

## 8. THE PROMOTION — EXECUTED IN RULE 35's FIXED ORDER

**The owner ruled promote**, on the standard set at the SOCO-53 promotion and repeated this sitting:
*"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but
gates regress that may still be a keeper."* **This lane recommended promotion, and the case is
stronger than that standard required — the gates did not regress at all.**

| step | rule | result |
|---|---|---|
| **(b)** enumerate the year union BEFORE pruning | 35(b) | **{2023, 2024, 2025}** over every SOCO sidecar; one registered run |
| **(c)** incoming keeper covers the union | 35(c) | **yes, in its own bundle** — one `--year 2023 2024 2025` invocation, so no `holdout.keeper` stamp is needed and none was invented |
| **(e)** promote, VERIFY, then delete | 35(e) | keeper shard re-pointed with a structured `superseded` lineage; `build_status.py --iso SOCO` rebuilt; **E1 and E11 both green BEFORE the prune** |
| **(a)** prune the outgoing keeper's THREE stores | 35(a) | `prune_iso_runs.py --iso SOCO --force-uncite` removed registry, payload and bundle together |
| **(d)** `--force-uncite` is the INTENDED route | 35(d) | the guard fired on this lane's own matrix citation; the "looking" is the enumeration and the E1/E11 verification above |
| **(f)** the invariant | 35(f) | **`audit_keepers --check --iso SOCO` PASSES, 0 failures.** One registered SOCO run, it *is* the keeper, year set unchanged |

### 8.1 E11 was COMPUTABLE this time, and its substance is recorded because the prune destroys it

Unlike the SOCO-53 promotion (where E11 was already non-computable), the outgoing keeper's bundle
**was** on disk here, so E11 ran and was **green**. Its substance, measured directly from the two
`run_config.json` files while both were present:

> **Of 852 `scenario_config` fields, exactly TWO differ:**
> `egrid_family_heat_rates` **False → True** (the declared mechanism) and
> `coal_prb_proxy_own_iso` **absent → False** (an NWPP-only field that did not exist at the
> superseded run's basis, sitting at its default).
> **SILENT DE-ARMS (True → not-True): NONE.**

### 8.2 Retrievability — a promotion from here costs ZERO re-solves

| bundle | full SHA | recovery |
|---|---|---|
| `soco53c_family` (**the keeper**) | `c91dde5e4cfbecd4e1da14ebba9209923ef9d500` | `git archive c91dde5e4cfbecd4e1da14ebba9209923ef9d500 results/calibration/soco53c_family \| tar -x` |
| `soco53c_control` (the control, out of `main` per rule 29(c)) | `adb289959d43ce95da3d586aa0dc6b7763784106` | `git archive adb289959d43ce95da3d586aa0dc6b7763784106 results/calibration/soco53c_control \| tar -x` |
| `soco53_measured_ct_hr` (superseded, pruned) | `3f477ec55ffb2cafc29df6121203c5b8f75611ef` | `git archive 3f477ec55ffb2cafc29df6121203c5b8f75611ef results/calibration/soco53_measured_ct_hr \| tar -x` |

Both live bundles carry `marginal_emission_rate` — the marginal-abatement page should read the
**keeper** bundle above.

---

## 9. GATES

| gate | exit | result |
|---|---|---|
| `audit_keepers.py --check --iso SOCO` | **0** | **PASS, 0 failures.** 1 warning: E11 non-computable post-prune — expected, substance in §8.1 |
| `check_mechanism_matrix.py` | **0** | PASS (pre-existing anchor-drift warnings on unrelated rows) |
| `check_cache_key_registration.py` | **0** | ok — 852 fields, 307 registered, all resolve |
| `check_golden_manifest.py` | **0** | OK |
| `check_bench_freshness.py` | **1** | **RED, 44/44 parts STALE across EVERY ISO — pre-existing**, from `ed96378e` (caiso-284) editing a `PAYLOAD_SOURCE`. Not this lane's; **deliberately not repaired** (§10) |
| `check_registry_payload_parity.py` | **1** | **RED on exactly two pre-existing unmapped bundle dirs — `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`. NAMED, NEITHER DELETED** (rule 31). *(Correction to the brief: `caiso285_instr_2024` has since been resolved and is no longer red.)* |
| `check_gate_a_provenance.py` | **1** | RED on other ISOs' markers. SOCO's only line is the NOTE *"has a keeper shard but no entry on the forecast board"*, which is **correct and deliberate** — card S10 routes the forecast namespace to the capx director. **No gate-(a) stamp was created** |
| `tests/unit/data/test_egrid_family_heat_rates.py` | **0** | 15 passed, incl. 2 new guard tests |

**One pre-existing test failure, named and not silently fixed:**
`tests/unit/config/test_data_profiles_tokens.py::test_soco_token_collides_with_no_other_raw_name` is
**red at HEAD independent of this lane** — its offenders are `campd-unit-outages-short-SOCO.csv` and
`thermal_tranches_SOCO.meta.json`, both pre-dating it; this lane's artifact does **not** appear in the
failure. Routed to the SOCO desk; a shared contract test is not patched from a calibration lane.

---

## 10. ROUTED ITEMS

| item | to |
|---|---|
| **SOCO-53d — a multi-week-campaign COMMITMENT mechanism.** The root cause of the `CT_PEAKER`/`ST_GAS` split, re-measured here: CC is at ≥99 % of its max in only 44 of 7,305 CT hours. NOT a gap bridge (`R`), NOT a pricing rule (`G`) | SOCO desk — **the top of the queue** |
| **E C Gaston (26)'s coal/gas-steam ST blend** (12.111 vs 10.887) — unreachable by a prime-mover construction; needs a FUEL-subfamily rate, a different mechanism | SOCO desk |
| **CAISO 50624 Torrance Refining** — 2 applied rows on a **2.800** boundary mismatch, inside the live CAISO keeper `2026-09-12-caiso-275-gascoupling`. Pinned by a TIGHT test assertion that fails once CAISO re-derives, so it cannot rot into a carve-out | CAISO desk |
| **NWPP-41's ERCOT-pooled PRB proxy reaches SOCO too** — SOCO has three PRB plants (6002 Miller, **6073 Daniel**, 6257 Scherer) priced off a pool of seven **Texas** plants. NWPP-41's census named MISO (12), PJM (2), SPP (3–5) and **missed SOCO** | SOCO desk |
| **`benchmark_semantics.OIL_GROUPS`** — `dashboard_add_run` auto-rebuilt SOCO's bench and this lane **reverted it**: applying the nyiso-239 repair to SOCO alone while seven ISOs stay stale is a cross-ISO decision | cross-ISO |
| 44/44 bench parts STALE repo-wide from `ed96378e` | cross-ISO / caiso-284's lane |
| `dashboard_add_run.py`'s docstring still describes the **removed** `[R-HOLDOUT]` registration marker gate (`enforce_registration_marker_gate` exists only in prose) | docs / `/sync-docs` |
| 2025 EIA-923 hydro input hole — **hydro is byte-identical** to the superseded run in all three years, confirming this seam does not touch it | SOCO-53b data-intake |
| `soco15_spp_arm` — dead committed bundle holding parity RED; **not deleted** (rule 31) | SOCO desk / owner |
| `test_soco_token_collides_with_no_other_raw_name` red at HEAD | SOCO desk |

---

## Log entry

## soco-53c — 2026-09-19 — the plant-blend repair lands, and its own artifact needed repairing first

SOCO's keeper is now `2026-09-19-soco53c-egrid-family-hr` (bundle `results/calibration/soco53c_family`, recoverable at `c91dde5e4cfbecd4e1da14ebba9209923ef9d500`), and `2026-09-17-soco53-measured-ct-hr` is superseded and pruned. The owner ruled promote on the standing standard that a structural gain with a gate regression may still be a keeper — and the case turned out stronger than that standard required, because the gates did not regress. C1 all 12/14 and free 8/10 on both sides, the same two rows fail, C2/C4/C6/C8 pass on both, zero ledgered and zero protective caveats on both, grade_summary identical, and no row changed status in either direction. The two failing rows moved only in magnitude (2023 CT_PEAKER +9.85 → +10.09 TWh, 2023 ST_GAS −7.34 → −7.36), and C2's ungated 2025 coal row improved from +16.0 % to +12.4 %. Determination is NOT-YET both ways, C3a/b/c remain unscorable because SOCO publishes no price and never will, the DOF ledger is unchanged at three entries and one residual, every offer band is still exactly 1.0 and `authorized_price_tuning` is declared NONE.

The arm is the rule 14 repair of a physically impossible input. eGRID joins heat rate at plant grain, so every generator at a multi-technology plant inherits one generation-weighted blend: Victor J Daniel Jr priced 1,004 MW of coal at 8.399 MMBtu/MWh, which no coal boiler can attain and against which its own meter reads 12.895, and Barry priced 1,118.5 MW of coal, 1,821.2 MW of gas CC and 160 MW of gas steam all at 8.994965. The construction gives each prime-mover family its own heat input over its own net generation from the same eGRID vintage the plant-grain join already reads — zero free parameters, a finer read of the identical source — and it moves 24 generator rows and 6,473.2 MW at four plants.

The lane's real product is that the mechanism's own artifact was wrong at five of its nine SOCO plants, and the existing guard caught only half of it. The derive claims a family rate replaces the blend on the identical net-annual boundary; that is an identity rather than a description, because the plant rate is the same ratio over the union of the families, so it can be checked. Checked, it partitions the nine plants with three orders of magnitude to spare: four recompose at ratio 1.000 and five at 4.05 to 8.40. The five are cogeneration paper mills, and the cause is eGRID's own convention — the plant rate's numerator is steam-credited at a CHP plant while the unit sheet's heat input is raw fuel, so a family rate there charges the host's process steam to the electric output, Pensacola recomposing to 22.537 against a published 5.568. The pre-existing `out_of_window` guard is a per-family plausibility test and caught only the steam halves; the turbine halves landed inside 3,000–30,000 Btu/kWh and were being applied — four rows, 160 MW, onto CT_CHP and CC_CHP, the latter a scored C1 row. That is rule 14's misalignment exception verbatim, so a per-plant `boundary_mismatch` flag now refuses them and SOCO's artifact goes from twelve applied rows to eight. The guard is derive-side and never consumer-side, because a default-on consumer guard would have moved CAISO's keeper fleet from this lane; no `src/market_sim` file is touched. Its tolerance is a rounding allowance incapable of being tuned — every value between 0.001 and 1.8 gives the identical partition over all 26 covered plants in the three ISOs that carry an artifact.

Rule 19 was settled mechanically rather than declared. The family rate applies at frame level in `_rows_to_generators` and `measured_ct_heat_rates` applies inside the row loop gated on CT_PEAKER, so the precedence is measured CAMPD, then eGRID family, then eGRID plant blend — and CT_PEAKER's cap-weighted heat rate is byte-identical at 11.2666 on both sides, meaning Greene County's computed GT family rate of 14.105 and Watson's 21.925 are both entirely overwritten and nothing is priced twice.

The effect was predicted before the solve and confirmed, including the part that is unflattering: the PRECOMMIT registered that CT_PEAKER and ST_GAS would not materially improve, so this arm does not fix SOCO's headline defect. Coal fell 0.665, 1.855 and 1.528 TWh, CC_REGULAR rose 0.468, 1.915 and 1.947, and CT_PEAKER moved only +0.234, +0.399 and +0.157, inside the declared one-TWh falsifier. Two of the lane's own predictions were imprecise and are recorded as such — the coal fall was over-predicted at two to five TWh against 0.7 to 1.9 delivered, and the flagged 2024 CC_REGULAR break did not occur. Why CT barely moves is measured rather than asserted: CC_REGULAR sits at or above 99 % of its own annual maximum in only 44 of the 7,305 hours CT_PEAKER runs in 2023, so the split is a commitment defect and no cost change at four other plants can reach it. The successor is SOCO-53d, a multi-week-campaign commitment mechanism.

A control solve was spent and answered a cross-ISO question. G-DRIFT classified thirteen of fourteen changed solve-path files inert and one live: commit `fba0ecd7` added an emissions-dual re-pricing that runs unconditionally at the end of every solve for every ISO, and its byte-identity claim was a scorer claim over committed artifacts that no re-solve had ever tested. Rule 29(b) earns a control solve for exactly that, so one was spent: the keeper's own recipe re-solved at the pinned SHA reproduces the committed keeper bundle to 0.000000 TWh on every class in every year, with the two run_configs differing by exactly one field sitting at its default. `fba0ecd7` is byte-identical on a real ISO and form 4 was valid. Both bundles also carry the new marginal emission rate — load-weighted mean 0.633, 0.616 and 0.635 tCO2/MWh, with the share of zone-hours at exactly zero immaterial at 0.00, 0.00 and 0.15 %, which corrects this lane's own expectation that SOCO's export-heavy posture would produce a material zero share. Record: `docs/handoffs/FINDING-soco-53c-2026-09-19.md`.
