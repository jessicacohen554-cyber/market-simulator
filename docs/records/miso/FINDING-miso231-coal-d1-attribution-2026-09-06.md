# FINDING miso-231 — the keeper's COAL D-1 regression is an AMPLITUDE loss beside a broad SHAPE gain, and its object is a lane already CLOSED. **No build. Zero LP.**

Session miso-231, 2026-09-06, branch `claude/miso-backcast-calibration-a5oogr`,
off `origin/main` at `4fa2a714`. Successor to miso-230.

**Keeper unchanged: `2026-09-06-miso-230-ctdrag-seam`** (`miso230_ctdrag_seam_K`),
CALIBRATED, C3c the single ledgered caveat. Rule 22: 2023–2025. DOF ledger 41/2.

Discharges the handoff's item (3) — *"a real cost miso-230 introduced, worth a
zero-LP look before anything else"*. Everything below is read from committed
artifacts: both bundles' `hourly/` sidecars and `legitimacy_diagnostics.json`,
and the CAMPD bench D-1 itself scores against. Probe
`scripts/probes/_miso231_coal_d1_attribution.py` →
`results/calibration/_miso231_coal_d1_attribution.json`. **No solve, no
mechanism, no parameter, nothing licensed.**

---

## 0. Verdict

**The regression is real, and it is not the drag's defect.** The CT net-load
drag displaced coal out of its **price-responsive** bands — which is what a
cheaper resource entering merit is supposed to do — and the displacement
registers as a large D-1 `cv_ratio` fall because on this class that statistic
is arithmetically dominated by a **numerically flat block** that is 31–96 % of
the level and contributes no shape at all.

**Three results the miso-230 assessment did not report, and one correction to
the handoff's framing:**

1. **`profile_r` IMPROVES in 8 of 9 coal cells** (COAL_PRB 0.982/0.973/0.977 →
   0.989/0.985/0.978). The keeper's coal tracks MISO's actual diurnal *pattern*
   more faithfully than the predecessor's in almost every cell. The loss is
   **amplitude only**. §2.
2. The underlying object — MISO coal too flat — decomposes into a **sign split**
   no prior finding states: the model **over**-produces coal at night (+580 MW,
   h0–4, COAL_PRB 2023) and **under**-produces it by **2,502 MW** in h10–20. §4.
3. That object is a **CLOSED lane**: `coal_prb_committed_dispatchable` **R**
   (miso-111), `coal_prb_committed_split` **R** (miso-112, "closed in this form,
   both ways"), `miso_coal_night_floor` **I** (miso-113). Its named root cause is
   **offer-level merit saturation**, not commitment structure (miso-111 §1). §5.
4. **Correction.** The handoff names *"the committed take-or-pay band
   (8,900 MW)"* as the reconciliation target. On this measurement that is only
   half right: for **COAL_PRB** the flat block is `mustrun` **alone** (4,780 MW,
   31–37 % of the off-peak level) and the committed band carries **real shape**
   (h0–14 profile std 210 MW in 2023). The committed band is numerically flat
   only for **COAL_BIT** (std 0.6–1.6 MW). §3.

**Nothing should be built for this number in this session, and the C3c frontier
LP is not spent on it.**

## 1. The regression, from the committed D-1 rows

| year | class | `profile_r` | `cv_ratio` | verdict |
|---|---|---|---|---|
| 2023 | COAL_PRB | 0.982 → **0.989** | 0.521 → **0.488** | pass → **FAIL** |
| 2024 | COAL_PRB | 0.973 → **0.985** | 0.554 → **0.492** | pass → **FAIL** |
| 2025 | COAL_PRB | 0.977 → 0.978 | 0.388 → 0.389 | FAIL → FAIL |
| 2024 | COAL_BIT | 0.844 → **0.884** | 0.616 → **0.387** | pass → **FAIL** |
| 2023 | COAL_BIT | 0.882 → **0.905** | 0.785 → 0.574 | pass → pass |
| 2025 | COAL_BIT | 0.854 → **0.875** | 1.289 → 1.257 | pass → pass |
| 2023–25 | COAL_LIGNITE | 0.959/0.953/0.919 → 0.968/0.961/0.915 | 1.494/0.717/0.588 → 1.463/0.615/0.602 | pass throughout |

Gate line `D1_MIN_CV_RATIO = 0.5`, `D1_MIN_PROFILE_R = 0.8`. **`profile_r` clears
its gate with margin in every cell and rises in eight of nine.** Rule 18
`[R-FORCED-BUDGET]`'s shape leg binds only above the forced cap and COAL sits at
~0.3 % forced, so **none of these gate**; standalone C7 was retired at rubric
v3.1.

## 2. What `cv_ratio` measures on this class — an identity, verified to 4 dp

D-1's CV is taken over the hour-of-day profile's off-peak points h0–14
(`D1_OFFPEAK_LAST_HOUR = 14`). Splitting each class's bands into those whose
off-peak profile std is **below 2 MW** (measured, not assumed) and the rest:

| year | class | flat bands | flat MW | % of level | flat std | shape-bearing MW | shape std |
|---|---|---|---:|---:|---:|---:|---:|
| 2023 | COAL_PRB | `mustrun` | 4,780 | 36.1 % | **0.85** | 8,463 | 967.4 |
| 2024 | COAL_PRB | `mustrun` | 4,607 | 37.0 % | **0.57** | 7,844 | 722.7 |
| 2025 | COAL_PRB | `mustrun` | 4,823 | 31.0 % | **0.35** | 10,728 | 433.4 |
| 2023 | COAL_BIT | `mustrun` | 2,753 | 45.5 % | **0.65** | 3,298 | 171.5 |
| 2024 | COAL_BIT | `committed`+`mustrun` | 5,299 | **95.6 %** | **1.63** | 243 | 93.3 |
| 2025 | COAL_BIT | `committed`+`mustrun` | 5,257 | 82.3 % | **0.64** | 1,128 | 236.4 |

The flat block contributes no std, so the class CV collapses to

> **CV = std(shape-bearing bands) ÷ mean(TOTAL level)**

which reproduces the measured class CV to four decimals in **all six cells**
(e.g. 2024 COAL_BIT 0.0168 vs 0.0171; 2023 COAL_PRB 0.0730 vs 0.0730). The flat
block sits in the **denominator only**.

**The consequence.** Energy removed from a shape-bearing band moves the
numerator at full weight while the denominator barely moves. 2024 COAL_BIT is
the extreme: a **−0.9 %** change in level produced a **−37 %** change in
`cv_ratio`, because 95.6 % of that class's level cannot move at all. Scored on
their own, the shape-bearing bands are **more** variable than the actual in five
of six cells (`cv_ratio` 0.55 to **9.05**).

## 3. Which band gave up the energy — rule 19 `[R-ONE-MECH]`

Profile-MW change, keeper − predecessor, over the off-peak window's two halves:

| year · class | h10–14 total | `mustrun` | `committed` | `econ*` | `peak` |
|---|---:|---:|---:|---:|---:|
| 2023 COAL_PRB | −1,879 | **0** | −261 (13.9 %) | **−1,517 (80.7 %)** | −101 |
| 2024 COAL_PRB | −1,522 | **0** | −161 (10.6 %) | **−1,317 (86.5 %)** | −44 |
| 2024 COAL_BIT | −715 | **0** | −6 (0.8 %) | **−697 (97.5 %)** | −11 |

**The `mustrun` band does not move at all, and the take-or-pay `committed` band
gives up 0.8–13.9 %.** 81–98 % of the displacement comes out of the
price-responsive `econ*` bands. This is the LP backing down coal whose offer has
lost merit to a cheaper resource — correct behaviour, and **rule 19 is not
engaged**: no mechanism was stacked, and the keeper's own D-2 already confirms
`ct_netload_drag` as the sole CT_PEAKER forcing mechanism in all three years.

The hold-one-half counterfactuals agree: reverting h10–14 to the predecessor
raises 2023 COAL_PRB's CV to 0.0824 — **above** the predecessor's own 0.0779 —
because the drag's displacement is 3× denser per hour in h10–14 (376 MW/h) than
in h0–9 (129 MW/h). Where the displacement is even across the window
(**2025**, 73 vs 110 MW/h) the CV does not move (+0.3 %). Where it is 34× denser
(**2024 COAL_BIT**, 4 vs 143 MW/h) it falls 37 %.

## 4. The object underneath, and the sign split that names it

The model's coal shortfall is **entirely a daytime shortfall**. COAL_PRB
hour-of-day, model − actual:

| | h02 | h05 | h09 | h12 | h15 | **h18** | h21 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **2023** | **+909** | −257 | −1,811 | −2,330 | −2,358 | **−2,910** | −1,881 |
| **2024** | **+294** | −791 | −1,909 | −2,173 | −2,228 | **−3,038** | −2,169 |

Day/night class balance, 2023, against the CAMPD bench (fossil classes only —
the bench carries no nuclear/wind/hydro/import comparator):

| class | h10–20 actual | model | gap | h0–4 actual | model | gap |
|---|---:|---:|---:|---:|---:|---:|
| **COAL_PRB** | 16,868 | 14,366 | **−2,502** | 11,455 | 12,035 | **+580** |
| COAL_BIT | 6,773 | 6,247 | −526 | 5,986 | 5,831 | −155 |
| CC_REGULAR | 17,424 | 16,659 | −765 | 14,595 | 14,301 | −295 |
| ST_GAS | 2,138 | 2,832 | +694 | 1,052 | 1,122 | +70 |
| CT_PEAKER | 2,770 | 2,732 | **−38** | 581 | 118 | −462 |

**COAL_PRB carries the fleet's largest diurnal shape error — a 3,082 MW
day/night swing — and it is PRE-EXISTING.** The model reproduces MISO's coal
*night floor* and misses its *daytime ramp*. Annually the model is short
10.5/13.1/10.2 TWh of COAL_PRB; the drag moved it a further −1.80/−1.26/−0.66 TWh
along an axis already 3 GW wide, all of it inside C1's band (C1 16/16 PASS).

The same table shows the drag doing its job: **CT_PEAKER's daytime gap is now
−38 MW**, essentially closed.

## 5. Why nothing is built here — the DO-NOT-REDO discipline (rule 28(a))

Every construction that would attack §4 directly is already adjudicated in
MISO's shard, and none is re-opened:

| cell | verdict | evidence |
|---|---|---|
| `coal_prb_committed_dispatchable` | **R** | miso-111, `FINDING-miso111-prb-committed-dispatch-2026-07-31.md` |
| `coal_prb_committed_split` | **R** | miso-112 — *"closed in this form, both ways"* |
| `miso_coal_night_floor` | **I** | miso-113 — binds 1.09–4.24 TWh, changes nothing scored |
| `coal_takeorpay_committed` | **K** | miso-96/102/103/104; contract tonnage sourced, no testable candidate |
| `coal_mustrun_per_plant` | **K** | armed in the keeper |

miso-111 §1 already named the root cause and it is **not commitment structure**:
**merit saturation** — the model's off-peak LMP p10 rises above the entire PRB
SRMC band, so the econ tranches never back out. §2's identity is the same
finding from the other side: what is left is a flat block plus a thin,
over-variable econ layer.

**This finding adds two measurements to that closed lane and no proposal.** The
**sign split** (§4: over at night, −2.5 GW in the day) and the **denominator
identity** (§2) belong to whichever future session opens an offer-level charter
for MISO coal. Neither is a lever, and neither licenses re-testing an `R`/`I`
cell — that needs new evidence about the *mechanism*, which this is not.

## 6. Reported against this finding

- The `cv_ratio` reconstruction from class TOTALS (0.504→0.472, 0.537→0.477,
  0.639→0.403) differs from the authoritative per-plant D-1 rows
  (0.521→0.488, 0.554→0.492, 0.616→0.387) because D-1 pairs bench keys and so
  covers only CAMPD-metered plants. **The deltas agree**, which is what §2–§3
  rest on, but the two are not the same statistic and the artifact carries both.
- The flat/shape-bearing split uses a **2 MW** std threshold. It is a
  measurement convenience, not a derived constant; it is an order of magnitude
  under the smallest shape-bearing band observed (`econ*` at 10–140 MW) and an
  order above float noise, and no cell sits near it (measured flat bands read
  0.35–1.63 MW; the nearest shape-bearing band is `peak` at 2.8 MW).
- **2025 COAL_PRB was already FAILing in the predecessor** (0.388) and is
  unmoved (0.389). Only three of the keeper's four FAILs are new, exactly as the
  miso-230 assessment states.
- COAL_LIGNITE 2025 is the one cell where `profile_r` falls (0.919 → 0.915);
  it passes both gates.

## 7. Governance

Rule 1 `[R-STRUCT]`: the drag is not judged by this residual and is not
reverted — §3 shows it doing the structurally correct thing. Rule 15
`[R-DASHBOARD]`: no run was produced, so there is nothing to register; keeper
retention unchanged. Rule 19: not engaged (§3). Rule 21 `[R-DOF]`: no parameter
added, ledger stays 41/2. Rule 22: 2023–2025 only, no held-out year touched.
Rule 28(a): the target ISO's adjudicated cells were checked **before** any
successor was considered, and none is re-tested (§5). Rule 28(b): **no
mechanism was tested**, so no cell verdict changes; this finding is cited from
the `netload_drag_floors` cell as reported evidence against the promoted keeper.
Rule 29 `[R-SCREEN]`: this is a phase-0 measurement and **no LP was spent**.
