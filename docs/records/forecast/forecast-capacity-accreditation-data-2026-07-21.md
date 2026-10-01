# Forecast capacity-accreditation data — in-repo-vs-missing audit (2026-07-21)

**Lane.** Published-basis accreditation-input intake/wiring for the five
capacity-market ISOs (PJM, MISO, NYISO, NEISO, CAISO) — the three parameters
that feed the forecast capacity-revenue / adequacy chain: **per-year net-CONE**,
**ICAP→UCAP requirement conversion**, and the **declining VRE ELCC axis**.
Parent flags BLK-3 / BLK-4 / BLK-7 / BLK-9 (gap register §3.9/§3.10), P-2B
accreditation-basis memo (`docs/handoffs/accreditation-basis-memo-2026-07-12.md`).

**Scope guard.** Published-parameter intake/wiring only — **no LP solve** (rule
22 no-LP), `capacity_market_clearing` **not** flipped, constants on the
`ScenarioConfig`/registry channel only (rule 24). Never fit, never fabricate a
number a filing does not publish (rules 1/13).

## Headline

**Almost everything is already wired and reconciled on `main`.** The task's
premise (5 ISOs *lack* published-basis accreditation inputs) predates the
FF-2B / FF-2C / FF-3D landings of 2026-07-18/19/20, which closed it. This
session **verified** the wiring end-to-end against the on-disk raw data, found
**no silent gap**, fixed the one **stale gap-register row** it contradicted
(§3.10 R5a — see below), and records the genuine remainder as **owner-decisions
where no filed constant exists** (must not be fabricated). `constants.py` /
`capacity_market.py` were **not modified** — they are already complete, and a
no-benefit rewrite of a core file carries only rule-27 risk.

All 298 capacity tests pass (`tests/test_capacity*.py`,
`test_renewable_elcc_curves.py`, `test_constants_facade.py`,
`test_capacity_evolution_facade.py`).

## Per-ISO × parameter matrix

Legend — **W** wired · **U** on-disk but deliberately unwired (documented basis
reason) · **N** no published ISO basis (cited generic/fixed fallback) ·
**n/a** structurally not applicable.

All code anchors in `src/market_sim/config/capacity_market.py` (re-exported via
`config/constants.py`). Raw data under `data/raw/capacity-market/`.

| ISO | Per-year net-CONE | ICAP→UCAP ratio | VRE ELCC axis |
|---|---|---|---|
| **PJM** | **W** — 7/7 delivery years 2021/22–2027/28 (`MARKET_DESIGN_VINTAGES:1232`); FPR devintaged 2025/26=0.938, 2026/27=0.917, 2027/28=0.926 (`FORECAST_POOL_REQUIREMENT_BY_ISO:2142`) | **W** — `0.9170/1.191` (`:2118`), reconciles `demand-curve/pjm/pjm.csv` (FPR + IRM 19.1%, 2026/27) | **W** wind (flat 0.41) + solar (0.106→0.079) (`:1764`); **U** ER24-99 declining wind axis (BLK-7, see OD-1) |
| **MISO** | **W** — 5/6 (`:1356`); 2026-27 held-last (**U**, rule-5 per-LRZ-only, `:1370`) | **W** — `1.079/1.157 = 0.9326` (`:2119`), filing-cited (LOLE Study Module E-1, off-disk) | **W** wind class-avg (`:1818`); **U** marginal-tranche rows; **N** solar (no published curve, `:1815`) |
| **NYISO** | **W** — all curve-publishing DYs 2021/22–2025/26 (`:1308`); 2020-21 publishes only the translation factor, no curve | **W** — `1 − 0.1321 = 0.8679` (`:2120`), reconciles `demand-curve/nyiso/nyiso.csv` CY 2024-25 row (**resolved FF-3D 2026-07-18, Option B**) | **W** wind/solar/offshore single-point CAFs (`:1839`); **U** 2022 NY-BEST declining (third-party) |
| **NEISO** | **W** — 8/8 DYs 2020/21–2027/28 (`:1323`) | **n/a** — `claimed_capability` basis, no EFORd derate (R5b, `:1912`); ratio-1.0 is correct, not a gap | **N** — all on-disk rows third-party (2022 GE/NRDC, 2024 E3/Mettetal), not ISO-NE-adopted (`:1749`) |
| **CAISO** | **N** — no published net-CONE curve; fixed CPM soft-offer-cap proxy $88.08/kW-yr (`:1020`), reconciled to `caiso.csv` | **n/a** — bilateral RA, no ICAP↔UCAP requirement pairing | **N/U** — only marginal-tranche CPUC E3/Astrapé (IRP-portfolio-conditioned); misalignment exception, rule 15 (`:1754`) |

Exact on-disk paths: `data/raw/capacity-market/{demand-curve,elcc}/{pjm,miso,nyiso,neiso,caiso}/<iso>.csv`;
PJM planning workbooks `demand-curve/pjm/pjm-<yr>-planning-parameters.xlsx`;
filing READMEs `accreditation-filings/{nyiso,neiso}/README.md` (no MISO/PJM/CAISO
filing files present — those bases are filing-cited in code, not on disk).

## What changed this session

1. **Gap register §3.10 R5a (NYISO ICAP/UCAP)** — status cell was **stale**: it
   still read "ADJUDICATED, NOT IMPLEMENTED (2026-07-15)", "`…ICAP_TO_UCAP…`
   still absent for NYISO, ratio-1.0 fallback", and "NYISO stays
   curve-INELIGIBLE". All three now contradict code: the ratio is present
   (`0.8679`, `:2120`) and `CAPACITY_CURVE_ELIGIBLE_BY_ISO["NYISO"] = True`
   (`:757`), both landed FF-3D 2026-07-18 (owner-selected Option B). Refreshed
   to **IMPLEMENTED**, history + rule-13 caveat preserved.
