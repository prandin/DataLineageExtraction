import re
from collections import OrderedDict

def extract_view_metadata(sql_text: str):
    """
    Extracts:
    1. View name
    2. Ordered column dictionary {1: col1, 2: col2, ...}
    3. SELECT statement following AS (verbatim)
    """

    # Normalize line endings but preserve content
    sql = sql_text.strip()

    # -----------------------------
    # 1. Extract VIEW name
    # -----------------------------
    view_name_match = re.search(
        r"""
        CREATE\s+(?:OR\s+REPLACE\s+)?      # CREATE OR REPLACE
        FORCE\s+VIEW\s+                   # FORCE VIEW
        ([A-Za-z0-9_.]+)                  # schema.view_name
        """,
        sql,
        re.IGNORECASE | re.VERBOSE
    )

    if not view_name_match:
        raise ValueError("View name not found")

    view_name = view_name_match.group(1)

    # -----------------------------
    # 2. Extract column list
    # -----------------------------
    column_block_match = re.search(
        r"""
        VIEW\s+[A-Za-z0-9_.]+\s*
        \(
            ([^)]*)
        \)
        """,
        sql,
        re.IGNORECASE | re.VERBOSE | re.DOTALL
    )

    if not column_block_match:
        raise ValueError("Column list not found")

    column_block = column_block_match.group(1)

    columns = [
        col.strip()
        for col in column_block.split(",")
        if col.strip()
    ]

    column_dict = OrderedDict(
        (i + 1, col) for i, col in enumerate(columns)
    )

    # -----------------------------
    # 3. Extract SELECT after AS
    # -----------------------------
    as_match = re.search(
        r"""
        \bAS\b
        (.*)$
        """,
        sql,
        re.IGNORECASE | re.DOTALL | re.VERBOSE
    )

    if not as_match:
        raise ValueError("AS SELECT clause not found")

    select_statement = as_match.group(1).strip()

    return view_name, column_dict, select_statement
