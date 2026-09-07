# FINDING — SCN-WS5A-POLICY-CAISO: the Stage A-POLICY case set, solved and scored

**Lane** SCN-WS5A-POLICY-CAISO (COORDINATOR, ruling **S16**; this is the FINISHING session) ·
**Model** Opus (`claude-opus-5`, rule 27 `[R-PUSH]`) · **Date** 2026-09-07 · **Branch**
`claude/scn-ws5a-policy-caiso-finish-ctxime` (harness-assigned; the issuance stem was
`claude/scn-ws5a-policy-caiso-c2-…` — same lane, one branch, the mismatch every SCN lane has
recorded) · **Base** `origin/main` `e0cc4d14`; the state this session verified is
`32516df6` (desk r#20), an ancestor of it · **Data profile** `caiso` · **Campaign**
`scn-campaign-policy-2026-09-06`, kind `scenario`, `reference_case: REF` ·
**THE PIN** `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-scn-ws5a-policy-caiso-2026-09-07.md` (pushed before the
first solve; every §2 key, §3 volume, §4 price and §6 prediction below is quoted from it
unrevised) · **Solves spent by THIS session: ZERO.** All eight legs were solved and registered
by the four shard sessions before this one opened; §1 verifies the registered set against the
PRECOMMIT's surviving set and finds nothing missing, so no shard was launched.

---

## 0. Bottom line

1. **All eight surviving legs are solved and registered — 40 solve-years, 4.21 h of LP, every
   key matching the PRECOMMIT's §2 table to the character.** Nothing was left to solve, so this
   session spent no LP (§1).
2. **CAISO's CES premium acts through DISPATCH, exactly as the PRECOMMIT's §6.3 P-1 argued — and
   it SATURATES between $10 and $30/MWh, which P-7 predicted it would not.** ΔCO2 at 2030 is
   **−0.8205 / −0.8152 / −0.8317 Mt** at P10 / P20 / P30 — the P20→P30 step is **−0.0165 Mt =
   0.086 %**, against a pre-registered ">1 %" band. The channel is `gas_cc_ccs` displacing
   unabated `gas_cc`, and it saturates because **the 3 GW/yr retrofit cap is already binding in
   REF**: the CCS fleet sits at 2,996.6–2,999.9 / 5,979.1–5,998.4 / 8,885.7–8,997.0 MW against a
   cumulative cap of 3,000 / 6,000 / 9,000 MW in every arm, REF included (§4.1).
3. **The S15 bracketing leg is the campaign's cleanest demonstration that the entry channel is
   real and correctly masked, and it is CAISO's only entry response.** `CES-P60` is the one arm
   whose entry attribute exceeds REF's ($60 vs the flat $50 RPS escape), and it is the one arm
   that builds: **+1,000 MW of new nuclear in 2029**, displacing **1,031.9 MW of backstop gas
   CT**, worth **+8.1237 TWh** of nuclear generation and **−2.5180 Mt** of CO2 at 2030 over
   `CES-P30`. Every masked rung (P10/P20/P30/T80) builds **byte-identically to REF** (§7).
4. **`CES-T80` exercises BOTH limbs of the CES identity in one arm, and CAISO is the first ISO in
   the campaign to MEET the federal target in a year.** The row escapes at the ACP **$50.0000
   exactly** in 2026–2029 and goes **strictly interior at 6.9465** in 2030, where credited
   generation reaches **178.915 TWh** against an obligation of **178.912 TWh**. My P-8 bet was
   that *both* 2029 and 2030 would flip; **only 2030 did** (§5).
5. **The whole voluntary axis is inert on CAISO, confirmed on the two legs that carry it.** Both
   surviving voluntary rows price at **−0.0** in all five years with escape 0; `CES-P20+VOL-HI`
   is not byte-identical to `CES-P20` but its differences are LP degeneracy, proven by an
   objective that moves in **both directions** across years (+34,708 to −225,621, i.e. ±3×10⁻⁵
   relative) — a constraint can only raise a minimum (§4.4).
6. **Leakage: `import_co2_mt_reported` is 0.0000 in every measured Stage-A year except one.**
   `CES-P60` books **0.020423 Mt** at 2030 — the first non-zero CAISO import CO2 in the campaign
   — because its own entry response removed 1,021 MW of backstop CT and pulled a carbon-bearing
   tranche into merit in scarcity hours. **A records gap is routed**: only two of the eight legs
   committed the `annual_readout.json` that carries this line (§9 item 1).
7. **Gate scoring, Stage-A legs only (seven legs, `CAP-STATE-TIGHT` excluded under S17):
   9 PASS, 1 VACUOUS, 2 FAIL, 1 BOUNDED-not-measured.** Both FAILs are on `CES-P60` and both are
   the entry response the leg exists to find, arriving through gate wordings drafted before it
   was observed. No gate killed an arm (§3).
8. **`CAP-STATE-TIGHT` is OUT of Stage A under owner ruling S17 and is reported as a Stage-B seed
   in §8.** It stays registered. Its measured content confirms NEISO's S17 basis and exceeds it:
   the "tight" cap **permits +6.27 / +12.86 / +16.51 Mt more leakage-inclusive CO2 than REF** in
   2028–2030, builds **zero** CCS where REF builds 8.9 GW, prices at **$4,975/t**, and sheds
   **12.2 TWh** of load.
9. **Carried caveat, from the predecessor lane, unchanged:** RESOLVE-CAISO's re-solved REF passes
   G1–G5 and **misses both of its magnitude bands** (P-A −11.2021 Mt against a 3–8 Mt band; P-B
   −0.9799 Mt against 1–3 Mt). Every delta below differences against that REF; its *levels* are
   disclosure-only under G2 (§3, G2).

---

## 1. Phase 0 as committed, and the registered set verified against it

### 1.1 The PRECOMMIT's surviving set vs what is on `main`

The PRECOMMIT §2 killed six of fourteen cases on a proven one-field identity and named **eight
legs to solve**. All eight are registered at `32516df6` and still at `e0cc4d14`:

| PRECOMMIT §2 case | PRECOMMIT key | key in the committed bundle | registered sidecar |
|---|---|---|---|
| `CES-P10` | `f672e9134d51a475` | `f672e9134d51a475` | `…-ces-p10` |
| `CES-P20` | `46f5eb984e5a4614` | `46f5eb984e5a4614` | `…-ces-p20` |
| `CES-P30` | `cedae86096ba6c3e` | `cedae86096ba6c3e` | `…-ces-p30` |
| `CES-P60` (S15) | `cb35acef1879e80e` | `cb35acef1879e80e` | `…-ces-p60` |
| `CES-T80` | `2ad09fb1eac689a9` | `2ad09fb1eac689a9` | `…-ces-t80` |
| `CES-P20+VOL-HI` | `130a2410b012cf93` | `130a2410b012cf93` | `…-ces-p20-vol-hi` |
| `ALL-CLEAN` | `e2820065dbdcb708` | `e2820065dbdcb708` | `…-all-clean` |
| `CAP-STATE-TIGHT` | `2c5abed281bcee82` | `2c5abed281bcee82` | `…-cap-state-tight` |

Run ids are `caiso-2026-2030-scn-campaign-policy-2026-09-06-<label>`. Every leg reports
`solved_years [2026, 2027, 2028, 2029, 2030]`, `n_solved_years 5`, `error null`.
**Nothing is missing; the shard channel was not used and no LP was spent by this session.**

`CES-P60` carries `case: "CES-P30"` in its `duals.json` with the resolved key
`cb35acef1879e80e` — the declared `--set federal_ces_premium_usd_per_mwh=60.0` provenance
deviation of PRECOMMIT §A.3, exactly as pre-declared, because the campaign matrix carries no
`CES-P60` row and that file is outside this lane's regions (§9 item 4).

### 1.2 The six kills stand — nothing solved contradicts them

The four `CARB-*` kills rest on the S2 floor resolving carbon **identically** in REF and in every
carbon arm (30.0242 / 32.1259 / 34.3747 / 36.7809 / 39.3556 $/t, PRECOMMIT §4.1) with
`carbon_price_path`'s only LP-input consumer audited to one seam (`carbon.py:187`). Nothing in
the eight solved legs touches that argument: every solved leg carries the same resolved adder,
and `rps_dual` is **50.0 in all eight legs and all five years**, confirming the mask premise
post-solve (§7). `VOL-MID` / `VOL-HI` were killed on a slack-row identity; §4.4 measures the
same slackness on the two legs that do carry the row, so the kill is corroborated rather than
merely asserted. **20 carbon solve-years and 10 voluntary solve-years were never spent.**

---

## 2. Per-case deltas vs REF, with the leakage line beside every CO2 number

**The leakage line, stated once and then carried.** On CAISO the import node **pays** carbon:
the CARB border adjustment charges `0.428 × resolved price` on the import tranche VOM, so only
the zero-EF tranches (PNW hydro, midC, DSW solar) clear and the three carbon-bearing ones
(DSW_CCGT 0.37, DSW_CT 0.55, WECC_scarcity 0.428) stay out of merit. **REF books
`import_co2_mt_reported` 0.0000 in every year** (WS-1b §4). Every arm below carries the same
resolved carbon price as REF (§1.2), so its border charge is identical and the *price* channel
cannot move the import stack. Where an arm nevertheless books import CO2, a **quantity** effect
did it — and exactly one Stage-A leg does (`CES-P60`, §2.3).

**Measurement caveat, stated at the head rather than buried.** `import_co2_mt_reported` and
`unserved_mwh` live in `annual_readout.json`, which only the shard that solved `CES-P60` and
`CAP-STATE-TIGHT` committed. For the other six legs the line is **NOT COMMITTED**, and this
session may not solve to recover it. Where the table below reads *not committed*, that is what
it means — never "measured 0.0000". §9 item 1 routes the gap. Two structural facts bound it:
those six legs' `total_cap_mw` is byte-identical to their own baseline in every year (REF's for
five of them, LOAD-HI's for `ALL-CLEAN`), and I3 PASSES on all six, which caps unserved at
`< 1e-4 × demand` ≈ 25 GWh/yr.

### 2.1 CO2 (Mt) — arm, delta vs its own baseline, and the leakage line

`CES-P10/P20/P30/P60/T80/P20+VOL-HI` difference against **REF**; `ALL-CLEAN` against **LOAD-HI**
(its own demand posture). `CAP-STATE-TIGHT` is in §8, not here.

| year | REF | `CES-P10` | `CES-P20` | `CES-P30` | `CES-P60` | `CES-T80` | `CES-P20+VOL-HI` | LOAD-HI | `ALL-CLEAN` |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 31.3061 | 31.3061 (+0.0000) | 31.3061 (+0.0000) | 31.3060 (−0.0001) | 31.3060 (−0.0001) | 31.3029 (−0.0032) | 31.3028 (−0.0033) | 34.3009 | 34.2994 (−0.0015) |
| 2027 | 34.5149 | 34.5150 (+0.0001) | 34.5150 (+0.0001) | 34.5150 (+0.0001) | 34.5157 (+0.0008) | 34.5148 (−0.0001) | 34.5145 (−0.0004) | 39.3295 | 39.3302 (+0.0007) |
| 2028 | 30.1194 | 30.0431 (−0.0763) | 30.1328 (+0.0134) | 30.1310 (+0.0116) | 30.1787 (+0.0593) | 30.0488 (−0.0706) | 30.1318 (+0.0124) | 36.8832 | 36.8517 (−0.0315) |
| 2029 | 21.9693 | 21.0791 (−0.8902) | 21.0756 (−0.8937) | 21.0622 (−0.9071) | **18.2829 (−3.6864)** | 20.9613 (−1.0080) | 21.0754 (−0.8939) | 29.6054 | 29.2871 (−0.3183) |
| 2030 | 19.9574 | 19.1369 (−0.8205) | 19.1422 (−0.8152) | 19.1257 (−0.8317) | **16.6077 (−3.3497)** | 19.3398 (−0.6176) | 19.1500 (−0.8074) | 29.2082 | 28.9342 (−0.2740) |

| leg | `import_co2_mt_reported`, per year 2026→2030 |
|---|---|
| REF | **0.0000 ×5** (WS-1b §4) |
| `CES-P60` | 0.0 · 0.0 · 0.0 · 0.0 · **0.020423** |
| `CES-P10`, `CES-P20`, `CES-P30`, `CES-T80`, `CES-P20+VOL-HI`, `ALL-CLEAN` | **not committed** (§2 head; structural expectation 0.0000, not measured) |

### 2.2 Price, and the two years that are disclosure-only

| year | REF `lw_price` | P10 | P20 | P30 | **P60** | T80 | P20+VOL-HI | LOAD-HI | ALL-CLEAN |
|---|---|---|---|---|---|---|---|---|---|
| 2026 | 55.708 | +0.000 | +0.000 | +0.000 | +0.000 | +0.005 | +0.004 | 57.165 | +0.002 |
| 2027 | 55.946 | +0.002 | +0.002 | +0.002 | +0.004 | +0.001 | +0.002 | 57.975 | +0.002 |
| 2028 | 58.205 | −0.055 | −0.062 | −0.063 | −0.065 | −0.079 | −0.079 | 64.476 | −0.040 |
| 2029 | 58.852 | −0.588 | −0.663 | −0.684 | **−2.267** | −0.560 | −0.671 | 69.154 | −0.158 |
| 2030 | 71.554 | −1.227 | −1.515 | −1.529 | **−3.894** | −0.923 | −1.530 | 88.048 | −0.350 |

Direction is right everywhere from 2028: the premium cuts the CCS cohort's offer, and RESOLVE
§3.2 measured that cohort setting price in many more hours post-D77. **The 2029–2030 price
levels are disclosure-only** under G2 (11 and 37 hours ≥ $500, max $967–974 in REF); the deltas
are the campaign-grade quantity.

### 2.3 The by-fuel footprint (TWh) — where the CES response actually lives

| fuel | year | REF | P10 | P20 | P30 | **P60** | T80 |
|---|---|---|---|---|---|---|---|
| `gas_cc_ccs` | 2028 | 22.7396 | 23.0163 | 23.0397 | 23.0457 | 23.0324 | 23.0124 |
| | 2029 | 42.3053 | 45.9325 | 46.0080 | 46.0704 | 46.0358 | 46.0376 |
| | 2030 | 64.9875 | 69.0986 | 70.2198 | 70.3532 | 70.3636 | 67.9392 |
| `gas_cc` | 2029 | 49.9664 | 46.9410 | 46.8928 | 46.8563 | **40.5798** | 46.8552 |
| | 2030 | 38.2577 | 35.3950 | 35.2581 | 35.2190 | **30.5921** | 36.3060 |
| `gas_ct` | 2030 | 4.4094 | 4.3873 | 4.3431 | 4.3257 | **2.9180** | 4.4182 |
| `nuclear` | 2029 | 18.1972 | 18.1972 | 18.1972 | 18.1972 | **26.3210** | 18.1972 |
| | 2030 | 9.0824 | 9.0824 | 9.0824 | 9.0824 | **17.2061** | 9.0824 |
| `import` | 2030 | 44.4344 | 43.6831 | 42.9297 | 42.8725 | **40.8961** | 43.7714 |
| `wind` | 2026→2030 | 16.4618 · 16.4618 · 16.4618 · 18.3053 · 20.1489 | ← **identical in all eight legs, every year** | | | | |
| `solar` | 2026→2030 | 56.8047 · 56.8047 · 56.8047 · 66.3381 · 66.3381 | ← **identical in all eight legs, every year** | | | | |
| `hydro` | 2026→2030 | 18.8032 ×5 | ← **identical in all eight legs, every year** | | | | |

Three readings, each load-bearing:

- **The wind/solar offer channel is exactly inert.** `apply_eac_to_mc` /
  `compute_eac_dispatch_credits` subtract the full premium from wind and solar (credit fraction
  1.00), and it changes **nothing**: both rows are identical to the MWh in all five years of all
  eight legs. CAISO's VRE is already dispatched to its CF bound wherever it is economic; cutting
  an already-zero offer buys no MWh. This is the mechanism behind PRECOMMIT P-2 and it is
  stronger than P-2 claimed.
- **The `gas_cc_ccs` ↔ `gas_cc` substitution is the whole dispatch response, and it saturates.**
  P10 → P30 moves 2030 CCS by **+1.2546 TWh** while P30 → P60 moves it by **+0.0104 TWh**.
- **`CES-P60` is a different animal, and the difference is entry, not dispatch.** Its 2030 CCS
  generation (70.3636) is `CES-P30`'s (70.3532) to within 0.015 %, yet its CO2 is **2.5180 Mt
  lower**. The whole gap is the +8.1237 TWh of new nuclear displacing gas_cc (−4.6269), gas_ct
  (−1.4077) and imports (−1.9764).

### 2.4 Structural rows that do not move

`hydro` and `nuclear` are byte-identical to REF in every arm except `CES-P60` (§7). `retire_mw`
is **identical in every leg and every year** — 0.0 / 1,527.3 / 0.8 / 0.0 / 1,127.2 — so the
Diablo Canyon confirmed exits (SB 846, `data/raw/confirmed-retirements/caiso.csv`, step 0,
instrument-bound) fire on schedule in every arm and no premium defers them. That is
PRECOMMIT P-5's actual claim and it **holds**; what P-5 also asserted — that the nuclear
*capacity path* is therefore identical — does not, and §5 scores it.

---

## 3. Gate verdicts — Stage-A legs only

Per **owner ruling S17** (2026-09-07, desk card D-13) `CAP-STATE-TIGHT` is **excluded from
Stage-A gate scoring**. G10, G11 and G12 are its gates alone and are reported in §8. The seven
Stage-A legs are `CES-P10/P20/P30/P60/T80`, `CES-P20+VOL-HI` and `ALL-CLEAN`.

A gate PASS means only *"the mechanism did what its own arithmetic says"*; it promotes nothing
and reads no residual (rules 1 `[R-STRUCT]`, 29 `[R-SCREEN]`).

| gate | verdict | measurement |
|---|---|---|
| **G1** resolved-input premise reproduces at THE PIN | **PASS** | Already PASS pre-solve. Re-verified post-solve: all eight committed `cache_key`s match the PRECOMMIT §2 table to the character (§1.1); `rps_dual` = 50.0 in all 8 legs × 5 years, confirming the §A.1 mask premise the whole S15 argument rests on |
| **G2** REF-side precondition | **PASS (asserted, as declared)** | REF carries FAIL `{I7, I12}`, WARN `{}`, I3 PASS; backstop ladder 0 → 1,396.4 → 2,792.8 → 3,795.8 → 2,176.6 MW; `rps_dual` at its $50 escape ×5. **Consequence, as pre-declared:** deployment/capacity-mix LEVELS are disclosure-only in 2026–2028 and price LEVELS in 2029–2030; deltas, orderings and duals stay campaign-grade |
| **G3** footprint confinement | **FAIL on `CES-P60`; PASS on the other six** | Six arms move only `gas_cc_ccs`, `gas_cc`, `gas_ct`, `import` and the retrofit capacity, with `nuclear` and `hydro` Δ = 0.0000 TWh and `retire_mw` unchanged — exactly as written. `CES-P60` moves **nuclear +8.1237 TWh** (2029/2030), so the gate as written fails. **Named, not absorbed:** the move arrives through the audited ENTRY seam (`new_entry.py:1131-1143`, attribute 60.0 > REF's 50.0), i.e. inside the target mechanism; the gate's clause enumerating nuclear as unreachable was drafted from the *masked* rungs, where it is true, and $60 unmasks the fold. `retire_mw` and `hydro` are unmoved even here |
| **G4** `CES-T80` / `ALL-CLEAN` dual identity | **PASS (exact, both limbs)** | `CES-T80`: dual **50.0000** = ACP exactly in 2026–2029 where credited < obligation (gaps −20.742 / −31.826 / −21.630 / −0.626 TWh), and **strictly interior 6.946498** in 2030 where credited **178.915** meets obligation **178.912** (residual +0.003 TWh = 1.7×10⁻⁵ of the row, LP tolerance). `ALL-CLEAN`: dual **50.0000** ×5 with gaps −24.889 / −38.626 / −31.625 / −14.181 / −15.409 TWh. **The regime was NOT pre-chosen for 2029–2030** (PRECOMMIT §6.4) and the identity is what is gated |
| **G5** no non-target load-bearing invariant flips PASS → FAIL | **PASS on five; conditional PASS on `CES-T80` and `ALL-CLEAN`** | Against REF's FAIL `{I7, I12}`: `CES-P10/P20/P30/P20+VOL-HI` carry exactly `{I7, I12}` — clean. `CES-T80` adds **I9** (2028: simultaneous chg+dis 0.13 % of throughput, against a 0.10 % tolerance). `ALL-CLEAN` adds **I3** — pre-declared admissible in the gate text as a load case, and now measured to be **inherited, not induced**: its own baseline `LOAD-HI` already fails I3 with 38.8 GWh (2029) and 106.2 GWh (2030), and `ALL-CLEAN` reads **38.8** and **106.2 GWh** — identical to the 0.1 GWh, differing only in breach-hour count (16 → 19, 50 → 56) — and **I9** (2028, 0.14 %). Reported at full magnitude: I9 is a storage-degeneracy tolerance breach at 1.3–1.4× the bar on a rule-9 `[R-EPSILON]` tiebreaker, driven by the premium's negative-offer surface; it is not a mechanism footprint and it kills no arm |
| **G6** no unserved energy where REF has none | **FAIL on `CES-P60` (measured); BOUNDED-not-measured on five; n/a on `ALL-CLEAN`** | `CES-P60` books `unserved_mwh` **461.945** (2029) and **15,724.348** (2030) where REF books 0 — a real gate failure, reported at full magnitude, and its cause is named in §7 (the 1,021–1,032 MW of backstop CT its own entry displaced). I3 still PASSES on that leg because 15.7 GWh is 0.0058 % of load against a 0.01 % bar — **the invariant and the gate disagree, and the gate is the stricter one**. Five legs have no committed `unserved_mwh`; I3 PASS bounds each below ~25 GWh/yr but does not establish 0. The gate does not bind on `ALL-CLEAN` by its own text — and would not have caught anything if it did: its shed energy is `LOAD-HI`'s to the 0.1 GWh |
| **G7** voluntary dual bounded | **PASS (third admissible state)** | `CES-P20+VOL-HI` and `ALL-CLEAN` both price the voluntary row at **−0.0** in all five years with escape 0 — the slack state the gate admits. Ceiling in force is **$7.0/MWh** (`high`), correcting the charter's $4.5 mid literal (PRECOMMIT §3.3); it is never approached |
| **G8** curtailment before thermal | **VACUOUS — reported as vacuous, never as passed** | No binding voluntary year exists on CAISO, so the gate has no year to evaluate. This is P-13/P-14 holding, and it is a null, not a pass |
| **G9** both nettings | **PASS (both reported, §4.5)** | Counts-toward as the headline, additional beside it, the CES dual under each |
| **G-B1** the S15 mask is cleared at $60 | **PASS (pre-solve, and re-verified post-solve)** | `attr` = 60.00 on `CES-P60` against 50.00 in REF and in every masked rung, for wind/solar/geothermal in every zone and year. Post-solve confirmation the pre-solve computation could not give: `rps_dual` stayed **50.0 in all five years of `CES-P60` itself**, so the mask premise is not an artefact of REF |
| **G-B2** `CES-P60` footprint as a CES case | **FAIL, on its G3 clause only** | The gate's own added clause (entry attribute 60.0 vs REF's 50.0) **PASSES**. Its inherited G3 clause fails on the nuclear entry, for the reason G3 records. Reported as a fail because that is what the gate says; adjudicated in §7 as the leg's intended result rather than a defect |
| **G-B3** no non-target load-bearing invariant flips on `CES-P60` | **conditional PASS** | Adds **I9** only (2029: 0.24 %, 2030: 0.18 % of throughput). No I3, no new I7/I12 line. Same adjudication as G5 |

**Score: 9 PASS · 1 VACUOUS · 2 FAIL · 1 BOUNDED-not-measured. No gate killed an arm**, and the
two failures are the same event seen twice — the entry response `CES-P60` was chartered to
find, arriving through gate text drafted before anyone had seen it.

---

## 4. The deployment response vs REF

### 4.1 Builds, retirements and the retrofit cap

| quantity | year | REF | P10 | P20 | P30 | **P60** | T80 | P20+VOL-HI | LOAD-HI | ALL-CLEAN |
|---|---|---|---|---|---|---|---|---|---|---|
| `builds_renew_mw` | 2029 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 | 4,702.2 |
| | 2030 | 702.2 | 702.2 | 702.2 | 702.2 | 702.2 | 702.2 | 702.2 | 702.2 | 702.2 |
| economic entry | 2029 | 2,000.0 | 2,000.0 | 2,000.0 | 2,000.0 | **3,000.0** | 2,000.0 | 2,000.0 | 2,000.0 | 2,000.0 |
| `builds_thermal_backstop_mw` | 2029 | 3,795.788 | 3,795.788 | 3,795.788 | 3,795.788 | **2,763.873** | 3,795.788 | 3,795.788 | 5,585.6 | 5,585.6 |
| | 2030 | 2,176.584 | 2,176.584 | 2,176.584 | 2,176.584 | **2,187.562** | 2,176.584 | 2,176.584 | 4,920.464 | 4,920.464 |
| `retire_mw` | 2026→2030 | 0 · 1,527.3 · 0.8 · 0 · 1,127.2 | ← **identical in all eight legs** | | | | | | | |
| `builds_storage_mw` | 2026→2030 | 0.0 ×5 | ← **identical in all eight legs** | | | | | | | |

`gas_cc_ccs` capacity, against the **3 GW/yr/ISO retrofit cap** (cumulative 3,000 / 6,000 /
9,000 MW at 2028 / 2029 / 2030):

| year | cap | REF | P10 | P20 | P30 | P60 | T80 | LOAD-HI | ALL-CLEAN |
|---|---|---|---|---|---|---|---|---|---|
| 2028 | 3,000 | 2,996.6 | 2,997.8 | 2,999.9 | 2,999.9 | 2,998.2 | 2,996.6 | 2,982.2 | 2,982.2 |
| 2029 | 6,000 | 5,993.5 | 5,985.9 | 5,998.0 | 5,998.4 | 5,997.8 | 5,993.5 | 5,979.1 | 5,979.1 |
| 2030 | 9,000 | 8,885.7 | 8,983.5 | 8,992.5 | 8,995.6 | **8,997.0** | 8,885.7 | 8,968.4 | 8,968.4 |

**This one table explains the saturation.** REF is already inside 0.11 % of the 2028 cap, 0.11 %
of the 2029 cap and 1.27 % of the 2030 cap. The premium can therefore buy at most **+111.3 MW**
of additional retrofit anywhere in the window (P60 at 2030), and the entire premium response on
the capacity axis is that 111 MW. Everything else is **utilization**: 2030 CCS output rises
64.99 → 70.36 TWh (+8.3 %) on a fleet that grows 1.25 %. That is precisely the axis RESOLVE's
P-E declined to predict on and then found decisive (CF 59.3 % → 83.5 %); here it is the whole
mechanism.

### 4.2 `CES-P60`'s capacity substitution, in full

| | 2029 | 2030 |
|---|---|---|
| `nuclear` | 2,240.0 → **3,240.0** (+1,000.0) | 1,118.0 → **2,118.0** (+1,000.0) |
| `gas_ct` | 17,541.8 → 16,509.9 (**−1,031.9**) | 19,713.2 → 18,692.2 (**−1,021.0**) |
| `gas_cc_ccs` | 5,993.5 → 5,997.8 (+4.3) | 8,885.7 → 8,997.0 (+111.3) |
| `gas_cc` | 12,389.9 → 12,385.7 (−4.2) | 9,497.8 → 9,386.4 (−111.4) |
| `total_cap_mw` | 93,772.7 → 93,740.8 (−31.9) | 95,524.3 → 95,503.3 (−21.0) |
| `reserve_margin` | 0.165872 → 0.165684 | 0.152377 → 0.152379 |

**1,000 MW of firm clean capacity substitutes for ~1,026 MW of backstop peaking capacity, at a
system reserve margin that barely moves — and the substitution is not energy-neutral.** New
nuclear runs at ~93 % CF where the backstop CT it replaced ran at ~2.5 %, so the system gets
8.12 TWh of zero-carbon energy it did not have, and loses the peaking availability that was
carrying REF's scarcity hours. That trade is why the same leg produces both the campaign's
largest CO2 cut **and** its only unserved energy and only import leakage (§7).

### 4.3 Wind and solar deployment is untouched by every rung

`builds_renew_mw`, wind capacity and solar capacity are byte-identical to REF in **all eight
legs and all five years**. The CES premium adds **zero renewable entry on CAISO at any level**,
$10 through $60. The $60 rung, which does clear the mask, spends its unmasked attribute on
**nuclear**, not on VRE — because the attribute enters `new_entry`'s screen for every eligible
tech at credit fraction 1.00 and CAISO's VRE queue is already exhausted at the levels the
2029/2030 builds show (4,702.2 / 702.2 MW commissioned in both arms).

### 4.4 The voluntary axis measured on the two legs that carry it

Both voluntary rows price at **−0.0** in all five years, with escape 0 — the slack state
PRECOMMIT §3.2 proved from the resolved volumes (`V` 21.8–32.8 TWh on `CES-P20+VOL-HI`,
26.2–52.8 TWh on `ALL-CLEAN`, against eligible generation `G` of 73.3–86.5 TWh, thinnest margin
+33.670 TWh). `ALL-CLEAN`'s `clean_region_duals` reads `[50.0, −0.0]` in every year: the CES
target row at its ACP escape, the voluntary row slack, beside each other.

**`CES-P20+VOL-HI` is NOT byte-identical to `CES-P20`, and the difference is provably
degeneracy.** P-13 predicted byte-identity; measured, the two differ:

| year | Δ objective | Δ CO2 (Mt) | Δ `lw_price` | largest by-fuel Δ |
|---|---|---|---|---|
| 2026 | **+34,707.80** (+6.5×10⁻⁶) | −0.0033 | +0.004 | gas_cc −17,420.9 MWh |
| 2027 | **−23,087.51** (−3.7×10⁻⁶) | −0.0005 | 0.000 | gas_cc −901.3 MWh |
| 2028 | **−118,889.53** (−1.7×10⁻⁵) | −0.0010 | −0.017 | gas_cc +2,673.3 MWh |
| 2029 | **+377,837.52** (+6.0×10⁻⁵) | −0.0002 | −0.008 | gas_cc −7,671.0 MWh |
| 2030 | **−225,620.67** (−2.9×10⁻⁵) | +0.0078 | −0.015 | gas_ct +14,284.7 MWh |

**The proof is the sign pattern, not the magnitude.** Adding a constraint to a minimisation can
only raise the optimum; adding the escape column can only lower it, but the escape is measured 0
so it contributes nothing. An objective that **falls** in three years and **rises** in two,
by ±3×10⁻⁵ relative, is the solver landing on a different vertex of the same optimal face — not
a row with content. The voluntary axis has **no LP content on CAISO**, and this is the strongest
form of that statement the campaign can produce.

### 4.5 G9 — both nettings, on both carrying legs (ruling S11)

`ALL-CLEAN` is the leg with a live CES target row beside a live voluntary row, so it is where
D-6 would have content:

| year | obligation `target·D` | federal credited | **counts-toward** (headline): implied escape | **additional** (`credited − V`): implied escape | CES dual under each |
|---|---|---|---|---|---|
| 2026 | 135.156 | 110.267 | **24.889** | 51.042 | $50.0000 / $50.0000 |
| 2027 | 148.893 | 110.267 | **38.626** | 71.373 | $50.0000 / $50.0000 |
| 2028 | 163.647 | 132.022 | **31.625** | 71.013 | $50.0000 / $50.0000 |
| 2029 | 179.456 | 165.275 | **14.181** | 60.258 | $50.0000 / $50.0000 |
| 2030 | 196.445 | 181.037 | **15.409** | 68.226 | $50.0000 / $50.0000 |

**The two readings differ by exactly `V` (26.153 / 32.747 / 39.388 / 46.077 / 52.817 TWh) in
escape volume and coincide exactly in dual**, because the row is deep in escape under both, so
both price at the ACP cap. That refines P-14, which claimed the readings "coincide": the *dual*
coincides and the *escape volume* cannot, by construction. The counts-toward reading is the
headline, per S11.

On `CES-P20+VOL-HI` the CES is a **price, not a row** (`clean_region_duals` carries the single
voluntary entry; there is no CES target row to net against), so the netting question has no LP
content there at all. For comparability the same accounting is reported against the notional
target ladder — counts-toward escape 20.742 / 31.826 / 21.604 / 0.654 / **0.000** TWh, additional
42.557 / 56.347 / 48.851 / 30.647 / 30.591 TWh — and is labelled as report-layer arithmetic, not
a measured dual. **Card D-6 remains unexercised on CAISO**, which is the deliverable (§9 item 3).

---

## 5. Predictions scored at full magnitude, including the misses

| # | prediction (PRECOMMIT §6, §A.4) | measured | verdict |
|---|---|---|---|
| **P-1** | `gas_cc_ccs` rises, `gas_cc` falls ~1:1, CO2 falls **monotonically** REF → P10 → P20 → P30 → P60 in 2028–2030 | CCS rises and CC falls in all three years ✔. Monotone in **2029 only**. 2028: 30.1194 → 30.0431 → 30.1328 → 30.1310 → 30.1787 — three arms **above** REF. 2030: P20 (19.1422) sits above P10 (19.1369) | **SPLIT** — direction and mechanism right, monotonicity wrong in 2 of 3 years. Cause named: the retrofit screen is cap-bound (§4.1), so which units convert differs at the margin between arms and the fleet-average emission rate moves by ±0.06 Mt (0.2 %) independent of the premium |
| **P-2** | \|ΔCO2\| < 0.5 Mt in 2026 and 2027 in every premium arm; nuclear and hydro Δ = 0.000 in every year | max \|ΔCO2\| over P10/P20/P30/P60 × {2026, 2027} = **0.0008 Mt**. Hydro Δ = 0.0000 in every leg and year; nuclear Δ = 0.0000 in every leg and year **except `CES-P60`** | **HIT on the band (600× inside it); SPLIT on the nuclear clause** — the exception is P60's entry, which P-2 was written about the *dispatch* channel |
| **P-3** | 2030 `lw_price` falls from 71.554 by **$3–15/MWh at P30** | falls **$1.529** | **MISS** — 2× below the band floor. Labelled in the PRECOMMIT as "the guess most likely to miss"; it was. The sizing error is the same class RESOLVE recorded: I sized a price move from a cost-of-offer cut without accounting for how few hours the cut cohort is actually marginal in |
| **P-4** | entry is masked: `builds_renew_mw` stays 0.0 in 2026–2028 in all three premium arms | 0.0 in 2026–2028 in **all eight legs**; and identical to REF in 2029/2030 too | **HIT** |
| **P-5** | `retire_mw` and the nuclear capacity path are IDENTICAL to REF in every CES arm | `retire_mw` identical in every leg and year ✔. Nuclear **capacity** moves +1,000 MW in `CES-P60` (2029, 2030) | **SPLIT** — the confirmed-exit channel does exactly what its documentation says (SB 846 exits fire on schedule, unaffected by any premium); the capacity path moves through a channel P-5 did not enumerate, **entry**, not deferral |
| **P-6** | `gas_cc_ccs` capacity at 2030 **≥** REF's 8,885.7 MW in every premium arm, weakly monotone; hedged that the 3 GW/yr cap may bind first | 8,983.5 / 8,992.5 / 8,995.6 / **8,997.0** — all ≥ REF and **strictly** monotone. And the hedge is **also** true: every arm including REF is cap-bound (§4.1) | **HIT, and the hedge holds too** — the prediction I was least confident in is the cleanest one |
| **P-7** | CAISO does **not** saturate between P20 and P30; they differ by **> 1 %** on 2030 CO2 | **0.086 %** (19.1422 → 19.1257, −0.0165 Mt). `gas_cc_ccs` differs by 0.19 % | **MISS, by an order of magnitude, and it is the most informative miss of the lane.** I transferred ERCOT's saturation *mechanism* (an entry-queue budget) correctly and concluded CAISO would not saturate because its entry is masked — but CAISO saturates on a **different** binding constraint I had the number for and did not connect: the retrofit cap. The premium's dispatch channel is linear in premium only while capture capacity is free to grow, and it is not |
| **P-8** | `CES-T80` escapes 2026–2028 (dual = ACP $50 exactly); 2029/2030 pre-declared OPEN; **my bet: both flip to interior** | escape at **$50.0000** in 2026, 2027, 2028 **and 2029**; **interior 6.946498** in 2030 | **HIT on the pre-registered 2026–2028 claim; HALF-MISS on the bet.** 2029's gap of −0.626 TWh (0.38 % of obligation) was inside the range I called OPEN and it did not close. CAISO is still the first ISO in the campaign to **meet** the federal target in any year |
| **P-9** | `ALL-CLEAN`'s target row is in escape in all five years, dual $50.0000 exactly | escape ×5, dual **50.0** ×5, gaps −24.889 to −38.626 TWh | **HIT** |
| **P-13** | `CES-P20+VOL-HI` **byte-identical** to `CES-P20` in all five years; voluntary dual 0.0, escape 0.0 | dual **−0.0** ×5 and escape 0 ✔. **Not** byte-identical: CO2 differs by up to 0.0078 Mt, objective by ±3×10⁻⁵ relative | **SPLIT** — the substantive claim (no LP content) holds and is now *proved* by the two-sided objective (§4.4); the byte-identity claim was too strong for a degenerate LP |
| **P-14** | `ALL-CLEAN`'s voluntary row slack; both nettings reported and they **coincide** | dual −0.0 ×5, escape 0 ✔. The two nettings coincide in **dual** ($50 under both) and differ in **escape volume** by exactly `V` | **SPLIT** — right that D-6 is unexercised, imprecise about what "coincide" can mean when the volumes differ by construction |
| **P-15** | `import_co2_mt_reported` **0.0000** in every leg and year except `CAP-STATE-TIGHT`, which I flagged in advance as the one plausible leakage channel | `CES-P60` books **0.020423 Mt** at 2030 — the exception I did not name. The exception I **did** name is right and enormous (§8: 0.019 → 8.934 Mt) | **SPLIT** — the flagged case is right for the reason given; a second leg breaks 0 through a mechanism (an entry-driven firm-capacity deficit) not contemplated. **And the claim is not fully testable**: six of eight legs never committed the line (§9 item 1) |
| **P-B1** | `CES-P60` is the only arm with an entry response; `builds_renew_mw` > REF's in at least one year, "most plausibly 2027 or 2028" | It **is** the only arm with an entry response ✔. But `builds_renew_mw` is **identical to REF in every year**; the response is **+1,000 MW nuclear in 2029** | **SPLIT** — the existence claim, which is what G-B1 was chartered on, is a clean HIT; the technology and the year are both wrong |
| **P-B2** | a leg clearing G-B1 with **no** entry response is a reportable finding; the two candidate explanations named in advance | not exercised — the entry response fired | **N/A (the contingency did not arise)** |
| **P-B3** | `CES-P60`'s dispatch response is `CES-P30`'s doubled; it carries the largest CCS-for-`gas_cc` substitution and the lowest CO2 of any CAISO leg in 2028–2030 | Lowest CO2 in 2029/2030 ✔ (18.2829 / 16.6077). But its **CCS substitution is not larger** — 2030 CCS 70.3636 vs P30's 70.3532, a 0.015 % difference, and 2028 CCS is *below* P30's | **SPLIT, and the miss is the finding.** The dispatch response is **not** doubled; it is saturated at P30's level. P60's advantage is entirely the entry channel — which is exactly what an S15 bracketing leg is for, arrived at by falsifying my own dispatch story |

**Tally: 4 HIT · 8 SPLIT · 2 MISS · 1 N/A.** The two clean misses (P-3, P-7) are both *magnitude*
predictions, and both are under-sized in the same way RESOLVE's two band misses were: I sized a
response from its cost arithmetic and did not check which constraint would bind first. The
carried caveat from RESOLVE (§0 item 9) is therefore not an isolated event on this ISO — it is a
repeated lane habit, and it is named here so the next CAISO lane pre-registers a binding-constraint
census beside every band.

---

## 6. Wall clock and RSS per solve-year

| leg | total wall (s) | peak RSS (MB) | per-year wall 2026 → 2030 (s) | per-year peak RSS (MB) |
|---|---|---|---|---|
| `CES-P10` | 1,317.6 | 5,270.3 | 562.7 · 198.2 · 194.4 · 179.6 · 182.5 | 4,775.7 · 4,498.3 · 4,650.5 · 4,695.3 · 5,270.3 |
| `CES-P20` | 1,353.6 | 5,176.0 | 572.3 · 190.2 · 236.4 · 154.4 · 200.0 | 4,854.3 · 4,299.7 · 4,549.6 · 4,260.2 · 5,176.0 |
| `CES-P30` | 1,039.3 | 5,056.4 | 445.3 · 138.1 · 160.7 · 134.5 · 160.5 | 4,763.6 · 4,409.0 · 4,540.6 · 4,236.1 · 5,056.4 |
| `CES-P60` | 1,360.1 | 5,228.5 | 686.3 · 172.6 · 169.8 · 157.8 · 173.4 | 4,643.2 · 4,385.2 · 4,273.2 · 4,805.8 · 5,228.5 |
| `CES-T80` | 1,088.9 | 5,054.3 | 434.9 · 186.1 · 188.4 · 133.8 · 145.5 | 4,537.2 · 4,366.0 · 4,474.6 · 4,888.2 · 5,054.3 |
| `CES-P20+VOL-HI` | 1,222.4 | 5,123.5 | 520.0 · 162.6 · 209.5 · 183.8 · 146.4 | 4,503.3 · 4,400.2 · 4,651.1 · 4,367.0 · 5,123.5 |
| `ALL-CLEAN` | 1,277.8 | 5,002.9 | 461.9 · 234.2 · 213.7 · 181.0 · 186.9 | 4,771.9 · 3,941.8 · 4,432.4 · 4,978.5 · 5,002.9 |
| **`CAP-STATE-TIGHT`** | **6,505.3** | 5,306.7 | **1,563.4 · 399.5 · 552.8 · 2,819.6 · 1,170.0** | 5,306.7 · 4,996.8 · 4,982.7 · 5,018.7 · 4,811.1 |

**Stage-A legs: 8,659.7 s over 35 solve-years = 4.12 min/solve-year**, against the PRECOMMIT
§8's derived 4.33–5.60 min/solve-year. The shard-width derivation (2 legs per shard against a
60-minute LP budget) was sound and slightly conservative — a Stage-A leg costs 17–23 min.

**`CAP-STATE-TIGHT` costs 4.8× the next-slowest leg** (108 min; its 2029 solve alone is 47 min,
2.4× the whole `CES-P30` leg). The mass-cap row is a dense annual-coupling constraint over every
in-region thermal column and it degrades HiGHS' basis substantially. **Stage-B budgeting must
assume ~13 min/solve-year for a cap leg, not 4.** Peak RSS is stable at 4.0–5.3 GB across all
eight legs, comfortably inside the per-plant memory envelope; the year-1 wall (435–686 s) is
2.4–3.5× the later years' in every leg, the usual first-year fleet-build cost.

---

## 7. Ruling S15 — the threshold beside the masked ladder

**CAISO is a TIE CASE, and the tie is exact.** `STATE_RPS_ACP["CAISO"]` is **50.0 $/MWh**, and
REF's `rps_dual` sits at that escape in **every** year: CAISO's RPS floor rises 0.50 → 0.60
while its RPS-eligible (wind + solar) output is ~31 % of load, so the row never leaves escape.
The entry fold is `attr = max(effective_eac_price_for_tech, rps_credit_for_zone,
_clean_credit_for_tech)` (`new_entry.py:1131-1143`), and the RPS leg carries **no fuel gate**, so
it applies at $50 to every eligible technology.

