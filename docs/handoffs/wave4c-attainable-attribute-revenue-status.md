# Wave 4C — attainable attribute revenue (retirement screen): PENDING APPLICATION

**State: the fix is NOT applied to the codebase.** It exists on main only as two
verified patch files. Everything below is the record of a completed, verified
change whose final step — applying it to `retirements.py` — is blocked on the
large-file push path, not on any open question about the change itself.

## What the change does

`apply_economic_retirements` credits attribute revenue (EAC / RPS / §45U) on
**attainable in-merit generation**, `cap_mw × 1[price > mc]`, instead of realized
per-unit dispatch. It reuses the same `cap_mw` / `rows` / `zone` the attainable
`net_revenue` loop directly above already builds — one notion of capacity,
availability-derated (rule 19). In-merit is the energy test, not the reserve leg:
EAC/RPS/§45U are per-MWh credits on energy produced, and a unit holding reserve is
not generating. The `mc is None` legacy gross-revenue fallback has no cost basis
and therefore no in-merit test, so it keeps its realized reader.

The energy margin was already the basis-independent attainable (pro-forma) margin;
the attribute term was the last realized-dispatch reader in the screen. With both
on the same basis the retire/keep decision is a function of prices, `mc` and
capacity only, so it cannot be tipped by the alternate-optima reshuffle among units
tied at the marginal price (warm-start backlog #4).

The in-merit test is **strict** (`price > mc`), matching the energy margin's
`max(0, price − mc)`, which contributes 0 at a tie. `>=` would also be
tie-invariant but would credit *every* tied unit its full capacity, over-counting
energy.

### §45U adjudication — attainable on BOTH sides of the ratio

Not just the denominator:

1. **The realized ratio is not provably tie-invariant.** A ratio of two realized
   quantities *can* be tie-invariant, but this one is not: a marginal-tie reshuffle
   moves realized MW *between hours carrying different prices*, so the
   generation-weighted average `Σ(pₜdₜ)/Σ(dₜ)` shifts even though every `pₜ` and the
   LP objective are bit-identical. It is invariant only in the special case where
   all reshuffled hours share one price. Leaving §45U realized would re-open exactly
   the channel this change closes.
2. **The statutory reading is preserved.** §45U's basis is gross receipts from
   electricity sold ÷ MWh sold — an average *sale price* — and this screen is the
   Potomac SOM pro-forma, in which the unit sells its attainable in-merit output.
   Taking numerator and denominator from that same quantity keeps the ratio a true
   $/MWh average price; mixing bases (realized receipts over attainable MWh) would
   understate the price and *overpay* the credit.

## Verification performed

* **Backcast byte gate — PASS.** `scripts/regression_gate.py --mode byte`, ERCOT
  keeper `ercot_netrev_margin`, 2023–2025, both arms captured with
  `capture_keeper_goldens.py`: 6 files / 31 numeric columns identical at
  `atol=rtol=0`; `Σ|hourly Δ| = 0.0 GWh = 0.000%` of total generation in every year.
  Independently corroborated: all seven `content_hashes` in
  `results/regression-goldens/wave4c-{before,after}/manifest.json` are identical —
  those two files differ in exactly one field (`git_sha`).
  Mechanism: a backcast solves each year as a separate single-year invocation, so
  `fleet is None` → `build_base_fleet`, and `evolve_fleet` (hence the retirement
  screen) is never reached.
* **Forecast smoke — identical trajectory.** ERCOT 2026–2028, pre-fix and post-fix
  arms: 0 retirements and identical `fleet_by_fuel_after` in all three years.
  **Read this narrowly.** In the ERCOT reference config `eac_price_nuclear/wind/solar
  = 0.0` and `rps_dual = 0.0` in all three years, so for every non-nuclear fuel the
  attribute term is identically zero and the change is *provably* inert. It is live
  only for nuclear (4,980 MW; §45U pays 9–15 $/MWh at 2026–2028 prices, expiring
  2032) — that path was genuinely exercised and nuclear screen revenue did move, but
  no unit sat near the retire/keep threshold. A 3-year ERCOT horizon is a weak
  exercise of this screen; the golden 2026–2040 bands are the stronger test and have
  **not** been run.
* **Tests.** `tests/test_forecast_warmstart_tie_invariance.py` (merged test-only in
  PR #2845, RED on main) passes, as does `tests/test_xyear_warmstart_default.py`,
  unweakened.
* **Fast tier.** 4,913 passed / 82 failed — all 82 pre-existing, proven by reverting
  only `retirements.py` to main and re-running the same selection for a
  byte-identical FAILED set.

## Nothing was flipped

No `ScenarioConfig.xyear_cache` field was added and `runner.py` still passes
`xyear_cache=None`, so the forecast path remains cold-only. Removing the mechanism
that made cross-year warm start *non-neutral* is a **precondition** for the D-9
default flip, not the flip itself. D-9 still requires its own full-horizon
warm-vs-cold identical-trajectory A/B plus owner sign-off. **No such A/B exists** —
PR #2845 was 1 file / +135 lines (test only) and its branch is deleted.

## To land it

```
git fetch origin main && git checkout -B <branch> origin/main
git apply docs/handoffs/wave4c-attainable-attribute-revenue.patch
git apply docs/handoffs/wave4c-crossyear-warmstart-doc.patch
pytest tests/test_forecast_warmstart_tie_invariance.py tests/test_xyear_warmstart_default.py
```

Ten tests must pass, and `git hash-object src/market_sim/model/capacity_evolution/retirements.py`
must equal `3a0b919ea56be0d03cfeabc14943d965e33acaf2`. Delete all three
`wave4c-*` files in `docs/handoffs/` in the same commit that lands them, so the repo
does not accumulate un-applied patch debt.

**Apply both patches together or neither.** The doc patch states that the screen is
basis-independent; landing it without the code patch would make
`docs/cross-year-warmstart.md` assert something false about the code.

## Why this is a patch and not a commit

`retirements.py` is 1,804 lines / 88,612 bytes. `mcp__github__push_files` transmits
file content as model response output, and ~88 KB of JSON-escaped Python sits at the
single-response output boundary — the mechanism that clipped `constants.py`
6,368 → 33 lines and produced rule 27. Rule 27 also forbids it directly ("never
rewrite an existing source file ≥300 lines by pushing regenerated full content"),
while the Git section bans `git push` outright, so for any file ≥300 lines the two
rules leave no compliant path. That gap also blocks `scenarios.py` (563,932 B) and
`runner.py`, and needs an owner decision rather than a per-session workaround.

The patch is the safe carrier: at 6,500 bytes it transmits well within budget, and it
was verified two ways — `git apply` onto main's `retirements.py` reproduces blob
`3a0b919e`, and the pushed blob SHA `1be51bd5` matches the local `git hash-object`
byte-for-byte. Both patches were re-checked against main `f66a08b` and still apply.
