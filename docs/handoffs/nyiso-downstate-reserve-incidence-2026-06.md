# Handoff — NYISO downstate-reserve incidence frontier (analysis pass)

> **Status (2026-06-25): ANALYSIS COMPLETE. The task's hypothesised primary
> levers (import discipline / downstate interface tightening) are EMPIRICALLY
> REFUTED. The real lever is unit commitment (a binding synchronised-reserve
> requirement), which the current pure-ED LP cannot express. No keeper was
> registered — the grounded fix is out of the reserve-incidence/import-discipline
> scope this task assumed.**

This is the analysis-pass deliverable for the NYISO CT_PEAKER under-run + >$300
scarcity-tail miss. It mirrors `docs/handoffs/pjm-cc-level-tuning-2026-06.md`:
read the code + one diagnostic solve, then a ranked recommendation of the single
change to test first. It does **not** register a dashboard keeper (rule #1: an
analysis probe is never a keeper).

## The miss (recap, from the live keeper `nyiso 27 cc-offer`)

Re-scored `results/calibration/nyiso_27_cc-offer`
(`scripts/calibration_verdict.py`): determination **NOT-YET**. The two ledgered
exceptions this task targets:

- **C1 CT_PEAKER under-run** — 2023 −1.30 TWh (−0.8 pp), 2024 −1.51 TWh (−0.9 pp).
- **C3c >$300 scarcity hours** — 2023 model 1 vs actual 10; 2024 model 0 vs
  actual 12; 2025 model 8 vs actual 42.

Both are ledgered "incidence-gated by the model's too-loose downstate reserve
headroom." The live keeper already runs the in-LP **locational** energy+reserve
co-opt (`--energy-reserve-coopt`, 7 nested families NYCA ⊃ East ⊃ SENY ⊃ NYC,
2 reserve classes) **and** the priced import node + reconciliation
(`--priced-interchange --nyiso-import-reconciliation`). So the in-LP reserve
binding the task asks for **already exists** — the question is purely **why it
never binds**.

> Note: `main` now carries the run-28 NYISO-native CAMPD offer curve
> (`6826bfd`, the offer-curve handoff #1), but it did **not** register a bundle
> or move `keepers.json` — the live NYISO keeper is still
> `2026-06-25-nyiso-27-cc-offer`. Run 28 left CT_PEAKER untouched
> ("incidence-gated, out of scope") — i.e. this frontier. All diagnostics below
> are on current `main` code.

## Method

- Fleet-only capacity census (no solve): `run_year(..., fleet_only=True)` under
  the keeper flags, per-zone reserve-eligible capacity vs each family's
  requirement.
- One diagnostic single-year solve (2024, keeper flags, co-opt ON) to
  `scratchpad/nyiso_baseline_2024` (gone when the container is reclaimed —
  re-derive from this doc). Measured per-zone reserve incidence from
  `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`; measured net
  interchange from `eia_loader.nyiso_net_interchange`.

## Finding 1 — the requirement is never capacity-infeasible

Reserve-eligible capacity (pmax × availability) at the **minimum-availability
hour** of 2024 vastly exceeds every family requirement:

| family | class | req (MW) | min-hour eligible (MW) | min/req |
|---|---|---|---|---|
| NYCA 30-min | full | 2,620 | 15,779 | 6.0× |
| East 30-min | full | 1,200 | 10,668 | 8.9× |
| SENY 30-min | full | 1,100 | 7,514 | 6.8× |
| NYC 30-min | full | 1,000 | 4,837 | 4.8× |
| NYC 10-min | quick-start | 500 | 1,639 | 3.3× |

So a shortage can only arise from **energy dispatch consuming the headroom**, not
from a capacity deficit. The families bind only if in-pocket dispatch eats nearly
all eligible capacity.

## Finding 2 — in the solve, the downstate reserve essentially never binds

2024 solved bundle (co-opt ON):

- `reserve_price` (stacked family dual) **> $0 in 9 hours**, mean **$0.03/MWh**,
  max $97. Measured NYC reserve adder is **> $0 in 3,082 hours**, mean
  $7.64/MWh, max $2,180 (and 2025 measured: >$0 in 4,007 h, mean $28.73).
- Model system demand-wt LMP **mean $25.7, 0 hours > $300** (actual mean $36.0,
  **12 hours > $300**, max $997). NYC zonal LMP mean $26.6, max $157.
- Per-family solved reserve headroom: NYC 30-min median **3,411 MW** (req 1,000),
  < req in only 7 h; NYC 10-min median **1,630 MW** (req 500), < req in 48 h but
  prices barely move; SENY/East never < req.

In the **12 actual >$300 hours**, the model's NYC reserve headroom sits at
**2,031 MW (30-min) / 1,463 MW (10-min)** — 2–3× the requirements — and the
model prices those hours at **~$37**. The model has ~5× the downstate reserve
slack reality shows, in the exact hours reality is scarce.

## Finding 3 — the excess headroom is idle peakers, held for purely ECONOMIC reasons

Top-100 NYC-demand hours, 2024:

- NYC demand 9,624 MW; NYC in-zone generation 6,057 MW; net inflow 3,567 MW.
- NYC quick-start (peaker) generation **554 MW of ~1,639 MW available** — peakers
  run only ~34 % even at peak; ~1,085 MW sits idle as reserve headroom.

The peakers are idle because cheap CC + cheap wheeled-down upstate energy serve
NYC's energy below the peakers' marginal cost, and **nothing forces them online.**
This is the CT_PEAKER under-run and the missing tail in one picture: idle peakers
= phantom reserve = no scarcity price = NYC LMP stays ~$27 = peakers stay idle.

## Finding 4 — REFUTATION: the downstate interfaces do NOT bind

The task hypothesised that priced imports / loose downstate interfaces over-serve
the pocket and relax reserve. **The solve refutes this.** Net inflow vs the
physical interface ceiling, 2024:

| zone | inflow ceiling (MW) | mean | p95 | max | hrs > 90 % ceiling |
|---|---|---|---|---|---|
| NYC (Dunwoodie-South 3,900 + cables 1,000) | ~4,900 | 2,600 | 3,657 | 4,534 | **7** |
| Long_Island (NYC-LI 1,650 + cables 1,200) | ~2,850 | 1,188 | 1,887 | 2,480 | 0 |
| Lower_Hudson (UPNY-SENY 5,150) | ~5,150 | 928 | 1,357 | 1,916 | 0 |
| Capital_Hudson (Central-East 2,850) | ~2,850 | −493 | 466 | 1,697 | 0 |

NYC pulls only 2,600 MW mean inflow with 4,900 MW available; the interface is
within 90 % of its ceiling in **7 hours of the year**. The other downstate
interfaces never approach their ceilings (Capital_Hudson is a net *exporter* on
average). **Tightening any downstate interface to a grounded value cannot pull
peakers or tighten reserve — the LP is already choosing inflow well below the
limits for economic reasons.** To bite, an interface cap would have to drop
*below* the model's economic usage (NYC ~2,600 MW), far under the grounded
~3,900 MW Dunwoodie-South normal rating — i.e. an ungrounded knob (rule #12,
forbidden).

Corollary on the import node: measured NYISO net import is nearly **flat across
the day** (night 2,272 → peak 2,407 MW, +6 %), and the priced node's downstate
external delivery is already link-capped (NYC cable 1,000, LI cable 1,200). The
dominant NYC inflow is *internal* Dunwoodie wheeling, which (Finding 4) does not
bind. So an hourly import shape (`inject_interchange_shape`) would move very
little. The import-discipline lever is **spent** — it is not the constraint.

## Finding 5 — the structure is otherwise correct

The in-LP reserve formulation is deliverability-correct where it can be:
shared-headroom is **per-zone** (`dispatch.py:_build_reserve_rows`,
`R[c,z] ≤ zone z's own eligible headroom`), and each family sums only its member
zones' reserve. Out-of-pocket upstate thermal therefore **cannot** satisfy
East/SENY/NYC — the task's lever #3 ("non-deliverable MW must not count") is
**already honoured** at the zone-family level. The eligibility classes
(quick-start = gas_ct/oil for 10-min; full = +gas_cc/gas_st for 30-min) are
grounded in response speed.

The **one** structural gap: a unit provides reserve with **no online/commitment
requirement** — an offline peaker contributes its full pmax to headroom
(`R ≤ cap − P`, and `P = 0 ⇒ R = cap`). In reality 10-minute **spinning**
(synchronised) reserve must come from **online** units (generating ≥ pmin), and
even 30-minute reserve from slow CC/steam needs the unit committed. Because the
pure-ED LP has no online state, idle capacity is credited as deliverable
reserve, which is exactly why the families never bind.

## Root cause (one sentence)

The downstate reserve never binds because the pure-economic-dispatch LP **credits
idle (un-committed) peaker and slow-CC capacity as deliverable operating
reserve** — so the abundant idle headroom satisfies every family, the RCPF never
prices, NYC LMP never separates upward, and the peakers stay economically idle;
the interfaces and import node (the task's hypothesised levers) are **not** the
binding constraint.

## Ranked recommendation — single change to test first

1. **PRIMARY (the real fix): a commitment-aware, synchronised downstate reserve.**
   The faithful mechanism is a **spinning (synchronised) reserve sub-requirement
   that only ONLINE units satisfy** — forcing the NYC/SENY peaker fleet to
   *commit* (P ≥ pmin) to provide it, which (a) generates pmin energy
   (**CT_PEAKER ↑**) and (b) consumes genuine online headroom so the reserve
   family **binds → RCPF tail fires endogenously** and NYC LMP separates upward
   (**C3c ↑, C3a ↑ toward band**). This requires unit commitment — the P2 screen
   (`model/commitment.py`, `commitment_enabled`, currently OFF) extended so the
   downstate spinning-reserve family is satisfiable only by committed units, in a
   **zonal/family** formulation (per-gen reserve+commitment columns OOM at fleet
   scale; cap concurrency, rule #14). Grounded: NYISO Ancillary Services manual
   (10-min spin = synchronised; `process_nyiso_as.py`). Cost/risk: memory- and
   compute-heavy; the largest change of the three; needs its own calibration of
   the spinning fraction (use the measured spin requirement, not a fitted value).
   **This is the single change to test first** — it is the only lever that
   attacks the confirmed root cause.

2. **SECONDARY (tractable approximation): a dispatch-linked online-headroom cap on
   slow-unit reserve.** Without full commitment, cap the slow (gas_cc/gas_st)
   contribution to the 30-min / spinning families at an *online-proxy* headroom
   (a function of the unit's own dispatch), leaving quick-start to supply from
   full availability (correct — they synchronise ≤ 10 min). LP-linear,
   per-zone, memory-light. Risk: the no-commitment online proxy is approximate
   and easy to slip into a tuned knob — must be anchored to a physical ramp
   definition, not the residual. Likely **insufficient alone** (quick-start idle
   peakers still cover the small NYC requirement), so it reinforces #1 rather
   than replacing it.

3. **REFUTED — import discipline / downstate interface tightening** (the task's
   hypothesised primary lever). Finding 4: the interfaces bind ≤ 7 h/yr; NYC
   inflow is an economic choice 1–2 GW below its ceiling. No grounded tightening
   bites. Do not pursue.

4. **REFUTED — RCPF demand-curve steepening** (already proven by the nyiso-25
   `rcpf-steep` probe: zero added tail hours, C3a overshoot). Do not pursue.

### Predicted signs (for #1, the recommended first test)

| metric | direction | why |
|---|---|---|
| CT_PEAKER energy | **↑** (toward 0) | committed peakers generate pmin + clear on the lifted LMP |
| C3c >$300 tail | **↑** (toward actual) | binding spinning family prices the RCPF endogenously |
| C3a mean LMP | **↑** | reserve dual stacks into the downstate LMP (watch the +8 % guardrail) |
| CC over-run (C1) | ~flat to slightly ↓ | peakers displace marginal CC in tight hours |
| memory | **↑↑** | commitment + reserve columns; zonal/family formulation, concurrency-capped |

## Blockers for the implementation pass

- **Commitment is the real lever and it is a large change.** It is *outside* the
  reserve-incidence / import-discipline scope this task assumed. The
  implementation pass should be re-scoped around a zonal/family commitment +
  synchronised-reserve formulation (the same conclusion the PJM reserve note
  reached: post-solve overlays and pure-ED reserve co-opt cannot hold synchronised
  headroom).
- **Measured downstate interface data is absent in this container.** Even though
  interface tightening is refuted as the lever, note for completeness that
  `data/raw/NYISO/ATC_TTC.zip` (the `derive_nyiso_central_east_ttc.py` source for
  UPNY-SENY / Dunwoodie-South measured TTC) is **not present** — so no measured
  downstate-interface work is possible here regardless.

## Guardrails carried forward

- Any change is NYISO-only behind a default-off flag; ERCOT/PJM/CAISO/MISO/SPP/
  NEISO must stay byte-identical.
- The CT_PEAKER energy and >$300 tail must emerge **endogenously** from a binding,
  grounded reserve requirement — never a CEMS pin, a tail price-adder, or a
  steepened curve (rule #12).
- 2024/25 gas-TOTAL deficit + downstream CO2 stay the EIA-930/EIA-923 basis floor
  (`docs/nyiso-td-loss-resolution-2026-06.md`); td_loss_factor = 0.
