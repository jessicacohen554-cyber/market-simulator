# PREREG — nyiso-122: re-open queue item 4 (`nyiso_iroquois_winter_spread`) on new seasonal evidence

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only, rule 22) ·
**Keeper at entry:** `2026-08-04-nyiso-120-c119-scope`, determination **NOT-YET**,
C3c (`price_tail`) the sole ledgered caveat (budget 1 of 3, unspent).

**Committed BEFORE any solve.** The phase-0 decomposition below reads only
committed artifacts (the keeper's `hourly/` sidecars, the committed hourly actual
`actual_lmp_hourly_NYISO.parquet`, the committed bench) and the construction probe
evaluates an already-shipped function at two flag settings. No LP has run, no
derive script has been edited or re-run, and no `ScenarioConfig` value has changed
at the time this file is committed.

> **SESSION RENUMBERED nyiso-121 → nyiso-122, recorded not silent.** The brief
> opened this session as nyiso-121. That label was already spent on `origin/main`
> by the MISO-matrix-column session
> (`FINDING-nyiso121-miso-matrix-column-2026-08-04.md`), which had itself
> renumbered off nyiso-120 for the same reason. No pre-registered content changed.

---

## §1 — PHASE 0, and the finding that licenses re-opening item 4

`scripts/probes/_nyiso122_c3a_2025_decomp.py` decomposes the C3a-2025 gap
(−$6.53/MWh on this basis; the scorer reads −10.1 %) by **month × actual-price
band**. Result:

| | ≤$100 | $100–300 | >$300 | total |
|---|--:|--:|--:|--:|
| **Jan+Feb** | +0.20 | **−3.60** | −0.18 | **−3.58** |
| **Jun+Jul** | +0.72 | −0.66 | **−3.81** | **−3.76** |
| all other months | +2.67 | −1.66 | −0.21 | **+0.81** |
| **year** | +3.60 | −5.93 | −4.20 | **−6.53** |

**The 2025 C3a failure is two seasonally-separable objects, not one.**

1. **Summer (Jun+Jul), −3.76** — essentially ALL of it in the **>$300 tail** (33 of
   the year's 42 tail hours). This is **C3c**, whose queue is exhausted and whose
   re-open condition is the owner-chartered `Capital_Hudson` → Zone-F/G topology
   split. **Not touched by this session** (rule 19 `[R-ONE-MECH]`).
2. **Winter (Jan+Feb), −3.58** — in the **$100–300 band**, with only 5 tail hours
   contributing −0.18. A level/basis miss, a **different** object from (1).

Two independent corroborations that the winter half is real and specific:

- **December 2025 is essentially EXACT** (model 97.10 vs actual 98.12,
  contribution −0.06) on a $98/MWh month with $7.79 Transco Z6 NY gas. So this is
  not "the model cannot price a cold month".
- **February 2025 cleared at an implied heat rate of 16.5** (99.40 / 6.02) against
  December's 12.6 (98.12 / 7.79) — on *lower* Transco gas. The realized market
  says eastern February fuel was far dearer than the Transco Z6 NY monthly mean
  admits, which is exactly what the mechanism's own independent driver (the
  measured Algonquin citygate basis) says.

