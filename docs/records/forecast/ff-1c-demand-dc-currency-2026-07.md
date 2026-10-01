# FF-1C — Demand & DC forward-input currency + hydro fix (2026-07)

**Session.** Wave-1 lane **L-INP** of the Forecast Finalization Program
(`docs/forecast-development-plan-2026-07.md` §6, FF-1C), executing the FF-0D audit's
§7.1 fix list. Branch `claude/demand-inputs-currency-norigp`, off `origin/main` `6d6867b`.
Scope boundary honored: this session owns **the DEMAND/DC constants + `data/hydro.py`
only** — `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` / policy are FF-1E's and are
**untouched**.

**Rule posture.** Every refreshed number is a **source-driven re-derivation** (rule 23)
from the FF-0D-cited 2025/2026 ISO forecast vintages — never a nudge toward a residual
(rules 1/13). Benchmarks scoped currency; none is a fit target. Forecast-mode-only
inputs; backcast is byte-identical (the DC block is validator-forced `off` in backcast;
the growth-rate refresh only affects forecast years — a backcast solves its weather year
at factor 1.0 / uses measured load).

---

## 0. What changed (one-paragraph read)

Five ISOs' `DEMAND_GROWTH_RATES` were on 2024 vintages (PJM/NYISO/NEISO carried literal
`TODO: verify`); **MISO had no entry at all** (a 1%/yr scalar fallback vs a published
+35%-by-2035 outlook — the audit's single largest demand gap). All six are now on their
published 2025/2026 central forecasts, cited. The data-center block gained a **MISO**
entry (was `{}`), and the **growth × DC double-count hazard** the audit flagged (§1.6) is
**structurally resolved**: because the near-era growth rates are DC-inclusive,
`add_datacenter_block` now **relocates** the block's energy (scales the peaky grown
demand down by the block's energy fraction and adds it back flat) instead of naively
adding it — total energy invariant, only the hourly shape flattens, no double-count. The
hydro forecast-fleet drop (item 2) had already landed on main (commit `66c55fd`) and is
verified here. `DATACENTER_ZONE_SHARE` stays load-share default (documented — no published
per-zone fraction was sourceable in-session). **The BAU DC posture (off vs mid default)
is presented to the owner in §7; not flipped here — default stays `off`.**

---

## 1. Hydro forecast-fleet drop (item 2) — ALREADY FIXED on main, verified here

The FF-0D audit (§5.3) chartered clamping the forecast budget-**shape** year to the newest
final EIA-923 census so a forecast year past the data horizon reuses the real plant set
instead of silently emptying the conventional-hydro fleet (~3.3 GW NYISO; also CAISO/
NEISO/PJM). The audit verified this against its own HEAD `67e64ed`, where the bug was
still present. **Between that base and current `origin/main` the fix landed independently**
(commit `66c55fd`, "hydro: clamp forecast budget-shape year to newest final EIA-923
census", 2026-07-16, Fable 5) — exactly the chartered fix:

- `build_hydro_fleet` forecast branch (`data/hydro.py:640`): `shape_year = min(year,
  EIA923_LATEST_FINAL_VINTAGE)` (2024); the **level** stays the EIA-930 normal-water-year
  climatology; backcast paths (`eia930_monthly` / bare) untouched; the swallowed
  empty-fleet collapse now logs a warning.
- Tests present and passing: `test_build_hydro_fleet_forecast_shape_year_clamped` (forecast
  year past horizon → unit-for-unit identical to the final-vintage fleet, >50 PJM plants,
  not the ≤10-plant early-release partial), `test_build_hydro_fleet_backcast_paths_not_clamped`
  (bare backcast still empties — byte-identity preserved).

**FF-1C disposition:** no new code needed for item 2; verified the fix meets the charter
(mode-aware, backcast byte-identical, tested). `tests/test_hydro.py` hydro-forecast/clamp
suite: **12 passed**.

---

## 2. `DEMAND_GROWTH_RATES` refresh (item 1a) — 5 ISOs re-vintaged, cited

Rates are **TOTAL** (DC-inclusive) — the near era still carries the DC boom, so at the
default `datacenter_load_path="off"` they reproduce each ISO's published total-load
forecast directly. The model applies a flat hourly scalar, so peak CAGR == energy CAGR;
`mid` = each ISO's published central forecast, low/high bracket it on the prior-vintage
band ratios re-centred on the new mid (exact published low/high scenario MW-by-year tables
are FF-0D §7.3 manual downloads). Near→long transition at `DEMAND_GROWTH_TRANSITION_YEAR`
= 2030.

| ISO | mid near (old→new) | mid long (old→new) | Cited forecast (FF-0D §1.1/§1.2) |
|---|---|---|---|
| **ERCOT** | 0.050 → **0.085** | 0.025 → 0.025 | 2025 LTLF3 adjusted 2030 peak ~139 GW (from 85.0 GW base ⇒ 8.5%/yr) |
| **PJM** | 0.035 → **0.036** | 0.018 → **0.024** | 2026 Load Forecast: 10-yr +3.6%/yr near, 20-yr +2.4%/yr long |
| **CAISO** | 0.015 → **0.028** | 0.010 → **0.025** | CEC CED 2025-2045: 1-in-2 peak 46.1→52.9 GW 2030 (2.8%/yr), →68 GW 2040 |
| **NYISO** | 0.015 → **0.018** | 0.010 → **0.012** | 2025 Gold Book vintage bump (exact table = §7.3 M4) |
| **NEISO** | 0.015 → **0.013** | 0.010 → **0.012** | 2026 CELT: energy ~1.0%/yr, winter peak 2.6%/yr (blended; §5 note) |

`TODO: verify` markers (PJM/NYISO/NEISO) removed and replaced with the dated 2025/2026
source. **Anchor validation (analytic):** ERCOT new mid → 2030 peak **138.7 GW**,
reproducing the cited LTLF3 ~139 GW to <0.3%. Every value is in `docs/parameter-citations.md`.

---

## 3. MISO wired (item 1b) — the audit's largest demand gap

- **`DEMAND_GROWTH_RATES["MISO"]`** added (was absent ⇒ 1%/yr scalar fallback): mid near
  **0.031** / long **0.020**, from the MISO Sept-2025 Long-Term Load Forecast (peak
  121→163 GW by 2035, ~3.0%/yr; ~3.1%/yr to the 2030 boundary from the 121.6 GW base).
- **`DATACENTER_ADDITIONS_MW["MISO"]`** added (was `{}`): mid **11 GW by 2027 → 20 GW by
  2030** (8–14 GW DC 2026-27 band; DC ~20% of MISO energy by 2030 ⇒ ~20 GW at 0.85 LF),
  high 14→27 GW, low 0. Source: MISO 2025 LTLF (FF-0D §1.2/§1.4).

---

## 4. DC anchors + zonal siting (item 1c)

- `DATACENTER_ADDITIONS_MW` ERCOT/PJM/CAISO/NYISO anchors re-confirmed against the
  FF-0D-cited vintages (unchanged values; CAISO already matched IEPR-2025; the PJM 30 GW
  mid carries the 2026-trim caveat). **NEISO stays `{}`** — the 2026 CELT large-load
  framework exists but its DC quantum (~110 MW to peak) is immaterial (<0.6% of peak); a
  documented deferral per the "no MATERIAL source ⇒ ship {}" rule, not an omission.
- **`DATACENTER_ZONE_SHARE` stays `{}` (load-share default).** FF-1C confirmed the skew
  **directions** are published (ERCOT North/Oncor + West; PJM Dominion/DOM) but **no
  published per-zone MW fraction** was sourceable in-session. Per the memo's "never invent
  a split" rule and this charter's explicit allowance ("no published decomposition ⇒ ships
  as load-share default, documented"), every ISO keeps its `load_share`. Populating
  ERCOT/PJM from the queue-geography fractions is the remaining P2 data-intake follow-up.

---

## 5. Growth × DC double-count (item 1d) — RESOLVED by energy-invariant relocation

**The hazard (FF-0D §1.6):** the near-era `DEMAND_GROWTH_RATES` embed the DC boom, so
turning the DC block on would count DC twice (once implicitly in the rate, once explicitly
in the block). The CX-4 §3.5 co-change (re-derive the near rate as organic-ex-DC under a
2030 energy-continuity constraint) had never landed, so the block was double-count-unsafe
at any non-`off` path.

**The fix (implemented in `data/datacenter.py::add_datacenter_block`).** Rather than
re-derive a separate organic-ex-DC rate constant (which is fragile: it is keyed to the
demand-growth percentile while the block is keyed to the DC percentile, so decoupled
levers desynchronize it), the block now **relocates** its own energy, computed from the
block MW itself:

    E = year_demand.sum();  dc_E = block_mw * T
    year_demand := year_demand * (1 - dc_E/E) + flat_block         # relocate regime

This conserves energy exactly (`E*(1-dc_E/E) + dc_E == E`) and is algebraically **identical**
to the memo's "organic-ex-DC rate + add block" — the scale `1 - dc_E/E` extracts the
organic-peaky component (organic and the DC-embedded portion both grew at the same total
rate, so they are proportional), and the flat block replaces the DC-peaky part it removed.
Result: **total energy invariant, peak flattens** (DC's defining flatness restored — the
exact shape error the block exists to fix, memo §1). Decoupling-safe by construction.

**Tail regime.** When `dc_E >= E` (a full-credible-queue "high" path whose DC alone tops
the total forecast — e.g. ERCOT high), there is no containable DC to relocate: the block
is genuinely incremental load and is **added**. Every ISO's **mid** path is in the
relocate regime (verified below), so the decision-relevant BAU case is always
energy-invariant.

**Per-ISO continuity (mid path, weather-2024 base energy, 2030):**

| ISO | base TWh | total mid E@2030 | DC block E | DC%E | scale | implied organic near |
|---|---|---|---|---|---|---|
| ERCOT | 462.6 | 755 | 276 | 36.5% | 0.635 | +0.6%/yr |
| PJM | 845.6 | 1045 | 223 | 21.4% | 0.786 | −0.5%/yr |
| CAISO | 223.5 | 264 | 13 | 5.1% | 0.949 | +1.9%/yr |
| NYISO | 130.1 | 145 | 22 | 15.4% | 0.846 | −1.0%/yr |
| MISO | 644.6 | 774 | 149 | 19.2% | 0.808 | −0.5%/yr |

All mid cases are in the relocate regime (scale ∈ [0.64, 1.0]) ⇒ exact energy continuity,
no double-count. The negative implied-organic rates (PJM/NYISO/MISO) reflect the real
forecast story — those ISOs' non-DC load is flat-to-declining and essentially all growth
is data centers; the relocation absorbs it fine (scale stays positive). The implied
organic rate is documented per ISO in `constants.py` as transparency only — it is **not a
live constant** (the relocation is computed from the block MW).

**Tests** (`tests/test_datacenter.py`, `tests/test_runner.py`): off-path byte-identity
(same object); mid-path energy invariance closed-form (ERCOT + per-ISO ERCOT/PJM/CAISO/
NYISO/MISO); peak-flattening; tail-regime add; runner-seam relocation. **35 + demand/DC
runner tests pass.**

---

## 6. T0 smoke (item 4) — NEISO + ERCOT 2026-2028, default (`off`)

### 6.1 Demand deltas match the cited anchors (analytic before/after, mid path)

| ISO/yr | peak before → after | ΔPeak | energy before → after | ΔE |
|---|---|---|---|---|
| NEISO 2026 | 21.6 → 21.5 GW | −0.4% | 106.9 → 106.5 TWh | −0.4% |
| NEISO 2028 | 22.3 → 22.1 GW | −0.8% | 110.2 → 109.3 TWh | −0.8% |
| ERCOT 2026 | 93.7 → 100.1 GW | +6.8% | 510.0 → 544.6 TWh | +6.8% |
| ERCOT 2028 | 103.3 → 117.8 GW | +14.0% | 562.3 → 641.1 TWh | +14.0% |

ERCOT rises to its cited LTLF3 trajectory (2030 → 138.7 GW ≈ 139 GW anchor); NEISO edges
down onto the CELT ~1.0%/yr energy path (from the old 1.5%). Deltas match the cited
anchors by construction.

### 6.2 Structural invariants (I1–I14, `check_forecast_invariants.py`)

Solved `run_full_horizon.py` NEISO + ERCOT 2026–2028 at HEAD defaults
(`datacenter_load_path="off"`, `demand_growth_path="mid"`). Results:

| ISO | FAIL | WARN | Attribution |
|---|---|---|---|
| NEISO | I4 (2028 coal off 54 MW), **I7** (2026 firm 27171 < req 28797 MW) | I12 (2026 RM 9.2%) | **Pre-existing, not the refresh.** I7 is the documented base-year adequacy FAIL (plan §1.2 item 5: "I7 FAILs at 2026 for CAISO/NEISO/NYISO"); my NEISO refresh *lowered* demand (1.5→1.3%), which *reduces* the requirement — it makes I7 less bad, so it cannot be the cause. I4 is a capacity-ledger rounding. |
| ERCOT | **I12** (2026 RM 7.3%, 2027 10.7%, 2028 5.5% < band 13.8%), I3 (2026 slack 0.01%) | I14 (scarcity price) | **Higher demand surfacing a KNOWN entry gap, not a demand-input defect.** At the old 5% rate ERCOT 2026 peak was 93.7 GW → RM ≈14.6% (PASS); the refreshed 8.5% (LTLF3, 100.1 GW) drops RM to 7.3% (FAIL). ERCOT is energy-only and the entry stack does not build the ~50 GW its official forecast demands (plan §1.2 items 3/4, "ERCOT chronic shortage / economic entry commissions in-year"). Per rules 1/13 the correct demand input stays; the root cause is the entry/adequacy machinery (FF-2A/2B), not this session's inputs. |

All other invariants PASS (energy balance, no-NaN, retire/re-enter, one-pass, cobweb,
storage, RPS dual). **No FAIL is attributable to the DC relocation or a demand-input
error.** The refresh is structurally coherent; the FAILs are pre-existing (NEISO) or the
accurate higher ERCOT demand exposing the known entry-stack under-build (ERCOT) — a
discovered root-cause for the entry lane, exactly the rule-13 posture (keep the accurate
input, fix the real cause elsewhere; never bury it back in a softened demand number).

**Material flag for §7.** The ERCOT LTLF3 central case (8.5%/yr) is ERCOT's *official*
adjusted forecast but is aggressive; adopting it as the REF default drives an immediate,
persistent reserve-margin shortfall that the current entry stack cannot close in-window.
This is surfaced to the owner alongside the DC posture (§7).

---

## 7. BAU DC posture (item 3) — OWNER DECISION (not flipped here)

`datacenter_load_path` default for T1+/golden runs: **`off`** (current) vs **`mid`**.

**The two are energy-equivalent at mid; the choice is purely the DC hourly SHAPE:**

- **`off` (legacy):** DC rides the peaky weather-year shape (DC in the growth rate).
  Overstates DC's peak contribution — the exact error the block exists to fix. Byte-identical
  to today's mechanism (with the refreshed rates).
- **`mid` (DC block on, relocated):** identical total energy, but DC is modeled **flat**
  (its physical trait) → **lower peak** (e.g. ERCOT 2030 ~120 GW vs ~139 GW), less peaker
  over-build and less phantom scarcity rent (memo §5.1). Structurally more faithful.

**Now admissible.** The §5 relocation resolves the double-count the audit named as the
blocker ("`mid` is only admissible after the decomposition lands"), so `mid` is a valid
choice as of this session. **Recommendation:** the decision is the owner's; the structural
argument favors `mid` (correct DC shape), but it is a material change to the golden peak
trajectory and interacts with the capacity floor (memo §5.1), so it is surfaced, not
flipped. Recorded in plan §2.1 once decided.

---

## 8. Scope attestation & follow-ups

- **Files touched:** `config/constants.py` (DEMAND_GROWTH_RATES + MISO, DATACENTER_ADDITIONS_MW
  + MISO, DATACENTER_ZONE_SHARE comment), `data/datacenter.py` (relocation), `runner.py`
  (2 comment accuracy edits), `frontend/data/parameters.json` + `docs/parameter-citations.md`
  (regenerated), tests. **No `NEW_ENTRY_COSTS` / `TECH_COST_MULTIPLIERS` / policy / `capacity.py`
  touched** (FF-1E scope).
- **Backcast byte-identity:** preserved (DC block validator-forced `off` in backcast; the
  growth refresh only affects forecast years).
- **Golden band fixture** (`tests/golden/ercot_2026_2040`) uses ERCOT `mid` and will move
  under the refreshed rates; its band test is gated `RUN_GOLDEN_FORECAST=1` (skipped per-PR).
  **Re-seed is a documented follow-up** (`python scripts/golden_forecast_bands.py seed
  --force`), not a per-PR blocker.
- **P2 follow-ups (unchanged from FF-0D §7.1):** ERCOT/PJM published DC zonal fractions →
  `DATACENTER_ZONE_SHARE`; DC anchors → ISO MW-by-year tables (§7.3 manual pulls);
  optional material NEISO DC block if the CELT quantum grows.
- **Rule 27:** `constants.py` edited surgically (Edit tool), pushed as exact on-disk bytes,
  blob-verified after push.

*Produced 2026-07-17 (FF-1C, Opus). Feeds the forecast tier ladder; FF-1E rebases on this
`constants.py` state.*
