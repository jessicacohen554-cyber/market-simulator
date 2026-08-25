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

## ROUND 1 RESULT + ROUND 2 GRID (amendment, fixed before any round-2 solve)

Round-1 measured: R1 (3.0/1.0) **C3a −34.5 % / C3b 0.622 / C3c 155** —
CLEAN on all kills (coal +0.094 TWh, no new shed, off-season intact; spur
band 60 reported); R2 (3.0/1.75) −27.6 %/0.580 — **KILLED, G-COAL148
+6.04 TWh**; R3 (5.0/2.5) −16.8 %/0.465 — **KILLED, G-COAL148 +8.38 TWh +
G-OFFSEASON**. Diagnosis: `econ_high` scaling buys level by re-ordering the
merit stack (coal over-runs measured generation by 6–8 TWh) — the corrupt
lever, excluded from round 2; the `peak`-band family is clean and the
remaining gap is the deep tail (model 24 h ≥ $500 vs actual 102).

**Round 2 (three further 2023-only solves): k_eh = 1.0 fixed; k_peak ∈
{6.0, 10.0, 14.0}.** Same kills, same reporting. **Selection: over ALL
clean points from both rounds** (R1 + round-2 survivors), min |official
C3a-2023|, C3b tiebreak; the overall winner is the run registered under
round 1's registration clause (R1's conditional winner status transfers —
nothing is registered until the campaign's rounds in this session
conclude).

## ROUND 2 RESULT + ROUND 3 GRID (amendment, fixed before any round-3 solve)

Round-2 measured, ALL CLEAN (no kill fired; coal +0.10 TWh flat across all
peak-only points; off-season intact; zero shed; spur band saturated at
~68 h): R4 (6.0) −30.0 %/0.526/173 · R5 (10.0) −25.6 %/0.434/173 · R6
(14.0) −21.3 %/0.344/180. The response is monotone ~+4.4 pp per Δk_peak=4
with no structural cost, and at k_peak ≈ 40–50 the peak-tranche offers land
at $3.5–4.5k — the measured 2023 evening ask range the record documents
(ercot-161/162 SCED asks $3.4–5k), so the fitted scalar converges toward
the measured conduct level rather than past it.

**Round 3 (three further 2023-only solves): k_eh = 1.0 fixed; k_peak ∈
{20.0, 30.0, 45.0}.** Same kills, same reporting, plus one added
sanity report: max peak-tranche offer $/MWh (must stay ≤ VOLL $5,000 — a
breach is a REPORT naming the clip, not a kill; the LP price is
VOLL-bounded regardless). Selection unchanged: over ALL clean points from
all three rounds, min |official C3a-2023|, C3b tiebreak; register the
overall winner.
