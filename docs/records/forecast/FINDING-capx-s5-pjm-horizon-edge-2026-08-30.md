# FINDING — capx S-5: PJM requirement horizon-edge — hold-last-FPR implemented, D-1 checker repaired, T1-F leg re-scored

**Session:** capx S-5 PJM REQUIREMENT HORIZON-EDGE (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-30 · **Branch:** `claude/capx-s5-pjm-horizon-edge-pksr0z` (off `main` @ `65a39e378555`)
**Charter:** owner signature **card C-A, 2026-08-25**
(`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §3.3/§5.1; director ledger
`capx-director-ledger-2026-08.md`, lane S-5). The convention was DECIDED there; this session
implements it. Evidence base: `docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md` §5.
**No LP was solved, no year was scored against actuals, nothing was registered on either
dashboard namespace.** This is the chartered scorer/governance round: it restates an FC-1
verdict reading, and this FINDING — not a board edit — is the director's D7-class input.

---

## 0. Headline

1. **HOLD-LAST-FPR is implemented as the declared, greppable convention** in
   `resolve_forecast_pool_requirement`
   (`src/market_sim/model/capacity_evolution/retirements.py`): a delivery year strictly
   beyond the ISO's last published Forecast Pool Requirement now returns that last
   published value instead of falling onto the stale `(1 + PRM) × icap_to_ucap_ratio`
   composite. The code cites the card C-A signature and the
   `resolve_demand_curve_vintage` / `forward_net_cone_anchor` forward-carry precedent
   ("year after the latest vintage HOLDS-LAST to it") in place. Pre-table years and
   in-table gaps still return `None` — the convention extends the table's FORWARD edge
   only, so every backcast year is byte-identical (§5).
2. **The D-1 checker repair is bundled, as chartered:** `scripts/check_forecast_invariants.py`
   I7 and I12 now thread the ledger `year` into `resolve_adequacy_requirement_mw`. The
   year-less calls graded PJM 2026–2028 against the LOWER fallback composite while the
   model built to the published FPR (both D2 findings; card §3.2). Checker and model now
   grade the same bar in every year.
3. **The restated PJM T1-F position, at full magnitude (§3): the 2030 I7 miss restates
   from 366 MW to 5,858 MW** (3.39 % of peak) — the ~5.9 GW the card adopted with the
   signature — **and the 2029 bar rises 3.18 % of peak, so 2029 plausibly joins as a
   failing year** (inference, flagged: its supply side is committed nowhere; S-6
   measures it). The 2026–2028 checker bars rise 0.96/1.83/3.18 pp of peak onto the bars
   the model already built to. **This is a worse reported result, produced on purpose:**
   the 366 MW was an artifact of grading the horizon edge against the weakest available
   construction, and every correction available on either side runs against leniency.
4. **Rule 23 `[R-FROZEN-DERIVE]` intake check, on publication terms:** PJM's 2029/30
   planning parameters are **NOT yet published** as of 2026-08-30 — the latest published
   set remains 2028/29 (endorsed 2026-02-19 MRC, already intaken by FFR-2C), and the
   2029/30 BRA is scheduled for **December 2026**. Hold-last therefore stands, and the
   registry now carries an explicit intake pointer at the table edge: add the 2029/2030
   row on publication and the hold supersedes itself for that year automatically.
5. **S-6 is UNBLOCKED** (§7). The PJM T1-F ledger run now measures against the corrected
   bar, which is the entire point of running it strictly after this session.

---

## 1. The convention, as implemented

`resolve_forecast_pool_requirement(iso, year)` resolution order (all behavior changes are
in step 3; steps 1–2 and 4 are byte-identical to the pre-C-A resolver):

1. Exact delivery-year match in `FORECAST_POOL_REQUIREMENT_BY_ISO` → the published FPR
   (unchanged).
2. `year=None`, no table for the ISO → `None` → fallback composite (unchanged).
3. **Delivery year strictly AFTER the table's last entry → the last entry's FPR
   (HOLD-LAST-FPR, card C-A).** For PJM: calendar 2029+ (delivery 2029/30+) → 0.9401,
   the published 2028/29 value.
4. Delivery year BEFORE the first entry, or an in-table gap → `None` → fallback
   (unchanged — pre-CIFP years keep the composite deliberately, and a mid-table hole is
   a data problem hold-last must not paper over).

The citation block in the code names: the card C-A signature (owner, 2026-08-25), the
`resolve_demand_curve_vintage`/`forward_net_cone_anchor` precedent, the D2b §5.2
measurement of the discontinuity (3.18 % of peak, 5,492 MW at the 2030 peak), and the
rule-23 supersession discipline. The convention is registered where the construction
lives — no `ScenarioConfig` field, because there is **no free parameter**: the held value
is the table's own last published entry (zero DOF; rule 24 satisfied by construction).

Documented in the same round: the `FORECAST_POOL_REQUIREMENT_BY_ISO` registry comment,
the in-table 2029/30 intake pointer, `resolve_adequacy_requirement_mw`'s construction-1
docstring, and `model-methodology-spec.md` (three sites: §5 floor, the FPR devintaging
paragraph, the CR-1 position paragraph).

Tests (`tests/unit/model/test_capacity.py::TestForecastPoolRequirement`): hold-last at
2029/2030/2050 = 0.9401; requirement at 2030 = `peak × (1 − DR) × 0.9401` and strictly
above the composite it replaces; pre-table 2024 still falls back; an in-table gap is
never bridged; `year=None` byte-identity. Two `TestReserveMarginBuild` mocks that
simulate "an ISO absent from every adequacy registry" at year=2030 now also clear the
FPR registry — at 2030 that registry was previously silent (beyond-table `None`) and
hold-last makes it live, so the incomplete mock no longer matches those tests' own
stated premise.

## 2. The D-1 checker repair

`scripts/check_forecast_invariants.py`:

* `check_i7_reliability_floor` — `resolve_adequacy_requirement_mw(run.config, run.iso,
  peak, year)` (was year-less). The capacity-market absolute floor now grades the
  published FPR of the ledger year's delivery year (2026–2028) or the held-last FPR
  (2029+), exactly the bar the model's floor/backstop build to (year threading verified
  at all three model call sites: `evolve.py:811` backstop, `retirements.py:1300–1302`
  floor, `runner.py:1676→adequacy.py:379` CR-1 position — D-1 was checker-only, as the
  card states).
* `check_i12_reserve_margin` — same threading for the requirement-implied floor; the
  floor now MOVES across the horizon where the FPR series does, and the summary line
  prints the first year's band plus the last when they differ (out-years always printed
  their own band; unchanged).
* The energy-only (ERCOT) branches of both checks are untouched.

Pre-repair scope, restated from the card: **live for 2026–2028** (model built to the FPR,
checker graded the composite — a 0.96–3.18 pp-of-peak under-grade), **inert for the 2030
leg** (no published 2030/31 FPR — both sides used the fallback). Post-repair, with
hold-last, 2029–2030 are FPR-graded on both sides too.

Regression tests (`tests/regression/test_forecast_invariants.py`): a PJM 2026 ledger at
rm −12.2 % (firm 4,390 MW at peak 5,000) sits above the stale fallback bar (4,355 MW —
the D-1 defect PASSed it) and below the published 2026/27 bar (4,403 MW) → FAIL; a PJM
2030 ledger at rm −11 % (4,450 MW) sits above the composite and below the held-last bar
(4,514 MW) → FAIL; I12 floors thread the year (2026 vs 2030 bands differ and both are
excursions at rm −12.5 %, which the year-less floor −12.90 % graded in-band). All 47
checker tests pass; the pre-existing I7/I12 tests pass unchanged (their fixtures clear
both the old and new bars in the same direction).

## 3. The re-scored PJM T1-F leg, per year — before/after side by side

**Baseline (unmoved by this session):** board verdict `pjm-t1f`
(`frontend/data/forecast/ff-verdicts.json`; FFR-3A-2, `scored_at_sha 8ba592814d92`,
epoch 2026-08-03): determination **HOLD**, FC-1 **FAIL** on `I7: 2030: accredited firm
150088 < requirement 150454 MW`, FC-2 CAVEAT with I12 `out: 2030:-13.1% (band [-12.9%,
2.1%])`, backstop share 23.6 %.

**Observability limit, stated per the D2b discipline:** PJM's T1-F supply side is the one
leg no committed artifact can reproduce (D2b §5.1 — the FFR-3A-2 bundle is gitignored by
design; the only committed PJM evolution ledgers are hindcast 2021–2025). The committed
record carries exactly one (firm, requirement) pair: 2030. Everything below therefore
restates the REQUIREMENT bar for every year from constants via the live machinery, and
the VERDICT for the one year whose supply side is committed. `peak₂₀₃₀ = 150,454 /
0.871017 = 172,733.8` is back-solved from the verdict's own numbers (D2b §5.2 method;
the verdict rounds to the MW, so ±0.6 MW).

| year | delivery yr | req factor **before** (year-less composite) | req factor **after** (D-1 repair + hold-last) | bar change (pp of gross peak) | I7 **before** | I7 **after** (restated) | I12 floor **before** | I12 floor **after** |
|---|---|---:|---:|---:|---|---|---:|---:|
| 2026 | 2026/27 | 0.871017 | **0.880629** (published 0.9170) | +0.96 | PASS (silent) | bar +0.96 pp; supply **unobservable → S-6** | −12.90 % | **−11.94 %** |
| 2027 | 2027/28 | 0.871017 | **0.889272** (published 0.9260) | +1.83 | PASS (silent) | bar +1.83 pp; supply **unobservable → S-6** | −12.90 % | **−11.07 %** |
| 2028 | 2028/29 | 0.871017 | **0.902813** (published 0.9401) | +3.18 | PASS (silent) | bar +3.18 pp; supply **unobservable → S-6** | −12.90 % | **−9.72 %** |
| 2029 | 2029/30 | 0.871017 | **0.902813** (held-last 0.9401) | +3.18 | PASS (silent) | **plausibly FAIL** — inference, flagged (below) | −12.90 % | **−9.72 %** |
| 2030 | 2030/31 | 0.871017 | **0.902813** (held-last 0.9401) | +3.18 | **FAIL, miss 366 MW** | **FAIL, miss 5,858 MW** (3.39 % of peak) | −12.90 % | **−9.72 %** |

The 2030 restatement, reproduced exactly through `resolve_adequacy_requirement_mw` at
HEAD+this change (factors above are the function's own output at peak 1.0):

```
peak₂₀₃₀            = 150,454 / 0.871017          = 172,733.8 MW
requirement (after)  = 172,733.8 × 0.902813        = 155,946.2 MW   (D2b §5.2 predicted ~155,946)
I7 miss  (before)    = 150,454 − 150,088           =     366   MW
I7 miss  (after)     = 155,946.2 − 150,088         =   5,858   MW   (card C-A: "~5.9 GW") ✓
bar step at the edge = (0.902813 − 0.871017) × peak = 5,492 MW at the 2030 peak (D2b §5.2) ✓
I12 2030             = rm −13.11 % vs floor −12.90 % (breach 0.21 pp)
                     →           vs floor  −9.72 % (breach 3.39 pp)
```

**On 2029 "plausibly FAIL" — the inference and its basis, flagged as such (D2b
discipline):** the standing run's backstop was rate-limited and targeted the OLD bar
(0.871 × peak) in 2029–2030, and its 2030 landed 3.39 % of peak short of the corrected
bar. For restated 2029 to PASS, the 2029 fleet must exceed its own build target by
≥3.18 % of peak. That is not observable from any committed artifact and is not asserted
here — it is exactly the question S-6's ledger answers.

**The verdict restatement, said plainly (before/after):**

* **Before:** `pjm-t1f` FC-1 FAIL — "I7: 2030: accredited firm 150088 < requirement
  150454 MW" (miss **366 MW**, one failing year); FC-2 I12 single excursion −0.2 pp;
  determination HOLD.
* **After (this round):** FC-1 FAIL **stands and deepens** — the 2030 miss is **5,858
  MW**, 16× the reported number; **2029 is plausibly a second failing year** (S-6
  measures); the 2026–2028 rows revert from "graded PASS against the wrong bar" to
  "ungraded pending S-6". FC-2's I12 2030 excursion deepens −0.2 pp → −3.4 pp (still a
  single recorded excursion — WARN-class — until 2029's margin is measured; three
  consecutive excursions would make it FAIL). Determination remains **HOLD**; what
  changes is the magnitude the gate board must quote. **Any reading of PJM's I7 gap as
  "366 MW" is dead.**

Supply-side leniency, unchanged here and left to S-6 with its direction on the record:
the external-tie entry 1,281.7 MW is the 2026/27 BRA cleared UCAP held static; PJM's
published 2027/28 figure is 1,005.9 MW (−275.8 MW) — that correction would WIDEN the
miss further (D2b §5.2/§6; charter).

**What this FINDING does NOT touch:** `frontend/data/forecast/ff-verdicts.json` and
`program-status.json` are unedited. The standing `pjm-t1f` entry is the FFR-3A-2
scorer's output on its (unrecoverable, gitignored-by-design) bundle, and
`scripts/rescore_forecast_verdicts.py`'s discipline holds: nothing hand-edits a
determination — only the scorer's own output on committed artifacts is ever written.
The board refresh that carries this restatement is the director's D7-class work with
this FINDING as its input (charter), and the corrected machinery re-scores the leg
mechanically when S-6's run registers.

## 4. Cross-ISO scope of the change

* **The convention is implemented ISO-agnostically in the one shared resolver, but its
  behavior change is live for PJM alone today:** `FORECAST_POOL_REQUIREMENT_BY_ISO`
  contains only PJM. Every other ISO has no FPR table, so the resolver returns `None` in
  every year and both halves of this round — hold-last AND the checker year-threading —
  are byte-identical no-ops for them (their composite inputs — PRM, ICAP/UCAP ratio, DR
  netting — are all year-invariant registries).
* **The horizon-edge discontinuity was PJM-specific for the same reason:** only PJM had a
  published series to fall off. Every PJM T1-F leg that reaches 2029 crossed it
  (2026–2030 is the T1-F horizon, so every PJM T1-F leg did); no other ISO's leg had an
  edge to cross, and no other ISO's I7/I12 bar moves in this round.
* **Any future ISO that gains a published-FPR (or equivalent UCAP-basis requirement)
  table inherits the declared convention and the correctly-threaded checker
  automatically** — no further code change, which is why the convention was implemented
  in the resolver rather than as a PJM special case.
* ERCOT's energy-only I7/I12 branches are untouched.

## 5. Backcast-path isolation — reproduced for this change, not assumed

The NYISO extcap finding §6 argument, re-derived against this diff (charter requirement):

1. **Consumer chain:** `resolve_forecast_pool_requirement`'s only in-model consumer is
   `resolve_adequacy_requirement_mw` (`retirements.py:1081`); its model-side callers are
   exactly three, all on the capacity-evolution side: the CR-1 reserve position
   (`runner.py:1676` → `adequacy.py:379`, additionally gated on
   `resolve_capacity_market_clearing` AND a non-base year — `fleet is not None and
   prior_results is not None`), the step-6 adequacy backstop (`evolve.py:811` →
   `adequacy.py:479`), and the step-3 retirement reliability floor
   (`retirements.py:1300`).
2. **The calibration backcast never enters that side:** `run_calibration_full.py`'s year
   loop builds a pristine per-year `backcast_config(year, iso, hours, gas_price)`
   (`mode="backcast"`) — every year its own base year — and solves through `run_year`
   (`scripts/run_calibration.py` → the `market_sim.pipeline` per-year solve core).
   Grep over `scripts/run_calibration.py` + `src/market_sim/pipeline/` finds **zero**
   references to `evolve_fleet` / `capacity_reserve_position` /
   `resolve_adequacy_requirement_mw` (one docstring mention in `pipeline/prior.py`).
   `evolve_fleet` is invoked from exactly one site, `runner.py:1736`, on non-base years
   of a multi-year scenario.
3. **Second, independent leg — value-identity even under hypothetical reach:** the
   change alters return values only for delivery years strictly beyond 2028/29
   (calendar ≥ 2029 for PJM). The calibration years resolve to 2023/24 and 2024/25
   (pre-table → `None`, unchanged) and 2025/26 (exact hit → 0.9380, unchanged);
   `scripts/validate_capacity_prices.py` threads calibration years ≤ 2025 →
   byte-identical.
4. `scripts/probes/_ffr3n_i12_attribution.py` still calls the resolver year-less; it is
   a frozen per-run probe record (calibration record, `scripts/probes/` charter) and is
   noted here rather than retro-edited; year-less behavior is itself unchanged.

No backcast keeper shard, `status/*.js`, `calibration-complete.json`, offer curve or
commitment bridge was touched; the backcast registry was not written to (rule 15's
forecast/backcast split — and nothing was registered on the forecast namespace either,
since no run was produced).

## 6. Governance

* **Scorer/governance round, as chartered — it changes an FC-1 verdict reading** (§3,
  before/after side by side). Board update: director's D7-class work; input: this
  FINDING. No quiet absorption into a board refresh.
* **Rule 28 `[R-MECH-MATRIX]`:** no mechanism proposed or tested, no cell verdict
  minted, no `ScenarioConfig` field added, **no shard edited** — a declared requirement
  convention is scoring machinery, and a zero-DOF registry construction is an input,
  not a mechanism (the NYISO extcap §6 precedent). PJM lever queue read (duty a); this
  session takes no lever from it — it is not a mechanism session.
  `scripts/check_mechanism_matrix.py` passes at this diff.
* **Rule 22 `[R-HOLDOUT]`:** no solve, no scoring against actuals, no registration, any
  tier, any ISO. The restatement grades committed model artifacts against a
  constants-derived bar; no measured out-of-training actual was touched. The holdout
  spend freeze is not implicated.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the 2029/30 parameter check was made against
  PUBLICATION, not a residual: PJM's published series still ends at 2028/29 (2026-02-19
  MRC endorsement, the FFR-2C intake); the 2029/30 BRA is scheduled December 2026. The
  registry carries the intake pointer; on publication the new row supersedes the hold
  for that year with no code change.
* **Rules 5/24:** no magic number and no off-registry tunable — the held value IS the
  registry's last published entry (zero new DOF); the convention is cited in place.
* **Rule 13 `[R-MEASURED]`:** unchanged posture — the FPR is a published market-design
  input with a forward story (regenerates on each PJM publication; responds to PJM's own
  planning process), never an outcome fed back.
* **Rule 27 `[R-PUSH]`:** Fable session; all ≥300-line files edited locally via the Edit
  tool and pushed as exact on-disk bytes over `git push`, blob-verified post-push (line
  count + sha256).
* **Tests:** 289 passed across the three touched suites
  (`test_capacity.py` 240, `test_forecast_invariants.py` 47+1 skip,
  `test_capacity_evolution_facade.py`), plus 703 in the adjacent demand-curve/ELCC/config
  suites. The five `tests/scoring` failures at this HEAD
  (`test_ff_readiness_battery` ×4 hydration-dependent, `test_forecast_parity` keeper
  resolve) **pre-exist on clean `origin/main` in this container** (verified by stash) —
  environment-dependent, none introduced here.

## 7. S-6 is UNBLOCKED — explicit confirmation

With this round landed, **S-6 (the PJM T1-F ledger run) is unblocked and should be
chartered next**: solo heavy slot (8.8 GB peak RSS recorded, "no co-run"; 19.0 min cold,
3.8 min/solve-year), years sequential, ledgers under
`<out-dir>/PJM/<cache_key>/evolution_<year>.json`, registered on the FORECAST namespace
via `scripts/register_forecast_run.py` with `run_config.json` committed (FC-7), never
the backcast registry. It now measures against the corrected bar — the reason it was
sequenced strictly after S-5. Stated in advance so the result cannot be misread: the
default-on backstop will now target the held-last bar in 2029–2030 (rate limits
permitting), so S-6's ledger decides how the restated gap expresses — as a persisting
I7 shortfall, or as additional administrative backstop build surfacing in the FC-2
backstop-share caveat (23.6 % already) — and whether 2029 fails. Either expression is
the corrected bar working; neither resurrects the 366 MW reading.

---

*Files changed:* `src/market_sim/model/capacity_evolution/retirements.py` (the
convention + docstrings), `src/market_sim/config/capacity_market.py` (registry comment +
2029/30 intake pointer), `scripts/check_forecast_invariants.py` (D-1 repair, I7+I12),
`model-methodology-spec.md` (three sites), `tests/unit/model/test_capacity.py`,
`tests/regression/test_forecast_invariants.py`, this FINDING.
