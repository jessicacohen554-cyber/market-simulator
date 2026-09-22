# FINDING — SOCO-58 (2026-09-22): the model charged a $100/MW cold start to a boiler its own dispatch never let go out

**Lane** SOCO-58 · **DATA PROFILE** soco · **Model** Opus 5 (rule 27 `[R-PUSH]` — scope writes
`scripts/`).
**Control of record** `2026-09-20-soco57-measured-cc-heat`
(`results/calibration/soco57_measured_cc_hr`), rule 29 `[R-SCREEN]` (b) **form 4**, no control solve.
**Arm** `coal_warm_committed = True` — ONE existing default-off `ScenarioConfig` field
(`scenarios.py:12202`). **Zero new fields, zero new artifacts, zero free parameters.**
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-58-2026-09-21.md`, pushed at
`f10ed9b93f4366fa279918d46fca3c8f9cc38029` **before any LP was solved**.

---

## 1. HEADLINE

### (1) THE OBJECT SOCO-57 NAMED IS A FABRICATED COST, AND THE CODE'S OWN COMMENT NAMES IT

`model/commitment.py::compute_monthly_markup` adds a P1 bid markup of
`startup_cost / max(avg P0 run length, 1.0 h)`. SOCO's six coal `_committed` tranches each carry an
NREL **$100/MW cold start**, and in 2024 **four of the six had ZERO P0 runs**, so the amortization
hit its floor and the markup was **exactly $100.00/MWh**:

| plant | name | `mc_base` 2024 | **P1 bid** | **markup** | avail TWh | gen TWh |
|---|---|---|---|---|---|---|
| 26 | Gaston | 76.958 | **176.958** | **+100.000** | 0.111 | **0.000** |
| 703 | Scherer | 57.585 | **157.585** | **+100.000** | 5.147 | **0.000** |
| 6073 | Daniel | 41.900 | **141.900** | **+100.000** | 0.135 | **0.000** |
| 6257 | Bowen | 40.042 | **140.042** | **+100.000** | 5.597 | **0.000** |
| 3 | Barry | 31.056 | 44.812 | +13.756 | 0.200 | 0.002 |
| 6002 | Miller | 26.936 | 35.283 | +8.347 | 9.537 | 0.907 |

**20.73 TWh of available committed coal capacity producing 0.909 TWh**, into a market whose median
clearing price that year was **$28.27/MWh**. That is the run-97b inversion the warm-boiler branch's
own comment names — *"turning the design's cheap base band into a near-peak band."*

### (2) THE PHYSICS PREDICATE IS 100.0 % IN ALL EIGHTEEN COAL PLANT-YEARS

In every hour in which a plant's `_committed` tranche carries capacity, that plant's `_mustrun`
tranche is generating **at load fraction 1.00**:

| year | p3 | p26 | p703 | p6002 | p6073 | p6257 |
|---|---|---|---|---|---|---|
| 2023 | 8760/8760 | 2976/2976 | 8760/8760 | 8760/8760 | 5376/5376 | 8232/8232 |
| 2024 | 8760/8760 | 2832/2832 | 8760/8760 | 8760/8760 | 6240/6240 | 8760/8760 |
| 2025 | 8760/8760 | 4008/4008 | 8736/8736 | 8760/8760 | 6456/6456 | 8760/8760 |

**The boiler is never dark when the charge applies.** A vertically-integrated, cost-based utility
does not decline to raise output on an already-synchronised boiler because of a start it is not
paying for.

### (3) WHY 2024 IS DIFFERENT IS A P0 FEEDBACK, NOT AN INPUT

Inverting `markup = $100 / max(avg P0 run, 1.0)` gives each tranche's own implied P0 run length:

| year | p3 | p26 | p703 | p6002 | p6073 | p6257 |
|---|---|---|---|---|---|---|
| 2023 | 0.8 h | 0.8 h | 1.0 h | 17.5 h | 1.0 h | 1.0 h |
| 2024 | 7.3 h | 1.0 h | 1.0 h | 12.0 h | 1.0 h | 1.0 h |
| **2025** | **137.0 h** | 0.8 h | **7.9 h** | **769.2 h** | **10.4 h** | **11.4 h** |

At Miller (6002), the fleet's largest coal plant:

| year | price p50 | de-markup `mc` | margin | markup | bid | at p50 |
|---|---|---|---|---|---|---|
| 2023 | $32.10 | $27.95 | +$4.15 | $5.72 | $33.67 | OUT |
| **2024** | **$28.27** | **$26.94** | **+$1.33** | **$8.35** | **$35.29** | **OUT** |
| 2025 | $39.57 | $28.01 | +$11.56 | **$0.13** | $28.14 | **IN** |

**The markup is ANTI-CORRELATED with the year's need for coal**: a self-reinforcing lockout that
bites hardest in the lowest-price year. It is the mirror of the v2 circularity `_amortized`'s own
docstring records being removed for fast starts (*"too-cheap offers → long P0 blocks → ≈0 markup →
the lever self-disables"*); coal carries no `fast_start_run_hours` basis, so coal still runs on v2,
in the direction that self-**REINFORCES**.

### (4) AND THE RESULT IS THE FIRST SOCO PROMOTION IN FOUR LANES THAT DOES NOT NEED THE RULING'S SECOND CLAUSE

`C4` goes **FAIL → PASS**, `grade_summary` **5/3/2 → 5/4/1**, and the single remaining failing C1
row improves on **both** legs. **That is exactly why this lane argued the case on structure and said
so before the solve** — `PRECOMMIT-soco-58` §8: *"If the only argument for this arm were that C4 2024
coal flips, it would not be taken."*

---

## 2. THE HANDOFF'S THREE READINGS, ADJUDICATED ON MEASUREMENT BEFORE ANY LP

### (1) COAL AVAILABILITY / OUTAGES IN 2024 — **REFUSED. It moves the wrong way across years.**

The SOCO-56 contradiction test, re-run on the current keeper after the per-unit crosswalk landed,
coal-scoped — hours in which the model's ceiling sits BELOW the plant's own measured CAMPD output:

| year | fleet TWh forbidden | largest plant | coal availability | coal generation | util |
|---|---|---|---|---|---|
| 2023 | 1.295 | 6002 Miller 0.899 | 57.377 | 31.488 | 0.549 |
| **2024** | **2.059** | 6002 Miller 1.224 | 60.566 | 30.478 | 0.503 |
| 2025 | **2.758** | 6002 Miller **1.862** | 60.288 | 46.215 | **0.767** |

**2025 carries the MOST forbidden energy and the LEAST shortfall** — it is the year coal runs
+3.251 TWh OVER. The residue is the CAMPD-gross vs model-net-summer wedge SOCO-56 §3 already named as
the fleet-wide baseline. **Coal availability is flat at 57–61 TWh across all three years while
generation swings 30.5 → 46.2 TWh. Availability is not what changed.**

### (2) COAL OFFER LEVEL — the two named instruments stay REFUSED ON SIGN; the object is a different defect

`coal_takeorpay_SOCO.csv` (absent) and `derive_parasitic_load.py` (never run for SOCO) both make coal
MORE expensive, the wrong sign for a short `COAL_PRB` — SOCO-56 §2(c) refused them on that ground and
nothing here reopens it. **This lane's object is not a fuel cost: it is a fabricated cold-start
premium.**

### (3) THE 2025 HYDRO HOLE — MEASURED, ROUTED, NOT ARMED (rule 19 `[R-ONE-MECH]`)

0.327 TWh modelled against 6.012 measured; coal backfills it. **Correcting hydro would push 2025 coal
DOWN by up to ~5.7 TWh — the direction that would absorb this arm's 2025 overshoot.** It is this
lane's **named successor**, not its lever.

---

## 3. RULE 19 `[R-ONE-MECH]` — AND THE INVERSE OF SOCO-57's TRAP

**The fleet grains read EXACTLY ZERO, and that is the CORRECT signature.** The mechanism lives
entirely at the P0→P1 seam (**one** call site, `pipeline/solve.py:518` — not the four the
measured-heat-rate family needs). Measured on a `fleet_only` rebuild, arm vs control, 2024:

| `fuel_prices` | `mc_base` | `pmax` | `availability` | `heat_rate` |
|---|---|---|---|---|
| **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | **0.000000000000** · 0 | **0.000000000000** · 0 |

…while the **RESOLVED** `scenario_config.coal_warm_committed` reads `False` → `True`.

> **SOCO-57 §4's lesson applies in reverse and a successor must not confuse the two cases.** There,
> all-grains-zero meant *an arm that never armed*. Here it is **required**, and the resolved-config
> assertion is the ONLY thing that can distinguish an armed leg from a control — which is why
> `soco58_compose_span.assert_delta` reads the resolved `scenario_config`, never the
> `prb_overrides` bag, and was verified to refuse a control offered as the arm **and** accept one
> offered as a control before any leg was composed.

**P0 is byte-identical** (P0 solves on `mc_base`, which does not move), so the displaced classes' own
P0 run lengths — and therefore their own markups — are unchanged.

**Scope is exact, verified by execution** in `gen_soco58_attestation._verify_scope`, which raises on
any drift: **6 of 6** coal tranches carrying a startup cost exempted (all `_committed`, 3,464.0 MW),
**0** coal tranches paying the markup but missed, **0** non-coal tranches touched.

---

## 4. WHAT THE RUN DELIVERED

**Run `2026-09-22-soco58-warm-committed`, bundle `results/calibration/soco58_warm_committed`,
composed at zero LP from three per-year shards** (rule 36 `[R-YEAR-ISOLATION]` (a)).

### 4.1 Gates

| gate | control | **arm** |
|---|---|---|
| **determination** | `NOT-YET` (rubric v3.8, PRICE UNSCORED) | **`NOT-YET`** |
| **C1 fuel-mix** | FAIL · 13/14 all · 9/10 free | **FAIL · 13/14 all · 9/10 free** |
| **C2 system volume** | PASS | **PASS** |
| **C3a / C3b / C3c** | SKIPPED — UNSCORABLE | **SKIPPED — UNSCORABLE** |
| **C4 dispatch correlation** | **FAIL** (2024 coal) | **PASS** |
| **C6 governance** | PASS | **PASS** |
| **C8 forced share** | PASS | **PASS** |
| caveats | 0 ledgered · 0 protective | **0 ledgered · 0 protective** |
| `grade_summary` | scored 5 · target **3** · fails **2** | scored 5 · target **4** · fails **1** |
| DOF | 6 entries / 1 residual | **7 entries / 1 residual** |

### 4.2 C4 — five of six rows improve, and the failing one clears by 0.060

| year | fuel | control | **arm** | |
|---|---|---|---|---|
| 2023 | coal | r 0.882 / NRMSE 0.258 | **r 0.897 / NRMSE 0.214** | improves |
| 2023 | gas | r 0.951 / NRMSE 0.102 | r 0.946 / **NRMSE 0.094** | improves |
| **2024** | **coal** | r 0.829 / **NRMSE 0.309 — FAIL** | **r 0.847 / NRMSE 0.240 — PASS** | **the object** |
| 2024 | gas | r 0.950 / NRMSE 0.132 | r 0.940 / **NRMSE 0.122** | improves |
| 2025 | coal | r 0.882 / NRMSE 0.167 | r 0.883 / **NRMSE 0.206** | **worsens, passes** |
| 2025 | gas | r 0.955 / NRMSE 0.088 | r 0.949 / **NRMSE 0.083** | improves |

**WHY IT WAS PREDICTABLE.** `NRMSE = RMSE / mean(actual)`. Decomposing each coal year against its own
EIA-930 hourly series **before the solve**:

| year | bias / mean | **shape residual** | NRMSE |
|---|---|---|---|
| 2023 | 0.177 | **0.188** | 0.258 |
| **2024** | **0.246** | **0.186** | **0.309** |
| 2025 | 0.049 | **0.160** | 0.167 |

**The shape residual is nearly identical in all three years. What differs is the LEVEL BIAS.** 2024
coal was failing a shape gate on a level error — the model was 9.97 TWh (−24.6 %) short of the series
it is scored against — so adding coal volume was the direct repair, and the decomposition said by how
much.

### 4.3 The scored C1 rows

| year | class | control Δ | **arm Δ** | control share | **arm share** | status |
|---|---|---|---|---|---|---|
| 2023 | `CC_REGULAR` | +6.28 | **+5.83** | +2.5 | **+2.3** | PASS |
| 2023 | `CT_PEAKER` | +5.97 | **+4.65** | +2.5 | **+1.9** | PASS |
| **2023** | **`ST_GAS`** | −6.47 | **−6.86** | −2.7 | **−2.9** | **PASS — 0.32 TWh / 0.13 pp margin** |
| 2023 | `COAL_PRB` | −2.33 | **−0.14** | −1.0 | **−0.1** | PASS |
| 2023 | `COAL_BIT` | −1.24 | −1.24 | −0.5 | −0.5 | PASS |
| **2024** | **`CC_REGULAR`** | **+11.05** | **+10.42** | **+4.2** | **+4.0** | **FAIL — better on BOTH legs** |
| 2024 | `CT_PEAKER` | +2.97 | **+0.88** | +1.2 | **+0.3** | PASS |
| 2024 | `ST_GAS` | −5.75 | **−6.37** | −2.3 | **−2.6** | PASS |
| **2024** | **`COAL_PRB`** | **−5.78** | **−2.40** | **−2.4** | **−1.0** | **PASS — margin 1.69 → 5.06 TWh** |
| 2024 | `COAL_BIT` | −0.71 | −0.78 | −0.3 | −0.3 | PASS |
| *2025 (SKIPPED)* | `COAL_PRB` | *+3.25* | *+4.65* | | | *ungated* |
| *2025 (SKIPPED)* | `COAL_BIT` | *+0.98* | *+2.47* | | | *ungated* |

### 4.4 Check E — per-plant coal allocation

Σ|model − actual| over the six coal plants:

| year | control | **arm** | |
|---|---|---|---|
| 2023 | 7.444 TWh | **5.929** | **−20.4 %** |
| **2024** | **13.316 TWh** | **9.869** | **−25.9 %** |
| 2025 | 8.021 TWh | 7.957 | −0.8 % |

| plant | 2024 control | **2024 arm** | actual | ratio before | **ratio after** |
|---|---|---|---|---|---|
| **6002 Miller** | 12.109 | **15.486** | 18.597 | 0.651 | **0.833** |
| 6257 Bowen | 5.601 | 5.605 | 7.034 | 0.796 | 0.797 |
| 703 Scherer | 8.127 | 8.127 | 10.712 | 0.759 | 0.759 |
| 3 Barry | 2.427 | 2.361 | 0.698 | 3.480 | 3.384 |

**Scherer and Gaston do not move at all**, because their de-marked-up committed bids are $57.58 and
$57.54 against a $28.27 price — Scherer's delivered coal is $5.10/MMBtu against Miller's $2.10.
**Routed, §7.**

### 4.5 Legitimacy

**D-1 failing rows fall 3 → 2**, and the row the object sits on is repaired:

| year | class | control | **arm** |
|---|---|---|---|
| **2024** | **`COAL_PRB`** | cv_ratio **0.448 — FAIL** (model_cv 0.055) | **cv_ratio 0.932 — pass** (model_cv 0.114) |
| 2023 | `COAL_PRB` | cv_ratio 0.627 | **0.815** |
| 2025 | `COAL_PRB` | cv_ratio 0.553 | **0.723** |
| 2025 | `COAL_BIT` | cv_ratio 1.201 | **2.749** |
| **2023** | **`COAL_BIT`** | profile_r **0.436** — FAIL | profile_r **0.000** — FAIL *(worse)* |

The model's coal was **too FLAT** — which is exactly what a fleet pinned at its must-run floor looks
like. The 2023 `COAL_BIT` regression is real and is reported: that class is now exactly its must-run
floor in every hour, hence perfectly constant, so its correlation is undefined and reads 0.

**C8**: `ST_GAS` forced share 0.1296 / 0.1304 / 0.1473 → **0.1493 / 0.1701 / 0.1823** (its denominator
falls), all far under the 0.30 merchant cap. No COAL row appears in D-2 either side. **D-2 / D-4 /
D-5 / D-9 / D-10 PASS both sides.**

**C5a CO2 (REPORTED-ONLY, contributes no status)**: −7.7 / −12.3 / +2.3 % → **−6.7 / −10.8 / +3.3 %**.

---

## 5. THIS LANE'S OWN PREDICTIONS — **15 CONFIRMED, 4 PARTIAL, 0 FALSIFIED**

| # | prediction | outcome |
|---|---|---|
| **P1** | C4 2024 coal FLIPS to PASS; NRMSE `0.20…0.28`, r `0.83…0.90` | **CONFIRMED** — **0.240 / 0.847** |
| **P2** | 2024 `COAL_PRB` → `−4.0…+0.5 TWh`, stays PASS | **CONFIRMED** — **−2.40** |
| **P3** | 2024 `CC_REGULAR` improves, still FAILS both legs; `+9.0…+10.6 TWh`, `+3.5…+4.05 pp` | **CONFIRMED** — **+10.42 / +4.0** |
| **P4** | 2023 `ST_GAS` `−6.8…−7.6 TWh`, `−2.85…−3.19 pp`; MAY cross to FAIL (~40 %) | **CONFIRMED** — **−6.86 / −2.92**, did not cross |
| **P5** | 2023 C4 coal improves to `0.19…0.245` | **CONFIRMED** — **0.214** |
| **P6** | 2025 C4 coal worsens but passes; `0.19…0.28` | **CONFIRMED** — **0.206** |
| **P7** | 2023 `CC_REGULAR` `+4.4…+5.7`, `CT_PEAKER` `+2.0…+4.4` | **PARTIAL** — **+5.83** and **+4.65**, both just ABOVE their bands |
| **P8** | 2024 `CT_PEAKER` → `−0.9…+1.6 TWh` | **CONFIRMED** — **+0.88** |
| **P9** | 2024 `ST_GAS` → `−6.2…−7.1 TWh`, stays PASS | **CONFIRMED** — **−6.37** |
| **P10** | allocation falls: 2023 `7.444 → 4.0…5.6`, 2024 `13.316 → 8.0…10.9`; 2025 direction refused | **PARTIAL** — 2024 **9.869** confirmed; 2023 **5.929** just above its band; 2025 −0.8 % |
| **P11** | D-1 2024 `COAL_PRB` cv_ratio rises from 0.448; `0.50…0.80` | **PARTIAL** — **0.932**, well above the band |
| **P12** | rule 19: exactly 0.000000000000 on all five grains; resolved flag true in all three legs | **CONFIRMED** |
| **P13** | C8 PASS; `ST_GAS` forced share `0.14…0.20`; no COAL D-2 row | **CONFIRMED** — 0.149 / 0.170 / 0.182 |
| **P14** | DOF 6 → 7 entries, residual 1 unchanged, `n_scalars=0`, SOCO-cited source | **CONFIRMED** |
| **P15** | no peer ISO moves | **CONFIRMED** |
| **P16** | 2025 coal further over, stays SKIPPED; C2 2025 coal `+16…+25 %` | **CONFIRMED** — **+20.9 %** |
| **P17** | determination stays `NOT-YET`; fails 2 → 1 if P1 holds and P4 does not cross | **CONFIRMED** — **5 / 4 / 1** |
| **P18** | rule 17 holds in all 18 coal plant-years; no floor row moves | **CONFIRMED** |
| **P19** | P0 byte-identical | **CONFIRMED** |

**THE FOUR PARTIALS ARE REPORTED AS MISSES AND THEY SHARE ONE ROOT CAUSE — WHICH IS THE OPPOSITE OF
THE ONE SOCO-57 NAMED.** SOCO-57 §6 measured that its greedy re-stack *systematically UNDERSTATED*
every movement and told a successor to *"widen its bands by roughly 2× in the direction of the
correction."* This lane did that, and the bound turned out to **OVERSTATE in 2023** (predicted COAL
+2.965, actual **+2.189**) while **UNDERSTATING in 2024** (predicted +2.986, actual **+3.313**).

> **THE GREEDY BOUND IS NOISY, NOT DIRECTIONALLY BIASED. A successor should band it SYMMETRICALLY
> rather than skewing toward understatement — SOCO-57's advice, followed faithfully, produced all
> four of this lane's misses.**

---

## 6. THE GOVERNANCE READING — STATED, NOT SETTLED (rule 28 `[R-MECH-MATRIX]` (a))

`coal_warm_committed` is **not a matrix row**: the base matrix registers it *inside* the
`tranche_startup_amortization` row's `def`, as a sub-scalar of that family (rule 28 (c), xiso-3
census). **SOCO's cell for that family is `G` — GOVERNANCE-REFUSED EX ANTE, NO REOPEN CONDITION**
(SOCO-53), because the mechanism *"puts start costs INTO THE CLEARING PRICE"* and SOCO has none.

**THE TWO CLASS-SCOPED GATES IN THAT FAMILY HAVE OPPOSITE POLARITY**, which SOCO-53 did not
distinguish:

| gate | OFF means | SOCO measures |
|---|---|---|
| `gas_st_startup_cost` | **NO** markup (ST_GAS skipped) | ST_GAS committed markup **exactly −0.000** ✓ |
| `coal_warm_committed` | markup **APPLIED** | coal committed markup **+$100.00** ✗ |

**So SOCO-53's premise — "with `tranche_startup_amortization` off …" — was never true of SOCO's
coal.** The family is **ON BY DEFAULT** there, no master gate turns it off, and a footprint with no
clearing price was carrying $140–177/MWh start-cost bids: the very object the `G` cell refuses.
**Arming the exemption ENFORCES that cell's own position rather than reopening it.**

**THE CELL IS NOT FLIPPED.** `tranche_startup_amortization` stays **`G`** for SOCO; only its `ev` is
extended with this measurement. **The boundary is genuinely ambiguous and is put to the owner.**

**DELIBERATELY NOT EXTENDED TO CT_PEAKER.** Ten CT plants carry the identical +$20.00/MWh
1-hour-run saturation. Not taken — and the reason that **binds** is physical: a combustion turbine
with no must-run floor **genuinely does cold-start**, so no warm-boiler argument exists for it. (That
`CT_PEAKER` is also already over in 2024 is recorded as **not** the reason, so the scoping reads as
physics rather than convenience.)

---

## 7. ROUTED

1. **THE 2025 HYDRO HOLE IS THE NAMED SUCCESSOR** (SOCO-53b). 0.327 TWh modelled against 6.012
   measured; coal backfills it, and correcting it would push 2025 coal DOWN by up to ~5.7 TWh —
   the direction that absorbs this arm's 2025 overshoot. Instruments: `--hydro-backfill-year` /
   `--hydro-eia930-monthly`.
2. **SCHERER (703) AND GASTON (26) DO NOT MOVE**, because their de-marked-up committed bids are
   $57.58 and $57.54 against a $28.27 price. Scherer's delivered coal is **$5.10/MMBtu** against
   Miller's **$2.10** — a per-plant coal fuel-price question this lane does not touch.
3. **BARRY (3) IS THE FLEET'S LARGEST PER-PLANT COAL OVER-RUN** — 3.48× its own actual in 2024 and
   5.67× in 2025 — and the arm does not touch it. Its fleet row still follows a stale EIA-860 that
   files unit 4 as Conventional Steam Coal while CAMPD measures it burning Pipeline Natural Gas
   (SOCO-56 §3 resolved the OUTAGE routing; the FLEET row is untouched).
4. **THE `ST_GAS` SHORTFALL THIS ARM DEEPENS** is SOCO-12 §4's unmodelled within-footprint gas
   dispersion, measured by SOCO-54 §4 at **$1.0–1.7/MMBtu** between SOCO's gas steam and its CTs.
   No free public daily index exists at SONAT or Transco/Dalton. 2023 `ST_GAS` is now the run's
   thinnest passing row at **0.13 pp**.
5. **CT_PEAKER's own +$20.00/MWh 1-hour-run markup** — the same arithmetic, deliberately not taken
   (§6). If a successor wants it, the argument must be about CT start physics, not about this one.
6. Inherited and untouched from SOCO-57 §9: the over-dispatched CC tail; the two boundary-refused
   CC plants (533 McWilliams, 7946 Wansley U9); the `ST_GAS` denominator
   (`unit_outage_extract_basis_share`, ≤ 0.0071 TWh); **the tranche half of
   `campd_per_unit_attribution`, still a live landmine**; `derive_parasitic_load.py`, never run for
   SOCO's coal or gas-steam classes.

---

## 8. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** Phase 0, the `fleet_only` rebuilds, the greedy re-stack, the composition,
  `--rebuild-benchmark`, the diagnostics and all scoring are zero-LP (rule 32 `[R-SHARD]` (a)).
- **Three shards, ONE YEAR EACH** (rule 36 (a)), all pinned to
  `f10ed9b93f4366fa279918d46fca3c8f9cc38029`, each pushing a **full 16-file bundle** including
  `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34 (a)).
- **Leg SHAs** (rule 33 (d) — **provenance, NOT a durability claim**; cost any recovery as a
  re-solve):

  | leg | SHA |
  |---|---|
  | `soco58_arm_2023` | `6ad08eed8ea3289ad76301831a90b35cb81a4f9a` |
  | `soco58_arm_2024` | `605be037f0caf0bd71a22ffe57bcdbc6182e7e46` |
  | `soco58_arm_2025` | `74a1802e6492b34f13818e3a63decabdb0a423fe` |

- **RETRIEVABILITY (rule 34 (e)): the registered keeper bundle
  `results/calibration/soco58_warm_committed` is COMMITTED ON `main`**, in its rule-15 shape, with
  its registry sidecar and run payload. A promotion from that state costs **zero re-solves**. The
  per-year legs are gitignored and are transport only.
- **THE CONTROL'S PER-PLANT LAYER WAS RECOVERED AT ZERO LP FOR THE FOURTH CONSECUTIVE LANE.**
  `git fetch origin <40-char-sha>` on the SOCO-57 leg SHAs returned 16 files each, and **all twelve
  committed hourly sidecars verified byte-identical** to the registered keeper.
- **Expected gate noise, machine-verified rather than "fixed":**
  `check_registry_payload_parity` is RED **locally only**, naming six unmapped dirs; all six were
  verified `git check-ignore`-IGNORED with **0 tracked files** — three recovered control legs and
  three arm legs, every one this lane's own. **Nothing was deleted** (rule 31 `[R-RETAIN]`; the
  2026-09-16 correction documents exactly this).
  `audit_keepers` **E11 WARNING** (lineage diff not computable — the former keeper's bundle was
  pruned in this same session per rule 35 (a)) is expected by design, and the lineage evidence is
  captured in `superseded.reason` prose **before** the prune.

---

## 9. THE PROMOTION — EXECUTED IN THIS SESSION ON THE OWNER'S STANDING RULING

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."*

**This lane recommended it on rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]`, and SOCO's keeper is now
`2026-09-22-soco58-warm-committed`.** It is the first of four SOCO promotions that does **not** need
the ruling's second clause — and the lane treated that as a reason for more scrutiny, not less:

- **The cost removed is fictitious, measured rather than argued**: the warm-boiler predicate holds at
  **100.0 % in all eighteen coal plant-years**, at must-run load fraction 1.00.
- **The charge's magnitude is not a physical quantity**: it saturates at exactly $100.00/MWh on zero
  P0 runs and collapses to $0.13 on many — anti-correlated with the year's need for coal.
- **Zero free parameters**, `n_scalars=0`, `n_residual` unchanged at 1, no peer key moves.

**Against it, at full magnitude**: 2023 `ST_GAS` is now the run's thinnest passing row at **0.13 pp**;
2025 coal moves further above an actual it already exceeded, ungated only by the preliminary EIA-923
vintage; 2023 `COAL_BIT`'s D-1 `profile_r` falls to 0.000 on an already-failing row; and **four of
nineteen predictions were partial misses**.

Rule 35 `[R-PROMOTE]` executed **in order**: **(b)** the year union `{2023, 2024, 2025}` enumerated
over all three SOCO sidecars *before* anything was deleted; **(c)** the incoming keeper covers it in
one composed span, so the promotion **shrinks nothing**; **(e)** the designation was written,
`build_status --iso SOCO` rebuilt and `audit_keepers` re-run *before* `prune_iso_runs` touched
anything; **(a)** the outgoing keeper's three stores were then removed together via `--force-uncite`.

**E11 DECLARED, NOT SUPPRESSED.** `meta.composed_from` renames `['soco57_arm_*'] → ['soco58_arm_*']`
— the provenance list of the per-year shard bundles rule 36 `[R-YEAR-ISOLATION]` (a) *requires* be
re-solved per year, so it necessarily renames at every sharded keeper.

**`2026-09-20-soco53g-prb-own-iso` was deliberately NOT pruned** (passed to `--keep`). Rule 31
`[R-RETAIN]` forbids deleting it and rule 30 (a) forbids inventing a stamp, so **`audit_keepers` E13
fires once, by design, for the ELEVENTH CONSECUTIVE LANE, and is RE-RAISED**. The standing
recommendation across SOCO-55/56/57/58 is to **DECLINE it**, which would let the next promoting
session prune it and clear an eleven-lane-old gate failure.

---

## Log entry

```
## soco-58 — 2026-09-22

