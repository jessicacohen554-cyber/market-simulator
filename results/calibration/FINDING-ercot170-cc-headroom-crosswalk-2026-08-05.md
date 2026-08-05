# FINDING — ercot-170 Phase 0: the ~2.7 GW CC headroom object IS a capability object (102.4 % of the gap, identity error 0.000 GW), and the per-unit crosswalk that would attribute it is NOT LICENSABLE from committed data. FILED-UNLICENSED, no mechanism named.

**Session ercot-170, 2026-08-05. NO LP, no solve, no mechanism armed, no
`ScenarioConfig` field added, no matrix cell verdict minted, keeper UNCHANGED
(`2026-08-05-run168b-year-curves`; NOT-YET, open gates C3a 2023 −32.2 %, C3b 2023
0.604 + 2024 0.206, C3c ledgered CAVEAT ×3).** Charter: mechanism-testing-matrix
§5.1 **item 11**, the ERCOT-163 close-out. Decision rule pre-registered, committed
and pushed **before** the corpus was read:
`docs/PRECOMMIT-ercot170-cc-headroom-crosswalk-2026-08-05.md`. **No band,
threshold or licence was moved after measurement in the permissive direction**;
one pre-registered tier was **retracted** after measurement, which moves the
verdict further from its bar (§4).

Probe: `scripts/probes/ercot170_cc_headroom_phase0.py` →
`results/calibration/ercot170_cc_headroom_phase0.json`. Harness:
`scripts/lib/sced_corpus_instruments.capability_census` (ercot-169's module,
EXTENDED — it imports `ercot163_cc_commitment_state_census`'s `_cap_ref` /
`_train` / `_state_of` / `_hoy` verbatim).

## 0. Verdict

1. **The headroom object is a CAPABILITY object — confirmed, and it needs no
   crosswalk to establish.** The pre-registered attribution identity closes
   **exactly** (error 0.0000 GW against a 0.01 GW construction-error stop). At
   the committed top-100 2023 gap hours the model−reality undispatched gap is
   **2.648 GW**, of which term **A (capability) = 2.713 GW = 102.4 %**; term
   **B (reality's AS reservation) = 0.303 GW** and term **C (dispatch
   difference) = 0.367 GW** very nearly cancel. Branch 2 (REDIRECTED) does not
   fire: this is not an ancillary-services object and not a dispatch object.
2. **The per-unit crosswalk FAILS its pre-registered coverage licence, in both
   legs and by a wide margin.** L1 (SCED-side closure) = **0.5111** as
   pre-registered and **0.3375** on the tiers that survive inspection, against a
   **0.90** bar; L2 (ambiguity budget) = **0.1829** against a **0.10** bar. Per
   the pre-registered rule the verdict is **FILED-UNLICENSED**: the per-unit
   attribution is withheld **in both directions**, no arm is named, and none may
   be built on this record (rule 13 `[R-MEASURED]`).
3. **The blocker is not effort, it is evidence, and ERCOT-160's own README said
   so.** On defensible evidence only **19 of 58** ERCOT CC sites and **19 of 61**
   model CC plants resolve — **11.90 of 35.26 GW** of SCED capability and
   **13.17 of 38.83 GW** of model capability. The remaining ~2/3 rests on
   expanding ERCOT site mnemonics (`FRNYPP` → Forney, `DDPEC` → Deer Park,
   `PANDA_T1` → Temple) from prior knowledge, which **no on-disk artifact
   supports** and which the precommit ruled inadmissible. The NP4-160-SG README
   already stated the limit: *"substation → EIA plant code … this file does not
   carry EIA identifiers and cannot be made to."*
4. **The ERCOT-163 leading candidate — "cogeneration behind private-use
   networks" — is falsified as a COMPLETE explanation, by arithmetic, with no
   crosswalk.** ERCOT's SCED CC universe telemeters **30.397 GW** of
   committed-or-startable HSL at the gap hours, which **exceeds the model's
   entire CC_REGULAR available capability (28.310 GW) by 2.087 GW**. If the
   whole CC_CHP class (4.799 GW available) were behind private-use networks and
   absent from SCED, the model would be **2.09 GW short** on regular CC, not
   long. CC_CHP is therefore materially present in SCED and cannot carry the
   object by itself.
