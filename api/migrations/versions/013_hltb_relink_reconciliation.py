"""Preserve uncertain write history across cancellation and relinking."""
from alembic import op
import sqlalchemy as sa

revision='013'
down_revision='012'
branch_labels=depends_on=None

def upgrade():
    op.add_column('hltb_publications',sa.Column('attempted',sa.Boolean,nullable=False,server_default=sa.false()))
    op.execute("UPDATE hltb_publications SET attempted=true WHERE state IN ('processing','uncertain','synced','cancelled')")

def downgrade():
    op.drop_column('hltb_publications','attempted')
