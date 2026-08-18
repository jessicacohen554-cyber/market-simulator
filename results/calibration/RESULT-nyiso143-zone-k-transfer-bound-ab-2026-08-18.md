# RESULT nyiso-143 — the Zone-K transfer-bound A/B: **all six gates PASS, including the one that killed it — and the arm is still not promotable.** An owner escalation, NOT a rejection on fit

**Session nyiso-143, 2026-08-18.** Pre-registration:
`results/calibration/PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md`,
written and committed **before** either solve was launched. Charter D1
**GRANTED** 2026-08-16. Both arms solved 2023 / 2024 / 2025 in one bundle
(rule 16), years sequential (rule 12), and **both registered** (rule 15):

| arm | run id | bundle |
|---|---|---|
| control (keeper recipe replayed at this HEAD) | `2026-08-18-nyiso-143-control` | `results/calibration/nyiso143_control` |
| treatment (`nyiso_li_tsl_n11_security=True`) | `2026-08-18-nyiso-143-n11tsl-arm` | `results/calibration/nyiso143_n11tsl_arm` |

Gate record: `results/calibration/_nyiso143_ab_gates.json`, probe
`scripts/probes/_nyiso143_ab_gates.py`.

---

## 0. HEADLINE

> **All six kill gates are SILENT — K1, K2, K3, K4, K5 and K6′.** K6 killed this
> lever at nyiso-130; K6′, the owner's successor, escalates to provenance +
> shape and **clears it**. This is K6′'s second application and it did exactly
> what it was adopted to do.
>
> **And the arm still should not be promoted, for a reason that is a discovery
> rather than a fit result: the model's ENTIRE downstate scarcity formation IS
> this bound.** 100 % of its C3c tail hours are Long_Island, in both arms and
> every year. Relax the bound to the published number and the tail essentially
> vanishes — 21 → 2, 3 → 0, 24 → 5 h — turning a 2-of-3 C3c miss into 3-of-3
> and **breaking the only year C3c passes**.
>
> **This is a rule 22 D-5(b) escalation, not a session decision, and it is
> emphatically NOT a rejection on the residual (rule 1 `[R-STRUCT]` forbids
> that).** The cell moves `R → O`.

## 1. THE CONTROL REPRODUCES THE DESIGNATED KEEPER

The same-HEAD control replays the keeper's own `meta.json` recipe and scores
**C3c 21 / 3 / 24 h — bit-identical to the keeper's committed 21 / 3 / 24** —
with C1 / C2 / C3a / C3b / C4 / C8 all PASS and D-10 free-class C1 at
14/14 · 10/10. It carries no governance attestation (it is a probe, not a
keeper), so its determination reads NOT-YET on C6 UNATTESTED alone, as does the
arm's. **No keeper is promoted or superseded by this session.**

## 2. THE SIX GATES

| gate | verdict | evidence |
|---|---|---|
| **K1** config isolation | **PASS** | exactly one differing `scenario_config` field, and it is `nyiso_li_tsl_n11_security` |
| **K2** feasibility | **PASS** | slack 0.0 and dump 0.0 MWh, both arms, all three years |
| **K3** liveness | **PASS** | in-window bound 940.0 MW in the arm; 325 / 275 / 275 MW in the control |
| **K4** scope | **PASS** | `NYC>Long_Island` is the only link whose bounds move |
| **K5** seam | **PASS** | external import within the ±2 % band |
| **K6′** forcing provenance + shape | **PASS** | escalated (shares rose, as pre-registered) and cleared both legs |

**K6′ in detail.** The forced shares rose exactly as predicted — downstate
`reliability_floor × ST_GAS` 0.1694→0.1853, 0.1902→0.2224, 0.1225→0.1383, plus
sub-0.3 pp moves on `firm_import`, `nuclear_mustrun` and `hydro_min_flow`. Bare
K6 fires on *any* rise, including the +0.0001 ones, which is why it could not
adjudicate an import-relief lever. K6′ escalated instead:

* **leg (a) provenance (D-4, including this session's per-unit conduct rider):
  ZERO new failures in the arm.** It in fact **removes three** — 2024 and 2025
  `nyiso_gas_commitment_bridge × ST_GAS` on plant **2517 Port Jefferson**, and
  2024 `× CC_REGULAR` on 54574. 17 failures are pre-existing and present
  identically in both arms.
* **leg (b) shape (D-1): ZERO new misses.**
* **energy-normalised Δforced, reported and NOT gated:** +0.207 / +0.378 /
  +0.194 TWh on downstate `reliability_floor × ST_GAS`; everything else
  ≤ 0.05 TWh.
* **Recorded for the owner:** under an ABSOLUTE reading of leg (a) the gate
  *would* fire, on those 17 pre-existing failures. The pre-registration
  declared the **arm-vs-control** reading in advance and this run is scored on
  it; the absolute verdict is stored in the gate record so overturning the
  reading needs no re-run.

## 3. WHAT THE ARM DOES

| year | C3c model → (actual, band) | C3a model → | at-bound share, in-window | LI AC import TWh |
|---|---|---|---|---|
| 2023 | **21 → 2 h** (10, [5, 20]) | +9.6 % → **+9.0 %** | 0.845 → **0.248** | 3.392 → 4.563 |
| 2024 | **3 → 0 h** (13, [6, 26]) | +1.6 % → +1.9 % | 0.876 → **0.213** | 3.383 → 4.791 |
| 2025 | **24 → 5 h** (42, [21, 84]) | −2.5 % → −2.3 % | 0.711 → **0.068** | 2.599 → 3.321 |

* **C1 / C2 / C3a / C3b / C4 / C8 are PASS in both arms.** Mean LMP moves by at
  most $0.26/MWh, and 2023 C3a *improves*, away from the +10 % band edge.
* **C3c is the whole story, and it goes the wrong way.** The control misses in
  two years (2023 over-produces at 2.10×, 2024 under at 0.23×) and **passes
  2025**. The arm misses in **all three**, all under, and 2025 goes
  PASS → FAIL. Under the charter's D2 ruling the arm-vs-control *delta* is the
  reliable quantity, and the delta is unambiguous.
* **Class substitution is small and in the expected direction:** downstate
  ST_GAS −0.090 / −0.444 / −0.132 TWh and CT_PEAKER −0.177 / −0.087 / −0.041,
  displaced by CC_CHP / CC_REGULAR elsewhere.

## 4. THE DISCOVERY, WHICH IS THE REAL RESULT

**100 % of the model's C3c tail hours are Long_Island — in both arms, every
year** (control 21 / 3 / 24 all LI; arm 2 / 0 / 5 all LI). NYISO's modelled
scarcity pricing is produced by the Zone-K import bound binding in **84.5 /
87.6 / 71.1 %** of its design-condition hours. Replace that bound with the
published N-1-1 number and at-bound occupancy falls to **24.8 / 21.3 / 6.8 %**
and the scarcity disappears with it.

**The model has no other downstate scarcity mechanism.** That is exactly the
rule 14 `[R-ACCURATE]` signature — *"if swapping a hand estimate for real data
makes the backcast worse, that is a signal that something else in the model is
miscalibrated and the estimate was silently compensating for it"* — and it is
the same object nyiso-110 named from the other side (missing everyday
reserve-price formation) and nyiso-124 located as a downstate/in-city price
formation gap.

## 5. THE TWO READINGS, AND WHY THIS IS THE OWNER'S CALL

Stated plainly because the rules point in different directions and pretending
otherwise would be the dishonest move:

* **Reading A — rule 14 literal.** The 940 MW is the accurate published input
  and removes a 660 MW contingency the model already carries twice. Arm it; the
  C3c collapse is a **discovered bug**, and the downstate scarcity mechanism
  becomes the named root cause. Cost: C3c goes 3-of-3 miss, the single ledgered
  caveat slot cannot absorb it, and the determination goes NOT-YET.
* **Reading B — sequencing.** Build the downstate scarcity mechanism first,
  arm the accurate bound after, so the accurate input lands without leaving the
  model with **no** downstate scarcity formation at all. On rule 1
  `[R-STRUCT]`'s own terms — mechanisms that mirror the real market — a model
  whose scarcity comes from a deliberately-too-tight transfer bound and one
  whose scarcity comes from nowhere are both wrong; B says fix them in the
  order that never leaves the representation emptier than it started.

**Session recommendation: B, on sequencing — offered as a recommendation, not a
verdict.** Whichever way it goes, the deliverable is the same and it is already
committed: this A/B is DONE and must not be re-solved. What is open is the
ruling.

## 6. COLLATERAL FINDING — the nyiso-140 membership repair is INCOMPLETE, in a bigger way than Danskammer

The conduct rider, run on the full-dispatch bundles, shows that
`reliability_floor_plant_exclusions` fixed **one mechanism, not the plant**:

| year | mechanism | plant | floored | share of mechanism | binding h | measured median | at zero |
|---|---|---|---:|---:|---:|---:|---:|
| 2024 | `nyiso_gas_commitment_bridge × ST_GAS` | **2517 Port Jefferson** | 0.1495 TWh | **34.6 %** | 4,623 | 0.000 MW | 71.2 % |
| 2025 | `nyiso_gas_commitment_bridge × ST_GAS` | **2517 Port Jefferson** | 0.0529 TWh | 11.9 % | 1,568 | 0.000 MW | 50.3 % |
| 2025 | `nyiso_gas_commitment_bridge × CC_REGULAR` | 7314 | 0.0819 TWh | 11.4 % | 2,360 | 0.000 MW | 80.3 % |
| 2023–25 | `nyiso_gas_commitment_bridge × ST_GAS` + `reliability_floor × ST_GAS` | **2480 Danskammer** | 0.0010–0.0140 TWh | 0.0–4.4 % | 24–1,641 | 0.000 MW | 90.7–100 % |
| 2025 | `nyiso_gas_commitment_bridge × ST_GAS` | 8006 Roseton | 0.1881 TWh (arm) | 44.9 % | 1,714 | 0.000 MW | 60.9 % |

**The exclusion channel exists only on the reliability floor.** The gas
commitment bridge has no membership exclusion, so the very plant nyiso-140
identified as economically laid up is still being floored — by the other
mechanism, for 0.1495 TWh in 2024, a THIRD of everything that bridge leg
forces. This is rule 19 `[R-ONE-MECH]`'s "enumerate what already floors the
same class" working exactly as intended, one mechanism later. It is a named
successor object with its own identification and its own A/B; it is **not**
repaired here, and it is present identically in both arms so it does not bear
on the Zone-K adjudication.

**A guard the rider needed, added when the full-dispatch run exposed it.**
Plants carrying the benchmark's own **CT-only CEMS flag** (`ct_only`: EIA-923
net > 1.1× CAMPD gross, so the benchmark scores them on EIA-923 *monthly*
because the hourly CAMPD series is incomplete) are now **excluded** from the
conduct test — a zero median in a series the benchmark itself declines to trust
is a metering artifact, not conduct. Without it the rider convicted five such
plants. Recorded because the first version was wrong.
