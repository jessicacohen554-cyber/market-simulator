# FINDING miso-130 — C7 `COAL_PRB` is a SUMMER-NIGHT price-regime defect: the model's July night floor prices 55 % of the PRB econ ladder out of the diurnal wave in 2025, and the wave-compression that does it is the same object as the July price miss

Session miso-130, 2026-08-05, branch `claude/miso-july-prices-c7-coal-prb-xe9rck`,
off `origin/main` at `c09fa5a0`. **NO LP SOLVED. NO ARM BUILT. NO MECHANISM
ARMED. NO RUN REGISTERED. KEEPER UNCHANGED** at `2026-08-04-miso-127-onlinepmin`
(NOT-YET, sole FAIL C7 `COAL_PRB` 2025 cv_ratio 0.347 vs the 0.5 gate, ledgered
caveats 2/3 {C3a, C3c}). Rule 15 `[R-DASHBOARD]` is satisfied by this statement:
no run was produced, so there is nothing to register. Rule 22 `[R-HOLDOUT]`:
2023–2025 only — the probe hard-errors on any other year, and the 2022/2026 LMP
files present in `data/raw/lmp-data/MISO/` were **not read**.

**Probe** `scripts/probes/_miso130_c7_night_regime.py`;
**record** `results/calibration/_miso130_c7_night_regime.json`.
**No pre-registration was committed before these numbers were read, so every
measurement below is DESCRIPTIVE — nothing here adjudicates a lever, flips a
matrix cell, or licenses a mechanism.** A future lever screen on any object
named here must pre-register its own bars first (the pjm-142 discipline).

Origin: an owner question — *why are July-2025 MISO high prices not captured,
and why does C7 `COAL_PRB` run hot at night, concentrated in July, every year at
varying intensity?* Both halves are answered below, and they are one phenomenon.

---

## 1. The July price miss (question 1), on the current keeper

Model = keeper P1 demand-weighted system price; actual = RT hub-mean LMP
(8 hubs), load-weighted with the model's own demand weights.

| July, lw $/MWh | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model − actual (month) | +1.08 | −0.17 | **−8.24** |
| model − actual, actual censored at $200 (body) | +1.10 | +1.70 | **−3.08** |
| model − actual, night h0–5 (mean) | **+8.7** | **+7.5** | **+7.0** |
| model − actual, day h10–18 | −4.8¹ | −12.2¹ | **−28.2¹** |
| diurnal wave (hod-profile max−min), model / actual | 11.8 / 33.3 | 12.0 / 48.9 | **20.2 / 109.3** |

¹ h14–19 mean from the probe's hod profile; the single worst hod is
h18 2025: model 53.6 vs actual 133.6 (−$80.0).

**Answer to question 1.** The July-2025 monthly miss on the current keeper is
−$8.24/MWh load-weighted (June −6.13, Sep −5.62 — the three worst months of
2025). It decomposes into:

* **~$5.2 is the >$200 scarcity tail** — the C3c-ledgered object (the model has
  no MISO scarcity-tail mechanism; actual July 2025 carries a cluster of
  >$200 RT hours, model p99 $75.6 vs actual p99 $222.4). Standing ledger, not
  new.
* **~$3.1 is the sub-$200 body**, the remainder of what miso-87 measured at
  −$11–13 per summer month on the miso-86 keeper — the CHP/CT/heat-rate
  corrections since (miso-98/99/117/122/126) closed most of it. The known
  instrument-blocked component stands behind it: MISO's published Jun/Jul-2025
  offline record jumps ~+12.3 GW at peak hours while the model's derate moves
  +1.8 GW, and no source resolves MISO outages at unit/fuel grain
  (miso-89/90's owner-ledgered gap; the data ask
  `docs/handoffs/miso-outage-grain-data-ask-2026-07.md` remains open).
* **The miss is two-sided**: every July the model is +$7.0–8.7 HIGH overnight
  and low at the peaks — the diurnal price wave is compressed 3–5× (2025:
  20.2 vs 109.3 $/MWh). The overnight-high half is the C7 connection (§3);
  the peak-low half is the C3c tail plus the under-derate above.

## 2. The C7 summer-night structure (question 2), verified and quantified

`COAL_PRB` model − actual (CAMPD bench), July, current keeper:

| MW | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| night h0–5 | **+2,276** | **+2,204** | **+3,454** |
| day h10–18 | −1,975 | −1,047 | **+141** |
| off-peak diurnal amplitude, model / actual | 6,068 / 11,143 | 5,326 / 9,008 | **2,900 / 6,927** |

The owner's description is exact: the model runs PRB hot at night in the summer
of **every** year (Jun–Sep night surplus +2.5/+2.1/+3.3 GW seasonal means;
August 2025 peaks at +3.9 GW), at varying intensity, worst in 2025 — and in
summer 2025 the **daytime matches** (+141 MW), so the entire 2025 July defect
is the missing overnight backdown. The month-grain amplitude deficit is
summer-concentrated in all three years, which is why the annual D-1 profile
(the C7 statistic) is dominated by it.

## 3. The regime overlay — why 2025 and only 2025 fails

The probe assembles the fleet at HEAD under the keeper's committed config and
prices every tranche at its July basis (per-plant F923 July coal, ISO measured
July gas $2.97/$2.43/$3.41, the `apply_gas_offer_margin` form), then overlays
the keeper's own solved July night prices:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model July night floor (p10) | $26.11 | $20.67 | **$31.42** |
| model July night p50 | $27.86 | $25.86 | **$33.87** |
| actual July night p50 | $19.02 | $17.36 | $25.72 |
| PRB econ ladder offers (p5–p95, 7.7–7.9 GW) | $19.69–37.35 | $20.44–37.73 | $20.53–38.21 |
| **PRB econ capacity priced BELOW the model's night floor (p10)** | **21.1 %** | **2.8 %** | **55.4 %** |
| PRB econ capacity below the night p50 | 30.8 % | 17.4 % | **74.6 %** |

**The freeze statistic is the finding.** A tranche priced below the night floor
is below every price the wave ever visits — it can never cycle, whatever the
ladder's granularity. In 2025, **55.4 % of the PRB econ ladder is priced out of
the wave entirely**, against 2.8–21.1 % in the passing years — and the ordering
across years matches C7 exactly (cv_ratio 0.529 / 0.514 / 0.347 for frozen
shares 2.8 / 21.1 / 55.4 %). This converges, from the **price side**, with
miso-128's **dispatch-side** flat-plant census (59.4 % of 2025 PRB nameplate
flat vs reality's 12.3 %) — two independent constructions, same ~55–59 % of the
fleet.

**Why 2025:** the year's fuel moves invert the band order. The PRB ladder's
dollar placement barely moved (its p5–p95 is ~$20–38 in all three years), but
gas rose 61 % ($3.41 July), re-pricing the CC supply that used to clear *under*
the ladder ($17–26 at 2023–24 prices) up to $24–33 and lifting the night
clearing +$5–13 — the floor walked up **past the cheap majority of the PRB
ladder**, and that majority went price-insensitive (flat) while its loading
rose.
This is the year-invariant-defect + moved-denominator structure miso-128 proved
(`R_dfrac` 0.354 with `R_tot` 0.952): the defect is the compressed wave, and
2025's price regime is what makes the coal fleet's exposure to it catastrophic.
**miso-128's "DO NOT open a 2025-specific lane" stands confirmed — there is no
2025 driver, only a 2025 regime.**

## 4. What holds the night floor up — the overnight supply identity

At the actual July-2025 night clearing (~$26–27) the model's sub-$27 supply is
exhausted; reality's is not. The model's overnight non-coal supply deficit,
component by component, with each component's adjudication status:

| component | overnight size | status |
|---|---:|---|
| seam import hour-of-day hole | −1.0 to −1.5 GW | real, measured, **all three seam mechanism classes SPENT** (miso-114 price / miso-123 ceiling-bounded / floor rejected); re-openable only by a firm/JOA scheduling representation with non-interchange identification |
| CC_REGULAR (matched machines) | ~−0.5 GW | level defect at both ends of day (miso-127-parallel); trough *volume* refused as mis-specified (miso-115 R 0.95–0.99) |
| CHP classes | nominal −1.7 GW flat | **basis-disputed** — bench CHP series carry the host-steam add-back (miso-116/127-parallel §7b); not interpretable against `class_hourly` without the basis fix |
| ST_GAS unmatched bench gap | unknown | 37–39 % of the model class has no bench counterpart (miso-127-parallel §7a, handed off) |

The model fills that hole with the only headroom cheap enough: the coal fleet —
which is why the coal surplus is overnight-specific (days are
availability-capped on both sides) and why the marginal price lands **above**
the coal band instead of inside it. The miso-115 "trough pricing question on
correctly-sized units" is this arithmetic.

## 5. The gas-commitment-bridge pool at MISO reads ~EMPTY (descriptive)

pjm-142's screen statistic, measured from the keeper's own payload (July,
CC_REGULAR, day-anchored `>0.2×npl` day / `<0.05×npl` night): **3 plants /
1,601 MW nameplate in 2023, 0 / 0 in 2024 and 2025** — model CCs already run
near-flat through summer nights (17.8–18.8 GW night vs 18.5–20.0 GW day).
The bridge family's premise (idle day-anchored committed CC tranches to hold
overnight) is **absent at MISO**, the same shape as PJM's pre-registered kill.
**No verdict is taken — this was measured without a prereg** — but any future
`gas_commitment_bridge` MISO charter must confront this census in its own
pre-registered pre-check before building anything. Cell stays `U`.

## 6. Named successors — NOT chartered here (rule 19; nothing below is sized on any Δ measured above)