5. **Inside the matched subset the per-unit readings are dominated by GRAIN
   artifacts, not capability excess** — which is exactly what the licence bar
   exists to catch. The largest apparent per-unit excess, Jack County
   (+593.9 MW), is closed to a **1.001** capacity ratio by a single unmatched
   sibling site, `JCKCNTY2`, whose published `UNIT_NAME` set (`CT3;CT4;ST2`)
   continues `JACKCNTY`'s own (`CT1;CT2;STG`). A site-grain crosswalk cannot
   separate "the model over-rates this plant" from "ERCOT registers this plant
   as two sites".
6. **No mechanism is chartered and the hard fences hold.** Nothing here proposes
   a commitment gate, an aggregate cap, a per-hour telemetered-HSL cap, or a
   re-pricing of CC. Item 11 stays open, **re-pointed** (§5): its first step is
   now a **data-intake charter**, not a calibration one.

## 1. The attribution identity — exact, and it settles what kind of object this is

Pre-registered in precommit §1c, computed at the committed top-100 2023 gap
hours (400 SCED intervals; hour set `_ercot161_wall_phase0.json`):

```
U_m − U_r  =  [C_m − H_r]  +  [H_r − C_r]  −  [D_m − D_r]
                 term A         term B          term C
```

| quantity | GW |
|---|---|
| `C_m` model CC available (Σ pmax × availability) | **33.1092** |
| `D_m` model CC dispatch (keeper `class_hourly_2023`, P1) | 30.1013 |
| `H_r` reality telemetered HSL, committed-or-startable states | **30.3966** |
| `C_r` reality energy-dispatchable (HASL) | 30.0937 |
| `D_r` reality Base Point | 29.7339 |
| `U_m` model undispatched | 3.0079 |
| `U_r` reality undispatched | 0.3597 |
| **gap `U_m − U_r`** | **2.6482** |
| **term A — capability** | **2.7126** (**102.4 %**) |
| term B — reality's AS reservation (HSL − HASL) | 0.3029 |
| term C — dispatch difference | 0.3673 |
| **identity error** | **0.0000** (stop at 0.01) |

`C_m` reproduces ERCOT-163's 33.109 GW **exactly**; `H_r` / `C_r` / `D_r`
reproduce its 30.396 / 29.734 GW state census exactly, on the same imported
constructions. `D_m` reads 30.1013 GW against ERCOT-163's 30.0376 — a
**+0.064 GW keeper delta** (ERCOT-163 ran on `ercot158_poolarm_B`; this session
runs on the current keeper `ercot168_yearcurves_B`), disclosed rather than
smoothed.

**All-hours control (pre-registered, NON-GATING).** Over all 8,760 hours (35,038
SCED intervals) the same identity reads `C_m` 29.330 / `D_m` 19.550 / `H_r`
21.827 / `C_r` 21.435 / `D_r` 18.902 GW → gap 7.246 GW, term A 7.503 GW
(103.5 %), B 0.392, C 0.648. `C_m` reproduces ERCOT-163's all-hours 29.330 GW
exactly. **It is reported, and it is deliberately not the gating window**: over
the whole year ERCOT genuinely cycles CC off (ERCOT-163: committed share 72.7 %
all-hours vs 96.4 % at the gap hours), so `H_r` there mixes *commitment state*
into a *capability* comparison — the very conflation ERCOT-163 closed. The gap
hours are the window in which reality is ~fully committed, which is what makes
`H_r` a capability read there. The control's agreement in sign and share is
consistent with §0.1; its magnitude is not a capability number.

**Fleet scope**, the same object at registration grain: model CC nameplate
**38.834 GW** (CC_REGULAR 33.120 + CC_CHP 5.714, 61 plants, 616 LP rows) against
an ERCOT SCED CC universe of **35.260 GW** (`cap_ref`, per-train p98 telemetered
HSL over delivery-2023, 70 trains / 58 sites) — **+3.574 GW, +10.1 %**.

## 2. The crosswalk — what it reached, and where it stopped

Spine: ERCOT MIS NP4-160-SG (`CCP_Resource_Names` → `Resource_Node_to_Unit` →
`Settlement_Points`), published, no judgement. All 56 CC site mnemonics resolve
to a `UNIT_SUBSTATION` and to a `SETTLEMENT_LOAD_ZONE`.

| tier | sites | SCED `cap_ref` GW | cumulative L1 |
|---|---|---|---|
| **X1** committed (`ercot-dam-plant-crosswalk` accepted=1 + `ercot_noncampd_dam_crosswalk`) | 12 | 7.854 | 0.2227 |
| **X2** lexical identity on the published spine | 7 | 4.047 | **0.3375** |
| ~~X3/E3~~ substation-name identity | 2 | 1.050 | 0.3673 |
| ~~X3/E1~~ qse + capacity + zone unique survivor | 8 | 5.070 | 0.5111 |
| **unmatched** | 29 | **17.239** | — |

**L1 = 0.5111 as pre-registered / 0.3375 defensible, bar 0.90 — FAIL.**
**L2 = 0.1829, bar 0.10 — FAIL.** Either failure alone lands FILED-UNLICENSED.

The unmatched SCED block is not marginal: it is led by `FRNYPP` (1.947 GW),
`CBECII` (1.174), `OECCS` (1.157), `LPCCS` (1.138), `WHCCS2` (1.064), `WCPP`
(0.783), `WHCCS` (0.762), `PANDA_T1`/`T2` (0.751/0.740). Every one of these has
an *obvious* expansion to a model plant, and not one of them has an on-disk
artifact that says so.

**L3 — zone frame, REPORTED, pre-declared NOT A GATE.** The published
`SETTLEMENT_LOAD_ZONE` agrees with the model zone on the X1/X2 matches modulo the
known partition mismatch (ERCOT's `LZ_SOUTH` spans model `South` and parts of
`South_Central`/`Houston`; Colorado Bend Energy Center and Frontera are the two
disagreements, both representation artifacts). It does **not** agree with the
`zone` column of `ercot-dam-plant-crosswalk.csv` — see §4.

## 3. What is licensed, and what it says

These stand independently of the crosswalk and are the session's substantive
content:

* **The object is capability** (§1): 102.4 % of the gap, identity closed exactly.
  ERCOT-163's naming is confirmed and quantified.
* **The strong private-use-network reading is falsified** (§0.4):
  `H_r − C_m(CC_REGULAR)` = 30.397 − 28.310 = **+2.087 GW**. *Caveat, stated:*
  `CCGT90`/`CCLE90` is ERCOT's own resource typing and need not align with the
  model's CAMPD/EIA `plant_group` — a resource ERCOT types CC may sit in the
  model's `ST_GAS` or `CT_PEAKER` classes. The arithmetic is exact under the
  class alignment **ERCOT-163 itself used**; a different alignment would need its
  own crosswalk, which is the thing this session could not license.
* **The model's excess is broad, not concentrated in CHP.** Under the defensible
  tiers the unmatched model block is **17.86 GW available across 25 CC_REGULAR
  plants** and **3.96 GW across 17 CC_CHP plants** — the DAM-covered class
  carries ~82 % of the unmatched capability, and CC_CHP (the one CC class the
  `ercot_thermal_dam_availability_*` channel deliberately excludes) carries ~18 %.
* **The channel's shape is where a correction would have to live, if one is ever
  identified.** `derive_ercot_thermal_dam_availability.py` computes
  `avail(class, hour) = Σ_sites live_HSL / Σ_sites rating` and the model applies
  that **fraction** to its **own** class nameplate. A denominator that does not
  match the model's registered capability therefore transports a correct measured
  *ratio* onto a larger MW base. **This is a mechanism-shape observation, not a
  measured defect** — establishing that the denominators differ per unit is
  precisely the licence this session failed to obtain, and the ERCOT-163 §3
  lesson forbids handing an unattributed aggregate forward as a premise.

## 4. Reported against interest — a pre-registered tier RETRACTED after measurement

