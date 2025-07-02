import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
from parse_matrix import parse_matrix
from domain_parse import domain_parse
import json
from io import BytesIO
from datetime import datetime
# import requests
import boto3
import uuid

from database.models import Base, User, Group, File
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from auth_utils import verify_token


# Load environment variables
load_dotenv()

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

def login(username, password):
    session = SessionLocal()
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and user.password_hash == password:
            return jsonify({"msg": "login success"}), 200
        else:
            return jsonify({"msg": "login failed"}), 400
    finally:
        session.close()


def verify(access_token, id_token=None):
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
