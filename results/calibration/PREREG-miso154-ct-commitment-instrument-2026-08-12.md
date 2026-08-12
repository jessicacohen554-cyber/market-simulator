# PREREG — miso-154: the **CT commitment instrument**

**Session** miso-154 · **ISO** MISO · **Date** 2026-08-12 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**This document is pushed and blob-verified against the FETCHED remote ref
BEFORE any adjudicating statistic is computed** (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 ONLY. MISO holds **no** marker.
No holdout year is read, solved or scored anywhere in this session.

**NO LP SOLVE.** The deliverable is a reusable probe helper. Rule 15 is not
engaged (a no-run session produces no run — the miso-142 / miso-153
precedent). No `ScenarioConfig` field is added, so rule 28(c) is not engaged.
No mechanism is armed or tested, so **no matrix cell verdict is minted**.

---

## 1. The object

miso-153 §6 / §13 left the lane one blocking dependency, re-confirmed
independently after the `weather_year` repair:

> the price-taking reconstruction runs **+22.0 / +22.1 / +23.7 %** hot on
> `CT_PEAKER` in every year (miso-153 T-6b; miso-152 hit the same wall at
> +38–40 %). **CT volumes are currently unmeasurable**, so every CT
> object — offer LEVEL, fill-order — is descriptive-only.

The charter: build a reconstruction that reproduces **CT commitment**
(startup cost, min-run/min-down, the P1 startup amortization) rather than
pure price-taking, and validate it against the keeper's committed
`class_hourly`.

**The diagnosis this PREREG commits to, before measuring it.** miso-153's
T-6b compares `mc_base` against the keeper's **P1** clearing price. But
MISO's P1 clears on the **bid** cost, `mc_bid = mc_base + markup`
(`pipeline/solve.py:254-265`), where `markup` is the monthly startup
amortization `startup_cost / run_length`
(`model/commitment.py::compute_monthly_markup`). Comparing a **base** cost
against a **bid**-cost clearing price admits every tranche whose startup
recovery has not been earned. **That mis-specification, not a defect in the
fleet, is what I expect the +22–24 % to be.**

### 1.1 What I inspected BEFORE writing this document (disclosure)

Honest record of what was already on screen, so no reader mistakes a tuned
prior for a blind one. All of it is **instrument construction** — code paths,
armed gates, and input-artifact schema — **none of it is a statistic about
the residual**:

* `pipeline/solve.py:252-292` (the P0 → markup → P1 seam) and
  `model/commitment.py:210-331` (`compute_monthly_markup`).
* The keeper's `run_config.json` gates: `tranche_startup_amortization=True`,
  `tranche_startup_measured_runs=True`, `tranche_startup_conditional_runs=True`,
  `gas_st_startup_cost=True`, `gas_st_startup_spread=True`,
  `chp_startup_covered=False`, `coal_warm_committed=True`,
  `commitment_enabled=False`, `class_commitment_overrides={}`,
  `reliability_floor_overrides={}`.
* **Confirmed armed-mechanism surface:** MISO arms **no** P1 bid adjustment,
  **no** bid-max target, and **no** commitment bridge (`miso_commitment_posture`,
  `caiso_ra_mustoffer`, `ercot_gas_commitment_bridge`,
  `nyiso_gas_commitment_bridge` all `False`; every `*_offer_surface_*` off).
  So MISO's P1 bid is **exactly** `mc_base + markup` — the instrument has one
  seam to reproduce, not several.
* `data/raw/_processed-legacy/campd_ct_run_bands_MISO.csv`: pooled median run
  **10.0 h**; band ratios **0.9 / 1.1 / 1.1 / 0.8 / 0.6** over net-load
  percentile bands `[0, .5, .75, .9, .975, 1]`.
* The keeper's `hourly/` sidecar schema — **only `pass == "P1"` is committed**.
  There is **no committed P0**, which is why §3 Stage 2 must reconstruct one.

**Not inspected:** any CT startup-cost level, any markup magnitude, any
reconstruction residual. The §4 prior is reasoned from the mechanism above,
not read off the answer.

---

## 2. Scope, and what is deliberately NOT in it

**IN.** A reusable probe helper `scripts/probes/_miso154_ct_commitment.py`
exposing the reconstruction as importable functions (not a one-off script
body), plus its record
`results/calibration/_miso154_ct_commitment.json`.

**OUT — and each is a standing DO-NOT-REDO or an owner decision:**

* Any CT offer-**LEVEL** lever. It is reachable **only** through a SECOND
  PREREG, and **only** if the bar in §5 clears.
* The across-unit dispersion object — **CLOSED** on three measured grounds
  (miso-153 §12–§13). Not re-opened.
* The D-4 all-hours-window governance flag — **RAISED, INVESTIGATED,
  WITHDRAWN** (miso-153 §11). Not re-raised.
* The MISO outage extract (`X_cc = 0.240`) and the 2025 EIA-860 vintage
  under-carry — cross-ISO, not this lane's (miso-153 §3).
* C7 `COAL_PRB` — deprioritized by standing owner directive. No C7 lane, no
  C7 ledger.
* The offer-side class bridge — **built and REFUTED at miso-138**. The
  instrument is identified from **CAMPD unit conduct via the production
  fleet**, never from the masked offer book.

---

## 3. The instrument — construction, fixed here before it is built

Per year `y ∈ {2023, 2024, 2025}`, **no LP**, everything from HEAD production
code + the keeper's own committed artifacts.

**Stage 1 — assemble.** `build_year(dataclasses.replace(cfg, weather_year=y), y)`
→ `(raw_fleet, fleet, arrays, fuel_prices, mc_base, zone_names)`. The
`weather_year` pin is trap **T-6** and is non-optional.

**Stage 2 — P0 reconstruction** (the run-length source the markup needs).
There is no committed P0, so P0 dispatch is reconstructed price-taking on
`mc_base` against the keeper's own P1 zonal prices:
`p0[g,t] = pmax[g]·avail[g,t]` where `mc_base[g,t] ≤ price[zone(g),t]`, else 0.

> **Declared bias, and it runs AGAINST this session's conclusion.** P1 prices
> are ≥ P0 prices (P1 adds a non-negative markup to every offer), so this
> **over**-states P0 running → **longer** runs → a **smaller** markup → **more**
> CT admitted → the reconstruction stays **HOT**-leaning. The bias makes the
> §5 bar **harder** to clear, not easier. Bounded explicitly by T-9.

**Stage 3 — markup.** The **production** `compute_monthly_markup` (T-8
asserts the symbol's module), called with the keeper's own gates
(`gas_st_season_spread`, `gas_st_startup_cost`, `chp_startup_covered`,
`coal_warm_committed`) and `run_ratio_t` reconstructed per §3.1.

**Stage 3.1 — the v4 conditional band series.** `run_ratio_t` keys on the
hour's within-year net-load percentile. Production computes net load from
renewable **potential** (`cap × cf`); the committed sidecars carry only
**dispatched** wind/solar. The reconstruction therefore uses
`net_load = ISO demand − wind − solar` from the keeper's own `class_hourly`,
banded with the committed `campd_ct_run_bands_MISO.csv` edges. **Bounded by
T-10**, which reports the bar under `run_ratio_t ≡ 1.0` (the v3 basis) as
well.

**Stage 4 — the P1 bid.** `mc_bid = mc_base + markup`. Nothing else: §1.1
establishes MISO arms no further P1 bid seam.

**Stage 5 — the P1 reconstruction.** Two legs, both reported:

* **L1 — price-taking on the BID.** `recon[g,t] = pmax·avail` where
  `mc_bid ≤ price[zone(g),t]`. This is miso-153's T-6b with the single
  mis-specification of §1 corrected, so it is **directly comparable** to the
  published +22.0 / +22.1 / +23.7 %. **L1 is the gating leg.**
* **L2 — merit-order clearing** (declared refinement, reported, **ungated**).
  ISO-wide: min-gen floors (`arrays.min_gen`, falling back to
  `pmin`-broadcast) dispatch first; the remainder of the residual thermal
  demand implied by the keeper's own `class_hourly` is filled in ascending
  `mc_bid`. Conserves energy by construction and resolves the marginal
  tranche's partial loading, which L1 cannot.

**Stage 6 — validation.** `CT_PEAKER` energy, reconstruction vs the keeper's
committed `class_hourly`, at the **top-200 model-demand hours** (the miso-153
window, unchanged), with the annual figure reported alongside, ungated.

---

## 4. The prior — two-sided, numeric, committed before measurement

`resid ≡ (E_recon − E_keeper) / E_keeper` for `CT_PEAKER` over the top-200
hours. The published price-taking baseline is **+22.0 / +22.1 / +23.7 %**.

**PRIOR: L1 `resid` lands in `[−15 %, +15 %]` in at least 2 of 3 years,
centred on `+2 %`** — i.e. the markup removes most, but plausibly not all, of
the +22–24 pp, and may over-shoot into negative territory.

**It is genuinely two-sided.** The markup is bounded below by
`startup / (measured_run × band_ratio)` and the peak band ratio is **0.6**,
so at exactly the top-200 hours the markup is at its **largest**. An
over-correction into a *cold* CT reconstruction is a real outcome of this
construction, not a courtesy branch.

**Pre-committed surprise triggers:**

| trigger | fires when | what I do |
|---|---|---|
| **S-LOW** | `resid < −25 %` in any year | The markup is over-applied — suspect double-counting against something already in `mc_base`, or a P0 reconstruction that is too cold. **Investigate and disclose before reporting any conclusion.** |
| **S-HIGH** | `resid > +18 %` in **all three** years | The markup is **not** the driver. The instrument has not found the cause; **that** becomes the finding, and no lever follows. |
| **S-INERT** | cap-weighted CT markup ≈ 0 at the top-200 hours | The instrument is inert; the exercise is void (trap T-7). |

---

## 5. The gating bar — fixed, with its reasons, before measurement

**BAR (from the charter): `|resid| ≤ 10 %` for `CT_PEAKER` at the top-200
demand hours.** Evaluated **per year**, and the branch is decided on the
count of years that clear — pre-committed here so the per-year/pooled
ambiguity that miso-153 §6 had to disclose cannot recur:

| branch | condition | consequence |
|---|---|---|
| **B-CLEAR** | clears in **3 of 3** | The instrument is **validated**. CT volumes become measurable. **THEN and only then** a SECOND PREREG proposes **ONE** CT offer-LEVEL lever, stating its expected 2023 effect **before** any solve. |
| **B-PARTIAL** | clears in **2 of 3** | Reported at full magnitude. **NO lever.** The failing year's residual is the finding, and the instrument ships as a helper with its limitation stated in its own docstring. |
| **B-FAIL** | clears in **≤ 1 of 3** | The instrument does **not** validate. **NO lever.** Report the residual, the diagnosis, and what remains unreproduced. |

**The bar is on L1**, the leg directly comparable to the published baseline.
L2 is reported but never gates — it conserves energy by construction, so a
good L2 total is partly an artifact of its own clearing and must not be
allowed to buy a pass.

**Magnitudes are reported in BOTH branches, always** (the charter's standing
trap: a gate bar of "bit-identical" on floating-point data is unsatisfiable —
every bar here is a tolerance and every report states the number).

---

## 6. Traps, each with its counter-measurement

Carried from miso-153 (T-1…T-6), which paid for them; T-7…T-11 are new to
this instrument.

| # | Trap | Counter-measurement |
|---|---|---|
| **T-1** | `_miso134` is HARD-WIRED to `miso132_ccmin_B` — inheriting it screens the wrong keeper silently | Repoint to `miso148_basis_B` and **assert** `run_config.json` exists; report matched/dropped key counts |
| **T-2** | `getattr(obj, field, default)` on the offer path silently encodes the wrong field name | **Zero** 3-argument `getattr(` in the probe; `grep` count reported; `ruff` clean |
| **T-3** | The econ block smooths into `econc00..econc05`; collapsing one-per-band keeps only the DEAREST and yields a spurious exact 0.0 | Dump the **full raw suffix inventory** before any aggregation. **Disbelieve clean zeros** — any exact 0.0 gets a second, different derivation or is reported as unverified |
| **T-4** | `SimpleNamespace` fixtures encode the same wrong field name as the code and cannot fail | Every array from **production types** (`generators_to_fleet_arrays`); assert no `SimpleNamespace` in the probe |
| **T-5** | `MISO_external` / `MISO_external_South` are IMPORT NODES | Assert carry-zone count **== 6**; import nodes excluded from every price/demand aggregate |
| **T-6** | `_miso134.build_year` keys the CAMPD outage derate on `config.weather_year`, not the solve year — one config silently applies 2023's outage windows to 2024/2025 | `dataclasses.replace(cfg, weather_year=y)` per year, **plus its own control**: 2023 must be **unchanged** (tolerance `1e-9`, magnitude reported) since its `weather_year` already was 2023 |
| **T-7** | An inert instrument would "clear" nothing and look like a fix | Report cap-weighted CT markup `$/MWh` at the top-200 hours **and** its full distribution. Markup ≈ 0 ⇒ **S-INERT**, exercise void |
| **T-8** | A re-implemented markup would reproduce my own expectation, not the model's | **Assert** `compute_monthly_markup.__module__ == "market_sim.model.commitment"`. The production function, never a copy |
| **T-9** | The P0 price proxy (P1 prices) is not P0 | Recompute the markup on **three** P0 bases — (a) P1-price price-taking, (b) **no** P0 runs (markup at its measured ceiling, i.e. **maximum** markup), (c) always-on P0 (markup **floor**) — and report L1 `resid` under all three. This **bounds** the proxy error instead of assuming it away |
| **T-10** | `run_ratio_t` needs renewable **potential**; the sidecars carry **dispatched** | Report L1 `resid` under the reconstructed v4 ratios **and** under `run_ratio_t ≡ 1.0` (v3). A gap < 2 pp ⇒ immaterial; ≥ 2 pp ⇒ disclosed as a live limitation |
| **T-11** | The charter names min-run/min-down, but MISO arms no bridge and no P2 — the LP may not enforce them at all | Build an **optional min-run-enforcing L1 variant** and report its `resid`. If enforcing min-run makes the fit **worse**, that is positive evidence the LP does not carry it — reported as such, at full magnitude |

---

## 7. Rules engaged

* **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`** — the instrument is judged on
  whether it reproduces the model's own mechanism, never on whether it
  flatters the residual.
* **Rule 13 `[R-MEASURED]`** — every input is a reproducible physical/market
  quantity (CAMPD-measured run lengths, startup costs, delivered fuel).
  **Nothing is pinned to a measured outcome.** The reconstruction is
  validated against the keeper's own model output, which is not an actual.
* **Rule 19 `[R-ONE-MECH]`** — no floor, bridge or adder is added. The
  instrument reproduces the **existing** amortization; it does not stack a
  second one.
* **Rule 21 `[R-DOF]`** — the instrument introduces **zero** free parameters.
  Every constant is read from committed artifacts or HEAD production code.
* **Rules 23 / 24 / 25** — no derive is re-run, no off-registry knob, no
  cross-ISO transfer.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only.
* **AGAINST-INTEREST BOUND (binding):** 2023 passes C3a at **−0.3 %**. A lever
  that lifts 2023's mean by more than **+3 %** is a **REGRESSION** even if 2025
  improves. **This session runs no solve and applies no lever**; the bound is
  restated here so the SECOND PREREG — should §5 reach B-CLEAR — inherits it
  and must state the expected 2023 effect **before** solving.

---

## 8. §10 disclosure standard

Any statistic computed in this session that is **not** in §3–§6 is labelled
**NOT PRE-REGISTERED** where it is reported, with its counter-measurement and
its **full magnitude** — in both the favourable and the unfavourable branch.
Scope extensions are disclosed, never silently folded in.
