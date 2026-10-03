# PRECOMMIT — NWPP-NEXT-22: the priced interface with measured seam headroom, on keeper #20, 2019–2025

Fixed before any solve. Owner cards:

- NEXT-21 (2026-10-02): "Hold #20, fix seam headroom".
- NEXT-22 phase 0 (2026-10-02): "CAISO share + BPA BC".

Evidence: `FINDING-nwppnext22-seam-headroom-2026-10-02.md` (§A–§E). Lane NWPP-NEXT-22, branch `claude/nwppnext22`, base
main `d1eb727e`.

## 0. Parallel-lane check (done before any LP)

- No other live NWPP calibration session.
- NEXT-21 (`session_01LP9kkHDK9XimFi6RRJJmfQ`) was idle and its PR #7065 had merged, so it was archived at session
  start.
- The only open PR matching "nwpp" is #7021 (SOCO-100, not NWPP).
- `claude/w0-nwpp-*` belong to the close-out W0 lane (EIA-860 settlement re-solves). Their shard sessions are idle.
  W0 has not landed a new NWPP keeper: keeper #20 is unchanged on main.
- Card N4 / R-a is still unruled by the CAISO lane. FINDING §A bears on it.

## 1. The arm

Keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`), each year replayed from its own leg bundle with exactly:
`--set reference_price_interface=true --set priced_interchange=true --set nwpp_seam_measured_limits=true`.

- The first two keys are NEXT-21's arm, unchanged; NEXT-21 PRECOMMIT §1 says why both are needed.
- The third key is this lane's one new lever.

Leg SHAs (keeper #20): 2019 `1e4bd215c635aa876ab3ad75f8fb4657f4e47cec` · 2020 `aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6` ·
2021 `3b38fefe402b5168c1557459a28978eb9274ed92` · 2022 `11bb59fbf0d6a4b8716362f0e8c2f1899a601d11` ·
2023 `a54c7b97a9c588564bab90746f2dbbc44fd56838` · 2024 `91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8` ·
2025 `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe`.

**Mechanism (`nwpp_seam_measured_limits`).** There is one aggregate interface row per priced seam, on the net flow out
of the seam's external zone. Each row bounds it as `−export_cap(t) ≤ net import(t) ≤ import_cap(t)`.

| seam | cap source | mean import / export cap MW, 2019 … 2025 |
|---|---|---|
| CAISO_COI | CAISO MALIN500_ISL + CASCADE_ITC OTC (from 2023-06-19); else 2/3 × BPA COI operating limit | 2319/2398 · 1221/2695 · 1142/2624 · 1603/2947 · 1804/2705 · 1858/2751 · 1905/2740 |
| WECC_CAN | BPA BC Intertie operating limit (priced 2023–25 only) | 2413/2290 · 2271/2342 · 2301/2161 (2023–25) |
| CAISO_NEVP | unchanged, 1,933 MW (no published limit on its boundary) | — |

The bands still sum to the registered rating. The row binds only where the measured limit is tighter.

**Zero-LP construction check at the pin** (this session, the pin's code in isolation):

- 3 external zones;
- seam rows 32 (2019–22) / 48 (2023–25);
- served residual identical to NEXT-21: −1.96 / 4.27 / −10.39 / −9.28 / −22.12 / −19.06 / −6.15 TWh;
- seam groups 1 (2019–22) / 2 (2023–25), with the cap means above.

The arm demand frame is NEXT-21's: 272.855 / 274.573 / 268.646 / 277.900 / 262.091 / 271.477 / 287.331 TWh.

## 2. The pin and G-DRIFT (rule 29(b)): off the handoff's "main + code", with the reason

**Pin `a5a72ec04be06ef8cb861aa6d5c68689dfc9c688` (`claude/nwppnext22-pin`).** It consists of:

- NEXT-21's pin `86b73d6f` (= keeper code pin `33014efc` + NEXT-19/20 wiring; NEXT-21 PRECOMMIT §2 classified that
  drift);
- from main, the CAISO OASIS `TRNS_USAGE` intake the COI cap reads (R-CAISO-30);
- this lane's code.

The handoff asked for main + code. I declined that for two measured reasons:

1. **Main moved 167 solve-path files since `86b73d6f`, including `uv.lock`.** A G-DRIFT audit of that span is a lane of
   its own, and every LIVE hunk would contaminate the comparison against both keeper #20 and NEXT-21.
2. **Main's `data/raw/reference/nwpp_plant_basis_energy.csv` changed after `86b73d6f`** (the W0 settlement data). At
   main, the 2025 served residual is −9.39 TWh against −6.15 at the pin. That is a demand-basis change W0 owns, not
   this lever.

The pin keeps the arm a one-lever change against NEXT-21. The pin is a transport branch: if this arm is promoted, the
keeper's code provenance is the pin SHA, as with keepers #19 and #20.

G-DRIFT, pin against `86b73d6f`, from `git diff 86b73d6f a5a72ec0 -- src scripts`:

- `scripts/lib/transfer_interface_limits/{__init__,caiso,nwpp}.py`, the CAISO / BPA raw data, the schema and the two
  fetchers: read only through `nwpp_seam_limits_hourly`, so **INERT** for the keeper.
  (`__init__` gains `max_fill_hours`, whose default `None` gives PJM byte-identical output.)
- `constants.py`: three new constants. `solve_surface_declared.py`: their declarations. **INERT** (read only under
  the key).
- `scenarios.py`: the new field, default False, dropped from the cache hash at its default. **INERT** off, **LIVE** on.
- `spec.py`: `import numpy` and `build_seam_limit_groups`, called only under the key. **INERT**.
- `transfer_interface_limits.py`: new functions only. **INERT**.
- `run_calibration.py`: one block under `nwpp_seam_measured_limits and iso == "NWPP"`. **INERT** off.
- The probe and the tests are off the solve path.

**The only LIVE change is the key itself.** No control solve: NEXT-21's committed legs are the control for the first
two keys, and keeper #20's legs are the control for all three.

## 3. Gates, declared ex ante

**(a) Structural STOP gate (NEXT-21's, unchanged).** For each priced seam and year:

- the annual net flow has the measured sign;
- the hourly r against the measured leg is > 0.

NEVP 2019 (−0.3 TWh) and COI 2023 (+1.1 TWh) are read but cannot fail on sign alone.

**(a′) Headroom live (STOP).**

- Every shard's hard stop (h): the P1 net seam flow exceeds no cap by more than 1 MW, for COI in every year and BC in
  2023–25.
- The log line `measured seam headroom on N seam(s)` is present.

**(b) Verdict diff, per (criterion, year, key):**

- against keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`);
- **and** against NEXT-21 (its committed legs, scored this session).

