import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from parse_matrix import parse_matrix
import json
from io import BytesIO
from datetime import datetime
# import requests
import boto3
import uuid

from models import Base, User, Group, File
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from auth_utils import verify_token

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure AWS S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("S3_AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("S3_AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

# Configure sqlalchemy
if os.getenv("ENV") == "production":
    engine = create_engine(
        os.getenv("DATABASE_URL"),
        poolclass=NullPool,
        pool_pre_ping=True
    )
else:
    engine = create_engine(
        os.getenv("DATABASE_URL"),
        pool_size=5,
        max_overflow=10,
        pool_recycle=300,
        pool_pre_ping=True
    )

SessionLocal = sessionmaker(bind=engine)

@app.route('/login', methods=['POST'])
def login():
    req = request.get_json()
    username = req.get('username')
    password = req.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and user.password_hash == password:
            return jsonify({"msg": "login success"}), 200
        else:
            return jsonify({"msg": "login failed"}), 400
    finally:
        session.close()


# Expects a query parameter 'groupId' in the URL; e.g., /get_group_graph?groupId=123
# TODO: look into whether it makes sense to have query parameter or directly in the URL
@app.route('/get_group_graph', methods=['GET'])
def get_group_graph():
    group_id = request.args.get('groupId')
    if not group_id:
        return jsonify({"error": "Missing groupId parameter"}), 400

    session = SessionLocal()

    try:
        # Fetch group information
        group = session.query(Group).filter_by(id=group_id).first()
        if not group:
            return jsonify({"error": "Group not found"}), 404

        # Fetch associated files
        files = session.query(File).filter_by(group_id=group_id).all()
        if not files:
            return jsonify({"error": "No files associated with this group"}), 404

        matrix_s3_key = None
        coordinate_s3_key = None
        graph_s3_key = None

        for file in files:
            if file.file_type == "matrix":
                matrix_s3_key = file.s3_key
            elif file.file_type == "coordinate":
                coordinate_s3_key = file.s3_key
            elif file.file_type == "graph":
                graph_s3_key = file.s3_key

        if not (matrix_s3_key and coordinate_s3_key and graph_s3_key):
            return jsonify({"error": "Matrix/coordinate/graph file not found for this group"}), 400

        # Retrieve files **privately** with boto3
        bucket_name = os.getenv('S3_BUCKET_NAME')

        matrix_bytes = s3_client.get_object(
            Bucket=bucket_name, Key=matrix_s3_key)["Body"].read()

        coordinate_bytes = s3_client.get_object(
            Bucket=bucket_name, Key=coordinate_s3_key)["Body"].read()

        graph_str = s3_client.get_object(
            Bucket=bucket_name, Key=graph_s3_key)["Body"].read().decode()

        # Parse graph JSON
        graph = json.loads(graph_str)
        num_genes = len(graph.get("nodes", []))
        num_domains = 1  # Adjust as needed

        return jsonify({
            "message": "Graph generated successfully",
            "title": group.title,
            "description": group.description,
            "graph": graph,
            "num_genes": num_genes,
            "num_domains": num_domains
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    if 'file_matrix' not in request.files or 'file_coordinate' not in request.files:
        return jsonify({"error": "Both matrix and coordinate files are required"}), 400

    # Assumes only one matrix file uploaded, TODO: support multiple in the future
    file_matrix = request.files['file_matrix']
    file_coordinate = request.files['file_coordinate']
    is_domain_specific = request.form.get('is_domain_specific', 'false').lower() == 'true'

    try:
        matrix_bytes = file_matrix.read()
        coordinate_bytes = file_coordinate.read()

        graph = parse_matrix(BytesIO(matrix_bytes), BytesIO(coordinate_bytes))
        num_genes = len(graph["nodes"])
        num_domains = 1     # Placeholder, adjust in the future

        return jsonify({
            "message": "Graph generated successfully",
            "graph": graph,
            "num_genes": num_genes,
            "num_domains": num_domains,
            "is_domain_specific": is_domain_specific
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to generate graph: {str(e)}"}), 500


def guess_content_type(extension):
    mapping = {
        "csv": "text/csv",
        "json": "application/json",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    return mapping.get(extension.lower(), "application/octet-stream")

def upload_to_s3(file_obj):
    bucket_name = os.getenv('S3_BUCKET_NAME')

    # Extract original filename/extension and create a unique filename
    original_filename = file_obj.filename
    extension = file_obj.filename.rsplit('.', 1)[-1].lower()

    unique_filename = f"uploadedfiles/{uuid.uuid4()}.{extension.lower()}"

    # Upload to S3
    s3_client.upload_fileobj(
        Fileobj=BytesIO(file_obj.read()),  # Important: rewrap as BytesIO
        Bucket=bucket_name,
        Key=unique_filename,
        ExtraArgs={
            "ContentType": guess_content_type(extension),
            # "ACL": "public-read"
        }
    )

    return unique_filename, original_filename  # Return the S3 object key (not full URL)

@app.route('/save', methods=['POST'])
def save_files():
    username = request.form.get("username")
    if not username:
        return jsonify({"error": "Username is required"}), 400

    title = request.form.get('title')
    description = request.form.get('description')
    is_domain_specific = request.form.get('is_domain_specific', 'false').lower() == 'true'
    genomes = json.loads(request.form.get('genomes', '[]'))
    num_genes = request.form.get('num_genes')
    num_domains = request.form.get('num_domains')
    graph_data = request.form.get('graph')
    group_id = request.form.get('group_id')     # Optional, for updating existing groups

    file_matrix = request.files.get('file_matrix')
    file_coordinate = request.files.get('file_coordinate')

    session = SessionLocal()

    try:
        # Find user first
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Handle existing group
        if group_id:
            group = session.query(Group).filter_by(id=group_id).first()
            if not group:
                return jsonify({"error": "Invalid group_id provided"}), 400

            group.title = title
            group.description = description
            session.commit()

            return jsonify({"message": "Group updated successfully"}), 200

        # Handle new group creation
        new_group = Group(
            user_id=user.id,
            title=title,
            description=description,
            is_domain_specific=is_domain_specific,
            genomes=genomes,
            num_genes=int(num_genes),
            num_domains=int(num_domains)
        )
        session.add(new_group)
        session.commit()
        group_id = new_group.id

        # Upload files to S3
        matrix_s3_key, matrix_filename = upload_to_s3(file_matrix)
        coordinate_s3_key, coordinate_filename = upload_to_s3(file_coordinate)
        graph_file = BytesIO(graph_data.encode('utf-8'))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        graph_file.filename = f"graph_{timestamp}.json"
        graph_s3_key, graph_filename = upload_to_s3(graph_file)

        # Insert file records into database
        session.add_all([
            File(group_id=group_id, user_id=user.id, file_name=matrix_filename, s3_key=matrix_s3_key, file_type="matrix"),
            File(group_id=group_id, user_id=user.id, file_name=coordinate_filename, s3_key=coordinate_s3_key, file_type="coordinate"),
            File(group_id=group_id, user_id=user.id, file_name=graph_filename, s3_key=graph_s3_key, file_type="graph")
        ])
        session.commit()

        return jsonify({"message": "Files and group saved successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to save files: {str(e)}"}), 500

    finally:
        session.close()


@app.route('/get_user_file_groups', methods=['POST'])
def get_user_file_groups():
    req = request.get_json()
    username = req.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    session = SessionLocal()
    try:
        # Get user first
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get all file groups associated with user
        groups = session.query(Group).filter_by(user_id=user.id).all()

        result = []
        for group in groups:
            # Get files associated with the group
            files = session.query(File).filter_by(group_id=group.id).all()
            file_list = [{"file_name": file.file_name, "file_type": file.file_type} for file in files]

            # Assemble group data
            result.append({
                "id": str(group.id),
                "title": group.title,
                "description": group.description,
                "is_domain_specific": group.is_domain_specific,
                "genomes": group.genomes,
                "num_genes": group.num_genes,
                "num_domains": group.num_domains,
                "files": file_list
            })

        return jsonify({"file_groups": result}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to retrieve file groups: {str(e)}"}), 500

    finally:
        session.close()


@app.route('/get_user_files', methods=['POST'])
def get_user_files():
    req = request.get_json()
    username = req.get("username")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    session = SessionLocal()
    try:
        # Get user
        user = session.query(User).filter_by(username=username).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get all files for the user
        files = session.query(File).filter_by(user_id=user.id).all()

        file_list = [
            {
                "file_name": f.file_name,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                "file_type": f.file_type,
                "group_id": str(f.group_id) if f.group_id else None
            }
            for f in files
        ]

        return jsonify({"files": file_list}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to retrieve files: {str(e)}"}), 500

    finally:
        session.close()

@app.route('/api/user-data')
def get_user_data():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')

    try:
        user_info = verify_token(token)
        user_id = user_info['sub']

        # 🧠 Use user_email or user_id to fetch user-specific data from DB
        return jsonify({
            'message': 'Hello, authenticated user!',
            'user': {
                'id': user_id
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 401

@app.route('/pokemon', methods=['GET'])
def nintendo():
    return "Hello Pokemon"

@app.route('/', methods=['GET'])
def home():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True)
    # app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit


