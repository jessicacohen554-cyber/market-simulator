# FF-3D — NYISO ICAP/UCAP pairing (Option B) + first curve-ON probe — 2026-07-18

FF-3D of the forecast program (`docs/forecast-development-plan-2026-07.md` §6).
Owner selected **R5a Option B** (NYCA-wide static proxy —
`docs/handoffs/nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md` §3) and
authorized this session to download the source. Owner also approved flipping
capacity-market clearing ON for every real-capacity-market ISO (all but ERCOT);
this session leaves NYISO **flip-READY** but the production flip itself remains
**FF-2C** (not done here).

**Model: Opus** (core-infrastructure scope — rule 27).

---

## 1. Bottom line

- **Data intake: DONE + pushed** (commit `ee74428`). The NYCA-wide ICAP→UCAP
  translation ("Derate") factor is now on disk, loader-validated, cited to the
  exact NYSRC document + table + vintage.
- **Option-B pairing: IMPLEMENTED + fully unit-tested** (264 capacity/demand-curve
  tests green locally). `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
  = 1 - 0.1321 = 0.8679`; NYISO curve-eligibility block **lifted**.
- **Two pre-existing environment blockers found + handled** so the hindcast can
  run: (a) the capacity-hindcast **harness was broken on `main`** since `c48daca`
  (references 3 `ScenarioConfig` fields that never existed) — fixed; (b) `data/clean`
  is derived + gitignored, so a fresh checkout must regenerate it — regeneration
  was launched.
- **Hindcast pair: specified + pre-registered here; run is the remaining step.**
  The clean-data regeneration is the gating setup cost; the fixed/curve-ON legs
  and their scoring reproduce from the exact commands in §6.

**Grade preview (measured items):** item 1 **Basis → PASS** (the binding blocker
the flip memo §1.3 named is now closed with a *measured* NYCA-wide factor); item 2
**Instrument → PASS (transcription)** unchanged; item 5 **Plumbing → PASS**. Items
3 (Position) + 4 (Skill) are the curve-ON probe's job — pre-registered, not yet
solved (§4, §5).

---

## 2. The number (data intake)

**Source:** NYSRC "NYCA Installed Capacity Requirement for the Period May 2025
through April 2026 — **Technical Appendices**, December 6, 2024" (the appendices
companion to the 2025-2026 IRM Study that set the registry's IRM = 24.4%):
https://www.nysrc.org/wp-content/uploads/2024/12/IRM-Report-Appendices-Final-December-6-2024.pdf

The section the IRM Study Report Body calls "Appendix D, Table D.1.1" is **Appendix
D §D.1.1 "New York Control Area ICAP to UCAP Translation," Table D.2 "NYCA ICAP to
UCAP Translation"** (PDF p.73). Its **"Derate Factor"** column IS the ICAP Manual
§2.5 NYCA translation factor (`1 − Σ fleet UCAP / Σ fleet ICAP`).

**Most-recently-realized NYCA-wide value (2024-2025 capability year): 0.1321.**

The full recent series intaken (`data/raw/capacity-market/demand-curve/nyiso/nyiso.csv`,
`metric=icap_ucap_translation_factor`, `y_unit=fraction`, summer capability period):

| Capability year | EC-approved IRM (ICR%) | Derate factor | UCAP margin cross-check |
|---|---|---|---|
| 2020-2021 | 18.9 (118.9%) | 0.0830 | (1.189)(0.9170)−1 = 9.0% ✓ |
| 2021-2022 | 20.7 (120.7%) | 0.0877 | (1.207)(0.9123)−1 = 10.1% ✓ |
| 2022-2023 | 19.6 (119.6%) | 0.0978 | (1.196)(0.9022)−1 = 7.9% ✓ |
| 2023-2024 | 20.0 (120.0%) | 0.1014 | (1.200)(0.8986)−1 = 7.8% ✓ |
| **2024-2025** | **22.0 (122.0%)** | **0.1321** | (1.220)(0.8679)−1 = **5.9% ✓** |

Reconciliation (all rows, ≤0.1pp): `(1 + EC_IRM) × (1 − derate) − 1` equals the
same study's Table D.1 "NYCA Equivalent UCAP Requirement (%)" (the published
UCAP-basis reserve margin). Independently, Table D.2's `UCAP req MW = ICAP req MW
× (1 − derate)` holds to <1 MW every row. Two independent internal checks +
visual confirmation of the rendered page.

**Rising trend (0.083 → 0.132 over 2020-2021 → 2024-2025)** is the documented
wind-driven effect NYSRC narrates ("the increase in wind resources lowers the
translation factor from required ICAP to required UCAP"). This is the known
weakness of Option B vs the recommended Option A (lagged model-derived): a static
proxy of an intentionally time-varying quantity. Carried forward as the
most-recent realized value, per the owner's Option-B selection.

**Key finding vs the gap register's estimate:** the gap register (§3.10 R5a) put
the correction at "~5-7%, over-pays," derived from the only number RC-0A had —
the **NYC *Locational*** factor of **5.18%**. The true **NYCA-wide** factor is
**13.21%** — ~2.5× larger. So the NYC-as-NYCA proxy (rejected Option C) would have
**under-corrected by more than half**. The requirement was overstated by ~13% on
a UCAP basis (not ~5-7%), so the reserve-position understatement — and the
curve-ON over-payment it would drive — is correspondingly larger. This validates
the adjudication's rejection of Option C on boundary-mismatch grounds with a
measured margin.

Validation was **no-LP** (byte + loader): `curate_capacity_market_demand_curve.py
--isos NYISO` writes 86 rows through the frozen `write_clean` seam and the tidy
vocab check; the `icap_ucap_translation_factor` rows read back byte-identical
(most-recent → ratio 0.8679). An accreditation parameter, **outside the rule-22
quarantine** (it is not a solve-year holdout).

---

## 3. Implementation (Option B — one resolver, rule 19)

NYISO is the **direct MISO analogue**: its thermal fleet is counted at UCAP
(`1 − EFORd`, the registry default — NYISO is intentionally absent from
`THERMAL_ACCREDITATION_BASIS_BY_ISO`), and the ICAP-stated IRM (24.4%) is paired
onto that same UCAP basis by a published ICAP→UCAP ratio. The requirement resolver
already multiplies by `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO.get(iso,
1.0)`, so the pairing is a one-line registry entry — identical machinery to
PJM/MISO — with **no change to the supply side** (rule 19: `thermal_accreditation_fraction`
stays the one resolver; only the requirement side moved).

`resolve_adequacy_requirement_mw(NYISO)` → `firm_peak × (1 + 0.244) × 0.8679`
(NYISO nets no DR, publishes no FPR → the fallback ratio path). This **lowers**
the requirement vs the pre-R5a ratio-1.0 fallback by exactly `0.8679`, raising the
reserve position by `1/0.8679 = +15.2%` and collapsing the curve-ON over-payment.

Files changed (all local, tested; see §7 for push status):

- `src/market_sim/config/constants.py` — the registry entry + eligibility flip +
  3 stale-comment reconciliations. **Exact diff in §8.**
- `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv` — 5 intake rows ✅ pushed.
- `data/dictionary/schema/capacity-market-demand-curve.schema.yaml` — metric +
  `fraction` y_unit ✅ pushed.
- `scripts/lib/capacity_market_demand_curve/__init__.py` — vocab additions ✅ pushed.
- `data/raw/capacity-market/accreditation-filings/nyiso/README.md` — landed note ✅ pushed.
- `tests/test_capacity.py` — `TestNyisoIcapUcapTranslation` (R5a basis-consistency,
  mirrors the PJM R2/R3 pattern: registry↔CSV reconciliation, requirement uses the
  ratio, supply stays UCAP, curve now eligible).
- `tests/test_capacity_demand_curve.py` — updated the 4 tests that encoded NYISO
  *ineligibility* to the new eligible behavior; fixed one over-broad season-detection
  heuristic that my (accurate) `season=summer` intake rows exposed (rule 14: keep the
  accurate input, fix the real bug — a scalar metric should not flip a cap-curve branch).
- `scripts/run_capacity_hindcast.py` — harness bug fix (§5.1).

**Basis-consistency tests (R2/R3 mirror), all green:**
`test_registry_reconciles_with_published_csv` (registry == 1 − most-recent CSV
derate, and every factor is a `fraction` in the 0.05–0.20 band — never the NYC
5.18% Locational number); `test_requirement_uses_translation_ratio`;
`test_pairing_lowers_requirement_vs_ratio_one_fallback`; `test_supply_side_stays_ucap`;
`test_curve_now_eligible`. Full suite: **264 passed** across
`tests/test_capacity.py` + `tests/test_capacity_demand_curve.py` +
`tests/test_curate_capacity_market_demand_curve.py`. (Pre-existing unrelated
failure `test_data_dictionary_sync::test_every_schema_has_a_section` re
`dam-public-bids` confirmed on clean HEAD — not from this change.)

---

## 4. Pre-registered bands (BEFORE the run — never widened)

The scorer's committed band table (`scripts/score_capacity_hindcast.py`
`BANDS`, plan §1.4) is the pre-registration — these are not invented for this
run and a miss is a **root-cause investigation (rules 1/11/14), never a widening**:

| Metric | Band |
|---|---|
| thermal GW retired, total | ±10% |
| thermal GW retired, per-fuel | ±20% |
| retire recall (units >300 MW) | ≥ 0.70 |
| false-retire fraction | ≤ 0.15 |
| retire timing | ≤ 1.5 yr |
| additions GW (wind/solar/gas) | ±15% |
| additions GW (storage) | ±25% |
| tech-mix share | ≤ 5 pp |
| 2025 CO₂ | ±10% |

Plus the flip-gate §2.1 **item-3 Position** criterion (curve-ON leg): the
accredited reserve position is IN the priced region in the year(s) NYISO's real
ICAP market actually priced capacity and OUT (long) when it didn't — scored on
the *corrected* (0.8679-paired) requirement, which is the whole point of R5a.
Both legs also carry I5 (no retire→re-enter) and I13 (no sawtooth).

Scored side-by-side **raw and IS-2020** (RC-0B §c.5 / T-R8): raw grades realized
usefulness vs latest truth; IS-2020 grades forecast skill vs the 2020 information
set. Quoting only the flattering one is scoring abuse.

---

## 5. Hindcast pair — status: SPECIFIED, blocked on clean-data regen

The pair is NYISO fixed (BEFORE) vs curve-ON (AFTER), 2021→2025 realized, solve
years {2021, 2023, 2024, 2025}, **2022 bridged** (evolved, never solved — rule 22),
years **sequential** within each invocation (rule 12). Forecast-validation
dashboard only (never the backcast registry).

### 5.1 Blocker A — capacity-hindcast harness was broken on `main` (FIXED)

Launching the harness immediately errored:
`ScenarioConfig.__init__() got an unexpected keyword argument
'entry_vre_capacity_revenue'`. Root cause (verified, **pre-existing, not from this
task** — neither file is in this task's functional scope): the FF-2A harness
commit `c48daca` added a passthrough for three entry-stack probe arms
(`entry_vre_capacity_revenue`, `entry_rate_limits`, `entry_commissioning_lag`) but
those fields were **never added to `ScenarioConfig`** (`git log -S` finds them in
no `scenarios.py` commit) and have **no runner consumer** — so the harness raised
`TypeError` on *every* capacity hindcast, any ISO, since `c48daca`. Only
`entry_screen_diagnostics` (the 4th arm) actually landed.

**Fix (this session):** stop forwarding the three dead kwargs to `ScenarioConfig`
in `build_config`. All three are default-OFF, so this is **byte-identical to any
solve** — it only removes a passthrough that never worked. The CLI flags +
`build_config` params are retained as inert no-ops until the **FF-2A lane** wires
the `ScenarioConfig` fields + runner hooks as a unit (flagged for that lane).
This unblocks the capacity hindcast for **all** ISOs, not just NYISO.

### 5.2 Blocker B — `data/clean` regeneration (fresh-checkout setup)

`data/clean` is derived + gitignored; a fresh container has none, and
`load_confirmed_exits` (correctly) refuses to silently degrade. Standard setup:
`python scripts/regenerate_clean.py` (runs each `curate_<datatype>.py`). This was
launched in-session and is the gating wall-clock cost before any solve; it is a
one-time environment setup, not a code issue.

### 5.3 Reproduction (exact commands)

```
# 0. one-time setup (fresh checkout): regenerate derived clean data
python scripts/regenerate_clean.py

