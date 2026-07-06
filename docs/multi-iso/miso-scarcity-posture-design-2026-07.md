# MISO scarcity posture — design note: commitment-posture lever + Midwest locational reserve zone

**Date:** 2026-07-06. **Lane:** Wave-3 MISO L-14. **Status: §A BUILT 2026-07-06
(`miso_commitment_posture`, GATED default-off) and honesty-gate REJECTED as probe
`2026-07-06-miso-43-commitment-posture` — the pooled LINEAR relaxation holds 3.7-4.2× the measured
cleared reserve online (level FAIL; see the probe's `SUMMARY-posture-gate.md` and the 2026-07-06
L-14-continuation calibration-log entry). The measured ASM gate data landed in `data/raw/MISO-AS`
(`fetch_miso_asm.py`); §A's min-run/min-down window rows remain the deferred follow-up and §B stays
DATA-BLOCKED on the zonal requirement series.** Companion to
`docs/multi-iso/miso-scarcity-tail-diagnosis.md` (miso-39 gate 4
CLOSED-NEGATIVE, kept per rule 1) and `results/calibration/FINDING-miso-cc-decomposition-2026-07.md`
(the CC +44 TWh exemplar). The diagnosis proved that under deterministic perfect-foresight
hourly dispatch, MISO's published reserve demand curves cannot reach their shortage steps
through ANY admissible supply-side reserve structure: market-wide deliverable reserve never
falls near the requirement (≥11 GW vs 4.4 GW) and the South zonal requirement is always
clearable at ≤ ~$23/MWh of re-dispatch, because the LP may re-time any unit's energy at zero
commitment cost. This note designs the two remaining real mechanisms.

## Targets (recorded before any build, per the diagnosis's discipline)

- Reachable: the **DA-visible** scarcity — order **1 / 24 / 38 h** (2023/24/25) — plus the
  DP-1 CC posture wedge (P1 carries +34% committed CC energy vs MIP;
  `docs/handoffs/mip-uc-crossbench-*`). 135.6 × 1.34 ≈ 181.7 ≈ the keeper's 179.9 TWh —
  the commitment posture is magnitude-consistent with the whole C1 CC row.
- NOT reachable and never to be tuned toward: 2023's all-RT single-hour transients (30 h) and
  ~95% of 2024's RT tail — forecast error / 5-minute dynamics, outside the representation. A
  mechanism sized to hit 30/37/88 fails the rule-13 admissibility test by construction.

## A. Commitment-posture lever (pooled linear UC relaxation in P1)

**Phenomenon owned (rule 19):** the LP's free part-load/re-time relief channel — the measured
$4–23/MWh re-dispatch that always out-competes the $200 reserve step — plus the CC baseload
lift (C1) and the priced-out CT/ST_GAS under-run. One mechanism, three symptoms; it must NOT
be stacked with any new floor on the same classes (D-2 attribution today: only the CT evening
reliability floor and CHP steam floors touch these classes, different phenomena, kept).

**Mechanism (still pure LP — no MIP, P1 remains THE run):** per (zone × fuel-class) pool — the
same ~30-pool grain the pergen reserve build proved memory-feasible at MISO scale (rule 12 /
G-40; per-unit U columns are memory-infeasible) — add a continuous online-capacity variable
``U[p,t] ∈ [0, cap_p(t)]`` with:

1. ``P[p,t] ≤ U[p,t]`` and ``P[p,t] ≥ mlf_p × U[p,t]`` — dispatch is coupled to online
   capacity; being online costs min-load energy at the pool's committed-band offer.
2. ``SU[p,t] ≥ U[p,t] − U[p,t−1]``, cost ``startup_$/MW × SU`` — re-timing energy now pays a
   real startup, not zero.
3. Min-run/min-down smoothing on U via the existing linear run-length machinery (the P0
   run-length screen already discovers runs; reuse, do not duplicate).
4. **Reserve coupling — the scarcity payoff:** the pergen deliverability cap becomes
   ``R[p,t] ≤ ramp10_p × U[p,t]`` (online-gated) instead of availability-scaled nameplate.
   Offline capacity contributes no 10-minute ramp, so in thin hours the zonal/market families
   can genuinely run short and price the published curve steps.

