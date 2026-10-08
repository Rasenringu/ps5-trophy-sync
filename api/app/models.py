from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, UniqueConstraint, JSON, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Account(Base):
    __tablename__ = 'accounts'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password: Mapped[str] = mapped_column(String(256))

class Login(Base):
    __tablename__ = 'logins'
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    account: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    expires: Mapped[int] = mapped_column(BigInteger)

class Installation(Base):
    __tablename__ = 'installations'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))

class Profile(Base):
    __tablename__ = 'profiles'
    __table_args__ = (UniqueConstraint('installation', 'local_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    installation: Mapped[str] = mapped_column(ForeignKey('installations.id'))
    local_id: Mapped[str] = mapped_column(String(64))
    label: Mapped[str] = mapped_column(String(80))
    owner: Mapped[str | None] = mapped_column(ForeignKey('accounts.id'))
    token: Mapped[str | None] = mapped_column(String(64), unique=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    last_sync: Mapped[int | None] = mapped_column(BigInteger)

class Pairing(Base):
    __tablename__ = 'pairings'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    secret: Mapped[str] = mapped_column(String(64), unique=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    profile: Mapped[str] = mapped_column(ForeignKey('profiles.id'))
    expires: Mapped[int] = mapped_column(BigInteger)
    next_poll: Mapped[int] = mapped_column(BigInteger, default=0)
    state: Mapped[str] = mapped_column(String(16), default='pending')
    account: Mapped[str | None] = mapped_column(ForeignKey('accounts.id'))

class Import(Base):
    __tablename__ = 'imports'
    __table_args__ = (UniqueConstraint('profile', 'batch_id'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile: Mapped[str] = mapped_column(ForeignKey('profiles.id'))
    batch_id: Mapped[str] = mapped_column(String(36))
    digest: Mapped[str] = mapped_column(String(64))
    received: Mapped[int] = mapped_column(BigInteger)
    mock: Mapped[bool] = mapped_column(Boolean)

class Record(Base):
    __tablename__ = 'records'
    __table_args__ = (UniqueConstraint('profile', 'source', 'kind', 'key', 'mock'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    profile: Mapped[str] = mapped_column(ForeignKey('profiles.id'))
    source: Mapped[str] = mapped_column(String(16))
    kind: Mapped[str] = mapped_column(String(16))
    key: Mapped[str] = mapped_column(String(160))
    data: Mapped[dict] = mapped_column(JSON)
    mock: Mapped[bool] = mapped_column(Boolean)

class Rate(Base):
    __tablename__ = 'rates'
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)
    reset: Mapped[int] = mapped_column(BigInteger)

class Artwork(Base):
    __tablename__ = 'artwork'
    __table_args__ = (UniqueConstraint('source', 'title_id', 'trophy_id'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(String(16))
    title_id: Mapped[str] = mapped_column(String(64))
    trophy_id: Mapped[str] = mapped_column(String(64))  # Empty means game artwork.
    digest: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)

class TrophyInfo(Base):
    __tablename__ = 'trophy_info'
    source: Mapped[str] = mapped_column(String(16), primary_key=True)
    title_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trophy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    hidden: Mapped[bool] = mapped_column(Boolean)
    description: Mapped[str] = mapped_column(String(4000))

class TrophyText(Base):
    __tablename__ = 'trophy_text'
    source: Mapped[str] = mapped_column(String(16), primary_key=True)
    title_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trophy_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    language: Mapped[str] = mapped_column(String(15), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(4000))
    is_default: Mapped[bool] = mapped_column(Boolean)

class DevicePackage(Base):
    __tablename__ = 'device_packages'
    profile: Mapped[str] = mapped_column(ForeignKey('profiles.id'), primary_key=True)
    title_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    digest: Mapped[str] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column(JSON)

class DeviceArtwork(Base):
    __tablename__ = 'device_artwork'
    __table_args__ = (UniqueConstraint('profile', 'title_id', 'trophy_id'),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    profile: Mapped[str] = mapped_column(ForeignKey('profiles.id'))
    title_id: Mapped[str] = mapped_column(String(64))
    trophy_id: Mapped[str] = mapped_column(String(64))
    digest: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)

class SocialProfile(Base):
    __tablename__ = 'social_profiles'
    handle: Mapped[str] = mapped_column(String(32), primary_key=True)
    account: Mapped[str] = mapped_column(ForeignKey('accounts.id'), unique=True)
    display_name: Mapped[str] = mapped_column(String(60))
    visibility: Mapped[str] = mapped_column(String(16), default='friends', server_default='friends')

class Friendship(Base):
    __tablename__ = 'friendships'
    __table_args__ = (UniqueConstraint('first', 'second'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    first: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    second: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    requester: Mapped[str] = mapped_column(ForeignKey('accounts.id'))
    state: Mapped[str] = mapped_column(String(16))
    updated: Mapped[int] = mapped_column(BigInteger)
