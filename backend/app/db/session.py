# backend/app/db/session.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

import urllib.parse
from dotenv import load_dotenv

# Provide an explicit path to .env in the project root
load_dotenv(os.path.join(os.path.dirname(__file__), "../../../.env"))

# Build postgres connection URL from granular env vars
db_user = os.getenv("DB_USER", "postgres")
# Using quote_plus to safely URL-encode passwords containing special characters (like @)
db_password = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "postgres"))
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "projectmaster")

# Construct URL
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
