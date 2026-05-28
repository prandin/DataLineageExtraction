====================================================================
CONFORMANCE REVIEW AND REMEDIATION
====================================================================

--------------------------------------------------------------------
STEP 0 — HQL PROCESSING
--------------------------------------------------------------------

Purpose
-------
This step processes HQL lineage files and generates intermediate
CSV outputs that will later be used for transpose generation and
final lineage reconciliation.

The processing is executed using:

    lineage_wrapper.py

Outputs are generated in CSV format.

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

Step 1:
    HQL processing using lineage_wrapper.py

Step 2:
    Generate transpose outputs using hive_lineage.py
    with the reference file.

--------------------------------------------------------------------
Input Files
--------------------------------------------------------------------

• HQL source files
• Reference mapping file
• Sample input/output lineage files

Example:
    rdr_companycountrymap.hql.csv

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• Parsed lineage CSV outputs
• Transpose lineage outputs

--------------------------------------------------------------------
Main Scripts
--------------------------------------------------------------------

lineage_wrapper.py
    Parses and processes HQL lineage.

hive_lineage.py
    Generates transpose outputs using the reference file.

====================================================================
STEP 1 — SQL PROCESS
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step extracts lineage information from SQL queries and generates
parsed lineage outputs.

The process supports SQL override queries extracted from Informatica
PowerCenter workflows.

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
Pre-Requisites
--------------------------------------------------------------------

• sqlglot
    Python library used to parse SQL queries.

• Override SQL query
    Extracted from Informatica PowerCenter.

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

SQL_Lineage
│
├── inputs
│   ├── sql_files
│   └── archive
│
├── outputs
│   └── sql_out
│
└── sql_extraction.py   (MAIN FILE)

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place all SQL input files inside:

       inputs/sql_files/

2. Run:

       python sql_extraction.py

3. Parsed lineage outputs will be generated inside:

       outputs/sql_out/

4. Archive prompt will appear after execution.

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• SQL lineage CSV outputs
• Backend lineage extraction files

====================================================================
STEP 2 — XML PROCESS
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step extracts lineage details from Informatica XML workflow and
mapping files.

The extracted lineage is converted into structured outputs for
further transpose and reconciliation processing.

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
Pre-Requisites
--------------------------------------------------------------------

• sqlglot
    Python library to parse SQL queries.

• xml.etree.elementtree
    Python library to parse XML files.

• Override SQL queries
    Extracted from Informatica PowerCenter.

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

XML_Lineage
│
├── inputs
│   ├── DST_Reference_file.xlsx
│   └── xml_files
│       ├── archive
│       ├── workflow XML files
│       └── mapping XML files
│
├── outputs
│   └── xml_out
│       └── backend_files
│
└── xml_extraction.py   (MAIN FILE)

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place XML files inside:

       inputs/xml_files/

2. Place reference file:

       DST_Reference_file.xlsx

3. Run:

       python xml_extraction.py

4. Outputs will be generated inside:

       outputs/xml_out/

5. Archive confirmation prompt will appear after execution.

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• XML lineage outputs
• Backend lineage extraction files
• Workflow-level lineage details
• Mapping-level lineage details

====================================================================
STEP 3 — STORED PROCEDURE (SP) PROCESS
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step extracts lineage information from Oracle Stored Procedures
and generates lineage outputs for reconciliation.

The script parses SQL logic embedded inside stored procedures.

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
Pre-Requisites
--------------------------------------------------------------------

• ddl.json
    Contains database schema details.

• sqlglot
    SQL parsing library.

• config.yaml
    Contains DB paths, definitions and configurations.

• oracledb
    Oracle database connectivity library.

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

SP_lineage
│
├── inputs
│   └── SP files
│
├── outputs
│   └── combined_output
│
├── ddl.json
├── parsing_declare.py
├── config.yaml
├── lineage_adhoc.py
├── lineage_wrapper_adhoc.py
├── new_output_formatting_adhoc.py
│
└── stored_procedure.py   (MAIN FILE)

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place SP files inside:

       inputs/

