# FF-2C — capacity_market_clearing flip execution (PJM/MISO/CAISO/NEISO) + R4 — 2026-07-20

**Lane.** F-9 / RC-3A of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.3;
`docs/forecast-development-plan-2026-07.md` §7 binds). Executes the owner's
2026-07-19 sign-off (via the FF wave manager, turn 31) to **flip the CR-1
sloped capacity demand curve ON by default for PJM, MISO, CAISO, NEISO** —
the decision the RC-2B per-ISO flip memo
(`docs/handoffs/capacity-clearing-flip-memo-2026-07-16.md`) put to the owner
and the §5 D1=3 re-probe unblocked. **NYISO is excluded** this session (its
train-tier determination is NOT-YET — nyiso-65, marker withdrawn — and its
flip-gate pair evidence predates the corrected outage envelope, a rule-11
taint); it joins a later per-ISO flip session after re-calibration. **ERCOT is
energy-only and is never flipped.**

This is a **forecast-mode mechanism flip** (rule 1 — the CR-1 curve is the
structurally-faithful RA price; the fixed net-CONE × UCAP stub was the
low-fidelity stand-in). Nothing on the backcast dashboard; every backcast
keeper stays byte-identical (§1.2).

---

## 1. What landed (commit `dbbae9c`, one consolidated code commit)

### 1.1 The gate flip
`ScenarioConfig.capacity_market_clearing_by_iso` default `None` →
`{"PJM": True, "MISO": True, "CAISO": True, "NEISO": True}`
(`src/market_sim/config/scenarios.py`). Resolved per-ISO through the one seam
`constants.resolve_capacity_market_clearing` (rule 19), so each of the three
capacity-evolution screens (retirement, thermal entry, storage entry) now
prices resource adequacy off the ISO's published net-CONE-anchored sloped
demand curve `VRR(reserve_position) × net_cone_curve` instead of the flat
`net_cone_per_kw_yr × (1 − EFORd)` stub. NYISO is absent from the mapping →
falls through to the scalar (`capacity_market_clearing=False`, off); it is
also code-ineligible until R5a lands. ERCOT has no capacity market → the seam
returns 0 in both modes.

### 1.2 Backcast byte-identity (the FF-2A / FF-1F discipline)
`capacity_market_clearing_by_iso` is **not** in `_CACHE_KEY_OPTIONAL_FIELDS`,
so a backcast inheriting the flipped dict default would shift every keeper's
`cache_key`. `__post_init__` therefore coerces the field to `None` in a plain
backcast (`mode == "backcast"`) — a backcast runs no capacity evolution, so
the pricing seam is never consulted there; the coercion just keeps the key
byte-identical. **NOT** coerced when hindcast (`mode=="forecast"`,
`hindcast=True`): the capacity-hindcast harness arms the gate explicitly per
leg (`{iso: True}` for the curve leg, `None` for the fixed leg), so the
fixed↔curve pair stays scoreable. Same discipline as the FF-2A
`entry_lookahead_reprice` and FF-1F `datacenter_load_path` coercions.

### 1.3 R4 — legacy fixed anchor re-derivation (accreditation-basis memo §4.3-R4)
Now that the flip has landed, the legacy fixed `net_cone_per_kw_yr`
placeholders — kept only for pre-flip default byte-identity — are re-derived
to each ISO's own **published-basis** net-CONE (`constants.py` `MARKET_DESIGN`).
Every figure traces to the P-0B `capacity-market/demand-curve` raw data (rule
13 — published input, never a fit target):

| ISO | old (placeholder) | R4 (published basis) | source |
|---|--:|--:|---|
| PJM | 100.0 | **77.431** | 212.14 $/MW-day UCAP × 365/1000 (2026/27 BRA) = curve anchor |
| MISO | 80.0 | **79.8** | North/Central Net CONE ($79,800/MW-yr) = curve anchor |
| NEISO | 95.0 | **108.94** | FCA 18 net-CONE 9.078 $/kW-month × 12 = curve anchor |
| CAISO | 90.0 | **88.08** | CPM soft-offer cap 7.34 $/kW-month × 12 (FERC ER24-1225), exact |

For the three curve ISOs the fixed anchor is now **equal to** the published
curve anchor `net_cone_curve_per_kw_yr` (the "legacy" separation existed only
for byte-identity). CAISO carries no auction curve (RA-not-auction; the flip
is a **pricing no-op** for CAISO by construction — flip memo §1.5), so its
fixed anchor IS its price in both modes; R4 tightens the 90 rounding to the
exact CPM soft-offer cap. Reconciliation tests updated
(`tests/test_capacity_demand_curve.py`): fixed = curve anchor asserted for
PJM/MISO/NEISO; CAISO tightened from within-5% to exact.

### 1.4 Governance self-check
- Every R4 number is cited to primary raw data and surfaced in each run's
  `run_config.json` (rules 5/24 — no env knob, no getattr fallback literal,
  no residual-fitted value). Rules 1/13/14 clean.
- The flip is forecast-mode only; nothing registered on the backcast
  dashboard; no holdout year solved/scored (rule 22).
- Core-file edits (`scenarios.py`, `constants.py`) pushed as the exact on-disk
  bytes and blob-verified (rule 27: local blob SHAs identical to the pushed
  remote blobs; `git diff HEAD origin/<branch>` empty).

---

## 2. Post-flip evidence

### 2.1 Already-measured curve-ON behavior (published, pre-FF-2C)
The flip's mechanism was measured before this session and is the basis for the
owner's go decision. It is **not re-litigated here** (FF-2C executes; it does
not re-grade):

- **PJM (RC-1A curve-ON probe, D1=1):** coal economic exits 0 → 9.913 GW
  (actual 6.885; +44% overshoot), recall 0 → 76%; in the one year its position
  entered the priced region (2024) it paid 112 $/kW-yr vs the 10.6 cleared;
  the coupled BLK-10 backstop fired 6.43 GW gas_ct in one 2025 step.
  (`docs/handoffs/position-calibration-findings-2026-07-16.md` §1.)
- **MISO (RC-1A, seasonal grain, D1=1):** coal 0 → 11.809 GW (actual 10.934;
  +8%), false-retire 0.874 GW band-PASS; the 2025 shortage year stays
  under-priced (24.5 vs 243.3 cleared at cap) — a one-sided position residual.
- **NEISO (FF-2B first capacity-hindcast pair, 2026-07-19):** curve-ON retired
  9.3 GW (+880%, 8.4 GW false) vs 0.002 GW fixed — the BLK-9/BLK-10 over-fire
  signature, now measured for NEISO for the first time.
  (`docs/handoffs/ff-2b-adequacy-basis-2026-07.md` §6.)

The consistent finding: the flip **trades the fixed mode's 0-retirement /
nuclear-inversion pathology (BLK-9) for a curve-ON over-retirement wave
(BLK-10)** — a different, still-open root cause in the retirement decision-rule
+ backstop-sizing lanes (FF-0C/FF-1A/BLK-10), **NOT** something FF-2C tunes
(rules 1/11/14). The flip is kept because it is the structurally-faithful
mechanism; the wave is root-caused elsewhere. (This is the rule-1 discipline
the wave-manager note calls out explicitly for NEISO.)

### 2.2 Fresh flipped-default re-runs (this session)

**T1.7 net-CONE ladder — a rig-limitation finding (not a directional pass).**
PJM T1.7 (flipped, 2026–2030): thermal retirements **flat at 11.836 GW** across
net-CONE {0,1,2}× (entry 8.87 → 8.69 → 8.22 GW; lw_price ~39.68; CO₂ ~1936 Mt).
Two compounding reasons the ladder does not cleanly exercise the flipped curve:
1. **The rig scales the wrong knob.** `run_driver_battery.py`'s
   `_net_cone_scalar` patches `MarketDesign(net_cone_per_kw_yr=base×scalar)` and
   **drops `demand_curve` / `net_cone_curve_per_kw_yr` / `seasonal_rbdc`**
   (`scripts/run_driver_battery.py:595`). Post-flip the flipped ISOs price on
   the *curve* anchor `net_cone_curve_per_kw_yr`, which the scalar never
   touches; with the curve patched away the seam even falls back to the fixed
   path. So the T1.7 ladder measures the now-bypassed fixed channel.
2. **Exogenous-exit domination.** `retired_thermal_gw` is cumulative and
   includes the confirmed (step 0) + announced (step 1) exits, which are
   net-CONE-invariant; at PJM's healthy 2026–2030 energy price (~$39.68) the
   *economic* component adds ~0 marginal sensitivity, so the total is flat.

**Follow-up (routed → DONE this session, FF-2C-rig, rule 6):** the T1.7 rig now
preserves `demand_curve`/`seasonal_rbdc` and scales `net_cone_curve_per_kw_yr`
(registry + per-year vintages) for curve ISOs, and reports the *economic*
retirement component separately from exogenous exits. Rig repair only, no
behavioural tuning (rules 1/13). The fixed-rig re-measurement is **§2.3 below**;
it supersedes the flat-11.836-GW artifact above as the informative reading.
**ERCOT T1.7 is byte-identical across rungs (energy-only negative control), as
expected.**

**Position caveat (compounds #1):** even a curve-preserving rig would find PJM
at a position (~1.29–1.36) past its curve's 1.045 zero-cross → the curve pays
$0 (flip memo §2; P-2A Pass 2). The BLK-3 requirement/position half (R2/R3,
FF-2B-adjacent) must land before PJM's flipped curve prices non-zero. So the
flip is live and correct, but its *quantitative* retirement effect for PJM is
gated on the position fix — exactly the flip memo's measured caveat.

**Fresh curve-ON hindcast re-scores (registered on the forecast-validation
dashboard, this session):** both band-FAIL, and honest (rule 1 — the flip is
the structurally-correct mechanism; the residual is the retirement-rule +
backstop lanes', not tuned). At each ISO's current (mis-based, too-long)
position the flipped curve pays ~$0, so retirements are energy-driven and the
wave lands on the wrong classes:

| ISO | thermal retire model / actual | wave lands on | nuclear-inversion | recall | notes |
|---|---|---|---|--:|---|
| **MISO** (`miso-2021-2025-curve-ff2c`) | 10.8 / 15.2 GW (−29%) | gas_st 8.6 (actual 0) | — (nuclear 0.77≈actual 0.81) | 0.118 | coal under-retires (1.4 vs 10.9); solar 0 (BLK-8) |
| **PJM** (`pjm-2021-2025-curve-ff2c`) | 18.2 / 11.1 GW (+63%) | gas_st 10.4 (actual 0) | **4.1 GW false** (actual 0) | 0.235 | coal 0 (vs 6.9); solar over-builds 24 vs 13 |

The **PJM nuclear-inversion persists** (4.1 GW false-retired) — confirming that
the flip alone does not fix retirement direction while the position pays $0
(BLK-3 R2/R3 requirement half still open, flip memo §2). Both are the expected
curve-ON over-fire / mis-direction signature (BLK-10 successor), now measured on
the *shipping* (D1=3, R4-anchor) config for the first time — not the RC-1A D1=1
probe config.

**Still pending (documented, not run — per-plant hours each in a restart-prone
session):** CAISO hindcast (R4-anchor effect; pricing no-op), NEISO (reuse the
FF-2B `neiso-2021-2025-curve` leg — R4 changed only the fixed anchor, so its
curve-ON dispatch is unchanged), equilibrium T-R5 (25-yr), tornado. Commands
in §4.

### 2.3 Fixed-rig T1.7 re-measurement (FF-2C-rig, this session)

The §2.2 follow-up landed. `run_driver_battery.py`'s `_net_cone_scalar` now
(a) preserves `demand_curve` / `net_cone_curve_per_kw_yr` / `seasonal_rbdc` and
scales the **curve** anchor — registry **and** the per-delivery-year
`MARKET_DESIGN_VINTAGES` anchors, whose vintage override (`resolve_demand_curve_
vintage`) otherwise governs every threaded model year and would silently bypass
a registry-only scale; and (b) the battery reports the **economic** retirement
channel (RC-1B ledger `retirements[].reason`) separately from exogenous
(confirmed + announced) exits. A companion cache-namespace fix (`make_rung_specs`
gives each rung its own solve cache) was required: T1.7's scalar is a
worker-level module patch stripped from the ScenarioConfig, so all rungs share
one `config.cache_key()` and a shared solve cache pinned every dispatch-derived
metric to rung 0 — the §2.2 single-`lw_price`/single-`co2` signature. Rig repair
only, no behavioural tuning (rules 1/13); the curve scaling is verified to move
the PJM curve price **exactly 2.0×** at 2× (vs the old patch's flat fixed-
fallback ~1.43×), with the VRR shape / vintage structure intact.

**PJM T1.7 (flipped, 2026–2030, legacy bins), net-CONE {0,1,2}×:**

| metric | 0× | 1× | 2× | gate |
|---|--:|--:|--:|---|
| **economic_retired_thermal_gw** | **0.797** | **0.000** | **0.000** | **T1.7a PASS** (↓) |
| exogenous_retired_thermal_gw | 4.575 | 4.575 | 4.575 | flat by construction |
| retired_thermal_gw (old total) | 11.836 | 9.336 | 4.575 | confounded (net of entry) |
| entry_thermal_gw | 9.38 | 8.25 | 10.32 | — |
| lw_price ($/MWh) | 39.68 | 39.46 | 39.22 | now varies (was pinned) |
| co₂ (Mt) | 1936.1 | 1933.4 | 1937.4 | now varies |

The ladder now **moves on the net-CONE-sensitive channel**: economic
retirements fall 0.797 → 0 GW as the capacity anchor goes 0× → 1× (T1.7a PASS,
`monotone_down`), while the exogenous channel is **exactly flat** (4.575 GW) —
confirming the split isolates the sensitive component the old cumulative total
masked (the total itself, 11.836 → 4.575, is confounded: it nets same-fuel
entry, which is why §2.2 called it net-CONE-invariant *and* why it is the wrong
metric to gate on). Dispatch metrics now vary per rung (lw_price 39.68 → 39.22),
proving the cache fix — under the shared cache they were all pinned to rung 0.
**ERCOT T1.7 is byte-identical across all three rungs** (economic / exogenous /
total retire 0, entry 17.31, lw 29.516, co₂ 1092.651, rm 0.0653) → **T1.7b
PASS** — the energy-only negative control (net-CONE inert) holds under the fixed
rig, so the movement above is a genuine curve-ISO signal, not a rig artifact.

**What still bounds it (report what moves, claim nothing that doesn't).** The
effect **saturates by 1×** — 1× and 2× are identical on every retirement metric.
This is the §2.2 position caveat made visible: PJM sits at/past its VRR curve's
1.045 zero-cross (flip memo §2, position ~1.29–1.36), so beyond a modest anchor
the position-limited curve payment retains no further units. The fixed rig now
lets the ladder cleanly **see** the net-CONE → economic-retirement response
(~0.8 GW at the 0×→1× step) **and** its saturation; but the **quantitative**
magnitude stays gated on the BLK-3 requirement/position half (R2/R3,
FF-2B-adjacent). Until that lands, the 0×→1× step is the informative directional
signal, **not** a forecast of PJM's net-CONE retirement elasticity — exactly the
flip memo's measured caveat, now measurable rather than masked.

---

## 3. Blocker-register impact

- **BLK-4** (`capacity_market_clearing` default-off and unflippable) →
  **RESOLVED** for PJM/MISO/CAISO/NEISO. The gate is ON by default; NYISO
  remains its named exception (R5a).
- **BLK-3** (accreditation basis; the −22% anchor half) → the **anchor** half
  is **CLOSED by R4** (PJM 100→77.431 UCAP, and each ISO's fixed anchor now on
  its published basis). The requirement/position half continues under the
  accreditation-basis lane.
- **BLK-9** (fixed capacity payment ≥1.3× GFC → fossil exit impossible) →
  **no longer the active default** for the four flipped ISOs: they price on the
  curve, so the flat-payment arithmetic that made exit impossible is off the
  default path. The curve-ON over-fire (BLK-10) is the successor open item, per
  §2.1. NYISO (unflipped) still carries BLK-9 in the default path.

---

## 4. Re-run status & continuation

Rule-12 discipline: every flipped ISO takes the CAMPD per-plant path, so
capacity hindcasts run **one at a time** (per-plant multi-zone). The driver
battery + tornado force legacy heat-rate bins (documented fidelity trade) and
are lighter.

| Re-run | Command | Status |
|---|---|---|
| T1.7 net-CONE ladder, PJM (flipped) | `run_driver_battery.py --iso PJM --tests T1.7` | **DONE (fixed rig) — §2.3** (T1.7a PASS) |
| T1.7 ERCOT negative control | `run_driver_battery.py --iso ERCOT --tests T1.7` | **DONE — §2.3** (T1.7b PASS, byte-identical) |
| PJM hindcast re-score (curve-ON = flipped default) | `run_capacity_hindcast.py --iso PJM --vintage 2020 --fuel-variant realized --capacity-market-clearing --out-dir results/hindcast/pjm-2021-2025-curve-ff2c` then `register_hindcast.py --bundle …` | see §2.2 |
| MISO hindcast re-score | `… --iso MISO --capacity-market-clearing --out-dir results/hindcast/miso-2021-2025-curve-ff2c` | pending (per-plant, sequential) |
| CAISO hindcast re-score | `… --iso CAISO --capacity-market-clearing --out-dir results/hindcast/caiso-2021-2025-curve-ff2c` (pricing no-op; measures the R4 88.08 anchor) | pending |
| NEISO hindcast re-score | FF-2B `neiso-2021-2025-curve` already measured; R4 changed only the FIXED anchor, so the curve-ON leg dispatch is unchanged — re-register if a fresh bundle is wanted | reuse FF-2B curve leg |
| Equilibrium T-R5 rows | `run_equilibrium_battery.py` on flipped defaults | pending (25-yr NEISO full horizon — heavy) |
| Tornado capacity entries | `run_sensitivity_tornado.py --iso PJM` | pending |

All fresh runs register on the **forecast-validation** dashboard
(`register_hindcast.py` → `frontend/data/hindcast/…`, the namespace outside the
backcast CI gates — plan §1.5); NEVER the backcast registry. Hindcasts run
2021→2025 (2021 seed inside the rule-22 `{2021}` allowance, 2022 bridged, 2023–
2025 scored); the forecast-validation namespace is outside the backcast
quarantine CI, and the {2021} seed is carved out of the ≤2021 quarantine
(§7.4), so the re-scores are legal for all four flipped ISOs (matching the
RC-1A PJM/MISO precedent) despite only NEISO carrying a calibration-complete
marker.

---

*Produced 2026-07-20 (FF-2C, RC-3A execution). Flip + R4 landed as commit
`dbbae9c`; forecast-mode only; no backcast keeper, dashboard artifact, or
holdout year touched (rules 1/13/14/22/27).*
