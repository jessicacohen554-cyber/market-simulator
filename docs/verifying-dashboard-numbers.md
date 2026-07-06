# Verifying a published dashboard number

This is the chain a human — no repo tribal knowledge assumed — follows to go
from a number displayed on the backcast results dashboard back to the exact
LP solve that produced it, and to independently reproduce it. It promotes the
recipe that otherwise lives only in `.claude/skills/calibration-report/SKILL.md`
(an agent's working notes) into user-facing documentation, per CLAUDE.md rule
14 ("every completed backcast run goes on the dashboard").

The two dashboard pages are static HTML/JS served from GitHub Pages:

- `docs/codebase-site/backcast-runs.html` — the **Run Explorer**, one run at a
  time (`#iso=<ISO>&run=<run-id>`).
- `docs/codebase-site/calibration-status.html` — the **Calibration Status**
  all-ISO keeper summary (`#iso=<ISO>`).

Both render client-side from committed JSON/JS data files; nothing on the
dashboard is computed at page-load time from a live solve. Every number you
see was baked in when someone ran the steps below.

## The chain, step by step

### 1. Identify the run id

Every dashboard number belongs to a **run id** of the form
`<bundle-date>-<shorthand>` (e.g. `2026-06-24-neiso-30-other-carry`), visible
in the Run Explorer URL fragment and in the Calibration Status page's link to
each ISO's current keeper. The **keeper** — the run currently representing an
ISO's best calibrated state — is recorded in
`frontend/data/backcast/keepers.json`.

### 2. Read the registry sidecar

`frontend/data/backcast/registry/<run-id>.json` is the complete, authoritative
manifest entry for that run: label, date, shorthand, one-to-three sentence
definition of what changed, the years solved, the ISO, and the **bundle
path** — e.g.:

```json
{
  "id": "2026-06-24-neiso-30-other-carry",
  "label": "neiso 30 other carry",
  "shorthand": "neiso-30-other-carry",
  "definition": "neiso-29 + OTHER residual class vintage-carry ...",
  "years": [2023, 2024, 2025],
  "iso": "NEISO",
  "file": "frontend/data/backcast/runs/2026-06-24-neiso-30-other-carry.js",
  "bundle": "results/calibration/neiso_30_other_carry_3yr"
}
```

`bundle` is where the actual solve output lives on disk
(`results/calibration/<bundle>/`). This sidecar is the single source of truth
for "what run produced this dashboard entry" — `manifest.js` (the file the
dashboard actually loads) is generated *from* the sidecars by
`scripts/build_manifest.py` and should never be hand-edited or trusted as
primary.

The displayed chart/table data itself lives in `runs/<run-id>.js`
(`frontend/data/backcast/runs/<run-id>.js`) as a gzip+base64 blob the browser
inflates with `DecompressionStream` — it is a rendering of the bundle, not an
independent source. To read it outside a browser, base64-decode and gunzip
the string assigned to `window.BC.runGz["<run-id>"]`.

### 3. Read the results/calibration bundle

`results/calibration/<bundle>/` is committed **slim**: the `dispatch/`
per-hour parquets and `system.parquet` are gitignored regenerable
intermediates (see `.gitignore`'s slim-bundle block), but four things you need
for verification ARE committed:

- `meta.json` — bundle metadata.
- `run_config.json` — **the exact configuration the solve ran with**: git SHA,
  branch, dirty/clean state, a `model_changes_note`, and the full
  `calibration_flags` dict (ISO, years, every CLI-settable toggle and offer
  override that was in effect).
- `SUMMARY*.md` — the human-readable per-year scorecard, if present.
- `calibration_attestation.json` — the governance attestation (DOF ledger,
  exceptions) when the bundle carries one.

`run_config.json` is the ground truth for "what was actually run" — if the
dashboard's prose definition and `run_config.json`'s flags ever disagree, the
JSON wins (this is a real, previously-found discrepancy class — see gap G-14
in `docs/gap-register-2026-07.md`).

### 4. Re-solve from `run_config.json`

To independently reproduce a bundle:

1. `git checkout <run_config.json's git.sha>` (or diff your working tree
   against it if `dirty: true` — a non-empty `changed_files`/`diffstat` means
   the recorded run includes an uncommitted patch on top of that SHA, which
   the bundle does not currently re-attach as a diff file for you to replay
   automatically; treat `dirty: true` bundles as harder to reproduce exactly
   and check `model_changes_note` for what the patch did).
2. Translate `calibration_flags` back into the `run_calibration_full.py` CLI
   invocation: each key in the dict corresponds 1:1 to a `--<flag-with-
   underscores-as-dashes>` argument (e.g. `"coal_prb_passthrough": 1.0` →
   `--coal-prb-passthrough 1.0`; nested dicts like
   `coal_prb_sigmoid_overrides` correspond to a group of related flags —
   cross-reference `scripts/run_calibration_full.py`'s `argparse` block for
   the exact flag name behind each key).
3. Run:
   ```bash
   python scripts/run_calibration_full.py --iso <ISO> --year <years from sidecar> \
       <translated flags> --out-dir results/calibration/<new-name>
   ```
   Full-year calibration runs are multi-GB, minutes-to-hours LP solves
   (CLAUDE.md rule 12); this is the expensive step and the reason the
   dashboard doesn't just re-solve on every page load.
4. Compare the new bundle's `SUMMARY*.md` / re-run
   `python scripts/calibration_verdict.py results/calibration/<new-name>`
   against the original run's determination. `calibration_verdict.py` reads
   **only committed artifacts** (sidecar, payload, benchmark parts, config,
   attestation, `legitimacy_diagnostics.json`) and never re-solves or touches
   the gitignored dispatch/system parquets, so re-running it on the *original*
   bundle reproduces its verdict byte-for-byte without a re-solve — a cheap
   first check before committing to a full re-solve. Note that exact
   byte-for-byte re-solve reproducibility is not guaranteed for every keeper
   today (see gaps G-11/G-12/G-13 in `docs/gap-register-2026-07.md`, which
   track known reproducibility drift under active investigation for
   CAISO/ERCOT/NYISO); a re-solve that lands close but not identical to the
   committed numbers is a known open issue, not necessarily a mistake in your
   reproduction.

### 5. How a run got on the dashboard in the first place

For context, the forward direction (bundle → dashboard) is:

```
run_calibration_full.py  →  results/calibration/<bundle>/
                                     |
                                     v
scripts/dashboard_add_run.py --bundle <bundle>  (reads parquets, no re-solve)
        |                                   |
        v                                   v
frontend/data/backcast/registry/<id>.json   frontend/data/backcast/runs/<id>.js
        |
        v
scripts/build_manifest.py   (assembles manifest.js/benchmark.js from ALL
                              committed sidecars — this is what the dashboard
                              actually loads; it is deploy-workflow-owned and
                              regenerated on every merge to main, never
                              hand-committed)
```

`scripts/dashboard_add_run.py` also prints the run's calibration determination
(`scripts/calibration_verdict.py` scored against
`docs/calibration-determination-rubric.md`) at registration time — the same
determination the Calibration Status page shows.

## Quick-reference summary

| You have | You want | Read this |
|---|---|---|
| A number on a dashboard chart | Which run produced it | The Run Explorer URL's `run=<id>` fragment, or the ISO's entry in `keepers.json` |
| A run id | The run's definition + bundle location | `frontend/data/backcast/registry/<id>.json` |
| A bundle path | The exact solve configuration | `results/calibration/<bundle>/run_config.json` |
| A configuration | An independently re-solved bundle | `python scripts/run_calibration_full.py` with the translated flags |
| Two bundles | Whether they score the same | `python scripts/calibration_verdict.py` on each (no re-solve needed) |

## Implemented: a plaintext metrics sidecar (G-49)

Verifying a headline number (e.g. "system volume error: 2.1%") without
running Python used to mean decompressing and parsing the gzip+base64 blob in
`runs/<id>.js`, or reading `SUMMARY*.md` prose — neither a stable, greppable,
machine-checkable artifact.

Every bundle registered via `scripts/dashboard_add_run.py` now also gets a
small plaintext `results/calibration/<bundle>/metrics.json` alongside
`run_config.json`, holding the headline numbers `calibration_verdict.py`
already computes: the overall determination, the per-criterion PASS/CAVEAT/
FAIL/SKIPPED status (`calibration_verdict.determine`'s `criteria` dict,
condensed to label/hard/status — the per-class/per-year record detail stays
in `SUMMARY*.md` / `legitimacy_diagnostics.json` / the `runs/<id>.js` payload,
not duplicated here), the caveat budget, and the D-10 free-class C1 score. For
example, `results/calibration/nyiso41_hubprices/metrics.json`:

```json
{
  "run_id": "2026-07-03-nyiso-41-hub-prices",
  "iso": "NYISO",
  "label": "nyiso 41 hub prices",
  "target_years": [2023, 2024, 2025],
  "scorable_years": [2023, 2024, 2025],
  "data_blocked_years": [],
  "determination": "NOT-YET",
  "reasons": ["undocumented out-of-tolerance (FAIL) criteria: forced_share"],
  "criteria": {
    "fuelmix": {"label": "C1 fuel-mix by class (grid-delivered)", "hard": true, "status": "PASS"},
    "forced_share": {"label": "C8 forced-energy share (D-2)", "hard": true, "status": "FAIL"}
  },
  "caveats": {"hard": [], "soft": ["C3a mean LMP"], "budget": {"hard_max": 1, "soft_max": 2}},
  "free_class_score": {"headline": "C1 all 14/14 · free 10/10"}
}
```

This lets a verifier `git show <sha>:results/calibration/<bundle>/metrics.json`
or `jq` a headline number directly from the committed tree — no browser, no
gzip/base64 decode, no Python. `calibration_verdict.py` remains the
authoritative *generator*: `condensed_metrics()`/`write_metrics_sidecar()`
build the sidecar directly from the same `determine()` verdict the CLI and
`dashboard_add_run.py` print, so it is never a hand-maintained duplicate. To
(re)write the sidecar for an already-registered run without re-solving:

```bash
python scripts/calibration_verdict.py --run-id <run-id> --write-metrics
```

All six current keepers carry a backfilled `metrics.json`, generated this way
from their already-committed artifacts (no re-solve, no new score). Retention
follows the bundle: the sidecar lives and is pruned with
`results/calibration/<bundle>/`, same as `run_config.json`. CI does not (yet)
diff it against a fresh `calibration_verdict.py` run to catch drift between
the committed sidecar and the bundle it claims to describe — a fast follow,
not required for the sidecar itself to be useful today.
