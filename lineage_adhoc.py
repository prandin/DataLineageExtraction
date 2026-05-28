import json
import re
import sqlparse
import sqlglot

from sqlglot import exp
from sqlglot import parse_one
from sqlglot.generator import Generator
from sqlglot.lineage import lineage
from sqlglot.optimizer import eliminate_ctes


def get_all_column_lineages_legacy_version(
        sql_query: str,
        dialect: "DialectType" = None
):
    ast = parse_one(sql_query, read=dialect)

    column_names_already_found = []

    # print(ast.selects)

    for select in ast.selects:

        if isinstance(select, exp.Func):
            continue

        column_name = select.name

        # print(column_name)

        if column_name in column_names_already_found and select.alias == "":
            table_name = select.table
            select.replace(
                exp.alias_(select, f"{table_name}_{column_name}")
            )

        else:
            column_names_already_found.append(column_name)

    aliased_sql = ast.sql()

    ast = parse_one(aliased_sql, read="oracle")

    generator = Generator(pretty=True)

    qualified_expression = ast

    select_exprs = qualified_expression.find_all(exp.Select)

    column_lineage = []

    index = 1

    for select_expr in select_exprs:

        for column in select_expr.args["expressions"]:

            if "." not in str(column):
                continue

            if isinstance(column, exp.Star):
                continue

            column_name = column.alias_or_name

            # print(column_name)
            # print(column)

            try:
                lineage_node = lineage(
                    column=column_name,
                    sql=qualified_expression,
                    dialect=dialect
                )

                # source_columns = [
                #     generator.generate(node.expression)
                #     for node in lineage_node.walk()
                #     if node.expression != column
                # ]

                source_columns = []
                source_sql = []

                for node in lineage_node.walk():

                    # print(node.expression)

                    if node.expression != column:

                        if node.name not in source_columns:
                            source_columns.append(node.name)

                        node_sql = generator.generate(node.expression)

                        if node_sql not in source_sql:
                            source_sql.append(node_sql)

                # print(source_columns)
                # print(source_sql)

                info_block = {}

                info_block["target_column"] = column_name

                for i in range(len(source_columns)):
                    info_block[f"source_{i}"] = source_columns[i]

                info_block["index"] = str(index)

                column_lineage.append(info_block)

                # print(json.dumps(info_block, indent=4))
                # TODO: This was a main print

                with open("decoding_output.txt", "a") as d_append:
                    d_append.write(json.dumps(info_block, indent=4))
                    d_append.write("\n")
                    d_append.close()

                info_block = {}

                info_block["target_column"] = column_name

                for i in range(len(source_sql)):
                    info_block[f"source_{i}"] = source_sql[i]

                info_block["index"] = str(index)

                column_lineage.append(info_block)

                # print(json.dumps(info_block, indent=4))
                # TODO: This was a main print

                with open("decoding_output.txt", "a") as d_append:
                    d_append.write(json.dumps(info_block, indent=4))
                    d_append.write("\n")
                    d_append.close()

                # list_of_column.append({
                #     "column_name": column_name,
                #     "source_column": source_columns
                # })

            except:
                continue

            # index += 1

    return column_lineage


# def attach_alias():

def handle_func(func):

    for col in func.find_all(exp.Column):

        column_name = col.alias_or_name

        table_name = col.table

        func.replace(
            exp.alias_(func, f"{table_name}_{column_name}")
        )

        break


def handle_column_lineage(
        col,
        qualified_expression,
        generator,
        index,
        column_lineage
):
    column_name = col.alias_or_name

    # print(column_name)

    try:

        lineage_node = lineage(
            column=column_name,
            sql=qualified_expression,
            dialect="oracle"
        )

        source_columns = []
        source_sql = []

        for node in lineage_node.walk():

            # if node.name not in source_columns:

            source_columns.append(node.name)

            node_sql = generator.generate(node.expression)

            # if node_sql not in source_sql:

            source_sql.append(node_sql)

        # print(source_columns)
        # print(source_sql)

        info_block = {}

        info_block["target_column"] = column_name

        for i in range(len(source_columns)):
            info_block[f"source_{i}"] = source_columns[i]

        info_block["index"] = str(index)

        column_lineage.append(info_block)

        # print(json.dumps(info_block, indent=4))
        # TODO: This was a main print

        with open("decoding_output.txt", "a") as d_append:
            d_append.write(json.dumps(info_block, indent=4))
            d_append.write("\n")
            d_append.close()

        info_block = {}

        info_block["target_column"] = column_name

        for i in range(len(source_sql)):
            info_block[f"source_{i}"] = source_sql[i]

        info_block["index"] = str(index)

        column_lineage.append(info_block)

        # print(json.dumps(info_block, indent=4))
        # TODO: This was a main print

        with open("decoding_output.txt", "a") as d_append:
            d_append.write(json.dumps(info_block, indent=4))
            d_append.write("\n")
            d_append.close()

    except Exception as e:

        # print("Error processing column", column_name)
        # print("Error:", e)

        column_lineage.append({
            "column_name": column_name,
            "source_column": source_columns
        })

    return [], index


