# FINDING — miso-150: the model-side universe fix WORKS EXACTLY AS NAMED, and the asymmetry it corrects was NEVER LOAD-BEARING — so miso-145's missing offer wall survives symmetrisation UNCHANGED TO FOUR DECIMAL PLACES

**Session** miso-150 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`), **UNCHANGED — nothing promoted, nothing armed, no
`ScenarioConfig` field added, NO LP SOLVE** · **Date** 2026-08-10 ·
**PREREG** `PREREG-miso150-model-side-universe-2026-08-10.md`, pushed at
`79f2e90c` (on main via PR #3844, blob-verified) **before this probe was
written** · **Branch fired: `BRANCH-NULL`** (PREREG §6).

---

## 1. The one-paragraph answer

miso-146 §8(a) named a blocker — the model-vs-DA-book supply-curve comparison
is measured on **asymmetric universes**, because MISO's offer book carries its
VRE at ≤ $0 while the model's wind and solar are LP decision variables absent
from the model-side curve — and named its fix: **add the model's own VRE to the
model's curve at its own offer price.** This session built that fix. It works
exactly as specified, and **the asymmetry it corrects turns out never to have
been load-bearing on anything.** Adding the model's entire VRE capability
(8.158 / 12.376 / 16.357 GW) at its own offers moves the LEVEL term by
**+$0.58 … +$2.16**; adding storage as well — the model's *complete* offerable
universe, an upper bound with nothing left to add — reaches **+$2.59** at most,
against miso-145's **+$18** reinstatement bar. And the statistics the charter
sent this session to re-test are **exactly invariant**: the missing offer wall
and the ladder slope move by **0.0000 GW and $0.0000/GW in all 24 cells**.
**miso-145's standing measurement is therefore now a measurement on a
symmetrised universe, and item 9's stated prerequisite is DISCHARGED.**

---

## 2. Footing — reproduce before extend (PREREG §2, HARD STOP)

Not merely inside tolerance: **exactly zero everywhere.**

| gate | bar | measured |
|---|---|---|
| **G-F0** miso-145's committed artifact reproduces in full | $0.01 / 0.05 GW / 0.0005 | **0 fields out of tolerance** |
| **G-F0b** this probe's SEGMENT path vs miso-145's DENSE path, 12 cells | same | worst **0.0** on capability, percentile AND wall |
| **G-F1** the six committed miso-142/143 window deficits | $0.01 | worst **0.0** |
| **G-F0c** the packed curve reader vs `_miso145_offer_conduct.price_at_pctl`, every cell | — | worst **0** |
| weight identity: `sidecar_price` denominator ≡ `_miso137.model_hourly`'s `W` | 1e-6 | **True** |

**G-F0b and G-F0c are what make §4 meaningful.** An invariance claim is worth
nothing if the machinery testing it is the thing that flattens the difference.
Both gates measure this probe's own construction against miso-145's, and both
read exactly zero — so a non-zero Δ in §4 could not have been hidden by the
harness. (G-F0c exists because the PREREG's own probe docstring **asserted**
this cross-check without coding it; that is precisely what TRAP-1 forbids, and
it was converted into a measured gate before any reading was taken.)

---

## 3. What was actually added, and at what price

The renewable offers are read from `run_year`'s own `fleet_only` exit — this
session's one additive core change (§9) — never re-derived outside the
orchestrator:

* **wind** `wind_mc` = **−$26.00/MWh** flat (the IRA PTC dispatch credit),
* **solar** `solar_mc` = **$0.00/MWh**,
* **storage** (U1S only) at the rule-9 tiebreaker **$0.001/MWh** — the *lowest*
  admissible placement, which maximises foot mass and is therefore the
  conservative direction for a quantity used as an upper bound.

Capability added, `JJA_h12_17` (load-weighted GW):

| year | wind | solar | **VRE total** | storage | model capability U0 → U1 → U1S |
|---|---|---|---|---|---|
| 2023 | 6.112 | 2.045 | **8.158** | 2.505 | 118.926 → 127.084 → 129.588 |
| 2024 | 7.984 | 4.391 | **12.376** | 2.558 | 116.593 → 128.969 → 131.527 |
| 2025 | 7.039 | 9.318 | **16.357** | 3.219 | 112.200 → 128.557 → 131.775 |

The 2025 VRE capability **16.357 GW** sits just above miso-146's committed
16.286 GW of model VRE *dispatch* in the same hours — the expected ordering
(TRAP-4: MISO's CF path is `_forecast_uncurtailed_cf`, so capability exceeds
delivery), and it biases the correction **upward**, i.e. against this session's
own prior.

---

## 4. G-1 / G-2 — the invariance, and why it is EXACT rather than approximate

**Result: worst |Δ ladder slope| = 0.0000 $/GW and worst |Δ wall| = 0.0000 GW
across ALL 24 U1 and U1S cells** (3 years × 2 windows × 2 brackets × 2 markets),
against bars of $0.05/GW and 0.05 GW.

The identity: mass priced at or below the hour's anchor shifts both `below` and
the ladder target `below + G·1000` by the same MW, so `price_at_cum` returns the
same segment; and the wall counts MW priced **strictly above** the anchor, which
VRE at −$26/$0 cannot enter.

**TRAP-2 — the one legitimate breach channel — is EMPTY.** Hours whose anchor
is at or below the model's own VRE offer: **0 of 552 (JJA) and 0 of 793 (W1), in
every year.** So the identity has no exception in these windows at all, which is
why the measurement is 0.0000 rather than merely small. The complement-subset
re-evaluation the PREREG required is consequently degenerate and is reported as
such, not dressed up as a second confirmation.

**Consequence, stated plainly:** the charter's standing measurement is not
"approximately robust" to the universe fix — it is **algebraically untouched by
it**. The universe objection to miso-145's wall was answerable without ever
running this probe; what the probe adds is the proof, and the sizing in §5.

---

## 5. G-3 — the LEVEL move, all 24 cells

ΔLEVEL vs U0 (arm-vs-U0 on the SAME keeper, per the miso-148 K0 caveat):

| year · window · bracket | RT ΔU1 | RT ΔU1S | DA ΔU1 | DA ΔU1S |
|---|---|---|---|---|
| 2023 W1 lo | +0.582 | +0.773 | +0.655 | +0.887 |
| 2023 W1 hi | +0.592 | +0.780 | +0.673 | +0.894 |
| 2023 JJA lo | +0.653 | +0.829 | +0.743 | +0.984 |
| 2023 JJA hi | +0.657 | +0.839 | +0.795 | +1.018 |
| 2024 W1 lo | +0.990 | +1.167 | +0.880 | +1.053 |
| 2024 W1 hi | +1.015 | +1.185 | +0.868 | +1.041 |
| 2024 JJA lo | +1.012 | +1.193 | +1.477 | +1.699 |
| 2024 JJA hi | +1.044 | +1.222 | +1.463 | +1.681 |
| 2025 W1 lo | +1.458 | +1.770 | +2.041 | +2.475 |
| 2025 W1 hi | +1.470 | +1.769 | +1.909 | +2.326 |
| 2025 JJA lo | **+1.533** | +1.820 | +2.156 | **+2.594** |
| 2025 JJA hi | +1.540 | +1.806 | +1.960 | +2.381 |

**Max ΔLEVEL(U1S) over every cell = +2.594** (2025 JJA `lo` DA), against the
pre-registered **BRANCH-MATERIAL bar of +$5**. Every cell carries the predicted
**positive** sign; the "wrong way" adverse case did not materialise.

**The prior held tightly.** PREREG §5 predicted **+$1.4, band [+0.9, +2.2]** for
2025 JJA RT `lo` from committed artifacts alone. Measured: **+1.533**, at a
measured V of 16.357 GW against the 16.286 GW the prior's centre used.

Absolute LEVEL, 2025 JJA `lo`: RT **−13.929 → −12.396** (U1) → **−12.109**
(U1S); DA **−9.662 → −7.506 → −7.068**. The window deficit is **−$33.05**
(anchor $41.628 vs actual $74.680). The universe fix closes **at most 8 %** of
it.

---

## 6. G-4 — the ceiling, solved on the measured curve

The zero-priced model-side mass **V\*** at which the LEVEL term would reach
miso-145's +$18 reinstatement bar, bisected on the real per-hour curves (not the
linearised prior):

| year | JJA RT | × nameplate | JJA DA | × nameplate |
|---|---|---|---|---|
| 2023 | 877.9 GW | **24.1×** | 289.4 GW | **8.0×** |
| 2024 | 748.2 GW | **18.3×** | 278.4 GW | **6.8×** |
| 2025 | **612.0 GW** | **12.3×** | **184.0 GW** | **3.7×** |

(W1 is the same story: 867.0 / 995.1 / 581.4 RT, 314.2 / 372.9 / 188.7 DA.)
Nameplate is miso-146's EIA-860 control: 36.380 / 40.794 / **49.747 GW**.

The PREREG predicted 641 GW (RT) / 157 GW (DA) for 2025 from the percentile
grid; the measured bisection returns 612.0 / 184.0 — same order, same verdict.
**Reaching the bar by universe correction alone would require between 3.7 and
24 times MISO's entire installed VRE fleet in zero-priced capability.** That is
the quantitative form of "not load-bearing".

---

## 7. G-5 — the residual asymmetry miso-146 required be stated, and a correction

**TRAP-5 FIRED, and resolved with a correction to how a committed number is
described.** The fleet carries **64** rows of `fuel_type == "import"`, not the
32 miso-146 quotes. Resolved: **32 `refimp` tranches carrying exactly
17,200.0 MW** — reconciling to miso-146's committed 17,200 MW to the last
digit — plus **32 `refexp` rows carrying 0.0 MW**, which the `seg_mw > 0` filter
(miso-145's own, applied identically here) drops from every curve. **The MW
figure is right; "32 import tranches" describes a fleet that carries 64 rows
under that fuel type.** No result depends on the count, and G-5 is not voided.

miso-146's characterisation is **confirmed**: the import tranches are priced in
the **body** of the curve, not at its foot — JJA h12–17 mean offer **$172.61**
(min $21.82, max $433.12), against an anchor of $41.63.

**U4 (U1 minus the import tranches) is correctly NOT invariant** — removing
17.2 GW from the body is not a foot addition:

| year (JJA lo) | wall U1 → U4 | slope+1GW U1 → U4 | ΔLEVEL RT | ΔLEVEL DA |
|---|---|---|---|---|
| 2023 | 6.4322 → 5.7613 GW | $0.7004 → $0.7537 | +0.634 | +0.712 |
| 2024 | 8.0215 → 7.5546 GW | $1.8809 → $1.9152 | +0.966 | +0.821 |
| 2025 | 8.3024 → 7.3206 GW | $0.7197 → $0.8504 | +2.236 | +3.293 |

So the import asymmetry is **worth more than the VRE asymmetry in 2025**
(+3.293 DA) and still nowhere near the bar. It moves the wall by 0.45–1.02 GW —
a **9–12 %** effect on a wall of 6.4–8.3 GW, which bounds how much of that wall
could be an import-representation artifact. **Not adjudicated here**, and no
lever is proposed from it.

---

## 8. The standing measurement, restated on the current keeper

The charter's standing pair, re-measured (`JJA_h12_17`, `lo`, universe **U1** —
the symmetrised model side). Both real-side legs are identical under
U0/U1/U1S/U4 by construction (the real segment set is untouched), so they are
reported once; they move with the **keeper**, because the model's anchor
positions them.

| year · market | model wall | **real wall** | model $/GW | **real $/GW** |
|---|---|---|---|---|
| 2023 RT | 6.4322 GW | 0.8261 GW | $0.7004 | **$51.69** |
| 2024 RT | 8.0215 GW | −0.0078 GW | $1.8809 | **$56.06** |
| 2025 RT | **8.3024 GW** | **0.7081 GW** | **$0.7197** | **$73.4591** |
| 2025 DA | 8.3024 GW | 1.0723 GW | $0.7197 | $17.8987 |

The charter's committed **$73.46/GW** reproduces as **$73.4591** on a *different
keeper* — the residual is the demand weighting, which is keeper-dependent while
the real ladder itself is anchored on the actual price.

**On the current keeper the measurement is STRONGER than the charter's, not
weaker.** The wall is **8.30 GW** (charter: 5.698–6.038 on the superseded
miso-132 keeper) and the slope ratio is **102×** ($73.46 vs $0.72) rather than
49× ($73.46 vs $1.496). This is the miso-148 keeper change, not drift — and it
is exactly why the PREREG forbade quoting any arm-vs-committed-keeper delta.

---

## 9. The U2 locator — banded, and never load-bearing (as declared)

U2 truncates the model's VRE per hour to the intermittent MW miso-146's screen
identifies in the book. It sits monotonically inside U0 ≤ U2 ≤ U1 in every cell,
and the threshold sweep spans nearly the whole bracket (thr 0.70 ≈ U0,
thr 0.30 ≈ U1) — the load-bearing threshold miso-146's P-1 found, reproduced.
**Because the entire U0→U1 bracket is ≤ +$2.6, no verdict here depends on where
in it U2 sits**, exactly as the PREREG committed in advance.

**One clean reconciliation worth recording:** at miso-146's own primary
threshold (0.50), the book's identified intermittent capability reads
**7.78 GW** for RT-2025 against miso-146's committed **7.755 GW**.

---

## 10. Verdicts, gates and traps, closed out

| item | verdict |
|---|---|
| **G-F0 / G-F0b / G-F1 / G-F0c** footing | **PASS**, all exactly 0 |
| **G-1** ladder-slope invariance | **PASS** — 0.0000, 24/24 cells |
| **G-2** the missing offer wall | **PASS** — 0.0000 GW, 24/24 cells |
| **G-3** the LEVEL move | measured; max +2.594 vs the +$5 branch bar |
| **G-4** the ceiling | measured; 3.7×–24.1× MISO's VRE nameplate |
| **G-5** the import asymmetry | measured and stated; TRAP-5 fired and resolved |
| **TRAP-1** machinery verified, not assumed | G-F0b + G-F0c, both 0 |
| **TRAP-2** the one breach channel | **0 hours**, every cell |
| **TRAP-3** units vs denominators | GW↔GW, $/MWh↔$/MWh, $/GW↔$/GW; no share can exceed 1 |
| **TRAP-4** potential ≠ delivery | stated; biases the correction upward |
| **TRAP-5** a class silently reading zero | fired on the row count; MW reconciled exactly |
| **TRAP-6** the keeper pointer | footing at `miso132_ccmin_B`, measurement at `miso148_basis_B`, saved/restored |
| **TRAP-7** the CWD cache | `MISO150_CACHE` → `/tmp` |
| **TRAP-8** reading the level off the real curve's own percentile | never done; model percentile only |

**BRANCH-NULL** (PREREG §6): G-1 and G-2 hold and max ΔLEVEL(U1S) < +$5.

---

## 11. What this licenses, and what it does not

**Licensed.** miso-145's refutation of the offer-LEVEL hypothesis **stands on a
symmetrised universe**. The missing offer wall (**8.30 GW** on the current
keeper, against a book carrying **0.71 GW**) and the slope contrast
(**$73.46 vs $0.72 per GW**) are **universe-robust measurements**, provably
invariant to the largest model-side foot correction that exists. **Item 8
CLOSES.** The blocker miso-146 named is dissolved — by showing it was never
load-bearing, not by removing it.

**NOT licensed.** No mechanism, no arm, no `ScenarioConfig` field, no keeper
change. **Item 9 (a MISO `measured_offer_surface`, position-conditioned,
replacing or subsuming `gas_offer_margin` per rule 19) REMAINS AN OWNER
DECISION and is NOT chartered by this session** — what is discharged is its
stated *prerequisite*, nothing more.

**Named and NOT opened.** (a) The **import-representation** share of the wall,
bounded here at 9–12 % (§7) — it needs its own charter and it is not a VRE
question. (b) MISO's un-re-tuned outage extract and the 2025 EIA-860 vintage
under-carry, both explicitly out of scope (rule 25) and neither of which this
object touches.

---

## 12. Disclosures

* **One additive core change**, declared in PREREG §10 before it was made:
  `scripts/run_calibration.py`'s `fleet_only` exit returns **`wind_mc` /
  `solar_mc`** (+9 lines, 5695 → 5704). No solve path touched, no existing key
  changed, no behaviour changed. Rule 27 `[R-PUSH]`: edited locally, pushed as
  exact on-disk bytes, **pushed blob verified against the fetched remote ref —
  5704 lines both sides, identical sha256**.
* **Two defects in this session's own probe, found and fixed rather than worked
  around**: (i) the docstring asserted the G-F0c cross-check without coding it —
  now a measured gate; (ii) the U2 locator applied a per-window scale to
  full-year arrays, which cost a complete re-run and is now covered by a
  synthetic-fleet shape self-test.
* **A load-time warning that is inert here and is not glossed:**
  `capacity-deliverability clean partition for MISO absent — falling back to
  static PY2025-26 summer CIL/CEL caps`. It feeds `interface_groups`, an **LP
  transmission constraint** consumed only by the solve; this probe takes no
  solve, the keeper carries `capacity_deliverability_limits: None`, and the
  footing's **exact-zero** reproduction of miso-145 is the empirical proof the
  fleet reconstruction does not depend on it.
* **The offer corpus is gitignored and was re-fetched for this session**:
  552/552 files, **429.6 MB**, matching the README's landed span exactly
  (JJA 2023–2025, both markets), then re-curated to the `energy-offers` clean
  datatype.
* **No run was produced**, so there is nothing to register on the backcast
  dashboard (rule 15; the miso-149 Phase-0 precedent). **No mechanism was
  tested**, so no matrix cell verdict moves (rule 28(b)); the §5.4 MISO lever
  queue is stamped in this session.
* Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only. MISO holds no marker. No solve, so
  no year is spent in any sense.
* The charter's kill gates (C3a/C3b/C8/C3c/May-2025) are **inert**: no solve was
  taken, so no scored criterion can move. The keeper's determination is
  unchanged at **NOT-YET**, fail set **{C3a, C3b}**, re-verified from committed
  artifacts at session open.

**Artifacts.** `results/calibration/_miso150_universe.json`; probe
`scripts/probes/_miso150_universe.py`; PREREG
`results/calibration/PREREG-miso150-model-side-universe-2026-08-10.md`.
