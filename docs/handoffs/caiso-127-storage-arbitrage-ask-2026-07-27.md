# caiso-127 owner ask — the evening–overnight premium is pinned by the model's own storage arbitrage; the surviving candidate is the DA/RT allocation on the DISCHARGE side

**Status: FILED, NOT BUILT.** This is the TASK-2 design memo of
`results/calibration/FINDING-caiso127-evening-formation-2026-07-27.md`. Nothing
in it is armed, no A/B was run, the keeper
(`2026-07-27-caiso-126-ror-split`) is unchanged. Building any of it requires
an in-session owner grant on a specific construction (the session gate), and
§5's derive-first checks must pass *before* the grant is worth giving.

---

## §1 — what changed in the diagnosis

The lane was chartered on "the model compresses the evening premium ~2×;
find the supply-side price-formation fix". FINDING-caiso127 §2 measures the
mechanism instead of assuming it:

- The model's storage fleet is **strictly interior in discharge in both the
  overnight and the evening window on 53 / 54 / 76 % of days** (2023/24/25) —
  neither power-bound (54–56 % of the caiso-99 evening discharge cap; at the
  cap in only 5.7–15.0 % of evening hours) nor energy-bound (0.36–0.50
  cycles/day).
- On exactly those days LP optimality equalizes the marginal value of stored
  energy across the two windows, so the premium is a **fixed point of the
  storage arbitrage**, not of the supply stack. Measured evening−overnight gap
  on the pinned days: **+2.64 / +0.36 / +0.41 $/MWh** against the LP's own
  no-arbitrage prediction of 0.00.
- The stratification is the whole compression. **2025: pinned days model
  spread +1.69 vs actual +4.87; non-pinned days +6.11 vs actual +6.09 — the
  model reproduces the measured spread essentially exactly wherever the pin is
  absent.**

**The consequence that reorders the lane.** A supply-side steepening of the
evening raises λ_evening; the unbound storage immediately shifts discharge out
of the overnight into the evening and the two lambdas re-equalize at a *higher
common level*. The spread does not open and the overnight over-price (already
+1.73 / +2.81 in 2024/25) gets worse. That is precisely the caiso-113/114
C3a-guard failure mode — now a **predictable consequence** of any
evening-scoped supply-side candidate rather than a surprise. The charter's
nominated leading candidate (a caiso-114 refinement) is therefore **not the
first delta**; it is admissible only *behind* the storage pin.

## §2 — the storage conduct defect, stated as the thing a mechanism must fix

| year | overnight net (model / measured) | evening net (model / measured) |
|---|---|---|
| 2023 | **+157 / −53** MW | +2 547 / +1 640 |
| 2024 | **+188 / +5** MW | +4 154 / +3 122 |
| 2025 | **+453 / +267** MW | +5 404 / +4 361 |

(measured = EIA-930 CISO `NG: OTH`; model = the ISO-aggregate net recovered
from the energy balance — see §3's prerequisite on the basis caveat.)

The model over-discharges the overnight by a remarkably year-stable
**+210 / +184 / +187 MW**, which is what turns the overnight from a
charge/idle window into a discharge window and arms the pin. **The target is
the overnight net position, not the evening level and not the annual
throughput.** Any candidate that moves throughput instead is aimed at the
wrong quantity (§4's refutations).

## §3 — the technology prerequisite: ANSWERED IN-SESSION, and it passes

The candidate family below is only admissible if the pin is a *battery*
phenomenon: the caiso-99 shape anchor binds batteries only, so the LP's
**2 078 MW / 20 776 MWh of pumped storage** is its one entirely unrestrained
arbitrageur and the aggregate overnight net (+157/+188/+453 MW) sits inside PS's
power range. The committed slim bundle could not separate them (the gap
FINDING-caiso125 §6.4 flagged); this session added the per-tech sidecar
(`hourly/storage_<year>.parquet`, `(year, pass, tech, hour, charge_mw,
discharge_mw)`, write-only and solve-invariant) and replayed the keeper to
produce it — the replay reproduces the committed bundle digit-for-digit, so the
sidecars are the keeper's own and now ship in its `hourly/`.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **pinned days — li_ion** | **0.384** | **0.479** | **0.668** |
| pinned days — pumped storage | 0.074 | 0.132 | 0.077 |
| overnight net — li_ion / PS | +98 / +58 MW | +104 / +85 | +365 / +89 |

**The battery fleet carries the pin; pumped storage does not** — the battery
share rises with the build-out on a gap tightening toward zero (+2.45 → +1.27
$/MWh), PS's share has no trend and its gap does not converge (+5.71 / +0.48 /
−5.18, small-n noise), and PS discharges overnight in only 5–8 % of hours
against the battery's 28–41 %. **Gate D0 PASSES**: §4's battery-side candidate
is aimed at the right resource. (Retained as a live caveat, not a blocker: PS
still carries no shape restraint of any kind in the model and contributes
+58/+85/+89 MW of the overnight excess; that is a smaller, separate lane.)

## §4 — the candidate field, ranked, with what is already refuted

### REFUTED — do not build (state them so the ask is not a redo)

1. **AS-award power derate on the battery cap** — `caiso_storage_as_reservation`,
   built and A/B'd at **caiso-74** (2026-07-11): measured **ex-ante INERT**.
   The LP is energy/economics-limited, not power-limited; the derated cap sits
   0.9–3.7 GW above the LP's own maximum hour. Ships default-off.
2. **AS-award SOC sustain floor** — the same caiso-74 leg: mean 45/142/200 MWh
   against a 46–74 GWh fleet, three orders of magnitude below the binding
   surface.
3. **AS-award directional (reg-down) form** — *newly refuted here by
   arithmetic, no build*. Measured DAM battery awards by hour-of-day
   (`data/clean/storage-as-awards`, curated this session) put the overnight
   (hod 0–6) upward award at 334–713 MW and reg-down at 358–599 MW. Subtracting
   the upward award from the 2 830–3 521 MW overnight discharge cap still
   leaves ~2.1–3.1 GW of headroom against a model overnight net of
   +157/+453 MW; and a battery that is net-*discharging* satisfies a reg-down
   award by backing off, so the RD leg imposes no binding position either.
   **The entire AS family is closed for this defect.**
4. **A positive `battery_dispatch_adder`** — derived at $14.25 and A/B'd at
   **caiso-100/101**: REJECTED on the pre-registered two-sided ±15 %
   throughput guard (charge and discharge both collapsed below the measured
   floors). It is the wrong instrument here anyway: §2's target is the
   overnight *position*, and a throughput price moves *volume*.
5. **A cycle-count cap** (`storage_daily_cycling`) — inert by arithmetic: the
   model already runs 0.36–0.50 cycles/day, so any physically defensible cap
   is slack.
6. **Re-deriving or loosening the caiso-99 p95 shape envelope** — rule 21
   `[R-FROZEN-DERIVE]`, and useless regardless: the model uses 5–11 % of the
   overnight discharge cap, so the envelope's *level* is not the lever. A
   one-sided p95 cap cannot correct a mean-*sign* error.

### THE ASK — candidate S1: the DA/RT allocation on the DISCHARGE side

Arm the **two-sided reconciliation of M1** (`caiso_charge_allocation_schedule`,
the owner-granted caiso-103 ask executed at caiso-104), extending the existing,
precedented construction from charge to discharge.

- **Driver (real market structure, not a fit).** CAISO batteries are scheduled
  in the IFM and the single-market LP re-times the whole volume at the RT
  margin. Measured: the IFM schedules 76–84 % of realized *charge*
  (FINDING-caiso102 §1), on a fleet-size-invariant hour-of-day shape
  (cross-year r ≥ 0.994 across a 3.5× fleet, FINDING-caiso103 §1A). The
  discharge side of the same `market_output` sheet has never been derived.
- **Construction (identical to M1, already in the tree).** Per year, the
  24-value hour-of-day share of annual IFM fleet *discharge* plus its own
  `da_frac`; the dispatch mechanism floors each day's fleet discharge at
  `alloc_share_dis[hod] × da_frac_dis × (day total discharge)` — the same
  Fourier-Motzkin per-day construction as
  `model.lp.rows._build_storage_alloc_rows`. Since `Σ_hod alloc_share = 1`, this
  forces `da_frac_dis` of the day's discharge onto the measured intra-day
  shape and leaves `1 − da_frac_dis` free at the RT margin. **The discharge
  VOLUME stays fully endogenous**; only its intra-day allocation is
  constrained, and only for the DA-scheduled share.
- **Why it targets the defect.** The measured evening discharge share is high
  and the measured overnight share low; with the day total fixed by the LP's
  own charge, floors that bind in the evening leave less energy available to
  discharge overnight — it removes the arbitrage freedom in the exact window
  §2 identifies, without touching the evening supply stack.
- **Rule 13 `[R-MEASURED]`.** An allocation SHARE, not an outcome: the
  quantity regenerates for a forward year (fleet-size-invariant shape × that
  year's endogenous volume, latest-year carry per the caiso-99/104 precedent)
  and responds to changed conditions through the volume. This is the identical
  admissibility argument the owner already accepted for the charge side.
- **Rule 19 `[R-ONE-MECH]`.** It is ONE family with M1, never stacked: it must
  be armed as the two-sided version of `caiso_charge_allocation_schedule`
  (charge + discharge under one gate, one mechanism id), not as a second
  allocation mechanism. M1's charge leg is currently default-off and was
  measured belly-λ inert at caiso-104 — inert is not wrong, and the
  reconciliation is what rule 19 requires.
- **DOF:** zero new free parameters — the shape and `da_frac` are measured
  statistics of a committed raw source (rule 23 derive script).

### Candidate S2 (fallback, structural): DA/RT two-settlement separation

If S1's derive fails its stability gates (§5), the honest remaining diagnosis
is that the defect is the LP's single-market perfect-foresight arbitrage
itself. That is a structural change of a different size (a second settlement
or a non-anticipativity restriction), out of scope for a single delta, and it
should be chartered separately rather than approximated by a shaped floor.

### Explicitly NOT asked

The evening supply rung. FINDING-caiso127 §4 measures it — reality runs
241–714 MW more CT_PEAKER in the evening than the model, which serves the same
evening MW from a near-continuous CC_REGULAR/import band (the next rung above
lambda is a median **+0.59 $/MWh** away). That is a real defect, but on the
pinned days it changes the spread by ~0 by construction, and it belongs to the
C5a / C1 composition lane, priced LAST per rule 1.

## §5 — derive-first gates (must pass BEFORE a grant is worth giving)

Run in order; any failure stops the ask, no build (the caiso-106/107
discipline — measure the conduct before proposing the LP form).

- **D0 — DONE, PASSES (§3).** The per-tech split is measured: the pin is the
  battery fleet, PS is not the driver, S1 is aimed at the right resource.
- **D1.** Derive `alloc_share_dis[hod]` and `da_frac_dis` from the LESR IFM/RTD
  `EN` rows (HYBD excluded — solar-contaminated, the caiso-98/99/100/102/104
  basis). Report the three-year shapes.
- **D2 (stability, the caiso-106/107 gate).** Pairwise cross-year correlation
  of `alloc_share_dis` ≥ 0.99 and per-hod CV ≤ 0.20 across a 2× fleet growth,
  matching the charge side's r ≥ 0.994. A shape that is not fleet-invariant is
  a year-specific outcome, not a conduct statistic — **kill**.
- **D3 (binding pre-check, the caiso-74 lesson).** On the keeper's own
  committed hourlies, compute the floor the derived shape would impose and
  confirm it BINDS: the implied evening floor must exceed the keeper's evening
  discharge in a material share of days, and the residual overnight allowance
  must be **below** the keeper's +157/+188/+453 MW. If the construction is
  ex-ante slack — **kill, do not solve**.
- **D4.** Confirm the mechanism cannot pin the *level*: the day total stays
  the LP's own, and `1 − da_frac_dis` of it stays free.

## §6 — pre-registered A/B gates, if granted

Single delta on the caiso-126 keeper recipe, 3-year one bundle, same HEAD,
sequential (rules 12/16); both arms registered (rule 15); PREREG committed
before the B solve (the caiso-124/126 protocol).

**PRIMARY (all three years).**
- **P1 — the spread.** Model evening−overnight spread moves toward measured in
  every year, and the pinned-day share falls.
- **P2 — the keeper's disclosed evening hydro starvation heals WITHOUT any
  hydro-side change**: the −251 / −376 / −264 MW evening hydro gap comes within
  ±150 MW. (This is the charter's own PRIMARY; it is the honest test that the
  price surface, not the hydro family, was the defect.)
- **P3 — the overnight storage position** moves toward measured
  (+210/+184/+187 MW of over-discharge reduced).

**KILLS (pre-registered, non-negotiable post-hoc — the caiso-124 lesson).**
- **K1 — the C3a guard.** CA mean-LMP must not move away from the actual in
  any year (the caiso-113/114 killer, and the guard this lane exists to
  protect).
- **K2 — throughput.** The two-sided ±15 % battery-only NG:OTH charge and
  discharge guard that killed caiso-100 — the mechanism must fix the
  *position*, not buy it with a volume collapse.
- **K3 — D-4 off-window.** Any binding hour outside the mechanism's declared
  window (rule 17 `[R-FLOOR-WINDOW]`; the window is ALL hours by construction,
  so this reduces to the D-2/D-4 rows existing and the forced share being
  reported).

**Rule 22 LOYO** before any promotion talk; the derived shape re-estimated
leave-one-year-out and the verdict re-scored on the held-out year.

## §7 — what this memo does not authorize

No build, no derive-beyond-§5, no solve, no registration. `hydro_ror_split`
and the caiso-126 family stay exactly as promoted. The caiso-114 refinement
stays available as a **second** delta behind S1, never as the first.
