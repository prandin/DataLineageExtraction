====================================================================
STEP 6 — CONDENSATION / CENTRALIZED REVIEW PROCESS
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step consolidates transpose lineage outputs into a centralized
review template.

The script condenses transformation-level lineage into summarized
business-readable outputs by combining multiple transformation hops
into structured transformation and business translation sections.

The process also filters lineage attributes, reorders hierarchy-based
columns, and prepares governance review templates.

--------------------------------------------------------------------
Main Script
--------------------------------------------------------------------

condensation_v2_latest.py

--------------------------------------------------------------------
Environment Setup
--------------------------------------------------------------------

1. Create virtual environment:

       python -m venv venv

2. Activate environment:

       venv\Scripts\activate

3. Install dependencies:

       pip install -r requirements.txt

--------------------------------------------------------------------
Libraries Used
--------------------------------------------------------------------

• pandas
    DataFrame processing and Excel handling.

• openpyxl
    Excel reading/writing support.

• numpy
    Null and array handling.

• concurrent.futures.ThreadPoolExecutor
    Parallel chunk processing.

• glob
    File discovery and consolidation.

• re
    Transformation/function pattern matching.

--------------------------------------------------------------------
Input Files
--------------------------------------------------------------------

• Consolidated transpose Excel outputs
• AXIOM_DST_List.xlsx
• Transpose lineage files

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

Step_7_Condensation_view
│
├── Transpose
│   └── *_TRANSPOSE_final.xlsx
│
├── output
│   ├── consolidated_transpose.xlsx
│   ├── reordered_consolidated_transpose_PREPROD.xlsx
│   ├── 223_intermediate_output.xlsx
│   ├── extra_df.xlsx
│   └── Centralized_CFARRI_Review_Template_PREPROD.xlsx
│
├── AXIOM_DST_List.xlsx
│
└── condensation_v2_latest.py

--------------------------------------------------------------------
Core Processing Flow
--------------------------------------------------------------------

_TRANSPOSE_final.xlsx Files
            |
            v
Consolidate Transpose Outputs
            |
            v
Reorder Hierarchical Columns
            |
            v
Reorder Translation Columns
            |
            v
Filter Using AXIOM_KEY
            |
            v
Compute Transformation Hops
            |
            v
Condense Transformations
            |
            v
Generate Centralized Review Template

--------------------------------------------------------------------
Major Functionalities
--------------------------------------------------------------------

1. Transpose Consolidation
--------------------------

The script scans the transpose folder and loads all files containing:

    _TRANSPOSE_final

All transpose outputs are merged into a single consolidated
DataFrame.

Generated output:

    consolidated_transpose.xlsx

--------------------------------------------------------------------
2. Column Hierarchy Reordering
--------------------------------------------------------------------

Transformation hierarchy columns are reordered so that child
transformations immediately follow parent transformations.

Example:

    CF_SRC_TGT_TRANSFORMATION_1
    CF_SRC_TGT_TRANSFORMATION_1_A
    CF_SRC_TGT_TRANSFORMATION_1_B

This improves readability and lineage tracing.

--------------------------------------------------------------------
3. Translation Column Reordering
--------------------------------------------------------------------

Transformation translation columns are moved next to their
corresponding transformation columns.

Example:

    CF_SRC_TGT_TRANSFORMATION_1
    CF_SRC_TGT_TRANSFORMATION_TRANSLATIONS_1

--------------------------------------------------------------------
4. AXIOM-Based Filtering
--------------------------------------------------------------------

The script loads:

    AXIOM_DST_List.xlsx

Only lineage records whose:

    CF_FINAL_ATTRIBUTE

matches:

    AXIOM_KEY

are retained for downstream processing.

--------------------------------------------------------------------
5. Hop Detection Logic
--------------------------------------------------------------------

The process dynamically determines:

• Maximum transformation hops
• Hop column counts
• Last populated transformation column

This allows lineage chains of varying lengths to be condensed into a
standardized output structure.

--------------------------------------------------------------------
6. Transformation Condensation
--------------------------------------------------------------------

Transformation columns are condensed into centralized review fields.

Generated fields:

• TRANSFORMATION
• BUSINESS_TRANSLATION

Example output:

    TRANSFORMATION-(1):
        Source-to-target transformation logic

    TRANSLATION-(1):
        Business translation description

Multiple hops are appended sequentially into the same output field.

--------------------------------------------------------------------
7. Parallel Chunk Processing
--------------------------------------------------------------------

The script uses:

    ThreadPoolExecutor

to process row chunks in parallel while computing:

    last_column_which_has_value

This improves performance for large lineage datasets.

--------------------------------------------------------------------
8. Attribute Filtering
--------------------------------------------------------------------

Special filtering is applied for attributes such as:

• LINE_*
• CRR_INSTRUMENT_2
• CRR_INSTRUMENT_2_WIN

These attributes are isolated because they contain unusually large
transformation definitions.

--------------------------------------------------------------------
Important Functions
--------------------------------------------------------------------

find_functions()
    Detects transformation function names.

contains_transformation()
    Validates transformation existence.

add_last_non_empty_column()
    Identifies the last populated lineage column.

find_total_hops()
    Computes maximum hop count.

find_hopl_size()
    Computes hop-level structure size.

get_files()
    Retrieves and sorts transpose files.

reorder_df_by_columns_hierarchy()
    Reorders parent-child transformation columns.

reorder_translation_cols()
    Reorders translation columns.

consolidate_transpose()
    Consolidates transpose Excel outputs.

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place transpose outputs inside:

       Transpose/

2. Ensure:

       AXIOM_DST_List.xlsx

   is available.

3. Update folder paths inside:

       condensation_v2_latest.py

4. Run:

       python condensation_v2_latest.py

5. Review outputs inside:

       output/

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• Consolidated transpose outputs
• Reordered lineage outputs
• Intermediate filtered outputs
• Extra hop-analysis datasets
• Centralized CFARRI review templates
• Condensed transformation summaries

--------------------------------------------------------------------
Final Output
--------------------------------------------------------------------

Centralized_CFARRI_Review_Template_PREPROD.xlsx

This file contains the final condensed lineage review structure
used for governance and conformance review activities.