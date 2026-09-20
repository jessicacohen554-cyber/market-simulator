# FINDING — SOCO-54 (2026-09-20): SOCO's gas steam was priced out of its own merit order by a contract multiplier, and removing it closes C1

**Lane** SOCO-54 · **Model** Opus · **DATA PROFILE** `soco` · **Parent LP cost: ZERO**.
**Keeper UNCHANGED** at `2026-09-20-soco53f-measured-coal-hr`. **Nothing was pruned.**
**PROMOTION IS OPEN AND IS THE OWNER'S** (rule 31 `[R-RETAIN]`; §11).

---

## 1. HEADLINE

`2026-09-20-soco54-marginal-gas-basis` (bundle `results/calibration/soco54_marginal_gas`) arms
**one** delta against the keeper: `gas_plant_monthly_fuel_pricing` **returned to its own shipped
default, `False`**. **Zero new `ScenarioConfig` fields. Zero free parameters.** DOF unchanged at
3 entries / 1 residual.

| bench | keeper `2026-09-20-soco53f-measured-coal-hr` | arm `2026-09-20-soco54-marginal-gas-basis` |
|---|---|---|
| **COMMITTED** | `NOT-YET` · C1 **13/14** · FAIL 2023 `CT_PEAKER` +9.727 TWh | **`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`** · C1 **14/14** · free **10/10** |
| **FRESH** (nyiso-240 repair) | `NOT-YET` · C1 13/14 · FAIL 2023 `CT_PEAKER` +9.758 | `NOT-YET` · C1 13/14 · FAIL **2024 `CC_REGULAR`** +7.505 |

**On BOTH benches the arm CLOSES 2023 `CT_PEAKER`** — the single failing row this lane was
commissioned on — from **+9.727 TWh / +4.05pp to +6.134 TWh / +2.55pp** against a ±3.00pp cap.
On the committed bench nothing else fails and **SOCO reaches its ceiling for the first time**:
0 ledgered, 0 protective caveats, C2/C4/C6/C8 all PASS, `grade_summary` 5 scored / 5 target /
0 fails.

**AND THE CEILING READING RESTS ON 0.05 TWh.** 2024 `CC_REGULAR` lands at **+7.417 TWh against a
±7.47 TWh band** — which `PRECOMMIT-soco-54` §8 **P4 pre-registered as this arm's stated risk, at
81 % of its margin**. On the fresh bench that same row is +7.505 and **FAILS**. The determination is
one bench-rebuild away from `NOT-YET`, and this document says so in its headline rather than its
footnotes.

---

## 2. THE HANDOFF'S ROUTED LEVER IS REFUSED ON MEASUREMENT, EX ANTE

The handoff routed this lane at SOCO's commitment physics, and required a stop if phase 0 said the
lever could not cross the distance. **It said exactly that.**

**(a) The campaign floor FIRES. It is not the constraint.** Measured at plant grain on the keeper's
own committed `unit_hourly_<y>.parquet`, P1:

| year | plant | online h | **median load frac while online** | share of ONLINE hours with `mc < price` | model TWh | actual TWh |
|---|---|---|---|---|---|---|
| 2023 | 728 Yates | 659 | **0.083** | **0.073** | 0.061 | 2.239 |
| 2023 | 26 Gaston | 1,734 | **0.066** | 0.295 | 0.557 | 1.654 |
| 2023 | 10 Greene Co | 2,938 | **0.137** | 0.348 | 0.574 | 1.314 |
| 2023 | 2049 Watson | 7,234 | 0.419 | 0.495 | 2.355 | 3.270 |

SOCO's gas steam is **committed and cannot generate**. The floor holds these boilers synchronized
for 659–7,234 hours a year — its job, done — and they sit **pinned at 6–14 % of capacity** because
they are **out of merit in 65–93 % of the hours they are online**.

**(b) The distance, and the ceiling of every commitment lever.**

> **In-merit-but-not-dispatched `ST_GAS` headroom, 2023: 0.0727 TWh** against a **−6.935 TWh** C1
> gap. **One percent.**

**(c) Three commitment levers refused EX ANTE, with reasons, instead of solved.**
A **start cost in the objective** — the `tranche_startup_amortization` `G`-cell's own named
successor (*"the successor object is COMMITMENT, not pricing"*) — amortizes to **≈$1.28/MWh** against
a **$17.44/MWh** distance, because the model's turbines run at **62–74 % CF in blocks up to 760
hours** and do not two-shift. A **CT min-run floor** raises CT energy: wrong sign. **Strengthening the
ST campaign floor** adds online hours, not MWh, and SOCO-53d already measured its incremental
marginal class as `CC_REGULAR` in 1,170 of 3,988 hours against `CT_PEAKER` in 681.

