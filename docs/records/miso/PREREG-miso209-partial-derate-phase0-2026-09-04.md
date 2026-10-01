# PREREG miso-209 — the shoulder's COAL-SIDE availability object: phase 0 of the unit-grain partial-derate measurement (`unit_partial_outage_windows`), zero-solve (2026-09-04)

**Session:** miso-209, branch `claude/miso-208-backcast-calibration-bbtzvb`
restarted from `origin/main` `f71031f5` (miso-208's five commits merged; no
drift on this session's files). **Keeper at open:
`2026-09-03-miso-202-unitclip`** — NOT-YET on `{C3a-2025 −12.3845}` alone,
C3c the single ledgered caveat, C6 attested.

**ZERO-SOLVE phase 0.** Rule 22: 2023–2025 only. Committed artifacts, the
production deriver and production loaders only. **Pushed BEFORE the MISO
partial-plateau extract is derived and before any statistic in §3.**

---

## 0. The form, read before it is measured (rule 28(a))

`unit_partial_outage_windows` (default OFF in the keeper) is registered under
the `unit_outage_short_windows` row (MISO cell **K**, for the SHORT window
shape; the partial shape has never been derived for MISO —
`data/raw/campd-partial-outages-MISO.csv` does not exist; PJM's carries 76
rows, NYISO's 0 by construction, its cell I). The deriver
(`scripts/data/derive_campd_unit_outages.py --partial-windows --iso MISO`)
is the production path and its identification is FROZEN (rule 23):

* **coal units only**, when-operable CF ≥ 0.55 (the baseload guard);
* plateau = running days (daily-mean CF > 0.06) whose **7-day centered median
  of the daily-max CF sits below 0.65 × the unit's normal ceiling** (p90 of
  daily max over running days), sustained **≥ 5 days**; `derate_factor` =
  median plateau ceiling / normal ceiling;
* the revealed-availability in-merit filter (a span must overlap ≥ 24 hours
  above the p85 system-load percentile of a centered window) — Jun–Jul
  shoulder days are in-merit, so it does not bite there;
* consumed by the shared accumulator: removes `(1 − derate_factor) ×
  unit_capacity` from the `(plant_code, plant_group)` bin, concurrent units
  summed, per-unit clip, multiplied INTO the armed envelope.

Two consequences are stated now, before the extract exists: (a) the form
sees only DEEP derates (> 35 % of the unit's ceiling, ≥ 5 days) — a coal
unit running a summer at 80 % of its ceiling is invisible to it; (b) it
composes MULTIPLICATIVELY with the statistical forced-outage layer (coal
WEFOR; `coal_drop_pof=True` drops only the planned component) that is
already meant to represent forced derates in expectation, so it is a rule-19
stack unless the statistical layer is netted for the covered units.

## 1. Inputs (read, not re-derived)

* miso-208: 2025 shoulder (351 h, 52 days, gap −43.73) and tail (15 h, −636.86)
  on the model clock (CST); model coal +3.43 GW over EIA-930 measured coal at
  97.7 % of the model's own capability (32.0 of 32.8 GW; CAMPD part-gross
  32.36); MOM unplanned deficit +7.05 GW raw / **4.94 GW feasibility-clipped**
  on the shoulder days, Central 53 %; 2023/2024 raw deficits 1.47 / 1.72 GW.
  Cushion within $20 10.85 GW; lift engine `_miso208_find_the_supply.lift`.
* Armed MISO window extracts: `campd-unit-outages-MISO.csv` (≥ 5-day, 3,482
  COAL rows of 10,445), `campd-unit-outages-short-MISO.csv` (987 COAL rows),
  `campd-unit-outages-maxgen-unitroute-MISO.csv` (2,174 rows, 5 windows).
* Region crosswalk for the MOM comparison (DISCLOSED approximation of MISO's
  LRZ-based operating regions): MISO-West + MISO-Plains → North;
  MISO-Illinois + MISO-Indiana + MISO-East → Central; MISO-South → South.
  Plains straddles North/Central (IA vs MO); reported both ways where it
  matters.

## 2. Pre-conditions (any failure stops the session)

* **N-1** miso-208's populations, gaps and cushion reproduce exactly (same
  code path).
* **N-2** the derived MISO partial file loads through the PRODUCTION consumer
  (`outages.unit_partial_outage_derate_factors(year, iso="MISO", …keeper
  flags…)`) and the probe's own unit-hour accumulation reproduces the
  consumer's bin factors to ≤ 1 % of bin capacity on every shoulder day
  (else the probe reads the loader, never its own arithmetic).
* **N-3** the derived file's row count and coal-only composition are reported
  BEFORE any population statistic; `ST_GAS` / `CC_*` rows = 0 by construction.

## 3. Predictions and decision rules — each against its own population

"Removed MW" = the partial layer's removed capability summed over the coal
bins, per hour; "share" = the miso-208 lift engine's mean lift / |gap|.
**Licensing line (charter): chartered only if W2 lands in [3.4, 7.05] GW on
the shoulder days AND W3 is clean AND W4 ≥ 0.25 AND W5 and W6 pass.**

