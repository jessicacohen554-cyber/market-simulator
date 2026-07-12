# P-2C — Penetration-indexed ELCC curves for wind/solar (CR-3.1) — 2026-07-12

**Session.** P-2C of `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
(§3.4.1), building on the P-2B adopted basis (Option A — per-ISO
published-basis consistency, `docs/handoffs/accreditation-basis-memo-2026-07-12.md`
§4.1) and the P-0B `capacity-market-elcc` datatype
(`data/raw/capacity-market/elcc/`). Replaces the flat generic
`RENEWABLE_CAPACITY_CREDIT` wind 0.16 / solar 0.18 in the adequacy ledger with
each ISO's **own published, penetration-indexed ELCC accreditation**, evaluated
at the **model's own installed share** so the credit regenerates forward and
responds to modeled build (rule 13 — zero fitted parameters; every point is a
published market-design input reconciled against the committed datatype rows
by `tests/test_renewable_elcc_curves.py`, never a fit target).

## 1. What landed

- `constants.RenewableElccCurve` + `evaluate_renewable_elcc_curve` — pure
  piecewise-linear evaluation, flat-clamped beyond the published domain (no
  invented slope), three axis bases: `installed_mw`, `pct_of_peak_load`,
  `None` (published single point → constant). An axis quantity the model
  cannot supply returns `None` and the resolver falls back — a curve can
  never silently misprice.
- `constants.RENEWABLE_ELCC_CURVES_BY_ISO` — the digitized registry
  (§2 below), cited row-by-row to the P-0B CSVs.
- `capacity.resolve_renewable_capacity_credit` — the ONE resolver (rule 19):
  published curve (gated) → published per-ISO point override
  (`RENEWABLE_CAPACITY_CREDIT_BY_ISO`, ERCOT's CDR basis, untouched) →
  generic flat fallback. Penetration = the class's ISO-wide nameplate
  (zonal pools + fleet units, `_renewable_nameplate_by_fuel`) against the
  year's peak.
- All four consumers move together off that resolver:
  `accredited_firm_capacity_mw` (grew `peak_demand_mw` /
  `elcc_curves_enabled` kwargs), the retirement **reliability floor**, the
  **reserve-margin backstop**, and the **CR-1 reserve position**
  (`capacity_reserve_position`). The evolution ledger records the applied
  credits + pool nameplates + storage fleet state per year
  (`renewable_credit_applied`, `wind/solar_cap_mw`,
  `storage_power_mw`/`storage_firm_mw`) so the penetration response is
  observable per run.
- Gate `ScenarioConfig.renewable_elcc_curves`, default **ON** (rule 15:
  published accreditation over a generic estimate; the flat constants remain
  the fallback for ISOs without a study either way). `False` is the
  **frozen-penetration byte-compat mode** — credits pin back to the
  pre-CR-3.1 flat constants byte-identically (locked by
  `test_frozen_mode_reproduces_legacy_everywhere` +
  `test_default_args_reproduce_legacy_signature`); it is the capacity-hindcast
  BASELINE arm (`run_capacity_hindcast.py --legacy-renewable-credit`).
- Methodology spec §5.2 grew the "VRE accreditation (CR-3.1)" paragraph;
  parameter registry regenerated (`renewable_elcc_curves_by_iso.*` rows).

Backcast keepers are untouched: capacity evolution is forecast-only
machinery, and the resolver's dispatch-side surface is nil (renewables stay
LP decision variables; credits are adequacy bookkeeping only). The only
backcast-visible delta is the evolution ledger's new diagnostic fields.

## 2. Per-ISO digitization decisions (what, and why)

| ISO | Basis | Points | Decision |
|---|---|---|---|
| **PJM** | `installed_mw` (ELCC/RRS Table 5 axis) | wind (3549, 0.41), (3956, 0.41); solar (9902, 0.1064), (13106, 0.0789) | Official/final 2026/27 + 2027/28 BRA class ratings (Option A: the ELCC-class basis end-to-end). Solar = MW-weighted blend of Tracking + Fixed-Tilt per vintage (same-document arithmetic, re-derived in the reconciliation test). Wind is published flat 41 % over the observed range → clamps at 0.41 (the memo's 0.16 → ~0.41 under-crediting fix). The preliminary ER24-99 marginal trajectory (35 % → 19 % by 2032/33) is delivery-year-indexed with **no published MW axis** — deliberately NOT converted (never guess an axis); extend when PJM publishes the pairing. |
| **MISO** | `pct_of_peak_load` | 9 points, (7.6, 0.080) … (16.7, 0.166) | The 2019 Wind & Solar Capacity Credit Report's adopted "MISO Capacity Credit" class-average series PY2010–PY2020 — the strongest genuine public penetration curve. All published points as-is (incl. the real year-to-year wiggle; the identical PY2012/PY2015 pair deduplicated). NOTE the published curve **rises** with penetration (geographic-dispersion era) — the model follows the published shape, never an assumed decline; beyond 16.7 % of peak it clamps at 0.166, conservative against the PY23-24/PY25-26 seasonal marginal ELCCs (18–31 % at ~28 GW) which sit on a different axis + seasonal grain and are not blended in. MISO **solar** has no published probabilistic curve (only <30-day-data seasonal defaults) → generic fallback. |
| **NYISO** | `None` (single point) | wind 0.1684, solar 0.1224, offshore_wind 0.3579 | Official 2025-26 CAFs (marginal-accreditation design applied to every MW of the class — NYISO's own construction). Rest-of-State column for wind/solar (where nearly all NYISO wind/utility-solar physically sits), Long Island for OSW (the only locality with OSW). No penetration axis published → constants, never a fabricated curve (schema discipline). The third-party NY-BEST/Astrapé curves on disk are **not NYISO-adopted** → not wired. |
| **NEISO** | — (fallback) | — | No ISO-published ELCC study: both on-disk sources are third-party (2022 GE/NRDC, 2024 E3/Mettetal, each labeled "not ISO-NE-adopted") and ISO-NE accredits intermittents via seasonal claimed capability today. Generic flat fallback (cited, neutral — rule 25 spirit) until the RCA marginal-ELCC values publish. |
| **CAISO** | — (fallback) | — | The on-disk CPUC E3/Astrapé study publishes **incremental** (marginal-tranche) ELCCs conditioned on the IRP portfolio — solar *rises* 6.6→8.8 % with companion storage buildout. Using a marginal value as the whole-fleet class-average ledger credit would misstate the supply block (rule 15's documented misalignment exception). "CAISO untouched" (P-2B §4.1); revisit on a class-average NQC/ELCC intake. |
| **ERCOT** | — (existing point override) | wind 0.20 / solar 0.21 | CDR seasonal-rating basis stays (`RENEWABLE_CAPACITY_CREDIT_BY_ISO`, accreditation audit 2026-07-06) — plan §3.4.1: "ERCOT seasonal-rating basis stays". The curve mechanism is byte-inert for ERCOT (locked by test). |

## 3. Storage reconcile — rule-19 enumeration (NO new storage derate)

What already derates storage, before this session (the charter's required
enumeration):

1. **Duration ELCC** — `STORAGE_ELCC_BY_DURATION` via
   `storage._elcc_for_duration`: applied (a) in the runner when it
   pre-accredits `storage_firm_mw` for the adequacy ledger, and (b) in the
   storage entry screen (`estimate_capacity_value`).
2. **Marginal saturation derate** — `(1 − fleet/ceiling)^STORAGE_ELCC_SATURATION_EXPONENT`
   in `estimate_capacity_value` (entry screen only — the mechanism that
   tilts new entry toward longer durations).
3. **Portfolio ELCC dilution** — `capacity._storage_portfolio_elcc_dilution`
   (ERCOT-only registries), applied once at the evolve seam where the
   pre-accredited `storage_firm_mw` is consumed.

This session adds **nothing** to that stack and touches none of its
parameters. The new wind/solar resolver never sees storage:
`storage_firm_mw` passes through `accredited_firm_capacity_mw` exactly, in
both gate modes (locked by `test_storage_passthrough_untouched_rule19`).
The P-0B datatype's **storage rows** (PJM 4/6/8/10-h class ratings, NYISO
EDL CAFs, CPUC tranches) are deliberately **not wired**: wiring them into a
second storage path would stack a new mechanism on the existing
duration-ELCC/saturation/dilution stack (rule 19). Reconciling
`STORAGE_ELCC_BY_DURATION` (4 h → 0.60 generic) against PJM's published
4-h = 50 % / NYISO's 4-h CAFs is **Option-A step 3** work
(accreditation-basis memo §4.2.3) — flagged there, not smuggled in here.

## 4. T1.9 / #2063 status

- The #2063 crash (`AttributeError: ira_other_clean_75pct_year` from
  `ira_phaseout_fraction`, which killed all three T1.9 rungs and both NEISO
  T1.6 rungs in the P-1A round) is **already fixed at HEAD** — P-1C landed
  the step-schedule fields (`scenarios.py` `ira_other_clean_{75,50}pct_year`)
  after the P-1A battery ran. Verified end-to-end this session;
  `TestIraPhaseoutRegression2063` locks the schedule so the crash class
  cannot silently return.
- T1.9's metric existed only as a SKIP placeholder ("leave the metric absent").
  It is now real: `storage_cap_value_per_mw` = the model's own **marginal
  storage accreditation** at the final fleet — `ELCC(4 h) × saturation
  derate × portfolio dilution` at the ledger's `storage_power_mw` (in
  energy-only ERCOT the $ capacity price is 0 by design, so the accreditation
  fraction is the saturating observable the plan's expectation names). Extras:
  `storage_fleet_avg_elcc` (ledger firm/power) and
  `storage_new_longdur_share` (duration tilt of new builds).
- T1.9 ladder re-run: see §5.

## 5. Results — T1.9 re-run + ERCOT/PJM capacity hindcast before/after

*(filled in at end of session — runs in flight)*

## 6. Follow-ups opened / flagged

1. **PJM wind curve has no published declining axis** — the ER24-99
   marginal-ELCC trajectory needs its per-delivery-year MW pairing (RRS
   Table 5 forecast rows) intaken before it can become a penetration curve;
   until then PJM wind clamps flat at the final class rating (0.41).
2. **R3 thermal-class intake** (accreditation-basis memo §4.3-R3) — PJM's
   thermal ELCC class ratings are in the already-cited final-ratings docs but
   not yet in the datatype; needed for Option-A step 3 (thermal
   `elcc_class_rating` basis + payment seam). Sibling item, per the memo's
   "P-2C scope confirmation".
3. **Storage duration-table reconcile** (Option-A step 3): PJM publishes
   4-h = 50 % vs the generic `STORAGE_ELCC_BY_DURATION` 0.60 — reconcile
   per-ISO there, one mechanism, when the thermal basis migrates.
4. **VRE new-entry screen earns no capacity revenue** (pre-existing, audit D7
   scorecard): wind/solar entry margins see energy + attributes only, so the
   ELCC curves do not yet feed VRE entry payoffs — only the ledger, floor,
   backstop, and CR-1 position. Natural CR-2/CR-3 extension once the payment
   seam migrates (memo §4.2.4).
5. **`deliverability_headroom_by_zone` still uses the generic flat credits**
   (default-off gate, part (b) unvalidated in any keeper — pre-existing; its
   zonal grain needs a zonal penetration story before curves apply there).

*Produced 2026-07-12 (P-2C). Tests: `tests/test_renewable_elcc_curves.py`
(30) + full capacity/storage/runner/battery suites green.*