# 1. fixed (BEFORE) leg — years sequential in-invocation (rule 12)
python scripts/run_capacity_hindcast.py --iso NYISO --fuel-variant realized \
    --out-dir results/hindcast/nyiso-2021-2025-fixed

# 2. curve-ON (AFTER) leg — the R5a first probe (per-ISO gate; scalar stays off)
python scripts/run_capacity_hindcast.py --iso NYISO --fuel-variant realized \
    --capacity-market-clearing \
    --out-dir results/hindcast/nyiso-2021-2025-curve

# (the two invocations may run concurrently — rule-12 ≤2 cap — but on a
#  per-plant multi-zone ISO watch RSS; serialize if >2/3 of RAM is used.)

# 3. score each; 4. register both on the forecast-validation dashboard
python scripts/score_capacity_hindcast.py --bundle results/hindcast/nyiso-2021-2025-fixed
python scripts/score_capacity_hindcast.py --bundle results/hindcast/nyiso-2021-2025-curve
python scripts/register_hindcast.py ...   # forecast-validation namespace ONLY
```

---

## 6. Flip-gate grading (§2.1) — measured where the pairing lets it be measured

| # | Item | Grade | Evidence |
|---|---|---|---|
| 1 | **Basis** | **PASS (newly closed)** | The flip memo §1.3 named this the **binding blocker** (ICAP IRM vs UCAP supply, ratio-1.0 fallback → position understated, curve over-pays). R5a Option B closes it with a **measured** NYCA-wide translation factor (0.1321) reconciled two independent ways to the source. Supply stays UCAP; one requirement resolver (rule 19). The correction is ~13% (not the ~5-7% NYC-proxy estimate). |
| 2 | **Instrument** | **PASS (transcription), sparse years** | Unchanged from RC-1C: per-vintage Pass-1B reproduces 2023/24 + 2024/25 cleared spot + shape to 0%; 2021/22–2022/23 publish no ARV (honest flat anchor); 2025/26 locked. |
| 3 | **Position** | **PRE-REGISTERED, unsolved** | First curve-ON probe (this session's pair). Now measurable on the *correct* basis for the first time (before R5a it would have measured the wrong quantity by ~13%). Bands §4. |
| 4 | **Skill** | **PRE-REGISTERED, unsolved** | Same pair. Recall / false-retire / additions-not-degraded / LOYO on any mechanism-driven verdict flip, scored raw + IS-2020. |
| 5 | **Plumbing** | **PASS** | Per-ISO clearing gate (`capacity_market_clearing_by_iso`) + the curve-eligibility registry both work; NYISO is now `True` in the eligibility registry and prices on its sloped curve under an explicit curve-ON arm (verified in unit tests: short position > net-CONE, long → 0), while the **production clearing default stays OFF** (flip = FF-2C). |

**Honest position:** flipping NYISO in production is still **FF-2C's** owner-gated
step. This session removed the item-1 blocker (the reason the flip memo said "HOLD,
blocked, not re-probe-unblockable") and set NYISO curve-eligible, so the *first*
curve-ON position/skill measurement is now both possible and correctly-based. It
is pre-registered and reproduces from §5.3; it was **not** completed in-session
because the clean-data regeneration + a per-plant 5-zone 4-year × 2-leg solve
exceeded this session's window after the two pre-existing blockers were cleared.

---

## 7. Push status (rule 27 discipline)

Pushed via `mcp__github__push_files` (API-only; never `git push`), fresh branch
off `origin/main` `3abd022`, blob-verified (working-tree diff empty):

- **`ee74428`** — data intake: `nyiso.csv` + schema + curate vocab + README.
  **Blob-verify PASSED** (all 4 byte-identical on origin).

`constants.py` (7281 lines) + the two test files are large; their exact diffs are
recorded in §8 for a disk-reading push mechanism (`push_files` requires full
inline content, and `api.github.com` Data-API is session-blocked here —
"GitHub access is not enabled for this session"). The harness fix is small and
pushable. See §8 for the complete `constants.py` change — the mechanism is fully
recoverable from this doc.

---

## 8. Exact `constants.py` diff (recoverability)

Five edit sites (all cited, rule 5). This is the complete functional + doc change.

**(a) `CAPACITY_CURVE_ELIGIBLE_BY_ISO` — lift the NYISO block:**

```python
    # R5a pairing landed (FF-3D 2026-07-18): NYISO's ICAP-stated IRM is now
    # paired onto the model's UCAP supply basis via the NYCA translation factor
    # (PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"], Option B), so
    # a curve-ON position is measured on the correct basis. Eligibility only
    # ALLOWS the curve when capacity_market_clearing is explicitly enabled; the
    # production clearing default stays OFF (that flip is FF-2C, owner-gated).
    "NYISO": True,          # was: False,  # R5a pairing adjudicated; owner sign-off pending