| year | REF `rps_dual` | `CES-P10` | `CES-P20` | `CES-P30` | **`CES-T80`** | **`CES-P60`** |
|---|---|---|---|---|---|---|
| the arm's own CES credit | — | 10.0 | 20.0 | 30.0 | **50.0** (row dual = ACP, escape) | **60.0** |
| 2026 | 50.0 | masked | masked | masked | **TIE — max(50, 50) = 50** | **60.0, +10.0 strictly** |
| 2027 | 50.0 | masked | masked | masked | **TIE** | **+10.0** |
| 2028 | 50.0 | masked | masked | masked | **TIE** | **+10.0** |
| 2029 | 50.0 | masked | masked | masked | **TIE** | **+10.0** |
| 2030 | 50.0 | masked | masked | masked | **TIE** (row goes interior at 6.9465, i.e. *further* below 50) | **+10.0** |
| **incremental entry vs REF** | — | **0 MW** | **0 MW** | **0 MW** | **0 MW** | **+1,000 MW nuclear (2029), −1,031.9 MW backstop CT** |

**Stated explicitly, as ruling S15 requires: `CES-T80` is a TIE on CAISO, not a live increment.**
Its ACP is $50 and the state RPS escape is $50, so `max(50, 50) = 50` adds **nothing** the entry
screen did not already see in REF — and in 2030, where the row goes interior at $6.9465, its
credit is *further below* the RPS escape, so the tie becomes a strict masking. `CES-T80` is
therefore a **dispatch-and-compliance** case on CAISO and carries no entry information at all.
`federal_ces_replaces_state_rps` is `False` in every arm, so no CES leg suppresses the state row.

