# ISO-NE capacity-market-elcc (seasonal claimed capability / ELCC accreditation)

Drop the retrieved unified CSV here as **`neiso.csv`**. Use `iso=NEISO`.

## Authoritative sources

- ISO-NE Planning Advisory Committee (PAC) ELCC/accreditation materials:
  https://www.iso-ne.com/committees/planning/planning-advisory-committee

**STATUS:** `neiso.csv` committed — two genuine multi-point penetration
curves, NEITHER an ISO-NE-adopted tariff value (both flagged in
`study_vintage`): (1) a 2022 GE Energy Consulting / NRDC study presented at a
NEPOOL Markets Committee meeting (solar/wind/offshore-wind/storage_4hr,
class_average + marginal, by installed MW, 2028 and 2040 study years); (2) a
2024 E3/Mettetal analysis for MA-DOER/MassCEC (offshore wind + long-duration
storage joint incremental-ELCC surface, 2050 study year). No official
ISO-NE-adopted ELCC/accreditation percentage table exists yet — the Resource
Capacity Accreditation (RCA) reform is still open (CAR-PD accepted by FERC
2026-03-30; CAR-SA expected Q4 2026). See
`docs/handoffs/capacity-market-intake-2026-07.md`.
