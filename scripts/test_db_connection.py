
import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv
import urllib.parse

# 寻找 .env 文件
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(env_path)

def test_connection():
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")

    if not all([db_user, db_password, db_name]):
        print(f"错误: .env 中缺少必要变量。读取路径: {env_path}")
        print(f"DB_USER: {db_user}, DB_NAME: {db_name}, Password set: {bool(db_password)}")
        return

    password_encoded = urllib.parse.quote_plus(db_password)
    url = f"postgresql://{db_user}:{password_encoded}@{db_host}:{db_port}/{db_name}"
    
    print(f"尝试连接到: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")
    
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            print("Successfully connected to the database!")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
