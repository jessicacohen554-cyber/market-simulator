# SPP-14 instrument records (2026-09-06)

The scripts here are the records of what `FINDING-spp-14-2026-09-06.md` computed, kept beside their
outputs so every number in the FINDING is reproducible; they were run from the session scratchpad
and carry that absolute path (`/tmp/claude-0/…/scratchpad`) — edit `S` to re-run. Producers that a
later session should run live are elsewhere: `scripts/data/build_spp_lmp_reference.py --per-hub`
(row 5) and `scripts/data/fetch_spp_alt_portal.py` (rows 6–9).

| File | What |
|---|---|
| `crosscheck.py` → `crosscheck.json` | the rule-14 gate (§3) and the per-hub spread table (§4) |
| `census.py` → `census.csv` | every distinct (constraint, monitored, contingent) with binding hours, mean/max shadow price, 2023–2025 |
| `groups.py` → `four_group_table.csv`, `four_group_detail.csv` | the four-group membership rules (§5.1), the table (§5.2), constituents and sensitivities (§5.3) |
| `gridstatus_openapi_1.3.0.json` | the hosted API's OpenAPI document as served (`api.gridstatus.io/openapi.json`, 168,774 B) — the only gridstatus.io page the session could read |
