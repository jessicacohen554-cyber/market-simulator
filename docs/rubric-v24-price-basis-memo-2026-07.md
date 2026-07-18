# Rubric v2.4 — the like-for-like C3 price basis (2026-07-09)

Owner-authorized amendment (session-logged, the ercot52 offer-re-tune thread):
C3a/C3b score against a **load-weighted actual** instead of the legacy
equal-hour hub mean. Scorer `scripts/calibration_verdict.py`
(`RUBRIC_VERSION = 2.4`), bench derivation
`scripts/data/derive_actual_lmp.py --lw-retrofit`, committed-part retrofit
`scripts/archive/retrofit_lw_price_bench.py`, probe scorer
`scripts/probes/_score_probe.py`. Discovery + proof:
`docs/handoffs/ercot-ordc-capdual-adder-2026-07.md` §4 and the 2026-07-09
calibration-log entries.

## 1. The defect (why the old basis was not measuring price skill)

C3a's model side is the system **load-weighted** mean LMP (per-zone
demand-weighted zonal means, zone-demand-weighted across zones — the payload's
`lmp[z].p × lmp[z].d`). Its actual side was `avgLMP.rt` — the **equal-hour**
mean of a hub series (`derive_actual_lmp.py`; per-ISO constructions in §3).
The two bases diverge by the price-demand covariance, which is exactly what a
realistic scarcity tail creates:

* Feeding the **actual** 2023–25 ERCOT LZ settlement prices through the
  scorer's own formula scores **+33.5% / +15.5% / +11.7%** against the
  scorer's own benchmark — a byte-perfect model FAILS the ±10% gate in all
  three years.
* The wedge GROWS with tail realism, so C3a and C3c were structurally in
  tension: deepening the tail toward the measured price-duration curve
  (correct) inflated C3a (scored wrong). Historical single-digit C3a readings
  were partly shallow-tail-vs-wedge cancellations (ercot46's +9.3% flipped to
  **−17.5%** on the honest basis — it was under-pricing peak-demand hours by
  ~a sixth, hidden by the basis).

## 2. The v2.4 construction

`rt_lw` / `da_lw` (+ `*_lw_mon` monthly vectors, `src_lw` provenance) weight
each ISO's committed hourly actual by the **same measured demand the model
dispatches** in a backcast (`eia_loader.load_demand` — byte-identical weights
on both sides of the comparison):

* **ERCOT (zone-resolved):** committed zonal LZ settlement archives
  (`actual_lmp_zonal_ERCOT.parquet`) × measured zonal demand, model-zone
  crosswalk `ERCOT_MODEL_ZONE_TO_LZ` (Houston→LZ_HOUSTON, North→LZ_NORTH,
  Northeast→LZ_RAYBN, South→LZ_SOUTH, South_Central→mean(LZ_AEN, LZ_CPS,
  LZ_LCRA), West/Panhandle→LZ_WEST) — the scorer's formula mirrored on the
  actual. ERCOT 2025 has no committed zonal DA series, so `da_lw` is absent
  for that year (RT gates; nothing lost).
* **Other ISOs (system-level):** the committed hourly system series
  (`actual_lmp_hourly_<ISO>.parquet`) × measured system load. The residual
  zonal-weighting wedge (hub vs load-zone premium) is second-order (ERCOT
  measured it at ~$3/MWh equal-hour) and is documented per ISO in `src_lw`;
  an ISO gaining a committed zonal archive should upgrade to the
  zone-resolved construction.

Fallback ladder (scorer): `rt_lw` → `da_lw` → legacy `rt` → legacy `da`; the
legacy basis is labelled "LEGACY equal-hour basis" in the verdict record, so
no ISO-year loses coverage and every reading names its basis. C3c is
untouched (a count, not a mean). The legacy `rt`/`da` fields stay committed
for display continuity and the DA-diagnostic history.

> **Clock note (2026-07-15):** the committed `*_lw` fields were derived when
> the hourly parquets were still prevailing-clock indexed, so their
> price×demand pairing is one real hour off in DST months (the all-ISO
> scoring-clock fix, 2026-07-15 calibration-log entry). The parquets are now
> chronological; a `--lw-retrofit` re-run (plus the
> `derive_ercot_zonal_lmp.py` / zonal-parquet re-index it depends on for
> ERCOT) re-pairs them exactly, but it moves every ISO's C3a reference and
> re-scores keepers — deferred to its own owner-signed change. The committed
> values remain the standing C3a basis until then.

Admissibility: measured prices × measured load, both committed raw/derived
artifacts, forward-reproducible (a forecast year weights by forecast load);
no model output enters the bench (rules 11/13/15/21). The lw retrofit is a
methodology-change re-derivation, not a residual response (rule 23 of the
audit / CLAUDE.md rule 21 citation discipline).

## 3. Per-ISO bench audit (what the legacy field actually was)

| ISO | legacy `rt` construction | rt vs rt_lw (2023/2024/2025) |
|---|---|---|
| ERCOT | HB_HUBAVG settlement point, equal-hour mean | 48.36→**64.12** / 26.83→**30.71** / 32.49→**35.98** |
| PJM | mean of 12 trading hubs, equal-hour | 28.44→29.55 / 29.53→31.31 / 42.89→45.80 |
| CAISO | 3 trading hubs load-weighted by STATIC zone share, equal-hour over time | 43.83→46.25 / 32.94→34.60 / 33.63→34.39 |
| MISO | system reference series, equal-hour | 31.79→32.87 / 30.80→32.27 / 42.85→45.39 |
| NYISO | simple mean of 11 internal zones, equal-hour | 30.29→32.30 / 35.95→38.20 / 60.74→66.53 |
| NEISO | .H.INTERNAL_HUB, equal-hour | 35.70→38.00 / 39.50→41.56 / 65.89→70.09 |

Every ISO's actual rises under honest load weighting (real prices covary with
load everywhere); ERCOT's rises most because its 2023 tail is the deepest.

## 4. Keeper re-score (v2.3 → v2.4) — determinations and C3a magnitudes

No keeper's DETERMINATION flips: NYISO and NEISO stay
CALIBRATED-WITH-CAVEATS; ERCOT/PJM/CAISO/MISO were already NOT-YET on v2.3
and remain NOT-YET. Magnitudes move to the honest basis:

| keeper | C3a v2.3 | C3a v2.4 | note |
|---|---|---|---|
| ERCOT ercot46 | +9.3 / +6.5 / +4.9 (PASS) | **−17.5 (CAVEAT⚠)** / −6.9 / −5.3 | shallow tail exposed; ⚠ see §5 |
| PJM pjm-94 | −9.2 (PASS, 2025 only) | **−14.9 (FAIL)** | within-criterion flip; ISO already NOT-YET |
| CAISO caiso65 | +21.7 / +37.2 / +44.4 (FAIL) | +15.3 / +30.6 / +41.2 (FAIL) | overshoot shrinks (its miss was body, not tail) |
| NYISO nyiso-56 | +4.3 / −7.7 / −7.5 (PASS) | −2.2 / **−13.1 (CAVEAT⚠)** / **−15.5 (CAVEAT⚠)** | ⚠ see §5 |
| NEISO neiso-55 | −3.7 / −1.8 / +4.3 (PASS) | −9.6 / −6.6 / −2.0 (PASS) | clean |
| MISO miso-48 | −0.1 / −4.7 / −10.7 | −3.4 / −9.1 / −15.7 | 2025 FAIL either way |

The uniform downshift (~3–8 pp) says the fleet-wide bias is UNDER-pricing
load-weighted (peak-demand) hours — consistent with under-formed scarcity
tails everywhere except CAISO (a body-level overshoot). The candidate
`2026-07-09-ercot52-ordc-capdual` scores **C3a −1.0 / −0.3 / −3.6 (PASS all
years)** and **C3b 0.109 / 0.296 / 0.079** on v2.4.

## 5. Stale-ledger auto-forgiveness — OPEN owner decision

`_apply_ledger` matches exceptions on **(criterion, year[, key]) only** — no
magnitude, direction, or basis check. Two keepers now have out-of-band v2.4
readings auto-forgiven by ledger entries written for DIFFERENT numbers:

* ercot46 `price_mean 2023`: entry written for "+9.3% (CAVEAT, commercial
  band)" now covers **−17.5%** — opposite direction, ~2× magnitude.
* nyiso-56 `price_mean 2024/2025`: entries now cover −13.1% / −15.5% readings
  that PASSED when the entries were written.

Neither changes a determination today, but the matcher lets a ledger entry
outlive the reading it attested. Owner options: (a) require re-attestation
when a ledgered criterion's magnitude moves by more than some band, (b) add
the attested magnitude to the match, (c) accept and note. Tightening the
matcher is itself keeper-affecting (NYISO could drop) — deliberately NOT done
in v2.4 (out of authorized scope).

## 6. What did NOT change

Bands (±10% / 0.20), C3c (DA-expressible count + RT diagnostic), coverage
masking, the DA-diagnostic row (now read on the lw pair when both exist), the
decision logic, ledger budgets, and every non-C3 criterion. Registered run
payloads were not touched (they cannot be regenerated — bundle parquets are
not retained); only bench parts, the derived reference, and the scorer moved.