**The five masked rungs are byte-identical to REF on every deployment column** — economic entry
2,000.0 MW, backstop 3,795.788 / 2,176.584 MW, `builds_renew_mw` 4,702.2 / 702.2 MW, `retire_mw`
identical, wind and solar capacity identical. **`CES-P60` alone moves any of them.**

**G-B1 is scored from the duals and it PASSES**, pre-solve and post-solve. The post-solve half
matters: `rps_dual` stayed exactly 50.0 inside `CES-P60` itself, so the +10.0 margin is not an
artefact of reading REF's dual into another arm's screen.

**And the leg's entry response has a cost that is part of the finding, not a footnote.** Trading
1,000 MW of ~93 %-CF nuclear for ~1,026 MW of ~2.5 %-CF backstop CT is energy-rich and
capacity-poor: `CES-P60` is the only Stage-A leg that books unserved energy (461.9 MWh in 2029,
15,724.3 MWh in 2030) and the only one that books import CO2 (0.020423 Mt at 2030), because the
peaking capacity its own entry displaced was what carried REF's 37 scarcity hours. **This is not
a defect in the CES row.** It is the reliability backstop and the entry screen valuing the same
MW differently — the backstop sized firm capacity against a requirement, the entry screen bought
energy value — and the honest reading is that CAISO's REF is in an adequacy shortfall (G2: I7
and I12 FAIL in 2026–2028) tight enough that a 1 GW substitution at the top of the stack is
visible in the tail. Routed to the desk as §9 item 2.