def handle_function_lineage(
        col,
        qualified_expression,
        generator,
        index,
        column_lineage
):
    print(col)

    for column in col.find_all(exp.Column):

        column_lineage, index = handle_column_lineage(
            column,
            qualified_expression,
            generator,
            index,
            column_lineage
        )

    return column_lineage, index


def handle_function_lineage_union(
        col,
        qualified_expression,
        generator,
        index,
        column_lineage,
        column_extracted
):

    for column in col.find_all(exp.Column):

        if column.alias_or_name not in column_extracted:

            column_lineage, index = handle_column_lineage(
                column,
                qualified_expression,
                generator,
                index,
                column_lineage
            )

            column_extracted.append(column.alias_or_name)

    return column_lineage, index


def handle_union_statements(parsed):

    print(parsed)

    return isinstance(parsed, exp.Union)


def create_lineage(
        qualified_expression,
        generator,
        union_check
):

    column_lineage = []

    print("Extracting lineage")

    select_exprs = qualified_expression.find_all(exp.Select)

    columns_extracted = []

    for select_expr in select_exprs:

        if isinstance(select_expr, exp.Union):
            continue

        for col in select_expr.args["expressions"]:

            column_lineage = []

            if isinstance(col, exp.Column) or isinstance(col, exp.Alias):

                column_lineage, index = handle_column_lineage(
                    col,
                    qualified_expression,
                    generator,
                    index,
                    column_lineage
                )

                columns_extracted = handle_function_lineage_union(
                    col,
                    qualified_expression,
                    generator,
                    index,
                    column_lineage,
                    columns_extracted
                )

            else:

                outermost_select = qualified_expression.find(exp.Select)

                for inner_col in outermost_select.expressions:

                    if isinstance(inner_col, exp.Alias):

                        column_lineage, index = handle_column_lineage(
                            col,
                            qualified_expression,
                            generator,
                            index,
                            column_lineage
                        )

                    if isinstance(col, exp.Func):

                        column_lineage, index = handle_function_lineage(
                            col,
                            qualified_expression,
                            generator,
                            index,
                            column_lineage
                        )

                    if isinstance(col, exp.Paren):

                        col = col.this

                        column_lineage, index = handle_column_lineage(
                            col,
                            qualified_expression,
                            generator,
                            index,
                            column_lineage
                        )

            columns_extracted.append(col.alias_or_name)

            # print("Reached")

    return column_lineage


def find_columns_for_lineage(stmt, column_list):

    for func in stmt.find_all(exp.Func):

        for col in func.find_all(exp.Column):

            if col.alias_or_name not in column_list:
                column_list.append(col.alias_or_name)

    return column_list.append(col.alias_or_name)


def get_all_column_lineages_1(
        sql_query: str,
        dialect: "DialectType" = "oracle"
):

    generator = Generator(pretty=True)

    ast = parse_one(sql_query, read=dialect)

    union_check = handle_union_statements(ast)

    column_names_already_found = []

    for select in ast.selects:

        if isinstance(select, exp.Alias):
            continue

        if isinstance(select, exp.Func):
            handle_func(select)

        if isinstance(select, exp.Literal):

            literal = select.name

            literal = literal.replace("'", "")

            if literal in literal_names:
                literal_names[literal] + 1

            else:
                literal_names[literal] = 1

            select.replace(
                exp.alias_(select, f"literal_{counter}")
            )

            counter += 1

            if isinstance(select, exp.Paren):
                select = select.this

            column_name = select.name

            # print(column_name)

            if (
                    column_name in column_names_already_found
                    and select.alias == ""
            ):

                table_name = select.table

                select.replace(
                    exp.alias_(
                        select,
                        f"{table_name}_{column_name}"
                    )
                )

            else:
                column_names_already_found.append(column_name)

    qualified_expression = ast

    # print(qualified_expression.sql(pretty=True))

    column_lineage = create_lineage(
        qualified_expression,
        generator,
        union_check
    )

    return column_lineage


