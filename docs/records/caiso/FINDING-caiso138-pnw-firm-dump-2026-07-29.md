# FINDING — caiso-138: the WECC_PNW firm-hydro dump is the **COMPOSITION** — a must-flow floor built from the corridor-split DMM level × the TOTAL-system shape collides with the corridor's own (correct) measured envelope, and the residual has no lawful outlet because the design's outlet — the export sink — is **silently deleted in every scored P1 pass** by the bridge seam's zeros-floor max-composition. The reconciliation is the floor↔cap pointwise min (`caiso_firm_import_envelope_clip`), zero new DOF, E1/E2 pre-registered +$0.00.

Charter: the caiso-138 session brief (the caiso-134 §2 observation). All D-gates
(D1–D4) were passed on committed bytes before any solve. Instrument (committed,
no LP, no solver): `scripts/probes/_caiso138_pnw_firm_dump.py` (§A–§E).
Pre-registration (committed and pushed before arm B solved):
`PREREG-caiso138-firm-envelope-clip-2026-07-29.md`.

Keeper at session start: `2026-07-27-caiso-130-nameplate-aware`
(`results/calibration/caiso130_nameplate_B`, NOT-YET, fail {C3a-2025, C3c}).

---

## §A — D1: the defect, quantified on the keeper's committed bytes

Annually the dump is an order of magnitude larger than the filed per-window
means suggested:

| year | dump TWh | dump hours | annual mean MW | caiso-134-window mean MW (filed) | node λ in dump hrs | measured MALIN, SAME hrs (median) |
|---|---|---|---|---|---|---|
| 2023 | **1.086** | 2,774 | 124.0 | **70.2** (70) | −26.001 in 100.0 % | **+52.67** |
| 2024 | **1.716** | 4,084 | 195.9 | **160.9** (161) | −26.001 in 100.0 % | **+41.22** |
| 2025 | **0.965** | 2,769 | 110.1 | **307.2** (307) | −26.001 in 100.0 % | **+41.77** |

