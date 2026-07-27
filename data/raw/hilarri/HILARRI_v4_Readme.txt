Hydropower Infrastructure - LAkes, Reservoirs, and RIvers (HILARRI) v4 

Authors:
Hansen, C. H., Matson, P. G, Bozeman, B. B., Turner, S. W. D.


Citation:
Hansen, CH, Matson, PG, Bozeman, BB, Turner, SWD. 2026. Hydropower Infrastructure - LAkes, Reservoirs, and RIvers (HILARRI) v4. HydroSource. Oak Ridge National Laboratory, Oak Ridge, Tennessee, USA. https://doi.org/XXXXXXXXXXXX


File descriptions and user notes:
HILARRI_v4.csv: Complete table with linked identifiers. ***Note: if reading data into programs such as Excel, be aware of formatting issues with the "huc_02" and "huc_12" fields. These fields should have leading zeros to enforce the values are 2 digits and 12 digits, respectively. Data may be read in via the "from text/csv" option to avoid reformatting the field.
HILARRI_v4_Field_Descriptions.csv: Full descriptions of field names, along with units and no data values
HILARRI_v4_Acronyms: Definitions of acronyms used in HILARRI

Abstract: HILARRI is a database of links between major datasets of operational hydropower dams and powerplants, and inland water bodies. These connections are critical for conducting large-scale analysis of hydropower infrastructure and their associated natural and engineered water systems. Features include:
- Dams from the National Inventory of Dams (version published on August 18, 2025) and the Global Reservoir and Dam Database (GRanD v1.3)
- Hydropower plants from the Existing Hydropower Assets dataset (EHA 2025)
These hydropower infrastructure features are linked to several major datasets that provide hydrologic and hydraulic information relevant for analysis of hydropower systems that includes the integral water resources. That information comes from:
-Products from the National Hydrography Dataset (NHD) 
--NHDPlusV2 Medium Resolution river network flowlines, 
--NHD waterbodies (limited to lakes and reservoirs), 
--NHD Watershed Boundary Dataset (HUC12-level for the Conterminous United States (CONUS))
--NHD High Resolution waterbodies
-HydroLAKES water bodies (lakes and reservoirs) 
-LAGOS-US lakes and reservoirs
-EPA National Lakes Assessment (2007, 2012, 2017, and 2022)
-The Reservoir Sedimentation Database (RESSED)
-Sampling locations from the EPA SURGE project (2016-2023)

Unique identifiers are used to facilitate joining with the original full datasets. For example, characteristics of NHD flowlines such as estimated average flow rate can be joined from the NHDPlusV2 dataset to a dam or power plant listed in HILARRI based on the ID field, “COMID”, that is common to both datasets. HILARRI only includes basic information about identifiers, location, and data quality or usage notes. It does not contain the attributes or time series data associated with these sites.
The HILARRI dataset incorporates information from several datasets to facilitate more effective and accurate analysis of hydropower infrastructure and their associated waterbodies. For example, dams were checked against the most recent American Rivers Dam Removal Database to identify and flag facilities that may no longer exist. Additionally, dams that are listed multiple times in the NID are identified and flagged to avoid double-counting when analyzing and summarizing information. Other quality flags include certainty of operational hydropower (i.e., if one or more datasets indicates hydropower at a particular location), whether an associated water body is accurate or composed of multiple polygons, or whether there is a known issue with reported characteristics in one of the underlying datasets. These additional data flags are designed to increase confidence in the data that are joined through the identifiers listed in HILARRI.


Methodology:
HILARRI was created by using spatial joins and fuzzy matching techniques to determine matches between power plants and dams. Additional spatial joins and tabular joins based on common identifiers have been used to link other datasets. Cross-references between datasets describing removal, operational, or development status are also used to categorize the infrastructure into different types. Improvement to coordinates have been made based on OpenStreetMaps or satellite imagery.

Related Datasets:
Megan M. Johnson, Shih-Chieh Kao and Rocio Uría-Martínez. 2025. Existing Hydropower Assets (EHA) Plant Database, 2025. HydroSource. Oak Ridge National Laboratory, Oak Ridge, Tennessee, USA. DOI: 10.21951/EHA_FY2025/2568751

Megan M. Johnson and Rocio Uría-Martínez. 2025. U.S. Hydropower Development Pipeline Data, 2025. HydroSource. Oak Ridge National Laboratory, Oak Ridge, Tennessee, USA. DOI: 10.21951/HMR_PipelineFY25/2563167

Dataset contacts:
Carly Hansen: hansench@ornl.gov
  

Acknowledgement:
Funding and support were provided by the U.S. Department of Energy's (DOE) Water Power Technology Office through Oak Ridge National Laboratory, which is managed by UT-Battelle, LLC