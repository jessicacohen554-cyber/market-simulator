# NEISO (ISO-NE) measured reserve CLEARING PRICES — validation only

Two ISO Express reports, both per hour-ending × reserve location:

**Real-time** — *Final Hourly Reserve Zone Prices & Designations* (report tree
`ancillary-hourly-rzpd-final`), CSV endpoint (needs the report page's
`isox_token` session cookie; a bare `?start=` 500s — pass a range):

    https://www.iso-ne.com/transform/csv/finalhourlyreserveprice?start=YYYYMMDD&end=YYYYMMDD

Columns: Ten-Minute Spinning (TMSR), Ten-Minute (TMNSR) and Total 30-minute
(TMOR) reserve clearing price, plus each product's designated MW.

**Day-ahead** — *Day-Ahead Hourly Reserve Requirements Prices Designations and
Forecast* (tree `ancillary-daas-hourly-rr`):

    https://www.iso-ne.com/transform/csv/daasreservedata?start=YYYYMMDD&end=YYYYMMDD

Same three clearing prices plus the FER price, the hourly requirements and the
forecast MW. **Coverage starts 2025-03-01** — ISO-NE's Day-Ahead Ancillary
Services (DASI) go-live. Earlier months return a header-only report with zero
data rows (verified 2025-01-01 / 2025-02-01, neiso-76): before DASI ISO-NE
cleared **no day-ahead reserve product**, so the pre-2025-03 DA LMP carries no
reserve component at all.

Locations (ISO-NE reserve-location vocabulary): `7000=ROS` (system-wide — the
row the model's reserve requirement consumes), `7001=SWCT`, `7002=CT`,
`7003=NEMABSTN`.

## Layout

    rzpd_final_<start:YYYYMMDD>_<end:YYYYMMDD>.csv   # RT, one file per month
    daas_<start:YYYYMMDD>_<end:YYYYMMDD>.csv         # DA (DASI), one per month

The window CSVs are **gitignored** (the NYISO-archive push-limit precedent).
Regenerate with the committed probe:

    python scripts/probes/_neiso76_reserve_content.py --fetch

**Rule 13 posture: these are measured PRICES and are the VALIDATION TARGET.**
They are never an input to a solve and no derived artifact reads them — the
sibling `requirements/` series (as-enforced requirement MW) is the input side,
and it stays the only reserve series the LP sees. First used by neiso-76 to
reproduce the nyiso-110 reserve-content decomposition on NEISO's own posted
prices (`results/calibration/FINDING-neiso76-dabid-phase0-2026-08-02.md` §B).

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

DATA NEEDED: none beyond the public reports.
