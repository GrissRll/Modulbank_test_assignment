"""add sequence for id field in opetaions

Revision ID: 955c7d3f4948
Revises: 9f524647c4cd
Create Date: 2026-07-18 08:48:02.497834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "955c7d3f4948"
down_revision: Union[str, Sequence[str], None] = "9f524647c4cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("CREATE SEQUENCE operation_id_seq")

    op.alter_column(
        "operations",
        "operation_id",
        existing_type=sa.VARCHAR(length=120),
        server_default=sa.text("'operation-' || nextval('operation_id_seq')"),
        existing_nullable=False,
    )



def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "operations",
        "operation_id",
        existing_type=sa.VARCHAR(length=120),
        server_default=None,
        existing_nullable=False,
    )
    op.execute("DROP SEQUENCE operation_id_seq")
