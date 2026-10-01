# FINDING — who is marginal vs who SHOULD be: the $40–150 region belongs to CC-top + fast-start CT, and the model gives it to fitted coal rungs the measured corpus does not support (pjm-122, 2026-07-26)

> **STATUS — measurement complete, no lever armed.** This session landed the
> pjm-121 artifacts (bundle `results/calibration/pjm121_ccbelt` re-solved
> byte-faithfully; PR #2900) and then re-opened the dispersion lane per the
> pjm-121 handoff. Everything below is measured on the CALIBRATED pjm-121
> bundle with no solve beyond the landing re-solve — the proposed composite is
> a **candidate with a pre-registered no-LP pre-check**, not a result.

**Charter question (pjm-121 §7.2):** *why is coal marginal 38–80 % of the time
in every stratum, and what should be marginal instead?*

## 1. The signature reproduces on the CALIBRATED bundle

`scripts/probes/pjm121_marginal_decomp.py results/calibration/pjm121_ccbelt
--year 2025`: COAL sets the price **79 / 76 / 55 / 49 / 44 %** of hours across
the actual-price strata (0-25 through 200-376); CC_REGULAR is marginal **0–1 %**
despite 33–45 GW dispatched; the 50-100 stratum carries **15.5 GW idle
CT_PEAKER** of which only 1.8 GW is offered within $10 of the dual. Same
structure as the pjm-119 baseline — the CC belt moved the level, not the
ownership.

## 2. NEW MEASUREMENT — the coal that sets those prices is offering above the measured coal ceiling

The measured LONG_RUN ladder (36-month PJM DataMiner2 offer corpus, the same
frozen surface the keeper's floor reads) tops out at **8.47–8.97 × delivered
gas** at share s0.99, every net-load bin ("no coal wall", confirmed pjm-104).
Comparing the bundle's hourly load-weighted dual to that ceiling evaluated at
each hour's own delivered gas (8.62×, the bin-1/2 top):

| actual stratum | h | mean gas_day | measured coal ceiling | model dual (mean) | hours with dual > ceiling |
|---|---|---|---|---|---|
| 0-25    | 1,922 | $3.91 | $33.7 | $31.2 | 25 % |
| 25-50   | 4,848 | $4.24 | $36.6 | $39.2 | 72 % |
| 50-100  | 1,655 | $4.39 | $37.8 | $47.5 | **93 %** |
| 100-200 |   274 | $4.61 | $39.7 | $62.8 | **97 %** |
| 200-376 |    45 | $4.26 | $36.7 | $75.3 | **100 %** |
| >376    |    14 | $4.01 | $34.6 | $140.9 | **100 %** |

In the four tight strata the dual sits above the measured coal ceiling in
93–100 % of hours — **and coal is the price setter in 44–55 % of those same
hours.** The rungs doing it are the fitted `econ_high`/sigmoid tops of the coal
ladder ($40–90), offers the measured corpus says PJM coal does not submit. The
keeper's LONG_RUN floor is raise-only, so it never touches a fitted rung that
sits ABOVE measured — the fitted coal top survives measured ownership by
construction.

## 3. What the measured corpus says SHOULD own $40–150 (2025 tables, × delivered gas ≈ $4.2–4.6 tight-strata)

| segment | mid-ladder (s0.45–0.55) | top belt (s0.95–0.99) | $ at tight-strata gas |
|---|---|---|---|
| LONG_RUN (coal/ST) | 7.0–7.3× | 8.5–9.0× | ceiling **$36–40** |
| CC_LIKE | 4.9–5.5× | **11.1–18.8×** | belt **$49–83** |
| CT_FAST | 22.5–34.2× | **33.4–39.6×** | **$96–174** |

The measured CC top belt ($49–83) and CT_FAST ($96–174) bracket the actual
clearing levels of the two mid-tight strata ($66 and $129) almost exactly. The
model instead has: CC econ topping at ~9.6× (≈$42, keeper `econ_high` 1.5 ×
base-HR 6.372), CC peak starting at ~31.9× (≈$140, `peak` 5.0) — **a hole
covering precisely the $49–83 belt** — and a CT shelf whose marginal bids run
$47–80 against the measured $96–174.

## 4. The composite candidate (for pjm-123; NOT armed, NOT solved)

The three-part misallocation implies a three-part measured re-ownership, each
piece using the construction its refuted predecessor taught:

1. **COAL econ → LEVEL form** (`pjm_offer_midcurve_level_segments=("LONG_RUN",)`,
   the mechanism landed default-off this session): pulls the fitted
   above-measured coal rungs DOWN to the measured ladder. Direction: lowers the
   cheap/mid strata (which run +$10/+$4 too high) and vacates the $40–90 region.
2. **CC PEAK rows → measured belt**: extend the mid-curve targeting to the CC
   peak rungs (currently excluded by design), in level form, so the s0.95–0.99
   belt ($49–83) fills the 9.6×→31.9× hole. This is NOT the refuted pjm-121
   §5 arm — that measured the ECON rows (which sit at flat/cheap shares);
   the belt lands exactly on the rows the arm excluded.
3. **CT_FAST → max()-seam reprice**: the pjm-121 prescription — the measured
   CT level applied as a **max() against the full P1 bid (mc_base +
   startup_markup)**, never a floor on `mc_base` alone (the pjm-101/102
   stacking that over-expressed, CT −12 TWh). Raises the too-cheap idle CT
   shelf toward $96–174 in the hours it caps.

Directionally this is the first candidate whose construction is
dispersion-correct on all strata at once: cheap hours DOWN (1), tight hours UP
(2, 3). Individually each piece failed or would fail; jointly they re-assign
ownership the way the corpus measures it.

**Pre-registered kill criteria (no-LP pre-check first, the pjm-121 §5
pattern — run the real builder on the real arrays and diff):**
- the composite must LOWER the MW-weighted bid in the low net-load bins and
  RAISE it in bin3 (a level shift either way kills it);
- the CC econ offer-spread must not NARROW (the §5 refutation signature);
- the CT reprice must be a max() replacement — any row where markup adds on
  top of startup amortization kills that leg (rule 19).

C1 risk to watch at solve time: leg 1 cheapens coal (coal TWh up / CC down),
legs 2–3 push the other way; the fuel-mix bands gate the net.

## 5. Scope split — what offers can and cannot close

Measured CT tops at ~$174. The 200-376 and >376 strata clear at $252 and $815
on scarcity cascades (pjm-120 §3: all three reserve products at their $850
Step-1 penalties). **No offer surface reaches there.** The composite's
realistic scope is the 50-100 and 100-200 strata (−$3.66 and −$2.49 of the
−$4.54 gap); the extreme tail stays with the G-20b reserve/LP tightness class
(38.1 GW deliverable 10-min ramp vs ~3.7 GW requirement; dual never crosses
$300) — unchanged, and still the root cause of last resort.

## 6. Not re-litigated

Level-form on CC **econ** rows (pjm-121 §5, refuted — the composite targets CC
**peak** rows), the CT `mc_base`-anchored floor (pjm-101/102 — superseded by
the max()-seam form), `gas_offer_margin_anchor` (pjm-120 §1), reserve-product
coverage (pjm-120 §3).

## Reproduction

Environment + bundle: `docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md`
(landing recipe; the bundle re-solve reproduces the scored run to the cent —
2025 model_lw 41.53 / actual 46.07 / gap −4.54). This finding's measurements:
`pjm121_marginal_decomp.py <bundle> --year 2025` (§1) and the §2/§3 ceiling
comparison (delivered-gas day series = HH daily + PJM basis, the mid-curve
derive's own normalizer; ceiling = 8.62 × gas_day(h); duals from the bundle's
`hourly/system_2025.parquet`, RT load-weighted).
