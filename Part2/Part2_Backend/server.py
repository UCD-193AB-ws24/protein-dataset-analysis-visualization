from flask import Flask, request, jsonify
from flask_cors import CORS
import json

from auth_utils import authenticate_user

from controllers.group.controller import get_group_graph
from controllers.group.controller import save_group
from controllers.group.controller import get_user_file_groups
from controllers.group.controller import delete_group
from controllers.graph.controller import generate_graph
from controllers.graph.controller import download
from controllers.auth.controller import login
from controllers.auth.controller import verify_user_entry

from exception_templates.auth_exception import AuthenticationError


# Initialize Flask app
app = Flask(__name__)
CORS(app)


# Expects a query parameter 'groupId' in the URL; e.g., /get_group_graph?groupId=123
@app.route('/get_group_graph', methods=['GET'])
def controller_get_group_graph():
    group_id = request.args.get('groupId')
    return get_group_graph(group_id)


@app.route('/generate_graph', methods=['POST'])
def controller_generate_graph():
    coordinate_file = request.files.get('file_coordinate')
    matrix_files = [file for key, file in request.files.items() if key.startswith('file_matrix_')]
    is_domain_specific = request.form.get('is_domain_specific', 'false').lower() == 'true'
    return generate_graph(coordinate_file, matrix_files, is_domain_specific)


@app.route('/save', methods=['POST'])
def controller_save_group():
    try:
        access_claims, _ = authenticate_user(request)
    except AuthenticationError as e:
        return jsonify({"error": e.message}), e.status_code
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
    return save_group(user_id, title, description, coordinate_file, matrix_files, is_domain_specific, genomes, num_genes, num_domains, graph_data, group_id)


@app.route('/get_user_file_groups', methods=['POST'])
def controller_get_user_file_groups():
    try:
        access_claims, _ = authenticate_user(request)
    except AuthenticationError as e:
        return jsonify({"error": e.message}), e.status_code
    user_id = access_claims['sub']
    return get_user_file_groups(user_id)


@app.route('/verify_user')
def controller_verify_user():
    try:
        access_claims, id_claims = authenticate_user(request)
    except AuthenticationError as e:
        return jsonify({"error": e.message}), e.status_code
    user_id = access_claims['sub']
    email = None
    email = id_claims['email']
    return verify_user_entry(user_id, email)


@app.route('/pokemon', methods=['GET'])
def nintendo():
    return "Hello Pokemon"


@app.route('/download_file', methods=['GET'])
def controller_download_file():
    s3_key = request.args.get('key')
    if not s3_key:
        return jsonify({"error": "Missing file key"}), 400
    return download(s3_key)


@app.route('/delete_group', methods=['DELETE'])
def controller_delete_group():
    try:
        access_claims, _ =  authenticate_user(request)
    except AuthenticationError as e:
        return jsonify({"error": e.message}), e.status_code
    user_id = access_claims['sub']
    group_id = request.args.get('groupId')
    if not group_id:
        return jsonify({"error": "Missing groupId parameter"}), 400
    return delete_group(user_id, group_id)


@app.route('/', methods=['GET'])
def home():
    return "Hello World"


if __name__ == '__main__':
    app.run(debug=True, port=3050)
    # app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit