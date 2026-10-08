"""enable pgvector and create document_chunks table

Revision ID: 002_create_vector_db
Revises: 20c9b3dfba34
Create Date: 2026-10-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# MUST BE DECLARED AS TOP-LEVEL STRINGS
revision: str = '002_create_vector_db'
down_revision: Union[str, None] = '20c9b3dfba34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    if inspect(op.get_bind()).has_table("document_chunks"):
        return

    # 2. Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_document_chunk_index')
    )

    # 3. Create HNSW Index for vector similarity
    op.execute(
        """
        CREATE INDEX idx_document_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """
    )

    # 4. Additional indexes
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])


def downgrade() -> None:
    op.drop_index('ix_document_chunks_document_id', table_name='document_chunks')
    op.execute("DROP INDEX IF EXISTS idx_document_chunks_embedding_hnsw;")
    op.drop_table('document_chunks')