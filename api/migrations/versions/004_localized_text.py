"""Publisher-supplied native game/trophy translations, separate from observations."""
from alembic import op
import sqlalchemy as sa
revision='004'
down_revision='003'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('trophy_text',
        sa.Column('source',sa.String(16),primary_key=True),
        sa.Column('title_id',sa.String(64),primary_key=True),
        sa.Column('trophy_id',sa.String(64),primary_key=True),
        sa.Column('language',sa.String(15),primary_key=True),
        sa.Column('name',sa.String(200),nullable=False),
        sa.Column('description',sa.String(4000),nullable=False),
        sa.Column('is_default',sa.Boolean(),nullable=False))

def downgrade():
    op.drop_table('trophy_text')
