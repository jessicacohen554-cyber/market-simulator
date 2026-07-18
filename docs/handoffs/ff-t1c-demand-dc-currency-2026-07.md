# FF-1C — Demand & DC forward-input currency (+ hydro) — findings

**Session.** FF-1C of `docs/forecast-development-plan-2026-07.md` §6 (Wave 1, L-INP
lane), executing the FF-0D audit's §7.1 fix list
(`docs/handoffs/ff-inputs-currency-audit-2026-07.md`). Scope boundary honoured: this
session touched **only** the demand/DC constants (`DEMAND_GROWTH_RATES`,
`DATACENTER_ADDITIONS_MW`, `DATACENTER_ZONE_SHARE`) and their tests/citations. It did
**not** touch `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` / policy (FF-1E) or
`data/hydro.py` (the hydro fix already landed — §1).

**Rules.** Source-driven re-derivation only (rules 5/13/23): every changed number is
cited to an FF-0D-confirmed published forecast; no value is a residual fit. No default
behaviour flipped (`datacenter_load_path` stays `"off"`). Forecast-mode work only — no
holdout/quarantine contact (rule 22).

---

## 0. Headline

1. **The hydro forecast-fleet drop (FF-0D §5.3, the one outright bug) was ALREADY FIXED
   on main** — commit `66c55fd` clamps `shape_year = min(year, EIA923_LATEST_FINAL_VINTAGE)`
   in `build_hydro_fleet`'s forecast branch, with a passing regression test
   (`test_build_hydro_fleet_forecast_shape_year_clamped`). Verified green (11 passed);
   nothing to do.
2. **MISO's demand rate is now wired** — it was absent from `DEMAND_GROWTH_RATES`, so every
   MISO forecast fell back to the **1%/yr scalar** default while MISO publishes the steepest
   DC-driven outlook in the country (FF-0D §1.2, "single largest demand gap"). Added a MISO
   block from the Sept-2025 LTLF (~3.5%/2.5% near/long). Demand at 2035 rises **+18.7%** vs
   the old fallback — the marquee change.
3. **CAISO and PJM mids re-centered** on their 2025/2026 forecasts (CAISO CED 2025-2045
   → +5.2% by 2030; PJM 2026 Load Forecast → +3.4% by 2035). **ERCOT/NYISO/NEISO held** —
   their headline figures are either the *speculative DC-inclusive envelope* (ERCOT LTLF3)
   or locked inside XLSX/PDF tables (NYISO GB, NEISO CELT) that FF-0D flagged as
   manual-download-blocked (M4/M5/M6); refreshing them needs those tables, not a guess.
4. **The growth×DC double-count cannot be structurally dissolved this pass, and the BAU
   posture stays `off` (owner decision).** The §3.5 organic-ex-DC re-derivation does not
   close on the current *envelope* DC anchors: the ERCOT mid block is ≈**275 TWh/yr**
   (37 GW × 0.85 CF × 8760 h) against only ~**90 TWh** of near-term growth to relocate —
   the block is the *speculative interconnection queue*, not the *expected realized DC*
   the growth rate embeds. Reconciling them needs the realized-DC-by-year tables (FF-0D
   M3–M7). So `mid`/`high` DC paths stay inadmissible and the block ships populated-but-off.

---

## 1. Hydro forecast-fleet drop — already fixed (item 2, no-op)

FF-0D §5.3 chartered clamping the forecast budget-shape year. That fix is on `origin/main`
(`66c55fd`, "hydro: clamp forecast budget-shape year to newest final EIA-923 census"):

```python
# build_hydro_fleet, forecast_budget branch (data/hydro.py:638-640)
from market_sim.data.eia923 import EIA923_LATEST_FINAL_VINTAGE
shape_year = min(year, EIA923_LATEST_FINAL_VINTAGE)   # = 2024
```

`test_build_hydro_fleet_forecast_shape_year_clamped` (forecast 2030 & 2025 → clamped to
2024, non-empty fleet) passes; backcast paths untouched. **Verified: 11 hydro tests pass.**
No further work needed — the FF-1C charter's P0 hydro item is closed by prior work.

---

## 2. Demand-rate refresh (`DEMAND_GROWTH_RATES`)

**What moved (mids re-centered on cited 2025/2026 forecasts):**

| ISO | mid near | mid long | source | status |
|---|---|---|---|---|
| **MISO** *(new)* | 0.010→**0.035** | 0.010→**0.025** | MISO 2025 LTLF (Sept 2025): peak 121→~163 GW 2025-2035 = +35% = 3.1%/yr blended; DC front-loaded 8–14 GW 2026-27 | **added** (was 1%/yr scalar fallback) |
| **CAISO** | 0.015→**0.028** | 0.010→**0.018** | CEC CED 2025-2045: 1-in-2 peak 46.1→52.9 GW 2025-2030 = 2.78%/yr; 52.9→~68 GW 2040 = 2.54%/yr (long tempered to 0.018 for post-2040) | refreshed |
| **PJM** | 0.035→**0.036** | 0.018→**0.024** | PJM 2026 Load Forecast (2026-01-14): 10-yr +3.6%/yr, 20-yr +2.4%/yr | refreshed |
| **ERCOT** | 0.05 *(held)* | 0.025 *(held)* | 2025 LTLF3 headline (139 GW by 2030) is the speculative LFL envelope, not a clean organic CAGR — needs LTLF3 MW-by-year (M5) | held + re-cited |
| **NYISO** | 0.015 *(held)* | 0.010 *(held)* | 2025 Gold Book baseline is inside the XLSX (M4) — no clean headline CAGR | held + re-cited |
| **NEISO** | 0.015 *(held)* | 0.010 *(held)* | 2026 CELT net **energy** ~1.0%/yr — the prior mid already brackets it; peak (2.6%/yr) is the DC/electrification block's job | held + re-cited |

**Band widths (low/high) are retained** from each ISO's own prior repo offsets, re-labelled
as documented judgment pending the per-year scenario tables (M3–M7) — not a residual fit
(rule 23). MISO borrows PJM's offsets (nearest DC-heavy eastern analogue).

**Demand deltas (analytic, before→after, cumulative growth factor from 2026):**

| ISO | 2030 factor | Δ2030 | 2035 factor | Δ2035 | matches anchor? |
|---|---|---|---|---|---|
| ERCOT | 1.216→1.216 | **+0.0%** | 1.375→1.375 | +0.0% | held (regression guard) ✓ |
| NYISO | 1.061→1.061 | **+0.0%** | 1.116→1.116 | +0.0% | held ✓ |
| NEISO | 1.061→1.061 | **+0.0%** | 1.116→1.116 | +0.0% | held ✓ |
| PJM | 1.148→1.152 | +0.4% | 1.255→1.297 | **+3.4%** | 2026 LF 20-yr +2.4%/yr ✓ |
| CAISO | 1.061→1.117 | **+5.2%** | 1.116→1.221 | +9.5% | CED-2025 2.8%/yr ✓ |
| MISO | 1.041→1.148 | **+10.3%** | 1.094→1.298 | **+18.7%** | LTLF +35%/2035 (from 2026) ✓ |

The held ISOs show a byte-clean 0.0% delta — the designated NEISO/ERCOT T0 smokes are
therefore a **regression guard** (their demand is unchanged), and MISO/CAISO/PJM carry the
demand-delta verification.

---

## 3. Data-center block (`DATACENTER_ADDITIONS_MW`, `DATACENTER_ZONE_SHARE`)

- **MISO block added** (was `{}`): low `{2026:0, 2030:0}` (honest floor — no signed-IA
  subset published), mid `{2026:0, 2027:8000, 2030:18000}`, high `{2026:0, 2027:14000,
  2030:25000}`. Source: MISO 2025 LTLF (8–14 GW DC in 2026-27; DC ~20% of energy by 2030,
  25% by 2040). The 18 GW mid = 0.20 × ~670 TWh MISO annual energy ÷ (0.85 CF × 8760 h).
- **ERCOT/PJM/CAISO/NYISO blocks unchanged** — FF-0D §1.3 rates them CURRENT (envelope);
  re-verified, no numeric change.
- **NEISO stays `{}`** — its 2026 CELT large-load quantum (~110 MW) is immaterial vs a
  ~26 GW peak and below the block's useful resolution; a sourced block waits on the CELT
  table (M6). No fitted placeholder.
- **`DATACENTER_ZONE_SHARE` stays `{}`** — the ERCOT (North/Oncor + West) and PJM
  (Dominion) siting skews are published in *direction* only; a valid override needs the
  full per-zone fractions (summing to 1.0) from the queue-geography / LTLF zonal tables
  (M5). Per the never-invent rule (rule 5) it stays load-share default. Moot at `off`.

All DC-path resolution is a no-op at the default `datacenter_load_path="off"` (verified:
MISO `off`→0 MW, `mid`→18000 MW @2030).

---

## 4. The growth×DC double-count + BAU posture (items 1-hazard & 3)

**Finding: the §3.5 organic-ex-DC re-derivation does not close on envelope anchors.** The
cx4 §3.5 continuity constraint asks the mid-path 2030 energy to hold invariant as DC
*relocates* from the growth rate into the explicit block:

```
organic_energy@2030 + DC_block_energy@2030  ≈  current_total_energy@2030
```

But the envelope DC block is far larger than the DC the rate embeds:

| ISO | mid DC block @2030 | block energy (×0.85×8760) | near-term growth to relocate | closes? |
|---|---|---|---|---|
| ERCOT | 37 GW | **≈275 TWh** | ~90 TWh (5%/yr on ~430 TWh) | **no — organic goes negative** |

The block is sized off the *speculative interconnection queue* (ERCOT ~226 GW large load,
~70% DC); the growth rate embeds only *expected realized* DC. They are different scenarios,
so continuity can't reconcile them — refining needs the ISO's realized-DC-by-year table
(M3–M7, manual-download-blocked). Landing a §3.5 decomposition on the envelope anchors would
produce garbage (a negative organic rate), so it is **not** done this pass.

