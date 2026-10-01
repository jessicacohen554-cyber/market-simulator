# FINDING nyiso-144 — the C3c tail is a **NYCA-WIDE reserve-scarcity event, not a Long-Island locational one**; and `online_rho`, measured for the first time, lands **below its own code's band**

Session nyiso-144. Keeper at HEAD `2026-08-18-nyiso-143-n11tsl-arm`. **No solve
spent on anything in this document** — every number is measured on committed
artifacts, the frozen CAMPD/NYISO-AS source tree, or the keeper's own committed
hourly sidecars. Holdout spend freeze ACTIVE and untouched: only 2023–2025 are
read anywhere below.

---

## 0. THE ANSWER, in four lines

1. **The downstate scarcity mechanism the handoff asks for does not exist,
   because the object is not downstate.** In NYISO's actual C3c tail hours the
   NYCA-wide reserve price averages **$307 / $32 / $393**/MWh and clears $50 in
   **100 % / 15 % / 95 %** of them; the Long-Island *locational* adder averages
   $116 / $5 / $152. The tail is a **system-wide reserve-shortage pricing
   event** that Long Island participates in, not a Zone-K separation.
2. **The model's `nyca_10min_spin` family — published 655 MW at a $775 RCPF, the
   exact instrument that would price it — binds in ZERO hours of all three
   years.** So does every Long-Island family. That, not a transfer bound, is the
   missing channel.
3. **`online_rho` is measured for the first time**: 0.3014 (incity_obligation)
   and 0.2011 (nyc_spin), against a min-load sensitivity of 1.2462 / 1.1247.
   Across that entire band the downstate gated family **binds** — `rho*` for
   inertness is ~3.0 — so nyiso-143's open question is answered: rho decides
   *how hard*, never *whether*.
4. **But both measured values fall BELOW the code's own `[0.5, 4.0]` clip
   floor**, which carries no primary citation anywhere in the repo. Arming a
   gated family today would still set its only reserve bound from a guardrail
   rather than from data. **Neither gated NYISO flag is admissible in a keeper
   until the owner resolves the band** — a rule 22 D-5(b) escalation, not a
   session call. Both stay `U`.

---

## 1. JOB 1 — where NYISO's scarcity tail actually comes from

nyiso-143 established that 100 % of the *model's* C3c tail hours are
Long_Island, produced by the Zone-K import bound, and that arming the published
N-1-1 limit removes the bound and the tail together (21/3/24 → 2/0/5 h against
actuals 10/13/42). It concluded the model has no other downstate scarcity
channel and named building one as the successor.

**This session measured what the real tail is, before building anything.**

### 1.1 The measurement

C3c gates on the **RT hourly hub average** > $300/MWh
(`frontend/data/backcast/tail/actual_tail.json`; NYISO actuals 10 / 13 / 42 h).
Taking those hours from `actual_lmp_hourly_NYISO.parquet` and reading NYISO's
own posted RT ancillary prices (`data/raw/NYISO-AS/NYISO_as_rt_<year>.csv`,
full 11-zone coverage, 8,760 h/yr) in exactly those hours:

| year | tail h | NYCA-base spin_10 mean | median | max | share of tail h > $50 | LI adder mean | LI adder > $50 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 10 | **$306.74** | $248.22 | $761.73 | **100 %** | $116.00 | 70 % |
| 2024 | 13 | $31.74 | $0.00 | $277.71 | 15 % | $5.36 | 0 % |
| 2025 | 42 | **$393.31** | $403.74 | $1,101.85 | **95 %** | $152.12 | 48 % |

*NYCA-base* = the minimum posted spin_10 across all 11 zones (the component
every zone shares, i.e. the non-locational part). *LI adder* = LONGIL minus that
base, clipped at zero. All-hours means for comparison: base $1.25 / $1.03 /
$3.97, LI adder $1.52 / $1.83 / $4.34 — so in tail hours the NYCA component
rises by **250×** and the LI adder by ~**70×**.

### 1.2 What it says

**The dominant term is system-wide, and Long Island's locational premium is a
second-order layer on top of it.** In 2023 and 2025 essentially every tail hour
carries a large NYCA reserve price; the LI adder is real (mean $116 / $152, max
$329 / $996) but is roughly a third of the base and is absent in 30 % / 52 % of
those hours. 2024 is the exception in both directions — its 13 tail hours are
*not* reserve-priced at all (median base $0), so 2024's tail has a different
cause and is not evidence for any reserve mechanism.

A Zone-K-scoped mechanism therefore cannot reproduce this tail, and neither can
any other downstate-only construction. **Building one would have been building
the wrong object** — which is why this session measured before building.

### 1.3 The model has the right instrument and it never fires

From the keeper's own committed `hourly/reserve_family_<year>.parquet` (P1):

| family | req MW | RCPF | hours dual ≠ 0 (2023/24/25) | max dual |
|---|---:|---:|---:|---:|
| `nyca_10min_spin` | 655 | **$775** | **0 / 0 / 0** | $0 |
| `nyca_10min_total` | 1,310 | — | 0 / 0 / 0 | ~0 |
| `east_10min_total` | 1,200 | $775 | 0 / 0 / 13 | $126.96 |
| `seny_30min_total` | 1,800 | $500 | 5 / 3 / 9 | $40.00 |
| `nyc_10min_total` | 500 | $25 | 28 / 28 / 62 | $25.00 |
| `li_10min_total` | 120 | $25 | **0 / 0 / 0** | $0 |
| `li_30min_total` | 540 | $25 | **0 / 0 / 0** | $0 |

**Long Island's locational reserve families never bind in any hour of any
year**, and the one family carrying a $775 demand curve over the whole control
area never binds either. The only families that do bind are NYC's, at $25.

The reason is structural, not parametric: these classes are **idle-allowed**.
The requirement is met at zero cost by capacity that is not running, so no
shortage forms and no price is set. Long Island in particular has ~1.9 GW of
peaking capacity (814 MW CT_PEAKER + 1,122 MW oil GT) against a 120 MW 10-minute
requirement, so its family is slack by three orders of magnitude of headroom.

**This is the same object from three directions**: nyiso-110 named it from the
reserve side (missing everyday reserve-price formation, co-opt dual > $0 in
17/6/34 h against measured DA spin > $1 in ~100 % of peak hours); nyiso-124
located it as a downstate/in-city price-formation gap; nyiso-143 hit it as a
vanishing C3c tail. It is one gap — **NYISO's reserve products do not price in
the model** — and it is control-area-wide.

### 1.4 The gate that would fix it is blocked on ONE unmeasured number

`nyiso_spin_reserve_online` re-classes the published spinning families
(`nyca_10min_spin`, `east_10min_spin`) onto the online-gated class, so idle
capacity stops backing spinning reserve. That is exactly the missing physics.
nyiso-110 solved it and measured it **INERT**, and this session **confirms that
verdict rather than overturning it** — but sharpens why, and the "why" is a
single number nobody has measured.

The gated row is `R[c,z] ≤ rho · Σ_g P[g]`, so the family is inert whenever
`rho ≥ rho* = 655 / min_t ΣP_eligible`. Measured on the keeper's own committed
`class_hourly_<year>.parquet`:

