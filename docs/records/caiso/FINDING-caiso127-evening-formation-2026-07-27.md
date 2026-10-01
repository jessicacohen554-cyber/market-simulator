# FINDING — caiso-127: the evening premium is not primarily under-priced, it is ARBITRAGED FLAT — the model's battery fleet is interior-discharging in BOTH the overnight and the evening window, and on those days LP optimality pins the two lambdas equal (measured gap +2.64/+0.36/+0.41 $/MWh against a no-arbitrage prediction of 0.00)

**Keeper `2026-07-27-caiso-126-ror-split` UNCHANGED. Measurement-only session
(owner gate: instruments at most) — no mechanism armed, no solve, no A/B,
nothing registered.** TASK 3 is NOT executable: it is conditional on an
in-session owner grant on a specific construction and no such grant exists in
this session. The owner ask is TASK 2 below (§6), filed not built.

Instrument (committed): `scripts/probes/_caiso127_evening_formation.py` —
sections A–E, every number below reproducible from the two committed caiso-126
bundles plus raw EIA-930 / CAMPD CEMS / the committed actual-LMP reference and
a no-LP `run_year(fleet_only=True)` fleet reconstruction. No LP is built or
solved.

Bounds caveat, stated up front: the slim keeper bundle carries no `floors/`
npz, so §C/§E use the fleet reconstruction's own P0 `min_gen` as the lower
bound. The P0→P1 seam bridge floors (CAISO RA must-offer) are not in it, so
"free MW above a floor" is an **upper** bound on genuinely free capacity. Every
upper cap (`pmax × availability`) and every offer price (`mc_base`, the
assembled P0 objective the LP solved on) is exact, and the §B/§C/§E
conclusions rest on the caps and the offers, not on the floor.

---

## §1 — the ladder, re-based on the PROMOTED keeper (§A)

The prompt's context numbers (+9.0/+5.0/+2.8 vs implied real +15.6/+9.9/+5.3)
were measured in FINDING-caiso125 §4b on the caiso-124 control with the
implied-real side reconstructed from the caiso-102 keeper's ladder residuals.
Measured directly on the promoted keeper against the committed RT print (arm B,
CA demand-weighted P1 lambda; arm A in brackets):

| year | overnight model | actual | resid | evening model | actual | resid | spread model | spread actual | compression |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 57.61 (57.39) | 57.69 | **−0.09** | 66.51 (66.42) | 71.67 | **−5.16** | +8.90 (+9.03) | +13.97 | +5.07 (64 %) |
| 2024 | 40.42 (40.30) | 38.69 | **+1.73** | 45.27 (45.28) | 47.62 | **−2.35** | +4.85 (+4.98) | +8.93 | +4.08 (54 %) |
| 2025 | 42.83 (42.76) | 40.02 | **+2.81** | 45.59 (45.54) | 45.19 | **+0.41** | +2.76 (+2.78) | +5.17 | +2.40 (53 %) |

The compression reproduces (the model carries 53–64 % of the measured spread),
and the arm A/B agreement re-confirms the family's lambda-neutrality. **But the
charter's framing — "compressed evening premium", i.e. an evening
under-price — is only 2023's story.** By 2025 the model's evening level is
*right* (+0.41) and the entire compression is an **overnight OVER-price**
(+2.81). 2024 is split (+1.73 overnight / −2.35 evening). Any candidate
scoped to lift the evening alone therefore cannot fix 2025 and would break its
already-passing evening level: the lane's target must be the **spread**, not
the evening level.

## §2 — the load-bearing finding: the spread is arbitraged flat by storage (§B)

