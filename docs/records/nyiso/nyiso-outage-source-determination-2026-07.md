# NYISO generator-outage source determination — 2026-07-22

**Question (owner ask):** should NYISO backcast outages come from a NYISO-native
DAM / outage feed instead of the EPA CAMPD/CEMS proxy — the way CAISO, PJM and
MISO use a published ISO outage instrument (`fetch_caiso_dam_outages.py`,
`fetch_pjm_outages.py`, `fetch_miso_outages.py`)?

**Determination: NO native source exists. Keep CAMPD/CEMS for NYISO.** NYISO
treats unit-level generator outages as **confidential market data** and does not
publish any public unit-level (or zonal) measured generator-outage dataset. The
CAISO "Curtailed and Non-Operational Generator Report" has **no NYISO analogue**.
For 2023–2025, CAMPD/CEMS (`data/raw/campd-unit-outages-NYISO.csv`, derived by
the frozen `scripts/data/derive_campd_unit_outages.py --iso NYISO`), supplemented
by NERC GADS class-average EFORd statistics
(`data/raw/reference/nerc-gads-eford-*`), is the correct and effectively the only
public stack. This closes the "check for NYISO DAM outage data" line — no intake
follows.

## What NYISO actually publishes (MIS public menu, `mis.nyiso.com/public/menu.htm`)

NYISO's public posture is the **inverse** of what an outage overlay needs: rich,
facility-level **transmission**-outage detail; essentially no **generator**-outage
detail.

| Public feed | MIS index | Content | Usable for gen outages? |
|---|---|---|---|
| Generation Maintenance Report (`csv/genmaint/gen_maint_report.csv`) | P-15 | System-wide **aggregate** forecast MW on outage, daily, ~31 days forward. Two columns: `Date, Forecasted Generation Outage (MW)`. | **No** — no unit, no zone, no forced/planned split, and **not archived** (live snapshot overwrites itself, so 2023–2025 cannot be reconstructed). |
| Outage Schedules / Real-Time / Day-Ahead Scheduled/Actual Outages (`csv/os/…`, `csv/schedlineoutages/…`, `csv/realtimelineoutages/…`) | P-14, P-54A/B/C | **Transmission** LINE/TRANSFORMER outages, unit-level, with history and FORCED status. | No — zero generators. |
| 6-Month Bid Data | — | Historical DAM/RT bids & awards released on a 3-month delay with **generator identities MASKED** behind persistent masked IDs. | **No** — no mapping to real units; the masking is by design. |
| Real-Time Fuel Mix, zonal LBMP, load | — | Aggregate/zonal only. | No per-unit availability. |

**No public NYISO DAM posting reveals a named unit's availability, commitment or
outage** — unlike ERCOT's 60-Day DAM Disclosure (named-unit HSL/LSL). Generator
derations/outages are submitted confidentially by Generator Owners under the
Outage Scheduling process (NYISO Manual 29 / OATT outage coordination) and are not
disseminated at unit level. Confirmed by enumerating the full MIS public report
menu and pulling samples 2026-07-22.

## Why CAMPD remains correct here

- CAMPD/CEMS is a **measured physical availability** proxy (rule 13-admissible: a
  unit that stops emitting is offline; regenerates for a forward year), the same
  instrument every CAMPD-ISO uses. Its known blind spot — non-emitting units
  (nuclear refueling, hydro/PS, wind/solar, storage, and downstate units when not
  combusting) — is **not closable with any public NYISO data**, so switching
  sources would not recover it.
- Recommended public supplements (all already available or cheap to add), none of
  which replace CAMPD, only sharpen the non-emitting tail:
  - **NERC GADS** class-average EFORd/availability (unit records are confidential;
    class stats are published) — already in-tree (`nerc-gads-eford-*`).
  - **EIA-860/923** monthly net generation for nuclear-refuel / hydro-derate signal.
  - **NRC daily reactor status** for the NY nuclear fleet (a genuine measured
    unit-level availability source CAMPD cannot see) — candidate future intake if
    the nuclear-outage tail ever gates a keeper.

## Forward note

The only way to obtain a NYISO aggregate generator-outage series going forward is
to **snapshot** `gen_maint_report.csv` daily from today onward (forecast,
system-total). It cannot backfill the 2023–2025 training window and is too coarse
(no unit, no zone) to drive the unit-level derate overlay, so it is not worth
wiring. Recorded here only so a future session does not re-investigate.

## Cross-references

- `docs/handoffs/nyiso-data-asks-2026-07.md` — the standing NYISO data-ask
  register (this determination closes the implicit "native outage feed" line;
  it was never a filed ask because CAMPD already covers it).
- `scripts/data/fetch_caiso_dam_outages.py` — the CAISO instrument this ask asked
  whether to replicate for NYISO (answer: cannot, no NYISO equivalent is public).
- `scripts/data/derive_campd_unit_outages.py` — the frozen NYISO outage source
  that stays in place.
