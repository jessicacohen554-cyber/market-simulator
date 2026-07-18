# ERCOT → All-ISO Propagation: Audit & Prompt Pack

Status: **planning**. This pack is the *reverse* of docs 03/06/07/08. Those add
the mechanisms a non-ERCOT ISO needs that ERCOT lacks (capacity markets, hydro,
imports, reserves). This pack audits the improvements made to the **ERCOT**
model over time and perpetuates the ones that are **generic engine/methodology
improvements** through the whole model, while explicitly leaving the
**energy-only-design-specific** ones in ERCOT.

> **Classification rule (the user's rule).** If a change exists *because ERCOT
> is an energy-only market* (ORDC scarcity formula, the RTORDPA
> reliability-deployment offset, the RTC+B regime switch, the exogenous
> ancillary-service revenue stream, the $5,000 energy-only VOLL), it does **not**
> flow to the capacity-market ISOs. Everything else — anything that makes the
> shared dispatch/commitment/capacity engine more correct regardless of market
> design — should be perpetuated.

---

## 0. Headline finding

Most ERCOT *engine* improvements are **already ISO-agnostic** because they live
in code that operates on the struct-of-arrays fleet (`model/capacity.py`,
`model/commitment.py`, `model/dispatch.py`, `model/transmission.py`) and read
per-ISO config. The reserve-margin backstop, full fossil/nuclear retirement,
peaker new-entry, price-duration entry economics, the commitment screen, priced
import/export nodes and carbon pricing are **not gated on ERCOT** — they apply
to any ISO whose config/data populate them.

The genuine propagation gaps are narrower and fall into three kinds:

1. **ERCOT-tuned defaults applied globally** — a single calibrated scalar that
   silently becomes every ISO's value (the `planning_reserve_margin = 0.1375`
   default; `historic_outage_overlay = True` default).
2. **ERCOT-*gated* code paths** — `if … iso == "ERCOT"` branches that lock a
   generic capability to ERCOT (`runner.py:207` CAMPD per-plant binning;
   the ERCOT-only curated fleet dicts in `data/fleet.py`).
3. **Per-ISO data artifacts not yet built** — the mechanism is generalized but
   the input file only exists for some ISOs (`thermal_tranches_<ISO>.csv` for
   MISO/SPP; uncurtailed-HSL parquets for PJM/NEISO/MISO/SPP). These are already
   owned by the per-ISO Stage C–H / Pack J track and are referenced, not
   re-invented, here.

---

## 1. Audit

### 1A. Energy-only-specific — **DO NOT propagate**

These exist because ERCOT is energy-only. They must stay ERCOT-gated and remain
**off/zero** for the capacity-market ISOs (whose reliability value is carried by
the capacity-revenue module M1, already landed).

| Change | Where | Why it stays ERCOT-only |
|--------|-------|--------------------------|
| ORDC scarcity-price overlay (LOLP/RTORPA, multi-step floor) | `results/scarcity.py`; gated at `runner.py:547` (`iso == "ERCOT"`) | The published ORDC formula *is* ERCOT's energy-only scarcity-pricing mechanism. Capacity-market ISOs price reliability through the capacity market, not an energy-price adder. |
| RTORDPA reliability-deployment offset (`ordc_reliability_deployment_mw`) | `results/scarcity.py`, `scripts/data/derive_ordc_overlay.py` | Calibrated to ERCOT 2023 ECRS conservatism; an ORDC input. |
| Market-design regime switch (`ercot_market_design` auto/ordc/rtcb) | `results/scarcity.py` (`ercot_market_regime`), `scenarios.py` | Encodes ERCOT's RTC+B go-live (2025-12-05). Meaningless elsewhere. |
| Exogenous ancillary-service revenue stream | `model/ancillary.py` (gated `iso != "ERCOT"` → 0), `ERCOT_AS_REVENUE_PER_KW_YR` | ERCOT's energy-only design pays material AS revenue *outside* any capacity market. In RPM/ICAP/FCM/PRA ISOs, reliability income is the capacity payment (M1) — adding an AS stream on top risks double-counting. See decision item **D1** below before changing this. |
| $5,000 energy-only VOLL / DA SWCAP | `iso_configs.py` `_ercot_config().voll` | Already per-ISO (`ISOConfig.voll`); other ISOs are at $2,000. No action. |
| ERCOT NE_LOB Northeast-lobe carve-out (7th zone) | `iso_configs.py`, `zone_assignment.py`, `eia_loader._ERCOT_LOAD_ZONE_GROUPS` | The *principle* (split a zone to represent a binding intra-zonal pocket) is generic and already applied per-ISO; the specific NE_LOB carve-out is ERCOT topology data. Each ISO carves its own pockets in its own Pack A. |