| # | prediction (2025 unless stated) | conf. | rule |
|---|---|---:|---|
| **W1** | the extract has **80–300** rows over 2023–2025, ALL `COAL`; ≥ 25 distinct coal units qualify; mean `derate_factor` 0.35–0.60 | 0.6 | reported; 0 rows ⇒ the form is inert for MISO exactly as for NYISO (cell I by construction) |
| **W2** | shoulder-day removed MW **0.5–2.0 GW** mean — **BELOW the bracket** [3.4, 7.05]; tail days ≤ 2.0; Central share ≥ 50 % of the removed MW | 0.65 / 0.55 | **mechanism rule: < 3.4 GW ⇒ the frozen form cannot carry the object** (it sees deep plateaus, the object is a shallow, fleet-wide sub-ceiling); REFUSE as chartered. In-bracket ⇒ proceed to W3–W6 |
| **W2b (diagnostic, named not a mechanism)** | the SHALLOW revealed sub-ceiling gap — Σ over qualifying coal units of `max(0, ref − dmax_d) × unit capacity` on the 52 shoulder days, EXCLUDING hours inside any armed window and excluding plateau days — is **3–6 GW** mean | 0.5 | this is the quantity the object would need; reported as the successor's target, with its economic-idling ambiguity stated (a coal unit below ceiling on a $90 day is revealed unavailability only if the unit was in merit — the in-merit condition holds on shoulder days by construction) |
| **W3** | plateau unit-hours overlapping the unit's own armed windows (std / short / maxgen) ≤ 10 %; the coal statistical layer (armed envelope on the coal bins MINUS the three window layers) removes **4–7 GW** of coal on the shoulder days — i.e. the statistical layer is LARGER than the partial layer | 0.7 / 0.6 | rule 19: if the statistical coal removal ≥ the partial layer's MW, the partial layer is additive only under a SUBSTITUTION form (measured replaces statistical for covered units); a stack is refused |
| **W4** | share of the shoulder gap from the W2 MW **< 0.10**; tail < 0.02 | 0.7 | REFUSE at < 0.25 (the tail is reported only) |
| **W5** | 2023 / 2024 shoulder-day removed MW within **0.5–1.5×** of 2025's — the layer is NOT 2025-specific | 0.6 | a layer sized like 2025 in 2023/2024 (where the raw deficits are 1.5–1.7 GW) is a chronic level object, not the 2025 shoulder's; a 2025-only layer would be the surprise |
| **W6** | with the partial layer added to the envelope, capped availability vs the metered coal+gas daily max: **0–2 violation days** on the 52 | 0.6 | any violation day ⇒ the layer removes capability MISO's fleet demonstrably delivered — refuse the day-set that violates |
| **R-208** | miso-208's coal-side excess re-scored on this instrument: model coal CAPABILITY (32.8 GW) minus the partial layer, vs CAMPD coal NET-ADJUSTED (gross-only plants × 0.93): the excess survives at **≥ +2.0 GW** on the shoulder days | 0.6 | a survival < +1 GW would mean miso-208's coal row was a gross/net artifact — reported as a claim that may fail |
| **P9** | **REFUSED at W2 (form too coarse); nothing chartered; no solve.** Successor named: (i) the shallow sub-ceiling measurement (W2b) as the coal-side availability target; (ii) a substitution form vs the statistical coal WEFOR, never a stack | 0.7 | §5 stop rule |

**Signs, pre-committed:** removed MW ≥ 0 by construction; Central share
positive-majority; the statistical layer exceeds the partial layer in every
year; the coal-side excess survives net adjustment; W2b ≥ W2 in every
population.

## 4. Traps

| trap | counter-measurement |
|---|---|
| T1 the deriver's own in-merit filter uses system load, not price | shoulder days are top-quartile load days too (miso-205: load is the dominant driver); report the share of shoulder hours that are high-load under the deriver's own p85 mask |
| T2 CAMPD gross vs net | the detector runs on CF = gross / detect_cap (unit nameplate or observed peak), so the derate_factor is a ratio and gross/net cancels; R-208's coal comparison applies the 0.93 net adjustment to gross-only plants explicitly |
| T3 the model's coal bins vs CAMPD plants | the accumulator's `(plant_code, plant_group)` keying is used verbatim via the production loader (N-2) |
| T4 a plateau that IS the armed window | W3 overlap census at unit-hour grain against all three armed extracts |
| T5 leap year 2024 | fixed non-leap clock everywhere; the deriver's own year clip |
| T6 daily grain vs hourly object | the layer is day-granular by construction; the lift is computed on the shoulder HOURS with the day's removal |
| T7 aggregate agreement ≠ hour-set correctness | every quantity per population; W2b reported per band (p75–90 / p90–95 / p95–99) |

## 5. Stop rule

No lever is chartered and no LP is spent unless W2 lands in the bracket AND
W3 admits an additive form AND W4 ≥ 0.25 AND W5/W6 pass — in which case the
outcome is a re-charter for a single-field A/B (S-0 bit-identical control,
the miso-202 ten-gate scorer), still no solve this session. Otherwise the
FINDING refuses the form, names the successor measurement and the
substitution question, and the queue is re-ordered.

**Rule duties.** Rule 15: zero-solve, nothing registered. Rule 28(b): evidence
appended to `unit_outage_short_windows` (the row carrying the partial shape)
and `campd_outage_windows`; no verdict moves; §5.4 stamp. Rule 28(c): no
field. Rule 25: MISO's shard only; the derived extract is MISO-suffixed. Rule
27: blob-verify after push. Rule 13: the extract is a measured physical
availability input read as a diagnostic; nothing enters a solve.
