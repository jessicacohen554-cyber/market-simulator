# FINDING — pjm-133: `hydro_budget_nameplate_aware` **passes every pre-registered gate on PJM, with no kill fired** — the nameplate clip was the whole of PJM's hydro volume deficit (98/94/100 % of it), the LP takes 100.0 % of the freed water in all three years, and total class-volume error IMPROVES in all three. The same flag that caiso-130 killed.

**Registered (rule 15):** `2026-07-27-pjm-133-nameplate` (arm B) and
`2026-07-27-pjm-133-control` (arm A), both 2023+2024+2025 in one bundle each
(rule 16). Gates: `PREREG-pjm133-hydro-budget-nameplate-aware-2026-07-27.md`,
committed at `e1bb3d1` **before either arm solved** and merged to main before
the solve began. Scorer: `scripts/probes/_pjm133_nameplate_ab.py`. Pre-solve
sizing: `scripts/probes/_pjm133_nameplate_precheck.py` (no LP). Machine output:
`results/probes/pjm133_ab.json`, `results/probes/pjm133_precheck.json`.

**PROMOTION IS NOT REQUESTED AND NOT GRANTED** — it remains a separate owner act
(rule 1). §7 states the case and the one thing that blocks a clean promotion,
which is **not** this delta.

---

## §0 — the scorecard, in full

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **P1 PRIMARY** hydro deficit closes, ≥ 60 % of the re-allocation | +0.851 TWh (**100.0 %**) | +0.573 (**100.0 %**) | +1.042 (**100.0 %**) | **PASS all** |
| **P2/K5** identity: 0 MWh over bound, month totals, plant count | 73/73, drift 1.2e-9 | 72/72, drift 1.4e-9 | 72/72, drift 1.4e-9 | **PASS all** |
| **P3** D-2 ≤ 2 pp, hydro forced 0 %, D-4 off-window | ✓ | ✓ | ✓ | **PASS all** (worst move 0.33 pp) |
| **K1** C3a guard, ≤ +0.75 pp | −0.10 | +0.10 | +0.09 | **ok** |
| **K2** volume collateral, ≤ +0.50 TWh | **−0.534** | **−0.145** | **−1.120** | **ok — improves every year** |
| **K3** CO2, ≤ +1.0 pp and in ±7 % | +0.14 | +0.10 | −0.16 | **ok** |
| **K4** rubric non-regression | identical | identical | identical | **ok** |

**No pre-registered kill fired.** Every PRIMARY passes in every year.

C1 hydro volume, the PRIMARY's own quantity:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| arm A (control) | 14.599 TWh | 15.245 | 14.464 |
| **arm B** | **15.451** | **15.819** | **15.506** |
| benchmark | 15.468 | 15.855 | 15.507 |
| gap A → B | −0.869 → **−0.017** | −0.610 → **−0.037** | −1.043 → **−0.001** |

## §1 — the load-bearing result: the clip WAS the deficit, and it was predicted before the solve

The pre-registration, frozen before either arm ran, stated that the nameplate
clip explains **98.0 / 94.0 / 99.9 %** of PJM's entire hydro volume deficit and
predicted post-delta gaps of **−0.017 / −0.037 / −0.001 TWh**. The solve
returned **−0.017 / −0.037 / −0.001**. The prediction was exact to the GWh in
all three years.

The mechanism self-reports in-solve, every year, with nothing physically
unattainable:

```
PJM 2023 hydro budget: nameplate-aware rescale re-allocated  884.5 GWh over 156 clipped plant-months (0.0 GWh physically unattainable)
PJM 2024 hydro budget: nameplate-aware rescale re-allocated  592.3 GWh over 176 clipped plant-months (0.0 GWh physically unattainable)
PJM 2025 hydro budget: nameplate-aware rescale re-allocated 1203.4 GWh over 199 clipped plant-months (0.0 GWh physically unattainable)
```

*(Correction: commit `d303ced`'s message transcribed the 2025 line as "1075.6 GWh
over 176" — wrong on both figures. The solve log reads 1203.4 GWh over 199
clipped plant-months, as above; the pre-solve net figure of 1042.3 GWh and every
scored number are unaffected.)*

