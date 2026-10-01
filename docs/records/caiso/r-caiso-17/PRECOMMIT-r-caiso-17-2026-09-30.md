# PRECOMMIT — R-CAISO-17 (2026-09-30): pre-2022 EIA-930 CISO clock scan

Owner card 2026-09-30: next link = "Pre-2022 clock scan". Zero LP so far. Written before anything is built.

## 1. Phase-0 result: outcome (b), a window exists. The generation cells are published EARLY, not late

**From the first fuel-cell row (2018-07) through local 2022-06-13, every CISO `NG:` cell and `Net generation` is
stamped about one hour EARLY.** The value stamped at hour-ending `s` is (mostly) the true value of hour-ending `s + 1`.

- `Demand` is on the true clock in this period, and so is `Total interchange`.
- On 2022-06-14/15 the publisher moved every column by +1 h, all together:
  - generation went from early to the true clock;
  - Demand went from the true clock to late. That is the registered demand late window, which opens 2022-06-16.
- So the three windows are one publisher history:
  - generation early, 2018-07 .. 2022-06-13 (this finding);
  - generation true, 2022-06-16 .. 2023-10;
  - generation late, 2023-11 .. 2025-12-02 (R-CAISO-13).

This explains the R-CAISO-16 §7 lead. For 2019–21 the TAC regression preferred NG −1 h: hypothesis (i), a real publisher window.

- Hypothesis (ii), a TAC-file artifact, is refuted by §2.1.
- Hypothesis (iii), NG: WAT-gap noise, is refuted: the signal holds in 2021, which has no gap, and in every single month.

Probes:
- `scripts/probes/_rcaiso17_pre2022_clock_scan.py`, output in `phase0-monthly.csv`, `phase0-daily.csv` and `phase0-tac-audit.csv`;
- `scripts/probes/_rcaiso17_subhour_offset.py`.

Lag convention: +1 means the EIA-930 stamp is late, −1 means it is early. Every series is placed on UTC interval-start. The
EIA `UTC time` is hour-ending, which is the convention that puts Demand on TAC at lag 0.

## 2. The table

### 2.1 The references' own clocks, verified first

| Check | Result |
|---|---|
| OASIS TAC files 2018–2025: UTC continuity | 0 duplicate UTC hours. 0 missing, except one hour in 2024 (2024-08-31 17:00). No DST artifact in any year. |
| TAC vs the Outlook supply sum (no EIA data in this check) | Best lag 0 in 36 of 36 months, 2019–21 |
| Outlook wall clock → UTC | Converted independently. The fall-back hour is dropped. |
| EPA CAMPD (CEMS) | A different publisher. Clock: local standard time, hour-beginning. |

### 2.2 Monthly best lag, 2019–2022

| Pair (EIA-930 ~ reference) | 2019 | 2020 | 2021 | 2022 Jan–May | 2022 Jun | 2022 Jul–Dec |
|---|---|---|---|---|---|---|
| Demand ~ TAC | 0 (12/12) | 0 (12/12) | 0 (12/12) | 0 (5/5) | +1 | +1 (6/6) |
| NG: SUN ~ Outlook solar | **−1** (12/12) | **−1** (12/12) | **−1** (12/12) | no Outlook file | — | — |
| NG: NG ~ Outlook gas | **−1** (12/12) | **−1** (12/12) | **−1** (12/12) | no Outlook file | — | — |
| NG: NG ~ CEMS CA gas | **−1** (12/12) | **−1** (12/12) | **−1** (12/12) | **−1** (5/5) | 0 | 0 (6/6) |
| −TI ~ Outlook imports | 0 (12/12) | 0 (12/12) | 0 (12/12) | — | — | — |
| NG: SUN centroid, h PST (true ≈ 11.8) | 10.96–11.46 | 10.99–11.44 | 11.03–11.43 | 11.20–11.40 | 11.57 | 11.54–11.99 |
| Outlook solar centroid, h PST | 11.62–12.13 | 11.67–12.12 | 11.72–12.11 | — | — | — |

Other checks:
- **Other cells, full year 2019 / 2020 / 2021:**
  - NG: WND ~ Outlook wind: −1 each year (r 0.90 / 0.88 / 0.81, against 0.65 / 0.62 / 0.60 at lag 0);
  - NG: WAT ~ Outlook hydro: −1 each year;
  - Net generation ~ (Outlook supply − imports): −1 each year (r 0.84 / 0.89 / 0.95, against 0.74 / 0.79 / 0.82 at lag 0).
- **Daily resolution:**

  | Pair | 2019 | 2020 | 2021 | 2022 |
  |---|---|---|---|---|
  | NG: SUN ~ Outlook, share of days at −1 | 98.1 % | 99.7 % | 100 % | no Outlook file |
  | NG: NG ~ Outlook, share of days at −1 | 99.7 % | 99.7 % | 100 % | no Outlook file |
  | NG: NG ~ CEMS, share of days at −1 | 83 % | 88 % | 85 % | 39 % (the Jan–Jun 13 days) |
  | −TI ~ Outlook imports, share of days at 0 | ≥ 99.7 % | ≥ 99.7 % | ≥ 99.7 % | no Outlook file |
  | Demand ~ TAC, share of days at 0 | 95.6 % | 100 % | 100 % | — |
- **Solar centroids, sub-period sanity check.** The EIA `NG: SUN` centroid reads:
  - 11.28 h in 2022 Jan–Jun 10 (early);
  - 11.8 h from 2022-07 to 2023-10 (true);
  - 12.7–12.8 h from 2023-11 to 2024 (late).

### 2.3 The transition, hour by hour, 2022-06-13 .. 06-17

- **2022-06-13:** early by CEMS and by the dawn solar ramp. The row stamped 13:00 UTC, 04–05 PST, reads 1,059 MW, which is
  06:00-hour solar.
- **06-14 and 06-15:** mixed. The dawn is true on 06-14 and early on 06-15; the dusk is early on 06-14.
- **From 06-16:** true clock. CEMS daily lag is 0 from 06-14 on, apart from one day at −1 (06-18).
- The Demand late window registered by R-CAISO-13 opens 2022-06-16 08:00 on the same mixed days, which were not asserted there.

### 2.4 Sub-hour: the lead is ≈ 45 min, not a clean 60

Outlook's 5-minute samples resolve the offset below an hour (`_rcaiso17_subhour_offset.py`). The table gives the correlation
of the differenced series with an hour window ending at s + τ.

| τ (min) | 0 | +30 | +45 | +60 |
|---|---|---|---|---|
| NG: SUN, 2021 | 0.826 | 0.982 | **0.993** | 0.954 |
| NG: NG, 2021 | 0.789 | 0.961 | **0.976** | 0.938 |
| NG: WND, 2021 | 0.600 | 0.864 | **0.885** | 0.811 |
| −TI, 2021 | **0.985** | 0.892 | 0.774 | 0.633 |

2019 gives the same picture: the generation peak is at +45, and TI peaks at 0.

- The regression weights agree:
  - NG: NG on CEMS in differences puts ≈ 0.4 on hour t and ≈ 0.7 on hour t+1 through 2022-06;
  - 2022-07 .. 2023-10 puts 0.8 on hour t.
- The solar centroid leads by ≈ 0.55–0.7 h.
- **Consequence for the repair.** The frame is hourly, so the zero-parameter repair re-stamps by one whole hour.
  - The residual is ≈ 15 min late, down from ≈ 45 min early.
  - A fractional (0.75 / 0.25) deconvolution would put a measured parameter into the source repair. It is not built. It is
    noted as a possible refinement for the owner, not a decision of this lane.

### 2.5 Counterparty legs

The corpus holds the BPAT / PACW / NEVP BA-to-BA files only from 2023-01. They cannot reach 2019–22, so they are not
used and nothing is substituted for them. TI is covered instead by Outlook imports (§2.2): it is at lag 0.

## 3. What is built (outcome b)

**Registry.** A new constant:

```
EIA930_CISO_CLOCK_EARLY_WINDOWS_UTC = {"generation": ("2019-01-01 08:00", "2022-06-14 07:00")}
```

- The stamps are hour-ending UTC. Inside the window, the value stamped `s` is the true value of `s + 1 h`.
- The first stamp is the last local-2018 hour. Its value is the true value of the first 2019 model hour.
- Nothing earlier is asserted. The corpus holds no Outlook or CEMS data before 2019; only the solar centroid, 11.2 h in
  2018-12, speaks to it.
- The last stamp is local 2022-06-13 HE24 PDT.
- The mixed days 06-14/15 are not asserted, the same as the demand window.
- The family is the same as the late registry's `generation` family: `NG:` cells and `Net generation`. Total interchange,
  Demand and Demand forecast do not move.
- The constant sits under the SAME flag, `caiso_eia930_clock_repair` (rule 19).
- Zero parameters. The frozen parquet and the CSVs are untouched (rule 23).

**Repair semantics** mirror the late window:
- row `s + 1` takes `published(s)` for every `s` in the window;
- the window's first row, which carries no true value, takes its neighbours' mean;
- the row after the window is overwritten by a value equal to its own truth, because it was published twice.

**Seams**, each of which must honour both registries:

1. **Frame:** `frames._repair_clock_late_windows`, and through it the strict frame, the filled frame, the pool frames and
   the hourly benchmark.
2. **caiso-80 demand term:** `demand._repair_supply_consistent_clock`. The EIA `NetGen − NG_cell` term shifts one row later,
   with the year edge taken from `year − 1`.
3. **HSL generation term:** `renewables._repair_caiso_hsl_clock`. Its gate is widened to cover the early window.
4. **Battery envelope:** `storage._caiso_storage_envelope_clock_repaired`. Its gate is widened. This is inert here: the
   envelope years are 2023+, and 2019–22 borrow 2023.
5. **Zero-LP benchmark rebuild:** it arms from the bundle and inherits seam 1.
6. **Hydro backfill:** `caiso_hydro_backfill.repair_measured_gaps`. It was found in phase 0 and is not in the handoff's
   list.
   - It fills the 2019-10 .. 2020-08 `NG: WAT` hole from Outlook.
   - Its fill is aligned to the EIA stamp "at lag 0". That is the EARLY published grid (hour-beginning = the EIA
     hour-ending stamp).
   - It runs AFTER the clock repair, so armed, the fill must ride the same one-hour move: row `s` takes Outlook
     hour-beginning `s − 1 h`.

**Tests:**
- the off path is byte-identical;
- the armed path moves only the window;
- the seam and year-edge rows;
- the backfill alignment under the arm.

**Shard hard-stop counts** are re-measured after the build and written into the shard prompt before any shard is launched.

## 4. Solve

- 7 shards, one per year 2019–2025 (rule 36). The parent never solves.
- Template: `docs/records/caiso/r-caiso-16/shard-prompt.md`.
- `{SRC}` is `rcaiso16_A_tp_2019_2021` for 2019–21 and `rcaiso16_A_span` for 2022–25.
- The pin is the full SHA after the build PR merges.
- 2023–25 lie outside the new window, so their inputs are byte-identical to the incumbent's. The legs are solved anyway,
  under rules 34(c) and 36.

## 5. Decision rule (pre-registered)

- **Promote on structure (rule 14) if both hold:**
  - (a) 2022–25 stays CALIBRATED, with at most the single ledgered C3c;
  - (b) the window repair is complete: every leg carries the arm and shows the pre-measured hard-stop counts, and 2023–25
    reproduce the incumbent's inputs.
- The fold's movement in 2019–21 is reported at full magnitude. It can never downgrade the ISO (rule 30(c)), and it is not
  a criterion either way.
- **Otherwise** the trade goes to the owner as a decision card.
- A worse fit on 2022 or on the fold is not a reason to withhold the repair (rules 1 and 14). It is a root-cause lead.

## ADDENDUM (written after the build, before any solve)

### Build
- A new constant `EIA930_CISO_CLOCK_EARLY_WINDOWS_UTC`.
- A shared window iterator `frames._ciso_clock_windows()`, with step −1 for late windows and +1 for early ones. Four seams
  were extended:
  - frame, `_repair_clock_late_windows`;
  - caiso-80 demand term, `_repair_supply_consistent_clock`;
  - the HSL gate and the battery-envelope gate, through `frames.ciso_generation_windows_reach`;
  - hydro backfill, through `frames.ciso_generation_source_stamps`.
- The benchmark rebuild inherits the frame seam.
- The surface declaration is at the live hash, as the late sibling's was. The name is unscoped (CISO is not an ISO token),
  so a pre-arm declaration would re-key every ISO; the lane re-solves every CAISO year instead.
- The persisted-identity pins advance +1 row in every ISO. MISO's pin was already one row stale on main; it now reads
  current.

### Armed-vs-unarmed counts (these are the shard hard stop)

Columns: Demand, NG: SUN, caiso-80, HSL solar, HSL wind, TI.

| Year | Demand | NG: SUN | caiso-80 | HSL solar | HSL wind | TI |
|---|---|---|---|---|---|---|
| 2019 | 0 | 7007 | 8752 | 7007 | 8729 | 0 |
| 2020 | 0 | 7119 | 8757 | 7117 | 8739 | 0 |
| 2021 | 0 | 7321 | 8753 | 7321 | 8741 | 0 |
| 2022 | 4776 | 3530 | 3934 | 3530 | 3931 | 0 |
| 2023 | 8752 | 1140 | 1466 | 1140 | 1454 | 0 |
| 2024 | 8758 | 7666 | 8753 | 7664 | 8743 | 0 |
| 2025 | 8049 | 6943 | 8048 | 6943 | 8031 | 0 |

- 2023–25 are unchanged from R-CAISO-16.
- The battery envelope is unchanged: 2023 → 34, 2024 → 40, 2025 → 38.

### Delivered solar centroid on the HSL generation term, h PST, by month

| | Unarmed | Armed |
|---|---|---|
| 2019 | 10.96–11.46 | 11.96–12.43 |
| 2020 | 10.99–11.45 | 11.99–12.45 |
| 2021 | 11.03–11.43 | 12.03–12.43 |
| 2024–25 (true clock, reference) | — | 11.53–12.00 |

The whole-hour repair overshoots the ≈ 45-minute lead (§2.4): 2019–21 now sit ≈ 0.3–0.4 h later than the true-clock
years. The error drops from ≈ −0.6 h to ≈ +0.35 h by centroid, and from −45 min to +15 min by the 5-minute correlation
peak. It is reported; it is not tuned.

### Anomalies noted, not repaired
- **2019-10-03..08:** NG: SUN alone runs at daily lag 0..+2 against Outlook solar, while NG: NG stays at −1. That is a
  solar-cell defect, not the family's clock. October 2019 is the one month whose armed centroid moves 0.73 h rather than
  1.0.
- **caiso-80, 2019 row 0:** no 2018 artifact exists to supply the year-edge value, so the row keeps its own. That is one
  hour.
- **2019-10..2020-08, the `NG: WAT` hydro backfill:** armed, it now reads Outlook one hour earlier, matching its moved
  neighbours. Verified: exact equality on the armed frame at lag 1, and 0 % at lag 0.

### Tests
- `tests/unit/data/test_caiso_eia930_clock_repair.py`: 27 pass, 7 of them new.
- `tests/regression/test_persisted_identity.py`: 24 pass.
- `tests/unit/data`: every test passes except the 3 that also fail on origin/main. They are unrelated: gas anchor vintage
  and cc committed offer margin.
- `check_cache_key_registration`: OK.
