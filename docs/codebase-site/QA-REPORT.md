# Documentation Site — Final QA Accuracy Audit

**Date:** 2026-06-29
**Scope:** All 10 pages of `docs/codebase-site/`, audited against source code (the
source of truth), the `docs/codebase/*.md` reference docs, and the live config.
**Method:** Each page was audited against its mapped source files; every factual
claim, equation, diagram label, table value, variable/constraint/parameter name,
data file, file reference, and CDN link was verified. Discrepancies were fixed
directly in the HTML / data JSON.

**Result:** 41 discrepancies found and fixed across 9 HTML pages and 3 data JSON
files. All equations now match the code (not just the methodology spec); every
variable/constraint/parameter name was verified; `iso-topologies.json` matches
live `iso_configs.py` (6 ISOs / 32 zones / 38 links); all CDN links resolve
(HTTP 200); all internal links and referenced source files exist.

---

## Summary of discrepancies found & fixed

### mental-model.html  (vs `01-architecture.md`, `runner.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 1 | "solve 8,760 hours for 25 years **in parallel**" | `runner.py` year loop is strictly sequential (`01-architecture.md`; CLAUDE.md rule #11 — concurrent year solves OOM) | Reworded: hours of one year solved as a single LP, then years stepped through **sequentially** |
| 2 | "**For ERCOT**, an optional P2 commitment screen…" | P2 is gated on `config.commitment_enabled` (ISO-agnostic), default off (`runner.py:1195`) | Removed ERCOT-specific attribution; "off by default" |

### data-pipeline.html  (vs `04-data-layer.md`, `fleet.py`, `fuel.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 3 | `_committed` MC = "Base HR × fuel price" | `fleet.py` `heat_rate × committed_mult` | "HR × committed_mult × fuel" |
| 4 | `_econ` MC = "HR × (1 + econ_mult) × fuel" | `fleet.py` base_hr × multiplier (no `1+`) | "HR × econ_mult × fuel" |
| 5 | `_peak` MC = "HR × (1 + peak_mult) × fuel" | `fleet.py:6359` base_hr × peak_mult | "HR × peak_mult × fuel" |
| 6 | Coal sigmoid direction inverted (§2 prose): "low gas → high fuel fraction" and sigmoid attributed to `_sync` | `fuel.py:238–247` passthrough **rises** floor→ceil as gas gets dearer; `_sync` is full SRMC; the economic tranches carry the sigmoid | Rewrote: cheap gas → floor, dear gas → ceil; sigmoid on economic tranches, not `_sync` |
| 7 | Coal sigmoid direction inverted (§4 list): "`_sync` = sigmoid(gas)" | same | Split: `_sync` = fuel_fraction 1.0 (full SRMC); economic tranches = sigmoid |
| 8 | eGRID "2021 data" | `egrid.py` — eGRID 2023 anchors 2023, eGRID 2024 anchors 2024+ | Corrected vintage |
| 9 | `nox_rate` marked **Optional** | `fleet.py:318` required `(n_gen,)` array | Removed "Optional" |

### fleet-offer-curves.html  (vs `binning-methodology.md`, `fleet.py`)
| # | Claim/entry | Source truth | Fix |
|---|---|---|---|
| 10 | `offer-curve-tranches.json` had a duplicate `tranches_by_fuel` key — the second silently overwrote the first, **dropping `coal_prb`** (the fuel the page's dropdown selects) | data-file integrity | Merged the two objects; all 5 fuels now present, each summing to 100% with rising MC |
| — | *Noted, not changed:* §4 coal-sigmoid uses **illustrative** gas midpoints (3.5/3.2/3.4) that diverge from the live ERCOT calibration (`gas_mid=2.85`); page, chart, and data file are mutually self-consistent and explicitly framed as illustrative. Flagged for the team. | | |

### lp-core.html  (vs `02-lp-dispatch.md`, `dispatch.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 11 | VOLL = **$9000**/MWh | `scenarios.py:41` / `dispatch.py` `voll = 5000` | $5000/MWh |
| 12 | Cyclic boundary "SOC[s,0] = SOC[s,T]" | `dispatch.py:1153–1156` — hour 0's t−1 wraps to T−1 | "SOC[s,t−1] wraps to SOC[s,T−1], closing the year-end cycle" |
| 13 | Sparsity "~2.5M cols, ~5M rows, ~15M nz, ~0.2% dense" (more rows than cols is structurally impossible) | `dispatch.py:1925` "~1.8M column count"; rows = n_zones×T + n_storage×T ≪ cols | Rewrote to ~1.8M columns, far fewer rows, well under 1% dense |
| 14 | Threads "default: 4" | `dispatch.py:1920` env var only set if present; else HiGHS automatic | "unset → HiGHS automatic threading" |

### solving-pricing.html  (vs `03-capacity-and-commitment.md`, `commitment.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 15 | Warm-start via `set_hot_start()` passing primal & dual solutions | `dispatch.py:2163–2230` — only cost coeffs change; re-uses prior optimal basis via `getBasis()`/`setBasis()`; no `set_hot_start` exists | Rewrote to getBasis/setBasis dual-simplex warm start |
| 16 | Adequacy backstop "restores the **cheapest** decommitted units until the floor is met" | `commitment.py:808–827` restores **every** decommitted unit (with P1 dispatch) in the short zone to P1 availability — no cheapest-first ordering | "restores every decommitted unit in that zone to its P1 availability" |
| 17 | "P0 solves the full **~200k-variable** LP" | `dispatch.py:1925` "~1.8M column count"; same card cites 8–15 min / ~12 GB plant-level LP | "~1.8M-column LP … large plant-level ISO" (also resolves cross-page inconsistency with lp-core) |

### network.html + iso-topologies.json  (vs `transmission.py`, `iso_configs.py`)
| # | Claim/entry | Source truth | Fix |
|---|---|---|---|
| 18 | Stat card "**38** Total zones" | true zone sum = 32 (38 is the link count) | 32 |
| 19–21 | "**7-ISO**" in meta description, section comment, and `<h2>` | `_ISO_BUILDERS` has **6** ISOs (`iso_configs.py:657`) | "6-ISO" (×3) |
| 22 | Footer: "JSON regenerated by `scripts/extract_iso_topologies.py`" | script does not exist in repo | Reworded to "one-pass serialization of those configs" |
| 23 | `iso-topologies.json` `_meta`: "All **7** ISOs… regenerate with scripts/extract_iso_topologies.py" | 6 ISOs; no such script | "All 6 ISOs… serialized from the live config" |
| — | **Topology diff:** ERCOT 7z/9l, CAISO 4z/4l, MISO 3z/3l, PJM 8z/11l, NYISO 5z/4l, NEISO 5z/7l — all zone names, load shares, link TTCs, bidirectional flags, interface limits, and VOLL **match `iso_configs.py` exactly. No drift.** | | (verified, no change) |

### capacity-evolution.html  (vs `03-capacity-and-commitment.md`, `capacity.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 24 | Step-6 backstop framed as always-on | `capacity.py:1200` gated on `reserve_margin_build_enabled`, default **False** | Added "(default off)" |
| 25 | Retirement margin "for t where price[t] > mc[g,t]" (in-merit gate) | `capacity.py:377–379` sums over **all** hours; the price>mc gate is the new-entry peaker screen only | "summed over all hours t" |
| 26 | Retirement threshold "FOM × multiplier" | `capacity.py:413–414` `FOM × multiplier × pmax` ($-scaled to match $-margin) | "FOM × multiplier × pmax" |
| 27 | Wright's Law: "α = log₂(1 − LR)" (missing −); Solar α=0.276, Li-Ion α=0.371 | `capacity.py:722` `α = −log₂(1 − LR)` → Solar 0.238, Li-Ion 0.340 | Fixed sign and both values |

### learning-curves.json  (data file backing capacity-evolution §4)
| # | Entry | Source truth | Fix |
|---|---|---|---|
| 28–32 | `learning_exponent` fields 0.276/0.224/0.259/0.371/0.383 used the wrong convention | α = −log₂(1−LR): solar 0.238, onshore 0.198, offshore 0.226, Li-4h 0.340, Li-8h 0.349 | Corrected all 5 to match the code (and the now-fixed page) |

### policy-scarcity.html  (vs `05-policy.md`, `policy/*.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 33 | "Wind **and solar** applied as negative MC adders, reducing to $0 or below" | `ira.py:68–70` `wind_mc = −ira_ptc_wind` ($26); `solar_mc = 0.0` (ITC is capex only) | Rewrote: only wind PTC goes negative; solar MC stays $0 |
| 34 | RPS targets table (CAISO 65/85/100, NYISO 45/70/100, NEISO 38/50/100, knots 2026/2030/2040+) | `constants.py:1447` `STATE_RPS_FLOORS`: CAISO 50/60/80/100, NYISO 40/70/100/100, NEISO 30/45/70/80 @ 2026/2030/2040/2045; PJM none; ERCOT 0% | Replaced whole table with actual floors; added `get_rps_target` interpolation note |
| 35 | ORDC second term `LOLP(R_online/2)` (halving the reserve) | `scarcity.py:314` scales the **distribution params** `μ/2, σ/√2`, not the reserve | Corrected eq to `LOLP(R_online; μ/2, σ/√2)` |

### results-calibration.html  (vs `06-results-and-calibration.md`, `results/*.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 36 | Keeper checks list omits average price | `calibration.py:8–19` — four diagnostics include **average price** | Added "average price" |
| 37 | Diagnostics prose silent on grading; implied a "Warning" tier | `calibration.py:35,41–43` — single flat `DEFAULT_TOLERANCE=±5%`, binary PASS/FAIL/SKIPPED, **no WARN** | Added grading mechanics; "no intermediate warning tier" |
| 38 | Summary cards "10 Pass / 2 Warning / 1 Fail / 77%" (and 10+2+1≠14 rows) | regrade under ±5% binary rule → 13 PASS / 1 FAIL of 14 | "13 Pass / 1 Fail / ±5% Tolerance / 93%" |
| 39 | Three rows badged "**Warn**" (gas-CT −3.2%, solar −2.8%, coal CF +3.1%) | all within ±5% → PASS; only P10 (+20.5%) FAILs | Regraded the 3 to **Pass** |
| 40 | "A run becomes a keeper when it passes the **majority** of checks" | `calibration.py:478` `CalibrationReport.passed = all(status != FAIL)` (strict); keeper is a separate human judgment | Clarified report-pass (strict) vs keeper (human, structural-fidelity-first) |

### calibration-scorecard.json  (data file)
| # | Entry | Source truth | Fix |
|---|---|---|---|
| (part of 38–39) | `total_checks=13` (vs 14), `warn_count=2` (vs 3 WARN tokens), `pass_pct 76.9`, WARN tier | binary PASS/FAIL @ ±5% | Regraded to 13 PASS / 1 FAIL / 92.9%; removed WARN tokens; per-check tolerance 5.0 |

### config-reference.html  (vs `08-config-reference.md`, `scenarios.py`)
| # | Claim on page | Source truth | Fix |
|---|---|---|---|
| 41a | PJM reserve margin 15.5% | `constants.PLANNING_RESERVE_MARGIN_BY_ISO` PJM 0.178 | 17.8% |
| 41b | NYISO 20% | 0.244 | 24.4% |
| 41c | NEISO 13.6% | 0.157 | 15.7% |
| 41d | (MISO absent) | 0.179 | Added "MISO 17.9%" |
| 41e | Storage ELCC 4h≈75% / 8h≈85% / 12h≈95% | `constants.STORAGE_ELCC_BY_DURATION` 0.60 / 0.87 / 0.97 | 60% / 87% / 97% (named constant) |
| — | *Verified correct:* all **50 ScenarioConfig fields** in the data-driven table (name, type, default) match `scenarios.py` exactly — incl. `mode`, `commitment_enabled=False`, `storage_capacity_value/degradation=True`, `ccs_retrofit_available_year=2028`, per-fuel retirement thresholds, `voll=5000`, ORDC defaults. | | |

---

## Cross-cutting checks (whole site)

- **CDN links:** every external URL (D3 v7, GSAP 3.12.x + ScrollTrigger, KaTeX 0.16.8/0.16.9) returns **HTTP 200** and is well-formed. No MathJax is used (KaTeX throughout) — no broken math CDN.
- **Internal links:** all `*.html` hrefs point to sibling pages that exist; `/backcast-results.html` is the (gitignored, deploy-built) dashboard, expected.
- **Source-file references:** all `.py` paths/filenames cited on the pages
  (`capacity.py`, `iso_configs.py`, plus 20 bare filenames) resolve to real files
  in the repo.
- **Data JSON validity:** all 15 `data/*.json` files parse; internal consistency
  spot-checked (generation ≤ capacity, monotone price-duration, decreasing ORDC
  penalty, rising-MC tranches, load shares sum to 1.0, revenue components sum to
  totals).

## Items deliberately left unchanged (with rationale)
1. **fleet-offer-curves §4 illustrative coal-sigmoid midpoints (3.5/3.2/3.4).**
   Explicitly framed as illustrative; page, its chart JS, and its data file are
   mutually consistent. Editing only the prose would desync the trio. Flagged for
   the team to optionally reconcile to live calibration constants (`gas_mid=2.85`).
2. **Unused `.badge-status.warn` CSS rule** in results-calibration.html — harmless
   dead style after the WARN-tier removal.
