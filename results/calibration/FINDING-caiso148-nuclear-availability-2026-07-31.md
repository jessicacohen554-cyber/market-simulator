# FINDING — caiso-148 `nuclear_unit_availability` for CAISO

**Session:** caiso-148, 2026-07-31. **Lever:** mechanism-matrix §5.2 CAISO queue
**item 8**, `nuclear_unit_availability` (cells `KUUUKU` at entry; `K` in ERCOT on
its own flag/file, `K` in NYISO at nyiso-98, CAISO `U`).

**Pre-registration:** `PREREG-caiso148-nuclear-availability-2026-07-31.md`,
committed and pushed **before either arm solved**.

**Base keeper:** `2026-07-31-caiso147-chp-heat-rates`,
CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 ledgered non-protective caveats, 1 of 3
slots free, protective 0/1. CAISO holds **no** rule-22 calibration-complete
marker; this session solved **2023 2024 2025 only** and wrote no marker.

**Rule 25 `[R-ISO-SCOPE]` up front:** ERCOT's and NYISO's `K` verdicts transfer
**nothing**. Everything below is derived from CAISO's own reactors and CAISO's
own market data. The only thing inherited is the deriver's frozen constants
(rule 23 `[R-FROZEN-DERIVE]`).

---

## §A — the ex-ante wall check: NOT walled

The handoff required this be settled first, because queue item 5
(`unit_outage_short_windows`) was adjudicated INERT ex ante at caiso-136 on a
**coal-only CEMS detector** meeting a **CEMS-invisible** CAISO coal class. If
item 8 shared that detector it would have been adjudicated `I` the same way,
costing no solve.

**It does not, and the two share no input.** `unit_outage_short_windows` reads
CAMPD/CEMS. `nuclear_unit_availability` reads the **NRC daily Power Reactor
Status Report** (`data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt`,
`ReportDt|Unit|Power`, `Power` = percent of licensed thermal power at the morning
report; US-government public domain, fetched by
`scripts/data/fetch_nrc_reactor_status.py`). **Nuclear units carry no CO₂ and are
not CEMS reporters in any ISO**, so CEMS visibility is structurally irrelevant to
this lever everywhere. caiso-136 has no bearing on item 8.

---

## §B — the derive (STEP 1, no LP)

`scripts/data/derive_nuclear_availability.py --iso CAISO` →
`data/raw/nuclear-availability-CAISO.csv`.

**No source change was needed to arm CAISO.** The application seam
(`data/fleet/arrays.py`, the `_iso != "ERCOT"` block) and the loader
(`data.outages.nuclear_unit_availability_series`) were already ISO-generic. The
session's only code delta is a **two-row identifier crosswalk** in `NRC_TO_EIA`:

```
"CAISO": {"Diablo Canyon 1": (6099, 1), "Diablo Canyon 2": (6099, 2)}
```

That is an identifier map, not a tunable (rule 24 `[R-REGISTRY]`). **Zero fitted
scalars** — `EVENT_RAW_MAX = 0.90`, `SCALE_CLIP = 1.25`, `WEDGE_TOL = 0.01` are
inherited frozen and untouched.

**Unit rows.** 1,886 rows / **2 reactors** — Diablo Canyon 1 (EIA `6099_1`,
1,122 MW) and 2 (`6099_2`, 1,118 MW), both zone NP15, fleet 2,240 MW. That is
**100 % of CAISO's nuclear capacity and unit count**; SONGS 2/3 retired 2013 and
Rancho Seco 1989, and neither carries an NRC row nor a model fleet unit. NRC
reports both reactors on **365 / 366 / 365** days — no source gaps.

**Windows found: 18** in the covered extract (`avail_raw < 0.90`), three of them
major refuels:

| reactor | window | days | mean raw |
|---|---|---|---|
| DCPP-1 | 2023-09-27 → 2023-11-17 | 52 | 0.102 |
| DCPP-2 | 2024-04-07 → 2024-05-25 | 49 | 0.038 |
| DCPP-2 | 2025-10-05 → 2025-10-31 | 27 | 0.000 |
| DCPP-2 | 2025-08-05 → 2025-08-15 | 11 | 0.476 |
| DCPP-1 | 2023-12-09 → 2023-12-17 | 9 | 0.022 |
| DCPP-1 | 2023-03-13 → 2023-03-20 | 8 | 0.568 |
| DCPP-2 | 2023-11-10 → 2023-11-17 | 8 | 0.519 |
| DCPP-2 | 2025-03-11 → 2025-03-15 | 5 | 0.512 |
| + 10 shorter (1–3 d) | | | trips / grid-related reductions |

**Coverage: 2023 365/365 (100 %), 2024 366/366 (100 %), 2025 212/365 (58.1 %)**;
**31 of 36 months**, 1,886 of 2,192 reactor-days (86.0 %).

### B.1 — the five dropped months, and why the drop is CORRECT

All five are 2025 (Apr, May, Jul, Nov, Dec) and the selection is **systematic,
not random**: each is a month containing a *real event* (refuel, trip or ramp)
whose **non-event pool is already saturated at 100 %**, so the capped fixed-point
cannot scale **up** to reach the anchor. Worked example, 2025-07: DCPP-1 at 100 %
all 31 days, DCPP-2 at 55 % on Jul 5–6 and 100 % otherwise → fleet 0.98554
against an anchor of 1.00; the two event days are held as measured and every pool
day is already at the 1.0 cap, so the maximum achievable is 1.45 % below anchor.

