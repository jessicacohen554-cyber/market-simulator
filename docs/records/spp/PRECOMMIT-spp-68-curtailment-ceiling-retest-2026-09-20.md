# PRECOMMIT — SPP-68: card R-bc, the wind curtailment CEILING re-tested like-for-like against KEEPER 14

**Written and pushed BEFORE any LP is solved** (rules 1 `[R-STRUCT]`, 32 `[R-SHARD]` (a)).
Base pinned at session start: `14a11a9a7f5c1ef99e76d1f7b51b74ca76c2c113`.
Lane branch `claude/spp-curtailment-ceiling-retest-n1otup`. DATA PROFILE: `spp`.

Incumbent keeper 14 `2026-09-20-spp-67-yearown-rate` (`spp67_yearown_span`, 2023–2025,
CALIBRATED, one ledgered C3c) + rung `2026-09-20-spp-67-rung-yearown`
(`spp67_yearown_rung`, 2019–2022, NOT-YET, failing {C1, C3a, C3b, C4}), stamped to it.

Probe behind every number here: `scripts/probes/_spp68_ceiling_phase0.py` (ZERO LP).

---

## 0. THE LANE BRIEF'S FRAMING IS CORRECTED BEFORE ANYTHING IS SPENT

The brief says the ceiling's *"control was KEEPER 5 … it has never had a fair control."*
**That understates the record and the correction is made here rather than discovered later.**
`spp_curtailment_ceiling` has had a **solved, pre-registered, five-gate screen**: lane
**SPP-63**, 2026-09-10, one year (2025), shard pinned `92b59c73`, recorded in
`docs/handoffs/RESULT-spp-63-screen-2026-09-10.md` and in SPP's matrix cell. Its control was
the then-keeper `2026-09-10-spp-62-vintage-census` (keeper 7-era), not keeper 5.

**What SPP-63 measured, and it is the reason this lane pre-registers a kill condition rather
than a hypothesis:**

| SPP-63 gate | outcome |
|---|---|
| G-1 config identity | PASS |
| G-3 allocation identity (2.6049× flat) | PASS |
| wind 122.0430 → 110.2248 TWh, within **0.232 TWh** of actual | the arm does what its arithmetic says |
| **G-4 no-new-forcing** | **FAIL** — slack 0.0000 → **211.208 MWh** (pre-registered ≤ 100.0) |
| **G-5 no-load-bearing-regression** | **FAIL** — C3b NRMSE **0.167 → 0.253** (≤0.20 band), a load-bearing PASS → FAIL; negative-price hours **167 → 0** |
| where the energy went | COAL_PRB **+7.099**, CC_REGULAR **+3.680**, ST_GAS **−0.693** — the coal family **+0.72 → +8.69 TWh** long |

So the cell reads **O, not R** — correctly, because the mechanism is a rule-14 `[R-ACCURATE]`-owed
repair and three of five gates passed — and rule 28(a)'s DO-NOT-REDO does not bar a re-test.
**But the re-test is warranted on a specific, nameable change, not on "the control was stale":**
two keepers have landed since, and both touch exactly what killed SPP-63.

* **Keeper 13 (SPP-51)** armed SPP's first thermal min-load floor. It **eliminated the zero-coal
  collapse** (41–290 h/yr → 0 in every year) and roughly **doubled** negative-price hours
  (+129 to +268). SPP-63's G-5 failure ran through the negative-price regime; that regime is now
  structurally different.
* **Keeper 14 (SPP-67)** armed `vre_reference_rate_year_own`, so **five of seven years now gross
  up at their OWN published rate** instead of the 9.65 % three-year mean. The ceiling's depth was
  identified against the *old* basis. **That interaction is this lane's central finding and it is
  measurable at zero LP — see §3.**

---

## 1. RULE 19 `[R-ONE-MECH]`, VERIFIED IN CODE BEFORE THE SOLVE

