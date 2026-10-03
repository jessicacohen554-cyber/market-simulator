# FINDING — capx D101: gate-(a) re-key to the 2026-10-02 W0 keepers (2026-10-03)

**Lane:** capx D101 (zero LP, DATA PROFILE: code), desk refresh #69, standing duty Q34.
**Read at:** origin/main `792e55ad` (PR #7085). The charter pinned `d7ff7c20`, a sha that does not
exist on origin; every fact below was re-verified at `792e55ad`.
**Scope:** `frontend/data/forecast/program-status.json` only (derivation stamp). This lane changes
NO verdict, NO FC cell, NO tier, NO leg status and NO `complete` entry. Nothing solved or scored.

## 1. The nine-row keeper table

Board determination = `frontend/data/backcast/status/<ISO>.js` `keeper.determination` (rubric 3.17),
read live, never re-scored. `complete` = `calibration-complete.json` `complete` block (NEISO, PJM only;
NYISO / ERCOT / CAISO / SPP in `withdrawn`; MISO, NWPP, SOCO never held one).

| ISO | program-status keeper before | designated keeper now | board | `complete`? | gate (a) |
|---|---|---|---|---|---|
| ERCOT | 2026-09-30-r-19-eia-923 | 2026-10-02-closeout-l1-coal-fuel | NOT-YET | no (withdrawn) | NOT MET |
| CAISO | 2026-09-25-caiso-r2-cc-gross | 2026-10-02-closeout-caiso-w1-arm2 | NOT-YET | no (withdrawn) | NOT MET |
| PJM | 2026-09-24-pjm-h22-rggi-span | 2026-10-02-w0-pjm-fix2 | NOT-YET | **yes** | NOT MET (literal test MET; disputed, card 1) |
| MISO | 2026-09-28-miso-280-splitremap | 2026-10-02-w0-miso-fix2 | NOT-YET | no (never) | NOT MET |
| NYISO | 2026-09-22-nyiso-hydro3-ror-split | 2026-10-02-w0-nyiso | CALIBRATED | no (withdrawn) | NOT MET (card 2) |
| NEISO | 2026-09-26-neiso-119-anchor-fuelsec | 2026-10-02-w0-neiso | CALIBRATED | **yes** | **MET** |
| SPP | 2026-09-26-spp-85-netload-mask | 2026-10-02-w0-spp107r | NOT-YET | no (withdrawn) | NOT MET |
| NWPP | (no board row) | 2026-10-02-w0-nwpp-fix2 | NOT-YET | no | NOT MET (recorded in `gate_a_provenance`) |
| SOCO | (no board row) | 2026-10-02-w0-soco-fix2 | NOT-YET | no | NOT MET (recorded in `gate_a_provenance`) |

All seven top-level `isos.<ISO>.keeper` fields were stale; each now carries the prior id in a
`keeper_corrected_by` Supersedes chain and a new `gate_a` reading object. The
`gate.a_keeper_marker.detail` leaves were already re-keyed by `promote_keeper.py` on 2026-10-02 and
are byte-unchanged. `isos.CAISO.marker_complete` and `isos.SPP.marker_complete` are re-keyed
`true -> false` to the live `complete` block (their leg detail already read fail on the withdrawn
marker). `gate_a_provenance` is re-stamped (`derived_at_sha 792e55ad`, `derived_at_date 2026-10-03`,
`derived_by` capx gate-(a) re-key lane D101 r#69) with the prior r#66 stamp carried verbatim beneath.

**Charter premises found stale:** MISO and SPP do not read CALIBRATED; both keepers read NOT-YET at
rubric 3.17 (ISO determination covers every registered year). Only NEISO and NYISO read CALIBRATED.

**NWPP / SOCO rows:** the renderer (`docs/codebase-site/forecast-status.html` `isoCard`) null-guards
every FC field, so a row without them would render. They are NOT added because owner ruling Q68
(2026-09-24) adds their rows only after each declares backcast `complete`; both are recorded inside
`gate_a_provenance.derived_by` instead.

## 2. OWNER CARD 1 — PJM marker/board disagreement

> PJM reads `complete` (keeper `2026-10-02-w0-pjm-fix2`, declared 2026-07-31) but NOT-YET on the
> board — withdraw the entry, or does the owner stand on the 2026-07-31 declaration?

Context: the standing Q5 rule (owner r#12, 2026-08-30) says a `complete` marker cannot stand on a
NOT-YET keeper; it has been applied to NYISO four times. The `complete` block is an owner
declaration; this lane surfaces the disagreement and does not edit it. The row's leg (a) `status`
stays `pass` (literal §2.1b(2)(a) test); the new `gate_a.reading` is NOT MET pending the ruling.

## 3. OWNER CARD 2 — CALIBRATED ISOs outside `complete`

> NYISO reads CALIBRATED on the board but is not in `complete` (withdrawn 2026-09-25, ruling R-BC;
> re-entry is "a new explicit owner declaration on a designated keeper that scores CALIBRATED") —
> declare it? (The charter also named MISO and SPP; both read NOT-YET at rubric 3.17, so no
> declaration question arises for them today.)

## 4. Checks run (all exit 0 after the edit)

`scripts/check_registry_payload_parity.py` (9 runs OK) · `scripts/audit_keepers.py` (PASS, 0
failures, 2 warnings) · `scripts/check_forecast_parity.py` (9 postures, 0 unaccounted, 0 errors).
Edited by targeted string edits, never a `json.dumps` round-trip; the file re-parses.
