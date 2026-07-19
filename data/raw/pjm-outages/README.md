# PJM generation outages — Data Miner 2 `gen_outages_by_type`

PJM's published generation-outage forecast: the DAM-horizon
capacity-availability quantity that is the PJM analogue of ERCOT's 60-Day DAM
disclosure thermal availability, and the aggregate-coverage intake replacement
for the CAMPD unit-outage fallback in a PJM backcast.

## Source

- **Tool**: PJM Data Miner 2 — <https://dataminer2.pjm.com/feed/gen_outages_by_type>
- **API**: `https://api.pjm.com/api/v1/gen_outages_by_type`
- **Feed**: "Generation Outage for Seven Days by Type" (feed id 35).
  > "the actual and scheduled megawatt generation outages for today and the next
  > six days … subtotals for each of the following outage types: unplanned
  > (forced), maintenance, and planned … only outages with a status of active or
  > approved are included."
- **Posting**: daily 06:00 EPT. **First available**: 2015-05-26. Retained
  indefinitely.
- **Auth**: the anonymous `Ocp-Apim-Subscription-Key` the Data Miner 2 web
  client publishes at <https://dataminer2.pjm.com/config/settings.json> (no
  personal registration). Not a secret; grants read-only access to public feeds.
  Overridable via `--api-key` / `PJM_API_KEY` if PJM rotates it.

## Files

- `gen_outages_by_type.csv` — **immutable raw pull** (never edit in place),
  **gitignored** (reproducible). Written by `scripts/data/fetch_pjm_outages.py`;
  native feed columns (`forecast_execution_date_ept`, `forecast_date`, `region`,
  and the four MW columns). Current pull: execution dates
  **2018-01-01 → 2026-07-19**, 3 regions, 7 lead days each (65,511 rows).
- `by-year/gen_outages_by_type_<YEAR>.csv` — tidy per-year CSVs (the in-repo
  data the model reads). One file per year (~0.5 MB) with the `pjm-outages`
  schema: `forecast_execution_date`, `forecast_date`, `lead_days` (0..6),
  `region`, and the four MW columns. **Written locally by the derive step;
  see "Data-file status" below.**

## Processed artifact

`scripts/data/derive_pjm_dam_availability.py` writes two things from the raw
pull: the per-year CSVs above (the intended in-repo form) and the efficient
columnar `../pjm-dam-availability.parquet` (top-level `data/raw/`), which the
loader prefers when present. Both carry the identical schema
(`data/dictionary/schema/pjm-outages.schema.yaml`) and the deriver enforces the
RTO == sub-region-sum and components == total invariants.

## Data-file status (why the data bytes aren't committed here)

This intake session could commit only through the repo's **API-only push path**
(`mcp__github__push_files`), which commits file content as UTF-8 text emitted in
the call. That path **cannot** carry (a) the binary parquet (no binary
round-trip) nor (b) the ~4.3 MB of CSV rows (too large to emit reliably), and
`git push` is disallowed here. So the **data bytes are not committed**; what *is*
committed is the full, one-command-reproducible pipeline. The loader degrades
gracefully (returns NaN / empty, statistical fallback) until the data is present.
To land it, run the two commands under **Regenerate**, or land the `by-year/`
CSVs via a session with local `git`.

## Regenerate

```bash
python scripts/data/fetch_pjm_outages.py --start 2018-01-01 --end 2026-12-31
python scripts/data/derive_pjm_dam_availability.py
```

## Consumption

`market_sim.data.pjm_outages.pjm_dam_availability_series(year)` reads the source
(`pjm_outage_mw_series` → parquet-if-present else the per-year CSV),
selects the current-day actual (`lead_days == 0`), sums the unplanned components
(forced + maintenance) for the `PJM RTO` region, and converts to a fleet-wide
availability fraction against the model's PJM fossil-thermal nameplate, applied
uniformly across the covered classes. Intended to be gated by
`ScenarioConfig.pjm_dam_availability` (default off, backcast only); the config
flag + the `data.fleet` water-fill application are the ready-to-apply patch in
`docs/handoffs/pjm-dam-availability-wiring-2026-07.md` (deferred from this
data-intake session because they touch two 8k–10k-line core files that the
API-only push path can't re-emit safely).

## Admissibility (CLAUDE.md rules 11/13)

An operator-published, forward-looking outage forecast that regenerates for a
forward day and responds to conditions — a measured/forecast INPUT, not a fitted
answer. The measured negatives in `maintenance_outages_mw` (104 rows, min
-1232 MW) are a PJM reconciliation artifact and are preserved verbatim; the
components still sum to `total`.

## DATA NEEDED

- Nothing outstanding for the 2018–2026 window. To extend the horizon back to
  the feed's 2015-05-26 start, re-run the fetch with `--start 2015-05-26`.
- PJM publishes **no public per-fuel-class or unit-level outage split** (eDART
  generator detail is members-only), so the availability transform is a
  fleet-wide (uniform) derate. A zone/class-resolved allocation would need a
  non-public source or an assumed crosswalk; the sub-regional totals are retained
  in the parquet to support a future refinement.
