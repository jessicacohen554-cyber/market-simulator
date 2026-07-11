# NYISO capacity-market-elcc (ICAP/UCAP conversion factors)

Drop the retrieved unified CSV here as **`nyiso.csv`**.

## Authoritative sources

- NYISO Capacity Accreditation Task Force (CATF) materials:
  https://www.nyiso.com/en/committees (search "Capacity Accreditation Task
  Force")

**STATUS:** `nyiso.csv` committed — two tranches: (1) NYISO's own official
2025-2026 Final Capacity Accreditation Factors (CAFs) per resource class ×
region (ROS/GHI/NYC/LI) — single current-point marginal ratings, no
penetration axis; (2) a genuine multi-point penetration curve (1-9 GW
statewide installed capacity, class-average + marginal) for storage_4hr and
solar from a NY-BEST/Astrapé Consulting study (third-party, commissioned by a
storage trade association, not itself a NYISO output — flagged in
`study_vintage`). No NYISO-adopted penetration curve is publicly available.
See `docs/handoffs/capacity-market-intake-2026-07.md`.
