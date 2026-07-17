# FINDING — ERCOT-79 availability-envelope audit: the CAMPD phantom-outage bug and the scarcity-tail co-dependency (2026-07-17)

**Status: fix-or-ledger → LEDGER (isolated fix inadmissible).** A real input bug
was found and fixed; correcting it resolves the 2023 summer over-shoot but
un-catches the real scarcity tail, because the model's ERCOT scarcity
calibration is co-dependent on the phantom fleet tightness. Disposition pending
owner decision (keeper standing / re-calibration successor lane).

## The charter (ERCOT-78 successor)

The 2023 summer over-shoot is 58 event-afternoon hours (29 Jun + 29 Sep 2023,
hod 12-20, net-load p90+) where the keeper prints lw mean **$1,068** vs actual
RT **$421**, because the multi-product co-opt sits deep in its ORDC steps while
measured reality held 6-9 GW online reserve capability (NP6-905 RTOLCAP p50
7,541 MW; RTORPA p50 $1.4). ERCOT-78 named the gap as the event-time
availability/capability envelope and chartered this input audit (rule-14 input
side; a room-pin to measured RTOLCAP is pre-registered forbidden).

## Leg 0 — baseline reproduced

`replay_keeper.py` on `ercot76_ne_import_fullspan` → `_ercot79_keeper_replay`.
The pre-registered `_ercot78_summer_anatomy.py` reproduces the exact 58h set to
the decimal (29 Jun + 29 Sep, hod 12-20, w_CC 0.05, RT $421.0, model lw $1,068.2,
$-mass 37,541). Set-and-C3 byte-parity confirmed.

## Leg 1 — the input audit: the phantom-outage bug (CONFIRMED)

Per-class ledger on the 58h set (`_ercot79_availability_ledger.py`), model
`pmax×availability` vs measured CAMPD online envelope
(`derive_ercot_rtolcap_forward._class_hourly`) vs model dispatch:

| | model | measured |
|---|---|---|
| available capability | 58,408 MW | online_cap 54,880 |
| dispatch | 54,509 MW | online_gross 51,754 |
| **room** | **3,899 MW** | **RTOLCAP-thermal 6,632** (NP6-905 p50 **7,541**) |

The room gap is a **dispatch gap** (model runs 2.75 GW more thermal), traced to
a capability shortfall in cheap classes forcing gas up. **Root cause: the CAMPD
facility-outage detector manufactures phantom outages for daily-cycling
combined-cycle plants.**

`scripts/derive_campd_outages.py::detect_outages` marks a generation run
"available" only when it sustains CF > `REAL_RUN_CF` (5%) for ≥
`MIN_REAL_RUN_HOURS` (**24 consecutive** hours). A CC unit that runs the
afternoon peak and shuts overnight never accumulates 24 consecutive above-5%
hours, so its whole operating season folds into one "outage." The shared
`filter_revealed_outages` then *keeps* it (the summer-long span trivially
overlaps ≥ `min_inmerit_hours` high-load hours) — never checking whether the
unit was actually down. `fleet.py` applies the window as a hard
`availability = 0` on every tranche.

**Smoking gun — T H Wharton (ORIS 3469, 1,190 MW CC_REGULAR):** derived window
2023-06-21 → 2023-11-10 (3,404 h) zeros it across the entire summer, while its
own CEMS shows it generating 1,105 h at up to 813 MW. Independently verified on
the exact 58h set: **1,904 MW/h mean (peak 4,299)** of proven-online capability
deleted from plants demonstrably generating (`verify_phantom_58h.py`). It is a
**detector logic bug, not stale data** — re-running the detector on the current
on-disk CEMS reproduces the phantoms.

## The fix (source-faithful, rule-13/14/23 admissible)

`scripts/derive_campd_outages.py`, two changes, keyed only on measured CAMPD cf
+ EIA-930 net load (no price/MWh residual):

1. **Event-based detection for the daily-cycling classes** (CC_REGULAR, CC_CHP,
   CT_CHP, CT_PEAKER — `EVENTBASED_CYCLING_GROUPS`), the same rule ST_GAS
   already uses: any hour the unit runs (cf ≥ `REAL_RUN_CF`) breaks the outage
   window, so daily cycling produces no window and a genuine dead-stop stays a
   window. This also prevents a genuine outage EMBEDDED in a cycling season from
   being merged away.
