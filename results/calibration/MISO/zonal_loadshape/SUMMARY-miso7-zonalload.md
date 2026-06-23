# MISO miso7 zonalload — run summary

**Determination: NOT-YET (PROBE).** Governance gate unattested (no
`calibration_attestation.json`), and the level/scarcity misses below are real
MODEL MISSes, not accepted limitations. Registered as a comparison probe to
isolate the cumulative effect of the per-zone load work on the current MISO
build.

## What this run is

The `miso3` reserve-coopt config (`--energy-reserve-coopt --priced-interchange`,
reference-price import node, `miso_firm_imports` on), **re-solved on current main
(`7910d91`)** so it carries every MISO structural change merged since `miso3`:

- **Per-zone hourly load shapes** from EIA-930 sub-BA demand (this session) —
  zones drawn as whole sub-BA/LRZ unions so load and transmission partitions
  coincide; North=`{0001,0035}`, Central=`{0027,0004,0006}`, South=`{8910}`;
  fallback `load_share` 0.285/0.444/0.271; WI→Central, MO→North fleet alignment.
- **RDT asymmetric links** (3,000 MW N→S / 2,500 MW S→N one-way pair).
- **Per-zone N/C/S wind CF shapes** (NASA POWER, reconciled to EIA-930 aggregate).
- **#812 coal curves** (measured EIA-923 take-or-pay), coal-class, Manitoba
  firm-hydro import.

P1 only (no P2 commitment screen). All three testing years solved (2023/24/25).

## Result (load-weighted system LMP, $/MWh)

| year | miso7 model | actual | Δ | miso3 model |
|------|------------:|-------:|------:|------------:|
| 2023 | 28.98 | 31.79 | −8.8% | ~28.86 |
| 2024 | 25.89 | 30.80 | −15.9% | ~25.57 |
| 2025 | 37.11 | 42.85 | −13.4% | ~36.89 |

The full structural stack nudges the level a few tenths toward actual vs the
static-share `miso3` baseline, but the ~3–6 $/MWh shortfall remains.

## Where the miss lives

- **Scarcity tail absent (C3c).** Model produces **0** hours >$200 in every year
  vs actual 30 / 37 / 88. This is the dominant LMP-level driver: the energy/
  reserve co-optimization is structurally present but stays inert on the
  perfect-foresight LP, so no scarcity prices form.
- **No zonal price separation.** North 36.38 ≈ Central 36.38 ≈ South 36.27 (2025).
  The N↔C link is still the **12,000 MW order-of-magnitude placeholder** (the
  posted MTEP/OASIS limit was allowlist-blocked), so the internal wind-export
  corridor never binds and North/Central clear identically. The per-zone load
  and wind shapes are in, but without a real N↔C limit they cannot create
  congestion rent.
- **C2 family volumes** slightly off (2025 coal +19%); **C3b price shape PASSES**.

## Reading

The per-zone load/wind structure is correct and now wired, but the two levers
that would actually move MISO's LMP level/shape — a **binding N↔C corridor
limit** and a **live scarcity tail** — are still open. Next structural step is
the real N↔C interface limit (item 6 remainder) and making the reserve demand
curve bite (scarcity), not further load-share tuning.
