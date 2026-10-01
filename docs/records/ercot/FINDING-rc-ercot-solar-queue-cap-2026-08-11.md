# FINDING — RC-DERIVE: re-derive `QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]` from source

**Card:** R-c, SIGNED 2026-08-11 (owner sitting Addendum AK.8). **MEASUREMENT ONLY.**
**Branch:** `claude/rc-derive-ercot-solar-queue-cap-23ao54` off freshly-fetched `origin/main`.
**Scope discipline:** no constant is edited, no solve is run, no matrix cell changes, no other
cap is touched. Adoption returns to the owner as a card carrying the number below.

**Rule anchors:** rule 23 `[R-FROZEN-DERIVE]` — the trigger for this re-derivation is the
**data record** (the post-2020 EIA-860 COD history), never a residual or a gate. Rule 25
`[R-ISO-SCOPE]` — the D4 scope read reports what it sees per ISO and transfers nothing
between ISOs. Rule 5 `[R-NO-MAGIC]` — the object of the exercise is a constant whose citation
is the question.

---

## §0 PRE-REGISTRATION (committed before any number was computed)

This section was written and committed **before** the derivation was run, so the construction
could not be chosen to land on a preferred answer. Commit: the one that adds this file with
§1–§4 marked PENDING.

### §0.1 What the constant claims to be

`config/capacity_market.py::QUEUE_CAP_PER_TECH_GW` is introduced by exactly one comment:

```
# Per-technology annual interconnection queue caps (GW/yr) by ISO.
# Source: ERCOT CDR, CAISO TPP — approximate historical queue throughput by tech
```

and the ISO-total sibling `QUEUE_CAP_GW` states the semantics the per-tech caps inherit:

> a *ceiling* on the total nameplate MW … the institutional/physical interconnection
> *throughput* limit, i.e. how much capacity can plausibly reach commercial operation (COD)
> per year … it caps the pace, so **a value modestly above each ISO's demonstrated peak annual
> COD is correct**.

So the constant's own definition fixes the construction to be replicated:
**demonstrated peak annual COD throughput, rounded modestly up.** That is what §1 recomputes.

### §0.2 Pre-registered construction (D1)

| Element | Pre-registered choice |
|---|---|
| Source | `data/raw/eia-860/eia860_generator_operable.parquet` (top level = **2025 Early Release** snapshot) joined to `eia860_plant.parquet` on `Plant Code` |
| ERCOT filter | `Balancing Authority Code == "ERCO"` (1,402 plants present). Sensitivities: `NERC Region == "TRE"`; `State == "TX"` |
| Solar filter | `Technology` ∈ {`Solar Photovoltaic`, `Solar Thermal with Energy Storage`, `Solar Thermal without Energy Storage"`} — the model's `solar` tech |
| Capacity metric | `Nameplate Capacity (MW)`, AC. **Not** `DC Net Capacity (MW)` — the LP's `pmax` is AC nameplate |
| COD year | `Operating Year` (year of entry into commercial operation) |
| Throughput | annual sum of nameplate over generators with `Operating Year == Y` |
| Primary window | `Operating Year` ∈ **2021–2025** ("post-2020", per the card) |
| Primary statistic | **max** annual throughput over the window (the "demonstrated peak" the comment names), then rounded modestly up |
| Rounding | smallest value ≥ the demonstrated peak on the granularity the existing table already uses (0.5 GW steps), stated explicitly |
| Survivorship | `*_operable` holds only units still operable at the vintage. Units with an in-window COD that later retired are recovered from `eia860_generator_retired_and_canceled.parquet` and reported as a sensitivity |
| Status | `Status` ∈ {OP, SB, OS, OA} present; primary read uses all four (a built unit demonstrated throughput regardless of later status), with an OP-only sensitivity |

### §0.3 Pre-registered sensitivities (D3)

Window sensitivity is reported over: **2021–2025** (primary), **2021–2024** (drops the
possibly-partial Early-Release 2025), **2020–2025**, **2022–2025**, **2023–2025** (trailing 3).
Secondary statistics reported alongside the max: mean, median, min.

### §0.4 Pre-registered vintage test (D3, "was 5.0 ever right?")

`data/raw/eia-860/vintage_2018 … vintage_2024` snapshot the same schema at each historical
release. The identical construction is run **inside each vintage** — i.e. what would this
construction have returned to an author sitting at that vintage? A vintage whose demonstrated
peak rounds to 5.0 GW is a vintage for which 5.0 was the right answer.

### §0.5 Pre-registered refutation criterion

**If the derived cap rounds to 5.0 GW, the FFR-9C §4.2 case is refuted and this document says
so plainly.** That is a fully successful outcome of the card, not a failure.

### §0.6 Pre-registered scope read (D4)

The identical construction is run for every (ISO, tech) pair in `QUEUE_CAP_PER_TECH_GW` that
EIA-860 can identify (BA codes `ERCO`/`CISO`/`PJM`/`MISO`/`NYIS`/`ISNE`), and the ratio
cap ÷ demonstrated-peak is reported. **Report only.** No value is transferred between ISOs
(rule 25); no cap other than the ERCOT-solar object is recommended for change by this card.

### §0.7 What must survive this work

FFR-9C's contrast is load-bearing and is **not** to be manufactured away: **wind's cap never
binds after stage B, so there is no wind-cap case.** §1 reports wind's demonstrated throughput
as a measurement, and §5 does **not** recommend a wind change.

---

## §1 D1 — the cap recomputed from the post-2020 EIA-860 record

**Headline: the demonstrated peak is 7.74 GW. The pre-registered construction returns a cap of
8.0 GW. It does not land on 5.0, so the FFR-9C §4.2 case is NOT refuted — it is confirmed.**

ERCOT solar nameplate reaching COD, by year (GW, BA = `ERCO`, EIA-860 2025 Early Release):

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | **2024** | **2025** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.14 | 0.27 | 0.66 | 0.66 | 0.70 | 2.27 | 3.97 | 2.53 | 3.55 | **7.29** | **7.74** |

Primary window 2021–2025: **peak 7.74 GW (2025)**, mean 5.02, median 3.97.

This **independently reproduces FFR-9C's cross-check** (7.29 GW 2024 / 7.74 GW 2025) to the
second decimal, from the raw parquet, under a construction pre-registered before the numbers
were seen.

**The current cap sits below the record it claims to bound.** `5.0` is **0.65×** the
demonstrated peak; measured throughput is **1.55× the constant** — i.e. ERCOT physically
interconnected half again more solar in 2025 than the model is permitted to build in any
forecast year.

### Identification sensitivities (all 2021–2025)

| Identification | peak (GW) |
|---|---:|
| `Balancing Authority Code == ERCO` (primary) | **7.74** |
| `NERC Region == TRE` | 7.63 |
| `State == TX` | 8.21 |
| `ERCO`, `Status == OP` only | 7.74 |
| `ERCO`, + retired/canceled sheet (survivorship) | 7.74 |

The identification choice moves the peak by ±0.5 GW and **never below 7.6 GW**. Status
filtering and the survivorship correction change nothing — no post-2020 ERCOT solar unit has
left the operable sheet.

### The contrast that must survive: ERCOT wind (measurement only)

| 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3.39 | 2.52 | 1.83 | 1.51 | 3.47 | 2.10 | 3.95 | 3.85 | 1.46 | 1.73 | 1.67 |

Wind's peak over 2021–2025 is **3.95 GW (2021)** — comfortably **below** its 5.0 cap, which is
why the wind cap never binds. **This document therefore recommends no wind change and creates
no wind-cap case.** §2 shows *why* the two techs share a cap yet diverge: the number was right
for both when written, and only solar's throughput moved.

## §2 D2 — the original derivation: what produced 5.0?

**Recovered.** The introducing commit is
[`f4f139b`](https://github.com/jessicacohen554-cyber/market-simulator/commit/f4f139b0e7775b30b56515bb1d18c8e5c71c4fe0)
— **2026-05-16 16:31:53Z**, *"Add per-tech queue caps, carbon pricing, and capacity integration
tests"*. (The local clone is shallow at 357 commits and cannot reach it; recovered via the API
plus a `--depth=1` fetch of that one commit.) The ERCOT entry **at birth**:

```python
QUEUE_CAP_PER_TECH_GW: dict[str, dict[str, float]] = {
    "ERCOT": {"wind": 5.0, "solar": 5.0, "gas_cc": 3.0},
    "CAISO": {"wind": 3.0, "solar": 4.0, "gas_cc": 2.0},
}
```

