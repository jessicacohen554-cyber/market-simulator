# ERCOT on-line-capacity envelope (G-22 commitment thinness) — REJECTED PROBE

**Date:** 2026-07-07
**Branch:** `claude/ercot-commitment-thinness-fix-0g2yob`
**Status:** mechanism BUILT (default-off, ERCOT-gated, LP-linear), identification
gate PASSED, full-span A/B solved and registered — **RESULT: REJECTED PROBE.**
Keeper stays `ercot34-stage4-overlay-off`; `ercot_online_capacity_envelope`
stays default-off. G-22 **not struck** — structural conclusion #2 (online-
capability structure) is now tested and over-fires; the diagnosis and forward
path are below.
**Reads first:** `docs/FINDING-ercot-priceshape-2026-07.md` §3 / structural
conclusion #2 (the ~3.2 GW online-capability wedge this builds), the ercot34
calibration-log entry (the G-22 fold), `docs/handoffs/ercot-g22-offer-surface-
2026-07.md` (the rejected offer-surface, remedy (a); this is remedy (b)), and
`docs/handoffs/ercot-rtolcap-forward-2026-07.md` (the measured RTOLCAP anchor).

---

## 1. The mechanism (`ercot_online_capacity_envelope`, default-off)

The G-22 fold established that the missed 2023 tail is **energy-offer-carried
scarcity against a P1 online-capability wedge** — in the missed hours the model
carries ~3.2 GW of spare sub-$200 energy headroom BEYOND the measured RTOLCAP
online-reserve capability, so scarcity never tightens. `ercot_reserve_supply_cap`
already caps the cleared RESERVE at RTOLCAP (`Σ R ≤ RTOLCAP`), but the ENERGY
side of the co-opt's shared headroom still draws on the full-fleet capacity, so
the energy dual sits at ~$45 where SCED cleared $600+.

**This lever adds, per shared-headroom tier, a system-wide LP row**

    Σ_z Σ_{g∈E_h∩z} P[g] + Σ_z Σ_{p∈Prod_h} R[p,z]  ≤  online_cap_env(t)

where `online_cap_env` is the committed on-line HSL of the tier's responsive
classes (`scarcity.ercot_online_capacity_envelope_mw`), so the LP cannot dispatch
OR reserve more thermal than the real system had on-line. Applied to the
all-responsive tier only (the fast/spinning tier keeps the RTOLCAP reserve cap).
Unlike the flat reserve cap, the ENERGY term makes it **condition-responsive**:
inert in slack hours, binding only in the high-energy tight hours, tightening
reserve into the ORDC band with **no offer-height change** — the price rises via
the co-opt reserve-shortage channel (rule #1). The whole thing is pure LP (no
MIP, no P2), vectorized (`sp.kron`, no hour loop), and byte-identical when off.

`online_cap_env(t) = deliv × Σ_c ERCOT_ONLINE_CAP_SHARE_c(nl_decile, season) ×
cap_c(t)` — the CAMPD-measured committed on-line HSL fraction × the model fleet's
responsive-class capacity (summer-derated), derived by
`scripts/derive_ercot_rtolcap_forward.py --emit online-cap-constant`. Rule #23:
re-derives only on a CAMPD / measured-RTOLCAP source-data update, never a residual.

## 2. Identification gate — PASSED (in the binding regime)

`scripts/validate_ercot_online_capacity.py`: the envelope's headroom remainder
(`online_cap_env − CAMPD on-line gross + storage AS`) must reproduce the measured
RTOLCAP series. The **binding regime** (top-30% net-load, where the envelope is
not slack) is the load-bearing gate:

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| binding-regime headroom vs measured RTOLCAP | **−1%** | **+2%** | **−1%** |
| coverage (annual, RTOLCAP÷AS-req, anti-F1) | ~2× | ~2× | ~2× (not the 1.0× artifact) |

`deliv_env = 1.0830`, fit to reproduce the measured on-line HSL MW quantity
(CAMPD gross + measured RTOLCAP) in the binding regime, on the **production cap
basis** (model FleetArrays pmax + summer derate). It is a measured-MW-quantity
fit to the RTOLCAP band, never a price (rules #13/#14/#23). The control arm
confirms the model's unconstrained thermal dispatch ≈ measured CAMPD gross in
these hours (within 0.2–1.4 GW), so the in-LP room reproduces measured RTOLCAP
+ ~1 GW.

**Identification-gate lesson (recorded for the next attempt).** An initial gate
on the ANNUAL MEAN passed while the binding tail was badly under-reproduced — the
first probe (`deliv` fit all-hours, CAMPD-nameplate basis) collapsed the tail
room to ~2 GW and over-fired catastrophically (2023 hub $690, 1574 h>$200). Two
identification bugs were fixed against the measured RTOLCAP quantity (never the
price): (i) fit in the binding regime, not all-hours; (ii) fit on the production
cap basis (model FleetArrays), not the derive's CAMPD-nameplate class cap (which
ran ~20-30% too tight in the LP). The gate now checks the binding regime.

## 3. A/B result (2026-07-07) — REJECTED PROBE, no retune

Full-span 2023–2025, both arms the ercot34 recipe (overlay-off + WS-A forward
supply + the 4 gas-geography flags restored); treatment adds
`ercot_online_capacity_envelope=True`. Registered:
`2026-07-07-ercot41-envelope-off` (control) / `-on` (treatment). Load-weighted
hub LMP vs RT actual:

| year | actual dw | off | on | h>$200 (act/off/on) | in-model EXTREME(top2%) room vs meas RTOLCAP |
|---|---|---|---|---|---|
| 2023 (scarcity) | $48.36 | $46.5 | **$347** | 181 / 90 / 711 | **4.4 vs 8.0 GW (collapsed)** |
| 2024 (current-design) | $26.83 | $27.3 | **$73.1** | 53 / 23 / 132 | 6.7 vs 11.1 GW (collapsed) |
| 2025 (current-design) | $32.49 | $32.5 | $32.6 (inert) | 31 / 1 / 1 | 11.7 vs 11.2 GW (matched) |

Official rubric scores (`calibration_verdict.py`, DA-expressible C3c basis):

| criterion (2023) | arm A (off) | arm B (envelope on) |
|---|---|---|
| C3a price_mean | **PASS** +3.7% | **FAIL** +797% ($433.88 incl. ORDC adder) |
| C3b price_shape NRMSE | FAIL 0.324 | FAIL **13.195** (catastrophic) |
| C3c tail (model/DA-actual) | 92h / 311h = 0.30× (under) | 711h / 311h = 2.29× (over) |

The envelope **flips C3a PASS→FAIL, worsens C3b ~40×, and swings C3c from
under-firing (0.30×) to over-firing (2.29×)** — the "right" tail (the [0.5×, 2×]
band = 155–622 h) sits between the control's under-fire and the treatment's
over-fire, the clean signature of a mechanism that engages too hard.

**Class TWh is essentially unchanged** (D-8 volume-neutral — CC_REGULAR
139.1→139.0, CT_PEAKER 5.9→5.7, ST_GAS 14.4→14.3 in 2023; unchanged to 0.1 TWh
in 2024/25). Unlike the ercot33 offer wall, the envelope moves **no mid-merit
energy off the CAMPD-measured allocation** — it is a pure price mechanism. That
is a genuine structural advantage over the offer-surface remedies.

**Verdict: reject (rules 1/11); do not retune.** The envelope over-corrects in
the tight years — 2023 hub $347 vs actual $48 (7×), 2024 $73 vs $27 (2.7×), both
concentrated in the summer scarcity months (Aug-2023 $1,465, Aug-2024 $379). It
**hurts the current-design years 2024/2025**, which per the pre-committed
evaluation rule (`ercot-g22-offer-surface-2026-07.md` §6.1) is a rejection — and
`deliv_env` is **not** re-swept to recover the level (it is locked by the RTOLCAP
identification; sweeping it to a price would be exactly the fit-first move rule #1
forbids).

## 4. Root cause (why a correctly-identified envelope over-fires)