def replace_text(match):

    return match.group(1)


def remove_parenthesis(sql_query):

    pattern = r"\(([^()\s]+|\([^()\s]*\))*\)"

    result_string = re.sub(
        pattern,
        replace_text,
        sql_query
    )

    return result_string


def remove_comments_old(sql):

    sql_query = []

    in_comment = 0

    i = 0

    while i < len(sql):

        if sql[i:i + 2] == "/*":
            i += 2
            in_comment += 1

        elif sql[i:i + 2] == "*/" and in_comment > 0:
            i += 2
            in_comment -= 1

        elif in_comment:
            i += 1

        else:
            sql_query.append(sql[i])
            i += 1

    # strip characters inside comments

    return ''.join(sql_query).strip()


def remove_sql_comments(sql):

    # Removing single-line comments

    sql_query = re.sub(r'(--[^\n]*)', '', sql)

    print(
        "sql_query after removing comments",
        sql
    )

    while True:

        # multi-line comments

        cleaned = re.sub(
            r'/\*[^*]*+(?:[^/*][^*]*+)*\*/',
            '',
            sql_query,
            flags=re.DOTALL
        )

        if cleaned == sql_query:
            break

        sql_query = cleaned

    # remove any remaining /* or */ delimiters
    # (not part of valid comments)

    sql_query = sql_query.replace('/*', '')

    sql_query = sql_query.replace('*/', '')

    sql_query = re.sub(
        r'\s+',
        ' ',
        sql_query
    ).strip()

    return sql_query


def run_lineage(
        sql_file_name: str,
        input_dir_path: set
):

    # clear previous decoding output

    with open("decoding_output.txt", "w") as d:
        d.write("")
        d.close()

    # sys.stdout = open("decoding_output.txt", "w")

    sql_file_name = "SECURITY_NET_BI_S3.sql"

    print("processing", input_dir_path, sql_file_name)

    with open(
            f"{input_dir_path}/{sql_file_name}",
            "r"
    ) as f:

        sql_query = f.read()

    # sql_query = sql_query.replace(";", "")

    sql_query = sqlparse.format(
        sql_query,
        strip_comments=True
    ).strip().upper()

    # remove multi-line comments

    print(sql_query)

    sql_query = remove_sql_comments(sql_query)

    print(sql_query)

    # sql_query = re.sub(
    #     r".*?(\[.*?\n\s)",
    #     "",
    #     sql_query
    # )

    sql_query = re.sub(
        r"SUBPARTITION\s*\(.*?\)",
        "",
        sql_query,
        flags=re.S
    )

    # TODO: Add this into a preprocessing function

    if "MINUS" in sql_query:
        sql_query = sql_query.replace(
            "MINUS",
            "NOT IN ("
        )

        sql_query = sql_query + ")"

    with open("input.txt", "w") as i:
        i.write(sql_query)

    # Get immediate table and schema

    immediate_schema = None

    try:

        immediate_table = parsed.find(
            sqlglot.expressions.Table
        ).name

        immediate_schema = parsed.find(
            sqlglot.expressions.Table
        ).db

    except:

        print(
            "WARN: No immediate table and schema found."
        )

        sql_query = parsed.sql(pretty=True)

    # print(sql_query)

    parsed = sqlglot.parse_one(sql_query)

    # print(parsed)

    # print(parsed.sql(pretty=True))

    # print("Adding names by adding dummy schema")

    parsed1 = f"{parsed}"

    parsed1 = parsed1.replace(
        "FROM $$",
        "FROM DUMMY_SCHEMA.$$"
    )

    parsed = sqlglot.parse_one(parsed1)

    try:

        immediate_table = parsed.find(
            sqlglot.expressions.Table
        ).name

        immediate_schema = parsed.find(
            sqlglot.expressions.Table
        ).db

    except:

        print(
            "WARN: No immediate table and schema found."
        )

        sql_query = parsed.sql(pretty=True)

    # sql_query = remove_parenthesis(sql_query)

    # column_lineage = get_all_column_lineages_1(sql_query)

    column_lineage = get_all_column_lineages_legacy_version(
        sql_query
    )

    return immediate_schema, immediate_table


# run_lineage("sample.sql", "inputs")