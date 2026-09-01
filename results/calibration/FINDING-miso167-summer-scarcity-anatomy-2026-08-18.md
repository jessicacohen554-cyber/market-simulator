# FINDING miso-167 — MISO 2025 summer scarcity: the anatomy of the C3a-2025 miss

**Session:** miso-167 (2026-08-18). **Keeper:** `2026-08-16-miso-160-wefor-shape`
(bundle `results/calibration/miso160_wefor_B`), UNCHANGED.
**No LP solved, nothing armed, no `ScenarioConfig` field added, no cell verdict minted**
(the miso-142/153/155/156/157/161/163/164 no-LP precedent; rule 15 `[R-DASHBOARD]` not engaged).

**Status of the lane.** The MISO C3a-2025 lane was CLOSED by owner ruling at miso-163 as a
model-class limit. **The owner re-opened it in writing on 2026-08-18** — *"2025 miso needs to be
calibrated in summer scarcity it's unacceptable that it doesn't"* — which is unblock
condition (C) of the miso-166 gate, and which sets this session's scope. This finding is the
diagnostic that re-open requires. It does not promote, arm, or tune anything.

Instrument: `scripts/probes/_miso167_summer_scarcity_instrument.py` (5 stages, read-only),
record `results/calibration/_miso167_summer_scarcity_instrument.json`. Every number below is
reproducible from committed artifacts by running that one script.

---

## 1. The miss is 69 % concentrated in 47 hours, and it is a SLOPE defect

MISO's 2025 summer (Jun–Sep, 2,928 h) load-weighted price gap is **+11.75 $/MWh** (model under).
Binned by summer demand decile:

| decile | load GW | model | actual RT | err | model p95 | actual p95 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 62.60 | 31.14 | 23.18 | **+7.96** | 35.2 | 36.9 |
| 4 | 79.96 | 35.78 | 34.91 | +0.88 | 41.4 | 64.1 |
| 5 | 83.66 | 37.52 | 46.69 | −9.17 | 44.8 | 69.1 |
| 8 | 99.99 | 44.87 | 68.53 | −23.65 | 53.6 | 156.7 |
| 9 | **108.68** | **52.29** | **110.42** | **−58.13** | 76.7 | **325.1** |

The model is **over**-priced at low load and **under**-priced at high load. Its summer supply
curve is **4.32× too flat** (model 0.59 $/GW vs actual 2.55 $/GW between the median and top
decile). 47 hours — **1.6 % of summer** — carry **68.9 %** of the entire summer gap.

