# PRECOMMIT — capx D75: a delivery-year vintage axis on PJM's VRE ELCC accreditation

**Lane:** capx D75. Charter: pack §D75 + `FINDING-capx-d66-2026-09-06.md` §8 card B (and its §1.2
position definition). Branch `claude/capx-d75-pjm-vre-elcc-x1lilr`, fresh off `origin/main`
**2fa2f23a**. **DATA PROFILE: pjm.** MODEL: Opus (rule 27 `[R-PUSH]` — the card's scope writes
`src/market_sim/`).

**Pushed BEFORE any solve, and — as it turns out — before any build.** Every number below is
measured from committed artifacts, from the code at HEAD, or from a primary PJM publication whose
sha256 is recorded. **No LP has been run in this lane, and none will be**: phase 0 stops the card
short of the build (§5). Instrument: `docs/handoffs/d75/vre-elcc-vintage-phase0-2026-09-06.{py,json}`.

---

## 0. Three charter premises that do not survive contact with the primary record

All three are corrected here, in the open, before anything is measured against them. Each is a
**published-document** correction, not a modelling judgement.

**(a) The 2024/25 ratings the charter names are SUPERSEDED.** The charter and D66 §4.5 quote wind
**0.16** / solar **0.36 fixed, 0.54 tracking** for delivery year 2024/25, from PJM's December 2021
ELCC Report (Table 2, p.4–5; sha256 `1305626c…`). PJM's 2024/25 BRA was delayed and re-executed
(FERC ER23-729 — the repo's own `demand-curve/pjm/README.md` records the compressed schedule), and
PJM **re-ran the ELCC study**. The December 2023 ELCC Report states in its Introduction (p.1),
verbatim: *"ELCC Class Ratings are calculated for each delivery year in the period 2024/2025 –
2033/2034 but only the 2024/2025 values are final (the results for the rest of the delivery years
are preliminary)."* Its Table 2 (p.5), re-posted standalone as `elcc-class-ratings-for-2024-2025.pdf`
on **2023-12-29** (sha256 `f3fb54db…`), gives:

| class | Dec-2021 (what the charter / the repo carry) | **Dec-2023 — FINAL for DY 2024/25** |
|---|---:|---:|
| Onshore Wind | 16 % | **21 %** |
| Offshore Wind | 37 % | **47 %** |
| Solar Fixed Panel | 36 % | **33 %** |
| Solar Tracking Panel | 54 % | **50 %** |

Wiring the Dec-2021 set would put a superseded number on the accreditation path — rule 14
`[R-ACCURATE]` forbids it as squarely as it forbids an estimate.

**(b) The scope limit is one year too narrow. PJM's ELCC regime began with the 2023/2024 BRA, not
2024/25.** PJM posted `elcc-class-ratings-for-2023-2024-bra.pdf` on **2021-12-16** (sha256
`c50890fb…`): Onshore Wind 15 %, Solar Fixed 38 %, Solar Tracking 54 %. The December 2021 report's
own Table 3 is titled *"Comparison of ELCC Class Ratings, 2024/2025 BRA vs 2023/2024 BRA"*. So
**2023/24 is in scope**; only 2022/23 and earlier are genuinely pre-ELCC, and those stay out of
scope exactly as chartered.

**(c) The delivery year ↔ model year mapping in D66 §4.5 is off by one, and its pools are frozen.**
The model's own resolver is authoritative: `capacity_deliverability.resolve_delivery_year("PJM", Y)
== f"{Y}/{Y+1}"`, and every D48 call site passes `accreditation_year=year` (the model calendar
year). So **model year 2024 is DY 2024/2025**, with pools wind **11,653.9** / solar **6,990.4** MW
— not the 10,153.9 / 4,549.8 D66 §4.5 calls "2024/25's own pools". Those are the **2021 base-year**
pools: D66's instrument reads them once from `evolution_2021.json` and reuses them for every
delivery year (`supply-census-2026-09-06.py` L139–L163), although its own comment states the pool
"is the base year's pool plus every addition decided in 2021..Y-1" — the additions are never added.
D66's §1.4 table is unaffected (it reads `capacity_clearing` per year and maps model year Y → DY
Y/Y+1 correctly); the defect is confined to the pinned VRE/storage rows §3.2/§3.3 and §4.5 read.
Consequence for this card is stated at §4 and routed at §6.

---

## 1. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — **LIVE, not re-litigated**

The charter fixes this and forbids re-opening it: the D67 lane audited `5bb70047..HEAD` over the
arm-A window and found a LIVE hunk — `DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` moved
**0.036 → 0.064645** (`FINDING-capx-d67-2026-09-06.md` §2.2). **Form 4 is VOID: the D57 arm-A
committed bundle is not a valid control for a new solve, and any screen this card ran would have to
buy its own control at HEAD.** That cost is recorded here so §5's stop is priced honestly, and it is
one more reason not to spend an LP on a phase 0 that has not cleared.

The arm-A ledgers ARE still valid as a **measurement** of what the model accredited under the
incumbent registry — that is a read of committed artifacts, not a differencing of two solves, and
G-DRIFT does not bear on it.

---

## 2. The vintage rule, fixed ex ante

Had the card built, this is the rule it would have carried, fixed here before any measurement is
graded against it:

* The gate is a **new default-OFF `ScenarioConfig` field in the D48 family**, resolved through the
  SAME predicate D48 uses — `retirements.accreditation_design_vintage_armed(config, iso)` — so the
  thermal and VRE halves can never be devintaged apart (rule 19 `[R-ONE-MECH]`; D48's own docstring
  names the mixed-basis failure this prevents).
* The seam is `resolve_renewable_capacity_credit`, threaded `config` / `year` exactly as
  `thermal_accreditation_fraction` already is. `year=None` or gate-off resolves the registry curve,
  byte-identically.
* **Zero scalar fields** (rule 21 `[R-DOF]`): every rating is a published PJM class rating,
  reconciled to `data/raw/capacity-market/elcc/pjm/pjm.csv` by test, byte-for-byte.
* Vintage assignment is by **delivery year**, `resolve_delivery_year("PJM", year)`:
  DY ≤ 2022/23 → pre-ELCC, out of scope, registry unchanged; DY 2023/24 and 2024/25 → that year's
  published class-average ratings; DY ≥ 2025/26 → the marginal-ELCC regime.
* **Forward-edge rule**: beyond the last published delivery year, hold the last published rating —
  the same forward-only extension `resolve_forecast_pool_requirement` uses, so every in-table and
  pre-table year is byte-identical.

---

## 3. The one new operand — **NOT OBTAINABLE.** The chartered STOP fires

The model carries a single `solar` class; PJM rates **two** (Solar Fixed Panel / Solar Tracking
Panel). Blending them needs a fixed-tilt / tracking **MW split**. The charter: *"comes from PJM's
own Table 5 mix, source doc + page, NEVER chosen; if the table is not in-repo, intake it additively
and STOP rather than estimate (rule 14)."*

**PJM publishes no such split for any PRE-reform vintage.** Checked, primary documents, all
sha256-recorded:

| document | what it publishes | MW by class? |
|---|---|---|
| Dec-2021 ELCC Report (`elcc-report-december-2021.ashx`, 15 p.) | Tables 1–3: assumptions, 2024/25 ratings, a 2023/24-vs-2024/25 comparison | **no** |
| Dec-2022 ELCC Report (15 p.) | Tables 1–4: ratings for 2023/24 3IA, 2025/26 BRA, 2026/27 BRA + a 2023–2032 preliminary series | **no** |
| Dec-2023 ELCC Report (16 p.) | Tables 1–4: FINAL 2024/25 ratings + a 2024–2033 preliminary series | **no** |
| `elcc-class-ratings-for-2023-2024-bra.pdf` / `-for-2024-2025.pdf` (1 p. each) | the rating table alone | **no** |
| 2024/2025 BRA Report (20 p.) | offered/cleared UCAP by resource type — **"Solar" is ONE type** | **no** |
| 2025 PJM ELCC/RRS, Table 5 pp.16–17 | installed MW paired with ratings — **2026/27 and 2027/28 ONLY** | yes, wrong vintage |
| 2022 / 2023 / 2024 ELCC/RRS | — | **do not exist** (every URL pattern soft-404s; PJM's ELCC page lists no RRS before the 2025 study) |

So there is **nothing to intake**: the operand is not in the repo *and not published*. The
chartered STOP is the correct outcome and it fires here.

To keep the card decidable rather than merely blocked, §4 reports the delta as a **bracket over
every candidate mix** — the two PJM-published post-reform Table 5 mixes, an explicitly-labelled
EIA-860 footprint proxy, and both arithmetic bounds. **None is adopted; the bracket exists so the
sign and magnitude can be stated without choosing a weight.**

---

## 4. Phase 0 — the measurement, and the pre-declared band test

Zero LP. Read from the D57 arm-A committed ledgers, whose `wind_cap_mw` / `solar_cap_mw` /
`renewable_credit_applied` are written from the *same* arrays that feed
`accredited_firm_capacity_mw(..., accreditation_year=year)` (`runner.py` L4694 and L4796), so a
ledger's pools × its credits **is** the accredited VRE that year counted. PJM's persistent fleet
carries no wind or solar units, and PJM has no internal-supply accounting ratio, so
Δ accredited VRE flows 1:1 into `census_mw`.

| model yr | DY | regime | wind pool | solar pool | published W / F / T | **Δ net, full mix bracket** | **Δ net @ PJM's own Table-5 mix** |
|---:|---|---|---:|---:|---|---:|---:|
| 2021 | 2021/22 | pre-ELCC | 10,153.9 | 4,549.8 | — | — | out of scope |
| 2022 | 2022/23 | pre-ELCC | *(ledger omits the pool fields)* | | — | — | out of scope |
| 2023 | 2023/24 | class-avg | 10,153.9 | 4,549.8 | 15 / 38 / 54 % | −1,395.2 … −667.2 | **−754.6** |
| 2024 | **2024/25** | class-avg | 11,653.9 | 6,990.4 | **21 / 33 / 50 %** | −767.7 … **+420.6** | **+277.9** |
| 2025 | 2025/26 | marginal | 11,653.9 | 9,431.0 | 38 / 10 / 14 % | −410.0 … −32.7 | −78.0 |

**The chartered phase-0 gate — "the delta must land inside the pre-declared band (DOWN 0.6–1.4 GW)
before any solve" — FAILS on DY 2024/25, on both legs.** Measured range −767.7 … +420.6 MW; the
sign is **not** DOWN at any PJM-published mix. Under the charter that is where the card stops.

**Why the pre-declaration read DOWN 0.6–1.4 GW, decomposed exactly** (at PJM's 2026/27 Table-5 mix;
the instrument reports every mix):

| basis | Δ net MW | leg |
|---|---:|---:|
| D66 §4.5 / the charter — 2021 base pools + Dec-2021 ratings | **−664.0** | — |
| + correct DY 2024/25 pools (§0(c)) | −33.5 | **+630.5** |
| + operative Dec-2023 ratings (§0(a)) | **+277.9** | **+311.5** |

The charter's basis reproduces D66 §4.5's bracket to the MW (−1,384.6 … −565.7 vs its
"−1,384.7 … −565.7"), which is the check that this reconstruction is theirs and not a straw man.
**Both corrections push the same way, and the pool-year leg is the larger.** The pre-declared band
is not wrong arithmetic — it is the right answer to **DY 2023/24**, which is precisely where the
table above still lands it (−667 … −1,395 MW, DOWN at every mix).

**The charter's bug-test cannot be applied as written.** It says *"a lane that finds the census
moving UP has a bug, not a result."* The UP direction here survives the strongest available check:
both classes move **toward** PJM's published accreditation, not away from it. On DY 2024/25, against
PJM's cleared UCAP (2024/25 BRA Report Table 9, p.14) —

| class | model, incumbent | model, vintaged | PJM published | |
|---|---:|---:|---:|---|
| Wind | 4,778.1 | **2,447.3** | 1,396 | 3.42× → **1.75×** |
| Solar | 743.8 | **3,352.4** | 4,232 | 0.18× → **0.79×** |

The census rises because the solar leg was under-credited by more than the wind leg was
over-credited **once the right pools are used**. That is rule 14's signal working normally, not an
arithmetic error.

---

## 5. STOP — what this lane does NOT do

1. **No solve, of any arm, at any horizon.** Phase 0 has not cleared its pre-declared gate (§4), and
   form 4 is void so a screen would additionally have to buy a control (§1).
2. **No build.** No `ScenarioConfig` field, no registry vintage axis, no default, no cache-key
   change, no matrix row or cell, no registration, no keeper, no board byte. §2 records the rule the
   build *would* carry; it is not written.
3. **No estimated operand.** The fixed/tracking split is not chosen, not proxied, and not carried
   forward into a default (§3).
4. **No repair to D66.** §0(c)'s defect is reported and routed (§6 of the FINDING), not patched from
   this lane.

---

## 6. Pre-declared signs, recorded so they cannot be written to fit

Recorded here for whichever lane the director charters next, before that lane measures anything:

* On PJM's **operative** ratings, DY 2024/25's accredited VRE moves **UP** at both of PJM's own
  published Table-5 mixes (**+277.9** and **+285.2 MW**) and at the EIA-860 footprint proxy
  (+149.5 MW). It turns DOWN only above a **35.4 % fixed-tilt** share (the exact break-even:
  11,653.9 × (0.21 − 0.41) + 6,990.4 × (b − 0.1064) = 0 ⟹ b = 0.43983 ⟹ f = 0.354), which is
  three times PJM's own published fixed share and half again the EIA-860 proxy's.
* DY 2023/24 moves **DOWN** at every mix (−667 … −1,395 MW).
* DY 2025/26 moves **DOWN** at every mix, and is **small** (−33 … −410 MW).
* Summed over the three in-scope delivery years the net is **negative at every candidate mix**, so
  D66 §8 card B's headline — the accurate input widens the position residual on balance — survives
  the corrections. What does not survive is its per-year sign and its magnitude.