```

**(b) `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO` — add the entry** (after
the MISO row), with the full citation block prepended (NYCA translation factor =
1 − 0.1321 = 0.8679, NYSRC 2025-2026 IRM Study Technical Appendices Table D.2,
2024-2025 row; reconciled to Table D.1 UCAP margin 5.9%; static-proxy Option B):

```python
    "NYISO": 1.0 - 0.1321,  # 1 - NYCA translation (Derate) factor, CY 2024-2025
```

**(c)** pricing-seam inline comment (`capacity_price_per_firm_mw_yr`),
**(d)** the `CAPACITY_CURVE_ELIGIBLE_BY_ISO` registry preamble, and
**(e)** the `resolve_capacity_curve_eligible` docstring — all three updated from
"NYISO is INELIGIBLE (R5a not owner-signed)" to "every registry ISO is now
eligible; NYISO's block lifted when its R5a pairing landed (FF-3D 2026-07-18)".
(Doc-only; keeps code + comments consistent, rule 5.)

---

## 9. Residuals / handoffs

- **R-A (FF-2A lane):** the capacity-hindcast harness carries three dead
  entry-stack CLI flags/params (`--entry-vre-capacity-revenue`,
  `--entry-rate-limits`, `--entry-commissioning-lag`) whose `ScenarioConfig`
  fields + runner hooks were never landed. This session stopped forwarding them
  (byte-identical); FF-2A should either wire them as a unit or delete the flags
  (rule 26). Until then they are inert no-ops.
- **R-B (this lane):** run the pre-registered hindcast pair (§5.3) and complete
  items 3/4 grading + registration. Nothing about the pairing changes — a missed
  band is a root-cause investigation, never a re-selection of the (published,
  measured) translation factor.
- **Option A remains the recommended long-term target** (lagged model-derived
  translation factor; adjudication §3 "A"): Option B freezes an intentionally
  time-varying quantity. If a forecast-year run drifts materially from the 0.1321
  snapshot, that is the signal to schedule the Option-A architecture session — not
  to re-tune the proxy.

*Produced 2026-07-18 (FF-3D). Data intake pushed + blob-verified (`ee74428`).
Implementation complete + unit-tested locally (264 green). Harness bug fixed.
Hindcast pair pre-registered + reproducible (§5.3); production flip stays FF-2C.
No holdout year solved or scored (rule 22): 2022 bridged, 2019/H1-2026 untouched;
the intaken translation factor is an accreditation parameter, not a solve output.*
