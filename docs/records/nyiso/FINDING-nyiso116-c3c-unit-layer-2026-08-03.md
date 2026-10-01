# FINDING — nyiso-116: the C3c settlement basis is inert, the $2.46 pin is the wrong target, and the unit layer is now committed

**Date:** 2026-08-03 · **Scope:** NYISO 2023–2025 ·
**Keeper:** `2026-08-02-nyiso-113-li-locational` — **UNCHANGED by this session**
· **Pre-registration:** `PREREG-nyiso116-c3c-unit-layer-2026-08-03.md`
(committed and pushed before the solve).

**Headline: no C3c lever is proposed, and the knife-edge is formally retired as
a target.** Two lanes were tested and both are closed by measurement; a third —
the reproducibility of the attribution itself — is fixed.

---

## §1 — the settlement basis is INERT for C3c, and this is the first session that could test it

C3c scores the model's **energy-only** max-zonal LMP against an actual RT series
that, at NYISO, **embeds RCPF scarcity by market design**.
`calibration_verdict.py`'s own G-20a comment names this asymmetry outright
("Real RT settlement IS energy LMP + reserve price … NYISO RCPF-into-LBMP"), and
its designed remedy — the `overlay` key — never fires for a NYISO keeper: the
keeper's payload carries `ordc.hoursGt200 = {model, actual}` with **no
`overlay`**, because the post-solve RCPF overlay is refused under rule 19
`[R-ONE-MECH]` (matrix cell **G**: `reserves/spec.py::_nyiso_design` raises when
`nyiso_rcpf_enabled` meets `energy_reserve_coopt`).

So NYISO sits in the gap between two individually-correct decisions. The
admissible way to close it is not a second mechanism but the **co-opt's own
locational duals** — which only became readable from a bundle when nyiso-114
persisted `hourly/reserve_family_<year>.parquet`. Reconstructing the settlement
basis that way (a zone's adder = the sum of duals of every region containing it,
per `NYISO_RCPF_LOCATIONAL` + `…_LI`):

| year | C3c energy-only | C3c settlement | max zone adder | **best settlement in a sub-threshold hour** | margin to $300 |
|---|--:|--:|--:|--:|--:|
| 2023 | 3 | **3** | $81.25 | $286.42 | **$13.58** |
| 2024 | 0 | **0** | $31.25 | $297.54 | **$2.46** |
| 2025 | 14 | **14** | $140.62 | $276.42 | **$23.58** |

**Unchanged in every year, and the last column proves it rather than observing
it**: the highest settlement price attainable in *any* hour the energy-only
series leaves below the gate is still below the gate. The reserve families never
arrive before the energy price — in 2024 the adder is exactly **$0.00** in all
three pinned hours, and every one of that year's 7 family-binding hours has a
max-zonal price ≤ $250.

**Correction to this session's own pre-registration.** §0(1) of the prereg
wrote that the adder "is nonzero only in hours whose energy price already
exceeds $300". That is too strong and is **wrong**: the adder is nonzero in some
sub-threshold hours (up to $31.25 in 2024). The correct — and stronger —
statement is the margin column above. The conclusion is unaffected.

## §2 — the $2.46 knife-edge is not the gate, and closing it would score false positives

C3c bands the model within `[0.5×, 2.0×]` of the RT actual. Measured on the
keeper's own committed prices:

| year | model | RT actual | ratio | hours needed to PASS | the hour that must clear | it sits at | shortfall |
|---|--:|--:|--:|--:|---|--:|--:|
| 2023 | 3 | 10 | 0.30× FAIL | **5** | #5 | $286.42 | **+$13.58 (+4.7 %)** |
| 2024 | 0 | 12 | 0.00× FAIL | **6** | #6 | $201.69 | **+$98.31 (+48.7 %)** |
| 2025 | 14 | 42 | 0.33× FAIL | **21** | #21 | $235.73 | **+$64.27 (+27.3 %)** |

Three consequences, none of which survives the received framing:

1. **C3c fails in all three years**, not just 2024. The caveat is not a 2024
   defect with a 2024 lever.
2. **2023 is the nearest miss, not 2024** — $13.58 on hour #5 against $98.31 on
   hour #6. Two sessions have organised around the year that is *farthest* from
   its gate.
3. **Closing the $2.46 pin does not close 2024.** It moves the year to 3 h =
   **0.25×**, still below `TAIL_LO`. The pin is not one rung short of the gate;
   the gate is decided by hour #6, at $201.69.

**And the pinned hours are not real tail hours.** The actual RT (11-zone mean)
in the model's three pinned hours h4528–4530 is **$282.83 / $179.20 /
$128.43** — all below $300. Meanwhile **h4526, which reality priced at
$511.30 and which IS one of 2024's twelve tail hours, the model prices at
$201.69** — it is the very hour #6 above. So a lever sized to lift the pin over
$300 would book **three false positives** and still miss the one true tail hour
sitting inside its own range. That is the caiso-144 pattern (a mechanism that
improves a count by inventing a mis-timed tail) and it is a rule 1
`[R-STRUCT]` violation by construction, independent of any residual.

**This corroborates and refines nyiso-85 §7d rather than contradicting it.** At
the episode level nyiso-85's "not timing" stands, and this session measures it as
a rate: of the model's *own* tail hours, **67 % (2/3) in 2023 and 79 % (11/14)
in 2025 are real tail hours**, with only 1 and 3 false positives. What is new is
the finer grain — inside the June 2024 episode the model's peak is **phase-shifted
about two hours late and clipped**, which is exactly what makes its top hour a
false target while its 6th hour is the true one.

The distribution says the same thing. Model/actual percentiles track to ~p99 and
then the model runs out of ladder: p99 **$76.88/$119.69**, **$148.14/$137.93**,
**$194.81/$222.12**; p99.9 **$263.80/$310.08**, **$197.93/$388.41**,
**$329.42/$734.28**; annual max **$503.74/$1,146.91**, **$297.54/$997.49**,
**$489.62/$2,073.88**. The deficit lives in the top ~0.1 % of hours — which is
nyiso-85's SRMC/oil-parity roof, already attributed, and **not** something a
reserve-side or threshold-side lever reaches.

**Conclusion: the C3c lane at NYISO has no untested cheap lever.** The
settlement basis is closed by §1, the knife-edge by §2, and the residual belongs
to the owner-gated peak-half amplitude question (nyiso-110) — the same
phenomenon seen from its tail. Rule 1 forbids reaching the count any other way.

## §3 — a globally-failing replay can still be a faithful instrument, per gate

nyiso-114 §2 established that a keeper arming a P0-run-pattern bridge cannot be
re-solved into byte-identity once main has moved, and labelled every downstream
result "measured on the recipe, not the keeper". That labelling is right, but it
is not uniform across quantities, and this session measures where it bites:

| year | all zone-hours max \|Δp\| | **top-20 tail hours max \|Δp\|** | C3c keeper | C3c recipe |
|---|--:|--:|--:|--:|
| 2023 | $10.5045 | **$0.000000** | 3 | 3 |
| 2024 | $10.5637 | $1.789489 | 0 | 0 |
| 2025 | $9.0424 | $4.744358 | 14 | 14 |

The divergence is a marginal-tie reshuffle in the *body* of the distribution; the
**tail is untouched** (2023 bit-identical) and the scored C3c count is identical
in all three years. **Standing lesson, general to every ISO lane: G1 is a
per-gate property, not a bundle property.** A replay that fails G1 globally may
still be the correct instrument for a specific gate — but that has to be shown
for that gate, as here, never assumed.

## §4 — the attribution was not reproducible; now it is

nyiso-114 §6 attributed the 2024 pin to a named unit, a named offer rung and two
named transmission limits. **None of it was reproducible from any committed
artifact**, because `hourly/unit_hourly_*.parquet` and `hourly/network_*.parquet`
are excluded by `.gitignore:325–330`. That exclusion rests on two stated grounds
and **both are measured false here**:

* *"regenerable by a replay"* — nyiso-114 §2 measured that a replay does **not**
  reproduce a keeper arming a P0-pattern bridge. For such a keeper the
  unit/network layer is **permanently unrecoverable**, and it is precisely the
  layer C3c attribution needs.
* *"~58 MB/bundle"* — measured for NYISO: **920 KB/yr** unit + **170 KB/yr**
  network, **3.2 MB for the whole three-year bundle**. The figure predates the
  `DELTA_BINARY_PACKED` `hour` encoding, whose own docstring records CAISO's unit
  frame going **12.60 MB → 1.74 MB** from exactly that change. The rule is ~18×
  overstated for this ISO.

This session therefore commits the layer for the arm bundle (`git add -f`; the
gitignore default stands for ordinary bundles, and its comment is corrected to
state what was measured). The C3c pin attribution is now checkable from the
repository, by anyone, without a solve — which is the same argument nyiso-114 made
for the reserve dual, applied to the layer that answers the question this lane is
actually about.

## §5 — gates and predictions, as pre-registered

Arm `results/calibration/nyiso116_c3c_unitlayer`, 2023–2025 in one bundle.