**The common $60 level is not re-levelled and was never swept** (PRECOMMIT §A.2): it is one
level for all six ISOs, set above the footprint's highest published ACP, identified from
published ACPs and never from a residual. A level chosen to clear CAISO's own $50 would be the
per-ISO fitting rule 25 `[R-ISO-SCOPE]` forbids.

---

## 8. STAGE-B SEED — `CAP-STATE-TIGHT` (owner ruling S17)

**Status.** Ruling S17 (2026-09-07, desk card D-13) moved this case **out of Stage A**. This
lane's PRECOMMIT §2 marked it SOLVE at key `2c5abed281bcee82` and §4.2 built the binding test
for it; **that solve line is withdrawn**, and the leg had already been solved and registered by
shard G4 before the ruling reached this lane. Per S17 the leg **stays registered**
(un-registering strands a bundle and reddens the parity gate), is **excluded** from §3's gate
scoring, from §0's headline and from the plan §5.1 rows, and is reported here. **Ruling S12's
level is not withdrawn; only the stage moves. Nothing was re-solved and nothing was deleted.**

### 8.1 The binding test, carried verbatim from PRECOMMIT §4.2

> The resolved schedule, from `scheduled_power_sector_budget` (linear between the S12 knots):
>
> | year | budget (Mt) | re-solved REF CO2 (Mt) | naive REF comparison |
> |---|---|---|---|
> | 2026 | **30.5000** | 31.3061 | REF **over** by 0.806 |
> | 2027 | **29.5000** | 34.5149 | REF **over** by 5.015 |
> | 2028 | **28.5000** | 30.1194 | REF **over** by 1.619 |
> | 2029 | **27.5000** | 21.9693 | REF **under** by 5.531 |
> | 2030 | **26.5000** | 19.9574 | REF **under** by 6.543 |
>
> **SCN-CAP §3 measured this budget binding in all five years on the PRE-D77 REF** (31.31 /
> 34.51 / 33.32 / 31.36 / 31.16 Mt — every year above the budget). The charter's precondition P5
> anticipated that the thin margin at risk was CAISO-**2026**; it is not. 2026 is **byte-unmoved
> by D77** (31.3061 pre and post), and what moved are **2029 and 2030**, which D77 cut by 9.39
> and 11.20 Mt and which the naive comparison now reads as slack.
>
> **The naive comparison is the wrong test, and it is not the one I gate on.** `CAP-STATE-TIGHT`
> sets `state_carbon_pricing: true` with `mass_cap_enabled: true`, so the ROW **REPLACES** the
> adder (the resolver invariant, one instrument at a time) — measured in §4.1: the arm's resolved
> carbon price is **$0.0000 in every year** and its program object carries `cap_spec` with
> `price_adder: null`, against REF's `price_adder` $30.02–$39.36 and `cap_spec: null`. The arm
> therefore faces **no carbon price at all** except the row's own endogenous dual. Its emissions
> before the cap acts are consequently **≥ REF's in every year**, which gives a one-directional
> test:
>
> - **REF over budget ⇒ the cap binds, certainly.** 2026, 2027, 2028 — **binding**.
> - **REF under budget ⇒ INDETERMINATE, never "slack".** 2029 and 2030 REF lows are *produced by*
>   the very adder this arm removes: at 2030 the adder is worth
>   `(0.3806 − 0.0375) × 39.356 ≈ $13.50/MWh` to `gas_cc_ccs` against unabated `gas_cc`, and it is
>   what lifted the CCS fleet to 65.0 TWh at an 83.5 % capacity factor (RESOLVE §3.2). Remove it
>   and the CCS fleet loses its merit-order position, unabated `gas_cc` returns, and emissions
>   move back toward the ~31 Mt level REF carried in 2026–2028 — **above** the 27.5 / 26.5 Mt
>   budget.
>
> So the case is LIVE in every year, and gate **G10** is written to test the row's **identity**
> (binding ⇒ emissions = budget to 1e-6 and `co2_cap_price` > 0; slack ⇒ dual exactly 0), never a
> pre-chosen regime.

