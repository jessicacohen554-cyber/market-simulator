# PRECOMMIT ADDENDUM — SCN-WS1b-r2 (relaunch): the form change, leg 2's hold, G-DRIFT

**Lane:** SCN-WS1b-r2 · **Branch:** `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz`
**Date:** 2026-09-06 · **Model:** `claude-opus-5` (rule 27 `[R-PUSH]`; this lane writes no `src/`)
**Base:** rebased onto `origin/main` at `1aab49a0`.

This is an **APPENDIX to `docs/handoffs/PRECOMMIT-scn-ws1b-2026-09-06.md`, which is NOT edited**
(rule 29 `[R-SCREEN]`: nothing in a precommit may be rewritten after a result is seen). It is
pushed **before this lane's first solve**, and it records the three things the relaunch charter
requires — plus a **fourth that the charter did not anticipate and that changes the leg**.

---

## (a) The form change: `carbon_price_delta=25` → `carbon_price_path=mid`

The original PRECOMMIT §1 ran the **reduced** form `--set carbon_price_delta=25`, because owner
card D-1 was open and `carbon_price_path` still carried **REPLACE** semantics — under which a
path-written arm was a carbon-price **CUT** of $16–$102/t on CAISO / NYISO / NEISO, inverting the
pair's premise on three of six ISOs.

**That gate is now released.** D-1 is ruled **S2 = FLOOR**, and SCN-WS1c landed the repair at
`b1996141` (verified an ancestor of this branch's HEAD): `effective = max(RFF path, program
trajectory)` on a program ISO, the path alone elsewhere. The reduced form is **retired**, and
this lane runs the charter's original full form, `--set carbon_price_path=mid`.

**Expected consequence, declared before any solve** (WS-1c FINDING §2/§2.1): the RFF **mid** path
never exceeds a state-program trajectory in any horizon year, so `mid` is **inert on CAISO /
NYISO / NEISO** in every year — the ruled S2 outcome, on the record when the ruling was made. The
charter expects the arm to be **live on ERCOT / PJM / MISO**. Per the charter, an inert arm is
reported **as a result**, with the resolved trajectory beside it, and this lane does **not** reach
for a bigger number to make the three program ISOs move.

## (b) Leg 2 is HELD under ruling S5 — declared, not run

The NEISO/ERCOT T1-F 2026–2030 carbon ladder (original PRECOMMIT §3.5) **is not run by this
lane.** It spans 2028–2030, so it crosses `ccs_retrofit_available_year = 2028` (original PRECOMMIT
§2.3, measured 2028 in all six ISOs), so it moves `gas_cc_ccs` — and SCN-WS2b measured that the
CCS emission-rate seam can make that answer **sign-wrong**: **+9.99 Mt as scored vs −6.01 Mt with
capture applied**, on NEISO 2030 (`FINDING-scn-ws2b-2026-09-06.md` §8). Ruling **S5** holds every
case with that exposure.

`docs/handoffs/scn-ws1b/launch_ladder.sh` and `carbon-ladder-cases.yaml` stay **committed and
unrun**. **What releases leg 2:** the capx lane's repair of the CCS emission-rate seam in
`src/market_sim/model/capacity_evolution/ccs.py` (the routed defect — explicitly **not** this
lane's file), after which the ladder runs as §3.5 specifies with no other change.

## (c) G-DRIFT verdict at the new base

**Form 4 (differencing against a committed incumbent) never applied to this lane** and does not
now: these are **forecast pairs**, so the control is the **REF arm of each pair, solved at the
same HEAD, in the same session, with one field between the arms** (original PRECOMMIT §3.1). No
control solve is spent beyond the six REF arms the pair definition already requires.

The one place drift *could* have bitten is the original PRECOMMIT §3.1's free G-DRIFT read — that
NEISO's REF/CARB would reproduce SCN-WS0's committed 2026 pair. **Audited, and the verdict is
LIVE, not inert.** `git diff d5be0216 HEAD -- src/market_sim scripts/run_full_horizon.py
scripts/lib` (WS-0's merge base → my HEAD) is **32 files, +4,091 / −350**, and the changed set
includes hunks that are unambiguously **LIVE on the backcast/forecast solve path** for NEISO
2026 — `policy/carbon.py` (+192), `policy/cap_and_trade.py` (+63, the S2 floor itself),
`config/scenarios.py` (+207), `config/constants.py` (+735/−350), `pipeline/solve.py`,
`data/fleet/eia860.py`, `data/zone_assignment.py` — plus `capacity_evolution/ccs.py` and
`retirements.py`, which are inert for a 2026-only solve (below `ccs_retrofit_available_year`) but
not for the horizon generally.

**Verdict: WS-0's committed NEISO 2026 numbers are NOT expected to reproduce bit-for-bit at this
HEAD, and any difference is DRIFT, not a carbon result** — exactly the disposition the original
PRECOMMIT §3.1 pre-registered for this case. It does not weaken the pair's control, because the
control is the same-HEAD REF arm, not WS-0's committed number.

---

## (d) NOT ANTICIPATED BY THE CHARTER — the phase-0 gate KILLS leg 1 as specified

Rule 29 `[R-SCREEN]` clause **(0)**: *"An arm that has a computable pre-solve gate does not reach a
solve until that gate passes."* This lane re-ran its phase-0 census against the **repaired**
resolver and the **new** form, through the solves' own builder
(`run_full_horizon.reference_config(iso, 2026, 2030, cmc=False)`).
Instrument + output: `docs/handoffs/scn-ws1b/phase0-recensus-path-2026-09-06.py` / `.json`.

**The `carbon_price_path=mid` arm is INERT AT 2026 IN ALL SIX ISOs — including ERCOT, PJM and
MISO, which the charter expects to be live.**

| ISO | REF 2026 | ARM 2026 | **Δ 2026** | 2027 | 2028 | 2030 | why inert at 2026 |
|---|---|---|---|---|---|---|---|
| ERCOT | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| CAISO | 30.0242 | 30.0242 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| PJM | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| MISO | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| NYISO | 23.6363 | 23.6363 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| NEISO | 26.0545 | 26.0545 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |

**Two independent causes, and only one of them is the one the charter predicted:**

1. **CAISO / NYISO / NEISO — the floor.** The program trajectory ($30.02 / $23.64 / $26.05 at
   2026) exceeds the mid path in every horizon year, so `max()` returns the program and the arm
   is a no-op. **This is exactly what the charter said to expect**, and it is a result, reported
   as one.
2. **ERCOT / PJM / MISO — the RFF path's own shape, which the charter did not account for.** Both
   arms resolve to **$0.00** at 2026 because the mid path's **2026 knot is itself $0**. The floor
   has nothing to do with it.

**And it generalizes past `mid` — this is a property of the axis, not of one path:**

| path | 2026 | 2027 | 2028 | 2030 |
|---|---|---|---|---|
| zero | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| low | **0.0000** | 2.0000 | 4.0000 | 8.0000 |
| mid | **0.0000** | 3.7500 | 7.5000 | 15.0000 |
| high | **0.0000** | 7.5000 | 15.0000 | 30.0000 |

`CARBON_PRICE_PATHS` (`config/fuel_trajectories.py:1132-1137`) anchors **every** registered RFF
path at **$0 in 2026** — 2026 is the paths' common origin knot. **Therefore no `carbon_price_path`
value of any kind can produce a non-zero signal in a 2026-only solve.** The charter's leg 1 — "six
paired T0 runs, 2026 only, REF vs `carbon_price_path=mid`" — is **structurally unrunnable as
specified**: all twelve arms would be six pairs of *byte-identical configs*, and ~82 minutes of LP
would measure solver determinism, not carbon.

**Gate G1 (premise), original PRECOMMIT §3.3 — "the pair is not the pair" — FAILS in all six
ISOs.** Under rule 29 clause (0) the arms therefore **do not reach a solve**, and this lane spends
no LP on leg 1 as chartered. This is a **STOP**, which is the only thing the screen gate is
permitted to do; nothing here promotes anything.

### (d.1) The minimal repair, declared here BEFORE any solve

The smallest change that makes the chartered experiment *exist* is **one extra horizon year**:
`--start-year 2026 --end-year 2027`, scoring the pair at **2027**.

- It makes the arm **live on ERCOT / PJM / MISO at +$3.75/t**, which is the experiment the charter
  describes, and leaves CAISO / NYISO / NEISO inert — also as the charter describes.
- **It stays inside ruling S5.** S5's hold rests on `ccs_retrofit_available_year = 2028`; a
  2026–2027 solve never reaches 2028, so it has **zero `gas_cc_ccs` exposure**, exactly as the
  2026-only leg did. The S5 reasoning extends without weakening.
- Cost: 2 solve-years per arm instead of 1 (~130 min LP for all six pairs; ~76 min for the three
  live ISOs alone).

**This lane does not take that step on its own authority.** It changes a pre-registered screen
year and the charter's explicit "2026 only", both of which are the desk's to set — and rule 29
forbids choosing a screen year after seeing a result, so the choice is recorded **here, before any
solve**, rather than made silently. **Routed to SCN-DESK** for the scope call, per the charter's
"if you must touch a file outside your regions, STOP and route to SCN-DESK".

Rule 29's own text anticipates this case and is the reason the repair is stated rather than
abandoned: *"Where it does not apply: a mechanism measured INERT in the candidate screen year
(screen it where it is live, or go straight to the full span)."*

### (d.2) Pre-declared expectations at 2027, if the scope call releases it

Unchanged in kind from the original PRECOMMIT §3.2, rescaled from +$25/t to **+$3.75/t** (a 6.67×
reduction), and applying **only** to ERCOT / PJM / MISO:

| ISO | Δ load-weighted price, predicted at +$3.75/t | Δ CO2, predicted | coal→gas re-order? |
|---|---|---|---|
| **ERCOT** | **+$0.9–1.5/MWh** | **−0.2 to −0.8 %** | marginal — visible in by-class CO2, small |
| **PJM** | **+$1.5–2.7/MWh** | **−0.6 to −1.5 %** | **YES** — largest coal fleet of the six |
| **MISO** | **+$1.8–3.3/MWh** | **−0.8 to −1.8 %** | **YES, strongest** |
| CAISO / NYISO / NEISO | **exactly $0.00** | **exactly 0** | n/a — identical configs |

Arithmetic bound (G4, unchanged in form): `Δp / 3.75` must land inside `[0, 1.08]`, the span of
the repo's own fossil `CO2_RATES`. The **footprint** claim, the **leakage** duty and gates
**G2–G8** are carried over from the original PRECOMMIT §3.2–§3.4 verbatim; only the multiplier
changes. **Honest flag on the magnitude:** at +$3.75/t the CO2 signal is ~1 % and may sit near the
LP's own re-solve noise on the smaller ISOs — a null there would be **weak evidence, not a
refutation**, and will be reported as such rather than as "carbon does nothing".

---

## (e) What this lane has spent, and what it has not

**LP minutes spent on leg 1: zero.** The gate that stopped it is arithmetic over the committed
resolver, and it cost seconds — which is rule 29 clause (0) working exactly as written, and the
same posture G-DRIFT takes toward control solves.

`data/clean` (FF plan §2.4 HARD prerequisite, ~55 min) is **not** regenerated on this container,
because no solve is authorized to run yet. It is the first step if the scope call releases the
2027 leg.
