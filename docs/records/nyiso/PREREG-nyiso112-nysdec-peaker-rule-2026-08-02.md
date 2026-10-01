# PRE-REGISTRATION — nyiso-112: restore the NYSDEC 227-3 peaker-rule availability overlay, single delta `nysdec_peaker_rule_availability=True`

**Date:** 2026-08-02 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16
`[R-ALLYEARS]`, one bundle) · **Committed and pushed BEFORE the arm solved.** ·
Keeper under test: `2026-08-01-nyiso109-zonal-margin-anchor`. Control: the same
`results/calibration/nyiso111_control_A` zero-delta control the nyiso-111 arm is
scored against (two independent single-delta arms off one control — neither is
stacked on the other).

---

## §1 — what this is, and why it is OFF-QUEUE with cause

**Lever:** `ScenarioConfig.nysdec_peaker_rule_availability = True` — the curated
unit-level NYSDEC **6 NYCRR Subpart 227-3** ("peaker rule") ozone-season
compliance overlay (`data/raw/reference/nysdec-227-3-peaker-compliance.csv`,
24 rows sourced row-by-row to NYISO Gold Book Tables IV-3..IV-6, 2023-2025
vintages, per-unit citations in the file).

It is **off-queue** because §5.5 does not list it, and it is off-queue **with
cause**: this session found it is not merely untested on the current keeper —
**it has no row in the cross-ISO mechanism matrix at all**, so its status has
been invisible to every session since. That is a rule 28(c) `[R-MECH-MATRIX]`
hygiene gap on a solve-affecting field, and the row lands with this work.

**Its test history, in full.** It was armed exactly once — nyiso-46
(2026-07-04, `2026-07-04-nyiso-46-decpeaker`) — as one of *three* stacked
mechanisms in a probe that stayed a probe because C1-2024 ST_GAS was a hard
fail **for unrelated reasons** ("the CT reduction cleared to CC/imports, not
steam"). The calibration log calls nyiso-46 the session's **best probe, "most
structurally faithful"**. **There is no rejection of the 227-3 overlay itself
anywhere in the record**, and no NYISO bundle since carries it: every
`meta.json` in `results/calibration/nyiso*/` reads
`nysdec_peaker_rule_availability: false`. So it was dropped in a keeper-lineage
change, not adjudicated out.

**Why it is admissible (rule 13 `[R-MEASURED]`).** It is an exogenous
**regulatory availability event** with a published, per-unit compliance
schedule and a forward story (the schedule runs through the 2030 NYPA statutory
phase-out). Availability only — it never touches an offer or a price. Same
admissibility class as the CAMPD unit-outage windows. **Zero fitted DOF.**

**Why it is not a rule-19 `[R-ONE-MECH]` stack — measured, not assumed.** The
obvious double-count risk is the CAMPD outage overlay already zeroing these
units. **It does not.** On the keeper's own solved 2023 dispatch the restricted
units are dispatched *inside* their own ozone windows: Coxsackie GT1 316.5 MWh
over 42 h, Glenwood GT3 371.2 MWh over 9 h, Northport GT 116.8 MWh over 11 h,
Shoreham 114.5 MWh over 7 h — every hour after the 2023-05-01 effective date.
The model is running capacity the regulation says is out of service, so the
overlay adds a constraint nothing else imposes.

## §2 — what it restricts, and the honest scale

Ten units carry `ozone_season_oos` (seven effective 2023-05-01, three
2025-05-01), concentrated in the two zones NYISO's scarcity actually occurs in:
**Zone J (NYC) 11 rows, Zone K (Long Island) 7, Zone G 5**. Two STAR-designated
barges (Gowanus, Narrows) are carried in the file and deliberately **not**
restricted — the designation is part of the same regulatory record.

**The scale is small and is stated as small.** The clearly-restricted small GTs
carry roughly **0.9 GWh** of 2023 ozone-season dispatch in the keeper (plus an
unresolved share of Port Jefferson's CT_PEAKER bin, whose GT2/GT3 LM6000s the
compliance file explicitly exempts). That is ~10⁻³ % of ISO energy. **The case
for the arm is not volume — it is that the capacity is removed in the right
zones in the right hours**: every model >$300 hour at NYISO is Long Island
(nyiso-94 §d), and nyiso-92 dated the measured RT tail as summer. The
2025-05-01 phase adds NYC restrictions in the year with the largest tail
(42 h) and the largest peak miss (−17.23 $/MWh DA).

## §3 — falsifiable expectations, declared in advance

1. **Energy effect: near-inert** (sub-GWh class deltas). Predicted, not hoped.
2. **C3c: may improve slightly, may not move at all.** The mechanism is not
   *sized* to C3c and no part of this pre-registration is conditioned on it;
   C3c movement is REPORTED. An arm that leaves C3c bit-unchanged is still
   promotable on rule 14 grounds, exactly as the nyiso-98 nuclear-availability
   arm was.
3. **Direction: weakly upward on downstate peak prices** by construction
   (capacity only ever removed, never added, and only inside the ozone window).
   Since C3a-2023 sits at +7.51 % against a ±10 % band, an upward level move is
   a risk to 2023 — kill P1 exists to adjudicate that honestly.

## §4 — construction gates (K1–K5). All must pass or the arm is VOID.

- **K1 — single delta.** Exactly one recorded `scenario_config` key differs
  from the control: `nysdec_peaker_rule_availability` `false → true`.
- **K2 — control integrity.** Shared with nyiso-111: the same-HEAD zero-delta
  control reproduces the committed keeper's class-hourly dispatch to
  **≤ 1.0 MW** max class-hour delta in all three years.
- **K3 — liveness.** The overlay must actually restrict something: the arm's
  ozone-window dispatch at the restricted (plant, class) rows falls versus
  control by **> 0** in at least one year, and **no restricted row gains**
  inside its own window. Zero movement in all three years ⇒ INERT, registered
  as such.
- **K4 — window fidelity.** All dispatch reductions at restricted rows fall
  **inside** the unit's own effective window (May 1 – Sep 30, on or after
  `effective_date`, before `end_date`); a reduction outside it is a
  mis-applied overlay and voids the arm. STAR-designated Gowanus/Narrows rows
  must be **unrestricted** in every year.