Every PASS → FAIL flip against keeper #20 is reported with its root cause.

**(c) Rule 20 / D-2 / C6, and CT_PEAKER volume against actual** (from `legitimacy_diagnostics.json`).

**(d) The BC↔CA wheel:** hours with COI importing and BC exporting at once, 2023–25, with MWh.

**(e) Seam volume:** the per-seam and summed net TWh against NEXT-21 and against measured.

## 4. Expected outcome (stated so the result cannot reshape it)

From FINDING §D, at price-taker against keeper #20's price, the summed priced-seam export falls from
37.7 / 39.1 / 36.0 / 34.0 / 38.1 / 47.2 / 20.0 to 26.1 / 27.9 / 26.5 / 25.6 / 29.2 / 36.6 / 16.6 TWh.

NEXT-21's LP realized 27.7 / 33.3 / 35.2 / 32.7 / 30.2 / 36.8 / 17.1 TWh. Expectations, all against NEXT-21:

- The arm's seams fall by roughly a quarter to a third, and so does the gas fill (CC_REGULAR, CT_PEAKER).
- **COI 2019 / 2023 / 2024 stays 2–6× measured.** That is the price-level gap the FINDING routes onward, and this lever
  does not fix it.
- C4 gas regressions should shrink but may not all clear.
- The 2023 price and coal gains may partly give back, because a tighter seam imports less of CAISO's price shape.
- Price stays UNSCORED in 2019–2022.

## 5. Hard stops per shard

NEXT-21's nine, with these changes:

- STEP-1 adds `curate_transfer_interface_limits.py --isos NWPP CAISO` and checks the seam groups and cap means.
- The `scenario_config` diff allows exactly `nwpp_seam_measured_limits` and `reference_price_interface`.
- New stop (h): headroom live, the caps respected.

The prompts are at `docs/records/nwpp/nwppnext22/shards/shard_<Y>.txt`.

## 6. Composition and decision

Compose `nwppnext22_span` with `_nwpp42_compose_span.py --skip-diagnostics` (2023 leg first), then run legitimacy
diagnostics. The attestation is NEXT-21's wrapper extended with the third key. Register with
`dashboard_add_run --no-prune`, then score `calibration_verdict --json` for keeper #20, NEXT-21 and this run.

**Decision rule (owner standing ruling).** Promote if structural integrity improves, even if a gate regresses. Report
every regression at full magnitude.

The arm is the priced interface (the endogenous exchange NEXT-21 established) bounded by the market's measured operating
limit instead of the nameplate. It is a candidate when:

- (a) and (a′) hold;
- rule 20 and C6 pass;
- no new failing record traces to the arm's own construction.

If it is a candidate, promotion goes on ONE owner card with the prune. If it is not, the cells are recorded and the
next lever is the price level.