THE MODEL CHARGED A $100/MW COLD START TO A BOILER ITS OWN DISPATCH NEVER LET
GO OUT. model/commitment.py::compute_monthly_markup adds a P1 bid markup of
startup_cost / max(avg P0 run length, 1.0 h). SOCO's six coal _committed
tranches each carry an NREL $100/MW cold start, and in 2024 FOUR OF THE SIX HAD
ZERO P0 RUNS, so the amortization hit its floor and the markup was EXACTLY
$100.00/MWh -- bands at $140.04 (Bowen) / $141.90 (Daniel) / $157.58 (Scherer) /
$176.96 (Gaston) into a market whose median clearing price that year was
$28.27/MWh, leaving 20.73 TWh of available committed coal capacity producing
0.909 TWh. That is the run-97b inversion the warm-boiler branch's OWN comment
names: "turning the design's cheap base band into a near-peak band."

THE PHYSICS PREDICATE IS 100.0 % IN ALL EIGHTEEN COAL PLANT-YEARS. In every
hour in which a plant's _committed tranche carries capacity, that plant's
_mustrun tranche is generating AT LOAD FRACTION 1.00. The boiler is never dark
when the charge applies, so dispatching the committed band is an output ramp on
a hot unit and the cold start is a cost the plant does not incur.

WHY 2024 IS DIFFERENT IS A P0 FEEDBACK, NOT AN INPUT. Inverting the markup
gives each tranche's implied P0 run length: 1.0 h at four plants in 2024
against 769.2 h at plant 6002 in 2025. At Miller the de-markup mc is $26.94
against a $28.27 median price -- a $1.33 margin the $8.35 markup erases -- while
in 2025 the same plant's markup has collapsed to $0.13. THE CHARGE IS
ANTI-CORRELATED WITH THE YEAR'S NEED FOR COAL: a self-reinforcing lockout that
bites hardest in the lowest-price year, and the mirror of the v2 circularity
_amortized's own docstring records being removed for FAST STARTS. Coal carries
no fast_start_run_hours basis, so coal still runs on v2, in the self-REINFORCING
direction.

THE HANDOFF'S READING (1) IS REFUSED ON MEASUREMENT, ex ante, zero LP spent. The
SOCO-56 contradiction test re-run on the current keeper finds 1.295 / 2.059 /
2.758 TWh forbidden -- LARGEST in 2025, the year coal runs +3.251 TWh OVER -- and
coal availability is FLAT at 57-61 TWh across all three years while generation
swings 30.5 -> 46.2. Availability is not what changed. Reading (2)'s two named
instruments stay refused ON SIGN (SOCO-56 §2(c)); this lane's object is a
fabricated markup, not a fuel cost. Reading (3), the 2025 hydro hole, is
MEASURED (correcting it would push 2025 coal DOWN by up to ~5.7 TWh, absorbing
this arm's overshoot) and ROUTED as the NAMED SUCCESSOR rather than armed
(rule 19).

THE LEVER -- coal_warm_committed, an EXISTING registered default-off boolean
(scenarios.py:12202). ZERO new fields, ZERO new artifacts, ZERO free parameters
(n_scalars=0, n_residual unchanged at 1). SCOPE VERIFIED BY EXECUTION: 6 of 6
coal tranches carrying a startup cost exempted (all _committed, 3,464.0 MW),
0 coal tranches paying the markup but missed, 0 non-coal tranches touched.

RULE 19 AT THE RIGHT GRAIN, AND THE INVERSE OF SOCO-57's TRAP. The mechanism
lives entirely at the P0->P1 seam -- ONE call site, pipeline/solve.py:518 -- so
fuel_prices, mc_base, pmax, availability and heat_rate ALL read EXACTLY
0.000000000000 with zero rows moved, and P0 is BYTE-IDENTICAL. Here that is the
REQUIRED signature, not an inert arm: the resolved scenario_config assertion
(False -> True) is the only thing that can distinguish an armed leg from a
control, which is why soco58_compose_span.assert_delta reads the RESOLVED config
and was verified to refuse a control offered as the arm AND accept one offered as
a control before any leg was composed. A successor must not confuse the two cases.

WHAT MOVED, AND IT IS THE FIRST SOCO PROMOTION IN FOUR LANES THAT DOES NOT NEED
THE RULING'S SECOND CLAUSE. C4 goes FAIL -> PASS: 2024 coal NRMSE 0.309 -> 0.240
and r 0.829 -> 0.847, reversing the exact regression SOCO-57 introduced, with
NRMSE better in FIVE of six C4 rows. grade_summary 5 scored / 3 target / 2 fails
-> 5 / 4 / 1. The single remaining failing C1 row, 2024 CC_REGULAR, improves on
BOTH legs for the first time in three lanes: +11.05 -> +10.42 TWh of a +/-7.47
band and +4.2 -> +4.0 pp of a +/-3.00 pp cap. 2024 COAL_PRB -- the chartered
object -- goes -5.78 -> -2.40 TWh, margin 1.69 -> 5.06; 2024 CT_PEAKER +2.97 ->
+0.88; 2023 COAL_PRB -2.33 -> -0.14. Per-plant coal misallocation
Sum|model-actual| falls 13.316 -> 9.869 TWh in 2024 (-25.9 %) and 7.444 -> 5.929
in 2023 (-20.4 %), James H Miller landing at 0.833 of its own measured output
from 0.651. D-1 failing rows 3 -> 2, with 2024 COAL_PRB's off-peak CV ratio
0.448 -> 0.932 (FAIL -> pass) -- the model's coal was TOO FLAT, which is what a
fleet pinned at its must-run floor looks like.

C4 2024 WAS A LEVEL FAILURE WEARING A SHAPE GATE'S CLOTHES, AND THE PRECOMMIT
SAID SO. NRMSE = RMSE / mean(actual); decomposing each coal year BEFORE the solve
gives shape residuals of 0.188 / 0.186 / 0.160 -- nearly identical -- against
level biases of 0.177 / 0.246 / 0.049. 2024 failed because the model was 9.97 TWh
(-24.6 %) short of the series it is scored against, so adding coal volume was the
direct repair and the decomposition said by how much.

WHAT IT COSTS, AT FULL MAGNITUDE AND NOT IN A FOOTNOTE. (1) 2023 ST_GAS goes
-6.47 -> -6.86 TWh and -2.71 -> -2.92 pp and is NOW THE THINNEST PASSING ROW ON
THE RUN, at 0.32 TWh / 0.13 pp of margin; PRECOMMIT-soco-58 §7 P4 pre-registered
that band and put the chance of it CROSSING at ~40 %. It did not cross. Its cause
is separately known and untouched: SOCO-54 §4's measured $1.0-1.7/MMBtu
delivered-fuel separation between SOCO's gas steam and its CTs (SOCO-12 §4's
unmodelled within-footprint gas dispersion). (2) 2025 coal moves further above an
actual it already exceeded -- COAL_PRB +3.25 -> +4.65, COAL_BIT +0.98 -> +2.47,
SKIPPED C2 2025 coal diagnostic +13.8 % -> +20.9 %. Every 2025 C1 row is SKIPPED
on the preliminary EIA-923 vintage, so no gate registers it; THAT IS A FACT ABOUT
THE VINTAGE, NOT AN ARGUMENT THE COST IS ABSENT. (3) 2023 COAL_BIT's D-1
profile_r falls 0.436 -> 0.000 on a row that was ALREADY failing both legs -- the
class is now exactly its must-run floor in every hour, hence perfectly flat.

