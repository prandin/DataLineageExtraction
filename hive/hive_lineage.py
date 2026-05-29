import pandas as pd
import numpy as np
import re
import os
import warnings

warnings.filterwarnings("ignore")


def dst_name_to_file_name(dst_name):
    name_parts = dst_name.split(".")
    schema = name_parts[0]
    actual_dst = name_parts[1]

    new_file_name = f"{actual_dst}_TRANSPOSE_sch{schema}.csv"
    return new_file_name


# hive_dst_mapping = {
#     'frr_cidw_cce_daily_tf.hql'                : 'crr.cash_daily',
#     'cidw_daily_lineMappingOverride.hql'       : 'crr.cash_daily',
#     'cidw_daily_DST_GLOVERRIDE.hql'            : 'crr.cash_daily',
#     'frr_cash_d_tf.hql'                        : 'crr.post_gl_trans_adj_daily',
#     'frr_cidw_cce_tf.hql'                      : 'crr.cash',
#     'cidw_monthly_lineMappingOverride.hql'     : 'crr.cash',
#     'cidw_monthly_DST_GLOVERRIDE.hql'          : 'crr.cash',
#     'frr_arctic_cashtrd_tf.hql'                : 'crr.cash',
#     'arctic_monthly_lineMappingOverride.hql'   : 'crr.cash',
#     'arctic_monthly_DST_GLOVERRIDE.hql'        : 'crr.cash',
#     'frr_cash_d_tf.hql'                        : 'crr.post_gl_trans_adjustment'
# }


def reverse_row_stages(df):

    df = df.copy()

    try:
        number_of_columns_per_hop = 8
        num_tuples = len(df.columns) // number_of_columns_per_hop

        def reverse_row(row):

            data_tuples = [
                (
                    row[f"TGT_SCHEMA.TABLE_{i}"],
                    row[f"TGT_COLUMN_{i}"],
                    row[f"TGT_DATA_TYPE_{i}"],
                    row[f"SRC_TGT_TRANSFORMATION_{i}"],
                    row[f"SRC_SCHEMA.TABLE_{i}"],
                    row[f"SRC_COLUMN_{i}"],
                    row[f"SRC_DATA_TYPE_{i}"],
                    row[f"SET_CODE_{i}"]
                )
                for i in range(1, num_tuples + 1)
                if pd.notna(row[f"SRC_COLUMN_{i}"])
                or pd.notna(row[f"SRC_SCHEMA.TABLE_{i}"])
            ]

            data_tuples.reverse()

            new_row = [np.nan] * len(row)

            for i, (
                tgt_schema,
                tgt_col,
                tgt_data,
                src_tgt,
                src_schema,
                src_col,
                src_data,
                set_code
            ) in enumerate(data_tuples):

                new_row[number_of_columns_per_hop * i] = tgt_schema
                new_row[number_of_columns_per_hop * i + 1] = tgt_col
                new_row[number_of_columns_per_hop * i + 2] = tgt_data
                new_row[number_of_columns_per_hop * i + 3] = src_tgt
                new_row[number_of_columns_per_hop * i + 4] = src_schema
                new_row[number_of_columns_per_hop * i + 5] = src_col
                new_row[number_of_columns_per_hop * i + 6] = src_data
                new_row[number_of_columns_per_hop * i + 7] = set_code

            return pd.Series(new_row, index=row.index)

        df = df.apply(reverse_row, axis=1)

    except Exception as e:
        print("error while reversal")

    return df


def transform_lineage_to_transpose(lineage_nodes, group_set_code):
    """
    Function to transform a contiguous lineage_df to a base_lineage_record

    :param lineage_nodes:
    :return: base_lineage_record
    """

    lineage_nodes = lineage_nodes.copy()
    lineage_nodes = lineage_nodes.sort_values("NODE_NUMBER")

    base_lineage_record = {}

    try:

        # To insert new column into hop, edit here first
        for stage_num, row in enumerate(lineage_nodes.itertuples(), start=1):

            # col 1
            base_lineage_record[f"TGT_SCHEMA.TABLE_{stage_num}"] = row.TGT_TABLE

            # col 2
            base_lineage_record[f"TGT_COLUMN_{stage_num}"] = row.TGT_COLUMN

            # col 3
            base_lineage_record[f"TGT_DATA_TYPE_{stage_num}"] = row.TGT_DATA_TYPE

            # col 4
            base_lineage_record[
                f"SRC_TGT_TRANSFORMATION_{stage_num}"
            ] = row.SRC_TGT_TRANSFORMATION

            # col 5
            if (
                str(row.SOURCE_SCHEMA).strip() != ""
                and str(row.SOURCE_SCHEMA).strip().lower() != "nan"
            ):
                base_lineage_record[
                    f"SRC_SCHEMA.TABLE_{stage_num}"
                ] = str(row.SOURCE_SCHEMA) + "." + str(row.SRC_TABLE)
            else:
                base_lineage_record[
                    f"SRC_SCHEMA.TABLE_{stage_num}"
                ] = row.SRC_TABLE

            # col 6
            base_lineage_record[f"SRC_COLUMN_{stage_num}"] = row.SRC_COLUMN

            # col 7
            base_lineage_record[f"SRC_DATA_TYPE_{stage_num}"] = row.SRC_DATA_TYPE

            # col 8
            base_lineage_record[f"SET_CODE_{stage_num}"] = group_set_code

            # col 9 (commented)
            # base_lineage_record[f"SESSION_NAME_{stage_num}"] = row.SESSION_NAME

    except Exception as e:
        print("error while generating base lineage")

    return base_lineage_record


def generate_lineages_as_dfs(df):

    visited = set()
    lineage_dfs = []

    df = df.copy()

    try:

        for start_node in df['NODE_NUMBER']:

            if start_node not in visited:

                lineage = []
                current_node = start_node

                lineage.append(current_node)

                child_node = None

                matching_rows = df.loc[
                    df['NODE_NUMBER'] == current_node,
                    'CHILD_NODE'
                ]

                if not matching_rows.empty:

                    child_node = matching_rows.values[0]

                    if pd.notna(child_node) and child_node != '':
                        child_node = int(child_node)
                    else:
                        child_node = None

                while child_node is not None:

                    # break cycle
                    if child_node in lineage:
                        break

                    visited.add(child_node)
                    lineage.append(child_node)

                    matching_rows = df.loc[
                        df['NODE_NUMBER'] == child_node,
                        'CHILD_NODE'
                    ]

                    if not matching_rows.empty:

                        child_node = matching_rows.values[0]

                        if pd.notna(child_node) and child_node != '':
                            child_node = int(child_node)
                        else:
                            child_node = None
                    else:
                        child_node = None

                lineage_df = df[df['NODE_NUMBER'].isin(lineage)]
                lineage_dfs.append(lineage_df)

    except Exception as e:
        print("error with lineage")

    return lineage_dfs


def process_lineage_with_rules(group):

    processed_records = []
    reversed_df = pd.DataFrame()

    group_set_code_list = df['SET_CODE'].dropna()

    if group_set_code_list.empty:
        group_set_code = ''
    else:
        group_set_code_list = group_set_code_list[
            group_set_code_list.str.strip() != ''
        ]

        if not group_set_code_list.empty:
            group_set_code = group_set_code_list.iloc[0]
        else:
            group_set_code = ''

    group = group.sort_values("NODE_NUMBER")

    lineages = generate_lineages_as_dfs(group)

    for lineage in lineages:

        output_nodes = []

        for index, row in lineage.iterrows():
            output_nodes.append(row)

        if output_nodes:

            lineage_nodes = pd.DataFrame(output_nodes)

            base_lineage_record = transform_lineage_to_transpose(
                lineage_nodes,
                group_set_code
            )

            processed_records.append(base_lineage_record)

    if processed_records:

        all_columns = [
            col
            for record in processed_records
            for col in record.keys()
        ]

        unique_columns = sorted(
            set(all_columns),
            key=lambda x: all_columns.index(x)
        )

        processed_df = pd.DataFrame(
            processed_records,
            columns=unique_columns
        )

        reversed_df = reverse_row_stages(processed_df)

    return reversed_df


# ---------------------------------------------------------
# POST PROCESSING FUNCTIONS
# ---------------------------------------------------------

def output_processing(transpose_result_df):
    """
    Code to add FINAL_ATTRIBUTE, ACTUAL_SOURCE
    for the intersession joining

    :param transpose_result_df:
    :return:
    """

    transpose_result_df = transpose_result_df.copy()

    left_col = (
        transpose_result_df['TGT_SCHEMA.TABLE_1']
        .fillna('')
        .astype(str)
    )

    right_col = (
        transpose_result_df['TGT_COLUMN_1']
        .fillna('')
        .astype(str)
    )

    transpose_result_df['FINAL_ATTRIBUTE'] = np.where(
        (left_col != '') & (right_col != ''),
        left_col + '.' + right_col,
        left_col + right_col
    )

    last_sets = []

    for index, row in transpose_result_df.iterrows():

        last_set = None

        for col_prefix in [
            'SRC_SCHEMA.TABLE_',
            'SRC_COLUMN_'
        ]:

            matching_cols = [
                col
                for col in transpose_result_df.columns
                if col.startswith(col_prefix)
            ]

            for col in reversed(matching_cols):

                if pd.notna(row[col]):
                    last_set = col.split('_')[-1]
                    break

            if last_set:
                break

        if last_set:

            schema_col = f"SRC_SCHEMA.TABLE_{last_set}"
            column_col = f"SRC_COLUMN_{last_set}"

            schema_value = (
                row[schema_col]
                if pd.notna(row[schema_col])
                and str(row[schema_col]) != "nan"
                else ''
            )

            column_value = (
                row[column_col]
                if pd.notna(row[column_col])
                and str(row[column_col]) != "nan"
                else ''
            )

            actual_source_string = ""

            if schema_value:
                if column_value:
                    actual_source_string = (
                        f"{schema_value}.{column_value}"
                    ).strip('.')
                else:
                    actual_source_string = f"{schema_value}"
            else:
                if column_value:
                    actual_source_string = f"{column_value}"

            last_sets.append(actual_source_string)

        else:
            last_sets.append('')

    transpose_result_df['ACTUAL_SOURCE'] = last_sets

    cols = (
        ['FINAL_ATTRIBUTE', 'ACTUAL_SOURCE']
        + [
            col
            for col in transpose_result_df.columns
            if col not in ['FINAL_ATTRIBUTE', 'ACTUAL_SOURCE']
        ]
    )

    transpose_result_df = transpose_result_df[cols]

    return transpose_result_df


def drop_columns_from_transpose(output_transpose_df):
    """
    drops unnecessary columns
    """

    output_transpose_df = output_transpose_df.copy()

    data_columns_to_drop = [
        col
        for col in output_transpose_df.columns
        if any(
            col.startswith(prefix)
            for prefix in [
                'SRC_DATA_TYPE_',
                'TGT_DATA_TYPE_'
            ]
        )
    ]

    output_transpose_df = output_transpose_df.drop(
        columns=data_columns_to_drop
    )

    columns_to_drop = [
        col
        for col in output_transpose_df.columns
        if any(
            col.startswith(prefix)
            and not col.endswith('_1')
            for prefix in [
                'TGT_SCHEMA.TABLE_',
                'TGT_COLUMN_'
            ]
        )
    ]

    output_transpose_df = output_transpose_df.drop(
        columns=columns_to_drop
    )

    set_code_columns_to_drop = [
        col
        for col in output_transpose_df.columns
        if any(
            col.startswith(prefix)
            and not col.endswith('_1')
            for prefix in [
                'SET_CODE_'
            ]
        )
    ]

    output_transpose_df = output_transpose_df.drop(
        columns=set_code_columns_to_drop
    )

    return output_transpose_df


def split_character_length(
    output_transpose_df,
    max_length
):
    """
    :param output_transpose_df:
    :param max_length:
    :return:
    """

    output_transpose_df = output_transpose_df.copy()

    transformation_cols = [
        col
        for col in output_transpose_df.columns
        if col.startswith('SRC_TGT_TRANSFORMATION_')
    ]

    for col in transformation_cols:

        for index, value in output_transpose_df[col].items():

            if isinstance(value, str) and len(value) > max_length:

                num_splits = -(-len(value) // max_length)

                split_values = [
                    value[
                        i * max_length:
                        (i + 1) * max_length
                    ]
                    for i in range(num_splits)
                ]

                col_index = (
                    output_transpose_df.columns.get_loc(col)
                )

                for i, split_value in enumerate(split_values):

                    if i == 0:

                        output_transpose_df.at[
                            index,
                            col
                        ] = split_value

                    else:

                        new_col_name = (
                            f"{col}_{chr(64 + i)}"
                        )

                        if (
                            new_col_name
                            not in output_transpose_df.columns
                        ):
                            output_transpose_df.insert(
                                col_index + i,
                                new_col_name,
                                None
                            )

                        output_transpose_df.at[
                            index,
                            new_col_name
                        ] = split_value

    return output_transpose_df


def add_final_attribute(output_transpose_df):
    """
    Adds final attribute column to output transpose df

    :param output_transpose_df:
    :return:
    """

    output_transpose_df = output_transpose_df.copy()

    left_col = (
        output_transpose_df['TGT_SCHEMA.TABLE_1']
        .fillna('')
        .astype(str)
        .str.strip()
    )

    right_col = (
        output_transpose_df['TGT_COLUMN_1']
        .fillna('')
        .astype(str)
        .str.strip()
    )

    output_transpose_df['FINAL_ATTRIBUTE'] = np.where(
        (left_col != '') & (right_col != ''),
        left_col + '.' + right_col,
        left_col + right_col
    )

    return output_transpose_df


def add_actual_source(output_transpose_df):
    """
    Adds ACTUAL_SOURCE column to output_transpose_df

    :param output_transpose_df:
    :return: output_transpose_df
    """

    output_transpose_df = output_transpose_df.copy()

    last_sets = []

    for index, row in output_transpose_df.iterrows():

        last_set = 0

        for col_prefix in [
            'SRC_SCHEMA.TABLE',
            'SRC_COLUMN_'
        ]:

            matching_cols = [
                col
                for col in output_transpose_df.columns
                if col.startswith(col_prefix)
            ]

            for col in reversed(matching_cols):

                if pd.notna(row[col]):

                    last_stage_num = col.split('_')[-1]

                    if int(last_stage_num) > int(last_set):
                        last_set = last_stage_num

                    break

        # Fix for broken schema in sql lineage
        if last_set:

            schema_col = f"SRC_SCHEMA.TABLE_{last_set}"
            row = row.fillna('')

            actual_source_string = ""

            column_col = f"SRC_COLUMN_{last_set}"

            schema_value = (
                str(row[schema_col]).strip()
                if pd.notna(row[schema_col])
                and str(row[schema_col]) != "nan"
                else ''
            )

            column_value = (
                str(row[column_col]).strip()
                if pd.notna(row[column_col])
                and str(row[column_col]) != "nan"
                else ''
            )

            if schema_value:
                if column_value:
                    actual_source_string = (
                        f"{schema_value}.{column_value}"
                    )
                else:
                    actual_source_string = (
                        f"{schema_value}"
                    )
            else:
                if column_value:
                    actual_source_string = (
                        f"{column_value}"
                    )
                    
        # Hot fixes; to be fixed in respective modules
        if "." not in actual_source_string:
            actual_source_string = "HARDCODED"

        if (
            pd.notna(row[f"SRC_TGT_TRANSFORMATION_{last_set}"])
            and row[f"SRC_TGT_TRANSFORMATION_{last_set}"] != ""
        ):
            row[f"SRC_TGT_TRANSFORMATION_{last_set}"] = str(
                row[f"SRC_TGT_TRANSFORMATION_{last_set}"]
            )

            last_transformation = row[
                f"SRC_TGT_TRANSFORMATION_{last_set}"
            ].strip()

            actual_source_string = hardcoded_check_for_last_transformation(
                actual_source_string,
                last_transformation
            )

            row[f"SRC_TGT_TRANSFORMATION_{last_set}"] = \
                row[f"SRC_TGT_TRANSFORMATION_{last_set}"].strip()

            if (
                row[f"SRC_TGT_TRANSFORMATION_{last_set}"].startswith('$$')
                and '.' not in row[f"SRC_TGT_TRANSFORMATION_{last_set}"]
            ):
                # $$param_name
                actual_source_string = "RUNTIME_PARAMETER"

        last_sets.append(actual_source_string)

    else:
        last_sets.append('')

    output_transpose_df['ACTUAL_SOURCE'] = last_sets

    return output_transpose_df


def hardcoded_check_for_last_transformation(
    actual_source_string,
    last_transformation
):

    if (
        (last_transformation[0] == '"' and last_transformation[-1] == '"')
        or
        (last_transformation[0] == "'" and last_transformation[-1] == "'")
    ):
        actual_source_string = "HARDCODED"

    if re.fullmatch(
        r'\s*to_date\s*\(.*\)\s*',
        last_transformation,
        re.IGNORECASE
    ):
        actual_source_string = "HARDCODED"

    return actual_source_string


def column_prefix(df, prefix):
    """
    :param df:
    :param prefix:
    :return: df
    """

    df = df.copy()

    new_columns = {
        col_name: f"{prefix}{col_name}"
        for col_name in df.columns
    }

    df.rename(columns=new_columns, inplace=True)

    return df


def simplify_hop_data_hopwise(df):

    def combine_schema_columns(tbl_series, col_series):

        s1 = tbl_series.fillna('').str.strip()
        s2 = col_series.fillna('').str.strip()

        combined = s1.astype(str) + '.' + s2.astype(str)

        return combined.str.strip('.').replace('.', '', regex=False)

    # Start with fixed leading columns
    new_df = df[
        ['CF_FINAL_ATTRIBUTE', 'CF_ACTUAL_SOURCE', 'CF_SET_CODE']
    ].copy()

    # Extract hop numbers
    hop_nums = set()

    pattern = re.compile(r'_([0-9]+)(?:_[A-Z]*|$)')

    for col in df.columns:
        match = pattern.search(col)

        if match:
            hop_nums.add(int(match.group(1)))

    hop_nums = sorted(hop_nums)

    for hop in hop_nums:

        hop_block = []

        # Step 1
        # Place TGT_SCHEMA_TABLE_COLUMN at the start of only hop 1

        if hop == 1:

            tgt_tbl = f'CF_TGT_SCHEMA.TABLE_{hop}'
            tgt_col = f'CF_TGT_COLUMN_{hop}'

            if tgt_tbl in df.columns and tgt_col in df.columns:

                tgt_combined = f'CF_TGT_SCHEMA_TABLE_COLUMN_{hop}'

                new_df[tgt_combined] = combine_schema_columns(
                    df[tgt_tbl],
                    df[tgt_col]
                )

                hop_block.append(tgt_combined)

        # Step 2
        # Transformation columns

        transformation_cols = [
            col
            for col in df.columns
            if re.fullmatch(
                rf'CF_SRC_TGT_TRANSFORMATION_{hop}(_[A-Z]*)?',
                col
            )
        ]

        for col in transformation_cols:
            new_df[col] = df[col]
            hop_block.append(col)

        # Step 3
        # Source path

        src_tbl = f'CF_SRC_SCHEMA.TABLE_{hop}'
        src_col = f'CF_SRC_COLUMN_{hop}'

        if src_tbl in df.columns and src_col in df.columns:

            src_combined = f'CF_SRC_SCHEMA_TABLE_COLUMN_{hop}'

            new_df[src_combined] = combine_schema_columns(
                df[src_tbl],
                df[src_col]
            )

            hop_block.append(src_combined)

        current_cols = list(new_df.columns)

        for col in hop_block:
            if col in current_cols:
                current_cols.remove(col)

        new_df = new_df[current_cols + hop_block]

    return new_df


# ---------------------------------------------------------
# FLATPACKING
# ---------------------------------------------------------

def flatpack(sql_df):

    transpose_result = []

    if not sql_df.empty:

        sql_df = sql_df.sort_values(
            by="NODE_NUMBER"
        ).reset_index(drop=True)

        sql_groups = {
            key: group
            for key, group in sql_df.groupby(['FINAL_TARGET'])
        }

        for sql_key, sql_group in sql_groups.items():

            sql_group_flatpack_df = process_lineage_with_rules(
                sql_group
            )

            transpose_result.append(sql_group_flatpack_df)

        transpose_result_df = pd.concat(
            transpose_result,
            ignore_index=True
        )

        output_transpose_df = output_processing(
            transpose_result_df
        )

        output_transpose_df = drop_columns_from_transpose(
            output_transpose_df
        )

        # Step 2
        output_transpose_df = split_character_length(
            output_transpose_df,
            max_length=25000
        )

        # Step 3
        output_transpose_df = add_final_attribute(
            output_transpose_df
        )

        output_transpose_df = add_actual_source(
            output_transpose_df
        )

        output_transpose_df.rename(
            columns={'SET_CODE_1': 'SET_CODE'},
            inplace=True
        )

        cols = (
            ['FINAL_ATTRIBUTE', 'ACTUAL_SOURCE', 'SET_CODE']
            +
            [
                col
                for col in output_transpose_df.columns
                if col not in [
                    'FINAL_ATTRIBUTE',
                    'ACTUAL_SOURCE',
                    'SET_CODE'
                ]
            ]
        )

        output_transpose_df = output_transpose_df[cols]

        output_transpose_df = column_prefix(
            output_transpose_df,
            "CF_"
        )

        # hop-wise session names not needed
        output_transpose_df = simplify_hop_data_hopwise(
            output_transpose_df
        )

        output_transpose_df = output_transpose_df.drop_duplicates()

        return output_transpose_df


"""
Starting point of code.
"""

sql_file_path = "Input/output_frr_cash_d_tf.hql.csv"

output_path = "Output/output_frr_cash_d_tf.hql_TRANSPOSE.csv"

input_folder_path = 'Input/'
output_folder_path = 'Output/'
reference_file_path = 'Input/Reference_file.xlsx'

ref_df = pd.read_excel(reference_file_path)

# ref_df = ref_df.applymap(
#     lambda x: x.lower().strip()
#     if isinstance(x, str)
#     else x
# )

ref_df = ref_df.applymap(
    lambda x: x.strip()
    if isinstance(x, str)
    else x
)

# Ignore entries without .hql

ref_df = ref_df[
    ref_df['Hql File Name'].str.contains(
        r'\.hql$',
        case=False,
        na=False
    )
]

# Handle merged cells

ref_df['DST table in CFARRI'] = \
    ref_df['DST table in CFARRI'].ffill()

print(ref_df)

grouped = (
    ref_df.groupby('DST table in CFARRI')['Hql File Name']
    .apply(list)
    .to_dict()
)

for dst_name, hql_files in grouped.items():

    print(f"DST NAME: {dst_name}")
    print(
        "Number of HQL files for the DST= ",
        len(hql_files)
    )

    transpose_dfs = []

    for hql_file in hql_files:

        hql_path = os.path.join(
            input_folder_path,
            hql_file + ".csv"
        )

        if not os.path.exists(hql_path):
            print(f"{hql_path} does not exist")
            continue

        df = pd.read_csv(hql_path)

        df.columns = df.columns.str.upper()

        df = df.applymap(
            lambda x: x.upper().strip()
            if isinstance(x, str)
            else x
        )

        if 'TGT_TABLE' in df.columns:
            df['TGT_TABLE'] = df['TGT_TABLE'].replace(
                'XML',
                dst_name.upper()
            )

        transpose_df = flatpack(df)

        transpose_dfs.append(transpose_df)

    if not transpose_dfs:

        print(f"Empty df list for {dst_name}")

    else:

        combined_transpose_df = pd.concat(
            transpose_dfs,
            ignore_index=True
        )

        combined_transpose_df = (
            combined_transpose_df.drop_duplicates()
        )

        new_output_path = dst_name_to_file_name(
            dst_name.upper()
        )

        output_path = (
            f"{output_folder_path}/{new_output_path}.csv"
        )

        combined_transpose_df.to_csv(
            output_path,
            index=False
        )