(The log counter accumulates across water-fill iterations, so it reads slightly
above the pre-solve net |Δ|/2 of 851.5/573.4/1042.3 GWh — same operation,
different accounting, exactly as FINDING-caiso130 §2 recorded.)

**Delivery is 100.0 %, not merely above the 60 % bar.** The keeper was already
running its hydro fleet at its deliverable ceiling; the only thing withholding
the energy was a budget the LP's own `P[g,t] <= pmax × availability` bound
silently clipped. Freed, it is taken in full. Zero new degrees of freedom — the
bound is EIA-860 nameplate × the calendar.

## §2 — the basis: clean, once attributed

Arm A does **not** reproduce the committed keeper bundle (max hourly |Δ|
2 452.95 / 3 459.05 / 3 330.20 MW). That was pre-registered as requiring
attribution before any verdict could be quoted, so it was attributed:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| max \|pjm133_A − **pjm132_control_A**\| (post-guard) | **0.000000 MW** | **0.000000** | **0.000000** |
| max \|pjm133_A − pjm121_ccbelt\| (pre-guard keeper bundle) | 2 452.95 | 3 459.05 | 3 330.20 |

**Arm A is byte-identical, on every class and every hour, to the previous
session's post-guard control.** The difference against the committed keeper
bundle is entirely the documented **pre-guard → corrected outage-envelope**
change (`docs/calibration-log/pjm.md`: the keeper is CALIBRATED only on the
pre-guard inflated envelope; the same recipe on the corrected envelope is
NOT-YET). Independent confirmation from the run itself: arm A's 2025
demand-weighted λ is **40.93**, precisely the guard-corrected A1 the pjm-129/132
sessions recorded against the keeper's pre-guard 41.53.

So the `2a01de8..HEAD` window is **not** implicated, the difference **predates
this session**, and both arms carry it identically. **The A/B comparison is
clean.** What it is *not* clean against is the committed keeper bundle — and
that is a pre-existing keeper-designation issue (§7), not a product of this
delta.

## §3 — the ex-ante ceilings held, and one ex-ante prediction was wrong

**C3a (K1) — the ceiling held with room to spare.** The prereg computed a
no-feedback λ movement of at most −0.037 / −0.057 / −0.233 $/MWh and flagged
2025 as the live risk. Measured: model λ moved **−0.03 / −0.03 / −0.04 $/MWh**
(30.72 → 30.69, 30.25 → 30.22, 40.93 → 40.89). The feedback ran at ~1.0× the
flat proxy in 2023/24 and ~0.5× in 2025 — *below* the no-feedback estimate, the
opposite of caiso-126's 1.2–3× amplification. The delta is, as pre-registered, a
volume fix and not a price lever.

**K2 — the prediction was too pessimistic, and this is recorded as such.** The
prereg predicted "**≈ neutral in 2023/2024**" on the grounds that the model sits
below actual on nearly every fossil class, so displacement should worsen those
gaps roughly one-for-one against the hydro gain. Measured: total class-volume
error **improved in all three years** — −0.534 / −0.145 / −1.120 TWh. The
displacement landed better than the arithmetic worst case, most strongly in 2025
where the model was over-producing COAL_BIT (+3.97) and CT_PEAKER (+7.90). The
2025 improvement was predicted; the 2023/2024 improvements were not.

## §4 — where the freed water goes (P4, reported, NOT gated)

| window (hours-share) | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight h0-6 (29 %) | +111.8 MW / **33.6 %** | +75.5 / **33.6 %** | +134.9 / **33.1 %** |
| belly h9-15 (29 %) | +81.0 / 24.3 % | +58.2 / 25.9 % | +109.9 / 26.9 % |
| evening h17-21 (21 %) | +91.3 / **19.6 %** | +53.7 / **17.1 %** | +100.7 / **17.6 %** |
| late h22-23 (8 %) | +114.5 / 9.8 % | +92.8 / 11.8 % | +144.1 / 10.1 % |

The water spreads **almost exactly flat** — window shares track the hours-shares
to within ~5 pp — with a mild overnight tilt and a mild evening shortfall. That
is the **same qualitative signature caiso-130 measured** (§3 there), reproduced
independently on a keeper carrying none of CAISO's evening-λ storage pin. The
difference is that on PJM it costs nothing, because no gate depends on it.

**This is deliberately not scored**, for the reason pre-registered in §3 of the
prereg: PJM files no `NG: PS` column, so its `NG: WAT` — the comparator *and*
the pinned target — carries pumped-storage generation the model books separately
in its 5 046 MW storage fleet. The "evening gap" against measured WAT is
substantially a PS booking artifact, so a window gate here would have been
scoring a confounded quantity. The numbers are reported so pjm-133 and caiso-130
remain directly comparable, and for no other purpose.

## §5 — the disclosed defect this delta does NOT fix, and must not be read as fixing

Measured pre-solve and unchanged by this session:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| EIA-930 `NG: WAT` target (what the keeper pins) | 15.45 TWh | 15.82 | 15.51 |
| EIA-923 prime-mover-`HY` budget (unpinned) | 8.98 | 8.86 | 8.47 |
| **pin uplift** | **+6.47** | **+6.95** | **+7.04** |
| implied CF of the 3 334 MW `HY` fleet at target | 52.9 % | 54.2 % | 53.1 % |

PJM's pinned hydro level asks a 3.3 GW conventional fleet to deliver ~6.5–7.0
TWh/yr of energy that the model's own 5.0 GW pumped-storage fleet is separately
generating (keeper net-storage trace: −1.4 to −1.8 GW overnight charge, +0.8 to
+1.3 GW evening discharge).

**Rule 14 `[R-ACCURATE]`, stated precisely.** The silent nameplate clip was
deleting 0.57–1.04 TWh/yr of that phantom hydro *before the LP ever saw it* —
an inaccurate input quietly compensating for a contaminated target. This delta
removes the clip, which **exposes** the pin rather than causing it. That is the
rule-14 signal working as designed, and burying it again by reverting to the
uniform scale is what rule 14 forbids in terms.

**This is a separate, pre-existing defect in its own lane.** It is disclosed
here, was disclosed in the prereg before the solve, and is **not** fixed,
bundled, or claimed. Its fix is a `measured_monthly_hydro` question (whether a
PS-inclusive `NG: WAT` may pin a `HY`-only fleet) and it touches every hydro ISO
whose BA does not file `NG: PS` — PJM, CAISO, NYISO and MISO all lack the
column; ISNE has it. **Filed as an ask, not built.**

## §6 — rule-22 LOYO

**Zero fitted parameters** — the bound is EIA-860 nameplate × the calendar; no
threshold, no percentile, nothing derived from a residual — so LOYO reduces to
per-year gate consistency, exactly as in FINDING-caiso126 §5 and
FINDING-caiso130 §6. Nothing was re-tuned against any year and there is nothing
to re-tune.

- **P1 is same-signed and identical in all three years**: 100.0 % delivery in
  2023, 2024 and 2025. Not one year carrying an aggregate.
- **K2 improves in all three years** (−0.534 / −0.145 / −1.120 TWh). Same sign
  throughout; the magnitude scales with the re-allocation, largest in the
  largest year.
- **K1 and K3 are within bound in all three years**, and their signs differ by
  year (C3a improves 2023, worsens 2024/25 marginally; CO2 worsens 2023/24,
  improves 2025) purely because the baseline error sign differs by year — the
  underlying λ and CO2 movements are same-signed (down) in all three.
- **No gate passes only in the aggregate, and no verdict rests on a single
  year.** The 2025 year is the largest delta (1.8× 2024, 1.2× 2023) and is also
  the year with the strongest K2 improvement; if this were a single-year
  artifact it would show as a 2025-only effect, and it does not.

LOYO is clean.

## §7 — disposition, and the one thing that blocks a clean promotion (it is not this delta)

**Arm B strictly dominates arm A.** Identical recipe plus one flag; every rubric
criterion identical (C1/C3a/C3c FAIL, C2/C3b/C4/C5a/C7/C8 PASS, C6 UNATTESTED,
NOT-YET in both); no criterion regresses; total class-volume error improves in
all three years; a real physical defect closes with zero DOF. This meets the
owner's stated promotion criterion from caiso-130 — *"if structural integrity
improves but gates regress that may still be a keeper"* — a fortiori, since here
**nothing regresses at all**.