THE PREDICTION RECORD IS 15 CONFIRMED / 4 PARTIAL / 0 FALSIFIED, every partial
reported as a miss. P7 (2023 CC_REGULAR +4.4..+5.7, CT_PEAKER +2.0..+4.4) landed
at +5.83 and +4.65, just ABOVE both bands; P10's 2023 allocation leg (4.0..5.6)
landed at 5.929; P11 (2024 COAL_PRB cv_ratio 0.50..0.80) landed at 0.932. ALL
FOUR SHARE ONE ROOT CAUSE AND IT IS THE OPPOSITE OF THE ONE SOCO-57 NAMED.
SOCO-57 §6 measured that its greedy re-stack systematically UNDERSTATED every
movement and told a successor to widen its bands ~2x in the direction of the
correction. This lane did exactly that -- and the bound OVERSTATED 2023
(predicted COAL +2.965, actual +2.189) while UNDERSTATING 2024 (predicted +2.986,
actual +3.313). THE GREEDY BOUND IS NOISY, NOT DIRECTIONALLY BIASED; a successor
should band it SYMMETRICALLY.

RULE 28(a): THE CELL STAYS G AND IS NOT REOPENED, BUT SOCO-53's FACTUAL PREMISE
IS CORRECTED. coal_warm_committed is not a matrix row -- the base matrix registers
it inside the tranche_startup_amortization row's def as a sub-scalar (rule 28(c))
-- and SOCO's cell for that family is G, GOVERNANCE-REFUSED EX ANTE, NO REOPEN
CONDITION. The family's two class-scoped gates have OPPOSITE POLARITY:
gas_st_startup_cost OFF means NO markup (SOCO's ST_GAS committed markup measures
at EXACTLY -0.000, so the family is genuinely off there, as SOCO-53 assumed),
while coal_warm_committed OFF means the markup IS APPLIED (measured at +$100.00).
So "with tranche_startup_amortization off" was NEVER TRUE OF SOCO'S COAL: the
family is ON BY DEFAULT there, no master gate turns it off, and a footprint with
NO CLEARING PRICE was carrying $140-177/MWh start-cost bids -- the very object
that G cell refuses. ARMING THE EXEMPTION ENFORCES THE CELL RATHER THAN REOPENING
IT. The verdict stays G, only its ev is extended, and THE GOVERNANCE BOUNDARY IS
PUT TO THE OWNER rather than settled by the lane. DELIBERATELY NOT EXTENDED TO
CT_PEAKER, whose ten _committed tranches carry the identical +$20.00/MWh
1-hour-run saturation: a combustion turbine with no must-run floor GENUINELY
cold-starts, so no warm-boiler argument exists for it (that CT_PEAKER is also
already +2.97 TWh over in 2024 is recorded as NOT the reason, so the scoping reads
as physics rather than convenience).

