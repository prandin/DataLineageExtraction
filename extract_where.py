import re


def extract_where_conditions(sql_query: str):
    """
    Extracts equality conditions from all WHERE clauses in a SQL query,
    removes the WHERE clauses, and extracts the value of set_code.

    Returns:
        where_conditions (dict)
        updated_query (str)
        set_code_value (str or None)
    """

    where_conditions = {}
    set_code_value = None

    # Regex to capture WHERE clause content
    where_pattern = re.compile(
        r"\bWHERE\b(.*?)(?=\bGROUP\b|\bORDER\b|\bHAVING\b|\bJOIN\b|\bINNER\b|\bLEFT\b|\bRIGHT\b|\bUNION\b|\)|$)",
        re.IGNORECASE | re.DOTALL
    )

    matches = where_pattern.findall(sql_query)

    for clause in matches:

        # split conditions on AND
        conditions = re.split(r"\bAND\b", clause, flags=re.IGNORECASE)

        for cond in conditions:
            cond = cond.strip()

            # equality condition
            m = re.match(r"([\w\.]+)\s*=\s*(['\w\.]+)", cond)

            if m:
                column = m.group(1)
                value = m.group(2)

                where_conditions[column] = value

                if column.lower() == "set_code":
                    set_code_value = value.strip("'")

    # Remove WHERE clauses from query
    updated_query = where_pattern.sub("", sql_query)

    # Clean extra whitespace
    updated_query = re.sub(r"\s+", " ", updated_query).strip()

    return where_conditions, updated_query, set_code_value
