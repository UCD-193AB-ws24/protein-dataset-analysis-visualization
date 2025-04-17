import os
from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from flask_cors import CORS
from supabase import create_client, Client

import pandas as pd
import json
import logging
from io import BytesIO

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUD_NAME"),
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# Configure Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def Print_Data_Base(req):
    response = (
    supabase.table("users")
    .select("*")
    .execute()
    )
    print(response)
    for firstResponse in response.data:
        if req.get('username') == firstResponse.get('username'):
            if req.get('password') == firstResponse.get('password_hash'):
                return True
    return False

def add_file_for_user(username, file_name):
    # Step 1: Get the user ID
    response = (
        supabase.table("users")
        .select("id")
        .eq("username", username)
        .execute()
    )

    if response.data:
        user_id = response.data[0]["id"]  # Extract the user ID

        # Step 2: Insert the file with the user ID
        insert_response = (
            supabase.table("user_files")
            .insert({"user_id": user_id, "file_name": file_name})
            .execute()
        )

        return insert_response
    else:
        return {"error": "User not found"}




def parse_coordinates(coord_file):
    df = pd.read_excel(BytesIO(coord_file.read()), engine='openpyxl')

    df['name'] = df['name'].str.replace('^Lsativa_', '', regex=True)
    df['protein_name'] = df['name'].str.split('_').str[-1]
    df['genome_name'] = df['name'].str.split('_').str[0]
    df['rel_position'] = df.groupby('genome_name')['position'].rank(method='first').astype(int)

    return df[['name', 'genome_name', 'protein_name', 'position', 'rel_position', 'orientation']]


def add_nodes(coords):
    nodes = []

    for i in range(len(coords)):
        nodes.append({
            "id" : '_'.join([coords['genome_name'][i], coords['protein_name'][i]]),
            "genome_name": coords['genome_name'][i],
            "protein_name": coords['protein_name'][i],
            "direction": coords['orientation'][i],
            "rel_position": int(coords['rel_position'][i]),
        })
    
    return nodes

def add_links(df_only_cutoffs, row_max, col_max):
    links = []

    for row in df_only_cutoffs.index:
        for col in df_only_cutoffs.columns:
            entry = {}
            is_col_max = pd.notna(col_max.at[row, col])
            is_row_max = pd.notna(row_max.at[row, col])

            if is_row_max and is_col_max:
                source = row
                target = col
                reciprocal_max = True
            elif is_row_max:
                source = row
                target = col
                reciprocal_max = False
            elif is_col_max:
                source = col
                target = row
                reciprocal_max = False
            else:
                continue  # skip non-max values


            links.append({
                "source": '_'.join([source.split('_')[0], source.split('_')[-1]]),
                "target": '_'.join([target.split('_')[0], target.split('_')[-1]]),
                "score": float(df_only_cutoffs.at[row, col]),
                "is_reciprocal": reciprocal_max
            })

    return links

def parse_matrix(matrix_file, coord_file):
    df = pd.read_excel(BytesIO(matrix_file.read()), engine='openpyxl')
    df = df.reset_index(drop=True)
    df = df.set_index(df.columns[0])
    df.index.name = None
    df = df.dropna(how='all')
    df = df.dropna(axis = 1, how='all')
    print(df)

    df_only_cutoffs = df[df > 55]

    coords = parse_coordinates(coord_file)
    print(coords)

    output = {}

    subsections = df_only_cutoffs.index.to_series().str.split("_").str[0].unique()

    output["nodes"] = add_nodes(coords)


    # Generate a dataframe with the column maxes compared to the row genomes
    col_max = pd.DataFrame(index = df_only_cutoffs.index, columns = df_only_cutoffs.columns)

    # Precompute a Series mapping each row to its subsection (faster than repeated str.startswith)
    row_to_subsection = pd.Series(index=df_only_cutoffs.index, dtype="object")
    for section in subsections:
        row_to_subsection.loc[df_only_cutoffs.index.str.startswith(section)] = section

    for col in df_only_cutoffs.columns:
        temp = pd.DataFrame({
            'value': df_only_cutoffs[col],
            'subsection': row_to_subsection
        })

        # For each subsection, find the max and assign it
        max_vals = temp.groupby('subsection')['value'].transform('max')
        col_max[col] = df_only_cutoffs[col].where(df_only_cutoffs[col] == max_vals)

    #print(col_max)

    # Generate a dataframe with the row maxes compared to the row genomes
    row_max = pd.DataFrame(index=df_only_cutoffs.index, columns=df_only_cutoffs.columns, dtype=float)

    # Precompute a Series mapping each column to its subsection
    col_to_subsection = pd.Series(index=df_only_cutoffs.columns, dtype="object")
    for subsection in subsections:
        col_to_subsection.loc[df_only_cutoffs.columns.str.startswith(subsection)] = subsection

    # Now process each row efficiently
    for idx, row in df_only_cutoffs.iterrows():
        # Combine row values with their subsections
        temp = pd.DataFrame({
            'value': row,
            'subsection': col_to_subsection
        })

        # Find max per subsection
        max_vals = temp.groupby('subsection')['value'].transform('max')

        # Keep only the max values per subsection in the row
        row_max.loc[idx] = row.where(row == max_vals)

   # print(row_max)

    output["links"] = add_links(df_only_cutoffs, row_max, col_max)
    #print(output)

    #print(json_output)
    #print(json.dumps(output, indent=4))

    return output




@app.route('/login', methods=['POST'])
def printdata():
    req = request.get_json()
    print(req)
    if Print_Data_Base(req):
        return jsonify({"msg": "login success"}), 200
    return jsonify({"msg": "login failed"}), 400


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file_matrix' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    if 'file_coordinate' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    if 'username' not in request.form:
        return jsonify({"error": "Username is required"}), 400

    file_matrix = request.files['file_matrix']
    file_coordinate = request.files['file_coordinate']
    username = request.form['username']  # Get username from form data
    print(username)


    matrix_original_filename = file_matrix.filename.rsplit('.', 1)[0]
    matrix_file_extension = file_matrix.filename.rsplit('.', 1)[-1].lower()
    matrix_idName = f"{matrix_original_filename}.{matrix_file_extension}" 

    # Determine resource type
    matrix_resource_type = "raw" if matrix_file_extension not in ["jpg", "jpeg", "png", "gif", "mp4", "mov"] else "auto"

    coordinate_original_filename = file_coordinate.filename.rsplit('.', 1)[0]
    coordinate_file_extension = file_coordinate.filename.rsplit('.', 1)[-1].lower()
    coordinate_idName = f"{coordinate_original_filename}.{coordinate_file_extension}" 

    # Determine resource type
    coordinate_resource_type = "raw" if coordinate_file_extension not in ["jpg", "jpeg", "png", "gif", "mp4", "mov"] else "auto"

    logging.basicConfig(level=logging.DEBUG)

    try:
        # The uploads work but the parse_matrix doesn't work if the uploads are there for some reason
        upload_result_matrix = cloudinary.uploader.upload(file_matrix, resource_type=matrix_resource_type, public_id=matrix_idName, overwrite=True)
        add_file_for_user(username=username, file_name=matrix_idName)

        upload_result_coordinate = cloudinary.uploader.upload(file_coordinate, resource_type=coordinate_resource_type, public_id=coordinate_idName, overwrite=True)
        add_file_for_user(username=username, file_name=coordinate_idName)

        ret_json = parse_matrix(file_matrix, file_coordinate)
        # print(ret_json)

        return jsonify([
            {
                "message": "File uploaded successfully",
                # "matrix_url": upload_result_matrix['secure_url'],
                # "coordinate_url": upload_result_coordinate['secure_url'],
                "file": ret_json
            }
        ])
            #jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/retrieve/<public_id>', methods=['GET'])
def retrieve_file(public_id):
    file_url = cloudinary.utils.cloudinary_url(public_id, resource_type="raw")[0]
    return jsonify({"file_url": file_url})


@app.route('/get_user_files', methods=['POST'])
def get_user_files():
    # Extract username from request JSON
    req = request.get_json()
    username = req.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Step 1: Get the user ID from Supabase
    user_response = (
        supabase.table("users")
        .select("id")
        .eq("username", username)
        .execute()
    )

    if not user_response.data:
        return jsonify({"error": "User not found"}), 404

    user_id = user_response.data[0]["id"]

    # Step 2: Get all files associated with the user ID
    files_response = (
        supabase.table("user_files")
        .select("file_name, uploaded_at")
        .eq("user_id", user_id)
        .execute()
    )

    # If no files are found, return an empty list
    return jsonify({"files": files_response.data}), 200

@app.route('/pokemon', methods=['GET'])
def nintendo():
    return "Hello Pokemon"

@app.route('/', methods=['GET'])
def home():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)
    # app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit



