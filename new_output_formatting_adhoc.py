import json
import re
import pandas as pd
import sqlglot

from sqlglot.expressions import Alias, Column, Case
from sqlglot import expressions

glob_file_name = ""


################## Global Variables ##################

SUPPORTED_TRANSFORMATIONS = (
    expressions.Round,
    expressions.Trim,
    expressions.Sum,
    expressions.Max,
    expressions.Cast,
    expressions.Mul,
    expressions.Add,
    expressions.Sub,
    expressions.Div,
    expressions.Sum
)

################## Global Variables End ##################

# Read the DDL file

# with open("inputs/DDL_Matt_SQL.json", "r") as ddl_file:

with open(
    r"C:\Users\ZKYGBl5\PycharmProjects\Lineage_Generation\Shareable_CFARRI_Codes\Step_3_SP_Lineage\_ddl.json",
    "r"
) as ddl_file:

    ddl = json.load(ddl_file)


def _check_schema_in_DDL(schema_name):

    for k, v in ddl.items():

        if k.lower() == schema_name.lower():

            return k, v

    return None, None


def _check_col_in_table(col_name, schema_obj, table_name):

    # print(
    #     f"_check_col_in_table for: col_name, schema_obj, table_name:\n",
    #     col_name,
    #     schema_obj,
    #     table_name
    # )

    col_obj_list = None

    schema_obj = dict()

    for k, v in schema_obj.items():

        if k.lower() == table_name.lower():

            col_obj_list = v

    if not col_obj_list:

        return None, None

    for col_obj in col_obj_list:

        if col_obj['column_name'].lower() == col_name.lower():

            # Updating this part to handle Matt's SQL Queries
            # and the non-existent tables in DDL JSON

            return col_obj['column_name'], col_obj['data_type']

    # return col_name, None

    return None, None


def _get_source_schema_and_datatype(df_dict):

    # Iterate over each row

    for i in range(len(df_dict['target_column'])):

        schema_name = df_dict['table_name_or_alias'][i]

        table_name = df_dict['column_name_or_alias'][i]

        if schema_name:

            # Check if schema is present

            # Changing this part to accommodate
            # for Matt's SQL query different tables

            sch_present, sch_obj = _check_schema_in_DDL(schema_name)

            # sch_present, sch_obj = None, None

            if schema_name:

                df_dict['source_schema'][i] = schema_name

                df_dict['table_name_or_alias'][i] = table_name

                # Identify column name

                child_node_number = df_dict['parent_node'][i]

                while child_node_number != 'output':

                    # Get child's column name

                    child_col_name = df_dict['column_name_or_alias'][
                        child_node_number - 1
                    ]

                    col_present, datatype = _check_col_in_table(
                        child_col_name,
                        sch_obj,
                        table_name
                    )

                    if not col_present:

                        # Go to the next child

                        old_child_node_number = child_node_number

                        child_node_number = df_dict['parent_node'][
                            child_node_number
                        ]

                        # continue

                        if old_child_node_number == child_node_number:

                            break

                        else:

                            continue

                    else:

                        df_dict['datatype'][i] = datatype

                        df_dict['column_name_or_alias'][i] = col_present

                        break

        elif schema_name == 'dummy_schema':

            # print(schema_name)

            df_dict['source_schema'][i] = ""

            df_dict['table_name_or_alias'][i] = table_name

            df_dict['column_name_or_alias'][i] = \
                df_dict['TGT_column'][i]

    return df_dict


def _get_parent_node_number(df_dict):

    # Get the length of df_dict

    df_dict_len = len(df_dict['target_column'])

    # Identify the starting index

    start_idx = 0

    for idx in range(df_dict_len):

        if 'CASE' in df_dict['transformation'][idx]:

            continue

        else:

            start_idx = idx

            break

    # Logic to find child node

    for i in range(start_idx, df_dict_len):

        parent_alias_or_name = sqlglot.parse_one(
            df_dict['transformation'][i]
        ).alias_or_name

        # Iterate over next-generation nodes

        for j in range(i):

            child_column = df_dict['column_name_or_alias'][j]

            child_table = df_dict['table_name_or_alias'][j]

            child_node_number = df_dict['node_number'][j]

            # Compare parent alias with child table
            # and column name (in that order)

            if child_table and \
                    parent_alias_or_name.lower() == child_table.lower():

                df_dict['parent_node'][i] = child_node_number

                df_dict['TGT_column'][i] = child_column

                df_dict['TGT_table'][i] = child_table

                df_dict['has_child'][i] = 'Y'

                continue

            elif child_column and \
                    parent_alias_or_name.lower() == child_column.lower():

                df_dict['parent_node'][i] = child_node_number

                df_dict['TGT_column'][i] = child_column

                df_dict['TGT_table'][i] = child_table

                df_dict['has_child'][i] = 'Y'

                continue

            else:

                continue

    return df_dict


def _convert_string_to_JSON(input_file_content, input_dict, start_line):

    for line in input_file_content[start_line:]:

        if line == "{\n":

            json_obj_str = "{"

            json_content = []

        elif line == "}\n":

            json_obj_str += ",".join(json_content)

            json_obj_str += "}"

            input_dict['column_lineage'].append(
                json.loads(json_obj_str)
            )

        else:

            json_content.append(line.replace("\n", ""))

    return input_dict


def format_output(file_name, start_line=0, metadata=None):

    file_name = file_name.split(".sql")[0].upper()

    global glob_file_name

    schema_tables = []

    for schema, tables in ddl.items():

        for table in tables.keys():

            schema_table = f"{schema}.{table}"

            schema_tables.append(schema_table)

    for i in schema_tables:

        if file_name == i.replace(".", "_"):

            file_name = i

            glob_file_name = file_name

        # else:
        #     file_name = ""
        #     glob_file_name = file_name

    print(glob_file_name)

    print("INFO: Starting output formatting")

    # Read intermediate output

    try:

        with open("decoding_output.txt", "r") as f:

            input_file_content = f.readlines()

    except Exception as e:

        print(
            f"ERROR: Error while reading input for output formatting.\n"
            f"Details: {e}"
        )

        return None

    # Preprocess input

    input_dict = {
        'column_lineage': []
    }

    input_dict = _convert_string_to_JSON(
        input_file_content,
        input_dict,
        start_line
    )

    with open("test.json", "w") as t:

        json.dump(input_dict, t)

    # Preparing output dataframe

    # this below code is to map sequence number to target table value

    # seq_mapping_list = create_sequence_mapping_list(input_dict)

    # _prepare_output_df(input_dict, metadata, seq_mapping_list)

    _prepare_output_df(input_dict, metadata)


def _add_to_df_dict(
        df_dict,
        target_column,
        node_number,
        column_name_or_alias,
        table_name_or_alias,
        transformation,
        source_schema=None,
        TGT_table='XMI',
        source='SP',
        has_child='N',
        parent_node='output',
        datatype=None,
        index=None
):

    global glob_file_name

    df_dict['target_column'].append(target_column)

    df_dict['node_number'].append(node_number)

    df_dict['column_name_or_alias'].append(column_name_or_alias)

    df_dict['source_schema'].append(source_schema)

    df_dict['table_name_or_alias'].append(table_name_or_alias)

    df_dict['transformation'].append(transformation)

    df_dict['TGT_column'].append(target_column)

    df_dict['TGT_table'].append(glob_file_name)

    df_dict['source'].append(source)

    df_dict['has_child'].append(has_child)

    df_dict['parent_node'].append(parent_node)

    df_dict['datatype'].append(datatype)

    df_dict['index'].append(index)

    return df_dict


# Method to preprocess lineage object

def _preprocess_lineage_object(lin_obj):

    new_order = []


def _log_unhandled_expressions(exp, metadata):

    with open("error_logs.txt", "a") as err:

        err.write(
            f"{metadata['file_name']} | [ERR_5] | "
            f"new_output_formatting.py -- line 203 | "
            f"Cannot handle the expression: {exp}"
        )

        err.close()


def _preprocess_lineage_dict(lin_dict):

    new_lin_dict = {}

    schema_list = []

    source_no = 0

    for k, v in lin_dict.items():

        if k == 'target_column' or k == 'index':

            new_lin_dict[k] = v

        else:

            if v.startswith('crr') or \
                    v.startswith('lookup') or \
                    v.startswith('crr_staging'):

                schema_list.append(v)

                continue

            else:

                # print(v, "\n", v)

                # print("new_lin_dict")

                # print(new_lin_dict[f"source_{str(source_no)}"])

                new_lin_dict[f"source_{str(source_no)}"] = v

                source_no += 1

                continue

    if len(schema_list) > 0:

        for it in schema_list:

            new_lin_dict[f"source_{str(source_no)}"] = it

            source_no += 1

    return new_lin_dict


def _prepare_output_df(it_json, metadata):

    op_df = pd.DataFrame(
        columns=[
            'target_column',
            'node_number',
            'parent_node',
            'has_child',
            'source_schema',
            'table_name_or_alias',
            'column_name_or_alias',
            'datatype',
            'transformation',
            'TGT_table',
            'TGT_column',
            'source',
            'index'
        ]
    )

    for i in range(len(it_json['column_lineage'])):

        if i % 2 != 0:

            # Odd index

            tran_lin_obj = it_json['column_lineage'][i]

            # Preprocess lineage JSON

            tran_lin_obj = _preprocess_lineage_dict(tran_lin_obj)

            # Extract target column

            target_column = tran_lin_obj['target_column']

            # Extract index for the target column

            index = tran_lin_obj['index']

            # Initialization of df_dict

            df_dict = {
                'target_column': [],
                'datatype': [],
                'node_number': [],
                'parent_node': [],
                'column_name_or_alias': [],
                'table_name_or_alias': [],
                'transformation': [],
                'source_schema': [],
                'TGT_column': [],
                'TGT_table': [],
                'has_child': [],
                'source': [],
                'index': []
            }

            # Iterate over each source

            c = 0

            node_number = 1

            for k, v in tran_lin_obj.items():

                # Skip the target column

                if k != 'target_column' and k != 'index':

                    try:

                        # Parse as AST

                        # print(f"Trying to parse expression:\n{v}")

                        exp = sqlglot.parse_one(v)

                        # print("Expression parsed successfully")

                    except Exception as e:

                        print(
                            f"ERROR: Error in parsing as AST.\n"
                            f"The expression that failed: {v}\n"
                            f"Details: {e}"
                        )

                        with open("error_logs.txt", "a") as error_logs:

                            error_logs.write(
                                f"new_output_formatting.py -- line 265 "
                                f"| [ERR_1] | Error in parsing as AST. "
                                f"| Details: {e}"
                            )

                            error_logs.close()

                        return 0

                    # Handle expressions

                    try:

                        # Simple Column expressions

                        if isinstance(exp.args['this'], Column):

                            # Simple column with alias

                            df_dict = _add_to_df_dict(
                                df_dict=df_dict,
                                target_column=target_column,
                                node_number=node_number,
                                column_name_or_alias=exp.args['this'].name,
                                table_name_or_alias=exp.args['this'].table,
                                transformation=v,
                                index=index
                            )

                            node_number += 1

                        # Case statements

                        elif isinstance(exp.args['this'], Case):

                            # Case statement

                            df_dict, node_number = _handle_case_statements(
                                exp,
                                df_dict,
                                v,
                                node_number,
                                target_column,
                                index
                            )

                            continue

                        # Coalesce

                        elif isinstance(
                                exp.args['this'],
                                expressions.Coalesce
                        ):

                            # Handle coalesce

                            df_dict, node_number = \
                                _handle_coalesce_statements(
                                    exp.args['this'],
                                    df_dict,
                                    v,
                                    node_number,
                                    target_column,
                                    index
                                )

                        # Aliases

                        elif isinstance(exp, expressions.Alias):

                            # Hard coded literals

                            if isinstance(
                                    exp.args['this'],
                                    expressions.Literal
                            ):

                                df_dict = _handle_literals_with_alias(
                                    exp,
                                    node_number,
                                    df_dict,
                                    target_column,
                                    v,
                                    index
                                )

                                node_number += 1

                                continue

                        # "NULL AS <COLUMN>"

                        elif isinstance(exp.args['this'], expressions.Null):

                            df_dict = _handle_literals_with_alias(
                                exp,
                                node_number,
                                df_dict,
                                target_column,
                                v,
                                index
                            )

                            node_number += 1

                            continue

                        # Simple Transformations

                        elif isinstance(
                                exp.args['this'],
                                SUPPORTED_TRANSFORMATIONS
                        ):

                            all_columns = [
                                (col.alias_or_name, col.table)
                                for col in exp.args['this'].find_all(
                                    expressions.Column
                                )
                            ]

                            for source in all_columns:

                                df_dict = _add_to_df_dict(
                                    df_dict=df_dict,
                                    target_column=target_column,
                                    node_number=node_number,
                                    column_name_or_alias=source[0],
                                    table_name_or_alias=source[1],
                                    transformation=v,
                                    index=index
                                )

                                node_number += 1

                        # Transformation

                        elif isinstance(exp, SUPPORTED_TRANSFORMATIONS):

                            df_dict = _add_to_df_dict(
                                df_dict=df_dict,
                                target_column=target_column,
                                node_number=node_number,
                                column_name_or_alias=exp.args['this'].name,
                                table_name_or_alias=exp.args['this'].table,
                                transformation=v,
                                index=index
                            )

                            node_number += 1

                        # Unhandled expression

                        else:

                            with open("error_logs.txt", "a") as error_logs:

                                error_logs.write(
                                    f"\n{metadata['file_name']} "
                                    f"| [ERR_5] | "
                                    f"new_output_formatting.py -- line 294 "
                                    f"| Unhandled expression: {v} "
                                    f"| Details: {e}"
                                )

                                error_logs.close()

                            continue

                    except Exception as e:

                        print(f"Exception as {exp}")

                        with open("error_logs.txt", "a") as err_logs:

                            err_logs.write(
                                f"\n{metadata['file_name']} "
                                f"| [ERR_3] | "
                                f"new_output_formatting.py -- line 267 "
                                f"| ERROR in handling the expression: {v} "
                                f"| Details: {e}"
                            )

                            err_logs.close()

                            continue

            # Add child node number

            df_dict = _get_parent_node_number(df_dict)

            # Get source and datatype

            df_dict = _get_source_schema_and_datatype(df_dict)

            # Reverse the order

            new_df = pd.DataFrame(df_dict).iloc[::-1].reset_index(drop=True)

            if len(df_dict['target_column']) > 0:

                op_df = pd.concat(
                    [op_df, new_df],
                    ignore_index=True
                )

    # Post-processing

    # op_df.drop_duplicates(inplace=True, keep='first')

    # print(
    #     "op_df:\n",
    #     op_df[op_df['target_column'].str.upper() == 'LOAD_ID']
    # )

    # Add static columns

    op_df['SQL file name'] = metadata['file_name']

    op_df['DST_NAME'] = metadata['DST_name']

    op_df['SET_CODE'] = metadata['set_code']

    op_df['SESSION_NAME'] = metadata['session_name']

    # Reorder node number and feeds into column

    op_df.to_csv('inter.csv')  # TODO: Delete this line

    op_df = _reorder_node_numbers(op_df)

    # Applying mapping of sequence numbers

    # op_df = map_seq_to_final_target(op_df, seq_mapping_list)

    # Postprocess dataframe

    op_df = _postprocess(op_df, metadata)

    # Write to CSV file

    # print(metadata['output_csv_name'])

    op_df = op_df.drop(columns=['SQL INDEX'])

    op_df.to_csv('inter.csv')  # TODO: Delete this line

    sp_col_order = [
        'FINAL_TARGET',
        'NODE_NUMBER',
        'CHILD_NODE',
        'HAS_CHILD',
        'SOURCE_SCHEMA',
        'SRC_TABLE',
        'SRC_COLUMN',
        'SRC_DATA_TYPE',
        'SRC_TGT_TRANSFORMATION',
        'TGT_TABLE',
        'TGT_COLUMN',
        'TGT_DATA_TYPE',
        'LINEAGE_SRC',
        'FILE_NAME',
        'DST_NAME',
        'SET_CODE',
        'SESSION_NAME'
    ]

    op_df = op_df[sp_col_order]

    op_df.to_csv(metadata['output_csv_name'], index=False)

    op_df.to_excel(metadata['output_excel_name'], index=False)


def _handle_literals_with_alias(
        exp: expressions.Alias,
        node_number,
        df_dict,
        target_column,
        transformation,
        index
):

    alias = exp.alias

    df_dict = _add_to_df_dict(
        df_dict=df_dict,
        target_column=target_column,
        node_number=node_number,
        column_name_or_alias=alias,
        table_name_or_alias=None,
        transformation=transformation,
        index=index
    )

    return df_dict


def _get_datatype(schema, table, column, ddl_json):

    for schema_name, sch_obj in ddl_json.items():

        if schema.lower() == schema_name.lower():

            for table_name, t_obj in ddl_json[schema_name].items():

                if table.lower() == table_name.lower():

                    for col_obj in t_obj:

                        if col_obj['column_name'].lower() == column.lower():

                            return col_obj['data_type']


def _postprocess(df, metadata):

    # print(metadata)

    # Add dummy TGT_DATA_TYPE column

    df['TGT_DATA_TYPE'] = None

    # Update column names

    df = _update_column_names(df)

    # Replace 'output' in child node column with None

    df.loc[df['CHILD_NODE'] == 'output', 'CHILD_NODE'] = None

    return df


def _update_column_names(df):

    new_column_map = {
        'target_column': 'FINAL_TARGET',
        'node_number': 'NODE_NUMBER',
        'parent_node': 'CHILD_NODE',
        'has_child': 'HAS_CHILD',
        'source_schema': 'SOURCE_SCHEMA',
        'table_name_or_alias': 'SRC_TABLE',
        'column_name_or_alias': 'SRC_COLUMN',
        'datatype': 'SRC_DATA_TYPE',
        'transformation': 'SRC_TGT_TRANSFORMATION',
        'TGT_table': 'TGT_TABLE',
        'TGT_column': 'TGT_COLUMN',
        'TGT_DATA_TYPE': 'TGT_DATA_TYPE',
        'source': 'LINEAGE_SRC',
        'SQL file name': 'FILE_NAME',
        'index': 'SQL_INDEX'
    }

    df = df.rename(columns=new_column_map)

    return df


def _update_feeds_into_col(target_col, node_num_map, df):

    for idx, row in df[df['target_column'] == target_col].iterrows():

        if row['parent_node'] != 'output':

            df.loc[idx, 'parent_node'] = \
                node_num_map[row['parent_node']]

    return df


def _handle_transformations():

    pass


def _reorder_node_numbers(df):

    # Get distinct target columns

    distinct_target_cols = df['index'].unique().tolist()

    for target_col in distinct_target_cols:

        # print("target_col:\n", target_col)

        # Get rows associated with the target column

        asso_rows = df.loc[df['index'] == target_col]

        if len(asso_rows) <= 1:

            continue

        # Get old node numbers

        old_node_nums = asso_rows['node_number'].tolist()

        # Get old feeds into

        old_feeds_into = asso_rows['parent_node'].tolist()

        # New node numbers

        new_node_nums = list(reversed(old_node_nums))

        new_node_map = {}

        for i in range(len(new_node_nums)):

            new_node_map[old_node_nums[i]] = new_node_nums[i]

            # Key = old node no. | val = new node no.

        # Update node nums

        df.loc[df['index'] == target_col, 'node_number'] = new_node_nums

        # Update feeds into column

        new_feeds_into = []

        for o in old_feeds_into:

            if o != 'output':

                new_feeds_into.append(new_node_map[o])

            else:

                new_feeds_into.append('output')

        # print(new_feeds_into)

        df.loc[df['index'] == target_col, 'parent_node'] = \
            new_feeds_into

    return df


def _handle_source_column_and_table_names(df_dict):

    # get the last three key-value pairs ("last hop") as a list of tuples

    last_hop = list(df_dict.items())[-3:]

    second_last_hop = list(df_dict.items())[-6:-3]

    # print(second_last_hop)

    try:

        table_name = last_hop[0][1]

        schema_name = last_hop[2][1]

        source_col_name = second_last_hop[0][1]

        # Get the data type for the table

        data_type = _get_data_type_for_col(
            col_name=source_col_name[0],
            table_name=table_name[0],
            schema_name=schema_name[0]
        )

        if not data_type:

            return df_dict

        new_df_dict = {
            'target_column': df_dict['target_column'],
            'source_schema': schema_name,
            'table_name_or_alias': table_name,
            'column_name_or_alias': source_col_name,
            'source_col_datatype': [data_type]
        }

        for li in list(df_dict.items())[:-3]:

            if li[0] == 'target_column':

                continue

            else:

                new_df_dict[li[0]] = li[1]

    except Exception as e:

        print(e)

        return df_dict

    return new_df_dict


def _get_data_type_for_col(col_name, table_name, schema_name):

    # Get the data type for the col

    schema_map = ddl[schema_name.upper()]

    table_map = schema_map[table_name.upper()]

    data_type = None

    for col_obj in table_map:

        if col_obj['column_name'].upper() == col_name.upper():

            data_type = col_obj['data_type']

            break

    # print(schema_name, table_name, col_name, data_type)

    return data_type


def _process_df_dict(df_dict):

    try:

        new_df_dict = {
            'target_column': df_dict['target_column']
        }

    except Exception as e:

        print(f"ERROR: {e}")

        return df_dict

    # Get the length of the dictionary

    dict_len = len(df_dict)

    # calculate the number of hops in the dictionary

    num_hops = (dict_len - 1) / 3

    i = 0

    while i < num_hops:

        column_list = df_dict[f"column_{str(i)}"]

        trns_list = df_dict[f"transformation_{str(i)}"]

        table_alias_list = df_dict[f"table_alias_{str(i)}"]

        if trns_list[0].startswith("CASE"):

            # Get the number of dependent columns

            num_dep_cols = len(column_list)

            # Duplicate rows before this hop

            for k in new_df_dict.keys():

                new_df_dict[k] = new_df_dict[k] * num_dep_cols

            # Add data for the current hop

            new_df_dict[f"column_{str(i)}"] = column_list

            new_df_dict[f"transformation_{str(i)}"] = \
                trns_list * num_dep_cols

            new_df_dict[f"table_alias_{str(i)}"] = table_alias_list

            # Add dependent column source

            for table_alias in table_alias_list:

                j = i + 1

                while j < num_hops:

                    if table_alias in df_dict[f"table_alias_{j}"]:

                        # Found a source

                        if not f"column_{str(i + 1)}" in new_df_dict.keys():

                            new_df_dict[f"column_{str(i + 1)}"] = \
                                df_dict[f"column_{j}"]

                            new_df_dict[f"transformation_{str(i + 1)}"] = \
                                df_dict[f"transformation_{j}"]

                            new_df_dict[f"table_alias_{str(i + 1)}"] = \
                                df_dict[f"table_alias_{j}"]

                            break

                        else:

                            new_df_dict[f"column_{str(i + 1)}"].append(
                                df_dict[f"column_{j}"]
                            )

                            new_df_dict[f"transformation_{str(i + 1)}"].append(
                                df_dict[f"transformation_{j}"]
                            )

                            new_df_dict[f"table_alias_{str(i + 1)}"].append(
                                df_dict[f"table_alias_{j}"]
                            )

                            # print(new_df_dict)

                            break

                    else:

                        j += 1

            break

        else:

            new_df_dict[f"column_{str(i)}"] = column_list

            new_df_dict[f"transformation_{str(i)}"] = trns_list

            new_df_dict[f"table_alias_{str(i)}"] = table_alias_list

        # Move to the next hop

        i += 1

    # print(new_df_dict)

    return new_df_dict


def _process_df_dict2(df_dict):

    # print(df_dict)

    new_df_dict = {}

    i = 5

    while i < len(list(df_dict.items())):

        col_tuple = list(df_dict.items())[i - 2]

        transformation_tuple = list(df_dict.items())[i - 1]

        table_alias_tuple = list(df_dict.items())[i]

        if transformation_tuple[1][0].startswith('CASE'):

            # Get the number of dependent columns

            num_dependent_cols = len(col_tuple[1])

            # Duplicate the previous indices based on the number of dependent columns

            for j in range(i - 2):

                new_df_dict[list(df_dict.items())[j][0]] = \
                    list(df_dict.items())[j][1] * num_dependent_cols

            # Add hop for case statement

            new_df_dict[col_tuple[0]] = col_tuple[1]

            new_df_dict[transformation_tuple[0]] = \
                transformation_tuple[1] * num_dependent_cols

            new_df_dict[table_alias_tuple[0]] = table_alias_tuple[1]

            # Go to the end of the source hops for the case dependent columns

            i += 3 * num_dependent_cols

        else:

            new_df_dict[col_tuple[0]] = col_tuple[1]

            new_df_dict[transformation_tuple[0]] = transformation_tuple[1]

            new_df_dict[table_alias_tuple[0]] = table_alias_tuple[1]

        # Jump to next hop

        i = i + 3

    return new_df_dict


