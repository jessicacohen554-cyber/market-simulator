# RESEARCH — ercot-220b (owner-directed, ercot-220 session addendum): what can still legitimately move the 2023 miss — the miss DECOMPOSES, two-thirds of it does NOT need the blocked capability truth, and exactly ONE un-adjudicated mechanism family can carry that share

**Owner directive (verbatim, mid-session 2026-08-18, on declining B-2):**
*"I won't sign that but some mechanism has to be able to improve to 40 % miss
for 2023 I refuse to believe it's not possible."*

This memo answers from committed artifacts, read-only (no LP, no solve, no
criterion re-scored; the arithmetic below is the ercot-214/219 probe basis —
demand-weighted P1 settled price vs actual hub RT — computed on the keeper
`ercot215_decontam_B` sidecars and the committed actuals; official-basis
numbers are quoted where recorded). Session ercot-220, branch
`claude/ercot-220-lever-phase0-je3znm`, keeper UNCHANGED
(`2026-08-17-ercot215-arm-decontam`).

## 0. THE ANSWER, IN ONE PARAGRAPH

The owner's instinct is right, and the record itself proves the number is
reachable — ercot-213 hit C3a-2023 **+0.4 %** — the problem was never
arithmetic but that the mechanism carrying it was one the 2023–25 design
cannot emit, and the owner promoted its removal. What the ercot-220
decomposition adds: the remaining miss is NOT one object. The model already
**catches 64 of the 181 tail hours on its own physics** — it prices them at
a demand-weighted **$659 where reality cleared $1,999**. Repricing ONLY
those 64 caught hours to reality's level moves probe C3a-2023 from
**−37.8 % to −13.4 %** — two-thirds of the miss — and needs **no capability
or commitment change at all**, because at those hours the model's own stack
is already tight (that is why they are in its tail). The remaining
**117 missed hours** (worth ~16 pp) are the exhaustion-count half that B-2
declined and every admissible basis was measured unable to supply
(FINDING-ercot220). And the mechanism family for the recoverable two-thirds
is the ONE family the record reserved but never tested: the
**adaptive/backward-looking expectation offer** — explicitly carved out of
DECISION-CARD-ercot218b §2 stage 3 as *"out of scope — it may be proposed
only as its own future card"* — for which this memo now shows fresh
month-grain evidence. Proposing that card (ercot-221 Phase-0) is this
memo's recommendation.

## 1. THE DECOMPOSITION — the miss is two objects, measured

2023, probe basis, keeper sidecars vs actual hub RT (this session's exact
recompute; official C3a-2023 is −40.1 % on the official basis):

| population | hours | model dw | actual dw |
|---|---:|---:|---:|
| actual tail (> $200) | 181 | — | — |
| **caught** (model AND actual > $200) | **64** | **$658.52** | **$1,998.97** |
| **missed** (actual > $200, model below) | **117** | $103.04 | $632.66 |

Counterfactual C3a-2023 (probe basis −37.8 % as carried):

| counterfactual | C3a-2023 |
|---|---:|
| **depth only** — the 64 caught hours priced at actual | **−13.4 %** |
| count only — the 117 missed hours priced at actual | −21.5 % |
| both — entire actual tail priced at actual | +2.9 % |

Reading: the **depth half (~24 pp)** lives at hours where the model's own
dispatch is already scarce — no telemetry, no commitment truth, no B-2
needed; what is missing there is only the *marginal offer level* (reality's
storage priced its SOC at $3–5k; the model's marginal unit clears at
$300–700). The **count half (~16 pp)** is the artificial-shortage
exhaustion population the model cannot see without the online/commitment
object — closed by FINDING-ercot220 unless B-2 is ever signed or the
Option-C crosswalk intake (RESEARCH-ercot218b §5) lands. The −13.4 figure
is an upper bound for any depth lever (the LP may partially substitute
cheaper headroom at repriced hours), but the bound's size is the point:
**most of the 2023 miss is depth, not count.**

## 2. THE EVIDENCE THAT THE DEPTH OBJECT IS AN *ADAPTIVE* EXPECTATION — new month-grain measurements

The three conduct closures (ercot-210/211/218) tested **static** functions
of *same-hour* drivers (tightness, capability, AS state) and killed them on
transfer (T4 0–1/6) and on tie-pairs (T5 71–95 % violating). Their own
post-mortems pointed at a **dynamic** driver ("consistent with
adaptive/lagged expectations", RESEARCH-ercot218b §5) — a state no session
has ever tested. Fresh month-grain checks, committed artifacts only:

1. **September 2023 is priced off August's experience.** Measured
   offer-implied spike probability (offer p50 / $5,000 cap): Sep **0.81**.
   September's own realized spike-day frequency: **0.13**. The trailing
   30-day realized frequency entering September: **0.53**. The trailing
   state fits 4× better than the contemporaneous one — a same-hour-rational
   offer cannot produce September; a backward-looking one does.
2. **June/July 2023 park at the cap under regime uncertainty** (implied
   P = 1.00 against trailing frequencies of 0.00/0.03) — the ECRS design
   was three weeks old; an adaptive agent with no history prices the
   worst case. 2024/2025 offers sit at implied 0.26/0.20 against realized
   0.01–0.07 — a slowly decaying prior, not noise.
3. **The 2023 conduct predates ECRS** — at the tightest pre-go-live hours,
   measured storage offers were already **$2,446 p50** where the
   2024/25-fitted static surface predicts $298
   (`ercot210_conduct_transfer_phase0.json`, reported_not_gating). The
   driver is the 2023 *competitive state* (small, short-duration fleet
   pricing scarce SOC), present all year and amplified — not created — by
   the sequestration summer.

None of this was in the tested cells: Door A's closures condition on
same-hour quantities and are untouched; what they measured — "the mapping
itself moves year-over-year" — is exactly what an adaptive state predicts.

## 3. WHAT A LEGITIMATE MECHANISM LOOKS LIKE (and what keeps it inside the rules)

**`ercot_storage_adaptive_expectation_offer`** (name reserved, NOT built):
in P1 only, through the existing ercot-219 stage-3 seam
(`p1_storage_discharge_cost` — already merged, default-off), storage
discharge is offered at `max(vom, P_hat(t) × VOLL)` where **`P_hat` is a
trailing function of the MODEL'S OWN realized scarcity** — e.g. the
exponentially-decayed frequency of the model's own price-path spike events
over the preceding weeks, seeded by a regime-uncertainty prior at a
published design date. Key properties:

- **Rule 13 clean by construction:** in both backcast and forecast, the
  trailing state is computed from the model's own solution path (a
  P0→P1-style second pass / fixed-point iteration — the model's 64 caught
  hours are the bootstrap events, and the feedback amplifies them), never
  from measured prices or offers. Measured conduct enters only as
  *identification evidence* inside the Phase-0 instrument, exactly as in
  ercot-210/211/218.
- **Forward-computable and self-extinguishing:** in a forecast year the
  state regenerates from the model's own events; as the fleet grows and
  spikes vanish, `P_hat` decays — the 2023-vs-2024/25 split emerges from
  carried inputs (fleet, load, sequestration) with no year key (ercot-217
  stays closed).
- **It carries real DOF** (a decay constant, a prior) — which is exactly
  why the ercot-218b card fenced it out of the zero-DOF build and why it
  needs its own owner card, an ex-ante identification, LOYO across
  2023–2025, and the standing kill-gate table. A residual-tuned decay is
  the forbidden form; the Phase-0's job is to show the constants are
  identifiable from the measured offer surface's own dynamics (the §2
  trail-vs-own contrast, at daily grain on the SCED corpus) before any
  solve.

**What it can and cannot buy, stated ex ante:** its ceiling is the depth
half (≈ −13.4 % probe-basis at perfect execution); it cannot create the 117
missed hours (the count half stays with B-2/Option C/Door D). A successful
arm would also deepen C3c's caught-hour tail without moving its count.

## 4. RECOMMENDATION

Charter **ercot-221 Phase-0** (read-only, its own card): identify the
adaptive rule ex ante on the SCED corpus at daily grain — the trailing
realized-scarcity state vs the measured storage offer surface, LOYO across
2023–2025, with the within-regime 2024→2025 control (the T4 that static
drivers failed 0/6) as the decisive gate, plus a fixed-point feasibility
leg from committed sidecars (does the bootstrap-amplification plausibly
reach reality's level from the model's own 64 events?). Only a Phase-0 PASS
charters a build. The corpus restore route is documented
(FINDING-ercot218 §1); the instrument discipline is inherited verbatim.

## 5. GOVERNANCE

Read-only; no LP, no solve, nothing armed; keeper unchanged. Q-B FINAL /
R-A honoured — the §1 counterfactuals are *attribution arithmetic* on
committed artifacts (the caught/missed split), reported at full magnitude,
never a basis, never fed to anything; no official criterion recomputed.
Door A honoured — nothing fitted here; §2's numbers are read from committed
probe artifacts and the actuals calendar. DO-NOT-REDO honoured (static
conduct functions not re-tested; the aggregate reconciliation untouched;
B-2 remains unsigned per the owner's decision, recorded). Rule 28(b): no
mechanism tested, no cell verdict; the proposal in §3 has no
`ScenarioConfig` field until its card is signed. Rules 22/25/27 fenced as
in the parent session.