**No cell adjudicated `R`/`I`/`G` was re-tested.** `gas_commitment_bridge`'s `R`,
`tranche_startup_amortization`'s `G` and `coal_prb_proxy_own_iso`'s `I` all stand untouched. Rule 28
`[R-MECH-MATRIX]` (a) was discharged **before** the lever was picked, not after.

---

## 3. THE BENCHMARK IS SOUND — CHECKED FIRST, AS THE HANDOFF REQUIRED

The handoff required the benchmark be cleared before the +9.73 TWh was treated as a model defect,
and a stop if it were not.

- **The 148.57× Jack Watson flag is REAL and IMMATERIAL.** `2049:CT_PEAKER`'s EIA-923 slice is
  0.1985 TWh against a CAMPD gross of 0.0013 — a genuine CT-only reporter, correctly routed by
  `_flag_ct_only_reporters` to score its per-plant capture on the EIA-923 monthly row. Its whole
  magnitude is **4.4 % of the 4.534 TWh `CT_PEAKER` actual**, and C1 scores `classFull` (the EIA-923
  class sum), not the per-plant capture. It cannot explain +9.73 TWh.
- **No `CT_PEAKER` plant is missing from the class actual.** Two plants carrying 2.706 TWh of model
  energy are absent from the per-plant bench layer — **7709 Dahlberg** and **54538 Hartwell**. Both
  are **inside** `run_calibration_full._eia923_frame(2023, …, "SOCO")`, at 0.2397 and 0.2071 TWh; the
  class reconstructs to 4.5961 against `classFull`'s 4.5342 (the gap is the BTM subtraction and the
  vintage reconcile).
- **They are the model's two most over-dispatched plants**, 8.3× and 4.1× their actuals — **2.259
  TWh, 23 % of the gap, at two sites.** The opposite of a benchmark defect.

---

## 4. THE OBJECT — IT IS FUEL PRICE, AND THE CLAIM IS MEASURED RATHER THAN ARGUED

SOCO-53 closed the cost side with *"the model already over-separates `CT_PEAKER` from `ST_GAS` by
+1.983 MMBtu/MWh against a measured +0.713 … so no cost-side lever can close it."* **That was
derived from HEAT RATES alone and it holds there. It is not the whole cost side.**

| plant | class | HR | **$/MMBtu** | mc | model TWh | actual TWh |
|---|---|---|---|---|---|---|
| 54538 Hartwell | CT_PEAKER | 11.500 | **2.057** | **27.15** | 1.728 | 0.207 |
| 55141 Hawk Road | CT_PEAKER | 11.275 | **2.207** | **28.38** | 2.209 | 0.569 |
| 55244 Doyle | CT_PEAKER | 12.119 | **2.397** | 32.55 | 1.038 | 0.054 |
| 10 Greene County | ST_GAS | 10.207 | **3.550** | 40.23 | 0.574 | 1.314 |
| 26 E C Gaston | ST_GAS | 11.074 | **3.386** | 41.50 | 0.557 | 1.654 |
| **728 Yates** | **ST_GAS** | 10.797 | **3.759** | **44.59** | **0.061** | **2.239** |

**Same machine class (10.2–12.1 MMBtu/MWh). The separation is $1.0–1.7/MMBtu of FUEL**, which at
~11 MMBtu/MWh is the **$17.44/MWh** distance §2(b) measured.

**WHY THE PRINT IS NOT A MARGINAL COST — three measurements, all zero-LP, all before the solve.**

1. **Eight SOCO plants file ONE common monthly shape × a plant-constant multiplier, in ALL THREE
   YEARS**, at ratio CV ≤ **0.00081** over 10–12 months each (reference 54538 Hartwell; members
   55141, 55244, 7813, 7829, 7916, 728 Yates, 55128). Every other SOCO gas plant's ratio series has
   CV 0.03–1.63. These are **formula contract prices**.
2. **The multipliers REPRICE.** Yates goes **1.8279 → 1.1669 → 0.7959** against Hartwell; Hartwell
   goes from the family's cheapest member in 2023 to its **dearest** in 2025. **No physical property
   of those machines changed by 2.3× in two years.** A merit order built on them is ordered by
   contract terms on a commercial calendar, not by the cost of the next MWh — and the C1 residual
   tracks the contract, which is what a mis-based cost input looks like and what a physical one does
   not.
3. **Hartwell's 2023 print is BELOW Henry Hub in eleven of twelve months** ($1.66–2.26 against
   $2.15–3.27), which no *delivered* gas can be; and **the model burns 4×–160× the gas these plants
   procured** at the price the procurement established (55409 Calhoun 159.6×, 6124 McIntosh 26.1×,
   55244 Doyle 20.6×, 54538 Hartwell 8.0×) while burning **2 %** of Yates's procurement and **33 %**
   of Gaston's.

**The prints are genuine filings, not a loader artifact** — `scripts/data/process_f923_fuel_costs.py`
is a straight quantity-weighted aggregation of EIA-923 Schedule-2 receipts with no imputation.
What is wrong is their **basis**, and rule 14 `[R-ACCURATE]`'s misalignment clause is the governing
text. **The fall-back is MEASURED-TO-MEASURED**: realized Henry Hub ($2.54, the run's
`gas_price_override`) plus SOCO's **own** EIA-923 delivered-gas basis
(`GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64`, registered by SOCO-20 from those same receipts) = the
$3.179/MMBtu annual mean the rebuild reports — the same data, re-aggregated to the grain at which a
marginal dispatch decision is made.

The reasoning is **MISO-224's** (`miso_gas_marginal_commodity_pricing`, verbatim: *"the print is an
average cost measured on a different basis (rule 14 misalignment clause)"*), **derived here from
SOCO's own receipts and never transferred** (rules 25 `[R-ISO-SCOPE]` / 28(d)). MISO's applier is
MISO-scoped by hard error, is **not** armed here (machine-verified), and the cross-ISO cost
convention stays in owner court.

---

## 5. WHAT THE RUN DELIVERED

### 5.1 Class volumes, arm − keeper (TWh, P1)

| class | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---|---|---|
| `CT_PEAKER` | **−3.592** | **−1.494** | **−2.294** |
| `ST_GAS` | **+0.438** | −0.041 | +0.392 |
| `CC_REGULAR` | +1.701 | **+2.387** | +1.909 |
| `COAL_PRB` | **+1.481** | −0.713 | +0.138 |
| `COAL_BIT` | −0.000 | −0.067 | −0.157 |
| `CC_CHP` / `CT_CHP` / `ST_CHP` | 0.000 / +0.006 / 0.000 | 0.000 / −0.001 / 0.000 | 0.000 / +0.001 / +0.005 |
| nuclear, hydro, wind, solar, biomass, oil, OTHER | **0.000 in all three years** | | |

### 5.2 The scored C1 rows, COMMITTED bench (2025's seven are SKIPPED on the preliminary vintage)

| year | class | model | actual | Δ | share | status |
|---|---|---|---|---|---|---|
| 2023 | `CC_REGULAR` | 112.126 | 107.829 | +4.297 | +1.69pp | PASS |
| 2023 | `CT_PEAKER` | **10.668** | 4.534 | **+6.134** | **+2.55pp** | **PASS** (was FAIL) |
| 2023 | `ST_GAS` | 3.986 | 10.483 | −6.497 | −2.72pp | PASS |
| 2023 | `COAL_PRB` | 21.722 | 22.374 | −0.652 | −0.29pp | PASS |
| 2023 | `COAL_BIT` | 11.672 | 12.857 | −1.185 | −0.51pp | PASS |
| 2024 | **`CC_REGULAR`** | **112.414** | 104.997 | **+7.417** | +2.81pp | **PASS by 0.05 TWh** |
| 2024 | `CT_PEAKER` | 9.103 | 4.785 | +4.318 | +1.72pp | PASS |
| 2024 | `ST_GAS` | 3.554 | 8.879 | −5.325 | −2.14pp | PASS |
| 2024 | `COAL_PRB` | 20.569 | 24.719 | −4.150 | −1.70pp | PASS |

### 5.3 Per plant, 2023 — five plants brought to their actuals, two made worse

| plant | keeper | arm | actual |
|---|---|---|---|
| 54538 Hartwell | 1.728 | **0.111** | 0.207 |
| 55141 Hawk Road | 2.209 | **0.228** | 0.569 |
| 55244 Doyle | 1.038 | **0.072** | 0.054 |
| 6124 McIntosh | 0.682 | **0.053** | 0.017 |
| 10 Greene County | 0.574 | **1.196** | 1.314 |
| 728 Yates | 0.061 | **0.801** | 2.239 |
| 55409 Calhoun | 2.184 | 1.383 | 0.015 |
| **55061 Tenaska Georgia** | 1.412 | **2.690** | **0.237** |
| **2049 Jack Watson** (ST_GAS) | 2.355 | **1.256** | **3.270** |

### 5.4 Rule 17 `[R-FLOOR-WINDOW]` — HOLDS IN ALL FIFTEEN PLANT-YEARS, and the handoff's lead closes

Every binding share stays **at or below** that plant's own measured synchronized share, with
positive margin everywhere, and the floored blocks are campaigns (median **87–1,482 h**), not gap
fills. The handoff's lead table named Yates 2023 at 0.074 against 0.843 — *"an 11× under-commitment"*:

| plant | measured | keeper 2023 | **arm 2023** | arm 2024 | arm 2025 |
|---|---|---|---|---|---|
| 3 Barry | 0.0632 | 0.000 | 0.000 | 0.000 | 0.000 |
| 10 Greene Co | 0.7516 | 0.309 | **0.698** | 0.630 | 0.698 |
| 26 Gaston | 0.6392 | 0.197 | 0.238 | 0.260 | 0.361 |
| **728 Yates** | 0.8429 | 0.074 | **0.482** | 0.338 | 0.730 |
| 2049 Watson | 0.9202 | 0.808 | 0.557 | 0.470 | 0.776 |

**Yates goes from 11× under-committed to 1.7×**, Greene County to near-exact. Barry carries zero
floored hours in every year because the derive's ex-ante campaign-duty gate refuses it at a 6.3 %
synchronized share.

### 5.5 Legitimacy diagnostics and C8

**D-2 / C8 PASS** on both sides. `ST_GAS` forced share **RISES** — 0.0855 / 0.0966 / 0.1167 →
**0.1375 / 0.1253 / 0.1381** — against the 0.30 merchant cap, so C8 passes with wide margin.
**This falsifies P12** (§6). **D-4 off-window binding 0.0** in every year.
**D-1 goes 3 failures → 2**: it **CLEARS** 2024 `COAL_PRB` and 2025 `CT_PEAKER` and **ADDS** 2025
`COAL_BIT`; 2023 `COAL_BIT` is byte-identical and inherited. D-1 is REPORTED, not gated (the C7 gate
was retired at rubric v3.1), and the 2025 `CT_PEAKER` shape verdict clearing is independent
structural support — a criterion that scores no volume.

---

## 6. THIS LANE'S OWN PREDICTIONS, SCORED HONESTLY — **THREE OF TWELVE FALSIFIED**

| # | prediction | outcome |
|---|---|---|
| **P1** | 2023 `CT_PEAKER` falls **1.5–3.5** TWh (point −2.45) | **FALSIFIED — band too tight.** Delivered **−3.592**, outside the upper edge. Direction and object right, magnitude under-predicted. |
| **P2** | 2023 `ST_GAS` rises 0.3–1.2 TWh | **CONFIRMED** — +0.438. |
| **P3** | 2023 `CT_PEAKER` most likely STAYS FAILED; a flip is possible and would be narrow | **The flip happened.** +6.134 TWh / +2.55pp, inside ±7.19 and ±3.00. The hedge was right; the modal call was wrong. |
| **P4** | **STATED RISK: 2024 `CC_REGULAR` may cross to FAIL**, predicted +1.745 on a +2.16 headroom | **MATERIALIZED, AND IT IS BENCH-DEPENDENT.** Delivered **+2.387**. Committed bench: PASS by **0.05 TWh**. Fresh bench: **FAIL**. |
| **P5** | 2023 `ST_GAS` is the second thinnest row; fails if it worsens > 0.26 TWh | **CONFIRMED** — it improved. |
| **P6** | 2024 `CT_PEAKER` falls 0.8–2.0 TWh | **CONFIRMED** — −1.494. |
| **P7** | No 2025 C1 class row changes status | **CONFIRMED** — all seven SKIPPED. |
| **P8** | Coal and the unmoved classes each move < 1.0 TWh | **FALSIFIED on coal** — 2023 `COAL_PRB` **+1.481**. The cause was named before the solve (the year-invariant basis adds ≈+$1.65/MWh to 2023 gas and "moves the gas block against coal") but the band was too tight. Every mc-unmoved class held at exactly 0.000. |
| **P9** | CHP classes each move < 0.30 TWh | **CONFIRMED** — ≤ 0.006. |
| **P10** | `NOT-YET`; C2/C4/C6/C8 PASS; 0 caveats; DOF 3/1; zero fields | **PARTLY FALSIFIED, IN THE LANE'S FAVOUR.** Everything holds EXCEPT the determination: on the committed bench it is **`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`**, not `NOT-YET`. On the fresh bench P10 is exactly right. |
| **P11** | Rule 17 holds in all fifteen plant-years; the floor binds LESS | **CONFIRMED on the gate, WRONG on the direction** — rule 17 holds everywhere, but the floor binds **MORE**, not less. |
| **P12** | `ST_GAS` forced share FALLS | **FALSIFIED** — it rises 0.0855→0.1375 / 0.0966→0.1253 / 0.1167→0.1381. C8 still passes with wide margin. |

