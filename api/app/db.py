import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

engine = create_engine(os.environ.get('DATABASE_URL', 'postgresql+psycopg://sync@db/sync'))
Session = sessionmaker(engine, expire_on_commit=False)

def database():
    with Session() as db:
        yield db
