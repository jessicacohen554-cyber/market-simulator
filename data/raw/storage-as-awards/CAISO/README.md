# storage-as-awards / CAISO — Daily Energy Storage Report quarterly data

Fetched 2026-07-11 from caiso.com (verified HTTP 200 through the session proxy;
index pages `https://www.caiso.com/library/{2023,2024,2025}-data-for-daily-energy-storage-reports`):

- 2023: `https://www.caiso.com/documents/storage-report-2023q{1..4}.xlsx`
- 2024: `https://www.caiso.com/documents/storage-report-2024q{1..4}.xlsx`
- 2025: `https://www.caiso.com/documents/storage-report-q{1..4}-2025.xlsx`
  (caiso.com flipped the filename pattern in 2025)

Field definitions: `https://www.caiso.com/documents/data-release-and-definitions.pdf`.
Release notice: `https://www.caiso.com/notices/daily-energy-storage-report-for-1-1-23-9-30-24-data-posted`
("system level market awards of energy and ancillary services … posted on a
quarterly basis"; preliminary raw market results, not settlement quality).

Content (`market_output` sheet): `TRADE_DATE | HOUR (1..25, DST-aware
hour-ending, prevailing Pacific) | INTERVAL | MARKET (IFM/RUC/RTPD/RTD) |
RES_TYPE (LESR = battery standalone + co-located, HYBD = hybrid) | TYPE (EN
energy schedule, SOC state of charge, RU/RD/SR/NR AS awards) | VALUE (MW)`.
The `bid_stack` sheet (charge/discharge bid volume by price range) is retained
but not curated.

Curation (`scripts/curate_storage_as_awards.py` →
`scripts/lib/storage_as_awards/caiso.py`) keeps the RU/RD/SR/NR award rows for
IFM (hourly, → market "DAM") and RTPD (15-min, hourly-averaged → "RTM"), both
resource classes, onto `data/dictionary/schema/storage-as-awards.schema.yaml`.

Cross-validation: DA battery (LESR) award means reproduce the DMM-published
averages — ~1,040 MW (2023) / ~1,500 MW (2024) average hourly battery AS
procurement, and the 69 % (2023) / ~84 % (2024) battery share of regulation —
to within ~1 % (DMM 2023 Annual Report on Market Issues & Performance ch. 11,
Jul 29 2024; DMM 2024 Annual Report ch. 12, Aug 7 2025; DMM 2023/2024 Special
Reports on Battery Storage).

Train years only (2023–2025, CLAUDE.md rule 22). Q1-2026 file publishes on the
same quarterly cadence (library page not yet posted as of 2026-07-11) — the
series regenerates forward. Immutable raw — never modified in place; curation
to `data/clean/` goes through the data-dictionary contract.

DATA NEEDED: none for 2023–2025. Add 2026 quarterly files when the ISO's
holdout/forward windows are authorized (rule 22).

## Payloads UNTRACKED at tip (BLOAT-S2, 2026-08-17)

The 12 quarterly xlsx are **gitignored** since the Stage-2 (a)-only untrack
(O2 grant, `docs/DECISION-CARD-bloat3-stage2-charter-2026-08-16.md`; evidence
pass `docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §1 — solve reads
the clean seam only, the `caiso_storage_as_reservation` overlay is default-off
/ probe-inert / in no keeper, and no CI or test opens the xlsx). This README
and `SHA256SUMS.txt` (identity record of the removed bytes) stay tracked.

**Recovery is re-fetch ONLY** (story (a); pins are dead — no history route):
the URL table above, **re-verified live 2026-08-17** (HTTP 206 on both
filename patterns: `storage-report-2023q1.xlsx`, `storage-report-q1-2025.xlsx`)
through the session proxy. One command per file:

    curl -fLO https://www.caiso.com/documents/storage-report-<slug>.xlsx

Re-fetch BEFORE running `scripts/data/curate_storage_as_awards.py` (clean
`storage-as-awards` rebuild — absent raw is a soft `[skip]`, and a solve with
the reservation flag armed then hard-errors at `read_clean`) or
`scripts/data/derive_caiso_charge_allocation.py` (loud `FileNotFoundError`;
its committed output `data/raw/reference/caiso-charge-allocation-profile.csv`
remains tracked, so solves using the charge-allocation schedule are
unaffected). Verify against `SHA256SUMS.txt` after fetching.
