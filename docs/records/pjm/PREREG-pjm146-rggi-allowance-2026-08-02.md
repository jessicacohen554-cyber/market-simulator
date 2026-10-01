# PREREG pjm-146 — PJM RGGI allowance cost in dispatch (`state_carbon_pricing` cell)

**Committed BEFORE any arm solves** (the pjm-144 protocol). Charter:
`docs/handoffs/pjm-matrix-column-triage-2026-08.md` §2.1 (the Phase-1 triage's
rank-1 live candidate). Keeper under test: `2026-07-31-pjm-143b-hy-level`
(CALIBRATED 9/9). One lever, zero fitted parameters, single-delta A/B.

## 1. The claim

PJM's RGGI-member fossil units (NJ/MD/DE all three years; VA in 2023 only)
carry a real, measured compliance cost — one RGGI allowance per short ton
CO2 — that is absent from every PJM offer in the model
(`CAP_AND_TRADE_PROGRAMS["PJM"].price_key = None`; adder provably $0). The
mechanism family is `K` in CAISO/NYISO/NEISO. Charging
`emission_rate × m[g] × p_allowance(year)` on member units is the faithful
representation (the adder path, `policy/cap_and_trade.py` plan §2) — a
rule-14 accuracy swap and a rule-1 structural mechanism, NOT an amplitude
lever from the pjm-142-closed queue (frontier compatibility: "a NEW measured
identification with its own charter").

## 2. Mechanism spec (the whole delta, committed before the control solves)

1. `ScenarioConfig.pjm_rggi_allowance_pricing: bool = False` — default-off
   gate, registered in `_CACHE_KEY_OPTIONAL_FIELDS` (default cache key stays
   `603c2498bf71d21d`; an armed run gets a distinct key). Matrix row updated
   in the same PR (duty 28c — the field joins the `state_carbon_pricing` row
   def).
2. `constants` (fuel_trajectories): `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE =
   {2023: 14.87, 2024: 22.83, 2025: 24.35}` — the RGGI quarterly-auction
   clearing-price annual means already cited in-repo (A59–A70 press
   releases), **metric-converted** at 1 short ton = 0.907185 t (the NEISO
   convention, unit-exact against the model's tCO2/MWh rates; the NYISO
   short-ton convention understates by ~10.2 % — harmonization note carried).
   Deliberately NOT placed in `STATE_CARBON_PRICE_BY_ISO` this session: that
   would silently re-arm every PJM backcast under default-True
   `state_carbon_pricing` (a same-key cache invalidation, `results/cache.py`
   epoch policy). Promotion-to-default is the owner's call after this A/B.
3. `policy/cap_and_trade.resolve_carbon_program`: backcast adder branch gains
   the gated PJM lookup (`price_key is None` + gate on + iso PJM → the
   registry above). Forecast branch untouched (PJM projected price stays 0 —
   mode `B`, like every measured backcast overlay; the escalator unification
   is a promotion-time item).
4. `scripts/run_calibration.py::run_year` mc seam: when the ISO's program has
   a fractional footprint (`program.zone_share is not None`) and the resolved
   adder is nonzero, the scalar carbon price is replaced by the
   per-generator column `per_generator_membership(iso, year,
   resolution.membership, fleet_arrays) × price_adder` into `assemble_mc`
   (which already accepts it). Scoped to `zone_share is not None` ⇒
   CAISO/NYISO/NEISO stay on the scalar path **by construction** (no code
   path change, byte-identical; rule 25 lane isolation), ERCOT/MISO have no
   program, and gated-off PJM resolves adder 0 ⇒ control byte-identical.
   `zone_names` passed is the runtime interchange-extended list
   (`run_calibration.py:2018`, post-`apply_interchange_topology`) matching
   `fleet_arrays.zone_idx`.
5. Composition (verified in Phase 1, cited here as load-bearing):
   `assemble_mc` carries the column; `apply_coal_tranches` "VOM, carbon and
   NOx are never touched" (fuel-portion-only discount);
   `apply_gas_offer_margin` is additive (`mc += markup×(anchor−fuel)`); the
   midcurve belt lifts to a measured target (`max(0, target − mc_base)`), so
   where it binds a carbon-inclusive mc is absorbed into a target measured
   from carbon-inclusive conduct — self-consistent, declared not patched.

**Identification, all measured, zero fitted (rules 13/23/24):** prices =
published auction clearing means (above); membership = exact per-plant
EIA-860 state test against `RGGI_MEMBER_STATES_BY_YEAR` (VA 2023-only), with
the committed `PJM_RGGI_ZONE_SHARE` fractional fallback only for synthetic
rows; emission rates = the fleet's own (CAMPD same-year in backcast). No new
number is chosen by this session.

## 3. Pre-declared expectations (E1)

Adder arithmetic (deterministic): member gas-CC (~0.37 t/MWh) +$5.50 /
+$8.45 / +$9.01 per MWh in 2023/24/25; member coal (~0.95–1.05 t/MWh)
+$14.1–15.6 / +$21.7–24.0 / +$23.1–25.6. Member footprint = EMAAC
0.7327/0.7252/0.7221, SWMAAC 0.9976, Dominion 0.9881 → 0.0 (VA exit),
West_APS 0.0108 → 0 (zone fossil-nameplate shares; per-unit test refines).

- **E1a (direction, all years):** load-weighted annual LMP RISES; member-state
  fossil energy FALLS; the displaced energy lands on non-member fossil +
  imports + (marginally) storage/hydro timing.
- **E1b (magnitude band, load-weighted annual):** **+$0.20 to +$2.50/MWh**.
  Declared wide (the member-marginal frequency is not directly observable
  pre-solve); a band miss is recorded, never re-fit (pjm-143 precedent).
- **E1c (year shape):** 2023 has the widest footprint (Dominion in) but the
  lowest price; 2024/25 have higher prices on a narrower footprint. No
  monotone-across-years prediction beyond E1a.
- **E1d (fit consequences, declared per the triage §2.1 caution):** C3a-2023
  (+2.99 % over) WORSENS; C3a-2025 (−9.04 % under) IMPROVES; C3a-2024
  (−1.28 %) likely crosses toward over. The fitted offer surfaces were
  identified on the uncompensated stack — the level shift is EXPECTED and
  goes to the owner with numbers; it is not a rejection ground by itself
  (rule 1/14; the ercot137 "structural integrity improves, gates regress"
  pattern). Zonal secondary (REPORTED, not gated): EMAAC/SWMAAC (+DOM 2023)
  rise more than ComEd/AEP/ATSI/West; PJM's price-coupled topology may mute
  the differential (the pjm-144 lesson) — muting does NOT kill a level
  mechanism.
- **E1e (C3c, queue item 6):** tail-hour counts reported explicitly in both
  arms against the 1 h (2024) / 2.5 h (2025) margins. No prediction beyond
  "reported".

## 4. Gates and kill rules (construction-grain; fit outcomes are reported, not killed)

- **K1 — mechanism live at its own grain (MC):** ≥ 50 fossil units carry a
  nonzero adder in every year; per-unit adder equals
  `emission_rate × m × price` to 1e-9 (probe recomputes from the built
  fleet). FAIL ⇒ stop, wiring defect.
- **K2 — control integrity (strict byte):** the control arm reproduces the
  committed keeper to 0.0 MW on every class-hour and to the third decimal on
  load-weighted prices (the pjm-144 standard; `class_hourly_<year>.parquet`
  + `system_<year>.parquet`). Any drift ⇒ stop-the-line, diagnose before any
  candidate solve.
- **K3 — membership audit (no-LP, from the built fleet, all three years):**
  (a) zero units in non-member states charged via the per-unit path; (b)
  zero VA units charged in 2024/2025 and Dominion's member fossil charged in
  2023; (c) every member-state fossil unit with a real `plant_code` charged;
  (d) synthetic rows carry exactly the committed zone shares. Any breach ⇒
  kill (construction).
- **K4 — sign:** load-weighted ΔLMP < $0 in any year ⇒ stop (a one-signed
  positive cost adder cannot lower the level; indicates a defect). Member
  fossil energy Δ > 0 in any year ⇒ same.
- **K5 — liveness (the pjm-144 K3 analogue, at the LEVEL grain the mechanism
  claims):** load-weighted annual |ΔLMP| < $0.10 in ALL three years ⇒
  verdict `I` (dispatch-live-price-inert is not a pass for a cost-level
  mechanism). Zonal differential explicitly NOT the liveness statistic.
- **Honesty:** every criterion of the standard scorecard on both arms from
  `metrics.json` only; `legitimacy_diagnostics` on both arms; C1/C2/C3/C4/
  C7/C8 flips REPORTED to the owner with numbers — never silently kept or
  reverted, and never auto-promoted. LOYO (rule 22): zero fitted parameters
  ⇒ nothing is identified on any training year; per-year results ARE the
  leave-one-year-out evidence and are reported per-year.

## 5. Protocol

- Chain: `scripts/probes/_pjm146_chain.sh` (the committed `_pjm145_chain.sh`
  passthrough pattern; keeper `pjm143_hy_level_B`; swap re-asserted first —
  keeper note 14).
  - control: `_pjm146_chain.sh pjm146_control_A "<note>"`
  - candidate: `_pjm146_chain.sh pjm146_rggi_B "<note>" --set pjm_rggi_allowance_pricing=true`
- Years 2023 2024 2025, sequential, one fresh process per year,
  `--reuse-solved` links (rule 12); arms sequential; both arms registered on
  the backcast dashboard (rule 15) whatever the verdict.
- Scorer: `scripts/probes/_pjm146_rggi_ab.py`, modeled on
  `_pjm144_zonal_anchor_ab.py` — all criteria from the two bundles'
  `metrics.json` + the K-gates above from the built fleet and hourly
  sidecars; attestation from the committed A/B JSON
  (`results/calibration/_pjm146_rggi_ab.json`).
- Verdict mapping: K2/K3/K4 breach ⇒ no verdict, fix-or-stop. K5 ⇒ `I`.
  Constructed-live + gates-intact ⇒ surface to owner with the E1d numbers as
  a promotion candidate (`U → K` only on owner promotion; `U → O` if left
  pending). A rejection on the merits (owner declines on the numbers) stamps
  `R` with this prereg cited.

## 6. What this session does NOT do (scope fence)

No retune of any fitted band toward or away from the RGGI effect (the
compensating-surface re-identification is a named successor lane); no
forecast-mode arming; no `STATE_CARBON_PRICE_BY_ISO` entry; no touch of the
mass-cap row path; no change to any other ISO's carbon path (byte-identity
asserted by construction and by the existing test suite).
