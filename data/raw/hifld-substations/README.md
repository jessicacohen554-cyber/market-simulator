# HIFLD Electric Substations — Texas subset (validation source)

- Source: HIFLD (Homeland Infrastructure Foundation-Level Data) "Electric
  Substations", public ArcGIS feature service
  services5.arcgis.com/HDRa0B57OVrv2E1q/.../Electric_Substations/FeatureServer/0
  (STATE='TX', 4,939 features), downloaded 2026-07-07.
- File: `hifld_substations_TX.parquet` — NAME, CITY, COUNTY, COUNTYFIPS,
  LATITUDE, LONGITUDE, MAX_VOLT, MIN_VOLT.
- Role: INDEPENDENT geographic cross-validation of the ERCOT SPL
  SUBSTATION -> SETTLEMENT_LOAD_ZONE crosswalk (see ../ercot-settlement-points).
  Named substations only (~1,433) are matchable to ERCOT codes; used to confirm
  LZ_WEST precision=1.00 vs coordinate geography. NOT the primary crosswalk
  (ERCOT SPL is), because HIFLD's TX set is 71% UNKNOWN placeholders and
  ERCOT's cryptic codes fuzzy-match at low coverage.
