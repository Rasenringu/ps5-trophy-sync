"""Frozen initial account/device/import schema."""
from alembic import op
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('CREATE TABLE accounts (\n\tid VARCHAR(36) NOT NULL, \n\temail VARCHAR(254) NOT NULL, \n\tpassword VARCHAR(256) NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (email)\n)')
    op.execute('CREATE TABLE installations (\n\tid VARCHAR(36) NOT NULL, \n\tdigest VARCHAR(64) NOT NULL, \n\tPRIMARY KEY (id)\n)')
    op.execute('CREATE TABLE rates (\n\tkey VARCHAR(64) NOT NULL, \n\tcount INTEGER NOT NULL, \n\treset BIGINT NOT NULL, \n\tPRIMARY KEY (key)\n)')
    op.execute('CREATE TABLE logins (\n\tdigest VARCHAR(64) NOT NULL, \n\taccount VARCHAR(36) NOT NULL, \n\texpires BIGINT NOT NULL, \n\tPRIMARY KEY (digest), \n\tFOREIGN KEY(account) REFERENCES accounts (id)\n)')
    op.execute('CREATE TABLE profiles (\n\tid VARCHAR(36) NOT NULL, \n\tinstallation VARCHAR(36) NOT NULL, \n\tlocal_id VARCHAR(64) NOT NULL, \n\tlabel VARCHAR(80) NOT NULL, \n\towner VARCHAR(36), \n\ttoken VARCHAR(64), \n\trevoked BOOLEAN NOT NULL, \n\tlast_sync BIGINT, \n\tPRIMARY KEY (id), \n\tUNIQUE (installation, local_id), \n\tFOREIGN KEY(installation) REFERENCES installations (id), \n\tFOREIGN KEY(owner) REFERENCES accounts (id), \n\tUNIQUE (token)\n)')
    op.execute('CREATE TABLE imports (\n\tid VARCHAR(36) NOT NULL, \n\tprofile VARCHAR(36) NOT NULL, \n\tbatch_id VARCHAR(36) NOT NULL, \n\tdigest VARCHAR(64) NOT NULL, \n\treceived BIGINT NOT NULL, \n\tmock BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (profile, batch_id), \n\tFOREIGN KEY(profile) REFERENCES profiles (id)\n)')
    op.execute('CREATE TABLE pairings (\n\tid VARCHAR(36) NOT NULL, \n\tsecret VARCHAR(64) NOT NULL, \n\tcode VARCHAR(64) NOT NULL, \n\tprofile VARCHAR(36) NOT NULL, \n\texpires BIGINT NOT NULL, \n\tnext_poll BIGINT NOT NULL, \n\tstate VARCHAR(16) NOT NULL, \n\taccount VARCHAR(36), \n\tPRIMARY KEY (id), \n\tUNIQUE (secret), \n\tUNIQUE (code), \n\tFOREIGN KEY(profile) REFERENCES profiles (id), \n\tFOREIGN KEY(account) REFERENCES accounts (id)\n)')
    op.execute('CREATE TABLE records (\n\tid VARCHAR(36) NOT NULL, \n\tprofile VARCHAR(36) NOT NULL, \n\tsource VARCHAR(16) NOT NULL, \n\tkind VARCHAR(16) NOT NULL, \n\tkey VARCHAR(160) NOT NULL, \n\tdata JSON NOT NULL, \n\tmock BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (profile, source, kind, key, mock), \n\tFOREIGN KEY(profile) REFERENCES profiles (id)\n)')

def downgrade():
    op.drop_table('records')
    op.drop_table('pairings')
    op.drop_table('imports')
    op.drop_table('profiles')
    op.drop_table('logins')
    op.drop_table('rates')
    op.drop_table('installations')
    op.drop_table('accounts')
