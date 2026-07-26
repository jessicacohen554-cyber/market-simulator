# FINDING — the dispersion composite is refuted before a solve, and the reason retires the whole family: the frozen measured offer surface prices EVERY segment cheapest in the tightest net-load bin (pjm-123, 2026-07-26)

> **STATUS — REFUTED at the no-LP pre-check. No solve was spent.** The
> pjm-122 §4 three-leg composite was built on the real fleet and offer arrays
> and failed its own pre-registered kill criteria in all three years
> (2023/2024/2025) at both endpoints of the startup-markup bracket. The
> CALIBRATED keeper `2026-07-25-pjm-121-cc-belt` is **untouched** — no config
> change, no re-solve, no dashboard change. The two new mechanisms ship
> **default-off** with regression tests, as pjm-121 §5's refuted level form
> did.
>
> **The result generalizes past this candidate.** The refutation is not "these
> three legs happened to cancel". It is a property of the frozen measured
> surface itself (§3): in the tightest net-load bin the corpus prices
> `CT_FAST`, `CC_LIKE` **and** `LONG_RUN` *below* the mid bins. Any mechanism
> that hands a model class its measured level therefore compresses the model's
> price dispersion at the top rather than widening it — which is the opposite
> of what the C3a-2025 residual needs (pjm-120). **This retires the measured
> offer surface as the dispersion lever, not just this composite.**

**Charter:** pjm-122 §4 — build the three-leg measured re-ownership of the
$40–150 region (COAL econ → level form; CC PEAK rows → measured belt; CT_FAST →
max()-seam reprice) behind a no-LP pre-check with pre-registered kill criteria,
and spend an A/B solve chain only if it survives.

---

## 1. Result

`scripts/probes/pjm123_composite_precheck.py`, run on the keeper bundle for
each of 2023/2024/2025. The criteria were written into the probe docstring
before it was first run.

| criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| **K1** cheap bins FALL | PASS | INDETERMINATE | **FAIL** |
| **K1** bin3 RISES | **FAIL** | **FAIL** | INDETERMINATE |
| **K1** gradient bin3−bin0 > 0 | **FAIL** | **FAIL** | **FAIL** |
| **K2** CC econ spread not narrowed | PASS (vacuous, §4) | PASS (vacuous) | PASS (vacuous) |
| **K3** CT leg is a strict `max()` | **PASS** | **PASS** | **PASS** |
| **composite survives** | **NO** | **NO** | **NO** |

The decisive number is the **K1 gradient** — the composite's MW-weighted bid
delta in the tightest bin minus the same in the slackest bin. A dispersion
mechanism must move the tight bin further UP than the slack bin; the sign of
that difference does not depend on where the arms' common level shift sits, nor
on how much idle capacity the MW-weighting picks up (§4). It is **negative in
all six year × endpoint combinations**:

| $/MWh | 2023 | 2024 | 2025 |
|---|---|---|---|
| markup endpoint `lo` | −1.317 | −1.786 | −4.787 |
| markup endpoint `hi` | −0.895 | −1.521 | −4.626 |

The composite raises SLACK-hour bids more than TIGHT-hour bids, in every year,
under every assumption about the startup markup. It is an anti-dispersion
mechanism.

## 2. What each leg does (2025, keeper fleet, MW-weighted bid delta by net-load bin)

| arm | bin0 (7,008 h) | bin1 (876 h) | bin2 (613 h) | bin3 (263 h) |
|---|---|---|---|---|
| L1 coal → level form | −6.34 | −7.33 | −6.86 | −5.77 |
| L2 CC peak → measured belt | −3.92 | −4.20 | −4.01 | −3.83 |
| L3 CT_FAST → max() reprice | **+17.19** | **+22.75** | **+23.26** | **+11.74** |
| **COMPOSITE** | **+6.93** | **+11.22** | **+12.39** | **+2.14** |

(endpoint `lo`; `hi` shifts L3/COMPOSITE down by ~$4–5 uniformly and does not
change any sign pattern.)

Legs 1 and 2 are near-flat level reductions — they lower the whole curve by
roughly the same amount in every bin, so they cannot supply the differential
cheap-hour reduction the residual needs. Leg 3 dominates and carries the wrong
gradient: **+$23 in bin2 but only +$12 in bin3.**

Per class, the composite lands as:

| class / rung | GW | bin0 | bin1 | bin2 | bin3 |
|---|---|---|---|---|---|
| COAL* econ | 15.50 | −7.42 | −7.87 | −6.84 | −5.40 |
| COAL* peak | 0.78 | −8.89 | −9.46 | −8.49 | −7.03 |
| ST_GAS econ | 7.13 | −28.75 | −36.27 | −33.88 | −27.10 |
| CC_REGULAR econ | 27.45 | 0.00 | 0.00 | 0.00 | 0.00 |
| CC_REGULAR peak | 3.89 | −79.44 | −85.18 | −81.22 | −77.70 |
| CT_PEAKER econ | 20.13 | +64.78 | +85.69 | +87.33 | +43.43 |
| CT_PEAKER peak | 2.34 | +22.11 | +29.82 | +32.88 | +22.18 |