### 8.2 What the solve measured — the one-directional test vindicated, and then some

| year | budget | `emissions_mt` | residual over budget | `co2_cap_price` $/t | REF's adder $/t | dual ÷ adder | `import_co2_mt_reported` | leakage-inclusive total | REF total | **Δ vs REF** | `unserved_mwh` |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 30.5 | 31.4602 | +0.9602 | 28.6682 | 30.0242 | **0.95×** | 0.019345 | 31.4795 | 31.3061 | **+0.1734** | 0.0 |
| 2027 | 29.5 | 30.5233 | +1.0233 | 66.6577 | 32.1259 | 2.07× | 2.616655 | 33.1400 | 34.5149 | −1.3749 | 0.0 |
| 2028 | 28.5 | 29.5373 | +1.0373 | 160.8161 | 34.3747 | 4.68× | 6.852249 | 36.3895 | 30.1194 | **+6.2701** | 0.0 |
| 2029 | 27.5 | 28.5373 | +1.0373 | 155.1955 | 36.7809 | 4.22× | 6.288630 | 34.8259 | 21.9693 | **+12.8566** | 461.9 |
| 2030 | 26.5 | 27.5373 | +1.0373 | **4,975.1195** | 39.3556 | **126.41×** | 8.934177 | 36.4715 | 19.9574 | **+16.5141** | **12,205,676.3** |

