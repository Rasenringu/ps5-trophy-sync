"""Public social identities and explicitly approved friendships."""
import uuid
from alembic import op
import sqlalchemy as sa
revision='006'
down_revision='005'
branch_labels=None
depends_on=None

def upgrade():
    profiles=op.create_table('social_profiles',
        sa.Column('handle',sa.String(32),primary_key=True),
        sa.Column('account',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False,unique=True),
        sa.Column('display_name',sa.String(60),nullable=False))
    op.create_table('friendships',
        sa.Column('id',sa.String(36),primary_key=True),
        sa.Column('first',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False),
        sa.Column('second',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False),
        sa.Column('requester',sa.String(36),sa.ForeignKey('accounts.id'),nullable=False),
        sa.Column('state',sa.String(16),nullable=False),
        sa.Column('updated',sa.BigInteger(),nullable=False),
        sa.UniqueConstraint('first','second'))
    connection=op.get_bind()
    for account in connection.execute(sa.text('SELECT id FROM accounts')).scalars():
        suffix=uuid.uuid4().hex[:12]
        connection.execute(profiles.insert().values(handle='player_'+suffix,account=account,display_name='Player '+suffix[:6]))

def downgrade():
    op.drop_table('friendships')
    op.drop_table('social_profiles')
