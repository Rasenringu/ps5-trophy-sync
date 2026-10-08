"""Explicit public library sharing; existing accounts remain friends-only."""
from alembic import op
import sqlalchemy as sa
revision='007'
down_revision='006'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('social_profiles',sa.Column('visibility',sa.String(16),nullable=False,server_default='friends'))

def downgrade():
    op.drop_column('social_profiles','visibility')
