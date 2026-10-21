"""Distinguish manual completion notes from automatic HLTB lookups."""
from alembic import op
import sqlalchemy as sa
revision='010'
down_revision='009'
branch_labels=depends_on=None
def upgrade():
    op.add_column('game_insights',sa.Column('hltb_mode',sa.String(16),nullable=False,server_default='automatic'))
    op.execute("UPDATE game_insights SET hltb_mode='manual' WHERE hltb_id IS NOT NULL OR main_seconds IS NOT NULL OR extra_seconds IS NOT NULL OR completionist_seconds IS NOT NULL")
def downgrade():
    op.drop_column('game_insights','hltb_mode')