**The cap binds in all five years** (`co2_cap_price` > 0, `n_co2_caps_binding` 1 in every year) —
so PRECOMMIT **P-10 HITS**, including the two years the naive comparison called slack, exactly
for the reason §8.1 gave. The one-directional test was the right test.

**The Stage-B seed content, which is what S17 asked for:**

1. **The "tight" cap is a policy LOOSENING against REF, and by far the largest in the campaign.**
   Reading the only complete emissions basis — in-region plus the border-crossing line REF prices
   out — the cap **permits +0.17 / +6.27 / +12.86 / +16.51 Mt more CO2** than REF in 2026 and
   2028–2030. This confirms NEISO's S17 basis (+2.9 to +13.9 Mt) on a second ISO and exceeds it.
   CAISO's mechanism is sharper than NEISO's because CAISO's REF prices **imports**, so removing
   the adder removes a border charge NEISO never had: `import_co2_mt_reported` goes
   **0.0000 → 8.934177 Mt**, i.e. **24.5 % of the arm's own total at 2030 crosses the boundary
   the cap does not cover**. A reader given `emissions_mt` alone would conclude the cap cut CO2
   by 7.6 Mt at 2030. It raised it by 16.5.
2. **The cap builds ZERO CCS where REF builds 8,885.7 MW.** `gas_cc_ccs` capacity and generation
   are **0.0 in every year** of this arm, against REF's 3.0 / 6.0 / 8.9 GW and 22.7 / 42.3 /
   65.0 TWh, and unabated `gas_cc` runs at **72.85 TWh at 2030** against REF's 38.26. **P-12
   HITS**, and its stated alternative ("if instead CCS rises, the cap's dual is doing the adder's
   work") is decisively excluded. The mechanism is the one §8.1 named: a mass cap prices
   *emissions*; the retrofit screen values *capture* against a carbon price, and with the price
   at $0 the screen never fires. **A quantity instrument that displaces a price instrument
   silently disarms every capital-formation screen that reads the price.** That is the single
   most transferable Stage-B finding here.
3. **P-11 is 4/5 and the miss is informative.** I predicted the cap dual exceeds REF's exogenous
   adder in every binding year; it does in 2027–2030 (2.07× to 126.41×) and does **not** in 2026
   (28.6682 vs 30.0242, **0.95×**). A quantity instrument can price below the price instrument in
   a year where the price instrument's *forward* effect — the retrofit pipeline it was already
   funding — has not yet materialised: at 2026 there is no CCS fleet to lose (retrofit opens in
   2028), so the two instruments are nearly interchangeable and the cap's shadow price lands just
   under the adder it replaced. From 2027 the divergence is explosive.
4. **G10's residual, named rather than absorbed, as the gate requires.** `emissions_mt` exceeds
   the resolved budget by **+0.9602 / +1.0233 / +1.0373 / +1.0373 / +1.0373 Mt** — the cap binds
   exactly on its *covered* set, and the reported total includes an uncovered block.
   `_build_mass_cap_rows` gives import-node and inter-zone flow columns a zero coefficient by
   construction, and `per_generator_membership` zeroes any in-footprint unit whose EIA-860 state
   is not a CARB member state. **The single-flat-EF-class explanation is ruled out
   arithmetically**: residual ÷ biomass generation gives 0.159817 / 0.170663 / 0.173184 /
   0.173184 / 0.173184 t/MWh, so no constant emission rate on a constant class reproduces
   2026–2027. The leading candidate is the out-of-state in-footprint units, whose generation
   varies in 2026–2027 and is flat 2028–2030 — **named as a candidate, not asserted**: the
   covered/uncovered split needs `emissions_by_fuel_mt`, which lives only in the uncommitted
   `results/CAISO/<key>/` bundle (§9 item 1).
5. **The arm's reliability outcome is catastrophic and must not be read past.** At 2030 it sheds
   **12,205,676 MWh (4.51 % of load, 3,078 hours, peak 20,553 MW)**, prices at **$1,906.35/MWh
   load-weighted with all 8,760 hours ≥ $100** and the max at the $2,000 VOLL cap, and trips I3
   FAIL and I14 WARN. The cap is not being met by abatement; it is being met by **not serving
   load**. Any Stage-B design must decide whether that is the instrument's honest answer at this
   stringency or an artefact of the arm removing the only incentive that was building the
   abatement capacity (item 2) — and those are distinguishable by a Stage-B arm that keeps the
   adder **and** adds the cap, which no case in the committed matrix expresses.
6. **Cost.** 108 minutes of LP for five solve-years (§6), 4.8× a Stage-A leg. Budget accordingly.

### 8.3 The gates this leg was to be scored on, reported outside the Stage-A score

| gate | verdict | measurement |
|---|---|---|
| **G10** row identity | **PASS on the dual limb; residual NAMED on the emissions limb** | `co2_cap_price` > 0 in all five years and `n_co2_caps_binding` = 1; no year has a zero dual. `emissions_mt` does **not** equal the budget to 1e-6 — it exceeds it by a fixed uncovered block (item 4), which is the gate's "named rather than absorbed" clause, not a silent pass |
| **G11** one instrument at a time | **PASS (pre-solve, confirmed post-solve)** | Resolved carbon price **0.0000** in all five years with `price_adder: null` and a live `cap_spec`, against REF's 30.0242–39.3556 with `cap_spec: null` |
| **G12** footprint as a carbon case | **PASS with a disclosure** | Fossil rows and imports only: `wind`, `solar`, `hydro`, `nuclear` and `biomass` are byte-identical to REF in every year; `retire_mw`, `builds_renew_mw` and `builds_storage_mw` identical. The disclosure the gate demands is delivered in §8.2's table — the row's dual beside the adder path's exogenous price in the same year |

---

## 9. Routed to SCN-DESK — not executed, outside this lane's regions

1. **RECORDS GAP: six of eight legs committed no `annual_readout.json`, so
   `import_co2_mt_reported`, `unserved_mwh` and `clean_share` are unrecoverable for them without
   a re-solve.** Only shard G4's two legs (`CES-P60`, `CAP-STATE-TIGHT`) wrote it; shards G1–G3
   committed `full_horizon_summary.json` + `duals.json` + `run_config.json` only, and the export
   metrics live in the uncommitted `results/CAISO/<key>/` bundle. **This directly degrades the
   WS-1b §4 leakage duty** — the duty says report the leakage line beside every CO2 number, and
   on six legs it cannot be reported at all. It also blocked §8.2 item 4's covered/uncovered
   decomposition. **The fix is a one-line addition to the shard registration protocol, not a
   re-solve**, and it should land before Stage B: whatever writes the slim bundle should always
   write `annual_readout.json`. This lane may not edit the shard protocol or `scripts/`.
2. **CAISO's adequacy shortfall makes a 1 GW entry substitution visible in the reliability
   tail.** `CES-P60` trades 1,000 MW of nuclear for 1,031.9 MW of backstop CT and produces the
   lane's only unserved energy and only import leakage (§7). The entry screen and the reserve
   backstop are valuing the same MW on different bases — energy value vs a firm-capacity
   requirement — and on a REF that already fails I7 and I12 in 2026–2028 the difference shows up
   as shed load. Whether the entry screen should net an accreditation-weighted capacity term
   against what the backstop would otherwise build is a `model/capacity_evolution` question, not
   this lane's.
3. **Card D-6 is NOT exercised on CAISO** (§4.5), for a now-measured reason rather than a
   predicted one: `V` never binds on either carrying leg. The campaign still needs an ISO where
   `V > G`; on present evidence that is ERCOT's `ALL-CLEAN` and nothing here. Routed beside the
   NEISO lane's identical finding.
4. **The campaign matrix carries no `CES-P60` case** (PRECOMMIT §9 item 1, unchanged and now
   material to three ISOs). MISO, NYISO and CAISO have all executed S15 through the `--set`
   channel, so three committed sidecars record `case: "CES-P30"` with a `set_overrides` block.
   One shared matrix row would fix the label for the remaining ISOs; `configs/scenario_campaign_matrix.yaml`
   is outside this lane's regions.
5. **Card D-3c is sharper on CAISO than anywhere.** Under ruling S10's "credit all eligible
   units" set the voluntary axis has **no LP content on CAISO at all** — proved here by the
   two-sided objective (§4.4), not merely by a slack margin. D-3c's alternative
   (new-builds-only crediting) is what would change that, and CAISO — smallest DC block, largest
   incumbent renewable fleet — remains the sharpest case for the card.
6. **SCN-CAP §3's binding table is stale for CAISO post-D77 and was built on the wrong
   comparison** (PRECOMMIT §4.2 / §8.1). The one-directional test is now vindicated by measurement
   (§8.2), which strengthens rather than weakens the routing: the same restatement plausibly
   applies to NYISO and NEISO, whose lanes read the same table.
7. **The charter's G7 ceiling literal is the mid cell ($4.5).** Corrected to $7.0 per arm in
   PRECOMMIT §3.3; still carried by the other charters. Third lane to route it.
8. **A Stage-B design gap, surfaced by §8.2 item 5.** No committed case expresses *cap + adder
   together*, which is the only arm that can distinguish "the cap's honest answer at this
   stringency" from "the cap disarmed the retrofit screen". Naming it, not building it.

---

## 10. Files

**Written by this session:**

- `docs/handoffs/FINDING-scn-ws5a-policy-caiso-2026-09-07.md` — this file.
- `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` — §5.1 rows **3** and **7**, CAISO
  material appended to the CES-premium, CES-target and Voluntary columns. `CAP-STATE-TIGHT` is
  **excluded** from these rows per S17.
- `docs/handoffs/scenario-desk-ledger-2026-09.md` — §3, the same two rows mirrored.
- `docs/codebase-site/data/mechanism-matrix/CAISO.js` — **LAST commit after rebase**, one
  appended evidence line each on `federal_ces`, `federal_ces_target`, `carbon_price_path` and
  `voluntary_clean_demand`, CAISO's shard only (rule 28(b)).

**Consumed, never edited:** `configs/scenario_campaign_matrix.yaml`, the CAISO base YAML,
everything under `src/` and `scripts/`, every committed bundle and sidecar, every other ISO's
matrix shard and keeper files, `program-status.json`, `ff-verdicts.json`, and the whole
**backcast** namespace.

**Duties discharged:**

- **No solve spent, no default moved, no knob moved, no `ScenarioConfig` field added, no case
  added, no year past 2030.** **DOF ledger: ZERO free parameters.** No `authorized_price_tuning`
  (rule 1's carve-out is a backcast offer-curve channel, untouched by a forecast lane).
- **Rule 15 `[R-DASHBOARD]`:** forecast-family runs, registered into `frontend/data/hindcast/`
  under campaign `scn-campaign-policy-2026-09-06` by the shards; the backcast namespace is
  untouched.
- **Rule 29(c):** no screen bundle and no control bundle exists for this lane — its legs are
  registered campaign arms and its control is the committed REF.
- **Rule 26 `[R-DELETE]`:** nothing deleted. Per S17, `CAP-STATE-TIGHT` stays registered.
- **Rule 27 `[R-PUSH]`:** no existing source file ≥300 lines is rewritten; every pushed file
  ≥300 lines is fetch-back verified.
- **Backcast byte-identity:** untouched by construction — every leg is `mode="forecast"` and no
  code, config default or constant was changed.
- **CI:** `scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` is
  **EXIT 0** at this branch's HEAD (163 sidecars / 2,282 records / 190 declared FAILs).
  **No CI workflow was created.**
