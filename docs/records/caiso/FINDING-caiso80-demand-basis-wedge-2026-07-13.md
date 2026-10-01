# FINDING — caiso-80 demand-basis adjudication: the CISO EIA-930 **Demand** cell carries the same fabricated block as the NG cell (Demand = NetGen + TI arithmetic), plus a grid-basis accounting wedge — the model's demand input makes its fleet serve **+10.4 / +11.6 / +18.5 TWh/yr (2023/24/25)** that the real grid fleet demonstrably did not serve; this, not the offer curves, is the C3a/C1 body root cause (2026-07-13)

**Lane B step 2 of the caiso-80 plan**
(`docs/handoffs/caiso-79-next-run-plan-2026-07-12.md` §4.2 — the caiso-72
STEP-0 candidate-4 demand-basis conflict, now adjudicated with full-year
data). Companion and demand-side completion of the owner-signed bench rework
(`FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md` §5/§6): that rework
removed the corrupt 930 NG cell from the **scored actuals**; this FINDING
shows the same corruption sits in the **model's demand input** (`load_demand`
→ `_load_caiso_hourly_demand` reads the raw 930 `Demand` cell), where it
still drives every CAISO solve. All numbers reproduce from committed repo
data (EIA-930 `CISO hourly` extract, CAMPD `CA_<year>` parquet, the committed
CEMS-anchored bench parts, `CAISO_tac_load_hourly_*`, CAISO DAM LMP files,
`caiso_citygate_daily.csv`) — diagnostic scripts only, **no LP was solved**.

## 1. The three-way comparison (entry question)

The plan's framing was "930 Demand vs supply-implied vs CAISO TAC actuals
disagree ~1.5 GW in the afternoon ramp." Measured on full years:

- **930 Demand vs TAC actual load** (`CA ISO-TAC`, full-year files exist for
  2024/25; the 2023 file covers January only): they **agree** — −0.83 / −0.80
  TWh annually (−0.09 GW mean), residual hod differences form a ±1.5 GW
  clock-shaped dipole (the known +1 h Demand-clock convention,
  `caiso_demand_clock_realign`). TAC is **not an independent check**: CAISO's
  published "actual load" is computed from the same supply-side telemetry
  books that feed its EIA-930 submission (Demand = NetGen + TI is an
  arithmetic identity of those books, §3).
- **930 Demand vs honest supply-implied load** — the real conflict, and it is
  ~10× the anticipated size. On the **grid-delivered basis** (the exact basis
  of the model's fleet representation and of the honest bench actuals the run
  is scored on: CEMS bench-gas grid + 923 cogen grid block + geo/biomass
  fold-in + all other 930 cells + measured TI):

  | year | 930 Demand (TWh) | honest supply + imports | **wedge** | wedge mean GW |
  |---|---|---|---|---|
  | 2023 | 218.1 | 207.7 | **+10.4** | 1.20 |
  | 2024 | 224.0 | 212.4 | **+11.6** | 1.37 |
  | 2025 | 223.8 | 205.3 | **+18.5** | 2.13 |

  (On TAC load instead of 930 Demand: +12.4 / +19.3 TWh for 2024/25 — same
  wedge, both load series carry it.)

## 2. The wedge's shape identifies it

Hour-of-day mean profile of the wedge (GW; grid basis, 930 Demand side):

```
hod      0    2    4    6    8   10   12   14   16   17   18   20   22
2023   2.2  1.7  0.7  0.3  1.7  2.4  1.8  0.2 -1.6 -1.4 -0.0  2.1  2.9
2024   1.5  1.3  0.8  1.4  3.9  3.7  3.6  1.7 -1.8 -1.9 -1.4  0.7  0.9
2025   1.3  1.4  1.4  1.8  4.4  5.4  6.0  4.1 -0.1 -1.1 -1.1  0.5  0.3
```

A growing **daylight-solar-shaped hump** (h7–14, peaking 3.9 → 6.0 GW) over a
~0.5–1.5 GW base, going **negative in the h16–18 shoulder** (honest supply
*exceeds* reported load there — reality's evening gas commitment). The
daylight hump grows exactly like the solar build-out — the same signature the
930-NG FINDING §3 used to identify the NG-cell corruption.

## 3. Net-generation-basis decomposition — the phantom block is in the Demand cell by arithmetic

Rebuilding honest supply on the **net-gen basis** (cogens at full 923 net gen
so the CHP host-load accounting drops out; CEMS gas at gross × 0.97 station
service) splits the wedge into 930's own identity imbalance
(`Demand − NetGen + TI`) and the NG-cell unexplained block:

| year | net-gen wedge | = identity gap | + NG-cell unexplained |
|---|---|---|---|
| 2023 | +4.1 | +5.3 | −0.8 |
| 2024 | +5.5 | +1.2 | **+4.4** |
| 2025 | +12.4 | +1.8 | **+10.8** |

The monthly NG-cell unexplained series flips positive at **2024-05** (2024:
Feb −0.06, Mar −0.06 → Jul +0.88, Aug +0.71; 2025: +0.5..+1.4 every month) —
the exact onset the 930-NG FINDING measured. Because the identity gap stays
small (+1–2 TWh in 2024/25), the fabricated NG energy flows **arithmetically
into the Demand cell**: CAISO's books added the phantom block to both sides.
The remaining grid-vs-netgen difference (~6–7 TWh/yr flat) is the CHP
host-load accounting: the 930 books carry the cogens at full net gen (host
consumption included), while the model's CHP classes and the scored
`classFull` are grid-delivery-netted — whichever side of the meter that
energy truly sits on, **the transmission-level grid fleet the model
represents did not serve it**. (The 2023 split between host accounting and
pure identity imbalance is not identifiable from 930 alone; the 2024/25
*growth* is firmly the demonstrated NG-cell defect.)

## 4. What the model does with the phantom demand (B1 + B3 evidence)

The caiso-78 payload's energy balance closes against the wedge almost term
for term (2024: model gas +6.8 over honest actual, imports +6.9 over the 930
TI, solar +3.2 — less curtailment — hydro +1.0 ≈ the 11.6 TWh wedge + storage
losses; same structure in 2023/25):

- **B1 (belly probe refreshed on caiso-78 — supersedes the caiso-65-vintage
  numbers):** the old "belly under-commitment" story is DEAD. Model CC
  (REGULAR+CHP, bench same-fleet) vs CAMPD by window, model−actual GW:
  overnight h0–6 **+0.58/+0.83/+1.51**, morning h6–9 **+0.70/+1.66/+2.54**,
  belly h9–16 +0.08/+0.09/+0.85, shoulder h16–18 +0.16/**−0.76/−1.00**,
  evening h18–22 +0.56/+1.02/+1.13 (2023/24/25). The model over-commits CC
  around the clock — worst at the morning ramp, growing with the wedge — and
  actually **under-runs the h16–18 shoulder**, the mirror of the wedge's
  negative evening lobe. (Same-fleet annual CC excess +3.5/+5.5/+10.3 TWh.)
- **B3 (fuel-basis level check — implied HR = monthly mean λ / citygate
  gas, model vs measured DAM TH_NP15/TH_SP15):** in 2023's genuinely tight
  months the model's price level is **correct** — Feb 0.97×, Apr 1.01×, Jul
  1.05×, Aug 0.98× — while soft/high-solar months carry the whole overprice
  (May 2.25×, Jun 1.74×, Sep 1.41×, Dec 1.47×). From the 2024-05 onset even
  summer months run 1.07–1.35×, and 2025 is broad (1.2–2.0×). The C3a body
  overprice is therefore **margin composition, not offer level**: phantom
  daytime demand (plus the flat base) keeps model gas marginal through hours
  and months where reality's margin collapses to renewables/curtailment/
  imports. A level re-tune (lane B step 4) is contraindicated by the
  tight-month evidence — it would break the months the model already prices
  correctly (rule 1).
- The wedge's year-gradient (+10.4/+11.6/+18.5) matches the C3a overprice
  gradient (+26.9/+37.0/+45.1 %) and the honest C1 CC-over gradient.

## 5. Blast radius beyond the backcast

`runner._scale_demand` compounds forecast demand from the **weather year's
actual hourly load** — the corrupted Demand cell propagates into every
forecast year that uses a ≥2024 weather year (and 2023's grid-basis wedge
into all of them). This is not a backcast-only defect.

## 6. Adjudication options (rule-14/15 decision for the owner)

The admissibility test (rule 14): the replacement series must be measured,
reproducible for any year from source data, and responsive to changed
conditions — never an output pinned back. All terms below are measured
inputs (930 cells, CEMS hourly, 923 blocks, measured TI); nothing is fitted
to a price/volume residual.

- **Option A (recommended) — supply-consistent honest demand,**
  gated `ScenarioConfig` flag (e.g. `caiso_supply_consistent_demand`),
  default off, CAISO-only: rebuild the backcast demand input as
  `demand(t) = [930 NetGen(t) − NG_cell(t) + CEMS bench-gas grid(t) +
  cogen grid flat + geo/biomass fold-in] − TI(t)`. This is the demand-side
  mirror of the owner-signed bench rework — the model's demand basis becomes
  **identical to the honest basis it is scored against**, so the books close
  by construction (it removes the phantom block, the CHP host accounting
  mismatch, AND the chronic identity gap). Annual levels: 207.7/212.4/205.3
  TWh (−4.8/−5.2/−8.3 % vs the corrupt cell). Built from the same
  generation-frame rows as the renewables series, so the clock is aligned by
  construction (`caiso_demand_clock_realign` becomes a no-op under it).
- **Option B (conservative) — corruption-only correction:** subtract only the
  demonstrated NG-cell phantom block (hourly, CEMS-anchored, from the 2024-05
  onset): −0 / −4.4 / −10.8 TWh. Cleanest provenance (only the proven
  defect), but leaves the model serving ~10–12 TWh/yr (2023 included) that
  the scored honest actuals say nobody generated — C1/C3a books stay
  permanently inconsistent between input and scoring bases.
- **Option C — no change:** keep dispatching the fleet against the corrupt
  cell. The C3a/C1 lanes then chase a residual whose root cause is upstream
  of every mechanism they can touch.

**Pre-registered directions for the Option-A probe** (single delta on the
caiso-78 keeper recipe, main + zero-forcing twin, 2023-2025 one invocation):
C1 CC_REGULAR over-run shrinks toward the honest actuals (largest 2025); C2
over-print shrinks; C3a falls with the year-gradient (2025 most; tight
months ~unchanged — they were already right); C3b NRMSE improves; C4-2025 r
improves; C5a CO₂ over falls; h16–18 demand *rises* ~1–2.7 GW → evening
gas/CT up (the surviving CT deficit the approved local-commitment driver
sizes against SHRINKS — re-measure before implementing it); model imports
fall toward the measured TI; solar curtailment rises toward actual. C6/C7/C8
must hold. Disclosed risk: 2023 May/Jun soft-month overprice may not fully
close (its wedge share is the less-identifiable flat component) — whatever
residual survives is the honest statement of the remaining
margin-formation lane.

Governance: this is a measured-data reconciliation citing the same
demonstrated source defect as the signed bench rework (rule 23 — source
shown wrong against two independent measured sources; rule 15's misalignment
clause — prefer a reconciled version of the real data, documented, over
continuing to use data proven wrong for our representation). It is
solve-side, so unlike the bench rework it requires a full probe solve +
LOYO within 2023–2025 before any keeper swap. LOYO note: nothing is fitted,
but the construction is year-specific measured data, so LOYO is scored
anyway (caiso-78 precedent does NOT apply — that was code-level and
year-invariant; this changes a per-year input series).

## 7. Files

- `scripts/caiso_belly_commitment_probe.py` refresh output (B1) and the
  wedge/fuel-basis diagnostics: session scratch scripts, reproducible from
  the committed data cited above; the probe script itself is unchanged
  (run with `--run-id 2026-07-12-caiso-78-cc-hr`).
- Decision requested: Option A / Option B / Option C above.

## 8. EXECUTED (2026-07-13, owner-signed — caiso-80 session)

The owner signed **Option A** as filed. Implementation (this commit series):
`ScenarioConfig.caiso_supply_consistent_demand` (default off, CAISO backcast
only), `scripts/derive_caiso_supply_consistent_demand.py` → the committed
`data/raw/reference/caiso-supply-consistent-demand/` artifact
(207.40/212.19/205.59 TWh — inside the §6 pre-registered windows),
`eia_loader._load_caiso_supply_consistent_demand` (fail-loud, supersedes the
clock realign by construction), threading through `run_calibration.py` /
`run_calibration_full.py`, and `tests/test_caiso_supply_consistent_demand.py`.
Side discovery fixed in the same series: the 2026-07-12 demand-threading
optimization (`48ec6b9`) checked the PRISTINE per-year config for the CAISO
demand flags, which arrive via the generic `prb_overrides` channel — so any
post-48ec6b9 CAISO solve with `caiso_demand_clock_realign=True` would have
silently threaded the RAW demand (flag inert). No committed bundle was
affected (no CAISO solve ran between 48ec6b9 and this fix); the gate now
reads the effective flag from `prb_overrides` with a `cfg` fallback.
