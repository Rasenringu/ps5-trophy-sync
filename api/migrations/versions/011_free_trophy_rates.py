"""Optional keyless trophy listing, independent of console imports."""
from alembic import op
import sqlalchemy as sa

revision='011'
down_revision='010'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('game_insights',sa.Column('exophase_slug',sa.String(250),nullable=True))

def downgrade():
    op.drop_column('game_insights','exophase_slug')