**(a) Synchronized-reserve online-gating at MISO — the structural gap with the
strongest claim on the phenomenon.** `_miso_design`
(`model/reserves/spec.py:2377`) never sets `online_gated`: every reserve MW of
the RBDC family (requirement ≈ MSSC + regulating, ~2.5–2.7 GW held every hour
of 2025) can be backed by **idle** capacity, so reserves exert zero overnight
backdown pressure on the model's coal. The generic machinery already exists and
is per-ISO precedented — NYISO's three online-gated arms and PJM's
`pjm_reserve_online_gated` build `R − ρ·ΣP ≤ 0` rows whose comment states the
mechanism exactly ("idle capacity backs nothing, which is what turns a reserve
requirement into a COMMITMENT driver"). In the real market the spinning +
regulating portion (~1–1.4 GW) must ride on synchronized units; overnight the
synchronized fleet thins to baseload coal/CC, so reality's coal runs backed
down by roughly that headroom — hour-organized by construction, exactly the
`R_dfrac` dimension miso-128 proved is the whole failure, and immune to the
price-regime inversion of §3. Charter prerequisites: (i) identification of the
online (spin+reg) portion of MISO's ORR from published requirements (BPM-002 /
Schedule 28 family — never the residual); (ii) the nested-family split (online
class ⊂ ORR, the NYISO nested template); (iii) `online_rho` as a fleet property
(the existing `(pmax−pmin)/pmin` construction); (iv) a prereg with C1 16/16,
`COAL_BIT` no-overshoot, D-4 window, and LOYO kills. Rule 25: PJM's flag and
NYISO's verdicts transfer nothing — MISO enters `U` and derives its own
requirement basis.

**(b) CC_REGULAR committed-band measured re-grounding — bounded, admissible
hygiene.** The registered `committed: 1.20` rests on a generic "part-load
$/MWh is ~30–40 % above full-load SRMC" claim that predates the repo's own
rule-23 measured artifact, which puts MISO's committed-band block-average burn
at **1.005×** (`avg_committed_p50`, n=103,
`miso_campd_marginal_hr_summary.csv`) — already wired as this very band's
`phys_committed`. `CT_PEAKER`'s committed band is grounded **on** its measured
value (1.025 = registered = phys, markup 0); `CC_REGULAR`'s is not (markup
0.195 ≈ $4.4/MWh at the anchor), and the cohort the split routes to
`CC_INTERMEDIATE` still carries the 0.92 the de-leak comment itself calls "an
unphysical, artificially-cheap min-load block". The in-code "metric-neutral"
validation of 1.20 was taken at 2023 prices where the band cleared *below* the
$32 system price; at 2025 prices the cohort's expensive tail prices **into**
the July night-clearing neighborhood (~0.3 GW of CC_REGULAR-routed committed
within $1 of the night p50, alongside ~1.5 GW of expensive-delivered coal econ
steps and ~0.3 GW of CHP committed), so the neutrality argument does not carry
to the failing year. Effect is bounded (the cohort is small); it is a rule-14
proxy-for-measurand swap with zero free parameters, needs its own prereg +
same-HEAD A/B, and must not be landed as a bare code edit (keeper
reproducibility, the miso-122 seam lesson).

**(c) What must NOT be chartered off this finding:** the ladder-granularity
object without its three miso-129 prerequisites — the freeze statistic shows
the 2025 wave never *enters* the cheap-PRB band, and no step count cycles a
band the wave does not cross, so prerequisite (i) ("granularity carries
`R_dfrac`") would measure FALSE for 2025; any re-open of the spent seam
classes, the take-or-pay family, the self-commitment forcing family, or a
fitted trough adder (rules 1/13/19/24).

## 7. Solve posture

This container holds 15 GB total against the documented 14.4–15.5 GB
single-year MISO solve peak (miso-89/90/92/115), and rule 12 requires years
sequential within an invocation — a same-HEAD control + arm A/B (6 solves,
~3 h/arm) is not feasible here. Per CLAUDE.md's GitHub-Actions rule this is
stated rather than offloaded to CI: **the successor A/Bs need a larger
container or an owner-run invocation**, commands as usual
(`scripts/run_calibration_full.py --iso MISO --year 2023 2024 2025 …` per arm,
concurrent arms only where RAM allows).

## 8. Rule duties

* **Rule 15** — no run produced; nothing to register (this statement).
* **Rule 16** — all three training years measured together throughout.
* **Rule 19 / 24** — nothing armed, nothing stacked, no knob added.
* **Rule 22** — 2023–2025 only; the probe raises on any other year.
* **Rule 23** — no derive re-run; the marginal-HR artifact is read as
  committed.
* **Rule 28(b)** — `gas_commitment_bridge` MISO `ev` annotated (pool census,
  descriptive, cell stays `U`); `diurnal_price_amplitude` MISO `ev` annotated
  (the §1 two-sided wave numbers + §3 attribution). No cell status changes.
* **Contamination declared:** the session read miso-87/90/96/102/111–129's
  findings, the matrix, and the keeper shard before measuring; every §1–§5
  number is nevertheless a fresh computation from committed artifacts, and the
  freeze statistic's convergence with miso-128's census (measured blind to it)
  is the cross-check.
* Next number: **miso-131**.

## 9. Reproduce

```
uv run python scripts/probes/_miso130_c7_night_regime.py
```

No LP, no network; reads the keeper bundle, the bench, the payload, the F923
monthly-cost parquet, and the 2023–2025 MISO hub LMP files; writes
`results/calibration/_miso130_c7_night_regime.json`.
