import csv
import json
import pandas as pd
import oracledb


def format_data_type(data_type, data_length, data_precision, data_scale):

    # Handle TIMESTAMP variations
    if data_type.upper().startswith('TIMESTAMP'):
        return data_type

    if data_type.upper().startswith('INTERVAL DAY'):
        return data_type

    if data_type.upper() == 'DATE':
        return data_type

    if data_length and (data_length != 'NaN' or data_length.lower() != 'null'):
        data_length = int(data_length)
    else:
        data_length = None

    if data_precision and (data_precision != 'NaN' or data_precision.lower() != 'null'):
        data_precision = int(data_precision)
    else:
        data_precision = None

    if data_scale and (data_scale != 'NaN' or data_scale.lower() != 'null'):
        data_scale = int(data_scale)
    else:
        data_scale = None

    if data_precision is not None and data_scale is not None:
        return f"{data_type}({data_precision},{data_scale})"
    elif data_precision is not None:
        return f"{data_type}({data_precision},0)"
    elif data_scale is not None:
        return f"{data_type}({data_length},{data_scale})"
    elif data_length is not None:
        return f"{data_type}({data_length})"
    else:
        return data_type


# def create_data_dictionary(csv_file_path):
def create_data_dictionary(df):

    data_dict = {}

    # with open(csv_file_path, mode='r') as csv_file:
    #     csv_reader = csv.DictReader(csv_file)
    #     for row in csv_reader:

    # df = pd.read_csv(csv_file_path, dtype=str)
    df = df.fillna("")
    df = df.drop_duplicates()

    for _, row in df.iterrows():

        schema_name = row['SCHEMA_NAME']
        table_name = row['TABLE_NAME']
        column_name = row['COLUMN_NAME']
        data_type = row['DATA_TYPE']
        data_length = row['DATA_LENGTH']
        data_precision = row['DATA_PRECISION']
        data_scale = row['DATA_SCALE']
        nullable = row['NULLABLE']

        formatted_data_type = format_data_type(
            data_type,
            data_length,
            data_precision,
            data_scale
        )

        if schema_name not in data_dict:
            data_dict[schema_name] = {}

        if table_name not in data_dict[schema_name]:
            data_dict[schema_name][table_name] = []

        data_dict[schema_name][table_name].append({
            'column_name': column_name,
            'data_type': formatted_data_type,
            'nullable': nullable
        })

    return data_dict


def write_data_dictionary_to_json(data_dict, json_file_path):

    with open(json_file_path, mode='w') as json_file:
        json.dump(data_dict, json_file, indent=4)

    # print output
    print(json.dumps(data_dict, indent=4))


# input and output files

def extract_ddl(DB, env, user, password):

    df = pd.DataFrame()
    connection_string = ""

    if DB == 'CFARRI' and env == 'PREPROD':
        connection_string = 'xtd06-scan.sdi.corp.bankofamerica.com:49125/TFSBRD01_SVC01'

    elif DB == 'CFARRI' and env == 'UAT':
        connection_string = 'xtu07-scan.sdi.corp.bankofamerica.com:49125/TFSBRU02_SVC01'

    elif DB == 'BDFRR' and env == 'PREPROD':
        connection_string = 'xtu14-scan.sdi.corp.bankofamerica.com:49125/TBDFRU02_SVC01'

    elif DB == 'BDFRR' and env == 'UAT':
        connection_string = 'xtu12-scan.sdi.corp.bankofamerica.com:49125/TBDFRU01_SVC01'

    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=connection_string
    )

    cursor = connection.cursor()

    query = """
    select owner as schema_name,
           table_name,
           column_name,
           data_type,
           data_length,
           data_precision,
           data_scale,
           nullable
    from all_tab_columns
    where owner in ()
      and table_name in ()
    """

    df = pd.read_sql(query, connection)

    connection.close()

    return df


DB = 'CFARRI'
env = 'PREPROD'

user = input("Enter Oracle username: ").upper()
password = input("Enter Oracle password: ")

# csv_file_path = '../input/ddl_files/ddl.csv'
json_file_path = f'./output/ddl_out/{DB}_{env}_ddl.json'

df = extract_ddl(DB, env, user, password)

# print(df)

# data_dict = create_data_dictionary(csv_file_path)
data_dict = create_data_dictionary(df)

write_data_dictionary_to_json(data_dict, json_file_path)

print(f"Data dictionary written to {json_file_path}")