# MISO sub-regional demand provenance

`miso_subba_demand_2023-2025.csv` — hourly metered demand (MWh) by MISO
EIA-930 sub-balancing-area, 2023-01-01 .. 2025-12-31.

Source: EIA Hourly Electric Grid Monitor, API v2
`electricity/rto/region-sub-ba-data` (frequency=hourly, parent=MISO).
Pulled 2026-06-22 with the project EIA_API_KEY.

MISO reports six sub-BAs (LRZ groupings):
  0001 = Zone 1            -> region North
  0027 = Zones 2 and 7     -> region Central
  0035 = Zones 3 and 5     -> region Central
  0004 = Zone 4            -> region Central
  0006 = Zone 6            -> region Central
  8910 = Zones 8, 9 and 10 -> region South

Region crosswalk uses MISO's OFFICIAL North/Central/South definition
(North = LRZ 1 only). See docs/multi-iso/miso-data-audit.md for the
recommended load_share and the zone-definition caveat (the model's
MISO-North docstring describes LRZ 1+2+3, which EIA's bundled 0027/0035
sub-BAs cannot cleanly separate).
