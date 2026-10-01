# PREREG nyiso-128 — NYISO front-of-meter solar capacity basis

**Status: PRE-REGISTERED AND NOT EXECUTED.** Filed **before** either arm is
solved, so the decision rule, the kill gates, the declared limitation and the
adverse case are on the record first.

Incumbent keeper: `2026-08-04-nyiso-125-seam-envelope`, determination
**NOT-YET**, sole FAIL `price_mean` (C3a) at **+7.7 / −0.8 / −10.2 %**, with
C3c carried as the single ledgered caveat (18/2/21 h vs 10/12/42 h > $300,
failing 2024 alone).

---

## §1 — the object

Replace the **capacity basis** of NYISO solar. Today it is the EIA-860
utility-scale operable schedule for New York, which lists every NY solar plant
≥ 1 MW. When armed, it is NYISO's own registry — Gold Book **Table III-2a,
"NYISO Market Generators"** — via
`data/raw/reference/nyiso-market-solar-capacity.csv`
(`scripts/data/derive_nyiso_market_solar.py`).

Flag: `nyiso_solar_market_generator_basis` (default off, byte-identical off).
CLI: `--nyiso-solar-market-generator-basis`.

---

## §2 — why the incumbent basis is wrong: a double count against the load series

EIA-860's NY population includes roughly **2 GW of distribution-connected
NY-Sun community solar that is not a NYISO market generator**. Its output is
**already netted out of the EIA-930 `NYIS` demand series the model uses as
load**: EIA-930 `NYIS` `NG: SUN` is **identically zero in every hour of
2023-2025** — nyiso-106 measured 8,760/8,760 zero hours and recorded the
reason, *"structurally absent (NY grid solar is overwhelmingly
distribution-connected / net-metered)"*.

So the same MWh is counted **twice**: once as a reduction in demand, once as a
grid-supply decision variable. This is the rule 14 `[R-ACCURATE]`
*documented-misalignment* path — the EIA-860 population is defined on a
**different boundary** than the model's representation, so it is reconciled to
the subset that is genuinely a NYISO grid resource rather than replaced by a
guess.

**Measured, before solving:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model solar capacity (EIA-860 basis) | 1,645 MW | 2,566 MW | 2,930 MW |
| model solar energy | 1.94 TWh | 2.64 TWh | 3.55 TWh |
| **NYISO registered market fleet** (III-2a) | **174.4 MW** | **573.4 MW** | **573.4 MW** |
| **NYISO published market-solar energy** (III-2a Net Energy) | **0.23 TWh** | **0.50 TWh** | **1.08 TWh** |
| armed-arm energy | 0.21 TWh | 0.52 TWh | 0.75 TWh |
| **energy removed by the arm** | **1.72 TWh** | **2.13 TWh** | **2.80 TWh** |

The 2026 Gold Book (already on disk) independently confirms **no PV market
generator entered during 2025** — the same 15 units — and publishes their
2025 output as 1,081.8 GWh. nyiso-106's independent MIS P-63 daylight-bulge
decomposition (0.212 / 0.577 / 0.994 TWh, stated there as a lower bound) agrees.
Three NYISO instruments, one answer.

---

## §3 — what makes this admissible, stated before the result

* **Zero free parameters.** Registry membership is an **identity**. Three
  published columns (zone letter, nameplate MW, in-service date), the existing
  A–K → five-zone crosswalk, and the same month-of-commercial-operation ramp the
  EIA-860 path already applies. No percentile, threshold or scalar is chosen
  anywhere. **`n_residual` must stay at 6.**
* **Rule 13 `[R-MEASURED]` forward test.** It is an INPUT — *which plants are
  NYISO market generators* — that regenerates for a forward year from the same
  registry (a newly interconnecting plant enters on its in-service date) and
  responds to changed conditions. It is **not** the measured generation series
  and **not** a cap at delivered output. The explicit contrast is
  `caiso_solar_cap_at_delivered`, which pins an outcome, has no forward
  analogue, and is barred from any keeper; this is the opposite construction.
  The LP still dispatches and curtails solar endogenously.
* **Rule 25 `[R-ISO-SCOPE]`.** NYISO-only, from NYISO's own posting; the
  artifact records its ISO and the loader hard-errors on a mismatch.
* **Rule 19 `[R-ONE-MECH]`.** One basis swap on one input. No floor, no D-2 id,
  no scarcity parameter, no offer change.
* **Independent level check, computed before the correction was built.** The
  registry's own Net Energy over its own mid-year capacity gives **12.9 %
  (2023) / 13.9 % (2024)** — physical utility PV, within a point of the 0.133
  the model's (nyiso-75 donor-repaired) NYISO solar profile already carries. The
  **shape and the CF level were already right**; only the capacity basis was
  wrong. That is what makes this an input repair and not a retune.

---

## §4 — the DECLARED LIMITATION, which bounds what may be claimed

This swaps the capacity basis **only** and keeps the existing ISO-wide CF
normalization (a whole-NY-fleet blend the model realizes at ≈ 0.133). NYISO's
registered fleet is more tracking-heavy (≈ 0.20 CF on the Gold Book's own Net
Energy column). Measured against the registry's published output, the armed arm
lands **within 8 % (2023) and 4 % (2024)** but **0.33 TWh short in 2025**, where
the large tracking plants (Morris Ridge, High River, East Point) came to
dominate the registry.

**The residual 2025 error is therefore in the TIGHTENING direction — the
direction that flatters C3a-2025.** Registered before any result:

> **A C3a-2025 improvement may NOT be banked whole.** The arm removes ~0.33 TWh
> more 2025 solar than the registry's own published output implies, and the
> finding must report the C3a-2025 movement **against that bound**, not as if
> the whole move were earned. If C3a-2025 closes, the finding states explicitly
> how much of the move the over-removal could account for.

Re-identifying the fleet CF is a separate object with its own identification
work (rule 19) and is deliberately **not** bundled here.

---

## §5 — blast radius

* **In scope:** the NYISO **solar** capacity basis only.
* **Untouched, verified numerically before filing:** wind (byte-identical in
  both arms, `np.array_equal` on capacity and CF), every other ISO
  (byte-identical — the hook is gated on `iso == "NYISO"` *and* the flag), and
  every scarcity, ORDC, floor, reserve, seam and offer mechanism. The armed
  `nyiso_seam_deliverability_envelope` is unchanged; the rejected
  `nyiso_seam_par_attribution` stays off.
* **All three years in one invocation, one bundle** (rule 16), years sequential
  (rule 12), 2023-2025 only. No out-of-training year is solved, scored, read or
  registered; the holdout spend freeze is ACTIVE and is not touched.

---

## §6 — the ex-ante prediction

Registered **before** solving, and falsifiable.

**P1 — the summer peak tightens and the merchant peaking fleet is called.**
The defect this lane was opened on is that the model does not run NYISO's
summer peaking fleet: in JJA h16–h18, model vs measured (CAMPD gross) is
**CT_PEAKER 0.27 / 0.29 / 0.41×** and **ST_GAS 1.07 / 0.89 / 0.81×**, against
model solar of **689 / 1,120 / 1,545 MW** in the same window that has no
counterpart in NYISO's published fuel mix. Removing the phantom solar should
raise CT_PEAKER and ST_GAS output in that window in every year, **most in 2025**.

**P2 — C3a moves UP in all three years, most in 2025.** The correction is
year-differentiated by the measured growth of NY community solar (1.72 / 2.13 /
2.80 TWh removed), which runs in the same direction as the C3a residual
(+7.7 / −0.8 / −10.2 %). This differentiation is **not** a fitted scoping — it
is what the registry says.

**P3 — the honest one.** P2 predicts the *direction*; it does **not** predict
that C3a-2025 lands in band, and it explicitly does not predict that C3a-2023
stays in band. See §8-3.

**P4 — C3c may move but is not the target.** Lifting the summer peak may add
> $300 hours. The C3c ledger is **not** re-opened by this arm and no scarcity
parameter is touched.

---

## §7 — kill gates

Any one firing **stops promotion**. Registered before the result.

* **K1 — no free parameter.** Any value not published in Table III-2a appears
  ⇒ **stop**.
* **K2 — no new unserved energy.** Any hour of new slack/VOLL that the
  same-HEAD control does not have ⇒ stop. (This arm removes ~1 GW of supply at
  the summer peak; if the system cannot serve load without it, the correction is
  removing something real.)
* **K3 — C1 does not regress.** The fuel-mix free-class score must not fall
  below the control's 10/10, and no gas class may leave its band.
* **K4 — live, not inert.** If max zonal |ΔLMP| < $1/MWh in every year, the arm
  is reported inert and **not armed** (rule 26 — no default-off parking).
* **K5 — the seam does not absorb the correction.** Net four-link seam p50 must
  stay inside the monthly EIA-930 reconciliation band. If the removed solar is
  simply replaced by imports rather than in-state thermal, P1 is falsified and
  the arm is not doing what it claims.
* **K6 — control reproduces.** The same-HEAD control must reproduce the
  nyiso-125 keeper's C3a to ±0.2 pp, else the comparison is invalid and nothing
  is read.
* **K7 — C7/C8 hold.** The protective diurnal-shape and forced-energy gates must
  not fail. Forcing an over-tight system is exactly how a supply removal goes
  wrong.

---

## §8 — the decision rule, and the adverse case

**Promotion is on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` grounds — the
more faithful input — and NEVER on a score.**

1. Any kill gate fires ⇒ **no promotion**; register the arm as a rejected probe
   (rule 15) and update the matrix cell with the rejection (rule 28).
2. All gates silent and the arm is live ⇒ promote, **even if C3a or C3c is
   unchanged or modestly worse**, under the owner's standing disposition that
   structural gain may outweigh a gate regression. A double count against the
   load series is a defect whether or not removing it improves the fit.
3. **The adverse case, named now:** the most likely bad outcome is that removing
   ~1.7 TWh in 2023 pushes **C3a-2023 (today +7.7 %, the closest to a band edge)
   through +10 %**, converting a PASS to a FAIL and trading one failing year for
   another. **If that happens it is reported as a FAIL and the arm is NOT
   rescued by scoping the basis to a year, a zone or a season.** Any such
   scoping is a fitted parameter and is refused in advance by §3.
4. A second adverse case: the arm closes C3a-2025 *and* the §4 over-removal can
   account for most of the move. That is **reported as unearned**, per §4.
5. **No tuning under any branch.** No band widened, no registry row dropped, no
   CF re-normalized in response to a score.

---

## §9 — leave-one-year-out

Rule 22 requires leave-one-year-out within 2023-2025 before promotion. Because
§1's registry is published and not fitted to any year, LOYO here is a
**consistency check**: the registry rows are identical whichever year is held
out, so a verdict that flips on which year is held out would indicate the
**CF-basis limitation of §4**, not the basis swap, is doing the work — and that
is itself a stop.
