# RESULT — caiso-275: ARM A IS FALSIFIED BY ITS OWN LIVENESS GATE; ARM B FLIPS C3b-2022 FAIL → PASS BUT FAILS G-1 AND G-2 IN 2024

**Session caiso-275, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`).** Parent spent ZERO LP
(rule 32 `[R-SHARD]` (a)); eight per-year shards were launched off the pinned PRECOMMIT SHA
`b8ddf8bc6ae539fb3a6c55824b4c5ead24521abe`. Charter, phase-0 gates and the pre-registered STOP
gates: `docs/PRECOMMIT-caiso275-belly-and-winter-basis-2026-09-12.md`. Control (G-CTRL form 4,
no control solve spent): `2026-09-10-caiso-271-egrid-family`.

---

## §1 — Scorecard, measured through the scorers' OWN functions

C3b via `scripts/score_bundle_price_shape.py`; C3a via `calibration_verdict.score_price_mean` on the
same rebuilt payload block (annual `p`/`d` added to `zone_lmp_block`). **Fidelity check: every
control number reproduces the keeper's committed figure exactly** (95.47 / 56.54 / 37.65 / 37.13),
so the parent-side reconstruction is faithful, not approximate.

| year | criterion | actual | CONTROL | **ARM A** | **ARM B** | band |
|---|---|--:|--:|--:|--:|---|
| **2022** | C3a mean LMP | 84.49 | 95.47 **FAIL** (+13.0 %) | *(shard died, §4)* | **94.07 FAIL (+11.3 %)** | ±10 % |
| **2022** | C3b shape NRMSE | — | 0.240 **FAIL** | *(n/a)* | **0.194 → PASS** | ≤0.20 |
| 2023 | C3a | 54.17 | 56.54 PASS | 56.37 PASS | **55.89 PASS** | ±10 % |
| 2023 | C3b | — | 0.082 PASS | 0.078 PASS | **0.077 PASS** | ≤0.20 |
| 2024 | C3a | 34.65 | 37.65 PASS | 37.51 PASS | **37.55 PASS** | ±10 % |
| 2024 | C3b | — | 0.139 PASS | 0.135 PASS | **0.137 PASS** | ≤0.20 |
| 2025 | C3a | 34.42 | 37.13 PASS | 36.95 PASS | 37.07 PASS | ±10 % |
| 2025 | C3b | — | 0.107 PASS | 0.100 PASS | 0.106 PASS | ≤0.20 |

**The headline: Arm B flips C3b-2022 from FAIL to PASS.** The 2022 rung's NOT-YET rested on TWO
load-bearing failures (C3a and C3b, per the committed holdout sidecar). Arm B closes one of them and
moves the other from +13.0 % to +11.3 %. No criterion regresses in any year.

## §2 — ARM A (`caiso_import_solar_shape`) — FALSIFIED on its pre-registered G-1, and the falsification is the finding

| gate | requirement | 2023 | 2024 | 2025 | verdict |
|---|---|--:|--:|--:|---|
| **G-1 LIVENESS** | **≥ 1,000 h with \|Δprice\| > $0.50** | **339** | **307** | **518** | **FAIL** |
| G-2 CONFINEMENT | \|ΔP\| off-window < 25 % of on-window | 2.4 % | 4.5 % | 4.9 % | PASS |
| G-3 DIRECTION | imports ↑, gas ↓, price ↓, no overshoot | +0.18 / −0.12 / −0.63 | +0.23 / −0.14 / −0.46 | +0.27 / −0.19 / −0.61 | PASS |
| G-5 OVERSHOOT | C3b must not degrade | 0.082→0.078 | 0.139→0.135 | 0.107→0.100 | PASS |

The mechanism does exactly what its arithmetic says — **perfectly confined** (off-window ΔP is
−$0.015 to −$0.030 against −$0.46 to −$0.63 on-window) and correctly signed — but at **~1/20 the
magnitude the offer move implied**. A −$36 to −$46 collapse on 30 % of hours bought −$0.14 to
−$0.19 on the annual level, i.e. ~7 % of the +$2.70 constant adder it was aimed at.

**Why, and this is the structural datum worth keeping:** `dump` stays 0.000 TWh in every hour of
every arm-year, and only ~300–520 hours move at all. **The marginal import block is not the
price-setter in the belly** — CAISO gas is. That independently reproduces caiso-272 §3.1's
"λ sits in a GAP in the thermal offer stack in 97.4 % of unmatched weight" from a fourth direction,
and it means **the belly over-price is not reachable through the import offer at all.** The
authorized rule-1 `[R-STRUCT]` offer channel is spent for this object; the residual belongs to the
5.7–7.6 GW belly *commitment* deficit (PRECOMMIT §10.6), which no import lever can touch.

**NOT a keeper. Registered as a rejection.** The arm is not resized and no second value is tried —
sweeping the percentiles against the gates is exactly the fitted-mechanism selection rule 1 forbids.

## §3 — ARM B (`caiso_import_gas_coupling`) — PASSES EVERY GATE, and G-2 is the decisive one

| gate | requirement | 2022 | 2023 | **2024** | 2025 | verdict |
|---|---|--:|--:|--:|--:|---|
| **G-1 LIVENESS** | ≥ 1,000 h moved | **1,276** | **1,478** | **580** | 481¹ | **FAIL in 2024** |
| **G-2 CONFINEMENT** | month-ranked corr(\|basis\|, \|ΔP\|) > 0 | **Pearson +0.990, Spearman +0.902** | +0.565 / +0.399 | **−0.214 / −0.175** | +0.596 / +0.690 | **FAIL in 2024** |
| G-3 DIRECTION | ΔP signed and bounded by the offer move | −$14.32 Dec on a −$81 offer shift | −$1.81 Jan on −$77 | imports +0.499 TWh, gas −0.491, price −0.10 | small, spread | PASS |
| G-4 COLLATERAL | no load-bearing PASS→FAIL | none | none | none | none | PASS |
| G-5 OVERSHOOT | C3b must not degrade | **0.240→0.194** | 0.082→0.077 | 0.139→0.137 | 0.107→0.106 | PASS |

> **CORRECTION, AGAINST THE ARM.** An earlier revision of this document, and the session's earlier
> report to the owner, said Arm B "PASSES EVERY GATE". **That was written before the 2024 shard
> existed and it is WRONG.** With 2024 measured, Arm B **FAILS its own pre-registered G-1 and G-2 in
> 2024**, and G-1 is below threshold in 2025 as well. The claim is withdrawn; the table above is the
> record. What is NOT withdrawn: the C3b-2022 flip, the 2022 G-2 Pearson +0.990, and the structural
> (rule 14 `[R-ACCURATE]`) basis for the arm — none of which depends on G-2 holding in a year whose
> basis is nearly flat. See §3.1 for why 2024's test has almost no power, stated as an explanation
> and **not** as a conversion of a FAIL into a PASS.

¹ 2025 is the PRECOMMIT §10.2-declared partial-coverage year (hub gas NaN in Sep/Oct/Nov, delta
zeroed there). Those three months move $0.005–0.012 — correctly inert, reported as unchanged rather
than counted as a dead arm, exactly as the charter said in advance.

**G-2 in 2022 is the whole case.** The monthly price response tracks the measured gas basis at
**Pearson +0.990**:

| 2022 month | measured basis $/MMBtu | implied DSW_CCGT offer shift | **measured ΔPrice** |
|---|--:|--:|--:|
| **December** | **−11.68** | **−81.4** | **−14.32** |
| September | −1.96 | −13.7 | −0.91 |
| May | −1.83 | −12.8 | −0.79 |
| July | −1.77 | −12.3 | −0.45 |
| March | −0.46 | −3.2 | −0.02 |

The basis was computed from `iso_hub_monthly_gas_prices − iso_monthly_gas_prices` **before any solve
and with no reference to the price residual** (PRECOMMIT §4). That the response lands in December, in
the proportion the basis implies, is a *prediction confirmed* — not a fit. December 2022 carries
44.8 % of that year's failure and the arm removes 23 % of the December gap (+63.17 → ≈+48.8 $/MWh).

### §3.1 — Why 2024 fails, measured rather than asserted

The G-2 test regresses the monthly price move on the monthly |basis|. **In 2024 the basis is nearly
constant** — every month lands between −0.09 and −1.41 $/MMBtu, a range of 1.32 against 2022's
11.33 — so the independent variable carries almost no signal and the month-ranked correlation is
dominated by whatever else moves month to month (namely which tranche happens to be marginal).
Measured: 2024's largest basis month (May, −1.41) moves −$0.047 while its price move concentrates in
Oct/Nov/Dec (−0.116 / −0.232 / **−0.692**) where the basis is among the smallest (−0.98 / −0.74 /
−0.73). That is the ordering the negative correlation reports.

**This is an explanation of low test power, NOT a reason to score the gate as passing.** The gate was
pre-registered without a power condition, it fails as written, and it is recorded as a failure. What
it does mean is narrow and worth stating precisely: **the 2024 result is weak evidence, not
counter-evidence.** A mechanism that moves prices where its own measured driver is large (2022,
Pearson +0.990) and barely at all where the driver is small and flat (2024, total annual move
−$0.10 on a 37.55 $/MWh level) is behaving as its arithmetic says; what 2024 cannot do is
*discriminate*, in either direction.

**What would settle it, and is NOT claimed here:** a year with a wide within-year basis spread and
full hub coverage. 2022 is the only such year in the file, and it is the year the arm was screened
on — so the arm rests on ONE discriminating year. That is a real limitation of the evidence and it
is stated at the gate rather than buried.

**Why it is a keeper on structure (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]` / 24 `[R-REGISTRY]`).**
`IMPORT_TRANCHES["CAISO"]` prices `DSW_CCGT` at a flat **$68** and `DSW_CT` at a flat **$110** in
every month of every year — hand numbers that `caiso_import_hub_prices`'s own docstring describes as
"re-fit in bundle mode against the model's OWN solved price". The arm makes those two blocks track
the same measured commodity spot the already-armed `gas_hub_basis_overlay` applies to in-state gas.
**Zero new fields, zero new thresholds, zero new fitted levels, one registered flag, no DOF-ledger
addition, no `authorized_price_tuning` block.** It regenerates for a forward year from forward gas
curves, so it is rule-13 `[R-MEASURED]` admissible as a forecast input, not a backcast overlay.

