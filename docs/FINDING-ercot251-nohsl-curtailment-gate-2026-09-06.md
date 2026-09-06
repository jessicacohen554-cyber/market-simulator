# FINDING — the ERCOT no-HSL backcast year grosses renewables UP and then disables both mechanisms that take it back (ercot-251, 2026-09-06)

> Status: DIAGNOSIS ONLY. **No code was changed, no `ScenarioConfig` field minted, no LP
> solved, no mechanism tested, no matrix cell touched, no keeper changed.** Zero-LP: every
> number below is read from committed artifacts or computed from the loader's own constants.
> The proposed repair is put to the owner in §5, not armed — see §4 for why it cannot be
> screened the ordinary way.

## 1. The claim

Two ERCOT curtailment mechanisms self-disable on a premise that is **false in exactly the
branch that disables them**. In a backcast year with no measured HSL parquet, both gates say
the renewable bound is the delivered actuals — but the loader has already grossed that bound
UP by another year's curtailment rate. The gross-up is applied and the two ceilings that would
take it back are switched off, so nothing re-curtails it.

`scripts/run_calibration.py`, both gates keyed on `load_hsl_hourly(iso, year) is None`:

```
L2687  if load_hsl_hourly(iso, year) is None:
           "ercot_gtc_limits_measured: %d has no measured HSL potential
            (renewables ride delivered-as-CF) — measured GTC limits skipped
            for this year to avoid double-curtailment"
L2805  if load_hsl_hourly(iso, year) is None:
           "ercot_wtx_curtailment_driver: %d has no measured HSL potential
            (renewables ride delivered-as-CF) — curtailment ceiling skipped
            to avoid double-curtailment"
```

The guard is correct for a `delivered_pinned` bound. It is wrong for a `forecast_uncurtailed`
one, and ERCOT's no-HSL years are the second case, not the first:

```
market_sim.data.renewables.renewable_bound_provenance("ERCOT", 2022, "wind")  -> forecast_uncurtailed
market_sim.data.renewables.renewable_bound_provenance("ERCOT", 2023, "wind")  -> measured_potential
"ERCOT" in renewables._UNCURTAILED_FALLBACK_ISOS                              -> True
renewables._reference_curtailment_rate("ERCOT", "wind")                       -> (0.070784, 2025)
renewables._reference_curtailment_rate("ERCOT", "solar")                      -> (0.072927, 2025)
```

`renewable_bound_provenance`'s own docstring says what that label means: *"the bound is the
delivered shape grossed up by a different year's measured rate — real headroom, endogenously
re-curtailed."* **Endogenously re-curtailed by what?** In 2022, by nothing: the corridor
ceiling and the measured GTC limits are the two mechanisms that do it, and both just turned
themselves off.

## 2. The codebase already states the correct pairing — in its FORECAST leg

`market_sim/data/renewables.py` L2496-2513, the forecast branch of the same driver, grosses the
profile up **and** leaves the ceiling armed, and says why:

> *"So the LP can re-curtail endogenously (and the corridor ceiling is not double-counted on an
> already-curtailed series), gross the profile up to an uncurtailed potential with the per-tech
> reference curtailment rate from the most recent HSL year — **exactly the
> `_forecast_uncurtailed_cf` construction the ERCOT no-HSL backcast years use**."*

So the forecast leg pairs gross-up + ceiling deliberately, naming the backcast no-HSL years as
the same construction — while the backcast leg pairs gross-up + **no** ceiling. One of the two
is wrong, and it is not the forecast leg.

## 3. It accounts for the ERCOT 2022 C1 miss in full

Measured on the folded touchpoint `2026-09-05-run250-2022-touchpoint-carveout`:

| fuel | rate applied | gross-up | potential (TWh) | model | LP re-curtailed | excess vs actual |
|---|---|---|---|---|---|---|
| wind | 0.070784 (2025) | ×1.07618 | 115.563 | 112.226 | 3.337 | **+4.843** |
| solar | 0.072927 (2025) | ×1.07866 | 25.529 | 25.243 | 0.286 | **+1.576** |
| | | | **added 10.042** | | **took back 3.623** | **NET +6.419** |

The gross-up injects **10.04 TWh** of headroom; the LP claws back 3.62 TWh on its own (negative
prices / dump, ~2.9 % of wind potential) and the corridor mechanisms that would take the rest
are disabled. Net **+6.419 TWh** — the exact renewable excess the touchpoint measures
(+6.42 TWh), and, with zero dump and zero slack in all 8,760 hours, it displaces thermal
one-for-one. CC_REGULAR reads **−10.39 TWh against a ±8.00 TWh band**; the C1 gap is
**2.39 TWh of that 6.42**, a 37 % capture against a measured 55.5 % (first-difference
regression of each class on renewables, controlling for demand:
CC_REGULAR 0.555, ST_GAS 0.206, CT_PEAKER 0.083, coal 0.052).

**Inputs for the repaired gate exist for 2022.** The WTX reference tables
(`data/raw/reference/ercot_wtx_curtailment_share{,_family}.csv`) are **year-pooled** — no year
column, by design, since the driver is a function of the model's own net-load — so they apply
to 2022 unchanged. The GTC half needs the 2022 `gtc-limits` clean partition re-curated from the
committed raws (`data/clean` is disposable/gitignored; the 2026-09-05 completeness pass built
it at 13,321 rows).

### 3.1 Zero-LP phase-0 census — the ceiling's footprint, measured (rule 29 clause 0)

The 2022 fleet was rebuilt on the run250 recipe with **no LP**
(`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`, fidelity-guarded), and the WTX ceiling
the repaired gate would arm was computed on the model's own net-load with the recipe's own
coefficients (`ercot_wtx_curtail_unpooled=True`, `panhandle_owner="share"`, depth_wind 0.1354,
depth_solar 0.1614):

| quantity | value |
|---|---|
| reconstructed bound: wind potential | **115.563 TWh** (actual 107.383) |
| reconstructed bound: solar potential | **25.415 TWh** (actual 23.667) |
| ceiling removes from the bound — wind | 4.537 TWh |
| ceiling removes from the bound — solar | 0.927 TWh |
| **ceiling total** | **5.464 TWh** (West 5.091, Panhandle 0.374; all other zones neutral 1.0) |

The reconstruction independently reproduces §3's gross-up arithmetic (115.563 TWh wind
potential against the 115.563 predicted from ×1.07618), which is the census's own control.

**Reading — this SIZES the arm, it does not settle it.** The ceiling's 5.46 TWh footprint is
the right order of magnitude against the 6.42 TWh excess, so the repair passes the "direction
and order of magnitude the pre-solve delta implies" test and is not killed here. But the
translation from *bound* reduction to *realized output* reduction depends on hour-by-hour
overlap with the 3.51 TWh the LP already curtails on its own, and that only the LP resolves:

* pessimistic (ceiling binds only where the LP already curtailed): ≈1.96 TWh less renewable
  ⇒ ≈1.1 TWh back to CC_REGULAR at the measured 0.555 capture — **short of the 2.39 TWh C1 needs**;
* optimistic (disjoint): ≈5.46 TWh less renewable ⇒ ≈3.0 TWh to CC_REGULAR — **enough**.

The band straddles the gate, so **no amount of further paper analysis decides it** — this is
precisely the point at which rule 29 says an arm has earned a solve.

## 4. Why this cannot be screened the ordinary way — the governance problem, stated up front

The repair is **byte-identical in every training year**. 2023, 2024 and 2025 all carry measured
HSL, so their provenance is `measured_potential`, the predicate never falls through, and the
LP is untouched. Its only live years are **2022, 2021, 2020, 2019 — every one of them held
out.** So:

* it cannot be identified on 2023–2025 (rule 22's requirement) because it does nothing there;
* it cannot be screened on the year its footprint is largest (rule 29 `[R-SCREEN]`) without
  spending a holdout year;
* and deciding whether to keep it from a 2022 re-solve is **selection on the holdout** — the
  same class of act the ex-ante 2022 config designation existed to prevent.

**A rule-clean test does exist, and it does not touch 2022: run the no-HSL branch on 2023,
where the truth is known.** Temporarily withhold the 2023 HSL parquet so 2023 falls to
`forecast_uncurtailed`, then solve two arms on 2023 — (A) the current predicate, ceilings
disabled; (B) the repaired predicate, ceilings armed — and score both against 2023's actuals
**and** against the keeper's own measured-HSL 2023 numbers. That asks the only question that
matters — *does arming the ceilings on a grossed-up bound move the renewable level toward
truth or away from it* — identifies nothing on any held-out year, and its gates are
pre-registrable before either solve. Cost: two ERCOT single-year plant-level solves.

## 5. Put to the owner, not armed

The repair is a predicate correction with **zero degrees of freedom** — no parameter, no
threshold, no fitted value:

```
skip the ceilings only when the bound is delivered_pinned,
not whenever the HSL parquet is absent
```

i.e. test `renewable_bound_provenance(iso, year, fuel)` instead of
`load_hsl_hourly(iso, year) is None`, so `measured_potential` and `forecast_uncurtailed` both
keep their ceilings and only `delivered_pinned` skips them. It is a solve-affecting change, so
it carries rule 24 `[R-REGISTRY]`, rule 26 `[R-MECH-MATRIX]` and rule 29 `[R-SCREEN]` duties
and a PRECOMMIT with pre-registered gates before either arm is solved.

Two open decisions, both the owner's:

1. **Run the §4 2023 HSL-withheld screen?** It is the only way to test the repair without
   spending a held-out year.
2. **If it passes, does arming it constitute a keeper recipe change?** In-sample it is
   byte-identical, so no training-year determination can move and no keeper number changes —
   but it would change every future holdout touchpoint, which is precisely where it is not
   allowed to be tuned. The honest framing is that this is a **construction repair argued from
   the code's own stated premise**, in the neiso-85/86 class (a defect found by a touchpoint,
   fixed with zero DOF), not a lever identified against a residual.

**What this does NOT displace.** The absent `data/raw/ercot-hsl/np6/2022/` archive is still the
first-order fix and still owner-side: with measured 2022 HSL the bound stops being a
reference-rate approximation at all and both ceilings arm on the existing predicate, no code
change needed. That intake is recorded as **confirmed ungettable from this environment**
(`data/raw/ercot-hsl/README.md`, 2026-07-10: the Data Access Portal is a login-gated SPA behind
Incapsula, and the rolling-window listing API retains no 2018–2022 history) — which is what
makes the §5 repair worth deciding on rather than waiting out.

## 6. Provenance

Diagnosed in session ercot-251 (2026-09-06) from the committed
`ercot250_2022_touchpoint_carveout` bundle and the loader's own constants; no LP was solved.
Companion records: `docs/FINDING-ercot249-250-2022-touchpoint-2026-09-05.md` §2 (the touchpoint
that surfaced the miss) and Addendum 1, and `docs/calibration-log/ercot.md` (ercot-251).