2. **Revealed-availability filter**: a down span is kept only where the unit was
   actually DOWN during its high-net-load hours, not merely overlapping them.

**Validated on source data (no LP):** 58h-set false-outage **1,904 → 0 MW/h**;
over-correction (genuine ≥5-day dead-stops dropped) **0%** (all genuine outages
— Petra Nova mothball, Sandy Creek, Victoria, Frontera — preserved). Outage
tests pass (the one NEISO failure is pre-existing and unrelated).

## Re-solve result — the over-shoot is fixed, the tail collapses

Full-span 2023-2025 replay with the corrected detector (`_ercot79_fix2`), single
delta vs the keeper:

* **2023 summer over-shoot: $1,068 → $242** (actual $421) — invented Jun/Sep
  prints collapse (Jun inv 20→1, Sep 10→0). The ERCOT-78 diagnosis is confirmed:
  the over-shoot is phantom-driven.
* **But the real scarcity tail is un-caught.** 2023 C3c 179 → **53h** (actual
  181; FAILS the [0.5×,2×] band floor of 90). Aug caught **71 → 25**; 2025 tail
  **19 → 0**. On 46 real-scarcity Aug hours (actual RT $1,131) the model fell
  from $767 → **$78**. Of 126 hours dropped below $200, 71 were real scarcity
  (correctly-caught events now missed), 55 were invented.

The clean fix (fix2, 0% over-correction) collapses the tail *identically* to a
first-pass over-aggressive fix (fix1: tail 49, Aug caught 25), so the collapse
is a genuine structural finding, not an artifact of over-removal.

## Adjudication

The phantom-outage fix is **correct** (validated) and resolves the over-shoot,
but it is **inadmissible in isolation** (fails the pre-registered Aug caught-set
and C3c guards) because **the model's ERCOT scarcity pricing rests on the
phantom fleet tightness**: the phantom outages simultaneously (a) invent the
Jun/Sep shoulder over-shoot and (b) supply the fleet tightness that lets the
co-opt price the real August scarcity. Remove them and the co-opt has too much
room to price scarcity at all — a single availability mechanism, both effects.

Per rule 11 (prefer the accurate input; a worse fit signals a compensating
miscalibration elsewhere), the fix should be kept and the **real root cause**
pursued: the ERCOT offer/scarcity calibration (offer curves, ORDC/co-opt) was
tuned against a phantom-tightened fleet and must be **re-calibrated against the
corrected availability envelope**. That is a large successor lane, not this
audit.

**Ledger:** the 2023 summer over-shoot is a phantom-availability input-bug
artifact entangled with the scarcity-tail calibration; the isolated input fix is
out-of-admissible-representation for a single-lane keeper. Successor lane: ERCOT
scarcity re-calibration on the corrected fleet.

## Owner decisions (flagged, not acted)

* **The frontier is NOT final for a clean close.** This lane converts ERCOT-78's
  "one open chartered lane" into a named successor (scarcity re-calibration on
  corrected availability) rather than a clean fix or clean ledger.
* **Adopting the fix** (regenerating `data/raw/campd-outages.csv` via the
  corrected `derive_campd_outages.py`) breaks the current keeper's reproducibility
  — its scarcity tail was solved on the phantom basis — and requires re-calibrating
  the ERCOT keeper. The corrected detector CODE is committed; the committed csv is
  left at the keeper's historical (phantom) basis pending that decision.
* The same detector bug affects every ISO's outage derivation (the detector is
  shared); each ISO's csv regen + re-calibration is its own lane.

## Files

* `scripts/derive_campd_outages.py` — the detector fix (committed).
* `scripts/probes/_ercot79_availability_ledger.py` — the per-class availability
  ledger (committed).
* Bundles `_ercot79_keeper_replay` (baseline), `_ercot79_fix` (fix1,
  over-corrected), `_ercot79_fix2` (clean fix) — throwaway, not committed.
* Regenerated `data/raw/campd-outages.csv` — NOT installed (keeper preserved);
  regenerable via `python scripts/derive_campd_outages.py --iso ERCOT --years
  2022 2023 2024 2025 2026`.
