import os
import sys
import time
import shutil

import pandas as pd

from alive_progress import alive_bar
from lineage_adhoc import run_lineage
from output_formatting_adhoc import format_output


INPUT_DIR_PATH = "input_sql"

"""
Intent:
This method is used to prepare and return output formatting metadata.
"""


def get_output_formatting_metadata(
        filename,
        output_folder_path,
        immediate_schema,
        immediate_table,
        dst_name
):

    print(
        "INFO: Starting metadata creation for output formatting"
    )

    # metadata creation for output formatting

    # os.makedirs(output_folder_path, exist_ok=True)

    # metadata creation for output formatting

    # workflows_df = pd.read_excel(
    #     master_workbook,
    #     sheet_name="workflows"
    # )

    # row = workflows_df.loc[
    #     workflows_df['SQL_FILE_NAME'] == filename
    # ]

    metadata = {
        "SET_code": "fldst_name",
        "SET_name": "",
        "file_name": filename,
        "SET_type": "",
        "output_csv_name": (
            f"{output_folder_path}/csv/sp_{filename.replace('.sql', '')}.csv"
        ),
        "output_xlsx_name": (
            f"{output_folder_path}/sp_{filename.replace('.sql', '')}.xlsx"
        ),
        "immediate_schema": immediate_schema,
        "immediate_table": immediate_table
    }

    return metadata


def transfer_file(filename, INPUT_DIR_PATH):

    # Create processed_files folder if it does not exist

    os.makedirs("processed_files", exist_ok=True)

    file_source_path = os.path.join(
        cwd,
        f"{INPUT_DIR_PATH}/{filename}"
    )

    file_dest_path = os.path.join(
        cwd,
        f"processed_files/{filename}"
    )

    if not os.path.exists(file_dest_path):

        print(
            f"INFO: Moving file from: {file_source_path} to {file_dest_path}"
        )

        try:

            # shutil.move(file_source_path, file_dest_path)

            shutil.move(file_source_path, file_dest_path)

        except Exception as e:

            with open("error_logs.txt", "a") as error_logs:
                error_logs.write(
                    f"{filename} [ERR_1] Error in file transfer.\nDetails: {e}"
                )
                error_logs.close()

            return 1

    else:

        print(f"WARN: File {filename} already exists.")

        return 2


def clear_logs():

    print("INFO: Clearing logs.")

    with open("error_logs.txt", "w") as e1:
        e1.write("")
        e1.close()


def main(
        INPUT_DIR_PATH,
        output_folder_path,
        dst_name
):

    dir_list = os.listdir(INPUT_DIR_PATH)

    print(
        f"INFO: Starting execution for {len(dir_list)} files"
    )

    clear_logs()

    for file in dir_list:

        if file != "DDL_Set_SQL.json":
            continue

        print(f"INFO: Starting execution for file: {file}")

        sys.stdout = open("decoding_output.txt", "w")

        e1 = open("error_logs.txt", "a")

        e1.write(f"\n\nINFO: Running for file: {file}")

        e1.close()

        # Run lineage

        try:

            immediate_schema, immediate_table = run_lineage(
                file,
                INPUT_DIR_PATH
            )

        except Exception as e:

            print(
                f"ERROR: Error in extracting lineage.\nDetails: {e}"
            )

            with open("error_logs.txt", "a") as error_logs:
                error_logs.write(
                    f"{file} [ERR_1] {file} could not perform lineage extraction. | Details: {e}"
                )
                error_logs.close()

            continue

        # Create metadata for output formatting

        try:

            metadata = get_output_formatting_metadata(
                file,
                output_folder_path,
                immediate_schema,
                immediate_table,
                dst_name
            )

        except Exception as e:

            print(
                f"ERROR: Error in creating metadata.\nDetails: {e}"
            )

            with open("error_logs.txt", "a") as error_logs:
                error_logs.write(
                    f"lineage_wrapper - line 94 - [ERR_2] {file} could not create metadata for output processing. | Details: {e}"
                )
                error_logs.close()

            continue

        # Run output formatting

        try:

            format_output(
                start_line=0,
                metadata=metadata
            )

        except Exception as e:

            with open("error_logs.txt", "a") as error_logs:
                error_logs.write(
                    f"{file} [ERR_3] Could not run output formatting. | Details: {e}"
                )
                error_logs.close()

            continue

        # Execution successful initiate file transfer

        status = transfer_file(file, INPUT_DIR_PATH)

        if status == 0:
            print("INFO: Execution finished unsuccessfully.")
            break

    sys.stdout.close()

    print("INFO: Execution completed successfully!")