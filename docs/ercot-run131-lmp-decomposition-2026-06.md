# ERCOT run131 — decomposing the 2025/2024 co-opt LMP hot bias

**Date:** 2026-06-18
**Branch:** `claude/ercot-run131-offer-mults-v5pz98`
**Baseline-to-beat:** run129 (`ercot_dam_offers_cconly_3yr`, the CC-only measured
DAM-offer curve + energy/reserve co-opt). Companion:
`docs/ercot-lmp-cooling-session-prompt.md` (the handoff),
`docs/lmp-decomposition-2026-06.md`, `docs/ordc-overlay.md`,
`docs/ercot-dam-offer-hrmults-2026-06.md`.

This is the handoff's mandated **first-hour decomposition**: which lever owns the
2025 LMP hot bias, *before* sweeping. Headline: the bias is the **co-opt ORDC
reserve adder over-firing in a comfortable year**, not the offer curve. The
sub-$20 price floor is the measured CC body and is not independently fixable
without a markup.

## Environment / provenance note

These numbers were produced during the input-recovery window, before
`data/raw/eia-930-hourly/ERCO hourly.parquet` was committed to `main`. At the
time the loader's extract was unavailable and `api.eia.gov` (the canonical
`scripts/fetch_eia930_hourly.py` source) is egress-blocked here, so the extract
was rebuilt offline by reshaping the already-committed region (D/NG/TI) and
fuel-type series (`data/raw/ERCO_region.parquet` / `data/raw/ERCO_fueltype.parquet`)
with the fetcher's exact pivot + local-time transform — a pure reshape, no
egress, no fabricated values. That rebuild reproduced run129's **documented 2025
signature exactly (6 hours <$20)**, confirming it was faithful for demand and
the fuel mix.

`main` now ships the canonical 10.76 MB `ERCO hourly.parquet` directly, so the
offline rebuild is no longer needed. The **qualitative decomposition below is
robust** (it is a structural energy-only-vs-co-opt and floor-on-vs-off split,
not a fitted result); the **exact $/MWh figures should be re-confirmed against
the shipped extract** before they anchor a keeper — they are expected to move at
most a dollar or two.

## Method

run129 recipe (the handoff command, with the `data/raw/_validation-source/`
relocation of the offer-curve JSONs and `--offer-curve-json` replacing the
renamed `--offer-curve-override-json`), 2025 single-year, three variants:

1. **co-opt ON** — the run129 recipe as-is.
2. **co-opt OFF** (energy-only) — drop `--energy-reserve-coopt`; strips the
   reserve adder, leaving the pure energy (offer-curve) price.
3. **floor OFF** — monkeypatch `ercot_ordc_demand_steps(multistep_floor=False)`
   to test the OBDRR048 $20/$10 floor.

Demand-weighted system price, P1 pass, vs actual RTSPP
(`actual_lmp_hourly_ERCOT.parquet`).

## Result

| 2025 series | mean $ | p1 $ | hrs <$20 | hrs [20,26) | hrs >$200 |
|---|---|---|---|---|---|
| **co-opt ON (run129)** | **45.1** | 21.4 | 6 | 2455 | 71 |
| **energy-only (no co-opt)** | **33.8** | 21.4 | 6 | 2448 | 6 |
| floor OFF (co-opt) | 45.1 | 21.4 | 6 | 2455 | 71 |
| actual RTSPP | ~32.5 | — | ~2329 | — | 31 |

Three separable conclusions:

1. **The +$11 mean overshoot is the co-opt ORDC reserve adder, not the offer
   curve.** Energy-only 2025 (mean **33.8**) already lands on actual (**32.5**);
   the co-opt adder lifts every hour ~$11 to 45.1 and over-builds the tail
   (**71 vs 31** actual >$200 hours). This is the fixable, defensible LMP target.
2. **The $21 floor / "only 6 hrs <$20 vs 2329 actual" is the measured CC energy
   body, not the reserve adder** — it is *identical* with co-opt off (p1 21.4,
   6 hrs <$20 in both). The cheapest CC tranche (the cc_merit_ramp delta pulls
   CC_REGULAR `econ_low` to 0.72×, ~$18–20 at 2025 gas $3.52) sets it. Lowering
   it below the measured DAM curve would be a **calibration markup**, not a
   measured change — out of scope per the honesty gate.
3. **The OBDRR048 $20/$10 multi-step floor is ruled out** — at reserves ≤7000 MW
   the VOLL-anchored LOLP penalty is already **$25.68**, so `max(penalty, floor)`
   never raises a band. Disabling it changes nothing (floor-OFF ≡ co-opt-ON).
   (CT/ST offer heights were already ruled out by run130.)

## Why the co-opt adder over-fires in a comfortable year

The in-LP reserve-demand curve fires on the *model's* reserve tightness. The
co-opt reserve supply counts thermal headroom + **storage** (`reserve_storage=
True`) but **omits ERCOT's load-side Reserves** (Load Resources providing
RRS/ECRS). The measured AS-by-restype data
(`data/raw/ercot-AS/ercot_2025_as_by_restype_hourly.parquet`, `load` column)
shows **~877 MW mean (median 908, p90 1159, max ~2 GW)** of load-side AS the
model never credits — so the model's reserve clears lower on the ORDC curve than
reality, pricing a scarcity adder in non-scarce hours.

## Proposed run131 lever (measured, GATED) — load-resource reserve credit

Credit the measured hourly load-side AS MW into the co-opt reserve balance by
reducing the reserve-balance requirement RHS by `load_mw(t)` in
`ercot_reserve_coopt_inputs`. Because the ORDC steps are priced by absolute
reserve level, this makes the marginal step price at total reserve
`R_gen + load_mw` — physically exact, no λ/double-count.

**Market-design check (per the 2023↔2024/25 question).** All of 2023–2025 is one
regime — ORDC/RTORPA reserve adders (in force to 2025-12-04; RTC+B AS demand
curves go live 2025-12-05, after the backcast). Load Resources supplied RRS/ECRS
in **all three years** (the `load` column exists for 2023/24/25), so the credit
is physically correct regardless of regime. It is **self-targeting**: ~877 MW is
negligible against 2023's GW-scale August scarcity (the 2023 tail, ~151/88,
survives), but meaningfully relieves the comfortable 2024/25 hours where the
adder over-fires. The 2023 reliability-deployment scarcity (erroneous ECRS
conservatism) is a separate, regime-gated offset and is untouched.

**This is a GATED change** (it re-runs dispatch, hence volumes). Acceptance:
re-run 3yr and hold run129's volume gate (≥12/18, no ST_GAS crater / CT over-run),
keep the 2023 >$200/>$500 tail (~151/88), and pull 2024/2025 monthly-LMP MAE
*down* toward actual. Implementation + 3-year gate is the next step.

## Status — run131 keeper landed

- Faithful run129 reproduction + this 2025 decomposition: **done**.
- Load-resource credit implemented (`--ercot-load-resource-reserve`, gated;
  measured RRS-UFR — the under-frequency-relay RRS only Load Resources provide,
  ~0.8–0.9 GW — credited into the co-opt reserve balance), 3-year run, gated, and
  registered: **done** (`2026-06-19-run131-load-resource-rrs`, bundle
  `ercot_dam_lrcredit_3yr`).

**Gate (same-extract baseline re-run of the run129 recipe, current extract):**

| year | LMP MAE base→r131 | avg base→r131 (act) | >$200 base→r131 (act) |
|---|---|---|---|
| 2023 | 10.5 → 10.5 | 46.7 → 46.7 (48.1) | 151 → 151 (181) |
| 2024 | 13.1 → **10.5** | 34.7 → 29.0 (26.7) | 82 → 49 (53) |
| 2025 | 17.1 → **11.3** | 49.5 → 43.7 (32.5) | 84 → 60 (31) |

