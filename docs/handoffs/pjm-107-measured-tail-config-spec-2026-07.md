# pjm-107/108/109 run-config spec — measured-tail cycle (gas daily shape + CC_LIKE belt)

**Date:** 2026-07-14 (Fable design session; owner approval required before any
solve). **Grounding:** `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md`.
**Base:** the `2026-07-13-pjm-105-symmetric-net` keeper recipe, replayed
byte-faithfully off its bundle meta (the `_pjm105_symmetric_net_probe.py`
pattern: pjm-98 meta replay + the G-22 flag set + symmetric-net virtuals).
**Run numbering:** pjm-106 stays RESERVED for the fleet_to_bins CC-HR re-gate
leg (caiso-81 lane E, OOM'd, unregistered — verify before reuse). This cycle
uses **pjm-107 / pjm-108 / pjm-109**. PJM carries 14 registered entries
(10 mains + 4 twins); registering this cycle may trip the top-15 retention —
displace oldest mains only, twins exempt.

**New code required: NONE in the model.** Both levers are existing, gated,
default-off mechanisms armed by config. The only new files are two ~20-line
probe drivers cloned from `scripts/probes/_pjm105_symmetric_net_probe.py`
(each applying one field override on top of the replayed recipe) and the
composite driver. This is a **runnable-flags cycle** → solve-session grade
(Opus/Sonnet), no mechanism engineering.

---

## 1. The three runs

### pjm-107 — leg A alone: `gas_daily_shape=True` (label `pjm 107 gas-daily`)

Exact delta vs the pjm-105 recipe: `ScenarioConfig.gas_daily_shape: False → True`.
Nothing else.

- **What it is:** the measured Henry Hub *daily* within-month shape injected
  onto the gas price series, mean-preserving per month (monthly delivered
  level byte-kept), including the re-carry onto every F923-overwritten gas
  plant-month (`fuel.py:3803–3817`) so plant-level monthly pricing keeps the
  daily swing. Composes with the keeper's `gas_plant_monthly_fuel_pricing`,
  `pjm_zonal_gas_basis`, `gas_monthly_actuals`, `dual_fuel_switching` (the
  oil-parity switch now sees real cold-snap days).
- **Citation:** measured HH daily prints, `data/raw/gas-prices/henry_hub_daily.csv`
  (EIA); mechanism docstring `scenarios.py:4664–4671`; precedents miso-50
  (coal-vs-gas flip days) and the NEISO daily-basis line (winter tail formed
  endogenously). Rule-13 class: delivered fuel price — forward years use a
  representative daily shape on the forward monthly level (already handled by
  the mechanism; forecast-native).
- **DOF ledger effect:** adds one measured-market entry; zero fitted scalars
  (no tunable exists on the mechanism).
- **Known bound (state honestly in the attestation):** HH shape only — the
  Jan-2025 *eastern-hub basis* blowout beyond the HH move is not carried
  (a PJM-hub daily-basis intake, TETCO-M3/Transco Z5 analogue of
  `transco_z6_ny_daily.csv`, is a separate chartered intake if leg A proves
  the winter lane but lands short).

### pjm-108 — leg B alone: CC_LIKE mid-curve scope (label `pjm 108 cc-belt`)

Exact delta vs the pjm-105 recipe:
`ScenarioConfig.pjm_offer_midcurve_segments: ("LONG_RUN",) → ("LONG_RUN", "CC_LIKE")`.
Nothing else.

- **What it is:** the already-live measured mid-curve floor
  (`pjm_offer_midcurve_conditional`, P1-only `mc_bid_adjust` seam, floor-only,
  VOLL-capped) extended to the CC_REGULAR econ rows. Row scoping is already
  rule-19-clean in code (`fleet.py:3295`): CC **econ** rows only — CT_FAST
  stays owned by the startup amortization, committed/must-run rows by the
  passthrough/commitment structure, CC **peak** rungs stay fitted-curve-owned
  (the pjm-99 top surface stays retired; nothing stacks).
- **Citation:** `pjm_offer_midcurve_condbinned.json` (36-month DataMiner2
  submitted-offer corpus, within-unit share ladders, extended top-share grid
  s0.97/s0.99, per-delivery-year + net-load-bin conditioning); midmerit
  finding §6 item 5 (the one remaining unmeasured mid-merit top, unblocked by
  the clamp removal). The floor target rides the measured HH-daily+basis
  gas-day normalizer (`fleet.py:3231–3236`), so leg B is event-day-responsive
  by construction.
- **DOF ledger effect:** adds one measured-market entry; begins retiring
  DOF #1's CC bands — the probe MUST emit the **dominance measurement**: per
  fitted CC band, the share of row-hours where the measured floor exceeds the
  fitted bid (a dominated band is retirable to 1.0 in a later byte-check
  cycle).

### pjm-109 — the composite keeper candidate (label `pjm 109 measured-tail`)

Both deltas together, iff **both** legs individually pass their gates (§2).
Full span `--year 2023 2024 2025`, one bundle (rule 16); zero-forcing
ablation twin registered alongside (rule 21); attestation carries the
pjm-105 ledger verbatim + the two measured entries (n_entries 16, residual
count unchanged at 6).

If exactly one leg passes its gates, the passing leg alone is the pjm-109
candidate (the other is a registered reject, rule 15). If both fail, no
candidate — register the probes, file the findings, stop (the C3c boundary
stands disclosed).

## 2. Pre-committed gates (decided BEFORE any solve; rule 1 — never the residual)

Structure/honesty gates per leg — these accept/reject the mechanism; C3c is
the *readout*, never the criterion:

- **G-A1 (leg A, integrity):** monthly mean preservation — the shaped
  delivered gas series' monthly means match the unshaped keeper's to
  numerical noise (<$0.001/MMBtu), verified no-LP from the resolved fuel
  grids before solving. A mean shift is a build bug, stop.
- **G-A2 (leg A, driver window — the ercot27 gate):** ≥ 70 % of NEW model
  > $200 hours (vs pjm-105's set) fall on days whose HH daily factor for
  that month is ≥ its own p90. New tail hours on ordinary-gas days = broad
  elevation, REJECT whatever the count.
- **G-B1 (leg B, scope):** LONG_RUN rows byte-identical to pjm-105's floors;
  no markup on any committed/must-run/sync or CT row; floor-only (no bid
  lowered). Verified from the markup matrix no-LP.
- **G-B2 (leg B, driver window):** ≥ 70 % of NEW > $200 hours sit in the
  surface's own top two net-load bins (≥ p90 conditioning) — the measured
  conditioning is the driver; off-window additions REJECT.
- **G-C (both, no-regression):** C1 16/16 stays; C2 within the keeper's
  de-regression bar; C3a stays PASS **and the 2023 near-exact mean does not
  degrade by more than the 2024/2025 means improve** (MW-weighted, per-year
  table published); C7/C8 stay PASS; 2023 tail ≤ 18 h, 2024 tail ≤ 12 h
  (scorer small-count bounds).

**Readout targets (pre-registered expectations, NOT gates):** 2025 tail
17 → ≥ 26 h with the additions concentrated Jan/Jun–Jul; DA-diag 2024/2025
means move toward zero; the dominance measurement (leg B) reported per band.
If 2025 lands < 26 h with both legs in and gates green, C3c remains FAIL as
a **disclosed LP-vs-MIP representation boundary** (diagnosis §B.4) — do NOT
reach for an adder, a haircut, or a re-tuned multiplier (rules 1/11/13), and
do NOT re-open the owner-closed reserve-supply lane.

**LOYO statement (rule 22):** both legs are zero-free-parameter measured
mechanisms — there is nothing to refit leave-one-year-out (pjm-105
precedent: "LOO is vacuous for this flip"). The rule-22 obligation is
discharged by the per-year criterion table (all three years scored and
published for each probe) plus the G-C per-year no-regression bounds.

## 3. Execution protocol (15 GB box)

1. `git fetch origin main` + branch from main; `git config user.email
   noreply@anthropic.com`, `user.name Claude`.
2. Swap first: `fallocate -l 10G /swapfile && chmod 600 /swapfile && mkswap
   /swapfile && swapon /swapfile`. `MALLOC_ARENA_MAX=2` on every solve.
3. `.venv/bin/python` for everything. Refetch the gitignored DA-virtual raw
   feeds BEFORE any solve (`scripts/fetch_pjm_da_virtuals.py --feeds
   hrl_da_incs_decs`, ~15 min, never concurrent with a solve) and regenerate
   the ramp-capability clean table (`regenerate_clean.py`) — the recipe
   carries `pjm_da_virtual_bids` + `measured_ramp_capability`.
4. No-LP pre-checks (G-A1, G-B1 scope, and the §1 dominance table can be
   computed from the built fleet without solving) — run them first; a failed
   integrity gate stops the cycle before it costs a solve.
5. Solves ALONE (one at a time on this box — the PJM plant-level+co-opt LP
   peaks ~15 GB), years SEQUENTIAL within each run (~8–10 min/yr), one
   background Bash task, no timeout. Order: pjm-107, then pjm-108, then
   pjm-109 (+ twin).
6. Score each via registration + `calibration_verdict` +
   `scripts/legitimacy_diagnostics.py --iso PJM --bundle … --json-out`;
   register EVERY completed run (keeper or reject) with the
   `calibration-report` skill in the same session (rules 15/16); honour the
   top-15 prune; label convention above.
7. pjm-109 keeper-bar extras iff gates pass: ablation twin, attestation
   (ledger + the two new measured entries + the leg-A HH-only bound note),
   keeper recommendation flagged to owner — `keepers.json` is owner-only.
8. Push: fetch-first `git push`; NEVER commit locally-regenerated PJM bench
   or `manifest.js`/`benchmark.js` (checkout them before committing); commit
   runs/registry/bundle-slim files + docs only. Commit trailer:
   `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` +
   `Claude-Session:` (the executing session's URL).

## 4. Chartered follow-ons (NOT this cycle — each needs its own session)

| leg | what | why sequenced later | grade |
|---|---|---|---|
| pjm-110: bituminous sigmoid re-derive | re-anchor `COAL_SIGMOID_DEFAULTS[PJM]` (+ the 0.65 floor) to the offer corpus's flat-in-gas implied passthrough (≈ 0.66–0.79) — retires 12+1 fitted scalars (DOF #4) | lowers coal offers ⇒ needs the CC_LIKE evening-margin structure landed first (midmerit §6 item 2); needs a derive script (source-data-triggered re-derive, rule 23 — supersedes #1347's premise) | Opus (derive + solve) |
| wefor measured residual | CAMPD short-outage statistics replace `wefor_multiplier=0.7` + `wefor_residual=0.015` (DOF #5/#6) | derive script + A/B; touches all thermal availability — own cycle | Opus |
| #1302 coal committed take-or-pay | evening-merit-style FINDING for the 5 sub-floor committed multipliers (DOF #2); candidate structure `coal_takeorpay_from_data` on EIA-923 Schedule-5 spot-vs-contract | diagnosis before any value moves (issue text); candidate C3a-trough lifter if drift persists post-109 | Opus (diagnosis first) |
| PJM-hub daily gas basis intake | TETCO-M3/Transco Z5 daily basis (the `transco_z6_ny_daily` analogue) under the existing `gas_hub_basis_daily` machinery | only if leg A proves the winter lane but lands short — data intake + `data-intake` skill contract | Sonnet/Opus |
| CC-band dominance retirement | neutralize measured-floor-dominated fitted CC bands to 1.0 with byte-delta evidence | needs pjm-109's dominance measurement first | Sonnet |

## 5. Owner decision requested

1. Approve the pjm-107/108/109 cycle as specified (flags-only, zero fitted
   scalars, gates pre-committed) → hand to an execution session.
2. Confirm the follow-on sequencing in §4 (in particular pjm-110 after the
   CC_LIKE leg, per midmerit §6 item 2).
3. Note: if C3c stays short after this cycle, the honest state is
   FAIL-as-disclosed-boundary (LP-vs-MIP online posture, pjm-82) — the
   alternative (accepting C3c as a documented limitation on the keeper line)
   is the owner's call, not a modeling lever.