The precommit's **X3/E1** tier ("qse + capacity ratio ∈ [0.90, 1.10] + zone
agreement leave exactly one surviving model plant") is **REFUTED BY INSPECTION
in-session**, together with **X3/E3**, and both are removed from the defensible
count. Cause, on published data:

* E1's zone leg consumes the `zone` column of `ercot-dam-plant-crosswalk.csv`,
  which is the **unaccepted auto-matcher's PROPOSED PLANT's** zone, not the
  site's own. The published spine falsifies it directly — `FRNYPP`
  `zone_xwalk = South_Central` vs published **`LZ_NORTH`**; `CBEC` `North` vs
  **`LZ_SOUTH`**; `TGCCS` `Northeast` vs **`LZ_NORTH`**; `DDPEC` `North` vs
  **`LZ_HOUSTON`**.
* The matches it produced are wrong on their face: **Paris Energy Center ←
  `INGLCOSW`** (the Ingleside cogen site, 400 km away), **Wolf Hollow II ←
  `DDPEC`**, **Magic Valley ← `PANDA_S`**, **Ennis ← `TXCTY`**, **Thad Hill ←
  `BOSQUESW`**, **Formosa ← `CAL`**.
* "Unique survivor in a capacity window" is not evidence; it is an assignment
  procedure. Writing it into the precommit as an evidence class was an error, and
  it is recorded as one.

**Direction check.** Retracting these tiers moves L1 **0.5111 → 0.3375**, i.e.
further *below* its bar. A post-measurement change to a pre-registered rule is
admissible only in that direction, and this one is: the verdict is unchanged and
strengthened. Nothing was retracted that would have helped.

**A second disclosed construction limit, NOT fixed by moving the bar.** The X2/E3
capacity window [0.70, 1.30] **conditions on the very quantity being measured**:
a plant whose model rating far exceeds its SCED capability fails the ratio test
and is pushed out of `A_derate` into the unmatched block. Six such lexical covers
were blocked — `THW`/T H Wharton (ratio 0.579), `TEN` (0.292–0.340, three
candidates), `FORMOSA`/Formosa Utility Venture (0.214), `SILASRAY`/Silas Ray
(0.404). The window is **not moved**; the effect can only understate `A_derate`
and overstate the unmatched block, and it does not touch the licence verdict
(L1 fails by 0.56 of its bar).

## 5. Item 11, re-pointed — the next step is DATA INTAKE, not calibration

The ERCOT-163 successor text said the first step is *identification, not a
mechanism*. That is right, and this session sharpens it: **the identification is
blocked on an artifact the repo does not hold**, and no amount of calibration work
produces it. What would unblock it, in order of directness:

1. **An ERCOT resource-registration extract carrying resource/unit name →
   county (or nameplate + commercial-operation date).** ERCOT's RARF-derived
   generation-resource listings and the Capacity/Demand-and-Reserves generator
   tables are the public candidates. Either one makes the precommit's **E3
   county leg** and a nameplate/COD join fire on the ~2/3 of the fleet that is
   currently mnemonic-only.
2. **A substation → county/city table for ERCOT.** Strictly weaker than (1) but
   sufficient for E3, and it composes with the NP4-160-SG spine already on disk.
3. Failing both, a **hand-adjudicated site → EIA-plant seed list in the
   ERCOT-110 coal pattern** (`ercot-dam-coal-site-seeds.csv`, all 26 coal sites
   adjudicated with citations) — an explicit, reviewed, per-row human artifact,
   not a model inference. That is an owner-authorized review task with its own
   evidence standard, and it is the honest form of "extend the reviewed
   crosswalk" that ERCOT-163 asked for.

Only after one of those lands does the mechanism question arise, and it remains
what ERCOT-163 said it was: a rule-14 `[R-ACCURATE]` fleet-scope correction on the
**existing** `ercot_thermal_dam_availability_*` channel — **never** a new
commitment gate, **never** an aggregate cap, **never** a per-hour
telemetered-HSL cap. Item 11's **extreme-hour face** (the 4 phantom shed hours,
the 1.7–3.1 GW gas shortness at the top-10 actual hours) was out of scope here
and stays chartered, untouched.

