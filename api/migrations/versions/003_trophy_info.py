"""Native secret flags and descriptions, separate from observed unlock state."""
from alembic import op
import sqlalchemy as sa
revision='003'
down_revision='002'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('trophy_info',
        sa.Column('source',sa.String(16),primary_key=True),
        sa.Column('title_id',sa.String(64),primary_key=True),
        sa.Column('trophy_id',sa.String(64),primary_key=True),
        sa.Column('hidden',sa.Boolean(),nullable=False),
        sa.Column('description',sa.String(4000),nullable=False))

def downgrade():
    op.drop_table('trophy_info')
