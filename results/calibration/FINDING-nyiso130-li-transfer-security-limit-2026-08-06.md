# FINDING nyiso-130 — the Long Island cap was a transfer limit **minus a generation contingency**, and NYISO publishes the transfer limit itself

**Session nyiso-130, 2026-08-06.** Priority 1 of the handoff; lever-queue item 1
(`docs/mechanism-testing-matrix.md` §5.5), named by nyiso-129 §3a. Pre-registered
in full **before any solve** at
`results/calibration/PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md`.

**Rule 22:** 2023–2025 only. No out-of-training year was solved, scored, read or
registered; the holdout spend freeze was checked and not touched.

*(§5 onward — the A/B result, gates and disposition — is written from the arms'
own artifacts once both bundles exist. §1–§4 are settled without a solve.)*

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
