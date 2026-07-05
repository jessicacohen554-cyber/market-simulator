# FINDING — PJM keeper burndown: the failing legitimacy criteria (2026-07-05)

**Thread:** the pjm-76 keeper (`results/calibration/pjm76_outage_fix`) is
registered but its legitimacy diagnostics return **Overall: FAIL** on
**D-4 off-window binding**, and the extended rubric (statistical-mode /
`docs/statistical-mode-results-2026-07.md`) reports the PJM keeper at 5→7 fails.
**Question (task step 1):** adjudicate the failing criteria with single-year
throwaway diagnostics and separate the **evidence-indicted structural bugs**
(fixable now, grounded) from the **known-open, out-of-scope** residual
(commitment / per-gen reserve, memory-blocked). Three priorities: (a) which PJM
offer-band values survive a physical grounding test vs which are pure residual
artifacts; (b) does PJM CT/CC evening merit show the CAISO sub-SRMC-CC-flood
pattern; (c) does any class show a flat-floor/drag signature — and is the pjm-75
CT drag hinge D-8-stable.

**Method.** Reproduced the pjm-76 recipe for **2024 only** as a throwaway
diagnostic (`scripts/diag_pjm_burndown_2024.py`, `--year 2024`, rule 15 — NOT
dashboard-registered), extracted P1 per-class hourly dispatch, and cross-read it
against: the reliability-floor coefficient CSV + engine code
(`data/raw/reference/reliability_floor_coeffs_PJM.csv`,
`transmission.inject_reliability_floor`), the offer-band overrides
(`scripts/run_pjm74_cc_ct_rebalance.py`, `run_pjm69_interchange_caps.py`), the
pjm-76 D-4 diagnostic, and measured CAMPD pure-play CT_PEAKER hour-of-day CF
(`scripts/diag_pjm_ct_hotday_hod.py`, the same fleet + series
`derive_pjm_ct_netload_drag.py` uses).

---

## The deciding failure — D-4 off-window binding (reliability_floor × CT_PEAKER)

pjm-76 `legitimacy_diagnostics.md` **D-4 FAIL**, all three years:

| year | floor | window | floored_twh | offwindow_share |
|---|---|---|---|---|
| 2023 | reliability_floor × CT_PEAKER | h15-21 | 0.0445 | **0.9911** |
| 2024 | reliability_floor × CT_PEAKER | h15-21 | 0.1392 | **0.9967** |
| 2025 | reliability_floor × CT_PEAKER | h15-21 | 0.1202 | **0.9747** |

**Root cause (mechanism, not fit).** The two ENABLED PJM CT_PEAKER reliability
limbs — `PJM_EMAAC` tmax 33.3 °C floor 0.2838, `PJM_West_APS` tmax 31.7 °C floor
0.3208 — carry **no `start_hour`/`end_hour`**. The engine's own docstring:
"on a flagged day the floor binds for all 24 h" (`transmission.py:2877`,
`3069-3074`). So on a hot day the floor holds CT_PEAKER at ~0.28–0.32 × available
capacity **around the clock**, including overnight when simple-cycle peakers are
physically offline.

**Measured proof it is overnight-phantom (CAMPD, `diag_pjm_ct_hotday_hod.py`).**
On EMAAC design-cooling days (tmax > 33.3 °C, the limb's own gate) the pure-play
PJM CT_PEAKER fleet CF by hour-of-day is:

| block | measured CAMPD CF |
|---|---|
| overnight h0–6 | **0.0165** |
| afternoon peak h15–19 | **0.3757** |

a **23× ratio** — CT commitment on hot days is an afternoon/evening cooling
phenomenon; overnight the class is at ~1.6 % CF (idle). The all-24h floor of
0.28–0.32 over-commits overnight by ~17×.

**Confirmed in the model P1 solve (2024 diag).** CT_PEAKER in the two floored
zones (EMAAC + West_APS):

| condition | model CT_PEAKER MW |
|---|---|
| hot-day overnight h0–6 | **941** |
| non-hot overnight h0–6 (economic) | **34** |
| CAMPD hot-day overnight expectation | ~0 (CF 0.016) |

The floor injects **~907 MW of phantom overnight CT on hot days** — a 28× jump
over the 34 MW economic level, exactly the **0.12 TWh** the D-2 attribution
tags to `reliability_floor × CT_PEAKER` in 2024. **The entire reliability-floor
CT contribution IS the off-window overnight artifact.**

**Why it is a bug by definition (rules 17 + 19).**
- **Rule 17** (no floor without a window/driver/forward story): "a floor binding
  in hours its own driver evidence says the class is offline (CT overnight CF ≈
  0) is a bug by definition, whatever it does to the residual." CAMPD overnight
  CF 0.016 is that evidence.
- **Rule 19** (one mechanism per phenomenon): pjm-75 **added** the CT net-load
  deployment drag (`ct_netload_drag`, `clip(0.01108·netGW − 0.9987, 0, 0.46)`,
  ramp window **[15,22)**) as the CT commitment mechanism **while the
  reliability floor already floored CT_PEAKER** — and never reconciled them.
  In-window [15,22) the drag (up to 0.46) dominates the reliability floor
  (0.28–0.32) via `np.maximum`, so the reliability floor's ONLY marginal
  contribution is off-window overnight (where the drag is 0). The two mechanisms
  are stacked; the residual of the stack is precisely the D-4 failure.

**Fix (implemented).** `config.iso_configs.drop_drag_owned_reliability_specs`:
when `ct_netload_drag` is active it is the single CT_PEAKER commitment mechanism,
so the reliability floor's CT_PEAKER limbs are dropped (reconcile onto the
grounded, forward-native drag — not stack). This is a **floor removal grounded
in CAMPD hot-day CT CF**, not a residual tune; it removes the ~0.12 TWh overnight
phantom and clears D-4. **Zero blast radius:** only CAISO (0 enabled CT limbs →
no-op) and PJM use the drag; ERCOT/NEISO/NYISO/MISO keepers do not set
`ct_netload_drag`, so their bundles are byte-identical (gated on the flag).

---

## Priority (a) — which offer bands survive a physical grounding test

The offer multiplier scales each HR-band's offer = mult × SRMC
(`heat_rate × fuel + vom + carbon`). The **physical floor** for a non-CHP,
non-take-or-pay class is **committed/econ_low ≥ 1.0×** — the LP carries no
no-load/start variable, so PJM Manual-15 composite-cost recovery puts every
above-min increment at ≥ 1.0× full-load AHR fuel cost (the argument pjm-74
already applied to CC_REGULAR econ_low 0.92→1.00). Test each class's
committed/econ_low against that floor and against its physical exemption:

| class | committed / econ_low | grounding verdict |
|---|---|---|
| **CC_REGULAR** | 1.00 / 1.00 | **SURVIVES** — Manual-15 composite-cost floor (pjm-74); at the floor, not below |
| **CT_PEAKER** | 1.05 / 1.05 (econ_high 1.27) | **SURVIVES** — above floor; econ_high 1.27 is the Manual-15 §2.3 10 % cost-cap (pjm-74) |
| COAL_BIT / PRB / LIGNITE / WC | 0.51–0.68 | **SURVIVES on physics** — take-or-pay + must-run: a committed coal unit's *incremental* cost is below full SRMC. (Exact odd-precision values are residual-set *within* the grounded band — a smaller, sanctioned surface.) |
| CC_CHP | 0.6624 / 0.684 | **SURVIVES on physics** — CHP steam-host credit (avoided boiler fuel offsets the electric SRMC) |
| CT_CHP | 0.864 / 0.864 | **SURVIVES on physics** — CHP steam credit |
| **ST_GAS** | **0.4752 / 0.6552** | **FAILS** — non-CHP gas steam boiler offered at 0.48× SRMC. No take-or-pay, no steam credit; at min-load a steam unit's *incremental* HR is **above** full-load, so committed should be **≥ 1.0×**, not 0.48×. Pure residual artifact (odd-precision product of the pjm-59..74 sweep). |
| **CT_INTERMEDIATE** | **0.9 / 0.92** | **FAILS** — non-CHP CT below the SRMC floor. No physical basis for sub-1.0. |

**Proposed re-groundings (NOT re-tunes) — deferred, see below.** Apply the exact
Manual-15 composite-cost floor already on CC_REGULAR to the two indicted classes:
**ST_GAS committed 0.4752→1.00, econ_low 0.6552→1.00; CT_INTERMEDIATE committed
0.9→1.00, econ_low 0.92→1.00.** These are grounded (a physical offer floor,
identical argument to pjm-74), not fitted to a residual. They are **not bundled
into this keeper**: both classes are small (ST_GAS ~15.7 TWh, CT_INTERMEDIATE
smaller), neither drives a scored FAIL (the 2024 aggregate fuel mix is clean —
coal 122.3 vs 122.4, gas 377 vs 391 TWh), and raising their offers shifts all
three years and needs its own regression-logged validation cycle (rule 1/14 —
keep the grounded value even if fit worsens, then root-cause). Task step 1(a)
asked to *propose* re-groundings; they are proposed here and left as the next
model-side step, so this keeper carries **one clean, attributable structural
change**.

---

## Priority (b) — does PJM show the CAISO evening-merit pattern? **No.**

