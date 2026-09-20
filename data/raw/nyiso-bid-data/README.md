# `data/raw/nyiso-bid-data/` — NYISO masked generator bid data (MIS report **P-27**)

**What it is.** NYISO's public archive of masked market-participant bids. One
row per **masked generator × hour × market**, carrying the resource's own
declared operating limits, its full economic bid curve, its commitment costs and
its ancillary-service offers.

**Why it is here.** The nyiso-242 intake charter
(`docs/RESULT-nyiso242-cc-winter-refused-and-the-intake-charter-2026-09-20.md`
§2.5) requires, for the NYISO 2022 price-tail object, a source that states
**AVAILABILITY** rather than **OPERATION** — CAMPD meters what ran, and every
route from "what ran" to "what could have run" passes through dispatch,
commitment and reserve holding. `Upper Oper Limit` is an availability
statement made by the resource itself.

## Provenance

| | |
|---|---|
| publisher | New York Independent System Operator, MIS public reports, **P-27 "NYISO Bid Data"** |
| index page | <http://mis.nyiso.com/public/P-27list.htm> |
| file URL | `https://mis.nyiso.com/public/csv/biddata/<YYYYMM01>biddata_genbids_csv.zip` |
| authentication | none |
| upstream archive | monthly, **1999-11 → present** |
| held here | **2022–2025**, 48 monthly archives, 172 MB |
| fetched | 2026-09-20, session nyiso-243 |

Sibling P-27 products **not** fetched (no current use): `biddata_loadbids`,
`biddata_tccbids`, `biddata_tranbids` (external transactions).

## Layout

    genbids/<YYYYMM01>biddata_genbids_csv.zip    # upstream bytes, verbatim
    genbids/SHA256SUMS.txt                       # tracked identity record

Each zip holds one CSV for the whole month. The upstream archive is stored
**unmodified** — `data/raw` is immutable, and re-serializing would break the
SHA256 identity record.

## Schema (59 columns; the load-bearing ones)

| column | meaning |
|---|---|
| `Masked Gen ID` | stable surrogate resource key — **no published crosswalk to a PTID or plant** |
| `Date Time` | hour stamp, **UTC** (a January file spans `01JAN:05:00 → 31JAN:04:00`; July spans `01JUL:04:00 → 01AUG:03:00`) |
| `Market` | `DAM` (day-ahead) or `HAM` (hour-ahead / RTC, resubmittable ~75 min out) |
| `Upper Oper Limit` | **the availability statement** — MW the resource told the ISO it could produce |
| `Emer Oper Limit` | emergency ceiling |
| `Fixed Min Gen MW` / `Fixed Min Gen Cost` | declared minimum and its cost |
| `Bid Curve Format`, `Dispatch MW1..12`, `Dispatch $/MW1..12` | the 12-block economic offer curve |
| `Self Commit Timestamp1..4`, `Self Commit MW1..4` | self-scheduled blocks |
| `10/30 Min Non-Synch/Spin MW` + costs, `Regulation MW` + costs | ancillary-service offers — the discriminator for "held as reserve, therefore available" |
| `On Dispatch` | `Y`/`N` |
| `Masked Bidder ID` | masked lead participant |

2022 scope: 332 masked gens, 182 masked bidders, ~390 k rows/month.

## Limits — read these before building on it

1. **Masked identity.** No zone, no fuel, no class, no unit name. This corpus
   can key a **fleet- or cohort-level** availability measurement; it **cannot
   key a per-unit derate**. (It is also why CLAUDE.md's "NYISO publishes no
   60-Day-DAM equivalent" stands as written — what NYISO withholds is the *unit
   identity*, not the offer data.)
2. **Offered, not audited.** UOL is what the participant declared, which is the
   right quantity for "what the market believed was available" and is not the
   same as a metered or GADS-verified capability.
3. **Rule 13 `[R-MEASURED]`.** Admissible as a measured market input — the same
   construction regenerates for any year from the same public archive and
   responds to changed conditions. It is inadmissible the moment its magnitude
   is set by a price residual (rules 1 / 13).

## Retention and recovery

Payload **gitignored** (corpus-conversion class,
`docs/bloat-removal-plan-2026-08.md` §4). The tracked record is this README,
`genbids/SHA256SUMS.txt`, and the committed downloader. Recovery is **re-fetch**,
not a git pin:

    python3 scripts/data/fetch_nyiso_bid_data.py --years 2022 2023 2024 2025
    python3 scripts/data/fetch_nyiso_bid_data.py --verify      # recovery check

The source is public and unauthenticated, so re-fetch is reliable; NYISO's MIS
archive reaches back to 1999 and has no stated retention cutoff.

**The recovery route has been EXERCISED, not just asserted** (session nyiso-248,
2026-09-20). The corpus was re-fetched from scratch into an empty container and
**all 48 archives came back byte-identical to the `SHA256SUMS.txt` written at
the original 2026-09-20 intake** — 0 missing, 0 extra, 0 hash mismatches, and
the regenerated record is byte-identical to the committed one. Upstream is
stable and the corpus-conversion class works as designed for this source.

**Use `--verify`, not `--checksums`, to check a recovery.** `--checksums`
**REWRITES** the identity record; only `--verify` compares against it. Until
nyiso-248 this README advertised `--checksums   # verify`, which was the
opposite of what the flag did. Two guards now exist because this bit:
`--verify` (read-only comparison, non-zero exit on drift) and a refusal in
`write_checksums` to **shrink** the record — a partial fetch such as
`--years 2022 --months 1` previously truncated the 48-entry record to one entry
and silently destroyed the only committed statement of what the bytes were.
Override with `--force-checksums` only when the corpus scope really did shrink.

## Consumers

* `scripts/probes/nyiso243_offered_availability.py` — the nyiso-243 kill test
  (`docs/PRECOMMIT-nyiso243-outage-intake-kill-test-2026-09-20.md` §3).
* `scripts/data/derive_nyiso_offer_surface.py` /
  `scripts/data/derive_nyiso_offer_level_dispersion.py` — the offer book and the
  conditional level-dispersion vector
  (`data/raw/_validation-source/nyiso_offer_level_dispersion.json`).
* `scripts/probes/nyiso248_book_daily_regrain.py` — re-measures that vector on a
  **daily** gas series. The derive divides the bid's bottom block by
  `_gas_series`, which nyiso-248 measured to be a **12-value monthly step**, and
  bins its scarcity window on the same array — so that one flat series enters the
  book as both the implied-heat-rate **denominator** and the **conditioner**.
  See `docs/FINDING-nyiso248-the-daily-citygate-is-already-armed-2026-09-20.md`.
