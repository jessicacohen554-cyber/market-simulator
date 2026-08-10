# FH-4-NEISO — the NEISO leg of the FH-4 forward-skill battery

**Session.** FH-4-NEISO `[FABLE]`, Wave FH Phase A (manager dispatch pack §0ag,
the five sibling legs RELEASED). Branch `claude/fh-4-neiso-leg-j42x61`, off
`origin/main` `aa61791e`. The FH-4 lift is **UNCONDITIONAL** (Addendum AI.1:
the ERCOT step-0 gate PASSED at 0.0 %/0.0 %/0.0 % vs the 26.8 % FAIL
reference), so this leg carries **no step-0 gate** — the I6 invariant rides as
a stop-the-line check on both arms instead (§1.1). Protocol of record:
`docs/handoffs/fh-4-ercot-leg-2026-08-09.md`, executed for NEISO at **SHIPPED
DEFAULTS** — no keeper contact, no arming, no tuning. Standing NEISO gas-basis
facts (neiso-86) noted and untouched: the window is 2023–2025; nothing here
re-opens the 2018-era basis.

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any solve was launched.
Nothing in §1 changes after. Sections §2+ are filled in order, as produced.
This leg lands NO code change — the Arm K `demand_growth_vintage` wiring
(protocol §1.3) is already at HEAD from the ERCOT leg; the only new file
committed with this prereg is the solve-independent γ-rider probe
`scripts/probes/fh4_instrument_date_split_neiso.py`.*

### 1.1 The I6 rider, as written (this leg's stop-the-line check)

**Criterion (dispatch step 3, applied AS WRITTEN).** The I6 over-retirement
invariant of `scripts/check_forecast_invariants.py`: single-year
economically-retired capacity as a fraction of prior thermal MW, cap **0.20**
(`Thresholds.econ_retire_frac_cap`), measured per evolution year from each
run's own ledgers (at `<out-dir>/NEISO/<runtime-key>/`).

**Verdict rule.** Each arm's registered invariant battery must read **I6 =
PASS**. An I6 FAIL on either arm is a **stop-the-line report to the manager**:
the run is still registered, the verdict + numbers are committed, and **no
skill number is quoted from a failed-I6 leg**. All other invariants (I7, I12
included) are reported alongside at full magnitude — they are context, not the
criterion.

**Expectation (to test, never a target).** PASS is expected on both arms: the
FH-1 I6 FAIL signature was measured on ERCOT at the pre-fix posture, the
re-based posture read I6 PASS on every subsequent ERCOT arm, and no
NEISO-specific over-retirement signature is on record. NEISO is untested on
the T1-FF surface — these are the first NEISO full-forward runs — so the
rider is applied as written whatever comes out.

### 1.2 Arm R invocation (declared before solving)

SHIPPED DEFAULTS throughout: no capacity-screen flags (the §0ag shared
protocol — the ERCOT-only scarcity restoration cannot and does not arm, rule
25 `[R-ISO-SCOPE]`; `capacity_screen_unified_lookahead` and
`capacity_screen_scarcity_restoration` both resolve **False**, verified in the
prereg config build), `retirement_rule="pipeline"` via the shipped default,
`confirmed_exits_enabled=True` (default-on) with
`confirmed_registry_as_of = 2023-12-31`.

```
uv run python scripts/run_capacity_hindcast.py --iso NEISO \
  --forward-from-base --arm realized --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/neiso-2023-2025-t1ff-armr-fh4
```

Posture resolved at prereg (config cache key **`a2c8e092ed5ec930`**): gas
`hindcast_realized` (annual Henry Hub 2.54 / 2.19 / 3.53 $/MMBtu for
2023/24/25), per-solve-year weather (`crossover_solve_year_weather=True`, so
the demand-growth table never binds — `demand_growth_vintage=None`),
`mode="forecast"`. Registered id `neiso-2023-2025-t1ff-armr-fh4`, hindcast
namespace, `meta.kind="full_forward"`, regardless of verdict or reads.

### 1.3 Arm K invocation (declared before solving)

The protocol-§1.3 wiring (landed by the ERCOT leg, already at HEAD — nothing
armed here): `--arm asknown` at base 2023 sets
`demand_growth_vintage = 2023`, fail-closed, alongside its gas path.

```
uv run python scripts/run_capacity_hindcast.py --iso NEISO \
  --forward-from-base --arm asknown --vintage 2023 \
  --start-year 2023 --end-year 2025 \
  --out-dir results/hindcast/neiso-2023-2025-t1ff-armk-fh4
```

Posture resolved at prereg (config cache key **`1c7271f2927c6542`**): gas
`hindcast_asknown_aeo2023` (nominal 5.48 / 4.34 / 3.80 $/MMBtu vs realized
2.54 / 2.19 / 3.53 — **+116 % / +98 % / +7.6 %**, the ex-ante AEO2023 error
Arm K exists to measure; Henry Hub is ISO-agnostic, and the NEISO basis rides
identically in both arms so it nets out of the K-vs-R spread); weather pinned
to 2023 for every solve year (`crossover_solve_year_weather=False`); demand
growth for 2024/25 at the **as-of-2023 ISO-NE CELT rate 2.03 %/yr** (2023
CELT, May 2023, Table 1.5.2: 122,057 GWh (2023) → 140,481 (2030)).
**Direction note, stated at prereg:** unlike ERCOT (live 8.5 %/yr vs as-known
2.433 %/yr), the NEISO as-known vintage grows FASTER than the live table's
1.3 %/yr near — the 2023 CELT expected growth that did not materialize
(ISO-NE 2026 CELT records 2025 net energy 116,679 GWh, BELOW the 2023 CELT's
122,057 GWh 2023 starting point) — so the vintage wiring pushes Arm K demand
UP against actuals in 2024/25, compounding the +98 % 2024 gas vintage on the
price side. Registered id `neiso-2023-2025-t1ff-armk-fh4`, hindcast
namespace, `meta.kind="full_forward"`, regardless of reads. Sequential after
Arm R (rule 12; 15 GB / 4-core container).

### 1.4 The skill reads (the §2.1b metric set), pre-registered

From `scripts/score_crossover.py` run verbatim per arm — no new metric, no
re-derivation: `dispatch_skill.metrics` = **fuelmix, price_mean, price_shape**
(+ `co2` reported) per scored year 2023–2025, each carrying `forecast_err`,
`keeper_backcast_err`, `input_gap = |forecast_err| / |keeper_backcast_err|`.
Keeper comparator: the CURRENT NEISO keeper at this head,
**`2026-08-06-neiso-87-control`** (**RE-VERIFIED** in
`frontend/data/backcast/keepers/NEISO.json` — the dispatch's "at this
writing" id holds; determination CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered
C3c caveat). The three-way read per metric-year (plan §2.1): keeper err →
Arm R err → Arm K err; the R-vs-keeper spread is the **overlay value**, the
K-vs-R spread the **driver-forecast error**. Both are the program's
deliverable, reported at full magnitude, never targets, never tuned toward.

**Pre-registered directions (to test, never targets):**

* **Arm R**: first NEISO T1-FF read — no defect reference and no
  pre-registered magnitude. Directions: input_gaps expected materially above
  1 everywhere (the forward stack loses the keeper's measured-overlay
  content: CAMPD outage windows, F923 delivered fuel, same-year CEMS rates,
  weather pinning); the keeper's ledgered C3c model-class limitation (0
  model hours > $300/MWh) carries to both arms a fortiori — no scarcity tail
  is expected to form in any lane, and NEISO's forward capacity-market
  footing carries no ORDC overlay (ERCOT-only, rule 25). Winter price_shape
  months are the expected locus of shape error (the keeper's known
  winter-scarcity family).
* **Arm K vs Arm R**: price errors expected HIGHER (shifted upward) in
  2023–2024 (+116 % / +98 % as-known gas on a gas-marginal system, plus the
  §1.3 demand-vintage push) and near-converged by 2025 (+7.6 % gas, though
  the demand push remains); fuel-mix expected to shift against gas in
  2023–2024, but with materially LESS switching headroom than ERCOT — NEISO
  carries ~0.4 GW of coal and no large non-gas thermal reserve, so the
  expected margin movers are oil/dual-fuel units and the fixed-profile
  import/nuclear base, and the K-vs-R fuelmix spread is expected SMALLER
  than ERCOT's. Directions only; the measured spread IS the result.
