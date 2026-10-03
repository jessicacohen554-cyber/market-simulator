# F1 — codebase-site follow-ups from D1/D2 (2026-10-03, branch claude/audit-followups-2026-10)

Three items D1 (`D1-site-drift-concept-pages.md`) and D2 (`D2-site-drift-calibration-pages.md`) left unresolved. Surgical edits only; element ids, CSS and animation mechanics preserved. Format: `file: was → now (source)`.

## 1. capacity-evolution.html + js/viz-capacity-flow.js — flowchart on the 0–7 order

- js/viz-capacity-flow.js `STEPS`: six entries (known ret → econ ret → known add → CCS → entry → backstop, numbered 1–6) → eight entries in the spec order 0 confirmed exits, 1 announced retirements, 2 CCS retrofit screen, 3 economic retirement, 4 known additions, 5 economic entry, 6 reserve-margin backstop (default off), 7 dispatch with RPS constraint (src/market_sim/model/capacity_evolution/__init__.py:6-17; CLAUDE.md "Capacity evolution"). Same data shape (`id/label/short/color/icon/description`).
- js/viz-capacity-flow.js badge `.text(i + 1)` / panel `Step ${stepIdx + 1}` → `i` / `Step ${stepIdx}` so the badge matches the spec's 0-based numbering.
- js/viz-capacity-flow.js desktop layout `cols = 3` (hard-coded 3×2 grid) and the row-turn arrow special case `i === 2` → `cols = Math.ceil(n / 2)` and `i === cols - 1`, so the 8-box snake renders 4×2 and the turn arrow lands on the last box of row 0. Mobile (single column) needed no change. Loop-back arrow comment, aria-label ("Six-step" → "Eight-step (0–7)") and idle prompt ("six-step" → "eight-step (0–7) one-pass") updated. `node --check` passes.
- js/viz-capacity-flow.js step-3 description "coal: 1yr, gas-CT: 2yr, gas-CC: 3yr" → "coal 3, gas-CC 3, nuclear 3, gas-CT / gas-ST / oil 2" (src/market_sim/config/scenarios.py:5398-5413 `retirement_years_*`; retirements.py:4001-4008 `_RETIREMENT_YEARS` lookup).
- js/viz-capacity-flow.js step-6 description "planning reserve margin (peak × 1.15)" → firm peak × (1 + PRM_ISO) on the accredited-firm ledger, PRM per ISO 13.75 % ERCOT / 15 % CAISO / 17.8 % PJM / 15.7 % MISO / 24.4 % NYISO / 16 % SPP / 14.4 % NWPP / 26 % SOCO, gas-CT fill, default off (src/market_sim/config/capacity_market.py:2586-2640 `PLANNING_RESERVE_MARGIN_BY_ISO`; retirements.py:1429-1443 `resolve_planning_reserve_margin`, :1894-1899; adequacy.py:805-928 `resolve_reserve_margin_build_enabled` / `apply_reserve_margin_build`, "gas_ct" at :881).
- capacity-evolution.html:218 "a six-step loop" → "an eight-step (0–7) one-pass loop"; :309 "six-step loop" → "0–7 loop". Section id `six-steps` kept (anchor).
- capacity-evolution.html Steps 0–3 card (:270-271) "(peak − firm clean) × 1.15" → un-retires until accredited firm capacity clears firm peak × (1 + PRM_ISO), `PLANNING_RESERVE_MARGIN_BY_ISO` 13.75 % … 26 % (sources above; floor verb retirements.py:2614-2640 `_apply_reliability_floor` docstring: "firm peak × (1 + PRM_iso)" on the accredited ledger).
- capacity-evolution.html Reliability-floor insight box (:393-394) "(peak demand − firm clean capacity) × 1.15" → same correction with the per-ISO list.
- capacity-evolution.html stat card (:446-447) "1.15× / Reliability floor (peak margin)" → "1 + PRM_ISO / Reliability floor (13.75–26 % by ISO)".

Verified, no edit: the CCS claim "≥ 15 years remaining life" is correct — `ccs_retrofit_min_remaining_life: int = 15` (scenarios.py:5816-5818), tested at ccs.py:417-418 `remaining_life < config.ccs_retrofit_min_remaining_life`; payback-vs-life gate ccs.py:580; 3 GW/yr cap `ccs_retrofit_max_gw_per_year = 3.0` (scenarios.py:5814, ccs.py:632); `ccs_retrofit_available_year = 2028` (scenarios.py:5813). The "× 1.15" multiplier does not exist anywhere in capacity_evolution/ or scenarios.py; the floor and backstop share `resolve_adequacy_requirement_mw` = firm peak × (1 + PRM_ISO) × ICAP→UCAP ratio.

## 2. calibration-rubric.html — version history to v3.17

- :323 `RUBRIC_VERSION = 3.4` → `RUBRIC_VERSION = "3.17"` (2026-10-02) (scripts/calibration_verdict.py:670; docs/calibration-determination-rubric.md:3).
- :373 scorecard data note "(illustrative)" → "(illustrative, frozen at rubric_version 2.4 — the live scorer is 3.17 …)" (docs/codebase-site/data/rubric-scorecard-v2.json:3 `_meta.source`, :12 `run_metadata.rubric_version = "2.4"`). The JSON itself is an explicitly illustrative v2.4 excerpt and was not regenerated (same posture as D2). The only other "v2" prose on the page (:505 "The v2 line is the 2026-07-06 re-anchor") is historical and correct.
- :550-551 v3.4 `is-current` + "current" badge removed; thirteen new `ver-item` rows appended in the existing markup pattern — v3.5 (2026-08-25), v3.6 (09-05), v3.7 (09-10), v3.8 (09-13), v3.9 (09-25), v3.10 (09-27), v3.11 (09-30), v3.12 (09-30), v3.13 (09-30), v3.14 / v3.15 / v3.16 / v3.17 (10-02, `is-current` on v3.17). Sources: docs/calibration-determination-rubric.md §9 (:1315-1410 for v3.5, v3.9, v3.14-v3.17; v3.7 at :1022), scripts/calibration_verdict.py genealogy comments :351-662 (v3.5-v3.17, the only place v3.6, v3.8 and v3.10-v3.13 are dated), docs/governance/rule-history.md §23-§27 (:1492-1624).
- :561 source caption `calibration_verdict.py:61–82` → `:162–670` (the genealogy comments now start at :162; the constant is at :670).

## 3. data-completeness.html — SPP / NWPP / SOCO note

Truth: the table rows are the static inline `#dcData` JSON in the page (hand-censused 2026-07-10, six ISOs: grep shows `"iso"` values ERCOT/CAISO/PJM/MISO/NYISO/NEISO only). It is NOT deploy-generated — `scripts/build_manifest.py:185-192` writes `frontend/data/backcast/completeness.js` from `scripts/audit_eia923_completeness.py` parts, which is the EIA-923 vintage flag for the backcast-runs page, not this census; `.github/workflows/deploy-pages.yml` has no completeness step. So "no audited rows" is accurate. The three Phase-0 censuses exist: docs/multi-iso/spp-data-audit.md (SPP-10, 2026-09-06), nwpp-data-audit.md (NWPP-10, 2026-09-13), soco-data-audit.md (SOCO-10, 2026-09-13).

- :368-370 comment → states the rows are the static `#dcData` JSON (not `build_manifest.py`'s completeness.js) and names all three census docs with lane and date.
- :443-445 empty-table message "SPP was registered 2026-09-06 … (the SPP census lives in spp-data-audit.md)" → names SPP, NWPP and SOCO with registration dates and links all three `docs/multi-iso/<iso>-data-audit.md` censuses. No rows fabricated.

## Unresolved

- Transcribing the SPP/NWPP/SOCO censuses into `#dcData` rows is a data-entry task (each audit doc is a multi-section table) — out of this budget; the page now points at the docs precisely.
- D1's remaining items (pipeline/solve.py:60 docstring, lp-core wallclocks) and D2's model-validity.html body rewrite were not in scope here.
