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

PENDING

## §2 D2 — the original derivation: what produced 5.0?

PENDING

## §3 D3 — derived value, window sensitivity, and whether 5.0 was ever right

PENDING

## §4 D4 — scope: is this ERCOT-solar-specific?

PENDING

## §5 Card-ready recommendation

PENDING