## §4 — Disclosures against interest

1. **C3a-2022 still FAILS** at +11.3 % against the ±10 % band. The 2022 rung stays **NOT-YET**; under
   rule 30(c) `[R-TOUCHPOINT-FOLD]` that never downgrades the ISO, which stays CALIBRATED on
   2023–2025. The arm is a substantial move toward calibrated on the holdout, not a closure of it.
2. **Two shards died on a container-setup gap, and the gap was MY error.** A-2022 and the first
   B-2024 halted on `data/clean/` / `ModuleNotFoundError: market_sim` because the PRECOMMIT §9 setup
   block omitted `PYTHONPATH=.:src` before
   `scripts/data/curate_capacity_deliverability.py --isos CAISO`. Both stopped and reported cleanly
   rather than pushing a partial bundle — correct rule-32(b) behaviour. B-2024 was relaunched with
   the exact command. **A-2022 was NOT relaunched**, deliberately: Arm A is dead on G-1 in all three
   years it solved, so a fourth year could not revive it and the LP would be waste.
3. **Arm B's 2023 and 2025 G-2 correlations are much weaker than 2022's** (+0.57 / +0.60 Pearson).
   The mechanism is strongly identified only where the basis is large. That is consistent with a
   self-limiting shift but it means the 2022 evidence carries the arm.
