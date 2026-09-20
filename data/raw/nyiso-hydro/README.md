# NYISO conventional-hydro forebay storage (`nyiso_hydro_pondage.csv`)

**What.** Per-plant usable forebay storage in **MWh**, the measured input behind
`ScenarioConfig.hydro_pondage_bound` (lane hydro-1, 2026-09-20). One row per EIA plant id of
NYISO's conventional-hydro (EIA prime mover `HY`) fleet for which a storage figure can be
identified. A plant absent from this file gets **no LP row** and keeps its monthly energy budget
unchanged — never a substituted value (rule 13 `[R-MEASURED]`).

**Built by.** `scripts/data/build_hydro_pondage.py` — re-run it, do not hand-edit:

```
curl -sS -L -o nid_nation.csv https://nid.sec.usace.army.mil/api/nation/csv
uv run --no-sync python3 scripts/data/build_hydro_pondage.py --iso NYISO --nid-csv nid_nation.csv
```

**Sources.** All three committed or publicly re-fetchable, none modified in place:

| source | what it supplies | vintage used |
|---|---|---|
| USACE National Inventory of Dams, national CSV export (`https://nid.sec.usace.army.mil/api/nation/csv`) | `Max Storage (Acre-Ft)`, `Hydraulic Height (Ft)`, `NID Height (Ft)` per dam | `Data Last Updated: 2026-9-11` (67,284,945 bytes) |
| ORNL HILARRI v4 (`data/raw/hilarri/HILARRI_v4.csv`) | plant -> dam linkage (`eha_ptid` -> `nidid`) | committed |
| ORNL EHA FY2024 (`data/raw/ornl-eha/...xlsx`, `Operational`) | BA filter and the EIA plant id | committed |
| `constants.HYDRO_PONDAGE_EXTRA_NID_BY_PLANT` | cited cross-references HILARRI does not carry | in-repo, each with its citation |

The 67 MB national NID file is **not committed** — it is a national dataset far outside this
repo's scope and is re-fetchable from the URL above. U.S. federal government work, public domain.

**Construction — zero fitted constants.** `E = rho g V h`, at turbine efficiency **1.0**.
`V` sums `Max Storage` over the plant's **distinct `NID ID` impoundments** (NID files one row
per *structure* and repeats an impoundment's volume on every dike, so summing rows would multiply
one reservoir several-fold); `h` is `Hydraulic Height` where the dam reports one, else
`NID Height` as the labelled proxy — nyiso-219's committed rule, frozen under rule 23
`[R-FROZEN-DERIVE]` and re-derived only on a new NID vintage, **never because a residual moved**.

**It is deliberately an UPPER bound** (gross impoundment rather than the licensed operating band;
efficiency 1.0), so the LP bound it feeds can only be too **loose**, never too tight. Any binding
observed under it is a lower bound on the true constraint.

**Columns.** `plant_id`, `storage_mwh` (what the LP consumes), `n_impoundments`,
`storage_af`, `head_ft_basis` (`hydraulic` / `nid_height_proxy`), `nid_ids`,
`link_source` (`hilarri` / `registry`), `nameplate_mw`, `pondage_hours` (reported for the
record only).

**Validation.** The derive independently reproduces `docs/FINDING-nyiso219-pondage-duration-2026-09-07.md`
to three figures on NYISO: 72.0 % of fleet MW under 24 h (219: 72.01), 97.5 % under a week
(97.54), 98.3 % under a month (98.31), St. Lawrence 73.04 h (73.07).
