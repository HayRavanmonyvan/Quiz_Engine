import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "academic-rnd-secret-key-2026")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "quiz_engine_db")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))