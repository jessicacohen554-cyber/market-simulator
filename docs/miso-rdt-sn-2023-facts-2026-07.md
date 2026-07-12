# MISO RDT South→North 2023 utilization — primary-source facts (re-secured)

**Status:** primary-source-verified research note. **Source of record:** 2023 MISO
State of the Market Report, Potomac Economics (Independent Market Monitor),
`https://www.potomaceconomics.com/wp-content/uploads/2024/06/2023-MISO-SOM_Report_Body-Final.pdf`.

**Why this note exists.** These 2023 figures were originally researched on an
unpushed branch (`claude/miso-rdt-south-north-lane-f0owj2`) that never opened a PR
and is not on the remote, so the work never reached `main`. This note re-secures the
figures from the primary PDF (adversarially verified) so they survive independent of
that session. It is the 2023 analog of the **2024** RDT facts already on `main` in
`src/market_sim/config/constants.py` (the `MISO_RDT_*` block: "utilization averaged
84% of contract when binding in 2024, i.e. ~390 MW below contract"; "92 percent
default derate") and of the FINDING §10 RDT-separation work (PRs #2017/#2043).

## Verified verbatim (2023 MISO SOM, §IV.E "Regional Directional Transfer Flows and Regional Reliability", printed p.39)

1. **Average S→N flow, 2023 ≈ 917 MW.** Verbatim: *"Actual flows on the RDT
   averaged 917 MW in the South to North direction in 2023."* — **CONFIRMED.**
2. **Binding-hour management ≈ 403 MW below the contract limit, 2023.** Verbatim:
   *"The latter involved MISO binding the RDT in real time at an average of 403 MW
   below its contractual limit in 2023."* — **CONFIRMED**, with the direction caveat
   below.
3. **S→N contract limit = 2,500 MW** (stated in the Resource Adequacy section, not
   §IV.E): *"MISO may dispatch up to 2,500 MW of energy transfers from MISO South to
   MISO Midwest."* — **CONFIRMED.**

## Inference (not a report statement — flagged)

- **~2,097 MW / ~84% "S→N when binding"** is an *inference*: 2,500 − 403 = 2,097;
  2,097 / 2,500 = 83.9%. The report does **not** state this. It is presented here
  exactly as the 2024 analog is on `main` — a derived figure, not a quoted one.
- **Direction caveat (adversarial finding, medium-confidence refute of the S→N-only
  pairing):** the §IV.E "403 MW below" sentence says *"its contractual limit"* with
  **no direction attribution**, even though the adjacent 917 MW sentence is explicitly
  labelled S→N. The report documents the RDT binds in **both** directions (§V.B,
  p.51: FTRs over the RDT "can bind in both directions … generate substantial
  surpluses when the RDT binds in the day-ahead market"; §IV.E: high wind drives N→S,
  low wind reverses to S→N). If the 403-below management were N→S instead, the ratio
  is (3,000 − 403)/3,000 = **86.6%**, not 84%. So mapping 403 specifically to the
  2,500 MW S→N limit is an assumption the report itself does not make — treat
  2,097/84% as S→N-conditional, not established.

## Not found in the 2023 report (research item #3 — Midwest↔South price separation)

- **No** Midwest–South energy price-separation ($/MWh) figure and **no** RDT
  shadow-price figure appears in the 2023 body. The only RDT-attributable dollar
  figure is **RSG (revenue sufficiency guarantee) uplift** paid to units managing RDT
  flows — on the order of **$0.8M total** for the year (Midwest + South), i.e. a
  make-whole cost, **not** a congestion price or shadow price. Item #3 is therefore
  unmet from this primary source.

## Corrections / cross-checks vs what's on `main`

- **Section label:** the RDT flows discussion is **§IV.E** (under "IV. ENERGY MARKET
  PERFORMANCE AND OPERATIONS"), **not** §II.E. Printed **p.39** is correct. (The
  constants.py 2024 cite of "§II.E/III.B" is the *2024* report's numbering; the 2023
  report numbers this section IV.E.)
- **"92% default derate" and "84% when binding" language is 2024-only.** Neither
  phrase appears in the 2023 body (the two "84 percent" hits in the 2023 report
  concern RSG payment reductions, unrelated to the RDT). The 2023 report gives the raw
  "403 MW below" figure and the 917 MW S→N average; it does not express utilization as
  a percent-of-contract or cite a default-derate percentage.
- **Consistency with the 2024 fact on `main`:** 2024 = "~390 MW below, 84% when
  binding"; 2023 = "403 MW below" (direction-agnostic). Same order of magnitude for
  the below-contract management; the 84% equivalence holds for 2023 only under the
  S→N-direction assumption.

## One-line summary

2023 MISO SOM (§IV.E, p.39): **S→N RDT flow averaged 917 MW**; **RDT bound ~403 MW
below its contract limit** (direction-agnostic in the report). The **~2,097 MW / ~84%
"S→N when binding"** is an inference (2,500 − 403), consistent with the 2024 analog on
`main` but not stated by the 2023 report; no Midwest–South price-separation/shadow-price
figure exists in the 2023 report.
