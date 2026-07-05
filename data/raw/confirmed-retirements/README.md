# Confirmed-retirements registry (raw)

Hand-curated, per-ISO extracts of **binding** retirement instruments — the
retirement analogue of the additions pipeline's U/V/TS construction-committed
statuses. Only confirmed exits (units already offline, or future exits bound by
an enforceable public instrument) belong here. **Announced** retirements
(EIA-860 planned dates, IRP/press announcements) do NOT — they stay with the
economic-retirement screen (`model.capacity.apply_economic_retirements`).

Each ISO's rows live in `<iso>.csv` in the canonical schema
(`data/dictionary/schema/confirmed-retirements.schema.yaml`). The curation
script (`scripts/curate_confirmed_retirements.py`) validates every row against
the EIA-860 fleet spine (plant/generator must exist; `capacity_mw` within 5 % of
nameplate; `exit_year >= 2023`) and writes the clean partition. The consumption
seam is `market_sim.data.confirmed_retirements.load_confirmed_exits`, feeding
`model.capacity.apply_confirmed_exits` — **forecast-mode only**, gated on
`ScenarioConfig.confirmed_exits_enabled` (default OFF).

## Binding instruments, per ISO

| ISO | Binding instrument (confirmation) | Public source to re-query |
|---|---|---|
| PJM | Deactivation request past reliability review with a confirmed date and no RMR; RMR **end** date where an RMR exists | PJM "Generator Deactivations" posting (XLSX) |
| MISO | Attachment Y retirement request **approved** (suspensions excluded — reversible) | MISO generator-retirements / Attachment Y status posting |
| NYISO | Generator Deactivation Notice completed per OATT; state (DEC/PSC) orders | NYISO deactivation-notices posting; Gold Book (announced-grade cross-check) |
| ISO-NE (NEISO) | Retirement / Permanent De-List Bid **cleared** in an FCA; approved Non-Price Retirement Request | ISO-NE retirements & FCA-results postings |
| CAISO | State instruments: SWRCB OTC compliance dates, CPUC/CEC decisions (SB 846 Diablo Canyon) | SWRCB OTC compliance-schedule table; CPUC/CEC dockets |
| ERCOT | Notification of Suspension of Operations (NSO) accepted, RMR review concluded **without** an agreement; permanent suspensions | ERCOT market notices / suspension-retirement notices |
| all | Federal consent decrees & court-approved settlements (EPA/DOJ NSR); dated state statutes (IL CEJA, coal phase-outs); PUC settlement/securitization orders | court dockets, state PUC dockets, statute text |

**Counter-instruments** (RMR/must-run agreements, DOE §202(c) orders,
deactivation-request withdrawals, statute amendments) remove or defer
confirmation. A row hit by one is marked `superseded=true` with its
`superseding_instrument` cited — kept for audit; the loader ignores it and the
unit reverts to the economic screen.

## Status (updated 2026-07-05, second intake pass — all six ISOs now seeded)

- **PJM** — seeded (`pjm.csv`, 10 rows): Rockport 1 (federal NSR consent decree,
  2028) + Rockport 2 (separate Indiana IURC Cause No. 45546 order, 2028 — split
  from a single mis-attributed citation in the first pass), Kincaid 1–2 (IL
  CEJA statute, 2030), Brandon Shores 1–2 + H.A. Wagner 3–4 (`rmr_end`, 2029 —
  a further extension to 2031 is pending, not yet FERC-approved), Eddystone
  3–4 (`superseded` by DOE 202(c) — worked counter-instrument; exit_year
  corrected 2026→2025 in this pass).
- **ERCOT** — seeded (`ercot.csv`, 2 rows): V H Braunig 1–2 (binding NSO,
  effective 2025-03-31 — confirmed by ERCOT's Board declining to RMR them).
  V H Braunig 3 stays held out — the *opposite* of retiring: it's under a
  binding RMR agreement (2025-03 to 2027-03) keeping it in service. Spruce /
  Sommers remain announced-grade (economic screen).
- **MISO** — seeded (`miso.csv`, 4 rows): DTE Monroe 1–4 (Michigan PSC Case
  No. U-21193 settlement — Units 3–4 by 2028, Units 1–2 by 2032). Direct fetch
  of MISO's own Attachment Y posting failed (TLS/access errors); a human with
  browser access should cross-check this posting directly at the next intake
  vintage. Everything else in the ~13.5 GW EIA-860-flagged 2026–2028 coal
  cluster was investigated and held out (announced/IRP-stage/contested/fuel-
  conversion — see `miso.csv` header for the full per-plant list).
- **NYISO** — still `DATA NEEDED` (`nyiso.csv`, 0 rows): every forward-looking
  deactivation notice found (Far Rockaway, Gowanus/Narrows, Pinelawn) has been
  reversed via a NYISO reliability determination (returned to service or
  withdrawn) — see `nyiso.csv` header. Honest zero, not an unresearched gap.
- **NEISO** — seeded (`neiso.csv`, 2 rows): Merrimack Station 1–2 (2024 Clean
  Water Act consent decree, 2028-06 — the plant actually ceased operating
  entirely 2025-09-12, ahead of the decree deadline). The ISO-NE de-list-bid
  tracker's other forward candidates could not be matched to a current
  EIA-860 plant/generator identity (tracker itself flags 2024-02-28 as its
  last update) and were excluded rather than seeded on an unverified match.
- **CAISO** — seeded (`caiso.csv`, 10 rows): AES Alamitos 3–5 / AES Huntington
  Beach 2 / Ormond Beach 1–2 (SWRCB OTC Resolution 2023-0025, 2026-12-31), and
  Diablo Canyon 1–2 (SB 846 + CPUC D.23-12-036, 2029/2030) plus its two
  `superseded` rows carrying the plant's earlier 2016-settlement exit dates —
  the worked `superseded` audit-trail example for this datatype.

**Every row above passed `scripts/curate_confirmed_retirements.py`'s EIA-860
spine cross-check (identity + MW within 5 %) against the real fleet spine.**
All instruments were independently re-verified via web research on
2026-07-05. Two rows had carried an explicit in-row caveat where a specific
docket/decision number could not be independently confirmed via secondary
sources (Rockport 1's civil action number; Diablo Canyon's CPUC decision
number) — both were resolved in a primary-document confirmation pass on
2026-07-05: Rockport 1's citation was checked directly against the filed
Fifth Joint Modification (Case 2:99-cv-01250-EAS-KAJ Doc #438), confirming
Consolidated Cases C2-99-1182/C2-99-1250 and its Paragraph 140 exit date;
Diablo Canyon's D.23-12-036 was checked directly against a CPUC decision in
R.23-01-007 that quotes D.23-12-036 verbatim, confirming the decision number
and both units' authorized-operation end dates. See the `pjm.csv`/`caiso.csv`
row notes for the full citations. Both rows are now on primary-document
footing and neither caveat remains.

**The default-flip to `confirmed_exits_enabled=True` is now unblocked on data
grounds for all six ISOs (five seeded + NYISO's honest zero) and the two
outstanding primary-document caveats have been resolved (2026-07-05) — the
flip has been executed per the owner's sign-off (plan §7).**
