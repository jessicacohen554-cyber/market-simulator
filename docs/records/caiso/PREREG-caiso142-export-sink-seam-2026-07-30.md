# PRE-REGISTRATION — caiso-142 `caiso_p1_export_sink_seam` (single delta, owner-granted structural arm)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document does
not contain cannot be quoted as a pass. Format follows
`PREREG-caiso138-firm-envelope-clip-2026-07-29.md`.

Charter: the caiso-142 session brief (FINDING-caiso140 §E ask A3), plus the
**owner's in-session promotion grant, 2026-07-30**: *"If structural integrity
improves but gates regress that may still be a keeper."* The D-gates were run
first and are recorded in `FINDING-caiso142-export-sink-seam-2026-07-30.md`
(§A–§F) with instrument `scripts/probes/_caiso142_export_sink_basis.py`. **The
D3 price gate FAILED and is not re-litigated here**: this arm is registered on
STRUCTURAL grounds under the grant, and its price prediction is a **regression**.

Keeper at arm time: `2026-07-29-caiso139-dump-guard-offer`
(`results/calibration/caiso139_dumpguard_B`, NOT-YET, fail {C3a-2025, C3c}).

---

## §0 — what the D-gates established, and what this arm is NOT claiming

1. **The defect is real and measured (§A).** `_bridge_floored_fleet` composed
   `max(base_min_gen, bridge_floor)` over a zeros-initialised floor, so both
   priced export sinks (`WECC_PNW_export_MALIN` −4,800 MW,
   `WECC_DSW_export_PALOVRDE` −10,623 MW) had `min_gen = 0` and were pinned off
   in **every scored P1 pass since the RA bridge** — zero exports in all 26,280
   corridor-hours — while **P0 kept the outlet**, so the two passes solved
   structurally different economies. Also: 17,520 spurious `MECH_RA_MUSTOFFER`
   sink row-hours, and the RA bridge's own decommit screen crediting up to
   **15.4 GW** of export absorption the scored pass cannot use.
2. **It is NOT a price lever, and this arm does not claim it is (§C).** An
   absorption column can only ADD demand, so restoring it can only weakly RAISE
   every zonal λ; C3a is an over-price. Both escape channels are measured dead
   (export leg priced below the plateau's marginal-import λ by the corridor's
   own wheel + 2ε — DSW defect p50 +$4.002, night +$0.002, in the money in only
   0.4/8.3/8.4 % of defect hours; the simultaneous interface group binds in **0
   of 26,280 corridor-hours**).
3. **The quantity bound is already armed and measured.** Each corridor group's
   `limit_dn` **is** `measured_corridor_flow_envelope(direction="export")` —
   verified byte-for-byte: DSW mean 177/189/171 MW with **0 MW in
   7,201/7,172/7,260 hours**, PNW mean 1,377/1,110/725 MW. So the restored
   outlet is bounded by the corridor's own **measured export capability**, not
   by the sink's pmin. This is the new evidence that retires caiso-138 §E's
   *"bounds beyond the stranded residual"* objection — the effective bound was
   never the sink's pmin.