**The pattern in the three misses is one error**: I modelled the arm as *repricing* gas steam and
assumed it would therefore need **less** forcing and displace **less** coal. In fact cheaper gas
steam changes the **P0 run pattern** the campaign floor is detected from, so the floor commits it
for **more** hours (P11, P12), and the common basis lift moves the whole gas block against coal
harder than banded (P8). All three are second-order consequences of the same mechanism, and none
changes a gate.

---

## 7. A/B INTEGRITY, RULE 19, AND G-DRIFT

**Rule 19 `[R-ONE-MECH]`, established mechanically at two grains BEFORE the solve.** The six GAS
classes move on `fuel_prices` AND `mc_base`; **COAL, oil, nuclear, hydro, wind, solar and biomass
are at max |Δ| exactly 0.000000000000 in all three years.** The COAL print path
(`coal_plant_monthly_pricing`) is carried forward ON and untouched — machine-verified by
`gen_soco54_attestation._verify`, which raises rather than writing a false assertion.

**A/B integrity is EXACT, and content-addressing proves it.** Every arm leg's shared-input hashes
are **byte-identical to the keeper's own leg for the same year**:

| year | `eia923` | `campd` | keeper leg | arm leg |
|---|---|---|---|---|
| 2023 | `f673c8cbc2c0` | `de6ac32942f9` | ✓ | ✓ |
| 2024 | `ff74c049be0f` | `d3315305e444` | ✓ | ✓ |
| 2025 | `8350c0fcada6` | `f4048907807c` | ✓ | ✓ |

**G-DRIFT (rule 29 `[R-SCREEN]` (b)): ALL HUNKS INERT, so form 4 stood and NO CONTROL SOLVE WAS
SPENT.** Five files changed since the keeper basis `04f7f849` (+445/−11), each classified with its
reason verified mechanically: the new `caiso_citygate_blackout_bridge` field and its
`_basis_bridge_blackouts` helper (reached only inside that default-off CAISO branch);
`REGIONAL_RENEWABLE_CF` / `PPA_COST_RECOVERY_YR` (`grep -rl` returns only `build_mac_sidecar.py` and
`derive_regional_renewable_cf.py`, neither on the solve path); and `wind_ptc_levelized_per_mwh`
(capacity-evolution new entry, which a `mode="backcast"` run never reaches).

**The solve-surface fingerprint moved and it is not this lane's.** `60895cac1f7c8879` / 182 rows
against the keeper's `f4d250dfebdf2c96` / 180, with `moved_rows("SOCO")` = **`{}`** — zero existing
rows changed value. The delta is the same two undeclared `constants.py` names that have
`check_cache_key_registration` RED at HEAD. A fingerprint that grew by two undeclared names re-keys
the cache and **cannot change a number**.

**The E11 `--set` transport** is declared (PRECOMMIT §7) and machine-verified benign: the RESOLVED
`coal_prb_sigmoid_overrides` is **null** on every leg and on the composite.

---

## 8. GATES

| gate | state |
|---|---|
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, anchors (0 unresolvable), keeper stamps, §5.x prose headers, all three ratchets; the duty-(b) warning cleared once the cell and §5.8 note landed. |
| `audit_keepers --iso SOCO` | **E13 × 2 + E11 — ALL EXPECTED, RE-RAISED NOT CLEARED** (§8.1). |
| `check_registry_payload_parity` | **RED LOCALLY, GREEN IN CI** — six unmapped dirs, all this session's own **gitignored** leg bundles (`soco53f_arm_*` recovered, `soco54_arm_*` solved). Verified: all six are `git check-ignore`-clean and **0 files tracked on HEAD**. Rule 31's 2026-09-16 correction documents exactly this; **no result was deleted to clear it**. |
| `check_cache_key_registration` | **RED at HEAD, NOT THIS LANE'S** — `PPA_COST_RECOVERY_YR`, `REGIONAL_RENEWABLE_CF` (commit `3fc20b97`). Routed, not patched. |
| `check_bench_freshness` | **RED for SOCO** — the committed parts do not carry nyiso-240's repair. **Both benches scored and both reported.** The bench was reverted to committed and `metrics.json` rewritten on it. |
| `tests/…::test_soco_token_collides_with_no_other_raw_name` | **RED at HEAD, not patched** — a SOCO-desk naming decision, not a lane's to silently fix. |

