from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP, ARRAY, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()

# Define the join table
join_group_files = Table(
    'join_group_files',
    Base.metadata,
    Column('group_id', UUID(as_uuid=True), ForeignKey('groups.id', ondelete='CASCADE'), primary_key=True),
    Column('file_id', UUID(as_uuid=True), ForeignKey('files.id', ondelete='CASCADE'), primary_key=True)
)

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

    # New relationship to files
    files = relationship("File", secondary=join_group_files, back_populates="groups")

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=True)  # Can be removed if join table is used exclusively
    group_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)  # Optional: used elsewhere?
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    file_name = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    file_type = Column(String)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    ref_count = Column(Integer, default=0)
    marked_for_deletion = Column(Boolean, default=False)  # New flag

    # New relationship to groups
    groups = relationship("Group", secondary=join_group_files, back_populates="files")

class Inbox(Base):
    __tablename__ = "inbox"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender = Column(String, nullable=False)
    to = Column(String, nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=True)
