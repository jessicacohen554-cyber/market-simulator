# FINDING — FR-22 gap filing: `nyiso_li_seam_posted_limit_cap` (2026-09-27)

**Filed by** SOCO-79 while it drove its own PR (#6788). `main` went red on `check_forecast_parity.py` (FR-22) when PR #6786 (NYISO-NEXT-6) merged and promoted `2026-09-27-nyisonext6-li-cap-span`:

> FAIL NYISO: nyiso_li_seam_posted_limit_cap is armed in the keeper with no forecast-orchestrator consumer and no registry declaration

**What the field is** (`docs/RESULT-nyiso-next6-li-posted-limit-2026-09-27.md`): the Long Island hourly import cap becomes min(envelope, posted import limit of Neptune + CSC + 1385). It is armed in the NYISO keeper and consumed only in `scripts/run_calibration.py::run_year` (NYISO, backcast). The forecast orchestrator never reads it, so a forecast on the keeper config keeps the envelope-only LI cap.

**Disposition filed: `GAP`**, following the nyiso-232 / nyiso-241 precedent. The RESULT calls the mechanism "backcast only", but it does not state a forecast substitute, and deciding whether it is an evidenced `BACKCAST_ONLY` (for example, the envelope as the forward substitute) or a wire-forward item (posted limits projected forward) is the NYISO desk's call with the forecast desk (owner ruling R-X). This filing does not make that decision. It only records the gap, so FR-22 reports it as filed rather than unaccounted.

Nothing is solved and nothing moves: the registry is read only by `scripts/check_forecast_parity.py`.
