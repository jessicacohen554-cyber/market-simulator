# FINDING — nyiso-231: **NYISO's keeper was not solved on the repository's pinned dependency set.** 1 of 7 designated keepers is off-pin, it is this lane's, and the standing handoff note about dependency drift is wrong on all three of its clauses

**Session** nyiso-231 · **ISO** NYISO · **Date** 2026-09-13 · **ZERO LP for this finding**
(every number is read from committed `meta.json` files and `requirements.txt`).
Discovered while re-screening `gas_offer_margin_zonal_anchor_vintage`: shard A of this lane stopped
and reported a package mismatch against its control. It was right, and my own handoff notes were
wrong.

---

## 1. What the standing note says, and why each clause is false

The nyiso-231 handoff carried forward, as a program-level open item:

> *"Dependency drift remains FILED, NOT FIXED: every runtime dep is floor-pinned and meta.json
> records no package set, so no bundle records which HiGHS it solved on. Program-level."*

| clause | status | evidence |
|---|---|---|
| "every runtime dep is **floor-pinned**" | **FALSE** | `requirements.txt` is EXACTLY pinned: `highspy==1.14.0`, `pandas==3.0.3`, `pyarrow==24.0.0`, `pydantic==2.13.4`, `numpy==2.4.6`, `scipy==1.17.1`. `highspy==1.14.0` has been the pin across many commits. |
| "meta.json **records no package set**" | **FALSE** | Every one of the **41** committed bundles carries `environment.packages` AND a top-level `highspy_version`. Zero bundles lack it. |
| "**no bundle records which HiGHS** it solved on" | **FALSE** | All 41 do. Distribution: **36 × 1.14.0, 5 × 1.15.1**. |

**Headline, after §2b measured it:** the record is wrong in 5 bundles; **the results are not**. The
actionable residue is one mechanical check, not a re-solve.

The note is retired and replaced by §2, which is a smaller, sharper and *actionable* problem.

## 2. The real finding: 5 of 41 bundles were solved OFF-PIN, and one of them is a designated keeper

| solved | ISO | bundle | recorded vs pinned |
|---|---|---|---|
| 2026-08-25 | ERCOT | `ercot234_eastex_identity` | highspy 1.15.1≠1.14.0, pandas 3.0.5≠3.0.3, pyarrow 25.0.1≠24.0.0 |
| 2026-08-25 | ERCOT | `ercot236_k33_clip` | same three |
| 2026-08-25 | ERCOT | `ercot248_two_config_keeper` | same three |
| 2026-09-12 | **NYISO** | **`nyiso229_arm_y2022`** | those three **+ pydantic 2.13.5≠2.13.4** |
| 2026-09-12 | **NYISO** | **`nyiso229_hourgrain_span`** | those three **+ pydantic 2.13.5≠2.13.4** |

**Cross-referenced against every ISO's keeper shard — the blast radius is ONE keeper, and it is
NYISO's:**

* **NYISO `2026-09-12-nyiso229-hourgrain-span` (the designated keeper) is OFF-PIN**, and so is
  `2026-09-12-nyiso229-arm-y2022`, the 2022 touchpoint folded to it. **Both** of NYISO's registered
  runs, i.e. **all four** of NYISO's registered years, rest on a package set this repository does not
  pin.
* The three ERCOT bundles are **not** the ERCOT keeper (`ercot265_receipts_five_year`, on-pin at
  1.14.0). They are retained non-keeper bundles, so ERCOT's determination does not rest on them. Left
  for ERCOT's lane to dispose of; **no ERCOT file was touched** (rule 28: a lane edits only its own
  ISO's shard).
* CAISO, MISO, NEISO, PJM and SPP keepers are all on-pin.

**What it means — and §2b MEASURES it, which overturns the sentence this paragraph originally
carried.** I first wrote here that "the NYISO keeper is not reproducible at HEAD … a replay at
HEAD's pins is not a replay, it is a different solve." **That was a prediction, and it is wrong.**
§2b measured it: the numbers are reproducible on-pin, exactly. What survives is narrower and true —
the keeper's *environment record* does not match the repo's pins, which is a bookkeeping defect
worth a mechanical check, not a reproducibility defect in its results.

## 2b. THE MEASUREMENT: the solver-version effect on NYISO 2022 is EXACTLY ZERO

`results/calibration/nyiso231_ctl_y2022` — the 2022 control recipe re-solved ON-PIN (highspy
1.14.0, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4) at code SHA `0acedb7e`, against the committed
OFF-PIN control `nyiso229_arm_y2022` (1.15.1 / 3.0.5 / 25.0.1 / 2.13.5). Same recipe, same year,
same code.

| | on-pin 1.14.0 | off-pin 1.15.1 | delta |
|---|---:|---:|---:|
| load-weighted LMP $/MWh | 67.657293 | 67.657293 | **+0.000000** |
| simple mean price $/MWh | 64.545842 | 64.545842 | **+0.000000** |
| served TWh | 152.681670 | 152.681670 | **+0.000000** |
| mean reserve price $/MWh | 0.346557 | 0.346557 | **+0.000000** |
| hours > $300 | 4 | 4 | **0** |

* **All 52,560 hourly ZONAL prices identical to 1e-9** — 100.0000 %, max &#124;Δ&#124; 0.0000.
  Prices are the LP's duals (rule 4 `[R-DUALS]`), so this is the strictest test available and it is
  the one the degeneracy concern was about.
* **All 6,648,840 unit-hours identical to 1e-9 in `mw`, `mc` AND `cap_mw`** — max &#124;Δ&#124;
  0.0000000000 on each.
* **Every one of the 16 class energies identical to 10 decimal places**, max &#124;Δ&#124;
  0.0000000000 TWh.

**Three things this settles.**

1. **The degeneracy worry does not bite here.** The concern was sound in principle — a degenerate
   LP's optimal basis, and hence its duals, need not be version-stable — and it is measured inert
   for this model on this year. HiGHS 1.14.0 and 1.15.1 return the same basis.
2. **Rule 29(b) form 4 is VINDICATED, not broken.** The committed keeper bundle is a valid control
   for this lane despite the package mismatch. The G-DRIFT gap named in §3 is real as a matter of
   specification — it audits code, not environment — but it is **empty in practice here**, and
   nobody should spend a control solve on this question again for NYISO without new evidence.
3. **nyiso-230's +5.470 $/MWh was NOT contaminated.** Its arm(1.14.0) − control(1.15.1) is two
   deltas only in form; the second is exactly zero, so the difference is the mechanism's, as that
   session reported it.

**What it does NOT establish.** One ISO, one year, one version pair. It is not a general claim that
HiGHS versions never move this model's duals, and a future version bump earns the same measurement
rather than a citation of this one.

## 3. Why it matters to rule 29(b) specifically, and what it does NOT say

Rule 29(b) `[R-SCREEN]` makes the incumbent keeper's **committed bundle** the control (form 4), and
validates that choice with **G-DRIFT** — a `git diff` of the solve path classifying every changed
hunk INERT or LIVE. **G-DRIFT audits CODE. It does not audit the ENVIRONMENT.** So form 4 silently
carries an assumption nobody checks: that the arm and the committed control solved on the same
package set. Here they did not, and the difference lands on the LP solver — whose duals **are** the
prices (rule 4 `[R-DUALS]`), in a model that ships an explicit ε tiebreaker (rule 9 `[R-EPSILON]`)
precisely because the LP is degenerate. A degenerate LP's primal objective is stable across solver
versions; its chosen optimal **basis**, and therefore its duals, need not be.

**nyiso-230 differenced an ON-PIN arm against an OFF-PIN control and nobody noticed.** Its arm
`nyiso230_arm_y2022` records highspy **1.14.0**; its control `nyiso229_arm_y2022` records **1.15.1**.
Its reported +5.470 $/MWh is therefore arm(1.14.0) − control(1.15.1) — two deltas, not one.