The filed 70/161/307 MW series reproduces exactly on caiso-134's defect-window
basis (Sep–Dec, hod 10–15, measured RT ≤ $20). The node-level pricing error is
*larger* than the charter's annual-print comparison: in the very hours the model
dumps at −$26.001, the measured MALIN hub prints +$41 to +$53 median (the
charter's +$26.23 was an annual-basis print). The dump hours are spread across
the day (overnight-heavy), not a belly artifact.

## §B — D2: attribution is exact, and there are TWO defects, not one

Per-hour identities on the committed sidecars (max residual 0.0005 MW):
`dump = firm + midC − flow`, and `flow ≡ corridor cap` in **100.0 %** of dump
hours, all years, both corridors. Split by cause:

| year | corridor | dump TWh | **α: firm capability > cap** | β: negative-hub gaming | dump hrs in collision set |
|---|---|---|---|---|---|
| 2023 | WECC_PNW | 1.086 | **1.086 (100 %)** | 0.000 | 2,774/2,774 |
| 2024 | WECC_PNW | 1.716 | **1.707 (99.5 %)** | 0.009 | 4,079/4,084 |
| 2025 | WECC_PNW | 0.965 | **0.951 (98.6 %)** | 0.014 | 2,769/2,769 |
| 2024 | WECC_DSW | 0.522 | 0.000 | **0.522** | 0/175 |
| 2025 | WECC_DSW | 0.021 | 0.000 | **0.021** | 0/24 |

* **α — the chartered defect.** The `caiso_firm_import_selfschedule` floor
  (pmin = pmax = shaped capability) exceeds the `caiso_corridor_flow_limit`
  cap; the link saturates at the cap and the residual is forced out the Dump
  variable at −dump_cost. With the floor notionally removed the α-dump is zero
  by optimality (every other unit at the node is economic with mc > 0 into a
  dump-priced node; analytic, no solve needed).
* **β — a DIFFERENT defect, filed not chased** (per the charter's D2 clause).
  `dump_cost = max(ε, −min(wind_mc, solar_mc)+ε)` guards only the renewable
  MCs; measured-hub-priced import tranches can go below −dump_cost (Palo Verde
  deep-negative hours), making generate-to-dump profitable. 2024 DSW: 0.522 TWh,
  dominated by `DSW_surplus_clean` (0.816 TWh of tranche output in those
  175 hours). Fix lane: extend the dump-cost formula's min to every negative
  offer that can reach a dumpable node — its own charter.

## §C — charter ask (a), answered: the PNW firm block is NOT real at its energy scale

The floor forces `level × 8760 × eford` of energy; the level is the DMM RA
"Imports" capacity row × MIC corridor split (1,072 / 1,558 / 1,566 MW) — a
**capacity-showing** quantity. Against the corridor's own EIA-930 bytes (same
parquet, same model-clock lag correction, same DIBA grouping the envelope is
built from):

| year | corridor | FORCED firm TWh | model link flow TWh | measured net TWh | measured net-importing-hours TWh |
|---|---|---|---|---|---|
| 2023 | WECC_PNW | **9.20** | 9.35 | **−0.55** | 4.65 |
| 2024 | WECC_PNW | **13.38** | 12.28 | **+2.06** | 5.77 |
| 2025 | WECC_PNW | **13.44** | 12.80 | **+4.73** | 7.05 |
| 2023 | WECC_DSW | 10.74 | 27.08 | 29.39 | 29.77 |
| 2024 | WECC_DSW | 15.56 | 28.41 | 29.37 | 29.81 |
| 2025 | WECC_DSW | 15.50 | 29.56 | 31.20 | 31.54 |

On DSW the firm block sits comfortably inside the corridor's measured energy.
On PNW it alone forces **2–4× the corridor's measured net-importing-hours
energy** (2023's corridor was a net EXPORTER), and the model's northern flow
runs 9.4–12.8 TWh against measured net of −0.5 to +4.7 — a ~1 GW-mean
year-round phantom import that is upstream fuel for the caiso-121/133 +2 GW
defect-window over-import. The dump is only the sliver even the generous
p95-of-net cap cannot admit.

**Why the collision grows**: the shape `w` is the (month × hod) median of the
TOTAL (PNW+DSW) corridor net import — DSW-dominated — applied to a
corridor-split level, while the cap is the corridor's OWN p95. Same source,
two aggregations; internal consistency (median component ≤ p95 of the same
corridor) fails by construction, and the level grew 1,072 → 1,566 MW while the
PNW corridor stayed near-balanced in net.

**Disposition of (a):** the E1-adverse level/shape re-basis (shrinking the
forced cheap import raises CA λ — the mirror of caiso-134 §B's +$14–18 pricing
of corridor tightening) is NOT armed here. It is the upstream lane's object
(caiso-133 §6 / caiso-134's committed-gas hand-back): the ~1 GW phantom
northern import is one more measured face of "the model wants ~2 GW more
import than reality took", and removing the crutch without fixing CA's own
midday supply state fails E1 on its face.

## §D — the composition's missing outlet: the P1 sink deletion (infrastructure defect, FILED)

The per-hub design already contains the correct outlet for un-deliverable firm
energy: a 4,800 MW `WECC_PNW_export_MALIN` sink (pmin −TTC, mc = measured
MALIN − ε) at the node. It is dead in every scored pass:

* `model/commitment.py::caiso_ra_mustoffer_min_gen` returns a **zeros-
  initialised** floor (positive only on bridged gas rows);
* `pipeline/commitment.py::_bridge_floored_fleet` composes it as
  `new_min_gen = np.maximum(base_min_gen, bridge_floor)` — for the sinks
  `max(−TTC, 0) = 0`, deleting the absorption range for the P1 solve (probe §D
  reproduces this on the reconstructed fleet with the real functions);
* the invariant this violates is already documented in the codebase
  (`data/fleet/arrays.py`, the min_gen zeros-init block: *"export sinks
  (pmin < 0 …) must keep their range — a zero floor would pin them off"*).

Consequences, all measured on committed bytes: zero exports in all 26,280
corridor-hours of every CAISO keeper since the RA bridge; caiso-132 §3's
"globally inert" export bound (its D0 is now *explained*, not just measured —
the LP was never able to export, not unwilling); P0 and P1 solve structurally
different economies (P0 has live sinks); and the α-dump has no outlet but the
Dump variable. The mech-tag line (`new_mech[bridge_floor > base_min_gen]`)
also stamps `MECH_RA_MUSTOFFER` on every sink row-hour, though the committed
`legitimacy_diagnostics.json` is unpolluted (import fuel is outside D-2's
scope).

**Why the naive fix is refused here** (probe §E): the CA terminus λ sits below
the measured hub in **20–57 %** of hours (mean positive gap $1.28–8.54/MWh).
A live sink priced hub−ε with bounds beyond the stranded residual U-turns
DELIVERED firm energy — and, through the link, CA supply — out of the market
in every such hour: it voids caiso-77's must-flow semantics (the measured
delivered shape is the mechanism's own evidence base) and fails E1 by
construction. A guarded re-arming (bound = the stranded residual only) prices
the strand at the hub but is exactly tight, so it buys no clean dual and books
phantom energy (§C) as hub resale — rejected in favour of the clip. **Cross-ISO
blast radius, flagged for the owner:** the generic priced-node export sinks
(`import_nodes.py:184/292`, `spec.py:1796`) give PJM/MISO/NYISO/NEISO
negative-pmin rows, and `_bridge_floored_fleet` serves the ERCOT and NYISO
bridges too — any keeper arming a P1-native bridge over a fleet with sinks has
been solving P1 with those sinks deleted. Each ISO's lane re-gates on its own
evidence; nothing is changed for them here (the fix below is CAISO-flag-gated
precisely so no other ISO's keeper recipe shifts).

## §E — the chartered reconciliation: `caiso_firm_import_envelope_clip`

The charter's option (b), its stated strongest prior, is confirmed: the cap is
a correct measured envelope (caiso-133 §5 untouched); the fix is how the floor
is netted against it. The flag clips each firm tranche's shaped capability —
and therefore the floor riding on it — at its OWN corridor's measured
deliverability envelope, inside `inject_caiso_firm_import_shape`
(`envelope_clip=True`):

    capability'[t] = min(level × w[t] × eford, envelope[corridor][t])

* Rule 19 `[R-ONE-MECH]`: a reconciliation of the two existing mechanisms —
  their pointwise min — not a third mechanism.
* Rule 24 / D4: **zero new DOF.** Both series already exist in the model; no
  threshold, no percentile, no margin, no tuned value.
* Rules 13/14/17: both inputs are measured and forward-regenerating; window =
  wherever the corridor's own envelope sits below the shaped block; a year
  with no measured envelope (forecast) is left unclipped — the forward
  analogue is the forward-ATC envelope, to be wired by the forecast lane.
* Pre-solve verification (reconstructed 2025 fleet): the clip equals
  `min(capability, envelope)` to 2e-13; touches exactly the 2,769 collision
  hours (the 2025 dump set); removes exactly the 0.951 TWh α capability;
  changes NO other row; verified no-op on DSW and on an envelope-less year.
* E1/E2 pre-registration: **+$0.00 / +$0.00** — in every collision hour the
  delivered corridor flow is the cap before and after, so the CA-side LP is
  unchanged. (The node's own λ in former collision hours becomes an
  LP-degenerate corner in [−26.001, +28] instead of the strict −26.001 dump
  optimum; the residual gap to the measured MALIN print is the G-26
  static-price limitation, not this lane's.)

## §F — the A/B (arms solved AFTER the prereg was pushed)

Arms: `caiso138_control_A` (keeper recipe, run id `2026-07-29-caiso138-control`)
and `caiso138_envclip_B` (+ the flag, run id
`2026-07-29-caiso138-envelope-clip`), both `--year 2023 2024 2025` in one
invocation, arms sequential. **Control integrity:** arm A is **byte-identical**
to the committed caiso-130 keeper on prices and dumps in all three years
(max |Δ| = 0.0) — which also proves the flag-off code path byte-identical on
the full solve path.

**Every pre-registered gate passed:**

| gate | prediction | result |
|---|---|---|
| P1 α-dump eliminated | PNW dump → β bound (0.000/0.009/0.014 TWh) | **EXACT**: 1.086/1.716/0.965 → 0.000/0.009/0.014 TWh; dump hours 2,774/4,084/2,769 → 0/5/8; DSW β unchanged |
| P2 E1/E2 | +$0.00 / +$0.00 (±$0.02 degeneracy) | **+0.0000 all three years**; max CA per-zone-hour \|Δprice\| = 0.0000 — CA-side LP byte-identical |
| P3 rubric | identical to control | **IDENTICAL** by construction (CA series byte-identical): NOT-YET, fail {C3a-2025, C3c} |
| P4 node print (reported) | degenerate corner, no longer −26.001 | median **+40.79 / +37.46 / +41.83** in former dump hours vs measured MALIN same-hours +52.67/+41.22/+41.77 (was −26.00; 2025 within $0.06 of the measured print) |

The degenerate corner resolved to the import-parity side, so the node-level
pricing error the charter named (~$52/MWh) is closed to $1–12 (the residual is
the G-26 static-price limitation and the remaining β hours). **Promotion:**
owner grant in-session ("if structural integrity improves but gates regress
that may still be a keeper" — here gates do not even regress, they are
byte-identical); keeper shard advanced to `2026-07-29-caiso138-envelope-clip`.
Rule-22 LOYO note: the mechanism carries no fitted parameter and its CA-side
effect is exactly zero in every year — nothing to overfit; the criterion is
satisfied degenerately.

## §G — DO-NOT-REDO (new, binding)

* **Re-measuring the dump, its α/β split, the collision identity, the forced-
  vs-measured corridor energy, or the U-turn arbitrage set.** The committed
  probe carries all of them from committed bytes in seconds.
* **Re-arming the export sinks naively** (fixing `_bridge_floored_fleet`
  unconditionally, or any hub-resale sink bound beyond the stranded residual)
  **as a CAISO lever.** §D/§E: U-turn voids caiso-77 and fails E1 on measured
  gaps of $1.28–8.54/MWh over 20–57 % of hours. The seam defect itself is an
  infrastructure lane with a cross-ISO exposure audit, not a CAISO tuning
  channel.
* **Quoting caiso-132 §3's D0 as evidence the model "does not want" to
  export.** §D: the P1 pass could not export; D0's census stands but its
  interpretation is corrected.
* **Re-deriving the PNW firm level/shape basis (charter ask (a)) as a quick
  fix.** §C: it is real, E1-adverse, and belongs to the upstream CA-supply
  lane with its own LOYO discipline.
* **Treating the β dump as part of this lane.** It is the dump-cost formula's
  blind spot for hub-priced tranches (mc < −dump_cost) — its own charter.

Carried forward unchanged: everything in `FINDING-caiso137b` §6, caiso-137 §7
first bullet, `FINDING-caiso136` §5, caiso-135 §10, caiso-134 §9, caiso-133
§9, caiso-132 §10, caiso-131 §10, caiso-130 §7, caiso-129 §6, caiso-127 §7.

Next number: caiso-139.
