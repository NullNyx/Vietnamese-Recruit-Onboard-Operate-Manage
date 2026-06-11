"""Merge 035 and 036 heads into a single branch.

Revision ID: 037
Revises: 035, 036
Create Date: 2026-06-11
"""

revision = "037"
down_revision = ("035", "036")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge two heads — no schema changes."""
    pass


def downgrade() -> None:
    """Undo merge — no schema changes."""
    pass
