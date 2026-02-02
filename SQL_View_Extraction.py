import sqlglot
from sqlglot import exp

def extract_view_metadata(sql_code):
    parsed = sqlglot.parse_one(sql_code, read="oracle")

    # --- Find CREATE node anywhere in the tree ---
    create_node = parsed.find(exp.Create)
    if not create_node:
        raise ValueError("No CREATE VIEW statement found.")

    # --- 1. Extract View Name and Columns ---
    target = create_node.this

    if isinstance(target, exp.Schema):
        # VIEW name (col1, col2, ...)
        view_name = target.this.sql()
        col_list = [c.name for c in target.expressions]
    else:
        view_name = target.sql()
        col_list = []

    column_dict = {i + 1: col for i, col in enumerate(col_list)}

    # --- 2. Extract SELECT statement ---
    # Everything after AS
    select_stmt = create_node.expression
    if not select_stmt:
        raise ValueError("CREATE VIEW has no AS SELECT clause.")

    select_sql = select_stmt.sql()

    return view_name, column_dict, select_sql