| gate | result |
|---|---|
| **G1** replay fidelity | **FAIL** — max \|Δp\| $10.505 / $10.564 / $9.042. Pre-registered as expected; it flips labels, not reporting. The 2024 figure is **identical to nyiso-114's own** ($10.5637), which is itself a useful check: the divergence is stable across sessions. |
| **G2** C3c-tail fidelity | **PASS** — C3c 3/0/14, identical to the keeper; top-8 tail \|Δp\| **$0.000000 / $0.000000 / $4.744**. Kill K-A did not fire, so G4 was permitted. |
| **G3** sidecars well-formed | **PASS** (after a disclosed gate correction, below) — 747/744/744 units, 8 links, 0 NaN, 0 cells over cap. |
| **G4** §6 re-verification | **all four claims CONFIRMED** — see below. |
| **G5** span | **PASS** — 2023–2025, no year outside training. |

| id | prediction | verdict |
|---|---|---|
| P1 | G1 fails | **CONFIRMED** |
| P2 | G2 passes | **CONFIRMED** |
| P3 | both LI import paths at their limits in h4528–4530 | **CONFIRMED** — `NYC>Long_Island` 275.0/275.0, `NYISO_external>Long_Island` 1200.0/1200.0, all three hours |
| P4 | exactly one part-loaded LI generator, an OIL tranche at ≈ $297.539 | **CONFIRMED** — **1** part-loaded of 132 tranches / 106 running: `7146_1`, oil, **68.9346 of 73.8 MW** |
| P5 | ≈ 596.9 MW idle on Long Island, ±5 MW | **CONFIRMED** — **596.9 MW** exactly (26 fully-idle tranches; total headroom 601.77 MW) |

**nyiso-114 §6 is verified in full, and now from committed artifacts.** Its
marginal-unit MW (68.93 of 73.80) and idle figure (596.9 MW) reproduce to the
decimal. The only bookkeeping difference is the tranche count behind the idle
total (26 fully-idle tranches here vs §6's "12 oil + DR" grouping); the MW agree
exactly.

**One honest divergence, reported not buried.** At the **year** level this arm
finds **1** LI-family-binding hour in 2024 (h3762) where nyiso-114 §3 reported
**0**. That is the G1 divergence reaching the reserve layer. It does **not**
touch §6: at the pin itself, zero LI families bind and `reserve_price` is
**0.0**, so the pin remains energy-side. It is recorded because a session that
only reports the agreements is not measuring.

### The gate correction, disclosed

**G3 and P4 initially FAILED, and the fault was mine, not the instrument's.**
Both were specified with an absolute `1e-6` MW tolerance, while
`_unit_hourly_frame` stores `mw` and `cap_mw` as **float32**, whose spacing is
**7.6e-06 MW at 113 MW and 6.1e-05 MW at 838 MW** — so the tolerance sat 8–60×
*below the representable precision* and **no float32 column could ever satisfy
it**. Measured consequences of the bad tolerance: **131,038 cells (2.0 %)** read
as "dispatch exceeds cap" with a **maximum excess of 1e-04 MW (1.2e-07
relative)**, and **15** units read as "part-loaded" of which **14 sat exactly at
their cap**. The tolerance was changed to **1e-3 MW (1 kW)** — a physical floor,
~130× above float32 spacing at fleet scale — **after seeing the result**, and
both readings are reported here.

This is the third instance in three sessions of the failure mode the brief names
— *specify every gate on an instrument that can observe what it claims*. The
first two (nyiso-113's K3/K4 on a broadcast column, nyiso-114's G3 needing
`held_mw`) were about a column's **semantics**. This one is about a column's
**dtype**, which is a distinct check and was not on anyone's list: it is not
enough to confirm the writer emits the column, one must also confirm the column
can *represent* the tolerance the gate asserts.

## §6 — governance

* **Keeper UNCHANGED** at `2026-08-02-nyiso-113-li-locational`. Nothing
  promoted, demoted or re-keyed. The arm is registered as a **diagnostic**; G1
  fails by design, so it is not a keeper candidate.
* **Rule 16** — 2023, 2024, 2025 in one bundle. **Rule 22** — the holdout spend
  freeze is ACTIVE; no year outside 2023–2025 was solved, scored or read, and no
  marker was spent or requested.
* **Rule 21 / 24** — zero DOF, no `ScenarioConfig` field, no CLI flag. Kill K-C
  (the no-tuning clause) held: **no parameter was introduced, changed or fitted
  in this session.**
* **Rule 28(b)/(d)** — the `nyiso_rcpf_postsolve_overlay` note records the §1
  measurement (cell stays **G**); one instrument row added. No other ISO's cell
  touched.
* **Rule 28(c) census** — re-run for NYISO on current main: **0 absent, 0
  prose-only, 0 armed-with-no-cell**, unchanged. The ratchet baseline is not
  widened.
