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
`scripts/data/fetch_eia930_hourly.py` source) is egress-blocked here, so the extract
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

`scripts/probes/_ercot_2025_adder_diag.py` on the regenerated run131, demand-weighted
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
**over-cools the calibrated keepers**, and the reason is structural, not a fit:
in 2023 and 2024 the model can only reach the year's *genuine* scarcity tail
*through* the reserve over-fire, so crediting the battery AS makes reserves look
adequate on days that were actually tight and the model loses the real tail.

- **2023** collapses (Aug model $74 vs actual $217; tail 88→27 >$500). Its tail
  is the documented **out-of-market** scarcity (ERCOT's 2023 RTORDPA /
  ECRS-conservatism, IMM-estimated >$12B; the >$200 hours are **47% of the
  year's total $**) that an ORDC-only model cannot otherwise reproduce.
- **2024** over-cools too, and a dedicated single-year probe quantifies it:
  crediting 2024 drops avg **29.0 → 21.2** (actual 26.8), **worsens MAE
  10.5 → 12.7**, and collapses the tail **49 → 7 hours >$200** (actual 53; the
  year really had 8 hours >$1000). So 2024's exclusion is **not** "lower storage
  penetration" — it is measured: 2024 carries real tight-day scarcity (14% of
  total $) that the ORDC model only produces via the over-fire.
- **2025 is the lone year whose residual is purely the reserve-accounting
  over-fire** (tail = 4% of total $, reserves genuinely fat, no large
  uncompensated out-of-market component), so the measured credit closes it
  cleanly. Forecast years inherit it under the reformed RTC+B fleet regime.

The physically-pure global path therefore needs 2023/2024 scarcity modeled by a
genuine **ORDC scarcity-price** mechanism — *not* the reliability-deployment
overlay. That overlay is an energy/congestion **min-gen floor**: a credit+overlay
probe on 2024 was indistinguishable from credit-only (21.1 vs 21.2 avg), because
forcing pocket-thermal output adds supply at the hub and moves system LMP by
~$0.1 (if anything down). Out of scope here.

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

## Global storage-AS credit — investigated, BLOCKED on a scarcity-price model

**Date:** 2026-06-19. **Branch:** `claude/ercot-storage-as-global-m8wjqo`.
**Question:** make the run132 storage-AS reserve credit *global* (on for
2023–2025 and forecast) instead of `weather_year >= 2025`, without regressing the
calibrated backcast. **Outcome:** kept run132's 2025+ scope. The global credit is
blocked, and the block is now sharper than "it over-cools" — it is two
independent, structural obstacles, neither closable with a measured input here.

### The credit *anti*-targets the 2024 tail (new measured diagnostic)

The scope comment said crediting 2024 "makes reserves look adequate on days that
were actually tight." The hourly measurement is stronger than that. The credit
subtracts the **measured hourly** battery up-AS (`storage` column,
`ercot_2024_as_by_restype_hourly.parquet`) from the reserve-balance RHS. On 2024:

| 2024 battery up-AS | all hours | actual >$200 (53 h) | >$500 (16 h) | >$1000 (8 h) |
|---|---|---|---|---|
| mean MW | 2045 | **2618** | **2920** | 2904 |

On the genuinely scarce hours ERCOT held **~28–43% *more* battery AS** than the
annual mean — physically sensible (more reserve procured into a tight grid), but
it means the credit removes the **most** reserve-balance MW *exactly* on the
hours the model's tail must survive. The credit does not merely fail to
self-target away from scarcity; it is anti-targeted. (corr(AS, RTSPP)≈0.08 — the
AS held carries no negative scarcity signal the credit could exploit.)

This is why the model's 2024 tail collapses under the credit, and it confirms the
tail is an **ORDC accounting over-fire**, not a physical reserve-margin signal:
ERCOT priced scarcity on those hours *with* 2.6–2.9 GW of battery AS still held,
because the energy was scarce (net-load peak, thermal maxed), not because total
reserve sat at MCL. The model has no such energy-scarcity driver, so removing the
over-fire removes the only thing producing the tail.

### Reproduced on the current extract (new `--ercot-storage-as-reserve-from-year` flag)

Single-year 2024, keeper recipe + `--ercot-storage-as-reserve
--ercot-storage-as-reserve-from-year 2023` (credit on for the backcast):

| 2024 | avg (act 26.8) | MAE | >$200 (act 53) | >$500 (act 16) |
|---|---|---|---|---|
| keeper (credit off) | 29.0 | **10.5** | 49 | 28 |
| global credit (this run) | 21.2 | **12.7** | **7** | 4 |

Byte-for-byte the handoff's documented 2024 probe, now reproduced on the shipped
extract and through the new CLI plumbing — the credit-only global path fails 2024
on every gate axis (avg, MAE, both tails).

### Why no measured mechanism closes it (the two structural blocks)

1. **2024 — the in-LP ORDC curve is hour-invariant.** In the co-opt path
   `ercot_reserve_coopt_inputs` reduces any seasonal/TOD LOLP table *to its mean*
   (`mu_s = float(np.mean(mu))`) and the requirement RHS is flat; the only hourly
   signal is fleet availability + the hourly credit. So **direction 1**
   (re-derive the LOLP curve) cannot make the credit self-target — a higher/steeper
   knee shifts *every* hour and re-inflates the 2025 keeper that run132 just
   closed. The available measured table
   (`data/raw/_validation-source/ercot_ordc_lolp_params.csv`) is itself near-flat
   (µ≈904–947, σ≈1333–1367) and offers no tight-day-specific lift. Tuning µ per
   year to restore the tail would be a fit to actuals — barred by the repo's
   no-pinning rule.
2. **2023 — the tail is out-of-market and un-modelable by any ORDC/LOLP curve.**
   2023's >$200 hours are **47% of the year's total $** and are documented
   *administrative* scarcity (ERCOT RTORDPA / ECRS conservatism, IMM-estimated
   >$12B), not a loss-of-load-probability event. No re-derived demand curve can
   reproduce administrative withholding. **Direction 2** (a regime-gated
   out-of-market 2023 adder) is the only mechanism that could, but it needs a
   *defensible measured* MW/$-withheld source; obtaining the IMM withholding
   series needs egress not available here, and inventing the magnitude would be a
   markup — also barred.

A truly global credit therefore needs **two** independent scarcity-price
mechanisms (an hour-resolved net-load/LOLP driver for 2024 *and* an out-of-market
adder for 2023), each blocked on inputs we cannot source without violating the
no-markup / no-fit rule. The reliability-deployment overlay does not help (it is
an energy/congestion min-gen floor, ~$0.1 on system LMP — measured last session).

**Decision:** keep run132's `ercot_storage_as_reserve_from_year=2025` scope. This
is the handoff's sanctioned honest stopping point: the global credit is blocked on
a scarcity-price model, not on the credit (which is the measured battery AS and
physically correct in every year).

### Deliverable — CLI plumbing for future global probing

Added `--ercot-storage-as-reserve-from-year` (default **2025**, so the keeper is
unchanged) threaded `run_calibration_full.py` → `run_calibration.run_year` →
`with_overrides`. The handoff noted there was no CLI flag for the scope and that
testing a backcast credit required temporarily editing the config default; the
flag removes that footgun. Set it to 2023 to probe a global credit *once a genuine
scarcity-price mechanism exists* to pair with it.

## 2023 tail decomposition against the MEASURED 2023 storage-AS series (2026-06-21)

**Date:** 2026-06-21. **Branch:** `claude/ercot-scarcity-decomposition-2023-o4sck1`.
**Baseline:** the committed `ercot_dam_storageas_ccsteam_regen` = run132 keeper
(storage-AS reserve credit, 2025-scoped) + run133's CC steam-turbine outage
coupling. **Data unlock:** commit `93b879a` replaced the 2023 storage-AS column
(the `storage` column of `ercot_2023_as_by_restype_hourly.parquet`) with a
**measured** series rebuilt from the in-repo 60-Day DAM Gen Resource Data
(`scripts/data/build_ercot_as_by_restype_from_60day.py`): **1249 MW mean vs the prior
832 MW intensity-transfer estimate** (the estimate undercounted real 2023 battery
AS by ~50%). The committed keeper bundle was solved at sha `8d4a852`, which
**predates** the data unlock, so its recorded 2023 numbers (avg 49.8, tail 171/94)
are on the *old estimate*. This section re-solves on the measured series.

Per the handoff: this is a **diagnostic, no keeper change**. The 2023 *storage-reserve*
credit is turned on here only to decompose the tail — *not* adopted. `scenarios.py`
and the "Global storage-AS credit — BLOCKED" section above document why a global
storage-reserve flip is wrong; the evidence below re-confirms it against measured
reserves.

> **Reconciliation note (a parallel session landed the keeper while this branch
> was open).** An independently-merged ERCOT session (`run136`–`run139` on `main`)
> reached the same measured-2023 data unlock and went one step further: **run138**
> independently reproduces this section's baseline finding (measured storage
> over-tightens 2023, 49.8 → 58.4, tail 210/130 over actual), and **run139 is now
> the keeper** — it keeps the storage-*reserve* credit scoped from 2025 (the global
> flip stays rejected, confirmed by its run137: load+storage credit over-cools 2023
> to 27.0 / tail 33/15) but **adopts a measured 2023 *load*-resource RRS-UFR credit
> (884 MW, `ercot_load_resource_reserve_from_year=2023`)**, which corrects the
> over-tightening to the best 2023 MAE (12.1). So the priority-3 "is any 2023 slice
> reserve-addressable?" question was answered *yes, on the load side* (not storage).
> This decomposition still stands as the formal 3-way attribution and the
> measured-reserve quantification of the "47% out-of-market" claim; the probe below
> is registered as **run140** (storage-credit isolation), distinct from main's
> run137/138. Where this section originally said "keeper stays run132", read
> **"keeper is now run139"**; the storage-reserve conclusion is unchanged.

### Method

Three single-year-2023 ERCOT solves, identical config to the keeper bundle
(offer curves, gas prices, outage data, `storage_as_commitment` on), differing
only as labelled. Demand-weighted hourly system price (co-opt LMP, already
scarcity-inclusive) vs actual RTSPP; `avg` = simple mean over hours (the registry
convention; actual 2023 = 48.4), tail = count of hours whose system price exceeds
the threshold. Probe: `scripts/probes/_ercot_2023_decomp.py`. The
"no-ccsteam" point swaps in the pre-coupling ERCOT outage CSV (`46acbc7^`) and is
otherwise byte-identical — isolating run133's derate on the *same measured AS
data*.

| 2023 series (measured AS data) | avg | >$200 | >$500 | >$1000 |
|---|---|---|---|---|
| 1. no-ccsteam, no credit (run132-equiv) | 54.1 | 188 | 115 | 79 |
| 2. + ccsteam derate, no credit (run134-equiv) | **58.4** | **210** | **130** | 98 |
| 3. + ccsteam + **measured-2023 reserve credit** | **31.6** | **61** | **34** | 21 |
| 4. actual RTSPP | 48.4 | 181 | 104 | 61 |

### Three-way attribution of the 2023 tail

* **(a) physical missing-derate (1 → 2): +22 / +15 hours (>$200 / >$500), +$4.3
  avg.** run133's CC steam-turbine outage coupling deepens CC derates (e.g. Wolf
  Hollow II 29% → 50%), tightening peak supply. On the measured AS data it lifts
  the tail toward — and slightly past — actual incidence. (Consistent with the
  old-data run132→run134 lift of +20/+6.)
* **(b) reserve-accounting over-fire removed by the measured credit (2 → 3): −149
  / −96 hours, −$26.8 avg.** Crediting the measured 1249 MW of battery AS back
  into the co-opt reserve balance (undoing the `storage_as_commitment`
  double-removal) collapses the ORDC tail from 210/130 to **61/34**. This is the
  *physically-correct reserve accounting*, and it shows how much of the
  uncredited tail was the accounting over-fire rather than genuine LOLP scarcity.
* **(c) residual out-of-market administrative (3 → 4): +120 / +70 hours, +$16.8
  avg.** Even with correct measured reserve accounting *and* the derate fix, the
  ORDC/LOLP model reproduces only **61 of actual's 181 >$200 hours (34%)** and
  **34 of 104 >$500 (33%)**. The remaining two-thirds is administrative scarcity
  (2023 RTORDPA / ECRS conservatism, IMM-estimated >$12B) that no
  loss-of-load-probability curve can produce.

### The "47% out-of-market" claim, now against measured reserves

The prior claim ("the 2023 >$200 hours are 47% of the year's total $, mostly
out-of-market") rested on an *estimated* AS series. On the measured series, the
$-decomposition (price × demand) is:

| share of total 2023 energy $ | from >$200 h | from >$500 h |
|---|---|---|
| actual | 55.4% | 49.2% |
| uncredited keeper (run134-equiv) | 67.0% | 61.8% |
| **credited (correct reserve accounting)** | **30.1%** | **26.0%** |

The credited ORDC model carries only **~31% of the tail $ (price × demand) actual
priced in those hours**. Its total energy-$ shortfall vs actual is **42% of the
year's total energy $, 94% of it concentrated in actual's >$200 hours.** So with
measured reserves the un-modelable administrative slice is ~**42–67%** of the 2023
tail (by total-$ shortfall and by tail-$ share / hour-incidence respectively) —
squarely on the IMM's ~47% magnitude, now grounded in measured AS rather than an
estimate.

### Two reframings the measured data forces

1. **The data unlock does NOT improve the uncredited keeper's 2023 — it sharpens
   the over-fire.** The larger measured battery AS (1249 vs 832 MW) makes
   `storage_as_commitment` withhold ~50% more battery energy in 2023, tightening
   peak supply, so the uncredited 2023 tail *rises* from the old-estimate 171/94
   to **210/130** — now *over* actual 181/104 (run132-equiv likewise 151/88 →
   188/115). The keeper's good-looking 2023 tail was partly the estimate
   undercounting the withholding.
2. **The uncredited keeper reaches the 2023 tail "for the wrong reason."** Two
   errors partly cancel: the reserve-accounting over-fire (double-removing battery
   AS from reserve *supply*) compensates for the *missing* out-of-market
   mechanism. Apply the physically-correct credit and the ORDC tail collapses to
   34% of actual; the over-fire was standing in for the administrative scarcity.

### Bounding the reserve-addressable slice (priority-3 evidence)

The handoff asks whether *any* 2023 slice is reserve-addressable (a partial/capped
credit). The bracket is now measured for the **storage-reserve** credit: the
**uncredited** keeper *over*-produces incidence (+29 h >$200 vs actual), the **full
measured storage credit** *under*-produces badly (−120 h). So the genuinely
storage-reserve-addressable over-fire in 2023 is **small — bounded by the +29-hour
over-incidence** — while the dominant residual (~120 h) is administrative scarcity
the ORDC model only reaches *through* the over-fire. A **full storage-reserve** 2023
credit is therefore quantitatively wrong (it cools avg to 31.6 vs actual 48.4 and
the tail to a third of actual): the storage-reserve global flip stays rejected.

**But a different 2023 slice *is* reserve-addressable — on the load side.** The
parallel run139 keeper showed the measured 2023 **load-resource RRS-UFR** credit
(884 MW) corrects the *storage-commitment over-tightening* (58.4 → 43.1, MAE
16.0 → 12.1) without the storage-reserve credit's over-cool, because the two
measured effects bracket actual rather than both relaxing the same reserve. So
priority-3 resolves as: **keep the storage-reserve credit scoped from 2025 (this
decomposition), and adopt the measured 2023 load credit (run139)** — not a global
storage flip. The decomposition leads; the addressable slice was the load credit,
not the storage one.

### Reproduce

```bash
# common keeper config (single-year 2023), resolved offer curves from the bundle:
python - <<'PY'  # write resolved offer JSONs from the keeper bundle meta
import json; m=json.load(open('results/calibration/ercot_dam_storageas_ccsteam_regen/meta.json'))
json.dump(m['offer_curve_overrides'], open('/tmp/ovr.json','w'))
json.dump(m['offer_curve_deltas'], open('/tmp/delta.json','w'))
PY
ARGS="--year 2023 --iso ERCOT --storage-daily-cycling --battery-adder 10 \
  --storage-as-commitment --offer-curve-json /tmp/ovr.json \
  --offer-curve-delta-json /tmp/delta.json --coal-lignite-sigmoid \
  --lignite-floor 0.675 --lignite-ceil 1.00 --prb-floor 0.73 \
  --prb-follower-floor 0.63 --curve-mid 0.35 --btm-backfill-year 2024 \
  --cc-duct-peaking --wefor-residual 0.06 --wefor-relief-groups ST_CHP,ST_GAS \
  --energy-reserve-coopt --ercot-load-resource-reserve --ercot-storage-as-reserve"
# 2 = run134-equiv (no 2023 credit):
python scripts/run_calibration_full.py $ARGS --ercot-storage-as-reserve-from-year 2025 \
  --out-dir results/calibration/_decomp_2023_base
# 3 = + measured-2023 credit:
python scripts/run_calibration_full.py $ARGS --ercot-storage-as-reserve-from-year 2023 \
  --out-dir results/calibration/_decomp_2023_credit
# 1 = no-ccsteam: as `2` but with `git show 46acbc7^:data/raw/campd-unit-outages.csv`
#     swapped in for data/raw/campd-unit-outages.csv (restore after the solve loads it).
python scripts/probes/_ercot_2023_decomp.py _decomp_2023_base _decomp_2023_credit
```

### Still missing from the repo (handoff)

* ~~60-Day DAM Load Resource Data (AWARDS) blocks a measured 2023 load credit~~ —
  **RESOLVED by the parallel session:** the 2023 load-resource RRS-UFR was instead
  derived from the in-repo 60-Day DAM Gen Resource Data + ASPLANNP433 (NP3-911 Dec
  tail) via `scripts/data/build_ercot_as_2023.py` (884 MW), and adopted in the run139
  keeper. The dedicated Load Resource AWARDS file would still let a future build
  cross-check it directly.
* **Oct-2023 (10-02..11-01) Gen Resource Data disclosure file** — absent, so 2023
  storage AS zero-fills those hours (2023 otherwise covers 335/365 delivery-days).
  Dropping it in extends coverage.

### Priority-2 handoff — 2024/2025 ORDC-mapping re-fit (the real accuracy lever)

> **SUPERSEDED (2026-06-21, run142/143).** This section's premise — that the
> 2024/25 over-fire is an ORDC/`ordc_as_plan_mw`/`RTOFFCAP` mapping problem — was
> wrong. `ordc_as_plan_mw` and `RTOFFCAP` are **post-solve-overlay** params and
> are **inert in the co-opt keeper** (`ercot_reserve_coopt_inputs` builds the
> requirement from `ordc_mcl_mw` + LOLP, netted only by the load/storage credits),
> and the published seasonal LOLP table is ~flat (no signal to exploit). The
> over-fire was the **CAMPD outage over-statement** (40–80 GW of economic-idle
> coal/CC removed in low-demand months → false VOLL in Oct/Apr), fixed by the
> net-load revealed-availability outage filter (run142/143). Do **not** spend time
> on the ASPLAN/RTOFFCAP re-fit. See the next section for what priority-2 now is.

Independent of 2023 and **not started here** (it is a large, GATED change the
`AS netting — investigated and rejected` section of `docs/ordc-overlay.md` flags
as regression-prone: netting the full AS plan out of reserves drove 2023 MAE
32→512). The inputs are now confirmed in-repo for a *careful* per-type re-fit:

* `data/raw/ercot/ASPLANNP433_{2023,2024,2025}.parquet` hold the **measured AS
  plan MW by type by hour** (`AncillaryType` ∈ {REGUP, REGDN, RRS, ECRS, NSPIN, …},
  `Quantity` MW) — *not* tuned to a price target. Set `ordc_as_plan_mw` per year
  from these, and evaluate a **grounded `RTOFFCAP` > 0** from the plan's offline
  Non-Spin / ECRS share (`scarcity.py` currently treats all netted reserves as
  on-line, `RTOFFCAP = 0`, which its own docstring flags as understating the
  adder — `scarcity.py:39`).
* Gate the steam-derate fix as the physical baseline first, then re-gate all
  three years vs actuals (the AS-netting caution means 2023 must NOT blow up).
  Lead with this before revisiting any 2023 credit scope (priority 3).

## Priority-2 (current) — the winter-tail under-fire is out-of-market, not an outage knob (2026-06-21)

**Date:** 2026-06-21. **Keeper:** run143 (net-load outage filter). After the
outage fix cooled the 2024/25 shoulder over-fire, the residual ERCOT miss is a
**thin moderate/winter tail**: 2024 model 22 vs actual 53 h>$200; 2025 1 vs 31;
the Jan-2024 winter storm $22/3 h vs actual $44/19 h. Net load (run143) ≈ load-p85
(run142) within noise and did **not** recover the Jan storm. The handoff's
candidate (a) was "a less-aggressive net-load percentile (p80) trades a touch of
over-fire for fatter tails — sweep the monthly outage-GW offline first (it's
cheap)."

### Offline percentile sweep (the mandated pre-solve step) — p80 rejected

Regenerated the ERCOT outages at `--high-load-pctl 0.80` vs the keeper's `0.85`
and compared capacity-weighted unit-level outage GW-hrs/1000 by month (no solve —
`scripts/data/derive_campd_unit_outages.py --iso ERCOT --high-load-pctl {0.80,0.85}`):

| band | months (Δ at p80) | Σ Δ GW-hrs/1000 |
|---|---|---|
| **winter tail** (want fatter) | Dec +7.5, Feb +3.6, Jan +2.5 | **+13.6** |
| **shoulder over-fire** (must NOT re-inflate) | Nov +7.3, May +6.9, Oct +3.9, Apr +3.7 | **+21.7** |
| summer (preserved either way) | Jul +0.3, Aug +0.03 | ~0 |

A global p80 **re-inflates the Oct/Apr/Nov shoulder over-fire by more than it
fattens the winter tail (+21.7 vs +13.6)** — i.e. it re-introduces exactly the
false-VOLL the run142/143 filter removed. The percentile is a single global knob;
because winter-tail hours and shoulder-idle hours both sit below the summer
raw-load peak, no global threshold separates them. **p80 is rejected offline; no
solve spent** (it would have regressed the 2024/25 average).

### Why no outage knob is the right instrument

A calendar-winter (Dec/Jan/Feb) p80 carve-out *would* add the +13.6 winter mass
at zero shoulder cost — but it is **selection-on-residual** (choosing the lever
and its season *because* we know winter is under), barred by the repo's
no-fit-to-residuals rule. More fundamentally, the diagnosis says the winter-tail
miss is **not a supply-availability problem at all**: it is the same class as the
2023 tail above — **out-of-market extreme-weather / administrative scarcity**
(ERCOT RTORDPA / ECRS conservatism) that an ORDC/LOLP availability model
structurally cannot produce, which is why net load didn't recover the Jan storm.
The only mechanism that could reach it is the handoff's **candidate (b): a
regime-gated, *exogenously-keyed* extreme-weather scarcity-price adder** — and it
is blocked on the same no-markup / no-fit constraint as the 2023 administrative
adder (Direction 2 above): a defensible *measured* MW/$-withheld source, not a
fitted magnitude.

**Decision:** documented and left; the run143 keeper stands. The winter tail joins
the 2023 administrative slice as a known, bounded, out-of-market residual outside
an ORDC/LOLP model's reach — not a knob to chase. Reproduce the sweep:

```bash
uv run python scripts/data/derive_campd_unit_outages.py --iso ERCOT \
  --high-load-pctl 0.80 --out /tmp/ercot-unit-p80.csv   # vs the committed 0.85 file
# then bucket unit_capacity_mw × duration over each window's calendar months.
```

## Monthly-SHAPE design diagnosis — the ORDC reserve curve is a cliff (2026-06-21)

**Date:** 2026-06-21. **Keeper:** run143. **Trigger:** the run143 *annual* averages
are close (2024 23.2 vs 26.8; 2025 31.4 vs 32.5) but the *monthly shape* is wrong —
the model is **bimodal** (1–2 VOLL-spike months too high, the broad mid-range
months too low), worst in 2023/2024. Mean |monthly model−actual| (lower = better):
2023 **11.2**, 2024 **10.2**, 2025 **3.0** (2025 was already fine; 2023/24 are the
problem). Two grounded probes were run to find the lever; **both over-fired**,
which together triangulate the cause.

### Probe 1 — ECRS as a measured reserve *requirement* (demand side)

The co-opt models one contingency-reserve product and never grew when ERCOT
launched ECRS (2023-06-10, ~2 GW). Added the measured ECRS plan
(`ASPLANNP433`) to the reserve-balance RHS (`ercot_ecrs_requirement`, default off).
Result — mean |monthly gap|: 2023 11.2→**57.7**, 2024 10.2→**17.6**, 2025 3.0→3.3.
It could **not** lift the loose months (May-2024 17.7→19.0 vs actual 38: +1.75 GW of
requirement moved it $1, because reserves are loose there and the ORDC curve is flat)
and it **detonated** the tight months (Aug-2023 158→**570**, Aug-2024 69→**157**),
where the added requirement lands on the steep $5000 tail.

### Probe 2 — unit commitment (the industry-standard energy-side mechanism)

The ERCOT keeper is uniquely **dispatch-only** (`commitment=False`); every other ISO
keeper runs `--commitment`. Production-cost models (PLEXOS/Aurora/PROMOD/SERVM/…)
all run chronological SCUC+SCED, where startup / min-load costs of cycling CTs set
above-marginal-cost shoulder prices. Enabled the P2 commitment screen for 2024
(`KEEPER_COMMIT=1`). Result: avg **44.6** (actual 26.8), tail **239** h>$200
(actual 53), mean |monthly gap| **18.9** — a worse over-fire than ECRS (May 71,
Jul 66, Aug 74, Oct 71). Decommitting uneconomic CC/CT tightens the reserve balance
and the same cliff explodes.

### Triangulated conclusion

Adding reserve **demand** (ECRS) → tight months explode. Cutting reserve **supply**
(commitment) → everything explodes. Loose months stay under-priced in **both**. The
common cause is the **ORDC reserve-demand curve shape**: built from `ordc_voll`
5000 / `ordc_mcl_mw` 3000 / `ordc_lolp_sigma_mw` 1400 with `ordc_lolp_mu_mw` 0, and
— critically — **reduced to a flat hourly mean** in `ercot_reserve_coopt_inputs`
(`mu_s = float(np.mean(mu))`, "the demand curve is constant across hours"). The
adder is therefore a **cliff**: ~$0 when the fleet is comfortable (so the broad
"tight-but-not-scarce" $25–40 band that sets real shoulder prices is missing), then
VOLL the instant anything tightens (so every supply-tightening lever over-fires).
There is no smooth middle — which is the entire shape error.

This **supersedes** the earlier "the loose-month / winter residual is out-of-market,
un-modelable" framing *for the shape*: the mid-range gap is not administrative
withholding, it is a **mis-shaped reserve demand curve**, which IS modelable. (The
2023 *tail*-$ administrative slice above still stands; that is a separate, smaller
residual.)

### The grounded fix (scoped, not yet done)

Re-ground the in-LP reserve demand curve in **ERCOT's published ORDC** as a
*continuous, hour-resolved* curve rather than a flat mean — so it adds modest $
across the moderate-reserve band (lifting loose months) and ramps gradually instead
of cliff-to-VOLL (taming the over-fire). The published seasonal/TOD LOLP table
(`data/raw/_validation-source/ercot_ordc_lolp_params.csv`, NP6-576-ER µ/σ) and the
ERCOT ORDC methodology are the grounding source — **no fit to the LMP residual**.
This needs the co-opt LP to accept an hour-varying reserve requirement / demand
curve (today `req_total` is a scalar broadcast to all hours), so it is an
architectural change to `ercot_reserve_coopt_inputs` + the reserve block, gated vs
all 3 years + the tail. Probes reproduce via:

```bash
# ECRS-requirement probe (over-fire):
python scripts/probes/_keeper_2023as_run.py ecrs_probe 2025 2023 '{"ST_GAS":{"committed":0.0}}' ecrs
# commitment probe (over-fire), single year:
KEEPER_YEARS=2024 KEEPER_COMMIT=1 python scripts/probes/_keeper_2023as_run.py commit_probe 2025 2023 '{"ST_GAS":{"committed":0.0}}'
```

### Step 1 done — published ORDC curve (grounded, NP6-576-ER): the right direction (2026-06-22)

The keeper's curve uses the **ungrounded neutral fallback µ=0, σ=1400** (the
`ScenarioConfig` comments say so explicitly), while ERCOT *publishes* the LOLP
table (`ercot_ordc_lolp_params.csv`, µ≈924/σ≈1348). The fallback prices reserve
~920 MW *too low*, so the adder stays $0 across the moderate band. Wired
`--ordc-lolp-params-path` (threaded `run_calibration_full` → `run_year` →
`config.ordc_lolp_params_path`; default off, baseline byte-identical) and re-solved
the run143 recipe with the **published** table — purely the published rule, no fit.

