Quarter-on-Quarter DST (CFARRI)
Comparison Utility

Business & Process Documentation


1. Purpose

This document explains the Quarter-on-Quarter DST / Transpose file (CFARRI) Comparison Utility in simple, business-friendly language to understand what the utility does and how the output reports should be interpreted.


2. Business Objective

Every quarter, DST lineage files are produced. These files contain transformation logic that drives downstream reporting. This utility compares two quarters of DST files to identify logic changes, newly added records, removed records, and file-level differences. The goal is to provide an accurate, auditable, and easy-to-review comparison.


3. Inputs and Outputs

Inputs

• DST files (Transpose files) from the previous quarter stored in the 'Old' folder

• DST files (Transpose files) from the current quarter stored in the 'New' folder


Outputs

• File_Difference_Report.xlsx showing added and removed files

• Detailed DST comparison Excel report for each common DST file


4. End-to-End Process Flow

The diagram below illustrates the complete flow of how the DST comparison utility works, from reading files to generating the final Excel reports.


                         +-----------+
                         | 1. Start  |
                         +-----------+
                               |
                               v
                 +--------------------------+
                 | 2. Read OLD & NEW       |
                 |    DST Files            |
                 +--------------------------+
                               |
                               v
                 +--------------------------+
                 | 3. File-Level           |
                 |    Difference Check     |
                 +--------------------------+
                               |
                               v
                 +--------------------------+
                 | 4. Remove Fully         |
                 |    Matching Records     |
                 +--------------------------+
                               |
                               v
                 +--------------------------+
                 | 5. Compare Remaining    |
                 |    Records              |
                 +--------------------------+
                               |
                               v
                 +--------------------------+
                 | 6. Classify Changes     |
                 +--------------------------+
                               |
                               v
                 +--------------------------+
                 | 7. Generate Excel       |
                 |    Report               |
                 +--------------------------+


5. Types of Differences Identified

• Transformation Logic Change:
  The same business record exists in both quarters, but one or more transformation rules have changed.

• Newly Added Records:
  Records that exist only in the new quarter and did not exist in the previous quarter.

• Removed Records:
  Records that existed in the previous quarter but are no longer present in the new quarter.


6. Excel Color Coding Explained

The Excel reports generated use color coding to make changes easy to identify:

• Cell colour change:
  When the transformation completely changed between the two quarters then the transformation logic cells are highlighted using cell colour change.

• Font colour change:
  When the transformation logic partially changed between the two quarters then exact portion of logic that changed is highlighted by font colour change to Red Bold text.

• Light Orange Cell:
  Represents the new transformation logic introduced in the current quarter.

• Dark Yellow Cell:
  Represents the old transformation logic from the previous quarter.

• Red Bold Text:
  Highlights the exact portion of logic that changed when only part of a transformation is modified.


7. Final Outcome

The final output is a structured, color-coded, and audit-ready Excel report that clearly shows what changed between quarters. This significantly reduces manual effort, improves accuracy, and enables confident business and audit review.