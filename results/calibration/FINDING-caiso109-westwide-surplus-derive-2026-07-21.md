# FINDING (caiso-109 P1-A, DERIVE-FIRST KILL): the west-wide surplus QUANTITY does NOT stabilize the belly import depth either — the belly net import is year-non-stationary at every fixed level of west surplus (CA-side fleet drift no import-supply observable can remove). Lever (A) is not filed; no mechanism armed; keeper `2026-07-19-caiso-102-hourfix` UNCHANGED.

**Session 2026-07-21 (CAISO-109 P1-A — owner GRANTED lever (A): a west-wide
surplus-quantity gate on the daytime/surplus clean-import depth. Derive-first
measurement FIRST (rule 1): no LP form on an unstable observable. The
measurement KILLS the identification, so (A) is filed and re-chartered, not
built — exactly the caiso-106/107 discipline.** NO SOLVE, NO LP. Instrument:
`scripts/probes/_caiso109_westwide_surplus.py` (pure raw EIA-930 BALANCE, all 66
BAs, already on disk).

## 0. What the derive had to settle

P0 (FINDING-caiso109-gas-underdispatch-economic) localized the ~8 TWh/yr
over-import to the belly/daytime clean-import depth and noted caiso-107 had
already refuted deriving that depth on any CA **price** observable, flagging the
neighbor **surplus QUANTITY** as the one un-refuted lever class. The owner
granted (A) on that basis. Derive-first go/no-go: **does a measured WEST-WIDE
surplus quantity make the belly net-import depth year-stable (per-band CV ≤ 0.20
+ LOYO ≤ 0.25, the caiso-81/86/87/106/107 gate)?** PASS → build; FAIL → file the
kill.

The signal is built from EIA-930 BALANCE (already on disk — no new intake
needed): the aggregate of every WECC-West BA (EIA-930 Region NW + SW, CISO
excluded) by UTC hour, three natural quantity forms — aggregate **solar (MW)**,
**solar penetration** (solar/demand), and **net-generation surplus** (NG − D =
net-export capability). The response is the measured CISO belly (local hod 10–14)
net import (= −Total Interchange), from the same BALANCE rows (UTC-aligned, so no
cross-file clock drift).

## 1. VERDICT — every signal FAILS the year-stability gate

| signal | stat | per-band CV / LOYO | verdict |
|---|---|---|---|
| West aggregate solar (MW) | p50 | CV 0.57–0.93, LOYO 158–1772 % | UNSTABLE |
| West solar penetration | p50 | CV 0.53–0.82, LOYO 156–2273 % | UNSTABLE |
| West net-gen surplus (NG−D) | p50 | CV 0.20–4.60, LOYO 53–1435 % | UNSTABLE |
| West net-gen surplus (NG−D) | **p95 ceiling** | CV 0.12–0.76, LOYO 29–1970 % | UNSTABLE |
| West surplus \| CA solar-peak (hod 11–13) | p50 | CV 0.19–3.39, LOYO 51–1701 % | UNSTABLE |

Not one band-set passes — at p50, at the p95 exhaustion ceiling, or conditioned
inside CAISO's own solar-peak hours (the two-sided joint-surplus state
caiso-107 §2 named). The p95 middle bands come closest (CV 0.12–0.18) but every
one still fails LOYO and carries the same trend.

## 2. WHY — a monotone CA-side year-drift the west state cannot remove

The failure has one signature: **at every fixed west-surplus band, the belly net
import rises monotonically 2023 → 2024 → 2025.** Two representative bands of the
net-gen-surplus signal (p50 belly net import, MW):

| west surplus band | 2023 | 2024 | 2025 |
|---|---|---|---|
| [−4, 920) | 962 | 1343 | 2348 |
| [2190, ∞) (West most flush) | 3243 | 4598 | 5305 |

Mean belly net import itself drifts **+743 → +1234 → +1868 MW** (~+560 MW/yr).
Holding the west-wide surplus state fixed, CAISO imports ~2.5× more in 2025 than
2023. This is a **CAISO-side non-stationarity**: CA belly solar grows +1.5 GW/yr
(10.8 → 12.3 → 13.8 GW hod-10–14 mean) and the CA storage fleet roughly doubles
over the window, so the belly transfer for a given west state is a moving target.
No import-supply-side observable — CA price (caiso-107) **or** west-wide quantity
(caiso-109) — can collapse a drift driven by the co-evolving CA fleet.

A second, independent result: the relationship is **positive** — West flush →
CAISO imports **more** (band [−inf,−2230): CAISO *exports* −2360/−2037/−490;
band [2190,∞): CAISO *imports* +3243/+4598/+5305). That is physically correct
(the West dumps into CAISO when it is long), and it means the mechanism
hypothesis "shrink the import depth when the West is flush" is **backwards** —
West-flush is exactly when the import should flow. The over-import is a LEVEL /
non-stationarity defect, not a "wrong-direction in the flush state" defect.

## 3. Verdict + redirect

**Derive-first verdict:** lever (A) is **NOT filed.** A west-wide surplus
quantity does not admit a year-stable, forward-reproducible belly-depth
identification — the second observable class to fail after caiso-107's CA prices.
The belly transfer is genuinely **endogenous to the co-evolving CA + West
fleets**; a single static-or-conditioned depth tranche (the current caiso-87/93/94
construction) cannot represent it, and no observable-conditioned gate on that
tranche will be forward-stable.

**What this leaves (owner-ask, re-raised):**
- **(1) Endogenous WECC import node** — replace the static clean-depth tranches
  with an actual neighbor node carrying its own solar/load/storage (EIA-930
  BALANCE gives the data, now shown on disk) that clears against CAISO through
  the ties, so the belly transfer co-evolves with both fleets instead of being a
  fixed capability. Structurally correct (rule 1); a MAJOR multi-session build
  (new zone + fleet + intake), and the honest home for the CAISO WECC-import
  representation. This is a new structural charter, not a caiso-109 depth patch.
- **(2) Midday gas commitment / min-load** (P0 §6 option B) — the complementary
  gas-side lever: keep ~1.0–1.2 GW more CA gas-CC online midday (CCGT
  min-load-to-bridge-the-evening-ramp physics) so the belly has less room for
  imports. Buildable/A-B-testable in one session; risk C8 forced-energy budget,
  overlaps `caiso_ra_mustoffer`. A partial fix (raises the belly floor; does not
  correct the import-supply root).
- **(3) File and re-charter** — keeper stays `2026-07-19-caiso-102-hourfix`;
  open the endogenous-WECC-node build as its own charter (caiso-110).

Per derive-first, no form is armed without an owner grant on a specific LP
construction.

## 4. Session artifacts

- No solve, no bundle, no mechanism, nothing registered. Keeper UNCHANGED.
- Reproduces from raw data already on disk:
  `scripts/probes/_caiso109_westwide_surplus.py` (EIA-930 BALANCE, no fetch, no
  LP). The measurement is the deliverable; the kill is filed per rule 1.
