# NYISO forecast findings — 2026–2035 (P-3A completion)

**Session.** Continuation of P-3A of
`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §2
(testing-audit **G1**). The prior P-3A session
(`docs/handoffs/full-horizon-findings-2026-07-12.md`) stopped mid-horizon at
the owner's request with **NYISO at only 1/25 years (2026)**. This session
completes NYISO's window: reference-config forecast, **2026–2035** (10 years,
not the full 2050 horizon — scoped run per this session's task), years
sequential, invariants I1–I14 scored. Findings only — no model code,
threshold, or offer-curve change (rules 1/11/14). Forecast probe: nothing
registered on the backcast dashboard. No 2022/H1-2026 solve (rule 22
inapplicable — forecast mode uses no measured holdout actuals).

**Config.** `ScenarioConfig(mode="forecast", start_year=2026, end_year=2035)`,
every other field at default — `use_campd_bins=True` (NYISO's per-plant CAMPD
default), **`capacity_market_clearing=False`** (the P-2A recommendation; not
an A/B this pass). `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1
OMP_NUM_THREADS=1`, single invocation (rule 12 — years solved sequentially
in-process).

**Reproduce.**
```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NYISO \
  --start-year 2026 --end-year 2035 --out-dir results/full-horizon/nyiso
uv run python scripts/check_forecast_invariants.py \
  --run-dir results/full-horizon/nyiso/NYISO/<cache_key>
```
Cache key this run: `4dd351321c4b2a6d`. Per-year cache makes this resumable.

---

## 1. Headline findings

1. **NEW — conventional hydro (~3.3 GW, ~9% of NYISO's 2026 fleet) silently
   drops out of the dispatch fleet in every forecast year past the last
   available EIA-923 vintage.** `build_hydro_fleet` → `load_hydro_budget` →
   `_load_hydro_generation(iso, year)` (`data/hydro.py:254-278`) filters the
   EIA-923 monthly-generation table to an **exact** `year` match. The forecast
   path calls it with the literal calendar year (`runner.py:936-943` passes
   `year` unclamped into `build_dispatch_fleet` → `build_hydro_fleet`), and
   `load_monthly_generation()`'s newest vintage tops out at **2026** (verified
   `sorted(df['year'].unique()) = [2018..2026]`). So year 2026 finds a
   non-empty subset and builds a normal ~3.3 GW hydro fleet, but **every year
   2027+ finds zero rows**, `load_hydro_budget` raises `ValueError("No
   EIA-923 hydro generation for NYISO in 2027")`, and `build_hydro_fleet`'s
   `except (FileNotFoundError, ValueError): return [], None`
   (`data/hydro.py:618-620`) swallows it — the hydro fleet becomes `[]` with
   no warning. Confirmed directly against this run's fleet context: `hydro`
   is a 3343 MW key in `capacity_by_fuel_mw` for 2026 and **absent entirely**
   for 2027–2035. This is a **forecast-path-only bug** (`forecast_budget=True`
   is meant to set the *level* to normal-water-year climatology per the
   docstring — the *shape* is still supposed to come from "`year`'s EIA-923"
   — but nothing clamps `year` to the latest available vintage when the
   literal forecast year has no data, so the whole plant lookup collapses
   instead of degrading to a shape fallback). Likely **not NYISO-specific** —
   any ISO with conventional hydro (CAISO, NEISO, PJM) hits the same wall in
   every forecast year past 2026, which the prior P-3A partial run
   (2026-07-12, produced before the 2026 EIA-923 vintage landed) would not
   have surfaced. Not fixed (findings-only); a plausible remedy is clamping
   `year` to `min(year, LATEST_EIA923_YEAR)` inside `build_hydro_fleet`'s
   forecast branch so the shape falls back to the newest real vintage instead
   of silently zeroing the fleet.
2. **I7 (reliability floor) and I12 (reserve-margin band) both fail, and the
   hydro dropout is a strong root-cause candidate for the magnitude, if not
   the whole story.** I7 fails at 2026 *and* 2027 (`accredited firm 31326 <
   requirement 37154 MW`; `36481 < 37711 MW`); I12 fails at the 2026 trough
   (4.9%, near the ERCOT-style de-firming pattern the 2026-07-12 report
   documented) and then the reserve margin **never re-enters the [13.8%,
   28.7%] band on the high side either** — it overshoots to 30.7% (2031),
   36.4% (2033), and 41.9% by 2035, monotonically widening every year from
   2031 on. This is the same "de-firm then over-correct" two-phase failure
   the 2026-07-12 report found in every scored capacity-market ISO with
   `capacity_market_clearing=False` (§1 finding 2 there) — a non-responsive
   fixed capacity price cannot equilibrate. The hydro-fleet loss compounds it
   here in a NYISO-specific way: the evolution ledger's own `firm_clean_mw`
   reads **0 in 2026 too** (not just 2027+ — see `evolution_2026.json`), so
   the accreditation/requirement bookkeeping already excludes hydro from
   "firm clean" credit in the base year, while the *dispatch* fleet still
   physically carried 3.3 GW of hydro in 2026 only. That inconsistency (hydro
   priced into dispatch capacity but zero-credited in the adequacy ledger,
   then removed from dispatch capacity entirely from 2027) is worth a
   dedicated root-cause session — it sits upstream of both invariant fails.
3. **Massive thermal overbuild, consistent with the fleet-wide non-equilibrium
   pattern.** Thermal capacity grows 30.0 GW → 43.9 GW (+46%) over the 10-year
   window while VRE (wind+solar) grows 3.9 GW → 24.9 GW (+538%); total
   installed capacity 43.5 GW → 75.1 GW (+73%) against peak demand growing
   only 29.9 GW → 33.5 GW (+12%). `builds_thermal_mw` is 5000 MW in the single
   year 2027 alone (the year hydro disappears), then a steady ~1000 MW/yr
   after — consistent with the model reacting to the hydro-fleet loss (and
   the I7 shortfall) with a large one-time thermal build, then continuing to
   build past what load growth alone would justify because the capacity
   price never falls to signal the fleet is now long (finding 2).
4. **Price and CO₂ trend directionally sane but the late-horizon price spike
   is scarcity-shaped, not overbuild-shaped — worth a second look.**
   Load-weighted price rises smoothly 45.15 → 61.13 $/MWh through 2034 (fuel/
   carbon/thermal-mix drift, unremarkable), but 2035's `max_hourly_price`
   jumps to $225.1 (vs. $60–95 in 2030–2034) even though 2035 has the
   *highest* reserve margin (41.9%) of the run — a single-hour scarcity spike
   coexisting with a fleet that is nominally 42% over its planning
   requirement is itself a symptom of the non-responsive capacity price (the
   $/MWh scarcity mechanism and the $/kW-yr capacity price are not talking to
   each other in this configuration). CO₂ is non-monotone (32.8 → 35.4 Mt
   2026→2030, then falling to 30.6 Mt by 2035) as VRE displaces the 2027-era
   gas overbuild — directionally consistent with the RPS dual sitting pinned
   at the $40 ACP ceiling every single year (I10 passes as "≥0, stable", but
   a *constant* ACP-bound dual for 10 straight years means NYISO's modeled
   VRE fleet never catches its RPS target in this window — worth confirming
   against T1.6 once the ladder harness runs NYISO).

---

## 2. Feasibility — wall time & peak RSS

| year | wall (s) | peak RSS (MB) |
|---|---|---|
| 2026 | 101.7 | 2587.8 |
| 2027 | 52.0 | 2263.6 |
| 2028 | 54.0 | 2117.6 |
| 2029 | 51.8 | 2118.5 |
| 2030 | 50.1 | 2138.3 |
| 2031 | 51.1 | 2326.0 |
| 2032 | 50.5 | 2325.7 |
| 2033 | 50.0 | 2163.4 |
| 2034 | 50.3 | 2122.4 |
| 2035 | 51.2 | 2514.9 |

**Total: 10/10 years solved, 563.0 s (9.4 min) wall, 2.59 GB global peak
RSS.** Unlike PJM/CAISO in the 2026-07-12 report, NYISO shows **no strong
super-linear growth through year 10** — median non-base-year wall is a flat
~51 s and RSS oscillates 2.1–2.6 GB rather than climbing (contrast PJM's
2045–2050 years at 30–40 min each). NYISO's per-plant CAMPD fleet is smaller
than PJM's 8-zone fleet, and this window doesn't yet reach NYISO's own
late-horizon tail (2036–2050 unrun) — this run cannot rule out the same
super-linear pattern appearing further out. 2026 is the slowest single year
(101.7 s) — plausibly the CAMPD per-plant bin construction's one-time cost
plus the (now-explained) hydro-fleet build only happening that year.

---

## 3. Invariant matrix (I1–I14)

| id | name | status | detail |
|---|---|---|---|
| I1 | energy balance | PASS | max \|supply−demand\| = 5.275e-11 MW (2026); tol 1.0 |
| I2 | no NaN/inf | PASS | clean |
| I3 | unserved/dump | PASS | ok |
| I4 | capacity accounting | PASS | closes |
| I5 | no retire-and-reenter | PASS | ok |
| I6 | econ-retirement sanity | PASS | ok |
| I7 | reliability floor | **FAIL** | 2026: accredited firm 31326 < requirement 37154 MW; 2027: accredited firm 36481 < requirement 37711 MW |
| I8 | planned-additions gating | PASS | ok |
| I9 | storage integrity | PASS | ok |
| I10 | RPS dual sign+stability | PASS | ≥0, stable (pinned at $40 ACP every year — see finding 4) |
| I11 | one-pass | PASS | single pass |
| I12 | reserve-margin band | **FAIL** | band [13.8%, 28.7%]; out: 2026:4.9%, 2031:30.7%, 2032:33.6%, 2033:36.4%, 2034:39.2%, 2035:41.9% |
| I13 | cobweb detector | PASS | smooth |
| I14 | price sanity | PASS | in band |

**2 FAIL, 0 WARN, 14 checks.** Same two invariants (I7, I12) fail as in the
2026-07-12 report's other capacity-market ISOs (CAISO, PJM) — this is the
documented systemic non-equilibrium under `capacity_market_clearing=False`,
not a new NYISO-only failure mode (though finding 1's hydro dropout is new
and NYISO-specific evidence for *why* the reserve-margin overshoot is as
large as it is here).

---

## 4. Capacity / price / CO₂ trajectory

| year | LW price $/MWh | max hourly $/MWh | CO₂ (Mt) | peak demand (MW) | reserve margin | RPS dual $ | thermal (MW) | firm-clean (MW) | VRE (MW) | total cap (MW) | builds: thermal / renew (MW) | retire (MW) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 45.15 | 58.8 | 32.83 | 29,866 | 4.9% | 40.0 | 30,008 | 3,343 | 3,900 | 43,544 | 0 / 0 | 0 |
| 2027 | 43.78 | 52.4 | 35.41 | 30,314 | 20.3% | 40.0 | 35,008 | 0 | 6,900 | 48,193 | 5,000 / 3,000 | 8 |
| 2028 | 44.19 | 54.7 | 34.60 | 30,769 | 25.0% | 40.0 | 36,907 | 0 | 7,900 | 51,092 | 1,899 / 1,000 | 0 |
| 2029 | 44.97 | 58.6 | 35.12 | 31,230 | 26.7% | 40.0 | 37,907 | 0 | 8,900 | 53,092 | 1,000 / 1,000 | 0 |
| 2030 | 46.41 | 60.7 | 35.45 | 31,699 | 28.4% | 40.0 | 38,907 | 0 | 9,900 | 55,092 | 1,000 / 1,000 | 0 |
| 2031 | 48.42 | 62.7 | 33.83 | 32,174 | 30.7% | 40.0 | 39,907 | 0 | 12,900 | 59,092 | 1,000 / 3,000 | 0 |
| 2032 | 52.95 | 77.9 | 32.66 | 32,496 | 33.6% | 40.0 | 40,907 | 0 | 15,900 | 63,092 | 1,000 / 3,000 | 0 |
| 2033 | 56.98 | 84.9 | 31.88 | 32,821 | 36.4% | 40.0 | 41,907 | 0 | 18,900 | 67,092 | 1,000 / 3,000 | 0 |
| 2034 | 59.66 | 94.7 | 30.74 | 33,149 | 39.2% | 40.0 | 42,907 | 0 | 21,900 | 71,092 | 1,000 / 3,000 | 0 |
| 2035 | 61.13 | 225.1 | 30.61 | 33,481 | 41.9% | 40.0 | 43,907 | 0 | 24,900 | 75,092 | 1,000 / 3,000 | 0 |

`firm-clean` is the evolution ledger's own field (reads 0 every year — see
finding 2); it is **not** the same figure the trajectory extractor's
`capacity_by_fuel_mw["hydro"]` shows for 2026 (3,343 MW) — the two hydro
accountings disagree even in the one year hydro is present in the dispatch
fleet.

---

## 5. Ranked issue list

1. **[NEW, high impact]** Forecast-path hydro fleet silently empties past the
   last EIA-923 vintage (§1 finding 1) — likely affects CAISO/NEISO/PJM too,
   any year beyond 2026 as of this session. Root cause: `data/hydro.py`
   `_load_hydro_generation`'s exact-year filter + `build_hydro_fleet`'s
   swallowed exception, called with an unclamped forecast `year` from
   `runner.py:936-943`.
2. **[carried from 2026-07-12]** I7/I12 two-phase non-equilibrium under
   `capacity_market_clearing=False` — NYISO reproduces the same systemic
   failure mode already documented for CAISO/PJM; the audit plan's CR-1/CR-2
   work (P-1B/P-2A, capacity demand curves) is the designated fix lane, not
   this session.
3. **[NEW]** `firm_clean_mw` accounting disagreement between the evolution
   ledger (0 every year) and the dispatch-fleet-derived trajectory metric
   (3,343 MW in 2026 only) — needs a root-cause session to determine which
   (if either) feeds the I7 requirement/accreditation calc correctly.
4. **[NEW, lower priority]** 2035's single-hour $225 price spike at a 41.9%
   reserve margin — flagged as a scarcity/capacity-price mechanism
   disconnect, not diagnosed further this session.
5. **[carried]** RPS dual pinned at the $40 ACP ceiling for all 10 years —
   consistent with a persistently-short VRE build relative to NYISO's RPS
   target in this configuration; worth a T1.6-style ladder check.

No code, threshold, or offer curve was changed. This report and the run's
`full_horizon_summary.json` (`results/full-horizon/nyiso/`, gitignored
disposable cache) are the deliverable; nothing here is registered on the
backcast dashboard (forecast probe, rule 15/16 inapplicable).
