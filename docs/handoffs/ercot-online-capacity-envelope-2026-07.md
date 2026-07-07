# ERCOT on-line-capacity envelope (G-22 commitment thinness) — REJECTED PROBE

**Date:** 2026-07-07
**Branch:** `claude/ercot-commitment-thinness-fix-0g2yob`
**Status:** mechanism BUILT (default-off, ERCOT-gated, LP-linear), identification
gate PASSED, full-span A/B solved and registered — **RESULT: REJECTED PROBE.**
Keeper stays `ercot34-stage4-overlay-off`; `ercot_online_capacity_envelope`
stays default-off. G-22 **not struck** — structural conclusion #2 (online-
capability structure) is now tested and over-fires; the diagnosis and forward
path are below.
**2026-07-07 (later, second session):** the §5 forward path was EXECUTED —
the extreme-peak-resolved variant (`ercot_online_capacity_envelope_extreme`,
ercot43 A/B on the ercot42 keeper recipe) — and is **also REJECTED**; §7
records it. The §5 caveat is CONFIRMED: with the extreme tail reproduced on
the measured data, the over-fire persists through the ORDC-span-vs-energy
competition. The envelope family (base + extreme) is now exhausted as a G-22
remedy; keeper stays `ercot42-wtx-curtailment-driver`.
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

---

## 7. The §5 forward path EXECUTED — extreme-peak-resolved variant (ercot43) — REJECTED PROBE

**Date:** 2026-07-07 (second session). **Branch:**
`claude/ercot-g22-extreme-peak-w2d-t6lshe`. Registered:
`2026-07-07-ercot43-extremeenv-off` (control = ercot42 keeper recipe replayed
at HEAD; doubles as the zero-forcing ablation twin) /
`2026-07-07-ercot43-extremeenv-on-probe` (treatment = + single delta
`ercot_online_capacity_envelope_extreme=True`). Keeper `ercot42` untouched.

### 7.1 Mechanism (built, default-off, mutually exclusive with the base flag)

Identical LP row; the driver resolution changes exactly as §5 filed, plus the
level completion §5's identification demanded:

1. **Shape** — `ERCOT_ONLINE_CAP_SHARE_EXTREME` resolves the committed on-line
   HSL fraction on **14 net-load bins** (deciles 0–8 + five 2-pp sub-bins of
   the top decile, `scarcity.ercot_online_cap_extreme_bin`). The measured CAMPD
   commitment saturation rises through the sub-bins (summer CT_PEAKER
   0.40→0.61, ST_GAS 0.83→0.97) where the decile-9 median collapsed it.
   Sub-bin cells with < 24 pooled hours inherit the parent decile-9 median.
2. **Level** — `ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME`: the scalar
   deliverability becomes a **per-bin profile** (same ratio-of-means
   identification, resolved on the share's own axis), fit to the measured
   thermal on-line HSL identity `CAMPD gross + (RTOLCAP − storage AS − LR
   credit)` — the LR netting is a target correction vs the base fit (the
   keeper LP credits the measured LR series against the requirement, so a
   thermal cap keeping LR capability would double-count). Monotone-rising
   1.05→1.10 through the binding bins — the measured capability margin
   (non-CEMS units + telemetered HSL above the summer-derated nameplate)
   that grows toward the extreme peak, which one scalar provably cannot span.

**Identification gate — PASSED where ercot41's design could not**
(`validate_ercot_online_capacity.py --extreme`): binding regime −0/+3/−2%
(2023/24/25), pooled top-2% EXACT (10.19 vs 10.19 GW), coverage 2.15×.
Recorded per-year extreme-tail ledger: **2023 −23% / 2024 −2% / 2025 +18%** —
the cross-year capability spread at a fixed within-year rank (2023's scarcity
summer mustered more absolute capability than 2025's milder tail), which a
year-symmetric pooled coefficient cannot span without year-pinning (rule 13).

### 7.2 A/B result — REJECTED, no retune (rules 1/11; §6.1 pre-committed rule)

Both arms the ercot42 keeper recipe at HEAD, single delta = the extreme flag.
The control reproduces the keeper's registered verdict exactly (C3a +8.9/+6.6
caveat, C3b 0.256/0.252, C3c 103/25/1 vs DA 311/68/23) — the keeper-at-HEAD
reproduction check. Demand-weighted settled price (LP dual + ORDC adder +
RTORDPA overlay):

| year | actual RT dw | off (control) | on (treatment) | h>$200 (off/on) | on-arm top-2% room+stor+LR vs meas RTOLCAP |
|---|---|---|---|---|---|
| 2023 | $48.36 | $56.67 | **$455.18** | 106 / 991 | 5.41 vs 7.89 GW (still collapsed) |
| 2024 | $26.83 | $29.19 | **$47.71** | 27 / 55 | 9.65 vs 11.04 GW (−13%) |
| 2025 | $32.49 | $33.99 | $34.04 (≈inert) | 2 / 2 | 15.26 vs 11.64 GW (slack → inert) |

Official rubric v2.2 (`calibration_verdict.py`, energy-only LMP / DA-expressible
C3c basis):

| criterion | arm A (off = keeper@HEAD) | arm B (extreme envelope) |
|---|---|---|
| C3a mean LMP | CAVEAT commercial-band (+8.9% / +6.6% / +3.2%) | **FAIL** (2023 **+708%**, 2024 **+61.4%**) |
| C3b shape NRMSE | FAIL 0.256 / 0.252 / 0.085 | FAIL **10.579** / **1.663** / 0.085 |
| C3c tail (model vs DA actual) | FAIL 103/311 (0.33×), 25/68 (0.37×), 1/23 | FAIL 989/311 (**3.18×**), **53/68 (0.78×) PASSES** — RT companion 53/53 exact, 1/23 unchanged |
| C1 / C2 / C4 / C5a / C5c | PASS / CAVEAT / PASS / PASS / PASS | identical — no volume/dispatch regression |

The treatment over-fires 2023 even harder than ercot41's base envelope ($455
vs $347 preview; C3a +708% vs +797%) and lifts 2024 (+61.4% official) — a
current-design year — which under the §6.1 pre-committed rule is a rejection
on its own. 2025 stays inert (slack envelope), exactly as the identification
ledger predicted. **The C3c-2024 leg individually flips FAIL→PASS (0.37×→0.78×
DA; the RT companion lands 53/53 exact)** — the mechanism produces the RIGHT
tail-hour count in the year whose extreme-tail identification is right (−2%),
at the wrong intensity. D-8 class volumes are neutral: CC_REGULAR 141.7→141.8,
ST_GAS 14.9→14.8 TWh (2023); 2024/25 unchanged at 0.1 TWh grain — a pure price
mechanism, like the base envelope.

