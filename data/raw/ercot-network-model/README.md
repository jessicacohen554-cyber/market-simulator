# ercot-network-model — raw (committed)

ERCOT MIS **NP4-160-SG "Settlement Points List and Electrical Buses Mapping"**
(`reportTypeId=10008`), the structural network crosswalks ERCOT publishes.
Members are written as their **exact published bytes** — ERCOT's Terms of Use
§5 permits redistribution "provided that the contents are not modified"
(`docs/data-licensing.md` §3), so the fetcher does not round-trip them through
a parser. `VERSION.json` carries the document stamp plus a sha256 per member.

| File | Rows | What it maps |
|---|---|---|
| `Settlement_Points_*.csv` | 19,287 | **the station→area crosswalk**: `ELECTRICAL_BUS`, `SUBSTATION`, `SETTLEMENT_LOAD_ZONE`, `RESOURCE_NODE`, `HUB`, `VOLTAGE_LEVEL`, `PSSE_BUS_NAME/NUMBER` |
| `Resource_Node_to_Unit_*.csv` | 1,624 | **the generator-side spine**: `RESOURCE_NODE` → `UNIT_SUBSTATION` + `UNIT_NAME` |
| `NOIE_Mapping_*.csv` | 817 | physical load → NOIE → substation → electrical bus |
| `CCP_Resource_Names_*.csv` | 68 | combined-cycle logical resource names |
| `Hub_Name_AND_DC_Ties_*.csv` | 11 | hub and DC-tie name list |

## Why it is here

ERCOT lever-queue **item 7** (WP-B nodal curtailment layer) is blocked on a
*station→area crosswalk that does not exist in-repo*, and **item 8 part (c)**
wants a CT resource→plant crosswalk. This report is ERCOT's own published
answer to the ERCOT half of both.

Measured against the CT fleet census
(`scripts/probes/ercot160_ct_target_population.py`), joining a SCED
`Resource Name` to `UNIT_SUBSTATION + "_" + UNIT_NAME`:

* **186 of 191 CT resources resolve to a substation** (97.4 %); a direct match
  on `RESOURCE_NODE` resolves only 15, so the reconstruction is the join that
  works.
* **all 50 of those substations carry a `SETTLEMENT_LOAD_ZONE`** (100 %).

So resource → substation → load zone is now available from published data.
What is still a judgement step is **substation → EIA plant code**; this file
does not carry EIA identifiers and cannot be made to.

## Vintage limit — read before concluding anything about a backcast year

MIS retention for NP4-160-SG is **~31 days** (`misDisplayDuration_i: 31`; 3
versions listed when fetched). The free path serves only the **current**
network-model version — **there is no 2023 / 2024 / 2025 vintage to fetch, and
there never will be on this path.** That is precisely why this directory is
committed rather than gitignored: an un-committed vintage is lost permanently,
unlike the re-fetchable bulk sources.

Substation→zone assignments are structural and change slowly, but a resource
node commissioned or retired between a backcast year and the fetched vintage
will not line up. **Any consumer must report its own match rate against its
target year** rather than assume the coverage measured above carries back.

## Regeneration

```bash
python scripts/data/fetch_ercot_settlement_point_mapping.py --list-only
python scripts/data/fetch_ercot_settlement_point_mapping.py
```

Re-running replaces the files with the newest listed version — filenames carry
ERCOT's own version stamp, so a new vintage lands beside the old one rather
than silently overwriting a different date's mapping.

## Licensing

ERCOT MIS — `docs/data-licensing.md` §3 (redistributable under ERCOT ToU §5,
same product family as `../ercot/` and `../ercot-AS/`).