**Why this re-opens item 4.** The queue's blocker is *"re-arming alone just moves
the miss to summer"*. That premise predates the seasonal band decomposition and is
now measurably inapplicable: **summer's miss is not a fuel-priced miss.** Of the
Jun+Jul gap, −3.81 of −3.76 lives above $300, where price is set by the ORDC/RCPF
shortfall curve rather than by any unit's fuel cost — so a monthly gas-basis
reallocation cannot move it in either direction. The withdrawal months the
mechanism actually shaves (Mar–Nov) are months 2025 currently **over**-prices in
the sub-$100 band (+2.67). Rule 28(a): this cell is **not** adjudicated `R`/`I`/`G`
— it is a live queue item blocked on a condition, and this is new evidence about
that condition. The sequencing gate ("re-opens only AFTER the nyiso-110 arm's
verdict") **is discharged**: that arm solved INERT and its cell is `G`.

**Stated plainly as a limitation:** the joint condition as originally written asked
for a *summer scarcity lever* to accompany this one. No such lever exists — C3c is
exhausted. This session proceeds **without** it, on the argument above that the
summer half is out of this mechanism's reach entirely, and that argument is itself
one of the things the A/B tests.

## §2 — the mechanism, and what it is NOT

`nyiso_iroquois_winter_spread`, `ScenarioConfig` default `False`, **NYISO-only**.
Both declared prerequisites are already armed on the keeper (`nyiso_zonal_gas_basis`,
`gas_hub_basis_overlay`), so this is a genuine single delta.

- **Zero free parameters, zero new numbers, zero derive edits** (rules 5, 23, 24).
  The construction is the committed one and is only *evaluated* at both flag
  settings. It re-allocates the **measured SOM annual** Iroquois−Transco spread
  across months in proportion to the **measured Algonquin monthly basis**, capped
  at the measured Algonquin citygate monthly level.
- It is **not** a lever fitted to a residual. Its driver is a measured pipeline
  scarcity series; rule 23 `[R-FROZEN-DERIVE]` is satisfied because nothing is
  re-derived at all.

## §3 — CONSTRUCTION gates, measured EX ANTE (no LP) — `_nyiso122_iroquois_construction.py`

| gate | requirement | measured | verdict |
|---|---|---|---|
| **K1 annual conservation** | reference-hub annual mean unchanged | Δ = **0.00000** in 2023, 2024, 2025 | **PASS** |
| **K2 NYC untouched** | NYC delivered $/MMBtu unchanged in all 36 months | max \|Δ\| **< 0.005** | **PASS** |
| **K3 blast radius** | only NYISO gas zones move | eastern trio + Upstate_West only | **PASS** |

The per-zone delivered deltas for 2025 ($/MMBtu, ON−OFF) — the quantity the LP sees:

| zone | Jan | Feb | Mar–Nov | Dec |
|---|--:|--:|--:|--:|
| Capital_Hudson / Lower_Hudson / Long_Island | **+2.82** | **+3.58** | −0.75 … −1.23 | **+3.67** |
| NYC | +0.00 | +0.00 | +0.00 | +0.00 |
| Upstate_West | **−7.48** | −0.72 | +1.40 … +2.23 | −2.42 |

## §4 — PRE-REGISTERED PREDICTIONS (so a miss cannot be re-narrated as a hit)

1. **Jan+Feb 2025 improve** (their contributions become less negative). This is the
   mechanism's target and the whole reason for the arm.
2. **December 2025 DEGRADES.** Stated in advance and unambiguously: Dec-2025 is
   currently near-exact (−0.06) and receives the **largest single lift of any
   month** (+3.67 $/MMBtu on the eastern trio). This arm is expected to over-shoot
   it. A December over-shoot is **not** a surprise and does **not** by itself
   revert the mechanism (rules 1 / 14) — but it is a real cost and will be reported
   as one.
3. **December 2024 improves substantially** — currently −1.556, the worst month of
   2024, and it receives +3.49.
4. **2023 improves** — an over-priced year (+7.2 %) whose Mar–Oct months are shaved.
5. **The C3a-2025 NET direction is NOT predicted.** The Jan+Feb lift, the December
   over-shoot and the Mar–Nov shave push in different directions on different
   zones, and the eastern/Upstate split makes the sign genuinely undetermined by
   hand. **This is declared undetermined in advance rather than claimed afterwards.**

## §5 — SOLVE gates and KILL RULES

**Arms.** Both `scripts/replay_keeper.py results/calibration/nyiso120_c119_scopegate`,
`--year 2023 2024 2025` in ONE invocation each (rule 16 `[R-ALLYEARS]`), years
sequential (rule 12):

- **control** — no `--set`, solved at THIS HEAD. Required, not optional: this
  session rebased onto a newer `origin/main` than the keeper solved on, which is
  exactly the hazard that invalidated nyiso-120's first control.
- **treatment** — `--set nyiso_iroquois_winter_spread=true`.

| gate | requirement | if it fails |
|---|---|---|
| **G1 zero config delta** | exactly ONE differing key between arms | **KILL** — not a single delta |
| **G2 year span** | [2023, 2024, 2025] in both arms | **KILL** |
| **G3 control integrity** | control's 18 scored fields reproduce the keeper's | if not, the **control** (never the keeper) is the comparator, and the drift is reported |
| **G4 liveness** | max zonal \|Δλ\| ≥ 0.10 $/MWh in ≥1 year | **INERT** — record as `I`, no promotion |
| **G5 protective gates** | C6 governance, C7 shape, C8 forced-share all PASS in the treatment | **KILL** — a protective regression is disqualifying |
| **G6 no slack / no dump** | zero in both arms | **KILL** |

**KILL RULES — pre-registered, and binding whatever the residual does:**

- **KR1.** If the treatment introduces **any new FAIL** on a *load-bearing*
  criterion other than `price_mean` (i.e. C1 fuelmix, C2 sysvol, C3b price_shape,
  or C4 dispatch_corr), the arm is **NOT promoted**. C3a is excepted because it is
  the criterion under study and is already FAILing on the keeper.
- **KR2.** If the **free-class C1 score regresses** (free `n/10` falls), **NOT
  promoted** — the nyiso-120 P1 gate.
- **KR3.** If **C3c gets worse** (model >$300 tail count moves further from the
  actual 10/12/42), **NOT promoted**. The ledgered caveat's budget is 1 of 3 and
  this session does not spend another slot.
- **KR4.** If the determination comes out **worse than the entry NOT-YET**, rule 22
  **D-5(b)** applies: the promotion **STOPS and escalates to the owner**; it is
  never silently written.
- **KR5.** No follow-up tuning. If the arm lands badly, the response is to record
  the verdict and stamp the matrix cell — **not** to sweep a threshold, add a
  scalar, or re-derive anything (rules 5 / 21 / 23).

**What does NOT kill it.** A worse C3a-2025 alone does not revert the mechanism if
the construction gates hold and no protective/load-bearing gate regresses: under
rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]` a measured-input correction is not
reverted because a residual moved the wrong way. In that case it is escalated with
the numbers under KR4, exactly as nyiso-120 was — **not** promoted unilaterally.

## §6 — governance

Rule 12 years sequential within each invocation. Rule 13 `[R-MEASURED]`: every
measured price in §1 is a **validation target**; no measured outcome enters any
solve. Rule 15: both arms registered on the dashboard **this session**, keeper or
not. Rule 16: 2023–2025, one bundle each. Rule 19 `[R-ONE-MECH]`: the summer/C3c
half is explicitly NOT addressed here. Rule 21: zero free parameters, DOF ledger
unchanged. Rule 22: **training years only**; NYISO holds `complete` but NOT
`final`; the holdout spend freeze is ACTIVE and untouched; the phase-0 probe hard
-refuses any year outside {2023, 2024, 2025} even though the committed actual
parquet contains 2018–2022 and 2026. Rule 25 `[R-ISO-SCOPE]`: NYISO-only; no other
ISO's cell is stamped. Rule 28(a): item 4 re-opened on the new evidence in §1,
with the off-queue element (no accompanying summer lever) stated explicitly above;
28(b): the cell is stamped this session whatever the verdict.
