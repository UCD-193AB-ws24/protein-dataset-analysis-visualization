import os
from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from flask_cors import CORS
from supabase import create_client, Client

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




@app.route('/login', methods=['POST'])
def printdata():
    req = request.get_json()
    print(req)
    if Print_Data_Base(req):
        return jsonify({"msg": "login success"}), 200
    return jsonify({"msg": "login failed"}), 400


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    if 'username' not in request.form:
        return jsonify({"error": "Username is required"}), 400

    file = request.files['file']
    username = request.form['username']  # Get username from form data
    print(username)

    original_filename = file.filename.rsplit('.', 1)[0]
    file_extension = file.filename.rsplit('.', 1)[-1].lower()
    idName = f"{original_filename}.{file_extension}" 

    # Determine resource type
    resource_type = "raw" if file_extension not in ["jpg", "jpeg", "png", "gif", "mp4", "mov"] else "auto"

    try:
        upload_result = cloudinary.uploader.upload(file, resource_type=resource_type, public_id=idName, overwrite=True)
        add_file_for_user(username=username, file_name=idName)
        return jsonify({
            "message": "File uploaded successfully",
            "url": upload_result['secure_url'],
        })
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


if __name__ == '__main__':
    app.run(debug=True)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit



