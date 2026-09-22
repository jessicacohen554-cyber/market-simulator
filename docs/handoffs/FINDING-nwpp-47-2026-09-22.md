# FINDING nwpp-47 — the plant-level attribution intake (FINDING-nwpp-45 §8, framing 1)

**Owner ruling (this session, on FINDING-nwpp-45 §8):** framing 1. Resolve the GRID / generation-only-BA
attribution from plant-level evidence and rebuild the subtrahend. Zero LP spent for this finding.
Reproduce with `scripts/probes/_nwpp47_attribution.py` (sections A–E). Every number below comes from it.

## 0. Result in one line

**The subtraction is mostly right, one leg of it is a double-count, and most of the gap is not in the
subtraction at all.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Scored system gap (model gen − `classFull`), keeper | −9.645 | −12.144 | −9.107 |
| (i) **GRID→PNM leg = GRID's wind, which the model supply also carries** → double-counted | **2.074** | **2.171** | **2.002** |
| (ii) GRID→SRP/WALC = Desert-SW gas the fleet does not own → correctly removed | 5.032 | 7.615 | 8.129 |
| Gap left after fixing (i) | −7.57 | −9.97 | −7.11 |

The part (i) doesn't close sits in the **930 net generation of the footprint's own BAs**, not in GRID
(§3). This lane does not close it; §5 returns it to the owner.

## 1. NWPP-45 §5's "refutation" rested on eGRID's host BA, and GRID's book says otherwise

NWPP-45 §4 counted 12.856 TWh of GRID generation "not attributable to a footprint plant" because
eGRID hosts only Hermiston (55328) in GRID. GRID's hourly book against CEMS says otherwise:

| GRID 2023 (TWh) | book | hourly match |
|---|---|---|
| coal | 4.143 | **Centralia (3845), r = 0.9998**. eGRID hosts it in **BPAT**, and it is a fleet plant |
| gas → BPAT leg | 5.145 | Hermiston 55328 (3.80) + Hermiston 54761 (0.71), r = 0.974 |
| gas → SRP + WALC legs | 5.032 | Santan, Mesquite, Griffith (AZ); r = 0.749 (2024: 0.931, 2025: 0.931) |
| wind → PNM leg | 2.073 | **PNM leg ≡ GRID `NG: WND`, r = 1.00000, max \|Δ\| 1 MW** (2024: 1 MW, 2025: 2 MW) |

So GRID's out-of-footprint generation is the SW legs (7.1 / 9.8 / 10.1 TWh), not 12.856. §5's
"literal principle lowers demand 5.741 TWh" is withdrawn: its subtrahend counted Centralia and
Hermiston as external.

## 2. The double-count (the fixable part)

- The PNM leg is GRID's wind, hour for hour, in all three years.
- NWPP's wind supply is the pool frame's `NG: WND`, **GRID included**, and so is the C1 wind actual:
  model 30.407 vs pool 30.410 TWh (2023).
- The served schedule removes the PNM export while the supply still generates that wind. The same
  energy leaves the requirement twice, so the thermal fleet is under-asked by **2.074 / 2.171 / 2.002
  TWh** (`load_demand`, zero LP).

**Fix:** `ScenarioConfig.nwpp_grid_carried_wind_served` (default off) serves the export leg of the wind
the supply carries.
- It has zero free parameters: one measured series, already in the pool frame.
- The SRP/WALC gas legs stay removed.
- It is equivalent, for thermal, to dropping GRID's wind from both the supply and the benchmark.
  Serving the leg was chosen because it leaves the benchmark and the wind row untouched.
- Rule 14 applies: this is a boundary reconciliation to the pool's own renewable definition, not a
  level rescale.

## 3. Where the rest of the gap lives: 930 books less footprint fossil output than CEMS measures

930 fossil net generation per footprint BA against the CEMS gross of the plants eGRID hosts there (§B):

| gas, 930 ÷ CEMS gross | 2023 | 2024 | 2025 |
|---|---|---|---|
| **control BAs** (AVA, AVRN, IPCO, NEVP) | 0.95–1.01 | 0.96–1.03 | 0.98–1.03 |
| BPAT | 0.66 | 0.60 | 0.65 |
| PGE | **0.56** | **0.53** | **0.58** |
| PACW | **0.00** | **0.00** | 0.45 |
| PSEI | 0.85 | 0.74 | 0.56 |
| PACE | 0.94 | 0.73 | 0.76 |
| **footprint total** (incl. GRID's SW gas) | 0.902 | 0.880 | 0.919 |

The hosted-plant ratio fails in BPAT, PGE, PACW, PSEI and PACE and holds in every control BA. The
missing output is **not booked in CAISO or BANC**. Their gas books are explained by their own plants
(residual +0.58 / +0.08 TWh), and that residual doesn't track footprint plants (r = 0.11 / 0.21) (§C).
So it is not a pseudo-tie out of the footprint that should be served as an export. On the evidence,
930 simply under-books these plants.

**Rough size, not a result:** assume 0.97 net/gross for gas and 0.92 for coal. Then 2023 under-booking
is ≈10 TWh gas + ≈3 TWh coal, the same order as the −7.6 TWh left after §2. The two measure different
bases (CEMS vs 923 net of BTM), so I'm not claiming they reconcile exactly.

## 4. Metered load plus external legs does not fix it either (§D)

Each footprint BA's external legs agree with the counterparty's own report to ≤ 0.04 TWh, except
PACE–WACM (1.2) and 2024 LDWP (±0.9, netting). But demand built from metered load plus mirror-verified
external legs gives:

| 2023, TWh | requirement |
|---|---|
| current (Σ 930 NG − SW legs) | 270.5 |
| Σ 930 load + external legs (mirror-first) − SW legs | ≈ 290.8 |
| fleet actual, 923 grid basis, less GRID's NM wind | ≈ 278.1 |

It overshoots by about 12 TWh, and 10.2 / 7.8 / 2.5 TWh of the external position is on Canadian
legs (BCHA, AESO) that no counterparty mirrors. **930 can't close this pool's energy balance to ±10 TWh
from either side**, so no pure-930 construction is offered.

## 5. What this leaves for the owner

- **Closed by this lane (subject to the solve):** the 2.0–2.2 TWh/yr double-count (§2).
- **Not closable under framing 1:** the ~7–10 TWh 930 under-book of in-footprint fossil plants (§3).
  Correcting it means putting measured plant generation into the requirement, which is FINDING-nwpp-45
  §8 **framing 2**. That needs a separate ruling. It stays open and is reported, not absorbed.
- **Refuted, zero LP:** the §5 "literal principle" subtrahend (§1). The pure-930 load plus interchange
  construction (§4).

## 6. Carried, unchanged

- C4 still FAILS; its live root cause is still intra-day price formation (NWPP-46).
- C2's PASS tests no family volume.
- Energy balance −10.02 TWh in 2025 is the same object as §3.
- NWPP-40/41/42 attestation corrections are still owed.
- Also carried: Chief Joseph pond dual; C5a CO2 is reported only; Jim Bridger absent from
  `thermal_tranches_NWPP.csv`; the 2025 930 hydro −44,969 MW hour.
- GRID's 0.38–0.42 TWh of solar: its leg is ambiguous (unstable split between the BPAT and SW legs).
  It's reported and not armed.
- **Data note:** EIA renamed the wind/solar columns in the 2024-H2+ national BALANCE files ("with /
  without Integrated Battery Storage"). Anything reading `… from Wind (Adjusted)` there sees half a
  year. The committed per-BA extracts are correct.
