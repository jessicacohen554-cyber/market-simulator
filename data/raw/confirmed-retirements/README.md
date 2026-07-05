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

## Status

- **PJM** — seeded (`pjm.csv`): Rockport 1–2 (consent decree, 2028), Kincaid 1–2
  (IL CEJA statute, 2030), Brandon Shores 1–2 + H.A. Wagner 3–4 (`rmr_end`,
  2029), Eddystone 3–4 (`superseded` by DOE 202(c) — worked counter-instrument).
- **ERCOT** — `DATA NEEDED` (`ercot.csv`): candidates evaluated and held out.
  Spruce/Sommers are announced-grade (economic screen). V H Braunig 3 is held out
  on a representation mismatch — the OA-status ST unit is not in the model fleet
  while plant 3612 is represented only by its OP gas-CT peakers, so a plant-code
  derate would wrongly shrink the peakers (rule 14). Add only after remapping to
  a modeled unit and verifying the RMR end date.
- **MISO** — `DATA NEEDED`: itemize the approved Attachment Y 2026–2028 coal
  cluster (~13.5 GW candidate block) from the public status posting.
- **NYISO** — `DATA NEEDED`: forward deactivation-notice list.
- **NEISO** — `DATA NEEDED`: cleared permanent de-list bids (forward list short;
  Mystic-class exits are already historical).
- **CAISO** — `DATA NEEDED`: SWRCB OTC compliance dates (Alamitos / Huntington
  Beach / Ormond Beach) and Diablo Canyon per SB 846 (2029/2030).

> All seeded instruments predate the 2026-07-05 intake and the model knowledge
> cutoff. **Re-verify every row against the current posting/docket before
> `confirmed_exits_enabled` is flipped on** (open item — plan §7).
