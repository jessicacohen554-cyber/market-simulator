# Security note — tracked `.env` credential leak remediation (2026-07)

> Status: RECORD (frozen). Documents a one-time security remediation.
> Lane: refactor-consolidation Workstream B1 (owner decision D-1,
> `docs/refactor-consolidation-plan-2026-07.md` §3, §9).

## What happened

A `.env` file carrying **5 live API keys** was tracked in git and had been for
its whole history:

| Key name | Service | Rotation portal |
|---|---|---|
| `EIA_API_KEY` | EIA Open Data API v2 | https://www.eia.gov/opendata/register.php |
| `MISO_PRICING_API_KEY` | MISO Data Exchange (pricing) | https://apim.misoenergy.org |
| `MISO_LOAD_API_KEY` | MISO Data Exchange (load) | https://apim.misoenergy.org |
| `ERCOT_API_KEY` | ERCOT Public API | https://apiexplorer.ercot.com |
| `DATA_GOV_API_KEY` | data.gov | https://api.data.gov/signup |

The keys were consumed by `scripts/data/fetch_*` scripts, each of which hand-rolled
its own inline `.env` parser (8 copies of the same loop).

## What was done (this remediation)

1. **All 5 keys were rotated by the owner** at their respective self-service
   portals before this change landed. The values previously committed are now
   **dead** — they no longer authenticate against any service.
2. **`.env` was untracked** — `git rm --cached .env` (the local working-copy
   `.env` is preserved on disk for continued local use; only the tracked copy is
   removed). `.env` / `.env.*` are ignored via `.gitignore` §2 (with a
   `!.env.example` negation), added in the Wave 1A `.gitignore` consolidation.
3. **`.env.example`** was committed carrying key **NAMES only** (no values) plus
   the registration portal for each — the template a developer copies to `.env`.
4. **`scripts/lib/env_keys.py`** (stdlib-only) is the single key resolver:
   `get_api_key(name, *, required=True, hint="")` checks `os.environ` first, then
   parses the repo-root `.env` if present, and exits with the registration-URL
   hint when a required key is missing. It never logs or prints a key value.
5. The **8 hand-rolled `.env` parsers were ported** to `get_api_key`:
   `scripts/data/fetch_eia930_hourly.py`, `fetch_miso_hub_lmp.py`,
   `fetch_eia860.py`, `fetch_eia_aeo.py`, `fetch_eia_delivered_gas.py`,
   `fetch_eia_coal_prices.py`, `fetch_aeo_electricity.py` (delegates via
   `scripts/lib/benchmark_corridor/aeo.py`), and that `aeo.py`. Optional-key and
   `DEMO_KEY`-fallback call sites use `required=False`; the `scripts/archive/`
   copies were left untouched (frozen calibration record).

## Decision: NO git history rewrite

The leaked values are **not** scrubbed from historical commits, deliberately:

- **The clone is shallow / grafted.** A history rewrite (filter-repo / BFG) needs
  full, ungrafted history; rewriting a grafted clone produces a broken or partial
  result.
- **Pushes are API-only and cannot force-push.** Per CLAUDE.md's Git & Pushing
  rule, all pushes go through `mcp__github__push_files`, which commits
  server-side and **cannot** force-update refs — a rewrite could not be published
  through the sanctioned path.
- **A rewrite would orphan `git.sha` provenance.** Every calibration bundle
  sidecar records the `git.sha` of the commit that produced it. Rewriting history
  changes every downstream SHA, orphaning that provenance chain across all
  registered runs — a far larger integrity cost than the (already-neutralized,
  rotated) dead keys in old commits.

**Rotation is the mitigation, not history rewrite.** Because the keys are dead,
their presence in historical commits carries no residual credential risk.

## Verification performed

- `git ls-files` confirms `.env` is no longer tracked.
- A grep of tracked files for the rotated key **values** (values never printed)
  found zero matches — no other tracked file carried a copy.
- Each ported fetcher's `--help` runs; `ruff check` is clean on all touched files.

## Optional follow-up (not done here)

- Enabling GitHub Advanced Security secret scanning (billed) — deferred to the
  owner (D-1 "optional").