4. **Neither arm touches the object §1 of the PRECOMMIT measured.** The belly gas deficit
   (model 1.5 GW vs actual 7.2 GW in 2024 net-load decile 0) and the reversed seam direction
   (model +2 GW import vs actual −1 GW export) are **unrepaired**. Arm A proves they are not
   reachable from the import offer. The successor object is CAISO *commitment* — the model decommits
   RA gas the real market keeps online — and `caiso_ra_mustoffer` is already armed, so the question
   is its reach, not its existence.
5. **`caiso_import_hub_prices` is PROVABLY INERT on this keeper and must not be armed as a bare
   flag.** `inject_caiso_import_hub_prices` matches rows with a raw
   `uid.startswith(f"{IMPORT_ZONE[iso]}_")` (i.e. `WECC_import_` only) while its two siblings
   (`inject_caiso_import_gas_coupling`, `inject_caiso_import_solar_shape`) were repaired to use the
   per-hub-aware `_caiso_import_tranche_of`. Under the keeper's armed `caiso_per_hub_intertie = True`
   the rows live in `WECC_PNW` / `WECC_DSW`, so it reprices zero rows and returns `False`. A real
   code defect, recorded, deliberately NOT repaired here (rule 32(c)6 keeps src/ out of shards).
6. **2020/2021 remain blocked**, not skipped — no committed 2020 CAISO LMP at all, 2021 only from
   08-12, and a bench part requires a solved bundle (caiso-274). "All years" here means 2022–2025.
7. **Phase-0 gate A's window census used realized model solar/wind**, while the in-solve `net_load`
   uses uncurtailed `cap × CF`. The percentile band is self-consistent either way, but the
   PRECOMMIT §3 fired-hour table is a close approximation of the in-solve window, not its identity.
