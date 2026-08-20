#!/usr/bin/env python3
"""ERCOT-224 — the item-8 CME/NYMEX basis-swap REOPEN SCREEN (Phase-0, no LP).

§5.1 item 8 (daily Texas gas basis for the CT offer-cost object) is CLOSED,
REFUSED ON DATA (owner, 2026-08-04). Its sole recorded reopen condition:
"CME/NYMEX publishes Waha and Houston-Ship-Channel basis-swap daily
settlements publicly at no cost", pending a rule-13 admissibility screen.
`docs/PRECOMMIT-ercot224-item8-cme-screen-2026-08-20.md` pinned the screen
(legs A1-A4 access, B1-B3 admissibility/fidelity, fail-closed verdict rule)
before any CME content was read.

VERDICT THIS PROBE RECORDS: **A1 (existence) FAILS on both hubs and both
in-scope families — item 8 STAYS CLOSED; the reopen condition is factually
FALSE.** CME/NYMEX does not publish, and at no point during the 2023-2025
training span published, Waha or HSC basis-swap daily settlements, because
the contracts do not exist there:

1. Oct-2017 ("Delisting and Removal of Platts Natural Gas Products",
   notices/electronic-trading/2017/10/delplatts.pdf; the SER-8000 track):
   the ENTIRE Platts regional gas complex removed from CME Globex,
   including Waha index IY / swing SY / fixed WFS / basis options A5O and
   HSC index HIP / swing SMN / fixed XJT / basis option 5F.
2. SER-8689 (2020-12-07): "Waha Natural Gas (Platts IFERC) Basis Futures"
   (ClearPort NW / Globex NW) delisted ENTIRELY - "There is no open
   interest in the Contracts." SER 8000 (2017-10-16) had already set
   Dec-2021 as the last listed month.
3. CME Clearing Advisory 22-008 (effective 2022-01-10): "Houston Ship
   Channel Natural Gas (Platts IFERC) Basis Futures" (Clearing NH / Globex
   NHN) delisted from Globex AND ClearPort - "There is currently no open
   interest in this product."
4. No live Waha/HSC gas product exists on cmegroup.com as of 2026-08-20
   (product pages + site searches; the only surviving CME gas products are
   the Henry Hub complex, E-mini/Micro, TTF/JKM).

Because A1 fails, A2-A4 are moot. For the record (precommit §2): B1 is
confirmed from the contract descriptions - a NYMEX basis future is
"monthly cash settled ... subtracting the price of the NYMEX Henry Hub
Natural Gas Futures Contract from the monthly price published by Inside
FERC for the location" - i.e. a forward on a MONTHLY index differential,
so the precommit's B3 default presumption stands: even a live F1 daily
settlement could not resolve the intra-month daily cash-basis variation
the ERCOT-147 §3 confound needs. The only venue with live Waha/HSC basis
daily markets is ICE (e.g. ice.com/products/6590171/Waha-Basis-Future) -
paid data, out of scope, and materially the same owner licensing decision
already refused on 2026-08-04 (NO PAID DAILY GAS DATA).

The adjudication basis is the quoted primary CME documents retrieved
2026-08-20 (the session's fetch route; direct curl to www.cmegroup.com is
bot-walled from this environment). This probe's re-fetch of those documents
is a best-effort transport check recorded for reproducibility - it is NEVER
load-bearing, and a fetch failure does not alter the recorded evidence.

Run:
    python scripts/probes/ercot224_cme_basis_screen.py \
        --out results/calibration/ercot224_cme_basis_screen.json
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
_TIMEOUT_S = 45

# The pinned evidence table: primary CME documents, retrieved 2026-08-20.
EVIDENCE = [
    {
        "leg": "A1",
        "doc": "Delisting and Removal of Platts Natural Gas Products",
        "url": (
            "https://www.cmegroup.com/notices/electronic-trading/2017/10/"
            "delplatts.pdf"
        ),
        "doc_date": "2017-10 (SER-8000 track, dated 2017-10-16 per SER-8689)",
        "retrieved": "2026-08-20",
        "finding": (
            "Entire Platts regional NG complex removed from CME Globex. "
            "Waha rows: 'Waha Natural Gas (Platts Gas Daily/Platts IFERC) "
            "Index Futures' (IY), 'Waha Natural Gas (Platts Gas Daily) Swing "
            "Futures' (SY), 'Waha Natural Gas (Platts IFERC) Fixed Price "
            "Futures' (WFS), 'Waha Texas Basis Swap Options' (A5O). HSC "
            "rows: 'Houston Ship Channel Natural Gas (Platts Gas "
            "Daily/Platts IFERC) Index Futures' (HIP), '... (Platts Gas "
            "Daily) Swing Futures' (SMN), '... (Platts IFERC) Fixed Price "
            "Futures' (XJT), '... (Platts IFERC) Basis Option' (5F)."
        ),
    },
    {
        "leg": "A1",
        "doc": "SER-8689: Delisting of Six (6) Natural Gas (Platts IFERC) "
        "Futures Contracts",
        "url": "https://www.cmegroup.com/notices/ser/2020/12/SER-8689.pdf",
        "doc_date": "2020-12-07",
        "retrieved": "2026-08-20",
        "finding": (
            "Verbatim: 'Effective today, Monday, December 7, 2020, [NYMEX] "
            "delisted six (6) natural gas (Platts IFERC) futures contracts "
            "... There is no open interest in the Contracts.' Row: 'Waha "
            "Natural Gas (Platts IFERC) Basis Futures', rulebook ch. 634, "
            "ClearPort NW, Globex NW. Also: 'The Exchange previously "
            "notified market participants ... (see SER 8000 dated October "
            "16, 2017). At that time, the Exchange advised that December "
            "2021 would be the Contracts' last listed month.'"
        ),
    },
    {
        "leg": "A1",
        "doc": "CME Clearing Advisory 22-008: Delisting of Houston Ship "
        "Channel Natural Gas (Platts IFERC) Basis Futures",
        "url": "https://www.cmegroup.com/notices/clearing/2022/01/Chadv22-008.pdf",
        "doc_date": "2022-01-11 (effective 2022-01-10)",
        "retrieved": "2026-08-20",
        "finding": (
            "Verbatim: 'Effective January 10, 2022, [NYMEX] delisted "
            "Houston Ship Channel Natural Gas (Platts IFERC) Basis Futures "
            "(Clearing Code NH/Globex Code NHN) from CME Globex and CME "
            "ClearPort. There is currently no open interest in this "
            "product.'"
        ),
    },
    {
        "leg": "A1",
        "doc": "SER-6358: Listing of 149 Existing Natural Gas Futures "
        "Contracts on CME Globex (product-code census only)",
        "url": (
            "https://www.cmegroup.com/tools-information/lookups/advisories/"
            "market-regulation/SER-6358.html"
        ),
        "doc_date": "2012 (effective 2012-09-30)",
        "retrieved": "2026-08-20",
        "finding": (
            "Pins the code census this screen adjudicated: Waha basis NW, "
            "index IY, swing SY; HSC basis NH/NHN, index IP/HIP, swing "
            "SM/SMN. Every one of these appears in a later removal/delist "
            "notice above; none has a live cmegroup.com product page as of "
            "2026-08-20."
        ),
    },
    {
        "leg": "B1",
        "doc": "NYMEX basis-futures settlement construction (contract "
        "descriptions, e.g. Barchart JNW* spec text mirroring the NYMEX "
        "rulebook)",
        "url": "https://www.barchart.com/futures/quotes/JNWK20/futures-prices",
        "doc_date": "n/a (spec text)",
        "retrieved": "2026-08-20",
        "finding": (
            "'Basis Futures are monthly cash settled ... based upon the "
            "mathematical result of subtracting the price of the NYMEX "
            "Henry Hub Natural Gas Futures Contract from the monthly price "
            "published by Inside FERC for the location specified.' A "
            "forward on a MONTHLY index differential - the precommit B3 "
            "default presumption stands: a daily settlement of a "
            "monthly-average forward cannot resolve intra-month daily "
            "cash-basis variation (the ERCOT-147 §3 confound object)."
        ),
    },
    {
        "leg": "context",
        "doc": "ICE Waha Basis Future (live venue for the instrument)",
        "url": "https://www.ice.com/products/6590171/Waha-Basis-Future",
        "doc_date": "live listing",
        "retrieved": "2026-08-20",
        "finding": (
            "The surviving Waha/HSC basis daily markets are ICE's - paid "
            "data, out of the precommit's scope, and materially the same "
            "owner licensing decision already refused 2026-08-04 (NO PAID "
            "DAILY GAS DATA)."
        ),
    },
]

VERDICT = {
    "A1_exists": "FAIL - both hubs, both families (F1 basis, F2 swing/index)",
    "A2_current_settlements_free": "MOOT (no product)",
    "A3_history_2023_2025_free": (
        "MOOT (no product listed at any point in 2023-2025; Waha basis "
        "delisted 2020-12-07, HSC basis 2022-01-10, swing/index families "
        "removed 2017-10 - and the final listed years carried ZERO open "
        "interest, so even archived settlements would be no-trade marks)"
    ),
    "A4_licence": "MOOT",
    "B1_instrument_is": (
        "F1 = forward on the MONTHLY Inside-FERC index differential vs the "
        "NYMEX HH last-day settle (recorded; confirms the B3 presumption)"
    ),
    "B2_rule13": "NOT ADJUDICATED (unreached; A1 failed)",
    "B3_fidelity": (
        "NOT ADJUDICATED (unreached); the recorded default presumption - a "
        "monthly-average forward cannot carry realized DAILY cash-basis "
        "variation - stands as the bar any future forward-market reopen "
        "proposal must clear IN ADDITION to existence"
    ),
    "item_8": (
        "STAYS CLOSED - the sole recorded reopen condition is factually "
        "FALSE. Closure is now effectively unconditional pending owner "
        "action: no free CME/NYMEX route exists; the instrument lives only "
        "on paid venues (ICE) already covered by the 2026-08-04 owner "
        "refusal."
    ),
}


def _transport_checks() -> list[dict]:
    """Best-effort re-fetch of the primary documents (never load-bearing).

    Direct requests to www.cmegroup.com are bot-walled from the calibration
    environment (measured 2026-08-20: curl times out / HTTP2 stream reset);
    a failure here is a transport fact, not evidence about the products.
    """
    try:
        import requests  # noqa: PLC0415 - optional, transport check only
    except ImportError:
        return [{"error": "requests unavailable; transport check skipped"}]
    out = []
    for row in EVIDENCE:
        url = row["url"]
        rec: dict = {"url": url}
        try:
            resp = requests.head(url, timeout=_TIMEOUT_S, allow_redirects=True)
            rec["status"] = resp.status_code
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            rec["error"] = f"{type(exc).__name__}: {exc}"
        out.append(rec)
    return out


def main() -> None:
    """Write the screen record (evidence table, verdict, transport checks)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/ercot224_cme_basis_screen.json"),
    )
    ap.add_argument(
        "--skip-transport",
        action="store_true",
        help="skip the best-effort URL re-checks (offline record only)",
    )
    args = ap.parse_args()

    record = {
        "session": "ercot-224",
        "precommit": "docs/PRECOMMIT-ercot224-item8-cme-screen-2026-08-20.md",
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "evidence": EVIDENCE,
        "verdict": VERDICT,
        "transport_checks": (
            [] if args.skip_transport else _transport_checks()
        ),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {out}")
    print(f"item 8: {VERDICT['item_8']}")


if __name__ == "__main__":
    main()
