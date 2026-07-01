# Planning Sessions

Each `PS-NN-*.md` is a **self-contained prompt** for a focused decision-making
session. The tool has many open design choices — especially how to price clean
resources and define the premium — and these sessions exist to **capture the
decision and the intent behind it** before code is written.

## How to run a session

1. Open the `PS-NN` prompt in a fresh working session. It states the question,
   the options, the data to look at, and what to decide.
2. Discuss/decide with the stakeholder. Record the reasoning, not just the pick.
3. Write the outcome as a numbered ADR in `../decisions/` (copy
   `../decisions/0000-template.md`) and add it to `../decisions/DECISIONS.md`.
4. The decision then flows into the matching **prompt pack** (`../prompt-packs/`),
   which is the build instruction that implements it.

## Flow

```
PS-NN prompt  →  discussion/decision  →  ADR (decisions/)  →  PP-NN build (prompt-packs/)  →  code
```

## Sessions

| PS | Topic | Feeds |
|---|---|---|
| PS-01 | Resource pricing / LCOE → fixed+VOM | PP-02 |
| PS-02 | Premium definition & excess-resale netting | PP-04, PP-06 |
| PS-03 | Storage costing (power/energy, LDES, H₂) | PP-02 |
| PS-04 | Matching semantics (annual vs 24/7; carbon) | PP-04 |
| PS-05 | Existing-resource treatment & additionality | PP-02 |
| PS-06 | Resource caps & regional potential | PP-02 |
| PS-07 | Load intake & growth | PP-01 |
| PS-08 | LMP coupling & scenario selection | PP-01 |

Run them in any order, but PS-01/PS-02 unblock the most. Nothing here should
require editing `src/market_sim` — this tool stays standalone.
