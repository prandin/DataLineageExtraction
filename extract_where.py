import sqlglot
from sqlglot import exp


def extract_where_conditions(sql_query):

    where_conditions = {}
    set_code_value = None

    tree = sqlglot.parse_one(sql_query, dialect="oracle")

    for where in list(tree.find_all(exp.Where)):

        parent = where.parent

        # Only remove WHERE if it belongs to a SELECT
        if not isinstance(parent, exp.Select):
            continue

        condition = where.this

        # Extract equality predicates
        for eq in condition.find_all(exp.EQ):

            left = eq.left.sql()
            right = eq.right.sql()

            where_conditions[left] = right

            if left.lower() == "set_code":
                set_code_value = right.strip("'")

        where.replace(None)

    updated_query = tree.sql(dialect="oracle")

    return where_conditions, updated_query, set_code_value
