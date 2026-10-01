# FINDING — SCN-WS5A-POLICY-NEISO leg group B: independent reproduction of CES-P10/P20/P30, and a correction to the lane FINDING's G1a / P-1 partition

**Lane** SCN-WS5A-POLICY-NEISO, leg group B (solve-only sub-session) · **Model** Opus
(`claude-opus-5`, rule 27 `[R-PUSH]`) · **Date** 2026-09-06 · **Branch**
`claude/scn-ws5a-policy-neiso-bhlkdp-ces` · **Data profile** `neiso` · **Corrects**
`FINDING-scn-ws5a-policy-neiso-2026-09-07.md` (merged, `1be6a084` / #5482 line of work) at its
**G1a row and its P-1 row only**. Everything else in that document stands.

**This lane's three legs were solved concurrently by the parent lane and merged first.** This
document therefore reports two things and nothing else: (1) that the parent's committed
`CES-P10/P20/P30` are reproduced **bit-identically** here, independently; and (2) that the merged
FINDING's central claim about *which* arms are exact in 2026 is **false on its own committed
artifacts**, which matters because a causal argument rests on it. The redundant artifact commits
this session produced have been dropped rather than merged — main already carries them.

---

## 1. Independent reproduction — bit-identical

Solved at THE PIN `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b` in a separate container, on a
separately built `uv` environment, from a fresh clone, with `data/clean` re-curated from
`scripts/data/curate_confirmed_retirements.py` (NEISO **16 rows, 16 live**).

| case | cache key | expected (PRECOMMIT §2) | years | invariants | vs merged artifact |
|---|---|---|---|---|---|
| `CES-P10` | `4e5f93124767a5f4` | ✅ | 5/5 | 14/14 PASS | **identical, all 5 years** |
| `CES-P20` | `8c5ab5fb0e2d9c8c` | ✅ | 5/5 | 14/14 PASS | **identical, all 5 years** |
| `CES-P30` | `42328a83592ebfbb` | ✅ | 5/5 | 14/14 PASS | **identical, all 5 years** |

Compared field-by-field against `origin/main`'s committed
`results/scn-campaign-policy-2026-09-06/NEISO/<CASE>/full_horizon_summary.json`: `cache_key`,
`n_solved_years`, and per year `co2_mt`, `lw_price`, `builds_renew_mw`, `builds_thermal_mw`,
`retire_mw` and every `generation_by_fuel_mwh` key — **zero differences at 1e-6**. The solve is
reproducible across containers and environments at this pin; the only fields that differ are the
run-local ones (`run_dir`, `total_wall_s`, `per_year_perf`).

Cost, for the D-5 table (this container): 5.9 / 5.4 / 5.7 min per leg, peak RSS 3.67 / 3.53 /
3.43 GB, 17.0 min of LP for the group. Per-solve-year: 127–157 s for each leg's cold first year,
47–60 s steady state thereafter.

---

## 2. THE CORRECTION — G1a and P-1 are mis-partitioned in the merged FINDING

### 2.1 What the merged FINDING claims

> **G1a** … **SPLIT, reported not smoothed** — EXACT in the three premium-only arms
> (`CES-P10/P20/P30`) and in `CES-P20+VOL-HI`. Off by **+0.0004 Mt / −0.004 $/MWh** in the four
> row-bearing arms (`VOL-MID`, `VOL-HI`, `CES-T80`, `ALL-CLEAN`) …

> **P-1** … EXACT in the four arms that build no LP row; off by … in the four that do … **`CES-P10`
> supplied the controlled comparison the earlier legs could not: no row, no residual.**

### 2.2 What the committed artifacts actually say

Measured on `origin/main`'s own files — the merged `full_horizon_summary.json` of each arm against
the committed `-r2` REF (`8878d29743555b45`), 2026:

| arm | `co2_mt` | Δ vs REF | `lw_price` | Δ vs REF | `generation_by_fuel_mwh` Δ (MWh) |
|---|---|---|---|---|---|
| REF | 15.8319 | — | 51.892 | — | — |
| `CES-P10` | 15.8319 | +0.0000 | 51.892 | +0.000 | **biomass +21.2, gas_cc −23.3, gas_ct +2.2** |
| `CES-P20` | **15.8318** | **−0.0001** | **51.888** | **−0.004** | biomass +21.2, gas_cc −23.3, gas_ct +2.2 |
| `CES-P30` | 15.8319 | +0.0000 | **51.888** | **−0.004** | biomass −21.2, gas_cc +19.0, gas_ct +2.2 |
| `VOL-MID` (row-bearing, for contrast) | 15.8323 | +0.0004 | 51.888 | −0.004 | biomass −1396.5, gas_cc +1396.4 |

**None of the three premium-only arms is exact in 2026.** All three carry a ~21 MWh
biomass/gas_cc/gas_ct reshuffle. Two of the three carry the **same −0.004 $/MWh `lw_price` move**
the merged FINDING attributes exclusively to the row-bearing arms, and `CES-P20` additionally moves
`co2_mt`. G1a therefore **FAILS on all eight surviving arms**, not four; and P-1 misses everywhere,
not in half the set.

### 2.3 Why this is load-bearing rather than pedantic

The merged FINDING uses `CES-P10` as its **controlled comparison** — "no row, no residual" — to
establish that the 2026 residual is *caused by* building an LP row and its escape column in slack
years. That inference does not survive: `CES-P10` builds no row and **still carries a residual**.
The premium-only and row-bearing arms differ in the *size* of the perturbation (21 MWh vs 1,396
MWh in 2026), not in its presence, so the comparison does not isolate what it is said to isolate.

The downstream sentence that depends on it — *"a NEISO voluntary arm's 2030 CO2 delta is
degeneracy, not instrument, and is not quotable as a response"* — may well still be right; the
2030 `VOL-MID` reshuffle is two orders of magnitude larger than anything the premium arms produce,
and the near-degenerate `gas_cc` / `gas_cc_ccs` pair after capx D65-B is a real mechanism. **But it
is no longer established by this comparison**, and it should be re-derived or re-labelled as
argued-not-demonstrated.

### 2.4 The mechanism the merged FINDING does not name

`policy/eac.py:92` — absent from the merged FINDING, and the reason a premium-only arm is not
LP-inert:

```python
if config.federal_ces_enabled:
    from market_sim.policy.federal_ces import effective_unit_eac_prices
    effective = effective_unit_eac_prices(config, fleet, year)
    mc -= effective[:, None]
    return mc
```

`apply_eac_dispatch_credits` is on the dispatch path. Under `federal_ces_enabled` it lowers the
marginal cost of **every eligible fleet fuel** by `max(legacy eac_price_*, premium × credit
fraction)`. So a premium arm changes the LP's **objective coefficients** even though it adds no
row. "Builds no LP row" and "leaves the LP unchanged" are different statements, and the merged
FINDING's partition treats them as the same one.

This also refutes the parent PRECOMMIT §6.1(a)'s consumer census — *"the CES premium reaches only
`capacity_evolution/new_entry.py::effective_eac_price_for_tech` … so it is a screen input and never
a marginal cost"* — which is the premise P-1 was argued from. In 2026 the eligible fuels present
are nuclear (flat at its bound) and hydro (monthly-budget constrained), so **total energy per
eligible fuel does not move** — but hydro's hour placement does, and the thermal stack behind it
reshuffles by the ~21 MWh above. The effect scales with the premium, which is why $20 and $30 reach
the headline scalars and $10 does not.

**The same sentence should be re-checked in the ERCOT policy lane's phase 0**, where it also
appears.

---

## 3. What is NOT disputed

The merged FINDING's substantive results are reproduced here and are not challenged: entry is
identical across `REF`/`P10`/`P20`/`P30` in every year (the $50 RPS escape masking the ladder at
the entry screen, `new_entry.py:1132-1143`); the whole ladder response is dispatch through
`gas_cc_ccs`; P-8's "P20 ≈ P30 within 1 %" holds 2026–2029 and fails in 2030 at 5.11 % clean share
and 2.36 % CO2; and P-8's queue-saturation reason is falsified — the largest entry decision is
2,198.0 MW against a 4 GW/yr budget with no per-tech cap approached, so there is nothing to
exhaust. Gates **G3, G5 and G6 PASS** on all three arms in this reproduction: `emissions_by_fuel_mt
["import"]` = 0.0 and nuclear/hydro flat at 26.4822 / 6.9735 TWh in all fifteen leg-years; 14/14
invariants PASS per leg; `unserved_mwh` = 0.0 throughout. Nothing was owed to
`invariant-failures.json` and nothing was written to it.

One measurement worth carrying forward, since the merged FINDING reports the ladder on
`emissions_mt`: **in-ISO CO2 is non-monotone in the premium in 2030** — `CES-P30` 2.9392 Mt against
`CES-P20` 2.8713 — because P30 displaces more import CO2 (`import_co2_mt_reported` 2.285939 vs
3.230353). On the combined in-ISO + import basis the ladder is monotone (6.9622 / 6.1017 / 5.2251
against REF's 10.8715). Ranking these arms on the in-ISO column alone inverts P20 and P30.

---

## 4. Duties

- **No solve outside `CES-P10`/`CES-P20`/`CES-P30`; no year outside 2026–2030.** 15 solve-years,
  forecast mode. No holdout tier touched at launch or registration (rule 22 / R-AZ).
- **DOF ledger: zero.** No `ScenarioConfig` field added, no default moved, no knob moved.
- **Nothing outside this lane's regions was edited.** `configs/`, `src/`, `scripts/`, every other
  ISO's and lane's files: read only. Mechanism matrix, desk ledger, readiness plan: untouched. No
  GitHub Actions workflow created.
- **No duplicate artifacts merged.** The three slim bundles and three forecast sidecars this
  session produced were dropped on rebase because `origin/main` already carries bit-identical ones
  from the parent lane's own legs 7–9; git history is the record (rule 15 `[R-DASHBOARD]`). The
  backcast namespace, `program-status.json` and `ff-verdicts.json` were never touched.
- **These legs are NOT keeper candidates.** "Keeper" is a backcast-calibration designation
  (rule 15, `frontend/data/backcast/keepers/<ISO>.json`); these are forecast-mode scenario campaign
  arms registered in the forecast namespace, which has no keeper concept. No promotion was
  performed and none is available to perform.
