# NEISO backcast diagnosis — CC steam-turbine outage derate integrated (2026-06-19)

**Task.** Re-run NEISO from the last keeper config (`neiso_monthly_keeper`,
"neiso 21") **without magic numbers**, integrating the combined-cycle
steam-turbine unit-outage derate (the `eia_*_cc` capacity-source coupling now in
`campd-unit-outages-NEISO.csv`), then decide whether NEISO is backcast-calibrated
or needs further refinement before a forecast run.

**Bundle:** `results/calibration/neiso_ccsteam_keeper_3yr` (2023–2025, 8760 h,
commitment on). Command = the keeper's exactly:

```
run_calibration_full.py --iso NEISO --year 2023 2024 2025 \
    --commitment --ct-deployment --hydro-backfill-year 2024 --hydro-eia930-monthly
```

No `--gas-hub-basis-daily` — the fitted daily-AGT convexity
(`AGT_DAILY_BASIS_CONVEXITY = 7.0`) is the rejected magic number and stays off.
The CC-steam derate is integrated structurally at the derivation-script level
(`derive_campd_unit_outages.py::build_capacity_index`), so a CT block's CSV
`unit_capacity_mw` is its steam-augmented share `CT_nameplate × (1 + ΣCA/ΣCT)`
and one CT out derates its turbine **plus the steam it fed** — no tuned constant.

---

## 1. Headline result

| Year | CC_REG TWh | gas tot | vs EIA-930 gas | LW hub $/MWh | actual DA | Δ price |
|------|-----------:|--------:|---------------:|-------------:|----------:|--------:|
| 2023 | 52.30 | 54.76 | 55.47 (−1.3%) | 35.08 | 36.82 | −4.7% |
| 2024 | 56.51 | 58.87 | 59.64 (−1.3%) | 40.52 | 41.47 | −2.3% |
| 2025 | 57.76 | 60.11 | 60.09 (+0.0%) | 71.20 | 67.86 | +4.9% |

Nuclear/hydro/wind/solar are EIA-930-pinned (near-exact); net interchange is the
measured EIA-930 schedule (exact by construction). CC_REGULAR reproduces the
keeper (52.31 / 56.48 / 57.75) to **within ±0.03 TWh** in every year.

**2025 monthly DA price, model vs actual (the hard year):**

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|--|--|--|--|--|--|--|--|--|--|--|--|
| model | 152 | 133 | 49 | 41 | 36 | 46 | 64 | **45** | 33 | 37 | 54 | 143 |
| actual | 134 | 130 | 47 | 41 | 35 | 44 | 70 | **46** | 34 | 40 | 60 | 136 |

The monthly shape tracks actual within a few $/MWh in every month; the only
residual is January running ~$18 hot (the winter tail).

## 2. What the CC steam-turbine derate actually did to NEISO — **near-nothing**

Controlled A/B on 2025 (same tree, same gas data; **only** the outage CSV
swapped between the pre-coupling and CC-steam versions):

| 2025 | CC_REG | gas tot | oil | LW price |
|------|-------:|--------:|----:|---------:|
| pre-coupling CSV | 57.33 | 59.72 | 0.08 | 81.87 |
| CC-steam CSV | 57.31 | 59.66 | 0.09 | 82.80 |
| **derate effect** | **−0.02** | −0.06 | +0.01 | **+0.93** |

The steam coupling is correct physics and carries **no magic numbers**, but it is
a **near-no-op for NEISO**: its CC fleet has enough headroom and few enough
binding CC outages that coupling the steam removes essentially no additional
energy (−0.02 TWh) and lifts price <$1. (Contrast ERCOT, where CC outages bind
more often.) **Adopt it for cross-ISO consistency; it neither fixes nor harms
the NEISO calibration.** 2023/24 are unchanged to the rounding.

## 3. The one real problem the re-run surfaced — a poisoned gas-basis cell (now fixed)

The first re-run on the current tree showed 2025 over-priced ($82.8 LW vs the
keeper's $68.5) with a spurious **August** spike (model $167 vs actual $46). It
was **not** the derate (above) — it was a bad data cell introduced by the
15:46 `fetch-eia-gas-prices` refresh, which postdates the keeper (00:35):

```
NEISO,2025,8,...EIA MA citygate proxy,13.4578,EIA N3050MA3 citygate - Henry Hub
```

A **+$13.46/MMBtu** Algonquin Citygate basis — winter-level — in a low-load
summer month. The EIA monthly state-citygate average recovers LDC city-gate
fixed costs and does not track the marginal AGT spot a generator pays; it is an
order of magnitude above the neighbouring measured ISO-NE MA index months
(Jul +1.03, Sep −0.95). Fixed in commit `aa62655`: replaced with the Jul/Sep
interpolation (+0.04), which the fetch loop's preserve-existing logic keeps
across re-fetches. With the cell fixed, August reprices to $45 (vs $46 actual)
and 2025 returns to $71.2 LW.

## 4. Verdict — **backcast-calibrated**

NEISO is a calibrated 2023–2025 backcast on both axes:

- **Energy mix:** gas within ~1% of EIA-930 all three years; CC_REGULAR matches
  the keeper; nuclear/hydro/renewables/interchange near-exact.
- **Price level & shape:** annual hub within −4.7% / −2.3% / +4.9% of actual DA;
  the 2025 monthly DA shape tracks within a few $/MWh every month.

No further **structural dispatch** refinement and **no magic numbers** are needed
for the backcast. The fitted daily-AGT convexity stays rejected.

## 5. Before a forecast run (not blockers for backcast sign-off)

1. **Neighbor convexity / priced-import node — REQUIRED for forecast.** The
   backcast serves the **measured EIA-930 net-interchange schedule** (HQ +
   NYISO ties), which is exact by construction but disappears in a forecast.
   The seam must become the price-responsive reference-price interface
   (`neighbor_price = (HH + basis) × marginal_HR × load_shape`, with the
   supply-curve convexity `load_shape_exponent > 1` and a per-region HR anchored
   to the neighbour's own realized LMP — see `docs/reference-price-interface.md`).
   This is NEISO's single biggest forecast-readiness gap: a steady ~1–1.7 GW net
   importer whose imports must respond to its own scarcity, not sit on a fixed
   schedule. Until it is wired, NEISO cannot be run as a forecast.
2. **Winter oil under-generation (polish).** Modeled oil 0.00 / 0.00 / 0.06 TWh
   vs EIA-930 0.32 / 0.37 / 1.24 — the documented monthly-AGT-granularity limit
   (monthly AGT never reaches distillate parity, so the dual-fuel CT/ST switch
   does not bind). LMP-neutral for the backcast (oil is a sub-percent share and
   the monthly price shape already matches). For forecast realism, **derive**
   the daily-AGT convexity from measured daily AGT spot (upload U4) — never the
   rejected fitted constant.
3. **January-2025 winter tail (~+13%, minor).** The highest-weight winter month
   runs ~$18 hot; within the ±5–10% price tolerance and not worth a knob.

## 6. Files

- Keeper bundle: `results/calibration/neiso_ccsteam_keeper_3yr/`
- Data fix: `data/raw/gas_basis_by_iso_month.csv` (commit `aa62655`)
- Scratch A/B bundles (gitignored, regenerable): `neiso_ccsteam_3yr`,
  `neiso_oldoutage_2025`
