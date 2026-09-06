# S2 — the DA/RT two-settlement structure: CHARTER (owner-funded 2026-09-06, session caiso-261)

**Owner decision (card, 2026-09-06): "Fund S2" — "Charter a two-settlement
design session (all-ISO LP core, Opus/Fable): DA schedule + RT re-dispatch,
storage arbitrage on the DA/RT spread. A large structural lane with its own
plan doc before any code."** This is the charter. **No code, no
`ScenarioConfig` field, no solve.** The plan doc is the funded session's
first deliverable and precedes any implementation.

## §1 — The object S2 exists for (measured five times)

The caiso-127 evening/overnight storage pin: the model's batteries and pumped
storage arbitrage the evening/overnight spread flat under single-market
perfect foresight, discharging **long at hod 22–05** (+0.14…+0.49 GW; at
hod 22–23 in 2025 li_ion +0.41 GW and PS +0.33 GW, caiso-258 §3) and
**short at hod 17–19** (−0.50 / −0.55 GW in 2025), while the real fleet —
which faces the DA/RT structure — keeps the spread (caiso-127 §2;
re-measured caiso-168, caiso-169, caiso-255b, caiso-256). caiso-169 §5
closed every cheaper substitute: the foresight-horizon family admits only
24 h or ∞ (any other value is fitted); every shaped or scalar storage
price cancels from the pinned-day identity; a belly SOC anchor is an
outcome pin. **What remains is the genuine two-market structure, and its
size is specified, not gestured at:** *"a second LP solved on day-ahead
information plus a measured DA-vs-actual forecast-error input … two 8,760
solves per year, an information structure the pipeline does not have, and
a decision about which λ is the scored price."*

## §2 — What the design session must decide, in order

1. **The information difference.** Two perfect-foresight settlements are
   algebraically one; S2 bites only through an explicit DA-vs-actual
   difference. The admissible input (rule 13): CAISO's own published
   day-ahead **forecasts** (load `SLD_FCST` DAM, wind/solar `SLD_REN_FCST`
   DAM — OASIS, continuous, forward-regenerating) against the realised
   series the backcast already uses. The DA LP dispatches on the forecast;
   the RT LP re-dispatches on actuals with the DA schedule as its starting
   state. **Never** a fitted error term, never a realised-flow pin.
2. **What carries between the two solves.** Commitment state (the P0→P1
   floors), storage SOC trajectory, DA awards as the RT re-dispatch's
   baseline — and what is *free* in RT (storage re-optimises on the RT
   price; thermal moves within ramp/min-gen). ERCOT/PJM/NYISO/NEISO/MISO
   share the LP, so the design is ISO-agnostic (rule 25: no ISO-tuned
   value).
3. **The scored λ.** The rubric scores C3a/C3b/C3c on the **RT** hourly
   price and reports DA; S2 produces both natively. The decision is which
   dual each scored quantity reads (RT energy-balance dual for C3a/b/c; DA
   dual for the DA diagnostic; the crossover window reports both).
4. **Cost.** Two 8,760 LPs per year (+P0) — a CAISO 3-year bundle goes from
   ~45 min to ~90 min; every ISO's keeper is affected, so the mechanism is
   GATED (`two_settlement_enabled`, default off), armed per ISO through its
   own PRECOMMIT, screened on ONE year first (rule 29), and every backcast
   keeper stays byte-identical while off.
5. **The rule-19 reconciliation.** The M1 charge-allocation floors
   (`caiso_charge_allocation_schedule`) and the caiso-99 envelope represent
   DA-scheduled storage conduct by proxy; the design states which of them
   S2 replaces and which it composes with — never stacks.

## §3 — Gates the plan doc must fix ex ante

* **G-IDENT**: with zero forecast error the two-settlement run reproduces
  the single-market keeper to the MW (the algebraic identity, tested).
* **G-STRUCT (STOP-only screen)**: the storage response has the sign the
  identity predicts — evening discharge up, overnight discharge down — and
  is confined to storage + the marginal gas rows; renewables/nuclear
  footprint < 0.5 %.
* **Excluded from every basis**: C3a and C4, both ways; the C4-2025
  (0.298 vs ≤ 0.30) and C3c-2023 (23 vs 47) exposures re-stated before any
  solve.
* **PRIMARY** (caiso-127 §6): the keeper's evening hydro starvation
  (−251 / −376 / −264 MW) heals to within ±150 MW with **no hydro-side
  change**.
* Screen year: the year with the largest measured DA-vs-actual forecast
  error energy (the mechanism's own footprint), fixed before the residual
  is looked at.

## §4 — Not authorized by this charter

Any storage price, adder, horizon or anchor (caiso-169 §5 closes them
all); any per-ISO tuned value; arming S2 on any keeper before its own
PRECOMMIT and screen; touching the caiso-201 resting-state objects (PS
water state, the 8,800 MW residual).

**Genealogy:** caiso-127 §6 (filed), caiso-129 §5 (named), caiso-169 §5
(specified), caiso-201 Q2 (unfunded), caiso-256 (measured a fourth time),
caiso-258 §3 (fifth), **caiso-261 (FUNDED)**.
