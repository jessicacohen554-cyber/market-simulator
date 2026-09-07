# FINDING — SCN-WS5A-RESOLVE-ERCOT: the three excluded legs re-solved at THE PIN, and the control they earn

**Lane** SCN-WS5A-RESOLVE-ERCOT (sub-lane of SCN-WS5A-RESOLVE, executing ruling **S8** for the three
legs it excluded) · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-resolve-ercot-0jqkt4` · **PRECOMMIT**
`docs/handoffs/PRECOMMIT-scn-ws5a-resolve-ercot-2026-09-07.md` (pushed before the first solve,
merged as `f03dcce4`) · **THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` · **Campaign**
`scn-campaign-load-2026-09-06`, kind `scenario`, `reference_case: REF`, run ids unchanged ·
**Trigger** `FINDING-scn-ws5a-policy-ercot-2026-09-06.md` §0 item 2 and §7 item 1.

Every number below is read from an artifact this lane produced or from a committed pre-fix one.
Three legs solved, 15 solve-years, **19.8 min of LP**, nothing else on the box.

---

## 0. Bottom line

1. **All three legs solved clean at THE PIN.** Every `cache_key` equals its phase-0 value
   (`REF de9c68e19316910e`, `LOAD-HI ec2ea8193e2e45a1`, `LOAD-HI-ORGANIC 0c87f2f2467e95b3`), every
   `git.sha` is the pin, `git.dirty` false, 5/5 years, `error` null, FAIL set exactly `{I3, I12}`
   in every arm — its own pre-fix set, so **no declaration moved** and the audit is EXIT 0
   (136 sidecars / 1,904 records / 129 declared FAILs).
2. **RULING S8's EXCLUSION OF THESE THREE LEGS WAS WRONG, AND THE PRECOMMIT PROVED IT BEFORE ANY
   LP.** S8 excluded ERCOT as "CCS-clean at `1cc45bb2`"; the parent PRECOMMIT §0.1 item 2 wrote
   *"D77 and D65-B are inert on a fleet that converts nothing; their keys move, their answers
   cannot."* The full resolved-`ScenarioConfig` diff pre-fix → pin is exactly **two** substantive
   fields, `ccs_retrofit_vom_adder` **8.0 → 2.95** and `ccs_retrofit_fixed_cost_co2_scaling`
   **False → True**, and both are **inputs to the retrofit screen**. Solved: ERCOT's REF converts
   **0 → 5,763.8 MW** by 2030 and its 2030 CO2 falls **328.874 → 312.866 Mt (−4.87 %)**. An input
   to a screen is never inert because the screen's pre-change output was zero — it is inert only
   if it cannot cross the threshold. **The control solve was earned and it was not a formality.**
3. **G3 — the question this lane exists to answer — SPLITS BY YEAR, and half of it corrects the
   policy FINDING rather than confirming it.**
   - **At 2028 the pin REF converts NOTHING** while every carbon and CES policy arm converts
     2,932–2,996 MW on the same code. So **the 2028 conversion is a POLICY RESPONSE**, and the
     policy FINDING §4's *"the CCS retrofit row is a NULL for the policy reading"* is **too strong
     at 2028**: the policy pulls the first retrofit forward a full year.
   - **At 2029–2030 the pin REF converts on its own** (2,763.8 then +3,000 MW), so those arms'
     rows are largely REF's and the contamination reading **stands** there.
   - The clean A/B is available **at equal load**: `LOAD-HI` (carbon zero) converts
     **0 / 2,932 / 3,000 MW**; the committed `CARB-MID+LOAD-HI` (same demand paths, carbon mid)
     converts **2,996 / 3,000 / 3,000**. And the committed `VOL-HI` — carbon $0, its row unable to
     credit CCS — converts **0 / 2,764 / 3,000**, i.e. **REF's schedule to the tenth of a MW**.
     Only the arms pricing carbon or clean attributes move the schedule.
4. **The load delta survives the repair almost intact — ERCOT is the exception among the six.**
   ΔCO2 (LOAD-HI − REF) at 2030: **+13.4072 → +12.5978 Mt**, a fall of **0.81 Mt (−6.0 %)**;
   NEISO's collapsed 82 % and NYISO's 42 %. The reason is structural: **both ERCOT arms convert on
   the same schedule at nearly the same size**, so the correction very nearly cancels out of the
   difference, whereas NEISO's and NYISO's arm cohorts diverged.