2. **Gap register §3.9 BLK-9 row** — the secondary clause "Fixed-mode BLK-9
   persists only for NYISO (unflipped, **curve-ineligible R5a**)" corrected: the
   flat-payment persistence is because NYISO's *default `capacity_market_clearing`
   flip stays OFF*, **not** curve-ineligibility (NYISO is now curve-eligible).

No code, data, or test file was modified.

## Open owner-decisions (no filed constant — do NOT fabricate)

**OD-1 — PJM onshore-wind declining ELCC axis (BLK-7 accreditation-data half).**
The model wires PJM wind at the published **class-average** rating (flat 0.41 on
an installed-MW axis, `elcc/pjm/pjm.csv` 2026/27 + 2027/28 official/final). PJM
*also* publishes a **declining** trajectory — ER24-99 preliminary marginal
ratings 35% (2026/27) → 15% (2034/35) — but it is `elcc_type=marginal`,
**delivery-year-indexed with no penetration/installed-MW axis**
(`penetration_pct` null). The model's resolver is penetration-indexed; the
elcc schema *forbids* back-filling a guessed penetration axis
(`capacity-market-elcc.schema.yaml`: "never back-filled with a guessed
penetration level"). So the declining axis **cannot be wired without
fabricating an axis PJM did not publish** (rule 13). Options for the owner:
   - **(a)** keep the flat published class-average (current, conservative,
     zero-DOF) — *recommended until PJM publishes a marginal-rating × MW pairing*;
   - **(b)** thread a delivery-year-indexed (not penetration-indexed) wind axis
     as a distinct resolver mode fed by the ER24-99 preliminary column — a
     resolver-architecture change, and the values are explicitly "preliminary,
     non-binding, indicative", so this trades a published-final constant for a
     published-preliminary one;
   - **(c)** wait for PJM's final ER24-99 methodology ratings with an MW axis,
     then wire as a normal penetration curve.
   This is the accreditation-*data* face of BLK-7; the entry-screen consumption
   of VRE capacity revenue (BLK-7 term (c)) is the separate FF-2A lane.

**OD-2 — NYISO static proxy vs lagged model-derived (deferred, carried from
adjudication §3).** Option B (wired) freezes the 2024-25 realized NYCA-wide
translation factor (0.8679). NYISO recomputes it twice a year from the
then-qualified fleet, and it rises with wind penetration (0.083 → 0.132 across
2020-25), so the frozen snapshot is the weaker rule-13 forward story. The
recommended long-run target is **Option A** (lagged model-derived roll-up,
`1 − Σ prior-year accredited MW / Σ prior-year nameplate`), which needs a
prior-year-threading architecture change (comparable to the existing
`mc_cost`/`prior_results` pattern). Not required while `capacity_market_clearing`
stays default-OFF for NYISO; revisit if a curve-ON NYISO forecast is chartered.

## Deliberately-unwired-with-basis (not gaps, no owner action)

- **MISO 2026-27 net-CONE** — CSV publishes per-LRZ Net CONE only (no
  North/Central aggregate); rule 5 boundary → hold-last on PY2025-26 (`:1370`).
- **MISO solar ELCC** — no published probabilistic curve (flat seasonal
  defaults only) → generic fallback (`:1815`).
- **NYISO 2022 NY-BEST / NEISO 2022 GE-NRDC + 2024 E3-Mettetal / CAISO CPUC
  E3-Astrapé** VRE curves — all **third-party or marginal-tranche**, explicitly
  not the ISO's adopted accreditation basis; wiring any as the whole-fleet
  ledger credit would misstate the supply block (rule 15 misalignment
  exception). Cited generic/fixed fallback stands until an ISO-adopted
  class-average study is published (`:1749`, `:1754`).
- **CAISO net-CONE / ICAP→UCAP** — bilateral RA, no capacity auction cleared in
  the model; fixed CPM soft-offer-cap proxy by design, gate is a no-op.

## Verification

- Runtime registry snapshot (all five ISOs) — ratios `{PJM 0.7699, MISO 0.9326,
  NYISO 0.8679}`; thermal bases `{ERCOT seasonal_rating, PJM elcc_class_rating,
  NEISO claimed_capability}`; PJM FPR `{2025/26 0.938, 2026/27 0.917, 2027/28
  0.926}`; curve-eligible all True; vintages PJM 7 / NYISO 5 / NEISO 8 / MISO 5;
  VRE-ELCC classes PJM{wind,solar} MISO{wind} NYISO{wind,solar,offshore_wind}.
- `docs/parameter-citations.md` + `frontend/data/parameters.json` both carry the
  NYISO ratio (0.8679) and NEISO `claimed_capability` rows — the registry drift
  the adjudication §6 flagged (unpushed at 2026-07-15) has since been
  regenerated; no drift remains.
- `pytest tests/test_capacity.py tests/test_capacity_demand_curve.py
  tests/test_renewable_elcc_curves.py tests/test_constants_facade.py
  tests/test_capacity_evolution_facade.py` → **298 passed**.

*Produced 2026-07-21, branch `claude/forecast-capacity-accreditation-data`.
Verification-and-doc-sync session: two gap-register status corrections, this
findings doc; no code/data/test change (the accreditation inputs were already
wired). No dashboard registration (forecast-only, no solve).*
