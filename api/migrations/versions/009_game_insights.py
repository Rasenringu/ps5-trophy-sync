"""Account-owned game information and bounded provider cache."""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'
branch_labels = depends_on = None

def upgrade():
    op.create_table('game_insights',
        sa.Column('account', sa.String(36), sa.ForeignKey('accounts.id'), primary_key=True),
        sa.Column('source', sa.String(16), primary_key=True),
        sa.Column('title_id', sa.String(64), primary_key=True),
        sa.Column('hltb_id', sa.BigInteger(), nullable=True),
        sa.Column('main_seconds', sa.Integer(), nullable=True),
        sa.Column('extra_seconds', sa.Integer(), nullable=True),
        sa.Column('completionist_seconds', sa.Integer(), nullable=True),
        sa.Column('updated', sa.BigInteger(), nullable=False),
        sa.Column('platprices_id', sa.BigInteger(), nullable=True))
    op.create_table('provider_cache',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('fetched', sa.BigInteger(), nullable=True),
        sa.Column('expires', sa.BigInteger(), nullable=False))

def downgrade():
    op.drop_table('provider_cache')
    op.drop_table('game_insights')
