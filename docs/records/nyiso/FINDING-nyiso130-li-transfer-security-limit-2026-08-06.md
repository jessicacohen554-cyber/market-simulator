# FINDING nyiso-130 — the Long Island cap was a transfer limit **minus a generation contingency**, and NYISO publishes the transfer limit itself

**Session nyiso-130, 2026-08-06.** Priority 1 of the handoff; lever-queue item 1
(`docs/mechanism-testing-matrix.md` §5.5), named by nyiso-129 §3a. Pre-registered
in full **before any solve** at
`results/calibration/PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md`.

**Rule 22:** 2023–2025 only. No out-of-training year was solved, scored, read or
registered; the holdout spend freeze was checked and not touched.

**Headline: the arm is REJECTED as armed by its own pre-registered kill gate
(§5–§6); the IDENTIFICATION stands and is the durable result. The keeper is
UNCHANGED and NYISO now reads `CALIBRATED-WITH-CAVEATS` under an explicit owner
authorization for the in-training C3c ledger entry (§7).** §1–§4 were settled
without a solve and were committed before the arms finished.

---

## 1. The defect, as a category error rather than a residual

The armed `nyiso_li_lcr_tsl` caps the model's **only** mainland→Zone-K AC link,
`NYC>Long_Island`, at NYISO's published Zone-K **"Locality Limit"** — 325 MW
(2023) / 275 MW (2024, 2025) — inside the HB14-21 design-cooling window.

NYISO's own report says what that number is. **TABLE 1, note 2** of the Locality
Bulk Power Transmission Capability Reports, worded **identically in the 2024-25,
2025-26 and 2026-27 editions**:

> *"The true N-1-1 Transmission Security Limit is 940 in this scenario, the Bulk
> Transfer Limit accounts for the loss-of-source of 660 MW."*

So the quantity the model uses as an **hourly energy transfer bound** is

```
published Locality Limit  =  transfer limit (940 MW)  −  generation loss-of-source (660 MW, Neptune HVDC)
```

and it is consumed downstream as a *capacity-adequacy accounting* term: the 2023
LCR Report's **TSL Floor Calculation** enters it as
`Transmission Security Limit (MW) [B] = Studied 325` and computes
`UCAP Requirement [C] = [A] − [B]` against a **load forecast**. A term subtracted
from a load forecast to size an ICAP requirement is not a limit on an hour.

The 2023-24 edition organises the same arithmetic the other way round — the
applied N-1 outage is Y49 and the *limiting contingency* is `L/O Neptune HVDC
(660MW)` — so **the 660 MW deduction is inside the number in every edition**,
2023-24 through 2026-27, with the same limiting element throughout
(Dunwoodie–Shore Road (Y50) 345 kV @ **LTE 964 MVA**).

### 1a. Why it is a DOUBLE COUNT in this model specifically

The deduction exists so the ICAP requirement survives Long Island losing its
largest source. This model already carries that phenomenon **twice, explicitly**:

1. **Neptune's energy is delivered on a separate link.**
   `NYISO_external>Long_Island` (Neptune 660 + Cross Sound 330 + Northport-Norwalk
   1385 200) carries a measured seam envelope of 1,012 / 986 / 990 MW and sits
   **at its bound in 99.9 / 99.9 / 98.9 %** of all hours. The model *delivers* the
   660 MW **and** deducts 660 MW from the AC link against losing it.
2. **The contingency reserve is already held**, by the armed
   `nyiso_li_locational_reserve` — NYISO's own published Zone-K locational reserve
   ladder (`li_30min_total`), a keeper `K` cell since nyiso-113.

Rule 19 `[R-ONE-MECH]`. A generation-contingency reserve embedded inside a
*transmission* bound, on top of an explicit reserve requirement for the same
contingency, is the duplicate — and it is the **implicit** one, so it is the one
that goes.

### 1b. D-2 enumeration — what already owns Zone K (done before proposing)

