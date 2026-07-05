# FOM + scarcity joint sensitivity protocol — ERCOT/PJM (2026-07-05, W2-P3 Stage 1)

*Executes `docs/handoffs/capacity-economics-plan-2026-07.md` §5 (the joint FOM+scarcity
protocol) and §1 (the ATB going-forward FOM recalibration). This is the **verification** leg
that keeps the cost side (FOM) and the revenue side (scarcity/AS) from being co-tuned against a
single retirement/emissions residual (CLAUDE.md rule 1). It records the probe matrix and decides
whether the ATB FOM defaults may be flipped **before** any default changes.*

**Headline decision: DO NOT flip the FOM defaults this session.** The grid shows the going-forward
FOM level is currently **inert** in the ERCOT forecast — the nameplate reliability floor retains
100 % of thermal and the adequacy backstop backfills the rest, so changing CT 8→21 / CC 12→30 /
coal 40→45 $/kW-yr moves **zero MW** and **zero tonnes** of CO₂. Flipping now would be a no-op
falsely credited with the plan §1.4 emissions effect. Per rule 1 the recalibration is **blocked
behind two later-stage prerequisites** (floor accreditation §3, revenue-side fix §5 step 2). The
ATB values are recorded as the externally-identified targets; nothing is tuned to a residual.

**Scope (W2-P3 Stage 1 only):** the capacity-evolution retirement screen going-forward FOM bar
(`capacity.py` `apply_economic_retirements`) and the joint protocol. Foresight (EWMA/lookahead),
floor accreditation, and the DC-load block are later stages. No dispatch-layer floor was touched.
No 2022 / H1-2026 solve or data intake (rule 22). Forecast probes only — nothing registers on the
backcast dashboard. Base commit `6a38c72` (the diagnostic + grid runner landed via PR #1396;
capacity/scenarios unchanged since).

---

## 1. The two sides and their identification (rule 1 / rule 21 DOF ledger)

The retirement inequality `net_revenue < going_forward_cost` is hit from opposite sides. Each side
must be identified by its **own external evidence**, never by the retirement residual:

| Side | Parameter(s) | Identification source (NOT the retirement residual) |
|---|---|---|
| Cost | `fixed_om_gas_ct/gas_cc/coal` | NREL ATB 2024 existing-unit FOM: CT ≈ 21, CC ≈ 30, coal ≈ 45 $/kW-yr (plan §1.2) |
| Revenue | ORDC energy adder + AS credit (exogenous or endogenous co-opt) | Potomac Economics **ERCOT State of the Market** net-revenue tables (below) |

### 1.1 Revenue-side external observable — Potomac ERCOT SOM

Source: **2024 State of the Market Report for the ERCOT Markets** (Potomac Economics IMM,
published 2025-06), Figure 56 (CT/CC net revenues 2020-2024, $/kW-yr) and Figure 57 (Peaker Net
Margin 2018-2024), pp. 80-83.

| Observable (2024) | Value |
|---|---|
| CT net revenue (energy + reserves/AS) | **≈ $68 /kW-yr** |
| CT CONE | $102-106 /kW-yr |
| CC net revenue (energy + reserves/AS) | **≈ $89 /kW-yr** |
| CC CONE | $116-121 /kW-yr |
| Peaker Net Margin threshold (3×CONE, SWCAP step-down) | $315 /kW-yr |

SOM "net revenue" stacks **Reserves (AS) + Energy Sales** — the same stack the retirement screen
builds (energy margin + ORDC adder + AS credit). It is a measured *validation observable*
(rule 13: compare, never pin). Caveat: the SOM figure is for a **new, efficient proxy** CT/CC
(heat rate 10.5, VOM $4, 10 % outage) and is an **upper anchor** for a marginal *existing* unit;
a fleet-average across old units sits below it. The screen's going-forward bar is FOM-only
(avoidable), not CONE, so an efficient CT earning $68 clears a $21 ATB FOM bar comfortably.

