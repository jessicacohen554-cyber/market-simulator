# FINDING nyiso-219 §Q1/Q3 — Robert Moses Niagara holds **15 minutes** of pondage. The LP gives it **730 hours** of arbitrage freedom

**Session:** nyiso-219, NYISO `backcast-calibration` lane. **Branch:**
`claude/nyiso-hydro-within-month-cq14o1`. **Date:** 2026-09-07.
**Owner rulings executed:** **Q1** *fund the full intake*; **Q2** *decide the rule-19 posture at
phase 0*; **Q3** *undecided — measure the shaping horizon, not the `Mode` label*.
**ZERO LP.** Keeper `2026-09-07-nyiso-213-summer-seam` untouched; nothing armed, screened, solved
or registered; no `ScenarioConfig` field; no `src/market_sim/` change; no marker moved; no cell
letter changed; no held-out year spent.
**Instruments:** `scripts/probes/nyiso219_pondage_duration.py` →
`results/calibration/_nyiso219_pondage_duration.json`; new raw source `data/raw/nid/`
(USACE National Inventory of Dams, vintage 2026-08-28, provenance + checksum in its README).

---

## 0. The result in one paragraph

The owner funded the NID intake and asked, on Q3, that the fleet's **shaping horizon** be measured
rather than read off ORNL EHA's categorical `Mode` label. It is now measured, and it settles the
charter's premise. Built deliberately as an **upper bound** — full reservoir volume rather than the
licensed operating range, turbine efficiency taken as **1.0**, zero free parameters — **72.01 % of
NYISO's scored hydro MW cannot hold even ONE DAY of its own full output**, 97.54 % cannot hold a
week, and 98.31 % cannot hold a month. **Robert Moses Niagara — 51.89 % of the fleet's MW — holds
0.244 hours: about fifteen minutes**, from a **71-acre** forebay of 5,350 acre-ft. The LP's hydro
budget row grants that plant a **730-hour** month to arbitrage across. Because the bound is generous
in every direction, **no refinement of the operating range can rescue the monthly period**: the
overstatement is roughly three orders of magnitude for the single largest plant in the fleet.
**Q3 is answered: the fleet does not shape across weeks.**

## 1. What was measured, and why an upper bound is enough

Pondage duration is derived from first principles with **no fitted constant**:

```
E(J)   = rho * g * V * H
E(MWh) = 1000 * 9.81 * V(m^3) * H(m) / 3.6e9  =  1.024505e-3 * V(acre-ft) * H(ft)
pondage_hours = E(MWh) / pmax(MW)
```

**Every choice runs in the generous direction**, so the conclusion cannot be an artifact of a
tuned input:

* **full reservoir volume**, not the licensed operating range — the range is a *band* inside this
  volume, so the true usable figure is strictly smaller (the charter named this overstatement in
  advance, before the number was seen);
* **efficiency = 1.0**, a strict physical bound; any real efficiency (~0.85–0.92) only *reduces*
  the hours;
* `Max Storage` reported alongside `Normal`, the larger of the two carrying the headline.

**The logic that makes this decisive:** if even the most generous reading holds far less than a
month, a **monthly** budget period overstates the plant's intertemporal freedom — and the two
things the intake did **not** recover (§4) could only make the number *smaller*.

## 2. The measurement

**Coverage:** 152 of 163 plants, **98.53 % of fleet MW** (the 11 unscored plants carry no NID dam
id). Head is NID's `Hydraulic Height` for **20.80 %** of scored MW and the **labelled dam-height
proxy** for the rest (§4).

| generous bound | share of scored MW below it |
|---|---:|
| **1 day (24 h)** | **72.01 %** |
| 1 week (168 h) | 97.54 % |
| **1 month — the LP's period today (730 h)** | **98.31 %** |

**The plants that carry the fleet:**

| plant | MW | % fleet | storage (normal, acre-ft) | head (ft) | head basis | **pondage hours (max storage)** |
|---|---:|---:|---:|---:|---|---:|
| **2693 Robert Moses Niagara** | 2,429.1 | **51.89** | **5,350** *(71-acre forebay)* | 97 | dam-height **proxy** | **0.244 h ≈ 15 min** |
| **2694 Robert Moses St. Lawrence** | 912.0 | **19.48** | 750,000 | 81 | **hydraulic height** | **73.07 h ≈ 3.0 d** |
| 54580 | 59.0 | 1.26 | 3,150 | 37 | proxy | 2.02 h |
| 2612 | 56.0 | 1.20 | 31,000 | 146 | proxy | 82.80 h |
| 54953 | 44.0 | 0.94 | 413 | 17 | proxy | 0.16 h |
| 2641 | 43.6 | 0.93 | 414 | 22 | proxy | 0.21 h |

MW-weighted mean 124.0 h; **median plant 4.42 h**; p90 120.3 h.

**On Niagara specifically, where the proxy runs the *helpful* way.** Its NID dam height (97 ft)
badly *understates* the true powerhouse head — the plant takes water above the falls and drops it
through conduits to the base of the escarpment, a head several times the dam's. **Using the proxy
therefore UNDERSTATES its pondage hours**, and the conclusion survives the correction: even at a
head three times larger the figure is ~0.75 h. **Under an hour, against a 730-hour budget period.**

**On St. Lawrence, where the bound is wildly generous.** 750,000 acre-ft is the full volume of Lake
St. Lawrence; the licensed band the operator may actually move within, under the IJC Plan-2014
regulation of Lake Ontario outflow, is a small fraction of it. The true figure is far below 73 h.

## 3. What this does to the charter's premise — and to Q3

The charter argued the budget **period** is the defect. §2 is the physical confirmation:

* the LP's hydro row grants every plant a **730-hour** reallocation window;
* **72 % of fleet MW physically holds under 24 hours**, and the single largest plant holds
  **minutes**;
* so the model's freedom exceeds the fleet's physics by **one to three orders of magnitude**,
  concentrated in exactly the plant that dominates the fleet.

**This is a fully independent confirmation of the nyiso-218/219 measurements**, arriving from
hydrology rather than from dispatch: the model over-swings within-month daily energy at
**1.86–2.25×** the actual's amplitude, tracks daily load at **r 0.62–0.69** where the real fleet
tracks it at 0.20–0.47, and no daily driver explains the gap — because the missing constraint was
never a driver, it was the **storage the fleet does not have**.

**Q3's answer, in the terms Q3 asked for.** The owner declined to read the horizon off EHA's
`Mode` label and asked for a measurement. Measured: **the fleet does not shape across weeks.** The
`Peaking` labels are not wrong — they describe genuine *diurnal* forebay cycling, which is exactly
what a 15-minute-to-3-day pondage supports — but they do **not** license a month. The object stands.

## 4. What the intake did NOT recover — stated plainly

The owner funded storage **plus** the licensed operating range **plus** head. **One of the three
came back.**

| target | outcome |
|---|---|
| **per-dam storage** | **RECOVERED** — `Normal`/`Max Storage` present for **98.4–98.5 %** of fleet MW |
| **head** | **MOSTLY NOT** — NID's `Hydraulic Height` covers only **20.80 %** of scored MW; the rest is on the **dam-height proxy**, whose error runs in **both** directions (§2) |
| **licensed operating range** | **NOT IN NID AT ALL** — `Normal Storage` is a reservoir volume, not an operating band. Recovering it needs the projects' **FERC licence documents**, which this intake did not touch |

**This does not block the conclusion**, because both missing pieces could only shrink the bound:
a true operating range is a band *inside* the volume, and a corrected head changes individual
plants without touching the fact that 72 % of MW is under a day. **It does block a per-plant period
length**, which is what a build would need — see §6.

## 5. Two defects I made and corrected, reported rather than smoothed over

**(a) `drop_duplicates` silently discarded the informative row.** A `NID ID` names a **project**,
not a structure, and is **not unique**: St. Lawrence's `NY00678` carries **seven** rows (main dam +
six dikes), all repeating the same project storage. My first pass collapsed them with
`drop_duplicates`, which kept an arbitrary first row — "South Forebay Dike", no hydraulic height —
and discarded "Robert Moses - St. Lawrence" (81 ft). That put **19.5 % of fleet MW** on a
dam-height proxy it did not need and reported head coverage as **1.03 %** of scored MW. **Caught by
cross-checking against the §5-census figure of 20.50 %, which disagreed.** Corrected to a
project-level aggregation (storage `max` once per project — never a sum, which would multiply it by
the structure count; head the best figure any structure reports). Head coverage is now **20.80 %**,
consistent with the census, and St. Lawrence's bound *tightened* from 122.68 h to **73.07 h**.

**(b) The published headline was wrong by 6 points for one turn.** The charter as first written
said "78 % of fleet MW carries a peaking component"; the committed probe's own definition — every
label containing "Peaking" — gives **84.24 %**. Both are now reported with the difference explained
(`Run-of-river/Upstream Peaking`, 3.23 %, has the peaking *upstream* of the powerhouse), and
neither is quoted alone.

Both traps are recorded in `data/raw/nid/README.md` so the next consumer does not repeat them.

## 6. What is now known, and what a build would still need

**Known:** the monthly period is refuted for essentially the whole fleet, on a bound that cannot be
argued down. **Still needed before any mechanism arms:**

1. **A per-plant period length** identified from the **licensed operating range**, not from the
   full reservoir volume — i.e. the FERC-licence half of Q1 that NID could not serve. Rule 21
   `[R-DOF]` case 3 stands: **a length chosen because it makes a criterion move is forbidden**, and
   this session neither chose nor swept one.
2. **The Q2 phase-0 overlap arithmetic** — the owner ruled the rule-19 posture is decided *there*,
   on measurement. `hydro_dispatch_envelope` is armed in the keeper and binds **27–42 %** of hours
   carrying **32–49 %** of annual hydro energy, so replace-vs-reconcile turns on how much of that
   binding a shortened period would subsume. **Not measured here** — it needs the period length
   from (1) first.
3. Everything §6 of the charter already refuses: no `NG: WAT` pin, no period sweep against the
   gates, no stacking, no per-plant hourly structure invented.

**Rule 14 `[R-ACCURATE]`, restated before any build:** hydro is ~20 % of NYISO generation, so
re-timing it **will** move C3a/C3b/C3c. If the faithful representation makes the price fit worse,
**it stays**, and the worse fit is a discovered root-cause question. The 2026-07-25 probe is the
precedent — it made C3a-2023 worse (+18.3 → +22.2 %) and was still recorded as mechanism confirmed.

**No new owner card is opened.** Q1 is discharged (with §4's honest partial result), Q3 is answered,
and Q2 remains where the owner put it: at phase 0, pending a period length. The seven unrelated
pending rulings are untouched.
