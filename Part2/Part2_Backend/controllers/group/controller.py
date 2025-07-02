from flask import jsonify
import json
from io import BytesIO
from datetime import datetime

from database.models import Base, User, Group, File

from services.s3_service import upload_to_s3
from services.s3_service import delete_from_s3
from services.s3_service import get_file_url
from services.s3_service import get_file
from database.crud import create_group
from database.crud import add_file
from database.crud import get_first_or_none
from database.crud import get_all
from database.crud import delete
from database import session_scope



def get_group_graph(group_id):
    if not group_id:
        return jsonify({"error": "Missing groupId parameter"}), 400

    try:
        with session_scope() as session:
            group = get_first_or_none(session, Group, id=group_id)
            if not group:
                return jsonify({"error": "Project not found"}), 404

            # Fetch associated files
            files = get_all(session, File, group_id=group_id)
            if not files:
                return jsonify({"error": "No files associated with this group"}), 404

            matrix_files = []
            coordinate_file = None
            graph_s3_key = None

            for file in files:
                presigned_url = get_file_url(file.s3_key)
                file_info = {"url": presigned_url, "original_name": file.file_name}

                if file.file_type == "matrix":
                    matrix_files.append(file_info)
                elif file.file_type == "coordinate":
                    coordinate_file = file_info
                elif file.file_type == "graph":
                    graph_s3_key = file.s3_key

            if not (matrix_files and coordinate_file and graph_s3_key):
                return jsonify({"error": "Matrix/coordinate/graph file not found for this project"}), 400

            graph_str = get_file(graph_s3_key)

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




def get_user_file_groups(user_id):

    try:
        with session_scope() as session:
            user = get_first_or_none(session, User, id=user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

            # Get all file groups associated with user
            groups = get_all(session, Group, user_id=user.id)
            file_groups = []
            for group in groups:
                # Get files associated with the group
                files =get_all(session, File, group_id=group.id)

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
        return jsonify({"error": f"Failed to retrieve projects: {str(e)}"}), 500



def delete_group(user_id, group_id):

    try:
        with session_scope() as session:
            user = get_first_or_none(session, User, id=user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404
            
            group = get_first_or_none(session, Group, id=group_id, user_id=user.id)
            if not group:
                return jsonify({"error": "Project not found"}), 404

            # Get all files associated with the group
            files = get_all(session, File, group_id=group_id)

            # Delete files from S3
            for file in files:
                try:
                   delete_from_s3(file)
                except Exception as e:
                    print(f"Error deleting file from S3: {str(e)}")
                    # Continue with deletion even if S3 delete fails

            # Delete file records from database
            for file in files:
                delete(file)

            # Delete the group
            delete(group)

            return jsonify({"message": "Project and associated files deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to delete project: {str(e)}"}), 500





def save_group(user_id, title, description, coordinate_file, matrix_files, is_domain_specific, genomes, num_genes, num_domains, graph_data, group_id=None):

    try:
        with session_scope() as session:
            user = get_first_or_none(session, User, id=user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

            # Handle existing group
            if group_id:
                group = get_first_or_none(session, Group, id=group_id)
                if not group:
                    return jsonify({"error": "Invalid group_id provided"}), 400

                group.title = title
                group.description = description
                return jsonify({"message": "Project updated successfully", "group_id": group_id}), 200

            # Handle new group creation
            if not coordinate_file or not matrix_files:
                return jsonify({"error": "Coordinate file and at least one matrix file are required for new projects"}), 400
            print("Coordinate file:", coordinate_file)
            print("Matrix files:", matrix_files)


            new_group = create_group(session, user.id, title, description, is_domain_specific, genomes, num_genes, num_domains)
            group_id = new_group.id

            # Upload files to S3
            coordinate_s3_key, coordinate_filename = upload_to_s3(coordinate_file)
            graph_file = BytesIO(graph_data.encode('utf-8'))
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            graph_file.filename = f"graph_{timestamp}.json"
            graph_s3_key, graph_filename = upload_to_s3(graph_file)

            # Insert coordinate and graph file records into database
            add_file(session, group_id, user.id, coordinate_filename, coordinate_s3_key, "coordinate")
            add_file(session, group_id, user.id, graph_filename, graph_s3_key, "graph")


            # Insert matrix file records into database
            for matrix_file in matrix_files:
                matrix_s3_key, matrix_filename = upload_to_s3(matrix_file)
                add_file(session, group_id, user.id, matrix_filename, matrix_s3_key, "matrix")

            return jsonify({"message": "Files and project saved successfully", "group_id": group_id}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to save files: {str(e)}"}), 500
