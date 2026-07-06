# 0015 — Forecast LMP selection: study years, BAU scenario identity, readiness gate, rollout

- **Status:** accepted (stakeholder-decided 2026-07-02) — **execution on hold**
  until the readiness gate below is met per ISO (PLAN.md §10)
- **Date:** 2026-07-02
- **Session:** PS-12 (planning-session doc removed at handoff cleanup; in git history)
- **Implemented by:** no code — `scripts/export_lce_lmp.py` (market-sim root)
  already implements everything; this ADR pins its arguments

## Context

ADR 0011 fixed the export *contract* — `(hour, iso, lmp)` CSV, load-weighted
zonal→ISO collapse, no escalation, the calibrated **forecast** run for the
modeled year — and the exporter is built and smoke-tested in `--dummy` mode.
Forecast runs are on hold (PLAN.md §10): the market-sim forecast side is not
yet production-ready. What the contract left open is the *selection*: which
modeled year(s), which exact `ScenarioConfig` is "the BAU", what must be true
of the forecast before its LMPs are trusted here, and the multi-ISO rollout
order. Deciding these now means lifting the hold requires zero new decisions.

## Options considered

1. **Years — single 2030** (the tool's `config.year` default); add years later.
2. **Years — small set (2028/2030/2035)** as separate sweeps.
3. **Years — five-point trajectory 2030/2035/2040/2045/2050** (chosen): full
   horizon coverage at 5-year spacing; one full-horizon solve per ISO caches
   all five, so the marginal export cost of the extra years is nil.
4. **Scenario — base `ScenarioConfig()`** (chosen) vs a named variant (mid
   carbon path, high gas path): the variants bake a policy/stress assumption
   into the BAU baseline that the premium is measured against.
5. **Readiness — backcast keeper + per-ISO sign-off** (chosen) vs sign-off
   only vs a blanket all-ISO lift: the chosen gate pairs objective evidence
   with an explicit human decision, per ISO.
6. **Rollout — readiness-driven** (chosen) vs fixed ERCOT-first vs all-six-at
   once: a fixed order would idle a ready ISO behind an unready one.

## Decision

1. **Study years: 2030, 2035, 2040, 2045, 2050.** One export file per year
   (`bau_lmp_<year>.csv` + provenance sidecar), one portfolio sweep per year
   with the tool's `config.year` set to match. 2030 is the first/primary study
   year. All five exports read the *same* upstream run: one sequential
   full-horizon forecast solve per ISO (2026→2050, one-pass capacity
   evolution) caches every year's `DispatchResult` as it completes.
2. **BAU scenario identity: the base `ScenarioConfig()` dataclass defaults, no
   scenario YAML.** Concretely: `mode="forecast"`, `gas_price_path="mid"`,
   `carbon_price=0.0` with `carbon_price_path="zero"`, `weather_year=2024`,
   default demand growth. The exporter canonicalizes per-ISO exactly as the
   runner does (`resolve_bau_config`: ISO override + `default_scenario_overrides`
   for fields left at dataclass defaults) **before** computing the cache key;
   the recorded provenance identity is that canonicalized `cache_key` in the
   sidecar, per ISO. If the dataclass defaults ever change, the cache key —
   not this ADR's prose — is the ground truth of what was exported.
3. **Readiness gate (lifts the PLAN.md §10 hold, per ISO).** An ISO's forecast
   LMPs may feed this tool only when **both** hold:
   - the ISO has a **current calibrated backcast keeper on the dashboard
     covering all its scoreable years** (the objective evidence that the ISO's
     market structure is calibrated), and
   - the **stakeholder explicitly signs off** that the forecast side is
     production-ready for that ISO, recorded by checking that ISO off in the
     PLAN.md §10 hold item.
   Until then that ISO stays on the `--dummy` synthetic stub (always labeled
   SYNTHETIC) or, for validation studies only, an `--allow-backcast` export
   (ADR 0011).
4. **Rollout: readiness-driven, first-ready-first.** Expected/preferred
   sequence is ERCOT (the calibrated reference) → PJM → the rest, but any ISO
   that passes the gate sooner (e.g. NEISO) goes ahead of the queue. Portfolio
   runs proceed on the ready subset immediately; as each ISO joins, the export
   command re-runs with the expanded `--iso` list (the per-ISO provenance
   blocks in the sidecar keep mixed-readiness files impossible — every ISO in
   the file passed the gate).

**The export, the day the hold lifts for a set of ISOs `<READY>` (from the
market-sim repo root; requires the cached full-horizon BAU forecast solve for
each ISO):**

```bash
for Y in 2030 2035 2040 2045 2050; do
    python scripts/export_lce_lmp.py --year "$Y" ${READY[@]/#/--iso }
    # e.g. first lift, ERCOT only:
    # python scripts/export_lce_lmp.py --year $Y --iso ERCOT
done
# companion residual-carbon file (ADR 0013), same cached solves, per ISO-year:
for Y in 2030 2035 2040 2045 2050; do
    for ISO in "${READY[@]}"; do
        python scope2-lce-portfolio/scripts/build_fossil_avg_co2_rate.py \
            --iso "$ISO" --year "$Y"
    done
done
```

No `--scenario`, no `--allow-backcast`, no `--dummy`, no `--out`: the defaults
*are* the decision. Missing caches are skipped and reported, never solved
implicitly.

## Consequences

- **Zero code changes.** The exporter already implements the contract; this
  ADR only pins `--year` values and the (default) scenario. The tool side sets
  `config.year` per sweep — 2030 needs no change; 2035–2050 sweeps override it.
- The upstream ask per ISO is one sequential 2026→2050 BAU forecast run (years
  are never solved in parallel within a run; the five export years fall out of
  the same cache). ISOs' runs are independent and may run concurrently per the
  market-sim parallelism rules.
- Rules out: escalated or interpolated LMP vintages between the five study
  years (a year between the grid points gets its own export, not
  interpolation); mixed forecast/dummy ISO blocks inside one blessed file;
  any 2030-only shortcut being presented as the trajectory.
- Defers: profile-year selection for 2035+ CF profiles (tool-side; today's
  profiles target 2030) — flagged for the first 2035 sweep, not blocking 2030.
- Follow-up: when the first ISO passes the gate, update PLAN.md §10 (check the
  ISO off), run the commands above, and record the sidecar `cache_key` in the
  sweep's outputs metadata.