The CAISO finding (`FINDING-caiso-evening-merit-2026-07-04.md`) traced CT being
priced out to an **audit-flagged sub-SRMC CC committed band (0.90×, econ_low
0.95×)** flooding cheap CC around the clock. **PJM does not have that artifact in
its dominant class:** CC_REGULAR committed/econ_low = **1.00 / 1.00** (Manual-15
floor), not 0.90. The model CC_REGULAR still runs a huge ~32–40 GW block every
hour (2024 diag), but that is the **correct LP answer**, not an offer artifact:
CC (HR ~7) is thermodynamically ~30 % more efficient than CT (HR ~10), so CC
dominates on merit exactly as in CAISO — **the same energy-only, ramp-free
structural gap, WITHOUT the sub-SRMC offer bug.**

- CT is **not** "priced out by cheap committed CC"; it is merit-dominated + the
  fast-ramp/local-reliability commitment an energy-only zonal LP can't see —
  which is *precisely* what the `ct_netload_drag` [15,22) floor stands in for
  (and why the redundant reliability-floor CT limb is removable, not needed).
- The sub-SRMC bands that DO exist (ST_GAS, CT_INTERMEDIATE, (a) above) are
  small classes, not the CC flood; they are a grounding hygiene item, not the
  CC/CT merit driver.
- The PJM CC over-run + scarcity-tail miss (0 hours > $200 vs actual 6/18/59)
  is the **known, memory-blocked** per-gen reserve / commitment structural gap
  (`docs/multi-iso/pjm-reserve-ordc.md` Phase 2; P1 warm-start OOM at ~14.6 GB
  on the 16 GB box) — out of scope, not an offer or floor issue.

---

## Priority (c) — flat-floor / drag signatures per class; the CT-drag D-8 verdict

**One class shows a flat-floor signature: CT_PEAKER — and it is the
`reliability_floor`, NOT the `ct_netload_drag`.** The evidence is the D-4 table +
the 941-vs-34 MW overnight measurement above: a floor pinning the class flat
across all 24 h on hot days.

**The ct_netload_drag hinge is clean and NOT the culprit.** It is (i)
window-gated to [15,22) — zero overnight by construction; (ii) net-load-gated —
`clip(...)` zero below the ~90.1 GW knee, so it never fires on a mild day; (iii)
its floored energy (4.70/6.29/7.16 TWh) tracks measured CT (+4/+7/+5 %) and is
year-differentiated. **D-8 stability:** the drag coefficients derive from CAMPD
pure-play CT CF vs EIA-930 net-load pooled 2023–2025, ramp-window Spearman
ρ = **0.50 / 0.51 / 0.60** — monotonic and year-stable; the hinge SSE (0.133)
beats the unclipped ERCOT-recipe line (0.176). The drag is the **grounded**
mechanism; the reliability-floor CT limb is the redundant one stacked on it.

Other classes: COAL / CC_REGULAR / ST_GAS reliability limbs floor all-24h too,
but that is **correct** for them — a coal/CC unit committed for a multi-day heat
event genuinely runs overnight (long min-up), which is why D-4 flags *only*
CT_PEAKER (the fast-start class) and passes the rest. No change to those limbs.

---

## Conclusion — one implemented structural fix, one proposed re-grounding

1. **CT reliability-floor / net-load-drag reconcile (IMPLEMENTED, keeper
   pjm-77).** `drop_drag_owned_reliability_specs` drops the CT_PEAKER reliability
   limbs when the drag is active (rule 19). Clears the D-4 FAIL, removes the
   ~0.12 TWh overnight phantom, zero blast radius. Structural improvement, not a
   fit move (rule 1/17/19).
2. **ST_GAS / CT_INTERMEDIATE Manual-15 committed/econ_low floor (PROPOSED,
   deferred).** Grounded re-grounding of the only two offer bands that fail the
   physical SRMC-floor test; deferred to its own regression-logged cycle because
   it shifts all years and drives no current scored FAIL.
3. **PJM has NOT got the CAISO sub-SRMC-CC-flood pattern** (CC committed at the
   1.0 floor). The CC over-run + scarcity tail are the known memory-blocked
   per-gen reserve gap — not addressable this session.

## Files
- `scripts/diag_pjm_burndown_2024.py`, `scripts/diag_pjm_ct_hotday_hod.py` —
  throwaway 2024 diagnostics (rule 15, NOT registered).
- `src/market_sim/config/iso_configs.py` — `drop_drag_owned_reliability_specs`
  (+ wiring in `scripts/run_calibration.py` `run_year`).
- `scripts/run_pjm77_ct_relfloor_reconcile.py` — keeper candidate (pjm-76 recipe
  verbatim on the fix).
