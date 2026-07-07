# ERCOT VRE under-curtailment — step 2: dumping + storage timing (2026-07-07)

**Scope.** Step 2 of `docs/handoffs/ercot-vre-undercurtailment-2026-07.md` §5.2.
Step 1 (ercot39) ruled out measured NP6-86 GTC limits. This step checks the two
next real mechanisms in order: (1) negative-price **dumping** and (2) **storage
absorption timing**. Both are **cleared as the lever** — the diagnosis localises
the under-curtailment to the reduced 8-zone West→North transmission corridor, not
to the objective's dump guard or to storage arbitrage.

Read-only analysis on a byte-faithful re-solve of the `ercot38` keeper config
(`results/calibration/_diag_ercot38_baseline`, static TTC — reproduces ercot38's
dispatch exactly: model wind 110.84 / 116.28 / 120.38 TWh for 2023/24/25, matching
the registered bundle). No config delta, so **no new dashboard run** — the
[3e] table and C-scores below are `ercot38`'s already-registered result
(`2026-07-06-ercot38-measured-hsl-2425`: C2 FAIL, C3a PASS, C5c PASS). Analysis
driver: `scripts/_diag_vre_curtailment.py`. A `dump` column was added to
`system.parquet` (`scripts/run_calibration_full.py`) so the LP's per-zone
overgeneration `Dump[z,t]` is persisted for this and future oversupply work.

## [3e] model vs ISO-reported curtailment (reproduces ercot38)

| year | fuel | potential TWh | model TWh | model curt % | reported curt % | ratio |
|---|---|---|---|---|---|---|
| 2023 | wind | 113.28 | 110.84 | 2.16 | 4.67 | 0.46× |
| 2023 | solar | 34.01 | 33.56 | 1.32 | 6.29 | 0.21× |
| 2024 | wind | 119.19 | 116.28 | 2.45 | 6.01 | 0.41× |
| 2024 | solar | 50.66 | 49.74 | 1.82 | 7.35 | 0.25× |
| 2025 | wind | 123.70 | 120.38 | 2.68 | 7.07 | 0.38× |
| 2025 | solar | 72.83 | 70.61 | 3.05 | 7.29 | 0.42× |

Model captures only 21–50% of reported curtailment volume — the handoff's gap,
reproduced exactly.

## Q1 — Negative-price dumping: NOT the mechanism (dump never binds)

**The `dump_cost` guard never fires. System dump = 0.0000 TWh, 0 hours, all three
years.** This is correct LP behaviour, not a bug: reducing wind/solar below their
CF ceiling ("curtailment") costs ~$0, strictly cheaper than paying `dump_cost` to
spill, so the LP always curtails renewables before it ever dumps. "Dumping" and
"curtailment" are therefore distinct — the real under-curtailment signal is W/S
below potential (the [3e] table), and the question is why the LP so rarely
*needs* to curtail.

**Why the model doesn't reach oversupply — the West→North corridor is wide open.**
The reduced 8-zone West/Panhandle export corridor is 12,680 MW aggregate
(West→North 7300 + West→South_Central 2700 + Panhandle→North 2680). Per-link
saturation (flow ≥ 95% of TTC):

| link | TTC | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| West→South_Central | 2700 | 79% | 76% | 68% |
| Panhandle→North | 2680 | 38% | 44% | 55% |
| **West→North** | **7300** | **1.3%** | **3.8%** | **3.2%** |
| aggregate | 12680 | 1.5% | 4.5% | 3.7% |

The two small links (West→SC, Panhandle→North) *are* chronically bound — but the
big **West→North (7300 MW) link almost never binds** and its mean flow is near
zero or negative (North → West). It is a wide-open relief valve for West/Panhandle
surplus.

Decisive cut — in the hours ERCOT actually reported wind curtailment:

| year | West→North mean flow | mean spare headroom | curt-hrs with >500 MW spare |
|---|---|---|---|
| 2023 | −201 MW | 7,501 MW | 98% |
| 2024 | +725 MW | 6,575 MW | 94% |
| 2025 | −72 MW | 7,372 MW | 96% |

In **94–98%** of the hours reality curtailed wind, the model's West→North pipe is
nearly empty. The surplus flows out freely, the West LMP stays positive (West
price ≤ $1 in only 22–42% of reported-curt hours), and the LP has no reason to
curtail. Reported wind curtailment, by contrast, is **chronic — active in 66–90%
of ALL hours**, evenly split day/night, i.e. driven by continuous sub-corridor
(nodal) West/Panhandle congestion, not by system-wide oversupply events.

**Must-run is not the cause (task Q1 parenthetical, ruled out).** D-2 forced
energy in ercot38 is `chp_steam` (coastal industrial cogeneration, ~11 TWh) plus a
small peaker `reliability_floor` — no coal/CC must-run, none in the West. And by
the West energy balance, max West wind dispatch = `West_load + export − must_run`,
so must-run *raises* curtailment; it cannot explain *under*-curtailment. The
headroom eaten in the real curtailment hours is transmission headroom on
West→North, not thermal headroom.

**Consistent with step 1.** This is exactly why ercot39's measured aggregate GTC
didn't move it: the WESTEX limit maps onto West→North (+ a West→SC share), the one
link that is rarely the binding element. Real curtailment is set by finer nodal
constraints the 8-zone reduction collapses into one fat 7300 MW pipe. It is a
**topology-resolution gap**, not a dump-guard or an aggregate-limit gap.

## Q2 — Storage absorption timing: legitimate, not eating the wrong hours

Storage charges **preferentially during** curtailment hours and is not
arbitraging them away:

| year | total charge | mean charge in reported-curt hrs | vs non-curt hrs | midday(10–16) charge share | evening(17–21) discharge share |
|---|---|---|---|---|---|
| 2023 | 0.63 TWh | 77 MW | 85 MW | 12% | 67% |
| 2024 | 0.86 TWh | 116 MW | 77 MW | 35% | 83% |
| 2025 | 3.15 TWh | 379 MW | 164 MW | 51% | 87% |

As solar penetration rises the charge shifts into midday (12% → 51%) and discharge
into the evening (67% → 87%) — the correct solar-arbitrage shape, charging into the
midday solar surplus that would otherwise curtail. Storage is idle in 74–90% of
reported-curt hours only because most of those are overnight wind-curtailment hours
when the (small, ~4h) battery fleet is empty/discharging. It competes on economics
in the right direction; it does not systematically eat the hours curtailment would
otherwise occur. **No bug.**

## Conclusion & recommended next step

Neither dumping nor storage is the lever. The under-curtailment is a structural
transmission-resolution limitation: the 8-zone West→North (7300 MW) corridor is
far larger than the nodally-fragmented real network that bottlenecks West/Panhandle
wind, so the LP almost never reaches the constrained state that forces curtailment,
and aggregate GTC limits (static or measured) cannot supply the missing structure.

Two forward-admissible fixes remain, both requiring owner sign-off (guardrails
CLAUDE.md #1/#13/#14, handoff §6 — no HSL pinning, no residual-tuned adder, no GTC
re-probe):

1. **Topology refinement** — split the West/Panhandle zone (or the West→North
   corridor) so the chronically-binding nodal paths are represented. Largest,
   most faithful, but a substantial structural change to `iso_configs`/`constants`.
2. **Derived, forward-admissible curtailment-share driver** (handoff §5.2 last
   bullet; WS-A precedent, `docs/handoffs/ercot-as-coopt-plan-2026-07.md` §4): a
   curtailment share as a function of net-load percentile / hour-of-day / season,
   fit to the **measured GTC-binding frequency / RTOLCAP-style supply shares** —
   never the price or volume residual — with a DOF-ledger identification source
   before any keeper (rule 21/23). The last-resort fallback; smaller than (1) but
   carries its own identification burden.

This step's job was to check dumping and storage; both are cleared and the lever is
localised. Building either fix is a new decision for the owner, not part of step 2.