**What this does NOT establish.** It does **not** show the solver delta is material. That is
unmeasured, by anyone, and it cannot be measured at zero LP. The one piece of free evidence is
weak-but-real and points toward "small": across **2.1 million non-gas unit-hours**, `mc` is
**bit-identical** between the 1.14.0 arm and the 1.15.1 control (hydro 0.000000 over 1.38 M rows;
the unlabelled group 0.000000 over 718 k) — but `mc` is an LP *input*, so that constrains input
construction, not the duals. **No claim is made either way here.**

## 4. What this session did about it

**Shard C: the 2022 control recipe re-solved ON-PIN** (`results/calibration/nyiso231_ctl_y2022`,
highspy 1.14.0), concurrently with the on-pin arm — two simultaneous per-plant multi-zone
invocations, which is exactly rule 12 `[R-PARALLEL]`'s cap.

It earns its LP under rule 29(b): an LP-solver version change on the solve path is **LIVE** by any
honest reading, and rule 29(b) says a LIVE delta is the one thing that earns a control solve. And it
is not a detour — it buys **two** things one solve cannot otherwise get:

1. **A single-delta A/B.** arm(1.14.0) − control(1.14.0) isolates the anchor field, which is what a
   screen is for.
2. **The first measurement of the solver-version effect**, as control(1.14.0) − control(1.15.1) on
   an otherwise byte-identical recipe. That number is what tells the program whether §2 is a
   bookkeeping repair or a real one — and whether a span arm may be differenced against the
   committed keeper at all for 2023/2024/2025, where the same contamination applies.

## 5. Recommended disposition — the owner's call, with the costs stated

The lane does **not** act on this beyond §4. Two routes, and they are not equivalent:

* **(i) Re-pin `requirements.txt` up to the keeper's recorded set** (highspy 1.15.1, pandas 3.0.5,
  pyarrow 25.0.1, pydantic 2.13.5). Cost: zero LP. Makes the NYISO keeper reproducible immediately
  and the three off-pin ERCOT bundles too. Risk: it moves the solver for **all seven** ISOs, so
  every other keeper — all on-pin at 1.14.0 today — becomes the off-pin one, inverting the problem
  onto six ISOs instead of fixing it for one. **Not recommended.**
* **(ii) Keep the 1.14.0 pins and let NYISO's next keeper land on them.** Cost: **zero**, now that
  §2b has measured the numbers to be identical either way. If this lane's span is promoted it will
  be solved on-pin and the record corrects itself; if it is not, the incumbent keeper's numbers are
  demonstrably the same numbers the pins produce, so nothing is owed. **Recommended.**
  *(This clause originally argued the promotion would "repair a reproducibility defect" and counted
  that as a benefit of the span. §2b removes that argument: there is no defect in the results to
  repair, only in the record. The span must stand on the mechanism alone.)*

**A third item, cheap and worth doing whichever route wins:** nothing in the repo compares a
bundle's recorded `environment.packages` against `requirements.txt`. The audit in §2 is nine lines of
Python and would have caught this on the day it happened. A check in `audit_keepers.py` — "every
designated keeper's recorded package set matches the pins" — is the durable fix, and it belongs to
whoever owns that script rather than to this lane.

## 6. RULES

13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — the defect is that a keeper cannot be reproduced from the
repo's own inputs; §5(ii) prefers the accurate route over the convenient one. 19 `[R-ONE-MECH]` — the
solver-version question is kept separate from the anchor mechanism rather than entangled with it.
21 `[R-DOF]` / 24 `[R-REGISTRY]` — a bundle that records an environment it did not solve on is the
same class of defect as one that records an anchor it did not price against, which is the other half
of this session. 25 `[R-ISO-SCOPE]` — the ERCOT bundles are reported, not touched. 28
`[R-MECH-MATRIX]` — no mechanism verdict rests on this. 29 `[R-SCREEN]` (b) — the G-DRIFT gap is
named, and the control solve is justified by the LIVE delta rather than by a heuristic.
31 `[R-RETAIN]` — nothing deleted. 32 `[R-SHARD]` — the parent ran no LP.
