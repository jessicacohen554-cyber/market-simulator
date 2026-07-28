# FINDING — pjm-135: **the star-node import is real, the BAND is 1.7–1.9× too wide, and the per-border decomposition that chartered this session is a degenerate artifact.** `PJM_external` clears at the identical dual to every PJM zone in **100.00 % of hours** (max |Δ| = **0.0000 $/MWh**), so no re-attribution can bind. What *is* measurable and non-degenerate: the model's own net interchange is **−28.9 / −21.9 / −25.8 TWh** against a measured **−40.0 / −32.8 / −32.9** — the star node supplies PJM with **7.1–11.1 TWh/yr the real seam did not** — and **nothing in the model constrains it.**

**All four measurements were run; no LP was solved for them.** Probes:
`scripts/probes/_pjm135_star_node_import.py` (M1/M2/M3),
`scripts/probes/_pjm135_star_node_net_position.py` (M1b/M4). Machine output:
`results/probes/pjm135_star_node_import.json`,
`results/probes/pjm135_star_node_net_position.json`. Every input is
already-committed data (the `pjm134_control_A` bundle's `hourly/` sidecars, PJM's
published tie-line file `PJM_<year>_import_export_act_sch_interchange.csv`, and
the model's own envelope code).

---

## §0 — the verdict in one table

| test | question | result | fires? |
|---|---|---|---|
| **M1** border attribution | does the tie→zone map hand Dominion an import band it does not physically have? | the map is **complete** (all 22 ties matched, no fallback) and **geographically sound** — Dominion genuinely net-imports **1,329/1,395/1,288 MW = 11.6/12.2/11.3 TWh**, in 86–93 % of hours. But the band it is given is **2,268/2,485/2,471 MW = 19.9/21.8/21.7 TWh — 1.71/1.78/1.92×** the measured net | **PARTLY — not the address, the SIZE** |
| **M2** shape | is the flow a capability envelope used as an energy schedule? | the band is a **(month × hod) p95 climatology** — 281–286 distinct values over 8,760 h, CV **0.19–0.35** against a measured **0.56–0.80**, sitting above the measured flow in **93.4 %** of hours *by construction*. R² vs the measured hourly import is **negative every year** (−1.04/−1.19/−0.43) | **YES** |
| **M3** degeneracy guard | is any of this a physical statement? | `PJM_external` is price-tied to **every** PJM zone in **100.00 %** of hours, all three years, **max \|Δ\| = 0.0000 $/MWh** (EMAAC alone ever separates, 4.0/2.3/2.9 %) | **YES — and it is binding on the charter** |
| **M4** net position | what *is* non-degenerate, and is it right? | the `import` class **is** the LP's net interchange: **−28.89/−21.86/−25.80 TWh** vs a measured **−39.98/−32.83/−32.93**. Hourly R² **negative** (−0.015/−0.220/−0.042), corr +0.57/+0.42/+0.40; the model sits above the measured net in **74.2/73.1/61.4 %** of hours | **YES — the real defect** |

---

## §1 — M1: the attribution is sound; the band is not

`eia930/envelopes.py::_PJM_TIE_ZONE` maps each of PJM's tie lines to the model
border zone it interconnects. It is labelled *"Tier 3 (calibration) — approximate
pending PJM's authoritative tie-to-zone assignment"*, which made it the session's
prime suspect. **It survives the test.** All 22 tie names in the file match a map
key in every year, so `_PJM_TIE_ZONE_DEFAULT` never fires and nothing is silently
dumped on ComEd. Dominion's four are `TVA`, `CPLE`, `CPLW`, `DUK` — all
genuinely Carolinas/TVA-facing.

And Dominion **really is** a large, persistent net importer on its own ties:

| PJM_Dominion border | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured net import, mean MW | 1,329 | 1,395 | 1,288 |
| measured net import, TWh | **+11.64** | **+12.22** | **+11.29** |
| hours importing | 93.4 % | 90.7 % | 85.8 % |
| **model import band (p95)**, mean MW | **2,268** | **2,485** | **2,471** |
| band, TWh if ridden | 19.86 | 21.77 | 21.65 |
| **band / measured net** | **1.71×** | **1.78×** | **1.92×** |

So the charter's framing — *"an attribution that hands Dominion a ~2.3 GW
continuous import band it does not physically have is the answer"* — is **half
right and half wrong, and the wrong half matters**: the import exists, at roughly
1.3 GW. What does not exist is its **size**. The arm-A flow of 19.9 TWh (2025) is
**+8.6 TWh above the measured 11.3** — **71 % of Dominion's entire 12.1 TWh
fossil deficit**, from one mechanism.

**Why the band is 1.7–1.9× the mean, mechanically.** `pjm_zonal_interchange_envelope`
splits each border's signed measured flow into an import side and an export side
and takes the p95 of **each, independently**, per (month × hod) bucket. A p95 of
a distribution whose mean is 1.3 GW is ~2.4 GW; used as a *ceiling* the LP can
sit at in every hour, it delivers the 95th percentile as though it were the mean.

**Reported, not fixed here (§7 hands it over):** `_PJM_TIE_ZONE` puts the **whole**
TVA tie — Dominion's single largest attributed import (+6.21/+5.40 TWh) — on
Dominion, while `INTERFACE_NEIGHBORS` splits TVA across `PJM_AEP_Ohio` **and**
`PJM_Dominion`. Two constructs built on the same seam disagree. It conserves the
ISO total, so it cannot cause the net-position defect below, but it is an
internal inconsistency and it is not this session's delta.

## §2 — M1b: five marginal percentiles are summed as though they were a joint one

The per-border error compounds into an aggregate error that has a name in this
codebase: it is the **AP-South misalignment one level up** — a limit that belongs
to an aggregate, applied element by element.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **sum of the five marginal p95 import bands** | **4,235 MW** | **5,140** | **5,358** |
| **joint p95 of the simultaneous total** | **3,309 MW** | **3,855** | **3,996** |
| gap | **925 MW** | **1,285** | **1,362** |
| gap, TWh/yr | **+8.11** | **+11.26** | **+11.93** |
| ratio | 1.28× | 1.33× | 1.34× |
| measured simultaneous import, mean | 2,045 MW | 2,454 | 2,435 |

The per-neighbor bands (`inject_pjm_seam_flow_limit`) compound it further, because
`INTERFACE_NEIGHBORS` border zones **overlap**: `PJM_Dominion` is counted **twice**
(Carolinas + TVA) and `PJM_AEP_Ohio` **three times** (MISO + TVA + LGEE), lifting
the seam-band ceiling to **6,506 / 7,649 / 8,015 MW**.

## §3 — M2: a capability envelope carrying an energy schedule

The band is a 288-cell (month × hour-of-day) table tiled over the year — 281–286
distinct values across 8,760 hours. Against the measured hourly import at the
same border:

| PJM_Dominion | 2023 | 2024 | 2025 |
|---|---|---|---|
| band R² vs measured hourly import | **−1.04** | **−1.19** | **−0.43** |
| *best possible* month×hod table (bucket **mean**) R² | +0.41 | +0.37 | +0.59 |
| band CV / measured CV | 0.21 / 0.56 | 0.19 / 0.58 | 0.35 / 0.80 |
| hours the band sits **above** the measured flow | **93.4 %** | 93.4 % | 93.4 % |

Two separate facts. First, **a month×hod climatology can carry at most 37–59 %**
of the measured hourly variation — that is the ceiling of the representation
itself. Second, **the p95 version carries *negative* explanatory power**: it is a
worse predictor of the measured flow than a constant, because it is
systematically ~1.7× too high. The 93.4 % figure is not a coincidence — it is the
definition of a 95th percentile, and it means that an LP which rides the band
over-delivers against the real schedule in essentially every hour.

## §4 — M3: the number that chartered this session is a vertex artifact

`FINDING-pjm134` §7 decomposed Dominion's supply from `flows.parquet` and handed
pjm-135 the largest single path: `PJM_external → PJM_Dominion`, +2,266 MW /
+19.9 TWh/yr. The session charter's own M3 instruction — *"before believing any
flow number, re-check whether the binding link carries a nonzero dual"* — is the
one that fires hardest.

**Arm A's P1 duals, `PJM_external` vs every PJM zone:**

| year | zones tied to the star node in 100.00 % of hours | max \|Δ\| | the exception |
|---|---|---|---|
| 2023 | ComEd, AEP_Ohio, ATSI, West_APS, Central_PA, **Dominion**, SWMAAC | **0.0000 $/MWh** | EMAAC separates in 3.98 % |
| 2024 | AEP_Ohio, ATSI, West_APS, Central_PA, **Dominion**, SWMAAC (ComEd 99.81 %) | **0.0000** | EMAAC 2.34 % |
| 2025 | AEP_Ohio, ATSI, West_APS, Central_PA, **Dominion**, SWMAAC (ComEd 99.67 %) | **0.0000** | EMAAC 2.92 % |

The star-node link into Dominion **never carries a nonzero shadow price in any
hour of any year.** The LP is therefore indifferent to how the external injection
splits across the five border links, and the simplex's choice of 19.9 TWh into
Dominion is an arbitrary vertex on a degenerate face — exactly the caveat that
also applies to pjm-134's measured SWMAAC↔Dominion pinning (bound in 80.1 % of
hours at a price difference of exactly 0.0000).

