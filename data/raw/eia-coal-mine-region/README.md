# EIA mine-level coal production (MSHA ID -> Coal Supply Region)

Source: U.S. EIA, annual mine-level coal data behind the *Annual Coal Report*,
<https://www.eia.gov/coal/data.php> ("Coal production and number of mines by
mine", `coalpublic<year>.xls[x]` under
`https://www.eia.gov/coal/data/public/xls/`). Public domain (EIA). Fetched
2026-09-30 by lane PJM-NEXT-13. 2021 and 2022 are SpreadsheetML (XML) despite the
`.xls` suffix; 2019/2020 are BIFF `.xls`; 2023/2024 are `.xlsx`.

Used only for the column pair `MSHA ID` -> `Coal Supply Region` (EIA's own basin
assignment; with `Mine State` + `Mine County` as the fallback key), so each
EIA-923 coal receipt (`Coalmine Msha Id`) is assigned to a supply basin from
EIA's own data rather than a hand-made state list.

| file | sha256 |
|---|---|
| `coalpublic2019.xls` | `c0d98010a1abe683f50df5d722b5a080cb0a6700b55566a2da3632857c0b52ac` |
| `coalpublic2020.xls` | `29e99eb2c0568d4946e0091c23d0a2dccaf285cc7e01f03d8465aa25091c5264` |
| `coalpublic2021.xls` | `f4dcd312df012b9e0ec1080460a0b0ee9d050be8ce99975c724294a2c53f8204` |
| `coalpublic2022.xls` | `24c31586369f880c1f15019fba0862f9b0d0f40c0d860068ff6aa25f87998ce8` |
| `coalpublic2023.xlsx` | `0b0ced83fee51d6e81b828faaee5be628be599c53ab47855475c64eef643a664` |
| `coalpublic2024.xlsx` | `5077a18230eaf009c016423c6cf2a05967b0e4db25432fdb87bd281c3b873a9a` |

Consumer: `scripts/data/derive_pjm_replacement_fuel.py`.