- **K5 — span.** Both bundles cover **[2023, 2024, 2025]** (rule 16); no
  out-of-training year is solved (rule 22; the holdout spend freeze is ACTIVE
  and untouched).

## §5 — kill gates (P1–P4). Any firing ⇒ NOT promotable; the run still registers (rule 15).

- **P1 — C3a band.** C3a leaves ±10 % in any year that passes on the keeper
  (+7.51 / −0.55 / −9.64 %).
- **P2 — C1.** All-class falls below 14/14 or free-class below 10/10.
- **P3 — C8 forced share / D-4.** Any material class crosses its budget, or a
  grounded class loses its D-4 grounding. (The overlay removes availability, so
  the mechanical risk is a floor being clipped against a now-zero cap.)
- **P4 — feasibility.** Any load-shed slack or dump energy appears in any zone
  in any hour.

## §6 — no-tuning clause (binding)

The compliance file is a **regulatory record**, not a parameter. It may not be
edited, extended, re-scoped or partially applied in response to this arm's
result; the STAR-designated rows stay unrestricted. Rule 23
`[R-FROZEN-DERIVE]`: it re-derives only when the Gold Book vintage updates.

## §7 — promotion rule, decided in advance

- **All K pass, no P fires:** candidate for promotion on rule 14
  `[R-ACCURATE]` / rule 1 `[R-STRUCT]` — *the model is currently dispatching
  capacity a published regulation forbids from operating* — whatever the gates
  do. This is the nyiso-98 pattern (an accuracy restoration promoted on its own
  merits with the gate movement reported).
- **K3 fails (no restriction bites):** registered INERT; matrix row records the
  measurement so nobody re-runs it.
- **Any P fires:** registered as a rejected probe with the trade on the record;
  keeper unchanged.

## §8 — reproduction

```
PYTHONPATH=.:src python scripts/replay_keeper.py results/calibration/nyiso109_zonalanchor_B \
    --set nysdec_peaker_rule_availability=true \
    --out-dir results/calibration/nyiso112_decpeaker_C --years <Y> [--reuse-solved <prev>]
```
