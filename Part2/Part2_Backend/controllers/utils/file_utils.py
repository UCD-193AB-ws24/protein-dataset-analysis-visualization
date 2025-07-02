# import os
# from flask import Flask, request, jsonify
# from dotenv import load_dotenv
# from flask_cors import CORS
# from parse_matrix import parse_matrix
# from domain_parse import domain_parse
# import json
# from io import BytesIO
# from datetime import datetime
# # import requests
# import boto3
# import uuid

# from database.models import Base, User, Group, File
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import NullPool
# from auth_utils import verify_token

# # import traceback

# # Load environment variables
# load_dotenv()

# # Initialize Flask app
# app = Flask(__name__)
# CORS(app)

# # Configure AWS S3
# s3_client = boto3.client(
#     's3',
#     aws_access_key_id=os.getenv("S3_AWS_ACCESS_KEY_ID"),
#     aws_secret_access_key=os.getenv("S3_AWS_SECRET_ACCESS_KEY"),
#     region_name=os.getenv("AWS_REGION")
# )

# # Configure sqlalchemy
# if os.getenv("ENV") == "production":
#     engine = create_engine(
#         os.getenv("DATABASE_URL"),
#         poolclass=NullPool,
#         pool_pre_ping=True
#     )
# else:
#     engine = create_engine(
#         os.getenv("DATABASE_URL"),
#         pool_size=5,
#         max_overflow=10,
#         pool_recycle=300,
#         pool_pre_ping=True
#     )

# SessionLocal = sessionmaker(bind=engine)


# def guess_content_type(extension):
#     mapping = {
#         "csv": "text/csv",
#         "json": "application/json",
#         "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     }
#     return mapping.get(extension.lower(), "application/octet-stream")

# def upload_to_s3(file_obj):
#     file_obj.seek(0)       # rewind before wrapping
#     bucket_name = os.getenv('S3_BUCKET_NAME')

#     # Extract original filename/extension and create a unique filename
#     original_filename = file_obj.filename
#     extension = file_obj.filename.rsplit('.', 1)[-1].lower()

#     unique_filename = f"uploadedfiles/{uuid.uuid4()}.{extension.lower()}"

#     # Upload to S3
#     s3_client.upload_fileobj(
#         Fileobj=BytesIO(file_obj.read()),  # Important: rewrap as BytesIO
#         Bucket=bucket_name,
#         Key=unique_filename,
#         ExtraArgs={
#             "ContentType": guess_content_type(extension),
#             # "ACL": "public-read"
#         }
#     )

#     return unique_filename, original_filename  # Return the S3 object key (not full URL)