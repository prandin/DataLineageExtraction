import os
import re
import openpyxl
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from glob import glob

from pandas import read_excel


def find_functions(query, fns):
    found = []
    for fn in fns:
        if re.search(rf'\b{re.escape(fn)}\b', query):
            found.append(fn)
    return found


def contains_transformation(query):
    query = str(query)

    if len(query.strip()) <= 0 or query.lower() == 'nan':
        return False
    else:
        return True


def add_last_non_empty_column(df):

    chunk_size = 500

    temp_df = df.replace("", np.nan)

    chunks = [temp_df.iloc[i:i + chunk_size]
              for i in range(0, len(temp_df), chunk_size)]

    def process_chunk(chunk):
        return chunk.apply(lambda row: row.last_valid_index(), axis=1)

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_chunk, chunks))

    last_cols = pd.concat(results)

    df["last_column_which_has_value"] = last_cols

    return df


def find_total_hops(name) -> int:
    split_val = name.split("_")
    return int(split_val[-1])


def find_hopl_size(column_list):

    count_hopl_size = 0

    for i in range(len(column_list)):

        split_values = column_list[i].split("_")

        if split_values[-1] == "1":
            count_hopl_size += 1

        else:

            if split_values[-2] == "1":
                count_hopl_size += 1

    return count_hopl_size


def get_files(ext, directory):

    extension = f"*.{ext}"

    csv_files = glob(os.path.join(directory, extension))

    sorted_file_list = sorted(
        csv_files,
        key=lambda f: os.path.getsize(f),
        reverse=True
    )

    return sorted_file_list


def reorder_df_by_columns_hierarchy(unordered_df, prefix):

    """
    Reorders columns in a DataFrame such that child columns
    immediately follow their parent columns.

    Parent columns:
        CF_SRC_TGT_TRANSFORMATION_1

    Child columns:
        CF_SRC_TGT_TRANSFORMATION_1_A
        CF_SRC_TGT_TRANSFORMATION_1_B
    """

    df = unordered_df

    original_cols = df.columns.tolist()

    new_cols = []

    used = set()

    for col in original_cols:

        if col in used:
            continue

        new_cols.append(col)

        used.add(col)

        if col.startswith(prefix):

            suffix = col[len(prefix):]

            if suffix.isdigit():

                children_prefix = col + "_"

                children = [
                    c for c in original_cols
                    if c.startswith(children_prefix)
                    and c not in used
                ]

                children.sort()

                new_cols.extend(children)

                used.update(children)

    for col in original_cols:

        if col not in used:
            new_cols.append(col)

    ordered_df = df[new_cols]

    return ordered_df


def reorder_translation_cols(df):

    cols = df.columns.tolist()

    reordered_cols = []

    skip_set = set()

    for col in cols:

        if col in skip_set:
            continue

        reordered_cols.append(col)

        if (
            col.startswith('CF_SRC_TGT_TRANSFORMATION_')
            and not '_TRANSLATION' in col
        ):

            translation_col = col.replace(
                'CF_SRC_TGT_TRANSFORMATION',
                'CF_SRC_TGT_TRANSFORMATION_TRANSLATIONS'
            )

            if translation_col in cols:

                reordered_cols.append(translation_col)

                skip_set.add(translation_col)

    df = df[reordered_cols]

    return df


def consolidate_transpose(directory_path):

    all_excel_data = []

    count_of_rows = 0

    tracker_list = get_files("xlsx", directory_path)

    print("Found len(tracker_list): files")
    print(tracker_list)

    for file in tracker_list:

        if "_TRANSPOSE_final" in file.split("\\")[-1]:

            print("Loaded:", file.split("\\")[-1])

            df = pd.read_excel(file, dtype=str)

            df = df.fillna("")

            count_of_cols = len(df.columns)

            print("count-of-columns:", count_of_cols)

            all_excel_data.append(df)

        else:

            print(f"FILE-NOT-FOUND: {file}")

    consolidated_df = pd.concat(
        all_excel_data,
        ignore_index=True
    )

    print(f"len(consolidated_df): {len(consolidated_df)}")

    print("Consolidated csv files")

    print(consolidated_df.shape)

    consolidated_df.to_excel(
        rf"{output_folder}\consolidated_transpose.xlsx",
        index=False
    )

    return consolidated_df