### 1B. Generic & already ISO-agnostic — **verify only, no code propagation**

These already apply to every ISO; the only risk is that a non-ERCOT ISO's
config/data doesn't populate them. Covered by the Wave 1c verification prompt.

| Improvement | Where (ISO-agnostic) | Verify |
|-------------|----------------------|--------|
| Reserve-margin adequacy backstop (engine) | `capacity.py::apply_reserve_margin_build`, `accredited_firm_capacity_mw` | Reads `config.planning_reserve_margin` + `QUEUE_CAP_GW[iso]` — works for any ISO. Gap is the *value* (Wave 1a). |
| Full fossil/nuclear retirement coverage (oil, gas_cc_ccs, nuclear, gas_st) | `capacity.py::apply_economic_retirements`, `scenarios.py` `retirement_years_*`/`fixed_om_*` | Per-fuel, ISO-agnostic defaults — auto-applies. |
| Gas-CT peaker as new-entry candidate | `capacity.py::_NEW_ENTRY_TECHS`, `QUEUE_CAP_PER_TECH_GW[iso]["gas_ct"]` | Per-ISO queue caps already present (ERCOT/CAISO/PJM/MISO/SPP/NYISO/NEISO). |
| Price-duration new-entry economics (`Σ max(price−vc,0)` vs CONE) | `capacity.py::estimate_expected_revenue` | Price shape is universal; auto-applies. |
| Optional commitment screen (3-solve, IRR hurdle, min-run/down) | `model/commitment.py`, `commitment_enabled` | ISO-agnostic; opt-in per run. |
| Priced import/export node (interchange) | `model/transmission.py`, `IMPORT_TRANCHES`/`EXPORT_TRANCHES[iso]` | Generalized; ERCOT simply has none. |
| State/regional carbon pricing (RGGI/CARB) | `policy/carbon.py`, `STATE_CARBON_PRICE_BY_ISO` | Per-ISO registry; ERCOT zero. |
| Per-zone measured hourly load shapes | `data/eia_loader.py` (`*_zonal_load_shares`) | Per-ISO loaders with EIA-930 fallback. |
| Coal supply-class curated override (PRB/lignite pricing) | `fleet.py::load_coal_supply_overrides` (`coal_supply_<ISO>.csv`) | Already generalized per-ISO; ERCOT dict is precedence-only. **Template for Wave 2a.** |

### 1C. Generic improvement, but ERCOT-gated or ERCOT-defaulted — **PROPAGATE (actionable)**

This is the real work. Each becomes a prompt below.

| ID | Gap | Where | Action |
|----|-----|-------|--------|
| **G1** | `planning_reserve_margin = 0.1375` is ERCOT's economically-optimal RM but is the **global default** for every ISO; reserve-margin build is a forecast adequacy floor. | `scenarios.py:384`, `capacity.py:1188/1551` | Add `PLANNING_RESERVE_MARGIN_BY_ISO` (NERC/ISO targets, cited); resolve per-ISO with the scalar as fallback. Decide forecast-enable policy. → **W1a** |
| **G2** | Per-plant CAMPD offer-curve binning (`use_campd_bins`) is hard-gated to ERCOT even though `bin_assignments_<ISO>.csv` / `thermal_tranches_<ISO>.csv` already exist for CAISO/NEISO/NYISO/PJM. | `runner.py:207` (`use_campd_bins and iso == "ERCOT"`) | Generalize the gate to any ISO with a bin artifact; clean legacy-binning fallback for ISOs without one (MISO/SPP). → **W1b** |
| **G3** | `historic_outage_overlay = True` is the right ERCOT default but wrong for ISOs that derive unit-level outages fresh (e.g. PJM) — stacking double-counts. | `scenarios.py:199`, `runner.py` | Make the default per-ISO (`HISTORIC_OUTAGE_OVERLAY_BY_ISO`), keyed to whether the ISO has a complete unit-level file. → **W1b** (same files/area) |
| **G4** | ERCOT-only curated fleet dicts (`COAL_COMMISSION_YEAR`, `CC_REGULAR_COMMITTED_PCT_BY_PLANT`, `CHP_PMIN_CF_BY_PLANT`) override generic classification for ERCOT plants only. | `data/fleet.py` | Generalize each to read a per-ISO artifact (mirror the `coal_supply_<ISO>.csv` pattern); ERCOT dict stays precedence. → **W2a** |
| **G5** | `thermal_tranches_<ISO>.csv` (per-plant committed/peaking tranches) missing for **MISO & SPP**. | `data/raw/_processed-legacy/`, `scripts/` | Derive the artifact for MISO/SPP (needs their CAMPD/EIA-860). Folds into their Pack J. → **W2b** |
| **G6** | Uncurtailed-HSL renewable potential built only for ERCOT/CAISO (+NYISO partial); PJM/NEISO/MISO/SPP fall back to pre-curtailed EIA-930. | `data/renewables.py` (`_hsl_file` markers), `scripts/build_*_hsl.py` | Build per-ISO HSL parquets following `build_caiso_hsl.py`. Data task; folds into Pack J. → **W3** |

### 1D. Decision items (need a human call)

- **D1 — Ancillary-service revenue for non-ERCOT.** Real PJM/CAISO/NYISO/NEISO/
  MISO/SPP do run AS markets, but their *reliability* value is already in the
  capacity payment (M1). **Recommendation: keep AS revenue ERCOT-only** (status
  quo) unless calibration shows a specific ISO's storage/peaker entry is
  under-valued; if so, add a *small* per-ISO AS credit net of capacity revenue
  to avoid double-count. Listed here so it is a conscious choice, not drift.
- **D2 — Reserve-margin build in forecasts.** `reserve_margin_build_enabled`
  defaults off (pure economics). Decide whether forward runs for all ISOs turn
  it on as an adequacy floor (recommended for the published-forecast scenario,
  off for the pure price-discovery scenario).

---

## 2. Prompt pack — waves & dependencies

```
W0  parity baseline & guard ─┬─> W1a  per-ISO reserve margin (G1) ─┐
   (sequential gate; FIRST)  ├─> W1b  CAMPD binning unlock (G2,G3) ─┼─> W2a curated fleet dicts → per-ISO (G4)
                             └─> W1c  generic-coverage verify       │   W2b thermal_tranches MISO/SPP (G5)
                                      (no code, populates config)    │
                                                                     └─> W3  per-ISO HSL + recalibration (G6)
                                                                            (parallel per ISO; folds into Pack J)
```

- **W0 is a hard gate** — run and merge it before anything else. It freezes the
  golden baselines every later wave checks against.
- **W1a / W1b / W1c run in parallel** (separate worktrees). They touch mostly
  disjoint files; where they share `config/constants.py` they edit **different
  dicts**, so merges are clean. Land them, then re-baseline.
- **W2a / W2b run in parallel after W1b merges** (both build on the binning
  path). **W3 is per-ISO data/calibration** — parallel across ISOs, and is the
  existing Pack J work, not new engine code.

Every prompt below carries the same **ERCOT parity guard**: with the new per-ISO
parameter resolving to ERCOT's existing value/branch, the ERCOT backcast must be
**byte-identical** (compare result parquet hashes against the W0 baseline).

---

### W0 — Cross-ISO propagation baseline & parity guard  *(sequential, first)*

**Goal:** Freeze a golden baseline of current backcast outputs for every
calibrated ISO so each propagation PR can prove (a) ERCOT is unchanged and
(b) the target ISO changed only as intended.

**Prereqs:** none.

**Files:**
- `scripts/snapshot_propagation_baseline.py` (new) — run the existing backcast
  harness (`run_calibration_full.py`) for ERCOT (2023) and each ISO with a
  signed-off/active backcast (NEISO 2023–2025, NYISO 2023+2025, PJM 2023–2024)
  to a pinned `--out-dir`; record per-result-parquet SHA256 + headline
  fuel-mix/price stats into `tests/baselines/propagation_baseline.json`.
- `tests/test_propagation_parity.py` (new) — a parametrized test asserting the
  ERCOT result hash is unchanged; a helper other waves import to diff a target
  ISO against its baseline with documented tolerances.

**Tests / acceptance:** baseline JSON committed; `test_propagation_parity.py`
green on `main` (it just re-hashes the committed baseline). Document in the file
header how a later wave updates a *non-ERCOT* baseline intentionally (ERCOT row
is immutable without explicit sign-off).

---

### W1a — Per-ISO planning reserve margin  *(parallel; G1, D2)*

**Goal:** Stop every ISO inheriting ERCOT's 13.75% economically-optimal reserve
margin. Make the reserve-margin adequacy backstop resolve a per-ISO target.

**Prereqs:** W0.

**Files:**
- `src/market_sim/config/constants.py` — add `PLANNING_RESERVE_MARGIN_BY_ISO:
  dict[str, float]` with cited NERC/ISO targets (e.g. ERCOT 0.1375 Brattle/
  Astrapé 2022; PJM IRM ~0.175; MISO PRMR ~0.179; ISO-NE/NYISO/CAISO/SPP from
  their resource-adequacy filings). Each value gets a `needs-citation`/source
  comment per the no-magic-numbers rule.
- `src/market_sim/model/capacity.py` — in `apply_reserve_margin_build` (and the
  call site ~line 1551) resolve the margin as
  `PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, config.planning_reserve_margin)`; the
  `ScenarioConfig.planning_reserve_margin` scalar remains the explicit override.
- `src/market_sim/config/scenarios.py` — keep the `0.1375` default (it is the
  fallback); document that the per-ISO registry now leads.
- (D2) document the recommended `reserve_margin_build_enabled` policy per
  forecast scenario in the methodology spec / scenario presets; do not change
  the default-off without sign-off.

**Tests:** `tests/test_capacity.py` — ERCOT resolves to 0.1375 (parity); a
PJM/MISO run resolves to its higher target and force-builds gas_ct to the higher
floor; explicit `config.planning_reserve_margin` still overrides.

**Acceptance:** ERCOT backcast byte-identical vs W0 baseline; non-ERCOT
adequacy floor reflects the ISO's published target.

---

### W1b — Unlock per-plant CAMPD binning & per-ISO outage-overlay default  *(parallel; G2, G3)*

**Goal:** Let any ISO with a per-plant bin artifact use the CAMPD per-plant
offer-curve path (today locked to ERCOT), and set the historic outage overlay
per-ISO so unit-level-complete ISOs don't double-count.

**Prereqs:** W0. Reference `docs/binning-methodology.md` and
`docs/offer-curve-methodology.md`.

**Files:**
- `src/market_sim/runner.py:~207` — replace `config.use_campd_bins and iso ==
  "ERCOT"` with a check that the ISO has a bin artifact (e.g.
  `bin_assignments_<ISO>.csv` / `thermal_tranches_<ISO>.csv` present, or a
  `CAMPD_BINNING_ISOS` set). ISOs without one fall back to legacy
  `aggregate_fleet` exactly as today. Keep the ERCOT path bit-identical.
- `src/market_sim/config/constants.py` — add `HISTORIC_OUTAGE_OVERLAY_BY_ISO`
  (True for ERCOT/facility-summed ISOs; False for ISOs whose unit-level file is
  the complete source, e.g. PJM per the existing `scenarios.py:199` comment).
- `src/market_sim/config/scenarios.py:199` — `historic_outage_overlay` default
  resolves from the registry (scalar stays the explicit override).

**Tests:** `tests/test_runner.py` / `tests/test_fleet.py` — ERCOT still takes
the CAMPD path and is byte-identical; CAISO/NEISO/NYISO/PJM now take the CAMPD
path (assert per-plant tranches present); MISO/SPP cleanly fall back to legacy
bins with no error; PJM overlay resolves False.

**Acceptance:** ERCOT parity vs W0; the four artifact-having ISOs build
per-plant tranche offer curves; outage layers no longer stack for PJM.

---

### W1c — Generic-coverage verification & config backfill  *(parallel; 1B items)*

**Goal:** Confirm the already-ISO-agnostic ERCOT engine improvements actually
fire for every non-ERCOT ISO, and backfill any per-ISO config they need.

**Prereqs:** W0.

**Files (config/data + a sweep test; no engine code change expected):**
- Verify per-ISO presence and plausibility of: `QUEUE_CAP_PER_TECH_GW[iso]
  ["gas_ct"]`, `retirement_years_*`/`fixed_om_*` coverage of oil/gas_cc_ccs/
  nuclear/gas_st, `NEW_ENTRY_COSTS`, `STATE_CARBON_PRICE_BY_ISO`,
  `IMPORT_TRANCHES`/`EXPORT_TRANCHES`. Fill cited gaps in
  `config/constants.py`.
- `tests/test_iso_coverage.py` (new) — for each registered ISO, assert the
  new-entry candidate set includes gas_ct, every thermal fuel class is in the
  retirement screen, and (where the ISO has imports) an import node resolves.

**Acceptance:** a single test documents that the generic capacity/entry/exit and
policy improvements are live for all seven ISOs; any missing per-ISO datum is
filed with a citation.

**Status: DONE.** `tests/test_iso_coverage.py` (parametrized over
`_ISO_BUILDERS`) confirms, for every ISO: gas_ct is a new-entry candidate with
a `QUEUE_CAP_PER_TECH_GW[iso]["gas_ct"]` cap; all seven thermal fuel classes
are in the retirement screen; an import node resolves where the ISO has import
tranches; and ERCOT carries no import node and a zero state carbon price
(parity). **No config gap was found — no backfill and no engine-code change
were needed.** Per-ISO results are tabulated in
`docs/sessions/multi-iso/propagation-coverage.md` (archived).