5. **THE DC-SHAPE AXIS IS UNTOUCHED — to four decimal places.** ΔORGANIC − ΔLOAD-HI at 2030:
   **+0.0030 → +0.0029 Mt**; 2029 +0.0203 → +0.0202; 2026–2028 identical. The two high-load arms
   convert identically, so the repair cannot reach the shape gap at all. The load synthesis §1.1
   headline is unaffected on ERCOT.
6. **TWO PRE-REGISTERED PREDICTIONS MISS, AND BOTH MISSES ARE THE INFORMATIVE PART** (§5). P-A
   predicted ~2,900–3,000 MW converted **in 2028**; measured **0 MW in 2028**, 2,763.8 in 2029 —
   and that miss is exactly what splits G3 into item 3's two halves, which a hit would have
   hidden. P-B predicted unserved energy **rising** +2.3 / +2.9 TWh on the capture derate;
   measured **+0.0000 TWh in every year of every arm**.
7. **G5 FAILED AS PRE-REGISTERED, AND THE DEFECT IS THE GATE'S, NOT THE MODEL'S — with a
   consequence for five sibling lanes.** `unit_id` is **not unique** in the ERCOT fleet; the
   scorer resolved it last-occurrence-wins and graded an unconverted twin. A corrected
   measurement (**G5′**, resolving by `(unit_id, fuel_type == "gas_cc_ccs")`) is **PASS on all
   three legs at max relative deviation `0.000e+00`**. G5′ is reported as a *different*
   measurement, never as G5 passing (§2.5). **Routed:** every sibling RESOLVE lane scored its G1
   identity keyed on `unit_id`; here that produced a false FAIL, and on a fleet whose duplicate
   label is the *converted* twin it would produce a false **PASS**.
8. **What is campaign-grade now:** ERCOT's REF / LOAD-HI / LOAD-HI-ORGANIC absolutes and deltas in
   **every** year 2026–2030, on the same pin as the eleven policy legs and the other five ISOs.
   **What is NOT, and is routed:** every 2028–2030 policy-vs-REF delta in the policy FINDING §2,
   which was differenced against the pre-fix REF and must be re-differenced against this one
   (its owed ADDENDUM B — the parent lane's or a follow-up's, not this one's).

---

## 1. Gate verdicts

Pre-registered in PRECOMMIT §4 before the first solve; structural and **kill-only** (rules 1
`[R-STRUCT]`, 29 `[R-SCREEN]`). Scored zero-LP from each leg's own bundle.

| leg | G1 pre-2028 identity | G2 cache-hit proof | G3 conversion | G4 collateral flip | G5 identity (as registered) | G5′ identity (corrected) |
|---|---|---|---|---|---|---|
| REF | **PASS** | **PASS** | CONVERTS | **PASS** | **FAIL** (gate defect) | **PASS** 13 unit-yr |
| LOAD-HI | **PASS** | **PASS** | CONVERTS | **PASS** | **FAIL** (gate defect) | **PASS** 15 unit-yr |
| LOAD-HI-ORGANIC | **PASS** | **PASS** | CONVERTS | **PASS** | **FAIL** (gate defect) | **PASS** 15 unit-yr |

### 1.1 G1 — pre-2028 identity, and a stronger result than the gate asked for

2026 and 2027 are identical to each leg's committed pre-fix bundle on `co2_mt`, `lw_price` and
**every one of the 8 fuel rows**, at relative tolerance 1e-6 — 20 compared quantities per leg,
zero drift. **2028 is identical too**, on every one of the same quantities, because nothing
converts in 2028 on any load leg. That was not required and is reported as the stronger
confinement measurement it is: the D65-B/D77 seam is empirically inert on these legs until the
first retrofit, not merely until `ccs_retrofit_available_year`.

### 1.2 G2 — the cache-hit proof, per leg

| # | evidence | REF | LOAD-HI | ORGANIC |
|---|---|---|---|---|
| a | `results/ERCOT/<PIN key>/` absent pre-solve | **`results/ERCOT/` did not exist at all**; each key re-checked ABSENT at solve time | idem | idem |
| b | `cache_key` == the phase-0 PIN key | `de9c68e19316910e` | `ec2ea8193e2e45a1` | `0c87f2f2467e95b3` |
| c | `git.sha` == THE PIN, `dirty == false` | `bdfb3095`, false | idem | idem |
| d | wall is a solve's, 5 per-year rows | 472.3 s / [169.5, 94.9, 87.3, 65.5, 54.9] | 361.8 s / [148.6, 92.0, 54.3, 35.4, 31.1] | 354.5 s / [150.0, 90.9, 45.7, 34.7, 32.8] |
| e | does NOT reproduce the pre-fix 2028–30 CO2 | 2029/2030 move −7.95 / −16.01 Mt | −8.74 / −16.82 | −8.74 / −16.82 |

The HEAD GUARD (`[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90`) was evaluated before each of the
three legs and **held every time** — this lane pushed its per-leg commits through git plumbing
(`hash-object` / `commit-tree` / `push`) rather than by checking a branch out, so the working tree
never left THE PIN while an LP was running. That is a deliberate improvement on the MISO lane's
disclosed guard trip (`FINDING-scn-ws5a-resolve-miso` §5.1) and it costs nothing.

### 1.3 G3 — the conversion question, reported in both directions

Pre-registered as a **reporting** gate in both directions precisely so this lane's prior could not
pick the answer. Cumulative `gas_cc_ccs` capacity, MW (incremental in brackets):

| leg | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| REF | 0 | 0 | **0** | 2,763.8 [+2,763.8] | 5,763.8 [+3,000.0] |
| LOAD-HI | 0 | 0 | **0** | 2,932.1 [+2,932.1] | 5,932.1 [+3,000.0] |
| LOAD-HI-ORGANIC | 0 | 0 | **0** | 2,932.1 [+2,932.1] | 5,932.1 [+3,000.0] |
| *committed policy legs, for comparison* | | | 2,932–2,996 (carbon/CES) · 0 (`VOL-HI`, `CES-T80`) | 2,764–3,000 | 2,981–3,000 |

Generation: REF 21.575 / 46.463 TWh at 2029 / 2030; both load arms 22.880 / 47.822 TWh.

### 1.4 G4 — no collateral flip

Every leg's post-fix set is exactly its pre-fix set: **FAIL `{I3, I12}`** on all three, WARN
`{I13, I14}` on REF and `{I14}` on the two load arms. **No ident added, none healed**, measured on
both the `full_horizon_summary.json` and the registered sidecar. `invariant-failures.json`
therefore needed **no edit** — nothing to add, no stale ident to delete — and
`check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` is **EXIT 0**, as it was on
`main` before.

### 1.5 G5 — the gate failed, the model did not, and the failure is not argued away

**What was pre-registered:** for every retrofitted unit-year, the LP's persisted
`FleetContext.emission_rate` equals the evolution ledger's `old_emission_rate × (1 − 0.90)` to
relative tolerance 1e-9, with `fuel_type == "gas_cc_ccs"`.

**What happened:** FAIL on all three legs — `2030 gas_cc_h_class_North: expected 0.036 got 0.360,
rel dev 9.0; fuel_type 'gas_cc'`.

**The cause, diagnosed rather than assumed.** The 2030 ERCOT fleet carries **two rows named
`gas_cc_h_class_North`**: the converted one (`gas_cc_ccs`, rate 0.036000, 3,000 MW) and a
different, unconverted one (`gas_cc`, rate 0.360000, 3,000 MW) — new-build gas-CC capacity landing
in the same legacy heat-rate-bin label. `unit_id` is a **bin label, not a key**. The scorer built
`{u: i for i, u in enumerate(fc.unit_ids)}`, so the last occurrence won and it graded the
unconverted twin. **The gate never evaluated its own predicate.**

**G5′, the corrected measurement.** Resolving the cohort row by `(unit_id, fuel_type ==
"gas_cc_ccs")`, requiring exactly one such row, and additionally asserting `pmax == ` the ledger's
`mw`: **PASS on all three legs — 13 / 15 / 15 unit-years, max relative deviation `0.000e+00`**,
every converted unit at `old_emission_rate × 0.10` exactly. REF's 2029 cohort is 6 units
(`CC_REGULAR_North_p55320_econ` 0.380357 → 0.038036, `…_North_p58001_econ` 0.434286 → 0.043429,
`…_South_Central_p7900_econ` 0.439243 → 0.043924, `…_West_p56233_econ` 0.468 → 0.046797,
`…_West_p56349_econ` 0.470272 → 0.047027, `gas_cc_h_class_Houston` 0.36 → 0.036) plus
`gas_cc_h_class_North` (0.36 → 0.036) in 2030.

**What is and is not claimed.** G5 **as written FAILED**; G5′ is a **different measurement** and is
reported as one. Reinterpreting a failed gate after seeing the result — even correctly — is the
fitted-gate move rule 29 exists to forbid, and the PJM leg's own precedent
(`FINDING-scn-ws5a-resolve` §4.1, where a leg was discarded and re-solved rather than argued past)
is the standard this lane holds itself to. The distinction that makes a re-measurement admissible
here rather than a re-interpretation: in the PJM case the **run** carried the defect, so the run
was redone; here the **scorer** carried it, and a scorer that reads the wrong row has not tested
the gate at all. Both verdicts stand in the table above, and no leg's acceptance rests on G5.

**Routed, and it is the more valuable half of this finding.** Every sibling RESOLVE lane
(CAISO, MISO, NEISO, NYISO, PJM) scored its G1 identity with `unit_id`-keyed resolution. On ERCOT
that produced a **false FAIL**, which is the safe direction. On a fleet whose duplicate label
happens to be the **converted** twin it produces a **false PASS** — a gate reporting that the S5
identity holds when it was never checked. Their G1 PASSes should be re-run with fuel-type-qualified
resolution before being relied on. Zero LP; the caches are the only input.

---

## 2. Per-leg results, pre-fix vs THE PIN

"pre" is the committed pre-fix bundle (`REF` at sha `20f9ce9f`, the two load arms at `73c109cb`);
"post" is this lane's re-solve. CO2 in Mt, `gas_cc_ccs` in TWh, `lw` in $/MWh.

### 2.1 Levels

| leg | year | CO2 pre | CO2 post | Δ | `gas_cc_ccs` post | lw pre → post | unserved TWh pre → post |
|---|---|---|---|---|---|---|---|
| REF | 2026 | 214.3926 | 214.3926 | 0.0000 | 0.000 | 91.037 → 91.037 | 0.3816 → 0.3816 |
| REF | 2027 | 255.9732 | 255.9732 | 0.0000 | 0.000 | 982.313 → 982.313 | 4.6218 → 4.6218 |
| REF | 2028 | 285.6966 | 285.6966 | **0.0000** | 0.000 | 3215.987 → 3215.987 | 41.3892 → 41.3892 |
| REF | 2029 | 305.1914 | **297.2393** | **−7.9521** | 21.575 | 3846.002 → 3846.003 | 76.3864 → 76.3864 |
| REF | **2030** | 328.8742 | **312.8655** | **−16.0087** | 46.463 | 4437.529 → 4437.532 | 127.2204 → 127.2204 |
| LOAD-HI | 2028 | 301.5261 | 301.5261 | 0.0000 | 0.000 | 4990.954 → 4990.954 | 227.7885 → 227.7885 |
| LOAD-HI | 2029 | 321.8841 | **313.1458** | **−8.7383** | 22.880 | 4998.435 → 4998.435 | 360.9840 → 360.9840 |
| LOAD-HI | **2030** | 342.2814 | **325.4633** | **−16.8181** | 47.822 | 4999.549 → 4999.549 | 538.8695 → 538.8695 |
| ORGANIC | 2029 | 321.9044 | **313.1660** | **−8.7384** | 22.880 | 4999.756 → 4999.756 | 360.9301 → 360.9301 |
| ORGANIC | **2030** | 342.2844 | **325.4662** | **−16.8182** | 47.822 | 4999.994 → 4999.994 | 538.8587 → 538.8587 |

**Share of the 2030 level corrected: REF −4.87 %, LOAD-HI −4.91 %, ORGANIC −4.91 %** — between
PJM's −1.58 % and CAISO's/NYISO's. ERCOT is the only re-solved ISO whose correction cannot be an
accounting one: **`gas_cc_ccs` was absent from every pre-fix fuel dict in every year**, so there
was no mis-rated stock. All of it is a changed retrofit *decision*.

### 2.2 The mechanism is a 1:1 swap, not a merit-order displacement — and that separates ERCOT from PJM

By-fuel movement, pre → post, TWh (every row moving more than 1 GWh):

| leg | year | movement |
|---|---|---|
| REF | 2029 | `gas_cc` **−21.576**, `gas_cc_ccs` **+21.575**, solar −0.013, wind +0.013, gas_ct +0.002 |
| REF | 2030 | `gas_cc` **−46.485**, `gas_cc_ccs` **+46.463**, gas_ct +0.022, wind +0.009, solar −0.009 |
| LOAD-HI | 2029 | `gas_cc` **−22.880**, `gas_cc_ccs` **+22.880** |
| LOAD-HI | 2030 | `gas_cc` **−47.822**, `gas_cc_ccs` **+47.822**, wind +0.026, solar −0.026 |

**Nothing else moves.** Coal, nuclear, hydro and storage are unchanged to the GWh; wind and solar
move by ≤0.03 TWh on an 80 GW VRE fleet. So ERCOT's fall is **the re-rating of the converted block
and essentially nothing else**: 16.0087 Mt over 46.463 TWh is an avoided intensity of
**0.3446 t/MWh**, which at a 90 % capture rate implies a host rate of **0.383 t/MWh** — squarely
inside the cohort's measured 0.36–0.47 range. **This is the opposite of PJM**, where the same
repair's *dispatch* channel dominated (abated gas displacing unabated gas and coal, 3.50 → 14.80
TWh). On ERCOT the LP simply converts a block and keeps running it; on an ISO shedding 127–539 TWh
at $3,200–5,000/MWh, every thermal unit is already inframarginal and there is nothing to displace.

### 2.3 The deltas the campaign actually quotes

| quantity | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|
| ΔCO2 (LOAD-HI − REF) **pre** | +41.6256 | +42.8002 | +15.8295 | +16.6927 | **+13.4072** |
| ΔCO2 (LOAD-HI − REF) **post** | +41.6256 | +42.8002 | +15.8295 | **+15.9065** | **+12.5978** |
| DC-shape gap (ORGANIC − LOAD-HI) **pre** | −0.7588 | −3.9416 | +0.0495 | +0.0203 | +0.0030 |
| DC-shape gap (ORGANIC − LOAD-HI) **post** | −0.7588 | −3.9416 | +0.0495 | **+0.0202** | **+0.0029** |

The load delta falls **6.0 %** at 2030 and the shape gap moves by **0.0001 Mt**. Both are reported;
neither was predicted directionally (P-F, deliberately).

### 2.4 Clean share rises, and it is the crediting convention

REF `clean_share` 2029 **0.3246 → 0.3504**, 2030 **0.3172 → 0.3684**; both load arms 0.3102 →
0.3367 and 0.3071 → 0.3584. `gas_cc_ccs` counts as clean under `clean_capture` crediting, so
converting 5.8–5.9 GW moves the share **+2.6 to +5.1 points** with **no change** in wind, solar,
nuclear or hydro output and curtailment flat at 4.9079 TWh. Any campaign statement about ERCOT's
2029–2030 clean share must name the convention it is on. Stated, not adjusted.

---

## 3. Cost

| leg | total wall | peak RSS | 2026 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|---|---|---|
| REF | 7.9 min | 4.00 GB | 169.5 s | 94.9 | 87.3 | 65.5 | 54.9 |
| LOAD-HI | 6.0 min | 3.71 GB | 148.6 | 92.0 | 54.3 | 35.4 | 31.1 |
| LOAD-HI-ORGANIC | 5.9 min | 3.48 GB | 150.0 | 90.9 | 45.7 | 34.7 | 32.8 |

**19.8 min of LP for 15 solve-years = 1.32 min per solve-year**, all rc=0, 5/5 years each, legs
strictly serial. That reproduces the desk ledger's own measured ERCOT rate (1.30 min/solve-year,
r#18 am.1) to within 2 %, so the S16 shard-sizing arithmetic is confirmed on a fresh container.
Peak RSS **4.00 GB on a 15 GB box** — comfortable, unlike MISO's 9.98 GB.

**Precondition cost, for the next lane's planning:** `data/clean` is derived and gitignored, so
`regenerate_clean.py` had to build **56 datatypes / 1.5 GB** first, which took **~39 minutes** —
**twice the LP**. A shard budgeting only for solve time will misjudge its wall by a factor of two.

---

## 4. Routed to SCN-DESK — not executed, outside this lane's regions

1. **The eleven committed ERCOT policy legs must be re-differenced against THIS REF** — the policy
   FINDING's owed **ADDENDUM B**. **LANDED 2026-09-07:** `docs/handoffs/ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md`. Its §2 tables at 2028–2030 are differenced against a REF that
   converts nothing; every one of them changes. §0 item 3 above already says which way the
   headline reading moves (2028 is policy, 2029–30 is the pin), but the numbers are the parent
   lane's or a follow-up's to restate. **Until it lands, no ERCOT policy-vs-REF delta at 2028–2030
   should be quoted from either document.**
2. **The `unit_id`-keyed G1 in five sibling lanes** (§1.5). Zero-LP re-check; false-PASS risk.
   **ANSWERED 2026-09-07 — `docs/handoffs/FINDING-scn-resolve-g1-recheck-2026-09-07.md`.** The five caches are
   absent from any container, but the re-check did not need them: `aggregate_fleet` returns
   `passthrough + representatives` and nothing downstream reorders, so the converted twin is **always** at the lower
   index — **the defect is one-directional and can produce a false FAIL only**. A masked cohort member fails BOTH legs
   of the sibling predicate (rate *and* `fuel_type`), and all five reported zero failures, so **their G1 PASSes stand**
   and the false-PASS risk routed here does not exist through this mechanism. Item 3 below is what remains open.
3. **`unit_id` is not unique in the ERCOT fleet**, and this reaches further than one gate: any
   per-unit attribution, ledger join or diagnostic keyed on `unit_id` is exposed. The duplicate
   here is a legacy heat-rate-bin label (`gas_cc_h_class_North`) colliding with new-build capacity
   in the same bin. Whether the fleet builder should be emitting unique ids, or every consumer
   should be qualifying by fuel type, is a code question this lane does not own.
   **OPENED as desk card D-14** (`scenario-desk-ledger-2026-09.md` §2), with the exposure enumerated: ~20 committed
   sites key on `unit_id`, three of them on the decision path (`retirements.py:3318`/`:3403`, `:3833`, `evolve.py:686`)
   plus the `ccs_retrofits` ledger this gate reads. Recommendation: a uniqueness guard, then rename-on-retrofit;
   *not* "every consumer qualifies by fuel type". Proposed, not implemented.
4. **P-B's failure re-opens the policy FINDING §2.1 attribution.** That document reads the carbon
   arms' +2.28 / +2.89 TWh of extra 2029–30 unserved as "the capture parasitic derate on 5.9 /
   8.9 GW of converted CC". Measured here, the derate moves unserved by **exactly zero** — it
   raises the converted unit's heat rate, not its pmax. So that +2.28 / +2.89 was the gap between
   an arm converting ~8.9 GW and a REF converting none, and against this control it should largely
   close. **MEASURED 2026-09-07 (ADDENDUM B §4): it does NOT close — Δunserved is unchanged in every cell, because
   REF's unserved never moved. The derate is confirmed at exactly zero; the real driver is the 500 MW gas-CT the
   carbon and CES arms do not build in 2029** (Δthermal −500 / −1,500 / −3,500 MW → +2.28 / +6.97 / +16.82 TWh, with
   `VOL-HI` at Δthermal 0 and Δunserved 0.0000 as the control). Belongs with item 1.
5. **The synthesis's A.1 table row for ERCOT** ("0 (clean) / 0 (clean) / unchanged at `1cc45bb2`")
   is now false. Corrected in this commit as a marked correction beside the addendum, per §5 of
   this document; the parent lane owns any further restatement.

---

## 5. Predictions, scored as written — misses at full magnitude

**P-A (the pin REF converts at the cap in 2028) — MISS.** Predicted ~2,900–3,000 MW in **2028**.
Measured **0 MW in 2028**, 2,763.8 MW in 2029. Wrong by a full year. **The miss is the informative
result**: it is what makes the 2028 policy comparison possible at all, because it gives the policy
arms a control that converts nothing in the year they convert most. A hit would have hidden it.

**P-B (unserved rises ~+2.3 / +2.9 TWh on the capture derate) — MISS, at zero.** Measured
**+0.0000 TWh in every year of every arm** (identical to the pre-fix bundle to the 0.1 GWh the
report prints). The derate raises heat rate, not capacity; on an energy-only ISO already shedding
127–539 TWh nothing about deliverable energy changes. Routed as §4 item 4, because the policy
FINDING attributes a real number to this mechanism.

**P-C (2030 REF CO2 falls 5–20 Mt / 1.5–6 %) — HIT.** −16.0087 Mt, −4.87 %. The reasoning was
right for the right reason: ERCOT prices carbon at $0, so there is no carbon channel, and §2.2
measures the fall as almost pure re-rating.

**P-D (2026–2027 do not move at all) — HIT**, and better than stated: **2028 does not move
either** (§1.1).

**P-E (no new FAIL class) — HIT.** FAIL `{I3, I12}` unchanged on all three; `I7` (the named risk)
stayed PASS.

**P-F (no directional call on the LOAD-HI delta or the shape gap) — held.** Delta +13.4072 →
+12.5978 Mt; shape gap +0.0030 → +0.0029 Mt. Reported, not scored. The reasoning offered for why
it *might* cancel (both arms converting at the same annual cap) is what happened, but that was
offered as one of two possibilities and is not claimed as a prediction.

**Gate-design self-score.** G5 was the one gate this lane **added** beyond its charter, and it is
the one that failed — on its own implementation. The lesson is narrow and worth recording: a gate
that joins two artifacts on an identifier must first establish that the identifier is a key.

---

## 6. Files

**Added / changed by this lane, all inside its declared regions:**

- `docs/handoffs/PRECOMMIT-scn-ws5a-resolve-ercot-2026-09-07.md` (new, pushed pre-solve, `f03dcce4`)
- `docs/handoffs/FINDING-scn-ws5a-resolve-ercot-2026-09-07.md` (this file)
- `results/scn-campaign-load-2026-09-06-r2/ERCOT/{REF,LOAD-HI,LOAD-HI-ORGANIC}/` — the three legs'
  slim artifacts (`full_horizon_summary.json` + `run_config.json`)
- `results/scn-campaign-load-2026-09-06/ERCOT/{bundle,report}/` — rebuilt in place on the three
  PIN-key legs; the pre-fix pair named dead cache keys
- `frontend/data/hindcast/ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}.json`
  — re-registered under the **SAME** ids; only `cache_key`, `bundle`, `total_wall_s`, the
  trajectory, `registered_utc` and `provenance` move
- `results/scn-campaign-load-2026-09-06/ERCOT/{REF,LOAD-HI,LOAD-HI-ORGANIC}/` — **DELETED**
  (rule 26 `[R-DELETE]`): slim artifacts at cache keys that no longer exist. Git history is the record.
- `docs/handoffs/scenario-desk-ledger-2026-09.md` §1 (the RESOLVE row) and
  `docs/handoffs/FINDING-scn-ws5a-load-synthesis-2026-09-06.md` (the pin statement + A.1's ERCOT
  row) — the two updates this lane was chartered to make, and no other lane's region.

**`frontend/data/hindcast/invariant-failures.json` needed NO edit** — every leg's post-fix set is
exactly its existing declaration. The checker is **EXIT 0** after every commit, as on `main` before.

**Duties discharged.** No default moved, no knob moved, no `ScenarioConfig` field added, no new
case, no solve outside the three, no year past 2030, **no policy leg re-solved**. **DOF ledger:
ZERO free parameters**; no `authorized_price_tuning`. Everything under `src/`, `scripts/`,
`configs/`, `data/` consumed, never edited. Rule 27 `[R-PUSH]`: no source file ≥300 lines
rewritten; every push fetch-back verified. Rule 29(c) not engaged — these are registered campaign
arms, not screen or control bundles. Rule 28 `[R-MECH-MATRIX]`: no mechanism proposed or tested —
this lane re-solved existing cases at a new pin and added no `ScenarioConfig` field, so no matrix
cell changes hands. Backcast byte-identity untouched (forecast-mode only). No CI workflow created;
every solve ran in-session. No PR opened.
