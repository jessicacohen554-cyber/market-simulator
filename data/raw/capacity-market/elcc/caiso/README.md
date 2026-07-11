# CAISO capacity-market-elcc (NQC / CPUC-commissioned ELCC studies)

Drop the retrieved unified CSV here as **`caiso.csv`**.

## Authoritative sources

- CPUC Resource Adequacy proceeding ELCC studies (E3-authored):
  https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-power-procurement/long-term-procurement-planning/resource-adequacy-homepage

**STATUS:** `caiso.csv` committed — a genuine multi-point incremental-ELCC
penetration curve (by MW tranche/vintage year, 2023-2028) for solar, wind (CA
in-state / WY / NM out-of-state — all mapped to `wind`, distinguished only via
`source_page`, a known key-granularity limitation), wind_offshore, and storage
by duration (4/6/8hr), from the CPUC-commissioned E3/Astrapé "Incremental
ELCC Study" (2023-01 update of the 2021-10 study) filed in the IRP/LTPP
proceeding. This is the CPUC/CAISO NQC methodology's own basis. See
`docs/handoffs/capacity-market-intake-2026-07.md`.
