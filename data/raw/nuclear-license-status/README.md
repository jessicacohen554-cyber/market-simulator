# Nuclear fleet forward-lifetime registry (raw)

Hand-curated, per-ISO extracts of every operating (or restart-pathway) commercial
power reactor **unit** in the six modeled ISOs, with its forward-lifetime drivers:
NRC operating-license expiry + stage, Subsequent License Renewal (SLR) status,
announced power uprates, restart pathway, and a cross-reference to the
`confirmed-retirements` registry where a binding exit instrument exists. This is
the clean-firm-supply grounding for 2030–2050 (FF-G5 / gap-register BLK-9 lane).

Each ISO's rows live in `<iso>.csv` in the canonical schema
(`data/dictionary/schema/nuclear-license-status.schema.yaml`). The curation script
(`scripts/data/curate_nuclear_license_status.py`) validates every row against the
EIA-860 fleet spine (the `(eia_plant_id, unit)` identity must exist; `capacity_mw`
within 5 % of nameplate) and writes the clean partition. The read-only consumption
stub is `market_sim.data.nuclear_license.load_nuclear_license_status`.

**Nothing in the solve path consumes this yet.** FF-G5 shipped the registry as
grounded DATA plus a forward-channel *design memo*
(`docs/handoffs/ff-g5-nuclear-registry-2026-07.md`); the implementing session that
wires a mechanism is chartered separately. Admissibility (rule 13): an NRC license
is an enforceable public instrument with a date that regenerates forward at each
intake vintage and responds to changed conditions (SLR grants, restarts, uprates)
— never an observed generation outcome or a residual-tuned value.

## Scope

61 EIA-860 nuclear generator rows sit in the six modeled ISOs' balancing
authorities; **2 are excluded** (Cooper, Wolf Creek — SPP, not a modeled ISO),
leaving **59 units**: CAISO 2, ERCOT 4, NEISO 3, MISO 14, NYISO 4, PJM 32. One row
per unit (the NRC unit / EIA generator ID). Diablo Canyon 1-2 also appear in
`confirmed-retirements` (SB 846 state exit) — cross-referenced here via
`confirmed_retirement_ref`, **not duplicated**.

## Primary sources (per-source provenance)