### 8.1 E13 fires TWICE, for the sixth consecutive SOCO lane

Two registered SOCO runs are neither the keeper nor stamped to one: the inherited
`2026-09-20-soco53g-prb-own-iso` and this lane's `2026-09-20-soco54-marginal-gas-basis`. **Both are
candidates the owner has not ruled on.** Rule 31 `[R-RETAIN]` forbids deleting them; rule 30
`[R-TOUCHPOINT-FOLD]` (a) forbids inventing a `holdout.keeper` stamp. **E13 is re-raised, not
cleared.** It clears when the owner rules, not before.

---

## 9. ROUTED

1. **`GAS_BASIS_DIFFERENTIAL["SOCO"]` is the 2024 value applied to every year** — 0.64 against a
   measured +0.49 / +0.64 / +0.65, so 2023 carries +0.15 $/MMBtu (≈+$1.65/MWh) on every gas unit
   alike, and its own comment registered it as a *forward-year / fallback* value. Making it per-year
   is a rule 23 `[R-FROZEN-DERIVE]` re-derivation **on source data already committed in that
   comment**. **Not taken here** — it would make this a two-delta arm, and taking it after seeing
   the result would be selecting a parameter on the outcome.
2. **55061 Tenaska Georgia** — 1.412 → **2.690** TWh against a 0.237 actual. Made worse by this arm,
   and now the largest single `CT_PEAKER` miss after Calhoun.
3. **2049 Jack Watson** — the one `ST_GAS` plant whose mc RISES under the arm, pushed the wrong way
   (2.355 → 1.256 against 3.270).
4. **The `_shared/<ISO>` shard gap, and it is a PROMPT defect worth fixing for every lane.** The
   shards committed only their own out-dir, so `results/calibration/_shared/SOCO/` — gitignored and
   a *sibling* of that dir — never came back, and `dashboard_add_run` failed with a bare `TypeError`
   from `pd.read_parquet(None)`. `.gitignore` line ~2273 warns about exactly this. The parent
   repaired it at **zero LP** with `run_calibration_full.py --rebuild-benchmark` (11 s; **exactly one
   file changed, `meta.json`; all 34 other outputs byte-identical**). **A future shard prompt should
   either carry the `_shared/<ISO>` negation or state that the parent will rebuild it** — and
   `dashboard_add_run` deserves a real error message here.
5. **`derive_parasitic_load.py` has never been run for SOCO** — coal meter 0.866–0.928 against the
   committed 0.93 default, so every SOCO coal heat rate is biased LOW by 1.5–5.9 %. Cross-ISO intake
   (544 plants, 7 ISOs); reported, not taken.
6. **SOCO-53b, the 2025 hydro hole** — 0.327 TWh modelled against 6.012 measured. Untouched here
   (hydro byte-identical in all three years).
7. **Barry unit 4** — a 362 MW COAL model row CAMPD files as Pipeline Natural Gas.
8. **The cross-ISO formula-family question.** Five other keepers arm
   `gas_plant_monthly_fuel_pricing`. Whether their footprints carry constant-multiplier families is
   **their** lanes' question on **their** receipts (rules 25 / 28(d)). The one-line test: pivot
   `load_monthly_fuel_costs()` to `plant_id × month`, divide by a **fixed** reference row, report the
   ratio CV.

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** Phase 0, the `fleet_only` rebuilds, the greedy re-stack, composition,
  the floor re-measurement, the `--rebuild-benchmark` repair and all scoring are zero-LP.
