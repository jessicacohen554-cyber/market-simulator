### 2026-07-13 — CAISO — caiso-80 (supply-consistent honest demand, owner-signed Option A): the 930 **Demand** cell carries the NG-cell corruption by identity — C1 FAIL→PASS (12/12), C2 +19.3% over→−6.6% under, C3a −8/−9/−12 pts with the pre-registered gradient, **PROMOTED to keeper** (owner re-confirmed on the registered record; cross-machine solver spread disclosed below); local-commitment driver design approved (sizes against a GROWN CT deficit)

The caiso-80 lane (caiso-79 plan §4, the C3a/CC body-base decomposition on the
honest bench) ran its three no-tuning steps and found the root cause upstream
of every mechanism the lane could have touched
(`results/calibration/FINDING-caiso80-demand-basis-wedge-2026-07-13.md`):

- **B1 (belly probe refreshed on caiso-78):** the caiso-65-vintage "belly
  under-commitment" story is dead — the model over-commits CC around the
  clock (overnight +0.6/+0.8/+1.5 GW, morning h6–9 +0.7/+1.7/+2.5 GW) and
  under-runs the h16–18 shoulder.
- **B2 (demand-basis adjudication, the caiso-72 STEP-0 candidate 4):** the
  CISO EIA-930 `Demand` cell — the model's demand input — carries the SAME
  fabricated solar-shaped block as the corrupt NG cell by the
  `Demand = NetGen + TI` identity (930's identity gap is only +1–2 TWh in
  2024/25 while the NG-cell unexplained block is +4.4/+10.8; monthly onset
  exactly 2024-05), plus a ~6 TWh/yr flat CHP host-accounting wedge and the
  chronic identity gap: **+10.4/+11.6/+18.5 TWh/yr (2023/24/25) of demand no
  real grid fleet served**. CAISO's own TAC "actual load" agrees with the
  cell to −0.8 TWh — it is computed from the same telemetry books, not an
  independent check. The model's energy balance closes against the wedge
  term for term (2024: gas +6.8, imports +6.9, solar +3.2, hydro +1.0).
  `runner._scale_demand` compounds forecast demand from weather-year actual
  load, so the corruption propagated into forecasts too.
- **B3 (fuel-basis level check):** monthly implied HR (mean λ ÷ citygate
  gas) shows the model price level is CORRECT (±5 %) in 2023's genuinely
  tight months (Feb 0.97×, Apr 1.01×, Jul 1.05×, Aug 0.98×) — the whole
  overprice is in soft/high-solar months (May 2.25×, Jun 1.74×) where
  phantom daytime demand keeps model gas marginal. Margin composition, not
  offer level: the lane's step-4 offer re-tune is CONTRAINDICATED (rule 1)
  and was closed without tuning.

**Owner signed Option A** (rule-14/15 adjudication, the demand-side
completion of the signed bench rework): replace the backcast demand input
with the supply-consistent honest series `demand(t) = 930 NetGen(t) −
NG_cell(t) + CEMS bench-gas grid(t) + cogen grid flat + geo/biomass fold-in
flat − TI(t)` = **207.40/212.19/205.59 TWh** (−4.8/−5.2/−8.3 % vs the corrupt
cell). Derived measured artifact
(`scripts/derive_caiso_supply_consistent_demand.py` →
`data/raw/reference/caiso-supply-consistent-demand/`, guard-railed to the
committed CEMS anchors and pre-registered windows), gated
`ScenarioConfig.caiso_supply_consistent_demand` (default off, CAISO backcast
only), supersedes `caiso_demand_clock_realign` by construction. Zero fitted
values; re-derives only on source updates (rule 23). Side fix in the same
series: the 2026-07-12 demand-threading optimization (`48ec6b9`) read the
PRISTINE per-year config for the CAISO demand flags (which arrive via
`prb_overrides`), silently threading RAW demand into probe-channel solves —
caught before any bundle was affected; the orchestrator now loads the
effective-flag series so must-run derivation, the persisted
`system.parquet` demand, the payload load-weights, and the LP ride ONE basis
(realign-only keeps its historical caiso-75..78 behavior).

- **caiso-80** (`2026-07-13-caiso-80-supply-demand` + zero-forcing twin
  `2026-07-13-caiso-80-supply-demand-ablation`): single delta on the
  caiso-78 keeper recipe — `caiso_supply_consistent_demand=True`. Solved
  2023-2025 in one invocation; registered from the
  `caiso80-solve-register-v2` one-shot (Data-API-only publish; run-1
  postmortem in the workflow header).
