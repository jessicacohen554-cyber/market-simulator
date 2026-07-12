## 2026-07-12 — ERCOT-60: thread-1 of the storage-cycling lane adjudicated — the ERCOT-59 release scale is CORRECT (measured-data-only, no solve); ~96% of the remaining ~2.0 TWh battery-throughput gap lies OUTSIDE the AS-release window and is incentive-bound; next lever filed as the binding-regime ST_GAS drag-floor level (the ERCOT-58 §5 thermal lane)

**Task (this session, the ERCOT-59 filed forward path (a)).** Investigate why
the `ercot_storage_as_deployment` released draw-down (~20–100 MW mean) is small
against the 1.2–2.8 GW measured award: gate too conservative, or scale correct
and the +2.4 GW binding-regime thermal excess needs a different mechanism?

**Method: measured data only, zero solves.** The 60-Day DAM by-restype award
series, the EIA-930 2025 battery series, and the keeper's committed
`legitimacy_diagnostics.json` — full workings appended as §7 of
docs/DIAGNOSIS-ercot-storage-cycling-lane-2026-07.md.

**Determination: the scale is CORRECT; the mechanism stays exactly as built.**

* Window decomposition of the 2025 measured-vs-keeper gap (§7.1): evening
  up-ramp hod 17–20 — the only window where AS-award release is physically
  justified — is already ~closed (+0.09 TWh). The morning ramp (+0.77), daytime
  (+0.91) and late night (+0.27) carry ~1.95 of the ~2.0 TWh gap, and in each
  the construction is structurally zero (award RISING all morning — procurement
  follows load) or dishonest (post-peak award decline is procurement shape;
  measured discharge falls to 465/202/184 MW at hod 21–23 while the ungated
  draw-down grows to 2.2–2.5 GW — forcing it is the loose-gate shape failure
  ERCOT-59 already rejected, hourly r 0.807→0.630).
* Binding-hour ceiling: even UNGATED, the cummax draw-down at top-30 % net-load
  hours averages 263 MW (2023) / 626 MW (2025) — no honest variant reaches the
  +1–2 GW the binding regime misses. Loosening the gate is residual-fitting on
  a window the driver evidence contradicts (rules 1/11/12): NOT done.
* The gap is incentive-bound, not reservation-bound (§7.2): ~11 GW of free
  non-AS battery capacity at the 2025 morning ramp against ≤1 GW measured
  discharge; 2023 binding hours ~2.4–2.7 GW free against the model's 145 MW.
  The binding constraint is the flat modelled spread — the ERCOT-58 §4 circle.
* **Rule-13 dead end recorded:** no admissible measured input exists for a
  morning/daytime discharge floor — the PRC morning dip is not
  battery-specific, and the EIA-930 battery series is the outcome being
  validated (pinning dispatch to it is forbidden). The morning/daytime energy
  must come endogenously from price formation.

**Filed forward path (sharpened).** (a) Next lever = the binding-regime thermal
side, ST_GAS first: keeper D-2 shows `st_netload_drag` forcing 4.96/5.70/4.97
TWh (25/33/31 % of class energy 2023/24/25) under an all-hours window while
ERCOT-58 §4 measured ST_GAS +1.3 GW at top-30 % net-load hours vs CAMPD (D-1
diurnal r 0.97–1.00 passes — a binding-hour LEVEL excess, not shape). First
probe: 2023 throwaway masking which binding-hour ST_GAS MWh sit ON the drag
floor vs above it economically — decides whether the defect is the hinge's
high-net-load extrapolation (derived from overnight CF) or the offer curve
above it. (b) The ERCOT-58 v3 realized-room RTORPA re-probe stays parked (gap
narrowed only ~0.23 of ~2.0 TWh). (c) The C5c monthly-shape residual remains a
separate untouched root-cause item.

**Holdouts / governance.** No solve, no scoring, no registration, no intake —
analysis touched 2023–2025 measured inputs already in-repo (rule 22 clean).
No parameter, offer curve, floor, or derive script changed (rules 13/21/23/24);
`ercot_storage_as_deployment` and its gate byte-identical; keeper stays
`2026-07-10-ercot56-nucwin`; dashboard unchanged (no run produced — rule 15
N/A).
