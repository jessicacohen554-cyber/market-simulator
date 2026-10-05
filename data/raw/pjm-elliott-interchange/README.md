# pjm-elliott-interchange — PJM tie-line actual and scheduled interchange, 20–28 Dec 2022

**Source.** PJM Data Miner 2 REST API (`https://api.pjm.com/api/v1/<feed>`, public subscription key as in
`scripts/data/fetch_pjm_energy_offers.py`), fetched 2026-10-04.
- `act_sch_interchange` gives hourly `actual_flow`, `sched_flow` and `inadv_flow` per tie (22 ties; **negative =
  export from PJM**).
- `rt_scheduled_interchange` gives hourly `hrly_net_tie_sched` per tie.

Filter: `datetime_beginning_ept=2022-12-20T00:00:00.0 to 2022-12-28T23:59:59.0`, CSV.

| file | rows | sha256 |
|---|---|---|
| `act_sch_interchange_2022-12-20_28.csv` | 4,752 | `690b71cf…0553` |
| `rt_scheduled_interchange_2022-12-20_28.csv` | 4,104 | `d3da66dc…f232` |

**Use.** Zero-LP diagnostic for the Elliott identity (closeout-PJM-w3). It is not a solve input. Scheduled
interchange is a market outcome, and a hard-wired interchange would pin an output (rule 13).

**Clock note.** Against these EPT-stamped tie flows, the EIA-930 per-DIBA file
`eia-930-interchange/PJM interchange hourly.parquet` matches best at a −5 h shift (corr 0.92 vs 0.65 at 0 h), so
its `local_time` column reads as UTC-like for PJM. Flagged for the owner of the EIA-930 interchange loaders. It is
not repaired here.

DATA NEEDED: none.