### 7.3 The failure signature (what the extreme resolution PROVES)

* **The room collapse is no longer an identification artifact.** The envelope
  is +3.0 GW looser than the base in 2023's top-2% (60.0 vs 57.0 GW) and
  reproduces the pooled measured capability exactly. Loosening it released
  ~+4.9 GW of previously-suppressed thermal dispatch in those hours (52.6 →
  57.5 GW — the phantom-scarcity release working as designed), yet the room
  still landed at 2.56 GW thermal (5.41 incl. stor+LR) vs measured 7.89 —
  because with fixed demand the extra capability is consumed by energy until
  the ORDC-span competition prices it.
* **2023 fails on BREADTH, not depth**: >$200 hours spread nearly uniformly
  across bins 8–13 (186/135/153/159/173/175 of ~175 h each — ~94% of the top
  ~22% of the year) where reality priced 181 h concentrated in the extreme
  tail. The raw energy dual itself carries it (mean $267, p99.5 $6,383): the
  co-opt makes energy compete with the full ~10.7 GW ORDC total-reserve span
  inside the envelope, while the real 2023 market repeatedly operated ~5 GW
  below that span and the tariff curve priced it small ($1.84 mean RTORPA).
* **2024 is structurally CORRECT and only hot on level**: 47 of its 52 >$200
  hours sit in bin 13 (the top-2%) — the concentration reality shows — with
  the level +78%. The mechanism's shape is right where the capability
  identification is right (2024's extreme ledger: −2%).
* **Recipe compounding (new vs ercot41):** on the ercot42 recipe the WTX
  curtailment driver backfills curtailed West VRE with thermal in exactly the
  congested extreme-peak hours, consuming ~all of the room the extreme
  resolution restored (like-for-like 2023 room 4.63 GW incl. storage vs
  ercot41's 4.4). Any envelope in this family binds harder the more thermal
  the recipe dispatches — the two mechanisms compound in the tail.

### 7.4 Structural conclusion for G-22 (the honest answer, sharpened)

The §5 caveat is **confirmed as the root cause**: contributor (2), the
ORDC-vs-energy competition, survives a fully-identified envelope. Both
G-22 remedies are now exhausted across three probes — (a) the offer surface
(ercot33/37, collapses offer heterogeneity), (b) the on-line-capacity envelope
at base grain (ercot41, room collapse) AND at extreme-peak-resolved grain
(ercot43, this section). No supply-side cap that reproduces the measured
on-line capability can price the 2023 tail correctly while the co-opt demands
energy + the full ORDC total-reserve span inside it: the remaining structural
object is the **reserve-demand side** — how much of the ORDC span the
scarcity-year market actually held as priced reserve (PRC ran ~5.7 GW where
the span is ~10.7 GW) — i.e. the deployment/held-reserve representation, not
offer heights and not on-line capability. Filed, not built (rule 1: the
mechanism must be real market structure, and any such change re-opens the
ORDC-family design that rule 26 froze; it needs its own owner-sanctioned
design round).

### 7.5 Files (delta vs §6)

* `scripts/derive_ercot_rtolcap_forward.py` — `derive_online_capacity_extreme()`,
  `--emit online-cap-extreme-{constant,report}`, `N_BIN_EXTREME`,
  `MIN_CELL_HOURS_EXTREME`.
* `src/market_sim/config/constants.py` — `ERCOT_ONLINE_CAP_SHARE_EXTREME`,
  `ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME` (+ identification block comment).
* `src/market_sim/config/scenarios.py` — `ercot_online_capacity_envelope_extreme`
  (default-off, TIER_TAGS, `__post_init__` mutual exclusion with the base flag).
* `src/market_sim/results/scarcity.py` — `ercot_online_cap_extreme_bin()` +
  the extreme branch of `ercot_online_capacity_envelope_mw`.
* `src/market_sim/config/reserve_config.py` — gate extended to either flag.
* `scripts/validate_ercot_online_capacity.py` — `--extreme` mode (+ pooled
  top-2% gate, LR add-back).
* `tests/test_ercot_online_capacity_envelope.py` — bin-helper equal-counts /
  top-2%, both-flags-off None, mutual-exclusion raise, extreme-alone
  activates, extreme-lifts-top-2%-room-vs-base.