**This reframes how the lane has been judged.** In 2023 the same defect is present at 1.68× and
in 2024 at 1.67×, but the annual C3a still passes — **by cancellation**, not by correctness: the
low-load over-pricing offsets the high-load under-pricing. 2025's flatness ratio roughly doubles,
cancellation stops working, and C3a-2025 fails at −12.5 %. This is the MISO instance of the
pattern PJM recorded at pjm-139/141 ("annual price level passes by CANCELLATION, not
correctness"). **Consequence for successors: any lever that moves the annual mean uniformly makes
2023 and 2024 worse.** That is why every annual-level lever this lane has tried has failed or been
refused, and it is the mechanical form of miso-161's "against-interest bound" (2023 sits +0.62 % high).

## 2. What it is NOT — three causes measured and eliminated

**(a) It is not load.** Model demand tracks EIA-930 measured MISO demand to **+0.04 %** annual,
**+0.07 %** summer, and **−0.72 %** inside the 47 scarcity hours. Eliminated.

**(b) It is not availability, and no outage intake can reach it.** At the top-200 demand hours the
keeper carries **11.54 GW of idle thermal capability** (miso-161's committed D-1 reconstruction),
of which CT_PEAKER alone is **8.23 GW (45.2 % of its available capacity)**. miso-160 already
removed 3.67 GW of phantom summer capability and miso-161 measured the *remaining* admissible
outage increment at the peak at **+0.69 GW** — against an 11.54 GW cushion. Confirms miso-164's
closure of the GADS ask (candidate 1) and miso-161's immateriality result: **the model is not
short of capacity in these hours, so no availability lever can price them.**

**(c) It is not the reserve REQUIREMENT.** The model already requires **5.21 GW** in the scarcity
hours against the **2.62 GW** MISO's own RT market actually cleared (reg 0.745 + spin 1.165 +
supp 0.712 GW). The model requires roughly **2×** what MISO procures. Raising the requirement
would argue against measured data (rule 14 `[R-ACCURATE]`) and is refuted as a route.

**(d) One real but second-order defect, disclosed:** the model **over-imports by +1.33 GW**
precisely in the scarcity hours (model +5.30 GW vs EIA-930 +3.97 GW), and the same sign appears in
2023 (+1.76) and 2024 (+1.01) — phantom outside energy arriving exactly when MISO was tight. Real,
measured, and worth its own lever; but 1.33 GW against an 11.54 GW cushion cannot be the object.

## 3. What it IS — MISO's own reserve market prices the whole gap

In the 47 actual summer-2025 RT>$200 hours:

| | value |
|---|---:|
| actual RT energy | **$478.55** |
| model energy | $70.31 |
| **energy gap** | **$408.24** |
| **MISO's own published RT ASM MCP (reg+spin+supp)** | **$484.87** |
| model reserve dual | $10.71 (mean), $200 (max) |
| model reserve shortfall hours | 1 of 47 |

**MISO's own reserve price accounts for 118.8 % of the energy gap** (2023: 120.9 %; 2024 is the
honest exception at 19.2 % — 2024's spikes were not reserve-priced). The scarcity is real,
published, and already sitting in `data/raw/MISO-AS/`. The model's reserve constraint is
effectively dormant in exactly the hours MISO's reserve market cleared at hundreds of dollars.

> **[CORRECTED 2026-09-01 — xiso-cascade, rule 14 `[R-ACCURATE]`.]** The "$484.87
> (reg+spin+supp)" row SUMS the three generator ASM MCPs. They are a nested
> CUMULATIVE cascade (`GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP` in 100.0000 % of
> committed cells, every year, both markets — BPM-002 product substitution), so a
> reserve MW earns the cascade TOP — **$193.30** in these 47 hours — never the sum;
> the sum triple-counts the shared shadow prices (the nyiso-166 §2 instrument
> rule). Corrected headline: **MISO's own published reserve price accounts for
> 47.3 % of the energy gap** (2023: 48.4 %; 2024: 10.5 %) — roughly HALF the gap,
> not all of it. The §4 structural argument (the model's reserve constraint is
> dormant while MISO's own market priced reserves at real money) survives at the
> corrected magnitude; the stronger reading "MISO's own reserve market prices the
> WHOLE gap" (this section's title included) does not. Measured and independently
> reproduced: `scripts/probes/_xiso1_miso_asm_cascade_check.py`; instrument
> corrected (`asm_top`), record carries a dated CORRECTION key;
> `docs/FINDING-xiso-cascade-scan-2026-09-01.md`.

## 4. Why the model's reserve constraint never binds — the structural defect

`src/market_sim/model/reserves/spec.py::_miso_design` **never sets `online_gated`**; it is left at
the `ReserveDesign` default of `None`. MISO's reserve requirement is therefore backed by the
headroom of **all** eligible capacity, **online or not** — an idle, unsynchronised CT's full pmax
can satisfy MISO's regulating and spinning requirement.

This is precisely the misrepresentation NYISO identified at nyiso-83 and corrected with
`nyiso_spin_reserve_online` — whose own citation reads: *"Idle capacity cannot be 'spinning':
letting an offline peaker's pmax satisfy a spinning requirement is the same idle-allowed-headroom
misrepresentation."* The `online_gated` / `online_rho` machinery is **ISO-agnostic and already in
the LP** (`model/lp/reserve_rows.py`); PJM arms it via `pjm_reserve_online_gated`. **MISO does not
arm it, and no MISO cell for it exists** (`nyiso_spin_reserve_online` is `.` in the MISO shard —
n/a, being NYISO-scoped by name).

The sizing is the point: the 5.21 GW requirement is being met substantially by **CT_PEAKER's
8.23 GW of idle, largely unsynchronised capacity**, while the classes that are genuinely running
(COAL 0.29, CC_REGULAR 1.34, CC_CHP 0.12, CHP 0.09 GW) contribute only **~1.8 GW** of true online
headroom. Gate reserve supply to online capacity and the constraint stops being dormant.

**This answers the objection standing against the neighbouring `measured_ramp_capability` cell**
(MISO `U`), which reads: *"miso-153's D-4 found reserves INERT at the summer peak … A qualifier
that tightens a constraint which never binds cannot move a price."* The inference is inverted: the
constraint never binds **because** reserve supply is unrestricted. Non-binding is the *symptom* of
the defect, not an independent fact about the market. Restricting supply to what can physically
provide the product is what makes it bind.

**It is NOT `ordc_scarcity_overlay` (MISO cell `G`).** That refusal is about the reserve DEMAND
curve — MISO's Monte-Carlo LOLP construct pricing 10–30-minute probabilistic risk a
perfect-foresight hourly LP does not contain. The object here is the reserve **SUPPLY** side: who
is physically allowed to sell the product. No demand curve is touched, no adder is added, and no
LOLP construct is reconstructed. The miso-163 grounds are untouched by it.

## 5. How much of the miss is actually reachable — the honest ceiling

Splitting the 47 scarcity hours by whether MISO's **own day-ahead market** (itself a deterministic
co-optimized LP with foresight) also priced the hour up:

| | n | mean load | DA | RT | model | share of summer gap |
|---|---:|---:|---:|---:|---:|---:|
| **DA-foreseen** (DA>$150) | 20 | 109.09 GW | $254.12 | $546.68 | $102.72 | **34.1 %** |
| **RT-only** (DA≤$150) | 27 | 98.69 GW | $80.55 | $428.09 | $46.31 | **34.8 %** |

- The **RT-only half is a genuine model-class limit** and miso-163 was right about it. These
  spikes occurred at *moderate* load (98.7 GW) in hours MISO's own DA market priced at $80. A
  perfect-foresight hourly LP cannot manufacture a spike the market's own forward-looking
  deterministic clearing did not foresee. Example: hour 6425 (Sep), load 84.57 GW, DA $98.90,
  RT $1,598.45. Nothing structural in an hourly LP reaches that.
- The **DA-foreseen half is reachable.** At 109.09 GW of load MISO's DA market — deterministic,
  co-optimized, foresighted, the same class of model as ours — cleared **$254**; ours clears
  **$103**. That gap is not a model-class limit, it is a missing supply-side restriction.

**Therefore the honest ceiling on any structural fix is ~34 % of the summer gap** (~34.1 % of
+11.75 $/MWh ≈ 4.0 $/MWh of summer, ≈ 1.3 $/MWh annual ≈ **+3.3 pp on C3a-2025**, against the
2.5 pp needed to clear the ±10 % bar). **This is not a promise that C3a-2025 will pass** — it is
the arithmetic bound on what the reachable half is worth if a mechanism captured all of it, which
no mechanism does. It is stated here so no successor session can quote a larger prize.

## 6. What this finding does and does not change

- It **does not** change the keeper, any determination, any caveat, or any ledger text. MISO
  remains **NOT-YET on C3a-2025 alone (−12.5 %)**, reported at full magnitude as a model miss;
  C3c remains the single ledgered caveat.
- It **does not** re-open `ordc_scarcity_overlay` (`G`), the GADS ask (miso-164), the MOM daily
  grain (miso-161), or any other DO-NOT-REDO cell. It confirms (b) and (c) of those closures on
  fresh, independent measurements.
- It **does** identify one previously-unexamined structural defect with a named code site, a
  published product-definition driver, zero fitted parameters, and a forward story
  (§4), and it **bounds the prize honestly** (§5).
- It **does** put on record that MISO's 2023/2024 C3a passes are partly cancellation artifacts
  (§1), which every future MISO session should know before quoting them.

## 7. Next step and its blocker

The mechanism is specified with pre-registered kill gates in
`PREREG-miso167-online-gated-reserve-supply-2026-08-18.md`. **It was not executed in this session:
the container has 15 GB RAM against miso-161's measured >13.9 GB/year for a MISO plant-level LP,**
so the required control+arm pair over `--year 2023 2024 2025` is not runnable here. Per CLAUDE.md
("If the session lacks RAM/time for a solve, say so and ask the owner how to proceed — do NOT
silently spin up a CI job"), this is reported rather than worked around. A successor session needs
**≥24 GB**.
