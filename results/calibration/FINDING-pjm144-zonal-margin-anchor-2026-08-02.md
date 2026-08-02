# FINDING — pjm-144: the zone-resolved gas-offer margin anchor is DISPATCH-LIVE but PRICE-INERT at PJM — verdict `I` by the pre-registration's own rule; the keeper is unchanged

**Session:** pjm-144. **Frozen HEAD:** `05b579d` (= origin/main `a92ae97` +
this session's mechanism-registration commits). **Keeper under test — and
still the keeper:** `2026-07-31-pjm-143b-hy-level` (CALIBRATED, 9/9 target
grade, C1 16/16 all-class / 12/12 free-class, zero FAILs).
**Pre-registration:** `results/calibration/PREREG-pjm144-zonal-margin-anchor-2026-08-02.md`,
committed and pushed **before either arm solved**, including the derived
anchor table, the K6 drop, the zonal K3 construction, and the K3-fail ⇒ `I`
disposition this finding executes.
**Solves: 2** — one same-HEAD zero-delta control
(`2026-07-31-pjm-144a-control-zerodelta`, bundle
`results/calibration/pjm144_control_A`), one single-delta arm
(`2026-08-02-pjm-144b-zonal-anchor`, bundle
`results/calibration/pjm144_zonalanchor_B`), three years each, sequential
(the recipe peaks ~15.5 GB RSS; swap re-asserted per keeper note 14).
**Scorer artifact:** `results/calibration/_pjm144_zonal_anchor_ab.json`.
**Owner instruction (in-session, 3×):** *"Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates
regress that may still be a keeper."* — §6 answers it directly.

---

## §0 — Headline

nyiso-109 measured an identification-**grain** error in
`gas_offer_net_revenue_margin` — the anchor of `markup_hr × (anchor − fuel)`
is ISO-level while the solve prices each gas unit at its zone's basis — and
chartered per-ISO transfers (its §7). PJM arms `pjm_zonal_gas_basis=True` on
its keeper with the second-largest measured spread (1.483 $/MMBtu across
zones), so the same mismatch was live here. This session derived PJM's own
zone-anchor table (zero fitted parameters, the runtime applier on the
keeper's own fleet), pre-registered a two-sided A/B, and ran it.

**The result splits along exactly the line the pre-registration drew.** The
mechanism is unambiguously **live in dispatch** — the LP reallocates
0.4–1.0 TWh/yr of gas energy across classes once eastern premium zones stop
being under-marked and western discount zones stop being over-marked — but
**price-inert at every scored grain**: the maximum zonal annual-mean λ move
is **$0.034/MWh** against the pre-registered $0.10 liveness gate, the system
load-weighted move is +$0.021…+$0.030, C3c tail hours are identical, and
**every criterion status is identical between the arms** (both CALIBRATED,
9/9, zero FAILs). PJM's price-coupled zones absorb a two-sided, mean-zero
offer redistribution almost completely.

Per the prereg's pre-committed rule — *"Failing K3 is verdict `I` (inert),
not `R`"* — the matrix cell records **`I`**, the keeper is **unchanged**, and
the derived table stays registered in `constants` (the mechanism is one
`--gas-offer-margin-zonal-anchor` away for any future lane with new
evidence).

---

## §1 — The admissibility check that shaped the experiment (no LP)

### 1.1 PJM's applier convention is NOT NYISO's — and that changed the gates

`apply_pjm_zonal_gas_basis` delegates to the **capacity-weighted MEAN-ZERO**
core (`src/market_sim/data/fuel/basis/meanzero.py`): the measured per-zone
basis (each zone's primary-state EIA delivered-to-electric-power price minus
Henry Hub, `data/raw/pjm_zonal_gas_hub.csv`) has the gas-capacity-weighted
fleet mean subtracted before application, so the calibrated fleet-aggregate
level is preserved and only the cross-zonal spread opens. Consequences,
all pre-registered:

* The ISO anchor (3.3483) is the fleet **centroid**, not a reference level —
  the defect is **two-sided** (east under-marked, west over-marked), so
  nyiso-109's one-sided **K6 direction gate was DROPPED**, not copied.
* **K3 liveness was priced on the ZONAL grain** (max zone |Δλ| > $0.10),
  because a mean-zero redistribution can be live at ~zero net system effect.
* The derivation must carry **the solve's own fleet weights**: the applier
  weights by `fleet.pmax` over gas rows, so the derive gained a
  `--weights-bundle` path that rebuilds the keeper's per-year fleet no-LP
  (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`) and calls the
  RUNTIME applier on it. The removed means are **−0.1049 / +0.1689 /
  +0.2386 $/MMBtu** (2023/24/25); a synthetic unweighted fleet would have
  been wrong by up to **0.106 $/MMBtu** (2025) — larger than the 0.1
  inertness bar itself.

### 1.2 The derived table (registered in `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]`)

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 3.3483 |
|---|---|---|---|---|---|
| PJM_SWMAAC | 3.7841 | 3.6357 | 5.8786 | **4.4328** | +1.0845 |
| PJM_Dominion | 4.1211 | 3.3207 | 4.1976 | **3.8798** | +0.5315 |
| PJM_EMAAC | 3.0401 | 2.8117 | 4.6176 | **3.4898** | +0.1415 |
| PJM_ComEd | 3.2521 | 2.8067 | 3.7136 | **3.2575** | −0.0909 |
| PJM_AEP_Ohio | 3.1141 | 2.7427 | 3.5036 | **3.1201** | −0.2282 |
| PJM_ATSI | 3.1141 | 2.7427 | 3.5036 | **3.1201** | −0.2282 |
| PJM_Central_PA | 2.9281 | 2.5497 | 3.4346 | **2.9708** | −0.3775 |
| PJM_West_APS | 2.7871 | 2.5917 | 3.4696 | **2.9495** | −0.3989 |

Three zones above the centroid, five below. The mean-zero invariant is
**exact**: the gas-capacity-weighted mean of the zone anchors is **3.3483,
Δ +0.0000** (weights + census in
`results/calibration/_pjm144_zonal_anchor_derivation.json`: window gas
capacity ComEd 13.3 / AEP_Ohio 20.6 / ATSI 4.7 / West_APS 6.3 /
Central_PA 18.1 / Dominion 14.7 / EMAAC 15.4 / SWMAAC 5.9 GW; 986/994/993
marked-up tranches, 0 band-scoped, so all resolve zone anchors).
Max |anchor − ISO| = 1.0845 ≫ the 0.1 inertness bar → the arm was declared
**LIVE ex ante** and the solves proceeded. **Zero fitted parameters**
(+1 derived DOF entry, 18 → 19; `n_residual` 6 → 6).

### 1.3 Offer-side liveness confirmed at build time

The arm's own build log: median fixed margin 9.51 → 9.18 $/MWh, max
255.97 → 238.53 (2023), with all marked-up tranches on zone anchors. (The
log line labels them "per-class EP anchors" — a stale ERCOT-118/119
band-scope wording in `offer_curves.py:704` that fires for ANY overridden
anchor; cosmetic, left untouched mid-A/B.)

---

## §2 — Construction gates: four PASS, and the one FAIL is the verdict

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — arm `true` + resolved 8-zone map equal to the registry; control `false`/`null`; `gas_offer_net_revenue_margin` armed at 3.3483 in **both** |
| **K2** control integrity | **PASS on BOTH bases** — scorecard: control reproduces the keeper's determination and every criterion status; **strict byte: control − committed keeper = 0.0 MW on every class-hour of all three years**, and its `legitimacy_diagnostics` are content-identical (only the bundle-name label differs). The 27 src files that moved on main since the keeper's `a1a3a60` were PJM-inert exactly as the prereg recorded — an expectation the control could have falsified and did not |
| **K3** liveness | **FAIL — the pre-registered verdict condition.** MW leg passes ×26 (max class-hour Δ **1317 / 1288 / 1537 MW**); the zonal-price leg fails in every year: max zone \|Δλ\| **0.034 / 0.032 / 0.026 $/MWh** vs the 0.10 gate |
| **K4** single delta | **PASS** — the two scenario blocks differ in exactly the two zonal-anchor keys |
| **K5** year span | **PASS** — both bundles [2023, 2024, 2025]; holdout freeze ACTIVE and untouched |

## §3 — Kill gates: none fires

P1 C1 **16/16 all / 12/12 free** in both arms. P2 FAIL sets both **empty**.
P3 C6/C7/C8 all PASS (C8's watched CT_PEAKER cell stays grounded:
15.2/15.7 % + ST_GAS 36.6/40.0 % 2025-vintage rows, all D-4-clear and
shape-passing in both arms). P4 slack and dump exactly 0.0 everywhere.
P5 nothing swept — the anchors are the derive script's output, untouched
after the result.

**Both arms: CALIBRATED, 9/9 target grade, zero FAILs.** The A/B is clean;
the arm simply does not move anything the scorecard can see.

---

## §4 — What the arm DOES move: dispatch, reported in full

Class-energy deltas (arm − control, TWh):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_REGULAR | −0.398 | −0.701 | −0.967 |
| ST_GAS | +0.401 | +0.506 | +0.909 |
| CT_PEAKER | +0.117 | +0.225 | +0.123 |
| CC_CHP | −0.212 | −0.129 | −0.062 |

The re-anchoring makes eastern premium-zone CC energy dearer and western
discount-zone steam/CT energy cheaper at the margin, and the LP swaps
accordingly — the direction of both standing class-accuracy notes
(CT_PEAKER's C1 deficit note and Dominion CC_REGULAR 2025 overshoot, keeper
notes 3/8), **reported, never banked** (each shift is ≤ ~10 % of its note's
gap, and no gate distinguishes the arms). Zonal λ moves are uniformly tiny
and slightly positive (all zones +0.008…+0.034 $/MWh; the two-sided zonal
pattern the offer arithmetic predicts does NOT survive to zonal annual-mean
prices — sign agreement 3/8): PJM's zones are price-coupled in most hours,
so the system-marginal unit sets every zone's λ and the mean-zero
redistribution nets out, leaving only a small re-ordering residue (the
slightly dearer marginal mix).

**Why this differs from NYISO, where the same mechanism was a keeper:**
NYISO's convention is one-sided (reference zone fixed, others shifted DOWN
−1.14/−1.87 $/MMBtu), so its correction moved the whole offer stack's level
in two zones carrying 67.6 % of load — a level effect (λ −0.60…−0.87 $/MWh)
that closed a failing C3a. PJM's mean-zero convention preserves the level by
construction; what remains is cross-zonal redistribution, and PJM's coupled
topology prices almost none of it. Same mechanism, opposite conventions,
opposite verdicts — which is exactly why rule 25 makes verdicts per-ISO.

## §5 — C3c, the thinnest margin, is untouched

The keeper's thinnest margin (C3c tail counts vs the 0.5× floor) was the
declared risk of a cross-zonal offer redistribution. Measured: **PASS in
both arms with identical statuses**, and on the load-weighted tail-hour
probe basis the counts are identical (0/0/5 in keeper, control and arm
alike). No margin was consumed.

---

## §6 — The keeper question, answered directly

**Is this a recommended keeper candidate? No.** The pre-registration fixed
this case in advance: *"K3 fails → the arm is `I` (inert) on the matrix;
registered; keeper unchanged."* No kill gate fired, so the owner-escalation
branch (pre-committed only for P-kills, and covered by the in-session
standing instruction to promote structurally-sound arms whose gates regress)
is **not reached** — gates did not regress; they are bit-equal. Promoting
would replace a keeper bundle with one that differs by a ≤$0.034/MWh zonal
price wiggle and an unscored dispatch reallocation, spending keeper churn on
an effect no gate can see, against the prereg's own letter. The repo's `I`
convention (ercot-138's inert band, pjm-143's `hydro_budget_nameplate_aware`
K→I) leaves adjudicated-inert mechanisms default-off.

**What is preserved rather than lost:** the structural correction is fully
registered — the derived table lives in
`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]` (rule-23 frozen, exact
capw invariant), the derive path is standing tooling, and the flag is one
CLI switch away. Legitimate re-open conditions: (a) a mechanism or measured
input that decouples PJM's zonal prices enough that zone-level gas
economics become priced (e.g. a future sub-zonal split under its own
charter), (b) a zone-grain scored criterion entering the rubric, or (c) an
owner override of the prereg's K3 rule — any of which re-adjudicates with
new evidence under rule 28's DO-NOT-REDO discipline.

## §7 — Cross-ISO: what this verdict does and does not transfer

Nothing (rule 25). ERCOT and MISO keep `U`. But the *measurement pattern* is
worth stating for their lanes' own preregs: a capacity-weighted mean-zero
applier on a price-coupled topology produced a dispatch-live, price-inert
arm. ERCOT's spread is larger (2.580 $/MMBtu), `_gas_series` already carries
a flat EP-basis level term, **and its West decouples under GTCs** — so
ERCOT's exposure may price where PJM's did not; measure before assuming
either way. MISO's raw spread (0.332) is smaller than PJM's and MISO is
similarly coupled — its prior of inertness just got stronger, but its cell
stays `U` until its own lane measures it.

## §8 — Test baseline at this HEAD

`tests/{curation,scoring,unit}` sweep results recorded in the calibration
log entry (compared against nyiso-109's 14-failed baseline; the three
cache-key tests fail against a stale pinned literal on main —
`ScenarioConfig().cache_key()` verified **byte-identical** to origin/main at
`0e9fce2fb55b889f` despite this session's constants addition). 13/13
mechanism tests pass, including the new PJM registry coverage and
two-sidedness pins.

**Not claimed:** no amplitude claim (within-day offer σ remains $0.000000 by
construction — the pjm-141 flat-stack boundary is untouched and this arm was
never its lever); no C3c claim; no Dominion-CT claim; no forecast-lane
result; no out-of-training year touched (2023–2025 only, freeze ACTIVE).