RULE 25 / 28(d): MISO's keeper arms this same gate and that transfers NOTHING.
Every number is SOCO's own. A RULE-25 DEFECT IN THE PUBLISHED RECORD WAS FOUND IN
PHASE 0 AND REPAIRED IN THE SAME PR: build_dof_ledger.py hardcoded MISO's dispatch
forensics as this field's identification source for EVERY ISO, so SOCO arming it
would have published MISO's evidence as SOCO's. The source is now per-ISO, SOCO's
cites its own measurement, an unlisted ISO gets an explicit "NOT IDENTIFIED FOR
THIS ISO", and gen_soco58_attestation._verify raises if SOCO's entry is missing or
cites MISO.

PROMOTED. SOCO's keeper is now 2026-09-22-soco58-warm-committed (bundle
results/calibration/soco58_warm_committed, three per-year shards composed at zero
LP under rule 36), on the owner's standing ruling. Rule 35 executed in order: the
year union {2023,2024,2025} enumerated over all three sidecars BEFORE any delete,
the incoming keeper covering it in one composed span so the promotion SHRINKS
NOTHING, audit_keepers run BEFORE prune_iso_runs, and the outgoing
2026-09-20-soco57-measured-cc-heat's three stores then removed via --force-uncite.
E11 DECLARED, not suppressed: meta.composed_from necessarily renames at every
sharded keeper because rule 36 requires per-year re-solves.
2026-09-20-soco53g-prb-own-iso is KEPT (rule 31) and unstamped (rule 30(a)), so
audit_keepers E13 fires once by design and is RE-RAISED FOR THE ELEVENTH
CONSECUTIVE LANE; the standing recommendation across SOCO-55/56/57/58 is to
DECLINE it so the next promoting session may prune it. THE CONTROL'S PER-PLANT
LAYER WAS RECOVERED AT ZERO LP FOR THE FOURTH CONSECUTIVE LANE, all twelve
committed hourly sidecars byte-identical. Records:
docs/handoffs/PRECOMMIT-soco-58-2026-09-21.md,
docs/handoffs/FINDING-soco-58-2026-09-22.md, scripts/gen_soco58_attestation.py,
scripts/probes/soco58_compose_span.py, scripts/probes/_soco58_phase0.py,
scripts/probes/_soco58_checkd.py.
```