`src/market_sim/data/renewables.py` L3106-3117: the oversupply water-fill
(`_oversupply_uncurtailed_cf`) is skipped whenever `spp_curtailment_ceiling` is armed, so the
basis reverts to the flat gross-up and the two can never both be live. Checked mechanically in
probe leg E; **PASS**. Keeper 14 arms `vre_curtailment_oversupply_allocation = True`, so the arm
*does* disarm it — and SPP-58 measured that swap **energy-neutral on the basis to the
milli-TWh** (the water-fill only ever moved hours). Re-stated here as the identity the arm must
reproduce: **annual potential unchanged; every TWh the arm removes is the ceiling's.**

Three further gates checked in source, all **PASS**: backcast leg gates on `iso == "SPP"`,
forecast leg gates on `iso == "SPP"`, the share table and the ceiling zones are SPP's own.

---

## 2. PHASE 0 ITEM 1 — HOW MUCH OF THE HEADROOM DOES THE LP SPEND? (keeper 14, not keeper 12)

Numerator and denominator stated separately throughout.
`headroom = potential − delivered` · `spent = model − delivered` · `re-curtailed = potential − model`.

| year | gross src | rate | delivered | potential | headroom | model | re-curt | **spent/headroom** | re-curt/potential |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2019 | own | 1.591 % | 77.0324 | 78.2777 | 1.2453 | 78.2784 | −0.0007 | **100.05 %** | −0.00 % |
| 2020 | reference | 9.650 % | 82.0416 | 90.8044 | 8.7627 | 90.6257 | +0.1787 | **97.96 %** | 0.20 % |
| 2021 | reference | 9.650 % | 92.8547 | 102.7723 | 9.9177 | 101.8115 | +0.9608 | **90.31 %** | 0.93 % |
| 2022 | own | 9.357 % | 107.4414 | 118.5322 | 11.0909 | 117.4226 | +1.1096 | **90.00 %** | 0.94 % |
| 2023 | own | 8.493 % | 103.0494 | 112.6142 | 9.5648 | 111.9715 | +0.6428 | **93.28 %** | 0.57 % |
| 2024 | own | 10.561 % | 109.3074 | 122.2147 | 12.9073 | 121.4475 | +0.7673 | **94.06 %** | 0.63 % |
| 2025 | own | 9.896 % | 110.4538 | 122.5845 | 12.1307 | 121.9946 | +0.5899 | **95.14 %** | 0.48 % |

**The LP spends 90.00–100.05 % of the headroom the gross-up hands it.** That is card R-bc stated
as a ratio on the CURRENT keeper: nothing in the LP can refuse wind bid at −$26/MWh below every
thermal offer, so a bound the model invents is a bound it takes. (SPP-50 read the same object as
0.00–0.48 % *re-curtailment* at keeper 12; the complement is the same measurement.)

---

## 3. PHASE 0 ITEM 2 — THE DEPTH, RECONCILED. IT STAYS FROZEN, AND THE RECONCILIATION IS THE FINDING

SPP-58's identification, verbatim from its §3: depth is the value centring the removal on SPP's
published curtailment MW.

```
removal_y = depth × Σ_t potential_y(t)·share(t) = depth × potential_y × wms_y
want      = published_share_y × potential_y
⇒  depth_y = published_share_y / wms_y          ← potential CANCELS
```

So a **scalar** change in the gross-up rate cannot move the depth — answerable in closed form.
What can move it is the published MW changing (it has not) or `wms_y` moving. Measured on keeper
14's own potential:

| year | gross src | published share | `wms_y` | implied depth | SPP-58's | Δ | **0.288137 / implied** |
|---|---|---:|---:|---:|---:|---:|---:|
| 2019 | own | 1.591 % | 0.33941 | **0.04687** | — | — | **6.1476** |
| 2020 | reference | — | 0.34637 | — | — | — | — |
| 2021 | reference | — | 0.34147 | — | — | — | — |
| 2022 | own | 9.357 % | 0.33424 | 0.27995 | — | — | 1.0293 |
| 2023 | own | 8.493 % | 0.33180 | 0.25598 | 0.25646 | −0.00048 | 1.1256 |
| 2024 | own | 10.561 % | 0.33746 | 0.31296 | 0.31391 | −0.00095 | 0.9207 |
| 2025 | own | 9.896 % | 0.34097 | 0.29022 | 0.29168 | −0.00146 | 0.9928 |

