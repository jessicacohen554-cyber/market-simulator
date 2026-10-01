# RESULT miso-169 — PREREG-miso167 EXECUTED: the online-gated reserve supply survives every pre-registered gate; promotion is ESCALATED on two owner questions the prereg predates

**Session miso-169 (2026-08-19).** Charter: execute
`PREREG-miso167-online-gated-reserve-supply-2026-08-18.md` with the miso-168
corrected order, on the container the memory work of
`FINDING-miso169-15gb-memory-fit-2026-08-19.md` made solve-capable.
**Keeper `2026-08-16-miso-160-wefor-shape` UNCHANGED. Nothing is promoted by
this session.** Runs registered (rule 15): control
`2026-08-19-miso-169-control` (`miso169_gated_A`), arm
`2026-08-19-miso-169-online-gated` (`miso169_gated_B`).

---

## 1. Execution order compliance (miso-168 §3)

1. **Control first** — same-recipe zero-delta replay, `--year 2023 2024 2025`
   sequential, one invocation. **Bit-identical to the committed keeper on
   every scored sidecar of every year** (class_hourly / storage /
   reserve_family / system, numeric max|diff| = 0, non-numeric equal), so
   the control's tranche-grain `unit_hourly` IS the keeper's own P1.
   Committed with the unit_hourly layer before anything was built.
2. **§3 pre-check on the control's own unit_hourly**
   (`_miso169_online_gated_precheck.json`, committed before construction):
   **K-PRE-A did NOT fire — 78.7 %** (37/47 scarce hours with
   H_on ≥ reg+spin requirement) vs the ≥ 80 % inertness kill, one hour
   inside the line; **K-PRE-B clear** in every year (0.1–0.2 % of hours
   short vs the ≥ 99 % over-reach kill). Verdict: proceed to arm.
3. **Arm** — the keeper recipe through `replay_keeper --set
   miso_reserve_online_gated=true` (the sanctioned override channel), same
   years, same protocol. The single delta is the flag.

## 2. What was built (the §2 mechanism, as specified with one disclosed update)

`miso_reserve_online_gated` (GATED default OFF, MISO-only, zero fitted
parameters — the build commit carries the full inventory): the pergen pools'
R columns split into a GATED Reg+Spin product carrying the prereg's coupling
row `R − online_rho·ΣP ≤ 0` and an UNGATED Supplemental product; ONE nested
market-wide Reg+Spin family (measured cleared reg+spin requirement,
published Schedule 28 / BPM-002 $65/$98 two-step curve); a pool-shared
10-minute ramp row. Every pre-existing family is byte-untouched.