**`solar: 5.0` has never been edited.** It is the birth value, and the two-line comment above it
is byte-identical to the one on `main` today, 87 days later.

**What produced it — the honest answer to "what window, what statistic, what vintage":**

> **None of the three was ever recorded, and the commit that created the constant was not a
> measurement exercise.**

The commit message states its own purpose:

> *"Fix economic new entry awarding the entire ISO queue budget to one tech by adding
> per-technology queue caps"*

The constant was introduced to **fix a budget-allocation bug** — one tech consuming the whole
12 GW ISO budget — not to strike a measured per-tech throughput. The values are what was needed
to make a per-tech cap *exist and bind*. Corroborating detail: ERCOT's caps at birth partition
the 12 GW ISO total (5 + 5 + 3 = 13 ≈ 12), and **wind and solar were given the identical value**
— the signature of a split, not of two independent per-tech measurements.

**Everything the repo offers as provenance, exhaustively:**

| Artifact | What it says about `ERCOT.solar = 5.0` |
|---|---|
| `capacity_market.py` comment | `Source: ERCOT CDR, CAISO TPP — approximate historical queue throughput by tech`. A source **name** and the hedge *"approximate"*. **No window, no statistic, no vintage.** |
| `docs/parameter-citations.md:1750` | `queue_cap_per_tech_gw.ERCOT.solar \| 5.0 \| … \| auto-generated, needs-citation` — **citation column empty**. The repo's own "every numeric input traced to a primary source" registry carries it as uncited. |
| `docs/handoffs/queue-cap-citation-2026-07.md` | The 2026-07 citation pass cited the **ISO totals** and relabelled the **eastern** per-tech splits as engineering judgment. It **never examined ERCOT/CAISO per-tech**, leaving them the only unreviewed cells. Its §"In-repo check (Step 0)" confirms **no queue/COD-throughput dataset exists on disk** — the named ERCOT CDR source was never curated. |
| `CHANGELOG.md` | **No entry** records the constant's introduction (the CHANGELOG begins 2026-05-16, the same day). |

So the named source (ERCOT CDR) is real and plausible but **unverifiable in-repo**, and the
construction behind the number was never written down. A value that cannot be regenerated from
a stated window + statistic + vintage is, in rule 5 `[R-NO-MAGIC]` terms, a magic number wearing
a citation.

## §3 D3 — derived value, window sensitivity, and whether 5.0 was ever right

### The derived value

| Basis | Value |
|---|---:|
| **Pre-registered primary** (smallest 0.5 GW step ≥ demonstrated peak 7.74) | **8.0 GW** |
| Same-multiplier-as-the-original (§3.3: 1.26 × 7.74) | 9.75 → **9.5–10 GW** |
| **Defensible band** | **8.0 – 9.5 GW** |

§0.2 binds this document to **8.0 GW** as *the* derived number — the most conservative
defensible value, only 1.03× the demonstrated peak. The 9.75 figure is reported as a
sensitivity because it is what the *original author's own implied multiplier* returns against
the updated record (§3.3); it is not the pre-registered answer.

### §3.1 Window sensitivity — the answer barely moves

| Window | peak | mean | median | ⇒ derived cap |
|---|---:|---:|---:|---:|
| **2021–2025 (primary)** | **7.74** | 5.02 | 3.97 | **8.0** |
| 2021–2024 (drops Early-Release 2025) | 7.29 | 4.33 | 3.76 | 7.5 |
| 2020–2025 | 7.74 | 4.56 | 3.76 | 8.0 |
| 2022–2025 | 7.74 | 5.28 | 5.42 | 8.0 |
| 2023–2025 (trailing 3) | 7.74 | 6.19 | 7.29 | 8.0 |

**Window sensitivity is ±0.5 GW.** Four of five pre-registered windows return 8.0 GW; the
fifth returns 7.5 GW. Combined with the identification sensitivities (§1), the derived cap
spans **7.5 – 8.5 GW across every reasonable choice**. **No window, statistic, or
identification produces anything near 5.0.** The result is not an artifact of window selection.

Two biases both run **against** the finding, so 8.0 GW is conservative:
- 2025 sits in an **Early Release** and may be under-reported (the top-level snapshot's 2024
  figure, 7.29 GW, matches the settled `vintage_2024` figure of 7.28 GW, so the release is not
  materially lossy — but a partial 2025 can only push the true peak *up*).
- Nameplate AC is used, not DC (§0.2); the DC figure would be higher still.

### §3.2 Was 5.0 ever right? — **Yes. It was right for its vintage, and it has gone stale.**

The identical construction run *inside* each historical EIA-860 snapshot — what an author
sitting at that vintage would have measured:

| vintage | demonstrated peak ERCOT solar COD visible | 5.0 vs that peak |
|---|---:|---|
| 2018 | 0.71 GW (2018) | 7.0× — far above |
| 2019 | 0.71 GW (2018) | 7.0× — far above |
| 2020 | 2.47 GW (2020) | 2.0× — above |
| 2021 | 3.96 GW (2021) | **1.26× — correct** |
| 2022 | 3.97 GW (2021) | **1.26× — correct** |
| 2023 | 3.96 GW (2021) | **1.26× — correct** |
| **2024** | **7.28 GW (2024)** | **0.69× — already stale** |

**5.0 GW was a well-struck number against a ≤2023-vintage record.** At vintages 2021–2023 the
demonstrated peak was 3.96–3.97 GW and 5.0 sits **1.26×** above it — squarely inside the
"modestly above demonstrated peak" convention the constant's own docstring states, and in line
with the ISO-total anchors (MISO 10 GW on ~9 GW/yr = 1.11×; PJM 10 GW on a demonstrated 8–10 GW
peak = 1.0–1.25×).

**This also explains the wind/solar contrast without manufacturing a wind case.** At the
seeding vintage the two techs' demonstrated peaks were nearly identical — wind 3.95 GW, solar
3.97 GW (both 2021) — so one number, 5.0, was correct for both at the **same 1.26× multiplier**
(wind 1.27×, solar 1.26×). What happened next is that ERCOT wind throughput *fell* (1.46/1.73/
1.67 GW in 2023–25) while solar roughly **doubled off its own prior peak twice**. Same
constant, same vintage, same construction — divergent futures. **Wind's 5.0 is still correct
today; solar's is not.**

### §3.3 What actually went wrong

Not the derivation — **the freshness**. The constant was seeded on 2026-05-16 against a record
whose latest fully-settled year was 2023. But the repo's own `vintage_2024` snapshot (EIA data
year 2024, published by EIA in 2025 — *before* the seeding date) already showed a 7.28 GW peak.
So the value was defensible against the record the author evidently used and **already stale
against the best record then available**; two further years of throughput (7.29, 7.74) have
since widened the gap to 1.55×.

Rule 23 `[R-FROZEN-DERIVE]` is satisfied precisely here: **the trigger for re-deriving is that
the source data record moved** — 2024 and 2025 CODs landed — not that a residual or a gate
moved. Nothing in this document is derived from, or checked against, any model output.

## §4 D4 — scope: is this ERCOT-solar-specific?

**No — but it is nearly so.** Running the identical construction across every (ISO, tech) cell
in `QUEUE_CAP_PER_TECH_GW` (2021–2025, BA-code identification), **exactly two of 42 cells have
a cap below demonstrated peak throughput**:

| ISO | tech | cap (GW) | demonstrated peak (GW) | cap ÷ peak | throughput ÷ cap |
|---|---|---:|---:|---:|---:|
| **ERCOT** | **solar** | 5.0 | **7.74** | 0.65 | **1.55×** |
| **MISO** | **solar** | 6.0 | **7.15** | 0.84 | **1.19×** |

Every other cell has a cap at or above its demonstrated peak. So the defect is **not generic to
the construction** — it is specific to **solar in the two ISOs where solar build accelerated
hardest**, which is exactly the failure mode of a per-tech pace ceiling frozen at a 2021-vintage
record while one technology's throughput tripled.

Reported per rule 25 `[R-ISO-SCOPE]`: **the MISO number is an observation, not a transfer and
not a recommendation.** No ERCOT value is proposed for MISO, and MISO's cell would need its own
session deriving its own parameter from its own market's record. This document recommends **no
change to any cap other than the ERCOT-solar object of card R-c.**

Two further observations, report-only:

1. **Large slack elsewhere is common and harmless in this direction** — CAISO geothermal 68×,
   PJM offshore-wind 167×, CAISO gas-CT 14×, ERCOT gas-CC 12× demonstrated peak. A cap far
   above throughput simply never binds; it is not evidence of a defect, and none of these is
   proposed for change.
2. **ERCOT's ISO-total `QUEUE_CAP_GW` = 12 GW is *not* the binding constraint** and does not
   need to move for a solar change to take effect. ERCOT's all-tech COD was 13.84 GW (2024) and
   15.28 GW (2025), which *is* above 12 — but batteries (4.12 / 5.62 GW) enter through the
   separate storage-entry path, not this budget. **Excluding storage, ERCOT COD was 9.72 GW
   (2024) and 9.66 GW (2025)** — roughly 2.3 GW of headroom under the 12 GW total. A solar cap
   of 8.0 GW alongside recent wind (~1.7 GW) and gas (~1 GW) throughput sums to ~10.7 GW and
   **still clears the ISO total**, so raising the solar cap would not simply relocate the
   binding constraint. (Stated as measurement to inform the owner's card; `QUEUE_CAP_GW` is not
   touched and no change to it is recommended here.)

## §5 Card-ready recommendation

**For the owner's adoption card. Nothing below has been applied.**

**Recommendation: change `QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]` from `5.0` to `8.0`
(GW/yr).**

| | |
|---|---|
| **Object** | `src/market_sim/config/capacity_market.py::QUEUE_CAP_PER_TECH_GW["ERCOT"]["solar"]` |
| **Current** | `5.0` — unedited since 2026-05-16 (`f4f139b`) |
| **Derived** | **`8.0`** (pre-registered primary); defensible band **8.0–9.5** |
| **Basis** | Demonstrated peak annual ERCOT solar COD 2021–2025 = **7.74 GW** (2025), EIA-860 2025 Early Release, BA `ERCO`, nameplate AC — the constant's own documented construction ("modestly above demonstrated peak annual COD") |
| **Robustness** | 7.5–8.5 GW across all five pre-registered windows × four identifications. Both known biases run conservative |
| **Rule 23 trigger** | The **source data record moved** (2024 + 2025 CODs landed). No residual, gate, or model output enters this derivation |
| **Rule 13 admissibility** | Unchanged. It stays a published throughput ceiling regenerable for any forward year — the same class of input it already was, at a current value |
| **Scope** | **This cell only.** No other cap, no ISO-total, no wind change, no MISO change |

**Why 8.0 rather than the 9.75 the original multiplier implies:** 8.0 is the smallest value
consistent with the measured record, so it is the change least able to be accused of buying
model freedom. If the owner prefers strict fidelity to the original author's own convention
(peak × 1.26, the ratio implied by 5.0 ÷ 3.97), the answer is 9.75 and the cap would be 9.5–10.
**8.0 is recommended; the band exists so the owner can choose the convention, not the outcome.**

**What adoption would change, stated honestly:** FFR-9C §4.2 established this cap binds at
into-2024 in both staged arms, margin-independently across $51–$2,420. Raising it to 8.0
therefore **will** change forecast build and is **not** a cosmetic edit — it releases a
constraint that is currently the sole thing holding 2024 solar entry down. That is the point of
the card, but it means adoption should be followed by a forecast-lane run whose result is
reported on the **forecast** dashboard, and the mechanism-matrix cell for the ERCOT entry lever
re-stamped by **that** session (rule 28(b)) — not by this one, which tested no mechanism.

**If the owner declines:** the constant should at minimum stop claiming a citation it cannot
support. `docs/parameter-citations.md` already carries it as `needs-citation`; the code comment
should say so too, or name the window/statistic/vintage that justifies 5.0 — which, per §2, no
artifact in the repo currently does.

---

### Provenance of this document

Derivation script (measurement only, wrote nothing into the repo): the session scratchpad copy
of `derive_queue_cap.py`, reproducible from §0.2 against `data/raw/eia-860/`. Every number in
§1, §3 and §4 comes from that one run over committed raw data.

**Card compliance:** no constant edited · no solve run · no matrix cell changed · no other cap
touched · no ISO transfer · pre-registration committed before derivation (`2daa219`).
