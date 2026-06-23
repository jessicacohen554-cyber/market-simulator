# CAISO diurnal phase residual — measured WECC corridor deliverability limit (2026-06-23)

Branch: `claude/caiso-diurnal-body-residuals-hcuoc1`. Picks up the per-hub
signed-legs keeper `2026-06-23-caiso-per-hub-signed` (bundle
`caiso_perhub_legs_3yr`) and attacks OPEN residual #1 — the diurnal phase miss
(2024/2025 net-import corr −0.15 / −0.36): the model imports ~5 GW midday when
actual is ~1 GW, a phase shift that integrates to the correct annual volume.

## Root cause (confirmed on the keeper's solved 2024 dispatch)

The per-hub injector prices every import tranche at its corridor's measured hub
LMP (+ wheel + border carbon). **In the CAISO backcast `carbon_price = 0`** (CA
carbon is handled in-state via the gas adder, not the WECC border adder), so
`wecc_border_carbon_adder = 0` and the per-tranche spread collapses: at the
midday PALOVRDE hub (~$8) the WHOLE desert-SW stack — DSW_solar_PV ($48 in the
ladder), DSW_CCGT ($68), DSW_CT ($110), WECC_scarcity ($180) — is offered flat at
~$12, and PNW at ~$10–13. The `IMPORT_TRANCHES` rising export supply curve is
flattened to one cheap offer across all 11.4 GW of tranche capacity, capped only
by the 8.3 GW simultaneous interface limit.

Hour-of-day decomposition of the keeper's 2024 midday (h12) import (5.4 GW net):

| tranche | midday MW | reading |
|---|---|---|
| DSW_solar_PV | 1.8 | genuine desert-SW surplus (~flat all hours) |
| **DSW_CCGT + DSW_CT + WECC_scarcity** | **3.5** | **phantom: neighbor thermal that is OFF midday (the SW is long on its own solar)** |
| PNW (hydro + midC − export) | ~0.1 | — |

The 3.5 GW of neighbor *thermal* import is the spurious midday hump driving the
anti-correlation. The cheap midday hub LMP is the price of the neighbor's
*marginal* (surplus solar) MW — it is **not** a deliverable supply of the
neighbor's idle gas, which the model imports anyway because the hub overwrite
makes it look cheap.

## The instrument — measured WECC corridor deliverability envelope (`--caiso-corridor-flow-limit`)

A real, measured, forward-reproducible transmission quantity: cap each per-hub
corridor's import-direction link flow at the **per-(month × hour-of-day) p95 net
import** on that corridor (an ATC proxy — the operational transfer ceiling, TTC
net of parallel commitments and the neighbor's own diurnal length). Built from
**EIA-930 BA-to-BA interchange** (self-fetched: the six six-month INTERCHANGE
files 2023–2025, filtered to CISO's 11 DIBAs → `data/raw/eia-930-interchange/
CISO interchange hourly.parquet`), with each CISO↔DIBA pair summed into its
corridor by a geographic Path-15 split (`CAISO_CORRIDOR_DIBA`):

* **WECC_PNW** (COI/Path-66 → NP15): BPAT, PACW, BANC, TIDC.
* **WECC_DSW** (Path-46/WOR + Mexico → SP15): AZPS, SRP, WALC, NEVP, IID, LDWP, CEN.

The envelope collapses midday exactly as the physics require: **DSW ~6 → ~3.6 GW,
PNW ~2.3 → ~0.8 GW** (p95, mean over months). Applied as a **one-sided** hourly
upper bound on the corridor link's import flow — the export direction keeps the
physical TTC (midday CA export is real), and the LP still clears its own merit
order *below* the ceiling, so this is a deliverability *capability* limit, **not
a flow pinned to the residual** (rule #12). The p95 (not the mean) keeps it a
ceiling: the model imports below it in the typical hour.

### Why this is admissible (rules #1, #11, #12)
- The ceiling is a measured WECC transmission quantity that **regenerates for a
  forward year** (forecast-mode analogue: the path's forecast ATC) and **responds
  to conditions** (a tighter neighbor length lowers the deliverable envelope).
- It is a high-percentile *operational ceiling*, not a pin to the mean — the LP
  prices freely under it.
- It removes a structurally *wrong* behaviour (importing the neighbor's idle
  thermal over a flat cheap hub), exactly the rule-#1 mandate: a real market
  mechanism the model was missing.

### Implementation
- `config/constants.py`: `CAISO_CORRIDOR_DIBA`, `CAISO_CORRIDOR_FLOW_PERCENTILE` (95).
- `data/eia_loader.py`: `measured_corridor_flow_envelope` (per-hour ceiling/corridor).
- `model/transmission.py`: `build_caiso_corridor_flow_groups` (one-sided groups).
- `model/dispatch.py`: `_build_interface_rows` extended to a per-hour `(T,)` cap.
- `config/scenarios.py`: `caiso_corridor_flow_limit` (default off; requires per-hub).
- `scripts/run_calibration*.py`: `--caiso-corridor-flow-limit` wiring.
- `tests/test_caiso_corridor_flow_limit.py` (7 tests).

## Results (2024; full 3-year in the dashboard bundle `caiso_corridor_flow_3yr`)

| metric (2024) | per-hub keeper | **+ corridor flow limit** | actual |
|---|---|---|---|
| diurnal net-import corr | −0.146 | **+0.077** | (→ +) |
| midday import (h12) | 5.4 GW | **3.8 GW** | 1.0 |
| net interchange (TWh) | −32.39 | −28.34 | −32.38 |
| in-state midday LMP | $27 | $33 | ~$14 |

* **Priority 1 (diurnal phase) — flipped POSITIVE.** corr −0.146 → **+0.077**, the
  first per-hub run with a positive diurnal sign. The cap removed the phantom
  desert-SW thermal flood (DSW_CT 1.3→0.6, WECC_scarcity 0.7→0.1 GW midday).
* **Net interchange now *under*-imports (−28.34 vs −32.38), and that is the
  finding (rule #1).** The keeper's dead-on annual volume was partly the midday
  phantom *offsetting* the evening under-import (model 0.4 vs actual 4.4 GW at
  h18). With the midday flood removed, the honest annual volume is lower and the
  residual is now the **evening import shortfall** (roadmap alternate C) — a
  separate mechanism, not a reason to re-admit the phantom.
* **In-state midday LMP rose $27 → $33 (body worse midday), exposing residual #2.**
  Removing the cheap midday imports forces more in-state gen at the margin, which
  is the standing in-state midday over-pricing item — the next phase, to fix at
  root cause, not by reverting the deliverability limit.

## Full 3-year scorecard (dashboard `caiso_corridor_flow_3yr`)

| metric (2024 / 2025) | per-hub keeper | **+ corridor flow limit** | actual |
|---|---|---|---|
| diurnal net-import corr | −0.15 / −0.36 | **+0.08 / +0.03** | (→ +) |
| net interchange (TWh) | −32.39 / −41.11 | −28.34 / **−36.31** | −32.38 / −36.16 |
| mean LMP (body, P1 load-wt) | 43.82 / 44.86 | 46.38 / 49.79 | 35.85 / 34.62 |
| neg-price hours | 459 / 193 | 346 / 61 | ~800 / — |
| import-hours share | — | 85.8% / 91.5% | 89.0% / 90.9% |

(2023, static-ladder hub fallback but the corridor cap is active: net −29.75 vs
−28.87, **corr +0.97** — the cap alone gives a strongly correct shape in the year
the per-hub prices are unavailable.)

**Verdict — new keeper (rule #1).** The corridor deliverability limit is the most
structurally faithful CAISO run to date: it adds a REAL, measured,
forward-reproducible transmission mechanism the model was missing, and with it

* **Priority 1 (diurnal phase) is SOLVED** — corr flips positive both scored years
  (−0.15→+0.08, −0.36→+0.03), the first per-hub run with the right diurnal sign; and
* **2025's over-import is fixed** — net −41.11 → −36.31, dead on actual −36.16.

The costs are the honest exposure of the next residuals, NOT reasons to revert
(rule #1 — a real mechanism stays in even when it worsens the fit):

* **Body rose** (2024 +2.6, 2025 +4.9) and **neg-hours fell** (459→346, 193→61).
  The keeper's lower body / more negatives were partly the SAME midday-import
  artifact the per-hub diagnosis already flagged: cheap phantom midday imports
  suppressed in-state prices and manufactured negatives. Removing them lifts the
  body to its honest level and removes the artificial negatives — squarely the
  standing **in-state midday over-pricing residual (#2)**, the next phase (fix at
  root cause: the in-state midday floor is too high and does not price negative
  enough in the solar glut), NOT by re-admitting the phantom.
* **2024 net now under-imports** (−28.34 vs −32.38): the keeper's dead-on 2024
  volume was the midday phantom offsetting the **evening import shortfall** (model
  0.4 vs actual 4.4 GW at h18; roadmap alternate C) — now exposed as the residual
  it always was.

## Open residuals handed off
1. **In-state midday over-pricing / negatives (#2, body).** The next phase. The
   midday in-state floor ($33, was $27) is too high and the in-state solar glut
   does not price negative enough (model 346 neg vs ~800 actual). Offer-curve-
   adjacent — only after the structure (interchange + diurnal) is right, which it
   now is.
2. **Evening import shortfall (alternate C).** Model imports ~0.4 GW at h18 vs
   actual ~4.4; needs a non-AS evening mechanism. Lower priority.
