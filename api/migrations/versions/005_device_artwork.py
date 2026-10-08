"""Profile-scoped native packages and derived PNGs."""
from alembic import op
import sqlalchemy as sa
revision='005'
down_revision='004'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('device_packages',
        sa.Column('profile',sa.String(36),sa.ForeignKey('profiles.id'),primary_key=True),
        sa.Column('title_id',sa.String(64),primary_key=True),
        sa.Column('digest',sa.String(64),nullable=False),
        sa.Column('metadata_json',sa.JSON(),nullable=False))
    op.create_table('device_artwork',
        sa.Column('id',sa.String(64),primary_key=True),
        sa.Column('profile',sa.String(36),sa.ForeignKey('profiles.id'),nullable=False),
        sa.Column('title_id',sa.String(64),nullable=False),
        sa.Column('trophy_id',sa.String(64),nullable=False),
        sa.Column('digest',sa.String(64),nullable=False),
        sa.Column('content',sa.LargeBinary(),nullable=False),
        sa.UniqueConstraint('profile','title_id','trophy_id'))

def downgrade():
    op.drop_table('device_artwork')
    op.drop_table('device_packages')
