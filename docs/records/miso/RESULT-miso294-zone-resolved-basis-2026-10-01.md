# RESULT — miso-294: MISO C3a/C3b actual is now zone-resolved (Part A); C3b 2021 is the fall coal-for-gas swap (Part B, zero LP)

```
LANE      : miso-294 (owner rulings on DESIGN-miso293 §8: "Basis: Adopt for MISO now"; "Next lane: C3b 2021")
PRECOMMIT : docs/PRECOMMIT-miso294-zone-resolved-basis-2026-10-01.md (46d299f1, pushed before any change)
KEEPER    : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span), unchanged
LP        : none
```

## Part A — zone-resolved basis

### What changed

1. `scripts/data/derive_actual_lmp.py`: the ERCOT-only `if iso == "ERCOT"` branch of `_lw_fields` is now a
   per-ISO registry `ZONAL_LW_SOURCES` (ERCOT, MISO). MISO's zone → hubs map is read from the archive's own
   `zone` column, and MISO-Plains uses the declared MINN+ILLINOIS proxy. `src_lw` comes from the registry
   entry. No other ISO was added.
2. **Defect found and fixed in the same file.** Run as a CLI (`python scripts/data/derive_actual_lmp.py`),
   the repo root was not on `sys.path`. `load_demand` therefore could not import
   `scripts.data.curate_zonal_shares`, and it **silently fell back to STATIC zone shares**. The system total is
   unchanged; only the zonal split differs. That is harmless for a system-hub actual, but wrong for a
   zone-resolved one: MISO 2019 `rt_lw` came out 25.52 instead of 25.67. The script now also inserts the repo
   root. Evidence the fix is correct: ERCOT's committed `rt_lw` values (derived through an importer) now
   reproduce exactly from the CLI, while without the fix ERCOT 2019 drifted 46.55 → 46.85.
3. `actual_lmp.json`: MISO 2019–2025 `{rt,da}_lw`, `{rt,da}_lw_mon` and `src_lw` were rewritten. Every
   non-MISO block is byte-identical, and the refactor itself is ERCOT-neutral (old vs new code give
   byte-identical ERCOT output).
4. `frontend/data/backcast/bench/MISO/{2019..2025}.json.gz`: the four numeric `avgLMP` keys were surgically
   patched using the miso-292 method:
   - same writer settings, and the original bytes round-trip exactly;
   - the decoded part minus the four keys equals the original;
   - the fingerprint is untouched, and there was no bench regeneration.
   `check_bench_freshness --iso MISO`: 7 parts, **0 STALE**.
5. `status/MISO.js` rebuilt. New test: `tests/curation/test_lw_zonal_registry.py` (4 tests).

### Numbers — every PRECOMMIT value reproduced exactly

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `rt_lw` single hub (before) | 27.15 | 22.99 | 40.63 | 73.45 | 32.85 | 32.30 | 45.46 |
| `rt_lw` zone-resolved | 25.67 | 21.97 | 39.23 | 63.25 | 30.19 | 29.28 | 42.12 |
| C3a | +8.7 % | **+11.6 % F** | −5.6 % | −5.1 % | +8.4 % | +5.1 % | −1.1 % |
| C3b NRMSE | 0.114 | 0.165 | **0.201 F** | 0.122 | 0.104 | 0.101 | 0.083 |

Flips: C3a 2020 PASS→FAIL, C3a 2022 FAIL→PASS, C3b 2022 FAIL→PASS. **Full span NOT-YET on C1 ST_GAS 2019,
C3a 2020, C3b 2021.** Train tier 2023–2025 CALIBRATED (C3c ledgered). C3a 2023 now sits at +8.4 %, near the
band edge. No frontier.

## Part B — C3b 2021 phase 0 (zero LP; `scripts/probes/_miso294_c3b2021_phase0.py`)

C3b 2021 is 0.201 against a 0.20 cap. Share of the squared error by month (zone-resolved):

| month | model | actual | gap | SSE share |
|---|---:|---:|---:|---:|
| Feb | 47.5 | 60.9 | −13.4 | 24 % |
| Sep | 37.4 | 46.2 | −8.9 | 11 % |
| Oct | 41.0 | 56.3 | −15.2 | 31 % |
| Nov | 41.0 | 52.4 | −11.4 | 18 % |
| other 8 months | | | +2 to +6 high, mostly | 16 % |

- **Feb** is Winter Storm Uri. That miss is already owner-ruled a routed extreme-event miss (miso-269/280: no
  admissible daily Gulf print).
- **Sep–Nov is 60 % of the error, and it is a North-wide level miss, not congestion and not gas.**
  - In Oct, every North zone actual is $53–60 against a uniform model $38; South is $47 vs $51.
  - The median misses as well as the tail (Oct p50: 39 model vs 53 actual).
  - miso-269 already showed model gas sits *above* the hub in these months.
- **The quantity signature is a coal-for-gas swap.** Model minus EIA-930 MISO TWh:

  | 2021 | Jul | Aug | Sep | Oct | Nov | Dec |
  |---|---:|---:|---:|---:|---:|---:|
  | coal | −2.0 | −2.7 | +2.8 | +4.5 | +4.0 | +2.7 |
  | gas | −0.7 | −0.2 | −5.2 | −7.3 | −6.8 | −4.6 |

  - In fall 2021 the real fleet burned gas at $5+ and held coal back. The model burns that coal and clears
    $15 lower on CCs.
  - This shape (coal under in summer, over in fall) appears in **2021 and 2022 only**. The other years carry
    a flat annual coal offset vs EIA-930 of +6 to +13 TWh, which is likely boundary, but no seasonal swing.
  - 2022 is the year miso-288 documented: the fleet drew its piles in summer and rebuilt them Sep–Nov.
- **Reading:** C3b 2021's fall component is the **coal budget-grain object**, which the owner CLOSED in
  miso-290 after four pre-registered kills (all on 2022). Under rule 28 no cell is re-tested. Two facts are
  new: 2021 has the same signature as 2022, and that signature dominates a scored failure. Whether that
  justifies reopening is the owner's call.

### C3a 2020 (+11.6 %) — the same object as 2019/2023/2024, yes

- In **every** year 2019–2025, the model is $3–7 above actual in the bottom four load quintiles, with p50 high
  by $4–7. It is under only in the top load quintile, where the actual tail is missing from the model.
- C3a is the net of the two. In low-volatility years (2019, 2020, 2023, 2024) the tail is small, so the
  low-end overshoot dominates (+5 to +12 %). 2020 (COVID load, $2 gas) has the smallest tail, so it reads
  highest.
- This is the night/low-end overshoot that miso-285–287 traced to price formation at matched quantities,
  mainly the coal fuel-budget dual. Its levers are adjudicated:
  - `diurnal_price_amplitude`: G.
  - `miso_gas_ecomin_online_floor`: I.
  - the coal budget-grain line: closed.
- No new admissible lever was found.

## Retrievability

No solve; nothing on shard disk. All artifacts are in this PR.
