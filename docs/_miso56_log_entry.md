## 2026-07-11 — Owner decisions: miso-56 PROMOTED to keeper; PJM G-20b reserve co-opt hold CONFIRMED

**MISO keeper swap (owner-authorized this session):** `2026-07-11-miso-56-measured-scarcity`
promoted, superseding `2026-07-10-miso-54-som-restored`, per the recommendation in the
2026-07-11 miso-56 entry above — supersedes on structural grounding (two measured series
replace two wrong requirement estimates; zero fitted scalars) at an identical-to-marginally-
better score. `keepers.json` updated, `build_status.py` re-run (MISO: NOT-YET, FAIL set
identical to miso-55 as recorded), keeper-auditor pass clean (0 repairs). Retention was
already handled at registration (miso-41-ct-evening + twin displaced).

**PJM G-20b confirmed HELD (owner, this session):** per
`docs/handoffs/owner-decision-briefs-2026-07-08.md` Decision 2, neither `pjm-87`
(`pjm_reserve_pergen_sync`) nor `pjm-88` (`pjm_reserve_pergen_size_split`) is promoted. The
per-gen reserve dual fires in the correct opportunity-cost regime but at $0–10 — below the
$75–200 afternoon residual C3c needs — with verdicts criterion-identical to the flag-off
baseline (and pjm-88 adding a real 2025 CT_PEAKER dispatch distortion). Both stay default-off
probes; the C3c lane needs a different identification, not a re-sweep of these two. Do not
re-open without new measured evidence.

**Keeper-auditor E7 staleness notes surfaced for owner (no action taken):** ERCOT keeper is
one run behind (`2026-07-11-ercot58-joint-ordc-only` is newer) and PJM likewise
(`2026-07-11-pjm-98-cc-mustrun`). Both keeper determinations remain owner calls.