**The disclosed update:** the prereg (written 2026-08-18, before nyiso-143
landed) identified `online_rho` as the fleet's `(pmax−pmin)/pmin` — now
known to be dead code on binned fleets. Execution used the successor seam
the same day's NYISO merge shipped: the CAMPD-measured statistic, derived
from MISO's OWN record (rule 25) — **rho = 0.1764** over 5,276,357 online
unit-hours, 93.1 % coverage (`campd_online_reserve_rho_MISO.csv`; per class
coal 0.14 / CC 0.19 / CT 0.31 / ST 0.29; full-hour sensitivity 0.1705 —
partial-hour geometry immaterial). **The consumption seam clips to
`RHO_CLIP = (0.5, 4.0)`, whose 0.5 floor has NO primary citation — the
standing nyiso-144 owner escalation — so the arm SOLVED AT 0.5, not at the
measurement.** Unlike NYISO (where the gated row is the class's only bound),
here the coupling row ADDS to the pool's joint headroom row, so the floor
blunts the refinement in the CONSERVATIVE direction: at the measured 0.1764
the gate binds strictly tighter than what this arm measured.

## 3. The A/B (`_miso169_gated_ab.json`; arm − control, load-weighted P1)

| year | annual | summer | 47-scarce | DA-foreseen | RT-only | regspin dual>0 |
|---|---|---|---|---|---|---|
| 2023 | −0.00 % | −0.002 $/MWh | −4.46 | −49.00 | −0.00 | 5 h |
| 2024 | +0.01 % | +0.004 | +0.00 | +0.00 | +0.00 | 6 h |
| 2025 | **+0.10 %** | +0.119 | **+4.31** | **+10.12** | **−0.00** | **12 h** |

The 2023 foreseen-hour DECREASE is a real interaction worth naming: the
regspin binding re-dispatches synchronized capacity and RELIEVES the Midwest
sub-regional family's $200 binding (3 control hours → 0), a net price drop
in a handful of hours; annual effect −0.0003 %.

## 4. The §6 decision rule, gate by gate

* **K-1 (no criterion-year PASS→FAIL flip, C3a-2023/2024 included): PASS.**
  Verified at RECORD grain over the full scorer output: zero flips on any
  (criterion, class, year) record in any year. The §4 against-interest risk
  did not materialize (2023 annual −0.00 %).
* **K-2 (C3b never crosses 0.200): PASS** — price_shape PASS in both arms,
  all years.
* **K-3 (C8 both arms; no class newly over budget): PASS ON ITS INTENT,
  with a disclosed instrument caveat.** ST_GAS forced share is unchanged to
  four decimals in every year (0.3198/0.3348/0.4514 → 0.3198/0.3348/0.4513)
  and the mechanism adds no floor and no D-2 id. The caveat: BOTH freshly
  regenerated bundles score C8 FAIL under the **nyiso-143 D-4 per-unit
  conduct rider** (shipped 2026-08-18, AFTER the keeper's committed
  diagnostics), which un-grounds ST_GAS on ~4 tiny plants
  (1104/1131/1891/8056, each ≪ the 2 % materiality line individually)
  whose floors bind in hours their own meter reads offline. The control
  fails IDENTICALLY to the arm on a bit-identical-to-keeper dispatch, so
  this is the measuring instrument moving, not the mechanism — but it means
  **the standing MISO keeper itself would score C8 FAIL if its diagnostics
  were regenerated at HEAD**, which is owner-relevant beyond this lane (§6
  ask 2).
* **K-4 (C6 attested at promotion): moot** — no promotion (below).
* **K-5 (the rise lands in DA-foreseen hours): PASS, textbook.** 2025's
  price movement is +$10.12 in DA-foreseen scarce hours and **exactly $0.00
  in RT-only hours**; the regspin dual is $25.81 foreseen vs $0.00 RT-only.
  The mechanism reaches only the hours a deterministic LP may claim.
* **Magnitude vs the §4 ceiling:** +0.10 pp on C3a-2025 against the ~+3.3 pp
  reachable ceiling — nowhere near over-reach, and small in the direction
  the rho floor predicts (a 0.5-rho gate binds less than the measured-0.1764
  gate would).
* **Rule-22 leave-one-year-out: not triggered** — no verdict flip
  (both runs read the keeper's own C3a-2025/C3c posture; the registration
  headline NOT-YET is the replay bundles' absent governance attestation,
  identical in both arms).

## 5. Disposition — VALIDATED, NOT PROMOTED; two owner asks

Every pre-registered gate passes, so the prereg's own rule would promote.
The session nevertheless does NOT self-promote, because two questions the
prereg could not have known about (both born in the 2026-08-18 NYISO merge,
hours after the prereg was written) now sit between this mechanism and a
keeper, and both are recorded owner calls:

1. **The RHO_CLIP band.** The solved coefficient was the uncited 0.5 floor,
   not the measured 0.1764 (nyiso-144: "resolving the band is an owner
   call, not a session's"). Promoting would enshrine a keeper whose armed
   mechanism carries a guardrail-chosen coefficient — rule 21's letter is
   met (the measurement exists, committed), but its spirit is the owner's
   band decision. **Ask 1: resolve the band (or authorize the measured
   value for constructions where rho is not the sole bound); a re-solved
   arm at 0.1764 is one `--set` invocation on this container.**
2. **The nyiso-143 D-4 conduct rider vs every regenerated MISO artifact.**
   Any future MISO bundle — including a re-generated keeper diagnostics —
   now scores C8 FAIL on tiny-plant conduct that predates this session.
   **Ask 2: adjudicate whether the rider's per-unit conduct leg should gate
   sub-materiality plants, or whether the MISO ST_GAS floors need the
   plant-membership repair the rider is pointing at (the nyiso-140
   `reliability_floor_plant_exclusions` machinery exists for exactly
   this).**

Matrix: the `reserve_deliverability_scoping` MISO cell moves `R → O` — the
miso-132(a) refutation grounds (July-NIGHT slack, S-2 = 0.10–0.11 vs 0.25)
are defeated for the SCARCE window by owner-chartered post-dated evidence
(miso-167 anatomy; this session's measurement: H_on < requirement in 21 %
of the 47 scarce hours, and the built gate binding K-5-clean in 12 2025
hours), while promotion stays open on the two asks above. The
miso-132 night-lane finding itself is untouched — the gate is still slack
overnight, exactly as it measured.

## 6. Structural verdict (rule 1)

The mechanism is real market structure: MISO's Reg+Spin are synchronised
products by published definition, the requirement is MISO's own cleared MW,
the curve is the published tariff curve, and the LP now prices
synchronisation opportunity cost in exactly (and only) the hours MISO's own
DA market priced. C3a-2025 stays NOT-YET at essentially full magnitude
(−12.5 → −12.4 %) — which the prereg §6 anticipated: "if every gate passes
and C3a-2025 still fails, the mechanism stays and the determination stays
NOT-YET." The C3a-2025 residue beyond the reachable half remains the
model-class RT-only limit the miso-167 anatomy measured.