2. Update ddl.json path inside:

       stored_procedure.py

3. Run:

       python stored_procedure.py

4. Outputs will be generated inside:

       outputs/combined_output/

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• Stored Procedure lineage outputs
• Combined SP lineage files
• Parsed transformation lineage

====================================================================
STEP 4 — DATA MERGE & TRANSPOSE
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step merges lineage outputs generated from SQL, XML and Stored
Procedure processing stages.

The merged lineage is then transposed into a standardized tabular
format for governance and downstream consumption.

--------------------------------------------------------------------
Input Sources
--------------------------------------------------------------------

• SQL lineage outputs
• XML lineage outputs
• Stored Procedure lineage outputs
• FR Y9C Reference file

--------------------------------------------------------------------
Pre-Requisites
--------------------------------------------------------------------

• DST_Reference_file.xlsx
    Contains all DST reference details.

• SQL/XML/SP processed output files

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

CFARRI_combined
│
├── CFARRI_TABULAR (RDBMS)
├── CFARRI_TRANSPOSE (Column)
├── CFARRI_UNMERGED_SP
├── logs
├── sp_input
├── sql_input
└── xml_input

--------------------------------------------------------------------
Execution Flow
--------------------------------------------------------------------

SQL Output
      |
XML Output
      |
SP Output
      |
      v
Data Merge
      |
      v
Transpose Generation
      |
      v
Combined Lineage Output

--------------------------------------------------------------------
Code Configuration
--------------------------------------------------------------------

Update folder paths in:

    main.py

Example:

    sql_folder_path
    xml_folder_path
    sp_folder_path
    output_path

--------------------------------------------------------------------
Additional Configuration
--------------------------------------------------------------------

Inside:

    dynamic_merge.py

Update:

    Line 342
        Configure transpose output path.

    Line 224
        Configure transpose output with
        7-column transpose structure.

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place SQL/XML/SP outputs into their respective folders.

2. Update paths inside:

       main.py

3. Execute:

       python main.py

4. Transpose and merged outputs will be generated automatically.

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• Merged lineage datasets
• Standardized transpose outputs
• Reduced-column transpose outputs
• Governance-ready lineage outputs

====================================================================
STEP 4A — HQL TRANSPOSE PROCESS
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step generates transpose lineage outputs specifically for HQL
lineage generated in Step 0.

The processing logic is similar to SQL/XML transpose generation and
produces governance-ready transpose lineage structures.

--------------------------------------------------------------------
Input Sources
--------------------------------------------------------------------

• HQL lineage CSV outputs generated in Step 0
• Reference mapping files

--------------------------------------------------------------------
Execution Flow
--------------------------------------------------------------------

HQL Lineage Output
        |
        v
Transpose Generation
        |
        v
Standardized HQL Transpose Output

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• HQL transpose lineage files
• Standardized transpose mappings
• Governance-ready lineage structures

====================================================================
STEP 5 — FINAL COMPARISON / REPORTING LAYER
====================================================================

--------------------------------------------------------------------
Purpose
--------------------------------------------------------------------

This step performs the final merge between AXIOM lineage outputs and
the CFARRI transpose lineage generated from earlier stages.

The process validates mappings, identifies unmatched lineage columns,
reorders hierarchical transformation columns, and generates large-scale
Excel reports.

This acts as the final reconciliation and reporting layer for the
complete lineage framework.

--------------------------------------------------------------------
Main Functionalities
--------------------------------------------------------------------

• Merge AXIOM lineage with CFARRI transpose outputs
• Generate combined lineage reports
• Identify unmatched lineage mappings
• Produce error logs
• Reorder hierarchical transformation columns
• Generate large-scale Excel outputs
• Split outputs exceeding Excel row limits
• Execute merges in parallel using multithreading

--------------------------------------------------------------------
Execution Flow
--------------------------------------------------------------------

AXIOM Files (.csv / .xlsx)
            |
            v
Read AXIOM Data
            |
            v
Generate AXIOM_KEY
            |
            v
Group by AX_DST
            |
            v
Parallel Merge Processing
(ThreadPoolExecutor)
            |
            v
Merge with CFARRI Transpose Outputs
            |
            v
Generate Error Logs
            |
            v
Reorder Transformation Columns
            |
            v
Split Large Outputs into Excel Chunks
            |
            v
Generate Final Combined Reports

--------------------------------------------------------------------
Folder Structure
--------------------------------------------------------------------

project_root
│
├── axiom
│   └── UAT
│       ├── CSV lineage files
│       └── XLSX lineage files
│
├── cfarri
│   └── UAT
│       └── transpose lineage outputs
│
├── combined
│   └── UAT
│       └── final combined reports
│
├── error_log
│   └── UAT
│       └── lineage error logs
│
└── full_lineage_optimized_v1.py

--------------------------------------------------------------------
Core Processing Logic
--------------------------------------------------------------------

1. AXIOM File Processing
------------------------

The script reads AXIOM lineage files from:

    axiom/UAT/

Supported formats:

• CSV
• XLSX

A lineage comparison key is generated:

    AXIOM_KEY =
        AX_DST + "." + AX_FINAL_ATTRIBUTE

--------------------------------------------------------------------
2. CFARRI Merge Processing
--------------------------------------------------------------------

The script groups lineage records by destination:

    AX_DST

Each group is merged against corresponding transpose lineage outputs
using:

    AXIOM_KEY = CR_FINAL_ATTRIBUTE

Missing lineage mappings are captured into error logs.

--------------------------------------------------------------------
3. Parallel Processing
--------------------------------------------------------------------

The script uses:

    ThreadPoolExecutor

to process multiple destination groups concurrently, improving
performance for large-scale lineage reconciliation.

--------------------------------------------------------------------
4. Column Hierarchy Reordering
--------------------------------------------------------------------

Transformation hierarchy columns are reordered so that child columns
immediately follow their parent columns.

Example:

Parent:
    CF_SRC_TGT_TRANSFORMATION_1

Children:
    CF_SRC_TGT_TRANSFORMATION_1_A
    CF_SRC_TGT_TRANSFORMATION_1_B

This improves readability and preserves lineage hierarchy.

--------------------------------------------------------------------
5. Large Excel Output Handling
--------------------------------------------------------------------

The process includes utilities for:

• Splitting large outputs into multiple Excel files
• Supporting ZIP64 Excel generation
• Writing data in batches
• Handling outputs larger than Excel row limitations
• Reducing memory consumption

--------------------------------------------------------------------
Important Functions
--------------------------------------------------------------------

process_dst_group()
    Performs merge processing for individual destination groups.

merge_cfarri_axiom()
    Executes threaded merge operations.

reorder_df_by_columns_hierarchy()
    Reorders hierarchical lineage columns.

create_large_excel_file2()
    Generates large Excel reports.

split_df_to_xlsx_chunks()
    Splits massive datasets into multiple Excel files.

--------------------------------------------------------------------
Output Files
--------------------------------------------------------------------

Combined reports:

    COMBINED_<source_file>.xlsx

Error logs:

    <source_file>_error_log.txt

--------------------------------------------------------------------
Execution Steps
--------------------------------------------------------------------

1. Place AXIOM lineage files inside:

       axiom/UAT/

2. Ensure transpose outputs are available inside:

       cfarri/UAT/

3. Execute:

       python full_lineage_optimized_v1.py

4. Combined reports will be generated inside:

       combined/UAT/

5. Error logs will be generated inside:

       error_log/UAT/

--------------------------------------------------------------------
Generated Outputs
--------------------------------------------------------------------

• Final combined lineage reports
• AXIOM-to-CFARRI reconciliation outputs
• Missing lineage mapping reports
• Large-scale Excel exports
• Hierarchically ordered lineage outputs