**Consequence, and it is the load-bearing one:** any correction that
re-attributes the *border* share is provably re-routable. Tighten Dominion's
band and the LP imports at ATSI (band 2,346 MW against a measured net of 643) or
ComEd and rails it back at zero cost. This is the AP-South failure mode, and
pjm-134 §8 already forbids re-running it. **The per-border lever the charter
proposed is dead on arrival, and this finding does not pursue it.**

## §5 — M4: what survives the degeneracy, and it is wrong

The `import` class in the committed `class_hourly` sidecars is the star node's
signed pergen output. `PJM_external` carries **zero demand**, so its energy
balance makes that quantity **exactly** `Σ_z Flow(PJM_external → z)` — the LP's
own net interchange. It is an aggregate, so the degeneracy of §4 does not touch
it.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **model net interchange** | **−28.89 TWh** | **−21.86** | **−25.80** |
| **measured net interchange** | **−39.98 TWh** | **−32.83** | **−32.93** |
| error (model too import-heavy) | **+11.09** | **+10.97** | **+7.13** |
| hourly R² | −0.015 | −0.220 | −0.042 |
| hourly correlation | +0.569 | +0.423 | +0.402 |
| hours model above measured net | 74.2 % | 73.1 % | 61.4 % |
| hours model above the measured **p95 envelope** | **23.48 %** | **21.22 %** | **18.56 %** |
| hours model above the bucket **maximum ever observed** | **9.34 %** | **11.72 %** | **10.71 %** |

Two things stand out. The hourly R² is **negative**, so the model's net
interchange is a worse description of PJM's actual net position than PJM's own
annual mean would be. And in **~10 % of hours the model is more import-heavy than
PJM has ever been in that (month, hour-of-day) bucket** — not merely above p95,
above the observed maximum. Those hours are unambiguously outside the measurement.

**And nothing in the model constrains this.** The star node carries three
mechanisms — `build_pjm_external_flow_groups` (per-link signed envelope),
`inject_pjm_seam_flow_limit` / `_export_limit` (per-neighbor bands),
`pjm_seam_measured_ladder` (measured band prices). Every one of them is
**marginal**: per border, per direction, per neighbor. **None of them says
anything about the total.**

## §6 — the delta this charters

A market model with no statement about its own net interchange position is
structurally incomplete. The correction is the construction this codebase has
already built, validated and shipped **twice** — a measured aggregate applied to
the aggregate rather than element by element — carried from the internal
flowgates (`pjm_east_interface_cut`, `pjm_apsouth_interface_cut`, shared core
`_build_joint_interface_cut`) to the external seam:

```
Σ_z Flow(PJM_external -> z)   <=   P_p95( measured net import | month(t), hod(t) )
```

Same tie-line file, same existing `PJM_EXTERNAL_FLOW_PERCENTILE = 95.0`, same
(month × hour-of-day) bucketing the per-border envelope already uses. **Zero
fitted scalars** (rule 24 `[R-DOF]`). One-sided, so net export is never bounded.
Rule 19 `[R-ONE-MECH]`: it **replaces** the sum-of-marginals ceiling on the
aggregate question — the joint cap dominates, and the per-border groups keep the
*locational* bound while this row owns the *total*.

