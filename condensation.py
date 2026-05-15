import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from glob import glob


def contains_transformation(query):
    query = str(query)

    if len(query.strip()) <= 0 or query.lower() == 'nan':
        return False
    else:
        return True


def add_last_non_empty_column(df):
    chunk_size = 500

    temp_df = df.replace("", np.nan)

    chunks = [
        temp_df.iloc[i:i + chunk_size]
        for i in range(0, len(temp_df), chunk_size)
    ]

    def process_chunk(chunk):
        return chunk.apply(
            lambda row: row.last_valid_index(),
            axis=1
        )

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(process_chunk, chunks))

    last_cols = pd.concat(results)

    df["last_column_which_has_value"] = last_cols

    return df


def find_total_hops(name) -> int:
    split_val = name.split("_")
    return int(split_val[-1])


def find_hop1_size(column_list):
    count_hop1_size = 0

    for i in range(len(column_list)):
        split_values = column_list[i].split("_")

        if split_values[-1] == "1":
            count_hop1_size += 1
        else:
            if split_values[-2] == "1":
                count_hop1_size += 1

    return count_hop1_size


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
    Reorders columns in a Dataframe such that child columns immediately
    follow their parent columns.

    Logic:
    A parent column is identified if its name starts with prefix
    "CF_SRC_TGT_TRANSFORMATION_" and is followed by a digit
    (e.g., "CF_SRC_TGT_TRANSFORMATION_1").

    Child columns are those that start with the parent's full name
    followed by an underscore
    (e.g., "CF_SRC_TGT_TRANSFORMATION_1_A",
            "CF_SRC_TGT_TRANSFORMATION_1_B")

    param unordered_df:
        Merged_df which has wrong order of parent-child columns

    return:
        Merged_df which will have correct order of parent-child columns
        i.e. child columns will be placed immediately after parent columns
        and rest columns will be there in their original order
    """

    # Input df
    df = unordered_df

    # Get all original columns
    original_cols = df.columns.tolist()

    new_cols = []

    used = set()

    for col in original_cols:

        if col in used:
            continue

        new_cols.append(col)

        used.add(col)

        # Apply logic only to columns that start with the prefix
        if col.startswith(prefix):

            suffix = col[len(prefix):]

            if suffix.isdigit():

                children_prefix = col + "_"

                # Find all child columns
                children = [
                    c for c in original_cols
                    if c.startswith(children_prefix)
                    and c not in used
                ]

                children.sort()

                # get alphabetical order of child columns
                new_cols.extend(children)

                used.update(children)

    # Add any remaining columns that weren't captured
    for col in original_cols:

        if col not in used:
            new_cols.append(col)

    # Re-order Dataframe
    ordered_df = df[new_cols]

    # Print the re-ordered columns
    # print("New order of the columns",
    #       ordered_df.columns.tolist())

    return ordered_df


def consolidate_transpose(directory_path):

    all_excel_data = []

    count_of_rows = 0

    tracker_list = get_files("csv", directory_path)

    # get_files(".csv", directory_path)

    print(f"Found : {len(tracker_list)} files")

    print(tracker_list)

    for file in tracker_list:

        if '_TRANSPOSE' in file.split("\\")[-1]:

            # old logic :
            # if '_TRANSPOSE_sch' in file.split("\\")[-1]:

            # file_path = os.path.join(directory_path, file)

            print(f"Loaded : {file.split('\\')[-1]}")

            df = pd.read_csv(file, dtype=str)

            # old logic :
            # df = pd.read_csv(file, dtype=str)

            df = df.fillna("")

            count_of_cols = len(df.columns)

            print("count of columns:", count_of_cols)

            all_excel_data.append(df)

        else:
            print(f"FILE NOT FOUND: {file}")

    consolidated_df = pd.concat(
        all_excel_data,
        ignore_index=True
    )

    print(f"len(consolidated_df): {len(consolidated_df)}")

    print("Concatenated csv files")

    print(consolidated_df, "shape: ", consolidated_df.shape)

    consolidated_df.to_excel(
        rf"{output_folder}\consolidated_transpose.xlsx",
        index=False
    )

    return consolidated_df


def axiom_dst_filter(ax_dst_df, df):

    ax_dst_df = ax_dst_df.fillna('')

    axiom_key_list = ax_dst_df['AXIOM_KEY'].tolist()

    axiom_key_list = list(set(axiom_key_list))

    updated_list = []

    for col in axiom_key_list:
        updated_list.append(col.strip().upper())

    print(f"axiom_key_list: {updated_list}")

    print(f"len- axiom_key_list: {len(updated_list)}")

    df = df[df['CF_FINAL_ATTRIBUTE'].isin(updated_list)]

    return df


if __name__ == "__main__":

    transpose_folder = "Outputs"

    ax_dst_file = "Axiom_outputs"

    output_folder = "Outputs/Combined"

    # Step 1: consolidate all transpose outputs
    df = consolidate_transpose(transpose_folder)

    # Step 2: Reorder columns
    df = reorder_df_by_columns_hierarchy(
        df,
        "CF_SRC_TGT_TRANSFORMATION_"
    )

    df.to_excel(
        rf"{output_folder}\Consolidated_Reordered.xlsx",
        index=False
    )

    # df.to_excel(
    #     rf"{output_folder}\reordered_consolidated_transpose_{env}.xlsx",
    #     index=False
    # )

    # Step 3
    # Uses axiom dst file to filter on AXIOM KEY attributes
    # to only have those in the output.

    # ax_dst_df = pd.read_excel(
    #     ax_dst_file,
    #     sheet_name=env,
    #     dtype=str
    # )

    # df = axiom_dst_filter(ax_dst_df, df)

    print(f"df.columns: {list(df.columns)}")

    #########################
    # STARTING OF MAIN LOGIC
    #########################

    column_list = df.columns.to_list()

    last_col_name = column_list[-1]

    max_no_of_hops = find_total_hops(last_col_name)

    print("Max number of hops:", max_no_of_hops)

    hop1_size = find_hop1_size(column_list)

    print(f"hop1_size: {hop1_size}")

    # compute last hop for each row
    extra_df = add_last_non_empty_column(df)

    extra_df.to_excel(
        rf"{output_folder}\extra_df.xlsx",
        index=False
    )

    print("Extra df computed")

    # create new df
    new_df = pd.DataFrame(
        "",
        index=range(df.shape[0]),
        columns=[
            "CF_FINAL_ATTRIBUTE",
            "CF_SET_CODE",
            "TRANSFORMATION",
            "CF_ACTUAL_SOURCE"
        ]
    )

    # before_numbered_df = new_df

    # iterate over each row
    print("iterating over each row")

    final_df_hop_array = []

    for i in range(df.shape[0]):

        # TODO:
        # Drop empty hops only if the source and target
        # columns are the same

        transformation_result_array = []

        new_df.loc[i, "CF_FINAL_ATTRIBUTE"] = \
            df["CF_FINAL_ATTRIBUTE"].iloc[i]

        new_df.loc[i, "CF_ACTUAL_SOURCE"] = \
            df["CF_ACTUAL_SOURCE"].iloc[i]

        new_df.loc[i, "CF_SET_CODE"] = \
            df["CF_SET_CODE"].iloc[i]

        # new_df.loc[i,
        #   "CF_TGT_SCHEMA_TABLE_COLUMN"] =
        #   df["CF_TGT_SCHEMA_TABLE_COLUMN"].iloc[i]

        for hop_count in range(1, max_no_of_hops + 1):

            transformation_col_name = \
                f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"

            is_transformation_valid = contains_transformation(
                df[transformation_col_name].iloc[i]
            )

            keep_hop = True

            if hop_count > 1 and hop_count < max_no_of_hops:

                current_hop_src = \
                    f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count}"

                next_hop_src = \
                    f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count-1}"

                if current_hop_src == next_hop_src:

                    # since the source and targets are the same,
                    # drop the hop for simplifying the lineage

                    keep_hop = False

            last_hop_value_for_row = int(
                extra_df["last_column_which_has_value"]
                .iloc[i]
                .split("_")[-1]
            )

            if (
                keep_hop
                and (
                    is_transformation_valid
                    or last_hop_value_for_row == hop_count
                )
            ):

                # include the hop
                transformation_result_array.append(
                    (
                        1,
                        f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"
                    )
                )

                # transformation_result_array.append(
                #     (
                #         1,
                #         f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count}"
                #     )
                # )

            else:

                # exclude the hop
                transformation_result_array.append(
                    (
                        0,
                        f"CF_SRC_TGT_TRANSFORMATION_{hop_count}"
                    )
                )

                # transformation_result_array.append(
                #     (
                #         0,
                #         f"CF_SRC_SCHEMA_TABLE_COLUMN_{hop_count}"
                #     )
                # )

        final_df_hop_array.append(transformation_result_array)

    # for i in final_df_hop_array:
    #     print("->", i)

    print("Created final df hop array")

    # print("final_df_hop_array:",
    #       final_df_hop_array)

    file_name = "final_df_hop_array.txt"

    with open(file_name, 'w') as file:

        for row in final_df_hop_array:
            file.write('\t'.join(map(str, row)) + '\n')

    for i in range(len(final_df_hop_array)):

        hop_count_flag = 1

        transformation_counter = 1

        counter_flag = 0

        for j in range(len(final_df_hop_array[i])):

            if final_df_hop_array[i][j][0] == 1:

                if final_df_hop_array[i][j][1].startswith(
                    "CF_SRC_TGT_TRANSFORMATION_"
                ):

                    new_df.loc[i, "TRANSFORMATION"] = \
                        f"TRANSFORMATION-{transformation_counter}:\n" + \
                        str(
                            df[
                                final_df_hop_array[i][j][1]
                            ].iloc[i]
                        ) + \
                        "\n\n" + \
                        new_df.loc[i, "TRANSFORMATION"]

                    counter_flag += 1

            if counter_flag == 1:

                transformation_counter += 1

                counter_flag = 0

    new_df.to_excel(
        rf"{output_folder}\Condensed_GRIFFIN_Review_Template_old.xlsx",
        index=False
    )

    print("df_rest Saved to excel")