The over-fire is **not** an identification failure at the binding-regime grain
(±2%) — it is the **extreme-peak (top 2%) room collapse**. In those hours the
model's thermal energy dispatch approaches the on-line-capacity envelope, so the
room `online_cap_env − dispatch` collapses to **4.4 GW (2023) / 6.7 GW (2024)**
where the measured RTOLCAP retained **8.0 / 11.1 GW**. Once the room drops below
the ORDC total-reserve demand span (~10.7 GW), the tariff LOLP×VOLL curve prices
scarcity — and it prices it in far more hours than reality, because reality
retained several GW of on-line reserve in those same hours. The mild year (2025)
never reaches the collapse (extreme room 11.7 > demand) → the envelope stays
inert → no change.

Two coupled contributors:

1. **Share saturation at the absolute peak.** The pooled-median on-line-capacity
   share reproduces the top-30% RTOLCAP but under-states the *committable*
   capacity in the top 2%, where the real system commits ~everything (share →
   ~1.0). A single binding-regime deliverability coefficient cannot fix a SHAPE
   error — it reproduces the top-30% mean while the top-2% room still collapses.
2. **Energy vs the full ORDC-demanded reserve.** The envelope makes energy
   compete with the ~10.7 GW ORDC total-reserve *span* for the on-line capacity.
   Reality held far less reserve (PRC ~5.7 GW in 2023) and the ORDC priced it
   small ($1.84 mean adder). Forcing the model to hold the full span within an
   on-line capacity ≈ RTOLCAP + energy over-prices the shortfall.

## 5. Forward path (not executed — would be the next probe)

- **Extreme-peak-resolved on-line-capacity share.** Re-derive the share with
  finer top-percentile net-load bins (a top-2% bin → share ≈ full commitment),
  so `online_cap_env` reproduces the measured on-line HSL in the extreme tail,
  not just the top-30% mean. A data-driven refinement (rule #13, calibrated to
  the measured RTOLCAP band), NOT price-tuning. **Caveat:** even with the extreme
  tail reproduced, contributor (2) may still over-fire — the ORDC-vs-energy
  competition is the deeper coupling, and the envelope may fundamentally
  over-price when energy is forced to compete with the full ORDC span.
- **Filed structural conclusion.** G-22's two sanctioned remedies are now both
  tested and rejected: (a) offer surface (`ercot-g22-offer-surface-2026-07.md`,
  over-corrects by collapsing offer heterogeneity) and (b) online-capacity
  envelope (this note, over-fires from the extreme-peak room collapse + ORDC
  competition). The C3b/C3c miss remains an open structural gap; the honest
  reading is that neither a taller offer surface nor a thinner online-capacity
  cap, calibrated to measured quantities, reproduces the ERCOT summer scarcity
  tail without over-firing — the wedge is real but sits inside the ORDC/reserve
  demand interaction, which both remedies perturb.

## 6. Files

* `scripts/derive_ercot_rtolcap_forward.py` — `derive_online_capacity()`,
  `_model_class_cap()`, `--emit online-cap-{constant,report}`.
* `src/market_sim/config/constants.py` — `ERCOT_ONLINE_CAP_SHARE`,
  `ERCOT_ONLINE_CAP_DELIV_COEF`.
* `src/market_sim/config/scenarios.py` — `ercot_online_capacity_envelope` flag
  (+ TIER_TAGS).
* `src/market_sim/results/scarcity.py` — `ercot_online_capacity_envelope_mw`.
* `src/market_sim/config/reserve_config.py` — `ReserveDesign.online_capacity_cap`,
  `_ercot_multiproduct_design` wiring, `build_reserve_dispatch_kwargs` mapping.
* `src/market_sim/model/dispatch.py` — `_build_reserve_rows` envelope block +
  `reserve_online_capacity_cap` threaded through `build_constraints` /
  `DispatchModel` / `solve_dispatch` + the balance-dual row-offset accounting.
* `scripts/validate_ercot_online_capacity.py` — the binding-regime identification
  gate.
* `tests/test_ercot_online_capacity_envelope.py` — trivial-case (flag-off no-op,
  condition-responsive prices-on-the-energy-dual, tighter-prices-higher) +
  builder (gated, all-tier-only, rises-with-net-load).
