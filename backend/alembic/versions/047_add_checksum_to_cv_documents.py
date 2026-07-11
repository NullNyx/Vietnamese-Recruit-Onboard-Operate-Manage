"""add_checksum_to_cv_documents

Revision ID: fe0a86a67893
Revises: 046
Create Date: 2026-07-11 04:57:26.984866+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fe0a86a67893'
down_revision: Union[str, None] = '046'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cv_documents', sa.Column('checksum', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_cv_documents_checksum'), 'cv_documents', ['checksum'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_cv_documents_checksum'), table_name='cv_documents')
    op.drop_column('cv_documents', 'checksum')