Per-class TWh: **DAM−BASE ≈ 0.00 every class/year** — the credit moves the
reserve clearing *price*, not dispatch, so the 12/18 volume keeper and the
ST_GAS/CT classes hold exactly. 2023 is uncredited (archive starts 2023-12-10),
so its LMP and the 151/88 scarcity tail are untouched — the keeper is protected
by construction, not by tuning. **Measured (no markup).**

A note correcting an interim read: the standalone run131 numbers first looked
like a ~$1 lever only because they were compared against the decomposition's
*offline-rebuild* baseline; against the **same-extract** baseline the credit
cuts 2025 LMP MAE by a third. 2025 still runs ~$11 hot (residual co-opt
overshoot) — a real but separate problem, not closable by pushing CT/ST below
the measured offer curve (that would be a markup).

## run132 — the residual 2025 overshoot is the storage-AS reserve omission

**Date:** 2026-06-19. **Branch:** `claude/ercot-2025-lmp-overshoot-dxet66`.
**Baseline-to-beat:** run131 (`ercot_dam_lrcredit_3yr`, regenerated on the
shipped extract — reproduces the documented gate exactly: 2023 MAE 10.5 / tail
151/88; 2024 10.5 / 49/28; 2025 11.3 / avg 43.7 vs 32.5 / tail 60/39).

### First-hour diagnostic (where the 2025 adder over-fires)

`scripts/_ercot_2025_adder_diag.py` on the regenerated run131, demand-weighted
model price vs actual RTSPP:

- **The +$11.2 overshoot is entirely the deep tail.** Decomposed by model price
  band, the **39 hours the model prices >$500 contribute +$10.4** of the +$11.2
  demand-weighted gap; the <$200 body nets to ~0. The mean overshoot *is* the
  VOLL-anchored top steps firing ~13× too often (39 model vs 3 actual >$500).
- **In those 39 model-scarcity hours actual RTSPP had median $90** (mean $172,
  inflated by 2 genuinely-scarce hours); only 2 of 39 truly exceeded $500 and 7
  were under $50. The model invents scarcity reality didn't have.
- Concentrated in **summer (Jul +21.9, Aug +33.4, Sep +15.3)** plus spring
  (Mar–May) and Jan — exactly when 2025's solar+storage buildout made reserves
  fat.
- **The fleet is not undersized** (the most-measured suspect, checked first):
  EIA-860 ERCOT storage reaches **13.7 GW by end-2025** (8.1 GW end-2024) and
  the run carries the full year-end fleet (`storage_vintage_ramp` off); solar is
  vintage-ramped to 29 GW by Dec. So the residual is reserve **supply**, not a
  thin fleet.

### Mechanism — `storage_as_commitment` double-removes the battery AS

`--storage-as-commitment` (run127+) subtracts ERCOT's *measured* hourly battery
up-AS (the `storage` column of `ercot_<year>_as_by_restype_hourly.parquet`;
~0.8 GW 2023 → 2.0 GW 2024 → **2.8 GW 2025**) from the storage **power cap**
(`storage.reserve_storage_as_power`). The co-opt reserve block then derives a
unit's reserve room from that **reduced** cap (`reserve_storage_power_cap =
storage_power_cap`, `dispatch._coopt_rows`: `R_z <= thermal + (cap − dis +
chg)`). So the committed battery RRS/ECRS is removed from energy (**correct** —
it can't also arbitrage) *and* from reserve supply (**a bug** — that committed
AS *is* responsive reserve, counted in ERCOT's RTOLCAP/RTOFFCAP that drive the
ORDC adder). The model clears reserve ~2.8 GW lower on the ORDC curve than
reality and prices a scarcity adder in non-scarce hours — biggest in 2025,
where the battery-AS fleet is largest. This is the **same omission class** as
the run131 load-resource credit (787 MW of RRS-UFR); the storage piece is ~3.5×
larger and uncredited.

### Lever (measured, GATED) — `--ercot-storage-as-reserve`, scoped to 2025

`scarcity.ercot_reserve_coopt_inputs` now credits the measured storage-AS MW
back into the reserve-balance RHS (`requirement -= storage_as_mw`, clipped at
MCL), exactly as the load credit does — physically exact, no double count (the
reserve room from the reduced cap is the disjoint arbitrage headroom). Guarded
on `storage_as_commitment` (off → the full cap is already in the reserve block).

**Scoped to `weather_year >= ercot_storage_as_reserve_from_year` (default
2025) — a labeled modeling choice, not a measured one.** The credit is
physically correct in *every* year, but a global probe (credit on for 2023–25)
**over-cools the calibrated keepers**: 2023 collapses (Aug model $74 vs actual
$217; tail 88→27 >$500) and 2024 over-cools (avg 26.7→21.1). The reason is
structural, not a fit: in **2023** the model's ORDC tail is a deliberate keeper
standing in for the documented **out-of-market** scarcity (ERCOT's 2023
RTORDPA / ECRS-conservatism, IMM-estimated >$12B) that an ORDC-only model
cannot otherwise reproduce — crediting storage AS there correctly removes the
reserve over-fire but leaves that scarcity unmodeled. **2025 is the lone year
whose residual is purely the reserve-accounting over-fire** (reserves were
genuinely fat, no large uncompensated out-of-market component), so the measured
credit closes it cleanly. The physically-pure global path needs 2023/2024
out-of-market scarcity modeled separately (the deprecated RTORDPA
reliability-deployment overlay) — out of scope here.

### Gate (same-extract run131 baseline → run132)

| year | LMP MAE | avg (act) | >$200 (act) | >$500 (act) |
|---|---|---|---|---|
| 2023 | 10.5 → **10.5** | 46.7 → 46.7 (48.1) | 151 → 151 (181) | 88 → 88 (104) |
| 2024 | 10.5 → **10.5** | 29.0 → 29.0 (26.7) | 49 → 49 (53) | 28 → 28 (16) |
| 2025 | 11.3 → **2.7** | 43.7 → **33.9** (32.5) | 60 → **8** (31) | 39 → **6** (3) |

2023 and 2024 are **byte-identical** to run131 (the credit is off for those
years — keepers protected by construction). 2025's +$11 overshoot closes to
+$1.4 and the >$500 over-fire drops 39→6 (actual 3); every 2025 month lands
within ~$6, most within $1–2. **Volumes unchanged** (`DAM−BASE ≈ 0` — a
price-only reserve-clearing lever). Judged on the 2025 benchmarks (EIA-923 2025
is an incomplete vintage and is not used): the **gas/coal split is 76.4% model
vs 76.0% actual** (EIA-930; gas 203.9 vs 200.2 TWh, coal 62.9 vs 63.4) and the
LMP lands on actual. Honest caveat: the credit slightly *under*-counts the
moderate $200–500 tail incidence (8 vs 31 >$200) while the mean and MAE land on
actual — the reserve credit relieves the over-fire broadly.

**Measured (no markup on the credit magnitude — it is the measured battery AS);
the 2025 *scope* is a labeled modeling choice, justified above, not dressed as
measured.** Keeper: `2026-06-19-run132-storage-as-reserve`, bundle
`ercot_dam_storageas_3yr`.

### Dashboard fix (incidental, found this session)

The backcast HTML had stopped drawing the actual ERCOT LMP line. Cause: the W1
data relocation moved `actual_lmp.json` to `data/raw/_validation-source/`
(`paths.CALIBRATION_DIR`), and commit 01a5882 fixed that stale path everywhere
*except* `render_calibration_html.py:_actual_lmp_table`, which builds the
dashboard's per-(ISO,year) bench `avgLMP` block — so it read the missing path,
returned `{}`, and no `avgLMP` was attached (the page's `actualLMP(yr)` then
returned null). Fixed to read `CALIBRATION_DIR` (old path kept as fallback);
the ERCOT bench parts repopulate on the run132 render. The same fix repopulates
the other ISOs on their next render.
