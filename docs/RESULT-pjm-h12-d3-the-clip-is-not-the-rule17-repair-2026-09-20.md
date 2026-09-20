# RESULT — pjm-h12 card D-3: the commitment-feasibility clip is REJECTED for PJM. It does not repair the rule-17 defect it was justified by, and the causal chain behind it is refuted 0/6 (2026-09-20)

**Session:** pjm-h12 · **Branch:** `claude/pjm-h12-midcurve-seam-ar8wcb` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)) — six shards, one year each (rule 36 `[R-YEAR-ISOLATION]` (a)), each
solving ARM + CONTROL at pinned SHA `65ab6205c40a3d5703f084bf747f2b132eee5c28`.
**CHARTER:** `docs/handoffs/PRECOMMIT-pjm-h12-2026-09-20.md` — **every gate below was fixed there
before any solve, and none was re-read or adjusted after a number landed.**
**KEEPER UNCHANGED:** `2026-09-19-pjm-h11-c1seam-span` stands. Nothing registered, nothing pruned.

---

## 1. Verdict

**NOT PROMOTED. The PJM cell for `mustrun_commitment_feasibility_clip` moves `U` → `R`.**

The arm was chartered on one claim: that it is *"promotable on rule 17 `[R-FLOOR-WINDOW]` alone"*
because the PJM keeper's committed D-4 fails on `cc_mustrun_per_plant`. **That claim is false, and
the gate written to test it is the gate that caught it.** G6 fails. The carve-out does not apply.

| gate | bar | result |
|---|---|---|
| **G1** — the arm fires | > 0 infeasible plant-hours, every year | **PASS** — 106.7k–114.3k plant-hours, 65–66 of 69 plant-groups infeasible |
| **G2** — census reproduces through the solver | 2023 release within ±20 % of the 6.7829 TWh offline census | **PASS** — 2025 leg matched its own census to **0.02 %** |
| **G3** — CC_REGULAR falls | ≥ 5 of 6 years | **PASS, 6/6** |
| **G4** — decile-1 price falls | ≥ 5 of 6 years | **FAIL, 0/6** — it *rises* in every year |
| **G5** — net export rises | ≥ 5 of 6 years | **FAIL** — falls in every year measured |
| **G6** — rule 17 is served | D-4 `cc_mustrun_per_plant` failures do not increase | **FAIL** — 2024 goes **8 → 9** |
| **G7** — nothing stacked | no other mechanism moves > 0.5 % | **PASS in 2024** (all < 0.5 %); 2021 flagged `reliability_floor` +27.44 %, year-specific |

## 2. The six-year table (parent-computed, zero LP, from the committed bundles)

| year | CC ctl | CC arm | **ΔCC (G3)** | decile-1 ctl | decile-1 arm | **Δprice (G4)** | D-4 cc ctl | D-4 cc arm | G6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2020 | 283.4770 | 282.7039 | **−0.7731** | 17.564 | 17.577 | **+0.0124** | 3 | 3 | PASS |
| 2021 | 289.7383 | 289.5125 | **−0.2257** | 24.032 | 24.045 | **+0.0136** | 7 | 7 | PASS |
| 2022 | 319.1278 | 318.6882 | **−0.4396** | 41.726 | 41.768 | **+0.0416** | 6 | **4** | PASS |
| 2023 | 328.4610 | 327.9951 | **−0.4659** | 21.955 | 21.963 | **+0.0088** | 5 | 5 | PASS |
| 2024 | 335.8024 | 335.5155 | **−0.2868** | 20.489 | 20.497 | **+0.0079** | 8 | **9** | **FAIL** |
| 2025 | 333.1017 | 332.9406 | **−0.1612** | 27.254 | 27.257 | **+0.0032** | 8 | 8 | PASS |

CC in TWh; price in $/MWh, load-weighted across the eight internal zones, averaged over the 876
hours of the **measured**-DA cheapest decile. D-4 counts are `cc_mustrun_per_plant` failure rows from
each leg's own committed `legitimacy_diagnostics.json`.

## 3. Why it fails, mechanically

**The arm does exactly what its construction says it does, and that turns out not to be the defect.**
It releases ~7–8.5 TWh of *asserted commitment floor* per year. CC_REGULAR responds by only
**0.16–0.77 TWh — 2 % to 11 % of the release.** The LP re-dispatches almost all of the freed capacity
economically, so the floor was rarely the binding constraint on CC in the first place.

And the small amount that *does* move goes the wrong way for the chain. 2024, measured: CC_REGULAR
−0.2868 TWh, while **COAL_BIT +0.0744, CT_PEAKER +0.0817, COAL_PRB +0.0053** absorb 0.162 TWh of it.
The freed CC energy is re-served by **dearer** units, which is why the trough price *rises* and the
seam exports *fall* — the opposite sign to §2 of the charter at both steps 4 and 5.

**G4 is the cleanest refutation in this lane's history: 0 of 6, same sign every year,** on a
prediction that was written down before any solve.

## 4. The finding that actually settles it — the populations are disjoint

The charter's rule-17 mandate rested on the keeper's D-4 failures for plants **2393** and **7153**.
Verified in the parent from the two committed 2023 bundles:

> **CONTROL** `cc_mustrun_per_plant` D-4 failures: 2393, 7153, 10308, 10751, 59220
> **ARM** `cc_mustrun_per_plant` D-4 failures: 2393, 7153, 10308, 10751, 59220

**Byte-identical. The arm repairs none of them.** The 2023 shard put it precisely: the clip *"fires on
passing plants (3797, 56807) but fails to repair target failures (2393, 7153)."*

The reason is a conflation **in the charter, which is this session's error**: the clip's test is
*available capacity < asserted commitment* (a **feasibility** question about outage derates), while
D-4's test is *floored while the plant's own meter reads zero* (a **conduct** question). Those select
different plants. The PRECOMMIT asserted they were the same population; they are not, and nothing
measured before the solve would have revealed it — the census counted *plant-hours*, never *which
plants*.

**2022 is the honest counter-example and is reported rather than buried:** there the arm takes D-4
failures **6 → 4**. It genuinely helps in one year of six. The gate's bar is no increase in any year,
and 2024 increases.

## 5. By-product: the `_basis_bridge_blackouts` LIVE hunk measured

The charter (§5) classified `data/fuel/hubs.py::_basis_bridge_blackouts` as **LIVE** since the
keeper's `basis_sha` — ungated, and it moves delivered citygate gas, the denominator of PJM's whole
offer surface. That classification is what earned the twelve control solves.

**Measured, the drift is ~nil.** The 2022 shard's control reproduces the committed keeper with
**0 of 78,840 price cells moved**. The conservative call cost six extra solves and bought certainty;
stated plainly, **form 4 would have been valid after all**, at least for 2022. A successor may treat
that hunk as INERT for PJM on this evidence rather than re-litigating it.

## 6. What is NOT concluded

- **Nothing about the mechanism on other ISOs.** Rule 25 `[R-ISO-SCOPE]` / 28(d): this is PJM's cell
  only. SPP-42's identification stands untouched, and this result fills no other ISO's cell.
- **Nothing about the underlying rule-17 defect.** Plants 2393, 7153, 10308, 10751 and 59220 still
  fail D-4 on `cc_mustrun_per_plant`, in both legs, in every year. **That defect is real and
  unrepaired** — this arm simply is not its repair. A successor needs a *conduct*-based membership
  correction (the `mustrun_plant_exclusions` lay-up route), not a feasibility clip. No PJM lay-up
  census exists yet (`campd_bridge_layup_exclusions_PJM.csv` is absent; only MISO and NYISO are
  built), so that is a data-intake step first.
- **Nothing about cards D-1 and D-2**, which closed at zero LP and are unaffected.

## 7. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

All twelve bundles are pushed and either leg of any year can back a promotion with **zero
re-solves**. Recovery by FULL sha (rule 33 `[R-SHARD-ARCHIVE]` (d) — never by branch name), also
recorded in `.gitignore`:

| year | sha | bundles |
|---|---|---|
| 2020 | `3232230b57c3c3e38fba06f763682cad48782849` | `pjm_h12_{clip,ctl}_2020` |
| 2021 | `f80efbe73a017a0827a4442c575b78ae928f9c0b` | `pjm_h12_{clip,ctl}_2021` |
| 2022 | `b578ffa75485432d4e8bc7082cccb9bf1adec0f5` | `pjm_h12_{clip,ctl}_2022` |
| 2023 | `d6f1d89d5d93d2768e44b062861e774a68417169` | `pjm_h12_{clip,ctl}_2023` |
| 2024 | `4975e114dc185a70ec3ff3f653ad8b7c1480e3d5` | `pjm_h12_{clip,ctl}_2024` |
| 2025 | `1b7484d31e42856abb5f1d01b90a1bfdfc516d87` | `pjm_h12_{clip,ctl}_2025` |

All six shard sessions are **archived** (rule 33(e)); every one was fetched, checked out and verified
(`git ls-tree` > 0 files, `dispatch/<year>_P1.parquet` present) **before** archiving, per rule 33(a) /
34(d). **Branches are left in place** — rule 33(f)(3): a branch carrying a bundle a promotion would
register stays until the owner has ruled, and rule 31 `[R-RETAIN]` forbids deleting a result before
that. `.gitignore` keeps them out of `main`; **nothing was `rm`'d.**

## 8. The promotion question (rule 31 `[R-RETAIN]`)

**This lane recommends NOT promoting**, and — unlike pjm-h11 — this is not a close call the owner
should be asked to split: the arm fails the gate written specifically to test its own justification,
and the plant-level evidence shows it does not touch the defect it was chartered against.

**The owner may still rule otherwise**, and rule 31 is explicit that a session never acts on its own
recommendation by destroying evidence. Every bundle is retained and retrievable at zero cost, so
"promote anyway" remains available at the price of one composition pass. What would be registered is
a run that moves CC_REGULAR by ≤ 0.77 TWh/yr, raises the trough price in all six years, and adds a
D-4 failure in 2024.

**Cost of this lane:** 12 solves across 6 containers, ~13 min per leg. It bought a firm `R` on a cell
that was `U`, the disjoint-population finding, and the measurement that the `_basis_bridge_blackouts`
drift is nil.
