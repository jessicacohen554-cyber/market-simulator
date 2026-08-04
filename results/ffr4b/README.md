# FFR-4B — the four arms behind the MISO solar-revenue lane

Slim per-arm record for
`docs/handoffs/ffr-4b-miso-solar-revenue-2026-08-04.md`. Each arm keeps its own
`--out-dir` cache root, so the `evolution_<year>.json` ledgers live at
`<arm>/MISO/<cache_key>/` — **not** the out-dir root (FFR-3C blocker 10:
`load_ledgers_for_run` returns `{}` rather than raising, so a wrong path reads
as "no evolution happened", which in an entry-screen lane looks exactly like a
null result).

Committed: the `evolution_<year>.json` ledgers (which carry the
`entry_screen_diagnostics` rows this lane is measured on), the
`year_<year>_floor_retentions.json`, and each arm's `run_config.json` /
`meta.json`. **Ignored** (`.gitignore`, same class as `/results/ffr3v/`): the
heavy regenerable `year_<year>.parquet` LP output and `config.yaml`.

These are **unregistered forecast-family diagnostic probes with no scored
output** — not backcast runs (rule 15 registers those) and carrying no scored
leg for the forecast dashboard. Same disposition FFR-3V gave its own
instrumented probe.

| arm | registry | `entry_vre_capacity_revenue` | cache key |
|---|---|---|---|
| `ctl`  | unwired (generic 0.18)  | off | `ca36ba26ebe1640f` |
| `gate` | unwired (generic 0.18)  | ON  | `27597e342ed68fd1` |
| `wire` | wired (MISO 0.3875)     | off | `ca36ba26ebe1640f` |
| `both` | wired (MISO 0.3875)     | ON  | `27597e342ed68fd1` |

The registry constant is a `constants.py` value, not a `ScenarioConfig` field,
so it does **not** enter the cache key — `ctl`/`wire` and `gate`/`both` share
keys by design, and they were kept apart by their **separate `--out-dir` cache
roots**. All four were solved at base `5eac75b0`, i.e. BEFORE FFR-4C's wind-PTC
window.

Reproduce (one arm at a time — a single MISO solve holds ~7.3 GB RSS, so two
concurrent invocations will not fit in a 15 GB container):

    uv run python scripts/run_capacity_hindcast.py --iso MISO \
      --fuel-variant realized --vintage 2020 --start-year 2021 --end-year 2025 \
      --entry-screen-diagnostics [--entry-vre-capacity-revenue] \
      --out-dir results/ffr4b/<arm>

Read them with:

    uv run python scripts/probes/ffr4b_read_arms.py \
      CTL=results/ffr4b/ctl GATE=results/ffr4b/gate \
      WIRE=results/ffr4b/wire BOTH=results/ffr4b/both

**NOTE:** the `ctl` and `wire` arms are no longer reproducible from HEAD by the
command above. MISO's `ISOConfig.default_scenario_overrides` now arms the gate,
and an explicit `--no-entry-vre-capacity-revenue` does **not** override it —
the runner applies the per-ISO default to any field equal to its
`ScenarioConfig` default. See handoff §4.4.
