import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from parsing.general_parse import parse_matrix
from parsing.domain_parse import domain_parse
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

# import traceback

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
            return jsonify({"error": "Project not found"}), 404

        # Fetch associated files
        files = session.query(File).filter_by(group_id=group_id).all()
        if not files:
            return jsonify({"error": "No files associated with this group"}), 404

        matrix_files = []
        coordinate_file = None
        graph_s3_key = None

        for file in files:
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': os.getenv('S3_BUCKET_NAME'),
                    'Key': file.s3_key,
                    'ResponseContentDisposition': f'attachment; filename="{file.file_name}"'
                },
                ExpiresIn=3600
            )
            file_info = {"url": presigned_url, "original_name": file.file_name}

            if file.file_type == "matrix":
                matrix_files.append(file_info)
            elif file.file_type == "coordinate":
                coordinate_file = file_info
            elif file.file_type == "graph":
                graph_s3_key = file.s3_key

        if not (matrix_files and coordinate_file and graph_s3_key):
            return jsonify({"error": "Matrix/coordinate/graph file not found for this project"}), 400

        graph_str = s3_client.get_object(
            Bucket=os.getenv('S3_BUCKET_NAME'), Key=graph_s3_key)["Body"].read().decode()

        # Parse graph JSON
        graph = json.loads(graph_str)

        return jsonify({
            "message": "Graph generated successfully",
            "title": group.title,
            "description": group.description,
            "graphs": graph,
            "num_genes": group.num_genes,
            "num_domains": group.num_domains,
            "matrix_files": matrix_files,  # Include presigned URLs and original filenames for matrix files
            "coordinate_file": coordinate_file  # Include presigned URL and original filename for coordinate file
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()


@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    coordinate_file = request.files.get('file_coordinate')
    matrix_files = [file for key, file in request.files.items() if key.startswith('file_matrix_')]
    is_domain_specific = request.form.get('is_domain_specific', 'false').lower() == 'true'

    if not coordinate_file or not matrix_files:
        return jsonify({"error": "Coordinate file and at least one matrix file are required"}), 400
    if is_domain_specific and len(matrix_files) > 3:
        return jsonify({"error": "A maximum of three matrix files are allowed for domain-specific graphs"}), 400
    if not is_domain_specific and len(matrix_files) != 1:
        return jsonify({"error": "Exactly one matrix file is required for non-domain-specific graphs"}), 400

    try:
        if is_domain_specific:
            # Create BytesIO objects with filenames for all files
            matrix_ios = []
            for matrix_file in matrix_files:
                matrix_bytes = matrix_file.read()
                matrix_io = BytesIO(matrix_bytes)
                matrix_io.name = matrix_file.filename
                matrix_ios.append(matrix_io)

            coordinate_bytes = coordinate_file.read()
            coordinate_io = BytesIO(coordinate_bytes)
            coordinate_io.name = coordinate_file.filename

            result = domain_parse(
                matrix_ios,
                coordinate_io,
                [m.filename for m in matrix_files],
            )
        else:
            matrix_file = matrix_files[0]
            matrix_bytes = matrix_file.read()
            coordinate_bytes = coordinate_file.read()
            # Create BytesIO objects with filename attributes
            matrix_io = BytesIO(matrix_bytes)
            matrix_io.name = matrix_file.filename
            coordinate_io = BytesIO(coordinate_bytes)
            coordinate_io.name = coordinate_file.filename
            graph = parse_matrix(matrix_io, coordinate_io)
            result = [{**graph, "domain_name": "general"}]

        combined = next(g for g in result if (g["domain_name"] == "ALL" or g["domain_name"] == "general"))
        num_genes = len(combined["nodes"])
        num_domains = len(result) - 1  # Exclude the combined graph

        return jsonify({
            "message": "Graph(s) generated successfully",
            "graphs": result,
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
    file_obj.seek(0)       # rewind before wrapping
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
    auth_header = request.headers.get('Authorization', '')
    access_token = auth_header.replace('Bearer ', '')
    if not access_token:
        return jsonify({"error": "Not Signed In"}), 400
    access_claims = verify_token(access_token)
    user_id = access_claims['sub']

    title = request.form.get('title')
    description = request.form.get('description')
    is_domain_specific = request.form.get('is_domain_specific', 'false').lower() == 'true'
    genomes = json.loads(request.form.get('genomes', '[]'))
    num_genes = request.form.get('num_genes')
    num_domains = request.form.get('num_domains')
    graph_data = request.form.get('graphs')
    group_id = request.form.get('group_id')  # Optional, for updating existing groups

    coordinate_file = request.files.get('file_coordinate')
    matrix_files = [file for key, file in request.files.items() if key.startswith('file_matrix_')]

    session = SessionLocal()

    try:
        # Find user first
        user = session.query(User).filter_by(id=user_id).first()
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

            return jsonify({"message": "Project updated successfully", "group_id": group_id}), 200

        # Handle new group creation
        if not coordinate_file or not matrix_files:
            return jsonify({"error": "Coordinate file and at least one matrix file are required for new projects"}), 400

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
        coordinate_s3_key, coordinate_filename = upload_to_s3(coordinate_file)
        graph_file = BytesIO(graph_data.encode('utf-8'))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        graph_file.filename = f"graph_{timestamp}.json"
        graph_s3_key, graph_filename = upload_to_s3(graph_file)

        # Insert coordinate and graph file records into database
        session.add_all([
            File(group_id=group_id, user_id=user.id, file_name=coordinate_filename, s3_key=coordinate_s3_key, file_type="coordinate"),
            File(group_id=group_id, user_id=user.id, file_name=graph_filename, s3_key=graph_s3_key, file_type="graph")
        ])

        # Insert matrix file records into database
        for matrix_file in matrix_files:
            matrix_s3_key, matrix_filename = upload_to_s3(matrix_file)
            session.add(File(group_id=group_id, user_id=user.id, file_name=matrix_filename, s3_key=matrix_s3_key, file_type="matrix"))

        session.commit()

        return jsonify({"message": "Files and project saved successfully", "group_id": group_id}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to save files: {str(e)}"}), 500

    finally:
        session.close()


@app.route('/get_user_file_groups', methods=['POST'])
def get_user_file_groups():
    auth_header = request.headers.get('Authorization', '')
    access_token = auth_header.replace('Bearer ', '')
    if not access_token:
        return jsonify({"error": "Not Signed In"}), 400
    access_claims = verify_token(access_token)
    user_id = access_claims['sub']

    session = SessionLocal()
    try:
        # Get user first
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Get all file groups associated with user
        groups = session.query(Group).filter_by(user_id=user.id).all()
        file_groups = []
        for group in groups:
            # Get files associated with the group
            files = session.query(File).filter_by(group_id=group.id).all()

            # Assemble group data
            file_groups.append({
                "id": str(group.id),
                "title": group.title,
                "description": group.description,
                "genomes": group.genomes,
                "num_genes": group.num_genes,
                "num_domains": group.num_domains,
                "is_domain_specific": group.is_domain_specific,
                "created_at": group.created_at.isoformat() if group.created_at else None,
                "last_updated_at": group.last_updated_at.isoformat() if group.last_updated_at else None,
                "files": [{
                    "file_name": file.file_name,
                    "file_type": file.file_type
                } for file in files]
            })
        return jsonify({"file_groups": file_groups}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to retrieve projects: {str(e)}"}), 500

    finally:
        session.close()


@app.route('/verify_user')
def get_user_data():
    auth_header = request.headers.get('Authorization', '')
    access_token = auth_header.replace('Bearer ', '')
    id_token = request.headers.get('X-ID-Token', '')

    try:
        access_claims = verify_token(access_token)
        user_id = access_claims['sub']

        id_claims = None
        email = None
        if id_token:
            id_claims = verify_token(id_token, access_token=access_token)
            email = id_claims['email']

        session = SessionLocal()
        #check if user exists
        user = session.query(User).filter_by(id=user_id).first()
        #if not, create new user
        if not user:
            new_user = User(id=user_id, email=email)
            session.add(new_user)
            session.commit()
            user = new_user

        return jsonify({
            'message': 'Hello, authenticated user!',
            'user': {
                'id': user_id,
                'email': email,
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 401
    finally:
        if 'session' in locals():
            session.close()


@app.route('/pokemon', methods=['GET'])
def nintendo():
    return "Hello Pokemon"

@app.route('/download_file', methods=['GET'])
def download_file():
    s3_key = request.args.get('key')
    if not s3_key:
        return jsonify({"error": "Missing file key"}), 400

    bucket_name = os.getenv('S3_BUCKET_NAME')

    try:
        # Generate a presigned URL for downloading the file
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return jsonify({"url": presigned_url}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate download URL: {str(e)}"}), 500

@app.route('/delete_group', methods=['DELETE'])
def delete_group():
    auth_header = request.headers.get('Authorization', '')
    access_token = auth_header.replace('Bearer ', '')
    if not access_token:
        return jsonify({"error": "Not Signed In"}), 400

    access_claims = verify_token(access_token)
    user_id = access_claims['sub']

    group_id = request.args.get('groupId')
    if not group_id:
        return jsonify({"error": "Missing groupId parameter"}), 400

    session = SessionLocal()
    try:
        # Find user first
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Find group and verify ownership
        group = session.query(Group).filter_by(id=group_id, user_id=user.id).first()
        if not group:
            return jsonify({"error": "Project not found"}), 404

        # Get all files associated with the group
        files = session.query(File).filter_by(group_id=group_id).all()

        # Delete files from S3
        for file in files:
            try:
                s3_client.delete_object(
                    Bucket=os.getenv('S3_BUCKET_NAME'),
                    Key=file.s3_key
                )
            except Exception as e:
                print(f"Error deleting file from S3: {str(e)}")
                # Continue with deletion even if S3 delete fails

        # Delete file records from database
        for file in files:
            session.delete(file)

        # Delete the group
        session.delete(group)
        session.commit()

        return jsonify({"message": "Project and associated files deleted successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"Failed to delete project: {str(e)}"}), 500

    finally:
        session.close()

@app.route('/', methods=['GET'])
def home():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True, port=3050)
    # app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit


