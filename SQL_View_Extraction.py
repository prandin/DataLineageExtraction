import sqlglot
from sqlglot import exp

def extract_view_metadata(sql_code):
    """
    Parses a CREATE VIEW statement and returns:
    1. The view name
    2. A dictionary of column names {position: name}
    3. The inner SELECT statement
    """
    # Parse the SQL using the Oracle dialect (matches your screenshot)
    parsed = sqlglot.parse_one(sql_code, read="oracle")

    # Ensure this is actually a CREATE statement
    if not isinstance(parsed, exp.Create):
        raise ValueError("The provided SQL is not a CREATE statement.")

    # --- 1. Extract View Name ---
    # In sqlglot, 'this' holds the target of the Create. 
    # If columns are defined, 'this' is a Schema node; otherwise it's a Table/Identifier.
    target_node = parsed.this
    
    if isinstance(target_node, exp.Schema):
        # If explicit columns are present: CREATE VIEW x (cols) ...
        # The view name is inside the Schema's 'this'
        view_name = target_node.this.sql()
        
        # --- 2. Extract Columns (Explicit Definition) ---
        # The columns are listed in the 'expressions' list of the Schema node
        col_list = [e.name for e in target_node.expressions]
        
    else:
        # If no explicit columns: CREATE VIEW x AS ...
        view_name = target_node.sql()
        
        # Fallback: Extract columns from the SELECT statement aliases
        # This is strictly not "the ones in the VIEW query" header, but serves as a backup.
        # Note: This simple fallback might not catch 'SELECT *' expansion.
        col_list = parsed.expression.named_selects

    # Create the dictionary {1: "COL_A", 2: "COL_B", ...}
    column_dict = {i + 1: name for i, name in enumerate(col_list)}

    # --- 3. Extract the Inner Statement ---
    # The 'expression' attribute holds everything after the AS (the query body)
    inner_statement = parsed.expression.sql()

    return view_name, column_dict, inner_statement

try:
    name, cols, stmt = extract_view_metadata(sql_input)
    
    print(f"1. View Name: {name}")
    print(f"2. Columns: {cols}")
    print(f"3. Statement: {stmt}")
    
except Exception as e:
    print(f"Error parsing SQL: {e}")