**RULE 23 `[R-FROZEN-DERIVE]`: the depth STAYS FROZEN at the registered 0.288137.** Its source
data has not changed — the five ASOM curtailment-MW rows and five GenMix delivered-MW rows in
`data/raw/spp-hsl/spp_wind_curtailment_annual.csv` are byte-identical to what SPP-58 read — and
this lane re-derives nothing. The reconciliation reproduces SPP-58's own per-year depths to
**≤ 0.0015**, which validates the construction on keeper 14's basis.

**THE FINDING, AND IT IS STRUCTURAL RATHER THAN RESIDUAL.** The ceiling's depth is identified
against a **pooled** published share (≈ 9.65 %); keeper 14's gross-up is now sized by each year's
**own** published rate. They are two answers to *"how much wind is there"* (rule 19
`[R-ONE-MECH]`), and a pooled depth is only consistent with a year-own gross-up in a year whose
own rate happens to equal the pool. **2019's own rate is 1.591 %, so the pooled depth is 6.15×
too large there.**

The consistent alternatives are both refused, in advance:
* a **per-year depth** — refused by rule 1 `[R-STRUCT]` condition (b): one config across every
  scored year;
* **re-cutting the pooled depth** so a year or a gate comes right — refused by rule 1 condition
  (c) and by SPP-64's finding that no depth fixes the price channel.

Neither is attempted in this lane. The registered value is solved as registered.

## 3b. RECONSTRUCTION SENSITIVITY — stated because the hourly reconstruction is NOT exact

`potential(t) = delivered_930(t) × factor_y` is exact on **annual** energy (probe leg A: max
|diff| vs the scored bench 0.0126 TWh, the payload's own 2-dp rounding; SPP-67's CAPACITY and
SHAPE legs are 0.0000 TWh) but **not hour-exact** — measured hourly `model/potential` runs
p1–p99 0.64–1.30 at r ≈ 0.96, because the model carries a per-zone shape and a monthly
commissioning ramp no annual scalar reproduces. Items 2 and 3 are therefore **bracketed**: net
load is rebuilt a second time from the model's own committed wind dispatch (the true bound lies
between the two, since the LP spends 90–100 % of it). The bracket is **≤ 0.92 pt wide in every
year except 2019 (4.08 pt)** — far inside every quantity this lane decides on.

---

## 4. PHASE 0 ITEM 3 — PREDICTIONS, PRE-REGISTERED. EVERY NUMBER BELOW IS WRITTEN BEFORE THE SOLVE

`new bound(t) = potential(t) × clip(1 − 0.288137 × share(t), 0, 1)`. The LP spends ~all of its
bound (§2), so the bound is the prediction; it is bracketed anyway — **[LO]** the LP keeps
re-curtailing the same *fraction* of the new headroom, **[HI]** it takes the whole new bound.

### P-1 — wind (point predictions; the bracket is ≤ 0.06 TWh wide, so one number is honest)

| year | bench | keeper 14 wind | excess now | **predicted arm wind** | **predicted excess** | **Δ wind** | removal / headroom |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 77.0300 | 78.2784 | +1.2484 | **70.6223** | **−6.4077** | **−7.6560** | **614.8 %** |
| 2020 | 82.0300 | 90.6257 | +8.5957 | **81.7418** | **−0.2882** | **−8.8839** | 103.4 % |
| 2021 | 92.8600 | 101.8115 | +8.9515 | **92.6605** | **−0.1995** | **−9.1510** | 102.0 % |
| 2022 | 107.4400 | 117.4226 | +9.9826 | **107.1168** | **−0.3232** | **−10.3058** | 102.9 % |
| 2023 | 103.0500 | 111.9715 | +8.9215 | **101.8479** | **−1.2021** | **−10.1236** | 112.6 % |
| 2024 | 109.3200 | 121.4475 | +12.1275 | **110.3313** | **+0.9505 … +1.0113** | **−11.1466** | 92.1 % |
| 2025 | 110.4600 | 121.9946 | +11.5346 | **110.5410** | **+0.0767 … +0.0810** | **−11.4557** | 99.3 % |

