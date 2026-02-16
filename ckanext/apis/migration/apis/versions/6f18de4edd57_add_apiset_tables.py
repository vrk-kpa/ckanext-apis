"""Add Apiset tables

Revision ID: 6f18de4edd57
Revises:
Create Date: 2025-12-16 12:19:47.132229

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6f18de4edd57"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    engine = op.get_bind()
    inspector = sa.inspect(engine)
    tables = inspector.get_table_names()
    if "apiset_package_association" not in tables:
        op.create_table(
            'apiset_package_association',
            sa.Column(
                "package_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "apiset_id",
                sa.UnicodeText,
                sa.ForeignKey("package.id", ondelete="CASCADE", onupdate="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
        )


def downgrade():
    op.drop_table('apiset_package_association')
