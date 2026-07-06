# HP-05 — Final extraction QA signoff

**Verdict: SHIP-WITH-NOTES.** The standalone `scope2-lce-portfolio/` tool
extracts cleanly, runs end-to-end outside the parent repo on committed data
only, and passes its full suite (328 tests). Six adversarial audit passes
found five documentation/provenance defects and zero correctness or isolation
defects; all five were fixed inline this session (Fixes A–E below). The "notes"
are the standing carve-outs already documented (ADR 0015 backcast-validation
LMP/CO₂ bundles are not forecast-mode outputs; the market-sim forecast path
stays on hold per stakeholder), not open blockers.

Audit date: 2026-07-06. This re-applies the six confirmed findings of a prior
HP-05 audit session whose container died before it could commit.

## The six audit passes

### 1. Extraction (does the folder run alone outside the repo?)
**Pass.** `scripts/verify_standalone.sh` copies the tool to a temp dir outside
the checkout, builds a fresh venv from `requirements.txt` only, and drives it
end-to-end: `pytest -q` (328 passed), the synthetic sample sweep, a real-ISO
ERCOT CLI run on bundled data (real non-synthetic CF profile confirmed, a
170 KB `report.html` written), and a launcher HTTP smoke test (served `/` with
200 on an ephemeral port). Trimmed output at the end of this file.

### 2. Isolation / vendoring (no `import market_sim`?)
**Pass.** No `.py` file under `src/` imports `market_sim`
(`grep -rn "import market_sim" src/ --include=*.py` → none; the only textual
hit is a comment in `src/lce_portfolio/vendored/README.md` that explains the
tool avoids the import). The two market-sim-reading scripts
(`build_profiles.py`, `build_fossil_avg_co2_rate.py`) reuse vendored logic and
read on-disk parquet, never the package. The verify script's own guard is
anchored to real import statements so the doc comment does not trip it.

### 3. Data contract (are the committed bundles complete & traceable?)
**Finding → fixed (Fix A).** The six `data/emissions/*_2024_fossil_avg_co2_rate.parquet`
files shipped with **no** `.provenance.json` sidecars, unlike the sibling LMP
bundles. A committed market-sim output with no provenance is untraceable. Added
one sidecar per ISO mirroring the ADR 0011 LMP schema (source keeper id,
bundle, solve date, mode, hours, collapse note, summary stats,
`backcast_validation_only`), pointing at the same bridge solve as the sibling
LMP bundle (ADR 0013), plus a `.gitignore` negation so they are tracked.

### 4. Docs truth (do the docs match the code/tree?)
**Findings → fixed (Fixes C, E).** (a) Stale suite counts (147 / 254 / 259)
across README.md, PLAN.md and `docs/handoff/README.md`; the README Status
paragraph predated the HP waves. (b) `docs/how-it-works.md` described the
committed `data/profiles/*` CF profiles as "Gitignored" — they are committed
(HP-02, gitignore-negated), and the regenerates-vs-ships sentence mislabeled
them. Both corrected against the tree.

### 5. Launcher posture (self-contained, loopback-only, no dead routes?)
**Finding → fixed (Fix B).** The launch-page footer linked to
`../docs/site/index.html` — a `/docs/` route the hardened server deliberately
does **not** serve (it serves only `/`, `/api/*`, `/reports/*`), so the link
404s. Replaced with honest text pointing at the on-disk docs path; the page
stays fully self-contained (no CDN/external fetch, verified by the existing
self-containment test). Loopback-only binding and the no-`--host`-flag guard
are intact.

### 6. Results store (committed sample bundle browsable?)
**Pass.** The committed `results/SAMPLE_premium_cap_*` bundle is discovered by
the past-runs browser with a working `/reports/<id>/report.html` link
(`test_list_past_runs_finds_committed_sample_run`); the `/reports/` route
rejects traversal/absolute paths.

## Fixes applied inline this session

| Fix | What | Commit |
|-----|------|--------|
| A | Six `data/emissions/*.provenance.json` CO₂-rate sidecars + `.gitignore` negation | `ca2a697` |
| B | Replace dead `/docs/` footer link with on-disk docs text | `ca2a697` |
| C | Refresh stale test counts → 328 (README, PLAN, handoff README) + README Status | `9c4dbfb` |
| D | Regression tests: `test_launch_page_has_no_dead_relative_links`, `tests/test_bundled_provenance.py` | `ca2a697` |
| E | Correct `how-it-works.md` profiles status (committed, not gitignored) + ships-vs-regenerates | `9c4dbfb` |

## Final inventory

**Top-level tree:** `PLAN.md`, `README.md`, `data/`, `docs/`, `examples/`,
`launcher/`, `pyproject.toml`, `requirements.txt`, `results/`,
`run_portfolio.py`, `scripts/`, `src/`, `tests/`. Package
`src/lce_portfolio/` = 12 modules; `tests/` = 29 `test_*.py` files;
`docs/decisions/` = 17 ADRs (0004–0019 + index).

**Authoritative test count: 328 passed** (`python -m pytest tests/ -q`,
2026-07-06; same 328 inside the standalone copy).

**Six-ISO bundled data — every file now provenance-sidecarred:**

| ISO | Source keeper (bridge solve) | LMP CSV (+prov) | CO₂-rate parquet (+prov) | CF profile |
|-----|------------------------------|-----------------|--------------------------|------------|
| ERCOT | 2026-07-06-ercot34-stage4-overlay-off | 165 KB (+782 B) | 136 KB (+988 B) | 132 KB |
| CAISO | 2026-07-03-caiso-51-firm-base | 165 KB (+756 B) | 109 KB (+972 B) | 189 KB |
| PJM   | 2026-07-05-pjm-77-ct-relfloor | 148 KB (+767 B) | 135 KB (+977 B) | 190 KB |
| MISO  | 2026-07-06-miso-42-coal-econ-ablation | 157 KB (+783 B) | 134 KB (+996 B) | 271 KB |
| NYISO | 2026-07-06-nyiso-53-li-tsl | 165 KB (+744 B) | 110 KB (+967 B) | 178 KB |
| NEISO | 2026-07-06-neiso-49-stgas-netload | 165 KB (+763 B) | 114 KB (+976 B) | 189 KB |

All CO₂-rate sidecars carry `backcast_validation_only: true` and the ADR 0013
contract note; each names the same keeper as its sibling LMP bundle (ADR 0011).

## Trimmed extraction-run output (`scripts/verify_standalone.sh`, EXIT 0)

```
== grep guard: no real 'import market_sim' statement anywhere in the copy ==
OK: no market_sim import
== building a fresh venv (PARENT_ROOT unreachable from here) ==
== pytest -q ==
328 passed, 1 warning in 135.32s (0:02:15)
== examples/run_sample_sweep.py ==
LCE portfolio sweep — ISO=SAMPLE mode=premium_cap
                 1 |     47.87% | solar_pv=882, onshore_wind=94
                20 |     73.38% | solar_pv=1,274, onshore_wind=436, battery_4h=268
== real-ISO CLI run on bundled data only (ERCOT) ==
                10 |     54.42% |  residualCO2=227,546 t | solar_pv=104, onshore_wind=78
                20 |     84.58% |  residualCO2= 77,401 t | solar_pv=110, onshore_wind=216
OK: results/verify_standalone_ercot/ERCOT_run_metadata.json confirms a real (non-synthetic) CF profile was used
OK: results/verify_standalone_ercot/report.html written (170115 bytes)
== launcher smoke test (--no-open --port 0) ==
OK: launcher served / with HTTP 200 on port 38063
== ALL CHECKS PASSED ==
```
