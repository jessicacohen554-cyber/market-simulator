# Desktop launcher

Double-click entry point for the Scope 2 Hourly LCE Portfolio tool — no
command line required. Implements **ADR 0016**
(`../docs/decisions/0016-desktop-launcher.md`).

## Usage

- **macOS / Linux:** double-click `run_lce.sh` (or run it from a terminal:
  `./launcher/run_lce.sh`).
- **Windows:** double-click `run_lce.bat` (or run it from a terminal:
  `launcher\run_lce.bat`).

Either script resolves a usable Python (see below), starts a local web
server bound to `127.0.0.1` on an ephemeral port, and opens your default
browser on the launch page. Configure a run, click **Add to queue** for each
one you want, then **Submit queue** — runs execute **sequentially** (one LP
solve at a time), and each finished run's `results/<run_id>/report.html`
opens automatically when "open report when done" is checked.

Both scripts accept the same flags, forwarded to
`python -m lce_portfolio.launcher`:

| Flag | Effect |
|---|---|
| `--no-open` | Don't open a browser (server still starts; used by tests/CI). |
| `--port N` | Bind a fixed port instead of an OS-assigned ephemeral one. |
| `--results DIR` | Results-store root each run's `--results` output writes under (default `results/`). |
| `--state-dir DIR` | Where saved configs / last-used values persist (default `launcher/`). |
| `--inputs-dir DIR` | Directory searched for the default LMP export (default `data/inputs/`). |

Stop the server with `Ctrl+C` in the terminal it's running in (or just close
the terminal window).

## Exposed parameters

Exactly the set in ADR 0016 §3 — everything else stays config-file-only
(pass an advanced `--config` file straight to `python -m lce_portfolio`
yourself if you need a non-default knob):

- **ISO** — one of `ERCOT`, `CAISO`, `PJM`, `MISO`, `NYISO`, `NEISO`, or the
  data-free `SAMPLE` demo/test ISO.
- **Mode** — `premium_cap` (maximize matching under a premium cap) or
  `matching_target` (minimize premium to hit a matching target).
- **Premium deltas** / **matching targets** — whichever list the selected
  mode sweeps (comma-separated).
- **LCOE sensitivity** — `low` / `mid` / `high`.
- **Load file path** — defaults to the bundled 100 MW stylized reference
  load (`data/reference/reference_load_100mw.csv`, generated on first use).
- **LMP file path** — defaults to the newest `bau_lmp_*.csv` export found
  under `data/inputs/`; a `_dummy` file is clearly flagged **SYNTHETIC** in
  the UI. The launcher never generates or fetches an LMP file itself and
  never triggers a market-sim solve — it only reports what's already on
  disk.
- **Run ID** — auto-generated (`<iso>_<mode>_<timestamp>`) if left blank.
- **Open report when done** — auto-opens that run's `report.html` on
  success.

The side panel also lets you **save the current form as a named
configuration** and reload it later, and shows the **queue** of runs staged
for the next submit. Saved configurations and the last-submitted values
persist as JSON under `launcher/` (`saved_configs.json` / `last_used.json`,
both gitignored — machine-local state, not shared through version control).

## Python resolution (ADR 0016 §4)

Both scripts try, in order:

1. `../.venv` relative to `scope2-lce-portfolio/` (i.e. the repo-root venv).
2. `python3`, then `python` on `PATH` — gated by a version check (`>= 3.11`)
   **and** an import check (`highspy`, `numpy`, `pandas` must import
   cleanly).
3. If neither resolves, the script exits with an actionable message
   pointing at `requirements.txt` — it never creates a venv or runs `pip`
   itself.

```
python3 -m venv .venv
.venv/bin/pip install -r scope2-lce-portfolio/requirements.txt   # macOS/Linux
.venv\Scripts\pip install -r scope2-lce-portfolio\requirements.txt  # Windows
```

## Platform coverage

`run_lce.sh` and `run_lce.bat` are twins with identical behavior (ADR 0016
§1). CI exercises the `.sh`/Python path end-to-end (`tests/test_launcher.py`);
**`run_lce.bat` is not CI-tested on Windows** — its Windows-only batch logic
(`where`, `.venv\Scripts\python.exe`, `%~dp0` resolution) is review-verified
only. If you hit an issue running it on Windows, please report it.

## Troubleshooting

- **"no usable Python found"** — install Python 3.11+ and the packages in
  `requirements.txt` (see above), or make sure `../.venv` (relative to
  `scope2-lce-portfolio/`) has them installed.
- **Browser doesn't open** — the server still starts; the terminal prints
  the URL (`http://127.0.0.1:<port>/`) to open manually.
- **"load file not found" / "LMP file not found"** — the launch page shows
  the resolved default paths; if neither exists yet, generate the bundled
  reference load automatically (it's created on first run) or point the
  fields at your own files.
- **A run shows an error status** — the launch page shows a short, friendly
  message (never a raw traceback); the full detail is also printed to the
  terminal running the server.