**The last column is the point of the table.** At 100 % the ceiling and the gross-up exactly
cancel and wind returns to its delivered basis. **Above 100 % the ceiling removes energy SPP
actually delivered** — 2.9 % of it in 2022, 12.6 % in 2023, and **514.8 % of the headroom, i.e.
≈ 5.1 TWh of delivered energy, in 2019.** Tolerance on P-1: **± 0.25 TWh** per year, widened to
± 0.50 TWh in 2019 (the 4.08 pt bracket).

### P-2 — thermal absorption (the energy has to go somewhere; this is the weakest prediction and is labelled so)

Priors are SPP-63's measured 2025 split on an 11.818 TWh removal (COAL_PRB +7.099 = 60.1 %,
CC_REGULAR +3.680 = 31.1 %, ST_GAS −0.693 = −5.9 %, remainder 14.7 %). **Keeper 13's coal floor
has since raised coal's baseline, so the marginal absorption may tilt toward gas; the bands are
wide on purpose and a miss here is scored as a miss, not explained away.** As a fraction of that
year's |Δ wind|, in every year:

| class | predicted band |
|---|---|
| COAL_PRB | **+0.45 … +0.70** |
| CC_REGULAR | **+0.18 … +0.42** |
| CT_PEAKER | **+0.00 … +0.20** |
| ST_GAS | **−0.12 … +0.12** |
| Σ thermal | **+0.90 … +1.05** (energy balance; storage/imports/dump absorb the rest) |

Directional call, stated separately because it is the one that decides C1: **the coal family goes
LONG in every year.** SPP-63 took it from +0.72 to +8.69 TWh against actual.

### P-3 — C3a mean LMP: rises in EVERY year (removed wind is replaced at positive SRMC)

SPP-63 measured +2.2 % → +9.9 % on 2025, i.e. **+7.7 pts** of relative error. Predicted band
**+4 to +11 pts** in every year:

| year | keeper 14 C3a | predicted arm C3a | band ±10 % |
|---|---:|---:|---|
| 2019 | +7.7 % | **+12 to +19 %** | **FAIL predicted** |
| 2020 | +19.3 % (FAIL) | **+23 to +30 %** | FAIL, worse |
| 2021 | +2.7 % | **+7 to +14 %** | at risk |
| 2022 | −4.0 % | **+0 to +7 %** | **IMPROVES** |
| 2023 | +0.1 % | **+4 to +11 %** | at risk |
| 2024 | −1.6 % | **+2 to +9 %** | holds |
| 2025 | +1.3 % | **+5 to +12 %** | at risk |

### P-4 — C3b price shape: worsens in EVERY year by **+0.04 to +0.09** NRMSE

SPP-63 measured 0.167 → 0.253 (+0.086) on 2025. Predicted: 2023 0.168 → **0.21–0.26**, 2024
0.156 → **0.20–0.25**, 2025 0.157 → **0.20–0.25** — i.e. **all three keeper years at or past the
0.20 band.** **THE STRONGEST AVAILABLE COUNTER-EVIDENCE, STATED RATHER THAN OMITTED:** 2019 is
the year with the *smallest* headroom (1.245 TWh) and the *best* C3b (0.128) of all seven. If
headroom were monotonically bad for C3b, the ceiling would help. It is **not** monotone
(2020 has the second-smallest headroom and the worst C3b, 0.273; 2024/2025 have the largest
headroom and the 2nd/3rd best C3b), and 2019/2020 are rung years differing in `gas_price_override`
and `mid_vintage_exit_carry`, so the cross-year comparison is confounded where SPP-63's within-year
arm-vs-control is not. P-4 rests on the direct measurement. If P-4 is wrong, it is wrong.

### P-5 — the negative-price regime collapses to ≈ 0 in every year

Measured on keeper 14's own committed prices, no reconstruction. The model's wind offer is a flat
`−ira_ptc_wind`, so `price == −26.000` is the exact signature that wind is marginal.

| year | model h < 0 | model h ≤ −25.9 | **ACTUAL RT h < 0** | model/actual | headroom TWh | min price |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | **0** | **0** | 547 | 0.00× | **1.2453** | **+4.500** |
| 2020 | 170 | 169 | 936 | 0.18× | 8.7627 | −26.000 |
| 2021 | 511 | 494 | 1108 | 0.46× | 9.9177 | −26.000 |
| 2022 | 498 | 483 | 995 | 0.50× | 11.0909 | −26.000 |
| 2023 | 393 | 334 | 992 | 0.40× | 9.5648 | −26.000 |
| 2024 | 464 | 346 | 1172 | 0.40× | 12.9073 | −26.000 |
| 2025 | 414 | 293 | 1018 | 0.41× | 12.1307 | −26.000 |

**2019 is the natural experiment this lane did not have to build.** Its gross-up headroom is
1.25 TWh against 8.8–12.9 elsewhere, and it has **zero** negative hours and a **positive** minimum
price. The model's negative-price regime *is* the gross-up headroom being spilled. A ceiling that
removes the headroom removes the regime — at any depth, which is why SPP-64 concluded no value of
`spp_curtail_depth_wind` changes it and why re-cutting the depth is both forbidden and pointless.
And the model is **already at 0.18–0.50× the market's** negative-hour count, so removing them
moves **away** from the market, not toward it. Predicted: **model h ≤ −25.9 falls below 50 (i.e.
> 85 % reduction) in every year.**

---

## 5. THE KILL CONDITION, PRE-REGISTERED. NO LIMB MAY BE RE-CUT AFTER SEEING A RESULT

Evaluated on the composed span (2023–2025) and rung (2019–2022) against keeper 14's **committed
bundle** as the control (rule 29(b) form 4 — validated in §6). **ANY limb tripping ⇒ the lane
reports the cell `R`, recommends AGAINST promotion, and says so plainly.**

* **K-1 — over-removal.** Any year's arm wind lands more than **2.00 TWh BELOW** the EIA-930
  bench. *(Below-bench wind is energy the market demonstrably delivered; 2.00 TWh is ≈ 2 % of
  SPP's annual wind and ~2× the largest measured re-curtailment. **Predicted to trip on 2019 at
  −6.41.**)*
* **K-2 — load-bearing regression.** Any load-bearing criterion (C1 / C2 / C3a / C3b) flips
  PASS → FAIL in any KEEPER-span year (2023–2025). *(This is SPP-63's G-5 restated. Predicted to
  trip on C3b.)*
* **K-3 — the price floor.** Model hours at `price ≤ −25.9` fall below **50 %** of keeper 14's
  value in any year where keeper 14 carries ≥ 100. *(Predicted to trip in all six such years.)*
