# MISO capacity-market-demand-curve (seasonal PRA reliability-based demand curve)

Drop the retrieved unified CSV here as **`miso.csv`**. MISO's demand curve is
seasonal from Planning Year 2025-26 onward (summer/fall/winter/spring) — the
only ISO in this registry whose `season` column is populated. Note the season
for each row's curve in `source_page` if the CSV's own `season` column isn't
present.

- **metric:** `net_cone` (native alias `cone` — MISO calls it Cost of New
  Entry), `curve_point` (native alias `rbdc_point` — Reliability-Based Demand
  Curve).
- **delivery_year:** MISO Planning Year label, e.g. "2025-2026".
- **area:** Local Resource Zone (LRZ 1-10) if MISO publishes zonal curves,
  else blank for a MISO-wide row.
- **y_unit:** MISO publishes PRA prices in $/MW-day.

## Pre-RBDC era (PY2009-10 through PY2024-25): a VERTICAL curve, capped at CONE — not VOLL, not sloped

Before Planning Year 2025-26, MISO's PRA did **not** clear against a sloped
demand curve at all. From the Auction's inception in the 2009/2010 Planning
Year through PY2024-25, MISO used a **vertical (flat) demand curve**: for each
Local Resource Zone (and, once the seasonal construct began PY2023-24, each
season), MISO fixed a single reserve-requirement quantity (the zonal Reserve
Requirement, derived from the system-wide Planning Reserve Margin), and the
Auction Clearing Price was whatever price cleared supply against *that one
fixed quantity* — a single point, not a curve with multiple (x, y) pairs.
Mechanically this collapsed to two regimes: price near $0 when the zone had
even a small supply surplus (supply beyond the Reserve Requirement could not
clear at all), or price at/near the zone's **Cost of New Entry (CONE)** when
the zone was short. There was never a published intermediate price for an
intermediate reserve position — that is precisely what the RBDC reform added.

**The pre-RBDC ceiling was CONE, not VOLL.** The task-framing question of "what
VOLL figure capped the curve" turns out to have no answer, because VOLL is a
*different* MISO Tariff parameter that never touched the PRA. VOLL
($3,500/MWh from 2009 — set at the launch of the Ancillary Services Market —
until MISO's 2025 reform raised it to $10,000/MWh) serves four functions, and
all four are scoped to MISO's **Day-Ahead and Real-Time energy and operating-
reserve markets**: the LMP price cap, the administrative price during MISO-
directed load-shedding, the reference point at the top of the Operating
Reserve Demand Curve (ORDC), and the Emergency Demand Response offer cap
(MISO, "Scarcity Pricing White Paper: Value of Lost Load and Operating Reserve
Demand Curve," 2024-04-18, pp.7-9 — "The VOLL presently serves four functions
in MISO's Day-Ahead and Real-Time markets"). The *capacity*-market ceiling was
always CONE: "MISO... set[s] an artificially high Auction Clearing Price at or
near the Cost of New Entry (CONE) if there is any shortfall of capacity"
(FERC, *Midcontinent Indep. Sys. Operator, Inc.*, 187 FERC ¶ 61,202, Docket
No. ER23-2977-000 et al., issued 2024-06-27, p.3). The same order confirms the
regime dates and the RBDC's start: "MISO has used a vertical demand curve...
since the Auction's inception in the 2009/2010 Planning Year" (p.1) and MISO's
filing sought to "implement a downward-sloping Reliability Based Demand Curve
(RBDC)... beginning with the 2025/2026 Planning Year" (p.1), replacing the
vertical curve.

**This is why `miso.csv` carries no `curve_point` rows for PY2009-10 through
PY2024-25** (concretely, this file's coverage starts at PY2021-22): there is
no sloped curve to digitize for those years without fabricating structure
that MISO never published or used. What *is* recorded for each pre-RBDC year
is exactly what actually governed the auction — the zonal/LRZ **CONE** (the
ceiling price a shortfall zone cleared at) and the **Planning Reserve Margin
(%)** (which sized the vertical line's fixed quantity) — both as `gross_cone`
and `irm` scalar rows, `season` blank (pre-seasonal-construct PRM was a single
annual %, only becoming seasonal from PY2023-24). The Independent Market
Monitor's own retrospective estimate of what a sloped curve *would* have
produced in this era is a useful gauge of how much the vertical design
suppressed prices: "in the 2019/2020, 2020/2021, and 2021/2022 Planning
Years, an efficient Auction Clearing Price would have ranged from just over
$100/MW-day in 2019/2020 to $175/MW-day in 2020/2021, whereas the actual
Auction Clearing Price for those Planning Years in all but one Zone was less
than $7/MW-day" (187 FERC ¶ 61,202 at p.5, citing the Market Monitor's
affidavit) — consistent with this file's PY2021-22 clearing-price history
column (not itself transcribed here; see `capacity-market-auction-price`)
showing $5.00 or less in ten of eleven zones that year, while CONE sat near
$230-267/MW-day.

## Authoritative sources

- MISO Resource Adequacy hub: https://www.misoenergy.org/planning/resource-adequacy/
- MISO Planning Resource Auction results/parameters: search "MISO Planning
  Resource Auction results [planning year]" on misoenergy.org
- FERC eLibrary docket for MISO's reliability-based demand curve filing:
  https://elibrary.ferc.gov (search "MISO demand curve"; Docket No.
  ER23-2977, order 187 FERC ¶ 61,202)

**STATUS:** `miso.csv` committed — gross CONE (Annual) by LRZ 1-10 + ERZs,
regional Net CONE (North/Central + South), seasonal CONE by System/subregion ×
4 seasons, the 8 labeled RBDC clearing-intersection points (subregion ×
season), and Planning Reserve Margin (%) by season for PY2023-24 through
PY2025-26 — all from the PY2025-26 PRA Results Posting + the RASC Net-CONE
update. MISO's reliability-based demand curve (RBDC) began PY2025-26; the full
continuous curve (beyond the one labeled clearing point per chart) is not
published as a data table, only as chart images — the labeled intersection is
the only exact point available. A more granular per-zone-per-season PRMR (MW)
breakdown exists in the source but was not transcribed at this pass (season-
level % IRM was kept instead).

**2026-07-15 pass** extended the file both backward and forward from that
base, all pre-RBDC/RBDC-transition years, no `curve_point` rows added except
where noted:

- **PY2021-22 and PY2022-23 (new)** — pre-RBDC vertical-curve years, previously
  entirely absent from this file. Zonal `gross_cone` (LRZ 1-10 + ERZs, $/MW-day,
  each year's own PRA Results Posting) plus one annual `irm` row per year (no
  seasonal breakdown existed yet) from a later report's "Historic PRM Trend"
  chart. Both years' PRA Results Postings returned HTTP 403 directly from
  `cdn.misoenergy.org` (consistent with the prior intake's documented block);
  retrieved instead via state-PSC docket mirrors that reproduce MISO's
  original posting verbatim (SC PSC Docket 2021-88-E for PY2021-22; Missouri
  PSC EFIS #304507, "Schedule MM-D5," for PY2022-23) — both primary-document
  reproductions, not secondary commentary.
- **PY2023-24 and PY2024-25 (backfilled)** — the `irm` rows already present
  came from the PY2025-26 report's retrospective history table; this pass
  added each year's own-year `gross_cone` (Annual, $/MW-yr, LRZ 1-10 + ERZs)
  read directly from that year's own PRA Results Posting.
- **PY2026-27 (new, partial)** — the actual PRA Results Posting (which would
  carry the RBDC `curve_point` chart intersections and seasonal net_cone, on
  the same pattern as PY2025-26) returned HTTP 403 from `cdn.misoenergy.org`
  and could not be located via any alternate mirror this pass — still
  outstanding. In its place, two other primary MISO/FERC documents supplied
  real (non-curve) PY2026-27 parameters: `gross_cone` **and**, uniquely for
  this year, `net_cone` **by individual LRZ** (not just by System/subregion)
  from MISO's FERC Docket No. ER26-139-000 CONE/Net CONE filing (filed
  2025-10-15); and system-wide seasonal `irm` (Summer 7.9%, Fall 11.6%, Winter
  18.9%, Spring 23.4%) from the PY2026-27 LOLE Study Report's Table 1-1 — a
  pre-auction estimate, explicitly flagged in that row's `vintage` as not yet
  the finalized post-auction PRMR.

See `docs/handoffs/capacity-market-intake-2026-07.md` for the original intake
session (including its "MANUAL DOWNLOADS NEEDED" precedent for the
PY2026-27/2022-23/2020-21 `cdn.misoenergy.org` HTTP 403 block referenced
above).
