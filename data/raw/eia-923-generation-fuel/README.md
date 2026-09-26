# eia-923-generation-fuel — raw

EIA Form 923 Schedules 2–5, **Page 1 "Generation and Fuel Data"**, annual totals per
plant × reported prime mover × reported fuel, 2019–2025, every US plant:

`eia923_generation_fuel_2019_2025.csv` — `year, plant_id, plant_state, prime_mover, fuel_type,
total_fuel_mmbtu, elec_fuel_mmbtu, net_generation_mwh` (MMBtu HHV; MWh net).

**Why it is here (R-CAISO-3, 2026-09-25).** This is the owner's own fuel filing. It is independent
of EPA CAMPD CEMS heat input. `scripts/data/derive_campd_cc_heat_rates.py` uses it as the measured
fallback for a combined cycle whose CEMS record the derive's gross-net identity refuses: EIA-923
fuel ÷ EIA-923 net, with numerator and denominator from one filing and one boundary. The case
that prompted it is Pastoria 55656. Its CEMS heat input reads ×1.09 of EIA-923 fuel in every
year from 2020 on (×1.04 in 2019), while its EIA-923 fuel ÷ net holds at 7.04–7.08 MMBtu/MWh.
eGRID, the derive's previous fallback terminal, is CEMS heat input ÷ EIA-923 net, so it
inherits the bias (7.69). See `docs/handoffs/r-caiso-3/`.

**Source:** EIA, public domain. `https://www.eia.gov/electricity/data/eia923/xls/f923_<year>.zip`,
or `.../archive/xls/f923_<year>.zip` for older releases. Workbook
`EIA923_Schedules_2_3_4_5_M_12_<year>_Final*.xlsx`, first sheet, header row 6. Fetched
2026-09-25. 2025 is the "Final" release as published at fetch time.

**Regeneration (the primary recovery route):**
`python3 scripts/data/fetch_eia923_generation_fuel.py` (optionally `--zip-dir <dir>` for
already-downloaded release ZIPs). `SHA256SUMS.txt` records the CSV and the seven source ZIPs as
fetched.