| Source | What it grounds | URL |
|---|---|---|
| NRC per-reactor **info-finder** pages | per-unit operating-license issued date, current-license **expiry**, docket, MWt | `https://www.nrc.gov/info-finder/reactors/<slug>` (each unit's `source_url`) |
| NRC **Subsequent License Renewal** status list | SLR grant / under-review status + entry-to-SLR-period date | <https://www.nrc.gov/reactors/operating/licensing/renewal/subsequent-license-renewal.html> |
| NRC **Expected Power Uprate** applications | announced (forward) uprates → `announced_uprate_mw` / `uprate_status` | <https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/expected-applications.html> |
| NRC **Approved Power Uprate** applications | HISTORICAL uprates (already in EIA-860 nameplate) — context only | <https://www.nrc.gov/reactors/operating/licensing/power-uprates/status-power-apps/approved-applications.html> |
| State / licensee instruments | restarts (Holtec Palisades; Constellation Crane/TMI-1), CA SB 846 (Diablo Canyon, via confirmed-retirements) | per-row `restart_instrument` / `retirement_announcement` |

`scripts/data/fetch_nuclear_license_status.py` re-queries the four consolidated NRC
pages and prints their current sha256. Those pages are **living documents** (NRC
updates SLR/uprate status as applications move), so the pinned audit artifacts are
the markdown snapshots under `md/` (below), NOT the live HTML.

### md/ snapshots — sha256 (the pinned audit artifacts)

| File | sha256 | accessed |
|---|---|---|
| `md/nrc-subsequent-license-renewal-status-2026-07-20.md` | `2a13ad34b1d192acc331df1ce4f47e574e6205bb7d907a5fc76047d86d8675cb` | 2026-07-20 |
| `md/nrc-expected-power-uprates-2026-07-20.md` | `cc45fb67dc236031499e62ced74beadab47c5b42d6c81f4bf73c8856d2dc70a6` | 2026-07-20 |
| `md/nrc-approved-power-uprates-2026-07-20.md` | `b4f83cfedfe3b361330a91f3f3bcc7980bda8f9628773a77ddcc028a4db6820b` | 2026-07-20 |

### <iso>.csv — sha256 (the committed registry extracts)

| File | sha256 |
|---|---|
| `caiso.csv` | `7e3594c4e7d98f9c6833212fa3a289594e403c8d86a8961832ce89c00fbe5ed3` |
| `ercot.csv` | `a977d86199128fd3ace647625808f1c4e17847eacd27c8e97231bfefdfe62688` |
| `miso.csv`  | `e2e27da104120b7dd45b9776095eaf584cf14339f254b77145f118aacec40b3b` |
| `neiso.csv` | `5912fa505339cf01057dc3361ee93f7f637e238a424e55005ddacef65714f188` |
| `nyiso.csv` | `99dd2189e7076a7fd9ec3f41ea450ecd86c4bb5bdf5096ec2bce36c01edbd19b` |
| `pjm.csv`   | `f7f06a7304cec77d5b5843924434526b25746971d9ddff1524f7a6cd5e804a94` |

## Per-ISO status (intake 2026-07-20)

- **CAISO** (2 units): Diablo Canyon 1-2. NRC granted 20-yr FEDERAL renewal
  2026-04-02 (ROD ML26022A077 → 2044/2045); CA SB 846 sets an EARLIER state
  ceiling (2029/2030) that governs the exit via `confirmed-retirements`
  (`sb846-diablo-1/-2`). `current_license_expiry` = FEDERAL license per schema.
- **ERCOT** (4): Comanche Peak 1-2, South Texas Project 1-2 — all `renewed_60`,
  expiries late-2040s/2050s. No SLR / uprate / restart / retirement instruments.
- **NEISO** (3): Millstone 2-3, Seabrook 1 — all `renewed_60`. No SLR application
  on file yet.
- **MISO** (14): **SLR granted** Monticello (2024), Point Beach 1-2 (2025);
  **original license** Clinton (initial renewal under NRC review); **restart**
  Palisades (NRC reauthorized 2025, generation target 2026, Holtec; SLR intent
  filed 2024-04-18). Others `renewed_60`.
- **NYISO** (4): FitzPatrick, NMP 1-2, Ginna. **SLR under review** NMP1
  (2026-03-25) and Ginna (2026-06-17) — stage stays `renewed_60` (not granted).
  NMP1 & Ginna licenses expire 2029.
- **PJM** (32): **SLR granted** Peach Bottom 2-3 (2020), Surry 1-2 (2021), North
  Anna 1-2 (2024), Dresden 2-3 (2025); **original license** Perry (expiry
  2026-11-07); **restart** Crane Clean Energy Center / former TMI-1 (target 2027,
  Microsoft PPA). Announced (forward) uprates: Salem 1-2, Perry, Beaver Valley
  1-2, Davis-Besse.

### The info-finder lag (documented, honored per rule 5)

For six SLR-granted units (Surry 1-2, North Anna 1-2, Dresden 2-3) **and**
Monticello / Point Beach 1-2, the per-reactor info-finder page still displayed the
**60-year** renewed expiry at access, even though the NRC SLR **status list**
records the grant. Both are NRC primary sources; the status list is authoritative
for the grant. The registry records the **80-year** `current_license_expiry` =
"entry-to-SLR-period" (from the status list) **+ 20-yr statutory term**, cites the
SLR issuance in `slr_instrument`, and flags the lag in each unit's `notes`. Peach
Bottom 2-3's info-finder pages DID reflect the 80-yr dates (no derivation). Diablo
Canyon's info-finder likewise lagged the 2026 federal renewal (dates from ROD
ML26022A077). A future intake should re-read these pages once NRC refreshes them
and confirm the derived dates verbatim.

## MANUAL DOWNLOADS NEEDED / re-query list (next intake vintage)

- **NRC Expected SLR Applications list** — the fleet-wide announced-SLR-intent
  table (URL returned HTTP 404 this session). Populating `slr_status=announced_intent`
  fleet-wide (beyond Palisades + Crane, the two independently cited here) needs it.
- **Constellation "Proprietary" expected uprates** — several NRC Expected-Uprate
  rows withhold the plant; per-unit `announced_uprate_mw` for the Constellation
  fleet is DATA NEEDED until a de-anonymized filing lands (rule 5 — no unattributed
  assignment).
- **Per-unit forward-uprate MWt** — the Expected-Uprate page publishes no per-unit
  MW; `announced_uprate_mw` is left blank with `uprate_status=announced_intent`
  until each licensee's application specifies the increase.
- **Info-finder refresh** — re-confirm the SLR-granted + Diablo Canyon expiries
  verbatim once NRC updates the lagging per-reactor pages (see the lag note above).
- **Clinton / Perry initial renewals** — both are on their ORIGINAL license with an
  initial (40→60) renewal pending/expected; re-check for the grant date.
