# PRECOMMIT — ercot-235 round 1: the 2023-discrete-config offer-surface sweep (grid, gates, selection rule), fixed before any solve

**Date:** 2026-08-25 · **ISO:** ERCOT · **Authorization:** the owner's
2023-discrete-config order (verbatim in the ercot-235 log entry): solve 2023
for its own conditions; rule 16 waived; Q-B/R-A superseded by the owner for
2023-targeted rounds. **This is a rule-1-sanctioned offer-curve TUNING round
on a discrete 2023 config** — structure frozen at the
`2026-08-25-234-eastex-identity` keeper recipe; every swept scalar is
residual-identified and will be DOF-ledgered as such on any registered run.

**Phase-0 basis (zero-solve, keeper 2023 sidecars):** the miss is Jun/Aug/Sep
afternoons-evenings — Aug 61.6 % / Sep 19.3 % / Jun 14.0 % of the lw-gap
(Aug model $93.02 vs actual $220.16; Jun–Sep h12–20 model $61–142 vs actual
$137–287); off-season months calibrated within ±$3.5 and overnight slightly
over. Actual-band structure: [100,200) 165 h (model mean $67), [200,500)
77 h ($119), [500,1000) 43 h ($168), ≥1000 59 h ($533). Band-targeted
multiplier lifts localize to those windows through the merit order itself —
no time window is coded.

## The grid (three 2023-only solves, keeper recipe + ONE composite knob)

Scale the gas-group top-band multipliers (`peak`, `peak_ladder` mults,
`phys_peak`) by k_peak and the `econ_high`/`phys_econ_high` bands by k_eh,
all 8 gas groups (`offer_curve_by_group`), coal/storage/renewables untouched
(coal curves are measured per-plant; storage offers are structural):

- **R1:** k_peak 3.0, k_eh 1.0 (peak-only)
- **R2:** k_peak 3.0, k_eh 1.75
- **R3:** k_peak 5.0, k_eh 2.5

Years: **2023 ONLY** (owner rule-16 waiver, invoked; rule 22 still bounds to
the training window). Solves run SEQUENTIALLY — one 2023 solve peaks ~11 GB
of this container's 15 GB, so rule 12's own memory cap binds at 1.

## Gates and selection (fixed ex ante)

KILL (a run failing any is ineligible for registration as the round's pick;
it is still reported):
- **G-SHED-NEW:** any 2023 shed hour not in the keeper's 2023 set (keeper:
  none).
- **G-OFFSEASON:** any off-season month (Jan–May, Oct–Dec) lw-price moving
  more than **$5/MWh** further from actual than the keeper's (protects the
  calibrated months from the lift).
- **G-COAL148:** 2023 coal TWh rise vs keeper > 0.5 TWh.

SELECTION among survivors: min |official C3a-2023|, tiebreak lower C3b-2023.
The winner is REGISTERED (rule 15) as a 2023-only run with the discrete
config in its run_config and a DOF-ledger note naming k_peak/k_eh as
residual-identified 2023 scalars; whether it becomes any kind of keeper is
the owner's call, reported not assumed. If NO grid point reaches the C3a
band (±10 %), the best survivor is registered anyway and the k→C3a response
curve reported for round 2.

Side reporting per run: monthly lw table, band coverage (model hours in
[200,500)/[500,1000)/≥1000 vs actual 77/43/59), G-SPUR banded+lidless, C3c
tail count, class-energy span vs keeper.

Instrumentation: `scripts/probes/ercot235_offer2023_sweep.py` (builds the
scaled `offer_curve_by_group`, replays the keeper meta 2023-only via
`replay_keeper.py --set`, scores officially). Official scorer already
validated against the keeper this session. Sweep bundles are LOCAL
probe bundles (W-2, gitignored) except the registered winner.
