import os
from flask import Flask, request, jsonify
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
from flask_cors import CORS

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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    original_filename = file.filename.rsplit('.', 1)[0]
    file_extension = file.filename.rsplit('.', 1)[-1].lower()
    idName = original_filename + '.' + file_extension

    # Determine resource type based on file extension
    resource_type = "raw" if file_extension not in ["jpg", "jpeg", "png", "gif", "mp4", "mov"] else "auto"

    try:
        upload_result = cloudinary.uploader.upload(file, resource_type=resource_type, public_id=idName,  overwrite=True)
        return jsonify({
            "message": "File uploaded successfully",
            "url": upload_result['secure_url']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/retrieve/<public_id>', methods=['GET'])
def retrieve_file(public_id):
    file_url = cloudinary.utils.cloudinary_url(public_id, resource_type="raw")[0]
    return jsonify({"file_url": file_url})

if __name__ == '__main__':
    app.run(debug=True)
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit

