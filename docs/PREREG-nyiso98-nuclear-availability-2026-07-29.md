# PRE-REGISTRATION — nyiso-98 `nuclear_unit_availability` (NYISO derivation)

**Committed BEFORE the NYISO extract is derived and BEFORE any LP runs.**
Matrix §5.5 item 7 (dispatch-matching lane, nyiso-92 charter). Instrument:
`scripts/probes/nyiso98_nuclear_availability_provenance.py` (no LP).

House protocol for this lane: same-HEAD zero-delta control + single-delta arm,
this pre-registration committed before solving, LIVE-mechanism check
(nyiso-89 §4a) before results are read.

---

## 1. Premise correction (measured BEFORE the gate was set, and it re-bases it)

The lever queue states the defect as *"nuclear r_day drops 0.84 → 0.50/0.51 in
2024–25"*. Those numbers are reproduced exactly on the keeper
(`nyiso96_ctamort`, probe `baseline` section: 0.839/0.504/0.511) — **but they
are scored against a contaminated benchmark and the defect they describe does
not exist.**

EIA-930 `NYIS` `NG: NUC` posts **exactly 0.0 MW** in contiguous blocks — a
1,179-hour block in 2023 (50 all-zero days, 2023-03-13 → 2023-04-30 plus
scattered), 380 h in 2024, 117 h in 2025. These are BA reporting gaps written
as zeros in the source parquet (**not** NaN, and not produced by the repo's
`_eia_hourly_frame_filled` gap-bridging, which emits NaN).

**Falsified against NRC, all 81 gap days, all three years:** every gap day has
at least one NY reactor at **100 %** of licensed thermal power (probe
`benchmark`: `unfalsified gap days: 0`). E.g. 2023-04-14…20 — FitzPatrick 100 %
and Nine Mile Point 2 100 % (2,127 MW online) against a metered 0.0 MW for all
24 h. A four-reactor fleet with a unit at power cannot meter zero.

Define a **gap day** = a day posting 0.0 MW in ≥1 hour. Masking them:

| year | r_day as-published (raw) | r_day gap-CLEAN | n clean |
|---|---|---|---|
| 2023 | 0.839 | **0.446** | 309 |
| 2024 | 0.504 | **0.833** | 344 |
| 2025 | 0.511 | **0.534** | 356 |
| 3-yr mean | 0.618 | **0.605** | |

The published ordering **inverts**: 2023's "good" 0.84 is inflated by 50
phantom zero-days that happen to fall in the model's low-CF months (Mar 0.86,
Apr 0.74); 2024's "bad" 0.50 is deflated by its own gap block. The real
per-year skill is **worst in 2023**, good in 2024, mediocre in 2025.

Second artifact, same cause: the nyiso-92 component table's nuclear level
`27.49/24.00 TWh` (2023) reads as a +14.5 % model over-production. On
gap-clean days the model is **−2.1 %** (27.49 vs a 28.08 TWh gap-clean-rate
annualization). There is no nuclear level defect.

**Consequence for this session:** the item is NOT closed by the correction —
a genuine daily-timing deficit remains on clean days (0.446 / 0.534 in
2023/2025) and a per-reactor refuel overlay is exactly the mechanism for it.
But the target is **re-based onto gap-clean r_day**, and every gate below is
stated on the clean statistic. Scoring an arm against known-phantom zeros
would be scoring against noise.

## 2. Source adjudication (rule 13, done before the derive)

| candidate | verdict |
|---|---|
| NYISO unit outage schedules | **unavailable** — CEII; no public unit-level equivalent (same wall as PJM's masked `unit_code`) |
| EIA-923 monthly | **already the level anchor**; monthly grain cannot see intra-month timing |
| CAMPD | **n/a** — nuclear does not report to CEMS |
| EIA-930 `NG: NUC` hourly | **rule-13 FORBIDDEN as an input** — it is the scored outcome, and it is the contaminated series audited above |
| **NRC daily Power Reactor Status** | **SELECTED** — public, per reactor, daily, **365/366 days for all four NY reactors in all three years** (probe `census`) |

Admissibility: percent of licensed thermal power at the morning report is a
**physical availability event**, the same rule-13 class as the CAMPD fossil
outage windows and ERCOT's live keeper overlay
(`ercot_nuclear_unit_availability`). Forward analogue: refuel cadence →
`NUCLEAR_MONTHLY_CF` / refuel-block scheduling. Zero fitted scalars —
`EVENT_RAW_MAX` 0.90 / cap 1.0 / `SCALE_CLIP` 1.25 / `WEDGE_TOL` 0.01 are
inherited **frozen** from the ERCOT deriver (rule 23: re-derives only when a
new NRC year lands).

**Stated tension, not hidden:** nuclear is a flat must-run price-taker, so an
availability overlay on it is close to an output overlay. The line that keeps
it admissible is that the **level** is owned by the independent EIA-923 anchor
(`NUCLEAR_MONTHLY_CF_BY_YEAR`), never by the scored EIA-930 series — NRC
supplies **timing only**. That is also why the reconciliation stays even though
it costs signal (G2 below).

## 3. The PJM precedent this gate is shaped by

pjm-nuc-1b (`docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md` §8.2.1) built this
same overlay in full and **stopped at its build-time provenance gate**: the
923-anchor reconciliation redistributes event-day energy onto near-full pool
days, and PJM's target (scarcity tail hours) *is* near-full pool days, so net
recovery came out **−72 MW** against a ≥ +75 MW pre-commitment. The mechanism
was self-defeating **for that target**.

NYISO's target is different in kind — **daily timing across the whole year**,
not a level at 22 tail hours — and the anchor is by construction neutral to
within-month shape. That is a reason to test, **not** a reason to assume.
Gate **G2** is written to detect exactly the PJM failure mode.

## 4. Build-time gates (measured in extract arithmetic, no LP)

Baseline = the smear's gap-clean r_day: **0.446 / 0.833 / 0.534, mean 0.605**.

* **G1 — the source carries timing content.** RAW NRC (`avail_raw`, no
  reconciliation) must lift 3-yr mean gap-clean r_day by **≥ +0.10** and must
  not regress below the smear in any year. *Threshold derivation:* +0.10 is
  ~¼ of the remaining distance to 1.0 from 0.605 and is the order of the
  hydro-envelope arm's demonstrated per-class r gains (nyiso-92: CC_REGULAR
  0.705 → 0.770). Below it the source does not reach the defect → **stop, no
  derive committed, no solve**.
* **G2 — the reconciliation survives (the PJM failure mode).** RECONCILED
  (`avail`) must retain **≥ 70 %** of G1's measured raw lift in the 3-yr mean,
  **and** be **> 0 in every year**. *Threshold derivation:* event days keep raw
  values by construction, so only the pool scale can erode signal; PJM's
  retention was negative. Requiring most-but-not-all preserved is the direct
  test. Fail → **stop before solving**, disclose, matrix cell **R** on the
  build-time citation.
* **G3 — level neutrality.** Max |annual ΔTWh vs the smear| **< 0.5 %**, and
  every kept month reconciles to the anchor within `WEDGE_TOL`. This is a
  TIMING mechanism; a level move means it is doing something else.

## 5. Solve gates (only if G1–G3 hold)

Same-HEAD zero-delta control + single-delta arm, `--year 2023 2024 2025` in one
invocation (rule 16), sequential within it (rule 12).

* **S1 — no currently-PASS criterion flips in any year.** C1 **14/14 free
  10/10** (watch: 2023 `CC_REGULAR` sits at **−2.76 of ±2.94**, 0.18 TWh
  margin — a walk out of band is a REPORTED regression, never silent), C2,
  C3a, C3b, C4, C6, C7, C8. C8 2024 `ST_GAS` is grounded-above-budget at
  **30.4 %** and is fragile.
* **S2 — the mechanism's own target.** In-solve nuclear gap-clean r_day
  improves in **every** year.
* **S3 — C3c is NOT the target and NOT a gate.** It is a diagnosed, unclosed
  structural limitation with an empty lever queue (nyiso-94/95/96/97) and is
  roof-blocked (nyiso-85 §7d). Reported either way; movement in either
  direction adjudicates nothing.

**Outcomes.** G1–G3 + S1 + S2 → register both runs, recommend keeper.
S2 holds and S1 regresses → register both, report the regression on the
record, adjudicate on rule 1 [R-STRUCT] (an accurate measured input is not
reverted because a residual moved — rule 14). Anything else → register both
runs anyway (rule 15) and adjudicate **R**. No constant is revisited after
results (rules 1/5/23/26).
