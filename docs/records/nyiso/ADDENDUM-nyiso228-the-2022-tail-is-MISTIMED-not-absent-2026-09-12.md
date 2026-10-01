# ADDENDUM 1 to PRECOMMIT-nyiso228 — the 2022 tail is **MISTIMED, not absent**, and two claims in §1 of the PRECOMMIT are CORRECTED

**Session:** nyiso-228 · **Date:** 2026-09-12 · **ZERO LP** — every number is read or recomputed
from committed artifacts (`results/calibration/nyiso_fuelvintage_H2/hourly/`, the committed
`2026-09-09-nyiso-221-fuelvintage-tp2022` payload, `frontend/data/backcast/bench/NYISO/2022.json.gz`).

Written **after** the three shards were launched and **before** any of them returned. It changes no
shard's charter, no gate and no arm: the shards are pinned to `55cd0a6c` and every gate they carry is
stated against 2025/2023 comparators that this addendum does not touch. It is published as an
addendum rather than an edit because the PRECOMMIT is a pre-registration and the shards read it.

---

## 1. WHAT I GOT WRONG, stated plainly

The PRECOMMIT §1.2 said *"the model has NO UPPER TAIL. Its price ceiling is ~$200–315."* That was
measured on **2023–2025 only** and I generalised it to 2022 without checking. **It is false for
2022.** The committed 2022 keeper touchpoint reaches a load-weighted **$1,429.99**, sheds firm load
at VOLL in two hours, and drives `east_10min_total` to its full published **$775** (9 h, the whole
1,200 MW short) and `seny_30min_total` to its full published **$500** (12 h, 1,800 MW short).

**What SURVIVES unchanged:** the three NYCA-wide families (`nyca_30min_total`, `nyca_10min_total`,
`nyca_10min_spin`) bind in **0 hours of all FOUR years** — 2022 included. And §1.1's winter
decomposition is measured off the hourly delta series and is untouched.

## 2. THE CORRECTED FINDING, and it is STRONGER than the one it replaces

2022, model vs actual, load-weighted:

| | h>150 | h>200 | h>300 | h>500 | h>1000 | max | p99 | mean |
|---|---|---|---|---|---|---|---|---|
| **model** | 198 | 30 | **8** | 6 | 4 | 1,430 | 170 | 65.28 |
| **actual** | 543 | 260 | **101** | 22 | 9 | 2,944 | 320 | 74.75 |

**The model's eight hours above $300 ALL FALL ON ONE DAY — 31 May 2022.** The market's 101 fall in
**January 28 · February 8 · December 34** (62 % winter) and **August 15** (heat).

> **Overlap: ZERO hours. Precision 0 %. Recall 0 %.**

The model is not producing a thin version of the market's scarcity. It is producing a **different,
spurious scarcity event** and **none** of the real one. This is the same anti-correlation signature
nyiso-225 measured on the nyiso-224 cutset arm (lift 0.63×), one tier up, and it is a far stronger
statement than "the tail is too thin": **the C3c 2022 count of 8–10 h is entirely spurious**, and a
mechanism that merely thickened the tail would deepen the wrong day.

## 3. THE 31-MAY EVENT IS AN AVAILABILITY ARTIFACT, AND THE PROOF IS THE VOLL HOUR ITSELF

31 May 2022 is the **18th-busiest day of 365** (peak 27,046 MW). The model sheds **125 MW at 16h and
236 MW at 17h** at VOLL. At the **true annual peak** — 20 July, **30,505 MW**, 3.5 GW higher — it
serves load with room to spare.

The difference is availability, and it is identified per plant. Five plants dispatch **exactly zero**
all day on 31 May and run at the 20 July annual peak:

| group | plant | zone | nameplate MW | 05-31 max CF | 07-20 max CF |
|---|---|---|---|---|---|
| ST_GAS | Ravenswood | NYC | 1,828 | **0.0 %** | 67.0 % |
| ST_GAS | Bowline Point | Capital_Hudson | 1,242 | **0.0 %** | 82.0 % |
| ST_GAS | Roseton Generating Facility | Capital_Hudson | 1,242 | **0.0 %** | 38.0 % |
| CC_CHP | Empire Generating Co LLC | Capital_Hudson | 654 | **0.0 %** | 86.0 % |
| CC_CHP | Selkirk Cogen | Capital_Hudson | 446 | **0.0 %** | 34.0 % |
| | | | **5,412 MW** | | |

Class-level corroboration at the two peak hours: `ST_GAS` **1,968 MW** on 31 May against **5,987 MW**
at the annual peak — ~4 GW absent — while the model burns **1,202 MW of oil** on 31 May against
**56 MW** at the true peak, and *still* sheds load.

**Why this is PROOF of unavailability and not economics.** In an hour where the LP is shedding firm
load at VOLL, every **available** MW dispatches by construction — there is no price at which an
available unit is out-of-merit against VOLL. **5,412 MW of nameplate dispatching exactly zero in a
VOLL hour is only possible if it is unavailable.** No inference, no threshold, no tuning.

The real NYISO system was not short on 31 May 2022. This is a **shoulder-season maintenance-window
collision in the CAMPD-derived outage overlay** landing on an unusually warm late-May day.

## 4. CONSEQUENCES — declared now, before any arm returns

**(a) ARM A's honest limit.** The peak-band ×1.50 is a **price-level and amplitude** instrument. It
prices the top tranche across many hours and should move C3a, C3b and the D-A amplitude. It **cannot
fix timing**, and it will make the spurious 31-May event **more** extreme, not less. That is a cost
of the arm and it is stated here **before** the result lands, not after. It does not change the
arm — the amplitude defect is real and independent — but it bounds what a good result would mean.

**(b) The C3c 2022 number must not be read as progress in either direction.** With precision 0 %, a
count that moves from 8 to 20 hours has not necessarily produced one real scarcity hour. Any arm's
2022 C3c will be reported **with its precision and recall against the market's own 101 hours**, not
as a bare count. This is a reporting rule adopted now so no arm can be flattered by it.

**(c) A THIRD variable is identified and is NOT being launched blind.** Availability-window
**placement** — distinct from arm A's offer surface and arm B's seam — is the object that would
actually move the timing. It is **not** the family nyiso-227 closed: that census covered the
**sub-5-day** gas outage family and found it near-inert; this is a **multi-day shoulder-season
maintenance window** on five named large units. It earns its own phase 0 (which artifact places the
window — the CAMPD extract, the detector, or the layup reclassification — and whether the real units
were on outage on those dates), and it has **no registered ScenarioConfig flag today**, so an arm for
it is a code change that rule 32 forbids a shard from making. Launching a fourth shard now would be
launching one with no lever. **It is recorded as the named successor and the session will put it to
the owner rather than guess at it.**

## 5. WHAT THIS DOES NOT CHANGE

Arms A, B and C are unchanged and running. Their gates, screen years, comparators and the frozen
×1.50 are all untouched. Rule 1 `[R-STRUCT]` condition (c) still binds: the factor will not be
re-cut whatever any of this implies.
