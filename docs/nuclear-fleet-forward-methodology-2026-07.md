# Nuclear fleet forward-lifetime methodology (FF-G5)

**Date:** 2026-07-20 · **Produced by:** FF-G5 [OPUS] (lane L-INP, coordinates
L-CAP) · **Datatype:** `nuclear-license-status`
(`data/raw/nuclear-license-status/`, schema
`data/dictionary/schema/nuclear-license-status.schema.yaml`) · **Design memo +
session record:** `docs/handoffs/ff-g5-nuclear-registry-2026-07.md`.

**Data + design only — no mechanism code, no ScenarioConfig field, no
constants.py value, and zero LP solves in this session** (task scope §3). The
registry is a grounded DATA input plus a read-only loader stub; how a license
expiry / SLR / restart / uprate should *enter the forecast* is the design memo's
subject and is chartered to a separate implementing session.

## 1. Why this exists

2035–2050 clean-firm supply is ungrounded. Mechanism facts (verified against
`src/market_sim/config/constants.py` ~L3527–3535 and
`docs/handoffs/confirmed-retirement-plan-2026-07.md`):

- Announced non-fossil retirement dates are honored only within
  `EIA860_OPERABLE_VINTAGE (2025) + NONFOSSIL_ANNOUNCED_HORIZON_YEARS (5)` — i.e.
  through ~2030. The constants comment explicitly notes speculative 2040–2072 EOL
  placeholders stop force-retiring past the horizon.
- Beyond ~2030 a nuclear unit exits ONLY via the confirmed-retirements registry
  (whose only nuclear rows are Diablo Canyon) or the economic-retirement screen.
- **BLK-9** (`docs/gap-register-2026-07.md` §3.9): the economic screen is
  *inverted* against nuclear in capacity-market ISOs — the flat capacity payment
  clears FOM for every fossil/CCS class (1.26×–4.92×) but leaves nuclear the only
  class below 1.0× (0.60×–0.82×), so the PJM hindcast false-retired 4.1 GW of
  nuclear (100 % false) while real nuclear retirements were zero.

Meanwhile the real forward record — NRC license expirations, subsequent license
renewals (SLR, 60→80 yr), power uprates, and restarts (Palisades 2025/2026;
Crane/TMI-1 ~2027) — is rich and fully public, and **none of it was a model
input**. This registry makes it one. It does **not** by itself fix BLK-9 (that is
the capacity-revenue accreditation chain, owned by L-CAP / BLK-3+BLK-4); §6 of the
design memo reconciles the two so this registry never becomes a patch that hides
the screen inversion.

## 2. Sources (primary only)