**What blocks a clean promotion is upstream and pre-existing.** Both arms score
**NOT-YET** on the corrected outage envelope, while the designated keeper
`2026-07-25-pjm-121-cc-belt` is registered **CALIBRATED (10/10)** on the
pre-guard envelope (§2). So arm B cannot be compared like-for-like to the
*registered* keeper — only to the *same-recipe* control, which it dominates.
The keeper designation on the corrected envelope is an **owner-only** decision
already open in the PJM lane before this session (`docs/calibration-log/pjm.md`,
miso-88 precedent, three routes in FINDING-pjm132 §5). This session neither
resolves it nor is blocked by it.

**Recommendation:** arm B is a **keeper candidate on the corrected envelope**,
and the honest framing is that it is strictly better than the same-recipe
control on that envelope. Promotion is the owner's act, and it is coupled to the
open envelope decision — promoting arm B *is* effectively deciding the keeper
sits on the corrected envelope. That coupling is why this session does not
self-promote.

**The flag is NOT refuted anywhere, and is now validated where it matters most.**
caiso-130 armed it on the ISO with the *smallest* exposure (0.12–1.50 %) and was
killed by an overnight gate driven by CAISO's own storage-arbitrage λ pin. PJM
carries 3.6–6.7 % — an order of magnitude more — and passes every gate. The
cross-ISO reading is that the mechanism is sound and the caiso-130 kill was a
property of CAISO's evening λ surface, not of the nameplate bound.

## §8 — DO-NOT-REDO (new, binding)

Re-measuring the PJM undeliverable shares, the delta's energy budget, its
destination split, or the C3a/CO2 no-feedback ceilings — §0/§1/§3/§4 and the
committed precheck carry them. Re-solving this A/B to "confirm" the direction —
both arms are committed with their `hourly/` sidecars and arm A is byte-identical
to `pjm132_control_A`. Re-attributing the basis caveat — §2 settles it at
0.000000 MW against the post-guard control. Reverting to the uniform fleet-wide
scale as an improvement (rule 14 — that is the silent compensation this session
identified, not a fix). Scoping WHERE the overflow is re-allocated: the
water-fill has no free parameter and that is a feature (rule 24); adding one to
chase a residual is rule 13/21 forbidden. Gating a PJM hydro hour-of-day window
against measured `NG: WAT` while the PS contamination stands (§5) — the
comparator is confounded and the prereg refused it before the solve.

Carried forward unchanged: everything in FINDING-caiso130 §7. Notably still
binding: do not re-arm the flag on CAISO in any scoped form; do not re-measure
the cross-ISO blast radius.

**Filed by this session, not built:** the PS-inclusive `NG: WAT` pin (§5), and
`ASK-pjm134-dominion-zonal-inversion-2026-07-27.md` (the Dominion CT/CC zonal
inversion, raised by the owner during this session and measured from committed
payloads only).

## §9 — environment note (provisioning, not methodology)

A PJM per-plant year-solve peaks at **14.80 / 15.21 / 15.21 GB** (2023/24/25) on
a **15 GB** box; an earlier attempt was OOM-killed (exit 137) in 2024 at exactly
that peak. The year-release machinery is working correctly —
resident-after-release is flat at 1.02–1.08 GB with accumulators ≤ 0.19 GB, i.e.
**no cross-year leak** — so this is a provisioning fact, not a bug. **Splitting
years into separate invocations does not help**, because the peak is intra-year;
the rule-16 single-invocation requirement is therefore not in tension with the
memory limit. Resolved here with swap headroom; dispatch is unaffected.

Also environment-only, both of which hard-failed the arms once before any LP
ran: the container shipped an empty `data/clean` tree (48 datatypes regenerated)
and an empty `data/raw/pjm-da-virtuals` (36 months fetched from DataMiner2, the
feed `pjm_da_virtual_bids` reads directly by design).

Next number: pjm-134.
