# USACE National Inventory of Dams (NID) — NYISO hydro subset

**What.** Per-dam storage, height and identity attributes for the dams that NYISO's
conventional-hydro fleet sits on. Intaken under owner ruling **Q1 "fund the full intake"**
(2026-09-07) on `docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md`, to establish whether a
**pondage duration** — the physical basis for a shortened hydro budget period — can be identified
for the NYISO fleet.

**Source.** U.S. Army Corps of Engineers, National Inventory of Dams, national CSV export:

```
https://nid.sec.usace.army.mil/api/nation/csv
```

* **Data vintage** (the file's own first line): `Data Last Updated: 2026-8-28`
* **Fetched:** 2026-09-07
* **National file:** 92,766 dam rows × 84 fields, 67,284,928 bytes,
  sha256 `561217d7829315b6a353c416011d70eb48dd14c257dd3f85b62470db40f2335a`
* **Licence:** U.S. federal government work — public domain. NID is published by USACE under the
  National Dam Safety Program; no use restriction.
* **Forward availability:** the same endpoint is re-published on a rolling basis (the vintage
  string above is the file's own stamp), so the identical query regenerates for a future year.
  Re-fetch on a newer vintage under rule 23 `[R-FROZEN-DERIVE]` — **never** because a residual
  moved.

**What is committed here.** `nid_nyiso_hydro_dams.csv` — **189 rows × 21 fields**, the subset of
the national file whose `NID ID` is named by an ORNL HILARRI v4 linkage row for one of the 163
plants in NYISO's model hydro fleet. The 67 MB national file is **not** committed (it is a national
dataset far outside this repo's scope, and it is re-fetchable from the URL above).

Regenerate the subset with:

```
curl -sSL "https://nid.sec.usace.army.mil/api/nation/csv" -o nid_nation.csv
# then keep the rows whose "NID ID" appears in HILARRI v4 for the NYISO hydro fleet;
# the join and the retained field list are in scripts/probes/nyiso219_pondage_duration.py
```

## Two traps in this file, both hit and both documented

1. **A `NID ID` names a PROJECT, not a structure, and is NOT unique in the file.** The
   St. Lawrence project `NY00678` carries **seven** rows — the Robert Moses main dam plus six
   dikes — and **all seven repeat the same project storage** (750,000 normal / 803,000 max
   acre-ft). Storage must therefore be taken **once per project** (`max` across its rows), never
   summed, which would multiply it by the structure count. Collapsing with `drop_duplicates`
   instead is also wrong: it keeps an arbitrary first row and silently discards the informative
   one — here it kept "South Forebay Dike" (no hydraulic height) over "Robert Moses -
   St. Lawrence" (81 ft), putting 19.5 % of NYISO hydro MW on a dam-height proxy that did not need
   it. Both errors were made and corrected in this session; the aggregation that is correct is in
   `nyiso219_pondage_duration.py`.

2. **`Hydraulic Height (Ft)` — the field that is actually head — is mostly absent.** It is present
   for only **20.8 %** of the scored NYISO hydro MW. `Dam Height (Ft)` is present for 98.5 % but is
   a **proxy, not head**, and its error runs in **both** directions: for a diversion plant such as
   Robert Moses Niagara — whose water is taken above the falls and dropped through conduits — dam
   height (97 ft) badly *understates* the true powerhouse head, while for a simple impoundment it
   can *overstate* the usable head. Never substitute it silently; label it, and state the direction
   per plant.

## What this file does NOT contain

* **The licensed operating range.** NID's `Normal Storage` is a reservoir volume, not the band a
  licence permits the operator to move between. The usable figure is strictly **smaller**, so any
  pondage duration computed from NID storage is an **upper bound**. Recovering the range would
  require the projects' FERC licence documents, which are not intaken here.
* **Design head or turbine flow.** See trap 2.

## Fields retained

`Dam Name`, `NID ID`, `State`, `County`, `Primary Purpose`, `Purposes`, `Owner Names`,
`Primary Owner Type`, `Year Completed`, `Dam Height (Ft)`, `Hydraulic Height (Ft)`,
`Structural Height (Ft)`, `NID Height (Ft)`, `Normal Storage (Acre-Ft)`, `Max Storage (Acre-Ft)`,
`NID Storage (Acre-Ft)`, `Surface Area (Acres)`, `Drainage Area (Sq Miles)`, `Latitude`,
`Longitude`, `River or Stream Name`.

## Consumers

* `scripts/probes/nyiso219_pondage_duration.py` — the pondage-duration upper bound
  (`results/calibration/_nyiso219_pondage_duration.json`).

**No `src/market_sim/` code reads this file.** It is evidence for a charter, not yet a modelled
input; nothing in the solve path depends on it and no `ScenarioConfig` field consumes it. Promoting
it to a curated `data/clean` datatype is a separate job for whichever session actually builds the
mechanism (the `data-intake` skill's schema-first path).

**Profile note:** `nid` carries no ISO name token, so `configs/data-profiles.yaml` attributes it to
`shared` and every profile hydrates it. At 41 KB that is immaterial.

---

# NWPP hydro subset (lane NWPP-49, 2026-09-23)

`nid_nwpp_hydro_dams.csv` — **231 structure rows / 194 distinct `NID ID`s**, the subset of the
national export whose `NID ID` is named by an ORNL HILARRI v4 linkage row for an NWPP conventional-
hydro plant (EHA FY2024 `Operational`, `BACode` in the 17 NWPP BAs, `CH_MW > 0`). Line 1 keeps the
file's own vintage banner so `scripts/data/build_hydro_pondage.py::load_nid` reads it unchanged.

* **Data vintage:** `Data Last Updated: 2026-9-11` (the same vintage as `nwpp_hydro_cascade_nid.csv`)
* **Fetched:** 2026-09-23 from `https://nid.sec.usace.army.mil/api/nation/csv`
* **National file:** 67,284,945 bytes, sha256
  `6d3b6656dfd62bfc4277ab4a1b4dec3ad06ecdff40b20eed58a351c84467caaf` (not committed; re-fetchable)
* **Fields retained:** exactly the builder's (`Dam Name`, `NID ID`, `State`, `Owner Names`,
  `Primary Purpose`, `Normal Storage (Acre-Ft)`, `Max Storage (Acre-Ft)`, `Hydraulic Height (Ft)`,
  `NID Height (Ft)`, `Surface Area (Acres)`) plus `River or Stream Name`, `Latitude`, `Longitude`
  for identification.

**Reproducibility gate (checked 2026-09-23):** `build_hydro_pondage.py --iso NWPP --nid-csv
data/raw/nid/nid_nwpp_hydro_dams.csv` writes `data/raw/nwpp-hydro/nwpp_hydro_pondage.csv`
**byte-identical** to the build from the full national file.

Consumer: `data/raw/nwpp-hydro/nwpp_hydro_pondage.csv` → `data/hydro.py::load_hydro_pondage`
(only when `ScenarioConfig.hydro_pondage_bound` is armed; it is not armed in any committed NWPP run).
The two traps above (a `NID ID` is a project, not a structure; hydraulic height is often absent) apply
unchanged and are handled by the builder's `groupby("NID ID").max()` and its labelled
`nid_height_proxy` fallback. For NWPP, 11 of 168 plants (175.7 of 31,746.8 MW, 0.6 %) fall back
to the labelled NID-height proxy; the rest carry a hydraulic height.
