# fuel-forward-benchmarks — raw

Near-term natural-gas forward **benchmarks** for the FF-G2 fuel-forward
triangulation (`docs/fuel-forward-methodology-2026-07.md`, 2026-07-20). These
are **context only — NEVER fit targets** (CLAUDE.md rule 1): they let the doc
compare the model's AEO2026 annual Henry Hub path against two independent
near-term references. Nothing in `constants.py` reads this directory; no solve
or score consumes it.

## Why this exists

The model's forecast gas price is the AEO2026 annual Henry Hub trajectory
(`HENRY_HUB_TRAJECTORIES`, refreshed FF-G2). The AEO is a **long-horizon
fundamentals** projection; the standard commercial practice triangulates the
near term (12-36 months) against **exchange futures** and the **STEO** (EIA's
short-horizon, market/futures-informed outlook). This datatype snapshots those
two references so the near-term reconciliation is auditable and reproducible,
not asserted.

## Files (landed)

| File | Source | Fetch |
|---|---|---|
| `steo_henry_hub.part00.csv`, `.part01.csv` | EIA Short-Term Energy Outlook (July 2026 vintage), Henry Hub spot forecast — annual `NGHHUUS` (**nominal** $/MMBtu) + monthly `NGHHMCF` ($/mcf) | `scripts/data/fetch_fuel_forward_benchmarks.py` (EIA API v2 `steo` route) |
| `nymex_hh_futures_eia_free.csv` | EIA free NYMEX Henry Hub futures contracts 1-4 (`RNGC1..RNGC4`) | same script (EIA API v2 `natural-gas/pri/fut`) — **STALE**, see below |

**On-disk layout note:** the fetch script writes a single
`steo_henry_hub.csv`; it is committed as header-repeating numbered parts
(`steo_henry_hub.part00.csv`, `.part01.csv`) because the git-API push path caps
individual file-content size — same convention as `data/raw/eia-aeo/`. The
parts concatenate byte-identically to the single file; a re-fetch writes the
single file again.

### sha256 (committed parts)

```
1cee74f2b11d3881031d87a85426388514adffde3833b40fad47bccaa834aa44  steo_henry_hub.part00.csv
b3d39a36025e1a0933fe57b1169fa6ba8fe133b676f3634cd1d2a8fa19748424  steo_henry_hub.part01.csv
950b0024d1a16c6f495747e04d527f7e3b0969b6837c5cb96f277ce3b79f6ad1  nymex_hh_futures_eia_free.csv
```

Regenerate + re-pin: `python scripts/data/fetch_fuel_forward_benchmarks.py`
then `sha256sum data/raw/fuel-forward-benchmarks/*.csv` (the STEO series is
revised monthly, so a later fetch will legitimately change the hash — update
the table and the fetch date in the doc when it does).

## Key near-term values (as-of July 2026 STEO)

STEO annual Henry Hub spot (nominal $/MMBtu): **2025 = 3.53, 2026 = 3.67,
2027 = 3.49** (horizon ends 2027). Historical anchors match reality (2023 =
2.54, 2024 = 2.19). The Jan-2026 monthly print ($8.02/mcf) is a realized
cold-snap actual the monthly series carries, not a forecast — use the annual
figures for the AEO comparison. Full markdown snapshot: `md/steo-henry-hub-snapshot.md`.

## MANUAL DOWNLOADS NEEDED (bot-walled — never guessed, rule 5)

| Item | Why manual | Where |
|---|---|---|
| **Current NYMEX Henry Hub futures strip (full multi-year curve, CME settlements)** | The free EIA futures feed (`RNGC1..RNGC4`) stopped updating on the open API — the latest print it returns is **2024-04-05** (RNGC1 $1.785, RNGC2 $2.010, RNGC3 $2.339, RNGC4 $2.437/MMBtu; recorded in `nymex_hh_futures_eia_free.csv` so the staleness is auditable). The *current* full strip (contracts out ~10+ years, needed to build calendar-year strips comparable to the AEO annual path) is published by CME behind a bot-wall / data licence and cannot be fetched from this environment. | CME Henry Hub settlements: <https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.settlements.html> · EIA republished futures page: <https://www.eia.gov/dnav/ng/ng_pri_fut_s1_d.htm> |

To land the current strip: manually download the CME daily settlements (or the
EIA futures page prints), save as `nymex_hh_strip_<YYYY-MM-DD>.csv` here,
compute per-calendar-year strips (average of that year's 12 monthly
settlements), add the sha256 to the table above, and record the as-of date in
the methodology doc's near-term triangulation table. Until then the doc uses
the STEO as the market-informed near-term reference and flags the NYMEX strip
as an open manual pull — it is context, never a fit target regardless.

## Authoritative sources

- EIA STEO: <https://www.eia.gov/outlooks/steo/> (natural gas section:
  <https://www.eia.gov/outlooks/steo/report/natgas.php>). July 2026 release.
- EIA API v2 docs: <https://www.eia.gov/opendata/documentation.php>.
- CME NYMEX Henry Hub (NG) contract:
  <https://www.cmegroup.com/markets/energy/natural-gas/natural-gas.html>.

## Not covered

- Locational basis forwards (Waha, Algonquin, etc.) — the model's delivered
  basis adders are grounded separately (F923 realized basis; FF-G2 doc §5).
- Coal/oil forward strips — no liquid multi-year exchange curve is used; the
  AEO2026 paths are the sole forward source (FF-G2 doc §4).