- **Three shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)), all pinned to
  `d85e0c47567b0ae8258a99920d512fd3fe8fe1df`, each pushing a **full 16-file bundle** including
  `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 (a)). Peak memory
  2.64 GiB; every solve well inside the 20-minute ceiling.
- **Retrievability verified before anything was archived** (rule 34(d)): `git ls-tree` returns **16
  files** on each leg. Recovery by IMMUTABLE SHA, also recorded in `.gitignore` — the explicit
  `git fetch origin <sha>` is REQUIRED first:

  | leg | SHA |
  |---|---|
  | `soco54_arm_2023` | `0ccc7271232fc6bd1fdaf98a4b7e6080c97e3afd` |
  | `soco54_arm_2024` | `a4cf3a5f29e822ff8239752974fb1ddbf73d72d0` |
  | `soco54_arm_2025` | `50e747ca4cd11008d831f1679f9a5bde638e482b` |

  Re-compose at zero LP with `scripts/probes/soco54_compose_span.py --expect-print false`.
  **Per rule 33(f)(1) those shard branches are auto-deleted when this lane's PR merges, so these
  SHAs are PROVENANCE, not a durability claim — cost any leg recovery as a RE-SOLVE.**
- **WHAT SURVIVES ON `main`** (rule 33(f)(4)(ii)): the **composed, registered bundle**
  `results/calibration/soco54_marginal_gas` in its rule-15 slim shape (17 files: the four JSON +
  twelve `hourly/` sidecars + `run_config.json`), its registry sidecar, and its 292 KB run payload.
  **A promotion from that state costs ZERO re-solves.**
- **The three per-year legs are gitignored, NOT deleted** (rule 31; `.gitignore` discharges rule
  29(c), `rm` never does). **Nothing was deleted.**
- **The keeper's own legs were re-verified**: composing them with `--expect-print true` reproduces
  the committed keeper bundle's **twelve hourly sidecars BYTE-IDENTICALLY**, which both validated the
  composer before use and confirmed the recovered legs are the keeper.
- **All three shard sessions ARCHIVED** after fetch + checkout + verify + report-read (rule 33(a),
  (b), (e)). None left alive.

---

## 11. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — AND MY RECOMMENDATION

**SOCO's keeper is unchanged at `2026-09-20-soco53f-measured-coal-hr`. Nothing has been pruned.**
The candidate is **`2026-09-20-soco54-marginal-gas-basis`**, and `2026-09-20-soco53g-prb-own-iso`
remains open from the previous lane.

**MY RECOMMENDATION: PROMOTE IT** — and the case does not rest on the gates.

**The structural case (rule 1 `[R-STRUCT]`, which decides).** The keeper prices a dispatch decision
with an average delivered **contract** cost whose plant multiplier reprices by 2.3× in two years on
machines whose physics does not change. That is not a cost; it is a contract term, and it was
setting SOCO's merit order. Removing it is right **whatever the residual did** — and this run also
moves five plants from 4×–40× their actuals to within a factor of ~2, brings Yates's commitment from
11× under-committed to 1.7×, and clears 2025 `CT_PEAKER`'s diurnal-shape verdict, all on criteria
that score no volume. **Zero free parameters, zero new fields, and the field goes back to the default
the repo already ships.**

**The case AGAINST, stated at full strength.**
- The committed-bench ceiling reading **rests on 0.05 TWh** on 2024 `CC_REGULAR`, and on the fresh
  bench that row **FAILS**. A bench rebuild — which SOCO owes anyway — flips the determination back
  to `NOT-YET`. **Promoting on the strength of "SOCO reached its ceiling" would be promoting on a
  number that a pending data repair is likely to take away.**
- The arm's benefit is **concentrated in 2023** because that is where the contract spread was widest;
  2024 is materially weaker.
- **Two plants are made worse**, one of them by 1.28 TWh.
- **Three of my twelve pre-registered predictions were falsified.**

**Why I still recommend it:** none of those is a reason to keep a mis-based input. The bench
question is about which number we quote, not about which cost basis is correct; the 2023
concentration is a property of the defect, not of the lever; and the two worsened plants are the
successor's object, named in §9.

**If you promote**, the promoting session owes rule 35 `[R-PROMOTE]`: enumerate SOCO's registered
year union **before** pruning (it is `{2023, 2024, 2025}` and this bundle covers all three), verify
the incoming three stores with `audit_keepers` E1, then prune the outgoing keeper's three stores
with `prune_iso_runs.py --iso SOCO --force-uncite`, and re-key `calibration-complete.json`, the
keeper shard and the matrix stamp. **`2026-09-20-soco53g-prb-own-iso` needs its own ruling and must
not be swept up in this one.**

**If you decline**, say so and I will record it; the bundle stays registered as a candidate and the
keeper is untouched either way.

---

## Log entry

## soco-54 — 2026-09-20 — SOCO's gas steam was priced out of its own merit order by a contract multiplier, and removing it closes C1

**Keeper UNCHANGED** at `2026-09-20-soco53f-measured-coal-hr`; nothing pruned. Registered
`2026-09-20-soco54-marginal-gas-basis` (bundle `results/calibration/soco54_marginal_gas`) as a
**candidate; promotion is OPEN and is the owner's** (rule 31 `[R-RETAIN]`). Full 2023–2025 span, one
shard per year (rule 36), composed at zero LP; G-DRIFT all-INERT so form 4 stood and **no control
solve was spent**.

**The arm is one field turned OFF** — `gas_plant_monthly_fuel_pricing` back to its own shipped
default. **Zero new fields, zero free parameters**, DOF 3 entries / 1 residual unchanged.

**RULE 28(a) FIRST.** `gas_commitment_bridge` (`R`), `tranche_startup_amortization` (`G`),
`coal_prb_proxy_own_iso` (`I`) all left untouched; the arm sits on a `U` cell.

**THE ROUTED LEVER WAS REFUSED EX ANTE ON MEASUREMENT.** The campaign floor already holds SOCO's
boilers online 659–7,234 h/yr **pinned at a median 6–14 % of capacity**, out of merit in 65–93 % of
those hours (Yates 2023: online 659 h, in-merit in 7.3 %). In-merit-but-off `ST_GAS` headroom is
**0.0727 TWh against a −6.935 TWh gap**. A start cost amortizes to ≈$1.28/MWh against a $17.44/MWh
distance, on turbines running 62–74 % CF in blocks up to 760 h.

**THIS CORRECTS THE 53/53c/53e/53f DIAGNOSIS.** "No cost-side lever can close it" was derived from
**heat rates alone** and holds there. The separation that binds is **FUEL PRICE**: eight SOCO plants
file one common monthly shape × a plant-constant multiplier in **all three years** at CV ≤ 0.00081,
and the multipliers **reprice** — Yates 1.8279 → 1.1669 → 0.7959 against Hartwell, whose own 2023
print sits below Henry Hub in 11 of 12 months. The model burned **4×–160×** the gas these plants
procured. Rule 14's misalignment clause governs; the fall-back is **measured-to-measured** (realized
Henry Hub + SOCO's own EIA-923 basis, SOCO-20).

**RESULT — BOTH BENCHES, BECAUSE THEY DISAGREE ON ONE ROW.** Committed: arm
**`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`**, C1 **14/14 · free 10/10** — SOCO's ceiling, first time
— vs keeper `NOT-YET` / 13/14. Fresh: both `NOT-YET` / 13/14, failing row **moves** from 2023
`CT_PEAKER` to 2024 `CC_REGULAR`. **On both benches 2023 `CT_PEAKER` CLOSES**: 14.261 → 10.668 TWh
(actual 4.534), +4.05pp → **+2.55pp** against ±3.00pp. **The ceiling rests on 0.05 TWh** — 2024
`CC_REGULAR` at +7.417 of ±7.47, which PRECOMMIT P4 pre-registered as this arm's risk at 81 % of its
margin. C2/C4/C6/C8 PASS; C3a/b/c UNSCORABLE; 0 ledgered, 0 protective.

**Plant grain 2023:** Hartwell 1.728 → 0.111 (0.207), Hawk Road 2.209 → 0.228 (0.569), Doyle 1.038 →
0.072 (0.054), McIntosh 0.682 → 0.053 (0.017), Greene Co 0.574 → 1.196 (1.314). **Against the lane:**
Tenaska Georgia 1.412 → **2.690** (0.237) is made worse; Jack Watson 2.355 → 1.256 (3.270) moves the
wrong way; Yates still at 36 % of actual. **Rule 17 holds in all fifteen plant-years** and Yates's
commitment goes from **11× under to 1.7× under**. D-1 **3 failures → 2**.

**THREE OF TWELVE PREDICTIONS FALSIFIED** and §6 leads with them: P1's band too tight (−2.45 vs
**−3.592**), P8's coal band too tight (<1.0 vs **+1.481** `COAL_PRB`), P12's forced-share direction
wrong (it **rises**, 0.0855 → 0.1375, C8 still passing wide). All three are second-order
consequences of one modelling error — cheaper gas steam changes the P0 pattern the floor is detected
from.

**Gates:** matrix PASS; `audit_keepers` **E13 × 2** (two unruled candidates — 53g's and this one,
**re-raised not cleared**) + E11 (pruned predecessor); parity RED **locally only** (six gitignored
leg dirs, 0 tracked on HEAD); `check_cache_key_registration` and `check_bench_freshness` RED at HEAD,
not this lane's. **Nothing was deleted.** All three shards archived. **Promotion question put to the
owner.**
