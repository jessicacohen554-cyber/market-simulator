# ADDENDUM A1 (nyiso-249) — G-3: the form's WINDOW must reach the C3c deficit, and that is pre-registered here

**Added to `docs/PRECOMMIT-nyiso249-upper-tail-offer-dispersion-2026-09-20.md` (pushed `f8046c19`)
BEFORE the gate is run.** Zero LP. Nothing below has been measured yet.

## Why this gate was missing, and why it is added now

The PRECOMMIT's duty-(f) prediction (§6) rests on a premise it never stated, let alone tested:
**the form fires only in the measured book's TIGHT window, so it can only lift a price in an hour
that window contains.** Two instruments run since the PRECOMMIT went in make that premise
doubtful enough to gate:

1. **`nyiso242_tail_reachability` re-run on the current keeper.** In 2022's 91 missed hours the
   model still holds **4,689 MW idle below $300** (32.1 % of available); 2023 winter holds 6,712 MW,
   2024 holds 3,038 MW. **2025 is the only year that is close** — 991 MW idle (5.4 %), and 898 MW
   of that in summer.
2. **The lane's own carried DO-NOT-REDO:** *"2025 SUMMER's 31 missed hours are made by real-time
   shortage pricing, not an energy offer; do not fold either in."* 31 of 2025's 39 missed hours
   are therefore **out of scope by instruction** — which strips the year that looked most
   reachable.

Those two together say the PRECOMMIT §6 prediction (2022 ≥ 25 h, 2025 ≥ 8 h) may be
**unreachable by construction**, and it is better to find that out at zero LP than after four
shards.

## The gate

`scripts/probes/nyiso249_window_tail_overlap.py`, on nyiso-248's corrected **daily** coordinate,
using the **C3c gate's own two quantities** (`missed_mask`: actual RT hub > $300 **and** the
model's max zonal dual ≤ $300).

| quantity | definition | role |
|---|---|---|
| **COVERAGE** | share of that year's **missed** hours falling **inside** the tight window | a hard **CEILING** on how many hours the form can possibly fix |
| **EXPOSURE** | share of **tight** hours whose actual RT price is **below** $300 | hours where the form lifts offers with no tail to find — any price it creates there is a **false positive** costing C3a / C3b |

## THE BAR, FIXED HERE, BEFORE THE NUMBERS

> **The form is a C3c route only if at least TWO of the four years put ≥ 25 % of their missed
> hours inside the tight window.**

25 % and two years are chosen as round values ex ante and are **never swept**. Rationale for the
shape rather than the level: a ceiling below a quarter in three or more years means the window and
the deficit are substantially **different hour sets**, and a mechanism that fires where the
deficit is not cannot be the mechanism that closes it.

**EXPOSURE is REPORTED, never gating.** This probe cannot know whether a lifted offer becomes the
marginal one — only the LP decides that. Reporting it stops a favourable coverage number from
being read as a free lunch.

## WHAT EACH OUTCOME MEANS — fixed here, so the number cannot choose the conclusion

* **G-3 PASSES** → §6's prediction stands as written and the lane proceeds to the form, subject to
  G-2 (§2.3) still returning "conduct".
* **G-3 FAILS** → **the measured object is not a C3c mechanism**, whatever G-2 says about whether
  it is real. The lane then says so plainly, reports the object's magnitude and its window, routes
  C3c to a successor that can reach the deficit hours, and **does not spend four shards** proving a
  prediction already falsified at zero cost. Rule 1 `[R-STRUCT]`: a structurally-faithful
  mechanism is never rejected because the residual did not move — but a mechanism proposed **as**
  the route to a named residual, whose own window cannot reach that residual, has had its stated
  purpose falsified, and saying so is not the same as rejecting it on fit.

A G-3 failure does **not** delete the object. It re-files it: still measured, still real if G-2
says so, still a candidate on its own structural merits — but no longer this lane's C3c answer,
and never quoted as one.
