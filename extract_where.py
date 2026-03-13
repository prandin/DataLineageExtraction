import sqlglot
from sqlglot import exp


def extract_where_conditions(sql_query):

    where_conditions = {}
    set_code_value = None

    tree = sqlglot.parse_one(sql_query)

    # find all WHERE clauses
    for where in tree.find_all(exp.Where):

        condition = where.this

        # collect equality predicates
        for eq in condition.find_all(exp.EQ):

            left = eq.left.sql()
            right = eq.right.sql()

            where_conditions[left] = right

            if left.lower() == "set_code":
                set_code_value = right.strip("'")

        # remove the WHERE clause safely
        where.replace(None)

    updated_query = tree.sql()

    return where_conditions, updated_query, set_code_value
