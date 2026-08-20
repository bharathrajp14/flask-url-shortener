import os
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Integer, String

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///short_urls.sqlite")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = sa.create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Urls(Base):
    __tablename__ = 'urls'
    id = sa.Column(Integer, primary_key=True)
    short_url = sa.Column(String(50), nullable=False, unique=True, index=True)
    original_url = sa.Column(String(2048), nullable=False)

Base.metadata.create_all(engine)
