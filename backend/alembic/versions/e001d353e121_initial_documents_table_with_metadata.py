"""initial_documents_table_with_metadata

Adds metadata columns to the documents table:
- filename, file_type, chunk_index, total_chunks, uploaded_at

Strategy: add as nullable → backfill defaults → set NOT NULL

Revision ID: e001d353e121
Revises:
Create Date: 2026-06-10 09:13:06.450588

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = 'e001d353e121'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add metadata columns to documents, handling existing rows safely."""

    # Step 1: add columns as NULLABLE (to avoid NOT NULL violation on existing rows)
    op.add_column('documents', sa.Column('filename', sa.String(length=512), nullable=True))
    op.add_column('documents', sa.Column('file_type', sa.String(length=32), nullable=True))
    op.add_column('documents', sa.Column('chunk_index', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column('total_chunks', sa.Integer(), nullable=True))
    op.add_column('documents', sa.Column(
        'uploaded_at',
        sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        nullable=True,
    ))

    # Step 2: backfill defaults for any existing rows
    op.execute("""
        UPDATE documents
        SET
            filename    = 'legacy_document.pdf',
            file_type   = 'pdf',
            chunk_index = 0,
            total_chunks = 1,
            uploaded_at = NOW()
        WHERE filename IS NULL
    """)

    # Step 3: set NOT NULL now that all rows have values
    op.alter_column('documents', 'filename', nullable=False)
    op.alter_column('documents', 'file_type', nullable=False)
    op.alter_column('documents', 'chunk_index', nullable=False)
    op.alter_column('documents', 'total_chunks', nullable=False)
    op.alter_column('documents', 'uploaded_at', nullable=False)

    # embedding was already nullable in DB; mark it NOT NULL to match model
    op.alter_column(
        'documents', 'embedding',
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        nullable=False,
    )

    # drop the old hnsw index (we'll rely on cosine distance queries directly)
    try:
        op.drop_index(
            op.f('documents_embedding_idx'),
            table_name='documents',
            postgresql_ops={'embedding': 'vector_cosine_ops'},
            postgresql_using='hnsw',
        )
    except Exception:
        pass  # index may not exist on all environments


def downgrade() -> None:
    """Reverse: restore index and drop metadata columns."""
    op.create_index(
        op.f('documents_embedding_idx'),
        'documents',
        ['embedding'],
        unique=False,
        postgresql_ops={'embedding': 'vector_cosine_ops'},
        postgresql_using='hnsw',
    )
    op.alter_column(
        'documents', 'embedding',
        existing_type=pgvector.sqlalchemy.vector.VECTOR(dim=384),
        nullable=True,
    )
    op.drop_column('documents', 'uploaded_at')
    op.drop_column('documents', 'total_chunks')
    op.drop_column('documents', 'chunk_index')
    op.drop_column('documents', 'file_type')
    op.drop_column('documents', 'filename')