| mechanism | what it owns in Zone K | status |
|---|---|---|
| `nyiso_li_lcr_tsl` | in-window bound on `NYC>Long_Island` | **the mechanism reconciled here** — forces no energy, correctly absent from D-2 |
| `nyiso_li_locational_reserve` | published Zone-K locational reserve ladder | armed, `K` — **the correct home of the loss-of-source phenomenon** |
| `nyiso_seam_deliverability_envelope` | measured P-32 envelope on the external LI link | armed, `K` — untouched |
| `nyiso_local_selfsupply` | LI 0.45 energy floor | **skips Long_Island** whenever the cap is on — confirmed absent from D-2 |
| `reliability_floor × ST_GAS` | LI persistent 24 h ST_GAS base (0.262) | live; the LI peak-window ramps are OFF (`NYISO_PEAK_WINDOW_FLOORS_OFF`) |

**Nothing is stacked.** One published number replaces another inside one already
armed mechanism: same link, same window, same symmetry, no new floor.

## 2. The identification — published, zero free parameters

New canonical metric `transfer_security_limit` (the area boundary's N-1-1
transfer capability *before* any loss-of-source deduction), distinct from
`import_limit`. Long Island = **940 MW**, one constant across all three years.

| capability year | published Locality Limit | stated true N-1-1 TSL | loss-of-source | limiting element |
|---|---:|---:|---:|---|
| 2023/24 | 325 MW | *(not stated)* | 660 MW (as the limiting contingency) | Y50 @ LTE 964 MVA |
| 2024/25 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |
| 2025/26 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |
| 2026/27 | 275 MW | **940 MW** | 660 MW | Y50 @ LTE 964 MVA |

**Declared, against interest.** The 2023-24 edition prints no true-N-1-1 figure,
so the 2023 row carries the 2024-25 value. Grounds: identical interface,
identical limiting element and rating, identical 660 MW deduction, and NYISO's
own Table 4 recording the Zone-K limit **unchanged 2022 → 2023**, with the later
325 → 275 move attributed purely to *"a change in methodology of this study"* —
not to any physical change. The arithmetically implied 2023-24 figure is
325 + 660 ≈ **985 MW**, so **940 is the tighter of the two candidates**, chosen
in the very year whose gate this lever was expected to help. `n_residual`
unchanged at 6.

**The boundary is clean.** The report's own Appendix A defines the Zone-K
interface as Y49 (Sprain Brook–East Garden City) + Y50 (Dunwoodie–Shore Road)
345 kV **plus** the two PAR-controlled 138 kV J→K ties, with the UDR-backed
external cables counted **separately** — exactly the model's two-link split. The
940 MW is a **net** Zone-K import limit (the base case schedules 300 MW K→J on
the PARs), so it maps onto this single net link directly.

Forward-reproducible (rule 13 `[R-MEASURED]`): the table is republished every
capability year and responds to changed conditions — the G-J row moves
3,425 → 4,350 → 4,500 → 4,525 MW across the same four editions as new circuits
enter service.

## 3. What the keeper looked like going in (measured, no solve)

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| in-window bound on `NYC>Long_Island` | 325 | 275 | 275 MW |
| flow at that bound, in-window p50 / p95 | 325 / 325 | 275 / 275 | 275 / 275 MW |
| share of in-window hours at bound | 80.1 % | 85.5 % | 66.3 % |
| **C3c model tail hours** | **22** | **3** | **24** |
| RT actual tail hours | 10 | 12 | 42 |
| gate band [0.5×, 2×] | [5, 20] | [6, 24] | [21, 84] |
| gate status | **FAIL (2.20×)** | CAVEAT (0.25×) | PASS — **3 h above the lower edge** |
| **tail hours that are Long Island** | **100 %** | **100 %** | **100 %** |
| **tail hours inside HB14-21** | **100 %** | **100 %** | **100 %** |
| both Zone-K links at bound, in tail hours | **100 %** | **100 %** | **100 %** |

**The whole of NYISO's modelled scarcity tail, in every year, is Long Island in
the window this bound is applied, with the bound saturated.** Evidence:
`results/calibration/_nyiso130_li_tsl_identification.json`, probe
`scripts/probes/_nyiso130_li_tsl_identification.py`.

## 4. The adverse case, stated BEFORE the solve

Because 100 % of the tail is this bound in every year, the arm was known in
advance to remove tail hours in the two years that do not want them removed —
2024 (already 3 h vs 12 h) and 2025 (24 h against a band whose **lower edge is
21 h**). The pre-registration therefore fixed, in advance, that **the single most
likely outcome is the C3c fail moving from 2023 to 2025 rather than closing**,
and that this would **not** count as a refutation (rule 1 `[R-STRUCT]`): the arm
replaces a mis-typed quantity with the published one and removes a double count
the model carries twice elsewhere. What *would* refute it: kill gates K1–K6, or
a load-bearing / protective criterion breaking — C3a most of all, since the arm
pushes all three years **down** against a ±10 % band.

---

## 5. The A/B result — the arm is REJECTED by its own pre-registered kill gate

Arms `nyiso130_control` / `nyiso130_n11tsl`, both 2023–2025 in one bundle each
(rule 16), years sequential and invocations concurrent (rule 12). Registered as
`2026-08-06-nyiso-130-control` and `2026-08-06-nyiso-130-n11-tsl`.

**The baseline is sound — the nyiso-128 stale-baseline failure does NOT recur.**
The control reproduces the designated keeper exactly: 22 h tail, all Long
Island, bound 325 MW, at-bound 80.1 %.

| gate | verdict | |
|---|---|---|
| K1 config isolation | **PASS** | exactly one differing field, and it is `nyiso_li_tsl_n11_security` |
| K2 feasibility | **PASS** | zero slack and zero dump, both arms, all three years |
| K3 liveness | **PASS** | in-window bound reads exactly **940.0** in the treatment, 325/275/275 in the control |
| K4 scope | **PASS** | no other link's bound moves |
| K5 seam | **PASS** | external import energy moves 0.000 / 0.000 / **+0.047 %** — the seam is exonerated |
| **K6 forcing** | **FIRED** | the downstate ST_GAS reliability floor forces **+0.22 / +0.42 / +0.23 TWh** more |

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| C3c control → treatment | 22 → **2** | 3 → **0** | 24 → **5** |
| RT actual / band | 10, [5, 20] | 12, [6, 24] | 42, [21, 84] |
| verdict | FAIL (0.20×) | FAIL (0.00×) | FAIL (0.12×) |
| LI AC in-window p50 | 325 → **621** MW | 275 → **671** MW | 275 → **428** MW |
| at-bound share, in-window | 80.1 → **21.9 %** | 85.5 → **17.0 %** | 66.3 → **4.7 %** |
| mean LMP | 33.855 → 33.604 | 37.043 → 36.937 | 61.113 → 61.113 |

C1 / C2 / C3a / C3b / C4 / C6 / C8 **PASS in both arms**, and the pre-registered
C3a adverse case **did not materialise** — mean LMP barely moves.

**P4 is confirmed far past its prediction.** The tail did not move years; it
**collapsed**, and 2024 forms **zero** scarcity hours. That settles §3's
measurement into a finding: **NYISO's entire modelled scarcity tail was
manufactured by the in-window Zone-K bound.** The incumbent's 2025 C3c PASS
(24 h against a band floor of 21) was a right number produced by a number NYISO
says is not a transfer limit — the failure mode rule 1 `[R-STRUCT]` names in its
second half ("never reach the right number through a mechanism that isn't real").

### 5a. Why K6 firing is substantive, not a rounding artifact

Most of the rises K6 caught are denominator effects (nuclear 0.7769 → 0.7771).
One is not. `reliability_floor × ST_GAS` rises in **forced energy**, not merely
in share: **2.784 → 3.002**, **2.797 → 3.216**, **2.371 → 2.598 TWh**. The floor
is a `min_gen` bound, so as cheaper imports displace the downstate steam fleet
its economic dispatch falls *below* the floor in more hours and the floor forces
more energy up to it. C8 still passes (ST_GAS forced share 23.5 / **27.9** /
19.3 % against a 30 % cap) — but 2024 lands within 2.1 pp of the cap.

## 6. Disposition — REJECTED AS ARMED, and why that is not rule 1 in reverse

The pre-registration fixed **REJECT on any kill gate** before the solve. K6
fired. The arm is rejected, and the grounds are stated precisely because rule 1
forbids the other kind:

1. **A protective gate fired, substantively** — not "the residual didn't move".
2. **The arm RELOCATES a proxy rather than removing one.** Zone-K reliability in
   this model is carried by **two** proxies — the too-tight transfer bound and
   the LI/NYC ST_GAS `min_gen` floor — and relieving the first loads the second.
   That makes the model *more* floor-driven, the opposite of what rule 20
   `[R-FORCED-BUDGET]` asks (floors are commitment scaffolding, not the dispatch
   model).
3. **It leaves the model forming essentially no scarcity**, which is a
   **mechanism** deficiency — rule 1's own primary criterion — not merely a fit
   one.

**The identification is untouched and is this session's durable result.** The
275/325 MW is demonstrably a transfer limit minus a generation contingency; the
double count is real and measured. What is refuted is the **bare number swap**
as the fix.

**Named successor (rule 19 `[R-ONE-MECH]`):** a **joint** reconciliation of the
Zone-K transfer bound **and** the downstate ST_GAS floor — one local-security
representation replacing both — with its own charter and pre-registration. Do
**not** re-test the bare swap.

## 7. What the keeper does, and the owner directive

**Keeper UNCHANGED**: `2026-08-06-nyiso-128-solar-basis`. Its C3c-2023 miss is
exactly the *"+12 hours in 2023"* the owner's directive names, and C3c is its
sole non-passing criterion. Applied as written, the directive supplies the
in-training authorization rule 22's C3c standing rule does not reach, so the
exception nyiso-129 withheld is now **written** — with its **own correctly-signed
OVER-production classification**, not folded under the 2024 under-production
caveat, and with the withheld block **preserved** as
`_withheld_exception_history`.

**NYISO reads `CALIBRATED-WITH-CAVEATS`** (re-verified from committed artifacts,
no solve). Ledgered caveats **1 of 1**. `audit_keepers.py --iso NYISO`: **PASS,
0 failures, 0 warnings**.

The ledger entry says, in the artifact itself, that the lane is **not exhausted**:
this session identified the object and tested the obvious fix, and the fix failed
its own gate.

## 8. Priority 2 — the GWh reconciliation, discharged

**981.8 GWh CONFIRMED; nyiso-128's 1,081.8 GWh RETIRED.** Detail and the CF
identification (narrowed against interest to the one mature-fleet year, 0.1955)
are in `PREREG-nyiso130-solar-cf-level-2026-08-06.md` and
`_nyiso130_solar_gwh_reconciliation.json`. The lever is identified, sized and
**deliberately not armed**: it pushes C3a and C3c the same direction as the
Priority-1 arm, so arming both on the same arms would make neither attributable.

## 9. Session integrity note, recorded against interest

The first recipe-fidelity check was run **without an explicit `--out-dir`** and
overwrote the committed `results/calibration/nyiso128_control` bundle with a
24-hour solve. It was caught immediately and restored from git; every tracked
blob in that bundle was then verified byte-identical to `HEAD`, and the check was
re-run against a scratch directory. Recorded so the next session knows the
driver's default out-dir points at a **committed** bundle.
