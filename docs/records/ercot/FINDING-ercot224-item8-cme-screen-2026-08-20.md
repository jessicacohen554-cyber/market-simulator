# FINDING — ercot-224 (item-8 CME/NYMEX reopen screen, Phase-0): the sole reopen condition is FACTUALLY FALSE — CME/NYMEX delisted every Waha and Houston-Ship-Channel gas contract before the training span (Waha basis 2020-12-07, HSC basis 2022-01-10, the swing/index families 2017-10, all on zero open interest) — **ITEM 8 STAYS CLOSED, now effectively unconditionally**

**Session ercot-224, 2026-08-20, branch
`claude/ercot-224-calibration-ye2ivp`. NO LP, no solve, no intake, no
arming, no registration; keeper untouched at
`2026-08-20-ercot223-arm-eventrelease`.** Precommit
`docs/PRECOMMIT-ercot224-item8-cme-screen-2026-08-20.md` pushed +
blob-verified (blob `df65c0eb`, 151 lines) BEFORE any CME/NYMEX content was
read; executed as written. Probe record:
`scripts/probes/ercot224_cme_basis_screen.py` →
`results/calibration/ercot224_cme_basis_screen.json`.

## 1. What was screened

§5.1 item 8 (a daily Waha/HSC gas basis to ground the CT offer-cost
object — ERCOT-147 §3's confound is daily by construction) is CLOSED,
REFUSED ON DATA (owner, 2026-08-04: NO PAID DAILY GAS DATA; monthly
insufficient). Its **sole recorded reopen condition**: *"CME/NYMEX
publishes Waha and Houston-Ship-Channel basis-swap daily settlements
publicly at no cost"*, subject to a rule-13 admissibility screen. The
precommit pinned two in-scope families on that route — **F1** basis
futures (monthly Platts Inside FERC index differential vs NYMEX HH) and
**F2** Gas-Daily-settled swing/index products, both hubs — with access
legs A1–A4, admissibility legs B1–B3, and a fail-closed verdict rule.

## 2. The screen result — A1 (existence) FAILS on both hubs and both families

The reopen condition presumes the products exist. They do not, and did not
at any point in the 2023–2025 training span. Primary CME documents
(retrieved 2026-08-20; quoted in the probe record):

| Document | Date | What it establishes |
|---|---|---|
| "Delisting and Removal of Platts Natural Gas Products" (`notices/electronic-trading/2017/10/delplatts.pdf`, the SER-8000 track, 2017-10-16) | Oct 2017 | The **entire Platts regional gas complex removed from CME Globex**: Waha index **IY**, swing **SY**, fixed **WFS**, basis options **A5O**; HSC index **HIP**, swing **SMN**, fixed **XJT**, basis option **5F**. This alone kills family F2 for both hubs. |
| **SER-8689** (`notices/ser/2020/12/SER-8689.pdf`) | 2020-12-07 | *"Waha Natural Gas (Platts IFERC) Basis Futures"* (ClearPort **NW**, Globex NW) **delisted entirely** — *"There is no open interest in the Contracts."* SER 8000 had already set Dec-2021 as the last listed month. |
| **CME Clearing Advisory 22-008** (`notices/clearing/2022/01/Chadv22-008.pdf`) | effective 2022-01-10 | *"Houston Ship Channel Natural Gas (Platts IFERC) Basis Futures"* (Clearing **NH**, Globex **NHN**) **delisted from CME Globex and CME ClearPort** — *"There is currently no open interest in this product."* |
| cmegroup.com product pages + site search | 2026-08-20 | **No live Waha or HSC product** of any form (basis, swing, index, options). The surviving CME gas slate is the Henry Hub complex, E-mini/Micro, TTF/JKM. The one "Waha basis options" launch release found (code 5O/A5O, "New York trading floor") is the pre-2016 launch of the product the 2017 notice removed — not a relaunch. |

Because A1 fails, A2–A4 are moot — with one aggravating fact recorded for
honesty: even in the contracts' final listed years both carried **zero
open interest**, so archived "daily settlements", were they free, would be
no-trade marks, not transacted prices.

## 3. The B-legs, for the record (unreached; recorded because cheaply determinable)

- **B1 (what the number IS):** confirmed from the contract descriptions —
  a NYMEX basis future is *"monthly cash settled … subtracting the price
  of the NYMEX Henry Hub Natural Gas Futures Contract from the monthly
  price published by Inside FERC for the location specified"*. F1's daily
  settlement is therefore a **forward on a MONTHLY index differential**.
- **B3 (fidelity presumption, standing):** the precommit's default
  presumption is confirmed in kind — a daily mark of a monthly-average
  forward carries expectation revisions, not realized daily cash-basis
  variation, so **even a live F1 could not resolve the ERCOT-147 §3
  confound** (whether a given DAY's CT offer is below that day's true burn
  cost; Waha's 2023 negative DAYS vanish in monthly means). Any future
  forward-market reopen proposal must clear this bar **in addition to**
  existence. F2 (Gas-Daily-settled) would have passed B3 by construction —
  and is exactly the family CME removed in 2017.
- **B2 (rule-13):** not adjudicated (unreached). Noted without deciding:
  a forward basis curve is prima facie forecast-compatible, so if a live,
  free, history-bearing instrument ever appears, B2 is unlikely to be the
  binding leg; B3 is.

## 4. Disposition

**Item 8 STAYS CLOSED, and its closure is now effectively unconditional
pending owner action.** The sole recorded reopen condition is factually
false — there is no free CME/NYMEX route, for the training span or today.
The instrument survives only on paid venues (ICE lists live Waha/HSC basis
futures, e.g. `ice.com/products/6590171/Waha-Basis-Future`) — out of the
precommit's scope and materially the same owner licensing decision already
refused on 2026-08-04. Reopening item 8 now requires one of exactly two
things, both outside this lane's authority: **(a)** a new free daily
Waha/HSC source (none known; the free paths were exhausted by ERCOT-160
and this screen), or **(b)** the owner reversing the no-paid-daily-gas
decision (ICE/NGI/Platts/Argus). No new screen is owed until one of those
happens — the matrix §5.1 item-8 block is re-stamped accordingly so the
condition is never re-litigated from memory (28a discipline).

The ERCOT-160/163 DO-NOT-REDO fences were honoured: no free EIA/ERCOT path
re-screened, no licence re-asked, no Henry Hub substitution, no price
series read (contract SPECS and ACCESS facts only — rule 22 untouched).

## 5. Environment note (transport, not evidence)

Direct `curl` to `www.cmegroup.com` is bot-walled from this environment
(HTTP/2 stream reset; HTTP/1.1 times out). The primary documents were
retrieved 2026-08-20 via the session's fetch route and are quoted in the
probe record; the probe's own best-effort URL re-checks record the
transport state reproducibly and are never load-bearing.

## 6. Queue state after this session

The R-A re-pointed queue's standing items: **item-8 screen — DONE (this
session, negative)**; the **G-SPUR band-top blindness owner gate revision**
(FINDING-ercot214 §5: the [150, 500] band reads phantom adders that
overshoot $500 as *improvements* — h5822-2023 $583 vs actual $145,
h3355-2025 $1,411 vs $135; the revision is to count
`actual < 150 & model ≥ 150` without the upper lid, or report both) remains
the next queue item — owner-decision-card shaped, no solve. Door D
(2026 SOM anchors, ~mid-2027) stands as the recorded floor for the 2023
depth/count object; the adaptive family stays closed.