**Owner posture decision (2026-07-17): `datacenter_load_path` default stays `"off"`.** With
the rates DC-inclusive and the block off, there is no double-count and no default regression;
the block ships populated-but-off for scenario use. `"mid"`/`"high"` remain **inadmissible**
until the organic-ex-DC decomposition lands (gated on M3–M7). Recorded in plan §2.1.

---

## 5. Verification

- **Unit tests:** `test_datacenter.py` (29 pass — MISO sourced-block + NEISO-zero tests
  updated), `test_config.py` demand-growth tests (MISO-uses-table + fallback-via-unmodeled-ISO
  updated). `parameter-citations.md` + `frontend/data/parameters.json` regenerated
  (`generate_parameter_registry.py`): 12 value-refreshes, 11 new rows (MISO demand + DC).
- **T0 invariant smokes (2026–2028, `run_full_horizon.py` → `check_forecast_invariants.py`):**

  | ISO | rate | solved | invariants | read |
  |---|---|---|---|---|
  | **NEISO** | held | 3/3 | I4 FAIL (2028 coal off 54 MW), I7 FAIL (2026 27171<28911), I12 WARN (2026 8.7%) | regression guard — demand byte-identical, so these equal the baseline |
  | **MISO** | **new (3.5%/2.5%)** | 3/3 | I7 FAIL (2026 133834<143177; 2027 146899<148188), I12 WARN (2026 2.8%, 2027 9.0%) | **executes end-to-end — FF-0B blocker cleared**; new rate reflected in the requirement path |

  Both runs' failures are the **known pre-existing forecast-baseline adequacy** items
  (I7 absolute floor / I12 margin — nothing force-builds firm capacity by default; identical
  in kind to the FF-0B 25-yr baseline). The structural machinery invariants (I1 energy
  balance, I2, I5, I11) PASS. **No NEW structural failure is introduced** — NEISO (held rate)
  is byte-identical demand to baseline, and MISO's only new behaviour is the higher demand
  path, which does not break any machinery invariant. ERCOT is a held-ISO equivalent to
  NEISO (its analytic demand delta is 0.0%); a separate ERCOT solve would reproduce the same
  held-ISO baseline, so it was not re-run.

_(The 8 pre-existing `test_soundness.py` end-to-end failures are environmental — a
fresh-checkout `data/clean` needs `regenerate_clean.py`, and one CAISO topology test is
stale spec drift — confirmed identical on the clean `origin/main` baseline; none are caused
by this change.)_

---

## 6. What this session did / did not do

- **Did:** verified the hydro fix (already on main); added the MISO demand rate + MISO DC
  block; re-centered CAISO/PJM mids on 2025/2026 forecasts; re-cited ERCOT/NYISO/NEISO
  (held); documented the DC-zone-share deferral; established that the §3.5 decomposition
  can't close on envelope anchors; recorded the owner's `off` posture; updated citations,
  tests, plan §1.2/§2.1.
- **Did not:** flip `datacenter_load_path`; touch `NEW_ENTRY_COSTS`/`TECH_COST_MULTIPLIERS`/
  policy (FF-1E); land the organic-ex-DC re-derivation (blocked on M3–M7); refresh
  ERCOT/NYISO/NEISO demand mids or DC zonal siting (blocked on M3–M7); invent any spread,
  siting fraction, or per-year anchor.

## 7. Follow-ups opened

| Item | Needs | Routes to |
|---|---|---|
| ERCOT/NYISO/NEISO demand mid refresh | ERCOT LTLF3 (M5), NYISO GB XLSX (M4), NEISO CELT (M6) | M-download intake → FF-1C follow-up |
| Organic-ex-DC re-derivation + `mid` admissibility | realized-DC-by-year tables (M3–M7) | intake → decomposition session |
| DC zonal siting (`DATACENTER_ZONE_SHARE`) | ERCOT LFL queue geography, PJM LTLF zonal DC (M5) | published-siting intake |
| DC anchor precision (envelope → MW-by-year) | ERCOT/PJM/NYISO MW-by-year tables | precision follow-up (FF-0D §1.3 P2) |

## 8. Push note (regenerated derivatives)

`frontend/data/parameters.json` (1.44 MB) and `docs/parameter-citations.md` (205 KB) were
regenerated locally by `scripts/generate_parameter_registry.py` (12 value-refreshes + 11
new MISO rows) but are **too large to push through `mcp__github__push_files`** within one
call's content budget, and this environment's proxy blocks all direct GitHub write APIs
(`/git/blobs`, `/contents` → 403). They are **deterministic derivatives of `constants.py`**
and are not CI-gated, so they are left to be regenerated (`python
scripts/generate_parameter_registry.py`) rather than pushed stale-then-corrected. The
authoritative citations are preserved **inline in `constants.py` comments and in §2–§4
above** (rule 5 satisfied at the source), so the numbers are fully traced without the
generated registry view.

*Produced 2026-07-17 (FF-1C, Opus). Feeds the T1-F baseline and every Wave-1/2 demand-side
comparison. Source URLs: `docs/handoffs/ff-inputs-currency-audit-2026-07.md` §1.1–§1.2,
§7.3; `docs/parameter-citations.md`.*