* **Quoting rule.** These reads are quoted as T1-FF skill ONLY if both arms
  ran the pre-registered posture and the arm's I6 rider PASSED (§1.1).
  Otherwise they are rider context only.

### 1.5 The γ rider: instrument-date split of the window's actual exits

**Purpose (AG.2 γ rider, carried by every leg).** The exit-side skill number
must never be mis-attributed: the T1-FF confirmed-exit channel is
information-gated at `confirmed_registry_as_of = date(vintage, 12-31)` =
**2023-12-31**, so a window exit whose enforceable instrument post-dates the
cutoff is invisible to that channel BY DESIGN — the information gate working,
not a screen miss.

**Method (solve-independent; computed from committed artifacts only).**
`scripts/probes/fh4_instrument_date_split_neiso.py` (committed with this
prereg, the ERCOT probe's construction verbatim with NEISO paths): take the
scorer's own target rows
(`data/raw/_validation-source/capacity_actuals_neiso.csv`,
`kind="retirement"`) for the leg's window 2023–2025; match
`(plant_id, generator_id)` against the confirmed-exit registry
`data/raw/confirmed-retirements/neiso.csv`; split the actual MW into
instrument-dated **≤ 2023-12-31** vs **after / no instrument**. Also reported
for 2021–2025 — the scorer's own unfiltered referent window
(`score_capacity_hindcast.score_retirements` reads the ENTIRE actuals file,
never the bundle's window; protocol §5).

**The split, computed AT PREREG (probe run before either arm solved):**

| Window | Actual exits (all) | Thermal | Instrumented ≤ cutoff | Instrumented after | No instrument in registry |
|---|---|---|---|---|---|
| 2023–2025 (the leg's) | 1,402.1 MW | 1,360.7 MW | **0.0 MW** | 345.6 MW | 1,056.5 MW |
| 2021–2025 (the scorer's referent) | 3,273.9 MW | 2,991.5 MW | **0.0 MW** | 345.6 MW | 2,928.3 MW |

Registry facts visible at prereg, stated for honesty: the NEISO registry
carries exactly two rows — Merrimack 1/2 (plant 2364), instrument the 2024
Clean Water Act consent decree dated **2024-03-29**, exit deadline 2028-06 —
both post-cutoff, and only Merrimack 2 (345.6 MW coal, physical cessation
2025) appears in the actuals window at all. ZERO MW of the window's actual
exits were confirmed-knowable at the vintage cutoff, so both arms' exit-side
rows measure the economic/announced channel only. The full attribution
narrative follows in §5 after the arms run.

### 1.6 Governance

* Holdout freeze read at launch by the harness (recorded in `meta.json`);
  solve years {2023, 2024, 2025} — training-tier only; no out-of-training
  backcast year solved/scored/registered; no measured H1-2026 contact
  anywhere; scoring never leaves 2023–2025 (the scorer refuses both bounds).
* Hindcast namespace ONLY — never the backcast registry, never
  `frontend/data/forecast/`. No keeper contact, no promotion, no shipped
  default flip, no matrix cell verdict beyond measurement citations. Bar
  re-levels, signal scaling, tuning toward any residual: refused by name.
  The NEISO keeper's open items (the P2 replay escalation, the stale-Aug-2025
  basis defect (i), the site-retention state) are the comparator's record —
  read, not acted on.
* ≤5 solve-years per invocation (3 here); years sequential within an
  invocation; invocations sequential in this container (15 GB / 4 cores).
* Registration commitment: every solved run registers REGARDLESS of verdict
  or reads. Commit order: prereg → rider verdicts → results → handoff, as
  they exist.
* The other sibling ISO legs and FH-5 are NOT this session's; re-litigating
  the lift is refused (the determination is the manager's record, Addendum
  AI.1).

---

*(Sections below this line are filled AFTER the pre-registered work runs, in
order, as produced.)*