Result (dashboard `2026-06-22-published-ordc-curve-np6`, PROBE) — demand-wtd
avg / h>$200 / h>$500 vs actual, run143 → published:

| year | avg (143→pub / act) | h>$200 (143→pub / act) |
|---|---|---|
| 2023 | 36.5 → **45.3** / 48.4 | 104 → **156** / 181 |
| 2024 | 23.2 → **25.2** / 26.8 | 22 → **34** / 53 |
| 2025 | 31.4 → 31.5 / 32.5 | 1 → 4 / 31 |

A **single grounded curve moves all three years' average and scarcity-hour
frequency toward actual at once** — the structural (non-fit) test — without
over-inflating the already-good 2025 or exploding (unlike the ECRS / commitment
over-fires). The extreme tail (P99, max) is about right.

**Residual — the duration curve localizes what's left.** The model is still hollow
in the **P90–P99 "moderately scarce" band** (2024 model P95 **27.9** vs actual
**61.4**; P90 24.8 vs 42.4) and slightly over-shoots P99.9 in 2023/24. The median is
fine. So the curve grounding was necessary but not sufficient: the model's reserves
rarely tighten into the band where even the published curve prices the P90–P95 hours.
That points the **next grounded lever at the reserve-*supply* definition** —
`ercot_reserve_eligible` counts ~all dispatchable thermal headroom as reserve, vs
ERCOT's ORDC reserve = online responsive capability (RTOLCAP); over-counting supply
keeps reserves artificially abundant in the moderate-scarce hours. This is an
exogenous physical/rule distinction (online vs offline/slow-start), not a fit.

```bash
# published-ORDC probe (this step):
KEEPER_ORDC_TABLE=data/raw/_validation-source/ercot_ordc_lolp_params.csv \
  python scripts/probes/_keeper_2023as_run.py ordc_pub 2025 2023 '{"ST_GAS":{"committed":0.0}}'
```

**Status:** the published curve is the grounded improvement and a keeper candidate
*after a volume re-gate* (the operating-shape gate flagged 19 regressions; the
fuel-mix split must be re-confirmed before it replaces run143). The reserve-supply
definition is the next step on the same no-fit basis.

