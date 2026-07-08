# CAISO Gas-CC Belly/Evening Commitment — Model-vs-Actual Probe (2026-07-08)

**Scoped diagnostic (no re-solve, no keeper change).** Grounds the G-15
residual-(a) belly-commitment question — the seam-tz forensics' reattribution of
the C3a body overprice to belly gas commitment
(`results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md` §4.3/§6) —
in model-vs-actual numbers, so the next mechanism is designed against measured
leverage, not a narrative. Reproduce: `python scripts/caiso_belly_commitment_probe.py`.

## Measurement

CAISO gas-CC (CC_REGULAR + CC_CHP) mean online GW, model (`caiso65` keeper
run-payload) vs actual (CAMPD CEMS), by hour-of-day window:

| year | belly h9-15 (model/actual/Δ) | evening h18-21 (model/actual/Δ) |
|---|---|---|
| 2023 | 5.1 / 6.3 / **+1.2** | 8.9 / 10.8 / **+1.9** |
| 2024 | 5.3 / 6.0 / **+0.7** | 8.8 / 10.0 / **+1.2** |
| 2025 | 5.4 / 5.0 / **−0.4** | 8.3 / 8.5 / **+0.3** |

(Δ = actual − model. Model side decoded via
`legitimacy_diagnostics.load_payload_plants`, the same source the committed D-1/D-2
scores use, so this is byte-consistent with the keeper's scores.)

## What it refines vs the FINDING

1. **The belly CC level is already close (within ~1 GW).** The RA must-offer P1
   bridge that G-61 flags for over-committing merchant CC lands the *aggregate CC
   belly output* roughly where reality is (−0.4 to +1.2 GW). The FINDING's larger
   "3.1–5.2 GW more belly gas" figure is the *all-gas* belly (CC + CT + ST) and/or
   the low-price-hour incidence, not the CC diurnal mean measured here — both
   framings are consistent; this one localizes the CC piece.

2. **The bigger, more consistent miss is the EVENING, not the belly.** Model
   under-runs the CC evening ramp by **+1.9 / +1.2 / +0.3 GW** — larger than the
   belly gap in every year. This is the same evening hours where `ct_netload_drag`
   is scaffolding CT commitment (D-2: 59.7% of CT_PEAKER energy) and where the CT
   D-1 shape fails in 2025 (profile_r 0.704). The evening deficit is **shared
   across CC and CT**: reality commits more of *both* into the ramp than the
   energy-only merit order clears.

3. **G-61(b) points the wrong way for the belly.** `caiso_ra_bridge_startup_aware`
   (built, probed as caiso-66) *releases* merchant CC off the belly floor, dropping
   model belly CC further **below** actual in 2023/24 (where Δ is already +0.7/+1.2).
   The measured direction says the belly wants *more* committed CC, not less —
   corroborating the W3a caveat that held caiso-66 back from promotion. Adopting
   (b) on UC-physics grounds (removing phantom sub-min-down P0 runs) must be
   weighed against moving the belly level away from actual; it is **not** a clean
   calibration win.

## Recommended next step (leverage-ordered)

The high-leverage target is the **evening CC/CT commitment**, then the belly
*shape* — one grounded mechanism, replacing the phantom RA-bridge (rule 14/19):

- **Ground the evening + belly gas commitment from measured drivers** (G-15
  residual a). The commitment shape is directly derivable from CEMS (this probe's
  actual series is the target) plus CAISO must-offer / exceptional-dispatch / AS-
  holding records; the driver (net-load / duck-depth) is forward-native (rule 13).
  A measured commitment floor keyed to that driver would (i) hold the evening CC/CT
  the merit order misses — taking load off `ct_netload_drag` (C8/G-15) — and
  (ii) fix the belly *shape* while *replacing* the unconditional RA-bridge (G-61),
  not stacking on it. This unifies C3a/C3b (body λ toward the measured $13–33),
  C1/C4 (CC/CT dispatch), and C8/G-15 (CT over-carry) under one root.
- **Do NOT** adopt G-61(b) as a standalone calibration change first — the belly it
  releases is at/below actual, so it should only land (if at all) *together with*
  the grounded evening/belly commitment that replaces the mechanism it thins.

This probe writes nothing and changes no keeper; it is the measurement gate before
the mechanism build. `scripts/caiso_belly_commitment_probe.py` re-runs it against
any keeper via `--run-id`.
