# CAISO-AS — DAM ancillary-service regional requirements (OASIS AS_REQ)

Fetched 2026-07-10 by `scripts/fetch_caiso_oasis.py --datasets asreq --years 2023 2024 2025`
(CAISO OASIS `SingleZip?queryname=AS_REQ&market_run_id=DAM&version=1&anc_type=ALL&anc_region=ALL`,
adaptive ≤25-day windows, resumable). Coverage verified complete: every day 2023-01-01 →
2025-12-31 (1,096 days), 44 window CSVs. **Train years only** (CLAUDE.md rule 22 — no 2022, no
H1-2026).

Content: hourly MW ancillary-service requirement per **AS region** and product, DAM. Key
columns: `ANC_REGION` (`AS_CAISO`, `AS_CAISO_EXP`, `AS_NP26`, `AS_NP26_EXP`, `AS_SP26`,
`AS_SP26_EXP`), `ANC_TYPE` (`SR` spin, `NR` non-spin, `RU`/`RD` regulation, `RMU`/`RMD` on the
EXP region), `XML_DATA_ITEM` (`{SP,NS,RU,RD}_REQ_{MIN,MAX}_MW` — each region×product×hour
carries a MINIMUM row and a MAXIMUM row), `MW`, `OPR_DT`, `OPR_HR` (hour-ending, prevailing
Pacific), `INTERVALSTARTTIME_GMT`.

Semantics (CAISO BPM for Market Operations, AS region constraints): the regional **MINIMUM** is
the must-procure-within-region floor (the locational driver — SP26 ≈ south of Path 26 →
model zones LA_BASIN/SDGE/SP15_rest; NP26 → NP15/ZP26); the regional **MAXIMUM** is the
anti-concentration cap. `AS_CAISO`/`AS_CAISO_EXP` are the system totals (EXP = expanded region
including participating interties). Purpose: the measured requirement series for CAISO
sub-regional reserve families (`docs/handoffs/caiso-locational-as-mechanism-2026-07-10.md`;
caiso-70 FINDING probe-#2 redirect). Immutable raw — never modified in place; curation to
`data/clean/` goes through the data-dictionary contract.
