# Queue-cap citation -- eastern-ISO `QUEUE_CAP_GW` (2026-07)

**Branch:** `claude/forecast-queue-caps-citation`
**Scope:** forecast-only; no holdout solve. `config/capacity_market.py`
(`QUEUE_CAP_GW`, `QUEUE_CAP_PER_TECH_GW`).

## What this is

`QUEUE_CAP_GW[iso]` (GW/yr) caps the **total nameplate MW** the economic
new-entry screen (`model/capacity_evolution/new_entry.py:768`) and the
reserve-margin adequacy backstop (`model/capacity_evolution/adequacy.py:346`)
may build in one forecast year. It is a *pace ceiling* -- the plausible annual
**commercial-operation (COD) throughput** of the interconnection process --
NOT the queue-*request* volume (100s of GW/ISO, never all built), and NOT a
central-case forecast. So a value modestly above each ISO's demonstrated peak
annual COD is the correct level; the number only ever bites as an upper bound
on build speed. Rule-13 admissible: a published throughput ceiling that
regenerates for any forecast year.

## In-repo check (Step 0)

No queue/COD-throughput dataset exists on disk. Checked: `data/raw/` (full
listing), `data/raw/capacity-deliverability/` (holds **locational RA
requirements** -- CETO/CETL/LCR/MIC -- not annual throughput),
`data/raw/iso-specific-transmission/` (transfer limits/flows), and
`data/raw/reference/`. **Research-first**; caps are cited to public ISO/EIA/LBNL
reporting in the code comments, not to a curated partition.

## Caps set (with provenance)

| ISO | cap (GW/yr) | basis | status |
|-----|------------:|-------|--------|
| ERCOT | 12 | ERCOT CDR throughput; recent COD ~5-10 GW/yr | cited (pre-existing) |
| CAISO | 8 | CAISO TPP deliverability; recent COD ~4-8 GW/yr | cited (pre-existing) |
| PJM | 10 | demonstrated peak COD ~8-10 GW (2015-2018 gas build; ~11 GW gas CC 2013-2017). Recent COD backlog-depressed (2.0/4.8/2.8 GW in 2023/24/25); reformed Cycle process clearing ~63 GW for 2025-2028 -> 10 GW forward ceiling at historical peak | **CITED** |
| MISO | 10 | recent COD 5.6 GW (2023), 7.5 GW (2024), ~26.8 GW over 2023-2025 (~9 GW/yr, rising) -> 10 GW just above demonstrated throughput | **CITED** |
| NYISO | 4 | measured COD ~0.5 GW/yr (~2,274 MW total 2019-2024, Gold Book). 4 GW is a forward ceiling **above** demonstrated throughput, driver = CLCPA offshore-wind + downstate bursts | **LABELLED ESTIMATE** |
| NEISO | 4 | measured COD ~0.5-1.5 GW/yr (solar+storage). 4 GW forward ceiling **above** throughput, driver = MA/RI/CT OSW pipeline | **LABELLED ESTIMATE** |

Values are **unchanged** from the prior placeholders -- the work here replaced
the single vague `needs-citation` comment with per-ISO provenance and an honest
`CITED` vs `LABELLED ESTIMATE` split (rule 11: prefer real data; where a real
number couldn't ground the level, keep the estimate but label it and open this
follow-up rather than bury it).

### Sources
- EIA Today-in-Energy id=37293 (PJM natural-gas build-out); id=67205 (record 2026 US additions).
- S&P Global Market Intelligence, "PJM 2017 capacity additions led by gas combined-cycle, renewables."
- PJM Inside Lines 2024/2025 Year-in-Review; Utility Dive #728145 (recent PJM COD < 2 GW).
- MISO System Planning Committee, "Resource Adequacy & Generator Interconnection Queue Update" (2025-09 / 2025-12); MISO GI queue-cycle results (misoenergy.org).
- NYISO 2024 Load & Capacity Data Report (Gold Book) / Power Trends 2024.
- ISO-NE Annual Markets Report (Fig. 1-9, generator additions & retirements), 2023/2024 editions.
- LBNL "Queued Up: 2024 Edition" (completion-rate analysis, queue mix).

## Per-tech caps (`QUEUE_CAP_PER_TECH_GW`)

Eastern per-tech splits are relabelled from `needs-citation` to
**engineering-judgment estimates**: the cited ISO-total ceiling disaggregated by
recent build mix (solar/storage-led PJM & MISO; OSW-weighted NYISO & NEISO). The
binding, cited quantity is the ISO total; the per-tech split is a judgment.

## Open follow-up (rule 11)

1. **NYISO / NEISO -- strike a real throughput number.** Both 4 GW caps are
   forward-ceiling estimates ~3-8x measured COD. If a forecast ever leans on
   eastern OSW build timing, replace with a pipeline-derived ceiling (Gold Book
   proposed-project COD schedule / ISO-NE FCA + queue COD dates), or curate a
   `data/raw/queue-throughput/` partition of annual COD by ISO x tech and read
   the caps from it (would also let per-tech splits become measured, not judged).
2. **PJM / MISO -- periodic re-verification.** Both are cited to demonstrated
   peaks; re-check against each ISO's latest planning report before quoting an
   eastern-ISO forecast that binds on entry pace.