if __name__ == "__main__":

    env = "PREPROD"

    transpose_folder = (
        r"C:\Users\ZKDN4AW\PycharmProjects\Lineage_Generation"
        r"\Shareable_CFARRI_Codes\Step_7_Condensation_view\Transpose"
    )

    ax_dst_file = (
        r"C:\Users\ZKDN4AW\PycharmProjects\Lineage_Generation"
        r"\Shareable_CFARRI_Codes\Step_7_Condensation_view"
        r"\AXIOM_DST_List.xlsx"
    )

    output_folder = (
        r"C:\Users\ZKDN4AW\PycharmProjects\Lineage_Generation"
        r"\Shareable_CFARRI_Codes\Step_7_Condensation_view\output"
    )

    df = consolidate_transpose(transpose_folder)

    df = reorder_df_by_columns_hierarchy(
        df,
        "CF_SRC_TGT_TRANSFORMATION_"
    )

    df.to_excel(
        rf"{output_folder}\reordered_consolidated_transpose_{env}.xlsx",
        index=False
    )

    filter = (
        df['CF_FINAL_ATTRIBUTE'].str.split('.').str[-1].str.startswith("LINE_")
        |
        df['CF_FINAL_ATTRIBUTE'].str.split('.').str[-1].eq("CRR_INSTRUMENT_2")
        |
        df['CF_FINAL_ATTRIBUTE'].str.split('.').str[-1].eq("CRR_INSTRUMENT_2_WIN")
    )

    df_special = df[filter].copy()

    translation_present = False

    for col in df.columns:

        if "_TRANSLATION" in col:

            translation_present = True

            print("translation columns present")

    if translation_present:

        df = reorder_translation_cols(df)

        df = df.rename(
            columns={
                col: col.replace(
                    'CF_SRC_TGT_TRANSFORMATION_TRANSLATION',
                    'CF_SRC_TGT_TRANSLATION'
                )
                for col in df.columns
                if col.startswith(
                    'CF_SRC_TGT_TRANSFORMATION_TRANSLATION'
                )
            }
        )

    ax_dst_df = pd.read_excel(
        ax_dst_file,
        sheet_name=env,
        dtype=str
    )

    ax_dst_df = ax_dst_df.fillna("")

    axiom_key_list = ax_dst_df["AXIOM_KEY"].tolist()

    axiom_key_list = list(set(axiom_key_list))

    updated_list = []

    for col in axiom_key_list:

        updated_list.append(col.strip().upper())

    print(f"axiom_key_list: {updated_list}")

    print(f"len-axiom_key_list: {len(updated_list)}")

    df = df[df['CF_FINAL_ATTRIBUTE'].isin(updated_list)]

    print(f"df-columns: {list(df.columns)}")

    df.to_excel(
        rf"{output_folder}\223_intermediate_output.xlsx",
        index=False
    )

    ############################################################
    # STARTING-OF-MAIN-LOGIC
    ############################################################

    column_list = df.columns.to_list()

    last_col_name = column_list[-1]

    max_no_of_hops = find_total_hops(last_col_name)

    print("Max-number-of-hops:", max_no_of_hops)

    hopl_size = find_hopl_size(column_list)

    print(f"hopl_size: {hopl_size}")

    extra_df = add_last_non_empty_column(df)

    extra_df.to_excel(
        rf"{output_folder}\extra_df.xlsx",
        index=False
    )

    print("Extra df computed")

    new_df = pd.DataFrame(
        "",
        index=range(df.shape[0]),
        columns=[
            "CF_FINAL_ATTRIBUTE",
            "CF_SET_CODE",
            "TRANSFORMATION",
            "BUSINESS_TRANSLATION",
            "CF_ACTUAL_SOURCE"
        ]
    )

    print("iterating over each row")

    final_df_hop_array = []

    if hopl_size == 12:

        for i in range(df.shape[0]):

            transformation_result_array = []

            new_df.loc[i, "CF_FINAL_ATTRIBUTE"] = (
                df["CF_FINAL_ATTRIBUTE"].iloc[i]
            )

            new_df.loc[i, "CF_ACTUAL_SOURCE"] = (
                df["CF_ACTUAL_SOURCE"].iloc[i]
            )

            new_df.loc[i, "CF_SET_CODE"] = (
                df["CF_SET_CODE"].iloc[i]
            )

            for hop_count in range(1, max_no_of_hops + 1):

                transformation_col_name = (
                    f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"
                )

                is_transformation_valid = contains_transformation(
                    df[transformation_col_name].iloc[i]
                )

                last_hop_value_for_row = int(
                    extra_df["last_column_which_has_value"]
                    .iloc[i]
                    .split("_")[-1]
                )

                if is_transformation_valid or hop_count:

                    transformation_result_array.append(
                        (
                            1,
                            f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"
                        )
                    )

                    transformation_result_array.append(
                        (
                            1,
                            f"CF_SRC_TGT_TRANSLATIONS_{hop_count}"
                        )
                    )

                    transformation_result_array.append(
                        (
                            1,
                            f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count}"
                        )
                    )

                else:

                    transformation_result_array.append(
                        (
                            0,
                            f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"
                        )
                    )

                    transformation_result_array.append(
                        (
                            0,
                            f"CF_SRC_TGT_TRANSLATIONS_{hop_count}"
                        )
                    )

                    transformation_result_array.append(
                        (
                            0,
                            f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count}"
                        )
                    )

            final_df_hop_array.append(
                transformation_result_array
            )

    print("Created final_df_hop_array")

    file_name = "final_df_hop_array.txt"

    with open(file_name, "w") as file:

        for row in final_df_hop_array:

            file.write('\t'.join(map(str, row)) + '\n')

    for i in range(len(final_df_hop_array)):

        hop_count_flag = 1

        transformation_counter = 1

        counter_flag = 0

        for j in range(len(final_df_hop_array[i])):

            if final_df_hop_array[i][j][0] == 1:

                if final_df_hop_array[i][j][1].startswith(
                    "CF_SRC_TGT_TRANSLATIONS_"
                ):

                    new_df.loc[i, "BUSINESS_TRANSLATION"] = (
                        f"TRANSLATION-(transformation_counter):\n"
                        + str(df[final_df_hop_array[i][j][1]].iloc[i])
                        + ";\n\n"
                        + new_df.loc[i, "BUSINESS_TRANSLATION"]
                    )

                    counter_flag += 1

                elif final_df_hop_array[i][j][1].startswith(
                    "CF_SRC_TGT_TRANSFORMATION_"
                ):

                    new_df.loc[i, "TRANSFORMATION"] = (
                        f"TRANSFORMATION-(transformation_counter):\n"
                        + str(df[final_df_hop_array[i][j][1]].iloc[i])
                        + ";\n\n"
                        + new_df.loc[i, "TRANSFORMATION"]
                    )

                    counter_flag += 1

            if counter_flag == 1:

                transformation_counter += 1

                counter_flag = 0

    filter = (
        ~new_df['CF_FINAL_ATTRIBUTE']
        .str.split('.')
        .str[-1]
        .str.startswith("LINE_")
        &
        ~new_df['CF_FINAL_ATTRIBUTE']
        .str.split('.')
        .str[-1]
        .eq("CRR_INSTRUMENT_2")
        &
        ~new_df['CF_FINAL_ATTRIBUTE']
        .str.split('.')
        .str[-1]
        .eq("CRR_INSTRUMENT_2_WIN")
    )

    df_special = new_df[filter].copy()

    df_rest = new_df[filter].copy()

    df_rest.to_excel(
        rf"{output_folder}\Centralized_CFARRI_Review_Template_{env}.xlsx",
        index=False
    )

    print("df_rest Saved-to-excel")