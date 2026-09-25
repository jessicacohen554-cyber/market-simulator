# CHARTER — SPP-80: measure the 2022+ SPP upper-tercile price premium (data intake, zero LP)

Chartered 2026-09-25 by SPP-79 on the owner's "Yes" to: *"the real driver of the dearer upper
tercile from 2022 on is still unmeasured … Want a data-intake lane chartered for that?"*
Parent finding: `docs/handoffs/FINDING-spp-79-c3a-is-a-cancellation-2026-09-25.md`.

## 1. The object, as measured by SPP-79

The real SPP system hub's upper tercile (RT p67–p99, Feb excluded) cleared at a much higher
implied heat rate from 2022 on. The model's did not.

| year | up RT $ | HR / Henry Hub | HR / KS delivered | HR / TX delivered | DA up HR / HH | wind share |
|---|---|---|---|---|---|---|
| 2019 | 32.0 | 12.5 | 10.9 | 13.8 | 13.0 | 28.2 % |
| 2020 | 27.9 | 13.6 | 10.8 | 13.3 | 13.6 | 31.1 % |
| 2021 | 46.4 | 12.3 | 8.8 | 10.1 | 12.1 | 34.3 % |
| 2022 | 88.9 | 13.5 | 12.8 | 14.4 | 14.0 | 37.3 % |
| 2023 | 41.6 | 16.3 | 13.7 | 16.4 | 16.7 | 37.0 % |
| 2024 | 46.1 | 20.6 | 16.0 | 21.7 | 21.3 | 37.6 % |
| 2025 | 47.6 | 13.7 | 11.0 | 15.8 | 13.7 | 36.6 % |

**Already ruled out, do not redo:**
- **An RT uncertainty premium.** The DA upper tercile rose identically, and RT sits *below* DA in
  every year.
- **Regional gas basis.** The rise persists against KS and TX delivered-to-electric-power gas.
- **Wind share alone.** It fits 2019–22 and fails 2025.

## 2. Candidate drivers the intake must separate

1. **Internal congestion.** The benchmark is the SPP *system hub*; the model has two zones. SPP's
   congestion is widely reported to have grown after 2021. Measure the hub vs system-marginal
   spread, and binding-constraint shadow prices, by year.
2. **Offer markup.** The SPP MMU publishes a price–cost markup / competitive-benchmark comparison
   in each annual State of the Market (SOM). If markup rose in 2023–24, the premium is conduct,
   which is the offer-curve object (rule 1 carve-out territory, not a new mechanism).
3. **Scarcity and reserve pricing.** RTBM operating-reserve MCPs and shortage intervals. SPP
   revised its scarcity-pricing design during this window; get the dates from SPP's own filings,
   never from memory.
4. **Supply tightness.** Net load at the p67–p99 hours against available thermal (retirements,
   outage rates). SPP-local inputs already committed cover part of this (EIA-930 SWPP, CAMPD).

## 3. The intake gap (why this is a data lane)

These are committed for **2023–2025 only**:
- `data/raw/spp-binding-constraints/` (RTBM-BC)
- `data/raw/spp-or-mcp/` (RTBM MCP)
- `_validation-source/actual_lmp_hourly_zonal_SPP.parquet` (NORTH/SOUTH hubs)

The comparison years 2019–2022 are missing for all three. `data/raw/spp-lmp-alt/SOURCES.md`
records that SPP's portal (`portal.spp.org/file-browser-api`) answers anonymously over HTTPS, so
the same products should be fetchable for the earlier years.

## 4. Deliverables

1. **2019–2022 extensions** of the three corpora above, fetched from SPP's portal in their
   existing schema, with `SOURCES.md` + `SHA256SUMS.txt` updated. Follow `data-intake` skill
   conventions. Respect the gitignore corpus convention if a payload is bulky: read each corpus
   README first.
2. **SPP MMU State of the Market annual reports, 2019–2024 (2025 if published).** Commit the
   *numbers*, not the PDFs: a small CSV per metric, year × value, with page citations. Metrics:
   markup / competitive-benchmark index, congestion rent, scarcity or shortage intervals, and
   the annual average hub LMP (as a cross-check of our reference parquet).
3. **A FINDING doc** that decomposes the upper-tercile premium by year into congestion, markup,
   reserve/scarcity and residual. Use SPP-79's table as the target. Name which driver owns the
   2022+ rise, at full magnitude, including "none of them" if that is the measurement.
4. **Matrix**: if a driver maps to an existing SPP cell (e.g. a scarcity/ORDC, congestion or
   offer-shape row), add the evidence to `docs/codebase-site/data/mechanism-matrix/SPP.js` without
   changing its verdict. Add a §5.7 queue note in `docs/mechanism-testing-matrix.md`.

## 5. Bounds

- **Zero LP.** No solve, no shard, no `ScenarioConfig` field, nothing under `src/`.
- **A proposed mechanism is a PRECOMMIT for the owner**, never an armed flag. It must pass rule 13
  (forward-reproducible) and rule 1 (structure, not residual). A markup finding routes to the
  offer-curve channel under the rule 1(a)–(e) carve-out, and **multipliers are not re-tuned here**.
- Coupling constraint from SPP-79: a body-price lever breaks the 2023–25 C3a pass unless paired
  with this upper-tercile object. The FINDING states whether the measured driver can carry that
  pairing.
