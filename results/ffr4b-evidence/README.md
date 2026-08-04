# FFR-4B — the four arms' evolution ledgers (evidence only)

The small, human-readable half of the four arms behind
`docs/handoffs/ffr-4b-miso-solar-revenue-2026-08-04.md`: each arm's per-year
`evolution_<year>.json` (which carries the `entry_screen_diagnostics` rows the
lane is measured on) plus its `run_config.json` and `meta.json`.

The full bundles (~84 MB of solved parquet) are NOT committed — these are
**unregistered forecast-family diagnostic probes with no scored output**, so
they are not backcast runs (rule 15 registers those) and they carry no scored
leg for the forecast dashboard. Same disposition FFR-3V gave its own
instrumented probe.

| arm | registry | `entry_vre_capacity_revenue` | cache key |
|---|---|---|---|
| `ctl`  | unwired (generic 0.18)  | off | `ca36ba26ebe1640f` |
| `gate` | unwired (generic 0.18)  | ON  | `27597e342ed68fd1` |
| `wire` | wired (MISO 0.3875)     | off | `ca36ba26ebe1640f` |
| `both` | wired (MISO 0.3875)     | ON  | `27597e342ed68fd1` |

The registry constant is not a `ScenarioConfig` field, so it does not enter the
cache key — `ctl`/`wire` and `gate`/`both` share keys by design and were kept
apart by their **separate `--out-dir` cache roots**. All four were solved at
base `5eac75b0`, i.e. BEFORE FFR-4C's wind-PTC window.

Reproduce (each arm, sequentially — one MISO solve holds ~7.3 GB RSS):

    uv run python scripts/run_capacity_hindcast.py --iso MISO \
      --fuel-variant realized --vintage 2020 --start-year 2021 --end-year 2025 \
      --entry-screen-diagnostics [--entry-vre-capacity-revenue] \
      --out-dir results/ffr4b/<arm>

Read them with `scripts/probes/ffr4b_read_arms.py <label>=<out-dir> ...`.

NOTE: the `ctl` and `wire` arms are no longer reproducible from HEAD by the
command above — MISO's `default_scenario_overrides` now arms the gate, and an
explicit `--no-entry-vre-capacity-revenue` does NOT override it (handoff §4.4).