---

### W2a — Generalize curated fleet dicts to per-ISO artifacts  *(after W1b; G4)*

**Goal:** Turn the remaining ERCOT-only hand-curated fleet overrides into the
same per-ISO-artifact pattern already used for coal supply class.

**Prereqs:** W1b merged. Template: `fleet.py::load_coal_supply_overrides`
(`coal_supply_<ISO>.csv`, ERCOT dict is precedence).

**Files:**
- `src/market_sim/data/fleet.py` — for `COAL_COMMISSION_YEAR`,
  `CC_REGULAR_COMMITTED_PCT_BY_PLANT`, `CHP_PMIN_CF_BY_PLANT`: add a loader that
  reads `data/raw/_processed-legacy/<name>_<ISO>.csv` and merges under the ERCOT
  hand-curated dict (ERCOT precedence preserved). No values change for ERCOT.
- `scripts/` — extend/author the per-ISO derivers that emit those CSVs from
  CAMPD/EIA-860 (parallel to the existing thermal-tranche/coal-supply derivers).

**Tests:** `tests/test_fleet.py` — ERCOT plants keep their hand-curated values
(parity); a non-ERCOT plant with a derived CSV row picks it up; absent rows fall
back to generic classification.

**Acceptance:** ERCOT parity vs W0; non-ERCOT fleets can carry measured
commission year / committed-share / CHP pmin where derived.

---

### W2b — Per-plant thermal tranches for MISO & SPP  *(after W1b; G5)*

**Goal:** Produce `thermal_tranches_MISO.csv` / `thermal_tranches_SPP.csv` so
those two ISOs can use the per-plant offer-curve path unlocked in W1b.

**Prereqs:** W1b; MISO/SPP CAMPD + EIA-860 ingested (their Pack C). Mirror the
existing `thermal_tranches_<ISO>.csv` schema and the deriver used for
CAISO/NEISO/NYISO/PJM.

**Files:** `scripts/` deriver run for MISO and SPP; outputs to
`data/raw/_processed-legacy/`. Register the two ISOs in `CAMPD_BINNING_ISOS` from W1b.

**Acceptance:** MISO/SPP build per-plant tranche offer curves; plant count &
capacity sanity-checked vs ISO published totals; ERCOT untouched.

---

### W3 — Per-ISO uncurtailed HSL & recalibration  *(parallel per ISO; G6 + Pack J)*

**Goal:** Feed dispatch the *uncurtailed* wind/solar potential (LP re-curtails
endogenously against transmission) for PJM/NEISO/MISO/SPP, as already done for
ERCOT/CAISO.

**Prereqs:** W1a/W1b merged so the ISO is on the parity harness. This is the
existing Stage D / Pack J data work — see `docs/multi-iso/03-prompt-pack-plan.md`
Pack B/J and `docs/multi-iso/04-transmission-zones-and-congestion.md` §4.

**Files:** `scripts/build_<iso>_hsl.py` (follow `build_caiso_hsl.py`);
`data/renewables.py` already routes via `_hsl_file` data-needed markers — no
mechanism change, just the per-ISO parquet + a markers entry.

**Acceptance:** modeled curtailment is an endogenous transmission response, not
a baked-in delivery haircut; per-ISO backcast re-scored and logged in
`docs/calibration-log.md`; status table in `00-iso-addition-protocol.md`
updated.

---

## 3. How to run this pack

1. Land **W0** on `claude/ercot-audit-iso-propagation-*`; merge it. The baseline
   JSON is now the contract.
2. Launch **W1a, W1b, W1c** as three concurrent sessions in separate worktrees.
   Each runs its named tests **plus** the full suite **plus** the W0 parity
   guard, then commits at its boundary.
3. Re-snapshot the baseline (non-ERCOT rows may legitimately move; the ERCOT row
   must not). Then launch **W2a, W2b** concurrently, and **W3** per ISO.
4. Each wave updates `CHANGELOG.md` and, where it changes behaviour for an ISO,
   that ISO's row in `00-iso-addition-protocol.md`.

**Non-negotiables carried from `claude.md`:** no Python loops over hours in LP
construction; prices stay LP duals; no magic numbers (every per-ISO value cites
a source in `docs/parameter-citations.md`); struct-of-arrays; full 8760; and the
**ERCOT byte-identical guard on every PR**.