- **A/B vs the caiso-78 keeper (v2.4, same honest bench; REGISTERED = the
  CI-runner solve, commit 487c085), every load-bearing pre-registered
  direction confirmed:** C1 fuel-mix **FAIL → PASS (12/12)** — the honest
  +7.69/+10.62 TWh CC over-run eliminated; C2 gas **+19.3 % over →
  −6.2/−6.6 % (2024/25)**; C3a **+26.9/+37.0/+45.1 → +18.7/+28.4/+32.8 %**
  (falls with the pre-registered year-gradient, 2025 most; vs DA the
  residual is +8.9/+17.2/+29.1 %); C3b NRMSE 0.31/0.41/0.41 →
  **0.298/0.402/0.365** (local-verification print; registered statuses
  identical-FAIL); C4 gas r **0.861/0.918/0.868** with dispatch NRMSE
  0.305/0.257/0.32 (2024/25 r up; 2025 NRMSE improved from 0.38);
  C5a +3.2/+9.1/+14.6 % → **−8.3 % CAVEAT / in-band / in-band**; imports
  move toward the measured TI; C6/C7/C8 PASS hold; twin clean
  (zero-forcing FAILs fuelmix/prices — the keeper's floors carry real
  structure). LOYO within 2023–2025: every year improves independently on
  C2/C3a/C3b (the construction is per-year measured data; no pooled fit).
- **Cross-machine solver spread (DISCLOSED — first time it is visible on
  record):** the session's local verification solve of the identical recipe
  differs from the registered runner solve by ~0.5–1.2 TWh/yr of gas (HiGHS
  degenerate-optimum selection; 2025 gas 49.46 local vs 48.21 registered).
  At the band edges this flips two statuses: C2-2024/25 print −3.7/−4.1 %
  CAVEAT locally vs −6.2/−6.6 % FAIL registered, and C4-2025 NRMSE ~0.30
  PASS locally vs 0.32 FAIL registered. The registered record is the
  committed one; the spread itself is now a known ±band-edge hazard for
  future A/B reads.
- **Disclosed counter-moves (pre-registered risk + two direction misses):**
  the registered solve is now consistently ~5–7 % UNDER on gas (2024/25)
  and C5a-2023 flips to −8.3 % — the 2023-flat-wedge risk (host-accounting
  vs identity-gap split not identifiable from 930 alone) generalized; the
  honest statement of the remaining volume lane. C3c-2023 spurious tail
  GREW 458 → 665 h (supporting tier; scarcity-overlay interaction with the
  recommitted fleet — open). CT_PEAKER fell further (1.52/1.16/0.70 →
  0.71/0.56/0.27 TWh vs actual 4.13/4.33/2.37): the h16–18 demand rise did
  NOT recommit CT; the evening deficit the approved local-commitment driver
  sizes against is BIGGER, not smaller. Solar curtailment ~flat
  (pre-registered rise did not materialize).
- **PROMOTED to keeper (owner decision, taken twice):** the owner approved
  promotion on the session's local verification prints (C2 CAVEAT / C4
  PASS); when the registered record's band-edge flips (above) surfaced, the
  question was re-asked with the registered statuses and the owner
  **re-confirmed promotion** — rule 1, the honest demand basis is strictly
  more structurally faithful (the replaced cell is proven fabricated
  against CEMS + the 930 identity), every magnitude improves, protectives
  hold, and the flips are cross-machine solver spread. Keeper
  `2026-07-12-caiso-78-cc-hr` → `2026-07-13-caiso-80-supply-demand`. v2.4
  determination stays NOT-YET (C3a/C3b/C3c).
- **Registry:** caiso-74 inert-probe pair pruned (top-15 retention).
- **Owner decision (same session): the local-commitment driver design
  (`docs/handoffs/caiso-local-commitment-driver-design-2026-07.md`) is
  APPROVED as designed** — implementation still waits on the post-caiso-80
  deficit re-measurement per the doc's own sequencing; note the deficit
  GREW (above), so the response-curve sizing must use the caiso-80 payload.
- **Open after caiso-80** (rule-1 order): (i) the residual C3a body
  overprice (+18.7/+28.4/+32.8 %; vs DA +8.9/+17.2/+29.1 % — 2023 is now
  close to the DA basis, the 2024/25 residual is the live lane), (ii) the
  approved CT local-commitment driver (bigger target), (iii) the 2023
  under-shoot / C5a-2023 −8.3 % (the flat-wedge split), (iv) C3c local-tail
  formation + the 2023 spurious-tail regression, (v) PJM/NYISO/NEISO
  re-gate on the fixed `fleet_to_bins` (caiso-78 blast radius, still
  pending).
