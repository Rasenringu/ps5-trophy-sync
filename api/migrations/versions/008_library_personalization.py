"""Persistent account game visibility and profile customization."""
from alembic import op
import sqlalchemy as sa
revision='008'
down_revision='007'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('hidden_games',
        sa.Column('account',sa.String(36),sa.ForeignKey('accounts.id'),primary_key=True),
        sa.Column('source',sa.String(16),primary_key=True),
        sa.Column('title_id',sa.String(64),primary_key=True))
    for name,size,default in [('bio',600,''),('theme',16,'blue'),('avatar',16,'trophy')]:
        op.add_column('social_profiles',sa.Column(name,sa.String(size),nullable=False,server_default=default))
    op.add_column('social_profiles',sa.Column('favorite',sa.JSON(),nullable=True))

def downgrade():
    for name in ('favorite','avatar','theme','bio'):op.drop_column('social_profiles',name)
    op.drop_table('hidden_games')
