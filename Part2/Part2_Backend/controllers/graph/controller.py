from flask import jsonify
from parsing.general_parse import parse_matrix
from parsing.domain_parse import domain_parse
from io import BytesIO

from services.s3_service import get_file_url



def generate_graph(coordinate_file, matrix_files, is_domain_specific):
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



def download(s3_key):
    try:
        # Generate a presigned URL for downloading the file
        presigned_url = get_file_url(s3_key)
        return jsonify({"url": presigned_url}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to generate download URL: {str(e)}"}), 500