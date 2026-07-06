# ERCOT accreditation-basis audit — the accredited-short / dispatch-long root cause (2026-07-06, L-7c)

*Executes the Stage-3 addendum's explicit handoff
(`fom-scarcity-joint-protocol-2026-07-06-stage3-addendum.md`, "Root-cause
pointer"): audit whether the ERCOT reliability floor's requirement —
`peak × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)` against
`accredited_firm_capacity_mw` (UCAP/ELCC basis) — matches the physical
adequacy the dispatch shows. Verdict: **the basis was wrong, on four
separately-citable elements, all in the same direction.** Fixed in
`model/capacity.py` / `config/constants.py` with per-ISO registries; every
non-ERCOT ISO is byte-identical. This is a measured-data correction against
ERCOT's own published adequacy construction (rules 5/14), not a tuning: no
element was chosen by looking at a residual, a retirement pace, or the FOM
axis — each is the published number for the thing the ledger was already
trying to count, and the validation target is the CDR's own reserve-margin
arithmetic (§4), not any model outcome.*

## 1. The finding in one table

Model 2026 ERCOT adequacy ledger, mid growth, legacy bins (the FOM-grid
configuration), computed with no LP (fleet build + arithmetic only):

| Ledger | Requirement | Accredited | Margin | Verdict |
|---|---:|---:|---:|---|
| OLD model basis | 106,598 MW (93,712 gross peak × 1.1375) | 99,033 MW | **−7,565 MW** | SHORT (floor binds year 1, worsens ~2.5 GW/yr → "perpetually short") |
| NEW basis (ERCOT's own CDR convention) | 100,415 MW (firm peak × 1.1375) | 107,110 MW | **+6,694 MW** | LONG (implied RM 21.3%) |
| ERCOT's published ledger (Dec 2025 CDR) | — | — | **+18.3%** summer 2026 PRM | LONG |

The model was declaring ERCOT ~7.6 GW short in a year ERCOT's own published
Capacity, Demand and Reserves report scores at **+18.3%** reserve margin —
comfortably above the 13.75% Board target. The "accredited-short but
dispatch-long" contradiction the Stage-2/Stage-3 grids kept hitting was not
a deterministic-dispatch-vs-probabilistic-tail subtlety: **the model's
adequacy ledger disagreed with ERCOT's adequacy ledger**, because it mixed
counting conventions. The dispatch was right; the ledger was mis-based.

## 2. The four basis errors (each cited, each formulaic-forward)

All four mixed a piece of one convention into another. The 13.75% target is
defined on the CDR's counting convention; testing it against a differently-
constructed ledger double-counts risk that the target already carries.

1. **Gross peak where ERCOT uses firm peak load.** The CDR nets standing
   load-side capacity products out of the gross seasonal peak before
   applying any margin: Load Resources providing RRS (935) + Non-Spin (50)
   + ECRS (300) + controllable LRs (20) + ERS (2,750) + TDSP load
   management (303) + distribution voltage reduction (1,162) = **5,520 MW
   on the 95,419 MW summer-2026 gross peak = 5.8%** (Dec 2025 CDR, Seasonal
   Summary, peak-load-hour column). Rooftop-PV netting is excluded — EIA-930
   demand is already net of behind-the-meter PV. New registry:
   `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO` (fraction of peak, so it
   regenerates for forward years; rule 13: a market-design input, not an
   outcome). Worth ~6.3 GW of 2026 requirement.
2. **UCAP-derated thermal against a rating-basis target.** The CDR counts
   thermal at installed seasonal rating with **no EFORd derate** — forced-
   outage risk lives inside the 13.75% target margin, not in the capacity
   count. Derating by `1 − EFORd` against that same target double-counts
   outage risk. New registry: `THERMAL_ACCREDITATION_BASIS_BY_ISO["ERCOT"]
   = "seasonal_rating"`; default for every other ISO stays UCAP. Worth
   ~4.4 GW on the 2026 thermal fleet.
3. **Generic wind/solar credits where ERCOT publishes ELCCs.** The old flat
   0.16/0.18 were generic NREL/E3-class values (flagged `needs-citation` in
   the parameter table since introduction). ERCOT's Dec 2025 CDR accredits
   IBRs at probabilistic ELCCs; implied percentages (CDR summer ELCC MW,
   operational + CDR-eligible planned, peak-load-hour column, over installed
   nameplate from the July 2026 Fact Sheet — wind 40,739 MW, utility solar
   39,591 MW): **wind 20.2% (2026), stable 20.5–20.8% through 2030 → 0.20;
   solar 28.0% (2026) diluting to 20.5–21.1% by 2028–2030 → 0.21** (the
   CDR's own plateau — conservative for 2026-27, right for the forecast
   horizon where the floor decision matters). New registry:
   `RENEWABLE_CAPACITY_CREDIT_BY_ISO["ERCOT"]`. Worth ~2.9 GW in 2026 at
   the plateau values (~5.6 GW at the 2026-vintage values).
4. **DC-tie firm imports missing.** The CDR counts 817 MW of non-synchronous
   tie support ("average net import contribution during the summer 2023 and
   winter 2020/2021 EEA events"). The model's ERCOT topology has no import
   node, so this measured contribution was silently zero. New registry:
   `ADEQUACY_EXTERNAL_TIE_FIRM_MW["ERCOT"] = 817`.

Also corrected: the `PLANNING_RESERVE_MARGIN_BY_ISO["ERCOT"]` citation. The
0.1375 **value is right** but it is ERCOT's **Board-established minimum
target reserve margin**, not (as the old comment claimed) the Brattle
economically-optimal RM — the Brattle/Astrapé MERM/EORM studies for the
PUCT put the market-equilibrium RM near 10.25% and the economic optimum
near 9%. Using the Board target (the benchmark the CDR reads margins
against) is the conservative published choice; the value is unchanged.

## 3. What was NOT changed (and why)

- **Storage ELCC.** The duration-table basis (`STORAGE_ELCC_BY_DURATION`)
  stays: model 2026 storage firm 11.7 GW vs the CDR-implied 12.3 GW
  (operational + planned, ELCC 60.2% on 20,438 MW installed) — close at
  fleet level. The model's assumed 4h/8h duration mix is generous against
  ERCOT's real 1–2h-dominated fleet while its per-duration credits are
  conservative; the errors offset today. Follow-up (storage module, not
  accreditation basis): the CDR's own BESS ELCC dilutes 60% → 46% by 2030 as
  penetration triples; the duration table has no penetration term.
- **The 13.75% value itself** (see §2 — citation fixed, value kept).
- **`_zone_deliverability_headroom`** (the locational gate's zonal ledger)
  keeps generic credits: it only fires under `capacity_deliverability_limits`
  for ISOs with published deliverability parameter sets, which ERCOT does
  not have — the ERCOT overrides can never reach it.
- **The runner's evolution-ledger `firm_mw` record** (`runner.py`) still
  logs the generic-basis value — `runner.py` is owned by a parallel lane
  this wave. One-line follow-up: pass `iso=iso` at that call site so the
  persisted ledger matches the floor's test. The floor and backstop
  themselves resolve the ISO basis internally in `capacity.py`.
- **PJM/MISO ICAP-vs-UCAP pairing** — flagged, not fixed (out of lane):
  PJM's 17.8% IRM and MISO's 17.9% PRMR are **ICAP-basis** targets; testing
  them against UCAP-accredited supply is the same class of double-count
  (PJM's published UCAP-basis pair is FPR ≈ (1 + IRM) × (1 − pool EFORd)).
  This plausibly contributes to the PJM backstop's FOM-invariant ~10 GW/yr
  forced builds noted in Stage 2 §2.1. Needs its own audit against the
  IRM/FPR filing before anyone touches it.

## 4. Validation — against the CDR's arithmetic, never a model outcome

No-LP checks (`rule 22` untouched: no backcast, no holdout, no solve):

- Legacy path byte-identity: `accredited_firm_capacity_mw(..., iso=None)`
  and every non-ERCOT ISO reproduce the old numbers exactly (99,033 MW on
  the 2026 ERCOT diagnostic fleet; PJM/MISO/... have no registry entries).
- ERCOT restatement: new ledger 107,110 MW accredited vs 100,415 MW
  required → implied 2026 reserve margin **21.3%** against the CDR's
  published **18.3%**. Residual +3 pts decomposes into the model's larger
  thermal fleet (78.2 GW incl. 2026-due planned units and PUN-class cogen
  the CDR reports separately) and the storage duration mix (§3) — both
  fleet-composition questions, not basis questions.
- Full test suite passes; floor/backstop unit tests updated to the CDR
  arithmetic where they pinned ERCOT defaults, with one test explicitly
  pinning the legacy UCAP basis via registry patch (the default-basis
  conservatism property).

## 5. Consequences for the blocked lanes (what this predicts, honestly)

Static projection under the corrected basis (no evolution feedback): mid
growth is long ~6.7 GW in 2026, and the requirement (~1.0715 × gross peak)
crosses the static 2026 accredited level around **2028-29** (gross peaks
93.7 → 119.6 GW over 2026–2031). So:

- The floor should now be **quiet in 2026-27 and bind only as genuine
  late-decade shortage emerges** — retirement decisions in the Stage-2 gate
  window (2026-2028 pace) return to the economic screen, where the FOM bar
  can finally decide something. Whether it does is exactly the path-(c)
  probe (run separately, this lane, after this fix).
- Late-decade mid-growth shortage is **real in that demand world** — our
  mid path (~5%/yr peak growth) sits between ERCOT's protocol-prescribed
  and SB6-adjusted scenarios, and ERCOT's own protocol-prescribed margins
  go negative from 2028. Post-fix shortage should express as scarcity
  price and economic entry, not year-one wholesale un-retirement.
- The ERCOT capacity-hindcast scarcity question (s3) inherits the same
  correction: the floor no longer over-retains against a phantom shortage
  in the hindcast window.

*Files: `src/market_sim/config/constants.py` (four new registries + PRM
citation fix), `src/market_sim/model/capacity.py`
(`resolve_adequacy_requirement_mw`, `_thermal_firm_mw`, `_renewable_credit`,
iso-aware `accredited_firm_capacity_mw`, floor/backstop call sites),
`tests/test_capacity.py`. Primary sources: ERCOT, "Report on the Capacity,
Demand and Reserves (CDR) in the ERCOT Region", December 2025 (Seasonal
Summary, ELCC background/tabs, scenario tables); ERCOT Fact Sheet, July
2026 (installed wind/solar/storage MW); Brattle/Astrapé, "Estimation of the
Market Equilibrium and Economically Optimal Reserve Margins for the ERCOT
Region" (2018), for the PRM-citation correction. Produced 2026-07-06, lane
L-7c.*