* **K-4 — new forcing.** Total slack exceeds **100 MWh** in any year where keeper 14 carries
  0.000. *(SPP-63's G-4, same threshold, unchanged. It read 211.208.)*

**PROMOTION CONDITION, stated so the test is not rigged one way.** If **none** of K-1…K-4 trips,
**and** the span determination stays CALIBRATED, **and** the D-10 free-class C1 score does not
fall below keeper 14's 16/16 · 12/12, the lane **recommends promotion** on the strength of the
wind row — 6 of 7 years landing within 1.21 TWh of actual against +8.60…+12.13 now.

**WHY THE SPAN IS SOLVED AT ALL, given §3 predicts K-1 trips.** Rule 34 `[R-SHARD-PROMOTABLE]`
(b): *"a screen is not an exception, because you cannot know it is one until the owner rules."*
Rule 31 `[R-RETAIN]`: the owner routinely promotes what a session declined. **Six of seven years
move from +8.6…+12.1 TWh of phantom wind to within ±1.21 TWh of actual** — that is a large, real
C1 improvement the owner is entitled to rule on with solved numbers, not with my arithmetic. The
predicted costs (2019, the price channel, the coal family) are stated above at full magnitude so
the ruling is made on both sides at once.

---

## 6. G-DRIFT — rule 29(b) form 4 IS VALID; keeper 14's committed bundle IS the control, zero LP

`git diff 40eeb43adf013114fccc23a90518a3683d5bf377 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`

**Exactly ONE file changed on the whole audited solve path:**

| file | hunks | classification |
|---|---:|---|
| `data/raw/_validation-source/nyiso_offer_level_dispersion.json` | +2344 / −0 | **INERT** — a per-ISO artifact SPP does not have (NYISO offer dispersion); no SPP code path reads it |

**All hunks INERT ⇒ form 4 valid, and no control solve is spent.** (For completeness: the other
172 changed files across the whole repo are docs, `frontend/`, `.gitignore`, and
`data/raw/campd-unit-outages-perunit-SOCO.*` — another ISO's artifact.)

---

## 7. RULE 25 `[R-ISO-SCOPE]` — DEFAULT-OFF BYTE-IDENTITY, PROVEN BEFORE THE SOLVE, TWO WAYS

**By construction** (checked mechanically in source, all PASS): the backcast leg
(`scripts/run_calibration.py` L3363) and the forecast leg (`runner.py` L3305) each gate on
`iso == "SPP"`; the share table is `spp_curtailment_share.csv`; the ceiling zones are
`("SPP-North", "SPP-South")`; and the rule-19 skip is the one in §1.

**By census:** all **46** committed `run_config*.json` under `results/calibration/` scanned; **38**
carry the field; **0** arm it, in any ISO. Arming it for SPP moves no other ISO's bytes and no
other ISO's keeper.

---

## 8. THE DOF LEDGER AND THE ATTESTATION

Zero new free parameters are introduced. `spp_curtailment_ceiling` is a registered `ScenarioConfig`
boolean and `spp_curtail_depth_wind` a registered float at its **declared dataclass default**,
identified off SPP's own published curtailment MW (§3) and **frozen** — never swept against a gate
(rule 1 condition (c), rule 24 `[R-REGISTRY]`). The arm must reproduce keeper 14's ledger:
`build_dof_ledger.py --iso SPP --check <bundle>` → **5 entries / 3 residual**, same five names.
`offer_curve_by_group` is untouched: SHA-256 `090abd793b5fa5a7`, and the run carries keeper 14's
own `authorized_price_tuning` declaration unchanged.

---

## 9. EXECUTION PLAN (rules 32 / 34 / 36)

* **The parent never solves** (32(a)). Phase 0, this document, composition, scoring and
  registration are the parent's; every LP is a shard's.
* **ONE SHARD PER YEAR**, seven of them (2019…2025) — rule 36 `[R-YEAR-ISOLATION]` (a), the one
  place rule 32(b)'s fan-out ban does not apply, because rule 34(a) makes every shard push its
  FULL bundle including `dispatch/<year>_P1.parquet` so the legs compose.
* **Rule 34(c): every year the ISO carries.** SPP's registered year union, enumerated from
  `frontend/data/backcast/registry/*.json` **before** anything else: **{2019, 2020, 2021, 2022,
  2023, 2024, 2025}** — seven, none omitted.
* **Trap (n): the two sides differ.** Keeper span (2023–2025) runs `mid_vintage_exit_carry=False`,
  `gas_price_override=2.54`, `weather_year=2023`; the rung (2019–2022) runs `True` / `2.57` /
  `2019`. They are composed **separately** and each shard hard-stops on its OWN expected value.
* **Rule 34(a): each shard pushes its bundle** via a `.gitignore` NEGATION for its own out-dir
  then a **plain `git add`** (`-f` is refused by the auto-mode classifier). The negation pattern
  was verified in this session against `results/calibration/*/dispatch/` and
  `results/calibration/*/*.parquet`: both are re-included.
* **Rule 32(d):** the parent keeps per-year dirs out of `main` by gitignore, never `rm`
  (rule 31 `[R-RETAIN]`).

---

## 10. SECOND DELIVERABLE — the deleted-rule footprint sweep (taken whatever the ceiling does)

SPP-67's defect was a removed governance rule (`[R-HOLDOUT]`, deleted 2026-09-09) still narrowing
what a measured input was allowed to read. The sweep for other instances is run in this session and
filed as cards; **only SPP's are acted on** (rule 25). Reported in the RESULT.

---

*Rules bearing on this lane: 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 19
`[R-ONE-MECH]`, 21 `[R-DOF]`, 23 `[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`, 25 `[R-ISO-SCOPE]`, 27
`[R-PUSH]`, 28 `[R-MECH-MATRIX]`, 29(b) `[R-SCREEN]`, 31 `[R-RETAIN]`, 32 `[R-SHARD]`, 34
`[R-SHARD-PROMOTABLE]`, 35 `[R-PROMOTE]`, 36 `[R-YEAR-ISOLATION]`.*
