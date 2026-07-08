# CAISO ST_GAS Overnight Drag + CT_PEAKER Reconciliation (2026-07-08)

**Status: SHIPPED DISABLED — no admissible CAISO ST_GAS overnight driver; keeper
stays `caiso65`.** Ports the PJM extreme-day steam-gas overnight pre-positioning
drag (`scripts/derive_pjm_st_gas_overnight_drag.py`, branch
`claude/steam-gas-min-duration-0ngvto`) to CAISO for both ST_GAS and CT_PEAKER.
The derivation runs on CAISO's own fleet/weather/net-load (rule 24), applies the
identical honesty gate, and finds the overnight signal inadmissible on a
collapsing, evening-peaked ST_GAS fleet. The CT_PEAKER phenomenon is already
reconciled onto the active `ct_netload_drag`; no second mechanism is added.

## 1. What shipped

- `scripts/derive_caiso_st_gas_overnight_drag.py` — reproducible derivation,
  mirroring the PJM script (overnight window h0-6, `min_stable_pct` 0.12, steam
  `min_event_hours` 48, honesty gate ρ≥0.3 / n≥30 / commit_frac>baseline_commit).
- `data/raw/reference/reliability_floor_coeffs_CAISO.csv` — the old all-day SP15
  ST_GAS `tmax`/`tmin` limbs are REPLACED by three overnight-windowed limbs
  (`tmax`/`tmin`/`netload`), all `enabled=False` and VISIBLE (rule 12). A
  `threshold_percentile` column is appended (CAISO already carried
  `start_hour`/`end_hour`); every non-ST_GAS row is byte-verbatim. Other ISOs
  untouched.

## 2. The ST_GAS derivation result — DISABLED (correct null)

Pooled 2023-2025 (rule 16), CAISO ST_GAS = 3 SP15 plants (315/335/350), 2,859 MW,
legacy coastal once-through-cooling steam:

| driver | thr | ρ | n | commit_frac | baseline_commit | floor_pct | enabled |
|---|---|---|---|---|---|---|---|
| tmax    | 26.7 °C  | 0.123  | 56  | 0.290 | 0.126 | 0.0348 | **False** |
| tmin    | 5.66 °C  | −0.319 | 10  | 0.088 | 0.135 | 0.0105 | **False** |
| netload | 27.58 GW | 0.221  | 329 | 0.225 | 0.096 | 0.0270 | **False** |

Every limb fails the ρ≥0.3 gate (tmin also fails n and commit_frac). The magnitude
side is real-ish (tmax/netload commit_frac > baseline_commit) but the
**driver→commitment correlation is too weak to be admissible**.

**Why (the honest fleet picture).** CAISO ST_GAS is tiny and collapsing —
measured CAMPD energy **1.04 → 0.08 → 0.05 TWh (2023/24/25)** — and even in its
only active year (2023) it is **evening-peaked, not overnight-held**: diurnal CF
runs ~0.02-0.03 in the overnight window (h0-6, its trough) and peaks ~0.07 at
h18-20. The class does not pre-position overnight to catch the next peak; when it
runs it runs *at* the peak. An overnight floor there would bind in hours the
class's own driver evidence says it is offline — a rule-12 bug by definition. On
the mandated pooled derivation the near-dead 2024/25 years drive ρ below the gate,
which is the correct signal. **Forced overnight energy = 0.0% of class energy in
all three years** (rule 20, trivially clear — nothing is forced).

This is the outcome the task anticipated: *"if the overnight signal is too thin,
ship disabled and say so honestly rather than manufacturing a floor."* The
disabled limbs remain in the CSV so a future data update (rule 23) re-derives
them automatically if the fleet behaviour ever changes.

## 3. CT_PEAKER — reconciled, NOT stacked (rule 14/19)

D-2 enumeration of every mechanism that floors CAISO CT_PEAKER at the keeper
(`caiso65`) config — one mechanism per phenomenon holds, nothing to add:

| mechanism | status | CT_PEAKER role |
|---|---|---|
| `ct_netload_drag` (h15-22, `frac=clip(slope·netGW+intercept,0,cap)`) | **ON** (CAISO default) | the SOLE live CT commitment mechanism (duck-curve evening ramp) |
| reliability_floor CT netload limbs (h15-21) | `enabled=False` in the CSV **and** code-dropped by `drop_drag_owned_reliability_specs` whenever the drag is on | 0 |
| `caiso_ra_mustoffer` P1 bridge (frac 0.26) | ON | floors CC, no CT attribution in D-2 |
| RA startup bridge | physics-gated (min-down ≥ 4 h); fast-start CTs never bridge | <0.4% |

The CT_PEAKER evening window is already correct (h15-22 in the drag / h15-21 in
the retired CSV limbs) — it is NOT overnight, avoiding the rule-12 trap the ST_GAS
window walks into. The drag-vs-reliability_floor choice for CT is **already
settled** by the D-8 closure A/B (`docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md`
§6): the ramp+LCR arm failed criterion (i), so `ct_netload_drag` STAYS as the most
structurally faithful available CT mechanism (rule 1), G-15 open. This change does
**not** reopen that; it only refreshes the ST_GAS rows and leaves the CT rows
byte-verbatim.

## 4. Effect on the keeper — byte-identical

The set of ENABLED CAISO reliability_floor limbs is `[]` both before and after
this change (every CAISO limb was already disabled; the ST_GAS limbs remain
disabled). With `ct_netload_drag` on, CT_PEAKER limbs are dropped regardless. So
`inject_reliability_floor` is a no-op for CAISO in both states → the reliability
floor injects the same (empty) `min_gen` → the CAISO keeper solve is **provably
byte-identical to `caiso65`**. The keeper stays `2026-07-07-caiso65-seam-envelope-clock`;
no promotion, no new DOF, no re-tune. A full 2023-2025 re-solve would reproduce
`caiso65` exactly.

## 5. Rule ledger

- **1 / 11:** structure-first; a real behaviour would stay even if it hurt the fit —
  but here there is no real overnight behaviour to keep (evidence says the class is
  offline overnight), so nothing is forced.
- **12:** floor needs a window + driver + forward story; the overnight window has no
  admissible driver on this fleet → disabled + visible.
- **13:** trigger (temp/net-load) and magnitude (physical Pmin) are forward-derivable
  and condition-responsive; nothing pinned to a measured outcome.
- **14 / 19:** one mechanism per phenomenon — ST_GAS limbs are the only ST_GAS
  mechanism (`gas_st_netload_drag` off); CT_PEAKER stays drag-owned, no stacking.
- **16 / 22:** derived pooled across 2023-2025 (train only; CAISO has no
  calibration-complete marker, holdouts quarantined).
- **20:** 0.0% forced overnight ST_GAS energy — trivially within budget.
- **23:** coefficients re-derive only on CAMPD/EIA-930/EIA-860 source updates.
- **24:** CAISO's own fleet/weather/net-load; nothing crosses ISO boundaries.