4. **The export PRICE basis is measured too HIGH, and that is pre-registered as
   a known bias, not fixed here.** New measurement (this session, on committed
   bytes: EIA-930 CISO BA-to-BA interchange + the committed actual RT LMP + the
   measured hub series): in **real net-export hours** (corridor net < −50 MW)
   the actual CAISO RT clears, against the RAW neighbour hub,

   | corridor | 2023 p50 | 2024 p50 | 2025 p50 | deep export (< −500 MW) p50 |
   |---|---|---|---|---|
   | WECC_PNW (n=4,341/3,224/2,560) | **−3.56** | **−8.30** | **−7.40** | −4.68 / −10.81 / −8.30 |
   | WECC_DSW (n=474/459/405) | **+3.69** | **+4.39** | **+4.49** | +5.20 / +5.60 / +5.09 |

   Reality's PNW export netback sits **$3.6–$10.8 BELOW** the raw hub, and
   reality's DSW exports happen with CA priced **$3.7–$5.1 ABOVE** the raw Palo
   Verde hub. The as-built export leg is `hub − ε` (the WEIM/EDAM
   transfer basis — no OATT point-to-point wheel, the same basis the *import*
   side's `DSW_overnight_clean` / `DSW_daytime_clean` rungs carry, cited to
   FINDING-caiso93 §3/§5 and caiso-94 §2–3 in `CAISO_IMPORT_DELIVERY_BASIS`).
   Against the measurement above that basis is **too generous on both
   corridors**, so this arm will **over-export** relative to reality and its
   price regression is an **UPPER BOUND** on the correctly-priced mechanism's.
   Re-basing the export leg is a SEPARATE charter (a new measured parameter
   needing its own derive script, citation and forward story) and is
   deliberately **not** stacked here — single delta.

   *(This corrects FINDING-caiso142 §E, which called the free wheel-out "an
   asymmetry with no source": the source is the WEIM transfer design, cited in
   the constant block. What the new measurement shows is not an unsourced
   asymmetry but a basis that is measurably too high.)*

## §1 — the delta (ONE switch, zero new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
    results/calibration/caiso139_dumpguard_B \
    --out-dir results/calibration/caiso142_seam_B \
    --set caiso_p1_export_sink_seam=true \
    --note "caiso-142 P1 export-sink seam (single delta)"
```

**Arm A** `results/calibration/caiso142_control_A` — the same replay with **no**
`--set`, same HEAD, same container, same regenerated curated partitions
(`capacity-deliverability`, `hydro-plant-modes`, `confirmed-retirements`,
`transfer-interface-limits`, `ramp-capability` — all curated before either
solve). Expected to reproduce the committed keeper's sidecars; registered as the
run explorer's control arm per rule 15.

Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years sequential
within each run, arms sequential to each other (rule 12 — CAISO is
single-solve-only on this 15 GB box).

**What the flag does** (`pipeline/commitment.py::_bridge_floored_fleet`,
`preserve_absorption=True`, threaded from the CAISO RA path only): the
`pmin < 0` rows are exempted from the bridge floor's maximum-composition, so
each export sink keeps its own lower bound through the P1 solve. Verified
pre-solve on the reconstructed 2025 fleet (§A): **2 rows differ, 0 others**,
`availability` byte-identical, `MECH_RA_MUSTOFFER` sink row-hours 17,520 → 0.
No other ISO's path changes (rule 25 [R-ISO-SCOPE]).

## §2 — pre-registered gates

**P1 — the outlet exists (STRUCTURAL, the arm's reason to exist).** Arm B
exports in a materially nonzero set of corridor-hours; arm A exports in **zero**
(the seam). PASS iff B's export hours > 0 on at least one corridor in every
year, and every exported MW respects the corridor group's measured export
envelope (`|flow| ≤ |limit_dn|` to solver tolerance, no violation).

**P2 — the export volume is inside reality's measured envelope, not beyond it.**
Arm B's per-corridor annual export energy ≤ the corridor's measured
export-envelope energy (`Σ_t limit_dn`), and B's exports are **0 MW in every
hour the envelope is 0** (the DSW corridor's 7,201/7,172/7,260 closed hours).
PASS iff both hold exactly. This is the gate that distinguishes a bounded,
measured outlet from the caiso-138 §E unbounded U-turn.

**P3 — the corridor NET interchange moves TOWARD its measured net (STRUCTURAL,
the named structural-integrity claim).** caiso-138 §C measured a ~1 GW-mean
year-round phantom PNW import: model link flow 9.35/12.28/12.80 TWh against a
measured corridor net of **−0.55/+2.06/+4.73 TWh**. PASS iff arm B's PNW
corridor net interchange moves toward the measured net in **all three years**
(i.e. `|net_B − net_measured| < |net_A − net_measured|`), reported per corridor
with the MW-mean and TWh deltas. This is the falsifiable structural prediction —
a fail here would mean the restored outlet is not doing the thing it is being
promoted for.

**P4 — E1/E2 price: a REGRESSION is predicted and pre-registered as such.**
C3a moves in the WRONG direction (up) in all three years. Pre-registered
ceilings from §D of the finding, on the as-built `hub − ε` basis:
**C3a-2023 ≤ +9.379, C3a-2024 ≤ +7.860, C3a-2025 ≤ +3.865 $/MWh**, and the true
move is expected to be well inside them because the measured export envelope
caps the volume (§0.3) and because those ceilings assume unbounded absorption.
PASS iff every year's realised C3a move is (a) ≥ 0 (up — the sign the
monotonicity argument requires; a *fall* would falsify §C and must be
investigated before any promotion) and (b) **inside** its ceiling. This gate
cannot "pass" in the fit sense; it tests that the model behaves as the structure
predicts.

**P5 — rubric.** Reported, not predicted to improve. C3a-2025 and C3c remain
FAIL. The material risk is that C3a-**2023/2024**, which currently PASS, are
pushed out of band; that count is reported explicitly and is the promotion
decision's main input.

**P6 — no other mechanism moved.** Arm A byte-identical to the committed keeper
on prices and dumps in all three years (max |Δ| = 0.0) — which also proves the
flag-off code path byte-identical on the full solve path. Dump TWh unchanged
between A and B except where an export now substitutes for a dump (reported).

## §3 — promotion rule, fixed in advance

Under the owner's grant, arm B is promoted **iff**:

* **P1, P2, P3 and P6 all PASS** — the outlet exists, is bounded by reality's
  measured capability, moves the corridor net toward its measured value, and
  nothing else moved; **and**
* **P4's sign and ceilings hold** (the regression is the predicted one, not a
  surprise).

Arm B is **NOT** promoted if P3 fails (the structural claim is falsified — then
the mechanism is correct-but-inert-for-the-stated-reason and the arm is a
registered probe), or if P2 fails (an unbounded U-turn, which is caiso-138 §E's
refusal reproduced), or if P4's sign flips (which would falsify §C and require
re-derivation before any promotion).

**Explicitly NOT a promotion criterion:** any improvement in C3a, C3c or the
fail count. None is predicted and none would be attributable to this mechanism.

**Regression accounting, stated in advance.** If C3a-2023/2024 leave their band,
the arm trades **two currently-passing gates** for the structural fix. That
trade is inside the owner's grant as written, and it is reported as a headline
number, never buried — with the §0.4 measurement attached, since the
correctly-priced mechanism would regress less and the re-basis charter is the
named successor.

## §4 — rule compliance

* **Rule 12 [R-PARALLEL]:** arms sequential, years sequential within each arm.
* **Rule 16 [R-ALLYEARS]:** 2023 + 2024 + 2025 in one invocation per arm.
* **Rule 19 [R-ONE-MECH]:** one mechanism — the bridge composition's absorption
  exemption. No second floor, no stacked price change (the export re-basis is
  deliberately deferred, §0.4).
* **Rule 22 [R-DOF]:** zero new free parameters. The restored bound is the
  sink's own pmin, further bounded by the already-armed measured export
  envelope; the price is the measured hub series the injector already writes.
* **Rule 23 [R-HOLDOUT]:** 2023–2025 only; no out-of-training year touched.
* **Rule 25 [R-ISO-SCOPE]:** the exemption is threaded from the CAISO RA path
  only. NYISO is measured exposed (FINDING-caiso142 §F) and re-gates on its own
  evidence; ERCOT is measured NOT exposed (0 interchange rows).
* **Rule 28 [R-MECH-MATRIX]:** the row `caiso_p1_export_sink_seam` exists and is
  re-stamped in the same session as this arm's verdict, whatever it is.
