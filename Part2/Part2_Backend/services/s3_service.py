import os
from dotenv import load_dotenv
from io import BytesIO
import boto3
import uuid

load_dotenv()

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("S3_AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("S3_AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

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

def delete_from_s3(file_obj):
    s3_client.delete_object(
        Bucket=os.getenv('S3_BUCKET_NAME'),
        Key=file_obj.s3_key
    )

def get_file_url(s3_key):
    return s3_client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': os.getenv('S3_BUCKET_NAME'),
            'Key': s3_key
        },
        ExpiresIn=3600
    )

def get_file(s3_key):
    return s3_client.get_object(Bucket=os.getenv('S3_BUCKET_NAME'), Key=s3_key)["Body"].read().decode()