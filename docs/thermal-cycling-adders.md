# Complete Thermal Cycling Adders — All Resources

Source: NREL/SR-5500-55433 (Kumar et al. 2012) “Power Plant Cycling Costs”
Methodology: startup cost ($/MW × starts/yr ÷ operating hours) + min-run drag (uneconomic hours × margin)
Plant operating profiles: EPA eGRID 2023, ERCOT BA

## Full Adder Table

|Resource     |HR Range   |Start $/MW|Avg Run|Min Run|Startup $/MWh|Drag $/MWh|Total $/MWh|
|-------------|-----------|----------|-------|-------|-------------|----------|-----------|
|**Gas CC**   |           |          |       |       |             |          |           |
|h_class      |<6500      |$63.8     |22 hrs |10 hrs |$2.90        |$1.02     |**$3.92**  |
|f_class      |6500-7500  |$48.6     |17 hrs |7.5 hrs|$2.88        |$0.78     |**$3.66**  |
|older        |7500+      |$24.1     |10 hrs |4.5 hrs|$2.41        |$0.50     |**$2.91**  |
|**Coal**     |           |          |       |       |             |          |           |
|supercritical|<9500      |$147.0    |96 hrs |36 hrs |$1.53        |$1.12     |**$2.66**  |
|subcritical  |9500-10500 |$119.0    |72 hrs |24 hrs |$1.65        |$0.90     |**$2.55**  |
|older        |>10500     |$97.2     |60 hrs |24 hrs |$1.62        |$0.96     |**$2.58**  |
|**Gas CT**   |           |          |       |       |             |          |           |
|aero         |<10000     |$12.3     |4 hrs  |0.5 hrs|$3.09        |$0.05     |**$3.14**  |
|frame        |10000-11000|$24.5     |5 hrs  |1 hr   |$4.90        |$0.12     |**$5.02**  |
|older        |>11000     |$19.0     |4 hrs  |1 hr   |$4.75        |$0.10     |**$4.85**  |

## Key Insights

1. **Coal has the LOWEST per-MWh adder** despite the highest per-start costs — long run cycles (60-96 hrs) amortize the start cost over many MWh.
1. **Gas CTs have the HIGHEST per-MWh adder** despite the lowest per-start costs — very short runs (4-5 hrs) concentrate the start cost into few MWh. Frame CTs at $5.02/MWh are the most expensive cyclers.
1. **Gas CC is in the middle** — moderate start costs, moderate cycle lengths.
1. The CT adder makes CTs MORE expensive in the LP, which worsens the CT under-dispatch. This is physically correct (CTs really do cost this much per MWh of cycling). The LP’s CT under-dispatch is a structural limitation (no integer commitment), not a cost issue.

## NREL Source Details

- NREL/SR-5500-55433: “Power Plant Cycling Costs” (Kumar, Besuner, Lefton, Agan, Hilleman, 2012)
- Table ES-1: Cycling costs by plant type and start type
- Start type mix: estimated from Potomac Economics ERCOT SOM 2023 + engineering judgment
- Average run lengths: OEM specs + eGRID operating hour analysis
- Drag margins: estimated from typical below-MC price spreads during committed hours

## Model Implementation

Add to ScenarioConfig as Tier 3 calibration parameters:

```python
# CC cycling adders ($/MWh) — NREL/SR-5500-55433
cc_cycling_adder_h_class: float = 3.92
cc_cycling_adder_f_class: float = 3.66
cc_cycling_adder_older: float = 2.91

# Coal cycling adders ($/MWh)
coal_cycling_adder_supercritical: float = 2.66
coal_cycling_adder_subcritical: float = 2.55
coal_cycling_adder_older: float = 2.58

# CT cycling adders ($/MWh)
ct_cycling_adder_aero: float = 3.14
ct_cycling_adder_frame: float = 5.02
ct_cycling_adder_older: float = 4.85
```

Applied after `assemble_mc()` by matching generator bin names.