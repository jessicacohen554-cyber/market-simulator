# PRE-REGISTRATION — caiso-138 `caiso_firm_import_envelope_clip` (single delta)

**Written and committed BEFORE arm B was solved.** No B-arm result existed when
this document was frozen. Gates below are final — a gate this document does not
contain cannot be quoted as a pass. Format follows
`PREREG-caiso130-hydro-budget-nameplate-aware-2026-07-27.md`.

Charter: the caiso-138 session brief (the caiso-134 §2 WECC_PNW firm-hydro dump
observation). The D-gates D1–D4 were passed on committed bytes before any solve;
the full derivation is `FINDING-caiso138-pnw-firm-dump-2026-07-29.md` (§A–§E)
and its committed instrument `scripts/probes/_caiso138_pnw_firm_dump.py`.

---

## §0 — what the D-gates established (no solve)

1. **D1.** The dump is confirmed and larger than filed: annually **1.086 /
   1.716 / 0.965 TWh** (means 124/196/110 MW) at `WECC_PNW`; the filed
   70/161/307 MW series is the caiso-134 defect-window mean and reproduces
   exactly (70.2/160.9/307.2). Node λ = **−26.001 in 100.0 %** of dump hours;
   measured MALIN in the SAME hours prints **+52.67 / +41.22 / +41.77** median.
2. **D2.** Attribution is exact: the α component (firm shaped capability >
   corridor cap, per-hour identity `dump = firm + midC − flow`, `flow ≡ cap` in
   100 % of dump hours) carries **100 / 99.5 / 98.6 %** of the PNW dump energy.
   The β remainder (economic tranches whose measured-hub mc < −dump_cost
   generate-to-dump; 0.009–0.014 TWh at PNW, 0.522/0.021 TWh at DSW in
   2024/2025) is a **different defect** (the dump-cost formula guards only
   wind/solar mc) — filed, not chased here.
3. **Root mechanism.** The floor's shape `w` is the TOTAL-system revealed
   profile while its level is corridor-split (DMM RA-import × MIC), so on the
   near-balanced PNW corridor `level × w` exceeds the corridor's own p95
   net-import envelope in a growing bucket set (level 1,072 → 1,566 MW). The
   forced PNW firm energy is **9.20 / 13.38 / 13.44 TWh** against a measured
   corridor net of **−0.55 / +2.06 / +4.73 TWh** (net-importing hours only:
   4.65/5.77/7.05) — charter ask (a) is answered NO at the energy level, and
   the E1-adverse level/shape re-basis is handed to the upstream lane, not
   armed here.
4. **Composition.** The design's own outlet for stranded firm energy — the
   4,800 MW `WECC_PNW_export_MALIN` sink priced MALIN−ε — is **deleted in the
   scored P1 pass** by `pipeline.commitment._bridge_floored_fleet`
   (`np.maximum(base_min_gen, bridge_floor)` with a zeros-initialised floor:
   max(−TTC, 0) = 0), reproduced by the probe §D on the reconstructed fleet.
   Re-arming it naively is REFUSED: the terminus λ sits below the measured hub
   in 20–57 % of hours (mean positive gap $1.28–8.54/MWh), so an unguarded
   sink U-turns delivered firm (and CA supply) out of the market, voiding
   caiso-77's must-flow semantics and failing E1. Filed as an infrastructure
   defect with cross-ISO blast radius (any ISO with negative-pmin sinks and an
   armed P1-native bridge — the generic priced-node sinks of
   `import_nodes.py`/`spec.py` qualify); its fix is its own lane.

## §1 — the delta (ONE switch, one reconciliation, zero new free parameters)

**Arm B** = the keeper recipe replayed at this session's HEAD **plus the single
flag**:

```
PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
    results/calibration/caiso130_nameplate_B \
    --out-dir results/calibration/caiso138_envclip_B \
    --set caiso_firm_import_envelope_clip=true \
    --note "caiso-138 firm-import deliverability clip (single delta)"
```

- **Arm A** `results/calibration/caiso138_control_A` — keeper recipe, no
  delta, same HEAD, same container, same regenerated
  `capacity-deliverability` and `hydro-plant-modes` partitions (both curated
  before either solve). Expected to reproduce the committed keeper sidecars;
  registered as the run explorer's control arm per rule 15.
- Both arms `--year 2023 2024 2025` in ONE invocation (rule 16), years
  sequential within each run, arms sequential to each other (rule 12 — CAISO
  is single-solve-only on this 15 GB box).

**What the flag does** (`model/interchange/caiso.py::inject_caiso_firm_import_
shape`, `envelope_clip=True`): each firm tranche's shaped hourly capability —
and therefore the caiso-77 must-flow floor riding on it — is capped at its OWN
corridor's measured deliverability envelope, the same
`measured_corridor_flow_envelope` series `caiso_corridor_flow_limit` caps the
link with. Verified pre-solve on the reconstructed 2025 fleet: the clip equals
`min(capability, envelope)` to 2e-13, touches exactly the 2,769 collision
hours, removes exactly the 0.951 TWh α-dump capability, changes NO other row,
and is a verified no-op on the DSW block and on an envelope-less forecast year.

- **DRIVER (rules 13/14/17)**: both inputs are existing measured series (DMM
  level × 930 shape; 930 p95 envelope). The clip is their pointwise min — a
  deliverability statement, not a fit. Window = wherever the corridor's own
  envelope sits below the shaped block; forward story = the envelope
  regenerates per year (forecast years unclipped until the forward-ATC
  analogue is wired in the forecast lane).
- **DOF added: zero** (rule 24). No threshold, no percentile, no tuned value.
- **Rule 19**: reconciles the two colliding mechanisms; no third mechanism.

## §2 — pre-registered predictions and gates

- **P1 (primary, kill if missed).** Arm B's `WECC_PNW` α-dump = **0** in all
  three years (residual dump at PNW ≤ the β bound 0.000/0.009/0.014 TWh;
  DSW's β dump unchanged within ±10 %). The caiso-134-window dump mean falls
  from 70.2/160.9/307.2 MW to ~0.
- **P2 (E-envelope, kill if missed).** CA demand-weighted annual LMP move vs
  arm A: **2025 ≤ +$0.00** and **2024 ≤ +$0.30** (ask memo caiso-131 §2 E1/E2).
  Point prediction: **+$0.00 both**, because in every collision hour the
  delivered corridor flow is the cap before and after (CA-side LP unchanged);
  tolerance for LP degeneracy noise ±$0.02.
- **P3 (rubric).** Arm B's C-gate rubric is IDENTICAL to arm A's (C1/C2/C3b/
  C4/C7/C8 PASS, C3a-2025/C3c fail set unchanged, determination NOT-YET).
  Any scored-gate flip vs arm A in either direction is a stop-and-report.
- **P4 (reported, not gated).** The node price in former collision hours: the
  strict −26.001 dump optimum is gone; the realized print is reported as
  found (the corner is LP-degenerate in [−26.001, +28] and the residual gap
  to the measured MALIN print is the G-26 static-price limitation, not this
  lane's).
- **Control integrity.** Arm A reproduces the committed keeper's scored
  metrics; a material arm-A drift vs the keeper is investigated before any
  B-arm claim is made.

Promotion is NOT pre-granted: if P1–P3 hold, the flag is a keeper CANDIDATE
and promotion (with rule-22 LOYO on the mechanism change) is a separate owner
act. Whatever the verdict, both arms are registered on the dashboard (rule 15)
and the `caiso_firm_envelope_clip` matrix cell is stamped in this session
(rule 28 duty b).
