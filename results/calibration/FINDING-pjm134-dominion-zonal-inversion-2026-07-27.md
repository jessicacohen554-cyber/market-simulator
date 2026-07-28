# FINDING — pjm-134: **C1 is REFUTED, C2 FIRES.** The model's PJM is a copper-plate — Dominion clears at its neighbours' price in **100.0 % of 26,280 hours** — while PJM's own DA congestion says the Dominion boundary separates in roughly half of them. The zonal gas basis is not merely innocent, it is measured-faithful: Dominion's gas genuinely IS $0.5–1.2/MMBtu dearer, and with no congestion to counteract it, the correct basis alone decides the allocation.

**Both ASK §4 tests were run; no LP was solved.** Probes:
`scripts/probes/_pjm134_c1_zonal_gas_basis.py`,
`scripts/probes/_pjm134_c2_dominion_interface.py`. Machine output:
`results/probes/pjm134_c1_zonal_gas_basis.json`,
`results/probes/pjm134_c2_dominion_interface.json`. Every input is
already-committed data (the `pjm121_ccbelt` bundle's `hourly/` sidecars, its
dashboard run payload, `data/raw/pjm_zonal_gas_hub.csv`,
`eia923_monthly_fuel_costs.parquet`, PJM's published hourly hub LMPs and
transfer-limit feed).

---

## §0 — the verdict in one table

| test | question | result | fires? |
|---|---|---|---|
| **C1** zonal gas basis | does the model's Dominion-vs-west gas ranking invert the measured one? | model spread is **smaller** than measured in 2023/24 and within $0.05 in 2025; **no sign inversion in any year**; Kendall τ(model rank, measured rank) = −0.32 / +0.55 / +0.91 | **NO — refuted** |
| **C2** transfer capability | do the Dominion-facing interfaces bind in the model as they do in PJM? | model: Dominion clears at the **identical** dual to all three neighbours in **100.0 %** of hours, all three years, 0/26,280 separated. Measured: PJM DA **congestion** separates DOM from AEP-DAYTON by >$1 in 59.2/49.5/62.7 % of hours, DOM dearer in **55.9/42.8/49.9 %**, mean **+$2.17/+$2.53/+$4.41** | **YES — decisively** |

---

## §1 — C1: the gas basis is right, and that is what makes C2 fatal

The keeper prices PJM gas off `pjm_zonal_gas_hub.csv` — each zone's primary-state
EIA delivered-to-electric-power series minus Henry Hub, re-centred on a
gas-capacity-weighted mean of zero. The comparator here is **EIA-923 Schedule 2
plant-level delivered gas receipts**, volume-weighted over the plants
**`build_zone_lookup("PJM")` itself places in each zone** — the same measured
quantity on the *model's own boundary* rather than the state boundary, which is
the rule-14 misalignment question asked directly.

Basis vs Henry Hub, $/MMBtu:

| year | zone | model | measured (F923, model-zone) | model − measured | receipts |
|---|---|---|---|---|---|
| 2023 | Dominion | +0.761 | **+1.153** | −0.392 | 242.6 M MMBtu, 16 plants |
| | AEP_Ohio | −0.246 | −0.078 | −0.168 | 113.3 M MMBtu, 8 plants |
| 2024 | Dominion | +0.634 | **+0.879** | −0.245 | 295.4 M MMBtu, 15 plants |
| | AEP_Ohio | +0.056 | +0.230 | −0.174 | 119.8 M MMBtu, 8 plants |
| 2025 | Dominion | +0.502 | **+0.566** | −0.064 | 305.2 M MMBtu, 15 plants |
| | AEP_Ohio | −0.192 | −0.077 | −0.115 | 99.9 M MMBtu, 5 plants |

The spread that actually sets merit order:

| Dominion − AEP_Ohio | 2023 | 2024 | 2025 |
|---|---|---|---|
| model | +1.007 | +0.578 | +0.694 |
| **measured (F923)** | **+1.231** | **+0.649** | **+0.643** |
| model overstates by | **−0.224** | **−0.071** | +0.051 |
| = on a 10.5 MMBtu/MWh CT | −$2.35/MWh | −$0.74/MWh | +$0.54/MWh |

**C1 is refuted, and not narrowly.** The model does not invert the measured
ranking — it reproduces it, and in two of three years it **understates**
Dominion's gas premium. There is no data correction to make here. (ComEd has
**zero** reporting gas plants in the F923 receipts sample in all three years, so
its measured basis is unavailable; AEP_Ohio, with 100–120 M MMBtu of receipts
against Dominion's 243–305 M, carries the comparison, and its model basis
(−0.246/+0.056/−0.192) and ComEd's (−0.108/+0.120/+0.018) sit within
$0.14/MMBtu of each other in every year, so nothing turns on the gap.)

**And this is the important half of the C1 result.** Dominion really does pay
$0.6–1.2/MMBtu more for gas than the western zones — $6–13/MWh on a peaker.
Reality clears its CTs at a **19.5 % capacity factor anyway** (ASK §2). A market
that dispatches expensive local peakers in preference to cheap remote ones is a
market where the network, not the fuel bill, is deciding — which is precisely
what C2 measures the model to have thrown away.

## §2 — C2: the model's PJM has no internal congestion at all

**Method note — a substitution, stated plainly.** ASK §4 specified a
"binding-share and flow-direction histogram … from the keeper's committed
`hourly/` sidecars". Those sidecars carry per-zone hourly prices, demand, slack
and dump, but **no flow column**: a run *does* write `flows.parquet`, but at the
bundle top level, where `.gitignore` (`results/calibration/*/*.parquet`) strips
it — so no *committed* bundle has flows, and a no-LP test on the keeper cannot
use them. (§6/§7 report the real flow histogram from this session's own arms.)
The test was therefore run on **price separation**, which for this LP is exact and
strictly stronger: every PJM link has `flow_cost = 0` and the transport
formulation is lossless, so two zones joined by an uncongested path clear at the
*same* energy-balance dual. Hence `P[Dominion,t] ≠ P[neighbour,t]` **iff** the
path between them binds at `t`, and the sign gives the direction. (A flow can
sit exactly at its bound with a zero shadow price; price separation cannot.)

**Model — the three Dominion-facing links** (AEP_Ohio→Dominion 4,050 MW
measured-hourly, West_APS→Dominion 3,000 MW static, SWMAAC→Dominion 3,500 MW
static):

| year | Dom dearer | tied | Dom cheaper | mean spread |
|---|---|---|---|---|
| 2023 | 0.0 % | **100.0 %** | 0.0 % | $0.00 |
| 2024 | 0.0 % | **100.0 %** | 0.0 % | $0.00 |
| 2025 | 0.0 % | **100.0 %** | 0.0 % | $0.00 |

Not one hour of 26,280, on any of the three links. Widening to the whole ISO:
all eight internal zones plus the import node clear at a **single identical
price in 95.5 / 97.3 / 96.2 %** of hours, and the only zone that ever separates
materially is **EMAAC** (mean +$0.44/+0.82/+1.52) — i.e. `pjm_east_interface_cut`
works, and it is the *only* internal cut in PJM that ever binds. Dominion is a
copper-plate extension of the western coal belt.

**Measured — PJM's own published hourly hub LMPs**, DOMINION HUB vs AEP-DAYTON
HUB, separation at a $1/MWh threshold:

| year | component | DOM dearer | within $1 | DOM cheaper | mean |
|---|---|---|---|---|---|
| 2023 | DA congestion | **55.9 %** | 40.8 % | 3.3 % | **+$2.17** |
| 2024 | DA congestion | **42.8 %** | 50.4 % | 6.7 % | **+$2.53** |
| 2025 | DA congestion | **49.9 %** | 37.3 % | 12.8 % | **+$4.41** |

Against ComEd it is starker still — DOM dearer on DA congestion in
**78.5 / 74.6 / 75.5 %** of hours, mean **+$5.42 / +$6.47 / +$11.50**. The
congestion component is PJM's own statement that the path bound; the model's
answer to the same question is zero in every hour of every year.

**The energy this misallocates.** Zonal fossil generation against zonal demand,
model vs EIA-923 (`volErr.zoneMon` + the keeper's own demand sidecar):

| year | Dominion Δ | AEP_Ohio Δ | ComEd Δ | ISO-wide Δ | Dominion self-supply model / actual |
|---|---|---|---|---|---|
| 2023 | **−20.0 TWh** | +5.8 | −0.2 | −20.6 | 0.27 / 0.44 |
| 2024 | **−19.8 TWh** | −0.5 | +4.6 | −24.7 | 0.34 / 0.50 |
| 2025 | **−12.1 TWh** | +9.8 | +10.3 | **+0.2** | 0.39 / 0.48 |

2025 is the cleanest read in the whole diagnosis: the ISO-wide fossil total is
**+0.2 TWh — essentially perfect** — while Dominion runs 12.1 TWh short and
AEP_Ohio + ComEd run 20.1 TWh long. The model burns the right amount of fossil
fuel in PJM and burns it in the wrong states. Dominion's fossil serves 27–39 %
of its own load in the model against 44–50 % in reality; the difference,
**1.4–2.3 GW on annual average**, is energy the LP rails in from the west that
the real grid cannot deliver.

## §3 — but the fix is NOT "the AEP/DOM number is wrong" (rule 14 misalignment, measured)

The obvious reading — loosen/tighten the crosswalked flowgate — is refuted by
the same feed. `AEP/DOM Post-Contingency`, the series
`PJM_INTERFACE_LINK_MAP` maps AEP_Ohio→Dominion to:

| year | limit p50 | transfer p50 | util p50 | util p90 | util p99 | hours ≥ 90 % |
|---|---|---|---|---|---|---|
| 2023 | 4,028 MW | 1,643 MW | 41.7 % | 62.3 % | 82.2 % | **0.4 %** |
| 2024 | 4,051 MW | 1,625 MW | 41.0 % | 64.4 % | 88.6 % | **0.8 %** |
| 2025 | 4,091 MW | 2,048 MW | 51.0 % | 75.8 % | 91.1 % | **1.4 %** |

**The real AEP/DOM flowgate is at ~41–51 % of its limit in the median hour and
is loaded past 90 % in ≤ 1.4 % of hours.** Dominion's persistent congestion
premium is therefore *not* produced by that interface, and the model already
carries its measured hourly limit. Nor is there a substitute: PJM publishes the
DOM LDA's import limit (CETL) only from delivery year 2025/26 (5,164 MW); for
2023/24 and 2024/25 it published **a lower bound only** (">989.0", ">3,231.5")
because DOM was not a separately modelled, import-constrained LDA then
(`data/raw/capacity-deliverability/pjm/README.md`, caveats). CETL is in any case
a peak-hour *capacity-emergency deliverability* quantity, not an hourly energy
transfer capability.

So: **there is no published hourly series on the Dominion zone boundary for the
scored years.** This is exactly rule 14's documented-misalignment case — the
accurate data is defined on a different boundary than our zones — and it means
the delta cannot be a swap-in of the real number.

For scale, the model's total Dominion import capability is
4,050 + 3,000 + 3,500 = **10,550 MW**, against a Dominion peak demand of
22.1/23.2/24.8 GW — 43–48 % of peak, permanently available, never binding.

## §4 — what the reconciliation actually is

`constants.py` already flags, in its own words, the one place where the reduced
network gives Dominion capability the measurement does not support:

> *"AP-South is the aggregate western→MAD 500 kV flowgate, one of several
> parallel paths this 8-zone mesh splits across West_APS→SWMAAC and
> West_APS→Dominion. It is applied ONLY to the seeded link (West_APS→SWMAAC);
> West_APS→Dominion keeps its static 3,000 MW so the total west→MAD capability
> is the reconciled measured-plus-static sum, never the single flowgate
> double-applied."*

The measured AP-South interface caps the **whole** western→Mid-Atlantic/Dominion
transfer at ~3,900 MW. The model applies it to one of the two parallel paths and
lets the other ride a 3,000 MW static, so the LP's west→MAD capability is
**AP-South(t) + 3,000 MW ≈ 6,900 MW — roughly 1.8× the published flowgate**, and
every megawatt of the excess is Dominion-facing.

The faithful reduced-network reading of a flowgate that spans two model links is
the **joint one-sided aggregate cut** — which this codebase has already built,
validated and shipped for the EASTERN interface
(`build_pjm_east_interface_cut_groups`, `pjm_east_interface_cut`), the one
mechanism §2 measures actually binding. Applying the same construction to
AP-South is a **replacement of the flagged misalignment, not a new floor stacked
on a residual** (rule 19 `[R-ONE-MECH]`), uses only already-committed measured
data, and carries **zero fitted parameters** (rule 23 `[R-DOF]`).

That delta is chartered — with its PRIMARY, its no-feedback ceiling and its
pre-registered kills — in
`PREREG-pjm134-apsouth-joint-cut-2026-07-27.md`, committed before either arm
solves.

**It is chartered because it is structurally correct, not because it is
predicted to close the residual** (rule 1 `[R-STRUCT]`). Whether the joint cut
binds often enough to move 1.4–2.3 GW of Dominion imports is exactly what the
A/B measures, and INERT is a pre-registered, publishable outcome.

## §5 — DO-NOT-REDO (binding)

- **Do not re-run C1.** The gas basis is measured-faithful on the model's own
  zone boundary, in all three years, with no sign inversion. Do not propose a
  Dominion gas-basis correction, and do not "fix" the ComEd F923 gap — ComEd has
  no reporting gas plants in the receipts sample and its model basis sits within
  $0.14/MMBtu of AEP_Ohio's, so nothing in this defect turns on it.
- **Do not re-measure the copper-plate result.** 0 of 26,280 hours of Dominion
  price separation, 95.5/97.3/96.2 % single-price ISO-wide, EMAAC the only
  internal cut that ever binds — all committed in
  `results/probes/pjm134_c2_dominion_interface.json`.
- **Do not propose re-rating AEP/DOM.** §3 measures that flowgate at 41–51 %
  median utilisation with ≤ 1.4 % of hours past 90 %; the model already carries
  its measured hourly limit. It is not the constraint that separates Dominion.
- **Do not use DOM CETL as an hourly energy cap.** Wrong construct
  (peak-hour capacity-emergency deliverability) and unpublished as a clean
  number for two of the three scored years.
- **Flows: `flows.parquet` DOES exist in a fresh bundle** (top-level, gitignored
  by `results/calibration/*/*.parquet`, so absent from every *committed* keeper —
  which is why the no-LP tests above had to use price separation). Once this
  session solved its own arms the real flow histogram became available and is
  reported in §6/§7. Correcting this file's own earlier wording: the claim was
  "the committed sidecars carry no flow column", which is true; "no run persists
  flows" would not be.
- Carried forward unchanged: ASK-pjm134 §5 (not bundled with pjm-133; no
  measured-offer-surface retry — pjm-132 moves Dominion by 0.00 TWh) and
  FINDING-pjm133 §8.

Next number: pjm-135.

---

## §6 — the A/B result: every pre-registered gate PASSES, and the delta is INERT on the defect

Arms `pjm134_control_A` / `pjm134_apsouth_B`, 2023+2024+2025 each in one
invocation (rule 16), solved sequentially (rule 12) at HEAD `b0ee3eb`. Scorer:
`scripts/probes/_pjm134_apsouth_ab.py`; machine output
`results/probes/pjm134_apsouth_ab.json`.

**Verified single-delta.** Arm A reproduces `pjm132_control_A` **byte-identically
— 0.000000000 MW on all 19 classes, every hour, all three years** (K5). The
`_build_joint_interface_cut` refactor of the EMAAC cut is therefore provably
inert, and `git diff src/market_sim/ scripts/run_calibration*.py
scripts/replay_keeper.py` between the two arms' HEADs is **empty** despite a
container restart that forced arm B to re-base — the arms share identical solve
code.

| gate (PREREG §3/§5) | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **P1** cut engages (> 0 % of hours; arm A = 0.00 %) | 0.03 % | 0.09 % | 0.62 % | **PASS** |
| **P2** Dominion is the dearer side ≥ 2/3 of separated hours | **100.0 %** | **100.0 %** | **100.0 %** | **PASS** |
| **P3** no counterflow forcing (cap ≥ 0 every hour) | ✓ | ✓ | ✓ | **PASS** |
| **K2** load shedding (slack/dump) | 0 / 0 | 0 / 0 | 0 / 0 | **PASS** |
| **K5** arm-A identity | — | — | — | **PASS (0.000000000 MW)** |

**The mechanism does exactly what it was built to do, and the misalignment it
corrects was real and large.** Arm A flows across the AP-South pair **exceed
PJM's published cap in 11.6 % / 11.7 % / 20.4 % of hours, by up to 3,000 MW**;
arm B enforces it to **0.00 %** of hours in every year, moving the joint flow by
−117 / −152 / −266 MW on average across 77–82 % of hours. That is a genuine,
zero-DOF repair of a published security limit the model was violating.

**And it does nothing whatsoever to the defect.**

| PJM_Dominion, TWh | 2023 A → B | 2024 A → B | 2025 A → B | actual |
|---|---|---|---|---|
| CT_PEAKER | 0.68 → **0.68** | 1.25 → **1.25** | 2.46 → **2.47** | 7.38 / 8.68 / 9.64 |
| CC_REGULAR | 31.76 → **31.76** | 41.10 → **41.11** | 48.33 → **48.33** | 41.70 / 49.27 / 49.23 |

Largest zonal movement anywhere in PJM: **0.01 TWh**. Dominion's total net
import *rises* by +1.9 / +1.3 / +2.7 MW-average. ISO-wide class volumes move
0.006 TWh. Price separation reaches 0.03–0.62 % of hours against a **measured
50–63 %** — two orders of magnitude short.

**Determination: INERT on the defect** — the outcome PREREG §4 pre-registered.
Per §4's no-feedback ceiling, **no scale factor, percentile or haircut may be
applied to the published AP-South series in response to this**, and none was.

## §7 — WHY it is inert, and the next charter this hands over

Capping one path in a meshed reduced network does nothing when the load pocket
is fed by parallel paths with slack. Dominion's import decomposition (arm A,
2025, from `flows.parquet`):

| path into PJM_Dominion | mean MW | TWh/yr |
|---|---|---|
| PJM_AEP_Ohio → Dominion | +3,877 | **+34.0** |
| **PJM_external → Dominion** | **+2,266** | **+19.9** |
| PJM_West_APS → Dominion | +1,080 | +9.5 |
| Dominion → PJM_SWMAAC (export) | −3,273 | −28.7 |
| **net** | **+3,951** | **+34.6** |

Two facts settle it:

1. **AP-South is not Dominion's supply route.** The West_APS path carries 9.5 of
   the 34.6 TWh. Squeezing it by ~0.3 GW is absorbed by the mesh.
2. **The external seam node feeds Dominion directly with 19.9 TWh/yr** — more
   than Dominion's entire 12.1 TWh fossil deficit — and **no internal interface
   cut can touch it.** `PJM_external → PJM_Dominion` is a star-node link
   governed by the seam/import-envelope family (`pjm_seam_flow_limit`,
   `priced_interchange`, `PJM_EXTERNAL_FLOW_PERCENTILE`), not by
   `PJM_INTERFACE_LINK_MAP`.

Add the degeneracy this session measured — links pinned at their bounds with
**exactly zero** shadow prices (SWMAAC↔Dominion sits at its 3,500 MW bound in
80.1 % of hours with a price difference of 0.0000) — and the picture is complete:
the reduced network has so much redundant Dominion-facing capability that
tightening any single internal path is re-routed at zero cost.

**Next charter (pjm-135), stated but NOT built here** (ASK-pjm134 §5 discipline):
the external star-node import into Dominion. It is the largest single
unexplained Dominion supply path, it is ~1.6× the zone's fossil deficit, and it
is governed by a *different* mechanism family than the one this session tested.
Whether PJM's measured tie-line deliverability envelope should be attributed to
border zones in a way that lets ~2.3 GW land continuously in Dominion is a
measurement question with committed data
(`PJM_<year>_import_export_act_sch_interchange.csv`), not a new mechanism.

**Solve-cost note, for whoever picks this up:** arm B ran **~2.5× slower** than
arm A (2023 P0 1,902 s vs 765 s; 2024 P0 2,308 s; whole arm 2 h 07 m vs 59 m).
The added 8,760 interface rows cut across the degenerate face, and simplex pays
for it. That cost is real and recurs on every future PJM solve — it is the main
argument against carrying a flag that moves 0.01 TWh.

## §8 — DO-NOT-REDO (added by the A/B)

- **Do not re-run this A/B, and do not re-parameterise AP-South.** The cut is
  correctly implemented, provably enforced (11.6–20.4 % → 0.00 % violations),
  directionally perfect (P2 = 100.0 %), and immaterial (≤ 0.01 TWh). PREREG §4's
  ceiling is binding: no multiplier, percentile, haircut or blend on the
  published series, ever, in response to this result.
- **Do not extend the joint-cut construction to another internal PJM interface
  expecting it to move Dominion.** §7 shows the mesh re-routes; the binding
  question is the external node, not another internal flowgate.
- **Do not re-derive the import decomposition** — §7's table is committed.