## 6. Carried forward, NOT decided — the ercot-169 open owner decision

ERCOT-169 left an **OPEN OWNER DECISION** on the 2023 application of
`COAL_OFFER_MARGIN_LEVEL_BY_ISO` (ERCOT-137) and `COAL_PEAK_OFFER_LEVEL_BY_ISO`
(ERCOT-140). Both are **NOT-IDENTIFIABLE-2023**: the instrument's coverage licence
fails on the 2023 COAL rows (`curve_share` 0.9702 vs the 0.9876 floor — Martin
Lake 1–3 submit no incremental curve in 20–24 % of online intervals, Mar–Jun).
The **unlicensed** readings are large and one-directional — limb A `level₂₀₂₃`
17.5211, **+1.6404 = 1.76×** its ±0.9300 band; limb C's measured above-min-load
p90 is **$75.00/MWh**, flat at $75 in 9 of 12 months, `level₂₀₂₃` 71.3378,
**+36.14 = 14.4×** its ±$2.5062 band, i.e. the armed constant is roughly half the
measured 2023 top, corroborating ERCOT-168 at fleet scale.

The pre-registered REFUTED branch was **not reached**, so **no candidate arm is
named and none may be built without a fresh owner adjudication**. This session
did not act on it and proposes none of the three options ERCOT-169 §6 laid out.

Also filed by ERCOT-169 for the next **keeper-promoting** session (not this one —
no promotion here): the three margin constants have **no dedicated DOF-ledger
entries** in the keeper attestation. Zero fitted scalars, so it is bookkeeping —
add them and carry limb B's **RETIRED-BY-VERIFICATION** note in.

## 7. Governance

* **No mechanism tested ⇒ no matrix cell verdict minted** (rule 28(b)), the
  ERCOT-163/147/152/161 no-LP precedent. Matrix §5.1 **item 11** is stamped
  EXECUTED-AND-RE-POINTED in this session; `scripts/check_mechanism_matrix.py`
  exit 0.
* **No run produced ⇒ no dashboard registration** (rule 15). Keeper UNCHANGED;
  no bundle, no sidecar, no registry entry.
* **Rule 22 `[R-HOLDOUT]`**: delivery-**2023 only**. `load_corpus_year` /
  `capability_census` refuse any year outside 2023–2025 by construction; no
  holdout year was read, solved or scored. ERCOT holds no `complete` marker.
* **Rule 25 `[R-ISO-SCOPE]`**: ERCOT-scoped throughout; no other ISO's cell or
  artifact read or written.
* **Rule 23 `[R-FROZEN-DERIVE]`**: no derive was re-run and no measured-behaviour
  parameter was re-identified. `scripts/lib/sced_corpus_instruments.py` is
  **extended** (a new `capability_census` + its imports); every ercot-169 function
  in it is byte-unchanged.
* **Rule 28(c)**: no `ScenarioConfig` field added, no solve-affecting code
  touched — the guard is not engaged.
* Scope fences honoured as listed in the precommit §4; the DO-NOT-REDO list is
  carried unchanged.

## 8. DO-NOT-REDO honored

The "~8 GW cheap CC offline block" **DOES NOT EXIST** (ERCOT-163, not reopened);
`energy_online_capability_cap` `R` (ERCOT-159); `ercot_storage_rt_offer_surface`
`R` (ERCOT-162); per-year CT re-identification REFUSED (ERCOT-147, modal identity
11/160); lignite offer SLOPE (ERCOT-143 as adjudicated); `coal_min_load_floor`
both grains; lignite daily unit commitment; coal seasonal LEVEL split;
`coal_offer_level_rebasis` `R`; `tranche_startup_amortization` `G`; ERCOT-168
**OPTION B** stays DEFERRED; the ercot-167 SOC-reserve re-gate still waits on the
H4-item-4 2024 maintenance-season availability defect; the West/Panhandle topology
split is **CLOSED** (`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md`
§§7–10).

**Next shorthand: ercot-171.**