| Source | Grounds | URL |
|---|---|---|
| NRC per-reactor **info-finder** pages | per-unit license issued date, current expiry, docket, MWt | `https://www.nrc.gov/info-finder/reactors/<slug>` |
| NRC **Subsequent License Renewal** status list | SLR grant / under-review + entry-to-SLR-period date | [subsequent-license-renewal.html](https://www.nrc.gov/reactors/operating/licensing/renewal/subsequent-license-renewal.html) |
| NRC **Expected Power Uprate** applications | announced (forward) uprates | [expected-applications.html](https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/expected-applications.html) |
| NRC **Approved Power Uprate** applications | historical uprates (already in EIA-860 nameplate) — context | [approved-applications.html](https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/approved-applications.html) |
| Holtec / NRC | Palisades restart (reauthorization July 2025, operations-status 2025-08-25) | holtecinternational.com; NRC info-finder `pali` |
| Constellation / NRC / PJM | Crane (TMI-1) restart (2024-09 announcement, Microsoft PPA, NRC CCEC review) | constellationenergy.com; NRC CCEC restart page |
| CA SB 846 + CPUC D.23-12-036 | Diablo Canyon STATE ceiling (in `confirmed-retirements`, cross-ref only) | see `confirmed-retirements` |

Committed audit snapshots (sha256-pinned in the datatype README): `md/` — the NRC
SLR status list, expected-uprate list, and approved-uprate list as fetched
2026-07-20. Living NRC pages are re-queried by
`scripts/data/fetch_nuclear_license_status.py`.

## 3. Per-ISO unit tables (59 units; the current registry)

Scope: 61 EIA-860 nuclear generator rows fall in the six modeled ISOs' balancing
authorities; **Cooper and Wolf Creek (SPP) are excluded** (not a modeled ISO),
leaving 59. License expiry = current NRC **federal** operating-license expiration
(reflects renewal/SLR granted). Full provenance per unit is in `<iso>.csv`.

### CAISO (2 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| Diablo Canyon | 1 | 6099 | 50-275 | 2044-11-02 | renewed_60 | none |  |  |
| Diablo Canyon | 2 | 6099 | 50-323 | 2045-08-26 | renewed_60 | none |  |  |

### ERCOT (4 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| Comanche Peak | 1 | 6145 | 50-445 | 2050-02-08 | renewed_60 | none |  |  |
| Comanche Peak | 2 | 6145 | 50-446 | 2053-02-02 | renewed_60 | none |  |  |
| South Texas Project | 1 | 6251 | 50-498 | 2047-08-20 | renewed_60 | none |  |  |
| South Texas Project | 2 | 6251 | 50-499 | 2048-12-15 | renewed_60 | none |  |  |

### NEISO (3 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| Millstone | 2 | 566 | 50-336 | 2035-07-31 | renewed_60 | none |  |  |
| Millstone | 3 | 566 | 50-423 | 2045-11-25 | renewed_60 | none |  |  |
| Seabrook | 1 | 6115 | 50-443 | 2050-03-15 | renewed_60 | none |  |  |

### MISO (14 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| Arkansas Nuclear One | 1 | 8055 | 50-313 | 2034-05-20 | renewed_60 | none |  |  |
| Arkansas Nuclear One | 2 | 8055 | 50-368 | 2038-07-17 | renewed_60 | none |  |  |
| Callaway | 1 | 6153 | 50-483 | 2044-10-18 | renewed_60 | none |  |  |
| Clinton Power Station | 1 | 204 | 50-461 | 2027-04-17 | **original** | none |  |  |
| Fermi | 2 | 1729 | 50-341 | 2045-03-20 | renewed_60 | none |  |  |
| Grand Gulf | 1 | 6072 | 50-416 | 2044-11-01 | renewed_60 | none |  |  |
| Monticello | 1 | 1922 | 50-263 | 2050-09-08 | **slr_granted_80** | granted |  |  |
| Palisades | 1 | 1715 | 50-255 | 2031-03-24 | renewed_60 | announced_intent |  | **in_progress 2026** |
| Point Beach | 1 | 4046 | 50-266 | 2050-10-05 | **slr_granted_80** | granted |  |  |
| Point Beach | 2 | 4046 | 50-301 | 2053-03-08 | **slr_granted_80** | granted |  |  |
| Prairie Island | 1 | 1925 | 50-282 | 2033-08-09 | renewed_60 | none |  |  |
| Prairie Island | 2 | 1925 | 50-306 | 2034-10-29 | renewed_60 | none |  |  |
| River Bend | 1 | 6462 | 50-458 | 2045-08-29 | renewed_60 | none |  |  |
| Waterford 3 | 3 | 4270 | 50-382 | 2044-12-18 | renewed_60 | none |  |  |

### NYISO (4 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| James A FitzPatrick | 1 | 6110 | 50-333 | 2034-10-17 | renewed_60 | none |  |  |
| Nine Mile Point | 1 | 2589 | 50-220 | 2029-08-22 | renewed_60 | **under_review** |  |  |
| Nine Mile Point | 2 | 2589 | 50-410 | 2046-10-31 | renewed_60 | none |  |  |
| R E Ginna | 1 | 6122 | 50-244 | 2029-09-18 | renewed_60 | **under_review** |  |  |

### PJM (32 units)
| Plant | U | EIA | Docket | License expiry | Stage | SLR | Uprate | Restart |
|---|---|---|---|---|---|---|---|---|
| Beaver Valley | 1 | 6040 | 50-334 | 2036-01-29 | renewed_60 | none | announced_intent |  |
| Beaver Valley | 2 | 6040 | 50-412 | 2047-05-27 | renewed_60 | none | announced_intent |  |
| Braidwood | 1 | 6022 | 50-456 | 2046-10-17 | renewed_60 | none |  |  |
| Braidwood | 2 | 6022 | 50-457 | 2047-12-18 | renewed_60 | none |  |  |
| Byron | 1 | 6023 | 50-454 | 2044-10-31 | renewed_60 | none |  |  |
| Byron | 2 | 6023 | 50-455 | 2046-11-06 | renewed_60 | none |  |  |
| Calvert Cliffs | 1 | 6011 | 50-317 | 2034-07-31 | renewed_60 | none |  |  |
| Calvert Cliffs | 2 | 6011 | 50-318 | 2036-08-13 | renewed_60 | none |  |  |
| Crane Clean Energy Center | 1 | 8011 | 50-289 | 2034-04-19 | renewed_60 | announced_intent |  | **in_progress 2027** |
| Davis Besse | 1 | 6149 | 50-346 | 2037-04-22 | renewed_60 | none | announced_intent |  |
| Donald C Cook | 1 | 6000 | 50-315 | 2034-10-25 | renewed_60 | none |  |  |
| Donald C Cook | 2 | 6000 | 50-316 | 2037-12-23 | renewed_60 | none |  |  |
| Dresden | 2 | 869 | 50-237 | 2049-12-22 | **slr_granted_80** | granted |  |  |
| Dresden | 3 | 869 | 50-249 | 2051-01-12 | **slr_granted_80** | granted |  |  |
| LaSalle | 1 | 6026 | 50-373 | 2042-04-17 | renewed_60 | none |  |  |
| LaSalle | 2 | 6026 | 50-374 | 2043-12-16 | renewed_60 | none |  |  |
| Limerick | 1 | 6105 | 50-352 | 2044-10-26 | renewed_60 | none |  |  |
| Limerick | 2 | 6105 | 50-353 | 2049-06-22 | renewed_60 | none |  |  |
| North Anna | 1 | 6168 | 50-338 | 2058-04-01 | **slr_granted_80** | granted |  |  |
| North Anna | 2 | 6168 | 50-339 | 2060-08-21 | **slr_granted_80** | granted |  |  |
| PSEG Hope Creek | 1 | 6118 | 50-354 | 2046-04-11 | renewed_60 | none |  |  |
| PSEG Salem | 1 | 2410 | 50-272 | 2036-08-13 | renewed_60 | none | announced_intent |  |
| PSEG Salem | 2 | 2410 | 50-311 | 2040-04-18 | renewed_60 | none | announced_intent |  |
| Peach Bottom | 2 | 3166 | 50-277 | 2053-08-08 | **slr_granted_80** | granted |  |  |
| Peach Bottom | 3 | 3166 | 50-278 | 2054-07-02 | **slr_granted_80** | granted |  |  |
| Perry | 1 | 6020 | 50-440 | 2026-11-07 | **original** | none | announced_intent |  |
| Quad Cities | 1 | 880 | 50-254 | 2032-12-14 | renewed_60 | none |  |  |
| Quad Cities | 2 | 880 | 50-265 | 2032-12-14 | renewed_60 | none |  |  |
| Surry | 1 | 3806 | 50-280 | 2052-05-25 | **slr_granted_80** | granted |  |  |
| Surry | 2 | 3806 | 50-281 | 2053-01-29 | **slr_granted_80** | granted |  |  |
| TalenEnergy Susquehanna | 1 | 6103 | 50-387 | 2042-07-17 | renewed_60 | none |  |  |
| TalenEnergy Susquehanna | 2 | 6103 | 50-388 | 2044-03-23 | renewed_60 | none |  |  |

## 4. SLR-status census

| slr_status | count | units |
|---|---|---|
| **granted** (→ 80-yr life) | 11 | Monticello; Point Beach 1-2; Dresden 2-3; North Anna 1-2; Peach Bottom 2-3; Surry 1-2 |
| **under_review** | 2 | Nine Mile Point 1 (2026-03-25); R.E. Ginna (2026-06-17) |
| **announced_intent** | 2 | Palisades (Holtec, to ~2051); Crane/TMI-1 (Constellation, to 2054) |
| **none** | 44 | all others |

License-stage census: **11 slr_granted_80**, **46 renewed_60**, **2 original**
(Clinton — initial renewal under NRC review; Perry — expiry 2026-11-07, initial
renewal expected). No unit in the six ISOs is retiring on its license clock before
~2030 except by the confirmed-retirements channel (Diablo Canyon SB 846).

**The info-finder lag (honored per rule 5).** For Surry 1-2, North Anna 1-2,
Dresden 2-3, Monticello, and Point Beach 1-2, the per-reactor info-finder page
still displayed the **60-yr** renewed expiry at access even though the NRC SLR
**status list** records the grant. Both are NRC primary sources; the status list
is authoritative for the grant. The registry records the **80-yr** expiry =
"entry-to-SLR-period" (status list) + 20-yr statutory term, cites the SLR issuance
in `slr_instrument`, and flags the lag per unit. Peach Bottom 2-3's info-finder
pages *did* reflect the 80-yr dates (no derivation). Diablo Canyon's info-finder
similarly lagged the 2026 federal renewal (dates from ROD ML26022A077).

## 5. Uprate & restart census

**Announced (forward) uprates** — `uprate_status=announced_intent`, MW **not
published** on the NRC Expected-Uprate list, so `announced_uprate_mw` is blank:
Salem 1-2 (stretch, Q2 2027), Perry 1 (extended, Q3 2029), Beaver Valley 2
(extended, Q3 2030), Beaver Valley 1 (extended, Q3 2031), Davis-Besse (extended,
Q3 2032). Constellation's several "Proprietary" expected-uprate rows are not
attributable to a unit and are excluded (rule 5). Historical uprates (the NRC
approved list) are already in EIA-860 nameplate and are **not** re-recorded — the
modeled fleet is largely already uprated, so forward headroom is modest.

**Restarts** — `restart_status=in_progress`:
- **Palisades** (MISO, 811.8 MW): NRC reauthorized the operating license July 2025
  — the first US restart of a shut-down reactor — and Holtec transitioned it to
  "operations status" 2025-08-25; generation restart targeted 2026 under NRC/INPO
  oversight. Current renewed license expires 2031-03-24; Holtec filed SLR intent
  (~2051) 2024-04-18. EIA-860 status is `OA`.
- **Crane Clean Energy Center** (PJM, 980.8 MW, former TMI-1, docket 50-289):
  Constellation announced the restart 2024-09-20 under a 20-yr Microsoft PPA; NRC
  CCEC restart review in progress (RAI 2025-11-19, response 2026-01-29, draft
  EA/FONSI 2026-06-03); PJM interconnection accelerated approval → target 2027.
  Constellation intends to extend the license to at least 2054.

## 6. Field survey — how other models treat nuclear lifetime

Context for the design memo's mechanism choice (not a source for registry data):

- **EIA AEO / EMM (NEMS).** Historically assumed existing nuclear retires after
  60 years; more recent AEOs assume broad life extension (AEO2013 Reference
  extended most lives "at least through 2040") and now represent the 40→60→80
  SLR framework. AEO2017 assumed ~25 % of unannounced-retirement nuclear capacity
  removed by 2050 as an economic-stress assumption. Assumptions doc:
  [EMM_Assumptions.pdf](https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf);
  background [Today-in-Energy #10991](https://www.eia.gov/todayinenergy/detail.php?id=10991).
- **NREL ReEDS.** Age-based retirement with a nuclear lifetime in the 60–80-yr
  band (deployment-year dependent); NREL decarbonization analyses commonly assume
  an 80-yr life, reflecting the NRC 40→60→80 licensing ladder. ReEDS documentation:
  [fy21osti/78195.pdf](https://docs.nrel.gov/docs/fy21osti/78195.pdf).
- **EPA IPM.** Models existing nuclear with license renewals and honors announced
  retirements; the exact life-extension / SLR assumption should be confirmed
  against the current IPM documentation at the next intake (flagged, not asserted).

**Takeaway for our model.** The field consensus is that a US nuclear unit's
default forward life is its NRC license clock (60 yr, extending to 80 with SLR),
*not* an economic-retirement outcome — which is exactly what BLK-9 shows our
economic screen gets wrong for nuclear. That argues for a license-clock upper
bound on nuclear life (design memo option iii) with the economic screen retained
only as a possible earlier accelerant — never as the *sole* nuclear exit driver.

## 7. Rule-13 admissibility

The registry passes the admissibility test — *could this same quantity be produced
for a forward year from forward drivers, and would it respond to changed
conditions?*

- **Regenerates forward:** every date is an NRC (or state/licensee) instrument
  re-queryable at each intake vintage (the same discipline as the additions
  pipeline's U/V/TS statuses and the confirmed-retirements registry). Nothing is
  fitted to a residual or copied from an observed generation outcome.
- **Responds to changed conditions:** the instrument set itself moves — an SLR
  grant extends a license 20 years, a restart returns a unit, an uprate raises
  capacity, a state statute (SB 846) caps a federal license. The registry's
  `slr_status` / `restart_status` / `uprate_status` columns are exactly those
  responses.

What stays inadmissible (and is absent): pinning a nuclear unit to its observed
CEMS generation, or tuning any date to a capacity/price residual.

## 8. Gaps / MANUAL DOWNLOADS NEEDED

- **NRC Expected SLR Applications list** (URL 404'd this session) — needed to
  populate `announced_intent` fleet-wide beyond the two units independently cited.
- **Constellation "Proprietary" expected uprates** — plant withheld; per-unit
  `announced_uprate_mw` for the Constellation fleet is DATA NEEDED.
- **Per-unit forward-uprate MWt** — the NRC Expected-Uprate page publishes no
  per-unit MW; recorded as `announced_intent` with blank MW until each licensee's
  application specifies the increase.
- **Info-finder refresh** — re-confirm the SLR-granted + Diablo Canyon expiries
  verbatim once NRC updates the lagging per-reactor pages.
- **Clinton / Perry initial (40→60) renewals** — both are on their original
  license with a renewal pending/expected; re-check for the grant date.

## 9. Maintenance rules

- **Re-derive only when source data updates** (rule 25 analogue). A registry row
  changes only when its NRC/state/licensee instrument changes (an SLR granted, a
  restart completed, an uprate approved, a statute amended) — never because a
  forecast residual moved. A re-derivation commit cites the instrument change.
- **Re-query cadence:** at each EIA-860 vintage and whenever an SLR/uprate/restart
  docket advances. Refresh the `md/` snapshots (and their README sha256) in a NEW
  intake commit; never silently edit a row.
- **The confirmed-retirements boundary:** a nuclear unit gains a binding EXIT
  instrument (statute, consent decree, RTO deactivation) → that row lives in
  `confirmed-retirements`, and this registry only cross-references it
  (`confirmed_retirement_ref`). Diablo Canyon is the sole current case.
- **Additivity:** a new ISO or unit is a new/edited `<iso>.csv` row plus a spine
  re-validation — no code change. A new column is a schema-v2 change with a
  data-dictionary re-render.
