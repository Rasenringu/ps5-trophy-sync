"""Private console artwork cache; trophy records remain unchanged."""
from alembic import op
import sqlalchemy as sa
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('artwork',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('source', sa.String(16), nullable=False),
        sa.Column('title_id', sa.String(64), nullable=False),
        sa.Column('trophy_id', sa.String(64), nullable=False),
        sa.Column('digest', sa.String(64), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.UniqueConstraint('source', 'title_id', 'trophy_id'))

def downgrade():
    op.drop_table('artwork')
