# 0019 — Mode A build-size tiebreak (`build_tiebreak_epsilon`)

- **Status:** accepted
- **Date:** 2026-07-05
- **Session:** CAISO Mode-A degenerate-solution follow-up (flagged by
  `docs/validation-2026-07-05-5iso-backcast-extension.md`, PLAN.md §10/§8
  "next open work")
- **Implemented by:** `config.py` (`build_tiebreak_epsilon`), `lp.py`
  (`build_and_solve`'s Mode A objective block), `tests/test_mode_a_build_tiebreak.py`

## Context

The 5-ISO backcast-validation extension (2026-07-05) found that CAISO's
Mode-A premium-cap sweep does not reproduce the clean monotonic frontier the
other five ISOs show: matching saturates at **100% from the lowest premium
setpoint ($1/MWh) up**, with the LP building `onshore_wind` to 16,000–19,500 MW
against its 20,000 MW ADR 0009 resource-potential cap, for a facility whose
real need is a small fraction of that.

The root cause is structural, not CAISO-specific. Mode A's objective is a pure

```
minimize Σ_t grid_buy[t]
subject to net_cost − BAU ≤ delta · Σ load
```

with **zero weight on `build_mw`** — `build_mw` (and, when active,
split-storage `build_energy`) appear nowhere in the Mode A cost vector, only in
constraints. Once a portfolio drives `grid_buy` to its floor (matching = 100%)
at a build level *below* a resource's cap, and the premium constraint still has
slack at that build level (as CAISO's LMP/excess-resale economics do — a
volatile, mean-$48/MWh series with `excess_sale_fraction = 1.0`, ADR 0005),
every larger build up to the cap is **exactly tied** on the only thing Mode A's
objective measures. The LP is free to return any point on that degenerate
face. The crossover-off IPM (ADR 0003) does not reliably return the
minimum-norm vertex of a tied face — which point it lands on depends on
irrelevant details like the resource cap itself (confirmed empirically, see
`tests/test_mode_a_build_tiebreak.py::test_no_tiebreak_is_degenerate_across_resource_caps`:
the same system with caps 450/1000/2000 MW returns build 449/967/1320 MW at an
identical setpoint and identical matching).

The existing code carried a prior note (`lp.py`, since removed) that "a
least-cost tiebreak was tried and removed — it stalled the solver." Two
things are true about that:

1. A **cost-scaled** tiebreak (weighting `build_mw` by `fixed_mwyr`, mixing
   $10⁴–10⁵/MW-yr coefficients into the same objective as a `+1`-per-MWh
   `grid_buy` term) reproduces the historical mixed-scale problem: the
   coefficient ratio between the two objective components varies by resource
   and by cost scenario, so no single small constant is safely negligible
   everywhere without also risking being scaled away to numerical noise
   somewhere else.
2. It also doesn't necessarily fix the *symptom*. `net_cost` is not
   monotonic in `build_mw` along the degenerate face either — spot-checking
   the same toy system (`fixed_mwyr=30`, `excess_sale_fraction=1.0`) shows
   `net_cost` at a smaller build can be *more* negative (cheaper) or *less*
   negative than at a larger build depending on where the IPM's interior
   point happens to land, because nothing in the *true* LP ever asked for
   `net_cost` to be minimized either — it is only ever bounded, not optimized,
   in Mode A. Weighting the tiebreak by real $ terms inherits that same
   flatness instead of curing it.

## Options considered

1. **Least-cost tiebreak, weighted by `fixed_mwyr`/`vom`/`lmp` (the net-cost
   expression).** Rejected per the two points above: reintroduces the
   documented mixed-scale solver risk, and is not guaranteed to discriminate
   toward a smaller build (net cost can be exactly as flat as matching along
   the degenerate face).
2. **A hard per-run sanity cap on `build_mw`.** Rejected: arbitrary, ISO- and
   scenario-specific, and just relocates the degenerate corner to wherever the
   new cap sits instead of removing the degeneracy.
3. **Flat, unitless epsilon directly on `build_mw` (and `build_energy`),
   Mode A only.** A pure "prefer less capacity when the primary objective is
   indifferent" tiebreak. Dimensionally simple (a single small constant, not a
   product of two differently-scaled quantities), directly targets the
   observed symptom (unnecessary capacity) regardless of whether the tied
   face is also cost-flat, and mirrors the existing `storage_epsilon` pattern
   (`config.py`, already applied as a flat constant on `chg`/`dis` in both
   modes without solver issues). Chosen.

## Decision

Add `PortfolioConfig.build_tiebreak_epsilon: float = 1e-6` (validated
non-negative, `0.0` disables it exactly reproducing pre-ADR-0019 behavior).
In `lp.py`'s Mode A objective block only:

```
cost[build_off : gen_off]        += build_tiebreak_epsilon   # build_mw[r], all r
cost[bev_off : bev_off + n_split] += build_tiebreak_epsilon  # split-storage build_energy[k]
```

Mode B is untouched — its objective already directly minimizes `net_cost`
(`fixed_mwyr`, `vom`, `lmp` terms), so `build_mw` is never a free direction
there.

### Sizing rationale

The tiebreak's total contribution to the objective must always be dominated
by any real difference the *primary* objective (`Σ grid_buy`, units: MWh of
unmatched load) could report. With `build_tiebreak_epsilon = 1e-6` and even a
generous sum of every resource's cap across a full multi-technology ISO
catalog (order 10⁵–10⁶ MW, e.g. CAISO's ~3×10⁵ MW summed cap table), the
tiebreak's maximum possible total is order 0.1–1 — several orders of
magnitude below any meaningful `grid_buy` difference for a facility load of
any realistic size (hundreds to low thousands of MWh at typical matching
levels, `sum_load` up to ~10⁶ MWh/yr at the low end of industrial scale), and
far above the crossover-off IPM's own interior-point noise floor observed in
practice (~1e-10–1e-13 MWh residuals on `grid_buy`, see the test module). This
keeps the tiebreak "always negligible, always distinguishable" without
per-scenario tuning — the same design property `storage_epsilon` (0.001,
flat on `chg`/`dis`) already relies on.

Unlike the rejected cost-scaled tiebreak, this coefficient is applied in a
single unit (MW) with no multiplication by a differently-scaled resource
attribute, so there is no scenario-dependent risk of the ratio between the
tiebreak and the primary objective blowing up for an expensive resource or
collapsing to numerical noise for a cheap one.

## Validation (2026-07-05)

`tests/test_mode_a_build_tiebreak.py`:

- **Characterizes the bug**: a 24h synthetic system engineered to reproduce
  the CAISO mechanism (a resource with a CF floor that never drops to zero, a
  duck-curve-like LMP, full excess resale) shows the raw (epsilon = 0)
  solution's `build_mw` drifting with the resource cap (449 / 967 / 1320 MW
  across caps 450 / 1000 / 2000 MW) at identical matching and setpoint — the
  degenerate-face signature.
- **Proves the fix**: with the tiebreak on, `build_mw` locks to the true
  minimum sufficient capacity (400 MW, `load / cf_floor`) across caps spanning
  450 MW up to 20,000 MW (CAISO's actual onshore-wind cap, in miniature) — the
  direct fix for "saturates ... by building onshore wind to its cap."
- **Frontier check**: a 7-point Mode-A sweep (`{1,2,5,7,10,15,20}` $/MWh) on
  the same system stays monotonic non-decreasing in matching, honors the
  premium cap at every setpoint, and now reports a build 400x smaller than the
  20,000 MW cap at every point instead of drifting toward it.
- **Non-distortion check**: on a structurally-capped solar-only system (no
  storage, 8/24 sun hours, so matching genuinely cannot saturate at any
  premium and `grid_buy` is a real, non-zero, binding quantity), the
  tiebreak changes `matching_pct`/`premium`/`build_mw` by less than the
  solver's own numerical tolerance — confirming it never perturbs an
  already-pinned, non-degenerate optimum. This is the regime PJM/MISO/NYISO/
  NEISO (and CAISO away from the saturated band) actually solve in.

Real-data re-validation (CAISO 2024 sweep before/after, ERCOT 2024 sweep as
control) is recorded in
`docs/validation-2026-07-05-caiso-mode-a-tiebreak-fix.md`.

## Consequences

- New config field flows into run metadata automatically (`asdict(config)`)
  and into `PortfolioConfig.from_file`'s `_FLOAT_FIELDS` type check.
- Every existing committed `results/*_backcast2024_premiumcap/` bundle other
  than CAISO's already sits in the non-degenerate regime (per the 5-ISO
  memo's own monotonicity findings) — the fix changes their reported
  `build_mw` by a numerically negligible amount, never their `matching_pct`/
  `premium`. CAISO's bundle is expected to change materially (that is the
  point) and is re-solved and re-committed alongside this ADR.
- Isolation boundary unchanged: zero `market_sim` imports; the change touches
  only `scope2-lce-portfolio/`.
- Defers: a true lexicographic (two-phase) solve — first minimize `grid_buy`,
  then re-solve minimizing `build_mw` subject to that optimal value — would be
  exact rather than epsilon-approximate, at the cost of a second LP solve per
  setpoint. Not pursued: the epsilon approach is a single solve, the existing
  codebase already accepts the same approximation for `storage_epsilon`, and
  the validation above shows no observable distortion at realistic scales.
  Revisit only if a future ISO/scenario is found where the epsilon's fixed
  magnitude is not comfortably subdominant (e.g. a facility load many orders
  of magnitude smaller than any tested here).
