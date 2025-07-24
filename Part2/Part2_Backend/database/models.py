# Defines models for database tables
from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ARRAY, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    password_hash = Column(String, nullable=True)

class Group(Base):
    __tablename__ = "groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    title = Column(String)
    description = Column(String)
    is_domain_specific = Column(Boolean)
    num_genes = Column(Integer)
    num_domains = Column(Integer)
    genomes = Column(ARRAY(String))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    file_name = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    file_type = Column(String)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