| year | eligible set | min ΣP | median ΣP | `rho*` | binding h at rho=1.0 | at rho=0.3014 |
|---|---|---:|---:|---:|---:|---:|
| 2023 | quick + hydro (**the keeper's**) | 1,912 MW | 3,567 MW | **0.3426** | **0** | 398 |
| 2024 | quick + hydro | 1,802 MW | 3,418 MW | **0.3635** | **0** | 720 |
| 2025 | quick + hydro | 1,418 MW | 2,429 MW | **0.4619** | **0** | 2,694 |
| 2023 | quick only (no hydro) | 59 MW | 147 MW | 11.0932 | 8,478 | 8,727 |

nyiso-110's stated ground — *"reserve-eligible hydro's output alone (2–5 GW ×
ρ ≥ 0.5) keeps it slack in every hour"* — is **exactly right at ρ = 1.0**, and
the ρ = 1.0 column reproduces its zero-delta result precisely. But its own
stated floor of ρ ≥ 0.5 sits **above** every measured `rho*` (0.3426 / 0.3635 /
0.4619). The verdict therefore turns on where ρ actually is, and:

* **hydro dominates ΣP** (1,912 MW vs 59 MW without it), so ρ for this family is
  essentially hydro's own headroom-per-MW-online; and
* **hydro has no CEMS and carries no entry in `fleet.RAMP10_FRAC_*` at all** —
  its 10-minute headroom in the model is `0`, which is a **coverage gap, not a
  measured zero**. (CAISO carries a local `CAISO_HYDRO_RAMP10_FRAC = 1.0` on an
  NREL/WWSIS-2 basis, explicitly scoped ISO-local because "only the CAISO design
  admits hydro reserve" — a premise NYISO's keeper falsified when it armed
  `nyiso_hydro_reserve_eligible`.)

Measuring ρ through that gap would manufacture a binding constraint out of
missing data — precisely what nyiso-110 §10 forbade ("excluding hydro would
falsify its real NYISO reserve eligibility to manufacture a binding
constraint"). **So no NYCA-wide `rho` row was derived, deliberately**, and the
`spin_online` path in `spec.py` is wired to find no row and fall through to the
legacy identification while logging that it is unidentified.

**`nyiso_spin_reserve_online` keeps its `I`.** What changes is that its re-open
condition is now a single, named, purchasable object: **a defensible 10-minute
deliverable-ramp capability for NYISO hydro**, from NYISO's own AS certification
/ capability data. That one number decides a family with a $775 demand curve
over the whole control area.

---

## 2. JOB 2 — `online_rho`, measured

Full derivation: `scripts/data/derive_campd_online_reserve_rho.py`; artifact
`data/raw/_processed-legacy/campd_online_reserve_rho_NYISO.csv` (+ `_units.csv`);
consumption seam `src/market_sim/data/online_reserve_rho.py`.

### 2.1 What rho is, and why the identification is load-bearing

`R[c,z] − rho · Σ_g P[g] ≤ 0`. For a gated class this row **REPLACES** the
capability row `Σ_g P[g] + R[c,z] ≤ Σ_g cap[g]` rather than joining it
(`model/lp/reserve_rows.py` — the branch ends in `continue`, and `zone_cap`
stays 0). **rho is therefore the class's ONLY bound**, which is why it cannot be
defaulted.

Its declared identification was the eligible fleet's cap-weighted
`(pmax−pmin)/pmin`. On the keeper's binned fleet only **4 of 851 / 849 / 705** LP
rows carry `pmin > 0` (the nuclear block, none quick-start eligible), so the
value deciding the mechanism was the literal `1.0` fallback — in every year and
in both branches (`FINDING-nyiso143-online-rho-unidentified-2026-08-18.md`).

### 2.2 The measurement

Per eligible unit, pooled 2023–2025 CAMPD: `HSL` = p99.5 of gross load; online
per the frozen convention; `head = min(HSL − P, ramp10_frac × HSL)`; and

  **rho = Σ head / Σ P over online unit-hours** — the aggregate ratio, because
  the LP row itself sums over the fleet.

`ramp10_frac` is the model's own `RAMP10_FRAC_BY_GROUP`/`BY_FUEL` lookup, so the
statistic and `FleetArrays.ramp10` read one source (rule 19). Both `HSL` and `P`
come from the same meter and `ramp10` is a fraction, so the MW basis cancels
exactly — no plant/unit basis flag is needed, unlike the min-load derivation.

| family set | consumer | zones | rho | full-hour | min-load | online unit-h | CAMPD coverage |
|---|---|---|---:|---:|---:|---:|---:|
| `incity_obligation` | `nyiso_incity_commitment_obligation` | NYC + Long_Island | **0.3014** | 0.2864 | 1.2462 | 401,361 | 95.5 % |
| `nyc_spin` | `nyiso_synchronised_reserve` | NYC | **0.2011** | 0.0874 | 1.1247 | 124,850 | 80.5 % |

Per bucket (obligation): quick-start 0.2157 over 3,149 MW of measured
capability, steam 0.3283 over 6,380 MW.

### 2.3 What it settles, and what it does not

**Settled: the downstate gated family is LIVE.** `rho*` for inertness is ~3.0
and the entire admissible band — from the as-operated 0.20 to the min-load 1.25
— sits far below it. rho's identification decides how hard the row binds, never
whether. nyiso-143's open question is answered.

**Not settled: the clip.** `RHO_CLIP = (0.5, 4.0)` is inherited from the legacy
path and has **no primary citation anywhere in the repo** — both call sites
described it only as "the same [0.5, 4.0] physical band the path-A family uses",
which is self-referential. It never mattered, because the legacy path was dead
code and the 1.0 fallback sits inside the band. It matters now: **both measured
values fall below the 0.5 floor**, so `rho_used` returns the floor, not the
measurement, and the coefficient deciding the class's only bound is again chosen
by a guardrail rather than by data — the same rule 21 `[R-DOF]` defect moved one
level out.

The band is left **UNCHANGED** rather than widened to fit the measurement:
re-banding a coefficient in the same change that re-identifies it would make the
two indistinguishable. Resolving it is an owner call.

**Disposition: `nyiso_synchronised_reserve` and
`nyiso_incity_commitment_obligation` both stay `U`**, now blocked on a *named,
resolvable* question rather than an unmeasured one.

### 2.4 A structural note on the obligation, recorded because it is not obvious

Arming `nyiso_incity_commitment_obligation` moves `nyc_10min_total` and
`li_10min_total` from class 1 to class 2. Class 1 carries the capability row
`ΣP + R ≤ Σcap`; class 2 does not. So the arm would **remove a constraint that
is currently live** — `nyc_10min_total` binds 28 / 28 / 62 h at $25 precisely
because NYC quick-start capacity is short — and replace it with a row that
imposes no energy/reserve capacity trade-off at all. Combined with the families'
$25 RCPF ceiling, the mechanism is a **commitment driver, not a scarcity-price
channel**, and its expected effect on the C3c tail is neutral-to-negative. This
is recorded as an ex-ante structural prediction, not a solved result.

---

## 3. WHAT THIS LICENSES, AND WHAT IT DOES NOT

* **Does NOT re-open the Zone-K transfer bound.** nyiso-143's A/B is closed and
  must not be re-solved. Nothing here reaches the tail back by re-tightening it —
  §1 says the tail was never a Zone-K object in the first place.
* **Does NOT re-open `diurnal_price_amplitude`** (NYISO `G`). §1 is a tail
  measurement, not a price-amplitude claim. It does show that C3c and the
  nyiso-110 peak-half share one root cause, which is a *fact about the queue*,
  not a new lever.
* **Transfers to NO other ISO** (rules 25 / 28d). The `online_rho` seam is
  ISO-general code, but every measured value is NYISO's own. §7 of the nyiso-143
  finding already flagged that any ISO running a binned fleet hits the same
  `pmin`-based dead code; that remains flagged, not actioned.
* **Adds no free parameter.** The rho seam replaces a dead identification with a
  measurement; the lay-up membership artifact (§4 of the companion prereg)
  introduces no scalar. `n_residual` unchanged.

## 4. THE QUEUE AFTER THIS SESSION

1. **NYISO hydro's 10-minute deliverable ramp** — one number, no CEMS, decides
   `nyca_10min_spin` ($775, control-area-wide) and with it the only in-model
   route to the measured tail. **The critical path.**
2. **The `RHO_CLIP` band** — owner D-5(b). Unblocks the gated pair (only one may
   ever be armed).
3. **Plant 7314's bridge over-run** — a D-4 FAIL that is *not* a membership
   defect (it fails the lay-up test), so it is an offer/economics object.
4. Unchanged and not re-opened: `nyiso_iroquois_winter_spread` (owner D-5(b) +
   the two-row matrix remediation), the closed items listed in the nyiso-143
   assessment §6.

## 5. REPRODUCTION

```
python scripts/data/derive_campd_online_reserve_rho.py --iso NYISO
python scripts/data/derive_campd_bridge_layup_exclusions.py --iso NYISO --detail
python scripts/probes/_nyiso144_tail_anatomy.py
```