Note the size of the ST_GAS and CC-peak reductions: leg 1 pulls the whole
LONG_RUN class (coal **and** gas-steam) onto a ladder topping at 8.6 × gas, and
leg 2 replaces the fitted CC `peak` rung (5.0 × base HR ≈ 31.9 × gas) with a
measured belt at 11–19 × gas. Both are real consequences of "hand the class its
measured level", and both are level effects, not dispersion ones.

## 3. ROOT CAUSE — the measured surface itself is non-monotone in tightness

The CT leg's shape is not an artifact of the mechanism. Reading the frozen
surface directly (`data/raw/_validation-source/pjm_offer_midcurve_condbinned.json`,
2025 tables; multipliers are × delivered gas; bins are the surface's own
within-year net-load percentile edges `[0.80, 0.90, 0.97]`):

**CT_FAST**, body shares s0.05–0.85:

| bin | multiplier range |
|---|---|
| bin0 (slack) | 26.5 – 30.9 |
| bin1 | 32.0 – 33.9 |
| bin2 | 32.7 – 34.5 |
| **bin3 (tightest)** | **22.5 – 25.2 — the lowest of all four** |

The same inversion holds at the top of the ladder (bin3 s0.95–0.99 = 34.1–35.4
against bin2's 37.7–39.6), and it is **not** a gas artifact: bin3's mean
delivered gas is itself the lowest of the four ($4.03 vs $4.53 in bin1), so a
constant dollar offer would show up as a *higher* multiplier there. The
measured dollar offers in the tightest bin are lower still.

It is not confined to CT_FAST:

* **CC_LIKE** — bin3 body 4.83–4.92 vs bin1/bin2 5.17–5.53; bin3 s0.95 = 11.12
  vs bin2 11.97.
* **LONG_RUN** — bin3 top 8.07–8.47 vs bin0 top 8.57–8.97.

**Every segment of the frozen corpus is priced cheapest, or near-cheapest, in
the tightest net-load bin.** A mechanism whose whole content is "set the model
class to its measured conditional level" inherits that shape. This is why
pjm-108, pjm-121 §5, and now all three legs of the pjm-123 composite each moved
the level and left the dispersion compression intact — they were always going
to. The lane's working assumption since pjm-120 — that the measured corpus
holds the tight-hour price information the model is missing — is **false as the
surface is currently conditioned.**

**Open question for the owner, NOT resolved here and NOT a licence to re-derive
against a residual (rule 20).** Whether this inversion is a real property of
PJM offers or an artifact of the derive's conditioning is unanswered. The
plausible artifact story is that the within-*year* net-load percentile puts
winter evening peaks and summer scarcity in the same bin3, and that fast-start
units in those hours are largely already committed — so the offers *submitted*
in bin3 come from a different population than the offers that *set* the price.
Testing that means re-examining `scripts/data/derive_pjm_offer_midcurve.py`'s
conditioning (e.g. season-split or committed/uncommitted-split bins), which is
a data-derivation question with its own admissibility review, not a solve.

## 4. Honest scope of the pre-check

* **K2 passed vacuously.** No leg of the composite touches the CC **econ**
  rows, so the CC econ offer spread is bit-identical to the keeper's in every
  bin and the criterion carries no information here. It was pre-registered
  because it is the pjm-121 §5 refutation signature; it simply does not bind
  on this candidate. Reported, not counted as evidence for.
* **K1's MW-weighting cannot distinguish a repriced row that sets the price
  from one that does not.** Raising a CT shelf that sits $60 above the dual in
  a slack hour changes no price. This is why the finding leans on the
  **gradient** rather than the absolute per-bin levels: the gradient asks only
  whether the mechanism treats tight hours more favourably than slack ones,
  which is weighting-robust. It does not, in any year.
* **The startup markup is bracketed, not known.** It is amortized over P0 run
  lengths, which only an LP produces. Both endpoints come from the real
  `compute_monthly_markup` fed a synthetic P0 (all-idle → the full
  CAMPD-measured run-length ceiling, the smallest markup; every-run-one-hour →
  the largest). The bracket is wide — 1,132 rows, mean $4.87 vs $8.91, max
  difference $19.92 — and every criterion is reported PASS only if it holds at
  both ends. No criterion's verdict flipped inside the bracket except the two
  weaker K1 sign tests, which is exactly why the gradient was added.
* **A reconstruction defect was found and fixed along the way (§6).** The
  numbers above are on a fleet that carries the keeper's own flags; the first
  pass was not.

## 5. What ships, and what it is worth

Both mechanisms stay in the codebase **default-off** with regression tests
(`tests/test_pjm_dispersion_composite.py`, 10 cases), on the pjm-121 §5
precedent — a refuted lever whose construction is correct is worth keeping.

* **`ScenarioConfig.pjm_offer_midcurve_peak_segments`** (leg 2) — extends the
  mid-curve targeting to a segment's own `peak*` rungs in LEVEL form. Rejected
  at config construction alongside `pjm_offer_surface_conditional`, which
  prices the same rows additively (rule 19).
* **`ScenarioConfig.pjm_ct_measured_max_reprice`** + the pipeline's new
  `p1_bid_max_target` seam and `pipeline.solve.apply_bid_max_target` (leg 3).

**K3 is the one criterion that passed on its merits, and it is the reusable
result.** The measured level enters as `max(bid, target)` against the FULL P1
bid — after the startup amortization and every additive adjustment — with
**zero additive row-hours in all three years**. That is the rule-19
reconciliation pjm-101/102 lacked when the same measured level was applied as a
floor against `mc_base` alone and stacked with the pjm-103 start-cost pricing
(CT −12 TWh, C3a +12 %). The seam is now a tested primitive available to any
future measured-level mechanism, on any ISO.

Zero free parameters were introduced (rule 18); the surface JSON is untouched
(rules 20/23); only 2023–2025 were touched (rule 22).

## 6. Defect found: the bundle-reconstruction helper drops most of the keeper's flags

`derive_pjm_ordc_overlay._run_year_kwargs` — the helper every PJM no-LP probe
reconstructs a bundle's fleet with, including `pjm121_level_form_precheck.py` —
forwards a hand-curated subset of `meta.json`. On the pjm-121 keeper it drops
**38 non-default flags that are `run_year` parameters**, among them:

* `tranche_startup_amortization` / `_measured_runs` / `_conditional_runs` — the
  pjm-103 start-cost pricing that **owns the CT stack**, i.e. exactly the term
  leg 3 is supposed to reconcile with;
* `ct_netload_drag` + `ct_drag_overrides`, `gas_st_netload_drag` +
  `gas_st_drag_overrides` — the drag mechanisms that own CT and ST_GAS offers;
* `ct_intermediate_split`, `coal_sync_srmc_tranche`, `coal_mustrun_online_pmin`;
* `pjm_offer_midcurve_conditional` itself — the mid-curve MASTER gate (the
  segment scope rides in on `prb_overrides`, the gate does not), which
  `pjm121_level_form_precheck.py` works around by forcing it on.

Reconstructed that way, the CT rows carry no start-cost markup at all, and the
first pass of this pre-check measured leg 3 against a CT stack missing its own
pricing mechanism. The visible symptom was that the startup-markup bracket
**collapsed** (`lo == hi` exactly), which is now a hard error in the probe.

This probe uses `full_run_year_kwargs`, which keeps the proven base mapping
(including renamed keys such as `prb_overrides` ← `coal_prb_sigmoid_overrides`)
and then overlays every remaining meta key `run_year` accepts, plus fidelity
guards that hard-fail if the mid-curve gate, the segment scope, or any
startup-amortization flag failed to survive.

**Consequence for the record:** pjm-121 §5's level-form numbers (−8.76 $/MWh
MW-weighted, and the CC econ spread table) were measured on the partial
reconstruction. Its *conclusion* is unaffected and is independently reconfirmed
here — leg 1 and leg 2 are both level movers (§2), and §3 explains why any
measured-level arm must be — but the specific magnitudes in that table should
not be quoted as the keeper fleet's. Re-running that probe on
`full_run_year_kwargs` is a small, unblocked follow-up; it is not required to
act on this finding.

## 7. For the next session

1. **Do NOT re-open the measured offer surface as a dispersion lever.** §3
   applies to every segment and every form (floor, level, max()-seam) — this
   is a property of the frozen corpus's conditioning, not of any one
   construction. Legs 1, 2 and 3, and any recombination of them, are closed.
2. **The one live question the surface raises is a DERIVE question, not a
   solve question:** is the bin3 inversion real, or an artifact of within-year
   net-load-percentile conditioning that mixes winter and summer tight hours
   and samples already-committed fast-start units? That is an owner-gated
   review of `derive_pjm_offer_midcurve.py`, subject to rule 20 — a
   re-derivation commit must cite a data or conditioning-definition change,
   never a residual.
3. **The dispersion root cause reverts to G-20b**, where pjm-120 and pjm-121 §4
   already put it: 38.1 GW of deliverable 10-min ramp against a ~3.7 GW
   requirement and a reserve dual that reaches $300 in zero hours all year. No
   offer surface reaches the >$200 strata ($252 / $815 actual); that remains
   owner-held frontier.
4. **`full_run_year_kwargs` should probably replace `_run_year_kwargs`** at its
   other call sites (or the shared helper should be widened), so no future
   probe silently measures a fleet the keeper never solved. Out of this
   session's scope; §6 is the write-up.

## Reproduction

```
uv sync
python scripts/regenerate_clean.py transfer-interface-limits ramp-capability lmp
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
for Y in 2023 2024 2025; do
  python scripts/probes/pjm123_composite_precheck.py results/calibration/pjm121_ccbelt \
    --year $Y --json-out results/calibration/pjm123_precheck_$Y.json
done
```

No LP; ~4 min per year (fleet reconstruction only). The refactor that let the
mid-curve builder and the CT target share one surface/share context was proven
**bit-identical** on the real 2025 keeper fleet: the keeper-scope markup array
(3,325 × 8,760) is byte-equal before and after, `nonzero_rows=431` both ways.