def _handle_coalesce_statements(
        parsed_query,
        df_dict,
        transformation,
        node_number,
        target_column,
        index
):

    coalesce_cols = [
        (col.alias_or_name, col.table)
        for col in parsed_query.find_all(expressions.Column)
    ]

    for dep_col in coalesce_cols:

        df_dict = _add_to_df_dict(
            df_dict=df_dict,
            target_column=target_column,
            node_number=node_number,
            column_name_or_alias=dep_col[0],
            table_name_or_alias=dep_col[1],
            transformation=transformation,
            index=index
        )

        node_number += 1

    return df_dict, node_number


def _handle_case_statements(
        parsed_query,
        df_dict,
        transformation,
        node_number,
        target_column,
        index
):

    parent_node = node_number - 1

    # Extract end/target column

    end_column = parsed_query.alias_or_name

    # Extract ELSE/default column

    default_source = None

    # Handling default condition

    if isinstance(
            parsed_query.args['this'].args['default'],
            Column
    ):

        default_exp = parsed_query.args['this'].args['default']

        default_source = (
            default_exp.alias_or_name,
            default_exp.table
        )

    else:

        try:

            columns = parsed_query.args['this'].args['default'].find_all(
                expressions.Column
            )

            default_source = [
                (col.table, col.name)
                for col in columns
            ]

        except Exception as e:

            print(
                f"WARN: Default not present in CASE statement. "
                f"Details: {e}"
            )

    # Extract dependent columns for IF expressions

    dependent_cols_and_sources = []

    for if_exp in parsed_query.args['this'].args['ifs']:

        # Iterate over each if expression

        for col in if_exp.find_all(Column):

            # Extract dependent columns from the expression

            # Check if it's a duplicate

            is_duplicate = False

            for item in dependent_cols_and_sources:

                if item[0] == col.alias_or_name and item[1] == col.table:

                    is_duplicate = True

                    break

            # If not a duplicate, add the dependent list

            if not is_duplicate:

                dependent_cols_and_sources.append(
                    (col.alias_or_name, col.table)
                )

    # Add dependents to df_dict

    for dependent in dependent_cols_and_sources:

        df_dict = _add_to_df_dict(
            df_dict=df_dict,
            target_column=target_column,
            node_number=node_number,
            column_name_or_alias=dependent[0],
            table_name_or_alias=dependent[1],
            transformation=transformation,
            index=index
        )

        node_number += 1

    # Add ELSE dependency if present

    if default_source:

        if isinstance(default_source, tuple):

            df_dict = _add_to_df_dict(
                df_dict=df_dict,
                target_column=target_column,
                node_number=node_number,
                column_name_or_alias=default_source[0],
                table_name_or_alias=default_source[1],
                transformation=transformation,
                index=index
            )

            node_number += 1

        else:

            for it in default_source:

                df_dict = _add_to_df_dict(
                    df_dict=df_dict,
                    target_column=target_column,
                    node_number=node_number,
                    column_name_or_alias=it[1],
                    table_name_or_alias=it[0],
                    transformation=transformation,
                    index=index
                )

                node_number += 1

    return df_dict, node_number


# if __name__ == "__main__":

#     sql_file_name = "_S_PEAKSCOM_COLLATERALEXPOSURE_UTIL_DST_B1_S1.sql"
#     # TODO: Add SQL file name here

#     metadata = {
#         "DST_name": "COMMERCIAL_LENDING_COLLAT_UTIL",
#         "set_code": "peakscorn/collateralexposure/agg",
#         "file_name": sql_file_name,
#         "session_name": "S_PEAKSCOM_COLLATERALEXPOSURE_UTIL_DST",
#         "output_csv_name": f"output_{sql_file_name}.csv"
#     }

#     format_output(
#         start_line=0,
#         metadata=metadata,
#         file_name
#     )