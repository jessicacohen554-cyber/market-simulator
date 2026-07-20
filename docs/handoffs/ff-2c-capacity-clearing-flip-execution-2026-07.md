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

**Follow-up (routed, not fixed here — rule 6):** update the T1.7 rig to
preserve `demand_curve`/`seasonal_rbdc` and scale `net_cone_curve_per_kw_yr`
for curve ISOs, and to report the *economic* retirement component separately
from exogenous exits, before the net-CONE ladder is informative for a flipped
ISO. This is a `scripts/run_driver_battery.py` change (Opus/Fable, rule 27),
its own small commit. **ERCOT T1.7 is byte-identical across rungs (energy-only
negative control), as expected.**

**Position caveat (compounds #1):** even a curve-preserving rig would find PJM
at a position (~1.29–1.36) past its curve's 1.045 zero-cross → the curve pays
$0 (flip memo §2; P-2A Pass 2). The BLK-3 requirement/position half (R2/R3,
FF-2B-adjacent) must land before PJM's flipped curve prices non-zero. So the
flip is live and correct, but its *quantitative* retirement effect for PJM is
gated on the position fix — exactly the flip memo's measured caveat.

**Hindcast re-scores / equilibrium T-R5 / tornado (per-plant, hours each):**
launched but not carried to completion in this restart-prone session (the
container restarted mid-solve). Exact continuation commands in §4. The
already-published curve-ON evidence (§2.1) stands as the measured post-flip
record until they land.

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
| T1.7 net-CONE ladder, PJM (flipped) | `run_driver_battery.py --iso PJM --tests T1.7` | see §2.2 |
| T1.7 ERCOT negative control | `run_driver_battery.py --iso ERCOT --tests T1.7` | control (energy-only, net-CONE inert) |
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