---

## 2. Probe matrix (plan §5 step 3)

`scripts/run_fom_scarcity_grid.py`, ERCOT 2026-2031 mid-growth, legacy equal-width fleet
(`use_campd_bins=False`, runtime; leverage ranking robust to granularity), sequential years,
2 concurrent solves (rule 12), 42 min wall-clock. `reserve_margin_build_enabled=True` in every
cell so the adequacy backstop is *observable* (it is default-off in a normal forecast; enabling
it turns over-retirement into a measurable forced-build MW rather than silent thinning of
reserves).

- **FOM axis:** `legacy` = today's defaults (CT 8 / CC 12 / coal 40×1.3=52 effective) ·
  `atb` = plan §1.2 (CT 21 / CC 30 / coal 45×1.3=58.5).
- **Scarcity axis (ERCOT):** `off` = bare LP duals, no AS (today's raw ScenarioConfig default) ·
  `ordc` = post-solve ORDC energy adder + exogenous AS overlay (intended forecast stack) ·
  `coopt` = endogenous multi-product AS co-optimization (scarcity + AS priced in the LP).
- **PJM check (FOM axis only):** capacity-market revenue side (net-CONE × UCAP); 2 cells.

### 2.1 Results — the FOM level is inert

| Cell | 2026-2031 CO₂ (Mt) | mean price ($/MWh) | thermal retired (GW) | 2031 fleet coal / gas_cc / gas_ct (GW) |
|---|---:|---:|---:|---|
| ercot legacy × off   | 1105.520 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| ercot **atb** × off   | 1105.520 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| ercot legacy × ordc  | 1105.520 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| ercot **atb** × ordc  | 1105.520 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| ercot legacy × coopt | 1105.486 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| ercot **atb** × coopt | 1105.486 | 24.60 | 0 | 12.68 / 40.75 / 44.09 |
| pjm legacy           | 2352.002 | 34.24 | 0 | — |
| pjm **atb**           | 2352.002 | 34.24 | 0 | — |

The capacity trajectory is **byte-identical** across the FOM axis (and near-identical across the
scarcity axis — co-opt shifts dispatch by 0.03 Mt via reserve pricing, not the fleet). CO₂ is
identical to 3 decimals between legacy and ATB in every scarcity state and in PJM. **The
going-forward FOM level changes nothing in the realized forecast.**

Two compounding causes, both structural (not residual):

1. **The nameplate reliability floor retains 100 % of thermal.** ERCOT peak ≈ 93.7 GW,
   `firm_clean` (nuclear+hydro nameplate) ≈ 7 GW, so the floor
   `(peak − firm_clean) × (1 + 0.15) ≈ 100 GW` **exceeds the entire ~72 GW ERCOT thermal fleet.**
   Every economically-eligible unit is un-retired to (try to) clear the floor, so coal sits pinned
   at 12.68 GW for all six years **despite a screen net revenue of −8.5…+6.5 $/kW-yr against its
   52 $/kW-yr bar** — deeply, persistently eligible, never retired. The economic screen — and
   therefore the FOM level — is fully masked. This is exactly the defect the plan §3.1 floor
   redesign targets (wrong accounting basis: raw thermal nameplate vs a nameplate peak).
2. **The adequacy backstop backfills whatever does clear.** Identical force-builds of
   7168 / 459 / 1398 / 6236 / 6498 MW gas_ct in 2027-2031 in **every** cell regardless of FOM or
   scarcity — the fleet is driven by the peak-adequacy requirement, not the economics.

Even setting the floor aside, the ATB increase crosses **no** class's fleet-average revenue:
gas_cc clears both bars (≈39 > 30), gas_ct fails both (≈1.5 < 8), coal fails both (≈0 < 52). So
there is no fleet-average retire decision for the FOM level to flip here — consistent with the
behavioural unit test, which isolates the flip on a single unit whose revenue sits *between* the
two bars.

---

## 3. Revenue-side audit (plan §5 step 1)

Final-year (2031) capacity-weighted screen net revenue ($/kW-yr) from the diagnostic log line
`screen revenue stack [...]` in `apply_economic_retirements`, against the SOM anchors of §1.1:

| Fuel | off | ordc | coopt | Going-forward bar (legacy / ATB) | SOM anchor (new, 2024) |
|---|---:|---:|---:|---|---:|
| gas_ct | 1.3 | 1.6 | 1.3 | 8 / 21 | ≈ 68 |
| gas_cc | 39.0 | 39.1 | 39.2 | 12 / 30 | ≈ 89 |
| coal | 6.5 | 6.6 | 6.6 | 52 / 58.5 | — |

Findings:

- **gas_ct is understated ~40-50× vs the SOM proxy** (1.3-1.6 vs ≈68 $/kW-yr). The ORDC overlay
  lifts it only 0.3 $/kW-yr and the endogenous co-opt not at all, because the adequacy backstop
  floods the system with ~7 GW of extra gas_ct → reserves are ample → the perfect-foresight LP
  prices ~zero scarcity. This confirms `forecast-methodology-gaps-2026-06.md` G1/P1: the screen
  structurally under-collects scarcity/AS revenue.
- **gas_cc (≈39) clears both bars** — a fleet-average CC is not a retirement candidate at either
  FOM level; it sits below the SOM proxy (≈89) but comfortably above avoidable FOM, which is
  correct.
- The revenue side is **understated on its own external evidence** — independent of the retirement
  residual, exactly as the protocol requires (rule 1). It cannot be repaired by an FOM haircut or
  an `as_revenue_multiplier` sweep (rules 1, 14, 26).

---

## 4. Acceptance gates & decision (plan §5 step 4)

Gate (plan §5.4): flip the ATB FOM defaults **only if** the ATB-FOM × default-scarcity cell shows
(i) near-term 2026-2028 thermal retirement pace within the observed ERCOT band (~0.5-2 GW/yr) and
(ii) adequacy backstop force-builds ≈ 0 in the first three years.

| Gate | Observed (atb × ordc) | Pass? |
|---|---|---|
| 2026-2028 thermal retirement 0.5-2 GW/yr | **0 GW retired** (floor retains all) | ✗ (degenerate: the screen is inert) |
| Backstop ≈ 0 in years 1-3 | 7168 / 459 MW (2027/2028), FOM-invariant & structural | ✗ (but not FOM-attributable) |

**Decision: DO NOT flip.** Both gate legs fail, but the deeper reason is that **the FOM level is
inert**: with the nameplate floor retaining 100 % of thermal and the backstop backfilling
adequacy, no FOM value changes the fleet or emissions. Flipping an inert parameter and attributing
the §1.4 "fossil retirement accelerates, CO₂ down" effect to it would be false — the effect does
not exist until the floor and revenue mechanisms are corrected. Per rule 1 ("judge by structure,
not residual") and rule 14 (the accurate input stays; fix the compensating error at its source):

- **The ATB values (CT 21 / CC 30 / coal 45 $/kW-yr) stand as the externally-identified targets**,
  recorded here and in the DOF ledger, to be flipped once the prerequisites land. They are **not**
  reverted and **not** tuned.
- **Prerequisite A — floor accreditation (plan §3, later stage):** rebuild the retirement floor on
  the accredited (UCAP/ELCC) basis so it stops retaining the entire nameplate thermal fleet and
  the economic screen (and the FOM level) can express itself. This is the dominant blocker.
- **Prerequisite B — revenue-side fix (plan §5 step 2, later stage):** raise CT/CC screen revenue
  toward the SOM observable via *published* ORDC parameters / engaging the endogenous co-opt as
  the forward mechanism — never an FOM haircut or a residual-swept multiplier.

Only after A (and ideally B) will re-running this grid show a non-degenerate FOM response; the
flip commit is gated on that.

---

## 5. DOF-ledger entries (rule 21)

| Parameter | Current default | Identified target | Identification source | Status |
|---|---|---|---|---|
| `fixed_om_gas_ct` | 8.0 | **21.0** | NREL ATB 2024 Gas CT (F-frame) FOM; Brattle ERCOT CONE 2026 frame-CT component | target frozen; flip blocked on floor §3 + revenue §5.2 |
| `fixed_om_gas_cc` | 12.0 | **30.0** | NREL ATB 2024 Gas CC FOM (= repo's `NEW_ENTRY_COSTS["gas_cc"]` value) | target frozen; flip blocked |
| `fixed_om_coal` | 40.0 | **45.0** | NREL ATB 2024 / EIA-S&L existing-coal FOM class | target frozen; flip blocked |
| revenue stack (ORDC / AS) | ORDC overlay + exogenous AS | CT/CC net revenue ≈ SOM ($68/$89 /kW-yr) | Potomac ERCOT SOM Fig 56 | understated ~40× (CT); open root-cause, revenue-side stage |

The current 8 / 12 / 40 defaults are **mis-cited** in `frontend/data/parameters.json` as "NREL ATB
2024" — ATB 2024 existing-unit FOM is 21 / 30 / 45. They are in fact aggressive avoidable-only
(PJM-ACR-style) estimates below the ATB total-plant figure, with no primary citation. The
`parameters.json` notes are corrected to flag this and point here (value unchanged, no flip).

---

## 6. Handoff — remaining Stage-1 / later-stage work

**Landed this session (PR #1396 + this follow-up):**

- Pure-diagnostic per-fuel screen revenue stack log in `apply_economic_retirements` (rule-24 safe;
  no decision effect) — the revenue-side audit instrument.
- `scripts/run_fom_scarcity_grid.py` — the 2×3 ERCOT + 2-cell PJM probe matrix.
- Behavioural test `TestFomThresholdFlip` — retirement flips at the ATB FOM bar on a single unit
  whose revenue sits between the legacy (8) and ATB (21) $/kW-yr bars.
- This report + `fom-scarcity-grid-2026-07-05.json`; corrected FOM citations.

**Explicitly NOT done (blocked / deferred), with the blocking reason:**

1. **FOM default flip (CT 8→21, CC 12→30, coal 40→45).** Blocked: FOM is inert behind the
   nameplate floor + backstop; flipping now is a no-op mis-credited with an emissions effect.
   Unblocks after prerequisite A. When flipping: dedicated commit citing this report; update
   `parameters.json` value + source (ATB 2024 / EIA-S&L); re-centre the tornado FOM bands
   (low = legacy, high = ATB × 1.25) and add the paired `fom_and_scarcity` perturbation (plan
   §5.4). **These tornado edits are deferred with the flip** — re-centring bands on defaults that
   have not moved would misreport the base case.
2. **Floor accreditation (plan §3) — the critical next stage.** Rebuild the retirement floor on
   `accredited_firm_capacity_mw` (UCAP/ELCC), thread the wind/solar/storage-firm pools, replace
   `retirement_reserve_margin` with `PLANNING_RESERVE_MARGIN_BY_ISO`, add the CO₂-aware retention
   tie-break, and emit `floor_retention_log`. This is what makes the FOM recalibration
   *observable*; it should precede the flip.
3. **Revenue-side fix (plan §5 step 2).** Recalibrate ORDC from the published methodology / engage
   `ercot_thermal_as_endogenous` as the forward mechanism so CT/CC screen revenue approaches the
   SOM observable. Never an FOM haircut or `as_revenue_multiplier` sweep.
4. Foresight (EWMA/lookahead, plan §2) and the DC-load block (plan §4) — later stages, untouched.

**Collision note honoured:** no CAISO-touching change (scalar remediation B-CAI-1… is live on CAISO
scalars).

*Grid JSON: `docs/handoffs/fom-scarcity-grid-2026-07-05.json`. Produced 2026-07-05, W2-P3.*