**This session measured the cause rather than assuming it.** EIA-930 CISO
`NG: NUC` peaks at **2,281 / 2,279 / 2,309 MW** against the model's 2,240 MW
EIA-860 nameplate — Diablo runs up to **+3.1 % above nameplate**, so a full-power
month's EIA-923 ratio (net generation ÷ nameplate × hours, **clipped at 1.0** per
the constants' own construction) hits the clip, and NRC-%thermal × nameplate can
never express it. Posting the NRC level in those months would **delete real
capability**. The deriver drops them, the loader NaNs them, and the smear stands
— rule 14 `[R-ACCURATE]`'s misalignment clause operating exactly as designed.

**Consequence, accepted in advance and not engineered around:** in 2025 the U1
Apr–May refuel, the Jul U2 derate and the Dec U1 trip keep the smear; only the
**October U2 refuel** carries measured timing. 2023 and 2024 are fully covered.
This was stated in the pre-registration §2 before either arm solved.

### B.2 — independent-source validation

Validated against **EIA-930 CISO metered hourly nuclear** — a source independent
of both NRC (the timing input) and EIA-923 (the level anchor).

NRC-derived available MW vs EIA-930 metered daily mean, 942 fully-covered days:
**r_day 0.9807** overall (0.9708 / 0.9918 / 0.9876), bias **−1.8 / +13.7 /
+20.0 MW** on a 2,240 MW fleet (≤ 0.9 %), MAE 43.2 / 28.7 / 36.2 MW (1.3–1.9 %).

**The nyiso-98 EIA-930 zero-block artifact was screened for and does NOT occur in
CISO**: 23 exact-zero hours in 2023 (25 hours < 50 MW), **0** in 2024 and 2025 —
against NYISO's 1,179 / 380 / 117. CISO `NG: NUC` is therefore usable directly as
an independent check, and nyiso-98's gap-masking step is not needed here. This is
a CAISO-specific determination; it says nothing about any other ISO's 930 series.

### B.3 — build-time gates (the nyiso-98 set), all PASS

| gate | test | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|---|
| **G1** | raw-NRC r_day lift ≥ +0.10 | +0.1836 | +0.1447 | +0.1327 | PASS |
| **G2** | reconciled retention of raw lift ≥ 70 % | 100.1 % | 100.2 % | 100.1 % | PASS |
| **G3** | annual \|ΔTWh\| < 0.5 % | 0.0001 % | 0.0239 % | 0.0746 % | PASS |

Overlay vs smear against metered, on covered days: r_day **0.7873 → 0.9709**,
**0.8474 → 0.9921**, **0.8550 → 0.9878**; MAE **156.4 → 47.2**, **100.7 → 31.3**,
**125.0 → 39.9 MW**.

### B.4 — regression (rule 25)

`--check` reproduces `nuclear-availability-PJM.csv` and
`nuclear-availability-NYISO.csv` **byte-for-byte** after the CAISO addition. No
other ISO's artifact moves.

---

## §C — the reserve-requirement framing, CORRECTED before it could be quoted

The handoff framed Diablo as "the 2,240 MW MSSC that sets CAISO's ENTIRE reserve
requirement … it moves the reserve floor for the whole ISO." **That is not how
the keeper is wired**, and this finding does not claim it. Verified in
`caiso147_chp_B/run_config.json`:

- `energy_reserve_coopt = False`, `caiso_reserve_coopt = False` — the reserve
  co-optimization is **not armed**, consistent with caiso-144's `I` /
  DO-NOT-SOLVE adjudication.
- `as_reserve_formula = False` — the `max(MSSC, 0.067×load)` withholding formula,
  the one place a live MSSC would enter the LP, is **off**.
- `caiso_scarcity_pricing = True`, but its MCL is a **static 1,400 MW tariff
  constant**, not keyed to Diablo's hourly availability.

**There is no dynamic MSSC channel in this A/B.** The live channels are:

1. **Primary — within-month daily re-timing** of nuclear availability, displacing
   energy on and off the marginal classes.
2. **Secondary — the `caiso_scarcity_pricing` overlay's `reserve_headroom`.**
   Nuclear contributes ~0 to either reserve tier itself (at pmax it has no
   headroom; out, it is a cold slow-start unit backing neither tier), but the
   *displaced* energy loads gas units higher, cutting their headroom and raising
   the LOLP adder. Second-order.

**Binding on successors:** do not cite caiso-148 as evidence about CAISO's
reserve floor or MSSC. It tested neither.

---

## §D — the "0 reactors" log line is NOT a defect (diagnosed, not left open)

Arm B's log contains two overlay lines per year:

```
CAISO nuclear unit-availability overlay (2023): 0 reactor(s) ...
CAISO nuclear unit-availability overlay (2023): 2 reactor(s) ...
```

The `0` comes from `assembly.bins_to_fleet` (lines 96–1111), which builds
`FleetArrays` for the **CAMPD-binned thermal fleet only** — that fleet contains
no nuclear by construction, because for non-ERCOT ISOs nuclear joins later
through `build_base_fleet`'s `non_thermal` list. The `2` is the dispatch fleet
build at `runner.py:1118`, which is the one the LP consumes. **The mechanism is
correctly armed.** The duplicate line is pre-existing, ISO-generic log noise
(PJM and NYISO emit it identically) and was not changed here.

---

## §E — the A/B

*(filled from the solved arms — see §F for the verdict)*

## §F — verdict

*(pending)*

## §G — DO-NOT-REDO (binding on successors)

*(pending)*
