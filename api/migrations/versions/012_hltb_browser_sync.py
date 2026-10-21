"""Revocable browser connector and durable reviewed publications."""
from alembic import op
import sqlalchemy as sa

revision='012'
down_revision='011'
branch_labels=depends_on=None

def upgrade():
    op.create_table('hltb_pairings',
        sa.Column('account',sa.String(36),sa.ForeignKey('accounts.id'),primary_key=True),
        sa.Column('code',sa.String(64),unique=True,nullable=False),sa.Column('expires',sa.BigInteger,nullable=False))
    op.create_table('hltb_connections',
        sa.Column('account',sa.String(36),sa.ForeignKey('accounts.id'),primary_key=True),
        sa.Column('token',sa.String(64),unique=True,nullable=True),
        sa.Column('user_id',sa.BigInteger,nullable=False),sa.Column('username',sa.String(20),nullable=False),
        sa.Column('expires',sa.BigInteger,nullable=False),sa.Column('last_seen',sa.BigInteger,nullable=False))
    op.create_table('hltb_publications',
        sa.Column('id',sa.String(64),primary_key=True),
        sa.Column('account',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False),
        sa.Column('user_id',sa.BigInteger,nullable=False),sa.Column('source',sa.String(16),nullable=False),
        sa.Column('title_id',sa.String(64),nullable=False),sa.Column('hltb_id',sa.BigInteger,nullable=False),
        sa.Column('title',sa.String(400),nullable=False),sa.Column('platform',sa.String(32),nullable=False),
        sa.Column('seconds',sa.Integer,nullable=False),sa.Column('state',sa.String(16),nullable=False),
        sa.Column('updated',sa.BigInteger,nullable=False),sa.Column('submission_id',sa.BigInteger,nullable=True),
        sa.Column('error',sa.String(64),nullable=True))
    op.create_index('ix_hltb_publications_account','hltb_publications',['account'])

def downgrade():
    op.drop_table('hltb_publications');op.drop_table('hltb_connections');op.drop_table('hltb_pairings')
