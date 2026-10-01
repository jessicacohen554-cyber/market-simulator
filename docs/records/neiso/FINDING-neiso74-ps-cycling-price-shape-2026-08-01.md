# neiso-74 — NEISO pumped-storage under-cycling is a PRICE-SHAPE defect, not a storage-side one

**Date:** 2026-08-01 · **ISO:** NEISO · **Keeper (unchanged):**
`2026-07-31-neiso-72-hy-window` (`results/calibration/neiso72_hy_window_B`)
**Verdict: Lever A (storage-side PS cycling depth) REFUSED AT THE SCREEN — NO LP SPENT.**
**Probe:** `scripts/probes/_neiso74_ps_cycling_screen.py` (read-only, 2023–2025).

---

## 0. The question and the answer

neiso-72 left the post-split `NG: PS` column as NEISO's first measured
pumped-storage series: **1.932 TWh discharged in 2025** against the keeper's
endogenous **0.497 TWh** (~4×). The handoff named a storage-side lever —
dispatch adder, AS value, duration, RTE — to close it.

The screen separates the only two candidate root causes, because rule 1
`[R-STRUCT]` forbids patching the second with a storage-side parameter:

* **H1 — storage-side.** The model's storage physics/objective is wrong, so even
  facing the *real* price shape it would refuse to cycle.
* **H2 — price-shape.** The storage physics is right and the model's own diurnal
  spread is too narrow to clear the round-trip hurdle. Then the defect is
  upstream and a storage-side knob is a fitted patch on someone else's residual.

**The measurement returns H2, unambiguously and with the opposite sign to the
handoff's premise.** Given the *measured* NEISO price vector, the model's OWN
storage physics does not under-cycle — it **over-cycles by 2.2×**.

---

## 1. The discriminator

A perfect-foresight price-taker LP with the model's exact storage physics
(1,865.0 MW from `load_eia860_pumped_storage`; `PUMPED_STORAGE_DURATION_HOURS`
10.0 h → 18.65 GWh; `PUMPED_STORAGE_RTE` 0.80, one-way 0.8944; cyclic SOC; the
rule-9 `[R-EPSILON]` 0.001 $/MWh tiebreaker), solved on CSC → HiGHS. Only the
price vector changes between rows.

| price vector fed to the SAME storage LP | 2023 | 2024 | 2025 |
|---|---|---|---|
| measured NEISO **DA** hub | 4.331 TWh | 4.411 TWh | **4.301 TWh** |
| measured NEISO **RT** hub | 4.579 TWh | 4.799 TWh | 4.691 TWh |
| **model P1 duals** | 0.370 TWh | 0.339 TWh | 0.612 TWh |
| *keeper's own endogenous PS* | *0.400* | *0.363* | *0.497* |
| **measured actual (`NG: PS`)** | n/a | *partial* | **1.932** |

Two readings, both decisive:

1. **The storage block is innocent.** The keeper's endogenous PS (0.400 / 0.363
   / 0.497 TWh) brackets the perfect-foresight optimum on its own prices (0.370
   / 0.339 / 0.612). The LP's storage is already doing what an optimal
   arbitrageur would do with the price signal it is shown.
2. **The price signal is the constrained object.** Swap in measured prices and
   the same physics discharges **4.3–4.8 TWh** — *2.2× the 1.932 TWh actual*,
   not 4× below it. No storage-side parameter can be the fix, because the
   parameters are not what is binding.

## 2. Sizing the real defect: diurnal amplitude, not level and not phase

| 2025 (vs measured DA) | model | measured DA | gap |
|---|---|---|---|
| annual level | $69.75 | $67.86 | **+2.8 %** |
| mean daily MAX | $78.57 | $106.51 | **−26.2 %** |
| mean daily MIN | $63.95 | $48.24 | **+32.6 %** |
| mean daily spread | $14.62 | $58.27 | **25 %** of measured |
| hour-of-day mean range | $13.30 | $44.47 | **30 %** of measured |
| daily max/min ratio, p50 | 1.19 | 2.07 | — |
| days clearing the 1.25× RTE hurdle | **86**/365 | **365**/365 | — |

Stable across all three years — 2023: level +3.9 %, max −26.2 %, min +40.8 %,
spread $8.11 vs $33.85, 45/365 days over the hurdle. 2024: +5.0 %, −25.3 %,
+40.0 %, $7.41 vs $35.29, 43/365. Against measured **RT** the compression is
larger still (daily spread $55.38 / $57.49 / $83.26).

**The level is right and the phase is right; only the amplitude is wrong.** The
model's hour-of-day price peaks at **h17** in every year — the same hour as the
measured DA curve — and troughs at h2 against DA's h2/h3. This is a pure
amplitude defect: the model knows *when* the peak is and clears it ~26 % too
low while holding the overnight trough ~33–41 % too high.

## 3. What the measured PS fleet actually does (2025, the wholly-split year)

`NG: PS` is **strictly non-negative** — 5,682 h above +1 MW, **0 h below −1 MW**
— so it is gross discharge with pumping load booked to Demand, confirming
neiso-72's read. Coverage 0.997 (2024 is 0.148, post-seam only, and is not a
full-year observation).

Hour-of-day mean MW / fraction of hours online:

```
h00  14 (0.11)  h02  11 (0.11)  h06 174 (0.53)  h11 128 (0.67)
h14 141 (0.77)  h17 636 (0.99)  h18 728 (1.00)  h21 277 (1.00)
```

A wide, price-following afternoon–evening discharge block that peaks at h18 and
is essentially offline h00–04 — **phase-aligned with the DA price curve**. The
real fleet is not running some flat non-arbitrage reserve duty the model is
missing; it is doing the same thing the model does, against a price shape four
times deeper.

## 4. Why every storage-side knob is inadmissible here

| candidate | why it is refused |
|---|---|
| `pumped_storage_dispatch_adder` (NEISO entry) | Raises the discharge hurdle ⇒ **less** cycling — wrong sign. The map is empty at every ISO because it was retired at PJM for precisely this failure mode (`constants.py` `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO`: a $10 knob fitted to a mis-measured target). Re-arming it here is rules 21/24/26. |
| `PUMPED_STORAGE_RTE` ↑ | Shared cross-ISO constant — fitting it on NEISO's residual is rule 25 `[R-ISO-SCOPE]`. And no measured NEISO RTE would move throughput 4×; a value chosen to land 1.932 TWh is a fitted parameter (rules 21/24). |
| `PUMPED_STORAGE_DURATION_HOURS` | Same objection, plus the wrong lever: with only 86/365 days clearing the hurdle, energy capacity is not the binding constraint. |
| AS / reserve power reservation | Reduces energy cycling further (wrong sign), and §3 shows the measured duty is price-following, not a flat reserve block — the AS story is not what the data shows. |

Any of them tuned to close 1.932 − 0.497 TWh would be sizing a storage parameter
to an **upstream price residual** — rule 1 `[R-STRUCT]`, rule 19 `[R-ONE-MECH]`,
rule 21 `[R-DOF]`.

## 5. Where the amplitude is lost (attribution, for the successor)

Model 2025 P1, hour-of-day means. Demand swings **10,504 MW (h02) → 14,621 MW
(h17)**, +4,117 MW. `CC_REGULAR` absorbs **2,045 MW** of it (5,752 → 7,797,
49.7 % of the swing) and hydro **+809 MW** (19.6 %); `CT_PEAKER` moves only
**+209 MW** (114 → 323, 5.1 %) and `oil` **+99 MW** (159 → 259, 2.4 %).
Critically, **`CT_PEAKER` and `oil` are already online at the overnight
trough** — so the same offer band is marginal at h02 and at h17, and the
clearing price barely moves. The model's annual price *distribution* is wide
(p10 $37 → p90 $137); that variation is seasonal/fuel-driven, not diurnal.

The named identification class for this is already on the NEISO queue:
**§5.6 item 1, DA-bid offer formation / DA depth** (NEISO publishes DA cleared
and bid data; `data/raw/NEISO-AS/da-energy-offers/` exists but currently holds
only a README). It requires its own owner charter — unchanged by this session.

## 6. Reported against interest

* **The handoff's premise is inverted.** It asked for a lever adding cycling
  depth on the storage side; the measurement says the storage side, fed real
  prices, would over-cycle by 2.2×.
* **A price-shape fix must NOT be graded on "does PS reach 1.932 TWh."** The
  real fleet realizes only **45 %** (1.932 / 4.301) of the DA-price
  perfect-foresight optimum. Correcting the price shape without also
  representing the non-arbitrage limits (imperfect foresight, min-run, head and
  reservoir limits, reserve duty) would push model PS *past* the actual. Any
  successor that lands PS on 1.932 TWh by tuning storage is a fitted answer.
* **No load-bearing criterion sees this defect.** C3a is a level test (PASS,
  +2.8 %). **C3b is a MONTHLY load-weighted price NRMSE**
  (`scripts/calibration_verdict.py::score_price_shape`) — a *seasonal* shape
  test, structurally blind to hour-of-day. C7 (D-1) scores class *dispatch*
  shape and is SKIPPED for NEISO. So the keeper passes every price criterion
  while intraday price formation runs at ~25 % of measured amplitude. Whether
  the rubric should carry a diurnal-amplitude criterion is an **owner call** —
  flagged here, not acted on.
* **Handoff Lever C is already done.** Its premise ("`data/raw/eia-930-hourly/
  {MISO,CISO} hourly.parquet` cover 2022 with 7 and 9 rows") is stale: both
  carry **8,760 rows for 2022 with 100 % column coverage** at this HEAD, landed
  by commit `5cd9374` ("eia-930: fill the CISO/MISO 2022 wide-hourly hole",
  2026-07-31). The miso-110 §4.3 window mismatch is closed; nothing to intake.

## 7. Governance

Years 2023–2025 only. **No LP solved, no bundle produced, no keeper changed, no
dashboard registration** (rule 15 applies to bundles; there is none — same
disposition as neiso-71 Lever A and neiso-73). The holdout spend freeze is
ACTIVE and NEISO's locked test is SPENT (2026-07-07); the 2022 row-count check
in §6 is a loader-resolvability census of an on-disk raw file, explicitly
permitted by rule 20 `[R-HOLDOUT]` as no-LP data validation. Matrix row
`pumped_storage_cycling_depth` added with NEISO → `G` (rule 28c).

**DO-NOT-REDO:** do not re-open a storage-side PS lever at NEISO — adder, RTE,
duration, or AS value — until the diurnal price-amplitude defect in §2 is
closed. The gap is not in the storage block.