It is chartered **because it is structurally correct, not because it is predicted
to close the Dominion residual** (rule 1 `[R-STRUCT]`). The prereg pre-computes,
from arm A's own committed series, that it removes only **1.54/1.80/1.73 TWh** —
14/16/24 % of the net-position error, and ~13 % of Dominion's deficit at
best — and §4 guarantees the displaced energy is replaced wherever the
copper-plate finds it cheapest. **INERT on the Dominion defect is the expected,
pre-registered, publishable outcome.**

Gates, kills, the no-feedback ceiling and the named principal risk (K2 load
shedding: the cap binds in **93.2/92.1/96.6 %** of the top-1 % load hours,
clipping 1,428/1,487/2,334 MW there) are in
`PREREG-pjm135-star-node-net-position-cut-2026-07-28.md`, committed before either
arm solved.

## §7 — DO-NOT-REDO (binding)

- **Do not propose a per-border re-attribution of the PJM star node.** §4
  measures the star node price-tied to every zone in 100.00 % of hours at
  max |Δ| = 0.0000 $/MWh; the border share is a degenerate vertex choice and any
  such delta is re-routed. This is the AP-South result (pjm-134 §8) generalised,
  and it is now measured directly rather than inferred.
- **Do not re-litigate `_PJM_TIE_ZONE`'s completeness or geography.** All 22 ties
  match, the default never fires, Dominion's four are correctly Carolinas/TVA.
  The band's **size** is the defect, not its address.
- **Do not quote "external → Dominion = 19.9 TWh" as a physical quantity.** It is
  an arbitrary vertex on a zero-dual face. The non-degenerate aggregate is the
  net interchange (§5), and that is what any future delta must be scored on.
- **Do not sweep `PJM_EXTERNAL_FLOW_PERCENTILE`, `pjm_seam_flow_percentile` or
  any percentile in this family** in response to any result here (PREREG §4
  no-feedback ceiling, binding on successors).
- Carried forward unchanged: `FINDING-pjm134` §5/§8 in full.

**Handover leads, stated but NOT built here** (ASK-pjm134 §5 discipline):

1. **The TVA border split** (§1): `_PJM_TIE_ZONE` assigns the whole TVA tie to
   Dominion while `INTERFACE_NEIGHBORS` splits it AEP_Ohio/Dominion. Conserves
   the ISO total, so it cannot move the net position — an internal-consistency
   charter, not a defect charter.
2. **PJM CC_CHP is a live C1 row running +42 %** — model 8.654 TWh vs a
   grid-delivered actual of 6.115 (2023). It passes C1 only because the ±8 TWh
   absolute band is generous for a small class, and it is why the Run Explorer's
   Generation-mix tab (which folds CHP into the parent via `CHP_MERGE`) reads
   CC Regular at −5.56 TWh while the C1 gate scores the unmerged CC_REGULAR at
   **−8.10 TWh against a ±8.00 TWh band** — the single failing C1 row in the
   whole PJM lineage, missed by **0.10 TWh**. Closing the CC_CHP over-run is the
   cheapest identified route to a C1 pass and is **not** an offer-curve tune.
   (Surfaced this session in answer to an owner question; not in scope here.)

---

## §8 — the A/B result

*(Written after both arms solved; see `results/probes/pjm135_netpos_ab.json`.)*

<!-- PENDING: arms pjm135_control_A / pjm135_netpos_B -->
