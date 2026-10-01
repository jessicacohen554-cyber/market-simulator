# FINDING miso-179 — the across-unit dispersion object dies at its own pre-check: the model already carries HALF the eligible spread at the margin, and the granted rank-mapped LEVEL form would crash every year's body by ~−41 pp

**Session:** miso-179 (2026-08-23). **Keeper `2026-08-22-miso-177-rho-measured`
UNCHANGED.** **NO LP solved, nothing armed, no `ScenarioConfig` field added, no
registration** (the miso-142/…/176/178 no-LP precedent; rule 15 `[R-DASHBOARD]`
not engaged). **PREREG:**
`PREREG-miso179-offer-level-dispersion-2026-08-23.md`, committed and pushed at
`4712ae8` BEFORE the identification derive or any hour-set-conditioned quantity
existed; the derive landed at `00a81a7`, the probe + record at `492f1d4`, in
the prereg's own order.

**Charter:** the owner granted FINDING-miso178 §10 **D-1** in the session
prompt — the across-unit dispersion object chartered, the
conduct-distribution admissibility FORM approved in kind (rank-mapped markup
DISTRIBUTION, the ercot-223 precedent), the ~430 MB corpus refetch authorized.
D-2 / D-3 were NOT granted and were not touched.

**The one-paragraph answer.** The corpus was refetched (552/552 manifest
sha256 verified, 429.6 MB) and curated; the measured quantile vector was
identified exactly as pre-registered (pooled JJA 2023–2025 DA, 881
price-setting-eligible units, 4.08 M unit-hours); and the two decisive
pre-checks then fired against the mechanism, on thresholds frozen before
measurement. **K-PRE-a:** the model's own affected stack already disperses
**$36.94/MWh p90−p10** at the 2025 summer top-decile margin against the
eligible book's **$68.27** — ratio **0.541**, over the frozen ≥ 0.5 kill line:
the object is roughly half the size Δ₁'s 197 % attribution implied.
**K-PRE-c:** the granted construction — replace affected-tranche offers with
the measured level at matched rank — is predicted (static, no re-dispatch) to
move C3a-2023 from **+1.28 % to −40.1 %**, with the same ~−42 pp in 2024/2025:
at every rank below ~p90, MISO's real eligible book offers FAR BELOW the
model's current offers, so a faithful level transfer crashes the body — the
quantified rank-grain confirmation of miso-145's "the real book is $8–15/MWh
CHEAPER at matched position". **K-PRE-b cleared** (the dispersion IS
price-setting-eligible: 87.8 % of the above-margin book mass is eligible and
the eligible spread is 1.58× the all-book spread) — the family fails on SIZE
and FORM, not on eligibility. Per the prereg's frozen closure path: **no LP,
cell minted `R`, keeper unchanged, and the lane falls back to the open
D-2/D-3/D-4 owner decision points.**

---

## 1. What was landed (Phase A intake — all committed / reproducible)

* Corpus refetch: JJA 2023–2025, both markets, 552 daily zips, **552/552
  fetched OK, 429.6 MB**; every landed file re-hashed against
  `manifest.json` — **0 mismatches** (the manifest's own digest is recorded
  in the derive artifact: `825c9f7c696dabbc…`).
* Curation through the frozen `write_clean_iter` seam:
  DA 10.89/10.87/11.19 M rows, RT 6.56/6.74/7.06 M rows (2023/24/25); rule-13
  outcome columns dropped and asserted absent. (RT 2023: 49,620 within-day
  duplicate key rows dropped — the known corpus repeat, DA identification
  unaffected.)
* Identification derive `scripts/data/derive_miso_offer_level_dispersion.py`
  → `data/raw/_validation-source/miso_offer_level_dispersion.json`
  (sha256 `b4e723127de63806…`): BOOK-ELIG population (available AND economic
  AND NOT must-run; weight `(ecomax − self_scheduled)⁺`), base level =
  step-1 price, normalized by the miso-156 PRIMARY delivered-gas monthly
  reference, pooled 199-point quantile vector. Pooled implied-offer-heat-rate
  quantiles p10/p50/p90/p95/p99 = **1.10 / 5.33 / 15.11 / 24.46 / 72.61
  MMBtu/MWh** (881 units; per-year sub-vectors reported, max interior
  divergence 2.0–8.6 MMBtu/MWh — 2025 the most divergent, report-only).

## 2. The pre-check record (probe `_miso179_dispersion_precheck.py` → `_miso179_dispersion_precheck.json`)

Validity gates first, all PASS: V1 reproduces the keeper's C3a to ≤ 3e-05 pp
in every year; V4 n_gen 2929/2923/2923, carry zones 6. H\* = the 221 highest
carry-demand JJA-2025 hours (105.8–118.7 GW; Jun 43 / Jul 112 / Aug 66;
congested share 31.2 % — the copper-plate caveat carried on every pooled
number). Model affected stack: 1,480 econ/peak tranches, 59.71 GW
(CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS).

**K-PRE-a — across-unit offer-level distributions on H\* ($/MWh, cap-weighted):**

| | p10 | p50 | p90 | p95 | p99 | **S = p90−p10** |
|---|---:|---:|---:|---:|---:|---:|
| model affected tranches (`mc_base`) | 22.43 | 34.96 | 59.37 | 85.29 | 167.96 | **36.94** |
| model across-plant base (G-5 grain) | 20.97 | 31.01 | 51.08 | 58.62 | 115.83 | 30.12 |
| book ELIGIBLE (the mechanism's population) | 0.00 | 19.98 | 68.27 | 127.22 | 276.15 | **68.27** |
| book ALL-available | 0.00 | 18.90 | 43.30 | 76.00 | 287.14 | 43.30 |

**Ratio S_mod / S_book_elig = 0.541 ≥ 0.5 → KILL.** Two robustness facts,
both running AGAINST the kill and it fired anyway: (i) the model side is
`mc_base` — the P1 startup-amortization markup (not reconstructable without a
P0 solve) would only WIDEN the model's spread and push the ratio higher;
(ii) the masked eligible book includes zero-price offer mass the model's
affected stack excludes by construction (its cheap mass lives in the
untouched committed/must-run bands), which INFLATES S_book_elig's lower half
and pushes the ratio lower. The kill is conservative on both axes.

**The shape underneath the kill is the durable measurement.** The model is
not uniformly under-dispersed — it is **over-priced through the body and
under-priced only at the top**: at the median rank the model offers **+$15
ABOVE** the eligible book (34.96 vs 19.98), and the book only crosses the
model above ~p90 (68 vs 59 at p90; 127 vs 85 at p95; 276 vs 168 at p99). The
true residual object is a **top-decile tail steepening** (roughly +$40 at
p95, +$110 at p99 over ~6 GW of eligible rank mass), not an across-the-board
dispersion deficit.

**K-PRE-b — CLEAR (both legs):** of the 2,244 GWh-grain of available book
mass offering above the model's clearing price on H\*, **87.8 %** is
price-setting-eligible (kill line < 1/3); the eligible spread is **1.58×**
the all-book spread (kill line < 0.5) — eligibility CONCENTRATES the
dispersion rather than stripping it. Only 14.6 % of eligible book mass sits
above the model's clearing price. The family did not die on eligibility.

**K-PRE-c — KILL, and not at the margin of its threshold:**

| static level-replacement prediction | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model lw as-is → predicted ($/MWh) | 33.27 → 19.66 | 30.99 → 17.29 | 40.12 → 20.69 |
| C3a as-is → predicted (%) | +1.28 → **−40.14** | −4.06 → −46.48 | −11.74 → −54.48 |
| mean clearing rank r\* in the affected stack | 0.437 | 0.445 | 0.482 |

The kill line was ±10 % on 2023; the prediction lands at 4× the band. The
mechanism is legible: the model clears at the ~44–48th percentile of its
affected stack, and Q(0.44–0.48) ≈ 4.9–5.2 MMBtu/MWh ≈ **$15–18/MWh** at the
measured gas reference — ~$14 BELOW the model's current clearing level, in
every year, because the book's levels at matched rank sit far below the
model's. The predictor overstates movement (no substitution channel — that
was declared when it was frozen), but nothing in a real LP recovers a −41 pp
static gap into a +1.75 pp target: the direction is unambiguous.

## 3. The verdict, and what it does and does not close

**`miso_offer_level_dispersion` minted `R` (no field ever created).** Both
kills fired on pre-registered thresholds; per the prereg's frozen closure
path there is no LP, no arm, no registration, and the keeper stands.

What the verdict CLOSES: the across-unit dispersion family **in the granted
form** — a rank-mapped markup-over-reference LEVEL distribution replacing the
affected tranches' offers. That form is refuted twice over: the object is
half the size the Δ₁ attribution implied (K-PRE-a), and the level transfer
is body-catastrophic in every year including the against-interest one
(K-PRE-c). This lands exactly on miso-178 §7's own named kill risk (b): "the
rank mapping is non-identifying at the model's tranche grain (a K-2-style
apportionment objection)" — with the masked corpus offering no unit identity,
no class bridge (miso-138 R), and no non-circular way to align the model's
affected-stack rank coordinate with the book's eligible-mass rank coordinate,
the level transfer inherits the population misalignment at full strength.
A price-conditioned population trim to fix it would be residual-adjacent and
is not proposed.

What the verdict does NOT close, stated honestly:

* **The measured object itself is real, price-setting, and now precisely
  located.** K-PRE-b cleared; the eligible book's top decile carries
  +$40…+$110/MWh over the model's stack top. The 2025 miss anatomy
  (miso-178: DA-foreseen tail −3.94 pp, Jun+Jul body −2.26 pp) is exactly
  where a top-of-stack conduct object would bite.
* **NAMED SUCCESSOR, NOT OPENED, NOT CHARTERED — an owner decision:** the
  **anchored SPREAD-ONLY variant** — transfer the measured eligible
  distribution's shape ABOVE an interior anchor rank (the model keeps its own
  level at and below the anchor; only the top-decile rise
  `Q(r) − Q(r_anchor)` grafts on, in the exact structural pattern of
  miso-151's shape-only within-unit surface, which was chartered as
  admissible in form). It targets precisely the measured residual (the tail
  steepening), cannot lower the body by construction, and its against-interest
  exposure is confined to hours whose clearing rank reaches the top decile.
  It is a DIFFERENT mechanism from the one granted and refuted here — this
  session does not build, pre-check, or adjudicate it. If the owner charters
  it, K-PRE-c's machinery (this probe, one line changed) prices its 2023 risk
  before any LP.
* The within-unit family stays CLOSED (`measured_offer_surface` R); nothing
  here re-opens it.

**The lane's fallback (per the charter):** the open owner decision points
stand as miso-178 §10 left them — **D-2** (the 5(i) seam-response envelope
admissibility ruling, holding miso-176's FFE evidence), **D-3** (the South
under-export evidence charter), **D-4** (the standing determination-posture
question) — now joined by the successor ask above. §3 of miso-178 remains the
honest record: the annual target is deterministic-reachable (−13.7 pp of
space for a +1.75 pp need); this session subtracts one named route and
sharpens where the remaining reach actually lives.

## 4. Disclosures

1. **Estimator conventions:** step-function weighted quantiles (the
   miso-151 convention) everywhere; midpoint-free `searchsorted` on
   cumulative weight. The K-PRE-c interpolation uses the artifact's own
   199-point grid.
2. **The model offer basis is `mc_base`** (the committed miso-156/161/178
   instrument lineage), P1 markup absent — disclosed in the prereg as an
   understatement whose bias runs toward proceeding; both kills fired
   anyway (K-PRE-a against that bias).
3. **Congestion:** 31.2 % of H\* hours carry > $1 cross-zone spread; every
   pooled statistic is ISO-level (copper-plate approximation, carried as a
   caveat, adjudicating nothing beyond the frozen constructions).
4. **The derive's loader was amended post-commit** to also emit the hour
   index for the probe's reuse; the artifact was re-generated and is
   **byte-identical** (same sha256 `b4e72312…`) — no measured value moved.
5. **G_ref consistency** between identification and instrument was asserted
   in-probe (derive JJA values vs `_miso156.measured_gas_monthly`,
   divergence < 1e-9).
6. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds neither marker; the
   corpus span is training-years-only. Rule 13: the identification path
   contains no LMP, no residual, no award column (dropped at curation,
   asserted absent).
7. The ~1.0 GB raw + clean corpus stays on this session's disk only (both
   gitignored); `manifest.json` + the committed derive make the refetch
   reproducible bit-for-bit.

## 5. Reproduction

```
python3 scripts/data/fetch_miso_energy_offers.py            # 552 zips, ~430 MB
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/data/curate_miso_energy_offers.py
uv run --no-project --with pyarrow,pandas,numpy --python 3.12 \
  python scripts/data/derive_miso_offer_level_dispersion.py
uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
  --python 3.12 python scripts/probes/_miso179_dispersion_precheck.py
```

Records: `results/calibration/_miso179_dispersion_precheck.json`,
`data/raw/_validation-source/miso_offer_level_dispersion.json`. PREREG:
`PREREG-miso179-offer-level-dispersion-2026-08-23.md` (commit `4712ae8`).