**Driver (rule 17a):** unit physics and measured operating economics — CEMS-measured min-stable
levels (``mlf`` from the same derive pipeline as the existing min-stable loads, re-derived only
on source-data updates, rule 23), engineering startup costs by class (published ranges; PJM
Manual-15-style cost basis), and min-down hours. Eligibility gates on parameters, never class
tuples (rule 18): fast-start pools (min-down ≤ 2 h, startup < $30/MW — CT peakers, ICs) get
``mlf = 0`` / free U — they are never economically bridged.

**Window (rule 17b):** none needed and none permitted — this is not a floor and forces no
energy (D-2 forced-energy attribution must show ZERO MWh attributed to it; the min-load term
binds only units the LP *chooses* to keep online for economic/reserve reasons). If any
diagnostic shows it forcing energy a driver can't explain, that is a bug, whatever the residual
does.

**Forward story (rule 17c):** regenerates entirely from fleet physics (mlf, ramp10, min-down,
startup cost by class/vintage) and forecast fuel prices; no backcast-only input. Identical
machinery serves forecast years unchanged.

**Honesty gate (the PJM pattern — accept/reject BEFORE looking at the tail residual):** the
build is gated against **measured MISO cleared reserve MW and reserve MCPs by zone** (MISO
market reports; the data ask recorded in the diagnosis §5). Acceptance = modeled online
headroom / cleared-reserve behavior tracks the measured series (level + event-day direction);
the >$200 tail count is NEVER the gate (rule 1/13). Score full-span 2023–25, register keeper
or rejected probe either way (rules 15/16).

**Expected side-effects to verify, not tune:** CC_REGULAR level falls toward the DP-1 wedge;
CT_PEAKER/ST_GAS pick up the shoulder/evening energy real units serve while CC is offline;
LOYO-scored before promotion (rule 22's in-sample LOYO clause).

## B. Midwest locational reserve zone (data-gated)

**Phenomenon owned:** the 2024 Winter Storm Heather DA block (Jan 14–17, 24 h) — a Midwest
event the South family correctly does not fire on; market-wide RBDC stays ≥11 GW deliverable
under perfect commitment, so only a Midwest sub-regional family plus lever A can price it.

**Mechanism:** mirror of the existing South zonal family (`reserve_config._miso_design`): a
Midwest zone-group reserve requirement with the published BPM-002 §5.2.1.2 demand-curve steps
and the pergen 10-minute deliverability caps (online-gated once A lands). No new code shape —
the family machinery is generic; only the requirement series is new.

**Driver / admissibility:** the requirement must be MISO's own published quantity. BPM-002
zonal reserve zone definitions are quarterly IROL-based; the **blocking data ask** (unchanged
from the diagnosis, restated as the actionable item): MISO historical zonal operating-reserve
requirements (MW by zone-group, 2023–25) and zonal reserve MCPs. Without that series the
family is DATA-BLOCKED — a hand-sized Midwest requirement would be a fitted breakpoint and is
forbidden. If only the current-quarter definitions are obtainable, the family may ship
forecast-forward only (requirement regenerates from MSSC/IROL each planning year) and stays
out of the backcast score.

**Window:** none — fires whenever requirement + deliverability bind.

**Forward story:** requirement regenerates each planning year from the published basis
(MSSC / IROL studies), responds to fleet and topology changes.

## Sequencing and budget

1. **A first.** It is simultaneously the C1-CC lever (DP-1 wedge), the intra-gas
   misallocation lever, and the precondition for ANY reserve family to run short. One
   structural build, LOYO-scored, honesty-gated on measured cleared reserve.
2. **B second**, once the zonal-requirement series lands (file the data ask now — longest
   lead time). B without A cannot fire (the diagnosis measured exactly this: re-dispatch
   relief always undercuts the curve at zero commitment cost).
3. Memory (G-40): pooled U adds ~30×8760 columns + 3 row families — same order as the pergen
   reserve build that fit in ~15 GB with the 12 GB swap. Per-unit commitment variables are
   OUT at MISO scale. Years remain strictly sequential.

Neither mechanism is a floor; the existing CT-evening reliability floor and CHP steam floors
are untouched and no new min-gen enters (rules 17–20). Zero fitted parameters: every input is
measured (CEMS mlf), published (startup-cost basis, BPM-002 curves, zonal requirements), or
physics (ramp10, min-down).