The keeper's LP storage is `SOC[t] = SOC[t−1] + η_c·Chg − Dis/η_d`, RTE 0.85
(`ScenarioConfig.storage_rte_4hr`), battery vom 5 $/MWh, `battery_dispatch_adder`
0.0, ε 0.001 (CLAUDE.md #9). Two LP-optimality facts follow directly:

- If the fleet is **interior in discharge in two windows of the same SOC
  episode**, the marginal value of stored energy (`μ`) is common to both and
  `λ = vom + μ` in each ⇒ **λ_evening − λ_overnight = 0**.
- If the overnight is instead a **charging** window and the evening an interior
  discharge, the premium must clear the round-trip wedge
  `λ_on/η + vom − λ_on` = **+15.17 / +12.13 / +12.56 $/MWh** at the model's own
  overnight levels.

Measured on the keeper:

| year | fleet MW | overnight net | evening net | at evening discharge cap | evening utilisation | cycles/day |
|---|---|---|---|---|---|---|
| 2023 | 7 602 | **+157** MW | +2 547 | 0.150 | 0.54 | 0.36 |
| 2024 | 11 355 | **+188** MW | +4 154 | 0.077 | 0.55 | 0.45 |
| 2025 | 15 249 | **+453** MW | +5 404 | 0.057 | 0.56 | 0.50 |

The fleet is **neither power-bound nor energy-bound**: it sits at 54–56 % of
its (caiso-99-anchored) evening discharge cap, touches that cap in only
5.7–15.0 % of evening hours, and turns 0.36–0.50 cycles/day against its own
energy capability. **The overnight is a DISCHARGE window in the model** — net
+157/+188/+453 MW, discharging in 30/31/43 % of overnight hours and charging in
only 9/10/5 %. So the operative bound is not the round-trip wedge at all; it is
the degenerate **discharge-to-discharge zero wedge**.

**The KKT test fires.** On the days with strictly-interior active discharge in
*both* windows the measured evening−overnight gap is

| year | pinned days | gap on pinned days | LP's own prediction |
|---|---|---|---|
| 2023 | 192 / 365 | **+2.64** (median +1.54) | 0.00 |
| 2024 | 197 / 365 | **+0.36** (median +0.29) | 0.00 |
| 2025 | 276 / 365 | **+0.41** (median +0.25) | 0.00 |

and the stratification is the whole compression:

| year | | pinned days | not-pinned days |
|---|---|---|---|
| 2023 | model / actual spread | +7.36 / +13.66 (54 %) | +10.60 / +14.32 (74 %) |
| 2024 | model / actual spread | +2.30 / +4.92 (47 %) | +7.85 / +13.63 (58 %) |
| 2025 | model / actual spread | **+1.69 / +4.87 (35 %)** | **+6.11 / +6.09 (100 %)** |

**On the 89 non-pinned days of 2025 the model reproduces the measured spread
essentially exactly (+6.11 vs +6.09).** The residual there is a pure level
offset (overnight +3.04, evening +3.06 — equal, so the *shape* is right). The
compression is created on the pinned days and nowhere else in 2025; in 2023/24
the pin explains the larger half and a smaller second channel survives on the
non-pinned days (evening resid −2.54 / −3.92 — §4's supply-rung defect).

The dose–response across the fleet build-out is the cleanest corroboration:
pinned-day share 0.53 → 0.54 → 0.76 as the fleet goes 7.6 → 11.4 → 15.2 GW,
against a model spread of +8.90 → +4.85 → +2.76 (measured +13.97 → +8.93 →
+5.17). The model over-compresses *increasingly* as the battery fleet grows.

**Consequence for the lane (the reason this is the load-bearing finding).**
On a pinned day the premium is a *fixed point of the storage arbitrage*, not of
the supply stack. Steepening the evening supply rung raises λ_evening, the
unbound battery immediately shifts discharge out of the overnight into the
evening, and the two lambdas re-equalize at a **higher common level** — the
spread does not open, and the overnight over-price gets worse. That is exactly
the caiso-113/114 C3a-guard failure mode (an evening over-price with no spread
gain), and it makes the C3a guard a *predictable* consequence of any
supply-side-only evening candidate rather than bad luck. **The storage conduct
is the prerequisite, not a co-symptom.**

**Which technology? RESOLVED — it is the BATTERY fleet (§B2, gate D0).** The
KKT argument is technology-blind, but which technology is interior decides
which mechanism family is admissible at all: the caiso-99 shape anchor binds
batteries only, so the LP's **2 078 MW / 20 776 MWh of pumped storage** is its
one entirely unrestrained arbitrageur, and the aggregate overnight net
(+157/+188/+453 MW) sits inside PS's power range. The committed slim bundle
could not separate them (the gap FINDING-caiso125 §6.4 flagged); this session
added the sidecar that does (`hourly/storage_<year>.parquet`, per-tech
charge/discharge, write-only and solve-invariant) and replayed the keeper to
produce it — the replay reproduces the committed bundle **digit-for-digit**
(class dispatch max |Δ| 0.000 MW over 122 640 rows and zonal price max |Δ|
0.0000 $/MWh over 61 320 rows, every year), so the sidecars are the keeper's
own and are committed into its `hourly/`.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| overnight net — **li_ion** | +98 MW (discharging 0.29 of h) | +104 (0.28) | +365 (0.41) |
| overnight net — pumped storage | +58 MW (0.05) | +85 (0.08) | +89 (0.06) |
| **pinned days — li_ion** | **140/365 (0.384)** | **175/365 (0.479)** | **244/365 (0.668)** |
| pinned-day gap — li_ion | +2.45 | +1.62 | +1.27 $/MWh |
| pinned days — pumped storage | 27/365 (0.074) | 48/365 (0.132) | 28/365 (0.077) |
| pinned-day gap — pumped storage | +5.71 | +0.48 | −5.18 $/MWh |

**The battery fleet carries the pin and pumped storage does not.** The battery
pinned-day share rises 0.384 → 0.479 → 0.668 with the build-out, on a gap that
tightens toward zero (+2.45 → +1.27); PS's share is 0.074–0.132 with no trend
and a gap that does not converge (+5.71 / +0.48 / −5.18, small-n noise). PS
discharges overnight in only 5–8 % of hours against the battery's 28–41 %, so
the sustained interior-overnight-discharge *pattern* — the thing the KKT
argument needs — is a battery phenomenon. Gate D0 therefore **passes for the §6
ask as filed**: the battery-side candidate is aimed at the right resource.

## §3 — the storage conduct defect, measured (§B)

Model vs measured (EIA-930 CISO `NG: OTH`; the OTH cell carries a small
non-battery positive residual so the measured side is if anything *over*-stated
— which only widens every gap below):

| year | overnight net (model / meas) | evening net (model / meas) |
|---|---|---|
| 2023 | **+157 / −53** (+210) | +2 547 / +1 640 (+906) |
| 2024 | **+188 / +5** (+184) | +4 154 / +3 122 (+1 032) |
| 2025 | **+453 / +267** (+187) | +5 404 / +4 361 (+1 043) |

**The model over-discharges the overnight by +210/+184/+187 MW** — a remarkably
constant offset — which is what converts the overnight from a charge/idle
window (reality: net −53/+5/+267, with a measured charging trough at hod 1–4 in
every year) into a discharge window and arms the pin. The keeper's only
battery-side restraint is the caiso-99 `caiso_storage_shape_anchor`, which is a
one-sided **p95 discharge CAP** (overnight 2 830 / 2 922 / 3 521 MW). A p95 cap
cannot correct a mean-*sign* error: the model's overnight discharge is 5–11 %
of that cap, so the anchor never binds there and never will.

**Position, not throughput — and the two point opposite ways.** The table above
is a *position* comparison on impure sides: the model series is the aggregate
net (battery **plus** PS) and the measured series is EIA-930 `NG: OTH` (a *net*
cell that understates gross battery throughput). On the clean battery-only
basis now available from the D-0 sidecar, the annual comparison **inverts**:
model li_ion discharge **4.06 / 7.62 / 11.46 TWh** against the measured LESR
RTD schedules' **5.67 / 10.04 / 12.06 TWh** (the caiso-74 follow-up's basis) —
the LP **under**-cycles the battery by 28 / 24 / 5 %, which is why
`battery_dispatch_adder` stays 0.0 for CAISO and why the caiso-100/101 positive
adder was rejected on its throughput guard.

So the two readings are not in conflict; together they are the diagnosis: **the
model's battery moves too little energy overall and places too much of what it
does move in the overnight.** The defect is the overnight net POSITION, not the
annual volume — the distinction the §6 ask is built on, and the reason every
volume-priced instrument in §6's refuted list is aimed at the wrong quantity.
On the battery-only basis the overnight over-discharge is
**+151 / +99 / +98 MW** (model li_ion +98/+104/+365 vs measured −53/+5/+267).

## §4 — the supply side: the marginal rung, and what would have to steepen (§C/§D/§E)

**The evening marginal rung is a CC_REGULAR / import tie on a near-continuous
stack.** An offer brackets lambda (±0.50 $) in 96–97 % of evening hours; the
free capacity sitting exactly at lambda is, per year:

| year | at lambda (MW/h) | CC_REGULAR | import | CT_PEAKER | next rung above lambda (median) |
|---|---|---|---|---|---|
| 2023 | | 255 | 256 | 75 | **+0.59 $/MWh** |
| 2024 | | 403 | 159 | 38 | +0.58 |
| 2025 | | 458 | 225 | 16 | +0.59 |

The overnight window is set by the *same two classes* (2024: CC_REGULAR 1 028 /
import 1 027 MW at lambda) — which is the structural reason the two windows'
prices are so easily equalized: there is no distinct evening rung. The
steepening requirement (§E): to lift lambda by the year's compression delta the
`(λ, λ+δ]` band holds **1 856 / 1 444 / 867 MW/h** of free capacity that must
be called or re-priced through — 45 / 33 / 19 % of the model's own evening
import.

**Reality's implied stack calls the peakers; the model calls more CC (§D).**
Evening MW, model vs CAMPD CEMS:

| year | CC_REGULAR | CT_PEAKER | gas total | actual RT ≥ the model's cheapest available CT offer | model λ ≥ that rung |
|---|---|---|---|---|---|
| 2023 | +578 | **−561** | +399 | 0.442 | 0.334 |
| 2024 | +572 | **−714** | +451 | 0.204 | 0.130 |
| 2025 | +431 | **−241** | +561 | 0.131 | 0.084 |

The evening gas **volume** is close (+399/+451/+561 MW); the **composition** is
not. Reality runs 241–714 MW more CT_PEAKER in the evening and reaches/exceeds
the CT rung 1.3–1.6× as often as the model. The magnitude of the missing CT
energy is the same order as the §E band capacity — i.e. the supply-side half of
the premium is exactly "the model serves the evening from the flat
CC_REGULAR/import continuum instead of climbing onto the CT step".

This is the second, smaller channel §2 isolates on the non-pinned days
(2023/24). It is **not** the whole answer and, on the pinned days, fixing it
alone changes the spread by construction ~0.

## §5 — what this closes and what it re-opens

- **Closed as a framing:** "the evening premium is under-priced" — true only in
  2023; 2025's compression is an overnight over-price at a correct evening
  level (§1).
- **Closed as a first move:** any evening-scoped supply-side repricing
  (including the caiso-114 refinement the charter nominated as the leading
  candidate) as a *stand-alone* fix. On 53–76 % of days it is arbitraged into
  the overnight by construction (§2), and it re-runs the caiso-113/114 C3a
  failure with a mechanism now identified in advance. It stays admissible only
  as the **second** delta, after the storage pin is addressed.
- **Consistent with, and sharper than, caiso-105:** the evening λ is indeed
  hub-equalized to a WECC node. §2 adds what caiso-105 could not see: that same
  hub level is then *propagated into the overnight* by the interior battery, so
  the import rung sets both windows and the premium collapses. The two findings
  are one mechanism, not two.
- **Re-opened (new):** the CAISO storage conduct as a price-formation object.
  The keeper's only restraint on it is a one-sided p95 discharge cap that cannot
  bind where the defect lives (§3), and pumped storage carries no restraint at
  all. This is the caiso-127 owner ask (§6).

## §6 — the owner ask (TASK 2), filed not built

Full design memo:
`docs/handoffs/caiso-127-storage-arbitrage-ask-2026-07-27.md`.

**Surviving candidate: the DA/RT allocation on the DISCHARGE side** — the
two-sided rule-19 `[R-ONE-MECH]` reconciliation of M1
(`caiso_charge_allocation_schedule`, the owner-granted caiso-103 ask executed at
caiso-104). Same committed source (the CAISO Daily Energy Storage Report
`market_output` LESR rows), same Fourier-Motzkin per-day floor construction
already in `model.lp.rows._build_storage_alloc_rows`, discharge VOLUME left fully
endogenous, zero new free parameters. It targets §2's defect directly: floors
that bind on the measured evening share leave less of the day's energy free to
discharge overnight.

Closed in the memo so the ask is not a redo — and the closures matter, because
the obvious first guesses are all already refuted:

- **The entire AS-award family.** `caiso_storage_as_reservation` was built and
  A/B'd at **caiso-74** and measured *ex-ante inert* in both legs (the power
  derate sits 0.9–3.7 GW above the LP's own maximum hour; the SOC sustain floor
  is three orders of magnitude below the binding surface). The memo adds the
  third form — the reg-down/directional one — and refutes it by arithmetic on
  the curated award series (`data/clean/storage-as-awards`, re-curated this
  session): the overnight upward award is 334–713 MW against 2.1–3.1 GW of
  remaining discharge headroom, and a net-*discharging* battery satisfies a
  reg-down award by backing off. Rule 13 names "a measured ancillary-service
  power reservation" as an admissible input, and it is — it simply does not
  bind this fleet.
- **A positive `battery_dispatch_adder`** — derived at $14.25 and REJECTED at
  **caiso-100/101** on the two-sided ±15 % throughput guard. It is the wrong
  instrument regardless: §3's target is the overnight *position*, and a
  throughput price moves *volume*.
- **A cycle-count cap** — slack by arithmetic at 0.36–0.50 cycles/day.
- **Loosening or re-deriving the caiso-99 envelope** — rule 21
  `[R-FROZEN-DERIVE]`, and useless: the model uses 5–11 % of the overnight
  discharge cap.

Derive-first gates D0–D4 (D0 = the §2 battery/PS split, blocking) and the
pre-registered A/B kills are memo §5/§6. The eventual A/B's PRIMARY is the
charter's own test: the keeper's disclosed evening hydro starvation
(−251/−376/−264 MW) heals to within ±150 MW with **no hydro-side change**.

## §7 — DO-NOT-REDO (this lane, additions)

- Re-measuring the ladder / spread / compression on the caiso-126 keeper (§1;
  instrument committed).
- Re-measuring the storage interiority, cycle count, hod profile or the pinned/
  non-pinned stratification (§2/§3) — and in particular re-running the KKT test
  on a fresh solve: the committed sidecars carry it.
- Proposing an evening-scoped supply-side repricing as a **stand-alone**
  candidate (§5) — it is refuted by construction on the pinned days; it may
  only be filed as a second delta behind the storage pin.
- A hydro-side or an offer-curve adder tuned to the spread residual (rule 13):
  the spread is a fixed point of the storage arbitrage on the majority of days,
  so any such adder is fitting a quantity the LP re-equalizes.
- Widening the caiso-99 p95 discharge envelope, or re-deriving its percentile
  against this residual (rule 21 `[R-FROZEN-DERIVE]`): §3 shows the anchor is
  slack by 89–95 % where the defect lives, so its level is not the lever.
