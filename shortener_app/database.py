from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

engine = create_engine( # entry point to the database
    get_settings().db_url, connect_args={"check_same_thread": False} # check_same_thread=False is required for SQLite allowing more than 1 request at a time to communicate with the database.
)
SessionLocal = sessionmaker( # creates a working database session when SessionLocal is instantiated
    autocommit=False, autoflush=False, bind=engine
)
Base = declarative_base() # returns a class that connects the database engine to the SQLAlchemy functionality of the models